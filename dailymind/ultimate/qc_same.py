"""QC for the long-form "everyone the same" video. PASS/FAIL per check; sheets in ../same/qc/.

  python qc_same.py FINAL.mp4 [whisper_python]
  - frames: count; 1-frame pop detector (skips the frames around shot cuts and chapter splats); 2 fps contact sheets
    (one per minute); frame-by-frame strips around every chapter cut
  - length 9:30-10:30; audio -14 +-0.5 LUFS, true peak <= -1.5 dBTP, no clipped samples
  - every SFX onset within 1 frame of its cue (own stem); whisper transcript of the final mix == script
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf
from PIL import Image

import make_same as M

MP4 = sys.argv[1]
WPY = sys.argv[2] if len(sys.argv) > 2 else None
FR = os.path.join(M.D, "frames")
QC = os.path.join(M.D, "qc")
os.makedirs(QC, exist_ok=True)
FPS = M.FPS
res = []


def check(name, ok, detail):
    res.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + " | " + detail, flush=True)


def frame(i):
    return Image.open(os.path.join(FR, f"{i + 1:05d}.png")).convert("RGB")


def sheet(idx, cols, scale, out):
    ims = [frame(i).resize((int(1920 * scale), int(1080 * scale)), Image.BILINEAR) for i in idx]
    w, h = ims[0].size
    sh = Image.new("RGB", (cols * w, ((len(ims) + cols - 1) // cols) * h))
    for k, im in enumerate(ims):
        sh.paste(im, ((k % cols) * w, (k // cols) * h))
    sh.save(out)


n = len([f for f in os.listdir(FR) if f.endswith(".png")])
check("frame count", n == M.NF, f"{n} / {M.NF}")
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", MP4]).decode())
check("length 9:30-10:30", 570 <= dur <= 630, f"{dur:.1f} s ({int(dur // 60)}:{dur % 60:04.1f})")
for m in range(0, n, 60 * FPS):   # one sheet per minute at 2 fps
    sheet(list(range(m, min(n, m + 60 * FPS), FPS // 2)), 12, 0.09, os.path.join(QC, f"minute_{m // (60 * FPS):02d}.png"))
cut_frames = sorted(set(int(round(s * FPS)) for s in M.SHOT_START[1:]))
for k, tc in enumerate(M.CHAP_CUTS):
    cf = int(round(tc * FPS))
    sheet([max(0, min(n - 1, cf + d)) for d in range(-5, 7)], 12, 0.1, os.path.join(QC, f"chapter_cut_{k:02d}.png"))
# pop detector on a downscaled copy (skip +-6 frames around every cut: those changes are intended)
near = set(f for cf in cut_frames for f in range(cf - 6, cf + 7))
prev2 = prev = None
pops, maxd = [], 0.0
for i in range(n):
    cur = np.asarray(frame(i).resize((192, 108), Image.BILINEAR)).astype(np.float32)
    if prev2 is not None and (i - 1) not in near:
        a = float(np.mean(np.abs(prev - prev2)))
        b = float(np.mean(np.abs(cur - prev)))
        sk = float(np.mean(np.abs(cur - prev2)))
        maxd = max(maxd, a)
        if min(a, b) > 3.0 and sk < 0.5 * min(a, b):
            pops.append((i - 1, round(a, 1), round(b, 1), round(sk, 1)))
    prev2, prev = prev, cur
check("no 1-frame pops", not pops, f"{len(pops)} suspects {pops[:10]}")
# audio
wav = os.path.join(QC, "final.wav")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", MP4, "-vn", "-ar", "48000", wav], check=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
TP = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
check("loudness -14 +-0.5 LUFS", abs(I + 14) <= 0.5, f"{I} LUFS")
check("true peak <= -1.5 dBTP", TP <= -1.5, f"{TP} dBTP")
a, _ = sf.read(wav, always_2d=True)
check("no clipped samples", int(np.sum(np.abs(a) >= 0.999)) == 0, f"{int(np.sum(np.abs(a) >= 0.999))}")
cues = json.load(open(os.path.join(M.D, "_audio", "cues.json")))
bad = []
for k, t in cues.items():
    st, ssr = sf.read(os.path.join(M.D, "_audio", "stems", f"{k}.wav"))
    hop = int(0.002 * ssr)
    e = np.array([np.abs(st[i:i + hop]).max() for i in range(0, len(st) - hop, hop)])
    on = float(np.argmax(e > 0.3 * e.max()) * 0.002)
    if abs(on - t) > 1 / FPS:
        bad.append((k, t, round(on, 3)))
check("every SFX within 1 frame", not bad, f"{len(cues)} cues, off: {bad[:6]}")
if WPY:
    code = ("import torch,sys,json,numpy as np,soundfile as sf;from faster_whisper import WhisperModel;"
            "a,sr=sf.read(sys.argv[1],always_2d=True);a=a.mean(1);a=np.interp(np.arange(0,len(a),sr/16000),np.arange(len(a)),a).astype(np.float32);"
            "m=WhisperModel('small.en',device='cuda',compute_type='float16');s,_=m.transcribe(a,language='en',beam_size=5,condition_on_previous_text=False);"
            "print(json.dumps(' '.join(x.text for x in s)))")
    heard = json.loads(subprocess.check_output([WPY, "-c", code, wav], stderr=subprocess.DEVNULL).decode().strip().splitlines()[-1])
    src = open(os.path.join(M.HERE, "..", "tts", "chatter_takes.py"), encoding="utf-8").read()
    ns = {"re": re}
    exec(src[src.index("ONES ="):src.index("def transcribe")], ns)
    want, got = ns["norm"](" ".join(l["text"] for l in M.LINES)), ns["norm"](heard)
    import difflib
    diff = [d for d in difflib.ndiff(want, got) if d[0] in "+-"]
    open(os.path.join(QC, "transcript.txt"), "w", encoding="utf-8").write(heard)
    check("final mix transcript == script", not diff, f"{len(want)} words; differences: {diff[:12]}")
fails = [x for x in res if not x[1]]
print("\nALL PASS" if not fails else f"\n{len(fails)} FAIL")
json.dump([dict(check=a, ok=b, detail=c) for a, b, c in res], open(os.path.join(QC, "qc.json"), "w"), indent=1)
