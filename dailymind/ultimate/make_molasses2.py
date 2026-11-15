"""YouTube Short: "The Great Molasses Flood" (Boston, 15 Jan 1919) - in the canary-video look: the channel's toon
characters inside real lit 3D Blender plates (blender/boston_plates.py), the approved 2D engine finish, title slams,
stamps, gold splats, and the CTA v2 end card. Voice: vidIQ "Chris" (chris.wav, timings by faster-whisper: chris_timing.py).

Facts: a 2.3-million-gallon tank by Boston's harbor burst; a wave up to ~25 ft swept the North End; the cold thickened it;
21 dead, ~150 hurt; the harbor stayed brown for months. The tank leaked from the start (neighbours collected the
drips); it was painted brown, never tested with water; the company blamed anarchists; the court held it responsible
(~$628,000 in settlements); Boston then required engineers' calculations to be filed and signed. (Wikipedia,
Smithsonian, Boston Globe.) Generic cartoon people; no likenesses.

  python make_molasses2.py stills 1.0,5.2     -> ../molasses2/stills/
  python make_molasses2.py frames             -> ../molasses2/frames/%04d.png (multiprocess, PROCS=4)
"""
import json
import math
import os
import random
import sys
from multiprocessing import Pool

import numpy as np
import skia
from PIL import Image

import style2d_engine as E
import toon as T
from style2d_engine import C, P, S, BLUR, W, H, K, FPS, lerp, clamp, ramp, snap, smooth, noise1

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "molasses2")
PL_DIR = os.path.join(D, "plates")
TIMES = json.load(open(os.path.join(D, "vo_final.wav.times.json")))
WORDS = json.load(open(os.path.join(D, "vo_final.wav.words.json")))
LINES = json.load(open(os.path.join(D, "lines_final.json")))
ORDER = [l["key"] for l in LINES]
DUR = round(min(64.6, max(61.5, TIMES["cta"] + 3.9)), 3)
NF = int(round(DUR * FPS))
OUT_FR = os.path.join(D, "frames")
PHYS = {}
G_PX = 3600.0            # px/s^2 : a 1.75 m toon is ~770 px tall here -> 9.81 m/s^2 * 440 px/m ~ 4300, perspective ~0.85


def word_t(line, *cands, nth=1):
    nxt = ORDER.index(line) + 1
    t1 = TIMES[ORDER[nxt]] if nxt < len(ORDER) else 1e9
    for w in cands:
        hits = sorted(v for k, v in WORDS.items() if k.split("#")[0] == w and TIMES[line] - 0.3 <= v < t1 - 0.05)
        if len(hits) >= nth:
            return hits[nth - 1]
    raise KeyError(f"none of {cands} in line {line!r}")


def _cut(key):
    return TIMES[key] - 0.12


SCENES = [("hook", 0.0), ("tank", _cut("l01")), ("gallons", _cut("l02")), ("flatten", _cut("l03")), ("stuck", _cut("l04")),
          ("dead", _cut("l05")), ("harbor", _cut("l06")), ("crazy", _cut("l07")), ("leak", _cut("l08")), ("paint", _cut("l09")),
          ("wink", word_t("l09", "so") - 0.12), ("tested", _cut("l10")), ("blame", _cut("l11")), ("court", _cut("l12")),
          ("verdict", _cut("l13")), ("paid", word_t("l13", "paid") - 0.12), ("engineers", _cut("l14")), ("smell", _cut("l15")),
          ("leaky", _cut("l16")), ("cta", TIMES["cta"] - 0.3)]
CUTS = [t for _, t in SCENES] + [DUR]


def scene_at(t):
    for i in range(len(SCENES)):
        if CUTS[i] <= t < CUTS[i + 1]:
            return i
    return len(SCENES) - 1


def span(name):
    i = [n for n, _ in SCENES].index(name)
    return CUTS[i], CUTS[i + 1]


# =================================================================================== looks
EDDIE = dict(skin=(238, 196, 160), hair="cap", hair_col=(95, 85, 75), coat=(70, 95, 130), pants=(55, 52, 58), nose="small")
BOSS = dict(skin=(242, 205, 178), hair="neat", hair_col=(40, 30, 25), coat=(40, 40, 48), vest=(120, 35, 35), pants=(35, 35, 40),
            nose="long", mustache=True, hat="bowler")
