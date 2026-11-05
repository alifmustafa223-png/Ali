"""Long-form (16:9, 1920x1080) Skia engine for 10-minute "What if" videos.

Pieces:
  - Story: script paragraphs + forced-aligned word times (align_script.py) -> one SHOT per paragraph
  - Shot helpers: S.at(word, n) = seconds into the shot when that word (n-th match in the paragraph) is spoken
  - HUD: balance counter (rolls between waypoints) + phone notifications (+$1) triggered by the spoken "Plus ..."
  - Chapter cards (MONDAY...) with gold-splat transitions; hard cuts with camera moves inside a chapter
  - Post: bloom, vignette, grain (same look as the Shorts)
  - Parallel rendering: --part k/N renders a frame range; parts are concatenated without re-encoding
"""
import json
import math
import random
import re
import subprocess

import numpy as np
import skia

from toon import *  # noqa: F401,F403  (characters, props, helpers)
import toon as T

W, H, FPS = 1920, 1080, 30
FB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf")
FM = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-Medium.otf")

WORDNUM = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
           "twelve": 12, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "hundred": 100, "thousand": 1000,
           "million": 10 ** 6, "billion": 10 ** 9}


def clean(w):
    return re.sub(r"[^a-z0-9'-]", "", w.lower())


class Story:
    def __init__(self, align_json, tail=2.5):
        d = json.load(open(align_json))
        self.words = d["words"]  # [t, word, para]
        self.paras = d["paras"]
        self.length = d["length"]
        n = len(self.paras)
        # cuts: halfway through the gap before each paragraph (never inside speech)
        self.start = [0.0]
        for k in range(1, n):
            prev_end = max(t for t, w, p in self.words if p == k - 1) + 0.25
            nxt = self.paras[k][0]
            self.start.append(round(max(prev_end, (prev_end + nxt) / 2, nxt - 0.35), 3))
        self.total = round(self.length + tail, 3)
        self.end = self.start[1:] + [self.total]

    def words_of(self, k):
        return [(t, w) for t, w, p in self.words if p == k]

    def at(self, k, word, n=1, lead=0.08):
        """Seconds into shot k when `word` (prefix match on the cleaned word) is spoken for the n-th time."""
        cnt = 0
        target = clean(word)
        for t, w in self.words_of(k):
            if clean(w).startswith(target):
                cnt += 1
                if cnt == n:
                    return max(0.0, t - self.start[k] - lead)
        raise KeyError(f"'{word}' #{n} not in paragraph {k}")

    def shot_at(self, gt):
        for k in range(len(self.start)):
            if self.start[k] <= gt < self.end[k]:
                return k
        return len(self.start) - 1

    def plus_events(self):
        """Every spoken 'Plus <amount>' -> (time, amount)."""
        out = []
        ws = self.words
        for i, (t, w, p) in enumerate(ws):
            if clean(w) == "plus":
                amt, j = 0, i + 1
                cur = 0
                while j < len(ws) and clean(ws[j][1]).strip("-") in WORDNUM or (j < len(ws) and "-" in clean(ws[j][1])):
                    v = clean(ws[j][1])
                    parts = v.split("-") if "-" in v else [v]
                    for part in parts:
                        x = WORDNUM.get(part, None)
                        if x is None:
                            break
                        if x >= 100:
                            cur = max(1, cur) * x
                        else:
                            cur += x
                    j += 1
                amt = cur or 1
                out.append((t, amt))
        return out


# ---------- drawing helpers ----------

def font(size, bold=True):
    return skia.Font(FB if bold else FM, size)


def text(c, s, x, y, size, col=(255, 255, 255), a=255, align="center", bold=True, stroke=0, stroke_col=(20, 12, 10), shadow=True):
    f = font(size, bold)
    w = f.measureText(s)
    ox = x - w / 2 if align == "center" else (x - w if align == "right" else x)
    if shadow:
        c.drawString(s, ox + size * 0.04, y + size * 0.06, f, P(C(0, 0, 0, int(a * 0.55)), MaskFilter=blur(size * 0.05)))
    if stroke:
        c.drawString(s, ox, y, f, P(C(*stroke_col, a), Style=skia.Paint.kStroke_Style, StrokeWidth=stroke, StrokeJoin=skia.Paint.kRound_Join))
    c.drawString(s, ox, y, f, P(C(*col, a)))
    return w


