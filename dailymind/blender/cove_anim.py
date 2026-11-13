"""10-second animated test of the full-3D character style (Rain + Snow on the smugglers' pier).

  python cove_anim.py -- OUTDIR [RES_PCT=50] [SAMPLES=20] [F0] [F1]        (STILL_FRAMES=1,80,200 for stills)
Narration (Chatterbox, timed by VO_TIMES): "This chest is full of gold... and she's about to throw it into the sea.
Because every coin in it... is fake."
"""
import json
import math
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUTDIR = argv[0] if argv else "/tmp/cove_anim"
RES = int(argv[1]) if len(argv) > 1 else 50
SAMPLES = int(argv[2]) if len(argv) > 2 else 20
FPS, DUR = 24, 10.0
NF = int(FPS * DUR)
F0 = int(argv[3]) if len(argv) > 3 else 1
F1 = int(argv[4]) if len(argv) > 4 else NF
STILLS = [int(x) for x in os.environ.get("STILL_FRAMES", "").split(",") if x.strip()]
# line start times (s); overwritten by the voice's real timings when available
VO = {"gold": 0.25, "throw": 2.9, "because": 6.2, "fake": 8.3}
vt = os.environ.get("VO_TIMES")
if vt and os.path.exists(vt):
    VO.update(json.load(open(vt)))

os.environ["COVE_BUILD_ONLY"] = "1"
os.environ.setdefault("COVE_COINS", "160")
sys.argv = [sys.argv[0], "--", "/dev/null"]
try:
    g = runpy.run_path(os.path.join(HERE, "cove_style.py"), run_name="cove_build")
except SystemExit:
    pass
import bpy  # noqa: E402
import mathutils  # noqa: E402

SC = bpy.context.scene
R = math.radians
rain, snow = bpy.data.objects["RIG-rain"], bpy.data.objects["RIG-Snow"]
DECK = bpy.data.objects["lantern_light"].location.z - 1.02
SC.render.fps = FPS
SC.frame_start, SC.frame_end = 1, NF


def fr(t):
    return 1 + round(t * FPS)


def kb(arm, bone, t, loc=None, rot=None, interp=None):
    b = arm.pose.bones[bone]
    if rot is not None:
        b.rotation_mode = "XYZ"
        b.rotation_euler = tuple(R(x) for x in rot)
        b.keyframe_insert("rotation_euler", frame=fr(t))
    if loc is not None:
        b.location = loc
        b.keyframe_insert("location", frame=fr(t))


def hold(arm, bone, ts, **kw):
    for t in ts:
        kb(arm, bone, t, **kw)


def blink(arm, bones, t, open_y):
    for b in bones:
        kb(arm, b, t - 0.06, loc=(0, open_y, 0))
        kb(arm, b, t, loc=(0, open_y - 0.0075, 0))
        kb(arm, b, t + 0.1, loc=(0, open_y, 0))


T_RAISE, T_TOSS, T_FAKE = VO["throw"] + 0.45, VO["because"] + 0.35, VO["fake"]
# ------------------------------------------------------------------ RAIN: smug -> lifts a coin -> flips it -> one brow up
pr = rain.pose.bones["Properties_IKFK"]
pr["ik_arm_left"] = pr["ik_arm_right"] = 0.0
hold(rain, "FK-Upperarm.R", (0, DUR), rot=(0, 0, 70))
hold(rain, "FK-Forearm.R", (0, DUR), rot=(14, 0, 0))
kb(rain, "FK-Upperarm.L", 0, rot=(4, 0, -68))
kb(rain, "FK-Forearm.L", 0, rot=(18, 0, 0))
kb(rain, "FK-Upperarm.L", T_RAISE - 0.5, rot=(4, 0, -68))
kb(rain, "FK-Forearm.L", T_RAISE - 0.5, rot=(18, 0, 0))
for t in (T_RAISE + 0.3, T_TOSS - 0.25):           # coin up beside her face
    kb(rain, "FK-Upperarm.L", t, rot=(35, 0, -52))
    kb(rain, "FK-Forearm.L", t, rot=(122, 0, 0))
kb(rain, "FK-Forearm.L", T_TOSS - 0.1, rot=(105, 0, 0))     # dip ...
kb(rain, "FK-Forearm.L", T_TOSS + 0.05, rot=(130, 0, 0))   # ... flick
kb(rain, "FK-Forearm.L", T_TOSS + 0.6, rot=(122, 0, 0))
kb(rain, "FK-Forearm.L", DUR, rot=(122, 0, 0))
kb(rain, "FK-Upperarm.L", DUR, rot=(35, 0, -52))
for t, rot in ((0, (-2, 6, -4)), (T_RAISE, (-3, 10, -6)), (T_TOSS, (2, 4, -2)), (T_TOSS + 0.7, (-6, 2, 0)), (T_FAKE + 0.1, (-5, 12, -10)),
               (DUR, (-5, 13, -11))):
    kb(rain, "FK-Head", t, rot=rot)
