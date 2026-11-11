"""Real-3D plates for "The Leaning Tower of Pisa should have collapsed... and a WAR saved it" (The DailyMind.).

v2 of the Blender pipeline (after the airplane video): REAL 3D toon characters (blender/toon3d.py, no flat sprites),
REAL rigid-body physics (Bullet, baked: falling stones, scaffolding, crates, soil grains, lead ingots),
cinematic cameras (eased paths + organic handheld drift + DOF + motion blur), dusk/floodlit "classic dark" look.
Text, slams, stamps, splats, music/SFX and the end card are composited later by ultimate/make_pisa3d.py.

Run (bpy module):   python pisa3d.py -- SCENE OUTDIR [RES_PCT=100] [SAMPLES=64] [ENGINE=EEVEE] [F0] [F1]
Run (Blender app):  blender -b -P pisa3d.py -- SCENE OUTDIR ...        (RTX PC: PLATE_FMT=MP4)
Stills:             STILL_FRAMES=1,60,120 python pisa3d.py -- SCENE OUTDIR 30 16
"""
import json
import math
import os
import random
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SCENE = int(argv[0]) if argv else 0
OUTDIR = argv[1] if len(argv) > 1 else "/tmp/plates"
RES = int(argv[2]) if len(argv) > 2 else 100
SAMPLES = int(argv[3]) if len(argv) > 3 else 64
ENGINE = argv[4] if len(argv) > 4 else "EEVEE"
OUTFMT = os.environ.get("PLATE_FMT", "PNG")
STILLS = [int(x) for x in os.environ.get("STILL_FRAMES", "").split(",") if x.strip()]
ROOT = os.path.dirname(HERE)
PLAN = json.load(open(os.path.join(ROOT, "pisa", "plan.json")))
DUR, START, ABS = PLAN["durs"], PLAN["starts"], PLAN["abs"]
FPS = 30
NF = int(math.ceil(DUR[SCENE] * FPS)) + 1
F0 = int(argv[5]) if len(argv) > 5 else 1
F1 = int(argv[6]) if len(argv) > 6 else NF

bpy.ops.wm.read_factory_settings(use_empty=True)
from toon3d import Toon  # noqa: E402  (after the factory reset)

SC = bpy.context.scene
SC.render.fps = FPS
SC.frame_start, SC.frame_end = 1, NF
SC.render.resolution_x, SC.render.resolution_y = 1080, 1920
SC.render.resolution_percentage = RES
R = random.Random(SCENE * 101 + 7)


def cue(name):
    """Seconds into THIS scene at which the narrator says the cue word."""
    return ABS[name] - START[SCENE]


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ease_io(x):  # smoother (quintic) for camera moves
    x = max(0.0, min(1.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)


def back_out(x, s=1.7):  # overshoot then settle: fun, springy arrivals
    x = max(0.0, min(1.0, x)) - 1
    return 1 + x * x * ((s + 1) * x + s)


def spring(t, at, amp=1.0, freq=2.5, damp=5.0):
    k = t - at
    return 0.0 if k < 0 else amp * math.exp(-damp * k) * math.cos(2 * math.pi * freq * k)


def lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b)) if isinstance(a, tuple) else a + (b - a) * k


def frames():
    for f in range(1, NF + 1):
        yield f, (f - 1) / FPS


# ---------------------------------------------------------------- materials
def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


def pbr(name, col, rough=0.5, metal=0.0, emit=None, estr=0.0, alpha=1.0):
    m, nt, out = new_mat(name)
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = estr
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
        for attr, val in (("blend_method", "BLEND"), ("surface_render_method", "BLENDED")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def emission(name, col, strength):
    m, nt, out = new_mat(name)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


def noisy(name, col_a, col_b, scale=8.0, rough=0.7, bump=0.15, detail=6.0, metal=0.0, coords="Object"):
    m, nt, out = new_mat(name)
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail
    nt.links.new(tc.outputs[coords], nz.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].color = (*col_a, 1)
    rp.color_ramp.elements[1].color = (*col_b, 1)
    nt.links.new(nz.outputs["Fac"], rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], p.inputs["Base Color"])
    if bump:
        b = nt.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = bump
        nt.links.new(nz.outputs["Fac"], b.inputs["Height"])
        nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


M = {}


def mats():
    M["marble"] = noisy("marble", (0.86, 0.82, 0.72), (0.97, 0.94, 0.86), scale=3.0, rough=0.42, bump=0.05)
    M["marble_in"] = noisy("marble_in", (0.55, 0.52, 0.46), (0.7, 0.67, 0.6), scale=4.0, rough=0.6, bump=0.08)
    M["grass"] = noisy("grass", (0.03, 0.07, 0.02), (0.07, 0.14, 0.04), scale=0.6, rough=0.95, bump=0.3, coords="Generated")
    M["sand"] = noisy("sand", (0.36, 0.27, 0.17), (0.52, 0.41, 0.27), scale=1.5, rough=0.95, bump=0.4, coords="Generated")
    M["mud"] = noisy("mud", (0.22, 0.15, 0.09), (0.36, 0.26, 0.16), scale=2.0, rough=0.35, bump=0.3, coords="Generated")
    M["puddle"] = pbr("puddle", (0.05, 0.05, 0.06), rough=0.03)
    M["stone"] = noisy("stone", (0.62, 0.58, 0.5), (0.8, 0.76, 0.66), scale=6.0, rough=0.8, bump=0.3)
    M["wood"] = noisy("wood", (0.33, 0.2, 0.1), (0.5, 0.33, 0.17), scale=14.0, rough=0.75, bump=0.1)
    M["lead"] = noisy("lead", (0.2, 0.21, 0.24), (0.33, 0.34, 0.38), scale=9.0, rough=0.35, metal=0.9, bump=0.05)
    M["soil1"] = noisy("soil1", (0.32, 0.22, 0.12), (0.45, 0.33, 0.2), scale=5.0, rough=0.9, bump=0.3)
    M["soil2"] = noisy("soil2", (0.5, 0.4, 0.26), (0.62, 0.5, 0.33), scale=5.0, rough=0.9, bump=0.3)
    M["glow_gold"] = emission("glow_gold", (1.0, 0.72, 0.15), 6.0)
    M["red"] = pbr("red", (0.75, 0.06, 0.05), 0.4)
    M["white"] = pbr("white", (0.92, 0.92, 0.9), 0.4)
    M["roof"] = noisy("roof", (0.45, 0.18, 0.1), (0.6, 0.27, 0.15), scale=10.0, rough=0.8)
    M["banana"] = noisy("banana", (0.98, 0.78, 0.08), (1.0, 0.86, 0.25), scale=3.0, rough=0.45, bump=0.03)
    M["banana_tip"] = pbr("banana_tip", (0.25, 0.16, 0.05), 0.6)


# ---------------------------------------------------------------- objects
def link(o):
    if o.name not in SC.collection.objects:
        SC.collection.objects.link(o)
    return o


def mesh_obj(name, verts, faces, mat=None, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    link(o)
    if mat:
        o.data.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return o


def prim(op, name, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), mat=None, bevel=0.0, smooth=False, **kw):
    op(location=loc, rotation=rot, **kw)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    if mat:
        o.data.materials.append(mat)
    if bevel:
        bv = o.modifiers.new("bevel", "BEVEL")
        bv.width = bevel
        bv.segments = 3
        bv.limit_method = "NONE"
    if smooth:
        bpy.ops.object.shade_smooth()
    return o


def box(name, center, size, mat, bevel=0.0, rot=(0, 0, 0)):
    return prim(bpy.ops.mesh.primitive_cube_add, name, center, (size[0] / 2, size[1] / 2, size[2] / 2), rot=rot, mat=mat, bevel=bevel)


def cyl(name, center, r, h, mat, verts=48, rot=(0, 0, 0), smooth=True):
    o = prim(bpy.ops.mesh.primitive_cylinder_add, name, center, (r, r, h / 2), rot=rot, mat=mat, vertices=verts)
    if smooth:
        bpy.ops.object.shade_smooth()
    return o


