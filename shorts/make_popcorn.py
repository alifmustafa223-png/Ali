"""YouTube Short #15: "Movie Theaters Once BANNED Popcorn?!"

Ketchup-video animation style + strong hook + automatic timing. New this time: full sound design
(audio.py: music with ducking, whoosh/thud/pop/click/ding effects, -14 LUFS mastering).

Usage: python make_popcorn.py final.mp4 voice.mp3
"""
import math
import sys

from PIL import ImageDraw

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
from make_short import F_MID, H, W, ease, font, FONT_B, person, tag, text_block
from style import fit_font, heading
from timing import Timeline

CREAM, CREAM_DARK, BUTTER = (255, 248, 225), (235, 215, 160), (255, 210, 80)
RED, GOLD = (215, 45, 45), (255, 195, 60)
make_ketchup.SPLAT_COLOR = (250, 230, 170)
base.HOOK_SKIP = 0.0
C = {}


# ---------- drawings ----------

def kernel(d, x, y, s, k=0):
    for j, (dx, dy, r) in enumerate(((0, 0, 26), (-20, -14, 20), (20, -12, 21), (-6, 18, 18), (16, 14, 17))):
        d.ellipse([x + (dx - r) * s, y + (dy - r) * s, x + (dx + r) * s, y + (dy + r) * s], fill=CREAM if (j + k) % 3 else CREAM_DARK)
    d.ellipse([x - 7 * s, y - 4 * s, x + 7 * s, y + 8 * s], fill=BUTTER)


def bucket(d, cx, by, s, t, overflow=True):
    """Striped popcorn bucket; by = bottom."""
    w0, w1, h = 150 * s, 200 * s, 330 * s
    for k in range(6):
        xa = cx - w0 + 2 * w0 * k / 6
        xb = cx - w0 + 2 * w0 * (k + 1) / 6
        xa2 = cx - w1 + 2 * w1 * k / 6
        xb2 = cx - w1 + 2 * w1 * (k + 1) / 6
        d.polygon([(xa, by), (xb, by), (xb2, by - h), (xa2, by - h)], fill=RED if k % 2 == 0 else (250, 250, 250))
    if overflow:
        for k in range(14):
            x = cx - w1 + 30 * s + (k * 53) % int(2 * w1 - 60 * s)
            y = by - h - 20 * s - (k * 37) % int(80 * s + 1) + math.sin(t * 3 + k) * 4 * s
            kernel(d, x, y, s * 1.1, k)


def coin(d, x, y, r):
    d.ellipse([x - r, y - r, x + r, y + r], fill=GOLD, outline=(200, 145, 30), width=max(2, int(r * 0.12)))


def bill(d, x, y, s, ang):
    c, sn = math.cos(ang), math.sin(ang)
    pts = [(-70, -36), (70, -36), (70, 36), (-70, 36)]
    d.polygon([(x + (px * c - py * sn) * s, y + (px * sn + py * c) * s) for px, py in pts], fill=(110, 180, 100))
    d.ellipse([x - 18 * s, y - 18 * s, x + 18 * s, y + 18 * s], fill=(80, 150, 75))


def screen_and_curtains(d, t, top=900, bottom=1500):
    d.rectangle([140, top, W - 140, bottom - 140], fill=(225, 235, 245))
    flick = 0.9 + 0.1 * math.sin(t * 20)
    d.rectangle([170, top + 30, W - 170, bottom - 170], fill=(int(160 * flick), int(190 * flick), int(220 * flick)))
    for side in (-1, 1):  # red curtains with folds
        x0 = 0 if side < 0 else W - 190
        d.rectangle([x0, top - 40, x0 + 190, bottom - 60], fill=(170, 30, 40))
        for k in range(4):
            d.line([(x0 + 25 + k * 45, top - 40), (x0 + 25 + k * 45, bottom - 60)], fill=(130, 20, 30), width=10)
    d.rectangle([0, top - 80, W, top - 30], fill=(150, 25, 35))


