"""YouTube Short: "What If the Internet Shut Down for a Day?" - what-if explainer in the owner's favourite all-2D
fortune-cookie style (make_fortune.py / make_free.py). Voice: vidIQ "Chris".

Grounding: 19 July 2024 - a faulty CrowdStrike update crashed ~8.5 million Windows PCs (Microsoft's estimate); thousands
of flights were cancelled worldwide. 4 October 2021 - Facebook was offline for ~6 hours; engineers had trouble getting
into buildings because the badge system depended on the same network (NYT and others). No logos are drawn.

Physics (solved + asserted, reused by audio/QC): hospital papers fall and rest EXACTLY on the growing stack; the engineer
walks into the locked glass door and bounces back (never passes the door plane); the moths from the empty wallet fly
with drag + flutter.

  python make_offline.py stills 1.0,5.2  |  python make_offline.py frames (PROCS=4)
"""
import json
import math
import os
import random
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
import skia
from PIL import Image

import style2d_engine as E
import toon as T
from style2d_engine import C, P, S, W, H, K, FPS, path, lerp, lerp2, clamp, ramp, snap, smooth, noise1
import make_free as F          # shared 2D props/sets (counter, text, product, bg_shop, ...); its timing is not used here

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "offline")
TIMES = json.load(open(os.path.join(D, "vo_final.wav.times.json")))
WORDS = json.load(open(os.path.join(D, "vo_final.wav.words.json")))
LINES = json.load(open(os.path.join(D, "lines_final.json")))
ORDER = [l["key"] for l in LINES]
DUR = round(min(64.6, max(61.5, TIMES["cta"] + 3.4)), 3)
NF = int(round(DUR * FPS))
OUT_FR = os.path.join(D, "frames")
G_PX = 3600.0
PHYS = {}
OUT = T.OUT
counter, text = F.counter, F.text


def word_t(line, *cands, nth=1):
    nxt = ORDER.index(line) + 1
    t1 = TIMES[ORDER[nxt]] if nxt < len(ORDER) else 1e9
    for w in cands:
        hits = sorted(v for k, v in WORDS.items() if k.split("#")[0] == w and TIMES[line] - 0.3 <= v < t1 - 0.05)
        if len(hits) >= nth:
            return hits[nth - 1]
    raise KeyError(f"none of {cands} in line {line!r}")


def _cut(k):
    return TIMES[k] - 0.12


SCENES = [("hook", 0.0), ("minute", _cut("minute")), ("cards", _cut("cards")), ("flights", _cut("flights")), ("paper", _cut("paper")),
          ("trucks", word_t("paper", "never") - 0.1), ("real", _cut("real")), ("twist", _cut("twist")), ("end", _cut("end")),
          ("cta", TIMES["cta"] - 0.3)]
CUTS = [t for _, t in SCENES] + [DUR]


def scene_at(t):
    for i in range(len(SCENES)):
        if CUTS[i] <= t < CUTS[i + 1]:
            return i
    return len(SCENES) - 1


def span(name):
    i = [n for n, _ in SCENES].index(name)
    return CUTS[i], CUTS[i + 1]


# =================================================================================== people
YOU = dict(skin=(238, 196, 160), hair="neat", hair_col=(70, 45, 30), coat=(60, 140, 200), pants=(50, 60, 90), nose="small")
CASHIER = dict(skin=(232, 190, 160), hair="pigtails", hair_col=(120, 70, 35), coat=(230, 90, 80), apron=(250, 240, 220), pants=(60, 60, 70), nose="small")
PILOT = dict(skin=(225, 185, 150), hair="cap", hair_col=(30, 40, 80), coat=(35, 45, 85), pants=(30, 35, 60), nose="long", mustache=True)
NURSE = dict(skin=(235, 195, 165), hair="curly", hair_col=(60, 40, 25), coat=(120, 200, 190), pants=(110, 190, 180), nose="small", hat="papercap")
WORKER = dict(skin=(230, 188, 155), hair="neat", hair_col=(30, 25, 25), coat=(150, 150, 160), pants=(60, 60, 70), nose="small", glasses=True)
ENGINEER = dict(skin=(236, 196, 165), hair="neat", hair_col=(140, 90, 50), coat=(90, 90, 100), pants=(50, 55, 70), nose="small", glasses=True)


def layer_over(img, draw):
    s, c = E.surf()
    draw(c)
    return E.over(img, E.arr(s))


def char(img, look, x, y, s_, pose, t, shadow=0.0, rim=0.5, rim_col=(1.0, 0.7, 0.45), extra=None):
    ch = E.draw_person(look, x, y, s_, pose, t, extra)
    return E.light_char(ch, img, y, shadow=shadow, rim=rim, rim_col=rim_col)


def cam(name, keys):
    a = span(name)[0]
    return lambda t: E.catmull([(a + dt, z, x, y) for dt, z, x, y in keys], t)


