"""Hero3D — stylized animated-film characters, built in code (no flat cartoons, no outlines).

    from hero3d import Hero
    h = Hero("capt", height=1.55, skin=(0.86, 0.6, 0.45), coat=("fabric_leather_02", (0.45, 0.28, 0.16)), beard=True, hat="brim")
    h.place((0, 0, 0), yaw_deg=10)
    h.pose(eyes="smug", brows="smug", mouth="grin", look=(0.3, 0.1), head=(10, -5, 4),
           arm_l=(10, 15, 20), arm_r=(-60, 20, 90), lean=4)           # one pose; call per frame with frame=f to animate

Design: big expressive head (~1/3.6 of height), glossy eyes with iris/pupil/cornea and real eyelids (blink, squint,
smug, wide), sculpted brows, a carved mouth (grin with teeth, O, smile, frown, smirk), metaball hair / beard /
mustache, subsurface-scattering skin, PBR cloth from Poly Haven textures. Every joint is a pivot empty, so poses and
animation are just rotations (keyframed when `frame` is given). Faces -Y at yaw 0.
"""
import math

import bmesh
import bpy

try:
    import dm_assets as AS
except Exception:  # texture library optional
    AS = None

_MAT = {}
_TEX = {}


def _link(o):
    if o.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(o)


def _empty(name, par=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    _link(e)
    if par is not None:
        e.parent = par
    e.location = loc
    return e


def mat(name, col, rough=0.5, metal=0.0, sss=0.0, clearcoat=0.0, alpha=1.0, trans=0.0, ior=1.45):
    key = (name, tuple(round(c, 3) for c in col), rough, sss)
    if key in _MAT:
        return _MAT[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["IOR"].default_value = ior
    if sss:
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
        p.inputs["Subsurface Scale"].default_value = 0.02
    if clearcoat:
        p.inputs["Coat Weight"].default_value = clearcoat
        p.inputs["Coat Roughness"].default_value = 0.03
    if trans:
        p.inputs["Transmission Weight"].default_value = trans
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
    _MAT[key] = m
    return m


def cloth(tex_id, tint, scale=6.0):
    """Poly Haven fabric tinted to `tint`; falls back to plain paint without the library."""
    if AS is None or not tex_id:
        return mat("cloth_" + str(tint), tint, 0.85)
    key = (tex_id, tint)
    if key not in _TEX:
        _TEX[key] = AS.texture(tex_id, "1k", scale=scale, tint=tint, name=f"{tex_id}_{len(_TEX)}")
    return _TEX[key]


def _obj(name, me, par, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), m=None, subsurf=2, smooth=True):
    o = bpy.data.objects.new(name, me)
    _link(o)
    o.parent = par
    o.location, o.rotation_euler, o.scale = loc, rot, scale
    if m is not None:
        me.materials.append(m)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    if subsurf:
        s = o.modifiers.new("sub", "SUBSURF")
        s.levels, s.render_levels = 1, subsurf
    return o


def _sphere_me(name, segs=24, rings=14, cut_below=None, cut_above=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    if cut_below is not None:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < cut_below - 1e-6], context="VERTS")
    if cut_above is not None:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > cut_above + 1e-6], context="VERTS")
    bm.to_mesh(me)
    bm.free()
    return me


