"""YouTube Short #23: "Coca-Cola Was Invented as MEDICINE?!" (Skia toon, unedited vidIQ "Chris" voice).

Topic picked from vidIQ outliers: "products invented for a different purpose" (41x breakout) and "who invented
famous drinks" (25x). Facts: John Pemberton, Atlanta pharmacist, wounded in the Civil War and addicted to
morphine; 1886 syrup from coca leaves + kola nuts (hence the name); sold as a "brain tonic" that claimed to cure
headaches, tiredness and morphine addiction; 5 cents a glass at a drugstore soda fountain, ~9 glasses a day the
first year; he sold his rights and died nearly broke in 1888; Asa Candler bought the formula for ~$2,300; the
cocaine was removed in the early 1900s; today the company sells over 2 billion drinks a day.
No brand logo or trademark bottle shape is drawn: plain apothecary bottles and glasses only.

Usage: python make_cola.py final.mp4 [scene,...] [t1,...]   stills: STILLS_DIR=dir python make_cola.py x 0,1 1.0
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
sys.argv = [sys.argv[0], "base_cola.mp4"]
sys.path.insert(0, "..")

import audio  # noqa: E402
import make_ketchup  # noqa: E402
import make_salt  # noqa: E402
import make_short as base  # noqa: E402
import ultimate as U  # noqa: E402
from fx import impact  # noqa: E402
from make_honey import slam  # noqa: E402
from make_ketchup import splat, stamp  # noqa: E402
from make_short import FONT_B, F_MID, H, W, font, tag, text_block  # noqa: E402
from style import heading  # noqa: E402
from timing import Timeline  # noqa: E402
from toon import *  # noqa: E402,F401,F403

GOLD, RED, GREEN, FIZZ = (255, 200, 60), (235, 60, 60), (130, 220, 120), (255, 190, 140)
make_ketchup.SPLAT_COLOR = (250, 195, 50)
base.HOOK_SKIP = 0.0
base.CRF = 16
CUE = {}
VOICE_DIR = "../cola"
TAIL = 1.45

PEMBERTON = dict(skin=(240, 200, 170), hair="neat", hair_col=(70, 50, 40), sideburns=True, coat=(55, 55, 68), vest=(120, 35, 45),
                 pants=(60, 60, 70), collar=(245, 245, 240), mustache=True, nose="long")
PEMBERTON_OLD = dict(PEMBERTON, hair_col=(175, 175, 180), coat=(70, 70, 80), vest=(90, 60, 60))
CANDLER = dict(skin=(240, 200, 170), hair="neat", hair_col=(140, 130, 120), coat=(85, 85, 95), vest=(40, 40, 45), pants=(60, 60, 65),
               glasses=True, mustache=True, hat="bowler", collar=(245, 245, 240), nose="long")
CLERK = dict(SHOP)


def blinking(t, ph=0.0):
    return ((t + ph) % 3.3) < 0.11


def pop_in(t, at, dur=0.35):
    return out_back((t - at) / dur, 2.2) if t > at else 0.0


def head_top(y, s):
    return y + s * (-262 - 70 - 88)


def head_c(y, s):
    return y - 332 * s


# ---------- props ----------

def bottle(c, x, y, s, t, label="BRAIN TONIC", fill=0.8, cork=True, glow_a=0):
    """Plain apothecary bottle (bottom at y) with brown syrup and a paper label. No brand shape."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    if glow_a:
        glow(c, 0, -170, 260, (255, 170, 90), glow_a)
    body = skia.Path()
    body.moveTo(-85, -10)
    body.lineTo(-85, -230)
    body.cubicTo(-85, -280, -40, -290, -32, -320)
    body.lineTo(-32, -380)
    body.lineTo(32, -380)
    body.lineTo(32, -320)
    body.cubicTo(40, -290, 85, -280, 85, -230)
    body.lineTo(85, -10)
    body.cubicTo(85, 4, -85, 4, -85, -10)
    body.close()
    c.drawPath(body, P(C(210, 235, 245, 70)))
    c.save()
    c.clipPath(body, doAntiAlias=True)
    top = -10 - 300 * fill
    c.drawRect(skia.Rect(-100, top + 6 * math.sin(t * 3), 100, 10), P(Shader=lin((0, top), (0, 0), [C(140, 60, 25, 235), C(70, 25, 10, 245)])))
    for k in range(10):  # fizz bubbles
        u = (t * 0.7 + k / 10) % 1
        c.drawCircle(-60 + (k * 37) % 120, -20 - u * (-top - 30), 5, S(C(255, 220, 180, int(200 * (1 - u))), 2))
    c.restore()
    c.drawPath(body, S(C(230, 245, 255, 220), 6))
    c.drawLine(-62, -220, -62, -40, S(C(255, 255, 255, 110), 12))
    if label:
        blob(c, rrect(-72, -200, 72, -95, 10), (245, 235, 205), 1.05, 0.85)
        size = 30
        f = skia.Font(FB, size)
        while f.measureText(label) > 126 and size > 10:  # always fits inside the label
            size -= 1
            f = skia.Font(FB, size)
        w = f.measureText(label)
        c.drawString(label, -w / 2, -140, f, P(C(150, 40, 40)))
        c.drawLine(-55, -122, 55, -122, S(C(150, 40, 40), 3))
        c.drawString("5¢", -14, -100, skia.Font(FB, 20), P(C(90, 60, 40)))
    if cork:
        blob(c, rrect(-28, -410, 28, -372, 8), (170, 120, 70), 1.3, 0.7)
    c.restore()


def leaf(c, x, y, s, rot, col=(70, 150, 70)):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    p = skia.Path()
    p.moveTo(0, -60)
    p.cubicTo(36, -30, 36, 30, 0, 60)
    p.cubicTo(-36, 30, -36, -30, 0, -60)
    p.close()
    blob(c, p, col, 1.3, 0.65)
    c.drawLine(0, -55, 0, 55, S(C(40, 100, 45), 3))
    c.restore()