def pop_text(c, s, x, y, size, t, at, col=(255, 255, 255), stroke=10, dur=0.32):
    """Text that pops in on a word: scale overshoot, then holds."""
    if t < at:
        return
    k = out_back((t - at) / dur, 2.0)
    a = int(255 * min(1, (t - at) / 0.12))
    c.save()
    c.translate(x, y)
    c.scale(max(0.01, k), max(0.01, k))
    text(c, s, 0, size * 0.35, size, col, a, stroke=stroke)
    c.restore()


def slam_text(c, s, x, y, size, t, at, col=(255, 200, 60), stroke=12):
    """Huge slam: falls from 2.4x scale to 1x in 0.2 s with a little shake."""
    if t < at:
        return
    p = min(1, (t - at) / 0.2)
    sc = 1 + 1.4 * (1 - ease(p))
    shake = math.sin(t * 90) * 10 * max(0.0, 1 - (t - at) / 0.4)
    c.save()
    c.translate(x + shake, y)
    c.scale(sc, sc)
    text(c, s, 0, size * 0.35, size, col, int(255 * min(1, p * 1.6)), stroke=stroke)
    c.restore()


def money(n):
    if n >= 10 ** 9:
        v = n / 10 ** 9
        return f"${v:,.1f} BILLION" if v < 10 else f"${v:,.0f} BILLION"
    if n >= 10 ** 6:
        v = n / 10 ** 6
        return f"${v:,.1f} MILLION" if v < 10 else f"${v:,.0f} MILLION"
    return f"${int(round(n)):,}"


def phone(c, x, y, s, t, screen=None, buzz=0.0, glow_col=None):
    """Smartphone centred at (x, y), height 560*s. screen(c, w, h) draws the screen content in local coords."""
    c.save()
    c.translate(x + math.sin(t * 80) * 6 * buzz, y)
    c.rotate(math.sin(t * 60) * 3 * buzz)
    c.scale(s, s)
    if glow_col:
        glow(c, 0, 0, 420, glow_col, 90)
    body = rrect(-150, -280, 150, 280, 40)
    c.drawPath(body, P(C(0, 0, 0, 120), MaskFilter=blur(18)))
    blob(c, body, (35, 38, 48), 1.6, 0.7)
    scr = rrect(-132, -255, 132, 255, 26)
    c.drawPath(scr, P(Shader=lin((0, -255), (0, 255), [C(30, 40, 70), C(15, 20, 40)])))
    c.save()
    c.clipPath(scr, doAntiAlias=True)
    c.translate(-132, -255)
    if screen:
        screen(c, 264, 510)
    c.restore()
    c.drawRoundRect(skia.Rect(-40, -268, 40, -258), 5, 5, P(C(20, 20, 25)))
    c.restore()


