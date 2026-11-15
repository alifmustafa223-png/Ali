"""Splice the verified Chatterbox takes into the final narration, then verify it word by word with faster-whisper.

  /home/user/tts_env/bin/python assemble_vo.py
Inputs: vo.wav (+ its log of start/len per line), vo_add.wav (3 added lines). Output: vo_final.wav, vo_final.wav.times.json
(line starts), vo_final.wav.words.json (word -> time, '#n' for repeats), lines_final.json (the script in order).
"""
import json
import re
import sys

import numpy as np
import soundfile as sf

ORDER = ["hook", "killer", "late", "afterdamp", "haldane", "mice", "alarm", "first", "stopped", "law", "twist", "revive", "retire", "cta"]
GAP = {"killer": 0.45, "late": 0.4, "afterdamp": 0.45, "haldane": 0.55, "mice": 0.4, "alarm": 0.45, "first": 0.4, "stopped": 0.4,
       "law": 0.55, "twist": 0.55, "revive": 0.4, "retire": 0.55, "cta": 0.7}
LEAD = 0.12


def segs(wav, log):
    a, sr = sf.read(wav)
    out = {}
    for ln in open(log):
        m = re.match(r"\s*(\w+): ([\d.]+)s\s+\(([\d.]+)s\)\s+(.*)", ln)
        if m:
            k, t0, d, txt = m.group(1), float(m.group(2)), float(m.group(3)), m.group(4).strip()
            out[k] = (a[int(t0 * sr): int((t0 + d) * sr)], txt)
    return out, sr


A, sr = segs("vo.wav", sys.argv[1])
B, _ = segs("vo_add.wav", sys.argv[2])
A.update(B)
for k, wav, txt in (("stopped", "vo_fix3.wav", "If the canary stopped singing, or fell off its perch, everyone got out. Fast."),
                    ("cta", "vo_fix2.wav", "Did you learn something new? Like, and subscribe.")):   # best-of-4 takes (LESSONS 166)
    a_, sr_ = sf.read(wav)
    assert sr_ == sr
    A[k] = (a_[int(0.1 * sr):], txt)
parts, times, t = [np.zeros(int(LEAD * sr))], {}, LEAD
lines = []
for k in ORDER:
    if k != ORDER[0]:
        g = np.zeros(int(GAP[k] * sr))
        parts.append(g)
        t += len(g) / sr
    seg, txt = A[k]
    times[k] = round(t, 3)
    parts.append(seg)
    t += len(seg) / sr
    lines.append({"key": k, "text": txt})
v = np.concatenate(parts)
sf.write("vo_final.wav", v, sr)
json.dump(times, open("vo_final.wav.times.json", "w"), indent=1)
json.dump(lines, open("lines_final.json", "w"), indent=1)
print("narration length", round(t, 2), "s")

from faster_whisper import WhisperModel  # noqa: E402
model = WhisperModel("small.en", device="cpu", compute_type="int8")
a16 = sf.read("vo_final.wav")[0]
a16 = np.interp(np.arange(0, len(a16), sr / 16000), np.arange(len(a16)), a16).astype(np.float32)   # hand whisper a 16 kHz array (skips PyAV)
segs_, _ = model.transcribe(a16, word_timestamps=True, beam_size=5)
words, heard = {}, []
for s in segs_:
    for w in s.words:
        key = re.sub(r"[^a-z0-9]", "", w.word.lower())
        if not key:
            continue
        heard.append(key)
        k, n = key, 1
        while k in words:
            n += 1
            k = f"{key}#{n}"
        words[k] = round(w.start, 3)
json.dump(words, open("vo_final.wav.words.json", "w"), indent=1)


def norm(s):
    s = s.lower().replace("-", " ")
    return [re.sub(r"[^a-z0-9]", "", x) for x in s.split() if re.sub(r"[^a-z0-9]", "", x)]


NUM = {"1890s": ["eighteen", "nineties"], "1911": ["nineteen", "eleven"], "1986": ["nineteen", "eighty", "six"], "75": ["seventy", "five"]}
exp = [w for ln in lines for w in norm(ln["text"])]
got = []
for w in heard:
    got += NUM.get(w, [w])
ok = got == exp
print("WHISPER", "MATCH" if ok else "MISMATCH")
if not ok:
    import difflib
    for op in difflib.SequenceMatcher(None, exp, got).get_opcodes():
        if op[0] != "equal":
            print(op[0], exp[op[1]:op[2]], "->", got[op[3]:op[4]])
