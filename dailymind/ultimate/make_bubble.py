"""YouTube Short: "Bubble Wrap Was Invented as WALLPAPER?!" (Skia toon, unedited vidIQ "Chris" voice).

Facts: 1957, two engineers in New Jersey (Alfred Fielding and Marc Chavannes) sealed two plastic shower curtains
together, trapping air bubbles, and tried to sell it as textured wallpaper - a flop; then as greenhouse insulation -
also a flop; then IBM needed to ship a new computer safely, the bubbles protected it, and the packaging business took
off (Sealed Air, a billion-dollar company). Today the company also sells a bubble wrap that does not pop.

New this video: a satisfying POP system (bubble collapses + ring + shards + comic "POP!" + a real pop sound on every
pop, collected into the SFX track automatically), bubble-wrap walls with living highlights, inflating bubbles on the
machine, an unpoppable bubble that squishes and springs back, walk-ins on every intro, and a hand guard so no hand
ever covers a face.
Usage: python make_bubble.py final.mp4 [scene,...] [t1,...]   stills: STILLS_DIR=dir python make_bubble.py x 0,1 1.0
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
sys.argv = [sys.argv[0], "base_bubble.mp4"]
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

GOLD, RED, AQUA, PINK = (255, 200, 60), (235, 60, 60), (120, 220, 255), (255, 130, 190)
make_ketchup.SPLAT_COLOR = (250, 195, 50)
base.HOOK_SKIP = 0.0
base.CRF = 16
CUE = {}
VOICE_DIR = "../bubble"
TAIL = 2.0

ENG1 = dict(skin=(240, 200, 170), hair="grey", hair_col=(180, 180, 185), coat=(240, 240, 238), pants=(70, 70, 82), glasses=True, nose="long")
ENG2 = dict(skin=(235, 190, 155), hair="neat", hair_col=(60, 40, 30), coat=(70, 95, 130), vest=(230, 230, 235), pants=(60, 60, 70),
            mustache=True, nose="long")
LADY50 = dict(skin=(245, 205, 180), hair="neat", hair_col=(150, 80, 50), coat=(230, 120, 150), dress=(230, 120, 150), pearls=True, lips=True,
              nose="small")
WORKER = dict(skin=(225, 180, 145), hair="cap", hair_col=(90, 60, 40), coat=(80, 110, 160), pants=(60, 70, 90), nose="small")
KIDY = dict(KID)


def blinking(t, ph=0.0):
    return ((t + ph) % 3.3) < 0.11


def pop_in(t, at, dur=0.35):
    return out_back((t - at) / dur, 2.2) if t > at else 0.0


def head_top(y, s):
    return y + s * (-262 - 70 - 88)


def safe_hands(hands):
    """A hand that would land on the face (centre (0,-332)) rests on the chest instead."""
    out = []
    for side, (hx, hy) in zip((-1, 1), hands):
        ax, ay = side * 60 + hx, -235 + hy
        if (ax / 118) ** 2 + ((ay + 332) / 125) ** 2 < 1:
            hx, hy = side * 10, 60
        out.append((hx, hy))
    return out


def stand(c, who, x, y, s, t, **pose):
    if "hands" in pose:
        pose["hands"] = safe_hands(pose["hands"])
    pose.setdefault("blink", blinking(t, x * 0.01))
    pose.setdefault("tilt", 2 * math.sin(t * 1.6 + x * 0.003))
    person(c, x, y, s, who, pose, t)


# ---------- bubbles ----------

POPS = {}  # scene -> list of (t, x, y, r, hero); filled by the scenes' pop schedules and used for the SFX track


def bubble(c, x, y, r, a=1.0, sq=0.0):
    """One air bubble (sq = squash for presses)."""
    rx, ry = r * (1 + 0.35 * sq), r * (1 - 0.45 * sq)
    c.drawOval(skia.Rect(x - rx, y - ry, x + rx, y + ry), P(Shader=rad(x - r * 0.3, y - r * 0.35, r * 1.4, [C(255, 255, 255, int(85 * a)), C(200, 230, 255, int(25 * a))])))
    c.drawOval(skia.Rect(x - rx, y - ry, x + rx, y + ry), S(C(230, 245, 255, int(130 * a)), max(1.5, r * 0.07)))
    c.drawOval(skia.Rect(x - r * 0.55, y - r * 0.6, x - r * 0.1, y - r * 0.3), P(C(255, 255, 255, int(200 * a))))


def popped(c, x, y, r, a=1.0):
    """A flattened, wrinkled bubble."""
    p = skia.Path()
    for k in range(7):
        ang = k / 7 * 2 * math.pi
        rr = r * (0.75 + 0.2 * math.sin(k * 2.7))
        (p.moveTo if k == 0 else p.lineTo)(x + math.cos(ang) * rr, y + math.sin(ang) * rr * 0.8)
    p.close()
    c.drawPath(p, P(C(255, 255, 255, int(40 * a))))
    c.drawPath(p, S(C(255, 255, 255, int(110 * a)), max(1.5, r * 0.06)))
    c.drawLine(x - r * 0.4, y - r * 0.1, x + r * 0.3, y + r * 0.2, S(C(255, 255, 255, int(110 * a)), max(1.2, r * 0.05)))


def comic_pop(c, x, y, k, s=1.0, word="POP!"):
    if not 0 <= k < 0.7:
        return
    sc = out_back(min(1, k / 0.18), 2.4) * s
    a = int(255 * min(1, (0.7 - k) / 0.2))
    c.save()
    c.translate(x, y - 40 * k)
    c.rotate(-10 + 20 * ((int(x) * 7) % 3) / 2)
    c.scale(sc, sc)
    p = skia.Path()  # starburst
    for i in range(16):
        ang = i / 16 * 2 * math.pi
        rr = 95 if i % 2 == 0 else 62
        (p.moveTo if i == 0 else p.lineTo)(math.cos(ang) * rr * 1.25, math.sin(ang) * rr)
    p.close()
    c.drawPath(p, P(C(255, 230, 80, a)))
    c.drawPath(p, S(C(60, 30, 20, a), 6))
    f = skia.Font(FB, 52)
    w = f.measureText(word)
    c.drawString(word, -w / 2, 18, f, P(C(60, 30, 20, a), Style=skia.Paint.kStroke_Style, StrokeWidth=10))
    c.drawString(word, -w / 2, 18, f, P(C(255, 70, 60, a)))
    c.restore()


def popfx(c, x, y, r, k, hero=False):
    """Pop: ring + shards (+ comic POP! for hero pops); k = seconds since the pop."""
    if 0 <= k < 0.4:
        u = k / 0.4
        c.drawCircle(x, y, r * (1 + 1.8 * u), S(C(255, 255, 255, int(220 * (1 - u))), max(2, r * 0.12 * (1 - u))))
        for i in range(8):
            ang = i / 8 * 2 * math.pi + 0.3
            r0, r1 = r * (1.1 + 1.2 * u), r * (1.5 + 1.8 * u)
            c.drawLine(x + math.cos(ang) * r0, y + math.sin(ang) * r0, x + math.cos(ang) * r1, y + math.sin(ang) * r1,
                       S(C(255, 255, 255, int(230 * (1 - u))), max(2, r * 0.1)))
    if hero:
        comic_pop(c, x + r * 1.6, y - r * 1.4, k, 0.9)


def bubble_grid(x0, y0, x1, y1, r):
    pts = []
    sp = r * 2.25
    row = 0
    y = y0 + r
    while y < y1 - r * 0.5:
        x = x0 + r + (sp / 2 if row % 2 else 0)
        while x < x1 - r * 0.5:
            pts.append((x, y))
            x += sp
        y += sp * 0.87
        row += 1
    return pts


_GRID_CACHE = {}


def bubble_wall(c, x0, y0, x1, y1, t, r=26, tint=(150, 200, 230), pops=(), alpha=1.0, base_a=255):
    """A bubble-wrap surface; pops = list of (time, idx) - bubble idx pops at that time (stays flat after)."""
    c.drawRect(skia.Rect(x0, y0, x1, y1), P(C(*tint, base_a)))
    key = (x0, y0, x1, y1, r)
    if key not in _GRID_CACHE:
        _GRID_CACHE[key] = bubble_grid(x0, y0, x1, y1, r)
    pts = _GRID_CACHE[key]
    gone = {i: tp for tp, i in pops}
    for i, (x, y) in enumerate(pts):
        tp = gone.get(i)
        shimmer = 0.85 + 0.15 * math.sin(t * 2 + x * 0.02 + y * 0.03)
        if tp is not None and t >= tp:
            popped(c, x, y, r, alpha)
        else:
            sq = 0.0
            if tp is not None and tp - 0.12 < t < tp:
                sq = (t - (tp - 0.12)) / 0.12  # the finger presses in just before the pop
            bubble(c, x, y, r, alpha * shimmer, sq)
    for tp, i in pops:
        if i < len(pts):
            popfx(c, pts[i][0], pts[i][1], r, t - tp)
    return pts


def wall_index(pts, x, y):
    return min(range(len(pts)), key=lambda i: (pts[i][0] - x) ** 2 + (pts[i][1] - y) ** 2)


# ---------- props ----------

def curtain_sheet(c, x0, y0, x1, y1, col, t, stripe=(255, 255, 255)):
    p = skia.Path()
    p.moveTo(x0, y0)
    for k in range(9):
        x = x0 + (x1 - x0) * k / 8
        p.lineTo(x + 6 * math.sin(t * 2 + k), y0 + (8 if k % 2 else 0))
    p.lineTo(x1, y1)
    p.lineTo(x0, y1)
    p.close()
    c.drawPath(p, P(C(*col, 220)))
    c.save()
    c.clipPath(p, doAntiAlias=True)
    for k in range(12):
        c.drawLine(x0 + k * 40, y0, x0 + k * 40 + 60, y1, S(C(*stripe, 90), 8))
    c.restore()


def machine(c, x, y, t, s=1.0):
    """Heat-sealing machine with two rollers."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    blob(c, rrect(-170, -240, 170, 60, 20), (110, 120, 135), 1.3, 0.7)
    for ry in (-150, -30):
        c.save()
        c.translate(0, ry)
        c.rotate(math.degrees(t * 4) * (1 if ry < 0 else -1))
        c.drawCircle(0, 0, 58, P(C(200, 200, 210)))
        c.drawCircle(0, 0, 58, S(OUT, 5))
        for k in range(6):
            ang = k / 6 * 2 * math.pi
            c.drawLine(0, 0, math.cos(ang) * 52, math.sin(ang) * 52, S(C(130, 130, 140), 6))
        c.restore()
    c.drawCircle(-120, -210, 12, P(C(255, 80, 60) if (t * 2) % 1 < 0.5 else C(120, 30, 30)))
    c.drawCircle(-85, -210, 12, P(C(90, 230, 120)))
    glow(c, 0, -90, 180, (255, 160, 80), int(70 + 30 * math.sin(t * 6)))
    c.restore()


