"""YouTube Short #6: "Coffee Was Once BANNED?!" (reuses the style from make_short.py)."""
import math

from PIL import Image, ImageDraw

import make_short as base
import make_salt
from make_short import F_BIG, F_MID, F_SMALL, W, ease, font, FONT_B, person, tag, text_block

COFFEE, CREMA, CUP = (95, 55, 30), (190, 130, 75), (245, 240, 230)
RED = (230, 40, 50)


def steam(d, cx, top, t, n=3, length=9, spread=60):
    for k in range(n):
        pts = [(cx - spread + k * spread + math.sin(j * 0.5 + t * 3 + k) * 18, top - j * 22) for j in range(length)]
        d.line(pts, fill=(255, 255, 255, 110), width=11)


def cup(d, cx, cy, t, s=1.0, steaming=True):
    """Coffee cup on a saucer; cy is the saucer centre."""
    d.ellipse([cx - 230 * s, cy - 30 * s, cx + 230 * s, cy + 40 * s], fill=(225, 220, 210))
    d.chord([cx - 170 * s, cy - 260 * s, cx + 170 * s, cy + 20 * s], 0, 180, fill=CUP)
    d.rectangle([cx - 170 * s, cy - 120 * s, cx + 170 * s, cy - 110 * s], fill=CUP)
    d.ellipse([cx - 170 * s, cy - 150 * s, cx + 170 * s, cy - 90 * s], fill=CUP)
    d.ellipse([cx - 150 * s, cy - 140 * s, cx + 150 * s, cy - 100 * s], fill=COFFEE)
    d.ellipse([cx - 60 * s, cy - 130 * s, cx + 60 * s, cy - 110 * s], fill=CREMA)
    d.arc([cx + 130 * s, cy - 110 * s, cx + 250 * s, cy + 0 * s], 270, 90, fill=CUP, width=int(26 * s))
    if steaming:
        steam(d, cx, cy - 170 * s, t)


def stamp(d, cx, cy, word, t, start):
    a = ease((t - start) / 0.3)
    if a <= 0:
        return
    sc = 1.6 - 0.6 * a
    f = font(FONT_B, int(140 * sc))
    tw = d.textlength(word, font=f)
    bw, bh = tw + 80 * sc, 200 * sc
    x0, y0 = cx - bw / 2, cy - bh / 2
    col = RED + (int(235 * a),)
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=int(24 * sc), outline=col, width=int(16 * sc))
    d.text((cx - tw / 2, y0 + 12 * sc), word, font=f, fill=col)


def goat(d, x, y, t, k, flip=1):
    hop = abs(math.sin(t * 5 + k * 1.3)) * 70
    y -= hop
    body = (235, 230, 220)
    d.ellipse([x - 120, y - 70, x + 120, y + 60], fill=body)
    for lx in (-80, -40, 40, 80):
        kick = math.sin(t * 10 + lx + k) * 12
        d.line([(x + lx, y + 40), (x + lx + kick, y + 140)], fill=body, width=20)
        d.ellipse([x + lx + kick - 12, y + 132, x + lx + kick + 12, y + 150], fill=(90, 80, 70))
    hx = x + 120 * flip
    d.line([(x + 80 * flip, y - 30), (hx, y - 110)], fill=body, width=50)
    d.ellipse([hx - 50, y - 170, hx + 50, y - 80], fill=body)
    d.arc([hx - 40 * flip - 30, y - 230, hx - 40 * flip + 30, y - 150], 180, 360, fill=(120, 100, 80), width=12)
    d.ellipse([hx + 10 * flip - 9, y - 140, hx + 10 * flip + 9, y - 122], fill=(30, 30, 30))
    d.polygon([(hx + 10 * flip, y - 85), (hx + 30 * flip, y - 85), (hx + 20 * flip, y - 45)], fill=(200, 195, 185))  # beard
    for nx in range(3):  # music notes = "dancing"
        ph = (t * 0.8 + nx * 0.33 + k * 0.5) % 1
        nxp = x - 60 + nx * 60
        nyp = y - 250 - ph * 200
        d.ellipse([nxp - 14, nyp - 10, nxp + 14, nyp + 10], fill=(255, 220, 120, int(255 * (1 - ph))))
        d.line([(nxp + 12, nyp), (nxp + 12, nyp - 50)], fill=(255, 220, 120, int(255 * (1 - ph))), width=5)


def draw_goats(d, cx, cy, t):
    d.rectangle([0, cy + 200, W, cy + 650], fill=(90, 130, 60))
    bx, by = cx, cy + 120
    d.ellipse([bx - 170, by - 150, bx + 170, by + 110], fill=(50, 110, 55))
    for k in range(9):
        x = bx - 120 + (k * 67) % 240
        y = by - 100 + (k * 43) % 170
        d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=(215, 35, 45))
    goat(d, cx - 300, cy + 130, t, 0, flip=1)
    goat(d, cx + 300, cy + 130, t, 1, flip=-1)


