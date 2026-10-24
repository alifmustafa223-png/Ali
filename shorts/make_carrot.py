"""YouTube Short #10: "Carrots Used to Be PURPLE?!" (reuses the style from make_short.py).

Animation upgrades over the ketchup video: diagonal orange swipe transitions, parallax
backgrounds, a purple-to-orange color morph, colored key words in titles, a self-drawing
route map, and a night scene with searchlights and a sweeping radar screen.
"""
import math

from PIL import Image, ImageDraw

import make_short as base
import make_salt
from make_chocolate import VIGNETTE, dust, sparkle, title_pop
from make_ketchup import camera, face, stamp
from make_pizza import back, bokeh
from make_short import F_BIG, F_MID, F_SMALL, H, W, ease, font, FONT_B, FONT_M, person, tag, text_block

PURPLE, PURPLE_DARK = (150, 70, 200), (105, 45, 150)
ORANGE, ORANGE_DARK = (245, 140, 40), (205, 100, 25)
YELLOW, WHITE_C = (245, 205, 60), (240, 232, 210)
LEAF, LEAF_DARK = (80, 170, 70), (55, 130, 50)
HL = {"PURPLE": (200, 140, 255), "YELLOW": (255, 215, 80), "ORANGE": (255, 160, 60), "SECRET": (120, 230, 140)}


def lerp(a, b, u):
    return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))


# ---------- new animation helpers ----------

def swipe(img, t, dur, idx):
    """Scene change: a diagonal orange band sweeps across, hiding the old scene and revealing the new one."""
    last = idx == len(base.SCENES) - 1
    span = W + H * 0.45 + 200
    def cover(edge):  # everything left of a slanted line at position `edge`
        return [(-10, -10), (edge, -10), (edge - H * 0.45, H + 10), (-10, H + 10)]
    out = None
    if idx > 0 and t < 0.34:  # band continues off the right side, uncovering the new scene from the left
        e = ease(t / 0.34) * span
        out = img.copy()
        dd = ImageDraw.Draw(out)
        dd.polygon([(e, -10), (span + 50, -10), (span + 50, H + 10), (e - H * 0.45, H + 10)], fill=ORANGE)
        dd.polygon([(e, -10), (e + 40, -10), (e + 40 - H * 0.45, H + 10), (e - H * 0.45, H + 10)], fill=(255, 190, 110))
    if not last and t > dur - 0.3:  # band sweeps in from the left, covering the old scene
        e = ease((t - (dur - 0.3)) / 0.3) * span
        out = (out or img.copy())
        dd = ImageDraw.Draw(out)
        dd.polygon(cover(e), fill=ORANGE)
        dd.polygon([(e - 40, -10), (e, -10), (e - H * 0.45, H + 10), (e - 40 - H * 0.45, H + 10)], fill=(255, 190, 110))
    return out if out is not None else img


def parallax(img, t, layers):
    """Background bands that slide at different speeds for depth. layers: (y, height, color, speed, bumpiness)."""
    d = ImageDraw.Draw(img)
    for y, h, col, speed, bump in layers:
        off = (t * speed) % 400
        pts = [(-400 + i * 50 - off, y - bump * (0.5 + 0.5 * math.sin((i * 50) / 400 * 2 * math.pi))) for i in range(int((W + 800) / 50) + 2)]
        d.polygon(pts + [(W + 400, y + h), (-400, y + h)], fill=col)


def carrot(d, x, y, s, ang, body=ORANGE, dark=ORANGE_DARK, leaves=True):
    """Carrot pointing down; (x, y) is the top of the root."""
    c, sn = math.cos(ang), math.sin(ang)
    def rot(px, py):
        return (x + (px * c - py * sn) * s, y + (px * sn + py * c) * s)
    if leaves:
        for k, lx in enumerate((-25, 0, 25)):
            d.polygon([rot(lx - 12, 0), rot(lx + 12, 0), rot(lx * 2.4, -120 - 20 * (k == 1))], fill=LEAF if k != 1 else LEAF_DARK)
    d.polygon([rot(-48, -6), rot(48, -6), rot(8, 300), rot(-8, 300)], fill=body)
    for k in range(4):
        yy = 50 + k * 60
        w = 42 - k * 9
        d.line([rot(-w, yy), rot(-w + 18, yy + 6)], fill=dark, width=max(2, int(6 * s)))
        d.line([rot(w, yy + 25), rot(w - 18, yy + 31)], fill=dark, width=max(2, int(6 * s)))


