"""YouTube Short: "What If Everything Was Free?" - a what-if explainer in the owner's favourite all-2D fortune-cookie style
(make_fortune.py / make_pringles.py): Skia-drawn sets, big close-up toons behind counters / carts / blankets, props in
front, title slams + stamps on their spoken words, gold splats, CTA v2. Voice: vidIQ "Chris".

Grounding: price controls that set prices too low produced shortages and long bread queues in the Soviet Union and in
Venezuela (2010s). Prices carry information about scarcity (Hayek, "The Use of Knowledge in Society", 1945).
Generic cartoon people, no brands.

Physics (solved, asserted, and reused by the audio/QC): items thrown in the cart fall under gravity and rest EXACTLY on
the pile top; the tumbleweed rolls without slipping (angle = distance / r) on the floor; rotten tomatoes fall and rest on
the ground; the twist price tag is a damped pendulum.

  python make_free.py stills 1.0,5.2  |  python make_free.py frames (PROCS=4)
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

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "free")
TIMES = json.load(open(os.path.join(D, "vo_final.wav.times.json")))
WORDS = json.load(open(os.path.join(D, "vo_final.wav.words.json")))
LINES = json.load(open(os.path.join(D, "lines_final.json")))
ORDER = [l["key"] for l in LINES]
DUR = round(min(64.6, max(61.5, TIMES["cta"] + 3.4)), 3)
NF = int(round(DUR * FPS))
OUT_FR = os.path.join(D, "frames")
G_PX = 3600.0
PHYS = {}
INK = C(30, 18, 14)
OUT = T.OUT


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


SCENES = [(k, 0.0 if k == "hook" else (TIMES["cta"] - 0.3 if k == "cta" else _cut(k))) for k in ORDER]
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
SHOPPER = dict(skin=(238, 196, 160), hair="neat", hair_col=(70, 45, 30), coat=(220, 80, 60), pants=(50, 60, 90), nose="small")
DRIVER = dict(skin=(225, 180, 145), hair="cap", hair_col=(40, 90, 160), coat=(70, 120, 170), pants=(60, 60, 70), nose="long", mustache=True)
FARMER = dict(skin=(230, 185, 150), hair="neat", hair_col=(120, 80, 40), coat=(70, 110, 160), pants=(70, 60, 50), nose="small", hat="bowler", apron=(200, 170, 110))
OFFICIAL = dict(skin=(232, 190, 160), hair="neat", hair_col=(40, 35, 30), coat=(90, 95, 100), vest=(60, 65, 70), pants=(50, 50, 55), nose="long", hat="bowler")
KID = dict(skin=(240, 200, 170), hair="kid", hair_col=(60, 40, 25), coat=(250, 200, 60), pants=(60, 90, 140), nose="small")
QUEUE = [dict(skin=s, hair=h, hair_col=hc, coat=co, pants=(55, 55, 60), nose="small")
         for s, h, hc, co in (((235, 195, 160), "neat", (40, 30, 25), (110, 90, 80)), ((225, 180, 150), "curly", (70, 45, 30), (90, 100, 120)),
                              ((240, 200, 170), "pigtails", (120, 80, 40), (140, 80, 80)), ((220, 175, 140), "grey", (200, 200, 205), (80, 90, 70)),
                              ((235, 190, 160), "kid", (50, 35, 25), (150, 120, 70)), ((230, 185, 150), "neat", (90, 60, 35), (70, 75, 95)))]


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


def counter(c, y, top=(150, 85, 45), front=(115, 60, 30), stripe=None):
    c.drawRect(skia.Rect(-60, y - 22, W + 60, y + 10), P(C(*top)))
    c.drawRect(skia.Rect(-60, y + 10, W + 60, H), P(Shader=T.lin((0, y), (0, H), [C(*front), C(*[v * 0.6 for v in front])])))
    for k in range(10):
        x = 40 + k * 115
        c.drawLine(x, y + 40, x, H, S(C(0, 0, 0, 30), 5))
    if stripe:
        c.drawRect(skia.Rect(-60, y + 90, W + 60, y + 130), P(C(*stripe)))
    c.drawLine(-60, y - 22, W + 60, y - 22, S(OUT, 5))
    c.drawLine(-60, y + 10, W + 60, y + 10, S(OUT, 5))


def text(c, txt, x, y, size, col, center=True):
    f = skia.Font(T.FB, size)
    w = f.measureText(txt)
    c.drawString(txt, x - w / 2 if center else x, y, f, P(col))


# =================================================================================== props
def product(c, x, y, kind, s=1.0, rot=0.0):
    """Small shelf/cart products, drawn with their BASE at (x, y). Returns nothing."""
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    if kind == "box":
        c.drawRect(skia.Rect(-45, -130, 45, 0), P(Shader=T.lin((-45, 0), (45, 0), [C(240, 180, 50), C(250, 210, 90)])))
        c.drawCircle(0, -80, 24, P(C(220, 60, 50)))
        c.drawRect(skia.Rect(-45, -130, 45, 0), S(OUT, 4))
    elif kind == "can":
        c.drawRoundRect(skia.Rect(-30, -80, 30, 0), 8, 8, P(Shader=T.lin((-30, 0), (30, 0), [C(60, 130, 200), C(120, 190, 240), C(50, 110, 180)])))
        c.drawRect(skia.Rect(-30, -55, 30, -30), P(C(250, 245, 230)))
        c.drawRoundRect(skia.Rect(-30, -80, 30, 0), 8, 8, S(OUT, 4))
    elif kind == "bottle":
        c.drawPath(path([(-16, -150), (16, -150), (16, -110), (32, -80), (32, 0), (-32, 0), (-32, -80), (-16, -110)]), P(C(90, 190, 120)))
        c.drawRect(skia.Rect(-32, -60, 32, -25), P(C(250, 240, 220)))
        c.drawPath(path([(-16, -150), (16, -150), (16, -110), (32, -80), (32, 0), (-32, 0), (-32, -80), (-16, -110)]), S(OUT, 4))
    elif kind == "jar":
        c.drawRoundRect(skia.Rect(-36, -90, 36, 0), 14, 14, P(C(230, 120, 70)))
        c.drawRect(skia.Rect(-38, -100, 38, -84), P(C(200, 60, 50)))
        c.drawRoundRect(skia.Rect(-36, -90, 36, 0), 14, 14, S(OUT, 4))
    c.restore()


def tv(c, x, y, s=1.0, rot=0.0):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    c.drawRoundRect(skia.Rect(-150, -190, 150, 0), 18, 18, P(C(40, 42, 50)))
    c.drawRoundRect(skia.Rect(-130, -172, 130, -20), 10, 10, P(Shader=T.lin((-130, -172), (130, -20), [C(90, 160, 220), C(40, 80, 150)])))
    c.drawPath(path([(-100, -160), (-40, -160), (-110, -60)]), P(C(255, 255, 255, 60)))
    c.drawRoundRect(skia.Rect(-150, -190, 150, 0), 18, 18, S(OUT, 5))
    c.restore()


def car(c, x, y, s=1.0, rot=0.0, col=(230, 70, 60)):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    body = skia.Path(); body.addRoundRect(skia.Rect(-180, -95, 180, -25), 30, 30)
    roof = path([(-100, -95), (-60, -150), (70, -150), (115, -95)])
    c.drawPath(roof, P(C(*col))); c.drawPath(roof, S(OUT, 5))
    c.drawPath(path([(-80, -98), (-52, -138), (0, -138), (0, -98)]), P(C(170, 220, 245)))
    c.drawPath(path([(12, -98), (12, -138), (62, -138), (95, -98)]), P(C(170, 220, 245)))
    c.drawPath(body, P(C(*col))); c.drawPath(body, S(OUT, 5))
    for wx in (-110, 110):
        c.drawCircle(wx, -25, 32, P(C(40, 40, 45))); c.drawCircle(wx, -25, 14, P(C(190, 190, 195))); c.drawCircle(wx, -25, 32, S(OUT, 4))
    c.restore()


def steak(c, x, y, s=1.0, rot=0.0):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    c.drawRoundRect(skia.Rect(-120, -30, 120, 0), 12, 12, P(C(240, 240, 235)))
    c.drawRoundRect(skia.Rect(-120, -30, 120, 0), 12, 12, S(OUT, 4))
    m = skia.Path(); m.addOval(skia.Rect(-95, -70, 95, -18))
    c.drawPath(m, P(C(200, 60, 70))); c.drawOval(skia.Rect(-40, -58, 10, -34), P(C(250, 220, 220)))
    c.drawPath(m, S(OUT, 4))
    c.restore()


def gift(c, x, y, s=1.0, rot=0.0, col=(120, 90, 200)):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    c.drawRect(skia.Rect(-80, -110, 80, 0), P(C(*col)))
    c.drawRect(skia.Rect(-12, -110, 12, 0), P(C(250, 220, 90)))
    c.drawRect(skia.Rect(-80, -110, 80, 0), S(OUT, 4))
    c.restore()


def loaf(c, x, y, s=1.0, rot=0.0):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    p = skia.Path(); p.addRoundRect(skia.Rect(-90, -70, 90, 0), 40, 40)
    c.drawPath(p, P(Shader=T.lin((0, -70), (0, 0), [C(225, 150, 70), C(180, 105, 45)])))
    for k in (-45, 0, 45):
        c.drawLine(k - 12, -58, k + 12, -40, S(C(250, 210, 150), 6))
    c.drawPath(p, S(OUT, 4))
    c.restore()


def price_tag(c, x, y, s, txt, flip=1.0, col=(255, 230, 90), swing=0.0):
    """A hanging price tag; flip in [-1,1] is its scale-x (a flip shows the other side)."""
    c.save(); c.translate(x, y); c.rotate(swing); c.scale(s * max(0.02, abs(flip)), s)
    c.drawLine(0, -40, 0, -10, S(OUT, 3))
    p = path([(-70, 0), (40, 0), (70, 30), (40, 60), (-70, 60)])
    c.drawPath(p, P(C(*col))); c.drawPath(p, S(OUT, 4))
    c.drawCircle(46, 30, 7, P(C(255, 255, 255))); c.drawCircle(46, 30, 7, S(OUT, 2))
    text(c, txt, -14, 44, 34 if len(txt) <= 5 else 28, C(40, 30, 25))
    c.restore()


# =================================================================================== physics
CART_BASE = 1760.0          # the cart's floor (inside, behind its wire front)
CART_X = 640.0
CART_ITEMS = [   # (spoken word cue, kind, height px, dx, scale)  - each lands ON the word
    (("rush", ("tvs",)), "tv", 190.0, -20.0, 1.0),
    (("rush", ("cars",)), "car", 150.0, 10.0, 0.9),
    (("rush", ("steak",)), "steak", 70.0, -30.0, 1.0),
    (("rush", ("take",), 2), "gift", 110.0, 40.0, 1.0),
    (("rush", ("ten",)), "box", 130.0, -50.0, 1.0),
    (("rush", ("ten",), 1, 0.14), "gift2", 110.0, 30.0, 1.0),
    (("rush", ("ten",), 1, 0.28), "can", 80.0, -10.0, 1.0),
]
DROP_H = 760.0


def cart_land_times():
    out = []
    for cue, kind, h, dx, s in CART_ITEMS:
        line, cands = cue[0], cue[1]
        nth = cue[2] if len(cue) > 2 else 1
        off = cue[3] if len(cue) > 3 else 0.0
        out.append(word_t(line, *cands, nth=nth) + off)
    return out


def cart_pile(t):
    """Item k is released sqrt(2h/g) before its word and falls straight down onto the pile top (sum of the heights of
    the items under it, x 0.9 for nesting). Returns [(kind, x, y_base, landed, s)] for the released items."""
    out = []
    top = CART_BASE
    fall = math.sqrt(2 * DROP_H / G_PX)
    for (cue, kind, h, dx, s), tl in zip(CART_ITEMS, cart_land_times()):
        rest = top
        u = t - (tl - fall)
        if u >= 0:
            y = rest - DROP_H + 0.5 * G_PX * u * u
            out.append((kind, CART_X + dx, min(y, rest), y >= rest, s))
        top = rest - h * 0.9
    PHYS["cart_fall_s"] = fall
    return out


FLOOR_BARE = 1790.0
WEED_R = 85.0


def weed_state(t, t0):
    """Tumbleweed rolling without slipping: x = x0 + v*u, angle = (x - x0)/r, centre exactly r above the floor."""
    u = max(0.0, t - t0)
    x0, v = -150.0, 330.0
    x = x0 + v * u
    return x, FLOOR_BARE - WEED_R, math.degrees((x - x0) / WEED_R)


GROUND_FIELD = 1640.0
TOMATOES = [(160, 1080), (300, 1150), (430, 1060), (700, 1120), (840, 1060), (960, 1140)]


def tomato_drop_times():
    t0 = word_t("rot", "rots")
    return [t0 + 0.25 + 0.33 * k for k in range(len(TOMATOES))]


def tomato_state(k, t):
    x, y0 = TOMATOES[k]
    td = tomato_drop_times()[k]
    u = t - td
    if u <= 0:
        return x, y0, False
    y = y0 + 0.5 * G_PX * u * u
    return x, min(y, GROUND_FIELD - 26), y >= GROUND_FIELD - 26


def tomato_land_times():
    return [td + math.sqrt(2 * (GROUND_FIELD - 26 - y0) / G_PX) for td, (x, y0) in zip(tomato_drop_times(), TOMATOES)]


def tag_swing(t, t0):
    """Damped pendulum (L = 0.4 m at 1 m = 900 px): theta = A e^(-bt) cos(w t)."""
    u = max(0.0, t - t0)
    w = math.sqrt(9.81 / 0.4)
    return 16 * math.exp(-0.9 * u) * math.cos(w * u)


# =================================================================================== 2D sets
@lru_cache(maxsize=None)
def bg_shop(empty=False):
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(60, 110, 120), C(95, 160, 160), C(70, 120, 125)])))
    for k in range(4):   # ceiling lamps glow
        c.drawCircle(135 + k * 270, 600, 220, P(Shader=T.rad(135 + k * 270, 600, 220, [C(255, 250, 220, 50), C(255, 250, 220, 0)])))
    r = random.Random(3)
    for row, y in enumerate((900, 1150, 1400)):
        c.drawRect(skia.Rect(30, y, 1050, y + 26), P(C(225, 225, 220)))
        c.drawRect(skia.Rect(30, y, 1050, y + 26), S(OUT, 4))
        if empty:
            for _ in range(3):   # a few crumbs and one sad toppled can
                c.drawCircle(r.uniform(80, 1000), y - 6, 6, P(C(200, 160, 90)))
            if row == 1:
                product(c, 760, y - 30, "can", 1.0, 90)
            continue
        x = 80
        while x < 1010:
            kind = r.choice(["box", "can", "bottle", "jar"])
            product(c, x, y, kind, 0.85)
            x += 82
    c.drawRect(skia.Rect(0, 1560, W, H), P(Shader=T.lin((0, 1560), (0, H), [C(230, 225, 215), C(180, 175, 165)])))
    for k in range(0, W, 120):
        c.drawLine(k, 1560, k - 200, H, S(C(150, 145, 135, 120), 3))
    c.drawLine(0, 1560, W, 1560, S(OUT, 5))
    return E.arr(s)


SHELF_TAGS = [(x, y) for y in (930, 1180, 1430) for x in range(110, 1000, 205)]


@lru_cache(maxsize=None)
def bg_bedroom():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(70, 80, 140), C(110, 120, 180)])))
    for k in range(0, W, 140):
        c.drawCircle(k + 70, 760, 10, P(C(255, 255, 255, 40)))
        c.drawCircle(k + 70, 1060, 10, P(C(255, 255, 255, 40)))
    c.drawRect(skia.Rect(600, 620, 1000, 1080), P(Shader=T.lin((0, 620), (0, 1080), [C(255, 210, 150), C(250, 240, 200)])))
    c.drawCircle(720, 760, 60, P(C(255, 240, 160)))
    c.drawRect(skia.Rect(600, 960, 1000, 1080), P(C(90, 140, 90)))
    # the truck parked outside, going nowhere
    c.drawRect(skia.Rect(700, 930, 930, 1030), P(C(240, 240, 235))); c.drawRect(skia.Rect(700, 930, 930, 1030), S(OUT, 4))
    c.drawRect(skia.Rect(930, 960, 990, 1030), P(C(220, 60, 50))); c.drawRect(skia.Rect(930, 960, 990, 1030), S(OUT, 4))
    for wx in (740, 890, 960):
        c.drawCircle(wx, 1035, 18, P(C(40, 40, 45)))
    c.drawRect(skia.Rect(600, 620, 1000, 1080), S(C(240, 235, 225), 14))
    c.drawLine(800, 620, 800, 1080, S(C(240, 235, 225), 10))
    # headboard
    c.drawRoundRect(skia.Rect(60, 1040, 760, 1500), 40, 40, P(C(140, 90, 55)))
    c.drawRoundRect(skia.Rect(60, 1040, 760, 1500), 40, 40, S(OUT, 5))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_field():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, 1300), [C(120, 170, 230), C(250, 220, 170)])))
    c.drawCircle(860, 700, 110, P(C(255, 230, 140)))
    c.drawPath(path([(-50, 1300), (300, 1150), (700, 1230), (1130, 1140), (1130, 1500), (-50, 1500)]), P(C(110, 160, 90)))
    for x, y in TOMATOES:     # tomato plants: stake + leafy bush (the fruit is drawn per frame)
        c.drawLine(x, y - 120, x, GROUND_FIELD, S(C(120, 85, 50), 8))
        for k in range(7):
            a = k / 7 * 2 * math.pi
            c.drawCircle(x + 70 * math.cos(a), y - 20 + 60 * math.sin(a) + 90, 50, P(C(60, 130, 60)))
        c.drawCircle(x, y + 70, 62, P(C(70, 145, 70)))
    c.drawRect(skia.Rect(0, GROUND_FIELD, W, H), P(Shader=T.lin((0, GROUND_FIELD), (0, H), [C(150, 105, 65), C(110, 75, 45)])))
    for k in range(6):
        c.drawLine(0, GROUND_FIELD + 30 + k * 50, W, GROUND_FIELD + 30 + k * 50, S(C(90, 60, 35, 120), 4))
    c.drawLine(0, GROUND_FIELD, W, GROUND_FIELD, S(OUT, 5))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_bakery():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(150, 95, 60), C(210, 150, 90)])))
    for row, y in enumerate((860, 1100)):    # bread racks, nearly empty
        c.drawRect(skia.Rect(60, y, 1020, y + 22), P(C(110, 70, 40))); c.drawRect(skia.Rect(60, y, 1020, y + 22), S(OUT, 4))
        if row == 0:
            loaf(c, 200, y, 0.8)
    # window: the queue outside, as silhouettes
    c.drawRect(skia.Rect(560, 1150, 1020, 1440), P(Shader=T.lin((0, 1150), (0, 1440), [C(170, 190, 210), C(200, 210, 220)])))
    for k in range(9):
        x = 590 + k * 50
        c.drawCircle(x, 1300, 20, P(C(70, 70, 90)))
        c.drawRoundRect(skia.Rect(x - 22, 1318, x + 22, 1440), 14, 14, P(C(70, 70, 90)))
    c.drawRect(skia.Rect(560, 1150, 1020, 1440), S(C(240, 230, 210), 12))
    counter(c, 1500, top=(235, 225, 205), front=(120, 75, 45), stripe=(200, 60, 50))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_street(muted=True):
    s, c = E.surf()
    sky = ((120, 130, 150), (175, 180, 190)) if muted else ((60, 50, 100), (240, 150, 110))
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, 1500), [C(*sky[0]), C(*sky[1])])))
    c.drawRect(skia.Rect(-20, 780, 560, 1560), P(C(150, 120, 105)))
    c.drawRect(skia.Rect(-20, 780, 560, 1560), S(C(40, 35, 35), 6))
    c.drawRect(skia.Rect(40, 820, 520, 930), P(C(60, 70, 80)))
    text(c, "BREAD", 280, 905, 90, C(230, 220, 195))
    c.drawRect(skia.Rect(80, 990, 330, 1250), P(C(70, 80, 95)))
    c.drawRect(skia.Rect(380, 1060, 520, 1560), P(C(95, 70, 55)))
    c.drawRect(skia.Rect(380, 1060, 520, 1560), S(C(40, 35, 35), 6))
    c.drawRect(skia.Rect(560, 900, 1100, 1560), P(C(130, 125, 125) if muted else C(160, 110, 90)))
    for k in range(3):
        for j in range(2):
            c.drawRect(skia.Rect(620 + k * 150, 960 + j * 220, 720 + k * 150, 1100 + j * 220), P(C(80, 90, 105) if muted else C(255, 210, 120)))
    c.drawRect(skia.Rect(0, 1560, W, H), P(Shader=T.lin((0, 1560), (0, H), [C(215, 220, 228) if muted else C(120, 110, 115), C(170, 175, 185) if muted else C(85, 80, 85)])))
    c.drawLine(0, 1560, W, 1560, S(OUT, 5))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_rays(col0=(40, 30, 70), col1=(120, 70, 140)):
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.rad(540, 1150, 1500, [C(*col1), C(*col0)])))
    for k in range(16):
        a0 = math.radians(k * 22.5)
        c.drawPath(path([(540, 1150), (540 + 2000 * math.cos(a0), 1150 + 2000 * math.sin(a0)),
                         (540 + 2000 * math.cos(a0 + 0.17), 1150 + 2000 * math.sin(a0 + 0.17))]), P(C(255, 255, 255, 22)))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_sky():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, 1500), [C(70, 150, 235), C(190, 230, 255)])))
    c.drawCircle(860, 760, 230, P(Shader=T.rad(860, 760, 230, [C(255, 250, 200, 150), C(255, 250, 200, 0)])))
    c.drawCircle(860, 760, 100, P(C(255, 240, 150)))
    c.drawPath(path([(-50, 1700), (250, 1500), (600, 1560), (900, 1470), (1130, 1530), (1130, H), (-50, H)]), P(C(110, 190, 90)))
    c.drawPath(path([(-50, 1800), (400, 1690), (1130, 1760), (1130, H), (-50, H)]), P(C(90, 170, 75)))
    return E.arr(s)


def cloud(c, x, y, s):
    for dx, dy, r in ((-60, 10, 50), (0, -20, 70), (70, 5, 55), (20, 25, 55)):
        c.drawCircle(x + dx * s, y + dy * s, r * s, P(C(255, 255, 255, 235)))


# =================================================================================== scenes
def sc_hook(t, f):
    img = np.array(bg_shop())
    tf = word_t("hook", "free")

    def tags(c):
        for i, (x, y) in enumerate(SHELF_TAGS):   # every price tag flips to FREE, a ripple from the centre
            d = abs(x - 540) / 540 + (y - 930) / 1000
            u = clamp((t - (tf + 0.05 + 0.25 * d)) / 0.22)
            flip = math.cos(math.pi * u)
            txt = f"${(i * 7) % 9 + 1}.99" if u < 0.5 else "FREE"
            price_tag(c, x, y + 40, 0.95, txt, flip, (255, 230, 90) if u < 0.5 else (120, 230, 120))
    img = layer_over(img, tags)
    te = word_t("hook", "empty")
    u = snap(t, tf, 6, 1.5)
    pose = dict(eyes=min(1.2, max(0.0, u)), brows="up", brow_lift=(lerp(0, 8, u),) * 2, mouth="O" if u > 0.05 else "smile",
                mouth_amt=lerp(0.4, 1.2, u), look=(0, -0.4), hands=[lerp2((-20, 120), (-60, -40), u), lerp2((20, 120), (60, -40), u)],
                blink=any(0 <= t - b < 0.1 for b in (0.5, 3.0)))
    img = char(img, SHOPPER, 540, 1820, 2.05, pose, t)
    img = layer_over(img, lambda c: counter(c, 1560, top=(80, 80, 85), front=(60, 70, 85), stripe=(250, 220, 90)))
    lays = [E.title_layer(t, [("WHAT IF EVERYTHING", 90, 260, E.WHITE, -0.3), ("WAS FREE?", 160, 430, E.GOLD, tf)]),
            E.stamp_layer(t, "EMPTY BY LUNCH", te, 540, 1650, 100)]
    return img, cam("hook", [(0, 1.0, 540, 960), (2.5, 1.07, 540, 1000), (6.2, 1.13, 540, 1040)])(t), lays


def sc_rush(t, f):
    img = np.array(bg_shop())
    a = span("rush")[0]
    greedy = t > word_t("rush", "grab")
    pose = dict(eyes="squint" if greedy else "open", brows="smug" if greedy else "up", mouth="grin", look=(0.6, -0.4),
                hands=[(-40, -90), (60, -150)] if greedy else [(-20, 120), (20, 120)], tilt=-6 if greedy else 0)
    img = char(img, SHOPPER, 250, 1830, 1.85, pose, t)

    def draw(c):
        for kind, x, y, landed, s in cart_pile(t):
            if kind == "tv":
                tv(c, x, y, s)
            elif kind == "car":
                car(c, x, y, s)
            elif kind == "steak":
                steak(c, x, y, s)
            elif kind == "gift":
                gift(c, x, y, s)
            elif kind == "gift2":
                gift(c, x, y, s, col=(60, 170, 120))
            else:
                product(c, x, y, kind, 1.2)
        # the cart's wire front (items show through the grid above and behind it)
        x0, x1, y0, y1 = CART_X - 330, CART_X + 330, 1430, CART_BASE + 20
        c.drawRoundRect(skia.Rect(x0, y0, x1, y1), 14, 14, P(C(200, 210, 220, 70)))
        for k in range(13):
            xx = x0 + k * 55
            c.drawLine(xx, y0, xx, y1, S(C(170, 180, 190), 6))
        for k in range(6):
            yy = y0 + k * 60
            c.drawLine(x0, yy, x1, yy, S(C(170, 180, 190), 6))
        c.drawRoundRect(skia.Rect(x0, y0, x1, y1), 14, 14, S(OUT, 6))
        for wx in (x0 + 60, x1 - 60):
            c.drawCircle(wx, y1 + 60, 40, P(C(50, 50, 55))); c.drawCircle(wx, y1 + 60, 40, S(OUT, 4))
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("DAY 1", 150, 300, E.GOLD, word_t("rush", "day", "one"))]),
            E.title_layer(t, [("NO PRICES. NO MONEY.", 70, 450, E.WHITE, word_t("rush", "prices"))]),
            E.stamp_layer(t, "TAKE 10!", word_t("rush", "ten"), 820, 640, 120, (220, 35, 45), 8)]
    return img, cam("rush", [(0, 1.0, 540, 960), (8.0, 1.08, 600, 1000)])(t), lays


def sc_bare(t, f):
    img = np.array(bg_shop(empty=True))
    a = span("bare")[0]
    td = word_t("bare", "dry")
    img = char(img, SHOPPER, 280, FLOOR_BARE, 1.45, dict(eyes="sad", brows="sad", mouth="frown", look=(0.5, 0), hands=[(-20, 130), (60, 40)]),
               t, shadow=0.4)

    def draw(c):
        # the gas pump (right), its display blinking EMPTY after "dry"
        x, y = 860, FLOOR_BARE
        c.drawRoundRect(skia.Rect(x - 110, y - 460, x + 110, y), 20, 20, P(C(220, 60, 50)))
        c.drawRoundRect(skia.Rect(x - 110, y - 460, x + 110, y), 20, 20, S(OUT, 5))
        c.drawRect(skia.Rect(x - 80, y - 420, x + 80, y - 310), P(C(30, 35, 30)))
        blink = t > td and int((t - td) * 3) % 2 == 0
        text(c, "EMPTY" if t > td else "0.00", x, y - 345, 46, C(255, 90, 70) if blink or t <= td else C(120, 40, 35))
        c.drawRoundRect(skia.Rect(x + 110, y - 300, x + 150, y - 200), 10, 10, P(C(40, 40, 45)))
        c.drawLine(x + 150, y - 250, x + 190, y - 120, S(C(40, 40, 45), 10))
        # tumbleweed: rolls without slipping across the floor
        wx, wy, ang = weed_state(t, a + 0.3)
        c.save(); c.translate(wx, wy); c.rotate(ang)
        for k in range(9):
            r_ = WEED_R * (0.5 + 0.06 * k)
            c.drawArc(skia.Rect(-r_, -r_, r_, r_), k * 40, 250, False, S(C(160, 120, 70), 5))
        c.restore()
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("SHELVES:", 90, 300, E.WHITE, word_t("bare", "shelves")), ("BARE", 170, 470, E.GOLD, word_t("bare", "bare"))]),
            E.stamp_layer(t, "NO GAS", td, 820, 1100, 120, (220, 35, 45), -8)]
    return img, cam("bare", [(0, 1.0, 540, 980), (4.5, 1.06, 560, 1010)])(t), lays


def sc_work(t, f):
    img = np.array(bg_bedroom())
    a = span("work")[0]
    tw = word_t("work", "worthless")
    th = word_t("work", "home")
    pose = dict(eyes="squint" if t > th else "open", brows="smug" if t > th else "flat", mouth="grin" if t > th else "smile",
                hands=[(-40, -20), (40, -20)] if t > th else [(-20, 120), (60, -40)], look=(0.4, -0.3), tilt=-4)
    img = char(img, DRIVER, 380, 1800, 1.95, pose, t)

    def draw(c):
        # the blanket (covers him like a counter) and the ringing alarm clock
        c.drawRect(skia.Rect(-60, 1480, 820, H), P(Shader=T.lin((0, 1480), (0, H), [C(90, 160, 210), C(50, 100, 150)])))
        for k in range(8):
            c.drawLine(-60 + k * 120, 1480, -20 + k * 120, H, S(C(255, 255, 255, 40), 12))
        c.drawRoundRect(skia.Rect(-60, 1450, 820, 1520), 30, 30, P(C(240, 240, 235)))
        c.drawLine(-60, 1480, 820, 1480, S(OUT, 5))
        c.drawRect(skia.Rect(820, 1500, 1100, H), P(C(120, 75, 45))); c.drawRect(skia.Rect(820, 1500, 1100, H), S(OUT, 5))
        ring = t < th and int(t * 14) % 2 == 0
        cx, cy = 960 + (4 if ring else -4) * (t < th), 1420
        c.drawCircle(cx, cy, 70, P(C(230, 70, 60))); c.drawCircle(cx, cy, 56, P(C(250, 250, 245)))
        c.drawLine(cx, cy, cx, cy - 40, S(OUT, 6)); c.drawLine(cx, cy, cx + 28, cy, S(OUT, 6))
        c.drawCircle(cx, cy, 70, S(OUT, 5))
        for sx in (-1, 1):
            c.drawCircle(cx + sx * 50, cy - 62, 22, P(C(230, 200, 60))); c.drawCircle(cx + sx * 50, cy - 62, 22, S(OUT, 4))
        c.drawLine(cx - 40, cy + 60, cx - 55, 1500, S(OUT, 8)); c.drawLine(cx + 40, cy + 60, cx + 55, 1500, S(OUT, 8))
        if t < th:
            for k in range(3):
                rr = 90 + 25 * k + 12 * math.sin(t * 20)
                c.drawArc(skia.Rect(cx - rr, cy - rr, cx + rr, cy + rr), -60, 40, False, S(C(255, 255, 255, 180), 6))
                c.drawArc(skia.Rect(cx - rr, cy - rr, cx + rr, cy + rr), 200, 40, False, S(C(255, 255, 255, 180), 6))
        # the paycheck: drifts down (drag-limited) and lands on the blanket
        if t > tw - 0.6:
            u = t - (tw - 0.6)
            y = min(900 + 260 * u, 1462)
            x = 660 + (40 * math.sin(u * 4) if y < 1462 else 0)
            ang = 18 * math.sin(u * 4) if y < 1462 else -6
            c.save(); c.translate(x, y); c.rotate(ang)
            c.drawRect(skia.Rect(-110, -45, 110, 45), P(C(200, 235, 200))); c.drawRect(skia.Rect(-110, -45, 110, 45), S(OUT, 4))
            text(c, "PAY $0.00", 0, 12, 34, C(40, 90, 50))
            c.restore()
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("DAY 2", 150, 300, E.GOLD, word_t("work", "day", "two"))]),
            E.stamp_layer(t, "WORTHLESS", tw, 540, 520, 120),
            E.title_layer(t, [("FARMERS STOP", 86, 1700, E.WHITE, word_t("work", "farmers"))])]
    return img, cam("work", [(0, 1.0, 540, 980), (4.0, 1.06, 520, 1000), (7.5, 1.1, 560, 1030)])(t), lays


def sc_rot(t, f):
    img = np.array(bg_field())
    tr = word_t("rot", "rots")
    img = char(img, FARMER, 870, 1830, 1.45, dict(eyes="sad", brows="sad", mouth="frown", look=(-0.6, 0.2), hands=[(-50, 20), (50, 20)]), t, shadow=0.4)

    def draw(c):
        for k in range(len(TOMATOES)):
            x, y, landed = tomato_state(k, t)
            rot = clamp((t - tr + 0.2) / 1.0)
            col = (int(lerp(225, 120, rot)), int(lerp(45, 85, rot)), int(lerp(40, 40, rot)))
            if landed:
                c.drawOval(skia.Rect(x - 38, y + 4, x + 38, y + 26), P(C(110, 70, 35, 160)))
                c.drawOval(skia.Rect(x - 32, y - 18, x + 32, y + 26), P(C(*col)))
                c.drawOval(skia.Rect(x - 32, y - 18, x + 32, y + 26), S(OUT, 3))
            else:
                c.drawCircle(x, y, 28, P(C(*col))); c.drawCircle(x, y, 28, S(OUT, 3))
                c.drawLine(x, y - 28, x + 6, y - 40, S(C(60, 120, 50), 5))
            if rot > 0.4:     # flies circling the rotten ones
                for j in range(2):
                    ph = t * 7 + k * 2 + j * 3
                    c.drawCircle(x + 45 * math.cos(ph), y - 60 + 20 * math.sin(ph * 1.3), 5, P(C(30, 30, 30)))
        # the delivery truck, parked: NOBODY delivers
        x, y = 200, 1700
        c.drawRect(skia.Rect(x - 170, y - 230, x + 120, y - 40), P(C(240, 240, 235))); c.drawRect(skia.Rect(x - 170, y - 230, x + 120, y - 40), S(OUT, 5))
        c.drawRect(skia.Rect(x + 120, y - 170, x + 230, y - 40), P(C(70, 120, 170))); c.drawRect(skia.Rect(x + 120, y - 170, x + 230, y - 40), S(OUT, 5))
        for wx in (x - 110, x + 170):
            c.drawCircle(wx, y - 30, 38, P(C(40, 40, 45))); c.drawCircle(wx, y - 30, 38, S(OUT, 4))
        text(c, "CLOSED", x - 25, y - 120, 44, C(200, 50, 45))
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("FOOD ROTS", 150, 330, E.GOLD, tr)]),
            E.title_layer(t, [("NOBODY DELIVERS", 80, 480, E.WHITE, word_t("rot", "delivers", "nobody"))])]
    return img, cam("rot", [(0, 1.0, 540, 980), (3.0, 1.06, 560, 1020)])(t), lays


def sc_ration(t, f):
    img = np.array(bg_bakery())
    tl = word_t("ration", "loaf")
    tq = word_t("ration", "lines")
    pose = dict(eyes="open", brows="flat", mouth="frown", look=(0, 0), hands=[(-20, 120), (110, -60)] if t > tl - 0.3 else [(-20, 120), (20, 120)])
    img = char(img, OFFICIAL, 330, 1780, 1.95, pose, t, rim_col=(1.0, 0.8, 0.6))
    if t > tl - 0.3:
        hx, hy = T.hand_pos(330, 1780, 1.95, pose, 1)
        img = layer_over(img, lambda c: loaf(c, hx + 60, hy + 30, 1.0, -8))
    img = layer_over(img, lambda c: counter(c, 1560, top=(235, 225, 205), front=(120, 75, 45), stripe=(200, 60, 50)))
    lays = [E.title_layer(t, [("1 LOAF", 160, 320, E.GOLD, tl), ("PER PERSON", 100, 470, E.WHITE, word_t("ration", "person"))]),
            E.stamp_layer(t, "THE LINE >>>", tq, 560, 700, 96, (220, 35, 45), -6)]
    return img, cam("ration", [(0, 1.0, 540, 980), (tq - span("ration")[0], 1.04, 560, 1000), (5.6, 1.18, 790, 1260)])(t), lays


def sc_real(t, f):
    """Real history, told plainly: muted palette, no jokes."""
    img = np.array(bg_street())
    for i, look in enumerate(QUEUE + QUEUE[:2]):
        x = 300 + i * 110
        s_ = 1.05 - 0.03 * i
        pose = dict(eyes="sad" if i % 2 else "open", brows="sad", mouth="frown", look=(-0.7, 0), hands=[(-20, 130), (20, 130)],
                    blink=(t * 0.7 + i * 0.37) % 3 < 0.05)
        img = char(img, look, x, 1720 + (i % 2) * 14, s_, pose, t, shadow=0.35, rim=0.2, rim_col=(0.75, 0.8, 0.9))
    img = char(img, QUEUE[1], 180, 1760, 1.15, dict(eyes="sad", brows="sad", mouth="frown", look=(0.6, 0), hands=[(-20, 130), (20, 130)]), t,
               shadow=0.35, rim=0.2)

    def snow(c):
        for i in range(70):
            x0 = (i * 151) % W
            ph = t * (60 + (i % 5) * 15) + i * 37
            y = (ph % (H + 40)) - 20
            c.drawCircle(x0 + 15 * math.sin(t + i), y, 4 + (i % 3), P(C(255, 255, 255, 200)))
    img = layer_over(img, snow)
    lum = img[..., :3].mean(axis=2, keepdims=True)
    img[..., :3] = img[..., :3] * 0.6 + lum * 0.4 * np.array([0.95, 1.0, 1.08], np.float32)
    grey = [C(235, 235, 240), C(190, 195, 205)]
    lays = [E.title_layer(t, [("NOT FICTION", 96, 300, grey, word_t("real", "fiction")),
                              ("SOVIET UNION", 110, 440, E.GOLD, word_t("real", "soviet")),
                              ("& VENEZUELA", 110, 570, E.GOLD, word_t("real", "venezuela"))]),
            E.stamp_layer(t, "HOURS FOR BREAD", word_t("real", "bread"), 560, 1180, 96, (200, 40, 45), -4)]
    return img, cam("real", [(0, 1.0, 540, 960), (7.0, 1.06, 600, 990)])(t), lays


def sc_twist(t, f):
    img = np.array(bg_rays())
    a = span("twist")[0]
    tt = word_t("twist", "tell")
    u = snap(t, word_t("twist", "twist"), 6, 1.5)
    pose = dict(eyes=min(1.2, max(0.0, u)), brows="up", mouth="O", mouth_amt=0.9, look=(0.2, -0.9), hands=[(-50, -60), (50, -60)])
    img = char(img, SHOPPER, 540, 1900, 2.0, pose, t)

    def draw(c):
        if t > tt - 0.2:   # signal rings pulse out of the tag
            for k in range(3):
                ph = ((t - tt) * 0.8 + k / 3) % 1.0
                r_ = 120 + 420 * ph
                c.drawCircle(540, 900, r_, S(C(255, 230, 120, int(200 * (1 - ph))), 8))
        c.drawCircle(540, 900, 260, P(Shader=T.rad(540, 900, 260, [C(255, 230, 120, 120), C(255, 230, 120, 0)])))
        price_tag(c, 540, 860, 2.6, "$", 1.0, (255, 220, 80), swing=tag_swing(t, a + 0.1))
        counter(c, 1560, top=(80, 70, 100), front=(60, 45, 85), stripe=(250, 210, 90))
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("THE TWIST", 140, 300, E.GOLD, word_t("twist", "twist"))]),
            E.title_layer(t, [("PRICES = SIGNALS", 86, 450, E.WHITE, tt)]),
            E.stamp_layer(t, "WHAT'S RARE", word_t("twist", "rare"), 540, 640, 84, (220, 35, 45), -8) if t < word_t("twist", "worth", "making") - 0.05
            else E.stamp_layer(t, "WORTH MAKING", word_t("twist", "worth", "making"), 540, 640, 84, (40, 140, 70), 6)]
    return img, cam("twist", [(0, 1.0, 540, 960), (6.2, 1.06, 540, 940)])(t), lays


def sc_air(t, f):
    img = np.array(bg_sky())
    a = span("air")[0]
    breath = 0.5 + 0.5 * math.sin((t - a) * 2.2)
    pose = dict(eyes="closed" if breath > 0.5 else "squint", brows="up", mouth="smile" if breath > 0.5 else "O", mouth_amt=0.5,
                hands=[(-120, -120), (120, -120)], tilt=0, squash=0.04 * breath)

    def back(c):
        for k, (x0, y, s) in enumerate(((100, 760, 1.2), (600, 640, 0.9), (950, 900, 1.0))):
            cloud(c, (x0 + 30 * (t - a)) % (W + 300) - 150, y, s)
        for k in range(4):      # birds: gliding v's
            bx = (200 + k * 230 + 60 * (t - a)) % (W + 100) - 50
            by = 1000 + 40 * k + 10 * math.sin(t * 3 + k)
            fl = 14 * math.sin(t * 9 + k)
            c.drawPath(path([(bx - 26, by - fl), (bx, by), (bx + 26, by - fl)], close=False), S(C(40, 50, 70), 5))
    img = layer_over(img, back)
    img = char(img, KID, 540, 1800, 1.75, pose, t, shadow=0.3, rim_col=(1.0, 0.95, 0.8))

    def wind(c):
        for k in range(6):
            ph = ((t - a) * 0.6 + k / 6) % 1.0
            x = -200 + 1500 * ph
            y = 1150 + 90 * k
            c.drawPath(path([(x, y), (x + 140, y - 10), (x + 220, y + 10)], close=False), S(C(255, 255, 255, int(200 * math.sin(math.pi * ph))), 6))
    img = layer_over(img, wind)
    lays = [E.title_layer(t, [("AIR IS FREE", 140, 320, E.GOLD, word_t("air", "air"))]),
            E.title_layer(t, [("ENOUGH FOR EVERYONE", 72, 470, E.WHITE, word_t("air", "enough"))])]
    return img, cam("air", [(0, 1.0, 540, 960), (5.2, 1.06, 540, 1000)])(t), lays


def sc_end(t, f):
    img = np.array(bg_street(muted=False))
    a = span("end")[0]
    tline = word_t("end", "line")
    for i, look in enumerate(QUEUE):
        x = 260 + i * 120
        pose = dict(eyes="squint" if i % 2 else "open", brows="flat", mouth="frown", look=(-0.7, 0), hands=[(-20, 130), (20, 130)])
        img = char(img, look, x, 1720 + (i % 2) * 14, 1.0 - 0.03 * i, pose, t, shadow=0.35, rim=0.3)
    chk = (t - a) % 2.4 < 1.2
    pose = dict(eyes="sad" if chk else "open", brows="sad", mouth="frown", look=(0.3, 0.6) if chk else (-0.7, 0),
                hands=[(-20, 130), (20, 30)] if chk else [(-20, 130), (20, 130)], tilt=4)
    img = char(img, SHOPPER, 990, 1830, 1.5, pose, t, shadow=0.4)
    lays = [E.title_layer(t, [("NOTHING IS FREE", 100, 300, E.WHITE, word_t("end", "nothing")),
                              ("SOMEONE ALWAYS PAYS", 80, 440, E.GOLD, word_t("end", "pays", "always"))]),
            (E.stamp_layer(t, "TIME", word_t("end", "time"), 540, 640, 120, (220, 35, 45), -8) if t < word_t("end", "effort") - 0.05 else
             E.stamp_layer(t, "EFFORT", word_t("end", "effort"), 540, 640, 120, (40, 70, 150), 7) if t < tline - 0.05 else
             E.stamp_layer(t, "A LONG LINE", tline, 540, 640, 120, (220, 35, 45), -4))]
    return img, cam("end", [(0, 1.0, 540, 960), (4.0, 1.04, 620, 990), (7.6, 1.1, 780, 1030)])(t), lays


def sc_cta(t, f):
    from cta2 import draw_cta2
    img = E.gblur(np.array(bg_shop()), 10 * K)
    img[..., :3] *= 0.55
    t0 = span("cta")[0]
    s, c = E.surf(world=False)
    draw_cta2(c, max(0.0, t - t0), word_t("cta", "like") - t0, word_t("cta", "subscribe") - t0)
    return img, (1.08, 540, 1000), [E.arr(s)]


RENDER = {n: globals()["sc_" + n] for n, _ in SCENES}
NO_SPLAT = {"cta", "real"}         # into the real-history queue: a slow dip, not a gold splat (tone)


def splat_cuts():
    return [CUTS[i] for i in range(1, len(SCENES)) if SCENES[i][0] not in NO_SPLAT and SCENES[i - 1][0] != "real"]


def dip_real(t):
    for i in range(1, len(SCENES)):
        if SCENES[i][0] == "real" or SCENES[i - 1][0] == "real":
            k = t - CUTS[i]
            if abs(k) < 0.25:
                return 1 - abs(k) / 0.25
    return 0.0


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
        SHAKES = [word_t("hook", "free"), word_t("rush", "ten"), word_t("bare", "bare"), word_t("ration", "loaf"), word_t("end", "line")]
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
    d = dip_real(t)
    if d > 0:
        rgb *= (1 - 0.9 * d)
    if t > DUR - 0.4:
        rgb *= clamp((DUR - t) / 0.4)
    out = out or os.path.join(OUT_FR, f"{f + 1:04d}.jpg")
    if out.endswith(".jpg"):
        Image.fromarray(np.clip(rgb * 255, 0, 255).astype(np.uint8)).save(out, quality=96, subsampling=0)
    else:
        E.save(rgb, out)
    return f


def physics_report():
    pile = cart_pile(1e3)
    top = CART_BASE
    for (kind, x, y, landed, s), (cue, k2, h, dx, s2) in zip(pile, CART_ITEMS):
        assert landed and abs(y - top) < 1e-9, f"{kind} must rest exactly on the pile top"
        top -= h * 0.9
    for tt in np.arange(0, 6, 1 / FPS):
        x, y, ang = weed_state(tt, 0.0)
        assert abs(y + WEED_R - FLOOR_BARE) < 1e-9 and abs(math.radians(ang) * WEED_R - (x + 150.0)) < 1e-6, "tumbleweed must roll without slipping"
    for k in range(len(TOMATOES)):
        x, y, landed = tomato_state(k, 1e3)
        assert landed and abs(y - (GROUND_FIELD - 26)) < 1e-9, "tomatoes must rest on the ground"
    return dict(cart_fall_s=PHYS["cart_fall_s"], cart_land=cart_land_times(), tomato_land=tomato_land_times(), g_px=G_PX,
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
