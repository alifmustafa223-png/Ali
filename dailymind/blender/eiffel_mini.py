"""THE DAILYMIND — the Eiffel Tower Short in the Miniature Cinematic Universe (giant everyday object: the radio that saved it).

(Engine below is shared with mini3d.py; per-scene builders m0..m11 at the end.)
Run: python eiffel_mini.py -- SCENE OUTDIR [RES] [SAMPLES]   (PC: blender -b -P eiffel_mini.py -- SCENE ..\\eiffel_mini\\plates 100 64)

Original sample notes:

  S1  A miniature historical world      : 1889 Paris building site on a diorama board (tower rising, workers, crane)
  S2  A surreal giant everyday object   : a real pocket watch standing in a 1:100 town square, ruling day and night
  S3  A cinematic miniature industrial world : a tiny factory — conveyor, press, gears, pistons, steam, workers

Everything is built at true miniature scale (figures are 1.75 cm tall), so the depth of field is real macro optics.
Assets: Poly Haven CC0 models / PBR textures / HDRIs (dm_assets.py), painted figurines (figurine.py).
Run:  python mini3d.py -- S1 OUTDIR [RES_PCT=100] [SAMPLES=64] [F0] [F1]     (PC: blender -b -P mini3d.py -- S1 ...)
      STILL_FRAMES=1,180,359 python mini3d.py -- S2 /tmp/out 25 16           (preview stills)
"""
import math
import os
import random
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAMPLE = argv[0] if argv else "0"
IDX = int(SAMPLE)
OUTDIR = argv[1] if len(argv) > 1 else "/tmp/mini"
RES = int(argv[2]) if len(argv) > 2 else 100
SAMPLES = int(argv[3]) if len(argv) > 3 else 64
F0 = int(argv[4]) if len(argv) > 4 else 1
OUTFMT = os.environ.get("PLATE_FMT", "PNG")
STILLS = [int(x) for x in os.environ.get("STILL_FRAMES", "").split(",") if x.strip()]
FPS = 30
import json as _j0
DUR = _j0.load(open(os.path.join(os.path.dirname(HERE), "eiffel", "plan.json")))["durs"][IDX]
NF = int(math.ceil(DUR * FPS)) + 1
F1 = int(argv[5]) if len(argv) > 5 else NF

bpy.ops.wm.read_factory_settings(use_empty=True)
import dm_assets as AS  # noqa: E402
from figurine import Figure, bake_all  # noqa: E402

SC = bpy.context.scene
SC.render.fps = FPS
SC.frame_start, SC.frame_end = 1, NF
SC.render.resolution_x, SC.render.resolution_y = 1080, 1920
SC.render.resolution_percentage = RES
R = random.Random(7)
FIG_H = 0.0175  # 1:100 scale figures


# ---------------------------------------------------------------- basics
def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ease_io(x):
    x = max(0.0, min(1.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)


def lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b)) if isinstance(a, tuple) else a + (b - a) * k


def frames():
    for f in range(1, NF + 1):
        yield f, (f - 1) / FPS


def link(o):
    if o.name not in SC.collection.objects:
        SC.collection.objects.link(o)
    return o


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


def show(o, f, vis):
    o.hide_render = not vis
    o.keyframe_insert("hide_render", frame=f)


def empty(name, loc=(0, 0, 0), par=None):
    o = bpy.data.objects.new(name, None)
    link(o)
    if par:
        o.parent = par
        o.matrix_parent_inverse.identity()
    o.location = loc
    return o


def parent(c, p):
    c.parent = p
    c.matrix_parent_inverse.identity()


def prim(op, name, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), mat=None, bevel=0.0, smooth=False, **kw):
    op(location=loc, rotation=rot, **kw)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    if mat:
        o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new("bevel", "BEVEL")
        b.width = bevel
        b.segments = 3
        b.limit_method = "NONE"
    if smooth:
        bpy.ops.object.shade_smooth()
    return o


def box(name, c, size, mat, bevel=0.0, rot=(0, 0, 0)):
    return prim(bpy.ops.mesh.primitive_cube_add, name, c, (size[0] / 2, size[1] / 2, size[2] / 2), rot, mat, bevel)


def cyl(name, c, r, h, mat, verts=32, rot=(0, 0, 0), smooth=True):
    return prim(bpy.ops.mesh.primitive_cylinder_add, name, c, (r, r, h / 2), rot, mat, smooth=smooth, vertices=verts)


