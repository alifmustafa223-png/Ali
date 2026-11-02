"""YouTube Short #4: "Where Did Ice Cream Come From?" (reuses the style from make_short.py)."""
import math

from PIL import ImageDraw

import make_short as base
from make_short import F_BIG, F_MID, F_SMALL, F_TAG, W, ease, font, FONT_B, person, tag, text_block

ICE = (190, 230, 250)
SCOOPS = [(250, 160, 190), (250, 240, 220), (140, 85, 55)]


def cone(d, cx, cy, t, s=1.0, scoops=3):
    """Waffle cone; cy is the top rim of the cone."""
    tip = (cx, cy + 420 * s)
    d.polygon([(cx - 130 * s, cy), (cx + 130 * s, cy), tip], fill=(215, 160, 80))
    for k in range(-4, 5):
        d.line([(cx + k * 34 * s, cy), (cx + k * 34 * s * 0.1 + 60 * s * (1 if k < 0 else -1) * 0.2, cy + 380 * s)], fill=(180, 120, 55), width=int(5 * s))
    for k in range(1, 7):
        y = cy + k * 55 * s
        half = 130 * s * (1 - (y - cy) / (420 * s))
        d.line([(cx - half, y), (cx + half, y)], fill=(180, 120, 55), width=int(5 * s))
    for i in range(scoops):
        col = SCOOPS[i % 3]
        y = cy - 70 * s - i * 120 * s
        r = (150 - i * 15) * s
        d.ellipse([cx - r, y - r * 0.85, cx + r, y + r * 0.85], fill=col)
    drip = (math.sin(t * 2) + 1) / 2
    d.rounded_rectangle([cx + 60 * s, cy - 20 * s, cx + 90 * s, cy + (40 + 60 * drip) * s], radius=int(15 * s), fill=SCOOPS[0])


def snow(d, t, n=14, top=900, bottom=1850):
    for k in range(n):
        ph = (t * 0.25 + k * 0.071) % 1
        x = (k * 157) % W + math.sin(t + k) * 20
        y = top + ph * (bottom - top)
        r = 6 + (k % 3) * 3
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 170))


def draw_yakhchal(d, cx, cy, t):
    r = 140 + 8 * math.sin(t * 2)
    d.ellipse([cx + 320 - r, cy - 360 - r, cx + 320 + r, cy - 360 + r], fill=(255, 190, 70))
    d.rectangle([0, cy + 200, W, cy + 700], fill=(220, 175, 105))
    pts = []
    for k in range(41):
        u = k / 40
        x = cx - 300 + 600 * u
        y = cy + 200 - 620 * (math.sin(u * math.pi) ** 1.6)
        pts.append((x, y))
    d.polygon(pts, fill=(190, 135, 80))
    for k in range(1, 6):  # brick courses
        y = cy + 200 - k * 100
        xs = [x for x, yy in pts if yy <= y]
        if xs:
            d.line([(min(xs) + 10, y), (max(xs) - 10, y)], fill=(160, 110, 60), width=6)
    d.chord([cx - 70, cy + 40, cx + 70, cy + 360], 180, 360, fill=(70, 40, 25))
    d.rectangle([cx - 70, cy + 200, cx + 70, cy + 210], fill=(70, 40, 25))
    for k in range(4):  # ice blocks sliding toward the door
        ph = (t * 0.3 + k * 0.25) % 1
        x = 60 + ph * (cx - 140)
        y = cy + 300
        d.rounded_rectangle([x - 45, y - 45, x + 45, y + 45], radius=10, fill=ICE, outline=(255, 255, 255), width=4)
    for k in range(4):  # heat shimmer
        y = cy - 300 + k * 50
        d.line([(80 + j * 30, y + math.sin(t * 5 + j + k) * 8) for j in range(8)], fill=(255, 220, 160, 90), width=5)


def draw_faloodeh(d, cx, cy, t):
    d.polygon([(cx - 280, cy - 150), (cx + 280, cy - 150), (cx + 180, cy + 180), (cx - 180, cy + 180)], fill=(220, 240, 250, 120))
    d.polygon([(cx - 250, cy - 110), (cx + 250, cy - 110), (cx + 170, cy + 160), (cx - 170, cy + 160)], fill=(245, 245, 250))
    for k in range(8):
        y = cy - 90 + k * 30
        d.line([(cx - 220 + k * 9 + j * 26, y + math.sin(j * 1.3 + t * 2 + k) * 9) for j in range(17 - k)], fill=(255, 255, 255), width=6)
    d.polygon([(cx - 250, cy - 110), (cx + 250, cy - 110), (cx + 225, cy - 30), (cx - 225, cy - 30)], fill=(240, 90, 120, 120))
    d.rectangle([cx - 40, cy + 180, cx + 40, cy + 260], fill=(220, 240, 250))
    d.ellipse([cx - 160, cy + 240, cx + 160, cy + 290], fill=(220, 240, 250))
    for k in range(6):  # rose petals
        ph = (t * 0.3 + k * 0.17) % 1
        x = cx - 250 + k * 100 + math.sin(t * 2 + k) * 30
        y = cy - 430 + ph * 330
        d.ellipse([x - 22, y - 14, x + 22, y + 14], fill=(235, 70, 110))


