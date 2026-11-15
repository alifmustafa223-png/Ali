"""Flat 2D white stickmen with thick black outlines and big expressive faces (+ birdcage & canary), drawn with Skia.

    miner(c, x, y, s, pose)      feet at (x, y); s = pixels per unit (body is ~300 units tall)
pose keys (all optional): lean, head_tilt, look (lx, ly), eyes 'open|wide|happy|squint|shut', brows 'up|flat|worried|proud',
mouth 'smile|grin|O|scream|flat|tight', arms [(shoulder_deg, elbow_deg), (..)] for left/right (0 = hanging down,
positive = raised forward/outward), legs [(hip_deg, knee_deg), (..)], sweat 0..1, helmet True/False, lamp True/False.
"""
import math

import skia

BLACK = skia.Color(18, 14, 16)
WHITE = skia.Color(250, 250, 246)


def P(col, **kw):
    p = skia.Paint(AntiAlias=True, **kw)
    p.setColor(col)
    return p


def S(col, w):
    return skia.Paint(AntiAlias=True, Color=col, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                      StrokeJoin=skia.Paint.kRound_Join)


def limb(c, pts, w=18):
    """A white tube with a thick black outline through the given points."""
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    c.drawPath(p, S(BLACK, w + 12))
    c.drawPath(p, S(WHITE, w))


def chain(origin, angles, lengths, down=True):
    """Joint positions from a start point and relative angles (degrees, 0 = straight down)."""
    pts, ang = [origin], 0.0
    x, y = origin
    for a, L in zip(angles, lengths):
        ang += a
        x += L * math.sin(math.radians(ang))
        y += L * math.cos(math.radians(ang)) * (1 if down else -1)
        pts.append((x, y))
    return pts


def face(c, pose, R):
    lx, ly = pose.get("look", (0.0, 0.0))
    eyes = pose.get("eyes", "open")
    brows = pose.get("brows", "flat")
    for side in (-1, 1):
        ex, ey = side * R * 0.38, -R * 0.08
        if eyes in ("happy", "shut"):
            p = skia.Path()
            p.moveTo(ex - R * 0.2, ey + (4 if eyes == "happy" else 0))
            p.quadTo(ex, ey - (R * 0.22 if eyes == "happy" else -R * 0.05), ex + R * 0.2, ey + (4 if eyes == "happy" else 0))
            c.drawPath(p, S(BLACK, R * 0.1))
        else:
            sc = {"open": 1.0, "wide": 1.35, "squint": 0.55}[eyes]
            rx, ry = R * 0.2 * (1.15 if eyes == "wide" else 1.0), R * 0.25 * sc
            c.drawOval(skia.Rect(ex - rx, ey - ry, ex + rx, ey + ry), P(WHITE))
            c.drawOval(skia.Rect(ex - rx, ey - ry, ex + rx, ey + ry), S(BLACK, R * 0.07))
            pr = R * (0.08 if eyes == "wide" else 0.11)
            px, py = ex + lx * rx * 0.45, ey + ly * ry * 0.45
            c.drawCircle(px, py, pr, P(BLACK))
            c.drawCircle(px - pr * 0.35, py - pr * 0.4, pr * 0.35, P(WHITE))
        # brows
        by = ey - R * 0.42
        tilt = {"up": (-0.12, -0.12), "flat": (0, 0), "worried": (-0.1, 0.12), "proud": (0.08, -0.1), "angry": (0.14, -0.06)}[brows]
        inner, outer = tilt
        if brows == "up":
            by -= R * 0.12
        x_in, x_out = ex - side * R * 0.18, ex + side * R * 0.2
        c.drawLine(x_in, by + inner * R, x_out, by + outer * R, S(BLACK, R * 0.1))
    # mouth
    m = pose.get("mouth", "smile")
    my = R * 0.42
    if m == "smile":
        c.drawArc(skia.Rect(-R * 0.3, my - R * 0.3, R * 0.3, my + R * 0.08), 20, 140, False, S(BLACK, R * 0.09))
    elif m == "flat":
        c.drawLine(-R * 0.18, my, R * 0.18, my, S(BLACK, R * 0.09))
    elif m == "tight":
        p = skia.Path()
        p.moveTo(-R * 0.22, my + 3)
        for k in range(1, 7):
            p.lineTo(-R * 0.22 + k * R * 0.44 / 6, my + (5 if k % 2 else -3))
        c.drawPath(p, S(BLACK, R * 0.07))
    else:
        w, h = {"grin": (0.36, 0.2), "O": (0.15, 0.22), "scream": (0.26, 0.34)}[m]
        p = skia.Path()
        if m == "grin":
            p.moveTo(-R * w, my - R * 0.12)
            p.quadTo(0, my + R * 0.45, R * w, my - R * 0.12)
            p.close()
        else:
            p.addOval(skia.Rect(-R * w, my - R * h * 0.6, R * w, my + R * h))
        c.drawPath(p, P(skia.Color(110, 20, 30)))
        if m == "grin":
            c.save()
            c.clipPath(p, doAntiAlias=True)
            c.drawRect(skia.Rect(-R, my - R * 0.2, R, my - R * 0.02), P(WHITE))
            c.restore()
        else:
            c.save()
            c.clipPath(p, doAntiAlias=True)
            c.drawCircle(0, my + R * h, R * w * 0.8, P(skia.Color(220, 80, 95)))
            c.restore()
        c.drawPath(p, S(BLACK, R * 0.07))
    sw = pose.get("sweat", 0.0)
    if sw > 0:
        sx, sy = R * 0.78, -R * 0.35 + sw * R * 0.4
        p = skia.Path()
        p.moveTo(sx, sy - R * 0.22)
        p.quadTo(sx + R * 0.13, sy, sx, sy + R * 0.06)
        p.quadTo(sx - R * 0.13, sy, sx, sy - R * 0.22)
        c.drawPath(p, P(skia.Color(150, 210, 255, int(230 * min(1, sw * 2)))))
        c.drawPath(p, S(BLACK, 3))