# ---------- illustrations ----------

def art_hook(t):
    def draw(d):
        cx, cy = W / 2, 1000
        bob = math.sin(t * 2) * 14
        carrot(d, cx, cy + bob, 2.0, math.sin(t * 1.2) * 0.06, PURPLE, PURPLE_DARK)
        for k in range(7):
            ph = (t * 0.7 + k * 0.143) % 1
            sparkle(d, cx + math.cos(k * 0.9 + t * 0.8) * 320, cy + 280 + math.sin(k * 1.7 + t) * 330, 15 * math.sin(ph * math.pi) + 2, (220, 180, 255))
    return draw


def art_field(t):
    def draw(d):
        cy = 1460
        d.rectangle([0, cy + 40, W, cy + 600], fill=(110, 75, 45))
        for k in range(6):  # carrots pop out of the soil one by one
            p = back((t - 0.4 - k * 0.25) / 0.4)
            if p <= 0:
                continue
            x = 120 + k * 168
            col, dark = ((PURPLE, PURPLE_DARK) if k % 2 == 0 else (YELLOW, (200, 160, 40)))
            rise = 210 * p
            carrot(d, x, cy + 120 - rise, 0.95, math.sin(t * 2 + k) * 0.05, col, dark)
        d.rectangle([0, cy + 150, W, cy + 600], fill=(95, 62, 38))  # front soil hides the roots' lower part
        for k in range(14):
            d.ellipse([k * 80 - 20, cy + 135, k * 80 + 40, cy + 170], fill=(95, 62, 38))
    return draw


def art_route(t, beats):
    def draw(d):
        cy = 1350
        pins = [(W - 170, cy - 260), (W - 420, cy - 60), (W / 2 - 160, cy + 160), (170, cy - 120)]
        names = ["Afghanistan & Iran", "Middle East", "North Africa", "Europe"]
        times = [0.0, beats[0], beats[1], beats[2]]
        land = [(40, cy - 380), (W - 40, cy - 420), (W - 30, cy + 330), (60, cy + 360)]
        d.rounded_rectangle([40, cy - 420, W - 40, cy + 360], radius=60, fill=(215, 190, 140))
        for k in range(5):
            d.ellipse([90 + k * 190, cy - 360 + (k * 97) % 500, 230 + k * 190, cy - 280 + (k * 97) % 500], fill=(200, 175, 125))
        # route draws itself between pins, timed to the narration
        head = None
        for i in range(len(pins) - 1):
            if t <= times[i] + 0.1:
                break
            p = ease((t - times[i] - 0.1) / max(0.4, times[i + 1] - times[i] - 0.1))
            (x0, y0), (x1, y1) = pins[i], pins[i + 1]
            n = 20
            seg = [(x0 + (x1 - x0) * (j / n), y0 + (y1 - y0) * (j / n) - math.sin(j / n * math.pi) * 70) for j in range(int(n * p) + 1)]
            for j in range(0, len(seg) - 1, 2):
                d.line([seg[j], seg[j + 1]], fill=(150, 60, 40), width=12)
            head = seg[-1]
        if head:  # a little carrot travels along the route
            carrot(d, head[0], head[1] - 120, 0.35, 0.3, PURPLE, PURPLE_DARK)
        f = font(FONT_M, 40)
        for i, ((x, y), name) in enumerate(zip(pins, names)):
            p = back((t - times[i]) / 0.35)
            if p <= 0:
                continue
            d.ellipse([x - 26 * p, y - 26 * p, x + 26 * p, y + 26 * p], fill=(220, 50, 50))
            d.ellipse([x - 10 * p, y - 10 * p, x + 10 * p, y + 10 * p], fill=(255, 255, 255))
            tw = d.textlength(name, font=f)
            tx = min(max(x - tw / 2, 60), W - 60 - tw)
            d.rounded_rectangle([tx - 14, y + 34, tx + tw + 14, y + 92], radius=14, fill=(40, 40, 50, int(220 * min(1, p))))
            d.text((tx, y + 38), name, font=f, fill=(255, 255, 255, int(255 * min(1, p))))
    return draw


