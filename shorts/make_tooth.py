"""YouTube Short #17: "Ancient Romans Whitened Their Teeth With PEE?!"

Stop-the-scroll hook (LESSONS 30-33): bright purple frame, captions readable on mute, the key
word slams in, a stained tooth turns sparkling white on "it actually kind of worked" (~2.5 s).
Automatic timing, sound design, -14 LUFS, all lessons.

Usage: python make_tooth.py final.mp4 voice.mp3
"""
import math
import sys

from PIL import ImageDraw

import audio
import make_ketchup
import make_salt
import make_short as base
from fx import impact, overlay
from make_banana import captions
from make_chocolate import VIGNETTE, dust, sparkle
from make_honey import slam
from make_ketchup import camera, face, splat, stamp
from make_nutmeg import ship
from make_pizza import back, bokeh
from make_potato import pig
from make_short import F_MID, FONT_B, H, W, ease, font, person, tag, text_block
from style import heading
from timing import Timeline

WHITE, STAIN, MINT, GOLD = (250, 250, 255), (235, 210, 120), (120, 225, 200), (255, 205, 60)
make_ketchup.SPLAT_COLOR = MINT
base.HOOK_SKIP = 0.0
C = {}
HOOK_WORDS = []


def lerp(a, b, u):
    return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))


# ---------- drawings ----------

def tooth(d, x, y, s, t, col=WHITE, happy=True):
    """Cartoon molar with a face; (x, y) is the crown centre."""
    d.ellipse([x - 150 * s, y - 150 * s, x - 10 * s, y + 10 * s], fill=col)
    d.ellipse([x + 10 * s, y - 150 * s, x + 150 * s, y + 10 * s], fill=col)
    d.rounded_rectangle([x - 150 * s, y - 80 * s, x + 150 * s, y + 110 * s], radius=int(60 * s), fill=col)
    d.polygon([(x - 140 * s, y + 60 * s), (x - 30 * s, y + 60 * s), (x - 60 * s, y + 260 * s), (x - 110 * s, y + 250 * s)], fill=col)
    d.polygon([(x + 140 * s, y + 60 * s), (x + 30 * s, y + 60 * s), (x + 60 * s, y + 260 * s), (x + 110 * s, y + 250 * s)], fill=col)
    d.ellipse([x - 105 * s, y - 120 * s, x - 55 * s, y - 70 * s], fill=(255, 255, 255))  # shine
    if happy:
        face(d, x, y - 10 * s, t, 1.6 * s)
    else:
        for ex in (-35, 35):
            d.ellipse([x + (ex - 10) * s, y - 30 * s, x + (ex + 10) * s, y - 8 * s], fill=(40, 25, 20))
        d.arc([x - 35 * s, y + 30 * s, x + 35 * s, y + 70 * s], 200, 340, fill=(120, 50, 40), width=max(2, int(7 * s)))


def toothbrush(d, x, y, s, ang=0.0, handle=(80, 160, 230), bristle=(255, 255, 255)):
    c, sn = math.cos(ang), math.sin(ang)
    def r(px, py):
        return (x + (px * c - py * sn) * s, y + (px * sn + py * c) * s)
    d.polygon([r(-260, -16), r(60, -20), r(60, 20), r(-260, 16)], fill=handle)
    d.polygon([r(60, -24), r(200, -24), r(200, 24), r(60, 24)], fill=handle)
    for k in range(8):
        bx = 70 + k * 17
        d.polygon([r(bx, -24), r(bx + 10, -24), r(bx + 10, -90), r(bx, -90)], fill=bristle)


