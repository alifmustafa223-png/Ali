"""Shared engine for full Shorts in the APPROVED 2D "Classic+" style (owner approved 2026-11-13).

Everything here is the approved test's look, extracted so every scene matches it exactly:
  - world drawn at 1.25x (1350x2400), camera = crop (zoom >= 1 never upsamples)
  - the hero frame's blend (premultiplied skia colour blended with alpha again - see LESSONS 154)
  - characters: cast shadow, cel shade, warm rim light, optional bounce light
  - finish: bloom, teal-shadow / warm-highlight grade, vignette, animated grain
  - title slams (1.7x -> 1x with a bounce over ~6 frames) in screen space, measured to fit
"""
import math
import random

import numpy as np
import skia
from PIL import Image, ImageFilter

import toon as T

FPS = 30
W, H = 1080, 1920
K = 1.25
WW, WH = int(W * K), int(H * K)
C, P, S = T.C, T.P, T.S
BLUR = lambda r: skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r)  # noqa: E731
FB = T.FB


# ------------------------------------------------------------------ timing helpers
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(x):
    return T.ease(x)


def ramp(t, t0, dur):
    return smooth((t - t0) / dur)


def snap(t, t0, frames=6, over=1.4):
    """0 -> 1 over `frames` frames with a small overshoot. Never a 1-frame jump."""
    return T.out_back((t - t0) / (frames / FPS), over)


def lerp(a, b, u):
    return a + (b - a) * u


def lerp2(a, b, u):
    return tuple(lerp(x, y, u) for x, y in zip(a, b))


_NOISE = {}


def noise1(t, seed, speed=1.0):
    """Smooth value noise in [-1, 1]."""
    if seed not in _NOISE:
        r = random.Random(seed)
        _NOISE[seed] = [r.uniform(-1, 1) for _ in range(256)]
    kn = _NOISE[seed]
    x = t * speed
    i = int(math.floor(x))
    u = (1 - math.cos(math.pi * (x - i))) / 2
    return lerp(kn[i % 256], kn[(i + 1) % 256], u)


# ------------------------------------------------------------------ surfaces + blending
def surf(world=True):
    s = skia.Surface(WW, WH) if world else skia.Surface(W, H)
    c = s.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    if world:
        c.scale(K, K)
    return s, c


def arr(s):
    return s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32) / 255.0


def over(dst, src):
    """The approved hero blend (alpha applied twice on premultiplied skia colour). Do not 'fix' it: LESSONS 154."""
    a = src[..., 3:4]
    dst[..., :3] = src[..., :3] * a + dst[..., :3] * (1 - a)
    dst[..., 3:4] = a + dst[..., 3:4] * (1 - a)
    return dst