def draw_china(d, cx, cy, t):
    person(d, cx - 220, cy + 160, 1.4, (190, 40, 40))
    d.rectangle([cx - 300, cy - 225, cx - 140, cy - 205], fill=(30, 30, 30))
    d.rectangle([cx - 250, cy - 270, cx - 190, cy - 220], fill=(30, 30, 30))
    bx, by = cx + 200, cy + 200
    d.chord([bx - 200, by - 120, bx + 200, by + 160], 0, 180, fill=(40, 90, 160))
    for k in range(5):
        d.line([(bx - 160 + k * 80, by + 40), (bx - 140 + k * 80, by + 110)], fill=(250, 250, 255), width=8)
    bob = math.sin(t * 2) * 6
    d.chord([bx - 170, by - 170 + bob, bx + 170, by + 70 + bob], 180, 360, fill=(250, 245, 230))
    d.ellipse([bx - 40, by - 200 + bob, bx + 40, by - 130 + bob], fill=(255, 210, 120))
    snow(d, t)


def draw_myth(d, img, cx, cy, t):
    rock = math.sin(t * 2) * 12
    d.rectangle([0, cy + 230, W, cy + 650], fill=(40, 80, 140))
    for k in range(6):
        y = cy + 260 + k * 60
        d.line([(j * 40, y + math.sin(j * 0.6 + t * 3 + k) * 10) for j in range(30)], fill=(80, 130, 190), width=6)
    d.polygon([(cx - 300, cy + 150 + rock), (cx + 300, cy + 150 - rock), (cx + 220, cy + 280 - rock), (cx - 220, cy + 280 + rock)], fill=(120, 70, 40))
    d.line([(cx, cy + 160), (cx, cy - 330)], fill=(90, 55, 30), width=16)
    d.polygon([(cx + 10, cy - 320), (cx + 260, cy + 60), (cx + 10, cy + 100)], fill=(245, 235, 210))
    d.polygon([(cx - 10, cy - 260), (cx - 200, cy + 80), (cx - 10, cy + 100)], fill=(235, 225, 200))
    a = ease((t - 5.4) / 0.35)
    if a > 0:
        sc = 1.6 - 0.6 * a
        f = font(FONT_B, int(150 * sc))
        tw = d.textlength("MYTH", font=f)
        bw, bh = tw + 80 * sc, 210 * sc
        x0, y0 = cx - bw / 2, cy - 160 - bh / 2
        col = (230, 40, 50, int(235 * a))
        d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=int(24 * sc), outline=col, width=int(16 * sc))
        d.text((cx - tw / 2, y0 + 10 * sc), "MYTH", font=f, fill=col)


def draw_royal(d, cx, cy, t):
    d.polygon([(cx - 230, cy - 60), (cx + 230, cy - 60), (cx + 120, cy + 120), (cx - 120, cy + 120)], fill=(220, 240, 250, 140))
    d.rectangle([cx - 25, cy + 120, cx + 25, cy + 280], fill=(220, 240, 250))
    d.ellipse([cx - 150, cy + 260, cx + 150, cy + 310], fill=(220, 240, 250))
    for i, (dx, col) in enumerate([(-100, SCOOPS[0]), (100, SCOOPS[2]), (0, SCOOPS[1])]):
        y = cy - 120 - (60 if i == 2 else 0)
        d.ellipse([cx + dx - 130, y - 110, cx + dx + 130, y + 110], fill=col)
    bob = math.sin(t * 2) * 12
    y = cy - 420 + bob
    d.polygon([(cx - 170, y + 110), (cx - 170, y - 20), (cx - 85, y + 40), (cx, y - 70), (cx + 85, y + 40), (cx + 170, y - 20), (cx + 170, y + 110)], fill=(240, 190, 50))
    for x in (cx - 100, cx, cx + 100):
        d.ellipse([x - 18, y + 60, x + 18, y + 96], fill=(220, 50, 70))
    for k in range(6):  # sparkles
        ph = (t * 0.7 + k * 0.17) % 1
        x = cx + math.cos(k * 1.05 + t) * 330
        yy = cy - 200 + math.sin(k * 1.05 + t) * 260
        r = 14 * (1 - abs(ph - 0.5) * 2)
        d.polygon([(x, yy - r * 2), (x + r * 0.6, yy), (x, yy + r * 2), (x - r * 0.6, yy)], fill=(255, 230, 120))