JUDGE = dict(skin=(232, 192, 160), hair="grey", hair_col=(220, 220, 225), coat=(22, 22, 26), pants=(22, 22, 26), nose="long", glasses=True)
INK = C(30, 18, 14)

# =================================================================================== plates
_PL = {}


def plate(name, blur=0.0):
    key = (name, blur)
    if key not in _PL:
        im = Image.open(os.path.join(PL_DIR, f"plate_{name}.png")).convert("RGB").resize((E.WW, E.WH), Image.LANCZOS)
        a = np.asarray(im).astype(np.float32) / 255.0
        a = np.dstack([a, np.ones(a.shape[:2], np.float32)])
        if blur:
            a = E.gblur(a, blur)
        _PL[key] = a
    return _PL[key].copy()


META = {n: json.load(open(os.path.join(PL_DIR, f"plate_{n}.json"))) for n in
        ("wave", "flood", "tank", "burst", "tankclose", "tankbrown", "harbor", "court", "summer") if os.path.exists(os.path.join(PL_DIR, f"plate_{n}.json"))}


MOL_COL = (0.17, 0.075, 0.025)


def plate_col(name, x, y):
    return MOL_COL
    """Average plate colour around (x, y) in 1080-space (the molasses band in front of a waist-deep character)."""
    a = plate(name)
    xi, yi = int(x * K), int(y * K)
    return tuple(float(v) for v in a[yi - 6:yi + 6, max(0, xi - 60):xi + 60, :3].reshape(-1, 3).mean(0))


def char(img, look, x, y, s_, pose, t, shadow=0.5, rim=0.55, rim_col=(1.0, 0.85, 0.7), extra=None, blur=0):
    ch = E.draw_person(look, x, y, s_, pose, t, extra)
    if blur:
        return E.over(img, E.gblur(ch, blur))
    return E.light_char(ch, img, y, shadow=shadow, rim=rim, rim_col=rim_col)


def layer_over(img, draw):
    s, c = E.surf()
    draw(c)
    return E.over(img, E.arr(s))


def snowfall(c, t, n=70, seed=3):
    r = random.Random(seed)
    for k in range(n):
        x0, y0, sp, ph = r.uniform(0, W), r.uniform(0, H), r.uniform(60, 140), r.uniform(0, 6.28)
        x = (x0 + 25 * math.sin(t * 0.8 + ph) + 20 * t) % W
        y = (y0 + sp * t) % H
        c.drawCircle(x, y, r.uniform(2, 5), P(C(255, 255, 255, int(150 + 80 * math.sin(ph)))))


# =================================================================================== props
def can(c, x, y, s):
    c.save(); c.translate(x, y); c.scale(s, s)
    body = skia.Rect(-38, -10, 38, 80)
    c.drawRect(body, P(Shader=T.lin((-38, 0), (38, 0), [C(140, 145, 150), C(215, 220, 225), C(120, 125, 130)])))
    c.drawRect(body, S(INK, 6))
    c.drawOval(skia.Rect(-38, -22, 38, 2), P(C(70, 30, 10)))
    c.drawOval(skia.Rect(-38, -22, 38, 2), S(INK, 5))
    c.restore()


def brush(c, x, y, s, ang):
    c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s)
    c.drawRoundRect(skia.Rect(-8, -150, 8, 10), 6, 6, P(C(176, 122, 68))); c.drawRoundRect(skia.Rect(-8, -150, 8, 10), 6, 6, S(INK, 6))
    c.drawRect(skia.Rect(-30, -200, 30, -150), P(C(150, 150, 155))); c.drawRect(skia.Rect(-30, -200, 30, -150), S(INK, 6))
    c.drawRoundRect(skia.Rect(-32, -250, 32, -196), 6, 6, P(C(90, 45, 18))); c.drawRoundRect(skia.Rect(-32, -250, 32, -196), 6, 6, S(INK, 6))
    c.restore()


def paper(c, x, y, s, rot):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    r = skia.Rect(-150, -200, 150, 10)
    c.drawRect(r, P(C(238, 232, 214))); c.drawRect(r, S(INK, 7))
    f1, f2 = skia.Font(T.FB, 46), skia.Font(T.FB, 58)
    c.drawString("ANARCHIST", -f1.measureText("ANARCHIST") / 2, -140, f1, P(INK))
    c.drawString("BOMB?!", -f2.measureText("BOMB?!") / 2, -80, f2, P(C(190, 30, 30)))
    for k in range(4):
        c.drawRect(skia.Rect(-120, -50 + k * 14, 120, -44 + k * 14), P(C(120, 115, 105)))
    c.restore()


