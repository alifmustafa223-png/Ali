"""Toon kit for code-drawn Shorts (Skia): characters with poses and expressions, props, scenery.

    person(c, x, y, s, LOOK, pose, t)   # feet at (x, y), scale s
    pose = dict(lean=deg, tilt=deg, hands=[(dx, dy), (dx, dy)] relative to shoulders (left, right),
                eyes='open|wide|squint|closed|sad', look=(lx, ly), brows='up|angry|sad|smug|flat',
                mouth='smile|O|frown|disgust|grin|laugh|talk|chew', talk=0..1 (chew: time), blink=bool,
                walk=phase (legs swing + body bobs), hat_bounce=deg (hat lags behind the head))
"""
import math
import random

import skia

FB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf")


def C(r, g, b, a=255):
    return skia.Color(int(r), int(g), int(b), int(max(0, min(255, a))))


def P(color=None, **kw):
    p = skia.Paint(AntiAlias=True, **kw)
    if color is not None:
        p.setColor(color)
    return p


def S(color, w):
    return P(color, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def blur(sigma):
    return skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma)


def lin(p0, p1, cols, pos=None):
    return skia.GradientShader.MakeLinear([p0, p1], cols, pos)


def rad(cx, cy, r, cols, pos=None):
    return skia.GradientShader.MakeRadial((cx, cy), r, cols, pos)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def out_back(x, s=1.7):
    if x <= 0:
        return 0.0
    x = min(1.0, x) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def spring(t, at, freq=3.0, damp=4.5):
    k = t - at
    return 0.0 if k < 0 else math.exp(-damp * k) * math.cos(2 * math.pi * freq * k)


OUT = C(45, 22, 20)  # outline colour
LINE = 5


def shade(col, k):
    r, g, b = col
    return C(r * k, g * k, b * k)


def blob(c, path, col, light=1.25, dark=0.6, box=None, outline=True):
    """Fill a path with a top-left lit gradient and a soft outline."""
    b = box or path.getBounds()
    r, g, bb = col
    c.drawPath(path, P(Shader=lin((b.left(), b.top()), (b.right(), b.bottom()),
                                  [C(min(255, r * light), min(255, g * light), min(255, bb * light)), C(r, g, bb), C(r * dark, g * dark, bb * dark)], [0, 0.45, 1])))
    if outline:
        c.drawPath(path, S(OUT, LINE))


def oval(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def rrect(x0, y0, x1, y1, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), r, r))
    return p


# ---------------- characters ----------------

LADY = dict(skin=(250, 205, 180), hair="wig", hair_col=(236, 232, 240), coat=(240, 140, 160), trim=(255, 230, 235), dress=(240, 140, 165),
            pearls=True, nose="small", lips=True)
COLUMBUS = dict(skin=(240, 190, 150), hair="grey", hair_col=(165, 165, 175), coat=(40, 50, 100), trim=(220, 180, 80), pants=(60, 45, 40),
                collar=(245, 245, 240), nose="long")
GARDENER = dict(skin=(245, 185, 150), hair="cap", hair_col=(120, 75, 45), coat=(220, 200, 165), apron=(70, 110, 70), pants=(95, 70, 50),
                beard=(120, 75, 45), nose="red")
KING = dict(skin=(240, 195, 160), hair="curly", hair_col=(30, 22, 25), coat=(170, 25, 45), trim=(240, 190, 70), pants=(150, 20, 40),
            stockings=True, jabot=True, crown=True, mustache=True, nose="long")
SHOP = dict(skin=(240, 195, 165), hair="neat", hair_col=(95, 65, 45), coat=(245, 240, 230), vest=(35, 35, 40), pants=(50, 45, 45),
            glasses=True, nose="long")
KID = dict(skin=(250, 205, 170), hair="kid", hair_col=(110, 70, 40), coat=(230, 70, 120), hoodie=True, pants=(70, 100, 160), nose="small")


def crowd_look(i):
    cols = [(60, 90, 70), (40, 60, 110), (120, 60, 40), (90, 50, 110), (140, 120, 60)]
    return dict(skin=(240, 200, 170), hair="powder", hair_col=(225, 225, 230), coat=cols[i % len(cols)], trim=(230, 200, 120),
                pants=(60, 50, 50), nose="small", dress=(cols[i % len(cols)] if i % 2 else None), collar=(240, 240, 235))


def ik(sx, sy, hx, hy, a, b, bend):
    dx, dy = hx - sx, hy - sy
    d = max(1e-3, min(a + b - 1, math.hypot(dx, dy)))
    ang = math.atan2(dy, dx)
    cosA = (a * a + d * d - b * b) / (2 * a * d)
    A = math.acos(max(-1, min(1, cosA)))
    e = ang + A * bend
    return sx + a * math.cos(e), sy + a * math.sin(e)


def arm(c, sx, sy, hx, hy, col, skin, bend, sleeve_w=30):
    ex, ey = ik(sx, sy, hx, hy, 82, 80, bend)
    p = skia.Path()
    p.moveTo(sx, sy)
    p.cubicTo(sx + (ex - sx) * 0.9, sy + (ey - sy) * 0.9, ex + (hx - ex) * 0.1, ey + (hy - ey) * 0.1, hx, hy)  # smooth bend through the elbow
    c.drawPath(p, S(OUT, sleeve_w + LINE * 2))
    r, g, b = col
    c.drawPath(p, S(C(r, g, b), sleeve_w))
    c.drawPath(p, S(C(min(255, r * 1.2), min(255, g * 1.2), min(255, b * 1.2), 120), sleeve_w * 0.35))
    hand = oval(hx, hy, 21, 21)
    blob(c, hand, skin)


