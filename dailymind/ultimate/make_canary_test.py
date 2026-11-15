"""10 s test: flat 2D white stickmen (thick black outlines, big faces) inside 3D miniature mine-tunnel plates.

  python make_canary_test.py PLATE_DIR OUT.mp4
Story: "This tiny bird? It had a JOB... in a coal mine. Because if the canary STOPPED singing... the miners had about
TWO MINUTES... to RUN!"  Voice: ../canary_test/vo.wav (Chatterbox). Word cues from timing.Timeline (pocketsphinx).
Physics: the cage swings as a damped pendulum (L = 0.3 m); the flying helmet is ballistic (g scaled to the frame).
"""
import json
import math
import os
import random
import subprocess
import sys

import numpy as np
import skia
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import stick as K  # noqa: E402

PLATES, OUT = sys.argv[1], sys.argv[2]
CT = os.path.join(HERE, "..", "canary_test")
FPS, DUR = 30, 10.0
NF = int(FPS * DUR)
W, H = 1080, 1920
BASE = 1.3                                   # plates are upscaled 1.3x so the camera can push in without going soft
BW, BH = int(W * BASE), int(H * BASE)
sys_argv = sys.argv
sys.argv = [sys.argv[0], "unused.mp4"]
import audio  # noqa: E402
import timing  # noqa: E402

tl = timing.Timeline(os.path.join(CT, "vo.wav"))
T_JOB, T_STOP, T_TWO, T_RUN = tl.find("job"), tl.find("stop"), tl.find("two"), tl.find("run")
print("cues", T_JOB, T_STOP, T_TWO, T_RUN)
S1, S2 = 3.3, 6.1                            # scene cuts (between the narration lines)
FB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf")
hook = json.load(open(os.path.join(PLATES, "plate_B.json")))["hook_px"]


def plate(name):
    im = Image.open(os.path.join(PLATES, f"plate_{name}.png")).convert("RGB").resize((BW, BH), Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255.0


PL = {k: plate(k) for k in "ABC"}


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def out_back(x, s=1.9):
    x = max(0.0, min(1.0, x)) - 1
    return 1 + x * x * ((s + 1) * x + s)


def lerp(a, b, k):
    return a + (b - a) * k


def layer():
    s = skia.Surface(BW, BH)
    c = s.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    c.scale(BASE, BASE)                     # draw in 1080x1920 "world" units
    return s, c


def rgba(s):
    return s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32) / 255.0


def over(dst, src):
    a = src[..., 3:4]
    return src[..., :3] * a + dst * (1 - a)


def shadow_of(a, dx, dy, blur, opacity):
    sh = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    sh = np.roll(np.roll(np.asarray(sh).astype(np.float32) / 255.0, int(dy * BASE), 0), int(dx * BASE), 1)
    return sh * opacity


