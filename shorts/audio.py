"""Sound upgrade (added for the popcorn video): real background music, sound effects, ducking
and loudness mastering.

    music("music.wav", 62.5)
    sfx("sfx.wav", 62.5, [("whoosh", 4.6), ("thud", 1.4), ("pop", 8.2), ...])
    master("base.mp4", "voice.mp3", "music.wav", "sfx.wav", "final.mp4")

The music ducks automatically under the narrator (sidechain compression) and the final mix is
normalised to YouTube's loudness target (-14 LUFS) so every video plays at the same volume.
"""
import subprocess
import wave

import numpy as np

SR = 44100


def _write(path, x):
    x = np.clip(x, -1, 1)
    data = (np.stack([x, x], axis=1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def _env(n, decay):
    t = np.arange(n) / SR
    return np.exp(-t * decay)


def _tone(freq, dur, decay, harm=0.3):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * freq * t) + harm * np.sin(4 * np.pi * freq * t)) * _env(n, decay)


def _add(buf, start, sig, gain=1.0):
    i = int(start * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain


def music(path, dur, bpm=100, seed=1):
    """Light, upbeat loop: plucked arpeggio, bass, soft pad, kick/clap/hats (Am-F-C-G)."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    buf = np.zeros(n)
    beat = 60 / bpm
    chords = [(110.0, (220.0, 261.63, 329.63)), (87.31, (174.61, 220.0, 261.63)),
              (130.81, (261.63, 329.63, 392.0)), (98.0, (196.0, 246.94, 293.66))]
    t = 0.0
    k = 0
    while t < dur:
        root, notes = chords[(k // 8) % 4]
        _add(buf, t, _tone(root, beat * 0.95, 3.0, 0.2), 0.16)  # bass on every beat
        for e in range(2):  # plucked arpeggio, eighth notes
            note = notes[(k * 2 + e) % 3] * (2 if (k // 4) % 2 else 1)
            _add(buf, t + e * beat / 2, _tone(note, 0.45, 7.0, 0.35), 0.07)
        if k % 8 == 0:  # soft pad, one per chord
            for f in notes:
                pad = np.sin(2 * np.pi * f * np.arange(int(beat * 8 * SR)) / SR)
                fade = np.minimum(1, np.arange(len(pad)) / (SR * 0.6)) * np.minimum(1, (len(pad) - np.arange(len(pad))) / (SR * 0.6))
                _add(buf, t, pad * fade, 0.018)
        if k % 2 == 0:  # kick on 1 and 3
            kn = int(0.25 * SR)
            kt = np.arange(kn) / SR
            freq = 45 + 85 * np.exp(-kt * 25)
            _add(buf, t, np.sin(2 * np.pi * np.cumsum(freq) / SR) * _env(kn, 14), 0.42)
        else:  # clap on 2 and 4
            cn = int(0.18 * SR)
            _add(buf, t, rng.standard_normal(cn) * _env(cn, 22), 0.07)
        hn = int(0.05 * SR)  # hats on the off-beats
        hat = np.diff(rng.standard_normal(hn + 1)) * _env(hn, 70)
        _add(buf, t + beat / 2, hat, 0.035)
        t += beat
        k += 1
    fade_in = np.minimum(1, np.arange(n) / (SR * 0.25))
    fade_out = np.minimum(1, (n - np.arange(n)) / (SR * 2.0))
    buf *= fade_in * fade_out
    _write(path, buf / (np.abs(buf).max() + 1e-9) * 0.8)


def _whoosh(rng):
    n = int(0.42 * SR)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    acc = 0.0
    for i in range(n):  # low-pass filter that opens then closes = sweeping "whoosh"
        a = 0.02 + 0.25 * np.sin(np.pi * i / n) ** 2
        acc += a * (noise[i] - acc)
        out[i] = acc
    return out * np.sin(np.pi * np.arange(n) / n) ** 2 * 2.2


def _thud(rng):
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    freq = 42 + 110 * np.exp(-t * 14)
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 8)
    click = np.zeros(n)
    click[: int(0.01 * SR)] = rng.standard_normal(int(0.01 * SR)) * 0.6
    return body + click


def _pop():
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    freq = 500 + 700 * (t / t[-1])
    return np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 45)


def _click(rng):
    n = int(0.03 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2200 * t) * 0.6 + rng.standard_normal(n) * 0.3) * np.exp(-t * 160)


def _ding():
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1318.5 * t) + 0.6 * np.sin(2 * np.pi * 1975.5 * t)) * np.exp(-t * 3.5) * 0.5


def sfx(path, dur, events, seed=2):
    """events: list of (kind, time) with kind in whoosh/thud/pop/click/ding."""
    rng = np.random.default_rng(seed)
    buf = np.zeros(int(dur * SR))
    gains = {"whoosh": 0.22, "thud": 0.55, "pop": 0.22, "click": 0.35, "ding": 0.25}
    for kind, t in events:
        sig = {"whoosh": lambda: _whoosh(rng), "thud": lambda: _thud(rng), "pop": _pop,
               "click": lambda: _click(rng), "ding": _ding}[kind]()
        start = t - (0.25 if kind == "whoosh" else 0.0)  # whoosh peaks right at the cut
        _add(buf, max(0.0, start), sig, gains[kind])
    _write(path, buf)


def master(video, voice, music_wav, sfx_wav, out):
    """Voice + ducked music + sound effects, normalised to -14 LUFS, over the rendered video."""
    flt = ("[1:a]aformat=channel_layouts=stereo,asplit=2[v][vsc];"
           "[2:a]volume=0.5[m];"
           "[m][vsc]sidechaincompress=threshold=0.02:ratio=6:attack=20:release=400[md];"
           "[v][md][3:a]amix=inputs=3:normalize=0:duration=longest[mix];"
           "[mix]loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    # two-pass loudness: measure first, then normalise with the measured values (one pass landed at -16.6)
    import json, re
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", video, "-i", voice, "-i", music_wav, "-i", sfx_wav,
                          "-filter_complex", flt.replace("loudnorm=I=-14:TP=-1.5:LRA=11", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json"),
                          "-map", "[a]", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(re.findall(r"\{[^{}]*\}", log)[-1])
    flt = flt.replace("loudnorm=I=-14:TP=-1.5:LRA=11", "loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={input_i}:measured_TP={input_tp}:"
                      "measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}".format(**m))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-i", voice, "-i", music_wav, "-i", sfx_wav,
                    "-filter_complex", flt, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "44100", "-shortest", "-movflags", "+faststart", out], check=True)
