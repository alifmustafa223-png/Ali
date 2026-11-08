"""YouTube Short: "Messi's Contract Was a NAPKIN... Ronaldo Had HEART SURGERY" (Skia toon + physics.py + CTA v2).

Facts (all well documented): Messi was diagnosed with growth hormone deficiency around age 10-11; treatment cost about
$900-1,000 a month; he injected himself in the legs every night; in December 2000 Barcelona director Carles Rexach
wrote the first agreement on a paper napkin in a restaurant; the napkin sold at auction in 2024 for about
£762,000 (~$965,000, "almost a million dollars"). Cristiano Ronaldo was nicknamed "cry baby" as a boy because he cried
when teammates didn't pass; at 15 he was diagnosed with a racing heart (tachycardia), had laser surgery and was training
again days later; his father named him after Ronald Reagan, his favourite actor.
Cartoon kids/players only: no club crests, sponsor logos or real-person likenesses.

Physics (physics.py): bouncing footballs with gravity/restitution/spin/squash, a Verlet-cloth napkin, confetti with
drag + 3D flip, tears with gravity and splash, trophies dropping with spring settle, impact dust, jiggle on hits.
Usage: python make_goat.py final.mp4 [scene,...] [t1,...]   stills: STILLS_DIR=dir python make_goat.py x 0,1 1.0
"""
import json
import math
import os
import random
import sys

import numpy as np
import skia
from PIL import Image, ImageDraw

OUTFILE = sys.argv[1]
ONLY = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 and sys.argv[2][0].isdigit() else None
STILLS = sys.argv[3].split(",") if len(sys.argv) > 3 else None
sys.argv = [sys.argv[0], "base_goat.mp4"]
sys.path.insert(0, "..")

import audio  # noqa: E402
import make_ketchup  # noqa: E402
import make_short as base  # noqa: E402
import ultimate as U  # noqa: E402
import physics as PH  # noqa: E402
from cta2 import draw_cta2  # noqa: E402
from fx import impact  # noqa: E402
from make_honey import slam  # noqa: E402
from make_ketchup import splat, stamp  # noqa: E402
from make_short import FONT_B, F_MID, H, W, font, tag, text_block  # noqa: E402
from style import heading  # noqa: E402
from timing import Timeline  # noqa: E402
from toon import *  # noqa: E402,F401,F403

GOLD, RED, SKY, GREEN, PINK = (255, 200, 60), (235, 60, 60), (120, 190, 255), (90, 210, 120), (255, 130, 190)
make_ketchup.SPLAT_COLOR = (250, 195, 50)
base.HOOK_SKIP = 0.0
base.CRF = 16
CUE = {}
VOICE_DIR = "../goat"
TAIL = 1.4

LEO = dict(skin=(245, 210, 180), hair="kid", hair_col=(90, 60, 35), coat=(120, 185, 240), pants=(30, 40, 70), nose="small")
CR = dict(skin=(220, 175, 140), hair="neat", hair_col=(35, 25, 20), coat=(215, 40, 50), pants=(30, 110, 60), nose="small")
LEO_PRO = dict(LEO, hair="neat", hair_col=(80, 55, 35), beard=(80, 55, 35), coat=(120, 185, 240), pants=(255, 255, 255))
CR_PRO = dict(CR, coat=(215, 40, 50), pants=(255, 255, 255))
DOC = dict(skin=(240, 205, 175), hair="grey", hair_col=(180, 180, 185), coat=(245, 248, 250), pants=(70, 80, 100), glasses=True, nose="long")
DIRECTOR = dict(skin=(235, 195, 165), hair="neat", hair_col=(110, 110, 115), coat=(40, 50, 90), vest=(200, 50, 60), pants=(40, 45, 70),
                mustache=True, nose="long")
DAD = dict(skin=(220, 175, 140), hair="neat", hair_col=(40, 30, 25), coat=(120, 100, 80), pants=(70, 60, 50), mustache=True, nose="long")


KIDS = [dict(skin=(235, 195, 160), hair="kid", hair_col=(60, 40, 25), coat=(250, 190, 60), pants=(40, 50, 80), nose="small"),
        dict(skin=(200, 150, 110), hair="neat", hair_col=(30, 20, 15), coat=(110, 200, 130), pants=(50, 50, 60), nose="small"),
        dict(skin=(240, 210, 185), hair="kid", hair_col=(150, 90, 40), coat=(180, 120, 230), pants=(40, 40, 60), nose="small")]


def blinking(t, ph=0.0):
    return ((t + ph) % 3.3) < 0.11


def pop_in(t, at, dur=0.35):
    return out_back((t - at) / dur, 2.2) if t > at else 0.0


def head_c(y, s):
    return y - 332 * s


def safe_hands(hands):
    out = []
    for side, (hx, hy) in zip((-1, 1), hands):
        ax, ay = side * 60 + hx, -235 + hy
        if (ax / 118) ** 2 + ((ay + 332) / 125) ** 2 < 1:
            hx, hy = side * 10, 60
        out.append((hx, hy))
    return out


def stand(c, who, x, y, s, t, **pose):
    if "hands" in pose:
        pose["hands"] = safe_hands(pose["hands"])
    pose.setdefault("blink", blinking(t, x * 0.01))
    pose.setdefault("tilt", 2 * math.sin(t * 1.6 + x * 0.003))
    person(c, x, y, s, who, pose, t)


def bg(c, top, bot):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(*top), C(*bot)])))


