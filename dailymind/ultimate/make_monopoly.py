"""YouTube Short: "Monopoly Was Invented to Show Monopolies Are EVIL" (Skia toon, vidIQ "Chris" voice, CTA v2).

Follow-up to the best performer (chess): a famous game + a hidden origin twist + characters made of game pieces.
Facts: Lizzie Magie patented The Landlord's Game (1904) to show how land monopoly enriches landlords and impoverishes
tenants (Georgist ideas); it had two rule sets (anti-monopolist "Prosperity" where all gain, and a monopolist one);
players made homemade boards, including an Atlantic City version; Charles Darrow sold his version as his own in the
1930s, Parker Brothers bought it in 1935 and he became a millionaire; Magie was paid about $500 for her patent; Darrow
was credited as the inventor for decades. No trademarked logos, mascot or exact board art: generic board, generic tokens.

Usage: python make_monopoly.py final.mp4 [scene,...] [t1,...]   stills: STILLS_DIR=dir python make_monopoly.py x 0,1 1.0
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
sys.argv = [sys.argv[0], "base_monopoly.mp4"]
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

GOLD, RED, GREEN, CASH = (255, 200, 60), (235, 60, 60), (90, 210, 120), (150, 215, 140)
make_ketchup.SPLAT_COLOR = (250, 195, 50)
base.HOOK_SKIP = 0.0
base.CRF = 16
CUE = {}
VOICE_DIR = "../monopoly"
TAIL = 2.2

LIZZIE = dict(skin=(245, 210, 185), hair="neat", hair_col=(110, 60, 40), coat=(70, 110, 120), dress=(70, 110, 120), pearls=True, lips=True,
              glasses=True, nose="small")
DARROW = dict(skin=(240, 200, 170), hair="neat", hair_col=(50, 40, 35), coat=(90, 80, 70), vest=(150, 40, 50), pants=(70, 60, 55),
              mustache=True, hat="bowler", nose="long")
LANDLORD = dict(skin=(245, 195, 170), hair="neat", hair_col=(60, 50, 45), coat=(40, 40, 50), vest=(200, 160, 60), pants=(40, 40, 50),
                mustache=True, hat="tophat", nose="long")
TENANT = dict(skin=(230, 185, 150), hair="cap", hair_col=(90, 60, 40), coat=(140, 120, 100), pants=(80, 70, 60), nose="small")
KIDM = dict(KID, coat=(60, 150, 90))
GROUPS = [(150, 80, 50), (120, 200, 240), (230, 90, 170), (240, 150, 40), (220, 50, 50), (250, 220, 60), (60, 170, 90), (50, 80, 170)]


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
    return x, (abs(x - x0) / 40) if t < dur else None


# ---------- game pieces with faces ----------

def face(c, x, y, s, mood="smile", look=(0, 0), blink=False, col=(30, 22, 18)):
    for side in (-1, 1):
        ex = x + side * 14 * s
        if blink or mood == "closed":
            c.drawArc(skia.Rect(ex - 8 * s, y - 5 * s, ex + 8 * s, y + 7 * s), 200, 140, False, S(C(*col), 3.5 * s))
        else:
            hh = (13 if mood in ("scared", "wide") else 10) * s
            c.drawOval(skia.Rect(ex - 8 * s, y - hh, ex + 8 * s, y + hh), P(C(255, 255, 255)))
            c.drawCircle(ex + look[0] * 3 * s, y + look[1] * 3 * s, 5 * s, P(C(30, 22, 18)))
            c.drawOval(skia.Rect(ex - 8 * s, y - hh, ex + 8 * s, y + hh), S(C(30, 22, 18), 2 * s))
        if mood == "evil":
            c.drawLine(ex - 10 * s, y - 14 * s + side * 4 * s, ex + 10 * s, y - 14 * s - side * 4 * s, S(C(*col), 4 * s))
        if mood in ("scared", "sad"):
            c.drawLine(ex - 10 * s, y - 14 * s - side * 4 * s, ex + 10 * s, y - 14 * s + side * 4 * s, S(C(*col), 4 * s))
    my = y + 22 * s
    if mood in ("smile", "closed"):
        c.drawArc(skia.Rect(x - 12 * s, my - 8 * s, x + 12 * s, my + 6 * s), 20, 140, False, S(C(*col), 3.5 * s))
    elif mood == "evil":
        c.drawArc(skia.Rect(x - 18 * s, my - 12 * s, x + 18 * s, my + 10 * s), 10, 160, True, P(C(110, 25, 35)))
        c.drawRect(skia.Rect(x - 12 * s, my - 4 * s, x + 12 * s, my + 1 * s), P(C(255, 255, 255)))
    elif mood in ("scared", "wide"):
        c.drawOval(skia.Rect(x - 7 * s, my - 4 * s, x + 7 * s, my + 12 * s), P(C(110, 25, 35)))
    elif mood == "sad":
        c.drawArc(skia.Rect(x - 12 * s, my, x + 12 * s, my + 12 * s), 200, 140, False, S(C(*col), 3.5 * s))


def house(c, x, y, s, t, mood="smile", col=(70, 180, 90), hop=0.0, look=(0, 0), ph=0.0):
    """Little green game house standing on (x, y)."""
    c.save()
    c.translate(x, y - hop)
    c.scale(s, s)
    c.drawOval(skia.Rect(-46, -8, 46, 8), P(C(0, 0, 0, 90), MaskFilter=blur(6)))
    blob(c, rrect(-40, -70, 40, 0, 6), col, 1.25, 0.7)
    roof = skia.Path()
    roof.moveTo(-50, -66)
    roof.lineTo(0, -112)
    roof.lineTo(50, -66)
    roof.close()
    blob(c, roof, tuple(int(v * 0.85) for v in col), 1.3, 0.65)
    c.restore()
    face(c, x, y - hop - 42 * s, s * 0.9, mood, look, blinking(t, ph))


def hotel(c, x, y, s, t, mood="evil", hop=0.0):
    c.save()
    c.translate(x, y - hop)
    c.scale(s, s)
    c.drawOval(skia.Rect(-80, -10, 80, 10), P(C(0, 0, 0, 100), MaskFilter=blur(8)))
    blob(c, rrect(-74, -120, 74, 0, 8), (215, 50, 50), 1.25, 0.7)
    roof = skia.Path()
    roof.moveTo(-84, -116)
    roof.lineTo(0, -170)
    roof.lineTo(84, -116)
    roof.close()
    blob(c, roof, (180, 35, 35), 1.3, 0.65)
    c.restore()
    face(c, x, y - hop - 70 * s, s * 1.3, mood, (0, 0), blinking(t, 0.4))


def tophat_token(c, x, y, s, t, mood="evil", look=(0, 0), chomp=0.0):
    """The villain token: a silver top hat with a face; chomp 0..1 opens a big mouth."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawOval(skia.Rect(-120, -16, 120, 16), P(C(0, 0, 0, 110), MaskFilter=blur(10)))
    blob(c, oval(0, -14, 120, 26), (170, 175, 185), 1.5, 0.6)
    crown = skia.Path()
    crown.moveTo(-80, -20)
    crown.lineTo(-90, -230)
    crown.cubicTo(-40, -246, 40, -246, 90, -230)
    crown.lineTo(80, -20)
    crown.close()
    blob(c, crown, (190, 195, 205), 1.5, 0.6)
    c.drawRect(skia.Rect(-82, -80, 82, -50), P(C(120, 125, 135)))
    c.drawLine(-60, -215, -50, -100, S(C(255, 255, 255, 120), 10))
    c.restore()
    if chomp > 0:
        mx, my = x, y - 140 * s
        c.drawOval(skia.Rect(mx - 50 * s, my - 10 * s, mx + 50 * s, my + 60 * s * chomp + 10 * s), P(C(90, 20, 30)))
        for k in range(5):
            c.drawRect(skia.Rect(mx - 40 * s + k * 18 * s, my - 8 * s, mx - 28 * s + k * 18 * s, my + 6 * s), P(C(255, 255, 255)))
        face(c, x, y - 180 * s, s * 1.6, "evil", look, False)
    else:
        face(c, x, y - 165 * s, s * 1.6, mood, look, blinking(t, 0.2))


