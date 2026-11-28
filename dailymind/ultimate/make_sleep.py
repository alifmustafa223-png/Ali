"""YouTube Short: "What If Everyone Stopped Sleeping?" - what-if explainer in the owner's favourite all-2D fortune-cookie
style (make_fortune.py / make_free.py / make_offline.py). Voice: vidIQ "Chris".

Grounding: ~24 h awake impairs performance about like a 0.10% blood alcohol level (Dawson & Reid, Nature 1997);
microsleeps of a few seconds occur under sleep deprivation; perceptual distortions/hallucinations commonly appear after
~48-72 h awake. Randy Gardner, 17, stayed awake ~264 h (11 days) in Dec 1963 - Jan 1964 for a San Diego science fair and
had hallucinations near the end. The glymphatic system clears brain waste mostly during sleep (Xie et al., Science 2013).
Guinness World Records stopped accepting sleep-deprivation records because of the health risks. No logos are drawn.

Physics (solved + asserted, reused by audio/QC): torn calendar pages fall with air drag (terminal speed) and rest on the
floor; the coffee pot's last drop falls under gravity into the cup.

  python make_sleep.py stills 1.0,5.2  |  python make_sleep.py frames (PROCS=4)
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
import make_free as F          # shared 2D props (counter, text, ...); its timing is not used here

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "sleep")
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
YOU = dict(skin=(238, 196, 160), hair="neat", hair_col=(70, 45, 30), coat=(120, 110, 200), pants=(50, 60, 90), nose="small")
RANDY = dict(skin=(236, 198, 165), hair="neat", hair_col=(150, 100, 50), coat=(200, 70, 60), pants=(60, 70, 110), nose="small")
SCIENTIST = dict(skin=(230, 188, 155), hair="grey", hair_col=(210, 210, 215), coat=(245, 245, 240), pants=(60, 60, 70), nose="long", glasses=True)


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


def eye_bags(c, x, y, s_, strength):
    """Dark tired rings under the toon's eyes (drawn over the face, centred on the head)."""
    if strength <= 0:
        return
    hx, hy = x, y - 296 * s_ / 1.0 * 0.0
    for sx in (-1, 1):
        c.drawArc(skia.Rect(x + sx * 34 * s_ - 26 * s_, y - 28 * s_, x + sx * 34 * s_ + 26 * s_, y + 10 * s_), 20, 140, False,
                  S(C(110, 60, 120, int(200 * strength)), 6 * s_))


def head_centre(x, y, s_, pose):
    """Where the toon's head is (from toon's own hand-free geometry: the face sits above the body)."""
    ch = T.hand_pos(x, y, s_, dict(pose, hands=[(0, 0), (0, 0)]), 1)
    return ch


# =================================================================================== props
def bed_front(c, y=1480, col=(90, 120, 200)):
    c.drawRect(skia.Rect(-60, y, W + 60, H), P(Shader=T.lin((0, y), (0, H), [C(*col), C(*[int(v * 0.6) for v in col])])))
    for k in range(9):
        c.drawLine(-60 + k * 130, y, -20 + k * 130, H, S(C(255, 255, 255, 35), 12))
    c.drawRoundRect(skia.Rect(-60, y - 30, W + 60, y + 40), 30, 30, P(C(240, 240, 235)))
    c.drawLine(-60, y, W + 60, y, S(OUT, 5))


def wall_clock(c, x, y, r, t, spin=1.0):
    c.drawCircle(x, y, r, P(C(250, 245, 230))); c.drawCircle(x, y, r, S(OUT, 6))
    for k in range(12):
        a = k * math.pi / 6
        c.drawLine(x + 0.8 * r * math.cos(a), y + 0.8 * r * math.sin(a), x + 0.9 * r * math.cos(a), y + 0.9 * r * math.sin(a), S(OUT, 4))
    am = t * 2.2 * spin
    ah = am / 12
    c.drawLine(x, y, x + 0.75 * r * math.sin(am), y - 0.75 * r * math.cos(am), S(OUT, 5))
    c.drawLine(x, y, x + 0.5 * r * math.sin(ah), y - 0.5 * r * math.cos(ah), S(OUT, 8))