def stadium(c, t, night=True):
    """Stadium at night: floodlights with flicker, crowd dots, pitch with stripes."""
    bg(c, (8, 12, 30) if night else (60, 120, 200), (30, 45, 80) if night else (150, 200, 240))
    c.drawRect(skia.Rect(0, 1150, W, 1460), P(C(25, 30, 45)))
    r = random.Random(5)
    for i in range(320):  # crowd
        x, y = r.uniform(0, W), r.uniform(1160, 1440)
        cl = [(230, 80, 80), (120, 180, 240), (240, 240, 240), (250, 210, 80)][i % 4]
        bob = 4 * math.sin(t * 6 + i)
        c.drawCircle(x, y + bob, 7, P(C(*cl, 180)))
    for fx in (120, 960):
        c.drawLine(fx, 1150, fx, 940, S(C(60, 60, 70), 10))
        blob(c, rrect(fx - 70, 900, fx + 70, 950, 6), (230, 230, 240))
        glow(c, fx, 925, 340, (255, 250, 220), int(130 * flicker(t, fx)))
    c.drawRect(skia.Rect(0, 1460, W, H), P(Shader=lin((0, 1460), (0, H), [C(60, 150, 70), C(30, 100, 45)])))
    for k in range(6):
        if k % 2:
            c.drawRect(skia.Rect(0, 1460 + k * 80, W, 1540 + k * 80), P(C(255, 255, 255, 14)))
    c.drawLine(0, 1560, W, 1560, S(C(255, 255, 255, 120), 6))


def ecg(c, x0, y0, w, h, t, bpm=70, col=(80, 255, 140)):
    """Heart-monitor line scrolling right->left; bpm drives spike spacing."""
    blob(c, rrect(x0 - 20, y0 - h / 2 - 20, x0 + w + 20, y0 + h / 2 + 20, 18), (20, 30, 35), 1.1, 0.8)
    p = skia.Path()
    period = 60.0 / bpm
    for i in range(int(w / 4) + 1):
        x = x0 + i * 4
        tt = t - (w - i * 4) / w * 2.0
        ph = (tt % period) / period
        if 0.42 < ph < 0.46:
            y = y0 - h * 0.45
        elif 0.46 <= ph < 0.5:
            y = y0 + h * 0.3
        elif 0.3 < ph < 0.36:
            y = y0 - h * 0.08
        else:
            y = y0
        (p.moveTo if i == 0 else p.lineTo)(x, y)
    c.drawPath(p, S(C(*col), 5))
    glow(c, x0 + w, y0, 60, col, 120)


def heart_shape(c, x, y, s, col=(230, 50, 70)):
    p = skia.Path()
    p.moveTo(x, y + 60 * s)
    p.cubicTo(x - 120 * s, y - 20 * s, x - 60 * s, y - 110 * s, x, y - 50 * s)
    p.cubicTo(x + 60 * s, y - 110 * s, x + 120 * s, y - 20 * s, x, y + 60 * s)
    p.close()
    blob(c, p, col, 1.35, 0.65)


def tear(c, x, y, r=10, a=230):
    p = skia.Path()
    p.moveTo(x, y - r * 1.6)
    p.cubicTo(x + r, y - r * 0.2, x + r, y + r, x, y + r)
    p.cubicTo(x - r, y + r, x - r, y - r * 0.2, x, y - r * 1.6)
    c.drawPath(p, P(C(150, 210, 255, a)))


def napkin_ink(progress):
    """Pen strokes on the napkin, revealed progressively (in sheet uv)."""
    def ink(c, pts, nx, ny):
        def at(u, v):
            i = min(nx - 2, int(u * (nx - 1)))
            j = min(ny - 2, int(v * (ny - 1)))
            fu, fv = u * (nx - 1) - i, v * (ny - 1) - j
            a, b, d, e = pts[j * nx + i], pts[j * nx + i + 1], pts[(j + 1) * nx + i + 1], pts[(j + 1) * nx + i]
            x = (a[0] * (1 - fu) + b[0] * fu) * (1 - fv) + (e[0] * (1 - fu) + d[0] * fu) * fv
            y = (a[1] * (1 - fu) + b[1] * fu) * (1 - fv) + (e[1] * (1 - fu) + d[1] * fu) * fv
            return x, y
        lines = [(0.15, 0.22, 0.85), (0.15, 0.4, 0.75), (0.15, 0.56, 0.8), (0.15, 0.72, 0.6)]
        total = sum(b - a for a, _, b in lines)
        left = progress * total
        for a, v, b in lines:
            if left <= 0:
                break
            seg = min(b - a, left)
            p = skia.Path()
            n = 14
            for k in range(n + 1):
                u = a + seg * k / n
                x, y = at(u, v + 0.03 * math.sin(u * 40))
                (p.moveTo if k == 0 else p.lineTo)(x, y)
            c.drawPath(p, S(C(30, 50, 140), 4))
            left -= seg
        if progress > 0.95:  # signature loop
            x, y = at(0.6, 0.86)
            c.drawArc(skia.Rect(x - 40, y - 14, x + 40, y + 14), 180, 300, False, S(C(30, 50, 140), 4))
    return ink


# ---------- scenes ----------

