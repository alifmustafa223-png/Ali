"""'Ultimate power' test: a fully code-drawn 10-second shot rendered with Skia (anti-aliased vector
art, real gradients, soft shadows, glow and bloom) instead of PIL.

A vector pineapple character on a velvet cushion under a volumetric spotlight: blinks, eyes that
follow the coins, squash & stretch, crown leaves with spring physics, coins raining with gravity,
bounce and spin, a 3D-extruded "$8,000" slam, a swinging FOR RENT sign on chains, sunglasses that
drop on "show off", a wink at the end. Camera push-in with parallax, bloom, vignette, film grain.

Usage: python ultimate.py out.mp4
"""
import math
import random
import subprocess
import sys

import numpy as np
import skia

sys.path.insert(0, "..")
import audio  # noqa: E402

W, H, FPS = 1080, 1920, 30
DUR = 10.0
FB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf")
FM = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-Medium.otf")

# voice cues (seconds), from the recognizer
T_EIGHT, T_SO, T_RENTED, T_SHOW, T_END = 1.42, 3.16, 4.95, 6.22, 7.03


def C(r, g, b, a=255):
    return skia.Color(int(r), int(g), int(b), int(max(0, min(255, a))))


def P(color=None, **kw):
    p = skia.Paint(AntiAlias=True, **kw)
    if color is not None:
        p.setColor(color)
    return p


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def out_back(x, s=1.7):
    if x <= 0:
        return 0.0
    x = min(1.0, x) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def spring(t, at, freq=3.2, damp=4.5):
    """Damped oscillation that starts at time `at` (1 -> 0)."""
    k = t - at
    if k < 0:
        return 0.0
    return math.exp(-damp * k) * math.cos(2 * math.pi * freq * k)


def blur(sigma):
    return skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma)


# ---------- background ----------

rnd = random.Random(11)
BOKEH = [(rnd.uniform(-100, W + 100), rnd.uniform(200, 1500), rnd.uniform(18, 70), rnd.uniform(0.25, 0.7), rnd.uniform(0, 6.28)) for _ in range(28)]
MOTES = [(rnd.uniform(0, 1), rnd.uniform(0, 1), rnd.uniform(1.5, 4), rnd.uniform(0, 6.28)) for _ in range(70)]


def background(c, t, cam_dx):
    c.drawPaint(P(Shader=skia.GradientShader.MakeRadial((540, 980), 1250, [C(78, 22, 48), C(30, 8, 22), C(8, 3, 8)], [0, 0.55, 1])))
    for x, y, r, depth, ph in BOKEH:  # far gold lights, parallax with the camera
        xx = x + cam_dx * depth * 0.6 + math.sin(t * 0.4 + ph) * 12
        a = 40 + 40 * math.sin(t * 0.8 + ph)
        c.drawCircle(xx, y, r, P(C(255, 200, 110, a * depth), MaskFilter=blur(r * 0.35)))
    curtain(c, t, left=True)
    curtain(c, t, left=False)
    # floor + light pool
    c.drawRect(skia.Rect(0, 1560, W, H), P(Shader=skia.GradientShader.MakeLinear([(0, 1560), (0, H)], [C(40, 10, 22), C(12, 3, 8)])))
    c.drawOval(skia.Rect(90, 1500, 990, 1760), P(Shader=skia.GradientShader.MakeRadial((540, 1630), 450, [C(255, 210, 150, 90), C(255, 210, 150, 0)])))


