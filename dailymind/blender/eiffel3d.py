"""Real-3D plates for "The Eiffel Tower was supposed to be torn down... and a RADIO saved it" (The DailyMind.).

v3 of the Blender pipeline (after Pisa): every toon pose channel is smoothed (no snapping between expressions/poses),
toons have elbows/knees/thumbs, and every camera path is sampled then zero-lag smoothed (no jerks at path joins).
Same engine otherwise: Bullet rigid bodies baked per scene, volumetric dust, classic dark look.
(The Pisa notes below describe the shared engine.)

v2 of the Blender pipeline (after the airplane video): REAL 3D toon characters (blender/toon3d.py, no flat sprites),
REAL rigid-body physics (Bullet, baked: falling stones, scaffolding, crates, soil grains, lead ingots),
cinematic cameras (eased paths + organic handheld drift + DOF + motion blur), dusk/floodlit "classic dark" look.
Text, slams, stamps, splats, music/SFX and the end card are composited later by ultimate/make_pisa3d.py.

Run (bpy module):   python eiffel3d.py -- SCENE OUTDIR [RES_PCT=100] [SAMPLES=64] [ENGINE=EEVEE] [F0] [F1]
Run (Blender app):  blender -b -P eiffel3d.py -- SCENE OUTDIR ...        (RTX PC: PLATE_FMT=MP4)
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
PLAN = json.load(open(os.path.join(ROOT, "eiffel", "plan.json")))
DUR, START, ABS = PLAN["durs"], PLAN["starts"], PLAN["abs"]
FPS = 30
NF = int(math.ceil(DUR[SCENE] * FPS)) + 1
F0 = int(argv[5]) if len(argv) > 5 else 1
F1 = int(argv[6]) if len(argv) > 6 else NF

bpy.ops.wm.read_factory_settings(use_empty=True)
from toon3d import Toon, bake_all  # noqa: E402  (after the factory reset)

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
    M["iron"] = noisy("iron", (0.32, 0.2, 0.12), (0.45, 0.3, 0.18), scale=8.0, rough=0.5, metal=0.6, bump=0.1)
    M["iron_dark"] = noisy("iron_dark", (0.16, 0.12, 0.1), (0.26, 0.2, 0.15), scale=8.0, rough=0.5, metal=0.6, bump=0.1)
    M["gold_light"] = emission("gold_light", (1.0, 0.72, 0.3), 9.0)
    M["red_light"] = emission("red_light", (1.0, 0.1, 0.05), 20.0)
    M["gravel"] = noisy("gravel", (0.45, 0.4, 0.33), (0.6, 0.55, 0.46), scale=2.0, rough=0.95, bump=0.3, coords="Generated")
    M["slate"] = noisy("slate", (0.18, 0.2, 0.26), (0.28, 0.3, 0.36), scale=6.0, rough=0.6)
    M["leaves"] = noisy("leaves", (0.05, 0.14, 0.04), (0.12, 0.26, 0.08), scale=3.0, rough=0.9, bump=0.5)
    M["paper"] = noisy("paper", (0.9, 0.84, 0.66), (0.97, 0.92, 0.78), scale=4.0, rough=0.8, bump=0.05)
    M["ink"] = pbr("ink", (0.05, 0.04, 0.04), 0.5)
    M["red_ink"] = pbr("red_ink", (0.75, 0.05, 0.05), 0.4)
    M["crane"] = noisy("crane", (0.85, 0.55, 0.08), (0.95, 0.65, 0.15), scale=6.0, rough=0.5, metal=0.3)
    M["burlap"] = noisy("burlap", (0.5, 0.38, 0.22), (0.62, 0.48, 0.3), scale=20.0, rough=0.9, bump=0.3)


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


def _smooth_seq(vals, alpha):
    fw = [vals[0]]
    for v in vals[1:]:
        fw.append(tuple(p + alpha * (x - p) for p, x in zip(fw[-1], v)))
    bw = [fw[-1]]
    for v in reversed(fw[:-1]):
        bw.append(tuple(p + alpha * (x - p) for p, x in zip(bw[-1], v)))
    return list(reversed(bw))


def animate_cam(cam, aim, fn, lens_fn=None, roll_fn=None, smooth=0.12, shakes=None):
    """Sample the camera path, smooth it (zero-lag, removes every jerk/joint), THEN add impact shakes on top."""
    ts = [t for _, t in frames()]
    cs = _smooth_seq([tuple(fn(t)[0]) for t in ts], smooth)
    as_ = _smooth_seq([tuple(fn(t)[1]) for t in ts], smooth * 0.8)
    for (f, t), c, a in zip(frames(), cs, as_):
        if shakes:
            c = add(c, shakes(t))
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



# ---------------------------------------------------------------- the Eiffel tower (generic wrought-iron lattice tower)
from mathutils import Vector  # noqa: E402

TH = 100.0  # tower height (stylised scale)


def tw(z):
    """half-width of the tower at height z."""
    return 23.0 * math.exp(-z / 32.0) + 1.0


def beams_mesh(name, beams, mat):
    """One mesh from many thin square beams [(p0, p1, thick), ...] — fast even with 1000+ beams."""
    verts, faces = [], []
    for p0, p1, th in beams:
        a, b = Vector(p0), Vector(p1)
        d = b - a
        if d.length < 1e-6:
            continue
        d.normalize()
        up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        u = d.cross(up).normalized() * th / 2
        v = d.cross(u).normalized() * th / 2
        n = len(verts)
        for base in (a, b):
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                verts.append(tuple(base + u * su + v * sv))
        faces += [(n, n + 1, n + 2, n + 3), (n + 7, n + 6, n + 5, n + 4)]
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((n + k, n + 4 + k, n + 4 + k2, n + k2))
    o = mesh_obj(name, verts, faces, mat)
    return o


def eiffel(name="E", bands=12, antenna=True, lights=True):
    """Returns dict(root, bands[list of (obj, z0)], antenna, top_z, platforms). Bands let the tower assemble floor by floor."""
    root = empty(name + "_root")
    iron = M["iron"]
    zs = [0.0]
    while zs[-1] < 94:
        zs.append(zs[-1] + (1.8 if zs[-1] < 18 else 2.6))
    band_beams = [[] for _ in range(bands)]
    band_h = 96.0 / bands

    def bidx(z):
        return min(bands - 1, int(z / band_h))

    def add_b(p0, p1, th):
        band_beams[bidx(min(p0[2], p1[2]) + 0.01)].append((p0, p1, th))
    for i in range(len(zs) - 1):
        z0, z1 = zs[i], zs[i + 1]
        w0, w1 = tw(z0), tw(z1)
        th = 0.75 - 0.5 * (z0 / 96)
        for sx in (-1, 1):
            for sy in (-1, 1):
                add_b((sx * w0, sy * w0, z0), (sx * w1, sy * w1, z1), th)
        if z1 <= 18.5:  # four separate legs, each a lattice box
            lw0, lw1 = 7.5 - 0.22 * z0, 7.5 - 0.22 * z1
            for sx in (-1, 1):
                for sy in (-1, 1):
                    c0 = [(sx * w0, sy * w0), (sx * (w0 - lw0), sy * w0), (sx * (w0 - lw0), sy * (w0 - lw0)), (sx * w0, sy * (w0 - lw0))]
                    c1 = [(sx * w1, sy * w1), (sx * (w1 - lw1), sy * w1), (sx * (w1 - lw1), sy * (w1 - lw1)), (sx * w1, sy * (w1 - lw1))]
                    for k in range(1, 4):
                        add_b((*c0[k], z0), (*c1[k], z1), th * 0.8)
                    for k in range(4):
                        k2 = (k + 1) % 4
                        add_b((*c0[k], z0), (*c1[k2], z1), th * 0.35)
                        add_b((*c0[k2], z0), (*c1[k], z1), th * 0.35)
                        if i % 3 == 0:
                            add_b((*c0[k], z0), (*c0[k2], z0), th * 0.4)
        else:  # one tapering shaft: X bracing on every face + rings
            for f_ in range(4):
                a0 = [(-w0, -w0), (w0, -w0), (w0, w0), (-w0, w0)]
                a1 = [(-w1, -w1), (w1, -w1), (w1, w1), (-w1, w1)]
                k2 = (f_ + 1) % 4
                add_b((*a0[f_], z0), (*a1[k2], z1), th * 0.4)
                add_b((*a0[k2], z0), (*a1[f_], z1), th * 0.4)
                if i % 2 == 0:
                    add_b((*a0[f_], z0), (*a0[k2], z0), th * 0.45)
    # the great arches between the legs
    for side in range(4):
        n = 16
        pts = []
        for k in range(n + 1):
            u = -1 + 2 * k / n
            x = u * (tw(0) - 7.5) * 0.98
            z = 14.5 * math.sqrt(max(0.0, 1 - u * u)) + 1.0 * (1 - abs(u))
            pts.append((x, z))
        for k in range(n):
            (x0, z0), (x1, z1) = pts[k], pts[k + 1]
            y0, y1 = tw(z0) * 0.98, tw(z1) * 0.98
            if side == 0:
                add_b((x0, -y0, z0), (x1, -y1, z1), 0.55)
            elif side == 1:
                add_b((x0, y0, z0), (x1, y1, z1), 0.55)
            elif side == 2:
                add_b((-y0, x0, z0), (-y1, x1, z1), 0.55)
            else:
                add_b((y0, x0, z0), (y1, x1, z1), 0.55)
    out = []
    for b in range(bands):
        if band_beams[b]:
            o = beams_mesh(f"{name}_band{b}", band_beams[b], iron)
            parent(o, root)
            out.append((o, b * band_h))
    plats = []
    for z, extra, th in ((18.0, 2.5, 2.0), (39.0, 1.6, 1.6), (89.0, 0.9, 1.4)):
        w = tw(z) + extra
        p = box(f"{name}_plat{z}", (0, 0, z), (2 * w, 2 * w, th), M["iron_dark"], bevel=0.1)
        parent(p, root)
        if lights:  # thin glowing edge bars, not a slab
            for k_, (cx, cy, sx_, sy_) in enumerate(((0, -w, 2 * w, 0.18), (0, w, 2 * w, 0.18), (-w, 0, 0.18, 2 * w), (w, 0, 0.18, 2 * w))):
                rim = box(f"{name}_rim{z}_{k_}", (cx, cy, z + th / 2 + 0.1), (sx_ + 0.2, sy_ + 0.2, 0.18), M["gold_light"])
                parent(rim, root)
        plats.append(p)
    cap = box(f"{name}_cap", (0, 0, 92.5), (3.6, 3.6, 5.0), M["iron_dark"], bevel=0.15)
    parent(cap, root)
    ant = None
    if antenna:
        ant = cyl(f"{name}_antenna", (0, 0, 95 + 6), 0.35, 12, M["iron"], verts=12)
        parent(ant, root)
        tip = sphere(f"{name}_tip", (0, 0, 107.2), 0.6, M["red_light"])
        parent(tip, ant)
        tip.location = (0, 0, 0.52)
        tip.scale = (0.6 / 0.35, 0.6 / 0.35, 0.6 / 6)
    if lights:  # gold sparkle bulbs along the four corner members (night illumination)
        src = sphere(f"{name}_bulbsrc", (0, 0, -999), 0.17, M["gold_light"], segs=8)
        for z in [1.5 + 2.4 * k for k in range(38)]:
            w = tw(z) + 0.15
            for sx in (-1, 1):
                for sy in (-1, 1):
                    b_ = instance(src, f"{name}_bulb", (sx * w, sy * w, z))
                    parent(b_, root)
    return dict(root=root, bands=out, antenna=ant, plats=plats)


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



def wave_rings(name, center, t_on, n=4, period=0.35, speed=40.0, life=1.6, col=(0.4, 0.9, 1.0), inward=False, thick=0.5):
    """Glowing radio-wave rings (tori) expanding from (or shrinking into) a point."""
    m = emission(name + "m", col, 5.0)
    for i in range(n):
        o = prim(bpy.ops.mesh.primitive_torus_add, f"{name}{i}", center, mat=m, major_radius=1.0, minor_radius=0.025 * thick, major_segments=64,
                 minor_segments=8)
        o.rotation_euler = (math.pi / 2 * 0 + 0.0, 0, 0)
        t0 = t_on + i * period
        for f, t in frames():
            k = t - t0
            if k < 0 or k > life:
                key(o, f, scale=(1e-3, 1e-3, 1e-3))
                continue
            r = speed * (life - k) if inward else 0.5 + speed * k
            r = max(0.3, r)
            fade = max(0.05, 1 - k / life) if not inward else min(1.0, k * 3)
            key(o, f, scale=(r, r, max(0.02, r * fade)))


def paris(night=True):
    """Haussmann blocks with lit windows and slate roofs, round trees, street lamps, the Champ de Mars lawn."""
    ground(M["grass"])
    box("champ_path", (0, -60, 0.03), (16, 100, 0.06), M["gravel"])
    box("champ_path2", (0, 0, 0.02), (90, 90, 0.04), M["gravel"])
    rr = random.Random(21)
    win_m = emission("parwin", (1.0, 0.72, 0.38), 6.0 if night else 0.0)
    cream = [(0.82, 0.76, 0.62), (0.88, 0.82, 0.68), (0.78, 0.7, 0.56)]
    for row, y0 in enumerate((110, 150, 190)):
        for i in range(18):
            x = -200 + i * 24 + rr.uniform(-3, 3) + row * 8
            y = y0 + rr.uniform(-4, 4)
            h = rr.uniform(16, 24)
            hm = noisy(f"hm{row}_{i}", cream[i % 3], tuple(min(1, c * 1.08) for c in cream[i % 3]), scale=3, rough=0.9, bump=0.15)
            box(f"blk{row}_{i}", (x, y, h / 2), (20, 14, h), hm)
            rf = prim(bpy.ops.mesh.primitive_cylinder_add, f"mans{row}_{i}", (x, y, h + 2.2), (10.5, 7.5, 2.4), mat=M["slate"], vertices=4)
            rf.rotation_euler = (0, 0, math.pi / 4)
            rf.scale = (10.5 * 1.41, 7.5 * 1.41, 2.4)
            if night:
                for w_ in range(rr.randint(3, 7)):
                    box(f"pw{row}_{i}_{w_}", (x + rr.uniform(-8, 8), y - 7.1, rr.uniform(3, h - 2)), (1.4, 0.2, 2.2), win_m)
    for side in (-1, 1):
        for k in range(8):
            x = side * 34
            y = -24 - k * 13
            sphere(f"tree{side}_{k}", (x, y, 6), 1, M["leaves"], scale=(3.2, 3.2, 3.6))
            cyl(f"trunk{side}_{k}", (x, y, 2), 0.35, 4, M["wood"], verts=10)
    if night:
        for i, (x, y) in enumerate(((9, -24), (-9, -24), (9, -48), (-9, -48), (9, -72), (-9, -72))):
            lamp(f"plamp{i}", (x, y), 300)


def lightbulb(name, loc, t_on):
    glass = pbr(name + "g", (1.0, 0.95, 0.7), 0.1, emit=(1.0, 0.85, 0.4), estr=8.0)
    b = sphere(name, loc, 0.35, glass)
    base = cyl(name + "base", (0, 0, -0.38), 0.16, 0.22, M["iron"], verts=12)
    parent(base, b)
    base.location = (0, 0, -1.0)
    base.scale = (0.16 / 0.35, 0.16 / 0.35, 0.11 / 0.35)
    L = light("POINT", loc, 0.0, (1.0, 0.85, 0.5), 0.2)
    for f, t in frames():
        k = (t - t_on) / 0.35
        s_ = 0.35 * (back_out(min(1.0, k)) if k > 0 else 0.0) + 1e-3
        key(b, f, loc=(loc[0], loc[1], loc[2] + 0.06 * math.sin(t * 5)), scale=(s_, s_, s_))
        L.data.energy = 300 * min(1.0, max(0.0, k)) * (1 + 0.15 * math.sin(t * 30))
        L.data.keyframe_insert("energy", frame=f)
    return b


def text3d(name, body, loc, size, mat, rot=(math.pi / 2, 0, 0), extrude=0.08):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    o = bpy.data.objects.new(name, cu)
    link(o)
    o.location = loc
    o.rotation_euler = rot
    cu.materials.append(mat)
    return o


def gustave(scale=1.6):
    return Toon("gustave", skin=(0.95, 0.78, 0.66), coat=(0.12, 0.13, 0.22), pants=(0.1, 0.1, 0.14), hair=(0.55, 0.5, 0.48),
                hat="tophat", hat_col=(0.06, 0.06, 0.07), beard=True, mustache=True, scale=scale)


def crowd1889(n, center, radius, seed, face_to=(0, 0), scale=1.5):
    rr = random.Random(seed)
    cols = [(0.35, 0.15, 0.2), (0.15, 0.25, 0.4), (0.4, 0.3, 0.15), (0.2, 0.35, 0.25), (0.5, 0.2, 0.35), (0.25, 0.22, 0.3)]
    skins = [(0.96, 0.76, 0.62), (0.9, 0.68, 0.52), (0.98, 0.84, 0.72)]
    out = []
    for i in range(n):
        p = (center[0] + rr.uniform(-radius[0], radius[0]), center[1] + rr.uniform(-radius[1], radius[1]), 0)
        tn = Toon(f"c{seed}_{i}", skin=skins[i % 3], coat=cols[i % 6], hair=(rr.uniform(0.1, 0.5), 0.1, 0.05),
                  hairstyle=rr.choice(["short", "long", "short"]), hat=rr.choice(["tophat", "beret", "fedora", None]),
                  hat_col=rr.choice([(0.08, 0.08, 0.1), (0.35, 0.1, 0.12), (0.2, 0.2, 0.3)]), mustache=rr.random() < 0.4, outline=0.01)
        yaw = math.degrees(math.atan2(-(face_to[0] - p[0]), (face_to[1] - p[1]))) + 180
        place(tn, p, yaw, scale * rr.uniform(0.92, 1.06))
        out.append((tn, rr.uniform(0, 6)))
    return out


def crane_wreck(name, base=(-40, -14, 0), boom_tip=(-14, -14, 62)):
    """A tall demolition crane with a wrecking ball on a cable (the ball is animated by the caller)."""
    mast = box(name + "_mast", (base[0], base[1], 32), (2.5, 2.5, 64), M["crane"])
    boom = beams_mesh(name + "_boom", [((base[0], base[1], 63), boom_tip, 1.2), ((base[0] - 8, base[1], 63), (base[0], base[1], 63), 1.2)], M["crane"])
    cab = box(name + "_cab", (base[0] + 1.5, base[1] - 2, 60), (4, 3, 3), M["crane"], bevel=0.1)
    cw = box(name + "_cw", (base[0] - 9, base[1], 62), (3, 3, 3), M["iron_dark"])
    ball = sphere(name + "_ball", boom_tip, 2.6, M["iron_dark"])
    rope = cyl(name + "_rope", boom_tip, 0.12, 1.0, M["iron_dark"], verts=8)
    return dict(ball=ball, rope=rope, tip=boom_tip, parts=[mast, boom, cab, cw])


def pendulum(ball, rope, tip, f, ang_deg, L=26.0, axis="x"):
    a = math.radians(ang_deg)
    p = (tip[0] + L * math.sin(a), tip[1], tip[2] - L * math.cos(a))
    key(ball, f, loc=p)
    mid = ((tip[0] + p[0]) / 2, (tip[1] + p[1]) / 2, (tip[2] + p[2]) / 2)
    key(rope, f, loc=mid, rot=(0, a, 0), scale=(0.12, 0.12, L / 2))


def night_sky():
    world_dusk(top=(0.008, 0.012, 0.045), horizon=(0.12, 0.08, 0.18), strength=1.0)
    stars()


def gold_spots(energy=70000):
    tgt = empty("gold_tgt", (0, 0, 45))
    for a in (-50, 0, 50, 180):
        L = light("SPOT", (34 * math.sin(math.radians(a)), -34 * math.cos(math.radians(a)), 0.5), energy, (1.0, 0.72, 0.38), 0.6, spot_deg=45)
        aim_at(L, tgt)


# ================================================================= scenes
def sc0_hook():
    """1909, night: a demolition crane swings a wrecking ball at the golden tower ('torn down')... on 'radio' glowing
    waves pulse from the antenna, the ball bounces back on a spring and the workers' jaws drop ('saved it')."""
    night_sky()
    paris(night=True)
    E = eiffel()
    gold_spots()
    light("SUN", (0, 0, 50), 0.4, (0.5, 0.6, 1.0), 2, rot=(math.radians(60), 0, math.radians(140)))
    tt, tr, ts = cue("torn"), cue("radio0"), cue("saved")
    C = crane_wreck("wc", base=(-46, -16, 0), boom_tip=(-20, -16, 64))
    for f, t in frames():
        if t < tt - 0.3:
            ang = -38 + 2 * math.sin(t * 2)
        elif t < tr:
            k = ease((t - tt + 0.3) / (tr - tt + 0.3))
            ang = -38 + 70 * k  # swings in towards the tower
        else:
            ang = 32 - 62 * (1 - math.exp(-3.5 * (t - tr))) + spring(t, tr, 10, 1.4, 2.5)
        pendulum(C["ball"], C["rope"], C["tip"], f, ang)
    wave_rings("hookwave", (0, 0, 107), tr - 0.1, n=5, period=0.22, speed=30, life=1.4)
    wk = [Toon("w1", coat=(0.3, 0.32, 0.4), hat="cap", hat_col=(0.25, 0.2, 0.18), mustache=True),
          Toon("w2", skin=(0.9, 0.68, 0.52), coat=(0.45, 0.28, 0.18), hat="cap", hat_col=(0.15, 0.15, 0.2))]
    place(wk[0], (-5.5, -45.5, 0), 50, 1.7)
    place(wk[1], (-2.5, -48.0, 0), 40, 1.7)
    for f, t in frames():
        for i, w in enumerate(wk):
            if t < tr:
                w.pose(f, t, arm_side=(150, 150) if i == 0 else (20, 20), arms=(0, 0) if i == 0 else (40, 40), eyes="happy",
                       mouth="grin", look=(0.4, 0.8), head=(-20, 18, 0), jump=0.12 * abs(math.sin(t * 6 + i)) if i == 0 else 0)
            else:
                w.pose(f, t, arm_side=(30, 30), arms=(70, 70), eyes="wide", mouth="O", brows=1, look=(0.3, 1), head=(-20, 22, 0),
                       jump=0.0)
    focus = empty("focus", (-4, -47, 2))
    cam, aim = camera(24, 4.0, focus)
    light("POINT", (-30, -30, 40), 30000, (1.0, 0.75, 0.5), 2.0)  # rim light on the wrecking ball

    def cf(t):
        k = ease_io(t / DUR[0])
        c = lerp((6, -60, 2.4), (-12, -60, 4.0), k)
        a = lerp((-4, -40, 6.5), (-8, -14, 46), ease_io((t - 1.0) / 2.4))
        return add(c, drift(t, 0.08)), add(a, drift(t, 0.06, 2))
    animate_cam(cam, aim, cf, shakes=lambda t: shake(t, tr + 0.05, 0.4, 0.6))
    for f, t in frames():
        key(focus, f, loc=lerp((-4, -47, 2), (-10, -14, 40), ease_io((t - 1.0) / 1.4)))