def helmet(c, R, lamp_on=True, glow=True):
    c.save()
    c.translate(0, -R * 0.42)          # sits above the brows, never over the eyes
    p = skia.Path()
    p.addArc(skia.Rect(-R * 1.05, -R * 1.25, R * 1.05, R * 0.6), 180, 180)
    p.close()
    c.drawPath(p, P(skia.Color(215, 160, 40)))
    c.drawPath(p, S(BLACK, R * 0.09))
    c.drawRoundRect(skia.Rect(-R * 1.25, -R * 0.38, R * 1.25, -R * 0.2), R * 0.08, R * 0.08, P(skia.Color(190, 135, 30)))
    c.drawRoundRect(skia.Rect(-R * 1.25, -R * 0.38, R * 1.25, -R * 0.2), R * 0.08, R * 0.08, S(BLACK, R * 0.08))
    c.drawCircle(0, -R * 0.62, R * 0.2, P(skia.Color(255, 245, 190) if lamp_on else skia.Color(90, 90, 80)))
    c.drawCircle(0, -R * 0.62, R * 0.2, S(BLACK, R * 0.07))
    if lamp_on and glow:
        c.drawCircle(0, -R * 0.62, R * 0.7, P(skia.Color(255, 230, 150, 70), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, R * 0.4)))
    c.restore()


