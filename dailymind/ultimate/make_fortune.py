"""YouTube Short: "Fortune Cookies Aren't Chinese" - in the APPROVED 2D Classic+ style (style2d_engine.py).

Facts (sourced): Japanese origin - a family bakery near a Kyoto shrine still makes tsujiura senbei; an 1878 print shows a
baker grilling them on hand irons (Smithsonian; researcher Yasuko Nakamachi). Bigger, darker, sesame + miso, fortune
tucked into the fold. Japanese bakers brought them to California; the Japanese Tea Garden in San Francisco served them
and Benkyodo made them in quantity (KQED, KRDO). 1942: Japanese Americans on the West Coast were sent to internment camps
(~120,000 people); the bakeries closed and Chinese-American factories took over (KEYT). ~3 billion made a year
(Wikipedia est.); Wonton Food (New York) makes 4+ million a day. 1992: Wonton Food's factory in China flopped -
"too American" (Snopes citing the NYT). Generic cartoon people; no likenesses, no brands.

  python make_fortune.py frames            -> ../fortune/frames/%04d.png  (all scenes, multiprocess)
  python make_fortune.py stills 1.0,5.2    -> ../fortune/stills/*.png    (seconds)
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

import style2d_engine as E
import toon as T
from style2d_engine import C, P, S, BLUR, W, H, K, FPS, path, lerp, lerp2, clamp, ramp, snap, smooth, noise1

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "fortune")
TIMES = json.load(open(os.path.join(D, "vo.wav.times.json")))
WORDS = json.load(open(os.path.join(D, "vo.wav.words.json")))
LINES = json.load(open(os.path.join(D, "lines.json")))
ORDER = [l["key"] for l in LINES]
VO_END = float(open(os.path.join(D, "vo_end.txt")).read()) if os.path.exists(os.path.join(D, "vo_end.txt")) else TIMES["cta"] + 2.4
CTA_HOLD = 2.6
DUR = max(61.5, VO_END + CTA_HOLD)
NF = int(round(DUR * FPS))


def line_t(key):
    return TIMES[key]


def word_t(line, word, nth=1):
    """Time of the nth occurrence of `word` at/after the start of `line` (from faster-whisper word timestamps)."""
    t0 = TIMES[line] - 0.05
    hits = sorted(v for k, v in WORDS.items() if k.split("#")[0] == word and v >= t0)
    if len(hits) < nth:
        raise KeyError(f"word {word!r} not found after line {line!r}")
    return hits[nth - 1]


# scenes: (name, first line key). A scene runs from its first line's start (minus a hair) to the next scene's.
SCENES = [("restaurant", "hook"), ("sunrise", "japanese"), ("kyoto", "kyoto"), ("tray", "darker"), ("ship", "california"),
          ("teagarden", "teagarden"), ("bakery42", "camps"), ("factory", "factories"), ("pile", "billion"), ("china", "flop"),
          ("reveal", "twist"), ("cta", "cta")]
CUTS = [0.0] + [line_t(k) - 0.12 for _, k in SCENES[1:]] + [DUR]


def scene_at(t):
    for i in range(len(SCENES)):
        if CUTS[i] <= t < CUTS[i + 1]:
            return i
    return len(SCENES) - 1


# =================================================================================== props
def cookie_body():
    """Fortune cookie, 3/4 view (~156 x 92 box): a dome with two pointed wings and a DEEP centre fold.
    (A first design read as goggles / a bean; the deep fold, the visible inner surface and the paper slip make it read.)"""
    body = skia.Path()
    body.moveTo(-78, 30)
    body.cubicTo(-86, -30, -40, -62, 0, -62)
    body.cubicTo(40, -62, 86, -30, 78, 30)
    body.cubicTo(60, 26, 34, 14, 14, -4)
    body.lineTo(0, -16)
    body.lineTo(-14, -4)
    body.cubicTo(-34, 14, -60, 26, -78, 30)
    body.close()
    return body


def cookie(c, x, y, s=1.0, rot=0.0, kind="modern", side=0, slip=0.0, slip_text=None):
    """side: 0 whole, -1 / +1 one half (cracked open). slip: 0..1 how far the paper slip shows from the fold."""
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    body = cookie_body()
    if side:
        clip = skia.Path()
        clip.addRect(skia.Rect(0 if side > 0 else -100, -80, 100 if side > 0 else 0, 60))
        c.clipPath(clip, doAntiAlias=True)
    pal = {"modern": [C(255, 230, 165), C(242, 188, 98), C(208, 138, 56)], "senbei": [C(205, 140, 72), C(160, 96, 42), C(112, 62, 24)]}[kind]
    c.drawPath(body, P(Shader=T.lin((-50, -62), (50, 30), pal)))
    c.save()
    c.clipPath(body, doAntiAlias=True)
    c.drawPath(body, S(C(160, 90, 30, 110) if kind == "modern" else C(70, 35, 10, 140), 14))
    c.restore()
    for sgn in (-1, 1):
        inner = skia.Path()
        inner.moveTo(0, -16)
        inner.lineTo(sgn * 14, -4)
        inner.cubicTo(sgn * 30, 10, sgn * 48, 20, sgn * 60, 24)
        inner.cubicTo(sgn * 40, 24, sgn * 16, 12, 0, -2)
        inner.close()
        c.drawPath(inner, P(C(175, 105, 40) if kind == "modern" else C(90, 48, 18)))
    cr = skia.Path()
    cr.moveTo(0, -16)
    cr.cubicTo(-4, -36, -2, -50, 4, -60)
    c.drawPath(cr, S(C(190, 120, 45, 170) if kind == "modern" else C(85, 45, 15, 170), 4))
    hl = skia.Path()
    hl.moveTo(-60, 0)
    hl.cubicTo(-58, -34, -34, -52, -10, -54)
    c.drawPath(hl, S(C(255, 252, 230, 170), 6))
    if kind == "senbei":
        r = random.Random(4)
        for i in range(34):
            sx, sy = r.uniform(-70, 70), r.uniform(-58, 26)
            if body.contains(sx, sy):
                c.save()
                c.translate(sx, sy)
                c.rotate(r.uniform(0, 180))
                c.drawOval(skia.Rect(-3.2, -1.6, 3.2, 1.6), P(C(250, 240, 210)))
                c.restore()
    c.drawPath(body, S(T.OUT, 4))
    if slip > 0 and side == 0:
        c.save()
        c.translate(0, -6)
        c.rotate(70)
        L = 44 * slip
        c.drawRect(skia.Rect(0, -7, L, 7), P(C(252, 250, 244)))
        c.drawRect(skia.Rect(0, -7, L, 7), S(C(120, 110, 100), 1.6))
        for k in range(int(L // 9)):
            c.drawLine(5 + k * 9, 0, 9 + k * 9, 0, S(C(200, 40, 50, 210), 2))
        c.restore()
    c.restore()


def slip_card(c, x, y, s, text, a=255):
    """A fortune slip held up to camera with readable text."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    w = 820
    c.drawRect(skia.Rect(-w / 2, -66, w / 2, 66), P(C(0, 0, 0, int(a * 0.3)), MaskFilter=BLUR(10)))
    c.drawRect(skia.Rect(-w / 2, -62, w / 2, 62), P(C(253, 251, 245, a)))
    c.drawRect(skia.Rect(-w / 2, -62, w / 2, 62), S(C(140, 130, 120, a), 2))
    f = skia.Font(T.FB, E.fit_size(text, 54, w - 60))
    tw = f.measureText(text)
    c.drawString(text, -tw / 2, 18, f, P(C(200, 35, 45, a)))
    c.restore()


def table_front(c, y, col=(245, 240, 232), dark=False):
    """Round table with a cloth, seen from the front (covers the diner's legs)."""
    top = skia.Rect(-60, y, W + 60, y + 60)
    c.drawOval(top, P(C(*[v * 0.8 for v in col])))
    c.drawRect(skia.Rect(-60, y + 30, W + 60, H), P(Shader=T.lin((0, y), (0, H), [C(*col), C(*[v * 0.72 for v in col])])))
    for k in range(9):   # cloth folds
        x = 60 + k * 125
        c.drawLine(x, y + 70, x + 15, H, S(C(0, 0, 0, 22), 6))
    c.drawLine(-60, y + 30, W + 60, y + 30, S(T.OUT, 5))


