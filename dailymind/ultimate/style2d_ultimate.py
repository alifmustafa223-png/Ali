"""The best 2D frame we can make in code — 'Classic+ cartoon', fully polished.

  python style2d_ultimate.py OUT.png
Layers: painted sky (lit clouds, god rays, birds), atmospheric cliffs + tiny lighthouse, a detailed backlit ship with
rigging and its reflection, sea with a sun-glitter path, a plank-by-plank pier (grain, seams, nails), props (barrels,
coiled rope, lantern), a detailed open chest (iron bands, rivets, gems, pearls, heaped coins), the characters with
cel shading + sunset rim light + cast shadows, then glow/bloom, colour grade, vignette and grain.
"""
import math
import os
import random
import sys

import numpy as np
import skia
from PIL import Image, ImageFilter

import toon as T

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ultimate2d.png"
TITLE = os.environ.get("TITLE", "1") == "1"
W, H = 1080, 1920
C, P, S = T.C, T.P, T.S
rr = random.Random(11)
SUN = (760, 820)
HOR = 940


def surf():
    s = skia.Surface(W, H)
    s.getCanvas().clear(skia.ColorTRANSPARENT)
    return s


def arr(s):
    return s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32) / 255.0


def over(dst, src):
    a = src[..., 3:4]
    dst[..., :3] = src[..., :3] * a + dst[..., :3] * (1 - a)
    dst[..., 3:4] = a + dst[..., 3:4] * (1 - a)
    return dst