def bill(c, x, y, s, rot=0.0, col=CASH):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    blob(c, rrect(-50, -24, 50, 24, 4), col, 1.2, 0.75)
    c.drawCircle(0, 0, 12, P(C(255, 255, 255, 140)))
    c.restore()


def board(c, cx, cy, size, t, tilt=0.55, hl=None):
    """Generic property-trading board in perspective (square ring of spaces, colored property strips)."""
    n = 10
    c.save()
    c.translate(cx, cy)
    c.scale(1, tilt)
    c.rotate(45)
    half = size / 2
    c.drawRect(skia.Rect(-half - 20, -half - 20, half + 20, half + 20), P(C(0, 0, 0, 120), MaskFilter=blur(20)))
    c.drawRect(skia.Rect(-half, -half, half, half), P(Shader=lin((-half, -half), (half, half), [C(210, 235, 215), C(180, 215, 190)])))
    cell = size / (n + 2)
    k = 0
    for side in range(4):
        for i in range(n):
            if side == 0:
                x0, y0 = -half + cell * (i + 1), half - cell
            elif side == 1:
                x0, y0 = half - cell, half - cell * (i + 2)
            elif side == 2:
                x0, y0 = half - cell * (i + 2), -half
            else:
                x0, y0 = -half, -half + cell * (i + 1)
            c.drawRect(skia.Rect(x0, y0, x0 + cell, y0 + cell), S(C(40, 60, 50), 2))
            if i % 3 != 2:
                gc = GROUPS[(k // 2) % len(GROUPS)]
                band = cell * 0.3
                if side == 0:
                    r = skia.Rect(x0, y0, x0 + cell, y0 + band)
                elif side == 1:
                    r = skia.Rect(x0, y0, x0 + band, y0 + cell)
                elif side == 2:
                    r = skia.Rect(x0, y0 + cell - band, x0 + cell, y0 + cell)
                else:
                    r = skia.Rect(x0 + cell - band, y0, x0 + cell, y0 + cell)
                c.drawRect(r, P(C(*gc)))
                k += 1
    c.drawRect(skia.Rect(-half, -half, half, half), S(C(40, 60, 50), 5))
    c.drawRect(skia.Rect(-half + cell, -half + cell, half - cell, half - cell), S(C(40, 60, 50), 3))
    c.restore()


def bg(c, top, bot):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(*top), C(*bot)])))