def lantern(c, x, y, r, t, ph=0.0, col=(225, 40, 40)):
    sw = 3 * math.sin(t * 1.3 + ph)                     # slow sway
    c.save()
    c.translate(x, y)
    c.rotate(sw)
    c.drawLine(0, -400, 0, -r * 1.05, S(C(60, 30, 20), 3))
    fl = 0.85 + 0.15 * noise1(t, int(ph * 10) + 50, 5)
    c.drawCircle(0, 0, r * 2.6, P(Shader=T.rad(0, 0, r * 2.6, [C(255, 150, 80, int(90 * fl)), C(255, 120, 60, 0)])))
    c.drawOval(skia.Rect(-r, -r * 0.95, r, r * 0.95), P(Shader=T.rad(-r * 0.2, -r * 0.2, r * 1.2, [C(255, 170, 120), C(*col), C(150, 20, 25)])))
    for k in range(-2, 3):
        c.drawArc(skia.Rect(-r * abs(1 - abs(k) * 0.3), -r * 0.95, r * abs(1 - abs(k) * 0.3), r * 0.95), 270, 180 if k >= 0 else -180, False,
                  S(C(140, 20, 25, 150), 2))
    c.drawRect(skia.Rect(-r * 0.45, -r * 1.12, r * 0.45, -r * 0.9), P(C(200, 150, 50)))
    c.drawRect(skia.Rect(-r * 0.45, r * 0.9, r * 0.45, r * 1.12), P(C(200, 150, 50)))
    c.drawLine(0, r * 1.12, 0, r * 1.6, S(C(230, 180, 60), 4))
    c.drawOval(skia.Rect(-r, -r * 0.95, r, r * 0.95), S(T.OUT, 4))
    c.restore()


def takeout_box(c, x, y, s=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = path([(-60, -90), (60, -90), (45, 30), (-45, 30)])
    c.drawPath(body, P(Shader=T.lin((-60, 0), (60, 0), [C(245, 245, 240), C(225, 222, 215)])))
    c.drawPath(path([(-60, -90), (-80, -125), (0, -105), (80, -125), (60, -90)]), P(C(235, 232, 225)))
    c.drawArc(skia.Rect(-40, -170, 40, -80), 200, 140, False, S(C(160, 160, 165), 5))
    c.drawCircle(0, -35, 22, S(C(200, 40, 50), 5))   # plain red ring motif, no brand
    c.drawPath(body, S(T.OUT, 4))
    c.restore()


def teacup(c, x, y, s, t, green=True, steam=True):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    cup = path([(-38, -40), (38, -40), (28, 18), (-28, 18)])
    c.drawPath(cup, P(Shader=T.lin((-38, 0), (38, 0), [C(235, 235, 225), C(250, 250, 245), C(205, 205, 195)])))
    c.drawOval(skia.Rect(-38, -50, 38, -30), P(C(120, 160, 70) if green else C(140, 80, 40)))
    c.drawPath(cup, S(T.OUT, 4))
    c.drawOval(skia.Rect(-38, -50, 38, -30), S(T.OUT, 3))
    if steam:
        for k in range(3):
            ph = (t * 0.55 + k / 3) % 1
            sp = skia.Path()
            x0 = -14 + k * 14
            sp.moveTo(x0, -55)
            for j in range(1, 7):
                sp.lineTo(x0 + 8 * math.sin(j * 1.3 + t * 2 + k), -55 - j * 14)
            c.save()
            c.translate(0, -30 * ph)
            c.drawPath(sp, S(C(255, 255, 255, int(110 * math.sin(math.pi * ph))), 5))
            c.restore()
    c.restore()


def suitcase(c, x, y, s, col=(120, 75, 45), rot=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    c.drawRoundRect(skia.Rect(-55, -75, 55, 0), 10, 10, P(Shader=T.lin((0, -75), (0, 0), [C(*col), C(*[v * 0.7 for v in col])])))
    c.drawRoundRect(skia.Rect(-55, -75, 55, 0), 10, 10, S(T.OUT, 4))
    c.drawArc(skia.Rect(-18, -95, 18, -65), 180, 180, False, S(T.OUT, 6))
    c.drawRect(skia.Rect(28, -60, 48, -40), P(C(240, 235, 220)))   # luggage tag
    c.drawLine(38, -60, 30, -75, S(C(80, 60, 40), 2))
    c.restore()


def petal(c, x, y, r, ang, a=230):
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    p = skia.Path()
    p.moveTo(0, -r)
    p.quadTo(r * 0.9, -r * 0.2, 0, r)
    p.quadTo(-r * 0.9, -r * 0.2, 0, -r)
    c.drawPath(p, P(C(255, 190, 205, a)))
    c.restore()


# ------------------------------------------------------------------ physics helpers (simulated, deterministic)
def falling_bodies(n, seed, t, t0, x_rng, y0, floor_y, g=2600.0, rest=0.3, vx_rng=(-60, 60), stagger=0.05, drag=0.0):
    """Bodies dropped from y0 at staggered times, ballistic with gravity, bouncing on a floor (restitution ~0.3), settling.
    Returns [(x, y, angle, landed)] at time t. Sub-stepped integration so nothing tunnels or sinks."""
    r = random.Random(seed)
    out = []
    for i in range(n):
        x, y = r.uniform(*x_rng), y0 - r.uniform(0, 200)
        vx, vy, ang, w_ = r.uniform(*vx_rng), r.uniform(-50, 50), r.uniform(0, 360), r.uniform(-300, 300)
        fy = floor_y + r.uniform(-25, 25)
        start = t0 + i * stagger
        if t < start:
            continue
        dt, k = 1 / 240.0, 0.0
        landed = False
        while k < t - start:
            vy += g * dt
            vx *= (1 - drag * dt)
            x += vx * dt
            y += vy * dt
            ang += w_ * dt
            if y >= fy:
                y = fy
                if abs(vy) < 120:
                    vy, vx, w_ = 0.0, vx * 0.6, w_ * 0.5
                    landed = True
                else:
                    vy = -vy * rest
                    vx *= 0.7
                    w_ *= -0.6
            k += dt
        out.append((x, y, ang, landed))
    return out


def flutter(t, t0, x0, y0, seed, floor_y=None):
    """Paper / petal: drag-limited fall with a side-to-side flutter (terminal velocity ~180 px/s)."""
    k = max(0.0, t - t0)
    vt = 180.0
    y = y0 + vt * (k - (1 - math.exp(-k * 4)) / 4)
    x = x0 + 60 * math.sin(k * 2.4 + seed) + 25 * noise1(k, seed, 1.0)
    ang = 35 * math.sin(k * 2.4 + seed + 1.2)
    if floor_y is not None and y > floor_y:
        y, ang = floor_y, 0.0
    return x, y, ang


# =================================================================================== scene renderers
# each returns (world RGBA, (zoom, cx, cy), title/screen layers list)
LOOK_DINER = dict(skin=(235, 185, 150), hair="neat", hair_col=(60, 40, 30), coat=(70, 110, 170), pants=(60, 60, 70), nose="small")
LOOK_BAKER = dict(skin=(232, 190, 150), hair="neat", hair_col=(30, 25, 25), coat=(60, 70, 110), pants=(60, 60, 80), nose="small", hat="headband")
LOOK_GUEST = dict(skin=(240, 200, 170), hair="pigtails", hair_col=(80, 50, 30), coat=(230, 150, 160), pants=(80, 70, 90), nose="small")
LOOK_DAD = dict(skin=(225, 185, 150), hair="neat", hair_col=(30, 25, 25), coat=(95, 95, 105), pants=(70, 70, 80), nose="small", hat="bowler")
LOOK_MOM = dict(skin=(230, 190, 160), hair="curly", hair_col=(30, 25, 25), coat=(120, 100, 120), pants=(80, 70, 80), nose="small")
LOOK_KID = dict(skin=(235, 195, 165), hair="kid", hair_col=(30, 25, 25), coat=(150, 120, 90), pants=(70, 70, 90), nose="small")
LOOK_WORKER = dict(skin=(230, 190, 150), hair="neat", hair_col=(30, 25, 25), coat=(245, 245, 240), pants=(70, 70, 80), nose="small", hat="papercap")
LOOK_WAITER = dict(skin=(225, 185, 150), hair="neat", hair_col=(25, 22, 22), coat=(245, 245, 245), vest=(30, 30, 35), pants=(30, 30, 35), nose="small")
LOOK_SHOPPER = dict(skin=(230, 190, 155), hair="neat", hair_col=(25, 22, 22), coat=(90, 140, 120), pants=(60, 60, 70), nose="small")
LOOK_SHOPPER2 = dict(skin=(235, 195, 160), hair="pigtails", hair_col=(25, 22, 22), coat=(230, 180, 80), pants=(70, 70, 90), nose="small")


@lru_cache(maxsize=None)
def bg_restaurant():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(70, 14, 20), C(120, 25, 30), C(60, 12, 16)])))
    for k in range(7):   # lattice wall panels
        x = 40 + k * 160
        c.drawRoundRect(skia.Rect(x, 560, x + 120, 1180), 12, 12, S(C(200, 150, 60, 110), 6))
        for j in range(5):
            c.drawLine(x + 10, 600 + j * 120, x + 110, 600 + j * 120, S(C(200, 150, 60, 60), 3))
    c.drawRect(skia.Rect(0, 1180, W, 1260), P(C(40, 8, 12)))
    return E.arr(s)


