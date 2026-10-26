"""YouTube Short #13: "Potatoes Were Once FEARED?!" (ketchup-video animation style + strong hook).

First video built with style.heading() (auto-fit one-line titles, subtitle placed under the
title) and checked with qa.py — see LESSONS.md.
"""
import math

from PIL import Image, ImageDraw

import make_ketchup
import make_salt
import make_short as base
from make_carrot import parallax
from make_chocolate import VIGNETTE, dust, sparkle
from make_honey import slam
from make_ketchup import camera, face, splat, stamp
from make_lobster import frown_face
from make_pizza import back, bokeh
from make_short import F_BIG, F_MID, H, W, ease, font, FONT_B, person, tag, text_block
from style import heading

SKIN, SKIN_DARK, SKIN_LIGHT = (205, 160, 95), (160, 115, 60), (230, 190, 125)
GOLD = (255, 190, 70)
make_ketchup.SPLAT_COLOR = SKIN
base.HOOK_SKIP = 0.0


# ---------- drawings ----------

def potato(d, x, y, s, t=0.0, ang=0.0, face_on=False, scared=False, seed=0):
    pts = []
    for k in range(28):
        a = k / 28 * 2 * math.pi
        r = 1 + 0.07 * math.sin(a * 3 + seed) + 0.05 * math.sin(a * 5 + seed * 2)
        px, py = math.cos(a) * 110 * r, math.sin(a) * 78 * r
        c, sn = math.cos(ang), math.sin(ang)
        pts.append((x + (px * c - py * sn) * s, y + (px * sn + py * c) * s))
    d.polygon(pts, fill=SKIN)
    d.ellipse([x - 60 * s, y - 50 * s, x - 10 * s, y - 25 * s], fill=SKIN_LIGHT)
    for k in range(4):
        ex = x + (-60 + (k * 47 + seed * 13) % 120) * s
        ey = y + (-30 + (k * 31 + seed * 7) % 60) * s
        d.ellipse([ex - 6 * s, ey - 4 * s, ex + 6 * s, ey + 4 * s], fill=SKIN_DARK)
    if face_on:
        blink = (t % 3.0) < 0.12
        for ex in (-28, 28):
            if blink:
                d.line([(x + (ex - 12) * s, y - 10 * s), (x + (ex + 12) * s, y - 10 * s)], fill=(40, 25, 15), width=max(2, int(6 * s)))
            else:
                d.ellipse([x + (ex - 11) * s, y - 24 * s, x + (ex + 11) * s, y + 4 * s], fill=(255, 255, 255))
                d.ellipse([x + (ex - 5) * s, y - 16 * s, x + (ex + 5) * s, y - 4 * s], fill=(40, 25, 15))
        if scared:
            d.ellipse([x - 14 * s, y + 18 * s, x + 14 * s, y + 46 * s], fill=(90, 40, 30))
        else:
            d.arc([x - 26 * s, y + 6 * s, x + 26 * s, y + 40 * s], 20, 160, fill=(90, 40, 30), width=max(2, int(6 * s)))


def guard(d, x, y, s, t, k=0):
    person(d, x, y, s, (50, 70, 140))
    face(d, x, y - 200 * s, t, s * 0.9, phase=k * 0.7)
    d.rectangle([x - 50 * s, y - 330 * s, x + 50 * s, y - 250 * s], fill=(30, 30, 40))  # tall hat
    d.rectangle([x - 60 * s, y - 262 * s, x + 60 * s, y - 248 * s], fill=(30, 30, 40))
    d.line([(x + 110 * s, y + 140 * s), (x + 110 * s, y - 330 * s)], fill=(120, 90, 60), width=max(2, int(10 * s)))  # spear
    d.polygon([(x + 95 * s, y - 330 * s), (x + 125 * s, y - 330 * s), (x + 110 * s, y - 380 * s)], fill=(200, 205, 215))


