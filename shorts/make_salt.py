"""YouTube Short #5: "Why Salt Was Worth More Than Gold" (reuses the style from make_short.py)."""
import math

from PIL import ImageDraw

import make_short as base
from make_short import F_BIG, F_MID, F_SMALL, F_TAG, W, ease, font, FONT_B, person, tag, text_block

SALT = (245, 245, 250)
GOLD = (240, 190, 50)


def sparkle(d, x, y, r, col=(255, 255, 255)):
    d.polygon([(x, y - r * 2), (x + r * 0.5, y), (x, y + r * 2), (x - r * 0.5, y)], fill=col)
    d.polygon([(x - r * 2, y), (x, y + r * 0.5), (x + r * 2, y), (x, y - r * 0.5)], fill=col)


def shaker(d, cx, cy, t, s=1.0, pour=True):
    tilt = math.sin(t * 3) * 0.15 if pour else 0
    def rot(px, py):
        py = -py
        c, sn = math.cos(tilt), math.sin(tilt)
        return (cx + (px * c - py * sn) * s, cy + (px * sn + py * c) * s)
    d.polygon([rot(-110, -40), rot(110, -40), rot(130, 260), rot(-130, 260)], fill=(225, 235, 245, 150))
    d.polygon([rot(-100, 60), rot(100, 60), rot(122, 250), rot(-122, 250)], fill=SALT)
    d.polygon([rot(-115, -40), rot(115, -40), rot(100, -150), rot(-100, -150)], fill=(190, 195, 205))
    d.polygon([rot(-100, -150), rot(100, -150), rot(80, -175), rot(-80, -175)], fill=(170, 175, 185))
    for hx in (-45, 0, 45):
        x, y = rot(hx, -162)
        d.ellipse([x - 9 * s, y - 6 * s, x + 9 * s, y + 6 * s], fill=(90, 95, 105))
    if pour:
        for k in range(16):
            ph = (t * 1.2 + k * 0.0625) % 1
            x, y = rot(-40 + (k * 37) % 80, -180)
            y -= 0
            yy = y + ph * 380 * s
            xx = x + math.sin(k) * 30 * s * ph
            d.rectangle([xx - 5 * s, yy - 5 * s, xx + 5 * s, yy + 5 * s], fill=SALT)


def draw_barrel(d, cx, cy, t):
    d.rounded_rectangle([cx - 240, cy - 200, cx + 240, cy + 300], radius=80, fill=(140, 85, 45))
    for y in (cy - 120, cy + 50, cy + 220):
        d.rectangle([cx - 245, y - 14, cx + 245, y + 14], fill=(90, 90, 100))
    d.ellipse([cx - 230, cy - 250, cx + 230, cy - 150], fill=(110, 65, 35))
    d.ellipse([cx - 210, cy - 240, cx + 210, cy - 160], fill=SALT)
    bob = math.sin(t * 2) * 8
    # fish
    d.ellipse([cx - 170, cy - 300 + bob, cx + 10, cy - 220 + bob], fill=(120, 160, 190))
    d.polygon([(cx + 5, cy - 260 + bob), (cx + 70, cy - 300 + bob), (cx + 70, cy - 220 + bob)], fill=(120, 160, 190))
    d.ellipse([cx - 140, cy - 275 + bob, cx - 120, cy - 255 + bob], fill=(30, 30, 30))
    # meat leg
    d.ellipse([cx + 40, cy - 330 - bob, cx + 190, cy - 210 - bob], fill=(190, 80, 70))
    d.line([(cx + 170, cy - 230 - bob), (cx + 240, cy - 170 - bob)], fill=(245, 235, 220), width=22)
    for k in range(18):
        ph = (t * 0.9 + k * 0.055) % 1
        x = cx - 200 + (k * 53) % 400
        y = cy - 540 + ph * 310
        d.rectangle([x - 6, y - 6, x + 6, y + 6], fill=SALT)