def sc_restaurant(t, f, reveal=False):
    img = np.array(bg_restaurant())
    s, c = E.surf()
    for i, (lx, ly, r) in enumerate(((150, 760, 70), (540, 700, 85), (930, 760, 70))):   # below the title band
        lantern(c, lx, ly, r, t, i * 1.7)
    E.over(img, E.arr(s))
    t0 = 0.0 if not reveal else line_t("twist")
    k = t - t0
    # the diner, seated behind the table
    if not reveal:
        t_crack = word_t("hook", "cracked")
        t_ch = word_t("hook", "chinese")
        crack = snap(t, t_crack, 5, 1.6)
        u_shock = snap(t, t_ch, 6, 1.5)
        pose = dict(eyes=min(1.2, max(0.0, u_shock)), brows="up", brow_lift=(lerp(0, 8, u_shock),) * 2, mouth="O" if u_shock > 0.05 else "smile",
                    mouth_amt=lerp(0.4, 1.1, u_shock), look=(0, 0.6 - 0.6 * u_shock), lean=0, tilt=lerp(0, -5, u_shock),
                    hands=[lerp2((-10, 30), (-40, 10), crack), lerp2((10, 30), (40, 10), crack)], bends=(-1, 1),
                    blink=any(0 <= t - b < 0.1 for b in (0.6, 2.4)))
    else:
        t_jp = word_t("twist", "japanese")
        u = snap(t, t_jp, 6, 1.5)
        pose = dict(eyes=min(1.2, 0.2 + max(0.0, u)), brows="up", brow_lift=(4 + 6 * u,) * 2, mouth="O", mouth_amt=lerp(0.6, 1.3, u),
                    look=(0, 0.2), lean=0, tilt=lerp(-3, 4, u), hands=[(-40, 10), (40, 10)], bends=(-1, 1),
                    blink=any(0 <= t - b < 0.1 for b in (line_t("twist") + 0.5,)))
    ch = E.draw_person(LOOK_DINER, 540, 1900, 2.1, pose, t)
    img = E.light_char(ch, img, 1900, shadow=0, rim_col=(1.0, 0.55, 0.45), rim=0.5)
    s, c = E.surf()
    table_front(c, 1500)
    takeout_box(c, 190, 1560, 1.1)
    c.drawOval(skia.Rect(700, 1520, 980, 1580), P(C(250, 250, 250)))       # plate
    c.drawOval(skia.Rect(700, 1520, 980, 1580), S(T.OUT, 4))
    for dx in (0, 22):                                                    # chopsticks
        c.drawLine(380 + dx, 1590, 600 + dx, 1545, S(C(120, 70, 40), 9))
    # the cookie in his hands (crack: halves rotate apart around the crease)
    hl = T.hand_pos(540, 1900, 2.1, pose, -1)
    hr = T.hand_pos(540, 1900, 2.1, pose, 1)
    cx_, cy_ = (hl[0] + hr[0]) / 2, (hl[1] + hr[1]) / 2 - 70
    if not reveal:
        crack = snap(t, word_t("hook", "cracked"), 5, 1.6)
        if crack <= 0.01:
            cookie(c, cx_, cy_, 1.6)
        else:
            sep = 70 * crack
            cookie(c, cx_ - sep, cy_, 1.6, -25 * crack, side=-1)
            cookie(c, cx_ + sep, cy_, 1.6, 25 * crack, side=1)
            # crumbs: ballistic, bounce on the table cloth (restitution 0.3) and settle
            for (x, y, ang, landed) in falling_bodies(9, 21, t, word_t("hook", "cracked"), (cx_ - 30, cx_ + 30), cy_, 1515,
                                                       g=2400, vx_rng=(-260, 260), stagger=0.0):
                c.drawCircle(x, y - 4, 6, P(C(225, 165, 70)))
                c.drawCircle(x, y - 4, 6, S(T.OUT, 2))
            # the slip pops out and flutters down (drag-limited), lands on the plate
            sx, sy, sa = flutter(t, word_t("hook", "cracked") + 0.15, cx_, cy_ - 10, 3, floor_y=1540)
            c.save()
            c.translate(sx, sy)
            c.rotate(sa)
            c.drawRect(skia.Rect(-40, -9, 40, 9), P(C(252, 250, 244)))
            c.drawRect(skia.Rect(-40, -9, 40, 9), S(C(130, 120, 110), 1.5))
            c.restore()
    else:
        cookie(c, cx_ - 70, cy_, 1.6, -25, side=-1)
        cookie(c, cx_ + 70, cy_, 1.6, 25, side=1)
    E.over(img, E.arr(s))
    glow = 0.10 + 0.03 * noise1(t, 7, 4)
    img[..., :3] += E.glow_map(540, 700, 420, 380)[..., None] * glow * np.array([1.0, 0.6, 0.3], np.float32)
    lay = []
    if not reveal:
        cam = E.catmull([(0, 1.0, 540, 980), (2.0, 1.08, 540, 1010), (4.5, 1.14, 540, 1030)], t)
        lay.append(E.title_layer(t, [("FORTUNE COOKIES", 104, 300, E.WHITE, -1.0), ("AREN'T CHINESE", 150, 470, E.GOLD, word_t("hook", "chinese"))]))
    else:
        cam = E.catmull([(t0, 1.08, 540, 1000), (t0 + 3, 1.16, 540, 1040)], t)
        u = ramp(t, t0 + 0.2, 0.5)
        sl = E.surf(world=False)
        if u > 0:
            slip_card(sl[1], 540, 1500, 0.85 + 0.15 * u, "YOU ARE EATING JAPANESE HISTORY", int(255 * u))
        lay.append(E.arr(sl[0]))
        lay.append(E.title_layer(t, [("JAPANESE", 160, 400, E.GOLD, word_t("twist", "japanese")),
                                     ("ALL ALONG", 110, 540, E.WHITE, word_t("twist", "along"))]))
    return img, cam, lay


@lru_cache(maxsize=None)
def bg_sunrise():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(250, 200, 190), C(255, 225, 200), C(250, 240, 225)], [0, 0.55, 1])))
    for k in range(12):
        a0 = math.radians(-180 + k * 15)
        c.drawPath(path([(540, 1150), (540 + 1500 * math.cos(a0), 1150 + 1500 * math.sin(a0)),
                         (540 + 1500 * math.cos(a0 + 0.12), 1150 + 1500 * math.sin(a0 + 0.12))]), P(C(255, 255, 255, 40)))
    return E.arr(s)


