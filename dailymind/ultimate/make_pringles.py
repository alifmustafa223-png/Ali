"""YouTube Short: "This Man Is Buried Inside a Chip Can" - Fred Baur (1918-2008), the chemist who designed the stackable
chip can (patent 1970). APPROVED 2D style of the fortune-cookie Short (make_fortune.py): every set is drawn in Skia,
big close-up toons behind counters/benches, props in front, title slams + stamps on their words, gold splats, CTA v2.
(The canary-look v1-v3 with Blender plates was rejected by the owner: "make it like fortune cookies style".)
Voice: vidIQ "Chris".

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
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
import skia
from PIL import Image

import style2d_engine as E
import toon as T
from style2d_engine import C, P, S, W, H, K, FPS, path, lerp, clamp, ramp, snap, smooth, noise1

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "pringles")
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


FRED = dict(skin=(238, 198, 166), hair="neat", hair_col=(95, 65, 42), coat=(245, 245, 240), pants=(55, 55, 62), nose="long", glasses=True)
FRED_OLD = dict(skin=(236, 196, 168), hair="grey", hair_col=(215, 215, 220), coat=(150, 112, 78), pants=(70, 66, 70), nose="long", glasses=True)
DAUGHTER = dict(skin=(232, 190, 160), hair="curly", hair_col=(110, 70, 40), coat=(70, 110, 85), pants=(60, 60, 70), nose="small")
SON = dict(skin=(226, 186, 150), hair="neat", hair_col=(60, 45, 35), coat=(60, 70, 110), pants=(50, 50, 60), nose="small")


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



# ----------------------------------------------------------------------------- 2D-set geometry (physics surfaces)
COUNTER_Y = 1500.0       # top edge of every counter / bench / table front (fortune-style framing)
BAGS_POSE_HANDS = [(-20, 130), (150, -140)]
FRED_BAGS = (330.0, 1760.0, 2.0)
_hx, _hy = T.hand_pos(*FRED_BAGS, dict(hands=BAGS_POSE_HANDS, tilt=-3), 1)
BAG_X, BAG_Y = _hx + 95.0, _hy + 10.0          # gripped at its left edge by Fred's right hand
CRUMB_Y0, CRUMB_FLOOR = BAG_Y + 140.0, COUNTER_Y + 6.0   # out of the bag's bottom seal, onto the counter top
PLAN_STACK = dict(n=16, base_y=COUNTER_Y + 4.0, drop_h=420.0, every=0.33)
PLAN_X = 790.0
TUBE_STACK = dict(n=10, drop_h=420.0, every=0.28)


def layer_over(img, draw):
    s, c = E.surf()
    draw(c)
    return E.over(img, E.arr(s))


def char(img, look, x, y, s_, pose, t, shadow=0.0, rim=0.5, rim_col=(1.0, 0.7, 0.45), extra=None, ghost=0.0):
    ch = E.draw_person(look, x, y, s_, pose, t, extra)
    if ghost:      # a friendly ghost: pale, blue-rimmed, see-through, softly glowing
        a = ch[..., 3:4]
        ch[..., :3] = ch[..., :3] * 0.55 + np.array([0.75, 0.85, 1.0], np.float32) * 0.45
        glow = E.gblur(ch, 14 * K)
        ch[..., 3:4] = a * ghost
        img = E.over(img, np.dstack([glow[..., :3] * 0 + np.array([0.7, 0.85, 1.0], np.float32), glow[..., 3:4] * 0.45]))
        return E.over(img, ch)
    return E.light_char(ch, img, y, shadow=shadow, rim=rim, rim_col=rim_col)


def cam(name, keys):
    """Catmull camera with keys given relative to the scene start: [(dt, zoom, cx, cy)]."""
    a = span(name)[0]
    return lambda t: E.catmull([(a + dt, z, x, y) for dt, z, x, y in keys], t)


def counter(c, y, top=(150, 85, 45), front=(115, 60, 30), stripe=None):
    """A counter / bench seen from the front: covers the character's legs; its top edge is a physics surface."""
    c.drawRect(skia.Rect(-60, y - 22, W + 60, y + 10), P(C(*top)))
    c.drawRect(skia.Rect(-60, y + 10, W + 60, H), P(Shader=T.lin((0, y), (0, H), [C(*front), C(*[v * 0.6 for v in front])])))
    for k in range(10):
        x = 40 + k * 115
        c.drawLine(x, y + 40, x, H, S(C(0, 0, 0, 30), 5))
    if stripe:
        c.drawRect(skia.Rect(-60, y + 90, W + 60, y + 130), P(C(*stripe)))
    c.drawLine(-60, y - 22, W + 60, y - 22, S(T.OUT, 5))
    c.drawLine(-60, y + 10, W + 60, y + 10, S(T.OUT, 5))


