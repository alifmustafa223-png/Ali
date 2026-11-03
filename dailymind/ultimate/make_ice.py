"""YouTube Short #21: "He Sold ICE to India... With No Fridges!" (Skia toon style, vidIQ "Chris" voice, UNEDITED).

Frederic Tudor, the Ice King: mocked in 1806, broke, debtors' prison, sawdust insulation, free ice for
bartenders, 16,000 miles to Calcutta in 1833 with ~100 tons of ice surviving.

Voice: Chris exactly as generated (no pause cutting, no inserted silence) - only a low-cut and a gentle
1.6:1 compressor, so it sounds like a person talking (LESSONS.md 70).
Hair: back hair is drawn behind the body (toon.py) and no pose puts a hand into long hair (LESSONS.md 71).

Usage: python make_ice.py final.mp4 [scene,scene,...] [t1,t2,...]   (run inside dailymind/ultimate)
       stills: STILLS_DIR=dir python make_ice.py x 0,1 0.5,2.0 -> dir/ice_<scene>_<t>.png
"""
import json
import math
import os
import random
import sys

import numpy as np
import skia
from PIL import Image, ImageDraw

OUTFILE = sys.argv[1]
ONLY = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 and sys.argv[2][0].isdigit() else None
STILLS = sys.argv[3].split(",") if len(sys.argv) > 3 else None
sys.argv = [sys.argv[0], "base_ice.mp4"]
sys.path.insert(0, "..")

import audio  # noqa: E402
import make_ketchup  # noqa: E402
import make_salt  # noqa: E402
import make_short as base  # noqa: E402
import ultimate as U  # noqa: E402
from fx import impact  # noqa: E402
from make_honey import slam  # noqa: E402
from make_ketchup import splat, stamp  # noqa: E402
from make_short import FONT_B, F_MID, H, W, font, tag, text_block  # noqa: E402
from style import heading  # noqa: E402
from timing import Timeline  # noqa: E402
from toon import *  # noqa: E402,F401,F403

GOLD, ICE, RED = (255, 200, 60), (150, 225, 255), (235, 60, 60)
make_ketchup.SPLAT_COLOR = (250, 195, 50)
base.HOOK_SKIP = 0.0
base.CRF = 16
CUE = {}
VOICE_DIR = "../ice"
TAIL = 1.75  # seconds after the last word (CTA); keeps the total under 65 s with the unedited voice

TUDOR = dict(skin=(240, 195, 160), hair="neat", hair_col=(95, 60, 35), sideburns=True, coat=(35, 75, 70), vest=(200, 160, 70),
             pants=(200, 180, 140), collar=(245, 245, 240), hat="tophat", nose="long")
TUDOR_KING = dict(TUDOR, hat=None, crown=True, coat=(120, 30, 60))
LOCAL = dict(skin=(160, 105, 70), hair="neat", hair_col=(30, 22, 20), coat=(245, 235, 210), pants=(90, 110, 150), nose="small")
LOCAL2 = dict(skin=(120, 80, 55), hair="kid", hair_col=(25, 18, 15), coat=(240, 190, 80), pants=(70, 60, 55), nose="small")
BARMAN = dict(skin=(240, 195, 165), hair="neat", hair_col=(60, 40, 30), coat=(245, 240, 230), vest=(40, 40, 45), pants=(50, 45, 45),
              mustache=True, nose="long")


def blinking(t, ph=0.0):
    return ((t + ph) % 3.3) < 0.11


def pop_in(t, at, dur=0.35):
    return out_back((t - at) / dur, 2.2) if t > at else 0.0


def mouth_pos(x, y, s):
    return x, y + s * (-262 - 70 + 88 * 0.55)


def head_top(y, s):
    return y + s * (-262 - 70 - 88)


def chest(x, y, s):
    return x, y - 190 * s


# ---------- props ----------

def ice_block(c, x, y, w, h, t, melt=0.0, glow_a=1.0):
    """Translucent ice block standing on (x, y) bottom-centre; melt 0..1 shrinks it and rounds the corners."""
    k = 1 - 0.75 * melt
    w, h = w * (0.4 + 0.6 * k), h * k
    r = 10 + 40 * melt
    rr = rrect(x - w / 2, y - h, x + w / 2, y, r)
    c.drawPath(rr, P(Shader=lin((x - w / 2, y - h), (x + w / 2, y), [C(225, 248, 255, 235), C(150, 215, 245, 220), C(90, 170, 225, 230)])))
    c.drawPath(rr, S(C(70, 130, 180), 4))
    c.save()
    c.clipPath(rr, doAntiAlias=True)
    for k_ in range(3):  # inner cracks / bubbles
        c.drawLine(x - w * 0.3 + k_ * w * 0.25, y - h * 0.8, x - w * 0.1 + k_ * w * 0.2, y - h * 0.45, S(C(255, 255, 255, 90), 3))
    c.drawRect(skia.Rect(x - w / 2 + 8, y - h + 8, x - w / 2 + 22, y - 10), P(C(255, 255, 255, 120)))
    c.restore()
    if glow_a > 0:
        glow(c, x, y - h / 2, max(w, h) * 0.9, (160, 220, 255), int(60 * glow_a))
    s = 0.5 + 0.5 * math.sin(t * 3 + x)
    sparkle(c, x + w * 0.25, y - h * 0.75, 6 + 4 * s, int(200 * s), (230, 250, 255))


def mist(c, x, y, t, w=160, n=5):
    """Cold vapour rolling down off ice."""
    for k in range(n):
        ph = (t * 0.45 + k / n) % 1
        c.drawCircle(x - w / 2 + (k / max(1, n - 1)) * w + math.sin(t + k) * 10, y + ph * 140, 26 + 40 * ph,
                     P(C(225, 245, 255, int(90 * math.sin(math.pi * ph))), MaskFilter=blur(14)))


def puddle(c, x, y, r, t):
    if r <= 2:
        return
    c.drawOval(skia.Rect(x - r, y - r * 0.22, x + r, y + r * 0.22), P(C(140, 200, 240, 150)))
    c.drawOval(skia.Rect(x - r * 0.6, y - r * 0.1, x - r * 0.1, y), P(C(255, 255, 255, 70)))
    for k in range(2):
        ph = (t * 0.7 + k * 0.5) % 1
        c.drawOval(skia.Rect(x - r * ph, y - r * 0.22 * ph, x + r * ph, y + r * 0.22 * ph), S(C(220, 245, 255, int(120 * (1 - ph))), 2))


def drips(c, x, y, t, n=3, ph=0.0):
    for k in range(n):
        u = (t * 1.3 + k / n + ph) % 1
        c.drawCircle(x - 30 + k * 30, y + u * 80, 6, P(C(160, 215, 250, int(230 * (1 - u)))))