def art_hook(c, t):
    bg(c, (12, 20, 45), (40, 30, 60))
    c.drawLine(540, 900, 540, 1920, S(C(255, 255, 255, 60), 4))
    nk, ht = CUE["napkin"], CUE["heart"]
    # left: little Leo + a napkin fluttering in the wind (cloth sim), ink appears on "napkin"
    stand(c, LEO, 250, 1900, 1.2, t, eyes="wide" if t > nk else "open", mouth="O" if t > nk else "smile", brows="up", look=(0.6, -0.5),
          hands=[(-30, 150), (110, -80)])
    PH.cloth(c, t, 270, 960, 300, 240, 1.0, "top", ink=napkin_ink(ease((t - nk + 0.2) / 1.2)))
    c.drawLine(110, 960, 430, 960, S(C(120, 90, 60), 8))
    # right: little Cristiano with a heart beating faster and faster
    beat = 1.6 + 2.8 * ease((t - ht + 0.6) / 1.2)
    ph = (t * beat) % 1
    pulse = math.exp(-ph * 8)
    stand(c, CR, 830, 1900, 1.2, t, eyes="wide" if t > ht else "open", mouth="O" if t > ht else "smile", brows="up", look=(-0.6, -0.5),
          hands=[(-60, 60), (40, 150)])
    heart_shape(c, 830, 1260, 0.75 + 0.18 * pulse)
    glow(c, 830, 1250, 180, (255, 80, 90), int(60 + 120 * pulse))
    ecg(c, 650, 1060, 360, 120, t, 70 + 110 * ease((t - ht) / 1.0))
    # a ball bouncing across the split line from frame 0
    x, y, rot, sq, _ = PH.ball_path(t, 470, 1500, 120, -200, 1880, 44, t_start=0.0)
    if x < 1000:
        PH.draw_ball(c, x, y, 44, rot, sq, shadow_floor=1890)


def art_both(c, t):
    stadium(c, t)
    nv = CUE["never"]
    stand(c, LEO, 330, 1880, 1.15, t, eyes="sad" if t > nv else "open", mouth="frown" if t > nv else "smile", brows="sad" if t > nv else "up",
          look=(0.5, 0.4), hands=[(-30, 150), (30, 150)])
    stand(c, CR, 760, 1880, 1.15, t, eyes="sad" if t > nv else "open", mouth="frown" if t > nv else "smile", brows="sad" if t > nv else "up",
          look=(-0.5, 0.4), hands=[(-30, 150), (30, 150)])
    # the ball rolls between them, bounces and finally stops
    x, y, rot, sq, hit = PH.ball_path(t, 540, 1100, 140, 0, 1880, 46, e=0.55, mu=0.8)
    PH.draw_ball(c, x, y, 46, rot, sq, shadow_floor=1890)
    PH.dust(c, t, hit, x, 1880)
    q = pop_in(t, nv + 0.2)
    if q > 0:
        c.drawString("?", 520, 1180, skia.Font(FB, 150 * q), P(C(255, 220, 120)))


def art_growth(c, t):
    bg(c, (230, 225, 210), (200, 190, 170))
    c.drawRect(skia.Rect(0, 1700, W, H), P(C(150, 120, 90)))
    for k in range(11):  # height chart on the wall
        y = 1700 - k * 90
        c.drawLine(80, y, 160, y, S(C(90, 70, 50), 4))
        c.drawString(f"{100 + k * 10}", 170, y + 10, skia.Font(FB, 28), P(C(90, 70, 50)))
    gr = CUE["growing"]
    grow = ease(t / max(1.0, gr))  # the other kids keep growing, Leo doesn't
    for i, x in enumerate((420, 870)):
        s = 0.9 + 0.35 * grow
        stand(c, KIDS[i], x, 1700, s, t, eyes="open", mouth="smile", brows="flat", look=(1 if x < 600 else -1, 0), hands=[(-30, 150), (30, 150)])
    stand(c, LEO, 640, 1700, 0.85, t, eyes="sad" if t > gr else "open", mouth="frown" if t > gr else "smile", brows="sad", look=(0, -0.6),
          hands=[(-30, 150), (30, 150)])
    th = CUE["thousand"]
    if t > th - 0.2:  # the monthly price tag swings in on a spring
        k = pop_in(t, th - 0.2)
        sw = PH.spring_v(t, th, 18, 1.6, 2.0)
        c.save()
        c.translate(870, 880)
        c.rotate(sw)
        c.scale(k, k)
        c.drawLine(0, -90, 0, 0, S(C(80, 60, 40), 4))
        blob(c, rrect(-150, 0, 150, 120, 16), (255, 230, 140), 1.1, 0.8)
        c.drawString("$1,000", -110, 60, skia.Font(FB, 64), P(C(170, 40, 40)))
        c.drawString("/ MONTH", -80, 100, skia.Font(FB, 34), P(C(120, 60, 40)))
        c.restore()