def notif_card(c, x, y, s, amount, a=255, label="Somebody thought of you"):
    """Bank-style notification card (no real brand)."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    r = rrect(-260, -62, 260, 62, 28)
    c.drawPath(r, P(C(0, 0, 0, int(a * 0.4)), MaskFilter=blur(14)))
    c.drawPath(r, P(C(250, 250, 252, a)))
    c.drawCircle(-200, 0, 40, P(C(40, 190, 110, a)))
    text(c, "$", -200, 16, 46, (255, 255, 255), a, shadow=False)
    text(c, f"+{money(amount)}", -140, -6, 40, (30, 140, 80), a, align="left", shadow=False)
    text(c, label, -140, 34, 26, (90, 90, 100), a, align="left", bold=False, shadow=False)
    c.restore()


class HUD:
    """Balance counter (top-right) that rolls between waypoints, + notification cards on every spoken 'Plus ...'."""

    def __init__(self, waypoints, plus_events, hidden=()):
        self.wp = sorted(waypoints)  # [(time, balance)]
        self.plus = plus_events
        self.hidden = hidden  # [(t0, t1)] ranges where the HUD is hidden

    def balance(self, gt):
        prev = (0.0, 0.0)
        for t, v in self.wp:
            if gt < t:
                k = ease((gt - prev[0]) / max(0.05, min(1.2, t - prev[0]))) if gt > t - min(1.2, t - prev[0]) else 0.0
                lo = prev[1]
                if gt < t - min(1.2, t - prev[0]):
                    return lo
                return lo + (v - lo) * ease((gt - (t - min(1.2, t - prev[0]))) / min(1.2, t - prev[0]))
            prev = (t, v)
        return prev[1]

    def draw(self, c, gt):
        if any(a <= gt < b for a, b in self.hidden):
            return
        bal = self.balance(gt)
        bump = 0.0
        for t, v in self.wp:
            if 0 <= gt - t < 0.25:
                bump = 1 - (gt - t) / 0.25
        c.save()
        c.translate(W - 60, 70)
        sc = 1 + 0.12 * bump
        c.scale(sc, sc)
        label = money(bal)
        f = font(54)
        w = max(260, f.measureText(label) + 110)
        r = rrect(-w, -46, 0, 46, 46)
        c.drawPath(r, P(C(0, 0, 0, 120), MaskFilter=blur(12)))
        c.drawPath(r, P(C(15, 30, 22, 225)))
        c.drawPath(r, S(C(70, 220, 130), 4))
        c.drawCircle(-w + 46, 0, 28, P(C(60, 210, 120)))
        text(c, "$", -w + 46, 13, 36, (10, 40, 20), shadow=False)
        text(c, label, -30, 19, 54, (235, 255, 240), align="right", shadow=False)
        c.restore()
        # notification cards stack top-left
        shown = [(t, a) for t, a in self.plus if 0 <= gt - t < 1.6]
        for i, (t, amt) in enumerate(reversed(shown[-3:])):
            k = gt - t
            slide = out_back(k / 0.3, 1.6)
            a = int(255 * min(1, (1.6 - k) / 0.3))
            notif_card(c, 330 - 400 * (1 - slide), 90 + i * 135, 1.0, amt, a)


# ---------- chapter card + transitions ----------

def chapter_card(c, t, label, sub=None, col=(255, 200, 60)):
    c.drawPaint(P(Shader=rad(W / 2, H / 2, 1100, [C(40, 20, 50), C(10, 6, 14)])))
    for k in range(16):
        a = k / 16 * 2 * math.pi + t * 0.3
        p = skia.Path()
        p.moveTo(W / 2, H / 2)
        p.lineTo(W / 2 + math.cos(a) * 1500, H / 2 + math.sin(a) * 1500)
        p.lineTo(W / 2 + math.cos(a + 0.12) * 1500, H / 2 + math.sin(a + 0.12) * 1500)
        p.close()
        c.drawPath(p, P(C(255, 220, 160, 18)))
    slam_text(c, label, W / 2, H / 2 - 30, 190, t, 0.05, col, 14)
    if sub:
        pop_text(c, sub, W / 2, H / 2 + 120, 60, t, 0.45, (255, 255, 255), 8)


_SPLAT = [(random.Random(i).uniform(0, W), random.Random(i + 99).uniform(0, H), random.Random(i + 7).uniform(140, 320)) for i in range(26)]


def splat(c, k, col=(250, 195, 50)):
    """Gold blobs covering the frame; k 0..1 (1 = fully covered)."""
    if k <= 0:
        return
    for i, (x, y, r) in enumerate(_SPLAT):
        rr = r * 1.35 * k * (0.85 + 0.15 * math.sin(i))
        c.drawCircle(x, y, rr, P(C(*col)))
        if 0.35 < k < 0.9:
            for j in range(3):
                a = i * 1.7 + j * 2.1
                c.drawCircle(x + math.cos(a) * rr * 1.3, y + math.sin(a) * rr * 1.3, rr * 0.16, P(C(*col)))
    if k > 0.93:
        c.drawPaint(P(C(*col)))


# ---------- post ----------

_g = np.random.default_rng(3)
GRAIN = []
for _ in range(6):
    n = (_g.standard_normal((H // 2, W // 2)) * 18 + 128).clip(0, 255).astype(np.uint8)
    GRAIN.append(skia.Image.fromarray(np.dstack([n, n, n, np.full_like(n, 255)]), colorType=skia.kRGBA_8888_ColorType))
BLOOM = skia.ColorFilters.Matrix([2.2, 0, 0, 0, -1.25, 0, 2.2, 0, 0, -1.25, 0, 0, 2.2, 0, -1.25, 0, 0, 0, 1, 0])


def post(surf, c, t):
    snap = surf.makeImageSnapshot()
    c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=BLOOM, ImageFilter=skia.ImageFilters.Blur(20, 20), BlendMode=skia.BlendMode.kPlus, Alphaf=0.35))
    c.drawPaint(P(Shader=rad(W / 2, H / 2, 1250, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 170)], [0, 0.55, 1])))
    c.drawImageRect(GRAIN[int(t * 30) % len(GRAIN)], skia.Rect(0, 0, W, H), skia.SamplingOptions(), P(Alphaf=0.05, BlendMode=skia.BlendMode.kOverlay))


def encoder(out, crf=18):
    return subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), "-preset", "medium", "-movflags", "+faststart", out],
                            stdin=subprocess.PIPE)
