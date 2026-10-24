"""YouTube Short #7: "Pizza Was Once Food for POOR People" (reuses the style from make_short.py).

Animation upgrades over earlier videos: illustrations pop in with a small bounce and then
slowly push in (a gentle camera zoom), and soft light particles drift in the background.
"""
import math

from PIL import Image, ImageDraw

import make_short as base
import make_salt
from make_short import F_BIG, F_MID, F_SMALL, H, W, ease, font, FONT_B, person, tag, text_block

CRUST, CRUST_DARK = (225, 165, 85), (185, 120, 55)
SAUCE, CHEESE, BASIL, PEPPERONI = (205, 45, 35), (250, 225, 150), (60, 150, 60), (175, 40, 35)
GOLD, RED = (255, 190, 70), (230, 40, 50)


def back(x):
    """Ease-out with a little overshoot (the 'pop')."""
    x = max(0.0, min(1.0, x))
    c1 = 1.70158
    return 1 + (c1 + 1) * (x - 1) ** 3 + c1 * (x - 1) ** 2


def bokeh(img, t, seed, col=(255, 230, 180)):
    """Soft glowing dots drifting up behind the illustration (drawn on a layer so alpha is kept)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for k in range(10):
        ph = (t * 0.04 + k * 0.1 + seed * 0.37) % 1
        x = (k * 211 + seed * 97) % W + math.sin(t * 0.5 + k) * 30
        y = H - 120 - ph * (H - 1080)
        r = 14 + (k * 7) % 18
        a = int(60 * math.sin(ph * math.pi))
        ld.ellipse([x - r, y - r, x + r, y + r], fill=col + (a,))
    img.alpha_composite(layer)


def camera(img, t, draw_fn, anchor):
    """Draw the scene's art on its own layer, then pop it in and slowly push in toward `anchor`."""
    art = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(art, "RGBA"))
    s = (0.9 + 0.1 * back(t / 0.45)) * (1 + 0.04 * min(t, 10) / 10)
    if abs(s - 1) > 0.002:
        sw, sh = int(W * s), int(H * s)
        art = art.resize((sw, sh), Image.BILINEAR)
        ox, oy = int(anchor[0] - anchor[0] * s), int(anchor[1] - anchor[1] * s)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer.paste(art, (ox, oy), art)
        art = layer
    img.alpha_composite(art)


def pizza(d, cx, cy, r, rot=0.0, margherita=False, slice_out=0.0):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CRUST)
    d.ellipse([cx - r * 0.86, cy - r * 0.86, cx + r * 0.86, cy + r * 0.86], fill=SAUCE)
    for k in range(9):
        a = rot + k * 0.7
        rr = r * (0.25 + 0.5 * ((k * 37) % 10) / 10)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        b = r * 0.17
        d.ellipse([x - b, y - b * 0.8, x + b, y + b * 0.8], fill=CHEESE)
    for k in range(6):
        a = rot + k * 1.05 + 0.3
        rr = r * 0.55
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        if margherita:
            d.ellipse([x - r * 0.09, y - r * 0.05, x + r * 0.09, y + r * 0.05], fill=BASIL)
        else:
            p = r * 0.1
            d.ellipse([x - p, y - p, x + p, y + p], fill=PEPPERONI)
    if slice_out > 0:  # cut a slice out of the pie (drawn separately by the caller)
        a0 = -math.pi / 2 - 0.4
        pts = [(cx, cy)] + [(cx + math.cos(a0 + 0.8 * i / 10) * (r + 2), cy + math.sin(a0 + 0.8 * i / 10) * (r + 2)) for i in range(11)]
        d.polygon(pts, fill=(0, 0, 0, 0))


def slice_shape(d, tipx, tipy, length, lift):
    """A slice pointing down, lifted up by `lift`, with stretchy cheese strings."""
    top = tipy - length - lift
    left, right = tipx - length * 0.42, tipx + length * 0.42
    ty = tipy - lift
    for k in range(4):  # cheese strings from the slice down to the pie
        x = left + 40 + k * (right - left - 80) / 3
        sway = math.sin(lift * 0.05 + k) * 8
        d.line([(x, ty - 40), (x + sway, ty + lift * 0.9)], fill=CHEESE, width=10)
    d.polygon([(left, top), (right, top), (tipx, ty)], fill=SAUCE)
    d.rounded_rectangle([left - 10, top - 30, right + 10, top + 15], radius=20, fill=CRUST)
    for k in range(4):
        x = left + 40 + (k * 61) % int(right - left - 80)
        y = top + 50 + (k * 47) % int(length * 0.5)
        d.ellipse([x - 28, y - 20, x + 28, y + 20], fill=CHEESE)
    d.ellipse([tipx - 35, top + 80, tipx + 5, top + 120], fill=PEPPERONI)


