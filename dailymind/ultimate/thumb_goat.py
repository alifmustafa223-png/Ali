"""Cover for the Messi/Ronaldo Short (1080x1920). Usage (in dailymind/ultimate): python thumb_goat.py ../goat/thumbnail.png"""
import sys

out = sys.argv[1]
sys.argv = [sys.argv[0], "unused.mp4"]
import make_goat as M  # noqa: E402
from make_goat import *  # noqa: E402,F401,F403
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

T = 3.0
surf = skia.Surface(W, H)
c = surf.getCanvas()
M.bg(c, (12, 20, 50), (45, 25, 60))
c.drawLine(540, 760, 540, 1920, S(C(255, 255, 255, 90), 6))
glow(c, 270, 1250, 420, (120, 185, 240), 70)
glow(c, 810, 1250, 420, (255, 80, 90), 80)
# left: Leo holding up the signed napkin
M.stand(c, M.LEO, 270, 1900, 1.35, T, eyes="wide", mouth="O", brows="up", look=(0.3, -0.6), hands=[(-30, 150), (110, -80)])
PH.cloth(c, T, 290, 830, 360, 280, 0.6, "top", ink=M.napkin_ink(1.0))
c.drawLine(90, 830, 490, 830, S(C(120, 90, 60), 9))
# right: Cristiano with a racing heart + ECG
M.stand(c, M.CR, 810, 1900, 1.35, T, eyes="wide", mouth="O", brows="up", look=(-0.3, -0.6), hands=[(-60, 60), (40, 150)])
M.heart_shape(c, 810, 1130, 1.0)
glow(c, 810, 1120, 220, (255, 80, 90), 170)
M.ecg(c, 610, 880, 400, 130, T, 190)
PH.draw_ball(c, 540, 1800, 70, 20, 0.0, shadow_floor=1900)
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


big(img, "MESSI'S CONTRACT", 150, 110, (255, 255, 255))
big(img, "WAS A NAPKIN?!", 285, 140, (255, 205, 60), stroke=18)
d = ImageDraw.Draw(img, "RGBA")
f = font(FONT_B, 62)
label = "RONALDO: HEART SURGERY"
tw = d.textlength(label, font=f)
bx0, by0 = (W - tw) / 2 - 36, 500
banner = Image.new("RGBA", img.size, (0, 0, 0, 0))
bd = ImageDraw.Draw(banner)
bd.rounded_rectangle([bx0, by0, bx0 + tw + 72, by0 + 106], radius=24, fill=(225, 40, 50, 245), outline=(255, 255, 255), width=8)
bd.text((bx0 + 36, by0 + 12), label, font=f, fill=(255, 255, 255))
img.alpha_composite(banner.rotate(-3, resample=Image.BICUBIC, center=(W / 2, by0 + 53)))
img.convert("RGB").save(out)
print("wrote", out)