def rays(c, t, col=(255, 220, 160), a=16, y=1300):
    for k in range(16):
        ang = k / 16 * 2 * math.pi + t * 0.3
        p = skia.Path()
        p.moveTo(540, y)
        p.lineTo(540 + math.cos(ang) * 1600, y + math.sin(ang) * 1600)
        p.lineTo(540 + math.cos(ang + 0.12) * 1600, y + math.sin(ang + 0.12) * 1600)
        p.close()
        c.drawPath(p, P(C(*col, a)))


def paper(c, x, y, w, h, rot, title_txt, lines=6, stamp_txt=None, stamp_k=0.0, col=(245, 238, 215)):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.drawRect(skia.Rect(-w / 2 + 8, -h / 2 + 10, w / 2 + 8, h / 2 + 10), P(C(0, 0, 0, 90), MaskFilter=blur(10)))
    blob(c, rrect(-w / 2, -h / 2, w / 2, h / 2, 6), col, 1.03, 0.88)
    f = skia.Font(FB, 34)
    tw = f.measureText(title_txt)
    c.drawString(title_txt, -tw / 2, -h / 2 + 60, f, P(C(60, 40, 30)))
    for k in range(lines):
        c.drawLine(-w / 2 + 40, -h / 2 + 100 + k * 34, w / 2 - 40 - (k % 3) * 40, -h / 2 + 100 + k * 34, S(C(140, 125, 105), 4))
    if stamp_txt and stamp_k > 0:
        sc = 1.6 - 0.6 * min(1, stamp_k)
        c.save()
        c.translate(w * 0.12, h * 0.28)
        c.rotate(-14)
        c.scale(sc, sc)
        fs = skia.Font(FB, 44)
        sw = fs.measureText(stamp_txt)
        a = int(230 * min(1, stamp_k * 3))
        c.drawRoundRect(skia.Rect(-sw / 2 - 20, -40, sw / 2 + 20, 24), 10, 10, S(C(200, 40, 40, a), 7))
        c.drawString(stamp_txt, -sw / 2, 8, fs, P(C(200, 40, 40, a)))
        c.restore()
    c.restore()


