"""YouTube Short: "The Mona Lisa Was NOBODY... Until It Got STOLEN" (Skia toon + physics.py + CTA v2).

Facts (well documented): on 21 Aug 1911 Vincenzo Peruggia, an Italian handyman who had worked at the Louvre, hid in a
storage closet overnight, took the painting off the wall in the morning, hid it under his white workman's smock and
walked out. The theft went unnoticed for over a day (staff assumed it was with the photographers). The Louvre closed
for a week; when it reopened, crowds queued to look at the empty wall. Police questioned Pablo Picasso. Peruggia kept
the painting in a trunk in his small Paris room for over two years, was arrested in Florence in December 1913 after
offering it to an art dealer. The worldwide press coverage made it the most famous painting on Earth.
The painting is public domain; it is drawn here as a simple cartoon. Generic cartoon people, no likenesses.

Physics (physics.py + local): the painting yanked off the wall on a ballistic arc with spin, a pendulum clock and a
swinging interrogation lamp (real pendulum period), a CLOSED sign on a damped spring, a trunk lid on a spring,
newspapers falling with air drag + flutter, a FOLLOW pill that drops and bounces, dust on impacts, confetti.
Usage: python make_mona.py final.mp4 [scene,...]   stills: STILLS_DIR=dir python make_mona.py x 0,1 1.0,2.0
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
sys.argv = [sys.argv[0], "base_mona.mp4"]
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

GOLD, RED, SKY, GREEN = (255, 200, 60), (235, 60, 60), (120, 190, 255), (90, 210, 120)
make_ketchup.SPLAT_COLOR = (250, 195, 50)
base.HOOK_SKIP = 0.0
base.CRF = 16
CUE = {}
VOICE_DIR = "../mona"
TAIL = 1.4

PER = dict(skin=(230, 190, 155), hair="neat", hair_col=(40, 30, 25), coat=(245, 245, 238), pants=(55, 55, 65), mustache=True, nose="long")
GUARD = dict(skin=(235, 200, 170), hair="grey", hair_col=(170, 170, 175), coat=(40, 50, 95), trim=(220, 180, 80), pants=(40, 45, 70),
             mustache=True, nose="long")
DETECT = dict(skin=(235, 195, 165), hair="neat", hair_col=(60, 45, 35), hat="bowler", coat=(110, 85, 60), pants=(60, 50, 45), mustache=True,
              nose="long")
PAINTER = dict(skin=(215, 170, 130), hair="neat", hair_col=(20, 15, 15), coat=(40, 70, 140), pants=(50, 45, 40), nose="small")
DEALER = dict(skin=(235, 200, 170), hair="grey", hair_col=(185, 185, 190), coat=(60, 45, 40), vest=(160, 120, 60), pants=(50, 45, 40),
              glasses=True, mustache=True, nose="long")
CARAB = dict(skin=(225, 185, 150), hair="neat", hair_col=(35, 25, 20), hat="bicorne", coat=(25, 30, 55), trim=(220, 180, 80),
             pants=(25, 30, 55), mustache=True, nose="small")
VIS = [dict(skin=(235, 200, 170), hair="neat", hair_col=(70, 50, 35), hat="bowler", coat=(70, 60, 55), pants=(50, 45, 45), nose="small"),
       dict(skin=(240, 210, 185), hair="curly", hair_col=(120, 70, 40), coat=(130, 60, 90), dress=(130, 60, 90), collar=(240, 235, 230),
            pants=(60, 50, 50), nose="small"),
       dict(skin=(225, 185, 150), hair="neat", hair_col=(30, 25, 20), hat="tophat", coat=(35, 35, 45), pants=(35, 35, 45), mustache=True,
            nose="long")]
NOW = [dict(skin=(235, 195, 160), hair="neat", hair_col=(60, 40, 25), coat=(240, 120, 60), pants=(40, 50, 80), nose="small"),
       dict(skin=(200, 150, 110), hair="curly", hair_col=(30, 20, 15), coat=(90, 180, 220), pants=(50, 50, 60), nose="small"),
       dict(skin=(240, 210, 185), hair="pigtails", hair_col=(200, 150, 70), coat=(200, 90, 160), pants=(40, 40, 60), nose="small"),
       dict(skin=(220, 175, 140), hair="neat", hair_col=(20, 15, 10), coat=(90, 190, 120), pants=(40, 40, 60), nose="small")]


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


def sh(col, k):
    return tuple(max(0, min(255, int(v * k))) for v in col)


def bg(c, top, bot):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(*top), C(*bot)])))


HOLD = [(30, 40), (-30, 40)]  # both hands in front of the chest
DOWN = [(-30, 150), (30, 150)]


# ---------- props ----------

def mona(c, x, y, s, t=0.0, look=0.0, frame=True):
    """A cartoon of the (public domain) portrait: centred at (x, y), 340x460 * s with frame."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    if frame:
        blob(c, rrect(-170, -230, 170, 230, 10), (205, 160, 70), 1.35, 0.6)
        c.drawRect(skia.Rect(-148, -208, 148, 208), P(C(70, 50, 30)))
    c.save()
    c.clipRect(skia.Rect(-140, -200, 140, 200))
    c.drawPaint(P(Shader=lin((0, -200), (0, 200), [C(150, 170, 140), C(110, 120, 90), C(60, 60, 40)])))
    hp = skia.Path()  # distant hills + winding road
    hp.moveTo(-140, -40)
    hp.cubicTo(-90, -90, -40, -60, 0, -80)
    hp.cubicTo(50, -100, 100, -50, 140, -70)
    hp.lineTo(140, 200)
    hp.lineTo(-140, 200)
    hp.close()
    c.drawPath(hp, P(C(95, 110, 90)))
    c.drawArc(skia.Rect(-130, -60, -40, 0), 200, 120, False, S(C(170, 150, 110), 5))
    c.drawOval(skia.Rect(-62, -150, 62, 40), P(C(45, 32, 24)))  # hair behind
    c.drawRect(skia.Rect(-62, -60, 62, 60), P(C(45, 32, 24)))
    dress = skia.Path()
    dress.moveTo(-140, 200)
    dress.cubicTo(-130, 60, -80, 30, 0, 30)
    dress.cubicTo(80, 30, 130, 60, 140, 200)
    dress.close()
    c.drawPath(dress, P(C(40, 35, 28)))
    c.drawOval(skia.Rect(-36, 20, 36, 60), P(C(225, 190, 135)))  # neckline
    c.drawOval(skia.Rect(-44, -120, 44, 4), P(Shader=rad(-10, -70, 70, [C(240, 210, 160), C(205, 165, 110)])))  # face
    for side in (-1, 1):  # eyes look slightly to the side
        ex = side * 17 + 3 * look
        c.drawOval(skia.Rect(ex - 8, -72, ex + 8, -64), P(C(250, 240, 220)))
        c.drawCircle(ex + 3 * look + 2, -68, 4, P(C(40, 30, 20)))
    c.drawLine(-2, -64, 2, -42, S(C(170, 120, 80), 3))
    sm = skia.Path()  # the famous half smile
    sm.moveTo(-14, -30)
    sm.cubicTo(-6, -24, 6, -24, 16, -32)
    c.drawPath(sm, S(C(140, 70, 60), 3))
    c.drawOval(skia.Rect(-70, 140, 30, 180), P(C(225, 190, 135)))  # folded hands
    c.drawOval(skia.Rect(-10, 132, 80, 172), P(C(232, 198, 142)))
    c.drawPaint(P(C(120, 90, 30, 40)))  # old varnish tint
    c.restore()
    c.restore()