def cup(c, x, y, s=1.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    c.drawPath(path([(-50, -100), (50, -100), (40, 0), (-40, 0)]), P(C(250, 250, 245)))
    c.drawArc(skia.Rect(35, -85, 85, -30), -90, 180, False, S(C(250, 250, 245), 12))
    c.drawPath(path([(-50, -100), (50, -100), (40, 0), (-40, 0)]), S(OUT, 4))
    c.drawOval(skia.Rect(-48, -108, 48, -92), P(C(110, 65, 35)))
    c.restore()


def coffee_pot(c, x, y, s=1.0, rot=0.0, empty=False):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    c.drawPath(path([(-60, -150), (60, -150), (75, 0), (-75, 0)]), P(C(200, 220, 235, 200)))
    if not empty:
        c.drawPath(path([(-70, -50), (70, -50), (75, 0), (-75, 0)]), P(C(110, 65, 35)))
    c.drawRect(skia.Rect(-66, -175, 66, -150), P(C(40, 40, 45)))
    c.drawArc(skia.Rect(55, -140, 125, -40), -90, 180, False, S(C(40, 40, 45), 14))
    c.drawPath(path([(-60, -150), (60, -150), (75, 0), (-75, 0)]), S(OUT, 5))
    c.restore()


def car(c, x, y, s, col, rot=0.0, driver=None, t=0.0):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    c.drawPath(path([(-110, -95), (-70, -160), (80, -160), (120, -95)]), P(C(*col)))
    c.drawPath(path([(-88, -100), (-60, -146), (5, -146), (5, -100)]), P(C(170, 220, 245)))
    c.drawPath(path([(15, -100), (15, -146), (70, -146), (100, -100)]), P(C(170, 220, 245)))
    if driver:    # a sleepy head in the window, nodding
        nod = driver
        c.drawCircle(-30, -118 + 8 * nod, 24, P(C(238, 196, 160))); c.drawCircle(-30, -118 + 8 * nod, 24, S(OUT, 3))
        c.drawLine(-40, -120 + 8 * nod, -32, -120 + 8 * nod, S(OUT, 3)); c.drawLine(-26, -120 + 8 * nod, -18, -120 + 8 * nod, S(OUT, 3))
    c.drawPath(path([(-110, -95), (-70, -160), (80, -160), (120, -95)]), S(OUT, 5))
    body = skia.Path(); body.addRoundRect(skia.Rect(-190, -100, 190, -30), 30, 30)
    c.drawPath(body, P(C(*col))); c.drawPath(body, S(OUT, 5))
    c.drawCircle(178, -70, 12, P(C(255, 240, 160)))
    for wx in (-115, 115):
        c.drawCircle(wx, -30, 34, P(C(40, 40, 45))); c.drawCircle(wx, -30, 14, P(C(190, 190, 195))); c.drawCircle(wx, -30, 34, S(OUT, 4))
    c.restore()


def spook(c, kind, x, y, s, a, t):
    """Hallucinations: friendly-weird floating things (an eye, a fish, a wobbly shadow), see-through."""
    if a <= 0:
        return
    c.save(); c.translate(x, y); c.scale(s, s); c.rotate(10 * math.sin(t * 1.7 + x))
    al = int(220 * a)
    if kind == "eye":
        c.drawOval(skia.Rect(-70, -40, 70, 40), P(C(255, 255, 255, al)))
        c.drawCircle(15 * math.sin(t * 2), 0, 26, P(C(80, 160, 90, al))); c.drawCircle(15 * math.sin(t * 2), 0, 12, P(C(20, 20, 20, al)))
        c.drawOval(skia.Rect(-70, -40, 70, 40), S(C(30, 18, 14, al), 5))
    elif kind == "fish":
        c.drawOval(skia.Rect(-70, -32, 50, 32), P(C(255, 150, 60, al)))
        c.drawPath(path([(40, 0), (90, -40), (90, 40)]), P(C(255, 150, 60, al)))
        c.drawCircle(-40, -6, 7, P(C(20, 20, 20, al)))
    else:
        p = skia.Path()
        p.moveTo(-60, 60)
        for k in range(9):
            p.lineTo(-60 + k * 15, -40 + 18 * math.sin(t * 5 + k))
        p.lineTo(60, 60); p.close()
        c.drawPath(p, P(C(40, 20, 60, int(160 * a))))
        c.drawCircle(-20, -10, 8, P(C(255, 240, 100, al))); c.drawCircle(20, -10, 8, P(C(255, 240, 100, al)))
    c.restore()


def brain(c, x, y, s, t, clean=0.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    base = (255, 170, 185)
    lobes = ((-120, -40, 120), (0, -90, 130), (120, -40, 120), (-70, 60, 110), (80, 60, 110))
    for dx, dy, r in lobes:          # outline first (thick), fills on top: only the outer silhouette line remains
        c.drawCircle(dx, dy, r, S(OUT, 12))
    for dx, dy, r in lobes:
        c.drawCircle(dx, dy, r, P(C(*base)))
    for k in range(7):   # folds
        a0 = k * 0.9
        c.drawArc(skia.Rect(-150 + k * 40, -150 + (k % 3) * 60, -60 + k * 40, -60 + (k % 3) * 60), 200 + 30 * k, 140, False, S(C(220, 120, 140), 6))
    c.drawPath(path([(-30, 150), (30, 150), (20, 260), (-20, 260)]), P(C(240, 150, 165)))
    c.drawPath(path([(-30, 150), (30, 150), (20, 260), (-20, 260)]), S(OUT, 5))
    # cartoon face: happy once clean
    c.drawCircle(-50, -10, 14, P(OUT)); c.drawCircle(50, -10, 14, P(OUT))
    if clean > 0.5:
        c.drawArc(skia.Rect(-40, 10, 40, 60), 20, 140, False, S(OUT, 7))
    else:
        c.drawLine(-30, 40, 30, 40, S(OUT, 7))
    c.restore()


def record_book(c, x, y, s, stamp_u):
    c.save(); c.translate(x, y); c.scale(s, s)
    c.drawRoundRect(skia.Rect(-260, -320, 260, 320), 20, 20, P(C(30, 60, 140)))
    c.drawRoundRect(skia.Rect(-240, -300, 240, 300), 14, 14, P(C(240, 235, 220)))
    text(c, "RECORD BOOK", 0, -220, 52, C(30, 60, 140))
    c.drawRect(skia.Rect(-180, -180, 180, -176), P(C(30, 60, 140)))
    text(c, "LONGEST TIME", 0, -100, 40, C(60, 50, 40))
    text(c, "AWAKE:", 0, -50, 40, C(60, 50, 40))
    text(c, "11 DAYS", 0, 40, 74, C(200, 50, 45))
    for k in range(4):
        c.drawRect(skia.Rect(-180, 110 + k * 36, 180 - 60 * (k % 2), 120 + k * 36), P(C(180, 170, 150)))
    c.drawRoundRect(skia.Rect(-260, -320, 260, 320), 20, 20, S(OUT, 6))
    if stamp_u > 0:      # the big X: no longer tracked
        e = clamp(stamp_u)
        c.drawLine(-200, -60, -200 + 400 * e, -60 + 260 * e, S(C(220, 40, 40, 220), 26))
        c.drawLine(200, -60, 200 - 400 * e, -60 + 260 * e, S(C(220, 40, 40, 220), 26))
    c.restore()


# =================================================================================== physics
FLOOR_FAIR = 1720.0
PAGES = 10                     # day 1 -> day 11: ten pages torn off
PAGE_VT = 520.0                # terminal fall speed of a sheet of paper (px/s), drag time constant TAU
PAGE_TAU = 0.15
CAL = (790.0, 980.0)           # calendar position (top-centre of the pad)


def page_tear_times():
    a, b = word_t("real", "stayed") + 0.2, word_t("real", "days") + 0.05
    return [a + (b - a) * k / (PAGES - 1) for k in range(PAGES)]


def page_y(u, y0):
    """Fall with linear drag: v(u) = VT (1 - e^(-u/tau)), y(u) = y0 + VT (u - tau (1 - e^(-u/tau)))."""
    return y0 + PAGE_VT * (u - PAGE_TAU * (1 - math.exp(-u / PAGE_TAU)))


def page_land_u(y0):
    lo, hi = 0.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if page_y(mid, y0) < FLOOR_FAIR:
            lo = mid
        else:
            hi = mid
    return hi


def page_state(k, t):
    tt = page_tear_times()[k]
    y0 = CAL[1] + 90
    u = t - tt
    if u < 0:
        return None
    ul = page_land_u(y0)
    if u >= ul:
        return CAL[0] - 200 + 90 * math.sin(k * 1.7), FLOOR_FAIR, 0.0, True
    x = CAL[0] + 60 * math.sin(u * 5 + k) - 200 * clamp(u / ul) + 90 * math.sin(k * 1.7) * clamp(u / ul)
    return x, page_y(u, y0), 25 * math.sin(u * 6 + k), False


def page_land_times():
    y0 = CAL[1] + 90
    return [tt + page_land_u(y0) for tt in page_tear_times()]


CUP_TOP = 1400.0               # the coffee surface in the cup


def drop_t0():
    return word_t("night", "sells") - math.sqrt(2 * (CUP_TOP - 1190.0) / G_PX)


# =================================================================================== 2D sets
@lru_cache(maxsize=None)
def bg_bedroom(dark=1.0):
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(40, 45, 95), C(70, 70, 130)])))
    for k in range(0, W, 120):
        for j in range(5):
            c.drawCircle(k + 60 + (j % 2) * 60, 640 + j * 160, 8, P(C(255, 255, 255, 30)))
    c.drawRect(skia.Rect(620, 600, 1000, 1000), P(Shader=T.lin((0, 600), (0, 1000), [C(15, 20, 50), C(35, 40, 90)])))
    c.drawCircle(880, 720, 50, P(C(250, 240, 200)))
    r = random.Random(2)
    for _ in range(12):
        c.drawCircle(r.uniform(640, 980), r.uniform(620, 980), 3, P(C(255, 255, 230)))
    c.drawRect(skia.Rect(620, 600, 1000, 1000), S(C(230, 225, 215), 14))
    c.drawLine(810, 600, 810, 1000, S(C(230, 225, 215), 10))
    c.drawRoundRect(skia.Rect(80, 1020, 1000, 1500), 40, 40, P(C(110, 75, 55)))
    c.drawRoundRect(skia.Rect(80, 1020, 1000, 1500), 40, 40, S(OUT, 5))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_cafe(dawn=False):
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(120, 80, 60), C(170, 115, 80)])))
    sky = ((255, 190, 140), (255, 230, 180)) if dawn else ((20, 25, 60), (45, 50, 100))
    c.drawRect(skia.Rect(80, 600, 520, 1050), P(Shader=T.lin((0, 600), (0, 1050), [C(*sky[0]), C(*sky[1])])))
    if dawn:
        c.drawCircle(300, 1020, 90, P(C(255, 220, 120)))
    else:
        c.drawCircle(420, 690, 40, P(C(250, 240, 200)))
    c.drawRect(skia.Rect(80, 600, 520, 1050), S(C(240, 225, 200), 14))
    c.drawLine(300, 600, 300, 1050, S(C(240, 225, 200), 10))
    c.drawRect(skia.Rect(600, 640, 1040, 664), P(C(90, 55, 35))); c.drawRect(skia.Rect(600, 640, 1040, 664), S(OUT, 4))
    for k in range(4):     # empty coffee bags on the shelf (all gone but one, lying down)
        c.drawRect(skia.Rect(640 + k * 100, 560, 700 + k * 100, 640), P(C(60, 40, 30, 60)))
    c.drawRect(skia.Rect(600, 900, 1040, 924), P(C(90, 55, 35))); c.drawRect(skia.Rect(600, 900, 1040, 924), S(OUT, 4))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_road(night=True):
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, 1300), [C(25, 30, 70), C(90, 70, 120)])))
    for x, w_, h_ in ((-20, 200, 380), (170, 160, 500), (320, 220, 300), (530, 180, 560), (700, 200, 420), (890, 210, 480)):
        c.drawRect(skia.Rect(x, 1250 - h_, x + w_, 1250), P(C(40, 40, 70)))
        r = random.Random(x)
        for j in range(int(h_ / 70)):
            for k in range(int(w_ / 55)):
                if r.random() < 0.5:
                    c.drawRect(skia.Rect(x + 14 + k * 55, 1270 - h_ + j * 70, x + 40 + k * 55, 1300 - h_ + j * 70), P(C(255, 215, 120)))
    c.drawRect(skia.Rect(0, 1250, W, H), P(C(55, 55, 65)))
    for y in (1450, 1700):
        for k in range(8):
            c.drawRect(skia.Rect(k * 160, y, k * 160 + 90, y + 14), P(C(250, 220, 90)))
    c.drawLine(0, 1250, W, 1250, S(OUT, 5))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_office():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(150, 175, 190), C(190, 205, 210)])))
    c.drawRoundRect(skia.Rect(120, 620, 960, 1160), 16, 16, P(C(245, 245, 240)))   # whiteboard
    c.drawRoundRect(skia.Rect(120, 620, 960, 1160), 16, 16, S(OUT, 6))
    for k, (x0, y0, x1, y1) in enumerate(((200, 760, 520, 760), (200, 860, 700, 860), (200, 960, 440, 960))):
        c.drawLine(x0, y0, x1, y1, S(C(60, 110, 200), 10))
    c.drawPath(path([(620, 1080), (700, 960), (780, 1010), (880, 820)], close=False), S(C(220, 70, 60), 10))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_swirl():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.rad(540, 1100, 1400, [C(110, 50, 140), C(30, 15, 50)])))
    for k in range(10):
        r_ = 120 + k * 130
        c.drawArc(skia.Rect(540 - r_, 1100 - r_, 540 + r_, 1100 + r_), k * 37, 220, False, S(C(255, 255, 255, 20), 30))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_fair():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(190, 170, 140), C(220, 200, 170)])))
    for k in range(0, W, 180):   # gym wall panels
        c.drawLine(k, 520, k, 1500, S(C(160, 140, 110), 6))
    c.drawRect(skia.Rect(60, 560, 520, 840), P(C(250, 245, 230)))
    c.drawRect(skia.Rect(60, 560, 520, 840), S(OUT, 5))
    text(c, "SCIENCE FAIR", 290, 640, 54, C(170, 50, 45))
    text(c, "1964", 290, 720, 60, C(60, 90, 160))
    c.drawRect(skia.Rect(0, 1500, W, H), P(Shader=T.lin((0, 1500), (0, H), [C(200, 160, 110), C(160, 120, 80)])))
    for k in range(10):
        c.drawLine(0, 1540 + k * 45, W, 1540 + k * 45, S(C(130, 95, 60, 90), 3))
    c.drawLine(0, 1500, W, 1500, S(OUT, 5))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_brainroom():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.rad(540, 1050, 1300, [C(60, 120, 170), C(20, 40, 80)])))
    return E.arr(s)