def nut(c, x, y, s, rot=0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    blob(c, oval(0, 0, 34, 26), (150, 80, 50), 1.35, 0.6)
    c.drawArc(skia.Rect(-20, -16, 20, 16), 200, 140, False, S(C(100, 50, 30), 3))
    c.restore()


def soda_glass(c, x, y, s, t, fill=0.75):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = skia.Path()
    body.moveTo(-60, -230)
    body.lineTo(60, -230)
    body.lineTo(40, 0)
    body.lineTo(-40, 0)
    body.close()
    c.drawPath(body, P(C(220, 240, 255, 60)))
    if fill > 0:
        c.save()
        c.clipPath(body, doAntiAlias=True)
        top = -230 * fill
        c.drawRect(skia.Rect(-70, top, 70, 5), P(Shader=lin((0, top), (0, 0), [C(150, 70, 30, 235), C(80, 30, 12, 245)])))
        c.drawRect(skia.Rect(-70, top - 14, 70, top + 4), P(C(240, 210, 180, 220)))  # foam
        for k in range(8):
            u = (t * 0.8 + k / 8) % 1
            c.drawCircle(-30 + (k * 23) % 60, -10 - u * (-top - 20), 3.5, S(C(255, 225, 190, int(200 * (1 - u))), 1.5))
        c.restore()
    c.drawPath(body, S(C(230, 245, 255, 220), 4))
    c.restore()


def coin(c, x, y, r, face=1.0):
    w = max(4, r * abs(face))
    c.drawOval(skia.Rect(x - w, y - r, x + w, y + r), P(Shader=lin((x - w, y - r), (x + w, y + r), [C(255, 240, 160), C(240, 180, 40), C(170, 110, 20)])))
    c.drawOval(skia.Rect(x - w, y - r, x + w, y + r), S(C(140, 85, 15), 3))


def rain(c, t, n=110, seed=4, col=(170, 190, 230)):
    r = random.Random(seed)
    for i in range(n):
        x0, y0, sp = r.uniform(-200, W), r.uniform(0, H), r.uniform(1500, 2300)
        y = (y0 + t * sp) % (H + 200) - 100
        x = x0 + (y / H) * 160
        c.drawLine(x, y, x + 10, y + 46, S(C(*col, 120), 2.5))


def shelves(c, t, y0=960, rows=3, cols_=8):
    for row in range(rows):
        y = y0 + row * 170
        c.drawRect(skia.Rect(0, y, W, y + 14), P(C(100, 65, 35)))
        for k in range(cols_):
            x = 40 + k * 130 + (row % 2) * 40
            col = [(120, 170, 90), (200, 120, 60), (150, 100, 160), (220, 190, 90), (110, 150, 200)][(k + row) % 5]
            blob(c, rrect(x, y - 110 + (k % 2) * 20, x + 70, y, 14), col, 1.4, 0.7)
            c.drawRect(skia.Rect(x + 10, y - 70 + (k % 2) * 20, x + 60, y - 40 + (k % 2) * 20), P(C(245, 235, 210, 200)))


def pharmacy_bg(c, t, lamp_x=880):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(30, 22, 20), C(75, 50, 35), C(30, 20, 15)])))
    shelves(c, t)
    glow(c, lamp_x, 1000, 460, (255, 190, 110), int(130 * flicker(t, 2)))
    c.drawRect(skia.Rect(0, 1660, W, H), P(Shader=lin((0, 1660), (0, H), [C(110, 75, 45), C(60, 40, 25)])))


# ---------- scenes ----------

def art_hook(c, t):
    pharmacy_bg(c, t)
    med, coc = CUE["medicine"], CUE["cocaine"]
    blob(c, rrect(0, 1560, W, 1660, 10), (120, 80, 45))  # counter
    c.drawRect(skia.Rect(0, 1660, W, H), P(C(80, 52, 30)))
    pose = dict(hands=[(-20, 150), (90, 30)], eyes="open", brows="smug", mouth="grin" if t > med else "smile", look=(-1, 0.2),
                tilt=2 * math.sin(t * 1.7), blink=blinking(t, 0.5))
    person(c, 880, 1600, 1.25, PEMBERTON, pose, t)  # behind the counter
    blob(c, rrect(560, 1560, W, 1660, 10), (120, 80, 45))
    pop = spring(t, med, 2.8, 4) if t > med else 0
    s = 1.25 * (1 + 0.06 * pop)
    bottle(c, 400, 1580, s, t, "BRAIN TONIC", glow_a=int(90 + 60 * max(0, 1 - (t - med) / 0.8)) if t > med else 60)
    if t > med:  # the cork pops on "medicine"
        k = t - med
        cy = 1580 - 410 * s - 900 * k + 1500 * k * k
        if cy < 1700:
            c.save()
            c.translate(400 + 260 * k, cy)
            c.rotate(720 * k)
            blob(c, rrect(-35, -24, 35, 24, 8), (170, 120, 70), 1.3, 0.7)
            c.restore()
        for j in range(12):  # fizz spray
            u = min(1, k / 0.8)
            a = math.radians(-90 + (j - 6) * 9)
            c.drawCircle(400 + math.cos(a) * 300 * u, 1580 - 480 * s + math.sin(a) * 360 * u + 300 * u * u, 9 * (1 - u) + 3,
                         P(C(255, 220, 180, int(220 * (1 - u)))))
    for j in range(7):  # coca leaves drift down into the bottle on "cocaine"
        at = coc + j * 0.12
        dt = t - at
        if 0 < dt < 1.6:
            u = min(1, dt / 1.1)
            lx = 400 + (j - 3) * 70 * (1 - u) + 20 * math.sin(dt * 6 + j)
            ly = 900 + (1580 - 380 * s - 900) * u
            if u < 1:
                leaf(c, lx, ly, 0.6, 40 * math.sin(dt * 5 + j))
    burst(c, t, med, 400, 1580 - 250 * s, n=12, reach=300)


