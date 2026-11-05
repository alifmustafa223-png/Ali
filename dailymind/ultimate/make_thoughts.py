"""10-minute long-form: "What If You Got $1 Every Time Someone Thought About You?" (1920x1080, Skia toon).

One shot per script paragraph (74). Cue words come from the forced alignment (align_script.py), so every pop-in,
+$1 notification and slam lands on the spoken word. Signature visuals: a little "$1" thought bubble flies from the
person thinking to YOU's phone; a balance counter rolls up in the corner all video long.

Render:   python make_thoughts.py render 0/4 ... 3/4   (4 parallel parts)  then   python make_thoughts.py final
Stills:   python make_thoughts.py stills 12,13 0.5,2.0 [outdir]
"""
import json
import math
import os
import random
import subprocess
import sys

import numpy as np
import skia

sys.path.insert(0, "..")
from long_engine import *  # noqa: F401,F403
import long_engine as E

DIR = "../long_thoughts"
ST = Story(f"{DIR}/align.json", tail=2.5)
GOLD, GREEN, RED, PINK, BLUE = (255, 200, 60), (90, 230, 140), (240, 70, 70), (255, 120, 190), (90, 170, 255)

# ---------- cast (short hair everywhere near hands; pigtails sit behind the body) ----------
YOU = dict(skin=(245, 205, 170), hair="kid", hair_col=(80, 50, 30), coat=(40, 150, 170), pants=(60, 80, 130), nose="small")
YOU_BLUE = dict(YOU, hair_col=(60, 130, 255))
MOM = dict(skin=(240, 200, 170), hair="neat", hair_col=(120, 70, 45), coat=(200, 95, 115), apron=(245, 235, 225), pants=(70, 60, 80),
           lips=True, nose="small")
BRO = dict(skin=(245, 205, 170), hair="kid", hair_col=(80, 50, 30), coat=(240, 140, 50), pants=(60, 80, 130), nose="small")
FRIEND = dict(skin=(205, 150, 115), hair="kid", hair_col=(30, 22, 20), coat=(245, 200, 60), pants=(50, 60, 90), glasses=True, nose="small")
TEACHER = dict(skin=(240, 200, 170), hair="neat", hair_col=(100, 90, 85), coat=(110, 90, 140), vest=(60, 50, 70), pants=(60, 55, 70),
               glasses=True, mustache=True, nose="long")
CRUSH = dict(skin=(250, 210, 185), hair="pigtails", hair_col=(140, 60, 40), coat=(170, 110, 210), dress=(170, 110, 210), lips=True, nose="small")
GRANDMA = dict(skin=(240, 205, 180), hair="powder", hair_col=(225, 225, 230), coat=(160, 140, 190), dress=(160, 140, 190), pearls=True,
               glasses=True, lips=True, nose="small")
PRINCIPAL = dict(skin=(235, 190, 160), hair="grey", hair_col=(170, 170, 175), coat=(60, 60, 75), vest=(150, 40, 50), pants=(50, 50, 60),
                 glasses=True, nose="long")
SALESMAN = dict(skin=(240, 200, 170), hair="neat", hair_col=(40, 30, 25), coat=(200, 60, 60), vest=(240, 240, 240), pants=(50, 50, 60),
                mustache=True, nose="long")
BANKER = dict(skin=(235, 195, 165), hair="neat", hair_col=(60, 50, 45), coat=(50, 60, 80), vest=(230, 230, 235), pants=(45, 50, 60),
              glasses=True, nose="long")
LAWYER = dict(skin=(200, 145, 110), hair="neat", hair_col=(30, 25, 22), coat=(30, 30, 40), vest=(200, 40, 50), pants=(30, 30, 40), nose="long")
SINGER = dict(skin=(245, 210, 185), hair="pigtails", hair_col=(250, 100, 180), coat=(240, 70, 160), dress=(240, 70, 160), glasses=True,
              lips=True, nose="small")
REPORTER = dict(skin=(230, 185, 150), hair="neat", hair_col=(60, 40, 30), coat=(90, 110, 160), pants=(50, 50, 60), nose="small")
CATGUY = dict(skin=(240, 200, 170), hair="kid", hair_col=(200, 160, 60), coat=(90, 180, 110), pants=(60, 60, 80), glasses=True, nose="small")


def you(k):
    return YOU_BLUE if k >= 27 else YOU


def blink(t, ph=0.0):
    return ((t + ph) % 3.4) < 0.11


def pop(t, at, dur=0.35):
    return out_back((t - at) / dur, 2.2) if t > at else 0.0


def head_c(x, y, s):
    return x, y - 332 * s


# ---------- props ----------

def thought(c, x0, y0, x1, y1, t, t0, dur=0.9, amt="$1", col=GREEN):
    """A little thought bubble with '$1' that flies from a thinker's head (x0, y0) to (x1, y1)."""
    k = (t - t0) / dur
    if not 0 <= k <= 1:
        return
    u = ease(k)
    x = x0 + (x1 - x0) * u
    y = y0 + (y1 - y0) * u - 160 * math.sin(math.pi * u)
    a = int(255 * min(1, k * 5, (1 - k) * 5))
    s = 0.6 + 0.4 * math.sin(math.pi * min(1, k * 1.4))
    for j, (dx, r) in enumerate(((-28, 7), (-16, 11))):
        c.drawCircle(x + dx * s - 30 * (1 - u), y + 40 * s + j * 8, r * s, P(C(255, 255, 255, a)))
    c.drawCircle(x, y, 46 * s, P(C(255, 255, 255, a)))
    c.drawCircle(x, y, 46 * s, S(C(40, 40, 50, a), 4))
    text(c, amt, x, y + 15 * s, 40 * s, (30, 150, 80), a, shadow=False)
    if k > 0.9:
        glow(c, x1, y1, 120, col, int(200 * (1 - (k - 0.9) / 0.1)))


def sparkle_ring(c, x, y, r, t, n=8, a=210, col=(255, 240, 170)):
    for j in range(n):
        ang = t * 1.4 + j / n * 2 * math.pi
        sparkle(c, x + math.cos(ang) * r, y + math.sin(ang) * r * 0.7, 10, a, col)


def screen_bank(lines, t, title="Thought Bank"):
    def fn(c, w, h):
        c.drawRect(skia.Rect(0, 0, w, h), P(C(245, 247, 250)))
        c.drawRect(skia.Rect(0, 0, w, 70), P(C(40, 190, 110)))
        text(c, title, w / 2, 46, 26, (255, 255, 255), shadow=False)
        for i, (amt, lab) in enumerate(lines[:5]):
            y = 110 + i * 78
            c.drawRoundRect(skia.Rect(12, y - 30, w - 12, y + 40), 16, 16, P(C(255, 255, 255)))
            c.drawRoundRect(skia.Rect(12, y - 30, w - 12, y + 40), 16, 16, S(C(220, 225, 230), 2))
            text(c, amt, 26, y + 2, 26, (30, 150, 80), align="left", shadow=False)
            text(c, lab, 26, y + 30, 16, (110, 110, 120), align="left", bold=False, shadow=False)
    return fn


def screen_views(views, t, likes=None, red=False):
    def fn(c, w, h):
        c.drawRect(skia.Rect(0, 0, w, h), P(C(20, 20, 28)))
        c.drawRect(skia.Rect(0, 60, w, 300), P(C(255, 220, 90)))
        for j in range(9):  # ducks in the thumbnail
            duck(c, 30 + (j * 37) % 210, 120 + (j * 53) % 160, 0.32, t + j)
        tri = skia.Path()
        tri.moveTo(w / 2 - 22, 150)
        tri.lineTo(w / 2 - 22, 210)
        tri.lineTo(w / 2 + 28, 180)
        tri.close()
        c.drawPath(tri, P(C(255, 255, 255)))
        text(c, "Why not?", 16, 340, 26, (255, 255, 255), align="left", shadow=False)
        text(c, views, 16, 380, 22, (240, 90, 90) if red else (190, 190, 200), align="left", bold=False, shadow=False)
        if likes:
            text(c, likes, 16, 420, 22, (190, 190, 200), align="left", bold=False, shadow=False)
    return fn


def duck(c, x, y, s, t=0.0, rot=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot + 4 * math.sin(t * 3))
    c.scale(s, s)
    blob(c, oval(0, 0, 60, 40), (255, 215, 50), 1.25, 0.75)
    blob(c, oval(34, -40, 32, 30), (255, 215, 50), 1.25, 0.75)
    p = skia.Path()
    p.moveTo(60, -44)
    p.lineTo(92, -36)
    p.lineTo(60, -28)
    p.close()
    c.drawPath(p, P(C(250, 130, 40)))
    c.drawCircle(42, -48, 6, P(C(30, 20, 15)))
    c.restore()


def money_pile(c, x, y, s, t, n=30):
    r = random.Random(4)
    for i in range(n):
        dx, dy = r.uniform(-1, 1) * 200 * s, -abs(r.gauss(0, 1)) * 60 * s
        c.save()
        c.translate(x + dx, y + dy)
        c.rotate(r.uniform(-30, 30))
        blob(c, rrect(-50 * s, -24 * s, 50 * s, 24 * s, 6), (110, 180, 100), 1.2, 0.7)
        c.drawCircle(0, 0, 10 * s, P(C(220, 240, 210)))
        c.restore()


def bill_rain(c, t, t0, n=40, seed=3):
    if t < t0:
        return
    r = random.Random(seed)
    for i in range(n):
        x0, sp, ph = r.uniform(0, W), r.uniform(250, 450), r.uniform(0, 6.28)
        y = -80 + ((t - t0) * sp + r.uniform(0, 1200)) % (H + 160)
        c.save()
        c.translate(x0 + 40 * math.sin(t * 2 + ph), y)
        c.rotate(30 * math.sin(t * 3 + ph))
        blob(c, rrect(-40, -18, 40, 18, 5), (110, 180, 100), 1.2, 0.7, outline=False)
        c.drawCircle(0, 0, 8, P(C(220, 240, 210)))
        c.restore()


def heart(c, x, y, s, a=255, col=(255, 90, 140)):
    p = skia.Path()
    p.moveTo(x, y + 30 * s)
    p.cubicTo(x - 60 * s, y - 10 * s, x - 30 * s, y - 55 * s, x, y - 25 * s)
    p.cubicTo(x + 30 * s, y - 55 * s, x + 60 * s, y - 10 * s, x, y + 30 * s)
    p.close()
    c.drawPath(p, P(C(*col, a)))


def angry_face(c, x, y, s, a=255):
    c.drawCircle(x, y, 40 * s, P(C(240, 80, 70, a)))
    c.drawLine(x - 22 * s, y - 14 * s, x - 6 * s, y - 6 * s, S(C(60, 10, 10, a), 5 * s))
    c.drawLine(x + 22 * s, y - 14 * s, x + 6 * s, y - 6 * s, S(C(60, 10, 10, a), 5 * s))
    c.drawArc(skia.Rect(x - 16 * s, y + 6 * s, x + 16 * s, y + 26 * s), 200, 140, False, S(C(60, 10, 10, a), 5 * s))


# ---------- sets ----------

def bedroom(c, t, night=False):
    wall = (40, 45, 80) if night else (120, 160, 200)
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(*wall), C(*[v * 0.7 for v in wall])])))
    c.drawRect(skia.Rect(1250, 160, 1700, 560), P(C(20, 25, 60) if night else C(170, 220, 255)))
    if night:
        c.drawCircle(1580, 260, 50, P(C(240, 240, 220)))
        for k in range(14):
            c.drawCircle(1270 + (k * 97) % 420, 190 + (k * 53) % 330, 3, P(C(255, 255, 240, 200)))
    else:
        c.drawCircle(1600, 260, 60, P(C(255, 240, 160)))
    c.drawRect(skia.Rect(1250, 160, 1700, 560), S(C(240, 240, 245), 16))
    c.drawLine(1475, 160, 1475, 560, S(C(240, 240, 245), 10))
    for k, col in enumerate(((240, 120, 90), (90, 200, 160), (250, 210, 80))):  # posters
        c.drawRect(skia.Rect(200 + k * 230, 180 + (k % 2) * 40, 380 + k * 230, 420 + (k % 2) * 40), P(C(*col)))
    c.drawRect(skia.Rect(0, 820, W, H), P(Shader=lin((0, 820), (0, H), [C(160, 110, 80), C(110, 75, 55)])))
    blob(c, rrect(1150, 620, 1880, 860, 30), (240, 240, 250), 1.05, 0.85)  # bed
    blob(c, rrect(1180, 560, 1420, 660, 30), (255, 255, 255), 1.05, 0.85)
    c.drawRect(skia.Rect(1150, 700, 1880, 860), P(C(80, 120, 200)))
    if night:
        c.drawPaint(P(C(10, 15, 40, 90)))