def gavel(c, x, y, s, ang):
    c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s)
    c.drawRoundRect(skia.Rect(-9, -150, 9, 10), 6, 6, P(C(120, 72, 36))); c.drawRoundRect(skia.Rect(-9, -150, 9, 10), 6, 6, S(INK, 6))
    c.drawRoundRect(skia.Rect(-60, -200, 60, -145), 12, 12, P(C(95, 55, 26))); c.drawRoundRect(skia.Rect(-60, -200, 60, -145), 12, 12, S(INK, 7))
    c.restore()


def moneybag(c, x, y, s):
    c.save(); c.translate(x, y); c.scale(s, s)
    p = skia.Path(); p.addOval(skia.Rect(-80, -40, 80, 120))
    c.drawPath(p, P(Shader=T.lin((0, -40), (0, 120), [C(220, 195, 130), C(175, 145, 85)]))); c.drawPath(p, S(INK, 7))
    c.drawRoundRect(skia.Rect(-26, -62, 26, -34), 8, 8, P(C(180, 150, 90))); c.drawRoundRect(skia.Rect(-26, -62, 26, -34), 8, 8, S(INK, 6))
    f = skia.Font(T.FB, 90)
    c.drawString("$", -f.measureText("$") / 2, 76, f, P(C(60, 110, 50)))
    c.restore()


def blueprint(c, x, y, s, stamped):
    c.save(); c.translate(x, y); c.rotate(-5); c.scale(s, s)
    r = skia.Rect(-170, -230, 170, 10)
    c.drawRect(r, P(C(40, 90, 160))); c.drawRect(r, S(INK, 7))
    for k in range(6):
        c.drawLine(-140, -200 + k * 36, 140, -200 + k * 36, S(C(200, 225, 255, 160), 3))
    c.drawCircle(40, -110, 60, S(C(220, 235, 255), 5))
    c.drawRect(skia.Rect(-120, -150, -30, -40), S(C(220, 235, 255), 5))
    if stamped > 0:
        c.save(); c.translate(0, -110); c.rotate(-12); sc = 1.8 - 0.8 * T.out_back(stamped, 1.6); c.scale(sc, sc)
        f = skia.Font(T.FB, 50)
        w = f.measureText("APPROVED")
        c.drawRoundRect(skia.Rect(-w / 2 - 18, -52, w / 2 + 18, 16), 10, 10, S(C(230, 40, 45, int(255 * min(1, stamped * 3))), 8))
        c.drawString("APPROVED", -w / 2, 0, f, P(C(230, 40, 45, int(255 * min(1, stamped * 3)))))
        c.restore()
    c.restore()


def smell(c, x, y, t):
    for k in range(3):
        ph = (t * 0.6 + k / 3) % 1.0
        path = skia.Path()
        for j in range(26):
            yy = y - ph * 260 - j * 8
            xx = x + k * 34 + math.sin(j * 0.5 + t * 3) * 18
            path.lineTo(xx, yy) if j else path.moveTo(xx, yy)
        c.drawPath(path, S(C(150, 80, 25, int(230 * math.sin(math.pi * ph))), 9))


def molasses_band(c, x, y_surf, half_w, col, t):
    """A thick glossy molasses surface drawn in front of a waist-deep character (top edge at y_surf, wavy)."""
    p = skia.Path()
    p.moveTo(x - half_w, H + 50)
    for k in range(41):
        xx = x - half_w + 2 * half_w * k / 40
        p.lineTo(xx, y_surf + 7 * math.sin(xx * 0.03 + t * 2.4) + 4 * math.sin(xx * 0.071 - t * 1.7))
    p.lineTo(x + half_w, H + 50)
    p.close()
    r, g, b = [int(255 * v) for v in col]
    c.drawPath(p, P(Shader=T.lin((0, y_surf - 10), (0, y_surf + 160), [C(min(255, r + 45), min(255, g + 25), min(255, b + 10)), C(r, g, b)])))
    c.drawPath(p, S(C(30, 12, 4, 200), 5))
    for k in range(4):        # specular streaks sliding along the surface
        xx = x - half_w * 0.7 + ((t * 40 + k * 90) % (half_w * 1.4))
        c.drawLine(xx, y_surf + 14 + k * 5, xx + 60, y_surf + 16 + k * 5, S(C(255, 220, 170, 110), 4))


