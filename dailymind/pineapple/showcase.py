"""10-second showcase: the hothouse + King scenes at full power (bigger character motion, flying
manure, flying sweat drops, sparkles), with the real voice lines, music and sound effects.

Usage: python showcase.py showcase.mp4
"""
import json
import math
import subprocess
import sys

sys.argv = [sys.argv[0], sys.argv[1] if len(sys.argv) > 1 else "showcase.mp4"]
OUT = sys.argv[1]
import make_pineapple as mp  # noqa: E402
from make_pineapple import C, ImageDraw, base, ease, math as _m, rot, move, breathe, wave  # noqa: E402,F401

import audio  # noqa: E402
from timing import Timeline  # noqa: E402

SHOVEL_A, SHOVEL_P = 8.0, 1.6
shovel = lambda t: SHOVEL_A * math.sin(2 * math.pi * t / SHOVEL_P)
mp.RIG_SPECS["06"] = [
    rot((902, 1865), (885, 1615), (250, 270), lambda t: 5 * math.sin(2 * math.pi * t / 0.6) * (0.5 + 0.5 * abs(math.sin(t * 1.3))) + 1.5),
    rot((1236, 2062), (880, 2200), (460, 140), shovel, tilt=-21.6),
    rot((1180, 1880), (1180, 2000), (170, 160), lambda t: 0.4 * shovel(t)),            # arm follows the shovel
    breathe((900, 2150), (330, 250), wave(0.02, 0.8)),                                   # retching
]
mp.RIG_SPECS["07"] = [
    move((735, 2020), (180, 270), lambda t: (0, -40 * ease(t / 1.0) - 10 * math.sin(2 * math.pi * t / 1.4))),
    rot((440, 2000), (428, 1840), (165, 175), wave(4.5, 1.2)),
    rot((1100, 2320), (1030, 1800), (300, 520), lambda t: -4.5 * ease(t / 1.2) + wave(1.2, 1.6)(t)),
    rot((1031, 1845), (998, 1625), (175, 200), lambda t: -3 * ease((t - 1.2) / 0.5) + wave(2, 0.8)(t)),  # King's head: wow!
]


def flying(img, t, to, k):
    """Manure clumps fly off the shovel at the top of each scoop, sweat flies off the head."""
    d = ImageDraw.Draw(img, "RGBA")
    for n in range(4):
        t0 = 0.3 + n * SHOVEL_P
        dt = t - t0
        if not 0 < dt < 1.1:
            continue
        a = math.radians(shovel(t0))
        px, py = 600 - 1236, 2270 - 2062           # lump on the blade
        tx = 1236 + px * math.cos(a) - py * math.sin(a)
        ty = 2062 + px * math.sin(a) + py * math.cos(a)
        for j in range(5):
            vx, vy = -40 + 45 * j + 25 * math.sin(j * 3.1), -620 - 70 * (j % 3)
            x, y = tx + vx * dt, ty + vy * dt + 0.5 * 2200 * dt * dt
            sx, sy = to(x, y)
            r = (11 + 5 * ((j * 2) % 3)) * k
            spin = dt * 9 + j
            for q in range(3):  # irregular lump: three overlapping blobs
                ox, oy = math.cos(spin + q * 2.1) * r * 0.5, math.sin(spin + q * 2.1) * r * 0.4
                rr = r * (0.75 + 0.15 * q)
                d.ellipse([sx + ox - rr, sy + oy - rr * 0.8, sx + ox + rr, sy + oy + rr * 0.8], fill=(118, 74, 40, 255))
            d.ellipse([sx - r * 0.45, sy - r * 0.55, sx + r * 0.05, sy - r * 0.15], fill=(165, 115, 70, 255))
    for n in range(8):  # sweat drops
        t0 = 0.25 + n * 0.62
        dt = t - t0
        if not 0 < dt < 0.6:
            continue
        side = 1 if n % 2 else -1
        x, y = 885 + side * (120 + 380 * dt), 1500 - 420 * dt + 0.5 * 2600 * dt * dt
        sx, sy = to(x, y)
        r = 13 * k
        d.polygon([(sx, sy - r * 2.2), (sx - r, sy), (sx + r, sy)], fill=(190, 225, 255, 235))
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(190, 225, 255, 235))
        d.ellipse([sx - r * 0.5, sy - r * 0.6, sx - r * 0.05, sy - r * 0.1], fill=(255, 255, 255, 240))


orig_manure = mp.s_manure


def s_manure(img, d, t):
    orig_manure(img, d, t)
    fr, to, k = mp.shot("06@", t, C["d"][5], 1.0, 1.15, (768, 1380), (870, 1540))  # same camera -> same mapping
    flying(img, t, to, k)


voice = "voice.mp3"
paras = json.load(open("paras.json"))
tl = Timeline(voice)
starts = [0.0] + [(paras[i - 1][1] + paras[i][0]) / 2 for i in range(1, len(paras))]
S = starts
f = lambda phrase, sc, lead=0.1: round(tl.find(phrase, S[sc]) - S[sc] - lead, 2)
durs = [round(b - a, 2) for a, b in zip(starts, starts[1:] + [tl.length + 1.9])]
C.update(d=durs, heated=f("heated", 5, 0.4), rotting=f("rotting", 5), handed=f("handed", 6), royal=f("royal", 6, 0.3))
d5, d6 = durs[5], durs[6] + 0.4
base.SCENES[:] = [(d5, ((20, 14, 20), (8, 6, 10)), s_manure), (d6, ((20, 14, 20), (8, 6, 10)), mp.s_king)]
total = d5 + d6
seg = "showcase_voice.wav"
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(S[5]), "-t", str(total), "-i", voice,
                "-af", f"afade=t=out:st={total - 0.4}:d=0.4", seg], check=True)
ev = [("whoosh", d5), ("thud", C["rotting"] + 0.15), ("pop", d5 + C["handed"]), ("ding", d5 + C["handed"] + 0.05)]
ev += [("pop", 0.3 + n * SHOVEL_P + 0.05) for n in range(4) if 0.3 + n * SHOVEL_P < d5]
audio.music("sc_music.wav", total, bpm=96, seed=4)
audio.sfx("sc_sfx.wav", total, ev)
_tr = base.TRANSITION
base.TRANSITION = lambda img, t, dur, idx: _tr(img, t, dur, max(idx, 1)) if idx == 0 and t < 0.4 else _tr(img, t, dur, idx)
base.OUT = "base_showcase.mp4"
sys.argv = [sys.argv[0], "base_showcase.mp4"]
try:
    base.main()
except SystemExit:
    pass
audio.master("base_showcase.mp4", seg, "sc_music.wav", "sc_sfx.wav", OUT)
print("wrote", OUT, round(total, 2), "s")
