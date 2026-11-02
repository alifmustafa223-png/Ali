"""Shorten long pauses in a voice track (keeps the natural speed; added for the gum video).

    python tighten.py in.mp3 out.wav [max_pause=0.55]

Every silence longer than max_pause (silencedetect -35 dB, >= 0.25 s) is cut from its middle down
to max_pause, with 20 ms crossfades so no clicks appear."""
import re
import subprocess
import sys
import wave

import numpy as np

SR = 44100


def main(src, dst, keep=0.55):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", "silencedetect=n=-35dB:d=0.25", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    sil = list(zip(map(float, re.findall(r"silence_start: ([0-9.]+)", log)), map(float, re.findall(r"silence_end: ([0-9.]+)", log))))
    fade = int(0.02 * SR)
    out, pos, removed = [], 0, 0.0
    for a, b in sil:
        if b - a <= keep:
            continue
        mid = (a + b) / 2
        c0, c1 = int((mid - keep / 2) * SR), int((mid + keep / 2) * SR)
        cut0, cut1 = c0 + int(keep / 2 * SR), c1 - int(keep / 2 * SR)  # cut [cut0, cut1) = excess, centred
        cut0, cut1 = int((mid - (b - a - keep) / 2) * SR), int((mid + (b - a - keep) / 2) * SR)
        seg = x[pos:cut0].copy()
        tail = x[cut1:cut1 + fade]
        seg[-fade:] = seg[-fade:] * np.linspace(1, 0, fade) + tail * np.linspace(0, 1, fade)
        out.append(seg)
        pos = cut1 + fade
        removed += (cut1 - cut0) / SR
    out.append(x[pos:])
    y = np.concatenate(out)
    with wave.open(dst, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f"removed {removed:.2f}s -> {len(y) / SR:.2f}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 0.55)
