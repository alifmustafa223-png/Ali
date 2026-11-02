"""YouTube Short #20: "Chewing Gum Exists Because of a DICTATOR" (Skia toon style, vidIQ "Chris" voice).

Animation upgrades over the pineapple video (see LESSONS.md 61+):
  - lip-sync: Santa Anna's mouth follows the real loudness of the narrator during his quote
  - walk cycles (legs swing around the hip, body bobs; stride tied to distance so feet never slide)
  - chewing jaws, hats with lag/spring, squash-and-stretch pop-ins on the spoken word
  - bubble-gum physics: a wobbling bubble that inflates and bursts into flying shreds on "dictator"
  - gum strings that stretch, thin out and snap; a rotating glowing DNA helix; melting experiments

Usage: python make_gum.py final.mp4 [scene,scene,...] [t1,t2,...]   (run inside dailymind/ultimate)
       stills mode: python make_gum.py x 0,1,2 0.5,2.0  -> gum_<scene>_<t>.png
"""
import json
import math
import os
import random
import subprocess
import sys

import numpy as np
import skia
from PIL import Image, ImageDraw

OUTFILE = sys.argv[1]
ONLY = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 and sys.argv[2][0].isdigit() else None
STILLS = sys.argv[3].split(",") if len(sys.argv) > 3 else None
sys.argv = [sys.argv[0], "base_gum.mp4"]
sys.path.insert(0, "..")

import audio  # noqa: E402
import make_ketchup  # noqa: E402
import make_salt  # noqa: E402
import make_short as base  # noqa: E402
import ultimate as U  # noqa: E402
from fx import impact  # noqa: E402
from make_honey import slam  # noqa: E402
from make_ketchup import splat, stamp  # noqa: E402
from make_short import FONT_B, FONT_M, F_MID, H, W, font, tag, text_block  # noqa: E402
from style import heading  # noqa: E402
from timing import Timeline  # noqa: E402
from toon import *  # noqa: E402,F401,F403

GOLD, PINK, RED = (255, 200, 60), (255, 120, 185), (235, 60, 60)
make_ketchup.SPLAT_COLOR = (250, 195, 50)
base.HOOK_SKIP = 0.0
base.CRF = 16
CUE = {}
VOICE_DIR = "../gum"

SANTA = dict(skin=(225, 175, 135), hair="neat", hair_col=(35, 28, 28), sideburns=True, coat=(30, 45, 95), trim=(235, 190, 80),
             pants=(235, 235, 230), collar=(200, 40, 50), hat="bicorne", epaulettes=True, medals=True, sash=(60, 140, 80), nose="long")
SANTA_OLD = dict(SANTA, hair="grey", hair_col=(185, 185, 190), coat=(60, 65, 85), sash=(90, 110, 95), medals=False)
ADAMS = dict(skin=(240, 195, 165), hair="grey", hair_col=(150, 140, 135), beard=(150, 140, 135), coat=(110, 80, 60), vest=(60, 45, 40),
             pants=(70, 60, 55), glasses=True, nose="long")
SCIENTIST = dict(skin=(245, 205, 175), hair="neat", hair_col=(200, 150, 80), coat=(245, 248, 250), pants=(60, 70, 90), glasses=True,
                 collar=(120, 170, 220), nose="small")
GREEK = dict(skin=(235, 185, 140), hair="curly", hair_col=(70, 45, 30), beard=(70, 45, 30), coat=(245, 240, 228), dress=(245, 240, 228),
             sash=(150, 60, 140), hat="laurel", nose="long")
GREEK2 = dict(skin=(245, 200, 160), hair="powder", hair_col=(60, 40, 30), coat=(220, 205, 170), dress=(220, 205, 170),
              sash=(60, 120, 170), nose="small")
GIRL = dict(skin=(250, 210, 180), hair="pigtails", hair_col=(120, 70, 40), coat=(240, 120, 160), dress=(240, 120, 160), nose="small", lips=True)
CLERK = dict(SHOP)
WRIGLEY = dict(skin=(240, 195, 165), hair="neat", hair_col=(60, 40, 30), coat=(70, 75, 90), vest=(170, 40, 50), pants=(60, 60, 70),
               hat="bowler", collar=(245, 245, 240), nose="long")


def blinking(t, ph=0.0):
    return ((t + ph) % 3.3) < 0.11


def pop_in(t, at, dur=0.35):
    """Scale for an object that pops in on a word: 0 before, overshoots, settles at 1."""
    return out_back((t - at) / dur, 2.2) if t > at else 0.0


# ---------- voice loudness for lip-sync ----------

VOX = None


def load_vox(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    hop = 16000 // 30
    n = len(x) // hop
    rms = np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1))
    rms = rms / max(1e-6, np.percentile(rms, 95))
    return np.clip(rms, 0, 1)


def vox(gt):
    """Narrator loudness 0..1 at global time gt (30 values per second)."""
    i = int(gt * 30)
    return float(VOX[i]) if VOX is not None and 0 <= i < len(VOX) else 0.0


def G(i, t):
    return CUE["S"][i] + t


# ---------- props ----------

def bubble(c, x, y, r, t, alpha=255):
    """Glossy bubble-gum bubble with a living wobble."""
    p = skia.Path()
    n = 48
    for k in range(n + 1):
        a = k / n * 2 * math.pi
        rr = r * (1 + 0.035 * math.sin(4 * a + t * 9) + 0.02 * math.sin(3 * a - t * 6))
        px, py = x + math.cos(a) * rr, y + math.sin(a) * rr * 0.96
        if k == 0:
            p.moveTo(px, py)
        else:
            p.lineTo(px, py)
    p.close()
    c.drawPath(p, P(Shader=rad(x - r * 0.35, y - r * 0.4, r * 1.5, [C(255, 190, 225, alpha), C(250, 120, 185, alpha), C(200, 60, 130, alpha)], [0, 0.55, 1])))
    c.drawPath(p, S(C(170, 40, 100, alpha), 4))
    c.drawOval(skia.Rect(x - r * 0.62, y - r * 0.7, x - r * 0.2, y - r * 0.42), P(C(255, 255, 255, int(alpha * 0.75))))
    c.drawCircle(x + r * 0.45, y + r * 0.42, r * 0.07, P(C(255, 255, 255, int(alpha * 0.5))))


def shreds(c, x, y, r, k, seed=1):
    """Bubble burst: pink shreds fly outward and fall (k = seconds since the pop)."""
    if not 0 <= k < 0.9:
        return
    rnd = random.Random(seed)
    a_ = int(255 * (1 - k / 0.9))
    for i in range(14):
        a = i / 14 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        v = rnd.uniform(600, 1100)
        px = x + math.cos(a) * (r * 0.8 + v * k)
        py = y + math.sin(a) * (r * 0.8 + v * k) + 900 * k * k
        c.save()
        c.translate(px, py)
        c.rotate(math.degrees(a) + k * 400 * (1 if i % 2 else -1))
        blob(c, oval(0, 0, 26 - 10 * k, 11), (250, 120, 185), 1.3, 0.7, outline=False)
        c.restore()
    if k < 0.15:
        glow(c, x, y, r * 1.6, (255, 200, 230), int(200 * (1 - k / 0.15)))


def gum_pack(c, x, y, s=1.0, rot=0.0, col=(250, 120, 185)):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    blob(c, rrect(-70, -28, 70, 28, 8), (245, 245, 240), 1.05, 0.8)
    c.drawRect(skia.Rect(-70, -12, 70, 12), P(C(*col)))
    c.drawRect(skia.Rect(-70, -28, -48, 28), P(C(*[v * 0.8 for v in col])))
    c.drawPath(rrect(-70, -28, 70, 28, 8), S(OUT, 4))
    c.restore()


