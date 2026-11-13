"""Style frame: film-quality 3D characters (Blender Studio rigs, CC-BY) acting in a rich 3D set.

  python cove_style.py -- OUT.png [RES_PCT=40] [SAMPLES=96]
Set: a smugglers' pier at sunset (Poly Haven CC0): ship in the bay, cliffs, barrels, crates, lantern, open treasure chest.
Characters: Rain (smug, a gold coin in hand) and Snow (shocked) — CC-BY Blender Foundation | studio.blender.org.
"""
import math
import os
import random
import sys

import bpy
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/tmp/cove.png"
RES = int(argv[1]) if len(argv) > 1 else 40
SAMPLES = int(argv[2]) if len(argv) > 2 else 96
RIGS = os.path.join(os.path.dirname(HERE), "assets_cache", "rigs")

bpy.context.preferences.filepaths.use_scripts_auto_execute = True
bpy.ops.wm.read_factory_settings(use_empty=True)
import dm_assets as AS  # noqa: E402

SC = bpy.context.scene
V = mathutils.Vector
R = math.radians


def paint(name, col, rough=0.5, metal=0.0, emit=None, estr=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = estr
    return m


def place(asset, loc, rot_z=0.0, scale=1.0, res="1k", keep_lod0=True):
    root, objs = AS.model(asset, res, loc=loc, rot=(0, 0, R(rot_z)), scale=scale)
    for o in objs:
        if keep_lod0 and "_LOD" in o.name and not o.name.endswith("LOD0"):
            o.hide_render = o.hide_viewport = True
    return root, objs


# ------------------------------------------------------------------ world + light
AS.hdri("kiara_8_sunset", "2k", 0.8, 200)
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
SC.collection.objects.link(sun)
sun.data.energy, sun.data.color, sun.data.angle = 4.5, (1.0, 0.55, 0.28), R(2.5)
sun.rotation_euler = (R(83), 0, R(155))       # low sun from behind-left: warm rim light on both characters

# warm key (sunset bounce) on the faces + a cool fill, so backlit characters still read
def area(name, loc, aim, energy, col, size):
    o = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA"))
    SC.collection.objects.link(o)
    o.location = loc
    o.data.energy, o.data.color, o.data.size = energy, col, size
    d = V(aim) - V(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o


# ------------------------------------------------------------------ set
pier, pier_objs = place("modular_wooden_pier", (0, 0, 0), 0)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
hit, loc, *_ = SC.ray_cast(dg, V((0.0, 0.5, 20.0)), V((0, 0, -1)))
DECK = loc.z if hit else 0.0
print("DECK", DECK)
water = bpy.data.meshes.new("water")
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, DECK - 1.6))
wo = bpy.context.active_object
wm = paint("sea", (0.02, 0.06, 0.08), 0.04)
nt = wm.node_tree
wv = nt.nodes.new("ShaderNodeTexNoise")
wv.inputs["Scale"].default_value = 1.2
wv.inputs["Detail"].default_value = 8
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.25
nt.links.new(wv.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
wo.data.materials.append(wm)
place("dutch_ship_large_01", (14, 70, DECK - 3.5), 70, 1.0)
place("coastal_cliff_01", (-60, 60, DECK - 5.0), 75, 1.6)
place("coastal_cliff_01", (70, 110, DECK - 6.0), -110, 1.8)
place("wooden_barrels_01", (-1.0, 3.2, DECK), 20, 0.7)
place("wooden_crate_02", (1.05, 1.6, DECK), -12)
place("wooden_crate_01", (1.05, 1.62, DECK + 0.45), 8)
place("wooden_lantern_01", (0.95, 1.55, DECK + 0.79), 30)
lamp = bpy.data.objects.new("lantern_light", bpy.data.lights.new("lantern_light", "POINT"))
SC.collection.objects.link(lamp)
lamp.location = (0.95, 1.55, DECK + 1.02)
lamp.data.energy, lamp.data.color, lamp.data.shadow_soft_size = 40, (1.0, 0.62, 0.3), 0.05
place("wooden_bucket_01", (-1.05, 0.6, DECK), 0)
chest_root, chest = place("treasure_chest", (0.15, 0.95, DECK), -18)
for o in chest:
    if o.name.endswith("_lid"):
        o.rotation_euler.x += R(-105)   # hinge open (lid origin sits on the hinge)
# gold heaped in the chest + a few spilled coins
gold = paint("gold", (1.0, 0.72, 0.28), 0.18, 1.0)
rr = random.Random(3)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.022, depth=0.004)
coin_me = bpy.context.active_object.data
bpy.data.objects.remove(bpy.context.active_object)
coin_me.materials.append(gold)
for i in range(220):
    o = bpy.data.objects.new(f"coin{i}", coin_me)
    SC.collection.objects.link(o)
    o.parent = chest_root
    u, v = rr.uniform(-0.38, 0.38), rr.uniform(-0.18, 0.18)
    o.location = (u, v, 0.5 + 0.09 * (1 - (u / 0.4) ** 2) * (1 - (v / 0.2) ** 2) + rr.uniform(-0.01, 0.01))
    o.rotation_euler = (rr.uniform(-0.5, 0.5), rr.uniform(-0.5, 0.5), rr.uniform(0, 6))
for i in range(14):
    o = bpy.data.objects.new(f"spill{i}", coin_me)
    SC.collection.objects.link(o)
    o.location = (0.15 + rr.uniform(-0.6, 0.5), 0.6 + rr.uniform(-0.45, 0.1), DECK + 0.002)
    o.rotation_euler = (0, 0, rr.uniform(0, 6))


