"""YouTube Short #2: "Where Did Bread Come From?" (reuses the style from make_short.py)."""
import math

from PIL import ImageDraw

import make_short as base
from make_short import F_BIG, F_MID, F_SMALL, W, draw_fire, ease, font, FONT_B, tag, text_block

CRUST, CRUST_DARK, CRUMB = (196, 126, 58), (150, 88, 38), (240, 205, 150)


def steam(d, cx, top, t, n=3, length=10, spread=90):
    for k in range(n):
        pts = [(cx - spread + k * spread + math.sin(j * 0.5 + t * 3 + k) * 22, top - j * 22) for j in range(length)]
        d.line(pts, fill=(255, 255, 255, 110), width=12)


def draw_loaf(d, cx, cy, t, s=1.0):
    d.ellipse([cx - 300 * s, cy + 90 * s, cx + 300 * s, cy + 150 * s], fill=(0, 0, 0, 70))
    d.chord([cx - 280 * s, cy - 200 * s, cx + 280 * s, cy + 220 * s], 180, 360, fill=CRUST)
    d.rectangle([cx - 280 * s, cy, cx + 280 * s, cy + 110 * s], fill=CRUST)
    d.rounded_rectangle([cx - 280 * s, cy + 40 * s, cx + 280 * s, cy + 120 * s], radius=int(40 * s), fill=CRUST_DARK)
    for k in range(3):
        x = cx - 140 * s + k * 140 * s
        d.line([(x - 50 * s, cy - 60 * s), (x + 50 * s, cy - 150 * s)], fill=CRUMB, width=int(18 * s))
    steam(d, cx, cy - 230 * s, t)


def draw_flatbread(d, cx, cy, t):
    draw_fire(d, cx, cy + 260, t, 0.55)
    d.ellipse([cx - 330, cy - 40, cx + 330, cy + 150], fill=(110, 110, 115))
    d.ellipse([cx - 310, cy - 60, cx + 310, cy + 110], fill=(150, 150, 155))
    d.ellipse([cx - 220, cy - 40, cx + 220, cy + 70], fill=(225, 185, 120))
    for k in range(9):
        x = cx - 160 + (k * 47) % 320
        y = cy - 15 + (k * 31) % 70
        d.ellipse([x - 14, y - 9, x + 14, y + 9], fill=(150, 95, 45))
    for k in range(12):  # scattered grains
        x = cx - 380 + k * 70
        y = cy - 170 + math.sin(k * 2.1) * 40
        d.ellipse([x - 12, y - 20, x + 12, y + 20], fill=(222, 180, 90))
    steam(d, cx, cy - 80, t, length=8)


def wheat(d, x, base_y, h, t, k):
    sway = math.sin(t * 2 + k * 0.7) * 30
    top = (x + sway, base_y - h)
    d.line([(x, base_y), top], fill=(170, 140, 60), width=8)
    for j in range(6):
        fx = x + sway * (1 - j * 0.04)
        fy = base_y - h + j * 26
        d.ellipse([fx - 30, fy - 12, fx - 4, fy + 14], fill=(235, 190, 80))
        d.ellipse([fx + 4, fy - 12, fx + 30, fy + 14], fill=(235, 190, 80))


def draw_field(d, cx, cy, t):
    r = 120 + 6 * math.sin(t * 2)
    d.ellipse([cx + 230 - r, cy - 260 - r, cx + 230 + r, cy - 260 + r], fill=(255, 205, 90))
    d.rectangle([0, cy + 230, W, cy + 600], fill=(110, 80, 40))
    for k in range(11):
        wheat(d, 70 + k * 95, cy + 250, 420 + (k * 53) % 120, t, k)


def draw_rising(d, cx, cy, t):
    for px, ph in [(cx - 260, 300), (cx + 200, 400)]:
        d.polygon([(px - ph * 0.9, cy - 100), (px + ph * 0.9, cy - 100), (px, cy - 100 - ph)], fill=(150, 115, 70))
    rise = ease(t / 4.5)
    dh = 60 + 230 * rise
    d.ellipse([cx - 230, cy - dh, cx + 230, cy + dh * 0.3 + 40], fill=(245, 225, 185))
    for k in range(int(rise * 9)):
        x = cx - 140 + (k * 61) % 280
        y = cy - dh * 0.6 + (k * 37) % int(dh * 0.6 + 1)
        rr = 10 + (k % 3) * 5
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(210, 180, 130), width=4)
    d.chord([cx - 300, cy - 60, cx + 300, cy + 300], 0, 180, fill=(180, 100, 60))
    d.line([(cx - 300, cy + 120), (cx + 300, cy + 120)], fill=(140, 75, 45), width=14)


def draw_pyramid_pay(d, cx, cy, t):
    d.polygon([(cx - 420, cy + 150), (cx + 420, cy + 150), (cx, cy - 330)], fill=(205, 165, 95))
    d.polygon([(cx, cy - 330), (cx + 420, cy + 150), (cx + 120, cy + 150)], fill=(175, 135, 75))
    bob = abs(math.sin(t * 3)) * 25
    for k, x in enumerate([cx - 200, cx + 30]):
        y = cy + 260 - (bob if k == 0 else 0)
        d.chord([x - 110, y - 90, x + 110, y + 90], 180, 360, fill=CRUST)
        d.rectangle([x - 110, y, x + 110, y + 30], fill=CRUST_DARK)
    jy = cy + 260 - (0 if bob > 12 else bob)
    x = cx + 240
    d.polygon([(x - 60, jy - 120), (x + 60, jy - 120), (x + 90, jy + 10), (x + 50, jy + 40), (x - 50, jy + 40), (x - 90, jy + 10)], fill=(170, 85, 55))
    d.rectangle([x - 40, jy - 150, x + 40, jy - 120], fill=(140, 70, 45))