for side, (c0, c1, c2) in (("L", (0.012, 0.018, 0.016)), ("R", (0.012, 0.02, 0.028))):
    kb(rain, f"ACT-Lips_Corner.{side}", 0, loc=(0, c0, 0))
    kb(rain, f"ACT-Lips_Corner.{side}", T_RAISE, loc=(0, c1, 0))
    kb(rain, f"ACT-Lips_Corner.{side}", T_FAKE - 0.2, loc=(0, c1, 0))
    kb(rain, f"ACT-Lips_Corner.{side}", T_FAKE + 0.15, loc=(0, c2, 0))     # lopsided smirk on "fake"
kb(rain, "MSTR-Jaw", 0, rot=(2, 0, 0))
lids = ("ACT-Eyelid_Upper.L", "ACT-Eyelid_Upper.R")
for b in lids:
    kb(rain, b, 0, loc=(0, -0.002, 0))
    kb(rain, b, T_RAISE, loc=(0, -0.0042, 0))
    kb(rain, b, DUR, loc=(0, -0.0042, 0))
blink(rain, lids, 1.7, -0.002)
blink(rain, lids, 5.4, -0.0042)
kb(rain, "MSTR-Eyebrow.L", 0, loc=(0, 0.0, 0))
kb(rain, "MSTR-Eyebrow.L", T_FAKE - 0.1, loc=(0, 0.0, 0))
kb(rain, "MSTR-Eyebrow.L", T_FAKE + 0.2, loc=(0, 0.014, 0))          # one brow up
kb(rain, "MSTR-Eyebrow.R", 0, loc=(0, 0.0, 0))
kb(rain, "MSTR-Eyebrow.R", T_FAKE + 0.2, loc=(0, -0.003, 0))
# ------------------------------------------------------------------ SNOW: staring at the gold -> snaps to her, jaw drops -> confused
ps = snow.pose.bones["Properties"]
ps["ik_left_upperarm"] = ps["ik_right_upperarm"] = 0.0
hold(snow, "FK-UpperArm.R", (0, DUR), rot=(0, 0, -68))
hold(snow, "FK-Forearm.R", (0, DUR), rot=(12, 0, 0))
kb(snow, "FK-UpperArm.L", 0, rot=(0, 0, 66))
kb(snow, "FK-Forearm.L", 0, rot=(12, 0, 0))
T_SNAP = VO["throw"] + 1.0
kb(snow, "FK-UpperArm.L", T_SNAP, rot=(0, 0, 66))
kb(snow, "FK-Forearm.L", T_SNAP, rot=(12, 0, 0))
kb(snow, "FK-UpperArm.L", T_SNAP + 0.35, rot=(48, 0, 40))          # hand flies up toward his face
kb(snow, "FK-Forearm.L", T_SNAP + 0.35, rot=(105, 0, 0))
hold(snow, "FK-UpperArm.L", (DUR,), rot=(48, 0, 40))
hold(snow, "FK-Forearm.L", (DUR,), rot=(105, 0, 0))
for t, rot in ((0, (14, 4, 0)), (T_SNAP - 0.05, (16, 2, 0)), (T_SNAP + 0.18, (0, 26, -4)), (T_FAKE, (-2, 24, -6)), (T_FAKE + 0.4, (4, 20, -10)),
               (DUR, (4, 19, -10))):
    kb(snow, "FK-Head", t, rot=rot)
for t, j in ((0, 0), (T_SNAP + 0.05, 0), (T_SNAP + 0.3, 24), (T_FAKE, 22), (T_FAKE + 0.4, 9), (DUR, 8)):
    kb(snow, "Jaw", t, rot=(j, 0, 0))
for b in ("MSTR-Eyebrow.L", "MSTR-Eyebrow.R"):
    kb(snow, b, 0, loc=(0, 0.004, 0))
    kb(snow, b, T_SNAP + 0.05, loc=(0, 0.004, 0))
    kb(snow, b, T_SNAP + 0.25, loc=(0, 0.016, 0))
    kb(snow, b, T_FAKE + 0.1, loc=(0, 0.016, 0))
    kb(snow, b, T_FAKE + 0.45, loc=(0, 0.006 if b.endswith("L") else 0.012, 0))
slids = ("MSTR-Eyelid_Upper.L", "MSTR-Eyelid_Upper.R")
for b in slids:
    kb(snow, b, 0, loc=(0, 0.0, 0))
    kb(snow, b, T_SNAP + 0.05, loc=(0, 0.0, 0))
    kb(snow, b, T_SNAP + 0.25, loc=(0, 0.003, 0))
    kb(snow, b, DUR, loc=(0, 0.003, 0))
