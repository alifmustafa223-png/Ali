"""Paper cut-out theatre: the 2D artwork's layers (sky / sea / deck / characters) as real paper cards in depth,
lit by a warm stage light so they cast shadows on each other, with paper grain and shallow depth of field.

  python paper_theatre.py -- LAYER_DIR OUT.png [RES=40] [SAMPLES=64]
LAYER_DIR holds sky.png sea.png deck.png chars.png (RGBA, 1080x1920) from `LAYER=... style2d_frame.py`.
"""
import math
import os
import sys

import bpy
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
LD, OUT = argv[0], argv[1]
RES = int(argv[2]) if len(argv) > 2 else 40
SAMPLES = int(argv[3]) if len(argv) > 3 else 64
bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
R = math.radians
V = mathutils.Vector
LENS, SENSOR = 50.0, 36.0
ASPECT = 1080 / 1920


def card(name, img, dist, extra=1.03, xoff=0.0, zoff=0.0, tilt=0.0):
    """A paper card at `dist` metres that exactly fills the frame (times `extra`)."""
    h = dist * SENSOR / LENS * extra
    w = h * ASPECT
    bpy.ops.mesh.primitive_plane_add(size=1, location=(xoff, dist, zoff))
    o = bpy.context.active_object
    o.name = name
    o.scale = (w, h, 1)
    o.rotation_euler = (R(90) + R(tilt), 0, 0)
    sol = o.modifiers.new("paper", "SOLIDIFY")
    sol.thickness = 0.004 * dist
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(LD, img))
    t.extension = "CLIP"
    nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(t.outputs["Color"], p.inputs["Emission Color"])     # keep the painted colours vivid under stage light
    p.inputs["Emission Strength"].default_value = 0.35
    nt.links.new(t.outputs["Alpha"], p.inputs["Alpha"])
    p.inputs["Roughness"].default_value = 0.85
    # paper fibre: fine noise bump
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 260.0
    n.inputs["Detail"].default_value = 6.0
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = 0.12
    nt.links.new(n.outputs["Fac"], b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
    m.blend_method = "HASHED" if hasattr(m, "blend_method") else None
    o.data.materials.append(m)
    return o


# camera at the origin looking +Y
cd = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cd)
SC.collection.objects.link(cam)
SC.camera = cam
cam.rotation_euler = (R(90), 0, 0)
cd.lens, cd.sensor_width = LENS, SENSOR
cd.dof.use_dof = True
cd.dof.aperture_fstop = 2.8
cd.dof.focus_distance = 3.2
card("sky", "sky.png", 6.0, 1.06)
card("sea", "sea.png", 4.4, 1.05)
card("deck", "deck.png", 3.6, 1.04)
card("chars", "chars.png", 3.2, 1.0, xoff=0.0, zoff=-0.02)
# stage lighting: warm key from front-left-top (casts the cards' shadows back onto the layers), cool fill, sunset backlight
def light(kind, loc, energy, col, size, aim):
    o = bpy.data.objects.new(kind, bpy.data.lights.new(kind, kind))
    SC.collection.objects.link(o)
    o.location = loc
    o.data.energy, o.data.color = energy, col
    if kind == "AREA":
        o.data.size = size
    else:
        o.data.shadow_soft_size = size
        o.data.spot_size = R(70)
        o.data.spot_blend = 0.6
    o.rotation_euler = (V(aim) - V(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


light("AREA", (-1.6, 1.2, 1.6), 420, (1.0, 0.86, 0.7), 0.5, (0.2, 3.4, 0.0))
light("AREA", (2.5, 0.0, 0.5), 60, (0.7, 0.8, 1.0), 2.0, (0, 4.5, 0))
light("SPOT", (0.6, 8.2, 0.4), 300, (1.0, 0.7, 0.4), 0.3, (0, 3.2, -0.3))
w = bpy.data.worlds.new("w")
SC.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.015, 0.03, 1)
SC.render.engine = "CYCLES"
SC.cycles.samples = SAMPLES
SC.cycles.use_denoising = True
SC.view_settings.view_transform = "AgX"
SC.view_settings.look = "AgX - Medium High Contrast"
SC.render.resolution_x, SC.render.resolution_y, SC.render.resolution_percentage = 1080, 1920, RES
SC.render.filepath = OUT
bpy.ops.render.render(write_still=True)
