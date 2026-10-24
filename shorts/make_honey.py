"""YouTube Short #11: "Honey NEVER Goes Bad?!" (ketchup-video animation style).

Hook rework to stop early swipes: no pause in the first line, the key phrase SLAMS in (zoom,
shake, flash) the moment it is spoken, the art moves from frame one, and a second surprise
(a 10 -> 3,000 YEARS counter) lands about two seconds in.
"""
import math

from PIL import Image, ImageDraw

import make_ketchup
import make_salt
import make_short as base
from make_carrot import parallax
from make_chocolate import VIGNETTE, dust, sparkle, title_pop
from make_ketchup import camera, face, splat, stamp
from make_pizza import back, bokeh
from make_short import F_BIG, F_MID, F_SMALL, H, W, ease, font, FONT_B, person, tag, text_block

HONEY, HONEY_DARK, HONEY_LIGHT = (240, 165, 30), (200, 120, 20), (255, 210, 90)
GOLD = (255, 190, 70)
make_ketchup.SPLAT_COLOR = HONEY
base.HOOK_SKIP = 0.0  # this hook is designed to be full and moving from frame one


# ---------- shared drawings ----------

def jar(d, cx, cy, s=1.0, level=0.85, crystals=0.0, label=True):
    """Honey jar; cy is the bottom of the jar."""
    w, h = 170 * s, 300 * s
    d.rounded_rectangle([cx - w, cy - h, cx + w, cy], radius=int(50 * s), fill=(235, 240, 245, 120))
    top = cy - h * level
    d.rounded_rectangle([cx - w + 14 * s, top, cx + w - 14 * s, cy - 14 * s], radius=int(40 * s), fill=HONEY)
    d.rounded_rectangle([cx - w + 40 * s, top + 25 * s, cx - w + 70 * s, cy - 50 * s], radius=int(14 * s), fill=HONEY_LIGHT)
    if crystals > 0:
        for k in range(40):
            x = cx - w + 30 * s + (k * 37) % int(2 * w - 60 * s)
            y = top + 20 * s + (k * 53) % int(max(1, cy - top - 50 * s))
            r = 7 * s
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 245, 210, int(230 * crystals)))
    d.rounded_rectangle([cx - w - 12 * s, cy - h - 60 * s, cx + w + 12 * s, cy - h + 10 * s], radius=int(20 * s), fill=(150, 90, 50))
    if label:
        d.rounded_rectangle([cx - w * 0.6, cy - h * 0.62, cx + w * 0.6, cy - h * 0.3], radius=int(16 * s), fill=(250, 240, 215))
        f = font(FONT_B, max(10, int(44 * s)))
        tw = d.textlength("HONEY", font=f)
        d.text((cx - tw / 2, cy - h * 0.6), "HONEY", font=f, fill=HONEY_DARK)


def dipper(d, x, y, t, s=1.0):
    """Honey dipper with a stretching drip; (x, y) is the head centre."""
    d.line([(x + 40 * s, y - 40 * s), (x + 220 * s, y - 220 * s)], fill=(160, 100, 55), width=int(22 * s))
    for k in range(4):
        d.ellipse([x - (60 - k * 6) * s, y - (40 - k * 22) * s - 22 * s, x + (60 - k * 6) * s, y - (40 - k * 22) * s + 22 * s], fill=(190, 125, 65))
    d.ellipse([x - 64 * s, y + 10 * s, x + 64 * s, y + 60 * s], fill=HONEY)
    ph = (t * 0.9) % 1
    drip = 40 * s + ph * 260 * s
    d.polygon([(x - 14 * s, y + 50 * s), (x + 14 * s, y + 50 * s), (x + 4 * s, y + drip), (x - 4 * s, y + drip)], fill=HONEY)
    d.ellipse([x - 14 * s, y + drip - 14 * s, x + 14 * s, y + drip + 14 * s], fill=HONEY)


