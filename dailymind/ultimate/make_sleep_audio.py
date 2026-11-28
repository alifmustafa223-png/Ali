"""Sound for the canary-style "What If Everyone Stopped Sleeping?" Short: narration on top, real CC0 foley placed on the animation's own cues, -14 LUFS / <= -1.5 dBTP.

  python make_sleep_audio.py OUT.mp4
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

import make_sleep as M

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




def crunch(d=0.28):
    """Dry chips breaking: a fast train of tiny clicks."""
    n = int(d * SR)
    out = np.zeros(n)
    for _ in range(40):
        i = int(rng.uniform(0, n - 400))
        L = int(rng.uniform(80, 300))
        out[i:i + L] += rng.normal(0, 1, L) * np.exp(-np.arange(L) / (L / 4)) * rng.uniform(0.3, 1)
    return out - lowpass(out, 5)


def click(f=3200):
    tt = np.arange(int(0.04 * SR)) / SR
    return (np.sin(2 * np.pi * f * tt) * 0.5 + (rng.normal(0, 1, len(tt)) - lowpass(rng.normal(0, 1, len(tt)), 4))) * np.exp(-tt * 160)


def bubbles(d):
    out = np.zeros(int(d * SR))
    t = 0.0
    while t < d - 0.1:
        b = drip() * rng.uniform(0.3, 1.0)
        b = pitch(b, rng.uniform(0.5, 0.9))
        i = int(t * SR)
        m = min(len(b), len(out) - i)
        out[i:i + m] += b[:m]
        t += rng.uniform(0.08, 0.25)
    return out


def hum(d):
    tt = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * 60 * tt) + 0.4 * np.sin(2 * np.pi * 120 * tt) + 0.3 * lowpass(rng.normal(0, 1, len(tt)), 30) * 6


def wind(d):
    x = lowpass(rng.normal(0, 1, int(d * SR)), 90)
    tt = np.arange(len(x)) / SR
    return x * (0.6 + 0.4 * np.sin(2 * np.pi * 0.23 * tt) ** 2)


def crunch(d=0.28):
    """Dry chips breaking: a fast train of tiny clicks."""
    n = int(d * SR)
    out = np.zeros(n)
    for _ in range(40):
        i = int(rng.uniform(0, n - 400))
        L = int(rng.uniform(80, 300))
        out[i:i + L] += rng.normal(0, 1, L) * np.exp(-np.arange(L) / (L / 4)) * rng.uniform(0.3, 1)
    return out - lowpass(out, 5)


def click(f=3200):
    tt = np.arange(int(0.04 * SR)) / SR
    return (np.sin(2 * np.pi * f * tt) * 0.5 + (rng.normal(0, 1, len(tt)) - lowpass(rng.normal(0, 1, len(tt)), 4))) * np.exp(-tt * 160)


def bubbles(d):
    out = np.zeros(int(d * SR))
    t = 0.0
    while t < d - 0.1:
        b = drip() * rng.uniform(0.3, 1.0)
        b = pitch(b, rng.uniform(0.5, 0.9))
        i = int(t * SR)
        m = min(len(b), len(out) - i)
        out[i:i + m] += b[:m]
        t += rng.uniform(0.08, 0.25)
    return out


def hum(d):
    tt = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * 60 * tt) + 0.4 * np.sin(2 * np.pi * 120 * tt) + 0.3 * lowpass(rng.normal(0, 1, len(tt)), 30) * 6


def wind(d):
    x = lowpass(rng.normal(0, 1, int(d * SR)), 90)
    tt = np.arange(len(x)) / SR
    return x * (0.6 + 0.4 * np.sin(2 * np.pi * 0.23 * tt) ** 2)



def ring(d):
    tt = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * 2200 * tt) * (np.sin(2 * np.pi * 24 * tt) > 0) * np.minimum(1, (d - tt) / 0.05)


def buzz(d):
    tt = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * np.cumsum(220 + 30 * np.sin(2 * np.pi * 7 * tt)) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.8 * tt))


def thud():
    tt = np.arange(int(0.3 * SR)) / SR
    return np.sin(2 * np.pi * np.cumsum(120 * np.exp(-tt * 8) + 50) / SR) * np.exp(-tt * 14) + 0.3 * lowpass(rng.normal(0, 1, len(tt)), 20) * np.exp(-tt * 30) * 8


def murmur(d):
    out = np.zeros(int(d * SR))
    for _ in range(14):
        f0 = rng.uniform(110, 220)
        tt = np.arange(len(out)) / SR
        env = np.clip(np.sin(2 * np.pi * rng.uniform(0.3, 0.8) * tt + rng.uniform(0, 6)), 0, 1) ** 2
        out += np.sin(2 * np.pi * f0 * tt + 3 * np.sin(2 * np.pi * rng.uniform(3, 6) * tt)) * env
    return lowpass(out, 12)



def err_buzz(d=0.35):
    tt = np.arange(int(d * SR)) / SR
    return np.sign(np.sin(2 * np.pi * 140 * tt)) * 0.5 * np.minimum(1, (d - tt) / 0.04)



def tick():
    tt = np.arange(int(0.05 * SR)) / SR
    return np.sin(2 * np.pi * 3000 * tt) * np.exp(-tt * 120)


def horn(d=0.5):
    tt = np.arange(int(d * SR)) / SR
    return (np.sign(np.sin(2 * np.pi * 330 * tt)) + np.sign(np.sin(2 * np.pi * 415 * tt))) * 0.3 * np.minimum(1, (d - tt) / 0.05) * np.minimum(1, tt / 0.02)


def snore(d=1.2):
    tt = np.arange(int(d * SR)) / SR
    return lowpass(rng.normal(0, 1, len(tt)), 40) * 8 * np.sin(np.pi * tt / d) ** 2 * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * tt))


def drip_low():
    return pitch(drip(), 0.7)


w, sp = M.word_t, M.span
whoosh = load("bsb_1802.wav", 0, None, 0.003, 0.05)
ting = load("bsb_0339.wav", 0, 0.6, 0.002, 0.25)
chime1 = load("bsb_2079.wav", 0, 2.2, 0.01, 0.6)
chime2 = load("bsb_2080.wav", 0, 2.2, 0.01, 0.6)
door = load("bsb_0103.wav", 1.85, 0.9, 0.003, 0.3)
gasp = load("bsb_1103.wav", 2.12, 0.42, 0.004, 0.12)
stamp = pitch(door, 1.4)

for tc in M.splat_cuts():
    place("whoosh", whoosh, tc - 4 / M.FPS, -16)
a, b = sp("hook")
for k, t in enumerate(np.arange(a + 0.25, b - 0.1, 0.5)):          # the fast-spinning wall clock
    place("clock", tick(), t, -30, stem=k == 0)
place("slam_slept", pitch(door, 1.2), w("hook", "slept") + 0.05, -11)
place("eerie", pitch(chime1, 0.7), w("hook", "see"), -20)
place("stamp_visions", stamp, w("hook", "there") + 0.35, -11)
place("ting_n1", pitch(ting, 1.0), w("night", "night", "one"), -18)
place("drop_in_cup", drip_low(), w("night", "sells"), -18)
place("stamp_sold", stamp, w("night", "out") + 0.3, -11)
place("grumble", pitch(groan(0.8), 1.6), w("night", "cranky") + 0.3, -26)
a, b = sp("drunk")
bed(lowpass(rng.normal(0, 1, int((b - a) * SR)), 30) * 6, a, b, -34)          # night traffic rumble
place("slam_drunk", pitch(door, 1.2), w("drunk", "drunk") + 0.4, -12)
place("horn1", horn(0.45), w("drunk", "every") + 0.3, -20)
place("horn2", pitch(horn(0.35), 1.2), w("drunk", "driver") + 0.95, -22)
place("stamp_every", stamp, w("drunk", "driver") + 0.5, -12)
place("ting_d2", pitch(ting, 0.95), w("micro", "day", "two"), -18)
t0 = w("micro", "few") - 0.1
t1 = w("micro", "mid") + 0.05
place("snore", snore(t1 - t0 - 0.15), t0 + 0.2, -26)
place("jolt", gasp, t1, -16)
place("stamp_mid", stamp, w("micro", "sentence") + 0.5, -11)
a, b = sp("halluc")
place("ting_d3", pitch(ting, 0.9), w("halluc", "day", "three"), -18)
bed(pitch(chime2, 0.5)[:int((b - a) * SR)], a, b, -32)
place("boom", boom(), w("halluc", "explode") + 0.4, -13)
place("stamp_boom", stamp, w("halluc", "explode") + 0.4, -12)
for k, tl in enumerate(M.page_land_times()):
    place("page_land", lowpass(pitch(click(900), 1.0), 6), tl, -30, stem=k == 0)
for k, tt in enumerate(M.page_tear_times()):
    place("page_tear", pitch(click(2000), 0.8), tt, -26, stem=k == 0)
place("stamp_days", stamp, w("real", "days") + 0.45, -11)
place("chime_twist", chime1, w("twist", "twist"), -16)
place("wash", pitch(whoosh, 0.6), w("twist", "washes") - 0.1, -20)
place("stamp_gone", stamp, w("twist", "away") + 0.5, -12)
place("stamp_tracked", stamp, w("end", "record") + 0.3, -11)
place("lamp_click", pitch(click(1200), 1.0), w("end", "go"), -20)
place("lullaby", chime2, w("end", "go") + 0.1, -18)
place("like", pitch(ting, 1.25), w("cta", "like"), -15)
place("subscribe", pitch(ting, 1.5), w("cta", "subscribe"), -15)

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
for it in range(12):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", pre, "-af",
                    f"volume={gain:.3f}dB,alimiter=limit={10 ** (ceil / 20):.4f}:attack=1:release=60:level=disabled:asc=1", "-ar", str(SR), mast], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-i", mast, "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                    "-t", f"{DUR:.3f}", "-movflags", "+faststart", OUT], check=True)
    I, TP = measure(OUT)
    print(f"master pass {it}: gain {gain:+.2f} dB ceiling {ceil} -> {I} LUFS {TP} dBTP", flush=True)
    if abs(I + 14) <= 0.35 and TP <= -1.5:
        break
    gain += -14.0 - I
    if TP > -1.5:
        ceil -= (TP + 1.5) + 0.2
print("cues", len(CUES))
print("wrote", OUT)