def pig(d, x, y, s, t):
    bob = math.sin(t * 6) * 6 * s
    d.ellipse([x - 130 * s, y - 70 * s, x + 130 * s, y + 70 * s], fill=(245, 170, 180))
    for lx in (-80, -30, 40, 90):
        d.rectangle([x + (lx - 12) * s, y + 50 * s, x + (lx + 12) * s, y + 110 * s], fill=(230, 150, 160))
    hx, hy = x + 140 * s, y - 20 * s + bob
    d.ellipse([hx - 70 * s, hy - 60 * s, hx + 70 * s, hy + 60 * s], fill=(245, 170, 180))
    d.polygon([(hx - 40 * s, hy - 50 * s), (hx - 10 * s, hy - 100 * s), (hx, hy - 45 * s)], fill=(230, 140, 155))
    d.ellipse([hx + 40 * s, hy - 10 * s, hx + 90 * s, hy + 30 * s], fill=(230, 130, 150))
    d.ellipse([hx + 55 * s, hy + 2 * s, hx + 63 * s, hy + 14 * s], fill=(150, 70, 80))
    d.ellipse([hx + 70 * s, hy + 2 * s, hx + 78 * s, hy + 14 * s], fill=(150, 70, 80))
    d.ellipse([hx + 5 * s, hy - 25 * s, hx + 17 * s, hy - 13 * s], fill=(40, 25, 20))


def potato_flower(d, x, y, s, col=(245, 245, 250)):
    for p in range(5):
        a = p * 2 * math.pi / 5
        px, py = x + math.cos(a) * 18 * s, y + math.sin(a) * 18 * s
        d.ellipse([px - 14 * s, py - 14 * s, px + 14 * s, py + 14 * s], fill=col)
    d.ellipse([x - 9 * s, y - 9 * s, x + 9 * s, y + 9 * s], fill=(250, 200, 40))


# ---------- illustrations ----------

def art_hook(t, warn_at):
    def draw(d):
        cx = W / 2
        hop = abs(math.sin(t * 3)) * 40
        potato(d, cx + 160, 1380 - hop, 2.1, t, ang=math.sin(t * 3) * 0.08, face_on=True, seed=1)
        lean = math.sin(t * 2) * 6
        person(d, cx - 280 + lean, 1700, 1.35, (120, 70, 120))
        hx, hy = cx - 280 + lean, 1700 - 1.35 * 200
        for ex in (-22, 22):  # wide scared eyes + open mouth
            d.ellipse([hx + ex * 1.3 - 15, hy - 22, hx + ex * 1.3 + 15, hy + 8], fill=(255, 255, 255))
            d.ellipse([hx + ex * 1.3 - 6, hy - 13, hx + ex * 1.3 + 6, hy - 1], fill=(40, 25, 20))
        d.ellipse([hx - 16, hy + 22, hx + 16, hy + 58], fill=(90, 40, 30))
        for k in range(3):  # shaking lines
            d.line([(hx - 120 - k * 18, hy - 60 + k * 50), (hx - 150 - k * 18, hy - 50 + k * 50)], fill=(255, 255, 255, 200), width=6)
        if t >= warn_at:  # second beat: warning sign "DISEASE?"
            p = back((t - warn_at) / 0.3)
            wx, wy = cx + 170, 980
            d.polygon([(wx, wy - 120 * p), (wx - 130 * p, wy + 100 * p), (wx + 130 * p, wy + 100 * p)], fill=(250, 200, 40))
            d.polygon([(wx, wy - 85 * p), (wx - 100 * p, wy + 80 * p), (wx + 100 * p, wy + 80 * p)], fill=(40, 35, 30))
            d.rounded_rectangle([wx - 9 * p, wy - 40 * p, wx + 9 * p, wy + 30 * p], radius=4, fill=(250, 200, 40))
            d.ellipse([wx - 10 * p, wy + 42 * p, wx + 10 * p, wy + 62 * p], fill=(250, 200, 40))
    return draw


def art_andes(t):
    def draw(d):
        cy = 1500
        for k in range(4):  # terraced fields
            y = cy - 120 + k * 90
            d.rounded_rectangle([60 + k * 30, y, W - 60 - k * 30, y + 70], radius=30, fill=[(110, 150, 70), (95, 140, 60)][k % 2])
        for k in range(7):  # potato plants with potatoes popping out of the soil
            x = 150 + k * 130
            y = cy + 260
            sway = math.sin(t * 2 + k) * 8
            d.line([(x, y), (x + sway, y - 120)], fill=(70, 140, 60), width=10)
            d.ellipse([x + sway - 45, y - 170, x + sway + 45, y - 100], fill=(80, 160, 70))
            potato_flower(d, x + sway, y - 165, 0.7, (200, 170, 240))
            p = back((t - 1.0 - k * 0.2) / 0.35)
            if p > 0:
                potato(d, x, y + 40, 0.45 * p, ang=0.3 * (k % 2), seed=k)
    return draw