def seats(d, y, n=7, col=(40, 30, 45)):
    for k in range(n):
        x = 80 + k * (W - 160) / (n - 1)
        d.rounded_rectangle([x - 62, y - 70, x + 62, y + 40], radius=26, fill=col)


# ---------- illustrations ----------

def art_hook(t):
    def draw(d):
        screen_and_curtains(d, t)
        seats(d, 1780)
        cx, by = W / 2, 1700
        bucket(d, cx, by, 1.0, t)
        money = t >= C["money"]
        if not money:  # NO sign over the bucket
            r = 230
            d.ellipse([cx - r, by - 420, cx + r, by + 40], outline=(230, 40, 40), width=30)
            d.line([(cx - 160, by - 350), (cx + 160, by - 30)], fill=(230, 40, 40), width=30)
        else:  # second beat: money bursts out of the bucket
            q = (t - C["money"])
            for k in range(10):
                ph = min(1.0, q * 1.2 + (k % 3) * 0.1)
                ang = -math.pi / 2 + (k - 4.5) * 0.28
                x = cx + math.cos(ang) * 420 * ph
                y = by - 380 + math.sin(ang) * 300 * ph + 260 * ph * ph
                if k % 2:
                    bill(d, x, y, 0.9, ang + q * 3)
                else:
                    coin(d, x, y, 30)
    return draw


