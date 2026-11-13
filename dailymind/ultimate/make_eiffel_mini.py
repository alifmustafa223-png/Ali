"""YouTube Short: "The Eiffel Tower was supposed to be TORN DOWN... and a RADIO saved it" — MINIATURE CINEMATIC UNIVERSE version.

Plates: blender/eiffel_mini.py (1:220 miniature Paris, a giant vintage radio, painted figurines, real pendulum/bounce physics,
one continuous camera per scene). Same narration, titles, slams, SFX and end card as the real-3D version.

Facts (well documented): built for the 1889 Exposition Universelle, the tallest man-made structure in the world until
1930; a protest letter by prominent artists (1887) called it "useless and monstrous"; Eiffel's concession ran 20 years
and the city could dismantle it in 1909. Eiffel promoted scientific uses: a meteorological station, aerodynamics
experiments (objects dropped / slid down a cable from the 2nd floor), and from 1903 he funded military wireless
(radiotelegraphy) experiments himself. The army's radio station made it strategic, so it was kept; in WWI the tower
intercepted enemy messages, including those that led to the arrest of the spy Mata Hari. Today it is often cited as
the most visited paid monument in the world.

Plates = blender/eiffel3d.py (rendered on the RTX PC as eiffel3d/plates/s{i}.mp4). This file adds the classic layer.
Usage: python make_eiffel3d.py ../eiffel3d/final.mp4        stills: STILLS_DIR=d python make_eiffel3d.py x 0,1 1.0,2.0
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
import skia
from PIL import Image, ImageDraw

OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "../eiffel_mini/final.mp4"
ONLY = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 and sys.argv[2][0].isdigit() else None
STILLS = sys.argv[3].split(",") if len(sys.argv) > 3 else None
sys.argv = [sys.argv[0], "base_eiffel_mini.mp4"]
sys.path.insert(0, "..")

import audio  # noqa: E402
import make_ketchup  # noqa: E402
import make_short as base  # noqa: E402
import ultimate as U  # noqa: E402
import physics as PH  # noqa: E402
from cta2 import draw_cta2  # noqa: E402
from fx import impact  # noqa: E402
from make_honey import slam  # noqa: E402
from make_ketchup import splat, stamp  # noqa: E402
from make_short import FONT_B, F_MID, H, W, font, tag, text_block  # noqa: E402
from style import heading  # noqa: E402
from toon import *  # noqa: E402,F401,F403

GOLD, RED, SKY, GREEN = (255, 200, 60), (235, 60, 60), (120, 190, 255), (90, 210, 120)
make_ketchup.SPLAT_COLOR = (250, 195, 50)
base.HOOK_SKIP = 0.0
base.CRF = 16
HERE = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.path.join(HERE, "..", "eiffel")
PLATES = os.path.join(HERE, "..", "eiffel_mini", "plates")
PLAN = json.load(open(os.path.join(VOICE_DIR, "plan.json")))
ST, D, A = PLAN["starts"], PLAN["durs"], PLAN["abs"]
TWO_D = {10, 12}
_missing = set()


def cue(name, i):
    return A[name] - ST[i]


# ------------------------------------------------------------------ art
def unpack_videos():
    for i in range(13):
        mp4 = os.path.join(PLATES, f"s{i}.mp4")
        d = os.path.join(PLATES, f"s{i}")
        if os.path.exists(mp4) and not (os.path.isdir(d) and os.listdir(d)):
            os.makedirs(d, exist_ok=True)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp4, "-start_number", "1", os.path.join(d, "%04d.png")], check=True)
            print("unpacked", mp4)


def art_follow(c, t):
    bg(c, (25, 15, 45), (70, 30, 90))
    for k in range(14):
        a = k / 14 * 2 * math.pi + t * 0.5
        p = skia.Path()
        p.moveTo(540, 1350)
        p.lineTo(540 + math.cos(a) * 1500, 1350 + math.sin(a) * 1500)
        p.lineTo(540 + math.cos(a + 0.13) * 1500, 1350 + math.sin(a + 0.13) * 1500)
        p.close()
        c.drawPath(p, P(C(255, 220, 255, 14)))
    blob(c, rrect(380, 1000, 700, 1300, 16), (250, 248, 240), 1.03, 0.88)
    c.drawRect(skia.Rect(380, 1000, 700, 1070), P(C(220, 60, 60)))
    day = 2 + int(t / 0.5)
    f = skia.Font(FB, 140)
    w = f.measureText(str(day))
    c.drawString(str(day), 540 - w / 2, 1240, f, P(C(50, 40, 40)))
    k = (t % 0.5) / 0.5
    c.save()
    c.translate(540 + 300 * k, 1185 - 200 * k + 600 * k * k)
    c.rotate(120 * k)
    c.scale(1, 1 - 0.6 * k)
    blob(c, rrect(-160, -115, 160, 115, 16), (250, 248, 240), 1.03, 0.88)
    w0 = f.measureText(str(day - 1))
    c.drawString(str(day - 1), -w0 / 2, 55, f, P(C(50, 40, 40)))
    c.restore()
    _, py, _, sq, hit = PH.ball_path(t, 540, 1380, 0, 0, 1700, 70, e=0.45, mu=1.0)
    c.save()
    c.translate(540, py)
    c.scale(1 + sq * 0.5, 1 - sq * 0.5)
    blob(c, rrect(-260, -70, 260, 70, 70), (235, 35, 45), 1.25, 0.7)
    f2 = skia.Font(FB, 72)
    w2 = f2.measureText("+ FOLLOW")
    c.drawString("+ FOLLOW", -w2 / 2, 26, f2, P(C(255, 255, 255)))
    c.restore()
    PH.dust(c, t, hit, 540, 1700, (230, 190, 255), 5)


def bg(c, top, bot, y0=0, y1=H):
    c.drawRect(skia.Rect(0, y0, W, y1), P(Shader=lin((0, y0), (0, y1), [C(*top), C(*bot)])))


def art_cta(c, t):
    U.T_EIGHT = -10
    U.background(c, t, 0)
    U.spotlight(c, t, 0)
    c.drawPaint(P(C(10, 6, 14, 120)))
    draw_cta2(c, t, cue("like", 12) - 0.05, cue("like", 12) + 0.7)


def plate(i, t):
    f = int(t * 30) + 1
    d = os.path.join(PLATES, f"s{i}")
    path = os.path.join(d, f"{f:04d}.png")
    if not os.path.exists(path):
        frames = sorted(os.listdir(d)) if os.path.isdir(d) else []
        if not frames:
            _missing.add(i)
            return None
        path = os.path.join(d, frames[min(len(frames) - 1, f - 1)])
    im = Image.open(path).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    return im


def render_art(i, t, dur):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    if i == 10:
        art_follow(c, t)
    elif i == 12:
        art_cta(c, t)
    else:
        im = plate(i, t)
        if im is None:
            c.clear(skia.Color(20, 14, 24))
        else:
            c.drawImage(skia.Image.fromarray(np.ascontiguousarray(np.dstack([np.asarray(im), np.full((H, W), 255, np.uint8)]))), 0, 0)
    if i != 12:  # classic DailyMind finish on top: soft bloom, vignette, dark top for titles, film grain
        snap = surf.makeImageSnapshot()
        c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=U.BLOOM, ImageFilter=skia.ImageFilters.Blur(24, 24),
                                                          BlendMode=skia.BlendMode.kPlus, Alphaf=0.22))
        c.drawPaint(P(Shader=rad(540, 1100, 1250, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 170)], [0, 0.5, 1])))
        c.drawRect(skia.Rect(0, 0, W, 900), P(Shader=lin((0, 0), (0, 900), [C(5, 4, 10, 190), C(5, 4, 10, 0)])))
        c.drawImageRect(U.GRAIN[int(t * 30) % len(U.GRAIN)], skia.Rect(0, 0, W, H), skia.SamplingOptions(),
                        P(Alphaf=0.05, BlendMode=skia.BlendMode.kOverlay))
    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    return Image.fromarray(np.ascontiguousarray(arr))


# ------------------------------------------------------------------ text layer
def title(img, t, text, sub=None, sub_at=1.0, y=400, sub_color=(255, 235, 210)):
    heading(img, t, text, sub, sub_at, F_MID, y, sub_color=sub_color)


def line(img, text, y, f, t=None, at=None):
    if at is not None and t < at:
        return
    dd = ImageDraw.Draw(img, "RGBA")
    tw = dd.textlength(text, font=f)
    dd.text(((W - tw) / 2 + 4, y + 5), text, font=f, fill=(0, 0, 0, 140))
    dd.text(((W - tw) / 2, y), text, font=f, fill=(255, 255, 255))


def tx0(img, t):
    line(img, "The Eiffel Tower was", 200, font(FONT_B, 70))
    line(img, "supposed to be...", 290, font(FONT_B, 70))
    slam(img, "TORN DOWN!", 395, t, cue("torn", 0) - 0.15, RED, 130)
    line(img, "...and a", 585, font(FONT_B, 64), t, cue("radio0", 0) - 0.45)
    slam(img, "RADIO SAVED IT", 665, t, cue("radio0", 0) - 0.1, GOLD, 105)
    impact(img, t, cue("torn", 0) + 0.05, 16)
    impact(img, t, cue("radio0", 0) + 0.1, 18)


def tx1(img, t):
    tag(img, "PARIS, 1889", t, (40, 90, 170))
    title(img, t, "Gustave Eiffel builds", "the TALLEST structure on Earth", cue("tallest", 1) - 0.3, sub_color=GOLD)


def tx2(img, t):
    title(img, t, "Parisians HATE it", "artists call it useless...", cue("useless", 2) - 0.4, sub_color=(255, 235, 210))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 700, "MONSTROUS!", t, cue("monstrous", 2), col=RED, size=120)
    impact(img, t, cue("monstrous", 2) + 0.15, 14)


def tx3(img, t):
    # titles sit HIGH here: the giant permit sheet fills the middle of the frame (no text over its printed text)
    title(img, t, "A permit for just 20 years", "in 1909... it comes down", cue("nineteen", 3) - 0.3, y=210, sub_color=(255, 235, 210))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 640, "DEMOLISH", t, cue("comes", 3), col=RED, size=120)  # empty middle: below the subtitle, above the sheet
    impact(img, t, cue("comes", 3) + 0.15, 14)


def tx4(img, t):
    title(img, t, "So Eiffel gets clever...", y=260)
    slam(img, "MAKE IT USEFUL", 420, t, cue("useful", 4) - 0.15, GOLD, 108)
    impact(img, t, cue("useful", 4) + 0.05, 12)


def tx5(img, t):
    title(img, t, "A weather station on top", "...and drops to study AIR resistance", cue("drops", 5) - 0.3, sub_color=SKY)


def tx6(img, t):
    title(img, t, "A giant RADIO antenna", "...paid with his OWN money", cue("money", 6) - 0.5, sub_color=GOLD)


def tx7(img, t):
    title(img, t, "The army LOVES it", "messages fly across France", cue("messages", 7) - 0.3, sub_color=SKY)


def tx8(img, t):
    tag(img, "1914", t, (170, 40, 40))
    title(img, t, "It catches ENEMY radio...", "...and helps catch a famous spy", cue("spy", 8) - 1.0, sub_color=(255, 235, 210))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 700, "SPY CAUGHT!", t, cue("spy", 8) + 0.1, col=RED, size=110)
    impact(img, t, cue("spy", 8) + 0.25, 14)


def tx9(img, t):
    title(img, t, "Now nobody dares...", "most visited PAID monument on Earth", cue("visited", 9) - 0.4, sub_color=GOLD)
    slam(img, "#1 MONUMENT", 640, t, cue("monument", 9) - 0.1, GOLD, 110)
    impact(img, t, cue("monument", 9) + 0.1, 12)


def tx10(img, t):
    title(img, t, "A surprising fact", "...EVERY day!", cue("every", 10) - 0.2, sub_color=GOLD)


def tx11(img, t):
    line(img, "Would you...", 230, font(FONT_B, 64), t, cue("top2", 11) - 0.9)
    slam(img, "GO TO THE TOP?", 320, t, cue("top2", 11) - 0.35, (255, 255, 255), 100)
    text_block(img, "Tell me in the comments!", font(FONT_B, 60), 500, t, GOLD, cue("comments", 11) - 0.3)
    impact(img, t, cue("top2", 11) - 0.25, 12)


def tx12(img, t):
    pass


TEXT = [tx0, tx1, tx2, tx3, tx4, tx5, tx6, tx7, tx8, tx9, tx10, tx11, tx12]
base.TRANSITION = splat


def scene(i):
    def fn(img, d, t):
        img.paste(render_art(i, t, D[i]))
        TEXT[i](img, t)
    return fn


def sfx_events():
    ev = [("whoosh", s) for s in ST[1:]]
    ev += [("whoosh", A["torn"] - 0.6), ("thud", A["torn"] - 0.05), ("whoosh", A["radio0"] - 0.2), ("ding", A["radio0"]),
           ("thud", A["radio0"] + 0.1)]
    ev += [("thud", ST[1] + 0.15 + j * 0.33 + 0.4) for j in range(12)] + [("ding", A["tallest"])]
    ev += [("pop", A["fair"] - 0.1 + 0.25 * j) for j in range(3)]
    ev += [("pop", A["hated"] - 0.2 + j * 0.42 + 0.9) for j in range(10)] + [("thud", A["monstrous"]), ("ding", A["monstrous"] + 0.05)]
    ev += [("whoosh", A["permit"] - 0.5), ("ding", A["twenty"])] + [("click", A["twenty"] + 0.2 + k * 0.08) for k in range(20)]
    ev += [("thud", A["comes"]), ("ding", A["comes"] + 0.05)]
    ev += [("ding", A["clever"]), ("pop", A["clever"] + 0.05), ("thud", A["useful"])]
    ev += [("whoosh", A["drops"] + 0.2), ("thud", A["drops"] + 2.9)]
    ev += [("whoosh", A["antenna"] - 0.9), ("ding", A["antenna"] - 0.3)] + [("click", A["money"] - 0.6 + i * 0.07) for i in range(14)]
    ev += [("pop", A["loves"]), ("pop", A["loves"] + 0.12), ("whoosh", A["messages"] - 0.2)]
    ev += [("whoosh", A["catches"] - 0.9), ("ding", A["catches"]), ("thud", A["spy"] - 0.15), ("ding", A["spy"] + 0.1)]
    ev += [("whoosh", A["nobody"] - 0.2), ("pop", A["today"])] + [("pop", A["monument"] - 0.2 + 0.3 * j) for j in range(4)] + [("thud", A["monument"])]
    ev += [("click", A["every"])]
    ev += [("thud", A["top2"] - 0.25)] + [("pop", A["comments"] - 0.5 + i * 0.13) for i in range(8)]
    lk = A["like"] - 0.05
    ev += [("click", lk), ("ding", lk + 0.03), ("click", lk + 0.75), ("ding", lk + 1.1)]
    return ev


if __name__ == "__main__":
    unpack_videos()
    voice = os.path.join(VOICE_DIR, "voice.mp3")
    total = round(sum(D), 2)
    if STILLS:
        out = os.environ.get("STILLS_DIR", os.path.join(VOICE_DIR, "stills"))
        os.makedirs(out, exist_ok=True)
        for i in ONLY or range(13):
            for tt in STILLS:
                img = Image.new("RGBA", (W, H))
                scene(i)(img, ImageDraw.Draw(img), float(tt))
                img.convert("RGB").save(f"{out}/e3d_{i:02d}_{tt}.png")
        sys.exit()
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), scene(i)) for i, dd in enumerate(D)]
    if ONLY:
        base.SCENES[:] = [s for i, s in enumerate(base.SCENES) if i in ONLY]
    ev = [(k, round(v, 3)) for k, v in sfx_events() if 0 <= v < total]
    music = os.path.join(VOICE_DIR, "music.wav")
    sfx = os.path.join(VOICE_DIR, "sfx.wav")
    audio.music(music, total, bpm=100, seed=89)
    audio.sfx(sfx, total, ev)
    base.OUT = "base_eiffel_mini.mp4"
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_eiffel_mini.mp4", voice, music, sfx, OUTFILE)
    if _missing:
        print("WARNING: no 3D plates for scenes", sorted(_missing))
    print("wrote", OUTFILE)
