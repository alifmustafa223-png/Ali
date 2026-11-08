"""YouTube Short: "Purple Was Worth More Than GOLD?!" (Skia toon, unedited vidIQ "Chris" voice, new CTA v2).

Topic from vidIQ outliers: "Dark history of colors" (192x breakout, 374K views on a 1.4K-sub channel) +
"products invented by accident" (23-41x). Facts: Tyrian purple from murex sea snails (Phoenician Tyre), roughly
10,000 snails per gram of dye, workshops famous for the stench; purple silk worth more than its weight in gold in
late Rome; sumptuary laws reserved purple for emperors; 1856, 18-year-old William Perkin tried to synthesise quinine
(malaria), got a black sludge, cleaned the flask with alcohol and found mauveine - the first synthetic dye; he left
the Royal College of Chemistry, opened a factory and grew rich; Queen Victoria wore mauve (1862), making it popular.

Usage: python make_purple.py final.mp4 [scene,...] [t1,...]   stills: STILLS_DIR=dir python make_purple.py x 0,1 1.0
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
sys.argv = [sys.argv[0], "base_purple.mp4"]
sys.path.insert(0, "..")

import audio  # noqa: E402
import make_ketchup  # noqa: E402
import make_short as base  # noqa: E402
import ultimate as U  # noqa: E402
from cta2 import draw_cta2  # noqa: E402
from fx import impact  # noqa: E402
from make_honey import slam  # noqa: E402
from make_ketchup import splat, stamp  # noqa: E402
from make_short import FONT_B, F_MID, H, W, font, tag, text_block  # noqa: E402
from style import heading  # noqa: E402
from timing import Timeline  # noqa: E402
from toon import *  # noqa: E402,F401,F403

GOLD, PURPLE, LILAC, RED, GREEN = (255, 200, 60), (175, 70, 230), (215, 160, 255), (235, 60, 60), (110, 220, 130)
PURP = (120, 40, 170)
make_ketchup.SPLAT_COLOR = (250, 195, 50)
base.HOOK_SKIP = 0.0
base.CRF = 16
CUE = {}
VOICE_DIR = "../purple"
TAIL = 1.2

DYER = dict(skin=(200, 145, 100), hair="cap", hair_col=(60, 40, 30), beard=(60, 40, 30), coat=(200, 180, 140), apron=(130, 50, 160),
            pants=(110, 90, 70), nose="long")
EMPEROR = dict(skin=(240, 200, 170), hair="curly", hair_col=(80, 60, 40), coat=PURP, dress=PURP, trim=GOLD, hat="laurel", nose="long")
GUARD = dict(skin=(225, 180, 145), hair="neat", hair_col=(40, 30, 25), coat=(180, 50, 50), trim=(220, 180, 80), pants=(140, 110, 70), nose="long")
COMMONER = dict(skin=(240, 200, 170), hair="neat", hair_col=(110, 70, 40), coat=PURP, pants=(110, 90, 70), nose="small")
PERKIN = dict(skin=(245, 210, 180), hair="neat", hair_col=(70, 45, 30), coat=(245, 245, 248), vest=(60, 60, 80), pants=(55, 55, 70),
              collar=(255, 255, 255), nose="small")
VICTORIA = dict(skin=(245, 215, 195), hair="neat", hair_col=(80, 55, 40), coat=(140, 75, 175), dress=(140, 75, 175), crown=True, pearls=True,
                lips=True, nose="small")
KIDP = dict(KID, coat=(160, 70, 220))


def blinking(t, ph=0.0):
    return ((t + ph) % 3.3) < 0.11


def pop_in(t, at, dur=0.35):
    return out_back((t - at) / dur, 2.2) if t > at else 0.0


def head_top(y, s):
    return y + s * (-262 - 70 - 88)


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


def walk_in(t, x0, x1, dur=1.6):
    k = ease(min(1, t / dur))
    x = x0 + (x1 - x0) * k
    return x, ((x - x0) / 40 * (1 if x1 > x0 else -1)) if t < dur else None


# ---------- props ----------

def snail(c, x, y, s, t, face=True, cracked=0.0):
    """Murex-style sea snail: spiky spiral shell + soft body with eye stalks."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = skia.Path()
    body.moveTo(-110, 0)
    body.cubicTo(-110, -40, 60, -46, 110, -10)
    body.cubicTo(130, 4, 120, 20, 90, 20)
    body.lineTo(-100, 20)
    body.close()
    blob(c, body, (210, 175, 200), 1.2, 0.75)
    for side in (-1, 1):
        ex = 95 + side * 10 + 4 * math.sin(t * 3 + side)
        c.drawLine(92, -20, ex, -80, S(C(190, 150, 180), 9))
        c.drawCircle(ex, -84, 10, P(C(250, 250, 250)))
        c.drawCircle(ex + 2, -84, 5, P(C(30, 20, 30)))
    if cracked < 1:
        c.save()
        c.translate(-20, -70)
        c.rotate(-8 * cracked)
        shell = skia.Path()
        for k in range(10):  # spikes
            a = k / 10 * 2 * math.pi
            r = 92 if k % 2 == 0 else 70
            (shell.moveTo if k == 0 else shell.lineTo)(math.cos(a) * r, math.sin(a) * r * 0.85)
        shell.close()
        blob(c, shell, (225, 200, 175), 1.25, 0.7)
        for k in range(3):  # spiral
            c.drawArc(skia.Rect(-60 + k * 14, -50 + k * 12, 60 - k * 14, 50 - k * 12), 20 + k * 40, 260, False, S(C(160, 110, 140), 7))
        c.restore()
    if face:
        c.drawArc(skia.Rect(70, -16, 110, 6), 20, 140, False, S(C(110, 60, 90), 4))
    c.restore()


