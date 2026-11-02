"""YouTube Short #3: "How Did Humans Start Drinking Tea?" (reuses the style from make_short.py)."""
import math

from PIL import ImageDraw

import make_short as base
from make_short import F_BIG, F_MID, F_SMALL, W, draw_fire, ease, font, FONT_B, person, tag, text_block

TEA, TEA_LIGHT, GLASS = (170, 45, 25), (215, 85, 40), (235, 240, 245)


def steam(d, cx, top, t, n=3, length=10, spread=70):
    for k in range(n):
        pts = [(cx - spread + k * spread + math.sin(j * 0.5 + t * 3 + k) * 20, top - j * 22) for j in range(length)]
        d.line(pts, fill=(255, 255, 255, 110), width=11)


def leaf(d, x, y, ang, s=1.0, col=(80, 160, 70)):
    pts = []
    for k in range(13):
        u = k / 12
        w = math.sin(u * math.pi) * 22 * s
        px, py = (u - 0.5) * 90 * s, w
        pts.append((px, py))
    pts += [(px, -py) for px, py in reversed(pts)]
    c, sn = math.cos(ang), math.sin(ang)
    d.polygon([(x + px * c - py * sn, y + px * sn + py * c) for px, py in pts], fill=col)


def istikan(d, cx, cy, s=1.0, level=1.0):
    """Tulip-shaped tea glass on a saucer; cy is the saucer centre."""
    d.ellipse([cx - 210 * s, cy - 35 * s, cx + 210 * s, cy + 45 * s], fill=(200, 60, 50))
    d.ellipse([cx - 170 * s, cy - 25 * s, cx + 170 * s, cy + 25 * s], fill=(230, 90, 75))
    outline = [(-95, -330), (95, -330), (70, -200), (60, -170), (95, -60), (80, -10), (-80, -10), (-95, -60), (-60, -170), (-70, -200)]
    pts = [(cx + x * s, cy + y * s) for x, y in outline]
    d.polygon(pts, fill=GLASS + (90,))
    top = -10 - 290 * level
    inner = [(x * 0.88, max(y, top)) for x, y in outline]
    d.polygon([(cx + x * s, cy + y * s) for x, y in inner], fill=TEA)
    d.line([(cx - 60 * s, cy - 290 * s), (cx - 70 * s, cy - 220 * s)], fill=(255, 255, 255, 150), width=int(10 * s))
    d.line(pts + [pts[0]], fill=GLASS, width=int(6 * s))


def draw_legend(d, cx, cy, t):
    draw_fire(d, cx + 180, cy + 300, t, 0.5)
    d.chord([cx + 30, cy + 40, cx + 330, cy + 300], 0, 180, fill=(90, 90, 100))
    d.rectangle([cx + 30, cy + 150, cx + 330, cy + 170], fill=(70, 70, 80))
    person(d, cx - 220, cy + 160, 1.4, (220, 170, 40))
    d.polygon([(cx - 300, cy - 210), (cx - 140, cy - 210), (cx - 220, cy - 270)], fill=(40, 40, 40))  # hat
    for k in range(4):
        ph = (t * 0.35 + k * 0.25) % 1
        x = cx + 180 + math.sin(ph * 6 + k) * 90
        y = cy - 500 + ph * 640
        leaf(d, x, y, t * 2 + k, 0.9)
    steam(d, cx + 180, cy + 20, t, length=6)