def kitchen(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(250, 225, 180), C(230, 190, 140)])))
    c.drawRect(skia.Rect(300, 150, 700, 450), P(C(170, 220, 255)))
    c.drawRect(skia.Rect(300, 150, 700, 450), S(C(255, 255, 255), 14))
    c.drawCircle(560, 260, 50, P(C(255, 240, 160)))
    for x in range(0, W, 160):  # tiles
        c.drawLine(x, 500, x, 760, S(C(255, 255, 255, 80), 3))
    blob(c, rrect(0, 740, W, 820, 6), (150, 100, 70))
    c.drawRect(skia.Rect(0, 820, W, H), P(C(120, 80, 55)))
    blob(c, rrect(1500, 300, 1780, 820, 20), (230, 235, 240), 1.05, 0.85)  # fridge
    c.drawLine(1520, 520, 1760, 520, S(C(180, 185, 190), 4))
    c.drawRect(skia.Rect(950, 620, 1250, 740), P(C(60, 60, 70)))  # stove
    for k in range(3):
        ph = (t * 0.6 + k / 3) % 1
        c.drawCircle(1080 + k * 40, 600 - ph * 160, 20 + 30 * ph, P(C(255, 255, 255, int(110 * (1 - ph))), MaskFilter=blur(10)))


def classroom(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(230, 215, 170), C(200, 180, 140)])))
    blob(c, rrect(260, 120, 1660, 520, 10), (50, 90, 70), 1.1, 0.8)
    c.drawRect(skia.Rect(240, 520, 1680, 545), P(C(160, 120, 80)))
    for k, s in enumerate(("2 + 2 = 4", "E = mc²", "HOMEWORK DUE")):  # low on the board, clear of the titles
        text(c, s, 460 + k * 500, 440 + (k % 2) * 50, 42, (240, 240, 230), 180, shadow=False, bold=False)
    c.drawRect(skia.Rect(0, 860, W, H), P(C(150, 110, 80)))


def cafeteria(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(210, 225, 230), C(170, 190, 200)])))
    for k in range(6):
        c.drawRect(skia.Rect(k * 340, 180, k * 340 + 200, 420), P(C(255, 255, 255, 120)))
    c.drawRect(skia.Rect(0, 830, W, H), P(C(140, 150, 160)))


def table(c, x0, x1, y):
    blob(c, rrect(x0, y, x1, y + 50, 10), (200, 170, 130))
    c.drawRect(skia.Rect(x0 + 30, y + 50, x0 + 60, y + 200), P(C(120, 100, 80)))
    c.drawRect(skia.Rect(x1 - 60, y + 50, x1 - 30, y + 200), P(C(120, 100, 80)))


def studio(c, t, col=(25, 20, 45)):
    c.drawPaint(P(Shader=rad(W / 2, H / 2, 1200, [C(*[v * 2 for v in col]), C(*col)])))
    for k in range(24):
        c.drawLine(k * 90, 0, k * 90, H, S(C(255, 255, 255, 12), 2))
    for k in range(13):
        c.drawLine(0, k * 90, W, k * 90, S(C(255, 255, 255, 12), 2))


def town_map(c, t, world=False, glow_on=1.0, red=0.0):
    c.drawPaint(P(C(25, 35, 55)))
    if not world:
        for k in range(14):
            c.drawLine(k * 150, 0, k * 150 + 80, H, S(C(60, 75, 105), 18))
        for k in range(9):
            c.drawLine(0, k * 130, W, k * 130 - 50, S(C(60, 75, 105), 18))
        r = random.Random(5)
        for i in range(60):
            x, y = r.uniform(0, W), r.uniform(0, H)
            c.drawRect(skia.Rect(x, y, x + 40, y + 30), P(C(45, 60, 85)))
    else:
        for (cx, cy, rx, ry) in ((400, 380, 260, 180), (520, 720, 140, 220), (930, 330, 140, 120), (1000, 640, 170, 230),
                                 (1350, 380, 360, 200), (1550, 760, 140, 100)):
            blob(c, oval(cx, cy, rx, ry), (50, 75, 95), 1.1, 0.8, outline=False)
        r = random.Random(9)
        for i in range(260):
            x, y = r.uniform(150, 1800), r.uniform(150, 950)
            if r.random() < 0.85:
                tw = 0.5 + 0.5 * math.sin(t * r.uniform(2, 5) + i)
                colr = (int(90 + 160 * red), int(220 - 160 * red), int(140 - 90 * red))
                c.drawCircle(x, y, 4 + 3 * tw, P(C(*colr, int(220 * glow_on))))
                glow(c, x, y, 18, colr, int(60 * glow_on * tw))


def street(c, t, night=False):
    sky = [(30, 30, 70), (70, 60, 120)] if night else [(120, 190, 240), (200, 230, 250)]
    c.drawPaint(P(Shader=lin((0, 0), (0, 700), [C(*sky[0]), C(*sky[1])])))
    blob(c, rrect(560, 300, 1360, 820, 6), (230, 200, 160), 1.05, 0.85)  # house
    roof = skia.Path()
    roof.moveTo(520, 310)
    roof.lineTo(960, 110)
    roof.lineTo(1400, 310)
    roof.close()
    blob(c, roof, (170, 70, 60), 1.2, 0.7)
    for x in (640, 1160):
        c.drawRect(skia.Rect(x, 420, x + 120, 540), P(C(255, 230, 150) if night else C(170, 220, 255)))
    c.drawRect(skia.Rect(900, 560, 1020, 820), P(C(120, 70, 50)))
    c.drawRect(skia.Rect(0, 820, W, H), P(C(90, 150, 80)))
    c.drawRect(skia.Rect(0, 900, W, H), P(C(110, 110, 115)))


def office(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(70, 80, 100), C(40, 45, 60)])))
    for k in range(5):
        c.drawRect(skia.Rect(140 + k * 360, 160, 380 + k * 360, 520), P(C(110, 140, 180, 120)))
    blob(c, rrect(560, 700, 1360, 790, 10), (120, 85, 55))
    c.drawRect(skia.Rect(0, 860, W, H), P(C(50, 50, 60)))


def mansion(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(220, 215, 205), C(180, 175, 165)])))
    for k in range(4):
        c.drawRect(skia.Rect(150 + k * 450, 100, 420 + k * 450, 640), P(C(190, 210, 230)))
        c.drawRect(skia.Rect(150 + k * 450, 100, 420 + k * 450, 640), S(C(240, 240, 240), 12))
    c.drawRect(skia.Rect(0, 820, W, H), P(Shader=lin((0, 820), (0, H), [C(210, 200, 185), C(160, 150, 135)])))
    for k in range(10):
        c.drawLine(k * 220, 820, k * 220 - 300, H, S(C(150, 140, 125), 3))


def lot(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(130, 200, 250), C(220, 240, 250)])))
    for k in range(10):  # bunting
        x = k * 200
        p = skia.Path()
        p.moveTo(x, 120)
        p.lineTo(x + 200, 120)
        p.lineTo(x + 100, 200)
        p.close()
        c.drawPath(p, P(C(*[(240, 70, 70), (250, 200, 60), (70, 150, 240)][k % 3])))
    c.drawRect(skia.Rect(0, 820, W, H), P(C(110, 110, 120)))


def sports_car(c, x, y, s):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = skia.Path()
    body.moveTo(-300, 0)
    body.lineTo(-300, -70)
    body.cubicTo(-200, -90, -120, -170, 0, -170)
    body.cubicTo(120, -170, 200, -110, 300, -80)
    body.lineTo(300, 0)
    body.close()
    blob(c, body, (230, 40, 40), 1.3, 0.65)
    c.drawRect(skia.Rect(-120, -150, 90, -95), P(C(120, 170, 220)))
    for wx in (-180, 180):
        c.drawCircle(wx, 0, 60, P(C(30, 30, 35)))
        c.drawCircle(wx, 0, 28, P(C(180, 180, 190)))
    c.restore()


def golf_cart(c, x, y, s, t):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    blob(c, rrect(-180, -110, 180, -10, 20), (245, 245, 240), 1.05, 0.85)
    c.drawLine(-150, -110, -150, -280, S(C(120, 120, 130), 10))
    c.drawLine(150, -110, 150, -280, S(C(120, 120, 130), 10))
    blob(c, rrect(-190, -300, 190, -270, 10), (60, 160, 90))
    for wx in (-120, 120):
        c.save()
        c.translate(wx, 0)
        c.rotate(-math.degrees(t * 5))
        c.drawCircle(0, 0, 40, P(C(30, 30, 35)))
        c.drawLine(-25, 0, 25, 0, S(C(160, 160, 170), 6))
        c.restore()
    c.restore()


def gaming_pc(c, x, y, s, t):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    blob(c, rrect(-90, -260, 90, 0, 12), (40, 40, 50), 1.5, 0.7)
    for k in range(4):
        hue = [(255, 60, 120), (60, 200, 255), (120, 255, 120), (255, 200, 60)][int(t * 4 + k) % 4]
        c.drawCircle(0, -200 + k * 50, 16, P(C(*hue)))
        glow(c, 0, -200 + k * 50, 50, hue, 120)
    c.restore()


def pizza_box(c, x, y, s):
    blob(c, rrect(x - 80 * s, y - 20 * s, x + 80 * s, y + 20 * s, 4), (230, 200, 150), 1.05, 0.85)
    c.drawCircle(x, y, 12 * s, P(C(220, 60, 50)))


def mic(c, x, y, s=1.0):
    c.drawLine(x, y, x, y + 120 * s, S(C(40, 40, 45), 10 * s))
    blob(c, oval(x, y - 10 * s, 26 * s, 34 * s), (60, 60, 70), 1.4, 0.7)


def news_ticker(c, t, msg):
    c.drawRect(skia.Rect(0, H - 150, W, H - 60), P(C(200, 30, 40, 235)))
    c.drawRect(skia.Rect(0, H - 150, 330, H - 60), P(C(255, 255, 255)))
    text(c, "BREAKING", 165, H - 88, 48, (200, 30, 40), shadow=False)
    text(c, msg, 380 + 0 * t, H - 88, 46, (255, 255, 255), align="left", shadow=False)


def cat_drummer(c, x, y, s, t):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    for dx, r in ((-150, 70), (150, 70)):
        c.drawCircle(dx, -80, r, P(C(200, 40, 50)))
        c.drawCircle(dx, -80, r * 0.8, P(C(240, 240, 240)))
    blob(c, oval(0, -40, 110, 90), (200, 40, 50), 1.2, 0.7)
    blob(c, oval(0, -40, 90, 70), (245, 245, 240), 1.05, 0.85)
    blob(c, oval(0, -230, 90, 110), (240, 150, 60), 1.2, 0.7)  # cat body
    blob(c, oval(0, -340, 70, 60), (240, 150, 60), 1.2, 0.7)  # head
    for side in (-1, 1):
        ear = skia.Path()
        ear.moveTo(side * 30, -385)
        ear.lineTo(side * 60, -440)
        ear.lineTo(side * 70, -370)
        ear.close()
        blob(c, ear, (240, 150, 60), 1.2, 0.7)
        c.drawCircle(side * 24, -345, 10, P(C(30, 30, 30)))
        hit = math.sin(t * 14 + side)
        c.drawLine(side * 60, -250, side * (120 + 30 * hit), -150 - 40 * hit, S(C(140, 90, 40), 10))
    c.restore()


# ---------- shot helpers ----------

class Shot:
    def __init__(self, k):
        self.k = k
        self.d = ST.end[k] - ST.start[k]

    def at(self, word, n=1, lead=0.08):
        return ST.at(self.k, word, n, lead)


def safe_hands(hands):
    """Hand guard: a hand that would land on the face (centre (0,-332), ~110 px) is pushed out to the side."""
    out = []
    for side, (hx, hy) in zip((-1, 1), hands):
        ax, ay = side * 60 + hx, -235 + hy
        if (ax / 118) ** 2 + ((ay + 332) / 125) ** 2 < 1:  # would cover the face: rest the hand on the chest instead
            ax = side * 70
            ay = -175
            hx, hy = ax - side * 60, ay + 235
        out.append((hx, hy))
    return out


def stand(c, who, x, y, s, t, **pose):
    if "hands" in pose:
        pose["hands"] = safe_hands(pose["hands"])
    pose.setdefault("blink", blink(t, x * 0.01))
    pose.setdefault("tilt", 2 * math.sin(t * 1.6 + x * 0.003))
    person(c, x, y, s, who, pose, t)


# ---------- the 74 shots ----------

