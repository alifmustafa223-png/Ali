"""YouTube Short: "The Canary in the Coal Mine" - the channel's toon characters inside 3D miniature mine plates
(look approved on the 10 s canary test: toon characters + Blender plates; finish from the approved 2D engine).

Facts (sourced): carbon monoxide is colourless and odourless; after mine explosions it ("afterdamp") often killed more
miners than the blast (Haldane's 1890s investigations). John Scott Haldane tested the gases on himself and proposed small
animals as detectors; mice were tried, canaries were easier to watch. Canaries are small with a fast breathing rate, so
the gas affects them first. Britain's 1911 Coal Mines Act made larger mines keep small birds. Miners used a
resuscitator cage with a small oxygen cylinder to revive birds. Canaries were phased out in 1986 for electronic
detectors (~75 years after the 1911 rule). (Mental Floss, Ripley's, CIM Magazine, Paste/Science History.)

  python make_canary.py stills 1.0,5.2        -> ../canary/stills/s_XX.XX.png
  python make_canary.py frames                -> ../canary/frames/%04d.png   (multiprocess, PROCS=4)
Plates: ../canary/plates/plate_{A..E}.png (blender/mine_plates.py). Voice: ../canary/vo_final.wav (+ times/words json).
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
D = os.path.join(HERE, "..", "canary")
PLATES = os.environ.get("PLATES", os.path.join(D, "plates"))
TIMES = json.load(open(os.path.join(D, "vo_final.wav.times.json")))
WORDS = json.load(open(os.path.join(D, "vo_final.wav.words.json")))
LINES = json.load(open(os.path.join(D, "lines_final.json")))
ORDER = [l["key"] for l in LINES]
VO_LEN = float(open(os.path.join(D, "vo_end.txt")).read())
DUR = round(min(64.6, max(61.5, TIMES["cta"] + 3.9)), 3)   # CTA shows SUBSCRIBED + bell >= 0.5 s (LESSONS 82)
NF = int(round(DUR * FPS))
OUT_FR = os.path.join(D, "frames")
PHYS = {}          # physics numbers, asserted below and reused by the audio script


def line_t(key):
    return TIMES[key]


def word_t(line, *cands, nth=1):
    """Start time of the nth occurrence (at/after `line`) of the first candidate word whisper produced."""
    nxt = ORDER.index(line) + 1
    t1 = TIMES[ORDER[nxt]] if nxt < len(ORDER) else 1e9
    for w in cands:
        hits = sorted(v for k, v in WORDS.items() if k.split("#")[0] == w and TIMES[line] - 0.3 <= v < t1 - 0.05)
        if len(hits) >= nth:
            return hits[nth - 1]
    raise KeyError(f"none of {cands} in line {line!r}")


# scenes: (name, start time)
def _scenes():
    s = [("hook", 0.0), ("killer", line_t("killer")), ("late", line_t("late")), ("blast", line_t("afterdamp")),
         ("haldane", line_t("haldane")), ("mice", line_t("mice")), ("alarm", line_t("alarm")), ("first", line_t("first")),
         ("fall", line_t("stopped")), ("run", word_t("stopped", "everyone") - 0.08), ("law", line_t("law")),
         ("twist", line_t("twist")), ("revive", line_t("revive")), ("retire", line_t("retire")), ("cta", line_t("cta"))]
    return [(n, 0.0 if i == 0 else t - 0.12) for i, (n, t) in enumerate(s)]


SCENES = _scenes()
CUTS = [t for _, t in SCENES] + [DUR]


def scene_at(t):
    for i in range(len(SCENES)):
        if CUTS[i] <= t < CUTS[i + 1]:
            return i
    return len(SCENES) - 1


# =================================================================================== looks
HERO = dict(skin=(230, 190, 150), hair="neat", hair_col=(35, 25, 20), coat=(95, 75, 55), pants=(60, 55, 55), nose="small", hat="miner")
PAL = dict(skin=(205, 150, 110), hair="neat", hair_col=(25, 20, 18), coat=(70, 80, 95), pants=(55, 55, 60), nose="long", hat="miner")
OLD = dict(skin=(235, 195, 165), hair="neat", hair_col=(120, 110, 100), coat=(110, 60, 50), pants=(60, 55, 55), nose="small", hat="miner",
           mustache=True)
HALDANE = dict(skin=(238, 200, 172), hair="grey", hair_col=(215, 215, 220), coat=(45, 45, 55), vest=(120, 35, 35), pants=(45, 45, 50),
               nose="long", mustache=True, glasses=True)

# =================================================================================== plates
_PL = {}


def plate(name):
    if name not in _PL:
        im = Image.open(os.path.join(PLATES, f"plate_{name}.png")).convert("RGB").resize((E.WW, E.WH), Image.LANCZOS)
        a = np.asarray(im).astype(np.float32) / 255.0
        _PL[name] = np.dstack([a, np.ones(a.shape[:2], np.float32)])
    return _PL[name].copy()


HOOK_B = json.load(open(os.path.join(PLATES, "plate_B.json")))["hook_px"]   # hook position in plate B (1080x1920 px)
VP_A = (545, 850)        # tunnel vanishing point in plates A / E (from the plate render)


# =================================================================================== props
BRASS, BRASS_D, INK = C(220, 170, 70), C(150, 105, 35), C(30, 18, 14)
YEL, YEL_D = C(255, 214, 40), C(235, 175, 25)


def note(c, x, y, s, a, double=False):
    ink, fill = C(30, 18, 14, a), C(255, 230, 120, a)
    heads = [(0, 0)] + ([(34, -8)] if double else [])
    for hx, hy in heads:
        r = skia.Rect(x + (hx - 13) * s, y + (hy - 9) * s, x + (hx + 13) * s, y + (hy + 9) * s)
        c.drawOval(r, P(ink))
        c.drawOval(r.makeInset(3 * s, 3 * s), P(fill))
        c.drawLine(x + (hx + 11) * s, y + hy * s, x + (hx + 11) * s, y + (hy - 55) * s, S(ink, 7 * s))
        c.drawLine(x + (hx + 11) * s, y + hy * s, x + (hx + 11) * s, y + (hy - 55) * s, S(fill, 3 * s))
    if double:
        c.drawLine(x + 11 * s, y - 55 * s, x + 45 * s, y - 63 * s, S(ink, 10 * s))
        c.drawLine(x + 11 * s, y - 55 * s, x + 45 * s, y - 63 * s, S(fill, 5 * s))


def canary(c, x, y, s, t, sing=True, rot=0.0, eyes="open", breathe=0.0, flap=0.0):
    """Canary standing with its feet at (x, y) (cage units * s). eyes: open | shut | x."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.translate(0, -22)      # rotate about the body centre (22 units above the feet)
    c.rotate(rot)
    c.translate(0, 22)
    bob = math.sin(t * 9) * 1.5 if sing else 0.0
    br = 1 + breathe * math.sin(t * 2 * math.pi * 4.5)     # fast breathing (~4.5 breaths/s shown)
    c.translate(0, -22 + bob)
    for leg in (-6, 6):
        c.drawLine(leg, 8, leg + 2, 22 - bob, S(C(200, 120, 40), 3))
    c.save()
    c.scale(br, br)
    body = skia.Path()
    body.addOval(skia.Rect(-26, -20, 22, 20))
    c.drawPath(body, P(Shader=T.lin((0, -20), (0, 20), [C(255, 228, 80), YEL_D])))
    c.drawPath(body, S(INK, 5))
    wing = skia.Path()
    wing.moveTo(-14, -6)
    wing.quadTo(4, -14 - 10 * flap, 14, -2 - 14 * flap)
    wing.quadTo(0, 6, -14, -6)
    c.drawPath(wing, P(C(240, 190, 30)))
    c.drawPath(wing, S(INK, 3.5))
    c.restore()
    tail = skia.Path()
    tail.moveTo(-24, 0)
    tail.lineTo(-46, 10)
    tail.lineTo(-42, -6)
    tail.close()
    c.drawPath(tail, P(C(240, 190, 30)))
    c.drawPath(tail, S(INK, 4))
    c.drawCircle(18, -26, 15, P(Shader=T.lin((0, -41), (0, -11), [C(255, 235, 110), YEL])))
    c.drawCircle(18, -26, 15, S(INK, 5))
    if eyes == "open":
        c.drawCircle(22, -29, 4, P(INK))
        c.drawCircle(21, -30.5, 1.4, P(C(255, 255, 255)))
    elif eyes == "x":
        for d in (-1, 1):
            c.drawLine(18, -33, 26, -25 if d > 0 else -33, S(INK, 3))
        c.drawLine(18, -25, 26, -33, S(INK, 3))
    else:
        c.drawArc(skia.Rect(17, -32, 27, -24), 20, 140, False, S(INK, 3))
    open_ = sing and math.sin(t * 9) > 0
    beak = skia.Path()
    beak.moveTo(31, -30)
    beak.lineTo(44, -26 - (5 if open_ else 0))
    beak.lineTo(31, -24)
    if open_:
        beak.moveTo(31, -24)
        beak.lineTo(43, -18)
        beak.lineTo(31, -20)
    c.drawPath(beak, P(C(255, 140, 40)))
    c.drawPath(beak, S(INK, 3))
    c.drawCircle(10, -20, 4, P(C(255, 150, 120, 120)))
    c.restore()


