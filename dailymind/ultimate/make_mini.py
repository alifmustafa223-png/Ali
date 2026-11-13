"""Sound + finishing for the miniature samples (no narration): music bed, miniature foley, a brand sting, -14 LUFS.

Usage (in dailymind/ultimate): python make_mini.py S2B [in.mp4] [out.mp4]
Defaults: ../miniature/renders/S2B.mp4 -> ../miniature/S2B_final.mp4
S2B foley: the watch ticks every second, ticks accelerate into a whirr when the hands spin (7.0 s), a soft chime as
each street lamp is lit, a low swell as night falls. A small gold "The DailyMind." sting fades in over the last 1.2 s.
"""
import os
import subprocess
import sys

sys.argv = [sys.argv[0]] + sys.argv[1:]
SAMPLE = sys.argv[1] if len(sys.argv) > 1 else "S2B"
HERE = os.path.dirname(os.path.abspath(__file__))
IN = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "miniature", "renders", f"{SAMPLE}.mp4")
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "..", "miniature", f"{SAMPLE}_final.mp4")
sys.argv = [sys.argv[0], "unused.mp4"]
sys.path.insert(0, os.path.join(HERE, ".."))
import audio  # noqa: E402

WORK = os.path.join(HERE, "..", "miniature", "_work")
os.makedirs(WORK, exist_ok=True)
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", IN]).decode())

EVENTS = {
    "S3": lambda: ([("thud", k * 1.25 + 0.74) for k in range(10)] + [("click", k * 1.25 + 0.6) for k in range(10)] +
                   [("pop", k * 1.25 + 0.78) for k in range(10)] + [("whoosh", 7.7), ("ding", dur - 1.0)]),
    "S2B": lambda: ([("click", float(s)) for s in range(0, 7)] +
                    [("click", 7.0 + 0.9 * (1 - 0.82 ** k) / 0.18 * 0.25) for k in range(26)] +
                    [("whoosh", 7.2), ("whoosh", 7.9), ("thud", 7.4)] +
                    [("ding", t) for t in (8.6, 10.0, 11.0, 11.7)] + [("pop", 8.4 + 0.22 * k) for k in range(8)] + [("ding", dur - 1.0)]),
}

events = [(k, round(t, 3)) for k, t in EVENTS[SAMPLE]() if 0 <= t < dur]
music = os.path.join(WORK, f"{SAMPLE}_music.wav")
sfx = os.path.join(WORK, f"{SAMPLE}_sfx.wav")
silence = os.path.join(WORK, "silence.wav")
audio.music(music, dur, bpm=78, seed=5)
audio.sfx(sfx, dur, events)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono", "-t", str(dur), silence], check=True)
# brand sting: small gold wordmark + tagline fading in over the last 1.2 s
font = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
st = dur - 1.2
draw = (f"drawtext=fontfile={font}:text='The DailyMind.':fontcolor=0xFFC83C:fontsize=72:x=(w-text_w)/2:y=h*0.80:"
        f"alpha='if(lt(t,{st}),0,min(1,(t-{st})/0.5))':shadowcolor=black@0.6:shadowx=3:shadowy=3,"
        f"drawtext=fontfile={font}:text='Ever wondered where everyday things came from?':fontcolor=white:fontsize=34:x=(w-text_w)/2:y=h*0.80+90:"
        f"alpha='if(lt(t,{st + 0.2}),0,min(1,(t-{st + 0.2})/0.5))':shadowcolor=black@0.6:shadowx=2:shadowy=2")
branded = os.path.join(WORK, f"{SAMPLE}_branded.mp4")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", IN, "-vf", draw, "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p",
                branded], check=True)
pre = os.path.join(WORK, f"{SAMPLE}_premaster.mp4")
audio.master(branded, silence, music, sfx, pre)
# with no voice, sharp foley peaks (press thuds) can stop the linear loudnorm short of -14 (S3 landed at -16.4):
# limit the peaks, then normalise again
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", pre, "-af", "alimiter=limit=0.5:level=disabled,loudnorm=I=-14:TP=-1.5:LRA=11",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", OUT], check=True)
print("wrote", OUT)