def computer(c, x, y, s, t, wrap=0.0):
    """1950s mainframe: two cabinets with spinning tape reels and blinking lights (wrap 0..1 covers it in bubbles)."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    for k, cx in enumerate((-170, 170)):
        blob(c, rrect(cx - 150, -560, cx + 150, 0, 14), (205, 210, 215), 1.15, 0.8)
        for j, ry in enumerate((-450, -310)):
            c.save()
            c.translate(cx, ry)
            c.rotate(math.degrees(t * (3 + j)) * (1 if k else -1))
            c.drawCircle(0, 0, 56, P(C(60, 60, 70)))
            c.drawCircle(0, 0, 18, P(C(200, 200, 210)))
            for q in range(3):
                ang = q / 3 * 2 * math.pi
                c.drawCircle(math.cos(ang) * 34, math.sin(ang) * 34, 10, P(C(200, 200, 210)))
            c.restore()
        for j in range(12):
            on = ((t * 4 + j * 1.7 + k) % 2) < 1
            c.drawCircle(cx - 110 + (j % 6) * 44, -180 + (j // 6) * 40, 9, P(C(255, 200, 60) if on else C(90, 70, 40)))
    if wrap > 0:
        c.save()
        c.clipRect(skia.Rect(-330, -580 + 580 * (1 - wrap), 330, 10))
        bubble_wall(c, -330, -580, 330, 10, t, 30, (170, 210, 235), base_a=170)
        c.restore()
    c.restore()


def truck(c, x, y, s, t, bump=0.0):
    c.save()
    c.translate(x, y + bump)
    c.scale(s, s)
    blob(c, rrect(-420, -150, 260, -20, 12), (225, 90, 70), 1.25, 0.7)  # flat bed
    blob(c, rrect(260, -330, 470, -20, 26), (225, 90, 70), 1.25, 0.7)  # cab
    c.drawRoundRect(skia.Rect(300, -300, 440, -200), 16, 16, P(C(170, 215, 245)))
    for wx in (-300, 60, 380):
        c.save()
        c.translate(wx, -10)
        c.rotate(math.degrees(t * 6))
        c.drawCircle(0, 0, 62, P(C(35, 35, 40)))
        c.drawCircle(0, 0, 26, P(C(180, 180, 190)))
        c.drawLine(-22, 0, 22, 0, S(C(110, 110, 120), 6))
        c.restore()
    c.restore()


def plant(c, x, y, s, t, wilt=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    blob(c, rrect(-60, -10, 60, 90, 10), (190, 100, 70))
    for k in range(5):
        ang = math.radians(-150 + k * 30)
        ln = 150 - 30 * wilt
        lx, ly = math.cos(ang) * ln * (1 + 0.3 * wilt), math.sin(ang) * ln * (1 - 1.2 * wilt) + 30 * wilt  # leaves droop sideways
        p = skia.Path()
        p.moveTo(0, -10)
        p.quadTo(lx * 0.4, ly * 0.8 - 40, lx, ly)
        p.quadTo(lx * 0.5, ly * 0.4, 0, -10)
        col = (int(60 + 100 * wilt), int(160 - 60 * wilt), int(70 - 20 * wilt))
        blob(c, p, col, 1.3, 0.65)
    c.restore()


def snow(c, t, n=90, seed=3):
    r = random.Random(seed)
    for i in range(n):
        x0, y0, sp = r.uniform(0, W), r.uniform(0, H), r.uniform(60, 160)
        y = (y0 + t * sp) % (H + 40) - 20
        c.drawCircle(x0 + 20 * math.sin(t + i), y, r.uniform(3, 7), P(C(250, 252, 255, 200)))


def box(c, x, y, s, rot=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    blob(c, rrect(-90, -80, 90, 80, 6), (205, 160, 105), 1.2, 0.75)
    c.drawLine(-90, -10, 90, -10, S(C(170, 125, 75), 10))
    c.drawLine(0, -80, 0, 80, S(C(170, 125, 75), 10))
    c.restore()


def living_room(c, t, pops=()):
    pts = bubble_wall(c, 0, 0, W, 1560, t, 28, (45, 90, 140), pops)
    c.drawRect(skia.Rect(0, 0, W, 1560), P(Shader=lin((0, 0), (0, 1560), [C(10, 15, 35, 150), C(10, 15, 35, 40)])))
    c.drawRect(skia.Rect(0, 1520, W, 1560), P(C(240, 235, 225)))  # skirting
    c.drawRect(skia.Rect(0, 1560, W, H), P(Shader=lin((0, 1560), (0, H), [C(170, 120, 85), C(110, 75, 50)])))
    for k in range(8):
        c.drawLine(k * 160 - 200, H, k * 160 + 60, 1560, S(C(90, 60, 40, 90), 3))
    return pts


# ---------- scenes ----------

def hook_pops(d):
    """Pop rhythm in the hook: the kid's finger walks across the wall from frame 0."""
    out = []
    for i in range(int(d / 0.42)):
        out.append(0.15 + i * 0.42)
    return out


