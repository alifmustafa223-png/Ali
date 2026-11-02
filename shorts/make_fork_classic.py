"""YouTube Short #18 (classic ketchup-style version, as the user preferred): "Using a Fork Was Once a SIN?!"

New this time: live captions for the whole video (livecap.py, works on mute), an open-loop hook
("...and one princess paid for it with her life!"), and a loop ending whose last frame matches the
first so replays flow seamlessly. Plus the stop-the-scroll hook, sound design, all LESSONS.

Usage: python make_fork.py final.mp4 voice.mp3
"""
import math
import sys

from PIL import ImageDraw

import audio
import livecap
import make_ketchup
import make_salt
import make_short as base
from fx import impact, overlay
from make_banana import captions
from make_chocolate import VIGNETTE, dust, sparkle
from make_honey import slam
from make_ketchup import camera, face, splat, stamp
from make_lobster import frown_face
from make_pizza import back, bokeh
from make_short import F_MID, FONT_B, H, W, ease, font, person, tag, text_block
from style import fit_font, heading
from timing import Timeline

GOLD, SILVER, RED = (255, 200, 60), (215, 220, 230), (230, 60, 60)
make_ketchup.SPLAT_COLOR = GOLD
base.HOOK_SKIP = 0.0
C, HOOK_WORDS, CHUNKS, STARTS = {}, [], [], []


# ---------- drawings ----------

def fork(d, x, y, s, ang=0.0, prongs=2, col=GOLD, curve=0.0):
    """Fork pointing up; (x, y) is the middle of the handle."""
    c, sn = math.cos(ang), math.sin(ang)
    def r(px, py):
        return (x + (px * c - py * sn) * s, y + (px * sn + py * c) * s)
    d.polygon([r(-14, 180), r(14, 180), r(20, -60), r(-20, -60)], fill=col)
    d.ellipse([r(-22, 172)[0] - 4 * s, r(-22, 172)[1] - 10 * s, r(22, 172)[0] + 4 * s, r(22, 172)[1] + 16 * s], fill=col)
    d.polygon([r(-50, -60), r(50, -60), r(42, -110), r(-42, -110)], fill=col)
    for k in range(prongs):
        px = -40 + 80 * (k / (prongs - 1) if prongs > 1 else 0.5)
        bend = curve * 10 * (1 if k % 2 else -1)
        d.polygon([r(px - 8, -105), r(px + 8, -105), r(px + 4 + bend, -230), r(px - 4 + bend, -230)], fill=col)


def princess(d, x, y, s, t, sad=False):
    d.polygon([(x - 120 * s, y + 170 * s), (x + 120 * s, y + 170 * s), (x + 60 * s, y - 120 * s), (x - 60 * s, y - 120 * s)], fill=(150, 60, 160))  # gown
    hx, hy = x, y - 200 * s
    d.ellipse([hx - 75 * s, hy - 70 * s, hx + 75 * s, hy + 110 * s], fill=(120, 70, 40))  # long hair
    d.ellipse([hx - 60 * s, hy - 60 * s, hx + 60 * s, hy + 60 * s], fill=(235, 190, 150))
    d.polygon([(hx - 55 * s, hy - 55 * s), (hx - 55 * s, hy - 110 * s), (hx - 25 * s, hy - 80 * s), (hx, hy - 120 * s),
               (hx + 25 * s, hy - 80 * s), (hx + 55 * s, hy - 110 * s), (hx + 55 * s, hy - 55 * s)], fill=GOLD)  # crown
    if sad:
        frown_face(d, hx, hy, 1.0 * s)
    else:
        face(d, hx, hy, t, 1.0 * s, phase=0.6)


def bishop(d, x, y, s, t):
    person(d, x, y, s, (60, 40, 90))
    hx, hy = x, y - 200 * s
    d.polygon([(hx - 55 * s, hy - 50 * s), (hx + 55 * s, hy - 50 * s), (hx + 30 * s, hy - 170 * s), (hx, hy - 200 * s), (hx - 30 * s, hy - 170 * s)], fill=(240, 235, 220))  # mitre
    d.line([(hx, hy - 190 * s), (hx, hy - 60 * s)], fill=GOLD, width=max(2, int(8 * s)))
    frown_face(d, hx, hy, 1.0 * s)