def bee(d, x, y, t, s=1.0, ang=0.0):
    flap = abs(math.sin(t * 38)) * 0.7 + 0.3
    c, sn = math.cos(ang), math.sin(ang)
    def rot(px, py):
        return (x + (px * c - py * sn) * s, y + (px * sn + py * c) * s)
    for wx in (-18, 18):
        cx_, cy_ = rot(wx, -40)
        d.ellipse([cx_ - 30 * s, cy_ - 45 * s * flap, cx_ + 30 * s, cy_ + 10 * s], fill=(230, 245, 255, 170))
    d.ellipse([x - 55 * s, y - 32 * s, x + 55 * s, y + 32 * s], fill=(250, 200, 40))
    for k in (-18, 8):
        d.rectangle([x + k * s, y - 30 * s, x + (k + 14) * s, y + 30 * s], fill=(40, 30, 25))
    d.ellipse([x + 38 * s, y - 22 * s, x + 78 * s, y + 18 * s], fill=(40, 30, 25))
    d.ellipse([x + 58 * s, y - 12 * s, x + 66 * s, y - 4 * s], fill=(255, 255, 255))
    d.polygon([(x - 55 * s, y - 6 * s), (x - 78 * s, y), (x - 55 * s, y + 6 * s)], fill=(40, 30, 25))


def flower(d, x, y, s, col, t, k):
    sway = math.sin(t * 2 + k) * 6 * s
    d.line([(x, y + 90 * s), (x + sway, y)], fill=(70, 150, 70), width=max(2, int(8 * s)))
    for p in range(6):
        a = p * math.pi / 3 + t * 0.3
        px, py = x + sway + math.cos(a) * 26 * s, y + math.sin(a) * 26 * s
        d.ellipse([px - 18 * s, py - 18 * s, px + 18 * s, py + 18 * s], fill=col)
    d.ellipse([x + sway - 15 * s, y - 15 * s, x + sway + 15 * s, y + 15 * s], fill=(250, 200, 50))


# ---------- illustrations ----------

def art_hook(t, show_at, years_at):
    def draw(d):
        cx = W / 2
        jar(d, cx - 170, 1800, 1.3)
        dipper(d, cx - 40, 1190, t, 0.9)
        kx, ky, kr = cx + 280, 1450, 150  # clock with hands spinning fast = time flying by
        d.ellipse([kx - kr - 14, ky - kr - 14, kx + kr + 14, ky + kr + 14], fill=(150, 90, 50))
        d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill=(250, 245, 230))
        for k in range(12):
            a = k * math.pi / 6
            d.line([(kx + math.cos(a) * kr * 0.82, ky + math.sin(a) * kr * 0.82), (kx + math.cos(a) * kr * 0.95, ky + math.sin(a) * kr * 0.95)], fill=(120, 90, 60), width=6)
        speed = 6 if t < years_at else 22
        a1, a2 = t * speed, t * speed / 12
        d.line([(kx, ky), (kx + math.cos(a1) * kr * 0.8, ky + math.sin(a1) * kr * 0.8)], fill=(60, 40, 30), width=10)
        d.line([(kx, ky), (kx + math.cos(a2) * kr * 0.5, ky + math.sin(a2) * kr * 0.5)], fill=(60, 40, 30), width=16)
        d.ellipse([kx - 14, ky - 14, kx + 14, ky + 14], fill=(200, 60, 50))
        # the YEARS counter appears on "ten years" and flips to 3,000 on "three thousand"
        if t >= show_at:
            flip = t >= years_at
            num = "3,000" if flip else "10"
            pop = back((t - (years_at if flip else show_at)) / 0.3)
            f = font(FONT_B, max(10, int(110 * (0.55 + 0.45 * pop))))
            txt = f"{num} YEARS"
            tw = d.textlength(txt, font=f)
            y0 = 840
            d.rounded_rectangle([cx - tw / 2 - 30, y0 - 10, cx + tw / 2 + 30, y0 + f.size * 1.25], radius=26, fill=(30, 20, 10, 230))
            d.text((cx - tw / 2, y0), txt, font=f, fill=GOLD)
    return draw