def camel(d, x, y, t, k, load=SALT):
    d.ellipse([x - 120, y - 80, x + 120, y + 40], fill=(170, 115, 60))
    d.ellipse([x - 70, y - 150, x + 10, y - 50], fill=(170, 115, 60))
    d.line([(x + 100, y - 40), (x + 150, y - 160)], fill=(170, 115, 60), width=36)
    d.ellipse([x + 120, y - 200, x + 210, y - 145], fill=(170, 115, 60))
    for lx in (-80, -30, 50, 90):
        d.line([(x + lx, y + 20), (x + lx + math.sin(t * 8 + lx + k) * 10, y + 160)], fill=(150, 100, 50), width=18)
    for sx in (-75, 15):
        d.rounded_rectangle([x + sx - 45, y - 200, x + sx + 45, y - 110], radius=30, fill=load)


def draw_salt_road(d, cx, cy, t):
    d.ellipse([-300, cy + 120, W + 300, cy + 700], fill=(215, 170, 100))
    d.ellipse([-200, cy + 220, W + 500, cy + 800], fill=(195, 145, 80))
    off = (t * 70) % 520
    for k in range(3):
        camel(d, -200 + off + k * 520 - 520, cy + 170 + math.sin(t * 4 + k) * 6, t, k)
    # road sign
    sx, sy = cx + 260, cy - 260
    d.rectangle([sx - 12, sy, sx + 12, sy + 330], fill=(110, 70, 40))
    d.rounded_rectangle([sx - 200, sy - 90, sx + 200, sy + 20], radius=12, fill=(245, 235, 210), outline=(110, 70, 40), width=8)
    f = font(FONT_B, 54)
    tw = d.textlength("VIA SALARIA", font=f)
    d.text((sx - tw / 2, sy - 72), "VIA SALARIA", font=f, fill=(110, 50, 30))


def draw_word(img, d, cx, cy, t):
    f = font(FONT_B, 210)
    a1 = ease(t / 0.5)
    tw = d.textlength("SAL", font=f)
    d.text((cx - tw / 2, cy - 380), "SAL", font=f, fill=(255, 255, 255, int(255 * a1)))
    fs = font(FONT_B, 48)
    lab = "(Latin for salt)"
    lw = d.textlength(lab, font=fs)
    d.text((cx - lw / 2, cy - 130), lab, font=fs, fill=(220, 220, 230, int(220 * a1)))
    a2 = ease((t - 1.2) / 0.4)
    if a2 > 0:
        y = cy - 20 + (1 - a2) * 40
        d.polygon([(cx - 40, y), (cx + 40, y), (cx, y + 70)], fill=(255, 190, 70, int(255 * a2)))
    a3 = ease((t - 2.0) / 0.5)
    if a3 > 0:
        tw = d.textlength("SALARY", font=f)
        d.text((cx - tw / 2, cy + 90 + (1 - a3) * 50), "SALARY", font=f, fill=GOLD + (int(255 * a3),))
        for k in range(5):
            ang = t * 1.5 + k * 1.26
            sparkle(d, cx + math.cos(ang) * 420, cy + 200 + math.sin(ang) * 180, 12 * a3, (255, 230, 120))


def draw_salt_money(d, cx, cy, t):
    for row in range(4):
        for col in range(4 - row):
            x = cx - 230 + col * 150 + row * 75
            y = cy + 200 - row * 95
            d.rounded_rectangle([x - 70, y - 40, x + 70, y + 40], radius=14, fill=SALT, outline=(200, 205, 215), width=5)
            d.line([(x - 50, y - 18), (x + 50, y - 18)], fill=(215, 220, 230), width=5)
    glow = (math.sin(t * 3) + 1) / 2
    for k in range(7):
        ang = k * 0.9 + t * 0.6
        sparkle(d, cx + math.cos(ang) * 380, cy + 40 + math.sin(ang) * 260, 10 + glow * 8, (255, 225, 120))
    for k in range(3):  # gold coins for comparison
        x = cx - 260 + k * 60
        y = cy + 330
        d.ellipse([x - 45, y - 45, x + 45, y + 45], fill=GOLD, outline=(200, 150, 30), width=6)