def art_atlanta(c, t):
    pharmacy_bg(c, t, 200)
    pain, morph = CUE["pain"], CUE["morphine"]
    wince = ease((t - pain + 0.2) / 0.4)
    pose = dict(hands=[(70, 60), (-30, 150) if t < morph else (60, -40)], eyes="squint" if wince > 0.5 else "open",
                brows="sad" if wince > 0.5 else "flat", mouth="frown" if wince > 0.5 else "smile", look=(0, 0.3),
                tilt=-6 * wince + 2 * math.sin(t * 1.5), lean=-4 * wince, blink=blinking(t, 0.7) and wince < 0.5)
    x, y, s = 540, 1880, 1.55
    person(c, x, y, s, PEMBERTON, pose, t)
    if wince > 0:  # pain lines at his side
        for k in range(3):
            a = math.radians(-30 + k * 30)
            r0 = 120 + 20 * math.sin(t * 10 + k)
            cx, cy = x - 100 * s, y - 170 * s
            c.drawLine(cx - math.cos(a) * r0 * 0.4, cy + math.sin(a) * r0 * 0.4, cx - math.cos(a) * r0 * 0.75, cy + math.sin(a) * r0 * 0.75,
                       S(C(255, 230, 120, int(230 * wince)), 7))
        for n in range(3):  # sweat
            dt = (t + n * 0.7) % 2.1
            if dt < 0.6:
                side = 1 if n % 2 else -1
                c.drawCircle(x + side * (110 + 200 * dt), head_c(y, s) - 60 - 220 * dt + 800 * dt * dt, 10, P(C(190, 225, 255, 230)))
    vs = pop_in(t, morph)
    if vs > 0:  # a small vial in his raised hand
        hx, hy = hand_pos(x, y, s, pose, 1)
        c.save()
        c.translate(hx + 10, hy - 20)
        c.scale(vs, vs)
        blob(c, rrect(-24, -90, 24, 0, 8), (200, 230, 240), 1.1, 0.8)
        c.drawRect(skia.Rect(-20, -60, 20, -25), P(C(245, 240, 225)))
        c.drawString("MORPHINE", -19, -38, skia.Font(FB, 9), P(C(150, 40, 40)))
        blob(c, rrect(-14, -106, 14, -88, 4), (90, 60, 40))
        c.restore()


def art_mix(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(30, 18, 15), C(80, 45, 30), C(30, 18, 15)])))
    shelves(c, t, 980, 2)
    coc, kola, syr = CUE["coca2"], CUE["kola"], CUE["syrup"]
    glow(c, 540, 1800, 420, (255, 140, 60), int(150 * flicker(t, 1)))
    c.drawRect(skia.Rect(0, 1740, W, H), P(Shader=lin((0, 1740), (0, H), [C(90, 60, 40), C(50, 32, 20)])))
    for k in range(5):  # fire under the pot
        fx = 420 + k * 60
        h = 70 + 30 * math.sin(t * 9 + k * 1.7)
        p = skia.Path()
        p.moveTo(fx - 26, 1790)
        p.quadTo(fx, 1790 - h * 1.5, fx + 26, 1790)
        p.close()
        c.drawPath(p, P(Shader=lin((0, 1790 - h), (0, 1790), [C(255, 230, 120), C(255, 110, 40)])))
    stir = math.sin(t * 3)
    pose = dict(hands=[(150 + 20 * stir, 20), (120 + 20 * stir, 60)], eyes="open", brows="angry", mouth="grin", look=(1, 0.6),
                tilt=3 * stir, blink=blinking(t, 0.2))
    person(c, 230, 1880, 1.35, PEMBERTON, pose, t)
    hx, hy = hand_pos(230, 1880, 1.35, pose, 1)
    c.drawLine(hx, hy, 560 + 40 * stir, 1600, S(OUT, 20))
    c.drawLine(hx, hy, 560 + 40 * stir, 1600, S(C(170, 120, 70), 12))
    # copper pot
    pot = skia.Path()
    pot.moveTo(380, 1580)
    pot.lineTo(760, 1580)
    pot.cubicTo(760, 1720, 700, 1760, 570, 1760)
    pot.cubicTo(440, 1760, 380, 1720, 380, 1580)
    pot.close()
    blob(c, pot, (200, 110, 60), 1.4, 0.6)
    brown = ease((t - syr + 0.3) / 0.6)
    c.drawOval(skia.Rect(385, 1560, 755, 1600), P(C(int(120 - 40 * brown), int(150 - 100 * brown), int(90 - 70 * brown))))
    for k in range(6):
        ph = (t * 1.4 + k * 0.17) % 1
        c.drawCircle(420 + k * 60, 1575 - ph * 30, 10 + 8 * ph, S(C(240, 210, 170, int(255 * (1 - ph))), 3))
    for k in range(4):  # steam
        ph = (t * 0.4 + k * 0.25) % 1
        c.drawCircle(480 + k * 60 + 20 * math.sin(t + k), 1520 - ph * 380, 30 + 50 * ph, P(C(240, 230, 220, int(90 * math.sin(math.pi * ph))), MaskFilter=blur(16)))
    for j in range(6):  # coca leaves tumble in
        dt = t - (coc + j * 0.09)
        if 0 < dt < 0.6:
            u = dt / 0.6
            leaf(c, 470 + j * 40 + 60 * math.sin(j), 1000 + 560 * u * u, 0.7, 300 * u + j * 40)
    for j in range(6):  # kola nuts drop in
        dt = t - (kola + j * 0.09)
        if 0 < dt < 0.55:
            u = dt / 0.55
            nut(c, 640 - j * 35, 1000 + 570 * u * u, 0.9, 400 * u)
    if t > syr:
        for j in range(5):
            a = t * 1.5 + j * 1.25
            sparkle(c, 570 + math.cos(a) * 230, 1500 + math.sin(a) * 60, 8, 200)