# =================================================================================== scenes
def sc_hook(t, f):
    img = np.array(bg_bedroom())
    ts = word_t("hook", "slept")
    tsee = word_t("hook", "see")
    img = layer_over(img, lambda c: wall_clock(c, 300, 760, 120, t, 6.0))
    u = snap(t, ts, 6, 1.5)
    pose = dict(eyes=min(1.25, 0.3 + max(0.0, u)), brows="up", brow_lift=(lerp(0, 8, u),) * 2, mouth="O" if t > tsee else "frown",
                mouth_amt=0.9, look=(0.6 * math.sin(t * 3) if t > tsee else 0, -0.2), hands=[(-40, 40), (40, 40)],
                blink=any(0 <= t - b < 0.1 for b in (0.5, 2.6)))
    img = char(img, YOU, 540, 1800, 2.05, pose, t, rim_col=(0.7, 0.75, 1.0))

    def draw(c):
        a = ramp(t, tsee, 0.5)
        spook(c, "eye", 200, 1150, 1.0, a, t)
        spook(c, "fish", 880, 1100, 1.0, a, t)
        spook(c, "shadow", 900, 1380, 1.1, a, t)
        bed_front(c)
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("WHAT IF NOBODY", 90, 260, E.WHITE, -0.3), ("SLEPT?", 170, 440, E.GOLD, ts)]),
            E.stamp_layer(t, "DAY 3: VISIONS", word_t("hook", "there") + 0.35, 540, 1680, 100)]
    return img, cam("hook", [(0, 1.0, 540, 960), (2.5, 1.07, 540, 1000), (6.6, 1.13, 540, 1040)])(t), lays