def art_tomb(t, open_at):
    def draw(d):
        cx, cy = W / 2, 1500
        d.polygon([(cx - 520, cy + 300), (cx + 520, cy + 300), (cx, cy - 560)], fill=(120, 90, 60))  # tomb wall
        for k in range(5):  # hieroglyph-ish marks
            y = cy - 250 + k * 90
            for j in range(3):
                x = cx - 120 + j * 120
                d.rectangle([x - 22, y - 14, x + 22, y + 14], fill=(150, 115, 75))
        p = ease((t - open_at) / 0.6)
        jx = cx + 170
        if p > 0:  # light rays when the pot is opened (own layer, so they glow instead of punching holes)
            rays = Image.new("RGBA", d._image.size, (0, 0, 0, 0))
            rd = ImageDraw.Draw(rays)
            for k in range(5):
                a = -math.pi / 2 + (k - 2) * 0.28
                rd.polygon([(jx, cy + 40), (jx + math.cos(a - 0.06) * 600 * p, cy + 40 + math.sin(a - 0.06) * 600 * p), (jx + math.cos(a + 0.06) * 600 * p, cy + 40 + math.sin(a + 0.06) * 600 * p)], fill=(255, 225, 120, 90))
            d._image.alpha_composite(rays)
        d.chord([jx - 130, cy - 40, jx + 130, cy + 260], 0, 180, fill=(170, 110, 60))
        d.rectangle([jx - 130, cy + 100, jx + 130, cy + 115], fill=(170, 110, 60))
        d.ellipse([jx - 130, cy + 80, jx + 130, cy + 130], fill=HONEY if p > 0 else (140, 90, 50))
        lid_y = cy + 60 - p * 260
        d.ellipse([jx - 120 + p * 200, lid_y - 25, jx + 120 + p * 200, lid_y + 25], fill=(140, 90, 50))
        person(d, cx - 230, cy + 260, 1.3, (190, 160, 110))
        d.rectangle([cx - 340, cy - 25, cx - 120, cy - 5], fill=(170, 140, 90))  # explorer hat brim
        d.chord([cx - 300, cy - 110, cx - 160, cy + 20], 180, 360, fill=(170, 140, 90))
        face(d, cx - 230, cy + 260 - 1.3 * 200, t, 1.2)
        for k in range(5):
            ph = (t * 0.7 + k * 0.2) % 1
            if p > 0:
                sparkle(d, jx + math.cos(k * 1.3 + t) * 160, cy - 60 + math.sin(k * 2.1 + t) * 70, 12 * math.sin(ph * math.pi) + 2)
    return draw


def art_science(t, x_at):
    def draw(d):
        cx, cy = W / 2, 1450
        r = 230 + 8 * math.sin(t * 2)  # big honey drop
        d.ellipse([cx - r, cy - r * 0.9, cx + r, cy + r * 1.05], fill=HONEY)
        d.polygon([(cx - r * 0.55, cy - r * 0.7), (cx + r * 0.55, cy - r * 0.7), (cx, cy - r * 1.7)], fill=HONEY)
        d.ellipse([cx - r * 0.55, cy - r * 0.45, cx - r * 0.25, cy - r * 0.05], fill=HONEY_LIGHT)
        for k in range(6):  # germs bounce off and shrink away
            a = k * math.pi / 3 + t * 0.6
            q = ease((t - x_at) / 1.2)
            dist = 360 + 120 * q
            gx, gy = cx + math.cos(a) * dist, cy + math.sin(a) * dist * 0.8
            gr = 42 * (1 - 0.8 * q)
            if gr < 3:
                continue
            d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=(110, 190, 90))
            for sp in range(6):
                sa = sp * math.pi / 3 + t * 2
                d.line([(gx + math.cos(sa) * gr, gy + math.sin(sa) * gr), (gx + math.cos(sa) * gr * 1.4, gy + math.sin(sa) * gr * 1.4)], fill=(110, 190, 90), width=5)
            d.ellipse([gx - gr * 0.4, gy - gr * 0.3, gx - gr * 0.1, gy], fill=(30, 60, 30))
            d.ellipse([gx + gr * 0.1, gy - gr * 0.3, gx + gr * 0.4, gy], fill=(30, 60, 30))
        if t > x_at:  # big red X over a water drop: "almost no water"
            a = int(255 * ease((t - x_at) / 0.25))
            wx, wy = cx + 330, cy - 420
            d.ellipse([wx - 55, wy - 45, wx + 55, wy + 65], fill=(90, 170, 240, a))
            d.polygon([(wx - 40, wy - 20), (wx + 40, wy - 20), (wx, wy - 95)], fill=(90, 170, 240, a))
            d.line([(wx - 80, wy - 100), (wx + 80, wy + 80)], fill=(230, 50, 50, a), width=22)
            d.line([(wx + 80, wy - 100), (wx - 80, wy + 80)], fill=(230, 50, 50, a), width=22)
    return draw


