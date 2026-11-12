"""THE DAILYMIND STUDIO — compositor for the three sample directions (same topic, same narration, same brand layer).

Usage: python make_samples.py A|B|C [out.mp4]          plates: ../samples/plates/s{STYLE}{i}.mp4 (from blender/samples_eiffel.py)
Only the 3D plates and the signature transition differ between A (gold iris portal), B (blueprint scan line) and
C (molten time seam); titles, slams, stamps, music and SFX are identical so the comparison is fair.
Ends with the brand sting: "The DailyMind." + "Ever wondered where everyday things came from?"
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
import skia
from PIL import Image, ImageDraw

STYLE = sys.argv[1] if len(sys.argv) > 1 else "A"
OUTFILE = sys.argv[2] if len(sys.argv) > 2 else f"../samples/sample_{STYLE}.mp4"
ONLY = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[3][0].isdigit() else None
STILLS = sys.argv[4].split(",") if len(sys.argv) > 4 else None
sys.argv = [sys.argv[0], f"base_sample_{STYLE}.mp4"]
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
VOICE_DIR = os.path.join(HERE, "..", "samples")
PLATES = os.path.join(HERE, "..", "samples", "plates")
PLAN = json.load(open(os.path.join(VOICE_DIR, "plan.json")))
ST, D, A = PLAN["starts"], PLAN["durs"], PLAN["abs"]
TWO_D = set()
_missing = set()


def cue(name, i):
    return A[name] - ST[i]


# ------------------------------------------------------------------ art
def unpack_videos():
    for i in range(13):
        mp4 = os.path.join(PLATES, f"s{STYLE}{i}.mp4")
        d = os.path.join(PLATES, f"s{STYLE}{i}")
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
    d = os.path.join(PLATES, f"s{STYLE}{i}")
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
    if True:
        im = plate(i, t)
        if im is None:
            c.clear(skia.Color(20, 14, 24))
        else:
            c.drawImage(skia.Image.fromarray(np.ascontiguousarray(np.dstack([np.asarray(im), np.full((H, W), 255, np.uint8)]))), 0, 0)
    if True:  # classic DailyMind finish on top: soft bloom, vignette, dark top for titles, film grain
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
    title(img, t, "A permit for just 20 years", "in 1909... it comes down", cue("nineteen", 2) - 0.3, sub_color=(255, 235, 210))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 700, "DEMOLISH", t, cue("comes", 2), col=RED, size=120)
    impact(img, t, cue("comes", 2) + 0.15, 14)


def tx3(img, t):
    title(img, t, "A giant RADIO antenna", "...paid with his OWN money", cue("money", 3) - 0.5, sub_color=GOLD)


def tx4(img, t):
    tag(img, "1914", t, (170, 40, 40))
    title(img, t, "It catches ENEMY radio...", "...and helps catch a famous spy", cue("spy", 4) - 1.0, sub_color=(255, 235, 210))
    stamp(ImageDraw.Draw(img, "RGBA"), W / 2, 700, "SPY CAUGHT!", t, cue("spy", 4) + 0.1, col=RED, size=110)
    impact(img, t, cue("spy", 4) + 0.25, 14)


def tx5(img, t):
    title(img, t, "Now nobody dares...", "most visited PAID monument on Earth", cue("visited", 5) - 0.4, sub_color=GOLD)
    slam(img, "#1 MONUMENT", 640, t, cue("monument", 5) - 0.1, GOLD, 110)
    impact(img, t, cue("monument", 5) + 0.1, 12)
    k = (t - (D[5] - 1.5)) / 0.4  # brand sting
    if k > 0:
        a = min(1.0, k)
        ov = Image.new("RGBA", (W, H), (6, 5, 10, int(225 * a)))
        img.alpha_composite(ov)
        dd = ImageDraw.Draw(img, "RGBA")
        f1, f2 = font(FONT_B, 112), font(FONT_B, 44)
        for txt, f_, y, col in (("The DailyMind.", f1, 840, (255, 200, 60)), ("Ever wondered where", f2, 1000, (240, 235, 225)),
                                ("everyday things came from?", f2, 1056, (240, 235, 225))):
            tw = dd.textlength(txt, font=f_)
            dd.text(((W - tw) / 2, y), txt, font=f_, fill=col + (int(255 * a),))
        dd.line([(W / 2 - 300 * a, 975), (W / 2 + 300 * a, 975)], fill=(255, 200, 60, int(255 * a)), width=4)


TEXT = [tx0, tx1, tx2, tx3, tx4, tx5]
PREV = {}


def transition(img, t, dur, idx):
    """Style signature transitions. A = gold iris portal, B = blueprint scan line, C = molten time seam."""
    PREV[idx] = img
    if idx == 0 or (idx - 1) not in PREV:
        return img
    k = t / 0.5
    if k >= 1:
        return img
    e = ease(k)
    prev = PREV[idx - 1]
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    gold = (255, 200, 60)
    if STYLE == "A":
        r = 1150 * e
        md.ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], fill=255)
        for wdt, al in ((40, 60), (18, 140), (8, 255)):
            rd.ellipse([W / 2 - r - wdt / 2, H / 2 - r - wdt / 2, W / 2 + r + wdt / 2, H / 2 + r + wdt / 2], outline=gold + (al,), width=wdt)
    elif STYLE == "B":
        y = H * e
        md.rectangle([0, 0, W, y], fill=255)
        for wdt, al in ((30, 60), (12, 150), (4, 255)):
            rd.line([(0, y), (W, y)], fill=gold + (al,), width=wdt)
    else:
        x = -300 + (W + 600) * e
        poly = [(0, 0), (x + 200, 0), (x - 200, H), (0, H)]
        md.polygon(poly, fill=255)
        for wdt, al in ((50, 50), (20, 130), (7, 255)):
            rd.line([(x + 200, 0), (x - 200, H)], fill=gold + (al,), width=wdt)
    out = prev.copy()
    out.paste(img, (0, 0), mask)
    out.alpha_composite(ring)
    return out


base.TRANSITION = transition


def scene(i):
    def fn(img, d, t):
        img.paste(render_art(i, t, D[i]))
        TEXT[i](img, t)
    return fn


def sfx_events():
    ev = [("whoosh", s) for s in ST[1:]]
    ev += [("whoosh", A["torn"] - 0.6), ("thud", A["torn"] - 0.05), ("whoosh", A["radio0"] - 0.2), ("ding", A["radio0"]), ("thud", A["radio0"] + 0.1)]
    ev += [("ding", A["tallest"])] + [("pop", A["fair"] - 0.1 + 0.25 * j) for j in range(3)]
    ev += [("whoosh", A["permit"] - 0.5), ("ding", A["twenty"])] + [("click", A["twenty"] + 0.2 + k * 0.07) for k in range(20)]
    ev += [("thud", A["comes"]), ("ding", A["comes"] + 0.05)]
    ev += [("whoosh", A["antenna"] - 0.9), ("ding", A["antenna"] - 0.3)] + [("click", A["money"] - 1.2 + i * 0.09) for i in range(14)]
    ev += [("whoosh", A["catches"] - 0.9), ("ding", A["catches"]), ("thud", A["spy"] - 0.15), ("ding", A["spy"] + 0.1)]
    ev += [("whoosh", A["nobody"] - 0.2), ("pop", A["today"])] + [("pop", A["monument"] - 0.2 + 0.3 * j) for j in range(3)] + [("thud", A["monument"])]
    ev += [("ding", ST[5] + D[5] - 1.45)]
    return ev


if __name__ == "__main__":
    unpack_videos()
    voice = os.path.join(VOICE_DIR, "voice.mp3")
    total = round(sum(D), 2)
    if STILLS:
        out = os.environ.get("STILLS_DIR", os.path.join(VOICE_DIR, "stills"))
        os.makedirs(out, exist_ok=True)
        for i in ONLY or range(6):
            for tt in STILLS:
                img = Image.new("RGBA", (W, H))
                scene(i)(img, ImageDraw.Draw(img), float(tt))
                img.convert("RGB").save(f"{out}/s{STYLE}_{i:02d}_{tt}.png")
        sys.exit()
    base.SCENES[:] = [(dd, ((20, 14, 20), (8, 6, 10)), scene(i)) for i, dd in enumerate(D)]
    ev = [(k, round(v, 3)) for k, v in sfx_events() if 0 <= v < total]
    music = os.path.join(VOICE_DIR, f"music_{STYLE}.wav")
    sfx = os.path.join(VOICE_DIR, f"sfx_{STYLE}.wav")
    audio.music(music, total, bpm={"A": 92, "B": 108, "C": 100}[STYLE], seed={"A": 11, "B": 23, "C": 37}[STYLE])
    audio.sfx(sfx, total, ev)
    base.OUT = f"base_sample_{STYLE}.mp4"
    try:
        base.main()
    except SystemExit:
        pass
    audio.master(base.OUT, voice, music, sfx, OUTFILE)
    if _missing:
        print("WARNING: no 3D plates for scenes", sorted(_missing))
    print("wrote", OUTFILE)