def sc_sunrise(t, f):
    t0 = line_t("japanese") - 0.12
    k = t - t0
    img = np.array(bg_sunrise())
    s, c = E.surf()
    rise = ramp(t, t0, 1.6)
    sy = 1250 - 260 * rise
    c.drawCircle(540, sy, 330, P(Shader=T.rad(540, sy, 330, [C(255, 70, 60), C(215, 25, 35)])))   # the rising sun
    c.drawCircle(540, sy, 420, P(Shader=T.rad(540, sy, 420, [C(255, 120, 100, 80), C(255, 120, 100, 0)])))
    # mountain silhouette with snow cap
    c.drawPath(path([(-50, 1500), (320, 1080), (460, 1010), (620, 1010), (760, 1080), (1130, 1500)]), P(C(95, 80, 130)))
    c.drawPath(path([(395, 1050), (460, 1010), (620, 1010), (685, 1050), (640, 1080), (590, 1050), (540, 1085), (490, 1050), (440, 1080)]),
               P(C(250, 250, 255)))
    c.drawRect(skia.Rect(0, 1480, W, H), P(Shader=T.lin((0, 1480), (0, H), [C(90, 70, 110), C(50, 40, 70)])))
    # cherry branches framing the top corners
    for side in (-1, 1):
        br = skia.Path()
        x0 = 0 if side < 0 else W
        br.moveTo(x0, 620)
        br.cubicTo(x0 - side * -200, 600, x0 - side * -330, 700, x0 - side * -420, 760)
        c.drawPath(br, S(C(70, 40, 40), 16))
        r = random.Random(9 + side)
        for i in range(16):
            bx = x0 + side * -r.uniform(40, 400)
            by = r.uniform(600, 780)
            c.drawCircle(bx, by, r.uniform(14, 24), P(C(255, 185, 200)))
            c.drawCircle(bx, by, 5, P(C(240, 120, 150)))
    # the cookie floating centre stage, slowly turning (scale-x as a turn), with a breath
    turn = math.cos(k * 1.4)
    c.save()
    c.translate(540, 1380 + 10 * math.sin(k * 2))
    c.scale(0.78 + 0.22 * turn, 1)
    cookie(c, 0, 0, 4.0, 0, slip=1.0)
    c.restore()
    # petals: drag-limited fall with flutter
    for i in range(24):
        x0 = (i * 97) % W
        px, py, pa = flutter(k + i * 0.37, 0, x0, -60, i)
        py = (py % (H + 120)) - 60
        petal(c, px, py, 12, pa + i * 30)
    E.over(img, E.arr(s))
    cam = E.catmull([(t0, 1.0, 540, 960), (t0 + 3, 1.05, 540, 980)], t)
    lay = [E.title_layer(t, [("THEY'RE", 96, 300, E.WHITE, t0 + 0.05), ("JAPANESE", 170, 470, E.RED, word_t("japanese", "japanese"))])]
    return img, cam, lay


@lru_cache(maxsize=None)
def bg_kyoto():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(C(233, 214, 175)))          # washi paper
    r = random.Random(2)
    for i in range(700):
        x, y = r.uniform(0, W), r.uniform(0, H)
        c.drawLine(x, y, x + r.uniform(-18, 18), y + r.uniform(-4, 4), S(C(190, 160, 110, 40), 1.2))
    for b, (y, col) in enumerate(((930, (120, 150, 175)), (1010, (70, 100, 140)), (1090, (40, 60, 100)))):   # flat indigo hills
        pts = [(0, H)] + [(x, y - 70 * math.sin(x / (160 + b * 50) + b) - 40) for x in range(0, W + 1, 30)] + [(W, H)]
        c.drawPath(path(pts), P(C(*col)))
        c.drawPath(path(pts), S(C(30, 30, 50), 4))
    # vermilion torii gate
    for x in (250, 470):
        c.drawRect(skia.Rect(x - 16, 640, x + 16, 1000), P(C(205, 60, 40)))
        c.drawRect(skia.Rect(x - 16, 640, x + 16, 1000), S(C(30, 20, 20), 4))
    c.drawPath(path([(190, 640), (530, 640), (550, 615), (170, 615)]), P(C(40, 30, 30)))
    c.drawRect(skia.Rect(200, 650, 520, 674), P(C(205, 60, 40)))
    c.drawRect(skia.Rect(214, 700, 506, 722), P(C(205, 60, 40)))
    # stall roof + floor
    c.drawRect(skia.Rect(0, 1500, W, H), P(C(196, 160, 110)))
    for k in range(10):
        c.drawLine(0, 1520 + k * 42, W, 1520 + k * 42, S(C(150, 115, 70, 120), 3))
    return E.arr(s)


def sc_kyoto(t, f):
    t0 = line_t("kyoto") - 0.12
    k = t - t0
    img = np.array(bg_kyoto())
    # baker
    flip_ph = (k * 0.9) % 1.0
    open_amt = math.sin(math.pi * min(1, flip_ph / 0.35)) if flip_ph < 0.35 else 0.0
    pose = dict(eyes="open", brows="flat", mouth="smile", look=(0.6, 0.4), lean=4, tilt=6,
                hands=[(70, 40 - 30 * open_amt), (110, 50)], bends=(-1, -1), blink=0 <= (k % 3.1) < 0.1)
    ch = E.draw_person(LOOK_BAKER, 380, 1650, 1.7, pose, t)
    img = E.light_char(ch, img, 1650, shadow=0.35, rim_col=(1.0, 0.6, 0.35), rim=0.4)
    s, c = E.surf()
    # charcoal brazier
    bx, by = 760, 1600
    c.drawRoundRect(skia.Rect(bx - 150, by - 40, bx + 150, by + 120), 20, 20, P(C(70, 55, 50)))
    c.drawRoundRect(skia.Rect(bx - 150, by - 40, bx + 150, by + 120), 20, 20, S(C(25, 20, 20), 5))
    for i in range(9):
        gx = bx - 120 + i * 30
        g = 0.6 + 0.4 * noise1(t, 200 + i, 3)
        c.drawCircle(gx, by - 30, 16, P(C(255, int(120 + 80 * g), 40)))
    c.drawCircle(bx, by - 40, 160, P(Shader=T.rad(bx, by - 40, 160, [C(255, 150, 60, 90), C(255, 120, 40, 0)])))
    # the hand iron: two round plates on long handles, hinged; opens and closes as he works
    hx, hy = T.hand_pos(380, 1650, 1.7, pose, 1)
    base = math.degrees(math.atan2(1545 - hy, 790 - hx))       # the plates rest right over the coals
    Lh = math.hypot(790 - hx, 1545 - hy) - 44
    for j, a in enumerate((base, base - 26 * open_amt)):         # lower plate fixed, upper plate hinges open
        c.save()
        c.translate(hx, hy)
        c.rotate(a)
        c.drawLine(0, 0, Lh, 0, S(C(40, 35, 35), 10))
        c.drawCircle(Lh + 44, 0, 44, P(C(55, 50, 50)))
        c.drawCircle(Lh + 44, 0, 44, S(C(20, 18, 18), 4))
        c.restore()
    if open_amt > 0.25:
        cookie(c, 790, 1530, 0.45, base - 90 + 90, kind="senbei")
    for i in range(10):
        ph = (k * 0.45 + i / 10) % 1
        px = 760 + 30 * math.sin(i * 2.1 + ph * 4)
        py = 1540 - 600 * (1 - math.exp(-2.4 * ph))
        c.drawCircle(px, py, 18 + 40 * ph, P(C(255, 255, 255, int(110 * (1 - ph)))))
    E.over(img, E.arr(s))
    cam = E.catmull([(t0, 1.0, 540, 1000), (t0 + 4.5, 1.08, 600, 1080)], t)
    lay = [E.stamp_layer(t, "KYOTO 1878", word_t("kyoto", "kyoto"), 540, 420, 120, (200, 40, 35), -6)]
    return img, cam, lay


@lru_cache(maxsize=None)
def bg_tray():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(40, 25, 30), C(70, 45, 40)])))
    c.drawRoundRect(skia.Rect(60, 900, 1020, 1750), 40, 40, P(Shader=T.lin((0, 900), (0, 1750), [C(170, 110, 60), C(120, 70, 35)])))
    for k in range(12):
        c.drawLine(80, 940 + k * 65, 1000, 950 + k * 65, S(C(90, 50, 25, 90), 3))
    c.drawRoundRect(skia.Rect(60, 900, 1020, 1750), 40, 40, S(T.OUT, 8))
    return E.arr(s)


