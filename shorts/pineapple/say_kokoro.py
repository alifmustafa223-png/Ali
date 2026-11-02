import sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = "/tmp/claude-0/-home-user-Ali/955cd42a-5c7a-5245-9eb6-e7b2c7d4935c/scratchpad/tts/"
k = Kokoro(D + "kokoro-v1.0.onnx", D + "voices-v1.0.bin")
text, voice, speed, out = open(sys.argv[1]).read(), sys.argv[2], float(sys.argv[3]), sys.argv[4]
parts = []; starts = []; pos = 0
sr = 24000
for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
    a, sr = k.create(para, voice=voice, speed=speed, lang="en-us")
    starts.append([pos / sr, (pos + len(a)) / sr]); pos += len(a) + int(0.25 * sr)
    parts += [a, np.zeros(int(0.25 * sr), dtype=a.dtype)]
sf.write(out, np.concatenate(parts[:-1]), sr)
import json; json.dump(starts, open(out + '.paras.json', 'w'))