def art_night(c, t):
    bg(c, (10, 12, 35), (35, 35, 70))
    c.drawCircle(860, 1050, 60, P(C(240, 240, 220)))
    glow(c, 860, 1050, 240, (200, 210, 255), 70)
    for k in range(30):
        r = random.Random(k)
        c.drawCircle(r.uniform(0, W), r.uniform(900, 1300), 2 + (math.sin(t * 2 + k) + 1), P(C(255, 255, 240, 160)))
    c.drawRect(skia.Rect(0, 1650, W, H), P(C(50, 45, 70)))
    blob(c, rrect(120, 1520, 980, 1680, 30), (90, 110, 170), 1.1, 0.8)  # bed
    blob(c, rrect(150, 1460, 380, 1540, 30), (240, 240, 250), 1.05, 0.85)
    ni = CUE["night"]
    # calendar pages tear off and fall with air drag + flutter: "every night"
    for i in range(8):
        t0 = 0.3 + i * 0.45
        k = t - t0
        cx, cy = 300, 1180
        blob(c, rrect(cx - 90, cy - 110, cx + 90, cy + 90, 8), (245, 240, 230), 1.03, 0.88)
        c.drawRect(skia.Rect(cx - 90, cy - 110, cx + 90, cy - 70), P(C(200, 50, 50)))
        if 0 < k < 2.0:
            drag = 2.2
            px = cx + 220 * (1 - math.exp(-drag * k)) + 40 * math.sin(k * 7 + i)
            py = cy + 1100 / drag * (k - (1 - math.exp(-drag * k)) / drag)
            c.save()
            c.translate(px, py)
            c.rotate(40 * math.sin(k * 6 + i))
            c.scale(1, 0.4 + 0.6 * abs(math.cos(k * 5 + i)))
            blob(c, rrect(-80, -90, 80, 90, 6), (245, 240, 230), 1.03, 0.88)
            c.drawString(str(12 + i), -30, 20, skia.Font(FB, 60), P(C(60, 50, 50)))
            c.restore()
    stand(c, LEO, 640, 1700, 1.05, t, eyes="squint", mouth="frown", brows="angry", look=(0.4, 0.8), hands=[(60, 140), (120, 160)], tilt=-6)
    if t > CUE["legs"] - 0.6:  # small injector pen at the leg (non-graphic)
        hx, hy = 640 + 160, 1700 - 80
        blob(c, rrect(hx - 60, hy - 14, hx + 40, hy + 14, 10), (230, 235, 245), 1.2, 0.75)
        c.drawRect(skia.Rect(hx + 40, hy - 6, hx + 60, hy + 6), P(C(120, 190, 255)))
        sparkle(c, hx + 70, hy - 20, 8, 200, (200, 230, 255))


def art_deal(c, t):
    bg(c, (45, 30, 25), (95, 65, 45))
    for k in range(6):  # restaurant: warm lamps
        x = 100 + k * 180
        c.drawLine(x, 860, x, 980, S(C(40, 30, 25), 4))
        blob(c, oval(x, 1000, 50, 24), (240, 200, 120))
        glow(c, x, 1010, 160, (255, 200, 120), int(100 * flicker(t, k)))
    c.drawRect(skia.Rect(0, 1650, W, H), P(C(70, 45, 30)))
    blob(c, rrect(220, 1460, 860, 1520, 12), (230, 225, 215))  # tablecloth
    c.drawRect(skia.Rect(240, 1520, 840, 1650), P(C(210, 205, 195)))
    bc, nk, wr = CUE["barcelona"], CUE["napkin4"], CUE["wrote"]
    x, walk = (lambda k: (-160 + 360 * k, (360 * k) / 40 if t < 1.8 else None))(ease(min(1, t / 1.8)))
    talking = 1.8 < t < nk - 0.3
    mouth_d = ("O" if (t * 6) % 1 < 0.5 else "smile") if talking else ("grin" if t > wr else "smile")
    hand_r = (150, 20 + 50 * math.sin(t * 4.5)) if talking else (150, 60 if t < nk else 30 + 10 * math.sin(t * 9))
    stand(c, DIRECTOR, x, 1880, 1.25, t, walk=walk, eyes="open", mouth=mouth_d, brows="up", look=(1, 0.5),
          hands=[(-30, 150), hand_r])
    nod = 5 * math.sin(t * 5) if talking else 2 * math.sin(t * 1.6)
    stand(c, LEO, 880, 1880 - 18 * abs(math.sin(t * 3.2)) * (1 if talking else 0), 1.0, t, eyes="wide" if t > wr else "open",
          mouth="grin" if t > wr else "smile", brows="up", look=(-1, 0.3), hands=[(-30, 150), (30, 150)], tilt=nod)
    if t > nk - 0.3:  # the napkin, grabbed and laid flat; the pen writes the deal (cloth with almost no wind)
        PH.cloth(c, t, 560, 1290, 300, 170, 0.15, "top", ink=napkin_ink(ease((t - wr + 0.1) / 1.6)))
        px = 450 + 220 * ease((t - wr) / 1.6) % 220 if t > wr else 450
        c.drawLine(px, 1360, px + 50, 1290, S(C(30, 30, 40), 10))


def art_auction(c, t):
    U.T_EIGHT = CUE["million"] - 0.4
    bg(c, (30, 15, 25), (80, 30, 45))
    c.drawRect(skia.Rect(0, 1650, W, H), P(C(70, 30, 40)))
    blob(c, rrect(330, 1050, 750, 1400, 16), (200, 160, 70), 1.3, 0.7)  # gold frame
    c.drawRect(skia.Rect(360, 1080, 720, 1370), P(C(30, 25, 35)))
    PH.cloth(c, t + 2.0, 540, 1120, 300, 200, 0.0, "top", ink=napkin_ink(1.0))
    glow(c, 540, 1220, 260, (255, 230, 170), 60)
    ml = CUE["million"]
    # gavel: pivots at the hand end, the head swings down onto the block on "million", recoils on a spring
    swing = 55 * (1 - ease((t - ml + 0.22) / 0.22)) + 8 * abs(PH.spring_v(t, ml, 1, 3, 6))
    blob(c, rrect(660, 1580, 860, 1625, 10), (100, 65, 35))
    c.save()
    c.translate(990, 1530)
    c.rotate(swing)
    blob(c, rrect(-230, -11, 0, 11, 6), (140, 90, 50))
    blob(c, rrect(-290, -45, -190, 50, 14), (120, 75, 40), 1.3, 0.7)
    c.restore()
    PH.dust(c, t, ml, 760, 1590, (255, 220, 160))
    for x, y, r, face, speed in U.coins_at(t):
        U.draw_coin(c, x, y, r, face, speed)
    PH.confetti(c, t, ml + 0.05, 540, 1100, 70, 3)