def curtain(c, t, left):
    """Velvet curtain on one side: folds with gradient shading, gently swaying."""
    for i in range(5):
        x0 = (i * 52) if left else W - (i + 1) * 52
        sway = math.sin(t * 0.9 + i * 0.7) * 8
        path = skia.Path()
        top, bot = -10, 1600
        w = 70
        if left:
            path.moveTo(x0, top)
            path.cubicTo(x0 + w, 500, x0 + w * 0.6 + sway, 1100, x0 + w * 1.1 + sway * 2, bot)
            path.lineTo(x0 - 20, bot)
            path.lineTo(x0 - 20, top)
        else:
            path.moveTo(x0 + 52, top)
            path.cubicTo(x0 + 52 - w, 500, x0 + 52 - w * 0.6 + sway, 1100, x0 + 52 - w * 1.1 + sway * 2, bot)
            path.lineTo(x0 + 72, bot)
            path.lineTo(x0 + 72, top)
        path.close()
        shade = 0.55 + 0.45 * (i / 4)
        c.drawPath(path, P(Shader=skia.GradientShader.MakeLinear([(x0 - 20, 0), (x0 + 90, 0)],
                                                                    [C(60 * shade, 6, 18), C(150 * shade, 20, 40), C(50 * shade, 4, 14)])))
    # valance (top drape)
    path = skia.Path()
    path.moveTo(0, 0)
    for k in range(7):
        x = k * W / 6
        path.quadTo(x + W / 12, 150 + 10 * math.sin(t + k), x + W / 6, 90)
    path.lineTo(W, 0)
    path.close()
    c.drawPath(path, P(Shader=skia.GradientShader.MakeLinear([(0, 0), (0, 160)], [C(110, 14, 32), C(60, 6, 18)])))
    c.drawPath(path, P(C(230, 170, 70), Style=skia.Paint.kStroke_Style, StrokeWidth=5))


def spotlight(c, t, pulse):
    path = skia.Path()
    path.moveTo(430, -20)
    path.lineTo(650, -20)
    path.lineTo(900, 1640)
    path.lineTo(180, 1640)
    path.close()
    a = 80 + 60 * pulse
    c.drawPath(path, P(Shader=skia.GradientShader.MakeLinear([(0, 0), (0, 1640)], [C(255, 240, 210, a), C(255, 230, 190, a * 0.25)]),
                       MaskFilter=blur(40), BlendMode=skia.BlendMode.kPlus))
    for x, y, r, ph in MOTES:  # dust floating in the beam
        yy = ((y - t * 0.03) % 1) * 1600
        half = 110 + yy / 1640 * 250
        xx = 540 + (x - 0.5) * 2 * half + math.sin(t + ph) * 15
        c.drawCircle(xx, yy, r, P(C(255, 245, 220, 70 + 60 * math.sin(t * 2 + ph))))


# ---------- props ----------

def pedestal(c, t):
    # gold pedestal
    body = skia.Rect(330, 1470, 750, 1690)
    c.drawRect(body, P(Shader=skia.GradientShader.MakeLinear([(330, 0), (750, 0)], [C(120, 70, 20), C(255, 215, 120), C(200, 140, 40), C(90, 50, 15)], [0, 0.35, 0.6, 1])))
    c.drawOval(skia.Rect(330, 1440, 750, 1500), P(Shader=skia.GradientShader.MakeLinear([(330, 0), (750, 0)], [C(160, 100, 30), C(255, 230, 150), C(150, 90, 25)])))
    c.drawOval(skia.Rect(320, 1660, 760, 1720), P(C(110, 65, 18)))
    # velvet cushion
    path = skia.Path()
    path.moveTo(250, 1440)
    path.cubicTo(250, 1340, 830, 1340, 830, 1440)
    path.cubicTo(860, 1500, 220, 1500, 250, 1440)
    path.close()
    c.drawPath(path, P(C(0, 0, 0, 120), MaskFilter=blur(18)))
    c.drawPath(path, P(Shader=skia.GradientShader.MakeRadial((470, 1370), 420, [C(235, 60, 80), C(160, 20, 40), C(80, 6, 20)], [0, 0.55, 1])))
    c.drawPath(path, P(C(255, 200, 90), Style=skia.Paint.kStroke_Style, StrokeWidth=6))
    for side, x in ((-1, 250), (1, 830)):  # tassels swing (pendulum)
        ang = math.radians(10 * math.sin(t * 3.1 + side) + 18 * spring(t, T_EIGHT + 0.15) * side)
        c.save()
        c.translate(x, 1440)
        c.rotate(math.degrees(ang))
        c.drawLine(0, 0, 0, 60, P(C(240, 190, 80), StrokeWidth=6))
        tp = skia.Path()
        tp.moveTo(-14, 60)
        tp.lineTo(14, 60)
        tp.lineTo(24, 130)
        tp.lineTo(-24, 130)
        tp.close()
        c.drawPath(tp, P(Shader=skia.GradientShader.MakeLinear([(-24, 0), (24, 0)], [C(190, 130, 40), C(255, 220, 120), C(170, 110, 30)])))
        c.drawCircle(0, 60, 14, P(C(255, 215, 110)))
        c.restore()