# =================================================================================== props
def phone(c, x, y, s, t, mode="none", rot=0.0):
    """A phone held up; mode: 'none' (no-signal screen), 'spin' (loading forever), 'ok' (bars back)."""
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    c.drawRoundRect(skia.Rect(-80, -150, 80, 150), 24, 24, P(C(35, 35, 45)))
    scr = skia.Rect(-66, -128, 66, 128)
    c.drawRoundRect(scr, 12, 12, P(Shader=T.lin((0, -128), (0, 128), [C(40, 60, 110), C(20, 30, 60)]) if mode != "ok" else
                                    T.lin((0, -128), (0, 128), [C(90, 200, 140), C(40, 140, 100)])))
    if mode == "none":
        for k in range(3):     # wifi arcs, struck out
            r_ = 22 + 18 * k
            c.drawArc(skia.Rect(-r_, -20 - r_, r_, -20 + r_), 225, 90, False, S(C(255, 255, 255, 120), 7))
        c.drawLine(-50, -90, 50, 10, S(C(240, 70, 60), 9))
        text(c, "NO", 0, 60, 34, C(255, 255, 255))
        text(c, "SIGNAL", 0, 96, 28, C(255, 255, 255))
    elif mode == "spin":
        a0 = (t * 360) % 360
        c.drawArc(skia.Rect(-40, -40, 40, 40), a0, 270, False, S(C(255, 255, 255), 10))
    else:
        for k in range(3):
            r_ = 22 + 18 * k
            c.drawArc(skia.Rect(-r_, -r_, r_, r_), 225, 90, False, S(C(255, 255, 255), 8))
        c.drawCircle(0, 0, 8, P(C(255, 255, 255)))
    c.drawRoundRect(skia.Rect(-80, -150, 80, 150), 24, 24, S(OUT, 6))
    c.restore()


def app_icon(c, x, y, s, kind, crossed):
    c.save(); c.translate(x, y); c.scale(s, s)
    col = {"msg": (90, 200, 110), "map": (240, 180, 60), "vid": (230, 70, 60)}[kind]
    c.drawRoundRect(skia.Rect(-60, -60, 60, 60), 22, 22, P(C(*col)))
    if kind == "msg":
        c.drawRoundRect(skia.Rect(-34, -26, 34, 20), 14, 14, P(C(255, 255, 255)))
        c.drawPath(path([(-20, 16), (-30, 34), (0, 16)]), P(C(255, 255, 255)))
    elif kind == "map":
        c.drawCircle(0, -10, 22, P(C(255, 255, 255))); c.drawPath(path([(-18, 0), (18, 0), (0, 36)]), P(C(255, 255, 255)))
        c.drawCircle(0, -10, 9, P(C(*col)))
    else:
        c.drawPath(path([(-16, -24), (-16, 24), (26, 0)]), P(C(255, 255, 255)))
    c.drawRoundRect(skia.Rect(-60, -60, 60, 60), 22, 22, S(OUT, 5))
    if crossed > 0:
        e = crossed
        c.drawLine(-50, -50, -50 + 100 * e, -50 + 100 * e, S(C(255, 40, 40), 12))
        c.drawLine(50, -50, 50 - 100 * e, -50 + 100 * e, S(C(255, 40, 40), 12))
    c.restore()


def card_reader(c, x, y, s, t, declined_at):
    c.save(); c.translate(x, y); c.scale(s, s)
    c.drawRoundRect(skia.Rect(-80, -190, 80, 0), 20, 20, P(C(45, 50, 60)))
    on = t >= declined_at
    blink = on and int((t - declined_at) * 4) % 2 == 0
    c.drawRect(skia.Rect(-62, -170, 62, -100), P(C(200, 40, 40) if blink else (C(90, 30, 30) if on else C(60, 150, 200))))
    text(c, "DECLINED" if on else "TAP CARD", 0, -124, 24, C(255, 255, 255))
    for r in range(3):
        for k in range(3):
            c.drawRoundRect(skia.Rect(-52 + k * 38, -86 + r * 26, -24 + k * 38, -66 + r * 26), 4, 4, P(C(180, 185, 195)))
    c.drawRoundRect(skia.Rect(-80, -190, 80, 0), 20, 20, S(OUT, 5))
    c.restore()


def wallet(c, x, y, s, open_):
    c.save(); c.translate(x, y); c.scale(s, s)
    if open_:
        c.drawRoundRect(skia.Rect(-110, -70, 110, 70), 14, 14, P(C(120, 75, 40)))
        c.drawRect(skia.Rect(-98, -56, 98, 56), P(C(60, 35, 20)))
        c.drawLine(0, -70, 0, 70, S(OUT, 4))
        c.drawRoundRect(skia.Rect(-110, -70, 110, 70), 14, 14, S(OUT, 5))
    else:
        c.drawRoundRect(skia.Rect(-70, -55, 70, 55), 14, 14, P(C(120, 75, 40)))
        c.drawRoundRect(skia.Rect(-70, -55, 70, 55), 14, 14, S(OUT, 5))
    c.restore()


def moth(c, x, y, t, k):
    fl = math.sin(t * 30 + k) * 0.8
    for sx in (-1, 1):
        c.save(); c.translate(x, y); c.scale(sx, 1); c.rotate(-20 + 25 * fl)
        c.drawOval(skia.Rect(0, -14, 30, 10), P(C(200, 190, 170))); c.drawOval(skia.Rect(0, -14, 30, 10), S(OUT, 2))
        c.restore()
    c.drawOval(skia.Rect(x - 5, y - 12, x + 5, y + 14), P(C(110, 100, 90)))