def art_ship(t):
    def draw(d):
        cy = 1450
        d.rectangle([0, cy + 200, W, H], fill=(40, 90, 140))
        for k in range(5):
            y = cy + 230 + k * 70
            d.line([(j * 40, y + math.sin(j * 0.6 + t * 3 + k) * 10) for j in range(30)], fill=(80, 140, 190), width=6)
        sx = -300 + ease(t / 2.6) * (W / 2 + 320)
        rock = math.sin(t * 2) * 8
        d.polygon([(sx - 260, cy + 120 + rock), (sx + 260, cy + 120 - rock), (sx + 190, cy + 240 - rock), (sx - 190, cy + 240 + rock)], fill=(120, 70, 40))
        for mx, mh in ((sx - 90, 430), (sx + 100, 360)):
            d.line([(mx, cy + 120), (mx, cy + 120 - mh)], fill=(80, 50, 30), width=12)
            d.polygon([(mx - 100, cy + 90 - mh * 0.85), (mx + 100, cy + 90 - mh * 0.85), (mx + 110, cy + 70 - mh * 0.25), (mx - 110, cy + 70 - mh * 0.25)], fill=(240, 230, 210))
            d.rectangle([mx - 40, cy + 90 - mh * 0.75, mx + 40, cy + 70 - mh * 0.45], fill=(200, 40, 40))
        for k in range(3):  # sacks of potatoes on deck
            bx = sx - 150 + k * 110
            d.rounded_rectangle([bx - 45, cy + 40, bx + 45, cy + 120], radius=24, fill=(190, 150, 100))
            potato(d, bx, cy + 35, 0.32, seed=k)
    return draw


def art_suspicious(t, pig_at):
    def draw(d):
        cx, cy = W / 2, 1480
        person(d, cx - 270, cy + 240, 1.35, (90, 60, 110))
        frown_face(d, cx - 270, cy + 240 - 1.35 * 200, 1.25)
        poke = math.sin(t * 5) * 18
        d.line([(cx - 170, cy + 60), (cx - 40 + poke, cy + 10)], fill=(225, 175, 135), width=34)
        potato(d, cx + 60, cy + 30, 0.95, t, face_on=True, scared=True, seed=3)
        for k in range(3):  # question marks
            ph = (t * 0.7 + k * 0.33) % 1
            d.text((cx - 360 + k * 80, cy - 360 - ph * 120), "?", font=font(FONT_B, 70), fill=(255, 255, 255, int(230 * (1 - ph))))
        p = back((t - pig_at) / 0.4)
        if p > 0:
            pig(d, cx + 250, cy + 300, 0.9 * p, t)
    return draw


def art_day(t, guards_at):
    def draw(d):
        cy = 1500
        r = 120 + 6 * math.sin(t * 2)
        d.ellipse([W - 230 - r, 980 - r, W - 230 + r, 980 + r], fill=(255, 205, 80))
        d.rectangle([0, cy + 120, W, H], fill=(110, 80, 45))
        for k in range(9):
            x = 80 + k * 115
            d.line([(x, cy + 150), (x, cy + 60)], fill=(70, 140, 60), width=8)
            d.ellipse([x - 38, cy + 20, x + 38, cy + 80], fill=(80, 160, 70))
        d.rectangle([40, cy + 100, W - 40, cy + 112], fill=(140, 100, 60))  # fence rail
        for k in range(10):
            d.rectangle([40 + k * 110, cy + 60, 52 + k * 110, cy + 160], fill=(140, 100, 60))
        px = 190  # Parmentier: blue coat, white wig
        person(d, px, cy + 30, 0.95, (40, 70, 150))
        d.ellipse([px - 70, cy - 260, px + 70, cy - 150], fill=(240, 240, 240))
        face(d, px, cy + 30 - 0.95 * 200, t, 0.9, phase=0.3)
        for k, gx in enumerate((W / 2 - 40, W / 2 + 190, W - 150)):  # guards march in on "put guards"
            p = back((t - guards_at - k * 0.2) / 0.35)
            if p <= 0:
                continue
            step = abs(math.sin(t * 4 + k)) * 10
            guard(d, gx, cy + 30 - step, 0.95 * p, t, k)
    return draw


