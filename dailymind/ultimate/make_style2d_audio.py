"""Sound for the 2D test: narration on top, real CC0 foley + a sea/gull bed, mastered to -14 LUFS / -1.5 dBTP.

  python make_style2d_audio.py VOICE.wav FRAMES_DIR OUT.mp4
Every cue comes from ../cove_test/style2d/physics.json (the same numbers the animation used), so each effect lands on
its frame. No music in this test (owner's call). SFX: BigSoundBank.com, CC0 (public domain):
  0267 sea waves + gulls (bed) | 3051 squeaking oak parquet (pier creak) | 1103 breathless man (one sharp inhale = his gasp)
  1802 whoosh, wooden sheet (flick) | 0339 coin in cup (flick ting + catch clink) | 2079 / 2080 dream chimes (gold shimmer)
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
CT = os.path.join(HERE, "..", "cove_test")
SFX = os.path.join(CT, "sfx")
WORK = os.path.join(CT, "style2d")
VOICE, FRAMES, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SR, FPS, DUR = 48000, 30, 10.0
PH = json.load(open(os.path.join(WORK, "physics.json")))


def load(name, t0=0.0, dur=None, fade_in=0.005, fade_out=0.03):
    path = os.path.join(SFX, name)
    if not os.path.exists(path):   # the repo keeps the CC0 originals (.ogg/.mp3); decode them once
        stem = os.path.splitext(path)[0]
        src = next(stem + e for e in (".ogg", ".mp3") if os.path.exists(stem + e))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-ac", "1", "-ar", "44100", path], check=True)
    a, sr = sf.read(path, always_2d=True)
    a = a.mean(axis=1)
    if sr != SR:
        a = np.interp(np.arange(0, len(a), sr / SR), np.arange(len(a)), a)
    a = a[int(t0 * SR): int((t0 + dur) * SR) if dur else None].copy()
    fi, fo = max(1, int(fade_in * SR)), max(1, int(fade_out * SR))
    a[:fi] *= np.linspace(0, 1, fi)
    a[-fo:] *= np.linspace(1, 0, fo)
    return a


def pitch(a, ratio):
    return np.interp(np.arange(0, len(a), ratio), np.arange(len(a)), a)


def norm_peak(a, db):
    return a / (np.max(np.abs(a)) + 1e-9) * 10 ** (db / 20)


STEMS = {}


def place(bus, a, t, onset=0.0, name=None):
    """Put clip a so that its audible onset (onset s into the clip) lands exactly at time t (and keep a stem for QC)."""
    if name:
        STEMS[name] = np.zeros(len(bus))
        place(STEMS[name], a, t, onset)
    i = int(round((t - onset) * SR))
    j = max(0, i)
    a = a[j - i:]
    n = min(len(a), len(bus) - j)
    if n > 0:
        bus[j:j + n] += a[:n]


def onset_of(a, thr=0.3):
    """Onset = first 2 ms block whose peak passes 30 % of the clip's peak (the same rule qc_style2d.py measures with)."""
    hop = int(0.002 * SR)
    e = np.array([np.abs(a[i:i + hop]).max() for i in range(0, len(a) - hop, hop)])
    return float(np.argmax(e > thr * e.max()) * hop / SR)