def chicle(c, x, y, s=1.0, t=0.0):
    """A lumpy brown block of chicle sap."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    p = skia.Path()
    pts = [(-60, -30), (-35, -48), (5, -42), (45, -50), (62, -20), (58, 25), (20, 42), (-30, 38), (-62, 18)]
    p.moveTo(*pts[0])
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        p.quadTo(a[0] * 1.08, a[1] * 1.08, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    p.close()
    blob(c, p, (150, 100, 60), 1.35, 0.6)
    for k in range(4):
        c.drawCircle(-35 + k * 22, -10 + (k % 2) * 18, 5, P(C(110, 70, 40, 160)))
    c.restore()


def helix(c, cx, cy, h, t, a):
    """Rotating glowing DNA double helix (a = 0..1 fade/grow)."""
    if a <= 0:
        return
    n = 22
    pts = []
    for k in range(n):
        u = k / (n - 1)
        y = cy - h / 2 + u * h * a
        ph = u * 4 * math.pi + t * 2.2
        pts.append((y, math.sin(ph), math.cos(ph)))
    for y, sn, cs in pts:  # rungs (back first)
        x1, x2 = cx + sn * 90, cx - sn * 90
        c.drawLine(x1, y, x2, y, S(C(140, 230, 255, int(150 * a)), 6))
    for side in (1, -1):
        p = skia.Path()
        for k, (y, sn, cs) in enumerate(pts):
            x = cx + side * sn * 90
            (p.moveTo if k == 0 else p.lineTo)(x, y)
        c.drawPath(p, S(C(90, 220, 255, int(255 * a)), 12))
        c.drawPath(p, S(C(230, 250, 255, int(200 * a)), 4))
    for y, sn, cs in pts:
        for side in (1, -1):
            x = cx + side * sn * 90
            depth = 0.6 + 0.4 * (cs * side)
            c.drawCircle(x, y, 10 * depth + 4, P(C(255, 140 if side > 0 else 230, 200 if side > 0 else 120, int(255 * a))))
    glow(c, cx, cy, h * 0.8, (110, 220, 255), int(110 * a))


def lightbulb(c, x, y, s, t, at):
    k = pop_in(t, at)
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(s * k, s * k)
    glow(c, 0, 0, 260, (255, 240, 150), int(150 + 60 * math.sin(t * 12)))
    for i in range(8):
        a = i / 8 * 2 * math.pi + t
        c.drawLine(math.cos(a) * 95, math.sin(a) * 95, math.cos(a) * 140, math.sin(a) * 140, S(C(255, 235, 120), 8))
    blob(c, oval(0, -10, 62, 66), (255, 240, 140), 1.2, 0.8)
    blob(c, rrect(-30, 48, 30, 92, 8), (170, 170, 180), 1.4, 0.7)
    c.drawLine(-14, 10, 0, -20, S(C(230, 150, 40), 5))
    c.drawLine(0, -20, 14, 10, S(C(230, 150, 40), 5))
    c.restore()


def puff(c, x, y, k, col=(200, 200, 205)):
    """Smoke puff, k = seconds since it started."""
    if not 0 <= k < 1.2:
        return
    for i in range(6):
        a = i / 6 * 2 * math.pi
        r = 30 + 70 * ease(k / 0.8)
        c.drawCircle(x + math.cos(a) * r, y + math.sin(a) * r * 0.6 - 120 * k, 40 + 30 * k,
                     P(C(*col, int(170 * (1 - k / 1.2))), MaskFilter=blur(14)))


def rain(c, t, n=110, seed=4, col=(170, 190, 230)):
    r = random.Random(seed)
    for i in range(n):
        x0, y0, sp = r.uniform(-200, W), r.uniform(0, H), r.uniform(1500, 2300)
        y = (y0 + t * sp) % (H + 200) - 100
        x = x0 + (y / H) * 160
        c.drawLine(x, y, x + 10, y + 46, S(C(*col, 120), 2.5))


def heart(c, x, y, s, a=255):
    p = skia.Path()
    p.moveTo(x, y + 30 * s)
    p.cubicTo(x - 60 * s, y - 10 * s, x - 30 * s, y - 55 * s, x, y - 25 * s)
    p.cubicTo(x + 30 * s, y - 55 * s, x + 60 * s, y - 10 * s, x, y + 30 * s)
    p.close()
    c.drawPath(p, P(C(255, 90, 140, a)))


def mouth_pos(x, y, s):
    """Screen position of a person's mouth (feet at x, y; no lean/tilt)."""
    return x, y + s * (-262 - 70 + 88 * 0.55)


def head_top(y, s):
    return y + s * (-262 - 70 - 88)


# ---------- scenes ----------

def art_hook(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(40, 12, 20), C(95, 25, 35), C(35, 10, 18)])))
    for x in (80, 1000):  # gold pilasters
        c.drawRect(skia.Rect(x - 45, 250, x + 45, 1650), P(Shader=lin((x - 45, 0), (x + 45, 0), [C(110, 70, 25), C(235, 190, 100), C(100, 60, 20)])))
    # big framed map on the wall
    c.drawRect(skia.Rect(190, 870, 890, 1290), P(Shader=lin((190, 870), (890, 1290), [C(230, 200, 150), C(200, 165, 110)])))
    land = skia.Path()
    land.moveTo(230, 920)
    land.cubicTo(420, 900, 560, 960, 640, 1030)
    land.cubicTo(700, 1080, 760, 1150, 850, 1180)
    land.lineTo(820, 1230)
    land.cubicTo(700, 1210, 600, 1150, 520, 1090)
    land.cubicTo(430, 1030, 330, 1000, 230, 990)
    land.close()
    c.drawPath(land, P(C(170, 130, 80)))
    c.drawPath(land, S(C(120, 85, 50), 3))
    for k in range(5):  # little army flags pinned to the map
        fx, fy = 330 + k * 105, 960 + (k % 2) * 60 + k * 20
        c.drawLine(fx, fy, fx, fy - 50, S(C(60, 40, 30), 4))
        c.drawRect(skia.Rect(fx, fy - 50, fx + 32, fy - 30), P(C(200, 40, 50)))
    c.drawRect(skia.Rect(190, 870, 890, 1290), S(C(200, 150, 60), 14))
    c.drawRect(skia.Rect(0, 1600, W, H), P(Shader=lin((0, 1600), (0, H), [C(90, 40, 25), C(40, 18, 12)])))
    candle(c, 150, 1600, t, 0.0, 1.4)
    candle(c, 930, 1600, t, 2.0, 1.4)
    d_at, f_at = CUE["dict"], CUE["fail"]
    popped = t >= d_at
    x, y, s = 540, 1880, 1.75
    stomp = spring(t, f_at, 2.6, 5) if t > f_at else 0
    angry = popped
    pose = dict(eyes="squint" if angry else "open", brows="angry" if angry else "smug", mouth="frown" if angry else "chew",
                talk=t, look=(0, 0), blink=blinking(t, 0.6) and not angry,
                hands=[(-30, 150), (30, 150)] if not angry else [(-95, -10 + 30 * stomp), (95, -10 + 30 * stomp)],
                squash=0.05 * spring(t, d_at, 3, 4) + 0.06 * stomp, tilt=2 * math.sin(t * 1.7),
                hat_bounce=-25 * spring(t, d_at + 0.02, 2.2, 3.5))
    person(c, x, y, s, SANTA, pose, t)
    mx, my = mouth_pos(x, y, s)
    if not popped:  # bubble inflates from frame 0 and bursts exactly on "dictator"
        g = ease(t / d_at) if d_at > 0 else 1
        r = 40 + 150 * g
        bubble(c, mx, my + r * 0.75, r, t)
    else:
        k = t - d_at
        shreds(c, mx, my + 140, 170, k)
        # a sheet of burst gum stuck over his mouth and chin, with drips that stretch down
        sc = min(1, k / 0.1)
        sheet = skia.Path()
        pts = [(-95, -28), (-50, -52), (0, -40), (55, -55), (98, -25), (105, 25), (60, 48), (0, 40), (-60, 52), (-102, 22)]
        sheet.moveTo(mx + (pts[0][0] + pts[-1][0]) / 2 * sc, my + (pts[0][1] + pts[-1][1]) / 2 * sc)
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            sheet.quadTo(mx + a[0] * 1.1 * sc, my + a[1] * 1.1 * sc, mx + (a[0] + b[0]) / 2 * sc, my + (a[1] + b[1]) / 2 * sc)
        sheet.close()
        c.drawPath(sheet, P(Shader=rad(mx - 30, my - 30, 140, [C(255, 175, 215, 245), C(245, 105, 170, 245)])))
        c.drawPath(sheet, S(C(190, 50, 120), 4))
        c.drawOval(skia.Rect(mx - 60 * sc, my - 35 * sc, mx - 20 * sc, my - 20 * sc), P(C(255, 235, 245, 200)))
        for i, (dx, ln) in enumerate(((-55, 90), (10, 130), (65, 75))):  # drips
            dl = ln * ease((k - 0.05 * i) / 1.2) * sc
            if dl > 2:
                c.drawLine(mx + dx, my + 35, mx + dx, my + 35 + dl, S(C(245, 110, 175), 14 - 3 * i))
                c.drawCircle(mx + dx, my + 35 + dl, 10 - 2 * i, P(C(245, 110, 175)))
    if t > f_at:  # steam out of his ears
        for side in (-1, 1):
            hx = x + side * 92 * s
            for k in range(3):
                ph = ((t - f_at) * 1.6 + k / 3) % 1
                c.drawCircle(hx + side * ph * 60, my - 130 - ph * 160, 18 + 30 * ph, P(C(240, 240, 245, int(180 * (1 - ph))), MaskFilter=blur(8)))