def art_hook(c, t):
    d = CUE["d"][0]
    times = hook_pops(d)
    pts = _GRID_CACHE.get((0, 0, W, 1560, 28)) or bubble_grid(0, 0, W, 1560, 28)
    _GRID_CACHE[(0, 0, W, 1560, 28)] = pts
    path = [(470 + 70 * math.sin(i * 1.3), 1330 - 60 * math.cos(i * 0.9)) for i in range(len(times))]  # within arm's reach
    pops = [(tp, wall_index(pts, x, y)) for tp, (x, y) in zip(times, path)]
    living_room(c, t, pops)
    # which pop is the finger on right now
    i = max(0, min(len(times) - 1, int((t - 0.15) / 0.42 + 0.7)))
    tx, ty = pts[pops[i][1]]
    x, y, s = 230, 1880, 1.55
    stand(c, KIDY, x, y, s, t, eyes="closed" if (t - times[i]) % 0.42 < 0.12 and t > times[0] else "wide", mouth="grin", brows="up",
          look=(1, 0.3), hands=[(-20, 150), ((tx - x) / s - 60, (ty - y) / s + 235)], tilt=3 * math.sin(t * 3))
    for k, tp in enumerate(times):
        if 0 <= t - tp < 0.7 and k % 2 == 0:
            comic_pop(c, pts[pops[k][1]][0] + 90, pts[pops[k][1]][1] - 110, t - tp, 0.9)
    POPS[0] = [(tp, pts[j][0], pts[j][1], 28, k % 2 == 0) for k, (tp, j) in enumerate(pops)]


