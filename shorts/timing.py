"""Automatic scene timing from a voiceover (replaces hand-calculated cuts — see LESSONS.md #14).

    tl = Timeline("voice.mp3")
    durs = tl.plan(["okay", "in europe", ...], tail=1.3)   # first word(s) of scenes 2..N
    tl.cue("traded", scene=0)                               # seconds into scene 0 when "traded" starts

Each cut lands in the middle of the pause right before the scene's first word, so a scene always
opens just before its own sentence. Word matching is forgiving (speech recognition misspells
names), so anchor on plain words like "okay", "and", "today", "so".
"""
import json
import os
import re
import subprocess


class Timeline:
    def __init__(self, voice):
        self.voice = voice
        cache = voice + ".words.json"
        if os.path.exists(cache):
            data = json.load(open(cache))
        else:
            data = {"words": self._words(), "pauses": self._pauses()}
            json.dump(data, open(cache, "w"))
        self.words = [(t, w) for t, w in data["words"]]
        self.pauses = [tuple(p) for p in data["pauses"]]
        self.length = self._length()
        self.starts = []

    def _raw(self):
        return subprocess.run(["ffmpeg", "-loglevel", "error", "-i", self.voice, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                              capture_output=True, check=True).stdout

    def _words(self):
        from pocketsphinx import Decoder
        d = Decoder(samprate=16000)
        d.start_utt()
        d.process_raw(self._raw(), full_utt=True)
        d.end_utt()
        out = []
        for s in d.seg():
            w = re.sub(r"\(\d+\)$", "", s.word)
            if w not in ("<s>", "</s>", "<sil>", "[NOISE]", "[SPEECH]"):
                out.append((s.start_frame / 100, w))
        return out

    def _pauses(self):
        log = subprocess.run(["ffmpeg", "-hide_banner", "-i", self.voice, "-af", "silencedetect=n=-35dB:d=0.25", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
        return list(zip(map(float, re.findall(r"silence_start: ([0-9.]+)", log)), map(float, re.findall(r"silence_end: ([0-9.]+)", log))))

    def _length(self):
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", self.voice],
                             capture_output=True, text=True).stdout
        return float(out)

    def find(self, phrase, after=0.0):
        """Start time of the first occurrence of `phrase` (one or more words) after `after`."""
        target = phrase.lower().split()
        for i, (t, w) in enumerate(self.words):
            if t < after:
                continue
            if all(i + j < len(self.words) and self.words[i + j][1].startswith(tw[:4]) for j, tw in enumerate(target)):
                return t
        raise ValueError(f"'{phrase}' not found after {after:.2f}s")

    def plan(self, anchors, tail=1.3):
        """Scene durations: one cut before each anchor phrase (anchors = first words of scenes 2..N)."""
        cuts, after = [], 0.3
        for a in anchors:
            t = self.find(a, after)
            before = [p for p in self.pauses if p[1] <= t + 0.2 and p[0] >= after - 0.3]
            cut = (before[-1][0] + before[-1][1]) / 2 if before else t - 0.15
            cuts.append(cut)
            after = t + 0.3
        bounds = [0.0] + cuts + [self.length + tail]
        self.starts = bounds[:-1]
        return [round(b - a, 2) for a, b in zip(bounds, bounds[1:])]

    def cue(self, phrase, scene, lead=0.1):
        """Seconds into `scene` when `phrase` is spoken (minus a small lead so visuals land on the word)."""
        start = self.starts[scene]
        return round(self.find(phrase, start) - start - lead, 2)