def art_denmark(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(8, 22, 32), C(20, 50, 60), C(8, 18, 24)])))
    for row in range(3):  # shelves of specimen jars
        y = 980 + row * 200
        c.drawRect(skia.Rect(0, y, W, y + 14), P(C(50, 70, 75)))
        for k in range(8):
            x = 40 + k * 135 + (row % 2) * 50
            col = [(80, 160, 140), (150, 120, 70), (90, 110, 170)][(k + row) % 3]
            c.drawRoundRect(skia.Rect(x, y - 120 + (k % 2) * 25, x + 70, y), 14, 14, P(C(*col, 110)))
    c.drawRect(skia.Rect(0, 1560, W, H), P(Shader=lin((0, 1560), (0, H), [C(40, 55, 60), C(15, 22, 25)])))
    # table + velvet tray + bell jar
    blob(c, rrect(60, 1500, 760, 1580, 12), (110, 80, 55))
    c.drawRect(skia.Rect(100, 1580, 130, 1900), P(C(80, 55, 35)))
    c.drawRect(skia.Rect(690, 1580, 720, 1900), P(C(80, 55, 35)))
    blob(c, oval(400, 1495, 210, 34), (130, 30, 50), 1.3, 0.7)
    # the 5,700-year-old birch tar lump with tooth marks
    lump = skia.Path()
    lump.moveTo(320, 1480)
    lump.cubicTo(320, 1400, 480, 1390, 485, 1470)
    lump.cubicTo(470, 1500, 330, 1500, 320, 1480)
    lump.close()
    blob(c, lump, (45, 35, 30), 1.6, 0.6)
    for k in range(4):
        c.drawArc(skia.Rect(345 + k * 30, 1418, 370 + k * 30, 1446), 200, 140, False, S(C(110, 95, 85), 3))
    dna = CUE["dna"]
    hx = helix_a = ease((t - dna + 0.1) / 0.7)
    helix(c, 400, 1150, 380, t, helix_a)
    if hx > 0:
        burst(c, t, dna, 400, 1400, n=12, reach=220)
    jar = skia.Path()
    jar.moveTo(230, 1490)
    jar.lineTo(230, 1300)
    jar.cubicTo(230, 1180, 570, 1180, 570, 1300)
    jar.lineTo(570, 1490)
    c.drawPath(jar, P(C(200, 240, 255, 40)))
    c.drawPath(jar, S(C(200, 240, 255, 150), 5))
    c.drawLine(270, 1300, 270, 1450, S(C(255, 255, 255, 120), 8))
    # scientist leaning in with a magnifying glass
    shock = t > dna
    jump = spring(t, dna, 2.4, 4) if shock else 0
    pose = dict(lean=-8 + 6 * jump, hands=[(-170, -20), (-30, 140)], eyes="wide" if shock else "open", brows="up" if shock else "flat",
                mouth="O" if shock else "smile", look=(-1, 0.4), blink=blinking(t, 0.2) and not shock, squash=-0.04 * jump)
    px, py, ps = 800, 1880 - 30 * max(0, jump), 1.45
    person(c, px, py, ps, SCIENTIST, pose, t)
    hx_, hy_ = hand_pos(px, py, ps, pose, -1)
    c.drawLine(hx_, hy_, hx_ - 40, hy_ + 80, S(C(60, 45, 35), 16))
    c.drawCircle(hx_ - 70, hy_ - 50, 70, P(C(200, 240, 255, 60)))
    c.drawCircle(hx_ - 70, hy_ - 50, 70, S(C(200, 170, 80), 12))
    c.drawArc(skia.Rect(hx_ - 120, hy_ - 100, hx_ - 40, hy_ - 20), 200, 60, False, S(C(255, 255, 255, 180), 6))


def art_greece(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, 1500), [C(30, 30, 70), C(170, 90, 110), C(250, 170, 100)], [0, 0.6, 1])))
    glow(c, 540, 1300, 520, (255, 190, 120), 120)
    # temple
    c.drawRect(skia.Rect(90, 960, 990, 1020), P(C(225, 215, 200)))
    tri = skia.Path()
    tri.moveTo(70, 965)
    tri.lineTo(540, 880)
    tri.lineTo(1010, 965)
    tri.close()
    blob(c, tri, (230, 220, 205), 1.05, 0.8)
    for k in range(6):
        x = 150 + k * 156
        c.drawRect(skia.Rect(x - 34, 1020, x + 34, 1560), P(Shader=lin((x - 34, 0), (x + 34, 0), [C(170, 160, 150), C(245, 238, 225), C(160, 150, 140)])))
        for j in range(4):
            c.drawLine(x - 22 + j * 15, 1035, x - 22 + j * 15, 1545, S(C(150, 140, 130, 120), 3))
    c.drawRect(skia.Rect(60, 1560, 1020, 1600), P(C(210, 200, 185)))
    c.drawRect(skia.Rect(0, 1600, W, H), P(Shader=lin((0, 1600), (0, H), [C(200, 170, 130), C(140, 110, 80)])))
    fr = CUE["fresh"]
    # Greek chewing resin, then breathes out a sparkly fresh breath
    exhale = ease((t - fr) / 0.5)
    pose = dict(mouth="O" if fr < t < fr + 1.6 else "chew", talk=t, eyes="closed" if t > fr + 1.6 else "open", brows="smug",
                look=(1, 0), hands=[(30, 150), (110, 20)], tilt=3 * math.sin(t * 1.9), blink=blinking(t, 1.1))
    person(c, 330, 1860, 1.5, GREEK, pose, t)
    mx, my = mouth_pos(330, 1860, 1.5)
    if exhale > 0 and t < fr + 2.2:
        for k in range(16):
            u = ((t - fr) * 1.4 + k / 16) % 1
            if (t - fr) * 1.4 < k / 16:
                continue
            sx = mx + 40 + u * 330
            sy = my + math.sin(u * 7 + k) * 40 - u * 40
            sparkle(c, sx, sy, 9 * (1 - u) + 4, int(230 * (1 - u)), (170, 255, 230))
    sniff = ease((t - fr - 0.6) / 0.4)
    p2 = dict(mouth="grin" if sniff > 0.5 else "smile", eyes="closed" if sniff > 0.5 else "open", brows="up" if sniff > 0.5 else "flat",
              look=(-1, 0), hands=[(-20, 150), (40 - 30 * sniff, 150 - 260 * sniff)], tilt=-6 * sniff + 2 * math.sin(t * 2.3),
              blink=blinking(t, 0.4))
    person(c, 790, 1860, 1.45, GREEK2, p2, t)
    if sniff > 0.5:
        for k in range(3):
            heart(c, 790 + (k - 1) * 70, head_top(1860, 1.45) - 40 - ((t * 60 + k * 30) % 90), 0.7, 220)
    # resin drops on the tree branch at the edge
    c.drawLine(1080, 1100, 900, 1180, S(C(90, 60, 40), 26))
    for k in range(3):
        y = 1185 + k * 8 + 30 * ((t * 0.5 + k * 0.3) % 1)
        c.drawCircle(940 + k * 45, y, 11, P(C(255, 210, 120, 230)))


def art_newyork(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(10, 12, 30), C(30, 35, 60), C(15, 15, 25)])))
    c.drawCircle(860, 980, 55, P(C(240, 240, 220)))
    glow(c, 860, 980, 230, (200, 210, 255), 70)
    for k, (x0, w, h, col) in enumerate([(0, 300, 700, (110, 60, 50)), (300, 260, 640, (95, 55, 48)), (560, 280, 740, (120, 70, 55)), (840, 260, 660, (100, 58, 50))]):
        top = 1620 - h
        c.drawRect(skia.Rect(x0, top, x0 + w, 1620), P(Shader=lin((x0, 0), (x0 + w, 0), [C(*col), C(*[v * 0.75 for v in col])])))
        c.drawRect(skia.Rect(x0, top, x0 + w, top + 22), P(C(60, 40, 35)))
        for r in range(4):
            for j in range(2):
                wx, wy = x0 + 50 + j * (w - 140), top + 80 + r * 150
                if wy > 1450:
                    continue
                lit = (k + r + j) % 3 != 0
                c.drawRect(skia.Rect(wx, wy, wx + 70, wy + 100), P(C(255, 200, 110) if lit else C(40, 40, 60)))
                if lit:
                    glow(c, wx + 35, wy + 50, 90, (255, 190, 100), int(60 * flicker(t, k + r)))
    c.drawRect(skia.Rect(0, 1620, W, H), P(Shader=lin((0, 1620), (0, H), [C(55, 55, 65), C(25, 25, 30)])))
    for k in range(6):  # wet street reflections
        c.drawRect(skia.Rect(80 + k * 170, 1700 + (k % 2) * 60, 160 + k * 170, 1712 + (k % 2) * 60), P(C(255, 200, 120, 60)))
    for lx in (120, 960):  # gas lamps
        c.drawLine(lx, 1640, lx, 1180, S(C(30, 30, 35), 14))
        blob(c, rrect(lx - 30, 1110, lx + 30, 1190, 8), (40, 40, 45))
        c.drawRect(skia.Rect(lx - 20, 1122, lx + 20, 1178), P(C(255, 220, 140)))
        glow(c, lx, 1150, 280, (255, 200, 110), int(150 * flicker(t, lx)))
    # Santa Anna walks in from the left (stride tied to distance: no sliding feet)
    arrive = 2.6
    x = -160 + 700 * ease(min(1, t / arrive))
    moving = t < arrive
    walk = (x + 160) / 40 if moving else None
    turned = t > CUE["santa"]
    pose = dict(walk=walk, hands=[(-30 + (25 * math.sin(walk) if walk else 0), 150), (30 - (25 * math.sin(walk) if walk else 0), 150)],
                eyes="open", brows="angry", mouth="chew", talk=t, look=(1 if moving else 0, 0), blink=blinking(t, 0.3),
                tilt=(3 * math.sin(walk * 2) if walk else 0) + (4 * spring(t, CUE["santa"], 2, 4) if turned else 0),
                hat_bounce=(4 * math.sin(walk * 2) if walk else 0) - 8 * spring(t, arrive, 2.5, 4))
    person(c, x, 1850, 1.5, SANTA, pose, t)
    rain(c, t, 70, 9, (160, 170, 210))