def drips(c, t, x0, y0, floor_y, n=4, period=0.9, seed=1):
    """Molasses drops falling from the tank seam under gravity, landing exactly on floor_y (splat, no sink)."""
    r = random.Random(seed)
    for k in range(n):
        ph = (t / period + k / n) % 1.0
        tf = ph * period
        x = x0 + r.uniform(-40, 40)
        y = y0 + 0.5 * G_PX * tf * tf
        if y < floor_y:
            c.drawOval(skia.Rect(x - 7, y - 11, x + 7, y + 9), P(C(70, 30, 8)))
            c.drawOval(skia.Rect(x - 7, y - 11, x + 7, y + 9), S(INK, 3))
        else:
            c.drawOval(skia.Rect(x - 18, floor_y - 5, x + 18, floor_y + 4), P(C(70, 30, 8)))
    PHYS["drip_fall_s"] = math.sqrt(2 * (floor_y - y0) / G_PX)


# =================================================================================== scenes  -> (img, (zoom, cx, cy), [screen layers])
def push(name, z0, z1, c0, c1):
    a, b = span(name)

    def f(t):
        k = smooth((t - a) / (b - a))
        return lerp(z0, z1, k), lerp(c0[0], c1[0], k), lerp(c0[1], c1[1], k)
    return f


def sc_hook(t, f):
    img = plate("wave")
    run = 2 * math.pi * 2.6 * t
    pose = dict(eyes="wide", brows="up", mouth="O", amt=1.4, look=(0.2, -0.3), walk=run,
                hands=[(-40 + 20 * math.sin(run), -150), (40 - 20 * math.sin(run), -150)], lean=-6, tilt=4 * math.sin(run))
    x, y, s_ = 520 + 30 * t, 1820 + 6 * abs(math.sin(run)), 1.35 + 0.05 * t
    img = char(img, EDDIE, x, y, s_, pose, t)
    img = layer_over(img, lambda c: snowfall(c, t))
    lays = [E.title_layer(t, [("A 25-FOOT WAVE", 104, 300, E.WHITE, word_t("l00", "a", "25", "twentyfive")),
                              ("OF MOLASSES", 150, 460, E.GOLD, word_t("l00", "molasses"))])]
    z, cx, cy = push("hook", 1.12, 1.0, (540, 1000), (540, 960))(t)
    sh = (5 * noise1(t, 1, 9), 5 * noise1(t, 2, 9))
    return img, (z, cx + sh[0], cy + sh[1]), lays


def sc_tank(t, f):
    tb = word_t("l01", "burst")
    img = plate("burst" if t >= tb else "tank")
    fl = math.exp(-(t - tb) / 0.12) if t >= tb else 0.0
    if fl > 0:
        img[..., :3] = np.clip(img[..., :3] + fl * 0.8, 0, 1)
    lays = [E.title_layer(t, [("JANUARY 1919", 100, 300, E.WHITE, word_t("l01", "january")), ("BOSTON HARBOR", 70, 400, E.GOLD, word_t("l01", "harbor"))]),
            E.stamp_layer(t, "BURST!", tb, 540, 700, 150)]
    z, cx, cy = push("tank", 1.0, 1.1, (540, 960), (520, 940))(t)
    if t >= tb:
        a = 22 * math.exp(-(t - tb) / 0.35)
        cx, cy = cx + a * noise1(t, 3, 14), cy + a * noise1(t, 4, 14)
    return img, (z, cx, cy), lays


def sc_gallons(t, f):
    img = plate("wave")
    to = word_t("l02", "once")
    pose = dict(eyes="wide", brows="up", mouth="O", amt=1.2 if t < to else 1.6, look=(-0.4, -0.4), hands=[(-10, -130), (10, -130)],
                tilt=-6, squash=0.06 * math.exp(-max(0, t - to) / 0.2) if t > to else 0)
    img = char(img, EDDIE, 560, 2050, 2.1, pose, t)
    img = layer_over(img, lambda c: snowfall(c, t, 50, 5))
    lays = [E.title_layer(t, [("2.3 MILLION", 120, 300, E.GOLD, word_t("l02", "two", "2", "23")), ("GALLONS", 140, 450, E.WHITE, word_t("l02", "gallons"))]),
            E.stamp_layer(t, "ALL AT ONCE", to, 540, 640, 110)]
    return img, push("gallons", 1.0, 1.12, (540, 900), (560, 980))(t), lays


