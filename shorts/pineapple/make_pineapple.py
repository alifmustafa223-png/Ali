"""YouTube Short #19: "People Used to RENT Pineapples?!" (first video made from AI illustrations).

New this time: Gemini illustrations animated with a cinematic camera (push-ins / pull-outs toward the
subject), living light (flickering candles, lanterns, chandeliers, fire), weather and particles
(snow, steam, flies, stars, sparkles) placed on the real objects in each picture, a blinking
pineapple character, and the classic title + subtitle + slam/stamp style with sound design.

Usage: python make_pineapple.py final.mp4 voice.mp3 paras.json
"""
import json
import math
import random
import sys

sys.path.insert(0, "..")

from PIL import Image, ImageDraw, ImageFilter

import audio
import make_ketchup
import make_salt
import make_short as base
from fx import impact
from make_chocolate import VIGNETTE, dust, sparkle
from make_honey import slam
from make_ketchup import splat, stamp
from make_pizza import back, bokeh
from make_short import F_MID, FONT_B, FONT_M, H, W, ease, font, tag, text_block
from style import heading
from timing import Timeline

GOLD, WARM, RED, ICE, MUD = (255, 200, 60), (255, 170, 80), (230, 60, 60), (170, 215, 255), (150, 110, 60)
make_ketchup.SPLAT_COLOR = (250, 195, 50)
base.HOOK_SKIP = 0.0
C = {}

# ---------- pictures + camera ----------

SRC = {}


def load(name):
    if name not in SRC:
        SRC[name] = Image.open(f"img/{name}.jpg").convert("RGB")
    return SRC[name]


def blink_variants():
    """Three copies of the cute pineapple with its eyelids 0 %, 55 % and 100 % closed."""
    im = load("02b_face")
    out = [im]
    lid = (226, 158, 40)
    for frac in (0.55, 1.0):
        v = im.copy()
        d = ImageDraw.Draw(v)
        for cx in (683, 858):
            x0, y0, x1, y1 = cx - 56, 1896, cx + 56, 2004
            m = Image.new("L", v.size, 0)
            ImageDraw.Draw(m).ellipse([x0, y0, x1, y1], fill=255)
            cut = Image.new("L", v.size, 0)
            ImageDraw.Draw(cut).rectangle([x0, y0, x1, y0 + (y1 - y0) * frac], fill=255)
            from PIL import ImageChops
            mask = ImageChops.multiply(m, cut).filter(ImageFilter.GaussianBlur(1.5))
            v.paste(lid, (0, 0), mask)
            ly = y0 + (y1 - y0) * frac
            d.arc([x0 + 4, ly - 14, x1 - 4, ly + 10], 10, 170, fill=(110, 60, 15), width=5)
        out.append(v)
    SRC["blink"] = out


def shot(name, t, dur, z0, z1, c0, c1):
    """Ken-Burns camera: zoom z0->z1 while the centre glides c0->c1 (source pixels), eased."""
    im = load(name)
    sw, sh = im.size
    p = 0.5 - 0.5 * math.cos(math.pi * min(1.0, max(0.0, t / dur)))
    z = z0 + (z1 - z0) * p
    bw = sw / z
    bh = bw * H / W
    cx = c0[0] + (c1[0] - c0[0]) * p + math.sin(t * 0.7) * 4  # tiny hand-held drift
    cy = c0[1] + (c1[1] - c0[1]) * p + math.cos(t * 0.55) * 4
    cx = min(max(cx, bw / 2), sw - bw / 2)
    cy = min(max(cy, bh / 2), sh - bh / 2)
    box = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
    frame = im.resize((W, H), Image.BILINEAR, box=box).convert("RGBA")
    k = W / bw
    to = lambda x, y: ((x - box[0]) * k, (y - box[1]) * k)
    return frame, to, k


def scene_base(img, frame):
    img.paste(frame)


# ---------- light + particles ----------

_SPRITE = Image.new("L", (128, 128), 0)
ImageDraw.Draw(_SPRITE).ellipse([16, 16, 112, 112], fill=255)
_SPRITE = _SPRITE.filter(ImageFilter.GaussianBlur(18))
_SPRITE_CACHE = {}