def s0(c, t, Q):  # What if every time someone thought about you...
    bedroom(c, t, night=True)
    stand(c, YOU, 520, 1000, 1.45, t, eyes="wide", mouth="O", brows="up", hands=[(60, 40), (-60, 40)], look=(0.6, -0.3))
    buzz = 1.0 if (t % 0.9) < 0.35 else 0.0
    lines = [("+$1", "Somebody thought of you")] * min(5, int(t * 1.2) + 1)
    phone(c, 1180, 720, 0.95, t, screen_bank(lines, t), buzz=buzz, glow_col=GREEN)  # below the title lines
    for j in range(6):
        thought(c, 200 + j * 280, 1100, 1180, 660, t, 0.6 + j * 1.2, 1.0)
    pop_text(c, "WHAT IF...", W / 2, 190, 120, t, 0.05, GOLD, 12)
    pop_text(c, "every thought about you = $1", W / 2, 330, 64, t, Q.at("got"), (255, 255, 255), 9)


def s1(c, t, Q):  # millionaire... begging for it to stop
    studio(c, t)
    bill_rain(c, t, 0.0, 50)
    mil = Q.at("millionaire")
    beg = Q.at("begging")
    pose = dict(eyes="closed" if t > beg else "wide", mouth="laugh" if t < beg else "frown", brows="up" if t < beg else "sad",
                hands=[(-80, -200), (80, -200)] if t < beg else [(40, -110), (-40, -110)])
    stand(c, YOU, 960, 1050, 1.5, t, **pose)
    money_pile(c, 960, 1060, 2.0, t, 40)
    slam_text(c, "MILLIONAIRE", W / 2, 230, 150, t, mil, GOLD)
    if t > beg:
        pop_text(c, "...make it STOP!", W / 2, 380, 90, t, beg, RED, 10)


def s2(c, t, Q):  # Let's find out why.
    studio(c, t, (40, 15, 30))
    sparkle_ring(c, W / 2, H / 2, 420, t, 12)
    slam_text(c, "$1 PER THOUGHT", W / 2, H / 2 - 40, 160, t, 0.1, GREEN)
    pop_text(c, "a week you'll never forget", W / 2, H / 2 + 130, 60, t, 0.6, (255, 255, 255), 8)


def s3(c, t, Q):  # Monday... phone buzzes... Plus one dollar...
    if t < 1.6:
        chapter_card(c, t, "MONDAY")
        return
    bedroom(c, t)
    buzz = Q.at("buzzes")
    wake = ease((t - buzz) / 0.4)
    stand(c, YOU, 640, 1020, 1.4, t, eyes="open" if wake > 0.5 else "closed", mouth="O" if wake > 0.5 else "smile", brows="up",
          hands=[(-30, 150), (90, -60 * wake)], look=(1, -0.2))
    n = sum(1 for ts, a in ST.plus_events() if ST.start[Q.k] + 1.6 <= ts <= ST.start[Q.k] + t)
    phone(c, 1180, 560, 1.0, t, screen_bank([("+$1", "Somebody thought of you")] * max(1, n), t), buzz=1.0 if (t - buzz) % 1.2 < 0.3 and t > buzz else 0,
          glow_col=GREEN)


def s4(c, t, Q):  # no name... "Somebody thought of you."
    studio(c, t, (15, 30, 25))
    phone(c, W / 2, 660, 1.3, t, screen_bank([("+$1", "From: ???")], t), glow_col=GREEN)
    pop_text(c, "\"Somebody thought of you.\"", W / 2, 110, 76, t, Q.at("somebody"), (255, 255, 255), 9)
    q = pop(t, Q.at("name"))
    if q > 0:
        text(c, "?", 1480, 420, 260 * q, (255, 220, 120), stroke=12)
        text(c, "?", 440, 520, 200 * q, (255, 220, 120), stroke=12)


def s5(c, t, Q):  # 6:42, mom making breakfast
    kitchen(c, t)
    clock = Q.at("six")
    pop_text(c, "6:42 AM", 420, 120, 110, t, clock, (255, 255, 255), 12)
    stir = math.sin(t * 4)
    mx, my, ms = 1050, 1030, 1.4
    stand(c, MOM, mx, my, ms, t, eyes="open", mouth="smile", brows="flat", hands=[(110 + 15 * stir, 40), (60, 70)], look=(-0.6, 0))
    pl = Q.at("plus")
    thought(c, mx, my - 332 * ms - 120, 1700, 160, t, pl - 0.6, 0.8)
    if t > Q.at("wondering"):
        c.drawCircle(mx + 160, my - 640, 80, P(C(255, 255, 255, 230)))
        text(c, "late?", mx + 160, my - 625, 44, (60, 60, 70), shadow=False)


def s6(c, t, Q):  # best friend saves a seat... teacher... plus three
    classroom(c, t)
    seat = Q.at("saves")
    fx, fy, fs = 520, 1030, 1.25
    stand(c, FRIEND, fx, fy, fs, t, eyes="open", mouth="grin", brows="up", hands=[(-20, 150), (150 * ease((t - seat) / 0.4), 60)], look=(1, 0))
    tx_, ty_, ts_ = 1420, 1030, 1.35
    folder = Q.at("folder")
    stand(c, TEACHER, tx_, ty_, ts_, t, eyes="squint" if t > folder else "open", mouth="frown" if t > folder else "smile",
          brows="angry" if t > folder else "flat", hands=[(-120, 30), (30, 150)], look=(-1, 0.4))
    if t > folder:
        blob(c, rrect(tx_ - 340, ty_ - 420, tx_ - 160, ty_ - 300, 8), (240, 200, 80))
        text(c, "EMPTY", tx_ - 250, ty_ - 348, 34, (150, 40, 40), shadow=False)
    p1, p2, p3 = Q.at("plus", 1), Q.at("plus", 2), Q.at("plus", 3)
    thought(c, fx, fy - 560, 1700, 160, t, p1 - 0.6, 0.8)
    thought(c, tx_, ty_ - 600, 1700, 160, t, p2 - 0.6, 0.8)
    for j in range(3):
        thought(c, tx_, ty_ - 600, 1700, 160, t, p3 - 0.6 + j * 0.12, 0.8, "$1")


def s7(c, t, Q):  # By lunch, $18
    cafeteria(c, t)
    table(c, 500, 1420, 760)
    stand(c, YOU, 960, 1060, 1.3, t, eyes="open", mouth="grin", brows="smug", hands=[(60, -40), (-60, 60)], look=(0, -0.3))
    slam_text(c, "$18", W / 2, 230, 200, t, Q.at("eighteen"), GREEN)
    pop_text(c, "for doing NOTHING", W / 2, 400, 70, t, Q.at("nothing"), (255, 255, 255), 9)


def s8(c, t, Q):  # crush two tables away... zero dollars
    cafeteria(c, t)
    table(c, 80, 760, 780)
    table(c, 1160, 1860, 780)
    stand(c, YOU, 420, 1060, 1.25, t, eyes="wide" if t > Q.at("crush") else "open", mouth="smile", brows="up",
          hands=[(30, 60), (-30, 60)], look=(1, 0))
    laugh = abs(math.sin(t * 6)) * 6
    stand(c, CRUSH, 1500, 1060 - laugh, 1.25, t, eyes="closed", mouth="laugh", brows="up", hands=[(-30, 150), (30, 150)], look=(-1, 0))
    stand(c, FRIEND, 1760, 1060, 1.1, t, eyes="closed", mouth="laugh", brows="up", hands=[(-30, 150), (30, 150)], look=(-1, 0))
    if t > Q.at("crush"):
        for j in range(3):
            heart(c, 700 + j * 60, 420 - ((t * 60 + j * 30) % 90), 0.7, 220)
    z = Q.at("zero")
    if t > z - 0.3:
        phone(c, 960, 520, 0.8, t, screen_bank([("$0", "from: your crush")], t, "Thought Bank"))
        slam_text(c, "$0", W / 2, 150, 150, t, z, RED)


def s9(c, t, Q):  # glance... plus one... ketchup stain
    cafeteria(c, t)
    gl = Q.at("glance")
    stand(c, CRUSH, 1400, 1060, 1.35, t, eyes="open", mouth="O" if t > gl else "smile", brows="up", hands=[(-30, 150), (30, 150)],
          look=(-1, 0.6) if t > gl else (0, 0))
    jump = Q.at("heart")
    hop = max(0.0, math.sin(math.pi * min(1, (t - jump) / 0.5))) * 60 if t > jump else 0
    ket = Q.at("ketchup")
    stand(c, YOU, 560, 1060 - hop, 1.4, t, eyes="wide" if t < ket else "squint", mouth="grin" if t < ket else "frown",
          brows="up" if t < ket else "sad", hands=[(40, -100), (-40, 60)] if t < ket else [(40, 90), (-40, 90)], look=(1, 0) if t < ket else (0, 1))
    if t > Q.at("plus") - 0.6:
        thought(c, 1400, 470, 760, 520, t, Q.at("plus") - 0.6, 0.7)
    if t > jump and t < ket:
        for j in range(4):
            heart(c, 560 + (j - 1.5) * 70, 420 - ((t * 80 + j * 25) % 120), 0.7, 230)
    if t > ket:  # the ketchup stain
        k = pop(t, ket)
        c.drawCircle(560 - 10, 1060 - 1.4 * 180, 46 * k, P(C(210, 30, 30)))
        c.drawCircle(560 + 30, 1060 - 1.4 * 160, 26 * k, P(C(210, 30, 30)))
        pop_text(c, "KETCHUP.", W / 2, 180, 120, t, ket + 0.2, RED, 12)


def s10(c, t, Q):  # running tests
    bedroom(c, t)
    stand(c, YOU, 520, 1040, 1.35, t, eyes="squint", mouth="grin", brows="angry", hands=[(80, 20), (-40, 60)], look=(1, 0))
    blob(c, rrect(980, 300, 1620, 760, 12), (250, 250, 245), 1.05, 0.85)  # notepad on the wall
    text(c, "EXPERIMENTS", 1300, 380, 56, (60, 60, 120), shadow=False)
    for j in range(4):
        if t > 0.6 + j * 0.7:
            c.drawLine(1040, 450 + j * 80, 1040 + 460 * min(1, (t - 0.6 - j * 0.7) / 0.5), 450 + j * 80, S(C(80, 80, 140), 6))
    pop_text(c, "THE RULES", W / 2, 140, 110, t, 0.2, GOLD, 12)


def rule_card(c, t, n, title, col=GOLD):
    pop_text(c, f"RULE #{n}", 330, 130, 90, t, 0.05, col, 10)
    pop_text(c, title, W / 2 + 160, 130, 64, t, 0.35, (255, 255, 255), 8)


def s11(c, t, Q):  # rule 1: brother furious about cereal
    kitchen(c, t)
    rule_card(c, t, 1, "mean thoughts pay too")
    fur = Q.at("furious")
    shake = math.sin(t * 40) * 6 if t > fur else 0
    bx, by, bs = 1150 + shake, 1040, 1.05
    stand(c, BRO, bx, by, bs, t, eyes="squint" if t > fur else "open", mouth="frown" if t > fur else "O", brows="angry", hands=[(-60, -60), (60, -60)],
          look=(-1, 0))
    blob(c, rrect(1300, 640, 1420, 740, 10), (240, 200, 60))  # empty cereal box
    stand(c, YOU, 560, 1040, 1.3, t, eyes="open", mouth="grin", brows="smug", hands=[(60, 40), (-40, 60)], look=(1, 0))
    if t > fur:
        for j in range(3):
            ph = ((t - fur) * 1.6 + j / 3) % 1
            c.drawCircle(bx + (j - 1) * 50, by - 560 - ph * 140, 18 + 22 * ph, P(C(240, 240, 245, int(180 * (1 - ph))), MaskFilter=blur(6)))
    for j in range(3):
        thought(c, bx, by - 520, 1700, 160, t, Q.at("plus", j + 1) - 0.6, 0.7)


def s12(c, t, Q):  # rule 2: counts every time; ten times = ten dollars
    studio(c, t)
    rule_card(c, t, 2, "every single time counts")
    ten = Q.at("ten", 1)
    for j in range(10):
        k = pop(t, ten + j * 0.09)
        if k > 0:
            c.save()
            c.translate(330 + j * 140, 600)
            c.scale(k, k)
            c.drawCircle(0, 0, 58, P(C(255, 255, 255)))
            c.drawCircle(0, 0, 58, S(C(40, 40, 50), 4))
            text(c, "$1", 0, 16, 44, (30, 150, 80), shadow=False)
            c.restore()
    slam_text(c, "= $10", W / 2, 860, 130, t, Q.at("ten", 2), GREEN)