def sc_tray(t, f):
    t0 = line_t("darker") - 0.12
    img = np.array(bg_tray())
    s, c = E.surf()
    tb, td, ts, tm, tf = (word_t("darker", w) for w in ("bigger", "darker", "sesame", "miso", "fold"))
    grow = snap(t, tb, 7, 1.3)
    dark = ramp(t, td, 0.35)
    # the modern cookie (small, pale) on the right for comparison
    cookie(c, 790, 1420, 1.5, -8)
    # the senbei: grows bigger on "bigger", darkens on "darker" (crossfade), slip slides into the outside fold on "fold"
    sc_ = 1.9 + 1.1 * grow
    if dark < 1:
        cookie(c, 360, 1360, sc_, 6)
    if dark > 0:
        lay = c.saveLayerAlpha(None, int(255 * dark))
        cookie(c, 360, 1360, sc_, 6, kind="senbei", slip=ramp(t, tf - 0.15, 0.4))
        c.restore()
    E.over(img, E.arr(s))
    img[..., :3] += E.glow_map(540, 1250, 520, 420)[..., None] * 0.10 * np.array([1.0, 0.7, 0.4], np.float32)
    cam = E.catmull([(t0, 1.0, 540, 1100), (t0 + 4.5, 1.06, 500, 1130)], t)
    lay = [E.title_layer(t, [("BIGGER", 120, 300, E.WHITE, tb), ("DARKER", 120, 440, E.GOLD, td)]),
           E.title_layer(t, [("SESAME + MISO", 70, 1830, E.WHITE, ts)]),
           arrow_label(t, tf, "FORTUNE IN THE FOLD", 360 + 40 * (1.9 + 1.1 * grow) * 0.6, 1360 + 10, 620, 1000)]
    return img, cam, lay


def arrow_label(t, at, text, tx, ty, lx, ly):
    """A label that pops in on its word with a hand-drawn arrow to (tx, ty). Screen space."""
    s, c = E.surf(world=False)
    k = t - at
    if k >= 0:
        u = clamp(k / 0.3)
        a = int(255 * u)
        f = skia.Font(T.FB, 54)
        w = f.measureText(text)
        c.drawRoundRect(skia.Rect(lx - w / 2 - 24, ly - 58, lx + w / 2 + 24, ly + 18), 18, 18, P(C(20, 12, 20, int(170 * u))))
        c.drawString(text, lx - w / 2, ly, f, P(C(255, 236, 160, a)))
        ar = skia.Path()
        ar.moveTo(lx, ly + 22)
        ar.quadTo((lx + tx) / 2 + 60, (ly + ty) / 2, tx, ty)
        meas = skia.PathMeasure(ar, False)
        seg = skia.Path()
        meas.getSegment(0, meas.getLength() * u, seg, True)
        c.drawPath(seg, S(C(255, 236, 160, a), 8))
        if u >= 1:
            pos, tan = meas.getPosTan(meas.getLength())
            ang = math.atan2(tan.y(), tan.x())
            hp = path([(tx, ty), (tx - 30 * math.cos(ang - 0.5), ty - 30 * math.sin(ang - 0.5)), (tx - 30 * math.cos(ang + 0.5), ty - 30 * math.sin(ang + 0.5))])
            c.drawPath(hp, P(C(255, 236, 160, a)))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_ship():
    s, c = E.surf()
    hor = 1150
    c.drawRect(skia.Rect(0, 0, W, hor), P(Shader=T.lin((0, 0), (0, hor), [C(40, 30, 80), C(170, 80, 120), C(250, 150, 100), C(255, 200, 140)], [0, 0.45, 0.8, 1])))
    c.drawCircle(820, 1060, 110, P(C(255, 240, 200)))
    c.drawCircle(820, 1060, 300, P(Shader=T.rad(820, 1060, 300, [C(255, 210, 150, 120), C(255, 180, 120, 0)])))
    # California hills on the right
    c.drawPath(path([(560, hor), (700, 1060), (820, 1090), (950, 1020), (1080, 1050), (1080, hor)]), P(C(110, 70, 100)))
    c.drawRect(skia.Rect(0, hor, W, H), P(Shader=T.lin((0, hor), (0, H), [C(160, 90, 120), C(60, 50, 105), C(25, 35, 80)])))
    r = random.Random(6)
    for k in range(60):
        y = hor + 15 + (k / 60) ** 1.5 * 760
        x = r.uniform(-50, W)
        c.drawLine(x, y, x + 30 + (y - hor) * 0.2, y, S(C(220, 150, 170, 80), 2 + (y - hor) / 200))
    return E.arr(s)


def sc_ship(t, f):
    t0 = line_t("california") - 0.12
    k = t - t0
    img = np.array(bg_ship())
    s, c = E.surf()
    sx = lerp(-60, 520, smooth(k / 3.0))
    bob = 6 * noise1(t, 31, 1.2)
    roll = 2.0 * noise1(t, 32, 0.9)
    c.save()
    c.translate(sx, 1235 + bob)
    c.rotate(roll)
    hull = path([(-230, -40), (230, -50), (190, 40), (-190, 40)])
    c.drawPath(hull, P(C(50, 30, 40)))
    c.drawRect(skia.Rect(-140, -110, 140, -40), P(C(235, 225, 215)))
    c.drawRect(skia.Rect(-140, -110, 140, -40), S(T.OUT, 4))
    for i in range(6):
        c.drawCircle(-110 + i * 44, -75, 9, P(C(255, 210, 130)))
    c.drawRect(skia.Rect(-30, -200, 20, -110), P(C(200, 50, 45)))
    c.drawRect(skia.Rect(-30, -200, 20, -180), P(C(40, 30, 30)))
    c.drawPath(hull, S(T.OUT, 5))
    c.restore()
    for i in range(10):   # funnel smoke: rises, slows (drag), drifts back, fades
        ph = (k * 0.6 + i / 10) % 1
        px = sx - 5 - 260 * ph
        py = 1235 + bob - 205 - 280 * (1 - math.exp(-2 * ph))
        c.drawCircle(px, py, 20 + 50 * ph, P(C(220, 210, 220, int(150 * (1 - ph)))))
    # wake glints
    for i in range(14):
        wx = sx - 240 - i * 40
        c.drawLine(wx, 1275 + (i % 3) * 8, wx + 30, 1275 + (i % 3) * 8, S(C(255, 230, 220, int(160 * (1 - i / 14))), 3))
    E.over(img, E.arr(s))
    cam = E.catmull([(t0, 1.0, 540, 1000), (t0 + 3, 1.06, 560, 1020)], t)
    lay = [E.title_layer(t, [("TO", 80, 300, E.WHITE, t0 + 0.1), ("CALIFORNIA", 150, 460, E.GOLD, word_t("california", "california"))])]
    return img, cam, lay


@lru_cache(maxsize=None)
def bg_teagarden():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, 1100), [C(120, 170, 200), C(220, 230, 210)])))
    # pagoda
    px = 820
    for i in range(4):
        w = 220 - i * 40
        y = 980 - i * 110
        c.drawPath(path([(px - w, y), (px + w, y), (px + w * 0.7, y - 40), (px - w * 0.7, y - 40)]), P(C(60, 40, 40)))
        c.drawRect(skia.Rect(px - w * 0.55, y, px + w * 0.55, y + 70), P(C(200, 60, 45)))
    # pines + maples
    r = random.Random(12)
    for i in range(14):
        x, y = r.uniform(-50, W + 50), r.uniform(950, 1150)
        c.drawCircle(x, y, r.uniform(70, 120), P(C(*r.choice(((60, 110, 70), (80, 130, 80), (200, 80, 60))))))
    c.drawRect(skia.Rect(0, 1150, W, H), P(C(90, 140, 90)))
    # pond + red drum bridge
    c.drawOval(skia.Rect(-100, 1200, 1180, 1500), P(Shader=T.lin((0, 1200), (0, 1500), [C(110, 160, 180), C(60, 110, 140)])))
    br = skia.Path()
    br.moveTo(150, 1340)
    br.cubicTo(300, 1060, 640, 1060, 790, 1340)
    c.drawPath(br, S(C(30, 20, 20), 34))
    c.drawPath(br, S(C(215, 55, 40), 24))
    for k in range(9):
        x = 200 + k * 68
        yy = 1340 - 260 * math.sin(math.pi * (x - 150) / 640)
        c.drawLine(x, yy, x, yy - 60, S(C(215, 55, 40), 8))
    c.drawRect(skia.Rect(0, 1520, W, H), P(Shader=T.lin((0, 1520), (0, H), [C(150, 100, 60), C(100, 60, 35)])))   # tea table
    c.drawLine(0, 1520, W, 1520, S(T.OUT, 6))
    return E.arr(s)


