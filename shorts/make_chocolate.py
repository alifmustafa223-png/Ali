"""YouTube Short #8: "Chocolate Was Once MONEY?!" (reuses the style from make_short.py).

Animation upgrades over the pizza video: iris (circle) transitions between scenes, titles that
pop in word by word, soft drop shadows under every illustration, a cinematic vignette, and
drifting cocoa dust.
"""
import math

from PIL import Image, ImageDraw, ImageFilter

import make_short as base
import make_salt
from make_pizza import back, bokeh
from make_short import F_BIG, F_MID, F_SMALL, H, W, ease, font, FONT_B, person, tag, text_block

CHOC, CHOC_DARK, CHOC_LIGHT = (110, 60, 30), (75, 38, 18), (150, 90, 50)
FOIL, GOLD = (205, 210, 220), (255, 190, 70)
POD, POD_DARK = (230, 130, 40), (190, 85, 30)
LEAF = (60, 140, 70)


# ---------- new animation helpers ----------

def _make_vignette():
    small = Image.new("L", (W // 8, H // 8), 0)
    d = ImageDraw.Draw(small)
    for k in range(40):
        a = int(150 * (1 - k / 40) ** 2)
        d.ellipse([-W // 8 * 0.35 + k * 2.2, -H // 8 * 0.2 + k * 3.6, W // 8 * 1.35 - k * 2.2, H // 8 * 1.2 - k * 3.6], outline=a, width=3)
    mask = small.filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
    v = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    v.putalpha(mask)
    return v


VIGNETTE = _make_vignette()


def iris(img, t, dur, idx):
    """Open each scene through a growing circle and close it through a shrinking one."""
    rmax = math.hypot(W, H) / 2 + 20
    r_in = rmax if idx == 0 else rmax * ease(t / 0.32)
    r_out = rmax * ease((dur - t) / 0.26)
    r = min(r_in, r_out)
    if r >= rmax - 1:
        return img
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], fill=255)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    out.paste(img, (0, 0), mask)
    return out


def camera(img, t, draw_fn, anchor):
    """Art on its own layer: soft drop shadow, pop-in bounce, then a slow push-in."""
    art = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(art, "RGBA"))
    a = art.getchannel("A").resize((W // 6, H // 6), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    a = a.resize((W, H), Image.BILINEAR).point(lambda v: int(v * 0.5))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 255), (0, 22), a.crop((0, 0, W, H - 22)))
    layer = Image.alpha_composite(shadow, art)
    s = (0.9 + 0.1 * back(t / 0.45)) * (1 + 0.04 * min(t, 10) / 10)
    if abs(s - 1) > 0.002:
        sw, sh = int(W * s), int(H * s)
        scaled = layer.resize((sw, sh), Image.BILINEAR)
        ox, oy = int(anchor[0] - anchor[0] * s), int(anchor[1] - anchor[1] * s)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer.paste(scaled, (ox, oy), scaled)
    img.alpha_composite(layer)


def title_pop(img, text, f, y, t, delay=0.15, color=(255, 255, 255), gap=0.09):
    """Title where each word pops in (scale bounce) one after another."""
    d = ImageDraw.Draw(img, "RGBA")
    words = text.split()
    space = d.textlength(" ", font=f)
    lines, cur, curw = [], [], 0
    for w in words:
        ww = d.textlength(w, font=f)
        if cur and curw + space + ww > W - 140:
            lines.append((cur, curw))
            cur, curw = [], 0
        curw = curw + (space if cur else 0) + ww
        cur.append((w, ww))
    lines.append((cur, curw))
    lh = f.size * 1.18
    i = 0
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for li, (ws, lw) in enumerate(lines):
        x = (W - lw) / 2
        for w, ww in ws:
            p = (t - delay - i * gap) / 0.35
            if p > 0:
                sc = max(0.05, back(p))
                fs = font(f.path, max(8, int(f.size * sc)))
                sw = ld.textlength(w, font=fs)
                cx, cy = x + ww / 2, y + li * lh + f.size * 0.55
                a = int(255 * min(1, p * 2.5))
                ld.text((cx - sw / 2 + 4, cy - fs.size * 0.55 + 5), w, font=fs, fill=(0, 0, 0, int(a * 0.55)))
                ld.text((cx - sw / 2, cy - fs.size * 0.55), w, font=fs, fill=color + (a,))
            x += ww + space
            i += 1
    img.alpha_composite(layer)


def dust(img, t, seed):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for k in range(26):
        ph = (t * 0.06 + k * 0.0385 + seed * 0.13) % 1
        x = (k * 173 + seed * 61) % W + math.sin(t * 0.8 + k) * 25
        y = 900 + ((k * 97) % 1000) - ph * 120
        r = 3 + k % 4
        ld.ellipse([x - r, y - r, x + r, y + r], fill=(230, 180, 130, int(70 * math.sin(ph * math.pi))))
    img.alpha_composite(layer)


def stamp(d, cx, cy, word, t, start, col=GOLD):
    a = ease((t - start) / 0.3)
    if a <= 0:
        return
    sc = 1.6 - 0.6 * a
    f = font(FONT_B, int(130 * sc))
    tw = d.textlength(word, font=f)
    bw, bh = tw + 80 * sc, 190 * sc
    x0, y0 = cx - bw / 2, cy - bh / 2
    c = col + (int(240 * a),)
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=int(24 * sc), outline=c, width=int(15 * sc))
    d.text((cx - tw / 2, y0 + 12 * sc), word, font=f, fill=c)


# ---------- illustrations ----------

def choc_bar(d, cx, cy, w, h, t=0.0, foil=True, rows=4, cols=3, snap=0.0):
    x0, y0 = cx - w / 2, cy - h / 2
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=18, fill=CHOC_DARK)
    cw, ch = w / cols, h / rows
    for r in range(rows):
        for c in range(cols):
            off = 0
            if snap > 0 and r == 0:  # top row snaps off and jumps
                off = -snap
            bx, by = x0 + c * cw + 8, y0 + r * ch + 8 + off
            d.rounded_rectangle([bx, by, bx + cw - 16, by + ch - 16], radius=10, fill=CHOC)
            d.rounded_rectangle([bx + 8, by + 8, bx + cw - 30, by + 22], radius=6, fill=CHOC_LIGHT)
    if foil:
        d.polygon([(x0 - 10, y0 + h * 0.55), (x0 + w + 10, y0 + h * 0.45), (x0 + w + 10, y0 + h + 10), (x0 - 10, y0 + h + 10)], fill=FOIL)
        for k in range(5):
            xx = x0 + 20 + k * (w - 40) / 4
            d.line([(xx, y0 + h * 0.55 - (xx - x0) / w * h * 0.1 + 10), (xx + 10, y0 + h)], fill=(235, 238, 245), width=5)


def sparkle(d, x, y, r, col=(255, 230, 120)):
    d.polygon([(x, y - r * 2), (x + r * 0.5, y), (x, y + r * 2), (x - r * 0.5, y)], fill=col)
    d.polygon([(x - r * 2, y), (x, y + r * 0.5), (x + r * 2, y), (x, y - r * 0.5)], fill=col)


def coin(d, x, y, r):
    d.ellipse([x - r, y - r, x + r, y + r], fill=GOLD, outline=(205, 150, 40), width=max(2, int(r * 0.12)))
    d.ellipse([x - r * 0.6, y - r * 0.6, x + r * 0.6, y + r * 0.6], outline=(225, 170, 50), width=max(2, int(r * 0.08)))


def pod(d, x, y, s, ang):
    pts = []
    for k in range(24):
        a = k / 24 * 2 * math.pi
        px, py = math.cos(a) * 40 * s, math.sin(a) * 85 * s * (1 - 0.15 * math.cos(a))
        pts.append((px, py))
    c, sn = math.cos(ang), math.sin(ang)
    d.polygon([(x + px * c - py * sn, y + px * sn + py * c) for px, py in pts], fill=POD)
    for k in (-1, 0, 1):
        p1 = (k * 18 * s, -70 * s)
        p2 = (k * 22 * s, 70 * s)
        d.line([(x + p1[0] * c - p1[1] * sn, y + p1[0] * sn + p1[1] * c), (x + p2[0] * c - p2[1] * sn, y + p2[0] * sn + p2[1] * c)], fill=POD_DARK, width=max(2, int(5 * s)))


def bean(d, x, y, s=1.0):
    d.ellipse([x - 26 * s, y - 16 * s, x + 26 * s, y + 16 * s], fill=CHOC_LIGHT)
    d.line([(x - 18 * s, y), (x + 18 * s, y)], fill=CHOC_DARK, width=max(2, int(4 * s)))


def art_hook(t):
    def draw(d):
        cx, cy = W / 2, 1400
        tilt = math.sin(t * 1.5) * 0.04
        choc_bar(d, cx, cy, 420, 540, t)
        for k in range(5):
            ang = t * 0.9 + k * 1.256
            coin(d, cx + math.cos(ang) * 330, cy + math.sin(ang) * 140 - 40, 38 + 8 * math.sin(ang))
        for k in range(6):
            ph = (t * 0.8 + k * 0.17) % 1
            sparkle(d, cx + math.cos(k * 1.05 + t) * 300, cy - 330 + math.sin(k * 2.1 + t) * 60, 14 * math.sin(ph * math.pi) + 2)
    return draw


def art_tree(t):
    def draw(d):
        cx, cy = W / 2, 1380
        d.rectangle([0, cy + 330, W, cy + 560], fill=(70, 110, 50))
        d.polygon([(cx - 60, cy + 340), (cx + 60, cy + 340), (cx + 35, cy - 200), (cx - 35, cy - 200)], fill=(110, 75, 45))
        for k in range(7):
            ang = k / 7 * 2 * math.pi + math.sin(t + k) * 0.05
            lx, ly = cx + math.cos(ang) * 270, cy - 300 + math.sin(ang) * 150
            d.ellipse([lx - 170, ly - 90, lx + 170, ly + 90], fill=LEAF if k % 2 else (50, 125, 60))
        d.ellipse([cx - 220, cy - 420, cx + 220, cy - 180], fill=(55, 135, 65))
        for k, (dx, dy) in enumerate([(-55, -60), (55, 10), (-50, 110), (50, 190)]):
            sway = math.sin(t * 2 + k) * 0.12
            pod(d, cx + dx * 1.6, cy + dy, 0.95, sway + (0.25 if dx > 0 else -0.25))
    return draw


def art_drink(t):
    def draw(d):
        cx, cy = W / 2, 1500
        jx, jy, ang = cx - 190, cy - 560, 0.6 + 0.05 * math.sin(t * 2)
        c, sn = math.cos(ang), math.sin(ang)
        def rot(x, y):
            return (jx + x * c - y * sn, jy + x * sn + y * c)
        d.polygon([rot(-80, -120), rot(80, -120), rot(105, 110), rot(-105, 110)], fill=(190, 110, 70))
        d.polygon([rot(80, -120), rot(150, -150), rot(95, -70)], fill=(190, 110, 70))  # spout
        d.polygon([rot(-95, -10), rot(98, -10), rot(101, 20), rot(-99, 20)], fill=(150, 80, 50))  # band
        hx, hy = rot(-110, -5)
        d.arc([hx - 50, hy - 60, hx + 50, hy + 60], 100, 260, fill=(170, 95, 60), width=20)  # handle, attached to the jug's back
        sx, sy = rot(150, -150)
        wob = math.sin(t * 8) * 5
        d.line([(sx, sy), (sx + 40 + wob, sy + 110), (cx + 20, cy - 200)], fill=CHOC, width=20, joint="curve")
        d.chord([cx - 170, cy - 300, cx + 170, cy + 60], 0, 180, fill=(170, 90, 55))
        d.rectangle([cx - 170, cy - 130, cx + 170, cy - 110], fill=(170, 90, 55))
        d.ellipse([cx - 170, cy - 160, cx + 170, cy - 90], fill=CHOC)
        for k in range(11):  # froth bubbles bubbling up
            ph = (t * 1.2 + k * 0.09) % 1
            bx = cx - 140 + (k * 29) % 280
            r = 10 + (k % 3) * 6
            d.ellipse([bx - r, cy - 150 - ph * 60 - r, bx + r, cy - 150 - ph * 60 + r], fill=(235, 205, 170, int(255 * (1 - ph))))
        for k, (px, rot) in enumerate([(cx + 290, 0.5), (cx + 380, -0.3)]):
            bob = math.sin(t * 2 + k) * 10
            d.polygon([(px - 20, cy - 60 + bob), (px + 20, cy - 60 + bob), (px + 10 + 60 * rot, cy + 140 + bob), (px - 5 + 60 * rot, cy + 150 + bob)], fill=(215, 40, 35))
            d.rectangle([px - 12, cy - 95 + bob, px + 12, cy - 60 + bob], fill=(60, 140, 60))
    return draw


def art_montezuma(t):
    def draw(d):
        cx, cy = W / 2, 1450
        for k in range(9):  # feather headdress fan
            ang = math.pi + (k + 0.5) / 9 * math.pi
            fx, fy = cx - 150 + math.cos(ang) * 190, cy - 330 + math.sin(ang) * 190
            col = [(40, 160, 120), (240, 190, 50), (210, 60, 60)][k % 3]
            d.line([(cx - 150, cy - 300), (fx, fy)], fill=col, width=46)
        person(d, cx - 150, cy + 150, 1.5, (200, 150, 50), skin=(190, 135, 95))
        d.rectangle([cx - 245, cy - 250, cx - 55, cy - 225], fill=(240, 190, 50))
        n = int(min(5, t / 0.7 + 1))
        for k in range(n):  # cups stacking up: "every single day"
            pop = back((t - k * 0.7) / 0.35)
            x, y = cx + 220, cy + 300 - k * 120
            s = pop
            d.chord([x - 90 * s, y - 100 * s, x + 90 * s, y + 60 * s], 0, 180, fill=(220, 180, 60))
            d.ellipse([x - 90 * s, y - 40 * s, x + 90 * s, y - 0 * s], fill=CHOC)
    return draw


def art_money(t, money_at, food_at):
    def draw(d):
        cx, cy = W / 2, 1450
        d.polygon([(cx - 420, cy + 260), (cx + 420, cy + 260), (cx + 380, cy + 330), (cx - 380, cy + 330)], fill=(120, 75, 40))  # market table
        for col in range(5):  # stacks of beans grow like coin stacks
            h = int(min(7, max(0, (t - col * 0.25) / 0.18)))
            for r in range(h):
                bean(d, cx - 300 + col * 150, cy + 225 - r * 30, 1.6)
        fa = back((t - food_at) / 0.4)
        if fa > 0:  # what the beans buy: corn and a tomato pop up
            x, y = cx + 300, cy - 150
            d.ellipse([x - 45 * fa, y - 130 * fa, x + 45 * fa, y + 130 * fa], fill=(250, 210, 70))
            for k in range(5):
                d.line([(x - 35 * fa, y - 90 * fa + k * 45 * fa), (x + 35 * fa, y - 90 * fa + k * 45 * fa)], fill=(220, 175, 50), width=6)
            d.polygon([(x - 50 * fa, y + 80 * fa), (x, y - 20 * fa), (x - 20 * fa, y + 140 * fa)], fill=(90, 170, 70))
            x2 = cx - 300
            d.ellipse([x2 - 80 * fa, y - 70 * fa, x2 + 80 * fa, y + 70 * fa], fill=(225, 55, 45))
            d.ellipse([x2 - 20 * fa, y - 85 * fa, x2 + 20 * fa, y - 60 * fa], fill=(70, 150, 60))
    return draw


def art_europe(t):
    def draw(d):
        cx, cy = W / 2, 1480
        d.chord([cx - 190, cy - 230, cx + 190, cy + 130], 0, 180, fill=(245, 240, 235))
        d.rectangle([cx - 190, cy - 60, cx + 190, cy - 45], fill=(245, 240, 235))
        d.ellipse([cx - 190, cy - 90, cx + 190, cy - 20], fill=(245, 240, 235))
        d.ellipse([cx - 165, cy - 80, cx + 165, cy - 30], fill=CHOC)
        d.arc([cx + 160, cy - 60, cx + 280, cy + 60], 270, 90, fill=(245, 240, 235), width=24)
        d.line([(cx - 150, cy - 10), (cx + 150, cy - 10)], fill=(220, 170, 60), width=8)  # gold rim
        d.ellipse([cx - 280, cy + 110, cx + 280, cy + 160], fill=(225, 220, 215))
        for k in range(6):  # sugar cubes dropping in
            ph = (t * 0.7 + k * 0.166) % 1
            x = cx - 120 + (k * 53) % 240
            y = cy - 500 + ease(ph) * 420
            if y < cy - 70:
                d.rounded_rectangle([x - 22, y - 22, x + 22, y + 22], radius=6, fill=(255, 255, 255))
        bob = math.sin(t * 2) * 10
        y = cy - 640 + bob
        d.polygon([(cx - 150, y + 100), (cx - 150, y - 15), (cx - 75, y + 35), (cx, y - 60), (cx + 75, y + 35), (cx + 150, y - 15), (cx + 150, y + 100)], fill=(240, 190, 50))
        for x in (cx - 90, cx, cx + 90):
            d.ellipse([x - 16, y + 55, x + 16, y + 87], fill=(220, 50, 70))
    return draw


def art_bar1847(t, snap_at):
    def draw(d):
        cx, cy = W / 2, 1450
        p = max(0.0, t - snap_at)
        jump = 160 * math.exp(-p * 2.2) * abs(math.sin(p * 6)) if p > 0 else 0
        choc_bar(d, cx, cy, 460, 600, t, foil=True, snap=jump + (40 if p > 0 else 0))
        if p > 0:  # crumbs flying out at the snap
            for k in range(8):
                q = min(1.0, p / 0.8)
                ang = -math.pi / 2 + (k - 3.5) * 0.35
                x = cx + math.cos(ang) * 260 * q
                y = cy - 300 + math.sin(ang) * 200 * q + 300 * q * q
                if q < 1:
                    d.rectangle([x - 8, y - 8, x + 8, y + 8], fill=CHOC_LIGHT)
    return draw


def art_today(t):
    def draw(d):
        for k in range(12):
            ph = (t * 0.32 + k * 0.083) % 1
            x = (k * 389 + 90) % (W - 200) + 100
            y = 900 + ph * 1150
            ang = t * (0.6 + (k % 3) * 0.3) + k
            w, h = 120, 160
            pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
            c, s = math.cos(ang), math.sin(ang)
            d.polygon([(x + px * c - py * s, y + px * s + py * c) for px, py in pts], fill=CHOC)
            ip = [(-w / 2 + 12, -h / 2 + 12), (w / 2 - 12, -h / 2 + 12), (w / 2 - 12, 0), (-w / 2 + 12, 0)]
            d.polygon([(x + px * c - py * s, y + px * s + py * c) for px, py in ip], fill=CHOC_LIGHT)
            fp = [(-w / 2, 10), (w / 2, 10), (w / 2, h / 2), (-w / 2, h / 2)]
            d.polygon([(x + px * c - py * s, y + px * s + py * c) for px, py in fp], fill=FOIL)
    return draw


# ---------- scenes ----------

def finish(img, t, seed):
    dust(img, t, seed)
    img.alpha_composite(VIGNETTE)


def s_hook(img, d, t):
    bokeh(img, t, 1)
    camera(img, t, art_hook(t), (W / 2, 1400))
    finish(img, t, 1)
    text_block(img, "Chocolate was once used as", F_MID, 380, t)
    a = ease((t - 0.5) / 0.4)
    size = int(150 + 26 * math.sin(min(t, 1.5) * 4) * (1 - min(t / 1.5, 1)))
    f = font(FONT_B, max(60, size))
    if a > 0:
        dd = ImageDraw.Draw(img)
        tw = dd.textlength("MONEY", font=f)
        dd.text(((W - tw) / 2, 560), "MONEY", font=f, fill=GOLD + (int(255 * a),))


def s_tree(img, d, t):
    bokeh(img, t, 2, (200, 255, 200))
    camera(img, t, art_tree(t), (W / 2, 1350))
    finish(img, t, 2)
    tag(img, "OVER 3,000 YEARS AGO", t, (60, 130, 70))
    title_pop(img, "The cacao tree", F_BIG, 410, t)
    text_block(img, "Discovered in what's now Mexico and Central America.", F_SMALL, 590, t, (220, 245, 220), 4.6)


def s_drink(img, d, t):
    bokeh(img, t, 3)
    camera(img, t, art_drink(t), (W / 2, 1400))
    finish(img, t, 3)
    tag(img, "A BITTER DRINK", t, (180, 70, 40))
    title_pop(img, "Bitter, foamy and spicy", F_MID, 400, t)
    text_block(img, "With chili. No sugar at all!", F_SMALL, 560, t, (255, 225, 205), 5.2)


def s_montezuma(img, d, t):
    bokeh(img, t, 4)
    camera(img, t, art_montezuma(t), (W / 2, 1400))
    finish(img, t, 4)
    tag(img, "LEGEND", t, (40, 140, 120))
    title_pop(img, "Montezuma's daily drink", F_MID, 400, t)
    text_block(img, "Legend says he drank cups of it every day.", F_SMALL, 560, t, (220, 245, 235), 0.6)


MONEY_AT, FOOD_AT = 5.5, 7.2


def s_money(img, d, t):
    bokeh(img, t, 5, (255, 220, 140))
    camera(img, t, art_money(t, MONEY_AT, FOOD_AT), (W / 2, 1400))
    finish(img, t, 5)
    tag(img, "THE CRAZY PART", t, (170, 60, 110))
    title_pop(img, "Beans were MONEY!", F_MID, 400, t)
    text_block(img, "You could buy food with them.", F_SMALL, 560, t, (255, 225, 240), FOOD_AT)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 1040, "MONEY", t, MONEY_AT)