def art_dutch(t, morph_at):
    def draw(d):
        cx, cy = W / 2, 1400
        wx, wy = cx - 260, cy - 80  # windmill
        d.polygon([(wx - 90, cy + 230), (wx + 90, cy + 230), (wx + 55, wy), (wx - 55, wy)], fill=(200, 120, 80))
        d.polygon([(wx - 70, wy + 10), (wx + 70, wy + 10), (wx, wy - 90)], fill=(110, 70, 50))
        d.rectangle([wx - 25, cy + 140, wx + 25, cy + 230], fill=(90, 55, 35))
        for k in range(4):
            a = t * 1.6 + k * math.pi / 2
            c, s = math.cos(a), math.sin(a)
            hub = (wx, wy - 20)
            def r(px, py):
                return (hub[0] + px * c - py * s, hub[1] + px * s + py * c)
            d.polygon([r(10, -12), r(250, -12), r(250, 40), r(10, 40)], fill=(245, 240, 225))
            d.line([r(0, 0), r(250, 0)], fill=(90, 60, 40), width=8)
        d.ellipse([wx - 18, wy - 38, wx + 18, wy - 2], fill=(90, 60, 40))
        for k in range(9):  # tulip row
            x = 40 + k * 125
            sway = math.sin(t * 2 + k) * 6
            d.line([(x, cy + 330), (x + sway, cy + 250)], fill=LEAF_DARK, width=8)
            d.chord([x - 30 + sway, cy + 200, x + 30 + sway, cy + 270], 0, 180, fill=[(230, 60, 60), (245, 170, 40), (240, 110, 160)][k % 3])
            d.polygon([(x - 30 + sway, cy + 235), (x - 15 + sway, cy + 200), (x + sway, cy + 235), (x + 15 + sway, cy + 200), (x + 30 + sway, cy + 235)], fill=[(230, 60, 60), (245, 170, 40), (240, 110, 160)][k % 3])
        # the carrot morphs from purple to orange
        u = ease((t - morph_at) / 0.9)
        carrot(d, cx + 220, cy - 360, 1.25, math.sin(t * 1.5) * 0.06, lerp(PURPLE, ORANGE, u), lerp(PURPLE_DARK, ORANGE_DARK, u))
        if 0 < t - morph_at < 1.4:
            q = (t - morph_at) / 1.4
            for k in range(8):
                a = k * math.pi / 4 + q * 2
                sparkle(d, cx + 220 + math.cos(a) * 200 * (0.4 + q), cy - 170 + math.sin(a) * 260 * (0.4 + q), 16 * (1 - q) + 2)
    return draw


def art_crown(t):
    def draw(d):
        cx, cy = W / 2, 1450
        bob = math.sin(t * 2) * 10
        y = cy - 330 + bob
        d.polygon([(cx - 210, y + 140), (cx - 210, y - 20), (cx - 105, y + 60), (cx, y - 90), (cx + 105, y + 60), (cx + 210, y - 20), (cx + 210, y + 140)], fill=(240, 190, 50))
        for x in (cx - 130, cx, cx + 130):
            d.ellipse([x - 24, y + 80, x + 24, y + 128], fill=ORANGE)
        for k in range(3):
            carrot(d, cx - 220 + k * 220, cy + 60, 0.9, (k - 1) * 0.25, ORANGE, ORANGE_DARK)
        d.text((cx + 235, y - 40), "?", font=font(FONT_B, 160), fill=(255, 255, 255, 230))
    return draw


