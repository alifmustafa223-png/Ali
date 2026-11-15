"""3D plates for the Great Molasses Flood Short (Boston, January 1919) - the canary-video look: real lit Blender sets,
the channel's 2D toon characters are composited on top later (ultimate/make_molasses.py).

  python boston_plates.py -- OUTDIR [RES=60] [SAMPLES=64] [PLATES=wave,tank,burst,flood,harbor,tankclose,tankbrown,court,summer]
Real scale (metres). Street along +X, brick blocks both sides (town_kit), cobbles, sidewalks, snow, the elevated railway.
Each plate also writes OUTDIR/plate_<name>.json with screen positions (px, 1080x1920) of key points.
"""
import json
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
RES = int(argv[1]) if len(argv) > 1 else 60
SAMPLES = int(argv[2]) if len(argv) > 2 else 64
PLATES = (argv[3] if len(argv) > 3 else "wave,tank,burst,flood,harbor,tankclose,tankbrown,court,summer").split(",")
os.makedirs(OUTDIR, exist_ok=True)
R = math.radians
V = mathutils.Vector


def build(plate):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import importlib
    import dm_assets as AS
    import town_kit as TK
    importlib.reload(AS)
    importlib.reload(TK)
    SC = bpy.context.scene
    rr = random.Random(11)
    meta = {}

    def mat(name, col, rough=0.5, metal=0.0, coat=0.0, emit=None, estr=0.0):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        p = m.node_tree.nodes["Principled BSDF"]
        p.inputs["Base Color"].default_value = (*col, 1)
        p.inputs["Roughness"].default_value = rough
        p.inputs["Metallic"].default_value = metal
        if coat:
            p.inputs["Coat Weight"].default_value = coat
            p.inputs["Coat Roughness"].default_value = 0.05
        if emit:
            p.inputs["Emission Color"].default_value = (*emit, 1)
            p.inputs["Emission Strength"].default_value = estr
        return m

    def box(name, c, size, m, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=c, rotation=rot)
        o = bpy.context.active_object
        o.name = name
        o.scale = size
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)   # object coords = metres (texture scale)
        o.data.materials.append(m)
        return o

    def molasses():
        m = mat("molasses", (0.055, 0.02, 0.006), 0.07, coat=0.7)
        nt = m.node_tree
        p = nt.nodes["Principled BSDF"]
        p.inputs["Subsurface Weight"].default_value = 0.25
        p.inputs["Subsurface Radius"].default_value = (0.9, 0.35, 0.08)
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = 0.6
        n.inputs["Detail"].default_value = 6
        b = nt.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = 0.18
        nt.links.new(n.outputs["Fac"], b.inputs["Height"])
        nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
        return m

    def mesh_from(name, verts, faces, m, smooth=True):
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        me.update()
        o = bpy.data.objects.new(name, me)
        SC.collection.objects.link(o)
        o.data.materials.append(m)
        if smooth:
            for p in me.polygons:
                p.use_smooth = True
        return o

    def grid_surface(name, x0, x1, y0, y1, nx, ny, zf, m):
        verts = [(x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny, 0.0) for j in range(ny + 1) for i in range(nx + 1)]
        verts = [(x, y, zf(x, y)) for x, y, _ in verts]
        faces = [(j * (nx + 1) + i, j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i) for j in range(ny) for i in range(nx)]
        return mesh_from(name, verts, faces, m)

    winter = plate not in ("summer", "court")
    # ------------------------------------------------------------------ world + light
    if plate != "court":   # pure sky only (no foreign town in the background); sun from the far end of the street
        AS.hdri("kloppenheim_01_puresky", "2k", 1.1 if plate == "summer" else 0.8, 30)
        if winter:   # overcast winter: desaturate + cool the sky
            wn = SC.world.node_tree
            bg = wn.nodes["Background"]
            src = bg.inputs["Color"].links[0].from_socket
            hs = wn.nodes.new("ShaderNodeHueSaturation")
            hs.inputs["Saturation"].default_value = 0.35
            hs.inputs["Value"].default_value = 1.05
            wn.links.new(src, hs.inputs["Color"])
            wn.links.new(hs.outputs["Color"], bg.inputs["Color"])
        sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
        SC.collection.objects.link(sun)
        if plate == "summer":
            sun.data.energy, sun.data.color, sun.data.angle = 5.0, (1.0, 0.9, 0.74), R(1.5)
        else:
            sun.data.energy, sun.data.color, sun.data.angle = 3.2, (0.98, 0.95, 0.92), R(4)
        sun.rotation_euler = (R(42), 0, R(72))

    # ------------------------------------------------------------------ street kit
    cob = AS.texture("cobblestone_floor_08", "2k", scale=0.55, tint=(0.62, 0.6, 0.58) if winter else (0.72, 0.68, 0.62))
    pave = AS.texture("precast_stone_paving", "1k", scale=0.5, tint=(0.78, 0.76, 0.74))
    snow = mat("snow", (0.92, 0.94, 0.97), 0.85)
    steel = mat("steel", (0.12, 0.13, 0.14), 0.45, 0.8)

    def street(x0=-60, x1=140):
        box("street", ((x0 + x1) / 2, 0, -0.1), (x1 - x0, 8.2, 0.2), cob)
        for s in (-1, 1):
            box(f"walk{s}", ((x0 + x1) / 2, s * 5.3, 0.0), (x1 - x0, 2.6, 0.3), pave)
            box(f"kerb{s}", ((x0 + x1) / 2, s * 4.05, 0.0), (x1 - x0, 0.18, 0.32), mat("kerb", (0.55, 0.53, 0.5), 0.8))
            if winter:
                for k in range(26):    # snow banks along the kerbs and at the walls
                    x = x0 + rr.uniform(0, x1 - x0)
                    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(x, s * rr.choice([4.4, 6.3]), 0.12))
                    o = bpy.context.active_object
                    o.scale = (rr.uniform(1.2, 3.5), rr.uniform(0.35, 0.6), rr.uniform(0.18, 0.35))
                    o.data.materials.append(snow)
                    bpy.ops.object.shade_smooth()

    def blocks(x0=-50, x1=130, seed=3, skip=()):
        brick = AS.texture("factory_brick", "1k", scale=3.0)
        glass = mat("glass", (0.04, 0.05, 0.06), 0.08, emit=(1.0, 0.75, 0.45), estr=0.6 if winter else 0.0)
        TK.init(glass, brick, AS.texture("grey_roof_tiles", "1k", scale=2.0), scale=1.0)
        walls = [(0.95, 0.88, 0.85), (0.85, 0.72, 0.66), (0.92, 0.8, 0.72), (0.8, 0.7, 0.68), (0.98, 0.9, 0.8)]
        r2 = random.Random(seed)
        for s, yaw in ((1, 0.0), (-1, math.pi)):
            x = x0
            k = 0
            while x < x1:
                bays = r2.choice([2, 3, 3, 4])
                w = bays * 3.4
                if (s, k) not in skip:
                    TK.building(f"b{s}_{k}", (x + w / 2, s * 6.6), yaw, floors=r2.choice([4, 4, 5, 5, 6]), bays=bays,
                                wall=walls[r2.randrange(len(walls))], shutters=TK.SHUTTERS[r2.randrange(len(TK.SHUTTERS))],
                                shop=r2.random() < 0.7, seed=seed * 100 + k * 7 + (s > 0))
                x += w + 0.3
                k += 1

    def elevated(x0=-50, x1=130, bent=None):
        for x in range(int(x0), int(x1), 8):
            for y in (2.2, 3.9):
                rot = (0, 0, 0)
                if bent and abs(x - bent) < 9:
                    rot = (R(14 if y < 3 else 9), R(6), 0)
                box(f"post{x}_{y}", (x, y, 3.3), (0.38, 0.38, 6.6), steel, rot)
            box(f"brace{x}", (x, 3.05, 6.0), (0.25, 2.0, 0.25), steel)
        box("deck", ((x0 + x1) / 2, 3.05, 6.75), (x1 - x0, 2.6, 0.55), steel)
        for y in (2.3, 3.8):
            box(f"girder{y}", ((x0 + x1) / 2, y, 6.2), (x1 - x0, 0.2, 0.7), steel)

    def tank(cx, cy, painted=0.0, burst=False, leaks=False):
        col = tuple((1 - painted) * a + painted * b for a, b in zip((0.3, 0.32, 0.34), (0.24, 0.12, 0.05)))
        tex = mat(f"tankpaint{painted}", col, 0.5, 0.35)
        nt = tex.node_tree
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 0.9
        nz.inputs["Detail"].default_value = 10
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.inputs[6].default_value = (*col, 1)
        mx.inputs[7].default_value = (col[0] * 0.7, col[1] * 0.68, col[2] * 0.65, 1)
        nt.links.new(nz.outputs["Fac"], mx.inputs["Factor"])
        nt.links.new(mx.outputs[2], nt.nodes["Principled BSDF"].inputs["Base Color"])
        Rt, Ht, N = 13.5, 15.0, 40
        for i in range(N):
            a = 2 * math.pi * i / N
            w = 2 * math.pi * Rt / N + 0.06
            # facing-camera side (+y toward camera is -y here) bursts outward about its bottom edge
            out = burst and math.cos(a - math.radians(-90)) > 0.35
            tilt = R(55 + 25 * math.sin(i * 1.7)) if out else 0.0
            px, py = cx + Rt * math.cos(a), cy + Rt * math.sin(a)
            piv = bpy.data.objects.new(f"piv{i}", None)
            SC.collection.objects.link(piv)
            piv.location = (px, py, 0)
            piv.rotation_euler = (0, 0, a - math.pi / 2)
            o = box(f"plate{i}", (0, 0, 0), (w, 0.28, Ht), tex)
            o.location = (0, 0, Ht / 2)
            o.parent = piv
            if out:
                piv.rotation_euler = (-tilt, 0, a - math.pi / 2)
            for k in range(6):   # riveted seams
                b = box(f"band{i}_{k}", (0, 0, 0), (w + 0.02, 0.36, 0.14), mat("seam", (0.2, 0.2, 0.21), 0.5, 0.7))
                b.location = (0, 0, 0.6 + k * 2.75)
                b.parent = piv
            if leaks and i % 3 == 0 and math.cos(a + math.pi / 2) > 0.2:
                for k in range(3):   # dark glossy streaks running down from the seams
                    ln = rr.uniform(1.5, 4.0)
                    st = box(f"leak{i}_{k}", (0, 0, 0), (0.22, 0.1, ln), molasses())
                    st.location = (rr.uniform(-0.5, 0.5), 0.2, 0.6 + k * 2.75 + 2.75 - ln / 2)
                    st.parent = piv
        if not burst:
            bpy.ops.mesh.primitive_cone_add(vertices=N, radius1=Rt + 0.3, radius2=0.8, depth=3.0, location=(cx, cy, Ht + 1.5))
            bpy.context.active_object.data.materials.append(tex)
        return Rt, Ht

    def harbor(y0=-60, brown=False):
        water = mat("water", (0.11, 0.05, 0.015) if brown else (0.05, 0.1, 0.13), 0.45)
        nt = water.node_tree
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = 0.35
        n.inputs["Detail"].default_value = 8
        b = nt.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = 0.35
        nt.links.new(n.outputs["Fac"], b.inputs["Height"])
        nt.links.new(b.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
        box("water", (0, y0 - 150, -1.4), (600, 300, 0.2), water)
        box("quay", (0, y0 + 2, -0.7), (600, 4, 1.6), mat("quaystone", (0.42, 0.4, 0.38), 0.85))

    cd = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cd)
    SC.collection.objects.link(cam)
    SC.camera = cam

    def aim(loc, tgt, lens, fstop=None):
        cam.location = loc
        cam.rotation_euler = (V(tgt) - V(loc)).to_track_quat("-Z", "Y").to_euler()
        cd.lens = lens
        if fstop:
            cd.dof.use_dof = True
            cd.dof.aperture_fstop = fstop
            cd.dof.focus_distance = (V(tgt) - V(loc)).length

    def proj(p):
        from bpy_extras.object_utils import world_to_camera_view
        bpy.context.view_layer.update()
        q = world_to_camera_view(SC, cam, V(p))
        return [round(q.x * 1080, 1), round((1 - q.y) * 1920, 1)]

    # ------------------------------------------------------------------ the plates
    if plate in ("wave", "flood", "summer"):
        street()
        skip = {(-1, 5)} if plate == "flood" else set()
        blocks(skip=skip)
        elevated(bent=34 if plate == "flood" else None)
        if plate != "summer":
            for k in range(6):
                bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=4.2, location=(rr.uniform(-10, 60), rr.choice([-4.3, 4.3]), 2.1))
                bpy.context.active_object.data.materials.append(steel)
        else:
            for k, x in enumerate(range(-8, 80, 12)):
                AS.model("street_lamp_01", "1k", loc=(x, -4.5 if k % 2 else 4.5, 0.15), scale=1.0)
    if plate == "wave":
        # the wave front, ~7.5 m high, rolling down the street toward the camera; molasses already flooding behind it
        def zf(x, y):
            d = x - 11.0 + 1.6 * math.sin(y * 0.55) + 0.7 * math.sin(y * 1.7 + 1)
            if d < -1.0:
                return -0.3
            lead = min(1.0, (d + 1.0) / 1.0)
            crest = 8.0 * math.exp(-((d - 4.0) / 4.0) ** 2) + 2.4 * math.exp(-max(0.0, d) / 25)
            return lead * crest + 0.25 * math.sin(x * 0.9 + y * 0.7)
        grid_surface("wave", 9, 120, -6.8, 6.8, 240, 40, zf, molasses())
        for k in range(60):   # flying droplets at the crest
            y = rr.uniform(-6, 6)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=rr.uniform(0.08, 0.3), location=(rr.uniform(12, 16.5), y, rr.uniform(7.5, 11.5)))
            bpy.context.active_object.data.materials.append(molasses())
            bpy.ops.object.shade_smooth()
        aim((-9, -0.6, 1.1), (14, 0.3, 5.6), 20, 6.0)
        meta["crest"] = [proj((15.0, y, 10.0)) for y in (-6, -3, 0, 3, 6)]
        meta["ground_y"] = proj((0, 0, 0))[1]
    elif plate == "flood":
        def zf(x, y):
            return 0.95 + 0.06 * math.sin(x * 0.7 + y) + 0.04 * math.sin(y * 2.1 - x * 0.3)
        grid_surface("flood", -60, 140, -9, 9, 200, 18, zf, molasses())
        # the flattened building: a tipped, broken block half sunk in the molasses
        brick = AS.texture("factory_brick", "1k", scale=0.4)
        for k in range(5):
            box(f"rubble{k}", (34 + k * 2.2 - 4, -6.0 + rr.uniform(-0.6, 0.6), 0.9), (2.4, 3.5, rr.uniform(1.0, 2.6)), brick,
                rot=(R(rr.uniform(-25, 25)), R(rr.uniform(-30, 30)), R(rr.uniform(-20, 20))))
        box("wall_slab", (35, -8.5, 3.5), (12, 0.5, 8), brick, rot=(R(-58), 0, R(8)))
        AS.model("wooden_barrels_01", "1k", loc=(18, -2.4, 0.55), rot=(0, R(35), R(20)), scale=0.7)
        AS.model("wooden_crate_02", "1k", loc=(9, 2.2, 0.6), rot=(R(12), R(-8), R(40)), scale=1.4)
        for k in range(14):
            box(f"plank{k}", (rr.uniform(2, 50), rr.uniform(-4, 4), 0.98), (rr.uniform(1.5, 3.5), 0.25, 0.08),
                AS.texture("old_planks_02", "1k", scale=1.0, tint=(0.6, 0.45, 0.3)), rot=(0, 0, R(rr.uniform(0, 180))))
        aim((-8, -1.6, 2.3), (30, 0.6, 2.0), 24, 8.0)
        meta["surface_y_near"] = proj((0, 0, 0.95))[1]
        meta["surface_y_far"] = proj((30, 0, 0.95))[1]
    elif plate == "summer":
        aim((-6, -1.4, 1.6), (30, 0.6, 2.4), 24, 8.0)
        meta["ground_y"] = proj((0, 0, 0))[1]
    elif plate in ("tank", "burst"):
        g = box("yard", (0, -20, -0.1), (300, 120, 0.2), AS.texture("gravel_floor_02", "1k", scale=0.5, tint=(0.78, 0.78, 0.8)))
        harbor(-45)
        Rt, Ht = tank(0, -15, painted=1.0, burst=plate == "burst")
        for i, x in enumerate(range(-40, 41, 8)):   # the elevated railway passes the tank
            for y in (2.2, 3.9):
                box(f"ep{x}_{y}", (x, y + 6, 3.3), (0.38, 0.38, 6.6), steel)
        box("edeck", (0, 9.05, 6.75), (90, 2.6, 0.55), steel)
        TK.init(mat("glass2", (0.04, 0.05, 0.06), 0.08, emit=(1.0, 0.75, 0.45), estr=0.6),
                AS.texture("factory_brick", "1k", scale=3.0), AS.texture("grey_roof_tiles", "1k", scale=2.0), scale=1.0)
        for k, x in enumerate(range(-50, 60, 12)):
            TK.building(f"tb{k}", (x, 22), 0.0, floors=4 + k % 2, bays=3, wall=(0.9, 0.8, 0.75), shop=False, seed=500 + k)
        if plate == "burst":
            def zf(x, y):
                r = math.hypot(x, y + 15)
                if r < Rt - 0.5:
                    return 2.5
                d = 29 - r
                if d < -1.2:
                    return -0.4
                lead = min(1.0, (d + 1.2) / 1.2)
                return lead * (4.8 * math.exp(-((d - 3) / 3.5) ** 2) + 1.4) + 0.2 * math.sin(x * 0.8 + y)
            grid_surface("burstflood", -45, 45, -48, 18, 180, 130, zf, molasses())
            for k in range(70):
                a = rr.uniform(R(200), R(340))
                r = rr.uniform(Rt + 1, 30)
                bpy.ops.mesh.primitive_uv_sphere_add(radius=rr.uniform(0.15, 0.5), location=(r * math.cos(a), -15 + r * math.sin(a), rr.uniform(4, 11)))
                bpy.context.active_object.data.materials.append(molasses())
                bpy.ops.object.shade_smooth()
        aim((18, -55, 2.2), (0, -15, 9.5), 24)
        meta["tank_top"] = proj((0, -15, 16))
        meta["tank_base"] = proj((0, -28.5, 0))
    elif plate in ("tankclose", "tankbrown"):
        box("yard", (0, -20, -0.1), (200, 100, 0.2), AS.texture("cobblestone_floor_08", "2k", scale=0.55, tint=(0.6, 0.58, 0.56)))
        tank(0, 0, painted=1.0 if plate == "tankbrown" else 0.0, leaks=True)
        harbor(-60)
        aim((-6, -22.5, 1.4), (1, -10, 6.5), 22, 9.0)
        meta["ground_y"] = proj((-6, -19, 0))[1]
        meta["wall_base"] = proj((-3, -13.4, 0))
    elif plate == "harbor":
        harbor(-6, brown=True)
        box("quayland", (0, 20, -0.1), (300, 50, 0.2), pave)
        AS.model("dutch_ship_large_01", "1k", loc=(-26, -95, -1.5), rot=(0, 0, R(100)), scale=1.0)
        AS.model("wooden_barrels_01", "1k", loc=(7, -1.5, 0.0), rot=(0, 0, R(15)), scale=1.0)
        AS.model("wooden_crate_02", "1k", loc=(-6, -2, 0.0), rot=(0, 0, R(-12)), scale=1.6)
        AS.model("wooden_crate_01", "1k", loc=(-6, -2, 0.75), rot=(0, 0, R(8)), scale=1.6)
        for k, x in enumerate(range(-60, 70, 9)):
            box(f"bollard{k}", (x, -5.0, 0.4), (0.4, 0.4, 0.8), steel)
        aim((0, 9, 2.6), (-8, -60, 1.0), 24)
        meta["quay_y"] = proj((0, -4, 0))[1]
    elif plate == "court":
        wood = AS.texture("dark_wooden_planks", "1k", scale=0.8, tint=(0.75, 0.55, 0.38))
        box("floor", (0, 0, -0.1), (16, 22, 0.2), AS.texture("oak_wood_planks", "1k", scale=0.7))
        for x, y, sx, sy in ((0, 9, 16, 0.3), (-8, 0, 0.3, 22), (8, 0, 0.3, 22)):
            box(f"wall{x}{y}", (x, y, 4), (sx, sy, 8), mat("plaster", (0.36, 0.42, 0.36), 0.9))
            box(f"panel{x}{y}", (x * 0.995, y * 0.995, 1.3), (max(sx, 0.32), max(sy, 0.32), 2.6), wood)
        box("ceiling", (0, 0, 8.1), (16, 22, 0.2), mat("ceil", (0.85, 0.82, 0.75), 0.9))
        box("bench", (0, 6.6, 1.2), (7, 1.6, 2.4), wood)
        box("bench_top", (0, 6.4, 2.45), (7.4, 2.0, 0.12), wood)
        box("dais", (0, 7.2, 0.25), (9, 3.4, 0.5), wood)
        box("rail", (0, 1.0, 0.55), (12, 0.12, 1.1), wood)
        for x in (-3.5, 3.5):
            box(f"witness{x}", (x, 4.0, 0.6), (1.6, 1.2, 1.2), wood)
        for k in range(4):      # tall windows on the left wall, cold daylight through them
            y = -6 + k * 4.2
            box(f"win{k}", (-7.84, y, 4.6), (0.04, 1.8, 4.2), mat("winglass", (0.8, 0.88, 1.0), 0.1, emit=(0.8, 0.88, 1.0), estr=6.0))
            l = bpy.data.objects.new(f"winlight{k}", bpy.data.lights.new(f"winlight{k}", "AREA"))
            SC.collection.objects.link(l)
            l.location = (-7.6, y, 4.6)
            l.rotation_euler = (0, R(90), 0)
            l.data.energy, l.data.size, l.data.color = 900, 2.0, (0.85, 0.9, 1.0)
        f = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "AREA"))
        SC.collection.objects.link(f)
        f.location, f.rotation_euler = (2, -8, 6), (R(60), 0, 0)
        f.data.energy, f.data.size, f.data.color = 600, 6, (1.0, 0.85, 0.65)
        AS.model("vintage_oil_lamp", "1k", loc=(2.6, 6.2, 2.5), scale=0.55)
        AS.model("book_encyclopedia_set_01", "1k", loc=(-2.6, 6.3, 2.5), scale=0.25)
        for row in range(3):
            for x in (-4.5, 4.5):
                box(f"pew{row}{x}", (x, -2.5 - row * 2.2, 0.5), (5.5, 0.5, 1.0), wood)
                box(f"pewback{row}{x}", (x, -2.75 - row * 2.2, 1.05), (5.5, 0.12, 1.1), wood)
        for x in (-6.5, 6.5):
            box(f"column{x}", (x, 7.5, 4), (0.8, 0.8, 8), mat("colstone", (0.86, 0.82, 0.74), 0.7))
        box("seal", (0, 8.8, 5.2), (2.2, 0.1, 2.2), mat("seal", (0.75, 0.6, 0.25), 0.35, 0.8))
        w = bpy.data.worlds.new("w")
        SC.world = w
        w.use_nodes = True
        w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.02, 0.025, 1)
        aim((0.4, -5.0, 1.7), (0, 7.0, 2.6), 24, 6.0)
        meta["floor_y"] = proj((0, 0, 0))[1]
        meta["bench_top"] = proj((0, 6.4, 2.5))
    for o in bpy.data.objects:   # Poly Haven helper objects never render (LESSONS: the 1 m white "Sphere_stash")
        if o.name.startswith(("Sphere_stash", "wdg_", "rig_")):
            o.hide_render = True
    SC.render.engine = "CYCLES"
    SC.cycles.samples = SAMPLES
    SC.cycles.use_denoising = True
    SC.view_settings.view_transform = "AgX"
    SC.view_settings.look = "AgX - Medium High Contrast"
    SC.render.resolution_x, SC.render.resolution_y, SC.render.resolution_percentage = 1080, 1920, RES
    SC.render.filepath = os.path.join(OUTDIR, f"plate_{plate}.png")
    json.dump(meta, open(os.path.join(OUTDIR, f"plate_{plate}.json"), "w"))
    print("META", plate, meta, flush=True)
    bpy.ops.render.render(write_still=True)


for p in PLATES:
    build(p)