def truck(c, x, y, s=1.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    c.drawRect(skia.Rect(-260, -300, 120, -50), P(C(240, 240, 235))); c.drawRect(skia.Rect(-260, -300, 120, -50), S(OUT, 5))
    c.drawPath(path([(120, -220), (210, -220), (260, -140), (260, -50), (120, -50)]), P(C(220, 70, 55)))
    c.drawPath(path([(140, -205), (200, -205), (240, -145), (140, -145)]), P(C(170, 220, 245)))
    c.drawPath(path([(120, -220), (210, -220), (260, -140), (260, -50), (120, -50)]), S(OUT, 5))
    for wx in (-180, -60, 190):
        c.drawCircle(wx, -45, 45, P(C(40, 40, 45))); c.drawCircle(wx, -45, 18, P(C(180, 180, 185))); c.drawCircle(wx, -45, 45, S(OUT, 4))
    c.restore()


def monitor(c, x, y, w_, h_, state, t):
    """state 0 = normal desktop, 1 = crashed (blue screen with a sad face)."""
    c.drawRoundRect(skia.Rect(x - w_ / 2 - 8, y - h_ / 2 - 8, x + w_ / 2 + 8, y + h_ / 2 + 8), 8, 8, P(C(40, 40, 45)))
    if state:
        c.drawRect(skia.Rect(x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2), P(C(30, 90, 200)))
        text(c, ":(", x - w_ * 0.22, y - h_ * 0.02, h_ * 0.42, C(255, 255, 255))
        for k in range(3):
            c.drawRect(skia.Rect(x - w_ * 0.38, y + h_ * (0.12 + 0.1 * k), x + w_ * (0.2 - 0.12 * k), y + h_ * (0.16 + 0.1 * k)), P(C(200, 220, 255)))
    else:
        c.drawRect(skia.Rect(x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2), P(Shader=T.lin((x, y - h_ / 2), (x, y + h_ / 2), [C(120, 190, 230), C(70, 140, 200)])))
        for k in range(3):
            c.drawRoundRect(skia.Rect(x - w_ * 0.4, y - h_ * 0.35 + k * h_ * 0.22, x - w_ * 0.25, y - h_ * 0.2 + k * h_ * 0.22), 3, 3, P(C(255, 255, 255, 200)))
    c.drawRoundRect(skia.Rect(x - w_ / 2 - 8, y - h_ / 2 - 8, x + w_ / 2 + 8, y + h_ / 2 + 8), 8, 8, S(OUT, 4))


# =================================================================================== physics
DESK_Y = 1500.0
SHEET_T = 9.0
PAPER = dict(n=14, x=760.0, drop_h=560.0, every=0.05)


def paper_t0():
    return word_t("paper", "hospitals") + 0.2 - math.sqrt(2 * PAPER["drop_h"] / G_PX)   # all landed before "trucks"


def paper_stack(t):
    """Sheet k is dropped flat at t0 + k*every and falls under gravity onto the stack top (DESK_Y - k*SHEET_T)."""
    out = []
    t0 = paper_t0()
    for k in range(PAPER["n"]):
        u = t - (t0 + k * PAPER["every"])
        if u < 0:
            break
        rest = DESK_Y - k * SHEET_T
        y = rest - PAPER["drop_h"] + 0.5 * G_PX * u * u
        out.append((min(y, rest), y >= rest, k))
    PHYS["paper_fall_s"] = math.sqrt(2 * PAPER["drop_h"] / G_PX)
    return out


def paper_land_times():
    t0 = paper_t0()
    return [t0 + k * PAPER["every"] + math.sqrt(2 * PAPER["drop_h"] / G_PX) for k in range(PAPER["n"])]


DOOR_X = 640.0           # the glass door's plane (the engineer's nose can't pass it)
ENG_REACH = 95.0        # nose distance in front of his body centre at the scale used


def bonk_t():
    return word_t("twist", "building") - 0.05


def engineer_x(t):
    """Walks right at v until his nose reaches the door at bonk_t, then bounces back: a damped spring
    x = x_hit - A (1 - e^(-b u) cos(w u)) - never beyond the door."""
    tb = bonk_t()
    x_hit = DOOR_X - ENG_REACH
    v = 70.0
    if t < tb:
        return x_hit - v * (tb - t)
    u = t - tb
    return x_hit - 70.0 * (1 - math.exp(-5.0 * u) * math.cos(9.0 * u)) * (1 - math.exp(-12.0 * u))


# =================================================================================== 2D sets
@lru_cache(maxsize=None)
def bg_city(lit=False, dusk=True):
    s, c = E.surf()
    top, low = ((25, 25, 60), (120, 70, 110)) if dusk else ((12, 14, 40), (40, 40, 90))
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, 1400), [C(*top), C(*low)])))
    r = random.Random(5)
    for _ in range(50):
        c.drawCircle(r.uniform(0, W), r.uniform(0, 900), r.uniform(1.5, 3), P(C(255, 255, 240, r.randint(80, 200))))
    for x, w_, h_ in ((-20, 220, 700), (190, 180, 900), (360, 240, 620), (590, 200, 980), (780, 170, 720), (940, 200, 860)):
        y0 = 1560 - h_
        c.drawRect(skia.Rect(x, y0, x + w_, 1560), P(C(45, 45, 75)))
        c.drawRect(skia.Rect(x, y0, x + w_, 1560), S(C(20, 20, 35), 4))
        for j in range(int(h_ / 70)):
            for k in range(int(w_ / 55)):
                on = r.random() < (0.85 if lit else 0.12)
                c.drawRect(skia.Rect(x + 14 + k * 55, y0 + 20 + j * 70, x + 44 + k * 55, y0 + 58 + j * 70),
                           P(C(255, 215, 120) if on else C(30, 30, 50)))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_living():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(C(120, 150, 120)))
    for k in range(0, W, 90):
        c.drawRect(skia.Rect(k, 0, k + 45, 1500), P(C(112, 140, 112)))
    c.drawRect(skia.Rect(620, 600, 1000, 1000), P(Shader=T.lin((0, 600), (0, 1000), [C(130, 190, 240), C(200, 230, 250)])))
    c.drawRect(skia.Rect(620, 600, 1000, 1000), S(C(240, 235, 225), 14))
    c.drawLine(810, 600, 810, 1000, S(C(240, 235, 225), 10))
    # wifi router on a shelf, all lights dead
    c.drawRect(skia.Rect(80, 1000, 420, 1024), P(C(120, 80, 45))); c.drawRect(skia.Rect(80, 1000, 420, 1024), S(OUT, 4))
    c.drawRoundRect(skia.Rect(160, 940, 340, 1000), 12, 12, P(C(230, 230, 235))); c.drawRoundRect(skia.Rect(160, 940, 340, 1000), 12, 12, S(OUT, 4))
    for k in range(4):
        c.drawCircle(190 + k * 40, 970, 8, P(C(90, 90, 95)))
    for sx in (190, 310):
        c.drawLine(sx, 940, sx - 10 + (sx - 250) * 0.2, 870, S(OUT, 6))
    return E.arr(s)


