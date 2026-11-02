"""YouTube Short #19, code-drawn edition: "People Used to RENT Pineapples?!" (Skia toon style).

Every scene is drawn in code with the Skia toon kit (toon.py) + the 'ultimate' stage (ultimate.py),
then the classic title/subtitle/slam/stamp text, gold splat transitions and sound design are added
by the usual pipeline. Same voice, cuts and cues as the Gemini edition.

Usage: python make_toon.py final.mp4 [scene,scene,...]   (run inside short/ultimate)
"""
import json
import math
import os
import sys

import numpy as np
import skia
from PIL import Image, ImageDraw

OUTFILE = sys.argv[1]
ONLY = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 and sys.argv[2][0].isdigit() else None
STILLS = sys.argv[3].split(",") if len(sys.argv) > 3 else None
sys.argv = [sys.argv[0], "base_toon.mp4"]
sys.path.insert(0, "..")

import audio  # noqa: E402
import make_ketchup  # noqa: E402
import make_salt  # noqa: E402
import make_short as base  # noqa: E402
import ultimate as U  # noqa: E402
from fx import impact  # noqa: E402
from make_honey import slam  # noqa: E402
from make_ketchup import splat, stamp  # noqa: E402
from make_short import F_MID, FONT_B, FONT_M, H, W, font, tag, text_block  # noqa: E402
from style import heading  # noqa: E402
from timing import Timeline  # noqa: E402
from toon import *  # noqa: E402,F401,F403

GOLD, ICE = (255, 200, 60), (170, 215, 255)
make_ketchup.SPLAT_COLOR = (250, 195, 50)
base.HOOK_SKIP = 0.0
base.CRF = 16  # sharper Full HD export
CUE = {}


def title(img, t, text, sub=None, sub_at=1.0, y=400, sub_color=(255, 235, 210)):
    heading(img, t, text, sub, sub_at, F_MID, y, sub_color=sub_color)


def mascot(**kw):
    st = dict(squash=0.0, sway=0.0, eye_open=1.0, wink=0.0, pupil=1.0, brow=0.0, smug=0.3, mouth=0.0, glasses=None, glasses_rot=0.0, glint=0.0)
    st.update(kw)
    return st


def blinking(t, ph=0.0):
    return ((t + ph) % 3.3) < 0.11


# ---------- scenes (Skia art only; text is added afterwards) ----------

def art_hook(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, 1600), [C(70, 30, 45), C(110, 45, 60), C(60, 22, 35)])))
    for x in (90, 540, 990):  # gold pilasters
        c.drawRect(skia.Rect(x - 40, 300, x + 40, 1620), P(Shader=lin((x - 40, 0), (x + 40, 0), [C(120, 80, 30), C(240, 200, 110), C(110, 70, 25)])))
    for x in (315, 765):  # tall arched windows
        p = skia.Path()
        p.addRRect(skia.RRect.MakeRectXY(skia.Rect(x - 120, 520, x + 120, 1500), 120, 120))
        c.drawPath(p, P(Shader=lin((0, 520), (0, 1500), [C(30, 40, 90), C(60, 60, 120)])))
        c.drawPath(p, S(C(220, 170, 80), 10))
        c.drawLine(x, 520, x, 1500, S(C(220, 170, 80), 6))
    c.drawRect(skia.Rect(0, 1600, W, H), P(Shader=lin((0, 1600), (0, H), [C(120, 70, 35), C(60, 30, 15)])))
    for k in range(14):
        c.drawLine(k * 90 - 300, H, k * 90 + 100, 1600, S(C(40, 20, 10, 90), 3))
    chandelier(c, 190, 1000, t, 0.9)
    chandelier(c, 890, 980, t + 1.3, 0.9)
    rented = CUE["rented"]
    react = ease((t - rented - 0.1) / 0.3)
    for i, (x, s) in enumerate([(110, 1.0), (300, 0.95), (790, 0.95), (980, 1.0)]):
        pose = dict(mouth="O" if react > 0.5 else "smile", eyes="wide" if react > 0.5 else "open", brows="up" if react > 0.5 else "flat",
                    lean=(-1 if x > 540 else 1) * -6 * react * (1 + 0.4 * spring(t, rented + 0.1, 2, 4)), look=(1 if x < 540 else -1, -0.5),
                    hands=[(-30, 140), (30, 140)] if react < 0.5 else [(25, -40), (-25, -40)], blink=blinking(t, i))
        person(c, x, 1700, s, crowd_look(i), pose, t)
    bob = math.sin(2 * math.pi * t / 1.5)
    pose = dict(hands=[(-70, -235 - 18 * bob), (45, 110)], mouth="smile", brows="smug", eyes="open", look=(-0.6, -0.8),
                tilt=4 * math.sin(t * 2.2), blink=blinking(t, 1.7), squash=0.03 * spring(t, rented, 2.5, 4))
    person(c, 560, 1840, 1.55, LADY, pose, t)
    hx, hy = hand_pos(560, 1840, 1.55, pose, -1)
    pine(c, hx, hy - 85, 1.05, rot=6 * bob, t=t)
    for k in range(5):
        a = t * 1.3 + k * 1.26
        sparkle(c, hx + math.cos(a) * 90, hy - 85 + math.sin(a) * 110, 10 + 6 * math.sin(t * 4 + k), 220)