def draw_yemen(img, d, cx, cy, t):
    moon = Image.new("RGBA", img.size, (0, 0, 0, 0))
    md = ImageDraw.Draw(moon)
    md.ellipse([cx + 230, cy - 560, cx + 370, cy - 420], fill=(250, 240, 200, 255))
    md.ellipse([cx + 270, cy - 580, cx + 410, cy - 440], fill=(0, 0, 0, 0))  # crescent cut-out
    img.alpha_composite(moon)
    for k in range(12):
        x = (k * 173) % W
        y = cy - 520 + (k * 97) % 260
        r = 4 + (math.sin(t * 3 + k) + 1) * 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 230))
    # dallah coffee pot, tilting to pour
    tilt = 0.35 + 0.1 * math.sin(t * 1.5)
    px, py = cx - 120, cy - 40
    def rot(x, y):
        c, sn = math.cos(tilt), math.sin(tilt)
        return (px + x * c - y * sn, py + x * sn + y * c)
    gold, dark = (220, 170, 60), (170, 120, 40)
    d.polygon([rot(-120, 120), rot(120, 120), rot(90, -20), rot(-90, -20)], fill=gold)
    d.polygon([rot(-60, -20), rot(60, -20), rot(40, -120), rot(-40, -120)], fill=dark)
    d.polygon([rot(-50, -120), rot(50, -120), rot(0, -200)], fill=gold)
    d.polygon([rot(100, 0), rot(240, -110), rot(250, -90), rot(115, 40)], fill=gold)  # spout
    sx, sy = rot(248, -100)
    tx, ty = cx + 180, cy + 220
    d.line([(sx, sy), (sx + 20, (sy + ty - 60) / 2), (tx, ty - 60)], fill=COFFEE, width=12)
    # small handle-less cup (finjan)
    d.chord([tx - 90, ty - 120, tx + 90, ty + 60], 0, 180, fill=CUP)
    d.ellipse([tx - 90, ty - 50, tx + 90, ty - 10], fill=COFFEE)
    d.ellipse([tx - 140, ty + 50, tx + 140, ty + 80], fill=(225, 220, 210))


def draw_coffeehouse(d, cx, cy, t):
    d.rectangle([0, cy + 250, W, cy + 650], fill=(120, 70, 40))
    for k in range(3):  # hanging lamps
        lx = 200 + k * 340
        sw = math.sin(t * 2 + k) * 10
        d.line([(lx, cy - 560), (lx + sw, cy - 440)], fill=(60, 40, 25), width=4)
        d.ellipse([lx + sw - 40, cy - 450, lx + sw + 40, cy - 380], fill=(255, 190, 80))
    person(d, cx - 300, cy + 130, 1.15, (60, 110, 160))
    person(d, cx + 300, cy + 130, 1.15, (170, 60, 60))
    d.rectangle([cx - 210, cy + 110, cx + 210, cy + 140], fill=(90, 50, 25))
    d.rectangle([cx - 20, cy + 140, cx + 20, cy + 300], fill=(90, 50, 25))
    # game board on the table
    d.rectangle([cx - 140, cy + 70, cx + 140, cy + 110], fill=(200, 160, 100))
    for k in range(6):
        d.polygon([(cx - 130 + k * 47, cy + 110), (cx - 106 + k * 47, cy + 110), (cx - 118 + k * 47, cy + 78)], fill=(120, 60, 30) if k % 2 else (240, 230, 210))
    for x in (cx - 180, cx + 180):
        cup(d, x, cy + 100, t, 0.28, steaming=False)
    # speech bubbles take turns
    for k, (bx, by) in enumerate([(cx - 260, cy - 330), (cx + 260, cy - 330)]):
        on = (int(t / 1.5) % 2) == k
        if on:
            d.rounded_rectangle([bx - 120, by - 70, bx + 120, by + 50], radius=40, fill=(255, 255, 255))
            d.polygon([(bx - 20 + 40 * (1 if k == 0 else -1), by + 45), (bx + 20 + 40 * (1 if k == 0 else -1), by + 45), (bx + 60 * (1 if k == 0 else -1) * 0.2, by + 100)], fill=(255, 255, 255))
            for j in range(3):
                r = 13 + 4 * math.sin(t * 6 + j)
                d.ellipse([bx - 60 + j * 60 - r, by - 10 - r, bx - 60 + j * 60 + r, by - 10 + r], fill=(120, 120, 130))


def draw_ban(d, cx, cy, t, start):
    shake = math.sin(t * 30) * 10 * max(0.0, 1 - abs(t - start - 0.3) * 3)
    cup(d, cx + shake, cy + 220, t, 1.1, steaming=False)
    stamp(d, cx, cy - 40, "BANNED", t, start)


def draw_love(d, cx, cy, t):
    cup(d, cx, cy + 200, t, 1.1, steaming=False)
    for k in range(7):
        ph = (t * 0.5 + k / 7) % 1
        x = cx - 150 + (k * 53) % 300 + math.sin(t * 2 + k) * 25
        y = cy + 20 - ph * 520
        s = 26 * (1 - ph * 0.4)
        a = int(255 * (1 - ph))
        d.ellipse([x - s, y - s, x, y], fill=(240, 70, 100, a))
        d.ellipse([x, y - s, x + s, y], fill=(240, 70, 100, a))
        d.polygon([(x - s, y - s / 2), (x + s, y - s / 2), (x, y + s * 0.9)], fill=(240, 70, 100, a))