def sc_teagarden(t, f):
    t0 = line_t("teagarden") - 0.12
    k = t - t0
    img = np.array(bg_teagarden())
    t_tea = word_t("teagarden", "tea", 2)
    t_th = word_t("teagarden", "thousands")
    t_fam = word_t("teagarden", "family")
    second = t >= t_fam - 0.1
    reach = snap(t, t_tea - 0.2, 8, 1.2)
    pose = dict(eyes="open", brows="up", mouth="smile", look=(0.4, 0.5), lean=3, tilt=5,
                hands=[(-10, 140), lerp2((20, 140), (80, 60), reach)], bends=(1, -1), blink=0 <= (k % 2.7) < 0.1)
    if not second:
        ch = E.draw_person(LOOK_GUEST, 330, 1750, 1.8, pose, t)
        img = E.light_char(ch, img, 1750, shadow=0.0, rim_col=(1.0, 0.9, 0.7), rim=0.35)
    s, c = E.surf()
    if not second:
        teacup(c, 620, 1600, 1.4, t)
        teacup(c, 880, 1620, 1.2, t)
        c.drawOval(skia.Rect(640, 1660, 1000, 1720), P(C(245, 245, 240)))
        c.drawOval(skia.Rect(640, 1660, 1000, 1720), S(T.OUT, 4))
        for i in range(4):
            cookie(c, 700 + i * 80, 1670, 0.9, -10 + i * 8)
    else:
        # the family bakery: cookies pour into a big wooden tray and pile up (gravity, bounce 0.3, settle)
        c.drawRoundRect(skia.Rect(80, 1560, 1000, 1760), 30, 30, P(C(150, 100, 55)))
        c.drawRoundRect(skia.Rect(80, 1560, 1000, 1760), 30, 30, S(T.OUT, 6))
        n = int(clamp((t - t_fam) / 2.2) * 70) + 1
        for (x, y, ang, landed) in falling_bodies(70, 8, t, t_fam, (160, 920), 700, 1600, g=2600, stagger=2.2 / 70):
            cookie(c, x, y - 20, 0.85, ang * 0.15)
    E.over(img, E.arr(s))
    cam = E.catmull([(t0, 1.0, 540, 1050), (t_fam, 1.05, 560, 1080), (t0 + 5.5, 1.08, 540, 1100)], t)
    lay = [E.title_layer(t, [("SAN FRANCISCO", 110, 300, E.WHITE, word_t("teagarden", "san"))])]
    if second:
        lay.append(E.title_layer(t, [("BY THE THOUSANDS", 110, 450, E.GOLD, t_th)]))
    return img, cam, lay


@lru_cache(maxsize=None)
def bg_bakery42():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, 1500), [C(110, 120, 135), C(160, 165, 170)])))   # overcast
    # storefront
    c.drawRect(skia.Rect(80, 740, 1000, 1500), P(C(150, 130, 115)))
    c.drawRect(skia.Rect(80, 740, 1000, 1500), S(C(40, 35, 35), 6))
    c.drawRect(skia.Rect(120, 770, 960, 890), P(C(60, 70, 80)))
    f = skia.Font(T.FB, 96)
    w = f.measureText("BAKERY")
    c.drawString("BAKERY", 540 - w / 2, 865, f, P(C(225, 215, 190)))
    c.drawRect(skia.Rect(140, 930, 560, 1300), P(Shader=T.lin((0, 930), (0, 1300), [C(90, 100, 115), C(60, 70, 85)])))   # window
    c.drawRect(skia.Rect(140, 930, 560, 1300), S(C(40, 35, 35), 6))
    c.drawRect(skia.Rect(640, 950, 920, 1500), P(C(95, 70, 55)))     # door
    c.drawRect(skia.Rect(640, 950, 920, 1500), S(C(40, 35, 35), 6))
    c.drawRect(skia.Rect(0, 1500, W, H), P(Shader=T.lin((0, 1500), (0, H), [C(120, 120, 125), C(85, 85, 90)])))   # pavement
    for k in range(6):
        c.drawLine(0, 1560 + k * 70, W, 1560 + k * 70, S(C(70, 70, 75, 120), 3))
    return E.arr(s)


def sc_bakery42(t, f):
    """1942: told plainly and respectfully - muted palette, no jokes, no slams on the people."""
    t0 = line_t("camps") - 0.12
    k = t - t0
    img = np.array(bg_bakery42())
    t_closed = word_t("camps", "closed")
    t_homes = line_t("homes")
    walk = clamp(k / 6.5)
    for i, (look, x0, s_) in enumerate(((LOOK_DAD, 520, 1.45), (LOOK_MOM, 680, 1.4), (LOOK_KID, 800, 1.0))):
        x = x0 - 460 * smooth(walk) - 30 * i * walk
        ph = k * 5.5 + i
        pose = dict(eyes="sad", brows="sad", mouth="frown", look=(-0.6, 0.2), lean=-2, tilt=-4, walk=ph if 0 < walk < 1 else None,
                    hands=[(-20, 150), (25, 140)], bends=(1, -1))
        ch = E.draw_person(look, x, 1800, s_, pose, t,
                           extra=(lambda c, x=x, s_=s_, i=i: suitcase(c, x + 75 * s_, 1800 - 60 * s_, 0.8 * s_, ((120, 75, 45), (90, 80, 70), (130, 100, 60))[i])))
        img = E.light_char(ch, img, 1800, shadow=0.3, rim_col=(0.7, 0.75, 0.85), rim=0.25)
    s, c = E.surf()
    # the CLOSED sign: hung on the door on "closed", swings as a damped pendulum (real period for a 25 cm string)
    if t >= t_closed:
        kk = t - t_closed
        om = 2 * math.pi / (2 * math.pi * math.sqrt(0.25 / 9.81))
        th = 22 * math.exp(-1.6 * kk) * math.cos(om * kk)
        c.save()
        c.translate(780, 1010)
        c.rotate(th)
        c.drawLine(0, 0, -70, 70, S(C(40, 30, 25), 3))
        c.drawLine(0, 0, 70, 70, S(C(40, 30, 25), 3))
        c.drawRoundRect(skia.Rect(-110, 70, 110, 160), 10, 10, P(C(235, 225, 205)))
        c.drawRoundRect(skia.Rect(-110, 70, 110, 160), 10, 10, S(C(40, 30, 25), 4))
        f2 = skia.Font(T.FB, 54)
        w2 = f2.measureText("CLOSED")
        c.drawString("CLOSED", -w2 / 2, 135, f2, P(C(170, 35, 40)))
        c.restore()
    # falling leaves (drag + flutter)
    for i in range(10):
        lx, ly, la = flutter(k + i * 0.6, 0, 100 + i * 95, -40, 40 + i)
        ly = ly % (H + 80) - 40
        c.save()
        c.translate(lx, ly)
        c.rotate(la)
        c.drawOval(skia.Rect(-12, -6, 12, 6), P(C(160, 110, 60, 200)))
        c.restore()
    E.over(img, E.arr(s))
    # muted grade (desaturate toward blue-grey)
    lum = img[..., :3].mean(axis=2, keepdims=True)
    img[..., :3] = img[..., :3] * 0.55 + lum * 0.45 * np.array([0.95, 1.0, 1.08], np.float32)
    cam = E.catmull([(t0, 1.0, 540, 1050), (t_homes, 1.05, 520, 1060), (t0 + 11, 1.12, 640, 1000)], t)
    lay = [E.title_layer(t, [("1942", 140, 340, [C(235, 235, 240), C(190, 195, 205)], word_t("camps", "nineteen"))])]
    if t >= t_homes - 0.05:
        lay.append(E.title_layer(t, [("120,000 PEOPLE", 96, 500, [C(235, 235, 240), C(190, 195, 205)], word_t("homes", "people"))]))
    return img, cam, lay