def art_price(c, t):
    U.T_EIGHT = CUE["eight"]
    U.background(c, t, math.sin(t * 0.45) * 40)
    pulse = math.exp(-3 * max(0, t - CUE["eight"])) if t > CUE["eight"] else 0
    U.spotlight(c, t, pulse)
    U.pedestal(c, t)
    e = CUE["eight"]
    shock = e < t
    hop = spring(t, e + 0.05, 2.4, 3.2)
    st = mascot(squash=0.08 * hop + 0.015 * math.sin(t * 2.4), sway=-14 * hop + 3 * math.sin(t * 1.3),
                eye_open=0.1 if (blinking(t, 0.8) and not shock) else 1.0, pupil=0.75 if shock else 1.0,
                brow=24 if shock else 0, mouth=min(1, (t - e) * 5) if shock else 0.0)
    c.drawOval(skia.Rect(400, 1385, 680, 1430), P(C(60, 0, 10, 150), MaskFilter=blur(14)))
    c.save()
    c.translate(540, 1415)
    U.pineapple(c, t, math.sin(t * 3) * 0.6 if shock else 0, 0.6 if shock else 0, st)
    c.restore()
    for x, y, r, face, speed in U.coins_at(t):
        U.draw_coin(c, x, y, r, face, speed)


def art_beach(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, 1260), [C(40, 30, 80), C(150, 70, 110), C(250, 150, 80)], [0, 0.55, 1])))
    glow(c, 700, 1230, 420, (255, 180, 100), 120)
    c.drawCircle(700, 1235, 110, P(Shader=rad(700, 1235, 110, [C(255, 245, 200), C(255, 190, 90)])))
    c.drawRect(skia.Rect(0, 1250, W, 1520), P(Shader=lin((0, 1250), (0, 1520), [C(230, 130, 90), C(60, 60, 110)])))
    for k in range(30):  # sun glints on the sea
        x = 450 + (k * 97) % 520 + math.sin(t + k) * 14
        y = 1270 + (k * 53) % 220
        a = math.sin(t * 2.4 + k * 1.7)
        if a > 0.2:
            c.drawLine(x - 22 * a, y, x + 22 * a, y, S(C(255, 225, 160, 200 * a), 4))
    ship(c, 860, 1300, 0.55, t)
    c.drawRect(skia.Rect(0, 1500, W, H), P(Shader=lin((0, 1500), (0, H), [C(235, 190, 130), C(180, 120, 70)])))
    wave = skia.Path()
    wave.moveTo(0, 1515)
    for k in range(13):
        wave.quadTo(k * 90 + 45, 1500 + 14 * math.sin(t * 2 + k), k * 90 + 90, 1515)
    wave.lineTo(W, 1540)
    wave.lineTo(0, 1540)
    c.drawPath(wave, P(C(255, 255, 255, 170)))
    palm(c, 30, 1720, 760, t, 1)
    palm(c, 1060, 1640, 640, t + 1, -1)
    # pineapple plant
    px, py = 820, 1760
    for k in range(9):
        a = math.radians(-170 + k * 20 + math.sin(t * 1.5 + k) * 3)
        p = skia.Path()
        p.moveTo(px, py)
        p.quadTo(px + math.cos(a) * 120, py + math.sin(a) * 150 - 40, px + math.cos(a) * 230, py + math.sin(a) * 120 + 20)
        p.quadTo(px + math.cos(a) * 110, py + math.sin(a) * 120 - 10, px, py)
        blob(c, p, (60, 130, 70), 1.4, 0.6)
    pine(c, px, py - 110, 1.0, t=t)
    reach = ease(t / 2.2)
    pose = dict(lean=6 + 2 * reach, hands=[(30, 130), (130 + 60 * reach, 40 + 20 * reach)], eyes="wide", look=(1, 0.4), brows="up",
                mouth="O" if t > CUE["fruit"] else "smile", tilt=5 * math.sin(t * 1.8), blink=blinking(t, 0.4))
    person(c, 400, 1830, 1.5, COLUMBUS, pose, t)
    burst(c, t, CUE["fruit"], px, py - 110)


def art_hold(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(35, 25, 25), C(80, 50, 35), C(40, 25, 20)])))
    for k in range(30):
        c.drawLine(0, 300 + k * 55, W, 300 + k * 55 + 10, S(C(20, 12, 10, 120), 4))
    for k in range(4):
        c.drawArc(skia.Rect(-200, 200 + k * 140, W + 200, 1600 + k * 140), 200, 140, False, S(C(70, 45, 30), 30))
    ang = math.radians(10 * math.sin(2 * math.pi * t / 1.8))
    lx, ly = 280 + 260 * math.sin(ang), 560 + 260 * math.cos(ang)
    c.drawLine(280, 560, lx, ly, S(C(60, 50, 40), 5))
    blob(c, rrect(lx - 38, ly, lx + 38, ly + 90, 10), (90, 70, 40))
    c.drawRect(skia.Rect(lx - 26, ly + 12, lx + 26, ly + 78), P(C(255, 210, 120)))
    glow(c, lx, ly + 45, 420, (255, 170, 80), int(150 * flicker(t, 1)))
    shake = 7 * math.sin(t * 7) * (0.6 + 0.4 * math.sin(t))
    pose = dict(hands=[(60, -79), (20, 150)], eyes="squint", mouth="disgust", brows="angry", tilt=shake, lean=-3)
    person(c, 640, 1720, 1.55, COLUMBUS, pose, t)
    stink(c, 300, 1650, t)
    stink(c, 820, 1660, t, 1.3)
    for cx, cy, w in ((210, 1900, 330), (560, 1920, 300), (900, 1900, 330)):
        for k in range(3):
            pine(c, cx - 90 + k * 90, cy - 200, 0.9, rot=(k - 1) * 12, rotten=0.0 if (cx == 560 and k == 1) else 0.9, t=t)
        crate(c, cx, cy, w, 190)
    for k in range(6):
        fly(c, 200 + (k * 170) % 800, 1560 + (k * 37) % 120, t, k * 1.7)


