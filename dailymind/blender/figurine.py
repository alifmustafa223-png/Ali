"""Hand-painted miniature figurines for The DailyMind's miniature cinematic universe.

Not cartoon toons: realistic ~7.5-head proportions like painted model-railway figures, matte acrylic-paint materials
with tiny colour variation, simple painted faces, clothes as separate pieces (coat skirt, cap/hat, apron, boots).
Pivot hierarchy (hips/chest/neck/shoulders/elbows/hips/knees) animated per frame, then zero-lag smoothed (no snaps).

    from figurine import Figure, bake_all
    w = Figure("worker1", height=0.0175, coat=(0.25, 0.3, 0.45), hat="cap")
    w.place((x, y, z), yaw_deg)
    for f, t in frames(): w.pose(f, t, walk=phase, carry=True)
    bake_all()
Actions: walk (phase), carry (arms forward holding something), hammer (strike cycle 0..1), lever (pull 0..1),
look (head yaw/pitch deg), wave, point.
"""
import math
import random

import bpy

_ALL = []
_MATS = {}


def _paint(name, col, rough=0.62, var=0.06, seed=0):
    """Matte acrylic paint: slight colour noise (hand-painted look), soft sheen."""
    key = (name, tuple(round(c, 3) for c in col))
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    p.inputs["Roughness"].default_value = rough
    try:
        p.inputs["Coat Weight"].default_value = 0.08
    except Exception:
        pass
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 900.0
    nz.inputs["Detail"].default_value = 4.0
    rp = nt.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].color = (*[max(0.0, c * (1 - var)) for c in col], 1)
    rp.color_ramp.elements[1].color = (*[min(1.0, c * (1 + var)) for c in col], 1)
    nt.links.new(nz.outputs["Fac"], rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], p.inputs["Base Color"])
    _MATS[key] = m
    return m


def _link(o):
    sc = bpy.context.scene
    if o.name not in sc.collection.objects:
        sc.collection.objects.link(o)


def _empty(name, par=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    _link(o)
    o.empty_display_size = 0.01
    if par is not None:
        o.parent = par
        o.matrix_parent_inverse.identity()
    o.location = loc
    return o


def _mesh(kind):
    key = "_fig_" + kind
    me = bpy.data.meshes.get(key)
    if me is None:
        if kind == "sphere":
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0)
        elif kind == "cyl":
            bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=1.0, depth=2.0)
        elif kind == "cone":
            bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=1.0, radius2=0.62, depth=2.0)
        tmp = bpy.context.active_object
        me = tmp.data
        me.name = key
        for p in me.polygons:
            p.use_smooth = True
        bpy.data.objects.remove(tmp, do_unlink=True)
    return me


def _part(name, kind, par, loc, scale, mat, rot=(0, 0, 0)):
    o = bpy.data.objects.new(name, _mesh(kind))
    _link(o)
    o.parent = par
    o.matrix_parent_inverse.identity()
    o.location = loc
    o.scale = scale
    o.rotation_euler = rot
    if not o.data.materials:
        o.data.materials.append(None)
    o.material_slots[0].link = "OBJECT"
    o.material_slots[0].material = mat
    return o


def _smooth(vals, alpha):
    if alpha >= 1.0 or len(vals) < 3:
        return vals
    fw = [vals[0]]
    for v in vals[1:]:
        fw.append(tuple(p + alpha * (x - p) for p, x in zip(fw[-1], v)))
    bw = [fw[-1]]
    for v in reversed(fw[:-1]):
        bw.append(tuple(p + alpha * (x - p) for p, x in zip(bw[-1], v)))
    return list(reversed(bw))


def bake_all():
    for f in _ALL:
        f.bake()


SKINS = [(0.93, 0.74, 0.6), (0.8, 0.58, 0.42), (0.58, 0.4, 0.28), (0.96, 0.8, 0.68)]