def sc1_build():
    """Paris 1889, golden dusk: the tower ASSEMBLES band by band (springy drop-in, sparks of dust), Gustave Eiffel
    proudly presents it to a crowd in top hats; the camera cranes from him to the very top; fireworks on 'fair'."""
    world_dusk(top=(0.03, 0.05, 0.18), horizon=(1.0, 0.5, 0.22), strength=1.1)
    paris(night=False)
    light("SUN", (0, 0, 50), 3.0, (1.0, 0.7, 0.42), 3, rot=(math.radians(76), 0, math.radians(-50)))
    light("AREA", (-30, -60, 25), 9000, (0.6, 0.7, 1.0), 30)
    E = eiffel(antenna=False, lights=False)
    tg, ttl, tf = cue("gustave"), cue("tallest"), cue("fair")
    n = len(E["bands"])
    for j, (o, z0) in enumerate(E["bands"]):
        t_on = 0.15 + j * 0.33
        for f, t in frames():
            k = (t - t_on) / 0.4
            if k <= 0:
                key(o, f, loc=(0, 0, 40), scale=(1e-3, 1e-3, 1e-3))
            else:
                kk = min(1.0, k)
                sq = 1.0 + 0.06 * spring(t, t_on + 0.4, 1, 3, 7)
                key(o, f, loc=(0, 0, 25 * (1 - kk) ** 2), scale=(1 / math.sqrt(sq), 1 / math.sqrt(sq), sq))
    for p_ in E["plats"]:
        zp = p_.location.z
        s0 = tuple(p_.scale)
        t_on = 0.15 + (zp / 96 * n) * 0.33 + 0.3
        for f, t in frames():
            s_ = back_out(min(1.0, max(0.0, (t - t_on) / 0.35)))
            key(p_, f, scale=tuple(max(1e-3, v * s_) for v in s0))
    G = gustave()
    place(G, (3, -36, 0), 15, 1.8)
    cr = crowd1889(10, center=(-15, -32), radius=(6, 4), seed=31, face_to=(0, 0)) + crowd1889(6, center=(18, -30), radius=(4, 3), seed=32, face_to=(0, 0))
    for f, t in frames():
        present = t > tg - 0.3
        G.pose(f, t, arm_side=(150, 40) if present else (10, 10), arms=(30, 60) if present else (20, 20), eyes="happy" if present else "open",
               mouth="grin", look=(-0.3, 0.6), head=(-25, 12 if present else 0, 0), jump=0.0, brows=0.6)
        pose_crowd(cr, f, t, "cheer" if t > tf - 0.2 else "happy")
    for j, (c_, col) in enumerate((((-30, 30, 70), (1.0, 0.6, 0.15)), ((28, 20, 78), (0.35, 0.6, 1.0)), ((0, 45, 92), (1.0, 0.3, 0.45)))):
        firework(f"fw1{j}", c_, tf - 0.1 + 0.25 * j, col)
    focus = empty("focus", (3, -36, 2.5))
    cam, aim = camera(22, 3.5, focus)

    def cf(t):
        k = ease_io((t - 0.5) / 4.5)
        c = lerp((6.5, -43.5, 2.5), (14, -95, 22), k)
        a = lerp((3, -36, 3.0), (0, 0, 60), k)
        return add(c, drift(t, 0.07)), add(a, drift(t, 0.05, 2))
    animate_cam(cam, aim, cf)
    for f, t in frames():
        key(focus, f, loc=lerp((3, -36, 2.5), (0, 0, 50), ease_io((t - 0.6) / 4.0)))


