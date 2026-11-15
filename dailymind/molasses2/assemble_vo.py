"""Narration for the canary-style Molasses Short: the verified molasses lines (slots 0-58.6 s) + the verified CTA take
("Did you learn something new? Like, and subscribe." - LESSONS 166), whisper-checked word by word with word timestamps.
  /home/user/tts_env/bin/python assemble_vo.py
"""
import json, re
import numpy as np, soundfile as sf
M = "../molasses/"
L = json.load(open(M + "lines.json"))[:17]
v, sr = sf.read(M + "voice.wav")
cta, sr2 = sf.read("../canary/vo_fix2.wav")
assert sr == sr2
T_CTA = 59.0
v = v[:int(58.6 * sr)]
out = np.zeros(int(63.0 * sr))
out[:len(v)] = v
c = cta[int(0.1 * sr):]
i = int(T_CTA * sr)
out[i:i + len(c)] = c[:len(out) - i]
end = (i + len(c)) / sr
sf.write("vo_final.wav", out[:int((end + 0.2) * sr)], sr)
times = {l["key"]: round(l["slot"][0] + 0.06, 3) for l in L}
times["cta"] = T_CTA
lines = [{"key": l["key"], "text": l["text"]} for l in L] + [{"key": "cta", "text": "Did you learn something new? Like, and subscribe."}]
json.dump(times, open("vo_final.wav.times.json", "w"), indent=1)
json.dump(lines, open("lines_final.json", "w"), indent=1)
open("vo_end.txt", "w").write(f"{end:.3f}")
from faster_whisper import WhisperModel
m = WhisperModel("small.en", device="cpu", compute_type="int8")
a = sf.read("vo_final.wav")[0]
a16 = np.interp(np.arange(0, len(a), sr / 16000), np.arange(len(a)), a).astype(np.float32)
segs, _ = m.transcribe(a16, language="en", word_timestamps=True, beam_size=5)
raw = [w for s in segs for w in s.words]
words = {}
for w in raw:
    k0 = re.sub(r"[^a-z0-9]", "", w.word.lower())
    if not k0:
        continue
    k, n = k0, 1
    while k in words:
        n += 1
        k = f"{k0}#{n}"
    words[k] = round(w.start, 3)
json.dump(words, open("vo_final.wav.words.json", "w"), indent=1)
src = open("../tts/chatter_takes.py").read()
ns = {"re": re}
exec(src[src.index("ONES ="):src.index("def transcribe")], ns)
ok = ns["norm"]("".join(w.word for w in raw)) == ns["norm"](" ".join(l["text"] for l in lines))
print("narration", round(end, 2), "s | WHISPER", "MATCH" if ok else "MISMATCH")
