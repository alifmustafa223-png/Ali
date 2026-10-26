"""YouTube Short #12: "Lobster Was Once PRISON FOOD?!" (ketchup-video animation style + strong hook)."""
import math

from PIL import Image, ImageDraw

import make_ketchup
import make_salt
import make_short as base
from make_carrot import parallax
from make_chocolate import VIGNETTE, dust, sparkle, title_pop
from make_honey import slam
from make_ketchup import camera, face, splat, stamp
from make_pizza import back, bokeh
from make_short import F_BIG, F_MID, F_SMALL, H, W, ease, font, FONT_B, person, tag, text_block

RED, RED_DARK, RED_LIGHT = (215, 60, 40), (165, 40, 28), (240, 110, 80)
GOLD = (255, 190, 70)
make_ketchup.SPLAT_COLOR = (225, 75, 45)
base.HOOK_SKIP = 0.0


# ---------- drawings ----------

def lobster(d, x, y, s, t, ang=0.0, col=RED, dark=RED_DARK):
    """Lobster facing up (claws on top); (x, y) is the body centre. Claws snap open and shut."""
    c, sn = math.cos(ang), math.sin(ang)
    def rot(px, py):
        return (x + (px * c - py * sn) * s, y + (px * sn + py * c) * s)
    def ell(px, py, rx, ry, fill):
        pts = [rot(px + rx * math.cos(a), py + ry * math.sin(a)) for a in [k * math.pi / 12 for k in range(24)]]
        d.polygon(pts, fill=fill)
    for side in (-1, 1):  # legs
        for k in range(4):
            d.line([rot(side * 40, -30 + k * 30), rot(side * 95, -10 + k * 34)], fill=dark, width=max(2, int(8 * s)))
    for k in range(5):  # tail segments + fan
        ell(0, 70 + k * 38, 52 - k * 6, 26, col if k % 2 == 0 else RED_LIGHT)
    d.polygon([rot(0, 250), rot(-70, 310), rot(-25, 320), rot(0, 300), rot(25, 320), rot(70, 310)], fill=dark)
    ell(0, -10, 60, 90, col)  # body
    ell(0, -110, 38, 40, col)  # head
    for side in (-1, 1):
        d.line([rot(side * 14, -140), rot(side * 120, -330)], fill=dark, width=max(2, int(5 * s)))  # antennae
        d.ellipse([rot(side * 18, -128)[0] - 9 * s, rot(side * 18, -128)[1] - 9 * s, rot(side * 18, -128)[0] + 9 * s, rot(side * 18, -128)[1] + 9 * s], fill=(25, 20, 20))
        d.line([rot(side * 45, -60), rot(side * 110, -150)], fill=col, width=max(2, int(26 * s)))  # arm
        snap = 0.35 + 0.3 * abs(math.sin(t * 4 + side))
        cx_, cy_ = 110 * side, -200
        ell(cx_, cy_, 48, 70, col)  # claw
        jaw_a = -math.pi / 2 + side * snap
        d.polygon([rot(cx_ - 20 * side, cy_ - 50), rot(cx_ - 20 * side + math.cos(jaw_a) * 25, cy_ - 50 + math.sin(jaw_a) * 110), rot(cx_ + 15 * side, cy_ - 60)], fill=col)


def frown_face(d, cx, cy, s=1.0):
    for ex in (-22, 22):
        d.ellipse([cx + ex * s - 8 * s, cy - 10 * s, cx + ex * s + 8 * s, cy + 10 * s], fill=(40, 25, 20))
        d.line([(cx + ex * s - 14 * s, cy - 24 * s - ex * 0.3 * s), (cx + ex * s + 14 * s, cy - 24 * s + ex * 0.3 * s)], fill=(40, 25, 20), width=max(2, int(5 * s)))
    d.arc([cx - 24 * s, cy + 22 * s, cx + 24 * s, cy + 52 * s], 200, 340, fill=(120, 50, 40), width=max(2, int(6 * s)))


