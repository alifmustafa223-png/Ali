"""3D plates for "This Man Is Buried Inside a Chip Can" (Fred Baur, 1918-2008) - canary look.

  python pringles_plates.py -- OUTDIR [RES=60] [SAMPLES=64] [PLATES=grave,store,factory,home]
  ORBIT=1 python pringles_plates.py -- OUTDIR 45 20 graveorbit   -> OUTDIR/orbit/%04d.png (the hook's real 3D camera move)
Generic red chip can (no brand logo). Real scale (metres).
"""
import json
import math
import os
import random
import sys

import bpy
import mathutils
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:]
OUTDIR = argv[0]
RES = int(argv[1]) if len(argv) > 1 else 60
SAMPLES = int(argv[2]) if len(argv) > 2 else 64
PLATES = (argv[3] if len(argv) > 3 else "grave,store,factory,home").split(",")
ORBIT_FRAMES = int(os.environ.get("ORBIT_FRAMES", "110"))
os.makedirs(OUTDIR, exist_ok=True)
R = math.radians
V = mathutils.Vector
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"


def label_png(path, kind):
    """Painted textures made on the fly: the can label and the headstone engraving."""
    if kind == "can":
        im = Image.new("RGB", (1024, 512), (200, 22, 30))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 1024, 60), fill=(240, 236, 228))
        d.rectangle((0, 452, 1024, 512), fill=(240, 236, 228))
        f = ImageFont.truetype(FONT, 120)
        for x0 in (60, 572):
            d.ellipse((x0 + 90, 120, x0 + 300, 330), fill=(250, 205, 60))
            d.text((x0 + 20, 340), "CRISPS", font=ImageFont.truetype(FONT, 90), fill=(255, 255, 255))
    else:
        im = Image.new("RGB", (512, 640), (62, 62, 64))
        d = ImageDraw.Draw(im)
        f1, f2 = ImageFont.truetype(FONT, 44), ImageFont.truetype(FONT, 56)
        for txt, y, f in (("FREDRIC J.", 210, f1), ("BAUR", 270, f2), ("1918 - 2008", 360, f1)):
            w = d.textlength(txt, font=f)
            d.text(((512 - w) / 2 + 2, y + 2), txt, font=f, fill=(25, 25, 26))
            d.text(((512 - w) / 2, y), txt, font=f, fill=(225, 205, 150))
    im.save(path)
    return path


