"""Thumbnail / cover for the Coca-Cola Short (1080x1920 PNG).

Usage (inside dailymind/ultimate): python thumb_cola.py ../cola/thumbnail.png
"""
import json
import math
import sys

out = sys.argv[1]
sys.argv = [sys.argv[0], "unused.mp4"]
import make_cola as M  # noqa: E402  (its __main__ block does not run on import)
from make_cola import *  # noqa: E402,F401,F403
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

plan = json.load(open("../cola/plan.json"))
M.CUE.update(plan["cues"])
M.CUE["d"] = plan["durs"]

T = 3.3  # a moment with the bottle glowing and the cork already flying


def art(c):
    M.pharmacy_bg(c, T, 540)
    glow(c, 540, 1250, 700, (255, 170, 90), 95)
    for k in range(14):  # light rays behind the bottle
        a = k / 14 * 2 * math.pi
        p = skia.Path()
        p.moveTo(540, 1250)
        p.lineTo(540 + math.cos(a) * 1300, 1250 + math.sin(a) * 1300)
        p.lineTo(540 + math.cos(a + 0.13) * 1300, 1250 + math.sin(a + 0.13) * 1300)
        p.close()
        c.drawPath(p, P(C(255, 210, 150, 26)))
    blob(c, rrect(0, 1640, W, 1760, 10), (120, 80, 45))
    c.drawRect(skia.Rect(0, 1760, W, H), P(C(80, 52, 30)))
    # shocked Pemberton on the right, pointing at the bottle
    pose = dict(hands=[(-150, -40), (40, 150)], eyes="wide", brows="up", mouth="O", look=(-1, 0), tilt=-6)
    person(c, 900, 1900, 1.25, M.PEMBERTON, pose, T)
    # the hero bottle, big and glowing, with fizz spraying out
    M.bottle(c, 470, 1700, 2.15, T, "MEDICINE", cork=False, glow_a=90)
    for j in range(18):
        a = math.radians(-90 + (j - 9) * 8)
        r = 160 + (j * 37) % 120
        c.drawCircle(470 + math.cos(a) * r, 1700 - 400 * 2.15 + math.sin(a) * r * 1.2, 10 + (j % 3) * 4, P(C(255, 225, 185, 220)))
    for j, (lx, ly, rot) in enumerate(((160, 1000, -30), (820, 980, 25), (250, 1450, 40), (700, 1180, -15), (120, 1300, 70))):
        M.leaf(c, lx, ly, 1.1, rot)
    for k in range(8):
        a = k / 8 * 2 * math.pi + 0.3
        sparkle(c, 470 + math.cos(a) * 330, 1300 + math.sin(a) * 420, 12, 230)


surf = skia.Surface(W, H)
c = surf.getCanvas()
art(c)
snap = surf.makeImageSnapshot()
c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=U.BLOOM, ImageFilter=skia.ImageFilters.Blur(24, 24), BlendMode=skia.BlendMode.kPlus, Alphaf=0.28))
c.drawPaint(P(Shader=rad(540, 1150, 1250, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 170)], [0, 0.55, 1])))
c.drawRect(skia.Rect(0, 0, W, 900), P(Shader=lin((0, 0), (0, 900), [C(5, 4, 10, 200), C(5, 4, 10, 0)])))
img = Image.fromarray(np.ascontiguousarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType))).convert("RGBA")


def big_text(img, text, y, size, fill, stroke=14, max_w=1000):
    f = font(FONT_B, size)
    d = ImageDraw.Draw(img)
    while d.textlength(text, font=f) > max_w and size > 40:
        size -= 4
        f = font(FONT_B, size)
    w = d.textlength(text, font=f)
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text(((W - w) / 2 + 8, y + 12), text, font=f, fill=(0, 0, 0, 200), stroke_width=stroke, stroke_fill=(0, 0, 0, 200))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10)))
    d.text(((W - w) / 2, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(20, 10, 10))
    return f.size


big_text(img, "COCA-COLA WAS", 150, 104, (255, 255, 255))
big_text(img, "MEDICINE?!", 290, 190, (255, 205, 60), stroke=18)
# red "WITH COCAINE" banner
d = ImageDraw.Draw(img, "RGBA")
f = font(FONT_B, 92)
label = "WITH COCAINE!"
tw = d.textlength(label, font=f)
bx0, by0 = (W - tw) / 2 - 40, 545
banner = Image.new("RGBA", img.size, (0, 0, 0, 0))
bd = ImageDraw.Draw(banner)
bd.rounded_rectangle([bx0, by0, bx0 + tw + 80, by0 + 130], radius=24, fill=(215, 35, 40, 245), outline=(255, 255, 255), width=8)
bd.text((bx0 + 40, by0 + 12), label, font=f, fill=(255, 255, 255))
img.alpha_composite(banner.rotate(-4, resample=Image.BICUBIC, center=(W / 2, by0 + 65)))
img.convert("RGB").save(out)
print("wrote", out)