def camera(world, zoom, cx, cy, shake=(0.0, 0.0, 0.0), whip=0.0):
    """Sample the world (BW x BH) into the 1080x1920 frame: zoom about world point (cx, cy) in 1080-space units."""
    im = Image.fromarray(np.clip(world * 255, 0, 255).astype(np.uint8))
    z = zoom * BASE
    ang = math.radians(shake[2])
    ca, sa = math.cos(ang) / z, math.sin(ang) / z
    ox, oy = cx * BASE + shake[0] * BASE, cy * BASE + shake[1] * BASE
    # output (u, v) -> input (x, y)
    a, b = ca, -sa
    d, e = sa, ca
    c0 = ox - (a * W / 2 + b * H / 2)
    f0 = oy - (d * W / 2 + e * H / 2)
    frame = im.transform((W, H), Image.AFFINE, (a, b, c0, d, e, f0), resample=Image.BICUBIC)
    if whip > 0:
        k = int(1 + whip * 90)
        arr = np.asarray(frame).astype(np.float32)
        acc = np.zeros_like(arr)
        for i in range(0, k, max(1, k // 12)):
            acc += np.roll(arr, i, axis=1)
        arr = acc / len(range(0, k, max(1, k // 12)))
        frame = Image.fromarray(arr.astype(np.uint8))
    return frame


def text_pop(c, txt, t, t0, y, size, col, shake=0.0, fade=False):
    if t < t0:
        return
    k = (t - t0) / 0.2
    sc = out_back(k) if not fade else 1.0
    al = 255 if not fade else int(255 * ease((t - t0) / 0.5))
    f = skia.Font(FB, size)
    w = f.measureText(txt)
    if w > 900:                               # never wider than the safe area
        size *= 900 / w
        f = skia.Font(FB, size)
        w = f.measureText(txt)
    c.save()
    jx = shake * math.sin(t * 70) if t - t0 < 0.5 else 0.0
    c.translate(W / 2 + jx, y)
    c.scale(sc, sc)
    c.drawString(txt, -w / 2 + 6, 8, f, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, int(al * 0.6)),
                                                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
    c.drawString(txt, -w / 2, 0, f, K.S(skia.Color(12, 8, 10, al), size * 0.2))
    p = skia.Paint(AntiAlias=True, Color=skia.Color(*col, al))
    c.drawString(txt, -w / 2, 0, f, p)
    c.restore()


def dust(c, t, n, seed, col=(255, 220, 160)):
    r = random.Random(seed)
    for k in range(n):
        x0, y0, sp, ph = r.uniform(0, W), r.uniform(200, 1700), r.uniform(8, 25), r.uniform(0, 6.28)
        x = (x0 + sp * t + 20 * math.sin(t * 0.7 + ph)) % W
        y = y0 - 10 * t + 15 * math.sin(t * 0.5 + ph * 2)
        a = int(120 + 100 * math.sin(t * 2 + ph))
        c.drawCircle(x, y, r.uniform(1.2, 3.2), skia.Paint(AntiAlias=True, Color=skia.Color(*col, max(0, a))))


def pickaxe(c, hx, hy, ang):
    c.save()
    c.translate(hx, hy)
    c.rotate(ang)
    c.drawLine(0, 20, 0, -150, K.S(K.BLACK, 16))
    c.drawLine(0, 20, 0, -150, K.S(skia.Color(150, 100, 55), 9))
    head = skia.Path()
    head.moveTo(-80, -140)
    head.quadTo(0, -175, 80, -140)
    head.quadTo(0, -160, -80, -140)
    c.drawPath(head, K.S(K.BLACK, 16))
    c.drawPath(head, K.S(skia.Color(160, 160, 165), 8))
    c.restore()


def run_pose(t, ph, panic=1.0):
    w = 2 * math.pi * 3.0 * t + ph
    sw = math.sin(w)
    return dict(eyes="wide", brows="up", mouth="scream", look=(0, -0.2), lean=-6 + 3 * math.sin(2 * w),
                legs=[(32 * sw, 35 + 30 * max(0, -sw)), (-32 * sw, 35 + 30 * max(0, sw))],
                arms=[(150 + 25 * math.sin(w * 2.0), 30 + 20 * math.cos(w * 2)), (130 - 30 * math.sin(w * 2.0 + 1), -20 + 25 * math.sin(w * 2 + 2))],
                head_tilt=6 * math.sin(w), sweat=0.7)


def frame(i):
    t = i / FPS
    s, c = layer()
    sh_s, sh_c = layer()
    if t < S1:                                                    # ---- scene 1: the proud miner + his singing canary
        k = (t - 0.0) / S1
        hop = math.exp(-((t - T_JOB) / 0.12) ** 2) * 28 if t > T_JOB - 0.3 else 0.0
        breath = 4 * math.sin(t * 2.6)
        after = ease((t - T_JOB + 0.1) / 0.2)
        pose = dict(eyes="happy" if t < T_JOB else "open", brows="proud" if t < T_JOB else "up", mouth="grin",                     arms=[(38, 115), (112 - 5 * math.sin(t * 2), -18)], head_tilt=-6 + 3 * math.sin(t * 1.3), lean=-2, look=(0.9, -0.2))
        for cc in (c, sh_c):
            hands = K.miner(cc, 500, 1640 - hop - breath * 0.3, 2.25, pose)
        hx, hy = hands["R"]
        hx, hy = hx / BASE, hy / BASE
        sw = 4 * math.sin(t * 3.1)
        for cc in (c, sh_c):
            K.cage(cc, hx - 4, hy - 12, 1.25, "sing", t, swing=sw)
        dust(c, t, 40, 1)
        zoom, cx, cy = lerp(1.0, 1.15, ease(k)), lerp(540, 590, ease(k)), lerp(960, 1080, ease(k))
        world = PL["A"].copy()
        al = rgba(sh_s)[..., 3]
        world *= 1 - shadow_of(al, -38, 16, 10, 0.5)[..., None]
        world = over(world, rgba(s))
        return camera(world, zoom, cx, cy)
    if t < S2:                                                    # ---- scene 2: the canary goes silent
        k = (t - S1) / (S2 - S1)
        silent = t >= T_STOP
        # damped pendulum: L = 0.3 m -> w = sqrt(g/L) = 5.7 rad/s; a nudge when it stops singing
        ts = max(0.0, t - T_STOP)
        swing = (2.5 * math.cos(5.7 * (t - S1)) * math.exp(-(t - S1) / 1.4)) + (4.0 * math.sin(5.7 * ts) * math.exp(-ts / 1.0) if silent else 0)
        far_s, fc = layer()
        turn = ease((t - T_STOP + 0.15) / 0.35)
        pose = dict(eyes="wide" if silent else "open", brows="worried" if silent else "flat", mouth="O" if silent else "flat",
                    look=(lerp(0, 0.9, turn), -0.2), arms=[(150, -20), (165, -40)], head_tilt=lerp(0, 10, turn), sweat=lerp(0, 1, ease((t - T_STOP) / 1.0)))
        hands = K.miner(fc, 330, 1700, 1.35, pose)
        pickaxe(fc, hands["L"][0] / BASE, hands["L"][1] / BASE, -25)
        far = rgba(far_s)
        far_img = Image.fromarray((far * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))   # out of focus behind the cage
        far = np.asarray(far_img).astype(np.float32) / 255.0
        world = over(PL["B"].copy(), far)
        K.cage(c, hook[0], hook[1] + 14, 3.0, "silent" if silent else "sing", t, swing=swing)
        dust(c, t, 25, 2, (200, 240, 180))
        world = over(world, rgba(s))
        zoom, cx, cy = lerp(1.0, 1.14, ease(k)), lerp(540, hook[0], ease(k)), lerp(960, hook[1] + 220, ease(k))
        return camera(world, zoom, cx, cy)
    # ---- scene 3: RUN
    k = (t - S2) / (DUR - S2)
    ts = t - S2
    runners = [(-240, 0.0, 0), (0, 0.9, 1), (240, 1.7, 2)]
    world = PL["C"].copy()
    order = []
    for dx, ph, idx in runners:
        prog = min(1.0, ts / (3.6 + 0.3 * idx))
        sc = lerp(1.05, 2.15, prog ** 1.2)
        fx = 540 + dx * (0.55 + 0.6 * prog) + 20 * math.sin(ts * 2 + ph)
        fy = lerp(1380, 1990, prog ** 1.2)
        order.append((sc, fx, fy, ph, idx))
    for sc, fx, fy, ph, idx in sorted(order):
        p = run_pose(ts, ph)
        if idx == 0 and t > T_TWO + 0.15:
            p["helmet"] = False
        hands = K.miner(c, fx, fy, sc, p)
        K.miner(sh_c, fx, fy, sc, p)
        if idx == 1:
            hx, hy = hands["R"]
            K.cage(c, hx / BASE - 3, hy / BASE - 8, 0.75 * sc / 1.5, "silent", t, swing=18 * math.sin(ts * 9))
        if idx == 0 and t > T_TWO + 0.15:     # helmet flies off: ballistic, spinning
            tt = t - (T_TWO + 0.15)
            hx0, hy0 = fx - 10, fy - 262 * sc - 50 * sc
            g = 3600.0                        # px/s^2 at this scale (a 1.75 m man ~ 750 px)
            x_ = hx0 - 380 * tt
            y_ = hy0 - 1400 * tt + 0.5 * g * tt * tt
            c.save()
            c.translate(x_, y_)
            c.rotate(-540 * tt)
            c.scale(sc, sc)
            K.helmet(c, 52, True, glow=False)
            c.restore()
    al = rgba(sh_s)[..., 3]
    world *= 1 - shadow_of(al, 0, -40, 14, 0.45)[..., None]   # daylight from the exit behind the camera throws shadows up the tunnel
    world = over(world, rgba(s))
    n = random.Random(int(t * 30))
    shake = (7 * math.sin(t * 23) + 3 * n.uniform(-1, 1), 6 * math.sin(t * 19 + 1) + 3 * n.uniform(-1, 1), 0.6 * math.sin(t * 13))
    whip = ease((t - 9.55) / 0.35)
    fr = camera(world, lerp(1.0, 1.08, ease(k)), 540, 960, shake, whip)
    if t > 9.75:
        a = np.asarray(fr).astype(np.float32) * (1 - ease((t - 9.75) / 0.25))
        fr = Image.fromarray(a.astype(np.uint8))
    return fr


def texts(fr, t):
    """Punch words in screen space (after the camera), bottom-centre safe zone; scene 3 sits above the runners."""
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    if t < S1:
        text_pop(c, "A JOB?!", t, T_JOB, 1580, 150, (255, 214, 50))
    elif t < S2:
        text_pop(c, "SILENCE...", t, T_STOP + 0.25, 1580, 130, (255, 255, 255), fade=True)
    else:
        if t < T_RUN:
            text_pop(c, "2 MINUTES", t, T_TWO, 640, 140, (255, 214, 50))
        if t < 9.6:
            text_pop(c, "RUN!", t, T_RUN, 660, 230, (255, 60, 50), shake=14)
    a = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32) / 255.0
    base = np.asarray(fr).astype(np.float32) / 255.0
    return Image.fromarray(np.clip(over(base, a) * 255, 0, 255).astype(np.uint8))


def grade(fr, t):
    a = np.asarray(fr).astype(np.float32) / 255.0
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.5 * np.clip(((xx - W / 2) / (W * 0.72)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2, 0, 1)
    a = a * vig[..., None]
    a += np.random.default_rng(int(t * 1000)).normal(0, 0.012, (H, W, 1))
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))


if __name__ == "__main__":
    fdir = os.path.join(CT, "_frames")
    os.makedirs(fdir, exist_ok=True)
    only = [int(x) for x in os.environ.get("FRAMES", "").split(",") if x.strip()]
    for i in (only or range(NF)):
        grade(texts(frame(i), i / FPS), i / FPS).save(os.path.join(fdir, f"{i:04d}.png"))
        if i % 30 == 0:
            print("frame", i, flush=True)
    if only:
        raise SystemExit
    # ---- sound: chirps, silence, rumble, footsteps, slams, whooshes (synth + shaped noise; no music in this test)
    sr = 44100
    n = int(DUR * sr)
    sfx = np.zeros(n)
    rng = np.random.default_rng(5)

    def put(sig, t0, g=1.0):
        a = int(t0 * sr)
        b = min(n, a + len(sig))
        if a < n:
            sfx[a:b] += g * sig[: b - a]
    for k in range(40):                       # canary chirps until it stops singing
        t0 = 0.2 + k * 0.17 + rng.uniform(-0.03, 0.03)
        if t0 > T_STOP - 0.05:
            break
        d = rng.uniform(0.05, 0.09)
        tt = np.arange(int(d * sr)) / sr
        f = np.linspace(rng.uniform(3200, 4200), rng.uniform(4800, 6000), len(tt))
        env = np.sin(np.pi * tt / d) ** 2
        put(np.sin(2 * np.pi * np.cumsum(f) / sr) * env, t0, 0.18 if t0 < S1 else 0.12)
    rum_t = np.arange(n) / sr
    rumble = np.convolve(rng.normal(0, 1, n), np.ones(400) / 400, mode="same")
    rumble *= np.clip((rum_t - S1) / 2.5, 0, 1) * (1 + 0.6 * np.clip((rum_t - S2) / 1.0, 0, 1)) * (rum_t < 9.8)
    sfx += 2.2 * rumble
    for k, t0 in enumerate(np.arange(S2 + 0.1, 9.6, 0.11)):   # running boots on gravel
        d = 0.06
        put(rng.normal(0, 1, int(d * sr)) * np.exp(-np.arange(int(d * sr)) / (0.012 * sr)), t0 + rng.uniform(-0.02, 0.02), 0.22)
    def boom(t0, g):
        tt = np.arange(int(0.5 * sr)) / sr
        put(np.sin(2 * np.pi * (60 * tt + 40 * (1 - np.exp(-tt * 8)))) * np.exp(-tt * 7), t0, g)
    boom(T_JOB, 0.5)
    boom(T_TWO, 0.55)
    boom(T_RUN, 0.75)
    def whoosh(t0, d, g):
        m = int(d * sr)
        x = np.convolve(rng.normal(0, 1, m), np.ones(30) / 30, mode="same") * np.sin(np.pi * np.arange(m) / m) ** 2
        put(x, t0, g)
    whoosh(S1 - 0.15, 0.35, 0.5)
    whoosh(S2 - 0.15, 0.35, 0.5)
    whoosh(9.5, 0.45, 0.7)
    tt = np.arange(int(0.25 * sr)) / sr                       # helmet clank
    put((np.sin(2 * np.pi * 1300 * tt) + 0.6 * np.sin(2 * np.pi * 2210 * tt)) * np.exp(-tt * 18), T_TWO + 0.15, 0.25)
    sfx = sfx / max(1e-6, np.abs(sfx).max()) * 0.8
    import soundfile as sf
    sfx_wav, mus_wav = os.path.join(CT, "_sfx.wav"), os.path.join(CT, "_silence.wav")
    sf.write(sfx_wav, np.stack([sfx, sfx], 1), sr)
    sf.write(mus_wav, np.zeros((n, 2)), sr)
    voice = os.path.join(CT, "_voice.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", os.path.join(CT, "vo.wav"), "-af",
                    f"highpass=f=70,acompressor=threshold=0.12:ratio=2.5:attack=8:release=120,apad=whole_dur={DUR}", "-ar", "44100", voice], check=True)
    video = os.path.join(CT, "_video.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(fdir, "%04d.png"), "-c:v", "libx264", "-crf", "16",
                    "-preset", "slow", "-pix_fmt", "yuv420p", video], check=True)
    pre = os.path.join(CT, "_pre.mp4")
    audio.master(video, voice, mus_wav, sfx_wav, pre)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", pre, "-af", "alimiter=limit=0.6:level=disabled,loudnorm=I=-14:TP=-1.5:LRA=11",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", OUT], check=True)
    print("wrote", OUT)