def s13(c, t, Q):  # rule 3: 2:13 AM
    bedroom(c, t, night=True)
    rule_card(c, t, 3, "it works at night too", BLUE)
    pop_text(c, "2:13 AM", 400, 430, 110, t, Q.at("two"), (200, 220, 255), 12)
    lit = Q.at("lights")
    stand(c, YOU, 1500, 1000, 1.25, t, eyes="closed" if t < lit else "wide", mouth="smile" if t < lit else "O", brows="flat" if t < lit else "up",
          hands=[(-30, 150), (30, 150)], look=(-1, 0))
    phone(c, 1040, 700, 0.7, t, screen_bank([("+$1", "someone, somewhere")], t) if t > lit else None, buzz=1.0 if lit < t < lit + 0.6 else 0,
          glow_col=GREEN if t > lit else None)
    if t > Q.at("lying"):
        pop_text(c, "who is awake thinking about you?", W / 2, 1000, 50, t, Q.at("lying"), (255, 255, 255), 6)


def s14(c, t, Q):  # You decide not to ask who.
    bedroom(c, t, night=True)
    k = ease(t / 0.8)
    stand(c, YOU, 960, 1040, 1.4, t, eyes="squint", mouth="frown", brows="sad", hands=[(-30, 150), (30, 150)], look=(0.8 * k, 0), tilt=-6 * k)
    pop_text(c, "nope.", W / 2, 200, 120, t, 0.4, (255, 255, 255), 12)


def s15(c, t, Q):  # rule 4: mirror
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(200, 230, 235), C(160, 195, 205)])))
    for k in range(12):
        c.drawLine(k * 170, 0, k * 170, H, S(C(255, 255, 255, 60), 3))
    blob(c, rrect(960, 150, 1560, 860, 40), (230, 240, 245), 1.05, 0.85)
    c.drawRoundRect(skia.Rect(990, 180, 1530, 830), 30, 30, P(C(170, 210, 230)))
    rule_card(c, t, 4, "you can't pay yourself")
    strain = math.sin(t * 30) * 3 if t > Q.at("hard") else 0
    stand(c, YOU, 640 + strain, 1040, 1.35, t, eyes="squint", mouth="grin", brows="angry", hands=[(40, -110), (-40, -110)], look=(1, 0))
    c.save()  # reflection
    c.clipRect(skia.Rect(990, 180, 1530, 830))
    stand(c, YOU, 1260 - strain, 1040, 1.2, t, eyes="squint", mouth="grin", brows="angry", hands=[(40, -110), (-40, -110)], look=(-1, 0))
    c.restore()
    if t > Q.at("hair"):
        for j in range(4):
            sparkle(c, 560 + j * 60, 520 - (j % 2) * 40, 10, 220)
    z = Q.at("zero")
    if t > z - 0.2:
        slam_text(c, "$0", 960, 520, 140, t, z, RED)


def s16(c, t, Q):  # end of day one: $47, most from mom
    studio(c, t, (25, 40, 30))
    slam_text(c, "$47", W / 2, 330, 220, t, Q.at("forty"), GREEN)
    mom = Q.at("mom")
    if t > mom - 0.2:
        k = pop(t, mom)
        c.save()
        c.translate(960, 950)
        c.scale(k, k)
        stand(c, MOM, 0, 0, 1.0, t, eyes="closed", mouth="grin", brows="up", hands=[(-30, 150), (30, 150)])
        c.restore()
        pop_text(c, "mostly from MOM", W / 2, 480, 70, t, mom, PINK, 9)


def s17(c, t, Q):  # can't sleep, builds an app with a map
    bedroom(c, t, night=True)
    blob(c, rrect(260, 720, 900, 790, 8), (140, 100, 70))  # desk
    c.drawRect(skia.Rect(320, 790, 350, 1000), P(C(100, 70, 50)))
    c.drawRect(skia.Rect(810, 790, 840, 1000), P(C(100, 70, 50)))
    blob(c, rrect(380, 470, 780, 720, 12), (40, 40, 50), 1.4, 0.7)  # laptop screen
    code = int(t * 6)
    for j in range(min(7, code)):
        c.drawLine(410, 500 + j * 30, 410 + 60 + (j * 73) % 280, 500 + j * 30, S(C(90, 230, 140), 6))
    glow(c, 580, 600, 300, (90, 230, 140), 60)
    stand(c, YOU, 1100, 1040, 1.3, t, eyes="open", mouth="grin", brows="angry", hands=[(-150, -20), (-110, 0)], look=(-1, 0.3))
    m = Q.at("map")
    if t > m - 0.2:
        phone(c, 1560, 560, 0.85, t, lambda cc, w, h: (cc.save(), cc.scale(w / W, h / H), town_map(cc, t), cc.restore()), glow_col=GREEN)
        pop_text(c, "THOUGHT MAP", W / 2, 150, 100, t, m, GREEN, 12)