def draw_breads(d, cx, cy, t):
    # tanoor
    d.rounded_rectangle([cx + 80, cy - 40, cx + 400, cy + 360], radius=60, fill=(185, 120, 80))
    glow = 180 + int(60 * math.sin(t * 6))
    d.ellipse([cx + 150, cy - 70, cx + 330, cy + 10], fill=(255, glow, 60))
    # naan sliding out
    slide = ease(t / 1.5)
    nx = cx + 240 - 330 * slide
    ny = cy - 140 - 60 * slide
    d.ellipse([nx - 160, ny - 70, nx + 160, ny + 70], fill=(230, 180, 105))
    for k in range(7):
        d.ellipse([nx - 100 + k * 32 - 9, ny - 20 + (k % 3) * 18 - 7, nx - 100 + k * 32 + 9, ny - 20 + (k % 3) * 18 + 7], fill=(165, 100, 45))
    # baguette + round loaf
    d.line([(cx - 420, cy + 330), (cx - 30, cy + 130)], fill=CRUST, width=90)
    for k in range(4):
        x = cx - 360 + k * 90
        y = cy + 300 - k * 46
        d.line([(x - 15, y + 25), (x + 30, y - 20)], fill=CRUMB, width=12)
    d.chord([cx - 260, cy + 220, cx + 40, cy + 460], 180, 360, fill=CRUST_DARK)
    d.rectangle([cx - 260, cy + 340, cx + 40, cy + 380], fill=CRUST_DARK)
    steam(d, nx, ny - 90, t, length=6, spread=60)


def draw_timeline(d, cx, cy, t):
    draw_loaf(d, cx, cy - 120, t, 0.8)
    y = cy + 250
    prog = ease(t / 2.5)
    d.line([(120, y), (120 + (W - 240) * prog, y)], fill=(255, 190, 70), width=10)
    for k in range(5):
        x = 120 + k * (W - 240) / 4
        if (x - 120) / (W - 240) <= prog + 1e-6:
            d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=(255, 190, 70))


# ---------- scenes ----------

def s_hook(img, d, t):
    draw_loaf(d, W / 2, 1420, t, 1.1)
    text_block(img, "Where did", F_MID, 420, t)
    a = ease((t - 0.4) / 0.4)
    size = int(150 + 30 * math.sin(min(t, 1.5) * 4) * (1 - min(t / 1.5, 1)))
    f = font(FONT_B, max(60, size))
    if a > 0:
        dd = ImageDraw.Draw(img)
        tw = dd.textlength("BREAD", font=f)
        dd.text(((W - tw) / 2, 560), "BREAD", font=f, fill=(255, 190, 70, int(255 * a)))
    text_block(img, "come from?", F_MID, 780, t, delay=0.6)


def s_flat(img, d, t):
    tag(img, "ABOUT 14,000 YEARS AGO", t, (200, 70, 30))
    draw_flatbread(d, W / 2, 1300, t)
    text_block(img, "The first flatbread", F_BIG, 430, t, delay=0.2)
    text_block(img, "Hunters crushed wild grains and baked them on hot stones.", F_SMALL, 760, t, (255, 225, 190), 0.9)


def s_farm(img, d, t):
    tag(img, "ABOUT 9,000 YEARS AGO", t, (120, 140, 40))
    draw_field(d, W / 2, 1300, t)
    text_block(img, "People started farming grain.", F_MID, 400, t, delay=0.2)
    text_block(img, "Jarmo, one of the first farming villages, is right here in Kurdistan!", F_SMALL, 640, t, (240, 240, 200), 1.0)


def s_rise(img, d, t):
    tag(img, "ABOUT 5,000 YEARS AGO", t, (180, 120, 40))
    draw_rising(d, W / 2, 1380, t)
    text_block(img, "Then bread learned to rise.", F_MID, 400, t, delay=0.2)
    text_block(img, "In ancient Egypt, dough left out too long bubbled up with wild yeast.", F_SMALL, 640, t, (255, 235, 200), 1.0)


def s_pyramid(img, d, t):
    tag(img, "THE CRAZY PART", t, (170, 60, 110))
    draw_pyramid_pay(d, W / 2, 1300, t)
    text_block(img, "Pyramid builders were paid in bread...", F_MID, 400, t, delay=0.2)
    text_block(img, "...and beer!", F_BIG, 640, t, (255, 190, 70), 1.4)


def s_today(img, d, t):
    tag(img, "TODAY", t, (230, 60, 60))
    draw_breads(d, W / 2, 1250, t)
    text_block(img, "Thousands of breads worldwide.", F_MID, 400, t, delay=0.2)
    text_block(img, "From French baguettes to fresh naan from the tanoor.", F_SMALL, 640, t, (220, 230, 255), 0.9)


def s_end(img, d, t):
    draw_timeline(d, W / 2, 1300, t)
    text_block(img, "14,000 years in every bite.", F_MID, 400, t, delay=0.1)
    text_block(img, "Follow for more!", F_SMALL, 1720, t, (255, 210, 120), 1.5)


base.SCENES[:] = [
    (3.0, ((45, 25, 10), (12, 6, 3)), s_hook),
    (9.0, ((60, 25, 15), (15, 8, 5)), s_flat),
    (8.0, ((40, 70, 110), (90, 70, 35)), s_farm),
    (8.0, ((75, 55, 30), (25, 18, 10)), s_rise),
    (6.0, ((60, 25, 55), (20, 8, 25)), s_pyramid),
    (8.0, ((30, 40, 70), (10, 12, 28)), s_today),
    (8.0, ((50, 30, 15), (12, 8, 5)), s_end),
]

if __name__ == "__main__":
    base.main()
