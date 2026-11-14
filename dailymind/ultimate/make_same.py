"""LONG-FORM (16:9, ~10 min): "What If Everyone Had the Same Looks, Strength and IQ?" - APPROVED 2D Classic+ style.

Facts used (sourced in the commit / chat): people know ~5,000 faces (Jenkins et al. 2018, Proc. R. Soc. B); a brain area
specialises in faces; identical twins have different fingerprints (ridge detail set in the womb, weeks 13-19); mere
exposure effect (Zajonc 1968); Phelps ~6'4" with a ~6'7" arm span, 28 Olympic medals; comparative advantage (Ricardo 1817);
IQ bell curve, mean 100; Gros Michel banana (clones) wiped out as an export crop by Panama disease by the 1950s, Cavendish
also clonal, TR4 spreading; Irish famine 1840s, Lumper clones, ~1 million deaths; cheetahs accepted skin grafts from
unrelated cheetahs (O'Brien et al. 1985, criticised); identical twins diverge epigenetically with age (Fraga et al. 2005).
Generic cartoon people only - no likenesses (Phelps is shown as a generic swimmer diagram).

  python make_same.py frames | stills 3.0,40.5
"""
import json
import math
import os
import random
import sys
from functools import lru_cache
from multiprocessing import Pool

os.environ["S2D_ASPECT"] = "16:9"
import numpy as np  # noqa: E402
import skia  # noqa: E402

import style2d_engine as E  # noqa: E402
import toon as T  # noqa: E402
from style2d_engine import C, P, S, BLUR, W, H, K, FPS, path, lerp, lerp2, clamp, ramp, snap, smooth, noise1  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "same")
LINES = json.load(open(os.path.join(D, "lines.json")))
ORDER = [l["key"] for l in LINES]
CHAPTER = {l["key"]: l["chapter"] for l in LINES}
_tj = os.path.join(D, "vo.wav.times.json")
_have = json.load(open(_tj)) if os.path.exists(_tj) else {}
if set(ORDER) <= set(_have):
    TIMES = _have
    WORDS = json.load(open(os.path.join(D, "vo.wav.words.json")))
else:   # estimate until the voice for every line exists (stills only)
    TIMES, WORDS, t = {}, {}, 0.0
    for l in LINES:
        t += l["gap_before"]
        TIMES[l["key"]] = round(t, 3)
        for i, wd in enumerate(l["text"].split()):
            k = "".join(ch for ch in wd.lower() if ch.isalpha() or ch == "'")
            kk, n = k, 1
            while kk in WORDS:
                n += 1
                kk = f"{k}#{n}"
            WORDS[kk] = round(t + i * 0.36, 3)
        t += len(l["text"]) / 17.3
END_HOLD = 6.0
VO_END = TIMES[ORDER[-1]] + len(LINES[-1]["text"]) / 15.0
DUR = VO_END + END_HOLD
NF = int(round(DUR * FPS))


def L(key):
    return TIMES[key]


def wt(line, word, nth=1):
    t0 = TIMES[line] - 0.05
    hits = sorted(v for k, v in WORDS.items() if k.split("#")[0] == word and v >= t0)
    if len(hits) < nth:
        raise KeyError(f"word {word!r} not found after line {line!r}")
    return hits[nth - 1]


def wt_or(line, word, dflt):
    try:
        return wt(line, word)
    except KeyError:
        return L(line) + dflt


# shots: one per line; a chapter change gets the gold splat + a chapter title
SHOT_START = [0.0] + [L(k) - 0.12 for k in ORDER[1:]]
SHOT_END = SHOT_START[1:] + [DUR]
CHAP_ORDER = []
for l in LINES:
    if not CHAP_ORDER or CHAP_ORDER[-1] != l["chapter"]:
        CHAP_ORDER.append(l["chapter"])
CHAP_TITLE = {"hook": None, "morning": "1. THE MORNING", "identity": "2. WHO IS WHO?", "crime": "3. CRIME", "love": "4. LOVE",
              "fame": "5. FAME", "sports": "6. SPORTS", "jobs": "7. JOBS & MONEY", "school": "8. SCHOOL", "disease": "9. THE REAL DANGER",
              "drift": "10. THE TWIST", "ending": "11. SO WHAT HAPPENS?"}
CHAP_CUTS = [SHOT_START[i] for i in range(1, len(ORDER)) if CHAPTER[ORDER[i]] != CHAPTER[ORDER[i - 1]]]


def shot_at(t):
    for i in range(len(ORDER)):
        if SHOT_START[i] <= t < SHOT_END[i]:
            return i
    return len(ORDER) - 1


# =================================================================================== looks
AVG = dict(skin=(222, 178, 142), hair="neat", hair_col=(70, 50, 38), coat=(110, 130, 165), pants=(70, 75, 92), nose="small")
UNIQUE = [dict(skin=(250, 210, 180), hair="pigtails", hair_col=(200, 140, 60), coat=(230, 120, 140), pants=(80, 70, 100), nose="small"),
          dict(skin=(140, 95, 65), hair="curly", hair_col=(30, 22, 20), coat=(240, 200, 70), pants=(60, 60, 80), nose="small"),
          dict(skin=(235, 190, 150), hair="grey", hair_col=(170, 170, 180), coat=(70, 90, 70), pants=(60, 55, 50), nose="long", glasses=True),
          dict(skin=(190, 140, 100), hair="kid", hair_col=(60, 40, 25), coat=(90, 170, 220), pants=(70, 70, 90), nose="small"),
          dict(skin=(245, 200, 165), hair="neat", hair_col=(140, 70, 30), coat=(60, 60, 70), vest=(150, 30, 40), pants=(40, 40, 45),
               nose="long", mustache=True)]


def avg(**kw):
    d = dict(AVG)
    d.update(kw)
    return d


def P_(eyes="open", brows="flat", mouth="smile", look=(0, 0), lean=0, tilt=0, hands=None, **kw):
    d = dict(eyes=eyes, brows=brows, mouth=mouth, look=look, lean=lean, tilt=tilt, hands=hands or [(-20, 150), (20, 150)])
    d.update(kw)
    return d


def blink_at(t, seed, period=3.3):
    return ((t + seed * 0.77) % period) < 0.1


def crowd_layer(t, people):
    """people: [(look, x, y, s, pose)] drawn back-to-front with soft contact shadows, one lighting pass for the layer."""
    s, c = E.surf()
    for look, x, y, sc, pose in sorted(people, key=lambda q: q[2]):
        c.drawOval(skia.Rect(x - 70 * sc, y - 12 * sc, x + 70 * sc, y + 10 * sc), P(C(0, 0, 0, 70), MaskFilter=BLUR(8 * sc)))
        T.person(c, x, y, sc, look, pose, t)
    return E.arr(s)


def lit(img, layer, rim=0.45, rim_col=(1.0, 0.8, 0.55)):
    return E.light_char(layer, img, 0, shadow=0, rim=rim, rim_col=rim_col)


# =================================================================================== backgrounds
def grad_bg(top, bot, mid=None):
    s, c = E.surf()
    cols = [C(*top), C(*mid), C(*bot)] if mid else [C(*top), C(*bot)]
    c.drawRect(skia.Rect(0, 0, W, H), P(Shader=T.lin((0, 0), (0, H), cols)))
    return s, c


@lru_cache(maxsize=None)
def bg_bathroom():
    s, c = grad_bg((150, 190, 205), (110, 150, 170))
    for y in range(0, H, 90):                     # tiles
        c.drawLine(0, y, W, y, S(C(255, 255, 255, 40), 3))
    for x in range(0, W, 90):
        c.drawLine(x, 0, x, H, S(C(255, 255, 255, 40), 3))
    c.drawRect(skia.Rect(0, 820, W, H), P(C(235, 235, 230)))   # sink counter
    c.drawRect(skia.Rect(0, 820, W, 850), P(C(200, 200, 195)))
    c.drawRoundRect(skia.Rect(1060, 120, 1700, 800), 30, 30, P(C(210, 225, 230)))   # mirror frame
    c.drawRoundRect(skia.Rect(1085, 145, 1675, 775), 22, 22, P(Shader=T.lin((1085, 145), (1675, 775), [C(190, 215, 225), C(150, 180, 195)])))
    c.drawRoundRect(skia.Rect(1060, 120, 1700, 800), 30, 30, S(T.OUT, 6))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_city(night=False):
    if night:
        s, c = grad_bg((20, 25, 60), (70, 60, 110))
    else:
        s, c = grad_bg((120, 180, 230), (250, 215, 170))
    r = random.Random(3)
    for layer, (yb, col) in enumerate((((560, (150, 170, 200)) if not night else (560, (50, 55, 95))),
                                       ((650, (110, 130, 170)) if not night else (650, (35, 40, 75))))):
        x = -20
        while x < W:
            w = r.uniform(90, 200)
            h = r.uniform(150, 420)
            c.drawRect(skia.Rect(x, yb - h, x + w, yb + 400), P(C(*col)))
            for wy in range(int(yb - h + 25), int(yb), 46):
                for wx in range(int(x + 15), int(x + w - 20), 38):
                    if r.random() < (0.55 if night else 0.25):
                        c.drawRect(skia.Rect(wx, wy, wx + 18, wy + 24), P(C(255, 225, 140, 200 if night else 120)))
            x += w + r.uniform(4, 20)
    c.drawRect(skia.Rect(0, 760, W, H), P(Shader=T.lin((0, 760), (0, H), [C(170, 165, 160), C(120, 115, 115)])))   # pavement
    for x in range(-100, W, 160):
        c.drawLine(x, 760, x - 120, H, S(C(90, 90, 95, 60), 3))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_room(col=(235, 205, 160), floor=(160, 110, 70)):
    s, c = grad_bg(tuple(min(255, v + 15) for v in col), col)
    c.drawRect(skia.Rect(0, 780, W, H), P(Shader=T.lin((0, 780), (0, H), [C(*floor), C(*[v * 0.7 for v in floor])])))
    c.drawLine(0, 780, W, 780, S(T.OUT, 5))
    c.drawRect(skia.Rect(1350, 140, 1760, 520), P(C(170, 215, 240)))        # window
    c.drawRect(skia.Rect(1350, 140, 1760, 520), S(T.OUT, 8))
    c.drawLine(1555, 140, 1555, 520, S(T.OUT, 6))
    c.drawLine(1350, 330, 1760, 330, S(T.OUT, 6))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_dark(col=(25, 20, 45), col2=(60, 40, 90)):
    s, c = grad_bg(col, col2)
    r = random.Random(1)
    for i in range(120):
        c.drawCircle(r.uniform(0, W), r.uniform(0, H), r.uniform(1, 3), P(C(255, 255, 255, int(r.uniform(30, 120)))))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_stadium():
    s, c = grad_bg((80, 150, 220), (190, 225, 250))
    c.drawRect(skia.Rect(0, 260, W, 560), P(C(70, 80, 110)))            # stands
    r = random.Random(8)
    for i in range(900):
        c.drawCircle(r.uniform(0, W), r.uniform(280, 550), 7, P(C(*r.choice(((230, 90, 80), (240, 200, 80), (90, 150, 230), (240, 240, 240))))))
    c.drawRect(skia.Rect(0, 560, W, H), P(C(205, 90, 70)))              # track
    for k in range(6):
        y = 600 + k * 80
        c.drawLine(0, y, W, y, S(C(255, 255, 255, 200), 5))
    return E.arr(s)


@lru_cache(maxsize=None)
def bg_field(kind="banana"):
    if kind == "banana":
        s, c = grad_bg((150, 205, 235), (230, 240, 210))
        c.drawRect(skia.Rect(0, 600, W, H), P(C(120, 160, 80)))
    else:
        s, c = grad_bg((150, 160, 175), (205, 205, 200))
        c.drawRect(skia.Rect(0, 560, W, H), P(C(110, 85, 60)))
        for k in range(12):
            c.drawLine(0, 600 + k * 45, W, 600 + k * 45, S(C(80, 60, 40), 6))
    return E.arr(s)


# =================================================================================== props
def mirror_face(c, look, t, x, y, s, pose):
    c.save()
    c.clipRect(skia.Rect(1085, 145, 1675, 775), doAntiAlias=True)
    T.person(c, x, y, s, look, pose, t)
    c.restore()


def blend_looks(t, A, B, u, x, y, sc, pose):
    """Morph one look into another: draw A, then B on top with alpha u (both share the same pose)."""
    s, c = E.surf()
    if u < 1:
        T.person(c, x, y, sc, A, pose, t)
    if u > 0:
        c.saveLayerAlpha(None, int(255 * u))
        T.person(c, x, y, sc, B, pose, t)
        c.restore()
    return s, c


def stat_bar(c, x, y, w, label, val, col):
    f = skia.Font(T.FB, 40)
    c.drawString(label, x, y - 16, f, P(C(255, 255, 255)))
    c.drawRoundRect(skia.Rect(x, y, x + w, y + 42), 21, 21, P(C(30, 25, 50, 220)))
    c.drawRoundRect(skia.Rect(x, y, x + w * clamp(val), y + 42), 21, 21, P(Shader=T.lin((x, 0), (x + w, 0), [C(*col), C(*[min(255, v + 60) for v in col])])))
    c.drawRoundRect(skia.Rect(x, y, x + w, y + 42), 21, 21, S(C(255, 255, 255, 160), 3))
    c.drawLine(x + w / 2, y - 8, x + w / 2, y + 50, S(C(255, 236, 140), 4))


def globe(c, x, y, r, t):
    c.drawCircle(x, y, r * 1.15, P(Shader=T.rad(x, y, r * 1.15, [C(120, 200, 255, 90), C(120, 200, 255, 0)])))
    c.drawCircle(x, y, r, P(Shader=T.rad(x - r * 0.3, y - r * 0.3, r * 1.4, [C(90, 170, 240), C(30, 80, 170)])))
    c.save()
    c.clipPath(skia.Path().addCircle(x, y, r), doAntiAlias=True)
    rr = random.Random(5)
    rot = t * 30
    for i in range(9):
        lx = x - r + ((rr.uniform(0, 2 * r) + rot) % (2.6 * r)) - 0.3 * r
        ly = y + rr.uniform(-0.7, 0.7) * r
        c.drawOval(skia.Rect(lx - r * 0.25, ly - r * 0.16, lx + r * 0.25, ly + r * 0.16), P(C(90, 180, 100)))
    c.restore()
    c.drawCircle(x, y, r, S(T.OUT, 6))


def phone(c, x, y, s, screen_cb=None):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawRoundRect(skia.Rect(-110, -210, 110, 210), 30, 30, P(C(30, 30, 40)))
    c.drawRoundRect(skia.Rect(-98, -195, 98, 195), 22, 22, P(C(235, 240, 250)))
    if screen_cb:
        c.save()
        c.clipRRect(skia.RRect.MakeRectXY(skia.Rect(-98, -195, 98, 195), 22, 22), doAntiAlias=True)
        screen_cb(c)
        c.restore()
    c.drawRoundRect(skia.Rect(-110, -210, 110, 210), 30, 30, S(T.OUT, 5))
    c.restore()


def check_mark(c, x, y, r, col=(60, 200, 110), a=255):
    c.drawCircle(x, y, r, P(C(*col, a)))
    p = path([(x - r * 0.45, y), (x - r * 0.1, y + r * 0.35), (x + r * 0.5, y - r * 0.35)], close=False)
    c.drawPath(p, S(C(255, 255, 255, a), r * 0.22))


