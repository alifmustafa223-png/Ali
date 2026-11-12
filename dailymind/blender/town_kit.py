"""Modular miniature town kit (1:100 by default): detailed Parisian-style facades for The DailyMind's miniature worlds.

    import town_kit as TK
    TK.init(win_glow_mat, scale=0.01)          # 1 m in the real world = 1 cm here
    b = TK.building("b1", (x, y), yaw, floors=4, bays=3, wall=(0.86, 0.8, 0.68), shutters=(0.2, 0.35, 0.3), shop=True)
    TK.square_ring(radius, ...)

Each building: plaster body (PBR, tinted), floor cornices, recessed glass windows with light frames, sills, louvred
shutters, a wrought-iron balcony on the 2nd floor, a ground-floor shopfront with a striped awning, a slate mansard
roof with dormers, chimneys with pots. Parts share mesh data (instancing) so a whole square stays light.
Windows use one shared glowing-glass material, so a single keyframe lights the whole town at dusk.
"""
import math
import random

import bpy

_M = {}
S = 0.01  # metres per real metre (1:100)
_MESH = {}


def _link(o):
    sc = bpy.context.scene
    if o.name not in sc.collection.objects:
        sc.collection.objects.link(o)


def _cube_mesh(bevel=False):
    k = "_tk_cube_b" if bevel else "_tk_cube"
    if k not in _MESH:
        bpy.ops.mesh.primitive_cube_add(size=2.0)
        o = bpy.context.active_object
        me = o.data
        me.name = k
        bpy.data.objects.remove(o, do_unlink=True)
        _MESH[k] = me
    return _MESH[k]


