"""Sound for the canary-style Molasses Flood Short: narration on top, real CC0 foley placed on the animation's own cues, -14 LUFS / <= -1.5 dBTP.

  python make_canary_audio.py OUT.mp4
Cues come from make_canary.py (whisper word timestamps, scene cuts, physics.json), so every effect lands on its frame.
No music (approved house style). SFX: BigSoundBank.com, CC0 (../cove_test/sfx): 1802 whoosh | 0339 coin in cup (ting) |
0103 door (stamp thump, small door) | 1103 inhale (gasp) | 2079 / 2080 chimes | 3051 creaking wood.
Synthesised (no recording needed, shaped by hand): canary song (FM trills), the explosion boom + rumble, footsteps,
the oxygen hiss, detector beeps, mine drips + hum.
"""
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

import make_molasses2 as M

OUT = sys.argv[1]
SR = 48000
DUR = M.DUR
SFX = os.path.join(M.HERE, "..", "cove_test", "sfx")
WORK = os.path.join(M.D, "_audio")
os.makedirs(os.path.join(WORK, "stems"), exist_ok=True)
PH = json.load(open(os.path.join(M.D, "physics.json")))
rng = np.random.default_rng(7)


def load(name, t0=0.0, dur=None, fade_in=0.004, fade_out=0.03):
    path = os.path.join(SFX, name)
    if not os.path.exists(path):
        stem = os.path.splitext(path)[0]
        src = next(stem + e for e in (".ogg", ".mp3") if os.path.exists(stem + e))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-ac", "1", "-ar", "44100", path], check=True)
    a, sr = sf.read(path, always_2d=True)
    a = a.mean(axis=1)
    a = np.interp(np.arange(0, len(a), sr / SR), np.arange(len(a)), a)
    a = a[int(t0 * SR): int((t0 + dur) * SR) if dur else None].copy()
    fi, fo = max(1, int(fade_in * SR)), max(1, int(fade_out * SR))
    a[:fi] *= np.linspace(0, 1, fi)
    a[-fo:] *= np.linspace(1, 0, fo)
    return a


def pitch(a, ratio):
    return np.interp(np.arange(0, len(a), ratio), np.arange(len(a)), a)


def db(a, d):
    return a / (np.max(np.abs(a)) + 1e-9) * 10 ** (d / 20)


def onset_of(a, thr=0.3):
    hop = int(0.002 * SR)
    e = np.array([np.abs(a[i:i + hop]).max() for i in range(0, len(a) - hop, hop)])
    return float(np.argmax(e > thr * e.max()) * hop / SR)


N = int(DUR * SR)
bus = np.zeros(N)
CUES = {}


def place(name, a, t, gain_db=None, stem=True):
    if gain_db is not None:
        a = db(a, gain_db)
    on = onset_of(a)
    i = int(round((t - on) * SR))
    st = np.zeros(N)
    j = max(0, i)
    a2 = a[j - i:]
    n = min(len(a2), N - j)
    if n > 0:
        st[j:j + n] = a2[:n]
    bus[:] += st
    if stem:
        k, m = name, 1
        while k in CUES:
            m += 1
            k = f"{name}#{m}"
        CUES[k] = round(t, 4)
        sf.write(os.path.join(WORK, "stems", f"{k}.wav"), st.astype(np.float32), SR)