def protest_sign(name, word, loc, holder_t):
    board = box(name, loc, (2.4, 0.12, 1.3), M["paper"], bevel=0.03)
    stick = cyl(name + "st", (loc[0], loc[1] + 0.05, loc[2] - 1.4), 0.06, 1.6, M["wood"], verts=8)
    tx = text3d(name + "tx", word, (loc[0], loc[1] - 0.09, loc[2] - 0.05), 0.55, M["ink"])
    grp = empty(name + "grp", (0, 0, 0))
    for o in (board, stick, tx):
        parent(o, grp)
    return grp


def sc2_hate():
    """Parisians hate it: an angry crowd of artists in berets waves protest signs and throws tomatoes (real arcs that
    splat and roll); the camera tracks along the signs, then pushes in on a furious painter on 'monstrous'."""
    world_dusk(top=(0.04, 0.06, 0.2), horizon=(0.95, 0.45, 0.25), strength=1.0)
    paris(night=False)
    light("SUN", (0, 0, 50), 2.8, (1.0, 0.7, 0.45), 3, rot=(math.radians(70), 0, math.radians(-40)))
    light("AREA", (-30, -60, 25), 9000, (0.6, 0.7, 1.0), 30)
    E = eiffel(antenna=False, lights=False)
    th_, tu, tm = cue("hated"), cue("useless"), cue("monstrous")
    g = box("ground_rb", (0, 0, -0.5), (400, 400, 1.0), None)
    g.hide_render = True
    rb(g, active=False, shape="BOX")
    artists = []
    rr = random.Random(5)
    for i in range(7):
        p = (-12 + i * 4.0 + rr.uniform(-0.6, 0.6), -40 + rr.uniform(-1.5, 1.5), 0)
        a_ = Toon(f"art{i}", skin=[(0.96, 0.76, 0.62), (0.88, 0.66, 0.5), (0.98, 0.84, 0.72)][i % 3],
                  coat=[(0.55, 0.2, 0.2), (0.2, 0.3, 0.5), (0.35, 0.3, 0.15), (0.45, 0.2, 0.45)][i % 4], hat="beret",
                  hat_col=[(0.1, 0.1, 0.12), (0.6, 0.12, 0.15), (0.15, 0.2, 0.45)][i % 3], mustache=i % 2 == 0, hairstyle="short")
        place(a_, p, rr.uniform(-12, 12), 1.6)
        artists.append(a_)
    words = ["NON!", "UGLY!", "USELESS", "NON!", "MONSTER", "UGLY!", "NON!"]
    signs = [protest_sign(f"sign{i}", words[i], (0, 0, 0), 0) for i in range(7)]
    for f, t in frames():
        for i, (a_, sg) in enumerate(zip(artists, signs)):
            ph = t * 5 + i
            up = 0.25 * abs(math.sin(ph))
            a_.pose(f, t, arm_side=(160, 160), arms=(0, 0), eyes="open", mouth="talk", talk=0.5 + 0.5 * abs(math.sin(ph * 1.7)), brows=-1,
                    look=(0, 0.2), head=(0, -5, 4 * math.sin(ph)), jump=up * 0.5)
            r_ = a_.root.location
            key(sg, f, loc=(r_[0], r_[1] + 0.35, 1.6 * 2.15 + 1.3 + up * 0.8), rot=(0, math.radians(6 * math.sin(ph)), 0))
    # tomatoes: kinematic arcs from the crowd towards the tower, then real physics (bounce + roll)
    tom = pbr("tomato", (0.85, 0.08, 0.05), 0.3)
    for j in range(10):
        t0 = th_ - 0.2 + j * 0.42
        src = (-12 + (j * 3.7) % 26, -39.5, 4.0)
        tgt = (-6 + (j * 5.3) % 14, -14 + (j % 3) * 2, 0.6)
        o = sphere(f"tom{j}", src, 0.5, tom, segs=14)
        dur = 0.9
        for f, t in frames():
            kk = min(max((t - t0) / dur, 0.0), 1.0)
            show(o, f, t >= t0)
            if t <= t0 + dur:
                key(o, f, loc=(lerp(src[0], tgt[0], kk), lerp(src[1], tgt[1], kk), lerp(src[2], tgt[2], kk) + 9 * kk * (1 - kk)))
        rb(o, mass=0.3, bounce=0.2, shape="SPHERE", release=t0 + dur)
    cam, aim = camera(26, 3.2, artists[3].root)

    def cf(t):
        k = ease_io(t / (tm + 0.2))
        c = lerp((-14, -58, 3.2), (0.5, -49.0, 3.7), k)
        a = lerp((-4, -40, 4.0), (0.5, -40, 4.3), k)
        k2 = ease_io((t - tm - 0.3) / 1.0)
        c = lerp(c, (2, -64, 7), k2)
        a = lerp(a, (0, -20, 24), k2)
        return add(c, drift(t, 0.06)), add(a, drift(t, 0.04, 2))
    animate_cam(cam, aim, cf)