def art_cry(c, t):
    stadium(c, t, night=False)
    bb = CUE["baby"]
    # teammates pass the ball to each other (parabolic passes), never to him
    xs = [200, 520, 880]
    seg = 0.9
    k = int(t / seg) % 2
    u = (t % seg) / seg
    a, b = (xs[1], xs[2]) if k == 0 else (xs[2], xs[1])
    bx = a + (b - a) * u
    by = 1560 - 300 * math.sin(math.pi * u)
    for i, x in enumerate(xs[1:]):
        stand(c, KIDS[i + 1], x, 1880, 1.0, t, eyes="open", mouth="grin", brows="up", look=(1 if x < 700 else -1, -0.3),
              hands=[(-30, 150), (30, 150)], squash=0.04 * PH.spring_v(t % seg, 0.0, 1, 3, 5))
    PH.draw_ball(c, bx, by, 38, t * 400, 0.0, shadow_floor=1890)
    cry = t > CUE["cried"]
    stand(c, CR, 200, 1880, 1.05, t, eyes="closed" if cry else "open", mouth="frown" if cry else "smile", brows="sad", look=(1, 0),
          hands=[(-30, 150), (30, 150)], tilt=4 * math.sin(t * 10) if cry else 0)
    if cry:  # tears fly out with gravity and splash on the grass
        for i in range(10):
            t0 = CUE["cried"] + i * 0.28
            k2 = t - t0
            if 0 < k2 < 0.9:
                side = 1 if i % 2 else -1
                tx = 200 + side * (40 + 260 * k2)
                ty = head_c(1880, 1.05) - 10 - 500 * k2 + PH.G * 0.5 * k2 * k2
                if ty < 1880:
                    tear(c, tx, ty, 11)
                else:
                    PH.dust(c, t, t0 + 0.6, tx, 1880, (150, 210, 255), 4)


def art_heart(c, t):
    bg(c, (15, 25, 35), (40, 60, 70))
    c.drawRect(skia.Rect(0, 1700, W, H), P(C(200, 210, 215)))
    blob(c, rrect(160, 1560, 920, 1640, 20), (240, 245, 250), 1.05, 0.85)  # hospital bed
    rc, ls, bk = CUE["racing"], CUE["laser"], CUE["back"]
    bpm = 80 + 120 * ease((t - rc + 0.6) / 0.8) * (1 - ease((t - ls - 0.3) / 0.8))
    ecg(c, 160, 1080, 760, 170, t, bpm)
    ph = (t * bpm / 60) % 1
    pulse = math.exp(-ph * 8)
    if t < bk - 0.2:
        stand(c, CR, 540, 1700, 1.1, t, eyes="closed" if t > ls else "wide", mouth="smile" if t > ls else "O", brows="flat", look=(0, -0.3),
              hands=[(-30, 150), (30, 150)])
        heart_shape(c, 540, 1520, 0.32 + 0.07 * pulse)
        if ls < t < ls + 1.6:  # laser beam sweeping the heart
            c.drawLine(900, 900, 540 + 30 * math.sin(t * 12), 1520, S(C(255, 60, 80, 200), 8))
            glow(c, 540, 1520, 120, (255, 60, 80), 160)
    else:  # back training days later: kicks a ball that flies, bounces and rolls
        c.drawRect(skia.Rect(0, 1500, W, H), P(Shader=lin((0, 1500), (0, H), [C(60, 150, 70), C(30, 100, 45)])))
        c.drawLine(0, 1600, W, 1600, S(C(255, 255, 255, 110), 6))
        stand(c, CR, 300, 1880, 1.2, t, eyes="open", mouth="grin", brows="angry", look=(1, 0), hands=[(-60, 60), (60, 60)],
              squash=0.05 * PH.spring_v(t, bk, 1, 3, 5))
        x, y, rot, sq, hit = PH.ball_path(t, 420, 1830, 380, -1500, 1880, 44, t_start=bk)
        PH.draw_ball(c, min(x, 1000), y, 44, rot, sq, shadow_floor=1890)
        PH.dust(c, t, hit, min(x, 1000), 1880)


def art_reagan(c, t):
    bg(c, (40, 30, 30), (90, 70, 55))
    c.drawRect(skia.Rect(0, 1650, W, H), P(C(110, 80, 55)))
    blob(c, rrect(560, 1100, 1000, 1460, 30), (110, 80, 50), 1.2, 0.75)  # old TV
    c.drawRoundRect(skia.Rect(600, 1140, 900, 1400), 26, 26, P(C(40, 60, 80)))
    c.save()
    c.clipRect(skia.Rect(600, 1140, 900, 1400))
    c.drawPaint(P(Shader=lin((0, 1140), (0, 1400), [C(240, 180, 110), C(180, 110, 60)])))
    hx = 750 + 30 * math.sin(t * 1.5)  # a cowboy-movie silhouette on screen (generic, not a likeness)
    c.drawRect(skia.Rect(hx - 30, 1260, hx + 30, 1400), P(C(40, 25, 20)))
    c.drawCircle(hx, 1240, 26, P(C(40, 25, 20)))
    c.drawRect(skia.Rect(hx - 50, 1205, hx + 50, 1215), P(C(40, 25, 20)))
    c.drawRect(skia.Rect(hx - 26, 1175, hx + 26, 1210), P(C(40, 25, 20)))
    for k in range(40):  # TV noise
        r = random.Random(int(t * 24) * 100 + k)
        c.drawRect(skia.Rect.MakeXYWH(r.uniform(600, 895), r.uniform(1140, 1396), 6, 3), P(C(255, 255, 255, 40)))
    c.restore()
    for k in (-1, 1):
        c.drawLine(750 + k * 60, 1100, 750 + k * 130, 980, S(C(60, 60, 60), 5))
    rn = CUE["ronald"]
    stand(c, DAD, 320, 1880, 1.25, t, eyes="open", mouth="grin", brows="up", look=(1, -0.2), hands=[(-30, 150), (140, -60 if t > rn else 60)])
    k = pop_in(t, rn + 0.3)
    if k > 0:  # baby in a basket with a name card
        blob(c, rrect(640, 1720, 840, 1800, 20), (200, 150, 90), 1.2, 0.7)
        blob(c, oval(740, 1710, 46, 40), (220, 175, 140), 1.15, 0.8)
        c.save()
        c.translate(740, 1580)
        c.scale(k, k)
        c.rotate(PH.spring_v(t, rn + 0.3, 8, 2, 3))
        fnt = skia.Font(FB, 52)
        tw = fnt.measureText("RONALDO")
        blob(c, rrect(-tw / 2 - 30, -44, tw / 2 + 30, 44, 12), (255, 245, 220), 1.03, 0.88)
        c.drawString("RONALDO", -tw / 2, 18, fnt, P(C(200, 40, 50)))
        c.restore()