def box(c, x, y, s, rot=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    blob(c, rrect(-160, -100, 160, 0, 8), (220, 50, 50), 1.25, 0.7)
    c.drawRect(skia.Rect(-160, -70, 160, -30), P(C(250, 245, 235)))
    f = skia.Font(FB, 30)
    s_ = "PROPERTY GAME"
    w = f.measureText(s_)
    c.drawString(s_, -w / 2, -40, f, P(C(200, 40, 40)))
    c.restore()


# ---------- scenes ----------

def art_hook(c, t):
    bg(c, (25, 20, 35), (60, 40, 50))
    rays(c, t, (255, 210, 160), 14, 1450)
    board(c, 540, 1560, 900, t)
    ev, rb = CUE["evil"], CUE["robbed"]
    houses = [(300, 1520), (420, 1640), (660, 1660), (790, 1530), (560, 1440)]
    gone = 0
    for i, (hx, hy) in enumerate(houses):
        eat = ev + 0.15 + i * 0.35
        if t < eat:
            scared = t > ev
            house(c, hx + (3 * math.sin(t * 40 + i) if scared else 0), hy, 1.1, t, "scared" if scared else "smile",
                  hop=abs(math.sin(t * 4 + i)) * 10 if not scared else 0, look=(1 if hx < 540 else -1, -0.5) if scared else (0, 0), ph=i)
        else:
            gone += 1
    # the top hat villain slides in and chomps
    tx = 540 + 300 * (1 - ease(min(1, t / 1.2)))
    chomp = 0.0
    for i in range(len(houses)):
        eat = ev + 0.15 + i * 0.35
        if eat - 0.15 < t < eat + 0.2:
            chomp = math.sin(math.pi * (t - (eat - 0.15)) / 0.35)
    tophat_token(c, tx, 1660, 1.15 * (1 + 0.05 * gone), t, "evil", (0, 0.2), chomp)
    if t > rb:  # a dim portrait of the robbed inventor appears on the right
        k = pop_in(t, rb - 0.05)
        c.save()
        c.translate(900, 1060)
        c.scale(k, k)
        c.drawRoundRect(skia.Rect(-110, -150, 110, 120), 16, 16, P(C(230, 210, 170)))
        c.drawRoundRect(skia.Rect(-110, -150, 110, 120), 16, 16, S(C(160, 120, 60), 10))
        c.save()
        c.clipRect(skia.Rect(-100, -140, 100, 110))
        stand(c, LIZZIE, 0, 300, 0.75, t, eyes="sad", mouth="frown", brows="sad", look=(-1, 0), hands=[(-30, 150), (30, 150)])
        c.restore()
        c.restore()


def art_patent(c, t):
    bg(c, (35, 30, 30), (80, 65, 50))
    for k in range(9):  # wallpaper stripes
        c.drawRect(skia.Rect(k * 130, 880, k * 130 + 60, 1600), P(C(255, 230, 190, 16)))
    glow(c, 820, 1000, 420, (255, 200, 120), int(110 * flicker(t, 2)))
    c.drawRect(skia.Rect(0, 1600, W, H), P(Shader=lin((0, 1600), (0, H), [C(110, 75, 50), C(60, 40, 25)])))
    blob(c, rrect(380, 1500, 1080, 1580, 10), (120, 80, 50))  # desk
    c.drawRect(skia.Rect(420, 1580, 450, 1900), P(C(90, 60, 35)))
    c.drawRect(skia.Rect(1000, 1580, 1030, 1900), P(C(90, 60, 35)))
    pt = CUE["patent"]
    x, walk = walk_in(t, -150, 240, 1.6)
    stand(c, LIZZIE, x, 1880, 1.35, t, walk=walk, eyes="open", mouth="grin" if t > pt else "smile", brows="up", look=(1, 0.3),
          hands=[(-30, 150), (130, 20)])
    paper(c, 720, 1330, 360, 300, -6, "PATENT", 5, "GRANTED", (t - pt) / 0.3 if t > pt else 0)
    bg_k = pop_in(t, CUE["landlord1"] - 0.1)
    if bg_k > 0:  # the board game she invented
        c.save()
        c.translate(780, 1540)
        c.scale(bg_k, bg_k)
        board(c, 0, 0, 300, t, 0.5)
        c.restore()


def art_greedy(c, t):
    bg(c, (25, 20, 35), (55, 45, 60))
    c.drawRect(skia.Rect(0, 1700, W, H), P(C(60, 50, 55)))
    gr = CUE["richer"]
    grow = ease((t - gr + 0.2) / 2.0)
    s_l = 1.15 + 0.35 * grow
    stand(c, LANDLORD, 330, 1900, s_l, t, eyes="squint", mouth="grin", brows="smug", look=(1, 0), hands=[(-80, 40), (80, 40)],
          squash=0.04 * grow)
    for k in range(4):  # money bags pile up beside him
        if grow > k * 0.25:
            bx, by = 120 + k * 40, 1890 - k * 30
            blob(c, oval(bx, by - 40, 50, 55), (210, 180, 110), 1.3, 0.7)
            c.drawString("$", bx - 14, by - 25, skia.Font(FB, 44), P(C(90, 70, 30)))
    for i, x in enumerate((700, 860, 1010)):  # tenants get thinner and sadder
        broke = t > CUE["broke"]
        stand(c, TENANT, x, 1900, 0.95 - 0.12 * grow, t, eyes="sad", mouth="frown" if broke else "smile", brows="sad", look=(-1, 0),
              hands=[(-60, 60), (60, 60)] if not broke else [(-90, 100), (90, 100)])
        if broke:  # empty pockets
            for side in (-1, 1):
                px, py = x + side * 60, 1900 - 110
                p = skia.Path()
                p.moveTo(px - 18, py)
                p.lineTo(px + 18, py)
                p.lineTo(px + 10 * side, py + 34 + 4 * math.sin(t * 3 + i))
                p.close()
                blob(c, p, (235, 230, 220), 1.05, 0.8)
    for k in range(6):  # bills fly from the tenants to the landlord
        u = ((t * 0.7 + k / 6) % 1)
        x0, y0 = 860, 1500
        x1, y1 = 360, 1400
        bill(c, x0 + (x1 - x0) * u, y0 + (y1 - y0) * u - 160 * math.sin(math.pi * u), 0.7, 360 * u)


def art_rules(c, t):
    bg(c, (25, 25, 40), (50, 45, 65))
    c.drawLine(540, 880, 540, H, S(C(255, 255, 255, 160), 6))
    c.drawRect(skia.Rect(0, 1700, W, H), P(C(50, 45, 60)))
    sh, cr = CUE["shares"], CUE["crushes"]
    for side, (bx, col, lab) in enumerate(((270, (60, 150, 90), "RULES #1"), (810, (200, 50, 50), "RULES #2"))):
        k = pop_in(t, 0.4 + side * 0.35)
        if k <= 0:
            continue
        c.save()
        c.translate(bx, 1180 + 8 * math.sin(t * 2 + side))
        c.scale(k, k)
        c.drawRect(skia.Rect(-150, -100, 150, 110), P(C(0, 0, 0, 100), MaskFilter=blur(12)))
        blob(c, rrect(-150, -100, 0, 100, 8), (245, 240, 225), 1.03, 0.88)
        blob(c, rrect(0, -100, 150, 100, 8), (245, 240, 225), 1.03, 0.88)
        flip = (t * 1.6 + side * 0.5) % 1
        pg = skia.Path()  # a page turning
        w = 150 * math.cos(math.pi * flip)
        pg.moveTo(0, -100)
        pg.lineTo(w, -100 - 12 * math.sin(math.pi * flip))
        pg.lineTo(w, 100 - 12 * math.sin(math.pi * flip))
        pg.lineTo(0, 100)
        pg.close()
        c.drawPath(pg, P(C(255, 252, 240)))
        c.drawPath(pg, S(C(150, 140, 120), 3))
        for j in range(5):
            c.drawLine(-130, -60 + j * 30, -20, -60 + j * 30, S(C(140, 125, 105), 4))
        c.drawRect(skia.Rect(-150, -140, 150, -100), P(C(*col)))
        f = skia.Font(FB, 30)
        w2 = f.measureText(lab)
        c.drawString(lab, -w2 / 2, -110, f, P(C(255, 255, 255)))
        c.restore()
    # left: everybody shares
    for i, x in enumerate((110, 270, 430)):
        happy = t > sh
        stand(c, crowd_look(i), x, 1900, 0.92, t, eyes="closed" if happy else "open", mouth="laugh" if happy else "smile", brows="up",
              look=(0, 0), hands=[(-50, -150), (50, -150)] if happy else [(-30, 150), (30, 150)])
        if happy:
            for k in range(2):
                u = ((t - sh) * 1.2 + k * 0.5 + i * 0.3) % 1
                bill(c, x + 30 * math.sin(u * 6), 1450 - 200 * u, 0.5, 200 * u)
    # right: one player crushes everyone
    lk = t > cr
    stand(c, LANDLORD, 820, 1900, 1.05 * (1 + 0.2 * ease((t - cr) / 0.6)), t, eyes="squint", mouth="grin" if lk else "smile", brows="smug",
          look=(0, 0), hands=[(-120, -30), (120, -30)] if lk else [(-30, 150), (30, 150)])
    for i, x in enumerate((640, 1000)):
        sq = ease((t - cr - 0.1) / 0.4)
        stand(c, TENANT, x, 1900, 0.75 * (1 - 0.3 * sq), t, eyes="sad", mouth="frown", brows="sad", look=(0 if i else 1, 0), hands=[(-30, 150), (30, 150)],
              squash=0.25 * sq)
    if lk:
        for k in range(5):
            u = ((t - cr) * 1.2 + k / 5) % 1
            bill(c, 820 + 140 * math.cos(k * 1.3 + u), 1500 - 240 * u, 0.55, 300 * u)


def art_loved(c, t):
    bg(c, (35, 15, 25), (80, 30, 45))
    rays(c, t, (255, 120, 120), 16)
    c.drawRect(skia.Rect(0, 1700, W, H), P(C(60, 25, 35)))
    q = pop_in(t, 0.2)
    if q > 0:
        c.save()
        c.translate(540, 1150)
        c.scale(q, q)
        f = skia.Font(FB, 260)
        w = f.measureText("?")
        c.drawString("?", -w / 2 + 8, 90 + 10, f, P(C(0, 0, 0, 140)))
        c.drawString("?", -w / 2, 90, f, P(C(255, 220, 120)))
        c.restore()
    for i, x in enumerate((140, 330, 750, 940)):  # the crowd chants for the greedy rules
        bounce = abs(math.sin(t * 6 + i)) * 16
        stand(c, crowd_look(i + 1), x, 1900 - bounce, 0.85, t, eyes="closed", mouth="laugh", brows="up", look=(0, 0),
              hands=[(-60, -190), (60, -190)])
    tophat_token(c, 540, 1860, 0.85, t, "evil", (0, 0))


def art_homemade(c, t):
    bg(c, (40, 30, 25), (90, 65, 45))
    glow(c, 540, 1000, 450, (255, 200, 120), int(110 * flicker(t, 1)))
    c.drawLine(540, 860, 540, 960, S(C(40, 30, 25), 5))
    blob(c, oval(540, 980, 60, 30), (230, 200, 120))
    blob(c, rrect(120, 1560, 960, 1640, 12), (140, 95, 60))  # kitchen table
    c.drawRect(skia.Rect(160, 1640, 190, 1900), P(C(100, 65, 40)))
    c.drawRect(skia.Rect(890, 1640, 920, 1900), P(C(100, 65, 40)))
    draw = ease((t - 0.3) / 3.0)
    c.save()  # a hand-drawn board on cardboard: lines appear as they're drawn
    c.translate(540, 1460)
    c.scale(1, 0.45)
    c.rotate(45)
    half = 230
    c.drawRect(skia.Rect(-half, -half, half, half), P(C(215, 185, 140)))
    per = 8 * half * draw
    p = skia.Path()
    p.moveTo(-half, -half)
    pts = [(half, -half), (half, half), (-half, half), (-half, -half)]
    remaining = per
    cx_, cy_ = -half, -half
    for px, py in pts:
        seg = abs(px - cx_) + abs(py - cy_)
        if remaining <= 0:
            break
        u = min(1, remaining / seg)
        p.lineTo(cx_ + (px - cx_) * u, cy_ + (py - cy_) * u)
        remaining -= seg
        cx_, cy_ = px, py
    c.drawPath(p, S(C(60, 40, 30), 8))
    c.restore()
    for j, (hx, hy) in enumerate(((420, 1420), (540, 1370), (660, 1420), (540, 1480))):
        k = pop_in(t, 1.2 + j * 0.55)
        if k > 0:
            house(c, hx, hy, 0.5 * k, t, "smile", hop=abs(math.sin(t * 5 + j)) * 6, ph=j)
    ac = CUE["atlantic"]
    if t > ac - 0.2:  # boardwalk signpost
        k = pop_in(t, ac - 0.2)
        c.save()
        c.translate(880, 1540)
        c.scale(k, k)
        c.drawLine(0, 0, 0, -300, S(C(110, 80, 50), 14))
        blob(c, rrect(-170, -330, 120, -250, 8), (40, 110, 170))
        c.drawString("ATLANTIC CITY", -150, -278, skia.Font(FB, 34), P(C(255, 255, 255)))
        c.restore()
    hx = 540 + 160 * math.cos(t * 2.2)
    stand(c, KIDM, 300, 1880, 1.05, t, eyes="open", mouth="grin", brows="up", look=(1, 0.5), hands=[(-30, 150), (130, 20 + 15 * math.sin(t * 6))])
    stand(c, crowd_look(2), 760, 1880, 1.0, t, eyes="open", mouth="smile", brows="up", look=(-1, 0.5), hands=[(-110, 30), (30, 150)])
    c.drawLine(hx, 1420, hx + 20, 1470, S(C(250, 200, 60), 10))  # pencil


def art_darrow(c, t):
    bg(c, (20, 20, 30), (45, 40, 55))
    c.drawRect(skia.Rect(0, 1650, W, H), P(C(45, 40, 50)))
    cp = CUE["copied"]
    x, walk = walk_in(t, 1250, 760, 1.8)
    sneaky = t < cp + 0.3
    peek = math.sin(t * 3.2) if sneaky and walk is None else -1
    stand(c, DARROW, x, 1900, 1.3, t, walk=walk, eyes="squint" if sneaky else "open", mouth="grin", brows="smug", look=(peek, 0.2),
          hands=[(-120, 30), (30, 150)] if sneaky else [(-30, 150), (110, -40)])
    paper(c, 340, 1500, 420, 300, 4, "HOMEMADE GAME", 6)
    if t > cp:  # a copy slides off the original
        u = ease((t - cp) / 0.6)
        paper(c, 340 + 80 * u, 1500 - 320 * u, 420, 300, 4 - 10 * u, "MY INVENTION", 6, "COPIED", (t - cp - 0.4) / 0.3 if t > cp + 0.4 else 0,
              col=(255, 250, 240))


def art_hit(c, t):
    U.T_EIGHT = CUE["millionaire"] - 0.6
    bg(c, (40, 15, 20), (100, 35, 40))
    rays(c, t, (255, 220, 150), 18, 1350)
    c.drawRect(skia.Rect(0, 1700, W, H), P(C(70, 30, 35)))
    hit = CUE["hit"]
    n = int(min(12, max(0, (t - hit + 0.4) * 10)))
    for i in range(n):  # stacks of game boxes
        row, col = divmod(i, 4)
        box(c, 220 + col * 210 + (row % 2) * 20, 1700 - row * 100, 0.6, (i * 7) % 9 - 4)
    for x, y, r, face_, speed in U.coins_at(t):  # coins behind him
        U.draw_coin(c, x, y, r, face_, speed)
    rich = t > CUE["millionaire"]
    stand(c, DARROW, 540, 1900, 1.25, t, eyes="closed" if rich else "open", mouth="laugh" if rich else "grin", brows="up", look=(0, -0.2),
          hands=[(-90, -180), (90, -180)] if rich else [(-30, 150), (30, 150)], hat_bounce=-8 * abs(math.sin(t * 5)) if rich else 0)


def art_lizzie(c, t):
    bg(c, (15, 18, 30), (40, 45, 65))
    c.drawRect(skia.Rect(0, 1650, W, H), P(C(40, 42, 55)))
    for k in range(60):  # rain
        r = random.Random(k)
        x0, y0, sp = r.uniform(-200, W), r.uniform(0, H), r.uniform(1500, 2200)
        y = (y0 + t * sp) % (H + 200) - 100
        c.drawLine(x0 + y / H * 160, y, x0 + y / H * 160 + 10, y + 46, S(C(170, 190, 230, 110), 2.5))
    paid = CUE["five"]
    slump = ease((t - paid) / 0.8)
    stand(c, LIZZIE, 540, 1900, 1.4, t, eyes="sad", mouth="frown", brows="sad", look=(0.6, 0.6), hands=[(30, 70), (130, 20)], tilt=-4 * slump)
    if t < paid:  # an envelope drifts down toward her hand
        u = ease(min(1, t / max(0.5, paid - 0.1)))
        ex, ey = 820 - 40 * math.sin(t * 3) * (1 - u), 900 + 640 * u
        c.save()
        c.translate(ex, ey)
        c.rotate(25 * math.sin(t * 2.5) * (1 - u))
        blob(c, rrect(-90, -55, 90, 55, 6), (240, 230, 205), 1.05, 0.85)
        fl = skia.Path()
        fl.moveTo(-90, -55)
        fl.lineTo(0, 10)
        fl.lineTo(90, -55)
        c.drawPath(fl, S(C(170, 150, 120), 4))
        c.restore()
    k = pop_in(t, paid - 0.1)
    if k > 0:  # a tiny check
        c.save()
        c.translate(800, 1560)
        c.rotate(-6)
        c.scale(k, k)
        blob(c, rrect(-130, -60, 130, 60, 8), (230, 245, 230), 1.05, 0.85)
        c.drawString("PAY: $500", -110, 0, skia.Font(FB, 40), P(C(40, 100, 60)))
        c.drawLine(-110, 30, 100, 30, S(C(120, 140, 120), 3))
        c.restore()


def art_decades(c, t):
    bg(c, (25, 20, 35), (70, 55, 60))
    c.drawRect(skia.Rect(0, 1650, W, H), P(C(55, 45, 50)))
    yr = 1935 + int(min(40, max(0, t * 14)))  # calendar years rolling
    blob(c, rrect(780, 940, 1000, 1180, 14), (245, 240, 230), 1.03, 0.88)
    c.drawRect(skia.Rect(780, 940, 1000, 1000), P(C(220, 50, 50)))
    f = skia.Font(FB, 62)
    s = str(yr)
    w = f.measureText(s)
    c.drawString(s, 890 - w / 2, 1110, f, P(C(40, 30, 30)))
    # a golden statue of Darrow on a pedestal, crowd applauding
    blob(c, rrect(380, 1520, 700, 1650, 10), (200, 190, 175), 1.2, 0.75)
    c.saveLayer(None, P(ColorFilter=skia.ColorFilters.Matrix([0.55, 0.3, 0, 0, 0.06, 0.42, 0.3, 0, 0, 0.03, 0.08, 0.08, 0.12, 0, 0, 0, 0, 0, 1, 0])))  # dark bronze
    stand(c, DARROW, 540, 1525, 1.0, t, eyes="open", mouth="grin", brows="smug", look=(0, 0), hands=[(-30, 150), (90, -160)])
    c.restore()
    for i, x in enumerate((330, 470, 800, 960)):
        clap = math.sin(t * 12 + i)
        stand(c, crowd_look(i), x, 1920, 0.8, t, eyes="closed", mouth="laugh", brows="up", look=(0, -0.5),
              hands=[(30 + 15 * clap, -40), (-30 - 15 * clap, -40)])
    # Lizzie, forgotten, in the shadow at the edge
    c.saveLayer(None, P(Alphaf=0.45))
    stand(c, LIZZIE, 150, 1700, 0.75, t, eyes="sad", mouth="frown", brows="sad", look=(1, 0), hands=[(-30, 150), (30, 150)])
    c.restore()


def art_play(c, t):
    bg(c, (30, 25, 40), (75, 55, 70))
    glow(c, 540, 1100, 500, (255, 200, 130), int(100 * flicker(t, 3)))
    blob(c, rrect(80, 1500, 1000, 1580, 12), (130, 90, 55))
    c.drawRect(skia.Rect(120, 1580, 150, 1900), P(C(95, 65, 40)))
    c.drawRect(skia.Rect(930, 1580, 960, 1900), P(C(95, 65, 40)))
    board(c, 540, 1400, 700, t, 0.42)
    hotel(c, 470, 1390, 0.75, t, "evil", abs(math.sin(t * 4)) * 8)
    house(c, 650, 1440, 0.7, t, "scared", hop=0, look=(-1, -0.5), ph=1.0)
    wn = CUE["warning"]
    stand(c, KIDM, 230, 1900, 1.0, t, eyes="closed", mouth="laugh", brows="up", look=(1, 0), hands=[(-60, -170), (60, -170)])
    for k in range(4):
        u = ((t * 0.9 + k / 4) % 1)
        bill(c, 760 - 480 * u, 1420 - 140 * math.sin(math.pi * u), 0.55, 300 * u)
    lose = t > 1.2
    stand(c, crowd_look(3), 860, 1900, 0.95, t, eyes="sad" if lose else "open", mouth="frown" if lose else "smile", brows="sad", look=(-1, -0.2),
          hands=[(-30, 150), (30, 150)])
    if t > wn:
        for k in range(10):
            a = t * 1.3 + k * 0.63
            sparkle(c, 540 + math.cos(a) * 430, 1350 + math.sin(a) * 260, 8, 190, (255, 160, 140))


def art_cta(c, t):
    U.T_EIGHT = -10
    U.background(c, t, 0)
    U.spotlight(c, t, 0)
    c.drawPaint(P(C(10, 6, 14, 120)))
    draw_cta2(c, t, CUE["like"], CUE["sub"])


ART = [art_hook, art_patent, art_greedy, art_rules, art_loved, art_homemade, art_darrow, art_hit, art_lizzie, art_decades, art_play, art_cta]
PUSH = [(1.0, 1.06), (1.0, 1.06), (1.0, 1.06), (1.0, 1.05), (1.0, 1.06), (1.0, 1.06), (1.0, 1.06), (1.0, 1.07), (1.06, 1.0), (1.0, 1.05), (1.0, 1.06), (1.0, 1.0)]
ANCHOR = [(540, 1550), (540, 1500), (540, 1500), (540, 1500), (540, 1400), (540, 1500), (540, 1500), (540, 1500), (540, 1500), (540, 1500), (540, 1450), (540, 1080)]


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
    line(img, "Monopoly was invented", 230, F_MID)
    line(img, "to show monopolies are", 330, font(FONT_B, 66))
    slam(img, "EVIL!", 430, t, CUE["evil"] - 0.1, RED, 180)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "ROBBED", t, CUE["robbed"], col=GOLD, size=100)
    impact(img, t, CUE["evil"] + 0.1, 18)


