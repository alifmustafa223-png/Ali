"""YouTube Short #14: "This Spice Was Worth MORE THAN GOLD?!" (nutmeg).

Ketchup-video animation style + strong hook. New this time: scene cuts and cues come from
timing.Timeline (no hand-calculated timings) and fx.impact() jolts the frame when things land.

Usage: python make_nutmeg.py out.mp4 voice.mp3
"""
import math
import sys

from PIL import ImageDraw

import make_ketchup
import make_salt
import make_short as base
from fx import impact, overlay
from make_carrot import parallax
from make_chocolate import VIGNETTE, dust, sparkle
from make_honey import slam
from make_ketchup import camera, face, splat, stamp
from make_lobster import frown_face
from make_pizza import back, bokeh
from make_short import F_MID, H, W, ease, font, FONT_B, person, tag, text_block
from style import fit_font, heading
from timing import Timeline

NUT, NUT_DARK, MACE = (150, 95, 50), (110, 65, 30), (210, 50, 40)
GOLD, GOLD_DARK = (255, 195, 60), (205, 145, 30)
make_ketchup.SPLAT_COLOR = (170, 110, 55)
base.HOOK_SKIP = 0.0
C = {}  # cue times, filled from the voice in __main__


# ---------- drawings ----------

def nutmeg(d, x, y, s, mace=True):
    d.ellipse([x - 60 * s, y - 70 * s, x + 60 * s, y + 70 * s], fill=NUT)
    d.ellipse([x - 40 * s, y - 52 * s, x - 10 * s, y - 25 * s], fill=(180, 125, 75))
    if mace:  # the red lacy "mace" net around the seed
        for k in range(5):
            a = -1.2 + k * 0.6
            d.arc([x - 64 * s, y - 74 * s, x + 64 * s, y + 74 * s], math.degrees(a) * 40 % 360, math.degrees(a) * 40 % 360 + 50, fill=MACE, width=max(2, int(9 * s)))
            d.line([(x + math.cos(a) * 55 * s, y - 60 * s), (x + math.cos(a + 0.4) * 40 * s, y + 55 * s)], fill=MACE, width=max(2, int(7 * s)))


def gold_bar(d, x, y, s):
    d.polygon([(x - 80 * s, y + 30 * s), (x + 80 * s, y + 30 * s), (x + 55 * s, y - 30 * s), (x - 55 * s, y - 30 * s)], fill=GOLD)
    d.polygon([(x - 55 * s, y - 30 * s), (x + 55 * s, y - 30 * s), (x + 45 * s, y - 18 * s), (x - 45 * s, y - 18 * s)], fill=(255, 225, 130))
    d.line([(x - 80 * s, y + 30 * s), (x + 80 * s, y + 30 * s)], fill=GOLD_DARK, width=max(2, int(6 * s)))


def scale(d, cx, cy, tilt, left_fn, right_fn):
    """Balance scale; positive tilt = left side lower (heavier)."""
    d.polygon([(cx - 90, cy + 330), (cx + 90, cy + 330), (cx + 20, cy + 40), (cx - 20, cy + 40)], fill=(140, 100, 60))
    d.rectangle([cx - 14, cy - 60, cx + 14, cy + 60], fill=(120, 85, 50))
    lx, ly = cx - 300 * math.cos(tilt), cy - 60 + 300 * math.sin(tilt)
    rx, ry = cx + 300 * math.cos(tilt), cy - 60 - 300 * math.sin(tilt)
    d.line([(lx, ly), (rx, ry)], fill=(120, 85, 50), width=16)
    d.ellipse([cx - 22, cy - 82, cx + 22, cy - 38], fill=(200, 160, 80))
    for px, py, fn in ((lx, ly, left_fn), (rx, ry, right_fn)):
        d.line([(px, py), (px - 90, py + 170)], fill=(170, 140, 90), width=5)
        d.line([(px, py), (px + 90, py + 170)], fill=(170, 140, 90), width=5)
        d.chord([px - 130, py + 120, px + 130, py + 230], 0, 180, fill=(200, 160, 80))
        fn(px, py + 160)