@lru_cache(maxsize=None)
def bg_factory():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(55, 60, 80), C(95, 95, 110)])))
    for k in range(5):   # windows with light shafts
        x = 60 + k * 210
        c.drawRect(skia.Rect(x, 520, x + 150, 780), P(C(250, 220, 160)))
        c.drawRect(skia.Rect(x, 520, x + 150, 780), S(C(30, 30, 40), 5))
        c.drawPath(path([(x, 780), (x + 150, 780), (x + 260, 1500), (x + 60, 1500)]), P(C(255, 230, 170, 30)))
    c.drawRect(skia.Rect(0, 1500, W, H), P(C(70, 70, 80)))
    return E.arr(s)


def sc_factory(t, f):
    t0 = line_t("factories") - 0.12
    k = t - t0
    t_put = word_t("factories", "put")
    t_meal = word_t("factories", "meal")
    if t < t_put - 0.1:
        img = np.array(bg_factory())
        pose = dict(eyes="open", brows="flat", mouth="smile", look=(0.5, 0.6), lean=4, tilt=3,
                    hands=[(30, 60 + 10 * math.sin(k * 6)), (60, 70 + 10 * math.sin(k * 6 + 1.5))], bends=(-1, -1), blink=0 <= (k % 2.9) < 0.1)
        ch = E.draw_person(LOOK_WORKER, 230, 1560, 1.6, pose, t)
        img = E.light_char(ch, img, 1560, shadow=0.25, rim=0.4)
        s, c = E.surf()
        # conveyor belt: rollers turn, cookies ride it at belt speed (no slipping)
        v = 160.0
        c.drawRoundRect(skia.Rect(-40, 1380, W + 40, 1440), 30, 30, P(C(45, 45, 55)))
        for i in range(14):
            rx = 20 + i * 80
            c.drawCircle(rx, 1410, 24, P(C(120, 120, 130)))
            a = (k * v / 24) + i
            c.drawLine(rx, 1410, rx + 20 * math.cos(a), 1410 + 20 * math.sin(a), S(C(60, 60, 70), 4))
        off = (k * v) % 120
        for i in range(-1, 10):
            cookie(c, 300 + i * 120 + off, 1350, 0.75)
        # folding press: stamps down periodically
        prs = max(0.0, math.sin(k * 4.2)) ** 6
        c.drawRect(skia.Rect(620, 900, 760, 1260 + 70 * prs), P(C(150, 150, 165)))
        c.drawRect(skia.Rect(600, 1240 + 70 * prs, 780, 1290 + 70 * prs), P(C(110, 110, 125)))
        c.drawRect(skia.Rect(600, 1240 + 70 * prs, 780, 1290 + 70 * prs), S(T.OUT, 4))
        E.over(img, E.arr(s))
        cam = E.catmull([(t0, 1.0, 540, 1100), (t_put, 1.06, 600, 1120)], t)
        lay = [E.title_layer(t, [("CHINESE-AMERICAN", 90, 300, E.WHITE, word_t("factories", "american")),
                                 ("FACTORIES", 140, 450, E.GOLD, word_t("factories", "factories"))])]
    else:
        img = np.array(bg_restaurant())
        s, c = E.surf()
        for i, (lx, ly, r) in enumerate(((150, 760, 70), (930, 760, 70))):
            lantern(c, lx, ly, r, t, i * 1.7)
        E.over(img, E.arr(s))
        kk = t - t_put
        pose = dict(eyes="open", brows="flat", mouth="smile", look=(0.3, 0.6), lean=6, tilt=6,
                    hands=[(-20, 150), lerp2((60, 80), (120, 140), smooth(kk / 0.6))], bends=(1, -1))
        ch = E.draw_person(LOOK_WAITER, 700, 1880, 2.0, pose, t)
        img = E.light_char(ch, img, 1880, shadow=0, rim_col=(1.0, 0.55, 0.45), rim=0.5)
        s, c = E.surf()
        table_front(c, 1480)
        c.drawOval(skia.Rect(300, 1510, 640, 1580), P(C(250, 250, 250)))
        c.drawOval(skia.Rect(300, 1510, 640, 1580), S(T.OUT, 4))
        # the cookie set down: lowers from the hand onto the plate, then rests (no hover: contact at y=1535)
        hx, hy = T.hand_pos(700, 1880, 2.0, pose, 1)
        u = smooth(kk / 0.6)
        cy_ = lerp(hy - 20, 1535, u)
        cx_ = lerp(hx - 40, 470, u)
        cookie(c, cx_, cy_ - 20, 1.3)
        c.drawRect(skia.Rect(140, 1525, 260, 1575), P(C(250, 250, 240)))   # the check
        c.drawRect(skia.Rect(140, 1525, 260, 1575), S(T.OUT, 3))
        E.over(img, E.arr(s))
        cam = E.catmull([(t_put, 1.04, 500, 1060), (t_put + 3, 1.1, 480, 1100)], t)
        lay = [E.title_layer(t, [("EVERY CHINESE", 100, 300, E.WHITE, word_t("factories", "every")),
                                 ("MEAL", 170, 470, E.GOLD, t_meal)])]
    return img, cam, lay


def sc_pile(t, f):
    t0 = line_t("billion") - 0.12
    k = t - t0
    img = np.array(bg_factory())
    s, c = E.surf()
    # a mountain of cookies: rain down, bounce once (0.3), settle into a heap that grows
    heap_h = 520 * smooth(clamp(k / 6))
    c.drawPath(path([(-80, H), (540 - 700, H), (540, H - heap_h - 60), (540 + 700, H)]), P(Shader=T.lin((0, H - heap_h), (0, H), [C(240, 180, 80), C(170, 110, 40)])))
    r = random.Random(77)
    for i in range(150):
        u = r.uniform(-0.95, 0.95)
        hh = (1 - abs(u)) * heap_h
        y = H - r.uniform(0, hh)
        if hh > 20:
            cookie(c, 540 + u * 680, y, 0.7, r.uniform(-40, 40))
    for (x, y, ang, landed) in falling_bodies(60, 5, t, t0, (100, 980), -100, H - heap_h - 30, g=2200, stagger=0.09):
        if not landed:
            cookie(c, x, y, 0.8, ang * 0.3)
    E.over(img, E.arr(s))
    cam = E.catmull([(t0, 1.0, 540, 1000), (t0 + 6, 1.06, 540, 1040)], t)
    n = 3_000_000_000 * smooth(clamp((t - word_t("billion", "billion") + 0.6) / 0.8))
    lay = [E.title_layer(t, [(f"{int(n):,}", 120, 330, E.GOLD, word_t("billion", "three") - 0.1), ("EVERY YEAR", 90, 460, E.WHITE, word_t("billion", "year"))])]
    if t >= line_t("daily") - 0.05:
        lay.append(E.stamp_layer(t, "4,000,000 A DAY", word_t("daily", "four"), 540, 700, 96, (230, 60, 50), -5))
    return img, cam, lay


@lru_cache(maxsize=None)
def bg_china():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(180, 200, 220), C(230, 220, 200)])))
    c.drawRect(skia.Rect(0, 1400, W, H), P(C(150, 140, 130)))
    # a shop front with an upturned roof
    c.drawPath(path([(40, 640), (1040, 640), (1000, 560), (80, 560)]), P(C(60, 50, 50)))
    c.drawPath(path([(40, 640), (-20, 600), (80, 560)]), P(C(60, 50, 50)))
    c.drawPath(path([(1040, 640), (1100, 600), (1000, 560)]), P(C(60, 50, 50)))
    c.drawRect(skia.Rect(90, 640, 990, 1400), P(C(200, 70, 55)))
    c.drawRect(skia.Rect(150, 760, 930, 1250), P(C(250, 240, 220)))
    c.drawRect(skia.Rect(150, 760, 930, 1250), S(T.OUT, 6))
    for k in range(3):   # shelves
        c.drawRect(skia.Rect(170, 900 + k * 140, 910, 915 + k * 140), P(C(130, 80, 50)))
    f = skia.Font(T.FB, 64)
    w = f.measureText("FORTUNE COOKIES")
    c.drawRoundRect(skia.Rect(540 - w / 2 - 30, 670, 540 + w / 2 + 30, 745), 12, 12, P(C(250, 210, 80)))
    c.drawString("FORTUNE COOKIES", 540 - w / 2, 730, f, P(C(120, 20, 25)))
    return E.arr(s)


