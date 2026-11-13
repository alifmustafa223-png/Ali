"""Free, commercial-OK narration with Chatterbox (MIT, Resemble AI).

  /home/user/tts_env/bin/python chatter.py lines.json out.wav [exaggeration=0.6] [cfg=0.5] [voice_ref.wav]
lines.json: [{"key": "gold", "text": "...", "gap_before": 0.25}, ...]
Writes out.wav (mono, 24 kHz) and out.wav.times.json ({key: start_seconds}) so the animation can hit the words.
voice_ref.wav (optional, ~10-20 s of clean speech we have the rights to) clones that voice; without it the built-in voice.
"""
import json
import sys

import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS

lines = json.load(open(sys.argv[1]))
out = sys.argv[2]
exag = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
cfg = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
ref = sys.argv[5] if len(sys.argv) > 5 else None
torch.manual_seed(7)
model = ChatterboxTTS.from_pretrained(device="cuda" if torch.cuda.is_available() else "cpu")
sr = model.sr
parts, times, t = [], {}, 0.0
for ln in lines:
    gap = int(ln.get("gap_before", 0.2) * sr)
    parts.append(torch.zeros(1, gap))
    t += gap / sr
    wav = model.generate(ln["text"], audio_prompt_path=ref, exaggeration=ln.get("exaggeration", exag), cfg_weight=ln.get("cfg", cfg))
    # trim leading/trailing near-silence so the gaps we ask for are the gaps you hear
    a = wav[0].abs()
    idx = (a > 0.01).nonzero()
    if len(idx):
        wav = wav[:, max(0, int(idx[0]) - int(0.03 * sr)): int(idx[-1]) + int(0.08 * sr)]
    times[ln["key"]] = round(t, 3)
    parts.append(wav)
    t += wav.shape[1] / sr
    print(f"{ln['key']:>8}: {times[ln['key']]:.2f}s  ({wav.shape[1] / sr:.2f}s)  {ln['text']}")
ta.save(out, torch.cat(parts, dim=1), sr)
json.dump(times, open(out + ".times.json", "w"), indent=1)
print("total", round(t, 2), "s ->", out)