def table(d, cx, y, w):
    d.rectangle([cx - w, y, cx + w, y + 34], fill=(120, 75, 45))
    d.rectangle([cx - w + 30, y + 34, cx - w + 60, y + 220], fill=(100, 60, 35))
    d.rectangle([cx + w - 60, y + 34, cx + w - 30, y + 220], fill=(100, 60, 35))


# ---------- hook ----------

def art_hook(t, cta=False):
    def draw(d):
        cx, cy = W / 2, 1400
        def rays(od):
            for k in range(16):
                a = t * 0.25 + k * math.pi / 8
                od.polygon([(cx, cy - 80), (cx + math.cos(a - 0.09) * 1400, cy - 80 + math.sin(a - 0.09) * 1400),
                            (cx + math.cos(a + 0.09) * 1400, cy - 80 + math.sin(a + 0.09) * 1400)], fill=(255, 255, 255, 38))
        overlay(d, rays)
        doom = 0.0 if cta else (ease((t - C["life"]) / 0.6) if t > C["life"] else 0.0)
        princess(d, cx - 170, cy + 200, 1.6, t, sad=doom > 0.5)
        fork(d, cx + 230, cy - 20 + math.sin(t * 2.4) * 16, 2.0, ang=0.25 + 0.05 * math.sin(t * 2), prongs=2)
        for k in range(5):
            ph = (t * 0.9 + k * 0.2) % 1
            sparkle(d, cx + 230 + math.cos(k * 1.26 + t) * 170, cy - 220 + math.sin(k * 1.26 + t) * 160, 14 * math.sin(ph * math.pi) + 2)
        if doom > 0:  # open loop: a big "?!" — how did she pay with her life?
            p = back((t - C["life"]) / 0.35)
            f = font(FONT_B, max(10, int(240 * p)))
            tw = d.textlength("?!", font=f)
            d.text((cx + 20 - tw / 2 + 8, 880 + 8), "?!", font=f, fill=(60, 10, 20))
            d.text((cx + 20 - tw / 2, 880), "?!", font=f, fill=(255, 225, 90))
    return draw


def s_hook(img, d, t):
    bokeh(img, t, 1, (255, 200, 180))
    camera(img, t + 0.5, art_hook(t), (W / 2, 1400))
    finish(img, t, 1)
    dd = ImageDraw.Draw(img, "RGBA")
    top = fit_font("Using a fork was once", F_MID)
    tw = dd.textlength("Using a fork was once", font=top)
    dd.text(((W - tw) / 2 + 4, 385), "Using a fork was once", font=top, fill=(0, 0, 0, 140))
    dd.text(((W - tw) / 2, 380), "Using a fork was once", font=top, fill=(255, 255, 255))
    slam(img, "A SIN!", 500, t, C["sin"], (255, 120, 100), 150)
    impact(img, t, C["sin"] + 0.22)


# ---------- story ----------

def art_venice(t, fork_at):
    def draw(d):
        cx, cy = W / 2, 1500
        for k in range(5):  # Venetian houses on a canal
            x0 = k * 216
            h = 300 + (k * 71) % 140
            d.rectangle([x0, 1200 - h, x0 + 216, 1200], fill=[(220, 150, 110), (240, 200, 140), (200, 110, 90), (230, 180, 150), (210, 140, 100)][k])
            for wx in range(2):
                d.chord([x0 + 40 + wx * 90, 1120 - h + 40, x0 + 100 + wx * 90, 1120 - h + 160], 180, 360, fill=(70, 50, 40))
                d.rectangle([x0 + 40 + wx * 90, 1120 - h + 100, x0 + 100 + wx * 90, 1120 - h + 170], fill=(70, 50, 40))
        d.rectangle([0, 1200, W, 1290], fill=(60, 120, 150))
        for k in range(3):
            d.line([(j * 40, 1225 + k * 22 + math.sin(j * 0.6 + t * 3 + k) * 5) for j in range(30)], fill=(110, 170, 200), width=4)
        table(d, cx + 40, cy + 120, 300)
        d.ellipse([cx - 60, cy + 70, cx + 140, cy + 125], fill=(245, 245, 250))
        princess(d, cx - 280, cy + 230, 1.15, t)
        p = back((t - fork_at) / 0.35)
        if p > 0:
            fork(d, cx + 200, cy - 60, 1.0 * p, ang=0.5 + 0.15 * math.sin(t * 3))
            for k in range(4):
                ph = (t * 1.0 + k * 0.25) % 1
                sparkle(d, cx + 200 + math.cos(k * 1.6 + t) * 120, cy - 120 + math.sin(k * 1.6 + t) * 100, 12 * math.sin(ph * math.pi) + 2)
    return draw