def art_night(t, steal_at):
    def draw(d):
        cy = 1500
        d.ellipse([W - 300, 900, W - 160, 1040], fill=(245, 240, 210))
        for k in range(14):
            x, y = (k * 263) % W, 880 + (k * 131) % 360
            r = 3 + (math.sin(t * 3 + k) + 1) * 1.5
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 230))
        d.rectangle([0, cy + 120, W, H], fill=(60, 45, 30))
        d.rectangle([40, cy + 100, W - 40, cy + 112], fill=(90, 65, 40))
        for k in range(10):
            d.rectangle([40 + k * 110, cy + 60, 52 + k * 110, cy + 160], fill=(90, 65, 40))
        for k in range(2):  # sneaky people tiptoeing in with sacks
            x = -150 + ((t * 110 + k * 450) % (W + 300))
            step = abs(math.sin(t * 5 + k)) * 14
            person(d, x, cy + 40 - step, 0.95, (40, 40, 55))
            face(d, x, cy + 40 - step - 190, t + k, 0.85)
            d.rounded_rectangle([x + 60, cy - 30 - step, x + 160, cy + 70 - step], radius=30, fill=(170, 135, 90))
            potato(d, x + 110, cy - 40 - step, 0.3, seed=k)
        if t > steal_at:
            p = back((t - steal_at) / 0.3)
            for k in range(4):  # potatoes flying into the sacks
                q = ((t - steal_at) * 1.5 + k * 0.25) % 1
                potato(d, 200 + k * 200, cy + 100 - math.sin(q * math.pi) * 200, 0.28 * p, seed=k + 4)
    return draw


def art_queen(t):
    def draw(d):
        cx, cy = W / 2, 1520
        d.ellipse([cx - 170, cy - 520, cx + 170, cy - 120], fill=(235, 225, 225))  # tall powdered wig
        person(d, cx, cy + 200, 1.5, (120, 160, 220))
        face(d, cx, cy + 200 - 1.5 * 200, t, 1.3, phase=0.4)
        for k, (dx, dy) in enumerate([(-110, -380), (0, -460), (110, -380), (-60, -280), (70, -290)]):
            sway = math.sin(t * 2 + k) * 6
            potato_flower(d, cx + dx + sway, cy + dy, 1.1, (245, 245, 250) if k % 2 else (200, 170, 240))
        for k in range(7):
            ph = (t * 0.7 + k * 0.143) % 1
            sparkle(d, cx + math.cos(k * 0.9 + t) * 330, cy - 200 + math.sin(k * 1.7 + t) * 300, 13 * math.sin(ph * math.pi) + 2)
    return draw


def art_today(t):
    def draw(d):
        cx, cy = W / 2, 1500
        for k in range(12):  # falling fries
            ph = (t * 0.4 + k * 0.083) % 1
            x = (k * 389 + 90) % (W - 200) + 100
            y = 880 + ph * 1100
            ang = t * (0.8 + (k % 3) * 0.4) + k
            c, s = math.cos(ang), math.sin(ang)
            pts = [(-14, -70), (14, -70), (14, 70), (-14, 70)]
            d.polygon([(x + px * c - py * s, y + px * s + py * c) for px, py in pts], fill=(250, 205, 70))
        fx = cx - 220  # fries box
        for k in range(7):
            x = fx - 100 + k * 33
            top = cy - 220 + (k * 37) % 70
            d.rounded_rectangle([x - 14, top, x + 14, cy], radius=6, fill=(250, 205, 70))
        d.polygon([(fx - 140, cy - 40), (fx + 140, cy - 40), (fx + 110, cy + 200), (fx - 110, cy + 200)], fill=(210, 40, 40))
        bx = cx + 230  # bowl of mash with butter
        d.chord([bx - 190, cy - 120, bx + 190, cy + 200], 0, 180, fill=(80, 120, 170))
        d.chord([bx - 170, cy - 110, bx + 170, cy + 60], 180, 360, fill=(250, 240, 210))
        d.rectangle([bx - 170, cy - 26, bx + 170, cy + 40], fill=(250, 240, 210))
        d.rounded_rectangle([bx - 30, cy - 90, bx + 30, cy - 50], radius=8, fill=(255, 220, 90))
    return draw


# ---------- scenes ----------

def finish(img, t, seed):
    dust(img, t, seed)
    img.alpha_composite(VIGNETTE)


SLAM_AT, WARN_AT = 0.55, 2.5


