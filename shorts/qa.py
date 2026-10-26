"""Automatic quality check for a finished Short.

Usage: python qa.py final.mp4 "d1,d2,..." voice.mp3   (scene durations used for the render, the voice track)
Checks length, how fast the voice starts, the first frame, unexpected black frames,
and saves a contact sheet (qa_sheet.png) with a frame from the middle of every scene.
"""
import re
import subprocess
import sys

from PIL import Image, ImageStat

video = sys.argv[1]
durs = [float(x) for x in sys.argv[2].split(",") if x] if len(sys.argv) > 2 else []
voice = sys.argv[3] if len(sys.argv) > 3 else None
ok = True


def report(name, passed, detail):
    global ok
    ok &= passed
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")


def ff(*args):
    return subprocess.run(["ffmpeg", "-hide_banner", *args], capture_output=True, text=True).stderr


def frame(t, path):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t), "-i", video, "-frames:v", "1", path], check=True)
    return Image.open(path).convert("L")


dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                           capture_output=True, text=True).stdout)
report("length 61-65s", 61 <= dur <= 65, f"{dur:.2f}s")

if voice:
    log = ff("-i", voice, "-af", "silencedetect=n=-35dB:d=0.25", "-f", "null", "-")
    sil = [(float(a), float(b)) for a, b in zip(re.findall(r"silence_start: ([0-9.]+)", log), re.findall(r"silence_end: ([0-9.]+)", log))]
    start = sil[0][1] if sil and sil[0][0] < 0.05 else 0.0
    report("voice starts fast", start <= 0.6, f"first word at {start:.2f}s (aim <= 0.6s)")
    early = [p for p in sil if 0.05 < p[0] < 1.0]
    report("no pause inside the hook's first second", not early, f"pauses: {early or 'none'}")

f0 = frame(0, "qa_f0.png")
st = ImageStat.Stat(f0)
report("first frame is not dark/empty", st.mean[0] > 18 and st.stddev[0] > 25, f"brightness {st.mean[0]:.0f}, detail {st.stddev[0]:.0f}")

blk = ff("-i", video, "-vf", "blackdetect=d=0.3:pix_th=0.08", "-an", "-f", "null", "-")
long_black = re.findall(r"black_start:([0-9.]+) black_end:([0-9.]+)", blk)
report("no long black gaps", not long_black, f"{len(long_black)} black stretch(es) >= 0.3s {long_black[:3]}")

if durs:
    mids, acc = [], 0.0
    for dd in durs:
        mids.append(acc + dd * 0.6)
        acc += dd
    tiles = [frame(m, f"qa_s{i}.png").convert("RGB").resize((216, 384)) for i, m in enumerate(mids)]
    sheet = Image.new("RGB", (216 * len(tiles), 384))
    for i, tile in enumerate(tiles):
        sheet.paste(tile, (216 * i, 0))
    sheet.save("qa_sheet.png")
    print("contact sheet: qa_sheet.png (review every tile for overlaps and cut-off art)")

print("RESULT:", "ALL PASS" if ok else "FIX NEEDED")
sys.exit(0 if ok else 1)