def sphere(name, c, r, mat, segs=16, scale=None):
    return prim(bpy.ops.mesh.primitive_uv_sphere_add, name, c, scale or (r, r, r), (0, 0, 0), mat, smooth=True, segments=segs,
                ring_count=max(6, segs // 2))


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree, m.node_tree.nodes.get("Principled BSDF")


def paint(name, col, rough=0.5, metal=0.0, emit=None, estr=0.0):
    m, nt, p = new_mat(name)
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = estr
    return m


def glow(name, col, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


def light(kind, loc, energy, col=(1, 1, 1), size=0.01, rot=(0, 0, 0), spot_deg=None):
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
            o.data.spot_blend = 0.7
    elif kind == "SUN":
        o.data.angle = math.radians(size)
    return o


def aim_at(o, tgt):
    c = o.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"


def smooth_seq(vals, alpha):
    fw = [vals[0]]
    for v in vals[1:]:
        fw.append(tuple(p + alpha * (x - p) for p, x in zip(fw[-1], v)))
    bw = [fw[-1]]
    for v in reversed(fw[:-1]):
        bw.append(tuple(p + alpha * (x - p) for p, x in zip(bw[-1], v)))
    return list(reversed(bw))


def macro_camera(path_fn, focus_fn, lens=50, fstop=4.0, smooth=0.08):
    """Macro rig: smoothed camera + aim path and a smoothed focus point (rack focus). path_fn(t) -> (cam, aim)."""
    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    SC.camera = cam
    cam.data.lens = lens
    cam.data.sensor_width = 36
    cam.data.clip_start = 0.0005
    cam.data.clip_end = 50
    aim = empty("aim")
    aim_at(cam, aim)
    foc = empty("focus")
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = foc
    cam.data.dof.aperture_fstop = fstop
    ts = [t for _, t in frames()]
    cs = smooth_seq([tuple(path_fn(t)[0]) for t in ts], smooth)
    as_ = smooth_seq([tuple(path_fn(t)[1]) for t in ts], smooth)
    fs = smooth_seq([tuple(focus_fn(t)) for t in ts], smooth)
    for (f, t), c, a, fo in zip(frames(), cs, as_, fs):
        key(cam, f, loc=c)
        key(aim, f, loc=a)
        key(foc, f, loc=fo)
    return cam


def drift(t, amp, seed=0):
    s = seed * 1.7
    return (amp * (math.sin(t * 0.9 + s) + 0.5 * math.sin(t * 2.3 + 2 * s)), amp * 0.6 * math.sin(t * 1.3 + 3 * s),
            amp * (math.sin(t * 1.1 + 4 * s) + 0.4 * math.sin(t * 2.9 + s)))


def add(*vs):
    return tuple(sum(c) for c in zip(*vs))


def smoke(name, loc, t_on, n=6, size=0.004, rise=0.02, col=(0.85, 0.82, 0.78), period=None, life=2.2):
    """Volumetric steam / dust puffs (Principled Volume with a soft noisy falloff)."""
    m = bpy.data.materials.new(name + "_m")
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Color"].default_value = (*col, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    nt.links.new(tc.outputs["Object"], ln.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    sub = nt.nodes.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    nt.links.new(nz.outputs["Fac"], sub.inputs[0])
    nt.links.new(ln.outputs["Value"], sub.inputs[1])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 60.0 / max(size, 1e-4) * 0.004
    nt.links.new(sub.outputs[0], mul.inputs[0])
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "MAXIMUM"
    mx.inputs[1].default_value = 0.0
    nt.links.new(mul.outputs[0], mx.inputs[0])
    nt.links.new(mx.outputs[0], v.inputs["Density"])
    nt.links.new(v.outputs[0], out.inputs["Volume"])
    rr = random.Random(hash(name) % 997)
    for i in range(n):
        o = sphere(f"{name}{i}", loc, 1.0, m, segs=10)
        t0 = t_on + (i * period if period else rr.uniform(0, 0.4))
        dx, dy = rr.uniform(-1, 1) * size, rr.uniform(-1, 1) * size
        for f, t in frames():
            k = (t - t0) / life
            if period:
                k = ((t - t_on) % (period * n)) / life - i * period / life
            if k < 0 or k > 1:
                key(o, f, loc=loc, scale=(1e-6,) * 3)
                continue
            s_ = size * (0.4 + 1.6 * k) * (1 - k) ** 0.5
            key(o, f, loc=(loc[0] + dx * k * 2, loc[1] + dy * k * 2, loc[2] + rise * k), scale=(max(1e-6, s_),) * 3)


def sparks(name, loc, times, n=10, speed=0.06, col=(1.0, 0.65, 0.2)):
    """Bursts of glowing sparks with gravity (rivets, welding, stamping)."""
    m = glow(name + "m", col, 40.0)
    rr = random.Random(hash(name) % 991)
    parts = []
    for i in range(n):
        o = sphere(f"{name}{i}", (0, 0, -1), 0.00025, m, segs=6)
        parts.append((o, rr.uniform(0, 2 * math.pi), rr.uniform(0.3, 1.0), rr.uniform(0.4, 1.0)))
    for f, t in frames():
        burst = None
        for tb in times:
            if 0 <= t - tb < 0.5:
                burst = tb
        for o, a, up, v in parts:
            if burst is None:
                key(o, f, loc=(0, 0, -1))
                continue
            k = t - burst
            p = (loc[0] + math.cos(a) * speed * v * k, loc[1] + math.sin(a) * speed * v * k,
                 loc[2] + speed * up * k - 0.5 * 9.81 * 0.02 * k * k * 10)
            key(o, f, loc=p, scale=(max(1e-6, 0.00025 * (1 - k / 0.5)),) * 3)


# ---------------------------------------------------------------- Eiffel-style lattice (re-used from eiffel3d, at any scale)
def beams_mesh(name, beams, mat):
    from mathutils import Vector
    verts, faces = [], []
    for p0, p1, th in beams:
        a, b = Vector(p0), Vector(p1)
        d = b - a
        if d.length < 1e-9:
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
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    link(o)
    o.data.materials.append(mat)
    return o


def tw(z):
    return 23.0 * math.exp(-z / 32.0) + 1.0


def lattice_tower(name, mat, top_z=96.0, bands=10):
    """Wrought-iron lattice tower in model units (100 tall); returns band objects for build-up animation."""
    zs = [0.0]
    while zs[-1] < top_z - 0.1:
        zs.append(min(top_z, zs[-1] + (1.8 if zs[-1] < 18 else 2.6)))
    bb = [[] for _ in range(bands)]
    bh = top_z / bands

    def addb(p0, p1, th):
        bb[min(bands - 1, int(min(p0[2], p1[2]) / bh))].append((p0, p1, th))
    for i in range(len(zs) - 1):
        z0, z1 = zs[i], zs[i + 1]
        w0, w1 = tw(z0), tw(z1)
        th = 0.7 - 0.45 * z0 / 96
        for sx in (-1, 1):
            for sy in (-1, 1):
                addb((sx * w0, sy * w0, z0), (sx * w1, sy * w1, z1), th)
        if z1 <= 18.5:
            lw0, lw1 = 7.5 - 0.22 * z0, 7.5 - 0.22 * z1
            for sx in (-1, 1):
                for sy in (-1, 1):
                    c0 = [(sx * w0, sy * w0), (sx * (w0 - lw0), sy * w0), (sx * (w0 - lw0), sy * (w0 - lw0)), (sx * w0, sy * (w0 - lw0))]
                    c1 = [(sx * w1, sy * w1), (sx * (w1 - lw1), sy * w1), (sx * (w1 - lw1), sy * (w1 - lw1)), (sx * w1, sy * (w1 - lw1))]
                    for k in range(1, 4):
                        addb((*c0[k], z0), (*c1[k], z1), th * 0.8)
                    for k in range(4):
                        k2 = (k + 1) % 4
                        addb((*c0[k], z0), (*c1[k2], z1), th * 0.35)
                        addb((*c0[k2], z0), (*c1[k], z1), th * 0.35)
        else:
            a0 = [(-w0, -w0), (w0, -w0), (w0, w0), (-w0, w0)]
            a1 = [(-w1, -w1), (w1, -w1), (w1, w1), (-w1, w1)]
            for f_ in range(4):
                k2 = (f_ + 1) % 4
                addb((*a0[f_], z0), (*a1[k2], z1), th * 0.4)
                addb((*a0[k2], z0), (*a1[f_], z1), th * 0.4)
                if i % 2 == 0:
                    addb((*a0[f_], z0), (*a0[k2], z0), th * 0.45)
    for side in range(4):
        pts = []
        for k in range(17):
            u = -1 + 2 * k / 16
            pts.append((u * (tw(0) - 7.5) * 0.98, 14.5 * math.sqrt(max(0.0, 1 - u * u))))
        for k in range(16):
            (x0, z0), (x1, z1) = pts[k], pts[k + 1]
            y0, y1 = tw(z0) * 0.98, tw(z1) * 0.98
            seg = {0: ((x0, -y0, z0), (x1, -y1, z1)), 1: ((x0, y0, z0), (x1, y1, z1)), 2: ((-y0, x0, z0), (-y1, x1, z1)),
                   3: ((y0, x0, z0), (y1, x1, z1))}[side]
            addb(seg[0], seg[1], 0.55)
    root = empty(name + "_root")
    out = []
    for b in range(bands):
        if bb[b]:
            o = beams_mesh(f"{name}_b{b}", bb[b], mat)
            parent(o, root)
            out.append((o, b * bh))
    return root, out


# ---------------------------------------------------------------- render setup
def setup_render(exposure=0.0, vol=True):
    SC.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE_NEXT"
    SC.eevee.taa_render_samples = SAMPLES
    for attr, val in (("use_raytracing", True), ("use_fast_gi", True), ("use_shadows", True), ("clamp_surface_indirect", 6.0),
                      ("use_volumetric_shadows", vol), ("volumetric_tile_size", "4")):
        try:
            setattr(SC.eevee, attr, val)
        except Exception:
            pass
    try:
        SC.eevee.ray_tracing_options.use_denoise = True
    except Exception:
        pass
    SC.render.use_motion_blur = True
    SC.view_settings.view_transform = "AgX"
    try:
        SC.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    SC.view_settings.exposure = exposure
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
        SC.render.filepath = os.path.join(OUTDIR, f"s{IDX}.mp4")
        SC.render.use_file_extension = False
    else:
        SC.render.image_settings.file_format = "PNG"
        SC.render.image_settings.color_mode = "RGB"
        out = os.path.join(OUTDIR, f"s{IDX}")
        os.makedirs(out, exist_ok=True)
        SC.render.filepath = os.path.join(out, "")
    SC.frame_start, SC.frame_end = F0, min(F1, NF)


# ================================================================= EIFFEL — MINIATURE CINEMATIC UNIVERSE (full Short)
import json as _json
import town_kit as TK
from mathutils import Vector

PLAN = _json.load(open(os.path.join(os.path.dirname(HERE), "eiffel", "plan.json")))
DURS, STARTS, ABS = PLAN["durs"], PLAN["starts"], PLAN["abs"]
TS = 0.0045                 # town scale 1:220 (figures ~8 mm)
FH = 1.75 * TS
ST = 0.006                  # tower lattice units -> metres (the tower stands 0.6 m: a 'giant' landmark among 9 cm houses)
RADIO_AT = (0.33, -0.06, 0.0)
RADIO_YAW = math.radians(-28)


def cue(name):
    return ABS[name] - STARTS[IDX]


def catmull(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    for i in range(len(keys) - 1):
        t0, p1 = keys[i]
        t1, p2 = keys[i + 1]
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0)
            p0 = keys[i - 1][1] if i > 0 else p1
            p3 = keys[i + 2][1] if i + 2 < len(keys) else p2
            return tuple(0.5 * ((2 * b) + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (-a + 3 * b - 3 * c + d) * u ** 3)
                         for a, b, c, d in zip(p0, p1, p2, p3))


def cam_rig(cam_k, aim_k, foc_k, lens=35, fstop=11.0, smooth=0.06):
    """ONE continuous Catmull-Rom move per scene (never stops), zero-lag smoothed; focus bound to story keys."""
    return macro_camera(lambda t: (add(catmull(cam_k, t), drift(t, 0.0004)), catmull(aim_k, t)), lambda t: catmull(foc_k, t),
                        lens=lens, fstop=fstop, smooth=smooth)


def lens_check(cam, min_mm=18.0):
    """QC: no object may pass within min_mm of the lens while in view (blurry blobs). Prints the closest offenders."""
    objs = [o for o in SC.objects if o.type in ("MESH", "CURVE", "FONT") and not o.hide_render and max(o.dimensions) < 0.25]
    worst = []
    for f in range(1, NF + 1, 3):
        SC.frame_set(f)
        cp = cam.matrix_world.translation
        fwd = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
        for o in objs:
            if o.hide_render:
                continue
            bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
            mn = Vector([min(v[i] for v in bb) for i in range(3)])
            mx = Vector([max(v[i] for v in bb) for i in range(3)])
            q = Vector([min(max(cp[i], mn[i]), mx[i]) for i in range(3)])
            d = (q - cp).length
            if d * 1000 < min_mm and (q - cp).dot(fwd) > 0:
                worst.append((round(d * 1000, 1), round((f - 1) / FPS, 2), o.name))
    worst.sort()
    seen, rep = set(), []
    for w in worst:
        if w[2] not in seen:
            seen.add(w[2])
            rep.append(w)
    print("[lens-check] " + ("OK" if not rep else "TOO CLOSE: " + str(rep[:8])))
    SC.frame_set(1)
    return rep


# ---------------------------------------------------------------- shared world
def world(night=True, golden=False, era="1909", antenna=False, tower_lights=None, crowd_now=False, town=True):
    if night:
        AS.hdri("belfast_sunset_puresky", "2k", 0.05, 200)
        wnt = SC.world.node_tree
        bg = wnt.nodes["Background"]
        mix = wnt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["Factor"].default_value = 0.92
        mix.inputs[7].default_value = (0.008, 0.012, 0.04, 1)
        wnt.links.new(bg.inputs["Color"].links[0].from_socket, mix.inputs[6])
        wnt.links.new(mix.outputs[2], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = 0.6
        light("SUN", (0, 0, 1), 0.25, (0.5, 0.62, 1.0), 1.0, rot=(math.radians(50), 0, math.radians(150)))
    else:
        AS.hdri("belfast_sunset_puresky", "2k", 1.0, 200)
        light("SUN", (0, 0, 1), 3.5 if golden else 4.0, (1.0, 0.68, 0.42), 1.5, rot=(math.radians(74), 0, math.radians(-35)))
    cob = AS.texture("cobblestone_floor_08", "2k", scale=1.0 / (2.0 * TS) * 0.9, tint=(0.6, 0.55, 0.5))
    box("ground", (0, 0, -0.002), (2.4, 2.4, 0.004), cob)
    gravel = AS.texture("bicolour_gravel", "1k", scale=1.0 / (2.0 * TS), tint=(0.8, 0.75, 0.68))
    box("champ", (0, -0.35, 0.0002), (0.36, 0.5, 0.0004), gravel)
    lawn = AS.texture("aerial_grass_rock", "1k", scale=1.0 / (6.0 * TS), tint=(0.55, 0.75, 0.45))
    for s_ in (-1, 1):
        box(f"lawn{s_}", (s_ * 0.13, -0.35, 0.0004), (0.08, 0.46, 0.0008), lawn)
    if town:
        TK.init(None, AS.texture("painted_plaster_wall", "1k", scale=1.0 / (4.0 * TS)), AS.texture("grey_roof_tiles", "1k", scale=1.0 / (2.0 * TS)), scale=TS)
        rr = random.Random(5)
        glass = paint("eglass", (0.06, 0.07, 0.09), 0.08, emit=(1.0, 0.72, 0.38), estr=6.0 if night else 0.0)
        TK.TEX["glass"] = glass
        TK.TEX["shop_glass"] = glass
        n_b = 15
        for i in range(n_b):
            a = math.pi * (0.0 + 1.0 * i / (n_b - 1))
            r_ = 0.5 + rr.uniform(0, 0.03)
            TK.building(f"tb{i}", (r_ * math.cos(a), r_ * math.sin(a) + 0.1), a - math.pi / 2, floors=rr.choice([5, 6, 6, 7]), bays=rr.choice([3, 3, 4]),
                        wall=TK.WALLS[i % len(TK.WALLS)], shutters=TK.SHUTTERS[rr.randrange(len(TK.SHUTTERS))], shop=rr.random() < 0.7, seed=60 + i)
    iron = AS.texture("rusty_metal_02", "1k", scale=4.0, tint=(0.36, 0.25, 0.18))
    troot, bands = lattice_tower("T", iron, top_z=96, bands=12)
    troot.scale = (ST, ST, ST)
    deck = paint("deck", (0.22, 0.16, 0.12), 0.6, 0.3)
    plats = []
    for z, extra, th in ((18.0, 2.5, 2.0), (39.0, 1.6, 1.6), (89.0, 0.9, 1.4)):
        w_ = tw(z) + extra
        p_ = box(f"plat{z}", (0, 0, z * ST), (2 * w_ * ST, 2 * w_ * ST, th * ST), deck, bevel=0.0008)
        plats.append(p_)
    cap = box("tcap", (0, 0, 92.5 * ST), (3.6 * ST, 3.6 * ST, 5 * ST), deck, bevel=0.001)
    ant = cyl("antenna", (0, 0, (95 + 6) * ST), 0.35 * ST, 12 * ST, paint("antm", (0.3, 0.3, 0.32), 0.4, 0.8), verts=12)
    if not antenna:
        ant.scale = (0.35 * ST, 0.35 * ST, 1e-4)
    if tower_lights is not None:  # golden illumination: tiny bulbs up the four corner members
        src = sphere("bulbsrc", (0, 0, -9), 0.0011, glow("bulbm", (1.0, 0.72, 0.32), tower_lights), segs=8)
        for k in range(36):
            z = 1.5 + 2.5 * k
            w_ = tw(z) + 0.4
            for sx in (-1, 1):
                for sy in (-1, 1):
                    b_ = bpy.data.objects.new("bulb", src.data)
                    link(b_)
                    b_.location = (sx * w_ * ST, sy * w_ * ST, z * ST)
        sp = light("SPOT", (0.0, -0.45, 0.01), 18.0, (1.0, 0.72, 0.4), 0.02, spot_deg=40)
        aim_at(sp, empty("tspot_tgt", (0, 0, 0.3)))
    radio_root, robj = AS.model("vintage_radio_transceiver", "1k", loc=RADIO_AT, rot=(0, 0, RADIO_YAW), scale=1.0, name="radio")
    parts = {o.name.replace("vintage_radio_transceiver", "").strip("_") or "body": o for o in robj}
    dial_glow = light("POINT", (RADIO_AT[0] - 0.02, RADIO_AT[1] - 0.14, 0.05), 0.0, (1.0, 0.65, 0.3), 0.02)
    # street lamps (1:220)
    lamps = []
    for i, (x, y) in enumerate(((-0.2, -0.2), (0.2, -0.22), (-0.24, 0.05), (0.06, -0.58))):
        AS.model("street_lamp_02", "1k", loc=(x, y, 0.0), scale=TS, name=f"slamp{i}")
        L = light("POINT", (x, y, 4.0 * TS), 0.06 if night else 0.0, (1.0, 0.68, 0.38), 0.0008)
        lamps.append(L)
    return dict(tower=troot, bands=bands, plats=plats, antenna=ant, radio=radio_root, parts=parts, dial_glow=dial_glow, lamps=lamps)


def radio_wake(W, t_on, strength=1.0):
    """The giant radio comes alive: dial glow ramps, needle (dial) swings, warm light spills."""
    dial = W["parts"].get("dial")
    for f, t in frames():
        k = ease((t - t_on) / 0.35)
        W["dial_glow"].data.energy = 3.0 * k * strength * (1 + 0.15 * math.sin(t * 23))
        W["dial_glow"].data.keyframe_insert("energy", frame=f)
        if dial is not None:
            key(dial, f, rot=(0, math.radians(-110 * k + 8 * math.sin(t * 3) * k), 0))


def rings(name, center, t_on, n=4, period=0.25, speed=0.6, life=1.1, col=(1.0, 0.75, 0.3), inward=False, axis="Z"):
    """Glowing radio waves (thin tori) expanding from (or into) a point."""
    m = glow(name + "m", col, 6.0)
    for i in range(n):
        o = prim(bpy.ops.mesh.primitive_torus_add, f"{name}{i}", center, mat=m, major_radius=1.0, minor_radius=0.012, major_segments=64,
                 minor_segments=6)
        if axis == "Y":
            o.rotation_euler = (math.pi / 2, 0, 0)
        t0 = t_on + i * period
        for f, t in frames():
            k = t - t0
            if k < 0 or k > life:
                key(o, f, scale=(1e-5,) * 3)
                continue
            r = max(0.002, speed * (life - k) if inward else 0.004 + speed * k)
            fade = (1 - k / life) if not inward else min(1.0, k * 3)
            key(o, f, scale=(r, r, max(1e-5, r * fade)))


def toy_crane(name, base, tip):
    yel = paint("craneyel", (0.92, 0.62, 0.08), 0.35, 0.2)
    dark = paint("cranedark", (0.12, 0.12, 0.13), 0.5, 0.6)
    root = empty(name + "_root", base)
    parts = [box(name + "_body", (0, 0, 0.012), (0.05, 0.03, 0.018), yel, bevel=0.002)]
    for s_ in (-1, 1):
        for xw in (-0.017, 0.017):
            w = cyl(f"{name}_wheel{s_}{xw}", (xw, s_ * 0.017, 0.006), 0.006, 0.006, dark, verts=20, rot=(math.pi / 2, 0, 0))
            parts.append(w)
    mast = beams_mesh(name + "_mast", [((0, 0, 0.02), (0, 0, tip[2] - base[2]), 0.004)], yel)
    boom = beams_mesh(name + "_boom", [((0, 0, tip[2] - base[2]), (tip[0] - base[0], 0, tip[2] - base[2]), 0.003)], yel)
    parts += [mast, boom]
    for p_ in parts:
        parent(p_, root)
    wheels = [p_ for p_ in parts if "wheel" in p_.name]
    return root, wheels


def pendulum_sim(t_rel, ta, push_t, L, theta0=-0.8, kick=-26.0):
    """Integrate a real pendulum: released at t_rel, an impulse-like push (the radio wave) at push_t. Returns theta(t)."""
    g = 9.81
    dt = 1 / 600
    th, om = theta0, 0.0
    out = {}
    t = 0.0
    while t <= DURS[IDX] + 0.1:
        if t >= t_rel:
            F = kick * math.exp(-((t - push_t) / 0.06) ** 2) if push_t else 0.0
            al = -(g / L) * math.sin(th) - 0.15 * om + F
            om += al * dt
            th += om * dt
        out[round(t, 4)] = th
        t += dt
    keys = sorted(out)
    return lambda tt: out[min(keys, key=lambda k: abs(k - tt))] if tt <= keys[-1] else out[keys[-1]]


# ---------------------------------------------------------------- scenes
def m0_hook():
    W = world(night=True, tower_lights=None)
    tt, tr = cue("torn"), cue("radio0")
    base, tip = (-0.36, -0.1, 0.0), (-0.21, -0.1, 0.42)
    croot, wheels = toy_crane("crane", base, tip)
    L = 0.26
    push = tr + 0.12                      # the radio wave reaches the ball
    th = pendulum_sim(push - 0.32, None, push, L, theta0=-0.9, kick=-70.0)   # held back (creaking) until released into the swing
    ball = sphere("wball", (0, 0, 0), 0.016, paint("ballm", (0.08, 0.08, 0.09), 0.25, 0.9))
    rope = cyl("wrope", (0, 0, 0), 0.0006, 1.0, paint("ropem", (0.1, 0.1, 0.1), 0.6))
    mind = 9.0
    for f, t in frames():
        a = th(t)
        p = (tip[0] + L * math.sin(a), tip[1], tip[2] - L * math.cos(a))
        key(ball, f, loc=p)
        key(rope, f, loc=((tip[0] + p[0]) / 2, tip[1], (tip[2] + p[2]) / 2), rot=(0, a, 0), scale=(0.0006, 0.0006, L / 2))
        zt = max(0.0, p[2] / ST)
        mind = min(mind, abs(p[0]) - tw(zt) * ST - 0.016)
    print(f"[physics] wrecking ball closest approach to the tower: {mind * 1000:.1f} mm (must stay > 0)")
    radio_wake(W, tr - 0.05)
    spk = W["radio"].matrix_world @ Vector((-0.044, -0.071, 0.166))
    rings("wave0", tuple(spk), tr - 0.02, n=5, period=0.14, speed=0.55, life=1.0)
    for f, t in frames():
        k = ease((t - tr + 0.1) / 0.3)
        for L_ in W["lamps"]:
            L_.data.energy = 0.06 + 0.1 * k
            L_.data.keyframe_insert("energy", frame=f)
    wk = [Figure("w1", FH, coat=(0.3, 0.32, 0.4), hat="cap", mustache=True), Figure("w2", FH, coat=(0.45, 0.28, 0.18), hat="cap")]
    wk[0].place((-0.07, -0.2, 0.0), 160)
    wk[1].place((-0.055, -0.212, 0.0), 200)
    for f, t in frames():
        wow = t > tr + 0.2
        wk[0].pose(f, t, point=not wow, look=(0, 30), wave=wow)
        wk[1].pose(f, t, look=(-20, 35), carry=wow)
    cam_k = [(0.0, (0.02, -0.52, 0.03)), (1.6, (-0.04, -0.47, 0.06)), (3.0, (0.06, -0.5, 0.1)), (4.43, (0.12, -0.56, 0.14))]
    aim_k = [(0.0, (-0.1, -0.12, 0.2)), (1.6, (-0.06, -0.1, 0.26)), (3.0, (0.12, -0.1, 0.12)), (4.43, (0.2, -0.08, 0.12))]
    foc_k = [(0.0, (-0.12, -0.1, 0.2)), (2.6, (-0.05, -0.1, 0.25)), (3.2, (0.25, -0.1, 0.1)), (4.43, (0.28, -0.1, 0.1))]
    return cam_rig(cam_k, aim_k, foc_k, lens=30, fstop=14)


def m1_build():
    W = world(night=False, golden=True)
    tg, ttl, tf = cue("gustave"), cue("tallest"), cue("fair")
    for j, (o, z0) in enumerate(W["bands"]):
        t_on = 0.2 + j * 0.32
        for f, t in frames():
            k = (t - t_on) / 0.45
            if k <= 0:
                key(o, f, loc=(0, 0, 0), scale=(1, 1, 1e-4))
                continue
            drop = 6.0 * (1 - min(1.0, k)) ** 2                         # lowered into place, then a damped settle
            settle = 0.25 * math.exp(-8 * max(0.0, t - t_on - 0.45)) * math.sin(22 * max(0.0, t - t_on - 0.45))
            key(o, f, loc=(0, 0, drop + settle), scale=(1, 1, 1))
    for p_ in W["plats"]:
        zp = p_.location.z / ST
        t_on = 0.2 + (zp / 96 * 12) * 0.32 + 0.4
        s0 = tuple(p_.scale)
        for f, t in frames():
            s_ = ease((t - t_on) / 0.3)
            key(p_, f, scale=(s0[0] * max(1e-3, s_), s0[1] * max(1e-3, s_), s0[2] * max(1e-3, s_)))
    G = Figure("gustave", FH * 1.02, coat=(0.1, 0.1, 0.16), hat="tophat", long_coat=True, mustache=True, hair=(0.5, 0.48, 0.45), seed=3)
    G.place((0.03, -0.27, 0.0), 190)
    rr = random.Random(31)
    crowd = []
    for i in range(12):
        fg = Figure(f"c{i}", FH * rr.uniform(0.93, 1.05), coat=[(0.35, 0.15, 0.2), (0.15, 0.25, 0.4), (0.4, 0.3, 0.15), (0.2, 0.35, 0.25)][i % 4],
                    hat=rr.choice(["tophat", "bowler", "bowler", None]), long_coat=i % 2 == 0, mustache=i % 3 == 0, seed=200 + i)
        fg.place((rr.uniform(-0.08, 0.09), rr.uniform(-0.33, -0.29), 0.0), rr.uniform(170, 190))
        crowd.append(fg)
    for f, t in frames():
        G.pose(f, t, wave=t > tg - 0.2, look=(0, 25))
        for i, fg in enumerate(crowd):
            fg.pose(f, t, wave=t > tf - 0.3 and i % 2 == 0, look=(0, 30))
    flags = [paint(f"flag{i}", c, 0.6) for i, c in enumerate(((0.1, 0.2, 0.6), (0.92, 0.92, 0.9), (0.75, 0.08, 0.08)))]
    for k in range(18):
        x = -0.16 + k * 0.019
        fl = box(f"pennant{k}", (x, -0.2, 0.05 - 0.004 * math.sin(math.pi * k / 17)), (0.008, 0.0004, 0.01), flags[k % 3])
        for f, t in frames():
            key(fl, f, rot=(math.radians(8 * math.sin(t * 4 + k)), 0, 0))
    for j, (c_, col) in enumerate((((-0.2, 0.2, 0.75), (1.0, 0.6, 0.15)), ((0.2, 0.15, 0.82), (0.35, 0.6, 1.0)), ((0.0, 0.3, 0.9), (1.0, 0.3, 0.45)))):
        fw_burst(f"fw1{j}", c_, tf - 0.15 + 0.25 * j, col)
    cam_k = [(0.0, (0.06, -0.33, 0.012)), (2.2, (0.09, -0.48, 0.05)), (4.6, (0.14, -0.78, 0.26)), (6.75, (0.16, -0.95, 0.42))]
    aim_k = [(0.0, (0.03, -0.27, 0.01)), (2.2, (0.0, -0.1, 0.12)), (4.6, (0.0, 0.0, 0.35)), (6.75, (0.0, 0.0, 0.45))]
    foc_k = [(0.0, (0.03, -0.27, 0.01)), (1.8, (0.03, -0.27, 0.01)), (3.6, (0.0, 0.0, 0.25)), (6.75, (0.0, 0.0, 0.4))]
    return cam_rig(cam_k, aim_k, foc_k, lens=32, fstop=11)


def fw_burst(name, center, t_on, col, n=36, r=0.08):
    m = glow(name + "m", col, 30.0)
    rr = random.Random(hash(name) % 997)
    for i in range(n):
        th, ph = rr.uniform(0, 2 * math.pi), math.acos(rr.uniform(-1, 1))
        d = (math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph))
        o = sphere(f"{name}{i}", (0, 0, -9), 0.0018, m, segs=6)
        for f, t in frames():
            k = t - t_on
            if k < 0 or k > 1.4:
                key(o, f, loc=(0, 0, -9))
                continue
            e = 1 - math.exp(-4 * k)
            key(o, f, loc=(center[0] + d[0] * r * e, center[1] + d[1] * r * e, center[2] + d[2] * r * e - 0.05 * k * k),
                scale=(max(1e-4, 0.0018 * (1 - k / 1.4)),) * 3)


def m2_hate():
    W = world(night=False, golden=True)
    th_, tu, tm = cue("hated"), cue("useless"), cue("monstrous")
    rr = random.Random(9)
    painters = []
    for i in range(6):
        fg = Figure(f"p{i}", FH, coat=[(0.55, 0.2, 0.2), (0.2, 0.3, 0.5), (0.35, 0.3, 0.15), (0.45, 0.2, 0.45)][i % 4], hat="bowler" if i % 2 else None,
                    apron=(0.85, 0.8, 0.7) if i % 2 == 0 else None, mustache=i % 3 == 0, seed=300 + i)
        fg.place((-0.1 + i * 0.035, -0.24 - 0.008 * (i % 2), 0.0), 175 + rr.uniform(-12, 12))
        painters.append(fg)
    signs = []
    words = ["NON!", "UGLY", "NON!", "MONSTER", "NON!", "UGLY"]
    for i, fg in enumerate(painters):
        board = box(f"sign{i}", (0, 0, 0), (0.012, 0.0006, 0.007), paint("signm", (0.95, 0.92, 0.84), 0.8))
        stick = cyl(f"stick{i}", (0, 0, 0), 0.0003, 0.012, paint("stickm", (0.4, 0.26, 0.12), 0.7))
        tx = bpy.data.curves.new(f"signt{i}", "FONT")
        tx.body = words[i]
        tx.size = 0.0032
        tx.align_x = "CENTER"
        tx.align_y = "CENTER"
        to = bpy.data.objects.new(f"signt{i}", tx)
        link(to)
        to.rotation_euler = (math.pi / 2, 0, math.pi)
        tx.materials.append(paint("ink", (0.08, 0.06, 0.05), 0.6))
        signs.append((board, stick, to, fg))
    # one painter flings a blob of paint at the tower leg: ballistic arc, then it splats and stays (an impact with a consequence)
    src = (-0.03, -0.25, 0.012)
    hit = (-tw(4) * ST + 0.004, -tw(4) * ST + 0.002, 4 * ST)
    t0, dur = tm - 0.55, 0.5
    blob = sphere("paintblob", (0, 0, -9), 0.0025, paint("paintred", (0.85, 0.06, 0.05), 0.15))
    splat = sphere("paintsplat", hit, 1.0, paint("paintred2", (0.85, 0.06, 0.05), 0.15), scale=(1e-4, 1e-4, 1e-4))
    for f, t in frames():
        k = (t - t0) / dur
        for i, (board, stick, to, fg) in enumerate(signs):
            up = 0.002 * abs(math.sin(t * 5 + i))
            r_ = fg.root.location
            key(board, f, loc=(r_[0], r_[1] + 0.001, FH * 1.45 + up))
            key(stick, f, loc=(r_[0], r_[1] + 0.0012, FH * 1.45 - 0.006 + up))
            key(to, f, loc=(r_[0], r_[1] - 0.0004, FH * 1.45 + up))
            fg.pose(f, t, wave=(i != 2) and t > th_ - 0.3, look=(0, 25), point=(i == 2 and 0 < k < 0.3))
        if 0 <= k <= 1:
            p = (lerp(src[0], hit[0], k), lerp(src[1], hit[1], k), lerp(src[2], hit[2], k) + 0.05 * k * (1 - k))
            key(blob, f, loc=p, scale=(0.0025 * (1 + 0.3 * k), 0.0025, 0.0025 * (1 - 0.2 * k)))
        else:
            key(blob, f, loc=(0, 0, -9))
        s_ = 0.0 if k < 1 else min(1.0, (k - 1) * 6)
        key(splat, f, loc=hit, scale=(max(1e-4, 0.006 * s_), max(1e-4, 0.0012 * s_), max(1e-4, 0.005 * s_)))
    sparks("splash", hit, [t0 + dur], n=10, speed=0.03, col=(0.85, 0.08, 0.06))
    cam_k = [(0.0, (-0.14, -0.31, 0.014)), (3.0, (-0.02, -0.33, 0.018)), (5.0, (0.03, -0.34, 0.03)), (6.13, (0.05, -0.36, 0.05))]
    aim_k = [(0.0, (-0.08, -0.24, 0.01)), (3.0, (0.0, -0.24, 0.012)), (5.0, (-0.03, -0.1, 0.03)), (6.13, (-0.03, -0.08, 0.06))]
    foc_k = [(0.0, (-0.09, -0.24, 0.008)), (3.0, (0.0, -0.245, 0.008)), (4.8, (hit[0], hit[1], hit[2])), (6.13, (hit[0], hit[1], hit[2]))]
    return cam_rig(cam_k, aim_k, foc_k, lens=35, fstop=14)


def m3_permit():
    W = world(night=True, tower_lights=None)
    tp, ttw, t19, tc = cue("permit"), cue("twenty"), cue("nineteen"), cue("comes")
    # a giant real sheet of paper flutters down (falling-leaf motion) and lands FLAT in the square
    paper_m = AS.texture("paper_0025", "1k", scale=8.0) if False else paint("permitpaper", (0.93, 0.89, 0.78), 0.85)
    sheet = box("permit", (0, 0, 0), (0.15, 0.21, 0.0004), paper_m)
    land = (0.17, -0.3, 0.0004)
    t_land = ttw + 0.2
    for f, t in frames():
        k = (t - (tp - 0.5)) / (t_land - (tp - 0.5))
        if k < 0:
            key(sheet, f, loc=(land[0] - 0.05, land[1], 0.8), rot=(0.6, 0.3, 0.2))
        elif k < 1:
            sway = (1 - k)
            p = (land[0] + 0.06 * math.sin(k * 7) * sway, land[1] + 0.02 * math.cos(k * 5) * sway, land[2] + 0.8 * (1 - ease(k)) ** 1.3)
            key(sheet, f, loc=p, rot=(0.6 * sway * math.sin(k * 7 + 1), 0.4 * sway * math.cos(k * 6), 0.2 * sway + 0.15))
        else:
            key(sheet, f, loc=land, rot=(0, 0, 0.15))
    txt_m = paint("permink", (0.08, 0.06, 0.05), 0.6)
    red_m = paint("stampred", (0.75, 0.05, 0.04), 0.5)
    for i, (body, size, dy) in enumerate((("PERMIT", 0.022, 0.06), ("20 YEARS", 0.026, 0.02))):
        cu = bpy.data.curves.new(f"pt{i}", "FONT")
        cu.body = body
        cu.size = size
        cu.align_x = "CENTER"
        o = bpy.data.objects.new(f"pt{i}", cu)
        link(o)
        cu.materials.append(txt_m)
        parent(o, sheet)
        o.location = (0, dy, 0.0003)
    # a giant rubber stamp comes down and stamps 1909 — contact computed from the sheet top
    stamp = empty("stamp_root", (land[0], land[1] - 0.04, 0.5))
    handle = cyl("stamp_handle", (0, 0, 0.05), 0.012, 0.07, paint("stampwood", (0.42, 0.26, 0.12), 0.5))
    knob = sphere("stamp_knob", (0, 0, 0.095), 0.018, paint("stampwood2", (0.42, 0.26, 0.12), 0.5))
    pad = box("stamp_pad", (0, 0, 0.007), (0.07, 0.035, 0.014), paint("stampblock", (0.15, 0.1, 0.08), 0.5))
    rubber = box("stamp_rubber", (0, 0, 0.001), (0.066, 0.031, 0.002), red_m)
    for p_ in (handle, knob, pad, rubber):
        parent(p_, stamp)
    mark = bpy.data.curves.new("mark", "FONT")
    mark.body = "1909"
    mark.size = 0.026
    mark.align_x = "CENTER"
    mark.align_y = "CENTER"
    mo = bpy.data.objects.new("mark", mark)
    link(mo)
    mark.materials.append(red_m)
    parent(mo, sheet)
    mo.location = (0, -0.04, 0.00035)
    t_hit = t19 + 0.05
    for f, t in frames():
        if t < t19 - 0.6:
            z = 0.5
        elif t < t_hit:
            z = lerp(0.3, 0.0, ((t - (t19 - 0.6)) / 0.65) ** 2) + 0.0004
        elif t < t_hit + 0.25:
            z = 0.0004
        else:
            z = 0.0004 + 0.4 * ease((t - t_hit - 0.25) / 0.6)
        key(stamp, f, loc=(land[0], land[1] - 0.04, z))
        show(mo, f, t >= t_hit)
    # the demolition crane rolls in: wheels turn exactly with distance travelled
    croot, wheels = toy_crane("crane", (-0.5, -0.15, 0.0), (-0.35, -0.15, 0.42))
    x0, x1 = -0.75, -0.36
    for f, t in frames():
        k = ease_io((t - tc + 1.1) / 1.3)
        x = lerp(x0, x1, k)
        key(croot, f, loc=(x, -0.15, 0.0))
        for w in wheels:
            key(w, f, rot=(math.pi / 2, (x - x0) / 0.006, 0))
    cam_k = [(0.0, (0.25, -0.62, 0.32)), (2.4, (0.2, -0.55, 0.2)), (3.6, (0.16, -0.48, 0.16)), (5.66, (0.0, -0.75, 0.3))]
    aim_k = [(0.0, (0.15, -0.3, 0.25)), (2.4, (0.17, -0.31, 0.0)), (3.6, (0.17, -0.33, 0.0)), (5.66, (-0.15, -0.1, 0.12))]
    foc_k = [(0.0, (0.15, -0.3, 0.3)), (2.4, (0.17, -0.31, 0.0)), (4.0, (0.17, -0.33, 0.0)), (5.66, (-0.2, -0.12, 0.1))]
    return cam_rig(cam_k, aim_k, foc_k, lens=32, fstop=11)


def m4_clever():
    W = world(night=False, golden=True)
    tcl, tu = cue("clever"), cue("useful")
    G = Figure("gustave", FH * 1.02, coat=(0.1, 0.1, 0.16), hat="tophat", long_coat=True, mustache=True, hair=(0.5, 0.48, 0.45), seed=3)
    G.place((0.03, -0.27, 0.0), 200)
    bulb = sphere("idea", (0.03, -0.27, FH * 1.55), 0.0014, paint("ideag", (1.0, 0.95, 0.7), 0.1, emit=(1.0, 0.85, 0.4), estr=0.0))
    bp = bulb.data.materials[0].node_tree.nodes.get("Principled BSDF")
    bl = light("POINT", (0.03, -0.272, FH * 1.55), 0.0, (1.0, 0.85, 0.5), 0.001)
    for f, t in frames():
        k = ease((t - tcl) / 0.2)
        bp.inputs["Emission Strength"].default_value = 20 * k
        bp.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
        bl.data.energy = 0.02 * k
        bl.data.keyframe_insert("energy", frame=f)
        key(bulb, f, scale=(max(1e-4, 0.0014 * (0.2 + 0.8 * k)),) * 3)
        G.pose(f, t, look=(0, 30 if t > tcl else 10), point=t > tu - 0.3, carry=t < tcl - 0.1)
    cam_k = [(0.0, (0.05, -0.32, 0.011)), (3.56, (0.042, -0.305, 0.012))]
    aim_k = [(0.0, (0.03, -0.27, 0.009)), (3.56, (0.03, -0.27, 0.011))]
    foc_k = [(0.0, (0.03, -0.27, 0.009)), (3.56, (0.03, -0.27, 0.01))]
    return cam_rig(cam_k, aim_k, foc_k, lens=50, fstop=16)


def m5_science():
    W = world(night=False, golden=False)
    tw_, tdr = cue("weather"), cue("drops")
    top = 89 * ST + 0.7 * ST
    hut = box("hut", (-0.004, 0.003, top + 0.006), (0.01, 0.008, 0.012), paint("hutm", (0.9, 0.88, 0.82), 0.7))
    vane = empty("vane", (0.006, -0.004, top + 0.016))
    cyl("vpost", (0.006, -0.004, top + 0.008), 0.0004, 0.016, paint("vp", (0.2, 0.2, 0.2), 0.5, 0.8))
    for k in range(3):
        a = 2 * math.pi * k / 3
        cup = sphere(f"cup{k}", (0.004 * math.cos(a), 0.004 * math.sin(a), 0), 0.0012, paint("cupm", (0.8, 0.15, 0.1), 0.4))
        parent(cup, vane)
    for f, t in frames():
        key(vane, f, rot=(0, 0, t * (5 + 9 * ease((t - tw_) / 0.8))))
    # a cable from the 2nd platform to the ground; a weight slides down it with real incline physics (a = g sin(angle))
    p0, p1 = Vector((tw(39) * ST + 0.004, -0.01, 39 * ST)), Vector((0.24, -0.25, 0.0005))
    beams_mesh("cable", [(tuple(p0), tuple(p1), 0.0006)], paint("cablem", (0.1, 0.1, 0.1), 0.5))
    L_ = (p1 - p0).length
    sin_a = (p0.z - p1.z) / L_
    slider = sphere("slider", tuple(p0), 0.004, paint("sliderm", (0.85, 0.6, 0.15), 0.3, 1.0))
    for f, t in frames():
        k = max(0.0, t - tdr)
        s_ = min(L_ - 0.004, 0.5 * 9.81 * sin_a * 0.35 * k * k)       # friction + air drag lower the acceleration
        key(slider, f, loc=tuple(p0 + (p1 - p0).normalized() * s_))
    sci = Figure("sci", FH, coat=(0.92, 0.92, 0.88), mustache=True, seed=5)
    sci.place((0.0, -0.012, top), 180)
    for f, t in frames():
        sci.pose(f, t, point=t > tdr - 0.3, look=(20, -30 if t > tdr else 0))
    cam_k = [(0.0, (0.035, -0.06, top + 0.02)), (2.2, (0.05, -0.08, top + 0.0)), (5.62, (0.18, -0.42, 0.06))]
    aim_k = [(0.0, (0.0, 0.0, top + 0.008)), (2.2, (0.02, -0.02, 39 * ST)), (5.62, (0.22, -0.24, 0.0))]
    foc_k = [(0.0, (0.0, 0.0, top + 0.008)), (2.2, tuple(p0)), (5.62, tuple(p1))]
    return cam_rig(cam_k, aim_k, foc_k, lens=32, fstop=14)


def m6_antenna():
    W = world(night=True, antenna=True, tower_lights=4.0)
    ta, tm = cue("antenna"), cue("money")
    ant = W["antenna"]
    for f, t in frames():
        k = ease((t - ta + 0.9) / 0.7)
        settle = 0.06 * math.exp(-6 * max(0.0, t - ta + 0.2)) * math.sin(18 * max(0.0, t - ta + 0.2))
        h = max(1e-4, 12 * ST * (k + settle * k))
        key(ant, f, loc=(0, 0, 95 * ST + h / 2), scale=(0.35 * ST, 0.35 * ST, h / 2))
    # giant real coins drop beside the tower; analytic bounce (restitution 0.3), wobble, then lie flat — never overlapping
    coin_m = paint("gold", (1.0, 0.76, 0.25), 0.2, 1.0)
    spots = [(0.12, -0.2), (0.155, -0.235), (0.1, -0.25), (0.14, -0.28), (0.18, -0.205), (0.085, -0.215)]
    for i, (x, y) in enumerate(spots):
        c = cyl(f"coin{i}", (x, y, 0.5), 0.0105, 0.0016, coin_m, verts=48)
        t0 = tm - 0.9 + i * 0.12
        h0 = 0.35
        tf_ = math.sqrt(2 * h0 / 9.81)
        rr = random.Random(i)
        tilt0 = rr.uniform(0.6, 1.2)
        for f, t in frames():
            k = t - t0
            if k < 0:
                key(c, f, loc=(x, y, -1))
                continue
            if k < tf_:
                z = h0 - 0.5 * 9.81 * k * k
                rot = (tilt0 + 6 * k, 0.4 + 4 * k, 0)
            else:
                kb = k - tf_
                v0 = 0.3 * 9.81 * tf_
                hop = max(0.0, v0 * kb - 0.5 * 9.81 * kb * kb)
                z = 0.0008 + hop
                wob = 0.35 * math.exp(-6 * kb) * math.cos(30 * kb)
                rot = (wob, 0.5 * wob, kb * 0.5)
            key(c, f, loc=(x, y, max(0.0008, z)), rot=rot)
    cam_k = [(0.0, (0.06, -0.38, 0.62)), (1.8, (0.08, -0.4, 0.55)), (3.71, (0.25, -0.6, 0.12))]
    aim_k = [(0.0, (0.0, 0.0, 0.62)), (1.8, (0.0, 0.0, 0.6)), (3.71, (0.14, -0.23, 0.0))]
    foc_k = [(0.0, (0.0, 0.0, 0.62)), (2.2, (0.0, 0.0, 0.6)), (3.0, (0.14, -0.23, 0.0)), (3.71, (0.14, -0.23, 0.0))]
    return cam_rig(cam_k, aim_k, foc_k, lens=35, fstop=14)


def m7_army():
    W = world(night=False, golden=True, antenna=True)
    tl, tms = cue("loves"), cue("messages")
    sold = []
    for i in range(5):
        s_ = Figure(f"sol{i}", FH, coat=(0.15, 0.22, 0.5), trousers=(0.7, 0.08, 0.08), hat="cap", hat_col=(0.75, 0.08, 0.1), mustache=i % 2 == 0,
                    seed=400 + i)
        s_.place((0.1 + i * 0.016, -0.2 - (i % 2) * 0.008, 0.0), 160)
        sold.append(s_)
    for f, t in frames():
        for i, s_ in enumerate(sold):
            s_.pose(f, t, wave=t > tl, point=t <= tl and i == 2, look=(0, 30))
    top = (0, 0, 107 * ST)
    rings("msg", top, tms - 0.2, n=5, period=0.22, speed=0.55, life=1.3)
    t_arr = tms - 0.2 + 0.6
    radio_wake(W, t_arr)
    cam_k = [(0.0, (0.15, -0.3, 0.012)), (1.6, (0.2, -0.36, 0.05)), (3.61, (0.42, -0.42, 0.12))]
    aim_k = [(0.0, (0.13, -0.2, 0.01)), (1.6, (0.05, -0.05, 0.3)), (3.61, (0.33, -0.09, 0.07))]
    foc_k = [(0.0, (0.13, -0.2, 0.01)), (1.6, (0.0, 0.0, 0.4)), (3.0, (0.33, -0.18, 0.05)), (3.61, (0.33, -0.18, 0.05))]
    return cam_rig(cam_k, aim_k, foc_k, lens=30, fstop=14)


def m8_spy():
    W = world(night=True, antenna=True, tower_lights=2.0)
    tc, tr, tsp = cue("catches"), cue("radio"), cue("spy")
    rings("enemy", (0, 0, 107 * ST), tc - 0.9, n=5, period=0.2, speed=0.5, life=1.0, col=(1.0, 0.25, 0.2), inward=True)
    radio_wake(W, tc - 0.1)
    arm = W["parts"].get("morse_key_arm")
    taps = [tr - 0.2 + 0.18 * k for k in range(14) if k % 4 != 3]
    for f, t in frames():
        down = max([math.exp(-((t - tp) / 0.04) ** 2) for tp in taps] + [0.0])
        if arm is not None:
            key(arm, f, rot=(math.radians(-6 * down), 0, 0))
    spy = Figure("spy", FH, coat=(0.5, 0.42, 0.28), trousers=(0.15, 0.13, 0.12), hat="bowler", hat_col=(0.12, 0.1, 0.1), long_coat=True,
                 mustache=True, seed=7)
    p0, p1 = (-0.2, -0.45, 0.0), (-0.12, -0.38, 0.0)
    spot = light("SPOT", (-0.12, -0.42, 0.06), 0.0, (1.0, 0.95, 0.85), 0.002, spot_deg=16)
    aim_at(spot, spy.root)
    sold = [Figure(f"so{i}", FH, coat=(0.15, 0.22, 0.5), trousers=(0.7, 0.08, 0.08), hat="cap", hat_col=(0.75, 0.08, 0.1), seed=500 + i) for i in range(2)]
    so_from = [(-0.08, -0.36, 0.0), (-0.15, -0.33, 0.0)]
    so_to = [(-0.105, -0.375, 0.0), (-0.13, -0.36, 0.0)]
    for f, t in frames():
        caught = t > tsp - 0.15
        kk = ease((t - 1.0) / (tsp - 1.2))
        pos = lerp(p0, p1, kk)
        key(spy.root, f, loc=pos, rot=(0, 0, math.radians(-130)))
        spy.pose(f, t, walk=math.dist(p0, pos) / (0.35 * FH) if not caught and 0 < kk < 1 else None, look=(25 * math.sin(t * 2.4) if not caught else 0, 0),
                 wave=caught)
        spot.data.energy = 0.0 if not caught else 2.5
        spot.data.keyframe_insert("energy", frame=f)
        for i, s_ in enumerate(sold):
            k2 = ease((t - tsp + 0.05) / 0.6)
            q = lerp(so_from[i], so_to[i], k2)
            key(s_.root, f, loc=q, rot=(0, 0, math.radians(120 if i == 0 else -150)))
            s_.pose(f, t, walk=math.dist(so_from[i], q) / (0.35 * FH) if 0 < k2 < 1 else None, point=k2 >= 1)
    for i, (x, ph) in enumerate(((-0.3, 0.0), (0.3, 1.7))):
        m = paint(f"beam{i}", (0.85, 0.9, 1.0), 0.5, emit=(0.85, 0.9, 1.0), estr=0.6)
        m.node_tree.nodes.get("Principled BSDF").inputs["Alpha"].default_value = 0.06
        for attr, val in (("blend_method", "BLEND"), ("surface_render_method", "BLENDED")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
        piv = empty(f"slp{i}", (x, 0.3, 0.0))
        cone = prim(bpy.ops.mesh.primitive_cone_add, f"slb{i}", (0, 0, 0.6), mat=m, vertices=24, radius1=0.002, radius2=0.06, depth=1.2)
        parent(cone, piv)
        cone.location = (0, 0, 0.6)
        for f, t in frames():
            key(piv, f, rot=(math.radians(-25 + 12 * math.sin(t * 0.7 + ph)), math.radians(10 * math.sin(t * 0.5 + ph)), 0))
    key_pt = W["radio"].matrix_world @ Vector((0.074, -0.214, 0.03))
    cam_k = [(0.0, (0.05, -0.3, 0.6)), (2.6, (0.2, -0.42, 0.1)), (4.2, (0.15, -0.5, 0.04)), (6.86, (-0.07, -0.47, 0.016))]
    aim_k = [(0.0, (0.0, 0.0, 0.62)), (2.6, tuple(key_pt)), (4.2, tuple(key_pt)), (6.86, (-0.12, -0.38, 0.008))]
    foc_k = [(0.0, (0.0, 0.0, 0.62)), (2.6, tuple(key_pt)), (4.6, tuple(key_pt)), (5.6, (-0.12, -0.38, 0.008)), (6.86, (-0.12, -0.38, 0.008))]
    return cam_rig(cam_k, aim_k, foc_k, lens=35, fstop=14)


def m9_today():
    W = world(night=True, antenna=True, tower_lights=6.0)
    tn, ttd, tmo = cue("nobody"), cue("today"), cue("monument")
    croot, wheels = toy_crane("crane", (-0.36, -0.15, 0.0), (-0.21, -0.15, 0.42))
    for f, t in frames():
        k = ease_io((t - tn) / 1.6)
        x = lerp(-0.36, -0.85, k)
        key(croot, f, loc=(x, -0.15, 0.0))
        for w in wheels:
            key(w, f, rot=(math.pi / 2, (x + 0.36) / 0.006, 0))
    radio_wake(W, 0.0, 0.6)
    rr = random.Random(19)
    crowd = []
    for i in range(16):
        fg = Figure(f"now{i}", FH * rr.uniform(0.92, 1.05), coat=[(0.9, 0.3, 0.3), (0.3, 0.6, 0.9), (0.95, 0.8, 0.2), (0.4, 0.8, 0.5), (0.8, 0.45, 0.85)][i % 5],
                    hat=rr.choice([None, None, "cap"]), seed=600 + i)
        fg.place((rr.uniform(-0.1, 0.12), rr.uniform(-0.34, -0.26), 0.0), rr.uniform(165, 195))
        crowd.append(fg)
    for f, t in frames():
        for i, fg in enumerate(crowd):
            fg.pose(f, t, wave=t > ttd and (i % 2 == 0 or t > tmo), look=(0, 30))
    for j, (c_, col) in enumerate((((-0.18, 0.15, 0.75), (1.0, 0.6, 0.15)), ((0.2, 0.12, 0.8), (0.35, 0.6, 1.0)), ((0.0, 0.25, 0.95), (1.0, 0.3, 0.45)),
                                   ((-0.1, 0.3, 0.88), (0.4, 1.0, 0.5)))):
        fw_burst(f"fw9{j}", c_, tmo - 0.2 + 0.28 * j, col, r=0.09)
    cam_k = [(0.0, (0.04, -0.36, 0.014)), (2.5, (0.06, -0.5, 0.06)), (5.0, (0.2, -0.85, 0.3)), (7.13, (0.25, -1.15, 0.5))]
    aim_k = [(0.0, (0.0, -0.28, 0.012)), (2.5, (0.0, 0.0, 0.2)), (5.0, (0.08, 0.0, 0.35)), (7.13, (0.1, 0.0, 0.35))]
    foc_k = [(0.0, (0.0, -0.28, 0.012)), (2.0, (0.0, 0.0, 0.3)), (7.13, (0.1, 0.0, 0.3))]
    return cam_rig(cam_k, aim_k, foc_k, lens=32, fstop=11)


def m11_top():
    W = world(night=True, antenna=True, tower_lights=4.0)
    top = 89 * ST + 0.7 * ST
    pa = Figure("pa", FH, coat=(0.95, 0.4, 0.15), hat="cap", hat_col=(0.15, 0.4, 0.8), seed=8)
    pb = Figure("pb", FH, coat=(0.2, 0.75, 0.6), seed=9)
    pa.place((-0.004, -0.008, top), 0)
    pb.place((0.004, -0.009, top), 10)
    rail = box("rail", (0, -0.012, top + FH * 0.6), (0.026, 0.0004, 0.0004), paint("railm", (0.15, 0.15, 0.15), 0.4, 0.8))
    tcm = cue("comments")
    for f, t in frames():
        pa.pose(f, t, wave=True, look=(10, 0))
        pb.pose(f, t, carry=True, look=(0, -30 if t < tcm else 0))
    cam_k = [(0.0, (-0.03, -0.055, top + 0.022)), (2.77, (0.03, -0.06, top + 0.026))]
    aim_k = [(0.0, (0.0, -0.008, top + 0.006)), (2.77, (0.0, -0.008, top + 0.006))]
    foc_k = [(0.0, (0.0, -0.008, top + 0.006)), (2.77, (0.0, -0.008, top + 0.006))]
    return cam_rig(cam_k, aim_k, foc_k, lens=35, fstop=16)


SCENES_EM = {0: m0_hook, 1: m1_build, 2: m2_hate, 3: m3_permit, 4: m4_clever, 5: m5_science, 6: m6_antenna, 7: m7_army, 8: m8_spy, 9: m9_today, 11: m11_top}

if __name__ == "__main__":
    cam = SCENES_EM[IDX]()
    bake_all()
    setup_render(-0.2)
    lens_check(SC.camera)
    if os.environ.get("CHECK_ONLY"):
        sys.exit(0)
    if STILLS:
        SC.render.use_motion_blur = False
        for fr in STILLS:
            SC.frame_set(fr)
            SC.render.filepath = os.path.join(OUTDIR, f"s{IDX}", f"{fr:04d}.png")
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