def sc3_permit():
    """A golden permit scroll unrolls ('20 YEARS'), the years tick 1889 -> 1909 in 3D, then a demolition crane rolls in
    and the tower trembles ('it comes down')."""
    night_sky()
    paris(night=True)
    E = eiffel(antenna=False)
    gold_spots()
    tp, tt20, t19, tc = cue("permit"), cue("twenty"), cue("nineteen"), cue("comes")
    scroll = box("scroll", (0, -62, 9), (16, 0.15, 9), M["paper"], bevel=0.1)
    rod_t = cyl("rodt", (0, -62.2, 13.6), 0.45, 17, M["wood"], verts=16, rot=(0, math.pi / 2, 0))
    rod_b = cyl("rodb", (0, -62.2, 4.4), 0.45, 17, M["wood"], verts=16, rot=(0, math.pi / 2, 0))
    t1 = text3d("ptx1", "PERMIT", (0, -62.3, 11.3), 2.0, M["ink"])
    t2 = text3d("ptx2", "20 YEARS", (0, -62.3, 7.6), 2.6, M["red_ink"])
    for f, t in frames():
        k = back_out(min(1.0, max(0.0, (t - tp + 0.5) / 0.6)), 1.2)
        h = max(0.02, 9 * k)
        key(scroll, f, loc=(0, -62, 13.6 - h / 2), scale=(8, 0.075, h / 2))
        key(rod_b, f, loc=(0, -62.2, 13.6 - h))
        show(t1, f, k > 0.6)
        show(t2, f, t > tt20 - 0.1)
    years = []
    for y in range(1889, 1910):
        o = text3d(f"yr{y}", str(y), (0, -62.3, 2.0), 2.2, M["gold_light"])
        years.append((y, o))
    for f, t in frames():
        k = min(1.0, max(0.0, (t - tt20 - 0.2) / max(0.3, t19 - tt20 - 0.1)))
        cur = 1889 + int(round(20 * ease(k)))
        for y, o in years:
            show(o, f, y == cur and t > tt20 + 0.1)
    C = crane_wreck("wc", base=(-46, -16, 0), boom_tip=(-20, -16, 64))
    parts = C["parts"] + [C["ball"], C["rope"]]
    for f, t in frames():
        k = ease_io((t - tc + 1.2) / 1.2)
        dx = -60 * (1 - k)
        for p_ in C["parts"]:
            if f == 1:
                p_["x0"] = p_.location.x
            key(p_, f, loc=(p_["x0"] + dx, p_.location.y, p_.location.z))
        a = math.radians(-30 + 3 * math.sin(t * 2))
        tip = (C["tip"][0] + dx, C["tip"][1], C["tip"][2])
        p = (tip[0] + 26 * math.sin(a), tip[1], tip[2] - 26 * math.cos(a))
        key(C["ball"], f, loc=p)
        key(C["rope"], f, loc=((tip[0] + p[0]) / 2, tip[1], (tip[2] + p[2]) / 2), rot=(0, a, 0), scale=(0.12, 0.12, 13))
        trem = 0.35 * math.sin(t * 40) * max(0.0, min(1.0, (t - tc) * 3)) * math.exp(-1.0 * max(0.0, t - tc))
        key(E["root"], f, rot=(0, math.radians(trem), math.radians(trem * 0.5)))
    _ = parts
    cam, aim = camera(28, 5.0, scroll)

    def cf(t):
        k = ease_io((t - tc + 1.6) / 1.6)
        c = lerp((2, -84, 8.5), (12, -120, 24), k)
        a = lerp((0, -62, 8.5), (-8, 0, 40), k)
        return add(c, drift(t, 0.05)), add(a, drift(t, 0.04, 2))
    animate_cam(cam, aim, cf, shakes=lambda t: shake(t, tc, 0.5, 0.6))


