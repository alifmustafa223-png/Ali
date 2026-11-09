"""Blender test shot for The DailyMind: toon character billboard in a lit 3D set + rigid-body ball + camera move.
Run: blender -b -P test_scene.py -- out_prefix [engine] [frame_start] [frame_end]
"""
import math
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/tmp/test_"
ENGINE = argv[1] if len(argv) > 1 else "CYCLES"
F0 = int(argv[2]) if len(argv) > 2 else 1
F1 = int(argv[3]) if len(argv) > 3 else 90
HERE = os.path.dirname(os.path.abspath(__file__))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.fps = 30
sc.frame_start, sc.frame_end = 1, 90


def mat(name, build):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    sh = build(nt)
    nt.links.new(sh.outputs[0], out.inputs["Surface"])
    return m


def principled(nt, col, rough=0.6):
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    return p


def wood(nt, base=(0.32, 0.18, 0.08), planks=True):
    p = principled(nt, base, 0.55)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1, 6, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 3.0
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 3.0
    nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (base[0] * 0.55, base[1] * 0.55, base[2] * 0.55, 1)
    ramp.color_ramp.elements[1].color = (base[0] * 1.35, base[1] * 1.3, base[2] * 1.2, 1)
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    col_out = ramp.outputs["Color"]
    if planks:
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Brick Width"].default_value = 2.4
        br.inputs["Row Height"].default_value = 0.22
        br.inputs["Mortar Size"].default_value = 0.012
        br.inputs["Color1"].default_value = (1, 1, 1, 1)
        br.inputs["Color2"].default_value = (0.8, 0.8, 0.8, 1)
        br.inputs["Mortar"].default_value = (0.05, 0.05, 0.05, 1)
        nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs["Fac"].default_value = 1.0
        nt.links.new(col_out, mix.inputs["Color1"])
        nt.links.new(br.outputs["Color"], mix.inputs["Color2"])
        col_out = mix.outputs["Color"]
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.4
        nt.links.new(br.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], p.inputs["Normal"])
    nt.links.new(col_out, p.inputs["Base Color"])
    return p


def emit(nt, col, strength):
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1)
    e.inputs["Strength"].default_value = strength
    return e


M_DECK = mat("deck", lambda nt: wood(nt, (0.36, 0.2, 0.09)))
M_POST = mat("post", lambda nt: wood(nt, (0.42, 0.26, 0.12), planks=False))
M_GRASS = mat("grass", lambda nt: principled(nt, (0.05, 0.16, 0.06), 0.9))
M_BANNER = mat("banner", lambda nt: principled(nt, (0.85, 0.82, 0.76), 0.85))
M_RED = mat("red", lambda nt: principled(nt, (0.6, 0.04, 0.04), 0.5))
M_BULB = mat("bulb", lambda nt: emit(nt, (1.0, 0.8, 0.45), 18))
M_ROOF = mat("roof", lambda nt: principled(nt, (0.45, 0.47, 0.52), 0.35))
M_BALL = mat("ball", lambda nt: principled(nt, (0.92, 0.92, 0.92), 0.4))