def art_pitch(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(45, 30, 25), C(90, 60, 40), C(40, 25, 20)])))
    for k in range(12):
        c.drawLine(k * 100, 900, k * 100, 1600, S(C(60, 40, 28), 6))
    c.drawRect(skia.Rect(0, 1600, W, H), P(Shader=lin((0, 1600), (0, H), [C(110, 75, 45), C(60, 40, 25)])))
    # window with gears / tools on the wall
    for gx, gy, gr, sp in ((900, 1000, 70, 1.2), (990, 1090, 45, -1.9)):
        c.save()
        c.translate(gx, gy)
        c.rotate(math.degrees(t * sp))
        for i in range(10):
            c.save()
            c.rotate(i * 36)
            c.drawRect(skia.Rect(-10, -gr - 16, 10, -gr + 4), P(C(150, 120, 70)))
            c.restore()
        c.drawCircle(0, 0, gr, P(C(160, 130, 75)))
        c.drawCircle(0, 0, gr * 0.35, P(C(70, 50, 30)))
        c.restore()
    hang = ease((t - 0.2) / 0.5)
    lamp_x, lamp_y = 170 + 8 * math.sin(t * 1.4), 930
    c.drawLine(170, 860, lamp_x, lamp_y, S(C(40, 30, 25), 5))
    blob(c, rrect(lamp_x - 40, lamp_y, lamp_x + 40, lamp_y + 70, 12), (60, 45, 30))
    c.drawRect(skia.Rect(lamp_x - 28, lamp_y + 12, lamp_x + 28, lamp_y + 60), P(C(255, 215, 130)))
    glow(c, lamp_x, lamp_y + 60, 520, (255, 190, 110), int(130 * flicker(t, 3) * hang + 40))
    gave, chic, turn, rich, army = CUE["gave"], CUE["chicle"], CUE["turn"], CUE["rich"], CUE["army"]
    # Santa Anna offers the chicle, then talks (mouth follows the narrator's real loudness)
    talking = turn - 0.05 < t < CUE["d"][4] - 0.25
    reach = ease((t - gave + 0.1) / 0.5)
    gesture = math.sin(t * 5) if talking else 0
    sp = dict(hands=[(70 + 70 * reach, 110 - 70 * reach) if not talking else (-90 + 20 * gesture, -40 - 35 * gesture), (30, 150) if not talking else (100, 30 + 25 * gesture)],
              eyes="open", brows="up" if talking else "smug", mouth="talk" if talking else "chew",
              talk=vox(G(4, t)) if talking else t, look=(1, 0), tilt=4 * math.sin(t * 2.1) + (3 * gesture if talking else 0),
              blink=blinking(t, 0.9), hat_bounce=3 * gesture)
    person(c, 300, 1860, 1.4, SANTA, sp, t)
    ap = dict(hands=[(-60 - 40 * ease((t - turn) / 0.5), 80), (-20, 150)], eyes="wide" if t > chic else "open", brows="up",
              mouth="O" if t > rich else "smile", look=(-1, 0.3), tilt=-3 * math.sin(t * 1.6), blink=blinking(t, 0.1))
    person(c, 790, 1860, 1.45, ADAMS, ap, t)
    # the block of chicle: pops into Santa Anna's hand on "gave", passes to Adams when the pitch starts
    sx, sy = hand_pos(300, 1860, 1.4, dict(sp, hands=[(140, 40), (30, 150)]), -1)
    ax_, ay_ = hand_pos(790, 1860, 1.45, ap, -1)
    move = ease((t - turn) / 0.6)
    bx, by = sx + (ax_ - sx) * move, sy - 40 + (ay_ - sy) * move - 120 * math.sin(math.pi * move)
    sc = pop_in(t, gave)
    if sc > 0:
        chicle(c, bx, by, 0.9 * sc, t)
        if chic < t < chic + 1.2:
            for k in range(6):
                a = t * 2 + k * 1.05
                sparkle(c, bx + math.cos(a) * 85, by + math.sin(a) * 60, 8, 220)
    # thought bubble: money, then an army
    tb = pop_in(t, rich - 0.1)
    if tb > 0:
        cx, cy, r = 540, 1010, 135 * tb
        for k, (tx_, ty_, rr) in enumerate([(445, 1215, 14), (470, 1178, 20)]):
            c.drawCircle(tx_, ty_, rr * tb, P(C(250, 250, 245)))
            c.drawCircle(tx_, ty_, rr * tb, S(OUT, 3))
        c.drawCircle(cx, cy, r, P(C(250, 250, 245)))
        c.drawCircle(cx, cy, r, S(OUT, 5))
        c.save()
        c.clipPath(oval(cx, cy, r - 6, r - 6), doAntiAlias=True)
        if t < army:
            for k in range(5):
                coin(c, cx - 80 + k * 40, cy + 40 - 10 * math.sin(t * 6 + k), 26, face=math.cos(t * 5 + k))
        else:
            k = t - army
            for j in range(5):  # tiny soldiers marching in
                sx_ = cx - 220 + j * 70 + 110 * min(1, k / 0.8)
                sy_ = cy + 60 - abs(math.sin(t * 9 + j)) * 8
                c.drawRect(skia.Rect(sx_ - 12, sy_ - 70, sx_ + 12, sy_ - 20), P(C(30, 45, 95)))
                c.drawCircle(sx_, sy_ - 85, 14, P(C(225, 175, 135)))
                c.drawRect(skia.Rect(sx_ - 16, sy_ - 112, sx_ + 16, sy_ - 96), P(C(30, 28, 40)))
                c.drawRect(skia.Rect(sx_ - 9, sy_ - 20, sx_ - 2, sy_), P(C(235, 235, 230)))
                c.drawRect(skia.Rect(sx_ + 2, sy_ - 20, sx_ + 9, sy_), P(C(235, 235, 230)))
                c.drawLine(sx_ + 16, sy_ - 70, sx_ + 16, sy_ - 125, S(C(80, 60, 40), 4))
        c.restore()


def melt_duck(c, x, y, k):
    """Toy duck that sags and melts, k = seconds since it failed (<0: fine)."""
    m = ease(k / 0.8) if k > 0 else 0
    c.save()
    c.translate(x, y)
    c.scale(1 + 0.4 * m, 1 - 0.55 * m)
    blob(c, oval(0, -60, 80, 55), (250, 210, 60), 1.2, 0.7)
    blob(c, oval(45, -135 + 40 * m, 42, 40), (250, 210, 60), 1.2, 0.7)
    p = skia.Path()
    p.moveTo(80, -135 + 40 * m)
    p.lineTo(120, -125 + 50 * m)
    p.lineTo(80, -115 + 40 * m)
    p.close()
    blob(c, p, (240, 130, 40))
    c.drawCircle(55, -145 + 40 * m, 7, P(C(30, 20, 15)))
    c.restore()
    if m > 0:
        for j in range(3):
            c.drawCircle(x - 40 + j * 40, y + 6 + 20 * m * (j % 2), 10 * m, P(C(250, 210, 60)))


def droop_boot(c, x, y, k):
    m = ease(k / 0.8) if k > 0 else 0
    p = skia.Path()
    top = -200
    bend = 90 * m
    p.moveTo(-40, 0)
    p.lineTo(-40, top * 0.4)
    p.cubicTo(-40, top * 0.8, -40 - bend * 0.3, top + bend * 0.3, -40 - bend, top + bend)
    p.lineTo(30 - bend, top + bend + 10)
    p.cubicTo(30 - bend * 0.3, top + bend * 0.3, 30, top * 0.8, 30, top * 0.4)
    p.lineTo(30, -50)
    p.cubicTo(70, -50, 110, -40, 110, 0)
    p.close()
    c.save()
    c.translate(x, y)
    blob(c, p, (60, 50, 50), 1.5, 0.7)
    c.drawRect(skia.Rect(-44, -12, 114, 4), P(C(30, 25, 25)))
    c.restore()


def flop_tire(c, x, y, k, t):
    m = ease(k / 0.7) if k > 0 else 0
    wob = 0.05 * math.sin(t * 20) * (1 - m) if k > -0.3 else 0
    rx, ry = 95 * (1 + 0.35 * m + wob), 95 * (1 - 0.6 * m - wob)
    c.drawOval(skia.Rect(x - rx, y - 2 * ry, x + rx, y), P(C(40, 40, 45)))
    c.drawOval(skia.Rect(x - rx, y - 2 * ry, x + rx, y), S(OUT, 5))
    c.drawOval(skia.Rect(x - rx * 0.45, y - ry - ry * 0.45, x + rx * 0.45, y - ry + ry * 0.45), P(C(150, 150, 160)))