def art_shocked(t, sinful_at):
    def draw(d):
        cx, cy = W / 2, 1520
        table(d, cx, cy + 100, 460)
        for k, x in enumerate((cx - 330, cx - 110, cx + 110)):  # diners eating with their hands
            person(d, x, cy + 120, 0.9, [(90, 110, 70), (120, 70, 60), (70, 90, 130)][k])
            hx, hy = x, cy + 120 - 0.9 * 200
            for ex in (-16, 16):
                d.ellipse([hx + ex - 10, hy - 14, hx + ex + 10, hy + 6], fill=(255, 255, 255))
                d.ellipse([hx + ex - 4, hy - 8, hx + ex + 4, hy + 0], fill=(40, 25, 20))
            d.ellipse([hx - 12, hy + 18, hx + 12, hy + 42], fill=(90, 40, 30))  # gasp
            bob = math.sin(t * 5 + k) * 10
            d.ellipse([x + 50, cy + 30 + bob, x + 90, cy + 70 + bob], fill=(220, 175, 135))  # hand holding food
            d.ellipse([x + 60, cy + 10 + bob, x + 100, cy + 40 + bob], fill=(200, 140, 70))
        bishop(d, cx + 340, cy + 150, 1.2, t)
        wag = math.sin(t * 7) * 0.35
        d.line([(cx + 290, cy + 0), (cx + 290 + math.cos(-2.2 + wag) * 120, cy + math.sin(-2.2 + wag) * 120)], fill=(220, 175, 135), width=22)
    return draw


def art_candle(t, out_at):
    def draw(d):
        cx, cy = W / 2, 1480
        d.rounded_rectangle([cx - 230, cy - 420, cx + 230, cy + 60], radius=20, fill=(120, 85, 40))  # portrait frame
        d.rectangle([cx - 200, cy - 390, cx + 200, cy + 30], fill=(60, 40, 50))
        princess(d, cx, cy + 30, 0.95, t, sad=True)
        d.rectangle([cx + 300, cy + 60, cx + 360, cy + 300], fill=(245, 240, 230))  # candle
        if t < out_at:
            fl = 1 + 0.15 * math.sin(t * 11)
            d.ellipse([cx + 310, cy - 40 * fl, cx + 350, cy + 60], fill=(255, 200, 80))
        else:
            q = (t - out_at)
            def smoke(od):
                for k in range(5):
                    ph = (q * 0.6 + k * 0.2) % 1
                    r = 14 + ph * 40
                    od.ellipse([cx + 330 - r + math.sin(ph * 6 + k) * 20, cy + 40 - ph * 380 - r, cx + 330 + r + math.sin(ph * 6 + k) * 20, cy + 40 - ph * 380 + r], fill=(200, 200, 210, int(150 * (1 - ph))))
            overlay(d, smoke)
    return draw