def draw_today(img, d, cx, cy, t):
    n = int(min(20, t * 9))
    for i in range(n):
        r, c = divmod(i, 4)
        x = cx - 330 + c * 220
        y = cy - 330 + r * 170
        pop = ease((t - i / 9) / 0.25)
        cup(d, x, y + 60, t, 0.33 * pop, steaming=False)
    count = int(2_000_000_000 * ease(t / 2.2))
    f = font(FONT_B, 88)
    txt = f"{count:,}+"
    tw = d.textlength(txt, font=f)
    d.text((cx - tw / 2, cy + 560), txt, font=f, fill=(255, 190, 70))
    fs = font(FONT_B, 48)
    lab = "cups every single day"
    lw = d.textlength(lab, font=fs)
    d.text((cx - lw / 2, cy + 670), lab, font=fs, fill=(240, 230, 220))


# ---------- scenes ----------

def s_hook(img, d, t):
    cup(d, W / 2, 1550, t, 1.3)
    text_block(img, "Your morning coffee", F_MID, 380, t)
    text_block(img, "was once", F_MID, 480, t, delay=0.2)
    a = ease((t - 0.5) / 0.4)
    size = int(160 + 30 * math.sin(min(t, 1.5) * 4) * (1 - min(t / 1.5, 1)))
    f = font(FONT_B, max(60, size))
    if a > 0:
        dd = ImageDraw.Draw(img)
        tw = dd.textlength("ILLEGAL", font=f)
        dd.text(((W - tw) / 2, 590), "ILLEGAL", font=f, fill=RED + (int(255 * a),))


def s_goats(img, d, t):
    tag(img, "THE LEGEND · ETHIOPIA", t, (200, 70, 30))
    draw_goats(d, W / 2, 1350, t)
    text_block(img, "Kaldi's dancing goats", F_MID, 400, t, delay=0.2)
    text_block(img, "The story goes: they ate red berries... and couldn't sleep!", F_SMALL, 560, t, (255, 225, 190), 1.0)


def s_yemen(img, d, t):
    tag(img, "YEMEN · 1400s", t, (60, 70, 150))
    draw_yemen(img, d, W / 2, 1400, t)
    text_block(img, "Coffee for night prayers", F_MID, 400, t, delay=0.2)
    text_block(img, "Sufis drank it to stay awake.", F_SMALL, 560, t, (220, 225, 255), 1.0)


def s_house(img, d, t):
    tag(img, "COFFEE HOUSES", t, (160, 90, 40))
    draw_coffeehouse(d, W / 2, 1450, t)
    text_block(img, "\"Schools of the wise\"", F_MID, 400, t, delay=0.2)
    text_block(img, "People talked, played games and shared the news.", F_SMALL, 560, t, (255, 235, 210), 1.0)


BAN_START = 3.6


def s_ban(img, d, t):
    tag(img, "THE CRAZY PART · 1511", t, (170, 60, 110))
    draw_ban(d, W / 2, 1300, t, BAN_START)
    text_block(img, "Coffee was banned in Mecca!", F_MID, 400, t, delay=0.2)
    text_block(img, "Rulers feared people were gathering to talk about them.", F_SMALL, 650, t, (255, 225, 240), 5.5)


def s_love(img, d, t):
    draw_love(d, W / 2, 1300, t)
    text_block(img, "But it didn't work.", F_BIG, 430, t, delay=0.1)
    text_block(img, "People loved coffee way too much.", F_SMALL, 620, t, (255, 225, 230), 1.0)


def s_today(img, d, t):
    tag(img, "TODAY", t, (230, 60, 60))
    draw_today(img, d, W / 2, 1150, t)
    text_block(img, "Over 2 billion cups a day!", F_MID, 400, t, delay=0.2)


def s_cta(img, d, t):
    text_block(img, "Learned something new?", F_MID, 330, t, delay=0.0)
    make_salt.draw_cta(img, d, W / 2, 1250, t, off=0.5)


base.SCENES[:] = [
    (3.0, ((45, 25, 15), (12, 6, 3)), s_hook),
    (9.0, ((60, 100, 140), (40, 60, 30)), s_goats),
    (7.0, ((30, 25, 55), (8, 6, 18)), s_yemen),
    (9.0, ((70, 40, 25), (22, 12, 6)), s_house),
    (8.0, ((60, 25, 55), (20, 8, 25)), s_ban),
    (5.0, ((70, 25, 40), (20, 6, 12)), s_love),
    (5.0, ((45, 25, 15), (12, 6, 3)), s_today),
    (6.0, ((30, 30, 40), (8, 8, 12)), s_cta),
]

if __name__ == "__main__":
    base.main()