def bed(a, t0, t1, rms_db):
    """Ambience (not a cue): fitted to [t0, t1) with fades, at a fixed RMS."""
    n = int((t1 - t0) * SR)
    if len(a) < n:
        a = np.tile(a, n // len(a) + 1)
    a = a[:n].copy()
    f = min(n // 4, int(0.3 * SR))
    a[:f] *= np.linspace(0, 1, f)
    a[-f:] *= np.linspace(1, 0, f)
    a = a / (np.sqrt(np.mean(a ** 2)) + 1e-9) * 10 ** (rms_db / 20)
    i0 = int(t0 * SR)
    bus[i0:i0 + n] += a[:N - i0]


# ------------------------------------------------------------------ synthesised sounds
def chirp_song(dur):
    """Canary song: runs of fast FM trills (2.5-6 kHz) with breaths between."""
    out = np.zeros(int(dur * SR))
    t = 0.05
    while t < dur - 0.15:
        n = rng.integers(4, 9)
        f0 = rng.uniform(2600, 4200)
        for k in range(n):
            d = rng.uniform(0.035, 0.07)
            tt = np.arange(int(d * SR)) / SR
            f = f0 * (1 + 0.35 * np.sin(2 * np.pi * rng.uniform(25, 45) * tt)) + np.linspace(0, rng.uniform(-600, 900), len(tt))
            s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / SR)
            env = np.sin(np.pi * tt / d) ** 2
            i = int(t * SR)
            m = min(len(s), len(out) - i)
            if m <= 0:
                break
            out[i:i + m] += (s * env)[:m]
            t += d + rng.uniform(0.008, 0.03)
        t += rng.uniform(0.15, 0.45)
    return out


def boom():
    tt = np.arange(int(2.2 * SR)) / SR
    low = np.sin(2 * np.pi * (38 * tt + 30 * (1 - np.exp(-tt * 6)) / 6)) * np.exp(-tt * 2.2)
    nz = np.convolve(rng.normal(0, 1, len(tt)), np.ones(60) / 60, mode="same") * np.exp(-tt * 3.5)
    crack = rng.normal(0, 1, len(tt)) * np.exp(-tt * 30)
    return 1.0 * low + 0.8 * nz + 0.35 * crack


def hiss(dur):
    n = int(dur * SR)
    x = rng.normal(0, 1, n)
    x = x - np.convolve(x, np.ones(6) / 6, mode="same")          # high-passed air
    env = np.minimum(1, np.arange(n) / (0.08 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.25 * SR))
    return x * env


def step():
    d = 0.07
    tt = np.arange(int(d * SR)) / SR
    return np.convolve(rng.normal(0, 1, len(tt)), np.ones(25) / 25, mode="same") * np.exp(-tt * 55) + 0.6 * np.sin(2 * np.pi * 90 * tt) * np.exp(-tt * 40)


def beep():
    tt = np.arange(int(0.09 * SR)) / SR
    return np.sin(2 * np.pi * 2400 * tt) * np.minimum(1, np.minimum(tt, 0.09 - tt) / 0.005)


def drip():
    tt = np.arange(int(0.25 * SR)) / SR
    f = 1400 + 900 * np.exp(-tt * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 18)



# ------------------------------------------------------------------ extra synthesised sounds
def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def roar(d):
    n = int(d * SR)
    return 25 * lowpass(rng.normal(0, 1, n), 400) + 0.25 * (rng.normal(0, 1, n) - lowpass(rng.normal(0, 1, n), 4))


def groan(d=1.3):
    tt = np.arange(int(d * SR)) / SR
    f = 70 + 25 * np.sin(2 * np.pi * 0.7 * tt)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 2.02) / SR)) * np.minimum(1, tt / 0.3) * np.minimum(1, (d - tt) / 0.3)


def squelch():
    tt = np.arange(int(0.35 * SR)) / SR
    return np.sin(2 * np.pi * np.cumsum(160 + 260 * np.exp(-tt * 9)) / SR) * np.exp(-tt * 8) * (1 + 0.5 * np.sin(2 * np.pi * 31 * tt))


def brushs():
    n = int(0.3 * SR)
    x = rng.normal(0, 1, n) - lowpass(rng.normal(0, 1, n), 8)
    return x * np.sin(np.pi * np.arange(n) / n) ** 2


w, CUTS, SC = M.word_t, M.CUTS, [n for n, _ in M.SCENES]
sp = M.span
whoosh = load("bsb_1802.wav", 0, None, 0.003, 0.05)
ting = load("bsb_0339.wav", 0, 0.6, 0.002, 0.25)
chime1 = load("bsb_2079.wav", 0, 2.2, 0.01, 0.6)
door = load("bsb_0103.wav", 1.85, 0.9, 0.003, 0.3)
gasp = load("bsb_1103.wav", 2.12, 0.42, 0.004, 0.12)
creak = load("bsb_3051.wav", 0.2, 0.7, 0.01, 0.2)
sea = load("bsb_0267.wav", 5.0, 10.0, 0.4, 0.5)

for tc in M.splat_cuts():
    place("whoosh", whoosh, tc - 4 / M.FPS, -16)
tb = w("l01", "burst")
bed(roar(3.5), 0.0, sp("hook")[1], -21)
place("gasp_hook", gasp, 0.35, -12)
place("groan", groan(), tb - 1.2, -20)
place("burst", boom(), tb, -5)
bed(roar(3.0), tb + 0.05, sp("gallons")[1], -22)
place("stamp_once", pitch(door, 1.4), w("l02", "once"), -12)
tf = w("l03", "flattens")
place("collapse", boom(), tf, -8)
fy = M.PHYS.get("planks_land_y", M.META["flood"]["surface_y_far"] + 40)
for k, (vx, vy, _) in enumerate(M.PLANKS[:5]):   # each plank lands on the molasses when its ballistic arc reaches the surface
    y0 = 880.0
    a, b, c = 0.5 * M.G_PX, vy, y0 - fy
    tl = (-b + math.sqrt(b * b - 4 * a * c)) / (2 * a)
    place("plank_land", squelch(), tf + tl, -20, stem=k == 0)