def art_name(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(40, 12, 12), C(120, 30, 30), C(40, 10, 12)])))
    for k in range(14):  # rotating rays
        a = k / 14 * 2 * math.pi + t * 0.3
        p = skia.Path()
        p.moveTo(540, 1350)
        p.lineTo(540 + math.cos(a) * 1400, 1350 + math.sin(a) * 1400)
        p.lineTo(540 + math.cos(a + 0.16) * 1400, 1350 + math.sin(a + 0.16) * 1400)
        p.close()
        c.drawPath(p, P(C(255, 200, 150, 22)))
    coca, cola, name = CUE["coca3"], CUE["cola"], CUE["name"]
    merge = ease((t - name + 0.1) / 0.5)
    f = skia.Font(FB, 150)
    a = pop_in(t, coca - 0.1)
    if a > 0:  # COCA + leaf
        x = 300  # words stay apart; the hyphen joins them (sliding together made them overlap)
        c.save()
        c.translate(x, 1200)
        c.scale(a, a)
        for k in range(3):
            leaf(c, -60 + k * 60, 220, 1.4, -30 + k * 30)
        w = f.measureText("COCA")
        c.drawString("COCA", -w / 2 + 5, 6, f, P(C(0, 0, 0, 120)))
        c.drawString("COCA", -w / 2, 0, f, P(C(130, 230, 120)))
        c.restore()
    b = pop_in(t, cola - 0.1)
    if b > 0:  # COLA + nuts
        x = 780
        c.save()
        c.translate(x, 1200)
        c.scale(b, b)
        for k in range(3):
            nut(c, -60 + k * 60, 220 + (k % 2) * 20, 1.8, k * 30)
        w = f.measureText("COLA")
        c.drawString("COLA", -w / 2 + 5, 6, f, P(C(0, 0, 0, 120)))
        c.drawString("COLA", -w / 2, 0, f, P(C(240, 170, 110)))
        c.restore()
    if merge > 0.5:
        fh = skia.Font(FB, 150)
        c.drawString("-", 540 - fh.measureText("-") / 2, 1190, fh, P(C(255, 255, 255, int(255 * (merge - 0.5) * 2))))
    burst(c, t, name, 540, 1150, n=16, reach=420)


def icon_head(c, x, y, s, t):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    blob(c, oval(0, 0, 60, 66), (240, 200, 170), 1.15, 0.8)
    for k in range(3):  # throbbing headache bolts
        a = math.radians(-60 + k * 60)
        p = skia.Path()
        r0 = 70 + 6 * math.sin(t * 12 + k)
        bx, by = math.cos(a - math.pi / 2) * r0, math.sin(a - math.pi / 2) * r0
        p.moveTo(bx, by)
        p.lineTo(bx + 14, by - 22)
        p.lineTo(bx + 4, by - 22)
        p.lineTo(bx + 18, by - 46)
        c.drawPath(p, S(C(255, 220, 60), 6))
    c.drawLine(-25, -5, -10, 0, S(OUT, 5))
    c.drawLine(25, -5, 10, 0, S(OUT, 5))
    c.drawArc(skia.Rect(-18, 22, 18, 40), 200, 140, False, S(OUT, 5))
    c.restore()


def icon_tired(c, x, y, s, t):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    blob(c, oval(0, 0, 60, 66), (240, 200, 170), 1.15, 0.8)
    c.drawArc(skia.Rect(-32, -12, -8, 8), 0, 180, False, S(OUT, 5))
    c.drawArc(skia.Rect(8, -12, 32, 8), 0, 180, False, S(OUT, 5))
    c.drawOval(skia.Rect(-10, 22, 10, 38), P(C(110, 25, 35)))
    for k in range(3):
        u = (t * 0.8 + k / 3) % 1
        c.drawString("z", 50 + 30 * u + k * 6, -40 - 70 * u, skia.Font(FB, 30 + 14 * k), P(C(255, 255, 255, int(255 * (1 - u)))))
    c.restore()


def icon_vial(c, x, y, s, t):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    blob(c, rrect(-26, -60, 26, 50, 10), (200, 230, 240), 1.1, 0.8)
    blob(c, rrect(-16, -78, 16, -58, 4), (90, 60, 40))
    c.drawLine(-60, -70, 60, 70, S(C(230, 40, 40), 14))
    c.drawLine(60, -70, -60, 70, S(C(230, 40, 40), 14))
    c.restore()


