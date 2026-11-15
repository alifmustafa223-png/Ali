"""Chris (vidIQ) narration -> whisper word timestamps -> line start times (lines_final.json keys), verified."""
import json, re
import numpy as np, soundfile as sf
from faster_whisper import WhisperModel
L = json.load(open("lines_final.json"))
L[-1]["text"] = "Learned something new? Like, and subscribe."
a, sr = sf.read("chris.wav")
m = WhisperModel("small.en", device="cpu", compute_type="int8")
a16 = np.interp(np.arange(0, len(a), sr / 16000), np.arange(len(a)), a).astype(np.float32)
segs, _ = m.transcribe(a16, language="en", word_timestamps=True, beam_size=5)
raw = [w for s in segs for w in s.words if w.word.strip()]
src = open("../tts/chatter_takes.py").read()
ns = {"re": re}
exec(src[src.index("ONES ="):src.index("def transcribe")], ns)
norm = ns["norm"]
got = norm("".join(w.word for w in raw))
exp = norm(" ".join(l["text"] for l in L))
print("WHISPER", "MATCH" if got == exp else "MISMATCH")
if got != exp:
    import difflib
    for op in difflib.SequenceMatcher(None, exp, got).get_opcodes():
        if op[0] != "equal": print(op[0], exp[op[1]:op[2]], "->", got[op[3]:op[4]])
# line starts: walk the normalized words of each line and map to the whisper word that produced them
toks = []                      # (normalized token, start) for each normalized token, in order
for w in raw:
    for tk in norm(w.word):
        toks.append((tk, w.start))
times, i = {}, 0
for l in L:
    n = len(norm(l["text"]))
    times[l["key"]] = round(toks[min(i, len(toks) - 1)][1], 3)
    i += n
words = {}
for w in raw:
    k0 = re.sub(r"[^a-z0-9]", "", w.word.lower())
    if not k0: continue
    k, n = k0, 1
    while k in words:
        n += 1; k = f"{k0}#{n}"
    words[k] = round(w.start, 3)
json.dump(times, open("vo_final.wav.times.json", "w"), indent=1)
json.dump(words, open("vo_final.wav.words.json", "w"), indent=1)
json.dump(L, open("lines_final.json", "w"), indent=1)
print(times)