def amphora(d, x, y, s, liquid=True):
    d.ellipse([x - 90 * s, y - 120 * s, x + 90 * s, y + 140 * s], fill=(190, 110, 70))
    d.rectangle([x - 30 * s, y - 200 * s, x + 30 * s, y - 100 * s], fill=(190, 110, 70))
    d.rectangle([x - 42 * s, y - 215 * s, x + 42 * s, y - 195 * s], fill=(160, 90, 55))
    for side in (-1, 1):
        d.arc([x + side * 40 * s - 40 * s, y - 190 * s, x + side * 40 * s + 40 * s, y - 70 * s], 270 if side > 0 else 90, 90 if side > 0 else 270, fill=(160, 90, 55), width=max(2, int(12 * s)))
    d.polygon([(x - 60 * s, y + 20 * s), (x + 60 * s, y + 20 * s), (x, y + 120 * s)], fill=(150, 80, 50))  # pattern
    if liquid:
        d.ellipse([x - 26 * s, y - 214 * s, x + 26 * s, y - 196 * s], fill=(250, 220, 60))


def roman(d, x, y, s, t, phase=0.0):
    person(d, x, y, s, (240, 235, 225))
    d.polygon([(x - 95 * s, y - 120 * s), (x - 40 * s, y - 130 * s), (x + 95 * s, y + 100 * s), (x + 40 * s, y + 140 * s)], fill=(200, 60, 60))  # toga sash
    hx, hy = x, y - 200 * s
    for k in range(5):  # laurel wreath
        a = math.pi * (1.05 + k * 0.22)
        lx, ly = hx + math.cos(a) * 62 * s, hy + math.sin(a) * 62 * s
        d.ellipse([lx - 14 * s, ly - 8 * s, lx + 14 * s, ly + 8 * s], fill=(90, 160, 70))
    face(d, hx, hy, t, 0.95 * s, phase=phase)


def tube(d, x, y, s, squeeze=0.0):
    w = 90 * s * (1 - 0.25 * squeeze)
    d.polygon([(x - w, y - 260 * s), (x + w, y - 260 * s), (x + 60 * s, y + 120 * s), (x - 60 * s, y + 120 * s)], fill=(240, 245, 250))
    d.rectangle([x - w - 8 * s, y - 280 * s, x + w + 8 * s, y - 250 * s], fill=(200, 210, 220))
    d.rectangle([x - 60 * s, y - 120 * s, x + 60 * s, y - 30 * s], fill=(220, 60, 60))
    d.rounded_rectangle([x - 30 * s, y + 120 * s, x + 30 * s, y + 170 * s], radius=int(10 * s), fill=(60, 120, 200))  # cap end


def paste_swirl(d, x, y, s, p):
    n = int(18 * p)
    for k in range(n):
        a = k * 0.7
        px, py = x + k * 16 * s, y - abs(math.sin(a)) * 20 * s
        col = (255, 255, 255) if k % 2 else (90, 200, 230)
        d.ellipse([px - 22 * s, py - 22 * s, px + 22 * s, py + 22 * s], fill=col)


# ---------- illustrations ----------

def art_hook(t):
    def draw(d):
        cx, cy = W / 2, 1380
        def rays(od):
            for k in range(16):
                a = t * 0.25 + k * math.pi / 8
                od.polygon([(cx, cy - 40), (cx + math.cos(a - 0.09) * 1400, cy - 40 + math.sin(a - 0.09) * 1400),
                            (cx + math.cos(a + 0.09) * 1400, cy - 40 + math.sin(a + 0.09) * 1400)], fill=(255, 255, 255, 40))
        overlay(d, rays)
        u = ease((t - C["worked"]) / 0.6) if t > C["worked"] else 0.0
        tooth(d, cx + 120, cy - 40 + math.sin(t * 2.5) * 12, 1.9, t, lerp(STAIN, WHITE, u), happy=u > 0.5)
        amphora(d, cx - 300, cy + 260, 1.0)
        if u > 0:
            for k in range(8):  # sparkles burst when it turns white
                ph = (t * 0.9 + k / 8) % 1
                sparkle(d, cx + 120 + math.cos(k * 0.8 + t) * 330, cy - 60 + math.sin(k * 0.8 + t) * 300, 18 * math.sin(ph * math.pi) * u + 2)
    return draw


def s_hook(img, d, t):
    camera(img, t + 0.5, art_hook(t), (W / 2, 1380))
    dust(img, t, 1)
    sent2 = t >= C["and"] - 0.05
    words = HOOK_WORDS[C["split"]:] if sent2 else HOOK_WORDS[: C["split"]]
    captions(img, t, words, 300, {"PEE": GOLD, "WORKED": MINT})
    if not sent2:
        slam(img, "PEE?!", 660, t, C["pee"], GOLD, 170)
        impact(img, t, C["pee"] + 0.22)