def eye(c, x, y, kind, lx, ly, blink, size=1.0):
    w, h = 22 * size, 27 * size
    if blink or kind == "closed":
        c.drawArc(skia.Rect(x - w, y - h * 0.5, x + w, y + h * 0.7), 200, 140, False, S(OUT, 6))
        return
    if kind == "squint":
        p = skia.Path()
        p.moveTo(x - w, y - 4)
        p.lineTo(x + w * 0.9, y + 2)
        c.drawPath(p, S(OUT, 7))
        p2 = skia.Path()
        p2.moveTo(x - w * 0.8, y - h * 0.6)
        p2.lineTo(x + w * 0.4, y - 2)
        c.drawPath(p2, S(OUT, 6))
        return
    hh = h * (1.25 if kind == "wide" else 0.8 if kind == "sad" else 1.0)
    ww = w * (1.15 if kind == "wide" else 1.0)
    c.drawOval(skia.Rect(x - ww, y - hh, x + ww, y + hh), P(C(255, 255, 255)))
    pr = (11 if kind == "wide" else 14) * size
    px, py = x + lx * ww * 0.4, y + ly * hh * 0.4
    c.drawCircle(px, py, pr, P(Shader=rad(px, py, pr, [C(30, 20, 15), C(90, 60, 35)])))
    c.drawCircle(px - pr * 0.35, py - pr * 0.4, pr * 0.32, P(C(255, 255, 255)))
    if kind == "sad":
        c.drawLine(x - ww, y - hh * 0.5, x + ww, y - hh * 0.9, S(OUT, 5))
    c.drawOval(skia.Rect(x - ww, y - hh, x + ww, y + hh), S(OUT, 4))


def brow(c, x, y, kind, side, col):
    d = {"up": (-10, -12, -10), "angry": (2, -2, 10), "sad": (6, -4, -10), "smug": (-8, -8, -2), "flat": (0, -4, 0)}[kind]
    p = skia.Path()
    lo, mid, hi = d
    if side > 0:
        lo, hi = hi, lo
    p.moveTo(x - 22, y + lo * (1 if side < 0 else 1))
    p.quadTo(x, y + mid - 8, x + 22, y + hi)
    c.drawPath(p, S(col, 9))


def mouth(c, x, y, kind, talk, lips):
    col = C(150, 40, 50) if lips else C(110, 35, 35)
    if kind == "chew":  # jaw working sideways, talk = time
        ph = talk * 8.5
        w, h = 17 + 5 * math.sin(ph), 4 + 9 * abs(math.sin(ph))
        ox = 7 * math.sin(ph * 0.5)
        p = oval(x + ox, y + 2, w, h)
        c.drawPath(p, P(C(110, 25, 35)))
        c.drawPath(p, S(OUT, 4))
        return
    if kind == "talk":
        kind = "O" if talk > 0.45 else "smile" if talk < 0.15 else "open"
    if kind == "smile":
        c.drawArc(skia.Rect(x - 26, y - 22, x + 26, y + 12), 20, 140, False, S(col, 7))
    elif kind == "grin":
        p = skia.Path()
        p.moveTo(x - 32, y - 8)
        p.quadTo(x, y + 30, x + 32, y - 8)
        p.close()
        c.drawPath(p, P(C(120, 30, 40)))
        c.drawRect(skia.Rect(x - 24, y - 7, x + 24, y + 2), P(C(255, 255, 255)))
        c.drawPath(p, S(OUT, 4))
    elif kind in ("O", "open", "laugh"):
        h = {"O": 22, "open": 13, "laugh": 26}[kind]
        w = {"O": 15, "open": 20, "laugh": 30}[kind]
        p = oval(x, y + 2, w, h)
        if kind == "laugh":
            p = skia.Path()
            p.moveTo(x - w, y - 6)
            p.quadTo(x, y + h * 1.8, x + w, y - 6)
            p.close()
        c.drawPath(p, P(C(110, 25, 35)))
        c.save()
        c.clipPath(p, doAntiAlias=True)
        c.drawCircle(x, y + h, w * 0.8, P(C(230, 90, 100)))
        c.restore()
        c.drawPath(p, S(OUT, 4))
    elif kind == "frown":
        c.drawArc(skia.Rect(x - 22, y + 2, x + 22, y + 30), 200, 140, False, S(col, 7))
    elif kind == "disgust":
        p = skia.Path()
        p.moveTo(x - 26, y + 4)
        for k in range(1, 7):
            p.lineTo(x - 26 + k * 52 / 6, y + (8 if k % 2 else -4))
        c.drawPath(p, S(col, 7))