# ---------- the pineapple character ----------

def leaf(c, length, width, ang, col_a, col_b):
    c.save()
    c.rotate(ang)
    p = skia.Path()
    p.moveTo(0, 0)
    p.cubicTo(width, -length * 0.35, width * 0.5, -length * 0.8, 0, -length)
    p.cubicTo(-width * 0.5, -length * 0.8, -width, -length * 0.35, 0, 0)
    p.close()
    c.drawPath(p, P(Shader=skia.GradientShader.MakeLinear([(-width, 0), (width, 0)], [col_a, col_b])))
    c.drawPath(p, P(C(25, 60, 25), Style=skia.Paint.kStroke_Style, StrokeWidth=4))
    c.drawLine(0, -6, 0, -length * 0.85, P(C(255, 255, 200, 90), StrokeWidth=3))
    c.restore()


def pineapple(c, t, look_x, look_y, state):
    """Character centred on its base at (0, 0) in the current canvas transform."""
    sq = state["squash"]
    c.save()
    c.scale(1 + sq, 1 - sq)
    bw, bh = 165, 205
    cy = -bh - 10
    # crown: leaves with spring physics (lag behind the body)
    sway = state["sway"]
    c.save()
    c.translate(0, cy - bh + 30)
    for i, (ang, ln) in enumerate([(-58, 120), (58, 120), (-34, 165), (34, 165), (-14, 205), (14, 205), (0, 230)]):
        a = ang + sway * (1.0 + abs(ang) / 40) + math.sin(t * 2.2 + i) * 2
        leaf(c, ln, 34, a, C(40, 120, 45), C(120, 200, 80))
    c.restore()
    # body
    body = skia.Path()
    body.addOval(skia.Rect(-bw, cy - bh, bw, cy + bh))
    c.drawPath(body, P(C(0, 0, 0, 140), MaskFilter=blur(22)))
    c.drawPath(body, P(Shader=skia.GradientShader.MakeLinear([(0, cy - bh), (0, cy + bh)], [C(255, 232, 110), C(252, 185, 50), C(225, 125, 30)], [0, 0.55, 1])))
    c.save()
    c.clipPath(body, doAntiAlias=True)
    lat = P(C(205, 120, 25, 170), Style=skia.Paint.kStroke_Style, StrokeWidth=5)
    for k in range(-12, 13):  # diamond lattice
        x = k * 58
        c.drawLine(x - 400, cy - 400, x + 400, cy + 400, lat)
        c.drawLine(x + 400, cy - 400, x - 400, cy + 400, lat)
    for i in range(-6, 7):
        for j in range(-8, 9):
            x, y = i * 58 + (29 if j % 2 else 0), cy + j * 29
            c.drawCircle(x, y, 7, P(C(255, 250, 200, 170)))
    # 3D shading: light from the upper left
    c.drawPaint(P(Shader=skia.GradientShader.MakeRadial((-60, cy - 110), 330, [C(255, 255, 230, 110), C(255, 255, 230, 0)])))
    c.drawPaint(P(Shader=skia.GradientShader.MakeRadial((120, cy + 160), 260, [C(80, 20, 0, 0), C(80, 20, 0, 150)], [0.2, 1])))
    c.restore()
    c.drawPath(body, P(C(110, 50, 10), Style=skia.Paint.kStroke_Style, StrokeWidth=8))
    # face
    fy = cy - 10
    c.drawCircle(-105, fy + 70, 34, P(C(255, 110, 110, 120), MaskFilter=blur(12)))
    c.drawCircle(105, fy + 70, 34, P(C(255, 110, 110, 120), MaskFilter=blur(12)))
    open_ = state["eye_open"]
    for side in (-1, 1):
        ex, ey = side * 64, fy
        eh = 66 * max(0.08, open_ if not (state["wink"] and side == 1) else max(0.08, 1 - state["wink"]))
        c.drawOval(skia.Rect(ex - 50, ey - eh, ex + 50, ey + eh), P(C(255, 255, 255)))
        if eh > 14:
            c.save()
            clip = skia.Path()
            clip.addOval(skia.Rect(ex - 50, ey - eh, ex + 50, ey + eh))
            c.clipPath(clip, doAntiAlias=True)
            px, py = ex + look_x * 18, ey + look_y * 22
            pr = 30 * state["pupil"]
            c.drawCircle(px, py, pr, P(Shader=skia.GradientShader.MakeRadial((px, py), pr, [C(40, 25, 10), C(95, 55, 20)])))
            c.drawCircle(px, py, pr * 0.5, P(C(10, 5, 0)))
            c.drawCircle(px - pr * 0.35, py - pr * 0.4, pr * 0.3, P(C(255, 255, 255)))
            c.restore()
        c.drawOval(skia.Rect(ex - 50, ey - eh, ex + 50, ey + eh), P(C(90, 40, 10), Style=skia.Paint.kStroke_Style, StrokeWidth=5))
        # eyebrows
        lift = state["brow"]
        b = skia.Path()
        b.moveTo(ex - 42, ey - 88 - lift - side * 6 * state["smug"])
        b.quadTo(ex, ey - 112 - lift * 1.3, ex + 42, ey - 88 - lift + side * 6 * state["smug"])
        c.drawPath(b, P(C(110, 50, 10), Style=skia.Paint.kStroke_Style, StrokeWidth=12, StrokeCap=skia.Paint.kRound_Cap))
    # mouth
    mo = state["mouth"]
    m = skia.Path()
    if mo > 0.15:  # open "O!"
        m.addOval(skia.Rect(-26 * mo - 8, fy + 92 - 10, 26 * mo + 8, fy + 92 + 46 * mo))
        c.drawPath(m, P(C(110, 25, 30)))
        c.drawOval(skia.Rect(-16 * mo, fy + 92 + 26 * mo, 16 * mo, fy + 92 + 44 * mo), P(C(230, 90, 100)))
    else:  # smug smile
        s = state["smug"]
        m.moveTo(-50, fy + 92 - 6 * s)
        m.quadTo(10, fy + 128, 52, fy + 86 - 14 * s)
        c.drawPath(m, P(C(110, 40, 10), Style=skia.Paint.kStroke_Style, StrokeWidth=10, StrokeCap=skia.Paint.kRound_Cap))
    # sunglasses
    gd = state["glasses"]
    if gd is not None:
        c.save()
        c.translate(0, gd)
        c.rotate(state["glasses_rot"])
        for side in (-1, 1):
            r = skia.RRect.MakeRectXY(skia.Rect(side * 70 - 64, fy - 74, side * 70 + 64, fy + 60), 34, 34)
            c.drawRRect(r, P(Shader=skia.GradientShader.MakeLinear([(0, fy - 42), (0, fy + 40)], [C(70, 70, 90), C(8, 8, 14)], [0, 1])))
            c.drawRRect(r, P(C(10, 10, 10), Style=skia.Paint.kStroke_Style, StrokeWidth=8))
            g = state["glint"]
            if 0 < g < 1:  # light sweeping across the lens
                c.save()
                c.clipRRect(r, doAntiAlias=True)
                gx = side * 70 - 100 + g * 200
                gp = skia.Path()
                gp.moveTo(gx, fy - 80)
                gp.lineTo(gx + 34, fy - 80)
                gp.lineTo(gx - 12, fy + 70)
                gp.lineTo(gx - 46, fy + 70)
                gp.close()
                c.drawPath(gp, P(C(255, 255, 255, 170)))
                c.restore()
        c.drawLine(-8, fy - 30, 8, fy - 30, P(C(10, 10, 10), StrokeWidth=14))
        c.restore()
    c.restore()