def sc4_clever():
    """Close-up: Gustave strokes his beard, thinking... DING — a glowing light bulb pops above his top hat; he grins and
    points up at his tower ('useful')."""
    world_dusk(top=(0.02, 0.03, 0.1), horizon=(0.5, 0.25, 0.2), strength=0.9)
    paris(night=True)
    E = eiffel(antenna=False)
    gold_spots(50000)
    tcl, tu = cue("clever"), cue("useful")
    G = gustave(1.8)
    place(G, (0, -40, 0), 0, 1.8)
    light("AREA", (3, -46, 4), 600, (1.0, 0.85, 0.7), 3, rot=(math.radians(75), 0, math.radians(20)))
    for f, t in frames():
        if t < tcl:
            G.pose(f, t, arms=(70, 20), arm_side=(10, 8), elbows=(120, 20), eyes="open", mouth="flat", brows=-0.4, look=(0.6, 0.6),
                   head=(10, 10, 8))
        elif t < tu - 0.3:
            G.pose(f, t, arms=(20, 20), arm_side=(10, 10), eyes="wide", mouth="O", brows=1.0, look=(0, 1), head=(0, 18, 0), jump=0.12 * max(0, 1 - (t - tcl) * 3))
        else:
            G.pose(f, t, arms=(40, 20), arm_side=(10, 160), elbows=(20, 10), eyes="happy", mouth="grin", brows=0.6, look=(0.5, 0.8),
                   head=(-15, 15, 0))
    lightbulb("bulb", (0, -40, 1.8 * 2.25 + 0.9 + 1.0), tcl)
    cam, aim = camera(40, 2.2, G.head)

    def cf(t):
        k = ease_io(t / DUR[4])
        c = lerp((2.5, -48.5, 3.6), (1.2, -46.0, 4.0), k)
        a = lerp((0, -40, 3.4), (0, -40, 4.0), k)
        return add(c, drift(t, 0.03)), add(a, drift(t, 0.02, 2))
    animate_cam(cam, aim, cf)