def art_mocked(t, mock_at):
    def draw(d):
        cx, cy = W / 2, 1520
        person(d, cx - 40, cy + 200, 1.3, (60, 80, 60))  # the traveler, proudly holding his fork
        hx, hy = cx - 40, cy + 200 - 1.3 * 200
        d.rectangle([hx - 80, hy - 75, hx + 80, hy - 60], fill=(40, 40, 40))
        d.rectangle([hx - 50, hy - 140, hx + 50, hy - 70], fill=(40, 40, 40))
        face(d, hx, hy, t, 1.2)
        fork(d, cx + 110, cy - 10, 0.7, ang=0.3, col=SILVER)
        d.rounded_rectangle([cx - 230, cy + 40, cx - 120, cy + 140], radius=16, fill=(140, 90, 50))  # travel bag
        if t > mock_at:  # laughing crowd pops in around him
            for k, (x, sh) in enumerate(((cx - 360, (150, 80, 80)), (cx + 330, (80, 100, 150)))):
                p = back((t - mock_at - k * 0.2) / 0.35)
                if p <= 0:
                    continue
                person(d, x, cy + 230, 1.0 * p, sh)
                fx, fy = x, cy + 230 - 200 * p
                d.arc([fx - 22 * p, fy - 18 * p, fx - 4 * p, fy - 2 * p], 200, 340, fill=(40, 25, 20), width=5)
                d.arc([fx + 4 * p, fy - 18 * p, fx + 22 * p, fy - 2 * p], 200, 340, fill=(40, 25, 20), width=5)
                d.chord([fx - 26 * p, fy + 6 * p, fx + 26 * p, fy + 44 * p], 0, 180, fill=(90, 40, 30))
                bob = abs(math.sin(t * 9 + k)) * 14
                d.text((x - 60, cy - 160 - bob), "HA!", font=font(FONT_B, 54), fill=(255, 230, 140))
    return draw


def art_prongs(t, four_at):
    def draw(d):
        cx, cy = W / 2, 1500
        u = ease((t - four_at) / 0.7) if t > four_at else 0.0
        fork(d, cx - 230, cy, 1.5, ang=-0.1, prongs=2, col=SILVER)
        if u > 0:
            fork(d, cx + 230, cy, 1.5 * back(min(1.0, (t - four_at) / 0.35)), ang=0.1, prongs=4, col=SILVER, curve=u)
        f = font(FONT_B, 70)
        for x, lab, show in ((cx - 230, "2", True), (cx + 230, "4", u > 0)):
            if show:
                tw = d.textlength(lab, font=f)
                d.ellipse([x - 55, cy + 260, x + 55, cy + 370], fill=(40, 30, 50))
                d.text((x - tw / 2, cy + 272), lab, font=f, fill=(255, 225, 90))
        if u > 0:
            d.polygon([(cx - 60, cy - 20), (cx + 40, cy - 20), (cx + 40, cy - 50), (cx + 100, cy + 10), (cx + 40, cy + 70), (cx + 40, cy + 40), (cx - 60, cy + 40)], fill=(255, 225, 90))
    return draw


def art_today(t):
    def draw(d):
        cx, cy = W / 2, 1500
        fork(d, cx - 280, cy - 40, 1.2, ang=-0.2, prongs=4, col=SILVER, curve=1.0)
        d.ellipse([cx - 140, cy + 60, cx + 420, cy + 250], fill=(230, 200, 140))  # bread
        for k in range(8):
            d.ellipse([cx - 60 + (k * 61) % 420, cy + 110 + (k * 37) % 90, cx - 40 + (k * 61) % 420, cy + 126 + (k * 37) % 90], fill=(190, 140, 80))
        tear = math.sin(t * 2.5) * 20  # hand lifting a torn piece of bread
        hx, hy = cx + 230, cy - 60 + tear
        d.ellipse([hx - 70, hy - 50, hx + 70, hy + 70], fill=(220, 175, 135))  # palm
        for k in range(4):  # fingers curled over the bread
            fx = hx - 54 + k * 36
            d.rounded_rectangle([fx - 16, hy - 110, fx + 16, hy - 20], radius=16, fill=(220, 175, 135))
        d.rounded_rectangle([hx - 120, hy - 30, hx - 60, hy + 10], radius=18, fill=(220, 175, 135))  # thumb
        d.ellipse([hx - 60, hy - 150, hx + 60, hy - 90], fill=(230, 200, 140))  # bread piece
        d.rectangle([hx - 40, hy + 60, hx + 40, hy + 160], fill=(220, 175, 135))  # wrist
        for k in range(5):
            ph = (t * 0.8 + k * 0.2) % 1
            sparkle(d, cx + math.cos(k * 1.26 + t) * 360, cy - 200 + math.sin(k * 1.26 + t) * 150, 12 * math.sin(ph * math.pi) + 2)
    return draw


