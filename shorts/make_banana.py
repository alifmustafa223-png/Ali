"""YouTube Short #16: "Every Banana You've Eaten Is a CLONE".

Built to stop the scroll: bright yellow hook frame (stands out in a dark feed), the viewer is
addressed directly ("you've"), word-by-word captions readable with the sound off, an instant
visual of the claim (one banana copy-pastes into a grid of clones), and a stakes beat at ~2 s
("they could disappear"). Plus everything from LESSONS.md, automatic timing and sound design.

Usage: python make_banana.py final.mp4 voice.mp3
"""
import math
import sys

from PIL import Image, ImageDraw

import audio
import make_ketchup
import make_salt
import make_short as base
from fx import impact, overlay
from make_chocolate import VIGNETTE, dust, sparkle
from make_honey import slam
from make_ketchup import camera, face, splat, stamp
from make_lobster import frown_face
from make_pizza import back, bokeh
from make_short import F_MID, FONT_B, H, W, ease, font, person, tag, text_block
from style import heading
from timing import Timeline

YEL, YEL_DARK, BROWN, GREEN = (250, 215, 60), (225, 175, 40), (110, 70, 30), (90, 160, 70)
INK, RED = (40, 28, 10), (220, 45, 40)
make_ketchup.SPLAT_COLOR = YEL
base.HOOK_SKIP = 0.0
C = {}
HOOK_WORDS = []  # (time, word) for the karaoke captions, filled in __main__


# ---------- drawings ----------

def banana(d, x, y, s, ang=0.0, col=YEL, shade=YEL_DARK, spots=0):
    """Curved banana centred at (x, y)."""
    c, sn = math.cos(ang), math.sin(ang)
    def rot(px, py):
        return (x + (px * c - py * sn) * s, y + (px * sn + py * c) * s)
    outer, inner = [], []
    for k in range(21):
        a = math.pi * (0.15 + 0.7 * k / 20)
        thick = 46 * math.sin(math.pi * k / 20) + 10
        outer.append(rot(math.cos(a) * 170, math.sin(a) * 170 - 120))
        inner.append(rot(math.cos(a) * (170 - thick * 2), math.sin(a) * (170 - thick * 2) - 120))
    d.polygon(outer + inner[::-1], fill=col)
    mid = [rot(math.cos(math.pi * (0.15 + 0.7 * k / 20)) * (170 - 20), math.sin(math.pi * (0.15 + 0.7 * k / 20)) * (170 - 20) - 120) for k in range(4, 17)]
    d.line(mid, fill=shade, width=max(2, int(8 * s)))
    d.polygon([outer[0], inner[0], rot(math.cos(math.pi * 0.12) * 160 + 10, math.sin(math.pi * 0.12) * 160 - 150)], fill=BROWN)  # stem
    d.ellipse([outer[-1][0] - 7 * s, outer[-1][1] - 7 * s, outer[-1][0] + 7 * s, outer[-1][1] + 7 * s], fill=BROWN)  # tip
    for k in range(spots):
        i = 3 + (k * 7) % 15
        px, py = (outer[i][0] + inner[i][0]) / 2, (outer[i][1] + inner[i][1]) / 2
        d.ellipse([px - 8 * s, py - 6 * s, px + 8 * s, py + 6 * s], fill=BROWN)


def plant(d, x, base_y, s, t, k=0, sick=0.0):
    """Banana plant: green stem, big leaves, a hanging bunch. sick 0..1 browns and droops it."""
    leaf = tuple(int(GREEN[i] + ((140, 110, 50)[i] - GREEN[i]) * sick) for i in range(3))
    droop = sick * 0.8
    d.rectangle([x - 22 * s, base_y - 330 * s, x + 22 * s, base_y], fill=tuple(int(v * (1 - 0.3 * sick)) for v in (90, 140, 70)))
    for j, a in enumerate((-2.4, -1.9, -1.2, -0.7)):
        a2 = a + droop * (1 if a > -1.57 else -1) + math.sin(t * 1.5 + j + k) * 0.05
        lx, ly = x + math.cos(a2) * 190 * s, base_y - 330 * s + math.sin(a2) * 150 * s
        d.line([(x, base_y - 330 * s), (lx, ly)], fill=leaf, width=max(2, int(46 * s)))
    for j in range(3):  # bunch
        banana(d, x + (j - 1) * 26 * s, base_y - 180 * s, 0.32 * s, -0.4 + j * 0.3,
               col=tuple(int(YEL[i] + ((120, 90, 40)[i] - YEL[i]) * sick) for i in range(3)))


