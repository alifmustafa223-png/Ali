"""YouTube Short: "This Man Is Buried Inside a Chip Can" - Fred Baur (1918-2008), the chemist who designed the stackable
chip can (patent 1970). Canary look: the channel's toons in lit 3D Blender sets (blender/pringles_plates.py), the hook is a
REAL 3D camera orbit (plates/orbit/%04d.png + track.json), title slams, stamps, gold splats, CTA v2. Voice: vidIQ "Chris".

Facts: Baur, a Ph.D. organic chemist and former Navy aviation physiologist at Procter & Gamble, devised the uniform
stacking method and the tubular can (patent 1970). He died 4 May 2008, aged 89; at his request part of his ashes were
buried in one of the cans at Arlington Memorial Gardens near Cincinnati, Ohio (Wikipedia, AP/NBC, TIME, CBS).
Generic red can (no brand logo); generic cartoon people (no likenesses).

  python make_pringles.py stills 1.0,5.2  |  python make_pringles.py frames (PROCS=4)
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
from style2d_engine import C, P, S, W, H, K, FPS, lerp, clamp, ramp, snap, smooth, noise1

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "pringles")
PL_DIR = os.path.join(D, "plates")
TIMES = json.load(open(os.path.join(D, "vo_final.wav.times.json")))
WORDS = json.load(open(os.path.join(D, "vo_final.wav.words.json")))
LINES = json.load(open(os.path.join(D, "lines_final.json")))
ORDER = [l["key"] for l in LINES]
DUR = round(min(64.6, max(61.5, TIMES["cta"] + 3.9)), 3)
NF = int(round(DUR * FPS))
OUT_FR = os.path.join(D, "frames")
G_PX = 3600.0
PHYS = {}
INK = C(30, 18, 14)


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


SCENES = [("hook", 0.0), ("fred", _cut("fred")), ("bags", _cut("bags")), ("plan", _cut("plan")), ("tube", _cut("tube")),
          ("patent", _cut("patent")), ("twist", _cut("twist")), ("died", _cut("died")), ("ashes", _cut("ashes")), ("end", _cut("end")),
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


FRED = dict(skin=(238, 198, 166), hair="neat", hair_col=(95, 65, 42), coat=(222, 214, 198), pants=(55, 55, 62), nose="long", glasses=True)
FRED_OLD = dict(skin=(236, 196, 168), hair="grey", hair_col=(215, 215, 220), coat=(150, 112, 78), pants=(70, 66, 70), nose="long", glasses=True)
DAUGHTER = dict(skin=(232, 190, 160), hair="curly", hair_col=(110, 70, 40), coat=(70, 110, 85), pants=(60, 60, 70), nose="small")
SON = dict(skin=(226, 186, 150), hair="neat", hair_col=(60, 45, 35), coat=(60, 70, 110), pants=(50, 50, 60), nose="small")

_PL = {}


def plate(name, blur=0.0):
    key = (name, blur)
    if key not in _PL:
        im = Image.open(os.path.join(PL_DIR, f"plate_{name}.png") if not name.startswith("orbit/") else os.path.join(PL_DIR, name)).convert("RGB")
        a = np.asarray(im.resize((E.WW, E.WH), Image.LANCZOS)).astype(np.float32) / 255.0
        a = np.dstack([a, np.ones(a.shape[:2], np.float32)])
        if blur:
            a = E.gblur(a, blur)
        if not name.startswith("orbit/"):
            _PL[key] = a
        return a.copy()
    return _PL[key].copy()


ORBIT = json.load(open(os.path.join(PL_DIR, "orbit", "track.json"))) if os.path.exists(os.path.join(PL_DIR, "orbit", "track.json")) else []
META = {n: json.load(open(os.path.join(PL_DIR, f"plate_{n}.json"))) for n in ("grave", "store", "factory", "home")
        if os.path.exists(os.path.join(PL_DIR, f"plate_{n}.json"))}


def char(img, look, x, y, s_, pose, t, shadow=0.5, rim=0.55, rim_col=(1.0, 0.85, 0.7), extra=None, blur=0, ghost=0.0):
    ch = E.draw_person(look, x, y, s_, pose, t, extra)
    if ghost:      # a friendly ghost: pale, blue-rimmed, see-through, softly glowing
        a = ch[..., 3:4]
        ch[..., :3] = ch[..., :3] * 0.55 + np.array([0.75, 0.85, 1.0], np.float32) * 0.45
        glow = E.gblur(ch, 14 * K)
        ch[..., 3:4] = a * ghost
        img = E.over(img, np.dstack([glow[..., :3] * 0 + np.array([0.7, 0.85, 1.0], np.float32), glow[..., 3:4] * 0.45]))
        return E.over(img, ch)
    if blur:
        return E.over(img, E.gblur(ch, blur))
    return E.light_char(ch, img, y, shadow=shadow, rim=rim, rim_col=rim_col)


def dust(c, t, n, seed, col=(255, 220, 160), y0=200, y1=1750):
    """Floating lamp-lit dust motes (the canary look)."""
    r = random.Random(seed)
    for k in range(n):
        x0, yy, sp, ph = r.uniform(0, W), r.uniform(y0, y1), r.uniform(8, 25), r.uniform(0, 6.28)
        x = (x0 + sp * t + 20 * math.sin(t * 0.7 + ph)) % W
        y = yy - 10 * t + 15 * math.sin(t * 0.5 + ph * 2)
        a = int(110 + 90 * math.sin(t * 2 + ph))
        c.drawCircle(x, y, r.uniform(1.2, 3.2), P(C(*col, max(0, a))))


def layer_over(img, draw):
    s, c = E.surf()
    draw(c)
    return E.over(img, E.arr(s))


def push(name, z0, z1, c0, c1):
    a, b = span(name)

    def f(t):
        k = smooth((t - a) / (b - a))
        return lerp(z0, z1, k), lerp(c0[0], c1[0], k), lerp(c0[1], c1[1], k)
    return f


# =================================================================================== props
def can2d(c, x, y, s, open_top=False):
    """The generic red chip can, standing with its base at (x, y)."""
    c.save(); c.translate(x, y); c.scale(s, s)
    body = skia.Rect(-38, -250, 38, 0)
    c.drawRect(body, P(Shader=T.lin((-38, 0), (38, 0), [C(150, 15, 22), C(225, 40, 45), C(140, 12, 20)])))
    c.drawRect(skia.Rect(-38, -250, 38, -232), P(C(240, 236, 228))); c.drawRect(skia.Rect(-38, -18, 38, 0), P(C(240, 236, 228)))
    c.drawCircle(0, -140, 22, P(C(250, 205, 60)))
    c.drawRect(body, S(INK, 6))
    c.drawOval(skia.Rect(-40, -262, 40, -238), P(C(200, 205, 210) if not open_top else C(40, 20, 12)))
    c.drawOval(skia.Rect(-40, -262, 40, -238), S(INK, 5))
    c.restore()


def chip(c, x, y, s, ang=0.0, top=True):
    """A saddle-shaped chip seen almost edge-on: a curved golden wafer."""
    c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s)
    p = skia.Path()
    p.moveTo(-46, 4); p.cubicTo(-20, -12, 20, -12, 46, 4); p.cubicTo(20, 12, -20, 12, -46, 4); p.close()
    c.drawPath(p, P(Shader=T.lin((0, -12), (0, 12), [C(255, 225, 120), C(225, 165, 55)])))
    c.drawPath(p, S(C(120, 70, 20), 3.5))
    c.restore()


BAG_X, BAG_Y = 674.0, 1316.0       # held in Fred's right hand (T.hand_pos -> 594, 1316)
CRUMB_Y0, CRUMB_FLOOR = 1444.0, 1700.0   # crumbs leave the squeezed bag here and land on the shop floor at Fred's feet
PLAN_STACK = dict(n=16, base_y=935.0, drop_h=420.0, every=0.33)
PLAN_X = 700.0
TUBE_STACK = dict(n=10, drop_h=420.0, every=0.28)
CHIP_T = 13.0          # px: one chip's thickness in the stack


def stack_state(t, t0, n, base_y, drop_h=520.0, every=0.32):
    """Chip k is dropped at t0 + k*every from base_y - drop_h and falls under gravity until it lands EXACTLY on the
    stack top (base_y - k*CHIP_T). Returns [(y, landed)] for the chips already released."""
    out = []
    for k in range(n):
        tk = t - (t0 + k * every)
        if tk < 0:
            break
        rest = base_y - k * CHIP_T
        y = rest - drop_h + 0.5 * G_PX * tk * tk
        out.append((min(y, rest), y >= rest))
    PHYS["chip_fall_s"] = math.sqrt(2 * drop_h / G_PX)
    return out


def crumb_params(n=18, seed=3):
    r = random.Random(seed)
    return [(r.uniform(-260, 260), r.uniform(-500, -150), r.uniform(0, 0.25)) for _ in range(n)]


def crumb_land_times(t0, y0, floor_y, n=18, seed=3):
    """When each crumb hits the floor (solved, for the audio ticks and QC)."""
    return [t0 + d + (-vy + math.sqrt(vy * vy + 2 * G_PX * (floor_y - y0))) / G_PX for vx, vy, d in crumb_params(n, seed)]


def crumbs(c, t, t0, x, y0, floor_y, n=18, seed=3):
    """Broken crumbs falling out of a squeezed bag: ballistic, they land and stay ON the floor (never below)."""
    if t < t0:
        return
    for k, (vx, vy, d) in enumerate(crumb_params(n, seed)):
        u = t - t0 - d
        if u < 0:
            continue
        px = x + vx * u
        py = y0 + vy * u + 0.5 * G_PX * u * u
        landed = py >= floor_y
        py = min(py, floor_y)
        if landed:
            px = x + vx * ((-vy + math.sqrt(vy * vy + 2 * G_PX * (floor_y - y0))) / G_PX)
        chip(c, px, py, 0.5, ang=(k * 47) % 360 if not landed else 0)
    PHYS["crumb_floor"] = floor_y


def bag(c, x, y, s, puff):
    c.save(); c.translate(x, y); c.scale(s * (1 + 0.12 * puff), s * (1 + 0.05 * puff))
    p = skia.Path(); p.addRoundRect(skia.Rect(-110, -170, 110, 170), 50, 50)
    c.drawPath(p, P(Shader=T.lin((-110, 0), (110, 0), [C(200, 140, 20), C(250, 200, 60), C(190, 130, 15)])))
    c.drawPath(p, S(INK, 7))
    for yy in (-165, 165):
        c.drawRect(skia.Rect(-112, yy - 10, 112, yy + 10), P(C(170, 110, 15)))
        for k in range(-5, 6):
            c.drawLine(k * 20, yy - 10, k * 20 + 6, yy + 10, S(C(120, 75, 10), 3))
    f = skia.Font(T.FB, 46)
    c.drawString("CHIPS", -f.measureText("CHIPS") / 2, 16, f, P(C(150, 30, 20)))
    c.restore()


def parchment(c, x, y, s, rot, stamped):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    c.drawRect(skia.Rect(-200, -260, 200, 40), P(Shader=T.lin((0, -260), (0, 40), [C(245, 232, 200), C(225, 205, 160)])))
    c.drawRect(skia.Rect(-200, -260, 200, 40), S(C(120, 85, 50), 6))
    f1 = skia.Font(T.FB, 34)
    c.drawString("U.S. PATENT", -f1.measureText("U.S. PATENT") / 2, -200, f1, P(C(80, 50, 25)))
    for k in range(6):
        c.drawRect(skia.Rect(-160, -160 + k * 26, 160, -152 + k * 26), P(C(170, 150, 115)))
    can2d(c, -100, 10, 0.55)
    c.restore()


def smile_bubble(c, x, y, txt, a):
    if a <= 0:
        return
    f = skia.Font(T.FB, 54)
    w = f.measureText(txt)
    c.save(); c.translate(x, y); sc = 0.6 + 0.4 * T.out_back(min(1, a), 1.8); c.scale(sc, sc)
    r = skia.Rect(-w / 2 - 34, -70, w / 2 + 34, 30)
    c.drawRoundRect(r, 40, 40, P(C(255, 255, 255)))
    c.drawRoundRect(r, 40, 40, S(INK, 7))
    tail = skia.Path(); tail.moveTo(-20, 28); tail.lineTo(10, 28); tail.lineTo(-40, 80); tail.close()
    c.drawPath(tail, P(C(255, 255, 255)))
    c.drawString(txt, -w / 2, 0, f, P(INK))
    c.restore()


# =================================================================================== scenes
def sc_hook(t, f):
    n = len(ORBIT)
    k = min(n - 1, int(t * FPS))
    img = plate(f"orbit/{k + 1:04d}.png")
    tr = ORBIT[k]
    cx_can, cy_can = tr["can"]
    ti = word_t("hook", "idea", "own")
    ga = ramp(t, ti - 0.35, 0.4)
    if ga > 0:   # Fred's friendly ghost pops up beside his headstone, proud, on "his own idea"
        pose = dict(eyes="squint", brows="smug", mouth="grin", hands=[(-20, 120), (70, -150)], tilt=-6, look=(-0.5, 0))
        img = char(img, FRED_OLD, cx_can - 300, cy_can + 380 - 40 * math.sin(t * 2.2), 1.0, pose, t, ghost=0.82 * ga)
    lays = [E.title_layer(t, [("THIS MAN IS", 70, 190, E.WHITE, -0.3), ("BURIED INSIDE", 96, 300, E.WHITE, word_t("hook", "buried")),
                              ("A CHIP CAN", 150, 450, E.GOLD, word_t("hook", "can", "chips"))]),
            E.stamp_layer(t, "HIS IDEA!", ti, 520, 1560, 120)]
    hold = max(0.0, t - (n - 1) / FPS)          # after the orbit ends, keep pushing in on its last frame (no stop)
    return img, (1.0 + 0.05 * hold, 540, 960 + 40 * hold), lays


def sc_fred(t, f):
    img = plate("lab")
    pose = dict(eyes="open", brows="up", mouth="smile", look=(0.4, -0.2), hands=[(-20, 120), (80, -120)], tilt=-4)
    x, y, s_ = 560, 1760, 1.35

    def flask(c):
        hx, hy = T.hand_pos(x, y, s_, pose, 1)
        p = skia.Path(); p.moveTo(hx - 12, hy - 90); p.lineTo(hx - 12, hy - 50); p.lineTo(hx - 42, hy + 10)
        p.quadTo(hx, hy + 26, hx + 42, hy + 10); p.lineTo(hx + 12, hy - 50); p.lineTo(hx + 12, hy - 90); p.close()
        c.drawPath(p, P(C(150, 220, 240, 170))); c.drawPath(p, S(INK, 6))
        for k in range(3):
            ph = (t * 1.1 + k / 3) % 1.0
            c.drawCircle(hx + 8 * math.sin(k + t), hy - 100 - 90 * ph, 7 + 6 * ph, P(C(220, 240, 255, int(160 * math.sin(math.pi * ph)))))
    img = char(img, FRED, x, y, s_, pose, t, extra=flask)
    lays = [E.title_layer(t, [("FRED BAUR", 130, 330, E.GOLD, word_t("fred", "fred", "baur", "bauer"))]),
            E.stamp_layer(t, "NAVY VET", word_t("fred", "navy"), 370, 560, 90, (40, 70, 150), -8),
            E.stamp_layer(t, "PH.D.", word_t("fred", "phd", "ph", "chemistry"), 790, 600, 110, (200, 35, 45), 7)]
    return img, push("fred", 1.0, 1.1, (540, 960), (560, 1000))(t), lays


def sc_bags(t, f):
    img = plate("store")
    th = word_t("bags", "half", "air")
    tc = word_t("bags", "broken", "crumbs")
    x, y, s_ = 360, 1700, 1.3
    sq = ramp(t, tc - 0.25, 0.25)
    pose = dict(eyes="squint" if t >= tc else "open", brows="angry" if t >= tc else "up", mouth="disgust" if t >= tc else "O", amt=0.8,
                hands=[(-20, 120), (120, -60)], tilt=-4, look=(0.8, -0.2))
    img = layer_over(img, lambda c: bag(c, BAG_X, BAG_Y, 0.75, ramp(t, th - 0.2, 0.3) * (1 - 0.6 * sq)))   # behind the hand: he grips it
    img = char(img, FRED, x, y, s_, pose, t)
    img = layer_over(img, lambda c: crumbs(c, t, tc, BAG_X, CRUMB_Y0, CRUMB_FLOOR))
    lays = [E.title_layer(t, [("1960s CHIPS:", 100, 320, E.WHITE, word_t("bags", "nineteen", "1960s", "sixties"))]),
            E.stamp_layer(t, "HALF AIR", th, 540, 520, 130),
            E.title_layer(t, [("BROKEN CRUMBS", 92, 700, E.GOLD, tc)])]
    return img, push("bags", 1.0, 1.08, (540, 960), (500, 1000))(t), lays


def sc_plan(t, f):
    img = plate("factory")
    tsame = word_t("plan", "same", "shape")
    tstack = word_t("plan", "stack")
    base_x, base_y = PLAN_X, PLAN_STACK["base_y"]
    x, y, s_ = 330, 1800, 1.35
    cheering = t > tstack + 1.2
    pose = dict(eyes="squint" if cheering else "open", brows="up", mouth="grin" if cheering else "smile", look=(0.8, -0.3),
                hands=[(-30, -150), (30, -150)] if cheering else [(-20, 120), (110, -60)], tilt=-5)
    img = char(img, FRED, x, y, s_, pose, t)

    def draw(c):
        if t >= tsame - 0.2:
            for k, (yy, landed) in enumerate(stack_state(t, tsame, PLAN_STACK["n"], base_y, PLAN_STACK["drop_h"], PLAN_STACK["every"])):
                chip(c, base_x, yy, 1.4)
    img = layer_over(img, draw)
    if t < tsame - 0.1:     # "Fred had a strange plan": no empty seconds before the next title
        return img, push("plan", 1.0, 1.08, (560, 960), (600, 1000))(t), [E.title_layer(t, [("A STRANGE PLAN", 104, 320, E.GOLD, word_t("plan", "strange"))])]
    lays = [E.title_layer(t, [("THE SAME SHAPE", 100, 320, E.GOLD, tsame)]),
            E.stamp_layer(t, "STACKABLE!", tstack, 540, 500, 120),
            E.title_layer(t, [("LIKE ROOF TILES", 80, 1330, E.WHITE, word_t("plan", "roof", "tiles"))])]
    return img, push("plan", 1.0, 1.08, (560, 960), (600, 1000))(t), lays


def sc_tube(t, f):
    img = plate("lab", blur=7 * K)
    tna = word_t("tube", "air")
    x, y, s_ = 420, 2000, 1.8
    pose = dict(eyes="squint", brows="up", mouth="grin", hands=[(-20, 120), (120, -120)], tilt=-6)
    img = char(img, FRED, x, y, s_, pose, t, shadow=0)
    hx, hy = T.hand_pos(x, y, s_, pose, 1)

    def draw(c):
        cx_, cy_ = hx + 90, hy + 200
        for k, (yy, landed) in enumerate(stack_state(t, span("tube")[0] + 0.4, TUBE_STACK["n"], cy_ - 30, TUBE_STACK["drop_h"], TUBE_STACK["every"])):
            if not landed:
                chip(c, cx_, yy, 0.8)
        can2d(c, cx_, cy_, 1.2, open_top=True)
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("A TALL TUBE", 110, 320, E.GOLD, word_t("tube", "tube", "tall"))]),
            E.stamp_layer(t, "NO AIR", tna, 300, 560, 120, (40, 140, 70), -8),
            E.stamp_layer(t, "NO CRUMBS", word_t("tube", "crushed"), 760, 700, 100, (40, 140, 70), 6)]
    return img, push("tube", 1.0, 1.08, (540, 980), (560, 1020))(t), lays


def sc_patent(t, f):
    img = plate("lab")
    tp = word_t("patent", "patent")
    tf = word_t("patent", "famous")
    x, y, s_ = 330, 1780, 1.3
    pose = dict(eyes="squint" if t > tp else "open", brows="up", mouth="grin", hands=[(-20, 120), (100, -80)], tilt=-4)
    img = char(img, FRED, x, y, s_, pose, t)
    sl = snap(t, span("patent")[0] + 0.2, 9)

    def draw(c):
        parchment(c, lerp(1400, 770, sl), 1500, 1.0, lerp(20, -5, sl), t > tp)
        if t > tf:     # the can goes global: cans pop up across the lower frame
            r = random.Random(5)
            for k in range(9):
                tk = tf + k * 0.12
                if t > tk:
                    a = T.out_back(min(1, (t - tk) / 0.25), 1.6)
                    can2d(c, 120 + k * 110 + r.uniform(-20, 20), 1910, 0.55 * a)
    img = layer_over(img, draw)
    lays = [E.stamp_layer(t, "PATENT 1970", tp, 600, 560, 120),
            E.title_layer(t, [("FAMOUS WORLDWIDE", 90, 330, E.GOLD, tf)])]
    return img, push("patent", 1.0, 1.06, (540, 960), (560, 990))(t), lays


def sc_twist(t, f):
    img = plate("home")
    tp = word_t("twist", "put")
    img = char(img, FRED_OLD, 420, 1760, 1.2, dict(eyes="squint", brows="up", mouth="grin" if t < tp else "talk", talk=0.5 + 0.5 * math.sin(t * 20),
                                                   hands=[(-20, 120), (90, -100)], tilt=-4), t)
    shock = t > tp + 0.1
    img = char(img, DAUGHTER, 760, 1800, 1.1, dict(eyes="wide" if shock else "open", brows="up", mouth="O" if shock else "smile", look=(-0.8, 0),
                                                    hands=[(-30, -60), (30, -60)] if shock else [(-20, 120), (20, 120)]), t)
    img = char(img, SON, 930, 1830, 1.15, dict(eyes="wide" if shock else "open", brows="up" if shock else "flat", mouth="O" if shock else "smile",
                                               look=(-0.9, 0), hands=[(-20, 120), (20, 120)], tilt=6 if shock else 0), t)
    img = layer_over(img, lambda c: smile_bubble(c, 420, 980, "PUT ME IN IT!", (t - tp) / 0.25))
    lays = [E.title_layer(t, [("THE TWIST", 140, 330, E.GOLD, word_t("twist", "twist"))]),
            E.title_layer(t, [("SO PROUD...", 90, 470, E.WHITE, word_t("twist", "proud"))])]
    return img, push("twist", 1.0, 1.06, (560, 960), (600, 980))(t), lays


def sc_died(t, f):
    img = plate("home")
    img[..., :3] *= 0.85          # the lamp is the only light now
    tk = word_t("died", "kept", "promise")
    g = E.glow_map(890, 1420, 220, 220)
    img[..., :3] = np.clip(img[..., :3] + g[..., None] * 0.25 * np.array([1.0, 0.75, 0.4], np.float32), 0, 1)
    img = layer_over(img, lambda c: can2d(c, 890, 1500, 0.9))
    if t > tk - 0.3:
        img = char(img, DAUGHTER, 420, 1820, 1.15, dict(eyes="sad", brows="sad", mouth="smile", hands=[(-20, 120), (60, -40)], look=(0.8, 0)), t)
        img = char(img, SON, 640, 1840, 1.2, dict(eyes="sad", brows="sad", mouth="smile", hands=[(-20, 120), (20, 120)], look=(0.8, 0), tilt=5), t)
    lays = [E.title_layer(t, [("2008", 150, 330, E.WHITE, word_t("died", "2008", "two", "thousand")), ("AGE 89", 110, 480, E.GOLD, word_t("died", "89", "eightynine", "eighty"))]),
            E.stamp_layer(t, "PROMISE KEPT", tk, 540, 680, 110, (40, 140, 70), -6)]
    return img, push("died", 1.0, 1.08, (540, 960), (620, 1000))(t), lays


def sc_ashes(t, f):
    img = plate("grave")
    gy = META["grave"]["slab_front_y"] if "grave" in META else 1740
    img = char(img, DAUGHTER, 200, 1900, 1.05, dict(eyes="sad", brows="sad", mouth="smile", hands=[(-20, 120), (70, -30)], look=(0.8, -0.3)), t)
    img = char(img, SON, 900, 1910, 1.1, dict(eyes="sad", brows="sad", mouth="smile", hands=[(-20, 120), (20, 120)], look=(-0.8, -0.3)), t)
    lays = [E.title_layer(t, [("HIS ASHES", 110, 320, E.WHITE, word_t("ashes", "ashes")), ("IN A CHIP CAN", 120, 470, E.GOLD, word_t("ashes", "can", "chip"))]),
            E.stamp_layer(t, "OHIO", word_t("ashes", "ohio"), 540, 660, 130)]
    return img, push("ashes", 1.0, 1.1, (540, 960), (540, 1040))(t), lays


def sc_end(t, f):
    img = plate("grave")
    c0 = META["grave"]["can"] if "grave" in META else (524, 1173)
    ga = ramp(t, span("end")[0] + 0.6, 0.5)
    if ga > 0:
        pose = dict(eyes="squint", brows="up", mouth="grin", hands=[(-20, 120), (60, -160)], tilt=6, wave=True)
        img = char(img, FRED_OLD, c0[0] + 270, c0[1] + 380 - 40 * math.sin(t * 2.2), 0.95, pose, t, ghost=0.82 * ga)
    lays = [E.title_layer(t, [("STILL INSIDE", 120, 320, E.WHITE, word_t("end", "still")), ("HIS OWN CAN", 130, 470, E.GOLD, word_t("end", "inside", "one"))])]
    return img, push("end", 1.0, 1.28, (540, 1000), (c0[0], c0[1] + 120))(t), lays


def sc_cta(t, f):
    from cta2 import draw_cta2
    img = plate("grave", blur=10 * K)
    img[..., :3] *= 0.6
    t0 = span("cta")[0]
    s, c = E.surf(world=False)
    draw_cta2(c, max(0.0, t - t0), word_t("cta", "like") - t0, word_t("cta", "subscribe") - t0)
    return img, (1.08, 540, 1000), [E.arr(s)]


RENDER = {n: globals()["sc_" + n] for n, _ in SCENES}
NO_SPLAT = {"cta", "tube", "end"}


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
    if name != "cta":
        img = layer_over(img, lambda c: dust(c, t + 7 * scene_at(t), 45, scene_at(t) + 1,
                                             (200, 215, 255) if name in ("hook", "ashes", "end") else (255, 220, 160)))
    shake = (0, 0)
    for at in (word_t("bags", "half", "air"), word_t("twist", "put"), word_t("ashes", "ohio")):
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
    st = stack_state(10.0, 0.0, 22, 1500)
    assert all(landed for _, landed in st) and all(abs(y - (1500 - k * CHIP_T)) < 1e-9 for k, (y, _) in enumerate(st)), "chips must rest exactly on the stack"
    return dict(chip_fall_s=PHYS["chip_fall_s"], chip_t=CHIP_T, g_px=G_PX, scenes=[(n, round(a, 3)) for n, a in SCENES], dur=DUR)


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
