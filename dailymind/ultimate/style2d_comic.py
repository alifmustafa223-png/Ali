"""Comic-book version of the 2D frame: posterized inks, halftone shading, speed lines, speech bubble, panel border.

  python style2d_comic.py FULL_FRAME.png OUT.png
"""
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

src, out = sys.argv[1], sys.argv[2]
fg = Image.open(sys.argv[3]).convert("RGBA") if len(sys.argv) > 3 else None   # optional character layer kept above the speed lines
im = Image.open(src).convert("RGB")
if fg is not None:
    full = im.convert("RGBA")
    full.alpha_composite(fg)
    im = full.convert("RGB")
W, H = im.size
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
post = ImageOps.posterize(im, 3).filter(ImageFilter.SMOOTH)
# halftone in the mid/dark tones
lum = np.array(im.convert("L")).astype(float)
dots = Image.new("L", (W, H), 255)
dd = ImageDraw.Draw(dots)
step = 14
for y in range(0, H, step):
    for x in range((y // step % 2) * step // 2, W, step):
        v = lum[min(H - 1, y), min(W - 1, x)]
        r = max(0.0, (120 - v) / 120) * step * 0.5
        if r > 1.2:
            dd.ellipse((x - r, y - r, x + r, y + r), fill=0)
a = np.array(post).astype(float) * (0.7 + 0.3 * np.array(dots)[..., None] / 255)
# heavier ink lines from edges
edges = np.array(im.convert("L").filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))).astype(float)
a = a * (1 - np.clip((edges - 40) / 80, 0, 1)[..., None] * 0.9)
comic = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(comic)
# speed lines radiating from her coin
cx, cy = 975, 1100
for k in range(48):
    ang = 2 * math.pi * k / 48
    r0, r1 = 130, 700
    d.line([(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang)), (cx + r1 * math.cos(ang), cy + r1 * math.sin(ang))], fill=(255, 240, 190), width=3)
comic = Image.blend(comic, Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), 0.55)
if fg is not None:  # characters (already inked/halftoned above) go back on top of the speed lines
    inked = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    inked.putalpha(fg.getchannel("A").filter(ImageFilter.MaxFilter(5)))
    comic = comic.convert("RGBA")
    comic.alpha_composite(inked)
    comic = comic.convert("RGB")
d = ImageDraw.Draw(comic)
# speech bubble from her
f = ImageFont.truetype(FONT, 58)
d.ellipse((470, 640, 1050, 900), fill=(255, 255, 255), outline=(10, 10, 10), width=8)
d.polygon([(860, 880), (930, 880), (950, 990)], fill=(255, 255, 255), outline=(10, 10, 10))
d.line([(866, 878), (924, 878)], fill=(255, 255, 255), width=10)
d.text((540, 700), "EVERY COIN...", font=f, fill=(10, 10, 10))
d.text((585, 775), "IS FAKE!", font=ImageFont.truetype(FONT, 76), fill=(220, 30, 40))
# his "?!" burst
burst = [(60 + 120 * math.cos(2 * math.pi * k / 20) * (1.0 if k % 2 else 0.6) + 120,
          820 + 120 * math.sin(2 * math.pi * k / 20) * (1.0 if k % 2 else 0.6)) for k in range(20)]
d.polygon(burst, fill=(255, 220, 40), outline=(10, 10, 10))
d.text((128, 760), "?!", font=ImageFont.truetype(FONT, 100), fill=(10, 10, 10))
# panel border
d.rectangle((0, 0, W - 1, H - 1), outline=(10, 10, 10), width=24)
d.rectangle((24, 24, W - 25, H - 25), outline=(255, 255, 255), width=6)
comic.save(out)
print("wrote", out)