def trophy(c, x, y, s):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    blob(c, rrect(-50, -30, 50, 0, 6), (90, 60, 30))
    p = skia.Path()
    p.moveTo(-70, -200)
    p.cubicTo(-70, -100, -20, -70, -12, -40)
    p.lineTo(12, -40)
    p.cubicTo(20, -70, 70, -100, 70, -200)
    p.close()
    blob(c, p, (250, 200, 60), 1.45, 0.6)
    for side in (-1, 1):
        c.drawArc(skia.Rect(side * 70 - 34, -190, side * 70 + 34, -120), 90 if side > 0 else -90, 180 * side, False, S(C(230, 175, 40), 10))
    c.restore()


def art_greatest(c, t):
    stadium(c, t)
    gt = CUE["greatest"]
    stand(c, LEO_PRO, 330, 1880, 1.2, t, eyes="closed" if t > gt else "open", mouth="laugh" if t > gt else "grin", brows="up", look=(0, -0.3),
          hands=[(-70, -180), (70, -180)] if t > gt else [(-30, 150), (30, 150)])
    stand(c, CR_PRO, 760, 1880, 1.2, t, eyes="closed" if t > gt else "open", mouth="laugh" if t > gt else "grin", brows="up", look=(0, -0.3),
          hands=[(-70, -180), (70, -180)] if t > gt else [(-30, 150), (30, 150)])
    if t < gt - 0.1:  # keepy-uppy between them: real gravity bounce with squash at each touch
        per = 0.62
        u = (t % per) / per
        by = 1834 - 340 * 4 * u * (1 - u)
        sq = 0.25 * max(0.0, 1 - min(u, 1 - u) / 0.08)
        PH.draw_ball(c, 545, by, 46, t * 300, sq, shadow_floor=1890)
    else:  # last few bounces that die out (restitution) and the ball rests between them
        bx, by, rot, sq, _ = PH.ball_path(t, 545, 1834, 0, -900, 1880, 46, t_start=gt - 0.1)
        PH.draw_ball(c, bx, by, 46, rot, sq, shadow_floor=1890)
    for i, x in enumerate((105, 975)):  # trophies drop, bounce and settle (spring)
        t0 = gt - 0.2 + i * 0.18
        if t > t0:
            k = t - t0
            fall = min(1.0, (k / 0.4) ** 2)
            y = 1100 + 780 * fall - (90 * PH.spring_v(t, t0 + 0.4, 1, 2.5, 5) if k > 0.4 else 0)
            trophy(c, x, y, 0.55)
            if 0.4 < k < 1.2:
                PH.dust(c, t, t0 + 0.4, x, 1880, (255, 230, 150), 5)
    PH.confetti(c, t, gt, 540, 1000, 90, 7, 1.2)


def art_vote(c, t):
    bg(c, (25, 15, 40), (60, 25, 70))
    for k in range(14):
        a = k / 14 * 2 * math.pi + t * 0.4
        p = skia.Path()
        p.moveTo(540, 1350)
        p.lineTo(540 + math.cos(a) * 1500, 1350 + math.sin(a) * 1500)
        p.lineTo(540 + math.cos(a + 0.13) * 1500, 1350 + math.sin(a + 0.13) * 1500)
        p.close()
        c.drawPath(p, P(C(255, 200, 255, 16)))
    # two vote bars racing, each bar a spring that overshoots
    c.drawRect(skia.Rect(0, 1660, W, H), P(C(40, 20, 50)))
    for i, (x, col, who) in enumerate(((300, SKY, LEO_PRO), (780, (230, 60, 70), CR_PRO))):
        target = 0.5 + 0.12 * math.sin(t * 1.3 + i * 2)
        h = 520 * (target + 0.08 * PH.spring_v(t, 0.2 + i * 0.1, 1, 1.5, 1.5))
        blob(c, rrect(x - 110, 1660 - h, x + 110, 1660, 18), col, 1.3, 0.7)
        stand(c, who, x, 1900, 0.75, t, eyes="open", mouth="grin", brows="up", look=(0, -0.5), hands=[(-50, -160), (50, -160)])
    cm = CUE["comments"]
    for i in range(12):  # comment bubbles fly up with drag
        t0 = cm - 0.4 + i * 0.12
        k = t - t0
        if k > 0:
            r = random.Random(i)
            x = 540 + r.uniform(-380, 380) + 30 * math.sin(k * 4 + i)
            y = 1600 - 900 * (1 - math.exp(-2.2 * k))
            a = int(255 * max(0, min(1, (2.2 - k) / 0.5)))
            if a <= 0:
                continue
            c.saveLayerAlpha(None, a)
            blob(c, rrect(x - 70, y - 40, x + 70, y + 40, 20), (250, 250, 255), 1.03, 0.9)
            c.drawString("GOAT", x - 52, y + 14, skia.Font(FB, 38), P(C(*(SKY if i % 2 else (230, 60, 70)))))
            c.restore()