def hooks(c, x, y, s=1.0):
    """The four iron pegs left on the wall."""
    for dx, dy in ((-120, -190), (120, -190), (-120, 190), (120, 190)):
        c.drawCircle(x + dx * s, y + dy * s, 9 * s, P(C(40, 35, 30)))
        c.drawCircle(x + dx * s - 2, y + dy * s - 2, 3 * s, P(C(150, 140, 120)))
    c.drawRect(skia.Rect(x - 150 * s, y - 210 * s, x + 150 * s, y + 210 * s), P(C(0, 0, 0, 30)))  # clean patch


def gallery(c, t, wall=(120, 45, 45), floor=(110, 75, 45)):
    bg(c, sh(wall, 0.7), wall)
    for k in range(7):  # wall panels
        x = 40 + k * 160
        c.drawRect(skia.Rect(x, 880, x + 120, 1600), P(C(*sh(wall, 1.12), 70)))
    c.drawRect(skia.Rect(0, 1600, W, 1640), P(C(*sh(wall, 0.5))))
    c.drawRect(skia.Rect(0, 1640, W, H), P(Shader=lin((0, 1640), (0, H), [C(*floor), C(*sh(floor, 0.6))])))
    for k in range(12):
        c.drawLine(k * 100 - 200, H, k * 100 + 60, 1640, S(C(*sh(floor, 0.75)), 3))


def pendulum(T_len, t, amp=18):
    """Angle (deg) of a small-angle pendulum of the given period: theta(t) = A cos(2 pi t / T)."""
    return amp * math.cos(2 * math.pi * t / T_len)


def clock(c, x, y, t, speed=1.0):
    blob(c, rrect(x - 70, y - 120, x + 70, y + 260, 20), (110, 70, 40), 1.25, 0.7)
    c.drawCircle(x, y - 30, 58, P(C(245, 240, 225)))
    c.drawCircle(x, y - 30, 58, S(C(60, 40, 20), 5))
    for k in range(12):
        a = k / 12 * 2 * math.pi
        c.drawLine(x + math.cos(a) * 46, y - 30 + math.sin(a) * 46, x + math.cos(a) * 54, y - 30 + math.sin(a) * 54, S(C(60, 40, 20), 3))
    hm = t * speed
    for ln, rate, w in ((30, 1 / 12, 6), (44, 1.0, 4)):
        a = math.radians(hm * 360 * rate * 0.2 - 90)
        c.drawLine(x, y - 30, x + math.cos(a) * ln, y - 30 + math.sin(a) * ln, S(C(30, 25, 20), w))
    th = math.radians(pendulum(1.4, t))  # 1.4 s period pendulum
    c.save()
    c.clipRect(skia.Rect(x - 60, y + 40, x + 60, y + 250))
    px, py = x + math.sin(th) * 150, y + 50 + math.cos(th) * 150
    c.drawLine(x, y + 50, px, py, S(C(200, 160, 60), 5))
    c.drawCircle(px, py, 24, P(Shader=rad(px - 8, py - 8, 30, [C(255, 220, 120), C(200, 150, 40)])))
    c.restore()


def thought(c, x, y, r, a=255):
    for k, (dx, dy, rr) in enumerate(((-r * 0.9, r * 1.2, r * 0.16), (-r * 0.6, r * 0.95, r * 0.24))):
        c.drawCircle(x + dx, y + dy, rr, P(C(250, 250, 255, a)))
    blob(c, oval(x, y, r * 1.25, r * 0.85), (250, 250, 255), 1.03, 0.92)