def anemometer(name, loc, spin_fn):
    hub = cyl(name + "post", (loc[0], loc[1], loc[2] + 1.2), 0.08, 2.4, M["iron"], verts=10)
    rot_ = empty(name + "rot", (loc[0], loc[1], loc[2] + 2.5))
    for k in range(3):
        a = 2 * math.pi * k / 3
        arm = cyl(f"{name}arm{k}", (0.6 * math.cos(a), 0.6 * math.sin(a), 0), 0.04, 1.2, M["iron"], verts=8, rot=(0, math.pi / 2, a))
        parent(arm, rot_)
        cup = sphere(f"{name}cup{k}", (1.2 * math.cos(a), 1.2 * math.sin(a), 0), 0.25, M["red"])
        parent(cup, rot_)
    for f, t in frames():
        key(rot_, f, rot=(0, 0, spin_fn(t)))


def sc5_science():
    """He makes it useful: a weather station spins on the top platform; then objects are dropped down a cable to study
    air resistance — a heavy ball plunges (real physics), a flat plate drifts (high air drag), a slider zips down the
    cable — and the camera dives after them."""
    world_dusk(top=(0.05, 0.09, 0.26), horizon=(0.95, 0.55, 0.3), strength=1.1)
    paris(night=False)
    light("SUN", (0, 0, 50), 3.0, (1.0, 0.75, 0.5), 3, rot=(math.radians(60), 0, math.radians(-40)))
    E = eiffel(antenna=False, lights=False)
    g = box("ground_rb", (0, 0, -0.5), (400, 400, 1.0), None)
    g.hide_render = True
    rb(g, active=False, shape="BOX")
    tw_, tdr = cue("weather"), cue("drops")
    hut = box("hut", (-1.0, 0.5, 91.2 + 1.4), (2.4, 2.0, 2.4), M["paper"], bevel=0.1)
    anemometer("anem", (1.2, -1.2, 92.2), lambda t: t * (6 + 10 * ease((t - tw_) / 1.0)))
    vane = box("vane", (1.5, 1.2, 95.0), (1.6, 0.06, 0.6), M["iron"])
    sci = Toon("sci", coat=(0.92, 0.92, 0.88), hair=(0.3, 0.2, 0.1), glasses=True, mustache=True, scale=1.0)
    place(sci, (0.0, -2.4, 92.25), 0, 0.9)
    # cable from the 2nd platform to the ground, slider + free-falling ball/plate
    p0, p1 = Vector((tw(39) + 1.0, -2, 39.5)), Vector((44, -30, 0.5))
    cable = beams_mesh("cable", [(tuple(p0), tuple(p1), 0.12)], M["iron_dark"])
    slider = sphere("slider", tuple(p0), 0.7, M["red"])
    for f, t in frames():
        k = max(0.0, t - tdr) ** 2 * 0.09
        key(slider, f, loc=tuple(p0.lerp(p1, min(1.0, k))))
    ball = sphere("dropball", (tw(39) + 1.5, -6, 41), 0.8, M["iron_dark"])
    rb(ball, mass=20, bounce=0.35, shape="SPHERE", release=tdr + 0.2, damp=0.0)
    plate = box("dropplate", (tw(39) + 1.5, -9, 41), (2.4, 2.4, 0.12), M["paper"])
    rb(plate, mass=0.4, bounce=0.1, shape="BOX", release=tdr + 0.2, damp=0.85)
    for f, t in frames():
        sci.pose(f, t, arms=(80, 20), arm_side=(10, 10), elbows=(90, 15), eyes="open" if t < tdr else "wide", mouth="smile" if t < tdr else "O",
                 look=(0.4, -0.6) if t > tdr else (0, 0.3), head=(15, -25 if t > tdr else 0, 0))
    cam, aim = camera(26, 6.0, sci.root)

    def cf(t):
        k = ease_io((t - tdr + 0.3) / 2.6)
        c = lerp((5.5, -10.5, 95.5), (40, -58, 22), k)
        fall = max(0.0, t - tdr - 0.2)
        bz = max(1.0, 41 - 4.9 * fall * fall)
        a = lerp((0, -1, 93.4), (tw(39) + 1.5, -6, bz), ease_io((t - tdr) / 0.8))
        return add(c, drift(t, 0.05)), add(a, drift(t, 0.03, 2))
    animate_cam(cam, aim, cf, smooth=0.18)


def sc6_antenna():
    """A giant radio antenna telescopes up out of the top with crackling glow; Gustave tips a sack and gold coins pour
    out (real rigid bodies) — 'with his own money'."""
    night_sky()
    paris(night=True)
    E = eiffel(antenna=True)
    gold_spots(55000)
    ta, tmn = cue("antenna"), cue("money")
    for f, t in frames():
        k = back_out(min(1.0, max(0.0, (t - ta + 0.9) / 0.6)), 1.4)
        key(E["antenna"], f, scale=(0.35, 0.35, max(1e-3, 6 * k)), loc=(0, 0, 95 + 6 * k))
    wave_rings("antwave", (0, 0, 107), ta - 0.1, n=3, period=0.3, speed=18, life=1.2)
    G = gustave(1.0)
    place(G, (-1.5, -tw(89) - 0.2, 89.7), 0, 1.0)
    sack = sphere("sack", (0, 0, 0), 0.5, M["burlap"], scale=(0.45, 0.4, 0.55))
    g_rb = box("plat_rb", (0, 0, 89), (2 * tw(89) + 1.8, 2 * tw(89) + 1.8, 1.4), None)
    g_rb.hide_render = True
    rb(g_rb, active=False, shape="BOX")
    coin_m = pbr("coin", (1.0, 0.75, 0.2), 0.25, metal=1.0)
    src = cyl("coinsrc", (0, 0, -999), 0.22, 0.05, coin_m, verts=20)
    for i in range(36):
        rel = tmn - 0.7 + i * 0.035
        o = instance(src, f"coin{i}", (0.2 + R.uniform(-0.1, 0.1), -tw(89) - 1.6 + R.uniform(-0.1, 0.1), 92.2 + R.uniform(0, 0.4)),
                     rot=(R.uniform(0, 3), R.uniform(0, 3), 0))
        for f, t in frames():
            show(o, f, t >= rel - 0.03)
        rb(o, mass=0.05, bounce=0.3, friction=0.6, shape="CYLINDER", release=rel)
    for f, t in frames():
        pour = t > tmn - 0.8
        G.pose(f, t, arms=(90, 90) if pour else (20, 20), arm_side=(20, 20), elbows=(30, 30), eyes="happy", mouth="grin", look=(0.5, -0.5),
               head=(-10, -10 if pour else 15, 0))
        hp = G.hands[1].matrix_world.translation if False else None
        key(sack, f, loc=(0.2, -tw(89) - 1.6, 92.6 if pour else 91.4), rot=(math.radians(-110 if pour else 0), 0, 0))
    cam, aim = camera(26, 4.0, G.root)

    def cf(t):
        ang = math.radians(-30 + 25 * ease_io(t / DUR[6]))
        r_ = 12
        c = (r_ * math.sin(ang), -tw(89) - r_ * math.cos(ang), 93.5 + 3 * ease_io(t / 1.5))
        a = lerp((0, 0, 100), (0, -tw(89) - 1, 91), ease_io((t - tmn + 1.2) / 0.9))
        return add(c, drift(t, 0.05)), add(a, drift(t, 0.03, 2))
    animate_cam(cam, aim, cf)