def hair_back(c, look, R, t=0.0):
    hc = look["hair_col"]
    h = look["hair"]
    if h == "grey":
        for side in (-1, 1):  # shoulder-length locks behind the ears
            p = skia.Path()
            p.moveTo(side * R * 0.75, -R * 0.3)
            p.cubicTo(side * R * 1.35, -R * 0.1, side * R * 1.3, R * 0.9, side * R * 0.95, R * 1.05)
            p.cubicTo(side * R * 0.8, R * 0.6, side * R * 0.75, R * 0.2, side * R * 0.75, -R * 0.3)
            p.close()
            blob(c, p, hc, 1.2, 0.7)
    elif h == "curly":  # symmetric halo of curls that ends at the jaw (never hangs over the shoulders/arms)
        for side in (-1, 1):
            for k in range(7):
                ang = math.radians(-95 + k * 25)
                cx = side * math.cos(ang) * R * 1.03
                cy = math.sin(ang) * R * 1.03
                blob(c, oval(cx, cy, 33, 33), hc, 1.8, 0.7)
    elif h == "pigtails":
        for side in (-1, 1):
            sw = math.sin(t * 3.1 + side) * 6
            blob(c, oval(side * R * 1.25 + sw, R * 0.05, R * 0.32, R * 0.48), hc, 1.2, 0.7)
            c.drawCircle(side * R * 1.05, -R * 0.3, 14, P(C(240, 90, 140)))
    elif h == "wig":
        blob(c, oval(0, -R * 1.2, R * 0.95, R * 1.35), hc, 1.08, 0.75)
        for i in range(5):
            blob(c, oval(-R * 0.85 + i * R * 0.42, -R * 2.3 + abs(i - 2) * R * 0.18, R * 0.3, R * 0.25), hc, 1.08, 0.78)


def hair_front(c, look, R, t):
    hc = look["hair_col"]
    h = look["hair"]
    if h == "wig":
        for side in (-1, 1):
            for k in range(3):
                blob(c, oval(side * R * 0.95, -R * 0.55 + k * R * 0.42, R * 0.24, R * 0.2), hc, 1.08, 0.8)
        for k, (bx, by) in enumerate([(-0.4, -1.6), (0.45, -1.9), (0.1, -1.1)]):
            bw = P(C(240, 120, 150))
            x, y = bx * R, by * R
            p = skia.Path()
            p.moveTo(x, y)
            p.lineTo(x - 22, y - 14)
            p.lineTo(x - 22, y + 14)
            p.close()
            p.moveTo(x, y)
            p.lineTo(x + 22, y - 14)
            p.lineTo(x + 22, y + 14)
            p.close()
            c.drawPath(p, bw)
            c.drawPath(p, S(OUT, 3))
        p = skia.Path()
        p.moveTo(-R * 0.9, -R * 0.45)
        p.cubicTo(-R * 0.6, -R * 1.25, R * 0.6, -R * 1.25, R * 0.9, -R * 0.45)
        p.cubicTo(R * 0.4, -R * 0.75, -R * 0.4, -R * 0.75, -R * 0.9, -R * 0.45)
        blob(c, p, hc, 1.08, 0.8)
    elif h == "grey":
        p = skia.Path()
        p.moveTo(-R * 1.02, R * 0.15)
        p.cubicTo(-R * 1.15, -R * 1.2, R * 1.15, -R * 1.2, R * 1.02, R * 0.15)
        p.cubicTo(R * 0.85, -R * 0.45, R * 0.4, -R * 0.62, R * 0.05, -R * 0.6)
        p.cubicTo(-R * 0.35, -R * 0.75, -R * 0.75, -R * 0.5, -R * 1.02, R * 0.15)
        blob(c, p, hc, 1.25, 0.7)
        for k in range(4):
            c.drawArc(skia.Rect(-R * 0.8 + k * R * 0.38, -R * 1.0, -R * 0.3 + k * R * 0.38, -R * 0.45), 200, 110, False, S(C(110, 110, 120), 4))
    elif h == "curly":
        for i in range(7):
            a = math.pi * (1.1 + 0.8 * i / 6)
            blob(c, oval(math.cos(a) * R * 0.85, math.sin(a) * R * 0.85 - R * 0.05, 30, 30), hc, 1.8, 0.7)
    elif h == "powder":
        for side in (-1, 1):
            for k in range(2):
                blob(c, oval(side * R * 0.95, -R * 0.2 + k * R * 0.38, R * 0.22, R * 0.18), hc, 1.05, 0.8)
        p = skia.Path()
        p.moveTo(-R * 0.95, -R * 0.3)
        p.cubicTo(-R * 0.9, -R * 1.3, R * 0.9, -R * 1.3, R * 0.95, -R * 0.3)
        p.cubicTo(R * 0.5, -R * 0.7, -R * 0.5, -R * 0.7, -R * 0.95, -R * 0.3)
        blob(c, p, hc, 1.05, 0.8)
    elif h in ("neat", "pigtails"):
        p = skia.Path()
        p.moveTo(-R * 0.98, -R * 0.2)
        p.cubicTo(-R * 1.0, -R * 1.2, R * 1.0, -R * 1.2, R * 0.98, -R * 0.25)
        p.cubicTo(R * 0.5, -R * 0.85, -R * 0.1, -R * 0.6, -R * 0.98, -R * 0.2)
        blob(c, p, hc)
    elif h == "kid":
        p = skia.Path()
        p.moveTo(-R * 1.0, -R * 0.15)
        pts = [(-0.95, -0.95), (-0.6, -0.8), (-0.45, -1.3), (-0.15, -0.95), (0.1, -1.4), (0.35, -1.0), (0.65, -1.25), (0.75, -0.8), (1.05, -0.9), (1.0, -0.15)]
        for px, py in pts:
            p.lineTo(px * R, py * R + math.sin(t * 6 + px * 4) * 3)
        p.cubicTo(R * 0.5, -R * 0.6, -R * 0.4, -R * 0.55, -R * 1.0, -R * 0.15)
        p.close()
        blob(c, p, hc)
    elif h == "cap":
        blob(c, oval(-R * 0.92, -R * 0.05, R * 0.2, R * 0.3), hc)
        blob(c, oval(R * 0.92, -R * 0.05, R * 0.2, R * 0.3), hc)
        p = skia.Path()
        p.moveTo(-R * 1.05, -R * 0.35)
        p.cubicTo(-R * 1.1, -R * 1.35, R * 1.15, -R * 1.3, R * 1.15, -R * 0.45)
        p.close()
        blob(c, p, (125, 85, 55))
        brim = skia.Path()
        brim.moveTo(-R * 0.9, -R * 0.42)
        brim.cubicTo(-R * 0.2, -R * 0.62, R * 0.7, -R * 0.62, R * 1.35, -R * 0.3)
        brim.cubicTo(R * 0.7, -R * 0.3, -R * 0.2, -R * 0.3, -R * 0.9, -R * 0.42)
        blob(c, brim, (100, 65, 40))