N = int(DUR * SR)
sfx = np.zeros(N)
fr = lambda f: f / FPS  # noqa: E731
t_gold, t_snap, t_fake = PH["t_gold"], PH["t_snap"], PH["t_fake"]
t_launch, t_catch = fr(PH["launch_frame"]), fr(PH["catch_frame"])
cues = {}
# gold shimmer on "gold"
ch = norm_peak(load("bsb_2079.wav", 0, 2.2, 0.01, 0.6), -17)
place(sfx, ch, t_gold, onset_of(ch), name="shimmer")
cues["shimmer"] = t_gold
# his snap: plank creak as he recoils + a sharp inhale (gasp)
cr = norm_peak(load("bsb_3051.wav", 0, 0.7, 0.005, 0.15), -15)
place(sfx, cr, t_snap + 0.03, onset_of(cr), name="creak")
cues["creak"] = t_snap + 0.03
gs = norm_peak(load("bsb_1103.wav", 2.12, 0.42, 0.004, 0.12), -9)
place(sfx, gs, t_snap, onset_of(gs), name="gasp")
cues["gasp"] = t_snap
# the flick: a light whoosh + the thumb's metallic ting at launch
wh = norm_peak(load("bsb_1802.wav", 0, None, 0.003, 0.05), -14)
place(sfx, wh, t_launch, onset_of(wh), name="flick")
ting = norm_peak(pitch(load("bsb_0339.wav", 0, 0.5, 0.002, 0.2), 1.35), -18)
place(sfx, ting, t_launch, onset_of(ting))
cues["flick"] = t_launch
# the catch: clink, exactly on the catch frame, + a soft chime under "fake"
cl = norm_peak(load("bsb_0339.wav", 0, 0.8, 0.002, 0.25), -11)
place(sfx, cl, t_catch, onset_of(cl), name="catch")
cues["catch"] = t_catch
ch2 = norm_peak(load("bsb_2080.wav", 0, 1.4, 0.01, 0.5), -20)
place(sfx, ch2, t_fake + 0.02, onset_of(ch2), name="fake_chime")
cues["fake_chime"] = t_fake + 0.02
# ambience bed: waves + gulls, quiet, faded in/out
bed = load("bsb_0267.wav", 6.0, DUR, 0.6, 0.8)
bed = bed / (np.sqrt(np.mean(bed ** 2)) + 1e-9) * 10 ** (-36 / 20)
sfx[:len(bed)] += bed
# voice
v, vsr = sf.read(VOICE, always_2d=True)
v = v.mean(axis=1)
v = np.interp(np.arange(0, len(v), vsr / SR), np.arange(len(v)), v)
vb = np.zeros(N)
vb[:min(N, len(v))] = v[:N]
sf.write(os.path.join(WORK, "_sfx.wav"), sfx.astype(np.float32), SR)
sf.write(os.path.join(WORK, "_voice.wav"), vb.astype(np.float32), SR)
json.dump(cues, open(os.path.join(WORK, "audio_cues.json"), "w"), indent=1)
os.makedirs(os.path.join(WORK, "stems"), exist_ok=True)
for k, st in STEMS.items():
    sf.write(os.path.join(WORK, "stems", f"{k}.wav"), st.astype(np.float32), SR)
# mix: voice (light clean-up + compression) on top; foley ducks a little under the voice (sidechain); master
pre = os.path.join(WORK, "_premix.wav")
fc = ("[0:a]highpass=f=75,acompressor=threshold=0.1:ratio=2.5:attack=6:release=120,volume=1.0,asplit=2[v][vk];"
      "[1:a][vk]sidechaincompress=threshold=0.05:ratio=3:attack=10:release=250[s];"
      "[v][s]amix=inputs=2:normalize=0:duration=longest[m]")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", os.path.join(WORK, "_voice.wav"), "-i", os.path.join(WORK, "_sfx.wav"),
                "-filter_complex", fc, "-map", "[m]", "-ar", str(SR), pre], check=True)
# mastering: gain to -14 LUFS into a true-peak-safe limiter, then verify on the encoded AAC file itself
# (a linear loudnorm alone landed at -14.8 LUFS / -1.2 dBTP after AAC encoding)
def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    import re
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])


video_only = os.path.join(WORK, "_video.mp4")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(FRAMES, "%04d.png"),
                "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", "-t", str(DUR), video_only], check=True)
gain, ceil = 0.0, -2.6
I0, _ = measure(pre)
gain = -14.0 - I0
mast = os.path.join(WORK, "_master.wav")
for it in range(6):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", pre, "-af",
                    f"volume={gain:.3f}dB,alimiter=limit={10 ** (ceil / 20):.4f}:attack=1:release=60:level=disabled:asc=1", "-ar", str(SR), mast], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video_only, "-i", mast, "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
                    "-ar", "48000", "-t", str(DUR), "-movflags", "+faststart", OUT], check=True)
    I, TP = measure(OUT)
    print(f"master pass {it}: gain {gain:+.2f} dB, ceiling {ceil} dBFS -> {I} LUFS, {TP} dBTP")
    if abs(I + 14) <= 0.2 and TP <= -1.5:
        break
    gain += -14.0 - I
    if TP > -1.5:
        ceil -= (TP + 1.5) + 0.2
print("cues", cues)
print("wrote", OUT)