def candle(c, x, y, t, ph=0.0, s=1.0):
    fl = 0.85 + 0.15 * noise1(t, int(ph * 10) + 9, 6)
    c.drawCircle(x, y - 70 * s, 120 * s, P(Shader=T.rad(x, y - 70 * s, 120 * s, [C(255, 190, 90, int(110 * fl)), C(255, 150, 60, 0)])))
    c.drawRoundRect(skia.Rect(x - 16 * s, y - 60 * s, x + 16 * s, y), 6, 6, P(C(250, 240, 220)))
    c.drawRoundRect(skia.Rect(x - 16 * s, y - 60 * s, x + 16 * s, y), 6, 6, S(T.OUT, 3))
    c.drawOval(skia.Rect(x - 7 * s, y - 92 * s * fl, x + 7 * s, y - 60 * s), P(C(255, 200, 80)))


def glow_can(c, x, y, s, t):
    c.drawCircle(x, y - 130 * s, 260 * s, P(Shader=T.rad(x, y - 130 * s, 260 * s, [C(255, 120, 80, int(70 + 20 * math.sin(t * 3))), C(255, 90, 60, 0)])))
    can2d(c, x, y, s)


# =================================================================================== 2D sets (drawn once, cached)
@lru_cache(maxsize=None)
def bg_grave(dawn=False):
    s, c = E.surf()
    top, mid, low = ((20, 22, 52), (60, 45, 95), (150, 80, 90)) if not dawn else ((40, 50, 95), (120, 90, 140), (240, 150, 120))
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, 1300), [C(*top), C(*mid), C(*low)], [0, 0.6, 1])))
    r = random.Random(4)
    for _ in range(70):
        c.drawCircle(r.uniform(0, W), r.uniform(0, 1000), r.uniform(1.5, 3.5), P(C(255, 255, 240, r.randint(90, 220))))
    c.drawCircle(830, 760, 260, P(Shader=T.rad(830, 760, 260, [C(255, 240, 200, 90), C(255, 240, 200, 0)])))
    c.drawCircle(830, 760, 95, P(C(250, 240, 210)))
    c.drawCircle(800, 740, 18, P(C(225, 215, 185)))
    c.drawCircle(858, 790, 12, P(C(225, 215, 185)))
    # rolling hills + distant headstones + a bare tree
    c.drawPath(path([(-50, 1280), (200, 1180), (480, 1240), (760, 1160), (1130, 1230), (1130, 1600), (-50, 1600)]), P(C(40, 45, 70)))
    for x, h in ((90, 120), (190, 90), (880, 110), (990, 140), (300, 70), (700, 80)):
        y0 = 1260
        c.drawRoundRect(skia.Rect(x - 32, y0 - h, x + 32, y0 + 20), 26, 26, P(C(70, 72, 95)))
        c.drawRoundRect(skia.Rect(x - 32, y0 - h, x + 32, y0 + 20), 26, 26, S(C(25, 25, 40), 4))
    tr = skia.Path()
    tr.moveTo(60, 1300); tr.lineTo(80, 980); tr.lineTo(20, 860); tr.moveTo(80, 980); tr.lineTo(160, 870); tr.lineTo(210, 840)
    tr.moveTo(118, 920); tr.lineTo(110, 820)
    c.drawPath(tr, S(C(25, 22, 35), 18))
    # grass
    c.drawRect(skia.Rect(0, 1420, W, H), P(Shader=T.lin((0, 1420), (0, H), [C(50, 80, 55), C(25, 40, 30)])))
    for k in range(90):
        x = r.uniform(0, W)
        y = r.uniform(1440, H)
        c.drawLine(x, y, x + r.uniform(-8, 8), y - r.uniform(14, 30), S(C(70, 110, 70, 160), 3))
    # Fred's headstone with gold engraving + the grave slab
    hs = skia.Path(); hs.addRoundRect(skia.Rect(300, 860, 780, 1460), 200, 200)
    c.drawPath(hs, P(Shader=T.lin((300, 0), (780, 0), [C(95, 98, 115), C(130, 133, 150), C(90, 92, 108)])))
    c.drawRect(skia.Rect(300, 1100, 780, 1460), P(Shader=T.lin((300, 0), (780, 0), [C(95, 98, 115), C(130, 133, 150), C(90, 92, 108)])))
    c.drawPath(hs, S(T.OUT, 6))
    c.drawLine(300, 1100, 300, 1460, S(T.OUT, 6)); c.drawLine(780, 1100, 780, 1460, S(T.OUT, 6))
    for txt, size, y in (("FREDRIC J.", 50, 1010), ("BAUR", 92, 1110), ("1918 - 2008", 50, 1190)):
        f = skia.Font(T.FB, size)
        w = f.measureText(txt)
        c.drawString(txt, 540 - w / 2 + 3, y + 3, f, P(C(40, 40, 55)))
        c.drawString(txt, 540 - w / 2, y, f, P(C(240, 205, 120)))
    c.drawRect(skia.Rect(220, 1440, 860, 1530), P(Shader=T.lin((0, 1440), (0, 1530), [C(140, 142, 158), C(95, 97, 112)])))
    c.drawRect(skia.Rect(220, 1440, 860, 1530), S(T.OUT, 6))
    return E.arr(s)