def add(obj_op, name, loc, scale=(1, 1, 1), m=None, rot=(0, 0, 0)):
    obj_op(location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    if m:
        o.data.materials.append(m)
    return o


# deck, ground, railing, roof beams
deck = add(bpy.ops.mesh.primitive_plane_add, "deck", (0, 0, 0), (4, 3, 1), M_DECK)
add(bpy.ops.mesh.primitive_plane_add, "grass", (0, 0, -0.6), (60, 60, 1), M_GRASS)
for x in (-3.8, -1.3, 1.3, 3.8):
    add(bpy.ops.mesh.primitive_cube_add, f"post{x}", (x, 2.8, 0.6), (0.07, 0.07, 0.6), M_POST)
for z in (0.5, 1.05):
    add(bpy.ops.mesh.primitive_cube_add, f"rail{z}", (0, 2.8, z), (3.9, 0.04, 0.05), M_POST)
for x in (-3.8, 3.8):
    add(bpy.ops.mesh.primitive_cube_add, f"roofpost{x}", (x, -2.5, 1.7), (0.09, 0.09, 1.7), M_POST)
    add(bpy.ops.mesh.primitive_cube_add, f"roofpostb{x}", (x, 2.8, 1.7), (0.09, 0.09, 1.7), M_POST)
for y in (-2.5, -0.8, 1.0, 2.8):
    add(bpy.ops.mesh.primitive_cube_add, f"beam{y}", (0, y, 3.4), (4.0, 0.08, 0.1), M_POST)
add(bpy.ops.mesh.primitive_plane_add, "roof", (0, 0.15, 3.55), (4.1, 2.8, 1), M_ROOF)
# banner with the channel name
add(bpy.ops.mesh.primitive_plane_add, "banner", (0, 2.75, 2.25), (2.6, 0.45, 1), M_BANNER, rot=(math.pi / 2, 0, 0))
bpy.ops.object.text_add(location=(0, 2.7, 2.08), rotation=(math.pi / 2, 0, 0))
txt = bpy.context.active_object
txt.data.body = "THE DAILYMIND"
txt.data.align_x = "CENTER"
txt.data.size = 0.55
txt.data.extrude = 0.01
txt.data.materials.append(M_RED)
# string lights: catenary of glowing bulbs + a few real point lights
for side_y in (-2.4, 2.6):
    for i in range(15):
        u = i / 14
        x = -3.8 + 7.6 * u
        z = 3.1 - 0.45 * math.sin(math.pi * u)
        add(bpy.ops.mesh.primitive_uv_sphere_add, f"bulb{side_y}{i}", (x, side_y, z), (0.05, 0.05, 0.065), M_BULB)
for x in (-2.5, 0, 2.5):
    bpy.ops.object.light_add(type="POINT", location=(x, 0.1, 2.75))
    bpy.context.active_object.data.energy = 140
    bpy.context.active_object.data.color = (1.0, 0.75, 0.45)
    bpy.context.active_object.data.shadow_soft_size = 0.3
bpy.ops.object.light_add(type="AREA", location=(-3, -4, 4))
key = bpy.context.active_object
key.data.energy = 600
key.data.size = 3
key.data.color = (0.6, 0.7, 1.0)
key.rotation_euler = (math.radians(55), 0, math.radians(-35))
# barrel + crates
add(bpy.ops.mesh.primitive_cylinder_add, "barrel", (2.4, 1.6, 0.45), (0.38, 0.38, 0.45), M_POST)
add(bpy.ops.mesh.primitive_cube_add, "crate", (-2.6, 1.8, 0.35), (0.35, 0.35, 0.35), M_POST)
add(bpy.ops.mesh.primitive_cube_add, "crate2", (-2.0, 2.1, 0.25), (0.25, 0.25, 0.25), M_POST)

# toon character billboards (alpha-cut image planes), switching pose on the ball's first bounce
def toon_plane(name, img, loc):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(HERE, img))
    tex.interpolation = "Cubic"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.9
    for attr, val in (("blend_method", "CLIP"), ("shadow_method", "CLIP"), ("surface_render_method", "DITHERED")):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    bpy.ops.mesh.primitive_plane_add(location=loc, rotation=(math.pi / 2, 0, 0))
    o = bpy.context.active_object
    o.name = name
    o.scale = (0.6, 0.9, 1)  # 600x900 px image -> 1.2 x 1.8 m
    o.data.materials.append(m)
    return o


g1 = toon_plane("guy_idle", "guy_idle.png", (0, 0.6, 0.9))
g2 = toon_plane("guy_wow", "guy_wow.png", (0, 0.6, 0.9))
HIT = 34
for o, vis in ((g1, [(1, False), (HIT, True)]), (g2, [(1, True), (HIT, False)])):
    for f, hide in vis:
        o.hide_render = hide
        o.keyframe_insert("hide_render", frame=f)
        o.hide_viewport = hide
        o.keyframe_insert("hide_viewport", frame=f)