def cross_mark(c, x, y, r, a=255):
    c.drawCircle(x, y, r, P(C(220, 50, 50, a)))
    c.drawLine(x - r * 0.4, y - r * 0.4, x + r * 0.4, y + r * 0.4, S(C(255, 255, 255, a), r * 0.2))
    c.drawLine(x + r * 0.4, y - r * 0.4, x - r * 0.4, y + r * 0.4, S(C(255, 255, 255, a), r * 0.2))


def fingerprint(c, x, y, r, seed, col=(70, 60, 90), reveal=1.0, mark=None):
    """Concentric ridge loops with seeded wobble; mark = list of (angle, ring) minutiae to circle."""
    rr = random.Random(seed)
    n = 13
    for k in range(int(n * reveal)):
        rk = r * (0.12 + 0.88 * k / n)
        p = skia.Path()
        ph = rr.uniform(0, 6.28)
        for j in range(0, 73):
            a = j / 72 * 2 * math.pi
            rad = rk * (1 + 0.05 * math.sin(3 * a + ph) + 0.03 * math.sin(7 * a + ph * 2))
            px, py = x + rad * math.cos(a) * 0.82, y + rad * math.sin(a)
            p.moveTo(px, py) if j == 0 else p.lineTo(px, py)
        c.drawPath(p, S(C(*col), 5))
    for (a, ring) in (mark or []):
        rk = r * (0.12 + 0.88 * ring / n)
        c.drawCircle(x + rk * math.cos(a) * 0.82, y + rk * math.sin(a), 22, S(C(230, 50, 60), 6))


def door(c, x, y, w, h, col, sign=None, open_amt=0.0):
    c.drawRect(skia.Rect(x, y, x + w, y + h), P(C(40, 30, 30)))
    c.drawRect(skia.Rect(x + w * open_amt * 0.8, y, x + w, y + h), P(C(*col)))
    c.drawRect(skia.Rect(x, y, x + w, y + h), S(T.OUT, 6))
    if sign:
        f = skia.Font(T.FB, E.fit_size(sign, 46, w + 40))
        tw = f.measureText(sign)
        c.drawRoundRect(skia.Rect(x + w / 2 - tw / 2 - 18, y - 80, x + w / 2 + tw / 2 + 18, y - 16), 12, 12, P(C(250, 245, 230)))
        c.drawRoundRect(skia.Rect(x + w / 2 - tw / 2 - 18, y - 80, x + w / 2 + tw / 2 + 18, y - 16), 12, 12, S(T.OUT, 4))
        c.drawString(sign, x + w / 2 - tw / 2, y - 31, f, P(C(40, 30, 40)))


def label(c, x, y, txt, size=48, col=(255, 255, 255), bg=(20, 15, 30, 190), a=255):
    f = skia.Font(T.FB, size)
    w = f.measureText(txt)
    c.drawRoundRect(skia.Rect(x - w / 2 - 22, y - size * 0.95, x + w / 2 + 22, y + size * 0.35), 16, 16, P(C(*bg[:3], int(bg[3] * a / 255))))
    c.drawString(txt, x - w / 2, y, f, P(C(*col, a)))


def banana(c, x, y, s, rot=0.0, sick=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    p = skia.Path()
    p.moveTo(-60, -10)
    p.cubicTo(-30, 40, 40, 40, 66, -14)
    p.cubicTo(40, 18, -20, 18, -60, -10)
    col = (lerp(250, 70, sick), lerp(220, 60, sick), lerp(80, 30, sick))
    c.drawPath(p, P(C(*col)))
    c.drawLine(-60, -10, -70, -18, S(C(90, 70, 30), 8))
    c.drawPath(p, S(T.OUT, 4))
    c.restore()


def plant(c, x, y, s, t, sick=0.0, kind="banana"):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    sway = 3 * noise1(t, int(x) % 97, 0.6)
    c.rotate(sway)
    if kind == "banana":
        c.drawRect(skia.Rect(-14, -260, 14, 0), P(C(lerp(110, 90, sick), lerp(140, 80, sick), lerp(60, 40, sick))))
        for k in range(5):
            a = -150 + k * 30
            lp = skia.Path()
            lp.moveTo(0, -250)
            ex, ey = 170 * math.cos(math.radians(a)), -250 + 120 * math.sin(math.radians(a)) + 40
            lp.quadTo(ex * 0.5, -330, ex, ey + 60 * sick)
            c.drawPath(lp, S(C(lerp(70, 140, sick), lerp(160, 110, sick), lerp(70, 40, sick)), 34))
        banana(c, 20, -170, 0.6, 30, sick)
        banana(c, 30, -150, 0.6, 50, sick)
    else:   # potato plant
        for k in range(6):
            a = -160 + k * 28
            c.drawCircle(70 * math.cos(math.radians(a)), -60 + 50 * math.sin(math.radians(a)), 34,
                         P(C(lerp(80, 70, sick), lerp(140, 60, sick), lerp(60, 40, sick))))
        if sick > 0.2:
            for k in range(6):
                c.drawCircle(60 * math.cos(k * 1.1), -60 + 30 * math.sin(k * 1.7), 12 * sick, P(C(40, 30, 25, 200)))
    c.restore()


def cheetah(c, x, y, s, t, flip=1):
    c.save()
    c.translate(x, y)
    c.scale(s * flip, s)
    """Lean cat in profile: deep chest, tucked waist, long jointed legs (a stride cycle), small head, black tear marks."""
    coat, dark = C(205, 150, 70), C(170, 115, 45)
    tail = skia.Path()
    tail.moveTo(-110, -50)
    tail.cubicTo(-170, -50, -200, -10, -230 + 12 * math.sin(t * 3), 10)
    c.drawPath(tail, S(T.OUT, 18))
    c.drawPath(tail, S(coat, 12))
    for k, (hx, far) in enumerate(((-80, True), (70, True), (-60, False), (90, False))):   # far legs darker, drawn first
        ph = t * 7 + k * 1.6 + (math.pi if far else 0)
        knee = (hx + 14 * math.sin(ph), 10)
        foot = (hx + 30 * math.sin(ph) - 6, 72 - 8 * max(0, math.cos(ph)))
        leg = path([(hx, -30), knee, foot], close=False)
        c.drawPath(leg, S(T.OUT, 20))
        c.drawPath(leg, S(dark if far else coat, 13))
    body = skia.Path()
    body.moveTo(-120, -40)
    body.cubicTo(-120, -80, -40, -78, 20, -74)          # back
    body.cubicTo(80, -72, 120, -70, 120, -40)           # shoulders
    body.cubicTo(118, 0, 70, 6, 40, -6)                 # deep chest
    body.cubicTo(0, -24, -60, -24, -95, -10)            # tucked waist
    body.cubicTo(-115, -6, -122, -20, -120, -40)
    body.close()
    c.drawPath(body, P(coat))
    r = random.Random(2)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    for i in range(30):
        c.drawCircle(r.uniform(-115, 115), r.uniform(-75, -5), r.uniform(4, 7), P(C(55, 35, 25)))
    c.restore()
    c.drawPath(body, S(T.OUT, 4))
    c.drawLine(110, -60, 140, -78, S(T.OUT, 26))         # neck
    c.drawLine(110, -60, 140, -78, S(coat, 18))
    head = skia.Path()
    head.addOval(skia.Rect(122, -112, 190, -64))
    c.drawPath(head, P(coat))
    c.drawPath(head, S(T.OUT, 4))
    c.drawCircle(168, -95, 5, P(T.OUT))
    c.drawLine(166, -90, 178, -70, S(C(40, 25, 20), 4))   # tear mark
    c.drawPath(path([(134, -106), (140, -124), (150, -108)]), P(coat))   # ear
    c.restore()


def virus(c, x, y, r, t, col=(200, 60, 90), a=255):
    c.save()
    c.translate(x, y)
    c.rotate(t * 40)
    for k in range(10):
        ang = k / 10 * 2 * math.pi
        c.drawLine(r * math.cos(ang), r * math.sin(ang), r * 1.45 * math.cos(ang), r * 1.45 * math.sin(ang), S(C(*col, a), r * 0.16))
        c.drawCircle(r * 1.5 * math.cos(ang), r * 1.5 * math.sin(ang), r * 0.17, P(C(*col, a)))
    c.drawCircle(0, 0, r, P(Shader=T.rad(-r * 0.3, -r * 0.3, r * 1.3, [C(255, 150, 170, a), C(*col, a)])))
    c.drawCircle(0, 0, r, S(C(80, 20, 40, a), 4))
    c.restore()


def bell_curve(c, x0, y0, w, h, flat=0.0, col=(255, 210, 90)):
    """IQ bell curve (mean 100, sd 15) that collapses into one spike at 100 as flat -> 1."""
    p = skia.Path()
    sd = lerp(15, 1.2, smooth(flat))
    for i in range(0, 201):
        iq = 40 + i * 0.6
        g = math.exp(-0.5 * ((iq - 100) / sd) ** 2)
        px = x0 + (iq - 40) / 120 * w
        py = y0 - h * g
        p.moveTo(px, py) if i == 0 else p.lineTo(px, py)
    fill = skia.Path(p)
    fill.lineTo(x0 + w, y0)
    fill.lineTo(x0, y0)
    fill.close()
    c.drawPath(fill, P(C(*col, 110)))
    c.drawPath(p, S(C(*col), 7))
    c.drawLine(x0, y0, x0 + w, y0, S(C(255, 255, 255), 4))
    f = skia.Font(T.FB, 36)
    for iq in (55, 70, 85, 100, 115, 130, 145):
        px = x0 + (iq - 40) / 120 * w
        c.drawLine(px, y0, px, y0 + 14, S(C(255, 255, 255), 3))
        tw = f.measureText(str(iq))
        c.drawString(str(iq), px - tw / 2, y0 + 56, f, P(C(255, 255, 255)))


def heart(c, x, y, r, col=(240, 70, 100), a=255):
    p = skia.Path()
    p.moveTo(x, y + r * 0.9)
    p.cubicTo(x - r * 1.6, y - r * 0.2, x - r * 0.6, y - r * 1.4, x, y - r * 0.5)
    p.cubicTo(x + r * 0.6, y - r * 1.4, x + r * 1.6, y - r * 0.2, x, y + r * 0.9)
    c.drawPath(p, P(C(*col, a)))
    c.drawPath(p, S(C(90, 20, 40, a), 3))


def qmark(c, x, y, size, a=255, col=(255, 236, 140)):
    f = skia.Font(T.FB, size)
    c.drawString("?", x - size * 0.25, y, f, S(C(25, 10, 30, a), size * 0.12))
    c.drawString("?", x - size * 0.25, y, f, P(C(*col, a)))


# =================================================================================== shot renderers
# signature: shot(t, k, t0, t1) where k = t - t0; returns (img, cam(z, cx, cy), [screen layers])
def cam_drift(t0, t1, z0=1.0, z1=1.06, c0=(960, 540), c1=None):
    c1 = c1 or c0
    return lambda t: E.catmull([(t0, z0, *c0), (t1, z1, *c1)], t)


def s_hook1(t, k, t0, t1):
    img = np.array(bg_bathroom())
    u = smooth(clamp((t - wt_or("hook1", "isn't", 3.0) + 0.3) / 0.8))
    pose = P_(eyes=0.3 + 0.9 * u, brows="up", mouth="O" if u > 0.3 else "smile", mouth_amt=lerp(0.5, 1.2, u), look=(0.6, -0.1), tilt=-3,
              hands=[(-20, 150), (60, -40)], bends=(1, 1), blink=blink_at(t, 1) and u < 0.1)
    s, c = E.surf()
    T.person(c, 640, 1250, 2.3, UNIQUE[1], dict(pose, look=(0.7, -0.1)), t)   # you (from behind the sink, facing the mirror)
    # the reflection: your face, then the average face
    mirror_face(c, UNIQUE[1] if u < 0.5 else AVG, t, 1380, 1250, 2.0, dict(pose, look=(-0.7, -0.1)))
    if 0 < u < 1:   # shimmer while it changes
        for i in range(8):
            T.sparkle(c, 1380 + 200 * math.cos(i + t * 3), 470 + 160 * math.sin(i * 1.7 + t * 2), 14, int(220 * math.sin(math.pi * u)))
    c.drawRect(skia.Rect(0, 1000, W, H), P(C(235, 235, 230)))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.08, (960, 540), (1100, 500))(t), []


def s_hook2(t, k, t0, t1):
    img = np.array(bg_dark((40, 30, 70), (90, 60, 120)))
    s, c = E.surf()
    names = ["MOM", "BOSS", "NEIGHBOR", "FRIEND", "YOU"]
    for i, look in enumerate(UNIQUE):
        x = 260 + i * 350
        tm = L("hook2") + 0.4 + i * 0.35
        u = smooth(clamp((t - tm) / 0.5))
        pose = P_(eyes=0.5 * u, brows="up", mouth="O" if u > 0.5 else "smile", mouth_amt=0.7, look=(0, 0), blink=blink_at(t, i))
        if u < 1:
            T.person(c, x, 1000, 1.25, look, pose, t)
        if u > 0:
            c.saveLayerAlpha(None, int(255 * u))
            T.person(c, x, 1000, 1.25, AVG, pose, t)
            c.restore()
        label(c, x, 1060, names[i], 40)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), []


def s_hook3(t, k, t0, t1):
    img = np.array(bg_dark())
    s, c = E.surf()
    globe(c, 960, 520, 330, t)
    r = random.Random(4)
    people = []
    for i in range(26):   # a ring of identical people around the globe
        a = i / 26 * 2 * math.pi
        x, y = 960 + 470 * math.cos(a), 560 + 300 * math.sin(a) + 120
        people.append((AVG, x, y + 200, 0.42, P_(blink=blink_at(t, i), tilt=4 * math.sin(t * 2 + i))))
    E.over(img, E.arr(s))
    img = lit(img, crowd_layer(t, people), rim=0.3)
    n = int(8_000_000_000 * smooth(clamp((t - wt_or("hook3", "eight", 1.0) + 0.3) / 0.9)))
    lay = [E.title_layer(t, [(f"{n:,}", 120, 170, E.GOLD, wt_or("hook3", "eight", 1.0) - 0.2)])]
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), lay


def s_hook4(t, k, t0, t1):
    img = np.array(bg_dark((30, 25, 55), (70, 50, 100)))
    s, c = E.surf()
    T.person(c, 520, 1000, 1.9, AVG, P_(blink=blink_at(t, 3), look=(0.4, 0)), t)
    stats = (("HEIGHT", 0.85, (90, 170, 240)), ("STRENGTH", 0.25, (240, 120, 90)), ("LOOKS", 0.95, (240, 120, 200)), ("IQ", 0.15, (120, 220, 140)))
    for i, (lab, v0, col) in enumerate(stats):
        u = snap(t, L("hook4") + 0.4 + i * 0.35, 12, 1.3)
        stat_bar(c, 1000, 330 + i * 150, 700, lab, lerp(v0, 0.5, clamp(u, 0, 1.2)), col)
    f = skia.Font(T.FB, 52)
    if t > L("hook4") + 1.8:
        a = int(255 * clamp((t - L("hook4") - 1.8) / 0.3))
        c.drawString("ALL EXACTLY AVERAGE", 1000, 950, f, P(C(255, 236, 140, a)))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.05, (960, 540), (1000, 540))(t), []