def blur(x, r):
    im = Image.fromarray(np.clip(x * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255.0


def path(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


BLUR = lambda r: skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r)  # noqa: E731

# =========================================================================================== SKY
sky_s = surf()
c = sky_s.getCanvas()
c.drawRect(skia.Rect(0, 0, W, HOR + 10), P(Shader=T.lin((0, 0), (0, HOR), [C(28, 22, 70), C(92, 45, 110), C(196, 82, 112), C(250, 140, 96),
                                                                        C(255, 196, 130)], [0, 0.3, 0.58, 0.82, 1])))
# god rays fanning from the sun
for k in range(14):
    a0 = math.radians(-170 + k * 13 + rr.uniform(-3, 3))
    a1 = a0 + math.radians(rr.uniform(3, 6))
    L = 1600
    c.drawPath(path([SUN, (SUN[0] + L * math.cos(a0), SUN[1] + L * math.sin(a0)), (SUN[0] + L * math.cos(a1), SUN[1] + L * math.sin(a1))]),
               P(C(255, 220, 160, 26), MaskFilter=BLUR(10)))
# sun: halo, bloom, disc
c.drawCircle(*SUN, 420, P(Shader=T.rad(*SUN, 420, [C(255, 220, 150, 120), C(255, 170, 110, 0)])))
c.drawCircle(*SUN, 150, P(Shader=T.rad(*SUN, 150, [C(255, 245, 210, 255), C(255, 225, 150, 0)])))
c.drawCircle(*SUN, 92, P(C(255, 244, 205)))
# clouds: lit from below (warm undersides, cool tops), several depth bands
for band, (y0, n, sc, col_top, col_bot) in enumerate(((210, 5, 1.3, (120, 70, 140), (255, 160, 150)), (420, 6, 1.0, (150, 80, 130), (255, 180, 140)),
                                                      (640, 6, 0.75, (190, 100, 120), (255, 205, 150)))):
    for k in range(n):
        x = rr.uniform(-150, W)
        y = y0 + rr.uniform(-40, 40)
        w = rr.uniform(260, 460) * sc
        cl = skia.Path()
        for j in range(7):
            bx = x + j * w / 8
            br = rr.uniform(0.18, 0.32) * w
            cl.addOval(skia.Rect(bx - br * 0.6, y - br * rr.uniform(0.5, 0.9), bx + br * 0.6, y + br * 0.25))
        c.drawPath(cl, P(Shader=T.lin((0, y - 0.3 * w), (0, y + 0.1 * w), [C(*col_top, 150), C(*col_bot, 230)]), MaskFilter=BLUR(2)))
        cl = skia.Op(cl, skia.Path(), skia.PathOp.kUnion_PathOp) or cl   # merge puffs: no inner outlines
        c.drawPath(cl, S(C(255, 225, 190, 70), 2.5))
# birds
for k in range(6):
    bx, by, s = 520 + k * 48 + rr.uniform(-15, 15), 650 + rr.uniform(-30, 30), rr.uniform(8, 13)
    b = skia.Path()
    b.moveTo(bx - s, by)
    b.quadTo(bx - s / 2, by - s * 0.6, bx, by)
    b.quadTo(bx + s / 2, by - s * 0.6, bx + s, by)
    c.drawPath(b, S(C(50, 25, 50, 200), 3))
# far cliffs with atmospheric haze + a tiny lighthouse
for layer, (yb, amp, col) in enumerate(((870, 50, (150, 90, 130)), (900, 70, (110, 60, 105)))):
    pts = [(0, HOR)] + [(x, yb - amp * (0.6 + 0.4 * math.sin(x / (120 + 40 * layer) + layer)) - (40 if x < 380 else 0) * (1 - x / 380))
                        for x in range(0, W + 1, 20)] + [(W, HOR)]
    c.drawPath(path(pts), P(C(*col)))
c.drawPath(path([(0, HOR), (0, 700), (90, 690), (200, 730), (330, 780), (430, 860), (470, HOR)]), P(C(80, 42, 80)))
c.drawRect(skia.Rect(118, 640, 132, 692), P(C(240, 230, 220)))
c.drawRect(skia.Rect(115, 632, 135, 642), P(C(60, 30, 50)))
c.drawCircle(125, 628, 6, P(C(255, 240, 180)))
c.drawPath(path([(125, 628), (0, 600), (0, 650)]), P(C(255, 235, 170, 60), MaskFilter=BLUR(4)))
# sea
c.drawRect(skia.Rect(0, HOR, W, H), P(Shader=T.lin((0, HOR), (0, 1350), [C(150, 80, 120), C(70, 50, 105), C(30, 40, 90)], [0, 0.4, 1])))
for k in range(70):   # sun glitter path
    y = HOR + 6 + k * 5.5
    w = max(8, (75 - k) * 2.6 + rr.uniform(-20, 40))
    xc = SUN[0] + rr.uniform(-25, 25) * (1 + k / 40)
    c.drawRoundRect(skia.Rect(xc - w / 2, y, xc + w / 2, y + 2.6), 1.3, 1.3, P(C(255, 220, 160, max(30, 200 - k * 2))))
for k in range(55):   # wave strokes
    y = HOR + 20 + (k / 55) ** 1.6 * 420
    x = rr.uniform(-50, W)
    w = 20 + (y - HOR) * 0.25
    c.drawLine(x, y, x + w, y, S(C(190, 120, 160, 70), 2 + (y - HOR) / 160))
# the ship (backlit), rigging, its reflection
ship_s = surf()
sc_ = ship_s.getCanvas()
sx, sy = 255, 925
hull = path([(sx - 170, sy - 45), (sx + 175, sy - 50), (sx + 150, sy + 8), (sx - 140, sy + 10)])
sc_.drawPath(hull, P(C(45, 25, 40)))
for k in range(4):
    sc_.drawLine(sx - 160 + k * 4, sy - 34 + k * 10, sx + 165 - k * 6, sy - 38 + k * 10, S(C(80, 45, 55), 2))
for k in range(6):
    sc_.drawCircle(sx - 110 + k * 45, sy - 25, 5, P(C(255, 200, 120)))   # lit portholes
sc_.drawPath(path([(sx - 175, sy - 50), (sx - 210, sy - 75), (sx - 160, sy - 60)]), P(C(45, 25, 40)))   # bowsprit
masts = [(sx - 70, 210), (sx + 40, 250), (sx + 135, 170)]
for mx, mh in masts:
    sc_.drawLine(mx, sy - 45, mx, sy - 45 - mh, S(C(50, 28, 40), 7))
    for j, (sw, sh) in enumerate(((95, 70), (80, 55), (60, 40))):
        yt = sy - 45 - mh + 20 + j * (sh + 10)
        sail = skia.Path()
        sail.moveTo(mx - sw / 2, yt)
        sail.lineTo(mx + sw / 2, yt)
        sail.quadTo(mx + sw / 2 + 12, yt + sh / 2, mx + sw / 2 - 4, yt + sh)
        sail.lineTo(mx - sw / 2 + 4, yt + sh)
        sail.quadTo(mx - sw / 2 + 14, yt + sh / 2, mx - sw / 2, yt)
        sc_.drawPath(sail, P(Shader=T.lin((mx - sw / 2, 0), (mx + sw / 2, 0), [C(190, 140, 140), C(255, 215, 175)])))
        sc_.drawPath(sail, S(C(60, 30, 45), 2))
    sc_.drawPath(path([(mx, sy - 45 - mh), (mx + 30, sy - 45 - mh + 8), (mx, sy - 45 - mh + 16)]), P(C(200, 40, 50)))   # pennant
for a_, b_ in ((masts[0], masts[1]), (masts[1], masts[2])):
    sc_.drawLine(a_[0], sy - 45 - a_[1], b_[0], sy - 45 - b_[1], S(C(50, 28, 40, 200), 1.5))
for mx, mh in masts:
    sc_.drawLine(mx, sy - 45 - mh, sx - 205, sy - 72, S(C(50, 28, 40, 150), 1.2))
    sc_.drawLine(mx, sy - 45 - mh, sx + 170, sy - 48, S(C(50, 28, 40, 150), 1.2))
ship = arr(ship_s)
refl = ship[::-1].copy()
shift = H - 2 * (sy + 10)
refl = np.roll(refl, shift, axis=0)
refl[..., 3] *= 0.35
refl = blur(refl, 2.5)
for yy in range(0, H, 6):  # broken by ripples
    refl[yy:yy + 2, :, 3] *= 0.3
sky = arr(sky_s)
sky = over(sky, refl * (np.arange(H)[:, None, None] > sy + 8))
sky = over(sky, ship)

# =========================================================================================== PIER
deck_s = surf()
c = deck_s.getCanvas()
VT, VL, VR = 1180, 300, 760          # far edge of the deck
BL, BR = -260, W + 260               # near edge (off-screen)
N = 14
c.drawPath(path([(VL, VT), (VR, VT), (BR, H), (BL, H)]), P(C(30, 16, 10)))   # dark gaps between the planks
for i in range(N):
    u0, u1 = i / N, (i + 1) / N
    gap = 0.012
    p0 = (VL + (VR - VL) * (u0 + gap), VT)
    p1 = (VL + (VR - VL) * (u1 - gap), VT)
    p2 = (BL + (BR - BL) * (u1 - gap * 0.3), H)
    p3 = (BL + (BR - BL) * (u0 + gap * 0.3), H)
    tone = rr.uniform(0.85, 1.12)
    c.drawPath(path([p0, p1, p2, p3]), P(Shader=T.lin((0, VT), (0, H), [C(150 * tone, 100 * tone, 62 * tone), C(98 * tone, 60 * tone, 36 * tone)])))
    for g in range(5):   # grain lines along the plank
        f = rr.uniform(0.15, 0.85)
        a_ = (p0[0] + (p1[0] - p0[0]) * f, VT)
        b_ = (p3[0] + (p2[0] - p3[0]) * f, H)
        gp = skia.Path()
        gp.moveTo(*a_)
        gp.quadTo((a_[0] + b_[0]) / 2 + rr.uniform(-8, 8), (VT + H) / 2, *b_)
        c.drawPath(gp, S(C(70, 40, 24, 70), rr.uniform(1, 2.5)))
    for seam in range(2):  # plank ends + nails
        t_ = rr.uniform(0.15, 0.9) ** 1.5
        y = VT + (H - VT) * t_
        xa = p3[0] + (p0[0] - p3[0]) * (1 - t_)
        xb = p2[0] + (p1[0] - p2[0]) * (1 - t_)
        c.drawLine(xa, y, xb, y, S(C(40, 22, 14, 200), 2 + 3 * t_))
        for xn in (xa + (xb - xa) * 0.25, xa + (xb - xa) * 0.75):
            c.drawCircle(xn, y - 4 - 6 * t_, 1.5 + 3 * t_, P(C(40, 30, 30)))
c.drawRect(skia.Rect(0, VT - 4, W, VT + 4), P(C(60, 36, 22, 0)))
# posts + rope + lantern + barrels + coiled rope
for x, top in ((330, 990), (740, 990)):
    c.drawRoundRect(skia.Rect(x - 20, top, x + 20, VT + 30), 6, 6, P(Shader=T.lin((x - 20, 0), (x + 20, 0), [C(60, 36, 24), C(110, 70, 44), C(55, 32, 20)])))
    c.drawRoundRect(skia.Rect(x - 24, top - 12, x + 24, top + 6), 6, 6, P(C(95, 60, 36)))
rope = skia.Path()
rope.moveTo(330, 1015)
rope.quadTo(535, 1080, 740, 1015)
c.drawPath(rope, S(C(120, 95, 60), 9))
c.drawPath(rope, S(C(210, 180, 130), 5))
for (bx, by, s) in ():   # (side barrels read as a backpack / stray blob behind the characters)  # barrels at the sides
    w, h = 120 * s, 160 * s
    c.drawRoundRect(skia.Rect(bx - w / 2, by - h, bx + w / 2, by), 30 * s, 30 * s,
                    P(Shader=T.lin((bx - w / 2, 0), (bx + w / 2, 0), [C(80, 45, 25), C(160, 100, 55), C(70, 38, 20)])))
    for f in (0.18, 0.82):
        c.drawLine(bx - w / 2 + 2, by - h * f, bx + w / 2 - 2, by - h * f, S(C(60, 60, 65), 8 * s))
    c.drawRoundRect(skia.Rect(bx - w / 2, by - h, bx + w / 2, by), 30 * s, 30 * s, S(T.OUT, 5))
for k in range(6):   # coiled rope near the chest (stacked coils, top lit)
    r0 = 95 - k * 9
    c.drawOval(skia.Rect(240 - r0, 1735 - k * 9 - r0 * 0.32, 240 + r0, 1735 - k * 9 + r0 * 0.32), S(C(110, 85, 50), 15))
    c.drawOval(skia.Rect(240 - r0, 1733 - k * 9 - r0 * 0.32, 240 + r0, 1733 - k * 9 + r0 * 0.32), S(C(215, 180, 125), 8))
# lantern on a hook post (right)
LX, LY = 905, 1215
c.drawCircle(LX, LY, 300, P(Shader=T.rad(LX, LY, 300, [C(255, 190, 90, 110), C(255, 160, 60, 0)])))
c.drawRoundRect(skia.Rect(LX - 38, LY - 60, LX + 38, LY + 55), 12, 12, P(Shader=T.rad(LX, LY, 60, [C(255, 245, 190), C(255, 190, 80)])))
for xx in (LX - 38, LX, LX + 38):
    c.drawLine(xx, LY - 60, xx, LY + 55, S(C(45, 30, 25), 5))
c.drawRoundRect(skia.Rect(LX - 46, LY - 78, LX + 46, LY - 58), 6, 6, P(C(45, 30, 25)))
c.drawRoundRect(skia.Rect(LX - 46, LY + 52, LX + 46, LY + 66), 6, 6, P(C(45, 30, 25)))
c.drawArc(skia.Rect(LX - 22, LY - 110, LX + 22, LY - 66), 180, 180, False, S(C(45, 30, 25), 5))
# =========================================================================================== CHEST (detailed)
cx, cy = 540, 1430
cb = skia.Rect(cx - 235, cy - 115, cx + 235, cy + 115)
c.drawOval(skia.Rect(cx - 300, cy + 80, cx + 300, cy + 160), P(C(20, 10, 10, 120), MaskFilter=BLUR(18)))   # contact shadow
# lid (open, behind)
lid = skia.Path()
lid.moveTo(cx - 245, cy - 112)
lid.lineTo(cx - 205, cy - 340)
lid.quadTo(cx, cy - 415, cx + 205, cy - 340)
lid.lineTo(cx + 245, cy - 112)
lid.close()
c.drawPath(lid, P(Shader=T.lin((0, cy - 415), (0, cy - 112), [C(90, 48, 24), C(130, 72, 38)])))
c.drawPath(path([(cx - 225, cy - 125), (cx - 195, cy - 320), (cx + 195, cy - 320), (cx + 225, cy - 125)]),
           P(C(60, 30, 18)))   # lid inside (shadowed)
for xb in (cx - 150, cx + 150):
    c.drawPath(path([(xb - 16, cy - 112), (xb - 14 + (xb - cx) * 0.12, cy - 360), (xb + 14 + (xb - cx) * 0.12, cy - 360), (xb + 16, cy - 112)]),
               P(C(85, 80, 80)))
c.drawPath(lid, S(T.OUT, 8))
# heap of gold + gems + pearls
heap = skia.Path()
heap.moveTo(cx - 228, cy - 108)
heap.quadTo(cx - 60, cy - 300, cx + 40, cy - 250)
heap.quadTo(cx + 150, cy - 210, cx + 228, cy - 108)
heap.close()
c.drawPath(heap, P(Shader=T.lin((0, cy - 290), (0, cy - 105), [C(255, 236, 140), C(225, 150, 40)])))
for k in range(70):
    u = rr.uniform(-0.95, 0.95)
    top = cy - 108 - (1 - u * u) * 165
    T.coin(c, cx + u * 215, rr.uniform(top + 8, cy - 105), rr.uniform(13, 22))
for k, col in enumerate(((220, 30, 60), (40, 190, 110), (60, 120, 230), (220, 30, 60), (170, 60, 220))):   # gems
    gx, gy = cx + rr.uniform(-170, 170), cy - 130 - rr.uniform(0, 110)
    gem = path([(gx, gy - 16), (gx + 14, gy - 4), (gx + 9, gy + 13), (gx - 9, gy + 13), (gx - 14, gy - 4)])
    c.drawPath(gem, P(Shader=T.lin((gx - 14, gy - 16), (gx + 14, gy + 13), [C(*[min(255, v + 90) for v in col]), C(*col), C(*[v // 2 for v in col])])))
    c.drawPath(gem, S(C(30, 15, 20), 2.5))
    c.drawCircle(gx - 4, gy - 6, 3, P(C(255, 255, 255, 220)))
pearl = skia.Path()
pearl.moveTo(cx + 120, cy - 130)
pearl.cubicTo(cx + 210, cy - 40, cx + 230, cy + 60, cx + 290, cy + 130)
meas = skia.PathMeasure(pearl, False)
Lp = meas.getLength()
for k in range(26):
    pos, _ = meas.getPosTan(Lp * k / 25)
    c.drawCircle(pos.x(), pos.y(), 8, P(Shader=T.rad(pos.x() - 3, pos.y() - 3, 9, [C(255, 255, 250), C(215, 205, 200)])))
# chest body: planks, iron bands with rivets, lock
c.drawRoundRect(cb, 16, 16, P(Shader=T.lin((0, cy - 115), (0, cy + 115), [C(160, 92, 48), C(100, 55, 28)])))
for k in range(1, 4):
    c.drawLine(cx - 235, cy - 115 + k * 57, cx + 235, cy - 115 + k * 57, S(C(70, 36, 18, 180), 3))
for xb in (cx - 150, cx + 150):
    c.drawRect(skia.Rect(xb - 20, cy - 115, xb + 20, cy + 115), P(Shader=T.lin((xb - 20, 0), (xb + 20, 0), [C(70, 66, 66), C(140, 135, 130), C(60, 56, 56)])))
    for k in range(5):
        c.drawCircle(xb, cy - 95 + k * 47, 5, P(C(200, 195, 185)))
c.drawRect(skia.Rect(cx - 235, cy - 125, cx + 235, cy - 100), P(Shader=T.lin((0, cy - 125), (0, cy - 100), [C(150, 145, 140), C(70, 66, 66)])))
c.drawRoundRect(skia.Rect(cx - 34, cy - 100, cx + 34, cy - 30), 10, 10, P(Shader=T.lin((cx - 34, 0), (cx + 34, 0), [C(200, 150, 60), C(255, 215, 110), C(170, 120, 40)])))
c.drawCircle(cx, cy - 72, 8, P(C(40, 25, 15)))
c.drawRect(skia.Rect(cx - 3, cy - 72, cx + 3, cy - 52), P(C(40, 25, 15)))
c.drawRoundRect(cb, 16, 16, S(T.OUT, 8))
for k in range(12):   # spilled coins on the planks
    T.coin(c, cx + rr.uniform(-360, 340), cy + 160 + rr.uniform(0, 260), rr.uniform(16, 26), flat=True)
deck = arr(deck_s)
gold_glow = np.zeros((H, W, 4), np.float32)
yy, xx = np.mgrid[0:H, 0:W]
gd = np.exp(-(((xx - cx) / 330.0) ** 2 + ((yy - (cy - 170)) / 230.0) ** 2))

# =========================================================================================== CHARACTERS (+ cel shade, rim, shadows)
HER = dict(skin=(150, 95, 65), hair="curly", hair_col=(40, 25, 20), coat=(245, 245, 240), pants=(60, 90, 150), nose="small", collar=(70, 170, 190))
HIM = dict(skin=(200, 140, 100), hair="neat", hair_col=(40, 28, 22), coat=(80, 80, 90), pants=(90, 95, 110), nose="long")
PH = dict(eyes="wide", brows="up", mouth="O", look=(0.8, 0.1), hands=[(5, -55), (-5, -55)], lean=-3, tilt=-8)
PS = dict(eyes="squint", brows="smug", mouth="grin", look=(-0.6, 0), hands=[(-35, 115), (25, -135)], lean=2, tilt=7)
chars = []
for (x, y, s, look, pose) in ((190, 1560, 1.45, HIM, PH), (800, 1800, 1.75, HER, PS)):
    cs = surf()
    T.person(cs.getCanvas(), x, y, s, look, pose, 0.3)
    if look is HER:
        hx, hy = T.hand_pos(x, y, s, pose, 1)
        T.coin(cs.getCanvas(), hx + 6, hy - 52, 36)
    chars.append((arr(cs), x, y, s))


def shifted(a, dx, dy):
    return np.roll(np.roll(a, dy, axis=0), dx, axis=1)


img = over(sky, deck)
for ch, x, y, s in chars:
    A = ch[..., 3]
    # cast shadow: silhouette squashed toward the camera (sun is behind them), blurred, multiplied onto the deck
    sil = Image.fromarray((A * 255).astype(np.uint8))
    h0 = int(y)
    top = sil.crop((0, 0, W, h0)).transpose(Image.FLIP_TOP_BOTTOM).resize((W, int(h0 * 0.28)))
    sh = Image.new("L", (W, H), 0)
    sh.paste(top, (-18, h0 - 6))
    sh = np.asarray(sh.filter(ImageFilter.GaussianBlur(9))).astype(np.float32) / 255
    img[..., :3] *= (1 - 0.55 * sh[..., None] * np.array([1.0, 1.05, 0.9]))
    # cel shade: the side away from the sun/lantern (down-left) gets a cool shadow band
    shade = np.clip(A - shifted(A, 14, -10), 0, 1)
    shade = blur(np.dstack([shade] * 4), 1.2)[..., 0]
    ch[..., :3] = ch[..., :3] * (1 - 0.32 * shade[..., None] * np.array([1.0, 0.95, 0.75]))
    # rim light: warm sunset edge on the up/right sides
    rim = np.clip(A - shifted(A, -9, 7), 0, 1)
    ch[..., :3] = np.clip(ch[..., :3] + 0.55 * rim[..., None] * np.array([1.0, 0.75, 0.45]), 0, 1)
    # gold bounce light on the side facing the chest
    bounce = gd[..., None] * 0.25 * np.array([1.0, 0.75, 0.3])
    ch[..., :3] = np.clip(ch[..., :3] + bounce * A[..., None], 0, 1)
    img = over(img, ch)
# light pools: chest glow + lantern
img[..., :3] += gd[..., None] * 0.22 * np.array([1.0, 0.72, 0.28])
ld = np.exp(-(((xx - LX) / 260.0) ** 2 + ((yy - LY) / 260.0) ** 2))
img[..., :3] += ld[..., None] * 0.12 * np.array([1.0, 0.7, 0.35])
# sparkles on the gold and her coin
sp = surf()
spc = sp.getCanvas()
for k in range(9):
    T.sparkle(spc, cx + rr.uniform(-200, 60), cy - 130 - rr.uniform(0, 140), rr.uniform(10, 22))   # kept off her face
hx, hy = T.hand_pos(800, 1800, 1.75, PS, 1)
T.sparkle(spc, hx + 44, hy - 100, 40)
img = over(img, arr(sp))
# =========================================================================================== TITLE
if TITLE:
    ts = surf()
    tc = ts.getCanvas()
    lines = (("EVERY COIN...", 92, 300, [C(255, 255, 255), C(235, 225, 255)]), ("WAS FAKE", 160, 455, [C(255, 236, 140), C(255, 170, 40)]),
             ("the 1880s trick that fooled a millionaire", 48, 535, [C(255, 240, 225), C(255, 220, 200)]))
    for txt, size, y, grad in lines:
        f = skia.Font(T.FB, size)
        w = f.measureText(txt)
        x = (W - w) / 2
        tc.drawString(txt, x + 6, y + 8, f, P(C(10, 0, 20, 160), MaskFilter=BLUR(6)))
        tc.drawString(txt, x, y, f, S(C(25, 10, 30), size * 0.17))
        tc.drawString(txt, x, y, f, P(Shader=T.lin((0, y - size), (0, y), grad)))
    img = over(img, arr(ts))
# =========================================================================================== FINISH: bloom, grade, vignette, grain
rgb = np.clip(img[..., :3], 0, 1)
bright = np.clip((rgb - 0.72) / 0.28, 0, 1) * rgb
rgb = rgb + 0.55 * blur(np.dstack([bright, np.ones((H, W, 1), np.float32)]), 22)[..., :3] + 0.25 * blur(
    np.dstack([bright, np.ones((H, W, 1), np.float32)]), 6)[..., :3]
lum = rgb.mean(axis=2, keepdims=True)
rgb = rgb + (1 - lum) * 0.04 * np.array([-0.4, 0.0, 0.6]) + lum * 0.05 * np.array([0.6, 0.2, -0.5])   # teal shadows, warm highlights
vig = 1 - 0.42 * np.clip((((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.56) / (H * 0.62)) ** 2), 0, 1)[..., None]
rgb = rgb * vig
rgb = rgb + np.random.default_rng(1).normal(0, 0.012, (H, W, 1))
Image.fromarray(np.clip(rgb * 255, 0, 255).astype(np.uint8)).save(OUT)
print("wrote", OUT)
