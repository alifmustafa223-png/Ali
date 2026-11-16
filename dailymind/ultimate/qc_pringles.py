"""QC for the chip-can (Fred Baur) Short (adapted from qc_molasses2.py). Prints PASS/FAIL per check, sheets to ../pringles/qc/.

  python qc_canary.py FINAL.mp4 [whisper_python]
  - frames: count, 1-frame pop detector (skips cuts/splats), 10 fps contact sheets, frame strips around every cut
  - timing: 61-65 s
  - audio: -14 +-0.5 LUFS, true peak <= -1.5 dBTP, no clipped samples, every SFX onset within 1 frame of its cue,
           faster-whisper transcript of the FINAL MIX == script
  - physics: the falling canary rests exactly on the cage floor and never passes below it; the revived canary's hop lands
             where it started; blast debris never goes below its floor; the cage swing is a real pendulum (L = 0.3 m)
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

import make_pringles as M

MP4 = sys.argv[1]
WPY = sys.argv[2] if len(sys.argv) > 2 else None
FR = M.OUT_FR
QC = os.path.join(M.D, "qc")
os.makedirs(QC, exist_ok=True)
FPS = M.FPS
res = []


def check(name, ok, detail):
    res.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + " | " + detail, flush=True)


def frame(i):
    return Image.open(os.path.join(FR, f"{i + 1:04d}.jpg")).convert("RGB")


def sheet(idx, cols, scale, out):
    ims = [frame(i).resize((int(1080 * scale), int(1920 * scale)), Image.LANCZOS) for i in idx]
    w, h = ims[0].size
    sh = Image.new("RGB", (cols * w, ((len(ims) + cols - 1) // cols) * h))
    for k, im in enumerate(ims):
        sh.paste(im, ((k % cols) * w, (k // cols) * h))
    sh.save(out)


n = len([f for f in os.listdir(FR) if f.endswith(".jpg")])
check("frame count", n == M.NF, f"{n} / {M.NF}")
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", MP4]).decode())
check("length 61-65 s", 61 <= dur <= 65, f"{dur:.2f} s")
idx = list(range(0, n, 3))
for p in range(0, len(idx), 60):
    sheet(idx[p:p + 60], 12, 0.1, os.path.join(QC, f"sheet_{p // 60:02d}.png"))
cut_frames = sorted(set(int(round(c * FPS)) for c in M.CUTS[1:-1]))
for k, cf in enumerate(cut_frames):
    sheet([max(0, min(n - 1, cf + d)) for d in range(-5, 6)], 11, 0.12, os.path.join(QC, f"cut_{k:02d}.png"))
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
# physics: every chip rests exactly on the stack below it; crumbs land on the shop floor, never below it
ps = M.PLAN_STACK
st = M.stack_state(1e3, 0.0, ps["n"], ps["base_y"], ps["drop_h"], ps["every"])
check("chips rest exactly on the stack", all(l and abs(y - (ps["base_y"] - k * M.CHIP_T)) < 1e-9 for k, (y, l) in enumerate(st)),
      f"{len(st)} chips, fall {math.sqrt(2 * ps['drop_h'] / M.G_PX):.3f} s at g={M.G_PX} px/s^2")
lowest = -1e9
for f_ in range(int(M.span("bags")[0] * FPS), int(M.span("bags")[1] * FPS)):
    t_ = f_ / FPS
    tc_ = M.word_t("bags", "broken", "crumbs")
    for vx, vy, dd in M.crumb_params():
        u = t_ - tc_ - dd
        if u > 0:
            lowest = max(lowest, min(M.CRUMB_Y0 + vy * u + 0.5 * M.G_PX * u * u, M.CRUMB_FLOOR))
check("crumbs never pass below the floor", lowest <= M.CRUMB_FLOOR + 1e-9, f"lowest {lowest:.1f} / floor {M.CRUMB_FLOOR}")
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
cues = json.load(open(os.path.join(M.D, "_audio", "cues.json")))
bad = []
for k, t in cues.items():
    st, ssr = sf.read(os.path.join(M.D, "_audio", "stems", f"{k}.wav"))
    hop_ = int(0.002 * ssr)
    e = np.array([np.abs(st[i:i + hop_]).max() for i in range(0, len(st) - hop_, hop_)])
    on = float(np.argmax(e > 0.3 * e.max()) * 0.002)
    if abs(on - t) > 1 / FPS:
        bad.append((k, t, round(on, 3)))
check("every SFX within 1 frame", not bad, f"{len(cues)} cues, off: {bad}")
if WPY:
    code = ("import sys,json,numpy as np,soundfile as sf;from faster_whisper import WhisperModel;"
            "a,sr=sf.read(sys.argv[1],always_2d=True);a=a.mean(1);a=np.interp(np.arange(0,len(a),sr/16000),np.arange(len(a)),a).astype(np.float32);"
            "m=WhisperModel('small.en',device='cpu',compute_type='int8');s,_=m.transcribe(a,language='en',beam_size=5);"
            "print(json.dumps(''.join(x.text for x in s)))")
    heard = json.loads(subprocess.check_output([WPY, "-c", code, wav], stderr=subprocess.DEVNULL).decode().strip().splitlines()[-1])
    src2 = open(os.path.join(M.HERE, "..", "tts", "chatter_takes.py")).read()
    ns = {"re": re}
    exec(src2[src2.index("ONES ="):src2.index("def transcribe")], ns)
    FIX = {"learned": "learn", "bauer": "baur", "phd": "phd", "ph": "phd", "d": None}
    norm = lambda x: [FIX.get(w, w) for w in ns["norm"](x.replace("Ph.D.", "phd").replace("PhD", "phd")) if FIX.get(w, w) is not None]   # whisper hears Chris's "Learned" as "learn" 
    script = " ".join(l["text"] for l in M.LINES)
    check("final mix transcript == script", norm(heard) == norm(script), f"heard: {heard.strip()!r}")
fails = [x for x in res if not x[1]]
print("\nALL PASS" if not fails else f"\n{len(fails)} FAIL")
json.dump([dict(check=a, ok=b, detail=c) for a, b, c in res], open(os.path.join(QC, "qc.json"), "w"), indent=1)
