"""Real-3D (Blender) plates for "Airplane Windows Are Round Because of a TERRIBLE Mistake".

Each run builds ONE scene from scratch and renders its frames (no text — titles/slams/stamps, splats, music and the
end card are composited afterwards by ultimate/make_window3d.py, so the classic DailyMind look stays).
Toon characters are animated PNG sequences (ultimate/sprites_window.py) on camera-facing planes: flat characters in
a real lit 3D world. Every animation is keyframed per frame from closed-form physics (deterministic).

Run (bpy module):   python window3d.py -- SCENE OUTDIR [RES_PCT=100] [SAMPLES=24] [ENGINE=EEVEE|CYCLES] [F0] [F1]
Run (Blender app):  blender -b -P window3d.py -- SCENE OUTDIR ...      (use this on the RTX PC: ENGINE=EEVEE)
"""
import json
import math
import os
import random
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SCENE = int(argv[0]) if argv else 0
OUTDIR = argv[1] if len(argv) > 1 else "/tmp/plates"
RES = int(argv[2]) if len(argv) > 2 else 100
SAMPLES = int(argv[3]) if len(argv) > 3 else 24
ENGINE = argv[4] if len(argv) > 4 else "EEVEE"
OUTFMT = os.environ.get("PLATE_FMT", "PNG")  # PNG frames, or MP4 (one small high-quality video per scene, easy to upload)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PLAN = json.load(open(os.path.join(ROOT, "window", "plan.json")))
DUR, CUE = PLAN["durs"], PLAN["cues"]
SPR = os.path.join(ROOT, "window3d", "sprites")
FPS = 30
NF = int(math.ceil(DUR[SCENE] * FPS)) + 1
F0 = int(argv[5]) if len(argv) > 5 else 1
F1 = int(argv[6]) if len(argv) > 6 else NF

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
SC.render.fps = FPS
SC.frame_start, SC.frame_end = 1, NF
SC.render.resolution_x, SC.render.resolution_y = 1080, 1920
SC.render.resolution_percentage = RES


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def spring(t, at, amp=1.0, freq=3.0, damp=4.0):
    k = t - at
    return 0.0 if k < 0 else amp * math.exp(-damp * k) * math.cos(2 * math.pi * freq * k)


def frames():
    """(frame, t) for every frame of the scene."""
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


def pbr(name, col, rough=0.5, metal=0.0, emit=None, estr=0.0, alpha=1.0, transmission=0.0, ior=1.45):
    m, nt, out = new_mat(name)
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if transmission:
        p.inputs["Transmission Weight"].default_value = transmission
        p.inputs["IOR"].default_value = ior
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = estr
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def see_through(name, col, alpha, rough=0.05, glow=0.0):
    """Alpha-blended glass/water: renders the same in EEVEE and Cycles (EEVEE turned transmission into a black box)."""
    m, nt, out = new_mat(name)
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Alpha"].default_value = alpha
    if glow:
        p.inputs["Emission Color"].default_value = (*col, 1)
        p.inputs["Emission Strength"].default_value = glow
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    for attr, val in (("blend_method", "BLEND"), ("surface_render_method", "BLENDED"), ("use_backface_culling", False),
                      ("show_transparent_back", True)):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
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