def art_bee_power(t):
    def draw(d):
        cx, cy = W / 2, 1450
        jar(d, cx, cy + 300, 0.95)
        a = t * 1.4
        bx, by = cx + math.cos(a) * 300, cy - 300 + math.sin(a * 2) * 90
        bee(d, bx, by, t, 1.3, ang=math.sin(a) * 0.3)
        for k in range(8):  # sparkly enzyme trail from the bee into the jar
            ph = (t * 1.1 + k / 8) % 1
            sx = bx + (cx - bx) * ph
            sy = by + (cy + 40 - by) * ph
            sparkle(d, sx, sy, 10 * (1 - ph) + 2, (255, 240, 160))
        f = font(FONT_B, 70)
        tw = d.textlength("H2O2", font=f)
        bob = math.sin(t * 2) * 8
        d.rounded_rectangle([cx - 330 - tw / 2 - 24, cy - 40 + bob, cx - 330 + tw / 2 + 24, cy + 60 + bob], radius=22, fill=(40, 130, 200))
        d.text((cx - 330 - tw / 2, cy - 30 + bob), "H2O2", font=f, fill=(255, 255, 255))
    return draw


def art_wound(t):
    def draw(d):
        cx, cy = W / 2, 1450
        person(d, cx - 200, cy + 260, 1.45, (240, 230, 200), skin=(185, 130, 90))
        d.rectangle([cx - 330, cy - 160, cx - 70, cy - 120], fill=(40, 70, 160))   # Egyptian headdress band
        d.polygon([(cx - 330, cy - 140), (cx - 380, cy + 40), (cx - 300, cy + 40)], fill=(40, 70, 160))
        d.polygon([(cx - 70, cy - 140), (cx - 20, cy + 40), (cx - 100, cy + 40)], fill=(40, 70, 160))
        face(d, cx - 200, cy + 260 - 1.45 * 200, t, 1.3, phase=1.1)
        d.line([(cx - 90, cy + 80), (cx + 130, cy + 40)], fill=(185, 130, 90), width=58)  # arm
        wrap = ease(t / 1.5)
        for k in range(int(wrap * 5)):  # bandage wraps around the arm
            x = cx - 50 + k * 34
            d.line([(x, cy + 30 - k * 6), (x + 14, cy + 100 - k * 6)], fill=(250, 248, 240), width=16)
        jar(d, cx + 260, cy + 330, 0.6)
        dipper(d, cx + 200, cy - 120, t, 0.6)
    return draw


def art_flowers(t, count_at):
    def draw(d):
        cx, cy = W / 2, 1480
        cols = [(240, 110, 150), (160, 120, 230), (250, 250, 250), (250, 150, 60), (240, 80, 80)]
        for k in range(12):
            x = 70 + k * 90
            flower(d, x, cy + 120 + (k % 3) * 40, 0.85, cols[k % 5], t, k)
        bx = 120 + ((t * 260) % (W - 240))  # bee hopping from flower to flower
        by = cy - 40 - abs(math.sin(t * 4)) * 140
        bee(d, bx, by, t, 1.0)
        q = ease((t - count_at) / 2.0)
        n = int(2_000_000 * q)
        f = font(FONT_B, 92)
        txt = f"{n:,}"
        tw = d.textlength(txt, font=f)
        d.rounded_rectangle([cx - tw / 2 - 30, cy - 470, cx + tw / 2 + 30, cy - 340], radius=26, fill=(30, 20, 10, 210))
        d.text((cx - tw / 2, cy - 460), txt, font=f, fill=GOLD)
        fs = font(FONT_B, 46)
        lab = "flowers for 1 pound"
        lw = d.textlength(lab, font=fs)
        d.text((cx - lw / 2, cy - 320), lab, font=fs, fill=(255, 240, 210))
    return draw


def art_teaspoon(t):
    def draw(d):
        cx, cy = W / 2, 1450
        bee(d, cx - 160, cy - 160 + math.sin(t * 3) * 20, t, 2.2)
        sx, sy = cx + 230, cy + 120  # tiny teaspoon with a single drop
        d.line([(sx - 200, sy + 140), (sx - 40, sy + 20)], fill=(200, 205, 215), width=22)
        d.ellipse([sx - 90, sy - 50, sx + 90, sy + 50], fill=(200, 205, 215))
        p = back((t - 1.2) / 0.4)
        if p > 0:
            d.ellipse([sx - 16 * p, sy - 12 * p, sx + 16 * p, sy + 12 * p], fill=HONEY)
        f = font(FONT_B, 64)
        tw = d.textlength("1/12 tsp", font=f)
        d.text((sx - tw / 2, sy + 90), "1/12 tsp", font=f, fill=GOLD)
    return draw