def rain(c, t, n=110, seed=4, col=(170, 190, 230)):
    r = random.Random(seed)
    for i in range(n):
        x0, y0, sp = r.uniform(-200, W), r.uniform(0, H), r.uniform(1500, 2300)
        y = (y0 + t * sp) % (H + 200) - 100
        x = x0 + (y / H) * 160
        c.drawLine(x, y, x + 10, y + 46, S(C(*col, 120), 2.5))


def puff(c, x, y, k, col=(200, 200, 205)):
    if not 0 <= k < 1.2:
        return
    for i in range(6):
        a = i / 6 * 2 * math.pi
        r = 30 + 70 * ease(k / 0.8)
        c.drawCircle(x + math.cos(a) * r, y + math.sin(a) * r * 0.6 - 120 * k, 40 + 30 * k,
                     P(C(*col, int(170 * (1 - k / 1.2))), MaskFilter=blur(14)))


def newspaper(c, x, y, s, rot):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    c.drawRect(skia.Rect(-230, -160, 236, 166), P(C(0, 0, 0, 90), MaskFilter=blur(10)))
    blob(c, rrect(-230, -160, 230, 160, 6), (240, 232, 210), 1.02, 0.85)
    f = skia.Font(FB, 34)
    c.drawString("SLIPPERY", -150, -105, f, P(C(40, 35, 30)))
    c.drawString("SPECULATION?", -150, -65, f, P(C(40, 35, 30)))
    c.drawLine(-200, -45, 200, -45, S(C(60, 50, 40), 4))
    blob(c, rrect(-200, -30, -40, 90, 4), (150, 210, 240), 1.1, 0.8)  # little picture of an ice block
    for k in range(7):
        c.drawLine(-20, -25 + k * 18, 200, -25 + k * 18, S(C(120, 110, 95), 4))
    for k in range(3):
        c.drawLine(-200, 105 + k * 18, 200, 105 + k * 18, S(C(120, 110, 95), 4))
    c.restore()