def s18(c, t, Q):  # house covered in dots; grandma's big glowing dot
    town_map(c, t)
    home = (760, 560)
    for j in range(40):
        a, r = j * 2.4, 20 + (j * 37) % 90
        k = pop(t, 0.2 + j * 0.03)
        if k > 0:
            c.drawCircle(home[0] + math.cos(a) * r, home[1] + math.sin(a) * r * 0.7, 8 * k, P(C(90, 230, 140)))
    text(c, "HOME", home[0], home[1] + 150, 44, (255, 255, 255))
    sch = Q.at("school")
    for j in range(6):
        k = pop(t, sch + j * 0.06)
        if k > 0:
            c.drawCircle(1100 + (j % 3) * 30, 360 + (j // 3) * 30, 8 * k, P(C(90, 230, 140)))
    if t > sch:
        text(c, "SCHOOL", 1130, 470, 40, (255, 255, 255))
    gm = Q.at("grandma")
    if t > gm:
        gx, gy = 1640, 840
        pulse = 1 + 0.25 * math.sin(t * 4)
        glow(c, gx, gy, 220 * pulse, (255, 200, 120), 200)
        c.drawCircle(gx, gy, 34 * pulse, P(C(255, 220, 140)))
        text(c, "GRANDMA", gx, gy + 110, 44, (255, 230, 170))
        if t > Q.at("night"):
            c.save()
            c.translate(gx - 260, gy + 40)
            c.scale(0.7, 0.7)
            stand(c, GRANDMA, 0, 0, 1.0, t, eyes="closed", mouth="smile", brows="flat", hands=[(40, 60), (-40, 60)])
            c.restore()
            heart(c, gx - 260, gy - 340, 0.8, 230)


def s19(c, t, Q):  # let's do some math
    studio(c, t, (20, 25, 50))
    slam_text(c, "LET'S DO THE MATH", W / 2, H / 2, 140, t, 0.05, GOLD)
    for j, sym in enumerate(("+", "×", "=", "$", "÷")):
        a = t * 0.8 + j * 1.25
        text(c, sym, W / 2 + math.cos(a) * 700, H / 2 + math.sin(a) * 330, 90, (255, 255, 255), 150)


def s20(c, t, Q):  # normal person: 50/day = $18,000/yr
    studio(c, t, (20, 25, 50))
    x0 = 300
    fam = Q.at("family")
    for j, (look, at) in enumerate(((MOM, fam), (FRIEND, Q.at("friends")), (TEACHER, Q.at("teachers")), (BRO, Q.at("kid")))):
        k = pop(t, at)
        if k > 0:
            c.save()
            c.translate(x0 + j * 200, 1000)
            c.scale(0.75 * k, 0.75 * k)
            stand(c, look, 0, 0, 1.0, t, eyes="open", mouth="smile", brows="flat", hands=[(-30, 150), (30, 150)])
            c.restore()
    stand(c, YOU, 1500, 1020, 1.25, t, eyes="open", mouth="grin", brows="up", hands=[(-30, 150), (30, 150)], look=(-1, 0))
    pop_text(c, "~50 thoughts a day", 620, 200, 70, t, Q.at("fifty", 1), (255, 255, 255), 8)
    slam_text(c, "$50 / DAY", 620, 330, 100, t, Q.at("fifty", 2), GREEN)
    slam_text(c, "$18,000 / YEAR", W / 2, 520, 120, t, Q.at("eighteen"), GOLD)


def s21(c, t, Q):  # what about someone famous?
    studio(c, t, (50, 20, 60))
    for j in range(10):
        a = j / 10 * 2 * math.pi + t
        c.drawCircle(W / 2 + math.cos(a) * 520, 560 + math.sin(a) * 300, 14, P(C(255, 255, 255, 180)))
    stand(c, SINGER, 960, 1020, 1.35, t, eyes="open", mouth="grin", brows="smug", hands=[(-90, -180), (90, -40)])
    pop_text(c, "someone FAMOUS?", W / 2, 160, 110, t, Q.at("famous"), PINK, 12)


def s22(c, t, Q):  # YouTuber 10M fans -> millions a day
    studio(c, t, (40, 15, 25))
    blob(c, rrect(260, 300, 1000, 760, 30), (230, 40, 50), 1.2, 0.8)  # big play button
    tri = skia.Path()
    tri.moveTo(560, 420)
    tri.lineTo(560, 640)
    tri.lineTo(760, 530)
    tri.close()
    c.drawPath(tri, P(C(255, 255, 255)))
    bill_rain(c, t, Q.at("millions", 2))
    pop_text(c, "10 MILLION FANS", 640, 230, 80, t, Q.at("ten"), (255, 255, 255), 9)
    slam_text(c, "$ MILLIONS", 1400, 480, 120, t, Q.at("millions", 2), GREEN)
    pop_text(c, "EVERY. SINGLE. DAY.", 1400, 650, 70, t, Q.at("every", 2), GOLD, 9)


def s23(c, t, Q):  # biggest celebrities -> richest people ever in < a week
    studio(c, t, (15, 15, 30))
    for j in range(18):
        a = j * 0.9 + t * 0.4
        r = 200 + (j * 53) % 500
        c.drawCircle(W / 2 + math.cos(a) * r, 540 + math.sin(a) * r * 0.5, 6, P(C(255, 230, 150, 200)))
    slam_text(c, "HUNDREDS OF MILLIONS", W / 2, 360, 110, t, Q.at("hundreds"), GOLD)
    pop_text(c, "richest people who ever lived", W / 2, 560, 76, t, Q.at("richest"), (255, 255, 255), 9)
    pop_text(c, "in less than a WEEK", W / 2, 700, 76, t, Q.at("week"), GREEN, 9)


def s24(c, t, Q):  # Shakespeare still getting paid
    classroom(c, t)
    sh = Q.at("shakespeare")
    k = pop(t, sh)
    if k > 0:
        c.save()
        c.translate(960, 760)
        c.scale(k, k)
        blob(c, rrect(-150, 40, 150, 220, 20), (60, 55, 70), 1.3, 0.7)  # doublet
        for j in range(9):  # ruff collar
            blob(c, oval(-120 + j * 30, 40, 26, 22), (250, 250, 245), 1.05, 0.85)
        for side in (-1, 1):  # long hair at the sides, bald on top
            blob(c, oval(side * 120, -150, 50, 90), (110, 70, 40), 1.2, 0.7)
        blob(c, oval(0, -170, 125, 150), (240, 210, 180), 1.1, 0.8)
        beard = skia.Path()
        beard.moveTo(-70, -90)
        beard.cubicTo(-60, -10, -20, 20, 0, 30)
        beard.cubicTo(20, 20, 60, -10, 70, -90)
        beard.cubicTo(30, -70, -30, -70, -70, -90)
        blob(c, beard, (110, 70, 40), 1.2, 0.7)
        for side in (-1, 1):
            c.drawCircle(side * 45, -190, 13, P(C(30, 30, 30)))
            c.drawLine(side * 20, -105, side * 60, -112, S(C(110, 70, 40), 9))  # moustache
        c.drawArc(skia.Rect(-30, -95, 30, -60), 20, 140, False, S(C(80, 40, 30), 6))
        c.restore()
        pop_text(c, "SHAKESPEARE", W / 2, 160, 100, t, sh, GOLD, 12)
    for j in range(5):
        thought(c, 150 + j * 400, 1100, 960, 600, t, Q.at("students") + j * 0.25, 0.9)
    pop_text(c, "STILL GETTING PAID", W / 2, 1000, 80, t, Q.at("paid"), GREEN, 9)


def s25(c, t, Q):  # money isn't in being liked; it's in being noticed
    studio(c, t, (30, 20, 40))
    stand(c, YOU, 960, 1050, 1.4, t, eyes="wide", mouth="grin", brows="smug", hands=[(40, -120), (-60, 60)], look=(0, -0.4))
    lb = Q.at("liked")
    pop_text(c, "being LIKED", 520, 300, 80, t, lb, (200, 200, 210), 9)
    if t > lb + 0.6:
        c.drawLine(300, 280, 740, 280, S(C(240, 70, 70), 12))
    slam_text(c, "being NOTICED", 1400, 300, 100, t, Q.at("noticed"), GOLD)
    if t > Q.at("clicks"):
        lightbulb_ = pop(t, Q.at("clicks"))
        glow(c, 960, 280, 200 * lightbulb_, (255, 240, 150), 160)
        c.drawCircle(960, 280, 60 * lightbulb_, P(C(255, 240, 150)))


def s26(c, t, Q):  # Tuesday. You make a plan.
    if t < 1.3:
        chapter_card(c, t, "TUESDAY")
        return
    bedroom(c, t)
    stand(c, YOU_BLUE if False else YOU, 640, 1040, 1.35, t, eyes="squint", mouth="grin", brows="angry", hands=[(80, -40), (-30, 150)], look=(1, 0))
    pop_text(c, "THE PLAN", 1300, 300, 120, t, 1.35, GOLD, 12)


def s27(c, t, Q):  # dye hair bright blue: +$60
    classroom(c, t)
    stare = Q.at("stare")
    for j, x in enumerate((180, 420, 1500, 1740)):
        stand(c, [FRIEND, CRUSH, BRO, REPORTER][j], x, 1060, 0.95, t, eyes="wide" if t > stare else "open", mouth="O" if t > stare else "smile",
              brows="up", hands=[(-30, 150), (30, 150)], look=(1 if x < 960 else -1, -0.2))
    dye = Q.at("dye")
    look = YOU_BLUE if t > dye else YOU
    stand(c, look, 960, 1060, 1.4, t, eyes="open", mouth="grin", brows="smug", hands=[(60, -150), (-30, 150)], look=(0, -0.2))
    if dye < t < dye + 0.6:
        sparkle_ring(c, 960, 520, 180, t, 10, col=(120, 180, 255))
    pop_text(c, "BRIGHT BLUE", W / 2, 160, 100, t, Q.at("blue"), BLUE, 12)


def s28(c, t, Q):  # sing on the lunch table: +$300, detention, principal +1
    cafeteria(c, t)
    table(c, 560, 1360, 740)
    sing = Q.at("sing")
    det = Q.at("detention")
    x, y = 960, 750
    stand(c, YOU_BLUE, x, y + 6 * math.sin(t * 6), 1.15, t, eyes="closed", mouth="laugh" if t < det else "frown", brows="up" if t < det else "sad",
          hands=[(-110, -150), (110, -150)] if t < det else [(-30, 150), (30, 150)])
    if sing < t < det:
        for j in range(5):
            u = ((t - sing) * 0.8 + j * 0.2) % 1
            nx, ny, na = x + 200 + 300 * u * (1 if j % 2 else -1) * 0.6, 350 - 200 * u, int(255 * (1 - u))
            c.drawOval(skia.Rect(nx - 22, ny - 14, nx + 14, ny + 14), P(C(255, 255, 255, na)))
            c.drawLine(nx + 12, ny, nx + 12, ny - 70, S(C(255, 255, 255, na), 7))
            c.drawLine(nx + 12, ny - 70, nx + 40, ny - 55, S(C(255, 255, 255, na), 7))
    if t > det:
        k = pop(t, det)
        stand(c, PRINCIPAL, 1600, 1060, 1.3 * k if k > 0 else 0.01, t, eyes="squint", mouth="frown", brows="angry", hands=[(-140, -40), (30, 150)],
              look=(-1, 0))
        pop_text(c, "DETENTION", 1600, 140, 90, t, det, RED, 10)
        thought(c, 1600, 560, 1700, 160, t, Q.at("plus", 2) - 0.6, 0.7)


def s29(c, t, Q):  # not enough... need the whole internet
    studio(c, t, (15, 25, 50))
    glob = pop(t, Q.at("internet"))
    town_map(c, t, world=True, glow_on=0.4 * glob) if glob > 0 else None
    stand(c, YOU_BLUE, 480, 1050, 1.3, t, eyes="squint", mouth="grin", brows="angry", hands=[(120, -60), (-30, 150)], look=(1, -0.3))
    slam_text(c, "THE WHOLE INTERNET", 1200, 220, 100, t, Q.at("internet"), GOLD)


def s30(c, t, Q):  # 1000 rubber ducks, jump in, "Why not?"
    bedroom(c, t)
    fill = ease((t - Q.at("thousand")) / 1.2)
    r = random.Random(2)
    n = int(160 * fill)
    for i in range(n):
        duck(c, r.uniform(80, 1840), 1040 - r.uniform(0, 330) * fill, 0.55, t + i, r.uniform(-20, 20))
    jump = Q.at("jump")
    if t < jump:
        stand(c, YOU_BLUE, 960, 1000, 1.25, t, eyes="wide", mouth="grin", brows="up", hands=[(-80, -150), (80, -150)])
    else:
        k = min(1, (t - jump) / 0.6)
        y = 1000 - 300 * math.sin(math.pi * k) + 250 * k
        stand(c, YOU_BLUE, 960, y, 1.25, t, eyes="closed", mouth="laugh", brows="up", hands=[(-120, -170), (120, -170)])
        if k >= 1:
            for i in range(30):
                duck(c, 760 + r.uniform(0, 400), 980 + r.uniform(-60, 60), 0.6, t + i, r.uniform(-30, 30))
        if 0.6 < k < 1 or (t - jump) < 1.2:
            for i in range(10):
                a = i / 10 * math.pi
                u = min(1, (t - jump - 0.5) / 0.6) if t > jump + 0.5 else 0
                duck(c, 960 + math.cos(a) * 300 * u, 900 - math.sin(a) * 260 * u + 300 * u * u, 0.5, t, 120 * u)
    pop_text(c, "1,000 RUBBER DUCKS", W / 2, 140, 100, t, Q.at("thousand"), GOLD, 12)
    if t > Q.at("why"):
        pop_text(c, "\"Why not?\"", W / 2, 280, 90, t, Q.at("why"), (255, 255, 255), 10)


def s31(c, t, Q):  # 12 views, +$12
    studio(c, t, (20, 20, 30))
    phone(c, W / 2, 660, 1.3, t, screen_views("12 views", t))
    pop_text(c, "12 views...", W / 2, 120, 90, t, Q.at("twelve"), (200, 200, 210), 10)


def s32(c, t, Q):  # a huge account shares it
    studio(c, t, (40, 20, 60))
    sh = Q.at("shares")
    k = pop(t, sh)
    phone(c, 760, 560, 1.2, t, screen_views("12 views", t))
    if k > 0:
        c.save()
        c.translate(1300, 520)
        c.scale(k, k)
        c.drawCircle(0, 0, 150, P(C(60, 140, 240)))
        ck = skia.Path()
        ck.moveTo(-70, 0)
        ck.lineTo(-20, 55)
        ck.lineTo(80, -60)
        c.drawPath(ck, S(C(255, 255, 255), 30))
        c.restore()
        pop_text(c, "SHARED by a HUGE account", W / 2, 140, 80, t, sh, BLUE, 10)
        for j in range(8):
            a = j / 8 * 2 * math.pi
            r = 200 + 160 * min(1, (t - sh) / 0.6)
            c.drawLine(1300 + math.cos(a) * 170, 520 + math.sin(a) * 170, 1300 + math.cos(a) * r, 520 + math.sin(a) * r, S(C(120, 190, 255), 8))


def s33(c, t, Q):  # +100, +1000, +10000, phone in the fridge
    kitchen(c, t)
    fr = Q.at("fridge")
    hot = min(1, t / max(0.1, fr))
    if t < fr:
        phone(c, 900, 560, 1.15, t, screen_views(f"{int(1000 * 10 ** (3 * hot)):,} views", t), buzz=1.0, glow_col=(255, int(200 - 150 * hot), 60))
        for j in range(4):
            ph = (t * 1.3 + j / 4) % 1
            c.drawCircle(820 + j * 50, 230 - ph * 160, 20 + 30 * ph, P(C(255, 255, 255, int(150 * (1 - ph))), MaskFilter=blur(8)))
    else:  # in the fridge, open door, frost
        blob(c, rrect(1500, 300, 1780, 820, 20), (230, 235, 240), 1.05, 0.85)
        c.drawRect(skia.Rect(1520, 320, 1760, 800), P(C(200, 230, 255)))
        phone(c, 1640, 560, 0.5, t, screen_views("1,000,000+", t), buzz=0.5)
        for j in range(6):
            sparkle(c, 1540 + j * 40, 360 + (j * 67) % 400, 8, 200, (220, 240, 255))
        pop_text(c, "in the FRIDGE", 700, 300, 110, t, fr, BLUE, 12)


def s34(c, t, Q):  # by midnight, 2 million people
    town_map(c, t, world=True, glow_on=min(1, t / 2))
    slam_text(c, "2,000,000 VIEWS", W / 2, 160, 120, t, Q.at("two"), GOLD)
    for j in range(8):
        thought(c, 200 + j * 220, 900 - (j % 2) * 300, W / 2, 500, t, Q.at("every") + j * 0.1, 0.8)


def s35(c, t, Q):  # bed with 2 million, wake with 5
    night = t < Q.at("wake")
    bedroom(c, t, night=night)
    stand(c, YOU_BLUE, 900, 1040, 1.35, t, eyes="closed" if night else "wide", mouth="smile" if night else "O", brows="flat" if night else "up",
          hands=[(-30, 150), (30, 150)] if night else [(-90, -170), (90, -170)])
    slam_text(c, "$2,000,000", W / 2, 200, 150, t, Q.at("two"), GREEN)
    if not night:
        slam_text(c, "$5,000,000", W / 2, 380, 150, t, Q.at("five"), GOLD)


def s36(c, t, Q):  # Wednesday is a blur
    chapter_card(c, t, "WEDNESDAY", "is a blur...")


def s37(c, t, Q):  # pay off house, gaming PC, pizzas
    street(c, t)
    h, pc, pz = Q.at("house"), Q.at("computer"), Q.at("pizza")
    if t > h:
        pop_text(c, "PAID OFF!", 960, 220, 100, t, h, GREEN, 12)
        for j in range(5):
            sparkle(c, 700 + j * 130, 280 + (j % 2) * 60, 12, 220)
    if t > pc:
        k = pop(t, pc)
        stand(c, FRIEND, 300, 1060, 1.2, t, eyes="wide", mouth="laugh", brows="up", hands=[(-90, -160), (90, -160)])
        gaming_pc(c, 520, 1060, 1.0 * k, t)
    if t > pz:
        for j in range(int(min(12, (t - pz) * 10))):
            pizza_box(c, 1450 + (j % 3) * 60, 1040 - j // 3 * 46 - (j % 3) * 4, 1.1)
        stand(c, YOU_BLUE, 1700, 1060, 1.25, t, eyes="open", mouth="grin", brows="up", hands=[(-120, -40), (30, 150)], look=(-1, 0))
        pop_text(c, "FREE PIZZA FOR EVERYONE", 960, 380, 70, t, pz, GOLD, 9)


def s38(c, t, Q):  # try to buy a sports car; leave with a golf cart
    lot(c, t)
    car = Q.at("sports")
    gc = Q.at("golf")
    if t < gc:
        sports_car(c, 1250, 900, 1.3)
        laugh = t > Q.at("laughs")
        stand(c, SALESMAN, 1700, 1060, 1.3, t, eyes="closed" if laugh else "open", mouth="laugh" if laugh else "smile", brows="up",
              hands=[(-30, 150), (30, 150)] if not laugh else [(40, 60), (-40, 60)])
        stand(c, YOU_BLUE, 450, 1060, 1.3, t, eyes="open", mouth="grin" if t < Q.at("fifteen") else "frown", brows="up", hands=[(130, -40), (-30, 150)],
              look=(1, 0))
        if t > Q.at("fifteen"):
            pop_text(c, "AGE: 15", 450, 220, 100, t, Q.at("fifteen"), RED, 12)
    else:
        u = ease((t - gc) / 2.5)
        golf_cart(c, 300 + 1300 * u, 1000, 1.2, t)
        stand(c, YOU_BLUE, 300 + 1300 * u, 900, 0.9, t, eyes="closed", mouth="laugh", brows="up", hands=[(-60, -170), (60, -170)])
        pop_text(c, "...a very nice GOLF CART", W / 2, 200, 90, t, gc, GOLD, 10)


def s39(c, t, Q):  # news reporters: "Who is the duck kid?"
    street(c, t)
    for j, x in enumerate((300, 560, 1360, 1620)):
        left = x < 960
        hands = [(-30, 150), (170, -40)] if left else [(-170, -40), (30, 150)]
        stand(c, REPORTER, x, 1060, 1.0, t, eyes="open", mouth="O", brows="up", hands=hands, look=(1 if left else -1, -0.4))
        hx, hy = hand_pos(x, 1060, 1.0, dict(hands=hands), 1 if left else -1)
        mic(c, hx + (20 if left else -20), hy - 70)
    for j in range(3):  # camera flashes
        if (t * 3 + j) % 1 < 0.08:
            glow(c, 300 + j * 650, 500, 400, (255, 255, 255), 200)
    news_ticker(c, t, "WHO IS THE DUCK KID?")


def s40(c, t, Q):  # bank calls, freeze account
    office(c, t)
    stand(c, BANKER, 960, 1000, 1.35, t, eyes="squint", mouth="frown", brows="angry", hands=[(-30, 150), (75, -95)], look=(0, 0))
    bx, by = hand_pos(960, 1000, 1.35, dict(hands=[(-30, 150), (75, -95)]), 1)
    blob(c, rrect(bx - 18, by - 70, bx + 18, by + 10, 8), (30, 30, 35), 1.4, 0.7)  # phone at the ear
    fr = Q.at("freeze")
    if t > Q.at("suspicious"):
        pop_text(c, "SUSPICIOUS?", 500, 300, 90, t, Q.at("suspicious"), GOLD, 10)
    if t > fr:
        k = pop(t, fr)
        c.save()
        c.translate(1450, 420)
        c.scale(k, k)
        c.rotate(-8)
        c.drawRoundRect(skia.Rect(-260, -90, 260, 90), 20, 20, S(C(220, 40, 50), 14))
        text(c, "FROZEN", 0, 30, 100, (220, 40, 50), shadow=False)
        c.restore()
        for j in range(8):
            sparkle(c, 1150 + j * 80, 300 + (j % 3) * 120, 10, 200, (200, 230, 255))


def s41(c, t, Q):  # hire a lawyer who keeps thinking about the case
    office(c, t)
    stand(c, LAWYER, 1300, 1000, 1.35, t, eyes="squint", mouth="frown", brows="angry", hands=[(-120, -10), (-40, -120)], look=(-1, 0.3))
    stand(c, YOU_BLUE, 500, 1000, 1.25, t, eyes="open", mouth="smile", brows="flat", hands=[(-30, 150), (30, 150)], look=(1, 0))
    pop_text(c, "VERY EXPENSIVE LAWYER", W / 2, 140, 80, t, Q.at("expensive"), GOLD, 10)
    pl = Q.at("plus")
    for j in range(4):
        thought(c, 1300, 520, 1700, 160, t, pl - 0.6 + j * 0.9, 0.8)


def s42(c, t, Q):  # And then Thursday happens.
    chapter_card(c, t, "THURSDAY", col=RED)


def s43(c, t, Q):  # someone says the duck video was fake; people angry
    studio(c, t, (40, 10, 15))
    phone(c, 640, 560, 1.2, t, screen_views("FAKE?!", t, red=True))
    pop_text(c, "\"IT WAS FAKE!\"", 1300, 260, 110, t, Q.at("fake"), RED, 12)
    ang = Q.at("angry")
    for j in range(14):
        k = pop(t, ang + j * 0.06)
        if k > 0:
            angry_face(c, 1050 + (j % 5) * 150, 480 + (j // 5) * 150, 0.9 * k)


def s44(c, t, Q):  # angry people think about you way more
    studio(c, t, (45, 12, 20))
    sh, ty, sl = Q.at("shower"), Q.at("type"), Q.at("asleep")
    for j, (at, label, x) in enumerate(((sh, "in the shower", 360), (ty, "typing comments", 960), (sl, "before sleep", 1560))):
        k = pop(t, at)
        if k > 0:
            c.save()
            c.translate(x, 600)
            c.scale(k, k)
            angry_face(c, 0, 0, 2.6)
            c.restore()
            pop_text(c, label, x, 860, 56, t, at, (255, 255, 255), 7)
            for m in range(3):  # little red thought dots pulse out of each face (stay below the title)
                u = ((t - at) * 1.2 + m / 3) % 1
                c.drawCircle(x + 60 + 120 * u, 480 - 120 * u, 10 + 16 * u, P(C(255, 120, 110, int(220 * (1 - u)))))
    pop_text(c, "ANGER = MORE THOUGHTS", W / 2, 140, 90, t, Q.at("way"), RED, 11)


def s45(c, t, Q):  # money explodes: $10M in one afternoon
    studio(c, t, (20, 30, 20))
    ex = Q.at("explodes")
    bill_rain(c, t, ex, 70)
    if t > ex:
        k = (t - ex) / 0.6
        if k < 1:
            glow(c, W / 2, H / 2, 900 * k, (255, 240, 180), int(220 * (1 - k)))
    slam_text(c, "+$10,000,000", W / 2, H / 2 - 60, 170, t, Q.at("ten"), GREEN)
    pop_text(c, "in ONE afternoon", W / 2, H / 2 + 120, 70, t, Q.at("afternoon"), (255, 255, 255), 9)


def s46(c, t, Q):  # thought map: whole planet glowing, almost nothing nice
    red = ease((t - Q.at("nice") + 0.4) / 0.6)
    town_map(c, t, world=t > Q.at("planet"), glow_on=1.0, red=red)
    if t < Q.at("planet"):
        for j in range(30):
            c.drawCircle(760 + math.cos(j * 2.4) * (20 + j * 3), 560 + math.sin(j * 2.4) * (20 + j * 3) * 0.7, 8, P(C(90, 230, 140)))
    pop_text(c, "THE WHOLE PLANET", W / 2, 120, 100, t, Q.at("planet"), GOLD, 12)
    if red > 0.5:
        pop_text(c, "...and almost none of it nice", W / 2, 1000, 64, t, Q.at("nice"), RED, 8)


def s47(c, t, Q):  # hardest question: would you let them?
    studio(c, t, (25, 10, 15))
    c.drawPaint(P(Shader=rad(W / 2, 600, 700, [C(255, 255, 255, 40), C(0, 0, 0, 0)])))
    stand(c, YOU_BLUE, 960, 1050, 1.45, t, eyes="squint", mouth="frown", brows="sad", hands=[(40, -110), (-40, 60)], look=(0, 0.3))
    pop_text(c, "If hate makes you richer...", W / 2, 150, 80, t, Q.at("hating"), (255, 255, 255), 9)
    slam_text(c, "WOULD YOU LET THEM?", W / 2, 300, 110, t, Q.at("let"), RED)


def s48(c, t, Q):  # at first, no
    studio(c, t, (25, 30, 40))
    stand(c, YOU_BLUE, 960, 1050, 1.4, t, eyes="open", mouth="frown", brows="angry", hands=[(-120, -60), (120, -60)], look=(0, 0), tilt=8 * math.sin(t * 7))
    slam_text(c, "NO.", W / 2, 260, 200, t, Q.at("no"), (255, 255, 255))


def s49(c, t, Q):  # numbers glowing; annoying -> counter spins faster
    studio(c, t, (15, 30, 25))
    spin = ease((t - Q.at("annoying")) / 0.6)
    phone(c, 960, 660, 1.3, t, screen_bank([(money(int(10 ** 7 + (t * 3e6) * (1 + 5 * spin))), "counter spinning...")] * 3, t),
          glow_col=GREEN, buzz=spin)
    pop_text(c, "annoying = FASTER", W / 2, 120, 90, t, Q.at("annoying"), GOLD, 10)


def s50(c, t, Q):  # picking fights, roasting everyone, loved to hate
    studio(c, t, (40, 12, 30))
    stand(c, YOU_BLUE, 640, 1050, 1.35, t, eyes="squint", mouth="grin", brows="angry", hands=[(140, -60), (-40, 60)], look=(1, 0))
    rec = (t * 2) % 1 < 0.6
    if rec:
        c.drawCircle(160, 140, 24, P(C(240, 40, 40)))
        text(c, "REC", 210, 156, 44, (255, 255, 255), align="left")
    for j in range(10):
        k = pop(t, Q.at("roast") + j * 0.15)
        if k > 0:
            angry_face(c, 1250 + (j % 4) * 160, 380 + (j // 4) * 170, 0.9 * k)
    slam_text(c, "LOVED TO HATE", W / 2, 140, 110, t, Q.at("hate"), RED)


def s51(c, t, Q):  # fake drama with a famous singer; fans flood comments
    studio(c, t, (50, 15, 45))
    stand(c, SINGER, 1450, 1050, 1.35, t, eyes="squint", mouth="frown", brows="angry", hands=[(-60, -40), (40, 60)], look=(-1, 0))
    stand(c, YOU_BLUE, 470, 1050, 1.3, t, eyes="open", mouth="grin", brows="smug", hands=[(130, -40), (-30, 150)], look=(1, 0))
    flood = Q.at("flood")
    for j in range(24):
        k = pop(t, flood + j * 0.05)
        if k > 0:
            x, y = 700 + (j % 6) * 90, 260 + (j // 6) * 120
            c.drawRoundRect(skia.Rect(x - 40 * k, y - 30 * k, x + 40 * k, y + 30 * k), 12, 12, P(C(255, 255, 255, 230)))
            angry_face(c, x, y, 0.45 * k)
    slam_text(c, "$ MILLIONS", W / 2, 960, 110, t, Q.at("millions", 2), GREEN)


def s52(c, t, Q):  # whispers at school; little brother asks
    classroom(c, t)
    wh = Q.at("whisper")
    for j, x in enumerate((250, 450, 1500, 1700)):
        stand(c, [FRIEND, CRUSH, REPORTER, TEACHER][j], x, 1060, 0.95, t, eyes="squint", mouth="O" if (t * 2 + j) % 1 < 0.5 else "frown",
              brows="angry", hands=[(40, -120), (30, 150)] if j % 2 == 0 else [(-30, 150), (-40, -120)], look=(1 if x < 960 else -1, 0))
    asks = Q.at("brother")
    if t < asks:
        stand(c, YOU_BLUE, 960, 1060, 1.3, t, eyes="sad", mouth="frown", brows="sad", hands=[(-30, 150), (30, 150)], look=(0, 0.4))
        pop_text(c, "whisper whisper...", W / 2, 160, 80, t, wh, (220, 220, 230), 9)
    else:
        stand(c, YOU_BLUE, 860, 1060, 1.3, t, eyes="open", mouth="smile", brows="sad", hands=[(-30, 150), (40, 60)], look=(1, 0.3))
        stand(c, BRO, 1120, 1060, 0.95, t, eyes="sad", mouth="frown", brows="sad", hands=[(-30, 150), (30, 150)], look=(-1, -0.3))
        pop_text(c, "\"Why is everyone being mean?\"", W / 2, 160, 70, t, asks, (255, 255, 255), 9)
        if t > Q.at("game"):
            pop_text(c, "\"It's just a game.\"", W / 2, 290, 64, t, Q.at("game"), BLUE, 8)


def s53(c, t, Q):  # mom at dinner, looks at you differently
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(70, 50, 45), C(40, 28, 25)])))
    glow(c, 960, 300, 700, (255, 200, 120), 120)
    c.drawLine(960, 0, 960, 220, S(C(40, 30, 25), 6))
    c.drawCircle(960, 240, 40, P(C(255, 220, 150)))
    table(c, 300, 1620, 760)
    for x in (620, 1300):
        c.drawOval(skia.Rect(x - 90, 740, x + 90, 780), P(C(245, 245, 240)))
    stand(c, YOU_BLUE, 520, 1060, 1.25, t, eyes="open", mouth="smile", brows="flat", hands=[(60, 60), (-30, 150)], look=(1, 0))
    look = Q.at("looks")
    stand(c, MOM, 1400, 1060, 1.3, t, eyes="sad" if t > look else "open", mouth="frown" if t > look else "smile", brows="sad", hands=[(-60, 60), (30, 150)],
          look=(-1, 0))
    pop_text(c, "...", 1400, 240, 140, t, Q.at("anything"), (255, 255, 255), 10)


def s54(c, t, Q):  # By Friday, billionaire
    if t < 0.9:
        chapter_card(c, t, "FRIDAY")
        return
    studio(c, t, (40, 30, 10))
    bill_rain(c, t, 0.9, 80, 9)
    stand(c, YOU_BLUE, 960, 1060, 1.4, t, eyes="closed", mouth="laugh", brows="up", hands=[(-110, -180), (110, -180)])
    slam_text(c, "BILLIONAIRE", W / 2, 260, 170, t, Q.at("billionaire"), GOLD)


def s55(c, t, Q):  # best friend stopped answering
    studio(c, t, (20, 22, 35))
    def chat(cc, w, h):
        cc.drawRect(skia.Rect(0, 0, w, h), P(C(240, 242, 246)))
        cc.drawRect(skia.Rect(0, 0, w, 70), P(C(245, 200, 60)))
        text(cc, "Best Friend", w / 2, 46, 26, (60, 40, 10), shadow=False)
        for j, msg in enumerate(("hey?", "you there?", "hello??", "sorry...")):
            if t > 0.4 + j * 0.5:
                y = 120 + j * 90
                cc.drawRoundRect(skia.Rect(w - 210, y - 32, w - 16, y + 30), 20, 20, P(C(60, 150, 240)))
                text(cc, msg, w - 113, y + 9, 24, (255, 255, 255), shadow=False)
        text(cc, "Read", w - 20, 500, 18, (140, 140, 150), align="right", bold=False, shadow=False)
    phone(c, 960, 660, 1.3, t, chat)
    pop_text(c, "no reply.", W / 2, 120, 90, t, Q.at("stopped"), (200, 200, 210), 10)


def s56(c, t, Q):  # people move on. Fast.
    studio(c, t, (25, 25, 35))
    for j in range(40):
        y = (j * 47 + t * 900) % (H + 100) - 50
        c.drawLine(80 + j * 46, y, 80 + j * 46, y + 140, S(C(255, 255, 255, 60), 4))
    pop_text(c, "what nobody tells you about internet fame...", W / 2, 230, 58, t, 0.15, (200, 200, 215), 7)
    stand(c, YOU_BLUE, 960, 1060, 1.1, t, eyes="sad" if t > Q.at("move") else "open", mouth="frown" if t > Q.at("move") else "smile",
          brows="sad" if t > Q.at("move") else "flat", hands=[(-30, 150), (30, 150)], look=(0, -0.2))
    slam_text(c, "PEOPLE MOVE ON", W / 2, 400, 140, t, Q.at("move"), (255, 255, 255))
    slam_text(c, "FAST.", W / 2, 620, 160, t, Q.at("fast"), RED)


def s57(c, t, Q):  # Saturday: cat drummer goes viral, world forgets
    if t < 1.3:
        chapter_card(c, t, "SATURDAY")
        return
    studio(c, t, (30, 20, 50))
    cat = Q.at("cat")
    if t > cat - 0.2:
        cat_drummer(c, 1300, 980, 1.2 * pop(t, cat), t)
        stand(c, CATGUY, 560, 1060, 1.25, t, eyes="closed", mouth="laugh", brows="up", hands=[(-80, -170), (80, -170)])
        pop_text(c, "CAT PLAYS DRUMS", W / 2, 160, 100, t, cat, GOLD, 12)
    fg = Q.at("forgets")
    if t > fg:
        pop_text(c, "...the world forgets you", W / 2, 300, 70, t, fg, (200, 200, 210), 9)


def s58(c, t, Q):  # 10M -> 1M -> 100K -> nothing
    studio(c, t, (20, 20, 30))
    steps = [("10,000,000", Q.at("ten")), ("1,000,000", Q.at("one")), ("100,000", Q.at("hundred")), ("almost nothing", Q.at("nothing"))]
    cur = None
    for lab, at in steps:
        if t > at:
            cur = (lab, at)
    if cur:
        slam_text(c, cur[0], W / 2, 420, 150, t, cur[1], RED if cur[0] != "10,000,000" else GOLD)
    pop_text(c, "thoughts per day", W / 2, 640, 70, t, Q.at("thoughts"), (255, 255, 255), 9)


def s59(c, t, Q):  # phone goes quiet; nobody thinking
    bedroom(c, t, night=True)
    stand(c, YOU_BLUE, 700, 1040, 1.35, t, eyes="sad", mouth="frown", brows="sad", hands=[(80, -20), (-30, 150)], look=(1, 0.4))
    phone(c, 1250, 560, 0.9, t, screen_bank([("$0", "no new thoughts")], t))
    pop_text(c, "quiet.", W / 2, 140, 110, t, Q.at("quiet"), (200, 200, 210), 12)


def s60(c, t, Q):  # panic: 10,000 ducks -> 40 views; singer doesn't reply
    bedroom(c, t)
    r = random.Random(7)
    for i in range(160):
        duck(c, r.uniform(60, 1860), 1040 - r.uniform(0, 400), 0.55, t + i, r.uniform(-20, 20))
    stand(c, YOU_BLUE, 960, 1000, 1.25, t, eyes="wide", mouth="O", brows="sad", hands=[(-120, -150), (120, -150)], tilt=10 * math.sin(t * 8))
    pop_text(c, "10,000 DUCKS", W / 2, 140, 100, t, Q.at("ten"), GOLD, 12)
    if t > Q.at("forty"):
        slam_text(c, "40 views.", W / 2, 360, 110, t, Q.at("forty"), RED)


def s61(c, t, Q):  # staring at the counter; loneliest feeling
    studio(c, t, (12, 14, 22))
    c.drawPaint(P(Shader=rad(960, 500, 600, [C(255, 255, 255, 30), C(0, 0, 0, 0)])))
    stand(c, YOU_BLUE, 960, 1060, 1.35, t, eyes="sad", mouth="frown", brows="sad", hands=[(40, 60), (-40, 60)], look=(0, -0.6))
    pop_text(c, "the loneliest feeling", W / 2, 160, 90, t, Q.at("loneliest"), (200, 210, 230), 10)
    if t > Q.at("nobody"):
        pop_text(c, "nobody's thinking about you", W / 2, 300, 70, t, Q.at("nobody"), (255, 255, 255), 9)


def s62(c, t, Q):  # except... 6:42 AM, phone buzzes, +1
    bedroom(c, t)
    pop_text(c, "6:42 AM", 420, 130, 110, t, Q.at("six"), (255, 255, 255), 12)
    bz = Q.at("buzzes")
    stand(c, YOU_BLUE, 700, 1040, 1.35, t, eyes="wide" if t > bz else "sad", mouth="O" if t > bz else "frown", brows="up", hands=[(80, -30), (-30, 150)],
          look=(1, -0.2))
    phone(c, 1250, 560, 0.95, t, screen_bank([("+$1", "Somebody thought of you")], t) if t > bz else None, buzz=1.0 if bz < t < bz + 0.8 else 0,
          glow_col=GREEN if t > bz else None)


def s63(c, t, Q):  # it's your mom, wondering if you had breakfast
    kitchen(c, t)
    stand(c, MOM, 960, 1050, 1.5, t, eyes="open", mouth="smile", brows="sad", hands=[(110, 30), (60, 70)], look=(-0.6, 0))
    c.drawCircle(1350, 300, 110, P(C(255, 255, 255, 235)))
    c.drawCircle(1250, 420, 26, P(C(255, 255, 255, 235)))
    text(c, "breakfast?", 1350, 315, 44, (60, 60, 70), shadow=False)
    heart(c, 1350, 230, 0.6, 230)
    pop_text(c, "MOM.", W / 2, 140, 130, t, Q.at("mom"), PINK, 12)


def s64(c, t, Q):  # Sunday: empty mansion, $1.2 billion
    if t < 1.3:
        chapter_card(c, t, "SUNDAY")
        return
    mansion(c, t)
    stand(c, YOU_BLUE, 960, 1000, 1.1, t, eyes="sad", mouth="frown", brows="sad", hands=[(40, 80), (-40, 80)], look=(0, 0.6))
    slam_text(c, "$1,200,000,000", W / 2, 230, 140, t, Q.at("one"), GOLD)
    pop_text(c, "...and an empty house", W / 2, 380, 64, t, Q.at("empty"), (80, 80, 90), 0)


def s65(c, t, Q):  # billions felt like nothing; mom's dollar made you smile
    studio(c, t, (30, 20, 30))
    bil = Q.at("billions")
    if t > bil:
        k = max(0.0, 1 - (t - bil) / 2.5)
        bill_rain(c, t, bil, int(60 * k) + 1, 4)
        pop_text(c, "billions from strangers", 560, 300, 64, t, bil, (170, 170, 180), 8)
    md = Q.at("mom")
    if t > md:
        k = pop(t, md)
        c.save()
        c.translate(1350, 560)
        c.scale(k, k)
        c.drawCircle(0, 0, 150, P(C(255, 255, 255)))
        c.drawCircle(0, 0, 150, S(C(255, 120, 180), 8))
        text(c, "$1", 0, 40, 120, (30, 150, 80), shadow=False)
        c.restore()
        pop_text(c, "from MOM", 1350, 820, 70, t, md, PINK, 9)
        glow(c, 1350, 560, 360, (255, 160, 200), 120)
    sm = t > Q.at("smile")
    stand(c, YOU_BLUE, 560, 1060, 1.1, t, eyes="closed" if sm else "sad", mouth="grin" if sm else "frown", brows="up" if sm else "sad",
          hands=[(-30, 150), (30, 150)], look=(1, -0.3))


def s66(c, t, Q):  # library, teacher's trip, flowers for grandma
    studio(c, t, (30, 40, 30))
    lib, trip, fl = Q.at("library"), Q.at("trip"), Q.at("flowers")
    for at, x, kind in ((lib, 380, "lib"), (trip, 960, "trip"), (fl, 1540, "fl")):
        k = pop(t, at)
        if k <= 0:
            continue
        c.save()
        c.translate(x, 650)
        c.scale(k, k)
        if kind == "lib":
            blob(c, rrect(-200, -200, 200, 120, 10), (200, 160, 120))
            for j in range(5):
                c.drawRect(skia.Rect(-170 + j * 70, -160, -120 + j * 70, 80), P(C(*[(200, 60, 60), (60, 120, 200), (240, 190, 60), (90, 170, 90), (150, 90, 200)][j])))
            text(c, "LIBRARY", 0, 220, 54, (255, 255, 255))
        elif kind == "trip":
            p = skia.Path()  # paper plane
            p.moveTo(-160, 40)
            p.lineTo(170, -90)
            p.lineTo(-40, 110)
            p.close()
            blob(c, p, (240, 240, 250), 1.05, 0.85)
            text(c, "DREAM TRIP", 0, 220, 54, (255, 255, 255))
        else:
            for j in range(5):
                a = -0.8 + j * 0.4
                c.drawLine(0, 100, math.sin(a) * 140, -60, S(C(60, 140, 60), 8))
                c.drawCircle(math.sin(a) * 140, -80, 34, P(C(*[(255, 120, 160), (255, 200, 60), (200, 120, 255)][j % 3])))
            text(c, "FOR GRANDMA", 0, 220, 54, (255, 255, 255))
        c.restore()


def s67(c, t, Q):  # warm thoughts come back
    town_map(c, t)
    wm = Q.at("warm")
    for j in range(16):
        k = pop(t, Q.at("coming") + j * 0.12)
        if k > 0:
            x, y = 760 + math.cos(j * 2.4) * (40 + j * 14), 560 + math.sin(j * 2.4) * (40 + j * 14) * 0.7
            col = (255, 170, 200) if t > wm else (90, 230, 140)
            c.drawCircle(x, y, 10 * k, P(C(*col)))
            glow(c, x, y, 40, col, 120)
    pop_text(c, "just a few...", W / 2, 140, 90, t, Q.at("few"), (255, 255, 255), 10)
    if t > wm:
        pop_text(c, "but WARM", W / 2, 340, 110, t, wm, PINK, 12)
    if t > Q.at("you"):
        pop_text(c, "they're thinking about YOU", W / 2, 980, 64, t, Q.at("you"), (255, 255, 255), 8)


def s68(c, t, Q):  # call best friend; "I've been thinking about you all week"
    c.drawPaint(P(Shader=lin((0, 0), (W, 0), [C(60, 120, 170), C(60, 120, 170), C(220, 160, 80), C(220, 160, 80)], [0, 0.5, 0.5, 1])))
    c.drawLine(W / 2, 0, W / 2, H, S(C(255, 255, 255), 10))
    sorry = Q.at("sorry")
    stand(c, YOU_BLUE, 480, 1060, 1.35, t, eyes="sad" if t < Q.at("okay") else "closed", mouth="frown" if t < Q.at("okay") else "grin", brows="sad",
          hands=[(70, -100), (-30, 150)], look=(1, 0))
    stand(c, FRIEND, 1440, 1060, 1.35, t, eyes="open" if t < Q.at("okay") else "closed", mouth="frown" if t < Q.at("okay") else "grin",
          brows="flat" if t < Q.at("okay") else "up", hands=[(-70, -100), (30, 150)], look=(-1, 0))
    if t > sorry:
        pop_text(c, "\"Sorry.\"", 480, 200, 80, t, sorry, (255, 255, 255), 9)
    if t > Q.at("okay"):
        pop_text(c, "\"It's okay...\"", 1440, 200, 72, t, Q.at("okay"), (255, 255, 255), 9)
    if t > Q.at("thinking"):
        pop_text(c, "\"I've been thinking about you all week.\"", W / 2, 360, 60, t, Q.at("thinking"), (255, 240, 200), 8)
        for j in range(4):
            heart(c, 960 + (j - 1.5) * 90, 520 - ((t * 60 + j * 30) % 100), 0.8, 230)


def s69(c, t, Q):  # phone buzzes, +$1
    studio(c, t, (25, 35, 30))
    bz = Q.at("buzzes")
    phone(c, W / 2, 560, 1.45, t, screen_bank([("+$1", "Best Friend thought of you")], t) if t > bz else None, buzz=1.0 if bz < t < bz + 0.7 else 0,
          glow_col=PINK if t > bz else None)
    if t > bz:
        sparkle_ring(c, W / 2, 560, 420, t, 10, col=(255, 200, 220))


def s70(c, t, Q):  # some thoughts are worth more than money
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(250, 200, 160), C(200, 120, 140)])))
    glow(c, 960, 500, 800, (255, 230, 200), 160)
    pop_text(c, "Some people are worth billions.", W / 2, 360, 80, t, 0.1, (255, 255, 255), 9)
    slam_text(c, "Some thoughts are worth MORE.", W / 2, 560, 90, t, Q.at("thoughts"), (255, 255, 255))
    for j in range(5):
        heart(c, 300 + j * 330, 900 - ((t * 40 + j * 40) % 160), 0.9, 200)


