"""Animation upgrade (art pass): cartoon outlines, 3D shading, backdrops and talking mouths.

`camera()` is a drop-in replacement for make_ketchup.camera that adds, automatically, to every
drawn object:
  - a dark cartoon outline around every silhouette,
  - a soft shadow band along the lower-right inner edge and a highlight along the upper-left
    (light from the top-left), so flat shapes read as rounded,
plus the same pop-in squash/stretch, slow push-in and soft drop shadow as before.
"""
import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from make_pizza import back
from make_short import H, W

OUTLINE = (30, 18, 24)


def _shift(a, dx, dy):
    out = Image.new("L", a.size, 0)
    out.paste(a, (dx, dy))
    return out


def stylize(art):
    """Outline + inner shading + highlight, computed at half resolution for speed."""
    a_full = art.getchannel("A")
    a = a_full.resize((W // 2, H // 2), Image.BILINEAR).point(lambda v: 255 if v > 140 else 0)
    ring = ImageChops.subtract(a.filter(ImageFilter.MaxFilter(5)), a)          # outline band outside
    shade = ImageChops.subtract(a, _shift(a, -6, -7)).filter(ImageFilter.GaussianBlur(3))   # lower-right inner edge
    light = ImageChops.subtract(a, _shift(a, 5, 5)).filter(ImageFilter.GaussianBlur(2))     # upper-left inner edge
    up = lambda m, k: m.resize((W, H), Image.BILINEAR).point(lambda v: int(v * k))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(OUTLINE + (255,), (0, 0), up(ring, 1.0))
    out.alpha_composite(art)
    sh = Image.new("RGBA", (W, H), (20, 10, 30, 0))
    sh.putalpha(ImageChops.multiply(up(shade, 0.42), a_full))
    out.alpha_composite(sh)
    li = Image.new("RGBA", (W, H), (255, 250, 235, 0))
    li.putalpha(ImageChops.multiply(up(light, 0.30), a_full))
    out.alpha_composite(li)
    return out


def camera(img, t, draw_fn, anchor):
    art = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(art, "RGBA"))
    art = stylize(art)
    a = art.getchannel("A").point(lambda v: v if v > 200 else 0).resize((W // 6, H // 6), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    a = a.resize((W, H), Image.BILINEAR).point(lambda v: int(v * 0.5))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 255), (0, 22), a.crop((0, 0, W, H - 22)))
    layer = Image.alpha_composite(shadow, art)
    pop = back(t / 0.5)
    wob = math.sin(min(t, 0.9) / 0.9 * math.pi * 3) * 0.06 * max(0.0, 1 - t / 0.9)
    push = 1 + 0.04 * min(t, 10) / 10
    sx = (0.88 + 0.12 * pop) * push * (1 + wob)
    sy = (0.88 + 0.12 * pop) * push * (1 - wob)
    if abs(sx - 1) > 0.002 or abs(sy - 1) > 0.002:
        scaled = layer.resize((int(W * sx), int(H * sy)), Image.BILINEAR)
        ox, oy = int(anchor[0] - anchor[0] * sx), int(anchor[1] - anchor[1] * sy)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer.paste(scaled, (ox, oy), scaled)
    img.alpha_composite(layer)


# ---------- backdrops (drawn behind the art, not outlined) ----------

def backdrop(img, kind, t=0.0):
    """Drawn on its own layer and blended in (LESSONS #5: see-through shapes drawn straight onto
    the frame replace pixels instead of blending, so they come out solid black or white)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _backdrop(ImageDraw.Draw(layer), kind, t)
    img.alpha_composite(layer)


def _backdrop(d, kind, t):
    if kind == "hall":  # stone wall with arches + checkered floor
        for row in range(14):
            y = 860 + row * 46
            off = 0 if row % 2 else 60
            for k in range(-1, 10):
                x = off + k * 120
                d.rectangle([x + 3, y + 3, x + 117, y + 43], outline=(255, 255, 255, 16), width=2)
        for k, x in enumerate((180, 540, 900)):
            d.chord([x - 110, 900, x + 110, 1140], 180, 360, fill=(0, 0, 0, 40))
            d.rectangle([x - 110, 1020, x + 110, 1380], fill=(0, 0, 0, 40))
        for row in range(6):
            y0 = 1520 + row * 70
            for k in range(10):
                if (k + row) % 2 == 0:
                    d.rectangle([k * 108, y0, k * 108 + 108, y0 + 70], fill=(255, 255, 255, 14))
    elif kind == "street":  # brick wall + cobbles
        for row in range(12):
            y = 880 + row * 50
            off = 0 if row % 2 else 70
            for k in range(-1, 9):
                x = off + k * 140
                d.rectangle([x + 4, y + 4, x + 136, y + 46], fill=(255, 255, 255, 10))
        for k in range(40):
            x, y = (k * 137) % W, 1560 + (k * 53) % 330
            d.ellipse([x - 40, y - 18, x + 40, y + 18], fill=(255, 255, 255, 12))
    elif kind == "table":  # tablecloth with a soft pattern
        d.rectangle([0, 1400, W, H], fill=(255, 255, 255, 18))
        for k in range(12):
            d.line([(k * 100, 1400), (k * 100 - 200, H)], fill=(255, 255, 255, 14), width=4)


# ---------- talking mouth driven by the voice ----------

class Talk:
    """Mouth openness 0..1 from the voice loudness at a given time."""

    def __init__(self, voice_path):
        import subprocess
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", voice_path, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
        hop = 160  # 20 ms frames
        n = len(x) // hop
        rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
        self.env = np.clip(rms / (np.percentile(rms, 95) + 1e-6), 0, 1)

    def open(self, t):
        i = int(t / 0.02)
        return float(self.env[i]) if 0 <= i < len(self.env) else 0.0


def talking_mouth(d, cx, cy, s, amount):
    """Open oval mouth that grows with `amount` (0 = closed smile line)."""
    if amount < 0.12:
        d.arc([cx - 24 * s, cy - 6 * s, cx + 24 * s, cy + 22 * s], 20, 160, fill=(110, 40, 35), width=max(2, int(6 * s)))
        return
    h = 8 + 26 * amount
    d.ellipse([cx - 20 * s, cy - h / 2 * s + 8 * s, cx + 20 * s, cy + h / 2 * s + 8 * s], fill=(90, 25, 30))
    d.ellipse([cx - 12 * s, cy + (h / 2 - 6) * s + 4 * s, cx + 12 * s, cy + (h / 2 + 2) * s + 6 * s], fill=(220, 90, 100))