GRAVE_TOP = 1440.0       # the slab top: the can and the candles stand on it


@lru_cache(maxsize=None)
def bg_lab(chalk=False):
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(30, 62, 72), C(50, 95, 100), C(30, 60, 70)])))
    for k in range(9):    # tiled wall
        c.drawLine(0, 560 + k * 110, W, 560 + k * 110, S(C(255, 255, 255, 18), 3))
    if chalk:    # chalkboard with the idea sketched on it
        c.drawRoundRect(skia.Rect(90, 600, 990, 1300), 18, 18, P(C(150, 100, 55)))
        c.drawRect(skia.Rect(120, 630, 960, 1270), P(Shader=T.lin((0, 630), (0, 1270), [C(40, 80, 60), C(30, 62, 48)])))
        ch_ = S(C(235, 240, 230, 200), 6)
        sad = skia.Path(); sad.moveTo(560, 900); sad.cubicTo(640, 840, 760, 840, 840, 900); sad.cubicTo(760, 960, 640, 960, 560, 900)
        c.drawPath(sad, ch_)
        for k in range(4):
            yy = 1080 - k * 26
            sd = skia.Path(); sd.moveTo(600, yy); sd.cubicTo(660, yy - 30, 740, yy - 30, 800, yy)
            c.drawPath(sd, ch_)
        c.drawLine(700, 960, 700, 1010, ch_); c.drawLine(685, 995, 700, 1012, ch_); c.drawLine(715, 995, 700, 1012, ch_)
        f = skia.Font(T.FB, 60)
        c.drawString("?!", 900, 900, f, P(C(235, 240, 230, 200)))
        c.drawString("= =", 180, 900, f, P(C(235, 240, 230, 160)))
    else:        # shelves of flasks and books
        for row, y in enumerate((760, 1060)):
            c.drawRect(skia.Rect(60, y, 1020, y + 24), P(C(120, 80, 45)))
            c.drawRect(skia.Rect(60, y, 1020, y + 24), S(T.OUT, 4))
            r = random.Random(row + 3)
            x = 90
            while x < 980:
                kind = r.random()
                col = r.choice([(90, 200, 160), (240, 120, 80), (120, 160, 240), (240, 210, 90), (200, 110, 200)])
                if kind < 0.5:      # flask
                    h = r.uniform(110, 170)
                    fp = path([(x + 18, y - h), (x + 42, y - h), (x + 42, y - h * 0.55), (x + 70, y), (x - 10, y), (x + 18, y - h * 0.55)])
                    c.drawPath(fp, P(C(220, 240, 245, 150)))
                    c.drawPath(path([(x + 1, y - h * 0.3), (x + 59, y - h * 0.3), (x + 70, y), (x - 10, y)]), P(C(*col, 220)))
                    c.drawPath(fp, S(T.OUT, 3))
                    x += 95
                else:               # books
                    for b in range(r.randint(3, 6)):
                        h = r.uniform(120, 170)
                        bc = r.choice([(150, 50, 45), (50, 80, 130), (60, 110, 70), (170, 130, 50), (90, 60, 110)])
                        c.drawRect(skia.Rect(x, y - h, x + 26, y), P(C(*bc)))
                        c.drawRect(skia.Rect(x, y - h, x + 26, y), S(T.OUT, 2))
                        x += 28
                    x += 30
    # hanging lamp glow at the top
    c.drawCircle(540, 600, 520, P(Shader=T.rad(540, 600, 520, [C(255, 220, 150, 60), C(255, 200, 120, 0)])))
    counter(c, COUNTER_Y, top=(205, 210, 215), front=(70, 80, 95), stripe=(45, 50, 60))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_store():
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), [C(120, 60, 40), C(200, 120, 60), C(150, 80, 45)])))
    for k in range(12):   # 60s awning stripes at the top
        c.drawRect(skia.Rect(k * 100, 0, k * 100 + 50, 120), P(C(240, 230, 210, 70)))
    r = random.Random(11)
    for row, y in enumerate((800, 1060, 1320)):     # shelves of puffy chip bags
        c.drawRect(skia.Rect(40, y, 1040, y + 26), P(C(110, 65, 35)))
        c.drawRect(skia.Rect(40, y, 1040, y + 26), S(T.OUT, 4))
        x = 95
        while x < 1000:
            c.save(); c.translate(x, y - 75); c.scale(0.32, 0.4)
            p = skia.Path(); p.addRoundRect(skia.Rect(-110, -170, 110, 170), 60, 60)
            col = r.choice([(230, 170, 40), (210, 60, 50), (60, 140, 200), (90, 170, 90), (240, 120, 40)])
            c.drawPath(p, P(Shader=T.lin((-110, 0), (110, 0), [C(*[int(v * 0.8) for v in col]), C(*col), C(*[int(v * 0.75) for v in col])])))
            c.drawPath(p, S(T.OUT, 9))
            c.restore()
            x += 82
    counter(c, COUNTER_Y, top=(230, 215, 190), front=(170, 45, 45), stripe=(240, 225, 200))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_home(dark=False):
    s, c = E.surf()
    a, b = ((150, 92, 70), (138, 82, 62)) if not dark else ((95, 62, 52), (86, 55, 46))
    c.drawRect(skia.Rect(0, 0, W, H), P(C(*a)))
    for k in range(0, W, 90):   # wallpaper stripes
        c.drawRect(skia.Rect(k, 0, k + 45, 1560), P(C(*b)))
    # night window with the moon
    c.drawRect(skia.Rect(640, 640, 1000, 1080), P(Shader=T.lin((0, 640), (0, 1080), [C(25, 30, 70), C(60, 60, 120)])))
    c.drawCircle(900, 740, 40, P(C(250, 240, 210)))
    c.drawRect(skia.Rect(640, 640, 1000, 1080), S(C(240, 230, 210), 14))
    c.drawLine(820, 640, 820, 1080, S(C(240, 230, 210), 10)); c.drawLine(640, 860, 1000, 860, S(C(240, 230, 210), 10))
    for k, (x, y) in enumerate(((140, 700), (330, 760), (190, 950))):     # framed family photos
        c.drawRect(skia.Rect(x, y, x + 140, y + 170), P(C(200, 160, 90)))
        c.drawRect(skia.Rect(x + 14, y + 14, x + 126, y + 156), P(C(235, 225, 200)))
        c.drawCircle(x + 70, y + 70, 26, P(C(220, 180, 150)))
        c.drawRect(skia.Rect(x + 40, y + 98, x + 100, y + 156), P(C(110, 120, 150)))
        c.drawRect(skia.Rect(x, y, x + 140, y + 170), S(T.OUT, 4))
    # floor
    c.drawRect(skia.Rect(0, 1560, W, H), P(Shader=T.lin((0, 1560), (0, H), [C(140, 90, 55), C(90, 55, 35)])))
    for k in range(9):
        c.drawLine(0, 1600 + k * 40 + k * k * 4, W, 1600 + k * 40 + k * k * 4, S(C(60, 35, 20, 110), 3))
    c.drawLine(0, 1560, W, 1560, S(T.OUT, 5))
    # warm lamp glow (left)
    c.drawCircle(90, 1100, 600, P(Shader=T.rad(90, 1100, 600, [C(255, 200, 120, 110 if not dark else 140), C(255, 170, 90, 0)])))
    return E.arr(s)