def s_hook5(t, k, t0, t1):
    img = np.array(bg_city())
    people = [(AVG, 200 + i * 230 + 30 * math.sin(i * 2), 900 + (i % 2) * 70, 0.9,
               P_(blink=blink_at(t, i), walk=t * 5 + i, look=(1 if i % 2 else -1, 0))) for i in range(8)]
    img = lit(img, crowd_layer(t, people))
    lay = [E.title_layer(t, [("FAIR?", 150, 300, E.GOLD, wt_or("hook5", "fair", 2.0)), ("OR CHAOS?", 120, 460, E.RED, wt_or("hook5", "apart", 3.0))])]
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), lay


def s_hook6(t, k, t0, t1):
    img = np.array(bg_dark((15, 5, 15), (60, 10, 25)))
    s, c = E.surf()
    pulse = 0.5 + 0.5 * math.sin(t * 3)
    virus(c, 960, 520, 120 + 10 * pulse, t, a=int(140 + 100 * pulse))
    c.drawCircle(960, 520, 420, P(Shader=T.rad(960, 520, 420, [C(255, 40, 60, 70), C(255, 40, 60, 0)])))
    E.over(img, E.arr(s))
    lay = [E.title_layer(t, [("STAY UNTIL THE END", 90, 900, E.WHITE, L("hook6") + 0.2)])]
    return img, cam_drift(t0, t1, 1.0, 1.1)(t), lay


# ---------------------------------------------------------------- 1. morning
def s_brain(t, k, t0, t1):
    img = np.array(bg_dark((20, 30, 60), (50, 60, 110)))
    s, c = E.surf()
    T.person(c, 760, 1500, 3.2, AVG, P_(eyes="open", look=(0.5, 0), blink=blink_at(t, 5)), t)
    glow = 0.6 + 0.4 * math.sin(t * 4)
    bx, by = 690, 330
    c.drawOval(skia.Rect(bx - 120, by - 70, bx + 120, by + 70), P(C(255, 120, 200, int(170 * glow)), MaskFilter=BLUR(20)))
    c.drawOval(skia.Rect(bx - 70, by - 35, bx + 70, by + 35), P(C(255, 200, 240, int(220 * glow))))
    label(c, 1400, 360, "FACE AREA", 60, (255, 210, 240))
    c.drawLine(1170, 340, bx + 80, by, S(C(255, 210, 240), 6))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), []


def s_faces(t, k, t0, t1):
    img = np.array(bg_dark((35, 25, 60), (80, 50, 100)))
    s, c = E.surf()
    n_show = int(60 * smooth(clamp((t - t0) / 2.5)))
    for i in range(n_show):
        x, y = 140 + (i % 12) * 150, 260 + (i // 12) * 170
        same = t > wt_or("morn2", "same", 4.5) + (i % 12) * 0.04
        look = AVG if same else UNIQUE[i % 5]
        c.save()
        c.translate(x, y)
        c.scale(0.42, 0.42)
        T.head(c, look, P_(blink=blink_at(t, i)), t)
        c.restore()
    E.over(img, E.arr(s))
    n = int(5000 * smooth(clamp((t - wt_or("morn2", "five", 1.6) + 0.2) / 0.8)))
    lay = [E.title_layer(t, [(f"{n:,} FACES", 110, 150, E.GOLD, wt_or("morn2", "five", 1.6) - 0.1)])]
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), lay


def s_kitchen(t, k, t0, t1):
    img = np.array(bg_room((250, 225, 180), (170, 120, 80)))
    s, c = E.surf()
    c.drawRoundRect(skia.Rect(300, 760, 1620, 820), 16, 16, P(C(200, 140, 90)))     # table top
    E.over(img, E.arr(s))
    people = [(AVG, 450 + i * 340, 1000, 1.25, P_(blink=blink_at(t, i), look=(0.2 * (i - 1.5), 0.4), mouth="smile", tilt=3 * math.sin(t + i),
                                                  hands=[(-10, 70 + 8 * math.sin(t * 5 + i)), (20, 120)], bends=(-1, -1))) for i in range(4)]
    img = lit(img, crowd_layer(t, people))
    s, c = E.surf()
    c.drawRect(skia.Rect(300, 800, 1620, 1150), P(Shader=T.lin((0, 800), (0, 1150), [C(190, 130, 85), C(140, 90, 55)])))   # table front
    c.drawRect(skia.Rect(300, 800, 1620, 1150), S(T.OUT, 6))
    for i in range(4):
        x = 450 + i * 340
        c.drawOval(skia.Rect(x - 70, 770, x + 70, 800), P(C(245, 245, 245)))      # bowls
        c.drawOval(skia.Rect(x - 70, 770, x + 70, 800), S(T.OUT, 3))
    t_q = wt_or("morn3", "brother", 3.0)
    for i in range(4):
        a = int(255 * clamp((t - t_q - i * 0.15) / 0.2))
        if a > 0:
            qmark(c, 450 + i * 340 + 70, 330 + 12 * math.sin(t * 4 + i), 110, a)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), [E.title_layer(t, [("WHICH ONE IS YOUR BROTHER?", 80, 150, E.WHITE, t_q)])]


def s_pickup(t, k, t0, t1):
    img = np.array(bg_city())
    people = []
    r = random.Random(7)
    for i in range(12):
        x = 120 + i * 150 + 40 * math.sin(t * 1.5 + i)
        y = 880 + r.uniform(0, 140)
        kid = i % 3 == 0
        people.append((AVG, x, y, 0.65 if kid else 0.95, P_(eyes=0.8, brows="up", mouth="O", mouth_amt=0.6, look=(math.sin(t * 2 + i), 0),
                                                           blink=blink_at(t, i))))
    img = lit(img, crowd_layer(t, people))
    s, c = E.surf()
    for i in range(5):
        qmark(c, 250 + i * 360, 520 + 20 * math.sin(t * 3 + i), 90, 220)
    t_h = wt_or("morn4", "couples", 3.0)
    if t > t_h:   # a couple holding hands in front
        u = smooth(clamp((t - t_h) / 0.5))
        T.person(c, 820, 1300, 1.3, AVG, P_(hands=[(-20, 150), (60, 110)], bends=(1, -1), look=(0.5, 0), mouth="smile"), t)
        T.person(c, 1100, 1300, 1.3, AVG, P_(hands=[(-60, 110), (20, 150)], bends=(1, -1), look=(-0.5, 0), mouth="smile"), t)
        heart(c, 960, 860, 40 * u)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.06, (960, 540), (960, 600))(t), []


def s_window(t, k, t0, t1):
    img = np.array(bg_city())
    s, c = E.surf()
    c.drawRect(skia.Rect(700, 260, 1500, 860), P(Shader=T.lin((700, 260), (1500, 860), [C(170, 200, 220, 220), C(120, 150, 175, 220)])))
    c.drawRect(skia.Rect(700, 260, 1500, 860), S(T.OUT, 8))
    wave = math.sin(t * 9) * 0.5
    T.person(c, 1150, 1080, 1.2, AVG, P_(look=(0.6, 0), mouth="smile", hands=[(-20, 150), (60 + 20 * wave, -60)], bends=(1, 1)), t)   # stranger
    c.save()
    c.clipRect(skia.Rect(700, 260, 1500, 860))
    T.person(c, 900, 1080, 1.2, AVG, P_(look=(-0.6, 0), mouth="smile", hands=[(-60 - 20 * wave, -60), (20, 150)], bends=(-1, 1)), t)   # reflection
    c.restore()
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.07)(t), []


# ---------------------------------------------------------------- 2. identity
def s_phone(t, k, t0, t1):
    img = np.array(bg_room((200, 210, 230), (120, 120, 140)))
    s, c = E.surf()
    i_now = int(clamp((t - t0) / 0.75, 0, 3.99))

    def scr(cc):
        cc.drawRect(skia.Rect(-98, -195, 98, 195), P(C(40, 50, 80)))
        cc.save()
        cc.translate(0, -30)
        cc.scale(0.5, 0.5)
        T.head(cc, AVG, P_(), t)
        cc.restore()
        check_mark(cc, 0, 120, 34)
    phone(c, 1350, 560, 1.4, scr)
    for i in range(4):
        x = 250 + i * 230
        T.person(c, x, 1050, 0.95, AVG, P_(look=(0.8, 0), mouth="O" if i == i_now else "smile", mouth_amt=0.6, blink=blink_at(t, i)), t)
        if i <= i_now:
            check_mark(c, x, 300, 36)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.title_layer(t, [("FACE UNLOCK: FOR ANYONE", 76, 150, E.WHITE, wt_or("id1", "face", 2.0))])]


def s_cctv(t, k, t0, t1):
    img = np.array(bg_dark((20, 25, 35), (40, 45, 60)))
    s, c = E.surf()
    c.drawRoundRect(skia.Rect(360, 140, 1560, 860), 30, 30, P(C(30, 30, 35)))
    c.drawRect(skia.Rect(400, 180, 1520, 820), P(C(60, 80, 70)))
    for i in range(5):   # line-up of identical suspects
        T.person(c, 520 + i * 220, 820, 0.95, AVG, P_(look=(0, 0.2), mouth="frown", blink=blink_at(t, i)), t)
        f = skia.Font(T.FB, 40)
        c.drawString(str(i + 1), 510 + i * 220, 790, f, P(C(255, 255, 255)))
    for y in range(180, 820, 6):   # scanlines
        c.drawLine(400, y, 1520, y, S(C(0, 0, 0, 40), 2))
    c.drawCircle(470, 230, 12, P(C(255, 40, 40, int(255 * (0.5 + 0.5 * math.sin(t * 6))))))
    f = skia.Font(T.FB, 34)
    c.drawString("REC", 492, 243, f, P(C(255, 255, 255)))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), [E.title_layer(t, [("WHO DID IT?", 100, 980, E.RED, wt_or("id2", "suspect", 2.5))])]


def s_twins_prints(t, k, t0, t1):
    img = np.array(bg_dark((25, 30, 55), (60, 70, 110)))
    s, c = E.surf()
    T.person(c, 420, 1000, 1.4, AVG, P_(look=(0.4, 0), blink=blink_at(t, 1)), t)
    T.person(c, 1500, 1000, 1.4, AVG, P_(look=(-0.4, 0), blink=blink_at(t, 2)), t)
    rev = smooth(clamp((t - wt_or("id3", "fingerprints", 2.5) + 0.4) / 0.8))
    if rev > 0:
        c.drawRoundRect(skia.Rect(640, 230, 940, 610), 30, 30, P(C(245, 240, 230)))
        c.drawRoundRect(skia.Rect(980, 230, 1280, 610), 30, 30, P(C(245, 240, 230)))
        fingerprint(c, 790, 420, 150, 11, reveal=rev)
        fingerprint(c, 1130, 420, 150, 12, reveal=rev)
    E.over(img, E.arr(s))
    lay = [E.title_layer(t, [("SAME GENES", 90, 150, E.WHITE, L("id3") + 0.6)])]
    if rev >= 1:
        lay.append(E.stamp_layer(t, "DIFFERENT PRINTS", wt_or("id3", "fingerprints", 2.5) + 0.5, 960, 800, 80, (230, 60, 60), -4))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), lay


def s_print_detail(t, k, t0, t1):
    img = np.array(bg_dark((30, 30, 50), (60, 60, 90)))
    s, c = E.surf()
    c.drawRoundRect(skia.Rect(560, 120, 1360, 960), 40, 40, P(C(245, 240, 230)))
    rev = smooth(clamp((t - t0) / 2.2))
    marks = [(0.8, 6), (2.6, 9), (4.2, 4)] if t > wt_or("id4", "details", 1.0) else None
    fingerprint(c, 960, 540, 380, 11, reveal=rev, mark=marks)
    E.over(img, E.arr(s))
    lay = [E.title_layer(t, [("STILL UNIQUE", 110, 1040, E.GOLD, wt_or("id4", "work", 5.0))])]
    return img, cam_drift(t0, t1, 1.0, 1.08)(t), lay


def s_scanners(t, k, t0, t1):
    img = np.array(bg_room((200, 205, 215), (110, 110, 125)))
    s, c = E.surf()
    items = [("FINGERPRINT", wt_or("id5", "fingerprint", 1.5)), ("VOICE", wt_or("id5", "voice", 2.3)), ("PASSWORD", wt_or("id5", "passwords", 3.0)),
             ("NAME TAG", wt_or("id5", "name", 4.0))]
    for i, (lab, at) in enumerate(items):
        u = snap(t, at, 8, 1.4)
        if u <= 0:
            continue
        x = 300 + i * 440
        c.save()
        c.translate(x, 470)
        c.scale(u, u)
        c.drawRoundRect(skia.Rect(-170, -200, 170, 200), 30, 30, P(C(40, 45, 70)))
        c.drawRoundRect(skia.Rect(-170, -200, 170, 200), 30, 30, S(C(120, 200, 255), 5))
        if i == 0:
            fingerprint(c, 0, -20, 110, 5, col=(120, 220, 255))
        elif i == 1:
            for j in range(15):
                hh = 20 + 90 * abs(math.sin(j * 1.3 + t * 8))
                c.drawLine(-140 + j * 20, -20 - hh / 2, -140 + j * 20, -20 + hh / 2, S(C(120, 220, 255), 9))
        elif i == 2:
            for j in range(6):
                c.drawCircle(-110 + j * 44, -20, 14, P(C(120, 220, 255)))
        else:
            c.drawRoundRect(skia.Rect(-130, -90, 130, 50), 14, 14, P(C(255, 255, 255)))
            c.drawRect(skia.Rect(-130, -90, 130, -50), P(C(220, 50, 60)))
            f = skia.Font(T.FB, 36)
            c.drawString("HELLO", -60, -58, f, P(C(255, 255, 255)))
            c.drawString("SAM", -40, 20, skia.Font(T.FB, 48), P(C(30, 30, 40)))
        label(c, 0, 160, lab, 38, (200, 235, 255), (20, 25, 45, 0))
        c.restore()
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), []


def s_creative(t, k, t0, t1):
    img = np.array(bg_city())
    looks = [avg(hair_col=(240, 60, 180), coat=(255, 210, 40)), avg(hair_col=(60, 200, 255), coat=(240, 90, 60), hat="bowler"),
             avg(hair_col=(120, 255, 120), coat=(140, 70, 220)), avg(hair_col=(255, 120, 40), coat=(40, 180, 160), hat="tophat"),
             avg(hair_col=(255, 255, 255), coat=(230, 60, 90), glasses=True), avg(hair_col=(250, 220, 60), coat=(60, 90, 220), hat="turban")]
    people = [(lk, 230 + i * 290, 950 + (i % 2) * 60, 1.0, P_(walk=t * 5 + i, look=(1, 0), blink=blink_at(t, i), mouth="smile"))
              for i, lk in enumerate(looks)]
    for j in range(len(people)):
        lk, x, y, sc, ps = people[j]
        people[j] = (lk, (x + 120 * (t - t0)) % (W + 300) - 150, y, sc, ps)
    img = lit(img, crowd_layer(t, people))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.title_layer(t, [("THIS IS ME", 120, 220, E.GOLD, wt_or("id6", "me", 4.0))])]