ST1 = 0.0


def art_lab(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(40, 45, 55), C(80, 85, 95), C(35, 38, 45)])))
    for k in range(10):  # brick wall
        y = 900 + k * 60
        for j in range(12):
            x = j * 110 + (55 if k % 2 else 0) - 40
            c.drawRect(skia.Rect(x + 3, y + 3, x + 107, y + 57), P(C(120, 70, 60)))
    c.drawRect(skia.Rect(0, 1560, W, H), P(Shader=lin((0, 1560), (0, H), [C(110, 110, 120), C(60, 60, 70)])))
    glow(c, 540, 950, 420, (255, 220, 160), int(110 * flicker(t, 1)))
    c.drawLine(540, 760, 540, 900, S(C(30, 30, 35), 5))
    blob(c, rrect(500, 900, 580, 960, 10), (60, 60, 70))
    sealed, air, bub = CUE["sealed"], CUE["air"], CUE["bubbles1"]
    # two curtains feed into the machine from the left
    feed = ease((t - sealed + 0.3) / 0.6)
    curtain_sheet(c, 0, 1290, 300, 1360, (240, 140, 170), t, (255, 255, 255))
    curtain_sheet(c, 0, 1410, 300, 1480, (120, 190, 230), t, (255, 255, 255))
    machine(c, 420, 1520, t, 1.0)
    for k in range(3):  # air puffs
        ph = (t * 1.1 + k / 3) % 1
        if t > air:
            c.drawCircle(600 + ph * 100, 1330 - ph * 120, 14 + 20 * ph, P(C(255, 255, 255, int(150 * (1 - ph))), MaskFilter=blur(6)))
    arrive = 1.6
    x1 = -160 + 350 * ease(min(1, t / arrive))
    w1 = (x1 + 160) / 40 if t < arrive else None
    stand(c, ENG1, x1, 1880, 1.3, t, walk=w1, eyes="wide" if t > air else "open", mouth="O" if t > bub else "smile", brows="up",
          look=(1, 0), hands=[(-30, 150), (80, 40)])
    x2 = 1250 - 350 * ease(min(1, t / arrive))
    w2 = (1250 - x2) / 40 if t < arrive else None
    press = t > bub - 0.6
    stand(c, ENG2, x2, 1880, 1.3, t, walk=w2, eyes="wide" if press else "open", mouth="grin" if t > bub else "smile", brows="up",
          look=(-1, 0.6), hands=[(-28, 236) if press else (-90, 30), (30, 150)])
    # work table in front; the bubble sheet slides out of the machine onto it, bubbles inflating as they leave the rollers
    blob(c, rrect(560, 1600, 1060, 1660, 8), (150, 110, 70))
    c.drawRect(skia.Rect(590, 1660, 1030, 1760), P(C(110, 80, 50)))
    if t > sealed - 0.2:
        out_len = min(440, 170 * (t - sealed + 0.2))
        c.drawRect(skia.Rect(590, 1540, 590 + out_len, 1606), P(C(150, 200, 235, 170)))
        x = 606
        n = 0
        while x < 700 + out_len - 10:
            grow = min(1, (x - 590) / 110) * (0.6 + 0.4 * ease((t - air) / 0.6))
            r = 22 * grow + 3
            if n == 4 and t >= bub:  # x = 806: right under the engineer's finger
                popped(c, x, 1573, r)
                popfx(c, x, 1573, r, t - bub)
                comic_pop(c, 660, 1400, t - bub, 1.0)  # up-left, clear of every face
            else:
                bubble(c, x, 1573, r)
            x += 50
            n += 1


def art_design(c, t):
    living_room(c, t)
    c.drawRect(skia.Rect(0, 0, W, H), P(C(255, 220, 170, 25)))
    blob(c, rrect(330, 1390, 750, 1560, 40), (200, 90, 90), 1.2, 0.7)  # sofa
    blob(c, rrect(300, 1320, 380, 1560, 30), (180, 75, 75), 1.2, 0.7)
    blob(c, rrect(700, 1320, 780, 1560, 30), (180, 75, 75), 1.2, 0.7)
    c.drawLine(900, 1560, 900, 1150, S(C(60, 50, 40), 8))  # floor lamp
    blob(c, rrect(840, 1080, 960, 1160, 20), (250, 220, 150))
    glow(c, 900, 1120, 260, (255, 220, 150), int(120 * flicker(t, 2)))
    tada = ease((t - CUE["future"] + 0.2) / 0.4)
    for x, who, side in ((170, ENG1, 1), (1010, ENG2, -1)):
        stand(c, who, x, 1880, 1.15, t, eyes="closed" if tada > 0.5 else "open", mouth="grin", brows="up", look=(side, -0.3),
              hands=[(-60 * tada - 20, 150 - 300 * tada), (60 * tada + 20, 150 - 300 * tada)])
    if tada > 0:
        for k in range(10):
            a = t * 1.3 + k * 0.63
            sparkle(c, 540 + math.cos(a) * 420, 1150 + math.sin(a) * 260, 10, int(220 * tada))


