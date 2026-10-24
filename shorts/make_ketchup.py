"""YouTube Short #9: "Ketchup Was Once Sold as MEDICINE?!" (reuses the style from make_short.py).

Animation upgrades over the chocolate video: ketchup-splat scene transitions, squash-and-stretch
pop-ins, blinking characters, and ketchup squiggles that draw themselves.
"""
import math

from PIL import Image, ImageDraw, ImageFilter

import make_short as base
import make_salt
from make_chocolate import VIGNETTE, dust, sparkle, title_pop
from make_pizza import back, bokeh
from make_short import F_BIG, F_MID, F_SMALL, H, W, ease, font, FONT_B, person, tag, text_block

KETCHUP, KETCHUP_DARK = (200, 30, 25), (150, 20, 18)
GLASS = (225, 235, 240)
GOLD, HOOKRED = (255, 190, 70), (245, 70, 60)

# ---------- new animation helpers ----------

_BLOBS = [((k * 389) % W, (k * 557) % H, 380 + (k * 131) % 260) for k in range(16)] + [(0, 0, 520), (W, 0, 520), (0, H, 520), (W, H, 520), (W / 2, H / 2, 600)]


def splat(img, t, dur, idx):
    """Scene change: ketchup blobs burst in to cover the frame, then pull back to reveal the next scene."""
    last = idx == len(base.SCENES) - 1
    c_in = 0.0 if idx == 0 else 1 - ease(t / 0.36)
    c_out = 0.0 if last else ease((t - (dur - 0.3)) / 0.3)
    c = max(c_in, c_out)
    if c <= 0.001:
        return img
    mask = Image.new("L", (W // 4, H // 4), 0)
    md = ImageDraw.Draw(mask)
    for i, (x, y, r) in enumerate(_BLOBS):
        rr = r * 1.3 * c * (0.85 + 0.15 * math.sin(i)) / 4
        md.ellipse([x / 4 - rr, y / 4 - rr, x / 4 + rr, y / 4 + rr], fill=255)
        for j in range(3 if 0.35 < c < 0.9 else 0):  # splash droplets, only mid-burst
            a = i * 1.7 + j * 2.1
            dr = rr * 1.35
            dx, dy = x / 4 + math.cos(a) * dr, y / 4 + math.sin(a) * dr
            s = rr * 0.18
            md.ellipse([dx - s, dy - s, dx + s, dy + s], fill=255)
    if c > 0.92:
        md.rectangle([0, 0, W // 4, H // 4], fill=255)
    mask = mask.resize((W, H), Image.BILINEAR)
    red = Image.new("RGBA", (W, H), KETCHUP + (255,))
    out = img.copy()
    out.paste(red, (0, 0), mask)
    return out


def camera(img, t, draw_fn, anchor):
    """Art layer with soft shadow; pops in with squash-and-stretch, then slowly pushes in."""
    art = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(art, "RGBA"))
    a = art.getchannel("A").resize((W // 6, H // 6), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    a = a.resize((W, H), Image.BILINEAR).point(lambda v: int(v * 0.5))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 255), (0, 22), a.crop((0, 0, W, H - 22)))
    layer = Image.alpha_composite(shadow, art)
    pop = back(t / 0.5)
    wob = math.sin(min(t, 0.9) / 0.9 * math.pi * 3) * 0.06 * max(0.0, 1 - t / 0.9)
    push = 1 + 0.04 * min(t, 10) / 10
    sx = (0.88 + 0.12 * pop) * push * (1 + wob)
    sy = (0.88 + 0.12 * pop) * push * (1 - wob)
    if abs(sx - 1) > 0.002 or abs(sy - 1) > 0.002:
        sw, sh = int(W * sx), int(H * sy)
        scaled = layer.resize((sw, sh), Image.BILINEAR)
        ox, oy = int(anchor[0] - anchor[0] * sx), int(anchor[1] - anchor[1] * sy)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer.paste(scaled, (ox, oy), scaled)
    img.alpha_composite(layer)


def stamp(d, cx, cy, word, t, start, col=GOLD, size=130):
    a = ease((t - start) / 0.3)
    if a <= 0:
        return
    sc = 1.6 - 0.6 * a
    f = font(FONT_B, int(size * sc))
    tw = d.textlength(word, font=f)
    bw, bh = tw + 80 * sc, size * 1.45 * sc
    x0, y0 = cx - bw / 2, cy - bh / 2
    c = col + (int(240 * a),)
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=int(24 * sc), outline=c, width=int(15 * sc))
    d.text((cx - tw / 2, y0 + size * 0.09 * sc), word, font=f, fill=c)


def face(d, cx, cy, t, s=1.0, glasses=False, phase=0.0):
    """Eyes that blink every few seconds, plus a smile."""
    blink = ((t + phase) % 3.2) < 0.12
    for ex in (-22, 22):
        x = cx + ex * s
        if blink:
            d.line([(x - 9 * s, cy), (x + 9 * s, cy)], fill=(40, 25, 20), width=max(2, int(5 * s)))
        else:
            d.ellipse([x - 8 * s, cy - 10 * s, x + 8 * s, cy + 10 * s], fill=(40, 25, 20))
        if glasses:
            d.ellipse([x - 20 * s, cy - 18 * s, x + 20 * s, cy + 18 * s], outline=(60, 60, 70), width=max(2, int(5 * s)))
    d.arc([cx - 24 * s, cy + 6 * s, cx + 24 * s, cy + 40 * s], 20, 160, fill=(120, 50, 40), width=max(2, int(5 * s)))


def squiggle(d, x0, y0, x1, t, start, dur=0.8, amp=26, width=22):
    """A ketchup line that draws itself from left to right."""
    p = ease((t - start) / dur)
    if p <= 0:
        return
    n = 40
    pts = []
    for i in range(int(n * p) + 1):
        u = i / n
        pts.append((x0 + (x1 - x0) * u, y0 + math.sin(u * math.pi * 4) * amp))
    if len(pts) > 1:
        d.line(pts, fill=KETCHUP, width=width, joint="curve")


# ---------- illustrations ----------

def bottle(d, cx, cy, s=1.0, level=1.0, tilt=0.0):
    """Generic glass ketchup bottle (no brand); cy is the bottom of the bottle."""
    def rot(x, y):
        c, sn = math.cos(tilt), math.sin(tilt)
        return (cx + (x * c - y * sn) * s, cy + (x * sn + y * c) * s)
    body = [(-95, 0), (95, 0), (100, -300), (55, -380), (38, -470), (-38, -470), (-55, -380), (-100, -300)]
    d.polygon([rot(x, y) for x, y in body], fill=GLASS + (110,))
    top = -20 - 440 * level
    inner = [(x * 0.86, max(y, top)) for x, y in body]
    inner = [(x, min(-10, y)) for x, y in inner]
    d.polygon([rot(x, y) for x, y in inner], fill=KETCHUP)
    d.polygon([rot(-75, -110), rot(75, -110), rot(78, -220), rot(-78, -220)], fill=(245, 240, 225))  # label
    d.polygon([rot(-55, -150), rot(55, -150), rot(57, -180), rot(-57, -180)], fill=KETCHUP_DARK)
    d.polygon([rot(-42, -470), rot(42, -470), rot(42, -520), rot(-42, -520)], fill=(245, 245, 245))  # cap
    d.line([rot(-70, -60), rot(-75, -280)], fill=(255, 255, 255, 140), width=max(2, int(10 * s)))


def capsule(d, x, y, s, ang, col=(220, 50, 45)):
    c, sn = math.cos(ang), math.sin(ang)
    def rot(px, py):
        return (x + (px * c - py * sn) * s, y + (px * sn + py * c) * s)
    semi_l = [rot(-60 + 25 * math.cos(a), 25 * math.sin(a)) for a in [math.pi / 2 + k * math.pi / 8 for k in range(9)]]
    semi_r = [rot(60 + 25 * math.cos(a), 25 * math.sin(a)) for a in [-math.pi / 2 + k * math.pi / 8 for k in range(9)]]
    d.polygon(semi_l + [rot(0, -25), rot(0, 25)], fill=col)  # bottom -> left -> top, then back along the middle
    d.polygon(semi_r + [rot(0, 25), rot(0, -25)], fill=(245, 245, 240))


def fish(d, x, y, s, flip=1, col=(120, 160, 190)):
    d.ellipse([x - 70 * s, y - 32 * s, x + 70 * s, y + 32 * s], fill=col)
    d.polygon([(x - 60 * s * flip, y), (x - 120 * s * flip, y - 40 * s), (x - 120 * s * flip, y + 40 * s)], fill=col)
    d.ellipse([x + 38 * s * flip - 7 * s, y - 12 * s, x + 38 * s * flip + 7 * s, y + 2 * s], fill=(30, 30, 30))


def art_hook(t):
    def draw(d):
        cx, cy = W / 2, 1720
        squeeze = 1 + 0.05 * math.sin(t * 3)
        bottle(d, cx - 120, cy, 1.05 * squeeze, 0.9, tilt=-0.08)
        for k in range(5):
            ang = t * 0.8 + k * 1.256
            capsule(d, cx + 230 + math.cos(ang) * 120, cy - 330 + math.sin(ang) * 220, 0.8, ang * 1.5)
        x, y = cx + 250, cy - 640  # red cross: "medicine"
        d.rounded_rectangle([x - 30, y - 90, x + 30, y + 90], radius=10, fill=(240, 240, 240))
        d.rounded_rectangle([x - 90, y - 30, x + 90, y + 30], radius=10, fill=(240, 240, 240))
        d.rounded_rectangle([x - 22, y - 80, x + 22, y + 80], radius=8, fill=HOOKRED)
        d.rounded_rectangle([x - 80, y - 22, x + 80, y + 22], radius=8, fill=HOOKRED)
        for k in range(5):
            ph = (t * 0.8 + k * 0.2) % 1
            sparkle(d, cx - 120 + math.cos(k * 1.3 + t) * 230, cy - 560 + math.sin(k * 2.1 + t) * 80, 13 * math.sin(ph * math.pi) + 2)
    return draw


def art_fish(t, name_at):
    def draw(d):
        cy = 1350
        d.rectangle([0, cy + 120, W, cy + 650], fill=(40, 90, 120))
        for k in range(5):
            y = cy + 150 + k * 80
            d.line([(j * 40, y + math.sin(j * 0.6 + t * 3 + k) * 10) for j in range(30)], fill=(80, 140, 170), width=6)
        for k in range(4):  # fish swimming
            x = (t * (90 + k * 25) + k * 300) % (W + 300) - 150
            fish(d, x, cy + 260 + k * 75 + math.sin(t * 3 + k) * 10, 0.8)
        bx = W / 2 - 150  # little boat
        rock = math.sin(t * 2) * 8
        d.polygon([(bx - 200, cy + 60 + rock), (bx + 200, cy + 60 - rock), (bx + 140, cy + 150 - rock), (bx - 140, cy + 150 + rock)], fill=(130, 80, 45))
        d.line([(bx, cy + 60), (bx, cy - 280)], fill=(90, 55, 30), width=12)
        d.polygon([(bx + 8, cy - 270), (bx + 190, cy + 30), (bx + 8, cy + 40)], fill=(235, 220, 190))
        jx, jy = W / 2 + 270, cy + 30  # jar of fish sauce
        d.rounded_rectangle([jx - 90, jy - 200, jx + 90, jy + 60], radius=40, fill=(170, 110, 60))
        d.rectangle([jx - 60, jy - 240, jx + 60, jy - 195], fill=(140, 90, 50))
        d.ellipse([jx - 60, jy - 120, jx + 60, jy - 40], fill=(120, 75, 40))
        fish(d, jx, jy - 80, 0.45, col=(230, 210, 170))
    return draw


def art_britain(t, beats):
    def draw(d):
        cy = 1400
        d.rectangle([0, cy + 230, W, cy + 650], fill=(50, 80, 120))
        for k in range(5):
            y = cy + 260 + k * 70
            d.line([(j * 40, y + math.sin(j * 0.6 + t * 3 + k) * 9) for j in range(30)], fill=(90, 130, 170), width=6)
        sx = W / 2 - 230
        rock = math.sin(t * 2) * 8
        d.polygon([(sx - 230, cy + 170 + rock), (sx + 230, cy + 170 - rock), (sx + 170, cy + 280 - rock), (sx - 170, cy + 280 + rock)], fill=(110, 65, 40))
        for mx, mh in ((sx - 80, 420), (sx + 90, 360)):
            d.line([(mx, cy + 170), (mx, cy + 170 - mh)], fill=(80, 50, 30), width=12)
            d.polygon([(mx - 90, cy + 140 - mh * 0.85), (mx + 90, cy + 140 - mh * 0.85), (mx + 100, cy + 120 - mh * 0.25), (mx - 100, cy + 120 - mh * 0.25)], fill=(240, 235, 220))
        person(d, sx + 180, cy + 110, 0.7, (40, 60, 120))
        face(d, sx + 180, cy + 110 - 0.7 * 200, t, 0.7)
        # three jars pop in on "mushrooms", "walnuts", "oysters"
        labels = [((200, 170, 140), "mush"), ((150, 100, 60), "walnut"), ((210, 210, 215), "oyster")]
        for k, ((col, kind), at) in enumerate(zip(labels, beats)):
            p = back((t - at) / 0.35)
            if p <= 0:
                continue
            x, y = W / 2 + 120 + k * 150, cy - 40
            d.rounded_rectangle([x - 60 * p, y - 90 * p, x + 60 * p, y + 90 * p], radius=int(25 * p), fill=(180, 60, 40))
            d.rectangle([x - 45 * p, y - 115 * p, x + 45 * p, y - 88 * p], fill=(110, 70, 40))
            if kind == "mush":
                d.chord([x - 38 * p, y - 40 * p, x + 38 * p, y + 20 * p], 180, 360, fill=col)
                d.rectangle([x - 12 * p, y - 10 * p, x + 12 * p, y + 35 * p], fill=(240, 230, 210))
            elif kind == "walnut":
                d.ellipse([x - 35 * p, y - 30 * p, x + 35 * p, y + 30 * p], fill=col)
                d.line([(x, y - 30 * p), (x, y + 30 * p)], fill=(110, 70, 40), width=max(2, int(5 * p)))
            else:
                d.ellipse([x - 40 * p, y - 22 * p, x + 40 * p, y + 28 * p], fill=col)
                d.ellipse([x - 14 * p, y - 6 * p, x + 14 * p, y + 14 * p], fill=(250, 250, 250))
    return draw


def tomato(d, x, y, r, squash=0.0):
    rx, ry = r * (1 + squash), r * (1 - squash)
    d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=(225, 45, 35))
    d.ellipse([x - rx * 0.5, y - ry * 0.7, x - rx * 0.1, y - ry * 0.35], fill=(245, 120, 110))
    d.polygon([(x - 25, y - ry - 5), (x + 25, y - ry - 5), (x, y - ry + 20)], fill=(60, 140, 60))


def art_tomatoes(t):
    def draw(d):
        cx, cy = W / 2, 1500
        d.chord([cx - 280, cy - 150, cx + 280, cy + 320], 0, 180, fill=(80, 85, 95))
        d.rectangle([cx - 280, cy + 70, cx + 280, cy + 90], fill=(60, 65, 75))
        d.ellipse([cx - 280, cy + 40, cx + 280, cy + 120], fill=KETCHUP)
        for k in range(4):  # tomatoes bounce in with squash and stretch
            ph = ((t - k * 0.45) % 1.8) / 1.8 if t > k * 0.45 else -1
            if ph < 0:
                continue
            x = cx - 180 + k * 120
            h = abs(math.sin(ph * math.pi))
            y = cy + 40 - h * 420
            sq = 0.25 * (1 - h) ** 6
            tomato(d, x, y - 60, 60, squash=sq)
        for k in range(3):
            pts = [(cx - 120 + k * 120 + math.sin(j * 0.5 + t * 3 + k) * 16, cy - 30 - j * 22) for j in range(7)]
            d.line(pts, fill=(255, 255, 255, 100), width=10)
    return draw


def art_doctor(t, pills_at):
    def draw(d):
        cx, cy = W / 2, 1450
        person(d, cx - 220, cy + 170, 1.45, (245, 245, 250))
        d.line([(cx - 220, cy - 20), (cx - 220, cy + 300)], fill=(200, 200, 210), width=6)  # coat line
        d.arc([cx - 280, cy - 30, cx - 160, cy + 80], 0, 180, fill=(60, 60, 70), width=8)    # stethoscope
        face(d, cx - 220, cy + 170 - 1.45 * 200, t, 1.3, glasses=True, phase=0.7)
        bottle(d, cx + 200, cy + 300, 0.7, 0.85)
        n = 0 if t < pills_at else int(min(10, (t - pills_at) / 0.12))
        for k in range(n):  # pills pour out and bounce on the floor
            q = min(1.0, (t - pills_at - k * 0.12) / 0.5)
            x = cx + 120 + k * 32 - 120
            y = cy + 160 + q * 220 - abs(math.sin(q * math.pi * 2)) * 40 * (1 - q)
            capsule(d, x, y, 0.45, k * 0.7)
    return draw


def art_crash(t, crash_at):
    def draw(d):
        cx, cy = W / 2, 1450
        n = int(min(8, t / 0.3 + 1))
        for k in range(n):  # fake bottles multiply...
            p = back((t - k * 0.3) / 0.3)
            x = cx - 360 + (k % 4) * 240
            y = cy + 80 + (k // 4) * 300
            fall = 0.0
            if t > crash_at:  # ...then topple over
                fall = min(1.0, (t - crash_at - k * 0.05) / 0.4) * (1 if k % 2 else -1) * 1.4
            bottle(d, x, y, 0.42 * p, 0.8, tilt=fall)
            if fall == 0.0:
                d.text((x - 12, y - 92 * p), "?", font=font(FONT_B, 40), fill=(150, 20, 18))
        if t > crash_at:
            a = ease((t - crash_at) / 0.25)
            d.line([(cx - 260, cy - 420), (cx + 260, cy - 180)], fill=(230, 40, 50, int(255 * a)), width=34)
            d.line([(cx + 260, cy - 420), (cx - 260, cy - 180)], fill=(230, 40, 50, int(255 * a)), width=34)
    return draw


def art_1876(t):
    def draw(d):
        cx, cy = W / 2, 1720
        level = ease(t / 3.0)
        bottle(d, cx, cy, 1.25, 0.05 + 0.9 * level)
        if level < 0.98:  # pouring stream from above
            d.line([(cx + 3, 860), (cx, cy - 40 - 550 * level)], fill=KETCHUP, width=26)
        for k in range(6):
            ph = (t * 0.7 + k * 0.17) % 1
            sparkle(d, cx + math.cos(k * 1.05 + t) * 300, cy - 400 + math.sin(k * 1.05 + t) * 300, 12 * math.sin(ph * math.pi) + 2)
    return draw


def art_today(t):
    def draw(d):
        cx, cy = W / 2, 1450
        bx = cx - 170  # burger
        d.chord([bx - 230, cy - 230, bx + 230, cy + 60], 180, 360, fill=(225, 160, 80))
        for k in range(7):
            d.ellipse([bx - 150 + k * 48, cy - 170 + (k % 2) * 25, bx - 140 + k * 48, cy - 160 + (k % 2) * 25], fill=(250, 235, 200))
        d.line([(bx - 240 + j * 30, cy - 70 + math.sin(j) * 12) for j in range(17)], fill=(90, 170, 70), width=30)
        d.rounded_rectangle([bx - 235, cy - 60, bx + 235, cy + 20], radius=36, fill=(110, 60, 35))
        d.rounded_rectangle([bx - 230, cy + 20, bx + 230, cy + 100], radius=36, fill=(225, 160, 80))
        squiggle(d, bx - 190, cy - 100, bx + 190, t, 0.5, amp=18, width=20)
        fx = cx + 270  # fries
        for k in range(7):
            x = fx - 100 + k * 33
            top = cy - 260 + (k * 37) % 70
            d.rounded_rectangle([x - 14, top, x + 14, cy - 40], radius=6, fill=(250, 205, 70))
        d.polygon([(fx - 140, cy - 80), (fx + 140, cy - 80), (fx + 110, cy + 150), (fx - 110, cy + 150)], fill=(210, 40, 40))
        squiggle(d, fx - 110, cy - 200, fx + 110, t, 1.2, amp=14, width=16)
        for k in range(4):  # little ketchup drops falling
            ph = (t * 0.6 + k * 0.25) % 1
            x = cx - 380 + k * 250
            y = 900 + ph * 950
            d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=KETCHUP)
            d.polygon([(x - 14, y - 6), (x + 14, y - 6), (x, y - 40)], fill=KETCHUP)
    return draw


# ---------- scenes ----------

def finish(img, t, seed):
    dust(img, t, seed)
    img.alpha_composite(VIGNETTE)


def s_hook(img, d, t):
    bokeh(img, t, 1, (255, 200, 190))
    camera(img, t, art_hook(t), (W / 2, 1450))
    finish(img, t, 1)
    text_block(img, "Ketchup was once", F_MID, 380, t)
    text_block(img, "sold as", F_MID, 475, t, delay=0.2)
    a = ease((t - 0.5) / 0.4)
    size = int(140 + 24 * math.sin(min(t, 1.5) * 4) * (1 - min(t / 1.5, 1)))
    f = font(FONT_B, max(60, size))
    if a > 0:
        dd = ImageDraw.Draw(img)
        tw = dd.textlength("MEDICINE", font=f)
        dd.text(((W - tw) / 2, 580), "MEDICINE", font=f, fill=HOOKRED + (int(255 * a),))


NAME_AT = 8.6


def s_fish(img, d, t):
    bokeh(img, t, 2, (200, 230, 255))
    camera(img, t, art_fish(t, NAME_AT), (W / 2, 1350))
    finish(img, t, 2)
    tag(img, "SOUTHEAST ASIA · CENTURIES AGO", t, (40, 120, 150))
    title_pop(img, "It started with FISH", F_MID, 400, t)
    text_block(img, "One story: the name comes from a Chinese word, kê-tsiap.", F_SMALL, 560, t, (215, 235, 250), NAME_AT)


BEATS = (4.6, 5.3, 6.4)


def s_britain(img, d, t):
    bokeh(img, t, 3, (210, 225, 255))
    camera(img, t, art_britain(t, BEATS), (W / 2, 1400))
    finish(img, t, 3)
    tag(img, "BRITAIN", t, (50, 80, 150))
    title_pop(img, "British copycats", F_BIG, 410, t)
    text_block(img, "Mushroom, walnut, even oyster ketchup!", F_SMALL, 590, t, (225, 230, 250), BEATS[0])


def s_tomatoes(img, d, t):
    bokeh(img, t, 4, (255, 210, 200))
    camera(img, t, art_tomatoes(t), (W / 2, 1450))
    finish(img, t, 4)
    tag(img, "EARLY 1800s · AMERICA", t, (190, 50, 40))
    title_pop(img, "Then came tomatoes", F_MID, 400, t)


PILLS_AT = 7.7


def s_doctor(img, d, t):
    bokeh(img, t, 5, (255, 220, 160))
    camera(img, t, art_doctor(t, PILLS_AT), (W / 2, 1400))
    finish(img, t, 5)
    tag(img, "THE CRAZY PART · 1830s", t, (170, 60, 110))
    title_pop(img, "Ketchup as medicine!", F_MID, 400, t)
    text_block(img, "A doctor claimed tomatoes cured stomach problems.", F_SMALL, 560, t, (255, 225, 240), 3.0)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 1000, "PILLS", t, PILLS_AT)


CRASH_AT = 3.2


def s_crash(img, d, t):
    bokeh(img, t, 6, (220, 220, 230))
    camera(img, t, art_crash(t, CRASH_AT), (W / 2, 1450))
    finish(img, t, 6)
    tag(img, "THE CRASH", t, (110, 110, 130))
    title_pop(img, "Then it crashed", F_BIG, 410, t)
    text_block(img, "Fake versions flooded the market.", F_SMALL, 590, t, (225, 225, 235), 0.6)


def s_1876(img, d, t):
    bokeh(img, t, 7, (255, 220, 160))
    camera(img, t, art_1876(t), (W / 2, 1450))
    finish(img, t, 7)
    tag(img, "1876", t, (200, 150, 30))
    title_pop(img, "Ketchup in a bottle", F_MID, 400, t)
    text_block(img, "Heinz started selling it in glass bottles.", F_SMALL, 560, t, (255, 240, 205), 3.6)


def s_today(img, d, t):
    camera(img, t, art_today(t), (W / 2, 1400))
    finish(img, t, 8)
    tag(img, "TODAY", t, (230, 60, 60))
    title_pop(img, "On burgers, fries... everything!", F_MID, 400, t)


def s_cta(img, d, t):
    text_block(img, "Learned something new?", F_MID, 330, t, delay=0.0)
    make_salt.draw_cta(img, d, W / 2, 1250, t, off=0.5)


base.TRANSITION = splat
base.SCENES[:] = [
    (3.0, ((60, 20, 18), (15, 5, 4)), s_hook),
    (11.0, ((30, 60, 80), (8, 18, 26)), s_fish),
    (8.0, ((35, 45, 75), (10, 13, 24)), s_britain),
    (4.0, ((60, 25, 20), (16, 6, 5)), s_tomatoes),
    (11.0, ((60, 25, 55), (20, 8, 25)), s_doctor),
    (6.0, ((45, 45, 55), (12, 12, 16)), s_crash),
    (8.0, ((60, 45, 20), (18, 12, 5)), s_1876),
    (5.0, ((60, 20, 18), (15, 5, 4)), s_today),
    (6.0, ((30, 30, 40), (8, 8, 12)), s_cta),
]

if __name__ == "__main__":
    base.main()
