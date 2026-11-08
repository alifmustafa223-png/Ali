"""Cover for the purple Short (1080x1920). Usage (in dailymind/ultimate): python thumb_purple.py ../purple/thumbnail.png"""
import sys

out = sys.argv[1]
sys.argv = [sys.argv[0], "unused.mp4"]
import make_purple as M  # noqa: E402
from make_purple import *  # noqa: E402,F401,F403
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

M.CUE.update(gold=0.0, snail=0.0)
T = 2.0
surf = skia.Surface(W, H)
c = surf.getCanvas()
M.bg_dark(c, (30, 10, 45), (70, 25, 95))
for k in range(16):
    a = k / 16 * 2 * math.pi
    p = skia.Path()
    p.moveTo(540, 1300)
    p.lineTo(540 + math.cos(a) * 1500, 1300 + math.sin(a) * 1500)
    p.lineTo(540 + math.cos(a + 0.12) * 1500, 1300 + math.sin(a + 0.12) * 1500)
    p.close()
    c.drawPath(p, P(C(230, 170, 255, 20)))
c.drawRect(skia.Rect(0, 1700, W, H), P(C(50, 20, 60)))
M.scale_balance(c, 540, 1640, 1.35, T, 1.0, lambda cc: M.silk(cc, 190, 120, T), M.gold_bars)
glow(c, 540 - 380, 1300, 300, (200, 120, 255), 120)
M.snail(c, 840, 1760, 1.15, T)
snap = surf.makeImageSnapshot()
c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=U.BLOOM, ImageFilter=skia.ImageFilters.Blur(24, 24), BlendMode=skia.BlendMode.kPlus, Alphaf=0.3))
c.drawPaint(P(Shader=rad(540, 1150, 1250, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 170)], [0, 0.55, 1])))
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


big(img, "PURPLE WAS WORTH", 150, 100, (255, 255, 255))
big(img, "MORE THAN GOLD?!", 280, 140, (255, 205, 60), stroke=18)
d = ImageDraw.Draw(img, "RGBA")
f = font(FONT_B, 88)
label = "MADE FROM SNAILS"
tw = d.textlength(label, font=f)
bx0, by0 = (W - tw) / 2 - 40, 500
banner = Image.new("RGBA", img.size, (0, 0, 0, 0))
bd = ImageDraw.Draw(banner)
bd.rounded_rectangle([bx0, by0, bx0 + tw + 80, by0 + 126], radius=24, fill=(150, 50, 210, 245), outline=(255, 255, 255), width=8)
bd.text((bx0 + 40, by0 + 12), label, font=f, fill=(255, 255, 255))
img.alpha_composite(banner.rotate(-4, resample=Image.BICUBIC, center=(W / 2, by0 + 63)))
img.convert("RGB").save(out)
print("wrote", out)