def art_snow(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, 1500), [C(10, 15, 40), C(40, 55, 100), C(90, 90, 140)])))
    c.drawCircle(860, 1000, 60, P(C(240, 240, 220)))
    glow(c, 860, 1000, 240, (200, 210, 255), 70)
    for k in range(12):  # brick wall
        y = 1250 + k * 32
        for j in range(12):
            x = j * 100 + (50 if k % 2 else 0)
            c.drawRect(skia.Rect(x + 2, y + 2, x + 98, y + 30), P(C(110, 55, 50)))
    c.drawRect(skia.Rect(0, 1215, W, 1260), P(C(235, 240, 255)))
    for x, h in ((120, 600), (950, 500)):  # bare trees
        c.drawLine(x, 1260, x + 20, 1260 - h, S(C(40, 30, 35), 26))
        for k in range(5):
            y = 1260 - h * (0.4 + k * 0.12)
            c.drawLine(x + 15, y, x + 15 + (1 if k % 2 else -1) * 150, y - 90, S(C(40, 30, 35), 10))
    c.drawRect(skia.Rect(0, 1600, W, H), P(Shader=lin((0, 1600), (0, H), [C(220, 230, 250), C(170, 185, 220)])))
    shiver = math.sin(t * 40) * 2
    droop = math.sin(math.pi * min(1, t / 4.0))
    pose = dict(hands=[(30, 80), (-30, 80)], eyes="sad", mouth="frown", brows="sad", tilt=-5 * droop, look=(0.4, 0.8), blink=blinking(t, 2))
    person(c, 540 + shiver, 1830, 1.6, GARDENER, pose, t)
    lx, ly = hand_pos(540, 1830, 1.6, pose, -1)
    rx, ry = hand_pos(540, 1830, 1.6, pose, 1)
    px, py = (lx + rx) / 2, (ly + ry) / 2 - 10
    for k in range(7):  # dead plant drooping
        a = math.radians(-150 + k * 20)
        p = skia.Path()
        p.moveTo(px, py - 50)
        tipx, tipy = px + math.cos(a) * 110, py - 50 + math.sin(a) * 60 + 90 * (0.6 + 0.2 * math.sin(t * 2 + k))
        p.quadTo(px + math.cos(a) * 70, py - 160, tipx, tipy)
        c.drawPath(p, S(C(90, 80, 60), 10))
    pot = skia.Path()
    pot.moveTo(px - 75, py - 60)
    pot.lineTo(px + 75, py - 60)
    pot.lineTo(px + 55, py + 60)
    pot.lineTo(px - 55, py + 60)
    pot.close()
    blob(c, pot, (190, 100, 70))
    for side in (-1, 1):  # hands over the pot
        blob(c, oval(px + side * 70, py, 24, 24), GARDENER["skin"])
    drift = skia.Path()
    drift.moveTo(0, 1760)
    drift.cubicTo(300, 1690, 760, 1700, W, 1750)
    drift.lineTo(W, H)
    drift.lineTo(0, H)
    c.drawPath(drift, P(Shader=lin((0, 1700), (0, H), [C(250, 252, 255), C(200, 210, 235)])))
    for k in range(3):  # breath puffs
        ph = (t * 0.8 + k / 3) % 1
        c.drawCircle(560 + ph * 60, 1260 - ph * 90, 20 + ph * 40, P(C(240, 245, 255, 110 * (1 - ph)), MaskFilter=blur(10)))
    snowflakes(c, t)