def steam(d, cx, top, t, n=3, length=9, spread=70):
    for k in range(n):
        pts = [(cx - spread + k * spread + math.sin(j * 0.5 + t * 3 + k) * 18, top - j * 22) for j in range(length)]
        d.line(pts, fill=(255, 255, 255, 110), width=11)


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

def art_hook(t):
    def draw(d):
        cx, cy = W / 2, 1430
        pizza(d, cx, cy, 330, rot=t * 0.25)
        gap = [(cx, cy)] + [(cx + math.cos(-math.pi / 2 - 0.42 + 0.84 * i / 12) * 334, cy + math.sin(-math.pi / 2 - 0.42 + 0.84 * i / 12) * 334) for i in range(13)]
        d.polygon(gap, fill=(70, 35, 18))  # where the slice was lifted out
        lift = 60 + 50 * (math.sin(t * 2) + 1) / 2
        slice_shape(d, cx, cy + 20, 300, lift)
        steam(d, cx, cy - 420 - lift, t)
    return draw


def art_naples(t):
    def draw(d):
        cy = 1350
        # Vesuvius with a little smoke
        d.polygon([(260, cy - 80), (820, cy - 80), (600, cy - 420), (480, cy - 420)], fill=(110, 100, 130))
        for k in range(4):
            ph = (t * 0.3 + k * 0.25) % 1
            r = 30 + ph * 50
            d.ellipse([540 - r + ph * 60, cy - 450 - ph * 260 - r, 540 + r + ph * 60, cy - 450 - ph * 260 + r], fill=(200, 200, 210, int(150 * (1 - ph))))
        cols = [(230, 160, 90), (240, 200, 120), (210, 110, 80), (235, 185, 150), (200, 140, 100)]
        for k in range(5):
            x0 = k * 216
            h = 330 + (k * 73) % 140
            d.rectangle([x0, cy + 180 - h, x0 + 216, cy + 180], fill=cols[k])
            for wy in range(2):
                for wx in range(2):
                    d.rectangle([x0 + 40 + wx * 90, cy + 220 - h + wy * 110, x0 + 90 + wx * 90, cy + 290 - h + wy * 110], fill=(70, 50, 40))
        d.rectangle([0, cy + 180, W, cy + 600], fill=(150, 130, 110))
        for k in range(3):  # workers walking across
            x = (t * 120 + k * 380) % (W + 300) - 150
            step = abs(math.sin(t * 6 + k)) * 10
            person(d, x, cy + 280 - step, 0.9, [(90, 110, 140), (140, 90, 70), (100, 120, 80)][k])
    return draw


def art_street(t):
    def draw(d):
        cx, cy = W / 2, 1400
        d.rectangle([cx - 420, cy + 120, cx + 420, cy + 170], fill=(120, 75, 40))
        d.rectangle([cx - 400, cy + 170, cx - 370, cy + 420], fill=(100, 60, 30))
        d.rectangle([cx + 370, cy + 170, cx + 400, cy + 420], fill=(100, 60, 30))
        for k in range(7):  # striped awning
            d.rectangle([cx - 440 + k * 126, cy - 420, cx - 314 + k * 126, cy - 330], fill=(220, 60, 60) if k % 2 == 0 else (245, 240, 230))
        # flatbread being topped in three beats: sauce, cheese, garlic
        r = 240
        d.ellipse([cx - r, cy - 60 - r * 0.45, cx + r, cy - 60 + r * 0.45], fill=CRUST)
        sauce = ease((t - 1.6) / 0.5)
        if sauce > 0:
            rs = r * 0.85 * sauce
            d.ellipse([cx - rs, cy - 60 - rs * 0.45, cx + rs, cy - 60 + rs * 0.45], fill=SAUCE)
        for k in range(8):
            drop = ease((t - 2.1 - k * 0.06) / 0.35)
            if drop <= 0:
                continue
            x = cx - 160 + (k * 47) % 320
            y = cy - 80 + ((k * 31) % 60) - (1 - drop) * 300
            d.ellipse([x - 32, y - 16, x + 32, y + 16], fill=CHEESE)
        for k in range(5):
            drop = ease((t - 2.6 - k * 0.06) / 0.3)
            if drop <= 0:
                continue
            x = cx - 120 + (k * 59) % 240
            y = cy - 70 + ((k * 23) % 50) - (1 - drop) * 300
            d.ellipse([x - 12, y - 9, x + 12, y + 9], fill=(250, 250, 240))
        steam(d, cx, cy - 170, t, length=5)
    return draw


