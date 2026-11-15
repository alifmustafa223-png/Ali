"""Thumbnail (1080x1920): Eddie screaming in front of the molasses wave, big title, BOSTON 1919 stamp."""
import sys
import skia
import make_molasses2 as M
import style2d_engine as E
import toon as T
from style2d_engine import C, P, S

OUT = sys.argv[1]
t = 2.0
img, cam, _ = M.sc_hook(t, 0)
rgb = E.crop(img, 1.1, 540, 1000)
s, c = E.surf(world=False)
c.drawRect(skia.Rect(0, 0, 1080, 800), P(Shader=T.lin((0, 0), (0, 800), [C(10, 0, 10, 215), C(10, 0, 10, 0)])))
for txt, size, y, grad in (("A 25-FOOT WAVE", 120, 250, E.WHITE), ("OF MOLASSES", 160, 430, E.GOLD), ("KILLED 21", 140, 600, E.WHITE)):
    size = E.fit_size(txt, size, 980)
    f = skia.Font(T.FB, size)
    w = f.measureText(txt)
    x = (1080 - w) / 2
    c.drawString(txt, x + 7, y + 9, f, P(C(10, 0, 20, 170), MaskFilter=E.BLUR(7)))
    c.drawString(txt, x, y, f, S(C(25, 10, 30), size * 0.17))
    c.drawString(txt, x, y, f, P(Shader=T.lin((0, y - size), (0, y), grad)))
rgb = E.comp_screen(rgb, E.arr(s))
rgb = E.comp_screen(rgb, E.stamp_layer(10.0, "BOSTON 1919", 0.0, 540, 1780, 120, (220, 35, 45), -6))
E.save(E.finish(rgb, 0), OUT)
print("wrote", OUT)