def art_flop(c, t):
    living_room(c, t)
    nob, flop = CUE["nobody3"], CUE["flop"]
    arrive = 1.8
    x = 1250 - 600 * ease(min(1, t / arrive))
    walk = (1250 - x) / 40 if t < arrive else None
    look = t > nob
    stand(c, LADY50, x, 1880, 1.3, t, walk=walk, eyes="squint" if look else "open", mouth="disgust" if look else "smile",
          brows="angry" if look else "flat", look=(-1, -0.4) if look else (-1, 0), hands=[(-30, 150), (30, 150)] if not look else [(-140, -10), (20, 140)])
    sweat = t > flop - 0.4
    stand(c, ENG1, 220, 1880, 1.15, t, eyes="sad" if sweat else "open", mouth="frown" if sweat else "smile", brows="sad" if sweat else "up",
          look=(1, 0), hands=[(-20, 150), (20, 150)])
    if sweat:
        for n in range(3):
            dt = (t + n * 0.5) % 1.4
            if dt < 0.5:
                c.drawCircle(220 + (60 + 140 * dt) * (1 if n % 2 else -1), 1350 - 200 * dt + 700 * dt * dt, 10, P(C(190, 225, 255, 230)))
    if t > flop:  # a strip of wallpaper peels off and falls
        k = min(1, (t - flop) / 1.2)
        c.save()
        c.translate(820, 300 + 900 * k * k)
        c.rotate(25 * k)
        bubble_wall(c, -120, 0, 120, 600, t, 26, (70, 120, 170))
        c.restore()


def art_greenhouse(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(25, 35, 70), C(80, 100, 150)])))  # winter evening, readable titles
    snow(c, t)
    c.drawRect(skia.Rect(0, 1640, W, H), P(C(200, 210, 230)))
    gh = skia.Path()  # greenhouse frame
    gh.moveTo(120, 1640)
    gh.lineTo(120, 1050)
    gh.lineTo(540, 780)
    gh.lineTo(960, 1050)
    gh.lineTo(960, 1640)
    gh.close()
    c.drawPath(gh, P(C(210, 235, 245, 120)))
    cover = ease((t - CUE["greenhouse"] + 0.3) / 0.8)
    if cover > 0:
        c.save()
        c.clipPath(gh, doAntiAlias=True)
        c.clipRect(skia.Rect(0, 780, W, 780 + 880 * cover))
        bubble_wall(c, 120, 780, 960, 1640, t, 24, (90, 140, 190), base_a=110)
        c.restore()
    c.drawPath(gh, S(C(240, 245, 250), 16))
    for x in (330, 540, 750):
        c.drawLine(x, 1640, x, 1050 - (0 if x != 540 else 270), S(C(240, 245, 250), 10))
    for k, x in enumerate((260, 430, 650, 820)):
        plant(c, x, 1530, 0.9, t)
    warm = t > CUE["plants"]
    if warm:
        glow(c, 540, 1350, 420, (255, 190, 110), 70)
    stand(c, ENG2, 1010, 1880, 1.0, t, eyes="open", mouth="grin" if warm else "smile", brows="up", look=(-1, 0), hands=[(-120, -20), (30, 150)])


def art_flop2(c, t):
    art_greenhouse_bg(c, t)
    wilt = ease((t - CUE["flopped"] + 0.1) / 0.5)
    for k, x in enumerate((260, 430, 650, 820)):
        plant(c, x, 1530, 0.9, t, wilt)
    stand(c, ENG2, 1010, 1880, 1.0, t, eyes="sad", mouth="frown", brows="sad", look=(-1, 0.5), hands=[(-20, 150), (20, 150)])


def art_greenhouse_bg(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(20, 25, 50), C(60, 70, 110)])))
    snow(c, t + 3, 120)
    c.drawRect(skia.Rect(0, 1640, W, H), P(C(180, 190, 210)))
    gh = skia.Path()
    gh.moveTo(120, 1640)
    gh.lineTo(120, 1050)
    gh.lineTo(540, 780)
    gh.lineTo(960, 1050)
    gh.lineTo(960, 1640)
    gh.close()
    c.save()
    c.clipPath(gh, doAntiAlias=True)
    bubble_wall(c, 120, 780, 960, 1640, t, 24, (90, 140, 190), base_a=110)
    c.restore()
    c.drawPath(gh, S(C(240, 245, 250), 16))


def art_computer(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(30, 40, 60), C(60, 75, 100), C(30, 35, 50)])))
    for k in range(9):
        c.drawLine(0, 900 + k * 90, W, 900 + k * 90, S(C(255, 255, 255, 12), 2))
    c.drawRect(skia.Rect(0, 1620, W, H), P(Shader=lin((0, 1620), (0, H), [C(150, 150, 160), C(90, 90, 100)])))
    k = pop_in(t, 0.1)
    if k > 0:
        computer(c, 540, 1620, 0.95 * k, t)
    br = CUE["breaking"]
    worry = t > CUE["ship"]
    stand(c, WORKER, 160, 1900, 1.0, t, eyes="wide" if worry else "open", mouth="O" if worry else "smile", brows="up", look=(1, -0.3),
          hands=[(-20, 150), (20, 150)])
    stand(c, ENG1, 920, 1900, 1.0, t, eyes="wide" if worry else "open", mouth="O" if worry else "smile", brows="up", look=(-1, -0.3),
          hands=[(-20, 150), (20, 150)])
    if t > br:  # a crack flashes across the screen
        u = min(1, (t - br) / 0.25)
        p = skia.Path()
        p.moveTo(330, 1060)
        for j, (dx, dy) in enumerate(((60, 80), (-30, 70), (70, 90), (-20, 80), (60, 100))):
            if j / 5 <= u:
                p.rLineTo(dx, dy)
        c.drawPath(p, S(C(255, 255, 255, 230), 8))
        q = pop_in(t, br + 0.15)
        if q > 0:
            c.drawString("?!", 860, 1040, skia.Font(FB, 140 * q), P(C(255, 220, 120)))