def art_lab(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(30, 30, 38), C(60, 55, 60), C(25, 22, 28)])))
    for k in range(6):  # pipes on the wall
        c.drawLine(0, 950 + k * 30, W, 950 + k * 30, S(C(70, 65, 70, 120), 8))
    c.drawRect(skia.Rect(0, 1640, W, H), P(C(35, 30, 32)))
    toys, boots, tires, failed = CUE["toys"], CUE["boots"], CUE["tires"], CUE["failed"]
    fp = ease((t - failed) / 0.35)
    sweat = t < failed
    pose = dict(hands=[(-80, 60) if fp < 0.5 else (35, -95), (60, 60)], eyes="squint" if fp > 0.5 else "wide",
                brows="sad" if fp > 0.5 else "up", mouth="frown" if fp > 0.5 else "O", look=(-1, 0.6), tilt=-8 * fp + 2 * math.sin(t * 2),
                blink=False)
    person(c, 860, 1820, 1.4, ADAMS, pose, t)
    if sweat:
        for n in range(4):
            dt = t - (0.2 + n * 0.8)
            if 0 < dt < 0.6:
                c.drawCircle(860 + (90 + 200 * dt) * (1 if n % 2 else -1), 1300 - 260 * dt + 900 * dt * dt, 11, P(C(190, 225, 255, 230)))
    # workbench
    blob(c, rrect(0, 1620, 1080, 1700, 10), (120, 85, 55))
    c.drawRect(skia.Rect(40, 1700, 80, 1920), P(C(80, 55, 35)))
    c.drawRect(skia.Rect(640, 1700, 680, 1920), P(C(80, 55, 35)))
    for x0, at, fn in ((170, toys, "duck"), (420, boots, "boot"), (660, tires, "tire")):
        s = pop_in(t, at - 0.05)
        if s <= 0:
            continue
        c.save()
        c.translate(x0, 1620)
        c.scale(s, s)
        c.translate(-x0, -1620)
        k = t - (at + 0.9)
        if fn == "duck":
            melt_duck(c, x0, 1620, k)
        elif fn == "boot":
            droop_boot(c, x0, 1620, k)
        else:
            flop_tire(c, x0, 1620, k, t)
        c.restore()
        puff(c, x0, 1500, t - (at + 0.9))


def art_drugstore(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(35, 28, 30), C(75, 55, 45), C(35, 25, 22)])))
    for row in range(3):
        y = 990 + row * 170
        c.drawRect(skia.Rect(0, y, 620, y + 14), P(C(100, 70, 40)))
        for k in range(5):
            x = 30 + k * 118
            col = [(200, 80, 90), (90, 160, 120), (220, 180, 80), (110, 120, 200)][(k + row) % 4]
            blob(c, rrect(x, y - 105, x + 70, y, 16), col, 1.4, 0.7)
    c.drawRect(skia.Rect(0, 1560, W, H), P(Shader=lin((0, 1560), (0, H), [C(110, 80, 55), C(60, 40, 28)])))
    girl, so, boil, roll, loved = CUE["girl"], CUE["so"], CUE["boil"], CUE["roll"], CUE["loved"]
    # clerk behind the counter, girl buying gum
    cp = dict(hands=[(-120 * ease((t - girl) / 0.5), 60), (20, 150)], eyes="open", mouth="smile", brows="flat", look=(-1, 0.3),
              blink=blinking(t, 0.7), tilt=2 * math.sin(t * 1.5))
    person(c, 440, 1640, 1.15, CLERK, cp, t)
    blob(c, rrect(0, 1470, 600, 1600, 8), (130, 90, 55))
    c.drawRect(skia.Rect(0, 1600, 600, 1700), P(C(90, 60, 35)))
    jar = rrect(380, 1330, 520, 1470, 20)
    c.drawPath(jar, P(C(220, 240, 255, 70)))
    for k in range(9):
        gum_pack(c, 405 + (k % 3) * 45, 1450 - (k // 3) * 35, 0.32, rot=(k * 23) % 30 - 15, col=[(250, 120, 185), (120, 200, 160), (250, 200, 80)][k % 3])
    c.drawPath(jar, S(C(220, 240, 255, 160), 4))
    hop = abs(math.sin(t * 5)) * 10 if t > girl else 0
    gp = dict(hands=[(-20, 150), (90, -40 - 40 * ease((t - girl) / 0.4))], eyes="open", mouth="grin" if t > girl + 0.8 else "smile",
              brows="up", look=(1, -0.4), blink=blinking(t, 1.3))
    person(c, 170, 1860 - hop, 1.1, GIRL, gp, t)
    gx, gy = hand_pos(170, 1860 - hop, 1.1, gp, 1)
    if t > girl + 0.6:
        gum_pack(c, gx + 10, gy - 30, 0.5, rot=-20)
    elif t > girl:
        coin(c, gx + 10, gy - 20, 18, face=1.0)
    # Adams watching from the right, gets the idea
    idea = t > so
    ap = dict(hands=[(-40, 60), (60 if not idea else 40, 150 if not idea else -120)], eyes="wide" if idea else "squint",
              brows="up" if idea else "flat", mouth="grin" if idea else "smile", look=(-1, 0), tilt=-6 + 3 * math.sin(t * 2),
              blink=blinking(t, 0.5) and not idea)
    person(c, 880, 1860, 1.35, ADAMS, ap, t)
    lightbulb(c, 880, head_top(1860, 1.35) - 120, 0.9, t, so)
    # pot of boiling chicle -> gum balls hop into a bowl
    ps = pop_in(t, boil - 0.05)
    if ps > 0:
        c.save()
        c.translate(700, 1770)
        c.scale(ps, ps)
        glow(c, 0, 40, 160, (255, 140, 60), int(120 * flicker(t, 2)))
        blob(c, rrect(-110, -110, 110, 30, 30), (70, 70, 80), 1.5, 0.6)
        c.drawOval(skia.Rect(-110, -130, 110, -90), P(C(160, 105, 60)))
        for k in range(5):
            ph = (t * 1.5 + k * 0.23) % 1
            c.drawCircle(-80 + k * 40, -112 - ph * 25, 10 + 6 * ph, S(C(200, 150, 100, int(255 * (1 - ph))), 3))
        c.restore()
    for k in range(6):
        at = roll + k * 0.12
        dt = t - at
        if dt <= 0:
            continue
        u = min(1, dt / 0.55)
        x = 700 + (545 + k * 26 - 700) * u
        y = 1660 * (1 - u) + 1870 * u - 330 * math.sin(math.pi * u)
        col = [(250, 120, 185), (120, 200, 160), (250, 200, 80)][k % 3]
        c.drawCircle(x, y, 22, P(Shader=rad(x - 7, y - 7, 26, [C(255, 255, 255), C(*col)], [0, 0.6])))
        c.drawCircle(x, y, 22, S(OUT, 3))
    if t > loved:
        for k in range(7):
            a = k / 7 * 2 * math.pi
            r = 120 + 140 * ease((t - loved) / 0.8)
            heart(c, 540 + math.cos(a) * r, 1250 + math.sin(a) * r * 0.6, 0.6, int(255 * max(0, 1 - (t - loved) / 1.4)))


def art_poor(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(10, 14, 28), C(28, 36, 58), C(12, 14, 22)])))
    for k in range(4):  # far buildings
        c.drawRect(skia.Rect(k * 280 - 20, 1000 + (k % 2) * 80, k * 280 + 230, 1620), P(C(25, 30, 48)))
        c.drawRect(skia.Rect(k * 280 + 60, 1100 + (k % 2) * 80, k * 280 + 110, 1170 + (k % 2) * 80), P(C(255, 200, 110, 140)))
    c.drawRect(skia.Rect(0, 1620, W, H), P(Shader=lin((0, 1620), (0, H), [C(45, 45, 55), C(20, 20, 28)])))
    died, poor = CUE["died"], CUE["poor"]
    slump = ease(t / 1.2)
    pose = dict(hands=[(-60 + 10 * slump, 130), (60 - 10 * slump, 130)], eyes="sad", brows="sad", mouth="frown", look=(0, 0.8),
                tilt=-6 * slump + 1.5 * math.sin(t * 1.3), lean=2 * slump, blink=blinking(t, 0.4), hat_bounce=-14 * slump)
    x, y, s = 540, 1840, 1.55
    person(c, x, y, s, SANTA_OLD, pose, t)
    for side in (-1, 1):  # empty pockets turned inside out
        px = x + side * 70 * s
        py = y - 120 * s
        p = skia.Path()
        p.moveTo(px - 26, py)
        p.lineTo(px + 26, py)
        p.lineTo(px + 18 * side, py + 48 + 6 * math.sin(t * 3 + side))
        p.close()
        blob(c, p, (235, 230, 220), 1.05, 0.8)
    if t > poor:  # a moth flutters out of the pocket
        k = t - poor
        mx_, my_ = x + 70 * s + 140 * k + 20 * math.sin(k * 7), y - 120 * s - 220 * k + 30 * math.sin(k * 5)
        wing = 18 + 10 * math.sin(t * 40)
        c.drawOval(skia.Rect(mx_ - wing - 8, my_ - 16, mx_, my_ + 6), P(C(200, 190, 170, 230)))
        c.drawOval(skia.Rect(mx_, my_ - 16, mx_ + wing + 8, my_ + 6), P(C(200, 190, 170, 230)))
        c.drawCircle(mx_, my_, 6, P(C(90, 80, 70)))
    # his last coin rolls away into the dark
    if t > died:
        k = t - died
        cx = x - 70 * s - 260 * k
        coin(c, cx, 1830, 22, face=math.cos(k * 14))
    rain(c, t, 140, 4)
    for k in range(5):  # puddle ripples
        ph = (t * 0.9 + k * 0.37) % 1
        rx = 30 + 90 * ph
        c.drawOval(skia.Rect(150 + k * 190 - rx, 1760 + (k % 2) * 70 - rx * 0.25, 150 + k * 190 + rx, 1760 + (k % 2) * 70 + rx * 0.25),
                   S(C(170, 190, 230, int(150 * (1 - ph))), 3))


