"""Quick check renders of Hero3D characters: python hero_test.py -- OUT.png [face|body] [res_pct]"""
import math, os, sys
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index("--") + 1:]
out, mode, res = argv[0], argv[1] if len(argv) > 1 else "body", int(argv[2]) if len(argv) > 2 else 40
bpy.ops.wm.read_factory_settings(use_empty=True)
import dm_assets as AS
from hero3d import Hero
SC = bpy.context.scene
AS.hdri("studio_small_09", "1k", 0.8)
capt = Hero("capt", 1.6, skin=(0.86, 0.6, 0.45), beard=True, hat="brim", coat=("fabric_leather_02", (0.42, 0.26, 0.15)))
capt.place((-0.45, 0, 0), 15)
capt.pose(eyes="smug", brows="smug", mouth="grin", look=(-0.3, 0.1), head=(-4, -12, 5), arm_l=(15, 12, 25), arm_r=(70, 25, 100), lean=-3)
kid = Hero("lad", 1.35, skin=(0.92, 0.7, 0.55), hair="curly", hair_col=(0.45, 0.22, 0.08), eye_col=(0.35, 0.25, 0.12), coat=None,
           shirt=("rough_linen", (0.75, 0.68, 0.55)), pants=("hessian_230", (0.4, 0.3, 0.2)), scarf=(0.6, 0.12, 0.1))
kid.place((0.45, 0.1, 0), -20)
kid.pose(eyes="wide", brows="sad", mouth="O", look=(-0.6, 0.2), head=(6, 15, -6), arm_l=(30, 10, 80), arm_r=(25, 10, 85))
bpy.ops.mesh.primitive_plane_add(size=20)
fl = bpy.context.active_object
fl.data.materials.append(AS.texture("wood_planks_grey", "1k", scale=1.0))
key = bpy.data.lights.new("key", "AREA"); key.energy = 400; key.size = 2.0; key.color = (1, 0.85, 0.7)
ko = bpy.data.objects.new("key", key); SC.collection.objects.link(ko); ko.location = (-2.5, -3, 3.2)
ko.rotation_euler = (math.radians(55), 0, math.radians(-40))
rim = bpy.data.lights.new("rim", "AREA"); rim.energy = 300; rim.size = 1.0; rim.color = (0.7, 0.8, 1.0)
ro = bpy.data.objects.new("rim", rim); SC.collection.objects.link(ro); ro.location = (2.0, 2.5, 2.6)
ro.rotation_euler = (math.radians(-50), 0, math.radians(140))
cd = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cd); SC.collection.objects.link(cam); SC.camera = cam
if mode == "face":
    cd.lens = 85; cam.location = (-0.55, -1.6, 1.42); tgt = (-0.42, 0, 1.38)
else:
    cd.lens = 40; cam.location = (0, -4.0, 1.1); tgt = (0, 0, 0.8)
d = [tgt[i] - cam.location[i] for i in range(3)]
cam.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[0], -d[1]) * -1 + 0)
c = cam.constraints.new("TRACK_TO"); e = bpy.data.objects.new("tgt", None); SC.collection.objects.link(e); e.location = tgt
c.target = e; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
SC.render.engine = "CYCLES"; SC.cycles.samples = 48; SC.cycles.use_denoising = True
SC.view_settings.view_transform = "AgX"; SC.view_settings.look = "AgX - Medium High Contrast"
SC.render.resolution_x, SC.render.resolution_y, SC.render.resolution_percentage = 1080, 1920, res
SC.render.filepath = out
bpy.ops.render.render(write_still=True)