def s_fingertips(t, k, t0, t1):
    img = np.array(bg_dark((30, 40, 70), (70, 80, 120)))
    s, c = E.surf()
    T.person(c, 640, 1100, 1.6, AVG, P_(hands=[(-20, 150), (110, -30)], bends=(1, 1), look=(0.6, -0.2), mouth="smile"), t)
    hx, hy = T.hand_pos(640, 1100, 1.6, P_(hands=[(-20, 150), (110, -30)]), 1)
    c.drawRoundRect(skia.Rect(1100, 260, 1500, 760), 40, 40, P(C(40, 45, 70)))
    fingerprint(c, 1300, 480, 150, 21, col=(120, 220, 255))
    ok = t > wt_or("id7", "fingertips", 5.5)
    if ok:
        check_mark(c, 1300, 690, 46)
    E.over(img, E.arr(s))
    lay = [E.title_layer(t, [("FACE: WORTHLESS", 80, 160, E.WHITE, wt_or("id7", "nothing", 4.5)), ("FINGERTIPS: EVERYTHING", 80, 270, E.GOLD,
                                                                                                   wt_or("id7", "everything", 5.5))])]
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), lay


# ---------------------------------------------------------------- 3. love
def cafe(t, a_pose, b_pose, extra=None):
    img = np.array(bg_room((240, 200, 170), (140, 90, 60)))
    s, c = E.surf()
    c.drawCircle(960, 300, 160, P(Shader=T.rad(960, 300, 160, [C(255, 230, 160, 160), C(255, 230, 160, 0)])))
    T.person(c, 640, 1060, 1.5, AVG, a_pose, t)
    T.person(c, 1280, 1060, 1.5, avg(hair="pigtails"), b_pose, t)
    c.drawRect(skia.Rect(520, 820, 1400, 880), P(C(150, 95, 60)))
    c.drawRect(skia.Rect(520, 820, 1400, 880), S(T.OUT, 5))
    c.drawRect(skia.Rect(930, 880, 990, 1100), P(C(120, 75, 45)))
    for x in (800, 1120):
        c.drawRoundRect(skia.Rect(x - 40, 760, x + 40, 822), 10, 10, P(C(250, 250, 245)))
        c.drawRoundRect(skia.Rect(x - 40, 760, x + 40, 822), 10, 10, S(T.OUT, 3))
    if extra:
        extra(c)
    E.over(img, E.arr(s))
    return img


def s_love1(t, k, t0, t1):
    img = cafe(t, P_(look=(0.6, 0), mouth="smile", blink=blink_at(t, 1)), P_(look=(-0.6, 0), mouth="smile", blink=blink_at(t, 2)),
               lambda c: [qmark(c, 960, 330 + 15 * math.sin(t * 3), 140, 230)])
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), [E.title_layer(t, [("EQUALLY ATTRACTIVE", 90, 160, E.GOLD, wt_or("love1", "attractive", 2.5))])]


def s_love2(t, k, t0, t1):
    img = np.array(bg_dark((50, 25, 60), (110, 50, 90)))
    s, c = E.surf()
    x0, y0, w, h = 380, 860, 1160, 560
    c.drawLine(x0, y0, x0 + w, y0, S(C(255, 255, 255), 5))
    c.drawLine(x0, y0, x0, y0 - h, S(C(255, 255, 255), 5))
    f = skia.Font(T.FB, 40)
    c.drawString("TIME KNOWING SOMEONE", x0 + 330, y0 + 60, f, P(C(255, 255, 255)))
    u = smooth(clamp((t - t0) / 3.0))
    p = skia.Path()
    for i in range(0, int(100 * u) + 1):
        x = i / 100
        py = y0 - h * (0.85 * math.exp(-3.2 * x) + 0.12)
        p.moveTo(x0 + x * w, py) if i == 0 else p.lineTo(x0 + x * w, py)
    c.drawPath(p, S(C(255, 140, 180), 10))
    label(c, x0 + 760, y0 - h + 60, "HOW MUCH LOOKS MATTER", 40, (255, 200, 220))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), []


def s_love3(t, k, t0, t1):
    img = np.array(bg_dark((60, 25, 50), (120, 50, 80)))
    s, c = E.surf()
    x0, y0, w, h = 380, 860, 1160, 560
    c.drawLine(x0, y0, x0 + w, y0, S(C(255, 255, 255), 5))
    c.drawLine(x0, y0, x0, y0 - h, S(C(255, 255, 255), 5))
    f = skia.Font(T.FB, 40)
    c.drawString("TIME TOGETHER", x0 + 420, y0 + 60, f, P(C(255, 255, 255)))
    u = smooth(clamp((t - t0) / 3.0))
    p = skia.Path()
    for i in range(0, int(100 * u) + 1):
        x = i / 100
        py = y0 - h * (0.12 + 0.75 * (1 - math.exp(-3 * x)))
        p.moveTo(x0 + x * w, py) if i == 0 else p.lineTo(x0 + x * w, py)
    c.drawPath(p, S(C(255, 120, 150), 10))
    if u > 0.3:
        heart(c, x0 + w * u, y0 - h * (0.12 + 0.75 * (1 - math.exp(-3 * u))) - 50, 34)
    label(c, x0 + 160, y0 - h + 40, "LIKING", 44, (255, 200, 220))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), [E.title_layer(t, [("MERE EXPOSURE EFFECT", 86, 160, E.GOLD, wt_or("love3", "exposure", 1.2))])]


def s_love4(t, k, t0, t1):
    talk = abs(math.sin(t * 9))

    def ex(c):
        for i in range(3):
            ph = ((t - t0) * 0.6 + i / 3) % 1
            heart(c, 960 + 40 * math.sin(i * 2 + t), 700 - 360 * ph, 26, a=int(255 * math.sin(math.pi * ph)))
        c.drawRoundRect(skia.Rect(560, 260, 900, 380), 40, 40, P(C(255, 255, 255)))
        c.drawRoundRect(skia.Rect(560, 260, 900, 380), 40, 40, S(T.OUT, 4))
        for j in range(3):
            c.drawCircle(660 + j * 70, 320, 14, P(C(80, 80, 100)))
    img = cafe(t, P_(look=(0.6, 0), mouth="talk", talk=talk, blink=blink_at(t, 1)), P_(look=(-0.6, 0), mouth="smile", blink=blink_at(t, 2)), ex)
    return img, cam_drift(t0, t1, 1.0, 1.07)(t), [E.title_layer(t, [("THE CONVERSATION", 90, 160, E.GOLD, wt_or("love4", "conversation", 3.0))])]


def s_love5(t, k, t0, t1):
    img = np.array(bg_dark((60, 30, 70), (120, 60, 110)))
    s, c = E.surf()
    words = [("HUMOR", "humor"), ("KINDNESS", "kindness"), ("SHARED INTERESTS", "shared"), ("HOW THEY MAKE YOU FEEL", "feel")]
    for i, (lab, wd) in enumerate(words):
        at = wt_or("love5", wd, 0.5 + i * 0.7)
        u = snap(t, at, 7, 1.5)
        if u > 0:
            c.save()
            c.translate(960, 260 + i * 170)
            c.scale(u, u)
            label(c, 0, 0, lab, 64, (255, 236, 160), (40, 15, 50, 220))
            c.restore()
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.03)(t), []


def s_love6(t, k, t0, t1):
    img = np.array(bg_dark((40, 30, 70), (90, 60, 120)))
    s, c = E.surf()
    gone = smooth(clamp((t - wt_or("love6", "delete", 1.0) - 0.1) / 0.6))

    def scr(cc):
        cc.drawRect(skia.Rect(-98, -195, 98, 195), P(C(250, 245, 250)))
        if gone < 1:
            cc.saveLayerAlpha(None, int(255 * (1 - gone)))
            cc.drawRect(skia.Rect(-80, -175, 80, -10), P(C(200, 210, 230)))
            cc.save()
            cc.translate(0, -60)
            cc.scale(0.45, 0.45)
            T.head(cc, AVG, P_(), t)
            cc.restore()
            cc.restore()
        if gone > 0:
            cc.saveLayerAlpha(None, int(255 * gone))
            for j in range(7):
                cc.drawRoundRect(skia.Rect(-78, -170 + j * 34, 78 - (j % 3) * 30, -150 + j * 34), 8, 8, P(C(180, 170, 200)))
            cc.restore()
        cross_mark(cc, -55, 150, 30)
        heart(cc, 55, 150, 26)
    phone(c, 960, 520, 2.0, scr)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), [E.title_layer(t, [("JUST WORDS", 100, 1000, E.GOLD, wt_or("love6", "words", 3.0))])]


def s_love7(t, k, t0, t1):
    img = np.array(bg_city(night=True))
    s, c = E.surf()
    T.person(c, 820, 1000, 1.3, AVG, P_(look=(0.6, 0), mouth="smile", hands=[(-20, 150), (60, 110)], bends=(1, -1)), t)
    T.person(c, 1100, 1000, 1.3, avg(coat=(200, 120, 150)), P_(look=(-0.6, 0), mouth="smile", hands=[(-60, 110), (20, 150)], bends=(1, -1)), t)
    for i in range(5):
        ph = ((t - t0) * 0.4 + i / 5) % 1
        heart(c, 960 + 120 * math.sin(i * 2.3), 640 - 300 * ph, 22, a=int(230 * math.sin(math.pi * ph)))
    c.drawCircle(960, 760, 420, P(Shader=T.rad(960, 760, 420, [C(255, 210, 150, 90), C(255, 210, 150, 0)])))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.08, (960, 540), (960, 600))(t), []


# ---------------------------------------------------------------- 4. fame
def s_fame1(t, k, t0, t1):
    img = np.array(bg_dark((40, 20, 70), (100, 50, 130)))
    s, c = E.surf()
    likes = int(2_400_000 * smooth(clamp((t - t0) / 3)))

    def scr(cc):
        cc.drawRect(skia.Rect(-98, -195, 98, 195), P(Shader=T.lin((0, -195), (0, 195), [C(255, 150, 200), C(150, 100, 255)])))
        cc.save()
        cc.translate(0, -40)
        cc.scale(0.5, 0.5)
        T.head(cc, UNIQUE[0], P_(mouth="grin", eyes="squint"), t)
        cc.restore()
        heart(cc, -40, 140, 22, (255, 60, 100))
        cc.drawString(f"{likes / 1e6:.1f}M", -10, 150, skia.Font(T.FB, 34), P(C(255, 255, 255)))
    phone(c, 960, 520, 2.0, scr)
    for i in range(6):
        ph = ((t - t0) * 0.7 + i / 6) % 1
        heart(c, 1260 + 60 * math.sin(i), 860 - 600 * ph, 26, a=int(230 * (1 - ph)))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), []


def s_fame2(t, k, t0, t1):
    img = np.array(bg_city())
    s, c = E.surf()
    peel = smooth(clamp((t - wt_or("fame2", "disappear", 3.5) + 0.2) / 0.8))
    c.drawRect(skia.Rect(420, 120, 1500, 640), P(C(40, 40, 50)))
    c.drawRect(skia.Rect(440, 140, 1480 - 1040 * peel, 620), P(Shader=T.lin((440, 0), (1480, 0), [C(255, 190, 210), C(200, 160, 255)])))
    if peel < 0.6:
        c.save()
        c.clipRect(skia.Rect(440, 140, 1480 - 1040 * peel, 620))
        c.save()
        c.translate(780, 400)
        c.scale(1.1, 1.1)
        T.head(c, AVG, P_(eyes="squint", mouth="grin"), t)
        c.restore()
        c.drawString("BE BEAUTIFUL", 980, 420, skia.Font(T.FB, 64), S(C(60, 20, 70), 10))
        c.drawString("BE BEAUTIFUL", 980, 420, skia.Font(T.FB, 64), P(C(255, 255, 255)))
        c.restore()
    E.over(img, E.arr(s))
    people = [(AVG, 300 + i * 330, 1000, 1.0, P_(look=(0, -0.6), blink=blink_at(t, i), mouth="smile")) for i in range(5)]
    img = lit(img, crowd_layer(t, people))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.title_layer(t, [("NOTHING LEFT TO SELL", 80, 1000, E.GOLD, wt_or("fame2", "sell", 5.0))])]


def s_fame3(t, k, t0, t1):
    img = np.array(bg_dark((20, 15, 30), (50, 30, 60)))
    s, c = E.surf()
    c.drawPath(path([(860, 0), (1060, 0), (1360, 1080), (560, 1080)]), P(C(255, 240, 200, 50)))   # spotlight
    talk = abs(math.sin(t * 10))
    T.person(c, 960, 1000, 1.6, AVG, P_(mouth="talk", talk=talk, hands=[(-60, 40 + 20 * math.sin(t * 3)), (60, -40)], bends=(-1, 1), look=(0, 0.1)), t)
    c.drawLine(1010, 640, 1010, 1000, S(C(60, 60, 60), 8))   # mic stand
    c.drawCircle(1010, 630, 18, P(C(40, 40, 40)))
    E.over(img, E.arr(s))
    crowd = [(AVG, 200 + i * 220, 1240, 1.0, P_(eyes="closed" if (t * 2 + i) % 3 < 0.6 else "squint", mouth="laugh", look=(0, -0.5))) for i in range(8)]
    img = lit(img, crowd_layer(t, crowd), rim=0.25)
    return img, cam_drift(t0, t1, 1.0, 1.05, (960, 540), (960, 520))(t), [E.title_layer(t, [("VOICES · JOKES · IDEAS", 80, 150, E.GOLD,
                                                                                             wt_or("fame3", "voices", 2.0))])]


def s_fame4(t, k, t0, t1):
    img = np.array(bg_dark((30, 20, 60), (70, 50, 110)))
    s, c = E.surf()
    roles = [("COMEDIAN", "comedians"), ("STORYTELLER", "storytellers"), ("INVENTOR", "inventors")]
    for i, (lab, wd) in enumerate(roles):
        u = snap(t, wt_or("fame4", wd, 1.5 + i * 0.6), 8, 1.4)
        if u <= 0:
            continue
        x = 380 + i * 580
        c.drawCircle(x, 520, 230 * u, P(Shader=T.rad(x, 520, 230, [C(255, 220, 120, 120), C(255, 220, 120, 0)])))
        T.person(c, x, 900, 1.2 * u, AVG, P_(mouth="grin", eyes="squint"), t)
        label(c, x, 990, lab, 48, (255, 236, 160))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), [E.title_layer(t, [("INTERESTING IS THE NEW BEAUTIFUL", 70, 150, E.GOLD,
                                                                    wt_or("fame4", "beautiful", 5.0))])]


# ---------------------------------------------------------------- 5. sports
def s_wingspan(t, k, t0, t1):
    img = np.array(bg_dark((15, 50, 90), (30, 110, 160)))
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 0, W, H), P(C(255, 255, 255, 10)))
    sw = smooth(clamp((t - t0) / 1.2))
    pose = P_(hands=[lerp2((-20, 150), (-150, -10), sw), lerp2((20, 150), (150, -10), sw)], bends=(1, -1), look=(0, 0), mouth="smile")
    T.person(c, 960, 1000, 1.7, avg(coat=(30, 30, 40), hair="neat"), pose, t)
    if sw > 0.9:
        y = 1000 - 1.7 * 245
        c.drawLine(960 - 1.7 * 220, y + 70, 960 + 1.7 * 220, y + 70, S(C(255, 236, 140), 6))
        for xe in (960 - 1.7 * 220, 960 + 1.7 * 220):
            c.drawLine(xe, y + 50, xe, y + 90, S(C(255, 236, 140), 6))
        label(c, 960 - 1.7 * 220 - 10, y + 150, "ARM SPAN 6'7\"", 50, (255, 236, 140))
        c.drawLine(1400, 1000, 1400, 1000 - 1.7 * 460, S(C(140, 220, 255), 6))
        label(c, 1600, 1000 - 1.7 * 230, "HEIGHT 6'4\"", 50, (140, 220, 255))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), [E.title_layer(t, [("28 OLYMPIC MEDALS", 90, 150, E.GOLD, wt_or("sport1", "twenty", 8.0))])]