def art_ship(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, 1500), [C(40, 40, 90), C(200, 120, 110), C(250, 180, 120)], [0, 0.6, 1])))  # sunset
    for k in range(4):  # hills
        p = skia.Path()
        p.moveTo(0, 1500)
        for j in range(7):
            p.quadTo(j * 180 + 90, 1380 - 60 * ((j + k) % 2) - k * 20, j * 180 + 180, 1500)
        p.lineTo(W, H)
        p.lineTo(0, H)
        c.drawPath(p, P(C(100 + 20 * k, 170 - 10 * k, 100)))
    c.drawRect(skia.Rect(0, 1640, W, H), P(C(80, 80, 90)))
    off = (t * 600) % 240
    for k in range(6):
        c.drawRect(skia.Rect(k * 240 - off, 1720, k * 240 - off + 120, 1740), P(C(240, 220, 120)))
    arrive = CUE["arrived"]
    bump = -abs(math.sin(t * 9)) * 26 if t < arrive else 0
    x = 300 + 240 * ease(min(1, t / max(0.5, arrive)))
    truck(c, x, 1660, 1.0, t, bump)
    wrap = ease((t - CUE["wrapped"] + 0.2) / 0.8)
    c.save()
    c.translate(0, bump)
    computer(c, x - 80, 1510, 0.42, t, wrap=max(0.0, wrap))
    c.restore()
    if t > CUE["safe"]:
        for k in range(10):
            a = t * 1.5 + k * 0.63
            sparkle(c, x - 80 + math.cos(a) * 220, 1300 + math.sin(a) * 160, 9, 220)


def art_business(c, t):
    U.T_EIGHT = CUE["billion"] - 0.6
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(30, 25, 40), C(80, 60, 70), C(30, 25, 35)])))
    c.drawRect(skia.Rect(0, 1660, W, H), P(C(70, 65, 70)))
    belt = (t * 260) % 260
    c.drawRect(skia.Rect(0, 1500, W, 1560), P(C(50, 50, 55)))  # conveyor
    for k in range(6):
        c.drawCircle(k * 220 + 60 - (t * 120) % 220, 1530, 22, P(C(120, 120, 130)))
    for k in range(6):
        x = k * 260 - belt
        box(c, x, 1420, 0.85)
        c.save()
        c.clipRect(skia.Rect(x - 76, 1350, x + 76, 1400))
        bubble_wall(c, x - 76, 1350, x + 76, 1400, t, 12, (190, 225, 245), base_a=180)
        c.restore()
    for k in range(3):  # rolls of bubble wrap stacked
        cx = 160 + k * 380
        c.drawOval(skia.Rect(cx - 90, 1100, cx + 90, 1150), P(C(200, 230, 245)))
        c.drawRect(skia.Rect(cx - 90, 1125, cx + 90, 1340), P(C(200, 230, 245, 200)))
        c.save()
        c.clipRect(skia.Rect(cx - 90, 1125, cx + 90, 1340))
        bubble_wall(c, cx - 90, 1125, cx + 90, 1340, t, 16, (200, 230, 245), base_a=160)
        c.restore()
    for x, y, r, face, speed in U.coins_at(t):  # coins behind the characters
        U.draw_coin(c, x, y, r, face, speed)
    for i, (x, lk) in enumerate([(180, ENG1), (900, ENG2)]):
        bounce = abs(math.sin(t * 6 + i)) * 14 if t > CUE["billion"] else 0
        stand(c, lk, x, 1880 - bounce, 1.0, t, eyes="closed" if t > CUE["billion"] else "open", mouth="laugh" if t > CUE["billion"] else "grin",
              brows="up", look=(0, -0.2), hands=[(-80, -180), (80, -180)] if t > CUE["billion"] else [(-20, 150), (20, 150)])


def art_twist(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(35, 20, 50), C(80, 40, 90), C(30, 15, 40)])))
    for k in range(14):
        a = k / 14 * 2 * math.pi + t * 0.4
        p = skia.Path()
        p.moveTo(540, 1250)
        p.lineTo(540 + math.cos(a) * 1500, 1250 + math.sin(a) * 1500)
        p.lineTo(540 + math.cos(a + 0.13) * 1500, 1250 + math.sin(a + 0.13) * 1500)
        p.close()
        c.drawPath(p, P(C(255, 200, 255, 18)))
    # one giant bubble that refuses to pop: presses squish it and it springs back
    presses = [0.35 + i * 0.6 for i in range(int(CUE["d"][9] / 0.6))]  # pressing all scene long
    sq = 0.0
    for tp in presses:
        if tp <= t < tp + 0.45:
            u = (t - tp) / 0.45
            sq = math.sin(math.pi * min(1, u * 1.6)) * (1 - u) + 0.15 * spring(t, tp + 0.25, 4, 6)
    sq = max(0.0, sq)
    bx, by, br = 540, 1250, 230
    c.drawOval(skia.Rect(bx - 260, by + 200, bx + 260, by + 250), P(C(0, 0, 0, 80), MaskFilter=blur(14)))
    bubble(c, bx, by + 230 * 0.45 * sq * 0.5, br, 1.0, sq * 0.8)
    c.drawCircle(bx, by, br, P(C(160, 120, 255, 30)))
    # the kid's finger pressing from the right (hand never on the face)
    press_x = bx + br * 0.93 * (1 + 0.35 * sq * 0.8) + 10
    x, y, s = 930, 1760, 1.1  # close enough to reach the bubble; the arm stays clear of his face
    angry = t > CUE["pop9"]
    stand(c, KIDY, x, y, s, t, eyes="squint" if angry else "open", mouth="frown" if angry else "grin", brows="angry" if angry else "up",
          look=(-1, 0.3), hands=[((press_x - x) / s + 60, (by + 100 - y) / s + 235), (30, 150)], tilt=-4 * sq)
    if angry:
        for k in range(3):
            ph = ((t - CUE["pop9"]) * 1.6 + k / 3) % 1
            c.drawCircle(x + (k - 1) * 50, head_top(y, s) - ph * 120, 16 + 20 * ph, P(C(240, 240, 245, int(170 * (1 - ph))), MaskFilter=blur(6)))


