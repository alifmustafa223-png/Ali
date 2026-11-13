"""Finish the 10 s full-3D test: frames -> 1080x1920 H.264 (CRF 16), Chatterbox voice + music + foley, -14 LUFS.

  python make_cove_test.py FRAMES_DIR [out.mp4]
Voice: ../cove_test/vo_final.wav (+ .times.json word cues). Foley: whoosh as the camera starts, a coin "ting" when
she lifts it, a whoosh on the flick, ting on the catch, a soft thud + ding on "fake".
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "cove_test", "cove_test.mp4")
sys.argv = [sys.argv[0], "unused.mp4"]
sys.path.insert(0, os.path.join(HERE, ".."))
import audio  # noqa: E402

CT = os.path.join(HERE, "..", "cove_test")
DUR, FPS = 10.0, 24
vo = json.load(open(os.path.join(CT, "vo_final.wav.times.json")))
voice = os.path.join(CT, "_voice10.wav")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", os.path.join(CT, "vo_final.wav"), "-af",
                f"highpass=f=70,acompressor=threshold=0.12:ratio=2.5:attack=8:release=120,apad=whole_dur={DUR}", "-ar", "44100", voice], check=True)
t_raise, t_toss, t_fake = vo["throw"] + 0.45, vo["because"] + 0.35, vo["fake"]
events = [("whoosh", 0.1), ("ding", t_raise + 0.3), ("whoosh", t_toss), ("pop", t_toss + 0.6), ("ding", t_toss + 0.62),
          ("thud", t_fake), ("ding", t_fake + 0.05)]
music, sfx = os.path.join(CT, "_music.wav"), os.path.join(CT, "_sfx.wav")
audio.music(music, DUR, bpm=84, seed=11)
audio.sfx(sfx, DUR, events)
video = os.path.join(CT, "_video.mp4")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(FRAMES, "%04d.png"),
                "-vf", "scale=1080:1920:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-crf", "16", "-preset", "slow", video], check=True)
audio.master(video, voice, music, sfx, OUT)
print("wrote", OUT)
