"""Sound for the fortune cookie Short: narration on top, real CC0 foley on the animation's own cues, -14 LUFS / <= -1.5 dBTP.

  python make_fortune_audio.py OUT.mp4
Cues come from make_fortune.py (word timestamps + scene cuts), so each effect lands on its frame. No music (owner's call).
SFX (BigSoundBank.com, CC0): 0407 rusk crunch | 0261 ocean liner horn | 3404 printing press | 0103 door | 0267 waves + gulls |
1802 whoosh | 0339 coin in cup (ting / clink / tap) | 2079 + 2080 chimes | 1103 inhale (gasp)
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

import make_fortune as F

OUT = sys.argv[1]
SR = 48000
DUR = F.DUR
SFX = os.path.join(F.HERE, "..", "cove_test", "sfx")
WORK = os.path.join(F.D, "_audio")
os.makedirs(os.path.join(WORK, "stems"), exist_ok=True)


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
    """Onset = first 2 ms block whose peak passes 30 % of the clip's peak (the rule the QC measures with)."""
    hop = int(0.002 * SR)
    e = np.array([np.abs(a[i:i + hop]).max() for i in range(0, len(a) - hop, hop)])
    return float(np.argmax(e > thr * e.max()) * hop / SR)


N = int(DUR * SR)
bus = np.zeros(N)
CUES = {}


def place(name, a, t, gain_db=None):
    """Put clip a so its onset lands exactly at t; keep a stem for the QC."""
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
    k = name
    m = 1
    while k in CUES:
        m += 1
        k = f"{name}#{m}"
    CUES[k] = round(t, 4)
    sf.write(os.path.join(WORK, "stems", f"{k}.wav"), st.astype(np.float32), SR)


w, L = F.word_t, F.line_t
crunch = load("bsb_0407.wav", 0.12, 0.6, 0.002, 0.2)
whoosh = load("bsb_1802.wav", 0, None, 0.003, 0.05)
ting = load("bsb_0339.wav", 0, 0.6, 0.002, 0.25)
chime1 = load("bsb_2079.wav", 0, 2.2, 0.01, 0.6)
chime2 = load("bsb_2080.wav", 0, 1.4, 0.01, 0.5)
door = load("bsb_0103.wav", 1.85, 0.9, 0.003, 0.3)
horn = load("bsb_0261.wav", 0.05, 3.2, 0.02, 1.2)
gasp = load("bsb_1103.wav", 2.12, 0.42, 0.004, 0.12)

# hook: the crunch on "cracked" (the frame the halves start to part), a whoosh into each gold splat
place("crunch", crunch, w("hook", "cracked"), -6)
for i in range(1, len(F.SCENES)):
    if F.SCENES[i][0] in ("bakery42", "cta") or F.SCENES[i - 1][0] == "bakery42":
        continue
    place("whoosh", whoosh, F.CUTS[i] - 4 / F.FPS, -16)
place("chime_jp", chime1, w("japanese", "japanese"), -16)
place("stamp_kyoto", pitch(door, 1.4), w("kyoto", "kyoto"), -12)
place("ting_fold", pitch(ting, 1.2), w("darker", "fold"), -19)
place("horn", horn, L("california") + 0.15, -17)
for k in range(6):   # cookies landing in the bakery tray (soft taps)
    place("tap", pitch(ting, 0.62), w("teagarden", "family") + 0.42 + k * 0.23, -24)
place("door_closed", door, w("camps", "closed"), -15)
place("plate", pitch(ting, 0.85), w("factories", "put") + 0.6, -17)
place("chime_billion", chime2, w("billion", "billion"), -17)
place("stamp_daily", pitch(door, 1.4), w("daily", "four"), -12)
# the toppled box (sc_china): tips 90 deg with 1800 deg/s^2 about the shelf edge (sqrt(90/900) s), then falls 500 px at
# g = 2600 px/s^2 (sqrt(2*500/2600) s) onto the floor: the thud lands on that frame
t_box = w("flop", "flopped") + (90 / 900) ** 0.5 + (2 * (1400 - 900) / 2600) ** 0.5
place("box_drop", pitch(door, 1.9), t_box, -17)
place("stamp_too", pitch(door, 1.4), w("flop", "to"), -10)
place("gasp", gasp, w("twist", "japanese"), -9)
place("chime_twist", chime2, w("twist", "along"), -18)
t0c = L("cta") - 0.12
place("like", pitch(ting, 1.25), w("cta", "like"), -15)
place("subscribe", pitch(ting, 1.5), w("cta", "subscribe"), -15)

# ambience beds (not cues): factory press under the factory shot, sea + gulls under the ship and the tea garden
press = load("bsb_3404.wav", 2.0, F.word_t("factories", "put") - L("factories") + 0.3, 0.3, 0.4)
press = press / (np.sqrt(np.mean(press ** 2)) + 1e-9) * 10 ** (-32 / 20)
i0 = int((F.CUTS[[n for n, _ in F.SCENES].index("factory")]) * SR)
bus[i0:i0 + len(press)] += press[:N - i0]
sea_t0 = F.CUTS[[n for n, _ in F.SCENES].index("ship")]
sea_t1 = F.CUTS[[n for n, _ in F.SCENES].index("bakery42")]
sea = load("bsb_0267.wav", 5.0, sea_t1 - sea_t0, 0.5, 0.6)
sea = sea / (np.sqrt(np.mean(sea ** 2)) + 1e-9) * 10 ** (-34 / 20)
i0 = int(sea_t0 * SR)
bus[i0:i0 + len(sea)] += sea[:N - i0]

v, vsr = sf.read(os.path.join(F.D, "vo.wav"), always_2d=True)
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
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(F.FPS), "-i", os.path.join(F.D, "frames", "%04d.png"),
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