def s_bodies(t, k, t0, t1):
    img = np.array(bg_stadium())
    s, c = E.surf()
    kinds = [("BASKETBALL", 1.55, 0.95), ("SPRINTER", 1.25, 1.1), ("GYMNAST", 0.9, 0.9)]
    for i, (lab, h, wdt) in enumerate(kinds):
        x = 420 + i * 540
        c.save()
        c.translate(x, 1000)
        c.scale(wdt, h)
        T.person(c, 0, 0, 1.0, avg(coat=((230, 90, 60), (60, 150, 230), (220, 80, 180))[i]), P_(mouth="smile", blink=blink_at(t, i)), t)
        c.restore()
        label(c, x, 1050, lab, 46)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), []


def s_race(t, k, t0, t1):
    img = np.array(bg_stadium())
    run = clamp((t - t0 - 0.5) / 3.0)
    people = []
    for i in range(5):
        lane_y = 660 + i * 105
        x = lerp(120, 1440, smooth(run)) + 4 * noise1(t, 40 + i, 3) - (4 - i) * 70   # the finish line is diagonal in perspective
        people.append((AVG, x, lane_y, 0.42 + i * 0.07, P_(walk=t * 14 + i * 0.3, lean=8, look=(1, 0), mouth="grin")))
    img = lit(img, crowd_layer(t, people))
    s, c = E.surf()
    c.drawLine(1640, 560, 1360, 1080, S(C(255, 255, 255), 10))
    E.over(img, E.arr(s))
    lay = [E.stamp_layer(t, "TIE", wt_or("sport3", "tie", 4.0), 960, 300, 150, (240, 200, 60), -6)]
    return img, cam_drift(t0, t1, 1.0, 1.06, (900, 560), (1100, 560))(t), lay


def s_train(t, k, t0, t1):
    img = np.array(bg_room((210, 210, 225), (120, 120, 130)))
    s, c = E.surf()
    up = 0.5 + 0.5 * math.sin(t * 5)
    pose = P_(hands=[(-40, 150 - 110 * up), (40, 150 - 110 * up)], bends=(1, -1), mouth="frown", eyes="squint")
    T.person(c, 760, 1000, 1.5, avg(coat=(230, 80, 60)), pose, t)
    for sd in (-1, 1):   # dumbbell curls at the sides: nothing crosses the face
        hx, hy = T.hand_pos(760, 1000, 1.5, pose, sd)
        c.drawLine(hx - 45, hy, hx + 45, hy, S(C(60, 60, 70), 12))
        for x in (hx - 45, hx + 45):
            c.drawRoundRect(skia.Rect(x - 16, hy - 40, x + 16, hy + 40), 8, 8, P(C(40, 40, 50)))
    for i in range(3):   # sweat drops (ballistic)
        ph = ((t - t0) * 1.3 + i / 3) % 1
        c.drawCircle(830 + 30 * i, 560 + 300 * ph * ph, 10, P(C(140, 200, 255, int(255 * (1 - ph)))))
    E.over(img, E.arr(s))
    lay = [E.title_layer(t, [("TRAINING · STRATEGY · WILLPOWER", 70, 150, E.GOLD, wt_or("sport4", "training", 1.5))])]
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), lay


def s_honest(t, k, t0, t1):
    img = np.array(bg_stadium())
    s, c = E.surf()
    c.drawRect(skia.Rect(760, 900, 1160, 1080), P(C(250, 250, 250)))
    c.drawRect(skia.Rect(760, 900, 1160, 1080), S(T.OUT, 6))
    E.over(img, E.arr(s))
    people = [(AVG, 960, 910, 1.2, P_(hands=[(-60, -120), (60, -120)], bends=(-1, 1), mouth="grin", eyes="squint"))]
    img = lit(img, crowd_layer(t, people))
    s, c = E.surf()
    my = 910 - 1.2 * 190                                # gold medal on the chest, never over the face
    c.drawLine(930, my - 120, 960, my - 40, S(C(200, 40, 50), 8))
    c.drawLine(990, my - 120, 960, my - 40, S(C(200, 40, 50), 8))
    c.drawCircle(960, my, 40, P(C(250, 200, 60)))
    c.drawCircle(960, my, 40, S(T.OUT, 4))
    E.over(img, E.arr(s))
    lay = [E.title_layer(t, [("BORING?", 90, 150, E.WHITE, wt_or("sport5", "boring", 2.0)), ("OR MOST HONEST?", 90, 270, E.GOLD,
                                                                                               wt_or("sport5", "honest", 4.0))])]
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), lay


def s_archery(t, k, t0, t1):
    img = np.array(bg_stadium())
    s, c = E.surf()
    for i, col in enumerate(((255, 255, 255), (40, 40, 40), (60, 140, 230), (230, 60, 60), (250, 210, 60))):
        c.drawCircle(1500, 560, 220 - i * 42, P(C(*col)))
    fly = clamp((t - t0 - 1.0) / 0.5)
    ax = lerp(760, 1500, fly)
    ay = 560 - 40 * math.sin(math.pi * fly)
    c.drawLine(ax - 120, ay, ax, ay, S(C(90, 60, 30), 8))
    c.drawPath(path([(ax, ay), (ax - 26, ay - 12), (ax - 26, ay + 12)]), P(C(80, 80, 90)))
    E.over(img, E.arr(s))
    people = [(AVG, 520, 1000, 1.2, P_(hands=[(150, 10), (60, 25)], bends=(-1, 1), look=(1, 0), eyes="squint", mouth="smile"))]
    img = lit(img, crowd_layer(t, people))
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), [E.title_layer(t, [("THE SMARTEST PLAN WINS", 80, 150, E.GOLD, wt_or("sport6", "smartest", 4.0))])]


# ---------------------------------------------------------------- 6. jobs
def s_ricardo(t, k, t0, t1):
    img = np.array(bg_room((235, 220, 190), (120, 90, 60)))
    s, c = E.surf()
    c.drawRoundRect(skia.Rect(560, 200, 1360, 820), 20, 20, P(C(245, 235, 210)))
    c.drawRoundRect(skia.Rect(560, 200, 1360, 820), 20, 20, S(T.OUT, 6))
    c.drawLine(960, 220, 960, 800, S(C(180, 160, 130), 4))
    for j in range(9):
        c.drawLine(620, 280 + j * 56, 920, 280 + j * 56, S(C(120, 110, 100, 150), 4))
        c.drawLine(1000, 280 + j * 56, 1300 - (j % 3) * 60, 280 + j * 56, S(C(120, 110, 100, 150), 4))
    q = (t - t0) * 2
    c.drawLine(1300 + 20 * math.sin(q), 520, 1460, 360, S(C(240, 240, 235), 10))   # quill
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.stamp_layer(t, "1817", wt_or("job1", "eighteen", 1.0), 960, 960, 120, (150, 60, 40), -4)]


def s_trade(t, k, t0, t1):
    img = np.array(bg_room((225, 235, 210), (110, 130, 90)))
    s, c = E.surf()
    T.person(c, 520, 1000, 1.4, UNIQUE[0], P_(look=(0.6, 0), mouth="smile", hands=[(-20, 150), (90, 40)], bends=(1, -1)), t)
    T.person(c, 1400, 1000, 1.4, UNIQUE[1], P_(look=(-0.6, 0), mouth="smile", hands=[(-90, 40), (20, 150)], bends=(1, -1)), t)
    u = (math.sin((t - t0) * 2.0) + 1) / 2   # goods swap hands
    bx = lerp(700, 1220, u)
    c.drawOval(skia.Rect(bx - 60, 600, bx + 60, 660), P(C(210, 150, 80)))   # bread
    c.drawOval(skia.Rect(bx - 60, 600, bx + 60, 660), S(T.OUT, 4))
    hx = lerp(1220, 700, u)
    c.drawLine(hx - 50, 520, hx + 50, 560, S(C(120, 120, 130), 14))   # wrench
    c.drawCircle(hx + 55, 562, 20, S(C(120, 120, 130), 10))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.title_layer(t, [("COMPARATIVE ADVANTAGE", 84, 150, E.GOLD, wt_or("job2", "comparative", 0.6))])]


def s_jobs_diff(t, k, t0, t1):
    img = np.array(bg_city())
    s, c = E.surf()
    roles = [("NUMBERS", "numbers"), ("BUILDING", "building"), ("HELPING", "helping")]
    for i, (lab, wd) in enumerate(roles):
        u = snap(t, wt_or("job3", wd, 2 + i), 8, 1.4)
        if u <= 0:
            continue
        x = 400 + i * 560
        T.person(c, x, 1000, 1.2 * u, UNIQUE[i + 2], P_(mouth="grin", eyes="squint"), t)
        label(c, x, 1050, lab, 48, (255, 236, 160))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), []


def s_same_jobs(t, k, t0, t1):
    img = np.array(bg_room((215, 220, 235), (110, 115, 130)))
    s, c = E.surf()
    E.over(img, E.arr(s))
    people = [(AVG, 260 + i * 200, 1000, 0.95, P_(look=(0.2, -0.3), eyes=0.6, brows="up", mouth="O", mouth_amt=0.5, blink=blink_at(t, i)))
              for i in range(8)]
    img = lit(img, crowd_layer(t, people))
    s, c = E.surf()
    for i in range(4):
        qmark(c, 360 + i * 400, 360 + 15 * math.sin(t * 3 + i), 110, 220)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.title_layer(t, [("THE SAME JOBS?", 110, 150, E.RED, wt_or("job4", "jobs", 6.0))])]


def s_queues(t, k, t0, t1):
    img = np.array(bg_city(night=wt_or("job5", "sewers", 3.0) < t))
    s, c = E.surf()
    door(c, 160, 420, 260, 400, (90, 140, 200), "DOCTOR")
    door(c, 760, 420, 260, 400, (160, 90, 200), "GAME DESIGNER")
    door(c, 1460, 420, 260, 400, (110, 100, 80), "SEWERS 3 AM")
    E.over(img, E.arr(s))
    people = []
    for q, x0 in enumerate((290, 890)):
        for i in range(7):
            people.append((AVG, x0 + 70 * math.sin(i) + 0 * q, 860 + i * 34, 0.6 + i * 0.03, P_(look=(0, -0.4), blink=blink_at(t, i + q * 7))))
    img = lit(img, crowd_layer(t, people))
    s, c = E.surf()
    if t > wt_or("job5", "nobody", 2.5):
        c.drawString("0", 1560, 940, skia.Font(T.FB, 120), P(C(255, 236, 140)))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), []


def s_salary(t, k, t0, t1):
    img = np.array(bg_dark((25, 40, 40), (50, 90, 80)))
    s, c = E.surf()
    swap = smooth(clamp((t - wt_or("job6", "more", 3.0) + 0.3) / 1.2))
    for i, (lab, hi, lo) in enumerate((("DREAM JOB", 0.85, 0.35), ("UNWANTED JOB", 0.3, 0.9))):
        x = 620 + i * 520
        hgt = 600 * lerp(hi, lo, swap)
        c.drawRoundRect(skia.Rect(x - 120, 900 - hgt, x + 120, 900), 16, 16, P(Shader=T.lin((0, 900 - hgt), (0, 900), [C(140, 255, 160), C(40, 160, 80)])))
        c.drawRoundRect(skia.Rect(x - 120, 900 - hgt, x + 120, 900), 16, 16, S(T.OUT, 5))
        label(c, x, 980, lab, 48)
        c.drawString("$", x - 26, 900 - hgt - 30, skia.Font(T.FB, 80), P(C(255, 236, 140)))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), []


def s_effort(t, k, t0, t1):
    img = np.array(bg_dark((40, 30, 60), (90, 60, 110)))
    s, c = E.surf()
    words = [("CHOICES", "choices"), ("EFFORT", "effort"), ("WHAT YOU CARE ABOUT", "care")]
    for i, (lab, wd) in enumerate(words):
        u = snap(t, wt_or("job7", wd, 3 + i), 7, 1.5)
        if u > 0:
            c.save()
            c.translate(960, 380 + i * 180)
            c.scale(u, u)
            label(c, 0, 0, lab, 76, (255, 236, 160), (40, 15, 50, 220))
            c.restore()
    E.over(img, E.arr(s))
    lay = [E.title_layer(t, [("NOT TALENT", 100, 170, E.RED, wt_or("job7", "talent", 1.8))])]
    return img, cam_drift(t0, t1, 1.0, 1.03)(t), lay


def s_owns(t, k, t0, t1):
    img = np.array(bg_city())
    s, c = E.surf()
    for i in range(6):   # stacks of coins growing for one person
        hgt = (i + 1) * 16 * smooth(clamp((t - t0 - i * 0.3) / 0.5))
        c.drawRoundRect(skia.Rect(1250, 900 - i * 34 - hgt, 1450, 930 - i * 34), 12, 12, P(C(250, 200, 60)))
        c.drawRoundRect(skia.Rect(1250, 900 - i * 34 - hgt, 1450, 930 - i * 34), 12, 12, S(T.OUT, 3))
    E.over(img, E.arr(s))
    people = [(AVG, 700, 1000, 1.3, P_(look=(0.8, 0), mouth="grin", eyes="squint")), (AVG, 360, 1000, 1.1, P_(look=(0.8, 0), mouth="frown"))]
    img = lit(img, crowd_layer(t, people))
    lay = [E.title_layer(t, [("MORE EQUAL?", 90, 150, E.WHITE, wt_or("job8", "equal", 2.0)), ("OR NEW WAYS TO COMPETE?", 80, 270, E.GOLD,
                                                                                                  wt_or("job8", "compete", 4.5))])]
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), lay


# ---------------------------------------------------------------- 7. school
def s_bell(t, k, t0, t1, collapse_from=None):
    img = np.array(bg_dark((20, 35, 70), (40, 70, 120)))
    s, c = E.surf()
    flat = 0.0 if collapse_from is None else clamp((t - collapse_from) / 1.2)
    grow = smooth(clamp((t - t0) / 1.0))
    c.save()
    c.translate(0, 880 * (1 - grow))
    bell_curve(c, 300, 860, 1320, 600, flat)
    c.restore()
    E.over(img, E.arr(s))
    lay = [E.title_layer(t, [("IQ", 120, 170, E.GOLD, t0 + 0.2)])]
    return img, cam_drift(t0, t1, 1.0, 1.03)(t), lay


def s_sch1(t, k, t0, t1):
    return s_bell(t, k, t0, t1)


def s_sch2(t, k, t0, t1):
    return s_bell(t, k, t0 - 2, t1, collapse_from=wt_or("sch2", "collapses", 3.5) - 0.2)