def s71(c, t, Q):  # how much would you have made? who's thinking about you?
    studio(c, t, (30, 25, 50))
    pop_text(c, "How much would YOU have made today?", W / 2, 200, 70, t, Q.at("how"), GOLD, 9)
    who = Q.at("who")
    if t > who:
        pop_text(c, "Who is thinking about you RIGHT NOW?", W / 2, 340, 70, t, who, (255, 255, 255), 9)
    for j, (look, at) in enumerate(((MOM, Q.at("mom")), (FRIEND, Q.at("best")), (GRANDMA, Q.at("someone")))):
        k = pop(t, at)
        if k > 0:
            c.save()
            c.translate(480 + j * 480, 1050)
            c.scale(1.1 * k, 1.1 * k)
            stand(c, look, 0, 0, 1.0, t, eyes="closed", mouth="grin", brows="up", hands=[(-30, 150), (30, 150)])
            c.restore()
            thought(c, 480 + j * 480, 470, 960, 480, t, at + 0.3, 0.9, col=PINK)


def s72(c, t, Q):  # challenge: send one text
    studio(c, t, (20, 30, 40))
    def compose(cc, w, h):
        cc.drawRect(skia.Rect(0, 0, w, h), P(C(240, 242, 246)))
        cc.drawRect(skia.Rect(0, 0, w, 70), P(C(90, 170, 255)))
        text(cc, "New message", w / 2, 46, 26, (255, 255, 255), shadow=False)
        typed = "thinking of you :)"[: max(0, int((t - 1.0) * 8))]
        cc.drawRoundRect(skia.Rect(16, h - 90, w - 16, h - 30), 20, 20, P(C(255, 255, 255)))
        text(cc, typed, 30, h - 50, 24, (40, 40, 50), align="left", shadow=False)
    phone(c, 960, 660, 1.3, t, compose, glow_col=BLUE)
    pop_text(c, "THE CHALLENGE", W / 2, 120, 100, t, Q.at("challenge"), GOLD, 12)
    if t > Q.at("buzz"):
        pop_text(c, "your phone could be about to buzz...", W / 2, 1000, 60, t, Q.at("buzz"), (255, 255, 255), 8)


