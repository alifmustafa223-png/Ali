"""Airplane-windows Short, REAL-3D version: Blender plates (dailymind/blender/window3d.py) + the classic DailyMind layer
(titles, slams, stamps, gold splat transitions, vignette, grain, music + SFX, CTA v2) from make_window.py.

Pipeline (same voice, no new credits):
  1. python sprites_window.py                         (toon sprite sequences for Blender)
  2. for s in 0 1 2 3 4 5 6 7 8 9 11: blender -b -P ../blender/window3d.py -- $s ../window3d/plates 100 32 EEVEE
  3. python make_window3d.py ../window3d/final.mp4     (composite + audio, then qa.py)
Scenes 10 (FOLLOW) and 12 (CTA end card) stay 2D. A missing plate falls back to the old 2D frame and is reported.
"""
import math
import os
import sys

OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "../window3d/final.mp4"
EXTRA = sys.argv[2:]
sys.argv = [sys.argv[0], OUTFILE] + EXTRA
import make_window as MW  # noqa: E402
from make_window import *  # noqa: E402,F401,F403
from PIL import Image  # noqa: E402

PLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "window3d", "plates")
TWO_D = {10, 12}
_missing = set()
_old_render = MW.render_art


def render_art3d(i, t, dur):
    if i in TWO_D:
        return _old_render(i, t, dur)
    f = int(t * 30) + 1
    path = os.path.join(PLATES, f"s{i}", f"{f:04d}.png")
    if not os.path.exists(path):  # clamp to the last rendered frame of the scene
        d = os.path.join(PLATES, f"s{i}")
        frames = sorted(os.listdir(d)) if os.path.isdir(d) else []
        if not frames:
            _missing.add(i)
            return _old_render(i, t, dur)
        path = os.path.join(d, frames[min(len(frames) - 1, f - 1)] if f - 1 < len(frames) else frames[-1])
    im = Image.open(path).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.drawImage(skia.Image.fromarray(np.ascontiguousarray(np.dstack([np.asarray(im), np.full((H, W), 255, np.uint8)]))), 0, 0)
    # the classic DailyMind finish on top of the 3D plate: soft bloom, vignette, dark top for the titles, film grain
    snap = surf.makeImageSnapshot()
    c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=U.BLOOM, ImageFilter=skia.ImageFilters.Blur(24, 24), BlendMode=skia.BlendMode.kPlus, Alphaf=0.22))
    c.drawPaint(P(Shader=rad(540, 1100, 1250, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 170)], [0, 0.5, 1])))
    c.drawRect(skia.Rect(0, 0, W, 900), P(Shader=lin((0, 0), (0, 900), [C(5, 4, 10, 190), C(5, 4, 10, 0)])))
    c.drawImageRect(U.GRAIN[int(t * 30) % len(U.GRAIN)], skia.Rect(0, 0, W, H), skia.SamplingOptions(), P(Alphaf=0.05, BlendMode=skia.BlendMode.kOverlay))
    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    return Image.fromarray(np.ascontiguousarray(arr))


MW.render_art = render_art3d


def unpack_videos():
    """Plates rendered on the GPU PC come back as s{i}.mp4 — unpack them to PNG frames once."""
    import subprocess
    for i in range(13):
        mp4 = os.path.join(PLATES, f"s{i}.mp4")
        d = os.path.join(PLATES, f"s{i}")
        if os.path.exists(mp4) and not (os.path.isdir(d) and os.listdir(d)):
            os.makedirs(d, exist_ok=True)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp4, "-start_number", "1", os.path.join(d, "%04d.png")], check=True)
            print("unpacked", mp4)


unpack_videos()

if __name__ == "__main__":
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_window.py")).read()
    main_src = src[src.index('if __name__ == "__main__":'):].replace('if __name__ == "__main__":', "if True:", 1)
    main_src = main_src.replace('"base_window.mp4"', '"base_window3d.mp4"').replace("'base_window.mp4'", "'base_window3d.mp4'")
    main_src = main_src.replace("win_{i:02d}_{tt}.png", "w3d_{i:02d}_{tt}.png")
    MW.OUTFILE = OUTFILE
    try:
        exec(compile(main_src, "make_window_main", "exec"), MW.__dict__)
    finally:
        if _missing:
            print("WARNING: no 3D plates for scenes", sorted(_missing), "- used the old 2D frames there")
    _ = math