HOME_FLOOR = 1800.0     # where standing people put their feet in the living room


def side_table(c, x, y):
    c.drawRect(skia.Rect(x - 110, y, x + 110, y + 26), P(C(120, 75, 40)))
    c.drawRect(skia.Rect(x - 90, y + 26, x + 90, HOME_FLOOR - 40), P(C(95, 58, 32)))
    c.drawRect(skia.Rect(x - 110, y, x + 110, y + 26), S(T.OUT, 4))
    c.drawRect(skia.Rect(x - 90, y + 26, x + 90, HOME_FLOOR - 40), S(T.OUT, 4))


# =================================================================================== scenes
def sc_hook(t, f):
    img = np.array(bg_grave())
    ti = word_t("hook", "idea", "own")
    img = layer_over(img, lambda c: (candle(c, 330, GRAVE_TOP + 30, t, 0.1), candle(c, 750, GRAVE_TOP + 30, t, 0.7),
                                     glow_can(c, 540, GRAVE_TOP + 40, 1.15, t)))
    ga = ramp(t, ti - 0.35, 0.4)
    if ga > 0:   # Fred's friendly ghost pops up beside his headstone, proud, on "his own idea"
        pose = dict(eyes="squint", brows="smug", mouth="grin", hands=[(-20, 120), (70, -150)], tilt=-6, look=(0.5, 0))
        img = char(img, FRED_OLD, 210, 1820 - 40 * math.sin(t * 2.2) - 120 * (1 - smooth(ga)), 1.35, pose, t, ghost=0.82 * ga)
    lays = [E.title_layer(t, [("THIS MAN IS", 70, 190, E.WHITE, -0.3), ("BURIED INSIDE", 96, 300, E.WHITE, word_t("hook", "buried")),
                              ("A CHIP CAN", 150, 450, E.GOLD, word_t("hook", "can", "chips"))]),
            E.stamp_layer(t, "HIS IDEA!", ti, 720, 1700, 120)]
    return img, cam("hook", [(0, 1.0, 540, 960), (2.5, 1.12, 540, 1080), (5.7, 1.2, 540, 1150)])(t), lays