def draw_march(d, cx, cy, t):
    d.rectangle([0, cy + 260, W, cy + 650], fill=(150, 120, 80))
    sea_x = W - 300
    d.rectangle([sea_x, cy + 200, W, cy + 650], fill=(50, 110, 170))
    for k in range(5):
        y = cy + 230 + k * 70
        d.line([(sea_x + j * 30, y + math.sin(j * 0.7 + t * 3 + k) * 8) for j in range(12)], fill=(110, 170, 220), width=6)
    prog = ease(t / 6.0)
    x = 140 + prog * (sea_x - 260)
    for k in range(int(prog * 12)):
        fx = 140 + k * (sea_x - 260) / 12
        d.ellipse([fx - 10, cy + 300, fx + 10, cy + 314], fill=(110, 85, 55))
    step = math.sin(t * 6) * 8
    person(d, x, cy + 120 + step, 1.1, (245, 240, 225), skin=(160, 110, 75))
    d.line([(x + 70, cy - 40), (x + 110, cy + 270)], fill=(120, 80, 40), width=12)  # walking stick
    d.ellipse([x - 35, cy - 160 + step, x + 35, cy - 135 + step], outline=(40, 40, 40), width=5)  # glasses hint


def thumbs_up(d, cx, cy, s, col):
    crease = (40, 90, 200) if col[0] < 200 else (190, 190, 200)
    d.rounded_rectangle([cx - 150 * s, cy - 10 * s, cx - 105 * s, cy + 140 * s], radius=int(12 * s), fill=col)  # cuff
    d.rounded_rectangle([cx - 90 * s, cy - 10 * s, cx + 100 * s, cy + 140 * s], radius=int(34 * s), fill=col)  # fist
    d.rounded_rectangle([cx - 90 * s, cy - 150 * s, cx - 25 * s, cy + 20 * s], radius=int(30 * s), fill=col)  # thumb
    for k in range(3):  # finger creases
        y = cy + (35 + k * 35) * s
        d.line([(cx + 5 * s, y), (cx + 95 * s, y)], fill=crease, width=max(2, int(6 * s)))


def draw_cta(img, d, cx, cy, t, off=0.0):
    t = t - off
    # LIKE: thumb pops in and turns blue on "tap"
    a = ease((t - 0.3) / 0.4)
    if a > 0:
        tapped = t > 1.6
        pulse = 1 + (0.18 * math.sin(min(1, (t - 1.6) / 0.3) * math.pi) if tapped else 0)
        col = (60, 140, 255) if tapped else (255, 255, 255)
        thumbs_up(d, cx, cy - 330, 1.3 * a * pulse, col)
        f = font(FONT_B, 64)
        tw = d.textlength("LIKE", font=f)
        d.text((cx - tw / 2, cy - 110), "LIKE", font=f, fill=(255, 255, 255, int(255 * a)))
    # SUBSCRIBE button: red, then pressed -> grey "SUBSCRIBED" + bell
    b = ease((t - 2.2) / 0.4)
    if b > 0:
        pressed = t > 3.6
        bw, bh = 640, 150
        y0 = cy + 60 + (1 - b) * 60
        sc = 0.94 if 3.6 < t < 3.8 else 1.0
        x0 = cx - bw * sc / 2
        fill = (90, 90, 95) if pressed else (230, 30, 35)
        d.rounded_rectangle([x0, y0, x0 + bw * sc, y0 + bh * sc], radius=int(75 * sc), fill=fill + (int(255 * b),))
        label = "SUBSCRIBED" if pressed else "SUBSCRIBE"
        f = font(FONT_B, 70)
        tw = d.textlength(label, font=f)
        d.text((cx - tw / 2, y0 + 30 * sc), label, font=f, fill=(255, 255, 255, int(255 * b)))
        if pressed:
            bx, by = cx, y0 + bh + 140
            swing = math.sin(t * 10) * 0.25 * max(0, 1 - (t - 3.6) / 1.5)
            pts = []
            for k in range(13):
                u = k / 12
                w = 70 * (0.45 + 0.55 * u ** 1.5)
                pts.append((-w, -90 + u * 150))
            pts = pts + [(-x, y) for x, y in reversed(pts)]
            c, sn = math.cos(swing), math.sin(swing)
            d.polygon([(bx + x * c - y * sn, by + x * sn + y * c) for x, y in pts], fill=GOLD)
            d.ellipse([bx - 18, by + 55, bx + 18, by + 90], fill=GOLD)
    # cursor/tap finger
    if 1.2 < t < 4.2:
        target = (cx + 20, cy - 280) if t < 2.6 else (cx + 230, cy + 160)
        d.ellipse([target[0] + 30, target[1] + 30, target[0] + 90, target[1] + 90], fill=(255, 255, 255, 200), outline=(0, 0, 0, 120), width=4)