def draw_teahouse(d, cx, cy, t):
    d.rectangle([cx - 300, cy - 100, cx + 300, cy + 300], fill=(150, 50, 40))
    d.polygon([(cx - 420, cy - 80), (cx + 420, cy - 80), (cx + 260, cy - 260), (cx - 260, cy - 260)], fill=(40, 90, 70))
    d.polygon([(cx - 420, cy - 80), (cx - 470, cy - 130), (cx - 380, cy - 100)], fill=(40, 90, 70))
    d.polygon([(cx + 420, cy - 80), (cx + 470, cy - 130), (cx + 380, cy - 100)], fill=(40, 90, 70))
    d.rectangle([cx - 70, cy + 80, cx + 70, cy + 300], fill=(90, 30, 25))
    for k, lx in enumerate([cx - 220, cx + 220]):
        sw = math.sin(t * 2 + k) * 8
        d.ellipse([lx - 45 + sw, cy - 60, lx + 45 + sw, cy + 40], fill=(255, 90, 60))
        d.rectangle([lx - 20 + sw, cy - 70, lx + 20 + sw, cy - 58], fill=(230, 180, 60))
    for k in range(3):
        x = cx - 200 + k * 200
        d.rounded_rectangle([x - 45, cy + 380, x + 45, cy + 460], radius=20, fill=(245, 240, 225))
        steam(d, x + 60, cy + 360, t + k, n=1, length=6, spread=60)


def draw_silk_road(d, cx, cy, t):
    d.ellipse([-300, cy + 120, W + 300, cy + 700], fill=(215, 170, 100))
    d.ellipse([-200, cy + 220, W + 500, cy + 800], fill=(195, 145, 80))
    off = (t * 70) % 520
    for k in range(3):
        x = -200 + off + k * 520 - 520
        y = cy + 170 + math.sin(t * 4 + k) * 6
        d.ellipse([x - 120, y - 80, x + 120, y + 40], fill=(170, 115, 60))   # body
        d.ellipse([x - 70, y - 150, x + 10, y - 50], fill=(170, 115, 60))   # hump
        d.line([(x + 100, y - 40), (x + 150, y - 160)], fill=(170, 115, 60), width=36)  # neck
        d.ellipse([x + 120, y - 200, x + 210, y - 145], fill=(170, 115, 60))  # head
        for lx in (-80, -30, 50, 90):
            d.line([(x + lx, y + 20), (x + lx + math.sin(t * 8 + lx) * 10, y + 160)], fill=(150, 100, 50), width=18)
        d.rounded_rectangle([x - 40, y - 210, x + 60, y - 150], radius=8, fill=(90, 50, 30))  # tea brick
    # floating tea brick "coin"
    by = cy - 220 + math.sin(t * 2) * 15
    d.rounded_rectangle([cx - 150, by - 90, cx + 150, by + 90], radius=16, fill=(95, 55, 30))
    for k in range(3):
        d.line([(cx - 110, by - 50 + k * 50), (cx + 110, by - 50 + k * 50)], fill=(125, 80, 45), width=8)


def draw_locked_box(d, cx, cy, t):
    open_a = 0.0
    d.rounded_rectangle([cx - 280, cy - 60, cx + 280, cy + 260], radius=20, fill=(120, 65, 35))
    d.rounded_rectangle([cx - 300, cy - 160 - open_a, cx + 300, cy - 40], radius=24, fill=(150, 85, 45))
    for x in (cx - 220, cx + 220):
        d.rectangle([x - 18, cy - 160, x + 18, cy + 260], fill=(210, 170, 70))
    shake = math.sin(t * 14) * 8 * (1 if (t % 2) < 0.6 else 0)
    lx = cx + shake
    d.arc([lx - 60, cy - 110, lx + 60, cy + 10], 180, 360, fill=(220, 200, 90), width=22)
    d.rounded_rectangle([lx - 80, cy - 50, lx + 80, cy + 90], radius=16, fill=(230, 190, 60))
    d.ellipse([lx - 16, cy - 10, lx + 16, cy + 22], fill=(60, 40, 20))
    d.rectangle([lx - 7, cy + 10, lx + 7, cy + 50], fill=(60, 40, 20))


def draw_today(d, cx, cy, t):
    istikan(d, cx, cy + 200, 1.3)
    drop = (t * 0.8) % 1.6
    if drop < 1:
        y = cy - 600 + ease(drop) * 330
        d.rounded_rectangle([cx - 40, y - 40, cx + 40, y + 40], radius=8, fill=(255, 255, 255))
    ang = t * 4
    sx = cx + math.cos(ang) * 35
    d.line([(sx, cy - 110), (sx + 70, cy - 380)], fill=(200, 200, 210), width=14)
    steam(d, cx, cy - 260, t)