def art_tonic(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(40, 25, 20), C(110, 70, 45), C(45, 28, 20)])))
    for k in range(9):  # wallpaper stripes
        c.drawRect(skia.Rect(k * 130, 880, k * 130 + 60, 1660), P(C(255, 230, 190, 20)))
    c.drawRect(skia.Rect(0, 1660, W, H), P(Shader=lin((0, 1660), (0, H), [C(110, 75, 45), C(60, 40, 25)])))
    brain, head, tired, addict = CUE["brain"], CUE["headaches"], CUE["tired"], CUE["addiction"]
    raise_ = ease((t - brain + 0.2) / 0.4)
    pose = dict(hands=[(-30, 150), (60 + 30 * raise_, 40 - 230 * raise_)], eyes="open", brows="up", mouth="grin", look=(1, -0.5),
                tilt=3 * math.sin(t * 2), blink=blinking(t, 0.4))
    x, y, s = 300, 1880, 1.4
    person(c, x, y, s, PEMBERTON, pose, t)
    hx, hy = hand_pos(x, y, s, pose, 1)
    bottle(c, hx + 10, hy + 60, 0.6, t, "BRAIN TONIC", glow_a=int(110 * raise_))
    if raise_ > 0.5:
        for j in range(5):
            a = t * 2 + j * 1.25
            sparkle(c, hx + 10 + math.cos(a) * 110, hy - 60 + math.sin(a) * 130, 8, 200)
    for at, fn, ix, iy in ((head, icon_head, 760, 1150), (tired, icon_tired, 860, 1450), (addict, icon_vial, 700, 1700)):
        k = pop_in(t, at - 0.05)
        if k > 0:
            c.drawCircle(ix, iy, 115 * k, P(C(255, 255, 255, 230)))
            c.drawCircle(ix, iy, 115 * k, S(OUT, 5))
            fn(c, ix, iy, 1.0 * k, t)
            if fn is not icon_vial:  # a green tick: "cured!"
                tk = ease((t - at - 0.4) / 0.3)
                if tk > 0:
                    p = skia.Path()
                    p.moveTo(ix + 60, iy + 60)
                    p.lineTo(ix + 60 + 25 * tk, iy + 60 + 25 * tk)
                    p.lineTo(ix + 60 + 25 * tk + 50 * max(0, tk - 0.3), iy + 85 - 70 * max(0, tk - 0.3))
                    c.drawPath(p, S(C(60, 200, 90), 12))


def art_fountain(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(30, 35, 40), C(70, 80, 85), C(30, 35, 38)])))
    for k in range(8):  # tiled wall
        for j in range(10):
            c.drawRect(skia.Rect(k * 140 + 4, 880 + j * 80 + 4, k * 140 + 136, 880 + j * 80 + 76), P(C(220, 230, 225, 40 if (k + j) % 2 else 25)))
    five, soda, nine = CUE["five"], CUE["soda"], CUE["nine"]
    cp = dict(hands=[(60, 40), (-30, 150)], eyes="open", mouth="smile", brows="flat", look=(1, 0.3), blink=blinking(t, 0.6), tilt=2 * math.sin(t))
    person(c, 260, 1660, 1.2, CLERK, cp, t)
    # soda tap + glass
    c.drawRect(skia.Rect(470, 1120, 500, 1330), P(C(200, 200, 210)))
    c.drawRect(skia.Rect(470, 1120, 640, 1150), P(C(200, 200, 210)))
    c.drawRect(skia.Rect(610, 1150, 640, 1210), P(C(180, 180, 190)))
    pour = (t % 3.0) < 1.6
    if pour:
        c.drawLine(625, 1210, 625, 1500, S(C(130, 60, 25, 220), 10))
    blob(c, rrect(0, 1500, W, 1620, 10), (235, 230, 225), 1.05, 0.85)  # marble counter
    c.drawRect(skia.Rect(0, 1620, W, H), P(Shader=lin((0, 1620), (0, H), [C(120, 40, 45), C(70, 20, 25)])))
    soda_glass(c, 625, 1510, 1.0, t, fill=0.3 + 0.5 * ((t % 3.0) / 3.0))
    pt = pop_in(t, five - 0.05)
    if pt > 0:  # the 5 cent price tag
        c.save()
        c.translate(800, 1300)
        c.rotate(8 * math.sin(t * 2))
        c.scale(pt, pt)
        c.drawLine(0, -130, 0, -60, S(C(80, 60, 40), 4))
        blob(c, rrect(-80, -60, 80, 60, 14), (255, 230, 140), 1.1, 0.8)
        f = skia.Font(FB, 72)
        w = f.measureText("5¢")
        c.drawString("5¢", -w / 2, 26, f, P(C(150, 40, 40)))
        c.restore()
    # one bored customer, then a tally of 9 glasses
    pose = dict(hands=[(-20, 150), (-40, 60)], eyes="squint" if t > nine else "open", brows="flat", mouth="frown" if t > nine else "smile",
                look=(-1, 0), tilt=-3 + 2 * math.sin(t * 1.3), blink=blinking(t, 1.2))
    person(c, 900, 1900, 1.0, crowd_look(2), pose, t)
    if t > nine - 0.3:
        for k in range(9):
            g = ease((t - nine + 0.3 - k * 0.07) / 0.2)
            if g > 0:
                soda_glass(c, 120 + k * 60, 1880, 0.35 * g, t, 0.7)


def art_broke(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(10, 14, 28), C(28, 36, 58), C(12, 14, 22)])))
    for k in range(4):
        c.drawRect(skia.Rect(k * 280 - 20, 1000 + (k % 2) * 80, k * 280 + 230, 1620), P(C(25, 30, 48)))
        c.drawRect(skia.Rect(k * 280 + 60, 1100 + (k % 2) * 80, k * 280 + 110, 1170 + (k % 2) * 80), P(C(255, 200, 110, 140)))
    c.drawRect(skia.Rect(0, 1620, W, H), P(Shader=lin((0, 1620), (0, H), [C(45, 45, 55), C(20, 20, 28)])))
    died, broke = CUE["died"], CUE["broke"]
    slump = ease(t / 1.2)
    pose = dict(hands=[(-40, 130), (40, 130)], eyes="sad", brows="sad", mouth="frown", look=(0, 0.8),
                tilt=-6 * slump + 1.5 * math.sin(t * 1.3), lean=2 * slump, blink=blinking(t, 0.4))
    x, y, s = 540, 1840, 1.55
    person(c, x, y, s, PEMBERTON_OLD, pose, t)
    for side in (-1, 1):  # empty pockets
        px, py = x + side * 70 * s, y - 120 * s
        p = skia.Path()
        p.moveTo(px - 26, py)
        p.lineTo(px + 26, py)
        p.lineTo(px + 18 * side, py + 48 + 6 * math.sin(t * 3 + side))
        p.close()
        blob(c, p, (235, 230, 220), 1.05, 0.8)
    if t > broke:  # a moth flutters out
        k = t - broke
        mx_, my_ = x + 70 * s + 140 * k + 20 * math.sin(k * 7), y - 120 * s - 220 * k + 30 * math.sin(k * 5)
        wing = 18 + 10 * math.sin(t * 40)
        c.drawOval(skia.Rect(mx_ - wing - 8, my_ - 16, mx_, my_ + 6), P(C(200, 190, 170, 230)))
        c.drawOval(skia.Rect(mx_, my_ - 16, mx_ + wing + 8, my_ + 6), P(C(200, 190, 170, 230)))
        c.drawCircle(mx_, my_, 6, P(C(90, 80, 70)))
    if t > died - 0.5:  # his last coin rolls away
        k = t - died + 0.5
        coin(c, x - 70 * s - 260 * k, 1830, 22, face=math.cos(k * 14))
    rain(c, t, 140, 4)