def seeds_cut(d, x, y, r):
    d.ellipse([x - r, y - r, x + r, y + r], fill=(245, 235, 200))
    for k in range(9):
        a = k * 2 * math.pi / 9
        sx, sy = x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55
        d.ellipse([sx - r * 0.13, sy - r * 0.13, sx + r * 0.13, sy + r * 0.13], fill=(30, 25, 20))
    d.ellipse([x - r * 0.15, y - r * 0.15, x + r * 0.15, y + r * 0.15], fill=(30, 25, 20))


# ---------- hook: karaoke captions + clones ----------

def captions(img, t, words, y, emphasize):
    """TikTok-style captions: whole sentence readable from frame 0 (works on mute); the word being
    spoken sits in a yellow box; spoken words turn solid white, key words turn yellow."""
    d = ImageDraw.Draw(img, "RGBA")
    f = font(FONT_B, 80)
    space = d.textlength(" ", font=f)
    lines, cur, w_cur = [], [], 0
    for tm, w in words:
        ww = d.textlength(w, font=f)
        if cur and w_cur + space + ww > W - 120:
            lines.append((cur, w_cur))
            cur, w_cur = [], 0
        w_cur += (space if cur else 0) + ww
        cur.append((tm, w, ww))
    lines.append((cur, w_cur))
    active = max([i for i, (tm, _) in enumerate(words) if t >= tm], default=-1)
    i = 0
    for li, (ws, lw) in enumerate(lines):
        x = (W - lw) / 2
        yy = y + li * 100
        for tm, w, ww in ws:
            key = w.strip(".,!?").upper()
            if i == active:
                d.rounded_rectangle([x - 12, yy - 4, x + ww + 12, yy + 92], radius=18, fill=(255, 215, 60))
                col = (30, 20, 10, 255)
            elif i < active:
                col = emphasize.get(key, (255, 255, 255)) + (255,)
            else:
                col = (255, 255, 255, 140)
            if i != active:
                d.text((x + 3, yy + 5), w, font=f, fill=(0, 0, 0, 120))
            d.text((x, yy), w, font=f, fill=col)
            x += ww + space
            i += 1


def art_hook(t):
    def draw(d):
        cx, cy = W / 2, 1380
        clone_t, gone_t = C["clone"], C["disappear"]
        def rays(od):
            for k in range(16):
                a = t * 0.25 + k * math.pi / 8
                od.polygon([(cx, cy - 60), (cx + math.cos(a - 0.09) * 1400, cy - 60 + math.sin(a - 0.09) * 1400),
                            (cx + math.cos(a + 0.09) * 1400, cy - 60 + math.sin(a + 0.09) * 1400)], fill=(255, 255, 255, 40))
        overlay(d, rays)
        n = 1 if t < clone_t else min(9, 1 + int((t - clone_t) / 0.09))
        for k in range(n):  # one banana copy-pastes itself into a 3x3 grid
            r, c = divmod(k, 3)
            tx, ty = (cx, cy) if k == 0 else (cx + (c - 1) * 300, cy - 280 + r * 280)
            if k == 0 and n > 1:
                tx, ty = cx - 300, cy - 280
            p = back((t - clone_t - k * 0.09) / 0.25) if k else 1.0
            sc = (2.4 if n == 1 else 0.95) * p
            if t > gone_t:  # then they vanish one by one
                q = ease((t - gone_t - k * 0.07) / 0.3)
                sc *= 1 - q
                if 0 < q < 1:
                    overlay(d, lambda od, tx=tx, ty=ty, q=q: od.ellipse([tx - 120 * q - 40, ty - 120 * q - 40, tx + 120 * q + 40, ty + 120 * q + 40], fill=(255, 255, 255, int(160 * (1 - q)))))
            if sc > 0.02:
                bob = math.sin(t * 3 + k) * 8
                banana(d, tx, ty + bob, sc, -0.2 + 0.05 * math.sin(t * 2 + k))
        if t > gone_t + 0.5:  # big "?!" where the bananas were
            p = back((t - gone_t - 0.5) / 0.35)
            f = font(FONT_B, max(10, int(300 * p)))
            tw = d.textlength("?!", font=f)
            d.text((cx - tw / 2 + 8, cy - 222 * p), "?!", font=f, fill=(30, 20, 60))
            d.text((cx - tw / 2, cy - 230 * p), "?!", font=f, fill=(255, 215, 60))
    return draw