# rigid-body football dropping in, bouncing and rolling
bpy.ops.mesh.primitive_uv_sphere_add(location=(0.9, -0.2, 2.6), radius=0.17, segments=32, ring_count=16)
ball = bpy.context.active_object
ball.name = "ball"
ball.data.materials.append(M_BALL)
bpy.ops.object.shade_smooth()
bpy.ops.rigidbody.world_add()
sc.rigidbody_world.point_cache.frame_end = 120
bpy.context.view_layer.objects.active = ball
bpy.ops.rigidbody.object_add()
ball.rigid_body.restitution = 0.75
ball.rigid_body.friction = 0.6
ball.rigid_body.mass = 0.43
ball.rotation_euler = (0.3, 0.6, 0)
for o, rest in ((deck, 0.6),):
    bpy.context.view_layer.objects.active = o
    bpy.ops.rigidbody.object_add()
    o.rigid_body.type = "PASSIVE"
    o.rigid_body.restitution = rest
# tilted hidden ramp to kick the ball sideways on the first bounce
bpy.ops.mesh.primitive_plane_add(location=(0.9, -0.2, 0.02), rotation=(0, math.radians(-14), 0))
ramp = bpy.context.active_object
ramp.scale = (0.3, 0.3, 1)
ramp.hide_render = True
bpy.ops.rigidbody.object_add()
ramp.rigid_body.type = "PASSIVE"
ramp.rigid_body.restitution = 0.7

# camera: slow dolly-in with a slight orbit, depth of field on the character
bpy.ops.object.empty_add(location=(0, 0.6, 1.2))
aim = bpy.context.active_object
bpy.ops.object.camera_add(location=(2.2, -6.5, 1.5))
cam = bpy.context.active_object
sc.camera = cam
cam.data.lens = 32
cam.data.dof.use_dof = True
cam.data.dof.focus_object = aim
cam.data.dof.aperture_fstop = 2.4
tr = cam.constraints.new("TRACK_TO")
tr.target = aim
cam.keyframe_insert("location", frame=1)
cam.location = (-0.8, -4.2, 1.3)
cam.keyframe_insert("location", frame=90)

# world: night sky with a horizon glow
w = bpy.data.worlds.new("night")
sc.world = w
w.use_nodes = True
bgn = w.node_tree.nodes["Background"]
sky = w.node_tree.nodes.new("ShaderNodeTexGradient")
coord = w.node_tree.nodes.new("ShaderNodeTexCoord")
sep = w.node_tree.nodes.new("ShaderNodeSeparateXYZ")
ramp_w = w.node_tree.nodes.new("ShaderNodeValToRGB")
w.node_tree.links.new(coord.outputs["Generated"], sep.inputs[0])
w.node_tree.links.new(sep.outputs["Z"], ramp_w.inputs["Fac"])
ramp_w.color_ramp.elements[0].position = 0.5
ramp_w.color_ramp.elements[0].color = (0.25, 0.12, 0.08, 1)
ramp_w.color_ramp.elements[1].position = 0.62
ramp_w.color_ramp.elements[1].color = (0.01, 0.015, 0.05, 1)
w.node_tree.links.new(ramp_w.outputs["Color"], bgn.inputs["Color"])
bgn.inputs["Strength"].default_value = 1.0
_ = sky

# render settings
sc.render.engine = "CYCLES" if ENGINE == "CYCLES" else "BLENDER_EEVEE"
if ENGINE == "CYCLES":
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.cycles.device = "CPU"
else:
    sc.eevee.taa_render_samples = 16
    for attr in ("use_gtao", "use_soft_shadows", "use_bloom", "use_raytracing"):
        try:
            setattr(sc.eevee, attr, True)
        except Exception:
            pass
sc.view_settings.view_transform = "AgX" if bpy.app.version >= (4, 0, 0) else "Filmic"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = OUT
sc.frame_start, sc.frame_end = F0, F1
bpy.ops.ptcache.bake_all(bake=True)
bpy.ops.render.render(animation=True)