def art_candler(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(25, 30, 28), C(60, 75, 65), C(25, 30, 28)])))
    for k in range(6):  # wood panels
        c.drawRect(skia.Rect(k * 190 + 10, 900, k * 190 + 180, 1600), P(C(90, 60, 40, 120)))
    c.drawRect(skia.Rect(0, 1600, W, H), P(Shader=lin((0, 1600), (0, H), [C(100, 70, 45), C(55, 38, 25)])))
    glow(c, 540, 1050, 450, (255, 210, 140), int(110 * flicker(t, 4)))
    form, money = CUE["formula"], CUE["money"]
    grab = ease((t - form + 0.2) / 0.5)
    pose = dict(hands=[(-30, 150), (70 + 40 * grab, 60 - 120 * grab)], eyes="open", brows="smug", mouth="grin", look=(1, 0),
                tilt=2 * math.sin(t * 1.6), blink=blinking(t, 0.9))
    x, y, s = 330, 1880, 1.45
    person(c, x, y, s, CANDLER, pose, t)
    blob(c, rrect(520, 1500, 1080, 1580, 10), (130, 85, 50))  # desk
    c.drawRect(skia.Rect(560, 1580, 600, 1900), P(C(90, 55, 30)))
    c.drawRect(skia.Rect(1000, 1580, 1040, 1900), P(C(90, 55, 30)))
    hx, hy = hand_pos(x, y, s, pose, 1)
    if grab > 0:  # the formula scroll, rolled open in his hand
        c.save()
        c.translate(hx + 40, hy - 40)
        c.rotate(-8)
        sc = 0.6 + 0.4 * grab
        c.scale(sc, sc)
        blob(c, rrect(-90, -110, 90, 110, 6), (245, 235, 205), 1.05, 0.85)
        for k in range(7):
            c.drawLine(-65, -70 + k * 24, 65 - (k % 3) * 20, -70 + k * 24, S(C(120, 100, 80), 4))
        c.drawString("FORMULA", -60, -82, skia.Font(FB, 24), P(C(150, 40, 40)))
        c.restore()
    # stacks of cash slide across the desk on "two thousand..."
    for k in range(5):
        u = ease((t - money - k * 0.08) / 0.4)
        if u > 0:
            bx = 1100 - 300 * u - k * 50
            blob(c, rrect(bx - 55, 1460 - k * 6, bx + 55, 1500 - k * 6, 6), (110, 170, 100), 1.2, 0.7)
            c.drawCircle(bx, 1480 - k * 6, 12, P(C(220, 240, 200)))
    burst(c, t, money, 800, 1420, n=12, reach=260)


def art_removed(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(15, 25, 35), C(40, 60, 75), C(15, 22, 30)])))
    for k in range(4):  # lab bottles on a shelf
        blob(c, rrect(80 + k * 250, 1000, 160 + k * 250, 1130, 14), [(120, 170, 200), (180, 120, 90), (140, 190, 140), (200, 180, 110)][k], 1.4, 0.7)
    c.drawRect(skia.Rect(0, 1130, W, 1146), P(C(70, 80, 90)))
    c.drawRect(skia.Rect(0, 1700, W, H), P(Shader=lin((0, 1700), (0, H), [C(80, 90, 100), C(40, 45, 55)])))
    coc, taken = CUE["cocaine8"], CUE["quietly"]
    bottle(c, 540, 1720, 1.55, t, "TONIC", cork=False, glow_a=60)
    # tweezers pull the coca leaf up and out of the bottle; it fades into a red cross
    pull = ease((t - coc) / 1.0)
    lx, ly = 540, 1720 - 1.55 * 250 - 260 * pull  # stays below y~920, clear of the title and stamp
    leaf(c, lx, ly, 0.9, 20 * math.sin(t * 3))
    c.drawLine(lx - 8, ly - 30, lx - 26, ly - 150, S(C(200, 200, 210), 10))
    c.drawLine(lx + 8, ly - 30, lx + 26, ly - 150, S(C(200, 200, 210), 10))
    x_ = ease((t - taken - 0.1) / 0.3)
    if x_ > 0:
        c.drawLine(lx - 90 * x_, ly - 90 * x_, lx + 90 * x_, ly + 90 * x_, S(C(230, 40, 40), 18))
        c.drawLine(lx + 90 * x_, ly - 90 * x_, lx - 90 * x_, ly + 90 * x_, S(C(230, 40, 40), 18))