def s_hook(img, d, t):
    camera(img, t + 0.5, art_hook(t), (W / 2, 1380))
    dust(img, t, 1)
    sent2 = t >= C["and"] - 0.05
    words = HOOK_WORDS[C["split"]:] if sent2 else HOOK_WORDS[: C["split"]]
    captions(img, t, words, 300, {"CLONE": (255, 215, 60), "DISAPPEAR": (255, 215, 60)})
    if not sent2:
        slam(img, "CLONE", 540, t, C["clone"], (255, 215, 60), 170)
        impact(img, t, C["clone"] + 0.22)


# ---------- story ----------

def art_seeds(t, cut_at):
    def draw(d):
        cx, cy = W / 2, 1450
        seeds_cut(d, cx - 230, cy - 120, 150)
        d.text((cx - 300, cy + 60), "WILD", font=font(FONT_B, 54), fill=(255, 220, 190))
        p = back((t - cut_at) / 0.4)
        if p > 0:
            d.ellipse([cx + 230 - 150 * p, cy - 270 * p, cx + 230 + 150 * p, cy + 30 * p], fill=(250, 240, 205))
            d.text((cx + 120, cy + 60), "SEEDLESS", font=font(FONT_B, max(10, int(54 * p))), fill=(255, 230, 140))
            d.rectangle([cx + 150, cy + 300, cx + 310, cy + 390], fill=(110, 80, 50))  # cutting planted in soil
            d.line([(cx + 230, cy + 300), (cx + 230, cy + 210)], fill=GREEN, width=16)
            d.ellipse([cx + 175, cy + 175, cx + 230, cy + 225], fill=GREEN)
            d.ellipse([cx + 230, cy + 165, cx + 290, cy + 215], fill=GREEN)
    return draw


def art_copies(t, sick_at):
    def draw(d):
        base_y = 1780
        for k in range(5):  # identical plants pop in, then sickness spreads down the row
            p = back((t - 0.2 - k * 0.25) / 0.35)
            if p <= 0:
                continue
            sick = ease((t - sick_at - k * 0.35) / 0.6) if t > sick_at else 0.0
            plant(d, 120 + k * 210, base_y, 0.85 * p, t, k, sick)
    return draw


def art_store(t):
    def draw(d):
        cx = W / 2
        for row, y in enumerate((1180, 1480)):  # supermarket shelves of identical bunches
            d.rectangle([60, y + 90, W - 60, y + 120], fill=(150, 150, 160))
            for k in range(4):
                p = back((t - 0.2 - (row * 4 + k) * 0.08) / 0.3)
                if p <= 0:
                    continue
                x = 190 + k * 235
                for j in range(3):
                    banana(d, x + (j - 1) * 34, y - 10, 0.55 * p, -0.3 + j * 0.25)
        d.rounded_rectangle([cx - 230, 1650, cx + 230, 1760], radius=20, fill=(250, 245, 230))
        f = font(FONT_B, 66)
        tw = d.textlength("CAVENDISH", font=f)
        d.text((cx - tw / 2, 1664), "CAVENDISH", font=f, fill=(60, 120, 60))
    return draw