def sc_night(t, f):
    tm = word_t("night", "morning")
    img = np.array(bg_cafe(dawn=t > tm))
    tc = word_t("night", "cranky")
    tw = word_t("night", "forgetting")
    pose = dict(eyes="sad" if t > tc else "open", brows="angry" if t > tc else "flat", mouth="frown" if t > tc else "smile",
                look=(0.6, 0.3), hands=[(-20, 120), (130, -20)], tilt=-3)
    x, y, s_ = 330, 1780, 1.95
    img = char(img, YOU, x, y, s_, pose, t)

    def draw(c):
        counter(c, 1500, top=(150, 95, 60), front=(100, 60, 40), stripe=(230, 190, 120))
        coffee_pot(c, 820, 1500, 1.1, 0, empty=t > word_t("night", "sells"))
        cup(c, 620, 1500, 1.0)
        # the very last drop falls from the pot spout into the cup, landing on "sells"
        u = t - drop_t0()
        if 0 <= u:
            yy = 1190.0 + 0.5 * G_PX * u * u
            if yy < CUP_TOP:
                c.drawOval(skia.Rect(620 - 9, yy - 14, 620 + 9, yy + 10), P(C(110, 65, 35)))
        if t > tw:   # the forgotten word
            a = clamp((t - tw) / 0.2)
            c.drawRoundRect(skia.Rect(580, 960, 1040, 1070), 40, 40, P(C(255, 255, 255, int(255 * a))))
            c.drawRoundRect(skia.Rect(580, 960, 1040, 1070), 40, 40, S(OUT, 5))
            text(c, "the... uh... thing?", 810, 1030, 44, C(40, 30, 25, int(255 * a)))
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("NIGHT 1", 140, 300, E.GOLD, word_t("night", "night", "one"))]),
            E.stamp_layer(t, "SOLD OUT", word_t("night", "out") + 0.3, 760, 820, 110),
            E.title_layer(t, [("CRANKY", 100, 450, E.WHITE, tc)])]
    return img, cam("night", [(0, 1.0, 540, 960), (5.9, 1.06, 520, 990)])(t), lays