# ------------------------------------------------------------------ characters (CC-BY Blender Foundation)
def append_char(blend, coll_name):
    with bpy.data.libraries.load(blend, link=False) as (src, dst):
        dst.collections = [coll_name]
    c = dst.collections[0]
    SC.collection.children.link(c)
    arm = max((o for o in c.all_objects if o.type == "ARMATURE"), key=lambda o: len(o.pose.bones))
    return c, arm


def pose(arm, d):
    pb = arm.pose.bones
    for name, (kind, v) in d.items():
        b = pb.get(name)
        if b is None:
            print("MISSING BONE", arm.name, name)
            continue
        if kind == "loc":
            b.location = v
        else:
            b.rotation_mode = "XYZ"
            b.rotation_euler = tuple(R(x) for x in v)


rain_c, rain = append_char(os.path.join(RIGS, "rain", "rain_rig.blend"), "CH-rain")
snow_blend = os.path.join(RIGS, "snow", "snow_v03.blend")
with bpy.data.libraries.load(snow_blend) as (src, _):
    snow_coll = next((n for n in src.collections if n.lower().startswith("ch-snow")), None) or src.collections[0]
print("SNOW COLL", snow_coll)
snow_c, snow = append_char(snow_blend, snow_coll)
print("ARMS", rain.name, snow.name)

# Rain: front right of the chest, turned to camera, smug half-lidded grin, coin held up by her face
rain.location = (0.62, 0.62, DECK)
rain.rotation_euler = (0, 0, R(-28))
p = rain.pose.bones["Properties_IKFK"]
p["ik_arm_left"] = 0.0
p["ik_arm_right"] = 0.0
pose(rain, {
    "FK-Upperarm.R": ("rot", (0, 0, 70)), "FK-Forearm.R": ("rot", (12, 0, 0)),
    "FK-Upperarm.L": ("rot", (55, 0, -40)), "FK-Forearm.L": ("rot", (95, 0, 0)), "FK-Hand.L": ("rot", (0, 0, -15)),
    "FK-Head": ("rot", (-4, 8, -6)), "FK-Neck": ("rot", (0, 0, -4)),
    "MSTR-Jaw": ("rot", (5, 0, 0)),
    "ACT-Lips_Corner.L": ("loc", (0, 0.018, 0)), "ACT-Lips_Corner.R": ("loc", (0, 0.022, 0)),
    "ACT-Eyelid_Upper.L": ("loc", (0, -0.0045, 0)), "ACT-Eyelid_Upper.R": ("loc", (0, -0.0045, 0)),
    "MSTR-Eyebrow.L": ("loc", (0, 0.008, 0)), "MSTR-Eyebrow.R": ("loc", (0, -0.002, 0)),
})
# Snow: behind-left, leaning in, jaw dropped, eyes wide, brows up
snow.location = (-0.42, 1.55, DECK)
snow.rotation_euler = (0, 0, R(25))
sp = snow.pose.bones.get("Properties")
if sp is not None:
    sp["ik_left_upperarm"] = 0.0
    sp["ik_right_upperarm"] = 0.0
pose(snow, {
    "FK-UpperArm.R": ("rot", (0, 0, -68)), "FK-Forearm.R": ("rot", (10, 0, 0)), "FK-UpperArm.L": ("rot", (40, 0, -55)), "FK-Forearm.L": ("rot", (80, 0, 0)),
    "FK-Head": ("rot", (6, -10, 4)),
    "Jaw": ("rot", (22, 0, 0)),
    "MSTR-Eyelid_Upper.L": ("loc", (0, 0.003, 0)), "MSTR-Eyelid_Upper.R": ("loc", (0, 0.003, 0)),
    "MSTR-Eyebrow.L": ("loc", (0, 0.012, 0)), "MSTR-Eyebrow.R": ("loc", (0, 0.012, 0)),
})
print("SNOW FK", [b.name for b in snow.pose.bones if b.name.startswith(("FK-UpperArm", "FK-Forearm", "FK-Head", "FK-Neck"))])
# a coin in Rain's raised hand
hand = rain.pose.bones.get("FK-Hand.L")
held = bpy.data.objects.new("held_coin", coin_me)
SC.collection.objects.link(held)
held.scale = (2.2, 2.2, 2.2)
held.parent, held.parent_type, held.parent_bone = rain, "BONE", "FK-Hand.L"
held.location = (0.0, 0.05, 0.02)
held.rotation_euler = (R(90), 0, 0)

area("key", (-1.6, -1.4, DECK + 2.3), (0.2, 1.0, DECK + 1.3), 260, (1.0, 0.74, 0.52), 1.6)
area("fill", (2.4, -1.0, DECK + 1.6), (0.2, 1.0, DECK + 1.2), 70, (0.62, 0.72, 1.0), 2.5)

# ------------------------------------------------------------------ camera
cd = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cd)
SC.collection.objects.link(cam)
SC.camera = cam
cd.lens = 40
cd.dof.use_dof = True
cd.dof.aperture_fstop = 2.4
cam.location = (0.15, -2.75, DECK + 1.38)
tgt = bpy.data.objects.new("cam_tgt", None)
SC.collection.objects.link(tgt)
tgt.location = (0.1, 1.0, DECK + 0.95)
c = cam.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
foc = bpy.data.objects.new("focus", None)
SC.collection.objects.link(foc)
foc.location = (0.62, 0.62, DECK + 1.45)
cd.dof.focus_object = foc

# ------------------------------------------------------------------ render
SC.render.engine = "CYCLES"
SC.cycles.samples = SAMPLES
SC.cycles.use_denoising = True
SC.view_settings.view_transform = "AgX"
SC.view_settings.look = "AgX - Medium High Contrast"
SC.render.resolution_x, SC.render.resolution_y, SC.render.resolution_percentage = 1080, 1920, RES
SC.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("CREDIT: Rain & Snow rigs (c) Blender Foundation | studio.blender.org (CC-BY)")