def build(plate):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import importlib
    import dm_assets as AS
    importlib.reload(AS)
    SC = bpy.context.scene
    rr = random.Random(7)
    meta = {}

    def mat(name, col, rough=0.5, metal=0.0, coat=0.0, emit=None, estr=0.0, img=None):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        p = nt.nodes["Principled BSDF"]
        p.inputs["Base Color"].default_value = (*col, 1)
        p.inputs["Roughness"].default_value = rough
        p.inputs["Metallic"].default_value = metal
        if coat:
            p.inputs["Coat Weight"].default_value = coat
        if emit:
            p.inputs["Emission Color"].default_value = (*emit, 1)
            p.inputs["Emission Strength"].default_value = estr
        if img:
            t = nt.nodes.new("ShaderNodeTexImage")
            t.image = bpy.data.images.load(img)
            nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
        return m

    def box(name, c, size, m, rot=(0, 0, 0), bevel=0.0):
        bpy.ops.mesh.primitive_cube_add(size=1, location=c, rotation=rot)
        o = bpy.context.active_object
        o.name = name
        o.scale = size
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if bevel:
            b = o.modifiers.new("b", "BEVEL")
            b.width, b.segments = bevel, 3
        o.data.materials.append(m)
        return o

    def can(loc, s=1.0, rot_z=0.0):
        """Generic stackable chip can: red tube with a printed label, silver lid, white rim."""
        img = label_png(os.path.join(OUTDIR, "_can_label.png"), "can")
        h, r = 0.25 * s, 0.038 * s
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=r, depth=h, location=(loc[0], loc[1], loc[2] + h / 2), rotation=(0, 0, rot_z))
        body = bpy.context.active_object
        bpy.ops.object.shade_smooth()
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.uv.cylinder_project(direction="ALIGN_TO_OBJECT", scale_to_bounds=True)
        bpy.ops.object.mode_set(mode="OBJECT")
        body.data.materials.append(mat("canlabel", (1, 1, 1), 0.25, coat=0.6, img=img))
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=r * 1.03, depth=0.012 * s, location=(loc[0], loc[1], loc[2] + h + 0.004 * s))
        bpy.context.active_object.data.materials.append(mat("lid", (0.85, 0.86, 0.88), 0.2, 1.0))
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.004 * s, location=(loc[0], loc[1], loc[2] + 0.003 * s))
        bpy.context.active_object.data.materials.append(mat("rim", (0.85, 0.86, 0.88), 0.2, 1.0))
        return body

    cd = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cd)
    SC.collection.objects.link(cam)
    SC.camera = cam

    def aim(loc, tgt, lens, fstop=None, focus=None):
        cam.location = loc
        cam.rotation_euler = (V(tgt) - V(loc)).to_track_quat("-Z", "Y").to_euler()
        cd.lens = lens
        if fstop:
            cd.dof.use_dof = True
            cd.dof.aperture_fstop = fstop
            cd.dof.focus_distance = (V(focus or tgt) - V(loc)).length

    def proj(p):
        from bpy_extras.object_utils import world_to_camera_view
        bpy.context.view_layer.update()
        q = world_to_camera_view(SC, cam, V(p))
        return [round(q.x * 1080, 1), round((1 - q.y) * 1920, 1)]

    def light(kind, loc, energy, col, size=0.5, aim_at=None):
        o = bpy.data.objects.new(kind, bpy.data.lights.new(kind, kind))
        SC.collection.objects.link(o)
        o.location = loc
        o.data.energy, o.data.color = energy, col
        if kind == "AREA":
            o.data.size = size
        elif kind == "POINT":
            o.data.shadow_soft_size = size
        if aim_at:
            o.rotation_euler = (V(aim_at) - V(loc)).to_track_quat("-Z", "Y").to_euler()
        return o

    if plate in ("grave", "graveorbit"):
        AS.hdri("belfast_sunset_puresky", "2k", 0.45, 200)
        sun = light("SUN", (0, 0, 10), 2.4, (1.0, 0.62, 0.38))
        sun.rotation_euler = (R(78), 0, R(150))
        grass = AS.texture("aerial_grass_rock", "1k", scale=0.6, tint=(0.55, 0.62, 0.4))
        box("ground", (0, 0, -0.05), (80, 80, 0.1), grass)
        stone = mat("granite", (0.13, 0.13, 0.135), 0.45)
        gn = stone.node_tree
        nz = gn.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 40
        bm = gn.nodes.new("ShaderNodeBump")
        bm.inputs["Strength"].default_value = 0.15
        gn.links.new(nz.outputs["Fac"], bm.inputs["Height"])
        gn.links.new(bm.outputs["Normal"], gn.nodes["Principled BSDF"].inputs["Normal"])
        eng = label_png(os.path.join(OUTDIR, "_headstone.png"), "stone")
        # Fred's headstone (engraved face), grave slab, the chip can on the slab
        hs = box("headstone", (0, 0.9, 0.55), (0.9, 0.18, 1.1), stone, bevel=0.03)
        face = box("hs_face", (0, 0.805, 0.55), (0.8, 0.005, 0.95), mat("engrave", (1, 1, 1), 0.85, img=eng))
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.uv.cube_project(scale_to_bounds=True)
        bpy.ops.object.mode_set(mode="OBJECT")
        box("slab", (0, 0.05, 0.08), (1.0, 1.7, 0.16), stone, bevel=0.02)
        can((0.0, 0.25, 0.16), s=1.6)
        for k in range(0):    # (ball flowers read as eggs: removed)
            x, y = rr.uniform(-0.42, 0.42), rr.uniform(-0.65, 0.65)
            if abs(x) < 0.12 and abs(y - 0.25) < 0.12:
                continue
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(x, y, 0.19))
            bpy.context.active_object.data.materials.append(mat(f"fl{k}", rr.choice([(0.9, 0.85, 0.2), (0.85, 0.2, 0.25), (0.95, 0.95, 0.9)]), 0.6))
        candle = mat("candle", (0.95, 0.92, 0.85), 0.5, emit=(1.0, 0.7, 0.35), estr=4.0)
        for x in (-0.35, 0.35):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.12, location=(x, 0.6, 0.22))
            bpy.context.active_object.data.materials.append(candle)
            light("POINT", (x, 0.6, 0.32), 4.0, (1.0, 0.65, 0.3), 0.02)
        for k in range(26):    # rows of other headstones fading into the dusk
            x = -9 + (k % 9) * 2.3 + rr.uniform(-0.3, 0.3)
            y = 3.5 + (k // 9) * 3.2 + rr.uniform(-0.3, 0.3)
            hgt = rr.uniform(0.6, 1.2)
            box(f"stone{k}", (x, y, hgt / 2), (rr.uniform(0.5, 0.8), 0.16, hgt), stone, rot=(0, R(rr.uniform(-4, 4)), R(rr.uniform(-8, 8))), bevel=0.03)
        for k in range(5):
            AS.model("dead_tree_trunk", "1k", loc=(rr.uniform(-12, 12), rr.uniform(10, 18), 0), rot=(R(90), 0, R(rr.uniform(0, 360))), scale=2.5)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 8, 1.2))
        fog = bpy.context.active_object
        fog.scale = (40, 30, 2.4)
        fm = bpy.data.materials.new("fog")
        fm.use_nodes = True
        fm.node_tree.nodes.remove(fm.node_tree.nodes["Principled BSDF"])
        vol = fm.node_tree.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Density"].default_value = 0.012
        vol.inputs["Color"].default_value = (1.0, 0.85, 0.75, 1)
        fm.node_tree.links.new(vol.outputs[0], fm.node_tree.nodes["Material Output"].inputs["Volume"])
        fog.data.materials.append(fm)
        light("AREA", (1.2, -1.5, 1.2), 25, (1.0, 0.8, 0.6), 1.0, aim_at=(0, 0.25, 0.4))
        aim((0.55, -2.6, 0.9), (0, 0.55, 0.55), 30, 4.0, (0, 0.25, 0.35))
        meta["can"] = proj((0, 0.25, 0.36))
        meta["ground_y"] = proj((0, -1.4, 0))[1]
        meta["slab_front_y"] = proj((0, -0.8, 0.16))[1]
    elif plate == "store":
        AS.hdri("artist_workshop", "2k", 0.5, 0)
        floor = mat("checker", (1, 1, 1), 0.35)
        nt = floor.node_tree
        ch = nt.nodes.new("ShaderNodeTexChecker")
        ch.inputs["Scale"].default_value = 20.0
        ch.inputs["Color1"].default_value = (0.85, 0.82, 0.74, 1)
        ch.inputs["Color2"].default_value = (0.25, 0.32, 0.3, 1)
        nt.links.new(ch.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
        box("floor", (0, 0, -0.05), (12, 12, 0.1), floor)
        box("wall", (0, 3.2, 1.75), (12, 0.2, 3.5), mat("storewall", (0.7, 0.62, 0.46), 0.8))
        box("ceiling", (0, 0, 3.3), (12, 12, 0.1), mat("ceil", (0.8, 0.76, 0.66), 0.9))
        wood = AS.texture("brown_planks_05", "1k", scale=1.0, tint=(0.8, 0.6, 0.42))
        cols = [(0.8, 0.55, 0.05), (0.08, 0.25, 0.6), (0.65, 0.08, 0.06), (0.12, 0.42, 0.16), (0.8, 0.35, 0.05)]
        for side in (-1,):
            box("shelfback", (0, 2.9, 1.1), (5.0, 0.1, 2.2), wood)
            for lvl in range(4):
                z = 0.2 + lvl * 0.55
                box(f"shelf{lvl}", (0, 2.6, z), (5.0, 0.6, 0.04), wood)
                x = -2.3
                while x < 2.3:    # puffy chip bags (pillow shapes), slightly different sizes and colours
                    w = rr.uniform(0.26, 0.34)
                    col = cols[rr.randrange(len(cols))]
                    o = box(f"bag{lvl}_{x:.2f}", (x + w / 2, 2.6, z + 0.21), (w, 0.14, 0.36), mat(f"bag{lvl}_{x:.2f}", col, 0.22, coat=0.6))
                    bv = o.modifiers.new("bv", "BEVEL")
                    bv.width, bv.segments = 0.04, 4
                    for zz in (z + 0.035, z + 0.385):   # crimped seals top and bottom
                        box(f"seal{lvl}_{x:.2f}_{zz:.2f}", (x + w / 2, 2.6, zz), (w * 0.95, 0.03, 0.03), mat("seal", tuple(c * 0.75 for c in col), 0.3))
                    x += w + 0.02
        for x in (-1.5, 0, 1.5):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.05, location=(x, 1.2, 3.1))
            bpy.context.active_object.data.materials.append(mat("lampshade", (0.95, 0.95, 0.9), 0.3, emit=(1.0, 0.95, 0.85), estr=8))
            light("POINT", (x, 1.2, 2.8), 140, (1.0, 0.9, 0.75), 0.3)
        aim((0.2, -2.2, 1.5), (0, 2.6, 1.1), 26, 5.0)
        meta["floor_y"] = proj((0, 0.5, 0))[1]
        meta["shelf_mid"] = proj((0, 2.6, 0.95))
    elif plate == "factory":
        AS.hdri("boiler_room", "2k", 0.6, 0)
        metal = AS.texture("metal_plate", "1k", scale=1.0, tint=(0.6, 0.62, 0.65)) if False else mat("floorm", (0.28, 0.29, 0.3), 0.45, 0.6)
        box("floor", (0, 0, -0.05), (30, 30, 0.1), metal)
        brick = AS.texture("factory_brick", "1k", scale=0.5, tint=(0.75, 0.65, 0.6))
        box("backwall", (0, 4.5, 2.5), (30, 0.3, 5), brick)
        box("sidewall", (-6, 0, 2.5), (0.3, 30, 5), brick)
        box("ceiling", (0, 0, 4.6), (30, 30, 0.2), mat("fceil", (0.2, 0.2, 0.22), 0.8))
        belt = mat("belt", (0.08, 0.08, 0.09), 0.7)
        steel = mat("steel", (0.55, 0.57, 0.6), 0.3, 0.9)
        box("belt", (0, 1.5, 0.9), (12, 0.8, 0.06), belt)
        box("frame_l", (0, 1.08, 0.82), (12, 0.06, 0.14), steel)
        box("frame_r", (0, 1.92, 0.82), (12, 0.06, 0.14), steel)
        for x in range(-6, 7):
            for y in (1.1, 1.9):
                box(f"leg{x}{y}", (x, y, 0.4), (0.08, 0.08, 0.8), steel)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.8, location=(x, 1.5, 0.86), rotation=(R(90), 0, 0))
            bpy.context.active_object.data.materials.append(steel)
        AS.model("modular_industrial_pipes_01", "1k", loc=(-3, 5.4, 0), scale=1.0)
        for x in (-3, 0, 3):
            AS.model("hanging_industrial_lamp", "1k", loc=(x, 1.5, 4.5), scale=0.8)
            light("POINT", (x, 1.5, 2.3), 250, (1.0, 0.85, 0.6), 0.2)
        for k in range(10):   # rows of finished red cans waiting at the end of the line
            can((3.2 + (k % 5) * 0.12, 1.3 + (k // 5) * 0.12, 0.93), s=1.0)
        aim((-0.9, -0.2, 1.35), (0.9, 1.5, 0.95), 24, 5.6)
        meta["belt_left"] = proj((-2.5, 1.5, 0.93))
        meta["belt_right"] = proj((2.5, 1.5, 0.93))
        meta["floor_y"] = proj((-0.5, 0.0, 0))[1]
    elif plate == "home":
        AS.hdri("artist_workshop", "2k", 0.35, 0)
        box("floor", (0, 0, -0.05), (10, 10, 0.1), AS.texture("oak_wood_planks", "1k", scale=0.8))
        paper = mat("wallpaper", (1, 1, 1), 0.8)
        nt = paper.node_tree
        wv = nt.nodes.new("ShaderNodeTexWave")
        wv.inputs["Scale"].default_value = 6
        rp = nt.nodes.new("ShaderNodeValToRGB")
        rp.color_ramp.elements[0].color = (0.62, 0.5, 0.36, 1)
        rp.color_ramp.elements[1].color = (0.72, 0.6, 0.44, 1)
        nt.links.new(wv.outputs["Fac"], rp.inputs["Fac"])
        nt.links.new(rp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
        box("wall", (0, 3.0, 1.75), (10, 0.2, 3.5), paper)
        box("wall_l", (-3.2, 0, 1.75), (0.2, 10, 3.5), paper)
        box("ceiling", (0, 0, 3.4), (10, 10, 0.1), mat("hceil", (0.85, 0.8, 0.72), 0.9))
        sofa = mat("sofa", (0.45, 0.22, 0.18), 0.85)
        box("sofa_seat", (0.4, 2.3, 0.3), (2.2, 0.8, 0.4), sofa, bevel=0.08)
        box("sofa_back", (0.4, 2.7, 0.75), (2.2, 0.25, 0.8), sofa, bevel=0.08)
        for x in (-0.75, 1.55):
            box(f"arm{x}", (x, 2.3, 0.55), (0.25, 0.8, 0.5), sofa, bevel=0.08)
        AS.model("vintage_grandfather_clock_01", "1k", loc=(-2.4, 2.6, 0), scale=1.0)
        AS.model("wooden_bookshelf_worn", "1k", loc=(2.6, 2.75, 0), scale=1.0)
        AS.model("vintage_oil_lamp", "1k", loc=(1.9, 2.3, 0.5), scale=0.6)
        box("sidetable", (1.9, 2.3, 0.25), (0.5, 0.5, 0.5), AS.texture("brown_planks_05", "1k", scale=1.0))
        for k in range(3):    # framed family photos
            box(f"frame{k}", (-0.8 + k * 0.9, 2.88, 1.75), (0.5, 0.04, 0.4), mat(f"fr{k}", (0.4, 0.28, 0.15), 0.4))
            box(f"photo{k}", (-0.8 + k * 0.9, 2.86, 1.75), (0.4, 0.02, 0.3), mat(f"ph{k}", (0.7, 0.66, 0.58), 0.7))
        light("POINT", (1.9, 2.3, 1.3), 120, (1.0, 0.75, 0.45), 0.15)
        light("AREA", (-1.5, -1.8, 2.4), 260, (1.0, 0.85, 0.7), 2.0, aim_at=(0.2, 2.0, 0.8))
        aim((0.2, -2.6, 1.4), (0.2, 2.4, 1.1), 26, 5.0)
        meta["floor_y"] = proj((0, 0.4, 0))[1]
    for o in bpy.data.objects:
        if o.name.startswith(("Sphere_stash", "wdg_", "rig_")):
            o.hide_render = True
    SC.render.engine = "CYCLES"
    SC.cycles.samples = SAMPLES
    SC.cycles.use_denoising = True
    SC.cycles.volume_bounces = 1
    SC.view_settings.view_transform = "AgX"
    SC.view_settings.look = "AgX - Medium High Contrast"
    SC.view_settings.exposure = {"store": -0.9, "home": -0.4, "factory": -0.3, "grave": -0.8, "graveorbit": -0.8}.get(plate, 0.0)
    SC.render.resolution_x, SC.render.resolution_y, SC.render.resolution_percentage = 1080, 1920, RES
    if plate == "graveorbit":
        # the hook: a slow 40-degree orbit around the can, pushing in and dropping toward it (one eased move, no stops)
        od = os.path.join(OUTDIR, "orbit")
        os.makedirs(od, exist_ok=True)
        tgt = V((0, 0.25, 0.4))
        track = []
        for f in range(ORBIT_FRAMES):
            u = f / (ORBIT_FRAMES - 1)
            e = u * u * (3 - 2 * u)
            a = R(-30 + 40 * e)
            r = 2.7 - 1.0 * e
            loc = (tgt.x + r * math.sin(a), tgt.y - r * math.cos(a), 0.95 - 0.3 * e)
            aim(loc, (0, 0.45, 0.5 - 0.05 * e), 30, 4.0, (0, 0.25, 0.35))
            out = os.path.join(od, f"{f + 1:04d}.png")
            track.append(dict(f=f, can=proj((0, 0.25, 0.36)), ground_y=proj((0, -1.4, 0))[1]))
            if not os.path.exists(out):
                SC.render.filepath = out
                bpy.ops.render.render(write_still=True)
        json.dump(track, open(os.path.join(od, "track.json"), "w"))
        return
    SC.render.filepath = os.path.join(OUTDIR, f"plate_{plate}.png")
    json.dump(meta, open(os.path.join(OUTDIR, f"plate_{plate}.json"), "w"))
    print("META", plate, meta, flush=True)
    bpy.ops.render.render(write_still=True)


for p in PLATES:
    build(p)