def art_grandparents(t):
    def draw(d):
        cx, cy = W / 2, 1520
        for k, (dx, shirt) in enumerate(((-260, (110, 80, 130)), (-60, (80, 110, 150)))):
            person(d, cx + dx, cy + 220, 1.25, shirt)
            hx, hy = cx + dx, cy + 220 - 1.25 * 200
            d.chord([hx - 80, hy - 95, hx + 80, hy + 20], 180, 360, fill=(225, 225, 225))  # grey hair
            face(d, hx, hy, t + k, 1.15, glasses=k == 1)
        banana(d, cx + 300, cy - 100, 1.25, -0.5 + 0.05 * math.sin(t * 2))
        f = font(FONT_B, 44)
        lab = "GROS MICHEL"
        tw = d.textlength(lab, font=f)
        d.rounded_rectangle([cx + 300 - tw / 2 - 18, cy + 120, cx + 300 + tw / 2 + 18, cy + 180], radius=14, fill=(40, 30, 20))
        d.text((cx + 300 - tw / 2, cy + 124), lab, font=f, fill=(255, 225, 120))
        for k in range(4):  # little hearts = sweeter
            ph = (t * 0.6 + k * 0.25) % 1
            x, y = cx + 220 + k * 50, cy - 330 - ph * 160
            s = 18 * (1 - ph * 0.4)
            a = int(255 * (1 - ph))
            d.ellipse([x - s, y - s, x, y], fill=(240, 70, 100, a))
            d.ellipse([x, y - s, x + s, y], fill=(240, 70, 100, a))
            d.polygon([(x - s, y - s / 2), (x + s, y - s / 2), (x, y + s * 0.9)], fill=(240, 70, 100, a))
    return draw


def art_wipeout(t, wipe_at):
    def draw(d):
        base_y = 1800
        for k in range(5):
            sick = ease((t - wipe_at - k * 0.25) / 0.7) if t > wipe_at else 0.0
            plant(d, 120 + k * 210, base_y, 0.85, t, k, sick)
    return draw


