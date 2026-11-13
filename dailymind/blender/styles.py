"""Style samples we can make for free in Blender: python styles.py -- forest|vfx|mountain OUT.png [RES=40] [SAMPLES=64]

forest   = "3D animation": magical forest, light rays, glowing mushrooms, fireflies, Rain peeking from a giant tree
vfx      = "VFX / action": a ship's cannon fires on the pier — muzzle flash, smoke, sparks, flying debris; Snow flinches
mountain = "cinematic": misty mountain ridge at sunrise, a lone hiker (Snow, small, from behind)
Characters: Rain & Snow rigs (c) Blender Foundation | studio.blender.org (CC-BY). Assets: Poly Haven (CC0).
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
MODE = argv[0] if argv else "forest"
OUT = argv[1] if len(argv) > 1 else f"/tmp/{MODE}.png"
RES = int(argv[2]) if len(argv) > 2 else 40
SAMPLES = int(argv[3]) if len(argv) > 3 else 64
bpy.context.preferences.filepaths.use_scripts_auto_execute = True
bpy.ops.wm.read_factory_settings(use_empty=True)
import dm_assets as AS  # noqa: E402

SC = bpy.context.scene
V = mathutils.Vector
R = math.radians
rr = random.Random(5)


def paint(name, col, rough=0.5, metal=0.0, emit=None, estr=0.0, trans=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = estr
    if trans:
        p.inputs["Transmission Weight"].default_value = trans
    return m


def glow(name, col, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m


def place(asset, loc, rot_z=0.0, scale=1.0, res="1k"):
    print("PLACE", asset, flush=True)
    root, objs = AS.model(asset, res, loc=loc, rot=(0, 0, R(rot_z)), scale=scale)
    for o in objs:
        if "_LOD" in o.name and not o.name.endswith("LOD0"):
            o.hide_render = o.hide_viewport = True
    return root, objs


def prim(op, loc, mat, **kw):
    op(location=loc, **kw)
    o = bpy.context.active_object
    if mat:
        o.data.materials.append(mat)
    return o


def light(kind, loc, energy, col, size=0.1, aim=None):
    o = bpy.data.objects.new("L", bpy.data.lights.new("L", kind))
    SC.collection.objects.link(o)
    o.location = loc
    o.data.energy, o.data.color = energy, col
    if kind == "AREA":
        o.data.size = size
    elif kind in ("POINT", "SPOT"):
        o.data.shadow_soft_size = size
    elif kind == "SUN":
        o.data.angle = R(size)
    if aim:
        o.rotation_euler = (V(aim) - V(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def fog(center, size, density, col=(1, 1, 1), anis=0.6):
    """A volume box: god rays / mist in Cycles."""
    o = prim(bpy.ops.mesh.primitive_cube_add, center, None, size=1)
    o.scale = size
    m = bpy.data.materials.new("fog")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Density"].default_value = density
    v.inputs["Color"].default_value = (*col, 1)
    v.inputs["Anisotropy"].default_value = anis
    nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    o.data.materials.append(m)
    return o


def append_char(name):
    print("CHAR", name, flush=True)
    blend = os.path.join(AS.rig(name), "rain_rig.blend" if name == "rain" else "snow_v03.blend")
    coll = "CH-rain" if name == "rain" else "CH-snow"
    with bpy.data.libraries.load(blend, link=False) as (src, dst):
        dst.collections = [coll]
    c = dst.collections[0]
    SC.collection.children.link(c)
    return max((o for o in c.all_objects if o.type == "ARMATURE"), key=lambda o: len(o.pose.bones))


def pose(arm, d):
    for name, (kind, v) in d.items():
        b = arm.pose.bones.get(name)
        if b is None:
            print("MISSING", name)
            continue
        if kind == "loc":
            b.location = v
        else:
            b.rotation_mode = "XYZ"
            b.rotation_euler = tuple(R(x) for x in v)


def camera(loc, aim, lens, fstop=None, focus=None):
    cd = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cd)
    SC.collection.objects.link(cam)
    SC.camera = cam
    cam.location = loc
    cam.rotation_euler = (V(aim) - V(loc)).to_track_quat("-Z", "Y").to_euler()
    cd.lens = lens
    if fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        cd.dof.focus_distance = (V(focus or aim) - V(loc)).length
    return cam


# =========================================================================================== FOREST (3D animation)
def forest():
    AS.hdri("forest_grove", "2k", 0.5, 40)
    ground = prim(bpy.ops.mesh.primitive_plane_add, (0, 0, 0), AS.texture("forest_leaves_02", "2k", scale=0.6, tint=(0.45, 0.5, 0.32)), size=60)
    # the hero tree: a fat trunk that flares into roots (built ring by ring), bark texture, roots as tapered curves
    import bmesh
    bark = AS.texture("japanese_cedar_bark", "2k", scale=0.9, tint=(0.8, 0.62, 0.5))
    me = bpy.data.meshes.new("trunk")
    bm = bmesh.new()
    rings, seg, TX, TY = 40, 48, -0.35, 1.6
    prev = None
    for i in range(rings):
        z = 9.0 * (i / (rings - 1)) ** 1.4
        r = 0.85 + 1.1 * math.exp(-z / 0.55)
        ring = []
        for j in range(seg):
            a = 2 * math.pi * j / seg
            bump = 1 + 0.07 * math.sin(5 * a + z * 0.8) + 0.05 * math.sin(11 * a - z * 1.7) + (0.25 * max(0.0, math.cos(4 * a)) ** 6) * math.exp(-z / 0.5)
            ring.append(bm.verts.new((TX + r * bump * math.cos(a), TY + r * bump * math.sin(a), z)))
        if prev:
            for j in range(seg):
                bm.faces.new((prev[j], prev[(j + 1) % seg], ring[(j + 1) % seg], ring[j]))
        prev = ring
    bm.to_mesh(me)
    bm.free()
    trunk = bpy.data.objects.new("trunk", me)
    SC.collection.objects.link(trunk)
    me.materials.append(bark)
    for p_ in me.polygons:
        p_.use_smooth = True
    trunk.modifiers.new("s", "SUBSURF").render_levels = 1
    for k in range(6):
        a = R(-75 + k * 48 + rr.uniform(-10, 10))
        cu = bpy.data.curves.new(f"root{k}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.32
        cu.bevel_resolution = 4
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        L = rr.uniform(1.6, 2.4)
        for n, (d_, z_, rad) in enumerate(((0.9, 0.55, 1.0), (1.6 + 0.3 * L, 0.18, 0.55), (1.2 + L, -0.05, 0.12))):
            bp = sp.bezier_points[n]
            bp.co = (TX + d_ * math.cos(a), TY + d_ * math.sin(a), z_)
            bp.radius = rad
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        ro = bpy.data.objects.new(f"root{k}", cu)
        SC.collection.objects.link(ro)
        cu.materials.append(bark)
    # a leafy canopy above (so the sun breaks through in shafts)
    leaf = paint("canopy", (0.12, 0.22, 0.06), 0.7, trans=0.3)
    for k in range(0):
        o = prim(bpy.ops.mesh.primitive_ico_sphere_add, (rr.uniform(-9, 9), rr.uniform(-2, 14), rr.uniform(11, 14)), leaf, radius=rr.uniform(1.4, 2.6),
                 subdivisions=2)
        o.scale.z = 0.5
    # background forest + ground cover
    for k in range(4 if os.environ.get("RICH") else 0):   # full pine models run the cloud machine out of memory at render
        place("pine_tree_01", (rr.uniform(-14, 14), rr.uniform(9, 30), 0), rr.uniform(0, 360), rr.uniform(0.7, 1.0))
    for k in range(16):
        place("fern_02", (rr.uniform(0.9, 3.5), rr.uniform(0.6, 5.0), 0), rr.uniform(0, 360), rr.uniform(0.8, 1.3))
    if os.environ.get("RICH"):  # geometry-node flowers: too heavy for the cloud machine, fine on the PC
        for k in range(6):
            place("celandine_01", (rr.uniform(-2.5, 2.5), rr.uniform(-1.5, 1.0), 0), rr.uniform(0, 360), 0.6)
    place("rock_moss_set_01", (-3.2, 2.5, 0), 30, 0.6)
    place("tree_stump_01", (2.6, 2.4, 0), 0, 1.0)
    # glowing mushrooms (cap + stem, emissive gills) and fireflies
    cols = [(1.0, 0.15, 0.45), (0.1, 0.75, 1.0), (1.0, 0.45, 0.05), (0.55, 0.2, 1.0)]
    stem_m = paint("stem", (0.85, 0.8, 0.7), 0.5)
    for k in range(40):
        x, y = rr.uniform(-0.4, 2.4), rr.uniform(0.3, 2.6)
        if math.hypot(x - TX, y - TY) < 1.3 or (abs(x - 0.85) < 0.35 and abs(y - 2.15) < 0.35):
            continue
        s = rr.uniform(0.09, 0.22)
        c = cols[k % len(cols)]
        prim(bpy.ops.mesh.primitive_cylinder_add, (x, y, s * 0.9), stem_m, radius=s * 0.18, depth=s * 1.8, vertices=10)
        cap = prim(bpy.ops.mesh.primitive_uv_sphere_add, (x, y, s * 1.8), paint(f"cap{k}", tuple(x * 0.6 for x in c), 0.35, emit=c, estr=1.2), radius=s * 0.6,
                   segments=20, ring_count=10)
        cap.scale.z = 0.55
        bpy.ops.object.shade_smooth()
        light("POINT", (x, y, s * 1.6), 6 * s * 10, c, 0.05)
    ff = glow("firefly", (1.0, 0.8, 0.4), 18.0)
    for k in range(45):
        prim(bpy.ops.mesh.primitive_uv_sphere_add, (rr.uniform(0.2, 3.0), rr.uniform(0.6, 6), rr.uniform(0.4, 2.8)), ff, radius=0.007,
             segments=8, ring_count=4)
    # low warm sun through the canopy + god-ray mist
    light("SUN", (0, 0, 10), 6.0, (1.0, 0.78, 0.5), 1.0).rotation_euler = (R(40), 0, R(215))
    fog((0, 4, 4.5), (24, 24, 9), 0.008, (1.0, 0.85, 0.6), 0.75)
    light("AREA", (2.2, 0.2, 2.4), 90, (1.0, 0.78, 0.6), 2.0, aim=(0.95, 1.9, 1.6))
    # Rain peeking out from behind the trunk with a big curious smile
    rain = append_char("rain")
    rain.location = (0.85, 2.15, 0.35)
    rain.rotation_euler = (0, 0, R(-15))
    p = rain.pose.bones["Properties_IKFK"]
    p["ik_arm_left"] = p["ik_arm_right"] = 0.0
    pose(rain, {"FK-Spine": ("rot", (0, 0, 14)), "FK-Chest": ("rot", (6, 0, 16)), "FK-Head": ("rot", (-4, -10, 18)),
                "FK-Upperarm.R": ("rot", (55, 0, 20)), "FK-Forearm.R": ("rot", (85, 0, 0)),
                "FK-Upperarm.L": ("rot", (0, 0, -70)),
                "ACT-Lips_Corner.L": ("loc", (0, 0.024, 0)), "ACT-Lips_Corner.R": ("loc", (0, 0.024, 0)), "MSTR-Jaw": ("rot", (10, 0, 0)),
                "MSTR-Eyebrow.L": ("loc", (0, 0.01, 0)), "MSTR-Eyebrow.R": ("loc", (0, 0.01, 0))})
    camera((1.45, -1.3, 0.95), (0.75, 2.1, 1.2), 26, 2.2, (0.85, 2.1, 1.75))


# =========================================================================================== VFX (cannon fires)
def vfx():
    AS.hdri("kiara_8_sunset", "2k", 0.5, 200)
    pier, _ = place("modular_wooden_pier", (0, 0, 0))
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = SC.ray_cast(dg, V((0.0, 0.5, 20.0)), V((0, 0, -1)))
    D = loc.z if hit else 0.0
    water = prim(bpy.ops.mesh.primitive_plane_add, (0, 0, D - 1.6), paint("sea", (0.02, 0.06, 0.08), 0.05), size=600)
    place("dutch_ship_large_01", (-12, 60, D - 3.5), 120)
    place("coastal_cliff_01", (60, 100, D - 6), -100, 1.8)
    cannon, cobjs = place("cannon_01", (0.3, 1.2, D), 75)
    bpy.context.view_layer.update()
    mn = V((1e9,) * 3)
    mx = -mn
    for o in cobjs:
        if o.type == "MESH":
            for c in o.bound_box:
                w = o.matrix_world @ V(c)
                mn = V(map(min, mn, w))
                mx = V(map(max, mx, w))
    print("CANNON", mn, mx)
    # muzzle at the end of the barrel facing +X-ish (the cannon points to the sea, right of frame)
    muzzle = V((mx.x + 0.05, (mn.y + mx.y) / 2, mn.z + (mx.z - mn.z) * 0.72))
    flash = glow("flash", (1.0, 0.55, 0.15), 22.0)
    for k in range(9):
        s = 0.06 + 0.035 * k
        o = prim(bpy.ops.mesh.primitive_ico_sphere_add, muzzle + V((0.09 * k, rr.uniform(-0.05, 0.05), rr.uniform(-0.03, 0.05))), flash,
                 radius=s * 0.6, subdivisions=3)
        o.scale = (1.4, 1.0, 0.9)
    light("POINT", muzzle + V((0.3, -0.3, 0.2)), 1500, (1.0, 0.6, 0.25), 0.4)
    # smoke: a big billowing volume with noise density
    sm = prim(bpy.ops.mesh.primitive_ico_sphere_add, muzzle + V((1.0, 0.1, 0.25)), None, radius=0.8, subdivisions=4)
    sm.scale = (1.6, 1.0, 0.9)
    m = bpy.data.materials.new("smoke")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Color"].default_value = (0.75, 0.72, 0.7, 1)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.5
    noise.inputs["Detail"].default_value = 8
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.45
    ramp.inputs["To Max"].default_value = 6.0
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], v.inputs["Density"])
    nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    sm.data.materials.append(m)
    # sparks + flying wood debris (frozen mid-flight on ballistic paths)
    sp = glow("spark", (1.0, 0.55, 0.15), 80.0)
    for k in range(90):
        a, el, sp_ = rr.uniform(-0.6, 0.6), rr.uniform(-0.2, 0.9), rr.uniform(0.3, 2.2)
        p0 = muzzle + V((sp_ * math.cos(a), sp_ * math.sin(a) - 0.2, sp_ * el * 0.6))
        o = prim(bpy.ops.mesh.primitive_cylinder_add, p0, sp, radius=0.006, depth=rr.uniform(0.08, 0.22), vertices=6)
        o.rotation_euler = (0, R(90) - el * 0.6, a)
    wood = AS.texture("wood_planks_grey", "1k", scale=2.0)
    for k in range(14):
        o = prim(bpy.ops.mesh.primitive_cube_add, (0.3 + rr.uniform(-0.8, 1.5), 0.4 + rr.uniform(-0.6, 0.6), D + rr.uniform(0.3, 1.8)), wood,
                 size=1)
        o.scale = (rr.uniform(0.03, 0.12), rr.uniform(0.15, 0.4), 0.02)
        o.rotation_euler = (rr.uniform(0, 6), rr.uniform(0, 6), rr.uniform(0, 6))
    place("wooden_barrels_01", (-1.2, 3.0, D), 20, 0.7)
    place("wooden_crate_02", (1.3, 2.4, D), -12)
    # Snow flinches away, hands over his ears
    snow = append_char("snow")
    snow.location = (-0.35, -0.2, D)
    snow.rotation_euler = (0, 0, R(-35))
    ps = snow.pose.bones["Properties"]
    ps["ik_left_upperarm"] = ps["ik_right_upperarm"] = 0.0
    pose(snow, {"FK-UpperArm.L": ("rot", (70, 0, 55)), "FK-Forearm.L": ("rot", (130, 0, 0)),
                "FK-UpperArm.R": ("rot", (70, 0, -55)), "FK-Forearm.R": ("rot", (130, 0, 0)),
                "FK-Head": ("rot", (8, 25, 10)), "Jaw": ("rot", (18, 0, 0)),
                "MSTR-Eyelid_Upper.L": ("loc", (0, -0.006, 0)), "MSTR-Eyelid_Upper.R": ("loc", (0, -0.006, 0)),
                "MSTR-Eyebrow.L": ("loc", (0, -0.006, 0)), "MSTR-Eyebrow.R": ("loc", (0, -0.006, 0))})
    light("SUN", (0, 0, 10), 3.0, (1.0, 0.6, 0.35), 2).rotation_euler = (R(80), 0, R(160))
    light("AREA", (-2.2, -2.6, D + 2.2), 200, (1.0, 0.75, 0.55), 1.5, aim=(-0.35, -0.2, D + 1.3))
    camera((-1.6, -3.0, D + 1.05), (0.9, 0.9, D + 1.0), 24, 4.0, (-0.35, -0.2, D + 1.4))


# =========================================================================================== MOUNTAIN (cinematic)
def mountain():
    AS.hdri("kloppenheim_01_puresky", "2k", 0.9, 100)
    import bmesh
    # distant mountain ranges: three displaced ridgelines receding into the mist
    for layer, (ydist, h, zoff) in enumerate(((180, 70, -40), (320, 120, -50), (520, 200, -60))):
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=220, y_subdivisions=40, size=1, location=(0, ydist, zoff))
        g = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(g.data)
        ph = layer * 1.7
        for v in bm.verts:
            X, Y = v.co.x * 900, v.co.y * 120
            peak = h * (0.55 + 0.25 * math.sin(X * 0.012 + ph) + 0.15 * math.sin(X * 0.031 + 2 * ph) + 0.05 * math.sin(X * 0.09))
            v.co.x, v.co.y = X, Y
            v.co.z = max(0.0, peak * (1 - abs(Y) / 60))
        bm.to_mesh(g.data)
        bm.free()
        g.data.materials.append(AS.texture("aerial_rocks_02", "2k", scale=0.02, tint=(0.75, 0.72, 0.7)))
        bpy.ops.object.shade_smooth()
    # the near outcrop the hiker stands on
    rock_mat = AS.texture("aerial_rocks_02", "2k", scale=0.4, tint=(0.8, 0.75, 0.68))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1, location=(0.5, 6.0, -2.5))
    ro = bpy.context.active_object
    ro.scale = (4.5, 6.0, 3.0)
    tex = bpy.data.textures.new("rock", "CLOUDS")
    tex.noise_scale = 0.5
    tex.noise_depth = 4
    d = ro.modifiers.new("d", "DISPLACE")
    d.texture, d.strength = tex, 0.35
    ro.data.materials.append(rock_mat)
    for k in range(8):
        place("grass_medium_01", (rr.uniform(-2, 3), rr.uniform(2.5, 6), 0.0), rr.uniform(0, 360), 1.0)
    # the sun just above the horizon + mist layers in the valleys
    light("SUN", (0, 0, 10), 4.0, (1.0, 0.7, 0.42), 1.0).rotation_euler = (R(85), 0, R(190))
    fog((0, 350, 0), (1400, 500, 120), 0.0018, (1.0, 0.82, 0.62), 0.8)
    fog((0, 150, -45), (1000, 200, 40), 0.012, (1.0, 0.97, 0.95), 0.5)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = SC.ray_cast(dg, V((0.4, 4.6, 30.0)), V((0, 0, -1)))
    top = loc.z if hit else 0.4
    print("ROCK TOP", top)
    snow = append_char("snow")
    snow.location = (0.4, 4.6, top)
    snow.rotation_euler = (0, 0, R(165))
    ps = snow.pose.bones["Properties"]
    ps["ik_left_upperarm"] = ps["ik_right_upperarm"] = 0.0
    pose(snow, {"FK-UpperArm.R": ("rot", (0, 0, -70)), "FK-Forearm.R": ("rot", (12, 0, 0)),
                "FK-UpperArm.L": ("rot", (0, 0, 70)), "FK-Forearm.L": ("rot", (12, 0, 0)), "FK-Head": ("rot", (-8, 0, 0))})
    camera((-1.2, -1.6, top + 1.1), (1.5, 60, top + 4.0), 30, 8.0, (0.4, 4.6, top + 1.0))


{"forest": forest, "vfx": vfx, "mountain": mountain}[MODE]()
print("RENDER", flush=True)
bpy.context.view_layer.update()
SC.render.engine = "CYCLES"
SC.cycles.samples = SAMPLES
SC.cycles.use_denoising = True
SC.cycles.volume_bounces = 1
SC.view_settings.view_transform = "AgX"
SC.view_settings.look = "AgX - Medium High Contrast"
SC.render.resolution_x, SC.render.resolution_y, SC.render.resolution_percentage = 1080, 1920, RES
SC.render.filepath = OUT
bpy.ops.render.render(write_still=True)