def sc_drunk(t, f):
    img = np.array(bg_road())
    a = span("drunk")[0]
    td = word_t("drunk", "drunk")
    te = word_t("drunk", "every")

    def draw(c):
        # the hero car weaves (sine, growing) - driver nodding
        k = t - a
        wob = min(1.0, k / 3.0)
        x = (-260 + 210 * k) % (W + 520) - 260
        y = 1600 + 40 * wob * math.sin(k * 3.2)
        car(c, x, y, 1.25, (230, 80, 60), rot=6 * wob * math.cos(k * 3.2), driver=0.5 + 0.5 * math.sin(k * 2.5), t=t)
        if t > te:
            for i, (col, y0, sp) in enumerate((((70, 150, 220), 1350, 260), ((240, 200, 60), 1820, 180), ((90, 190, 120), 1460, 320))):
                kk = t - te
                xx = W + 200 - sp * kk * 2 - i * 300
                car(c, xx, y0 + 30 * math.sin(kk * 3 + i), 0.9, col, rot=6 * math.sin(kk * 3 + i), driver=0.5, t=t)
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("24 HOURS AWAKE", 100, 300, E.GOLD, word_t("drunk", "24", "twentyfour"))]),
            E.title_layer(t, [("= DRUNK", 150, 460, E.WHITE, td)]),
            E.stamp_layer(t, "EVERY DRIVER?!", word_t("drunk", "driver") + 0.5, 540, 1100, 110)]
    return img, cam("drunk", [(0, 1.0, 540, 960), (7.2, 1.05, 540, 1000)])(t), lays