def sphere(name, center, r, mat, scale=None, segs=24):
    o = prim(bpy.ops.mesh.primitive_uv_sphere_add, name, center, scale or (r, r, r), mat=mat, segments=segs, ring_count=segs // 2)
    bpy.ops.object.shade_smooth()
    return o


def instance(src, name, loc, rot=(0, 0, 0), scale=None):
    o = bpy.data.objects.new(name, src.data)
    link(o)
    o.location = loc
    o.rotation_euler = rot
    o.scale = scale or src.scale
    for mod in src.modifiers:
        if mod.type == "BEVEL":
            b = o.modifiers.new("bevel", "BEVEL")
            b.width, b.segments, b.limit_method = mod.width, mod.segments, "NONE"
    return o


def empty(name, loc=(0, 0, 0), par=None):
    o = bpy.data.objects.new(name, None)
    link(o)
    if par:
        o.parent = par
        o.matrix_parent_inverse.identity()
    o.location = loc
    return o


def parent(child, par):
    child.parent = par
    child.matrix_parent_inverse.identity()


def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None:
        o.location = loc
        o.keyframe_insert("location", frame=f)
    if rot is not None:
        o.rotation_euler = rot
        o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        o.scale = scale
        o.keyframe_insert("scale", frame=f)


def show(o, f, visible):
    o.hide_render = not visible
    o.keyframe_insert("hide_render", frame=f)
    for c in o.children:
        show(c, f, visible)


def appear(o, t_on, base_scale=None, pop=0.35):
    """Pop an object in with a springy overshoot at t_on (scale 0 -> 1.15 -> 1)."""
    s0 = base_scale or tuple(o.scale)
    for f, t in frames():
        k = (t - t_on) / pop
        s = 0.0001 if k <= 0 else back_out(min(1.0, k))
        key(o, f, scale=tuple(max(1e-4, v * s) for v in s0))


# ---------------------------------------------------------------- physics (Bullet rigid bodies, baked)
def rb_world():
    if SC.rigidbody_world is None:
        bpy.ops.rigidbody.world_add()
    w = SC.rigidbody_world
    w.point_cache.frame_start = 1
    w.point_cache.frame_end = NF
    w.substeps_per_frame = 12
    w.solver_iterations = 25
    return w


def rb(o, active=True, mass=1.0, friction=0.7, bounce=0.15, shape="CONVEX_HULL", release=None, damp=0.1):
    """Add a rigid body. release = time (s) until which it is held kinematic (animated by keyframes)."""
    rb_world()
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.rigidbody.object_add()
    b = o.rigid_body
    b.type = "ACTIVE" if active else "PASSIVE"
    b.mass = mass
    b.friction = friction
    b.restitution = bounce
    b.collision_shape = shape
    b.linear_damping = damp
    b.angular_damping = damp
    b.collision_margin = 0.01
    if release is not None:
        b.kinematic = True
        b.keyframe_insert("kinematic", frame=1)
        rf = max(2, int(release * FPS) + 1)
        b.keyframe_insert("kinematic", frame=rf - 1)
        b.kinematic = False
        b.keyframe_insert("kinematic", frame=rf)
    return o


def rb_bake():
    if SC.rigidbody_world is None:
        return
    end = max(STILLS) if STILLS else min(F1, NF)
    SC.rigidbody_world.point_cache.frame_end = max(end, 2)
    SC.frame_set(1)
    with bpy.context.temp_override(scene=SC, point_cache=SC.rigidbody_world.point_cache):
        bpy.ops.ptcache.bake(bake=True)


# ---------------------------------------------------------------- the tower (generic 8-storey romanesque bell tower)
FLOOR_H = [10.5, 6.3, 6.3, 6.3, 6.3, 6.3, 6.3, 5.6]  # ~54 m
R_OUT, R_CORE = 7.6, 6.1


def tower(name="T", floors=8, lean=0.0, loc=(0, 0, 0)):
    """Returns dict(base, joints[k], groups[k], top). base pivots at the ground; joint k sits on top of floor k-1 and
    carries floors k..; rotating joints about X (the lean axis, tower leans towards -Y... we lean towards +X) gives
    the famous banana curve. Lean = rotation about Y (towards +X)."""
    base = empty(name + "_base", loc)
    base.rotation_euler = (0, math.radians(lean), 0)
    col_src = cyl(name + "_colsrc", (0, 0, -100), 0.26, 1.0, M["marble"], verts=16)
    joints, groups = [], []
    par = base
    z = 0.0
    for k in range(floors):
        h = FLOOR_H[k]
        j = empty(f"{name}_j{k}", (0, 0, 0 if k == 0 else FLOOR_H[k - 1]), par)
        g = empty(f"{name}_g{k}", (0, 0, 0), j)
        joints.append(j)
        groups.append(g)
        belfry = k == 7
        rc = 4.4 if belfry else R_CORE
        ro = 4.9 if belfry else R_OUT
        core = cyl(f"{name}_core{k}", (0, 0, h / 2), rc + (0.9 if k == 0 else 0), h, M["marble_in"] if k else M["marble"], verts=64)
        parent(core, g)
        slab = cyl(f"{name}_slab{k}", (0, 0, h - 0.25), ro + 0.35, 0.5, M["marble"], verts=72)
        parent(slab, g)
        band = cyl(f"{name}_band{k}", (0, 0, h - 0.62), ro + 0.15, 0.25, M["marble"], verts=72)
        parent(band, g)
        if k == 0:
            plinth = cyl(f"{name}_plinth", (0, 0, 0.5), R_OUT + 0.5, 1.0, M["marble"], verts=72)
            parent(plinth, g)
        n = 15 if k == 0 else (12 if belfry else 24)
        col_h = h - (2.2 if not belfry else 2.0) - (1.0 if k == 0 else 0.5)
        z0 = (1.0 if k == 0 else 0.0) + col_h / 2
        bay_r = (ro if k else R_CORE + 0.9) * math.sin(math.pi / n)
        for i in range(n):
            a = 2 * math.pi * i / n
            r = ro if k else R_CORE + 1.0
            c = instance(col_src, f"{name}_col{k}_{i}", (r * math.cos(a), r * math.sin(a), z0), scale=(0.26 if k else 0.4, 0.26 if k else 0.4, col_h / 2 + 0.01))
            parent(c, g)
            # arch between this column and the next
            a2 = a + math.pi / n
            arc = arch(f"{name}_arch{k}_{i}", bay_r, 0.22 if k else 0.3, M["marble"])
            arc.location = (r * math.cos(a2) * math.cos(math.pi / n), r * math.sin(a2) * math.cos(math.pi / n), z0 + col_h / 2)
            arc.rotation_euler = (math.pi / 2, 0, a2 + math.pi / 2)
            parent(arc, g)
        if belfry:
            cap = cyl(f"{name}_cap", (0, 0, h + 0.25), 4.6, 0.5, M["marble"], verts=64)
            parent(cap, g)
        par = j
        z += h
    top = empty(name + "_top", (0, 0, FLOOR_H[floors - 1]), joints[-1])
    bpy.data.objects.remove(col_src, do_unlink=True)
    return dict(base=base, joints=joints, groups=groups, top=top)


_ARCH_MESH = {}


def arch(name, r, thick, mat):
    key_ = (round(r, 3), round(thick, 3))
    if key_ not in _ARCH_MESH:
        n = 16
        verts, faces = [], []
        for i in range(n + 1):
            a = math.pi * i / n
            for rr in (r - thick, r + thick * 0.6):
                for y in (-0.35, 0.35):
                    verts.append((rr * math.cos(a), y, rr * math.sin(a)))
        for i in range(n):
            b0, b1 = 4 * i, 4 * (i + 1)
            faces += [(b0, b1, b1 + 1, b0 + 1), (b0 + 2, b0 + 3, b1 + 3, b1 + 2), (b0, b0 + 2, b1 + 2, b1), (b0 + 1, b1 + 1, b1 + 3, b0 + 3)]
        me = bpy.data.meshes.new("archmesh")
        me.from_pydata(verts, [], faces)
        me.update()
        for p in me.polygons:
            p.use_smooth = True
        me.materials.append(mat)
        _ARCH_MESH[key_] = me
    o = bpy.data.objects.new(name, _ARCH_MESH[key_])
    link(o)
    return o


def set_lean(T, f, lean_deg, curve_deg=0.0, upto=8):
    """lean of the whole tower + extra curvature: every joint above the 3rd floor bends back (the builders' trick)."""
    key(T["base"], f, rot=(0, math.radians(lean_deg), 0))
    for k, j in enumerate(T["joints"]):
        bend = -curve_deg / 5.0 if 3 <= k < upto else 0.0
        key(j, f, rot=(0, math.radians(bend), 0))


# ---------------------------------------------------------------- world, piazza, lights, camera
def world_dusk(top=(0.02, 0.03, 0.09), horizon=(0.55, 0.3, 0.2), strength=1.0, fog=0.0):
    w = bpy.data.worlds.new("dusk")
    SC.world = w
    w.use_nodes = True
    nt = w.node_tree
    bgn = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    rp = nt.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].position = 0.0
    rp.color_ramp.elements[0].color = (*horizon, 1)
    mid = rp.color_ramp.elements.new(0.12)
    mid.color = (*tuple(0.5 * h + 0.5 * t_ for h, t_ in zip(horizon, top)), 1)
    rp.color_ramp.elements[2].position = 0.42
    rp.color_ramp.elements[2].color = (*top, 1)
    nt.links.new(sep.outputs["Z"], rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], bgn.inputs["Color"])
    bgn.inputs["Strength"].default_value = strength
    if fog:
        vs = nt.nodes.new("ShaderNodeVolumeScatter")
        vs.inputs["Density"].default_value = fog
        nt.links.new(vs.outputs[0], nt.nodes["World Output"].inputs["Volume"])
    return w, rp, bgn