def draw_end(d, cx, cy, t):
    istikan(d, cx, cy + 120, 1.1, level=ease(t / 2.5))
    steam(d, cx, cy - 280, t)


# ---------- scenes ----------

def s_hook(img, d, t):
    istikan(d, W / 2, 1600, 1.3)
    steam(d, W / 2, 1110, t)
    text_block(img, "Who drank", F_MID, 420, t)
    a = ease((t - 0.4) / 0.4)
    size = int(150 + 30 * math.sin(min(t, 1.5) * 4) * (1 - min(t / 1.5, 1)))
    f = font(FONT_B, max(60, size))
    if a > 0:
        dd = ImageDraw.Draw(img)
        tw = dd.textlength("TEA", font=f)
        dd.text(((W - tw) / 2, 560), "TEA", font=f, fill=(255, 190, 70, int(255 * a)))
    text_block(img, "first?", F_MID, 780, t, delay=0.6)


def s_legend(img, d, t):
    tag(img, "ABOUT 4,700 YEARS AGO", t, (200, 70, 30))
    draw_legend(d, W / 2, 1300, t)
    text_block(img, "A happy accident", F_BIG, 430, t, delay=0.2)
    text_block(img, "The story goes: leaves fell into Emperor Shen Nong's hot water.", F_SMALL, 640, t, (255, 225, 190), 0.9)


def s_teahouse(img, d, t):
    tag(img, "ANCIENT CHINA", t, (40, 120, 90))
    draw_teahouse(d, W / 2, 1250, t)
    text_block(img, "From medicine to everyday drink.", F_MID, 400, t, delay=0.2)
    text_block(img, "Soon, tea houses were everywhere.", F_SMALL, 640, t, (220, 245, 230), 1.0)


def s_silk(img, d, t):
    tag(img, "THE SILK ROAD", t, (180, 120, 40))
    draw_silk_road(d, W / 2, 1250, t)
    text_block(img, "Tea traveled by camel.", F_MID, 400, t, delay=0.2)
    text_block(img, "Tea pressed into bricks was even used as money!", F_SMALL, 560, t, (255, 235, 200), 1.0)


def s_box(img, d, t):
    tag(img, "THE CRAZY PART", t, (170, 60, 110))
    draw_locked_box(d, W / 2, 1300, t)
    text_block(img, "In Britain, tea was so expensive...", F_MID, 400, t, delay=0.2)
    text_block(img, "...people locked it in boxes!", F_MID, 640, t, (255, 190, 70), 1.4)


def s_today(img, d, t):
    tag(img, "TODAY", t, (230, 60, 60))
    draw_today(d, W / 2, 1380, t)
    text_block(img, "Here at home:", F_BIG, 400, t, delay=0.2)
    text_block(img, "Strong black tea, a little istikan glass, and lots of sugar.", F_SMALL, 560, t, (255, 225, 210), 0.9)


def s_end(img, d, t):
    draw_end(d, W / 2, 1350, t)
    text_block(img, "One accident. 4,700 years of tea.", F_MID, 400, t, delay=0.1)
    text_block(img, "Follow for more!", F_SMALL, 1720, t, (255, 210, 120), 1.5)


base.SCENES[:] = [
    (3.0, ((45, 20, 15), (12, 5, 4)), s_hook),
    (9.0, ((60, 25, 15), (15, 8, 5)), s_legend),
    (7.0, ((25, 60, 50), (8, 20, 16)), s_teahouse),
    (9.0, ((70, 110, 150), (110, 80, 40)), s_silk),
    (6.0, ((60, 25, 55), (20, 8, 25)), s_box),
    (8.0, ((70, 25, 25), (20, 6, 6)), s_today),
    (8.0, ((45, 20, 15), (12, 5, 4)), s_end),
]

if __name__ == "__main__":
    base.main()