# ---------- scenes ----------

def finish(img, t, seed):
    dust(img, t, seed)
    img.alpha_composite(VIGNETTE)


def s_venice(img, d, t):
    camera(img, t, art_venice(t, C["fork"]), (W / 2, 1450))
    finish(img, t, 2)
    tag(img, "VENICE · 1,000 YEARS AGO", t, (60, 110, 160))
    heading(img, t, "A golden fork at dinner", "A Byzantine princess used one in Venice.", C["fork"], colors={"GOLDEN": GOLD}, sub_color=(220, 235, 250))


def s_shocked(img, d, t):
    bokeh(img, t, 3, (255, 220, 200))
    camera(img, t, art_shocked(t, C["sinful"]), (W / 2, 1450))
    finish(img, t, 3)
    tag(img, "SCANDAL!", t, (180, 50, 60))
    heading(img, t, "Everyone ate with hands", "A church leader called her fork a sinful luxury.", C["church"], sub_color=(255, 225, 225))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 820, "SINFUL!", t, C["sinful"], col=(255, 110, 100), size=90)
    impact(img, t, C["sinful"] + 0.2)


def s_candle(img, d, t):
    camera(img, t, art_candle(t, C["died"]), (W / 2, 1450))
    finish(img, t, 4)
    tag(img, "THE STORY GOES...", t, (90, 70, 110))
    heading(img, t, "Punished for a fork?", "When she died, some said it was her punishment.", 0.6, sub_color=(235, 225, 245))


def s_mocked(img, d, t):
    bokeh(img, t, 5, (255, 220, 230))
    camera(img, t, art_mocked(t, C["mocked"]), (W / 2, 1450))
    finish(img, t, 5)
    tag(img, "THE CRAZY PART · 1611", t, (170, 60, 110))
    heading(img, t, "Laughed at for a fork!", "In 1611, an English traveler was mocked for one.", C["sixteen"], sub_color=(255, 225, 240))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 820, "MOCKED!", t, C["mocked"] + 0.3, col=(255, 150, 170), size=90)
    impact(img, t, C["mocked"] + 0.5)


def s_prongs(img, d, t):
    bokeh(img, t, 6, (220, 230, 255))
    camera(img, t, art_prongs(t, C["four"]), (W / 2, 1450))
    finish(img, t, 6)
    tag(img, "EARLY FORKS", t, (80, 90, 140))
    heading(img, t, "2 prongs... then 4", "The curved four-prong fork came much later.", C["four"], sub_color=(220, 230, 250))


def s_today(img, d, t):
    bokeh(img, t, 7, (255, 225, 190))
    camera(img, t, art_today(t), (W / 2, 1450))
    finish(img, t, 7)
    tag(img, "TODAY", t, (230, 60, 60))
    heading(img, t, "Fork... or bread and hands?", "Many of us still love eating with bread and our hands.", C["many"], sub_color=(255, 235, 215))


def s_cta(img, d, t):
    """Loop ending: same bright scene as the hook, so the replay flows straight into frame 0."""
    text_block(img, "Learned something new?", F_MID, 330, t, delay=0.0)
    make_salt.draw_cta(img, d, W / 2, 1250, t, off=C["cta_off"])
    return
    fade = 1 - ease((t - (C["cta_dur"] - 1.1)) / 0.5)  # buttons leave for the last second -> clean loop frame
    if fade > 0:
        from PIL import Image
        panel = Image.new("RGBA", img.size, (0, 0, 0, 0))
        pd = ImageDraw.Draw(panel, "RGBA")
        pd.rounded_rectangle([140, 380, W - 140, 1220], radius=60, fill=(20, 10, 30, int(240 * fade)))
        make_salt.draw_cta(panel, pd, W / 2, 900, t, off=C["cta_off"])
        if fade < 1:
            panel.putalpha(panel.getchannel("A").point(lambda v: int(v * fade)))
        img.alpha_composite(panel)


def with_captions(i, fn):
    def scene(img, d, t):
        fn(img, d, t)
        if False:
            livecap.draw(img, STARTS[i] + t, CHUNKS, y=600 if i < 7 else 230)
    return scene