def plate(d, cx, cy, s=1.0):
    d.ellipse([cx - 260 * s, cy - 70 * s, cx + 260 * s, cy + 70 * s], fill=(235, 235, 240))
    d.ellipse([cx - 200 * s, cy - 50 * s, cx + 200 * s, cy + 50 * s], fill=(250, 250, 252))


def price_tag(d, x, y, text, p, col=GOLD):
    f = font(FONT_B, max(10, int(80 * p)))
    tw = d.textlength(text, font=f)
    d.polygon([(x - tw / 2 - 60 * p, y), (x - tw / 2 - 20 * p, y - 55 * p), (x + tw / 2 + 30 * p, y - 55 * p), (x + tw / 2 + 30 * p, y + 55 * p), (x - tw / 2 - 20 * p, y + 55 * p)], fill=col)
    d.ellipse([x - tw / 2 - 34 * p, y - 10 * p, x - tw / 2 - 14 * p, y + 10 * p], fill=(40, 30, 20))
    d.text((x - tw / 2 + 4, y - f.size * 0.6), text, font=f, fill=(40, 30, 20))


def bars(d, x0, x1, y0, y1, n=6):
    for k in range(n):
        x = x0 + (x1 - x0) * (k + 0.5) / n
        d.rounded_rectangle([x - 12, y0, x + 12, y1], radius=10, fill=(120, 125, 135))
        d.line([(x - 5, y0 + 10), (x - 5, y1 - 10)], fill=(170, 175, 185), width=4)
    d.rectangle([x0, y0, x1, y0 + 24], fill=(100, 105, 115))
    d.rectangle([x0, y1 - 24, x1, y1], fill=(100, 105, 115))


# ---------- illustrations ----------

def art_hook(t, price_at):
    def draw(d):
        cx = W / 2
        lobster(d, cx - 120, 1430, 1.15, t, ang=math.sin(t * 1.5) * 0.08)
        bars(d, cx - 450, cx + 210, 880, 1850, n=6)
        if t >= price_at:  # second beat: a price tag pops in and climbs to $$$$
            p = back((t - price_at) / 0.3)
            n = 1 + min(3, int((t - price_at) / 0.25))
            price_tag(d, cx + 330, 1250, "$" * n, p)
            for k in range(5):
                ph = (t * 0.9 + k * 0.2) % 1
                sparkle(d, cx + 330 + math.cos(k * 1.3 + t) * 170, 1250 + math.sin(k * 2.1 + t) * 120, 13 * math.sin(ph * math.pi) + 2)
    return draw


def art_beach(t, ruler_at):
    def draw(d):
        cy = 1450
        d.rectangle([0, cy + 150, W, H], fill=(225, 200, 150))  # sand
        for k in range(4):  # waves rolling in
            y = cy + 40 + k * 32
            d.line([(j * 40, y + math.sin(j * 0.5 + t * 3 + k) * 12) for j in range(30)], fill=(90, 160, 210), width=10)
        n = int(min(9, t / 0.35 + 1))
        spots = [(-260, 0), (-90, 0), (80, 0), (250, 0), (-175, -120), (0, -120), (170, -120), (-85, -240), (90, -240)]
        for k in range(n):  # pile grows
            dx, dy = spots[k]
            p = back((t - k * 0.35) / 0.3)
            lobster(d, W / 2 - 80 + dx, cy + 200 + dy, 0.45 * p, t + k, ang=(k % 3 - 1) * 0.6)
        if t > ruler_at:  # a ruler shows "2 FT"
            q = ease((t - ruler_at) / 0.5)
            rx, top, bot = W - 170, cy + 330 - 520 * q, cy + 330
            d.rectangle([rx - 30, top, rx + 30, bot], fill=(250, 220, 90))
            for k in range(int((bot - top) / 40)):
                d.line([(rx - 30, bot - k * 40), (rx - 5, bot - k * 40)], fill=(80, 60, 30), width=4)
            if q > 0.95:
                f = font(FONT_B, 64)
                d.rounded_rectangle([rx - 120, top - 90, rx + 60, top - 10], radius=18, fill=(30, 25, 20, 230))
                d.text((rx - 100, top - 85), "2 FT", font=f, fill=GOLD)
    return draw


