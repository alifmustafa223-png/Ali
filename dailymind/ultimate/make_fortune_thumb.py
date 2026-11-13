"""Thumbnail (1080x1920) for the fortune cookie Short: the shocked diner + cracked cookie, big title, a JAPANESE stamp."""
import sys

import skia

import make_fortune as F
import style2d_engine as E
import toon as T
from style2d_engine import C, P, S

OUT = sys.argv[1]
t = F.word_t("hook", "chinese") + 0.6                       # mid-shock: wide eyes, jaw down, cookie cracked
img, cam, _ = F.sc_restaurant(t, 0)
rgb = E.crop(img, 1.18, 540, 1100)
s, c = E.surf(world=False)
c.drawRect(skia.Rect(0, 0, 1080, 760), P(Shader=T.lin((0, 0), (0, 760), [C(10, 0, 10, 200), C(10, 0, 10, 0)])))   # dark band for the title
for txt, size, y, grad in (("FORTUNE COOKIES", 112, 250, E.WHITE), ("AREN'T", 150, 420, E.WHITE), ("CHINESE?!", 190, 610, E.GOLD)):
    size = E.fit_size(txt, size, 980)
    f = skia.Font(T.FB, size)
    w = f.measureText(txt)
    x = (1080 - w) / 2
    c.drawString(txt, x + 7, y + 9, f, P(C(10, 0, 20, 170), MaskFilter=E.BLUR(7)))
    c.drawString(txt, x, y, f, S(C(25, 10, 30), size * 0.17))
    c.drawString(txt, x, y, f, P(Shader=T.lin((0, y - size), (0, y), grad)))
rgb = E.comp_screen(rgb, E.arr(s))
rgb = E.comp_screen(rgb, E.stamp_layer(10.0, "JAPANESE", 0.0, 540, 1780, 130, (220, 35, 45), -8))
rgb = E.finish(rgb, 0)
E.save(rgb, OUT)
print("wrote", OUT)
