"""Extra effects (added after the potato video)."""
import math

from PIL import Image

from make_short import H, W


def impact(img, t, at, strength=16, dur=0.28):
    """Jolt the whole frame for a split second when something lands (stamp, slam).
    Zooms 3% so the shifted edges never show empty borders."""
    k = t - at
    if not 0 <= k < dur:
        return
    fade = 1 - k / dur
    dx = math.sin(k * 85) * strength * fade
    dy = math.cos(k * 70) * strength * 0.6 * fade
    m = 0.03
    box = (W * m / 2 - dx, H * m / 2 - dy, W * (1 - m / 2) - dx, H * (1 - m / 2) - dy)
    img.paste(img.transform((W, H), Image.EXTENT, box, Image.BILINEAR))


def overlay(d, draw_fn):
    """Draw see-through things (smoke, glows, beams) on their own layer and blend them in,
    instead of drawing them straight onto art (which punches holes — LESSONS.md #5)."""
    from PIL import ImageDraw
    layer = Image.new("RGBA", d._image.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    d._image.alpha_composite(layer)