def art_today(c, t):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(20, 8, 15), C(90, 20, 30), C(25, 8, 12)])))
    bill, every = CUE["billion"], CUE["every"]
    for k in range(16):  # rays
        a = k / 16 * 2 * math.pi + t * 0.4
        p = skia.Path()
        p.moveTo(540, 1380)
        p.lineTo(540 + math.cos(a) * 1400, 1380 + math.sin(a) * 1400)
        p.lineTo(540 + math.cos(a + 0.14) * 1400, 1380 + math.sin(a + 0.14) * 1400)
        p.close()
        c.drawPath(p, P(C(255, 180, 160, 20)))
    # a globe with glasses orbiting it
    gx, gy, gr = 540, 1380, 260
    c.drawCircle(gx, gy, gr, P(Shader=rad(gx - 80, gy - 90, gr * 1.3, [C(120, 190, 255), C(40, 100, 190), C(15, 40, 90)])))
    for k, (dx, dy, rx, ry) in enumerate(((-90, -60, 90, 60), (70, 40, 110, 70), (-40, 120, 70, 40), (110, -110, 60, 40))):
        c.drawOval(skia.Rect(gx + dx - rx + 30 * math.sin(t * 0.5), gy + dy - ry, gx + dx + rx + 30 * math.sin(t * 0.5), gy + dy + ry), P(C(90, 170, 90, 220)))
    c.drawCircle(gx, gy, gr, S(C(200, 230, 255), 5))
    n = 6 + int(10 * ease((t - bill + 0.3) / 0.8))
    for k in range(n):
        a = k / n * 2 * math.pi + t * 1.1
        ox, oy = gx + math.cos(a) * (gr + 150), gy + math.sin(a) * (gr + 60) * 0.7
        if math.sin(a) < 0 and abs(math.cos(a)) < 0.8:
            continue  # behind the globe
        soda_glass(c, ox, oy + 70, 0.45, t + k, 0.75)
    if t > every:
        for k in range(10):
            a = k / 10 * 2 * math.pi + t
            sparkle(c, gx + math.cos(a) * 470, gy + math.sin(a) * 330, 9, 200)


def bottle_mascot(c, t):
    c.drawOval(skia.Rect(-120, -16, 120, 16), P(C(0, 0, 0, 120), MaskFilter=blur(14)))
    bottle(c, 0, 0, 1.0, t, None)
    fy = -150
    for side in (-1, 1):
        r = skia.RRect.MakeRectXY(skia.Rect(side * 36 - 32, fy - 26, side * 36 + 32, fy + 20), 16, 16)
        c.drawRRect(r, P(Shader=lin((0, fy - 26), (0, fy + 20), [C(70, 70, 90), C(8, 8, 14)])))
        c.drawRRect(r, S(C(10, 10, 10), 6))
    c.drawLine(-6, fy - 8, 6, fy - 8, S(C(10, 10, 10), 8))
    c.drawArc(skia.Rect(-30, fy + 30, 30, fy + 70), 20, 140, False, S(C(250, 230, 210), 7))


def art_cta(c, t):
    U.T_EIGHT = -10
    U.background(c, t, 0)
    U.spotlight(c, t, 0)
    U.pedestal(c, t)
    c.save()
    c.translate(540, 1440)
    bottle_mascot(c, t)
    c.restore()
    c.drawPaint(P(C(10, 6, 14, 150)))


ART = [art_hook, art_atlanta, art_mix, art_name, art_tonic, art_fountain, art_broke, art_candler, art_removed, art_today, art_cta]
PUSH = [(1.0, 1.06), (1.0, 1.06), (1.0, 1.06), (1.0, 1.05), (1.0, 1.06), (1.0, 1.06), (1.06, 1.0), (1.0, 1.06), (1.0, 1.07), (1.0, 1.06), (1.0, 1.0)]
ANCHOR = [(540, 1500), (540, 1500), (540, 1500), (540, 1300), (540, 1500), (540, 1500), (540, 1500), (540, 1500), (540, 1400), (540, 1380), (540, 1300)]


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
    line(img, "Coca-Cola was", 230, F_MID)
    line(img, "invented as", 330, F_MID)
    slam(img, "MEDICINE!", 430, t, CUE["medicine"] - 0.1, GOLD, 150)
    text_block(img, "...and it really had COCAINE in it!", font(FONT_B, 54), 660, t, GREEN, CUE["cocaine"])
    impact(img, t, CUE["medicine"] + 0.1, 18)


def tx_atlanta(img, t):
    tag(img, "ATLANTA, 1886", t, (160, 50, 50))
    title(img, t, "Pharmacist John Pemberton", "Hooked on morphine after the war", CUE["morphine"])


def tx_mix(img, t):
    title(img, t, "He wanted a cure...", "Coca leaves + kola nuts", CUE["coca2"], sub_color=GREEN)


def tx_name(img, t):
    title(img, t, "Where the name comes from!")


def tx_tonic(img, t):
    title(img, t, "Sold as a \"brain tonic\"")
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 640, "MIRACLE CURE?", t, CUE["promise"], col=GOLD, size=96)
    impact(img, t, CUE["promise"] + 0.15, 10)


def tx_fountain(img, t):
    title(img, t, "5 cents a glass", "...at a drugstore soda fountain", CUE["soda"])
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "ONLY 9 A DAY", t, CUE["nine"], col=RED, size=96)
    impact(img, t, CUE["nine"] + 0.15, 12)


def tx_broke(img, t):
    title(img, t, "He never got rich", "He died almost broke.", CUE["died"], sub_color=(190, 205, 235))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "BROKE", t, CUE["broke"], col=(170, 180, 200), size=110)
    impact(img, t, CUE["broke"] + 0.15, 10)


def tx_candler(img, t):
    title(img, t, "Asa Candler bought the formula")
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 640, "~$2,300", t, CUE["money"], col=GOLD, size=110)
    impact(img, t, CUE["money"] + 0.15, 12)


def tx_removed(img, t):
    tag(img, "EARLY 1900s", t, (60, 110, 170))
    title(img, t, "The cocaine was taken out")
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 640, "REMOVED", t, CUE["quietly"], col=RED, size=110)
    impact(img, t, CUE["quietly"] + 0.15, 12)