# ---------- coins with physics ----------

FLOOR = 1760
COINS = []
_cr = random.Random(5)
for i in range(46):
    COINS.append(dict(x=_cr.uniform(60, 1020), y=_cr.uniform(-900, -60), vx=_cr.uniform(-60, 60), vy=_cr.uniform(0, 300),
                      r=_cr.uniform(26, 40), spin=_cr.uniform(5, 12), ph=_cr.uniform(0, 6.28), floor=FLOOR + _cr.uniform(-60, 120)))


def coins_at(t):
    """Simulate (deterministically, from scratch) where every coin is at time t."""
    out = []
    k = t - T_EIGHT
    if k <= 0:
        return out
    dt = 1 / 120
    for cn in COINS:
        x, y, vx, vy = cn["x"], cn["y"], cn["vx"], cn["vy"]
        s = 0.0
        while s < k:
            vy += 3200 * dt
            x += vx * dt
            y += vy * dt
            if y > cn["floor"]:
                y = cn["floor"]
                vy = -vy * 0.42
                vx *= 0.7
                if abs(vy) < 90:
                    vy = 0
            s += dt
        resting = vy == 0 and y >= cn["floor"] - 1
        out.append((x, y + (cn["r"] * 0.6 if resting else 0), cn["r"], "flat" if resting else math.cos(k * cn["spin"] + cn["ph"]), abs(vy)))
    return out