# ---------- scenes ----------

def s_hook(img, d, t):
    shaker(d, W / 2, 1300, t, 1.3)
    text_block(img, "The salt on your table was once worth a", F_MID, 380, t)
    a = ease((t - 0.5) / 0.4)
    size = int(150 + 30 * math.sin(min(t, 1.5) * 4) * (1 - min(t / 1.5, 1)))
    f = font(FONT_B, max(60, size))
    if a > 0:
        dd = ImageDraw.Draw(img)
        tw = dd.textlength("FORTUNE", font=f)
        dd.text(((W - tw) / 2, 620), "FORTUNE", font=f, fill=GOLD + (int(255 * a),))


def s_preserve(img, d, t):
    tag(img, "BEFORE FRIDGES", t, (40, 110, 160))
    draw_barrel(d, W / 2, 1400, t)
    text_block(img, "Salt kept food alive.", F_BIG, 430, t, delay=0.2)
    text_block(img, "No salt? No food for winter.", F_SMALL, 760, t, (220, 235, 255), 1.0)


def s_road(img, d, t):
    tag(img, "THE SALT ROADS", t, (180, 120, 40))
    draw_salt_road(d, W / 2, 1250, t)
    text_block(img, "Salt made cities rich.", F_MID, 400, t, delay=0.2)
    text_block(img, "Rome even built a road just for salt.", F_SMALL, 560, t, (255, 235, 200), 4.9)


def s_word(img, d, t):
    tag(img, "WORD FACT", t, (90, 70, 170))
    draw_word(img, d, W / 2, 1250, t)
    text_block(img, "Salary comes from salt!", F_MID, 400, t, delay=0.2)


def s_money(img, d, t):
    tag(img, "THE CRAZY PART", t, (170, 60, 110))
    draw_salt_money(d, W / 2, 1300, t)
    text_block(img, "Salt bars were money!", F_BIG, 430, t, delay=0.2)
    text_block(img, "In Ethiopia, even in the 1900s.", F_SMALL, 760, t, (255, 225, 240), 1.0)


def s_march(img, d, t):
    tag(img, "1930", t, (200, 110, 30))
    draw_march(d, W / 2, 1300, t)
    text_block(img, "The Salt March", F_BIG, 430, t, delay=0.2)
    text_block(img, "Gandhi walked almost 400 km to the sea to make his own salt, protesting a British salt tax.", F_SMALL, 620, t, (255, 235, 200), 1.0)


def s_today(img, d, t):
    tag(img, "TODAY", t, (230, 60, 60))
    shaker(d, W / 2, 1250, t, 1.2)
    text_block(img, "We sprinkle it without thinking.", F_MID, 400, t, delay=0.2)


def s_cta(img, d, t):
    text_block(img, "Learned something new?", F_MID, 330, t, delay=0.0)
    draw_cta(img, d, W / 2, 1250, t)


base.SCENES[:] = [
    (3.0, ((40, 40, 55), (10, 10, 16)), s_hook),
    (8.0, ((25, 50, 75), (8, 16, 26)), s_preserve),
    (10.0, ((70, 110, 150), (110, 80, 40)), s_road),
    (6.0, ((40, 30, 75), (12, 10, 26)), s_word),
    (7.0, ((60, 25, 55), (20, 8, 25)), s_money),
    (9.0, ((80, 55, 30), (25, 16, 8)), s_march),
    (4.0, ((40, 40, 55), (10, 10, 16)), s_today),
    (6.0, ((30, 30, 40), (8, 8, 12)), s_cta),
]

if __name__ == "__main__":
    base.main()