def sofa_front(c):
    c.drawRoundRect(skia.Rect(-40, 1440, W + 40, 1700), 60, 60, P(Shader=T.lin((0, 1440), (0, 1700), [C(200, 90, 70), C(160, 65, 50)])))
    c.drawRoundRect(skia.Rect(-40, 1440, W + 40, 1700), 60, 60, S(OUT, 6))
    c.drawRect(skia.Rect(-40, 1680, W + 40, H), P(Shader=T.lin((0, 1680), (0, H), [C(150, 60, 45), C(100, 40, 30)])))
    c.drawLine(-40, 1680, W + 40, 1680, S(OUT, 6))
    for x in (360, 720):
        c.drawLine(x, 1700, x, H, S(C(0, 0, 0, 40), 6))


@lru_cache(maxsize=None)
def bg_airport():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(180, 200, 215), C(220, 225, 230)])))
    c.drawRect(skia.Rect(0, 1150, W, 1500), P(Shader=T.lin((0, 1150), (0, 1500), [C(140, 190, 240), C(200, 225, 245)])))
    for k in range(6):
        c.drawLine(k * 200, 1150, k * 200, 1500, S(C(90, 100, 110), 10))
    # a parked plane outside, going nowhere
    c.drawRoundRect(skia.Rect(200, 1330, 900, 1410), 40, 40, P(C(245, 245, 250))); c.drawRoundRect(skia.Rect(200, 1330, 900, 1410), 40, 40, S(OUT, 4))
    c.drawPath(path([(480, 1380), (700, 1380), (560, 1470)]), P(C(220, 225, 235))); c.drawPath(path([(480, 1380), (700, 1380), (560, 1470)]), S(OUT, 4))
    c.drawPath(path([(830, 1340), (900, 1250), (920, 1340)]), P(C(220, 70, 60))); c.drawPath(path([(830, 1340), (900, 1250), (920, 1340)]), S(OUT, 4))
    for k in range(7):
        c.drawCircle(300 + k * 70, 1360, 10, P(C(120, 170, 220)))
    c.drawRect(skia.Rect(0, 1150, W, 1500), S(OUT, 6))
    c.drawRect(skia.Rect(0, 1500, W, H), P(Shader=T.lin((0, 1500), (0, H), [C(200, 195, 185), C(160, 155, 145)])))
    for k in range(0, W, 160):
        c.drawLine(k, 1500, k - 250, H, S(C(140, 135, 125, 120), 3))
    c.drawLine(0, 1500, W, 1500, S(OUT, 5))
    return E.arr(s)


BOARD_ROWS = [("LONDON", "09:15"), ("DUBAI", "09:40"), ("TOKYO", "10:05"), ("NEW YORK", "10:30"), ("PARIS", "11:00"), ("SYDNEY", "11:20")]


def board(c, t, t0):
    x0, y0, x1 = 90, 580, 990
    c.drawRoundRect(skia.Rect(x0 - 20, y0 - 90, x1 + 20, y0 + 70 * len(BOARD_ROWS) + 20), 18, 18, P(C(25, 28, 35)))
    c.drawRoundRect(skia.Rect(x0 - 20, y0 - 90, x1 + 20, y0 + 70 * len(BOARD_ROWS) + 20), 18, 18, S(OUT, 6))
    text(c, "DEPARTURES", 540, y0 - 30, 46, C(255, 210, 80))
    for i, (city, tm) in enumerate(BOARD_ROWS):
        y = y0 + 20 + i * 70
        text(c, tm, x0 + 70, y + 36, 34, C(240, 240, 240))
        text(c, city, x0 + 300, y + 36, 34, C(240, 240, 240))
        u = clamp((t - (t0 + 0.12 * i)) / 0.18)      # split-flap flip
        sx = abs(math.cos(math.pi * u))
        c.save(); c.translate(x0 + 690, y + 24); c.scale(1, max(0.05, sx))
        c.drawRect(skia.Rect(-160, -26, 160, 26), P(C(50, 55, 65) if u < 0.5 else C(200, 40, 40)))
        text(c, "ON TIME" if u < 0.5 else "CANCELLED", 0, 12, 32, C(120, 230, 120) if u < 0.5 else C(255, 255, 255))
        c.restore()