def camera(c, x, y, s, flash=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    for a in (-18, 0, 18):  # tripod
        c.drawLine(0, 40, math.sin(math.radians(a)) * 260, 40 + math.cos(math.radians(a)) * 260, S(C(80, 60, 40), 8))
    blob(c, rrect(-70, -50, 70, 50, 10), (40, 35, 35), 1.4, 0.6)
    blob(c, rrect(-50, -70, -10, -50, 6), (60, 55, 55))
    c.drawCircle(50, 0, 34, P(C(20, 20, 25)))
    c.drawCircle(50, 0, 22, P(C(70, 90, 120)))
    c.restore()
    if flash > 0:
        glow(c, x - 30 * s, y - 70 * s, 320, (255, 255, 230), int(250 * flash))


def newspaper(c, x, y, rot, flip, s=1.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s * (0.35 + 0.65 * abs(flip)))
    blob(c, rrect(-120, -150, 120, 150, 4), (240, 235, 220), 1.03, 0.85)
    c.drawRect(skia.Rect(-105, -135, 105, -100), P(C(30, 30, 30)))
    f = skia.Font(FB, 40)
    w = f.measureText("STOLEN!")
    c.drawString("STOLEN!", -w / 2, -40, f, P(C(170, 30, 30)))
    mona(c, -45, 55, 0.2, frame=False)
    for k in range(5):
        c.drawLine(10, 0 + k * 22, 100, 0 + k * 22, S(C(120, 120, 120), 5))
    c.restore()


def trunk(c, x, y, t, open_k):
    # lid hinged at the back edge: rises behind the box (perspective-flattened)
    lh = 70 + 190 * open_k
    blob(c, rrect(x - 205, y - 150 - lh, x + 205, y - 140, 16), (135, 92, 52) if open_k < 0.3 else (95, 62, 35), 1.25, 0.65)
    if open_k > 0.02:  # the painting rises out of it, glowing
        glow(c, x, y - 200, 260, (255, 230, 150), int(190 * open_k))
        c.save()
        c.clipRect(skia.Rect(x - 200, y - 500, x + 200, y - 120))
        mona(c, x, y - 140 - 150 * open_k, 0.42)
        c.restore()
    blob(c, rrect(x - 200, y - 150, x + 200, y, 16), (120, 80, 45), 1.25, 0.65)
    for dx in (-140, 140):
        c.drawRect(skia.Rect(x + dx - 12, y - 150, x + dx + 12, y), P(C(70, 50, 30)))
    if open_k < 0.3:
        c.drawRect(skia.Rect(x - 20, y - 175, x + 20, y - 140), P(C(220, 180, 70)))


# ---------- scenes ----------

def art_hook(c, t):
    gallery(c, t)
    st = CUE["stole"]
    # visitors stroll past without even looking (nobody knew her)
    for i, who in enumerate(VIS):
        x = -200 + ((t * 150 + i * 430) % 1500)
        stand(c, who, x, 1880, 1.0, t, walk=x / 40, eyes="open" if t < st else "wide", mouth="smile" if t < st else "O",
              brows="flat" if t < st else "up", look=(1, 0) if t < st else (0, -0.6), hands=DOWN)
    if t < st:
        mona(c, 540, 1180, 0.85, t, look=math.sin(t * 0.7))
        glow(c, 540, 1180, 300, (255, 220, 160), 50)
    else:  # yanked off the wall: ballistic arc + spin, out of frame
        hooks(c, 540, 1180, 0.85)
        k = t - st
        px = 540 - 1500 * k
        py = 1180 - 900 * k + 0.5 * PH.G * k * k
        if px > -400 and py < 2300:
            c.save()
            c.translate(px, py)
            c.rotate(-540 * k)
            mona(c, 0, 0, 0.85 * (1 - 0.3 * min(1, k)))
            c.restore()
        PH.dust(c, t, st, 540, 1180, (230, 200, 160))
    nv = CUE["never"]
    if t > nv:  # "never heard of her": question marks pop over the visitors
        for i in range(3):
            q = pop_in(t, nv + i * 0.15)
            c.drawString("?", 230 + i * 300, 1400 + 15 * math.sin(t * 4 + i), skia.Font(FB, 120 * q), P(C(255, 220, 120)))


def art_closet(c, t):
    bg(c, (8, 10, 25), (25, 25, 45))
    c.drawRect(skia.Rect(0, 1640, W, H), P(C(40, 35, 45)))
    blob(c, rrect(700, 880, 960, 1360, 120), (40, 50, 80), 1.1, 0.8)  # tall window, moonlight
    c.drawRect(skia.Rect(720, 900, 940, 1340), P(C(120, 140, 200, 120)))
    c.drawLine(830, 900, 830, 1340, S(C(30, 35, 55), 8))
    c.drawLine(720, 1120, 940, 1120, S(C(30, 35, 55), 8))
    mp = skia.Path()  # moon beam on the floor
    mp.moveTo(720, 1340)
    mp.lineTo(940, 1340)
    mp.lineTo(1000, 1900)
    mp.lineTo(560, 1900)
    mp.close()
    c.drawPath(mp, P(C(150, 170, 230, 40)))
    # closet door, ajar, with eyes in the dark
    blob(c, rrect(120, 1150, 420, 1650, 10), (70, 50, 35), 1.2, 0.7)
    c.drawRect(skia.Rect(250, 1170, 300, 1640), P(C(5, 5, 10)))
    if t > CUE["closet"] - 0.2:
        bl = ((t % 2.3) < 0.12)
        for dx in (262, 288):
            c.drawOval(skia.Rect(dx - 8, 1330 - (1 if bl else 8), dx + 8, 1330 + (1 if bl else 8)), P(C(250, 250, 240)))
    clock(c, 560, 1260, t, speed=40)
    # a night guard with a lantern walks past the closet
    gx = -150 + 220 * t
    if gx < 1250:
        stand(c, GUARD, gx, 1880, 1.0, t, walk=gx / 40, eyes="squint", mouth="smile", brows="flat", look=(1, 0), hands=[(-30, 150), (80, 40)])
        glow(c, gx + 120, 1640, 200, (255, 210, 120), 160)


def art_lift(c, t):
    gallery(c, t, (125, 50, 45))
    lf, hd, wk = CUE["lifted"], CUE["hid"], CUE["walked"]
    # he walks up to the wall, lifts it, hides it, walks out
    if t < lf:
        x = -150 + (420 + 150) * ease(min(1, t / max(0.5, lf - 0.2)))
    elif t < wk:
        x = 420
    else:
        x = 420 + 900 * ((t - wk) / 1.8) ** 1.3
    walking = t < lf - 0.2 or t > wk
    lift = ease((t - lf) / 0.8)
    hidden = t > hd
    holding = lf < t < hd
    stand(c, PER, x, 1880, 1.15, t, walk=x / 40 if walking else None, eyes="squint" if not hidden else "open",
          mouth="smile" if not hidden else "grin", brows="angry" if not hidden else "up", look=(1, -0.4) if t < lf + 0.5 else (0.6, 0),
          hands=HOLD if holding or hidden else DOWN)
    if t < lf:
        mona(c, 700, 1180, 0.75)
    else:
        hooks(c, 700, 1180, 0.75)
        if holding:  # carried from the wall into his hands
            hx, hy = x + 0, 1880 - 120 * 1.15
            ky, kx = ease(min(1.0, lift * 1.6)), ease(max(0.0, (lift - 0.45) / 0.55))
            mona(c, 700 + (hx - 700) * kx, 1180 + (hy - 1180) * ky, 0.75 - 0.37 * lift)
            PH.dust(c, t, lf, 700, 1180, (230, 200, 160))
        if hidden:  # a suspicious rectangle under the white work coat
            k = pop_in(t, hd, 0.3)
            s = 1.15
            c.save()
            c.translate(x, 1880 - 170 * s)
            c.scale(1, k)
            blob(c, rrect(-95 * s, -80 * s, 95 * s, 80 * s, 14), (246, 246, 240), 1.08, 0.86)
            c.drawLine(-70 * s, 70 * s, 70 * s, 70 * s, S(C(205, 160, 70), 6))
            c.restore()
    if t > wk:
        sparkle(c, x + 130, 1500 + 10 * math.sin(t * 9), 14, 220)


def art_unnoticed(c, t):
    gallery(c, t, (110, 45, 50))
    hooks(c, 540, 1150, 0.75)
    clock(c, 900, 1150, t, speed=900)  # hours fly by
    # sleepy guard on a chair
    blob(c, rrect(170, 1700, 400, 1740, 8), (90, 60, 35))
    for dx in (185, 385):
        c.drawLine(dx, 1740, dx, 1880, S(C(90, 60, 35), 10))
    stand(c, GUARD, 290, 1820, 1.0, t, eyes="closed", mouth="O", brows="flat", look=(0, 0.3), hands=DOWN, tilt=8 + 3 * math.sin(t * 1.5))
    for i in range(3):  # Zzz
        k = (t * 0.6 + i / 3) % 1
        c.drawString("z", 400 + 80 * k, 1430 - 200 * k, skia.Font(FB, 40 + 40 * k), P(C(220, 230, 255, int(255 * (1 - k)))))
    ph = CUE["photo"]
    if t > ph - 0.6:  # "it's with the photographers": thought bubble with a camera that flashes
        a = pop_in(t, ph - 0.6)
        c.save()
        c.translate(560, 1350)
        c.scale(a, a)
        thought(c, 0, 0, 170)
        camera(c, 0, -30, 0.7, max(0.0, 1 - abs(t - ph - 0.3) / 0.25))
        c.restore()


def art_closed(c, t):
    ro = CUE["reopened"]
    if t < ro - 0.15:  # palace front, doors shut, CLOSED sign swinging on a spring
        bg(c, (20, 25, 45), (60, 70, 100))
        blob(c, rrect(60, 1050, 1020, 1700, 10), (200, 190, 165), 1.1, 0.75)
        tri = skia.Path()
        tri.moveTo(40, 1060)
        tri.lineTo(540, 880)
        tri.lineTo(1040, 1060)
        tri.close()
        blob(c, tri, (215, 205, 180), 1.1, 0.75)
        for k in range(6):
            x = 130 + k * 165
            blob(c, rrect(x - 26, 1090, x + 26, 1690, 8), (230, 222, 200), 1.12, 0.78)
        blob(c, rrect(420, 1350, 660, 1700, 100), (70, 45, 30), 1.2, 0.7)
        c.drawRect(skia.Rect(0, 1700, W, H), P(C(120, 110, 95)))
        cl = CUE["close"]
        k = pop_in(t, cl - 0.25)
        if k > 0:
            sw = PH.spring_v(t, cl, 22, 1.2, 1.8)
            c.save()
            c.translate(540, 1300)
            c.rotate(sw)
            c.scale(k, k)
            c.drawLine(-80, -60, 0, -130, S(C(60, 50, 40), 4))
            c.drawLine(80, -60, 0, -130, S(C(60, 50, 40), 4))
            blob(c, rrect(-190, -60, 190, 70, 14), (230, 50, 50), 1.2, 0.7)
            f = skia.Font(FB, 84)
            w = f.measureText("CLOSED")
            c.drawString("CLOSED", -w / 2, 34, f, P(C(255, 255, 255)))
            c.restore()
        PH.dust(c, t, cl, 540, 1700)
        return
    gallery(c, t, (120, 45, 45))
    hooks(c, 300, 1150, 0.75)
    c.drawLine(80, 1560, 1000, 1560, S(C(170, 30, 40), 10))  # velvet rope
    for k in range(4):
        c.drawLine(80 + k * 300, 1560, 80 + k * 300, 1680, S(C(200, 170, 70), 10))
    # the queue shuffles forward to stare at the empty wall
    k2 = t - ro
    for i in range(6):
        x = 470 + i * 170 - 60 * min(1, k2 / 2) + 6 * math.sin(t * 3 + i)
        stand(c, VIS[i % 3], x, 1880 + (i % 2) * 20, 0.85, t, eyes="wide", mouth="O", brows="up", look=(-1, -0.6), hands=DOWN,
              walk=x / 40 if k2 < 2 else None)
    for i in range(5):  # camera flashes from the crowd
        fl = (t * 1.7 + i * 0.37) % 1
        if fl < 0.08:
            glow(c, 500 + i * 120, 1520, 100, (255, 255, 230), 170)


def art_picasso(c, t):
    bg(c, (15, 15, 20), (40, 38, 45))
    c.drawRect(skia.Rect(0, 1700, W, H), P(C(55, 50, 55)))
    blob(c, rrect(260, 1560, 820, 1610, 10), (100, 70, 45), 1.2, 0.7)  # table
    for dx in (290, 790):
        c.drawLine(dx, 1610, dx, 1760, S(C(100, 70, 45), 12))
    pq = CUE["picasso"]
    stand(c, DETECT, 240, 1880, 1.15, t, eyes="squint", mouth="frown", brows="angry", look=(1, -0.1), hands=[(-30, 150), (130, 0)])
    # magnifying glass in his hand
    mx, my = 240 + 1.15 * (60 + 130), 1880 - 1.15 * 235 - 20
    c.drawLine(mx, my, mx + 50, my - 70, S(C(90, 60, 30), 12))
    c.drawCircle(mx + 70, my - 100, 42, P(C(200, 230, 255, 90)))
    c.drawCircle(mx + 70, my - 100, 42, S(C(60, 60, 60), 8))
    sweat = t > pq - 0.4
    stand(c, PAINTER, 820, 1880, 1.1, t, eyes="wide" if sweat else "open", mouth="O" if sweat else "smile", brows="sad" if sweat else "up",
          look=(-1, 0), hands=[(-30, 150), (40, 150)], tilt=-5 if sweat else 0)
    blob(c, oval(980, 1690, 70, 46), (220, 190, 140), 1.2, 0.75)  # painter's palette
    for k, col in enumerate(((230, 50, 50), (60, 120, 230), (250, 210, 60), (80, 190, 90))):
        c.drawCircle(950 + k * 22, 1680 + (k % 2) * 16, 9, P(C(*col)))
    if sweat:
        for i in range(3):
            k = ((t - pq) * 1.3 + i / 3) % 1
            tx = 820 + 90 + 20 * i
            ty = head_c(1880, 1.1) - 60 + 300 * k * k
            c.drawCircle(tx, ty, 9, P(C(160, 210, 255, int(255 * (1 - k)))))
    # interrogation lamp: a real pendulum (period 1.8 s), light cone follows it
    th = math.radians(pendulum(1.8, t, 14 + 6 * math.exp(-t * 0.3)))
    lx, ly = 540 + math.sin(th) * 420, 880 + math.cos(th) * 420
    c.drawLine(540, 880, lx, ly, S(C(30, 30, 30), 5))
    cone = skia.Path()
    cone.moveTo(lx - 40, ly + 30)
    cone.lineTo(lx + 40, ly + 30)
    cone.lineTo(lx + 420 + math.sin(th) * 500, 1900)
    cone.lineTo(lx - 420 + math.sin(th) * 500, 1900)
    cone.close()
    c.drawPath(cone, P(Shader=lin((0, ly), (0, 1900), [C(255, 240, 180, 90), C(255, 240, 180, 0)])))
    blob(c, oval(lx, ly + 10, 70, 36), (60, 70, 60), 1.3, 0.6)
    glow(c, lx, ly + 34, 90, (255, 240, 180), 200)


def art_follow(c, t):
    bg(c, (25, 15, 45), (70, 30, 90))
    for k in range(14):
        a = k / 14 * 2 * math.pi + t * 0.5
        p = skia.Path()
        p.moveTo(540, 1350)
        p.lineTo(540 + math.cos(a) * 1500, 1350 + math.sin(a) * 1500)
        p.lineTo(540 + math.cos(a + 0.13) * 1500, 1350 + math.sin(a + 0.13) * 1500)
        p.close()
        c.drawPath(p, P(C(255, 220, 255, 14)))
    # a calendar whose pages keep tearing off (one fact a day)
    blob(c, rrect(380, 1000, 700, 1300, 16), (250, 248, 240), 1.03, 0.88)
    c.drawRect(skia.Rect(380, 1000, 700, 1070), P(C(220, 60, 60)))
    day = 2 + int(t / 0.5)
    f = skia.Font(FB, 140)
    w = f.measureText(str(day))
    c.drawString(str(day), 540 - w / 2, 1240, f, P(C(50, 40, 40)))
    k = (t % 0.5) / 0.5
    c.save()
    c.translate(540 + 300 * k, 1185 - 200 * k + 600 * k * k)
    c.rotate(120 * k)
    c.scale(1, 1 - 0.6 * k)
    blob(c, rrect(-160, -115, 160, 115, 16), (250, 248, 240), 1.03, 0.88)
    w0 = f.measureText(str(day - 1))
    c.drawString(str(day - 1), -w0 / 2, 55, f, P(C(50, 40, 40)))
    c.restore()
    # FOLLOW pill drops in and bounces (ball_path for the y motion)
    _, py, _, sq, hit = PH.ball_path(t, 540, 1380, 0, 0, 1700, 70, e=0.45, mu=1.0)
    c.save()
    c.translate(540, py)
    c.scale(1 + sq * 0.5, 1 - sq * 0.5)
    blob(c, rrect(-260, -70, 260, 70, 70), (235, 35, 45), 1.25, 0.7)
    f2 = skia.Font(FB, 72)
    w2 = f2.measureText("+ FOLLOW")
    c.drawString("+ FOLLOW", -w2 / 2, 26, f2, P(C(255, 255, 255)))
    c.restore()
    PH.dust(c, t, hit, 540, 1700, (230, 190, 255), 5)


def art_trunk(c, t):
    bg(c, (35, 28, 30), (75, 55, 50))
    roof = skia.Path()  # slanted attic ceiling
    roof.moveTo(0, 880)
    roof.lineTo(W, 1150)
    roof.lineTo(W, 880)
    roof.close()
    c.drawPath(roof, P(C(25, 20, 22)))
    blob(c, rrect(120, 1000, 330, 1200, 10), (60, 80, 120), 1.1, 0.8)  # tiny window
    c.drawLine(225, 1000, 225, 1200, S(C(40, 30, 25), 8))
    c.drawRect(skia.Rect(0, 1700, W, H), P(C(90, 65, 45)))
    blob(c, rrect(700, 1560, 1060, 1700, 20), (150, 110, 80), 1.1, 0.8)  # little bed
    blob(c, rrect(720, 1520, 860, 1580, 20), (235, 230, 220), 1.05, 0.85)
    tk, yr = CUE["trunk"], CUE["years"]
    op = min(1.0, max(0.0, ease((t - tk + 0.3) / 0.5) + 0.12 * PH.spring_v(t, tk + 0.2, 1, 2.5, 4)))
    trunk(c, 520, 1830, t, op)
    stand(c, PER, 200, 1880, 1.0, t, eyes="squint", mouth="grin", brows="angry", look=(1, 0.3), hands=[(-30, 150), (110, 40)])
    # wall calendar: years flip 1911 -> 1913, torn sheets fall with drag
    blob(c, rrect(800, 1020, 1000, 1240, 10), (245, 240, 230), 1.03, 0.88)
    c.drawRect(skia.Rect(800, 1020, 1000, 1070), P(C(200, 50, 50)))
    yv = 1911 + min(2, int(max(0.0, t - (yr - 1.4)) / 0.7))
    f = skia.Font(FB, 64)
    w = f.measureText(str(yv))
    c.drawString(str(yv), 900 - w / 2, 1180, f, P(C(50, 40, 40)))
    for i in range(6):
        k = t - (0.4 + i * 0.55)
        if 0 < k < 2.0:
            d = 2.4
            px = 900 - 260 * (1 - math.exp(-d * k)) + 30 * math.sin(k * 6 + i)
            py = 1240 + 1000 / d * (k - (1 - math.exp(-d * k)) / d)
            c.save()
            c.translate(px, py)
            c.rotate(50 * math.sin(k * 5 + i))
            c.scale(1, 0.4 + 0.6 * abs(math.cos(k * 4 + i)))
            blob(c, rrect(-50, -55, 50, 55, 6), (245, 240, 230), 1.03, 0.88)
            c.restore()


def art_florence(c, t):
    bg(c, (45, 35, 25), (100, 75, 50))
    for k in range(3):  # frames on the shop wall
        x = 200 + k * 340
        blob(c, rrect(x - 90, 950, x + 90, 1170, 8), (190, 150, 70), 1.3, 0.65)
        c.drawRect(skia.Rect(x - 72, 968, x + 72, 1152), P(C(*[(90, 120, 150), (150, 110, 80), (110, 140, 90)][k])))
    c.drawRect(skia.Rect(0, 1700, W, H), P(C(80, 55, 35)))
    sl, ar = CUE["sell"], CUE["arrested"]
    stand(c, DEALER, 910, 1880, 1.1, t, eyes="wide" if t > sl + 0.4 else "open", mouth="O" if t > sl + 0.4 else "smile", brows="up",
          look=(-1, -0.1), hands=[(-80, 40), (30, 150)])
    arrested = t > ar - 0.2
    for i in range(2):  # police burst in from the door on the left (back one smaller = further away)
        if not arrested:
            break
        k = min(1.0, (t - ar + 0.2) / 0.7)
        x = -200 + (430 - i * 120) * ease(k)
        stand(c, CARAB, x, 1880 - (1 - i) * 30, 0.9 + 0.1 * i, t, walk=x / 40 if k < 1 else None, eyes="squint", mouth="frown",
              brows="angry", look=(1, 0), hands=[(30, 150), (120, -40)])
    stand(c, PER, 480, 1880, 1.1, t, eyes="wide" if arrested else "squint", mouth="O" if arrested else "grin",
          brows="sad" if arrested else "angry", look=(1, 0) if not arrested else (1, -0.5), hands=HOLD if not arrested else [(-90, -120), (90, -120)])
    if not arrested:
        k = pop_in(t, sl - 0.3)
        if k > 0:
            mona(c, 690, 1640, 0.38 * k)
    else:
        mona(c, 690, 1690, 0.38)  # left on the counter
        PH.dust(c, t, ar, 150, 1880)


def art_news(c, t):
    bg(c, (20, 18, 30), (55, 45, 60))
    fm = CUE["famous"]
    if t > fm - 0.3:  # the painting under spotlights with endless camera flashes
        k = pop_in(t, fm - 0.3, 0.5)
        glow(c, 540, 1300, 520, (255, 220, 150), int(120 * k))
        for side in (-1, 1):
            cone = skia.Path()
            cone.moveTo(540 + side * 500, 880)
            cone.lineTo(540 + side * 420, 880)
            cone.lineTo(540 - side * 120, 1600)
            cone.lineTo(540 + side * 160, 1600)
            cone.close()
            c.drawPath(cone, P(C(255, 240, 200, int(40 * k))))
        mona(c, 540, 1300, 0.95 * k, t, look=math.sin(t))
        PH.confetti(c, t, fm, 540, 1000, 80, 11, 1.1)
        for i in range(8):
            fl = (t * 2.3 + i * 0.29) % 1
            if fl < 0.07:
                r = random.Random(i)
                glow(c, r.uniform(100, 980), r.uniform(1600, 1850), 150, (255, 255, 230), 220)
    # newspapers rain down: drag + flutter + spin, they land and pile up
    for i in range(14):
        t0 = 0.1 + i * 0.22
        k = t - t0
        if k <= 0:
            continue
        r = random.Random(i + 3)
        x0 = r.uniform(120, 960)
        d = r.uniform(1.6, 2.4)
        py = 700 + 1500 / d * (k - (1 - math.exp(-d * k)) / d)
        floor = 1780 + r.uniform(-60, 60)
        landed = py >= floor
        py = min(py, floor)
        px = x0 + 50 * math.sin(k * r.uniform(3, 5) + i) * (0 if landed else 1)
        rot = r.uniform(-30, 30) + (0 if landed else 90 * math.sin(k * 3 + i))
        flip = 1.0 if landed else math.cos(k * r.uniform(4, 7) + i)
        a = 1.0 if t < fm - 0.3 else max(0.0, 1 - (t - fm + 0.3) / 0.4)
        if a > 0:
            c.saveLayerAlpha(None, int(255 * a))
            newspaper(c, px, py, rot, flip, 0.8)
            c.restore()


def art_vote(c, t):
    gallery(c, t, (60, 60, 75), (90, 85, 95))
    blob(c, rrect(330, 960, 750, 1450, 20), (200, 220, 240), 1.05, 0.9)  # glass case
    mona(c, 540, 1205, 0.75, t, look=math.sin(t * 0.8))
    c.drawRect(skia.Rect(330, 960, 750, 1450), P(C(200, 230, 255, 40)))
    c.drawLine(380, 1000, 470, 1100, S(C(255, 255, 255, 90), 6))
    for i, who in enumerate(NOW):  # today's queue: phones up
        x = 140 + i * 265
        stand(c, who, x, 1890, 0.85, t, eyes="open", mouth="smile", brows="up", look=(0.3 if x < 540 else -0.3, -0.7), hands=[(-60, -200), (30, 150)])
        hx, hy = x + 0.85 * (-120), 1890 - 0.85 * 435
        blob(c, rrect(hx - 22, hy - 38, hx + 22, hy + 38, 8), (30, 30, 35), 1.2, 0.7)
        if (t * 1.3 + i * 0.4) % 1 < 0.08:
            glow(c, hx, hy, 120, (255, 255, 230), 220)
    cm = CUE["comments"]
    for i in range(10):  # YES / NO bubbles fly up with drag
        t0 = cm - 0.5 + i * 0.13
        k = t - t0
        if k <= 0:
            continue
        r = random.Random(i)
        x = 540 + r.uniform(-400, 400) + 30 * math.sin(k * 4 + i)
        y = 1650 - 800 * (1 - math.exp(-2.2 * k))
        a = int(255 * max(0, min(1, (2.0 - k) / 0.5)))
        if a <= 0:
            continue
        lab, col = ("YES!", GREEN) if i % 3 else ("NO WAY", RED)
        f = skia.Font(FB, 38)
        w = f.measureText(lab)
        c.saveLayerAlpha(None, a)
        blob(c, rrect(x - w / 2 - 22, y - 38, x + w / 2 + 22, y + 38, 20), (250, 250, 255), 1.03, 0.9)
        c.drawString(lab, x - w / 2, y + 13, f, P(C(*col)))
        c.restore()


def art_cta(c, t):
    U.T_EIGHT = -10
    U.background(c, t, 0)
    U.spotlight(c, t, 0)
    c.drawPaint(P(C(10, 6, 14, 120)))
    draw_cta2(c, t, CUE["like"], CUE["sub"])


ART = [art_hook, art_closet, art_lift, art_unnoticed, art_closed, art_picasso, art_follow, art_trunk, art_florence, art_news, art_vote, art_cta]
PUSH = [(1.0, 1.05), (1.0, 1.06), (1.0, 1.05), (1.0, 1.06), (1.0, 1.05), (1.0, 1.06), (1.0, 1.04), (1.0, 1.06), (1.0, 1.05), (1.0, 1.07), (1.0, 1.04), (1.0, 1.0)]
ANCHOR = [(540, 1300), (540, 1400), (540, 1450), (540, 1400), (540, 1400), (540, 1500), (540, 1300), (540, 1500), (540, 1500), (540, 1300), (540, 1300), (540, 1080)]


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
    line(img, "The Mona Lisa", 230, F_MID)
    line(img, "wasn't famous... until", 330, F_MID)
    slam(img, "STOLEN!", 430, t, CUE["stole"] - 0.1, GOLD, 170)
    text_block(img, "Nobody had heard of her", font(FONT_B, 60), 650, t, (255, 235, 210), CUE["never"])
    impact(img, t, CUE["stole"] + 0.1, 18)


def tx_closet(img, t):
    tag(img, "PARIS, 1911", t, (70, 90, 160))
    title(img, t, "He hid in a closet", "...all night long", CUE["overnight"], sub_color=SKY)


def tx_lift(img, t):
    title(img, t, "Off the wall...", "...under his white coat", CUE["hid"])
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 680, "WALKED OUT", t, CUE["walked"], col=GOLD, size=100)
    impact(img, t, CUE["walked"] + 0.15, 12)


