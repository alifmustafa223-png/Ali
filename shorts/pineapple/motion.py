"""Character motion for still illustrations (puppet-style mesh warp).

Each motion bends one soft region of the picture: a head that tilts around its neck, an arm that
lifts around its shoulder, a chest that breathes, a pocket watch that swings. Inside the region's
core the pixels move rigidly; toward its edge the motion fades out smoothly, so the picture bends
like a body instead of tearing.

    rig = Rig(image, [rot(pivot, centre, radii, angle_fn), move(centre, radii, dxdy_fn), breathe(...)])
    frame = rig.at(t)     # PIL image with every motion applied at time t (seconds)
"""
import math

import cv2
import numpy as np
from PIL import Image


def rot(pivot, centre, radii, angle, tilt=0.0):
    """Rotate the region around `pivot`; angle(t) in degrees (positive = clockwise on screen)."""
    return ("rot", pivot, centre, radii, tilt, angle)


def move(centre, radii, offset, tilt=0.0):
    """Shift the region by offset(t) -> (dx, dy) pixels."""
    return ("move", None, centre, radii, tilt, offset)


def breathe(centre, radii, amount, tilt=0.0):
    """Stretch the region up/down around its bottom edge; amount(t) is the relative stretch."""
    return ("breathe", None, centre, radii, tilt, amount)


class Rig:
    def __init__(self, img, motions, core=0.55):
        self.src = np.asarray(img.convert("RGB"))
        h, w = self.src.shape[:2]
        boxes = []
        for _, pivot, (cx, cy), (rx, ry), _, _ in motions:
            r = max(rx, ry) * 1.05 + 40
            boxes.append((cx - r, cy - r, cx + r, cy + r))
        x0 = int(max(0, min(b[0] for b in boxes)))
        y0 = int(max(0, min(b[1] for b in boxes)))
        x1 = int(min(w, max(b[2] for b in boxes)))
        y1 = int(min(h, max(b[3] for b in boxes)))
        self.roi = (x0, y0, x1, y1)
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        self.xs, self.ys = xs, ys
        self.parts = []
        for kind, pivot, (cx, cy), (rx, ry), tilt, fn in motions:
            c, s = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
            dx, dy = xs - cx, ys - cy
            e = np.sqrt(((dx * c + dy * s) / rx) ** 2 + ((-dx * s + dy * c) / ry) ** 2)
            u = np.clip((1 - e) / (1 - core), 0, 1)
            wgt = (u * u * (3 - 2 * u)).astype(np.float32)  # smoothstep: rigid core, soft edge
            if kind == "rot":
                ref = (xs - pivot[0], ys - pivot[1])
            elif kind == "breathe":
                ref = (None, ys - (cy + ry))  # stretch upward from the bottom of the region
            else:
                ref = None
            self.parts.append((kind, wgt, ref, fn))

    def at(self, t):
        mx, my = self.xs.copy(), self.ys.copy()
        for kind, wgt, ref, fn in self.parts:
            if kind == "rot":
                a = -math.radians(fn(t)) * wgt  # backward map: sample from the un-rotated position
                ca, sa = np.cos(a), np.sin(a)
                vx, vy = ref
                mx += vx * ca - vy * sa - vx
                my += vx * sa + vy * ca - vy
            elif kind == "move":
                ox, oy = fn(t)
                mx -= ox * wgt
                my -= oy * wgt
            else:
                k = fn(t)
                my -= ref[1] * (k / (1 + k)) * wgt
        out = self.src.copy()
        x0, y0, x1, y1 = self.roi
        out[y0:y1, x0:x1] = cv2.remap(self.src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        return Image.fromarray(out)


def wave(amp, period, phase=0.0):
    return lambda t: amp * math.sin(2 * math.pi * t / period + phase)