def sc_fred(t, f):
    img = np.array(bg_lab())
    pose = dict(eyes="open", brows="up", mouth="smile", look=(0.4, -0.2), hands=[(-20, 120), (90, -130)], tilt=-4,
                blink=any(0 <= t - b < 0.1 for b in (7.0, 9.8)))
    x, y, s_ = 470, 1900, 2.05

    def flask(c):
        hx, hy = T.hand_pos(x, y, s_, pose, 1)
        p = skia.Path(); p.moveTo(hx - 14, hy - 110); p.lineTo(hx - 14, hy - 60); p.lineTo(hx - 52, hy + 12)
        p.quadTo(hx, hy + 32, hx + 52, hy + 12); p.lineTo(hx + 14, hy - 60); p.lineTo(hx + 14, hy - 110); p.close()
        c.drawPath(p, P(C(120, 230, 170, 200))); c.drawPath(p, S(T.OUT, 6))
        for k in range(4):
            ph = (t * 1.1 + k / 4) % 1.0
            c.drawCircle(hx + 10 * math.sin(k + t * 2), hy - 120 - 110 * ph, 8 + 8 * ph, P(C(200, 255, 220, int(170 * math.sin(math.pi * ph)))))
    img = char(img, FRED, x, y, s_, pose, t, extra=flask, rim_col=(1.0, 0.85, 0.6))
    img = layer_over(img, lambda c: counter(c, COUNTER_Y + 120, top=(205, 210, 215), front=(70, 80, 95), stripe=(45, 50, 60)))
    lays = [E.title_layer(t, [("FRED BAUR", 140, 330, E.GOLD, word_t("fred", "fred", "baur", "bauer"))]),
            E.stamp_layer(t, "NAVY VET", word_t("fred", "navy"), 370, 560, 90, (40, 70, 150), -8),
            E.stamp_layer(t, "PH.D.", word_t("fred", "phd", "ph", "chemistry"), 800, 600, 110, (200, 35, 45), 7),
            E.title_layer(t, [("CHEMIST", 90, 1700, E.WHITE, word_t("fred", "chemistry"))])]
    return img, cam("fred", [(0, 1.0, 540, 980), (6.6, 1.1, 520, 1020)])(t), lays