def art_war(t, radar_at):
    def draw(d):
        cx, cy = W / 2, 1450
        for k in range(14):  # stars
            x = (k * 263) % W
            y = 880 + (k * 131) % 380
            r = 3 + (math.sin(t * 3 + k) + 1) * 1.5
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 230))
        for k, base_x in enumerate((180, W - 180)):  # sweeping searchlights
            a = -math.pi / 2 + math.sin(t * 0.9 + k * 1.7) * 0.5
            tipx, tipy = base_x + math.cos(a) * 900, cy + 400 + math.sin(a) * 900
            d.polygon([(base_x - 10, cy + 400), (base_x + 10, cy + 400), (tipx + 90, tipy), (tipx - 90, tipy)], fill=(255, 250, 200, 55))
        px = -200 + ((t * 160) % (W + 400))  # plane crossing the sky
        py = 1000 + math.sin(t) * 20
        d.polygon([(px - 90, py), (px + 90, py - 8), (px + 110, py), (px + 90, py + 8)], fill=(60, 65, 80))
        d.polygon([(px - 10, py), (px + 30, py), (px - 30, py - 70), (px - 50, py - 70)], fill=(60, 65, 80))
        d.polygon([(px - 10, py), (px + 30, py), (px - 30, py + 70), (px - 50, py + 70)], fill=(60, 65, 80))
        d.rectangle([0, cy + 400, W, H], fill=(25, 30, 35))
        # radar screen with a sweeping beam (appears on "radar")
        p = back((t - radar_at) / 0.4)
        if p > 0:
            rx, ry, rr = cx + 220, cy + 190, 190 * p
            d.ellipse([rx - rr - 16, ry - rr - 16, rx + rr + 16, ry + rr + 16], fill=(60, 70, 80))
            d.ellipse([rx - rr, ry - rr, rx + rr, ry + rr], fill=(10, 45, 25))
            for k in (0.33, 0.66):
                d.ellipse([rx - rr * k, ry - rr * k, rx + rr * k, ry + rr * k], outline=(40, 140, 70), width=3)
            a = t * 3
            for j in range(12):  # fading trail behind the beam
                aj = a - j * 0.07
                d.pieslice([rx - rr, ry - rr, rx + rr, ry + rr], math.degrees(aj) - 4, math.degrees(aj), fill=(80, 230, 120, int(150 * (1 - j / 12))))
            bx, by = rx + math.cos(1.0) * rr * 0.6, ry + math.sin(1.0) * rr * 0.6
            blip = max(0.0, math.cos(a - 1.0)) ** 8
            d.ellipse([bx - 12, by - 12, bx + 12, by + 12], fill=(160, 255, 170, int(255 * blip)))
        # a pilot with "carrot vision"
        person(d, cx - 240, cy + 330, 1.2, (70, 90, 60))
        face(d, cx - 240, cy + 330 - 1.2 * 200, t, 1.1, glasses=True)
        carrot(d, cx - 120, cy + 120, 0.55, 0.9, ORANGE, ORANGE_DARK, leaves=True)
    return draw