def soap_box(c, x, y, s=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    blob(c, rrect(-70, -60, 70, 0, 8), (235, 225, 190), 1.1, 0.8)
    c.drawRect(skia.Rect(-70, -42, 70, -18), P(C(80, 150, 200)))
    f = skia.Font(FB, 22)
    c.drawString("SOAP", -32, -22, f, P(C(255, 255, 255)))
    c.restore()


def art_wrigley(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(30, 22, 30), C(70, 45, 40), C(30, 20, 20)])))
    for k in range(14):  # brick wall
        y = 900 + k * 50
        for j in range(12):
            x = j * 100 + (50 if k % 2 else 0)
            c.drawRect(skia.Rect(x + 3, y + 3, x + 97, y + 47), P(C(105, 50, 42)))
    for k in range(9):  # striped awning
        col = (200, 50, 60) if k % 2 else (240, 235, 225)
        p = skia.Path()
        p.moveTo(k * 120, 900)
        p.lineTo(k * 120 + 120, 900)
        p.lineTo(k * 120 + 130, 1010)
        p.lineTo(k * 120 + 10, 1010)
        p.close()
        c.drawPath(p, P(C(*col)))
    for k in range(9):
        c.drawArc(skia.Rect(k * 120 + 10, 985, k * 120 + 130, 1040), 0, 180, False, P(C(*((200, 50, 60) if k % 2 else (240, 235, 225)))))
    c.drawRect(skia.Rect(0, 1640, W, H), P(Shader=lin((0, 1640), (0, H), [C(90, 85, 85), C(45, 40, 40)])))
    free, cust = CUE["free"], CUE["cust"]
    # Wrigley at his table of soap, tossing free gum
    toss = t > free
    wp = dict(hands=[(-40, 70), (90 if not toss else 120, 40 if not toss else -110 + 30 * math.sin(t * 6))], eyes="open", brows="up",
              mouth="grin" if toss else "smile", look=(1, 0), tilt=3 * math.sin(t * 2), blink=blinking(t, 0.8))
    person(c, 330, 1800, 1.35, WRIGLEY, wp, t)
    blob(c, rrect(90, 1530, 560, 1600, 8), (140, 95, 60))
    c.drawRect(skia.Rect(120, 1600, 150, 1900), P(C(90, 60, 35)))
    c.drawRect(skia.Rect(500, 1600, 530, 1900), P(C(90, 60, 35)))
    for k in range(5):  # soap stack (ignored, one box gets knocked over)
        sx, sy = 160 + (k % 3) * 140, 1530 - (k // 3) * 60
        soap_box(c, sx, sy, 0.95)
    for k in range(7):  # gum packs flying to the customers
        at = free + k * 0.22
        dt = t - at
        if dt <= 0:
            continue
        u = min(1, dt / 0.6)
        x = 420 + (720 + (k % 3) * 100 - 420) * u
        y = 1320 - 380 * math.sin(math.pi * u) + 80 * u
        gum_pack(c, x, y, 0.55, rot=360 * u * (1 if k % 2 else -1))
    for i, (x, lk) in enumerate([(720, 0), (860, 2), (1000, 4)]):
        grab = ease((t - cust - i * 0.1) / 0.4)
        pose = dict(hands=[(-60 - 50 * grab, 80 - 200 * grab), (20, 150)], eyes="wide" if grab > 0.5 else "open",
                    brows="up", mouth="grin" if grab > 0.5 else "O" if t > free else "smile", look=(-1, -0.3),
                    tilt=4 * math.sin(t * 3 + i), blink=blinking(t, i))
        person(c, x, 1880 - abs(math.sin(t * 6 + i)) * 12 * grab, 0.95, crowd_look(lk), pose, t)
    if t > cust:
        for k in range(4):
            heart(c, 860 + (k - 1.5) * 110, 1050 - ((t - cust) * 120 + k * 40) % 160, 0.55, 220)


def art_empire(c, t):
    U.T_EIGHT = CUE["empire"] - 0.6
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(15, 15, 40), C(60, 40, 90), C(250, 150, 90)], [0, 0.55, 1])))
    glow(c, 540, 1300, 600, (255, 200, 120), 120)
    rise = ease((t - CUE["built"] + 0.3) / 0.9)
    # the white tower rising behind him
    th = 760 * rise
    if th > 4:
        c.drawRect(skia.Rect(380, 1650 - th, 700, 1650), P(Shader=lin((380, 0), (700, 0), [C(200, 195, 190), C(250, 248, 240), C(180, 175, 170)])))
        for r in range(int(th // 70)):
            for j in range(4):
                c.drawRect(skia.Rect(400 + j * 75, 1620 - r * 70 - 40, 440 + j * 75, 1620 - r * 70), P(C(255, 210, 120)))
        if rise > 0.9:
            c.drawCircle(540, 1650 - th + 70, 42, P(C(250, 245, 230)))
            c.drawCircle(540, 1650 - th + 70, 42, S(OUT, 4))
            c.drawLine(540, 1650 - th + 70, 540, 1650 - th + 42, S(OUT, 4))
            c.drawLine(540, 1650 - th + 70, 562, 1650 - th + 70, S(OUT, 4))
    # mountain of gum packs
    k = 0
    for row in range(6):
        n = 9 - row
        for j in range(n):
            x = 540 + (j - (n - 1) / 2) * 118
            y = 1890 - row * 58
            gum_pack(c, x, y, 0.85, rot=((j * 37 + row * 11) % 15) - 7, col=[(250, 120, 185), (120, 200, 160), (250, 200, 80)][(j + row) % 3])
            k += 1
    bounce = abs(math.sin(t * 5)) * 14
    wp = dict(hands=[(-70, -230 - 15 * math.sin(t * 6)), (70, -230 + 15 * math.sin(t * 6))], eyes="closed", mouth="laugh", brows="up",
              tilt=5 * math.sin(t * 5), hat_bounce=-10 * abs(math.sin(t * 5)))
    for x, y, r, face, speed in U.coins_at(t):  # coins rain behind him (never over his face)
        U.draw_coin(c, x, y, r, face, speed)
    person(c, 540, 1590 - bounce, 1.15, WRIGLEY, wp, t)


def art_singapore(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(8, 10, 35), C(40, 30, 90), C(120, 60, 120)], [0, 0.6, 1])))
    r = random.Random(8)
    for i in range(50):
        x, y = r.uniform(0, W), r.uniform(0, 900)
        tw = 0.5 + 0.5 * math.sin(t * r.uniform(1.5, 3.5) + i)
        c.drawCircle(x, y, 1.5 + 2 * tw, P(C(255, 250, 230, 80 + 140 * tw)))
    # Marina Bay skyline silhouette: three towers with the sky park on top
    for k in range(3):
        x = 640 + k * 120
        p = skia.Path()
        p.moveTo(x - 40, 1450)
        p.lineTo(x - 30, 1080)
        p.lineTo(x + 40, 1080)
        p.lineTo(x + 46, 1450)
        p.close()
        c.drawPath(p, P(C(40, 40, 75)))
        for j in range(9):
            c.drawRect(skia.Rect(x - 25, 1110 + j * 36, x + 30, 1118 + j * 36), P(C(255, 220, 150, 120)))
    deck = skia.Path()
    deck.moveTo(560, 1080)
    deck.cubicTo(700, 1050, 860, 1050, 1000, 1060)
    deck.lineTo(1000, 1080)
    deck.lineTo(560, 1095)
    deck.close()
    c.drawPath(deck, P(C(55, 55, 95)))
    for k, (x, h) in enumerate(((90, 300), (230, 360), (370, 280))):  # glowing super-trees
        c.drawLine(x, 1450, x, 1450 - h, S(C(60, 50, 90), 16))
        top = 1450 - h
        p = skia.Path()
        p.moveTo(x - 90, top - 40)
        p.quadTo(x, top + 60, x + 90, top - 40)
        p.quadTo(x, top + 10, x - 90, top - 40)
        c.drawPath(p, P(C(120, 60, 160)))
        glow(c, x, top - 20, 150, (200, 90, 255), int(90 + 50 * math.sin(t * 2 + k)))
    c.drawRect(skia.Rect(0, 1450, W, 1560), P(Shader=lin((0, 1450), (0, 1560), [C(40, 30, 80), C(15, 15, 35)])))
    for k in range(14):  # reflections on the bay
        x = (k * 83) % W
        c.drawLine(x, 1470 + (k % 4) * 22, x + 40 + 20 * math.sin(t * 2 + k), 1470 + (k % 4) * 22, S(C(255, 200, 150, 90), 3))
    c.drawRect(skia.Rect(0, 1560, W, H), P(Shader=lin((0, 1560), (0, H), [C(80, 80, 90), C(45, 45, 52)])))
    for k in range(6):
        c.drawLine(k * 200, 1560, k * 200 - 120, H, S(C(60, 60, 68), 4))
    messy, ban = CUE["messy"], CUE["ban"]
    # a shoe pulling free from a gum blob: the strings stretch, thin and snap
    lift = ease(t / max(0.1, messy + 0.5))
    snap = t > messy + 0.5
    shoe_y = 1800 - 160 * lift - (40 * ease((t - messy - 0.5) / 0.3) if snap else 0)
    gx, gy = 540, 1840
    blob(c, oval(gx, gy, 160, 26), (250, 120, 185), 1.3, 0.7)
    if not snap:
        for k in range(5):
            x0 = gx - 100 + k * 50
            w = max(3, 20 * (1 - lift) + 4)
            p = skia.Path()
            p.moveTo(x0, gy - 10)
            p.cubicTo(x0 + 10 * math.sin(t * 3 + k), (gy + shoe_y) / 2, x0 - 6, (gy + shoe_y) / 2, x0 + (k - 2) * 8, shoe_y)
            c.drawPath(p, S(C(250, 120, 185), w))
    else:
        k = t - messy - 0.5
        for j in range(5):  # snapped ends whip back
            x0 = gx - 100 + j * 50
            ln = 120 * max(0, 1 - k / 0.25)
            c.drawLine(x0, gy - 10, x0 + 6 * math.sin(j), gy - 10 - ln, S(C(250, 120, 185), 8))
    # the shoe
    c.save()
    c.translate(540, shoe_y)
    c.rotate(-6 * lift)
    sole = skia.Path()
    sole.moveTo(-170, 0)
    sole.cubicTo(-170, -70, -60, -90, 10, -100)
    sole.lineTo(10, -260)
    sole.lineTo(120, -260)
    sole.lineTo(130, -60)
    sole.cubicTo(170, -50, 190, -20, 180, 0)
    sole.close()
    blob(c, sole, (110, 70, 45), 1.3, 0.65)
    c.drawRect(skia.Rect(-175, -14, 185, 8), P(C(40, 30, 25)))
    c.drawRect(skia.Rect(10, -280, 120, -250), P(C(60, 60, 75)))
    c.restore()
    # NO GUM sign drops in on "banned"
    s = pop_in(t, ban - 0.05)
    if s > 0:
        c.save()
        c.translate(540, 1080)
        c.scale(s, s)
        c.drawCircle(0, 0, 175, P(C(255, 255, 255)))
        gum_pack(c, 0, 0, 1.4, rot=-20)
        c.drawCircle(0, 0, 160, S(C(220, 30, 40), 34))
        c.drawLine(-113, -113, 113, 113, S(C(220, 30, 40), 34))
        c.restore()


