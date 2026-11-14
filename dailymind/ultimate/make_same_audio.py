"""Sound for the long-form "everyone the same" video: voice on top, CC0 foley on the animation's own cues, -14 LUFS.

  python make_same_audio.py OUT.mp4
Cue times are not retyped: every title slam / stamp is recorded by running each shot once with style2d_engine's
title_layer / stamp_layer wrapped, so a pop lands on the exact frame each title slams in. No music (owner's call).
SFX (BigSoundBank.com, CC0): 1802 whoosh, 0339 coin-in-cup (pop/ting), 0103 door (stamp thud), 2079/2080 chimes, 1103 inhale.
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

import make_same as M
import style2d_engine as E

OUT = sys.argv[1]
SR, DUR = 48000, M.DUR
SFX = os.path.join(M.HERE, "..", "cove_test", "sfx")
WORK = os.path.join(M.D, "_audio")
os.makedirs(os.path.join(WORK, "stems"), exist_ok=True)

# ---- 1) record every slam / stamp the shots draw
EVENTS = set()
CUR = [0]
_tl, _st = E.title_layer, E.stamp_layer


def rec_title(t, lines):
    for txt, size, y, grad, at in lines:
        EVENTS.add(("pop", round(float(at), 4), txt, CUR[0]))
    return _tl(t, lines)


def rec_stamp(t, txt, at, *a, **kw):
    EVENTS.add(("stamp", round(float(at), 4), txt, CUR[0]))
    return _st(t, txt, at, *a, **kw)


E.title_layer, E.stamp_layer = rec_title, rec_stamp
for i, key in enumerate(M.ORDER):
    t0, t1 = M.SHOT_START[i], M.SHOT_END[i]
    CUR[0] = i
    M.SHOTS[key](t1 - 0.02, t1 - 0.02 - t0, t0, t1)
E.title_layer, E.stamp_layer = _tl, _st
# only slams that actually happen inside their shot (a title whose word falls after the cut never shows)
# keep only slams that land inside the shot that draws them (a title whose word falls after the cut never shows)
events = sorted(set((k, at, txt) for k, at, txt, i in EVENTS if M.SHOT_START[i] <= at < M.SHOT_END[i] and 0 <= at < DUR))


def load(name, t0=0.0, dur=None, fi=0.004, fo=0.03):
    path = os.path.join(SFX, name)
    if not os.path.exists(path):
        stem = os.path.splitext(path)[0]
        src = next(stem + e for e in (".ogg", ".mp3") if os.path.exists(stem + e))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-ac", "1", "-ar", "44100", path], check=True)
    a, sr = sf.read(path, always_2d=True)
    a = np.interp(np.arange(0, len(a), sr / SR), np.arange(len(a)), a.mean(axis=1))
    a = a[int(t0 * SR): int((t0 + dur) * SR) if dur else None].copy()
    a[:max(1, int(fi * SR))] *= np.linspace(0, 1, max(1, int(fi * SR)))
    a[-max(1, int(fo * SR)):] *= np.linspace(1, 0, max(1, int(fo * SR)))
    return a


def pitch(a, r):
    return np.interp(np.arange(0, len(a), r), np.arange(len(a)), a)


def db(a, d):
    return a / (np.max(np.abs(a)) + 1e-9) * 10 ** (d / 20)


def onset_of(a, thr=0.3):
    hop = int(0.002 * SR)
    e = np.array([np.abs(a[i:i + hop]).max() for i in range(0, len(a) - hop, hop)])
    return float(np.argmax(e > thr * e.max()) * hop / SR)


N = int(DUR * SR)
bus = np.zeros(N)
CUES = {}


def place(name, a, t, gain):
    a = db(a, gain)
    on = onset_of(a)
    i = int(round((t - on) * SR))
    st = np.zeros(N)
    j = max(0, i)
    a2 = a[j - i:]
    n = min(len(a2), N - j)
    if n <= 0:
        return
    st[j:j + n] = a2[:n]
    bus[:] += st
    k, m = name, 1
    while k in CUES:
        m += 1
        k = f"{name}#{m}"
    CUES[k] = round(t, 4)
    sf.write(os.path.join(WORK, "stems", f"{k}.wav"), st.astype(np.float32), SR)


whoosh = load("bsb_1802.wav", 0, None, 0.003, 0.05)
ting = load("bsb_0339.wav", 0, 0.6, 0.002, 0.25)
thud = load("bsb_0103.wav", 1.85, 0.9, 0.003, 0.3)
chime = load("bsb_2079.wav", 0, 2.2, 0.01, 0.6)
gasp = load("bsb_1103.wav", 2.12, 0.42, 0.004, 0.12)
pop = pitch(ting, 1.6)

for tc in M.CHAP_CUTS:
    place("whoosh", whoosh, tc - 4 / M.FPS, -16)
last_pop = -9.0
for kind, at, txt in events:
    if kind == "stamp":
        place("stamp", pitch(thud, 1.4), at, -12)
    elif at - last_pop > 0.25:          # two lines slamming together get one pop
        place("pop", pop, at, -21)
        last_pop = at
place("morph", chime, M.wt_or("hook1", "isn't", 3.0) - 0.3, -17)
place("gasp", gasp, M.wt_or("hook1", "isn't", 3.0) + 0.1, -10)
place("unlock", pitch(ting, 1.3), M.L("id1") + 0.6, -16)
place("like", pitch(ting, 1.25), M.wt_or("cta", "like", 2.0), -15)
place("subscribe", pitch(ting, 1.5), M.wt_or("cta", "subscribe", 2.6), -15)

v, vsr = sf.read(os.path.join(M.D, "vo.wav"), always_2d=True)
v = np.interp(np.arange(0, len(v), vsr / SR), np.arange(len(v)), v.mean(axis=1))
vb = np.zeros(N)
vb[:min(N, len(v))] = v[:N]
sf.write(os.path.join(WORK, "sfx.wav"), bus.astype(np.float32), SR)
sf.write(os.path.join(WORK, "voice.wav"), vb.astype(np.float32), SR)
json.dump(CUES, open(os.path.join(WORK, "cues.json"), "w"), indent=1)
json.dump([list(e) for e in events], open(os.path.join(WORK, "slams.json"), "w"), indent=1)

pre = os.path.join(WORK, "premix.wav")
fc = ("[0:a]highpass=f=75,acompressor=threshold=0.1:ratio=2.5:attack=6:release=120,asplit=2[v][vk];"
      "[1:a][vk]sidechaincompress=threshold=0.05:ratio=3:attack=10:release=250[s];[v][s]amix=inputs=2:normalize=0:duration=longest[m]")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", os.path.join(WORK, "voice.wav"), "-i", os.path.join(WORK, "sfx.wav"),
                "-filter_complex", fc, "-map", "[m]", "-ar", str(SR), pre], check=True)


def measure(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])


video = os.path.join(WORK, "video.mp4")
if not os.path.exists(video) or os.environ.get("REENCODE") == "1":
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(M.FPS), "-i", os.path.join(M.D, "frames", "%05d.png"),
                    "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p", "-t", f"{DUR:.3f}", video], check=True)
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
print("cues", len(CUES), "slams", len(events))
print("wrote", OUT)