def art_gross(t, bait_at, soil_at):
    def draw(d):
        cx, cy = W / 2, 1450
        person(d, cx - 250, cy + 260, 1.35, (90, 110, 70))
        frown_face(d, cx - 250, cy + 260 - 1.35 * 200, 1.25)
        d.line([(cx - 170, cy + 10), (cx - 245, cy - 110)], fill=(225, 175, 135), width=36)  # hand pinching nose
        lobster(d, cx + 220, cy - 30, 0.75, t, ang=0.15)
        f = font(FONT_B, 40)
        lab = "SEA COCKROACH?"
        tw = d.textlength(lab, font=f)
        d.rounded_rectangle([cx + 220 - tw / 2 - 18, cy - 360, cx + 220 + tw / 2 + 18, cy - 300], radius=16, fill=(40, 30, 30, 230))
        d.text((cx + 220 - tw / 2, cy - 356), lab, font=f, fill=(255, 220, 200))
        pb = back((t - bait_at) / 0.35)
        if pb > 0:  # fishing hook = bait
            hx, hy = cx + 80, cy + 300
            d.line([(hx, hy - 180 * pb), (hx, hy)], fill=(200, 200, 210), width=6)
            d.arc([hx - 40 * pb, hy - 30 * pb, hx + 40 * pb, hy + 50 * pb], 0, 180, fill=(200, 200, 210), width=8)
        ps = back((t - soil_at) / 0.35)
        if ps > 0:  # plant growing from soil = fertilizer
            gx, gy = cx + 330, cy + 360
            d.chord([gx - 110 * ps, gy - 40 * ps, gx + 110 * ps, gy + 60 * ps], 180, 360, fill=(110, 75, 45))
            d.line([(gx, gy), (gx, gy - 150 * ps)], fill=(70, 150, 70), width=10)
            d.ellipse([gx - 70 * ps, gy - 170 * ps, gx, gy - 120 * ps], fill=(80, 170, 70))
            d.ellipse([gx, gy - 200 * ps, gx + 70 * ps, gy - 150 * ps], fill=(80, 170, 70))
    return draw


def art_prison(t, again_at):
    def draw(d):
        cx, cy = W / 2, 1450
        person(d, cx - 120, cy + 280, 1.4, (235, 235, 235))
        for k in range(4):  # striped prison shirt (body only, below the head)
            y = cy + 115 + k * 52
            d.rectangle([cx - 245, y, cx + 5, y + 24], fill=(40, 40, 50))
        frown_face(d, cx - 120, cy + 280 - 1.4 * 200, 1.3)
        plate(d, cx + 230, cy + 260, 0.75)
        lobster(d, cx + 230, cy + 200, 0.42, t, ang=math.pi / 2)
        bars(d, 30, W - 30, 880, 1880, n=8)
        if t > again_at:  # thought bubble: "Lobster AGAIN?!"
            p = back((t - again_at) / 0.35)
            bx, by = cx + 170, cy - 380
            for r, dx, dy in ((14, -150, 190), (24, -110, 140)):
                d.ellipse([bx + dx - r * p, by + dy - r * p, bx + dx + r * p, by + dy + r * p], fill=(255, 255, 255))
            d.rounded_rectangle([bx - 230 * p, by - 70 * p, bx + 230 * p, by + 70 * p], radius=int(50 * p), fill=(255, 255, 255))
            f = font(FONT_B, max(10, int(56 * p)))
            txt = "Lobster AGAIN?!"
            tw = d.textlength(txt, font=f)
            d.text((bx - tw / 2, by - f.size * 0.6), txt, font=f, fill=(200, 50, 40))
    return draw