PLANKS = [(random.Random(k).uniform(-500, 500), random.Random(k + 50).uniform(-900, -500), random.Random(k + 90).uniform(-400, 400)) for k in range(9)]


def sc_flatten(t, f):
    img = plate("flood")
    tf = word_t("l03", "flattens")
    surf_y = META["flood"]["surface_y_far"]

    def debris(c):
        if t < tf:
            return
        u = t - tf
        for k, (vx, vy, w) in enumerate(PLANKS):
            x = 760 + vx * u * 0.6
            y = 880 + vy * u + 0.5 * G_PX * u * u
            land = y >= surf_y + 40
            y = min(y, surf_y + 40)                  # lands on the molasses and floats there
            c.save(); c.translate(x, y); c.rotate(k * 40 + (0 if land else w * u))
            c.drawRect(skia.Rect(-46, -8, 46, 8), P(C(120, 80, 45))); c.drawRect(skia.Rect(-46, -8, 46, 8), S(INK, 4))
            c.restore()
        PHYS["planks_land_y"] = surf_y + 40
    img = layer_over(img, lambda c: (debris(c), snowfall(c, t, 40, 7)))
    lays = [E.stamp_layer(t, "FLATTENED", tf, 540, 520, 130),
            E.title_layer(t, [("FREEZING COLD", 90, 330, E.WHITE, word_t("l03", "freezing"))])]
    z, cx, cy = push("flatten", 1.0, 1.08, (540, 960), (560, 940))(t)
    if tf <= t < tf + 0.6:
        a = (1 - (t - tf) / 0.6) * 11          # a damped rumble (14 Hz), not a per-frame jump
        cx, cy = cx + a * noise1(t, 5, 14), cy + a * noise1(t, 6, 14)
    return img, (z, cx, cy), lays


def sc_stuck(t, f):
    img = plate("flood")
    ts = word_t("l04", "stuck")
    x, y, s_ = 560, 1900, 1.6
    pose = dict(eyes="squint" if t < ts else "wide", brows="angry" if t < ts else "up", mouth="disgust" if t < ts else "O", amt=1.3,
                hands=[(-80, -40), (80, -40)] if t < ts else [(-30, -150), (30, -150)], lean=4 * math.sin(t * 5), tilt=6 * math.sin(t * 3.3))
    img = char(img, EDDIE, x, y, s_, pose, t, shadow=0.0)
    y_surf = y - 330 * s_ / 1.6 * 1.0
    col = plate_col("flood", 540, META["flood"]["surface_y_near"] + 120)
    img = layer_over(img, lambda c: molasses_band(c, x, y_surf, 760, col, t))
    lays = [E.title_layer(t, [("THICK AS GLUE", 100, 330, E.GOLD, word_t("l04", "glue"))]), E.stamp_layer(t, "STUCK!", ts, 540, 560, 150)]
    return img, push("stuck", 1.05, 1.18, (560, 1050), (560, 1120))(t), lays


def sc_dead(t, f):
    img = plate("flood")
    pose = dict(eyes="sad", brows="sad", mouth="frown", hands=[(-15, 140), (15, 140)], tilt=8)
    img = char(img, EDDIE, 330, 1700, 0.95, pose, t, shadow=0.0)
    col = plate_col("flood", 330, 1500)
    img = layer_over(img, lambda c: (molasses_band(c, 330, 1700 - 190, 700, col, t), snowfall(c, t, 50, 9)))
    lays = [E.title_layer(t, [("21 DEAD", 160, 360, E.WHITE, word_t("l05", "21", "twentyone", "twenty")),
                              ("150 HURT", 110, 520, E.GOLD, word_t("l05", "150", "hundred", "fifty"))])]
    return img, push("dead", 1.0, 1.1, (540, 980), (500, 960))(t), lays