def art_hothouse(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(15, 20, 35), C(50, 40, 50), C(90, 50, 30)])))
    for k in range(9):
        x = k * 135
        c.drawLine(x, 300, x, 1550, S(C(30, 35, 40), 10))
    for k in range(4):
        c.drawArc(skia.Rect(-150 + k * 20, 200 + k * 100, W + 150 - k * 20, 1300 + k * 100), 180, 180, False, S(C(30, 35, 40), 12))
    glow(c, 140, 1600, 500, (255, 130, 50), int(170 * flicker(t, 0)))
    c.drawRect(skia.Rect(0, 1550, W, H), P(Shader=lin((0, 1550), (0, H), [C(90, 55, 30), C(50, 30, 15)])))
    for row, (y, s) in enumerate(((1620, 0.55), (1880, 0.75))):
        for k in range(6):
            x = 90 + k * 180 + row * 60
            mound = oval(x, y + 30, 90 * s / 0.55, 40)
            blob(c, mound, (110, 70, 40), 1.2, 0.7, outline=False)
            pine(c, x, y - 40 * s / 0.55, s, t=t)
    scoop = math.sin(2 * math.pi * t / 1.6)
    pose = dict(hands=[(60, -79), (-60 + 20 * scoop, 130 - 30 * scoop)], eyes="squint", mouth="disgust", brows="angry",
                tilt=5 * math.sin(2 * math.pi * t / 0.6), lean=4)
    person(c, 650, 1800, 1.6, GARDENER, pose, t)
    hx, hy = hand_pos(650, 1800, 1.6, pose, 1)
    a = math.radians(205 - 18 * scoop)
    bx, by = hx + math.cos(a) * 360, hy - math.sin(a) * -1 * 0 + abs(math.sin(a)) * 0 + 160 + 60 * scoop
    c.drawLine(hx + 40, hy - 40, bx, by, S(OUT, 30))
    c.drawLine(hx + 40, hy - 40, bx, by, S(C(150, 100, 55), 20))
    blade = skia.Path()
    blade.moveTo(bx - 110, by - 30)
    blade.lineTo(bx + 50, by - 45)
    blade.lineTo(bx + 35, by + 70)
    blade.lineTo(bx - 95, by + 70)
    blade.close()
    blob(c, blade, (150, 150, 160))
    blob(c, oval(bx - 30, by - 40, 85, 45), (100, 60, 30), 1.3, 0.6)
    for n in range(4):  # manure tossed at the top of each scoop
        t0 = 0.2 + n * 1.6
        dt = t - t0
        if 0 < dt < 1.0:
            for j in range(5):
                x = bx - 20 + (-60 + 40 * j) * dt
                y = by - 30 - (620 + 70 * (j % 3)) * dt + 1100 * dt * dt
                blob(c, oval(x, y, 16 + 4 * (j % 2), 12), (110, 70, 35), 1.4, 0.6, outline=False)
    stink(c, 300, 1500, t)
    stink(c, 900, 1520, t, 0.7)
    for n in range(8):  # sweat
        dt = t - (0.3 + n * 0.62)
        if 0 < dt < 0.6:
            side = 1 if n % 2 else -1
            sx, sy = 650 + side * (120 + 300 * dt), 1150 - 350 * dt + 1300 * dt * dt
            c.drawCircle(sx, sy, 12, P(C(190, 225, 255, 230)))
    for k in range(5):  # steam
        ph = (t * 0.3 + k * 0.2) % 1
        c.drawCircle(150 + k * 200 + math.sin(t + k) * 30, 1650 - ph * 500, 50 + ph * 90, P(C(230, 220, 210, 70 * math.sin(ph * math.pi)), MaskFilter=blur(30)))


def art_king(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, 1500), [C(30, 25, 60), C(120, 70, 110), C(240, 150, 110)])))
    for k in range(3):
        x = 180 + k * 360
        p = skia.Path()
        p.addRRect(skia.RRect.MakeRectXY(skia.Rect(x - 130, 900, x + 130, 1520), 130, 130))
        c.drawRect(skia.Rect(x - 180, 820, x + 180, 1520), P(C(200, 180, 170)))
        c.drawPath(p, P(Shader=lin((0, 900), (0, 1520), [C(120, 80, 120), C(240, 160, 120)])))
    c.drawRect(skia.Rect(0, 800, W, 840), P(C(170, 150, 145)))
    for k in range(7):
        blob(c, oval(k * 170, 1540, 120, 70), (40, 90, 50), 1.3, 0.6, outline=False)
    c.drawRect(skia.Rect(0, 1560, W, H), P(Shader=lin((0, 1560), (0, H), [C(150, 120, 100), C(90, 70, 60)])))
    for x in (60, 1020):
        c.drawLine(x, 1600, x, 1150, S(C(40, 35, 35), 12))
        c.drawRect(skia.Rect(x - 25, 1090, x + 25, 1160), P(C(255, 210, 130)))
        glow(c, x, 1125, 260, (255, 180, 90), int(140 * flicker(t, x)))
    h = CUE["handed"]
    lift = ease((t - h + 0.4) / 0.8)
    gp = dict(hands=[(130, 10 - 50 * lift), (170, 30 - 50 * lift)], eyes="open", mouth="grin", brows="up", look=(1, -0.6),
              tilt=4 * math.sin(t * 3), blink=blinking(t, 0.5))
    person(c, 250, 1840, 1.4, GARDENER, gp, t)
    ax, ay = hand_pos(250, 1840, 1.4, gp, -1)
    bx, by = hand_pos(250, 1840, 1.4, gp, 1)
    px, py = (ax + bx) / 2, (ay + by) / 2 - 70
    pine(c, px, py, 1.1, t=t)
    lean = -10 * ease((t - h) / 0.6) + 1.5 * math.sin(t * 1.6)
    kp = dict(lean=lean, hands=[(-110, 50 - 20 * ease((t - h) / 0.6)), (-60, 70)], eyes="wide", mouth="O" if t > h else "smile", brows="up",
              look=(-1, 0.5), blink=blinking(t, 1.2) and t < h)
    person(c, 850, 1840, 1.5, KING, kp, t)
    burst(c, t, h, px, py, n=14)
    for k in range(4):
        a = t * 1.5 + k * 1.57
        sparkle(c, px + math.cos(a) * 80, py + math.sin(a) * 95, 8, 200)