def art_train(t):
    def draw(d):
        cy = 1500
        d.rectangle([0, cy + 170, W, cy + 190], fill=(90, 80, 70))
        for k in range(14):
            x = (k * 90 - t * 300) % (W + 90) - 45
            d.rectangle([x - 8, cy + 165, x + 8, cy + 200], fill=(110, 85, 60))
        tx = -500 + ease(t / 3.0) * 920
        for car in range(3):  # carriages
            x0 = tx - car * 330
            d.rounded_rectangle([x0 - 150, cy - 40, x0 + 150, cy + 140], radius=20, fill=(150, 40, 50) if car else (50, 50, 60))
            for w in (-90, 90):
                d.ellipse([x0 + w - 40, cy + 110, x0 + w + 40, cy + 190], fill=(40, 40, 45))
            if car:
                for k in range(3):
                    d.rectangle([x0 - 120 + k * 90, cy - 10, x0 - 60 + k * 90, cy + 50], fill=(255, 225, 140))
            else:
                d.rectangle([x0 + 60, cy - 160, x0 + 110, cy - 40], fill=(40, 40, 45))  # chimney
                for k in range(4):  # smoke puffs
                    ph = (t * 0.8 + k * 0.25) % 1
                    r = 30 + ph * 60
                    d.ellipse([x0 + 85 - r - ph * 160, cy - 200 - ph * 260 - r, x0 + 85 + r - ph * 160, cy - 200 - ph * 260 + r], fill=(230, 230, 235, int(200 * (1 - ph))))
        px, py = W - 170, cy + 60  # rich traveler standing on the platform
        person(d, px, py, 0.9, (40, 40, 60))
        d.rectangle([px - 55, py - 235, px + 55, py - 215], fill=(25, 25, 30))
        d.rectangle([px - 35, py - 315, px + 35, py - 225], fill=(25, 25, 30))
        face(d, px, py - 0.9 * 200, t, 0.9)
    return draw


def art_fancy(t, treasure_at):
    def draw(d):
        cx, cy = W / 2, 1480
        plate(d, cx, cy + 120, 1.3)
        lobster(d, cx, cy + 20, 0.62, t, ang=math.pi / 2)
        d.rectangle([cx - 380, cy - 220, cx - 350, cy + 60], fill=(245, 240, 230))  # candle
        fl = 1 + 0.15 * math.sin(t * 9)
        d.ellipse([cx - 380, cy - 290 * fl, cx - 350, cy - 220], fill=(255, 200, 70))
        u = ease((t - treasure_at) / 0.6)  # trash can turns into a treasure chest
        x, y = cx + 330, cy - 260
        if u < 0.5:
            d.rounded_rectangle([x - 70, y - 60, x + 70, y + 110], radius=10, fill=(120, 130, 140))
            d.rectangle([x - 85, y - 85, x + 85, y - 60], fill=(100, 110, 120))
        else:
            d.rounded_rectangle([x - 100, y - 40, x + 100, y + 100], radius=14, fill=(150, 90, 40))
            d.chord([x - 100, y - 120, x + 100, y + 40], 180, 360, fill=(170, 105, 50))
            d.rectangle([x - 100, y - 45, x + 100, y - 30], fill=GOLD)
            for k in range(5):
                ph = (t * 1.2 + k * 0.2) % 1
                sparkle(d, x + math.cos(k * 1.26 + t) * 140, y - 40 + math.sin(k * 1.26 + t) * 110, 12 * math.sin(ph * math.pi) + 2)
    return draw


def art_today(t, count_at):
    def draw(d):
        cx, cy = W / 2, 1480
        plate(d, cx, cy + 180, 1.4)
        lobster(d, cx, cy + 60, 0.75, t, ang=math.pi / 2)
        q = ease((t - count_at) / 1.6)
        n = int(50 * q)
        price_tag(d, cx, cy - 330, f"${n}+", 1.0)
    return draw


# ---------- scenes ----------

def finish(img, t, seed):
    dust(img, t, seed)
    img.alpha_composite(VIGNETTE)


SLAM_AT, PRICE_AT = 1.35, 3.0


