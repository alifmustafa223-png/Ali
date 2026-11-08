"""Cover for the Mona Lisa Short (1080x1920). Usage (in dailymind/ultimate): python thumb_mona.py ../mona/thumbnail.png"""
import sys

out = sys.argv[1]
sys.argv = [sys.argv[0], "unused.mp4"]
import make_mona as M  # noqa: E402
from make_mona import *  # noqa: E402,F401,F403
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

T = 2.0
surf = skia.Surface(W, H)
c = surf.getCanvas()
M.gallery(c, T, (115, 40, 45))
M.hooks(c, 300, 1150, 0.8)
c.drawString("?", 260, 1200, skia.Font(FB, 200), P(C(255, 220, 120)))  # the empty spot on the wall
# the thief sneaking off with the painting under his arm
M.stand(c, M.PER, 690, 1890, 1.4, T, eyes="squint", mouth="grin", brows="angry", look=(-0.8, -0.3), hands=M.HOLD, walk=3.0)
glow(c, 690, 1730, 260, (255, 220, 150), 70)
M.mona(c, 690, 1730, 0.55, T, look=-1.0)
snap = surf.makeImageSnapshot()
c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=U.BLOOM, ImageFilter=skia.ImageFilters.Blur(24, 24), BlendMode=skia.BlendMode.kPlus, Alphaf=0.25))
c.drawPaint(P(Shader=rad(540, 1250, 1250, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 170)], [0, 0.55, 1])))
c.drawRect(skia.Rect(0, 0, W, 800), P(Shader=lin((0, 0), (0, 800), [C(5, 4, 10, 200), C(5, 4, 10, 0)])))
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


big(img, "THE MONA LISA", 150, 120, (255, 255, 255))
big(img, "WAS A NOBODY?!", 290, 130, (255, 205, 60), stroke=18)
d = ImageDraw.Draw(img, "RGBA")
f = font(FONT_B, 68)
label = "UNTIL HE STOLE IT"
tw = d.textlength(label, font=f)
bx0, by0 = (W - tw) / 2 - 36, 500
banner = Image.new("RGBA", img.size, (0, 0, 0, 0))
bd = ImageDraw.Draw(banner)
bd.rounded_rectangle([bx0, by0, bx0 + tw + 72, by0 + 110], radius=24, fill=(225, 40, 50, 245), outline=(255, 255, 255), width=8)
bd.text((bx0 + 36, by0 + 14), label, font=f, fill=(255, 255, 255))
img.alpha_composite(banner.rotate(-3, resample=Image.BICUBIC, center=(W / 2, by0 + 55)))
img.convert("RGB").save(out)
print("wrote", out)