def sc_micro(t, f):
    img = np.array(bg_office())
    t0 = word_t("micro", "few") - 0.1           # head drops ("a few seconds long")
    t1 = word_t("micro", "mid") + 0.05          # jolts awake
    asleep = t0 <= t < t1
    jolt = snap(t, t1, 5, 1.6) if t >= t1 else 0
    pose = dict(eyes="closed" if asleep else (min(1.2, jolt) if t >= t1 else "open"), brows="flat" if asleep else "up",
                mouth="open" if asleep else ("O" if t >= t1 else "talk"), talk=0.5 + 0.5 * math.sin(t * 18),
                look=(0, 0.8) if asleep else (0, 0), tilt=14 * smooth(clamp((t - t0) / 0.5)) * (1 if asleep else 0),
                lean=0, hands=[(-20, 120), (120, -80)] if not asleep else [(-20, 120), (40, 60)])
    x, y, s_ = 540, 1800, 2.0
    img = char(img, YOU, x, y, s_, pose, t)

    def draw(c):
        if asleep:
            for k in range(3):
                ph = ((t - t0) * 0.8 + k / 3) % 1.0
                text(c, "z", 700 + 40 * k + 30 * ph, 1100 - 200 * ph, 50 + 25 * k, C(255, 255, 255, int(255 * (1 - ph))))
        counter(c, 1560, top=(170, 130, 90), front=(120, 85, 55), stripe=(90, 60, 40))
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("DAY 2", 150, 300, E.GOLD, word_t("micro", "day", "two"))]),
            E.title_layer(t, [("MICRO-SLEEPS", 100, 450, E.WHITE, word_t("micro", "tiny", "sleeps"))]),
            E.stamp_layer(t, "MID-SENTENCE!", word_t("micro", "sentence") + 0.5, 540, 1700, 100)]
    return img, cam("micro", [(0, 1.0, 540, 960), (t0 - span("micro")[0], 1.05, 540, 1000), (7.8, 1.12, 540, 1040)])(t), lays


def sc_halluc(t, f):
    img = np.array(bg_swirl())
    tsee = word_t("halluc", "see")
    tx = word_t("halluc", "explode", "tempers")
    angry = t > tx
    pose = dict(eyes=1.2 if not angry else "squint", brows="angry" if angry else "up", mouth="O" if not angry else "frown", mouth_amt=1.0,
                look=(0.7 * math.sin(t * 2.5), -0.3), hands=[(-80, -60), (80, -60)] if not angry else [(-60, -200), (60, -200)], tilt=0)
    img = char(img, YOU, 540, 1850, 2.0, pose, t, rim_col=(0.9, 0.6, 1.0))

    def draw(c):
        a = ramp(t, tsee - 0.2, 0.6)
        for i, (kind, x0, y0, s) in enumerate((("eye", 200, 900, 1.1), ("fish", 880, 820, 1.2), ("shadow", 170, 1350, 1.2), ("eye", 900, 1300, 0.8))):
            spook(c, kind, x0 + 40 * math.sin(t * 1.3 + i), y0 + 30 * math.cos(t * 1.1 + i), s, a, t)
        if angry:      # steam puffs from his ears
            for k in range(6):
                ph = ((t - tx) * 1.4 + k / 6) % 1.0
                sx = -1 if k % 2 else 1
                c.drawCircle(540 + sx * (210 + 120 * ph), 1150 - 220 * ph, 30 + 40 * ph, P(C(255, 255, 255, int(200 * (1 - ph)))))
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("DAY 3", 150, 300, E.GOLD, word_t("halluc", "day", "three"))]),
            E.title_layer(t, [("SEEING THINGS", 96, 450, E.WHITE, tsee)]),
            E.stamp_layer(t, "BOOM!", tx + 0.4, 540, 640, 130)]
    return img, cam("halluc", [(0, 1.0, 540, 960), (5.1, 1.08, 540, 1010)])(t), lays