def art_candy(t):
    def draw(d):
        cx, cy = W / 2, 1450
        for k in range(7):  # pile of banana-shaped candies on the left
            x = cx - 270 + (k % 3) * 80 - (k // 3) * 20
            y = cy + 120 - (k // 3) * 70 + math.sin(t * 2 + k) * 5
            banana(d, x, y, 0.42, -0.3 + (k % 3) * 0.3, col=(255, 230, 100), shade=(240, 190, 60))
        f = font(FONT_B, 54)
        d.text((cx - 360, cy + 220), "CANDY", font=f, fill=(255, 230, 140))
        eq = font(FONT_B, 150)
        tw = d.textlength("=", font=eq)
        d.text((cx - tw / 2, cy - 60), "=", font=eq, fill=(255, 255, 255))
        bob = math.sin(t * 2) * 10
        banana(d, cx + 260, cy + 40 + bob, 1.0, -0.3)
        lab = "GROS MICHEL"
        tw = d.textlength(lab, font=font(FONT_B, 44))
        d.rounded_rectangle([cx + 260 - tw / 2 - 16, cy + 210, cx + 260 + tw / 2 + 16, cy + 268], radius=14, fill=(40, 30, 20))
        d.text((cx + 260 - tw / 2, cy + 213), lab, font=font(FONT_B, 44), fill=(255, 225, 120))
        q = font(FONT_B, 120)
        d.text((cx - 30, cy - 360 + bob), "?", font=q, fill=(255, 230, 140))
    return draw


def art_today(t, enjoy_at):
    def draw(d):
        cx, cy = W / 2, 1500
        person(d, cx - 250, cy + 230, 1.35, (245, 245, 250))  # scientist
        face(d, cx - 250, cy + 230 - 1.35 * 200, t, 1.25, glasses=True)
        mx = cx - 120 + math.sin(t * 2) * 20  # magnifying glass
        d.ellipse([mx - 70, cy - 170, mx + 70, cy - 30], outline=(90, 90, 100), width=16)
        d.line([(mx - 50, cy - 50), (mx - 120, cy + 40)], fill=(90, 90, 100), width=18)
        sick = 0.25 + 0.15 * math.sin(t * 2)
        plant(d, cx + 240, cy + 300, 1.15, t, 0, sick if t < enjoy_at else 0.0)
        if t > enjoy_at:
            p = back((t - enjoy_at) / 0.35)
            for k in range(6):
                ph = (t * 0.8 + k * 0.166) % 1
                sparkle(d, cx + 240 + math.cos(k * 1.05 + t) * 230, cy - 50 + math.sin(k * 1.05 + t) * 200, 13 * math.sin(ph * math.pi) + 2)
    return draw


def finish(img, t, seed):
    dust(img, t, seed)
    img.alpha_composite(VIGNETTE)


def s_seeds(img, d, t):
    bokeh(img, t, 2, (255, 230, 170))
    camera(img, t, art_seeds(t, C["seedless"]), (W / 2, 1450))
    finish(img, t, 2)
    tag(img, "THOUSANDS OF YEARS AGO", t, (170, 120, 40))
    heading(img, t, "Wild bananas = hard seeds", "People grew the seedless ones from cuttings.", C["cuttings"], sub_color=(255, 235, 200))


def s_copies(img, d, t):
    camera(img, t, art_copies(t, C["sick"]), (W / 2, 1600))
    finish(img, t, 3)
    tag(img, "HERE'S THE THING", t, (70, 130, 70))
    heading(img, t, "Every plant is a COPY", "So if one gets sick... they all can.", C["sick"], colors={"COPY": YEL}, sub_color=(225, 245, 220))


def s_store(img, d, t):
    bokeh(img, t, 4, (255, 240, 190))
    camera(img, t, art_store(t), (W / 2, 1450))
    finish(img, t, 4)
    tag(img, "YOUR SUPERMARKET", t, (60, 110, 160))
    heading(img, t, "Just ONE type", "Almost every banana in stores: the Cavendish.", 0.8, colors={"ONE": YEL}, sub_color=(220, 235, 250))


def s_grand(img, d, t):
    bokeh(img, t, 5, (255, 210, 230))
    camera(img, t, art_grandparents(t), (W / 2, 1500))
    finish(img, t, 5)
    tag(img, "THE CRAZY PART", t, (170, 60, 110))
    heading(img, t, "Your grandparents' banana", "The Gros Michel: bigger and sweeter.", C["bigger"], sub_color=(255, 225, 240))


def s_wipe(img, d, t):
    camera(img, t, art_wipeout(t, C["wiped"]), (W / 2, 1600))
    finish(img, t, 6)
    tag(img, "THE 1950s", t, (120, 80, 50))
    heading(img, t, "A disease wiped it out", "Every plant was a copy... none could fight back.", C["copy2"], sub_color=(240, 225, 210))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 830, "WIPED OUT", t, C["wiped"], col=(255, 110, 90), size=90)
    impact(img, t, C["wiped"] + 0.2)


def s_candy(img, d, t):
    bokeh(img, t, 7, (255, 220, 160))
    camera(img, t, art_candy(t), (W / 2, 1450))
    finish(img, t, 7)
    tag(img, "SOME SAY...", t, (200, 60, 90))
    heading(img, t, "Banana candy = the OLD banana?", "That's why it tastes so different!", C["old"], colors={"OLD": YEL}, sub_color=(255, 230, 220))


def s_today(img, d, t):
    camera(img, t, art_today(t, C["enjoy"]), (W / 2, 1500))
    finish(img, t, 8)
    tag(img, "TODAY", t, (230, 60, 60))
    heading(img, t, "Scientists racing to save it", "A new disease is attacking the Cavendish.", 0.6, sub_color=(255, 230, 220))


def s_cta(img, d, t):
    text_block(img, "Learned something new?", F_MID, 330, t, delay=0.0)
    make_salt.draw_cta(img, d, W / 2, 1250, t, off=C["cta_off"])


base.TRANSITION = splat
SCENE_LIST = [
    (((70, 150, 255), (30, 60, 190)), s_hook),
    (((60, 45, 20), (18, 12, 5)), s_seeds),
    (((30, 55, 35), (8, 16, 10)), s_copies),
    (((40, 50, 70), (12, 15, 22)), s_store),
    (((60, 25, 55), (20, 8, 25)), s_grand),
    (((55, 40, 25), (15, 11, 6)), s_wipe),
    (((60, 25, 40), (18, 7, 12)), s_candy),
    (((35, 45, 60), (10, 13, 18)), s_today),
    (((30, 30, 40), (8, 8, 12)), s_cta),
]

if __name__ == "__main__":
    out, voice = sys.argv[1], sys.argv[2]
    tl = Timeline(voice)
    durs = tl.plan(["okay", "here's the|thing", "the bananas", "the crazy", "but in", "some say", "and today", "if you"], tail=2.4)
    # karaoke: hook words with their spoken times (spread evenly if recognition drops a word)
    s1 = "Every banana you've ever eaten is a clone.".split()
    s2 = "And they could disappear!".split()
    t_clone, t_and, t_end = tl.find("clone|clown"), tl.find("and", 1.0), tl.find("okay")
    t_dis = tl.find("disappear|disappeared|this", t_and)

    def word_times(words, t0, t1):
        """Exact recognized times when the word count matches, else spread evenly."""
        heard = [t for t, _ in tl.words if t0 - 0.05 <= t <= t1 + 0.05]
        if len(heard) == len(words):
            return list(zip(heard, words))
        return [(t0 + (t1 - t0) * i / (len(words) - 1), w) for i, w in enumerate(words)]
    HOOK_WORDS[:] = word_times(s1, tl.words[0][0], t_clone) + word_times(s2, t_and, t_dis)
    print("hook words:", [(round(t, 2), w) for t, w in HOOK_WORDS])
    C.update(split=len(s1), clone=t_clone - 0.12, **{"and": t_and}, disappear=t_dis,
             seedless=tl.cue("almost", 1), cuttings=tl.cue("growing", 1),
             sick=tl.cue("gets", 2) - 0.4, bigger=tl.cue("bigger", 4), wiped=tl.cue("wiped", 5), copy2=tl.cue("because", 5),
             old=tl.cue("tastes like|taste", 6), enjoy=tl.cue("so enjoy", 7), cta_off=tl.cue("like", 8) - 1.5)
    print("durations:", durs, "total:", round(sum(durs), 2))
    print("cues:", C)
    base.SCENES[:] = [(dd,) + sc for dd, sc in zip(durs, SCENE_LIST)]
    total, S = sum(durs), tl.starts
    events = [("whoosh", s) for s in S[1:]]
    events += [("thud", C["clone"] + 0.22)] + [("pop", C["clone"] + 0.1 + k * 0.09) for k in range(1, 9, 2)]
    events += [("whoosh", C["disappear"]), ("pop", C["disappear"] + 0.5), ("pop", S[1] + C["seedless"]),
               ("pop", S[2] + 0.2), ("thud", S[5] + C["wiped"] + 0.2), ("pop", S[7] + C["enjoy"]),
               ("click", S[8] + C["cta_off"] + 1.6), ("click", S[8] + C["cta_off"] + 3.6), ("ding", S[8] + C["cta_off"] + 3.65)]
    audio.music("music.wav", total)
    audio.sfx("sfx.wav", total, events)
    base.OUT = "base_banana.mp4"
    sys.argv = [sys.argv[0], "base_banana.mp4"]
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_banana.mp4", voice, "music.wav", "sfx.wav", out)
    print("wrote", out)
