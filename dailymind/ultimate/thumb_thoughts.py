"""Thumbnail for the long-form "$1 per thought" video (1280x720 render at 1920x1080, saved as 1280x720 JPG + PNG).

Design: shocked kid (left) holding a glowing phone with "+$1" notifications, a flood of "$1" thought bubbles coming
from everywhere, giant balance "$1,000,000,000" top-right, 3-4 word text "$1 PER THOUGHT?!" readable at phone size.
Usage (in dailymind/ultimate): python thumb_thoughts.py ../long_thoughts/thumbnail
"""
import math
import random
import sys

out = sys.argv[1]
sys.argv = ["make_thoughts.py", "none"]
import numpy as np  # noqa: E402
import skia  # noqa: E402

import make_thoughts as M  # noqa: E402
from long_engine import *  # noqa: E402,F401,F403
from PIL import Image  # noqa: E402

t = 1.3
surf = skia.Surface(W, H)
c = surf.getCanvas()
c.drawPaint(P(Shader=rad(700, 560, 1500, [C(70, 40, 110), C(20, 12, 35)])))
for k in range(18):  # rays from the phone
    a = k / 18 * 2 * math.pi
    p = skia.Path()
    p.moveTo(820, 600)
    p.lineTo(820 + math.cos(a) * 2200, 600 + math.sin(a) * 2200)
    p.lineTo(820 + math.cos(a + 0.12) * 2200, 600 + math.sin(a + 0.12) * 2200)
    p.close()
    c.drawPath(p, P(C(255, 230, 150, 22)))
r = random.Random(3)
for i in range(26):  # $1 thought bubbles flooding in
    x, y = r.uniform(80, 1860), r.uniform(80, 1040)
    if 520 < x < 1150 and 250 < y < 1080:
        continue
    s = r.uniform(0.6, 1.25)
    c.drawCircle(x, y, 52 * s, P(C(255, 255, 255, 235)))
    c.drawCircle(x, y, 52 * s, S(C(40, 40, 50), 5))
    text(c, "$1", x, y + 16 * s, 44 * s, (30, 150, 80), shadow=False)
M.bill_rain(c, 2.2, 0.0, 30, 5)
# the kid, shocked, phone in hand
pose = dict(eyes="wide", mouth="O", brows="up", hands=[(-120, -20), (200, 10)], look=(1, -0.2), tilt=-5)
person(c, 420, 1200, 2.0, M.YOU_BLUE, pose, t)
phone(c, 860, 620, 1.05, t, M.screen_bank([("+$1", "Somebody thought of you")] * 5, t), glow_col=(90, 230, 140))
post(surf, c, t)
# big text (thumbnail typography: thick stroke, max 4 words)
def fit(s, size, maxw):
    while font(size).measureText(s) > maxw:
        size -= 4
    return size


CX, MAXW = 1480, 760
text(c, "$1 PER", CX, 520, fit("$1 PER", 190, MAXW), (255, 255, 255), stroke=22)
text(c, "THOUGHT?!", CX, 720, fit("THOUGHT?!", 190, MAXW), (255, 205, 60), stroke=22)
bs = fit("$1,000,000,000", 84, MAXW - 120)
bw = font(bs).measureText("$1,000,000,000") / 2 + 50
c.save()
c.translate(CX, 880)
c.rotate(-4)
c.drawRoundRect(skia.Rect(-bw, -66, bw, 66), 24, 24, P(C(220, 35, 40)))
c.drawRoundRect(skia.Rect(-bw, -66, bw, 66), 24, 24, S(C(255, 255, 255), 8))
text(c, "$1,000,000,000", 0, bs * 0.35, bs, (255, 255, 255), shadow=False)
c.restore()
img = Image.fromarray(np.ascontiguousarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType))).convert("RGB")
img.resize((1280, 720), Image.LANCZOS).save(out + ".jpg", quality=92)
img.save(out + "_full.png")
print("wrote", out + ".jpg")