PERCH_Y, FLOOR_Y = 92.0, 146.0       # cage units: perch top, cage floor top


def _bird_outline():
    """Points of the drawn canary relative to its body centre (body, head, beak, tail, legs) - for contact physics."""
    pts = [(-2 + 24 * math.cos(a), 20 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 48)]
    pts += [(18 + 15 * math.cos(a), -26 + 15 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 32)]
    pts += [(44, -26), (31, -30), (-46, 10), (-42, -6), (-6, 22), (6, 22), (-4, 22), (8, 22)]
    return pts


_OUT = _bird_outline()


def rest_y(rot, floor):
    """Feet parameter that puts the rotated bird's LOWEST point exactly on `floor` (no hover, no sink)."""
    r = math.radians(rot)
    low = max(px * math.sin(r) + py * math.cos(r) for px, py in _OUT)   # y of the lowest point below the body centre
    return floor - low + 22


def cage(c, x, y, s, t, swing=0.0, bird=None, notes=True):
    """Brass birdcage hanging from its ring at (x, y). bird: dict(y=feet_y, rot, sing, eyes, breathe) in cage units."""
    bird = bird or {}
    c.save()
    c.translate(x, y)
    c.rotate(swing)
    c.scale(s, s)
    top, bot, w = 16, 150, 62
    c.drawCircle(0, 8, 8, S(INK, 9))
    c.drawCircle(0, 8, 8, S(BRASS, 4))
    by = bird.get("y", PERCH_Y)
    canary(c, 0, by, 1.0, t, bird.get("sing", True), bird.get("rot", 0.0), bird.get("eyes", "open"), bird.get("breathe", 0.0),
           bird.get("flap", 0.0))
    c.drawLine(-w + 8, PERCH_Y, w - 8, PERCH_Y, S(INK, 8))
    c.drawLine(-w + 8, PERCH_Y, w - 8, PERCH_Y, S(BRASS_D, 4))
    for k in range(-4, 5):
        xb = k * w / 4.5
        yt = 60 - (1 - (xb / w) ** 2) * 40
        c.drawLine(xb, yt, xb, bot, S(INK, 7))
        c.drawLine(xb, yt, xb, bot, S(BRASS, 3.5))
    dome = skia.Path()
    dome.moveTo(-w, 60)
    dome.cubicTo(-w, top, w, top, w, 60)
    c.drawPath(dome, S(INK, 9))
    c.drawPath(dome, S(BRASS, 5))
    c.drawRoundRect(skia.Rect(-w - 8, bot - 4, w + 8, bot + 14), 6, 6, P(BRASS_D))
    c.drawRoundRect(skia.Rect(-w - 8, bot - 4, w + 8, bot + 14), 6, 6, S(INK, 6))
    c.restore()
    if notes and bird.get("sing", True):
        for k in range(3):
            ph = (t * 1.3 + k / 3) % 1.0
            note(c, x + s * (50 + ph * 70 + k * 10), y + s * (60 - ph * 110), s * 0.55, int(255 * math.sin(math.pi * ph)), k % 2 == 0)


