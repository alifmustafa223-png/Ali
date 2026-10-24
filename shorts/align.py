"""Print word timings and pauses for a voiceover, so scene cuts can land in natural pauses.

Usage: python align.py voice.mp3
Needs: ffmpeg on PATH, `pip install pocketsphinx`.
"""
import re
import subprocess
import sys

voice = sys.argv[1]

raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", voice, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                     capture_output=True, check=True).stdout

try:
    from pocketsphinx import Decoder
    d = Decoder(samprate=16000)
    d.start_utt()
    d.process_raw(raw, full_utt=True)
    d.end_utt()
    words = [f"{s.start_frame / 100:.1f}:{s.word}" for s in d.seg() if s.word not in ("<s>", "</s>", "<sil>", "[NOISE]")]
    print("WORDS (approximate; spelling may be wrong, timing is what matters):")
    print(" ".join(words))
except ImportError:
    print("pocketsphinx not installed; showing pauses only")

log = subprocess.run(["ffmpeg", "-hide_banner", "-i", voice, "-af", "silencedetect=n=-35dB:d=0.25", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
starts = re.findall(r"silence_start: ([0-9.]+)", log)
ends = re.findall(r"silence_end: ([0-9.]+)", log)
print("\nPAUSES (cut scenes in the middle of one of these):")
for a, b in zip(starts, ends):
    print(f"  {float(a):6.2f} -> {float(b):6.2f}   mid {(float(a) + float(b)) / 2:6.2f}")
dur = re.search(r"Duration: (\d+):(\d+):([0-9.]+)", log)
if dur:
    h, m, s = dur.groups()
    print(f"\nVOICE LENGTH: {int(h) * 3600 + int(m) * 60 + float(s):.2f}s")
