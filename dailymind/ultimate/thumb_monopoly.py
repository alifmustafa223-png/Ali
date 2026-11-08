"""Cover for the Monopoly Short (1080x1920). Usage (in dailymind/ultimate): python thumb_monopoly.py ../monopoly/thumbnail.png"""
import sys

out = sys.argv[1]
sys.argv = [sys.argv[0], "unused.mp4"]
import make_monopoly as M  # noqa: E402
from make_monopoly import *  # noqa: E402,F401,F403
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

T = 2.0
surf = skia.Surface(W, H)
c = surf.getCanvas()
M.bg(c, (40, 12, 18), (90, 25, 35))
M.rays(c, T, (255, 150, 120), 22, 1450)
M.board(c, 540, 1600, 1000, T)
for i, (hx, hy) in enumerate(((250, 1600), (360, 1730), (780, 1720), (870, 1590))):
    M.house(c, hx, hy, 1.3, T, "scared", look=(1 if hx < 540 else -1, -0.5), ph=i)
M.tophat_token(c, 540, 1760, 1.55, T, "evil", (0, 0.2), chomp=0.8)
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


big(img, "MONOPOLY WAS MADE", 150, 100, (255, 255, 255))
big(img, "TO SHOW IT'S EVIL?!", 280, 130, (255, 80, 70), stroke=18)
d = ImageDraw.Draw(img, "RGBA")
f = font(FONT_B, 84)
label = "SHE GOT ROBBED"
tw = d.textlength(label, font=f)
bx0, by0 = (W - tw) / 2 - 40, 490
banner = Image.new("RGBA", img.size, (0, 0, 0, 0))
bd = ImageDraw.Draw(banner)
bd.rounded_rectangle([bx0, by0, bx0 + tw + 80, by0 + 120], radius=24, fill=(240, 190, 50, 245), outline=(255, 255, 255), width=8)
bd.text((bx0 + 40, by0 + 12), label, font=f, fill=(40, 20, 10))
img.alpha_composite(banner.rotate(-4, resample=Image.BICUBIC, center=(W / 2, by0 + 60)))
img.convert("RGB").save(out)
print("wrote", out)