def glass(c, x, y, s, t, fill=0.7):
    """Tall drinking glass (bottom at y)."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = skia.Path()
    body.moveTo(-150, -520)
    body.lineTo(150, -520)
    body.lineTo(120, 0)
    body.lineTo(-120, 0)
    body.close()
    c.drawPath(body, P(C(220, 240, 255, 50)))
    liq = skia.Path()
    top = -520 * fill
    liq.moveTo(-150 + 30 * (1 - fill), top + 6 * math.sin(t * 3))
    liq.quadTo(0, top - 6 * math.sin(t * 3), 150 - 30 * (1 - fill), top + 6 * math.sin(t * 3 + 1))
    liq.lineTo(120, 0)
    liq.lineTo(-120, 0)
    liq.close()
    c.drawPath(liq, P(Shader=lin((0, top), (0, 0), [C(255, 170, 70, 220), C(200, 90, 30, 230)])))
    for k in range(12):  # rising bubbles
        u = (t * 0.6 + k / 12) % 1
        bx = -90 + (k * 37) % 180
        c.drawCircle(bx + 6 * math.sin(t * 4 + k), -20 - u * (-top - 40), 5, S(C(255, 240, 210, int(200 * (1 - u))), 2))
    c.drawPath(body, S(C(230, 245, 255, 200), 6))
    c.drawLine(-125, -480, -100, -40, S(C(255, 255, 255, 120), 10))
    for k in range(9):  # condensation
        dx, dy = -110 + (k * 53) % 220, -470 + (k * 97) % 420
        c.drawCircle(dx, dy + ((t * 8 + k * 5) % 30 if k % 3 == 0 else 0), 5 + k % 3, P(C(240, 250, 255, 170)))
    c.restore()


def ice_cube(c, x, y, r, rot, t):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    p = rrect(-r, -r, r, r, r * 0.25)
    c.drawPath(p, P(Shader=lin((-r, -r), (r, r), [C(240, 252, 255, 230), C(160, 215, 245, 210), C(110, 180, 230, 220)])))
    c.drawPath(p, S(C(90, 150, 200), 3))
    c.drawRect(skia.Rect(-r * 0.7, -r * 0.7, -r * 0.35, r * 0.4), P(C(255, 255, 255, 120)))
    c.restore()


def bars(c, x0, x1, y0, y1, n=7):
    for k in range(n):
        x = x0 + (x1 - x0) * k / (n - 1)
        c.drawRect(skia.Rect(x - 11, y0, x + 11, y1), P(Shader=lin((x - 11, 0), (x + 11, 0), [C(60, 60, 70), C(150, 150, 165), C(50, 50, 60)])))
    for y in (y0 + 30, y1 - 30):
        c.drawRect(skia.Rect(x0 - 20, y - 12, x1 + 20, y + 12), P(C(70, 70, 80)))


# ---------- scenes ----------

def art_hook(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(60, 20, 40), C(200, 90, 60), C(250, 170, 80)], [0, 0.55, 1])))
    glow(c, 540, 1350, 600, (255, 200, 120), 140)
    c.drawCircle(540, 1250, 150, P(Shader=rad(540, 1250, 150, [C(255, 245, 200), C(255, 170, 70)])))
    # distant domes and arches (Calcutta skyline silhouette)
    sky = skia.Path()
    sky.moveTo(0, 1420)
    for x, kind in ((60, "arch"), (220, "dome"), (420, "tower"), (650, "dome"), (860, "arch"), (1000, "dome")):
        if kind == "dome":
            sky.lineTo(x - 90, 1420)
            sky.lineTo(x - 90, 1300)
            sky.cubicTo(x - 90, 1180, x + 90, 1180, x + 90, 1300)
            sky.lineTo(x + 90, 1420)
        elif kind == "tower":
            sky.lineTo(x - 30, 1420)
            sky.lineTo(x - 30, 1150)
            sky.lineTo(x, 1110)
            sky.lineTo(x + 30, 1150)
            sky.lineTo(x + 30, 1420)
        else:
            sky.lineTo(x - 80, 1420)
            sky.lineTo(x - 80, 1330)
            sky.lineTo(x + 80, 1330)
            sky.lineTo(x + 80, 1420)
    sky.lineTo(W, 1420)
    sky.lineTo(W, H)
    sky.lineTo(0, H)
    sky.close()
    c.drawPath(sky, P(C(90, 40, 50)))
    for k in range(6):  # heat shimmer
        y = 1450 + k * 40
        p = skia.Path()
        p.moveTo(0, y)
        for j in range(12):
            p.quadTo(j * 90 + 45, y + 8 * math.sin(t * 4 + j + k), j * 90 + 90, y)
        c.drawPath(p, S(C(255, 220, 160, 40), 3))
    palm(c, 40, 1900, 700, t, 1)
    palm(c, 1060, 1900, 640, t + 1, -1)
    c.drawRect(skia.Rect(0, 1700, W, H), P(Shader=lin((0, 1700), (0, H), [C(150, 90, 50), C(90, 50, 30)])))
    hit = CUE["ice"]
    x, y, s = 540, 1880, 1.55
    pose = dict(hands=[(80, 30), (-80, 30)], eyes="open" if t < hit else "open", brows="smug", mouth="grin" if t > hit else "smile",
                look=(0, -0.3), tilt=3 * math.sin(t * 1.8), blink=blinking(t, 0.4), squash=0.04 * spring(t, hit, 2.6, 4),
                hat_bounce=-14 * spring(t, hit + 0.02, 2.2, 3.5))
    person(c, x, y, s, TUDOR, pose, t)
    for k in range(4):  # sweat (it's hot) - drops fly off the face, away from the hands
        dt = (t + k * 0.55) % 2.2
        if dt < 0.6:
            side = 1 if k % 2 else -1
            hx, hy = x + side * (110 + 220 * dt), head_top(y, s) + 120 - 260 * dt + 900 * dt * dt
            c.drawCircle(hx, hy, 11, P(C(190, 225, 255, 230)))
    # the ice block held at the chest (covers both hands)
    bx, by = chest(x, y, s)
    lift = pop_in(t, hit - 0.05) if t > hit - 0.05 else 0
    sc = 0.8 + 0.2 * lift
    ice_block(c, bx, by + 95, 230 * sc, 190 * sc, t, glow_a=1 + 1.5 * max(0, 1 - (t - hit) / 0.6) if t > hit else 1)
    mist(c, bx, by + 95, t, 180)
    drips(c, bx, by + 100, t)
    burst(c, t, hit, bx, by, n=14, reach=300)


def art_boston(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, 1400), [C(30, 40, 80), C(120, 130, 170), C(240, 200, 160)], [0, 0.6, 1])))
    c.drawCircle(820, 1180, 80, P(C(255, 235, 190)))
    glow(c, 820, 1180, 300, (255, 220, 160), 90)
    c.drawRect(skia.Rect(0, 1330, W, H), P(Shader=lin((0, 1330), (0, H), [C(90, 120, 160), C(30, 45, 70)])))
    for k in range(18):
        x = (k * 67 + t * 30) % W
        c.drawLine(x, 1360 + (k % 5) * 50, x + 40, 1360 + (k % 5) * 50, S(C(220, 230, 250, 90), 3))
    car = CUE["carib"]
    sail = ease((t - car - 0.3) / 2.0)
    ship(c, 780 + 380 * sail, 1420, 0.85, t)
    # crane lowering ice blocks onto the ship
    c.drawLine(560, 1640, 560, 980, S(C(90, 60, 40), 22))
    c.drawLine(560, 990, 800 + 380 * sail * 0, 990, S(C(90, 60, 40), 16))
    if sail < 0.05:
        drop = (t % 2.0) / 2.0
        ly = 1000 + 260 * ease(drop)
        c.drawLine(780, 990, 780, ly, S(C(50, 40, 30), 4))
        ice_block(c, 780, ly + 110, 120, 105, t, glow_a=0.6)
    c.drawRect(skia.Rect(0, 1600, 640, H), P(Shader=lin((0, 1600), (0, H), [C(130, 90, 55), C(80, 55, 35)])))
    for k in range(8):
        c.drawLine(k * 85, 1600, k * 85, H, S(C(90, 60, 35), 4))
    for k, (bx, bh) in enumerate(((90, 110), (200, 110), (145, 95))):  # stacked blocks on the dock
        ice_block(c, bx, 1640 - (k // 2) * 110, 110, bh, t, glow_a=0.5)
    point = ease((t - CUE["ship"]) / 0.4)
    pose = dict(hands=[(-30, 150), (40 + 120 * point, 60 - 160 * point)], eyes="open", brows="up", mouth="grin" if point > 0.5 else "smile",
                look=(1, -0.2), tilt=3 * math.sin(t * 2), blink=blinking(t, 0.8))
    person(c, 350, 1880, 1.4, TUDOR, pose, t)


def art_laugh(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(30, 30, 45), C(70, 60, 70), C(40, 35, 40)])))
    for k in range(5):  # Boston brick fronts
        x0 = k * 230 - 40
        c.drawRect(skia.Rect(x0, 1000 + (k % 2) * 60, x0 + 220, 1650), P(C(110 - k * 6, 55, 48)))
        for j in range(3):
            c.drawRect(skia.Rect(x0 + 40 + j * 55, 1100 + (k % 2) * 60, x0 + 80 + j * 55, 1180 + (k % 2) * 60), P(C(255, 210, 130, 160)))
    c.drawRect(skia.Rect(0, 1650, W, H), P(Shader=lin((0, 1650), (0, H), [C(90, 85, 85), C(50, 45, 45)])))
    for i, (x, lk) in enumerate([(150, 0), (380, 1), (700, 3), (930, 2)]):
        bounce = abs(math.sin(t * 7 + i)) * 14
        pose = dict(hands=[(30, 90), (-30, 90)], eyes="closed", mouth="laugh", brows="up", tilt=7 * math.sin(t * 7 + i), look=(0, 0))
        if i == 1:  # one points at the newspaper
            pose["hands"] = [(30, 90), (130, -20)]
        person(c, x, 1870 - bounce, 1.0, crowd_look(lk), pose, t)
        for j in range(2):  # little "HA" puffs
            u = ((t * 0.9 + i * 0.3 + j * 0.5) % 1)
            hx = x + (i - 1.5) * 10 + 60 * (1 if i % 2 else -1) * u
            hy = head_top(1870, 1.0) - 40 - 140 * u
            c.drawString("HA", hx - 28, hy, skia.Font(FB, 38), P(C(255, 230, 150, int(230 * math.sin(math.pi * u)))))
    news = CUE["news"]
    k = ease((t - news + 0.2) / 0.6)
    if k > 0:
        newspaper(c, 540, 1180 - 400 * (1 - k), 0.6 + 0.6 * k, -720 * (1 - k) - 4)


def art_melt(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, 1260), [C(40, 60, 120), C(90, 160, 200), C(250, 200, 140)], [0, 0.6, 1])))
    c.drawCircle(860, 1100, 110, P(Shader=rad(860, 1100, 110, [C(255, 250, 220), C(255, 200, 90)])))
    glow(c, 860, 1100, 380, (255, 220, 140), 120)
    c.drawRect(skia.Rect(0, 1250, W, 1480), P(Shader=lin((0, 1250), (0, 1480), [C(70, 170, 200), C(40, 110, 160)])))
    c.drawRect(skia.Rect(0, 1470, W, H), P(Shader=lin((0, 1470), (0, H), [C(240, 210, 150), C(200, 160, 100)])))
    palm(c, 30, 1700, 720, t, 1)
    palm(c, 1060, 1640, 600, t + 1, -1)
    for k in range(5):  # heat waves
        y = 1300 + k * 50
        p = skia.Path()
        p.moveTo(0, y)
        for j in range(12):
            p.quadTo(j * 90 + 45, y + 7 * math.sin(t * 4 + j + k), j * 90 + 90, y)
        c.drawPath(p, S(C(255, 240, 200, 35), 3))
    melted = CUE["melted"]
    m = ease((t - 0.2) / max(0.5, melted + 0.4))
    for k, cx in enumerate((300, 780)):  # leaking crates
        crate(c, cx, 1700, 240, 170)
        drips(c, cx, 1700, t, 3, k * 0.3)
        puddle(c, cx, 1720, 60 + 120 * m, t)
    # the big block melting in the middle
    puddle(c, 540, 1800, 90 + 200 * m, t)
    ice_block(c, 540, 1790, 260, 220, t, melt=0.15 + 0.8 * m, glow_a=0.6)
    for k in range(3):
        ph = (t * 0.8 + k / 3) % 1
        c.drawCircle(500 + k * 40, 1640 - ph * 200, 18 + 26 * ph, P(C(255, 255, 255, int(110 * (1 - ph))), MaskFilter=blur(10)))
    nob = CUE["nobody"]
    puzzled = t > nob
    for i, (x, lk, ph) in enumerate(((190, LOCAL, 0.2), (890, LOCAL2, 1.1))):
        pose = dict(hands=[(-20, 150), (20, 150)] if not puzzled else [(70, 60), (-70, 60)], eyes="wide" if puzzled else "open",
                    brows="up", mouth="O" if puzzled else "smile", look=(1 if x < 540 else -1, 0.5), tilt=(8 if puzzled else 2) * math.sin(t * 2 + i),
                    blink=blinking(t, ph))
        person(c, x, 1880, 1.15, lk, pose, t)
        if puzzled:  # shrinking ice cube held at the chest
            cx, cy = chest(x, 1880, 1.15)
            r = max(6, 34 * (1 - ease((t - nob) / 1.5) * 0.8))
            ice_cube(c, cx, cy + 40, r, 10 * math.sin(t * 3), t)
            drips(c, cx, cy + 50, t, 2, i * 0.4)
            q = pop_in(t, nob + 0.2)
            if q > 0:
                c.drawString("?", x - 18, head_top(1880, 1.15) - 30, skia.Font(FB, 90 * q), P(C(255, 255, 255)))


def art_prison(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(20, 22, 30), C(45, 45, 55), C(20, 20, 26)])))
    for row in range(14):  # stone wall
        y = 900 + row * 75
        for j in range(8):
            x = j * 150 + (75 if row % 2 else 0) - 40
            c.drawRoundRect(skia.Rect(x + 4, y + 4, x + 146, y + 71), 14, 14, P(C(70 + (j * 7 + row * 3) % 18, 68, 75)))
    # barred window with moonlight
    c.drawRect(skia.Rect(640, 960, 900, 1180), P(C(30, 40, 80)))
    c.drawCircle(820, 1030, 34, P(C(240, 240, 220)))
    bars(c, 650, 890, 960, 1180, 5)
    beam = skia.Path()
    beam.moveTo(640, 960)
    beam.lineTo(900, 960)
    beam.lineTo(560, 1900)
    beam.lineTo(120, 1900)
    beam.close()
    c.drawPath(beam, P(C(200, 210, 255, 30), MaskFilter=blur(20)))
    c.drawRect(skia.Rect(0, 1700, W, H), P(C(35, 35, 42)))
    lost, prison = CUE["lost"], CUE["prison"]
    slump = ease((t - lost) / 0.8)
    pose = dict(hands=[(40, 120), (-40, 120)], eyes="sad", brows="sad", mouth="frown", look=(0, 0.7), tilt=-5 * slump + 1.5 * math.sin(t * 1.4),
                blink=blinking(t, 0.7), hat_bounce=-10 * slump)
    person(c, 400, 1860, 1.5, TUDOR, pose, t)
    for side in (-1, 1):  # empty pockets
        px, py = 400 + side * 70 * 1.5, 1860 - 120 * 1.5
        p = skia.Path()
        p.moveTo(px - 24, py)
        p.lineTo(px + 24, py)
        p.lineTo(px + 16 * side, py + 44 + 5 * math.sin(t * 3 + side))
        p.close()
        blob(c, p, (235, 230, 220), 1.05, 0.8)
    # the cell door slams shut on "debtors' prison"
    close = ease((t - prison + 0.05) / 0.25)
    off = 700 * (1 - close)
    bars(c, 60 + off, 1020 + off, 1150, 1920, 9)
    if t > prison:
        k = t - prison
        for j in range(8):
            a = j / 8 * 2 * math.pi
            r = 40 + 200 * ease(k / 0.4)
            c.drawCircle(540 + math.cos(a) * r, 1500 + math.sin(a) * r * 0.4, 8 * max(0, 1 - k / 0.5), P(C(255, 240, 200)))


def art_sawdust(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(40, 28, 20), C(95, 65, 40), C(45, 30, 20)])))
    for k in range(12):  # barn planks
        c.drawLine(k * 95, 900, k * 95, 1650, S(C(60, 40, 25), 6))
    c.drawLine(0, 960, W, 900, S(C(70, 48, 30), 30))
    c.drawRect(skia.Rect(0, 1650, W, H), P(Shader=lin((0, 1650), (0, H), [C(150, 110, 60), C(100, 70, 40)])))
    lamp = 0.8 + 0.2 * flicker(t, 2)
    glow(c, 900, 1050, 420, (255, 190, 110), int(140 * lamp))
    saw = CUE["saw"]
    # left: bare block melting fast; right: block buried in sawdust stays solid
    m = ease(t / 4.0)
    puddle(c, 230, 1760, 60 + 140 * m, t)
    ice_block(c, 230, 1750, 200, 180, t, melt=0.1 + 0.75 * m, glow_a=0.5)
    drips(c, 230, 1755, t)
    ice_block(c, 820, 1750, 200, 180, t, glow_a=0.5)
    cover = ease((t - saw + 0.3) / 1.2)
    pile = skia.Path()
    ph = 60 + 170 * cover
    pile.moveTo(680, 1755)
    pile.cubicTo(700, 1755 - ph, 940, 1755 - ph, 960, 1755)
    pile.close()
    c.drawPath(pile, P(Shader=lin((0, 1755 - ph), (0, 1755), [C(225, 185, 120), C(180, 135, 80)])))
    for k in range(24):
        c.drawCircle(700 + (k * 37) % 240, 1750 - (k * 23) % int(max(10, ph * 0.8)), 4, P(C(150, 110, 60)))
    # Tudor shovelling sawdust (shovel in his right hand, swinging toward the pile)
    sc_ = math.sin(2 * math.pi * t / 1.3)
    pose = dict(hands=[(40, 90), (110 + 20 * sc_, 30 - 40 * sc_)], eyes="open", brows="angry", mouth="grin", look=(1, 0.4), tilt=4 * sc_, lean=3,
                blink=blinking(t, 0.2))
    x, y, s = 520, 1840, 1.4
    person(c, x, y, s, TUDOR, pose, t)
    hx, hy = hand_pos(x, y, s, pose, 1)
    bx, by = hx + 120, hy + 150 + 40 * sc_
    c.drawLine(hx, hy, bx, by, S(OUT, 22))
    c.drawLine(hx, hy, bx, by, S(C(150, 100, 55), 14))
    blade = skia.Path()
    blade.moveTo(bx - 40, by - 10)
    blade.lineTo(bx + 60, by - 30)
    blade.lineTo(bx + 75, by + 40)
    blade.lineTo(bx - 25, by + 55)
    blade.close()
    blob(c, blade, (150, 150, 160))
    for n in range(4):  # sawdust tossed onto the pile
        t0 = 0.3 + n * 1.3
        dt = t - t0
        if 0 < dt < 0.7:
            for j in range(10):
                px = bx + 20 + (60 + 25 * j) * dt * 3
                py = by - 40 - 500 * dt + 1100 * dt * dt + (j % 3) * 8
                c.drawCircle(px, py, 6, P(C(220, 180, 110)))


def art_bar(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(35, 22, 18), C(80, 50, 30), C(35, 22, 18)])))
    for row in range(3):  # bottle shelves
        y = 1000 + row * 150
        c.drawRect(skia.Rect(0, y, W, y + 14), P(C(110, 70, 40)))
        for k in range(9):
            x = 40 + k * 120
            col = [(60, 120, 70), (140, 60, 50), (180, 140, 60), (70, 80, 130)][(k + row) % 4]
            blob(c, rrect(x, y - 100, x + 40, y, 12), col, 1.5, 0.6)
            c.drawRect(skia.Rect(x + 12, y - 125, x + 28, y - 95), P(C(*col)))
    glow(c, 540, 1000, 500, (255, 190, 110), int(120 * flicker(t, 1)))
    free, every = CUE["free"], CUE["every"]
    shake = math.sin(t * 22) * (1 if t > free + 0.5 else 0)
    bp = dict(hands=[(-130, -50 + 20 * shake), (40, 60)], eyes="open", brows="up", mouth="grin", look=(-1, 0), tilt=3 * shake,
              blink=blinking(t, 0.5))
    person(c, 760, 1700, 1.25, BARMAN, bp, t)
    sx, sy = hand_pos(760, 1700, 1.25, bp, -1)
    blob(c, rrect(sx - 30, sy - 90, sx + 30, sy + 20, 14), (200, 200, 210), 1.5, 0.7)  # cocktail shaker
    blob(c, rrect(0, 1560, W, 1660, 10), (120, 75, 40))  # counter
    c.drawRect(skia.Rect(0, 1660, W, H), P(C(80, 50, 28)))
    # Tudor tipping a bucket of free ice
    tip = ease((t - free + 0.2) / 0.5)
    tp = dict(hands=[(90, 110 - 30 * tip), (10, 130 - 30 * tip)], eyes="open", brows="smug", mouth="grin", look=(1, 0.3), tilt=2 * math.sin(t * 2),
              blink=blinking(t, 1.1))
    person(c, 260, 1880, 1.3, TUDOR, tp, t)
    hx, hy = hand_pos(260, 1880, 1.3, tp, -1)
    c.save()
    c.translate(hx + 75, hy + 20)
    c.rotate(-60 * tip)
    bucket = skia.Path()
    bucket.moveTo(-60, -60)
    bucket.lineTo(60, -60)
    bucket.lineTo(45, 50)
    bucket.lineTo(-45, 50)
    bucket.close()
    blob(c, bucket, (150, 150, 165), 1.4, 0.7)
    c.drawArc(skia.Rect(-60, -110, 60, -10), 180, 180, False, S(C(80, 80, 90), 5))
    for k in range(4):
        ice_cube(c, -35 + k * 23, -68, 16, k * 20, t)
    c.restore()
    for k in range(8):  # cubes tumble into glasses on the counter
        at = free + 0.3 + k * 0.15
        dt = t - at
        if dt <= 0:
            continue
        u = min(1, dt / 0.5)
        x = hx + 75 + (430 + (k % 4) * 70 - hx - 75) * u
        y = hy - 20 - 160 * math.sin(math.pi * u) + (1480 - hy + 20) * u
        ice_cube(c, x, y, 14, 360 * u * (1 if k % 2 else -1), t)
    for k in range(4):  # glasses
        gx = 430 + k * 70
        c.drawPath(rrect(gx - 26, 1470, gx + 26, 1565, 8), P(C(220, 240, 255, 70)))
        c.drawPath(rrect(gx - 26, 1500, gx + 26, 1565, 8), P(C(230, 140, 60, 200)))
        c.drawPath(rrect(gx - 26, 1470, gx + 26, 1565, 8), S(C(230, 245, 255, 200), 3))
    if t > every:  # customers cheer, frosty glasses raised
        for i, (x, lk) in enumerate([(560, 0), (980, 4)]):
            up = ease((t - every - i * 0.1) / 0.4)
            pose = dict(hands=[(-20, 150), (40, 60 - 260 * up)], eyes="closed", mouth="laugh", brows="up", tilt=5 * math.sin(t * 5 + i))
            person(c, x, 1930, 0.85, crowd_look(lk), pose, t)
            gx, gy = hand_pos(x, 1930, 0.85, pose, 1)
            c.drawPath(rrect(gx - 20, gy - 70, gx + 20, gy, 6), P(C(230, 150, 70, 220)))
            c.drawPath(rrect(gx - 20, gy - 70, gx + 20, gy, 6), S(C(230, 245, 255), 3))
            sparkle(c, gx + 18, gy - 60, 7, 220, (230, 250, 255))


def art_voyage(c, t):
    D = CUE["d"][7]
    # day/night racing by: 4 cycles = four months at sea
    cyc = t / D * 4
    ph = cyc % 1
    day = 0.5 - 0.5 * math.cos(2 * math.pi * ph)
    top = (int(20 + 60 * day), int(25 + 100 * day), int(60 + 140 * day))
    bot = (int(40 + 200 * day), int(50 + 150 * day), int(90 + 110 * day))
    c.drawPaint(P(Shader=lin((0, 0), (0, 1400), [C(*top), C(*bot)])))
    a = math.pi * ph * 2 - math.pi / 2
    sx, sy = 540 + math.cos(a + math.pi) * 520, 1350 + math.sin(a + math.pi) * 420
    mx, my = 540 + math.cos(a) * 520, 1350 + math.sin(a) * 420
    if sy < 1400:
        c.drawCircle(sx, sy, 70, P(C(255, 230, 150)))
        glow(c, sx, sy, 260, (255, 210, 130), 110)
    if my < 1400:
        c.drawCircle(mx, my, 50, P(C(235, 235, 225)))
    r = random.Random(2)
    for i in range(40):
        x, y = r.uniform(0, W), r.uniform(100, 1100)
        c.drawCircle(x, y, 2.2, P(C(255, 255, 240, int(200 * (1 - day)))))
    # big rolling waves
    for k, (yb, col, amp, sp) in enumerate(((1380, (40, 80, 130), 30, 1.0), (1500, (30, 65, 110), 45, 1.3), (1660, (20, 50, 90), 60, 1.6))):
        p = skia.Path()
        p.moveTo(0, H)
        for j in range(25):
            x = j * 45
            p.lineTo(x, yb + amp * math.sin(x / 140 + t * sp + k))
        p.lineTo(W, H)
        p.close()
        cc = tuple(int(v * (0.6 + 0.4 * day)) for v in col)
        c.drawPath(p, P(C(*cc)))
        if k == 1:
            bob = 1500 + 45 * math.sin(540 / 140 + t * 1.3 + 1)
            c.save()
            c.translate(540, bob - 40)
            c.rotate(6 * math.cos(540 / 140 + t * 1.3 + 1))
            ship(c, 0, 0, 1.0, t)
            c.restore()
            for j in range(4):  # ice crates on deck glow
                glow(c, 470 + j * 45, bob - 70, 50, (160, 220, 255), 80)
    for j in range(10):  # spray
        u = (t * 1.2 + j / 10) % 1
        c.drawCircle(300 + j * 50, 1480 - 120 * math.sin(math.pi * u), 6, P(C(230, 245, 255, int(200 * (1 - u)))))


def art_arrive(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, 1400), [C(40, 30, 70), C(200, 110, 90), C(255, 190, 110)], [0, 0.55, 1])))
    glow(c, 540, 1200, 600, (255, 200, 130), 120)
    for x in (120, 360, 720, 960):  # domes on the waterfront
        c.drawRect(skia.Rect(x - 90, 1140, x + 90, 1400), P(C(220, 190, 160)))
        dome = skia.Path()
        dome.moveTo(x - 90, 1145)
        dome.cubicTo(x - 90, 1020, x + 90, 1020, x + 90, 1145)
        dome.close()
        c.drawPath(dome, P(C(235, 205, 170)))
        for j in range(3):
            c.drawRoundRect(skia.Rect(x - 70 + j * 50, 1220, x - 40 + j * 50, 1320), 15, 15, P(C(120, 80, 70)))
    c.drawRect(skia.Rect(0, 1400, W, 1560), P(Shader=lin((0, 1400), (0, 1560), [C(90, 120, 150), C(50, 70, 100)])))
    c.drawRect(skia.Rect(0, 1560, W, H), P(Shader=lin((0, 1560), (0, H), [C(140, 100, 60), C(90, 60, 35)])))
    hund = CUE["hundred"]
    opened = ease((t - hund + 0.15) / 0.35)
    # crowd waiting, then cheering
    cheer = t > hund
    for i, (x, lk) in enumerate([(110, LOCAL), (300, crowd_look(1)), (800, LOCAL2), (980, crowd_look(3))]):
        up = ease((t - hund - 0.1 - i * 0.07) / 0.35)
        pose = dict(hands=[(-30, 150 - 270 * up), (30, 150 - 270 * up)], eyes="closed" if up > 0.6 else "open",
                    mouth="laugh" if cheer else "O", brows="up", look=(1 if x < 540 else -1, 0.4),
                    tilt=(6 * math.sin(t * 6 + i) if cheer else 2 * math.sin(t * 2 + i)), blink=blinking(t, i))
        person(c, x, 1900 - (abs(math.sin(t * 6 + i)) * 14 if cheer else 0), 0.95, lk, pose, t)
    # the crate: lid pops off, ice glows and steams cold
    cx, cy = 540, 1800
    crate(c, cx, cy, 300, 200)
    if opened > 0:
        for k in range(3):
            ice_block(c, cx - 90 + k * 90, cy - 150, 90, 90 + 30 * opened, t, glow_a=0.6)
        mist(c, cx, cy - 250, t, 260, 6)
        glow(c, cx, cy - 240, 260, (170, 225, 255), int(70 * opened))
    lid_y = cy - 205 - 380 * opened + 600 * max(0, opened - 0.6) ** 2
    c.save()
    c.translate(cx + 260 * opened, lid_y)
    c.rotate(140 * opened)
    blob(c, rrect(-160, -18, 160, 18, 4), (160, 110, 60))
    c.restore()
    if t < hund:  # "water?" sloshing sound bubble before the reveal
        u = (t * 1.5) % 1
        c.drawCircle(cx + 40, cy - 260 - 60 * u, 14, S(C(190, 225, 255, int(220 * (1 - u))), 3))
    burst(c, t, hund, cx, cy - 260, n=14, reach=340)


def art_king(c, t):
    U.T_EIGHT = CUE["king"] - 0.6
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(15, 25, 50), C(50, 90, 140), C(180, 220, 250)], [0, 0.6, 1])))
    glow(c, 540, 1300, 650, (200, 235, 255), 140)
    for x, y, w, h in ((540, 1880, 760, 180), (540, 1700, 560, 170), (300, 1530, 150, 360), (780, 1530, 150, 360)):
        ice_block(c, x, y, w, h, t, glow_a=0.8)
    for x, y, r, face, speed in U.coins_at(t):  # coins rain BEHIND him
        U.draw_coin(c, x, y, r, face, speed)
    proud = ease((t - CUE["king"]) / 0.4)
    pose = dict(hands=[(-90, -60 * proud + 40), (90, -60 * proud + 40)], eyes="open", brows="smug", mouth="grin", look=(0, -0.2),
                tilt=3 * math.sin(t * 2), squash=0.04 * spring(t, CUE["king"], 2.6, 4), blink=blinking(t, 0.6))
    person(c, 540, 1540, 1.3, TUDOR_KING, pose, t)
    for k in range(6):
        a = t * 1.3 + k * 1.05
        sparkle(c, 540 + math.cos(a) * 300, 1250 + math.sin(a) * 200, 9, 210, (230, 250, 255))


def art_drink(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(15, 15, 25), C(45, 35, 40), C(20, 15, 18)])))
    glow(c, 540, 1350, 600, (255, 170, 90), 90)
    c.drawRect(skia.Rect(0, 1760, W, H), P(Shader=lin((0, 1760), (0, H), [C(90, 60, 40), C(50, 32, 20)])))
    gx, gy, gs = 540, 1800, 1.05
    glass(c, gx, gy, gs, t)
    drink = CUE["drink"]
    for k in range(3):  # cubes drop in, splash, bob
        at = 0.25 + k * 0.45
        dt = t - at
        if dt < 0:
            continue
        surface = gy - 520 * 0.7 * gs
        if dt < 0.35:
            y = 700 + (surface - 700) * (dt / 0.35) ** 2
        else:
            y = surface + 20 + 12 * math.sin((dt - 0.35) * 6) * math.exp(-(dt - 0.35) * 2)
        x = gx - 70 + k * 70
        ice_cube(c, x, y, 52, 15 * math.sin(t * 2 + k) + k * 20, t)
        if 0.35 < dt < 0.9:  # splash droplets
            u = (dt - 0.35) / 0.55
            for j in range(6):
                a = math.pi * (1.1 + 0.8 * j / 5)
                c.drawCircle(x + math.cos(a) * 160 * u, surface - math.sin(a) * -1 * 0 - 260 * u + 500 * u * u, 8 * (1 - u) + 2,
                             P(C(255, 200, 120, int(230 * (1 - u)))))
    c.drawLine(gx + 60, gy - 700 * gs, gx + 20, gy - 200 * gs, S(C(240, 80, 90), 18))  # straw
    if t > drink:
        for k in range(6):
            a = t * 1.5 + k * 1.05
            sparkle(c, gx + math.cos(a) * 260, 1400 + math.sin(a) * 220, 8, 200, (230, 250, 255))


def cube_mascot(c, t, sub):
    """CTA mascot: a cool ice cube with sunglasses that slowly melts until 'subscribe' refreezes it."""
    c.drawOval(skia.Rect(-170, -20, 170, 20), P(C(0, 0, 0, 120), MaskFilter=blur(14)))
    sq = 0.03 * math.sin(t * 2.4)
    c.save()
    c.scale(1 + sq, 1 - sq)
    p = rrect(-170, -360, 170, 0, 60)
    c.drawPath(p, P(Shader=lin((-170, -360), (170, 0), [C(235, 250, 255), C(160, 215, 245), C(100, 170, 225)])))
    c.drawPath(p, S(C(70, 130, 180), 8))
    c.drawRect(skia.Rect(-130, -320, -95, -60), P(C(255, 255, 255, 110)))
    for side in (-1, 1):
        r = skia.RRect.MakeRectXY(skia.Rect(side * 70 - 62, -260, side * 70 + 62, -170), 30, 30)
        c.drawRRect(r, P(Shader=lin((0, -260), (0, -170), [C(70, 70, 90), C(8, 8, 14)])))
        c.drawRRect(r, S(C(10, 10, 10), 8))
        g = ((t * 0.7) % 1.5) / 0.4
        if 0 < g < 1:
            c.save()
            c.clipRRect(r, doAntiAlias=True)
            gx = side * 70 - 100 + g * 200
            gp = skia.Path()
            gp.moveTo(gx, -270)
            gp.lineTo(gx + 34, -270)
            gp.lineTo(gx - 12, -160)
            gp.lineTo(gx - 46, -160)
            gp.close()
            c.drawPath(gp, P(C(255, 255, 255, 170)))
            c.restore()
    c.drawLine(-8, -225, 8, -225, S(C(10, 10, 10), 14))
    c.drawArc(skia.Rect(-50, -150, 50, -90), 20, 140, False, S(C(40, 90, 140), 9))
    c.restore()
    if not sub:
        drips(c, -120, -10, t, 2)
        drips(c, 110, -10, t, 2, 0.5)
    else:
        for k in range(6):
            a = t * 2 + k * 1.05
            sparkle(c, math.cos(a) * 230, -180 + math.sin(a) * 200, 8, 220, (230, 250, 255))


def art_cta(c, t):
    U.T_EIGHT = -10
    U.background(c, t, 0)
    U.spotlight(c, t, 0)
    U.pedestal(c, t)
    c.save()
    c.translate(540, 1415)
    cube_mascot(c, t, t > CUE["cta_off"] + 3.6)
    c.restore()
    c.drawPaint(P(C(10, 6, 14, 150)))


ART = [art_hook, art_boston, art_laugh, art_melt, art_prison, art_sawdust, art_bar, art_voyage, art_arrive, art_king, art_drink, art_cta]
PUSH = [(1.0, 1.06), (1.0, 1.06), (1.0, 1.06), (1.0, 1.07), (1.06, 1.0), (1.0, 1.06), (1.0, 1.05), (1.0, 1.08), (1.0, 1.06), (1.0, 1.07), (1.0, 1.08), (1.0, 1.0)]
ANCHOR = [(540, 1400), (540, 1500), (540, 1500), (540, 1600), (400, 1500), (540, 1600), (540, 1500), (540, 1500), (540, 1600), (540, 1500), (540, 1500), (540, 1300)]


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


# ---------- text layer ----------

def title(img, t, text, sub=None, sub_at=1.0, y=400, sub_color=(255, 235, 210)):
    heading(img, t, text, sub, sub_at, F_MID, y, sub_color=sub_color)


def scene(i, text_fn):
    def fn(img, d, t):
        img.paste(render_art(i, t, CUE["d"][i]))
        text_fn(img, t)
    return fn


def line(img, text, y, f):
    dd = ImageDraw.Draw(img, "RGBA")
    tw = dd.textlength(text, font=f)
    dd.text(((W - tw) / 2 + 4, y + 5), text, font=f, fill=(0, 0, 0, 140))
    dd.text(((W - tw) / 2, y), text, font=f, fill=(255, 255, 255))


def tx_hook(img, t):
    line(img, "This man got rich", 230, F_MID)
    line(img, "selling", 330, F_MID)
    slam(img, "ICE", 430, t, CUE["ice"] - 0.1, ICE, 190)
    text_block(img, "...in INDIA! 200 years ago,", font(FONT_B, 58), 680, t, (255, 255, 255), CUE["india"])
    text_block(img, "with NO fridges!", font(FONT_B, 58), 752, t, GOLD, CUE["fridge"])
    impact(img, t, CUE["ice"] + 0.1, 18)


def tx_boston(img, t):
    tag(img, "BOSTON, 1806", t, (60, 90, 150))
    title(img, t, "Meet Frederic Tudor", "He shipped ICE to the Caribbean!", CUE["carib"], sub_color=ICE)


def tx_laugh(img, t):
    title(img, t, "Everyone laughed!", "\"A slippery speculation\"", CUE["slip"], sub_color=GOLD)


def tx_melt(img, t):
    title(img, t, "It was.", "Nobody knew what to do with it!", CUE["nobody"])
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "MELTED", t, CUE["melted"], col=ICE, size=110)
    impact(img, t, CUE["melted"] + 0.15, 12)


def tx_prison(img, t):
    title(img, t, "He lost everything...")
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "PRISON", t, CUE["prison"], col=RED, size=110)
    impact(img, t, CUE["prison"] + 0.15, 14)


def tx_sawdust(img, t):
    title(img, t, "But he didn't quit!", "He packed it in SAWDUST", CUE["saw"], sub_color=GOLD)


def tx_bar(img, t):
    title(img, t, "Then he gave ice away", "Everyone wanted cold drinks!", CUE["every"], sub_color=ICE)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "FREE!", t, CUE["free"], col=GOLD, size=110)
    impact(img, t, CUE["free"] + 0.15, 10)


def tx_voyage(img, t):
    tag(img, "1833", t, (60, 90, 150))
    title(img, t, "16,000 miles to India", "Four months at sea...", CUE["months"], sub_color=ICE)


def tx_arrive(img, t):
    title(img, t, "Everyone expected water...")
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "100 TONS!", t, CUE["hundred"], col=ICE, size=110)
    impact(img, t, CUE["hundred"] + 0.15, 14)


def tx_king(img, t):
    title(img, t, "He became known as", y=260)
    slam(img, "THE ICE KING", 420, t, CUE["king"] - 0.1, GOLD, 120)
    impact(img, t, CUE["king"] + 0.1, 16)


def tx_drink(img, t):
    title(img, t, "Next time you get ice...", "...thank the man everyone laughed at!", CUE["thank"], sub_color=GOLD)


def tx_cta(img, t):
    text_block(img, "Learned something new?", font(FONT_B, 68), 330, t, delay=0.0)
    make_salt.draw_cta(img, ImageDraw.Draw(img, "RGBA"), W / 2, 1250, t, off=CUE["cta_off"])


TEXT = [tx_hook, tx_boston, tx_laugh, tx_melt, tx_prison, tx_sawdust, tx_bar, tx_voyage, tx_arrive, tx_king, tx_drink, tx_cta]
base.TRANSITION = splat

if __name__ == "__main__":
    voice = f"{VOICE_DIR}/voice.mp3"
    tl = Timeline(voice)
    firsts = ["his name", "people laughed", "the|it ones|was", "to|tudor her|lost", "but he", "than|then a|he game|gave", "in eighteen",
              "people expect", "to|tudor her|became", "so next", "learn"]
    after, starts = 0.3, [0.0]
    for ph in firsts:
        w = tl.find(ph, after)
        before = [p for p in tl.pauses if p[1] <= w + 0.2 and p[0] >= after - 0.3]
        cut = max((before[-1][0] + before[-1][1]) / 2, before[-1][1] - 0.25) if before else w - 0.15
        starts.append(round(cut, 3))
        after = w + 0.3
    total = round(tl.length + TAIL, 2)
    durs = [round(b - a, 2) for a, b in zip(starts, starts[1:] + [total])]
    S0 = starts
    f = lambda phrase, sc, lead=0.1: round(tl.find(phrase, S0[sc]) - S0[sc] - lead, 2)
    CUE.update(d=durs, S=S0,
               ice=f("ice", 0, 0.0), india=f("india", 0), fridge=f("fridge|fridges", 0),
               ship=f("fellowship|ship", 1), carib=f("caribbean", 1),
               news=f("newspaper", 2), slip=f("slippery", 2),
               melted=f("melted", 3, 0.15), nobody=f("nobody", 3),
               lost=f("lost", 4), prison=f("debtors|prison", 4, 0.15),
               saw=f("solid|sawdust", 5),
               free=f("free", 6, 0.15), every=f("everyone", 6),
               months=f("months", 7),
               hundred=f("hundred", 8, 0.15),
               king=f("ice king", 9, 0.0),
               drink=f("drink", 10), thank=f("think|thank", 10))
    CUE["cta_off"] = round(tl.find("like", S0[11]) - S0[11] - 1.6 + 0.15, 2)
    print("starts:", S0)
    print("durations:", durs, round(sum(durs), 2))
    print("cues:", {k: v for k, v in CUE.items() if k not in ("d", "S")})
    json.dump({"starts": S0, "durs": durs, "cues": {k: v for k, v in CUE.items() if k not in ("d", "S")}}, open(f"{VOICE_DIR}/plan.json", "w"), indent=1)
    if STILLS:
        out = os.environ.get("STILLS_DIR", VOICE_DIR + "/stills")
        os.makedirs(out, exist_ok=True)
        for i in ONLY:
            for tt in STILLS:
                img = Image.new("RGBA", (W, H))
                scene(i, TEXT[i])(img, ImageDraw.Draw(img), float(tt))
                img.convert("RGB").save(f"{out}/ice_{i}_{tt}.png")
        sys.exit()
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), scene(i, TEXT[i])) for i, dd in enumerate(durs)]
    if ONLY:
        base.SCENES[:] = [s for i, s in enumerate(base.SCENES) if i in ONLY]
    ST, C_ = S0, CUE
    ev = [("whoosh", s) for s in ST[1:]]
    ev += [("thud", C_["ice"]), ("ding", C_["ice"] + 0.05), ("pop", C_["india"]), ("pop", C_["fridge"]),
           ("pop", ST[1] + C_["ship"]), ("ding", ST[1] + C_["carib"]),
           ("pop", ST[2] + C_["news"]), ("thud", ST[2] + C_["slip"] + 0.2),
           ("thud", ST[3] + C_["melted"] + 0.15), ("pop", ST[3] + C_["nobody"] + 0.2),
           ("thud", ST[4] + C_["prison"] + 0.15),
           ("pop", ST[5] + C_["saw"]),
           ("thud", ST[6] + C_["free"] + 0.15), ("ding", ST[6] + C_["every"]),
           ("pop", ST[7] + C_["months"]),
           ("thud", ST[8] + C_["hundred"] + 0.15), ("ding", ST[8] + C_["hundred"] + 0.2),
           ("thud", ST[9] + C_["king"]), ("ding", ST[9] + C_["king"] + 0.05),
           ("ding", ST[10] + C_["thank"]),
           ("click", ST[11] + C_["cta_off"] + 1.6), ("click", ST[11] + C_["cta_off"] + 3.6), ("ding", ST[11] + C_["cta_off"] + 3.65)]
    ev += [("click", ST[6] + C_["free"] + 0.8 + k * 0.15) for k in range(8)]  # cubes clinking into glasses
    ev += [("click", ST[10] + 0.25 + k * 0.45 + 0.35) for k in range(3)]  # cubes into the drink
    ev += [("click", ST[9] + C_["king"] - 0.6 + 0.35 + i * 0.09 + (i % 3) * 0.03) for i in range(10)]  # coins
    ev = [(k, round(v, 3)) for k, v in ev if 0 <= v < total]
    audio.music("music.wav", total, bpm=100, seed=11)
    audio.sfx("sfx.wav", total, ev)
    base.OUT = "base_ice.mp4"
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_ice.mp4", voice, "music.wav", "sfx.wav", OUTFILE)
    print("wrote", OUTFILE)
