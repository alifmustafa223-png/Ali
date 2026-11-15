"""Place each verified Chatterbox take in its script slot, verify the whole narration with faster-whisper,
and embed the real word timestamps into molasses.html (subtitles + reaction cues follow the voice).
  /home/user/tts_env/bin/python assemble.py
"""
import difflib, json, re, subprocess
import numpy as np, soundfile as sf
L = json.load(open("lines.json"))
T = json.load(open("vo_takes.wav.times.json"))
a, sr = sf.read("vo_takes.wav")
DUR = 62.0
out = np.zeros(int(DUR * sr))
keys = [l["key"] for l in L]
for i, l in enumerate(L):
    t0 = T[l["key"]]
    t1 = T[keys[i + 1]] - 0.1 if i + 1 < len(L) else len(a) / sr
    seg = a[int(t0 * sr): int(t1 * sr)]
    idx = np.nonzero(np.abs(seg) > 0.01)[0]
    seg = seg[: idx[-1] + int(0.06 * sr)] if len(idx) else seg
    s0, s1 = l["slot"]
    room = (s1 - s0) - 0.14
    if len(seg) / sr > room:          # gently speed the line up to fit its slot (pitch kept)
        f = len(seg) / sr / room
        assert f <= 1.22, (l["key"], f)
        sf.write("_tmp.wav", seg, sr)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "_tmp.wav", "-af", f"atempo={f:.4f}", "_tmp2.wav"], check=True)
        seg = sf.read("_tmp2.wav")[0]
        print(f"{l['key']}: sped up x{f:.3f}")
    j = int((s0 + 0.06) * sr)
    out[j: j + len(seg)] += seg[: len(out) - j]
sf.write("voice.wav", out, sr)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "voice.wav", "-af", "highpass=f=70,acompressor=threshold=0.12:ratio=2.5:attack=8:release=120",
                "-b:a", "192k", "voice.mp3"], check=True)
from faster_whisper import WhisperModel
m = WhisperModel("small.en", device="cpu", compute_type="int8")
a16 = np.interp(np.arange(0, len(out), sr / 16000), np.arange(len(out)), out).astype(np.float32)
segs, _ = m.transcribe(a16, language="en", word_timestamps=True, beam_size=5)
raw = [w for s in segs for w in s.words]
heard = [(w.word.strip(), w.start, w.end) for w in raw if w.word.strip()]
src = open("../tts/chatter_takes.py").read()          # the same normaliser the takes check uses
ns = {"re": re}
exec(src[src.index("ONES ="):src.index("def transcribe")], ns)
def norm(x):
    return ns["norm"](x)
exp = [w for l in L for w in norm(l["text"])]
got = norm("".join(w.word for w in raw))      # join first: whisper splits "2" ".3" and "$600" ",000"
ok = exp == got
print("WHISPER", "MATCH" if ok else "MISMATCH")
if not ok:
    for op in difflib.SequenceMatcher(None, exp, got).get_opcodes():
        if op[0] != "equal":
            print(op[0], exp[op[1]:op[2]], "->", got[op[3]:op[4]])
# subtitle words: the script's words, timed by the whisper words falling inside each line's slot
words = []
for l in L:
    s0, s1 = l["slot"]
    hw = [h for h in heard if s0 - 0.05 <= h[1] < s1]
    sw = l["text"].split()
    if len(hw) == len(sw):
        times = [(h[1], h[2]) for h in hw]
    else:                              # whisper merged/split words here: spread the script words over the heard span
        h0 = hw[0][1] if hw else s0 + 0.1
        h1 = hw[-1][2] if hw else s1 - 0.1
        wt = [len(re.sub(r"[^A-Za-z0-9]", "", w)) + 2 for w in sw]
        tot, t = sum(wt), h0
        times = []
        for x in wt:
            times.append((t, t + (h1 - h0) * x / tot))
            t += (h1 - h0) * x / tot
        print("spread", l["key"], len(hw), len(sw))
    for w, (t0, t1) in zip(sw, times):
        words.append({"w": w, "t0": round(t0, 3), "t1": round(max(t1, t0 + 0.12), 3), "line": s0})
json.dump(words, open("words.json", "w"), indent=0)
h = open("molasses.html").read()
h = re.sub(r"/\*WORDS\*/.*?/\*END\*/", "/*WORDS*/" + json.dumps(words) + "/*END*/", h, flags=re.S)
open("molasses.html", "w").write(h)
print("embedded", len(words), "words")