place("stamp_flat", pitch(door, 1.4), tf, -13)
ts = w("l04", "stuck")
for k, t in enumerate(np.arange(sp("stuck")[0] + 0.2, sp("stuck")[1] - 0.2, 0.55)):
    place("squelch", pitch(squelch(), rng.uniform(0.85, 1.2)), t, -21, stem=k == 0)
place("stamp_stuck", pitch(door, 1.4), ts, -11)
bed(sea, sp("harbor")[0], sp("harbor")[1], -28)
place("ting_crazy", pitch(ting, 1.3), w("l07", "crazy"), -18)
ld = M.span("leak")
period, n_ = 0.9, 4
for k in range(int((ld[1] - ld[0]) / period * n_) + 1):      # every drop lands at (k / n) * period + fall time
    t = ld[0] + (k / n_) * period - ((ld[0] / period) % (1 / n_)) * period + PH["drip_fall_s"]
    if ld[0] + 0.05 < t < ld[1] - 0.05:
        place("drip", drip(), t, -24, stem=k == 1)
for k, t in enumerate(np.arange(sp("paint")[0] + 0.15, sp("paint")[1] - 0.2, 0.35)):
    place("brush", brushs(), t, -26, stem=k == 0)
place("stamp_brown", pitch(door, 1.4), w("l09", "brown"), -13)
place("stamp_tested", pitch(door, 1.4), w("l10", "tested"), -12)
place("paper", pitch(whoosh, 1.5), sp("blame")[0] + 0.2, -19)
place("stamp_anarch", pitch(door, 1.4), w("l11", "anarchists"), -12)
place("gavel", pitch(door, 1.25), w("l12", "buy"), -8)
place("stamp_resp", pitch(door, 1.4), w("l13", "responsible"), -12)
for k in range(5):
    place("coins", pitch(ting, rng.uniform(0.9, 1.2)), w("l13", "600", "600000", "six", "hundred") + k * 0.07, -20, stem=k == 0)
place("stamp_sign", pitch(door, 1.45), w("l14", "sign"), -11)
place("chime_sweet", chime1, w("l15", "sweet"), -18)
place("creak_tank", creak, sp("leaky")[0] + 0.3, -22)
place("like", pitch(ting, 1.25), w("cta", "like"), -15)
place("subscribe", pitch(ting, 1.5), w("cta", "subscribe"), -15)
for name in ("hook", "gallons", "flatten", "stuck", "dead", "blame"):        # cold street wind under the winter scenes
    a, b = sp(name)
    bed(lowpass(rng.normal(0, 1, int((b - a) * SR)), 60), a, b, -42)

v, vsr = sf.read(os.path.join(M.D, "chris.wav"), always_2d=True)
v = v.mean(axis=1)
v = np.interp(np.arange(0, len(v), vsr / SR), np.arange(len(v)), v)
vb = np.zeros(N)
vb[:min(N, len(v))] = v[:N]
sf.write(os.path.join(WORK, "sfx.wav"), bus.astype(np.float32), SR)
sf.write(os.path.join(WORK, "voice.wav"), vb.astype(np.float32), SR)
json.dump(CUES, open(os.path.join(WORK, "cues.json"), "w"), indent=1)

pre = os.path.join(WORK, "premix.wav")
fc = ("[0:a]highpass=f=75,acompressor=threshold=0.1:ratio=2.5:attack=6:release=120,asplit=2[v][vk];"
      "[1:a][vk]sidechaincompress=threshold=0.05:ratio=3:attack=10:release=250[s];[v][s]amix=inputs=2:normalize=0:duration=longest[m]")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", os.path.join(WORK, "voice.wav"), "-i", os.path.join(WORK, "sfx.wav"),
                "-filter_complex", fc, "-map", "[m]", "-ar", str(SR), pre], check=True)


def measure(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])


video = os.path.join(WORK, "video.mp4")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(M.FPS), "-i", os.path.join(M.D, "frames", "%04d.jpg"),
                "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", "-t", f"{DUR:.3f}", video], check=True)
I0, _ = measure(pre)
gain, ceil = -14.0 - I0, -3.1
mast = os.path.join(WORK, "master.wav")
for it in range(8):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", pre, "-af",
                    f"volume={gain:.3f}dB,alimiter=limit={10 ** (ceil / 20):.4f}:attack=1:release=60:level=disabled:asc=1", "-ar", str(SR), mast], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-i", mast, "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                    "-t", f"{DUR:.3f}", "-movflags", "+faststart", OUT], check=True)
    I, TP = measure(OUT)
    print(f"master pass {it}: gain {gain:+.2f} dB ceiling {ceil} -> {I} LUFS {TP} dBTP", flush=True)
    if abs(I + 14) <= 0.2 and TP <= -1.5:
        break
    gain += -14.0 - I
    if TP > -1.5:
        ceil -= (TP + 1.5) + 0.2
print("cues", len(CUES))
print("wrote", OUT)