def tx_today(img, t):
    title(img, t, "Today, the company sells", y=260)
    slam(img, "2 BILLION", 420, t, CUE["billion"] - 0.1, GOLD, 150)
    text_block(img, "drinks... every single day!", font(FONT_B, 56), 630, t, (255, 255, 255), CUE["every"])
    impact(img, t, CUE["billion"] + 0.1, 16)


def tx_cta(img, t):
    text_block(img, "Learned something new?", font(FONT_B, 68), 330, t, delay=0.0)
    make_salt.draw_cta(img, ImageDraw.Draw(img, "RGBA"), W / 2, 1250, t, off=CUE["cta_off"])


TEXT = [tx_hook, tx_atlanta, tx_mix, tx_name, tx_tonic, tx_fountain, tx_broke, tx_candler, tx_removed, tx_today, tx_cta]
base.TRANSITION = splat

if __name__ == "__main__":
    voice = f"{VOICE_DIR}/voice.mp3"
    tl = Timeline(voice)
    firsts = ["in eighteen", "you|he want", "coca from", "he sold", "a glass", "merger|pemberton never", "business", "by the early",
              "company", "learn"]
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
               medicine=f("medicine", 0, 0.0), cocaine=f("had cocaine", 0, -0.2),  # "cocaine" alone matched "coca" at 0.04 s
               pain=f("pain", 1), morphine=f("morphine", 1),
               coca2=f("coca", 2), kola=f("kola|colon|cola", 2), syrup=f("syrup", 2),
               coca3=f("coca", 3), cola=f("cola|call", 3), name=f("name", 3),
               brain=f("brain", 4), promise=f("promise", 4, 0.15), headaches=f("headaches", 4), tired=f("tiredness", 4), addiction=f("morphine", 4),
               five=f("five", 5), soda=f("soda", 5), nine=f("nine", 5, 0.15),
               died=f("died", 6), broke=f("broke", 6, 0.15),
               formula=f("formula", 7), money=f("two thousand", 7, 0.15),
               cocaine8=f("cocaine", 8), quietly=f("quietly", 8, 0.15),
               billion=f("billion", 9, 0.0), every=f("every", 9))
    # LIKE tap a beat early so SUBSCRIBED + bell stay >= 0.5 s inside 65 s (voice untouched)
    CUE["cta_off"] = round(max(0.0, tl.find("like|within", S0[10]) - S0[10] - 1.6 + 0.15 - 0.4), 2)
    print("starts:", S0)
    print("durations:", durs, round(sum(durs), 2))
    print("cues:", {k: v for k, v in CUE.items() if k not in ("d", "S")})
    print("subscribed at", CUE["cta_off"] + 3.6, "of CTA", durs[-1])
    json.dump({"starts": S0, "durs": durs, "cues": {k: v for k, v in CUE.items() if k not in ("d", "S")}}, open(f"{VOICE_DIR}/plan.json", "w"), indent=1)
    if STILLS:
        out = os.environ.get("STILLS_DIR", VOICE_DIR + "/stills")
        os.makedirs(out, exist_ok=True)
        for i in ONLY:
            for tt in STILLS:
                img = Image.new("RGBA", (W, H))
                scene(i, TEXT[i])(img, ImageDraw.Draw(img), float(tt))
                img.convert("RGB").save(f"{out}/cola_{i}_{tt}.png")
        sys.exit()
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), scene(i, TEXT[i])) for i, dd in enumerate(durs)]
    if ONLY:
        base.SCENES[:] = [s for i, s in enumerate(base.SCENES) if i in ONLY]
    ST, C_ = S0, CUE
    ev = [("whoosh", s) for s in ST[1:]]
    ev += [("pop", C_["medicine"]), ("thud", C_["medicine"] + 0.05), ("pop", C_["cocaine"] + 0.4),
           ("thud", ST[1] + C_["pain"]), ("pop", ST[1] + C_["morphine"]),
           ("pop", ST[2] + C_["coca2"] + 0.5), ("pop", ST[2] + C_["kola"] + 0.5), ("ding", ST[2] + C_["syrup"]),
           ("pop", ST[3] + C_["coca3"]), ("pop", ST[3] + C_["cola"]), ("ding", ST[3] + C_["name"]),
           ("ding", ST[4] + C_["brain"]), ("thud", ST[4] + C_["promise"] + 0.15), ("pop", ST[4] + C_["headaches"]),
           ("pop", ST[4] + C_["tired"]), ("pop", ST[4] + C_["addiction"]),
           ("pop", ST[5] + C_["five"]), ("thud", ST[5] + C_["nine"] + 0.15),
           ("thud", ST[6] + C_["broke"] + 0.15),
           ("ding", ST[7] + C_["formula"]), ("thud", ST[7] + C_["money"] + 0.15),
           ("pop", ST[8] + C_["cocaine8"]), ("thud", ST[8] + C_["quietly"] + 0.15),
           ("thud", ST[9] + C_["billion"]), ("ding", ST[9] + C_["billion"] + 0.05),
           ("click", ST[10] + C_["cta_off"] + 1.6), ("click", ST[10] + C_["cta_off"] + 3.6), ("ding", ST[10] + C_["cta_off"] + 3.65)]
    ev += [("click", ST[5] + C_["nine"] - 0.3 + k * 0.07) for k in range(9)]  # nine glasses
    ev = [(k, round(v, 3)) for k, v in ev if 0 <= v < total]
    audio.music("music.wav", total, bpm=104, seed=17)
    audio.sfx("sfx.wav", total, ev)
    base.OUT = "base_cola.mp4"
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_cola.mp4", voice, "music.wav", "sfx.wav", OUTFILE)
    print("wrote", OUTFILE)