def art_rome(t, ammonia_at, paid_at):
    def draw(d):
        cx, cy = W / 2, 1480
        for k in range(4):  # columns
            x = 110 + k * 290
            d.rectangle([x - 34, 900, x + 34, cy + 300], fill=(225, 215, 195))
            d.rectangle([x - 50, 880, x + 50, 910], fill=(205, 195, 175))
        roman(d, cx - 230, cy + 230, 1.3, t)
        amphora(d, cx + 180, cy + 230, 1.1)
        if t > ammonia_at:
            p = back((t - ammonia_at) / 0.35)
            f = font(FONT_B, max(10, int(56 * p)))
            tw = d.textlength("AMMONIA", font=f)
            d.rounded_rectangle([cx + 180 - tw / 2 - 24, cy - 260, cx + 180 + tw / 2 + 24, cy - 260 + f.size * 1.4], radius=24, fill=(255, 255, 255))
            d.text((cx + 180 - tw / 2, cy - 254), "AMMONIA", font=f, fill=(60, 120, 200))
        if t > paid_at:  # coins fly from the Roman to the amphora
            for k in range(6):
                ph = ((t - paid_at) * 0.9 + k / 6) % 1
                x = cx - 130 + ph * 300
                y = cy - 40 - math.sin(ph * math.pi) * 200
                d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=GOLD, outline=(200, 145, 30), width=4)
    return draw


def art_egypt(t, eggs_at, ash_at, myrrh_at):
    def draw(d):
        cx, cy = W / 2, 1500
        d.polygon([(cx + 40, cy + 100), (cx + 520, cy + 100), (cx + 280, cy - 110)], fill=(200, 160, 95))  # pyramid, background right
        d.rectangle([0, cy + 100, W, H], fill=(225, 190, 120))
        mx, my = cx - 170, cy + 230  # mortar and pestle grinding
        d.chord([mx - 170, my - 120, mx + 170, my + 160], 0, 180, fill=(140, 120, 100))
        d.rectangle([mx - 170, my + 10, mx + 170, my + 24], fill=(120, 100, 85))
        g = math.sin(t * 6) * 0.3
        d.line([(mx - 20, my - 10), (mx + 120 + math.cos(g) * 40, my - 220 + math.sin(g) * 40)], fill=(160, 140, 120), width=40)
        items = [(eggs_at, "shell"), (ash_at, "ash"), (myrrh_at, "myrrh")]
        for k, (at, kind) in enumerate(items):  # each ingredient pops onto its own plate as it's named
            p = back((t - at) / 0.35)
            if p <= 0:
                continue
            x, y = cx - 300 + k * 300, cy - 340
            d.ellipse([x - 110 * p, y - 70 * p, x + 110 * p, y + 70 * p], fill=(70, 50, 35))
            if kind == "shell":
                for j in range(4):
                    d.polygon([(x - 60 * p + j * 30 * p, y + 10 * p), (x - 30 * p + j * 30 * p, y - 40 * p), (x - 5 * p + j * 30 * p, y + 14 * p)], fill=(250, 248, 240))
            elif kind == "ash":
                d.chord([x - 75 * p, y - 50 * p, x + 75 * p, y + 50 * p], 180, 360, fill=(150, 145, 145))
            else:
                for j in range(3):
                    d.ellipse([x - 55 * p + j * 38 * p, y - 22 * p, x - 20 * p + j * 38 * p, y + 14 * p], fill=(225, 145, 40))
            lab = {"shell": "EGGSHELL", "ash": "ASH", "myrrh": "MYRRH"}[kind]
            f = font(FONT_B, max(10, int(46 * p)))
            tw = d.textlength(lab, font=f)
            d.text((x - tw / 2, y + 85), lab, font=f, fill=(255, 240, 210))
    return draw