def classroom(t, extra=None, student_pose=None):
    img = np.array(bg_room((215, 230, 210), (150, 120, 90)))
    s, c = E.surf()
    c.drawRect(skia.Rect(500, 100, 1420, 420), P(C(40, 70, 55)))
    c.drawRect(skia.Rect(500, 100, 1420, 420), S(C(120, 80, 50), 14))
    if extra:
        extra(c)
    E.over(img, E.arr(s))
    for row in range(2):   # back row first: its desks sit behind the front row's students
        feet, sc = 900 + row * 150, 0.8 + row * 0.12
        people = [(AVG, 330 + i * 315 + row * 60, feet, sc,
                   student_pose(i, row) if student_pose else P_(look=(0, -0.5), blink=blink_at(t, i + row * 5))) for i in range(5)]
        img = lit(img, crowd_layer(t, people))
        s, c = E.surf()
        for i in range(5):
            x = 330 + i * 315 + row * 60
            top = feet - 120 * sc                          # desk top at the waist: covers legs, never faces
            c.drawRect(skia.Rect(x - 120, top, x + 120, top + 26), P(C(200, 150, 95)))
            c.drawRect(skia.Rect(x - 108, top + 26, x + 108, feet + 10), P(C(160, 110, 70)))
            c.drawRect(skia.Rect(x - 120, top, x + 120, top + 26), S(T.OUT, 4))
            c.drawRect(skia.Rect(x - 108, top + 26, x + 108, feet + 10), S(T.OUT, 4))
        E.over(img, E.arr(s))
    return img


def s_sch3(t, k, t0, t1):
    img = classroom(t, lambda c: c.drawString("IQ = 100", 760, 300, skia.Font(T.FB, 90), P(C(240, 240, 230))))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), []


def s_sch4(t, k, t0, t1):
    def ex(c):
        sp = (t - t0) * 300
        for i in range(4):
            c.drawLine(560 + (sp + i * 220) % 840, 220, 560 + (sp + i * 220) % 840 + 120, 220, S(C(240, 240, 230), 8))
        c.drawString("STUDY", 820, 340, skia.Font(T.FB, 80), P(C(240, 240, 230)))
    img = classroom(t, ex)
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.title_layer(t, [("HOW HARD YOU STUDY", 90, 1000, E.GOLD, wt_or("sch4", "study", 5.0))])]


def s_sch5(t, k, t0, t1):
    img = np.array(bg_room((220, 225, 215), (140, 120, 95)))
    s, c = E.surf()
    T.person(c, 660, 1000, 1.6, AVG, P_(eyes="sad", brows="sad", mouth="frown", look=(0.5, 0.5), hands=[(30, 40), (80, 60)], bends=(-1, -1)), t)
    c.drawRect(skia.Rect(900, 420, 1300, 900), P(C(250, 250, 245)))
    c.drawRect(skia.Rect(900, 420, 1300, 900), S(T.OUT, 5))
    for j in range(7):
        c.drawLine(940, 520 + j * 50, 1260, 520 + j * 50, S(C(160, 160, 170), 4))
    if t > wt_or("sch5", "fail", 2.0):
        c.drawString("F", 1150, 520, skia.Font(T.FB, 150), P(C(220, 40, 50)))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), [E.title_layer(t, [("NO EXCUSES", 100, 160, E.RED, wt_or("sch5", "brain", 4.0))])]


def s_sch6(t, k, t0, t1):
    img = np.array(bg_dark((30, 40, 60), (60, 90, 110)))
    s, c = E.surf()
    words = [("CREATIVITY", "creativity"), ("PATIENCE", "patience"), ("TEAMWORK", "teamwork")]
    for i, (lab, wd) in enumerate(words):
        u = snap(t, wt_or("sch6", wd, 4 + i * 0.5), 7, 1.5)
        if u > 0:
            c.save()
            c.translate(420 + i * 540, 560)
            c.scale(u, u)
            label(c, 0, 0, lab, 64, (200, 255, 210), (20, 50, 40, 220))
            c.restore()
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.03)(t), [E.title_layer(t, [("NO MORE RANKINGS", 90, 200, E.GOLD, wt_or("sch6", "ranking", 1.5))])]


# ---------------------------------------------------------------- 8. disease
def s_dis1(t, k, t0, t1):
    img = np.array(bg_dark((20, 10, 25), (60, 20, 40)))
    s, c = E.surf()
    turn = smooth(clamp((t - wt_or("dis1", "bananas", 3.0) + 0.2) / 0.5))
    if turn < 1:
        virus(c, 960, 520, 140, t, a=int(255 * (1 - turn)))
    if turn > 0:
        banana(c, 960, 540, 3.5 * turn, -20)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.title_layer(t, [("BIOLOGICAL", 110, 170, E.RED, wt_or("dis1", "biological", 1.5))])]


def banana_farm(t, sick_front=None):
    img = np.array(bg_field("banana"))
    s, c = E.surf()
    for row in range(3):
        for i in range(9):
            x = 100 + i * 220 + row * 60
            sick = 0.0
            if sick_front is not None:
                sick = clamp((sick_front - x) / 300)
            plant(c, x, 640 + row * 150, 0.8 + row * 0.15, t, sick)
    E.over(img, E.arr(s))
    return img


def s_dis2(t, k, t0, t1):
    img = banana_farm(t)
    lay = [E.title_layer(t, [("GROS MICHEL", 110, 170, E.GOLD, wt_or("dis2", "gros", 2.0))])]
    if t > wt_or("dis2", "clone", 4.0):
        lay.append(E.stamp_layer(t, "ALL CLONES", wt_or("dis2", "clone", 4.0), 960, 330, 90, (220, 40, 50), -5))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), lay


def s_dis3(t, k, t0, t1):
    front = lerp(-200, 2400, smooth(clamp((t - wt_or("dis3", "fungus", 0.8)) / 6.0)))
    img = banana_farm(t, front)
    lay = [E.title_layer(t, [("PANAMA DISEASE", 100, 170, E.RED, wt_or("dis3", "panama", 1.0))])]
    if t > wt_or("dis3", "wiped", 7.0):
        lay.append(E.stamp_layer(t, "WIPED OUT", wt_or("dis3", "wiped", 7.0), 960, 330, 100, (220, 40, 50), -5))
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), lay


def potato_field(t, sick_front=None):
    img = np.array(bg_field("potato"))
    s, c = E.surf()
    for row in range(3):
        for i in range(10):
            x = 90 + i * 200 + row * 50
            sick = clamp((sick_front - x) / 300) if sick_front is not None else 0.0
            plant(c, x, 680 + row * 140, 0.9 + row * 0.12, t, sick, kind="potato")
    E.over(img, E.arr(s))
    return img


def s_dis4(t, k, t0, t1):
    img = potato_field(t)
    lay = [E.title_layer(t, [("IRELAND, 1840s", 100, 170, E.WHITE, wt_or("dis4", "ireland", 1.2))]),
           E.stamp_layer(t, "THE LUMPER: CLONES", wt_or("dis4", "lumber", 5.0), 960, 330, 80, (150, 60, 40), -4)]
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), lay


def s_dis5(t, k, t0, t1):
    """Told plainly: no slams, no jokes. Blight spreads; one number."""
    front = lerp(-200, 2400, smooth(clamp((t - t0) / 4.0)))
    img = potato_field(t, front)
    lum = img[..., :3].mean(axis=2, keepdims=True)
    img[..., :3] = img[..., :3] * 0.6 + lum * 0.4
    lay = [E.title_layer(t, [("~1,000,000 DEATHS", 90, 170, [C(235, 235, 240), C(190, 195, 205)], wt_or("dis5", "million", 4.5))])]
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), lay


def s_dis6(t, k, t0, t1):
    img = np.array(bg_field("banana"))
    s, c = E.surf()
    c.drawRect(skia.Rect(0, 600, W, H), P(C(200, 180, 110)))     # savanna
    for i in range(3):
        cheetah(c, 260 + i * 590 + 40 * (t - t0), 900 + (i % 2) * 50, 1.25, t + i * 0.37, 1)
    E.over(img, E.arr(s))
    lay = [E.title_layer(t, [("NEARLY IDENTICAL GENES", 86, 170, E.GOLD, wt_or("dis6", "grafts", 3.0))])]
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), lay


def s_dis7(t, k, t0, t1):
    img = np.array(bg_dark((20, 35, 50), (40, 80, 90)))
    people = [(UNIQUE[i % 5], 220 + i * 210, 980, 0.95, P_(blink=blink_at(t, i), mouth="smile")) for i in range(8)]
    img = lit(img, crowd_layer(t, people))
    s, c = E.surf()
    for i in range(8):   # viruses fly in; most bounce off a shield
        ph = ((t - t0) * 0.6 + i / 8) % 1
        x = 220 + i * 210
        y = lerp(60, 420, min(1, ph * 1.6))
        if ph > 0.62:
            y = 420 - 600 * (ph - 0.62) ** 1.2
        virus(c, x, y, 26, t + i, a=int(255 * (1 - ph * 0.6)))
    c.drawPath(path([(140, 470), (1780, 470)], close=False), S(C(140, 230, 255, 160), 10))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), [E.title_layer(t, [("DIFFERENCE = SHIELD", 100, 170, E.GOLD, wt_or("dis7", "shield", 2.0))])]


def s_dis8(t, k, t0, t1):
    img = np.array(bg_dark((20, 10, 20), (70, 20, 30)))
    sick = smooth(clamp((t - wt_or("dis8", "disease", 3.0)) / 1.5))
    people = [(avg(skin=(lerp(222, 170, sick), lerp(178, 200, sick), lerp(142, 120, sick))), 220 + i * 210, 980, 0.95,
               P_(eyes="sad" if sick > 0.5 else "open", brows="sad" if sick > 0.5 else "flat", mouth="frown" if sick > 0.5 else "smile",
                  blink=blink_at(t, i))) for i in range(8)]
    img = lit(img, crowd_layer(t, people), rim=0.2)
    s, c = E.surf()
    for i in range(8):
        ph = clamp((t - t0) * 0.5 + i * 0.05)
        virus(c, 220 + i * 210, lerp(80, 560, smooth(ph)), 26, t + i)
    E.over(img, E.arr(s))
    lay = [E.title_layer(t, [("8 BILLION · ONE WEAKNESS", 80, 170, E.RED, wt_or("dis8", "eight", 4.0))])]
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), lay


def s_dis9(t, k, t0, t1):
    img = np.array(bg_room((240, 225, 190), (170, 130, 90)))
    s, c = E.surf()
    c.drawOval(skia.Rect(640, 680, 1280, 790), P(C(200, 140, 90)))
    c.drawOval(skia.Rect(640, 680, 1280, 790), S(T.OUT, 5))
    for i in range(5):                                   # a bunch: five fingers fanned from one crown
        c.save()
        c.translate(960, 560)
        c.rotate(-40 + i * 20)
        banana(c, 0, 140, 2.0, 90)
        c.restore()
    c.drawRoundRect(skia.Rect(930, 500, 990, 580), 12, 12, P(C(110, 120, 50)))
    c.drawRoundRect(skia.Rect(930, 500, 990, 580), 12, 12, S(T.OUT, 4))
    E.over(img, E.arr(s))
    lay = [E.title_layer(t, [("THE CAVENDISH", 100, 170, E.GOLD, wt_or("dis9", "cavendish", 2.5)),
                             ("ALSO A CLONE", 80, 290, E.RED, wt_or("dis9", "clone", 5.0))])]
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), lay


# ---------------------------------------------------------------- 9. drift
def s_drift1(t, k, t0, t1):
    img = np.array(bg_dark((40, 30, 70), (90, 70, 130)))
    people = [(AVG, 760, 1000, 1.4, P_(blink=blink_at(t, 1), look=(0.4, 0))), (AVG, 1160, 1000, 1.4, P_(blink=blink_at(t, 2), look=(-0.4, 0)))]
    img = lit(img, crowd_layer(t, people))
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), [E.title_layer(t, [("BUT...", 130, 200, E.GOLD, t0 + 0.3)])]


def s_drift2(t, k, t0, t1):
    img = np.array(bg_dark((30, 30, 60), (70, 70, 120)))
    s, c = E.surf()
    age = smooth(clamp((t - wt_or("drift2", "middle", 4.0) + 0.5) / 1.5))
    for i, sx in enumerate((620, 1300)):
        sc = lerp(0.8, 1.3, age)
        look = AVG if i == 0 else avg(coat=lerp2((110, 130, 165), (160, 90, 70), age), hair_col=lerp2((70, 50, 38), (150, 150, 155), age))
        T.person(c, sx, 1000, sc, look, P_(blink=blink_at(t, i), mouth="smile"), t)
    label(c, 960, 160, "AGE 3" if age < 0.5 else "AGE 50", 70, (255, 236, 160))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), []


def s_drift3(t, k, t0, t1):
    img = np.array(bg_dark((25, 35, 60), (60, 80, 120)))
    s, c = E.surf()
    for j in range(40):   # a DNA strand, with marks switching on
        y = 140 + j * 20
        a = j * 0.45 + t * 1.2
        x1, x2 = 960 + 200 * math.sin(a), 960 - 200 * math.sin(a)
        c.drawLine(x1, y, x2, y, S(C(150, 200, 255, 120), 4))
        c.drawCircle(x1, y, 10, P(C(120, 200, 255)))
        c.drawCircle(x2, y, 10, P(C(255, 150, 200)))
        if (j * 7) % 11 < 4 and t > t0 + 0.5 + (j % 9) * 0.25:
            c.drawCircle(x1, y, 18, S(C(255, 236, 140), 4))
    words = [("FOOD", "food"), ("PLACES", "places"), ("STRESS", "stress"), ("HABITS", "habits")]
    for i, (lab, wd) in enumerate(words):
        if t > wt_or("drift3", wd, 0.5 + i):
            label(c, 330 if i % 2 == 0 else 1590, 330 + (i // 2) * 300, lab, 56, (255, 236, 160))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), []


def s_drift4(t, k, t0, t1):
    img = np.array(bg_room((225, 225, 235), (130, 120, 120)))
    yrs = smooth(clamp((t - wt_or("drift4", "ten", 5.0) + 0.3) / 1.5))
    run = P_(walk=t * 9, lean=6, mouth="grin", look=(1, 0))
    people = [(avg(coat=(230, 80, 60), skin=(222, 178, 142)), 620, 1000, lerp(1.25, 1.2, yrs), run),
              (avg(coat=(90, 100, 130)), 1300, 1000, lerp(1.25, 1.3, yrs), P_(mouth="smile", look=(-0.6, 0.4), squash=0.12 * yrs))]
    img = lit(img, crowd_layer(t, people))
    s, c = E.surf()
    if t > wt_or("drift4", "piano", 2.0):
        u = snap(t, wt_or("drift4", "piano", 2.0), 7, 1.4)
        c.save()
        c.translate(620, 330)
        c.scale(u, u)
        for j in range(8):
            c.drawRect(skia.Rect(-184 + j * 46, -40, -142 + j * 46, 40), P(C(250, 250, 250)))
            c.drawRect(skia.Rect(-184 + j * 46, -40, -142 + j * 46, 40), S(T.OUT, 3))
            if j % 7 not in (2, 6):
                c.drawRect(skia.Rect(-156 + j * 46, -40, -132 + j * 46, 6), P(C(30, 30, 35)))
        c.restore()
    if t > wt_or("drift4", "code", 3.0):
        u = snap(t, wt_or("drift4", "code", 3.0), 7, 1.4)
        c.save()
        c.translate(1300, 330)
        c.scale(u, u)
        c.drawRoundRect(skia.Rect(-170, -70, 170, 70), 12, 12, P(C(30, 30, 40)))
        c.drawRoundRect(skia.Rect(-170, -70, 170, 70), 12, 12, S(C(200, 200, 210), 5))
        for j in range(4):
            c.drawLine(-140, -40 + j * 26, -140 + 80 + j * 50, -40 + j * 26, S(C(120, 255, 160), 7))
        c.restore()
    E.over(img, E.arr(s))
    lay = [E.title_layer(t, [("+10 YEARS", 100, 170, E.GOLD, wt_or("drift4", "ten", 5.0))])]
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), lay


def s_drift5(t, k, t0, t1):
    img = np.array(bg_city())
    people = [(UNIQUE[i % 5] if i % 2 else AVG, 180 + i * 200, 980, 0.95, P_(walk=t * 5 + i, look=(1, 0), blink=blink_at(t, i))) for i in range(9)]
    img = lit(img, crowd_layer(t, people))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.title_layer(t, [("LIFE MAKES US DIFFERENT", 90, 170, E.GOLD, wt_or("drift5", "different", 3.0))])]