def art_trophy(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(25, 45, 40), C(45, 70, 60), C(20, 35, 30)])))
    for k in range(9):
        for j in range(14):
            c.drawCircle(60 + k * 120 + (60 if j % 2 else 0), 80 + j * 110, 16, P(C(255, 255, 255, 18)))
    went = CUE["went"]
    rot = ease((t - went) / 0.8)
    for x in (170, 910):  # candelabras
        c.drawLine(x, 1500, x, 1250, S(C(200, 170, 90), 12))
        c.drawLine(x - 70, 1270, x + 70, 1270, S(C(200, 170, 90), 10))
        for k in (-70, 0, 70):
            candle(c, x + k, 1268 - (20 if k == 0 else 0), t, k + x)
    c.drawRect(skia.Rect(0, 1480, W, H), P(Shader=lin((0, 1480), (0, H), [C(250, 250, 245), C(200, 200, 205)])))
    c.drawOval(skia.Rect(250, 1430, 830, 1560), P(Shader=lin((250, 0), (830, 0), [C(150, 150, 160), C(240, 240, 250), C(140, 140, 150)])))
    c.drawOval(skia.Rect(250, 1430, 830, 1560), S(C(110, 110, 120), 5))
    st = mascot(squash=0.015 * math.sin(t * 2.4), sway=3 * math.sin(t * 1.3) - 20 * rot, smug=1.0 - rot,
                eye_open=0.1 if blinking(t, 0.3) else (1 - 0.45 * rot), brow=-10 * rot, pupil=1 - 0.3 * rot)
    c.save()
    c.translate(540, 1495)
    c.scale(0.9, 0.9)
    if rot > 0:
        mat = [1 - 0.45 * rot, 0.15 * rot, 0, 0, 0, 0.1 * rot, 1 - 0.5 * rot, 0, 0, 0, 0, 0, 1 - 0.6 * rot, 0, 0, 0, 0, 0, 1, 0]
        c.saveLayer(None, P(ColorFilter=skia.ColorFilters.Matrix(mat)))
    U.pineapple(c, t, 0.0, 0.3 * rot, st)
    if rot > 0:
        for k in range(7):
            c.drawCircle(-120 + (k * 47) % 240, -300 + (k * 67) % 260, 14 + (k % 3) * 6, P(C(70, 80, 45, 200 * rot)))
        c.restore()
    c.restore()
    if rot > 0.2:
        for k in range(3):
            fly(c, 540 + (k - 1) * 120, 1050 + k * 60, t, k * 2.1)
        stink(c, 540, 900, t)
    else:
        for k in range(6):
            a = t * 1.4 + k * 1.05
            sparkle(c, 540 + math.cos(a) * 240, 1250 + math.sin(a) * 260, 9 + 4 * math.sin(t * 5 + k), 200)


def art_shop(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(35, 25, 30), C(80, 55, 40), C(40, 25, 20)])))
    for row in range(4):  # shelves with jars
        y = 820 + row * 190
        c.drawRect(skia.Rect(0, y, W, y + 18), P(C(100, 65, 35)))
        for k in range(9):
            col = [(120, 170, 90), (200, 120, 60), (150, 100, 160), (220, 190, 90)][(k + row) % 4]
            x = 40 + k * 120 + (row % 2) * 40
            blob(c, rrect(x, y - 110 + (k % 2) * 20, x + 70, y, 14), col, 1.4, 0.7)
    lx, ly = 760, 650 + 10 * math.sin(t * 1.5)
    c.drawLine(760, 300, lx, ly, S(C(50, 40, 30), 5))
    blob(c, rrect(lx - 40, ly, lx + 40, ly + 100, 10), (60, 45, 30))
    c.drawRect(skia.Rect(lx - 28, ly + 14, lx + 28, ly + 86), P(C(255, 215, 130)))
    glow(c, lx, ly + 50, 480, (255, 180, 90), int(160 * flicker(t, 2)))
    sp = dict(hands=[(-30, -40), (150 + 25 * ease((t - CUE["same"]) / 0.5), 20)], eyes="open", mouth="smile", brows="smug", look=(1, 0.2),
              tilt=3 * math.sin(t * 2.6), blink=blinking(t, 0.9))
    person(c, 290, 1820, 1.5, SHOP, sp, t)
    wx, wy = hand_pos(290, 1820, 1.5, sp, -1)
    sw = math.radians(25 * math.sin(2 * math.pi * t / 1.2))
    ex, ey = wx + 110 * math.sin(sw), wy + 110 * math.cos(sw)
    c.drawLine(wx, wy, ex, ey, S(C(230, 190, 90), 4))
    c.drawCircle(ex, ey + 30, 34, P(Shader=lin((ex - 34, ey), (ex + 34, ey + 60), [C(255, 235, 150), C(200, 150, 50)])))
    c.drawCircle(ex, ey + 30, 26, P(C(250, 248, 240)))
    for k, ln in ((t * 2, 18), (t * 0.3, 13)):
        c.drawLine(ex, ey + 30, ex + ln * math.sin(k), ey + 30 - ln * math.cos(k), S(C(30, 30, 30), 3))
    hx, hy = hand_pos(290, 1820, 1.5, sp, 1)
    c.drawRect(skia.Rect(0, 1560, 700, 1700), P(Shader=lin((0, 1560), (0, 1700), [C(150, 100, 55), C(90, 55, 30)])))
    c.drawRect(skia.Rect(0, 1700, 700, H), P(C(70, 42, 22)))
    for k in range(7):
        coin(c, 420 + k * 34, 1572 - (k % 3) * 8, 20, flat=True)
    bounce = abs(math.sin(t * 4.5)) * 18
    lp = dict(hands=[(-130, -10 - bounce * 0.5), (-60, 40)], eyes="wide", mouth="grin", brows="up", look=(-1, 0), tilt=4 * math.sin(t * 4.5))
    person(c, 820, 1860 - bounce, 1.4, LADY, lp, t)
    pine(c, hx + 20, hy - 70, 1.0, t=t)


