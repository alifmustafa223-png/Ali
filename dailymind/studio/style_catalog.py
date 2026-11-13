"""Catalog of 2D looks we can produce in code: one subject (a lighthouse by the sea at dusk), many styles.

  python style_catalog.py OUTDIR      -> OUTDIR/<style>.png (540x960 each)
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/styles2d"
os.makedirs(OUT, exist_ok=True)
W, H = 540, 960
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"


def lerp(a, b, k):
    return tuple(int(x + (y - x) * k) for x, y in zip(a, b))


def vgrad(top, bot, h=H, w=W):
    a = np.linspace(0, 1, h)[:, None, None]
    return Image.fromarray((np.array(top)[None, None] * (1 - a) + np.array(bot)[None, None] * a).repeat(w, 1).astype(np.uint8))


def scene(d, pal, outline=None, ow=0, rough=0.0, seed=1):
    """Draw the subject with a palette dict: sky handled by caller. Shapes: far hills, cliff, lighthouse, beam, sea, boat."""
    rr = random.Random(seed)

    def j(p):
        return (p[0] + rr.uniform(-rough, rough), p[1] + rr.uniform(-rough, rough))

    def poly(pts, fill):
        pts = [j(p) for p in pts]
        d.polygon(pts, fill=fill, outline=outline, width=ow) if outline else d.polygon(pts, fill=fill)

    # moon / sun
    d.ellipse((360, 150, 450, 240), fill=pal["sun"], outline=outline, width=ow)
    # far hills
    poly([(0, 560)] + [(x, 520 - 40 * math.sin(x / 70) - 25 * math.sin(x / 31)) for x in range(0, W + 1, 30)] + [(W, 560)], pal["hill"])
    # sea
    poly([(0, 560), (W, 560), (W, H), (0, H)], pal["sea"])
    for k in range(10):  # wave lines
        y = 600 + k * 34
        d.line([j((x, y + 5 * math.sin(x / 25 + k))) for x in range(0, W + 1, 20)], fill=pal["wave"], width=max(2, ow or 3))
    # cliff
    poly([(0, 960), (0, 610), (60, 585), (150, 575), (250, 600), (300, 650), (330, 760), (360, 960)], pal["cliff"])
    # beam of light
    beam = [(205, 382), (W + 40, 260), (W + 40, 470)]
    d.polygon(beam, fill=pal["beam"])
    # lighthouse: tapered tower with stripes, gallery, lantern, roof
    x0b, x1b, x0t, x1t, yb, yt = 160, 250, 178, 232, 590, 400
    poly([(x0b, yb), (x1b, yb), (x1t, yt), (x0t, yt)], pal["tower"])
    for k in range(3):
        y0 = yt + 30 + k * 60
        f0, f1 = (y0 - yt) / (yb - yt), (y0 + 28 - yt) / (yb - yt)
        poly([(x0t + (x0b - x0t) * f0, y0), (x1t + (x1b - x1t) * f0, y0), (x1t + (x1b - x1t) * f1, y0 + 28), (x0t + (x0b - x0t) * f1, y0 + 28)],
             pal["stripe"])
    poly([(168, 400), (242, 400), (242, 388), (168, 388)], pal["dark"])
    poly([(182, 388), (228, 388), (228, 350), (182, 350)], pal["lamp"])
    poly([(176, 350), (234, 350), (205, 318)], pal["dark"])
    poly([(195, 590), (215, 590), (215, 560), (195, 560)], pal["dark"])   # door
    # little boat
    poly([(380, 700), (470, 700), (455, 720), (395, 720)], pal["dark"])
    poly([(422, 700), (422, 640), (455, 700)], pal["sail"])
    # stars
    for k in range(25):
        x, y = rr.uniform(10, W - 10), rr.uniform(20, 330)
        r = rr.uniform(1, 2.5)
        d.ellipse((x - r, y - r, x + r, y + r), fill=pal["star"])


DUSK = dict(sun=(255, 214, 140), hill=(88, 70, 120), sea=(30, 60, 110), wave=(70, 110, 170), cliff=(52, 42, 60), beam=(255, 236, 170),
            tower=(240, 236, 228), stripe=(210, 60, 60), dark=(40, 34, 48), lamp=(255, 220, 120), sail=(245, 240, 230), star=(255, 255, 230))


def base(pal=DUSK, sky=((40, 30, 80), (250, 140, 110)), outline=None, ow=0, rough=0.0, seed=1):
    im = vgrad(*sky).convert("RGB")
    scene(ImageDraw.Draw(im, "RGBA"), pal, outline, ow, rough, seed)
    return im


def noise(h=H, w=W, s=1.0, seed=0):
    return np.random.default_rng(seed).normal(0, s, (h, w))


def save(name, im):
    im.convert("RGB").resize((W, H)).save(os.path.join(OUT, name + ".png"))


# 1 flat vector
save("flat_vector", base())
# 2 paper cut-out: each layer a flat colour with a soft drop shadow + paper fibre texture
im = base()
edges = im.filter(ImageFilter.FIND_EDGES).convert("L").point(lambda v: 255 if v > 18 else 0)
shadow = ImageChops.offset(edges, 4, 6).filter(ImageFilter.GaussianBlur(4))
arr = np.array(im).astype(float) - np.array(shadow)[..., None] * 0.35
arr += noise(s=6)[..., None] + (np.array(Image.fromarray((np.random.default_rng(3).random((H // 3, W // 3)) * 255).astype(np.uint8))
                                         .resize((W, H)).filter(ImageFilter.GaussianBlur(2))) - 128)[..., None] * 0.08
save("paper_cutout", Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)))
# 3 pixel art
small = base(rough=0).resize((90, 160), Image.BILINEAR).quantize(24, dither=Image.Dither.NONE).convert("RGB")
save("pixel_art", small.resize((W, H), Image.NEAREST))
# 4 synthwave neon
im = vgrad((10, 0, 40), (120, 20, 120)).convert("RGB")
d = ImageDraw.Draw(im)
for k in range(9):  # striped sun
    y0 = 180 + k * 22
    d.ellipse((150, 140, 390, 380), fill=None)
sun = Image.new("L", (W, H), 0)
ImageDraw.Draw(sun).ellipse((140, 150, 400, 410), fill=255)
for k in range(8):
    ImageDraw.Draw(sun).rectangle((0, 300 + k * 14, W, 304 + k * 14 + k), fill=0)
sun_col = vgrad((255, 230, 80), (255, 40, 140)).convert("RGB")
im.paste(sun_col, (0, 0), sun)
glow = Image.new("RGB", (W, H))
gd = ImageDraw.Draw(glow)
for x in range(-600, 1200, 60):
    gd.line([(W / 2 + (x - W / 2) * 0.15, 560), (x, H)], fill=(255, 60, 220), width=3)
for k in range(12):
    y = 560 + (k / 12) ** 2 * 400
    gd.line([(0, y), (W, y)], fill=(255, 60, 220), width=3)
neon = (0, 255, 255)
gd.polygon([(160, 560), (250, 560), (232, 400), (178, 400)], outline=neon, width=5)
gd.polygon([(176, 350), (234, 350), (205, 318)], outline=neon, width=5)
gd.rectangle((182, 350, 228, 388), outline=(255, 240, 120), width=5)
gd.polygon([(205, 370), (W + 40, 280), (W + 40, 450)], outline=(255, 240, 120), width=3)
im = ImageChops.add(im, glow.filter(ImageFilter.GaussianBlur(6)))
im = ImageChops.add(im, glow)
save("synthwave_neon", im)
# 5 watercolor
im = base(rough=3, seed=4).filter(ImageFilter.GaussianBlur(2.5))
a = np.array(im).astype(float)
edge = np.array(im.filter(ImageFilter.FIND_EDGES).convert("L").filter(ImageFilter.GaussianBlur(1.5))).astype(float)
a = a * (1 - edge[..., None] / 400)                         # pigment pooling at edges
paper = np.array(Image.fromarray((np.random.default_rng(9).random((H // 4, W // 4)) * 255).astype(np.uint8)).resize((W, H)).filter(
    ImageFilter.GaussianBlur(3))).astype(float)
a = a * (0.9 + 0.1 * paper[..., None] / 255) + 255 * 0.12   # paper grain + lighter washes
a += noise(s=4, seed=2)[..., None]
save("watercolor", Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
# 6 comic / halftone
im = base(outline=(10, 10, 10), ow=5)
post = ImageOps.posterize(im, 3)
dots = Image.new("L", (W, H), 255)
dd = ImageDraw.Draw(dots)
lum = np.array(im.convert("L"))
for y in range(0, H, 10):
    for x in range(0, W, 10):
        r = (1 - lum[y, x] / 255) * 5
        if r > 0.6:
            dd.ellipse((x - r, y - r, x + r, y + r), fill=0)
comic = Image.composite(post, ImageChops.multiply(post, Image.merge("RGB", [dots] * 3)), Image.new("L", (W, H), 150))
cd = ImageDraw.Draw(comic)
cd.rounded_rectangle((30, 40, 330, 150), 30, fill=(255, 255, 255), outline=(0, 0, 0), width=5)
cd.polygon([(120, 148), (170, 148), (150, 200)], fill=(255, 255, 255), outline=(0, 0, 0))
cd.text((52, 70), "THE LIGHT\nNEVER WENT OUT!", font=ImageFont.truetype(FONT, 30), fill=(0, 0, 0))
save("comic_halftone", comic)
# 7 blueprint
im = Image.new("RGB", (W, H), (18, 60, 130))
d = ImageDraw.Draw(im)
for x in range(0, W, 20):
    d.line([(x, 0), (x, H)], fill=(40, 90, 165) if x % 100 else (70, 120, 190), width=1)
for y in range(0, H, 20):
    d.line([(0, y), (W, y)], fill=(40, 90, 165) if y % 100 else (70, 120, 190), width=1)
scene(d, {k: None for k in DUSK} | {"wave": (220, 235, 255), "star": (18, 60, 130)}, outline=(230, 240, 255), ow=2)
d.line([(120, 400), (120, 590)], fill=(230, 240, 255), width=1)
d.text((40, 480), "42 m", font=ImageFont.truetype(FONT, 22), fill=(230, 240, 255))
d.text((30, 880), "LIGHTHOUSE  |  ELEVATION A-A  |  1:200", font=ImageFont.truetype(FONT, 18), fill=(230, 240, 255))
save("blueprint", im)
# 8 chalkboard doodle
im = Image.new("RGB", (W, H), (34, 52, 44))
d = ImageDraw.Draw(im)
scene(d, {k: None for k in DUSK} | {"wave": (235, 235, 225), "star": (235, 235, 225)}, outline=(235, 235, 225), ow=4, rough=3.5, seed=7)
a = np.array(im).astype(float) + noise(s=10, seed=5)[..., None]
a = np.array(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))).astype(float)
save("chalkboard", Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
# 9 silhouette at sunset
sil = {k: (12, 8, 18) for k in DUSK} | {"sun": (255, 200, 120), "beam": (255, 220, 150, 120), "lamp": (255, 230, 150), "star": (255, 230, 200),
                                         "sea": (60, 30, 50), "wave": (230, 120, 90)}
im = vgrad((80, 20, 70), (255, 150, 70)).convert("RGB")
scene(ImageDraw.Draw(im, "RGBA"), sil)
save("silhouette", im)
# 10 film noir
im = base().convert("L")
a = np.array(ImageOps.autocontrast(im, cutoff=2)).astype(float)
yy, xx = np.mgrid[0:H, 0:W]
vig = 1 - 0.55 * (((xx - W / 2) / (W / 1.4)) ** 2 + ((yy - H / 2) / (H / 1.4)) ** 2)
a = a * vig + noise(s=14, seed=8)
save("film_noir", Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGB"))
# 11 ink & watercolor storybook (outlined + soft washes)
im = base(outline=(50, 35, 30), ow=3, rough=1.5, seed=11).filter(ImageFilter.SMOOTH_MORE)
a = np.array(im).astype(float) * 0.85 + np.array([255, 240, 215]) * 0.15
save("storybook", Image.fromarray(np.clip(a + noise(s=5, seed=12)[..., None], 0, 255).astype(np.uint8)))
# 12 vintage poster (limited palette, grain, border, title)
vint = {k: v for k, v in DUSK.items()} | {"hill": (60, 90, 100), "sea": (30, 70, 90), "wave": (70, 120, 130), "cliff": (40, 50, 55),
                                          "tower": (240, 228, 200), "stripe": (200, 80, 50)}
im = base(vint, sky=((235, 200, 140), (230, 120, 70)))
im = ImageOps.posterize(im, 4)
d = ImageDraw.Draw(im)
d.rectangle((14, 14, W - 14, H - 14), outline=(245, 235, 210), width=10)
f = ImageFont.truetype(FONT, 54)
d.text((W / 2 - d.textlength("CAPE NORTH", font=f) / 2, 40), "CAPE NORTH", font=f, fill=(245, 235, 210))
a = np.array(im).astype(float) + noise(s=9, seed=13)[..., None]
save("vintage_poster", Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
print("wrote", sorted(os.listdir(OUT)))