@lru_cache(maxsize=None)
def bg_hospital():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(190, 225, 225), C(150, 200, 205)])))
    c.drawRect(skia.Rect(0, 1100, W, 1130), P(C(110, 170, 175)))
    # a dark computer (no network) and a big red cross sign
    c.drawRoundRect(skia.Rect(560, 620, 980, 760), 20, 20, P(C(250, 250, 250))); c.drawRoundRect(skia.Rect(560, 620, 980, 760), 20, 20, S(OUT, 5))
    c.drawRect(skia.Rect(590, 668, 640, 712), P(C(220, 50, 50))); c.drawRect(skia.Rect(593, 655, 637, 725), P(C(220, 50, 50)))
    text(c, "WARD 3", 820, 710, 60, C(60, 110, 120))
    c.drawRoundRect(skia.Rect(620, 1080, 980, 1350), 10, 10, P(C(40, 40, 45)))
    c.drawRect(skia.Rect(640, 1100, 960, 1330), P(C(15, 15, 20)))
    text(c, "OFFLINE", 800, 1230, 44, C(240, 70, 60))
    c.drawRoundRect(skia.Rect(620, 1080, 980, 1350), 10, 10, S(OUT, 5))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_office():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(40, 45, 65), C(70, 75, 100)])))
    return E.arr(s)


MON_GRID = [(150 + k * 195, 640 + j * 165) for j in range(4) for k in range(5)]


@lru_cache(maxsize=None)
def bg_lobby():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(20, 25, 50), C(50, 55, 90)])))
    c.drawRect(skia.Rect(DOOR_X, 560, W + 20, 1560), P(C(70, 80, 110)))             # building facade
    c.drawRect(skia.Rect(DOOR_X, 560, W + 20, 1560), S(OUT, 6))
    for j in range(3):
        for k in range(2):
            c.drawRect(skia.Rect(DOOR_X + 60 + k * 170, 600 + j * 120, DOOR_X + 160 + k * 170, 680 + j * 120), P(C(30, 35, 55)))
    # the glass door (on its plane x = DOOR_X), lobby dark inside
    c.drawRect(skia.Rect(DOOR_X, 1000, DOOR_X + 300, 1560), P(C(110, 160, 200, 200)))
    c.drawLine(DOOR_X + 150, 1000, DOOR_X + 150, 1560, S(C(60, 70, 90), 8))
    c.drawPath(path([(DOOR_X + 30, 1040), (DOOR_X + 80, 1040), (DOOR_X + 30, 1160)]), P(C(255, 255, 255, 80)))
    c.drawRect(skia.Rect(DOOR_X, 1000, DOOR_X + 300, 1560), S(OUT, 6))
    c.drawRect(skia.Rect(0, 1560, W, H), P(Shader=T.lin((0, 1560), (0, H), [C(90, 90, 100), C(60, 60, 70)])))
    c.drawLine(0, 1560, W, 1560, S(OUT, 5))
    return E.arr(s)


# =================================================================================== scenes
def sc_hook(t, f):
    img = np.array(bg_city(lit=False))
    tb = word_t("hook", "bread")
    ts = word_t("hook", "shut", "down")
    u = snap(t, ts, 6, 1.5)
    pose = dict(eyes=min(1.2, max(0.0, u)), brows="up", brow_lift=(lerp(0, 8, u),) * 2, mouth="O" if u > 0.05 else "smile",
                mouth_amt=lerp(0.4, 1.2, u), look=(0.5, -0.2), hands=[(-20, 120), (120, -150)], tilt=-4,
                blink=any(0 <= t - b < 0.1 for b in (0.4, 3.0)))
    x, y, s_ = 420, 1800, 2.05
    img = char(img, YOU, x, y, s_, pose, t)
    hx, hy = T.hand_pos(x, y, s_, pose, 1)
    img = layer_over(img, lambda c: (phone(c, hx + 50, hy - 40, 1.25, t, "none" if t > ts else "ok", -6),
                                     counter(c, 1560, top=(110, 80, 60), front=(70, 55, 45), stripe=(180, 140, 80))))
    lays = [E.title_layer(t, [("WHAT IF THE INTERNET", 84, 260, E.WHITE, -0.3), ("SHUT DOWN?", 150, 420, E.GOLD, ts)]),
            E.stamp_layer(t, "NO BREAD BY LUNCH", tb, 540, 1680, 92)]
    return img, cam("hook", [(0, 1.0, 540, 960), (2.5, 1.07, 540, 1000), (6.0, 1.13, 560, 1040)])(t), lays


def sc_minute(t, f):
    img = np.array(bg_living())
    ta = word_t("minute", "annoying")
    pose = dict(eyes="squint" if t > ta else "open", brows="angry" if t > ta else "up", mouth="disgust" if t > ta else "O", mouth_amt=0.7,
                look=(0.6, -0.3), hands=[(-20, 120), (120, -130)], tilt=-5)
    x, y, s_ = 380, 1830, 2.05
    img = char(img, YOU, x, y, s_, pose, t)
    hx, hy = T.hand_pos(x, y, s_, pose, 1)
    shake = 6 * math.sin(t * 40) if t > ta else 0

    def draw(c):
        phone(c, hx + 50 + shake, hy - 40, 1.2, t, "spin", -6 + shake * 0.5)
        for i, (k, w_) in enumerate((("msg", "messages"), ("map", "maps"), ("vid", "videos"))):
            tw = word_t("minute", w_)
            a = clamp((t - tw + 0.15) / 0.2)
            if a > 0:
                app_icon(c, 300 + 240 * i, 640, 0.9 * T.out_back(a, 1.6), k, clamp((t - tw - 0.15) / 0.2))
        sofa_front(c)
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("MINUTE 1", 140, 300, E.GOLD, word_t("minute", "minute", "one"))]),
            E.title_layer(t, [("ANNOYING...", 96, 450, E.WHITE, ta)]),
            E.stamp_layer(t, "...BUT FINE", word_t("minute", "fine"), 560, 1600, 110, (40, 140, 70), -6)]
    return img, cam("minute", [(0, 1.0, 540, 960), (6.5, 1.07, 560, 1000)])(t), lays