def art_fudge(t):
    def draw(d):
        cx, cy = W / 2, 1450
        for k in range(2):  # jam jars
            p = back((t - 4.3 - k * 0.3) / 0.4)
            if p <= 0:
                continue
            x = cx - 260 + k * 200
            d.rounded_rectangle([x - 80 * p, cy - 130 * p, x + 80 * p, cy + 110 * p], radius=int(30 * p), fill=ORANGE)
            d.rectangle([x - 70 * p, cy - 170 * p, x + 70 * p, cy - 125 * p], fill=(230, 220, 200))
            d.rounded_rectangle([x - 55 * p, cy - 40 * p, x + 55 * p, cy + 30 * p], radius=10, fill=(250, 245, 230))
            carrot(d, x, cy - 25 * p, 0.12 * p, 0, ORANGE, ORANGE_DARK, leaves=False)
        for k in range(6):  # fudge squares stack up
            p = back((t - 1.6 - k * 0.2) / 0.35)
            if p <= 0:
                continue
            x = cx + 200 + (k % 3) * 95
            y = cy + 60 - (k // 3) * 95
            d.rounded_rectangle([x - 42 * p, y - 42 * p, x + 42 * p, y + 42 * p], radius=10, fill=(225, 150, 70))
            d.rounded_rectangle([x - 30 * p, y - 30 * p, x + 30 * p, y - 12 * p], radius=6, fill=(245, 185, 110))
        d.rounded_rectangle([cx - 430, cy + 115, cx + 430, cy + 150], radius=14, fill=(110, 70, 45))
    return draw


def art_today(t, purple_at):
    def draw(d):
        cx, cy = W / 2, 1180
        cols = [(ORANGE, ORANGE_DARK), (YELLOW, (200, 160, 40)), (WHITE_C, (200, 190, 165)), (PURPLE, PURPLE_DARK)]
        for k, (col, dark) in enumerate(cols):
            p = back((t - (1.8, 2.4, 3.0, 4.0)[k]) / 0.4)
            if p <= 0:
                continue
            x = 170 + k * 247
            hop = abs(math.sin(t * 3 + k)) * 12
            carrot(d, x, cy - hop, 1.05 * p, 0, col, dark)
        if t > purple_at:
            q = ease((t - purple_at) / 0.4)
            x, y = 170 + 3 * 247, cy - 230
            d.polygon([(x - 60, y + 40), (x - 60, y - 5), (x - 30, y + 20), (x, y - 30), (x + 30, y + 20), (x + 60, y - 5), (x + 60, y + 40)], fill=(240, 190, 50, int(255 * q)))
            f = font(FONT_B, 40)
            tw = d.textlength("ORIGINAL", font=f)
            d.rounded_rectangle([x - tw / 2 - 16, cy + 360, x + tw / 2 + 16, cy + 420], radius=16, fill=(150, 70, 200, int(255 * q)))
            d.text((x - tw / 2, cy + 366), "ORIGINAL", font=f, fill=(255, 255, 255, int(255 * q)))
            for k in range(6):
                ph = (t * 0.8 + k * 0.166) % 1
                sparkle(d, x + math.cos(k * 1.05 + t) * 140, cy + 120 + math.sin(k * 1.05 + t) * 240, 12 * math.sin(ph * math.pi) + 2, (220, 180, 255))
    return draw


# ---------- scenes ----------

def finish(img, t, seed):
    dust(img, t, seed)
    img.alpha_composite(VIGNETTE)


def s_hook(img, d, t):
    bokeh(img, t, 1, (220, 190, 255))
    camera(img, t, art_hook(t), (W / 2, 1300))
    finish(img, t, 1)
    text_block(img, "Carrots used to be", F_MID, 380, t)
    a = ease((t - 0.5) / 0.4)
    size = int(150 + 24 * math.sin(min(t, 1.5) * 4) * (1 - min(t / 1.5, 1)))
    f = font(FONT_B, max(60, size))
    if a > 0:
        dd = ImageDraw.Draw(img)
        tw = dd.textlength("PURPLE", font=f)
        dd.text(((W - tw) / 2, 500), "PURPLE", font=f, fill=HL["PURPLE"] + (int(255 * a),))


def s_field(img, d, t):
    parallax(img, t, [(1180, 900, (70, 75, 110), 8, 160), (1330, 800, (75, 110, 80), 22, 90)])
    camera(img, t, art_field(t), (W / 2, 1450))
    finish(img, t, 2)
    tag(img, "OVER 1,000 YEARS AGO", t, (120, 60, 160))
    title_pop(img, "Purple and yellow!", F_MID, 400, t, colors=HL)
    text_block(img, "Grown in what's now Afghanistan and Iran.", F_SMALL, 560, t, (235, 225, 250), 3.4)


ROUTE_BEATS = (3.0, 3.9, 5.3)


def s_route(img, d, t):
    bokeh(img, t, 3, (255, 230, 190))
    camera(img, t, art_route(t, ROUTE_BEATS), (W / 2, 1350))
    finish(img, t, 3)
    tag(img, "SPREADING WEST", t, (170, 110, 50))
    title_pop(img, "A long journey", F_BIG, 410, t)


MORPH_AT = 2.9


def s_dutch(img, d, t):
    parallax(img, t, [(1150, 900, (90, 120, 160), 6, 40), (1300, 800, (80, 140, 80), 18, 30)])
    camera(img, t, art_dutch(t, MORPH_AT), (W / 2, 1400))
    finish(img, t, 4)
    tag(img, "THE 1600s · NETHERLANDS", t, (230, 120, 30))
    title_pop(img, "Orange takes over", F_MID, 400, t, colors=HL)
    text_block(img, "Dutch farmers made orange carrots everyone's favorite.", F_SMALL, 560, t, (255, 230, 200), MORPH_AT)


MYTH_AT = 5.6


def s_crown(img, d, t):
    bokeh(img, t, 5, (255, 220, 160))
    camera(img, t, art_crown(t), (W / 2, 1400))
    finish(img, t, 5)
    tag(img, "THE ROYAL STORY", t, (200, 150, 30))
    title_pop(img, "For the royal family?", F_MID, 400, t)
    text_block(img, "A popular story: to honor the House of Orange.", F_SMALL, 560, t, (255, 240, 205), 0.5)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 880, "UNPROVEN", t, MYTH_AT, col=(230, 60, 60), size=100)