def art_cta(c, t):
    U.T_EIGHT = -10
    U.background(c, t, 0)
    U.spotlight(c, t, 0)
    c.drawPaint(P(C(10, 6, 14, 120)))
    draw_cta2(c, t, CUE["like"], CUE["sub"])


ART = [art_hook, art_both, art_growth, art_night, art_deal, art_auction, art_cry, art_heart, art_reagan, art_greatest, art_vote, art_cta]
PUSH = [(1.0, 1.05), (1.0, 1.06), (1.0, 1.05), (1.0, 1.06), (1.0, 1.06), (1.0, 1.07), (1.0, 1.05), (1.0, 1.05), (1.0, 1.06), (1.0, 1.06), (1.0, 1.04), (1.0, 1.0)]
ANCHOR = [(540, 1500), (540, 1600), (540, 1500), (540, 1500), (540, 1450), (540, 1300), (540, 1600), (540, 1400), (540, 1500), (540, 1500), (540, 1450), (540, 1080)]


def render_art(i, t, dur):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    z0, z1 = PUSH[i]
    z = z0 + (z1 - z0) * ease(t / dur)
    ax, ay = ANCHOR[i]
    c.save()
    c.translate(ax, ay)
    c.scale(z, z)
    c.translate(-ax + (math.sin(t * 0.5) * 6 if i != 11 else 0), -ay + (math.cos(t * 0.4) * 5 if i != 11 else 0))
    ART[i](c, t)
    c.restore()
    if i != 11:
        snap = surf.makeImageSnapshot()
        c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=U.BLOOM, ImageFilter=skia.ImageFilters.Blur(24, 24), BlendMode=skia.BlendMode.kPlus, Alphaf=0.3))
        c.drawPaint(P(Shader=rad(540, 1100, 1250, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 190)], [0, 0.5, 1])))
        c.drawRect(skia.Rect(0, 0, W, 900), P(Shader=lin((0, 0), (0, 900), [C(5, 4, 10, 170), C(5, 4, 10, 0)])))
        c.drawImageRect(U.GRAIN[int(t * 30) % len(U.GRAIN)], skia.Rect(0, 0, W, H), skia.SamplingOptions(), P(Alphaf=0.05, BlendMode=skia.BlendMode.kOverlay))
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
    line(img, "Messi's first contract", 230, F_MID)
    line(img, "was written on a", 330, F_MID)
    slam(img, "NAPKIN!", 430, t, CUE["napkin"] - 0.1, GOLD, 170)
    text_block(img, "Ronaldo: HEART SURGERY at 15!", font(FONT_B, 58), 650, t, RED, CUE["heart"])
    impact(img, t, CUE["napkin"] + 0.1, 18)


def tx_both(img, t):
    title(img, t, "Both almost NEVER", "became footballers", CUE["football"])


def tx_growth(img, t):
    tag(img, "MESSI, AGE 11", t, (70, 120, 190))
    title(img, t, "He stopped growing", "A hormone problem... very expensive", CUE["hormone"])


def tx_night(img, t):
    title(img, t, "Every single night...", "...an injection in his legs", CUE["legs"], sub_color=SKY)


def tx_deal(img, t):
    tag(img, "BARCELONA, 2000", t, (150, 40, 80))
    title(img, t, "The deal on a NAPKIN", "Written by a club director", CUE["wrote"], sub_color=GOLD)


def tx_auction(img, t):
    title(img, t, "That napkin sold for...", y=260)
    slam(img, "~$1 MILLION", 420, t, CUE["million"] - 0.1, GOLD, 130)
    impact(img, t, CUE["million"] + 0.1, 16)


def tx_cry(img, t):
    tag(img, "PORTUGAL", t, (40, 120, 70))
    title(img, t, "No pass? He cried.")
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 640, "CRY BABY", t, CUE["baby"], col=SKY, size=110)
    impact(img, t, CUE["baby"] + 0.15, 12)


def tx_heart(img, t):
    title(img, t, "Ronaldo, age 15", "His heart was racing way too fast", CUE["racing"], sub_color=RED)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "BACK IN DAYS", t, CUE["back"], col=GREEN, size=96)
    impact(img, t, CUE["back"] + 0.15, 12)


def tx_reagan(img, t):
    title(img, t, "Named after RONALD Reagan", "...his dad's favorite actor", CUE["actor"], sub_color=GOLD)


def tx_greatest(img, t):
    title(img, t, "They almost didn't make it...", y=260)
    slam(img, "GREATEST", 420, t, CUE["greatest"] - 0.1, GOLD, 150)
    impact(img, t, CUE["greatest"] + 0.1, 16)


def tx_vote(img, t):
    slam(img, "WHO'S BETTER?", 300, t, CUE["better"] - 0.1, (255, 255, 255), 108)
    text_block(img, "Tell me in the comments!", font(FONT_B, 60), 520, t, GOLD, CUE["comments"] - 0.3)
    impact(img, t, CUE["better"] + 0.1, 14)


def tx_cta(img, t):
    pass


TEXT = [tx_hook, tx_both, tx_growth, tx_night, tx_deal, tx_auction, tx_cry, tx_heart, tx_reagan, tx_greatest, tx_vote, tx_cta]
base.TRANSITION = splat