def art_rich(t):
    def draw(d):
        cx, cy = W / 2, 1380
        person(d, cx - 160, cy + 160, 1.5, (40, 40, 60))
        d.rectangle([cx - 260, cy - 250, cx - 60, cy - 228], fill=(25, 25, 30))   # hat brim
        d.rectangle([cx - 220, cy - 400, cx - 100, cy - 245], fill=(25, 25, 30))  # top hat
        d.ellipse([cx - 135, cy - 165, cx - 85, cy - 115], outline=(230, 200, 90), width=6)  # monocle
        tilt = math.sin(t * 2) * 4
        d.line([(cx - 215, cy - 180 + tilt), (cx - 165, cy - 170 + tilt)], fill=(60, 30, 20), width=8)  # raised brow
        d.ellipse([cx - 200, cy - 150, cx - 180, cy - 130], fill=(40, 25, 20))  # eye
        d.arc([cx - 205, cy - 100, cx - 135, cy - 60], 200, 340, fill=(60, 30, 20), width=8)  # frown
        # a slice held at arm's length, wobbling
        wob = math.sin(t * 5) * 0.08
        sx, sy = cx + 230, cy - 20
        d.line([(cx - 60, cy - 20), (sx - 40, sy + 30)], fill=(40, 40, 60), width=40)
        pts = [(-80, -120), (80, -120), (0, 120)]
        c, s = math.cos(wob), math.sin(wob)
        d.polygon([(sx + x * c - y * s, sy + x * s + y * c) for x, y in pts], fill=SAUCE)
        d.line([(sx - 90 * c + 125 * s, sy - 90 * s - 125 * c), (sx + 90 * c + 125 * s, sy + 90 * s - 125 * c)], fill=CRUST, width=34)
        for k in range(3):  # stink lines
            ph = (t * 0.8 + k * 0.33) % 1
            x = sx - 60 + k * 60
            d.line([(x + math.sin(j + t * 4) * 10, sy - 160 - j * 20 - ph * 60) for j in range(5)], fill=(150, 200, 120, int(200 * (1 - ph))), width=6)
    return draw


def art_queen(t, stamp_at):
    def draw(d):
        cx, cy = W / 2, 1600
        pizza(d, cx, cy, 250, rot=0.4, margherita=True)
        bob = math.sin(t * 2) * 10
        y = 930 + bob
        d.polygon([(cx - 170, y + 110), (cx - 170, y - 20), (cx - 85, y + 40), (cx, y - 70), (cx + 85, y + 40), (cx + 170, y - 20), (cx + 170, y + 110)], fill=(240, 190, 50))
        for x in (cx - 100, cx, cx + 100):
            d.ellipse([x - 18, y + 60, x + 18, y + 96], fill=(220, 50, 70))
        for k in range(6):
            ph = (t * 0.7 + k * 0.17) % 1
            x = cx + math.cos(k * 1.05 + t) * 380
            yy = 1330 + math.sin(k * 1.05 + t) * 300
            r = 14 * (1 - abs(ph - 0.5) * 2)
            d.polygon([(x, yy - r * 2), (x + r * 0.6, yy), (x, yy + r * 2), (x - r * 0.6, yy)], fill=(255, 230, 120))
    return draw


def art_newyork(t):
    def draw(d):
        cy = 1350
        for k in range(9):  # skyline
            x0 = 40 + k * 115
            h = 260 + (k * 97) % 300
            d.rectangle([x0, cy + 120 - h, x0 + 95, cy + 120], fill=(70, 80, 110))
            for wy in range(int(h / 60)):
                lit = (k + wy) % 3 != 0
                d.rectangle([x0 + 20, cy + 140 - h + wy * 60, x0 + 40, cy + 165 - h + wy * 60], fill=(255, 220, 120) if lit else (50, 60, 90))
                d.rectangle([x0 + 55, cy + 140 - h + wy * 60, x0 + 75, cy + 165 - h + wy * 60], fill=(255, 220, 120) if not lit else (50, 60, 90))
        d.rectangle([0, cy + 120, W, cy + 600], fill=(40, 80, 140))
        for k in range(5):
            y = cy + 160 + k * 70
            d.line([(j * 40, y + math.sin(j * 0.6 + t * 3 + k) * 10) for j in range(30)], fill=(80, 130, 190), width=6)
        sx = -250 + ease(t / 5.0) * (W / 2 + 250)
        rock = math.sin(t * 2) * 8
        d.polygon([(sx - 230, cy + 200 + rock), (sx + 230, cy + 200 - rock), (sx + 170, cy + 300 - rock), (sx - 170, cy + 300 + rock)], fill=(150, 50, 40))
        d.rectangle([sx - 110, cy + 110, sx + 110, cy + 200], fill=(240, 235, 225))
        d.rectangle([sx - 30, cy + 20, sx + 10, cy + 110], fill=(30, 30, 35))
        pizza(d, sx + 0, cy - 60, 70, rot=t)  # the pizza riding along on top
    return draw


