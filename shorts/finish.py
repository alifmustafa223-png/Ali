"""Mix the voiceover over a rendered video (music ducked to 30%) to make the final Short.

Usage: python finish.py base.mp4 voice.mp3 final.mp4
"""
import subprocess
import sys

base, voice, out = sys.argv[1:4]
subprocess.run([
    "ffmpeg", "-loglevel", "error", "-y", "-i", base, "-i", voice,
    "-filter_complex", "[0:a]volume=0.3[m];[m][1:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out,
], check=True)
print("wrote", out)