def draw_coin(c, x, y, r, face, speed):
    if face == "flat":  # resting on the floor: seen lying down, not edge-on
        c.drawOval(skia.Rect(x - r, y - r * 0.32, x + r, y + r * 0.32),
                   P(Shader=skia.GradientShader.MakeLinear([(x - r, y), (x + r, y)], [C(255, 240, 160), C(235, 175, 40), C(170, 110, 20)])))
        c.drawOval(skia.Rect(x - r, y - r * 0.32, x + r, y + r * 0.32), P(C(140, 85, 15), Style=skia.Paint.kStroke_Style, StrokeWidth=3))
        return
    w = max(4, r * abs(face))
    stretch = 1 + min(0.5, speed / 4000)
    c.drawOval(skia.Rect(x - w, y - r * stretch, x + w, y + r * stretch),
               P(Shader=skia.GradientShader.MakeLinear([(x - w, y - r), (x + w, y + r)], [C(255, 240, 160), C(240, 180, 40), C(170, 110, 20)])))
    c.drawOval(skia.Rect(x - w, y - r * stretch, x + w, y + r * stretch), P(C(140, 85, 15), Style=skia.Paint.kStroke_Style, StrokeWidth=4))
    if w > r * 0.5:
        c.drawOval(skia.Rect(x - w * 0.6, y - r * 0.6 * stretch, x + w * 0.6, y + r * 0.6 * stretch),
                   P(C(200, 140, 30), Style=skia.Paint.kStroke_Style, StrokeWidth=3))


# ---------- text ----------