if __name__ == "__main__":
    voice = f"{VOICE_DIR}/voice.mp3"
    tl = Timeline(voice)
    firsts = ["both of", "eleven", "his family", "than|then barcelona", "years later", "portugal", "fifteen", "fun fact", "almost didn't",
              "so who's", "learn"]
    after, starts = 0.3, [0.0]
    for ph in firsts:
        w = tl.find(ph, after)
        before = [p for p in tl.pauses if p[1] <= w + 0.2 and p[0] >= after - 0.3]
        cut = max((before[-1][0] + before[-1][1]) / 2, before[-1][1] - 0.25) if before else w - 0.15
        starts.append(round(cut, 3))
        after = w + 0.3
    total = round(tl.length + TAIL, 2)
    durs = [round(b - a, 2) for a, b in zip(starts, starts[1:] + [total])]
    S0 = starts
    f = lambda phrase, sc, lead=0.1: round(tl.find(phrase, S0[sc]) - S0[sc] - lead, 2)
    CUE.update(d=durs, S=S0,
               napkin=f("napkin", 0, 0.0), heart=f("heart", 0),
               never=f("never", 1), football=f("football", 1),
               growing=f("growing", 2), hormone=f("hormone", 2), thousand=f("thousand", 2),
               night=f("night", 3), legs=f("legs", 3),
               barcelona=f("barcelona", 4), napkin4=f("napkin", 4), wrote=f("wrote", 4),
               million=f("million", 5, 0.0),
               cried=f("cried", 6), baby=f("baby", 6, 0.15),
               racing=f("racing", 7), laser=f("laser", 7), back=f("back", 7, 0.15),
               ronald=f("ronald", 8), actor=f("actor", 8),
               greatest=f("greatest", 9, 0.0),
               better=f("better", 10, 0.0), comments=f("comments", 10))
    CUE["like"] = round(tl.find("like|within", S0[11]) - S0[11] - 0.05, 2)
    CUE["sub"] = round(CUE["like"] + 0.75, 2)
    print("starts:", S0)
    print("durations:", durs, round(sum(durs), 2))
    print("cues:", {k: v for k, v in CUE.items() if k not in ("d", "S")})
    print("subscribed visible for", round(durs[-1] - CUE["sub"], 2), "s")
    json.dump({"starts": S0, "durs": durs, "cues": {k: v for k, v in CUE.items() if k not in ("d", "S")}}, open(f"{VOICE_DIR}/plan.json", "w"), indent=1)
    if STILLS:
        out = os.environ.get("STILLS_DIR", VOICE_DIR + "/stills")
        os.makedirs(out, exist_ok=True)
        for i in ONLY:
            for tt in STILLS:
                img = Image.new("RGBA", (W, H))
                scene(i, TEXT[i])(img, ImageDraw.Draw(img), float(tt))
                img.convert("RGB").save(f"{out}/goat_{i}_{tt}.png")
        sys.exit()
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), scene(i, TEXT[i])) for i, dd in enumerate(durs)]
    if ONLY:
        base.SCENES[:] = [s for i, s in enumerate(base.SCENES) if i in ONLY]
    ST, C_ = S0, CUE
    ev = [("whoosh", s) for s in ST[1:]]
    ev += [("thud", C_["napkin"]), ("ding", C_["heart"])]
    # ball bounces in the hook and the training scene get a real thud on each impact
    for sc, args, ts in ((0, (470, 1500, 120, -200, 1880, 44), 0.0), (1, (540, 1100, 140, 0, 1880, 46), 0.0)):
        last = -1
        for k in range(int(durs[sc] * 30)):
            tt = k / 30
            *_, hit = PH.ball_path(tt, *args, t_start=ts) if sc else PH.ball_path(tt, *args, t_start=ts)
            if hit > last + 0.05 and hit >= 0:
                ev.append(("pop", ST[sc] + hit))
                last = hit
    ev += [("pop", ST[2] + C_["thousand"]),
           ("ding", ST[4] + C_["wrote"]),
           ("thud", ST[5] + C_["million"]), ("ding", ST[5] + C_["million"] + 0.05),
           ("thud", ST[6] + C_["baby"] + 0.15),
           ("ding", ST[7] + C_["laser"]), ("thud", ST[7] + C_["back"] + 0.15), ("pop", ST[7] + C_["back"] + 0.15),
           ("pop", ST[8] + C_["ronald"] + 0.3),
           ("thud", ST[9] + C_["greatest"]), ("ding", ST[9] + C_["greatest"] + 0.05),
           ("thud", ST[10] + C_["better"]),
           ("click", ST[11] + C_["like"]), ("ding", ST[11] + C_["like"] + 0.03),
           ("click", ST[11] + C_["sub"]), ("ding", ST[11] + C_["sub"] + 0.35)]
    ev += [("click", ST[9] + C_["greatest"] - 0.2 + i * 0.18 + 0.4) for i in range(2)]  # trophies land
    ev += [("pop", ST[10] + C_["comments"] - 0.4 + i * 0.12) for i in range(12)]  # comment bubbles
    ev += [("click", ST[5] + C_["million"] - 0.4 + 0.35 + i * 0.09 + (i % 3) * 0.03) for i in range(10)]  # coins
    ev = [(k, round(v, 3)) for k, v in ev if 0 <= v < total]
    audio.music("music.wav", total, bpm=112, seed=41)
    audio.sfx("sfx.wav", total, ev)
    base.OUT = "base_goat.mp4"
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_goat.mp4", voice, "music.wav", "sfx.wav", OUTFILE)
    print("wrote", OUTFILE)