def sc_real(t, f):
    """Real history: Randy Gardner, 1964 - warm sepia palette, told plainly."""
    img = np.array(bg_fair())
    tr = word_t("real", "randy")
    tse = word_t("real", "seeing")
    tired = clamp((t - page_tear_times()[0]) / (page_tear_times()[-1] - page_tear_times()[0]))
    pose = dict(eyes="sad" if tired > 0.5 else "open", brows="sad" if tired > 0.3 else "up", mouth="frown" if tired > 0.5 else "smile",
                look=(0.8 * math.sin(t * 2) if t > tse else 0.5, 0), hands=[(-20, 120), (20, 120)], tilt=6 * tired * math.sin(t * 1.5))
    img = char(img, RANDY, 300, FLOOR_FAIR + 10, 1.6, pose, t, shadow=0.4)

    def draw(c):
        # the day calendar: its number counts up as each page is torn off
        torn = sum(1 for tt in page_tear_times() if t >= tt)
        c.drawRect(skia.Rect(CAL[0] - 130, CAL[1] - 120, CAL[0] + 130, CAL[1] + 180), P(C(250, 250, 245)))
        c.drawRect(skia.Rect(CAL[0] - 130, CAL[1] - 120, CAL[0] + 130, CAL[1] - 40), P(C(200, 50, 45)))
        text(c, "DAY", CAL[0], CAL[1] - 60, 50, C(255, 255, 255))
        text(c, str(1 + torn), CAL[0], CAL[1] + 120, 150, C(40, 30, 25))
        c.drawRect(skia.Rect(CAL[0] - 130, CAL[1] - 120, CAL[0] + 130, CAL[1] + 180), S(OUT, 5))
        for k in range(PAGES):
            st = page_state(k, t)
            if st:
                x, y, ang, landed = st
                c.save(); c.translate(x, y); c.rotate(ang)
                c.drawRect(skia.Rect(-60, -40 if not landed else -8, 60, 0), P(C(250, 250, 245)))
                c.drawRect(skia.Rect(-60, -40 if not landed else -8, 60, 0), S(OUT, 3))
                c.restore()
        if t > tse:
            a = ramp(t, tse, 0.5)
            spook(c, "eye", 520, 1000, 0.7, a * 0.8, t)
            spook(c, "fish", 180, 900, 0.7, a * 0.8, t)
    img = layer_over(img, draw)
    lum = img[..., :3].mean(axis=2, keepdims=True)
    img[..., :3] = img[..., :3] * 0.75 + lum * 0.25 * np.array([1.08, 1.0, 0.85], np.float32)
    lays = [E.title_layer(t, [("THIS REALLY HAPPENED", 76, 270, E.WHITE, word_t("real", "really", "happened")),
                              ("1964", 140, 420, E.GOLD, word_t("real", "1964"))]),
            E.title_layer(t, [("RANDY GARDNER, 17", 74, 1830, E.WHITE, tr)]),
            E.stamp_layer(t, "11 DAYS AWAKE", word_t("real", "days") + 0.45, 690, 1620, 88, (200, 40, 45), -6)]
    return img, cam("real", [(0, 1.0, 540, 960), (10.7, 1.05, 560, 980)])(t), lays


def sc_twist(t, f):
    img = np.array(bg_brainroom())
    a = span("twist")[0]
    tw = word_t("twist", "washes")
    tc = word_t("twist", "cleaning")
    clean = ramp(t, tw, 1.2)

    def draw(c):
        bob = 10 * math.sin(t * 2)
        c.drawCircle(540, 1050, 420, P(Shader=T.rad(540, 1050, 420, [C(255, 255, 255, 50), C(255, 255, 255, 0)])))
        brain(c, 540, 1030 + bob, 1.6, t, clean)
        # waste specks: sit on the brain until "washes", then the wave carries them down and out of frame
        r = random.Random(7)
        for k in range(30):
            sx, sy = r.uniform(-300, 300), r.uniform(-300, 140)
            if t < tw:
                c.drawCircle(540 + sx, 1030 + bob + sy, 9, P(C(80, 70, 40)))
            else:
                u = t - tw - 0.02 * k
                if u < 0:
                    c.drawCircle(540 + sx, 1030 + bob + sy, 9, P(C(80, 70, 40)))
                else:
                    yy = 1030 + sy + 0.5 * 1800 * u * u
                    if yy < H + 40:
                        c.drawCircle(540 + sx + 40 * math.sin(u * 8 + k), yy, 9, P(C(80, 70, 40)))
        if t > tw - 0.3:   # the blue wash sweeping down over the brain
            ph = clamp((t - tw + 0.3) / 2.4)       # ~12 px/frame with 75 px spacing: no strobing stripes
            for k in range(5):
                yy = 640 + 900 * ph + k * 75
                c.drawArc(skia.Rect(140 + k * 10, yy - 60, 940 - k * 10, yy + 60), 200, 140, False,
                          S(C(120, 210, 255, int(200 * (1 - ph))), 14))
        if t > tc:   # bubbles
            for k in range(14):
                ph = ((t - tc) * 0.5 + k / 14) % 1.0
                c.drawCircle(220 + k * 48, 1600 - 900 * ph, 10 + (k % 3) * 6, S(C(200, 240, 255, int(220 * (1 - ph))), 4))
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("THE TWIST", 140, 300, E.GOLD, word_t("twist", "twist"))]),
            E.title_layer(t, [("SLEEP = CLEANING", 92, 450, E.WHITE, tc)]),
            E.stamp_layer(t, "WASTE: GONE", word_t("twist", "away") + 0.5, 540, 1720, 110, (40, 140, 70), -6)]
    return img, cam("twist", [(0, 1.0, 540, 960), (8.3, 1.06, 540, 1000)])(t), lays