def draw_end(d, cx, cy, t):
    cone(d, cx, cy - 80, t, 1.1)
    y = cy + 450
    prog = ease(t / 2.5)
    d.line([(120, y), (120 + (W - 240) * prog, y)], fill=(255, 190, 70), width=10)
    for k in range(5):
        x = 120 + k * (W - 240) / 4
        if (x - 120) / (W - 240) <= prog + 1e-6:
            d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=(255, 190, 70))


# ---------- scenes ----------

def s_hook(img, d, t):
    cone(d, W / 2, 1420, t, 1.0)
    text_block(img, "Ice cream is", F_MID, 420, t)
    a = ease((t - 0.4) / 0.4)
    size = int(130 + 30 * math.sin(min(t, 1.5) * 4) * (1 - min(t / 1.5, 1)))
    f = font(FONT_B, max(60, size))
    if a > 0:
        dd = ImageDraw.Draw(img)
        tw = dd.textlength("WAY OLDER", font=f)
        dd.text(((W - tw) / 2, 560), "WAY OLDER", font=f, fill=(255, 190, 70, int(255 * a)))
    text_block(img, "than you think.", F_MID, 760, t, delay=0.6)


def s_yakhchal(img, d, t):
    tag(img, "ABOUT 2,400 YEARS AGO", t, (200, 110, 30))
    draw_yakhchal(d, W / 2, 1350, t)
    text_block(img, "Ice in the desert?!", F_BIG, 430, t, delay=0.2)
    text_block(img, "Persians built giant ice houses called yakhchals.", F_SMALL, 620, t, (255, 235, 200), 0.9)


def s_faloodeh(img, d, t):
    tag(img, "ANCIENT PERSIA", t, (200, 60, 100))
    draw_faloodeh(d, W / 2, 1400, t)
    text_block(img, "Faloodeh", F_BIG, 430, t, delay=0.2)
    text_block(img, "Ice, rose water, syrup and thin noodles. One of the oldest frozen desserts!", F_SMALL, 620, t, (255, 220, 230), 0.9)


def s_china(img, d, t):
    tag(img, "OVER 1,000 YEARS AGO", t, (190, 40, 40))
    draw_china(d, W / 2, 1300, t)
    text_block(img, "Meanwhile in China...", F_MID, 400, t, delay=0.2)
    text_block(img, "Emperors enjoyed frozen milk treats.", F_SMALL, 560, t, (255, 225, 220), 0.9)


def s_myth(img, d, t):
    tag(img, "THE CRAZY PART", t, (170, 60, 110))
    draw_myth(d, img, W / 2, 1300, t)
    text_block(img, "Marco Polo brought ice cream to Europe?", F_MID, 400, t, delay=0.2)


def s_royal(img, d, t):
    tag(img, "THE 1600s", t, (200, 150, 30))
    draw_royal(d, W / 2, 1400, t)
    text_block(img, "A treat for kings.", F_BIG, 430, t, delay=0.2)
    text_block(img, "Then cafés in Paris sold it to everyone.", F_SMALL, 620, t, (255, 240, 200), 1.2)


def s_end(img, d, t):
    draw_end(d, W / 2, 1250, t)
    text_block(img, "It all started with ice in the desert.", F_MID, 400, t, delay=0.1)
    text_block(img, "Follow for more!", F_SMALL, 1760, t, (255, 210, 120), 1.5)


base.SCENES[:] = [
    (3.0, ((60, 30, 50), (15, 8, 14)), s_hook),
    (10.0, ((90, 60, 35), (40, 25, 12)), s_yakhchal),
    (10.0, ((70, 25, 45), (22, 8, 15)), s_faloodeh),
    (6.0, ((30, 45, 80), (10, 14, 28)), s_china),
    (8.0, ((60, 25, 55), (20, 8, 25)), s_myth),
    (8.0, ((60, 40, 15), (18, 12, 4)), s_royal),
    (8.0, ((60, 30, 50), (15, 8, 14)), s_end),
]

if __name__ == "__main__":
    base.main()