def art_peru(t, reveal_at):
    def draw(d):
        cx, cy = W / 2, 1500
        d.rectangle([0, cy - 40, W, H], fill=(150, 110, 70))
        for k in range(6):  # soil layers
            d.line([(0, cy + 40 + k * 70), (W, cy + 30 + k * 70)], fill=(130, 95, 60), width=8)
        person(d, cx - 280, cy + 60, 1.2, (170, 150, 110))
        d.rectangle([cx - 380, cy - 220, cx - 180, cy - 200], fill=(150, 120, 80))  # sun hat
        d.chord([cx - 345, cy - 300, cx - 215, cy - 180], 180, 360, fill=(150, 120, 80))
        face(d, cx - 280, cy + 60 - 1.2 * 200, t, 1.1)
        brush = math.sin(t * 9) * 30  # brushing the dirt
        d.line([(cx - 190, cy - 40), (cx + 40 + brush, cy + 70)], fill=(225, 175, 135), width=30)
        d.rounded_rectangle([cx + 20 + brush, cy + 50, cx + 110 + brush, cy + 90], radius=10, fill=(160, 110, 60))
        p = ease((t - reveal_at) / 1.0)
        for k in range(5):  # ancient kernels revealed
            x, y = cx + 160 + (k % 3) * 90, cy + 140 + (k // 3) * 80
            kernel(d, x, y, 0.75 * max(0.05, p), k)
        if p > 0.9:
            for k in range(5):
                ph = (t * 0.9 + k * 0.2) % 1
                sparkle(d, cx + 250 + math.cos(k * 1.26 + t) * 200, cy + 170 + math.sin(k * 1.26 + t) * 120, 12 * math.sin(ph * math.pi) + 2)
    return draw


def art_fancy(t, mess_at, noise_at):
    def draw(d):
        cx, cy = W / 2, 1500
        d.polygon([(cx - 220, H), (cx + 220, H), (cx + 120, cy - 120), (cx - 120, cy - 120)], fill=(170, 30, 40))  # red carpet
        for k in range(2):  # chandelier
            d.line([(cx, 860), (cx, 960)], fill=(200, 170, 90), width=6)
        d.chord([cx - 150, 900, cx + 150, 1060], 0, 180, fill=(230, 195, 90))
        for k in range(5):
            x = cx - 120 + k * 60
            d.ellipse([x - 12, 1040, x + 12, 1064], fill=(255, 240, 180))
        person(d, cx - 280, cy + 200, 1.35, (30, 30, 40))  # manager in a suit
        by = cy + 200 - 1.35 * 120  # bow tie at the collar, below the chin
        d.polygon([(cx - 330, by - 22), (cx - 330, by + 22), (cx - 280, by)], fill=(200, 40, 40))
        d.polygon([(cx - 230, by - 22), (cx - 230, by + 22), (cx - 280, by)], fill=(200, 40, 40))
        frown_face(d, cx - 280, cy + 200 - 1.35 * 200, 1.25)
        if t > mess_at:  # popcorn spilling onto the carpet
            q = t - mess_at
            for k in range(12):
                ph = min(1.0, q * 0.9 + (k % 4) * 0.08)
                x = cx + 80 + (k * 47) % 260 - 60 + ph * (k % 5 - 2) * 40
                y = cy - 200 + ph * (380 + (k * 31) % 140)
                kernel(d, x, y, 0.55, k)
        if t > noise_at:  # "CRUNCH" noise lines
            f = font(FONT_B, 56)
            a = int(255 * min(1, (t - noise_at) * 3))
            d.text((cx + 170, cy - 380), "CRUNCH!", font=f, fill=(255, 220, 120, a))
            for k in range(3):
                ang = -0.6 + k * 0.4
                d.line([(cx + 140 + math.cos(ang) * 30, cy - 280 + math.sin(ang) * 30), (cx + 140 + math.cos(ang) * 80, cy - 280 + math.sin(ang) * 80)], fill=(255, 220, 120, a), width=8)
    return draw


def art_coatcheck(t, hang_at):
    def draw(d):
        cx, cy = W / 2, 1500
        d.rectangle([60, cy + 120, W - 60, cy + 180], fill=(120, 80, 50))  # counter
        d.rectangle([60, cy + 180, W - 60, H], fill=(95, 62, 38))
        d.rectangle([90, 930, W - 90, 950], fill=(160, 160, 170))  # rail
        for k in range(3):  # coats on hangers
            x = 210 + k * 170
            d.polygon([(x, 950), (x - 60, 990), (x + 60, 990)], fill=(160, 160, 170))
            d.rounded_rectangle([x - 70, 985, x + 70, 1220], radius=30, fill=[(90, 60, 50), (60, 70, 100), (120, 50, 60)][k])
        p = back((t - hang_at) / 0.4)
        if p > 0:  # popcorn bucket hanging like a coat, with a ticket
            x = 760
            sw = math.sin(t * 3) * 0.06
            d.polygon([(x, 950), (x - 60, 990), (x + 60, 990)], fill=(160, 160, 170))
            bucket(d, x + sw * 100, 1240, 0.7 * p, t)
            d.rounded_rectangle([x + 90, 1080, x + 190, 1150], radius=10, fill=(250, 240, 200))
            d.text((x + 108, 1088), "#7", font=font(FONT_B, 44), fill=(150, 60, 40))
        person(d, cx - 220, cy + 150, 1.1, (160, 40, 50))  # attendant
        face(d, cx - 220, cy + 150 - 1.1 * 200, t, 1.0, phase=0.8)
    return draw


def art_vendor(t, cents_at):
    def draw(d):
        cx, cy = W / 2, 1500
        d.rectangle([60, 860, W - 60, 1000], fill=(60, 50, 70))  # theater marquee
        for k in range(14):
            on = (int(t * 6) + k) % 2
            d.ellipse([90 + k * 66, 870, 110 + k * 66, 890], fill=(255, 220, 120) if on else (120, 100, 60))
            d.ellipse([90 + k * 66, 970, 110 + k * 66, 990], fill=(255, 220, 120) if not on else (120, 100, 60))
        d.text((cx - 175, 900), "NOW SHOWING", font=font(FONT_B, 54), fill=(255, 230, 150))
        d.rectangle([0, cy + 200, W, H], fill=(90, 90, 100))  # sidewalk
        mx, my = cx + 150, cy  # popcorn cart with a glass case full of popping kernels
        d.rectangle([mx - 190, my - 40, mx + 190, my + 200], fill=(200, 50, 50))
        for wx in (mx - 130, mx + 130):
            d.ellipse([wx - 45, my + 170, wx + 45, my + 260], fill=(40, 40, 45))
        d.rectangle([mx - 160, my - 330, mx + 160, my - 40], fill=(230, 240, 250, 150))
        for k in range(16):
            ph = (t * 0.8 + k / 16) % 1
            x = mx - 130 + (k * 41) % 260
            y = my - 60 - math.sin(ph * math.pi) * 240
            kernel(d, x, y, 0.45, k)
        d.rectangle([mx - 175, my - 350, mx + 175, my - 320], fill=(180, 40, 40))
        person(d, cx - 260, cy + 150, 1.15, (200, 200, 190))  # vendor in apron
        face(d, cx - 260, cy + 150 - 1.15 * 200, t, 1.05, phase=0.3)
        if t > cents_at:  # coins rain in = "made a fortune"
            for k in range(8):
                ph = ((t - cents_at) * 0.7 + k * 0.125) % 1
                coin(d, cx - 420 + k * 115, 1060 + ph * 330, 24)
            f = font(FONT_B, 70)
            d.rounded_rectangle([cx - 470, 1060, cx - 290, 1150], radius=20, fill=(30, 25, 20))
            d.text((cx - 445, 1066), "5¢", font=f, fill=GOLD)
    return draw


def art_stand(t, saved_at):
    def draw(d):
        cx, cy = W / 2, 1500
        d.rectangle([80, cy - 80, W - 80, cy + 260], fill=(150, 40, 45))  # concession counter
        d.rectangle([80, cy - 110, W - 80, cy - 80], fill=(230, 195, 90))
        d.text((cx - 175, 930), "CONCESSIONS", font=font(FONT_B, 58), fill=(255, 225, 140))
        for k in range(3):
            bucket(d, cx - 280 + k * 280, cy - 110, 0.62, t + k)
        if t > saved_at:  # money bag pops onto the counter
            p = back((t - saved_at) / 0.35)
            x, y = cx + 360, cy - 210
            d.ellipse([x - 90 * p, y - 80 * p, x + 90 * p, y + 100 * p], fill=(200, 170, 110))
            d.polygon([(x - 40 * p, y - 70 * p), (x + 40 * p, y - 70 * p), (x, y - 120 * p)], fill=(180, 150, 95))
            d.text((x - 25 * p, y - 40 * p), "$", font=font(FONT_B, max(10, int(90 * p))), fill=(70, 120, 60))
    return draw


def art_war(t, ration_at, boom_at):
    def draw(d):
        cx, cy = W / 2, 1500
        jx = cx - 230  # candy jar emptying
        d.rounded_rectangle([jx - 150, cy - 300, jx + 150, cy + 150], radius=60, fill=(225, 235, 245, 140))
        d.rectangle([jx - 120, cy - 340, jx + 120, cy - 290], fill=(150, 90, 60))
        left = max(0.0, 1 - ease((t - ration_at) / 1.2))
        for k in range(int(12 * left)):
            x = jx - 100 + (k * 37) % 200
            y = cy + 110 - (k // 4) * 60
            d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=[(240, 80, 120), (90, 170, 240), (250, 200, 60)][k % 3])
        if t > boom_at:  # popcorn explodes upward from a bucket
            bucket(d, cx + 230, cy + 150, 0.85, t)
            q = t - boom_at
            for k in range(18):
                ph = (q * 0.8 + k / 18) % 1
                ang = -math.pi / 2 + (k - 9) * 0.12
                x = cx + 230 + math.cos(ang) * 380 * ph
                y = cy - 160 + math.sin(ang) * 520 * ph + 400 * ph * ph
                kernel(d, x, y, 0.55, k)
    return draw


def art_king(t):
    def draw(d):
        cx = W / 2
        bucket(d, cx, 1820, 1.5, t)
        bob = math.sin(t * 2) * 12
        y = 1080 + bob
        d.polygon([(cx - 170, y + 110), (cx - 170, y - 20), (cx - 85, y + 40), (cx, y - 70), (cx + 85, y + 40), (cx + 170, y - 20), (cx + 170, y + 110)], fill=GOLD)
        for x in (cx - 100, cx, cx + 100):
            d.ellipse([x - 18, y + 60, x + 18, y + 96], fill=(220, 50, 70))
        for k in range(7):
            ph = (t * 0.8 + k * 0.143) % 1
            sparkle(d, cx + math.cos(k * 0.9 + t) * 360, 1350 + math.sin(k * 1.7 + t) * 300, 14 * math.sin(ph * math.pi) + 2)
    return draw


# ---------- scenes ----------

def finish(img, t, seed):
    dust(img, t, seed)
    img.alpha_composite(VIGNETTE)


def s_hook(img, d, t):
    camera(img, t + 0.5, art_hook(t), (W / 2, 1450))
    finish(img, t, 1)
    dd = ImageDraw.Draw(img, "RGBA")
    top = fit_font("Movie theaters once", F_MID)
    tw = dd.textlength("Movie theaters once", font=top)
    dd.text(((W - tw) / 2 + 4, 385), "Movie theaters once", font=top, fill=(0, 0, 0, 140))
    dd.text(((W - tw) / 2, 380), "Movie theaters once", font=top, fill=(255, 255, 255))
    slam(img, "BANNED POPCORN", 500, t, C["slam"], (255, 90, 80), 100)
    impact(img, t, C["slam"] + 0.22)


def s_peru(img, d, t):
    bokeh(img, t, 2, (255, 230, 180))
    camera(img, t, art_peru(t, C["reveal"]), (W / 2, 1450))
    finish(img, t, 2)
    tag(img, "6,000+ YEARS AGO · PERU", t, (170, 110, 50))
    heading(img, t, "Popcorn is ancient!", "Popped corn over 6,000 years old was found in Peru.", C["reveal"], sub_color=(255, 235, 210))


def s_fancy(img, d, t):
    camera(img, t, art_fancy(t, C["messy"], C["noisy"]), (W / 2, 1450))
    finish(img, t, 3)
    tag(img, "THE 1920s", t, (170, 40, 50))
    heading(img, t, "Fancy theaters said NO", "Popcorn was messy... and noisy.", C["messy"], colors={"NO": (255, 100, 90)}, sub_color=(255, 225, 225))


def s_coat(img, d, t):
    bokeh(img, t, 4, (255, 230, 190))
    camera(img, t, art_coatcheck(t, C["hang"]), (W / 2, 1450))
    finish(img, t, 4)
    tag(img, "NO SNACKS INSIDE", t, (90, 70, 120))
    heading(img, t, "Check your popcorn here!", "Like a coat!", C["hang"] + 0.6, sub_color=(235, 225, 250))


def s_vendor(img, d, t):
    camera(img, t, art_vendor(t, C["cents"]), (W / 2, 1450))
    finish(img, t, 5)
    tag(img, "THE GREAT DEPRESSION", t, (90, 90, 110))
    heading(img, t, "Popcorn for pennies", "Street sellers made a fortune outside.", C["fortune"], sub_color=(230, 230, 240))


def s_stand(img, d, t):
    bokeh(img, t, 6, (255, 220, 160))
    camera(img, t, art_stand(t, C["saved"]), (W / 2, 1450))
    finish(img, t, 6)
    tag(img, "THE CRAZY PART", t, (170, 60, 110))
    heading(img, t, "Theaters gave in!", "Selling popcorn saved many from going broke.", C["saved"] - 0.4, sub_color=(255, 225, 240))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 790, "SAVED!", t, C["saved"], col=GOLD, size=100)
    impact(img, t, C["saved"] + 0.2)


