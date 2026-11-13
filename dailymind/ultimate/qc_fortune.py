"""QC for the fortune cookie Short. Prints PASS/FAIL per check and writes sheets to ../fortune/qc/.

  python qc_fortune.py FINAL.mp4 [whisper_python]
  - frames: count, 1-frame pop detector (skips scene cuts and splats), 10 fps contact sheets, strips around every cut
  - timing: 61-65 s
  - audio: -14 +-0.5 LUFS, true peak <= -1.5 dBTP, no clipped samples, every SFX onset within 1 frame on its own stem,
           whisper transcript of the final mix == script
  - physics: crumbs / cookies rest exactly on their floor (no hover, no sink), the CLOSED-sign pendulum period
"""
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf
from PIL import Image

import make_fortune as F

MP4 = sys.argv[1]
WPY = sys.argv[2] if len(sys.argv) > 2 else None
FR = os.path.join(F.D, "frames")
QC = os.path.join(F.D, "qc")
os.makedirs(QC, exist_ok=True)
FPS = F.FPS
res = []


def check(name, ok, detail):
    res.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + " | " + detail, flush=True)


def frame(i):
    return Image.open(os.path.join(FR, f"{i + 1:04d}.png")).convert("RGB")


def sheet(idx, cols, scale, out):
    ims = [frame(i).resize((int(1080 * scale), int(1920 * scale)), Image.LANCZOS) for i in idx]
    w, h = ims[0].size
    sh = Image.new("RGB", (cols * w, ((len(ims) + cols - 1) // cols) * h))
    for k, im in enumerate(ims):
        sh.paste(im, ((k % cols) * w, (k // cols) * h))
    sh.save(out)


n = len([f for f in os.listdir(FR) if f.endswith(".png")])
check("frame count", n == F.NF, f"{n} / {F.NF}")
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", MP4]).decode())
check("length 61-65 s", 61 <= dur <= 65, f"{dur:.2f} s")
# contact sheets at 10 fps, 60 tiles each
idx = list(range(0, n, 3))
for p in range(0, len(idx), 60):
    sheet(idx[p:p + 60], 12, 0.1, os.path.join(QC, f"sheet_{p // 60:02d}.png"))
# strips around each cut (frame by frame)
cut_frames = sorted(set([int(round(c * FPS)) for c in F.CUTS[1:-1]] + [int(round(c * FPS)) for c in F.INNER_CUTS]))
for k, cf in enumerate(cut_frames):
    sheet([max(0, min(n - 1, cf + d)) for d in range(-5, 6)], 11, 0.12, os.path.join(QC, f"cut_{k:02d}.png"))
# pop detector: a frame out of line with BOTH neighbours (skip +-6 frames around cuts: splats/fades are intentional)
small = [np.asarray(frame(i).resize((216, 384), Image.BILINEAR)).astype(np.float32) for i in range(n)]
d = [float(np.mean(np.abs(small[i + 1] - small[i]))) for i in range(n - 1)]
near_cut = set(f for cf in cut_frames for f in range(cf - 6, cf + 7))
pops = []
for i in range(1, n - 1):
    if i in near_cut:
        continue
    a, b, sk = d[i - 1], d[i], float(np.mean(np.abs(small[i + 1] - small[i - 1])))
    if min(a, b) > 3.0 and sk < 0.5 * min(a, b):
        pops.append((i, round(a, 1), round(b, 1), round(sk, 1)))
check("no 1-frame pops", not pops, f"{len(pops)} suspects {pops[:8]}")
# physics: everything that falls comes to rest exactly on its floor
rest_ok = True
for args in ((9, 21, 99.0, 0.0, (500, 560), 1300, 1515, 2400, 0.3, (-260, 260), 0.0),
             (70, 8, 99.0, 0.0, (160, 920), 700, 1600, 2600, 0.3, (-60, 60), 2.2 / 70)):
    nb, seed, t, t0, xr, y0, fy, g, rest, vxr, stg = args
    bodies = F.falling_bodies(nb, seed, t, t0, xr, y0, fy, g=g, rest=rest, vx_rng=vxr, stagger=stg)
    for (x, y, ang, landed) in bodies:
        if not landed or y > fy + 25.001 or y < fy - 25.001:
            rest_ok = False
check("falling bodies settle on the floor (no hover / sink)", rest_ok, "crumbs + bakery cookies after settling")
period = 2 * math.pi * math.sqrt(0.25 / 9.81)
check("CLOSED sign = real pendulum", abs(period - 1.003) < 0.01, f"period {period:.3f} s for a 25 cm string")
# audio
wav = os.path.join(QC, "final.wav")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", MP4, "-vn", "-ar", "48000", wav], check=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
TP = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
check("loudness -14 +-0.5 LUFS", abs(I + 14) <= 0.5, f"{I} LUFS")
check("true peak <= -1.5 dBTP", TP <= -1.5, f"{TP} dBTP")
a, _ = sf.read(wav, always_2d=True)
check("no clipped samples", int(np.sum(np.abs(a) >= 0.999)) == 0, f"{int(np.sum(np.abs(a) >= 0.999))} samples")
cues = json.load(open(os.path.join(F.D, "_audio", "cues.json")))
bad = []
for k, t in cues.items():
    st, ssr = sf.read(os.path.join(F.D, "_audio", "stems", f"{k}.wav"))
    hop = int(0.002 * ssr)
    e = np.array([np.abs(st[i:i + hop]).max() for i in range(0, len(st) - hop, hop)])
    on = float(np.argmax(e > 0.3 * e.max()) * 0.002)
    if abs(on - t) > 1 / FPS:
        bad.append((k, t, round(on, 3)))
check("every SFX within 1 frame", not bad, f"{len(cues)} cues, off: {bad}")
if WPY:
    code = ("import torch,sys,json,numpy as np,soundfile as sf;from faster_whisper import WhisperModel;"
            "a,sr=sf.read(sys.argv[1],always_2d=True);a=a.mean(1);a=np.interp(np.arange(0,len(a),sr/16000),np.arange(len(a)),a).astype(np.float32);"
            "m=WhisperModel('small.en',device='cuda',compute_type='float16');s,_=m.transcribe(a,language='en',beam_size=5);"
            "print(json.dumps(' '.join(x.text for x in s)))")
    heard = json.loads(subprocess.check_output([WPY, "-c", code, wav], stderr=subprocess.DEVNULL).decode().strip().splitlines()[-1])
    src = open(os.path.join(F.HERE, "..", "tts", "chatter_takes.py"), encoding="utf-8").read()
    ns = {"re": re}
    exec(src[src.index("ONES ="):src.index("def transcribe")], ns)
    script = " ".join(l["text"] for l in F.LINES)
    check("final mix transcript == script", ns["norm"](heard) == ns["norm"](script), f"heard: {heard.strip()!r}")
fails = [x for x in res if not x[1]]
print("\nALL PASS" if not fails else f"\n{len(fails)} FAIL")
json.dump([dict(check=a, ok=b, detail=c) for a, b, c in res], open(os.path.join(QC, "qc.json"), "w"), indent=1)