def head(c, look, pose, t, R=88, back=True):
    lx, ly = pose.get("look", (0, 0))
    if back:
        hair_back(c, look, R, t)
    face = oval(0, 0, R, R * 1.02)
    blob(c, face, look["skin"], 1.12, 0.8)
    for side in (-1, 1):  # ears
        if look["hair"] not in ("wig", "grey", "curly", "powder"):
            blob(c, oval(side * R * 0.98, R * 0.08, 16, 22), look["skin"], 1.05, 0.8)
    if look.get("beard"):
        p = skia.Path()
        p.moveTo(-R * 0.95, R * 0.05)
        p.cubicTo(-R * 0.95, R * 1.35, R * 0.95, R * 1.35, R * 0.95, R * 0.05)
        p.cubicTo(R * 0.6, R * 0.45, R * 0.35, R * 0.22, 0, R * 0.25)
        p.cubicTo(-R * 0.35, R * 0.22, -R * 0.6, R * 0.45, -R * 0.95, R * 0.05)
        blob(c, p, look["beard"])
    for side in (-1, 1):  # cheeks
        c.drawCircle(side * R * 0.55, R * 0.32, R * 0.2, P(C(255, 110, 110, 90), MaskFilter=blur(9)))
    ey = -R * 0.08
    for side in (-1, 1):
        eye(c, side * R * 0.36, ey, pose.get("eyes", "open"), lx, ly, pose.get("blink", False))
        brow(c, side * R * 0.36, ey - R * 0.42, pose.get("brows", "flat"), side,
             C(*[v * 0.5 for v in look["hair_col"]]) if look["hair"] not in ("wig", "powder") else C(140, 110, 100))
    if look.get("glasses"):
        for side in (-1, 1):
            c.drawCircle(side * R * 0.36, ey, 30, S(C(60, 50, 40), 5))
        c.drawLine(-R * 0.13, ey, R * 0.13, ey, S(C(60, 50, 40), 5))
    n = look.get("nose", "small")
    if n == "red":
        blob(c, oval(0, R * 0.2, 24, 21), (235, 90, 90), 1.2, 0.75)
    elif n == "long":
        p = skia.Path()
        p.moveTo(-4, -R * 0.02)
        p.cubicTo(18, R * 0.15, 22, R * 0.3, 2, R * 0.33)
        c.drawPath(p, S(C(190, 120, 100), 6))
    else:
        c.drawCircle(0, R * 0.2, 9, P(C(220, 140, 120)))
    if look.get("mustache"):
        for side in (-1, 1):
            p = skia.Path()
            p.moveTo(0, R * 0.42)
            p.cubicTo(side * 24, R * 0.32, side * 44, R * 0.45, side * 52, R * 0.3)
            c.drawPath(p, S(C(25, 18, 20), 9))
    mouth(c, 0, R * 0.55, pose.get("mouth", "smile"), pose.get("talk", 0), look.get("lips"))
    hair_front(c, look, R, t)
    if look.get("sideburns"):
        for side in (-1, 1):
            p = skia.Path()
            p.moveTo(side * R * 0.97, -R * 0.35)
            p.cubicTo(side * R * 1.02, R * 0.1, side * R * 0.9, R * 0.45, side * R * 0.7, R * 0.55)
            p.lineTo(side * R * 0.75, -R * 0.35)
            p.close()
            blob(c, p, look["hair_col"], 1.2, 0.7)
    hat(c, look, pose, R)
    if look.get("crown"):
        p = skia.Path()
        p.moveTo(-50, -R * 0.95)
        for k, (px, py) in enumerate([(-50, -R * 1.45), (-25, -R * 1.15), (0, -R * 1.55), (25, -R * 1.15), (50, -R * 1.45), (50, -R * 0.95)]):
            p.lineTo(px, py)
        p.close()
        blob(c, p, (250, 200, 60), 1.3, 0.7)
        c.drawCircle(0, -R * 1.1, 9, P(C(220, 30, 60)))
        for px in (-50, 0, 50):
            c.drawCircle(px, -R * (1.45 if px else 1.55), 7, P(C(255, 245, 200)))