def sc_cards(t, f):
    img = np.array(F.bg_shop())
    tf = word_t("cards", "fail")
    tn = word_t("cards", "nobody")
    img = char(img, CASHIER, 250, 1760, 1.75, dict(eyes="open", brows="sad" if t > tf else "up", mouth="frown" if t > tf else "smile",
                                                    look=(0.7, 0), hands=[(-20, 120), (90, -10)] if t > tf else [(-20, 120), (20, 120)]), t)
    pose = dict(eyes="wide" if t > tn else "open", brows="up", mouth="O" if t > tn else "smile", look=(-0.3, 0.4) if t > tn else (-0.7, 0),
                hands=[(-20, 120), (-120, 70)], tilt=4)
    x, y, s_ = 800, 1800, 1.9
    img = char(img, YOU, x, y, s_, pose, t)
    hx, hy = T.hand_pos(x, y, s_, pose, -1)

    def draw(c):
        counter(c, 1560, top=(90, 90, 95), front=(60, 70, 85), stripe=(250, 220, 90))
        card_reader(c, 520, 1560, 1.1, t, tf)
        wallet(c, hx - 40, hy - 10, 1.0, t > tn - 0.2)
        if t > tn:     # moths fly out of the empty wallet: drag-limited climb + flutter
            for k in range(3):
                u = t - tn - 0.1 * k
                if u > 0:
                    mx = hx - 40 + (k - 1) * 70 * u + 25 * math.sin(u * 6 + k)
                    my = hy - 30 - 260 * (1 - math.exp(-1.2 * u)) / 1.2 * 1.6
                    moth(c, mx, my, t, k)
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("HOUR 1", 140, 300, E.GOLD, word_t("cards", "hour", "one"))]),
            E.stamp_layer(t, "DECLINED", tf, 540, 470, 120),
            E.title_layer(t, [("CASH ONLY", 96, 640, E.WHITE, word_t("cards", "cash"))])]
    return img, cam("cards", [(0, 1.0, 540, 960), (5.9, 1.07, 600, 1000)])(t), lays


def sc_flights(t, f):
    img = np.array(bg_airport())
    ts = word_t("flights", "stop") + 0.45        # after the word "stop" ends: the flips/stamp never mask "flights stop"
    img = layer_over(img, lambda c: board(c, t, ts))
    shrug = t > ts + 0.3
    pose = dict(eyes="sad" if shrug else "open", brows="sad" if shrug else "flat", mouth="frown" if shrug else "smile",
                hands=[(-120, -40), (120, -40)] if shrug else [(-20, 120), (20, 120)], look=(0, 0), tilt=-3 if shrug else 0)
    img = char(img, PILOT, 540, 1800, 1.55, pose, t, shadow=0.4)
    lays = [E.title_layer(t, [("HOUR 3", 140, 300, E.GOLD, word_t("flights", "hour", "three"))]),
            E.stamp_layer(t, "ALL FLIGHTS STOP", ts, 540, 1110, 96),
            E.title_layer(t, [("NO CHECK-IN. NO ROUTES.", 64, 1690, E.WHITE, word_t("flights", "check", "passengers"))])]
    return img, cam("flights", [(0, 1.0, 540, 960), (6.4, 1.06, 540, 990)])(t), lays


def sc_paper(t, f):
    img = np.array(bg_hospital())
    pose = dict(eyes="open", brows="up", mouth="smile", look=(0.6, 0.4), hands=[(-20, 120), (110, 0)], tilt=-4)
    img = char(img, NURSE, 330, 1790, 1.9, pose, t)

    def draw(c):
        counter(c, DESK_Y, top=(235, 235, 230), front=(90, 150, 160), stripe=(60, 110, 120))
        for y, landed, k in paper_stack(t):
            c.save(); c.translate(PAPER["x"] + (k % 3 - 1) * 6, y); c.rotate(0 if landed else (k % 2 - 0.5) * 10)
            c.drawRect(skia.Rect(-130, -SHEET_T, 130, 0), P(C(255, 255, 250))); c.drawRect(skia.Rect(-130, -SHEET_T, 130, 0), S(C(150, 150, 150), 2))
            c.restore()
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("HOSPITALS:", 100, 300, E.WHITE, word_t("paper", "hospitals")), ("BACK TO PAPER", 120, 450, E.GOLD, word_t("paper", "paper"))])]
    return img, cam("paper", [(0, 1.0, 540, 960), (1.1, 1.04, 560, 990)])(t), lays


def sc_trucks(t, f):
    img = np.array(F.bg_shop(empty=True))
    img = layer_over(img, lambda c: truck(c, 640, 1800, 1.3))
    img = char(img, F.DRIVER, 200, 1800, 1.45, dict(eyes="open", brows="sad", mouth="frown", look=(0.4, -0.2), hands=[(-90, -30), (90, -30)]), t, shadow=0.4)
    lays = [E.title_layer(t, [("NO ORDERS", 120, 300, E.GOLD, word_t("paper", "orders", "never"))]),
            E.stamp_layer(t, "EMPTY SHELVES", word_t("paper", "shelves"), 540, 520, 110)]
    return img, cam("trucks", [(0, 1.0, 540, 960), (4.2, 1.06, 560, 990)])(t), lays


def crash_t(i):
    return word_t("real", "crashed") + 0.05 * i