def resus_cage(c, x, y, s, t, door=1.0, valve=0.0, flow=0.0, bird=None):
    """The canary resuscitator: a glass box with a round door and an oxygen cylinder on top. (x, y) = bottom centre.
    door: 1 open .. 0 shut. valve: wheel angle (turns). flow: 0..1 oxygen stream strength."""
    bird = bird or {}
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    bw, bh = 170, 150
    box = skia.Rect(-bw / 2, -bh, bw / 2, 0)
    c.drawRoundRect(box, 14, 14, P(C(160, 210, 230, 70)))
    bx, byy = bird.get("x", 0), bird.get("y", -8)
    canary(c, bx, byy, 1.0, t, bird.get("sing", False), bird.get("rot", 0), bird.get("eyes", "shut"), 0.0, bird.get("flap", 0))
    if flow > 0:   # oxygen: soft white streams from the inlet down into the box
        r = random.Random(3)
        for k in range(14):
            ph = (t * 1.6 + k / 14) % 1.0
            px = 30 + 10 * math.sin(k * 2.1 + t * 3) - ph * 40
            py = -bh + 10 + ph * (bh - 30)
            c.drawCircle(px, py, 4 + 5 * ph, P(C(235, 250, 255, int(150 * flow * math.sin(math.pi * ph))), MaskFilter=BLUR(3)))
    c.drawRoundRect(box, 14, 14, S(INK, 7))
    c.drawRoundRect(box, 14, 14, S(C(120, 130, 140), 3))
    for gx in (-bw / 2 + 6, bw / 2 - 6):
        c.drawLine(gx, -bh + 14, gx, -14, S(C(255, 255, 255, 120), 3))
    c.drawLine(-bw / 2 + 22, -bh + 22, -bw / 2 + 60, -bh + 22, S(C(255, 255, 255, 160), 5))   # glass glint
    # round door (front, hinged on its left): an ellipse whose width follows the door angle
    dr = 34
    dcx, dcy = -34, -92          # door high on the left, so the bird on the floor (right) is always visible
    c.drawCircle(dcx, dcy, dr + 8, S(INK, 9))
    c.drawCircle(dcx, dcy, dr + 8, S(BRASS, 5))
    ang = door * math.pi / 2 * 0.95
    wv = max(0.04, math.cos(ang))
    c.save()
    c.translate(dcx - dr, dcy)
    c.scale(wv, 1)
    c.translate(dr, 0)
    c.drawCircle(0, 0, dr, P(C(170, 220, 240, 90)))
    c.drawCircle(0, 0, dr, S(INK, 6))
    c.drawCircle(0, 0, dr - 6, S(BRASS, 4))
    c.drawCircle(dr - 10, 0, 5, P(BRASS_D))
    c.restore()
    # oxygen cylinder on top + tube into the box + valve wheel
    c.drawRoundRect(skia.Rect(-20, -bh - 120, 40, -bh - 8), 18, 18, P(Shader=T.lin((-20, 0), (40, 0), [C(40, 120, 70), C(90, 190, 120), C(30, 100, 60)])))
    c.drawRoundRect(skia.Rect(-20, -bh - 120, 40, -bh - 8), 18, 18, S(INK, 6))
    f = skia.Font(T.FB, 22)
    c.drawString("O2", -2, -bh - 54, f, P(C(255, 255, 255)))
    tube = skia.Path()
    tube.moveTo(40, -bh - 30)
    tube.quadTo(70, -bh - 30, 40, -bh + 4)
    c.drawPath(tube, S(INK, 10))
    c.drawPath(tube, S(C(90, 90, 95), 5))
    c.save()
    c.translate(10, -bh - 132)
    c.drawRect(skia.Rect(-5, 0, 5, 14), P(C(70, 70, 75)))
    c.rotate(valve * 360)
    for k in range(4):
        c.save()
        c.rotate(k * 90)
        c.drawLine(0, 0, 0, -18, S(INK, 7))
        c.drawLine(0, 0, 0, -18, S(C(210, 50, 45), 4))
        c.restore()
    c.drawCircle(0, 0, 18, S(INK, 7))
    c.drawCircle(0, 0, 18, S(C(210, 50, 45), 4))
    c.restore()
    c.drawRoundRect(skia.Rect(-bw / 2 - 10, -6, bw / 2 + 10, 12), 6, 6, P(C(80, 60, 45)))
    c.drawRoundRect(skia.Rect(-bw / 2 - 10, -6, bw / 2 + 10, 12), 6, 6, S(INK, 6))
    c.restore()


def mouse_box(c, x, y, s, t, asleep=True):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawRoundRect(skia.Rect(-70, -70, 70, 0), 8, 8, P(C(120, 90, 60, 90)))
    body = skia.Path()
    body.addOval(skia.Rect(-34, -34, 30, 0))
    c.drawPath(body, P(C(175, 170, 170)))
    c.drawPath(body, S(INK, 5))
    c.drawCircle(26, -26, 16, P(C(180, 175, 175)))
    c.drawCircle(26, -26, 16, S(INK, 5))
    c.drawCircle(18, -42, 9, P(C(230, 170, 175)))
    c.drawCircle(18, -42, 9, S(INK, 4))
    if asleep:
        c.drawArc(skia.Rect(28, -30, 38, -22), 20, 140, False, S(INK, 3))
    else:
        c.drawCircle(33, -27, 3.5, P(INK))
    c.drawCircle(42, -22, 3.5, P(C(240, 140, 150)))
    tail = skia.Path()
    tail.moveTo(-32, -10)
    tail.cubicTo(-60, -8, -50, -40, -66, -36)
    c.drawPath(tail, S(INK, 6))
    c.drawPath(tail, S(C(230, 170, 175), 3))
    for k in range(-60, 70, 20):
        c.drawLine(k, -70, k, 0, S(C(90, 90, 95, 200), 3))
    c.drawRoundRect(skia.Rect(-70, -70, 70, 0), 8, 8, S(INK, 6))
    if asleep:
        for k in range(2):
            ph = (t * 0.7 + k * 0.5) % 1.0
            f = skia.Font(T.FB, 22 + 10 * ph)
            c.drawString("z", 40 + 20 * ph, -60 - 50 * ph, f, P(C(255, 255, 255, int(220 * math.sin(math.pi * ph)))))
    c.restore()


def detector(c, x, y, s, t, beep_t=None):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawRoundRect(skia.Rect(-42, -70, 42, 40), 12, 12, P(Shader=T.lin((0, -70), (0, 40), [C(255, 210, 60), C(220, 160, 30)])))
    c.drawRoundRect(skia.Rect(-42, -70, 42, 40), 12, 12, S(INK, 6))
    c.drawRoundRect(skia.Rect(-30, -58, 30, -24), 5, 5, P(C(120, 160, 110)))
    c.drawRoundRect(skia.Rect(-30, -58, 30, -24), 5, 5, S(INK, 4))
    c.drawString("CO 0", -26, -32, skia.Font(T.FB, 22), P(C(30, 50, 30)))
    on = beep_t is not None and (t - beep_t) % 0.8 < 0.25 and t >= beep_t
    c.drawCircle(-18, -4, 8, P(C(80, 255, 120) if on else C(40, 90, 50)))
    c.drawCircle(-18, -4, 8, S(INK, 3))
    if on:
        c.drawCircle(-18, -4, 22, P(C(80, 255, 120, 90), MaskFilter=BLUR(8)))
    c.drawCircle(16, -4, 9, P(C(60, 60, 65)))
    c.restore()