def sc7_army():
    """French soldiers in kepis cheer and salute at the base; the camera cranes up as messages (glowing waves) ripple out
    from the antenna across the whole land."""
    world_dusk(top=(0.03, 0.05, 0.18), horizon=(0.9, 0.45, 0.25), strength=1.0)
    paris(night=False)
    light("SUN", (0, 0, 50), 2.6, (1.0, 0.7, 0.45), 3, rot=(math.radians(74), 0, math.radians(-40)))
    E = eiffel(antenna=True)
    tl, tms = cue("loves"), cue("messages")
    sold = []
    for i in range(6):
        s_ = Toon(f"sol{i}", coat=(0.15, 0.22, 0.5), pants=(0.7, 0.08, 0.08), hat="kepi", hat_col=(0.75, 0.08, 0.1),
                  mustache=i % 2 == 0, skin=[(0.96, 0.76, 0.62), (0.88, 0.66, 0.5)][i % 2])
        place(s_, (-8 + i * 3.2, -34 - (i % 2) * 2.2, 0), 180 + (i - 2.5) * 6, 1.6)
        sold.append(s_)
    for f, t in frames():
        for i, s_ in enumerate(sold):
            if t < tl:
                s_.pose(f, t, arms=(0, 0), arm_side=(8, 140), elbows=(10, 130), eyes="open", mouth="smile", look=(0, 0.2), head=(0, 0, 0))
            else:
                s_.pose(f, t, arm_side=(160, 160), arms=(0, 0), eyes="happy", mouth="grin", jump=0.3 * abs(math.sin(t * 6 + i)), head=(0, 12, 0))
    wave_rings("msg", (0, 0, 107), tms - 0.2, n=6, period=0.3, speed=90, life=2.0, col=(0.3, 0.85, 1.0), thick=1.2)
    cam, aim = camera(22, 4.0, sold[2].root)

    def cf(t):
        k = ease_io(t / DUR[7])
        c = lerp((2, -50, 2.5), (18, -150, 60), k)
        a = lerp((0, -34, 3.0), (0, 0, 80), k)
        return add(c, drift(t, 0.07)), add(a, drift(t, 0.05, 2))
    animate_cam(cam, aim, cf)


def searchlight(name, loc, sweep_fn):
    m = pbr(name + "m", (0.85, 0.9, 1.0), 0.5, emit=(0.85, 0.9, 1.0), estr=1.2, alpha=0.08)
    piv = empty(name + "piv", loc)
    beam = prim(bpy.ops.mesh.primitive_cone_add, name, (0, 0, 0), mat=m, vertices=24, radius1=0.2, radius2=6.0, depth=120)
    parent(beam, piv)
    beam.location = (0, 0, 60)
    for f, t in frames():
        key(piv, f, rot=sweep_fn(t))


def sc8_spy():
    """WWI night: searchlights sweep; enemy radio waves converge INTO the antenna ('catches'); the camera swoops down
    to a dark street where a spy in a fedora sneaks... a spotlight SNAPS onto him and soldiers jump out."""
    night_sky()
    paris(night=True)
    E = eiffel(antenna=True)
    gold_spots(40000)
    tc, tsp = cue("catches"), cue("spy")
    for i, (x, ph) in enumerate(((-40, 0), (38, 1.5), (-20, 3.0))):
        searchlight(f"sl{i}", (x, 30, 0.5), lambda t, ph=ph: (math.radians(-20 + 15 * math.sin(t * 0.8 + ph)), math.radians(12 * math.sin(t * 0.6 + ph)), 0))
    wave_rings("enemy", (0, 0, 107), tc - 0.9, n=5, period=0.25, speed=60, life=1.2, col=(1.0, 0.3, 0.25), inward=True, thick=1.0)
    spy = Toon("spy", coat=(0.5, 0.42, 0.28), pants=(0.15, 0.13, 0.12), hat="fedora", hat_col=(0.12, 0.1, 0.1), mustache=True)
    p0, p1 = (-6, -66, 0), (2, -60, 0)
    place(spy, p0, -50, 1.7)
    case = box("case", (0, 0, 0), (0.7, 0.2, 0.5), M["iron_dark"], bevel=0.04)
    sold = []
    for i, (x, y) in enumerate(((7, -57), (-5, -55))):
        s_ = Toon(f"sold{i}", coat=(0.15, 0.22, 0.5), pants=(0.7, 0.08, 0.08), hat="kepi", hat_col=(0.75, 0.08, 0.1), mustache=True)
        place(s_, (x, y, 0), 150 if i == 0 else 210, 1.7)
        sold.append(s_)
    spot = light("SPOT", (0, -70, 14), 0.0, (1.0, 0.95, 0.8), 0.3, spot_deg=18)
    aim_at(spot, spy.root)
    for f, t in frames():
        caught = t > tsp - 0.15
        ph = walk_path(spy, f, t, p0, p1, 2.8, tsp - 0.2, stride=0.3) if t < tsp - 0.2 else None
        spy.pose(f, t, walk=ph, arms=(10, 30), elbows=(20, 60), eyes="wide" if caught else "open", mouth="O" if caught else "flat",
                 brows=1 if caught else -0.8, look=((math.sin(t * 2.5), 0) if not caught else (0, 0.2)), head=(25 * math.sin(t * 2.5) if not caught else 0, 0, 0),
                 arm_side=(150, 150) if caught else None, jump=0.3 * max(0.0, 1 - (t - tsp + 0.15) * 3) if caught else 0)
        if not caught:
            key(case, f, loc=add(spy.root.location, (0.55, 0.1, 0.9)))
        spot.data.energy = 0.0 if not caught else 60000
        spot.data.keyframe_insert("energy", frame=f)
        for i, s_ in enumerate(sold):
            k = t - tsp - 0.05 * i
            if k < 0:
                key(s_.root, f, loc=(s_.root.location.x, s_.root.location.y, -5))
                s_.pose(f, t)
            else:
                key(s_.root, f, loc=(s_.root.location.x, s_.root.location.y, max(0.0, 6 * k - 15 * k * k) if k < 0.4 else 0.0))
                s_.pose(f, t, arms=(90, 90), eyes="open", mouth="grin", brows=-0.5, look=(0, 0), head=(0, 0, 0))
    g = box("ground_rb", (0, 0, -0.5), (400, 400, 1.0), None)
    g.hide_render = True
    rb(g, active=False, shape="BOX")
    rb(case, mass=2, bounce=0.2, release=tsp - 0.1)
    cam, aim = camera(26, 3.0, spy.root)

    def cf(t):
        k = ease_io((t - tc - 0.2) / 2.4)
        c = lerp((24, -60, 70), (4.5, -69, 2.8), k)
        a = lerp((0, 0, 104), (1.5, -61, 2.0), k)
        return add(c, drift(t, 0.06)), add(a, drift(t, 0.04, 2))
    animate_cam(cam, aim, cf, smooth=0.1, shakes=lambda t: shake(t, tsp, 0.25, 0.4))