def _sprite(r):
    r = max(4, int(r))
    if r not in _SPRITE_CACHE:
        _SPRITE_CACHE[r] = _SPRITE.resize((2 * r, 2 * r), Image.BILINEAR)
    return _SPRITE_CACHE[r]


def glows(img, items):
    """items: (x, y, radius, color, strength 0..1) in screen pixels. One layer, blended once (LESSONS #5)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for x, y, r, col, s in items:
        if s <= 0.01 or x < -r or x > W + r or y < -r or y > H + r:
            continue
        sp = _sprite(r)
        m = sp.point(lambda v, s=s: int(v * min(1.0, s)))
        layer.paste(col + (255,), (int(x - r), int(y - r)), m)
        # paste replaces; overlapping glows just merge, which is fine for soft light
    img.alpha_composite(layer)


def flick(t, ph, base_=0.55, amp=0.25):
    return base_ + amp * (0.6 * math.sin(t * 11 + ph) + 0.4 * math.sin(t * 27 + ph * 3.1))


def lights(img, t, to, k, spots, col=WARM, r=70, base_=0.5, amp=0.22):
    glows(img, [(*to(x, y), r * k * (1.4 if big else 1.0), col, flick(t, i * 1.3, base_, amp)) for i, (x, y, big) in enumerate(spots)])


def sparkles(img, t, to, k, pts, col=(255, 240, 170), size=14, speed=1.0):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, (x, y) in enumerate(pts):
        ph = (t * speed * 0.9 + i * 0.37) % 1.6
        if ph > 1:
            continue
        s = math.sin(ph * math.pi) * size
        sx, sy = to(x, y)
        sparkle(d, sx, sy, s, col + (230,))
    img.alpha_composite(layer)


def burst(img, t, at, cx, cy, n=12, reach=260, col=(255, 235, 150)):
    """Sparkles fly outward from (cx, cy) when something special appears."""
    p = (t - at) / 0.9
    if not 0 < p < 1:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(n):
        a = i / n * 2 * math.pi + 0.3
        r = reach * ease(p) * (0.75 + 0.25 * math.sin(i * 2.3))
        s = 20 * (1 - p) + 4
        sparkle(d, cx + math.cos(a) * r, cy + math.sin(a) * r, s, col + (int(255 * (1 - p * 0.8)),))
    img.alpha_composite(layer)


def snow(img, t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(7)
    for i in range(140):
        depth = rnd.choice((0.5, 0.8, 1.3))
        x0, y0, ph = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(0, 6.28)
        y = (y0 + t * 120 * depth) % (H + 40) - 20
        x = (x0 + math.sin(t * 0.9 * depth + ph) * 30 * depth + t * 12 * depth) % W
        r = 2.5 * depth + 1
        d.ellipse([x - r, y - r, x + r, y + r], fill=(240, 245, 255, int(150 + 70 * (depth > 1))))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.8)))


def steam(img, t, to, k, sources):
    """Soft puffs rising and spreading from the manure pits."""
    small = Image.new("RGBA", (W // 4, H // 4), (0, 0, 0, 0))
    for i, (x, y) in enumerate(sources):
        for j in range(4):
            ph = (t * 0.28 + j * 0.25 + i * 0.13) % 1
            sx, sy = to(x, y)
            px = (sx + math.sin(t * 0.8 + i + j) * 40 * ph) / 4
            py = (sy - ph * 520 * k) / 4
            r = (30 + 90 * ph) * k / 4 + 4
            a = math.sin(ph * math.pi) * 0.33
            sp = _sprite(r).point(lambda v, a=a: int(v * a))
            small.paste((235, 225, 215, 255), (int(px - r), int(py - r)), sp)
    img.alpha_composite(small.resize((W, H), Image.BILINEAR))


def flies(img, t, to, centres):
    d = ImageDraw.Draw(img, "RGBA")
    for i, (x, y) in enumerate(centres):
        for j in range(3):
            a = t * (3.2 + j * 0.9) + i * 2 + j * 2.1
            sx, sy = to(x, y)
            fx = sx + math.cos(a) * (60 + 20 * j) + math.sin(a * 2.7) * 15
            fy = sy + math.sin(a * 1.3) * (35 + 10 * j)
            wing = 5 + 3 * math.sin(t * 60 + j)
            d.ellipse([fx - wing - 4, fy - 8, fx - 1, fy - 1], fill=(220, 230, 240, 120))
            d.ellipse([fx + 1, fy - 8, fx + wing + 4, fy - 1], fill=(220, 230, 240, 120))
            d.ellipse([fx - 4, fy - 4, fx + 4, fy + 4], fill=(25, 20, 18, 255))


def stars(img, t, to, k, n=40):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(3)
    for i in range(n):
        x, y = rnd.uniform(40, 1500), rnd.uniform(60, 1000)
        tw = 0.5 + 0.5 * math.sin(t * rnd.uniform(1.5, 3.5) + i)
        sx, sy = to(x, y)
        r = 1.5 + 2.5 * tw
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 250, 230, int(90 + 140 * tw)))
        if i % 7 == 0 and tw > 0.85:
            sparkle(d, sx, sy, 7 * tw, (255, 250, 230, 200))
    img.alpha_composite(layer)


def shimmer(img, t, to, k):
    """Sun glints dancing on the sea."""
    d = ImageDraw.Draw(img, "RGBA")
    rnd = random.Random(5)
    for i in range(26):
        x, y = rnd.uniform(800, 1450), rnd.uniform(1640, 1880)
        a = math.sin(t * 2.4 + i * 1.7)
        if a < 0.2:
            continue
        sx, sy = to(x + math.sin(t + i) * 12, y)
        w = (12 + 18 * a) * k
        d.line([(sx - w, sy), (sx + w, sy)], fill=(255, 215, 150, int(170 * a)), width=max(2, int(3 * k)))


TOP = Image.new("RGBA", (W, H), (0, 0, 0, 0))
_td = ImageDraw.Draw(TOP)
for _y in range(0, 900, 6):
    _td.rectangle([0, _y, W, _y + 6], fill=(5, 4, 10, int(150 * (1 - _y / 900) ** 1.6)))


def finish(img, t, seed, motes=True):
    if motes:
        dust(img, t, seed)
    img.alpha_composite(VIGNETTE)
    img.alpha_composite(TOP)


def title(img, t, text, sub=None, sub_at=1.0, y=400, sub_color=(255, 235, 210), colors=None):
    heading(img, t, text, sub, sub_at, F_MID, y, colors=colors, sub_color=sub_color)


# ---------- scenes ----------

def s_hook(img, d, t):
    fr, to, k = shot("01", t, C["d"][0], 1.0, 1.12, (768, 1380), (640, 1520))
    scene_base(img, fr)
    lights(img, t, to, k, [(760, 1120, True), (40, 1380, False), (1490, 1380, False), (250, 1500, False), (1290, 1500, False)], r=90)
    sparkles(img, t, to, k, [(470, 1600), (560, 1660), (500, 1800), (600, 1760), (430, 1720)], size=16, speed=1.3)
    bokeh(img, t, 1, (255, 220, 150))
    finish(img, t, 1)
    dd = ImageDraw.Draw(img, "RGBA")
    line = "In the 1700s, people"
    tw = dd.textlength(line, font=F_MID)
    dd.text(((W - tw) / 2 + 4, 255), line, font=F_MID, fill=(0, 0, 0, 140))
    dd.text(((W - tw) / 2, 250), line, font=F_MID, fill=(255, 255, 255))
    slam(img, "RENTED", 360, t, C["rented"], GOLD, 170)
    text_block(img, "pineapples... just to show off!", font(FONT_B, 62), 580, t, (255, 255, 255), C["pine"])
    text_block(img, "And one man built a HOUSE", font(FONT_B, 56), 690, t, GOLD, C["house"])
    text_block(img, "shaped like one!", font(FONT_B, 56), 760, t, GOLD, C["house"] + 0.5)
    impact(img, t, C["rented"] + 0.2, 18)


def s_price(img, d, t):
    fr, to, k = shot("02", t, C["d"][1], 1.05, 1.25, (768, 1400), (770, 1520))
    scene_base(img, fr)
    sp = 0.35 + 0.25 * max(0.0, 1 - abs(t - C["eight"] - 0.2) / 0.6)
    glows(img, [(*to(770, 1700), 330 * k, (255, 235, 180), sp)])
    lights(img, t, to, k, [(136, 1860, False), (196, 1930, False), (1224, 1930, False), (1344, 1880, False), (1456, 2160, False), (1352, 2460, False), (112, 2370, False)], r=60)
    sparkles(img, t, to, k, [(300, 2250), (520, 2600), (1000, 2550), (1200, 2300), (900, 2650), (420, 2480), (1100, 2420), (650, 2700)], size=16)
    finish(img, t, 2)
    text_block(img, "One pineapple cost about...", font(FONT_B, 64), 260, t, (255, 255, 255), 0.25)
    slam(img, "$8,000", 400, t, C["eight"], GOLD, 210)
    text_block(img, "in today's money!", font(FONT_M, 54), 650, t, (255, 235, 210), C["todays"])
    burst(img, t, C["eight"] + 0.15, *to(770, 1900), reach=330)
    impact(img, t, C["eight"] + 0.2, 20)


def s_columbus(img, d, t):
    fr, to, k = shot("03", t, C["d"][2], 1.0, 1.15, (768, 1380), (900, 1500))
    scene_base(img, fr)
    glows(img, [(*to(980, 1640), 260 * k, (255, 170, 90), 0.35 + 0.08 * math.sin(t * 1.5))])
    shimmer(img, t, to, k)
    burst(img, t, C["fruit"], *to(1135, 1990), n=10, reach=180)
    finish(img, t, 3)
    tag(img, "1493", t, (230, 120, 40))
    title(img, t, "Columbus finds a strange fruit", "on an island in the Caribbean", C["carib"])


def s_ship(img, d, t):
    fr, to, k = shot("04", t, C["d"][3], 1.1, 1.0, (820, 1500), (768, 1376))
    scene_base(img, fr)
    lights(img, t, to, k, [(540, 1530, True)], r=120, base_=0.55, amp=0.3)
    flies(img, t, to, [(350, 2330), (1180, 2420), (180, 2160)])
    finish(img, t, 4)
    title(img, t, "The long trip home...", "Almost every pineapple...", C["almost"])
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "ROTTED", t, C["rot"], col=(140, 200, 80))
    impact(img, t, C["rot"] + 0.15, 14)


def s_snow(img, d, t):
    fr, to, k = shot("05", t, C["d"][4], 1.0, 1.12, (768, 1380), (740, 1500))
    scene_base(img, fr)
    glows(img, [(*to(1200, 1300), 300 * k, (190, 160, 220), 0.25)])
    snow(img, t)
    finish(img, t, 5, motes=False)
    title(img, t, "Europe tries to grow its own", "...but the cold killed every plant.", C["cold"], sub_color=ICE)
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "200 YEARS", t, C["two"], col=ICE, size=110)
    impact(img, t, C["two"] + 0.15, 12)


def s_manure(img, d, t):
    fr, to, k = shot("06", t, C["d"][5], 1.0, 1.15, (768, 1380), (870, 1540))
    scene_base(img, fr)
    lights(img, t, to, k, [(200, 2010, True), (248, 1500, False), (448, 1580, False)], col=(255, 140, 50), r=110, base_=0.55, amp=0.3)
    steam(img, t, to, k, [(250, 2300), (640, 2450), (1150, 2400), (900, 2600), (420, 2600)])
    finish(img, t, 6, motes=False)
    title(img, t, "The disgusting trick", "Heated with rotting MANURE!", C["heated"], sub_color=(255, 215, 160))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 720, "EWW!", t, C["rotting"], col=(170, 120, 60))
    impact(img, t, C["rotting"] + 0.15, 14)


def s_king(img, d, t):
    fr, to, k = shot("07", t, C["d"][6], 1.0, 1.12, (768, 1380), (790, 1520))
    scene_base(img, fr)
    lights(img, t, to, k, [(32, 1340, True), (1500, 1340, True), (1450, 1450, False)], r=90)
    glows(img, [(*to(735, 1930), 170 * k, (255, 225, 120), 0.25 + 0.35 * ease((t - C["handed"]) / 0.4))])
    burst(img, t, C["handed"], *to(735, 1930), n=14, reach=260)
    sparkles(img, t, to, k, [(660, 1800), (820, 1860), (700, 2080), (800, 2040)], size=14, speed=1.4)
    finish(img, t, 7)
    tag(img, "KING CHARLES II", t, (200, 40, 60))
    title(img, t, "A gift for the King", "It was a royal sensation!", C["royal"])


def s_trophy(img, d, t):
    blink = SRC["blink"]
    cyc = (t + 0.4) % 2.8
    closed = 2 if 0.05 < cyc < 0.13 else 1 if cyc < 0.18 else 0
    SRC["02b_now"] = blink[closed]
    fr, to, k = shot("02b_now", t, C["d"][7], 1.1, 1.3, (780, 1700), (770, 1800))
    scene_base(img, fr)
    glows(img, [(*to(770, 1700), 300 * k, (220, 240, 255), 0.25 + 0.06 * math.sin(t * 2))])
    lights(img, t, to, k, [(1320, 2140, False), (1400, 2250, False), (1350, 2400, False), (230, 2500, False), (1240, 2560, False)], r=60)
    sparkles(img, t, to, k, [(560, 1700), (980, 1750), (600, 2050), (950, 2000), (770, 1600)], size=12, col=(220, 250, 255))
    bokeh(img, t, 3, (255, 230, 180))
    finish(img, t, 8)
    title(img, t, "Nobody even ATE them!", "Just trophies, until they rotted!", C["sat"])


def s_rent(img, d, t):
    fr, to, k = shot("08", t, C["d"][8], 1.0, 1.12, (768, 1380), (760, 1540))
    scene_base(img, fr)
    lights(img, t, to, k, [(920, 1530, True), (80, 2110, False), (200, 2290, False), (1000, 1960, False), (240, 1340, False)], r=80)
    sw = (t * 1.2) % 2.2
    if sw < 0.5:  # glint sweeping across the pocket watch
        sparkle(ImageDraw.Draw(img, "RGBA"), *to(645 + sw * 40, 1950), 16 * math.sin(sw / 0.5 * math.pi), (255, 255, 240, 230))
    sparkles(img, t, to, k, [(800, 1900), (860, 2020), (740, 2050)], size=12)
    finish(img, t, 9)
    tag(img, "FOR RENT", t, (230, 120, 40))
    title(img, t, "Rented out for the night", "...then on to the next party!", C["same"])


def s_house(img, d, t):
    fr, to, k = shot("09", t, C["d"][9], 1.0, 1.1, (768, 1380), (800, 1460))
    scene_base(img, fr)
    stars(img, t, to, k)
    lights(img, t, to, k, [(944, 1790, False), (1056, 1790, False), (900, 1800, False), (915, 2090, True), (1150, 2000, False)], col=(255, 170, 70), r=70, base_=0.45, amp=0.15)
    lights(img, t, to, k, [(115, 2240, False), (300, 2220, False), (1170, 2240, False), (1360, 2270, False)], col=(255, 150, 50), r=40, base_=0.5, amp=0.3)
    burst(img, t, C["giant"], *to(900, 1200), n=14, reach=300)
    finish(img, t, 10, motes=False)
    tag(img, "SCOTLAND, 1761", t, (110, 70, 170))
    title(img, t, "A house with a PINEAPPLE on top", "...and it's still standing today!", C["still"])


def s_today(img, d, t):
    fr, to, k = shot("10", t, C["d"][10], 1.12, 1.0, (770, 1500), (768, 1376))
    scene_base(img, fr)
    bulbs = [(176, 1060), (516, 1080), (1036, 1080), (1368, 1040), (368, 1170), (1236, 1170), (1500, 1250), (240, 1320)]
    lights(img, t, to, k, [(x, y, False) for x, y in bulbs], col=(255, 200, 110), r=55, base_=0.5, amp=0.15)
    bokeh(img, t, 5, (255, 220, 150))
    finish(img, t, 11)
    title(img, t, "Today? Super cheap!", "Fast ships brought them everywhere", C["fast"], y=260)
    slam(img, "ONLY $2", 520, t, C["dollars"], GOLD, 160)
    burst(img, t, C["dollars"] + 0.1, W / 2, 600, reach=420)
    impact(img, t, C["dollars"] + 0.2, 16)


def s_cta(img, d, t):
    fr, to, k = shot("01", t, C["d"][11], 1.12, 1.12, (640, 1520), (640, 1520))
    scene_base(img, fr.filter(ImageFilter.GaussianBlur(6)))
    img.alpha_composite(Image.new("RGBA", (W, H), (10, 6, 14, 165)))
    img.alpha_composite(VIGNETTE)
    text_block(img, "Learned something new?", font(FONT_B, 68), 330, t, delay=0.0)
    make_salt.draw_cta(img, ImageDraw.Draw(img, "RGBA"), W / 2, 1250, t, off=C["cta_off"])


SCENE_LIST = [s_hook, s_price, s_columbus, s_ship, s_snow, s_manure, s_king, s_trophy, s_rent, s_house, s_today, s_cta]
base.TRANSITION = splat

if __name__ == "__main__":
    out, voice, paras = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3]))
    tl = Timeline(voice)
    assert len(paras) == len(SCENE_LIST)
    starts = [0.0] + [(paras[i - 1][1] + paras[i][0]) / 2 for i in range(1, len(paras))]
    total = round(tl.length + 1.9, 2)
    durs = [round(b - a, 2) for a, b in zip(starts, starts[1:] + [total])]
    S = starts
    f = lambda phrase, sc, lead=0.1: round(tl.find(phrase, S[sc]) - S[sc] - lead, 2)
    C.update(d=durs, rented=f("rented", 0, 0.12), pine=f("pineapples", 0), house=f("and one", 0),
             eight=f("eight", 1, 0.12), todays=f("today's", 1), fruit=f("fruit", 2), carib=f("caribbean", 2, 0.3),
             almost=f("almost", 3, 0.3), rot=f("rod|rot", 3, 0.0), cold=f("the cold", 4, 0.3), two=f("two hundred", 4),
             heated=f("heated", 5, 0.4), rotting=f("rotting", 5), handed=f("handed", 6), royal=f("royal", 6, 0.3),
             sat=f("they sat", 7, 0.3), same=f("same", 8, 0.4), giant=f("giant", 9), still=f("still", 9, 0.3),
             dollars=f("two dollars", 10, 0.05), fast=f("fast", 10, 0.3))
    C["cta_off"] = round(tl.find("like", S[11]) - S[11] - 1.6 + 0.15, 2)
    print("durations:", durs, "total:", round(sum(durs), 2))
    print("cues:", C)
    blink_variants()
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), fn) for dd, fn in zip(durs, SCENE_LIST)]
    ev = [("whoosh", s) for s in S[1:]]
    ev += [("thud", C["rented"] + 0.2), ("pop", C["pine"]), ("pop", C["house"]),
           ("thud", S[1] + C["eight"] + 0.2), ("pop", S[2] + C["fruit"]), ("thud", S[3] + C["rot"] + 0.15),
           ("thud", S[4] + C["two"] + 0.15), ("thud", S[5] + C["rotting"] + 0.15), ("pop", S[6] + C["handed"]),
           ("ding", S[6] + C["handed"] + 0.05), ("pop", S[8] + 0.2), ("pop", S[9] + C["giant"]), ("pop", S[9] + 0.2),
           ("thud", S[10] + C["dollars"] + 0.2), ("ding", S[10] + C["dollars"] + 0.25),
           ("click", S[11] + C["cta_off"] + 1.6), ("click", S[11] + C["cta_off"] + 3.6), ("ding", S[11] + C["cta_off"] + 3.65)]
    audio.music("music.wav", total, bpm=96, seed=4)
    audio.sfx("sfx.wav", total, ev)
    base.OUT = "base_pineapple.mp4"
    if len(sys.argv) > 4:  # preview: render only the listed scenes
        keep = [int(x) for x in sys.argv[4].split(",")]
        base.SCENES[:] = [s for i, s in enumerate(base.SCENES) if i in keep]
    sys.argv = [sys.argv[0], "base_pineapple.mp4"]
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_pineapple.mp4", voice, "music.wav", "sfx.wav", out)
    print("wrote", out, "durations", ",".join(map(str, durs)))