def s_war(img, d, t):
    bokeh(img, t, 7, (255, 230, 180))
    camera(img, t, art_war(t, C["rationed"], C["boom"]), (W / 2, 1450))
    finish(img, t, 7)
    tag(img, "IT GETS CRAZIER · WWII", t, (60, 90, 60))
    heading(img, t, "No sugar = no candy", "So popcorn sales exploded!", C["boom"], colors={"NO": (255, 100, 90)}, sub_color=(225, 245, 225))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 830, "RATIONED", t, C["rationed"], col=(255, 110, 90), size=90)
    impact(img, t, C["rationed"] + 0.2, strength=10)


def s_king(img, d, t):
    bokeh(img, t, 8, (255, 220, 160))
    camera(img, t, art_king(t), (W / 2, 1450))
    finish(img, t, 8)
    tag(img, "TODAY", t, (230, 60, 60))
    heading(img, t, "Popcorn is KING!", "Snacks are a huge part of a theater's profit.", 0.6, colors={"KING!": GOLD}, sub_color=(255, 235, 210))


def s_cta(img, d, t):
    text_block(img, "Learned something new?", F_MID, 330, t, delay=0.0)
    make_salt.draw_cta(img, d, W / 2, 1250, t, off=C["cta_off"])


base.TRANSITION = splat
SCENE_LIST = [
    (((40, 15, 25), (10, 4, 8)), s_hook),
    (((60, 45, 25), (18, 12, 6)), s_peru),
    (((55, 20, 30), (15, 5, 8)), s_fancy),
    (((45, 35, 55), (12, 9, 16)), s_coat),
    (((45, 45, 55), (12, 12, 16)), s_vendor),
    (((60, 25, 55), (20, 8, 25)), s_stand),
    (((40, 55, 40), (12, 16, 12)), s_war),
    (((60, 35, 15), (16, 9, 4)), s_king),
    (((30, 30, 40), (8, 8, 12)), s_cta),
]

