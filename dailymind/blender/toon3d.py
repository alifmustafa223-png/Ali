"""Real 3D toon characters for Blender (no armature needed: a pivot hierarchy animated per frame).

    from toon3d import Toon
    t = Toon("bob", skin=(0.95, 0.75, 0.6), coat=(0.8, 0.3, 0.2), hat="cap")
    t.root.location = (0, 0, 0)
    for f, tt in frames():
        t.pose(f, tt, walk=tt * 2, arms=(20, -10), look=(0.2, 0), mouth="smile", eyes="open", brows=0)

Chibi proportions (~1.15 m tall, big head, big eyes with pupils + highlights, noodle arms, round shoes), smooth
shading and an inverted-hull black outline so they match the 2D DailyMind toon style. Every part has its own pivot:
hips (bob/lean), chest, neck (head yaw/pitch/tilt), shoulders (arm swing/raise), hip joints (leg swing).
Expressions: eyes open/wide/closed/happy, pupils look (x, y), brows angle, mouth smile/grin/O/frown/talk.
"""
import math

import bpy

_MATS = {}


def _mat(name, col, rough=0.55, emit=0.0, sss=0.0):
    key = (name, tuple(round(c, 3) for c in col), rough, emit)
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    if emit:
        p.inputs["Emission Color"].default_value = (*col, 1)
        p.inputs["Emission Strength"].default_value = emit
    if sss:
        try:
            p.inputs["Subsurface Weight"].default_value = sss
            p.inputs["Subsurface Radius"].default_value = (0.3, 0.12, 0.08)
            p.inputs["Subsurface Scale"].default_value = 0.05
        except Exception:
            pass
    _MATS[key] = m
    return m


def _outline_mat():
    if "toon_outline" in _MATS:
        return _MATS["toon_outline"]
    m = bpy.data.materials.new("toon_outline")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (0.02, 0.015, 0.02, 1)
    e.inputs["Strength"].default_value = 1.0
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    m.use_backface_culling = True
    for attr in ("use_backface_culling_shadow", "use_backface_culling_lightprobe_volume"):
        try:
            setattr(m, attr, True)  # the hull must not shadow its own character (speckled 'fuzzy' skin)
        except Exception:
            pass
    _MATS["toon_outline"] = m
    return m


def _link(o):
    sc = bpy.context.scene
    if o.name not in sc.collection.objects:
        sc.collection.objects.link(o)
    return o