def parchment(c, x, y, s, rot):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    c.drawRoundRect(skia.Rect(-210, -150, 210, 150), 10, 10, P(Shader=T.lin((0, -150), (0, 150), [C(245, 228, 190), C(222, 196, 150)])))
    c.drawRoundRect(skia.Rect(-210, -150, 210, 150), 10, 10, S(C(120, 85, 50), 6))
    for txt, yy, sz, col in (("COAL MINES ACT", -88, 34, C(80, 40, 20)), ("1911", -30, 52, C(150, 30, 30)),
                             ("Larger mines must keep", 30, 24, C(70, 45, 25)), ("small birds underground", 66, 24, C(70, 45, 25))):
        f = skia.Font(T.FB, sz)
        c.drawString(txt, -f.measureText(txt) / 2, yy, f, P(col))
    c.drawCircle(150, 105, 30, P(C(180, 30, 35)))
    c.drawCircle(150, 105, 30, S(C(120, 20, 25), 4))
    c.restore()


# =================================================================================== effects
def gas(c, t, y0, y1, amount, seed=1):
    """Creeping green carbon-monoxide haze (artistic: CO is invisible, so it is drawn as a faint ghostly tint)."""
    if amount <= 0:
        return
    r = random.Random(seed)
    for k in range(16):
        x0 = r.uniform(-200, W + 200)
        yy = r.uniform(y0, y1)
        rx, ry = r.uniform(180, 380), r.uniform(60, 140)
        x = x0 + 60 * noise1(t, seed * 50 + k, 0.25) + 25 * t
        y = yy + 25 * noise1(t, seed * 70 + k, 0.3)
        a = int(70 * amount * (0.6 + 0.4 * noise1(t, seed * 90 + k, 0.4)))
        c.drawOval(skia.Rect(x - rx, y - ry, x + rx, y + ry), P(C(120, 210, 90, max(0, a)), MaskFilter=BLUR(40)))


def dust(c, t, n, seed, col=(255, 220, 160), y0=200, y1=1750):
    r = random.Random(seed)
    for k in range(n):
        x0, yy, sp, ph = r.uniform(0, W), r.uniform(y0, y1), r.uniform(8, 25), r.uniform(0, 6.28)
        x = (x0 + sp * t + 20 * math.sin(t * 0.7 + ph)) % W
        y = yy - 10 * t + 15 * math.sin(t * 0.5 + ph * 2)
        a = int(110 + 90 * math.sin(t * 2 + ph))
        c.drawCircle(x, y, r.uniform(1.2, 3.2), P(C(*col, max(0, a))))


def char(img, look, x, y, s_, pose, t, shadow=0.5, rim=0.55, rim_col=(1.0, 0.75, 0.45), extra=None, blur=0):
    ch = E.draw_person(look, x, y, s_, pose, t, extra)
    if blur:
        ch = E.gblur(ch, blur)
        return E.over(img, ch)
    return E.light_char(ch, img, y, shadow=shadow, rim=rim, rim_col=rim_col)


def layer_over(img, draw):
    s, c = E.surf()
    draw(c)
    return E.over(img, E.arr(s))


def cage_fall(tf):
    """Canary falls off its perch at tf = 0 (cage units, gravity scaled: 150 units ~ 30 cm -> 1 unit = 2 mm,
    g = 9.81 m/s^2 = 4905 units/s^2). Lands on the cage floor, one small bounce (e = 0.22), tips onto its side."""
    g = 4905.0
    h = FLOOR_Y - PERCH_Y
    t1 = math.sqrt(2 * h / g)
    v1 = g * t1
    e = 0.22
    t2 = 2 * e * v1 / g
    rot = 100 * smooth(clamp(tf / (t1 + t2 + 0.08)))
    floor_feet = rest_y(rot, FLOOR_Y)          # where the feet parameter must be for the body to touch the floor
    if tf <= 0:
        y = PERCH_Y
    elif tf < t1:
        y = min(floor_feet, PERCH_Y + 0.5 * g * tf * tf)
    elif tf < t1 + t2:
        u = tf - t1
        y = min(floor_feet, floor_feet - (e * v1 * u - 0.5 * g * u * u))
    else:
        y = floor_feet
    PHYS.setdefault("fall", dict(t_land=t1, t_settle=t1 + t2, drop_units=h))
    return y, rot


# =================================================================================== scenes
# each returns (world image, (zoom, cx, cy), [screen layers])
def sc_hook(t, f):
    t0, t1 = CUTS[0], CUTS[1]
    img = plate("A")
    k = smooth((t - t0) / (t1 - t0))
    hop = math.exp(-((t - word_t("hook", "saved")) / 0.12) ** 2) * 22
    pose = dict(eyes="squint" if t < word_t("hook", "saved") else "open", brows="smug" if t < word_t("hook", "saved") else "up", mouth="grin",
                look=(0.7, -0.3), hands=[(-30, 110), (115, -95)], tilt=-5 + 3 * math.sin(t * 1.3))
    x, y, s_ = 420, 1700 - hop, 1.38
    img = char(img, HERO, x, y, s_, pose, t)
    hx, hy = T.hand_pos(x, y, s_, pose, 1)
    img = layer_over(img, lambda c: (cage(c, hx - 2, hy - 10, 1.55, t, swing=3 * math.sin(t * 3.1)), dust(c, t, 40, 1)))
    lays = [E.title_layer(t, [("THIS TINY BIRD", 92, 330, E.WHITE, word_t("hook", "this")),
                              ("SAVED MINERS", 130, 470, E.GOLD, word_t("hook", "saved"))]),
            E.stamp_layer(t, "75 YEARS", word_t("hook", "seventy", "75", "seventyfive"), 540, 680, 110)]
    return img, (lerp(1.0, 1.12, k), lerp(540, 560, k), lerp(960, 1040, k)), lays