def sc_bags(t, f):
    img = np.array(bg_store())
    th = word_t("bags", "half", "air")
    tc = word_t("bags", "broken", "crumbs")
    x, y, s_ = FRED_BAGS
    sq = ramp(t, tc - 0.25, 0.25)
    pose = dict(eyes="squint" if t >= tc else "open", brows="angry" if t >= tc else "up", mouth="disgust" if t >= tc else "O", mouth_amt=0.8,
                hands=BAGS_POSE_HANDS, tilt=-3, look=(0.8, -0.2))
    img = layer_over(img, lambda c: bag(c, BAG_X, BAG_Y, 0.95, ramp(t, th - 0.2, 0.3) * (1 - 0.6 * sq)))   # behind the hand: he grips it
    img = char(img, FRED, x, y, s_, pose, t)
    img = layer_over(img, lambda c: (counter(c, COUNTER_Y, top=(230, 215, 190), front=(170, 45, 45), stripe=(240, 225, 200)),
                                     crumbs(c, t, tc, BAG_X, CRUMB_Y0, CRUMB_FLOOR)))
    lays = [E.title_layer(t, [("1960s CHIPS:", 100, 320, E.WHITE, word_t("bags", "nineteen", "1960s", "sixties"))]),
            E.stamp_layer(t, "HALF AIR", th, 540, 520, 130),
            E.title_layer(t, [("BROKEN CRUMBS", 96, 1720, E.GOLD, tc)])]
    return img, cam("bags", [(0, 1.0, 540, 980), (5.8, 1.08, 560, 1020)])(t), lays


def sc_plan(t, f):
    img = np.array(bg_lab(chalk=True))
    tsame = word_t("plan", "same", "shape")
    tstack = word_t("plan", "stack")
    x, y, s_ = 300, 1800, 1.95
    cheering = t > tstack + 1.2
    thinking = t < tsame - 0.1
    pose = dict(eyes="squint" if cheering else "open", brows="smug" if thinking else "up", mouth="grin" if cheering else "smile",
                look=(0.8, -0.4) if not thinking else (0.3, -0.8),
                hands=[(-30, -150), (30, -150)] if cheering else ([(-20, 120), (40, -60)] if thinking else [(-20, 120), (140, -40)]), tilt=-5)
    img = char(img, FRED, x, y, s_, pose, t)

    def draw(c):
        counter(c, COUNTER_Y, top=(205, 210, 215), front=(70, 80, 95), stripe=(45, 50, 60))
        if t >= tsame - 0.2:
            for k, (yy, landed) in enumerate(stack_state(t, tsame, PLAN_STACK["n"], PLAN_STACK["base_y"], PLAN_STACK["drop_h"], PLAN_STACK["every"])):
                chip(c, PLAN_X, yy, 1.6)
    img = layer_over(img, draw)
    if thinking:     # "Fred had a strange plan": no empty seconds before the next title
        return img, cam("plan", [(0, 1.0, 540, 980), (3.0, 1.06, 520, 1000)])(t), [
            E.title_layer(t, [("A STRANGE PLAN", 104, 320, E.GOLD, word_t("plan", "strange"))])]
    lays = [E.title_layer(t, [("THE SAME SHAPE", 100, 320, E.GOLD, tsame)]),
            E.stamp_layer(t, "STACKABLE!", tstack, 540, 500, 120),
            E.title_layer(t, [("LIKE ROOF TILES", 84, 1720, E.WHITE, word_t("plan", "roof", "tiles"))])]
    return img, cam("plan", [(0, 1.0, 540, 980), (3.0, 1.06, 520, 1000), (8.9, 1.12, 640, 1060)])(t), lays