def hat(c, look, pose, R):
    kind = look.get("hat")
    if not kind:
        return
    c.save()
    c.translate(0, -R * 0.75)
    c.rotate(pose.get("hat_bounce", 0.0))
    if kind == "bicorne":  # Napoleon-style general's hat, side to side
        p = skia.Path()
        p.moveTo(-R * 1.55, R * 0.05)
        p.cubicTo(-R * 1.0, -R * 0.35, -R * 0.55, -R * 1.05, 0, -R * 1.05)
        p.cubicTo(R * 0.55, -R * 1.05, R * 1.0, -R * 0.35, R * 1.55, R * 0.05)
        p.cubicTo(R * 0.8, -R * 0.12, -R * 0.8, -R * 0.12, -R * 1.55, R * 0.05)
        p.close()
        blob(c, p, (30, 28, 40), 1.6, 0.7)
        trim = skia.Path()
        trim.moveTo(-R * 1.5, R * 0.02)
        trim.cubicTo(-R * 0.8, -R * 0.16, R * 0.8, -R * 0.16, R * 1.5, R * 0.02)
        c.drawPath(trim, S(C(235, 190, 80), 7))
        c.drawCircle(0, -R * 0.42, 22, P(C(245, 245, 240)))  # cockade
        c.drawCircle(0, -R * 0.42, 13, P(C(60, 140, 80)))
        c.drawCircle(0, -R * 0.42, 6, P(C(210, 40, 50)))
        c.drawCircle(0, -R * 0.42, 22, S(OUT, 3))
    elif kind == "bowler":
        blob(c, oval(0, -R * 0.08, R * 1.2, R * 0.18), (45, 40, 40), 1.5, 0.7)
        p = skia.Path()
        p.moveTo(-R * 0.78, -R * 0.1)
        p.cubicTo(-R * 0.82, -R * 1.05, R * 0.82, -R * 1.05, R * 0.78, -R * 0.1)
        p.close()
        blob(c, p, (50, 44, 44), 1.6, 0.7)
        c.drawRect(skia.Rect(-R * 0.78, -R * 0.3, R * 0.78, -R * 0.14), P(C(120, 40, 45)))
    elif kind == "tophat":
        blob(c, oval(0, -R * 0.06, R * 1.15, R * 0.17), (35, 32, 38), 1.5, 0.7)
        crown = skia.Path()
        crown.moveTo(-R * 0.72, -R * 0.1)
        crown.lineTo(-R * 0.8, -R * 1.25)
        crown.cubicTo(-R * 0.4, -R * 1.33, R * 0.4, -R * 1.33, R * 0.8, -R * 1.25)
        crown.lineTo(R * 0.72, -R * 0.1)
        crown.close()
        blob(c, crown, (40, 36, 44), 1.7, 0.7)
        c.drawRect(skia.Rect(-R * 0.74, -R * 0.4, R * 0.74, -R * 0.2), P(C(110, 30, 40)))
        c.drawLine(-R * 0.55, -R * 1.15, -R * 0.5, -R * 0.5, S(C(255, 255, 255, 50), 6))
    elif kind == "turban":
        tc = look.get("turban_col", (240, 235, 220))
        p = skia.Path()
        p.moveTo(-R * 1.0, R * 0.05)
        p.cubicTo(-R * 1.15, -R * 1.1, R * 1.15, -R * 1.1, R * 1.0, R * 0.05)
        p.cubicTo(R * 0.5, -R * 0.12, -R * 0.5, -R * 0.12, -R * 1.0, R * 0.05)
        p.close()
        blob(c, p, tc, 1.2, 0.75)
        for k in range(3):  # wraps
            c.drawArc(skia.Rect(-R * 0.95, -R * (0.95 - k * 0.22), R * 0.95, -R * (0.2 - k * 0.22)), 200, 140, False,
                      S(C(*[v * 0.8 for v in tc]), 5))
        c.drawCircle(0, -R * 0.45, 14, P(C(220, 40, 70)))
        c.drawCircle(0, -R * 0.45, 14, S(C(240, 200, 80), 4))
    elif kind == "laurel":
        for side in (-1, 1):
            for k in range(6):
                a = math.radians(200 + k * 14) if side < 0 else math.radians(-20 - k * 14)
                lx, ly = math.cos(a) * R * 0.95, R * 0.55 + math.sin(a) * R * 0.95
                c.save()
                c.translate(lx, ly)
                c.rotate(math.degrees(a) + 90 * side)
                blob(c, oval(0, 0, 9, 18), (90, 160, 70), 1.4, 0.7)
                c.restore()
    c.restore()


def uniform_front(c, look, layer):
    """Military/toga details: 'chest' items go over the torso (under the arms), epaulettes over the arms."""
    if layer == "chest" and look.get("sash"):
        p = skia.Path()
        p.moveTo(-58, -250)
        p.lineTo(-30, -250)
        p.lineTo(70, -110)
        p.lineTo(45, -95)
        p.close()
        blob(c, p, look["sash"], 1.3, 0.75)
    if layer == "chest" and look.get("medals"):
        for k, col in enumerate([(250, 200, 70), (220, 220, 230), (250, 200, 70)]):
            x = 22 + k * 22
            c.drawRect(skia.Rect(x - 7, -222, x + 7, -200), P(C(*[(200, 40, 50), (40, 120, 70), (240, 240, 240)][k])))
            c.drawCircle(x, -190, 10, P(C(*col)))
            c.drawCircle(x, -190, 10, S(OUT, 2))
    if layer == "arms" and look.get("epaulettes"):
        for side in (-1, 1):
            blob(c, oval(side * 66, -246, 34, 15), (240, 195, 80), 1.3, 0.7)
            for k in range(5):
                fx = side * 66 - 26 + k * 13
                c.drawLine(fx, -236, fx, -214, S(C(230, 180, 60), 5))