def art_miswak(t, chew_at):
    def draw(d):
        cx, cy = W / 2, 1500
        person(d, cx - 220, cy + 260, 1.35, (60, 110, 90))
        face(d, cx - 220, cy + 260 - 1.35 * 200, t, 1.25, phase=0.5)
        fray = ease((t - chew_at) / 1.6)
        sx, sy = cx + 40, cy - 40  # the twig
        d.line([(sx, sy), (sx + 360, sy - 180)], fill=(150, 110, 70), width=34)
        for k in range(10):  # the chewed end frays into bristles
            a = -0.46 + (k - 4.5) * 0.08 * fray
            ln = 30 + 60 * fray
            d.line([(sx + 360, sy - 180), (sx + 360 + math.cos(a) * ln, sy - 180 + math.sin(a) * ln)], fill=(235, 220, 180), width=6)
        for k in range(3):
            ph = (t * 0.8 + k * 0.33) % 1
            sparkle(d, sx + 420 + math.cos(k * 2 + t) * 80, sy - 220 + math.sin(k * 2 + t) * 60, 12 * math.sin(ph * math.pi) * fray + 1)
    return draw


def art_china(t, pig_at):
    def draw(d):
        cx, cy = W / 2, 1450
        toothbrush(d, cx - 30, cy - 120, 1.6, -0.15 + 0.05 * math.sin(t * 2), handle=(240, 230, 210), bristle=(60, 50, 45))
        p = back((t - pig_at) / 0.4)
        if p > 0:
            pig(d, cx - 60, cy + 290, 1.15 * p, t)
    return draw


def art_trade(t):
    def draw(d):
        cy = 1500
        d.rectangle([0, cy + 80, W, H], fill=(40, 90, 140))
        for k in range(5):
            y = cy + 110 + k * 75
            d.line([(j * 40, y + math.sin(j * 0.6 + t * 3 + k) * 12) for j in range(30)], fill=(80, 140, 190), width=7)
        sx = -260 + ease(t / max(1.0, C["trade_len"] - 0.5)) * (W / 2 + 260)
        ship(d, sx, cy + 40, 1.0, "english", t)
        toothbrush(d, sx - 60, cy - 120, 0.45, -0.2, handle=(240, 230, 210), bristle=(60, 50, 45))
    return draw


def art_tube(t, jar_at):
    def draw(d):
        cx, cy = W / 2, 1480
        sq = 0.5 + 0.5 * math.sin(t * 3)
        tube(d, cx + 180, cy, 1.25, sq)
        paste_swirl(d, cx + 180 + 10, cy + 260, 1.0, ease(t / 1.2))
        if t > jar_at:
            p = back((t - jar_at) / 0.35)
            x, y = cx - 260, cy + 120
            d.rounded_rectangle([x - 130 * p, y - 150 * p, x + 130 * p, y + 150 * p], radius=int(40 * p), fill=(225, 235, 245))
            d.rectangle([x - 140 * p, y - 190 * p, x + 140 * p, y - 140 * p], fill=(180, 140, 100))
            d.rounded_rectangle([x - 110 * p, y - 40 * p, x + 110 * p, y + 120 * p], radius=int(20 * p), fill=(245, 245, 240))
            f = font(FONT_B, max(10, int(46 * p)))
            tw = d.textlength("BEFORE", font=f)
            d.rounded_rectangle([x - tw / 2 - 16, y + 180, x + tw / 2 + 16, y + 240], radius=14, fill=(40, 30, 50))
            d.text((x - tw / 2, y + 184), "BEFORE", font=f, fill=(255, 220, 140))
    return draw