def gumball(c, t, st, bub):
    """CTA mascot: a pink gumball with sunglasses, blowing a bubble (bub = radius)."""
    c.drawOval(skia.Rect(-150, -18, 150, 18), P(C(0, 0, 0, 120), MaskFilter=blur(14)))
    sq = 0.03 * math.sin(t * 2.4)
    c.save()
    c.scale(1 + sq, 1 - sq)
    body = oval(0, -200, 190, 190)
    c.drawPath(body, P(Shader=rad(-60, -280, 300, [C(255, 200, 230), C(245, 110, 175), C(190, 50, 120)], [0, 0.55, 1])))
    c.drawPath(body, S(C(150, 30, 90), 8))
    c.drawOval(skia.Rect(-120, -350, -40, -300), P(C(255, 255, 255, 170)))
    for side in (-1, 1):  # sunglasses
        r = skia.RRect.MakeRectXY(skia.Rect(side * 70 - 62, -270, side * 70 + 62, -180), 30, 30)
        c.drawRRect(r, P(Shader=lin((0, -270), (0, -180), [C(70, 70, 90), C(8, 8, 14)])))
        c.drawRRect(r, S(C(10, 10, 10), 8))
        g = ((t * 0.7) % 1.5) / 0.4
        if 0 < g < 1:
            c.save()
            c.clipRRect(r, doAntiAlias=True)
            gx = side * 70 - 100 + g * 200
            gp = skia.Path()
            gp.moveTo(gx, -280)
            gp.lineTo(gx + 34, -280)
            gp.lineTo(gx - 12, -170)
            gp.lineTo(gx - 46, -170)
            gp.close()
            c.drawPath(gp, P(C(255, 255, 255, 170)))
            c.restore()
    c.drawLine(-8, -235, 8, -235, S(C(10, 10, 10), 14))
    if bub > 0:
        bubble(c, 0, -105 + bub * 0.8, bub, t)
    else:
        c.drawArc(skia.Rect(-45, -150, 45, -90), 20, 140, False, S(C(130, 30, 80), 9))
    c.restore()


def art_cta(c, t):
    U.T_EIGHT = -10
    U.background(c, t, 0)
    U.spotlight(c, t, 0)
    U.pedestal(c, t)
    off = CUE["cta_off"]
    grow = ease((t - off - 0.3) / 2.8)
    pop_t = off + 3.6
    c.save()
    c.translate(540, 1415)
    gumball(c, t, None, 0 if t > pop_t else 30 + 110 * grow)
    if t > pop_t:
        shreds(c, 0, -105 + 140 * 0.8, 140, t - pop_t, seed=3)
    c.restore()
    c.drawPaint(P(C(10, 6, 14, 150)))


ART = [art_hook, art_denmark, art_greece, art_newyork, art_pitch, art_lab, art_drugstore, art_poor, art_wrigley, art_empire, art_singapore, art_cta]
PUSH = [(1.0, 1.06), (1.0, 1.07), (1.0, 1.06), (1.05, 1.0), (1.0, 1.06), (1.0, 1.07), (1.0, 1.05), (1.06, 1.0), (1.0, 1.06), (1.0, 1.08), (1.0, 1.06), (1.0, 1.0)]
ANCHOR = [(540, 1300), (450, 1400), (540, 1400), (540, 1500), (540, 1400), (540, 1450), (540, 1450), (540, 1500), (540, 1450), (540, 1500), (540, 1400), (540, 1300)]


def render_art(i, t, dur):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    z0, z1 = PUSH[i]
    z = z0 + (z1 - z0) * ease(t / dur)
    ax, ay = ANCHOR[i]
    c.save()
    c.translate(ax, ay)
    c.scale(z, z)
    c.translate(-ax + math.sin(t * 0.5) * 6, -ay + math.cos(t * 0.4) * 5)
    ART[i](c, t)
    c.restore()
    snap = surf.makeImageSnapshot()
    c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=U.BLOOM, ImageFilter=skia.ImageFilters.Blur(24, 24), BlendMode=skia.BlendMode.kPlus, Alphaf=0.45))
    c.drawPaint(P(Shader=rad(540, 1100, 1250, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 190)], [0, 0.5, 1])))
    c.drawRect(skia.Rect(0, 0, W, 900), P(Shader=lin((0, 0), (0, 900), [C(5, 4, 10, 150), C(5, 4, 10, 0)])))
    c.drawImageRect(U.GRAIN[int(t * 30) % len(U.GRAIN)], skia.Rect(0, 0, W, H), skia.SamplingOptions(), P(Alphaf=0.06, BlendMode=skia.BlendMode.kOverlay))
    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    return Image.fromarray(np.ascontiguousarray(arr))


# ---------- text layer ----------

def title(img, t, text, sub=None, sub_at=1.0, y=400, sub_color=(255, 235, 210)):
    heading(img, t, text, sub, sub_at, F_MID, y, sub_color=sub_color)


def scene(i, text_fn):
    def fn(img, d, t):
        img.paste(render_art(i, t, CUE["d"][i]))
        text_fn(img, t)
    return fn


def line(img, text, y, f):
    dd = ImageDraw.Draw(img, "RGBA")
    tw = dd.textlength(text, font=f)
    dd.text(((W - tw) / 2 + 4, y + 5), text, font=f, fill=(0, 0, 0, 140))
    dd.text(((W - tw) / 2, y), text, font=f, fill=(255, 255, 255))


def tx_hook(img, t):
    line(img, "Chewing gum exists", 230, F_MID)
    line(img, "because of a", 330, F_MID)
    slam(img, "DICTATOR", 430, t, CUE["dict"] - 0.1, GOLD, 150)
    text_block(img, "...and his failed plan", font(FONT_B, 58), 640, t, (255, 255, 255), CUE["fail"])
    text_block(img, "to take back Mexico!", font(FONT_B, 58), 712, t, PINK, CUE["fail"] + 0.35)
    impact(img, t, CUE["dict"] + 0.1, 18)