def s_drift6(t, k, t0, t1):
    img = np.array(bg_city())
    u = smooth(clamp((t - t0) / 4))
    people = []
    for i in range(10):
        look = UNIQUE[i % 5] if (i / 10) < u else AVG
        people.append((look, 140 + i * 180, 980 + (i % 2) * 40, 0.9, P_(mouth="smile", blink=blink_at(t, i))))
    img = lit(img, crowd_layer(t, people))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), [E.title_layer(t, [("VARIETY COMES BACK", 90, 170, E.GOLD, wt_or("drift6", "variety", 4.0))])]


# ---------------------------------------------------------------- 10. ending
def s_end1(t, k, t0, t1):
    img, cam, lay = s_hook4(t, k, t0, t1)
    return img, cam, []


def s_end2(t, k, t0, t1):
    img = np.array(bg_dark((30, 25, 55), (70, 50, 100)))
    s, c = E.surf()
    items = [("FACES", "faces"), ("FINGERPRINTS", "fingerprints"), ("LOVE", "love"), ("SPORTS", "sports")]
    for i, (lab, wd) in enumerate(items):
        u = snap(t, wt_or("end2", wd, 1 + i * 1.5), 7, 1.4)
        if u > 0:
            x = 300 + i * 440
            c.save()
            c.translate(x, 520)
            c.scale(u, u)
            c.drawCircle(0, 0, 150, P(C(50, 40, 80)))
            c.drawCircle(0, 0, 150, S(C(255, 236, 140), 6))
            if i == 0:
                c.save()
                c.scale(0.5, 0.5)
                T.head(c, AVG, P_(), t)
                c.restore()
            elif i == 1:
                fingerprint(c, 0, 0, 100, 3, col=(255, 236, 160))
            elif i == 2:
                heart(c, 0, 0, 70)
            else:
                c.drawCircle(0, 0, 70, P(C(250, 200, 60)))
            c.restore()
            label(c, x, 760, lab, 46)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.03)(t), []


def s_end3(t, k, t0, t1):
    img = np.array(bg_dark((25, 20, 45), (60, 40, 80)))
    s, c = E.surf()
    if t > wt_or("end3", "effort", 1.5):
        label(c, 600, 520, "EFFORT > TALENT", 70, (255, 236, 160))
    if t > wt_or("end3", "disease", 3.5):
        virus(c, 1400, 480, 90, t)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), []


def s_end4(t, k, t0, t1):
    img = np.array(bg_room((220, 215, 230), (120, 110, 130)))
    s, c = E.surf()

    def scr(cc):
        cc.drawRect(skia.Rect(-98, -195, 98, 195), P(C(250, 240, 245)))
        for j in range(4):
            cc.drawRoundRect(skia.Rect(-80, -170 + j * 90, 80, -100 + j * 90), 10, 10, P(C(220, 200, 230)))
            cc.drawString(f"{(97 - j * 13)}", -30, -125 + j * 90, skia.Font(T.FB, 34), P(C(120, 60, 160)))
    T.person(c, 760, 1000, 1.6, AVG, P_(eyes="sad", brows="sad", mouth="frown", look=(0.6, 0.2), hands=[(-20, 150), (90, -20)], bends=(1, 1)), t)
    phone(c, 1200, 520, 1.3, scr)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.title_layer(t, [("COMPARING", 100, 170, E.WHITE, wt_or("end4", "comparing", 3.5))])]


def s_end5(t, k, t0, t1):
    img = np.array(bg_bathroom())
    s, c = E.surf()
    pose = P_(eyes="squint", brows="smug", mouth="grin", mouth_amt=1.15, look=(0.6, 0), tilt=4)
    T.person(c, 640, 1250, 2.3, AVG, pose, t)
    mirror_face(c, AVG, t, 1380, 1250, 2.0, dict(pose, look=(-0.6, 0)))
    for i in range(6):   # sparkles run along the mirror frame (perimeter), never over the reflected face
        u = ((t * 0.12) + i / 6) % 1
        per = 2 * (590 + 630)
        d = u * per
        if d < 590:
            px, py = 1085 + d, 145
        elif d < 590 + 630:
            px, py = 1675, 145 + (d - 590)
        elif d < 2 * 590 + 630:
            px, py = 1675 - (d - 590 - 630), 775
        else:
            px, py = 1085, 775 - (d - 2 * 590 - 630)
        T.sparkle(c, px, py, 12, 210)
    c.drawRect(skia.Rect(0, 1000, W, H), P(C(235, 235, 230)))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.07, (960, 540), (1050, 520))(t), [E.title_layer(t, [("WHAT YOU CHOOSE", 100, 170, E.GOLD,
                                                                                               wt_or("end5", "choose", 4.0))])]


def s_end6(t, k, t0, t1):
    img, cam, _ = s_end5(t, k, t0 - 4, t1)
    return img, cam, [E.title_layer(t, [("THAT WAS ALWAYS TRUE", 90, 170, E.GOLD, wt_or("end6", "true", 1.2))])]


def s_cta(t, k, t0, t1):
    from cta2 import draw_cta2
    img, _, _ = s_end5(t, k, t0 - 8, t1)
    img = E.gblur(img, 10)
    img[..., :3] *= 0.55
    s, c = E.surf(world=False)
    c.save()
    c.translate(960 - 540 * 0.92, 540 - 1080 * 0.92)
    c.scale(0.92, 0.92)
    draw_cta2(c, t - t0, wt_or("cta", "like", 2.0) - t0, wt_or("cta", "subscribe", 2.6) - t0)
    c.restore()
    return img, (1.0, 960, 540), [E.arr(s)]


# ---------------------------------------------------------------- second content pass (morning / crime / extras)
def s_newborn(t, k, t0, t1):
    img = np.array(bg_room((245, 225, 225), (170, 140, 140)))
    s, c = E.surf()
    # mother (average look) holding a swaddled newborn; sound waves from her mouth to the baby
    pose = P_(look=(0.5, 0.5), mouth="talk", talk=abs(math.sin(t * 7)), hands=[(30, 40), (70, 30)], bends=(-1, -1), tilt=6)
    T.person(c, 760, 1000, 1.6, AVG, pose, t)
    bx, by = 1010, 640
    c.drawOval(skia.Rect(bx - 110, by - 60, bx + 110, by + 60), P(C(250, 240, 220)))
    c.drawOval(skia.Rect(bx - 110, by - 60, bx + 110, by + 60), S(T.OUT, 4))
    c.drawCircle(bx + 70, by - 20, 52, P(C(240, 200, 170)))
    c.drawCircle(bx + 70, by - 20, 52, S(T.OUT, 4))
    c.drawArc(skia.Rect(bx + 50, by - 30, bx + 70, by - 18), 200, 140, False, S(T.OUT, 4))
    c.drawArc(skia.Rect(bx + 78, by - 30, bx + 98, by - 18), 200, 140, False, S(T.OUT, 4))
    c.drawArc(skia.Rect(bx + 60, by - 8, bx + 84, by + 8), 20, 140, False, S(C(150, 60, 60), 4))
    for i in range(3):
        ph = ((t - t0) * 0.9 + i / 3) % 1
        r = 40 + 90 * ph
        c.drawArc(skia.Rect(860 - r, 360 - r, 860 + r, 360 + r), -40, 80, False, S(C(255, 140, 180, int(230 * (1 - ph))), 7))
    heart(c, bx + 150, by - 120, 26 * (0.8 + 0.2 * math.sin(t * 4)))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.06, (960, 540), (1000, 520))(t), [E.title_layer(t, [("MOM'S VOICE", 100, 160, E.GOLD,
                                                                                               wt_or("morn6", "voice", 3.5))])]


def s_dark_hug(t, k, t0, t1):
    img = np.array(bg_dark((15, 15, 35), (35, 30, 60)))
    s, c = E.surf()
    T.person(c, 860, 1000, 1.4, AVG, P_(eyes="closed", mouth="smile", look=(0.5, 0), hands=[(-20, 150), (110, 60)], bends=(1, -1)), t)
    T.person(c, 1080, 1000, 1.4, AVG, P_(eyes="closed", mouth="smile", look=(-0.5, 0), hands=[(-110, 60), (20, 150)], bends=(1, -1)), t)
    c.drawCircle(970, 640, 380, P(Shader=T.rad(970, 640, 380, [C(255, 200, 140, 70), C(255, 200, 140, 0)])))
    for i, lab in enumerate(("VOICES", "LAUGHS", "HABITS")):
        if t > wt_or("morn7", lab.lower(), 1.0 + i):
            label(c, 400 + i * 560, 250, lab, 56, (255, 236, 160))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), []


def s_dna(t, k, t0, t1):
    img = np.array(bg_dark((20, 30, 45), (40, 60, 80)))
    s, c = E.surf()
    for j in range(36):
        y = 160 + j * 22
        a = j * 0.45 + t * 1.4
        x1, x2 = 960 + 230 * math.sin(a), 960 - 230 * math.sin(a)
        c.drawLine(x1, y, x2, y, S(C(150, 220, 255, 120), 4))
        c.drawCircle(x1, y, 11, P(C(120, 220, 255)))
        c.drawCircle(x2, y, 11, P(C(255, 170, 120)))
    c.drawRoundRect(skia.Rect(1300, 380, 1620, 720), 20, 20, P(C(245, 245, 250)))
    c.drawRoundRect(skia.Rect(1300, 380, 1620, 720), 20, 20, S(T.OUT, 5))
    for j in range(9):
        c.drawRect(skia.Rect(1340 + j * 30, 420, 1356 + j * 30, 680), P(C(30, 30, 40, 70 + (j * 53) % 180)))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.title_layer(t, [("DNA", 140, 180, E.GOLD, wt_or("crime1", "dna", 4.0))])]


def s_twins_police(t, k, t0, t1):
    img = np.array(bg_room((200, 205, 220), (100, 100, 115)))
    s, c = E.surf()
    T.person(c, 760, 1000, 1.3, AVG, P_(look=(0.2, 0), mouth="smile", blink=blink_at(t, 1)), t)
    T.person(c, 1160, 1000, 1.3, AVG, P_(look=(-0.2, 0), mouth="smile", blink=blink_at(t, 2)), t)
    c.drawRect(skia.Rect(560, 60, 1360, 360), P(C(70, 80, 100, 200)))     # height chart behind them
    for j in range(5):
        c.drawLine(560, 100 + j * 60, 1360, 100 + j * 60, S(C(230, 230, 240, 160), 3))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.title_layer(t, [("IDENTICAL TWINS", 100, 1000, E.WHITE, wt_or("crime2", "twins", 4.0))])]


@lru_cache(maxsize=None)
def bg_store():
    s, c = grad_bg((20, 25, 60), (60, 60, 110))
    c.drawRect(skia.Rect(160, 300, 1760, 920), P(C(170, 150, 120)))           # the department store front
    c.drawRect(skia.Rect(160, 300, 1760, 920), S(T.OUT, 8))
    for j in range(5):
        c.drawRect(skia.Rect(220 + j * 310, 430, 470 + j * 310, 620), P(C(255, 225, 150, 210)))
        c.drawRect(skia.Rect(220 + j * 310, 430, 470 + j * 310, 620), S(T.OUT, 6))
    c.drawRect(skia.Rect(0, 920, W, H), P(C(80, 80, 95)))
    f = skia.Font(T.FB, 60)
    c.drawString("DEPARTMENT STORE", 960 - f.measureText("DEPARTMENT STORE") / 2, 385, f, P(C(250, 240, 220)))
    return E.arr(s)


def s_heist(t, k, t0, t1):
    img = np.array(bg_store())
    s, c = E.surf()
    # a jewelry display, then a gloved hand's shadow slides across it and the gems vanish one by one
    c.drawRoundRect(skia.Rect(700, 640, 1220, 820), 16, 16, P(C(60, 60, 80, 230)))
    c.drawRoundRect(skia.Rect(700, 640, 1220, 820), 16, 16, S(C(200, 220, 255), 4))
    gone = int(6 * clamp((t - t0 - 1.2) / 2.5))
    for j in range(6):
        if j >= gone:
            gx = 760 + j * 80
            gem = path([(gx, 700), (gx + 22, 722), (gx, 760), (gx - 22, 722)])
            c.drawPath(gem, P(C(*((120, 220, 255), (255, 120, 170), (140, 255, 170))[j % 3])))
            c.drawPath(gem, S(C(30, 30, 50), 3))
            T.sparkle(c, gx + 10, 705, 8, int(200 * (0.5 + 0.5 * math.sin(t * 5 + j))))
    sweep = clamp((t - t0 - 1.0) / 3.0)
    c.drawOval(skia.Rect(600 + 700 * sweep, 600, 900 + 700 * sweep, 860), P(C(0, 0, 0, int(140 * math.sin(math.pi * sweep)))))
    E.over(img, E.arr(s))
    lay = [E.title_layer(t, [("BERLIN, 2009", 100, 160, E.WHITE, wt_or("crime3", "berlin", 3.0))])]
    if t > wt_or("crime3", "millions", 5.0):
        lay.append(E.stamp_layer(t, "MILLIONS STOLEN", wt_or("crime3", "millions", 5.0), 960, 1000, 80, (220, 40, 50), -4))
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), lay


def s_glove(t, k, t0, t1):
    img = np.array(bg_dark((25, 25, 40), (50, 50, 75)))
    s, c = E.surf()
    g = skia.Path()                                          # a dropped glove on the floor
    g.addRoundRect(skia.Rect(260, 560, 560, 760), 60, 60)
    for j in range(4):
        g.addRoundRect(skia.Rect(270 + j * 70, 470, 320 + j * 70, 600), 25, 25)
    c.drawPath(g, P(C(40, 40, 48)))
    c.drawPath(g, S(C(120, 120, 140), 4))
    c.drawLine(560, 660, 760, 520, S(C(255, 236, 140), 5))
    for i, x in enumerate((1000, 1440)):
        T.person(c, x, 1000, 1.25, AVG, P_(look=(-0.4, 0), mouth="smile", blink=blink_at(t, i)), t)
        if t > wt_or("crime4", "matched", 3.5):
            u = smooth(clamp((t - wt_or("crime4", "matched", 3.5)) / 0.4))
            check_mark(c, x, 260, 40 * u)
    if t > wt_or("crime4", "which", 6.0):
        qmark(c, 1220, 420 + 15 * math.sin(t * 3), 150, 240)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.title_layer(t, [("DNA MATCH: BOTH", 90, 1000, E.GOLD, wt_or("crime4", "matched", 3.5))])]


def s_free(t, k, t0, t1):
    img = np.array(bg_city())
    s, c = E.surf()
    E.over(img, E.arr(s))
    walk = clamp((t - t0) / 4.0)
    people = [(AVG, 700 + 500 * walk, 1000, 1.2, P_(walk=t * 6, look=(1, 0), mouth="grin", eyes="squint")),
              (AVG, 520 + 500 * walk, 1000, 1.2, P_(walk=t * 6 + 1, look=(1, 0), mouth="grin", eyes="squint"))]
    img = lit(img, crowd_layer(t, people))
    lay = [E.stamp_layer(t, "CASE UNSOLVED", wt_or("crime5", "free", 3.5), 960, 300, 100, (220, 40, 50), -5)]
    if t > wt_or("crime5", "eight", 5.0):
        lay.append(E.title_layer(t, [("NOW: 8 BILLION TWINS", 80, 1000, E.GOLD, wt_or("crime5", "eight", 5.0))]))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), lay