def tx_patent(img, t):
    tag(img, "1904", t, (70, 110, 120))
    title(img, t, "Lizzie Magie's invention", "\"The Landlord's Game\"", CUE["landlord1"], sub_color=GOLD)


def tx_greedy(img, t):
    title(img, t, "A warning about greedy landlords", "They get richer... everyone goes broke", CUE["richer"])


def tx_rules(img, t):
    title(img, t, "Two sets of rules", y=260)
    text_block(img, "SHARE", font(FONT_B, 70), 470, t, GREEN, CUE["shares"])
    text_block(img, "CRUSH", font(FONT_B, 70), 560, t, RED, CUE["crushes"])


def tx_loved(img, t):
    title(img, t, "Guess which one people loved?")
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 640, "THE GREEDY ONE", t, CUE["d"][4] * 0.55, col=RED, size=90)
    impact(img, t, CUE["d"][4] * 0.55 + 0.15, 12)


def tx_homemade(img, t):
    title(img, t, "People made their own boards", "...one with Atlantic City streets", CUE["atlantic"], sub_color=GOLD)


def tx_darrow(img, t):
    tag(img, "1930s", t, (150, 40, 50))
    title(img, t, "Charles Darrow copied it", "...and sold it as HIS invention", CUE["invention"], sub_color=GOLD)