def tx_denmark(img, t):
    tag(img, "DENMARK", t, (200, 60, 70))
    title(img, t, "Chewed birch tar...", "The chewer's DNA was still inside!", CUE["dna"])
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "5,700 YEARS", t, CUE["five"], col=GOLD, size=100)
    impact(img, t, CUE["five"] + 0.15, 12)


def tx_greece(img, t):
    tag(img, "ANCIENT GREECE", t, (60, 110, 170))
    title(img, t, "They chewed tree resin", "...to freshen their breath!", CUE["fresh"], sub_color=(190, 255, 230))


def tx_newyork(img, t):
    tag(img, "NEW YORK, 1869", t, (90, 90, 140))
    title(img, t, "Mexico's exiled general", "Santa Anna", CUE["santa"], sub_color=GOLD)


def tx_pitch(img, t):
    title(img, t, "He hands an inventor chicle", "\"Turn it into rubber!\"", CUE["turn"], sub_color=GOLD)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "AN ARMY?!", t, CUE["army"], col=RED, size=100)
    impact(img, t, CUE["army"] + 0.15, 12)


def tx_lab(img, t):
    title(img, t, "A whole year of tests", "Toys... boots... tires...", CUE["toys"])
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "FAILED", t, CUE["failed"], col=RED, size=110)
    impact(img, t, CUE["failed"] + 0.15, 14)


def tx_drug(img, t):
    title(img, t, "Then he saw a girl buy gum", "So he made his own!", CUE["boil"], sub_color=PINK)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "A HIT!", t, CUE["loved"], col=PINK, size=110)
    impact(img, t, CUE["loved"] + 0.15, 12)


def tx_poor(img, t):
    title(img, t, "He never got his army", "He died poor in Mexico.", CUE["died"], sub_color=(190, 205, 235))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "BROKE", t, CUE["poor"], col=(170, 180, 200), size=110)
    impact(img, t, CUE["poor"] + 0.15, 10)


def tx_wrigley(img, t):
    tag(img, "CHICAGO, 1890s", t, (200, 60, 70))
    title(img, t, "A soap salesman's free gift", "Customers wanted the GUM!", CUE["cust"], sub_color=PINK)


def tx_empire(img, t):
    title(img, t, "So he sold gum instead...", y=260)
    slam(img, "EMPIRE!", 420, t, CUE["empire"] - 0.1, GOLD, 160)
    impact(img, t, CUE["empire"] + 0.1, 16)


def tx_singapore(img, t):
    tag(img, "SINGAPORE", t, (200, 40, 50))
    title(img, t, "Today, gum is so messy...", "Singapore banned selling it!", CUE["sing"])
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "BANNED", t, CUE["ban"], col=RED, size=110)
    impact(img, t, CUE["ban"] + 0.15, 14)


def tx_cta(img, t):
    text_block(img, "Learned something new?", font(FONT_B, 68), 330, t, delay=0.0)
    make_salt.draw_cta(img, ImageDraw.Draw(img, "RGBA"), W / 2, 1250, t, off=CUE["cta_off"])


TEXT = [tx_hook, tx_denmark, tx_greece, tx_newyork, tx_pitch, tx_lab, tx_drug, tx_poor, tx_wrigley, tx_empire, tx_singapore, tx_cta]
base.TRANSITION = splat

if __name__ == "__main__":
    voice = f"{VOICE_DIR}/voice.mp3"
    tl = Timeline(voice)
    VOX = load_vox(voice)
    # scene cuts in the pause before each paragraph's first words
    firsts = ["in denmark", "the ancient", "then", "he gave", "and|adams strive|tried", "they|then saw", "santana|santa", "years later",
              "so it's|is|he", "to|today they|got", "learn"]
    after, starts = 0.3, [0.0]
    for ph in firsts:
        w = tl.find(ph, after)
        before = [p for p in tl.pauses if p[1] <= w + 0.2 and p[0] >= after - 0.3]
        # cut late in the pause (0.25 s before the next words) so the last stamp/slam stays readable longer
        cut = max((before[-1][0] + before[-1][1]) / 2, before[-1][1] - 0.25) if before else w - 0.15
        starts.append(round(cut, 3))
        after = w + 0.3
    total = round(tl.length + 1.9, 2)
    durs = [round(b - a, 2) for a, b in zip(starts, starts[1:] + [total])]
    S0 = starts
    f = lambda phrase, sc, lead=0.1: round(tl.find(phrase, S0[sc]) - S0[sc] - lead, 2)
    CUE.update(d=durs, S=S0,
               dict=f("dictator", 0, 0.0), fail=f("fail", 0),
               five=f("five", 1, 0.15), dna=f("dna", 1),
               fresh=f("freshen", 2),
               santa=f("santana|santa", 3),
               gave=f("gave", 4), chicle=f("chicle|chuckle", 4), turn=f("turn", 4, 0.0), rich=f("rich", 4), army=f("army", 4, 0.15),
               toys=f("toys", 5), boots=f("boots", 5), tires=f("tires", 5), failed=f("failed", 5, 0.15),
               girl=f("girl", 6), so=f("so", 6), boil=f("boil", 6), roll=f("roll", 6), loved=f("loved", 6, 0.15),
               died=f("died", 7), poor=f("poor|porn", 7, 0.15),
               free=f("free", 8), cust=f("customers", 8),
               built=f("built", 9), empire=f("empire", 9, 0.0),
               messy=f("messy", 10), sing=f("singapore", 10), ban=f("banned|band", 10, 0.15))
    CUE["cta_off"] = round(tl.find("like", S0[11]) - S0[11] - 1.6 + 0.15, 2)
    print("starts:", S0)
    print("durations:", durs, round(sum(durs), 2))
    print("cues:", {k: v for k, v in CUE.items() if k not in ("d", "S")})
    json.dump({"starts": S0, "durs": durs, "cues": {k: v for k, v in CUE.items() if k not in ("d", "S")}}, open(f"{VOICE_DIR}/plan.json", "w"), indent=1)
    if STILLS:
        for i in ONLY:
            for tt in STILLS:
                img = Image.new("RGBA", (W, H))
                scene(i, TEXT[i])(img, ImageDraw.Draw(img), float(tt))
                img.convert("RGB").save(f"{os.environ.get('STILLS_DIR', VOICE_DIR + '/stills')}/gum_{i}_{tt}.png")
        sys.exit()
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), scene(i, TEXT[i])) for i, dd in enumerate(durs)]
    if ONLY:
        base.SCENES[:] = [s for i, s in enumerate(base.SCENES) if i in ONLY]
    ST = S0
    C_ = CUE
    ev = [("whoosh", s) for s in ST[1:]]
    ev += [("pop", 0.25), ("thud", C_["dict"]), ("pop", C_["dict"] + 0.02), ("thud", C_["fail"] + 0.1),
           ("thud", ST[1] + C_["five"] + 0.15), ("ding", ST[1] + C_["dna"] + 0.05),
           ("ding", ST[2] + C_["fresh"] + 0.1),
           ("pop", ST[3] + C_["santa"]),
           ("pop", ST[4] + C_["gave"]), ("ding", ST[4] + C_["chicle"]), ("pop", ST[4] + C_["rich"]), ("thud", ST[4] + C_["army"] + 0.15),
           ("pop", ST[5] + C_["toys"]), ("pop", ST[5] + C_["boots"]), ("pop", ST[5] + C_["tires"]), ("thud", ST[5] + C_["failed"] + 0.15),
           ("ding", ST[6] + C_["so"]), ("pop", ST[6] + C_["boil"]), ("thud", ST[6] + C_["loved"] + 0.15),
           ("thud", ST[7] + C_["poor"] + 0.15),
           ("pop", ST[8] + C_["free"]), ("ding", ST[8] + C_["cust"]),
           ("thud", ST[9] + C_["empire"]), ("ding", ST[9] + C_["empire"] + 0.05),
           ("pop", ST[10] + C_["messy"] + 0.5), ("thud", ST[10] + C_["ban"] + 0.15),
           ("click", ST[11] + C_["cta_off"] + 1.6), ("click", ST[11] + C_["cta_off"] + 3.6), ("ding", ST[11] + C_["cta_off"] + 3.65)]
    ev += [("pop", ST[6] + C_["roll"] + k * 0.12 + 0.5) for k in range(6)]  # gum balls landing
    ev += [("click", ST[9] + C_["empire"] - 0.6 + 0.35 + i * 0.09 + (i % 3) * 0.03) for i in range(10)]  # coins
    ev = [(k, round(v, 3)) for k, v in ev if 0 <= v < total]
    audio.music("music.wav", total, bpm=104, seed=7)
    audio.sfx("sfx.wav", total, ev)
    base.OUT = "base_gum.mp4"
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_gum.mp4", voice, "music.wav", "sfx.wav", OUTFILE)
    print("wrote", OUTFILE)
