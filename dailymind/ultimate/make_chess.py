"""YouTube Short #22: "The Queen Used to Be the WEAKEST Chess Piece?!" (Skia toon, unedited vidIQ "Chris" voice).

India (chaturanga, ~1,500 years ago) -> the army pieces -> Persia: "shah mat" = checkmate -> no queen, only the
king's advisor (one square) -> Europe: advisor becomes a (still weak) queen -> Spain, late 1400s: the queen can
fly across the board -> some historians link it to Queen Isabella -> "mad queen chess" -> strongest piece today.

New: chess pieces with faces on a perspective board (pieces map to real squares and scale with depth), a cartoon
army (elephant, horse, chariot with spinning wheel, foot soldiers), a king that topples on "checkmate", the queen
flying with a motion trail and knocking pieces over.
Usage: python make_chess.py final.mp4 [scene,...] [t1,...]   stills: STILLS_DIR=dir python make_chess.py x 0,1 1.0
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
sys.argv = [sys.argv[0], "base_chess.mp4"]
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

GOLD, RED, PURPLE = (255, 200, 60), (235, 60, 60), (215, 150, 255)
make_ketchup.SPLAT_COLOR = (250, 195, 50)
base.HOOK_SKIP = 0.0
base.CRF = 16
CUE = {}
VOICE_DIR = "../chess"
TAIL = 2.1  # room for the SUBSCRIBED + bell after the last word

RAJA = dict(skin=(195, 135, 95), hair="neat", hair_col=(30, 22, 20), coat=(190, 50, 60), trim=(240, 190, 80), pants=(240, 230, 210),
            hat="turban", turban_col=(245, 200, 90), mustache=True, nose="long")
SAGE = dict(skin=(205, 145, 105), hair="neat", hair_col=(30, 22, 20), beard=(40, 30, 28), coat=(60, 110, 150), trim=(230, 220, 200),
            pants=(240, 230, 210), hat="turban", turban_col=(240, 235, 225), nose="long")
ISABELLA = dict(skin=(245, 210, 185), hair="neat", hair_col=(150, 70, 40), coat=(150, 25, 45), dress=(150, 25, 45), crown=True,
                pearls=True, lips=True, nose="small")
PLAYER1 = dict(skin=(240, 200, 170), hair="neat", hair_col=(60, 40, 30), coat=(70, 90, 140), pants=(50, 50, 60), nose="small")
PLAYER2 = dict(skin=(200, 150, 115), hair="kid", hair_col=(30, 22, 18), coat=(160, 70, 60), pants=(60, 55, 55), glasses=True, nose="small")


def blinking(t, ph=0.0):
    return ((t + ph) % 3.3) < 0.11


def pop_in(t, at, dur=0.35):
    return out_back((t - at) / dur, 2.2) if t > at else 0.0


# ---------- chess pieces ----------

IVORY = ([C(255, 250, 235), C(235, 220, 190), C(180, 160, 130)], (120, 95, 70))
EBONY = ([C(110, 95, 100), C(55, 45, 50), C(20, 16, 18)], (10, 8, 10))


def _fill(c, path, white):
    cols, out = IVORY if white else EBONY
    b = path.getBounds()
    c.drawPath(path, P(Shader=lin((b.left(), b.top()), (b.right(), b.bottom()), cols, [0, 0.5, 1])))
    c.drawPath(path, S(C(*out), 5))


def piece(c, kind, x, y, s, white=True, t=0.0, face=None, rot=0.0, glow_col=None):
    """Chess piece standing with its base centre on (x, y). face = dict(eyes, mouth, look, blink) draws a cartoon face."""
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    c.drawOval(skia.Rect(-78, -14, 78, 14), P(C(0, 0, 0, 110), MaskFilter=blur(8)))
    if glow_col:
        glow(c, 0, -160, 220, glow_col, 55)
    base_ = rrect(-72, -42, 72, 0, 16)
    _fill(c, base_, white)
    _fill(c, oval(0, -46, 56, 13), white)
    top = {"pawn": 175, "rook": 250, "knight": 270, "bishop": 290, "queen": 330, "king": 360}[kind]
    if kind == "pawn":
        neck = skia.Path()
        neck.moveTo(-42, -48)
        neck.cubicTo(-30, -90, -24, -110, -22, -122)
        neck.lineTo(22, -122)
        neck.cubicTo(24, -110, 30, -90, 42, -48)
        neck.close()
        _fill(c, neck, white)
        _fill(c, oval(0, -124, 40, 10), white)
        _fill(c, oval(0, -158, 40, 40), white)
        fy = -158
    elif kind == "rook":
        body = skia.Path()
        body.moveTo(-50, -48)
        body.lineTo(-40, -200)
        body.lineTo(40, -200)
        body.lineTo(50, -48)
        body.close()
        _fill(c, body, white)
        tp = skia.Path()
        tp.moveTo(-62, -200)
        for k, (px, py) in enumerate([(-62, -250), (-38, -250), (-38, -228), (-12, -228), (-12, -250), (12, -250), (12, -228), (38, -228),
                                      (38, -250), (62, -250), (62, -200)]):
            tp.lineTo(px, py)
        tp.close()
        _fill(c, tp, white)
        fy = -140
    elif kind == "knight":
        body = skia.Path()  # horse head in profile, facing left
        body.moveTo(-52, -48)
        body.cubicTo(-56, -110, -30, -140, -60, -170)
        body.cubicTo(-92, -190, -100, -215, -78, -228)
        body.cubicTo(-50, -240, -10, -262, 10, -270)
        body.lineTo(22, -292)
        body.lineTo(34, -262)
        body.cubicTo(70, -230, 72, -140, 52, -48)
        body.close()
        _fill(c, body, white)
        cols, out = IVORY if white else EBONY
        for k in range(5):  # mane
            c.drawLine(30 + k * 6, -250 + k * 34, 52 + k * 4, -240 + k * 34, S(C(*out), 4))
        c.drawCircle(-82, -212, 4, P(C(*out)))  # nostril
        fy = -215
    elif kind == "bishop":
        neck = skia.Path()
        neck.moveTo(-44, -48)
        neck.cubicTo(-28, -110, -24, -150, -24, -168)
        neck.lineTo(24, -168)
        neck.cubicTo(24, -150, 28, -110, 44, -48)
        neck.close()
        _fill(c, neck, white)
        _fill(c, oval(0, -170, 44, 11), white)
        mitre = skia.Path()
        mitre.moveTo(0, -282)
        mitre.cubicTo(52, -250, 52, -195, 30, -176)
        mitre.lineTo(-30, -176)
        mitre.cubicTo(-52, -195, -52, -250, 0, -282)
        mitre.close()
        _fill(c, mitre, white)
        c.drawLine(10, -255, 26, -225, S(C(*(IVORY if white else EBONY)[1]), 5))
        _fill(c, oval(0, -287, 11, 11), white)
        fy = -215
    else:  # queen / king
        tall = 30 if kind == "king" else 0
        body = skia.Path()
        body.moveTo(-54, -48)
        body.cubicTo(-34, -120, -28, -190 - tall, -40, -238 - tall)
        body.lineTo(40, -238 - tall)
        body.cubicTo(28, -190 - tall, 34, -120, 54, -48)
        body.close()
        _fill(c, body, white)
        _fill(c, oval(0, -130 - tall * 0.5, 40, 10), white)
        _fill(c, oval(0, -240 - tall, 50, 12), white)
        if kind == "queen":
            cr = skia.Path()
            cr.moveTo(-46, -244)
            for px, py in [(-56, -298), (-28, -268), (0, -308), (28, -268), (56, -298), (46, -244)]:
                cr.lineTo(px, py)
            cr.close()
            _fill(c, cr, white)
            for px, py in [(-56, -302), (0, -314), (56, -302)]:
                _fill(c, oval(px, py, 9, 9), white)
        else:
            _fill(c, rrect(-36, -300, 36, -268, 10), white)
            _fill(c, rrect(-8, -360, 8, -296, 3), white)
            _fill(c, rrect(-26, -342, 26, -328, 3), white)
        fy = -185 - tall * 0.5
    if face:
        fx = -18 if kind == "knight" else 0
        ink = C(30, 22, 18) if white else C(250, 245, 235)
        eyes, mouth_ = face.get("eyes", "open"), face.get("mouth", "smile")
        lx, ly = face.get("look", (0, 0))
        for side in (-1, 1):
            ex = fx + side * 17
            if face.get("blink") or eyes == "closed":
                c.drawArc(skia.Rect(ex - 10, fy - 6, ex + 10, fy + 8), 200, 140, False, S(ink, 4))
            else:
                hh = 15 if eyes == "wide" else 12
                c.drawOval(skia.Rect(ex - 10, fy - hh, ex + 10, fy + hh), P(C(255, 255, 255)))
                c.drawCircle(ex + lx * 4, fy + ly * 4, 6 if eyes == "wide" else 7, P(C(30, 22, 18)))
                c.drawOval(skia.Rect(ex - 10, fy - hh, ex + 10, fy + hh), S(C(30, 22, 18), 2.5))
            if eyes == "sad":
                c.drawLine(ex - 11, fy - 15 - side * 3, ex + 11, fy - 15 + side * 3, S(ink, 4))
            if eyes == "angry":
                c.drawLine(ex - 11, fy - 15 + side * 4, ex + 11, fy - 15 - side * 4, S(ink, 4))
        my = fy + 28
        if mouth_ == "smile":
            c.drawArc(skia.Rect(fx - 14, my - 10, fx + 14, my + 6), 20, 140, False, S(ink, 4))
        elif mouth_ == "frown":
            c.drawArc(skia.Rect(fx - 14, my, fx + 14, my + 14), 200, 140, False, S(ink, 4))
        elif mouth_ == "O":
            c.drawOval(skia.Rect(fx - 8, my - 6, fx + 8, my + 12), P(C(110, 25, 35)))
        elif mouth_ == "grin":
            c.drawArc(skia.Rect(fx - 18, my - 12, fx + 18, my + 10), 10, 160, True, P(C(110, 25, 35)))
        if face.get("sweat"):
            u = (t * 1.2) % 1
            c.drawCircle(fx + 40, fy - 20 + 60 * u, 7, P(C(170, 215, 255, int(230 * (1 - u)))))
    c.restore()
    return top * s


# ---------- the board in perspective ----------

class Board:
    def __init__(self, cx, y_far, y_near, w_far, w_near, light=(235, 215, 175), dark=(120, 75, 45)):
        self.cx, self.y0, self.y1, self.w0, self.w1 = cx, y_far, y_near, w_far, w_near
        self.light, self.dark = light, dark

    def _row(self, r):  # r 0 (far edge) .. 8 (near edge), with perspective spacing
        u = r / 8
        k = u * (1 + 0.35 * (1 - u))  # rows grow toward the viewer
        k = (math.pow(1.6, u) - 1) / 0.6
        y = self.y0 + (self.y1 - self.y0) * k
        w = self.w0 + (self.w1 - self.w0) * k
        return y, w

    def corner(self, col, r):
        y, w = self._row(r)
        return self.cx - w / 2 + w * col / 8, y

    def sq(self, col, row):
        """Centre of square (col 0..7 left->right, row 0..7 far->near) and a depth scale for pieces."""
        y0, w0 = self._row(row)
        y1, w1 = self._row(row + 1)
        y, w = (y0 + y1) / 2, (w0 + w1) / 2
        return self.cx - w / 2 + w * (col + 0.5) / 8, y + (y1 - y0) * 0.1, w / self.w1

    def draw(self, c, hl=None):
        x0, y0 = self.corner(0, 0)
        x1, _ = self.corner(8, 0)
        x2, y2 = self.corner(8, 8)
        x3, _ = self.corner(0, 8)
        rim = skia.Path()
        rim.moveTo(x0 - 18, y0 - 12)
        rim.lineTo(x1 + 18, y0 - 12)
        rim.lineTo(x2 + 30, y2 + 20)
        rim.lineTo(x3 - 30, y2 + 20)
        rim.close()
        c.drawPath(rim, P(C(0, 0, 0, 150), MaskFilter=blur(20)))
        c.drawPath(rim, P(Shader=lin((0, y0), (0, y2), [C(90, 55, 30), C(60, 35, 20)])))
        c.drawRect(skia.Rect(x3 - 30, y2 + 20, x2 + 30, y2 + 50), P(C(45, 26, 15)))
        for r in range(8):
            for col in range(8):
                p = skia.Path()
                a = self.corner(col, r)
                b = self.corner(col + 1, r)
                d = self.corner(col + 1, r + 1)
                e = self.corner(col, r + 1)
                p.moveTo(*a)
                p.lineTo(*b)
                p.lineTo(*d)
                p.lineTo(*e)
                p.close()
                col_ = self.light if (r + col) % 2 == 0 else self.dark
                c.drawPath(p, P(C(*col_)))
                if hl and (col, r) in hl:
                    c.drawPath(p, P(C(*hl[(col, r)])))
        c.drawPath(rim, S(C(40, 22, 12), 4))


# ---------- army (chaturanga) ----------

def elephant(c, x, y, s, t, k=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s * k, s * k)
    sw = math.sin(t * 2.5)
    for lx in (-70, -30, 30, 70):
        blob(c, rrect(lx - 20, -90, lx + 20, 0, 10), (150, 150, 160), 1.2, 0.7)
    blob(c, oval(0, -130, 115, 75), (160, 160, 170), 1.25, 0.65)
    blob(c, rrect(-50, -200, 50, -150, 12), (200, 60, 70), 1.3, 0.7)  # saddle cloth
    c.drawLine(-40, -170, 40, -170, S(C(240, 190, 80), 6))
    hx, hy = -110, -150
    trunk = skia.Path()
    trunk.moveTo(hx - 30, hy + 10)
    trunk.cubicTo(hx - 70, hy + 60, hx - 60 + 20 * sw, hy + 120, hx - 90 + 30 * sw, hy + 140)
    c.drawPath(trunk, S(OUT, 34))
    c.drawPath(trunk, S(C(160, 160, 170), 26))
    blob(c, oval(hx, hy, 55, 50), (165, 165, 175), 1.25, 0.65)
    c.save()
    c.translate(hx + 30, hy - 5)
    c.rotate(8 * math.sin(t * 3))
    blob(c, oval(20, 10, 40, 52), (150, 150, 160), 1.2, 0.7)
    c.restore()
    c.drawLine(hx - 25, hy + 30, hx - 55, hy + 45, S(C(250, 245, 230), 9))
    c.drawCircle(hx - 15, hy - 12, 7, P(C(30, 20, 20)))
    c.restore()


def horse(c, x, y, s, t, k=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s * k, s * k)
    gal = math.sin(t * 9)
    for i, lx in enumerate((-60, -35, 35, 60)):
        c.save()
        c.translate(lx, -85)
        c.rotate(18 * gal * (1 if i % 2 else -1))
        blob(c, rrect(-12, 0, 12, 85, 8), (130, 85, 50), 1.2, 0.7)
        blob(c, rrect(-14, 70, 14, 88, 5), (50, 35, 30), 1.2, 0.7)  # hooves
        c.restore()
    tail = skia.Path()
    tail.moveTo(95, -120)
    tail.cubicTo(150, -110 + 15 * gal, 150, -60, 125, -30)
    c.drawPath(tail, S(C(60, 35, 20), 16))
    blob(c, oval(0, -115, 105, 52), (150, 100, 60), 1.25, 0.65)
    neck = skia.Path()  # thick neck leaning forward
    neck.moveTo(-60, -150)
    neck.cubicTo(-90, -190, -115, -215, -130, -235)
    neck.lineTo(-170, -205)
    neck.cubicTo(-140, -170, -120, -130, -95, -95)
    neck.close()
    blob(c, neck, (150, 100, 60), 1.25, 0.65)
    c.save()  # long head pointing down-forward
    c.translate(-175, -215)
    c.rotate(35)
    blob(c, oval(0, 0, 62, 30), (155, 105, 65), 1.25, 0.65)
    blob(c, oval(-45, 6, 20, 18), (120, 80, 50), 1.2, 0.7)  # muzzle
    c.drawCircle(-50, 2, 4, P(C(30, 20, 15)))
    c.drawCircle(8, -8, 7, P(C(30, 20, 15)))  # eye
    c.restore()
    for side in (0, 14):  # ears
        ear = skia.Path()
        ear.moveTo(-150 + side, -248)
        ear.lineTo(-140 + side, -282)
        ear.lineTo(-128 + side, -246)
        ear.close()
        blob(c, ear, (150, 100, 60), 1.2, 0.7)
    for k_ in range(6):  # mane along the neck
        mx, my = -128 + k_ * 14, -238 + k_ * 20
        c.drawLine(mx, my, mx + 22, my - 8 + 4 * math.sin(t * 6 + k_), S(C(60, 35, 20), 12))
    c.restore()

def chariot(c, x, y, s, t, k=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s * k, s * k)
    blob(c, rrect(-90, -150, 70, -60, 14), (200, 150, 60), 1.3, 0.65)
    c.drawLine(-110, -70, -190, -80, S(C(110, 70, 40), 10))
    c.save()
    c.translate(0, -55)
    c.rotate(-math.degrees(t * 6))
    c.drawCircle(0, 0, 55, S(C(90, 55, 30), 12))
    for i in range(8):
        a = i / 8 * 2 * math.pi
        c.drawLine(0, 0, math.cos(a) * 52, math.sin(a) * 52, S(C(120, 80, 45), 6))
    c.drawCircle(0, 0, 12, P(C(240, 190, 80)))
    c.restore()
    c.drawLine(50, -150, 50, -230, S(C(110, 70, 40), 6))
    flag = skia.Path()
    flag.moveTo(50, -230)
    flag.quadTo(85, -222 + 6 * math.sin(t * 6), 110, -215)
    flag.lineTo(50, -200)
    flag.close()
    c.drawPath(flag, P(C(220, 50, 60)))
    c.restore()


def snail(c, x, y, s, t):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    blob(c, oval(0, -14, 70, 16), (150, 190, 120), 1.2, 0.7)
    blob(c, oval(10, -60, 45, 45), (200, 140, 80), 1.3, 0.65)
    c.drawArc(skia.Rect(-10, -80, 30, -40), 0, 300, False, S(C(140, 90, 50), 5))
    for side in (-1, 1):
        c.drawLine(-55, -25, -70 + side * 6, -70 + 5 * math.sin(t * 4 + side), S(C(120, 160, 100), 5))
        c.drawCircle(-70 + side * 6, -72 + 5 * math.sin(t * 4 + side), 6, P(C(30, 30, 30)))
    c.restore()


# ---------- scenes ----------

def stage_bg(c, top, mid, bot):
    c.drawPaint(P(Shader=lin((0, 0), (0, H), [C(*top), C(*mid), C(*bot)])))


def art_hook(c, t):
    stage_bg(c, (20, 14, 30), (60, 30, 60), (15, 10, 20))
    glow(c, 540, 1350, 650, (200, 120, 255), 70)
    b = Board(540, 1180, 1820, 640, 1060)
    hl = {}
    one = CUE["one"]
    if t > one - 0.2:  # the single square she may step to lights up
        hl[(4, 5)] = (120, 255, 160, int(150 + 60 * math.sin(t * 6)))
    b.draw(c, hl)
    big = [((1, 3), "rook", False), ((6, 3), "knight", False), ((2, 2), "bishop", False), ((5, 2), "king", False),
           ((0, 6), "rook", True), ((7, 6), "knight", True), ((2, 7), "bishop", True)]
    for (cl, rw), kind, wh in sorted(big, key=lambda q: q[0][1]):
        x, y, k = b.sq(cl, rw)
        face = dict(eyes="angry", mouth="grin", look=(1 if x < 540 else -1, 0.5), blink=blinking(t, cl))
        piece(c, kind, x, y + 6 * math.sin(t * 2 + cl), 1.04 * k * (1 + 0.05 * math.sin(t * 3 + rw)), wh, t, face)
    # the tiny, nervous queen hops one square on "one square"
    hop = ease((t - one) / 0.45)
    x0, y0, k0 = b.sq(4, 6)
    x1, y1, k1 = b.sq(4, 5)
    x, y, k = x0 + (x1 - x0) * hop, y0 + (y1 - y0) * hop - 70 * math.sin(math.pi * hop), k0 + (k1 - k0) * hop
    weak = CUE["weak"]
    shrink = 1 - 0.25 * ease((t - weak) / 0.3)
    c.drawOval(skia.Rect(x - 120 * k, y - 40 * k, x + 120 * k, y + 30 * k), P(C(255, 240, 200, 90), MaskFilter=blur(18)))
    beam = skia.Path()
    beam.moveTo(x - 30, 0)
    beam.lineTo(x + 30, 0)
    beam.lineTo(x + 130 * k, y + 20)
    beam.lineTo(x - 130 * k, y + 20)
    beam.close()
    c.drawPath(beam, P(C(255, 240, 210, 40), MaskFilter=blur(25)))
    piece(c, "queen", x, y, 1.18 * k * shrink, True, t, dict(eyes="sad" if t > weak else "open", mouth="frown" if t > weak else "smile",
                                                            look=(0, -0.6), sweat=t > weak, blink=blinking(t, 0.3)), rot=4 * math.sin(t * 5) if t > weak else 0)
    q = pop_in(t, CUE["changed"])
    if q > 0:
        c.drawString("?", x + 70, y - 330 * k * 1.18, skia.Font(FB, 110 * q), P(C(255, 230, 120)))


def art_india(c, t):
    stage_bg(c, (40, 20, 50), (210, 100, 70), (255, 190, 100))
    glow(c, 540, 1250, 600, (255, 210, 140), 140)
    c.drawCircle(540, 1180, 140, P(Shader=rad(540, 1180, 140, [C(255, 245, 200), C(255, 170, 70)])))
    sky = skia.Path()
    sky.moveTo(0, 1420)
    for x, kind in ((90, "dome"), (300, "tower"), (540, "bigdome"), (780, "tower"), (990, "dome")):
        if kind in ("dome", "bigdome"):
            r = 150 if kind == "bigdome" else 90
            sky.lineTo(x - r, 1420)
            sky.lineTo(x - r, 1280)
            sky.cubicTo(x - r, 1280 - r * 1.3, x + r, 1280 - r * 1.3, x + r, 1280)
            sky.lineTo(x + r, 1420)
        else:
            sky.lineTo(x - 25, 1420)
            sky.lineTo(x - 25, 1120)
            sky.lineTo(x, 1080)
            sky.lineTo(x + 25, 1120)
            sky.lineTo(x + 25, 1420)
    sky.lineTo(W, 1420)
    sky.lineTo(W, H)
    sky.lineTo(0, H)
    sky.close()
    c.drawPath(sky, P(C(110, 45, 60)))
    c.drawRect(skia.Rect(0, 1600, W, H), P(Shader=lin((0, 1600), (0, H), [C(150, 80, 50), C(90, 45, 30)])))
    # two players at a low table with a board
    war = CUE["war"]
    rp = dict(hands=[(-20, 150), (140, 70)], eyes="open", brows="smug", mouth="grin", look=(1, 0.5), tilt=3 * math.sin(t * 1.6), blink=blinking(t, 0.2))
    sp = dict(hands=[(-120, 70), (20, 150)], eyes="wide" if t > war else "open", brows="up", mouth="O" if t > war else "smile", look=(-1, 0.5),
              tilt=-3 * math.sin(t * 1.4), blink=blinking(t, 1.1))
    person(c, 200, 1860, 1.25, RAJA, rp, t)
    person(c, 880, 1860, 1.25, SAGE, sp, t)
    blob(c, rrect(330, 1640, 750, 1700, 10), (130, 75, 40))
    c.drawRect(skia.Rect(360, 1700, 390, 1860), P(C(90, 50, 25)))
    c.drawRect(skia.Rect(690, 1700, 720, 1860), P(C(90, 50, 25)))
    b = Board(540, 1540, 1660, 300, 420, (240, 220, 170), (150, 60, 50))
    b.draw(c)
    mv = ease((t - war) / 0.6)
    for (cl, rw), kind, wh in [((1, 1), "rook", False), ((6, 1), "king", False), ((2, 6), "knight", True), ((5, 6), "pawn", True)]:
        if kind == "knight":  # a piece moves on "war"
            x0, y0, k0 = b.sq(2, 6)
            x1, y1, k1 = b.sq(3, 4)
            x, y, k = x0 + (x1 - x0) * mv, y0 + (y1 - y0) * mv - 40 * math.sin(math.pi * mv), k0
        else:
            x, y, k = b.sq(cl, rw)
        piece(c, kind, x, y, 0.27 * k, wh, t)
    if t > CUE["chat"]:
        for kk in range(6):
            a = t * 1.4 + kk * 1.05
            sparkle(c, 540 + math.cos(a) * 260, 1500 + math.sin(a) * 120, 8, 200)


def art_army(c, t):
    stage_bg(c, (30, 25, 40), (120, 80, 60), (60, 40, 30))
    glow(c, 540, 1300, 600, (255, 190, 120), 110)
    c.drawRect(skia.Rect(0, 1450, W, H), P(Shader=lin((0, 1450), (0, H), [C(170, 130, 80), C(110, 80, 45)])))
    for k in range(8):  # chequered ground
        for j in range(4):
            if (k + j) % 2:
                c.drawRect(skia.Rect(k * 135, 1450 + j * 118, k * 135 + 135, 1568 + j * 118), P(C(0, 0, 0, 40)))
    e, h, ch, so = CUE["eleph"], CUE["horses"], CUE["chariots"], CUE["soldiers"]

    def poof(x, y, at, r=160):
        k = (t - at + 0.1) / 0.5
        if 0 < k < 1:
            for j in range(10):
                a = j / 10 * 2 * math.pi
                rr = 40 + r * ease(k)
                c.drawCircle(x + math.cos(a) * rr, y + math.sin(a) * rr * 0.6, 34 * (1 - k) + 8,
                             P(C(255, 245, 230, int(200 * (1 - k))), MaskFilter=blur(10)))

    def standing(kind, x, y, s_, at, ph):
        """The chess piece waits in place, then shrinks away as its army unit pops in."""
        gone = ease((t - at + 0.05) / 0.2)
        if gone < 1:
            piece(c, kind, x, y - abs(math.sin(t * 3 + ph)) * 6, s_ * (1 - gone), True, t,
                  dict(eyes="open", mouth="smile", look=(0, -0.3), blink=blinking(t, ph)))

    standing("bishop", 330, 1620, 1.05, e, 0.1)
    standing("knight", 800, 1620, 1.05, h, 0.7)
    standing("rook", 330, 1890, 0.95, ch, 1.3)
    for i in range(4):
        standing("pawn", 600 + i * 110, 1890, 0.7, so + i * 0.08, 2 + i)
    elephant(c, 330, 1620, 1.2, t, pop_in(t, e))
    horse(c, 800, 1620, 1.2, t, pop_in(t, h))
    march = t - ch
    chariot(c, 330 + (40 * math.sin(t * 2) if march > 0 else 0), 1890, 1.1, t, pop_in(t, ch))
    for i in range(4):
        k = pop_in(t, so + i * 0.08)
        if k <= 0:
            continue
        x = 600 + i * 110
        step = (t - so) * 9 + i
        pose = dict(walk=step, hands=[(-20, 150), (30, 60)], eyes="open", brows="angry", mouth="grin", look=(-1, 0), blink=blinking(t, i))
        c.save()
        c.translate(x, 1880)
        c.scale(k, k)
        c.translate(-x, -1880)
        person(c, x, 1880, 0.62, dict(skin=(200, 150, 110), hair="neat", hair_col=(30, 22, 20), coat=(170, 60, 50), pants=(230, 220, 200),
                                       hat="turban", turban_col=(240, 230, 210), nose="small"), pose, t)
        hx, hy = hand_pos(x, 1880, 0.62, pose, 1)
        c.drawLine(hx, hy + 60, hx, hy - 170, S(C(110, 70, 40), 6))  # spear
        tip = skia.Path()
        tip.moveTo(hx, hy - 200)
        tip.lineTo(hx - 9, hy - 170)
        tip.lineTo(hx + 9, hy - 170)
        tip.close()
        c.drawPath(tip, P(C(200, 200, 210)))
        c.restore()
    poof(330, 1520, e)
    poof(800, 1520, h)
    poof(330, 1800, ch, 130)
    poof(760, 1800, so, 200)

def art_persia(c, t):
    stage_bg(c, (15, 20, 45), (40, 60, 110), (15, 20, 40))
    for k in range(3):  # blue-tiled arches
        x = 180 + k * 360
        c.drawRect(skia.Rect(x - 170, 950, x + 170, 1500), P(C(30, 70, 120)))
        arch = skia.Path()
        arch.moveTo(x - 120, 1500)
        arch.lineTo(x - 120, 1120)
        arch.cubicTo(x - 120, 1000, x, 980, x, 960)
        arch.cubicTo(x, 980, x + 120, 1000, x + 120, 1120)
        arch.lineTo(x + 120, 1500)
        arch.close()
        c.drawPath(arch, P(Shader=lin((0, 960), (0, 1500), [C(20, 25, 50), C(60, 50, 80)])))
        c.drawPath(arch, S(C(220, 190, 110), 8))
        for j in range(6):
            c.drawCircle(x - 150 + j * 60, 980, 10, P(C(90, 170, 210)))
    trapped, shah, check = CUE["trapped"], CUE["shah"], CUE["check"]
    b = Board(540, 1300, 1860, 700, 1080, (230, 215, 180), (60, 90, 130))
    hl = {}
    if t > trapped:
        for sq_ in [(3, 3), (4, 3), (5, 3), (3, 4), (5, 4), (4, 4)]:
            hl[sq_] = (255, 70, 70, int(110 + 50 * math.sin(t * 8)))
    b.draw(c, hl)
    attackers = [((1, 3), "rook", True), ((6, 6), "knight", True), ((2, 6), "queen", True)]
    for (cl, rw), kind, wh in attackers:
        x, y, k = b.sq(cl, rw)
        piece(c, kind if kind != "queen" else "bishop", x, y, 0.95 * k, wh, t,
              dict(eyes="angry", mouth="grin", look=(1 if x < 540 else -1, -0.3), blink=blinking(t, cl)))
    x, y, k = b.sq(4, 4)
    fall = ease((t - check - 0.05) / 0.5)
    shake = (5 * math.sin(t * 40) if trapped < t < check else 0)
    piece(c, "king", x + shake + 60 * fall, y, 1.04 * k, False, t,
          dict(eyes="wide" if t < check else "closed", mouth="O" if t > trapped else "smile", sweat=t > trapped, look=(0, 0)),
          rot=85 * fall)
    if t > shah:  # little speech bubble "shah mat!" from the player side
        q = pop_in(t, shah)
        c.save()
        c.translate(820, 1180)
        c.scale(q, q)
        c.drawRoundRect(skia.Rect(-150, -60, 150, 60), 40, 40, P(C(255, 255, 255)))
        c.drawRoundRect(skia.Rect(-150, -60, 150, 60), 40, 40, S(OUT, 4))
        tail = skia.Path()
        tail.moveTo(-40, 55)
        tail.lineTo(-90, 120)
        tail.lineTo(10, 58)
        tail.close()
        c.drawPath(tail, P(C(255, 255, 255)))
        c.drawString("SHAH MAT!", -125, 16, skia.Font(FB, 46), P(C(180, 40, 50)))
        c.restore()


def art_advisor(c, t):
    stage_bg(c, (25, 18, 15), (75, 50, 35), (25, 18, 15))
    glow(c, 540, 1400, 600, (255, 190, 120), 100)
    b = Board(540, 1250, 1860, 640, 1080)
    hl = {(3, 4): (120, 255, 160, 90)}
    b.draw(c, hl)
    q = CUE["noqueen"]
    x, y, k = b.sq(5, 4)
    piece(c, "king", x, y, 1.18 * k, True, t, dict(eyes="open", mouth="smile", look=(-1, 0), blink=blinking(t, 0.5)))
    if t > q:  # an empty spot where a queen would be: dashed outline + "?"
        xq, yq, kq = b.sq(4, 4)
        a = int(200 * ease((t - q) / 0.3))
        c.drawCircle(xq, yq - 200 * kq, 95 * kq, P(C(255, 255, 255, a // 4)))
        c.drawCircle(xq, yq - 200 * kq, 95 * kq, P(C(255, 255, 255, a), Style=skia.Paint.kStroke_Style, StrokeWidth=5,
                                                         PathEffect=skia.DashPathEffect.Make([14, 10], t * 30)))
        c.drawString("?", xq - 26, yq - 165 * kq, skia.Font(FB, 96), P(C(255, 255, 255, a)))
    # the advisor (a bishop-shaped old piece with a beard) crawling one square, panting
    adv, crawl = CUE["advisor"], CUE["crawl"]
    u = ease((t - crawl) / 2.2)
    x0, y0, k0 = b.sq(3, 5)
    x1, y1, k1 = b.sq(3, 4)
    ax, ay = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    wob = 3 * math.sin(t * 10) if crawl < t < crawl + 2.2 else 0
    vis = pop_in(t, adv - 0.1)
    if vis > 0:
        piece(c, "bishop", ax, ay, 1.04 * k0 * vis, True, t, dict(eyes="closed" if crawl < t < crawl + 2.2 else "open", mouth="O" if crawl < t else "smile",
                                                                  sweat=crawl < t, look=(0, -1)), rot=wob)
        bx, by = ax, ay - 160 * 1.05 * k0 * vis  # white beard on the advisor
        p = skia.Path()
        p.moveTo(bx - 48 * vis, by)
        p.cubicTo(bx - 38 * vis, by + 130 * vis, bx + 38 * vis, by + 130 * vis, bx + 48 * vis, by)
        p.close()
        c.drawPath(p, P(C(250, 250, 250)))
        c.drawPath(p, S(C(160, 160, 160), 3))
    # a snail overtakes him
    if t > crawl:
        snail(c, -100 + 260 * (t - crawl), 1840, 1.1, t)


def art_europe(c, t):
    stage_bg(c, (20, 20, 35), (60, 55, 80), (25, 22, 30))
    for k in range(9):  # stone castle hall
        for j in range(14):
            c.drawRoundRect(skia.Rect(k * 130 + (65 if j % 2 else 0) - 60, 880 + j * 70, k * 130 + (65 if j % 2 else 0) + 60, 940 + j * 70),
                            10, 10, P(C(70 + (k * 5 + j * 3) % 15, 68, 85)))
    for x in (140, 940):  # banners
        c.drawRect(skia.Rect(x - 70, 920, x + 70, 1300), P(C(150, 30, 45)))
        c.drawCircle(x, 1080, 40, P(C(240, 190, 80)))
        c.drawLine(x - 90, 920, x + 90, 920, S(C(90, 60, 30), 10))
        candle(c, x, 1420, t, x, 1.2)
    b = Board(540, 1360, 1860, 620, 1000, (230, 220, 200), (90, 80, 110))
    b.draw(c)
    qc, weak = CUE["queen5"], CUE["weak5"]
    x, y, k = b.sq(4, 4)
    morph = ease((t - qc + 0.1) / 0.4)
    sc = 1.35 * k
    if morph < 0.5:
        piece(c, "bishop", x, y, sc * (1 - morph * 0.6), True, t, dict(eyes="closed", mouth="smile", look=(0, 0)))
    else:
        sad = t > weak
        piece(c, "queen", x, y, sc * (0.7 + 0.3 * ease((t - qc - 0.1) / 0.3)) * (0.9 if sad else 1), True, t,
              dict(eyes="sad" if sad else "wide", mouth="frown" if sad else "grin", sweat=sad, look=(0, 0.3 if sad else -0.5),
                   blink=blinking(t, 0.2)), rot=-6 if sad else 0)
    if qc - 0.1 < t < qc + 0.6:  # poof
        k_ = (t - qc + 0.1) / 0.7
        for j in range(10):
            a = j / 10 * 2 * math.pi
            r = 60 + 220 * ease(k_)
            c.drawCircle(x + math.cos(a) * r, y - 380 * k + math.sin(a) * r * 0.7, 40 * (1 - k_) + 8,
                         P(C(255, 245, 230, int(200 * (1 - k_))), MaskFilter=blur(10)))
    for (cl, rw), kind in [((1, 2), "rook"), ((6, 2), "knight"), ((2, 6), "pawn"), ((6, 6), "pawn")]:
        xx, yy, kk = b.sq(cl, rw)
        laugh = t > weak
        piece(c, kind, xx, yy + (-abs(math.sin(t * 8 + cl)) * 8 if laugh else 0), 0.95 * kk, False, t,
              dict(eyes="closed" if laugh else "open", mouth="grin" if laugh else "smile", look=(1 if xx < 540 else -1, 0)))


def art_spain(c, t):
    stage_bg(c, (25, 15, 40), (170, 70, 70), (250, 170, 90))
    glow(c, 540, 1200, 650, (255, 200, 130), 130)
    for k in range(5):  # Moorish arches
        x = 110 + k * 215
        c.drawRect(skia.Rect(x - 100, 960, x + 100, 1400), P(C(200, 140, 100)))
        arch = skia.Path()
        arch.moveTo(x - 70, 1400)
        arch.lineTo(x - 70, 1080)
        arch.cubicTo(x - 90, 1010, x - 30, 990, x, 975)
        arch.cubicTo(x + 30, 990, x + 90, 1010, x + 70, 1080)
        arch.lineTo(x + 70, 1400)
        arch.close()
        c.drawPath(arch, P(C(70, 30, 50)))
    b = Board(540, 1330, 1860, 680, 1080, (240, 225, 190), (160, 60, 50))
    b.draw(c)
    ch, fly = CUE["changed6"], CUE["fly"]
    # pieces that get knocked over by the flying queen
    knocked = []
    for (cl, rw), kind in [((2, 2), "pawn"), ((5, 3), "knight"), ((1, 1), "rook"), ((6, 1), "bishop")]:
        x, y, k = b.sq(cl, rw)
        hit = fly + 0.2 + 0.12 * len(knocked)
        f = ease((t - hit) / 0.35)
        piece(c, kind, x + 50 * f * (1 if x > 540 else -1), y, 0.91 * k, False, t,
              dict(eyes="wide" if t > ch else "open", mouth="O" if t > ch else "smile", look=(0, 0)), rot=80 * f * (1 if x > 540 else -1))
        knocked.append(kind)
    # the queen powers up on "everything changed", then flies across the board on "fly"
    p0 = b.sq(1, 7)
    p1 = b.sq(6, 2)
    p2 = b.sq(2, 1)
    u = ease((t - fly) / 1.2)
    if u < 0.5:
        a = u / 0.5
        x = p0[0] + (p1[0] - p0[0]) * a
        y = p0[1] + (p1[1] - p0[1]) * a - 220 * math.sin(math.pi * a)
        k = p0[2] + (p1[2] - p0[2]) * a
    else:
        a = (u - 0.5) / 0.5
        x = p1[0] + (p2[0] - p1[0]) * a
        y = p1[1] + (p2[1] - p1[1]) * a - 180 * math.sin(math.pi * a)
        k = p1[2] + (p2[2] - p1[2]) * a
    power = ease((t - ch) / 0.4)
    if 0 < u < 1:  # motion trail
        for j in range(8):
            uu = max(0, u - j * 0.03)
            if uu < 0.5:
                aa = uu / 0.5
                tx = p0[0] + (p1[0] - p0[0]) * aa
                ty = p0[1] + (p1[1] - p0[1]) * aa - 220 * math.sin(math.pi * aa)
            else:
                aa = (uu - 0.5) / 0.5
                tx = p1[0] + (p2[0] - p1[0]) * aa
                ty = p1[1] + (p2[1] - p1[1]) * aa - 180 * math.sin(math.pi * aa)
            c.drawCircle(tx, ty - 230 * k, 90 * k * (1 - j / 8), P(C(255, 220, 120, int(160 * (1 - j / 8))), MaskFilter=blur(10)))
    wait = 1 - power
    piece(c, "queen", x, y - abs(math.sin(t * 4)) * 10 * wait, (1.15 + 0.2 * power) * k, True, t,
          dict(eyes="angry" if power > 0.5 else "sad", mouth="grin" if power > 0.5 else "frown", look=(1, -0.3), sweat=wait > 0.5,
               blink=blinking(t, 0.9)), rot=4 * math.sin(t * 6) * wait,
          glow_col=(255, 210, 120) if power > 0.3 else None)
    if power > 0:
        for j in range(5):  # crackling energy
            a = t * 3 + j * 1.25
            sparkle(c, x + math.cos(a) * 200 * k, y - 320 * k + math.sin(a) * 250 * k, 9, int(220 * power))


def art_isabella(c, t):
    stage_bg(c, (25, 10, 20), (90, 30, 40), (30, 10, 15))
    for x in (140, 940):  # gold columns + red drapes
        c.drawRect(skia.Rect(x - 45, 900, x + 45, 1700), P(Shader=lin((x - 45, 0), (x + 45, 0), [C(120, 80, 30), C(240, 200, 110), C(110, 70, 25)])))
    for k in range(5):
        c.drawLine(200 + k * 170, 900, 230 + k * 170, 1600, S(C(120, 20, 35, 120), 40))
    c.drawRect(skia.Rect(0, 1650, W, H), P(Shader=lin((0, 1650), (0, H), [C(110, 40, 40), C(50, 15, 20)])))
    isa = CUE["isabella"]
    spot = ease((t - isa + 0.2) / 0.4)
    beam = skia.Path()
    beam.moveTo(320, 880)
    beam.lineTo(480, 880)
    beam.lineTo(600, 1900)
    beam.lineTo(100, 1900)
    beam.close()
    c.drawPath(beam, P(C(255, 240, 200, int(30 + 50 * spot)), MaskFilter=blur(30)))
    pose = dict(hands=[(-30, 150), (110, 40 - 40 * spot)], eyes="open", brows="smug", mouth="grin" if spot > 0.5 else "smile", look=(1, -0.2),
                tilt=2 * math.sin(t * 1.5), blink=blinking(t, 0.4))
    person(c, 380, 1860, 1.45, ISABELLA, pose, t)
    # a giant queen piece beside her mirrors her pose
    piece(c, "queen", 790, 1850, 1.35, True, t, dict(eyes="open", mouth="grin" if spot > 0.5 else "smile", look=(-1, 0), blink=blinking(t, 1.4)),
          glow_col=(255, 220, 140) if spot > 0 else None)
    if spot > 0:
        for j in range(8):
            a = t * 1.2 + j * 0.78
            sparkle(c, 580 + math.cos(a) * 330, 1350 + math.sin(a) * 260, 9, int(210 * spot))


def art_mad(c, t):
    stage_bg(c, (30, 10, 40), (80, 20, 70), (20, 8, 25))
    for k in range(12):  # wild spinning rays
        a = k / 12 * 2 * math.pi + t * 0.6
        p = skia.Path()
        p.moveTo(540, 1350)
        p.lineTo(540 + math.cos(a) * 1300, 1350 + math.sin(a) * 1300)
        p.lineTo(540 + math.cos(a + 0.18) * 1300, 1350 + math.sin(a + 0.18) * 1300)
        p.close()
        c.drawPath(p, P(C(255, 120, 220, 30)))
    b = Board(540, 1260, 1860, 660, 1060, (240, 220, 240), (110, 50, 120))
    b.draw(c)
    # the queen zig-zags all over the board; pieces bounce off
    path_pts = [(1, 6), (6, 1), (6, 6), (1, 1), (4, 3), (7, 7), (0, 4), (5, 0)]
    seg_t = 0.45
    u = (t % (seg_t * (len(path_pts) - 1))) / seg_t
    i = int(u)
    a = u - i
    pa, pb = b.sq(*path_pts[i]), b.sq(*path_pts[(i + 1) % len(path_pts)])
    x = pa[0] + (pb[0] - pa[0]) * ease(a)
    y = pa[1] + (pb[1] - pa[1]) * ease(a) - 150 * math.sin(math.pi * a)
    k = pa[2] + (pb[2] - pa[2]) * a
    for j in range(6):
        aa = max(0, a - j * 0.06)
        tx = pa[0] + (pb[0] - pa[0]) * ease(aa)
        ty = pa[1] + (pb[1] - pa[1]) * ease(aa) - 150 * math.sin(math.pi * aa)
        c.drawCircle(tx, ty - 210 * k, 75 * k * (1 - j / 6), P(C(255, 150, 230, int(150 * (1 - j / 6))), MaskFilter=blur(8)))
    for j, ((cl, rw), kind) in enumerate([((3, 1), "rook"), ((2, 5), "knight"), ((5, 5), "pawn")]):
        xx, yy, kk = b.sq(cl, rw)
        bob = abs(math.sin(t * 7 + j)) * 30
        piece(c, kind, xx, yy - bob, 0.85 * kk, False, t, dict(eyes="wide", mouth="O", look=(0, -1)), rot=12 * math.sin(t * 9 + j))
    piece(c, "queen", x, y, 1.1 * k, True, t, dict(eyes="angry", mouth="grin", look=(1, 0)), rot=15 * math.sin(t * 12))
    # two players going wild at the edges
    for i, (px, lk) in enumerate(((120, PLAYER1), (960, PLAYER2))):
        pose = dict(hands=[(-60, -200 - 30 * math.sin(t * 8 + i)), (60, -200 + 30 * math.sin(t * 8 + i))], eyes="wide", brows="up",
                    mouth="laugh", tilt=6 * math.sin(t * 6 + i), look=(0, 0))
        person(c, px, 1920, 0.8, lk, pose, t)


def art_today(c, t):
    stage_bg(c, (15, 12, 25), (40, 30, 60), (15, 10, 20))
    U.background(c, t, math.sin(t * 0.5) * 30)
    pulse = math.exp(-3 * max(0, t - CUE["strong"])) if t > CUE["strong"] else 0
    U.spotlight(c, t, pulse)
    b = Board(540, 1420, 1860, 700, 1060)
    b.draw(c)
    st = CUE["strong"]
    rise = ease((t - st + 0.2) / 0.5)
    for (cl, rw), kind, wh in [((0, 2), "bishop", True), ((7, 2), "king", True), ((0, 5), "rook", False), ((7, 5), "knight", False)]:
        xx, yy, kk = b.sq(cl, rw)
        bow = 22 * rise * (1 if xx < 540 else -1)
        piece(c, kind, xx, yy, 0.95 * kk, wh, t, dict(eyes="closed" if rise > 0.5 else "open", mouth="smile", look=(1 if xx < 540 else -1, 0)), rot=bow)
    x, y, k = b.sq(3.5, 5)
    piece(c, "queen", x, y - 40 * rise, (1.3 + 0.25 * rise) * k, True, t, dict(eyes="open", mouth="grin", look=(0, -0.3), blink=blinking(t, 0.6)))
    if t > st:
        kk = min(1, (t - st) / 0.8)
        for j in range(12):
            a = j / 12 * 2 * math.pi + t * 0.8
            r = 120 + 260 * ease(kk)
            sparkle(c, x + math.cos(a) * r, y - 330 * k + math.sin(a) * r * 0.7, 8, int(170 * (1 - 0.5 * kk)))


def queen_mascot(c, t):
    c.drawOval(skia.Rect(-150, -18, 150, 18), P(C(0, 0, 0, 120), MaskFilter=blur(14)))
    piece(c, "queen", 0, 0, 1.15, True, t, dict(eyes="open", mouth="grin", look=(0, 0), blink=blinking(t, 0.5)))
    fy = -185 * 1.15
    for side in (-1, 1):  # sunglasses over the eyes
        r = skia.RRect.MakeRectXY(skia.Rect(side * 22 - 26, fy - 22, side * 22 + 26, fy + 18), 14, 14)
        c.drawRRect(r, P(Shader=lin((0, fy - 22), (0, fy + 18), [C(70, 70, 90), C(8, 8, 14)])))
        c.drawRRect(r, S(C(10, 10, 10), 5))
    c.drawLine(-4, fy - 6, 4, fy - 6, S(C(10, 10, 10), 7))


def art_cta(c, t):
    U.T_EIGHT = -10
    U.background(c, t, 0)
    U.spotlight(c, t, 0)
    U.pedestal(c, t)
    c.save()
    c.translate(540, 1440)
    queen_mascot(c, t)
    c.restore()
    c.drawPaint(P(C(10, 6, 14, 150)))


ART = [art_hook, art_india, art_army, art_persia, art_advisor, art_europe, art_spain, art_isabella, art_mad, art_today, art_cta]
PUSH = [(1.0, 1.06), (1.0, 1.06), (1.0, 1.06), (1.0, 1.07), (1.0, 1.06), (1.0, 1.06), (1.0, 1.06), (1.0, 1.06), (1.04, 1.0), (1.0, 1.07), (1.0, 1.0)]
ANCHOR = [(540, 1500), (540, 1500), (540, 1500), (540, 1550), (540, 1550), (540, 1550), (540, 1550), (540, 1500), (540, 1500), (540, 1550), (540, 1300)]


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
    line(img, "The queen used to be", 230, F_MID)
    line(img, "the", 330, F_MID)
    slam(img, "WEAKEST", 430, t, CUE["weak"] - 0.1, GOLD, 160)
    text_block(img, "She could only move ONE square!", font(FONT_B, 54), 660, t, (255, 255, 255), CUE["one"])
    text_block(img, "So what changed?", font(FONT_B, 54), 730, t, PURPLE, CUE["changed"])
    impact(img, t, CUE["weak"] + 0.1, 18)


def tx_india(img, t):
    tag(img, "INDIA, ~1,500 YEARS AGO", t, (200, 90, 50))
    title(img, t, "Chess was born in India", "A game of war: chaturanga", CUE["chat"], sub_color=GOLD)


def tx_army(img, t):
    title(img, t, "The pieces were a real army!", "Elephants, horses, chariots, soldiers", CUE["eleph"])


def tx_persia(img, t):
    tag(img, "PERSIA", t, (60, 110, 170))
    title(img, t, "\"Shah mat!\"", "= \"The king is helpless\"", CUE["helpless"], sub_color=GOLD)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "CHECKMATE", t, CUE["check"], col=RED, size=100)
    impact(img, t, CUE["check"] + 0.15, 14)


def tx_advisor(img, t):
    title(img, t, "There was no queen...", "Just the king's slow advisor", CUE["advisor"])


def tx_europe(img, t):
    tag(img, "EUROPE", t, (120, 90, 160))
    title(img, t, "The advisor became a queen", "...but still the weakest piece!", CUE["weak5"])


def tx_spain(img, t):
    tag(img, "SPAIN, LATE 1400s", t, (190, 60, 50))
    title(img, t, "Then everything changed!", "She could fly across the board!", CUE["fly"], sub_color=GOLD)


def tx_isabella(img, t):
    title(img, t, "Inspired by a real queen?", "Queen Isabella of Spain", CUE["isabella"], sub_color=GOLD)


def tx_mad(img, t):
    title(img, t, "Players called it...", y=260)
    slam(img, "MAD QUEEN CHESS", 420, t, CUE["mad"] - 0.1, PURPLE, 92)
    text_block(img, "Faster. Way more exciting!", font(FONT_B, 56), 620, t, (255, 255, 255), CUE["faster"])
    impact(img, t, CUE["mad"] + 0.1, 14)


def tx_today(img, t):
    title(img, t, "Today, the queen is the", y=260)
    slam(img, "STRONGEST", 420, t, CUE["strong"] - 0.1, GOLD, 140)
    impact(img, t, CUE["strong"] + 0.1, 16)


def tx_cta(img, t):
    text_block(img, "Learned something new?", font(FONT_B, 68), 330, t, delay=0.0)
    make_salt.draw_cta(img, ImageDraw.Draw(img, "RGBA"), W / 2, 1250, t, off=CUE["cta_off"])


TEXT = [tx_hook, tx_india, tx_army, tx_persia, tx_advisor, tx_europe, tx_spain, tx_isabella, tx_mad, tx_today, tx_cta]
base.TRANSITION = splat

if __name__ == "__main__":
    voice = f"{VOICE_DIR}/voice.mp3"
    tl = Timeline(voice)
    firsts = ["chess was", "the pieces", "in persia", "him|and back", "when chose|chess", "then been|in", "some historians", "players call",
              "than|and stock|it", "learn"]
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
               weak=f("weak|week", 0, 0.0), one=f("one", 0), changed=f("changed", 0),
               war=f("war", 1), chat=f("chatter|chaturanga", 1),
               eleph=f("elephants|offense", 2), horses=f("horses", 2), chariots=f("chariots", 2), soldiers=f("foot", 2),
               trapped=f("trapped", 3), shah=f("shah", 3), helpless=f("helpless|hopeless", 3), check=f("checkmate", 3, 0.15),
               noqueen=f("queen", 4), advisor=f("advisor|adviser", 4), crawl=f("crawling", 4),
               queen5=f("queen", 5), weak5=f("weak|week", 5),
               changed6=f("changed", 6), fly=f("fly", 6),
               isabella=f("isabella", 7),
               mad=f("mad|meant", 8, 0.0), faster=f("faster", 8),
               strong=f("strongest", 9, 0.0))
    CUE["cta_off"] = round(tl.find("like|within", S0[10]) - S0[10] - 1.6 + 0.15, 2)
    print("starts:", S0)
    print("durations:", durs, round(sum(durs), 2))
    print("cues:", {k: v for k, v in CUE.items() if k not in ("d", "S")})
    json.dump({"starts": S0, "durs": durs, "cues": {k: v for k, v in CUE.items() if k not in ("d", "S")}}, open(f"{VOICE_DIR}/plan.json", "w"), indent=1)
    if STILLS:
        out = os.environ.get("STILLS_DIR", VOICE_DIR + "/stills")
        os.makedirs(out, exist_ok=True)
        for i in ONLY:
            for tt in STILLS:
                img = Image.new("RGBA", (W, H))
                scene(i, TEXT[i])(img, ImageDraw.Draw(img), float(tt))
                img.convert("RGB").save(f"{out}/chess_{i}_{tt}.png")
        sys.exit()
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), scene(i, TEXT[i])) for i, dd in enumerate(durs)]
    if ONLY:
        base.SCENES[:] = [s for i, s in enumerate(base.SCENES) if i in ONLY]
    ST, C_ = S0, CUE
    ev = [("whoosh", s) for s in ST[1:]]
    ev += [("thud", C_["weak"]), ("pop", C_["one"] + 0.2), ("pop", C_["changed"]),
           ("pop", ST[1] + C_["war"]), ("ding", ST[1] + C_["chat"]),
           ("pop", ST[2] + C_["eleph"]), ("pop", ST[2] + C_["horses"]), ("pop", ST[2] + C_["chariots"]), ("pop", ST[2] + C_["soldiers"]),
           ("pop", ST[3] + C_["shah"]), ("thud", ST[3] + C_["check"] + 0.15),
           ("pop", ST[4] + C_["advisor"]),
           ("ding", ST[5] + C_["queen5"]), ("thud", ST[5] + C_["weak5"]),
           ("ding", ST[6] + C_["changed6"]), ("whoosh", ST[6] + C_["fly"] + 0.3), ("thud", ST[6] + C_["fly"] + 0.25),
           ("ding", ST[7] + C_["isabella"]),
           ("thud", ST[8] + C_["mad"]), ("pop", ST[8] + C_["faster"]),
           ("thud", ST[9] + C_["strong"]), ("ding", ST[9] + C_["strong"] + 0.05),
           ("click", ST[10] + C_["cta_off"] + 1.6), ("click", ST[10] + C_["cta_off"] + 3.6), ("ding", ST[10] + C_["cta_off"] + 3.65)]
    ev += [("click", ST[6] + C_["fly"] + 0.2 + 0.12 * k) for k in range(4)]  # pieces knocked over
    ev = [(k, round(v, 3)) for k, v in ev if 0 <= v < total]
    audio.music("music.wav", total, bpm=100, seed=13)
    audio.sfx("sfx.wav", total, ev)
    base.OUT = "base_chess.mp4"
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_chess.mp4", voice, "music.wav", "sfx.wav", OUTFILE)
    print("wrote", OUTFILE)