def art_popping(c, t):
    d = CUE["d"][10]
    pts = _GRID_CACHE.get((0, 0, W, 1560, 28)) or bubble_grid(0, 0, W, 1560, 28)
    _GRID_CACHE[(0, 0, W, 1560, 28)] = pts
    times = [0.1 + i * 0.3 for i in range(int(d / 0.3))]
    path = [(440 + 80 * math.sin(i * 1.7), 1350 - 70 * math.cos(i * 1.1)) for i in range(len(times))]  # within arm's reach
    pops = [(tp, wall_index(pts, x, y)) for tp, (x, y) in zip(times, path)]
    living_room(c, t, pops)
    i = max(0, min(len(times) - 1, int((t - 0.1) / 0.3 + 0.7)))
    tx, ty = pts[pops[i][1]]
    x, y, s = 200, 1880, 1.45
    stand(c, KIDY, x, y, s, t, eyes="closed", mouth="laugh", brows="up", look=(1, 0),
          hands=[(-20, 150), ((tx - x) / s - 60, (ty - y) / s + 235)], tilt=4 * math.sin(t * 5))
    for k, tp in enumerate(times):
        if k % 3 == 0 and 0 <= t - tp < 0.7:
            comic_pop(c, pts[pops[k][1]][0] + 90, pts[pops[k][1]][1] - 110, t - tp, 0.85)
    POPS[10] = [(tp, pts[j][0], pts[j][1], 28, k % 3 == 0) for k, (tp, j) in enumerate(pops)]


def art_cta(c, t):
    U.T_EIGHT = -10
    U.background(c, t, 0)
    U.spotlight(c, t, 0)
    U.pedestal(c, t)
    sub = CUE["cta_off"] + 3.6
    c.save()
    c.translate(540, 1560)
    if t < sub:
        bubble(c, 0, 0, 120, 1.6, 0.06 * math.sin(t * 3))
        for side in (-1, 1):  # sunglasses
            r = skia.RRect.MakeRectXY(skia.Rect(side * 55 - 48, -60, side * 55 + 48, 0), 22, 22)
            c.drawRRect(r, P(Shader=lin((0, -60), (0, 0), [C(70, 70, 90), C(8, 8, 14)])))
            c.drawRRect(r, S(C(10, 10, 10), 6))
        c.drawLine(-8, -40, 8, -40, S(C(10, 10, 10), 10))
        c.drawArc(skia.Rect(-40, 20, 40, 70), 20, 140, False, S(C(255, 255, 255), 8))
    else:
        popfx(c, 0, 0, 120, t - sub, hero=False)
        comic_pop(c, 0, -60, t - sub, 1.6)
    c.restore()
    c.drawPaint(P(C(10, 6, 14, 150)))


ART = [art_hook, art_lab, art_design, art_flop, art_greenhouse, art_flop2, art_computer, art_ship, art_business, art_twist, art_popping, art_cta]
PUSH = [(1.0, 1.05), (1.0, 1.06), (1.0, 1.06), (1.0, 1.06), (1.0, 1.06), (1.05, 1.0), (1.0, 1.07), (1.0, 1.05), (1.0, 1.06), (1.0, 1.08), (1.0, 1.05), (1.0, 1.0)]
ANCHOR = [(540, 1300), (540, 1450), (540, 1400), (540, 1450), (540, 1400), (540, 1400), (540, 1450), (540, 1500), (540, 1450), (540, 1300), (540, 1300), (540, 1300)]


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
    c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=U.BLOOM, ImageFilter=skia.ImageFilters.Blur(24, 24), BlendMode=skia.BlendMode.kPlus, Alphaf=0.35))
    c.drawPaint(P(Shader=rad(540, 1100, 1250, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 190)], [0, 0.5, 1])))
    c.drawRect(skia.Rect(0, 0, W, 900), P(Shader=lin((0, 0), (0, 900), [C(5, 4, 10, 170), C(5, 4, 10, 0)])))
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
    line(img, "Bubble wrap was invented", 235, font(FONT_B, 68))
    line(img, "to go on your", 330, F_MID)
    slam(img, "WALLS!", 430, t, CUE["walls"] - 0.1, AQUA, 170)
    text_block(img, "...as WALLPAPER!", font(FONT_B, 64), 650, t, GOLD, CUE["wallpaper"])
    text_block(img, "And nobody wanted it.", font(FONT_B, 54), 740, t, (255, 255, 255), CUE["nobody"])
    impact(img, t, CUE["walls"] + 0.1, 18)


def tx_lab(img, t):
    tag(img, "NEW JERSEY, 1957", t, (70, 110, 170))
    title(img, t, "Two engineers had an idea", "Seal two shower curtains together!", CUE["sealed"], sub_color=AQUA)


def tx_design(img, t):
    title(img, t, "\"The future of home design!\"", "Bumpy, textured WALLPAPER", CUE["bumpy"], sub_color=GOLD)


def tx_flop(img, t):
    title(img, t, "Bubbles on your walls?", "Nobody wanted them.", CUE["walls3"])
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "FLOP!", t, CUE["flop"], col=RED, size=120)
    impact(img, t, CUE["flop"] + 0.15, 14)


def tx_greenhouse(img, t):
    tag(img, "TRY #2", t, (60, 140, 90))
    title(img, t, "Greenhouse insulation!", "Bubbles to keep plants warm", CUE["plants"], sub_color=AQUA)


def tx_flop2(img, t):
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 560, "FLOP AGAIN!", t, CUE["flopped"], col=RED, size=110)
    impact(img, t, CUE["flopped"] + 0.15, 12)


def tx_computer(img, t):
    title(img, t, "A huge new computer...", "How do you ship it without breaking it?", CUE["ship"])


def tx_ship(img, t):
    title(img, t, "Wrapped in bubbles...")
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 640, "SAFE!", t, CUE["safe"], col=(80, 220, 120), size=130)
    impact(img, t, CUE["safe"] + 0.15, 14)