def tx_unnoticed(img, t):
    title(img, t, "Nobody noticed...", "Guards: \"it's at the photographer's\"", CUE["photo"] - 0.3, sub_color=SKY)
    slam(img, "FOR A DAY!", 640, t, CUE["day"] - 0.1, GOLD, 120)
    impact(img, t, CUE["day"] + 0.1, 12)


def tx_closed(img, t):
    title(img, t, "CLOSED for a week", "...then thousands came to see", CUE["thousands"])
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 680, "AN EMPTY WALL", t, CUE["empty"], col=RED, size=96)
    impact(img, t, CUE["empty"] + 0.15, 12)


def tx_picasso(img, t):
    title(img, t, "Police questioned...", y=260)
    slam(img, "PICASSO?!", 430, t, CUE["picasso"] - 0.1, GOLD, 150)
    impact(img, t, CUE["picasso"] + 0.1, 14)


def tx_follow(img, t):
    title(img, t, "A surprising fact", "...EVERY day!", CUE["fday"], sub_color=GOLD)


def tx_trunk(img, t):
    title(img, t, "Hidden in a trunk", "...in his tiny room", CUE["trunk"] + 0.4)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 680, "2 YEARS", t, CUE["years"], col=GOLD, size=110)
    impact(img, t, CUE["years"] + 0.15, 12)


