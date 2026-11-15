"""Sound for the Molasses Flood Short: narration on top, foley on the animation's own cues, -14 LUFS / <= -1.5 dBTP.
  python make_audio.py FRAMES_DIR OUT.mp4
Cues: shot times / whip entries parsed from molasses.html, word times from words.json (whisper). SFX: BigSoundBank CC0
(../cove_test/sfx): 1802 whoosh | 0339 coin (ting/clink) | 0103 door (gavel / stamp thump) | 0267 waves + gulls |
3051 creaking wood | 2079 chime. Shaped by hand: wave roar, burst boom, metal groan, molasses squelch, drips, brush, rumble.
"""
import json, os, re, subprocess, sys
import numpy as np, soundfile as sf

FR, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
SFX = os.path.join(HERE, "..", "cove_test", "sfx")
WORK = os.path.join(HERE, "_audio")
os.makedirs(os.path.join(WORK, "stems"), exist_ok=True)
SR, DUR, FPS = 48000, 62.0, 30
html = open(os.path.join(HERE, "molasses.html")).read()
SHOTS = [(float(a), float(b), (re.search(r'enter: "(\w+)"', rest) or [None, "cut"])[1])
         for a, b, rest in re.findall(r"shot\(\{ t0: ([\d.]+), t1: ([\d.]+),(.*?)\n", html)]
WORDS = json.load(open(os.path.join(HERE, "words.json")))
rng = np.random.default_rng(5)


def w(word, after=0.0):
    for o in WORDS:
        if o["t0"] >= after - 0.01 and re.sub(r"[^a-z0-9]", "", o["w"].lower()) == word:
            return o["t0"]
    raise KeyError(word)


def load(name, t0=0.0, dur=None, fi=0.004, fo=0.03):
    path = os.path.join(SFX, name)
    if not os.path.exists(path):
        stem = os.path.splitext(path)[0]
        src = next(stem + e for e in (".ogg", ".mp3") if os.path.exists(stem + e))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-ac", "1", "-ar", "44100", path], check=True)
    a, sr = sf.read(path, always_2d=True)
    a = np.interp(np.arange(0, len(a), sr / SR), np.arange(len(a)), a.mean(axis=1))
    a = a[int(t0 * SR): int((t0 + dur) * SR) if dur else None].copy()
    a[:max(1, int(fi * SR))] *= np.linspace(0, 1, max(1, int(fi * SR)))
    a[-max(1, int(fo * SR)):] *= np.linspace(1, 0, max(1, int(fo * SR)))
    return a


pitch = lambda a, r: np.interp(np.arange(0, len(a), r), np.arange(len(a)), a)   # noqa: E731
db = lambda a, d: a / (np.max(np.abs(a)) + 1e-9) * 10 ** (d / 20)               # noqa: E731


def onset_of(a, thr=0.3):
    hop = int(0.002 * SR)
    e = np.array([np.abs(a[i:i + hop]).max() for i in range(0, len(a) - hop, hop)])
    return float(np.argmax(e > thr * e.max()) * hop / SR)


N = int(DUR * SR)
bus = np.zeros(N)
CUES = {}


def place(name, a, t, gain, stem=True):
    a = db(a, gain)
    i = int(round((t - onset_of(a)) * SR))
    st = np.zeros(N)
    j = max(0, i)
    a2 = a[j - i:]
    n = min(len(a2), N - j)
    if n > 0:
        st[j:j + n] = a2[:n]
    bus[:] += st
    if stem:
        k, m = name, 1
        while k in CUES:
            m += 1
            k = f"{name}#{m}"
        CUES[k] = round(t, 4)
        sf.write(os.path.join(WORK, "stems", f"{k}.wav"), st.astype(np.float32), SR)


def bed(a, t0, t1, rms):
    n = int((t1 - t0) * SR)
    a = np.tile(a, n // len(a) + 1)[:n].copy()
    f = min(n // 4, int(0.25 * SR))
    a[:f] *= np.linspace(0, 1, f)
    a[-f:] *= np.linspace(1, 0, f)
    a = a / (np.sqrt(np.mean(a ** 2)) + 1e-9) * 10 ** (rms / 20)
    i0 = int(t0 * SR)
    bus[i0:i0 + n] += a[:N - i0]


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def roar(d):          # the wave: deep rumble + a wet hiss
    n = int(d * SR)
    return 1.0 * lowpass(rng.normal(0, 1, n), 400) * 25 + 0.25 * (rng.normal(0, 1, n) - lowpass(rng.normal(0, 1, n), 4))


def boom(d=2.0):
    tt = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * (36 * tt + 4 * (1 - np.exp(-tt * 6)))) * np.exp(-tt * 2.4) + 0.7 * lowpass(rng.normal(0, 1, len(tt)), 50) * np.exp(-tt * 3.5) * 3 \
        + 0.4 * rng.normal(0, 1, len(tt)) * np.exp(-tt * 28)


def groan(d=1.4):     # stressed steel: slow low tone with beating
    tt = np.arange(int(d * SR)) / SR
    f = 70 + 25 * np.sin(2 * np.pi * 0.7 * tt)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 2.02) / SR)) * np.minimum(1, tt / 0.3) * np.minimum(1, (d - tt) / 0.3)


def squelch():
    tt = np.arange(int(0.35 * SR)) / SR
    f = 160 + 260 * np.exp(-tt * 9)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 8) * (1 + 0.5 * np.sin(2 * np.pi * 31 * tt))