RADAR_AT, SECRET_AT = 10.4, 7.3


def s_war(img, d, t):
    camera(img, t, art_war(t, RADAR_AT), (W / 2, 1450))
    finish(img, t, 6)
    tag(img, "THE CRAZY PART · WWII", t, (170, 60, 110))
    title_pop(img, "Carrots = night vision?", F_MID, 400, t)
    text_block(img, "A cover story to hide Britain's secret radar!", F_SMALL, 560, t, (215, 240, 220), SECRET_AT)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 830, "SECRET", t, SECRET_AT, col=(120, 230, 140), size=95)


def s_fudge(img, d, t):
    bokeh(img, t, 7, (255, 210, 160))
    camera(img, t, art_fudge(t), (W / 2, 1400))
    finish(img, t, 7)
    tag(img, "WARTIME RECIPES", t, (200, 110, 40))
    title_pop(img, "Carrot fudge & jam!", F_MID, 400, t)


PURPLE_AT = 4.0


def s_today(img, d, t):
    camera(img, t, art_today(t, PURPLE_AT), (W / 2, 1350))
    finish(img, t, 8)
    tag(img, "TODAY", t, (230, 60, 60))
    title_pop(img, "And purple was first!", F_MID, 400, t, colors=HL)


def s_cta(img, d, t):
    text_block(img, "Learned something new?", F_MID, 330, t, delay=0.0)
    make_salt.draw_cta(img, d, W / 2, 1250, t, off=0.15)


base.TRANSITION = swipe
base.SCENES[:] = [
    (3.0, ((45, 25, 60), (12, 6, 18)), s_hook),
    (8.0, ((50, 40, 80), (14, 10, 24)), s_field),
    (6.0, ((40, 60, 90), (12, 18, 28)), s_route),
    (8.0, ((60, 110, 170), (40, 60, 40)), s_dutch),
    (8.0, ((60, 45, 20), (18, 12, 5)), s_crown),
    (10.0, ((15, 20, 45), (5, 6, 14)), s_war),
    (5.0, ((60, 35, 18), (16, 9, 4)), s_fudge),
    (6.0, ((45, 25, 60), (12, 6, 18)), s_today),
    (6.0, ((30, 30, 40), (8, 8, 12)), s_cta),
]

if __name__ == "__main__":
    base.main()