def gblur(x, r):
    im = Image.fromarray(np.clip(x * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255.0


def path(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def blank():
    return np.zeros((WH, WW, 4), np.float32)


# ------------------------------------------------------------------ characters
def draw_person(look, x, y, s_, pose, t, extra=None):
    s, c = surf()
    T.person(c, x, y, s_, look, pose, t)
    if extra:
        extra(c)
    return arr(s)


def light_char(ch, img, yfeet, bounce=None, shadow=0.55, shadow_dx=-18, rim_col=(1.0, 0.75, 0.45), rim=0.55):
    """Cast shadow onto img, then cel shade + rim (+ optional bounce light map) on the character; composite."""
    A = ch[..., 3]
    if shadow > 0:
        sil = Image.fromarray((A * 255).astype(np.uint8))
        h0 = int(yfeet * K)
        h0 = max(2, min(WH, h0))
        top = sil.crop((0, 0, WW, h0)).transpose(Image.FLIP_TOP_BOTTOM).resize((WW, max(1, int(h0 * 0.28))))
        sh = Image.new("L", (WW, WH), 0)
        sh.paste(top, (int(shadow_dx * K), h0 - int(6 * K)))
        sh = np.asarray(sh.filter(ImageFilter.GaussianBlur(9 * K))).astype(np.float32) / 255
        img[..., :3] *= (1 - shadow * sh[..., None] * np.array([1.0, 1.05, 0.9], np.float32))
    dx, dy = int(14 * K), int(10 * K)
    shade = np.clip(A - np.roll(np.roll(A, -dy, 0), dx, 1), 0, 1)
    shade = gblur(np.dstack([shade] * 4), 1.2 * K)[..., 0]
    ch[..., :3] *= (1 - 0.32 * shade[..., None] * np.array([1.0, 0.95, 0.75], np.float32))
    rm = np.clip(A - np.roll(np.roll(A, int(7 * K), 0), -int(9 * K), 1), 0, 1)
    ch[..., :3] = np.clip(ch[..., :3] + rim * rm[..., None] * np.array(rim_col, np.float32), 0, 1)
    if bounce is not None:
        ch[..., :3] = np.clip(ch[..., :3] + bounce[..., None] * 0.25 * np.array([1.0, 0.75, 0.3], np.float32) * A[..., None], 0, 1)
    return over(img, ch)


def glow_map(cx, cy, rx, ry):
    yy, xx = np.mgrid[0:WH, 0:WW].astype(np.float32) / K
    return np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)).astype(np.float32)


# ------------------------------------------------------------------ camera
def catmull(keys, t):
    ts = [k[0] for k in keys]
    i = max(0, min(len(keys) - 2, int(np.searchsorted(ts, t, side="right")) - 1))
    p0, p1, p2, p3 = keys[max(0, i - 1)], keys[i], keys[i + 1], keys[min(len(keys) - 1, i + 2)]
    u = 0 if p2[0] == p1[0] else clamp((t - p1[0]) / (p2[0] - p1[0]))
    out = []
    for j in range(1, len(p1)):
        a, b, c_, d = p0[j], p1[j], p2[j], p3[j]
        out.append(0.5 * ((2 * b) + (-a + c_) * u + (2 * a - 5 * b + 4 * c_ - d) * u * u + (-a + 3 * b - 3 * c_ + d) * u ** 3))
    return out


def crop(img, z, cx, cy, shake=(0, 0)):
    vw, vh = W / z, H / z
    x0 = min(max(0, cx - vw / 2 + shake[0]), W - vw) * K
    y0 = min(max(0, cy - vh / 2 + shake[1]), H - vh) * K
    src = Image.fromarray(np.clip(img[..., :3] * 255, 0, 255).astype(np.uint8))
    fr = src.transform((W, H), Image.EXTENT, (x0, y0, x0 + vw * K, y0 + vh * K), resample=Image.BICUBIC)
    return np.asarray(fr).astype(np.float32) / 255.0


# ------------------------------------------------------------------ titles (screen space)
def fit_size(txt, size, maxw=960):
    while skia.Font(FB, size).measureText(txt) > maxw:
        size -= 2
    return size


def title_layer(t, lines):
    """lines: [(text, size, baseline_y, gradient_colours, t_slam)]. Each slams in on its own word."""
    s, c = surf(world=False)
    for txt, size, y, grad, at in lines:
        k = t - at
        if k < 0:
            continue
        size = fit_size(txt, size)
        u = T.out_back(k / (6 / FPS), 2.2)
        sc = 1.7 - 0.7 * u
        a = min(1.0, k / (3 / FPS))
        f = skia.Font(FB, size)
        w = f.measureText(txt)
        x0 = (W - w) / 2
        c.save()
        c.translate(W / 2, y - size * 0.35)
        c.scale(sc, sc)
        c.translate(-W / 2, -(y - size * 0.35))
        c.saveLayerAlpha(None, int(255 * a))
        c.drawString(txt, x0 + 6, y + 8, f, P(C(10, 0, 20, 160), MaskFilter=BLUR(6)))
        c.drawString(txt, x0, y, f, S(C(25, 10, 30), size * 0.17))
        c.drawString(txt, x0, y, f, P(Shader=T.lin((0, y - size), (0, y), grad)))
        c.restore()
        c.restore()
    return arr(s)


WHITE = [C(255, 255, 255), C(235, 225, 255)]
GOLD = [C(255, 236, 140), C(255, 170, 40)]
RED = [C(255, 120, 110), C(220, 30, 40)]


def stamp_layer(t, txt, at, x, y, size=120, col=(220, 35, 45), rot=-8):
    """A rubber stamp that slams down (scale 2.2 -> 1 in 5 frames) with a slight rotation, rough ink edge."""
    s, c = surf(world=False)
    k = t - at
    if k >= 0:
        size = fit_size(txt, size, 860)
        u = T.out_back(k / (5 / FPS), 1.6)
        sc = 2.2 - 1.2 * u
        a = min(1.0, k / (2 / FPS))
        f = skia.Font(FB, size)
        w = f.measureText(txt)
        c.save()
        c.translate(x, y)
        c.rotate(rot)
        c.scale(sc, sc)
        c.saveLayerAlpha(None, int(235 * a))
        box = skia.Rect(-w / 2 - 34, -size * 0.95, w / 2 + 34, size * 0.32)
        c.drawRoundRect(box, 18, 18, S(C(*col), 12))
        c.drawString(txt, -w / 2, 0, f, P(C(*col)))
        r = random.Random(len(txt))
        for i in range(70):   # ink gaps
            c.drawCircle(r.uniform(box.left(), box.right()), r.uniform(box.top(), box.bottom()), r.uniform(1.5, 5), P(C(0, 0, 0, 0), BlendMode=skia.BlendMode.kClear))
        c.restore()
        c.restore()
    return arr(s)


def comp_screen(rgb, lay):
    return rgb * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4]


# ------------------------------------------------------------------ finish
_VIG = None


def finish(rgb, f, bloom=1.0):
    global _VIG
    if _VIG is None:
        oy, ox = np.mgrid[0:H, 0:W].astype(np.float32)
        _VIG = (1 - 0.42 * np.clip((((ox - W / 2) / (W * 0.75)) ** 2 + ((oy - H * 0.56) / (H * 0.62)) ** 2), 0, 1))[..., None]
    bright = np.clip((rgb - 0.72) / 0.28, 0, 1) * rgb
    b4 = np.dstack([bright, np.ones((H, W, 1), np.float32)])
    rgb = rgb + bloom * (0.55 * gblur(b4, 22)[..., :3] + 0.25 * gblur(b4, 6)[..., :3])
    lum = rgb.mean(axis=2, keepdims=True)
    rgb = rgb + (1 - lum) * 0.04 * np.array([-0.4, 0.0, 0.6], np.float32) + lum * 0.05 * np.array([0.6, 0.2, -0.5], np.float32)
    rgb = rgb * _VIG
    rgb = rgb + np.random.default_rng(1000 + f).normal(0, 0.010, (H, W, 1)).astype(np.float32)
    return np.clip(rgb, 0, 1)


def save(rgb, out):
    Image.fromarray(np.clip(rgb * 255, 0, 255).astype(np.uint8)).save(out)