def s_detective(t, k, t0, t1):
    img = np.array(bg_room((215, 200, 170), (110, 90, 70)))
    s, c = E.surf()
    c.drawRect(skia.Rect(900, 120, 1760, 760), P(C(150, 110, 70)))          # the evidence board
    c.drawRect(skia.Rect(900, 120, 1760, 760), S(T.OUT, 8))
    items = [("PRINTS", "fingerprints"), ("VOICE", "voices"), ("RECEIPT", "receipts"), ("PHONE", "phone"), ("WALK", "walks")]
    pins = []
    for i, (lab, wd) in enumerate(items):
        if t > wt_or("crime6", wd, 1.5 + i * 0.7):
            x, y = 1000 + (i % 3) * 260, 220 + (i // 3) * 280
            c.drawRect(skia.Rect(x, y, x + 200, y + 150), P(C(250, 248, 240)))
            c.drawRect(skia.Rect(x, y, x + 200, y + 150), S(T.OUT, 3))
            c.drawString(lab, x + 18, y + 95, skia.Font(T.FB, 40), P(C(40, 40, 50)))
            c.drawCircle(x + 100, y + 6, 10, P(C(220, 40, 50)))
            pins.append((x + 100, y + 6))
    for a_, b_ in zip(pins, pins[1:]):
        c.drawLine(*a_, *b_, S(C(220, 40, 50), 3))
    T.person(c, 520, 1000, 1.5, avg(hat="bowler", coat=(150, 120, 80)), P_(look=(0.8, -0.2), mouth="frown", brows="angry",
                                                                        hands=[(-20, 150), (60, 20)], bends=(1, 1)), t)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.title_layer(t, [("OLD SCHOOL", 100, 1000, E.GOLD, wt_or("crime6", "school", 1.2))])]


def s_disguise(t, k, t0, t1):
    img = np.array(bg_city())
    people = [(AVG, 140 + i * 210 + 40 * (t - t0) * (1 if i % 2 else -1), 940 + (i % 3) * 50, 0.9,
               P_(walk=t * 5 + i, look=(1 if i % 2 else -1, 0), blink=blink_at(t, i))) for i in range(9)]
    img = lit(img, crowd_layer(t, people))
    s, c = E.surf()
    c.drawCircle(960, 760, 170, S(C(255, 236, 140), 8))                     # "where is he?" ring that searches
    c.drawLine(1080, 880, 1200, 1000, S(C(255, 236, 140), 14))
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.06)(t), [E.title_layer(t, [("THE PERFECT DISGUISE", 90, 170, E.GOLD, wt_or("crime7", "disguise", 3.0))])]


def s_coach(t, k, t0, t1):
    img = np.array(bg_stadium())
    s, c = E.surf()
    c.drawRoundRect(skia.Rect(1100, 280, 1700, 720), 20, 20, P(C(40, 90, 60)))   # tactics board
    c.drawRoundRect(skia.Rect(1100, 280, 1700, 720), 20, 20, S(C(250, 250, 250), 6))
    for j in range(4):
        x0, y0 = 1180 + j * 120, 640 - j * 70
        c.drawCircle(x0, y0, 16, S(C(255, 255, 255), 5))
        u = smooth(clamp((t - t0 - 0.5 - j * 0.4) / 0.5))
        c.drawLine(x0, y0, x0 + 110 * u, y0 - 60 * u, S(C(255, 236, 140), 5))
    T.person(c, 720, 1000, 1.5, avg(coat=(40, 60, 120), hat="bowler"), P_(look=(0.8, -0.2), mouth="grin", hands=[(-20, 150), (120, -30)],
                                                                        bends=(1, 1)), t)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.title_layer(t, [("COACHES = SUPERSTARS", 90, 170, E.GOLD, wt_or("sport5b", "superstars", 2.5))])]


def s_beauty_pay(t, k, t0, t1):
    img = np.array(bg_dark((25, 40, 40), (50, 90, 80)))
    s, c = E.surf()
    grow = smooth(clamp((t - wt_or("job3b", "earn", 3.0) + 0.2) / 0.8))
    for i, (look, hgt, lab) in enumerate(((UNIQUE[0], 0.62 + 0.05 * grow, "RATED BETTER LOOKING"), (UNIQUE[2], 0.62, "EVERYONE ELSE"))):
        x = 660 + i * 600
        h = 520 * hgt
        c.drawRoundRect(skia.Rect(x - 110, 900 - h, x + 110, 900), 16, 16, P(Shader=T.lin((0, 900 - h), (0, 900), [C(140, 255, 160), C(40, 160, 80)])))
        c.drawRoundRect(skia.Rect(x - 110, 900 - h, x + 110, 900), 16, 16, S(T.OUT, 5))
        c.save()
        c.translate(x, 900 - h - 110)
        c.scale(0.55, 0.55)
        T.head(c, look, P_(mouth="smile"), t)
        c.restore()
        label(c, x, 980, lab, 40)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), [E.title_layer(t, [("THE BEAUTY PREMIUM", 100, 160, E.GOLD, wt_or("job3b", "premium", 6.0))])]


def s_premium_gone(t, k, t0, t1):
    img = np.array(bg_room((215, 220, 235), (110, 115, 130)))
    s, c = E.surf()
    img = lit(img, crowd_layer(t, [(AVG, 1400, 820, 1.2, P_(look=(-0.8, 0), mouth="smile", blink=blink_at(t, 9)))]))
    s, c = E.surf()
    c.drawRoundRect(skia.Rect(1100, 600, 1700, 900), 20, 20, P(C(150, 100, 60)))   # interview desk, in front of the interviewer
    c.drawRoundRect(skia.Rect(1100, 600, 1700, 900), 20, 20, S(T.OUT, 5))
    E.over(img, E.arr(s))
    people = [(AVG, 200 + i * 220, 1000, 1.1, P_(look=(0.8, 0), mouth="smile", blink=blink_at(t, i))) for i in range(4)]
    img = lit(img, crowd_layer(t, people))
    return img, cam_drift(t0, t1, 1.0, 1.05)(t), [E.stamp_layer(t, "HIRED FOR SKILLS", wt_or("job3c", "face", 5.0), 960, 220, 90, (60, 170, 90), -4)]


def s_medicine(t, k, t0, t1):
    img = np.array(bg_dark((20, 40, 55), (40, 80, 95)))
    people = [(UNIQUE[i % 5], 260 + i * 200, 1000, 0.95, P_(blink=blink_at(t, i), mouth="smile")) for i in range(8)]
    img = lit(img, crowd_layer(t, people))
    s, c = E.surf()
    for i in range(8):   # a pill above each person; each reacts differently (check / partial / cross)
        x = 260 + i * 200
        c.drawRoundRect(skia.Rect(x - 40, 300, x + 40, 340), 20, 20, P(C(255, 255, 255)))
        c.drawRoundRect(skia.Rect(x, 300, x + 40, 340), 20, 20, P(C(120, 200, 255)))
        if t > wt_or("dis7b", "differently", 5.0):
            (check_mark if i % 3 else cross_mark)(c, x, 420, 30)
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), [E.title_layer(t, [("DIVERSE MEDICAL STUDIES", 84, 170, E.GOLD, wt_or("dis7b", "diverse", 2.0))])]


def s_still_yours(t, k, t0, t1):
    img = np.array(bg_dark((40, 30, 70), (90, 60, 120)))
    s, c = E.surf()
    T.person(c, 960, 1000, 1.6, AVG, P_(mouth="grin", eyes="squint", hands=[(-60, -60), (60, -60)], bends=(-1, 1)), t)
    words = [("JOKES", "jokes"), ("KINDNESS", "kindness"), ("STORIES", "stories"), ("HOW YOU TREAT PEOPLE", "treat")]
    for i, (lab, wd) in enumerate(words):
        u = snap(t, wt_or("end5b", wd, 0.5 + i * 0.8), 7, 1.5)
        if u > 0:
            x = (380, 1540, 380, 1500)[i]
            y = (300, 300, 640, 760)[i]
            c.save()
            c.translate(x, y)
            c.scale(u, u)
            label(c, 0, 0, lab, 54, (255, 236, 160), (40, 15, 50, 220))
            c.restore()
    E.over(img, E.arr(s))
    return img, cam_drift(t0, t1, 1.0, 1.04)(t), []


def s_cover(t, k, t0, t1):
    img, cam, _ = s_end5(t, k, t0 - 8, t1)
    return img, cam, [E.title_layer(t, [("THE STORY IS YOU", 110, 170, E.GOLD, wt_or("end6b", "story", 4.0))])]


SHOTS = dict(hook1=s_hook1, hook2=s_hook2, hook3=s_hook3, hook4=s_hook4, hook5=s_hook5, hook6=s_hook6,
             morn1=s_brain, morn2=s_faces, morn3=s_kitchen, morn4=s_pickup, morn5=s_window, morn6=s_newborn, morn7=s_dark_hug,
             id1=s_phone, id2=s_cctv, id3=s_twins_prints, id4=s_print_detail, id5=s_scanners, id6=s_creative, id7=s_fingertips,
             crime1=s_dna, crime2=s_twins_police, crime3=s_heist, crime4=s_glove, crime5=s_free, crime6=s_detective, crime7=s_disguise,
             sport5b=s_coach, job3b=s_beauty_pay, job3c=s_premium_gone, dis7b=s_medicine, end5b=s_still_yours, end6b=s_cover,
             love1=s_love1, love2=s_love2, love3=s_love3, love4=s_love4, love5=s_love5, love6=s_love6, love7=s_love7,
             fame1=s_fame1, fame2=s_fame2, fame3=s_fame3, fame4=s_fame4,
             sport1=s_wingspan, sport2=s_bodies, sport3=s_race, sport4=s_train, sport5=s_honest, sport6=s_archery,
             job1=s_ricardo, job2=s_trade, job3=s_jobs_diff, job4=s_same_jobs, job5=s_queues, job6=s_salary, job7=s_effort, job8=s_owns,
             sch1=s_sch1, sch2=s_sch2, sch3=s_sch3, sch4=s_sch4, sch5=s_sch5, sch6=s_sch6,
             dis1=s_dis1, dis2=s_dis2, dis3=s_dis3, dis4=s_dis4, dis5=s_dis5, dis6=s_dis6, dis7=s_dis7, dis8=s_dis8, dis9=s_dis9,
             drift1=s_drift1, drift2=s_drift2, drift3=s_drift3, drift4=s_drift4, drift5=s_drift5, drift6=s_drift6,
             end1=s_end1, end2=s_end2, end3=s_end3, end4=s_end4, end5=s_end5, end6=s_end6, cta=s_cta)
assert set(SHOTS) == set(ORDER), set(ORDER) ^ set(SHOTS)


# =================================================================================== transitions + chapter titles
def splat_layer(t):
    for i, tc in enumerate(CHAP_CUTS, start=1):
        k = t - tc
        if -4 / FPS <= k < 5 / FPS:
            if CHAPTER[ORDER[shot_at(tc + 0.01)]] in ("disease",) and k >= 0 and False:
                return None
            u = (k + 4 / FPS) / (4 / FPS) if k < 0 else 1 - k / (5 / FPS)
            u = smooth(clamp(u))
            s, c = E.surf(world=False)
            r = random.Random(i)
            cx, cy = 960 + r.uniform(-200, 200), 540 + r.uniform(-100, 100)
            R = 1350 * u
            blob = skia.Path()
            blob.addCircle(cx, cy, R)
            for j in range(14):
                a = r.uniform(0, 2 * math.pi)
                d = R * r.uniform(0.85, 1.1)
                blob.addCircle(cx + d * math.cos(a), cy + d * math.sin(a), R * r.uniform(0.12, 0.25))
            c.drawPath(blob, P(Shader=T.rad(cx, cy, max(1, R), [C(255, 225, 120), C(235, 165, 40), C(190, 120, 25)])))
            return E.arr(s)
    return None


def chapter_layer(t):
    """Chapter name: slides in at the lower left for 2.4 s after each chapter cut."""
    for tc in CHAP_CUTS:
        k = t - tc - 0.15
        if 0 <= k < 2.4:
            ch = CHAPTER[ORDER[shot_at(tc + 0.02)]]
            txt = CHAP_TITLE.get(ch)
            if not txt:
                return None
            u = smooth(clamp(k / 0.35)) * (1 - smooth(clamp((k - 2.0) / 0.4)))
            s, c = E.surf(world=False)
            f = skia.Font(T.FB, 54)
            w = f.measureText(txt)
            x = -w - 80 + (w + 160) * u
            c.drawRoundRect(skia.Rect(x - 30, 940, x + w + 30, 1010), 18, 18, P(C(20, 12, 30, int(210 * u))))
            c.drawRoundRect(skia.Rect(x - 30, 940, x + 6, 1010), 4, 4, P(C(255, 200, 70, int(255 * u))))
            c.drawString(txt, x + 14, 993, f, P(C(255, 236, 160, int(255 * u))))
            return E.arr(s)
    return None


# =================================================================================== frame
def render(f, out=None):
    t = f / FPS
    i = shot_at(t)
    key = ORDER[i]
    img, cam, lays = SHOTS[key](t, t - SHOT_START[i], SHOT_START[i], SHOT_END[i])
    z, cx, cy = cam
    rgb = E.crop(img, z, cx, cy)
    for lay in lays:
        rgb = E.comp_screen(rgb, lay)
    for lay in (chapter_layer(t), splat_layer(t)):
        if lay is not None:
            rgb = E.comp_screen(rgb, lay)
    rgb = E.finish(rgb, f, bloom=0.6 if CHAPTER[key] == "disease" and key == "dis5" else 1.0)
    E.save(rgb, out or os.path.join(D, "frames", f"{f + 1:05d}.png"))
    return f


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "frames"
    print("duration", round(DUR, 1), "s,", NF, "frames,", len(ORDER), "shots,", len(CHAP_CUTS), "chapter cuts")
    if mode == "stills":
        os.makedirs(os.path.join(D, "stills"), exist_ok=True)
        targets = sys.argv[2].split(",") if len(sys.argv) > 2 else [f"mid:{k}" for k in ORDER]
        for tg in targets:
            if tg.startswith("mid:"):
                i = ORDER.index(tg[4:])
                ts = (SHOT_START[i] + SHOT_END[i]) / 2 + 0.6
            else:
                ts = float(tg)
            f = int(round(ts * FPS))
            render(f, os.path.join(D, "stills", f"{ORDER[shot_at(f / FPS)]}_{ts:07.2f}.png"))
        print("stills done")
    else:
        os.makedirs(os.path.join(D, "frames"), exist_ok=True)
        todo = [f for f in range(NF) if os.environ.get("SKIP") != "1" or not os.path.exists(os.path.join(D, "frames", f"{f + 1:05d}.png"))]
        with Pool(int(os.environ.get("PROCS", "6"))) as pool:
            for j, f in enumerate(pool.imap_unordered(render, todo, chunksize=8)):
                if j % 600 == 0:
                    print("frame", j, "/", len(todo), flush=True)
        print("done")
