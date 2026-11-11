"""YouTube Short: "The Leaning Tower of Pisa should have COLLAPSED... and a WAR saved it" — real 3D v2.

Facts (well documented): construction began in 1173; the tower began to lean after the third floor was built (~1178)
because of soft, wet subsoil; wars (Pisa vs Genoa, Lucca, Florence) halted work for almost a century, which let the
soil consolidate — engineers agree it would otherwise have toppled. Later builders made the upper floors taller on the
short side to compensate, so the tower is curved ("banana"). In 1990 the top overhung ~4.5 m; it closed to the public.
From 1993 about 600 tonnes of lead were placed on the north side, then 1999-2001 soil was extracted from under the
north side; the tilt was reduced by ~45 cm and it was declared stable for at least 200 years.

Pipeline: plates = blender/pisa3d.py (real 3D toons, Bullet physics, cinematic cameras; rendered on the RTX PC as
pisa3d/plates/s{i}.mp4). This file adds the classic DailyMind layer: bloom, vignette, dark top, grain, titles,
slams, stamps, gold splat transitions, follow card, CTA v2, music + SFX, -14 LUFS.
Usage: python make_pisa3d.py ../pisa3d/final.mp4        stills: STILLS_DIR=d python make_pisa3d.py x 0,1 1.0,2.0
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
import skia
from PIL import Image, ImageDraw

OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "../pisa3d/final.mp4"
ONLY = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 and sys.argv[2][0].isdigit() else None
STILLS = sys.argv[3].split(",") if len(sys.argv) > 3 else None
sys.argv = [sys.argv[0], "base_pisa3d.mp4"]
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
VOICE_DIR = os.path.join(HERE, "..", "pisa")
PLATES = os.path.join(HERE, "..", "pisa3d", "plates")
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
    line(img, "This tower should have", 220, font(FONT_B, 70))
    slam(img, "COLLAPSED!", 330, t, cue("collapsed", 0) - 0.15, RED, 138)
    line(img, "...and a", 545, font(FONT_B, 64), t, cue("war0", 0) - 0.55)
    slam(img, "WAR SAVED IT", 630, t, cue("war0", 0) - 0.1, GOLD, 120)
    impact(img, t, cue("collapsed", 0) + 0.05, 16)
    impact(img, t, cue("war0", 0) + 0.1, 18)


def tx1(img, t):
    tag(img, "PISA, 1173", t, (40, 90, 170))
    title(img, t, "Builders start a bell tower", "...on soft, WET sand", cue("sand", 1) - 0.5, sub_color=GOLD)


def tx2(img, t):
    title(img, t, "Only 3 floors up...", "it starts to lean", cue("lean", 2) - 0.2, sub_color=(255, 235, 210))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 700, "BADLY!", t, cue("badly", 2), col=RED, size=130)
    impact(img, t, cue("badly", 2) + 0.15, 14)


def tx3(img, t):
    tag(img, "WAR!", t, (170, 40, 40))
    title(img, t, "Work stops...", "for almost 100 YEARS", cue("hundred", 3) - 0.6, sub_color=GOLD)


def tx4(img, t):
    title(img, t, "And that pause...", y=260)
    slam(img, "SAVED IT!", 420, t, cue("saved", 4) - 0.1, GREEN, 150)
    text_block(img, "the soil packed down tight", font(FONT_B, 58), 620, t, (255, 235, 210), cue("soil", 4) - 0.2)
    impact(img, t, cue("saved", 4) + 0.1, 14)


def tx5(img, t):
    title(img, t, "The builders' TRICK", "new floors TALLER on the short side", cue("taller", 5) - 0.5, sub_color=GOLD)


def tx6(img, t):
    title(img, t, "It isn't just leaning...", y=260)
    slam(img, "IT'S CURVED", 420, t, cue("curved", 6) - 0.1, GOLD, 130)
    text_block(img, "...like a BANANA!", font(FONT_B, 64), 620, t, (255, 235, 210), cue("banana", 6) - 0.25)
    impact(img, t, cue("curved", 6) + 0.1, 14)


def tx7(img, t):
    tag(img, "1990", t, (170, 40, 40))
    title(img, t, "The top hung 4.5 m out", "...so they shut it", cue("closed", 7) - 0.8, sub_color=(255, 235, 210))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 700, "CLOSED", t, cue("closed", 7), col=RED, size=130)
    impact(img, t, cue("closed", 7) + 0.15, 14)


def tx8(img, t):
    title(img, t, "600 TONS of lead", "...then soil out, bucket by bucket", cue("pulled", 8) - 0.3, sub_color=SKY)


def tx9(img, t):
    title(img, t, "It WORKED", "straightened by 45 cm", cue("fortyfive", 9) - 0.4, sub_color=GREEN)
    slam(img, "200 MORE YEARS", 640, t, cue("twohundred", 9) - 0.15, GOLD, 105)
    impact(img, t, cue("twohundred", 9) + 0.1, 12)


def tx10(img, t):
    title(img, t, "A surprising fact", "...EVERY day!", cue("every", 10) - 0.2, sub_color=GOLD)


def tx11(img, t):
    slam(img, "WOULD YOU CLIMB IT?", 300, t, cue("climb", 11) - 0.6, (255, 255, 255), 76)
    text_block(img, "Tell me in the comments!", font(FONT_B, 60), 500, t, GOLD, cue("comments", 11) - 0.3)
    impact(img, t, cue("climb", 11) - 0.5, 12)


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
    c0 = A["collapsed"]
    rel = c0 + 0.25
    ev += [("whoosh", c0 - 0.45), ("thud", c0 - 0.05), ("thud", A["war0"]), ("ding", A["war0"] + 0.05),
           ("thud", rel + 3.2), ("thud", rel + 3.35), ("thud", rel + 3.5)]
    ev += [("pop", ST[1] + 0.3 + 0.12 * i) for i in range(4)] + [("thud", A["builders"] + 0.9)]
    ev += [("thud", A["lean"]), ("whoosh", A["lean"] + 0.1), ("thud", A["badly"]), ("ding", A["badly"] + 0.05)]
    ev += [("thud", A["war"] + 0.8), ("thud", A["war"] + 1.7), ("thud", A["war"] + 2.3), ("whoosh", A["hundred"])]
    ev += [("thud", A["saved"]), ("ding", A["saved"] + 0.05)]
    ev += [("thud", ST[5] + 0.9 + 0.55 * i + 0.45) for i in range(5)] + [("ding", A["taller"])]
    ev += [("thud", A["curved"]), ("whoosh", A["banana"] - 0.25), ("pop", A["banana"] + 0.25)]
    ev += [("whoosh", A["top"]), ("thud", A["closed"] + 0.15), ("ding", A["closed"] + 0.2)]
    ev += [("click", A["tons"] + 0.05 + n * 0.13 + 1.1) for n in range(16)]
    ev += [("pop", A["pulled"] + 0.4 + i * 0.24) for i in range(9)]
    ev += [("ding", A["worked"]), ("pop", A["worked"] + 0.3), ("thud", A["twohundred"])] + [("pop", A["twohundred"] - 0.2 + 0.3 * j) for j in range(3)]
    ev += [("click", A["every"])]
    ev += [("thud", A["climb"] - 0.5)] + [("pop", A["comments"] - 0.5 + i * 0.13) for i in range(8)]
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
                img.convert("RGB").save(f"{out}/p3d_{i:02d}_{tt}.png")
        sys.exit()
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), scene(i)) for i, dd in enumerate(D)]
    if ONLY:
        base.SCENES[:] = [s for i, s in enumerate(base.SCENES) if i in ONLY]
    ev = [(k, round(v, 3)) for k, v in sfx_events() if 0 <= v < total]
    music = os.path.join(VOICE_DIR, "music.wav")
    sfx = os.path.join(VOICE_DIR, "sfx.wav")
    audio.music(music, total, bpm=104, seed=73)
    audio.sfx(sfx, total, ev)
    base.OUT = "base_pisa3d.mp4"
    try:
        base.main()
    except SystemExit:
        pass
    audio.master("base_pisa3d.mp4", voice, music, sfx, OUTFILE)
    if _missing:
        print("WARNING: no 3D plates for scenes", sorted(_missing))
    print("wrote", OUTFILE)