def sc_tube(t, f):
    img = np.array(bg_lab())
    img = E.gblur(img, 6 * K)
    tna = word_t("tube", "air")
    x, y, s_ = 390, 2080, 2.35
    pose = dict(eyes="squint", brows="up", mouth="grin", hands=[(-20, 120), (120, -120)], tilt=-6, look=(0.8, -0.3))
    img = char(img, FRED, x, y, s_, pose, t)
    hx, hy = T.hand_pos(x, y, s_, pose, 1)

    def draw(c):
        cx_, cy_ = hx + 110, hy + 260
        for k, (yy, landed) in enumerate(stack_state(t, span("tube")[0] + 0.4, TUBE_STACK["n"], cy_ - 30, TUBE_STACK["drop_h"], TUBE_STACK["every"])):
            if not landed:
                chip(c, cx_, yy, 1.0)
        can2d(c, cx_, cy_, 1.5, open_top=True)
    img = layer_over(img, draw)
    lays = [E.title_layer(t, [("A TALL TUBE", 120, 320, E.GOLD, word_t("tube", "tube", "tall"))]),
            E.stamp_layer(t, "NO AIR", tna, 300, 560, 120, (40, 140, 70), -8),
            E.stamp_layer(t, "NO CRUMBS", word_t("tube", "crushed"), 760, 700, 100, (40, 140, 70), 6)]
    return img, cam("tube", [(0, 1.0, 540, 980), (5.5, 1.08, 560, 1020)])(t), lays


def sc_patent(t, f):
    img = np.array(bg_lab())
    tp = word_t("patent", "patent")
    tf = word_t("patent", "famous")
    x, y, s_ = 300, 1800, 1.95
    pose = dict(eyes="squint" if t > tp else "open", brows="up", mouth="grin", hands=[(-20, 120), (130, -70)], tilt=-4, look=(0.8, -0.2))
    img = char(img, FRED, x, y, s_, pose, t)
    sl = snap(t, span("patent")[0] + 0.2, 9)

    def draw(c):
        counter(c, COUNTER_Y, top=(205, 210, 215), front=(70, 80, 95), stripe=(45, 50, 60))
        parchment(c, lerp(1400, 790, sl), 1330, 1.05, lerp(20, -5, sl), t > tp)
        if t > tf:     # the can goes global: cans pop up along the counter top
            for k in range(8):
                tk = tf + k * 0.12
                if t > tk:
                    a = T.out_back(min(1, (t - tk) / 0.25), 1.6)
                    can2d(c, 90 + k * 128, COUNTER_Y + 2, 0.75 * a)
    img = layer_over(img, draw)
    lays = [E.stamp_layer(t, "PATENT 1970", tp, 600, 560, 120),
            E.title_layer(t, [("FAMOUS WORLDWIDE", 92, 330, E.GOLD, tf)])]
    return img, cam("patent", [(0, 1.0, 540, 960), (6.3, 1.06, 560, 990)])(t), lays


def sc_twist(t, f):
    img = np.array(bg_home())
    tp = word_t("twist", "put")
    shock = t > tp + 0.1
    img = char(img, FRED_OLD, 330, HOME_FLOOR + 40, 1.75, dict(eyes="squint", brows="up", mouth="grin" if t < tp else "talk", talk=0.5 + 0.5 * math.sin(t * 20),
                                                                hands=[(-20, 120), (90, -110)], tilt=-4, look=(0.6, 0)), t, shadow=0.45)
    img = char(img, DAUGHTER, 720, HOME_FLOOR, 1.45, dict(eyes="wide" if shock else "open", brows="up", mouth="O" if shock else "smile", look=(-0.8, 0),
                                                          hands=[(-30, -60), (30, -60)] if shock else [(-20, 120), (20, 120)]), t, shadow=0.45)
    img = char(img, SON, 930, HOME_FLOOR + 20, 1.5, dict(eyes="wide" if shock else "open", brows="up" if shock else "flat", mouth="O" if shock else "smile",
                                                         look=(-0.9, 0), hands=[(-20, 120), (20, 120)], tilt=6 if shock else 0), t, shadow=0.45)
    img = layer_over(img, lambda c: smile_bubble(c, 400, 900, "PUT ME IN IT!", (t - tp) / 0.25))
    lays = [E.title_layer(t, [("THE TWIST", 140, 330, E.GOLD, word_t("twist", "twist"))]),
            E.title_layer(t, [("SO PROUD...", 90, 470, E.WHITE, word_t("twist", "proud"))])]
    return img, cam("twist", [(0, 1.0, 540, 960), (6.7, 1.06, 560, 990)])(t), lays


