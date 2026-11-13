"""The DailyMind asset library: CC0 Poly Haven models, PBR textures and HDRIs, downloaded once and cached.

    import dm_assets as AS
    objs = AS.model("vintage_pocket_watch", res="1k", loc=(0, 0, 0), scale=1.0)   # appended, grouped under an empty
    mat  = AS.texture("cobblestone_floor_08", res="2k", scale=4.0)                # Principled PBR material (box-mapped)
    AS.hdri("blaubeuren_night", res="2k", strength=0.6, rot_deg=120)            # world lighting

Cache: dailymind/assets_cache/ (git-ignored). Works the same on the RTX PC (it downloads what it lacks).
All Poly Haven assets are CC0 (public domain) — free for commercial use, no attribution required.
"""
import json
import os
import urllib.request

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("DM_ASSETS", os.path.join(os.path.dirname(HERE), "assets_cache"))
API = "https://api.polyhaven.com"
UA = {"User-Agent": "dailymind-studio/1.0"}


def _get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    part = f"{path}.{os.getpid()}.part"  # unique: parallel renders may fetch the same file
    with urllib.request.urlopen(req, timeout=120) as r, open(part, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    os.replace(part, path)
    return path


def _files(asset_id):
    p = os.path.join(CACHE, "_api", asset_id + ".json")
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        req = urllib.request.Request(f"{API}/files/{asset_id}", headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            open(p, "wb").write(r.read())
    return json.load(open(p))


def _link(o):
    sc = bpy.context.scene
    if o.name not in sc.collection.objects:
        sc.collection.objects.link(o)


def model(asset_id, res="1k", loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, name=None):
    """Append every object of a Poly Haven model; returns (root_empty, [objects]). Textures are downloaded next to it."""
    info = _files(asset_id)["blend"][res]["blend"]
    folder = os.path.join(CACHE, "models", asset_id, res)
    blend = _get(info["url"], os.path.join(folder, os.path.basename(info["url"])))
    for rel, inc in info.get("include", {}).items():
        _get(inc["url"], os.path.join(folder, rel))
    with bpy.data.libraries.load(blend, link=False) as (src, dst):
        dst.objects = list(src.objects)
    objs = [o for o in dst.objects if o is not None]
    root = bpy.data.objects.new(name or (asset_id + "_root"), None)
    _link(root)
    for o in objs:
        _link(o)
        if o.parent is None:
            o.parent = root
    root.location = loc
    root.rotation_euler = rot
    root.scale = (scale, scale, scale)
    for img in bpy.data.images:  # make texture paths absolute (the .blend uses //textures/...)
        if img.filepath.startswith("//textures"):
            img.filepath = os.path.join(folder, img.filepath[2:])
    return root, objs


def texture(asset_id, res="2k", scale=1.0, disp=0.0, tint=None, name=None, coords="Object"):
    """PBR material from a Poly Haven texture set, box-projected so it needs no UVs. scale = repeats per metre."""
    f = _files(asset_id)
    folder = os.path.join(CACHE, "textures", asset_id, res)

    def grab(key, ext="jpg"):
        if key not in f or res not in f[key]:
            return None
        e = ext if ext in f[key][res] else list(f[key][res])[0]
        u = f[key][res][e]["url"]
        return _get(u, os.path.join(folder, os.path.basename(u)))
    m = bpy.data.materials.new(name or asset_id)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs[coords], mp.inputs["Vector"])

    def img_node(path, non_color=False):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(path, check_existing=True)
        n.projection = "BOX"
        n.projection_blend = 0.25
        if non_color:
            n.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mp.outputs[0], n.inputs["Vector"])
        return n
    d = grab("Diffuse")
    if d:
        dn = img_node(d)
        if tint:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            mix.inputs[7].default_value = (*tint, 1)
            nt.links.new(dn.outputs["Color"], mix.inputs[6])
            nt.links.new(mix.outputs[2], p.inputs["Base Color"])
        else:
            nt.links.new(dn.outputs["Color"], p.inputs["Base Color"])
    r = grab("Rough")
    if r:
        nt.links.new(img_node(r, True).outputs["Color"], p.inputs["Roughness"])
    mt = grab("Metal")
    if mt:
        nt.links.new(img_node(mt, True).outputs["Color"], p.inputs["Metallic"])
    n = grab("nor_gl")
    if n:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(img_node(n, True).outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
    if disp:
        dp = grab("Displacement", "png")
        if dp:
            dd = nt.nodes.new("ShaderNodeDisplacement")
            dd.inputs["Scale"].default_value = disp
            nt.links.new(img_node(dp, True).outputs["Color"], dd.inputs["Height"])
            nt.links.new(dd.outputs[0], nt.nodes["Material Output"].inputs["Displacement"])
    return m


def hdri(asset_id, res="2k", strength=1.0, rot_deg=0.0):
    f = _files(asset_id)["hdri"][res]["hdr"]
    path = _get(f["url"], os.path.join(CACHE, "hdris", os.path.basename(f["url"])))
    w = bpy.data.worlds.new("hdri_" + asset_id)
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(path, check_existing=True)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    import math
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(rot_deg))
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs[0], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    return w


RIG_ZIPS = {  # Blender Studio character rigs, CC-BY 4.0 — credit "Rain & Snow rigs (c) Blender Foundation | studio.blender.org"
    "rain": "https://studio.blender.org/download-source/files/10/1033fad76f67bba3e362065d68c85791/1033fad76f67bba3e362065d68c85791.zip",
    "snow": "https://studio.blender.org/download-source/files/ca/cab3fc59bce48d1b8090109016ac16f0/cab3fc59bce48d1b8090109016ac16f0.zip",
}


def rig(name):
    """Folder of a downloaded + unzipped character rig (fetched once into the cache)."""
    import zipfile
    folder = os.path.join(CACHE, "rigs", name)
    if not (os.path.isdir(folder) and any(f.endswith(".blend") for f in os.listdir(folder))):
        z = _get(RIG_ZIPS[name], os.path.join(CACHE, "rigs", name + ".zip"))
        with zipfile.ZipFile(z) as zf:
            zf.extractall(folder)
    return folder