def sc_harbor(t, f):
    img = plate("harbor")
    img = layer_over(img, lambda c: snowfall(c, t, 50, 11))
    lays = [E.title_layer(t, [("THE HARBOR", 100, 330, E.WHITE, word_t("l06", "harbor")), ("STAYED BROWN", 120, 480, E.GOLD, word_t("l06", "brown"))])]
    return img, push("harbor", 1.2, 1.32, (540, 780), (520, 760))(t), lays   # crop out the pale quay at the bottom


def sc_crazy(t, f):
    img = plate("tank", blur=8 * K)
    tc = word_t("l07", "crazy")
    pose = dict(eyes="open" if t < tc else "wide", brows="up", mouth="smile" if t < tc else "grin", look=(0.3, -0.2),
                hands=[(-20, 120), (110, -120)], tilt=-8, squash=0.05 * math.exp(-max(0, t - tc) / 0.2) if t > tc else 0)
    img = char(img, EDDIE, 540, 2080, 2.2, pose, t, shadow=0.0)
    lays = [E.title_layer(t, [("THE CRAZY PART", 110, 380, E.GOLD, tc)])]
    return img, push("crazy", 1.0, 1.1, (540, 960), (540, 1010))(t), lays


def sc_leak(t, f):
    img = plate("tankclose")
    x, y, s_ = 330, 1880, 1.2
    pose = dict(eyes="squint", brows="up", mouth="grin", look=(0.5, -0.6), hands=[(-20, 120), (60, -40)], tilt=-6)
    img = char(img, EDDIE, x, y, s_, pose, t)
    hx, hy = T.hand_pos(x, y, s_, pose, 1)
    img = layer_over(img, lambda c: (drips(c, t, hx, 900, hy - 20 * s_, seed=2), can(c, hx, hy - 30, s_ * 0.9)))
    lays = [E.title_layer(t, [("IT LEAKED", 120, 330, E.WHITE, word_t("l08", "leaked")), ("FROM DAY ONE", 100, 470, E.GOLD, word_t("l08", "day"))])]
    return img, push("leak", 1.0, 1.1, (540, 960), (480, 1000))(t), lays


def sc_paint(t, f):
    a, b = span("paint")
    k = smooth((t - a) / (b - a))
    img = plate("tankclose") * (1 - k) + plate("tankbrown") * k
    x, y, s_ = 420, 1900, 1.25
    sw = math.sin(t * 9)
    pose = dict(eyes="squint", brows="smug", mouth="smile", look=(0.6, -0.4), hands=[(-20, 120), (90 + 20 * sw, -110 - 30 * sw)], tilt=-4)
    img = char(img, BOSS, x, y, s_, pose, t)
    hx, hy = T.hand_pos(x, y, s_, pose, 1)
    img = layer_over(img, lambda c: brush(c, hx, hy, s_ * 0.8, 20 + 25 * sw))
    lays = [E.title_layer(t, [("THE COMPANY'S FIX?", 92, 330, E.WHITE, word_t("l09", "fix", "company"))]),
            E.stamp_layer(t, "PAINT IT BROWN", word_t("l09", "brown"), 540, 520, 100, (150, 75, 25), -5)]
    return img, push("paint", 1.0, 1.08, (540, 960), (500, 980))(t), lays


def sc_wink(t, f):
    img = plate("tankbrown", blur=6 * K)
    pose = dict(eyes="wink", brows="smug", mouth="grin", look=(0.2, 0), hands=[(-20, 120), (60, -150)], tilt=6)
    img = char(img, BOSS, 540, 2100, 2.1, pose, t, shadow=0.0)
    lays = [E.title_layer(t, [("SO NOBODY COULD", 86, 330, E.WHITE, word_t("l09", "nobody")), ("SEE THE LEAKS", 120, 470, E.GOLD, word_t("l09", "leaks"))])]
    return img, push("wink", 1.0, 1.08, (540, 980), (540, 1020))(t), lays


def sc_tested(t, f):
    img = plate("tankbrown")
    pose = dict(eyes="open", brows="sad", mouth="frown", look=(0.6, -0.6), hands=[(-120, -20), (120, -20)], tilt=-10)
    img = char(img, EDDIE, 330, 1880, 1.15, pose, t)
    lays = [E.stamp_layer(t, "NEVER TESTED", word_t("l10", "tested"), 540, 520, 120)]
    return img, push("tested", 1.0, 1.1, (540, 960), (520, 900))(t), lays


