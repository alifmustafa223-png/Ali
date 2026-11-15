"""3D miniature coal-mine tunnel plates for the canary test (flat 2D stickmen are composited on top later).

  python mine_plates.py -- OUTDIR [RES=50] [SAMPLES=64] [PLATES=A,B,C]
A = medium shot down the tunnel (miner shows off the cage)
B = close on a timber beam with an empty hook (the silent canary), green gas creeping along the floor
C = looking back up the tunnel: green gas rolling toward camera, daylight spill from the exit behind the lens
Each plate is rendered empty (no characters). Poly Haven CC0 textures/models.
"""
import math
import os
import random
import sys

import bpy
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:]
OUTDIR = argv[0]
RES = int(argv[1]) if len(argv) > 1 else 50
SAMPLES = int(argv[2]) if len(argv) > 2 else 64
PLATES = (argv[3] if len(argv) > 3 else "A,B,C").split(",")
os.makedirs(OUTDIR, exist_ok=True)
R = math.radians
V = mathutils.Vector


def build(plate):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import importlib
    import dm_assets as AS
    importlib.reload(AS)
    SC = bpy.context.scene
    rr = random.Random(3)
    rock = AS.texture("dark_rock", "2k", scale=0.9, tint=(0.6, 0.55, 0.5))
    rp = rock.node_tree.nodes["Principled BSDF"]
    rp.inputs["Roughness"].default_value = 0.42      # wet sheen on the coal
    wood = AS.texture("old_planks_02", "1k", scale=1.2, tint=(0.42, 0.3, 0.22))
    rust = AS.texture("metal_grate_rusty", "1k", scale=2.0)
    ground = AS.texture("gravel_floor_02", "1k", scale=1.0, tint=(0.35, 0.33, 0.32))
    # tunnel: an arched tube (half-cylinder + walls), displaced so it's craggy
    L = 40
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.6, depth=L, location=(0, L / 2 - 4, 1.1), rotation=(R(90), 0, 0), end_fill_type="NOTHING")
    tun = bpy.context.active_object
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts=6)
    bpy.ops.object.mode_set(mode="OBJECT")
    for v in tun.data.vertices:
        v.co *= 1.0
    tex = bpy.data.textures.new("crag", "CLOUDS")
    tex.noise_scale, tex.noise_depth = 0.35, 4
    d = tun.modifiers.new("d", "DISPLACE")
    d.texture, d.strength, d.texture_coords = tex, -0.35, "GLOBAL"
    tun.modifiers.new("s", "SUBSURF").render_levels = 1
    tun.data.materials.append(rock)
    for p in tun.data.polygons:
        p.use_smooth = True
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, L / 2 - 4, -0.2))
    fl = bpy.context.active_object
    fl.scale = (3.4, L, 1)
    fl.data.materials.append(ground)
    # timber frames every 2.2 m
    for k in range(14):
        y = -1.0 + k * 2.2
        for x in (-1.15, 1.15):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0.85))
            o = bpy.context.active_object
            o.scale = (0.14, 0.14, 2.1)
            o.rotation_euler = (0, R(-4 if x < 0 else 4), 0)
            o.data.materials.append(wood)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, y, 1.95))
        o = bpy.context.active_object
        o.scale = (2.5, 0.16, 0.16)
        o.data.materials.append(wood)
    # rails + sleepers
    steel = bpy.data.materials.new("steel")
    steel.use_nodes = True
    sp = steel.node_tree.nodes["Principled BSDF"]
    sp.inputs["Base Color"].default_value = (0.25, 0.22, 0.2, 1)
    sp.inputs["Metallic"].default_value = 1.0
    sp.inputs["Roughness"].default_value = 0.35
    for x in (-0.35, 0.35):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, L / 2 - 4, -0.12))
        o = bpy.context.active_object
        o.scale = (0.05, L, 0.06)
        o.data.materials.append(steel)
    for k in range(70):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -3.5 + k * 0.55, -0.17))
        o = bpy.context.active_object
        o.scale = (1.0, 0.16, 0.05)
        o.rotation_euler = (0, 0, R(rr.uniform(-3, 3)))
        o.data.materials.append(wood)
    # a mine cart heaped with coal
    def cart(loc, rot=0.0, tipped=False):
        root = bpy.data.objects.new("cart", None)
        SC.collection.objects.link(root)
        root.location, root.rotation_euler = loc, (0, R(70) if tipped else 0, R(rot))
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.55, radius2=0.75, depth=0.55, location=(0, 0, 0.42), rotation=(0, 0, R(45)))
        b = bpy.context.active_object
        b.scale = (1.0, 1.45, 1.0)
        b.data.materials.append(rust)
        b.parent = root
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.5, location=(0, 0, 0.72))
        coal = bpy.context.active_object
        coal.scale = (0.95, 1.35, 0.32)
        cm = bpy.data.materials.new("coal")
        cm.use_nodes = True
        cp = cm.node_tree.nodes["Principled BSDF"]
        cp.inputs["Base Color"].default_value = (0.02, 0.02, 0.025, 1)
        cp.inputs["Roughness"].default_value = 0.3
        n = cm.node_tree.nodes.new("ShaderNodeTexVoronoi")
        n.inputs["Scale"].default_value = 18
        bmp = cm.node_tree.nodes.new("ShaderNodeBump")
        bmp.inputs["Strength"].default_value = 0.8
        cm.node_tree.links.new(n.outputs["Distance"], bmp.inputs["Height"])
        cm.node_tree.links.new(bmp.outputs["Normal"], cp.inputs["Normal"])
        coal.data.materials.append(cm)
        coal.parent = root
        for wx in (-0.42, 0.42):
            for wy in (-0.45, 0.45):
                bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.14, depth=0.06, location=(wx, wy, 0.0), rotation=(0, R(90), 0))
                w = bpy.context.active_object
                w.data.materials.append(steel)
                w.parent = root
        return root
    # lanterns hanging from the cap beams (each with a warm light)
    lamps = []
    for k_, y in enumerate((1.2, 5.6, 10.0, 14.4, 18.8)):
        lx = 0.75 if k_ % 2 == 0 else -0.75
        AS.model("wooden_lantern_01", "1k", loc=(lx, y, 1.3), scale=0.8)
        L_ = bpy.data.objects.new("lamp", bpy.data.lights.new("lamp", "POINT"))
        SC.collection.objects.link(L_)
        L_.location = (lx, y, 1.5)
        L_.data.energy, L_.data.color, L_.data.shadow_soft_size = 140, (1.0, 0.62, 0.28), 0.06
        lamps.append(L_)

    def fog(center, size, density, col, anis=0.5):
        bpy.ops.mesh.primitive_cube_add(size=1, location=center)
        o = bpy.context.active_object
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

    w = bpy.data.worlds.new("w")
    SC.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.009, 0.007, 1)
    fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "AREA"))   # soft warm fill from behind the camera (the miner's own lamp)
    SC.collection.objects.link(fill)
    fill.location = (0.4, -3.2, 1.9)
    fill.rotation_euler = (R(80), 0, 0)
    fill.data.energy, fill.data.color, fill.data.size = 90, (1.0, 0.78, 0.55), 1.5
    cd = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cd)
    SC.collection.objects.link(cam)
    SC.camera = cam

    def aim(loc, tgt, lens, focus, fstop=2.8):
        cam.location = loc
        cam.rotation_euler = (V(tgt) - V(loc)).to_track_quat("-Z", "Y").to_euler()
        cd.lens = lens
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        cd.dof.focus_distance = focus

    if plate == "A":
        cart((-0.0, 6.5, -0.12), 2)
        fog((0, 8, 1), (3.4, 26, 3), 0.03, (1.0, 0.85, 0.7), 0.6)
        # a hard beam of light from a shaft above, cutting through dust
        sp_ = bpy.data.objects.new("shaft", bpy.data.lights.new("shaft", "SPOT"))
        SC.collection.objects.link(sp_)
        sp_.location = (-0.4, 3.2, 3.2)
        sp_.rotation_euler = (R(12), R(-8), 0)
        sp_.data.energy, sp_.data.color, sp_.data.spot_size, sp_.data.spot_blend = 2500, (1.0, 0.78, 0.45), R(16), 0.3
        aim((0.2, -2.8, 1.3), (0.0, 6.0, 0.95), 28, 3.4, 4.0)
    elif plate == "B":
        # close on a timber post + cap beam with an iron hook; green gas creeping low
        bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.01, location=(0.32, 1.25, 1.55), rotation=(R(90), 0, 0))
        bpy.context.active_object.data.materials.append(steel)
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.008, depth=0.3, location=(0.32, 1.25, 1.75))
        bpy.context.active_object.data.materials.append(steel)
        fog((0, 3, -0.05), (3.4, 10, 0.45), 0.9, (0.55, 0.85, 0.45), 0.2)
        fog((0, 6, 1), (3.4, 14, 3), 0.05, (0.85, 0.95, 0.8), 0.5)
        aim((0.55, -0.15, 1.35), (0.3, 1.25, 1.4), 45, 1.45, 2.0)
    elif plate == "C":
        cart((0.0, 5.0, -0.12), 0)
        fog((0, 11, 0.6), (3.4, 14, 2.6), 0.9, (0.45, 0.85, 0.38), 0.3)     # the gas cloud rolling down the tunnel
        fog((0, 6, 1), (3.4, 26, 3), 0.05, (1.0, 0.9, 0.8), 0.5)
        ex = bpy.data.objects.new("exit", bpy.data.lights.new("exit", "AREA"))   # daylight from the exit behind the camera
        SC.collection.objects.link(ex)
        ex.location = (0, -4.5, 1.0)
        ex.rotation_euler = (R(-90), 0, 0)
        ex.data.energy, ex.data.color, ex.data.size = 1500, (1.0, 0.95, 0.85), 2.5
        aim((0.0, -1.8, 1.1), (0.0, 10, 0.9), 24, 4.5, 5.6)
    SC.render.engine = "CYCLES"
    SC.cycles.samples = SAMPLES
    SC.cycles.use_denoising = True
    SC.cycles.volume_bounces = 1
    SC.view_settings.view_transform = "AgX"
    SC.view_settings.look = "AgX - Medium High Contrast"
    SC.render.resolution_x, SC.render.resolution_y, SC.render.resolution_percentage = 1080, 1920, RES
    if plate == "B":   # where the hook lands on screen, so the 2D cage hangs exactly on it
        from bpy_extras.object_utils import world_to_camera_view
        bpy.context.view_layer.update()
        q = world_to_camera_view(SC, cam, V((0.32, 1.25, 1.50)))
        import json
        json.dump({"hook_px": [q.x * 1080, (1 - q.y) * 1920]}, open(os.path.join(OUTDIR, "plate_B.json"), "w"))
        print("HOOK", q.x * 1080, (1 - q.y) * 1920)
    SC.render.filepath = os.path.join(OUTDIR, f"plate_{plate}.png")
    bpy.ops.render.render(write_still=True)


for p in PLATES:
    build(p)
