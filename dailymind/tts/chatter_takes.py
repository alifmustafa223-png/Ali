"""Best-of-N Chatterbox narration, verified by faster-whisper (both free; Chatterbox is MIT, faster-whisper MIT).

  python chatter_takes.py lines.json OUT.wav [takes=3] [exaggeration=0.7] [cfg=0.3]
For every line: generate N takes (different seeds) on the GPU, transcribe each with faster-whisper (word timestamps),
keep only takes whose words match the script exactly, and pick the one with the best recogniser confidence and no
odd gaps. A line may carry "pause_before_word": ["is", 0.35] to open a dramatic pause in post (cut at the word's
whisper timestamp) - short lines like "is fake." make Chatterbox glitch, so the twist stays inside a full sentence.
Writes OUT.wav (24 kHz mono), OUT.wav.times.json (line starts), OUT.wav.words.json (start of every word, by key
"word" and "word#n" for repeats) and OUT.wav.takes.json (the scorecard of every take).
"""
import json
import os
import re
import sys

import numpy as np
import soundfile as sf
import torch
from chatterbox.tts import ChatterboxTTS
from faster_whisper import WhisperModel

lines = json.load(open(sys.argv[1]))
out = sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 3
EXAG = float(sys.argv[4]) if len(sys.argv) > 4 else 0.7
CFG = float(sys.argv[5]) if len(sys.argv) > 5 else 0.3
dev = "cuda" if torch.cuda.is_available() else "cpu"
print("device", dev)
tts = ChatterboxTTS.from_pretrained(device=dev)
SR = tts.sr
asr = WhisperModel(os.environ.get("WHISPER", "small.en"), device=dev, compute_type="float16" if dev == "cuda" else "int8")


def norm(s):
    return re.sub(r"[^a-z' ]", " ", s.lower().replace("’", "'")).split()


def transcribe(wav):
    segs, _ = asr.transcribe(wav.astype(np.float32), language="en", word_timestamps=True, beam_size=5,
                             vad_filter=False, condition_on_previous_text=False)
    words = []
    for s in segs:
        for w in s.words:
            words.append(dict(w=w.word.strip(), start=w.start, end=w.end, p=w.probability))
    return words


def trim(w):
    a = np.abs(w)
    idx = np.nonzero(a > 0.01)[0]
    if len(idx) == 0:
        return w
    return w[max(0, idx[0] - int(0.03 * SR)): idx[-1] + int(0.10 * SR)]


card = []
parts, times, words_all, t = [], {}, {}, 0.0
for li, ln in enumerate(lines):
    want = norm(ln["text"])
    best = None
    for k in range(N):
        seed = 1000 * li + 17 * k + 7
        torch.manual_seed(seed)
        wav = tts.generate(ln["text"], exaggeration=ln.get("exaggeration", EXAG), cfg_weight=ln.get("cfg", CFG))[0].cpu().numpy()
        wav = trim(wav)
        # whisper wants 16 kHz
        w16 = np.interp(np.arange(0, len(wav), SR / 16000), np.arange(len(wav)), wav)
        ws = transcribe(w16)
        got = norm(" ".join(x["w"] for x in ws))
        exact = got == want
        gaps = [ws[i + 1]["start"] - ws[i]["end"] for i in range(len(ws) - 1)]
        max_gap = max(gaps) if gaps else 0.0
        conf = float(np.mean([x["p"] for x in ws])) if ws else 0.0
        peak = float(np.max(np.abs(wav)))
        dur = len(wav) / SR
        # the score: exact words first, then recogniser confidence; odd gaps (>0.6 s) or clipping are disqualifying
        ok = exact and max_gap < 0.6 and peak < 0.99
        score = (1 if ok else 0, conf)
        card.append(dict(line=ln["key"], take=k, seed=seed, heard=" ".join(x["w"] for x in ws), exact=exact, conf=round(conf, 3),
                         max_gap=round(max_gap, 2), peak=round(peak, 3), dur=round(dur, 2), ok=ok))
        print(f"{ln['key']:>8} take {k}: ok={ok} conf={conf:.3f} gap={max_gap:.2f} dur={dur:.2f} | {' '.join(x['w'] for x in ws)}", flush=True)
        if best is None or score > best[0]:
            best = (score, wav, ws, k)
    score, wav, ws, k = best
    if not score[0]:
        sys.exit(f"no clean take for line {ln['key']!r}; see the scorecard")
    card.append(dict(line=ln["key"], chosen=k))
    # dramatic pause in post, cut at the whisper timestamp of a word
    pb = ln.get("pause_before_word")
    if pb:
        word, gap = pb
        idx = [i for i, x in enumerate(ws) if norm(x["w"]) == [word]][-1]
        cut_t = (ws[idx - 1]["end"] + ws[idx]["start"]) / 2
        cut = int(cut_t * SR)
        fade = int(0.012 * SR)
        a, b = wav[:cut].copy(), wav[cut:].copy()
        a[-fade:] *= np.linspace(1, 0, fade)
        b[:fade] *= np.linspace(0, 1, fade)
        wav = np.concatenate([a, np.zeros(int(gap * SR), np.float32), b])
        for x in ws[idx:]:
            x["start"] += gap
            x["end"] += gap
    t += ln.get("gap_before", 0.2)
    parts.append(np.zeros(int(ln.get("gap_before", 0.2) * SR), np.float32))
    times[ln["key"]] = round(t, 3)
    for x in ws:
        key = norm(x["w"])[0] if norm(x["w"]) else x["w"]
        kk, n = key, 1
        while kk in words_all:
            n += 1
            kk = f"{key}#{n}"
        words_all[kk] = round(t + x["start"], 3)
    parts.append(wav.astype(np.float32))
    t += len(wav) / SR
sf.write(out, np.concatenate(parts), SR)
json.dump(times, open(out + ".times.json", "w"), indent=1)
json.dump(words_all, open(out + ".words.json", "w"), indent=1)
json.dump(card, open(out + ".takes.json", "w"), indent=1)
print("total", round(t, 2), "s ->", out)