def fuselage_paint(name="paint"):
    """White top, blue cheatline, bare-metal belly (by object-space height)."""
    m, nt, out = new_mat(name)
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = 0.22
    p.inputs["Metallic"].default_value = 0.15
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    rp = nt.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.interpolation = "CONSTANT"
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.6
    mr.inputs["From Max"].default_value = 1.6
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs[0], rp.inputs["Fac"])
    els = rp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.55, 0.57, 0.62, 1)
    els[1].position, els[1].color = 0.38, (0.03, 0.12, 0.42, 1)
    e = els.new(0.47)
    e.color = (0.92, 0.93, 0.95, 1)
    nt.links.new(rp.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def sky_window_mat(name, speed=0.15, night=False):
    """Emissive 'view through the window': sky gradient + soft clouds sliding past."""
    m, nt, out = new_mat(name)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 0.9
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    grad = nt.nodes.new("ShaderNodeValToRGB")
    if night:
        grad.color_ramp.elements[0].color = (0.05, 0.08, 0.2, 1)
        grad.color_ramp.elements[1].color = (0.01, 0.015, 0.05, 1)
    else:
        grad.color_ramp.elements[0].color = (1.0, 0.55, 0.3, 1)
        grad.color_ramp.elements[1].color = (0.15, 0.4, 0.95, 1)
    nt.links.new(sep.outputs["Z"], grad.inputs["Fac"])
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.5
    nz.inputs["Detail"].default_value = 4
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.5
    cr.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr.color_ramp.elements[1].position = 0.62
    cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(cr.outputs["Color"], mix.inputs["Factor"])
    nt.links.new(grad.outputs["Color"], mix.inputs["A"])
    mix.inputs["B"].default_value = (1, 1, 1, 1)
    nt.links.new(mix.outputs["Result"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    for f, t in frames():  # clouds slide past the window
        mp.inputs["Location"].default_value = (t * speed, 0, 0)
        mp.inputs["Location"].keyframe_insert("default_value", frame=f)
    return m


MAT = {}


def mats():
    MAT["paint"] = fuselage_paint()
    MAT["metal"] = noisy("metal", (0.55, 0.57, 0.6), (0.72, 0.74, 0.78), 40, 0.32, 0.03, metal=0.9)
    MAT["glass_dark"] = pbr("glass_dark", (0.01, 0.015, 0.03), 0.25, 0.0)
    MAT["tyre"] = pbr("tyre", (0.02, 0.02, 0.02), 0.8)
    MAT["concrete"] = noisy("concrete", (0.16, 0.16, 0.17), (0.3, 0.3, 0.31), 3, 0.85, 0.1)
    MAT["steel"] = pbr("steel", (0.25, 0.26, 0.28), 0.4, 0.7)
    MAT["grass"] = noisy("grass", (0.03, 0.09, 0.02), (0.1, 0.22, 0.05), 0.4, 0.9, 0.0)
    MAT["asphalt"] = noisy("asphalt", (0.035, 0.035, 0.04), (0.09, 0.09, 0.1), 2, 0.8, 0.05)
    MAT["white"] = pbr("white", (0.9, 0.9, 0.88), 0.5)
    MAT["cabin"] = pbr("cabin", (0.62, 0.6, 0.56), 0.55)
    MAT["seat"] = noisy("seat", (0.05, 0.1, 0.28), (0.09, 0.16, 0.38), 60, 0.9, 0.2)
    MAT["carpet"] = noisy("carpet", (0.16, 0.04, 0.06), (0.26, 0.07, 0.09), 80, 0.95, 0.2)
    MAT["yellow"] = pbr("yellow", (0.95, 0.7, 0.05), 0.4)
    MAT["red"] = pbr("red", (0.7, 0.04, 0.04), 0.4)
    MAT["wood"] = noisy("wood", (0.25, 0.13, 0.06), (0.45, 0.27, 0.12), 6, 0.6, 0.1)
    MAT["light"] = emission("light", (1.0, 0.92, 0.8), 6)
    MAT["frame"] = pbr("frame", (0.85, 0.84, 0.8), 0.35)


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
        bv.segments = 4
        bv.limit_method = "NONE"
    if smooth:
        bpy.ops.object.shade_smooth()
    return o


def box(name, center, size, mat, bevel=0.0):
    return prim(bpy.ops.mesh.primitive_cube_add, name, center, (size[0] / 2, size[1] / 2, size[2] / 2), mat=mat, bevel=bevel)


def rounded_panel(name, center, w, h, depth, radius, mat, rot=(0, 0, 0), n=8):
    """Rounded-rectangle slab built as a mesh: w along local X, h along local Z, depth along local Y."""
    r = max(0.001, min(radius, min(w, h) / 2 - 0.001))
    outline = []
    for cx, cz, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            outline.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    m = len(outline)
    verts = [(x, -depth / 2, z) for x, z in outline] + [(x, depth / 2, z) for x, z in outline]
    faces = [tuple(range(m)), tuple(range(2 * m - 1, m - 1, -1))]
    faces += [(i, (i + 1) % m, m + (i + 1) % m, m + i) for i in range(m)]
    o = mesh_obj(name, verts, faces, mat)
    o.location = center
    o.rotation_euler = rot
    return o


def sprite(name, folder, loc, height, cam, nframes=None, start=1):
    """Camera-facing plane with an animated PNG sequence (feet at loc)."""
    first = os.path.join(SPR, folder, "0001.png") if os.path.isdir(os.path.join(SPR, folder)) else os.path.join(SPR, folder)
    img = bpy.data.images.load(first)
    w = height * img.size[0] / img.size[1]
    o = mesh_obj(name, [(-w / 2, 0, 0), (w / 2, 0, 0), (w / 2, 0, height), (-w / 2, 0, height)], [(0, 1, 2, 3)])
    uv = o.data.uv_layers.new()
    for i, (u, v) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[i].uv = (u, v)
    o.location = loc
    m, nt, out = new_mat(name + "_m")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Cubic"
    if os.path.isdir(os.path.join(SPR, folder)):
        img.source = "SEQUENCE"
        n = nframes or len([f for f in os.listdir(os.path.join(SPR, folder)) if f.endswith(".png")])
        tex.image_user.frame_duration = n
        tex.image_user.frame_start = start
        tex.image_user.use_auto_refresh = True
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = 0.85
    em = nt.nodes.new("ShaderNodeEmission")  # a little self-light so toon colours stay vivid
    em.inputs["Strength"].default_value = 0.35
    nt.links.new(tex.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(p.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Alpha"], mx.inputs["Fac"])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(add.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    for attr, val in (("blend_method", "HASHED"), ("surface_render_method", "DITHERED")):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    o.data.materials.append(m)
    c = o.constraints.new("LOCKED_TRACK")  # turn around Z to always face the camera
    c.target = cam
    c.track_axis = "TRACK_NEGATIVE_Y"
    c.lock_axis = "LOCK_Z"
    return o


def text3d(name, body, loc, size, mat, cam=None):
    bpy.ops.object.text_add(location=loc, rotation=(math.pi / 2, 0, 0))
    o = bpy.context.active_object
    o.name = name
    o.data.body = body
    o.data.align_x = "CENTER"
    o.data.size = size
    o.data.extrude = size * 0.08
    o.data.materials.append(mat)
    if cam:
        c = o.constraints.new("DAMPED_TRACK")
        c.target = cam
        c.track_axis = "TRACK_Z"
    return o


def key_loc_rot(o, f, loc=None, rot=None, scale=None):
    if loc is not None:
        o.location = loc
        o.keyframe_insert("location", frame=f)
    if rot is not None:
        o.rotation_euler = rot
        o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        o.scale = scale
        o.keyframe_insert("scale", frame=f)


def empty(name, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    link(o)
    o.location = loc
    return o


def parent(child, par):
    """Children are built in the parent's local space (plane origin), so no inverse: they follow root's transform."""
    child.parent = par
    child.matrix_parent_inverse.identity()


# ---------------------------------------------------------------- the jet (generic 1950s airliner, ~28 m)
def comet(prefix, loc=(0, 0, 0), win_r=0.03, gear=True, glow_ring=False):
    """Returns (root, front, back): front/back halves are separate parents so the jet can break in two.
    Nose points +X, fuselage radius 1.5 m, windows row on both sides."""
    root = empty(prefix + "_root", loc)
    fr = empty(prefix + "_front")
    bk = empty(prefix + "_back")
    parent(fr, root)
    parent(bk, root)
    fr.location = bk.location = (0, 0, 0)
    R = 1.5
    f1 = prim(bpy.ops.mesh.primitive_cylinder_add, prefix + "_fusF", (5.5, 0, 0), (R, R, 5.5), (0, math.pi / 2, 0), MAT["paint"],
              smooth=True, vertices=48)
    b1 = prim(bpy.ops.mesh.primitive_cylinder_add, prefix + "_fusB", (-5.5, 0, 0), (R, R, 5.5), (0, math.pi / 2, 0), MAT["paint"],
              smooth=True, vertices=48)
    nose = prim(bpy.ops.mesh.primitive_uv_sphere_add, prefix + "_nose", (11, 0, 0), (3.4, R, R), mat=MAT["paint"], smooth=True, segments=48,
                ring_count=24)
    tail = prim(bpy.ops.mesh.primitive_cone_add, prefix + "_tail", (-13.5, 0, 0.15), mat=MAT["paint"], rot=(0, -math.pi / 2, 0),
                smooth=True, vertices=48, radius1=R, radius2=0.3, depth=5.0)
    # cockpit glazing
    for k in range(3):
        for s in (-1, 1):
            g = box(f"{prefix}_ck{k}{s}", (12.6 + k * 0.45, s * 0.75, 0.75 - k * 0.08), (0.38, 0.05, 0.28), MAT["glass_dark"], bevel=0.03)
            g.rotation_euler = (0, -0.35, s * 0.55)
            parent(g, fr)
    fin = mesh_obj(prefix + "_fin", [(-11.5, -0.12, 1.2), (-14.8, -0.12, 1.0), (-17.2, -0.12, 5.2), (-15.4, -0.12, 5.3),
                                      (-11.5, 0.12, 1.2), (-14.8, 0.12, 1.0), (-17.2, 0.12, 5.2), (-15.4, 0.12, 5.3)],
                   [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], MAT["paint"])
    stab = []
    for s in (-1, 1):
        st = mesh_obj(f"{prefix}_stab{s}", [(-13.0, 0, 0.6), (-15.6, 0, 0.6), (-16.6, s * 4.6, 0.85), (-15.4, s * 4.6, 0.85),
                                            (-13.0, 0, 0.75), (-15.6, 0, 0.75), (-16.6, s * 4.6, 0.95), (-15.4, s * 4.6, 0.95)],
                      [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], MAT["paint"])
        stab.append(st)
    wings = []
    for s in (-1, 1):
        w = mesh_obj(f"{prefix}_wing{s}", [(4.5, 0, -0.9), (-2.5, 0, -0.9), (-6.5, s * 17.0, -0.3), (-3.8, s * 17.0, -0.3),
                                           (4.5, 0, -0.55), (-2.5, 0, -0.55), (-6.5, s * 17.0, -0.18), (-3.8, s * 17.0, -0.18)],
                     [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], MAT["metal"])
        wings.append(w)
        for k in range(2):  # engine intakes buried in the wing root
            e = prim(bpy.ops.mesh.primitive_cylinder_add, f"{prefix}_eng{s}{k}", (4.4, s * (2.2 + k * 1.1), -0.72), (0.38, 0.38, 0.25),
                     (0, math.pi / 2, 0), MAT["glass_dark"], vertices=24)
            wings.append(e)
    wins = []
    for k in range(16):
        x = -8.0 + k * 1.05
        for s in (-1, 1):
            wn = rounded_panel(f"{prefix}_win{k}{s}", (x, s * 1.43, 0.42), 0.42, 0.55, 0.06, win_r, MAT["glass_dark"])
            wins.append((x, wn))
    gearo = []
    if gear:
        for gx, gy in ((9.0, 0), (-1.2, -2.6), (-1.2, 2.6)):
            st = prim(bpy.ops.mesh.primitive_cylinder_add, f"{prefix}_strut{gx}{gy}", (gx, gy, -1.9), (0.1, 0.1, 0.6), mat=MAT["steel"])
            wh = prim(bpy.ops.mesh.primitive_cylinder_add, f"{prefix}_wheel{gx}{gy}", (gx, gy, -2.55), (0.48, 0.48, 0.22),
                      (math.pi / 2, 0, 0), MAT["tyre"], vertices=24)
            gearo += [st, wh]
    for o in (f1, b1, nose, tail):  # bake rotation/scale so object-space Z = world up (paint bands run along the body)
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    for o in (f1, nose, *wings, *gearo):
        parent(o, fr)
    for o in (b1, tail, fin, *stab):
        parent(o, bk)
    for x, wn in wins:
        parent(wn, fr if x > 0 else bk)
    rings = []
    if glow_ring:
        gm = emission(prefix + "_ring", (1.0, 0.75, 0.15), 0.0)
        for x, wn in wins:
            r = rounded_panel(wn.name + "_ring", (x, math.copysign(1.415, wn.location.y), 0.42), 0.62, 0.75, 0.03, win_r + 0.1, gm)
            parent(r, fr if x > 0 else bk)
            rings.append(r)
        return root, fr, bk, gm
    return root, fr, bk, None


# ---------------------------------------------------------------- sets
def world_color(top, bottom, strength=1.0):
    w = bpy.data.worlds.new("w")
    SC.world = w
    w.use_nodes = True
    nt = w.node_tree
    bgn = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    rp = nt.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].position = 0.45
    rp.color_ramp.elements[0].color = (*bottom, 1)
    rp.color_ramp.elements[1].position = 0.7
    rp.color_ramp.elements[1].color = (*top, 1)
    nt.links.new(sep.outputs["Z"], rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], bgn.inputs["Color"])
    bgn.inputs["Strength"].default_value = strength


def world_sky(sun_elev_deg=4.0, sun_rot_deg=200.0, strength=0.6):
    w = bpy.data.worlds.new("sky")
    SC.world = w
    w.use_nodes = True
    nt = w.node_tree
    bgn = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    for t in ("MULTIPLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
        try:
            sky.sky_type = t
            break
        except Exception:
            continue
    for attr, val in (("sun_elevation", math.radians(sun_elev_deg)), ("sun_rotation", math.radians(sun_rot_deg)), ("air_density", 1.4),
                      ("dust_density", 2.5)):
        try:
            setattr(sky, attr, val)
        except Exception:
            pass
    nt.links.new(sky.outputs["Color"], bgn.inputs["Color"])
    bgn.inputs["Strength"].default_value = strength


def light(kind, loc, energy, col=(1, 1, 1), size=1.0, rot=(0, 0, 0)):
    bpy.ops.object.light_add(type=kind, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.data.energy = energy
    o.data.color = col
    if kind == "AREA":
        o.data.size = size
    elif kind in ("POINT", "SPOT"):
        o.data.shadow_soft_size = size
    elif kind == "SUN":
        o.data.angle = math.radians(size)
    return o


def hangar(cx=0.0, cy=0.0, w=80, d=60):
    prim(bpy.ops.mesh.primitive_plane_add, "floor", (cx, cy, 0), (w / 2, d / 2, 1), mat=MAT["concrete"])
    for k in range(-4, 5):  # floor markings
        box(f"mark{k}", (cx + k * 8, cy, 0.005), (0.15, d * 0.8, 0.01), MAT["yellow"])
    for k in range(-4, 5):
        box(f"col{k}", (cx + k * 9, cy + d / 2 - 6, 9), (0.6, 0.6, 18), MAT["steel"])
        box(f"truss{k}", (cx + k * 9, cy, 18), (0.4, d, 0.6), MAT["steel"])
    box("backwall", (cx, cy + d / 2 - 5, 9), (w, 0.3, 18), MAT["concrete"])
    for k in (-1, 0, 1):  # big soft skylight fill so the hangar reads (not a black void)
        light("AREA", (cx + k * 25, cy, 17), 12000, (0.85, 0.9, 1.0), 20)
    for k in range(-3, 4):  # high bay lamps
        light("SPOT", (cx + k * 11, cy - 2, 16), 4000, (1.0, 0.92, 0.8), 0.6, (0, 0, 0)).data.spot_size = math.radians(85)
        prim(bpy.ops.mesh.primitive_cylinder_add, f"lamp{k}", (cx + k * 11, cy - 2, 16.3), (0.6, 0.6, 0.15), mat=MAT["light"])


def cabin(rows=8, win_r=0.12, seats=True, pitch=0.86):
    """Airliner cabin along +Y (nose at +Y). Returns cabin length and window list."""
    L = rows * pitch + 1.6
    R, cz = 2.1, 1.0
    shell = prim(bpy.ops.mesh.primitive_cylinder_add, "shell", (0, L / 2, cz), (R, R, L / 2 + 0.6), (math.pi / 2, 0, 0), MAT["cabin"],
                 smooth=True, vertices=64)
    shell.modifiers.new("solid", "SOLIDIFY").thickness = 0.05
    prim(bpy.ops.mesh.primitive_plane_add, "floor", (0, L / 2, 0), (1.95, L / 2 + 0.6, 1), mat=MAT["carpet"])
    box("aisle", (0, L / 2, 0.004), (0.55, L + 1.2, 0.008), pbr("aisle_m", (0.3, 0.08, 0.1), 0.9))
    box("strip", (0, L / 2, cz + R - 0.2), (0.35, L + 1.0, 0.02), MAT["light"])
    for s in (-1, 1):  # overhead bins
        b = box(f"bin{s}", (s * 1.45, L / 2, 2.35), (0.75, L + 1.0, 0.5), MAT["frame"], bevel=0.06)
        b.rotation_euler = (0, s * 0.35, 0)
    wins = []
    skym = sky_window_mat("skyview")
    frm = MAT["frame"]
    for k in range(rows):
        y = 0.55 + k * pitch
        for s in (-1, 1):
            x = s * 1.985
            fr = rounded_panel(f"wf{k}{s}", (x, y, 1.3), 0.42, 0.56, 0.05, win_r + 0.05, frm, rot=(0, 0, math.pi / 2))
            gl = rounded_panel(f"wg{k}{s}", (x - s * 0.026, y, 1.3), 0.3, 0.44, 0.01, win_r, skym, rot=(0, 0, math.pi / 2))
            wins.append((k, s, gl, fr))
    if seats:
        for k in range(rows):
            y = 0.25 + k * pitch
            for s in (-1, 1):
                xc = s * 1.18
                box(f"cush{k}{s}", (xc, y + 0.25, 0.45), (1.3, 0.5, 0.14), MAT["seat"], bevel=0.04)
                box(f"back{k}{s}", (xc, y, 0.85), (1.3, 0.12, 0.8), MAT["seat"], bevel=0.05)
                box(f"skirt{k}{s}", (xc, y + 0.45, 0.2), (1.3, 0.08, 0.4), MAT["seat"], bevel=0.02)
                for hx in (-0.62, 0.62):
                    box(f"arm{k}{s}{hx}", (xc + hx, y + 0.25, 0.62), (0.06, 0.45, 0.06), MAT["steel"], bevel=0.02)
    return L, wins


def camera(lens=28, fstop=2.8, focus_obj=None):
    bpy.ops.object.camera_add(location=(0, -10, 2))
    cam = bpy.context.active_object
    SC.camera = cam
    cam.data.lens = lens
    cam.data.sensor_width = 36
    cam.data.dof.use_dof = focus_obj is not None
    if focus_obj:
        cam.data.dof.focus_object = focus_obj
        cam.data.dof.aperture_fstop = fstop
    cam.data.clip_end = 3000
    aim = empty("aim")
    tr = cam.constraints.new("TRACK_TO")
    tr.target = aim
    tr.track_axis = "TRACK_NEGATIVE_Z"
    tr.up_axis = "UP_Y"
    return cam, aim


def shake(t, at, amp=0.08, dur=0.4):
    k = t - at
    if not 0 <= k < dur:
        return 0.0, 0.0, 0.0
    e = (1 - k / dur) ** 2
    return amp * e * math.sin(k * 90), amp * e * math.cos(k * 77), amp * e * math.sin(k * 60)


def animate_cam(cam, aim, fn, roll_fn=None):
    """fn(t) -> (cam_xyz, aim_xyz); roll in degrees via the camera's own Z rotation offset (constraint keeps aim)."""
    for f, t in frames():
        c, a = fn(t)
        key_loc_rot(cam, f, loc=c)
        key_loc_rot(aim, f, loc=a)
        if roll_fn:
            cam.delta_rotation_euler = (0, 0, math.radians(roll_fn(t)))
            cam.keyframe_insert("delta_rotation_euler", frame=f)


# ================================================================= scenes
def s0_hook():
    """Cabin, camera down the aisle at the passengers' faces; oxygen masks drop + red alarm on 'mistake'."""
    world_color((0.01, 0.01, 0.02), (0.02, 0.02, 0.03))
    L, wins = cabin(rows=8, win_r=0.14)
    mk = CUE["mistake"]
    cam, aim = camera(lens=24, fstop=2.2, focus_obj=None)
    focus = empty("focus", (0, L - 2.6, 1.3))
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = focus
    cam.data.dof.aperture_fstop = 2.0
    for k in range(8):
        for s in (-1, 1):
            if (k + (s > 0)) % 2 == 0 or k >= 6:
                i = (k * 2 + (s > 0)) % 5
                sprite(f"pax{k}{s}", f"s0_pax{i}", (s * (1.5 if (k % 2) else 0.9), 0.47 + k * 0.86, 0.12), 2.05, cam)
    cup_m, cord_m = MAT["yellow"], MAT["white"]
    for k in range(8):
        for s in (-1, 1):
            x, y = s * 1.2, 0.75 + k * 0.86
            cup = prim(bpy.ops.mesh.primitive_cylinder_add, f"cup{k}{s}", (x, y, 2.15), (0.09, 0.09, 0.06), mat=cup_m, vertices=16)
            cord = prim(bpy.ops.mesh.primitive_cylinder_add, f"cord{k}{s}", (x, y, 2.15), (0.006, 0.006, 0.01), mat=cord_m, vertices=6)
            for f, t in frames():
                k2 = t - (mk - 0.15) - k * 0.03
                drop = 0.0 if k2 <= 0 else 0.62 * min(1.0, (k2 / 0.25) ** 2) + 0.07 * spring(k2, 0.25, 1, 3, 3.5)
                key_loc_rot(cup, f, loc=(x, y, 2.15 - drop))
                key_loc_rot(cord, f, loc=(x, y, 2.15 - drop / 2), scale=(0.006, 0.006, max(0.01, drop / 2)))
    for k in range(4):
        light("AREA", (0, 1 + k * 2.2, 2.75), 60, (1.0, 0.9, 0.78), 1.2)
    alarm = light("AREA", (0, L - 1.5, 2.8), 0, (1.0, 0.05, 0.03), 2.5)
    for f, t in frames():
        alarm.data.energy = 0 if t < mk - 0.15 else 2500 * (0.5 + 0.5 * math.sin((t - mk) * 14))
        alarm.data.keyframe_insert("energy", frame=f)
    animate_cam(cam, aim, lambda t: ((0.25 + 0.1 * math.sin(t * 0.7), L + 0.35 - 0.6 * ease(t / 3.4), 1.62),
                                     (0.0, L - 6.0, 1.12)), roll_fn=lambda t: -3 + 3 * math.sin(t * 0.8) + 40 * shake(t, mk, 0.06, 0.5)[2])


EXPOSURE = {0: -1.3, 9: -1.0, 11: -1.0}


def s1_runway():
    world_sky(3.0, 250, 0.5)
    sun = light("SUN", (0, 0, 10), 3.5, (1.0, 0.62, 0.38), 2.0, (math.radians(87), 0, math.radians(-110)))
    _ = sun
    prim(bpy.ops.mesh.primitive_plane_add, "grass", (0, 0, 0), (1500, 1500, 1), mat=MAT["grass"])
    box("runway", (0, 0, 0.02), (2400, 46, 0.04), MAT["asphalt"])
    for k in range(-40, 40):
        box(f"dash{k}", (k * 30, 0, 0.045), (14, 0.9, 0.01), MAT["white"])
    for s in (-1, 1):
        box(f"edge{s}", (0, s * 21.5, 0.045), (2400, 0.5, 0.01), MAT["white"])
    box("terminal", (-160, 190, 9), (120, 40, 18), MAT["concrete"])
    box("tower", (-90, 175, 22), (8, 8, 44), MAT["concrete"])
    box("towercab", (-90, 175, 46), (12, 12, 5), pbr("tglass", (0.2, 0.35, 0.45), 0.1, 0.3))
    for k in range(5):
        box(f"hangar{k}", (60 + k * 70, 230, 12), (55, 45, 24), MAT["steel"])
    root, fr, bk, _ = comet("jet", (0, 0, 3.03))
    fs, lv = CUE["fast"], CUE["loved"]

    def jet_state(t):
        k = max(0.0, t - fs + 0.6)
        x = -95 + 4.0 * t + 0.5 * 7.0 * k * k
        v = 4.0 + 7.0 * k
        lift = max(0.0, v - 27.0)
        z = 3.03 + 0.18 * lift * lift
        pitch = min(math.radians(10), math.radians(0.9) * lift)
        return x, z, pitch
    for f, t in frames():
        x, z, p = jet_state(t)
        key_loc_rot(root, f, loc=(x, 0, z), rot=(0, -p, 0))
    cam, aim = camera(lens=30)
    for i, (x, y) in enumerate(((-82, -41), (-79.5, -40), (-77, -41.5))):  # near crowd (foreground)
        sprite(f"near{i}", f"s1_old{i}", (x, y, 0), 1.75, cam)
    for i in range(14):  # far crowd behind the runway fence
        sprite(f"far{i}", f"s1_old{i % 3}", (-120 + i * 9, 36 + (i % 2) * 1.5, 0), 1.75, cam)
    for k in range(30):
        box(f"fence{k}", (-130 + k * 5, 34, 0.6), (0.08, 0.08, 1.2), MAT["wood"])
    box("fencerail", (-55, 34, 1.0), (150, 0.06, 0.08), MAT["wood"])

    def cam_fn(t):
        x, z, _ = jet_state(t)
        return (-80 + 2.0 * t, -50 + 0.6 * t, 2.6 + 0.25 * t), (x * 0.7 - 30, 0, z * 0.6 + 1.0)
    animate_cam(cam, aim, cam_fn, roll_fn=lambda t: -2 + 1.5 * math.sin(t * 0.6))


def s2_square():
    world_color((0.01, 0.01, 0.015), (0.03, 0.03, 0.04))
    mats_ = MAT
    _ = mats_
    hangar()
    root, fr, bk, ring = comet("jet", (0, 0, 3.03), win_r=0.03, glow_ring=True)
    sq = CUE["square"]
    for f, t in frames():
        ring.node_tree.nodes["Emission"].inputs["Strength"].default_value = 0 if t < sq - 0.05 else 8 * (0.6 + 0.4 * math.sin(t * 12))
        ring.node_tree.nodes["Emission"].inputs["Strength"].keyframe_insert("default_value", frame=f)
    cam, aim = camera(lens=32)
    animate_cam(cam, aim, lambda t: ((12 - 8 * ease(t / 2.1), -17 + 9 * ease(t / 2.1), 3.8 - 0.3 * ease(t / 2.1)),
                                     (1.5 - 1.0 * ease(t / 2.1), 1.4, 3.45)), roll_fn=lambda t: -4 * ease(t / 2.1))


def cloud_sprite(name, k, loc, size, cam, dark=False):
    o = sprite(name, f"clouds/cloud{k}.png", loc, size, cam)
    if dark:
        nt = o.data.materials[0].node_tree
        nt.nodes["Emission"].inputs["Strength"].default_value = 0.0
        p = nt.nodes["Principled BSDF"]
        mul = nt.nodes.new("ShaderNodeMixRGB")
        mul.blend_type = "MULTIPLY"
        mul.inputs["Fac"].default_value = 1
        mul.inputs["Color2"].default_value = (0.08, 0.08, 0.09, 1)
        nt.links.new(nt.nodes["Image Texture"].outputs["Color"], mul.inputs["Color1"])
        nt.links.new(mul.outputs[0], p.inputs["Base Color"])
    return o


def s3_breakup():
    br, gr, nb = CUE["broke"], CUE["grounded"], CUE["nobody"]
    cut = gr - 0.25
    world_color((0.01, 0.015, 0.05), (0.08, 0.1, 0.22), 1.0)
    light("SUN", (0, 0, 50), 1.2, (0.6, 0.7, 1.0), 3, (math.radians(50), 0, math.radians(30)))
    root, fr, bk, _ = comet("jet", (0, 0, 300), gear=False)
    cam, aim = camera(lens=30)
    rnd = random.Random(3)
    clouds = []
    for i in range(40):
        c = cloud_sprite(f"cl{i}", i % 3, (0, 0, 0), rnd.uniform(14, 30), cam)
        yy = rnd.choice((rnd.uniform(15, 160), rnd.uniform(-160, -70)))  # never between the camera and the jet
        clouds.append((c, rnd.uniform(-200, 200), yy, rnd.uniform(275, 330)))
    for f, t in frames():
        for c, x0, y0, z0 in clouds:  # clouds rush past (the jet flies at ~200 m/s; we keep the jet, move the sky)
            x = (x0 - t * 70 + 200) % 400 - 200
            key_loc_rot(c, f, loc=(x, y0, z0 - 8))
        k = t - br
        if k < 0:
            key_loc_rot(fr, f, loc=(0, 0, 0), rot=(0, 0, 0))
            key_loc_rot(bk, f, loc=(0, 0, 0), rot=(0, 0, 0))
        else:  # two rigid bodies: separate, tumble, fall (no people shown)
            key_loc_rot(fr, f, loc=(3.5 * k, 0.5 * k, -1.0 * k - 2.2 * k * k), rot=(0.1 * k, 0.28 * k + 0.08 * k * k, 0))
            key_loc_rot(bk, f, loc=(-3.5 * k, -0.4 * k, -0.6 * k - 2.0 * k * k), rot=(0.5 * k, -0.35 * k, 0.1 * k))
        key_loc_rot(root, f, loc=(0, 0, 300 + 0.3 * math.sin(t * 2)))
    deb = []
    for i in range(36):  # debris with drag + gravity
        d = box(f"deb{i}", (0, 0, 300), (rnd.uniform(0.1, 0.4), rnd.uniform(0.05, 0.2), rnd.uniform(0.1, 0.3)), MAT["metal"])
        ang, el, sp = rnd.uniform(0, 2 * math.pi), rnd.uniform(-0.5, 1.0), rnd.uniform(6, 18)
        deb.append((d, math.cos(ang) * math.cos(el) * sp, math.sin(ang) * math.cos(el) * sp, math.sin(el) * sp, rnd.uniform(-8, 8)))
    for f, t in frames():
        k = max(0.0, t - br)
        for d, vx, vy, vz, w in deb:
            dr = 1.6
            e = (1 - math.exp(-dr * k)) / dr
            key_loc_rot(d, f, loc=(vx * e, vy * e, 300 + vz * e - 4.9 * k * k * 0.6), rot=(w * k, w * 0.7 * k, w * 0.3 * k),
                        scale=None if k > 0 else (0.001, 0.001, 0.001))
            if k > 0 and f == int(br * FPS) + 2:
                pass
    flash = light("POINT", (0, 0, 300), 0, (1.0, 0.55, 0.2), 1.0)
    for f, t in frames():
        k = t - br
        flash.data.energy = 0 if k < 0 else 2.0e6 * math.exp(-k * 5)
        flash.data.keyframe_insert("energy", frame=f)
    smoke = []
    for i in range(0):
        s_ = cloud_sprite(f"smoke{i}", i % 3, (0, 0, 300), 6, cam, dark=True)
        smoke.append(s_)
    for f, t in frames():
        k = t - br
        for i, s_ in enumerate(smoke):
            kk = k - i * 0.08
            sc_ = 0.001 if kk <= 0 else 0.3 + 1.6 * kk
            key_loc_rot(s_, f, loc=(-1 + i * 0.3, 0, 300 + 1.5 * max(0, kk) - 3), scale=(sc_, sc_, sc_))
    # ---- grounded: parked jets in a hangar 3 km away, puzzled engineers
    HX = 3000
    world_hangar = (HX, 0)
    hangar(HX, 0, 120, 80)
    for i, (x, y) in enumerate(((HX - 6, 14), (HX + 30, 26), (HX - 40, 30))):
        comet(f"park{i}", (x, y, 3.03))
    q = emission("qmark", (1.0, 0.8, 0.2), 6)
    marks = []
    for i, x in enumerate((HX - 1.7, HX + 1.7)):
        sprite(f"eng{i}", f"s3_eng{i}", (x, -4 + i * 0.8, 0), 1.85, cam)
        m_ = text3d(f"q{i}", "?", (x, -4 + i * 0.8, 2.05), 1.0, q, cam)
        marks.append((m_, i))
    for f, t in frames():
        for m_, i in marks:
            s_ = 0.001 if t < nb + i * 0.15 else max(0.001, min(1.2, (t - nb - i * 0.15) / 0.25)) + 0.15 * spring(t, nb + i * 0.15 + 0.25, 1, 3, 4)
            key_loc_rot(m_, f, scale=(s_, s_, s_))

    def cam_fn(t):
        if t < cut:
            a = 0.25 * math.sin(t * 0.45)
            dx, dy, dz = shake(t, br, 1.2, 0.6)
            return (30 * math.sin(a) + dx, -42 * math.cos(a) + dy, 304 + dz), (0, 0, 300.5)
        k = t - cut
        return (HX + 1.0 - 1.0 * ease(k / 2.5), -12.5 + 2.0 * ease(k / 2.5), 2.4), (HX, 2, 2.0)
    animate_cam(cam, aim, cam_fn, roll_fn=lambda t: (5 * math.sin(t * 0.5)) if t < cut else 1.5)
    _ = world_hangar


def s4_tank():
    world_color((0.01, 0.01, 0.015), (0.03, 0.03, 0.04))
    hangar(0, 0, 120, 80)
    tk, up = CUE["tank"], CUE["up"]
    glass = see_through("tankglass", (0.75, 0.88, 1.0), 0.12, 0.05)
    W2, D2, Hh = 19, 3.4, 7.0
    for nm, c, sz in (("gF", (0, -D2, Hh / 2), (2 * W2, 0.12, Hh)), ("gB", (0, D2, Hh / 2), (2 * W2, 0.12, Hh)),
                      ("gL", (-W2, 0, Hh / 2), (0.12, 2 * D2, Hh)), ("gR", (W2, 0, Hh / 2), (0.12, 2 * D2, Hh))):
        box(nm, c, sz, glass)
    for x in (-W2, W2):
        for y in (-D2, D2):
            box(f"tp{x}{y}", (x, y, Hh / 2), (0.25, 0.25, Hh), MAT["steel"])
    water = see_through("water", (0.1, 0.45, 0.85), 0.5, 0.06, glow=0.6)
    wat = box("water", (0, 0, 0.01), (2 * W2 - 0.2, 2 * D2 - 0.2, 0.02), water)
    root, fr, bk, _ = comet("jet", (1.5, 0, 3.4), gear=False)
    pump = prim(bpy.ops.mesh.primitive_cylinder_add, "pump", (W2 + 4, -2, 2.2), (0.9, 0.9, 2.2), mat=MAT["red"], vertices=32)
    piston = prim(bpy.ops.mesh.primitive_cylinder_add, "piston", (W2 + 4, -2, 5.2), (0.35, 0.35, 1.0), mat=MAT["steel"], vertices=24)
    pipe = box("pipe", (W2 + 2, -2, 1.2), (4, 0.3, 0.3), MAT["steel"])
    _ = (pump, pipe)
    for f, t in frames():
        pk = max(0.0, t - up + 0.3)
        cyc = math.sin(pk * 2 * math.pi * (1.0 + 0.6 * min(1.0, pk / 3))) if pk > 0 else 0.0
        fill = ease((t - tk + 0.8) / 1.0)
        lvl = (6.4 + 0.18 * cyc) * fill
        key_loc_rot(wat, f, loc=(0, 0, max(0.01, lvl / 2)), scale=((2 * W2 - 0.2) / 2, (2 * D2 - 0.2) / 2, max(0.01, lvl / 2)))
        key_loc_rot(piston, f, loc=(W2 + 4, -2, 5.2 + 0.8 * cyc))
        key_loc_rot(root, f, scale=(1, 1 + 0.012 * cyc, 1 + 0.012 * cyc))
    cam, aim = camera(lens=28)
    sprite("counter", "s4_counter", (-8, -11, 2.0), 2.4, cam)
    for x, y in ((-8.3, -11.0), (-7.7, -11.0)):
        box(f"stand{x}", (x, y, 1.0), (0.1, 0.1, 2.0), MAT["steel"])
    sprite("eng0", "s4_eng0", (-8, -8, 0), 1.85, cam)
    sprite("eng1", "s4_eng1", (8, -8.5, 0), 1.85, cam)
    animate_cam(cam, aim, lambda t: ((-30 + 30 * ease(t / 9.8), -46 + 4 * ease(t / 9.8), 10 - 2.5 * ease(t / 9.8)),
                                     (-4 + 6 * ease(t / 9.8), 0, 3.2)), roll_fn=lambda t: -2)


def s5_crack():
    ck, co = CUE["crack"], CUE["corner"]
    world_color((0.005, 0.008, 0.02), (0.02, 0.03, 0.07))
    light("AREA", (4, 8, 4), 900, (0.75, 0.82, 1.0), 6)
    light("AREA", (-3, 6, -2), 200, (1.0, 0.8, 0.6), 4)
    root, fr, bk, _ = comet("jet", (0, 0, 0), win_r=0.03, gear=False)
    wx = -8.0 + 9 * 1.05  # the window in focus (k=9)
    for i in range(-14, 15):  # rivet rows around it
        for z in (1.15, -0.35):
            y = math.sqrt(max(0.0, 1.5 ** 2 - z * z)) + 0.005
            prim(bpy.ops.mesh.primitive_uv_sphere_add, f"riv{i}{z}", (wx + i * 0.16, y, z), (0.018, 0.018, 0.018), mat=MAT["steel"],
                 segments=8, ring_count=6)
    pts = []
    rnd = random.Random(9)
    x, z = wx + 0.21, 0.42 + 0.275
    for k in range(22):
        y = math.sqrt(max(0.0, 1.5 ** 2 - z * z)) + 0.012
        pts.append((x, y, z))
        x += 0.045
        z += 0.03 + rnd.uniform(-0.03, 0.03)
    cu = bpy.data.curves.new("crack", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    cu.bevel_depth = 0.006
    cobj = bpy.data.objects.new("crack", cu)
    link(cobj)
    cobj.data.materials.append(emission("crackm", (1.0, 0.35, 0.08), 12))
    for f, t in frames():
        cu.bevel_factor_end = max(0.0, min(1.0, (t - ck) / 1.2))
        cu.keyframe_insert("bevel_factor_end", frame=f)
    hot = light("POINT", (wx + 0.25, 1.7, 0.75), 0, (1.0, 0.35, 0.1), 0.1)
    for f, t in frames():
        hot.data.energy = 0 if t < ck else 4 + 2 * math.sin(t * 20)
        hot.data.keyframe_insert("energy", frame=f)
    cam, aim = camera(lens=30)

    def cam_fn(t):
        z = ease((t - ck + 0.15) / 0.35)
        dx, dy, dz = shake(t, ck, 0.05, 0.5)
        return ((wx + 2.6 - 1.6 * z + dx, 4.6 - 1.5 * z + dy, 1.3 - 0.2 * z + dz), (wx + 0.15 + 0.1 * z, 1.45, 0.5 + 0.1 * z))
    animate_cam(cam, aim, cam_fn, roll_fn=lambda t: -6 * ease((t - ck + 0.15) / 0.35) + 30 * shake(t, ck, 0.05, 0.5)[2])
    _ = co


def s6_balloon():
    pr, bl = CUE["pressurized"], CUE["balloon"]
    world_color((0.01, 0.01, 0.015), (0.03, 0.03, 0.04))
    hangar(0, 0, 120, 80)
    root, fr, bk, _ = comet("jet", (0, 0, 3.03))
    fus = [bpy.data.objects[n] for n in ("jet_fusF", "jet_fusB", "jet_nose", "jet_tail")]
    arrow_m = emission("arrow", (1.0, 0.25, 0.15), 5)
    arrows = []
    for k in range(9):
        for s in (-1, 1):
            a = prim(bpy.ops.mesh.primitive_cone_add, f"arr{k}{s}", (-8 + k * 2, 0, 3.03 + s * 2.1), mat=arrow_m,
                     rot=(0 if s > 0 else math.pi, 0, 0), radius1=0.22, radius2=0, depth=0.45)
            arrows.append((a, s, k))
    for f, t in frames():
        infl = ease((t - pr + 0.2) / 1.2)
        g = 1 + 0.06 * infl + 0.012 * infl * math.sin(t * 5)
        for o in fus:
            sx = o.scale.copy()
            key_loc_rot(o, f, scale=(sx[0], sx[1], sx[2]) if False else None)
        key_loc_rot(fr, f, scale=(1, g, g))
        key_loc_rot(bk, f, scale=(1, g, g))
        for a, s, k in arrows:
            off = (2.0 + 0.5 * infl + 0.15 * math.sin(t * 6 + k)) * g
            sc_ = max(0.001, infl)
            key_loc_rot(a, f, loc=(-8 + k * 2, 0, 3.03 + s * off), scale=(sc_, sc_, sc_))
    bal = prim(bpy.ops.mesh.primitive_uv_sphere_add, "balloon", (9.5, -17, 3.2), mat=pbr("balm", (0.85, 0.05, 0.1), 0.12), smooth=True,
               segments=32, ring_count=16)
    string = prim(bpy.ops.mesh.primitive_cylinder_add, "string", (9.5, -17, 1.1), (0.01, 0.01, 1.1), mat=MAT["white"], vertices=6)
    _ = string
    for f, t in frames():
        k = ease((t - bl + 0.5) / 0.6)
        r = max(0.001, (0.9 + 0.12 * spring(t, bl + 0.1, 1, 2.5, 3)) * k)
        key_loc_rot(bal, f, loc=(9.5, -17, 2.2 + r * 1.1), scale=(r, r, r * 1.15))
    cam, aim = camera(lens=28)
    sprite("kid", "s6_kid", (8.0, -18.0, 0), 1.6, cam)
    animate_cam(cam, aim, lambda t: ((12 - 4 * ease(t / 4.2), -30 + 3 * ease(t / 4.2), 5.0), (4 + 2 * ease(t / 4.2), -2, 2.8)),
                roll_fn=lambda t: 2 * math.sin(t * 0.7))


def stress_lines(sharp, hole_w, hole_h, heat_fn, tear_fn):
    n = 15
    objs = []
    for i in range(n):
        v0 = -1.75 + i * (3.5 / (n - 1))
        pts = []
        for k in range(81):
            u = -1.9 + k * (3.8 / 80)
            v = v0
            ah = hole_h / 2 + 0.06
            if abs(v0) < ah + 0.4:
                if sharp:
                    span = hole_w / 2 + 0.13
                    g = max(0.0, 1 - max(0.0, abs(u) - span + 0.13) / 0.13) if abs(u) < span else 0.0
                    target = math.copysign(ah + (abs(v0) / (ah + 0.4)) * 0.1, v0 if v0 != 0 else 1)
                else:
                    g = math.exp(-(u / (hole_w * 0.85)) ** 2)
                    target = math.copysign(ah + (abs(v0) / (ah + 0.4)) * 0.4, v0 if v0 != 0 else 1)
                v = v0 + (target - v0) * g
            pts.append((u, -0.08, v + 2.0))
        cu = bpy.data.curves.new(f"line{i}", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for j, p in enumerate(pts):
            sp.points[j].co = (*p, 1)
        cu.bevel_depth = 0.012
        o = bpy.data.objects.new(f"line{i}", cu)
        link(o)
        dense = abs(v0) < hole_h / 2 + 0.4
        col = (1.0, 0.25, 0.1) if (sharp and dense) else ((0.3, 1.0, 0.5) if not sharp else (0.4, 0.6, 1.0))
        m, nt, out = new_mat(f"lm{i}")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*col, 1)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        wv = nt.nodes.new("ShaderNodeTexWave")
        wv.wave_type = "BANDS"
        wv.bands_direction = "X"
        wv.inputs["Scale"].default_value = 3.0
        nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMath")
        mr.operation = "MULTIPLY"
        mr.inputs[1].default_value = 6.0
        nt.links.new(wv.outputs["Fac"], mr.inputs[0])
        nt.links.new(mr.outputs[0], em.inputs["Strength"])
        nt.links.new(em.outputs[0], out.inputs["Surface"])
        o.data.materials.append(m)
        for f, t in frames():
            mp.inputs["Location"].default_value = (-t * 0.6, 0, 0)
            mp.inputs["Location"].keyframe_insert("default_value", frame=f)
        objs.append(o)
    return objs


def plate_scene(sharp):
    world_color((0.005, 0.005, 0.01), (0.015, 0.015, 0.025))
    prim(bpy.ops.mesh.primitive_plane_add, "studio", (0, 0, 0), (30, 30, 1), mat=pbr("studiof", (0.02, 0.02, 0.025), 0.25))
    hole_w, hole_h, r = (1.1, 1.35, 0.03) if sharp else (1.1, 1.35, 0.45)
    plate = box("plate", (0, 0, 2.0), (4.0, 0.1, 4.0), noisy("brushed", (0.32, 0.34, 0.38), (0.45, 0.47, 0.52), 60, 0.35, 0.02, metal=0.9))
    cutter = rounded_panel("cutter", (0, 0, 2.0), hole_w, hole_h, 0.6, r, None)
    bo = plate.modifiers.new("hole", "BOOLEAN")
    bo.object = cutter
    bo.operation = "DIFFERENCE"
    cutter.hide_render = True
    cutter.hide_viewport = True
    light("AREA", (2.5, -4, 4.5), 500, (0.8, 0.85, 1.0), 4)
    light("AREA", (-3, -2, 1), 120, (1.0, 0.8, 0.6), 3)
    if sharp:
        st, pt, ti, tr = CUE["stress"], CUE["point"], CUE["tired"], CUE["tears"]
        heat = lambda t: ease((t - pt + 0.8) / 0.6)  # noqa: E731
        tear = lambda t: max(0.0, min(1.0, (t - tr) / 0.5))  # noqa: E731
    else:
        heat = lambda t: 0.0  # noqa: E731
        tear = lambda t: 0.0  # noqa: E731
    stress_lines(sharp, hole_w, hole_h, heat, tear)
    if sharp:
        gm = emission("hot", (1.0, 0.18, 0.05), 0)
        for su in (-1, 1):
            for sv in (-1, 1):
                prim(bpy.ops.mesh.primitive_uv_sphere_add, f"hot{su}{sv}", (su * hole_w / 2, -0.07, 2.0 + sv * hole_h / 2), (0.07, 0.07, 0.07),
                     mat=gm, segments=16, ring_count=8)
                pl = light("POINT", (su * hole_w / 2, -0.4, 2.0 + sv * hole_h / 2), 0, (1.0, 0.25, 0.08), 0.05)
                for f, t in frames():
                    pl.data.energy = 25 + 140 * heat(t) * (0.7 + 0.3 * math.sin(t * 8))
                    pl.data.keyframe_insert("energy", frame=f)
        en = gm.node_tree.nodes["Emission"].inputs["Strength"]
        for f, t in frames():
            en.default_value = 4 + 30 * heat(t) * (0.7 + 0.3 * math.sin(t * 8))
            en.keyframe_insert("default_value", frame=f)
        rnd = random.Random(4)
        pts = []
        u, v = hole_w / 2, hole_h / 2
        for k in range(16):
            pts.append((u, -0.075, 2.0 + v))
            u += 0.07
            v += 0.05 + rnd.uniform(-0.04, 0.04)
        cu = bpy.data.curves.new("tear", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for j, p in enumerate(pts):
            sp.points[j].co = (*p, 1)
        cu.bevel_depth = 0.014
        tobj = bpy.data.objects.new("tear", cu)
        link(tobj)
        tobj.data.materials.append(emission("tearm", (1.0, 0.5, 0.15), 15))
        for f, t in frames():
            cu.bevel_factor_end = max(0.0001, tear(t))
            cu.keyframe_insert("bevel_factor_end", frame=f)
    else:
        ev = CUE["evenly"]
        hm = emission("halo", (0.3, 1.0, 0.5), 0)
        for i in range(10):
            a = i / 10 * 2 * math.pi
            prim(bpy.ops.mesh.primitive_uv_sphere_add, f"halo{i}", (math.cos(a) * 1.05, -0.07, 2.0 + math.sin(a) * 1.2), (0.05, 0.05, 0.05),
                 mat=hm, segments=12, ring_count=6)
        en = hm.node_tree.nodes["Emission"].inputs["Strength"]
        for f, t in frames():
            en.default_value = 25 * ease((t - ev + 0.3) / 0.4)
            en.keyframe_insert("default_value", frame=f)
    cam, aim = camera(lens=35)
    tr_ = CUE["tears"] if sharp else -10

    def cam_fn(t):
        yaw = (0.42 if sharp else -0.42) * math.cos(t * 0.5)
        R = 7.2 - 1.0 * ease(t / 4)
        dx, dy, dz = shake(t, tr_, 0.1, 0.5)
        return (R * math.sin(yaw) + dx, -R * math.cos(yaw) + dy, 3.0 + dz), (0, 0, 2.75)
    animate_cam(cam, aim, cam_fn, roll_fn=lambda t: 40 * shake(t, tr_, 0.1, 0.5)[2])


def s7_sharp():
    plate_scene(True)


def s8_round():
    plate_scene(False)


def s9_today():
    world_color((0.01, 0.01, 0.02), (0.02, 0.02, 0.03))
    L, wins = cabin(rows=7, win_r=0.14, seats=False)
    rd = CUE["rounded"]
    k0, s0 = 3, -1
    wy = 0.55 + k0 * 0.86
    ring = emission("ring", (1.0, 0.75, 0.15), 0.6)
    frm = bpy.data.objects[f"wf{k0}{s0}"]  # this window's own frame lights up gold on "rounded"
    frm.data.materials.clear()
    frm.data.materials.append(ring)
    en = ring.node_tree.nodes["Emission"].inputs["Strength"]
    for f, t in frames():
        en.default_value = 0.6 if t < rd - 0.1 else 9 * (0.7 + 0.3 * math.sin(t * 8))
        en.keyframe_insert("default_value", frame=f)
    for k in range(3):
        light("AREA", (0, 1 + k * 2.2, 2.75), 60, (1.0, 0.9, 0.78), 1.2)
    cam, aim = camera(lens=26)
    kid_y = wy + 0.95
    sprite("kid", "s9_kid", (-1.2, kid_y, 0.05), 1.8, cam)
    animate_cam(cam, aim, lambda t: ((0.7 + 0.2 * ease(t / 3), wy - 2.4 + 0.5 * ease(t / 3), 1.45), (-1.8, wy + 0.2, 1.25)),
                roll_fn=lambda t: 3 * math.sin(t * 0.6))
    _ = (wins, s0)


def s11_vote():
    world_color((0.01, 0.01, 0.02), (0.02, 0.02, 0.03))
    L, wins = cabin(rows=5, win_r=0.14)
    for k in range(4):
        light("AREA", (0, 1 + k * 1.8, 2.75), 60, (1.0, 0.9, 0.78), 1.2)
    cam, aim = camera(lens=26)
    y = 0.25 + 4 * 0.86 + 0.22
    sprite("a", "s11_a", (-1.55, y, 0.12), 2.05, cam)
    sprite("b", "s11_b", (-0.85, y, 0.12), 2.05, cam)
    animate_cam(cam, aim, lambda t: ((-0.4 + 0.3 * math.sin(t * 0.8), L + 0.3 - 0.3 * ease(t / 3), 1.55), (-1.2, y, 1.25)),
                roll_fn=lambda t: -2)
    _ = wins


SCENES = {0: s0_hook, 1: s1_runway, 2: s2_square, 3: s3_breakup, 4: s4_tank, 5: s5_crack, 6: s6_balloon, 7: s7_sharp, 8: s8_round,
          9: s9_today, 11: s11_vote}


def setup_render():
    eng = "CYCLES" if ENGINE == "CYCLES" else None
    if eng is None:
        for e in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
            try:
                SC.render.engine = e
                break
            except Exception:
                continue
        SC.eevee.taa_render_samples = SAMPLES
        for attr in ("use_raytracing", "use_shadows", "use_gtao", "use_bloom", "use_soft_shadows"):
            try:
                setattr(SC.eevee, attr, True)
            except Exception:
                pass
    else:
        SC.render.engine = "CYCLES"
        SC.cycles.samples = SAMPLES
        SC.cycles.use_denoising = True
        SC.cycles.max_bounces = 6
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
    SC.view_settings.view_transform = "AgX"
    SC.view_settings.exposure = EXPOSURE.get(SCENE, 0.0)
    try:
        SC.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    if OUTFMT == "MP4":
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


if __name__ == "__main__":
    mats()
    SCENES[SCENE]()
    setup_render()
    bpy.ops.render.render(animation=True)