def _empty(name, par=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    _link(o)
    o.empty_display_size = 0.05
    if par is not None:
        o.parent = par
        o.matrix_parent_inverse.identity()
    o.location = loc
    return o


def _sphere(name, par, loc, scale, mat, outline=0.0, segs=32, rot=(0, 0, 0)):
    me = bpy.data.meshes.get("_toon_sphere_%d" % segs)
    if me is None:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=segs // 2, radius=1.0)
        tmp = bpy.context.active_object
        me = tmp.data
        me.name = "_toon_sphere_%d" % segs
        for p in me.polygons:
            p.use_smooth = True
        bpy.data.objects.remove(tmp, do_unlink=True)
    o = bpy.data.objects.new(name, me)
    _link(o)
    o.parent = par
    o.matrix_parent_inverse.identity()
    o.location = loc
    o.scale = scale
    o.rotation_euler = rot
    if mat is not None:
        _set_mat(o, mat)
    if outline:
        _add_outline(o, outline / max(1e-4, min(scale)))  # solidify works in local units
    return o


def _set_mat(o, mat):
    # object-linked material so the shared sphere mesh can carry different colours per part
    while len(o.data.materials) < 2:
        o.data.materials.append(None)
    o.material_slots[0].link = "OBJECT"
    o.material_slots[0].material = mat


def _add_outline(o, width):
    s = o.modifiers.new("outline", "SOLIDIFY")
    s.thickness = width
    s.offset = 1.0
    s.use_flip_normals = True
    s.use_rim = False
    s.material_offset = 1
    while len(o.data.materials) < 2:
        o.data.materials.append(None)
    o.material_slots[1].link = "OBJECT"
    o.material_slots[1].material = _outline_mat()


def _arc(name, par, loc, radius, angle_deg, thick, mat, rot=(0, 0, 0)):
    """Tube along a circular arc (mouths, brows, smiles). Built as a bevelled curve -> mesh."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = thick
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    n = 12
    sp.points.add(n - 1)
    a0 = math.radians(-angle_deg / 2)
    for i in range(n):
        a = a0 + math.radians(angle_deg) * i / (n - 1)
        sp.points[i].co = (radius * math.sin(a), 0, -radius * math.cos(a) + radius, 1)
    o = bpy.data.objects.new(name, cu)
    _link(o)
    o.parent = par
    o.matrix_parent_inverse.identity()
    o.location = loc
    o.rotation_euler = rot
    cu.materials.append(mat)
    return o


def _key(o, f, loc=None, rot=None, scale=None):
    if loc is not None:
        o.location = loc
        o.keyframe_insert("location", frame=f)
    if rot is not None:
        o.rotation_euler = rot
        o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        o.scale = scale
        o.keyframe_insert("scale", frame=f)


class Toon:
    """A chibi 3D character. Facing -Y (towards a camera placed at negative Y) when root rotation is 0."""

    def __init__(self, name, skin=(0.96, 0.76, 0.62), coat=(0.75, 0.3, 0.2), pants=(0.2, 0.22, 0.3),
                 hair=(0.25, 0.15, 0.08), hat=None, hat_col=(0.6, 0.15, 0.12), shoes=(0.12, 0.08, 0.06),
                 hairstyle="short", beard=False, mustache=False, belly=1.0, scale=1.0, outline=0.012, glasses=False):
        self.name = name
        S = _sphere
        ol = outline
        m_skin = _mat(name + "_skin", skin, 0.5)
        m_coat = _mat(name + "_coat", coat, 0.55)
        m_pants = _mat(name + "_pants", pants, 0.75)
        m_hair = _mat(name + "_hair", hair, 0.6)
        m_white = _mat("toon_eyewhite", (0.97, 0.97, 0.95), 0.25)
        m_black = _mat("toon_pupil", (0.02, 0.02, 0.03), 0.2)
        m_shine = _mat("toon_shine", (1, 1, 1), 0.1, emit=4.0)
        m_mouth = _mat("toon_mouth", (0.35, 0.05, 0.06), 0.5)
        m_shoe = _mat(name + "_shoe", shoes, 0.5)
        self.root = _empty(name + "_root")
        self.root.scale = (scale, scale, scale)
        self.hips = _empty(name + "_hips", self.root, (0, 0, 0.42))
        # legs: pivot at the hip joint, capsule down, shoe at the bottom
        self.legs = []
        for side in (-1, 1):
            hj = _empty(f"{name}_hip{side}", self.hips, (0.11 * side, 0, 0))
            S(f"{name}_leg{side}", hj, (0, 0, -0.17), (0.075, 0.075, 0.19), m_pants, ol)
            S(f"{name}_shoe{side}", hj, (0, -0.05, -0.37), (0.09, 0.14, 0.06), m_shoe, ol)
            self.legs.append(hj)
        # torso (egg) + chest pivot
        self.chest = _empty(name + "_chest", self.hips, (0, 0, 0.02))
        S(name + "_body", self.chest, (0, 0, 0.2), (0.24 * belly, 0.2 * belly, 0.27), m_coat, ol)
        # arms: pivot at the shoulder; a capsule hanging down + round hand
        self.arms = []
        for side in (-1, 1):
            sh = _empty(f"{name}_sh{side}", self.chest, (0.22 * side, 0, 0.36))
            S(f"{name}_arm{side}", sh, (0.0, 0, -0.15), (0.055, 0.055, 0.17), m_coat, ol)
            S(f"{name}_hand{side}", sh, (0.0, 0, -0.33), (0.065, 0.065, 0.065), m_skin, ol)
            self.arms.append(sh)
        # head
        self.neck = _empty(name + "_neck", self.chest, (0, 0, 0.47))
        self.head = _empty(name + "_head", self.neck, (0, 0, 0.3))
        S(name + "_skull", self.head, (0, 0, 0), (0.32, 0.3, 0.3), m_skin, ol)
        S(name + "_nose", self.head, (0, -0.3, -0.03), (0.045, 0.04, 0.04), m_skin, ol * 0.6)
        for side in (-1, 1):
            S(f"{name}_ear{side}", self.head, (0.31 * side, 0.0, -0.01), (0.05, 0.035, 0.07), m_skin, ol * 0.6)
        # eyes: white ball, pupil, highlight; each eye has a pivot that scales for blinks
        self.eyes, self.pupils = [], []
        for side in (-1, 1):
            ep = _empty(f"{name}_eye{side}", self.head, (0.115 * side, -0.245, 0.06))
            S(f"{name}_white{side}", ep, (0, 0, 0), (0.085, 0.05, 0.1), m_white, ol * 0.5)
            pp = _empty(f"{name}_pp{side}", ep, (0, -0.045, 0))
            S(f"{name}_pupil{side}", pp, (0, 0, 0), (0.045, 0.02, 0.055), m_black)
            S(f"{name}_shine{side}", pp, (0.018, -0.018, 0.022), (0.014, 0.008, 0.014), m_shine)
            self.eyes.append(ep)
            self.pupils.append(pp)
        # brows
        self.brows = []
        for side in (-1, 1):
            bp = _empty(f"{name}_brow{side}", self.head, (0.12 * side, -0.26, 0.2))
            S(f"{name}_browm{side}", bp, (0, 0, 0), (0.07, 0.02, 0.018), m_hair)
            self.brows.append(bp)
        # mouth: smile arc + open ellipse (one shown at a time via scale)
        self.mouth_p = _empty(name + "_mouth", self.head, (0, -0.285, -0.12))
        self.smile = _arc(name + "_smile", self.mouth_p, (0, 0, 0), 0.07, 120, 0.014, m_mouth)
        self.open = S(name + "_open", self.mouth_p, (0, 0.005, 0.0), (0.06, 0.025, 0.05), m_mouth)
        # hair / hats
        if hairstyle == "short":
            S(name + "_hair", self.head, (0, 0.04, 0.08), (0.335, 0.31, 0.27), m_hair, ol, rot=(math.radians(-12), 0, 0))
        elif hairstyle == "bald":
            S(name + "_hair", self.head, (0, 0.08, -0.02), (0.335, 0.27, 0.2), m_hair, ol)
        elif hairstyle == "long":
            S(name + "_hair", self.head, (0, 0.05, 0.02), (0.345, 0.32, 0.33), m_hair, ol, rot=(math.radians(-10), 0, 0))
            S(name + "_hairb", self.head, (0, 0.12, -0.25), (0.28, 0.16, 0.25), m_hair, ol)
        if beard:
            S(name + "_beard", self.head, (0, -0.12, -0.24), (0.22, 0.15, 0.13), m_hair, ol)
        if mustache:
            for side in (-1, 1):
                S(f"{name}_must{side}", self.head, (0.05 * side, -0.29, -0.08), (0.06, 0.025, 0.022), m_hair, ol * 0.5,
                  rot=(0, math.radians(-15 * side), 0))
        if glasses:
            m_gl = _mat("toon_glass", (0.1, 0.1, 0.12), 0.3)
            for side in (-1, 1):
                g = _arc(f"{name}_glass{side}", self.eyes[side > 0], (0, -0.06, -0.1), 0.1, 360, 0.01, m_gl)
                g.rotation_euler = (0, 0, 0)
        m_hat = _mat(name + "_hat", hat_col, 0.6)
        if hat == "cap":  # medieval builder's soft cap
            S(name + "_hat", self.head, (0, 0.03, 0.17), (0.35, 0.33, 0.2), m_hat, ol, rot=(math.radians(-15), 0, 0))
        elif hat == "hardhat":
            S(name + "_hat", self.head, (0, 0.0, 0.14), (0.35, 0.34, 0.24), m_hat, ol)
            S(name + "_brim", self.head, (0, -0.06, 0.1), (0.4, 0.4, 0.03), m_hat, ol)
        elif hat == "helmet":
            S(name + "_hat", self.head, (0, 0.0, 0.12), (0.36, 0.35, 0.26), m_hat, ol)
            S(name + "_nasal", self.head, (0, -0.33, 0.02), (0.025, 0.02, 0.1), m_hat, ol * 0.5)
        elif hat == "beret":
            S(name + "_hat", self.head, (0.05, 0.02, 0.24), (0.36, 0.34, 0.1), m_hat, ol, rot=(0, math.radians(10), 0))
        self.mats = dict(skin=m_skin, coat=m_coat)

    # ------------------------------------------------------------------ animation
    def pose(self, f, t, walk=None, arms=None, arm_side=None, look=(0.0, 0.0), head=(0.0, 0.0, 0.0), eyes="open",
             brows=0.0, mouth="smile", talk=0.0, bounce=0.0, lean=0.0, squash=1.0, blink=None, jump=0.0):
        """walk: phase in cycles (None = standing); arms: (left_deg, right_deg) forward swing,
        arm_side: (left_deg, right_deg) raise sideways (+ = up); look: pupil offset (-1..1); head: (yaw, pitch, tilt) deg;
        brows: + raised / - angry; mouth: smile/grin/O/frown/talk/flat; talk 0..1 opens the mouth; bounce/jump in metres."""
        sw = 0.0
        bob = 0.0
        sq_walk = 1.0
        lag = 0.0
        if walk is not None:
            ph = 2 * math.pi * walk
            sw = 34 * math.sin(ph)
            bob = 0.07 * abs(math.sin(ph))          # bouncy, happy hop on every step
            sq_walk = 1.0 + 0.05 * math.cos(2 * ph)   # squash on contact, stretch in the air
            lag = 5 * math.sin(2 * ph - 0.9)          # head follows the bounce a beat late
        sway = 1.5 * math.sin(t * 1.7 + len(self.name))  # idle life: nobody stands frozen
        squash = squash * sq_walk
        z = 0.42 + bob + bounce + jump
        _key(self.hips, f, loc=(0, 0, z), rot=(math.radians(lean), math.radians(sway * 0.5), 0),
             scale=(1 / math.sqrt(squash), 1 / math.sqrt(squash), squash))
        _key(self.legs[0], f, rot=(math.radians(sw), 0, 0))
        _key(self.legs[1], f, rot=(math.radians(-sw), 0, 0))
        a = arms if arms is not None else (-sw * 0.8, sw * 0.8)
        sd = arm_side if arm_side is not None else (8, 8)
        _key(self.arms[0], f, rot=(math.radians(a[0]), math.radians(sd[0]), 0))
        _key(self.arms[1], f, rot=(math.radians(a[1]), math.radians(-sd[1]), 0))
        _key(self.chest, f, rot=(0, 0, math.radians(sw * 0.15)))
        yaw, pitch, tilt = head
        breathe = 0.01 * math.sin(t * 2.2)
        _key(self.neck, f, loc=(0, 0, 0.47 + breathe),
             rot=(math.radians(pitch + lag), math.radians(tilt + sway), math.radians(yaw)))
        if blink is None:
            blink = ((t + hash(self.name) % 7 * 0.37) % 3.3) < 0.1 and eyes != "closed"
        ez = {"open": 1.0, "wide": 1.25, "closed": 0.08, "happy": 0.35}[eyes]
        if blink:
            ez = 0.08
        ps = 1.0 if eyes != "wide" else 0.75
        for i, (ep, pp) in enumerate(zip(self.eyes, self.pupils)):
            _key(ep, f, scale=(1.0 if eyes != "wide" else 1.12, 1.0, ez))
            _key(pp, f, loc=(0.035 * look[0], -0.045, 0.04 * look[1]), scale=(ps, 1, ps))
        for i, bp in enumerate(self.brows):
            side = -1 if i == 0 else 1
            _key(bp, f, loc=(0.12 * side, -0.26, 0.2 + 0.04 * max(0.0, brows) + (0.02 if eyes == "wide" else 0)),
                 rot=(0, math.radians(-18 * brows * side), 0))
        sm = {"smile": (1, 1), "grin": (1.35, 1.3), "frown": (1, -1), "flat": (1, 0.15), "O": (0, 0), "talk": (0.9, 0.6)}.get(mouth, (1, 1))
        op = {"O": 1.0, "grin": 0.0, "talk": talk}.get(mouth, 0.0)
        if mouth == "talk":
            sm = (0.9 * (1 - talk) + 0.01, 0.6)
        _key(self.smile, f, scale=(sm[0], 1, sm[1] if sm[1] != 0 else 0.01) if sm[0] > 0 else (0.001, 0.001, 0.001))
        _key(self.open, f, scale=(0.06 * (0.8 + 0.2 * op), 0.025, 0.05 * op + 0.0005) if op > 0 else (0.0001, 0.0001, 0.0001))