def light(kind, loc, energy, col=(1, 1, 1), size=1.0, rot=(0, 0, 0), spot_deg=None):
    bpy.ops.object.light_add(type=kind, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.data.energy = energy
    o.data.color = col
    if kind == "AREA":
        o.data.size = size
    elif kind in ("POINT", "SPOT"):
        o.data.shadow_soft_size = size
        if kind == "SPOT" and spot_deg:
            o.data.spot_size = math.radians(spot_deg)
            o.data.spot_blend = 0.6
    elif kind == "SUN":
        o.data.angle = math.radians(size)
    return o


def aim_at(o, target):
    tr = o.constraints.new("TRACK_TO")
    tr.target = target
    tr.track_axis = "TRACK_NEGATIVE_Z"
    tr.up_axis = "UP_Y"


def floodlights(T_loc=(0, 0, 0), energy=90000, warm=(1.0, 0.7, 0.4)):
    tgt = empty("flood_tgt", (T_loc[0], T_loc[1], 30))
    for i, a in enumerate((-55, 0, 55, 180)):
        r = 16
        L = light("SPOT", (T_loc[0] + r * math.sin(math.radians(a)), T_loc[1] - r * math.cos(math.radians(a)), 0.5), energy, warm, 0.6, spot_deg=38)
        aim_at(L, tgt)


def ground(mat, size=600):
    g = prim(bpy.ops.mesh.primitive_plane_add, "ground", (0, 0, 0), mat=mat, size=size)
    return g


def piazza(cathedral=True):
    ground(M["grass"])
    pave = cyl("pave", (0, 0, 0.04), 12.5, 0.08, M["marble"], verts=96)
    path = box("path", (0, -40, 0.03), (6, 60, 0.06), M["stone"])
    if cathedral:  # generic romanesque cathedral + round baptistery far behind (silhouettes against the dusk sky)
        cx, cy = -70, 95
        box("nave", (cx, cy, 14), (26, 90, 28), M["marble"])
        roof = prim(bpy.ops.mesh.primitive_cylinder_add, "naveroof", (cx, cy, 28), (13, 13, 45), rot=(math.pi / 2, 0, 0), mat=M["roof"], vertices=3)
        roof.rotation_euler = (math.pi / 2, 0, 0)
        roof.scale = (13, 5, 45)
        box("transept", (cx, cy + 15, 12), (60, 18, 24), M["marble"])
        cyl("drum", (cx, cy + 15, 30), 8, 8, M["marble"])
        sphere("dome", (cx, cy + 15, 34), 8, M["roof"], scale=(8, 8, 6))
        cyl("bapt", (-150, 60, 14), 18, 28, M["marble"], verts=64)
        sphere("baptdome", (-150, 60, 28), 18, M["roof"], scale=(18, 18, 12))
    return pave, path


def stars(n=400, r=900):
    m = emission("star", (1.0, 0.95, 0.85), 8.0)
    src = sphere("star_src", (0, 0, -999), 1.0, m, segs=8)
    rr = random.Random(5)
    for i in range(n):
        az = rr.uniform(0, 2 * math.pi)
        el = math.radians(rr.uniform(12, 85))
        s_ = rr.uniform(0.6, 1.8)
        instance(src, f"star{i}", (r * math.cos(el) * math.cos(az), r * math.cos(el) * math.sin(az), r * math.sin(el)), scale=(s_, s_, s_))
    moon = sphere("moon", (-260, 700, 330), 22, emission("moonm", (1.0, 0.95, 0.82), 6.0))
    return moon


def cypress(name, loc, h=9.0):
    m = noisy(name + "m", (0.03, 0.09, 0.04), (0.07, 0.17, 0.07), scale=4, rough=0.9, bump=0.5)
    o = prim(bpy.ops.mesh.primitive_uv_sphere_add, name, (loc[0], loc[1], h / 2), (1.1, 1.1, h / 2), mat=m, segments=16, ring_count=10)
    bpy.ops.object.shade_smooth()
    return o


def lamp(name, loc, energy=400):
    post = cyl(name + "p", (loc[0], loc[1], 2.0), 0.08, 4.0, M["lead"], verts=12)
    glob = sphere(name + "g", (loc[0], loc[1], 4.15), 0.28, emission(name + "e", (1.0, 0.78, 0.45), 12.0))
    light("POINT", (loc[0], loc[1], 4.0), energy, (1.0, 0.72, 0.4), 0.3)
    return post, glob


def town(night=True, medieval=False):
    """Rich backdrop: crenellated city wall, rows of houses with lit windows, cypresses, lamps, distant hills."""
    wall_m = noisy("wallm", (0.42, 0.33, 0.25), (0.55, 0.45, 0.34), scale=2, rough=0.9, bump=0.3)
    for i in range(16):
        x = -160 + i * 22
        box(f"wall{i}", (x, 150, 6), (22, 3, 12), wall_m)
        box(f"cren{i}", (x - 5, 150, 13), (5, 3, 2.5), wall_m)
        box(f"crenb{i}", (x + 6, 150, 13), (5, 3, 2.5), wall_m)
    win_m = emission("winm", (1.0, 0.7, 0.35), 6.0 if night else 0.0)
    rr = random.Random(11)
    house_cols = [(0.75, 0.5, 0.3), (0.85, 0.65, 0.4), (0.7, 0.4, 0.28), (0.82, 0.72, 0.55)]
    for i in range(22):
        x = -170 + i * 16 + rr.uniform(-3, 3)
        y = 175 + rr.uniform(0, 20)
        h = rr.uniform(10, 22)
        hm = noisy(f"hm{i}", house_cols[i % 4], tuple(min(1, c * 1.15) for c in house_cols[i % 4]), scale=3, rough=0.9, bump=0.2)
        box(f"house{i}", (x, y, h / 2), (13, 10, h), hm)
        rf = prim(bpy.ops.mesh.primitive_cylinder_add, f"hroof{i}", (x, y, h + 1.5), (7.5, 6, 1.5), rot=(0, math.pi / 2, 0), mat=M["roof"], vertices=3)
        rf.rotation_euler = (0, math.pi / 2, math.pi / 2)
        if night:
            for w_ in range(rr.randint(1, 4)):
                box(f"hw{i}_{w_}", (x + rr.uniform(-4, 4), y - 5.1, rr.uniform(3, h - 2)), (1.4, 0.2, 2.0), win_m)
    hill_m = noisy("hillm", (0.05, 0.08, 0.06), (0.09, 0.13, 0.09), scale=1, rough=1.0)
    for i in range(6):
        sphere(f"hill{i}", (-400 + i * 160, 600, -60), 1, hill_m, scale=(220, 120, 160))
    for i, (x, y) in enumerate(((28, 35), (34, 30), (40, 38), (-30, 40), (-38, 32), (46, -10), (-45, -5), (52, 20))):
        cypress(f"cyp{i}", (x, y), rr.uniform(8, 12))
    if not medieval:
        for i, (x, y) in enumerate(((22, -30), (-20, -26), (26, 12), (-25, 8))):
            lamp(f"lamp{i}", (x, y))


def crowd(n=10, center=(0, -26), radius=(18, 6), seed=3, scale=1.5, face_to=(0, 0)):
    """Background tourists: varied colours, idle bounce, looking up at the tower."""
    rr = random.Random(seed)
    cols = [(0.9, 0.3, 0.3), (0.3, 0.6, 0.9), (0.95, 0.8, 0.2), (0.4, 0.8, 0.5), (0.8, 0.45, 0.85), (1.0, 0.55, 0.2)]
    skins = [(0.96, 0.76, 0.62), (0.78, 0.55, 0.38), (0.55, 0.36, 0.24), (0.98, 0.84, 0.72)]
    out = []
    for i in range(n):
        p = (center[0] + rr.uniform(-radius[0], radius[0]), center[1] + rr.uniform(-radius[1], radius[1]), 0)
        tn = Toon(f"cr{seed}_{i}", skin=skins[i % 4], coat=cols[i % 6], hair=(rr.uniform(0.05, 0.6),) * 1 + (0.1, 0.05),
                  hairstyle=rr.choice(["short", "long", "short", "bald"]), hat=rr.choice([None, None, "beret", "cap"]),
                  hat_col=cols[(i + 2) % 6], outline=0.01)
        yaw = math.degrees(math.atan2(-(face_to[0] - p[0]), (face_to[1] - p[1]))) + 180
        place(tn, p, yaw, scale * rr.uniform(0.9, 1.08))
        out.append((tn, rr.uniform(0, 6)))
    return out


def pose_crowd(cr, f, t, mood="happy"):
    for tn, ph in cr:
        if mood == "cheer":
            tn.pose(f, t, arm_side=(140 + 20 * math.sin(t * 8 + ph), 140 + 20 * math.cos(t * 8 + ph)), arms=(0, 0), eyes="happy", mouth="grin",
                    jump=0.25 * abs(math.sin(t * 6 + ph)), head=(0, 15, 0))
        elif mood == "scared":
            tn.pose(f, t, arms=(150, 150), arm_side=(-15, -15), eyes="wide", mouth="O", brows=1, look=(0, 1), head=(0, 20, 0),
                    bounce=0.03 * abs(math.sin(t * 9 + ph)))
        elif mood == "sad":
            tn.pose(f, t, eyes="open", mouth="frown", brows=-0.3, look=(0, -0.3), head=(0, -8, 0))
        else:
            tn.pose(f, t, arms=(10 * math.sin(t * 2 + ph), -10 * math.sin(t * 2 + ph)), eyes="open", mouth="smile", look=(0.3 * math.sin(ph), 0.7),
                    head=(10 * math.sin(t * 0.7 + ph), 20, 0))


def camera(lens=30, fstop=4.0, focus=None):
    bpy.ops.object.camera_add(location=(0, -30, 2))
    cam = bpy.context.active_object
    SC.camera = cam
    cam.data.lens = lens
    cam.data.sensor_width = 36
    cam.data.clip_end = 5000
    cam.data.clip_start = 0.05
    aim = empty("aim")
    aim_at(cam, aim)
    if focus is not None:
        cam.data.dof.use_dof = True
        cam.data.dof.focus_object = focus
        cam.data.dof.aperture_fstop = fstop
    return cam, aim


def drift(t, amp=0.06, seed=0):
    """Organic handheld float (sum of slow sines) — the camera breathes instead of sliding on rails."""
    s = seed * 1.7
    return (amp * (math.sin(t * 0.9 + s) + 0.5 * math.sin(t * 2.3 + 2 * s)),
            amp * 0.6 * math.sin(t * 1.3 + 3 * s),
            amp * (math.sin(t * 1.1 + 4 * s) + 0.4 * math.sin(t * 2.9 + s)))


def shake(t, at, amp=0.25, dur=0.5):
    k = t - at
    if not 0 <= k < dur:
        return (0.0, 0.0, 0.0)
    e = (1 - k / dur) ** 2
    return (amp * e * math.sin(k * 95), amp * e * math.cos(k * 81), amp * e * math.sin(k * 63))


def animate_cam(cam, aim, fn, lens_fn=None, roll_fn=None):
    for f, t in frames():
        c, a = fn(t)
        key(cam, f, loc=c)
        key(aim, f, loc=a)
        if lens_fn:
            cam.data.lens = lens_fn(t)
            cam.data.keyframe_insert("lens", frame=f)
        if roll_fn:
            cam.delta_rotation_euler = (0, 0, math.radians(roll_fn(t)))
            cam.keyframe_insert("delta_rotation_euler", frame=f)


def add(*vs):
    return tuple(sum(c) for c in zip(*vs))


def place(toon, loc, yaw_deg=0.0, scale=None):
    toon.root.location = loc
    toon.root.rotation_euler = (0, 0, math.radians(yaw_deg))
    if scale:
        toon.root.scale = (scale, scale, scale)


def walk_path(toon, f, t, p0, p1, t0, t1, stride=0.55):
    """Move a toon from p0 to p1 between t0..t1 (eased) and return the walk phase from the distance (feet never slide)."""
    k = ease((t - t0) / max(1e-3, t1 - t0))
    p = lerp(p0, p1, k)
    key(toon.root, f, loc=p)
    d = math.dist(p0, p) / stride
    return d if 0 < k < 1 else None


def smoke_mat(name, col=(0.8, 0.72, 0.6), density=1.2):
    m, nt, out = new_mat(name)
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Color"].default_value = (*col, 1)
    v.inputs["Density"].default_value = density
    # soft edges: density falls off towards the sphere surface
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    nt.links.new(tc.outputs["Object"], ln.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.5
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "SUBTRACT"
    nt.links.new(nz.outputs["Fac"], mx.inputs[0])
    nt.links.new(ln.outputs["Value"], mx.inputs[1])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.use_clamp = False
    mul.inputs[1].default_value = density * 3
    nt.links.new(mx.outputs[0], mul.inputs[0])
    cl = nt.nodes.new("ShaderNodeMath")
    cl.operation = "MAXIMUM"
    cl.inputs[1].default_value = 0.0
    nt.links.new(mul.outputs[0], cl.inputs[0])
    nt.links.new(cl.outputs[0], v.inputs["Density"])
    nt.links.new(v.outputs[0], out.inputs["Volume"])
    return m


def dust_puff(name, loc, t_on, n=10, col=(0.8, 0.72, 0.6), spread=2.5, size=0.8):
    """Soft volumetric dust clouds that burst out, billow up and thin away."""
    m = smoke_mat(name + "_m", col)
    rr = random.Random(hash(name) % 9999)
    for i in range(n):
        a = rr.uniform(0, 2 * math.pi)
        v = rr.uniform(0.5, 1.0) * spread
        up = rr.uniform(0.3, 1.2)
        s0 = size * rr.uniform(0.8, 1.5)
        o = sphere(f"{name}{i}", loc, 1.0, m, segs=12)
        for f, t in frames():
            k = t - t_on
            if k < 0:
                key(o, f, loc=loc, scale=(1e-4,) * 3)
                continue
            e = 1 - math.exp(-3 * k)
            p = (loc[0] + math.cos(a) * v * e, loc[1] + math.sin(a) * v * e, loc[2] + up * e + 0.5 * k)
            sc_ = s0 * (0.4 + 1.6 * e) * (1.0 if k < 1.2 else max(0.0, 1 - (k - 1.2) / 1.5))
            key(o, f, loc=p, scale=(max(1e-4, sc_),) * 3)


# ================================================================= scenes
def sc0_hook():
    """Night, floodlit tower. Close on tourists doing the famous 'hold up the tower' pose; on 'collapsed' it CREAKS,
    the camera whips up as stones break off the top, follows them down (real physics) and they crash beside the
    tourists, who leap back. On 'war' the tower freezes with a springy settle."""
    world_dusk(top=(0.008, 0.012, 0.045), horizon=(0.09, 0.07, 0.16), strength=1.0)
    piazza(cathedral=False)
    stars()
    town(night=True)
    T = tower(lean=4.0)
    tc, tw = cue("collapsed"), cue("war0")
    for f, t in frames():
        k = ease((t - tc) / 1.4)
        lean = 4.0 + 2.6 * k - 1.0 * ease((t - tw) / 0.5) + spring(t, tw, 0.5, 2.2, 4.0)
        lean += 0.12 * math.sin(t * 40) * math.exp(-3 * max(0.0, t - tc)) * (t > tc)
        set_lean(T, f, lean)
    floodlights()
    light("SUN", (0, 0, 50), 0.6, (0.5, 0.6, 1.0), 2, rot=(math.radians(60), 0, math.radians(140)))
    face = light("SPOT", (15.5, -15.5, 5.0), 3000, (1.0, 0.82, 0.62), 1.0, spot_deg=22)  # key light on the tourists' faces
    aim_at(face, empty("face_tgt", (11, -7, 1.6)))
    ground_rb = box("ground_rb", (0, 0, -0.5), (200, 200, 1.0), None)
    ground_rb.hide_render = True
    rb(ground_rb, active=False, shape="BOX")
    rel = tc + 0.25
    SC.frame_set(int(rel * FPS) + 1)
    top = T["top"].matrix_world.translation.copy()
    rocks = []
    for i in range(7):
        a = math.radians(-50 + i * 15)
        p = (top.x + 5.2 * math.cos(a) + 0.8, top.y + 5.2 * math.sin(a) - 1.0, top.z - 0.8 - 1.2 * (i % 2))
        s = box(f"rock{i}", p, (1.7, 1.2, 1.0), M["marble"], bevel=0.1, rot=(R.uniform(0, 1), R.uniform(0, 1), R.uniform(0, 3)))
        rb(s, mass=120, bounce=0.3, friction=0.8, release=rel + i * 0.06)
        rocks.append(p)
    z0 = sum(p[2] for p in rocks) / len(rocks)
    land = rel + math.sqrt(2 * (z0 - 0.5) / 9.81)
    tour = [Toon("tA", coat=(0.95, 0.4, 0.15), hair=(0.3, 0.18, 0.08), hat="beret", hat_col=(0.15, 0.4, 0.8)),
            Toon("tB", skin=(0.78, 0.55, 0.38), coat=(0.2, 0.75, 0.6), hairstyle="long", hair=(0.08, 0.05, 0.03)),
            Toon("tC", skin=(0.98, 0.82, 0.7), coat=(0.95, 0.75, 0.15), hair=(0.85, 0.65, 0.25))]
    spots = [(10.6, -5.6, 0), (12.6, -7.6, 0), (10.2, -10.4, 0)]
    yaws = [-38, -32, 25]
    for i, tt_ in enumerate(tour):
        place(tt_, spots[i], yaws[i], 1.6)
    for f, t in frames():
        scared = tc + 0.15 < t
        hit = t > land - 0.1
        for i, tt_ in enumerate(tour):
            back = 0.0
            if hit:  # leap back from the crash with a squash-and-stretch hop
                k = t - land + 0.1
                jump = max(0.0, 1.6 * k - 4.9 * k * k) * 0.5
                back = min(1.2, 3 * k)
            else:
                jump = 0.0
            p = spots[i]
            key(tt_.root, f, loc=(p[0] + back * 0.8, p[1] - back * 0.6, 0))
            if i < 2:
                strain = scared and not hit
                tt_.pose(f, t, arms=(150 - (20 if strain else 0) * abs(math.sin(t * 18 + i)), 150) if not hit else (120, 120),
                         arm_side=(25, 25) if not hit else (60, 60), lean=-14 if strain else -6,
                         eyes="closed" if strain else ("wide" if hit else "happy"), mouth="O" if (strain or hit) else "grin",
                         brows=-1 if strain else (1 if hit else 0.5), squash=1 - 0.06 * abs(math.sin(t * 14 + i)) if strain else 1.0,
                         head=(0, -12 if not hit else 10, 0), jump=jump, look=(0, 0.6))
            else:  # the friend taking the photo: phone up, then hands on cheeks when it creaks
                tt_.pose(f, t, arms=(85, 85) if not scared else (150, 150), arm_side=(6, 6) if not scared else (-20, -20),
                         eyes="wide" if scared else "happy", mouth="O" if scared else "grin", brows=1 if scared else 0.3,
                         look=(0.5, 0.8) if scared else (0.6, 0), head=(-25, -18 if scared and not hit else 0, 0),
                         bounce=0.04 * abs(math.sin(t * 10)) if scared else 0, jump=jump)
    cr = crowd(7, center=(18, 0), radius=(4, 4), seed=4, face_to=(0, 0))
    for f, t in frames():
        pose_crowd(cr, f, t, "scared" if t > tc + 0.3 else "happy")
    phone = box("phone", (0, 0, -0.36), (0.1, 0.03, 0.18), M["lead"])
    parent(phone, tour[2].arms[1])
    focus = empty("focus", (11, -6, 2.5))
    cam, aim = camera(24, 2.8, focus)

    def cf(t):
        # 0..tc: close, low, tourists big with the tower rising out of frame
        c_close, a_close = (14.6 - 0.5 * t, -14.0 + 0.45 * t, 1.6), (9.6, -5.0, 3.6)
        c_wide, a_top = (27, -31, 9), (top.x + 2, top.y, top.z - 4)
        k_up = ease_io((t - tc - 0.05) / 0.6)
        if t < land - 0.2:
            fall = max(0.0, t - rel)
            rz = max(1.0, z0 - 4.9 * fall * fall)
            a_fall = (top.x + 4.5, top.y - 1.0, rz)
            k_follow = ease((t - rel - 0.5) / 0.6)
            a = lerp(lerp(a_close, a_top, k_up), a_fall, k_follow)
            c = lerp(c_close, c_wide, k_up)
        else:
            k_back = ease_io((t - land + 0.2) / 0.7)
            a = lerp((top.x + 4.5, top.y - 1.0, 3.0), (10.5, -5.0, 2.2), k_back)
            c = lerp(c_wide, (19.5, -20.5, 3.0), k_back)
        return add(c, drift(t, 0.07), shake(t, tc + 0.1, 0.3, 0.7), shake(t, land, 0.6, 0.7)), add(a, drift(t, 0.05, 2))
    animate_cam(cam, aim, cf)
    for f, t in frames():
        key(focus, f, loc=lerp((11, -6, 2.5), (top.x + 4, top.y, 40), ease_io((t - tc) / 0.6)) if t < land - 0.2 else (11, -4, 1.5))
    dust_puff("dust0", (12.5, 0.0, 0.3), land, 22, spread=5, size=1.2)


def sc1_builders():
    """Pisa 1173, golden hour: soft wet sand, a ring of foundation stones; builders bounce in carrying blocks, a block
    swings down from a wooden crane and lands with physics; camera cranes down from a high wide shot to sand level."""
    world_dusk(top=(0.08, 0.12, 0.3), horizon=(1.0, 0.55, 0.25), strength=1.2)
    ground(M["sand"])
    town(night=False, medieval=True)
    sun = light("SUN", (0, 0, 50), 4.0, (1.0, 0.75, 0.5), 3, rot=(math.radians(72), 0, math.radians(-60)))
    light("AREA", (-15, -25, 12), 4000, (0.6, 0.7, 1.0), 20)
    for i in range(6):  # glossy puddles = "wet" sand
        a = R.uniform(0, 6.3)
        r_ = R.uniform(10, 18)
        cyl(f"pud{i}", (r_ * math.cos(a), r_ * math.sin(a) - 4, 0.01), R.uniform(1.0, 2.2), 0.02, M["puddle"], verts=32).scale[1] *= 0.6
    ground_rb = box("ground_rb", (0, 0, -0.5), (200, 200, 1.0), None)
    ground_rb.hide_render = True
    rb(ground_rb, active=False, shape="BOX")
    # foundation ring (first courses) — passive
    for c in range(2):
        n = 28
        for i in range(n):
            a = 2 * math.pi * (i + 0.5 * c) / n
            b = box(f"fnd{c}_{i}", (8.2 * math.cos(a), 8.2 * math.sin(a), 0.4 + 0.8 * c), (1.75, 1.2, 0.78), M["stone"], bevel=0.06,
                    rot=(0, 0, a + math.pi / 2))
            rb(b, active=False, shape="BOX")
    # wooden crane with a block hanging, lowered then released onto the ring
    box("crane_post", (12, 6, 6), (0.5, 0.5, 12), M["wood"])
    arm = box("crane_arm", (9.5, 3.5, 12), (0.4, 7.5, 0.4), M["wood"], rot=(0, 0, math.radians(45)))
    rope = cyl("rope", (7.5, 1.5, 9), 0.05, 6, M["wood"], verts=8)
    blk = box("hang_block", (7.6, 1.6, 6.0), (1.75, 1.2, 0.78), M["stone"], bevel=0.06, rot=(0, 0, math.radians(40)))
    rel = cue("builders") + 0.6
    for f, t in frames():
        z = 6.0 - 3.6 * ease((t - 0.6) / 2.4) + 0.08 * math.sin(t * 3)
        key(blk, f, loc=(7.6 + 0.15 * math.sin(t * 1.4), 1.6, z), rot=(0.05 * math.sin(t * 2), 0, math.radians(40)))
        key(rope, f, loc=(7.6, 1.6, (12 + z) / 2), scale=(0.05, 0.05, max(0.01, (12 - z) / 2)))
    rb(blk, mass=200, bounce=0.1, release=rel)
    # pile of loose blocks a cart just dumped (real tumble on frame 1..)
    for i in range(7):
        b = box(f"pile{i}", (-9 + R.uniform(-1, 1), -6 + R.uniform(-1, 1), 1.5 + i * 0.9), (1.2, 0.9, 0.6), M["stone"], bevel=0.05,
                rot=(R.uniform(0, 0.5), R.uniform(0, 0.5), R.uniform(0, 3)))
        rb(b, mass=60, bounce=0.2)
    bld = [Toon("b1", coat=(0.65, 0.28, 0.12), hat="cap", hat_col=(0.7, 0.15, 0.1), beard=True, hair=(0.25, 0.15, 0.08)),
           Toon("b2", skin=(0.85, 0.6, 0.42), coat=(0.3, 0.45, 0.25), hat="cap", hat_col=(0.85, 0.7, 0.3)),
           Toon("b3", coat=(0.25, 0.3, 0.55), hairstyle="bald", hair=(0.5, 0.45, 0.4), mustache=True, belly=1.15)]
    carry = box("carried", (0, 0, 0), (0.6, 0.45, 0.35), M["stone"], bevel=0.04)
    for f, t in frames():
        ph = walk_path(bld[0], f, t, (-13, -12, 0), (-3.5, -11.5, 0), 0.0, 4.2)
        bld[0].pose(f, t, walk=ph, arms=(70, 70), arm_side=(-5, -5), mouth="grin", eyes="happy" if t > 3 else "open", look=(0.4, 0))
        key(carry, f, loc=add(bld[0].root.location, (0, -0.45 * 1.4, 1.1 * 1.4 + (0.07 * abs(math.sin(2 * math.pi * ph)) if ph else 0) * 1.4)))
        hit = (t * 2.2) % 1.0
        bld[1].pose(f, t, arms=(-20, 40 + 110 * (1 - abs(math.sin(math.pi * hit)))), mouth="talk", talk=0.5 + 0.5 * math.sin(t * 9),
                    eyes="open", look=(0, -0.6), head=(0, 12, 0))
        bld[2].pose(f, t, arms=(60, 10), arm_side=(20, 8), mouth="smile" if t < cue("sand") else "O", eyes="open" if t < cue("sand") else "wide",
                    look=(0.5, -0.5) if t < cue("sand") else (0, -1), brows=0.5, head=(15, 0, 0))
    place(bld[0], (-13, -12, 0), 80, 1.4)
    place(bld[1], (2.5, -12.0, 0), 160, 1.4)
    place(bld[2], (-1.0, -14.5, 0), 200, 1.4)
    bld[0].root.rotation_euler = (0, 0, math.radians(80))
    # hammer in b2's hand
    hm = box("hammer", (0, 0, -0.42), (0.1, 0.1, 0.35), M["wood"])
    parent(hm, bld[1].arms[1])
    hh = box("hammer_head", (0, 0, -0.6), (0.22, 0.12, 0.12), M["lead"])
    parent(hh, bld[1].arms[1])
    cam, aim = camera(24, 3.2, bld[2].root)

    def cf(t):
        k = ease_io(t / DUR[1])
        c = lerp((-30, -45, 38), (1.0, -21.5, 1.9), k)
        a = lerp((0, 0, 0), (0.5, -11.5, 2.0), k)
        return add(c, drift(t, 0.08, 1)), add(a, drift(t, 0.05, 3))
    animate_cam(cam, aim, cf)


def medieval_site(evening=False, ground_mat=None):
    world_dusk(top=(0.03, 0.06, 0.2) if not evening else (0.04, 0.02, 0.04), horizon=(1.0, 0.48, 0.2) if not evening else (0.75, 0.16, 0.05),
               strength=1.0)
    ground(ground_mat or M["sand"])
    town(night=evening, medieval=True)
    sun = light("SUN", (0, 0, 50), 3.2 if not evening else 2.0, (1.0, 0.72, 0.45) if not evening else (1.0, 0.45, 0.25), 3,
                rot=(math.radians(72), 0, math.radians(-60)))
    light("AREA", (-15, -25, 12), 3000, (0.6, 0.7, 1.0), 20)
    g = box("ground_rb", (0, 0, -0.5), (300, 300, 1.0), None)
    g.hide_render = True
    rb(g, active=False, shape="BOX")
    return sun


def builders3(scale=1.4):
    return [Toon("b1", coat=(0.65, 0.28, 0.12), hat="cap", hat_col=(0.7, 0.15, 0.1), beard=True, hair=(0.25, 0.15, 0.08), scale=scale),
            Toon("b2", skin=(0.85, 0.6, 0.42), coat=(0.3, 0.45, 0.25), hat="cap", hat_col=(0.85, 0.7, 0.3), scale=scale),
            Toon("b3", coat=(0.25, 0.3, 0.55), hairstyle="bald", hair=(0.5, 0.45, 0.4), mustache=True, belly=1.15, scale=scale)]


def scaffold(T_lean_side=1, n=6, r=8.6, h=14):
    poles = []
    for i in range(n):
        a = math.radians(-50 + i * 20) if T_lean_side > 0 else math.radians(130 + i * 20)
        p = (r * math.cos(a), r * math.sin(a), h / 2 + 0.05)
        o = cyl(f"pole{i}", p, 0.14, h, M["wood"], verts=10, rot=(0, math.radians(6), a))
        poles.append(o)
    for i in range(n - 1):
        a = math.radians(-40 + i * 20) if T_lean_side > 0 else math.radians(140 + i * 20)
        p = (r * math.cos(a), r * math.sin(a), 6 + (i % 2) * 4)
        o = box(f"plank{i}", p, (0.5, 3.4, 0.14), M["wood"], rot=(0, 0, a))
        poles.append(o)
    return poles


def sc2_lean():
    """Only three floors up... the soft ground gives way: the stub tilts with a crunch, scaffolding topples (physics),
    a builder drops his block, everybody leaps; 'Badly' = a second jolt + camera hit."""
    medieval_site()
    T = tower(floors=3, lean=0.0)
    tl, tb = cue("lean"), cue("badly")
    crater = cyl("crater", (7.5, 0, 0.02), 6.5, 0.04, M["mud"], verts=48)
    for f, t in frames():
        lean = 3.2 * back_out(min(1, max(0, (t - tl) / 0.7)), 1.2) + 1.6 * ease((t - tb) / 0.35) + 0.25 * spring(t, tb, 1, 4, 6)
        key(T["base"], f, loc=(0, 0, -0.6 * ease((t - tl) / 0.8) - 0.3 * ease((t - tb) / 0.4)), rot=(0, math.radians(lean), 0))
        key(crater, f, scale=(6.5 * ease((t - tl) / 0.6) + 1e-3, 4.5 * ease((t - tl) / 0.6) + 1e-3, 0.02))
    for o in scaffold(1, 5):
        rb(o, mass=8, bounce=0.2, release=tl + 0.25 + R.uniform(0, 0.25))
    bl = builders3()
    spots = [(13.5, -9, 0), (10.0, -13.0, 0), (16.5, -12.5, 0)]
    for b, p, y in zip(bl, spots, (-60, -20, 10)):
        place(b, p, y, 1.4)
    held = box("held", (13.5, -9.7, 1.5), (0.6, 0.45, 0.35), M["stone"], bevel=0.04)
    for f, t in frames():
        scared = t > tl + 0.1
        for i, b in enumerate(bl):
            k = t - tl - 0.1 - 0.08 * i
            jump = max(0.0, 2.2 * k - 4.9 * k * k) * 0.6 if 0 < k < 0.45 else 0.0
            k2 = t - tb - 0.05
            jump += max(0.0, 1.6 * k2 - 4.9 * k2 * k2) * 0.5 if 0 < k2 < 0.33 else 0.0
            if not scared:
                b.pose(f, t, arms=(70, 70) if i == 0 else (20 * math.sin(t * 3 + i), -20 * math.sin(t * 3 + i)), mouth="smile", eyes="open",
                       look=(0, 0.3), head=(0, 5, 0))
            else:
                b.pose(f, t, arm_side=(150, 150), arms=(0, 0), eyes="wide", mouth="O", brows=1, look=(-0.5, 1.0), head=(25, 20, 0), jump=jump,
                       squash=1.0 + 0.12 * math.sin(min(1, max(0, k / 0.45)) * math.pi))
    key_held = [(f, t) for f, t in frames()]
    for f, t in key_held:
        if t < tl + 0.15:
            key(held, f, loc=add(bl[0].root.location, (0.35, -0.6, 1.55)))
    rb(held, mass=40, bounce=0.2, release=tl + 0.15)
    cam, aim = camera(26, 3.0, bl[0].root)

    def cf(t):
        k = ease_io(t / DUR[2])
        c = lerp((26, -30, 5), (21, -24, 3.2), k)
        a = lerp((4, 0, 9), (6, -2, 7), k)
        return add(c, drift(t, 0.07), shake(t, tl + 0.05, 0.45, 0.7), shake(t, tb, 0.6, 0.6)), add(a, drift(t, 0.05, 2))
    animate_cam(cam, aim, cf, lens_fn=lambda t: 26 + 6 * ease_io((t - tb) / 0.4))
    dust_puff("dust2", (9, 0, 0.3), tl + 0.05, 10, spread=6, size=1.4)
    dust_puff("dust2b", (10, -3, 0.3), tb, 8, spread=5, size=1.2)


def fire(name, loc, t_on, size=1.0):
    """Flickering flame (emissive cones) + an orange light that lights the scene around it."""
    m = emission(name + "m", (1.0, 0.45, 0.08), 18.0)
    m2 = emission(name + "m2", (1.0, 0.85, 0.3), 25.0)
    cones = []
    rr = random.Random(hash(name) % 997)
    for i in range(5):
        o = prim(bpy.ops.mesh.primitive_cone_add, f"{name}c{i}", loc, mat=m if i else m2, vertices=12, radius1=0.5, depth=1.0)
        cones.append((o, rr.uniform(0, 6), (rr.uniform(-0.5, 0.5) * size, rr.uniform(-0.5, 0.5) * size)))
    L = light("POINT", (loc[0], loc[1], loc[2] + 1.5), 0.0, (1.0, 0.5, 0.15), 1.0)
    for f, t in frames():
        k = t - t_on
        g = 0.0 if k < 0 else min(1.0, k / 0.3)
        for o, ph, off in cones:
            fl = 0.75 + 0.25 * math.sin(t * 17 + ph) + 0.1 * math.sin(t * 31 + 2 * ph)
            h = size * 2.4 * g * fl
            key(o, f, loc=(loc[0] + off[0], loc[1] + off[1], loc[2] + h / 2), scale=(max(1e-3, size * g * 0.9), max(1e-3, size * g * 0.9), max(1e-3, h)))
        L.data.energy = 3000 * size * g * (0.8 + 0.2 * math.sin(t * 23))
        L.data.keyframe_insert("energy", frame=f)


def sc3_war():
    """War: the sky turns blood-red, FLAMING catapult boulders streak in and smash a stack of crates (physics), fires
    flare up, the builders run screaming towards the camera; then a 100-year time-lapse — days flash by, grass and
    trees grow around the abandoned stump."""
    sun = medieval_site(evening=True)
    T = tower(floors=3, lean=4.8)
    T["base"].location = (0, 0, -0.9)
    tw, ts, th = cue("war"), cue("stops"), cue("hundred")
    for i in range(12):
        p = (12.5 + (i % 3) * 1.25, -5.5 + (i // 6) * 1.25, 0.6 + ((i // 3) % 2) * 1.2)
        rb(box(f"crate{i}", p, (1.2, 1.2, 1.2), M["wood"], bevel=0.05), mass=10, bounce=0.2)
    fire_m = emission("rockfire", (1.0, 0.5, 0.1), 14.0)
    hits = []
    for j, (t0, tgt) in enumerate(((tw - 0.25, (13.5, -5.0, 1.2)), (tw + 0.6, (-6, -9, 0.6)), (tw + 1.2, (20, -1, 0.6)))):
        bd = sphere(f"boulder{j}", (-60, 0, 30), 1.3, M["stone"], segs=16)
        glow = sphere(f"boulderglow{j}", (0, 0, 0), 1.45, fire_m, segs=12)
        parent(glow, bd)
        glow.location = (0.25, 0, 0.25)
        bl_ = light("POINT", (0, 0, 0), 2500, (1.0, 0.5, 0.15), 1.0)
        parent(bl_, bd)
        trail = [sphere(f"trail{j}_{k}", (0, 0, -999), 0.9 - 0.12 * k, fire_m, segs=10) for k in range(6)]
        src = (-48, 14 - 10 * j, 30)
        dur = 1.05

        def path(tt, src=src, tgt=tgt, t0=t0):
            kk = min(max((tt - t0) / dur, 0.0), 1.0)
            return (lerp(src[0], tgt[0], kk), lerp(src[1], tgt[1], kk), lerp(src[2], tgt[2], kk) + 16 * kk * (1 - kk))
        for f, t in frames():
            key(bd, f, loc=path(t), rot=(t * 5, t * 3, 0))
            for k, tr in enumerate(trail):
                tk = t - 0.05 * (k + 1)
                on = t0 < tk < t0 + dur
                key(tr, f, loc=path(tk) if on else (0, 0, -999), scale=((0.9 - 0.12 * k) * on + 1e-3,) * 3)
            show(glow, f, t < t0 + dur + 0.6)
        rb(bd, mass=300, bounce=0.1, release=t0 + dur)
        bd.rigid_body.kinematic = True
        dust_puff(f"bdust{j}", tgt, t0 + dur, 8, col=(0.35, 0.3, 0.27), spread=3.5, size=1.3)
        fire(f"fire{j}", (tgt[0] + 1.5, tgt[1] - 1.0, 0.0), t0 + dur + 0.1, 1.2)
        hits.append(t0 + dur)
    bl = builders3()
    starts = [(6, -11, 0), (9.5, -12.5, 0), (3, -13, 0)]
    ends = [(4, -30, 0), (13, -31, 0), (-3, -31, 0)]
    for b, p in zip(bl, starts):
        place(b, p, 160, 1.4)
    for f, t in frames():
        for i, b in enumerate(bl):
            run0 = tw + 0.2 + 0.12 * i
            ph = walk_path(b, f, t, starts[i], ends[i], run0, run0 + 2.0, stride=0.42)
            yaw = math.degrees(math.atan2(-(ends[i][0] - starts[i][0]), (ends[i][1] - starts[i][1]))) + 180 if t > run0 else 160
            key(b.root, f, rot=(0, 0, math.radians(yaw)))
            b.pose(f, t, walk=ph * 1.5 if ph else None, eyes="wide" if t > tw - 0.2 else "open", mouth="O" if t > tw - 0.2 else "smile",
                   brows=1, arm_side=(165, 165) if ph else (8, 8), arms=(0, 0) if ph else (25, 25), lean=10 if ph else 0,
                   look=(0, 0), head=(0, -5 if ph else 0, 0))
    # time-lapse
    grass = cyl("grow", (0, 0, 0.03), 1.0, 0.06, M["grass"], verts=64)
    trees = []
    for i in range(8):
        h = R.uniform(5, 8)
        trees.append((cypress(f"sap{i}", (R.uniform(-24, 24), R.uniform(-6, 24)), h), h))
    for f, t in frames():
        k = max(0.0, t - th)
        key(sun, f, rot=(math.radians(72), 0, math.radians(-60 + 360 * 1.5 * k)))
        sun.data.energy = 2.0 + 3.0 * max(0.0, math.sin(2 * math.pi * 1.5 * k)) if k > 0 else 2.0
        sun.data.keyframe_insert("energy", frame=f)
        r_ = 34 * ease(k / 1.2)
        key(grass, f, scale=(max(1e-3, r_), max(1e-3, r_), 0.03))
        for i, (tr_, h) in enumerate(trees):
            g_ = back_out(min(1.0, max(0.0, (k - 0.1 * i) / 0.4)))
            key(tr_, f, scale=(1.1 * g_ + 1e-3, 1.1 * g_ + 1e-3, h / 2 * g_ + 1e-3))
    cam, aim = camera(24, 3.5, bl[1].root)

    def cf(t):
        run = ease_io((t - tw - 0.2) / 2.2)
        c = lerp((9, -26, 2.2), (2, -40, 7), run)
        a = lerp((7, -8, 4.0), (2, 0, 7), run)
        sh = (0, 0, 0)
        for hh in hits:
            sh = add(sh, shake(t, hh, 0.5, 0.6))
        return add(c, drift(t, 0.08), sh), add(a, drift(t, 0.05, 2))
    animate_cam(cam, aim, cf)


def sc4_soil():
    """Cutaway: under the abandoned stump the soil grains (real rigid spheres) are loose; over the decades the weight
    presses down and they pack tight — that pause SAVED it. A little worm wiggles through for fun."""
    world_dusk(top=(0.02, 0.03, 0.09), horizon=(0.35, 0.18, 0.14), strength=0.8)
    town(night=True, medieval=True)
    sun = light("SUN", (0, 0, 50), 3.0, (1.0, 0.8, 0.6), 3, rot=(math.radians(55), 0, math.radians(-30)))
    light("AREA", (0, -30, 6), 6000, (1.0, 0.9, 0.8), 30, rot=(math.radians(80), 0, 0))
    # soil block cut open towards the camera (-Y): back wall + floor + sides; grass skin on top
    W_, D_, H_ = 26.0, 6.0, 9.0
    for nm, c, s_ in (("sb_back", (0, D_ / 2 + 0.5, -H_ / 2 + 1.5), (W_ + 2, 1, H_ + 4)), ("sb_floor", (0, 0, -H_ - 0.5), (W_ + 2, D_ + 2, 1)),
                      ("sb_l", (-W_ / 2 - 0.5, 0, -H_ / 2 + 1.5), (1, D_ + 2, H_ + 4)), ("sb_r", (W_ / 2 + 0.5, 0, -H_ / 2 + 1.5), (1, D_ + 2, H_ + 4))):
        o = box(nm, c, s_, M["soil1"])
        rb(o, active=False, shape="BOX")
    front = box("sb_front", (0, -D_ / 2 - 0.5, -H_ / 2 + 1.5), (W_ + 2, 1, H_ + 4), None)
    front.hide_render = True
    rb(front, active=False, shape="BOX")
    # outside ground around the cut
    for nm, c, s_ in (("gl", (-W_ / 2 - 60, 0, -0.5), (118, 200, 1)), ("gr", (W_ / 2 + 60, 0, -0.5), (118, 200, 1)),
                      ("gb", (0, D_ / 2 + 50, -0.5), (W_ + 2, 98, 1))):
        box(nm, c, s_, M["grass"])
    rr = random.Random(3)
    grains = []
    src = sphere("grain_src", (0, 0, -999), 1.0, M["soil2"], segs=10)
    alt = sphere("grain_src2", (0, 0, -999), 1.0, M["soil1"], segs=10)
    n = 0
    for zl in range(10):
        for xi in range(26):
            for yi in range(5):
                if rr.random() < 0.18:
                    continue
                r_ = rr.uniform(0.38, 0.52)
                p = (-W_ / 2 + 0.7 + xi * 0.98 + rr.uniform(-0.12, 0.12), -D_ / 2 + 0.7 + yi * 1.15, -H_ + 0.6 + zl * 1.0 + rr.uniform(0, 0.05))
                g = instance(src if (xi + zl) % 3 else alt, f"grain{n}", p, scale=(r_, r_, r_))
                rb(g, mass=1, bounce=0.05, friction=0.9, shape="SPHERE")
                g.rigid_body.collision_margin = 0.0
                n += 1
    # the tower stump: a kinematic plunger that slowly presses down (decades of weight)
    T = tower(floors=3, lean=4.8)
    foot = cyl("foot", (0, 0, -0.6), 7.8, 1.2, M["marble"], verts=48)
    tp, ts_ = cue("pause"), cue("soil")
    for f, t in frames():
        d = 1.2 - 1.6 * ease(t / 1.2) - 2.4 * ease((t - ts_ + 0.6) / 2.6)  # settle onto the soil, then decades of pressing
        key(T["base"], f, loc=(0, 0, d))
        key(foot, f, loc=(0, 0, -0.6 + d))
    rb(foot, active=True, mass=1000, shape="CONVEX_HULL")
    foot.rigid_body.kinematic = True
    # worm
    wm = pbr("worm", (0.95, 0.45, 0.5), 0.35)
    segs = [sphere(f"worm{i}", (0, 0, -999), 0.32, wm, segs=12) for i in range(9)]
    eye_w = [sphere(f"wormeye{i}", (0, 0, -999), 0.09, M["white"], segs=10) for i in range(2)]
    for f, t in frames():
        for i, sg in enumerate(segs):
            u = t * 2.2 - i * 0.35
            key(sg, f, loc=(-9 + 1.6 * t - i * 0.42, -D_ / 2 - 0.05, -5.0 + 0.35 * math.sin(u * 2.4)))
        hd = segs[0].location
        for k_, e in enumerate(eye_w):
            key(e, f, loc=(hd.x + 0.12, hd.y - 0.25, hd.z + 0.1 + (0.0 if k_ else 0.0) + (0.12 if k_ else -0.05)))
    for f, t in frames():
        k = max(0.0, t - tp)
        sun.data.energy = 3.0 + 2.0 * math.sin(2 * math.pi * 1.2 * k) if k > 0 else 3.0
        sun.data.keyframe_insert("energy", frame=f)
    cam, aim = camera(30, 6.0, segs[0])

    def cf(t):
        k = ease_io(min(1.0, t / 1.4))
        c = lerp((8, -40, 22), (2, -30, -2.5), k)
        a = lerp((0, 0, 10), (0, 0, -3.5), k)
        return add(c, drift(t, 0.05), (0.8 * math.sin(t * 0.4), 0, 0)), add(a, drift(t, 0.03, 2))
    animate_cam(cam, aim, cf)


def sc5_trick():
    """Builders return; new floors drop in from the sky one by one with springy landings and dust; on 'taller' the
    trick glows gold: each new floor is taller on the short side, so the tower starts to bend back."""
    medieval_site()
    T = tower(floors=8, lean=4.8)
    T["base"].location = (0, 0, -0.9)
    tr_, tt_, tsh = cue("returned"), cue("trick"), cue("taller")
    drops = [0.9 + 0.55 * i for i in range(5)]  # floors 3..7
    for f, t in frames():
        for j, k in enumerate(range(3, 8)):
            g = T["groups"][k]
            d = (t - drops[j]) / 0.45
            z = 60 if d <= 0 else 60 * (1 - min(1.0, d)) ** 2
            sq = 1.0 + (0.12 * spring(t, drops[j] + 0.45, 1, 3, 7) if d > 1 else 0)
            key(g, f, loc=(0, 0, z), scale=(1 / math.sqrt(sq), 1 / math.sqrt(sq), sq))
            show(g, f, d > -0.3)
        curve = 3.0 * ease((t - tsh) / 1.0)
        for k, j in enumerate(T["joints"]):
            key(j, f, rot=(0, math.radians(-curve / 5.0) if k >= 3 else 0, 0))
    for j, k in enumerate(range(3, 8)):
        SC.frame_set(int((drops[j] + 0.45) * FPS) + 2)
        p = T["groups"][k].matrix_world.translation
        dust_puff(f"fd{k}", (p.x + 5, p.y - 4, p.z), drops[j] + 0.45, 4, spread=3, size=1.0)
    # the trick glows: a gold wedge ring on the short side of floor 4
    glow = cyl("wedge", (0, 0, 0.3), R_OUT + 0.6, 0.6, M["glow_gold"], verts=64)
    parent(glow, T["joints"][3])
    for f, t in frames():
        a = ease((t - tsh) / 0.3) * (1 - ease((t - tsh - 1.4) / 0.4))
        key(glow, f, scale=(1 + 0.03 * a, 1 + 0.03 * a, max(1e-3, a)))
    bl = builders3()
    starts = [(-24, -19, 0), (16, -26, 0), (-14, -28, 0)]
    ends = [(-6, -18, 0), (5, -20, 0), (-2, -22, 0)]
    for f, t in frames():
        for i, b in enumerate(bl):
            ph = walk_path(b, f, t, starts[i], ends[i], 0.1 + 0.15 * i, tr_ + 1.4, stride=0.5)
            yaw = math.degrees(math.atan2(-(ends[i][0] - starts[i][0]), (ends[i][1] - starts[i][1]))) + 180 if ph else -20 * (i - 1)
            key(b.root, f, rot=(0, 0, math.radians(yaw)))
            b.pose(f, t, walk=ph, mouth="grin", eyes="happy" if not ph else "open", brows=0.6,
                   arm_side=(150, 150) if (not ph and t > tsh) else None, arms=(0, 0) if (not ph and t > tsh) else None,
                   jump=0.25 * abs(math.sin(t * 7 + i)) if (not ph and t > tsh) else 0.0, look=(0, 0.8), head=(0, 18 if not ph else 0, 0))
    for b, p in zip(bl, starts):
        b.root.scale = (1.5, 1.5, 1.5)
    cam, aim = camera(22, 5.0, T["joints"][3])

    def cf(t):
        k = ease_io(t / DUR[5])
        ang = math.radians(-40 + 40 * k)
        r_ = 30 + 16 * k
        c = (r_ * math.sin(ang) + 2, -r_ * math.cos(ang), 3 + 12 * k)
        a = lerp((0, -12, 4), (3, 0, 26), ease_io((t - 0.6) / 3.5))
        return add(c, drift(t, 0.08)), add(a, drift(t, 0.05, 2))
    animate_cam(cam, aim, cf)


def banana_obj(name, length=40.0, bend=0.35):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.0
    cu.bevel_resolution = 6
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    n = 24
    sp.points.add(n - 1)
    for i in range(n):
        u = i / (n - 1)
        a = (u - 0.5) * bend * 2
        R_ = length / (2 * bend)
        sp.points[i].co = (R_ * (1 - math.cos(a)), 0, R_ * math.sin(a) + length / 2, 1)
        sp.points[i].radius = 3.2 * math.sin(math.pi * (0.06 + 0.88 * u)) ** 0.6
    o = bpy.data.objects.new(name, cu)
    link(o)
    cu.materials.append(M["banana"])
    tip = sphere(name + "tip", (0, 0, 0), 0.7, M["banana_tip"])
    parent(tip, o)
    tip.location = sp.points[-1].co[:3]
    return o


def sc6_banana():
    """Profile view at sunset: the tower isn't straight — it CURVES (a gold line traces its spine). On 'banana' a giant
    banana swings down beside it with a springy wobble; the crowd laughs."""
    world_dusk(top=(0.05, 0.06, 0.2), horizon=(1.0, 0.45, 0.2), strength=1.2)
    piazza(cathedral=True)
    town(night=False)
    light("SUN", (0, 0, 50), 3.5, (1.0, 0.65, 0.4), 3, rot=(math.radians(78), 0, math.radians(-100)))
    light("AREA", (-30, -40, 20), 8000, (0.6, 0.7, 1.0), 30)
    T = tower(lean=5.0)
    set_lean(T, 1, 5.0, 3.0)
    tc_, tb = cue("curved"), cue("banana")
    spine_m = emission("spine", (1.0, 0.75, 0.2), 10.0)
    dots = []
    for k in range(8):
        d = sphere(f"spine{k}", (0, 0, 0), 0.55, spine_m, segs=12)
        parent(d, T["joints"][k])
        d.location = (0, -R_OUT - 1.2, FLOOR_H[k] / 2)
        dots.append(d)
    for f, t in frames():
        for k, d in enumerate(dots):
            a = back_out(min(1.0, max(0.0, (t - tc_ + 0.3 - 0.06 * k) / 0.3)))
            key(d, f, scale=(max(1e-3, a), max(1e-3, a), max(1e-3, a) * 4.5))
    ban = banana_obj("banana", 46, 0.33)
    for f, t in frames():
        k = (t - tb + 0.25) / 0.5
        if k <= 0:
            key(ban, f, loc=(-26, -6, 90), rot=(0, math.radians(-40), 0))
        else:
            z = 90 * (1 - min(1.0, k)) ** 2 + 0
            w = spring(t, tb + 0.25, 12, 1.8, 3.5)
            key(ban, f, loc=(-26, -6, z), rot=(0, math.radians(-8 + w), 0))
    cr = crowd(10, center=(6, -24), radius=(14, 4), seed=6, face_to=(0, 0))
    for f, t in frames():
        pose_crowd(cr, f, t, "cheer" if t > tb + 0.2 else "happy")
    cam, aim = camera(24, 6.0, T["joints"][4])

    def cf(t):
        k = ease_io(t / DUR[6])
        ang = math.radians(-35 + 30 * k)
        r_ = 95 - 10 * k
        return add((r_ * math.sin(ang), -r_ * math.cos(ang), 10 + 6 * k), drift(t, 0.1)), add((-6 * ease(t - tb + 0.5), 0, 27), drift(t, 0.05, 2))
    animate_cam(cam, aim, cf)


def stripes_mat():
    m, nt, out = new_mat("stripes")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = 0.4
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.inputs["Scale"].default_value = 3.0
    wv.wave_profile = "SAW" if False else "SIN"
    nt.links.new(tc.outputs["Generated"], wv.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.interpolation = "CONSTANT"
    rp.color_ramp.elements[0].color = (0.85, 0.05, 0.04, 1)
    rp.color_ramp.elements[1].position = 0.5
    rp.color_ramp.elements[1].color = (0.95, 0.95, 0.92, 1)
    nt.links.new(wv.outputs["Fac"], rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def sc7_closed():
    """1990, night, floodlit: the top hangs 4.5 m out — a glowing plumb line drops from the top and a gold ruler
    shows the gap. On 'closed' striped barriers swing shut with a springy clank; tourists droop."""
    world_dusk(top=(0.008, 0.012, 0.045), horizon=(0.09, 0.07, 0.16), strength=1.0)
    piazza(cathedral=False)
    stars()
    town(night=True)
    T = tower(lean=5.5)
    set_lean(T, 1, 5.5, 1.5)
    floodlights()
    light("SUN", (0, 0, 50), 0.5, (0.5, 0.6, 1.0), 2, rot=(math.radians(60), 0, math.radians(140)))
    ttop, tm, tcl = cue("top"), cue("meters"), cue("closed")
    SC.frame_set(1)
    top = T["top"].matrix_world.translation.copy()
    red = emission("plumb", (1.0, 0.15, 0.1), 12.0)
    line = cyl("plumb", (top.x + 4.8, top.y - 5.5, top.z), 0.12, 1.0, red, verts=8)
    bob = sphere("plumb_bob", (0, 0, 0), 0.6, red)
    ruler = box("ruler", (0, 0, 0.15), (1, 0.4, 0.25), M["glow_gold"])
    for f, t in frames():
        k = ease((t - ttop - 0.2) / 0.9)
        L = max(0.01, top.z * k)
        key(line, f, loc=(top.x + 4.8, top.y - 5.5, top.z - L / 2), scale=(0.12, 0.12, L / 2))
        key(bob, f, loc=(top.x + 4.8, top.y - 5.5, top.z - L), scale=(0.6 * (k > 0) + 1e-3,) * 3)
        k2 = ease((t - tm) / 0.6)
        w = max(0.01, top.x * k2)
        key(ruler, f, loc=(w / 2 + 4.8, top.y - 5.5, 0.15), scale=(w, 1.0, 1.0))
    sm = stripes_mat()
    gates = []
    for side in (-1, 1):
        hinge = empty(f"hinge{side}", (side * 5.5, -14, 0))
        panel = box(f"gate{side}", (-side * 2.6, 0, 1.0), (5.2, 0.15, 0.9), sm)
        parent(panel, hinge)
        post = cyl(f"gpost{side}", (side * 5.5, -14, 0.8), 0.15, 1.6, M["lead"], verts=12)
        gates.append((hinge, side))
    for f, t in frames():
        for hinge, side in gates:
            a = 90 * (1 - ease((t - tcl + 0.15) / 0.3)) + spring(t, tcl + 0.15, 12, 3, 6)
            key(hinge, f, rot=(0, 0, math.radians(side * a)))
    cr = crowd(9, center=(0, -22), radius=(9, 4), seed=8, face_to=(0, 0))
    for f, t in frames():
        pose_crowd(cr, f, t, "sad" if t > tcl + 0.2 else "happy")
    cam, aim = camera(22, 5.0, T["joints"][3])

    def cf(t):
        up = ease_io((t - ttop + 0.1) / 0.8)
        down = ease_io((t - tcl + 0.6) / 0.6)
        c = (8 + 2 * t, -62, 4 + 6 * up - 4 * down)
        a = lerp(lerp((2, 0, 10), (top.x / 2, top.y, top.z * 0.55), up), (0, -14, 2), down)
        return add(c, drift(t, 0.08), shake(t, tcl + 0.15, 0.3, 0.4)), add(a, drift(t, 0.05, 2))
    animate_cam(cam, aim, cf, lens_fn=lambda t: 22 + 14 * ease_io((t - tcl + 0.6) / 0.6))


def engineers(scale=1.5):
    return [Toon("e1", coat=(0.95, 0.5, 0.1), hat="hardhat", hat_col=(1.0, 0.8, 0.05), glasses=True, mustache=True, scale=scale),
            Toon("e2", skin=(0.62, 0.42, 0.28), coat=(0.2, 0.5, 0.85), hat="hardhat", hat_col=(1.0, 1.0, 1.0), hairstyle="short", scale=scale),
            Toon("e3", skin=(0.98, 0.84, 0.72), coat=(0.95, 0.5, 0.1), hat="hardhat", hat_col=(1.0, 0.8, 0.05), hairstyle="long",
                 hair=(0.75, 0.5, 0.2), scale=scale)]


def sc8_lead():
    """Engineers stack lead ingots on the high side (each one drops and stacks with real physics, clank by clank);
    then a drill pulls soil from under the low side, bucket by bucket — and the tower eases back."""
    world_dusk(top=(0.1, 0.18, 0.4), horizon=(0.95, 0.6, 0.35), strength=1.2)
    piazza(cathedral=True)
    town(night=False)
    light("SUN", (0, 0, 50), 4.0, (1.0, 0.8, 0.6), 3, rot=(math.radians(60), 0, math.radians(-40)))
    light("AREA", (-30, -40, 20), 6000, (0.6, 0.7, 1.0), 30)
    g = box("ground_rb", (0, 0, -0.5), (300, 300, 1.0), None)
    g.hide_render = True
    rb(g, active=False, shape="BOX")
    T = tower(lean=5.5)
    tt, tld, tp, tbk = cue("tons"), cue("lead"), cue("pulled"), cue("bucket")
    for f, t in frames():
        set_lean(T, f, 5.5 - 0.7 * ease((t - tp) / 3.0), 1.5)
    plat = box("plat", (-12.5, 0, 0.4), (5.5, 7.0, 0.8), M["stone"], bevel=0.05)
    rb(plat, active=False, shape="BOX")
    n = 0
    for layer in range(4):
        for row in range(4):
            p = (-12.5 + (-1.3 if layer % 2 else 1.3) * (1 if row % 2 else -1) * 0.5 + (row // 2 - 0.5) * 2.4 * (layer % 2 == 0),
                 -2.4 + row * 1.6 if layer % 2 == 0 else -2.4 + row * 1.6, 0.8 + 0.25 + layer * 0.52 + 6.0)
            o = box(f"ingot{n}", p, (2.2, 1.3, 0.48), M["lead"], bevel=0.05)
            rel = tt + 0.05 + n * 0.13
            for f, t in frames():  # hidden and held in place until its drop (never teleport a kinematic body)
                show(o, f, t >= rel - 0.04)
            rb(o, mass=60, bounce=0.05, friction=0.8, release=rel)
            n += 1
    # drill rig on the low (+X) side: tower frame, spinning auger into the ground, soil chunks spilling from a chute
    box("rig_base", (15, -6, 0.5), (3, 3, 1), M["lead"])
    for dx in (-1, 1):
        cyl(f"rig_leg{dx}", (15 + dx, -6, 4.5), 0.18, 8, M["red"], verts=10)
    auger = cyl("auger", (15, -6, 3.5), 0.45, 7, M["lead"], verts=12)
    chute = cyl("chute", (17, -7, 1.8), 0.4, 3, M["red"], verts=12, rot=(0, math.radians(55), 0))
    for f, t in frames():
        key(auger, f, rot=(0, 0, t * 12 * (t > tp)), loc=(15, -6, 3.5 - 0.8 * ease((t - tp) / 0.8)))
    for i in range(18):
        rel = tp + 0.4 + i * 0.12
        c = sphere(f"chunk{i}", (18.3 + R.uniform(-0.1, 0.1), -7.6, 3.0), R.uniform(0.25, 0.4), M["soil1"], segs=10)
        for f, t in frames():
            show(c, f, t >= rel - 0.04)
        rb(c, mass=2, bounce=0.1, release=rel, shape="SPHERE")
    en = engineers()
    spots = [(-15, -7, 0), (8, -16, 0), (19, -10, 0)]
    for e, p, y in zip(en, spots, (-40, 10, 40)):
        place(e, p, y, 1.5)
    bucket = cyl("bucket", (0, 0, 0), 0.35, 0.5, M["red"], verts=16)
    for f, t in frames():
        en[0].pose(f, t, arms=(100, 40), arm_side=(10, 60) if t > tt else (10, 10), mouth="grin" if t > tld else "smile", eyes="open",
                   look=(-0.4, 0.5), head=(-20, 15, 0), jump=0.15 * abs(math.sin(t * 8)) if tld < t < tld + 1.2 else 0)
        en[1].pose(f, t, arms=(30 * math.sin(t * 4), -30 * math.sin(t * 4)), mouth="talk", talk=0.5 + 0.5 * math.sin(t * 11), eyes="open",
                   look=(0.5, 0.2), head=(15, 5, 0))
        ph = walk_path(en[2], f, t, (21, -12, 0), (14, -15, 0), tbk - 0.6, tbk + 1.2) if t > tbk - 0.6 else None
        en[2].pose(f, t, walk=ph, arms=(60, 20), mouth="grin", eyes="happy" if t > tbk + 1.2 else "open", look=(0, 0))
        key(bucket, f, loc=add(en[2].root.location, (0.5, -0.5, 0.9)))
    cam, aim = camera(24, 5.5, T["joints"][2])

    def cf(t):
        k = ease_io(t / DUR[8])
        ang = math.radians(-125 + 250 * k)
        r_ = 27
        return add((r_ * math.sin(ang), -r_ * abs(math.cos(ang)) - 9 * math.sin(math.pi * k), 3.5 + 3 * math.sin(math.pi * k)), drift(t, 0.08)), \
            add(lerp((-12, -1, 2.5), (15, -7, 3), ease((t - tp + 0.6) / 1.8)), drift(t, 0.04, 2))
    animate_cam(cam, aim, cf)


def confetti(n, area, t_on, height=25):
    cols = [(1.0, 0.8, 0.1), (0.95, 0.2, 0.3), (0.2, 0.6, 1.0), (0.3, 0.9, 0.4), (1.0, 0.5, 0.1), (0.8, 0.3, 0.9)]
    mats_ = [pbr(f"conf{i}", c, 0.4, emit=c, estr=0.6) for i, c in enumerate(cols)]
    src = [prim(bpy.ops.mesh.primitive_plane_add, f"confsrc{i}", (0, 0, -999), mat=m, size=0.35) for i, m in enumerate(mats_)]
    rr = random.Random(9)
    for i in range(n):
        o = instance(src[i % 6], f"conf{i}", (0, 0, -999))
        x0, y0 = rr.uniform(area[0], area[1]), rr.uniform(area[2], area[3])
        z0 = height + rr.uniform(0, 8)
        ph, sp = rr.uniform(0, 6), rr.uniform(1.5, 2.6)
        for f, t in frames():
            k = t - t_on
            if k < 0:
                key(o, f, loc=(x0, y0, -50))
                continue
            key(o, f, loc=(x0 + 0.8 * math.sin(k * sp + ph), y0 + 0.6 * math.cos(k * sp * 1.3 + ph), z0 - 3.2 * k),
                rot=(k * sp * 3 + ph, k * sp * 2, ph))


def firework(name, center, t_on, col, n=40, r=9.0):
    m = emission(name, col, 30.0)
    rr = random.Random(hash(name) % 999)
    for i in range(n):
        th, ph = rr.uniform(0, 2 * math.pi), math.acos(rr.uniform(-1, 1))
        d = (math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph))
        o = sphere(f"{name}{i}", (0, 0, -999), 0.35, m, segs=8)
        for f, t in frames():
            k = t - t_on
            if k < 0 or k > 1.6:
                key(o, f, loc=(0, 0, -999), scale=(1e-3,) * 3)
                continue
            e = 1 - math.exp(-4 * k)
            key(o, f, loc=(center[0] + d[0] * r * e, center[1] + d[1] * r * e, center[2] + d[2] * r * e - 2.5 * k * k),
                scale=(max(1e-3, 1 - k / 1.6),) * 3)


def sc9_worked():
    """Sunset, golden: the tower eases back 45 cm — engineers and tourists cheer and jump, confetti flutters down
    (keyframed flutter physics), and on '200 more years' fireworks bloom over the piazza as the camera cranes up."""
    world_dusk(top=(0.06, 0.06, 0.22), horizon=(1.0, 0.42, 0.18), strength=1.2)
    piazza(cathedral=True)
    town(night=False)
    stars(150)
    light("SUN", (0, 0, 50), 3.5, (1.0, 0.6, 0.35), 3, rot=(math.radians(80), 0, math.radians(-120)))
    light("AREA", (-30, -40, 20), 7000, (0.6, 0.7, 1.0), 30)
    T = tower(lean=4.8)
    tw_, tst, t2 = cue("worked"), cue("straightened"), cue("twohundred")
    for f, t in frames():
        set_lean(T, f, 4.8 - 0.55 * ease((t - tst) / 1.0) + 0.12 * spring(t, tst + 1.0, 1, 2, 4), 1.5)
    en = engineers()
    cr = crowd(12, center=(2, -12.5), radius=(12, 2.0), seed=12, face_to=(0, -40))
    spots = [(-3, -18.5, 0), (1, -19.5, 0), (5, -18.5, 0)]
    for e, p, y in zip(en, spots, (-10, 0, 15)):
        place(e, p, y, 1.5)
    for f, t in frames():
        cheer = t > tw_ + 0.1
        for i, e in enumerate(en):
            e.pose(f, t, arm_side=(150 + 15 * math.sin(t * 9 + i), 150 + 15 * math.cos(t * 9 + i)) if cheer else (10, 10), arms=(0, 0),
                   eyes="happy" if cheer else "open", mouth="grin" if cheer else "smile",
                   jump=0.35 * abs(math.sin(t * 6.5 + i)) if cheer else 0, head=(0, 12, 0), look=(0, 0.6))
        pose_crowd(cr, f, t, "cheer" if t > tw_ + 0.3 else "happy")
    confetti(160, (-14, 14, -26, -8), tw_ + 0.2, 16)
    for j, (c, col) in enumerate((((-25, 30, 55), (1.0, 0.6, 0.15)), ((22, 25, 62), (0.3, 0.6, 1.0)), ((-5, 40, 70), (1.0, 0.25, 0.4)))):
        firework(f"fw{j}", c, t2 - 0.2 + 0.3 * j, col)
    cam, aim = camera(22, 4.0, en[1].root)

    def cf(t):
        k = ease_io(t / DUR[9])
        c = lerp((1.5, -31, 2.2), (6, -66, 16), k)
        a = lerp((1, -17, 2.2), (0, 0, 38), ease_io((t - 1.5) / 4.5))
        return add(c, drift(t, 0.08)), add(a, drift(t, 0.05, 2))
    animate_cam(cam, aim, cf)


def sc11_climb():
    """At the top: two friends on the belfry rim, wind tugging their hair; one clings, one grins and waves; the
    camera orbits them with the lit town far below."""
    world_dusk(top=(0.03, 0.03, 0.12), horizon=(0.85, 0.35, 0.2), strength=1.1)
    piazza(cathedral=True)
    town(night=True)
    stars(200)
    light("SUN", (0, 0, 50), 2.5, (1.0, 0.6, 0.35), 3, rot=(math.radians(84), 0, math.radians(-120)))
    T = tower(lean=4.0)
    floodlights(energy=60000)
    SC.frame_set(1)
    topw = T["top"].matrix_world
    pa = Toon("pa", coat=(0.95, 0.4, 0.15), hat="beret", hat_col=(0.15, 0.4, 0.8), scale=1.0)
    pb = Toon("pb", skin=(0.78, 0.55, 0.38), coat=(0.2, 0.75, 0.6), hairstyle="long", hair=(0.08, 0.05, 0.03), scale=1.0)
    for tn, lp, y in ((pa, (-1.0, -2.6, 0.5), 0), (pb, (1.0, -2.7, 0.5), 10)):
        parent(tn.root, T["top"])
        tn.root.location = lp
        tn.root.rotation_euler = (0, 0, math.radians(y))
        tn.root.scale = (1.4, 1.4, 1.4)
    rail = prim(bpy.ops.mesh.primitive_torus_add, "rail", (0, 0, 1.3), mat=M["lead"], major_radius=4.5, minor_radius=0.05)
    parent(rail, T["top"])
    for i in range(16):
        a = 2 * math.pi * i / 16
        pst = cyl(f"railpost{i}", (4.5 * math.cos(a), 4.5 * math.sin(a), 0.9), 0.05, 0.8, M["lead"], verts=8)
        parent(pst, T["top"])
    tcl, tcm = cue("climb"), cue("comments")
    for f, t in frames():
        pa.pose(f, t, arm_side=(30, 150 + 20 * math.sin(t * 10)), arms=(20, 0), eyes="happy", mouth="grin", look=(0.4, 0), head=(-10, 0, 8),
                jump=0.12 * abs(math.sin(t * 5)))
        pb.pose(f, t, arms=(60, 60), arm_side=(-10, -10), eyes="wide", mouth="O" if t < tcm else "smile", brows=1, look=(0, -1),
                head=(10, -25, 0), bounce=0.02 * math.sin(t * 30))
    cam, aim = camera(24, 3.0, pa.root)
    c0 = topw @ __import__("mathutils").Vector((0, -3.4, 1.2))

    def cf(t):
        ang = math.radians(-35 + 45 * ease_io(t / DUR[11]))
        r_ = 8.0
        return add((c0.x + r_ * math.sin(ang), c0.y - r_ * math.cos(ang), c0.z + 3.0 + 0.4 * math.sin(t)), drift(t, 0.05)), \
            add((c0.x, c0.y + 0.4, c0.z - 0.4), drift(t, 0.03, 2))
    animate_cam(cam, aim, cf)


SCENES = {0: sc0_hook, 1: sc1_builders, 2: sc2_lean, 3: sc3_war, 4: sc4_soil, 5: sc5_trick, 6: sc6_banana, 7: sc7_closed,
          8: sc8_lead, 9: sc9_worked, 11: sc11_climb}


# ================================================================= render
def setup_render():
    if ENGINE == "CYCLES":
        SC.render.engine = "CYCLES"
        SC.cycles.samples = SAMPLES
        SC.cycles.use_denoising = True
    else:
        for e in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
            try:
                SC.render.engine = e
                break
            except Exception:
                continue
        SC.eevee.taa_render_samples = SAMPLES
        for attr, val in (("use_raytracing", True), ("use_fast_gi", True), ("use_shadows", True), ("clamp_surface_indirect", 4.0),
                          ("use_volumetric_shadows", True)):
            try:
                setattr(SC.eevee, attr, val)
            except Exception:
                pass
        try:
            SC.eevee.ray_tracing_options.use_denoise = True
        except Exception:
            pass
    SC.render.use_motion_blur = True  # smooth, filmic motion
    try:
        SC.render.motion_blur_shutter = 0.5
    except Exception:
        pass
    SC.view_settings.view_transform = "AgX"
    try:
        SC.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    SC.view_settings.exposure = EXPOSURE.get(SCENE, 0.0)
    if OUTFMT == "MP4" and not STILLS:
        os.makedirs(OUTDIR, exist_ok=True)
        try:
            SC.render.image_settings.media_type = "VIDEO"
        except Exception:
            pass
        SC.render.image_settings.file_format = "FFMPEG"
        SC.render.ffmpeg.format = "MPEG4"
        SC.render.ffmpeg.codec = "H264"
        SC.render.ffmpeg.constant_rate_factor = "PERC_LOSSLESS"
        SC.render.ffmpeg.ffmpeg_preset = "GOOD"
        SC.render.filepath = os.path.join(OUTDIR, f"s{SCENE}.mp4")
        SC.render.use_file_extension = False
    else:
        SC.render.image_settings.file_format = "PNG"
        SC.render.image_settings.color_mode = "RGB"
        out = os.path.join(OUTDIR, f"s{SCENE}")
        os.makedirs(out, exist_ok=True)
        SC.render.filepath = os.path.join(out, "")
    SC.frame_start, SC.frame_end = F0, min(F1, NF)


EXPOSURE = {1: -0.6, 2: -0.6, 3: -0.3, 4: -0.4, 5: -0.6, 6: -0.4, 8: -0.5, 9: -0.3}

if __name__ == "__main__":
    mats()
    SCENES[SCENE]()
    setup_render()
    rb_bake()
    if STILLS:
        SC.render.use_motion_blur = False
        for fr in STILLS:
            SC.frame_set(fr)
            SC.render.filepath = os.path.join(OUTDIR, f"s{SCENE}", f"{fr:04d}.png")
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