def sc_killer(t, f):
    t0, t1 = CUTS[1], CUTS[2]
    img = plate("C")
    k = smooth((t - t0) / (t1 - t0))
    u = (t - t0) / (t1 - t0)
    walk = (t - t0) * 2 * math.pi * 1.6
    pose = dict(eyes="open", brows="flat", mouth="smile", look=(0.3 * math.sin(t * 0.8), 0), walk=walk,
                hands=[(-20, 150), (40, -150)], tilt=3 * math.sin(t))
    x, y, s_ = lerp(380, 560, u), 1640 + lerp(0, 60, u), lerp(1.05, 1.25, u)

    def pick(c):
        hx, hy = T.hand_pos(x, y, s_, pose, 1)
        c.save()
        c.translate(hx, hy)
        c.rotate(-30)
        c.scale(s_, s_)
        c.drawLine(0, 30, 0, -150, S(INK, 16))
        c.drawLine(0, 30, 0, -150, S(C(150, 100, 55), 9))
        hp = skia.Path()
        hp.moveTo(-80, -140)
        hp.quadTo(0, -175, 80, -140)
        hp.quadTo(0, -160, -80, -140)
        c.drawPath(hp, S(INK, 16))
        c.drawPath(hp, S(C(160, 160, 165), 8))
        c.restore()
    img = char(img, HERO, x, y, s_, pose, t, extra=pick, rim_col=(0.7, 1.0, 0.6))
    img = layer_over(img, lambda c: gas(c, t, 1100, 1800, ramp(t, t0, 1.5), 2))
    lays = [E.title_layer(t, [("INVISIBLE", 140, 380, E.WHITE, word_t("killer", "invisible"))]),
            E.stamp_layer(t, "CARBON MONOXIDE", word_t("killer", "carbon"), 540, 620, 82, (90, 200, 80), -6),
            E.title_layer(t, [("NO SMELL. NO COLOR.", 70, 800, E.WHITE, word_t("killer", "smell"))])]
    return img, (lerp(1.0, 1.1, k), 540, lerp(960, 1010, k)), lays


def sc_late(t, f):
    t0, t1 = CUTS[2], CUTS[3]
    img = plate("C")
    td = word_t("late", "dizzy")
    sway = ramp(t, td - 0.3, 0.8)
    pose = dict(eyes="squint" if t < td else "closed" if math.sin(t * 7) > 0.3 else "squint", brows="sad", mouth="O", amt=0.6,
                look=(0, 0.2), hands=[(-10, -60), (-60, 90)], lean=sway * 9 * math.sin(t * 2.6), tilt=sway * 12 * math.sin(t * 3.1 + 1))
    img = char(img, HERO, 540, 1700, 1.45, pose, t, rim_col=(0.7, 1.0, 0.6))

    def spiral(c):
        if sway <= 0:
            return
        for k in range(3):
            ang = t * 300 + k * 120
            c.save()
            c.translate(540 + 150 * math.cos(math.radians(ang)), 960 + 40 * math.sin(math.radians(ang)) - 30)
            c.drawString("*", -12, 12, skia.Font(T.FB, 50), P(C(255, 240, 150, int(220 * sway))))
            c.restore()
        gas(c, t, 900, 1850, 1.0, 3)
    img = layer_over(img, spiral)
    lays = [E.stamp_layer(t, "TOO LATE", word_t("late", "late"), 540, 520, 130)]
    k = smooth((t - t0) / (t1 - t0))
    return img, (lerp(1.05, 1.18, k), 540, lerp(1000, 1040, k)), lays


DEBRIS = None


def sc_blast(t, f):
    """Explosion at the far end of the tunnel: flash, shock dust, debris on real ballistic arcs onto the floor."""
    global DEBRIS
    t0, t1 = CUTS[3], CUTS[4]
    tb = word_t("afterdamp", "explosion")
    img = plate("A")
    fl = math.exp(-max(0.0, t - tb) / 0.18) if t >= tb else 0.0
    if fl > 0:
        g = E.glow_map(VP_A[0], VP_A[1], 420, 360)
        img[..., :3] = np.clip(img[..., :3] + fl * 1.3 * g[..., None] * np.array([1.0, 0.62, 0.25], np.float32), 0, 1)
    if DEBRIS is None:
        r = random.Random(11)
        DEBRIS = [(r.uniform(-1, 1) * 900, -r.uniform(500, 1300), r.uniform(10, 26), r.uniform(0, 360), r.uniform(-900, 900)) for _ in range(26)]
    floor_y = 1520.0
    g_px = 3600.0     # px/s^2: the tunnel cap beam (~2 m) spans ~1000 px here -> 9.81 m/s^2 * 500 px/m ~ 4900; perspective-depth ~0.75

    def fx(c):
        if t < tb:
            return
        u = t - tb
        for vx, vy, sz, rot0, w in DEBRIS:
            x0, y0 = VP_A[0], VP_A[1]
            sc_ = 0.4 + 0.7 * min(1.0, u / 0.9)                # comes toward the camera, lands mid-tunnel
            x = x0 + vx * u * sc_ * 0.6
            y = y0 + vy * u + 0.5 * g_px * u * u
            if y > floor_y:                                    # lands and stays on the floor (no sink)
                y = floor_y
            c.save()
            c.translate(x, y)
            c.rotate(rot0 + (w * u if y < floor_y else w * 0.4))
            c.drawRect(skia.Rect(-sz * sc_, -sz * 0.6 * sc_, sz * sc_, sz * 0.6 * sc_), P(C(40, 32, 28)))
            c.drawRect(skia.Rect(-sz * sc_, -sz * 0.6 * sc_, sz * sc_, sz * 0.6 * sc_), S(INK, 3))
            c.restore()
        d = clamp(u / 1.2)
        c.drawCircle(VP_A[0], VP_A[1], 200 + 700 * d, P(C(170, 140, 110, int(150 * (1 - d) * 0.8)), MaskFilter=BLUR(60)))
        gas(c, t, 700, 1850, ramp(t, tb + 0.8, 1.5), 4)
    img = layer_over(img, fx)          # debris + dust land BEHIND the miners (floor y 1520 < their feet 1760): drawn first
    cower = ramp(t, tb, 0.25)
    for lk, x, s_, ph in ((PAL, 300, 1.2, 0.0), (OLD, 760, 1.25, 1.3)):
        pose = dict(eyes="wide" if cower > 0.5 else "open", brows="up" if cower > 0.5 else "flat", mouth="O" if cower > 0.5 else "smile",
                    hands=[(lerp(-20, 30, cower), lerp(150, -95, cower)), (lerp(20, -30, cower), lerp(150, -95, cower))],
                    lean=lerp(0, -8 if x < 540 else 8, cower), tilt=4 * math.sin(t * 2 + ph), squash=0.08 * cower)
        img = char(img, lk, x, 1760, s_, pose, t)
    PHYS["blast_floor"] = floor_y
    lays = [E.title_layer(t, [("EXPLOSION!", 130, 380, E.RED, tb)]),
            E.title_layer(t, [("THE GAS KILLED MORE", 74, 560, E.WHITE, word_t("afterdamp", "killed")),
                              ("THAN THE BLAST", 92, 670, E.GOLD, word_t("afterdamp", "blast"))])]
    sh = (0, 0)
    if tb <= t < tb + 0.6:
        a = (1 - (t - tb) / 0.6) * 18
        sh = (a * noise1(t, 5, 30), a * noise1(t, 6, 30))
    k = smooth((t - t0) / (t1 - t0))
    return img, (lerp(1.0, 1.08, k), 540 + sh[0], 960 + sh[1]), lays


