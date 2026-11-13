"""THE DAILYMIND — Miniature Cinematic Universe + Surreal Macro 3D: three 12-second test samples.

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
SAMPLE = argv[0] if argv else "S1"
OUTDIR = argv[1] if len(argv) > 1 else "/tmp/mini"
RES = int(argv[2]) if len(argv) > 2 else 100
SAMPLES = int(argv[3]) if len(argv) > 3 else 64
F0 = int(argv[4]) if len(argv) > 4 else 1
OUTFMT = os.environ.get("PLATE_FMT", "PNG")
STILLS = [int(x) for x in os.environ.get("STILL_FRAMES", "").split(",") if x.strip()]
FPS = 30
DUR = {"S2B": 15.0}.get(SAMPLE, 12.0)
NF = int(DUR * FPS)
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
    if os.environ.get("DM_ENGINE") == "CYCLES":   # ray-traced: real bounce light, soft shadows, true metal/glass
        SC.render.engine = "CYCLES"
        SC.cycles.samples = SAMPLES
        SC.cycles.use_denoising = True
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            for dev in ("OPTIX", "CUDA"):
                try:
                    prefs.compute_device_type = dev
                    prefs.get_devices()
                    for d in prefs.devices:
                        d.use = True
                    SC.cycles.device = "GPU"
                    break
                except Exception:
                    continue
        except Exception:
            pass
        SC.render.use_motion_blur = True
        SC.view_settings.view_transform = "AgX"
        try:
            SC.view_settings.look = "AgX - Medium High Contrast"
        except Exception:
            pass
        SC.view_settings.exposure = exposure
        _finish_output()
        SC.frame_start, SC.frame_end = F0, min(F1, NF)
        return
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
    _finish_output()


def _finish_output():
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
        SC.render.filepath = os.path.join(OUTDIR, f"{SAMPLE}.mp4")
        SC.render.use_file_extension = False
    else:
        SC.render.image_settings.file_format = "PNG"
        SC.render.image_settings.color_mode = "RGB"
        out = os.path.join(OUTDIR, SAMPLE)
        os.makedirs(out, exist_ok=True)
        SC.render.filepath = os.path.join(out, "")
    SC.frame_start, SC.frame_end = F0, min(F1, NF)


# ================================================================= S1 — the miniature historical world
def s1_paris1889():
    """A diorama of the 1889 Paris building site on an old workbench. Macro dolly at figure height past workers
    carrying a girder, a riveter throwing sparks, a steam crane lifting iron; the camera rises to reveal the half-built
    tower — and that the whole world is a model on a workbench beside giant tools."""
    AS.hdri("artist_workshop", "2k", 0.35, 160)
    bench = box("bench", (0, 0, -0.02), (1.6, 1.0, 0.04), AS.texture("dark_wooden_planks", "2k", scale=2.0))
    board_m = AS.texture("cobblestone_floor_08", "2k", scale=60.0)
    board = box("board", (0, 0, 0.004), (0.44, 0.3, 0.008), board_m, bevel=0.001)
    edge = box("board_edge", (0, 0, 0.002), (0.448, 0.308, 0.006), AS.texture("oak_wood_planks", "1k", scale=20.0), bevel=0.0015)
    gz = 0.008  # ground level of the diorama
    iron = AS.texture("rusty_metal_02", "1k", scale=4.0, tint=(0.32, 0.24, 0.2))  # lattice is built in model units (x0.0022 m)
    iron_m = AS.texture("rusty_metal_02", "1k", scale=600.0, tint=(0.32, 0.24, 0.2))  # same iron for objects built in metres
    S = 0.0022  # lattice units -> metres (the finished tower would be 22 cm)
    troot, bands = lattice_tower("T", iron, top_z=60, bands=8)
    troot.location = (0.06, 0.06, gz)
    troot.scale = (S, S, S)
    # the build goes up during the shot: band k appears with a springy settle
    for j, (o, z0) in enumerate(bands):
        t_on = -10 if j < 5 else 3.5 + (j - 5) * 2.2
        for f, t in frames():
            k = (t - t_on) / 0.5
            show(o, f, k > 0)
            if j >= 5:
                key(o, f, loc=(0, 0, 4.0 * (1 - min(1.0, max(0.0, k))) ** 2))
    # wooden scaffolding around the top of the build
    wood = AS.texture("brown_planks_05", "1k", scale=200.0)
    poles = []
    for i in range(10):
        a = 2 * math.pi * i / 10
        poles.append(((0.06 + 0.04 * math.cos(a), 0.06 + 0.04 * math.sin(a), gz), (0.06 + 0.032 * math.cos(a), 0.06 + 0.032 * math.sin(a), gz + 0.13), 0.0012))
    beams_mesh("scaffold", poles, wood)
    # steam crane lifting a girder
    crane_m = paint("crane_paint", (0.18, 0.2, 0.18), 0.5, 0.4)
    cbase = box("crane_base", (-0.07, 0.09, gz + 0.006), (0.02, 0.02, 0.012), crane_m, bevel=0.001)
    cpiv = empty("crane_piv", (-0.07, 0.09, gz + 0.012))
    boom = beams_mesh("crane_boom", [((0, 0, 0), (0.09, 0.0, 0.11), 0.0025), ((0.0, 0.006, 0), (0.09, 0.0, 0.11), 0.0015)], crane_m)
    parent(boom, cpiv)
    chim = cyl("crane_chim", (-0.075, 0.092, gz + 0.022), 0.0025, 0.02, paint("chim", (0.08, 0.08, 0.08), 0.4, 0.6))
    girder = beams_mesh("girder", [((-0.02, 0, 0), (0.02, 0, 0), 0.003)], iron_m)
    hook_rope = cyl("rope", (0, 0, 0), 0.0003, 1.0, paint("ropem", (0.15, 0.12, 0.1), 0.8))
    for f, t in frames():
        yaw = math.radians(-25 + 50 * ease_io((t - 1.0) / 8.0))
        key(cpiv, f, rot=(0, 0, yaw))
        tip = (cpiv.location.x + 0.09 * math.cos(yaw), cpiv.location.y + 0.09 * math.sin(yaw), cpiv.location.z + 0.11)
        L = 0.085 - 0.06 * ease_io((t - 0.5) / 7.0)
        gpos = (tip[0], tip[1], tip[2] - L)
        key(girder, f, loc=gpos, rot=(0, 0, yaw + 0.3 * math.sin(t * 0.8)))
        key(hook_rope, f, loc=(tip[0], tip[1], tip[2] - L / 2), scale=(0.0003, 0.0003, L / 2))
    smoke("steam", (-0.075, 0.092, gz + 0.034), 0.0, n=7, size=0.006, rise=0.05, period=0.45, life=3.0)
    # workers
    W = [Figure("w_carry1", FIG_H, coat=(0.22, 0.28, 0.42), hat="cap", mustache=True),
         Figure("w_carry2", FIG_H, coat=(0.42, 0.3, 0.2), hat="cap"),
         Figure("w_rivet", FIG_H, coat=(0.3, 0.25, 0.2), apron=(0.5, 0.42, 0.3), hat="cap", mustache=True),
         Figure("w_boss", FIG_H, coat=(0.08, 0.08, 0.1), hat="tophat", long_coat=True, mustache=True),
         Figure("w_lady", FIG_H, coat=(0.45, 0.18, 0.22), long_coat=True, hat="bowler", hat_col=(0.3, 0.1, 0.12)),
         Figure("w_walk", FIG_H, coat=(0.25, 0.32, 0.25), hat="bowler", long_coat=True)]
    beam = beams_mesh("carried_beam", [((-0.012, 0, 0), (0.012, 0, 0), 0.0016)], iron_m)
    p0, p1 = (-0.15, -0.07, gz), (0.0, -0.01, gz)
    rivet_t = [0.6 + 0.55 * k for k in range(22)]
    for f, t in frames():
        k = ease((t - 0.2) / 9.0)
        x = lerp(p0[0], p1[0], k)
        y = lerp(p0[1], p1[1], k)
        ph = (x - p0[0]) / 0.006
        yaw = math.degrees(math.atan2(-(p1[0] - p0[0]), (p1[1] - p0[1]))) + 180
        for i, w in enumerate(W[:2]):
            off = (-0.008 if i == 0 else 0.008)
            key(w.root, f, loc=(x + off * math.cos(math.radians(yaw - 90)) * -1, y + off * 0.3, gz), rot=(0, 0, math.radians(yaw - 90)))
            w.pose(f, t, walk=ph + 0.5 * i, carry=True)
        key(beam, f, loc=(x, y, gz + FIG_H * 0.82), rot=(0, 0, math.radians(yaw - 90 + 90)))
        W[2].pose(f, t, hammer=(t - 0.6) / 0.55, look=(0, -15))
        W[3].pose(f, t, point=t > 4.0, look=(30 if t < 4 else 10, 10))
        kk = ease((t - 0.0) / 12.0)
        key(W[4].root, f, loc=(lerp(0.05, -0.1, kk), -0.11, gz), rot=(0, 0, math.radians(-90)))
        W[4].pose(f, t, walk=(0.05 - lerp(0.05, -0.1, kk)) / 0.006, look=(70, 10))
        key(W[5].root, f, loc=(lerp(0.07, -0.08, kk), -0.12, gz), rot=(0, 0, math.radians(-90)))
        W[5].pose(f, t, walk=(0.07 - lerp(0.07, -0.08, kk)) / 0.006 + 0.3, look=(60, 15))
    W[2].place((0.035, 0.022, gz), 160)
    W[3].place((-0.02, 0.0, gz), 30)
    sparks("rivet_sparks", (0.033, 0.03, gz + FIG_H * 0.75), rivet_t, n=12, speed=0.05)
    # gas lamps (real model, 1:100) + warm practical lights
    for i, (x, y) in enumerate(((-0.12, -0.04), (0.13, -0.05), (-0.03, -0.09))):
        AS.model("street_lamp_01", "1k", loc=(x, y, gz), scale=0.01, name=f"lamp{i}")
        light("POINT", (x, y, gz + 0.036), 0.25, (1.0, 0.7, 0.4), 0.002)
    # giant real tools on the workbench (scale reveal)
    AS.model("adjustable_wrench", "1k", loc=(-0.05, 0.2, 0.0), rot=(0, 0, 0.3), scale=1.0, name="g_wrench")
    AS.model("vintage_hand_drill", "1k", loc=(0.1, 0.26, 0.0), rot=(0, 0, -0.4), scale=1.0, name="g_drill")
    AS.model("brass_candleholders", "1k", loc=(-0.12, 0.28, 0.0), scale=1.0, name="g_candle")
    key_l = light("SPOT", (-0.35, -0.45, 0.6), 45.0, (1.0, 0.8, 0.55), 0.06, spot_deg=50)
    aim_at(key_l, empty("key_tgt", (0.0, 0.03, 0.0)))
    light("AREA", (0.5, 0.2, 0.4), 2.0, (0.55, 0.65, 1.0), 0.4, rot=(math.radians(60), 0, math.radians(110)))

    def path(t):
        k1 = ease_io(t / 7.0)
        k2 = ease_io((t - 6.5) / 5.5)
        c = lerp((-0.19, -0.11, gz + 0.012), (-0.03, -0.075, gz + 0.016), k1)
        c = lerp(c, (0.0, -0.42, 0.26), k2)
        a = lerp((-0.09, -0.05, gz + 0.012), (0.04, 0.03, gz + 0.03), k1)
        a = lerp(a, (0.02, 0.03, 0.05), k2)
        return add(c, drift(t, 0.0006)), a

    def focus(t):  # follow the girder carriers, then rack to the riveter, then the whole tower
        kc = ease((t - 0.2) / 9.0)
        carriers = (lerp(p0[0], p1[0], kc), lerp(p0[1], p1[1], kc), gz + 0.012)
        k1 = ease_io((t - 4.0) / 1.5)
        k2 = ease_io((t - 6.5) / 4.0)
        p = lerp(carriers, (0.034, 0.025, gz + 0.012), k1)
        return lerp(p, (0.04, 0.04, 0.04), k2)
    macro_camera(path, focus, lens=45, fstop=9.0)
    w = SC.world
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    vs = w.node_tree.nodes.new("ShaderNodeVolumeScatter")
    vs.inputs["Density"].default_value = 0.25
    w.node_tree.links.new(vs.outputs[0], w.node_tree.nodes["World Output"].inputs["Volume"])
    return dict(exposure=0.3)


# ================================================================= S2 — surreal giant everyday object
def house(name, x, y, w, d, h, wall, roof, win_m, yaw=0.0):
    root = empty(name, (x, y, 0.0))
    root.rotation_euler = (0, 0, yaw)
    b = box(name + "_b", (0, 0, h / 2), (w, d, h), wall, bevel=0.0003)
    parent(b, root)
    b.location = (0, 0, h / 2)
    r = prim(bpy.ops.mesh.primitive_cylinder_add, name + "_r", (0, 0, 0), (1, 1, 1), mat=roof, vertices=4)
    parent(r, root)
    r.location = (0, 0, h + 0.008)
    r.rotation_euler = (0, 0, math.pi / 4)
    r.scale = (w * 0.74, d * 0.74, 0.008)
    wins = []
    rows = max(2, int(h / 0.022))
    cols = max(2, int(w / 0.018))
    for i in range(rows):
        for j in range(cols):
            wn = box(f"{name}_w{i}_{j}", (0, 0, 0), (0.0055, 0.0008, 0.009), win_m)
            parent(wn, root)
            wn.location = (-w / 2 + (j + 0.5) * w / cols, -d / 2 - 0.0002, 0.012 + i * (h - 0.014) / rows)
            wins.append(wn)
    door = box(name + "_door", (0, 0, 0), (0.007, 0.0008, 0.011), paint(name + "doorm", (0.18, 0.1, 0.06), 0.5))
    parent(door, root)
    door.location = (0, -d / 2 - 0.0003, 0.0055)
    return root, wins


def s2_giant_watch():
    """A real pocket watch stands like a monument in a 1:100 town square. Tiny townsfolk stroll, a child points, a
    cleaner on a ladder polishes the glass. Then the hands start to SPIN — and the sky falls from golden hour into
    night as every window lights up: the everyday object rules time itself."""
    AS.hdri("belfast_sunset_puresky", "2k", 1.0, 200)
    world = SC.world
    bg = world.node_tree.nodes["Background"]
    ground = cyl("square", (0, 0, -0.002), 0.5, 0.004, AS.texture("cobblestone_floor_08", "2k", scale=70.0), verts=96)
    walls = [AS.texture(n, "1k", scale=60.0) for n in ("painted_plaster_wall", "grey_plaster", "clay_plaster")]
    roofs = [AS.texture(n, "1k", scale=120.0) for n in ("grey_roof_tiles", "clay_roof_tiles")]
    win_m = paint("winlit", (0.2, 0.17, 0.12), 0.3, emit=(1.0, 0.7, 0.35), estr=0.0)
    p = win_m.node_tree.nodes.get("Principled BSDF")
    all_wins = []
    for i in range(14):
        a = math.pi * (0.15 + 0.7 * i / 13) + math.pi * 0.0
        r_ = 0.2 + R.uniform(-0.01, 0.02)
        x, y = r_ * math.cos(a + math.pi / 2 * 0), r_ * math.sin(a)
        x, y = r_ * math.cos(a), r_ * math.sin(a) + 0.04
        _, wins = house(f"h{i}", x, y, R.uniform(0.04, 0.06), 0.045, R.uniform(0.07, 0.11), walls[i % 3], roofs[i % 2], win_m,
                        yaw=a - math.pi / 2)
        all_wins += wins
    watch_root, wobjs = AS.model("vintage_pocket_watch", "2k", loc=(0, 0.035, 0.0), rot=(math.radians(-8), 0, 0), scale=1.0, name="watch")
    hands = {o.name.split("_")[-2]: o for o in wobjs if "hand" in o.name}
    for f, t in frames():
        spin = ease((t - 6.0) / 1.0) * (t - 6.0) * 6.0 if t > 6.0 else 0.0
        if "second" in hands:
            ang = -2 * math.pi * (int(t) / 60.0) - spin * 6
            key(hands["second"], f, rot=(0, ang, 0))
        if "minute" in hands:
            key(hands["minute"], f, rot=(0, -spin, 0))
        if "hour" in hands:
            key(hands["hour"], f, rot=(0, -spin / 12, 0))
        night = ease((t - 6.3) / 3.0)
        bg.inputs["Strength"].default_value = 1.0 - 0.93 * night
        bg.inputs["Strength"].keyframe_insert("default_value", frame=f)
        p.inputs["Emission Strength"].default_value = 6.0 * ease((t - 7.0) / 2.0)
        p.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
    sun = light("SUN", (0, 0, 1), 3.5, (1.0, 0.72, 0.45), 2, rot=(math.radians(72), 0, math.radians(-30)))
    moon = light("SUN", (0, 0, 1), 0.0, (0.55, 0.65, 1.0), 2, rot=(math.radians(50), 0, math.radians(150)))
    wglow = light("POINT", (0, 0.02, 0.045), 0.0, (1.0, 0.75, 0.4), 0.02)
    for f, t in frames():
        night = ease((t - 6.3) / 3.0)
        sun.data.energy = 3.5 * (1 - night)
        sun.data.keyframe_insert("energy", frame=f)
        moon.data.energy = 0.6 * night
        moon.data.keyframe_insert("energy", frame=f)
        wglow.data.energy = 1.2 * night
        wglow.data.keyframe_insert("energy", frame=f)
    for i, (x, y) in enumerate(((-0.08, -0.06), (0.09, -0.07), (-0.12, 0.05), (0.13, 0.06))):
        AS.model("street_lamp_02", "1k", loc=(x, y, 0.0), scale=0.01, name=f"slamp{i}")
        L = light("POINT", (x, y, 0.04), 0.0, (1.0, 0.7, 0.4), 0.002)
        for f, t in frames():
            L.data.energy = 0.35 * ease((t - 7.2) / 1.5)
            L.data.keyframe_insert("energy", frame=f)
    # townsfolk
    F = []
    rr = random.Random(12)
    cols = [(0.45, 0.18, 0.22), (0.2, 0.28, 0.45), (0.3, 0.35, 0.25), (0.5, 0.4, 0.2), (0.15, 0.15, 0.18), (0.55, 0.3, 0.15)]
    for i in range(9):
        fg = Figure(f"town{i}", FIG_H * rr.uniform(0.92, 1.05), coat=cols[i % 6], long_coat=i % 2 == 0,
                    hat=rr.choice(["bowler", "cap", None, "tophat"]), mustache=i % 3 == 0)
        F.append(fg)
    kid = Figure("kid", FIG_H * 0.62, coat=(0.75, 0.55, 0.15), hat=None)
    cleaner = Figure("cleaner", FIG_H, coat=(0.25, 0.3, 0.45), hat="cap", apron=(0.6, 0.55, 0.45))
    ladder = beams_mesh("ladder", [((-0.003, 0, 0), (-0.002, 0.004, 0.035), 0.0008), ((0.003, 0, 0), (0.004, 0.004, 0.035), 0.0008)] +
                        [((-0.003 + 0.0002 * k, 0.0004 * k, 0.004 * k), (0.003 + 0.0002 * k, 0.0004 * k, 0.004 * k), 0.0005) for k in range(1, 9)],
                        AS.texture("brown_planks_05", "1k", scale=300.0))
    ladder.location = (0.012, 0.0, 0.0)
    cleaner.place((0.0135, 0.0035, 0.021), 180)
    kid.place((-0.03, -0.045, 0.0), 160)
    paths = []
    for i, fg in enumerate(F):
        a0 = rr.uniform(0, 2 * math.pi)
        rad = rr.uniform(0.06, 0.11)
        sp = rr.choice([-1, 1]) * rr.uniform(0.05, 0.08)
        paths.append((a0, rad, sp))
    for f, t in frames():
        for fg, (a0, rad, sp) in zip(F, paths):
            a = a0 + sp * t / rad
            x, y = rad * math.cos(a), rad * math.sin(a) - 0.01
            yaw = math.degrees(a) + (180 if sp > 0 else 0)
            key(fg.root, f, loc=(x, y, 0.0), rot=(0, 0, math.radians(yaw)))
            fg.pose(f, t, walk=abs(sp) * t / 0.006, look=(rr.uniform(-20, 20) * 0 + 25 * math.sin(t * 0.5 + a0), 12))
        kid.pose(f, t, point=True, look=(0, 25), wave=t > 7.5)
        cleaner.pose(f, t, wave=True, look=(0, 10))
    def path(t):
        k = ease_io(t / 6.0)
        k2 = ease_io((t - 6.0) / 6.0)
        c = lerp((-0.05, -0.12, 0.006), (-0.012, -0.05, 0.02), k)
        c = lerp(c, (0.0, -0.3, 0.2), k2)
        a = lerp((-0.03, -0.045, 0.01), (0.0, 0.03, 0.045), k)
        a = lerp(a, (0.0, 0.02, 0.03), k2)
        return add(c, drift(t, 0.0005)), a

    def focus(t):
        return lerp(lerp((-0.03, -0.045, 0.01), (0.0, 0.025, 0.045), ease_io((t - 1.0) / 3.0)), (0.0, 0.02, 0.03), ease_io((t - 6.0) / 5.0))
    macro_camera(path, focus, lens=42, fstop=8.0)
    return dict(exposure=-0.3)


# ================================================================= S3 — the cinematic miniature industrial world
def gear_mesh(name, teeth, r_in, r_out, th, mat):
    verts, faces = [], []
    n = teeth * 4
    for z in (-th / 2, th / 2):
        for i in range(n):
            a = 2 * math.pi * i / n
            r = r_out if (i % 4) in (1, 2) else r_in
            verts.append((r * math.cos(a), r * math.sin(a), z))
        verts.append((0, 0, z))
    c0, c1 = n, 2 * n + 1
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, c0))
        faces.append((n + 1 + j, n + 1 + i, c1))
        faces.append((i, n + 1 + i, n + 1 + j, j))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    link(o)
    o.data.materials.append(mat)
    b = o.modifiers.new("bevel", "BEVEL")
    b.width = th * 0.08
    b.segments = 2
    b.limit_method = "ANGLE"
    return o


def s3_factory():
    """A tiny factory at 1:100: a conveyor carries crates under a stamping press (sparks + steam on every hit), big
    gears and pistons drive it, workers pull levers and push a cart, hanging lamps sway. Macro dolly along the line,
    then a rise to reveal the whole floor."""
    AS.hdri("boiler_room", "2k", 0.8, 40)
    fill = light("AREA", (0.0, -0.4, 0.3), 6.0, (0.7, 0.75, 0.9), 0.4, rot=(math.radians(55), 0, 0))
    floor = box("floor", (0, 0, -0.002), (0.6, 0.5, 0.004), AS.texture("concrete_floor_worn_001", "2k", scale=40.0))
    wall = box("wall", (0, 0.2, 0.09), (0.6, 0.01, 0.18), AS.texture("factory_brick", "2k", scale=40.0))
    wall2 = box("wall2", (-0.3, 0, 0.09), (0.01, 0.5, 0.18), AS.texture("factory_brick", "2k", scale=40.0))
    metal = AS.texture("rusty_painted_metal", "1k", scale=150.0)
    steel = paint("steel", (0.55, 0.56, 0.58), 0.3, 1.0)
    brass = paint("brassm", (0.8, 0.58, 0.22), 0.25, 1.0)
    belt_m = paint("belt", (0.04, 0.04, 0.045), 0.7)
    # conveyor
    cz = 0.012
    frame_ = box("conv_frame", (0, 0.0, cz - 0.003), (0.36, 0.03, 0.004), metal, bevel=0.0005)
    for k in range(7):
        box(f"conv_leg{k}", (-0.17 + k * 0.057, 0.0, (cz - 0.005) / 2), (0.003, 0.026, cz - 0.005), metal)
    belt = box("conv_belt", (0, 0.0, cz), (0.36, 0.024, 0.0015), belt_m)
    rollers = []
    for k in range(10):
        rl = cyl(f"roller{k}", (-0.17 + k * 0.038, 0.0, cz - 0.0005), 0.0018, 0.027, steel, verts=16, rot=(math.pi / 2, 0, 0))
        rollers.append(rl)
    # --- cause and effect: an INDEXED belt (stop-go) so each crate stops under the press, the ram lands exactly on the
    # crate's top, the crate squashes and springs back, gets a gold stamp, sparks + dust burst at the contact point.
    from mathutils import Vector
    crate_root, crate_objs = AS.model("wooden_crate_01", "1k", loc=(0, 0, -1), scale=1.0, name="crate_src")
    bpy.context.view_layer.update()  # matrix_world is stale until the depsgraph updates
    zs = [(o.matrix_world @ Vector(c)).z for o in crate_objs for c in o.bound_box]
    xs = [(o.matrix_world @ Vector(c)).x for o in crate_objs for c in o.bound_box]
    cdim = max(max(o.dimensions) for o in crate_objs)
    csc = 0.012 / cdim
    c_bottom = (min(zs) + 1.0) * csc          # crate origin -> bottom offset (scaled)
    c_h = (max(zs) - min(zs)) * csc           # crate height (scaled)
    c_w = (max(xs) - min(xs)) * csc
    belt_top = cz + 0.00075
    print(f"[crate] height {c_h * 1000:.2f} mm, width {c_w * 1000:.2f} mm, origin->bottom {c_bottom * 1000:.2f} mm")
    CYCLE, MOVE, SPACING = 1.25, 0.55, 0.05   # one stamp per cycle; the belt moves one crate-spacing in MOVE seconds
    T_DOWN, T_HIT, T_UP = 0.62, 0.74, 1.12    # ram starts down / contact / back up (seconds into the cycle)
    press_x = 0.02
    crates = []
    for i in range(8):
        r_, _ = AS.model("wooden_crate_01", "1k", loc=(0, 0, -1), scale=csc, name=f"crate{i}")
        stampm = glow(f"stamp{i}", (1.0, 0.72, 0.25), 3.0)
        st = box(f"stamp_mark{i}", (0, 0, 0), (0.7, 0.7, 0.02), stampm)   # in crate-local units (parented, scaled with the crate)
        parent(st, r_)
        st.location = (0, 0, (max(zs) + 1.0) + 0.005)
        st.scale = (0.25 * cdim, 0.25 * cdim, 0.01)
        crates.append((r_, st))

    def belt_pos(t):  # distance travelled by the belt at time t (stop-go)
        n = math.floor(t / CYCLE)
        return SPACING * (n + ease((t - n * CYCLE) / MOVE))

    hits = []
    n_cycles = int(DUR / CYCLE) + 1
    for k in range(n_cycles):
        th = k * CYCLE + T_HIT
        if th < DUR:
            hits.append(th)
    for f, t in frames():
        bp = belt_pos(t)
        ph = t % CYCLE
        for i, (c, st) in enumerate(crates):
            x = -0.18 + ((bp + i * SPACING) % 0.4)
            z = belt_top - c_bottom
            sq = 1.0
            # is this crate the one under the press right now?
            under = abs(x - press_x) < 0.004
            if under and T_HIT <= ph:
                sq = 1.0 - 0.14 * math.exp(-9 * (ph - T_HIT)) * math.cos(30 * (ph - T_HIT))   # squash, then spring back
            if x > 0.17:  # tips off the end into the bin
                kk = (x - 0.17) / SPACING * MOVE
                x = 0.17 + 0.02 * kk
                z = max(0.003 - c_bottom, z - 0.5 * 9.81 * kk * kk * 0.3)
            key(c, f, loc=(x, 0.0, z), scale=(csc / math.sqrt(sq), csc / math.sqrt(sq), csc * sq))
            stamped = x > press_x + 0.002 or (under and ph >= T_HIT)
            show(st, f, stamped)
        for rl in rollers:
            key(rl, f, rot=(math.pi / 2, -bp / 0.0018, 0))
    bin_ = box("bin", (0.205, 0.0, 0.006), (0.03, 0.04, 0.012), metal, bevel=0.0005)
    # stamping press: the ram's lowest point is EXACTLY the crate top (contact), computed from the real crate size
    press_col = paint("press_paint", (0.5, 0.12, 0.08), 0.45, 0.3)
    for s_ in (-1, 1):
        box(f"press_col{s_}", (press_x, s_ * 0.022, cz + 0.03), (0.008, 0.008, 0.06), press_col, bevel=0.0008)
    box("press_top", (press_x, 0.0, cz + 0.062), (0.016, 0.056, 0.012), press_col, bevel=0.001)
    RAM_H = 0.012
    ram = box("press_ram", (press_x, 0.0, cz + 0.03), (min(0.014, c_w * 0.9), 0.022, RAM_H), steel, bevel=0.0008)
    crate_top = belt_top + c_h
    z_up = cz + 0.05 - RAM_H / 2
    z_contact = crate_top + RAM_H / 2
    for f, t in frames():
        ph = t % CYCLE
        if ph < T_DOWN:
            z = z_up
        elif ph < T_HIT:
            z = lerp(z_up, z_contact, ((ph - T_DOWN) / (T_HIT - T_DOWN)) ** 2)   # accelerates down
        elif ph < T_HIT + 0.1:
            z = z_contact - 0.14 * c_h * math.exp(-9 * (ph - T_HIT)) * max(0.0, math.cos(30 * (ph - T_HIT)))  # follows the squash
        else:
            z = lerp(z_contact, z_up, ease((ph - T_HIT - 0.1) / (T_UP - T_HIT - 0.1)))
        key(ram, f, loc=(press_x, 0.0, z))
    sparks("press_sparks", (press_x, 0.0, crate_top), hits, n=16, speed=0.05)
    for k, th in enumerate(hits):
        smoke(f"press_dust{k}", (press_x, 0.0, belt_top + 0.002), th, n=3, size=0.004, rise=0.008, col=(0.7, 0.6, 0.48), life=0.9)
    PRESS_HITS[:] = hits
    smoke("press_steam", (press_x + 0.01, 0.015, cz + 0.06), 0.0, n=6, size=0.007, rise=0.06, period=0.5, life=3.0)
    # gears + pistons on the back wall
    gears = [gear_mesh("gear_big", 18, 0.028, 0.032, 0.006, brass), gear_mesh("gear_mid", 12, 0.018, 0.0215, 0.006, steel),
             gear_mesh("gear_sm", 8, 0.011, 0.0145, 0.006, brass)]
    places = [(-0.12, 0.19, 0.07), (-0.069, 0.19, 0.105), (-0.04, 0.19, 0.075)]
    rates = [1.0, -18 / 12, 18 / 8]
    for g, p_, rt in zip(gears, places, rates):
        g.location = p_
        for f, t in frames():
            key(g, f, rot=(math.pi / 2, 0.0, 0.0), loc=p_)
            g.rotation_euler = (math.pi / 2, t * 0.9 * rt, 0)
            g.keyframe_insert("rotation_euler", frame=f)
    for k in range(3):
        cylb = cyl(f"pist_cyl{k}", (0.1 + k * 0.03, 0.17, 0.05), 0.006, 0.05, steel)
        rod = cyl(f"pist_rod{k}", (0.1 + k * 0.03, 0.17, 0.08), 0.0025, 0.04, brass)
        for f, t in frames():
            key(rod, f, loc=(0.1 + k * 0.03, 0.17, 0.085 + 0.012 * math.sin(t * 5 + k * 2.1)))
        smoke(f"pist_steam{k}", (0.1 + k * 0.03, 0.165, 0.11), 0.3 * k, n=4, size=0.005, rise=0.04, period=0.7, life=2.5)
    # pipes + props (real models at 1:100)
    AS.model("modular_industrial_pipes_01", "1k", loc=(0.1, 0.18, 0.0), scale=0.012, name="pipes")
    for i, (nm, p_) in enumerate((("oil_tin", (-0.2, -0.08, 0.0)), ("metal_jerrycan", (-0.22, -0.05, 0.0)), ("metal_toolbox", (0.22, -0.1, 0.0)))):
        AS.model(nm, "1k", loc=p_, scale=0.012 * 6 if nm == "oil_tin" else 0.012, name=f"prop{i}")
    lamps = []
    for i, x in enumerate((-0.1, 0.02, 0.14)):
        piv = empty(f"lamp_piv{i}", (x, 0.0, 0.17))
        lr, _ = AS.model("hanging_industrial_lamp", "1k", loc=(0, 0, -0.06), scale=0.012 * 3.0, name=f"hlamp{i}")
        parent(lr, piv)
        lr.location = (0, 0, -0.06)
        L = light("SPOT", (0, 0, 0), 6.0, (1.0, 0.72, 0.42), 0.004, spot_deg=80)
        parent(L, piv)
        L.location = (0, 0, -0.07)
        L.rotation_euler = (0, 0, 0)
        cord = cyl(f"cord{i}", (0, 0, -0.03), 0.0004, 0.06, paint("cordm", (0.05, 0.05, 0.05), 0.6))
        parent(cord, piv)
        for f, t in frames():
            key(piv, f, rot=(math.radians(3 * math.sin(t * 1.6 + i)), math.radians(2 * math.cos(t * 1.3 + i)), 0))
        lamps.append(piv)
    # workers
    lev = Figure("f_lever", FIG_H, coat=(0.25, 0.32, 0.45), hat="cap", mustache=True, apron=(0.4, 0.35, 0.28))
    lev.place((press_x + 0.017, -0.035, 0.0), -143)    # beside the press, seen in profile, facing his lever
    # a real lever: pivot box bolted to the press column, linkage rod up into the press, handle from the pivot to his hand
    lever_red = paint("lever_red", (0.7, 0.1, 0.06), 0.35, 0.2)
    box("lever_box", (press_x + 0.01, -0.026, 0.003), (0.008, 0.006, 0.006), press_col, bevel=0.0005)
    link_bot, link_top = 0.006, cz + 0.048        # from the top of the pivot box up into the press head (no gap)
    cyl("lever_link", (press_x + 0.0095, -0.025, (link_bot + link_top) / 2), 0.0005, link_top - link_bot, steel)
    box("lever_link_top", (press_x + 0.0075, -0.025, cz + 0.048), (0.005, 0.0012, 0.0012), steel)
    piv = empty("lever_pivot", (press_x + 0.011, -0.029, 0.0058))
    lever = beams_mesh("lever", [((0, 0, 0), (0, 1.0, 0), 0.0011)], steel)
    lever.location = piv.location
    st = lever.constraints.new("STRETCH_TO")      # always spans pivot -> the worker's actual hand
    st.target = lev.hands[1]
    st.rest_length = 1.0
    st.volume = "NO_VOLUME"
    st.keep_axis = "PLANE_X"
    knob = sphere("lever_knob", (0, 0, 0), 1.0, lever_red, segs=12)
    parent(knob, lev.hands[1])
    knob.location = (0, 0, -0.01)
    knob.scale = (0.045, 0.045, 0.045)
    cartw = Figure("f_cart", FIG_H, coat=(0.45, 0.25, 0.15), hat="cap")
    cart = box("cart", (0, 0, 0), (0.018, 0.012, 0.008), metal, bevel=0.0006)
    weld = Figure("f_weld", FIG_H, coat=(0.2, 0.22, 0.2), hat="helmet", hat_col=(0.15, 0.15, 0.17))
    weld.place((-0.12, 0.16, 0.0), 0)
    insp = Figure("f_insp", FIG_H, coat=(0.9, 0.9, 0.86), hat=None, mustache=True)
    insp.place((0.17, 0.03, 0.0), 120)
    weld_t = [0.3 + 0.18 * k for k in range(60) if (k // 6) % 2 == 0]
    sparks("weld_sparks", (-0.12, 0.175, 0.012), weld_t, n=10, speed=0.04, col=(0.6, 0.8, 1.0))
    wl = light("POINT", (-0.12, 0.17, 0.014), 0.0, (0.6, 0.8, 1.0), 0.001)
    for f, t in frames():
        ph = t % CYCLE
        pull = ease((ph - 0.45) / 0.17) if ph < T_HIT else (1 - ease((ph - T_HIT - 0.1) / 0.35))
        lev.pose(f, t, lever=pull, look=(0, -10))
        k = ease((t - 0.5) / 9.0)
        x = lerp(-0.2, 0.08, k)
        key(cartw.root, f, loc=(x, -0.065, 0.0), rot=(0, 0, math.radians(-90)))
        cartw.pose(f, t, walk=(x + 0.2) / 0.006, carry=True)
        key(cart, f, loc=(x + 0.016, -0.065, 0.006))
        weld.pose(f, t, carry=True, look=(0, -20))
        insp.pose(f, t, point=t > 5, look=(-30, 0))
        on = any(0 <= t - w_ < 0.18 for w_ in weld_t)
        wl.data.energy = 0.25 * on * (0.6 + 0.4 * math.sin(t * 80))
        wl.data.keyframe_insert("energy", frame=f)

    cam_k = [(0.0, (-0.2, -0.06, 0.016)), (2.5, (-0.085, -0.065, 0.021)), (5.0, (-0.012, -0.064, 0.026)), (7.4, (0.012, -0.075, 0.034)),
             (12.0, (0.08, -0.36, 0.22))]
    aim_k = [(0.0, (-0.12, 0.0, 0.014)), (2.5, (-0.035, 0.0, 0.014)), (5.0, (press_x, 0.0, cz + 0.01)), (7.4, (press_x + 0.006, 0.0, cz + 0.014)),
             (12.0, (0.0, 0.05, 0.04))]
    foc_k = [(0.0, (-0.1, -0.01, 0.014)), (4.0, (press_x, 0.0, cz + 0.008)), (7.4, (press_x + 0.006, -0.01, cz + 0.008)), (12.0, (0.0, 0.05, 0.04))]

    def path(t):  # ONE continuous Catmull-Rom move: it never stops, it keeps drifting slowly past the press
        return add(catmull(cam_k, t), drift(t, 0.0003)), catmull(aim_k, t)

    def focus(t):
        return catmull(foc_k, t)
    macro_camera(path, focus, lens=40, fstop=8.0, smooth=0.06)
    w = SC.world
    vs = w.node_tree.nodes.new("ShaderNodeVolumeScatter")
    vs.inputs["Density"].default_value = 0.3
    w.node_tree.links.new(vs.outputs[0], w.node_tree.nodes["World Output"].inputs["Volume"])
    return dict(exposure=0.4)


# ================================================================= S2B — the polished giant watch (v2)
def catmull(keys, t):
    """Smooth path through (time, value-tuple) keys (Catmull-Rom with eased timing)."""
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    for i in range(len(keys) - 1):
        t0, p1 = keys[i]
        t1, p2 = keys[i + 1]
        if t0 <= t <= t1:
            u = ease_io((t - t0) / (t1 - t0)) if False else (t - t0) / (t1 - t0)
            p0 = keys[i - 1][1] if i > 0 else p1
            p3 = keys[i + 2][1] if i + 2 < len(keys) else p2
            u2, u3 = u * u, u * u * u
            return tuple(0.5 * ((2 * b) + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u2 + (-a + 3 * b - 3 * c + d) * u3)
                         for a, b, c, d in zip(p0, p1, p2, p3))


def s2b_giant_watch():
    """v2 — 15 s. Macro on a real pocket watch standing like a monument in a 1:220 Parisian square at golden hour; a
    cleaner on a ladder polishes its glass. The camera sinks to street level: strollers, a child with a red balloon, a
    newspaper reader, a lamplighter. The hands begin to SPIN — the sun drops, night falls in seconds, the lamplighter
    lights the lamps one by one and every window glows. A crane shot reveals the whole square around the glowing watch."""
    import town_kit as TK
    TS = 0.0045                     # town scale (1:220)
    FH = 1.75 * TS                  # figure height ~8 mm
    T_SPIN, T_NIGHT = 7.0, 7.4
    AS.hdri("belfast_sunset_puresky", "2k", 1.0, 200)
    wnt = SC.world.node_tree
    bg = wnt.nodes["Background"]
    env_link = bg.inputs["Color"].links[0]
    env_out = env_link.from_socket
    mix = wnt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[7].default_value = (0.012, 0.018, 0.05, 1)  # deep night blue
    wnt.links.new(env_out, mix.inputs[6])
    wnt.links.new(mix.outputs[2], bg.inputs["Color"])
    # ground: cobbled square (tinted so the stones read), stone kerb, paved pavement ring
    cob = AS.texture("cobblestone_floor_08", "2k", scale=1.0 / (2.0 * TS) * 0.9, tint=(0.62, 0.56, 0.5))
    cyl("square", (0, 0, -0.001), 0.17, 0.002, cob, verts=128)
    pave = AS.texture("rectangular_paving", "1k", scale=1.0 / (3.0 * TS), tint=(0.75, 0.72, 0.68))
    ring = cyl("pavement", (0, 0, -0.0022), 0.34, 0.003, pave, verts=128)  # top sits 0.7 mm BELOW the square: no z-fighting
    kerb = prim(bpy.ops.mesh.primitive_torus_add, "kerb", (0, 0, 0.0004), mat=AS.texture("precast_stone_paving", "1k", scale=600.0),
                major_radius=0.172, minor_radius=0.0009, major_segments=160, minor_segments=6)
    ground = box("outer_ground", (0, 0, -0.006), (2.0, 2.0, 0.004), AS.texture("concrete_floor_worn_001", "1k", scale=200.0, tint=(0.4, 0.4, 0.42)))
    # the town: a crescent of detailed buildings, each with its own window glass (lit one after another at dusk)
    TK.init(None, AS.texture("painted_plaster_wall", "1k", scale=1.0 / (4.0 * TS)), AS.texture("grey_roof_tiles", "1k", scale=1.0 / (2.0 * TS)), scale=TS)
    glass_mats = []
    rr = random.Random(5)
    n_b = 13
    for i in range(n_b):
        gm = paint(f"glass{i}", (0.06, 0.07, 0.09), 0.08, emit=(1.0, 0.72, 0.38), estr=0.0)
        TK.TEX["glass"] = gm
        TK.TEX["shop_glass"] = gm
        a = math.pi * (0.05 + 0.9 * i / (n_b - 1))
        r_ = 0.2 + rr.uniform(0, 0.012)
        TK.building(f"tb{i}", (r_ * math.cos(a), r_ * math.sin(a) + 0.01), a - math.pi / 2, floors=rr.choice([4, 5, 5, 6]),
                    bays=rr.choice([2, 3, 3]), wall=TK.WALLS[i % len(TK.WALLS)], shutters=TK.SHUTTERS[rr.randrange(len(TK.SHUTTERS))],
                    shop=rr.random() < 0.75, seed=40 + i)
        glass_mats.append((gm, T_NIGHT + 0.6 + 0.22 * ((i * 7) % n_b)))
    for gm, t_on in glass_mats:
        p = gm.node_tree.nodes.get("Principled BSDF")
        for f, t in frames():
            p.inputs["Emission Strength"].default_value = 7.0 * ease((t - t_on) / 0.35)
            p.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
    # the giant: a real pocket watch standing on its edge
    wr, wobjs = AS.model("vintage_pocket_watch", "2k", loc=(0, 0.035, 0.0405), rot=(math.radians(-6), 0, 0), scale=1.0, name="watch")
    hands = {o.name.split("_")[-2]: o for o in wobjs if "hand" in o.name}
    for f, t in frames():
        k = max(0.0, t - T_SPIN)
        spin = 14.0 * k * k / (1 + 1.2 * k)        # accelerates into a whirl
        sec = -2 * math.pi * (int(t) / 60.0) - spin * 3
        if "second" in hands:
            key(hands["second"], f, rot=(0, sec, 0))
        if "minute" in hands:
            key(hands["minute"], f, rot=(0, -spin * 0.6, 0))
        if "hour" in hands:
            key(hands["hour"], f, rot=(0, -spin * 0.05, 0))
        night = ease((t - T_NIGHT) / 2.2)
        bg.inputs["Strength"].default_value = 1.0 - 0.75 * night
        bg.inputs["Strength"].keyframe_insert("default_value", frame=f)
        mix.inputs["Factor"].default_value = night
        mix.inputs["Factor"].keyframe_insert("default_value", frame=f)
    sun = light("SUN", (0, 0, 1), 4.0, (1.0, 0.68, 0.42), 1.5, rot=(math.radians(76), 0, math.radians(-35)))
    moon = light("SUN", (0, 0, 1), 0.0, (0.5, 0.62, 1.0), 1.0, rot=(math.radians(45), 0, math.radians(150)))
    wglow = light("POINT", (0, -0.03, 0.06), 0.0, (1.0, 0.75, 0.42), 0.02)
    for f, t in frames():
        night = ease((t - T_NIGHT) / 2.2)
        key(sun, f, rot=(math.radians(76 + 14 * night), 0, math.radians(-35)))
        sun.data.energy = 4.0 * (1 - night) ** 1.5
        sun.data.keyframe_insert("energy", frame=f)
        moon.data.energy = 0.35 * night
        moon.data.keyframe_insert("energy", frame=f)
        wglow.data.energy = 0.35 * night
        wglow.data.keyframe_insert("energy", frame=f)
    # street lamps, lit one by one by the lamplighter
    lamp_pos = [(-0.06, -0.035), (0.075, -0.05), (0.095, 0.0), (-0.1, 0.03)]
    lamp_on = [T_NIGHT + 1.2, T_NIGHT + 2.6, T_NIGHT + 3.6, T_NIGHT + 4.3]
    for i, ((x, y), ton) in enumerate(zip(lamp_pos, lamp_on)):
        AS.model("street_lamp_02", "1k", loc=(x, y, 0.0), scale=TS, name=f"slamp{i}")
        L = light("POINT", (x, y, 4.0 * TS), 0.0, (1.0, 0.68, 0.38), 0.0008)
        bulb = sphere(f"lampglow{i}", (x, y, 4.0 * TS), 0.0007, glow(f"lg{i}", (1.0, 0.75, 0.4), 1.0))
        bm = bulb.data.materials[0].node_tree.nodes.get("Emission")
        for f, t in frames():
            k = ease((t - ton) / 0.25)
            L.data.energy = 0.08 * k
            L.data.keyframe_insert("energy", frame=f)
            bm.inputs["Strength"].default_value = 0.2 + 12 * k
            bm.inputs["Strength"].keyframe_insert("default_value", frame=f)
            show(bulb, f, t >= ton - 0.03)  # an unlit glow ball read as a dull olive disc when near the lens
    # benches
    for i, (x, y, yaw) in enumerate(((-0.045, 0.05, 0.6), (0.05, 0.055, -0.6))):
        b_ = box(f"bench{i}", (x, y, 0.45 * TS), (1.8 * TS, 0.5 * TS, 0.12 * TS), paint("benchwood", (0.32, 0.18, 0.08), 0.6), rot=(0, 0, yaw))
    # townsfolk
    cols = [(0.45, 0.18, 0.22), (0.2, 0.28, 0.45), (0.3, 0.35, 0.25), (0.5, 0.4, 0.2), (0.15, 0.15, 0.18), (0.55, 0.3, 0.15), (0.35, 0.22, 0.4)]
    walkers = []
    rr = random.Random(12)
    for i in range(14):
        fg = Figure(f"town{i}", FH * rr.uniform(0.93, 1.05), coat=cols[i % len(cols)], long_coat=i % 2 == 0,
                    hat=rr.choice(["bowler", "cap", None, "tophat", "bowler"]), mustache=i % 3 == 0, seed=100 + i)
        a0 = rr.uniform(0, 2 * math.pi)
        rad = rr.uniform(0.07, 0.15)
        sp = rr.choice([-1, 1]) * rr.uniform(0.012, 0.018)
        walkers.append((fg, a0, rad, sp))
    kid = Figure("kid", FH * 0.6, coat=(0.75, 0.55, 0.15), seed=7)
    kid.place((0.022, -0.05, 0.0), 200)
    string = cyl("balloon_string", (0, 0, 0), 0.00006, 1.0, paint("string", (0.9, 0.9, 0.9), 0.5))
    balloon = sphere("balloon", (0, 0, 0), 1.0, paint("balloonred", (0.85, 0.05, 0.06), 0.15), scale=(0.0007, 0.0007, 0.00085))
    reader = Figure("reader", FH, coat=(0.18, 0.2, 0.25), hat="bowler", long_coat=True, mustache=True, seed=8)
    reader.place((-0.04, 0.046, 0.0), 150)
    paper = box("newspaper", (0, 0, 0), (0.07, 0.003, 0.05), paint("paper", (0.9, 0.88, 0.82), 0.8))
    parent(paper, reader.hands[1])
    paper.location = (0.02, -0.04, 0.02)
    cleaner = Figure("cleaner", FH, coat=(0.25, 0.3, 0.45), hat="cap", apron=(0.6, 0.55, 0.45), seed=9)
    ladder = beams_mesh("ladder", [((-0.0013, 0, 0), (-0.0009, 0.0028, 0.03), 0.0004), ((0.0013, 0, 0), (0.0017, 0.0028, 0.03), 0.0004)] +
                        [((-0.0013 + 0.00013 * k, 0.00028 * k, 0.003 * k), (0.0013 + 0.00013 * k, 0.00028 * k, 0.003 * k), 0.00025) for k in range(1, 10)],
                        paint("ladderwood", (0.45, 0.3, 0.15), 0.6))
    ladder.location = (0.022, 0.025, 0.0)
    cleaner.place((0.0235, 0.0265, 0.026), 180)
    rag = box("rag", (0, 0, 0), (0.04, 0.03, 0.03), paint("rag", (0.9, 0.85, 0.7), 0.9))
    parent(rag, cleaner.hands[1])
    lighter = Figure("lamplighter", FH, coat=(0.12, 0.15, 0.25), hat="cap", mustache=True, seed=10)
    pole = cyl("lpole", (0, 0, 0), 0.006, 0.45, paint("lpolem", (0.25, 0.18, 0.1), 0.6))
    parent(pole, lighter.hands[1])
    pole.location = (0, 0, 0.2)
    flame = sphere("lflame", (0, 0, 0), 0.012, glow("lflamem", (1.0, 0.6, 0.2), 30.0))
    parent(flame, lighter.hands[1])
    flame.location = (0, 0, 0.43)
    lpath = [(-0.09, -0.055), lamp_pos[0], lamp_pos[1], lamp_pos[2]]
    for f, t in frames():
        for fg, a0, rad, sp in walkers:
            a = a0 + sp * t / rad
            x, y = rad * math.cos(a), rad * math.sin(a) - 0.01
            yaw = math.degrees(a) + (180 if sp > 0 else 0)
            key(fg.root, f, loc=(x, y, 0.0), rot=(0, 0, math.radians(yaw)))
            night = t > T_NIGHT + 0.5
            fg.pose(f, t, walk=abs(sp) * t / (0.35 * FH), look=(30 * math.sin(t * 0.5 + a0), 20 if night else 10))
        kid.pose(f, t, wave=True, look=(0, 30 if t > T_SPIN else 10))
        reader.pose(f, t, carry=t < T_SPIN + 0.4, look=(0, -15) if t < T_SPIN + 0.4 else (-30, 25))
        cleaner.pose(f, t, wave=True, look=(0, 0))
        # lamplighter: walk lamp to lamp; raise the pole to each lamp just before it comes on
        seg_t = [(T_NIGHT - 0.4, lamp_on[0]), (lamp_on[0] + 0.3, lamp_on[1]), (lamp_on[1] + 0.3, lamp_on[2])]
        pos, walking, raise_ = lpath[0], None, False
        for k_, (ts, te) in enumerate(seg_t):
            if t >= ts:
                kk = ease((t - ts) / max(0.1, te - ts - 0.35))
                a_, b_ = lpath[k_], lpath[k_ + 1]
                b_ = (b_[0] - 0.004, b_[1] - 0.004)
                a_ = a_ if k_ == 0 else (a_[0] - 0.004, a_[1] - 0.004)
                pos = lerp(a_, b_, kk)
                walking = None if kk >= 1 else math.dist(a_, pos) / (0.35 * FH)
                raise_ = te - 0.4 < t < te + 0.25
                yaw_l = math.degrees(math.atan2(-(b_[0] - a_[0]), (b_[1] - a_[1]))) + 180
        key(lighter.root, f, loc=(pos[0], pos[1], 0.0), rot=(0, 0, math.radians(yaw_l if t >= seg_t[0][0] else 160)))
        lighter.pose(f, t, walk=walking, point=raise_, look=(0, 30 if raise_ else 5))
        # balloon floats above the kid's hand
        # raised right hand of the child (local +X, the kid faces away at yaw 200 deg -> world offset (-0.94, -0.34))
        hx, hy, hz = 0.022 - 0.0013, -0.05 - 0.0005, 0.6 * FH * 1.09
        bz = hz + 0.0045 + 0.0003 * math.sin(t * 2)
        key(balloon, f, loc=(hx + 0.0004 * math.sin(t * 1.3), hy, bz))
        key(string, f, loc=(hx, hy, (hz + bz) / 2), scale=(0.00006, 0.00006, (bz - hz) / 2))
    # camera: Catmull-Rom through story beats, then zero-lag smoothing (macro rig)
    cam_k = [(0.0, (0.03, -0.035, 0.05)), (3.2, (0.045, -0.075, 0.03)), (6.6, (0.02, -0.105, 0.007)), (9.6, (-0.02, -0.12, 0.016)),
             (12.0, (-0.01, -0.2, 0.08)), (15.0, (0.0, -0.33, 0.21))]
    aim_k = [(0.0, (0.0, 0.035, 0.048)), (3.2, (0.015, -0.02, 0.02)), (6.6, (0.015, -0.03, 0.009)), (9.6, (-0.03, -0.03, 0.02)),
             (12.0, (0.0, 0.02, 0.03)), (15.0, (0.0, 0.03, 0.02))]
    foc_k = [(0.0, (0.0, 0.033, 0.045)), (2.0, (0.0235, 0.026, 0.033)), (3.4, (0.0235, 0.026, 0.03)), (4.6, (0.022, -0.05, 0.005)),
             (6.6, (0.022, -0.05, 0.005)), (7.4, (0.0, 0.03, 0.04)), (8.9, (0.0, 0.03, 0.04)), (9.8, (-0.06, -0.035, 0.008)),
             (11.5, (0.0, 0.03, 0.04)), (15.0, (0.0, 0.03, 0.03))]
    macro_camera(lambda t: (add(catmull(cam_k, t), drift(t, 0.0003)), catmull(aim_k, t)), lambda t: catmull(foc_k, t), lens=50, fstop=22.0,
                 smooth=0.1)
    return dict(exposure=-0.2)


PRESS_HITS = []
SAMPLES_FN = {"S1": s1_paris1889, "S2": s2_giant_watch, "S3": s3_factory, "S2B": s2b_giant_watch}

if __name__ == "__main__":
    cfg = SAMPLES_FN[SAMPLE]() or {}
    bake_all()
    setup_render(cfg.get("exposure", 0.0))
    if STILLS:
        SC.render.use_motion_blur = False
        for fr in STILLS:
            SC.frame_set(fr)
            SC.render.filepath = os.path.join(OUTDIR, SAMPLE, f"{fr:04d}.png")
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