def art_kurdistan(t):
    def draw(d):
        cx, cy = W / 2, 1500
        for k in range(3):  # wooden beehives
            x = cx - 300 + k * 300
            d.rounded_rectangle([x - 110, cy - 60, x + 110, cy + 200], radius=16, fill=(200, 140, 70))
            for j in range(3):
                d.line([(x - 110, cy + j * 70), (x + 110, cy + j * 70)], fill=(160, 105, 50), width=6)
            d.polygon([(x - 135, cy - 60), (x + 135, cy - 60), (x, cy - 160)], fill=(150, 90, 50))
            d.ellipse([x - 22, cy + 150, x + 22, cy + 175], fill=(60, 35, 20))
        for k in range(5):  # bees buzzing around the hives
            a = t * (1.2 + k * 0.2) + k * 1.3
            bee(d, cx + math.cos(a) * (250 + k * 30), cy - 250 + math.sin(a * 1.5) * 100, t + k, 0.55, ang=math.cos(a) * 0.4)
        cols = [(240, 110, 150), (250, 250, 250), (160, 120, 230), (250, 150, 60)]
        for k in range(10):
            flower(d, 60 + k * 107, cy + 300 + (k % 2) * 30, 0.6, cols[k % 4], t, k)
    return draw


def art_warm(t, melt_at):
    def draw(d):
        cx, cy = W / 2, 1480
        d.chord([cx - 330, cy - 160, cx + 330, cy + 260], 0, 180, fill=(80, 140, 200))  # bowl of warm water
        d.ellipse([cx - 330, cy - 10, cx + 330, cy + 70], fill=(120, 180, 230))
        melt = ease((t - melt_at) / 2.0)
        jar(d, cx, cy + 60, 0.85, level=0.8, crystals=1 - melt)
        for k in range(4):  # steam
            pts = [(cx - 240 + k * 160 + math.sin(j * 0.5 + t * 3 + k) * 16, cy - 40 - j * 24) for j in range(8)]
            d.line(pts, fill=(255, 255, 255, 110), width=10)
        if melt > 0.95:
            for k in range(5):
                ph = (t * 0.8 + k * 0.2) % 1
                sparkle(d, cx + math.cos(k * 1.3 + t) * 230, cy - 200 + math.sin(k * 2.1 + t) * 80, 12 * math.sin(ph * math.pi) + 2)
    return draw


# ---------- scenes ----------

def finish(img, t, seed):
    dust(img, t, seed)
    img.alpha_composite(VIGNETTE)


SLAM_AT, SHOW_AT, YEARS_AT = 0.35, 2.0, 3.15


def slam(img, text, y, t, at, col, size):
    """Key words smash in from huge to normal with a shake and a white flash."""
    p = (t - at) / 0.22
    if p <= 0:
        return
    sc = 1 + 1.6 * (1 - ease(p))
    shake = math.sin(t * 90) * 14 * max(0.0, 1 - (t - at) / 0.45)
    f = font(FONT_B, int(size * sc))
    d = ImageDraw.Draw(img, "RGBA")
    tw = d.textlength(text, font=f)
    a = int(255 * min(1, p * 1.6))
    d.text(((W - tw) / 2 + shake + 5, y - (f.size - size) * 0.5 + 6), text, font=f, fill=(0, 0, 0, int(a * 0.5)))
    d.text(((W - tw) / 2 + shake, y - (f.size - size) * 0.5), text, font=f, fill=col + (a,))
    flash = max(0.0, 1 - (t - at - 0.2) / 0.18) if t - at > 0.2 else 0
    if flash > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 245, 220, int(90 * flash))))


def s_hook(img, d, t):
    bokeh(img, t, 1, (255, 220, 150))
    camera(img, t + 0.5, art_hook(t, SHOW_AT, YEARS_AT), (W / 2, 1450))  # +0.5: art is already popped in on frame one
    finish(img, t, 1)
    dd = ImageDraw.Draw(img, "RGBA")
    tw = dd.textlength("This food", font=F_MID)
    dd.text(((W - tw) / 2 + 4, 385), "This food", font=F_MID, fill=(0, 0, 0, 140))
    dd.text(((W - tw) / 2, 380), "This food", font=F_MID, fill=(255, 255, 255))
    slam(img, "NEVER GOES BAD", 500, t, SLAM_AT, GOLD, 100)


OPEN_AT = 4.4


def s_tomb(img, d, t):
    bokeh(img, t, 2, (255, 220, 160))
    camera(img, t, art_tomb(t, OPEN_AT), (W / 2, 1450))
    finish(img, t, 2)
    tag(img, "ANCIENT EGYPT", t, (180, 130, 50))
    title_pop(img, "Honey in the tombs!", F_MID, 400, t, colors={"HONEY": GOLD})
    text_block(img, "Thousands of years old... and still preserved.", F_SMALL, 560, t, (255, 235, 200), 6.2)