def art_house(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, 1500), [C(15, 10, 40), C(70, 40, 100), C(240, 140, 90)], [0, 0.6, 1])))
    r = __import__("random").Random(3)
    for i in range(70):
        x, y = r.uniform(0, W), r.uniform(0, 1000)
        tw = 0.5 + 0.5 * math.sin(t * r.uniform(1.5, 3.5) + i)
        c.drawCircle(x, y, 1.5 + 2.5 * tw, P(C(255, 250, 230, 90 + 150 * tw)))
    for k, (y, col) in enumerate(((1380, (50, 45, 80)), (1450, (35, 35, 60)))):
        p = skia.Path()
        p.moveTo(0, y)
        for j in range(6):
            p.quadTo(j * 216 + 108, y - 90 + 40 * (j % 2), j * 216 + 216, y)
        p.lineTo(W, H)
        p.lineTo(0, H)
        c.drawPath(p, P(C(*col)))
    c.drawRect(skia.Rect(0, 1650, W, H), P(Shader=lin((0, 1650), (0, H), [C(30, 50, 40), C(15, 25, 20)])))
    blob(c, rrect(170, 1330, 910, 1660, 8), (150, 135, 120), 1.15, 0.7)
    for k in range(6):
        x = 220 + k * 120
        if k in (2, 3):
            continue
        c.drawRect(skia.Rect(x, 1420, x + 60, 1520), P(C(255, 200, 110)))
        glow(c, x + 30, 1470, 120, (255, 180, 90), int(110 * flicker(t, k)))
    c.drawRoundRect(skia.Rect(480, 1470, 600, 1660), 60, 60, P(C(255, 190, 100)))
    blob(c, rrect(400, 1130, 680, 1350, 10), (160, 145, 130), 1.15, 0.7)
    for k in range(3):
        c.drawRect(skia.Rect(430 + k * 85, 1180, 470 + k * 85, 1290), P(C(255, 200, 110)))
    # the giant stone pineapple on top
    c.save()
    c.translate(540, 920)
    for i, (a, ln) in enumerate([(-60, 150), (60, 150), (-35, 200), (35, 200), (-12, 250), (12, 250), (0, 270)]):
        c.save()
        c.translate(0, -160)
        c.rotate(a)
        p = skia.Path()
        p.moveTo(0, 0)
        p.cubicTo(36, -ln * 0.35, 18, -ln * 0.8, 0, -ln)
        p.cubicTo(-18, -ln * 0.8, -36, -ln * 0.35, 0, 0)
        blob(c, p, (150, 150, 145), 1.3, 0.6)
        c.restore()
    body = oval(0, 50, 170, 230)
    blob(c, body, (165, 160, 150), 1.25, 0.6)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    for k in range(-10, 11):
        c.drawLine(k * 50 - 300, -250, k * 50 + 300, 350, S(C(100, 95, 90), 5))
        c.drawLine(k * 50 + 300, -250, k * 50 - 300, 350, S(C(100, 95, 90), 5))
    c.restore()
    c.restore()
    burst(c, t, CUE["giant"], 540, 900, n=16, reach=330)
    for i, (x, lk) in enumerate([(130, 0), (300, 1), (790, 3), (960, 2)]):
        pose = dict(mouth="O", eyes="wide", brows="up", look=(0, -1), hands=[(-20, 150), (60 if x < 540 else -60, -170)], tilt=-8 if x < 540 else 8,
                    blink=blinking(t, i))
        person(c, x, 1860, 0.75, crowd_look(lk), pose, t)


def art_market(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(15, 20, 45), C(40, 40, 80), C(30, 20, 30)])))
    for k, (y0, sag) in enumerate(((520, 90), (760, 70))):
        pts = []
        for j in range(13):
            x = j * 90
            y = y0 + sag * math.sin(math.pi * j / 12)
            pts.append((x, y))
        p = skia.Path()
        p.moveTo(*pts[0])
        for x, y in pts[1:]:
            p.lineTo(x, y)
        c.drawPath(p, S(C(20, 20, 20), 3))
        for j, (x, y) in enumerate(pts):
            f = 0.7 + 0.3 * math.sin(t * 3 + j * 1.3 + k)
            c.drawCircle(x, y + 20, 13, P(C(255, 220, 140)))
            glow(c, x, y + 20, 90, (255, 200, 110), int(120 * f))
    for x, col in ((0, (200, 60, 60)), (W - 260, (60, 140, 90))):
        blob(c, rrect(x, 1180, x + 260, 1260, 10), col)
        c.drawRect(skia.Rect(x + 20, 1260, x + 240, 1700), P(C(70, 50, 40)))
    c.drawRect(skia.Rect(0, 1700, W, H), P(C(40, 30, 30)))
    k = 0
    for row in range(7):  # pineapple mountain
        n = 8 - row
        for j in range(n):
            x = 540 + (j - (n - 1) / 2) * 120
            y = 1880 - row * 95
            pine(c, x, y, 0.95, rot=((j * 37 + row * 11) % 21) - 10, t=t + k)
            k += 1
    bounce = abs(math.sin(t * 5)) * 16
    kp = dict(hands=[(55, -55), (90, -200 - 20 * math.sin(t * 6))], eyes="closed", mouth="laugh", brows="up", tilt=6 * math.sin(t * 5))
    person(c, 540, 1240 - bounce, 1.2, KID, kp, t)
    hx, hy = hand_pos(540, 1240 - bounce, 1.2, kp, -1)
    c.drawCircle(hx - 20, hy + 5, 34, P(C(255, 225, 90)))
    c.drawCircle(hx - 20, hy + 5, 34, S(C(200, 140, 40), 7))
    c.drawCircle(hx - 20, hy + 5, 10, P(C(240, 190, 70)))