def text3d(c, s, cx, y, size, t, at):
    """Gold 3D-extruded slam text with glow."""
    p = (t - at) / 0.25
    if p <= 0:
        return
    sc = 1 + 1.4 * (1 - ease(p))
    a = min(1, p * 1.5)
    f = skia.Font(FB, size)
    w = f.measureText(s)
    c.save()
    c.translate(cx, y)
    shake = math.sin(t * 90) * 12 * max(0, 1 - (t - at) / 0.45)
    c.translate(shake, 0)
    c.scale(sc, sc)
    c.drawString(s, -w / 2, 0, f, P(C(255, 180, 40, 160 * a), MaskFilter=blur(28)))
    for d in range(16, 0, -1):
        c.drawString(s, -w / 2 + d * 0.6, d * 1.6, f, P(C(120 + d * 3, 60, 10, 255 * a)))
    c.drawString(s, -w / 2, 0, f, P(Shader=skia.GradientShader.MakeLinear([(0, -size * 0.8), (0, 0)], [C(255, 250, 200, 255 * a), C(255, 190, 40, 255 * a)])))
    c.drawString(s, -w / 2, 0, f, P(C(120, 60, 0, 255 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=4))
    c.restore()


def label(c, s, cx, y, size, color, t, at, typeface=FB, shadow=True):
    a = ease((t - at) / 0.35)
    if a <= 0:
        return
    f = skia.Font(typeface, size)
    w = f.measureText(s)
    oy = (1 - a) * 40
    if shadow:
        c.drawString(s, cx - w / 2 + 4, y + oy + 6, f, P(C(0, 0, 0, 150 * a), MaskFilter=blur(4)))
    r, g, b = color
    c.drawString(s, cx - w / 2, y + oy, f, P(C(r, g, b, 255 * a)))


def rent_sign(c, t):
    k = t - T_RENTED + 0.15
    if k <= 0:
        return
    drop = out_back(k / 0.45, 2.2)
    swing = 9 * spring(t, T_RENTED + 0.3, 1.1, 1.6)
    c.save()
    c.translate(540, -60 + 560 * drop)
    c.rotate(swing)
    for sx in (-200, 200):  # chains
        for j in range(12):
            c.drawOval(skia.Rect(sx - 9, -40 - j * 42 - 26, sx + 9, -40 - j * 42 + 2), P(C(220, 180, 90), Style=skia.Paint.kStroke_Style, StrokeWidth=6))
    board = skia.RRect.MakeRectXY(skia.Rect(-300, -50, 300, 150), 26, 26)
    c.drawRRect(board, P(C(0, 0, 0, 140), MaskFilter=blur(20)))
    c.drawRRect(board, P(Shader=skia.GradientShader.MakeLinear([(0, -50), (0, 150)], [C(150, 95, 50), C(95, 55, 25)])))
    for gy in range(-30, 150, 34):
        c.drawLine(-290, gy, 290, gy + 6, P(C(70, 38, 15, 120), StrokeWidth=3))
    c.drawRRect(board, P(C(255, 205, 90), Style=skia.Paint.kStroke_Style, StrokeWidth=10))
    f = skia.Font(FB, 108)
    s = "FOR RENT"
    w = f.measureText(s)
    c.drawString(s, -w / 2 + 3, 92, f, P(C(40, 20, 5, 200)))
    c.drawString(s, -w / 2, 88, f, P(Shader=skia.GradientShader.MakeLinear([(0, 0), (0, 100)], [C(255, 245, 190), C(255, 195, 60)])))
    c.restore()


# ---------- post ----------

GRAIN = []
_g = np.random.default_rng(3)
for _ in range(6):
    n = (_g.standard_normal((H // 2, W // 2)) * 18 + 128).clip(0, 255).astype(np.uint8)
    arr = np.dstack([n, n, n, np.full_like(n, 255)])
    GRAIN.append(skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType))

BLOOM = skia.ColorFilters.Matrix([2.2, 0, 0, 0, -1.25,
                                  0, 2.2, 0, 0, -1.25,
                                  0, 0, 2.2, 0, -1.25,
                                  0, 0, 0, 1, 0])


def frame(t):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    # camera: slow push-in + gentle drift, kicks on impacts
    z = 1.0 + 0.07 * ease(t / DUR)
    kick = 10 * spring(t, T_EIGHT + 0.2, 6, 7) + 8 * spring(t, T_RENTED + 0.3, 6, 7)
    dx = math.sin(t * 0.45) * 14
    c.save()
    c.translate(540 + kick, 1180)
    c.scale(z, z)
    c.translate(-540 + dx, -1180)
    background(c, t, dx * 3)
    pulse = math.exp(-3 * max(0, t - T_EIGHT)) if t > T_EIGHT else 0
    spotlight(c, t, pulse)
    pedestal(c, t)
    # character state
    hop = spring(t, T_EIGHT + 0.05, 2.4, 3.2)
    blink = ((t + 1.4) % 3.1) < 0.12 and t < T_SHOW and not (T_EIGHT - 0.2 < t < T_SO + 0.3)
    st = dict(
        squash=0.08 * hop + 0.015 * math.sin(t * 2.4) - 0.06 * spring(t, T_SHOW + 0.25, 3, 6),
        sway=-14 * hop + 7 * spring(t, T_SHOW + 0.25, 2.5, 4) + 3 * math.sin(t * 1.3),
        eye_open=0.1 if blink else 1.0, wink=0.0,
        pupil=1.0 - 0.25 * min(1, max(0, (t - T_EIGHT) * 3)) * (1 if t < T_SO else 0),
        brow=24 * min(1, max(0, (t - T_EIGHT) * 4)) * (1 if t < T_SO + 0.3 else 0) + 10 * (t > T_SHOW + 0.6),
        smug=1.0 if t > T_SO else 0.3,
        mouth=0.0 if not (T_EIGHT < t < T_SO) else min(1, (t - T_EIGHT) * 5),
        glasses=None, glasses_rot=0.0, glint=0.0)
    gk = t - (T_SHOW - 0.05)
    if gk > 0:
        st["glasses"] = -700 * (1 - out_back(gk / 0.4, 1.4))
        st["glasses_rot"] = -8 * (1 - ease(gk / 0.4))
        st["glint"] = (t - (T_SHOW + 0.55)) / 0.4
    if t > 8.6:  # glasses slide down, wink
        slide = ease((t - 8.6) / 0.35)
        st["glasses"] = (st["glasses"] or 0) + 78 * slide
        st["eye_open"] = 1.0
        st["wink"] = ease((t - 8.95) / 0.12) * (1 - ease((t - 9.5) / 0.12))
        st["brow"] = 18 * slide
    # where is it looking?  at the coins while they fall, then at the viewer
    lx, ly = 0.0, 0.0
    if T_EIGHT < t < T_SO + 0.4:
        lx, ly = math.sin(t * 3) * 0.6, 0.6
    elif t > T_RENTED - 0.1 and t < T_SHOW:
        lx, ly = 0.0, -0.8  # looks up at the sign
    c.drawOval(skia.Rect(400, 1385, 680, 1430), P(C(60, 0, 10, 150), MaskFilter=blur(14)))
    c.save()
    c.translate(540, 1415)
    pineapple(c, t, lx, ly, st)
    c.restore()
    for x, y, r, face, speed in coins_at(t):
        draw_coin(c, x, y, r, face, speed)
    c.restore()
    # text (screen space, above the camera)
    hide_a = 1 - ease((t - (T_RENTED - 0.35)) / 0.25)
    if hide_a > 0:
        c.saveLayerAlpha(None, int(255 * hide_a))
        label(c, "This pineapple was worth", 540, 300, 72, (255, 255, 255), t, -1)
        text3d(c, "$8,000", 540, 560, 230, t, T_EIGHT)
        c.restore()
    rent_sign(c, t)
    label(c, "...just to show off", 540, 755, 60, (255, 230, 170), t, T_SHOW - 0.1)
    # post: bloom, vignette, grain
    snap = surf.makeImageSnapshot()
    c.drawImage(snap, 0, 0, skia.SamplingOptions(), P(ColorFilter=BLOOM, ImageFilter=skia.ImageFilters.Blur(26, 26), BlendMode=skia.BlendMode.kPlus, Alphaf=0.55))
    c.drawPaint(P(Shader=skia.GradientShader.MakeRadial((540, 1050), 1250, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 200)], [0, 0.5, 1])))
    c.drawImageRect(GRAIN[int(t * FPS) % len(GRAIN)], skia.Rect(0, 0, W, H), skia.SamplingOptions(),
                    P(Alphaf=0.07, BlendMode=skia.BlendMode.kOverlay))
    # progress bar
    c.drawRect(skia.Rect(0, H - 14, W * t / DUR, H), P(C(255, 170, 60)))
    return surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[:, :, :3]


if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) > 2:  # stills for checking: python ultimate.py x t1,t2,...
        from PIL import Image
        for tt in sys.argv[2].split(","):
            Image.fromarray(frame(float(tt))).save(f"still_{tt}.png")
        sys.exit()
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                             "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "base_ult.mp4"],
                            stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        proc.stdin.write(np.ascontiguousarray(frame(i / FPS)).tobytes())
    proc.stdin.close()
    proc.wait()
    ev = [("thud", T_EIGHT + 0.2), ("whoosh", T_RENTED - 0.1), ("thud", T_RENTED + 0.3), ("pop", T_SHOW + 0.3), ("ding", T_SHOW + 0.6),
          ("whoosh", 8.6), ("click", 8.95), ("ding", 9.0)]
    k0 = 0
    for cn in coins_at(T_EIGHT + 3.0) if False else []:
        pass
    for i in range(14):  # coin clinks as they land
        ev.append(("click", T_EIGHT + 0.35 + i * 0.09 + (i % 3) * 0.03))
    audio.music("music.wav", DUR, bpm=100, seed=6)
    audio.sfx("sfx.wav", DUR, ev)
    audio.master("base_ult.mp4", "voice.mp3", "music.wav", "sfx.wav", out)
    print("wrote", out)
