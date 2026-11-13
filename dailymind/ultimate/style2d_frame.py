"""The upgraded 2D style, one frame: big expressive characters in a rich painted set (Skia, renders in seconds).

  python style2d_frame.py OUT.png
Scene: sunset pier, open treasure chest; she smirks holding up a coin, he's shocked. Title in the channel's classic style.
"""
import math
import random
import sys

import numpy as np
import skia
from PIL import Image

import toon as T

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/style2d.png"
W, H = 1080, 1920
import os
LAYER = os.environ.get("LAYER", "full")
surf = skia.Surface(W, H)
c = surf.getCanvas()
_real = c
_null = skia.Surface(W, H).getCanvas()
if LAYER != "full":
    c.clear(skia.ColorTRANSPARENT)


def sec(name):
    """Paper-theatre layers: LAYER=sky|sea|deck|chars draws only that slice; bg = sky+sea+deck; full = everything."""
    if LAYER in ("full", name) or (LAYER == "bg" and name != "chars"):
        return _real
    return _null


c = sec("sky")
C, P, S = T.C, T.P, T.S
rr = random.Random(4)

# ---- sky: sunset gradient, sun with halo, soft clouds
c.drawRect(skia.Rect(0, 0, W, 1000), P(Shader=T.lin((0, 0), (0, 1000), [C(38, 30, 82), C(170, 70, 110), C(255, 150, 90), C(255, 205, 140)], [0, 0.45, 0.8, 1])))
c.drawCircle(760, 820, 260, P(Shader=T.rad(760, 820, 260, [C(255, 230, 160, 160), C(255, 200, 120, 0)])))
c.drawCircle(760, 820, 95, P(C(255, 236, 180)))
for k in range(7):
    x, y, w = rr.uniform(-100, W), rr.uniform(180, 640), rr.uniform(220, 420)
    cl = skia.Path()
    for j in range(5):
        cl.addOval(skia.Rect(x + j * w / 6, y - rr.uniform(10, 50), x + j * w / 6 + w / 3, y + 40))
    c.drawPath(cl, P(C(255, 190, 170, 70), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
c = sec("sea")
# ---- distant cliffs + sea with sun glitter + ship
cliff = skia.Path()
cliff.moveTo(0, 900)
for x in range(0, 460, 20):
    cliff.lineTo(x, 760 + 60 * math.sin(x / 90) - x * 0.15)
cliff.lineTo(460, 960)
cliff.lineTo(0, 960)
c.drawPath(cliff, P(C(70, 40, 80)))
c.drawRect(skia.Rect(0, 940, W, H), P(Shader=T.lin((0, 940), (0, 1300), [C(120, 70, 120), C(40, 50, 100)])))
for k in range(60):
    y = 950 + k * 6 + rr.uniform(-2, 2)
    w = (60 - k) * 2.2 + rr.uniform(0, 30)
    c.drawRect(skia.Rect(760 - w / 2 + rr.uniform(-30, 30), y, 760 + w / 2, y + 3), P(C(255, 210, 150, 160 - k * 2)))
T.ship(c, 260, 935, 0.9, 0.0, dark=True)
c = sec("deck")
# ---- pier deck in perspective (planks converge toward the horizon)
deck = skia.Path()
deck.moveTo(-200, H)
deck.lineTo(W + 200, H)
deck.lineTo(760, 1180)
deck.lineTo(300, 1180)
deck.close()
c.drawPath(deck, P(Shader=T.lin((0, 1180), (0, H), [C(120, 78, 50), C(80, 48, 30)])))
for k in range(-10, 14):
    x0 = 530 + k * 48
    x1 = 530 + (k - 1.6) * 150 + 40
    c.drawLine(x0, 1180, x1, H, S(C(45, 26, 16, 200), 4))
for y in (1260, 1380, 1540, 1760):
    c.drawLine(0, y, W, y, S(C(60, 36, 22, 120), 3))
# posts + rope at the deck edge
for x in (330, 740):
    c.drawRect(skia.Rect(x - 18, 1000, x + 18, 1200), P(C(70, 42, 26)))
    c.drawRect(skia.Rect(x - 22, 990, x + 22, 1006), P(C(95, 60, 36)))
rope = skia.Path()
rope.moveTo(330, 1030)
rope.quadTo(535, 1090, 740, 1030)
c.drawPath(rope, S(C(200, 170, 120), 7))
# ---- lantern glow
c.drawCircle(905, 1220, 240, P(Shader=T.rad(905, 1220, 240, [C(255, 190, 90, 120), C(255, 160, 60, 0)])))
c.drawRoundRect(skia.Rect(870, 1150, 940, 1260), 10, 10, P(C(255, 215, 120)))
c.drawRoundRect(skia.Rect(870, 1150, 940, 1260), 10, 10, S(C(50, 30, 20), 8))
c.drawRect(skia.Rect(860, 1135, 950, 1152), P(C(50, 30, 20)))
# ---- the treasure chest, open, heaped with gold
cx, cy = 540, 1430
body = skia.Rect(cx - 230, cy - 110, cx + 230, cy + 110)
c.drawRoundRect(body, 18, 18, P(Shader=T.lin((0, cy - 110), (0, cy + 110), [C(150, 85, 45), C(95, 50, 25)])))
for x in (cx - 150, cx + 150):
    c.drawRect(skia.Rect(x - 18, cy - 110, x + 18, cy + 110), P(C(70, 60, 55)))
c.drawRoundRect(body, 18, 18, S(T.OUT, 9))
lid = skia.Path()
lid.moveTo(cx - 240, cy - 110)
lid.lineTo(cx - 200, cy - 330)
lid.quadTo(cx, cy - 400, cx + 200, cy - 330)
lid.lineTo(cx + 240, cy - 110)
lid.close()
c.drawPath(lid, P(Shader=T.lin((0, cy - 400), (0, cy - 110), [C(110, 60, 30), C(150, 85, 45)])))
c.drawPath(lid, S(T.OUT, 9))
heap = skia.Path()
heap.moveTo(cx - 225, cy - 105)
heap.quadTo(cx, cy - 260, cx + 225, cy - 105)
heap.close()
c.drawPath(heap, P(Shader=T.lin((0, cy - 250), (0, cy - 100), [C(255, 225, 110), C(220, 150, 40)])))
for k in range(26):  # coins on the heap
    u = rr.uniform(-0.9, 0.9)
    x = cx + u * 210
    y = cy - 110 - (1 - u * u) * 130 + rr.uniform(0, 30)
    T.coin(c, x, y, rr.uniform(16, 24))
for k in range(8):   # spilled coins
    T.coin(c, cx + rr.uniform(-330, 330), cy + 150 + rr.uniform(0, 160), rr.uniform(18, 26), flat=True)
for k in range(10):
    T.sparkle(c, cx + rr.uniform(-200, 200), cy - 120 - rr.uniform(0, 140), rr.uniform(12, 22))
# ---- characters: big, readable acting
c = sec("chars")
HER = dict(skin=(150, 95, 65), hair="curly", hair_col=(40, 25, 20), coat=(245, 245, 240), pants=(60, 90, 150), nose="small",
           collar=(70, 170, 190))
HIM = dict(skin=(200, 140, 100), hair="neat", hair_col=(40, 28, 22), coat=(80, 80, 90), pants=(90, 95, 110), nose="long", mustache=False)
# him: left, hands flying to his cheeks, jaw dropped, eyes wide, brows up
PH = dict(eyes="wide", brows="up", mouth="O", look=(0.8, 0.1), hands=[(5, -55), (-5, -55)], lean=-3, tilt=-8)
T.person(c, 190, 1560, 1.45, HIM, PH, 0.3)
# her: right, hand on hip, smug half-lidded grin, a coin held up beside her face
PS = dict(eyes="squint", brows="smug", mouth="grin", look=(-0.6, 0), hands=[(-35, 115), (25, -135)], lean=2, tilt=7)
T.person(c, 800, 1800, 1.75, HER, PS, 0.3)
hx, hy = T.hand_pos(800, 1800, 1.75, PS, 1)
T.coin(c, hx + 6, hy - 52, 36)
T.sparkle(c, hx + 40, hy - 95, 34)
if LAYER != "full":
    img = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    Image.fromarray(img).save(OUT)
    raise SystemExit
# ---- title in the channel's classic look (title + subtitle, no caption box)
f1, f2 = skia.Font(T.FB, 92), skia.Font(T.FB, 50)
for txt, f, y, col in (("EVERY COIN...", f1, 300, C(255, 255, 255)), ("WAS FAKE", skia.Font(T.FB, 150), 450, C(255, 200, 60)),
                       ("the 1880s trick that fooled a millionaire", f2, 530, C(255, 240, 225))):
    w = f.measureText(txt)
    c.drawString(txt, (W - w) / 2, y, f, S(C(20, 10, 20), 16))
    c.drawString(txt, (W - w) / 2, y, f, P(col))
# ---- finish: warm vignette + light grain
c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.rad(W / 2, H * 0.55, H * 0.75, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(20, 5, 20, 170)], [0, 0.6, 1])))
img = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[:, :, :3].astype(float)
img += np.random.default_rng(1).normal(0, 4, img.shape[:2])[..., None]
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(OUT)
print("wrote", OUT)