def sc_end(t, f):
    tn = word_t("end", "tonight")
    tg = word_t("end", "go")
    if t < tn - 0.15:
        img = np.array(bg_brainroom())
        tr = word_t("end", "record")
        img = layer_over(img, lambda c: record_book(c, 540, 1180, 1.25, ramp(t, tr + 0.3, 0.3)))
        lays = [E.title_layer(t, [("TOO DANGEROUS", 104, 300, E.GOLD, word_t("end", "dangerous"))]),
                E.stamp_layer(t, "NOT TRACKED", tr + 0.3, 540, 1700, 110)]
        return img, cam("end", [(0, 1.0, 540, 960), (3.6, 1.06, 540, 1000)])(t), lays
    img = np.array(bg_bedroom())
    img[..., :3] *= lerp(1.0, 0.7, clamp((t - tg) / 0.6))            # the lamp clicks off
    u = clamp((t - tn) / 1.2)
    pose = dict(eyes="closed" if t > tg else "sad", brows="flat", mouth="smile", look=(0, 0.2), tilt=-10 * smooth(u), hands=[(-40, 40), (40, 40)])
    img = char(img, YOU, 540, 1830, 2.0, pose, t, rim_col=(0.7, 0.75, 1.0))

    def draw(c):
        if t > tg:
            for k in range(3):
                ph = ((t - tg) * 0.7 + k / 3) % 1.0
                text(c, "Z", 700 + 40 * k + 30 * ph, 1150 - 220 * ph, 60 + 25 * k, C(255, 255, 255, int(255 * (1 - ph))))
        bed_front(c)
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("SO TONIGHT...", 96, 300, E.WHITE, tn)]),
            E.title_layer(t, [("GO TO SLEEP", 130, 460, E.GOLD, tg)])]
    return img, cam("end", [(0, 1.0, 540, 960), (tn - span("end")[0], 1.0, 540, 960), (6.3, 1.1, 540, 1040)])(t), lays


def sc_cta(t, f):
    from cta2 import draw_cta2
    img = E.gblur(np.array(bg_bedroom()), 10 * K)
    img[..., :3] *= 0.55
    t0 = span("cta")[0]
    s, c = E.surf(world=False)
    draw_cta2(c, max(0.0, t - t0), word_t("cta", "like") - t0, word_t("cta", "subscribe") - t0)
    return img, (1.08, 540, 1000), [E.arr(s)]


RENDER = {n: globals()["sc_" + n] for n, _ in SCENES}
NO_SPLAT = {"cta"}
INNER_CUTS = None


def splat_cuts():
    out = [CUTS[i] for i in range(1, len(SCENES)) if SCENES[i][0] not in NO_SPLAT]
    return sorted(out + [word_t("end", "tonight") - 0.15])


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
        SHAKES = [word_t("hook", "slept"), word_t("night", "out") + 0.3, word_t("micro", "mid") + 0.05, word_t("halluc", "explode") + 0.4]
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
    for k in range(PAGES):
        st = page_state(k, 1e3)
        assert st and st[3] and abs(st[1] - FLOOR_FAIR) < 1e-9, "calendar pages must rest on the floor"
        tt = page_tear_times()[k]
        for u in np.arange(0, 5, 1 / FPS):
            s2 = page_state(k, tt + u)
            assert s2[1] <= FLOOR_FAIR + 1e-9, "a page must never sink below the floor"
    u_drop = word_t("night", "sells") - drop_t0()
    assert abs(1190.0 + 0.5 * G_PX * u_drop * u_drop - CUP_TOP) < 1e-6, "the coffee drop must hit the cup on 'sells'"
    return dict(page_land=page_land_times(), page_vt=PAGE_VT, drop_t0=drop_t0(), g_px=G_PX,
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