class Figure:
    """A painted miniature figure, 1 unit tall internally, scaled to `height` metres. Faces -Y at yaw 0."""

    def __init__(self, name, height=0.0175, skin=None, coat=(0.25, 0.3, 0.45), trousers=(0.18, 0.17, 0.2),
                 boots=(0.08, 0.06, 0.05), hair=(0.2, 0.13, 0.08), hat=None, hat_col=(0.12, 0.12, 0.14), apron=None,
                 long_coat=False, mustache=False, seed=0):
        self.name = name
        self._buf = {}
        _ALL.append(self)
        rr = random.Random(seed or hash(name) % 9999)
        skin = skin or SKINS[rr.randrange(len(SKINS))]
        P = _part
        m_skin = _paint(name + "skin", skin, 0.5, 0.04)
        m_coat = _paint(name + "coat", coat)
        m_tr = _paint(name + "tr", trousers)
        m_boot = _paint(name + "boot", boots, 0.4)
        m_hair = _paint(name + "hair", hair, 0.7)
        m_eye = _paint("fig_eye", (0.03, 0.025, 0.02), 0.3, 0.0)
        self.root = _empty(name + "_root")
        self.root.scale = (height, height, height)
        self.hips = _empty(name + "_hips", self.root, (0, 0, 0.5))
        self.legs, self.knees = [], []
        for s in (-1, 1):
            hj = _empty(f"{name}_hip{s}", self.hips, (0.06 * s, 0, 0))
            P(f"{name}_thigh{s}", "cyl", hj, (0, 0, -0.12), (0.045, 0.05, 0.13), m_tr)
            kn = _empty(f"{name}_knee{s}", hj, (0, 0, -0.245))
            P(f"{name}_shin{s}", "cyl", kn, (0, 0, -0.11), (0.038, 0.042, 0.12), m_tr)
            P(f"{name}_boot{s}", "sphere", kn, (0, -0.025, -0.235), (0.042, 0.075, 0.03), m_boot)
            self.legs.append(hj)
            self.knees.append(kn)
        self.chest = _empty(name + "_chest", self.hips, (0, 0, 0.0))
        P(name + "_pelvis", "sphere", self.chest, (0, 0, 0.02), (0.11, 0.075, 0.07), m_tr)
        P(name + "_torso", "cone", self.chest, (0, 0, 0.17), (0.115, 0.08, 0.16), m_coat, rot=(math.pi, 0, 0))
        P(name + "_shoulders", "sphere", self.chest, (0, 0, 0.31), (0.13, 0.08, 0.05), m_coat)
        if long_coat:
            P(name + "_skirt", "cone", self.chest, (0, 0, -0.08), (0.13, 0.1, 0.12), m_coat)
        if apron:
            P(name + "_apron", "cyl", self.chest, (0, -0.075, 0.05), (0.085, 0.01, 0.17), _paint(name + "apron", apron))
        self.arms, self.elbows, self.hands = [], [], []
        for s in (-1, 1):
            sh = _empty(f"{name}_sh{s}", self.chest, (0.135 * s, 0, 0.3))
            P(f"{name}_upper{s}", "cyl", sh, (0, 0, -0.08), (0.034, 0.036, 0.09), m_coat)
            el = _empty(f"{name}_el{s}", sh, (0, 0, -0.165))
            P(f"{name}_fore{s}", "cyl", el, (0, 0, -0.075), (0.03, 0.032, 0.085), m_coat)
            hd = _empty(f"{name}_hand{s}", el, (0, 0, -0.165))
            P(f"{name}_handm{s}", "sphere", hd, (0, 0, 0), (0.028, 0.022, 0.034), m_skin)
            self.arms.append(sh)
            self.elbows.append(el)
            self.hands.append(hd)
        self.neck = _empty(name + "_neck", self.chest, (0, 0, 0.34))
        P(name + "_neckm", "cyl", self.neck, (0, 0, 0.02), (0.03, 0.03, 0.03), m_skin)
        self.head = _empty(name + "_head", self.neck, (0, 0, 0.1))
        P(name + "_skull", "sphere", self.head, (0, 0, 0), (0.058, 0.064, 0.072), m_skin)
        P(name + "_nose", "sphere", self.head, (0, -0.062, -0.005), (0.012, 0.012, 0.016), m_skin)
        for s in (-1, 1):
            P(f"{name}_eye{s}", "sphere", self.head, (0.022 * s, -0.056, 0.012), (0.0075, 0.004, 0.0075), m_eye)
        P(name + "_hair", "sphere", self.head, (0, 0.008, 0.018), (0.061, 0.065, 0.062), m_hair)
        if mustache:
            P(name + "_must", "sphere", self.head, (0, -0.058, -0.022), (0.026, 0.008, 0.007), m_hair)
        m_hat = _paint(name + "hat", hat_col, 0.55)
        if hat == "cap":
            P(name + "_cap", "sphere", self.head, (0, 0.0, 0.045), (0.066, 0.07, 0.045), m_hat)
            P(name + "_peak", "sphere", self.head, (0, -0.06, 0.035), (0.045, 0.03, 0.006), m_hat)
        elif hat == "tophat":
            P(name + "_crown", "cyl", self.head, (0, 0.0, 0.11), (0.05, 0.05, 0.06), m_hat)
            P(name + "_brim", "cyl", self.head, (0, 0.0, 0.055), (0.085, 0.085, 0.005), m_hat)
        elif hat == "bowler":
            P(name + "_crown", "sphere", self.head, (0, 0.0, 0.07), (0.06, 0.06, 0.05), m_hat)
            P(name + "_brim", "cyl", self.head, (0, 0.0, 0.05), (0.08, 0.08, 0.005), m_hat)
        elif hat == "helmet":
            P(name + "_helm", "sphere", self.head, (0, 0.0, 0.04), (0.07, 0.074, 0.055), m_hat)
            P(name + "_brimh", "cyl", self.head, (0, 0.0, 0.03), (0.082, 0.085, 0.004), m_hat)

    def place(self, loc, yaw_deg=0.0):
        self.root.location = loc
        self.root.rotation_euler = (0, 0, math.radians(yaw_deg))

    def _k(self, o, f, loc=None, rot=None, alpha=0.4):
        for prop, v in (("location", loc), ("rotation_euler", rot)):
            if v is not None:
                self._buf.setdefault((o.name, prop), [alpha, {}])[1][f] = tuple(v)

    def bake(self):
        for (oname, prop), (alpha, d) in self._buf.items():
            o = bpy.data.objects[oname]
            fs = sorted(d)
            for f, v in zip(fs, _smooth([d[f] for f in fs], alpha)):
                setattr(o, prop, v)
                o.keyframe_insert(prop, frame=f)
        self._buf = {}

    def pose(self, f, t, walk=None, carry=False, hammer=None, lever=None, look=(0.0, 0.0), wave=False, point=False, lean=0.0):
        r = math.radians
        sw = kb0 = kb1 = 0.0
        bob = 0.0
        if walk is not None:
            ph = 2 * math.pi * walk
            sw = 26 * math.sin(ph)
            bob = 0.012 * abs(math.cos(ph))
            kb0 = 40 * max(0.0, math.sin(ph + 0.5))
            kb1 = 40 * max(0.0, math.sin(ph + 0.5 + math.pi))
        idle = 1.2 * math.sin(t * 1.5 + len(self.name))
        self._k(self.hips, f, loc=(0, 0, 0.5 + bob), rot=(r(lean), 0, r(idle * 0.3)))
        self._k(self.legs[0], f, rot=(r(-sw), 0, 0))
        self._k(self.legs[1], f, rot=(r(sw), 0, 0))
        self._k(self.knees[0], f, rot=(r(kb0 + 3), 0, 0))
        self._k(self.knees[1], f, rot=(r(kb1 + 3), 0, 0))
        # arms: (forward swing, sideways, elbow bend) per side; negative X rotation = forward
        L = [sw * 0.7, 6, 12]
        Rr = [-sw * 0.7, 6, 12]
        if carry:
            L, Rr = [55, 10, 60], [55, 10, 60]
        if hammer is not None:
            k = hammer % 1.0
            lift = 1 - abs(math.sin(math.pi * k)) if k < 0.75 else 0.0
            Rr = [40 + 110 * (1 - k * 1.33) if k < 0.75 else 40, 8, 70]
            L = [35, 8, 50]
        if lever is not None:
            L = Rr = [70 - 50 * lever, 10, 20 + 30 * lever]
        if wave:
            Rr = [20, 150 + 15 * math.sin(t * 10), 30]
        if point:
            Rr = [90, 15, 5]
        for s, (fw, sd, el) in enumerate((L, Rr)):
            side = -1 if s == 0 else 1
            self._k(self.arms[s], f, rot=(r(-fw), r(sd * -side), 0))
            self._k(self.elbows[s], f, rot=(r(-el), 0, 0))
        self._k(self.chest, f, rot=(0, 0, r(sw * 0.15)))
        self._k(self.neck, f, rot=(r(look[1]), 0, r(look[0] + idle)))