def art_today(t):
    def draw(d):
        for k in range(14):
            ph = (t * 0.35 + k * 0.071) % 1
            x = (k * 389 + 90) % (W - 120) + 60
            y = 860 + ph * 1170
            pizza(d, x, y, 70 + (k % 3) * 15, rot=t * (1 + k % 3) + k)
    return draw


# ---------- scenes ----------

def s_hook(img, d, t):
    bokeh(img, t, 1)
    camera(img, t, art_hook(t), (W / 2, 1430))
    text_block(img, "Pizza was once food for", F_MID, 380, t)
    a = ease((t - 0.5) / 0.4)
    size = int(128 + 24 * math.sin(min(t, 1.5) * 4) * (1 - min(t / 1.5, 1)))
    f = font(FONT_B, max(60, size))
    if a > 0:
        dd = ImageDraw.Draw(img)
        tw = dd.textlength("POOR PEOPLE", font=f)
        dd.text(((W - tw) / 2, 520), "POOR PEOPLE", font=f, fill=GOLD + (int(255 * a),))


def s_naples(img, d, t):
    bokeh(img, t, 2)
    camera(img, t, art_naples(t), (W / 2, 1300))
    tag(img, "NAPLES · 1700s", t, (200, 110, 40))
    text_block(img, "Fast food for workers", F_MID, 400, t, delay=0.2)
    text_block(img, "Cheap, fast and easy to eat.", F_SMALL, 560, t, (255, 230, 200), 7.4)


def s_street(img, d, t):
    bokeh(img, t, 3)
    camera(img, t, art_street(t), (W / 2, 1350))
    tag(img, "STREET FOOD", t, (200, 60, 60))
    text_block(img, "Tomato. Cheese. Garlic.", F_MID, 400, t, delay=0.2)
    text_block(img, "Sold right on the street.", F_SMALL, 560, t, (255, 225, 210), 3.9)


def s_rich(img, d, t):
    bokeh(img, t, 4)
    camera(img, t, art_rich(t), (W / 2, 1350))
    tag(img, "THE RICH", t, (90, 90, 120))
    text_block(img, "\"Food for the poor.\"", F_MID, 400, t, delay=0.2)
    text_block(img, "Rich people looked down on it.", F_SMALL, 560, t, (225, 225, 240), 0.8)


QUEEN_STAMP = 3.9


def s_queen(img, d, t):
    bokeh(img, t, 5, (255, 220, 140))
    camera(img, t, art_queen(t, QUEEN_STAMP), (W / 2, 1400))
    tag(img, "THE CRAZY PART · 1889", t, (170, 60, 110))
    text_block(img, "A pizza fit for a queen", F_MID, 400, t, delay=0.2)
    text_block(img, "The story goes: the Margherita was named after Queen Margherita.", F_SMALL, 560, t, (255, 225, 240), 1.2)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 1210, "ROYAL", t, QUEEN_STAMP)


def s_newyork(img, d, t):
    bokeh(img, t, 6, (200, 220, 255))
    camera(img, t, art_newyork(t), (W / 2, 1350))
    tag(img, "NEW YORK", t, (50, 100, 170))
    text_block(img, "Pizza goes global", F_MID, 400, t, delay=0.2)
    text_block(img, "Italian immigrants brought it to America.", F_SMALL, 560, t, (220, 230, 255), 0.9)


def s_today(img, d, t):
    camera(img, t, art_today(t), (W / 2, 1300))
    tag(img, "TODAY", t, (230, 60, 60))
    text_block(img, "Billions every year!", F_BIG, 430, t, delay=0.2)


def s_cta(img, d, t):
    text_block(img, "Learned something new?", F_MID, 330, t, delay=0.0)
    make_salt.draw_cta(img, d, W / 2, 1250, t, off=0.25)


base.SCENES[:] = [
    (3.0, ((55, 25, 15), (14, 6, 3)), s_hook),
    (9.0, ((70, 90, 140), (60, 40, 30)), s_naples),
    (6.0, ((60, 30, 20), (18, 8, 5)), s_street),
    (6.0, ((45, 45, 65), (12, 12, 20)), s_rich),
    (10.0, ((60, 25, 55), (20, 8, 25)), s_queen),
    (6.0, ((30, 45, 80), (10, 14, 28)), s_newyork),
    (5.0, ((55, 25, 15), (14, 6, 3)), s_today),
    (5.0, ((30, 30, 40), (8, 8, 12)), s_cta),
]

if __name__ == "__main__":
    base.main()