def sc_real(t, f):
    img = np.array(bg_office())

    def draw(c):
        for i, (x, y) in enumerate(MON_GRID):
            monitor(c, x, y, 160, 110, t >= crash_t(i), t)
        counter(c, 1560, top=(120, 110, 100), front=(70, 65, 60), stripe=None)
    img = layer_over(img, draw)
    facepalm = t > crash_t(0) + 0.4
    pose = dict(eyes="closed" if facepalm else "open", brows="sad", mouth="frown" if facepalm else "smile", look=(0, -0.3),
                hands=[(-70, -150), (70, -150)] if facepalm else [(-20, 120), (20, 120)], tilt=6 if facepalm else 0)
    img = char(img, WORKER, 540, 1820, 1.75, pose, t)
    img = layer_over(img, lambda c: counter(c, 1640, top=(120, 110, 100), front=(70, 65, 60), stripe=(50, 45, 40)))
    lays = [E.title_layer(t, [("NOT FICTION", 96, 280, E.WHITE, word_t("real", "fiction")), ("2024", 130, 410, E.GOLD, word_t("real", "2024"))]),
            E.stamp_layer(t, "8.5 MILLION PCs", word_t("real", "million"), 540, 900, 110),
            E.title_layer(t, [("FLIGHTS CANCELLED", 70, 1760, E.WHITE, word_t("real", "thousands"))])]
    return img, cam("real", [(0, 1.0, 540, 960), (8.7, 1.06, 540, 960)])(t), lays


def sc_twist(t, f):
    img = np.array(bg_lobby())
    tb = bonk_t()
    tc = word_t("twist", "cards")
    hit = clamp((t - tb) / 0.12) * (1 - clamp((t - tb - 1.2) / 0.4))
    pose = dict(eyes="squint" if t > tb else "open", brows="angry" if t > tc else ("sad" if t > tb else "up"),
                mouth="O" if t > tb else "smile", look=(0.8, 0), lean=-4 if t > tb else 4,
                hands=[(-20, 120), (110, -40)], tilt=-6 * hit, walk=(engineer_x(t) / 45.0) if t < tb else None)
    ex = engineer_x(t)

    def reader(c):     # the badge reader on the wall, behind him: red on "cards"
        red = t > tc and int((t - tc) * 4) % 2 == 0
        rx = DOOR_X + 330
        c.drawRoundRect(skia.Rect(rx, 1240, rx + 70, 1360), 12, 12, P(C(40, 40, 45)))
        c.drawCircle(rx + 35, 1275, 18, P(C(240, 50, 50) if red else (C(110, 40, 40) if t > tc else C(60, 200, 90))))
        if red:
            c.drawCircle(rx + 35, 1275, 60, P(Shader=T.rad(rx + 35, 1275, 60, [C(255, 60, 60, 140), C(255, 60, 60, 0)])))
        c.drawRoundRect(skia.Rect(rx, 1240, rx + 70, 1360), 12, 12, S(OUT, 4))
    img = layer_over(img, reader)
    img = char(img, ENGINEER, ex, 1830, 1.75, pose, t, shadow=0.4, rim_col=(0.7, 0.8, 1.0))
    hx, hy = T.hand_pos(ex, 1830, 1.75, pose, 1)

    def draw(c):
        # key card in his hand + the reader on the wall, red on "cards"
        c.drawRoundRect(skia.Rect(hx - 10, hy - 50, hx + 70, hy), 8, 8, P(C(250, 250, 250))); c.drawRoundRect(skia.Rect(hx - 10, hy - 50, hx + 70, hy), 8, 8, S(OUT, 3))
        if 0 < t - tb < 0.9:      # bonk stars
            for k in range(5):
                a = (t - tb) * 5 + k * 1.25
                c.drawCircle(ex + 40 + 70 * math.cos(a), 1120 + 30 * math.sin(a), 10, P(C(255, 230, 90)))
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("THE TWIST", 140, 280, E.GOLD, word_t("twist", "twist"))]),
            E.title_layer(t, [("2021: 6 HOURS OFFLINE", 70, 420, E.WHITE, word_t("twist", "offline"))]),
            E.stamp_layer(t, "LOCKED OUT!", tb + 0.05, 540, 620, 120) if t < tc - 0.05 else
            E.stamp_layer(t, "SAME NETWORK", tc, 540, 620, 110, (40, 70, 150), 6)]
    return img, cam("twist", [(0, 1.0, 540, 960), (tb - span("twist")[0], 1.08, 560, 1040), (10.0, 1.1, 560, 1020)])(t), lays


def sc_end(t, f):
    tb = word_t("end", "back")
    img = np.array(bg_city(lit=True, dusk=False)) if t > tb else np.array(bg_city(lit=False, dusk=False))
    if t > tb:      # the city lights wave back on: a bright flash fading out
        img[..., :3] = np.clip(img[..., :3] + 0.25 * math.exp(-(t - tb) * 3), 0, 1)
    pose = dict(eyes="squint" if t > tb else "open", brows="up", mouth="grin" if t > tb else "smile",
                hands=[(-60, -170), (60, -170)] if t > tb else [(-20, 120), (110, -120)], look=(0, -0.4))
    x, y, s_ = 540, 1840, 2.0
    img = char(img, YOU, x, y, s_, pose, t)

    def draw(c):
        if t <= tb:
            hx, hy = T.hand_pos(x, y, s_, pose, 1)
            phone(c, hx + 50, hy - 40, 1.2, t, "none", -6)
        else:
            for k in range(6):   # wifi signals pulse out over the city
                ph = ((t - tb) * 0.7 + k / 6) % 1.0
                cx, cy = 100 + k * 180, 820 + (k % 2) * 160
                for j in range(3):
                    r_ = (20 + 22 * j) * (0.6 + 0.6 * ph)
                    c.drawArc(skia.Rect(cx - r_, cy - r_, cx + r_, cy + r_), 225, 90, False, S(C(120, 230, 255, int(220 * (1 - ph))), 6))
        F.counter(c, 1600, top=(70, 70, 80), front=(45, 45, 55), stripe=(250, 210, 90))   # the balcony rail
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("MIDNIGHT", 130, 300, E.WHITE, word_t("end", "midnight"))]),
            E.stamp_layer(t, "IT'S BACK!", tb, 540, 560, 120, (40, 140, 70), -6) if t < word_t("end", "runs") - 0.3 else
            E.title_layer(t, [("IT RUNS EVERYTHING", 86, 560, E.GOLD, word_t("end", "runs"))])]
    return img, cam("end", [(0, 1.0, 540, 960), (7.0, 1.08, 540, 1010)])(t), lays


