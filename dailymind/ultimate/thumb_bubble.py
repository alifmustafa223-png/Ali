"""Cover for the bubble wrap Short (1080x1920 PNG). Usage (in dailymind/ultimate): python thumb_bubble.py ../bubble/thumbnail.png"""
import math
import sys

out = sys.argv[1]
sys.argv = [sys.argv[0], "unused.mp4"]
import make_bubble as M  # noqa: E402
from make_bubble import *  # noqa: E402,F401,F403
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

T = 1.0
surf = skia.Surface(W, H)
c = surf.getCanvas()
pts = M.bubble_grid(0, 0, W, 1560, 28)
pops = [(0.5, M.wall_index(pts, x, y)) for x, y in ((560, 1300), (620, 1240), (500, 1220), (680, 1330))]
M.living_room(c, T, pops)
M.stand(c, M.KIDY, 300, 1900, 1.75, T, eyes="wide", mouth="laugh", brows="up", look=(1, -0.2), hands=[(-20, 150), (170, -60)])
M.comic_pop(c, 760, 1130, 0.3, 2.2)
snap = surf.makeImageSnapshot()
c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=U.BLOOM, ImageFilter=skia.ImageFilters.Blur(24, 24), BlendMode=skia.BlendMode.kPlus, Alphaf=0.25))
c.drawPaint(P(Shader=rad(540, 1150, 1250, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 170)], [0, 0.55, 1])))
c.drawRect(skia.Rect(0, 0, W, 900), P(Shader=lin((0, 0), (0, 900), [C(5, 4, 10, 210), C(5, 4, 10, 0)])))
img = Image.fromarray(np.ascontiguousarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType))).convert("RGBA")


def big_text(img, text, y, size, fill, stroke=14, max_w=1000):
    d = ImageDraw.Draw(img)
    f = font(FONT_B, size)
    while d.textlength(text, font=f) > max_w and size > 40:
        size -= 4
        f = font(FONT_B, size)
    w = d.textlength(text, font=f)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text(((W - w) / 2 + 8, y + 12), text, font=f, fill=(0, 0, 0, 200), stroke_width=stroke, stroke_fill=(0, 0, 0, 200))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d.text(((W - w) / 2, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(20, 10, 10))


big_text(img, "BUBBLE WRAP WAS", 150, 104, (255, 255, 255))
big_text(img, "WALLPAPER?!", 290, 190, (120, 220, 255), stroke=18)
d = ImageDraw.Draw(img, "RGBA")
f = font(FONT_B, 88)
label = "NOBODY WANTED IT"
tw = d.textlength(label, font=f)
bx0, by0 = (W - tw) / 2 - 40, 545
banner = Image.new("RGBA", img.size, (0, 0, 0, 0))
bd = ImageDraw.Draw(banner)
bd.rounded_rectangle([bx0, by0, bx0 + tw + 80, by0 + 126], radius=24, fill=(215, 35, 40, 245), outline=(255, 255, 255), width=8)
bd.text((bx0 + 40, by0 + 12), label, font=f, fill=(255, 255, 255))
img.alpha_composite(banner.rotate(-4, resample=Image.BICUBIC, center=(W / 2, by0 + 63)))
img.convert("RGB").save(out)
print("wrote", out)