def drip():
    tt = np.arange(int(0.22 * SR)) / SR
    return np.sin(2 * np.pi * np.cumsum(900 + 700 * np.exp(-tt * 40)) / SR) * np.exp(-tt * 20)


def brush():
    n = int(0.32 * SR)
    x = rng.normal(0, 1, n) - lowpass(rng.normal(0, 1, n), 8)
    return x * np.sin(np.pi * np.arange(n) / n) ** 2


whoosh = load("bsb_1802.wav", 0, None, 0.003, 0.05)
ting = load("bsb_0339.wav", 0, 0.6, 0.002, 0.25)
door = load("bsb_0103.wav", 1.85, 0.9, 0.003, 0.3)
creak = load("bsb_3051.wav", 0.2, 0.9, 0.01, 0.2)
chime = load("bsb_2079.wav", 0, 2.2, 0.01, 0.6)
sea = load("bsb_0267.wav", 5.0, 12.0, 0.4, 0.5)

for a, b, enter in SHOTS[1:]:
    if enter in ("whip", "zoom"):
        place("whoosh", pitch(whoosh, 1.0 if enter == "whip" else 1.35), a - 4 / FPS, -15 if enter == "whip" else -19)
tb = w("burst")
bed(roar(3.6), 0.0, 3.5, -22)                      # hook: the wave is already roaring
place("groan", groan(1.3), tb - 1.3, -20)
place("burst_boom", boom(2.2), tb, -6)
bed(roar(3.2), tb + 0.1, 6.65, -24)
bed(roar(3.2), 6.6, 9.85, -21)
bed(roar(2.9), 9.8, 12.65, -21)
place("collapse", boom(1.8), 10.15, -9)
for k in range(6):
    place("debris", pitch(ting, rng.uniform(0.35, 0.6)), 10.5 + k * rng.uniform(0.08, 0.15), -25, stem=k == 0)
place("railcar_creak", creak, 10.25, -18)
for k, t in enumerate(np.arange(12.8, 15.9, 0.55)):
    place("squelch", pitch(squelch(), rng.uniform(0.85, 1.2)), t + rng.uniform(-0.05, 0.05), -21, stem=k == 0)
bed(sea, 19.4, 22.0, -30)
for k, t in enumerate(np.arange(24.3, 27.5, 0.62)):
    place("drip", drip(), t, -24, stem=k == 0)
for k, t in enumerate(np.arange(27.8, 30.1, 0.42)):
    place("brush", brush(), t, -26, stem=k == 0)
place("paper", pitch(whoosh, 1.5), 35.2, -19)
place("gavel", pitch(door, 1.25), w("buy", 38.2), -9)
place("coins", pitch(ting, 1.0), w("paid", 40.4), -16)
place("stamp", pitch(door, 1.45), w("sign", 45.0), -11)
place("chime_sweet", chime, w("sweet", 50.0), -18)
rumble = roar(2.6) * np.linspace(0, 1, int(2.6 * SR)) ** 2
bed(rumble, 59.4, 62.0, -24)                       # builds into the loop (the hook's roar)

v, vsr = sf.read(os.path.join(HERE, "voice.wav"), always_2d=True)
v = np.interp(np.arange(0, len(v), vsr / SR), np.arange(len(v)), v.mean(axis=1))
vb = np.zeros(N)
vb[:min(N, len(v))] = v[:N]
sf.write(os.path.join(WORK, "sfx.wav"), bus.astype(np.float32), SR)
sf.write(os.path.join(WORK, "voice.wav"), vb.astype(np.float32), SR)
json.dump(CUES, open(os.path.join(WORK, "cues.json"), "w"), indent=1)
pre = os.path.join(WORK, "premix.wav")
fc = ("[0:a]highpass=f=75,acompressor=threshold=0.1:ratio=2.5:attack=6:release=120,asplit=2[v][vk];"
      "[1:a][vk]sidechaincompress=threshold=0.05:ratio=3:attack=10:release=250[s];[v][s]amix=inputs=2:normalize=0:duration=longest[m]")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", os.path.join(WORK, "voice.wav"), "-i", os.path.join(WORK, "sfx.wav"),
                "-filter_complex", fc, "-map", "[m]", "-ar", str(SR), pre], check=True)


def measure(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])


video = os.path.join(WORK, "video.mp4")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(FR, "%04d.jpg"), "-c:v", "libx264", "-crf", "16",
                "-preset", "slow", "-pix_fmt", "yuv420p", "-t", f"{DUR:.3f}", video], check=True)
I0, _ = measure(pre)
gain, ceil = -14.0 - I0, -3.1
mast = os.path.join(WORK, "master.wav")
for it in range(8):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", pre, "-af",
                    f"volume={gain:.3f}dB,alimiter=limit={10 ** (ceil / 20):.4f}:attack=1:release=60:level=disabled:asc=1", "-ar", str(SR), mast], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-i", mast, "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                    "-t", f"{DUR:.3f}", "-movflags", "+faststart", OUT], check=True)
    I, TP = measure(OUT)
    print(f"master pass {it}: {I} LUFS {TP} dBTP", flush=True)
    if abs(I + 14) <= 0.2 and TP <= -1.5:
        break
    gain += -14.0 - I
    if TP > -1.5:
        ceil -= (TP + 1.5) + 0.2
print("cues", len(CUES), "-> wrote", OUT)