def art_today(t, fluoride_at):
    def draw(d):
        cx, cy = W / 2, 1420
        tooth(d, cx - 140, cy, 1.4, t)
        toothbrush(d, cx + 180, cy + 300, 1.2, -0.8)
        paste_swirl(d, cx + 210, cy + 50, 0.9, 1.0)
        if t > fluoride_at:  # shield with F = fluoride protection
            p = back((t - fluoride_at) / 0.35)
            x, y = cx + 230, cy - 300
            d.polygon([(x - 110 * p, y - 120 * p), (x + 110 * p, y - 120 * p), (x + 110 * p, y + 20 * p), (x, y + 140 * p), (x - 110 * p, y + 20 * p)], fill=(60, 160, 230))
            f = font(FONT_B, max(10, int(130 * p)))
            tw = d.textlength("F", font=f)
            d.text((x - tw / 2, y - 110 * p), "F", font=f, fill=(255, 255, 255))
        for k in range(6):
            ph = (t * 0.8 + k * 0.166) % 1
            sparkle(d, cx - 140 + math.cos(k * 1.05 + t) * 300, cy - 40 + math.sin(k * 1.05 + t) * 280, 13 * math.sin(ph * math.pi) + 2)
    return draw


# ---------- scenes ----------

def finish(img, t, seed):
    dust(img, t, seed)
    img.alpha_composite(VIGNETTE)


def s_rome(img, d, t):
    bokeh(img, t, 2, (255, 230, 190))
    camera(img, t, art_rome(t, C["ammonia"], C["paid"]), (W / 2, 1480))
    finish(img, t, 2)
    tag(img, "ANCIENT ROME", t, (180, 50, 50))
    heading(img, t, "Ammonia = a natural cleaner", "Some Romans even paid for \"imported\" pee!", C["paid"], sub_color=(255, 230, 220))


def s_egypt(img, d, t):
    camera(img, t, art_egypt(t, C["eggs"], C["ash"], C["myrrh"]), (W / 2, 1480))
    finish(img, t, 3)
    tag(img, "EGYPT · 5,000 YEARS AGO", t, (190, 140, 50))
    heading(img, t, "The first tooth powder", "Crushed eggshells, ashes and myrrh.", C["eggs"], sub_color=(255, 240, 210))


def s_miswak(img, d, t):
    bokeh(img, t, 4, (210, 245, 220))
    camera(img, t, art_miswak(t, C["chew"]), (W / 2, 1480))
    finish(img, t, 4)
    tag(img, "THE MIDDLE EAST", t, (50, 130, 90))
    heading(img, t, "Miswak: a twig toothbrush", "Chew the end into a brush. Still used today!", C["chew"], sub_color=(220, 245, 230))


def s_china(img, d, t):
    bokeh(img, t, 5, (255, 220, 230))
    camera(img, t, art_china(t, C["pig"]), (W / 2, 1450))
    finish(img, t, 5)
    tag(img, "THE CRAZY PART · CHINA 1498", t, (170, 60, 110))
    heading(img, t, "The first toothbrush", "Its bristles came from a pig's neck!", C["pig"], sub_color=(255, 225, 240))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 820, "PIG HAIR!", t, C["pig"] + 0.3, col=(255, 150, 170), size=90)
    impact(img, t, C["pig"] + 0.5)


def s_trade(img, d, t):
    camera(img, t, art_trade(t), (W / 2, 1480))
    finish(img, t, 6)
    tag(img, "TO EUROPE", t, (60, 100, 170))
    heading(img, t, "The idea sailed west", "Traders carried it all the way to Europe.", 0.6, sub_color=(220, 230, 250))


def s_tube(img, d, t):
    bokeh(img, t, 7, (230, 240, 255))
    camera(img, t, art_tube(t, C["jar"]), (W / 2, 1480))
    finish(img, t, 7)
    tag(img, "THE 1890s", t, (200, 60, 60))
    heading(img, t, "The toothpaste tube!", "Before that, it came in jars.", C["jar"], sub_color=(255, 230, 230))


def s_today(img, d, t):
    bokeh(img, t, 8, (210, 245, 240))
    camera(img, t, art_today(t, C["fluoride"]), (W / 2, 1420))
    finish(img, t, 8)
    tag(img, "TODAY", t, (230, 60, 60))
    heading(img, t, "Fluoride... and no pee!", f=font(FONT_B, 84), colors={"PEE!": GOLD})


def s_cta(img, d, t):
    text_block(img, "Learned something new?", F_MID, 330, t, delay=0.0)
    make_salt.draw_cta(img, d, W / 2, 1250, t, off=C["cta_off"])