def art_cta(c, t):
    U.T_EIGHT = -10
    U.background(c, t, 0)
    U.spotlight(c, t, 0)
    U.pedestal(c, t)
    st = mascot(glasses=0, smug=1.0, brow=10, eye_open=1.0, glint=((t * 0.7) % 1.5) / 0.4)
    c.save()
    c.translate(540, 1415)
    U.pineapple(c, t, 0, 0, st)
    c.restore()
    c.drawPaint(P(C(10, 6, 14, 150)))


ART = [art_hook, art_price, art_beach, art_hold, art_snow, art_hothouse, art_king, art_trophy, art_shop, art_house, art_market, art_cta]
PUSH = [(1.0, 1.06), (1.02, 1.1), (1.0, 1.08), (1.06, 1.0), (1.0, 1.07), (1.0, 1.08), (1.0, 1.07), (1.04, 1.12), (1.0, 1.06), (1.0, 1.06), (1.08, 1.0), (1.0, 1.0)]
ANCHOR = [(540, 1300), (540, 1250), (600, 1400), (640, 1400), (540, 1400), (650, 1400), (560, 1450), (540, 1300), (540, 1400), (540, 1200), (540, 1300), (540, 1300)]


def render_art(i, t, dur):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    z0, z1 = PUSH[i]
    z = z0 + (z1 - z0) * ease(t / dur)
    ax, ay = ANCHOR[i]
    c.save()
    c.translate(ax, ay)
    c.scale(z, z)
    c.translate(-ax + math.sin(t * 0.5) * 6, -ay + math.cos(t * 0.4) * 5)
    ART[i](c, t)
    c.restore()
    snap = surf.makeImageSnapshot()
    c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=U.BLOOM, ImageFilter=skia.ImageFilters.Blur(24, 24), BlendMode=skia.BlendMode.kPlus, Alphaf=0.45))
    c.drawPaint(P(Shader=rad(540, 1100, 1250, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 190)], [0, 0.5, 1])))
    c.drawRect(skia.Rect(0, 0, W, 900), P(Shader=lin((0, 0), (0, 900), [C(5, 4, 10, 150), C(5, 4, 10, 0)])))
    c.drawImageRect(U.GRAIN[int(t * 30) % len(U.GRAIN)], skia.Rect(0, 0, W, H), skia.SamplingOptions(), P(Alphaf=0.06, BlendMode=skia.BlendMode.kOverlay))
    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    return Image.fromarray(np.ascontiguousarray(arr))


# ---------- scenes = art + the classic text layer ----------

def scene(i, text_fn):
    def fn(img, d, t):
        img.paste(render_art(i, t, CUE["d"][i]))
        text_fn(img, t)
    return fn


def tx_hook(img, t):
    dd = ImageDraw.Draw(img, "RGBA")
    line = "In the 1700s, people"
    tw = dd.textlength(line, font=F_MID)
    dd.text(((W - tw) / 2 + 4, 255), line, font=F_MID, fill=(0, 0, 0, 140))
    dd.text(((W - tw) / 2, 250), line, font=F_MID, fill=(255, 255, 255))
    slam(img, "RENTED", 360, t, CUE["rented"], GOLD, 170)
    text_block(img, "pineapples... just to show off!", font(FONT_B, 62), 580, t, (255, 255, 255), CUE["pine"])
    text_block(img, "And one man built a HOUSE", font(FONT_B, 56), 690, t, GOLD, CUE["house"])
    text_block(img, "shaped like one!", font(FONT_B, 56), 760, t, GOLD, CUE["house"] + 0.5)
    impact(img, t, CUE["rented"] + 0.2, 18)


def tx_price(img, t):
    text_block(img, "One pineapple cost about...", font(FONT_B, 64), 260, t, (255, 255, 255), 0.25)
    slam(img, "$8,000", 400, t, CUE["eight"], GOLD, 210)
    text_block(img, "in today's money!", font(FONT_M, 54), 650, t, (255, 235, 210), CUE["todays"])
    impact(img, t, CUE["eight"] + 0.2, 20)


def tx_beach(img, t):
    tag(img, "1493", t, (230, 120, 40))
    title(img, t, "Columbus finds a strange fruit", "on an island in the Caribbean", CUE["carib"])


def tx_hold(img, t):
    title(img, t, "The long trip home...", "Almost every pineapple...", CUE["almost"])
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "ROTTED", t, CUE["rot"], col=(140, 200, 80))
    impact(img, t, CUE["rot"] + 0.15, 14)


def tx_snow(img, t):
    title(img, t, "Europe tries to grow its own", "...but the cold killed every plant.", CUE["cold"], sub_color=ICE)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "200 YEARS", t, CUE["two"], col=ICE, size=110)
    impact(img, t, CUE["two"] + 0.15, 12)


def tx_hot(img, t):
    title(img, t, "The disgusting trick", "Heated with rotting MANURE!", CUE["heated"], sub_color=(255, 215, 160))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "EWW!", t, CUE["rotting"], col=(170, 120, 60))
    impact(img, t, CUE["rotting"] + 0.15, 14)


def tx_king(img, t):
    tag(img, "KING CHARLES II", t, (200, 40, 60))
    title(img, t, "A gift for the King", "It was a royal sensation!", CUE["royal"])


