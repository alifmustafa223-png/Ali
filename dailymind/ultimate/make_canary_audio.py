"""Sound for the canary Short: narration on top, real CC0 foley placed on the animation's own cues, -14 LUFS / <= -1.5 dBTP.

  python make_canary_audio.py OUT.mp4
Cues come from make_canary.py (whisper word timestamps, scene cuts, physics.json), so every effect lands on its frame.
No music (approved house style). SFX: BigSoundBank.com, CC0 (../cove_test/sfx): 1802 whoosh | 0339 coin in cup (ting) |
0103 door (stamp thump, small door) | 1103 inhale (gasp) | 2079 / 2080 chimes | 3051 creaking wood.
Synthesised (no recording needed, shaped by hand): canary song (FM trills), the explosion boom + rumble, footsteps,
the oxygen hiss, detector beeps, mine drips + hum.
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

import make_canary as M

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


# ------------------------------------------------------------------ cues
w, L, CUTS, SC = M.word_t, M.line_t, M.CUTS, [n for n, _ in M.SCENES]
whoosh = load("bsb_1802.wav", 0, None, 0.003, 0.05)
ting = load("bsb_0339.wav", 0, 0.6, 0.002, 0.25)
chime1 = load("bsb_2079.wav", 0, 2.2, 0.01, 0.6)
chime2 = load("bsb_2080.wav", 0, 1.4, 0.01, 0.5)
door = load("bsb_0103.wav", 1.85, 0.9, 0.003, 0.3)
gasp = load("bsb_1103.wav", 2.12, 0.42, 0.004, 0.12)
creak = load("bsb_3051.wav", 0.2, 0.7, 0.01, 0.2)


def sc_span(name):
    i = SC.index(name)
    return CUTS[i], CUTS[i + 1]


for tc in M.splat_cuts():
    place("whoosh", whoosh, tc - 4 / M.FPS, -16)
place("whoosh_run", whoosh, CUTS[SC.index("run")] - 2 / M.FPS, -13)

# canary song wherever the bird is singing on screen (bed, follows the picture)
for a, b in ((0.0, sc_span("hook")[1]), (w("mice", "sang"), sc_span("mice")[1]), (sc_span("alarm")[0], w("stopped", "stopped")),
             (sc_span("twist")[0], w("twist", "special", "cage")), (w("revive", "woke") + PH["hop"]["t_air"], sc_span("revive")[1]),
             (sc_span("retire")[0], DUR - 0.3)):
    if b > a + 0.2:
        bed(chirp_song(b - a), a, b, -30)

# stamps / slams (the channel's thump)
for name, t in (("stamp_75", w("hook", "seventy", "75", "seventyfive")), ("stamp_co", w("killer", "carbon")), ("stamp_late", w("late", "late")),
                ("stamp_himself", w("haldane", "himself")), ("stamp_out", w("stopped", "out", "got")), ("stamp_1911", w("law", "eleven", "1911")),
                ("stamp_woke", w("revive", "woke")), ("stamp_1986", w("retire", "eighty", "1986", "nineteen"))):
    place(name, pitch(door, 1.4), t, -12)
place("ting_saved", pitch(ting, 1.2), w("hook", "saved"), -19)
place("gasp_dizzy", gasp, w("late", "dizzy"), -11)
place("gasp_himself", pitch(gasp, 0.92), w("haldane", "himself") + 0.05, -12)

# the explosion at the far end: boom on the word, debris clatter as the chunks land (physics: they fall back to y=1520)
tb = w("afterdamp", "explosion")
place("boom", boom(), tb, -5)
for k in range(7):
    place("debris", pitch(ting, rng.uniform(0.35, 0.55)), tb + 0.55 + k * rng.uniform(0.07, 0.14), -26, stem=k == 0)
place("gasp_blast", pitch(gasp, 1.05), tb + 0.15, -14)

# the canary falls off its perch: landing tap on the exact physics frame, then the cage creaks as it swings
tf = w("stopped", "fell")
place("bird_land", pitch(ting, 0.6), tf + PH["fall"]["t_land"], -20)
place("cage_creak", creak, tf + 0.05, -22)
# running feet (3 runners, ~3 steps/s each)
r0, r1 = sc_span("run")
for k, t in enumerate(np.arange(r0 + 0.05, r1 - 0.1, 0.11)):
    place("step", step(), t + rng.uniform(-0.015, 0.015), -22, stem=k == 0)

place("paper", pitch(whoosh, 1.3), w("law", "british", "law") - 0.05, -18)
place("chime_twist", chime2, w("twist", "twist"), -18)
place("chime_cage", chime1, w("twist", "oxygen"), -22)
ts, to, tw = w("revive", "shut"), w("revive", "opened"), w("revive", "woke")
place("door_shut", pitch(door, 1.8), ts + 6 / M.FPS, -14)        # the round door closes 6 frames after "shut"
place("o2_hiss", hiss(1.6), to + 0.2, -26)
place("chime_woke", chime1, tw, -16)
te = w("retire", "electronic")
for k, t in enumerate(np.arange(te + 0.3, CUTS[SC.index("cta")], 0.8)):    # detector LED blinks every 0.8 s from te + 0.3
    place("beep", beep(), t, -24, stem=k == 0)
place("like", pitch(ting, 1.25), w("cta", "like"), -15)
place("subscribe", pitch(ting, 1.5), w("cta", "subscribe"), -15)

# mine ambience under the tunnel scenes: a low hum + occasional drips (not cues)
for name in ("hook", "killer", "late", "blast", "law", "twist", "retire"):
    a, b = sc_span(name)
    hum = np.convolve(rng.normal(0, 1, int((b - a) * SR)), np.ones(300) / 300, mode="same")
    bed(hum, a, b, -40)
    for t in np.arange(a + rng.uniform(0.3, 1.0), b - 0.3, rng.uniform(1.1, 1.9)):
        place("drip", drip(), t, -36, stem=False)

v, vsr = sf.read(os.path.join(M.D, "vo_final.wav"), always_2d=True)
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
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(M.FPS), "-i", os.path.join(M.D, "frames", "%04d.png"),
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