def drop(c, x, y, r, a=255):
    p = skia.Path()
    p.moveTo(x, y - r * 1.6)
    p.cubicTo(x + r * 0.9, y - r * 0.4, x + r, y + r * 0.6, x, y + r)
    p.cubicTo(x - r, y + r * 0.6, x - r * 0.9, y - r * 0.4, x, y - r * 1.6)
    c.drawPath(p, P(Shader=rad(x - r * 0.3, y - r * 0.3, r * 1.6, [C(230, 150, 255, a), C(*PURP, a)])))
    c.drawCircle(x - r * 0.3, y - r * 0.2, r * 0.22, P(C(255, 255, 255, int(a * 0.8))))


def vat(c, x, y, w, h, t, col=PURP):
    blob(c, rrect(x - w / 2, y - h, x + w / 2, y, 20), (130, 95, 70), 1.2, 0.7)
    c.drawOval(skia.Rect(x - w / 2 + 12, y - h - 18, x + w / 2 - 12, y - h + 22), P(Shader=rad(x, y - h, w / 2, [C(200, 100, 240), C(*col)])))
    for k in range(4):
        ph = (t * 1.2 + k * 0.25) % 1
        c.drawCircle(x - w / 3 + k * w / 4.5, y - h - ph * 30, 8 + 6 * ph, S(C(230, 170, 255, int(230 * (1 - ph))), 3))


def stink(c, x, y, t, ph=0.0, col=(150, 200, 90)):
    for k in range(3):
        p = skia.Path()
        yy = y - ((t * 60 + k * 40 + ph * 30) % 120)
        p.moveTo(x + k * 26 - 26, yy)
        for j in range(4):
            p.quadTo(x + k * 26 - 26 + (12 if j % 2 else -12), yy - j * 20 - 10, x + k * 26 - 26, yy - j * 20 - 20)
        a = int(200 * math.sin(((t * 60 + k * 40 + ph * 30) % 120) / 120 * math.pi))
        c.drawPath(p, S(C(*col, a), 6))