def s_hook(img, d, t):
    bokeh(img, t, 1, (255, 200, 180))
    camera(img, t + 0.5, art_hook(t, PRICE_AT), (W / 2, 1400))
    finish(img, t, 1)
    dd = ImageDraw.Draw(img, "RGBA")
    tw = dd.textlength("Lobster was once", font=F_MID)
    dd.text(((W - tw) / 2 + 4, 385), "Lobster was once", font=F_MID, fill=(0, 0, 0, 140))
    dd.text(((W - tw) / 2, 380), "Lobster was once", font=F_MID, fill=(255, 255, 255))
    slam(img, "PRISON FOOD", 500, t, SLAM_AT, (255, 120, 90), 118)


RULER_AT = 8.3


def s_beach(img, d, t):
    camera(img, t, art_beach(t, RULER_AT), (W / 2, 1450))
    finish(img, t, 2)
    tag(img, "NEW ENGLAND · 1600s", t, (40, 120, 170))
    title_pop(img, "Lobsters EVERYWHERE!", F_MID, 400, t, colors={"EVERYWHERE!": (255, 140, 110)})
    text_block(img, "They washed up on beaches in piles.", F_SMALL, 560, t, (215, 235, 250), 5.5)


BAIT_AT, SOIL_AT = 5.9, 6.7


def s_gross(img, d, t):
    bokeh(img, t, 3, (200, 230, 200))
    camera(img, t, art_gross(t, BAIT_AT, SOIL_AT), (W / 2, 1450))
    finish(img, t, 3)
    tag(img, "GROSS!", t, (90, 130, 70))
    title_pop(img, "Fish bait & fertilizer", F_MID, 400, t)


AGAIN_AT = 7.8


def s_prison(img, d, t):
    camera(img, t, art_prison(t, AGAIN_AT), (W / 2, 1450))
    finish(img, t, 4)
    tag(img, "THE CRAZY PART", t, (170, 60, 110))
    title_pop(img, "Fed to prisoners!", F_BIG, 410, t)
    text_block(img, "And to servants... who complained!", F_SMALL, 590, t, (255, 225, 240), 4.1)


def s_train(img, d, t):
    parallax(img, t, [(1150, 900, (80, 90, 130), 10, 150), (1300, 800, (70, 110, 70), 30, 60)])
    camera(img, t, art_train(t), (W / 2, 1450))
    finish(img, t, 5)
    tag(img, "1800s · TRAINS", t, (150, 60, 60))
    title_pop(img, "Rich travelers loved it", F_MID, 400, t)
    text_block(img, "They didn't know its bad reputation!", F_SMALL, 560, t, (235, 225, 225), 3.8)


TREASURE_AT = 4.8


def s_fancy(img, d, t):
    bokeh(img, t, 6, (255, 220, 160))
    camera(img, t, art_fancy(t, TREASURE_AT), (W / 2, 1450))
    finish(img, t, 6)
    tag(img, "FANCY DISH", t, (200, 150, 30))
    title_pop(img, "From trash to treasure", F_MID, 400, t, colors={"TREASURE": GOLD})


COUNT_AT = 3.0


def s_today(img, d, t):
    bokeh(img, t, 7, (255, 220, 160))
    camera(img, t, art_today(t, COUNT_AT), (W / 2, 1450))
    finish(img, t, 7)
    tag(img, "TODAY", t, (230, 60, 60))
    title_pop(img, "Not bad for a sea cockroach!", F_MID, 400, t)


def s_cta(img, d, t):
    text_block(img, "Learned something new?", F_MID, 330, t, delay=0.0)
    make_salt.draw_cta(img, d, W / 2, 1250, t, off=0.3)


base.TRANSITION = splat
base.SCENES[:] = [
    (5.0, ((60, 25, 25), (16, 6, 6)), s_hook),
    (9.0, ((60, 110, 160), (20, 50, 80)), s_beach),
    (8.0, ((45, 60, 40), (12, 18, 12)), s_gross),
    (9.0, ((45, 45, 55), (12, 12, 16)), s_prison),
    (8.0, ((70, 90, 140), (30, 50, 30)), s_train),
    (8.0, ((60, 30, 25), (16, 8, 6)), s_fancy),
    (7.0, ((60, 25, 25), (16, 6, 6)), s_today),
    (6.0, ((30, 30, 40), (8, 8, 12)), s_cta),
]

if __name__ == "__main__":
    base.main()
