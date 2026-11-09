"""YouTube Short: "Airplane Windows Are Round Because of a TERRIBLE Mistake" (Skia toon + cam3d 3D camera + physics).

Facts (well documented): the de Havilland Comet (UK, first flight 1949, first jet airliner service 1952) had square-ish
windows. In 1954 two Comets broke up in flight months apart (January near Elba, April near Naples); the fleet was
grounded. At Farnborough an entire fuselage was put in a water tank and pressurised again and again to simulate
flights; it failed with a crack at the corner of a window/cut-out (metal fatigue). Sharp corners concentrate stress;
rounded corners spread it, which is why airliner windows have rounded corners.
Generic cartoon plane (no airline livery/logo) and generic people. No crash victims shown.

New: `cam3d.py` — the toon characters and props live in a real 3D set (perspective, painter's sort, fog, depth blur),
the camera orbits / dollies / cranes / rolls, impact shakes. Physics: oxygen masks on springs, take-off with
acceleration + rotation, hats thrown with gravity + spin, a jet breaking into two rigid bodies with debris and drag,
sloshing tank water, pump piston, cracks that grow, stress flow lines, spring vote bubbles.
Usage: python make_window.py final.mp4 [scene,...]   stills: STILLS_DIR=dir python make_window.py x 0,1 1.0,2.0
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
sys.argv = [sys.argv[0], "base_window.mp4"]
sys.path.insert(0, "..")

import audio  # noqa: E402
import make_ketchup  # noqa: E402
import make_short as base  # noqa: E402
import ultimate as U  # noqa: E402
import physics as PH  # noqa: E402
from cam3d import Cam, World, rounded_rect_pts, shake  # noqa: E402
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
VOICE_DIR = "../window"
TAIL = 1.4

PAX = [dict(skin=(235, 195, 160), hair="neat", hair_col=(60, 40, 25), coat=(240, 120, 60), pants=(40, 50, 80), nose="small"),
       dict(skin=(200, 150, 110), hair="curly", hair_col=(30, 20, 15), coat=(90, 180, 220), pants=(50, 50, 60), nose="small"),
       dict(skin=(240, 210, 185), hair="pigtails", hair_col=(200, 150, 70), coat=(200, 90, 160), pants=(40, 40, 60), nose="small"),
       dict(skin=(220, 175, 140), hair="neat", hair_col=(20, 15, 10), coat=(90, 190, 120), pants=(40, 40, 60), nose="small"),
       dict(skin=(235, 200, 170), hair="grey", hair_col=(185, 185, 190), coat=(150, 120, 200), pants=(50, 45, 40), glasses=True, nose="long")]
OLD = [dict(skin=(235, 200, 170), hair="neat", hair_col=(70, 50, 35), hat="bowler", coat=(70, 60, 55), pants=(50, 45, 45), nose="small"),
       dict(skin=(240, 210, 185), hair="curly", hair_col=(120, 70, 40), coat=(130, 60, 90), dress=(130, 60, 90), collar=(240, 235, 230),
            pants=(60, 50, 50), nose="small"),
       dict(skin=(225, 185, 150), hair="neat", hair_col=(30, 25, 20), hat="tophat", coat=(35, 35, 45), pants=(35, 35, 45), mustache=True,
            nose="long")]
ENG = [dict(skin=(235, 200, 170), hair="neat", hair_col=(80, 60, 40), coat=(245, 245, 240), pants=(60, 60, 70), glasses=True, mustache=True,
            nose="long"),
       dict(skin=(215, 170, 130), hair="grey", hair_col=(170, 170, 175), coat=(245, 245, 240), pants=(60, 60, 70), nose="small")]


def blinking(t, ph=0.0):
    return ((t + ph) % 3.3) < 0.11


def pop_in(t, at, dur=0.35):
    return out_back((t - at) / dur, 2.2) if t > at else 0.0


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


def bg(c, top, bot, y0=0, y1=H):
    c.drawPaint(P(Shader=lin((0, y0), (0, y1), [C(*top), C(*bot)])))


def guy(who, t, K=1.0, **pose):
    """A toon person as a 3D sprite (feet at the sprite position), K = world size."""
    def fn(c, sx, sy, s, fk):
        stand(c, who, sx, sy, s * K, t, **dict(pose))
    return fn


DOWN = [(-30, 150), (30, 150)]
CHEER = [(-70, -180), (70, -180)]


# ---------- props ----------

def comet(c, x, y, s, t=0.0, r=4.0, split=None, glow_win=0.0, gear=True):
    """Generic early-jet airliner, side view, nose to the right, origin at the fuselage centre.
    r = window corner radius (4 = square, 15 = round). split = (dx1, dy1, rot1, dx2, dy2, rot2) breaks it in two."""
    def body(c):
        if gear:
            for gx in (-120, 260):
                c.drawLine(gx, 60, gx, 120, S(C(60, 60, 70), 10))
                c.drawCircle(gx, 128, 16, P(C(30, 30, 35)))
        fin = skia.Path()
        fin.moveTo(-380, -40)
        fin.lineTo(-500, -250)
        fin.lineTo(-420, -255)
        fin.lineTo(-300, -40)
        fin.close()
        blob(c, fin, (235, 238, 245), 1.05, 0.78)
        hs = skia.Path()
        hs.moveTo(-470, -40)
        hs.lineTo(-560, -70)
        hs.lineTo(-520, -40)
        hs.close()
        blob(c, hs, (210, 215, 225))
        fus = skia.Path()
        fus.moveTo(-500, -40)
        fus.cubicTo(-500, -62, -470, -66, -430, -66)
        fus.lineTo(420, -66)
        fus.cubicTo(500, -66, 540, -20, 560, 6)
        fus.cubicTo(540, 40, 490, 66, 420, 66)
        fus.lineTo(-380, 66)
        fus.cubicTo(-450, 50, -500, 10, -500, -40)
        fus.close()
        c.drawPath(fus, P(Shader=lin((0, -66), (0, 66), [C(250, 252, 255), C(225, 230, 238), C(170, 178, 190)], [0, 0.55, 1])))
        c.save()
        c.clipPath(fus, doAntiAlias=True)
        c.drawRect(skia.Rect(-520, 0, 580, 16), P(C(40, 90, 170)))  # cheatline (generic)
        c.restore()
        c.drawPath(fus, S(C(40, 40, 55), 5))
        for k in range(4):  # cockpit
            c.drawRect(skia.Rect(470 + k * 16, -30 + k * 3, 482 + k * 16, -16 + k * 3), P(C(40, 60, 90)))
        for k in range(15):  # windows
            wx = -330 + k * 48
            rr = skia.RRect.MakeRectXY(skia.Rect(wx - 14, -42, wx + 14, -14), r, r)
            if glow_win > 0:
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(wx - 22, -50, wx + 22, -6), r + 6, r + 6), P(C(255, 220, 80, int(200 * glow_win))))
            c.drawRRect(rr, P(C(60, 90, 130)))
            c.drawRRect(rr, S(C(30, 30, 45), 3))
        wing = skia.Path()
        wing.moveTo(-40, 26)
        wing.lineTo(-250, 120)
        wing.lineTo(-170, 128)
        wing.lineTo(130, 40)
        wing.close()
        blob(c, wing, (195, 200, 212), 1.1, 0.7)
        for k in range(2):  # engine intakes buried in the wing root
            c.drawOval(skia.Rect(40 + k * 34, 22, 70 + k * 34, 46), P(C(40, 40, 50)))
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    if split is None:
        body(c)
    else:
        d1x, d1y, r1, d2x, d2y, r2 = split
        for (dx, dy, rot, clip) in ((d1x, d1y, r1, skia.Rect(-700, -400, -60, 300)), (d2x, d2y, r2, skia.Rect(-60, -400, 700, 300))):
            c.save()
            c.translate(dx, dy)
            c.rotate(rot)
            c.clipRect(clip)
            body(c)
            c.restore()
    c.restore()


def cloud(c, x, y, s, a=255, col=(235, 238, 248)):
    c.saveLayerAlpha(None, a)
    for dx, dy, r in ((-90, 10, 70), (0, -20, 95), (90, 5, 75), (40, 30, 70), (-40, 30, 65)):
        c.drawCircle(x + dx * s, y + dy * s, r * s, P(C(*col)))
    c.restore()


def sky_view(t, speed=260.0, night=False):
    """What you see through a cabin window: sky gradient + clouds sliding past."""
    def fn(c, cam, path, fk):
        b = path.getBounds()
        c.save()
        c.clipPath(path, doAntiAlias=True)
        top, bot = ((20, 30, 70), (70, 90, 150)) if night else ((80, 140, 230), (255, 190, 140))
        c.drawRect(b, P(Shader=lin((0, b.top()), (0, b.bottom()), [C(*top), C(*bot)])))
        w = max(10.0, b.width())
        for k in range(3):
            u = ((t * speed / w * 0.25 + k * 0.37) % 1.4) - 0.2
            cloud(c, b.right() - u * w * 1.4, b.top() + b.height() * (0.3 + 0.25 * k), w / 320, 230)
        c.restore()
        c.drawPath(path, S(C(220, 218, 210), max(3.0, b.width() * 0.09)))
        c.drawPath(path, S(C(150, 145, 140), max(1.5, b.width() * 0.02)))
    return fn


def cabin(w, t, rows=9, wr=48, night=False, speed=260.0, pax=True, mask_drop=None, look=(0, -0.2), skip_row=None, seats=True):
    """Airliner cabin along +Z (nose at high Z). Floor y=0, walls x=+-620, windows on both walls."""
    L = rows * 320 + 400
    zs = list(range(0, L, 160)) + [L]
    for za, zb in zip(zs, zs[1:]):  # short segments so the painter's sort works locally (windows over their own wall)
        w.panel([(-620, 0, za), (620, 0, za), (620, 0, zb), (-620, 0, zb)], (95, 45, 55))  # carpet
        w.panel([(-120, -1, za), (120, -1, za), (120, -1, zb), (-120, -1, zb)], (120, 60, 70), bias=1)  # aisle runner
        w.panel([(-420, -800, za), (420, -800, za), (420, -800, zb), (-420, -800, zb)], (150, 148, 150))
        for side in (-1, 1):
            w.panel([(side * 620, 0, za), (side * 620, -580, za), (side * 620, -580, zb), (side * 620, 0, zb)], (175, 168, 160))
            w.panel([(side * 620, -580, za), (side * 420, -800, za), (side * 420, -800, zb), (side * 620, -580, zb)], (165, 160, 158))
    for side in (-1, 1):
        for k in range(rows):  # overhead bin lips
            z = 80 + k * 320
            w.panel([(side * 600, -600, z), (side * 600, -600, z + 300), (side * 430, -690, z + 300), (side * 430, -690, z)],
                    (215, 212, 200), outline=(150, 145, 135), bias=2)
        for k in range(rows):
            z = 230 + k * 320
            pts = rounded_rect_pts(side * 619, -420, 120, 170, wr, z=z, plane="zy")
            w.custom(pts, sky_view(t + k * 0.13, speed, night), bias=40)
    for k in range(rows):
        z = 80 + k * 320
        w.panel([(-60, -799, z + 40), (60, -799, z + 40), (60, -799, z + 120), (-60, -799, z + 120)], (255, 250, 220), bias=1)
        for side in (-1, 1):
            if (skip_row is not None and k == skip_row) or not seats:
                continue
            x0, x1 = (-600, -140) if side < 0 else (140, 600)
            w.box((x0, -470, z), (x1, -140, z + 50), (60, 90, 150))
            w.box((x0, -230, z + 50), (x1, -140, z + 230), (70, 100, 160))
            w.box((x0, -140, z + 190), (x1, 0, z + 230), (50, 75, 130))
            if pax and (k + (side > 0)) % 2 == 0:
                who = PAX[(k * 2 + (side > 0)) % len(PAX)]
                wx = -380 if side < 0 else 380
                w.sprite((wx, 0, z + 140), guy(who, t, 1.6, eyes="open", mouth="smile", brows="flat",
                                                look=(-side * 0.5 + look[0], look[1]), hands=DOWN), bias=-2)
            if mask_drop is not None:  # oxygen masks on springs
                k2 = t - mask_drop - k * 0.03
                if k2 > 0:
                    yy = -800 + 300 * min(1.0, (k2 / 0.25) ** 2) + 40 * PH.spring_v(k2, 0.25, 1, 3, 3.5)
                    mx = -370 if side < 0 else 370

                    def mask(c, sx, sy, s, fk, yy=yy):
                        c.drawLine(sx, sy - (yy + 800) * s, sx, sy - 30 * s, S(C(240, 240, 240), max(2, 5 * s)))
                        blob(c, oval(sx, sy, 34 * s, 28 * s), (250, 210, 60), 1.2, 0.7)
                    w.sprite((mx, yy, z + 250), mask, bias=-4)
    return L


def tank_water(level, t):
    def fn(c, cam, path, fk):
        c.clipPath(path, doAntiAlias=True)
        b = path.getBounds()
        c.drawRect(b, P(Shader=lin((0, b.top()), (0, b.bottom()), [C(80, 170, 230, 110), C(30, 90, 170, 150)])))
        for k in range(6):  # caustic wobble lines
            yy = b.top() + b.height() * (0.15 + 0.14 * k)
            p = skia.Path()
            for i in range(21):
                xx = b.left() + b.width() * i / 20
                (p.moveTo if i == 0 else p.lineTo)(xx, yy + 6 * math.sin(i * 0.8 + t * 3 + k))
            c.drawPath(p, S(C(200, 240, 255, 60), 3))
    return fn


def flow_lines(c, cam, plate, hole_w, hole_h, r, t, sharp=True, heat=0.0, tear=0.0):
    """Stress 'flow' lines across a plate with a window hole. plate(u, v) -> world point. Lines bunch at sharp corners."""
    n = 15
    for i in range(n):
        v0 = -520 + i * (1040 / (n - 1))
        p = skia.Path()
        first = True
        for k in range(61):
            u = -560 + k * (1120 / 60)
            v = v0
            ah = hole_h / 2 + 18
            if abs(v0) < ah + 120:
                if sharp:  # squeezed hard against the hole edge, bunching right at the corners
                    span = hole_w / 2 + 40
                    g = max(0.0, 1 - max(0.0, abs(u) - span + 40) / 40) if abs(u) < span else 0.0
                    target = math.copysign(ah + (abs(v0) / (ah + 120)) * 30, v0 if v0 != 0 else 1)
                else:  # smooth detour that spreads far around a round hole
                    g = math.exp(-(u / (hole_w * 0.85)) ** 2)
                    target = math.copysign(ah + (abs(v0) / (ah + 120)) * 120, v0 if v0 != 0 else 1)
                v = v0 + (target - v0) * g
            q = cam.project(*plate(u, v))
            if q is None:
                first = True
                continue
            (p.moveTo if first else p.lineTo)(q[0], q[1])
            first = False
        dense = abs(v0) < hole_h / 2 + 120
        col = (255, 90, 60) if (sharp and dense) else ((120, 230, 160) if not sharp else (160, 200, 255))
        eff = skia.DashPathEffect.Make([26, 16], -t * 120)
        c.drawPath(p, P(C(*col, 220), Style=skia.Paint.kStroke_Style, StrokeWidth=5, PathEffect=eff, StrokeCap=skia.Paint.kRound_Cap))
    if sharp:  # hot spots at the four corners
        for su in (-1, 1):
            for sv in (-1, 1):
                q = cam.project(*plate(su * hole_w / 2, sv * hole_h / 2))
                if q:
                    pulse = 0.6 + 0.4 * math.sin(t * 8)
                    glow(c, q[0], q[1], 70 + 90 * heat, (255, 60, 30), int(120 + 120 * heat * pulse))
        if tear > 0:  # a crack running out from the top-right corner
            r_ = random.Random(4)
            u, v = hole_w / 2, -hole_h / 2
            p = skia.Path()
            q = cam.project(*plate(u, v))
            p.moveTo(q[0], q[1])
            for k in range(int(14 * tear) + 1):
                u += 26
                v -= 18 + r_.uniform(-14, 14)
                q = cam.project(*plate(u, v))
                if q:
                    p.lineTo(q[0], q[1])
            c.drawPath(p, S(C(20, 10, 10), 9))
            c.drawPath(p, S(C(255, 120, 60), 3))


# ---------- scenes ----------

def art_hook(c, t):
    bg(c, (10, 10, 20), (25, 20, 35))
    mk = CUE["mistake"]
    w = World()
    cabin(w, t, rows=8, wr=48, mask_drop=mk - 0.15, look=(0, -0.3))
    dx, dy, dr = shake(t, mk, 30, 0.5)
    L = 8 * 320 + 400
    cam = Cam((60 * math.sin(t * 0.7), -560, L - 120 - 260 * ease(t / 3.4)), math.pi + 0.08 * math.sin(t * 0.6), 0.04, -5 + 4 * math.sin(t * 0.8) + dr,
              820, cy=H / 2 + 300)
    cam.x += dx
    cam.y += dy
    w.render(c, cam, fog=(20, 15, 25), fog_near=1800, fog_far=6000)
    if t > mk - 0.15:  # red warning light
        a = int(90 * (0.5 + 0.5 * math.sin((t - mk) * 14)))
        c.drawPaint(P(C(255, 30, 30, a)))


def art_comet(c, t):
    bg(c, (25, 35, 80), (250, 160, 110), 0, 1450)
    glow(c, 760, 1380, 600, (255, 200, 140), 120)
    fs, lv = CUE["fast"], CUE["loved"]
    w = World()
    w.panel([(-9000, 0, 1200), (9000, 0, 1200), (9000, 0, 2600), (-9000, 0, 2600)], (55, 58, 66))  # runway (along X)
    for k in range(-30, 30):
        w.panel([(k * 300, -1, 1880), (k * 300 + 160, -1, 1880), (k * 300 + 160, -1, 1920), (k * 300, -1, 1920)], (235, 235, 230))
    w.panel([(-9000, 1, -2000), (9000, 1, -2000), (9000, 1, 1200), (-9000, 1, 1200)], (60, 110, 60))
    w.panel([(-9000, 1, 2600), (9000, 1, 2600), (9000, 1, 9000), (-9000, 1, 9000)], (55, 100, 58))
    w.box((-3200, -600, 5200), (-1400, 0, 5900), (150, 140, 130))  # terminal
    w.box((-2600, -1000, 5300), (-2300, -600, 5600), (130, 120, 110))  # control tower
    w.box((-2700, -1150, 5250), (-2200, -1000, 5650), (90, 140, 180))
    for k in range(9):  # far crowd behind the runway
        w.sprite((-1600 + k * 400, 0, 3000 + (k % 2) * 120),
                 guy(OLD[k % 3], t, 1.0, eyes="wide" if t > fs else "open", mouth="O" if t > fs else "smile", brows="up", look=(0, -0.3),
                     hands=CHEER if (t > lv and k % 2) else DOWN))
    # the jet: rolls, accelerates on "fast", rotates and lifts off
    k = max(0.0, t - fs + 0.6)
    px = -900 + 0.5 * 320 * k * k
    vel = 320 * k
    lift = max(0.0, vel - 650) / 650
    py = -150 - 420 * lift * lift
    rot = -min(10.0, 12 * lift)
    def jet(c, sx, sy, s, fk):
        c.save()
        c.translate(sx, sy)
        c.rotate(rot)
        comet(c, 0, 0, s * 1.0, t, 4, gear=lift < 0.5)
        c.restore()
    w.sprite((px, py, 1900), jet)
    # near crowd on the left of the frame with hats that fly up (gravity + spin) on "loved it"
    for k2 in range(3):
        x, z = 260 + k2 * 230, 600 + k2 * 70

        def near(c, sx, sy, s, fk, k2=k2):
            stand(c, OLD[k2], sx, sy, s * 1.0, t, eyes="closed" if t > lv else "open", mouth="laugh" if t > lv else "smile", brows="up",
                  look=(-1, -0.3), hands=CHEER if t > lv else DOWN)
        w.sprite((x, 0, z), near)
        if t > lv and OLD[k2].get("hat"):
            h = t - lv - k2 * 0.1
            if h > 0:
                hx, hy = x + 120 * h, -520 - 1400 * h + 0.5 * 2600 * h * h

                def hat_fn(c, sx, sy, s, fk, h=h, k2=k2):
                    c.save()
                    c.translate(sx, sy)
                    c.rotate(400 * h * (1 if k2 % 2 else -1))
                    blob(c, oval(0, 8 * s, 70 * s, 12 * s), (45, 40, 40))
                    blob(c, rrect(-42 * s, -40 * s, 42 * s, 8 * s, 30 * s), (50, 44, 44))
                    c.restore()
                if hy < 0:
                    w.sprite((hx, hy, z - 5), hat_fn, bias=10)
    yaw = 0.55 * math.atan2(px + 300, 2600) + 0.02 * t
    cam = Cam((-100 + 60 * t, -950 + 30 * t, -900), yaw, 0.2 + 0.01 * t, -2 + 2 * math.sin(t * 0.6), 950, cy=H / 2 + 330)
    w.render(c, cam, fog=(180, 130, 120), fog_near=2500, fog_far=12000, fog_max=0.6)


def art_square(c, t):
    bg(c, (20, 22, 35), (60, 60, 75))
    sq = CUE["square"]
    w = World()
    w.floor(-3000, 3000, -500, 4000, 0, [(80, 80, 88), (88, 88, 96)], plank=300, depth_step=300)
    for k in range(-3, 4):  # hangar pillars for parallax
        w.box((k * 900 - 40, -1800, 2600), (k * 900 + 40, 0, 2680), (110, 105, 100))
    w.sprite((0, -300, 1200), lambda c, sx, sy, s, fk: comet(c, sx, sy, s * 1.5, t, 4, glow_win=max(0.0, min(1.0, (t - sq + 0.1) / 0.2))
                                                               * (0.6 + 0.4 * math.sin(t * 12))))
    zoom = ease(t / 2.2)
    cam = Cam.orbit((150, -330, 1200), 1500 - 900 * zoom, -0.35 + 0.3 * zoom, height=-60, roll=-4 * zoom, f=1000, cy=H / 2 + 330)
    w.render(c, cam, fog=(20, 22, 35), fog_near=1500, fog_far=6000)


def art_breakup(c, t):
    br, gr = CUE["broke"], CUE["grounded"]
    if t < gr - 0.25:
        bg(c, (10, 15, 40), (60, 70, 120))
        w = World()
        r = random.Random(2)
        for i in range(26):  # clouds at many depths; the camera flies forward through them
            X, Y, Z = r.uniform(-2500, 2500), r.uniform(-900, 900), r.uniform(800, 9000)
            Z = (Z - t * 900) % 9000 + 600

            def cl(c, sx, sy, s, fk, i=i):
                cloud(c, sx, sy, s * 2.2, int(230 * (1 - fk)), (200, 205, 225))
            w.sprite((X, Y, Z), cl, layer="bg" if Z > 3000 else "main")
        k = t - br
        if k < 0:
            sp = None
        else:  # two rigid bodies: separate, spin, fall (gravity) — no people shown
            g = 0.5 * 900 * k * k
            sp = (-120 * k, 160 * k + g, -28 * k - 8 * k * k, 160 * k, 60 * k + g * 0.8, 22 * k + 6 * k * k)
        w.sprite((0, -200 + 15 * math.sin(t * 2), 2400), lambda c, sx, sy, s, fk: comet(c, sx, sy, s * 1.2, t, 4, split=sp, gear=False))
        cam = Cam.orbit((0, -200, 2400), 2400, 0.25 * math.sin(t * 0.4), height=-80, roll=6 * math.sin(t * 0.5), f=1000, cy=H / 2 + 300)
        dx, dy, dr = shake(t, br, 40, 0.6)
        cam.x += dx
        cam.y += dy
        cam.roll += dr
        w.render(c, cam, fog=(40, 45, 80), fog_near=2500, fog_far=9000, bg_blur=6)
        if k > 0:  # debris + smoke with drag
            pc = cam.project(0, -200, 2400)
            for i in range(24):
                r2 = random.Random(i)
                ang = r2.uniform(0, 2 * math.pi)
                sp_ = r2.uniform(200, 700)
                d = 1.8
                ex = pc[0] + math.cos(ang) * sp_ / d * (1 - math.exp(-d * k))
                ey = pc[1] + math.sin(ang) * sp_ / d * (1 - math.exp(-d * k)) + 300 * k * k
                a = max(0, int(255 * (1 - k / 2.5)))
                c.save()
                c.translate(ex, ey)
                c.rotate(k * r2.uniform(-500, 500))
                c.drawRect(skia.Rect(-10, -5, 10, 5), P(C(200, 205, 215, a)))
                c.restore()
            for i in range(10):
                kk = k - i * 0.08
                if kk > 0:
                    c.drawCircle(pc[0] - 40 + i * 8, pc[1] + 40 * kk, 40 + 80 * kk, P(C(60, 60, 70, int(max(0, 120 * (1 - kk / 2)))), MaskFilter=blur(14)))
        return
    # grounded: parked jets in a dark hangar, puzzled engineers
    bg(c, (15, 15, 22), (45, 42, 50))
    w = World()
    w.floor(-4000, 4000, -500, 7000, 0, [(70, 70, 76), (78, 78, 84)], plank=400, depth_step=400)
    for k in range(-4, 5):
        w.box((k * 1000 - 40, -2400, 6000), (k * 1000 + 40, 0, 6080), (100, 96, 92))
    for i, (X, Z) in enumerate(((-900, 3200), (900, 4300), (-200, 5400))):
        w.sprite((X, -200, Z), lambda c, sx, sy, s, fk: comet(c, sx, sy, s * 1.3, t, 4))
    kq = t - gr

    def eng(i):
        def fn(c, sx, sy, s, fk):
            stand(c, ENG[i], sx, sy, s * 1.0, t, eyes="open", mouth="frown", brows="sad", look=(0, -0.4),
                  hands=[(-30, 150), (40, -160)] if i == 0 else [(-40, -160), (30, 150)])
            if kq > CUE["nobody"] - gr:
                q = pop_in(t, CUE["nobody"] + i * 0.15)
                c.drawString("?", sx - 30 * s, sy - 560 * s, skia.Font(FB, 160 * s * q), P(C(255, 220, 120)))
        return fn
    w.sprite((-350, 0, 1500), eng(0))
    w.sprite((350, 0, 1550), eng(1))
    cam = Cam.orbit((0, -300, 1700), 1900 - 200 * ease(kq / 2), -0.25 + 0.2 * ease(kq / 2.5), height=-200, roll=2, f=950, cy=H / 2 + 330)
    w.render(c, cam, fog=(15, 15, 22), fog_near=2500, fog_far=9000, bg_blur=4)


def art_tank(c, t):
    bg(c, (15, 18, 28), (45, 50, 62))
    tk, up, th = CUE["tank"], CUE["up"], CUE["thousands"]
    w = World()
    w.floor(-4000, 4000, -800, 6000, 0, [(72, 72, 78), (80, 80, 86)], plank=400, depth_step=400)
    for k in range(-4, 5):
        w.box((k * 1000 - 40, -2400, 5200), (k * 1000 + 40, 0, 5280), (100, 96, 92))
    pump_k = max(0.0, t - up + 0.3)
    cyc = math.sin(pump_k * 2 * math.pi * (1.2 + 0.8 * min(1.0, pump_k / 3)))
    level = -560 + 25 * cyc
    fill = ease((t - tk + 0.6) / 0.8)
    # tank walls (see-through), water volume, the fuselage inside
    w.box((-900, -700, 1400), (900, 0, 2400), (150, 190, 220), alpha=60, outline=(190, 220, 240), bias=0)
    lv = -40 + (level + 40) * fill
    w.custom([(-890, lv, 1410), (890, lv, 1410), (890, -2, 1410), (-890, -2, 1410)], tank_water(level, t), bias=-30)
    breathe = 1 + 0.03 * cyc * (pump_k > 0)
    w.sprite((0, -260, 1900), lambda c, sx, sy, s, fk: (c.save(), c.translate(sx, sy), c.scale(1, breathe), c.translate(-sx, -sy),
                                                         comet(c, sx, sy, s * 1.45, t, 4, gear=False), c.restore()))
    # pump with piston
    w.box((1150, -900, 1700), (1350, 0, 1900), (120, 60, 50))
    w.box((1190, -1200 + 120 * cyc, 1740), (1310, -900, 1860), (180, 185, 190))
    w.panel([(900, -400, 1800), (1150, -400, 1800), (1150, -440, 1800), (900, -440, 1800)], (90, 90, 95))

    def board(c, sx, sy, s, fk):  # flights counter on a stand
        n = int(3000 * ease(max(0.0, (t - up) / 4.5)))
        blob(c, rrect(sx - 230 * s, sy - 560 * s, sx + 230 * s, sy - 360 * s, 18 * s), (25, 25, 30), 1.2, 0.7)
        c.drawLine(sx, sy - 360 * s, sx, sy, S(C(70, 70, 75), max(2, 12 * s)))
        f1 = skia.Font(FB, 44 * s)
        f2 = skia.Font(FB, 96 * s)
        lab = "FLIGHTS"
        c.drawString(lab, sx - f1.measureText(lab) / 2, sy - 505 * s, f1, P(C(200, 200, 210)))
        txt = f"{n:,}"
        c.drawString(txt, sx - f2.measureText(txt) / 2, sy - 400 * s, f2, P(C(120, 255, 140)))
    w.sprite((-950, 0, 1150), board)
    w.sprite((-650, 0, 900), guy(ENG[0], t, 1.0, eyes="wide", mouth="O", brows="up", look=(0.6, -0.3), hands=[(-30, 150), (60, 40)]))
    w.sprite((650, 0, 950), guy(ENG[1], t, 1.0, eyes="open", mouth="smile", brows="flat", look=(-0.6, -0.3), hands=DOWN))
    cam = Cam.orbit((0, -350, 1900), 2700 - 300 * ease(t / 9), -0.55 + 0.75 * ease(t / 9.5), height=-500 + 150 * ease(t / 9), roll=-2,
                    f=950, cy=H / 2 + 300)
    w.render(c, cam, fog=(15, 18, 28), fog_near=3000, fog_far=9000, bg_blur=3)
    if t > th - 0.2:  # light flicker day/night
        a = int(40 * (0.5 + 0.5 * math.sin((t - th) * 6)))
        c.drawPaint(P(C(0, 0, 30, a)))


def plate_fn(cx, cy, cz, yaw):
    ca, sa = math.cos(yaw), math.sin(yaw)

    def f(u, v):
        return cx + u * ca, cy + v, cz + u * sa
    return f


def art_crack(c, t):
    bg(c, (8, 10, 18), (30, 35, 50))
    ck, co = CUE["crack"], CUE["corner"]
    w = World()
    pl = plate_fn(0, -400, 1200, 0.25)
    pts = [pl(-700, -650), pl(700, -650), pl(700, 650), pl(-700, 650)]
    w.panel(pts, (190, 196, 205))
    for i in range(-6, 7):  # rivet rows
        for v in (-560, 560):
            q = pl(i * 100, v)
            w.panel([(q[0] - 8, q[1] - 8, q[2]), (q[0] + 8, q[1] - 8, q[2]), (q[0] + 8, q[1] + 8, q[2]), (q[0] - 8, q[1] + 8, q[2])], (120, 125, 135),
                    bias=2)
    win = [pl(u, v) for (u, v) in [(-200, -260), (200, -260), (200, 260), (-200, 260)]]
    w.custom(win, sky_view(t, 300, night=True), bias=3)
    grow = max(0.0, min(1.0, (t - ck) / 1.2))

    def crack_fn(c, cam, path, fk):
        if grow <= 0:
            return
        r_ = random.Random(9)
        u, v = 200, -260
        p = skia.Path()
        q = cam.project(*pl(u, v))
        p.moveTo(q[0], q[1])
        branches = []
        for k in range(int(20 * grow) + 1):
            u += 22
            v -= 16 + r_.uniform(-16, 16)
            q = cam.project(*pl(u, v))
            p.lineTo(q[0], q[1])
            if k in (5, 11):
                branches.append((u, v))
        c.drawPath(p, S(C(15, 10, 10), 10))
        c.drawPath(p, S(C(255, 140, 70), 3))
        for (bu, bv) in branches:
            bp = skia.Path()
            q = cam.project(*pl(bu, bv))
            bp.moveTo(q[0], q[1])
            for k in range(5):
                bu += 14
                bv += 10 + r_.uniform(-8, 8)
                q = cam.project(*pl(bu, bv))
                bp.lineTo(q[0], q[1])
            c.drawPath(bp, S(C(15, 10, 10), 6))
        q0 = cam.project(*pl(200, -260))
        glow(c, q0[0], q0[1], 120, (255, 80, 40), int(200 * min(1.0, grow * 3)))
    w.custom(win, crack_fn, bias=5)
    zoom = ease((t - ck + 0.2) / 0.35)
    cam = Cam.orbit((150, -650, 1200), 1500 - 650 * zoom, -0.1 + 0.35 * zoom + 0.05 * math.sin(t), height=-100, roll=-6 * zoom, f=1000,
                    cy=H / 2 + 280)
    dx, dy, dr = shake(t, ck, 26, 0.5)
    cam.x += dx
    cam.y += dy
    cam.roll += dr
    w.render(c, cam, fog=(8, 10, 18), fog_near=2500, fog_far=7000)
    if ck < t < ck + 0.15:
        c.drawPaint(P(C(255, 255, 255, int(150 * (1 - (t - ck) / 0.15)))))


def art_balloon(c, t):
    bg(c, (15, 20, 35), (40, 50, 75))
    pr, bl = CUE["pressurized"], CUE["balloon"]
    w = World()
    w.floor(-4000, 4000, -500, 6000, 0, [(62, 66, 80), (70, 74, 88)], plank=400, depth_step=400)
    infl = ease((t - pr + 0.2) / 1.2)
    sq_ = 1 + 0.07 * infl + 0.015 * math.sin(t * 5) * infl
    w.sprite((-200, -320, 1800), lambda c, sx, sy, s, fk: (c.save(), c.translate(sx, sy), c.scale(1 + 0.02 * infl, sq_), c.translate(-sx, -sy),
                                                           comet(c, sx, sy, s * 1.25, t, 4, gear=False), c.restore()))

    def arrows(c, sx, sy, s, fk):  # pressure pushing outwards
        if infl <= 0.05:
            return
        for k in range(8):
            ax = sx + (-480 + k * 130) * s
            for sgn in (-1, 1):
                L = (50 + 30 * math.sin(t * 6 + k)) * infl * s
                y0 = sy + sgn * 95 * s * sq_
                c.drawLine(ax, y0, ax, y0 + sgn * L, S(C(255, 120, 90, 230), max(2, 8 * s)))
                tri = skia.Path()
                tri.moveTo(ax - 14 * s, y0 + sgn * L)
                tri.lineTo(ax + 14 * s, y0 + sgn * L)
                tri.lineTo(ax, y0 + sgn * (L + 22 * s))
                tri.close()
                c.drawPath(tri, P(C(255, 120, 90, 230)))
    w.sprite((-200, -320, 1790), arrows, bias=5)
    bk = ease((t - bl + 0.5) / 0.6)

    def balloon(c, sx, sy, s, fk):  # a party balloon inflating with a spring wobble
        if bk <= 0:
            return
        r = (120 + 40 * PH.spring_v(t, bl + 0.1, 0.4, 2.5, 3)) * bk * s
        c.drawLine(sx, sy, sx + 10 * s, sy - 300 * s, S(C(230, 230, 230), max(1, 3 * s)))
        blob(c, oval(sx, sy - 300 * s - r * 1.1, r, r * 1.15), (235, 60, 80), 1.3, 0.65)
    w.sprite((850, 0, 1500), balloon)
    w.sprite((700, 0, 1200), guy(PAX[1], t, 1.0, eyes="wide" if t > bl else "open", mouth="O" if t > bl else "smile", brows="up",
                                 look=(0.4, -0.5), hands=DOWN))
    cam = Cam.orbit((150, -350, 1650), 1700 - 250 * ease(t / 4), 0.3 - 0.45 * ease(t / 4.2), height=-250, roll=3 * math.sin(t * 0.7), f=950,
                    cy=H / 2 + 300)
    w.render(c, cam, fog=(15, 20, 35), fog_near=2500, fog_far=8000, bg_blur=3)


def art_stress(c, t, sharp=True):
    bg(c, (10, 10, 18), (35, 30, 45))
    w = World()
    pl = plate_fn(0, -450, 1300, 0.0)
    w.panel([pl(-620, -600), pl(620, -600), pl(620, 600), pl(-620, 600)], (60, 64, 76), outline=(120, 125, 140))
    r = 12 if sharp else 140
    hole = rounded_rect_pts(0, -450, 360, 440, r, z=1300, plane="xy")
    w.panel(hole, (12, 12, 20), outline=(200, 205, 215), bias=2)
    if sharp:
        st, pt, ti, tr = CUE["stress"], CUE["point"], CUE["tired"], CUE["tears"]
        heat = ease((t - pt + 0.8) / 0.6)
        tear = max(0.0, min(1.0, (t - tr) / 0.5))
        wob = 6 * PH.spring_v(t, ti, 1, 4, 3) if t > ti else 0.0
    else:
        heat, tear, wob = 0.0, 0.0, 0.0
    w.custom([pl(-620, -600), pl(620, -600), pl(620, 600), pl(-620, 600)],
             lambda c, cam, path, fk: (c.clipPath(path, doAntiAlias=True), flow_lines(c, cam, pl, 360, 440, r, t, sharp, heat, tear)), bias=1)
    yaw = (0.45 if sharp else -0.45) * math.cos(t * 0.5) + wob * 0.01
    cam = Cam.orbit((0, -450, 1300), 1700 - 250 * ease(t / 4), yaw, height=-150, roll=wob, f=1000, cy=H / 2 + 260)
    if sharp and t > CUE["tears"]:
        dx, dy, dr = shake(t, CUE["tears"], 26, 0.5)
        cam.x += dx
        cam.y += dy
        cam.roll += dr
    w.render(c, cam, fog=(10, 10, 18), fog_near=3000, fog_far=8000)


def art_sharp(c, t):
    art_stress(c, t, True)


def art_round(c, t):
    art_stress(c, t, False)
    ev = CUE["evenly"]
    if t > ev - 0.3:
        for i in range(10):
            a = i / 10 * 2 * math.pi + t
            glow(c, 540 + math.cos(a) * 330, 1170 + math.sin(a) * 380, 80, (120, 255, 170), int(70 * pop_in(t, ev - 0.3)))


def art_today(c, t):
    bg(c, (20, 20, 35), (60, 45, 60))
    w = World()
    cabin(w, t, rows=7, wr=60, speed=200, pax=False, seats=False)
    zw = 230 + 320 * 3
    rd = pop_in(t, CUE["rounded"] - 0.1)

    def kid(c, sx, sy, s, fk):
        stand(c, PAX[2], sx, sy, s * 1.6, t, eyes="wide" if rd > 0 else "open", mouth="grin", brows="up", look=(-1, -0.3), hands=DOWN)
    w.sprite((-430, 0, zw + 150), kid, bias=-50)

    def ring(c, cam, path, fk):
        if rd > 0:
            c.drawPath(path, S(C(255, 210, 80, int(230 * min(1.0, rd))), 14 + 6 * math.sin(t * 8)))
    w.custom(rounded_rect_pts(-617, -420, 120, 170, 60, z=zw, plane="zy"), ring, bias=60)
    cam = Cam.orbit((-619, -440, zw - 60), 700 - 100 * ease(t / 3), -1.0 + 0.2 * ease(t / 3.2), height=-60, roll=4 * math.sin(t * 0.6),
                    f=850, cy=H / 2 + 300)
    w.render(c, cam, fog=(25, 20, 30), fog_near=1800, fog_far=6000)


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


def art_vote(c, t):
    bg(c, (20, 20, 35), (55, 45, 60))
    cm = CUE["comments"]
    w = World()
    cabin(w, t, rows=4, wr=60, speed=200, pax=False, skip_row=3)
    z = 80 + 320 * 3
    for side in (-1, 1):
        x0, x1 = (-600, -140) if side < 0 else (140, 600)
        w.box((x0, -470, z), (x1, -140, z + 50), (60, 90, 150))
        w.box((x0, -230, z + 50), (x1, -140, z + 230), (70, 100, 160))
        w.box((x0, -140, z + 190), (x1, 0, z + 230), (50, 75, 130))
    w.sprite((-470, 0, z + 140), guy(PAX[0], t, 1.6, eyes="open", mouth="grin", brows="up", look=(-0.6, -0.2), hands=DOWN), bias=-2)
    w.sprite((-230, 0, z + 140), guy(PAX[2], t, 1.6, eyes="open", mouth="smile", brows="up", look=(0.6, -0.2), hands=DOWN), bias=-2)

    def sign(lab, col):
        def fn(c, sx, sy, s, fk):
            f = skia.Font(FB, 64 * s)
            tw = f.measureText(lab)
            b = 0.06 * PH.spring_v(t, 0.3, 1, 2, 2)
            c.save()
            c.translate(sx, sy)
            c.rotate(b * 40)
            blob(c, rrect(-tw / 2 - 30 * s, -50 * s, tw / 2 + 30 * s, 40 * s, 16 * s), col, 1.2, 0.7)
            c.drawString(lab, -tw / 2, 18 * s, f, P(C(255, 255, 255)))
            c.restore()
        return fn
    _ = sign
    cam = Cam((-260 + 40 * math.sin(t), -600, z + 1150 - 120 * ease(t / 3)), math.pi - 0.12 + 0.08 * math.sin(t * 0.7), 0.06, -2, 900,
              cy=H / 2 + 330)
    w.render(c, cam, fog=(25, 20, 30), fog_near=2000, fog_far=6000)
    for i in range(10):  # comment bubbles fly up with drag
        t0 = cm - 0.5 + i * 0.13
        k = t - t0
        if k <= 0:
            continue
        r = random.Random(i)
        x = (r.uniform(110, 260) if i % 2 else r.uniform(820, 970)) + 20 * math.sin(k * 4 + i)
        y = 1800 - 900 * (1 - math.exp(-2.2 * k))
        a = int(255 * max(0, min(1, (2.0 - k) / 0.5)))
        if a <= 0:
            continue
        lab, col = ("WINDOW!", SKY) if i % 3 else ("AISLE!", (240, 140, 60))
        f = skia.Font(FB, 38)
        tw = f.measureText(lab)
        c.saveLayerAlpha(None, a)
        blob(c, rrect(x - tw / 2 - 22, y - 38, x + tw / 2 + 22, y + 38, 20), (250, 250, 255), 1.03, 0.9)
        c.drawString(lab, x - tw / 2, y + 13, f, P(C(*col)))
        c.restore()


def art_cta(c, t):
    U.T_EIGHT = -10
    U.background(c, t, 0)
    U.spotlight(c, t, 0)
    c.drawPaint(P(C(10, 6, 14, 120)))
    draw_cta2(c, t, CUE["like"], CUE["sub"])


ART = [art_hook, art_comet, art_square, art_breakup, art_tank, art_crack, art_balloon, art_sharp, art_round, art_today, art_follow, art_vote, art_cta]
NA = len(ART) - 1


def render_art(i, t, dur):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    ART[i](c, t)
    if i != NA:
        snap = surf.makeImageSnapshot()
        c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=U.BLOOM, ImageFilter=skia.ImageFilters.Blur(24, 24), BlendMode=skia.BlendMode.kPlus, Alphaf=0.3))
        c.drawPaint(P(Shader=rad(540, 1100, 1250, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 190)], [0, 0.5, 1])))
        c.drawRect(skia.Rect(0, 0, W, 900), P(Shader=lin((0, 0), (0, 900), [C(5, 4, 10, 200), C(5, 4, 10, 0)])))
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
    line(img, "Airplane windows are round", 220, font(FONT_B, 66))
    line(img, "because of a...", 315, font(FONT_B, 66))
    slam(img, "TERRIBLE", 420, t, CUE["mistake"] - 0.45, RED, 150)
    slam(img, "MISTAKE!", 590, t, CUE["mistake"] - 0.1, GOLD, 150)
    impact(img, t, CUE["mistake"] + 0.1, 18)


def tx_comet(img, t):
    tag(img, "BRITAIN, 1952", t, (40, 90, 170))
    title(img, t, "The first JET airliner", "Fast. Quiet. The future.", CUE["fast"], sub_color=GOLD)


def tx_square(img, t):
    title(img, t, "And its windows were...")
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 640, "SQUARE", t, CUE["square"], col=GOLD, size=130)
    impact(img, t, CUE["square"] + 0.15, 12)


def tx_breakup(img, t):
    tag(img, "1954", t, (170, 40, 40))
    title(img, t, "Two broke apart", "...in mid-air, months apart", CUE["midair"], sub_color=RED)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 700, "GROUNDED", t, CUE["grounded"], col=RED, size=110)
    impact(img, t, CUE["grounded"] + 0.15, 14)


def tx_tank(img, t):
    title(img, t, "A whole plane in a TANK", "pumped again and again...", CUE["up"], sub_color=SKY)


def tx_crack(img, t):
    title(img, t, "Then it happened...", y=260)
    slam(img, "CRACK!", 430, t, CUE["crack"] - 0.1, RED, 170)
    text_block(img, "right at the corner of a window", font(FONT_B, 58), 640, t, (255, 235, 210), CUE["corner"])
    impact(img, t, CUE["crack"] + 0.1, 18)


def tx_balloon(img, t):
    title(img, t, "Every flight...", "the cabin stretches like a balloon", CUE["balloon"] - 0.6, sub_color=SKY)


def tx_sharp(img, t):
    title(img, t, "A SHARP corner", "focuses ALL the stress", CUE["stress"], sub_color=RED)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 700, "IT TEARS", t, CUE["tears"], col=RED, size=110)
    impact(img, t, CUE["tears"] + 0.15, 14)


def tx_round(img, t):
    title(img, t, "A ROUND corner", "spreads it evenly", CUE["evenly"] - 0.4, sub_color=GREEN)


def tx_today(img, t):
    title(img, t, "Every plane window today...", y=260)
    slam(img, "ROUNDED", 420, t, CUE["rounded"] - 0.1, GOLD, 160)
    impact(img, t, CUE["rounded"] + 0.1, 14)


def tx_follow(img, t):
    title(img, t, "A surprising fact", "...EVERY day!", CUE["fday"], sub_color=GOLD)


def tx_vote(img, t):
    slam(img, "WINDOW OR AISLE?", 300, t, CUE["aisle"] - 0.6, (255, 255, 255), 92)
    text_block(img, "Tell me in the comments!", font(FONT_B, 60), 500, t, GOLD, CUE["comments"] - 0.3)
    impact(img, t, CUE["aisle"] - 0.5, 12)


def tx_cta(img, t):
    pass


TEXT = [tx_hook, tx_comet, tx_square, tx_breakup, tx_tank, tx_crack, tx_balloon, tx_sharp, tx_round, tx_today, tx_follow, tx_vote, tx_cta]
base.TRANSITION = splat

if __name__ == "__main__":
    voice = f"{VOICE_DIR}/voice.mp3"
    tl = Timeline(voice)
    firsts = ["nineteen", "and it had", "but", "so engineers", "then it happened", "every", "sharp", "around corners", "that's why", "follow", "so",
              "learn"]
    after, starts = 3.0, [0.0]
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
               mistake=f("mistake", 0, 0.0),
               fast=f("fast", 1), loved=f("loved", 1),
               square=f("square", 2, 0.15),
               midair=f("midair|mid", 3), broke=f("broke", 3, 0.0), grounded=f("grounded", 3, 0.15), nobody=f("nobody", 3),
               tank=f("tank", 4), up=f("up", 4), thousands=f("thousands", 4),
               crack=f("crack", 5, 0.0), corner=f("corner", 5),
               pressurized=f("pressurized", 6), balloon=f("balloon", 6),
               stress=f("stress", 7), point=f("point", 7), tired=f("tired", 7), tears=f("tears", 7, 0.15),
               evenly=f("evenly", 8),
               rounded=f("rounded", 9, 0.0),
               fday=f("every", 10),
               aisle=f("tell", 11, 0.0), comments=f("comments", 11))
    CUE["like"] = round(tl.find("like", S0[12]) - S0[12] - 0.05, 2)
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
                img.convert("RGB").save(f"{out}/win_{i:02d}_{tt}.png")
        sys.exit()
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), scene(i, TEXT[i])) for i, dd in enumerate(durs)]
    if ONLY:
        base.SCENES[:] = [s for i, s in enumerate(base.SCENES) if i in ONLY]
    ST, C_ = S0, CUE
    ev = [("whoosh", s) for s in ST[1:]]
    ev += [("whoosh", C_["mistake"] - 0.45), ("thud", C_["mistake"]), ("ding", C_["mistake"] + 0.05),
           ("whoosh", ST[1] + C_["fast"]), ("whoosh", ST[1] + C_["fast"] + 1.2), ("pop", ST[1] + C_["loved"]), ("pop", ST[1] + C_["loved"] + 0.1),
           ("thud", ST[2] + C_["square"] + 0.15),
           ("thud", ST[3] + C_["broke"]), ("whoosh", ST[3] + C_["broke"] + 0.1), ("thud", ST[3] + C_["grounded"] + 0.15), ("pop", ST[3] + C_["nobody"]),
           ("pop", ST[3] + C_["nobody"] + 0.15),
           ("thud", ST[5] + C_["crack"]), ("ding", ST[5] + C_["crack"] + 0.05),
           ("whoosh", ST[6] + C_["pressurized"]), ("pop", ST[6] + C_["balloon"]),
           ("ding", ST[7] + C_["point"]), ("thud", ST[7] + C_["tears"] + 0.15),
           ("ding", ST[8] + C_["evenly"]),
           ("thud", ST[9] + C_["rounded"]), ("ding", ST[9] + C_["rounded"] + 0.05),
           ("click", ST[10] + C_["fday"]),
           ("thud", ST[11] + C_["aisle"] - 0.5),
           ("click", ST[12] + C_["like"]), ("ding", ST[12] + C_["like"] + 0.03),
           ("click", ST[12] + C_["sub"]), ("ding", ST[12] + C_["sub"] + 0.35)]
    pk = ST[4] + C_["up"] - 0.3  # pump strokes
    k = 0
    while pk < ST[5] - 0.2:
        ev.append(("click", round(pk, 3)))
        k += 1
        pk += 1 / (1.2 + 0.8 * min(1.0, k / 4))
    last = -1
    for k in range(int(durs[10] * 60)):
        *_, hit = PH.ball_path(k / 60, 540, 1380, 0, 0, 1700, 70, e=0.45, mu=1.0)
        if hit > last + 0.05 and hit >= 0:
            ev.append(("pop", ST[10] + hit))
            last = hit
    ev += [("pop", ST[11] + C_["comments"] - 0.5 + i * 0.13) for i in range(10)]
    ev = [(k, round(v, 3)) for k, v in ev if 0 <= v < total]
    audio.music("music.wav", total, bpm=100, seed=61)
    audio.sfx("sfx.wav", total, ev)
    base.OUT = "base_window.mp4"
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_window.mp4", voice, "music.wav", "sfx.wav", OUTFILE)
    print("wrote", OUTFILE)