def _capsule_me(name, r0, r1, length, segs=20):
    """Tapered capsule along -Z from the origin (joint at the top): radius r0 at the joint, r1 at the far end."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=12, radius=1.0)
    for v in bm.verts:
        z = v.co.z
        if z >= 0:
            v.co.x *= r0
            v.co.y *= r0
            v.co.z = z * r0
        else:
            v.co.x *= r1
            v.co.y *= r1
            v.co.z = z * r1 - length
    bm.to_mesh(me)
    bm.free()
    return me


def _metaball(name, par, blobs, m, res=0.012):
    """blobs: list of (loc, radius, (sx, sy, sz))."""
    mb = bpy.data.metaballs.new(name)
    mb.resolution = res
    mb.render_resolution = res * 0.5
    mb.threshold = 0.6
    for loc, rad, sc in blobs:
        e = mb.elements.new(type="ELLIPSOID")
        e.co = loc
        e.radius = rad
        e.size_x, e.size_y, e.size_z = sc
    o = bpy.data.objects.new(name, mb)
    _link(o)
    o.parent = par
    mb.materials.append(m)
    return o


def _bezier(name, par, pts, bevel, m):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = bevel
    cu.bevel_resolution = 4
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    o = bpy.data.objects.new(name, cu)
    _link(o)
    o.parent = par
    cu.materials.append(m)
    return o


SKIN_TONES = [(0.92, 0.68, 0.53), (0.86, 0.6, 0.45), (0.72, 0.48, 0.34), (0.55, 0.36, 0.25), (0.4, 0.26, 0.18)]


class Hero:
    def __init__(self, name, height=1.5, skin=(0.9, 0.65, 0.5), eye_col=(0.25, 0.45, 0.6), hair_col=(0.18, 0.11, 0.07),
                 coat=("fabric_leather_02", (0.45, 0.28, 0.16)), shirt=("rough_linen", (0.85, 0.8, 0.7)),
                 pants=("denim_fabric", (0.25, 0.22, 0.2)), boots=(0.12, 0.08, 0.05), hair="swept", beard=False,
                 mustache=False, hat=None, hat_col=(0.22, 0.14, 0.08), belly=1.0, nose=1.0, scarf=None):
        self.name = name
        k = height / 1.5                   # everything below is designed at 1.5 m
        self.k = k
        self.root = _empty(name, None)
        self.root.scale = (k, k, k)
        m_skin = mat(name + "_skin", skin, 0.45, sss=0.35)
        m_hair = mat(name + "_hair", hair_col, 0.55)
        m_coat = cloth(*coat) if coat else None
        m_shirt = cloth(*shirt)
        m_pants = cloth(*pants)
        m_boot = mat(name + "_boot", boots, 0.35, clearcoat=0.3)
        self.hips = _empty(name + "_hips", self.root, (0, 0, 0.66))
        # ---- torso (shirt) + coat shell + belt
        self.chest = _empty(name + "_chest", self.hips, (0, 0, 0.12))
        tor = _obj(name + "_torso", _sphere_me(name + "_torso_me"), self.chest, (0, 0, 0.14), scale=(0.2 * belly, 0.15 * belly, 0.27), m=m_shirt)
        if m_coat:
            for side in (-1, 1):  # open coat: two front panels + back, slightly larger than the torso
                pan = _obj(f"{name}_coat{side}", _sphere_me(f"{name}_coatme{side}", cut_below=-0.95), self.chest, (side * 0.055, 0.0, 0.1),
                           scale=(0.165 * belly, 0.165 * belly, 0.33), m=m_coat)
                pan.rotation_euler = (0, 0, side * 0.25)
            _obj(name + "_coat_tail", _capsule_me(name + "_tail_me", 0.21, 0.24, 0.12), self.hips, (0, 0.01, 0.02),
                 scale=(belly, 0.82 * belly, 1.0), m=m_coat)
        _obj(name + "_belt", _sphere_me(name + "_belt_me"), self.hips, (0, 0, 0.03), scale=(0.205 * belly, 0.155 * belly, 0.035),
             m=mat("belt", (0.08, 0.05, 0.03), 0.4, clearcoat=0.4))
        _obj(name + "_buckle", _sphere_me(name + "_buckle_me", 12, 8), self.hips, (0, -0.15 * belly, 0.03), scale=(0.035, 0.012, 0.028),
             m=mat("brass", (0.85, 0.62, 0.25), 0.25, metal=1.0))
        if scarf:
            _obj(name + "_scarf", _sphere_me(name + "_scarf_me"), self.chest, (0, -0.01, 0.38), scale=(0.13, 0.11, 0.05),
                 m=cloth("rough_linen", scarf))
        # ---- head
        self.neck = _empty(name + "_neck", self.chest, (0, 0, 0.4))
        _obj(name + "_neckm", _capsule_me(name + "_neck_me", 0.055, 0.06, 0.06), self.neck, (0, 0, 0.06), m=m_skin)
        self.head = _empty(name + "_head", self.neck, (0, 0, 0.2))
        hb = [((0, 0, 0), 0.2, (1.0, 0.95, 1.0)),            # cranium
              ((0, -0.03, -0.09), 0.15, (0.95, 0.9, 0.75)),  # jaw
              ((0, -0.07, -0.13), 0.08, (1.0, 0.9, 0.8)),    # chin
              ((-0.085, -0.1, -0.04), 0.075, (1, 1, 1)), ((0.085, -0.1, -0.04), 0.075, (1, 1, 1))]  # cheeks
        self.face = _metaball(name + "_faceMB", self.head, hb, m_skin)
        _obj(name + "_nose", _sphere_me(name + "_nose_me"), self.head, (0, -0.205, -0.03), scale=(0.042 * nose, 0.05 * nose, 0.045 * nose), m=m_skin)
        for side in (-1, 1):
            _obj(f"{name}_ear{side}", _sphere_me(f"{name}_ear_me{side}"), self.head, (side * 0.19, 0.0, -0.02), scale=(0.025, 0.05, 0.065), m=m_skin)
        # eyes: white + iris + pupil + clear cornea, each on a rotating eye pivot; lids on lid pivots
        m_white = mat("eyewhite", (0.95, 0.94, 0.92), 0.15, sss=0.1)
        m_iris = mat(name + "_iris", eye_col, 0.25)
        m_pupil = mat("pupil", (0.01, 0.01, 0.01), 0.2)
        m_cornea = mat("cornea", (1, 1, 1), 0.0, trans=1.0, ior=1.38)
        self.eyes, self.lids_up, self.lids_lo = [], [], []
        for side in (-1, 1):
            ep = _empty(f"{name}_eye{side}", self.head, (side * 0.072, -0.155, 0.03))
            _obj(f"{name}_white{side}", _sphere_me(f"{name}_wme{side}"), ep, scale=(0.052, 0.052, 0.058), m=m_white)
            _obj(f"{name}_iris{side}", _sphere_me(f"{name}_ime{side}"), ep, (0, -0.043, 0), scale=(0.028, 0.012, 0.03), m=m_iris)
            _obj(f"{name}_pupil{side}", _sphere_me(f"{name}_pme{side}"), ep, (0, -0.0505, 0), scale=(0.013, 0.006, 0.014), m=m_pupil)
            _obj(f"{name}_cornea{side}", _sphere_me(f"{name}_cme{side}"), ep, scale=(0.055, 0.055, 0.061), m=m_cornea)
            self.eyes.append(ep)
            lu = _empty(f"{name}_lidu{side}", self.head, (side * 0.072, -0.155, 0.03))
            _obj(f"{name}_lidum{side}", _sphere_me(f"{name}_lume{side}", cut_below=0.0), lu, scale=(0.06, 0.06, 0.066), m=m_skin, subsurf=1)
            ll = _empty(f"{name}_lidl{side}", self.head, (side * 0.072, -0.155, 0.03))
            _obj(f"{name}_lidlm{side}", _sphere_me(f"{name}_llme{side}", cut_above=0.0), ll, scale=(0.059, 0.059, 0.063), m=m_skin, subsurf=1)
            self.lids_up.append(lu)
            self.lids_lo.append(ll)
        # brows: thick curved strokes on pivots
        self.brows = []
        for side in (-1, 1):
            bp_ = _empty(f"{name}_brow{side}", self.head, (side * 0.075, -0.19, 0.115))
            _bezier(f"{name}_browc{side}", bp_, [(-0.045, 0.012, -0.004), (0, 0, 0.012), (0.045, 0.012, -0.006)], 0.014, m_hair)
            self.brows.append(bp_)
        # mouth: cavity (half ellipsoid) + teeth + tongue for open shapes; a lip line for closed shapes
        self.mouth = _empty(name + "_mouth", self.head, (0, -0.19, -0.105))
        m_cav = mat("mouth_cavity", (0.18, 0.03, 0.04), 0.6)
        self.cavity = _obj(name + "_cavity", _sphere_me(name + "_cav_me", cut_above=0.02), self.mouth, scale=(0.065, 0.03, 0.06), m=m_cav)
        self.teeth = _obj(name + "_teeth", _sphere_me(name + "_teeth_me"), self.mouth, (0, -0.012, -0.004), scale=(0.055, 0.015, 0.013),
                          m=mat("teeth", (0.95, 0.93, 0.86), 0.2))
        self.tongue = _obj(name + "_tongue", _sphere_me(name + "_tong_me"), self.mouth, (0, -0.005, -0.045), scale=(0.04, 0.018, 0.016),
                           m=mat("tongue", (0.75, 0.25, 0.28), 0.35, sss=0.3))
        self.lip = _bezier(name + "_lip", self.mouth, [(-0.05, -0.006, 0.01), (0, -0.012, -0.012), (0.05, -0.006, 0.01)], 0.006,
                           mat("lipline", (0.35, 0.12, 0.1), 0.5))
        # hair / beard / mustache (metaballs)
        hbl = []
        if hair == "swept":
            hbl = [((0, 0.02, 0.12), 0.17, (1.1, 1.05, 0.65)), ((-0.06, -0.08, 0.15), 0.09, (1.2, 0.8, 0.6)), ((0.08, -0.06, 0.16), 0.1, (1.1, 0.8, 0.6)),
                   ((-0.15, 0.03, 0.04), 0.08, (0.6, 1.2, 1.0)), ((0.15, 0.03, 0.04), 0.08, (0.6, 1.2, 1.0)), ((0, 0.12, 0.0), 0.14, (1.1, 0.7, 1.0))]
        elif hair == "curly":
            import random
            rr = random.Random(len(name))
            for j in range(24):
                a, b = rr.uniform(0, 2 * math.pi), rr.uniform(0.15, 1.25)
                hbl.append(((0.18 * math.sin(b) * math.cos(a), 0.18 * math.sin(b) * math.sin(a) + 0.02, 0.2 * math.cos(b) + 0.02), 0.06, (1, 1, 1)))
            hbl = [h for h in hbl if not (h[0][1] < -0.1 and h[0][2] < 0.12)]
        if hbl:
            self.hairo = _metaball(name + "_hairMB", self.head, hbl, m_hair, 0.01)
        if beard:
            bb = [((0, -0.1, -0.17), 0.1, (1.1, 0.8, 1.0)), ((-0.1, -0.06, -0.1), 0.08, (0.8, 1.0, 1.2)), ((0.1, -0.06, -0.1), 0.08, (0.8, 1.0, 1.2)),
                  ((0, -0.12, -0.22), 0.07, (1.0, 0.8, 1.0))]
            _metaball(name + "_beardMB", self.head, bb, m_hair, 0.01)
        if mustache or beard:
            mb = [((-0.035, -0.215, -0.072), 0.04, (1.2, 0.6, 0.55)), ((0.035, -0.215, -0.072), 0.04, (1.2, 0.6, 0.55)),
                  ((-0.075, -0.2, -0.085), 0.03, (1.0, 0.6, 0.5)), ((0.075, -0.2, -0.085), 0.03, (1.0, 0.6, 0.5))]
            _metaball(name + "_mustMB", self.head, mb, m_hair, 0.008)
        if hat == "brim":
            m_hat = cloth("fabric_leather_02", hat_col, 8.0)
            hp = _empty(name + "_hat", self.head, (0, 0.0, 0.13))
            hp.rotation_euler = (math.radians(-8), 0, 0)
            br = _obj(name + "_brim", _sphere_me(name + "_brim_me"), hp, scale=(0.36, 0.36, 0.022), m=m_hat)
            _obj(name + "_crown", _capsule_me(name + "_crown_me", 0.17, 0.2, 0.08), hp, (0, 0, 0.16), scale=(1.0, 0.92, 1.0), m=m_hat)
            _obj(name + "_band", _sphere_me(name + "_band_me"), hp, (0, 0, 0.035), scale=(0.205, 0.19, 0.03), m=mat("hatband", (0.1, 0.06, 0.04), 0.4))
        # ---- arms: shoulder -> elbow -> hand (sleeves = coat or shirt)
        m_sleeve = m_coat or m_shirt
        self.shoulders, self.elbows, self.hands = [], [], []
        for side in (-1, 1):
            sh = _empty(f"{name}_sh{side}", self.chest, (side * 0.2 * belly, 0, 0.3))
            _obj(f"{name}_upper{side}", _capsule_me(f"{name}_up_me{side}", 0.068, 0.058, 0.2), sh, m=m_sleeve)
            el = _empty(f"{name}_el{side}", sh, (0, 0, -0.22))
            _obj(f"{name}_fore{side}", _capsule_me(f"{name}_fo_me{side}", 0.058, 0.055, 0.17), el, m=m_sleeve)
            _obj(f"{name}_cuff{side}", _capsule_me(f"{name}_cu_me{side}", 0.062, 0.062, 0.02), el, (0, 0, -0.17), m=m_shirt)
            hd = _empty(f"{name}_hand{side}", el, (0, 0, -0.215))
            _obj(f"{name}_palm{side}", _sphere_me(f"{name}_pa_me{side}"), hd, (0, 0, -0.035), scale=(0.028, 0.048, 0.052), m=m_skin)
            for j in range(4):
                fy = -0.03 + 0.02 * j
                _obj(f"{name}_f{side}{j}", _capsule_me(f"{name}_f_me{side}{j}", 0.0105, 0.0095, 0.045 - 0.004 * abs(j - 1.5)), hd,
                     (0, fy, -0.08), rot=(math.radians(-8 + 4 * j), math.radians(side * 12), 0), m=m_skin)
            _obj(f"{name}_thumb{side}", _capsule_me(f"{name}_th_me{side}", 0.012, 0.011, 0.035), hd, (side * -0.012, -0.04, -0.03),
                 rot=(math.radians(35), 0, 0), m=m_skin)
            self.shoulders.append(sh)
            self.elbows.append(el)
            self.hands.append(hd)
        # ---- legs: hip -> knee -> boot
        self.legs, self.knees = [], []
        for side in (-1, 1):
            hp = _empty(f"{name}_hip{side}", self.hips, (side * 0.09, 0, 0))
            _obj(f"{name}_thigh{side}", _capsule_me(f"{name}_th_me{side}2", 0.085, 0.07, 0.25), hp, m=m_pants)
            kn = _empty(f"{name}_knee{side}", hp, (0, 0, -0.28))
            _obj(f"{name}_shin{side}", _capsule_me(f"{name}_sh_me{side}", 0.068, 0.065, 0.24), kn, m=m_boot if boots else m_pants)
            _obj(f"{name}_boot{side}", _sphere_me(f"{name}_bo_me{side}"), kn, (0, -0.045, -0.315), scale=(0.075, 0.13, 0.06), m=m_boot)
            self.legs.append(hp)
            self.knees.append(kn)

    # ------------------------------------------------------------------ placement / posing
    def place(self, loc, yaw_deg=0.0):
        self.root.location = loc
        self.root.rotation_euler = (0, 0, math.radians(yaw_deg))

    def _set(self, o, frame, rot=None, loc=None, scale=None):
        if rot is not None:
            o.rotation_euler = rot
        if loc is not None:
            o.location = loc
        if scale is not None:
            o.scale = scale
        if frame is not None:
            for p, v in (("rotation_euler", rot), ("location", loc), ("scale", scale)):
                if v is not None:
                    o.keyframe_insert(p, frame=frame)

    def pose(self, frame=None, eyes="open", brows="neutral", mouth="smile", look=(0.0, 0.0), head=(0.0, 0.0, 0.0), lean=0.0,
             arm_l=(0, 8, 10), arm_r=(0, 8, 10), legs=(0, 0), knees=(4, 4), talk=0.0):
        """arm = (forward swing deg, side raise deg, elbow bend deg). head = (pitch, yaw, tilt) deg. look = pupils (-1..1)."""
        r = math.radians
        self._set(self.hips, frame, rot=(r(lean), 0, 0))
        self._set(self.head, frame, rot=(r(head[0]), r(head[2]), r(head[1])))
        for ep in self.eyes:
            self._set(ep, frame, rot=(r(-look[1] * 25), 0, r(look[0] * 30)))
        # lids: angle of the upper lid around X (0 = fully closed over the front; -100 = wide open)
        # upper lid: +X rotation closes it over the front (85 = shut, -40 = edge just above the iris);
        # lower lid: +X rotation lowers its edge (37 = rest, 8 = pushed up by a smile)
        up, lo = {"open": (-40, 37), "wide": (-58, 50), "closed": (85, 10), "squint": (8, 15), "smug": (-2, 35), "sad": (-30, 35),
                  "happy": (-25, 8), "angry": (-15, 30)}[eyes]
        for side, (lu, ll) in zip((-1, 1), zip(self.lids_up, self.lids_lo)):
            tilt = {"sad": -14, "angry": 14, "smug": 6}.get(eyes, 0) * side
            self._set(lu, frame, rot=(r(up), r(tilt), 0))
            self._set(ll, frame, rot=(r(lo), 0, 0))
        b = {"neutral": (0, 0.0), "up": (-10, 0.02), "angry": (22, -0.012), "sad": (-20, 0.008), "smug": (8, 0.0), "skeptic": (0, 0)}[brows]
        for side, bp_ in zip((-1, 1), self.brows):
            ang, dz = b
            if brows == "skeptic":   # one brow up, one down
                ang, dz = (14, -0.006) if side < 0 else (-14, 0.025)
            self._set(bp_, frame, rot=(0, r(-ang * side), 0), loc=(side * 0.075, -0.19, 0.115 + dz))
        # mouth shapes: (cavity sx, sz, teeth visible, tongue visible, lip line visible, smile curvature)
        shapes = {"smile": (0.0, 0.0, 0, 0, 1, 1.0), "frown": (0.0, 0.0, 0, 0, 1, -1.0), "smirk": (0.0, 0.0, 0, 0, 1, 0.6),
                  "grin": (1.0, 0.75, 1, 0, 0, 1.0), "O": (0.55, 1.0, 0, 1, 0, 0.0), "open": (0.9, 0.9, 1, 1, 0, 0.3),
                  "talk": (0.7, 0.35 + 0.6 * talk, 1, 1, 0, 0.3)}
        sx, sz, teeth, tongue, line, curve = shapes[mouth]
        self._set(self.cavity, frame, scale=(max(1e-4, 0.065 * sx), 0.03 if sx else 1e-4, max(1e-4, 0.06 * sz)))
        self._set(self.teeth, frame, scale=((0.055 * sx if teeth else 1e-4), 0.015, 0.013))
        self._set(self.tongue, frame, scale=((0.04 * sx if tongue else 1e-4), 0.018, 0.016))
        pts = self.lip.data.splines[0].bezier_points
        if line:
            c = 0.016 * curve
            asym = 0.012 if mouth == "smirk" else 0.0
            pts[0].co, pts[1].co, pts[2].co = (-0.05, -0.004, c - asym), (0, -0.012, -c * 0.6), (0.05, -0.004, c + asym)
        self._set(self.lip, frame, scale=(1, 1, 1) if line else (1e-4, 1e-4, 1e-4))
        for side, sh, el, a in zip((-1, 1), self.shoulders, self.elbows, (arm_l, arm_r)):
            fwd, out, bend = a
            self._set(sh, frame, rot=(r(-fwd), r(side * out), 0))
            self._set(el, frame, rot=(r(-bend), 0, 0))
        for side, hp, kn, sw, kb in zip((-1, 1), self.legs, self.knees, legs, knees):
            self._set(hp, frame, rot=(r(-sw), 0, 0))
            self._set(kn, frame, rot=(r(kb), 0, 0))