def miner(c, x, y, s, pose):
    """Returns world positions of both hands {'L': (x, y), 'R': (x, y)} for attaching props."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.rotate(pose.get("lean", 0.0))
    hip = (0, -120)
    neck = (0, -215)
    legs = pose.get("legs", [(6, 0), (-6, 0)])
    arms = pose.get("arms", [(12, 10), (12, 10)])
    hands = {}
    # back leg/arm first (right side drawn second so it overlaps)
    for side, (ha, ka) in zip((-1, 1), legs):
        limb(c, chain(hip, (-side * 0 + ha, ka), (62, 62)), 18)
    limb(c, [hip, neck], 22)                                   # spine
    for side, (sa, ea), key in zip((-1, 1), arms, ("L", "R")):
        pts = chain((0, -198), (side * sa, side * ea), (55, 52))
        limb(c, pts, 16)
        c.drawCircle(*pts[-1], 13, P(WHITE))
        c.drawCircle(*pts[-1], 13, S(BLACK, 6))
        m = c.getTotalMatrix()
        hp = m.mapXY(*pts[-1])
        hands[key] = (hp.x(), hp.y())
    # head
    c.save()
    c.translate(0, -262)
    c.rotate(pose.get("head_tilt", 0.0))
    R = 52
    c.drawCircle(0, 0, R, P(WHITE))
    c.drawCircle(0, 0, R, S(BLACK, 7))
    face(c, pose, R)
    if pose.get("helmet", True):
        helmet(c, R, pose.get("lamp", True))
    c.restore()
    c.restore()
    return hands


def cage(c, x, y, s, bird="sing", t=0.0, swing=0.0):
    """Brass birdcage hanging from (x, y) (top ring), with a canary. bird: 'sing' | 'silent'."""
    c.save()
    c.translate(x, y)
    c.rotate(swing)
    c.scale(s, s)
    brass, dark = skia.Color(220, 170, 70), skia.Color(150, 105, 35)
    c.drawCircle(0, 8, 8, S(BLACK, 9))
    c.drawCircle(0, 8, 8, S(brass, 4))
    top, bot, w = 16, 150, 62
    dome = skia.Path()
    dome.moveTo(-w, 60)
    dome.cubicTo(-w, top, w, top, w, 60)
    # bird first (behind the bars)
    bx, by = 0, 112
    bob = math.sin(t * 9) * 2 if bird == "sing" else 0
    c.save()
    c.translate(bx, by + bob)
    body = skia.Path()
    body.addOval(skia.Rect(-26, -20, 22, 20))
    c.drawPath(body, P(skia.Color(255, 215, 40)))
    c.drawPath(body, S(BLACK, 5))
    c.drawCircle(18, -26, 15, P(skia.Color(255, 215, 40)))
    c.drawCircle(18, -26, 15, S(BLACK, 5))
    tail = skia.Path()
    tail.moveTo(-24, 0)
    tail.lineTo(-44, 10)
    tail.lineTo(-40, -6)
    tail.close()
    c.drawPath(tail, P(skia.Color(240, 190, 30)))
    c.drawPath(tail, S(BLACK, 4))
    c.drawCircle(22, -29, 3.5, P(BLACK))
    open_ = bird == "sing" and math.sin(t * 9) > 0
    beak = skia.Path()
    beak.moveTo(31, -30)
    beak.lineTo(44, -26 - (5 if open_ else 0))
    beak.lineTo(31, -24)
    if open_:
        beak.moveTo(31, -24)
        beak.lineTo(43, -18)
        beak.lineTo(31, -20)
    c.drawPath(beak, P(skia.Color(255, 140, 40)))
    c.drawPath(beak, S(BLACK, 3))
    c.restore()
    c.drawLine(-w + 8, 130, w - 8, 130, S(BLACK, 8))       # perch
    c.drawLine(-w + 8, 130, w - 8, 130, S(dark, 4))
    # bars + base
    for k in range(-4, 5):
        xb = k * w / 4.5
        yt = 60 - (1 - (xb / w) ** 2) * 40
        c.drawLine(xb, yt, xb, bot, S(BLACK, 7))
        c.drawLine(xb, yt, xb, bot, S(brass, 3.5))
    c.drawPath(dome, S(BLACK, 9))
    c.drawPath(dome, S(brass, 5))
    c.drawRoundRect(skia.Rect(-w - 8, bot - 4, w + 8, bot + 14), 6, 6, P(dark))
    c.drawRoundRect(skia.Rect(-w - 8, bot - 4, w + 8, bot + 14), 6, 6, S(BLACK, 6))
    c.restore()
    # music notes while singing
    if bird == "sing":
        for k in range(3):
            ph = (t * 1.3 + k / 3) % 1.0
            nx = x + s * (50 + ph * 70 + k * 10)
            ny = y + s * (60 - ph * 110)
            a = int(255 * math.sin(math.pi * ph))
            note(c, nx, ny, s * 0.55, a, double=k % 2 == 0)


def note(c, x, y, s, a, double=False):
    """A drawn music note (no font glyph needed)."""
    ink, fill = skia.Color(18, 14, 16, a), skia.Color(255, 230, 120, a)
    heads = [(0, 0)] + ([(34, -8)] if double else [])
    for hx, hy in heads:
        r = skia.Rect(x + (hx - 13) * s, y + (hy - 9) * s, x + (hx + 13) * s, y + (hy + 9) * s)
        c.drawOval(r, P(ink))
        c.drawOval(r.makeInset(3 * s, 3 * s), P(fill))
        c.drawLine(x + (hx + 11) * s, y + hy * s, x + (hx + 11) * s, y + (hy - 55) * s, S(ink, 7 * s))
        c.drawLine(x + (hx + 11) * s, y + hy * s, x + (hx + 11) * s, y + (hy - 55) * s, S(fill, 3 * s))
    if double:
        c.drawLine(x + 11 * s, y - 55 * s, x + 45 * s, y - 63 * s, S(ink, 10 * s))
        c.drawLine(x + 11 * s, y - 55 * s, x + 45 * s, y - 63 * s, S(fill, 5 * s))
    else:
        f = skia.Path()
        f.moveTo(x + 11 * s, y - 55 * s)
        f.quadTo(x + 30 * s, y - 45 * s, x + 26 * s, y - 28 * s)
        c.drawPath(f, S(ink, 7 * s))
        c.drawPath(f, S(fill, 3 * s))