def s73(c, t, Q):  # comments + subscribe
    studio(c, t, (40, 15, 30))
    cm = Q.at("comments")
    sub = Q.at("subscribe")
    if t > cm:
        k = pop(t, cm)
        c.save()
        c.translate(640, 520)
        c.scale(k, k)
        c.drawRoundRect(skia.Rect(-260, -120, 260, 120), 40, 40, P(C(255, 255, 255)))
        text(c, "COMMENT", 0, 24, 64, (40, 40, 60), shadow=False)
        c.restore()
    if t > sub:
        k = pop(t, sub)
        pressed = t > sub + 1.2
        c.save()
        c.translate(1300, 520)
        c.scale(k * (0.94 if sub + 1.2 < t < sub + 1.35 else 1), k)
        c.drawRoundRect(skia.Rect(-300, -90, 300, 90), 90, 90, P(C(90, 90, 95) if pressed else C(230, 30, 35)))
        text(c, "SUBSCRIBED" if pressed else "SUBSCRIBE", 0, 26, 70, (255, 255, 255), shadow=False)
        c.restore()
        if pressed:
            sparkle_ring(c, 1300, 520, 380, t, 10)
    pop_text(c, "somebody is thinking about you.", W / 2, 900, 64, t, Q.at("definitely"), PINK, 8)


