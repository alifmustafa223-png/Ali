"""QC for the 2D test (run before showing the owner). Writes sheets to ../cove_test/style2d/qc/ and prints PASS/FAIL.

  python qc_style2d.py FINAL.mp4 FRAMES_DIR SCRIPT_TEXT [whisper_python]
Checks:
  frames  - 10 fps contact sheets; frame-by-frame strips around the snap, the flip and the catch;
            1-frame pop detector (a frame that differs from BOTH neighbours far more than they differ from each other)
  physics - catch error < 1 px, apex 0.3-0.6 m, the arc stays clear of her hair (from physics.json)
  audio   - integrated loudness -14 +-0.5 LUFS, true peak <= -1.5 dBTP, no clipped samples;
            whisper transcript of the final mix == script; every SFX onset within 1 frame of its cue
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "cove_test", "style2d")
QC = os.path.join(WORK, "qc")
os.makedirs(QC, exist_ok=True)
MP4, FRAMES, SCRIPT = sys.argv[1], sys.argv[2], sys.argv[3]
WPY = sys.argv[4] if len(sys.argv) > 4 else None
FPS = 30
PH = json.load(open(os.path.join(WORK, "physics.json")))
results = []


def check(name, ok, detail):
    results.append((name, ok, detail))
    print(("PASS " if ok else "FAIL ") + name + " | " + detail, flush=True)


def frame(i):
    return Image.open(os.path.join(FRAMES, f"{i + 1:04d}.png")).convert("RGB")


def sheet(idx, cols, scale, out, crop=None):
    ims = []
    for i in idx:
        im = frame(i)
        if crop:
            im = im.crop(crop)
        ims.append(im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS))
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (cols * w, rows * h), (0, 0, 0))
    for k, im in enumerate(ims):
        sh.paste(im, ((k % cols) * w, (k // cols) * h))
    sh.save(out)


n = len([f for f in os.listdir(FRAMES) if f.endswith(".png")])
check("frame count", n == 300, f"{n} frames")
# ---- contact sheets at 10 fps (two halves)
sheet(list(range(0, 150, 3)), 10, 0.16, os.path.join(QC, "sheet_10fps_a.png"))
sheet(list(range(150, 300, 3)), 10, 0.16, os.path.join(QC, "sheet_10fps_b.png"))
snap_f = int(round(PH["t_snap"] * FPS))
L, Cf = PH["launch_frame"], PH["catch_frame"]
sheet(list(range(snap_f - 4, snap_f + 12)), 8, 0.3, os.path.join(QC, "strip_snap.png"), (0, 650, 1080, 1700))
sheet(list(range(L - 6, Cf + 2)), 9, 0.3, os.path.join(QC, "strip_flip.png"), (150, 550, 1050, 1600))
sheet(list(range(Cf - 2, Cf + 14)), 8, 0.3, os.path.join(QC, "strip_catch.png"), (150, 550, 1050, 1600))
# ---- 1-frame pop detector (downscaled, grain-tolerant)
small = [np.asarray(frame(i).resize((270, 480), Image.BILINEAR)).astype(np.float32) for i in range(n)]
d = [float(np.mean(np.abs(small[i + 1] - small[i]))) for i in range(n - 1)]
pops = []
for i in range(1, n - 1):
    a, b, skip = d[i - 1], d[i], float(np.mean(np.abs(small[i + 1] - small[i - 1])))
    if min(a, b) > 3.0 and skip < 0.5 * min(a, b):      # frame i is out of line with both neighbours
        pops.append((i, round(a, 2), round(b, 2), round(skip, 2)))
check("no 1-frame pops", not pops, f"{len(pops)} suspects {pops[:6]}; max frame diff {max(d):.2f} at {int(np.argmax(d))}")
# ---- physics
check("coin catch error < 1 px", PH["catch_error_px"] < 1, f"{PH['catch_error_px']} px")
check("flip apex 0.3-0.6 m", 0.3 <= PH["apex_m"] <= 0.6, f"{PH['apex_m']} m ({PH['apex_px']} px at {PH['ppm']} px/m)")
check("arc clear of her face/hair", PH["coin_max_x"] < PH["hair_left_x"], f"coin right edge {PH['coin_max_x']} < hair {PH['hair_left_x']}")
# ---- audio
wav = os.path.join(QC, "final.wav")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", MP4, "-vn", "-ar", "48000", wav], check=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
TP = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
check("loudness -14 +-0.5 LUFS", abs(I + 14) <= 0.5, f"{I} LUFS")
check("true peak <= -1.5 dBTP", TP <= -1.5, f"{TP} dBTP")
a, sr = sf.read(wav, always_2d=True)
clipped = int(np.sum(np.abs(a) >= 0.999))
check("no clipped samples", clipped == 0, f"{clipped} samples >= 0.999")
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", MP4]).decode())
check("duration 10 s", abs(dur - 10) < 0.05, f"{dur:.3f} s")
# SFX onsets vs cues: each effect is checked on its own stem (overlapping sounds can't mask a late or early one)
cues = json.load(open(os.path.join(WORK, "audio_cues.json")))
bad = []
for k, t in cues.items():
    st, ssr = sf.read(os.path.join(WORK, "stems", f"{k}.wav"))
    hop = int(0.002 * ssr)
    e = np.array([np.abs(st[i:i + hop]).max() for i in range(0, len(st) - hop, hop)])
    on = float(np.argmax(e > 0.3 * e.max()) * 0.002)
    if abs(on - t) > 1 / FPS:
        bad.append((k, round(t, 3), round(on, 3)))
    print(f"   cue {k:<11} {t:6.3f}s  onset {on:6.3f}s  ({(on - t) * 1000:+.0f} ms)")
check("every SFX within 1 frame", not bad, f"{len(cues)} cues, off: {bad}")
# whisper transcript of the final mix
if WPY:
    code = ("import torch,sys,json,numpy as np,soundfile as sf;from faster_whisper import WhisperModel;"
            "a,sr=sf.read(sys.argv[1],always_2d=True);a=a.mean(1);a=np.interp(np.arange(0,len(a),sr/16000),np.arange(len(a)),a).astype(np.float32);"
            "m=WhisperModel('small.en',device='cuda',compute_type='float16');"
            "s,_=m.transcribe(a,language='en',beam_size=5);print(json.dumps(' '.join(x.text for x in s)))")
    heard = json.loads(subprocess.check_output([WPY, "-c", code, wav], stderr=subprocess.DEVNULL).decode().strip().splitlines()[-1])
    norm = lambda s: re.sub(r"[^a-z' ]", " ", s.lower()).split()  # noqa: E731
    check("final mix transcript == script", norm(heard) == norm(SCRIPT), f"heard: {heard.strip()!r}")
fails = [x for x in results if not x[1]]
print("\nALL PASS" if not fails else f"\n{len(fails)} FAIL")
json.dump([dict(check=a, ok=b, detail=c) for a, b, c in results], open(os.path.join(QC, "qc.json"), "w"), indent=1)