X_AT = 1.7


def s_science(img, d, t):
    bokeh(img, t, 3, (255, 230, 170))
    camera(img, t, art_science(t, X_AT), (W / 2, 1450))
    finish(img, t, 3)
    tag(img, "HOW?", t, (60, 140, 90))
    title_pop(img, "Almost no water", F_BIG, 410, t)
    text_block(img, "So germs can't survive. It's a little acidic, too.", F_SMALL, 590, t, (220, 245, 225), 2.8)


def s_bee(img, d, t):
    bokeh(img, t, 4, (255, 230, 170))
    camera(img, t, art_bee_power(t), (W / 2, 1450))
    finish(img, t, 4)
    tag(img, "BEE SUPERPOWER", t, (220, 160, 30))
    title_pop(img, "A natural germ killer!", F_MID, 400, t)
    text_block(img, "Bees add an enzyme that makes hydrogen peroxide.", F_SMALL, 560, t, (255, 240, 205), 0.6)


def s_wound(img, d, t):
    bokeh(img, t, 5, (255, 220, 160))
    camera(img, t, art_wound(t), (W / 2, 1450))
    finish(img, t, 5)
    tag(img, "ANCIENT MEDICINE", t, (40, 70, 160))
    title_pop(img, "Honey on wounds!", F_MID, 400, t, colors={"HONEY": GOLD})


COUNT_AT = 4.3


def s_flowers(img, d, t):
    bokeh(img, t, 6, (255, 210, 230))
    camera(img, t, art_flowers(t, COUNT_AT), (W / 2, 1450))
    finish(img, t, 6)
    tag(img, "THE CRAZY PART", t, (170, 60, 110))
    title_pop(img, "2 million flowers!", F_BIG, 410, t)


def s_teaspoon(img, d, t):
    bokeh(img, t, 7, (255, 230, 170))
    camera(img, t, art_teaspoon(t), (W / 2, 1450))
    finish(img, t, 7)
    tag(img, "ONE BEE'S LIFE", t, (220, 160, 30))
    title_pop(img, "Just 1/12 of a teaspoon!", F_MID, 400, t)


def s_kurdistan(img, d, t):
    parallax(img, t, [(1150, 900, (90, 100, 140), 6, 170), (1290, 800, (80, 130, 75), 18, 90)])
    camera(img, t, art_kurdistan(t), (W / 2, 1450))
    finish(img, t, 8)
    tag(img, "HERE AT HOME", t, (200, 60, 60))
    title_pop(img, "Kurdish mountain honey", F_MID, 400, t, colors={"HONEY": GOLD})
    text_block(img, "Famous for its amazing taste.", F_SMALL, 560, t, (255, 235, 220), 2.6)


MELT_AT = 2.7


def s_warm(img, d, t):
    bokeh(img, t, 9, (200, 225, 255))
    camera(img, t, art_warm(t, MELT_AT), (W / 2, 1450))
    finish(img, t, 9)
    tag(img, "TIP", t, (60, 120, 190))
    title_pop(img, "Hard honey? Warm it up!", F_MID, 400, t, colors={"HONEY": GOLD})


def s_cta(img, d, t):
    text_block(img, "Learned something new?", F_MID, 330, t, delay=0.0)
    make_salt.draw_cta(img, d, W / 2, 1250, t, off=0.4)


base.TRANSITION = splat
base.SCENES[:] = [
    (4.0, ((60, 35, 10), (16, 9, 3)), s_hook),
    (10.0, ((70, 50, 25), (20, 14, 6)), s_tomb),
    (6.0, ((40, 60, 40), (12, 18, 12)), s_science),
    (6.0, ((60, 45, 15), (18, 12, 4)), s_bee),
    (5.0, ((35, 45, 80), (10, 12, 24)), s_wound),
    (6.0, ((60, 25, 55), (20, 8, 25)), s_flowers),
    (4.0, ((60, 45, 15), (18, 12, 4)), s_teaspoon),
    (6.0, ((70, 90, 140), (30, 50, 30)), s_kurdistan),
    (6.0, ((25, 45, 75), (8, 14, 24)), s_warm),
    (6.0, ((30, 30, 40), (8, 8, 12)), s_cta),
]

if __name__ == "__main__":
    base.main()