def sc_blame(t, f):
    img = plate("flood")
    x, y, s_ = 560, 1880, 1.45
    pose = dict(eyes="wide", brows="angry", mouth="O", amt=0.9, look=(-0.3, 0), hands=[(-90, -60), (70, -60)], lean=-3, tilt=4 * math.sin(t * 6))
    img = char(img, BOSS, x, y, s_, pose, t, shadow=0.0)
    hx, hy = T.hand_pos(x, y, s_, pose, 1)
    col = plate_col("flood", 560, 1650)
    img = layer_over(img, lambda c: (molasses_band(c, x, y - 120, 760, col, t), paper(c, hx + 30, hy + 40, 1.0, -6)))
    lays = [E.title_layer(t, [("THEY BLAMED", 100, 330, E.WHITE, word_t("l11", "blamed"))]),
            E.stamp_layer(t, "ANARCHISTS", word_t("l11", "anarchists"), 540, 500, 120)]
    return img, push("blame", 1.0, 1.08, (540, 980), (560, 1000))(t), lays


def sc_court(t, f):
    img = plate("court")
    tb = word_t("l12", "buy")
    g = 0.0 if t < tb - 0.25 else (1 - math.exp(-(t - tb + 0.25) * 12)) if t < tb else math.exp(-(t - tb) * 3)
    x, y, s_ = 540, 1760, 1.3
    pose = dict(eyes="squint", brows="angry", mouth="frown", hands=[(-20, 120), (70, -150 + 110 * g)], tilt=-3)
    img = char(img, JUDGE, x, y, s_, pose, t)
    hx, hy = T.hand_pos(x, y, s_, pose, 1)
    img = layer_over(img, lambda c: gavel(c, hx, hy, s_ * 0.9, -40 + 70 * g))
    lays = [E.title_layer(t, [("THE COURT", 110, 330, E.WHITE, word_t("l12", "court"))]), E.stamp_layer(t, "DIDN'T BUY IT", tb, 540, 520, 110)]
    z, cx, cy = push("court", 1.0, 1.1, (540, 960), (540, 1000))(t)
    if tb <= t < tb + 0.3:
        cy += 8 * (1 - (t - tb) / 0.3) * noise1(t, 8, 14)
    return img, (z, cx, cy), lays


def sc_verdict(t, f):
    img = plate("court")
    img = char(img, JUDGE, 360, 1760, 1.15, dict(eyes="open", brows="angry", mouth="O", amt=0.6, hands=[(-20, 120), (90, -110)], look=(0.8, 0)), t)
    img = char(img, BOSS, 760, 1800, 1.2, dict(eyes="wide", brows="sad", mouth="O", amt=0.9, hands=[(-30, -60), (30, -60)], look=(-0.8, 0), tilt=5), t)
    lays = [E.stamp_layer(t, "RESPONSIBLE", word_t("l13", "responsible"), 540, 520, 120)]
    return img, push("verdict", 1.0, 1.06, (540, 980), (560, 1000))(t), lays


def sc_paid(t, f):
    img = plate("court", blur=6 * K)
    x, y, s_ = 540, 2080, 2.0
    pose = dict(eyes="squint", brows="sad", mouth="frown", hands=[(-20, 120), (90, -40)], tilt=-5)
    img = char(img, BOSS, x, y, s_, pose, t, shadow=0.0)
    hx, hy = T.hand_pos(x, y, s_, pose, 1)
    img = layer_over(img, lambda c: moneybag(c, hx + 20, hy + 20, 1.1))
    lays = [E.title_layer(t, [("PAID OVER", 100, 330, E.WHITE, word_t("l13", "paid")), ("$600,000", 150, 490, E.GOLD, word_t("l13", "600", "600000", "six", "hundred"))])]
    return img, push("paid", 1.0, 1.08, (540, 1000), (540, 1040))(t), lays