def tx_trophy(img, t):
    title(img, t, "Nobody ATE them!", "Just trophies, until they rotted!", CUE["sat"])


def tx_shop(img, t):
    tag(img, "FOR RENT", t, (230, 120, 40))
    title(img, t, "Rented out for the night", "...then on to the next party!", CUE["same"])


def tx_house(img, t):
    tag(img, "SCOTLAND, 1761", t, (110, 70, 170))
    title(img, t, "A house with a PINEAPPLE on top", "...and it's still standing today!", CUE["still"])


def tx_market(img, t):
    title(img, t, "Today? Super cheap!", "Fast ships brought them everywhere", CUE["fast"], y=260)
    slam(img, "ONLY $2", 520, t, CUE["dollars"], GOLD, 160)
    impact(img, t, CUE["dollars"] + 0.2, 16)


def tx_cta(img, t):
    text_block(img, "Learned something new?", font(FONT_B, 68), 330, t, delay=0.0)
    make_salt.draw_cta(img, ImageDraw.Draw(img, "RGBA"), W / 2, 1250, t, off=CUE["cta_off"])


TEXT = [tx_hook, tx_price, tx_beach, tx_hold, tx_snow, tx_hot, tx_king, tx_trophy, tx_shop, tx_house, tx_market, tx_cta]
base.TRANSITION = splat

if __name__ == "__main__":
    vdir = os.environ.get("DM_VOICE_DIR", "../pineapple")  # e.g. ../pineapple_chris (vidIQ "Chris" voice)
    voice = f"{vdir}/voice.mp3"
    paras = json.load(open(f"{vdir}/paras.json"))
    tl = Timeline(voice)
    starts = [0.0] + [(paras[i - 1][1] + paras[i][0]) / 2 for i in range(1, len(paras))]
    total = round(tl.length + 1.9, 2)
    durs = [round(b - a, 2) for a, b in zip(starts, starts[1:] + [total])]
    S0 = starts
    f = lambda phrase, sc, lead=0.1: round(tl.find(phrase, S0[sc]) - S0[sc] - lead, 2)
    CUE.update(d=durs, rented=f("rented", 0, 0.12), pine=f("pineapples", 0), house=f("and one", 0),
               eight=f("eight", 1, 0.12), todays=f("today's", 1), fruit=f("fruit", 2), carib=f("caribbean", 2, 0.3),
               almost=f("almost", 3, 0.3), rot=f("rod|rot", 3, 0.0), cold=f("the cold", 4, 0.3), two=f("two hundred", 4),
               heated=f("heated", 5, 0.4), rotting=f("rotting", 5), handed=f("handed|filing", 6), royal=f("royal", 6, 0.3),
               sat=f("they sat|said", 7, 0.3), went=f("went|toilet", 7), same=f("same", 8, 0.4), giant=f("giant", 9), still=f("still", 9, 0.3),
               dollars=f("two dollars", 10, 0.05), fast=f("fast|fashions", 10, 0.3))
    CUE["cta_off"] = round(tl.find("like", S0[11]) - S0[11] - 1.6 + 0.15, 2)
    print("durations:", durs, round(sum(durs), 2))
    if STILLS:  # check frames: python make_toon.py x scene t1,t2
        for i in ONLY:
            for tt in STILLS:
                img = Image.new("RGBA", (W, H))
                scene(i, TEXT[i])(img, ImageDraw.Draw(img), float(tt))
                img.convert("RGB").save(f"toon_{i}_{tt}.png")
        sys.exit()
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), scene(i, TEXT[i])) for i, dd in enumerate(durs)]
    if ONLY:
        base.SCENES[:] = [s for i, s in enumerate(base.SCENES) if i in ONLY]
    ST = S0
    ev = [("whoosh", s) for s in ST[1:]]
    ev += [("thud", CUE["rented"] + 0.2), ("pop", CUE["pine"]), ("pop", CUE["house"]),
           ("thud", ST[1] + CUE["eight"] + 0.2), ("pop", ST[2] + CUE["fruit"]), ("thud", ST[3] + CUE["rot"] + 0.15),
           ("thud", ST[4] + CUE["two"] + 0.15), ("thud", ST[5] + CUE["rotting"] + 0.15), ("pop", ST[6] + CUE["handed"]),
           ("ding", ST[6] + CUE["handed"] + 0.05), ("pop", ST[8] + 0.2), ("pop", ST[9] + CUE["giant"]), ("pop", ST[9] + 0.2),
           ("thud", ST[10] + CUE["dollars"] + 0.2), ("ding", ST[10] + CUE["dollars"] + 0.25),
           ("click", ST[11] + CUE["cta_off"] + 1.6), ("click", ST[11] + CUE["cta_off"] + 3.6), ("ding", ST[11] + CUE["cta_off"] + 3.65)]
    ev += [("click", ST[1] + CUE["eight"] + 0.35 + i * 0.09 + (i % 3) * 0.03) for i in range(12)]  # coins landing
    ev += [("pop", ST[5] + 0.2 + n * 1.6 + 0.05) for n in range(4)]  # manure tosses
    audio.music("music.wav", total, bpm=96, seed=4)
    audio.sfx("sfx.wav", total, ev)
    base.OUT = "base_toon.mp4"
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_toon.mp4", voice, "music.wav", "sfx.wav", OUTFILE)
    print("wrote", OUTFILE)