def tx_business(img, t):
    title(img, t, "Suddenly, EVERYONE wanted it", y=260)
    slam(img, "$1 BILLION", 420, t, CUE["billion"] - 0.1, GOLD, 150)
    impact(img, t, CUE["billion"] + 0.1, 16)


def tx_twist(img, t):
    title(img, t, "But here's the twist...", "Bubble wrap you CAN'T pop!", CUE["sells"], sub_color=PINK)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "NO POP?!", t, CUE["pop9"], col=RED, size=110)
    impact(img, t, CUE["pop9"] + 0.15, 12)


def tx_popping(img, t):
    title(img, t, "So every pop you hear...", "...is a piece of failed wallpaper!", CUE["popping"], sub_color=GOLD)


def tx_cta(img, t):
    text_block(img, "Learned something new?", font(FONT_B, 68), 330, t, delay=0.0)
    make_salt.draw_cta(img, ImageDraw.Draw(img, "RGBA"), W / 2, 1250, t, off=CUE["cta_off"])


TEXT = [tx_hook, tx_lab, tx_design, tx_flop, tx_greenhouse, tx_flop2, tx_computer, tx_ship, tx_business, tx_twist, tx_popping, tx_cta]
base.TRANSITION = splat

if __name__ == "__main__":
    voice = f"{VOICE_DIR}/voice.mp3"
    tl = Timeline(voice)
    firsts = ["in nineteen", "they thought", "but nobody", "so we|they tried", "have|that flocked|flopped", "then", "to|so the engineers",
              "suddenly", "but here's", "so next", "learn"]
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
               walls=f("walls", 0, 0.0), wallpaper=f("as wallpaper", 0), nobody=f("nobody", 0),
               sealed=f("sealed", 1), air=f("air", 1), bubbles1=f("bottles|bubbles", 1),
               future=f("future", 2), bumpy=f("bumpy", 2),
               nobody3=f("nobody", 3), walls3=f("walls", 3), flop=f("flop", 3, 0.15),
               greenhouse=f("greenhouse", 4), plants=f("plants|plan", 4),
               flopped=f("flocked|flopped", 5, 0.15),
               computer=f("computer", 6), ship=f("ship|shit", 6), breaking=f("breaking", 6),
               wrapped=f("rather|wrapped", 7), arrived=f("arrived", 7), safe=f("safe", 7, 0.15),
               billion=f("billion", 8, 0.0),
               sells=f("sells", 9), pop9=f("pop", 9, 0.15),
               popping=f("popping", 10))
    CUE["cta_off"] = round(max(0.0, tl.find("like|within", S0[11]) - S0[11] - 1.6 + 0.15), 2)
    print("starts:", S0)
    print("durations:", durs, round(sum(durs), 2))
    print("cues:", {k: v for k, v in CUE.items() if k not in ("d", "S")})
    print("subscribed at", CUE["cta_off"] + 3.6, "of CTA", durs[-1])
    json.dump({"starts": S0, "durs": durs, "cues": {k: v for k, v in CUE.items() if k not in ("d", "S")}}, open(f"{VOICE_DIR}/plan.json", "w"), indent=1)
    if STILLS:
        out = os.environ.get("STILLS_DIR", VOICE_DIR + "/stills")
        os.makedirs(out, exist_ok=True)
        for i in ONLY:
            for tt in STILLS:
                img = Image.new("RGBA", (W, H))
                scene(i, TEXT[i])(img, ImageDraw.Draw(img), float(tt))
                img.convert("RGB").save(f"{out}/bubble_{i}_{tt}.png")
        sys.exit()
    # pop schedules for the SFX track (computed by drawing one frame of each popping scene)
    for i in (0, 10):
        ART[i](skia.Surface(W, H).getCanvas(), 0.0)
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), scene(i, TEXT[i])) for i, dd in enumerate(durs)]
    if ONLY:
        base.SCENES[:] = [s for i, s in enumerate(base.SCENES) if i in ONLY]
    ST, C_ = S0, CUE
    ev = [("whoosh", s) for s in ST[1:]]
    ev += [("pop", ST[sc] + tp) for sc in (0, 10) for tp, *_ in POPS[sc]]
    ev += [("thud", C_["walls"]), ("ding", C_["wallpaper"]),
           ("ding", ST[1] + C_["bubbles1"]),
           ("ding", ST[2] + C_["future"]),
           ("thud", ST[3] + C_["flop"] + 0.15),
           ("ding", ST[4] + C_["greenhouse"]),
           ("thud", ST[5] + C_["flopped"] + 0.15),
           ("pop", ST[6] + C_["computer"] - 0.2), ("thud", ST[6] + C_["breaking"]),
           ("thud", ST[7] + C_["safe"] + 0.15), ("ding", ST[7] + C_["safe"] + 0.2),
           ("thud", ST[8] + C_["billion"]), ("ding", ST[8] + C_["billion"] + 0.05),
           ("thud", ST[9] + C_["pop9"] + 0.15),
           ("click", ST[11] + C_["cta_off"] + 1.6), ("pop", ST[11] + C_["cta_off"] + 3.6), ("ding", ST[11] + C_["cta_off"] + 3.65)]
    ev += [("click", ST[9] + 0.35 + i * 0.6) for i in range(int(durs[9] / 0.6))]  # presses on the unpoppable bubble
    ev += [("pop", ST[1] + C_["bubbles1"])]  # the very first bubble pop in the lab
    ev += [("click", ST[8] + C_["billion"] - 0.6 + 0.35 + i * 0.09 + (i % 3) * 0.03) for i in range(10)]  # coins
    ev = [(k, round(v, 3)) for k, v in ev if 0 <= v < total]
    audio.music("music.wav", total, bpm=108, seed=29)
    audio.sfx("sfx.wav", total, ev)
    base.OUT = "base_bubble.mp4"
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_bubble.mp4", voice, "music.wav", "sfx.wav", OUTFILE)
    print("wrote", OUTFILE)