def sc_haldane(t, f):
    t0, t1 = CUTS[4], CUTS[5]
    img = plate("D")
    th = word_t("haldane", "himself")
    dz = ramp(t, th - 0.1, 0.5)
    pose = dict(eyes="closed" if dz > 0.5 and math.sin(t * 6) > 0.2 else ("squint" if dz > 0.3 else "open"), brows="up" if dz < 0.3 else "sad",
                mouth="smile" if dz < 0.3 else "O", amt=0.5, look=(0.6, -0.2), hands=[(-25, 120), (50, -105)],
                lean=dz * 6 * math.sin(t * 2.4), tilt=lerp(-4, 14 * math.sin(t * 2.8), dz))
    x, y, s_ = 560, 1690, 1.3

    def flask(c):
        hx, hy = T.hand_pos(x, y, s_, pose, 1)
        c.save()
        c.translate(hx, hy - 20)
        p = skia.Path()
        p.moveTo(-12, -60)
        p.lineTo(-12, -20)
        p.lineTo(-40, 30)
        p.quadTo(0, 44, 40, 30)
        p.lineTo(12, -20)
        p.lineTo(12, -60)
        p.close()
        c.drawPath(p, P(C(170, 230, 160, 160)))
        c.drawPath(p, S(INK, 6))
        c.drawString("CO", -18, 24, skia.Font(T.FB, 22), P(C(30, 70, 30)))
        for k in range(3):     # a wisp drifting from the flask to his nose
            ph = (t * 0.9 + k / 3) % 1.0
            c.drawCircle(-10 - 40 * ph, -70 - 70 * ph, 10 + 10 * ph, P(C(150, 230, 120, int(120 * math.sin(math.pi * ph))), MaskFilter=BLUR(8)))
        c.restore()
    img = char(img, HALDANE, x, y, s_, pose, t, extra=flask, rim_col=(1.0, 0.7, 0.4))
    lays = [E.title_layer(t, [("JOHN HALDANE", 110, 340, E.GOLD, word_t("haldane", "haldane", "john")),
                              ("1890s SCIENTIST", 64, 440, E.WHITE, word_t("haldane", "scientist"))]),
            E.stamp_layer(t, "ON HIMSELF!", th, 540, 650, 120)]
    k = smooth((t - t0) / (t1 - t0))
    return img, (lerp(1.0, 1.12, k), 560, lerp(980, 1060, k)), lays


def sc_mice(t, f):
    t0, t1 = CUTS[5], CUTS[6]
    img = plate("D")
    tc = word_t("mice", "canary")
    cg = snap(t, tc - 0.1, 8)
    x, y, s_ = 560, 1760, 1.3
    pose = dict(eyes="open" if t < tc else "squint", brows="flat" if t < tc else "smug", mouth="smile" if t < tc else "grin",
                look=(-0.7, -0.2) if t < tc else (0.7, -0.1), hands=[(-90, -40), (40, 130)] if t < tc else [(-30, 120), (95, -60)],
                tilt=6 if t < tc else -6)
    img = char(img, HALDANE, x, y, s_, pose, t)
    hl, hr = T.hand_pos(x, y, s_, pose, -1), T.hand_pos(x, y, s_, pose, 1)

    def props(c):
        if t < tc:
            mouse_box(c, hl[0], hl[1] + 40, 1.5, t, asleep=True)
        else:
            cage(c, hr[0], hr[1] - 12, 1.45 * cg, t, bird=dict(sing=t > word_t("mice", "sang")), notes=True)
    img = layer_over(img, props)
    lays = [E.title_layer(t, [("MICE?", 130, 360, E.WHITE, word_t("mice", "mice"))]),
            E.title_layer(t, [("CANARY!", 140, 520, E.GOLD, tc)])]
    k = smooth((t - t0) / (t1 - t0))
    return img, (lerp(1.0, 1.08, k), 540, lerp(980, 1020, k)), lays


def _plate_b_world(t, bird, swing=0.0, bg_pose=None, gas_amt=0.0):
    img = plate("B")
    if bg_pose:
        img = char(img, HERO, 290, 1560, 1.15, bg_pose, t, blur=6 * K)
    img = layer_over(img, lambda c: (gas(c, t, 1500, 1950, gas_amt, 7), cage(c, HOOK_B[0], HOOK_B[1] + 14, 2.6, t, swing=swing, bird=bird),
                                     dust(c, t, 25, 2, (200, 240, 180))))
    return img


def sc_alarm(t, f):
    t0, t1 = CUTS[6], CUTS[7]
    img = _plate_b_world(t, dict(sing=True), swing=2.5 * math.sin(t * 2.2))
    lays = [E.title_layer(t, [("THE PERFECT", 96, 330, E.WHITE, word_t("alarm", "perfect")),
                              ("ALARM", 170, 500, E.GOLD, word_t("alarm", "alarm"))])]
    k = smooth((t - t0) / (t1 - t0))
    return img, (lerp(1.0, 1.1, k), lerp(540, HOOK_B[0], k), lerp(960, HOOK_B[1] + 230, k)), lays


def sc_first(t, f):
    t0, t1 = CUTS[7], CUTS[8]
    img = _plate_b_world(t, dict(sing=True, breathe=0.06), swing=2.0 * math.sin(t * 2.2), gas_amt=ramp(t, word_t("first", "gas"), 0.8))
    lays = [E.title_layer(t, [("BREATHES FAST", 92, 330, E.WHITE, word_t("first", "breathe")),
                              ("GAS HITS IT FIRST", 92, 450, E.GOLD, word_t("first", "first"))])]
    k = smooth((t - t0) / (t1 - t0))
    return img, (lerp(1.1, 1.22, k), HOOK_B[0], HOOK_B[1] + 240), lays