if __name__ == "__main__":
    out, voice = sys.argv[1], sys.argv[2]
    tl = Timeline(voice)
    durs = tl.plan(["okay", "but in", "some theaters", "then|than the", "the crazy", "it|the gets", "and today", "if you"], tail=1.3)
    C.update(
        slam=tl.cue("banned", 0, lead=0.25), money=tl.cue("money", 0, lead=0.15),
        reveal=tl.cue("archaeologists", 1) + 0.8, messy=tl.cue("messy", 2), noisy=tl.cue("noisy", 2),
        hang=tl.cue("door", 3), cents=tl.cue("cents", 4), fortune=tl.cue("fortune", 4),
        saved=tl.cue("saved", 5), rationed=tl.cue("rationed", 6), boom=tl.cue("exploded", 6),
        cta_off=tl.cue("like", 8) - 1.5,
    )
    print("durations:", durs, "total:", round(sum(durs), 2))
    print("cues:", C)
    base.SCENES[:] = [(dd,) + sc for dd, sc in zip(durs, SCENE_LIST)]
    total = sum(durs)
    S = tl.starts
    events = [("whoosh", s) for s in S[1:]]
    events += [("thud", C["slam"] + 0.22), ("pop", C["money"]), ("pop", S[1] + C["reveal"] + 0.6),
               ("pop", S[2] + C["messy"]), ("pop", S[3] + C["hang"]), ("pop", S[4] + C["cents"]),
               ("thud", S[5] + C["saved"] + 0.2), ("thud", S[6] + C["rationed"] + 0.2), ("pop", S[6] + C["boom"]),
               ("click", S[8] + C["cta_off"] + 1.6), ("click", S[8] + C["cta_off"] + 3.6), ("ding", S[8] + C["cta_off"] + 3.65)]
    audio.music("music.wav", total)
    audio.sfx("sfx.wav", total, events)
    sys.argv = [sys.argv[0], "base_popcorn.mp4"]
    base.OUT = "base_popcorn.mp4"
    base.main_no_exit = True
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_popcorn.mp4", voice, "music.wav", "sfx.wav", out)
    print("wrote", out)