def sc_engineers(t, f):
    img = plate("summer")
    tsg = word_t("l14", "sign")
    x, y, s_ = 360, 1840, 1.35
    pose = dict(eyes="open" if t < tsg else "squint", brows="flat" if t < tsg else "up", mouth="smile" if t < tsg else "grin",
                hands=[(-20, 120), (120, -10)], tilt=-4)
    img = char(img, EDDIE, x, y, s_, pose, t)
    st = clamp((t - tsg) / (5 / FPS)) if t >= tsg else 0.0
    hx, hy = T.hand_pos(x, y, s_, pose, 1)
    img = layer_over(img, lambda c: blueprint(c, hx + 150, hy + 80, 0.95, st))
    lays = [E.title_layer(t, [("NEW RULE:", 100, 330, E.WHITE, word_t("l14", "boston", "after")), ("ENGINEERS SIGN", 104, 470, E.GOLD, tsg)])]
    return img, push("engineers", 1.0, 1.1, (540, 960), (500, 1000))(t), lays


def sc_smell(t, f):
    img = plate("summer")
    x, y, s_ = 560, 1900, 1.6
    pose = dict(eyes="closed", brows="up", mouth="grin", hands=[(-90, 40), (90, 40)], tilt=-8 + 4 * math.sin(t * 1.5))
    img = char(img, EDDIE, x, y, s_, pose, t)
    img = layer_over(img, lambda c: smell(c, x + 120, y - 600 * s_ / 1.6, t))
    lays = [E.title_layer(t, [("SMELLED SWEET", 110, 330, E.GOLD, word_t("l15", "sweet")), ("FOR DECADES", 100, 470, E.WHITE, word_t("l15", "decades"))])]
    return img, push("smell", 1.0, 1.12, (540, 960), (560, 1020))(t), lays


def sc_leaky(t, f):
    img = plate("tank")
    lays = [E.title_layer(t, [("ALL FROM", 100, 330, E.WHITE, word_t("l16", "all")), ("ONE LEAKY TANK", 112, 480, E.GOLD, word_t("l16", "leaky"))])]
    return img, push("leaky", 1.0, 1.14, (540, 960), (540, 900))(t), lays


def sc_cta(t, f):
    from cta2 import draw_cta2
    img = plate("summer", blur=10 * K)
    img[..., :3] *= 0.6
    t0 = TIMES["cta"] - 0.12
    s, c = E.surf(world=False)
    draw_cta2(c, t - t0, word_t("cta", "like") - t0, word_t("cta", "subscribe") - t0)
    return img, (1.08, 540, 1000), [E.arr(s)]


RENDER = {n: globals()["sc_" + n] for n, _ in SCENES}
NO_SPLAT = {"cta", "wink", "paid"}     # close-ups that cut straight in on the word; the CTA fades


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


def render(f, out=None):
    t = f / FPS
    name = SCENES[scene_at(t)][0]
    img, (z, cx, cy), lays = RENDER[name](t, f)
    shake = (0, 0)
    for at in (word_t("l01", "burst"), word_t("l04", "stuck"), word_t("l12", "buy"), word_t("l10", "tested")):
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
    E.save(rgb, out or os.path.join(OUT_FR, f"{f + 1:04d}.png"))
    return f


def physics_report():
    if not os.path.exists(os.path.join(PL_DIR, "plate_tankclose.png")):
        return dict(partial=True)
    sc_leak(span("leak")[0] + 0.5, 0)
    sc_flatten(word_t("l03", "flattens") + 3.0, 0)
    return dict(drip_fall_s=PHYS["drip_fall_s"], planks_land_y=PHYS["planks_land_y"], g_px=G_PX, scenes=[(n, round(a, 3)) for n, a in SCENES], dur=DUR)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "frames"
    rep = physics_report()
    json.dump(rep, open(os.path.join(D, "physics.json"), "w"), indent=1)
    print("duration", DUR, "s,", NF, "frames")
    if mode == "stills":
        os.makedirs(os.path.join(D, "stills"), exist_ok=True)
        for ts in sys.argv[2].split(","):
            fr = int(round(float(ts) * FPS))
            render(fr, os.path.join(D, "stills", f"s_{float(ts):05.2f}.png"))
            print("still", ts, SCENES[scene_at(fr / FPS)][0], flush=True)
    else:
        os.makedirs(OUT_FR, exist_ok=True)
        todo = [fr for fr in range(NF) if os.environ.get("SKIP") != "1" or not os.path.exists(os.path.join(OUT_FR, f"{fr + 1:04d}.png"))]
        with Pool(int(os.environ.get("PROCS", "4"))) as pool:
            for j, _ in enumerate(pool.imap_unordered(render, todo, chunksize=4)):
                if j % 150 == 0:
                    print("frame", j, "/", len(todo), flush=True)
        print("done")