def tx_florence(img, t):
    tag(img, "FLORENCE, 1913", t, (150, 60, 40))
    title(img, t, "He tried to sell it...")
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 640, "ARRESTED!", t, CUE["arrested"], col=RED, size=110)
    impact(img, t, CUE["arrested"] + 0.15, 14)


def tx_news(img, t):
    title(img, t, "Her face was everywhere", y=260)
    slam(img, "MOST FAMOUS", 420, t, CUE["famous"] - 0.1, GOLD, 130)
    text_block(img, "painting on Earth", font(FONT_B, 64), 590, t, (255, 255, 255), CUE["earth"])
    impact(img, t, CUE["famous"] + 0.1, 16)


def tx_vote(img, t):
    slam(img, "WOULD YOU WAIT?", 300, t, CUE["wait"] - 0.15, (255, 255, 255), 94)
    text_block(img, "Tell me in the comments!", font(FONT_B, 60), 500, t, GOLD, CUE["comments"] - 0.3)
    impact(img, t, CUE["wait"] + 0.05, 12)


def tx_cta(img, t):
    pass


TEXT = [tx_hook, tx_closet, tx_lift, tx_unnoticed, tx_closed, tx_picasso, tx_follow, tx_trunk, tx_florence, tx_news, tx_vote, tx_cta]
base.TRANSITION = splat