base.TRANSITION = splat
SCENE_LIST = [
    (((60, 20, 25), (15, 5, 7)), s_hook),
    (((50, 80, 120), (15, 25, 40)), s_venice),
    (((60, 25, 40), (18, 7, 12)), s_shocked),
    (((40, 30, 50), (10, 8, 14)), s_candle),
    (((60, 25, 55), (20, 8, 25)), s_mocked),
    (((35, 40, 60), (10, 12, 18)), s_prongs),
    (((60, 40, 20), (16, 10, 5)), s_today),
    (((30, 30, 40), (8, 8, 12)), s_cta),
]

if __name__ == "__main__":
    out, voice = sys.argv[1], sys.argv[2]
    tl = Timeline(voice)
    anchors = ["okay", "people were", "when she", "the crazy", "early", "and today", "if you"]
    cues = ["sin", "and one", "life", "golden", "sinful", "died", "mocked", "prongs", "headlight|like", "church", "sixteen", "many"]
    missing = tl.check(anchors + cues)
    if missing:
        print("words:", " ".join(f"{t:.1f}:{w}" for t, w in tl.words))
        sys.exit(f"missing anchors/cues: {missing}")
    durs = tl.plan(anchors, tail=2.0)
    STARTS[:] = tl.starts
    s1 = "Using a fork was once called a sin.".split()
    s2 = "And one princess paid for it with her life!".split()
    t_sin, t_and = tl.find("sin"), tl.find("and one")
    t_life = tl.find("life", t_and)

    def word_times(words, t0, t1):
        heard = [t for t, _ in tl.words if t0 - 0.05 <= t <= t1 + 0.05]
        if len(heard) == len(words):
            return list(zip(heard, words))
        return [(t0 + (t1 - t0) * i / (len(words) - 1), w) for i, w in enumerate(words)]
    HOOK_WORDS[:] = word_times(s1, tl.words[0][0], t_sin) + word_times(s2, t_and, t_life)
    script = open("fork_script.txt").read().split("\n\n")
    scene_texts = ["", script[1], script[2].split(" When she")[0], "When she" + script[2].split(" When she")[1],
                   script[3], script[4], script[5], script[6]]
    CHUNKS[:] = livecap.build(tl, scene_texts)
    C.update(split=len(s1), sin=t_sin - 0.12, life=t_life, **{"and": t_and},
             fork=tl.cue("golden", 1), sinful=tl.cue("sinful", 2), died=tl.cue("died", 3),
             mocked=tl.cue("mocked", 4), church=tl.cue("church", 2), sixteen=tl.cue("sixteen", 4), many=tl.cue("many", 6), four=tl.cue("prongs", 5) - 0.3, cta_off=tl.cue("headlight|like", 7) + 0.3 - 1.5)
    C["cta_dur"] = durs[7]
    print("hook words:", [(round(t, 2), w) for t, w in HOOK_WORDS])
    print("durations:", durs, "total:", round(sum(durs), 2))
    print("cues:", C)
    print("caption chunks:", len(CHUNKS))
    base.SCENES[:] = [(dd, sc[0], with_captions(i, sc[1])) for i, (dd, sc) in enumerate(zip(durs, SCENE_LIST))]
    total, S = sum(durs), tl.starts
    events = [("whoosh", s) for s in S[1:]]
    events += [("thud", C["sin"] + 0.22), ("pop", C["life"]), ("pop", S[1] + C["fork"]), ("thud", S[2] + C["sinful"] + 0.2),
               ("whoosh", S[3] + C["died"]), ("pop", S[4] + C["mocked"]), ("thud", S[4] + C["mocked"] + 0.5),
               ("pop", S[5] + C["four"]),
               ("click", S[7] + C["cta_off"] + 1.6), ("click", S[7] + C["cta_off"] + 3.6), ("ding", S[7] + C["cta_off"] + 3.65)]
    audio.music("music.wav", total)
    audio.sfx("sfx.wav", total, events)
    base.OUT = "base_fork_classic.mp4"
    sys.argv = [sys.argv[0], "base_fork_classic.mp4"]
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_fork_classic.mp4", voice, "music.wav", "sfx.wav", out)
    print("wrote", out)
