"""Cover for the airplane-windows Short (1080x1920). Usage (in dailymind/ultimate): python thumb_window.py ../window/thumbnail.png"""
import sys

out = sys.argv[1]
sys.argv = [sys.argv[0], "unused.mp4"]
import make_window as M  # noqa: E402
from make_window import *  # noqa: E402,F401,F403
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

T = 1.3
surf = skia.Surface(W, H)
c = surf.getCanvas()
M.bg(c, (12, 14, 30), (40, 45, 70))
c.drawRect(skia.Rect(0, 860, W, 1700), P(Shader=lin((0, 860), (0, 1700), [C(175, 180, 192), C(140, 146, 160)])))  # fuselage skin
for k in range(11):
    c.drawCircle(60 + k * 96, 900, 7, P(C(110, 115, 128)))
    c.drawCircle(60 + k * 96, 1660, 7, P(C(110, 115, 128)))


def window(cx, cy, r, sky_t):
    rr = skia.RRect.MakeRectXY(skia.Rect(cx - 180, cy - 250, cx + 180, cy + 250), r, r)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - 215, cy - 285, cx + 215, cy + 285), r + 30, r + 30), P(C(230, 228, 220)))
    c.save()
    c.clipRRect(rr, doAntiAlias=True)
    c.drawPaint(P(Shader=lin((0, cy - 250), (0, cy + 250), [C(80, 140, 230), C(255, 190, 140)])))
    M.cloud(c, cx - 30 + sky_t, cy, 1.1)
    c.restore()
    c.drawRRect(rr, S(C(120, 118, 112), 10))


window(290, 1280, 14, 0)
window(790, 1280, 150, 60)
# crack from the square window's corner
p = skia.Path()
x, y = 470, 1030
p.moveTo(x, y)
import random as _r
r_ = _r.Random(3)
for k in range(9):
    x += 26
    y -= 20 + r_.uniform(-12, 12)
    p.lineTo(x, y)
c.drawPath(p, S(C(20, 10, 10), 12))
c.drawPath(p, S(C(255, 120, 60), 4))
glow(c, 470, 1030, 140, (255, 70, 40), 230)
snap = surf.makeImageSnapshot()
c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=U.BLOOM, ImageFilter=skia.ImageFilters.Blur(24, 24), BlendMode=skia.BlendMode.kPlus, Alphaf=0.25))
c.drawPaint(P(Shader=rad(540, 1250, 1250, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 170)], [0, 0.55, 1])))
img = Image.fromarray(np.ascontiguousarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType))).convert("RGBA")


def big(img, text, y, size, fill, stroke=14, max_w=1000):
    d = ImageDraw.Draw(img)
    f = font(FONT_B, size)
    while d.textlength(text, font=f) > max_w:
        size -= 4
        f = font(FONT_B, size)
    w = d.textlength(text, font=f)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text(((W - w) / 2 + 8, y + 12), text, font=f, fill=(0, 0, 0, 200), stroke_width=stroke, stroke_fill=(0, 0, 0, 200))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d.text(((W - w) / 2, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(20, 10, 10))


big(img, "WHY PLANE WINDOWS", 150, 110, (255, 255, 255))
big(img, "ARE ROUND", 290, 150, (255, 205, 60), stroke=18)
d = ImageDraw.Draw(img, "RGBA")
f = font(FONT_B, 66)
label = "A DEADLY MISTAKE"
tw = d.textlength(label, font=f)
bx0, by0 = (W - tw) / 2 - 36, 500
banner = Image.new("RGBA", img.size, (0, 0, 0, 0))
bd = ImageDraw.Draw(banner)
bd.rounded_rectangle([bx0, by0, bx0 + tw + 72, by0 + 106], radius=24, fill=(225, 40, 50, 245), outline=(255, 255, 255), width=8)
bd.text((bx0 + 36, by0 + 12), label, font=f, fill=(255, 255, 255))
img.alpha_composite(banner.rotate(-3, resample=Image.BICUBIC, center=(W / 2, by0 + 53)))
# X and check marks under the windows
d = ImageDraw.Draw(img)
fx = font(FONT_B, 150)
for (x0, y0, x1, y1) in ((230, 1630, 350, 1750), (350, 1630, 230, 1750)):
    d.line([(x0, y0), (x1, y1)], fill=(20, 10, 10), width=46)
    d.line([(x0, y0), (x1, y1)], fill=(235, 60, 60), width=28)
d.text((790 - 55, 1600), "✓", font=fx, fill=(90, 210, 120), stroke_width=10, stroke_fill=(20, 10, 10))
img.convert("RGB").save(out)
print("wrote", out)