base.TRANSITION = splat
SCENE_LIST = [
    (((175, 80, 235), (95, 35, 170)), s_hook),
    (((60, 35, 30), (18, 10, 8)), s_rome),
    (((70, 55, 30), (20, 15, 8)), s_egypt),
    (((30, 60, 50), (8, 18, 14)), s_miswak),
    (((60, 25, 55), (20, 8, 25)), s_china),
    (((60, 90, 140), (20, 40, 70)), s_trade),
    (((40, 45, 70), (12, 13, 22)), s_tube),
    (((30, 60, 70), (8, 18, 22)), s_today),
    (((30, 30, 40), (8, 8, 12)), s_cta),
]

if __name__ == "__main__":
    out, voice = sys.argv[1], sys.argv[2]
    tl = Timeline(voice)
    anchors = ["okay", "even earlier", "in the middle", "the crazy", "traders", "toothpaste in|toothpaste", "and today", "if you"]
    cues = ["pee|p", "and actually", "ammonia", "paid", "eggshells|eggs", "ashes", "myrrh|mir", "chew", "pig|big", "before", "fluoride", "like"]
    missing = tl.check(anchors + cues)
    if missing:
        print("words:", " ".join(f"{t:.1f}:{w}" for t, w in tl.words))
        sys.exit(f"missing anchors/cues: {missing}")
    durs = tl.plan(anchors, tail=1.6)
    s1 = "Ancient Romans whitened their teeth with pee.".split()
    s2 = "And it actually kind of worked!".split()
    t_pee, t_and = tl.find("pee|p"), tl.find("and actually")
    t_worked = tl.find("worked|work|award", t_and)

    def word_times(words, t0, t1):
        heard = [t for t, _ in tl.words if t0 - 0.05 <= t <= t1 + 0.05]
        if len(heard) == len(words):
            return list(zip(heard, words))
        return [(t0 + (t1 - t0) * i / (len(words) - 1), w) for i, w in enumerate(words)]
    HOOK_WORDS[:] = word_times(s1, tl.words[0][0], t_pee) + word_times(s2, t_and, t_worked)
    C.update(split=len(s1), pee=t_pee - 0.12, worked=t_worked, **{"and": t_and},
             ammonia=tl.cue("ammonia", 1), paid=tl.cue("paid", 1),
             eggs=tl.cue("eggshells|eggs", 2), ash=tl.cue("ashes", 2), myrrh=tl.cue("myrrh|mir", 2),
             chew=tl.cue("chew", 3), pig=tl.cue("pig|big", 4), jar=tl.cue("before", 6), fluoride=tl.cue("fluoride", 7),
             cta_off=tl.cue("like", 8) - 1.5)
    C["trade_len"] = durs[5]
    print("hook words:", [(round(t, 2), w) for t, w in HOOK_WORDS])
    print("durations:", durs, "total:", round(sum(durs), 2))
    print("cues:", C)
    base.SCENES[:] = [(dd,) + sc for dd, sc in zip(durs, SCENE_LIST)]
    total, S = sum(durs), tl.starts
    events = [("whoosh", s) for s in S[1:]]
    events += [("thud", C["pee"] + 0.22), ("ding", C["worked"]), ("pop", S[1] + C["ammonia"]), ("pop", S[1] + C["paid"]),
               ("pop", S[2] + C["eggs"]), ("pop", S[2] + C["ash"]), ("pop", S[2] + C["myrrh"]), ("pop", S[4] + C["pig"]),
               ("thud", S[4] + C["pig"] + 0.5), ("pop", S[6] + C["jar"]), ("pop", S[7] + C["fluoride"]),
               ("click", S[8] + C["cta_off"] + 1.6), ("click", S[8] + C["cta_off"] + 3.6), ("ding", S[8] + C["cta_off"] + 3.65)]
    audio.music("music.wav", total)
    audio.sfx("sfx.wav", total, events)
    base.OUT = "base_tooth.mp4"
    sys.argv = [sys.argv[0], "base_tooth.mp4"]
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_tooth.mp4", voice, "music.wav", "sfx.wav", out)
    print("wrote", out)