def skyline(d, x0, base_y, w, grow, t):
    for k in range(9):
        bx = x0 + k * w / 9
        h = (180 + (k * 97) % 260) * grow
        d.rectangle([bx, base_y - h, bx + w / 9 - 10, base_y], fill=(70, 80, 115))
        for wy in range(int(h / 50)):
            lit = (k + wy) % 3 != 0
            d.rectangle([bx + 14, base_y - h + 18 + wy * 50, bx + 30, base_y - h + 36 + wy * 50], fill=(255, 220, 120) if lit else (50, 60, 90))


def ship(d, x, y, s, flag, t, tilt=0.0):
    rock = math.sin(t * 2) * 8 * s + tilt
    d.polygon([(x - 200 * s, y + rock), (x + 200 * s, y - rock), (x + 150 * s, y + 90 * s - rock), (x - 150 * s, y + 90 * s + rock)], fill=(110, 65, 40))
    d.line([(x, y), (x, y - 330 * s)], fill=(80, 50, 30), width=max(2, int(10 * s)))
    d.polygon([(x - 120 * s, y - 300 * s), (x + 120 * s, y - 300 * s), (x + 130 * s, y - 80 * s), (x - 130 * s, y - 80 * s)], fill=(240, 232, 215))
    fx_, fy = x, y - 330 * s
    if flag == "dutch":
        for i, col in enumerate([(200, 40, 40), (245, 245, 245), (40, 60, 150)]):
            d.rectangle([fx_, fy + i * 18 * s, fx_ + 80 * s, fy + (i + 1) * 18 * s], fill=col)
    else:
        d.rectangle([fx_, fy, fx_ + 80 * s, fy + 54 * s], fill=(245, 245, 245))
        d.rectangle([fx_ + 32 * s, fy, fx_ + 48 * s, fy + 54 * s], fill=(200, 40, 40))
        d.rectangle([fx_, fy + 19 * s, fx_ + 80 * s, fy + 35 * s], fill=(200, 40, 40))


# ---------- illustrations ----------