blink(snow, slids, 2.2, 0.0)
blink(snow, slids, 7.6, 0.003)
# breathing: tiny chest rise on both
for arm, bone in ((rain, "FK-Chest"), (snow, "MSTR-Spine_Chest")):
    if bone in arm.pose.bones:
        for k in range(0, int(DUR * 2) + 1):
            t = k * 0.5
            kb(arm, bone, t, rot=(1.2 * math.sin(t * 2.2), 0, 0))
# ------------------------------------------------------------------ the coin flip (real ballistic arc + spin)
held = bpy.data.objects["held_coin"]
for t, v in ((0, False), (T_TOSS, False), (T_TOSS + 0.04, True), (T_TOSS + 0.56, True), (T_TOSS + 0.6, False)):
    held.hide_render = v
    held.keyframe_insert("hide_render", frame=fr(t))
SC.frame_set(fr(T_TOSS))
p0 = held.matrix_world.translation.copy()
SC.frame_set(fr(T_TOSS + 0.6))
p1 = held.matrix_world.translation.copy()
fly = bpy.data.objects.new("flip_coin", held.data)
SC.collection.objects.link(fly)
fly.scale = held.scale
tf = 0.6
g_ = 9.81           # real gravity: a 0.6 s flip peaks ~0.44 m above the hand
vz = ((p1.z - p0.z) + 0.5 * g_ * tf * tf) / tf
for k in range(0, int(tf * FPS) + 3):
    tt = min(tf, k / FPS)
    pos = p0.lerp(p1, tt / tf)
    pos.z = p0.z + vz * tt - 0.5 * g_ * tt * tt
    fly.location = pos
    fly.rotation_euler = (R(90) + tt * 6 * 2 * math.pi, 0, R(20))
    fly.keyframe_insert("location", frame=fr(T_TOSS) + k)
    fly.keyframe_insert("rotation_euler", frame=fr(T_TOSS) + k)
for t, v in ((0, True), (T_TOSS, True), (T_TOSS + 0.04, False), (T_TOSS + 0.56, False), (T_TOSS + 0.6, True)):
    fly.hide_render = v
    fly.keyframe_insert("hide_render", frame=fr(t))
print("COIN arc peak above hand (m):", round(vz * vz / (2 * g_), 3))
# ------------------------------------------------------------------ camera: one continuous push-in, then onto her face
cam, tgt, foc = SC.camera, bpy.data.objects["cam_tgt"], bpy.data.objects["focus"]
cam.data.lens = 40
keys = [(0.0, (0.05, -3.4, DECK + 1.65), (0.15, 1.0, DECK + 0.85), (0.15, 0.95, DECK + 0.6)),
        (VO["throw"] + 0.6, (0.2, -2.7, DECK + 1.5), (0.25, 1.0, DECK + 1.05), (0.62, 0.62, DECK + 1.4)),
        (T_TOSS, (0.15, -2.35, DECK + 1.5), (0.2, 1.0, DECK + 1.2), (0.62, 0.62, DECK + 1.45)),
        (T_FAKE - 0.3, (0.25, -2.1, DECK + 1.5), (0.3, 1.0, DECK + 1.25), (0.62, 0.62, DECK + 1.45)),
        (DUR, (0.48, -1.45, DECK + 1.52), (0.55, 0.75, DECK + 1.4), (0.62, 0.62, DECK + 1.45))]
for t, c, a, f in keys:
    cam.location, tgt.location, foc.location = c, a, f
    for o in (cam, tgt, foc):
        o.keyframe_insert("location", frame=fr(t))
# (Blender's default Bezier/auto-clamped keys give an eased, continuous move)
# ------------------------------------------------------------------ render (preview quality in the cloud)
SC.render.engine = "CYCLES"
SC.cycles.samples = SAMPLES
SC.cycles.use_denoising = True
SC.render.use_persistent_data = True
SC.view_settings.view_transform = "AgX"
SC.view_settings.look = "AgX - Medium High Contrast"
SC.render.resolution_x, SC.render.resolution_y, SC.render.resolution_percentage = 1080, 1920, RES
os.makedirs(OUTDIR, exist_ok=True)
if STILLS:
    for f in STILLS:
        SC.frame_set(f)
        SC.render.filepath = os.path.join(OUTDIR, f"{f:04d}.png")
        bpy.ops.render.render(write_still=True)
else:
    SC.frame_start, SC.frame_end = F0, F1
    SC.render.image_settings.file_format = "PNG"
    SC.render.filepath = os.path.join(OUTDIR, "")
    bpy.ops.render.render(animation=True)
