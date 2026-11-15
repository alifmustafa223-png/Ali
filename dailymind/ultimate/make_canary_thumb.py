"""Thumbnail (1080x1920) for the canary Short: the miner proudly holding the singing canary in the lamp-lit tunnel,
big title, a '75 YEARS' stamp. Same layout as the fortune thumbnail (dark top band for the title, no caption boxes)."""
import sys

import skia

import make_canary as M
import style2d_engine as E
import toon as T
from style2d_engine import C, P, S

OUT = sys.argv[1]
t = M.word_t("hook", "saved") + 0.5                           # eyes open, brows up, canary mid-song
img, cam, _ = M.sc_hook(t, 0)
rgb = E.crop(img, 1.25, 560, 1150)
s, c = E.surf(world=False)
c.drawRect(skia.Rect(0, 0, 1080, 800), P(Shader=T.lin((0, 0), (0, 800), [C(10, 0, 10, 215), C(10, 0, 10, 0)])))
for txt, size, y, grad in (("THIS TINY BIRD", 120, 260, E.WHITE), ("SAVED", 190, 470, E.GOLD), ("MINERS", 190, 660, E.GOLD)):
    size = E.fit_size(txt, size, 980)
    f = skia.Font(T.FB, size)
    w = f.measureText(txt)
    x = (1080 - w) / 2
    c.drawString(txt, x + 7, y + 9, f, P(C(10, 0, 20, 170), MaskFilter=E.BLUR(7)))
    c.drawString(txt, x, y, f, S(C(25, 10, 30), size * 0.17))
    c.drawString(txt, x, y, f, P(Shader=T.lin((0, y - size), (0, y), grad)))
rgb = E.comp_screen(rgb, E.arr(s))
rgb = E.comp_screen(rgb, E.stamp_layer(10.0, "FOR 75 YEARS", 0.0, 540, 1780, 110, (220, 35, 45), -6))
rgb = E.finish(rgb, 0)
E.save(rgb, OUT)
print("wrote", OUT)