def _paint(name, col, rough=0.6, metal=0.0, emit=None, estr=0.0):
    key = (name, tuple(round(c, 3) for c in col))
    if key in _M:
        return _M[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = estr
    _M[key] = m
    return m


def _box(name, par, center, size, mat):
    o = bpy.data.objects.new(name, _cube_mesh())
    _link(o)
    o.parent = par
    o.matrix_parent_inverse.identity()
    o.location = center
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    if not o.data.materials:
        o.data.materials.append(None)
    o.material_slots[0].link = "OBJECT"
    o.material_slots[0].material = mat
    return o


TEX = {}


def init(glass_mat, plaster_tex=None, slate_tex=None, scale=0.01):
    """glass_mat: shared window material (animate its emission to light the town). *_tex: optional PBR materials."""
    global S
    S = scale
    TEX["glass"] = glass_mat
    TEX["plaster"] = plaster_tex
    TEX["slate"] = slate_tex
    TEX["frame"] = _paint("tk_frame", (0.9, 0.88, 0.82), 0.5)
    TEX["sill"] = _paint("tk_sill", (0.78, 0.74, 0.66), 0.7)
    TEX["iron"] = _paint("tk_iron", (0.05, 0.05, 0.055), 0.4, 0.8)
    TEX["door"] = _paint("tk_door", (0.18, 0.1, 0.06), 0.45)
    TEX["chim"] = _paint("tk_chim", (0.55, 0.32, 0.22), 0.8)
    TEX["pot"] = _paint("tk_pot", (0.65, 0.35, 0.22), 0.7)
    TEX["shop_glass"] = glass_mat


def _wall_mat(col):
    if TEX.get("plaster") is None:
        return _paint(f"tk_wall_{col}", col, 0.85)
    # tint the shared PBR plaster per building (copy so tints don't collide)
    m = TEX["plaster"].copy()
    m.name = f"tk_wall_{round(col[0], 2)}_{round(col[1], 2)}_{round(col[2], 2)}"
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    src = p.inputs["Base Color"].links[0].from_socket if p.inputs["Base Color"].links else None
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.85
    mix.inputs[7].default_value = (*col, 1)
    if src is not None:
        nt.links.new(src, mix.inputs[6])
    else:
        mix.inputs[6].default_value = (1, 1, 1, 1)
    nt.links.new(mix.outputs[2], p.inputs["Base Color"])
    return m


AWNINGS = [((0.75, 0.12, 0.1), (0.95, 0.92, 0.85)), ((0.1, 0.3, 0.2), (0.92, 0.9, 0.82)), ((0.15, 0.2, 0.45), (0.93, 0.9, 0.82)),
           ((0.55, 0.35, 0.1), (0.95, 0.88, 0.7))]


def _striped(name, a, b):
    if name in _M:
        return _M[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    p.inputs["Roughness"].default_value = 0.8
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_profile = "SAW"
    wv.inputs["Scale"].default_value = 4.0
    nt.links.new(tc.outputs["Generated"], wv.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.interpolation = "CONSTANT"
    rp.color_ramp.elements[0].color = (*a, 1)
    rp.color_ramp.elements[1].position = 0.5
    rp.color_ramp.elements[1].color = (*b, 1)
    nt.links.new(wv.outputs["Fac"], rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], p.inputs["Base Color"])
    _M[name] = m
    return m


def building(name, pos, yaw, floors=4, bays=3, wall=(0.86, 0.8, 0.68), shutters=(0.2, 0.35, 0.3), shop=True, seed=0):
    """A Haussmann-ish facade block. pos=(x, y) of the front-centre at street level; the facade faces -Y before yaw."""
    rr = random.Random(seed or hash(name) % 9973)
    root = bpy.data.objects.new(name, None)
    _link(root)
    root.location = (pos[0], pos[1], 0.0)
    root.rotation_euler = (0, 0, yaw)
    bay = 3.4 * S
    fh = 3.2 * S
    gh = 4.0 * S
    W = bays * bay
    D = 9.0 * S
    H = gh + (floors - 1) * fh
    wm = _wall_mat(wall)
    _box(name + "_body", root, (0, D / 2, H / 2), (W, D, H), wm)
    # cornices between floors + a heavy top cornice
    for k in range(floors):
        z = gh + k * fh if k < floors - 1 else H
        _box(f"{name}_corn{k}", root, (0, -0.12 * S, z - 0.08 * S), (W + 0.3 * S, 0.45 * S, 0.22 * S if k < floors - 1 else 0.45 * S), TEX["sill"])
    sh_m = _paint(f"tk_shut_{shutters}", shutters, 0.6)
    for k in range(1, floors):
        z0 = gh + (k - 1) * fh
        for j in range(bays):
            x = -W / 2 + (j + 0.5) * bay
            ww, wh = 1.25 * S, 2.0 * S
            zc = z0 + 0.45 * S + wh / 2
            _box(f"{name}_gl{k}_{j}", root, (x, 0.12 * S, zc), (ww, 0.1 * S, wh), TEX["glass"])  # recessed glass
            fr = 0.14 * S
            for (dx, dz, sx, sz) in ((0, wh / 2, ww + 2 * fr, fr), (0, -wh / 2, ww + 2 * fr, fr), (-ww / 2, 0, fr, wh), (ww / 2, 0, fr, wh),
                                     (0, 0.15 * S, ww, fr * 0.6)):
                _box(f"{name}_fr{k}_{j}_{dx:.3f}_{dz:.3f}", root, (x + dx, -0.02 * S, zc + dz), (sx, 0.12 * S, sz), TEX["frame"])
            _box(f"{name}_sill{k}_{j}", root, (x, -0.2 * S, zc - wh / 2 - 0.12 * S), (ww + 0.5 * S, 0.4 * S, 0.14 * S), TEX["sill"])
            if rr.random() < 0.8:  # louvred shutters (some half-closed)
                ang = rr.choice([0.0, 0.0, 0.5])
                for s in (-1, 1):
                    sh = _box(f"{name}_sh{k}_{j}_{s}", root, (x + s * (ww / 2 + 0.35 * S), -0.08 * S, zc), (0.6 * S, 0.08 * S, wh), sh_m)
                    sh.rotation_euler = (0, 0, s * ang)
            if k == 2:  # wrought-iron balcony on the 'noble floor'
                _box(f"{name}_bal{j}", root, (x, -0.55 * S, z0 + 0.3 * S), (ww + 0.8 * S, 1.0 * S, 0.12 * S), TEX["sill"])
                _box(f"{name}_rail{j}", root, (x, -1.0 * S, z0 + 0.85 * S), (ww + 0.8 * S, 0.05 * S, 0.06 * S), TEX["iron"])
                for b in range(6):
                    _box(f"{name}_bar{j}_{b}", root, (x - (ww + 0.8 * S) / 2 + b * (ww + 0.8 * S) / 5, -1.0 * S, z0 + 0.6 * S),
                         (0.05 * S, 0.05 * S, 0.55 * S), TEX["iron"])
    # ground floor: shopfront with a striped awning, or a door + windows
    if shop:
        a, b = AWNINGS[rr.randrange(len(AWNINGS))]
        aw = _striped(f"tk_awn_{a}", a, b)
        _box(name + "_shopgl", root, (0, 0.1 * S, gh * 0.42), (W - 1.2 * S, 0.1 * S, gh * 0.6), TEX["shop_glass"])
        _box(name + "_shopfr", root, (0, -0.05 * S, gh * 0.78), (W - 0.8 * S, 0.2 * S, 0.35 * S), _paint(f"tk_shopfr_{a}", tuple(c * 0.7 for c in a), 0.5))
        awn = _box(name + "_awn", root, (0, -0.9 * S, gh * 0.72), (W - 1.0 * S, 1.8 * S, 0.06 * S), aw)
        awn.rotation_euler = (math.radians(-18), 0, 0)
    door_x = (W / 2 - 1.0 * S) if shop else 0.0
    _box(name + "_door", root, (door_x, 0.05 * S, 1.2 * S), (1.1 * S, 0.1 * S, 2.4 * S), TEX["door"])
    # mansard roof: steep slate front + dormers
    roof_h = 2.8 * S
    rf = _box(name + "_roof", root, (0, D / 2 + 0.6 * S, H + roof_h / 2), (W, D - 1.2 * S, roof_h), TEX["slate"] or _paint("tk_slate", (0.22, 0.24, 0.3), 0.6))
    front = _box(name + "_mans", root, (0, 0.7 * S, H + roof_h / 2), (W, 0.2 * S, roof_h * 1.05), TEX["slate"] or _paint("tk_slate", (0.22, 0.24, 0.3), 0.6))
    front.rotation_euler = (math.radians(-18), 0, 0)
    for j in range(bays):
        x = -W / 2 + (j + 0.5) * bay
        _box(f"{name}_dorm{j}", root, (x, 0.2 * S, H + 1.2 * S), (1.1 * S, 0.9 * S, 1.4 * S), TEX["frame"])
        _box(f"{name}_dgl{j}", root, (x, -0.26 * S, H + 1.15 * S), (0.7 * S, 0.05 * S, 0.9 * S), TEX["glass"])
    for c in range(rr.randint(1, 2)):
        cx = rr.uniform(-W / 2 + 0.8 * S, W / 2 - 0.8 * S)
        _box(f"{name}_chim{c}", root, (cx, D * 0.55, H + roof_h + 0.8 * S), (0.9 * S, 0.7 * S, 1.8 * S), TEX["chim"])
        for p in range(2):
            _box(f"{name}_pot{c}_{p}", root, (cx - 0.2 * S + p * 0.4 * S, D * 0.55, H + roof_h + 1.9 * S), (0.18 * S, 0.18 * S, 0.45 * S), TEX["pot"])
    return root, W, H


WALLS = [(0.93, 0.86, 0.72), (0.9, 0.78, 0.6), (0.88, 0.72, 0.66), (0.8, 0.84, 0.86), (0.94, 0.9, 0.8), (0.86, 0.74, 0.52)]
SHUTTERS = [(0.18, 0.34, 0.28), (0.2, 0.3, 0.45), (0.45, 0.2, 0.15), (0.3, 0.3, 0.32), (0.55, 0.5, 0.35)]


def square_ring(radius, arc=(0.12, 0.88), count=10, seed=3, centre=(0.0, 0.0)):
    """A crescent of buildings facing a square's centre."""
    rr = random.Random(seed)
    out = []
    for i in range(count):
        a = math.pi * (arc[0] + (arc[1] - arc[0]) * i / max(1, count - 1))
        x = centre[0] + radius * math.cos(a)
        y = centre[1] + radius * math.sin(a)
        yaw = a - math.pi / 2
        b = building(f"tb{i}", (x, y), yaw, floors=rr.choice([4, 5, 5, 6]), bays=rr.choice([2, 3, 3, 4]), wall=WALLS[i % len(WALLS)],
                     shutters=SHUTTERS[rr.randrange(len(SHUTTERS))], shop=rr.random() < 0.75, seed=seed * 100 + i)
        out.append(b)
    return out