def sc_cta(t, f):
    from cta2 import draw_cta2
    img = E.gblur(np.array(bg_city(lit=True, dusk=False)), 10 * K)
    img[..., :3] *= 0.6
    t0 = span("cta")[0]
    s, c = E.surf(world=False)
    draw_cta2(c, max(0.0, t - t0), word_t("cta", "like") - t0, word_t("cta", "subscribe") - t0)
    return img, (1.08, 540, 1000), [E.arr(s)]


RENDER = {n: globals()["sc_" + n] for n, _ in SCENES}
NO_SPLAT = {"cta"}


def splat_cuts():
    return [CUTS[i] for i in range(1, len(SCENES)) if SCENES[i][0] not in NO_SPLAT]


def splat_layer(t):
    for i, tc in enumerate(splat_cuts(), start=1):
        k = t - tc
        if -4 / FPS <= k < 5 / FPS:
            u = smooth(clamp((k + 4 / FPS) / (4 / FPS) if k < 0 else 1 - k / (5 / FPS)))
            s, c = E.surf(world=False)
            r = random.Random(i)
            cx, cy = 540 + r.uniform(-120, 120), 960 + r.uniform(-200, 200)
            R_ = 1250 * u
            blob = skia.Path()
            blob.addCircle(cx, cy, R_)
            for j in range(14):
                a = r.uniform(0, 2 * math.pi)
                d = R_ * r.uniform(0.85, 1.1)
                blob.addCircle(cx + d * math.cos(a), cy + d * math.sin(a), R_ * r.uniform(0.12, 0.25))
            c.drawPath(blob, P(Shader=T.rad(cx, cy, max(1, R_), [C(255, 225, 120), C(235, 165, 40), C(190, 120, 25)])))
            return E.arr(s)
    return None


SHAKES = None


def render(f, out=None):
    global SHAKES
    if SHAKES is None:
        SHAKES = [word_t("hook", "shut", "down"), word_t("cards", "fail"), word_t("flights", "stop") + 0.45, word_t("real", "million"), bonk_t()]
    t = f / FPS
    name = SCENES[scene_at(t)][0]
    img, (z, cx, cy), lays = RENDER[name](t, f)
    shake = (0, 0)
    for at in SHAKES:
        kk = int((t - at) * FPS + 1e-6)
        if 0 <= kk < 3:
            shake = ((4, -3), (-3, 2), (1, -1))[kk]
    rgb = E.crop(img, z, cx, cy, shake)
    for lay in lays:
        rgb = E.comp_screen(rgb, lay)
    sp = splat_layer(t)
    if sp is not None:
        rgb = E.comp_screen(rgb, sp)
    rgb = E.finish(rgb, f)
    if t > DUR - 0.4:
        rgb *= clamp((DUR - t) / 0.4)
    out = out or os.path.join(OUT_FR, f"{f + 1:04d}.jpg")
    if out.endswith(".jpg"):
        Image.fromarray(np.clip(rgb * 255, 0, 255).astype(np.uint8)).save(out, quality=96, subsampling=0)
    else:
        E.save(rgb, out)
    return f


def physics_report():
    st = paper_stack(1e3)
    assert len(st) == PAPER["n"] and all(l and abs(y - (DESK_Y - k * SHEET_T)) < 1e-9 for y, l, k in st), "papers must rest exactly on the stack"
    for tt in np.arange(span("twist")[0], span("twist")[1], 1 / FPS):
        assert engineer_x(tt) + ENG_REACH <= DOOR_X + 1e-9, "the engineer must never pass the locked door"
    return dict(paper_fall_s=PHYS["paper_fall_s"], paper_land=paper_land_times(), bonk_t=bonk_t(), g_px=G_PX,
                scenes=[(n, round(a, 3)) for n, a in SCENES], dur=DUR)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "frames"
    rep = physics_report()
    json.dump(rep, open(os.path.join(D, "physics.json"), "w"), indent=1)
    print("duration", DUR, "s,", NF, "frames;", [(n, round(a, 2)) for n, a in SCENES])
    if mode == "stills":
        os.makedirs(os.path.join(D, "stills"), exist_ok=True)
        for ts in sys.argv[2].split(","):
            fr = int(round(float(ts) * FPS))
            render(fr, os.path.join(D, "stills", f"s_{float(ts):05.2f}.png"))
            print("still", ts, SCENES[scene_at(fr / FPS)][0], flush=True)
    else:
        os.makedirs(OUT_FR, exist_ok=True)
        todo = [fr for fr in range(NF) if os.environ.get("SKIP") != "1" or not os.path.exists(os.path.join(OUT_FR, f"{fr + 1:04d}.jpg"))]
        with Pool(int(os.environ.get("PROCS", "4"))) as pool:
            for j, _ in enumerate(pool.imap_unordered(render, todo, chunksize=4)):
                if j % 150 == 0:
                    print("frame", j, "/", len(todo), flush=True)
        print("done")