def person(c, x, y, s, look, pose, t):
    """Chibi character standing with feet at (x, y)."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.rotate(pose.get("lean", 0))
    breath = 1 + 0.015 * math.sin(t * 2.4 + x)
    sq = pose.get("squash", 0.0)
    c.scale(1 + sq, (1 - sq) * breath)
    # legs / dress
    if look.get("dress"):
        p = skia.Path()
        p.moveTo(-60, -175)
        p.cubicTo(-120, -110, -190, -40, -185, 0)
        p.cubicTo(-60, 22, 60, 22, 185, 0)
        p.cubicTo(190, -40, 120, -110, 60, -175)
        p.close()
        blob(c, p, look["dress"], 1.25, 0.65)
        for k in range(5):
            c.drawLine(-120 + k * 60, -120 + abs(k - 2) * 10, -150 + k * 75, 0, S(C(255, 255, 255, 60), 4))
        c.drawPath(p, S(C(255, 235, 240, 140), 3))
    else:
        walk = pose.get("walk")
        for side in (-1, 1):
            c.save()
            if walk is not None:  # legs swing around the hip, opposite phase
                c.translate(side * 36, -95)
                c.rotate(side * 24 * math.sin(walk))
                c.translate(-side * 36, 95)
            leg = rrect(side * 36 - 21, -95, side * 36 + 21, -18, 14)
            blob(c, leg, (240, 240, 240) if look.get("stockings") else look.get("pants", (60, 50, 50)))
            shoe = oval(side * 40 + 8, -14, 32, 16)
            blob(c, shoe, (40, 30, 30), 1.4)
            c.restore()
        if walk is not None:
            c.translate(0, -9 * abs(math.sin(walk)))
    # back hair goes BEHIND the body, so long hair never covers the shoulders, arms or hands
    c.save()
    c.translate(0, -262)
    c.rotate(pose.get("tilt", 0))
    c.translate(0, -70)
    hair_back(c, look, 88, t)
    c.restore()
    # torso
    coat = look["coat"]
    tor = skia.Path()
    tor.moveTo(-58, -255)
    tor.cubicTo(-75, -200, -82, -130, -78 if not look.get("dress") else -60, -80 if not look.get("dress") else -170)
    tor.lineTo(78 if not look.get("dress") else 60, -80 if not look.get("dress") else -170)
    tor.cubicTo(82, -130, 75, -200, 58, -255)
    tor.close()
    if look.get("hoodie"):
        blob(c, tor, coat)
        c.save()
        c.clipPath(tor, doAntiAlias=True)
        for k, col in enumerate([(240, 200, 60), (80, 190, 210), (120, 90, 200)]):
            c.drawRect(skia.Rect(-100, -200 + k * 40, 100, -170 + k * 40), P(C(*col)))
        c.restore()
        c.drawPath(tor, S(OUT, LINE))
    else:
        blob(c, tor, coat)
    if look.get("apron"):
        ap = rrect(-50, -205, 50, -70, 14)
        blob(c, ap, look["apron"])
        c.drawLine(-45, -205, -30, -255, S(look_c(look["apron"]), 7))
        c.drawLine(45, -205, 30, -255, S(look_c(look["apron"]), 7))
    if look.get("vest"):
        v = skia.Path()
        v.moveTo(-50, -250)
        v.lineTo(-62, -95)
        v.lineTo(-8, -95)
        v.lineTo(-4, -215)
        v.close()
        v.moveTo(50, -250)
        v.lineTo(62, -95)
        v.lineTo(8, -95)
        v.lineTo(4, -215)
        v.close()
        blob(c, v, look["vest"], 1.8)
    if look.get("trim") and not look.get("dress"):
        c.drawLine(0, -245, 0, -90, S(C(*look["trim"]), 6))
        for k in range(4):
            c.drawCircle(-14, -225 + k * 35, 6, P(C(*look["trim"])))
    if look.get("dress"):
        c.drawPath(tor, S(C(255, 235, 240, 160), 3))
        bow = skia.Path()
        bow.moveTo(0, -215)
        bow.lineTo(-28, -232)
        bow.lineTo(-28, -198)
        bow.close()
        bow.moveTo(0, -215)
        bow.lineTo(28, -232)
        bow.lineTo(28, -198)
        bow.close()
        c.drawPath(bow, P(C(250, 170, 190)))
        c.drawPath(bow, S(OUT, 3))
    if look.get("collar"):
        p = skia.Path()
        p.moveTo(-34, -258)
        p.lineTo(0, -228)
        p.lineTo(34, -258)
        c.drawPath(p, S(C(*look["collar"]), 12))
    if look.get("jabot"):
        for k in range(3):
            blob(c, oval(0, -240 + k * 16, 22 - k * 4, 11), (250, 245, 230), 1.0, 0.85)
    uniform_front(c, look, "chest")
    # head
    c.save()
    c.translate(0, -262)
    c.rotate(pose.get("tilt", 0))
    c.translate(0, -70)
    if look.get("pearls"):
        c.drawArc(skia.Rect(-46, 40, 46, 120), 20, 140, False, P(C(250, 250, 245), Style=skia.Paint.kStroke_Style, StrokeWidth=9,
                                                                       PathEffect=skia.DashPathEffect.Make([1, 13], 0), StrokeCap=skia.Paint.kRound_Cap))
    head(c, look, pose, t, back=False)
    c.restore()
    # arms (in front)
    sleeve = look["coat"] if not look.get("dress") else look["coat"]
    hands = pose.get("hands", [(-20, 150), (20, 150)])
    for side, (hx, hy) in zip((-1, 1), hands):
        sx, sy = side * 60, -235
        arm(c, sx, sy, sx + hx, sy + hy, sleeve, look["skin"], -side if hy > 0 else side)
    uniform_front(c, look, "arms")
    c.restore()


def look_c(col):
    return C(col[0] * 0.8, col[1] * 0.8, col[2] * 0.8)


def hand_pos(x, y, s, pose, side, lean=None):
    """Screen position of a hand (side -1 = left, 1 = right), for attaching props."""
    hx, hy = pose.get("hands", [(-20, 150), (20, 150)])[0 if side < 0 else 1]
    px, py = side * 60 + hx, -235 + hy
    a = math.radians(pose.get("lean", 0) if lean is None else lean)
    return x + s * (px * math.cos(a) - py * math.sin(a)), y + s * (px * math.sin(a) + py * math.cos(a))


# ---------------- props ----------------

def pine(c, x, y, s, rot=0.0, rotten=0.0, t=0.0):
    """Small pineapple (no face), centred at (x, y); rotten 0..1 browns it."""
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    for i, (a, ln) in enumerate([(-40, 60), (40, 60), (-18, 85), (18, 85), (0, 100)]):
        c.save()
        c.translate(0, -62)
        c.rotate(a + math.sin(t * 2 + i) * 3 - rotten * 25 * (1 if a >= 0 else -1))
        p = skia.Path()
        p.moveTo(0, 0)
        p.cubicTo(16, -ln * 0.35, 8, -ln * 0.8, 0, -ln)
        p.cubicTo(-8, -ln * 0.8, -16, -ln * 0.35, 0, 0)
        g = (40 + 80 * rotten, 130 - 40 * rotten, 50)
        blob(c, p, g, 1.3, 0.7)
        c.restore()
    body = oval(0, 0, 50, 66)
    col = (250 - 120 * rotten, 185 - 100 * rotten, 50 - 10 * rotten)
    blob(c, body, col, 1.15, 0.65)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    for k in range(-6, 7):
        c.drawLine(k * 20 - 80, -80, k * 20 + 80, 80, S(C(150 - 60 * rotten, 80 - 30 * rotten, 15, 150), 3))
        c.drawLine(k * 20 + 80, -80, k * 20 - 80, 80, S(C(150 - 60 * rotten, 80 - 30 * rotten, 15, 150), 3))
    if rotten > 0.3:
        for k in range(6):
            c.drawCircle(-30 + (k * 23) % 60, -40 + (k * 31) % 80, 7 + k % 3 * 3, P(C(70, 80, 50, 200 * rotten)))
    c.restore()
    c.restore()


def coin(c, x, y, r, face=1.0, flat=False):
    if flat:
        c.drawOval(skia.Rect(x - r, y - r * 0.32, x + r, y + r * 0.32), P(Shader=lin((x - r, y), (x + r, y), [C(255, 240, 160), C(235, 175, 40), C(170, 110, 20)])))
        c.drawOval(skia.Rect(x - r, y - r * 0.32, x + r, y + r * 0.32), S(C(140, 85, 15), 3))
        return
    w = max(4, r * abs(face))
    c.drawOval(skia.Rect(x - w, y - r, x + w, y + r), P(Shader=lin((x - w, y - r), (x + w, y + r), [C(255, 240, 160), C(240, 180, 40), C(170, 110, 20)])))
    c.drawOval(skia.Rect(x - w, y - r, x + w, y + r), S(C(140, 85, 15), 4))


def glow(c, x, y, r, col, a):
    c.drawCircle(x, y, r, P(Shader=rad(x, y, r, [C(*col, a), C(*col, 0)]), BlendMode=skia.BlendMode.kPlus))


def flicker(t, ph):
    return 0.75 + 0.15 * math.sin(t * 11 + ph) + 0.1 * math.sin(t * 27 + ph * 3)


def candle(c, x, y, t, ph=0.0, s=1.0):
    blob(c, rrect(x - 9 * s, y - 50 * s, x + 9 * s, y, 4), (250, 240, 220), 1.0, 0.8, outline=False)
    f = flicker(t, ph)
    p = skia.Path()
    fx = x + math.sin(t * 9 + ph) * 2
    p.moveTo(fx, y - 50 * s - 30 * s * f)
    p.cubicTo(fx + 11 * s, y - 60 * s, fx + 8 * s, y - 50 * s, fx, y - 48 * s)
    p.cubicTo(fx - 8 * s, y - 50 * s, fx - 11 * s, y - 60 * s, fx, y - 50 * s - 30 * s * f)
    c.drawPath(p, P(Shader=lin((0, y - 85 * s), (0, y - 48 * s), [C(255, 250, 200), C(255, 160, 40)])))
    glow(c, fx, y - 62 * s, 70 * s, (255, 170, 80), int(120 * f))


def chandelier(c, x, y, t, s=1.0):
    c.drawLine(x, y - 400, x, y - 60 * s, S(C(120, 90, 40), 4))
    c.drawOval(skia.Rect(x - 120 * s, y - 30 * s, x + 120 * s, y + 20 * s), S(C(230, 180, 70), 8))
    blob(c, oval(x, y - 40 * s, 30 * s, 40 * s), (230, 180, 70), 1.3, 0.7, outline=False)
    for k in range(6):
        a = k / 6 * 2 * math.pi
        cx, cy = x + math.cos(a) * 110 * s, y + math.sin(a) * 18 * s
        candle(c, cx, cy, t, k, 0.7 * s)
    glow(c, x, y - 40 * s, 260 * s, (255, 200, 120), int(70 * flicker(t, 3)))


def palm(c, x, y, h, t, lean=1):
    trunk = skia.Path()
    trunk.moveTo(x - 22, y)
    trunk.cubicTo(x - 10 + lean * 30, y - h * 0.5, x + lean * 60, y - h * 0.8, x + lean * 80, y - h)
    trunk.lineTo(x + lean * 80 + 18, y - h + 6)
    trunk.cubicTo(x + lean * 70 + 18, y - h * 0.8, x + 30 + lean * 30, y - h * 0.5, x + 22, y)
    trunk.close()
    blob(c, trunk, (120, 80, 50))
    tx, ty = x + lean * 88, y - h
    for k in range(7):
        a = math.radians(-160 + k * 50 + math.sin(t * 1.2 + k) * 4)
        p = skia.Path()
        p.moveTo(tx, ty)
        ex, ey = tx + math.cos(a) * 220, ty + math.sin(a) * 120 + 60
        p.quadTo(tx + math.cos(a) * 120, ty + math.sin(a) * 120 - 50, ex, ey)
        p.quadTo(tx + math.cos(a) * 110, ty + math.sin(a) * 90 - 20, tx, ty)
        blob(c, p, (40, 110, 60), 1.4, 0.6)


def ship(c, x, y, s, t, dark=False):
    c.save()
    c.translate(x, y + math.sin(t * 1.3) * 6 * s)
    c.rotate(math.sin(t * 1.1) * 2)
    c.scale(s, s)
    hull = skia.Path()
    hull.moveTo(-160, -20)
    hull.lineTo(170, -40)
    hull.lineTo(130, 40)
    hull.lineTo(-130, 40)
    hull.close()
    blob(c, hull, (90, 55, 35) if not dark else (50, 30, 30))
    for mx, mh in ((-60, 230), (50, 270)):
        c.drawLine(mx, -20, mx, -20 - mh, S(C(70, 45, 30), 8))
        sail = skia.Path()
        sail.moveTo(mx - 70, -40 - mh * 0.85)
        sail.quadTo(mx + 10, -mh * 0.55, mx - 70, -40)
        sail.lineTo(mx + 70, -40)
        sail.quadTo(mx + 120, -mh * 0.55, mx + 70, -40 - mh * 0.85)
        sail.close()
        blob(c, sail, (240, 225, 200) if not dark else (190, 170, 160), 1.05, 0.75)
    c.restore()


def crate(c, x, y, w, h):
    blob(c, rrect(x - w / 2, y - h, x + w / 2, y, 6), (150, 100, 55))
    for k in range(1, 3):
        c.drawLine(x - w / 2 + 6, y - h + k * h / 3, x + w / 2 - 6, y - h + k * h / 3, S(C(100, 60, 30), 4))


def fly(c, x, y, t, ph):
    fx = x + math.cos(t * 3.4 + ph) * 60 + math.sin(t * 9 + ph) * 12
    fy = y + math.sin(t * 4.1 + ph * 2) * 40
    wing = 6 + 4 * math.sin(t * 60 + ph)
    c.drawOval(skia.Rect(fx - wing - 5, fy - 10, fx - 1, fy - 1), P(C(230, 240, 250, 150)))
    c.drawOval(skia.Rect(fx + 1, fy - 10, fx + wing + 5, fy - 1), P(C(230, 240, 250, 150)))
    c.drawCircle(fx, fy, 6, P(C(20, 20, 20)))


def stink(c, x, y, t, ph=0.0, col=(140, 190, 80)):
    for k in range(3):
        p = skia.Path()
        yy = y - ((t * 60 + k * 40 + ph * 30) % 120)
        p.moveTo(x + k * 26 - 26, yy)
        for j in range(4):
            p.quadTo(x + k * 26 - 26 + (12 if j % 2 else -12), yy - j * 20 - 10, x + k * 26 - 26, yy - j * 20 - 20)
        a = int(200 * math.sin(((t * 60 + k * 40 + ph * 30) % 120) / 120 * math.pi))
        c.drawPath(p, S(C(*col, a), 6))


def snowflakes(c, t, n=150, seed=7):
    r = random.Random(seed)
    for i in range(n):
        depth = r.choice((0.5, 0.8, 1.3))
        x0, y0, ph = r.uniform(0, 1080), r.uniform(0, 1920), r.uniform(0, 6.28)
        y = (y0 + t * 130 * depth) % 1960 - 20
        x = (x0 + math.sin(t * 0.9 * depth + ph) * 30 * depth + t * 12 * depth) % 1080
        rr = 2.5 * depth + 1.5
        c.drawCircle(x, y, rr, P(C(245, 248, 255, 200 if depth > 1 else 150), MaskFilter=blur(0.8 if depth < 1 else 0.3)))


def sparkle(c, x, y, r, a=230, col=(255, 240, 170)):
    p = skia.Path()
    p.moveTo(x, y - r * 2)
    p.lineTo(x + r * 0.45, y - r * 0.45)
    p.lineTo(x + r * 2, y)
    p.lineTo(x + r * 0.45, y + r * 0.45)
    p.lineTo(x, y + r * 2)
    p.lineTo(x - r * 0.45, y + r * 0.45)
    p.lineTo(x - r * 2, y)
    p.lineTo(x - r * 0.45, y - r * 0.45)
    p.close()
    c.drawPath(p, P(C(*col, a)))
    glow(c, x, y, r * 4, col, a // 3)


def burst(c, t, at, x, y, n=12, reach=260):
    p = (t - at) / 0.9
    if not 0 < p < 1:
        return
    for i in range(n):
        a = i / n * 2 * math.pi + 0.3
        r = reach * ease(p) * (0.75 + 0.25 * math.sin(i * 2.3))
        sparkle(c, x + math.cos(a) * r, y + math.sin(a) * r, 16 * (1 - p) + 4, int(255 * (1 - p * 0.7)))