def sc_fall(t, f):
    t0, t1 = CUTS[8], CUTS[9]
    ts = word_t("stopped", "stopped")
    tfall = word_t("stopped", "fell")
    sing = t < ts
    y, rot = cage_fall(t - tfall)
    tsw = max(0.0, t - tfall)
    swing = 2.0 * math.sin(t * 2.2) + (5.0 * math.sin(5.7 * tsw) * math.exp(-tsw / 0.9) if t > tfall else 0.0)   # pendulum: L=0.3 m
    turn = ramp(t, ts + 0.1, 0.3)
    bgp = dict(eyes="wide" if t > ts else "open", brows="sad" if t > ts else "flat", mouth="O" if t > ts else "smile",
               look=(lerp(0, 0.9, turn), -0.2), hands=[(-40, 120), (40, 120)], tilt=lerp(0, 10, turn))
    img = _plate_b_world(t, dict(sing=sing, y=y, rot=rot, eyes="open" if t < tfall else "x"), swing, bgp, gas_amt=1.0)
    lays = [E.title_layer(t, [("SILENCE...", 110, 360, E.WHITE, ts + 0.15)])]
    return img, (1.22, HOOK_B[0], HOOK_B[1] + 250), lays


def sc_run(t, f):
    t0, t1 = CUTS[9], CUTS[10]
    ts = t - t0
    img = plate("C")
    order = []
    for idx, (dx, ph) in enumerate(((-250, 0.0), (0, 0.9), (250, 1.7))):
        prog = min(1.0, ts / (2.6 + 0.3 * idx))
        sc_ = lerp(0.62, 1.32, prog ** 1.2)
        order.append((sc_, 540 + dx * (0.55 + 0.6 * prog) + 18 * math.sin(ts * 2 + ph), lerp(1380, 1990, prog ** 1.2), ph, idx))
    for sc_, fx, fy, ph, idx in sorted(order):
        w = 2 * math.pi * 3.0 * ts + ph
        pose = dict(eyes="wide", brows="up", mouth="O", amt=1.3, look=(0, -0.2), walk=w,
                    hands=[(-60 + 25 * math.sin(w * 2), -150), (60 - 25 * math.sin(w * 2 + 1), -150)], lean=-5 + 3 * math.sin(2 * w),
                    tilt=6 * math.sin(w))
        lk = (PAL, HERO, OLD)[idx]
        img = char(img, lk, fx, fy, sc_, pose, t, shadow=0.45)
    img = layer_over(img, lambda c: gas(c, t, 900, 1500, 1.0, 9))
    lays = [E.stamp_layer(t, "GET OUT!", word_t("stopped", "out", "got"), 540, 520, 140),
            E.title_layer(t, [("FAST.", 150, 760, E.RED, word_t("stopped", "fast"))])]
    n = random.Random(int(t * 30))
    sh = (6 * math.sin(t * 23) + 2 * n.uniform(-1, 1), 5 * math.sin(t * 19 + 1) + 2 * n.uniform(-1, 1))
    return img, (lerp(1.0, 1.06, clamp(ts / 2)), 540 + sh[0], 960 + sh[1]), lays


def sc_law(t, f):
    t0, t1 = CUTS[10], CUTS[11]
    img = plate("A")
    t11 = word_t("law", "eleven", "1911")
    pose = dict(eyes="open", brows="up", mouth="smile", look=(0.6, -0.2), hands=[(-30, 110), (100, -60)], tilt=-4)
    x, y, s_ = 330, 1720, 1.3
    img = char(img, HERO, x, y, s_, pose, t)
    hx, hy = T.hand_pos(x, y, s_, pose, 1)
    sl = snap(t, word_t("law", "british", "law") - 0.05, 9)
    img = layer_over(img, lambda c: (cage(c, hx, hy - 8, 1.3, t), parchment(c, lerp(1500, 720, sl), 1130, 1.05, lerp(25, -6, sl))))
    lays = [E.stamp_layer(t, "1911", t11, 720, 560, 150), E.title_layer(t, [("BRITISH LAW", 96, 330, E.WHITE, word_t("law", "british"))])]
    k = smooth((t - t0) / (t1 - t0))
    return img, (lerp(1.0, 1.08, k), 560, 980), lays


def sc_twist(t, f):
    t0, t1 = CUTS[11], CUTS[12]
    img = plate("A")
    tox = word_t("twist", "special", "cage")
    hug = t < tox
    pose = dict(eyes="squint" if hug else "open", brows="sad" if hug else "up", mouth="smile", look=(0.2, 0.2),
                hands=[(10, -10), (-10, -10)] if hug else [(-20, 40), (20, 40)], tilt=8 if hug else -4)
    up = snap(t, tox - 0.05, 9)
    x, y, s_ = lerp(540, 360, up), 1760, 1.4
    if not hug:
        pose["hands"] = [(-20, 120), (110, -20)]
    img = char(img, HERO, x, y, s_, pose, t)

    def props(c):
        if hug:
            cage(c, 540, 1345, 1.25, t, swing=0, bird=dict(sing=True), notes=False)
            for k in range(3):    # hearts
                ph = (t * 0.8 + k / 3) % 1.0
                hx, hy = 680 + 30 * k, 1050 - 160 * ph
                hp = skia.Path()
                hp.moveTo(hx, hy + 18)
                hp.cubicTo(hx - 34, hy - 6, hx - 14, hy - 30, hx, hy - 12)
                hp.cubicTo(hx + 14, hy - 30, hx + 34, hy - 6, hx, hy + 18)
                c.drawPath(hp, P(C(240, 70, 90, int(230 * math.sin(math.pi * ph)))))
        else:
            resus_cage(c, 780, lerp(1960, 1640, up), 1.35, t, door=1.0, bird=dict(sing=True, eyes="open", y=rest_y(0, -4.0), x=34))
    img = layer_over(img, props)
    lays = [E.title_layer(t, [("THE TWIST", 140, 360, E.GOLD, word_t("twist", "twist"))]),
            E.title_layer(t, [("OXYGEN CAGE", 100, 520, E.WHITE, word_t("twist", "oxygen"))])]
    k = smooth((t - t0) / (t1 - t0))
    return img, (lerp(1.0, 1.1, k), 540, lerp(960, 1040, k)), lays


