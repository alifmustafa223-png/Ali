"""Best-of-N Chatterbox narration, verified by faster-whisper (both free; Chatterbox is MIT, faster-whisper MIT).

  python chatter_takes.py lines.json OUT.wav [takes=3] [exaggeration=0.7] [cfg=0.3]
For every line: generate N takes (different seeds) on the GPU, transcribe each with faster-whisper (word timestamps),
keep only takes whose words match the script exactly, and pick the one with the best recogniser confidence and no
odd gaps. A line may carry "pause_before_word": ["is", 0.35] to open a dramatic pause in post (cut at the word's
whisper timestamp) - short lines like "is fake." make Chatterbox glitch, so the twist stays inside a full sentence.
Writes OUT.wav (24 kHz mono), OUT.wav.times.json (line starts), OUT.wav.words.json (start of every word, by key
"word" and "word#n" for repeats) and OUT.wav.takes.json (the scorecard of every take).
"""
import hashlib
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
CACHE = os.path.join(os.path.dirname(os.path.abspath(out)), "_takes_cache")
os.makedirs(CACHE, exist_ok=True)
dev = "cuda" if torch.cuda.is_available() else "cpu"
print("device", dev)
tts = ChatterboxTTS.from_pretrained(device=dev)
SR = tts.sr
asr = WhisperModel(os.environ.get("WHISPER", "small.en"), device=dev, compute_type="float16" if dev == "cuda" else "int8")


ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def two(n):
    return ONES[n] if n < 20 else TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])


def year_words(m):
    """Whisper writes years as digits ('1878'); the script spells them ('eighteen seventy-eight'). Compare as words."""
    y = int(m.group(0))
    hi, lo = divmod(y, 100)
    if 1100 <= y <= 1999 or 2010 <= y <= 2099:
        return " " + two(hi) + " " + ("hundred" if lo == 0 else ("oh " + ONES[lo] if lo < 10 else two(lo))) + " "
    return m.group(0)


def num_words(n):
    """Plain cardinal: 100000 -> 'one hundred thousand', 4000000 -> 'four million'."""
    if n < 100:
        return two(n)
    if n < 1000:
        h, r = divmod(n, 100)
        return ONES[h] + " hundred" + ("" if r == 0 else " " + two(r))
    for big, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
        if n >= big:
            q, r = divmod(n, big)
            return num_words(q) + " " + name + ("" if r == 0 else " " + num_words(r))


def norm(s):
    s = s.lower().replace("’", "'").replace("-", " ")
    s = re.sub(r"(\d) ?,(\d{3})", r"\1\2", s)          # whisper writes '100 ,000' / '3,000,000'
    s = re.sub(r"(\d) ?,(\d{3})", r"\1\2", s)
    s = re.sub(r"\b\d{4}\b", year_words, s)            # years: 1878 -> eighteen seventy eight
    s = re.sub(r"\b\d+\b", lambda m: " " + num_words(int(m.group(0))) + " ", s)
    s = re.sub(r"\ba (hundred|thousand|million|billion)\b", r"one \1", s)
    w = re.sub(r"[^a-z' ]", " ", s).split()
    return [{"too": "to", "two": "to", "learnt": "learned"}.get(x, x) for x in w]   # homophones whisper cannot tell apart


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
    for k in range(ln.get("takes", N)):
        seed = 1000 * li + 17 * k + 7
        # cache every take by (text, settings, seed): re-runs only generate lines that changed
        ex_, cf_ = ln.get("exaggeration", EXAG), ln.get("cfg", CFG)
        tag = hashlib.md5(f"{ln['text']}|{ex_}|{cf_}|{seed}".encode()).hexdigest()[:12]
        cpath = os.path.join(CACHE, tag + ".npz")
        if os.path.exists(cpath):
            z = np.load(cpath, allow_pickle=True)
            wav, ws = z["wav"], list(z["ws"])
        else:
            torch.manual_seed(seed)
            wav = tts.generate(ln["text"], exaggeration=ex_, cfg_weight=cf_)[0].cpu().numpy()
            wav = trim(wav)
            w16 = np.interp(np.arange(0, len(wav), SR / 16000), np.arange(len(wav)), wav)   # whisper wants 16 kHz
            ws = transcribe(w16)
            np.savez(cpath, wav=wav, ws=np.array(ws, dtype=object))
        ws = [dict(x) for x in ws]
        got = norm(" ".join(x["w"] for x in ws))
        exact = got == want
        gaps = [ws[i + 1]["start"] - ws[i]["end"] for i in range(len(ws) - 1)]
        max_gap = max(gaps) if gaps else 0.0
        conf = float(np.mean([x["p"] for x in ws])) if ws else 0.0
        peak = float(np.max(np.abs(wav)))
        if peak > 0.95:   # the model's float output can exceed 1.0 - nothing has clipped yet, so scale it, don't reject it
            wav = wav * (0.95 / peak)
        dur = len(wav) / SR
        # the score: exact words first, then recogniser confidence; odd silences inside a line (> 0.8 s) disqualify
        ok = exact and max_gap < 0.8
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
json.dump(card, open(out + ".takes.json", "w"), indent=1, default=float)
print("total", round(t, 2), "s ->", out)