def balloons(n, area, t_on):
    cols = [(0.95, 0.2, 0.3), (0.2, 0.6, 1.0), (1.0, 0.8, 0.1), (0.3, 0.85, 0.4), (0.8, 0.3, 0.9)]
    rr = random.Random(77)
    for i in range(n):
        m = pbr(f"bal{i}", cols[i % 5], 0.25)
        b = sphere(f"balloon{i}", (0, 0, 0), 0.8, m, scale=(0.8, 0.8, 0.95))
        x, y = rr.uniform(area[0], area[1]), rr.uniform(area[2], area[3])
        ph = rr.uniform(0, 6)
        for f, t in frames():
            k = max(0.0, t - t_on - 0.1 * i)
            key(b, f, loc=(x + 0.8 * math.sin(t * 1.3 + ph), y + 0.5 * math.cos(t * 1.1 + ph), 3.5 + 3.2 * k + 0.2 * math.sin(t * 2 + ph)))


def sc9_today():
    """Nobody dares now: the demolition crane slinks away; sunset crowds cheer, balloons rise, fireworks bloom on
    'monument', and the camera spirals up the golden tower."""
    world_dusk(top=(0.04, 0.05, 0.2), horizon=(1.0, 0.42, 0.18), strength=1.1)
    paris(night=True)
    stars(150)
    E = eiffel(antenna=True)
    gold_spots(45000)
    light("SUN", (0, 0, 50), 2.2, (1.0, 0.6, 0.35), 3, rot=(math.radians(82), 0, math.radians(-120)))
    tn, ttd, tmo = cue("nobody"), cue("today"), cue("monument")
    C = crane_wreck("wc", base=(-46, -16, 0), boom_tip=(-20, -16, 64))
    for f, t in frames():
        dx = -90 * ease_io((t - tn + 0.2) / 1.8)
        for p_ in C["parts"]:
            if f == 1:
                p_["x0"] = p_.location.x
            key(p_, f, loc=(p_["x0"] + dx, p_.location.y, p_.location.z))
        tip = (C["tip"][0] + dx, C["tip"][1], C["tip"][2])
        a = math.radians(8 * math.sin(t * 3))
        p = (tip[0] + 26 * math.sin(a), tip[1], tip[2] - 26 * math.cos(a))
        key(C["ball"], f, loc=p)
        key(C["rope"], f, loc=((tip[0] + p[0]) / 2, tip[1], (tip[2] + p[2]) / 2), rot=(0, a, 0), scale=(0.12, 0.12, 13))
    cr = crowd(14, center=(2, -34), radius=(14, 3), seed=19, face_to=(0, 0))
    for f, t in frames():
        pose_crowd(cr, f, t, "cheer" if t > ttd else "happy")
    balloons(10, (-12, 14, -38, -30), ttd)
    for j, (c_, col) in enumerate((((-35, 20, 80), (1.0, 0.6, 0.15)), ((32, 15, 88), (0.35, 0.6, 1.0)), ((0, 40, 115), (1.0, 0.3, 0.45)),
                                   ((-20, 30, 100), (0.4, 1.0, 0.5)))):
        firework(f"fw9{j}", c_, tmo - 0.2 + 0.3 * j, col, r=11)
    cam, aim = camera(22, 4.0, E["root"])

    def cf(t):
        k = ease_io(t / DUR[9])
        ang = math.radians(-25 + 60 * k)
        r_ = 70 - 10 * k
        return add((r_ * math.sin(ang), -r_ * math.cos(ang), 4 + 60 * k), drift(t, 0.1)), add((0, 0, 30 + 50 * k), drift(t, 0.06, 2))
    animate_cam(cam, aim, cf)


def sc11_top():
    """At the very top at night: two friends at the rail, Paris glittering far below; one waves, one clings on."""
    night_sky()
    paris(night=True)
    E = eiffel(antenna=True)
    gold_spots(40000)
    pz = 89.0 + 0.7 + 0.25
    pa = Toon("pa", coat=(0.95, 0.4, 0.15), hat="beret", hat_col=(0.15, 0.4, 0.8))
    pb = Toon("pb", skin=(0.78, 0.55, 0.38), coat=(0.2, 0.75, 0.6), hairstyle="long", hair=(0.08, 0.05, 0.03))
    place(pa, (-1.0, -tw(89) - 1.4, pz), 0, 1.25)
    place(pb, (1.0, -tw(89) - 1.5, pz), 8, 1.25)
    rail = box("rail", (0, -tw(89) - 2.4, pz + 1.15), (8, 0.08, 0.08), M["iron"])
    for i in range(7):
        box(f"rp{i}", (-3.6 + i * 1.2, -tw(89) - 2.4, pz + 0.6), (0.08, 0.08, 1.1), M["iron"])
    light("AREA", (0, -tw(89) - 8, pz + 4), 500, (1.0, 0.85, 0.7), 4, rot=(math.radians(60), 0, 0))
    tcm = cue("comments")
    for f, t in frames():
        pa.pose(f, t, arm_side=(30, 150 + 20 * math.sin(t * 10)), arms=(20, 0), elbows=(20, 40), eyes="happy", mouth="grin", look=(0.4, 0),
                head=(-10, 0, 8), jump=0.08 * abs(math.sin(t * 5)))
        pb.pose(f, t, arms=(80, 80), arm_side=(-5, -5), elbows=(40, 40), eyes="wide", mouth="O" if t < tcm else "smile", brows=1, look=(0, -1),
                head=(10, -25, 0), bounce=0.015 * math.sin(t * 30))
    cam, aim = camera(24, 3.0, pa.root)
    c0 = (0, -tw(89) - 1.4, pz + 1.6)

    def cf(t):
        ang = math.radians(-30 + 40 * ease_io(t / DUR[11]))
        r_ = 7.0
        return add((c0[0] + r_ * math.sin(ang), c0[1] - r_ * math.cos(ang), c0[2] + 2.2), drift(t, 0.04)), add((c0[0], c0[1] + 0.3, c0[2] - 0.4), drift(t, 0.02, 2))
    animate_cam(cam, aim, cf)


SCENES = {0: sc0_hook, 1: sc1_build, 2: sc2_hate, 3: sc3_permit, 4: sc4_clever, 5: sc5_science, 6: sc6_antenna, 7: sc7_army,
          8: sc8_spy, 9: sc9_today, 11: sc11_top}


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


EXPOSURE = {1: -0.5, 2: -0.5, 5: -0.5, 7: -0.4, 9: -0.2}

if __name__ == "__main__":
    mats()
    SCENES[SCENE]()
    bake_all()
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