def s_europe(img, d, t):
    bokeh(img, t, 6)
    camera(img, t, art_europe(t), (W / 2, 1400))
    finish(img, t, 6)
    tag(img, "THE 1500s", t, (200, 150, 30))
    title_pop(img, "Sugar made it sweet", F_MID, 400, t)
    text_block(img, "A luxury drink for the rich in Europe.", F_SMALL, 560, t, (255, 240, 205), 5.7)


SNAP_AT = 3.9


def s_bar(img, d, t):
    bokeh(img, t, 7)
    camera(img, t, art_bar1847(t, SNAP_AT), (W / 2, 1400))
    finish(img, t, 7)
    tag(img, "1847", t, (150, 80, 40))
    title_pop(img, "The first chocolate bar", F_MID, 400, t)
    text_block(img, "Made by a company in England.", F_SMALL, 560, t, (255, 230, 210), 1.5)


def s_today(img, d, t):
    camera(img, t, art_today(t), (W / 2, 1350))
    finish(img, t, 8)
    tag(img, "TODAY", t, (230, 60, 60))
    title_pop(img, "Millions of tons a year!", F_MID, 400, t)


def s_cta(img, d, t):
    text_block(img, "Learned something new?", F_MID, 330, t, delay=0.0)
    make_salt.draw_cta(img, d, W / 2, 1250, t, off=0.4)


base.TRANSITION = iris
base.SCENES[:] = [
    (3.0, ((55, 30, 18), (14, 7, 4)), s_hook),
    (6.0, ((40, 75, 60), (12, 24, 16)), s_tree),
    (6.0, ((65, 30, 20), (18, 8, 5)), s_drink),
    (5.0, ((30, 60, 60), (8, 18, 18)), s_montezuma),
    (9.0, ((60, 25, 55), (20, 8, 25)), s_money),
    (7.0, ((60, 45, 20), (18, 12, 5)), s_europe),
    (5.0, ((55, 30, 18), (14, 7, 4)), s_bar),
    (4.0, ((55, 30, 18), (14, 7, 4)), s_today),
    (5.0, ((30, 30, 40), (8, 8, 12)), s_cta),
]

if __name__ == "__main__":
    base.main()