def s_hook(img, d, t):
    bokeh(img, t, 1, (255, 220, 170))
    camera(img, t + 0.5, art_hook(t, WARN_AT), (W / 2, 1450))
    finish(img, t, 1)
    dd = ImageDraw.Draw(img, "RGBA")
    tw = dd.textlength("People were once", font=F_MID)
    dd.text(((W - tw) / 2 + 4, 385), "People were once", font=F_MID, fill=(0, 0, 0, 140))
    dd.text(((W - tw) / 2, 380), "People were once", font=F_MID, fill=(255, 255, 255))
    slam(img, "SCARED OF POTATOES", 500, t, SLAM_AT, (255, 150, 90), 78)


def s_andes(img, d, t):
    parallax(img, t, [(1150, 900, (100, 100, 150), 6, 220), (1300, 800, (90, 130, 80), 18, 100)])
    camera(img, t, art_andes(t), (W / 2, 1500))
    finish(img, t, 2)
    tag(img, "THE ANDES · SOUTH AMERICA", t, (60, 130, 70))
    heading(img, t, "Born in the mountains", "Grown there for thousands of years.", 5.1, sub_color=(225, 245, 225))


def s_ship(img, d, t):
    bokeh(img, t, 3, (210, 230, 255))
    camera(img, t, art_ship(t), (W / 2, 1450))
    finish(img, t, 3)
    tag(img, "THE 1500s", t, (60, 100, 170))
    heading(img, t, "Shipped to Europe", "Spanish explorers brought them over.", 1.5, sub_color=(220, 230, 250))


PIG_AT = 5.6


def s_suspicious(img, d, t):
    bokeh(img, t, 4, (230, 210, 255))
    camera(img, t, art_suspicious(t, PIG_AT), (W / 2, 1480))
    finish(img, t, 4)
    tag(img, "SUSPICIOUS", t, (120, 70, 140))
    heading(img, t, "Weird... and lumpy?", "Many thought it was only good for animals!", 4.6, sub_color=(235, 225, 245))


GUARDS_AT = 9.4


def s_day(img, d, t):
    camera(img, t, art_day(t, GUARDS_AT), (W / 2, 1500))
    finish(img, t, 5)
    tag(img, "THE CRAZY PART · FRANCE", t, (170, 60, 110))
    heading(img, t, "Parmentier's secret plan", "The story goes: he put guards around his potato field.", GUARDS_AT, sub_color=(255, 225, 240))


STEAL_AT = 3.1


def s_night(img, d, t):
    camera(img, t, art_night(t, STEAL_AT), (W / 2, 1500))
    finish(img, t, 6)
    tag(img, "AT NIGHT", t, (50, 60, 120))
    heading(img, t, "Then people stole them!", "They thought potatoes must be valuable.", 4.4, sub_color=(220, 225, 250))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 820, "STOLEN!", t, STEAL_AT + 0.6, col=(255, 120, 90), size=95)


def s_queen(img, d, t):
    bokeh(img, t, 7, (255, 220, 240))
    camera(img, t, art_queen(t), (W / 2, 1450))
    finish(img, t, 7)
    tag(img, "THE TRICK WORKED", t, (200, 150, 30))
    heading(img, t, "Potato flowers = fashion!", "Some say Marie Antoinette wore them in her hair.", 1.6, sub_color=(255, 235, 245))


def s_today(img, d, t):
    camera(img, t, art_today(t), (W / 2, 1450))
    finish(img, t, 8)
    tag(img, "TODAY", t, (230, 60, 60))
    heading(img, t, "One of the most eaten foods!")


def s_cta(img, d, t):
    text_block(img, "Learned something new?", F_MID, 330, t, delay=0.0)
    make_salt.draw_cta(img, d, W / 2, 1250, t, off=-0.15)


base.TRANSITION = splat
base.SCENES[:] = [
    (4.0, ((55, 35, 20), (15, 9, 5)), s_hook),
    (7.0, ((70, 100, 150), (30, 50, 30)), s_andes),
    (6.0, ((60, 110, 160), (20, 50, 80)), s_ship),
    (8.0, ((45, 35, 60), (12, 9, 18)), s_suspicious),
    (8.0, ((90, 150, 210), (40, 70, 40)), s_day),
    (8.0, ((15, 20, 45), (5, 6, 14)), s_night),
    (7.0, ((60, 40, 60), (18, 10, 18)), s_queen),
    (6.0, ((55, 35, 20), (15, 9, 5)), s_today),
    (6.0, ((30, 30, 40), (8, 8, 12)), s_cta),
]

if __name__ == "__main__":
    base.main()