def cookie_box(c, x, y, s=1.0, rot=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    c.drawRect(skia.Rect(-50, -110, 50, 0), P(Shader=T.lin((-50, 0), (50, 0), [C(250, 200, 80), C(230, 160, 50)])))
    c.drawRect(skia.Rect(-50, -110, 50, 0), S(T.OUT, 4))
    cookie(c, 0, -55, 0.5)
    c.restore()


def sc_china(t, f):
    t0 = line_t("flop") - 0.12
    k = t - t0
    img = np.array(bg_china())
    t_flop = word_t("flop", "flopped")
    t_too = word_t("flop", "to")
    # shoppers glance and walk on; one shrugs on "flopped"
    for i, (look, x0, dirn, yb, sc_) in enumerate(((LOOK_SHOPPER2, 1200, -1, 1700, 1.15), (LOOK_SHOPPER, -120, 1, 1830, 1.5))):
        i = 1 - i   # keep the shrug on the near shopper
        x = x0 + dirn * 190 * k
        sh = snap(t, t_flop, 6, 1.3) if i == 0 else 0
        pose = dict(eyes="open", brows="flat" if sh < 0.3 else "up", mouth="smile" if sh < 0.3 else "frown", look=(0.8 * dirn, 0), lean=0,
                    tilt=-4 * sh, walk=k * 6 + i, hands=[lerp2((-20, 150), (-90, -30), sh), lerp2((20, 150), (90, -30), sh)], bends=(1, -1))
        ch = E.draw_person(look, x, yb, sc_, pose, t)
        img = E.light_char(ch, img, yb, shadow=0.35, rim=0.4)
    s, c = E.surf()
    # boxes on the shelves; on "flopped" one tips over the shelf edge: rigid body rotation about the edge, then a fall
    for row in range(3):
        for i in range(6):
            bx, by = 240 + i * 120, 900 + row * 140
            if row == 0 and i == 5 and t >= t_flop:
                kk = t - t_flop
                ang = min(90, 0.5 * 1800 * kk * kk)          # tipping: angular acceleration about the edge
                if ang < 90:
                    cookie_box(c, bx + 50, by, 0.9, ang)
                else:
                    tf = kk - math.sqrt(90 / 900)
                    yy = by + 0.5 * 2600 * tf * tf
                    cookie_box(c, bx + 100, min(yy, 1400), 0.9, 90)
            else:
                cookie_box(c, bx, by, 0.9)
    E.over(img, E.arr(s))
    cam = E.catmull([(t0, 1.0, 540, 1050), (t0 + 4, 1.05, 560, 1060)], t)
    lay = [E.title_layer(t, [("CHINA, 1992", 110, 330, E.WHITE, word_t("flop", "china"))]),
           E.stamp_layer(t, "TOO AMERICAN", t_too, 540, 505, 100, (220, 35, 45), -5)]
    return img, cam, lay


def sc_reveal(t, f):
    return sc_restaurant(t, f, reveal=True)


def sc_cta(t, f):
    from cta2 import draw_cta2
    img, cam, lay = sc_restaurant(t, f, reveal=True)
    img = E.gblur(img, 10)
    img[..., :3] *= 0.6
    t0 = line_t("cta") - 0.12
    s, c = E.surf(world=False)
    draw_cta2(c, t - t0, word_t("cta", "like") - t0, word_t("cta", "subscribe") - t0)
    return img, (1.16, 540, 1040), [E.arr(s)]


RENDER = dict(restaurant=sc_restaurant, sunrise=sc_sunrise, kyoto=sc_kyoto, tray=sc_tray, ship=sc_ship, teagarden=sc_teagarden,
              bakery42=sc_bakery42, factory=sc_factory, pile=sc_pile, china=sc_china, reveal=sc_reveal, cta=sc_cta)


# =================================================================================== transitions (gold splat)
# cuts inside a scene (tea garden -> bakery tray, factory -> restaurant table): they get the splat too
INNER_CUTS = [word_t("teagarden", "family") - 0.1, word_t("factories", "put") - 0.1]


def splat_cuts():
    out = [CUTS[i] for i in range(1, len(SCENES))
           if not (SCENES[i][0] in ("bakery42", "cta") or SCENES[i - 1][0] == "bakery42")]
    return sorted(out + INNER_CUTS)


def splat_layer(t):
    """Gold ink splat wipe: grows over 4 frames to cover the cut, then clears over 5 frames. Not used into/out of 1942."""
    for i, tc in enumerate(splat_cuts(), start=1):
        k = t - tc
        if -4 / FPS <= k < 5 / FPS:
            u = (k + 4 / FPS) / (4 / FPS) if k < 0 else 1 - k / (5 / FPS)
            u = smooth(clamp(u))
            s, c = E.surf(world=False)
            r = random.Random(i)
            cx, cy = 540 + r.uniform(-120, 120), 960 + r.uniform(-200, 200)
            R = 1250 * u
            blob = skia.Path()
            blob.addCircle(cx, cy, R)
            for j in range(14):
                a = r.uniform(0, 2 * math.pi)
                d = R * r.uniform(0.85, 1.1)
                blob.addCircle(cx + d * math.cos(a), cy + d * math.sin(a), R * r.uniform(0.12, 0.25))
            c.drawPath(blob, P(Shader=T.rad(cx, cy, max(1, R), [C(255, 225, 120), C(235, 165, 40), C(190, 120, 25)])))
            return E.arr(s)
    return None


def fade_42(t):
    """Into and out of 1942: a slow dip to black instead of a splat (tone)."""
    for i in range(1, len(SCENES)):
        if SCENES[i][0] == "bakery42" or SCENES[i - 1][0] == "bakery42":
            k = t - CUTS[i]
            if abs(k) < 0.25:
                return 1 - abs(k) / 0.25
    return 0.0


# =================================================================================== frame
def render(f, out=None):
    t = f / FPS
    i = scene_at(t)
    name = SCENES[i][0]
    img, cam, lays = RENDER[name](t, f)
    z, cx, cy = cam
    shake = (0, 0)
    for at in (word_t("hook", "chinese"), word_t("flop", "to")):   # 3-frame micro-shake on the two big slams
        kk = int((t - at) * FPS + 1e-6)
        if 0 <= kk < 3:
            shake = ((4, -3), (-3, 2), (1, -1))[kk]
    rgb = E.crop(img, z, cx, cy, shake)
    for lay in lays:
        rgb = E.comp_screen(rgb, lay)
    sp = splat_layer(t)
    if sp is not None:
        rgb = E.comp_screen(rgb, sp)
    rgb = E.finish(rgb, f, bloom=0.5 if name == "bakery42" else 1.0)
    d = fade_42(t)
    if d > 0:
        rgb *= (1 - 0.9 * d)
    E.save(rgb, out or os.path.join(D, "frames", f"{f + 1:04d}.png"))
    return f


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "frames"
    print("duration", round(DUR, 2), "s,", NF, "frames; cuts", [round(x, 2) for x in CUTS])
    if mode == "stills":
        os.makedirs(os.path.join(D, "stills"), exist_ok=True)
        for ts in sys.argv[2].split(","):
            f = int(round(float(ts) * FPS))
            render(f, os.path.join(D, "stills", f"s_{float(ts):05.2f}.png"))
            print("still", ts, SCENES[scene_at(f / FPS)][0])
    else:
        os.makedirs(os.path.join(D, "frames"), exist_ok=True)
        todo = [f for f in range(NF) if os.environ.get("SKIP") != "1" or not os.path.exists(os.path.join(D, "frames", f"{f + 1:04d}.png"))]
        with Pool(int(os.environ.get("PROCS", "6"))) as pool:
            for j, f in enumerate(pool.imap_unordered(render, todo, chunksize=4)):
                if j % 150 == 0:
                    print("frame", j, "/", len(todo), flush=True)
        print("done")