def scale_balance(c, x, y, s, t, tip, left_draw, right_draw):
    """Balance scale; tip > 0 lowers the LEFT pan."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    blob(c, rrect(-20, -380, 20, 0, 8), (200, 160, 60), 1.4, 0.7)
    blob(c, rrect(-120, -20, 120, 20, 10), (180, 140, 50), 1.3, 0.7)
    ang = -12 * tip
    c.save()
    c.translate(0, -380)
    c.rotate(ang)
    blob(c, rrect(-280, -12, 280, 12, 6), (220, 180, 70), 1.4, 0.7)
    c.restore()
    for side, draw in ((-1, left_draw), (1, right_draw)):
        a = math.radians(ang)
        px, py = side * 280 * math.cos(a), -380 + side * 280 * math.sin(a)
        c.drawLine(px, py, px - 70, py + 170, S(C(200, 160, 60), 4))
        c.drawLine(px, py, px + 70, py + 170, S(C(200, 160, 60), 4))
        c.drawArc(skia.Rect(px - 110, py + 130, px + 110, py + 210), 0, 180, True, P(C(220, 180, 70)))
        c.save()
        c.translate(px, py + 165)
        draw(c)
        c.restore()
    c.restore()


def gold_bars(c):
    for k, (dx, dy) in enumerate(((-60, 0), (10, 0), (-25, -40))):
        p = skia.Path()
        p.moveTo(dx - 40, dy)
        p.lineTo(dx + 40, dy)
        p.lineTo(dx + 28, dy - 36)
        p.lineTo(dx - 28, dy - 36)
        p.close()
        blob(c, p, (250, 200, 60), 1.4, 0.7)


def silk(c, w=150, h=90, t=0.0, col=PURP):
    p = skia.Path()
    p.moveTo(-w / 2, 0)
    p.cubicTo(-w / 3, -h - 10 * math.sin(t * 2), w / 3, -h + 10 * math.sin(t * 2), w / 2, 0)
    p.close()
    c.drawPath(p, P(Shader=lin((-w / 2, -h), (w / 2, 0), [C(220, 140, 255), C(*col), C(70, 20, 110)])))
    for k in range(3):
        c.drawLine(-w / 3 + k * w / 3, -h * 0.7, -w / 4 + k * w / 3, -5, S(C(255, 220, 255, 90), 4))


def flask(c, x, y, s, liquid, t, a=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    p = skia.Path()
    p.moveTo(-22, -200)
    p.lineTo(22, -200)
    p.lineTo(22, -110)
    p.lineTo(90, 0)
    p.cubicTo(96, 12, 88, 22, 76, 22)
    p.lineTo(-76, 22)
    p.cubicTo(-88, 22, -96, 12, -90, 0)
    p.lineTo(-22, -110)
    p.close()
    c.save()
    c.clipPath(p, doAntiAlias=True)
    c.drawRect(skia.Rect(-100, -60, 100, 30), P(Shader=lin((0, -60), (0, 30), [C(*[min(255, v + 50) for v in liquid]), C(*liquid)])))
    for k in range(5):
        ph = (t * 1.3 + k * 0.2) % 1
        c.drawCircle(-50 + k * 25, 10 - ph * 70, 5 + 3 * ph, S(C(255, 255, 255, int(200 * (1 - ph))), 2))
    c.restore()
    c.drawPath(p, P(C(220, 240, 255, 50)))
    c.drawPath(p, S(C(230, 245, 255, 230), 6))
    c.drawLine(-14, -180, -14, -120, S(C(255, 255, 255, 140), 6))
    c.restore()


def burst_col(c, x, y, k, col=(200, 120, 255), n=16, reach=420):
    if not 0 <= k < 1:
        return
    for i in range(n):
        a = i / n * 2 * math.pi
        r0, r1 = 60 + reach * 0.6 * ease(k), 90 + reach * ease(k)
        c.drawLine(x + math.cos(a) * r0, y + math.sin(a) * r0, x + math.cos(a) * r1, y + math.sin(a) * r1, S(C(*col, int(255 * (1 - k))), 14 * (1 - k) + 3))


# ---------- scenes ----------

def bg_dark(c, top, bot):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(*top), C(*bot)])))


def art_hook(c, t):
    bg_dark(c, (30, 10, 45), (60, 20, 80))
    for k in range(16):  # rays
        a = k / 16 * 2 * math.pi + t * 0.3
        p = skia.Path()
        p.moveTo(540, 1300)
        p.lineTo(540 + math.cos(a) * 1500, 1300 + math.sin(a) * 1500)
        p.lineTo(540 + math.cos(a + 0.12) * 1500, 1300 + math.sin(a + 0.12) * 1500)
        p.close()
        c.drawPath(p, P(C(230, 170, 255, 16)))
    c.drawRect(skia.Rect(0, 1700, W, H), P(Shader=lin((0, 1700), (0, H), [C(70, 30, 90), C(30, 10, 40)])))
    gd = CUE["gold"]
    tip = 0.25 * math.sin(t * 2.2) if t < gd else 0.25 + 0.75 * ease((t - gd) / 0.35) + 0.05 * spring(t, gd + 0.35, 3, 4)
    scale_balance(c, 540, 1660, 1.15, t, tip, lambda cc: silk(cc, 170, 110, t), gold_bars)
    if t > gd:
        burst_col(c, 540 - 280 * 1.15, 1330, (t - gd) / 0.8)
        glow(c, 540 - 320, 1420, 260, (200, 120, 255), int(110 * min(1, (t - gd) / 0.4)))
    sl = CUE["snail"]
    k = pop_in(t, sl - 0.1)
    if k > 0:
        snail(c, 830, 1720, 1.0 * k, t)
        for j in range(3):  # slime trail
            c.drawOval(skia.Rect(600 + j * 60, 1730, 680 + j * 60, 1748), P(C(220, 170, 255, 140)))


def art_tyre(c, t):
    bg_dark(c, (40, 30, 80), (230, 140, 100))
    c.drawCircle(820, 1150, 90, P(Shader=rad(820, 1150, 90, [C(255, 240, 200), C(255, 170, 90)])))
    glow(c, 820, 1150, 380, (255, 190, 120), 120)
    c.drawRect(skia.Rect(0, 1240, W, 1500), P(Shader=lin((0, 1240), (0, 1500), [C(70, 110, 160), C(40, 70, 120)])))
    for k in range(4):  # city walls
        x = 60 + k * 270
        blob(c, rrect(x, 1060 + (k % 2) * 40, x + 200, 1260, 4), (210, 180, 140), 1.1, 0.8)
        for j in range(4):
            c.drawRect(skia.Rect(x + j * 50, 1040 + (k % 2) * 40, x + j * 50 + 28, 1062 + (k % 2) * 40), P(C(210, 180, 140)))
    c.drawRect(skia.Rect(0, 1500, W, H), P(Shader=lin((0, 1500), (0, H), [C(200, 170, 120), C(140, 110, 75)])))
    vat(c, 760, 1760, 300, 170, t)
    cr = CUE["cracked"]
    x, walk = walk_in(t, -160, 330, 1.6)
    hammer = math.sin(min(1, max(0, (t - cr + 0.25) / 0.35)) * math.pi) if t < cr + 0.6 else 0
    stand(c, DYER, x, 1880, 1.35, t, walk=walk, eyes="squint" if t > cr else "open", mouth="grin", brows="angry", look=(1, 0.6),
          hands=[(-20, 150), (120, 20 - 120 * hammer)])
    snail(c, 560, 1830, 0.7, t, face=False, cracked=ease((t - cr) / 0.3))
    if t > cr:  # shell shards
        k = min(1, (t - cr) / 0.6)
        for j in range(6):
            a = j / 6 * 2 * math.pi
            c.drawCircle(540 + math.cos(a) * 160 * k, 1780 + math.sin(a) * 90 * k + 300 * k * k, 10 * (1 - k) + 2, P(C(225, 200, 175)))
    dp = CUE["drop"]
    if t > dp - 0.3:  # the precious drop falls into the vat
        u = min(1, (t - dp + 0.3) / 0.9)
        drop(c, 640 + 100 * u, 1730 - 60 * math.sin(math.pi * u) + 20 * u, 22)
        if u >= 1:
            glow(c, 760, 1600, 200, (200, 120, 255), 150)


def art_snails(c, t):
    bg_dark(c, (40, 30, 30), (90, 70, 55))
    c.drawRect(skia.Rect(0, 1600, W, H), P(Shader=lin((0, 1600), (0, H), [C(150, 120, 90), C(90, 70, 50)])))
    ten = CUE["ten"]
    n = int(min(60, max(0, (t - ten + 0.4) * 40)))
    r = random.Random(4)
    for i in range(n):  # the growing mountain of snails
        row = int(math.sqrt(i))
        x = 540 + (i - row * row - row) * 70 + r.uniform(-12, 12)
        y = 1660 - (8 - row) * 0 - (7 - row) * 0 - (n ** 0.5 - row) * 50 + 40
        snail(c, x, min(1690, 1450 + row * 55), 0.42, t + i, face=False)
    count = int(10000 * ease(min(1, (t - ten + 0.2) / 1.6))) if t > ten - 0.2 else 0
    if count:
        f = skia.Font(FB, 96)
        s = f"{count:,} snails"
        w = f.measureText(s)
        c.drawString(s, 540 - w / 2 + 4, 1060 + 6, f, P(C(0, 0, 0, 140)))
        c.drawString(s, 540 - w / 2, 1060, f, P(C(255, 230, 200)))
    gm = CUE["gram"]
    k = pop_in(t, gm - 0.05)
    if k > 0:  # one tiny vial
        c.save()
        c.translate(540, 1240)
        c.scale(k, k)
        blob(c, rrect(-22, -70, 22, 20, 10), (230, 240, 250), 1.05, 0.85)
        c.drawRect(skia.Rect(-18, -20, 18, 16), P(C(*PURP)))
        glow(c, 0, -10, 120, (200, 120, 255), 130)
        c.restore()
        c.drawString("= 1 gram", 610, 1255, skia.Font(FB, 64), P(C(*LILAC)))
    rot = CUE["rotting"]
    if t > rot - 0.6:
        for k2 in range(4):
            stink(c, 220 + k2 * 220, 1450, t, k2)
        stand(c, DYER, 180, 1900, 1.0, t, eyes="squint", mouth="disgust", brows="angry", look=(1, 0), hands=[(70, -60), (-30, 150)])


def art_kings(c, t):
    bg_dark(c, (35, 10, 40), (80, 20, 60))
    for x in (120, 960):  # marble columns
        c.drawRect(skia.Rect(x - 55, 900, x + 55, 1700), P(Shader=lin((x - 55, 0), (x + 55, 0), [C(170, 160, 170), C(245, 240, 245), C(150, 140, 150)])))
    for k in range(5):  # purple drapes
        c.drawLine(230 + k * 150, 880, 260 + k * 150, 1500, S(C(*PURP, 140), 50))
    c.drawRect(skia.Rect(0, 1700, W, H), P(Shader=lin((0, 1700), (0, H), [C(120, 40, 60), C(50, 15, 30)])))
    blob(c, rrect(330, 1300, 750, 1720, 30), (230, 180, 60), 1.4, 0.7)  # throne
    blob(c, rrect(380, 1450, 700, 1600, 20), (*PURP,), 1.3, 0.7)
    kg = CUE["kings"]
    wave = math.sin(t * 5)
    stand(c, EMPEROR, 540, 1700, 1.25, t, eyes="open", mouth="grin" if t > kg else "smile", brows="smug", look=(0, -0.2),
          hands=[(-120, 60), (120 + 20 * wave, -60 - 25 * wave)])
    for side in (-1, 1):  # servants bring purple silk to the throne
        sx, walk = walk_in(t, 540 + side * 760, 540 + side * 330, 2.6)
        sv = dict(crowd_look(2 if side < 0 else 4), dress=None, coat=(230, 220, 200))
        stand(c, sv, sx, 1900, 0.9, t, walk=walk, eyes="open", mouth="smile", brows="flat", look=(-side, 0), hands=[(-side * 30 - 40, 40), (-side * 30 + 40, 40)])
        c.save()
        c.translate(sx, 1900 - 0.9 * 200)
        silk(c, 120, 70, t)
        c.restore()
    if t > kg:
        for j in range(8):
            a = t * 1.3 + j * 0.78
            sparkle(c, 540 + math.cos(a) * 380, 1300 + math.sin(a) * 260, 10, 210, (230, 190, 255))
    gd = CUE["gold3"]
    if t > gd - 0.4:  # mini scale: silk outweighs gold
        tip = ease((t - gd + 0.2) / 0.5)
        scale_balance(c, 540, 1100, 0.45, t, tip, lambda cc: silk(cc, 170, 110, t), gold_bars)


def art_banned(c, t):
    bg_dark(c, (30, 25, 45), (70, 50, 80))
    c.drawRect(skia.Rect(0, 1600, W, H), P(Shader=lin((0, 1600), (0, H), [C(160, 140, 120), C(100, 85, 70)])))
    for k in range(6):  # crowd silhouette
        blob(c, oval(100 + k * 180, 1560, 80, 120), (50, 40, 60), 1.0, 1.0, outline=False)
    bn = CUE["banned"]
    stand(c, EMPEROR, 250, 1900, 1.15, t, eyes="squint" if t > bn else "open", mouth="frown" if t > bn else "smile", brows="angry", look=(1, 0),
          hands=[(-20, 150), (170, -40) if t > bn else (60, 60)])
    caught = t > bn + 0.3
    stand(c, COMMONER, 640, 1900, 1.15, t, eyes="wide" if caught else "open", mouth="O" if caught else "smile", brows="up", look=(1, 0),
          hands=[(-60, -150), (60, -150)] if caught else [(-30, 150), (30, 150)], tilt=6 * math.sin(t * 9) if caught else 0)
    gx, walk = walk_in(t, 1250, 960, 1.4)
    stand(c, GUARD, gx, 1900, 1.1, t, walk=walk, eyes="squint", mouth="frown", brows="angry", look=(-1, 0), hands=[(-140, 20), (30, 150)])
    c.drawLine(gx + 60, 1900 - 1.1 * 420, gx + 60, 1900 - 1.1 * 120, S(C(120, 90, 60), 10))  # spear
    tip = skia.Path()
    tip.moveTo(gx + 60, 1900 - 1.1 * 470)
    tip.lineTo(gx + 44, 1900 - 1.1 * 420)
    tip.lineTo(gx + 76, 1900 - 1.1 * 420)
    tip.close()
    c.drawPath(tip, P(C(200, 200, 210)))


def lab_bg(c, t):
    bg_dark(c, (25, 25, 35), (60, 55, 70))
    for row in range(3):
        y = 980 + row * 170
        c.drawRect(skia.Rect(0, y, W, y + 14), P(C(100, 75, 50)))
        for k in range(8):
            x = 40 + k * 130 + (row % 2) * 40
            col = [(120, 170, 200), (180, 120, 90), (140, 190, 140), (200, 180, 110)][(k + row) % 4]
            blob(c, rrect(x, y - 100, x + 60, y, 14), col, 1.4, 0.7)
    glow(c, 540, 1000, 450, (255, 200, 130), int(110 * flicker(t, 3)))
    blob(c, rrect(0, 1560, W, 1640, 10), (130, 95, 65))
    c.drawRect(skia.Rect(0, 1640, W, H), P(C(80, 58, 40)))


def art_perkin(c, t):
    lab_bg(c, t)
    x, walk = walk_in(t, 1250, 760, 1.8)
    ml = CUE["malaria"]
    stir = math.sin(t * 6) if walk is None else 0
    stand(c, PERKIN, x, 1900, 1.3, t, walk=walk, eyes="open", mouth="grin", brows="up", look=(-1, 0.4),
          hands=[(-150 + 18 * stir, 60), (30, 150)])
    flask(c, 380, 1560, 1.0, (210, 200, 120), t)
    if walk is None:  # glass rod stirring + steam
        c.drawLine(380 + 30 * stir, 1340, 380 - 10 * stir, 1520, S(C(220, 240, 255, 220), 8))
        for j in range(3):
            ph = (t * 0.6 + j / 3) % 1
            c.drawCircle(380 + 20 * math.sin(t + j), 1330 - ph * 200, 18 + 26 * ph, P(C(240, 240, 220, int(110 * (1 - ph))), MaskFilter=blur(10)))
    if t > 1.5:  # mosquito buzzing around the "malaria" medicine
        mx, my = 380 + math.cos(t * 4) * 150, 1180 + math.sin(t * 6) * 60
        wing = 12 + 8 * math.sin(t * 60)
        c.drawOval(skia.Rect(mx - wing - 8, my - 14, mx, my + 2), P(C(230, 240, 250, 170)))
        c.drawOval(skia.Rect(mx, my - 14, mx + wing + 8, my + 2), P(C(230, 240, 250, 170)))
        c.drawLine(mx - 10, my, mx + 22, my + 6, S(C(40, 40, 40), 6))
        c.drawLine(mx + 22, my + 6, mx + 40, my + 14, S(C(40, 40, 40), 2))


def art_failed(c, t):
    lab_bg(c, t)
    fl = CUE["failed"]
    blk = ease((t - fl + 0.4) / 0.5)
    col = tuple(int(210 * (1 - blk) + 25 * blk) for _ in range(1)) + (int(200 * (1 - blk) + 20 * blk), int(120 * (1 - blk) + 20 * blk))
    flask(c, 540, 1560, 1.3, col, t)
    if blk > 0.3:  # black goo bubbling over the rim
        for j in range(3):
            ph = (t * 0.8 + j / 3) % 1
            c.drawCircle(540 + (j - 1) * 18, 1300 - 40 * ph, 18 + 10 * ph, P(C(20, 18, 22, int(240 * (1 - ph * 0.5)))))
        for j in range(4):  # smoke
            ph = (t * 0.5 + j / 4) % 1
            c.drawCircle(540 + 30 * math.sin(t + j), 1260 - ph * 300, 30 + 50 * ph, P(C(60, 60, 65, int(150 * (1 - ph))), MaskFilter=blur(14)))
    stand(c, PERKIN, 880, 1900, 1.2, t, eyes="squint" if blk > 0.5 else "open", mouth="frown" if blk > 0.5 else "O", brows="sad" if blk > 0.5 else "up",
          look=(-1, 0.4), hands=[(-30, 150), (30, 150)])


def art_purple(c, t):
    lab_bg(c, t)
    cl, pu = CUE["cleaned"], CUE["purple7"]
    turn = ease((t - pu + 0.2) / 0.35)
    col = tuple(int(25 + (PURP[j] + 60 - 25) * turn) if j != 1 else int(20 + (PURP[1] + 30 - 20) * turn) for j in range(3))
    flask(c, 540, 1560, 1.3, (min(255, col[0]), min(255, col[1]), min(255, col[2])), t)
    pour = ease((t - cl + 0.2) / 0.5) * (1 - ease((t - pu) / 0.4))
    if pour > 0:  # alcohol bottle tipping in
        c.save()
        c.translate(700, 1150)
        c.rotate(-70 * pour)
        blob(c, rrect(-40, -160, 40, 40, 14), (180, 220, 240), 1.1, 0.8)
        c.drawRect(skia.Rect(-30, -90, 30, -40), P(C(245, 240, 225)))
        c.restore()
        c.drawLine(640, 1210, 560, 1330, S(C(200, 230, 255, int(200 * pour)), 8))
    if t > pu:
        burst_col(c, 540, 1440, (t - pu) / 0.9, (220, 140, 255), 20, 520)
        glow(c, 540, 1440, 420, (200, 110, 255), int(170 * min(1, (t - pu) / 0.3)))
    stand(c, PERKIN, 880, 1900, 1.2, t, eyes="wide" if t > pu else "squint", mouth="laugh" if t > pu else "frown",
          brows="up", look=(-1, 0.3), hands=[(-90, -170), (90, -170)] if t > pu else [(-30, 150), (30, 150)])


def art_factory(c, t):
    U.T_EIGHT = CUE["rich"] - 0.6
    bg_dark(c, (30, 25, 50), (120, 80, 110))
    for k, (x, w, h) in enumerate(((120, 220, 520), (420, 280, 640), (760, 260, 560))):
        blob(c, rrect(x - w / 2, 1650 - h, x + w / 2, 1650, 6), (120, 70, 70), 1.15, 0.8)
        for r_ in range(3):
            for j in range(2):
                c.drawRect(skia.Rect(x - w / 2 + 30 + j * (w / 2), 1650 - h + 60 + r_ * 140, x - w / 2 + 90 + j * (w / 2), 1650 - h + 130 + r_ * 140),
                           P(C(255, 200, 120, 200)))
    for cx in (380, 520):  # chimneys puffing purple smoke
        c.drawRect(skia.Rect(cx - 24, 820, cx + 24, 1010), P(C(90, 50, 50)))
        for j in range(5):
            ph = (t * 0.5 + j / 5) % 1
            c.drawCircle(cx + 40 * ph + 10 * math.sin(t + j), 800 - ph * 260, 30 + 50 * ph, P(C(200, 120, 240, int(170 * (1 - ph))), MaskFilter=blur(12)))
    c.drawRect(skia.Rect(0, 1650, W, H), P(C(70, 60, 70)))
    for k in range(3):  # barrels of purple dye rolling out of the factory
        bx = -140 + ((t * 220 + k * 400) % 1360)
        c.save()
        c.translate(bx, 1700)
        c.rotate(math.degrees(t * 220 / 70))
        blob(c, oval(0, 0, 70, 70), (*PURP,), 1.4, 0.65)
        c.drawLine(-70, 0, 70, 0, S(C(220, 180, 70), 8))
        c.drawLine(0, -70, 0, 70, S(C(220, 180, 70), 8))
        c.restore()
    for x, y, r, face, speed in U.coins_at(t):  # coins behind him
        U.draw_coin(c, x, y, r, face, speed)
    rich = t > CUE["rich"]
    stand(c, PERKIN, 540, 1900, 1.25, t, eyes="closed" if rich else "open", mouth="laugh" if rich else "grin", brows="up", look=(0, -0.3),
          hands=[(-90, -180), (90, -180)] if rich else [(-30, 150), (30, 150)])


def art_victoria(c, t):
    bg_dark(c, (40, 20, 60), (120, 70, 140))
    for k in range(10):
        c.drawLine(k * 120, 880, k * 120 + 60, 1600, S(C(255, 220, 255, 14), 30))
    c.drawRect(skia.Rect(0, 1650, W, H), P(Shader=lin((0, 1650), (0, H), [C(130, 90, 120), C(70, 40, 70)])))
    vk = CUE["victoria"]
    k = pop_in(t, vk - 0.15)
    if k > 0:
        c.save()
        c.translate(540, 1720)
        c.scale(k, k)
        stand(c, VICTORIA, 0, 0, 1.25, t, eyes="open", mouth="smile", brows="smug", look=(0, -0.2), hands=[(-40, 80), (40, 80)])
        c.restore()
        glow(c, 540, 1500, 300, (230, 170, 255), 40)
    ev = CUE["everyone"]
    for i, (x, lk) in enumerate([(120, 0), (300, 1), (780, 3), (960, 2)]):
        on = t > ev + i * 0.1
        look = dict(crowd_look(lk), coat=PURP if on else crowd_look(lk)["coat"])
        if look.get("dress"):
            look["dress"] = PURP if on else look["dress"]
        bounce = abs(math.sin(t * 6 + i)) * 12 if on else 0
        stand(c, look, x, 1900 - bounce, 0.85, t, eyes="closed" if on else "open", mouth="laugh" if on else "smile", brows="up", look=(0, 0),
              hands=[(-60, -170), (60, -170)] if on else [(-30, 150), (30, 150)])
        if on and t < ev + i * 0.1 + 0.5:
            burst_col(c, x, 1600, (t - ev - i * 0.1) / 0.5, (220, 150, 255), 10, 160)


def art_today(c, t):
    bg_dark(c, (30, 15, 45), (70, 30, 95))
    for k in range(14):
        a = k / 14 * 2 * math.pi + t * 0.35
        p = skia.Path()
        p.moveTo(540, 1350)
        p.lineTo(540 + math.cos(a) * 1500, 1350 + math.sin(a) * 1500)
        p.lineTo(540 + math.cos(a + 0.13) * 1500, 1350 + math.sin(a + 0.13) * 1500)
        p.close()
        c.drawPath(p, P(C(230, 170, 255, 16)))
    c.drawRect(skia.Rect(0, 1700, W, H), P(C(50, 20, 60)))
    sn = CUE["snail10"]
    snx = 1250 - 450 * ease(min(1, t / max(0.5, sn)))
    stand(c, KIDP, 420, 1880, 1.45, t, eyes="wide" if t > sn else "open", mouth="grin", brows="up", look=(1, 0.5),
          hands=[(-30, 150), (150, 40)])
    snail(c, snx, 1700, 0.9 * (1 + 0.15 * spring(t, sn, 3, 4)), t)
    if t > sn:
        glow(c, snx, 1640, 200, (200, 120, 255), 70)
    md = CUE["medicine"]
    if t > md - 0.2:
        flask(c, 820, 1420, 0.7 * pop_in(t, md - 0.2), (190, 90, 240), t)


def art_cta(c, t):
    U.T_EIGHT = -10
    U.background(c, t, 0)
    U.spotlight(c, t, 0)
    c.drawPaint(P(C(10, 6, 14, 120)))
    draw_cta2(c, t, CUE["like"], CUE["sub"])


ART = [art_hook, art_tyre, art_snails, art_kings, art_banned, art_perkin, art_failed, art_purple, art_factory, art_victoria, art_today, art_cta]
PUSH = [(1.0, 1.06), (1.0, 1.06), (1.0, 1.06), (1.0, 1.06), (1.0, 1.06), (1.0, 1.06), (1.0, 1.08), (1.0, 1.07), (1.0, 1.06), (1.0, 1.06), (1.0, 1.06), (1.0, 1.0)]
ANCHOR = [(540, 1400), (540, 1500), (540, 1400), (540, 1400), (540, 1500), (540, 1500), (540, 1450), (540, 1450), (540, 1500), (540, 1500), (540, 1500), (540, 1080)]


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
    if i != 11:  # the CTA stays razor-sharp (no bloom/grain over it)
        snap = surf.makeImageSnapshot()
        c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=U.BLOOM, ImageFilter=skia.ImageFilters.Blur(24, 24), BlendMode=skia.BlendMode.kPlus, Alphaf=0.35))
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
    line(img, "Purple was once worth", 230, F_MID)
    line(img, "more than", 330, F_MID)
    slam(img, "GOLD!", 430, t, CUE["gold"] - 0.1, GOLD, 180)
    text_block(img, "...made from SNAIL SLIME!", font(FONT_B, 62), 680, t, LILAC, CUE["snail"])
    impact(img, t, CUE["gold"] + 0.1, 18)


def tx_tyre(img, t):
    tag(img, "TYRE, 3,000 YEARS AGO", t, (120, 60, 160))
    title(img, t, "Dyers cracked open sea snails", "...for one tiny drop of purple", CUE["drop"], sub_color=LILAC)


def tx_snails(img, t):
    title(img, t, "10,000 snails = 1 gram of dye")
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 640, "IT STANK!", t, CUE["rotting"], col=GREEN, size=110)
    impact(img, t, CUE["rotting"] + 0.15, 12)


def tx_kings(img, t):
    tag(img, "ROME", t, (160, 50, 60))
    title(img, t, "The color of KINGS", "Worth more than its weight in gold", CUE["gold3"], sub_color=GOLD)


def tx_banned(img, t):
    title(img, t, "Only the emperor could wear it")
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 640, "BANNED", t, CUE["banned"], col=RED, size=120)
    impact(img, t, CUE["banned"] + 0.15, 14)


def tx_perkin(img, t):
    tag(img, "LONDON, 1856", t, (60, 90, 150))
    title(img, t, "William Perkin, age 18", "...tried to make a malaria medicine", CUE["malaria"])


def tx_failed(img, t):
    title(img, t, "His experiment...")
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 640, "FAILED", t, CUE["failed"], col=RED, size=120)
    impact(img, t, CUE["failed"] + 0.15, 14)


def tx_purple(img, t):
    title(img, t, "He cleaned it with alcohol...", y=260)
    slam(img, "PURPLE!", 420, t, CUE["purple7"] - 0.1, PURPLE, 180)
    impact(img, t, CUE["purple7"] + 0.1, 18)


def tx_factory(img, t):
    title(img, t, "The first artificial dye!", "He quit school and opened a factory", CUE["factory"])
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "RICH!", t, CUE["rich"], col=GOLD, size=120)
    impact(img, t, CUE["rich"] + 0.15, 12)


def tx_victoria(img, t):
    title(img, t, "Even Queen Victoria wore it", "...and purple was for EVERYONE", CUE["everyone"], sub_color=LILAC)


def tx_today(img, t):
    title(img, t, "Own something purple?", "It started with snail slime...", CUE["snail10"], sub_color=LILAC)
    text_block(img, "...and a failed medicine!", font(FONT_B, 56), 620, t, GOLD, CUE["medicine"])


def tx_cta(img, t):
    pass  # the whole end card is drawn sharp in Skia (cta2)


TEXT = [tx_hook, tx_tyre, tx_snails, tx_kings, tx_banned, tx_perkin, tx_failed, tx_purple, tx_factory, tx_victoria, tx_today, tx_cta]
base.TRANSITION = splat

if __name__ == "__main__":
    voice = f"{VOICE_DIR}/voice.mp3"
    tl = Timeline(voice)
    firsts = ["three thousand", "it took", "so purple", "some members|emperors", "then", "is|his experiment", "we|but cling|when", "he had",
              "even queen", "so if", "learn"]
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
               gold=f("gold", 0, 0.0), snail=f("snail", 0),
               cracked=f("cracked", 1), drop=f("drop", 1),
               ten=f("ten", 2), gram=f("gram", 2), rotting=f("rotting", 2, 0.15),
               kings=f("kings", 3), gold3=f("gold", 3),
               banned=f("banned", 4, 0.15),
               malaria=f("malaria", 5),
               failed=f("failed", 6, 0.15),
               cleaned=f("cling|clean", 7), purple7=f("bright", 7, 0.0),
               factory=f("factory", 8), rich=f("rich", 8, 0.15),
               victoria=f("victoria", 9), everyone=f("everyone", 9),
               snail10=f("snail", 10), medicine=f("medicine", 10))
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
                img.convert("RGB").save(f"{out}/purple_{i}_{tt}.png")
        sys.exit()
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), scene(i, TEXT[i])) for i, dd in enumerate(durs)]
    if ONLY:
        base.SCENES[:] = [s for i, s in enumerate(base.SCENES) if i in ONLY]
    ST, C_ = S0, CUE
    ev = [("whoosh", s) for s in ST[1:]]
    ev += [("thud", C_["gold"]), ("ding", C_["gold"] + 0.05), ("pop", C_["snail"]),
           ("thud", ST[1] + C_["cracked"]), ("ding", ST[1] + C_["drop"] + 0.6),
           ("ding", ST[2] + C_["gram"]), ("thud", ST[2] + C_["rotting"] + 0.15),
           ("ding", ST[3] + C_["kings"]),
           ("thud", ST[4] + C_["banned"] + 0.15),
           ("pop", ST[5] + C_["malaria"]),
           ("thud", ST[6] + C_["failed"] + 0.15),
           ("thud", ST[7] + C_["purple7"]), ("ding", ST[7] + C_["purple7"] + 0.05),
           ("thud", ST[8] + C_["rich"] + 0.15),
           ("ding", ST[9] + C_["victoria"]), ("pop", ST[9] + C_["everyone"]),
           ("pop", ST[10] + C_["snail10"]), ("pop", ST[10] + C_["medicine"]),
           ("click", ST[11] + C_["like"]), ("ding", ST[11] + C_["like"] + 0.03),
           ("click", ST[11] + C_["sub"]), ("ding", ST[11] + C_["sub"] + 0.35)]
    ev += [("pop", ST[2] + C_["ten"] - 0.4 + k * 0.08) for k in range(12)]  # snails piling up
    ev += [("click", ST[8] + C_["rich"] - 0.6 + 0.35 + i * 0.09 + (i % 3) * 0.03) for i in range(10)]  # coins
    ev = [(k, round(v, 3)) for k, v in ev if 0 <= v < total]
    audio.music("music.wav", total, bpm=100, seed=31)
    audio.sfx("sfx.wav", total, ev)
    base.OUT = "base_purple.mp4"
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_purple.mp4", voice, "music.wav", "sfx.wav", OUTFILE)
    print("wrote", OUTFILE)