if __name__ == "__main__":
    voice = f"{VOICE_DIR}/voice.mp3"
    tl = Timeline(voice)
    firsts = ["nine|nineteen", "next morning", "nobody", "close|closed", "place|police", "follow", "meanwhile", "tried",
              "newspapers", "so", "learn"]
    after, starts = 7.0, [0.0]
    for ph in firsts:
        w = tl.find(ph, after)
        before = [p for p in tl.pauses if p[1] <= w + 0.2 and p[0] >= after - 1.0]
        cut = max((before[-1][0] + before[-1][1]) / 2, before[-1][1] - 0.25) if before else w - 0.15
        starts.append(round(cut, 3))
        after = w + 0.3
    total = round(tl.length + TAIL, 2)
    durs = [round(b - a, 2) for a, b in zip(starts, starts[1:] + [total])]
    S0 = starts
    f = lambda phrase, sc, lead=0.1: round(tl.find(phrase, S0[sc]) - S0[sc] - lead, 2)
    CUE.update(d=durs, S=S0,
               stole=f("stole", 0, 0.0), never=f("never", 0),
               closet=f("closet", 1), overnight=f("overnight", 1),
               lifted=f("lifted", 2), hid=f("hidden|hid", 2), walked=f("walked", 2, 0.15),
               day=f("day", 3, 0.0), photo=f("photographed", 3),
               close=f("close", 4, 0.0), reopened=f("reopened", 4), thousands=f("thousands", 4), empty=f("empty", 4, 0.15),
               picasso=f("picasso", 5, 0.0),
               fday=f("every", 6),
               trunk=f("trunk", 7), years=f("years", 7, 0.15),
               sell=f("sell", 8), arrested=f("arrested", 8, 0.15),
               famous=f("famous", 9, 0.0), earth=f("earth", 9),
               wait=f("weight|wait", 10, 0.0), comments=f("comments", 10))
    CUE["like"] = round(tl.find("like", S0[11]) - S0[11] - 0.05, 2)
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
                img.convert("RGB").save(f"{out}/mona_{i}_{tt}.png")
        sys.exit()
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), scene(i, TEXT[i])) for i, dd in enumerate(durs)]
    if ONLY:
        base.SCENES[:] = [s for i, s in enumerate(base.SCENES) if i in ONLY]
    ST, C_ = S0, CUE
    ev = [("whoosh", s) for s in ST[1:]]
    ev += [("whoosh", C_["stole"]), ("thud", C_["stole"] + 0.05), ("pop", C_["never"] + 0.0), ("pop", C_["never"] + 0.15), ("pop", C_["never"] + 0.3),
           ("ding", ST[1] + C_["closet"]),
           ("thud", ST[2] + C_["lifted"]), ("pop", ST[2] + C_["hid"]), ("thud", ST[2] + C_["walked"] + 0.15),
           ("thud", ST[3] + C_["day"]), ("click", ST[3] + C_["photo"] + 0.3), ("ding", ST[3] + C_["photo"] + 0.3),
           ("thud", ST[4] + C_["close"]), ("whoosh", ST[4] + C_["reopened"] - 0.15), ("thud", ST[4] + C_["empty"] + 0.15),
           ("thud", ST[5] + C_["picasso"]), ("ding", ST[5] + C_["picasso"] + 0.05),
           ("pop", ST[6] + 0.0), ("click", ST[6] + C_["fday"]),
           ("pop", ST[7] + C_["trunk"]), ("ding", ST[7] + C_["trunk"] + 0.2), ("thud", ST[7] + C_["years"] + 0.15),
           ("pop", ST[8] + C_["sell"] - 0.3), ("thud", ST[8] + C_["arrested"] + 0.15), ("whoosh", ST[8] + C_["arrested"] - 0.2),
           ("thud", ST[9] + C_["famous"]), ("ding", ST[9] + C_["famous"] + 0.05),
           ("thud", ST[10] + C_["wait"]),
           ("click", ST[11] + C_["like"]), ("ding", ST[11] + C_["like"] + 0.03),
           ("click", ST[11] + C_["sub"]), ("ding", ST[11] + C_["sub"] + 0.35)]
    # FOLLOW pill bounces: real impact times from the same simulation
    last = -1
    for k in range(int(durs[6] * 60)):
        *_, hit = PH.ball_path(k / 60, 540, 1380, 0, 0, 1700, 70, e=0.45, mu=1.0)
        if hit > last + 0.05 and hit >= 0:
            ev.append(("pop", ST[6] + hit))
            last = hit
    ev += [("click", ST[9] + 0.1 + i * 0.22 + 0.9) for i in range(0, 14, 2)]  # newspapers landing
    ev += [("pop", ST[10] + C_["comments"] - 0.5 + i * 0.13) for i in range(10)]  # comment bubbles
    ev += [("click", ST[4] + C_["reopened"] + 0.3 + i * 0.6) for i in range(4)]  # camera flashes
    ev = [(k, round(v, 3)) for k, v in ev if 0 <= v < total]
    audio.music("music.wav", total, bpm=104, seed=53)
    audio.sfx("sfx.wav", total, ev)
    base.OUT = "base_mona.mp4"
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_mona.mp4", voice, "music.wav", "sfx.wav", OUTFILE)
    print("wrote", OUTFILE)