def sc_revive(t, f):
    t0, t1 = CUTS[12], CUTS[13]
    img = E.gblur(plate("A"), 7 * K)
    ts, to, tw = word_t("revive", "shut"), word_t("revive", "opened"), word_t("revive", "woke")
    # door: swings shut (damped, closes in 6 frames with a tiny rebound), valve turns one full turn over 0.5 s
    dk = (t - ts) / (6 / FPS)
    door = 1.0 if t < ts else max(0.0, 1 - dk) if dk < 1 else 0.04 * math.exp(-(t - ts - 0.2) / 0.08) * abs(math.sin((t - ts) * 40))
    valve = clamp((t - to) / 0.5)
    flow = ramp(t, to + 0.2, 0.4)
    # bird: lying (fainted) until "woke", then a real hop from lying to standing (v0 so it rises 30 units and lands)
    tj = t - tw
    if tj < 0:
        bird = dict(sing=False, eyes="shut", rot=95, y=rest_y(95, -4.0), x=34)
    else:
        g = 4905.0
        v0 = math.sqrt(2 * g * 30)
        tt = 2 * v0 / g
        jy = max(0.0, v0 * tj - 0.5 * g * tj * tj) if tj < tt else 0.0
        rot_ = 95 * (1 - smooth(clamp(tj / tt)))
        bird = dict(sing=tj > tt, eyes="open", rot=rot_, y=rest_y(rot_, -4.0) - jy, x=34, flap=abs(math.sin(tj * 30)) if tj < tt else 0)
        PHYS.setdefault("hop", dict(v0=v0, t_air=tt))
    img = layer_over(img, lambda c: resus_cage(c, 540, 1500, 3.0, t, door=door, valve=valve, flow=flow, bird=bird))
    sp = []
    if tj > 0.15:
        def sparkle(c):
            r = random.Random(4)
            for k in range(8):
                T.sparkle(c, 540 + r.uniform(-220, 220), 1180 + r.uniform(-160, 160), 18 + 8 * math.sin(t * 6 + k))
        img = layer_over(img, sparkle)
    lays = [E.stamp_layer(t, "IT WOKE UP!", tw, 540, 400, 120, (40, 170, 70), -6)]
    if t < tw - 0.03:
        lays = [E.title_layer(t, [("SHUT THE DOOR", 84, 330, E.WHITE, ts), ("OPEN THE OXYGEN", 84, 440, E.WHITE, to)])]
    return img, (1.0, 540, 1000), lays


def sc_retire(t, f):
    t0, t1 = CUTS[13], CUTS[14]
    img = plate("E")
    te = word_t("retire", "electronic")
    pose = dict(eyes="open" if t < te else "squint", brows="up", mouth="smile" if t < te else "grin", look=(0.5, -0.1),
                hands=[(-30, 110), (70, -40)], tilt=-4)
    x, y, s_ = 470, 1740, 1.38
    img = char(img, HERO, x, y, s_, pose, t, rim_col=(0.75, 0.85, 1.0))
    hx, hy = T.hand_pos(x, y, s_, pose, 1)
    det = snap(t, te - 0.05, 8)

    def props(c):
        if det > 0:
            detector(c, hx + 10, hy + 20, 1.2 * det, t, te + 0.3)
        # the canary, retired: perched on top of his helmet, singing
        canary(c, x - 10, y - 545 * s_ / 1.38, 1.3, t, sing=True)
    img = layer_over(img, props)
    lays = [E.stamp_layer(t, "1986", word_t("retire", "eighty", "1986", "nineteen", nth=1), 760, 520, 150),
            E.title_layer(t, [("RETIRED", 140, 330, E.GOLD, word_t("retire", "kept"))])]
    k = smooth((t - t0) / (t1 - t0))
    return img, (lerp(1.0, 1.1, k), 520, lerp(980, 1030, k)), lays


def sc_cta(t, f):
    from cta2 import draw_cta2
    img, cam, _ = sc_retire(min(t, CUTS[14] - 0.01), f)
    img = E.gblur(img, 10)
    img[..., :3] *= 0.6
    t0 = line_t("cta") - 0.12
    s, c = E.surf(world=False)
    draw_cta2(c, t - t0, word_t("cta", "like") - t0, word_t("cta", "subscribe") - t0)
    return img, (1.1, 520, 1030), [E.arr(s)]


RENDER = dict(hook=sc_hook, killer=sc_killer, late=sc_late, blast=sc_blast, haldane=sc_haldane, mice=sc_mice, alarm=sc_alarm,
              first=sc_first, fall=sc_fall, run=sc_run, law=sc_law, twist=sc_twist, revive=sc_revive, retire=sc_retire, cta=sc_cta)
NO_SPLAT = {"run", "cta"}     # "stopped" -> run is a hard smash-cut on the word; the CTA fades


def splat_cuts():
    return [CUTS[i] for i in range(1, len(SCENES)) if SCENES[i][0] not in NO_SPLAT]


def splat_layer(t):
    """Gold ink splat wipe: grows over 4 frames to cover the cut, clears over 5 frames (the channel's transition)."""
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


def render(f, out=None):
    t = f / FPS
    name = SCENES[scene_at(t)][0]
    img, (z, cx, cy), lays = RENDER[name](t, f)
    shake = (0, 0)
    for at in (word_t("late", "late"), word_t("haldane", "himself"), word_t("stopped", "out", "got"), word_t("retire", "eighty", "1986", "nineteen")):
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
    y, rot = cage_fall(10.0)
    r = math.radians(rot)
    low = y - 22 + max(px * math.sin(r) + py * math.cos(r) for px, py in _OUT)
    assert abs(low - FLOOR_Y) < 1e-9, "canary must rest exactly on the cage floor"
    for tf in np.linspace(0, 1.0, 301):        # never below the floor at any moment of the fall
        y_, r_ = cage_fall(tf)
        rr_ = math.radians(r_)
        assert y_ - 22 + max(px * math.sin(rr_) + py * math.cos(rr_) for px, py in _OUT) <= FLOOR_Y + 1e-9
    fall = PHYS["fall"]
    assert 0.1 < fall["t_land"] < 0.2, fall
    sc_revive(word_t("revive", "woke") + 0.05, 0)
    hop = PHYS["hop"]
    return dict(fall=fall, hop=hop, scenes=[(n, round(t0, 3)) for n, t0 in SCENES], dur=DUR)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "frames"
    rep = physics_report()
    json.dump(rep, open(os.path.join(D, "physics.json"), "w"), indent=1)
    print("duration", DUR, "s,", NF, "frames; physics", rep["fall"], rep["hop"])
    if mode == "stills":
        os.makedirs(os.path.join(D, "stills"), exist_ok=True)
        for ts in sys.argv[2].split(","):
            f = int(round(float(ts) * FPS))
            render(f, os.path.join(D, "stills", f"s_{float(ts):05.2f}.png"))
            print("still", ts, SCENES[scene_at(f / FPS)][0], flush=True)
    else:
        os.makedirs(OUT_FR, exist_ok=True)
        todo = [f for f in range(NF) if os.environ.get("SKIP") != "1" or not os.path.exists(os.path.join(OUT_FR, f"{f + 1:04d}.png"))]
        with Pool(int(os.environ.get("PROCS", "4"))) as pool:
            for j, _ in enumerate(pool.imap_unordered(render, todo, chunksize=4)):
                if j % 150 == 0:
                    print("frame", j, "/", len(todo), flush=True)
        print("done")