def sc_died(t, f):
    img = np.array(bg_home(dark=True))
    tk = word_t("died", "kept", "promise")
    img = layer_over(img, lambda c: (side_table(c, 830, 1480),
                                     c.drawCircle(830, 1330, 300, P(Shader=T.rad(830, 1330, 300, [C(255, 200, 120, 80), C(255, 170, 90, 0)]))),
                                     can2d(c, 830, 1480, 1.0)))
    if t > tk - 0.3:
        img = char(img, DAUGHTER, 300, HOME_FLOOR, 1.5, dict(eyes="sad", brows="sad", mouth="smile", hands=[(-20, 120), (60, -40)], look=(0.8, 0)), t, shadow=0.45)
        img = char(img, SON, 540, HOME_FLOOR + 20, 1.55, dict(eyes="sad", brows="sad", mouth="smile", hands=[(-20, 120), (20, 120)], look=(0.8, 0), tilt=5), t, shadow=0.45)
    lays = [E.title_layer(t, [("2008", 150, 330, E.WHITE, word_t("died", "2008", "two", "thousand")), ("AGE 89", 110, 480, E.GOLD, word_t("died", "89", "eightynine", "eighty"))]),
            E.stamp_layer(t, "PROMISE KEPT", tk, 540, 680, 110, (40, 140, 70), -6)]
    return img, cam("died", [(0, 1.0, 540, 960), (4.9, 1.08, 620, 1000)])(t), lays


def sc_ashes(t, f):
    img = np.array(bg_grave(dawn=True))
    img = layer_over(img, lambda c: (candle(c, 330, GRAVE_TOP + 30, t, 0.1), candle(c, 750, GRAVE_TOP + 30, t, 0.7), glow_can(c, 540, GRAVE_TOP + 40, 1.15, t)))
    img = char(img, DAUGHTER, 170, 1900, 1.45, dict(eyes="sad", brows="sad", mouth="smile", hands=[(-20, 120), (70, -30)], look=(0.8, -0.3)), t, shadow=0.4)
    img = char(img, SON, 920, 1910, 1.5, dict(eyes="sad", brows="sad", mouth="smile", hands=[(-20, 120), (20, 120)], look=(-0.8, -0.3)), t, shadow=0.4)
    lays = [E.title_layer(t, [("HIS ASHES", 110, 320, E.WHITE, word_t("ashes", "ashes")), ("IN A CHIP CAN", 120, 470, E.GOLD, word_t("ashes", "can", "chip"))]),
            E.stamp_layer(t, "OHIO", word_t("ashes", "ohio"), 540, 660, 130)]
    return img, cam("ashes", [(0, 1.0, 540, 960), (4.3, 1.08, 540, 1040)])(t), lays


def sc_end(t, f):
    img = np.array(bg_grave())
    img = layer_over(img, lambda c: (candle(c, 330, GRAVE_TOP + 30, t, 0.1), candle(c, 750, GRAVE_TOP + 30, t, 0.7), glow_can(c, 540, GRAVE_TOP + 40, 1.15, t)))
    ga = ramp(t, span("end")[0] + 0.6, 0.5)
    if ga > 0:
        pose = dict(eyes="squint", brows="up", mouth="grin", hands=[(-20, 120), (60, -160)], tilt=6)
        img = char(img, FRED_OLD, 860, 1820 - 40 * math.sin(t * 2.2), 1.35, pose, t, ghost=0.82 * ga)
    lays = [E.title_layer(t, [("STILL INSIDE", 120, 320, E.WHITE, word_t("end", "still")), ("HIS OWN CAN", 130, 470, E.GOLD, word_t("end", "inside", "one"))])]
    return img, cam("end", [(0, 1.0, 540, 1000), (3.6, 1.3, 540, 1300)])(t), lays


def sc_cta(t, f):
    from cta2 import draw_cta2
    img = E.gblur(np.array(bg_grave()), 10 * K)
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
    assert CRUMB_FLOOR > CRUMB_Y0, "crumbs must fall DOWN onto the counter"
    return dict(chip_fall_s=PHYS["chip_fall_s"], chip_t=CHIP_T, g_px=G_PX, scenes=[(n, round(a, 3)) for n, a in SCENES], dur=DUR,
                bag=(BAG_X, BAG_Y), crumb_floor=CRUMB_FLOOR)


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