def art_hook(t):
    def draw(d):
        cx = W / 2
        settle = ease(t / 1.6)
        tilt = 0.22 * settle + 0.03 * math.sin(t * 3)
        scale(d, cx, 1420, tilt, lambda x, y: nutmeg(d, x, y - 40, 1.0),
              lambda x, y: [gold_bar(d, x - 50 + k % 2 * 100, y - 25 - (k // 2) * 50, 0.7) for k in range(4)])
        if t >= C["ny_hook"]:  # second beat: a little New York skyline pops up
            p = back((t - C["ny_hook"]) / 0.35)
            skyline(d, cx - 280, 1130, 560, p * 0.55, t)
            f = font(FONT_B, max(10, int(60 * p)))
            tw = d.textlength("NEW YORK?!", font=f)
            d.rounded_rectangle([cx - tw / 2 - 24, 1140, cx + tw / 2 + 24, 1140 + f.size * 1.3], radius=20, fill=(30, 25, 20))
            d.text((cx - tw / 2, 1146), "NEW YORK?!", font=f, fill=(255, 215, 120))
    return draw


def art_islands(t):
    def draw(d):
        cy = 1450
        d.rectangle([0, cy, W, H], fill=(40, 120, 170))
        for k in range(5):
            y = cy + 40 + k * 80
            d.line([(j * 40, y + math.sin(j * 0.6 + t * 3 + k) * 10) for j in range(30)], fill=(90, 170, 210), width=6)
        for k, (ix, iw) in enumerate(((260, 300), (640, 200), (880, 140))):  # tiny islands pop up
            p = back((t - 0.4 - k * 0.3) / 0.4)
            if p <= 0:
                continue
            d.chord([ix - iw * p, cy - 80 * p, ix + iw * p, cy + 70 * p], 180, 360, fill=(230, 210, 150))
            d.chord([ix - iw * 0.8 * p, cy - 120 * p, ix + iw * 0.8 * p, cy + 40 * p], 180, 360, fill=(70, 150, 70))
            if k == 0:  # volcano
                d.polygon([(ix - 90 * p, cy - 50 * p), (ix + 90 * p, cy - 50 * p), (ix + 25 * p, cy - 230 * p), (ix - 25 * p, cy - 230 * p)], fill=(110, 95, 80))
            for j in range(2):  # nutmeg trees
                tx = ix - iw * 0.4 * p + j * iw * 0.8 * p
                d.line([(tx, cy - 60 * p), (tx, cy - 150 * p)], fill=(100, 70, 40), width=10)
                d.ellipse([tx - 50 * p, cy - 220 * p, tx + 50 * p, cy - 130 * p], fill=(50, 130, 60))
        bob = math.sin(t * 3) * 10  # map pin on the main island
        px, py = 260, cy - 360 + bob
        d.ellipse([px - 40, py - 40, px + 40, py + 40], fill=(225, 50, 50))
        d.polygon([(px - 30, py + 20), (px + 30, py + 20), (px, py + 90)], fill=(225, 50, 50))
        d.ellipse([px - 15, py - 15, px + 15, py + 15], fill=(255, 255, 255))
    return draw


def art_fortune(t):
    def draw(d):
        cx, cy = W / 2, 1480
        d.chord([cx - 170, cy - 150, cx + 170, cy + 250], 0, 360, fill=(190, 150, 100))  # small bag
        d.polygon([(cx - 70, cy - 120), (cx + 70, cy - 120), (cx + 40, cy - 200), (cx - 40, cy - 200)], fill=(175, 135, 90))
        d.line([(cx - 60, cy - 130), (cx + 60, cy - 130)], fill=(120, 80, 50), width=10)
        for k in range(4):
            nutmeg(d, cx - 70 + k * 45, cy - 200 - (k % 2) * 25, 0.42, mace=False)
        for k in range(14):  # coins pouring out around it
            ph = (t * 0.6 + k / 14) % 1
            ang = -math.pi / 2 + (k - 7) * 0.22
            x = cx + math.cos(ang) * 300 * ph
            y = cy - 150 + math.sin(ang) * 220 * ph + 600 * ph * ph
            if y < cy + 330:
                d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=GOLD, outline=GOLD_DARK, width=4)
        for k in range(6):
            ph = (t * 0.8 + k * 0.166) % 1
            sparkle(d, cx + math.cos(k * 1.05 + t) * 300, cy - 50 + math.sin(k * 1.05 + t) * 260, 13 * math.sin(ph * math.pi) + 2)
    return draw


def art_storm(t):
    def draw(d):
        cy = 1450
        for k in range(3):  # storm clouds
            x = 200 + k * 340 + math.sin(t + k) * 20
            for j in range(3):
                d.ellipse([x - 120 + j * 80, 900 + (j % 2) * 30, x + 20 + j * 80, 1010 + (j % 2) * 30], fill=(70, 75, 90))
        if (t % 2.2) < 0.18:  # lightning
            d.line([(560, 1010), (520, 1120), (580, 1120), (530, 1260)], fill=(255, 245, 160), width=14)
        for k in range(30):  # rain
            x = (k * 73 + t * 400) % W
            y = 1000 + (k * 131 + t * 900) % 700
            d.line([(x, y), (x - 12, y + 40)], fill=(170, 190, 220), width=4)
        d.rectangle([0, cy + 80, W, H], fill=(30, 70, 110))
        for k in range(5):
            y = cy + 110 + k * 75
            d.line([(j * 40, y + math.sin(j * 0.5 + t * 4 + k) * 22) for j in range(30)], fill=(70, 120, 170), width=8)
        ship(d, W / 2, cy + 40, 1.0, "dutch", t, tilt=math.sin(t * 3) * 28)
    return draw


def art_plague(t):
    def draw(d):
        cx, cy = W / 2, 1500
        person(d, cx - 130, cy + 260, 1.5, (40, 35, 40))
        hx, hy = cx - 130, cy + 260 - 1.5 * 200
        d.rectangle([hx - 120, hy - 115, hx + 120, hy - 95], fill=(30, 25, 30))  # wide hat
        d.rectangle([hx - 75, hy - 190, hx + 75, hy - 100], fill=(30, 25, 30))
        d.polygon([(hx + 30, hy - 10), (hx + 30, hy + 40), (hx + 210, hy + 60)], fill=(225, 215, 190))  # beak mask
        for ex in (-25, 25):
            d.ellipse([hx + ex - 20, hy - 40, hx + ex + 20, hy], fill=(60, 90, 110), outline=(30, 30, 30), width=5)
        p = back((t - C["plague_nut"]) / 0.35)
        if p > 0:
            nutmeg(d, cx + 250, cy + 40, 1.1 * p)
            for k in range(5):
                ph = (t * 0.9 + k * 0.2) % 1
                sparkle(d, cx + 250 + math.cos(k * 1.26 + t) * 150, cy + 40 + math.sin(k * 1.26 + t) * 150, 12 * math.sin(ph * math.pi) + 2)
    return draw


def art_war(t):
    def draw(d):
        cy = 1450
        d.rectangle([0, cy + 80, W, H], fill=(40, 90, 140))
        for k in range(5):
            y = cy + 110 + k * 75
            d.line([(j * 40, y + math.sin(j * 0.6 + t * 3 + k) * 12) for j in range(30)], fill=(80, 140, 190), width=7)
        ship(d, 250, cy + 40, 0.85, "dutch", t)
        ship(d, W - 250, cy + 40, 0.85, "english", t + 1)
        for side, x0, dirn in ((0, 420, 1), (1, W - 420, -1)):  # cannonballs + smoke
            ph = ((t * 0.7 + side * 0.5) % 1)
            x = x0 + dirn * ph * (W - 840)
            y = cy - 60 - math.sin(ph * math.pi) * 220
            d.ellipse([x - 18, y - 18, x + 18, y + 18], fill=(40, 40, 45))
            r = 30 + ph * 50
            overlay(d, lambda od, x0=x0, r=r, ph=ph: od.ellipse([x0 - r, cy - 40 - r, x0 + r, cy - 40 + r], fill=(220, 220, 225, int(200 * (1 - ph)))))
    return draw


def art_deal(t):
    def draw(d):
        cx, cy = W / 2, 1450
        shake = math.sin(t * 8) * 18 * (1 if t > C["deal"] else 0)
        d.rounded_rectangle([cx - 330, cy - 40 + shake, cx - 20, cy + 60 + shake], radius=40, fill=(220, 175, 135))  # handshake
        d.rounded_rectangle([cx + 20, cy - 40 - shake, cx + 330, cy + 60 - shake], radius=40, fill=(190, 140, 100))
        d.rounded_rectangle([cx - 80, cy - 70, cx + 80, cy + 80], radius=50, fill=(205, 158, 118))
        d.rectangle([cx - 420, cy - 60, cx - 320, cy + 80], fill=(200, 40, 40))   # Dutch cuff
        d.rectangle([cx + 320, cy - 60, cx + 420, cy + 80], fill=(40, 60, 150))   # English cuff
        p1 = back((t - C["run"]) / 0.35)  # tiny Run island card
        if p1 > 0:
            x, y = cx - 250, cy + 240
            d.rounded_rectangle([x - 150 * p1, y - 110 * p1, x + 150 * p1, y + 110 * p1], radius=20, fill=(40, 120, 170))
            d.chord([x - 80 * p1, y - 30 * p1, x + 80 * p1, y + 50 * p1], 180, 360, fill=(70, 150, 70))
            nutmeg(d, x, y - 40 * p1, 0.4 * p1, mace=False)
        p2 = back((t - C["amsterdam"]) / 0.35)  # small New Amsterdam card
        if p2 > 0:
            x, y = cx + 250, cy + 240
            d.rounded_rectangle([x - 150 * p2, y - 110 * p2, x + 150 * p2, y + 110 * p2], radius=20, fill=(110, 150, 90))
            for k in range(3):
                hx = x - 70 * p2 + k * 70 * p2
                d.rectangle([hx - 22 * p2, y - 10 * p2, hx + 22 * p2, y + 50 * p2], fill=(170, 110, 70))
                d.polygon([(hx - 28 * p2, y - 10 * p2), (hx + 28 * p2, y - 10 * p2), (hx, y - 45 * p2)], fill=(130, 70, 50))
    return draw


def art_newyork(t):
    def draw(d):
        grow = ease(t / 1.2)
        skyline(d, 40, 1800, W - 80, grow * 2.2, t)
        for k in range(6):
            ph = (t * 0.8 + k * 0.166) % 1
            sparkle(d, 150 + k * 160, 1000 + math.sin(k * 2 + t) * 80, 13 * math.sin(ph * math.pi) + 2)
    return draw


def art_today(t):
    def draw(d):
        cx, cy = W / 2, 1500
        d.rectangle([60, cy + 140, W - 60, cy + 170], fill=(120, 80, 50))  # kitchen shelf
        for k, (col, lab) in enumerate((((150, 95, 50), "NUTMEG"), ((200, 60, 40), "PAPRIKA"), ((220, 180, 60), "CUMIN"))):
            x = 230 + k * 310
            d.rounded_rectangle([x - 80, cy - 120, x + 80, cy + 140], radius=20, fill=(235, 240, 245, 160))
            d.rounded_rectangle([x - 66, cy - 60, x + 66, cy + 128], radius=14, fill=col)
            d.rectangle([x - 70, cy - 160, x + 70, cy - 115], fill=(60, 60, 70))
            f = font(FONT_B, 30)
            tw = d.textlength(lab, font=f)
            d.rounded_rectangle([x - tw / 2 - 10, cy + 10, x + tw / 2 + 10, cy + 56], radius=8, fill=(250, 245, 230))
            d.text((x - tw / 2, cy + 14), lab, font=f, fill=(60, 40, 30))
        p = back((t - C["dollars"]) / 0.35)
        if p > 0:
            f = font(FONT_B, max(10, int(80 * p)))
            tw = d.textlength("$3", font=f)
            x, y = 230, cy - 330
            d.polygon([(x - tw / 2 - 60 * p, y), (x - tw / 2 - 20 * p, y - 55 * p), (x + tw / 2 + 30 * p, y - 55 * p), (x + tw / 2 + 30 * p, y + 55 * p), (x - tw / 2 - 20 * p, y + 55 * p)], fill=GOLD)
            d.text((x - tw / 2 + 4, y - f.size * 0.6), "$3", font=f, fill=(40, 30, 20))
    return draw


# ---------- scenes ----------

def finish(img, t, seed):
    dust(img, t, seed)
    img.alpha_composite(VIGNETTE)


def s_hook(img, d, t):
    bokeh(img, t, 1, (255, 215, 140))
    camera(img, t + 0.5, art_hook(t), (W / 2, 1450))
    finish(img, t, 1)
    dd = ImageDraw.Draw(img, "RGBA")
    top = fit_font("This spice was once worth", F_MID)
    tw = dd.textlength("This spice was once worth", font=top)
    dd.text(((W - tw) / 2 + 4, 385), "This spice was once worth", font=top, fill=(0, 0, 0, 140))
    dd.text(((W - tw) / 2, 380), "This spice was once worth", font=top, fill=(255, 255, 255))
    slam(img, "MORE THAN GOLD", 500, t, C["slam"], GOLD, 100)
    impact(img, t, C["slam"] + 0.22)


def s_islands(img, d, t):
    parallax(img, t, [(1250, 900, (90, 130, 170), 8, 50)])
    camera(img, t, art_islands(t), (W / 2, 1450))
    finish(img, t, 2)
    tag(img, "BANDA ISLANDS · INDONESIA", t, (40, 130, 120))
    heading(img, t, "It's nutmeg!", "It only grew on a few tiny islands.", C["islands_sub"], sub_color=(215, 240, 240))


def s_fortune(img, d, t):
    bokeh(img, t, 3, (255, 215, 140))
    camera(img, t, art_fortune(t), (W / 2, 1450))
    finish(img, t, 3)
    tag(img, "EUROPE · 1600s", t, (180, 130, 40))
    heading(img, t, "A small bag = a fortune", colors={"FORTUNE": GOLD})


def s_storm(img, d, t):
    camera(img, t, art_storm(t), (W / 2, 1450))
    finish(img, t, 4)
    tag(img, "DANGEROUS JOURNEYS", t, (60, 80, 130))
    heading(img, t, "Sailors risked everything", "Months at sea, storms and disease.", 1.0, sub_color=(220, 230, 250))


def s_plague(img, d, t):
    bokeh(img, t, 5, (230, 230, 200))
    camera(img, t, art_plague(t), (W / 2, 1450))
    finish(img, t, 5)
    tag(img, "THE PLAGUE", t, (90, 90, 70))
    heading(img, t, "A cure for the plague?", "Some people believed nutmeg could protect them.", 0.8, sub_color=(235, 235, 215))


def s_war(img, d, t):
    camera(img, t, art_war(t), (W / 2, 1450))
    finish(img, t, 6)
    tag(img, "SPICE WARS", t, (170, 50, 50))
    heading(img, t, "Battles over nutmeg!", "The Dutch and English fought for years.", C["war_sub"], sub_color=(240, 225, 225))


def s_deal(img, d, t):
    bokeh(img, t, 7, (255, 215, 140))
    camera(img, t, art_deal(t), (W / 2, 1450))
    finish(img, t, 7)
    tag(img, "THE CRAZY PART · 1667", t, (170, 60, 110))
    heading(img, t, "The deal of the century", "Dutch: tiny island Run. English: New Amsterdam.", C["run"], sub_color=(255, 225, 240))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 1150, "DEAL!", t, C["deal"], col=GOLD, size=100)
    impact(img, t, C["deal"] + 0.2)


def s_newyork(img, d, t):
    bokeh(img, t, 8, (255, 220, 160))
    camera(img, t, art_newyork(t), (W / 2, 1600))
    finish(img, t, 8)
    tag(img, "TODAY WE CALL IT...", t, (60, 100, 170))
    heading(img, t, "NEW YORK!", f=font(FONT_B, 130), y=420, colors={"NEW": GOLD, "YORK!": GOLD})
    impact(img, t, 0.35, strength=12)


def s_today(img, d, t):
    bokeh(img, t, 9, (255, 220, 160))
    camera(img, t, art_today(t), (W / 2, 1500))
    finish(img, t, 9)
    tag(img, "TODAY", t, (230, 60, 60))
    heading(img, t, "In almost every kitchen", "It once changed the map of the world.", C["map_sub"], sub_color=(255, 235, 215))


def s_cta(img, d, t):
    text_block(img, "Learned something new?", F_MID, 330, t, delay=0.0)
    make_salt.draw_cta(img, d, W / 2, 1250, t, off=C["cta_off"])


base.TRANSITION = splat
SCENE_LIST = [
    (((55, 35, 15), (15, 9, 4)), s_hook),
    (((60, 120, 170), (20, 50, 80)), s_islands),
    (((60, 45, 20), (18, 12, 5)), s_fortune),
    (((35, 40, 60), (10, 12, 18)), s_storm),
    (((45, 45, 40), (12, 12, 10)), s_plague),
    (((60, 90, 140), (20, 40, 70)), s_war),
    (((60, 25, 55), (20, 8, 25)), s_deal),
    (((40, 50, 90), (10, 14, 30)), s_newyork),
    (((60, 40, 20), (16, 10, 5)), s_today),
    (((30, 30, 40), (8, 8, 12)), s_cta),
]

if __name__ == "__main__":
    out, voice = sys.argv[1], sys.argv[2]
    tl = Timeline(voice)
    durs = tl.plan(["okay", "in europe", "sailors", "some people", "so european", "the crazy", "today we", "and today", "if you"], tail=1.3)
    C.update(
        slam=tl.cue("gold", 0, lead=0.25), ny_hook=tl.cue("new york", 0, lead=0.2),
        islands_sub=tl.cue("four", 1), war_sub=tl.cue("dutch", 5),
        deal=tl.cue("deal", 6), run=tl.cue("dutch", 6), amsterdam=tl.cue("english", 6),
        plague_nut=tl.cue("protect", 4), dollars=tl.cue("costs", 8), map_sub=tl.cue("not", 8),
        cta_off=tl.cue("like", 9) - 1.5,
    )
    print("durations:", durs, "total:", round(sum(durs), 2))
    print("cues:", C)
    base.SCENES[:] = [(dd,) + sc for dd, sc in zip(durs, SCENE_LIST)]
    sys.argv = [sys.argv[0], out]
    base.main()