def tx_hit(img, t):
    title(img, t, "A giant hit!", y=260)
    slam(img, "MILLIONAIRE", 420, t, CUE["millionaire"] - 0.1, GOLD, 130)
    impact(img, t, CUE["millionaire"] + 0.1, 16)


def tx_lizzie(img, t):
    title(img, t, "And Lizzie got...", y=260)
    slam(img, "$500", 420, t, CUE["five"] - 0.1, (190, 205, 235), 200)
    impact(img, t, CUE["five"] + 0.1, 12)


def tx_decades(img, t):
    title(img, t, "For decades...", "the world believed Darrow invented it", CUE["believed"])


def tx_play(img, t):
    title(img, t, "Next time you play...", "...remember, it was a WARNING", CUE["warning"], sub_color=RED)


def tx_cta(img, t):
    pass


TEXT = [tx_hook, tx_patent, tx_greedy, tx_rules, tx_loved, tx_homemade, tx_darrow, tx_hit, tx_lizzie, tx_decades, tx_play, tx_cta]
base.TRANSITION = splat

if __name__ == "__main__":
    voice = f"{VOICE_DIR}/voice.mp3"
    tl = Timeline(voice)
    firsts = ["in nineteen|ninety", "show|she under|wanted", "so our|her", "guess", "players|player", "than|then the|in", "the game", "and losing|lizzie",
              "for decades", "so excited|the", "learn"]
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
               evil=f("evil", 0, 0.0), robbed=f("robbed", 0, 0.15),
               patent=f("pen|patent", 1), landlord1=f("landlords|landlord", 1),
               richer=f("richer", 2), broke=f("broke", 2),
               shares=f("shares", 3), crushes=f("crushes", 3),
               atlantic=f("atlantic", 5),
               copied=f("copied", 6), invention=f("invention", 6),
               hit=f("head|hit", 7), millionaire=f("millionaire", 7, 0.0),
               five=f("five", 8, 0.0),
               believed=f("bully|believed", 9),
               warning=f("warning", 10))
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
                img.convert("RGB").save(f"{out}/mono_{i}_{tt}.png")
        sys.exit()
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), scene(i, TEXT[i])) for i, dd in enumerate(durs)]
    if ONLY:
        base.SCENES[:] = [s for i, s in enumerate(base.SCENES) if i in ONLY]
    ST, C_ = S0, CUE
    ev = [("whoosh", s) for s in ST[1:]]
    ev += [("thud", C_["evil"]), ("thud", ST[0] + C_["robbed"] + 0.15)]
    ev += [("pop", C_["evil"] + 0.15 + i * 0.35) for i in range(5)]  # chomps
    ev += [("thud", ST[1] + C_["patent"] + 0.1), ("ding", ST[1] + C_["landlord1"]),
           ("ding", ST[2] + C_["richer"]),
           ("ding", ST[3] + C_["shares"]), ("thud", ST[3] + C_["crushes"]),
           ("pop", ST[4] + 0.2), ("thud", ST[4] + durs[4] * 0.55 + 0.15),
           ("pop", ST[5] + C_["atlantic"]),
           ("pop", ST[6] + C_["copied"]), ("thud", ST[6] + C_["copied"] + 0.55),
           ("thud", ST[7] + C_["millionaire"]), ("ding", ST[7] + C_["millionaire"] + 0.05),
           ("thud", ST[8] + C_["five"]),
           ("ding", ST[10] + C_["warning"]),
           ("click", ST[11] + C_["like"]), ("ding", ST[11] + C_["like"] + 0.03),
           ("click", ST[11] + C_["sub"]), ("ding", ST[11] + C_["sub"] + 0.35)]
    ev += [("pop", ST[7] + C_["hit"] - 0.4 + i * 0.1) for i in range(12)]  # boxes stacking
    ev += [("click", ST[7] + C_["millionaire"] - 0.6 + 0.35 + i * 0.09 + (i % 3) * 0.03) for i in range(10)]
    ev = [(k, round(v, 3)) for k, v in ev if 0 <= v < total]
    audio.music("music.wav", total, bpm=104, seed=37)
    audio.sfx("sfx.wav", total, ev)
    base.OUT = "base_monopoly.mp4"
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_monopoly.mp4", voice, "music.wav", "sfx.wav", OUTFILE)
    print("wrote", OUTFILE)