SHOTS = [globals()[f"s{k}"] for k in range(74)]
CHAPTERS = {3, 26, 36, 42, 54, 57, 64}  # shots that open on a chapter card (gold splat in)

# camera per shot: (zoom from, zoom to, focus x, focus y)
CAM = {}
for k in range(74):
    r = random.Random(k)
    CAM[k] = (1.0, 1.0 + r.uniform(0.03, 0.07), r.uniform(800, 1120), r.uniform(480, 620))
for k in (2, 19, 36, 42):
    CAM[k] = (1.0, 1.02, 960, 540)


# ---------- HUD: balance waypoints ----------

def build_hud():
    pe = ST.plus_events()
    w = lambda k, word, n=1, lead=0.0: ST.start[k] + ST.at(k, word, n, lead)
    sets = [(w(7, "eighteen"), 18), (w(16, "forty"), 47), (w(35, "two"), 2_000_000), (w(35, "five"), 5_000_000), (w(37, "pizza"), 5_200_000),
            (w(39, "story"), 5_600_000), (w(45, "ten"), 15_600_000), (w(51, "millions", 2), 120_000_000), (w(54, "billionaire"), 1_000_000_000),
            (w(64, "one"), 1_200_000_000)]
    events = [(t, "add", a) for t, a in pe] + [(t, "set", v) for t, v in sets]
    events.sort()
    bal, wps = 0, [(0.0, 0)]
    for t, kind, v in events:
        bal = bal + v if kind == "add" else max(bal, v)
        wps.append((t, bal))
    return wps, pe


WPS, PLUS = build_hud()


def balance(gt):
    prev_t, prev_v = 0.0, 0
    for t, v in WPS:
        if gt < t:
            break
        prev_t, prev_v, cur = t, v, v
    # roll from the waypoint before the current one, over 0.9 s
    i = max(i for i, (t, v) in enumerate(WPS) if t <= gt) if gt >= 0 else 0
    v_now = WPS[i][1]
    v_before = WPS[i - 1][1] if i > 0 else 0
    k = ease((gt - WPS[i][0]) / 0.9)
    return v_before + (v_now - v_before) * k, (gt - WPS[i][0]) < 0.25 and i > 0


HIDE_HUD = []  # chapter cards and the outro hide the HUD
for k in CHAPTERS:
    dur = {3: 1.6, 26: 1.3, 36: 99, 42: 99, 54: 0.9, 57: 1.3, 64: 1.3}[k]
    HIDE_HUD.append((ST.start[k], min(ST.end[k], ST.start[k] + dur)))
HIDE_HUD += [(ST.start[k], ST.end[k]) for k in (0, 1, 2, 70, 71, 72, 73)]


def draw_hud(c, gt):
    if any(a <= gt < b for a, b in HIDE_HUD):
        return
    bal, bump = balance(gt)
    c.save()
    c.translate(W - 50, 64)
    sc = 1 + 0.12 * bump
    c.scale(sc, sc)
    frozen = ST.start[40] + ST.at(40, "freeze") <= gt < ST.start[42]
    label = money(bal)
    f = font(50)
    w = max(260, f.measureText(label) + 100)
    r = rrect(-w, -42, 0, 42, 42)
    c.drawPath(r, P(C(0, 0, 0, 120), MaskFilter=blur(12)))
    c.drawPath(r, P(C(15, 30, 22, 225) if not frozen else C(20, 40, 70, 230)))
    c.drawPath(r, S(C(70, 220, 130) if not frozen else C(150, 210, 255), 4))
    c.drawCircle(-w + 42, 0, 26, P(C(60, 210, 120) if not frozen else C(150, 210, 255)))
    text(c, "$", -w + 42, 12, 32, (10, 40, 20), shadow=False)
    text(c, label, -28, 17, 50, (235, 255, 240), align="right", shadow=False)
    c.restore()
    shown = [(t, a) for t, a in PLUS if 0 <= gt - t < 1.4]
    if shown:  # only the newest card, so titles below never get covered
        t, amt = shown[-1]
        k = gt - t
        slide = out_back(min(1, k / 0.3), 1.6)
        a = int(255 * max(0, min(1, (1.4 - k) / 0.3)))
        notif_card(c, 300 - 360 * (1 - slide), 80, 0.82, amt, a)


# ---------- frame ----------

def frame(gt):
    k = ST.shot_at(gt)
    t = gt - ST.start[k]
    d = ST.end[k] - ST.start[k]
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    z0, z1, fx, fy = CAM[k]
    z = z0 + (z1 - z0) * ease(t / d)
    c.save()
    c.translate(fx, fy)
    c.scale(z, z)
    c.translate(-fx + math.sin(gt * 0.5) * 5, -fy + math.cos(gt * 0.4) * 4)
    SHOTS[k](c, t, Shot(k))
    c.restore()
    post(surf, c, gt)
    draw_hud(c, gt)
    # transitions: gold splat into each chapter card, quick white flash between other shots
    if k in CHAPTERS and t < 0.35 and k != 0:
        splat(c, 1 - ease(t / 0.35))
    if k + 1 in CHAPTERS and d - t < 0.3:
        splat(c, ease((t - (d - 0.3)) / 0.3))
    if k not in CHAPTERS and k > 0 and t < 0.12:
        c.drawPaint(P(C(255, 255, 255, int(110 * (1 - t / 0.12)))))
    # progress bar
    c.drawRect(skia.Rect(0, H - 8, W * gt / ST.total, H), P(C(255, 170, 60)))
    return surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)


def render_part(i, n):
    nf = int(ST.total * FPS)
    a, b = nf * i // n, nf * (i + 1) // n
    out = f"{DIR}/part_{i}.mp4"
    enc = encoder(out, crf=18)
    for f in range(a, b):
        enc.stdin.write(np.ascontiguousarray(frame(f / FPS)).tobytes())
        if (f - a) % 900 == 0:
            print(f"part {i}: {f - a}/{b - a}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", out)


def sound():
    import audio
    ev = []
    for k in range(1, 74):
        ev.append(("whoosh", ST.start[k]))
    for t, a in PLUS:
        ev.append(("ding" if a < 100 else "thud", t))
    for k in CHAPTERS:
        ev.append(("thud", ST.start[k] + 0.05))
    ev = [(kind, round(t, 3)) for kind, t in ev if 0 <= t < ST.total]
    audio.music(f"{DIR}/music.wav", ST.total, bpm=96, seed=21)
    audio.sfx(f"{DIR}/sfx.wav", ST.total, ev)


def final():
    import audio
    n = len([f for f in os.listdir(DIR) if f.startswith("part_") and f.endswith(".mp4")])
    with open(f"{DIR}/parts.txt", "w") as fh:
        for i in range(n):
            fh.write(f"file 'part_{i}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{DIR}/parts.txt", "-c", "copy", f"{DIR}/video_only.mp4"],
                   check=True)
    sound()
    audio.master(f"{DIR}/video_only.mp4", f"{DIR}/voice.mp3", f"{DIR}/music.wav", f"{DIR}/sfx.wav", f"{DIR}/final.mp4")
    print("wrote", f"{DIR}/final.mp4")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "render":
        i, n = map(int, sys.argv[2].split("/"))
        render_part(i, n)
    elif cmd == "final":
        final()
    elif cmd == "stills":
        ks = [int(x) for x in sys.argv[2].split(",")]
        ts = [float(x) for x in sys.argv[3].split(",")]
        out = sys.argv[4] if len(sys.argv) > 4 else f"{DIR}/stills"
        os.makedirs(out, exist_ok=True)
        from PIL import Image
        for k in ks:
            for tt in ts:
                gt = min(ST.end[k] - 0.01, ST.start[k] + tt)
                Image.fromarray(np.ascontiguousarray(frame(gt))).convert("RGB").save(f"{out}/s{k}_{tt}.png")
    elif cmd == "check":  # verify every cue word exists (catches KeyError before rendering)
        bad = 0
        for k in range(74):
            for tt in (0.0, 0.5, (ST.end[k] - ST.start[k]) / 2, ST.end[k] - ST.start[k] - 0.05):
                try:
                    frame(ST.start[k] + tt)
                except Exception as e:  # noqa: BLE001
                    print("shot", k, "t", round(tt, 2), type(e).__name__, e)
                    bad += 1
                    break
        print("problems:", bad)
