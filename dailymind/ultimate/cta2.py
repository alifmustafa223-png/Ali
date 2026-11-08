"""CTA v2: sharp vector LIKE + SUBSCRIBE end card (Skia), smooth spring motion. Replaces make_salt.draw_cta.

    draw_cta2(c, t, t_like, t_sub, title="Learned something new?")

All shapes are anti-aliased vectors (no PIL bitmaps):
  - a dark glass card that rises in with a spring
  - a channel avatar + handle line
  - a thumbs-up drawn as a path: white outline -> fills blue on the tap, springs up, particle burst
  - a red SUBSCRIBE pill: pressed with a ripple, morphs to grey SUBSCRIBED with a drawn check mark
  - a bell that pops in and rings (damped swing) with sparkles
  - a pointer hand that glides on a smooth curve between the two taps and dips on each tap
Times are seconds inside the CTA scene; t_like / t_sub are the tap moments (put them on the spoken words).
"""
import math

import skia

from toon import C, P, S, FB, blur, ease, lin, out_back, rad, spring

W = 1080
FM = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-Medium.otf")
BLUE, RED, GREY = (62, 140, 255), (235, 35, 45), (70, 72, 80)


def _txt(c, s, x, y, size, col, a=255, bold=True, align="center"):
    f = skia.Font(FB if bold else FM, size)
    w = f.measureText(s)
    ox = x - w / 2 if align == "center" else x
    c.drawString(s, ox + 2, y + 3, f, P(C(0, 0, 0, int(a * 0.35)), MaskFilter=blur(2)))
    c.drawString(s, ox, y, f, P(C(*col, a)))
    return w


def thumb_path():
    """Thumbs-up in a 0..200 box (cuff on the left, fist on the right, thumb up)."""
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect(0, 86, 44, 200), 10, 10))
    q = skia.Path()
    q.moveTo(58, 92)
    q.lineTo(96, 30)
    q.cubicTo(104, 12, 132, 14, 132, 40)
    q.lineTo(124, 84)
    q.lineTo(178, 84)
    q.cubicTo(198, 84, 206, 104, 196, 120)
    q.cubicTo(204, 132, 200, 150, 188, 156)
    q.cubicTo(196, 168, 190, 186, 176, 190)
    q.cubicTo(180, 204, 168, 214, 154, 214)
    q.lineTo(80, 214)
    q.cubicTo(68, 214, 58, 206, 58, 194)
    q.close()
    p.addPath(q)
    return p


THUMB = thumb_path()


def bell_path():
    p = skia.Path()
    p.moveTo(0, -46)
    p.cubicTo(-30, -46, -38, -20, -38, 4)
    p.lineTo(-38, 18)
    p.lineTo(-50, 34)
    p.lineTo(50, 34)
    p.lineTo(38, 18)
    p.lineTo(38, 4)
    p.cubicTo(38, -20, 30, -46, 0, -46)
    p.close()
    return p


BELL = bell_path()


def hand(c, x, y, s, press):
    """Pointer hand (index finger up), tip at (x, y)."""
    c.save()
    c.translate(x, y + 10 * press)
    c.scale(s * (1 - 0.08 * press), s * (1 - 0.08 * press))
    p = skia.Path()
    p.moveTo(0, 0)
    p.cubicTo(-14, 0, -18, 10, -18, 22)
    p.lineTo(-18, 70)
    p.cubicTo(-30, 62, -48, 66, -48, 82)
    p.cubicTo(-48, 96, -30, 110, -24, 130)
    p.cubicTo(-16, 152, 6, 170, 34, 170)
    p.cubicTo(62, 170, 80, 152, 80, 122)
    p.lineTo(80, 80)
    p.cubicTo(80, 64, 60, 62, 54, 72)
    p.cubicTo(54, 58, 34, 56, 30, 68)
    p.cubicTo(30, 56, 18, 52, 18, 64)
    p.lineTo(18, 22)
    p.cubicTo(18, 10, 14, 0, 0, 0)
    p.close()
    c.drawPath(p, P(C(0, 0, 0, 90), MaskFilter=blur(10)))
    c.drawPath(p, P(Shader=lin((0, 0), (40, 170), [C(255, 255, 255), C(225, 228, 235)])))
    c.drawPath(p, S(C(30, 30, 40), 6))
    c.restore()


def draw_cta2(c, t, t_like, t_sub, title="Learned something new?", handle="@thedailymind0"):
    # card rises in
    k = out_back(min(1, t / 0.45), 1.3)
    a = int(255 * min(1, t / 0.25))
    cx, cy = W / 2, 1080
    c.save()
    c.translate(0, 120 * (1 - k))
    card = skia.RRect.MakeRectXY(skia.Rect(cx - 430, cy - 470, cx + 430, cy + 560), 56, 56)
    c.drawRRect(card, P(C(0, 0, 0, int(a * 0.55)), MaskFilter=blur(30)))
    c.drawRRect(card, P(Shader=lin((0, cy - 470), (0, cy + 560), [C(36, 30, 52, int(a * 0.92)), C(18, 15, 28, int(a * 0.95))])))
    c.drawRRect(card, P(Shader=lin((cx - 430, cy - 470), (cx + 430, cy + 560), [C(255, 200, 90, a), C(170, 110, 255, a), C(80, 200, 255, a)]),
                        Style=skia.Paint.kStroke_Style, StrokeWidth=4))
    tsize = 66
    while skia.Font(FB, tsize).measureText(title) > 760:
        tsize -= 2
    _txt(c, title, cx, cy - 360, tsize, (255, 255, 255), a)
    # avatar + handle
    c.drawCircle(cx - 150, cy - 255, 44, P(Shader=rad(cx - 165, cy - 270, 60, [C(255, 215, 110), C(220, 150, 40)])))
    c.drawCircle(cx - 150, cy - 255, 44, S(C(255, 255, 255, a), 4))
    _txt(c, "DM", cx - 150, cy - 240, 38, (60, 30, 10), a)
    _txt(c, handle, cx - 92, cy - 240, 40, (210, 210, 225), a, bold=False, align="left")

    # LIKE
    liked = t >= t_like
    lk = spring(t, t_like, 2.6, 5.0) if liked else 0.0
    ls = 1.0 + 0.22 * lk
    tx, ty = cx - 100, cy - 170
    c.save()
    c.translate(tx + 100, ty + 115)
    c.scale(ls, ls)
    c.rotate(-8 * lk)
    c.translate(-100, -115)
    if liked:
        fill = min(1, (t - t_like) / 0.18)
        c.drawPath(THUMB, P(Shader=lin((0, 0), (200, 214), [C(110, 175, 255), C(*BLUE)]), Alphaf=fill))
    c.drawPath(THUMB, S(C(255, 255, 255, a), 10))
    c.restore()
    if liked and t - t_like < 0.7:
        u = (t - t_like) / 0.7
        for i in range(12):
            ang = i / 12 * 2 * math.pi
            r0, r1 = 130 + 120 * ease(u), 150 + 160 * ease(u)
            c.drawLine(tx + 100 + math.cos(ang) * r0, ty + 115 + math.sin(ang) * r0, tx + 100 + math.cos(ang) * r1, ty + 115 + math.sin(ang) * r1,
                       S(C(*BLUE, int(255 * (1 - u))), 8))
    _txt(c, "LIKE", cx, cy + 130, 52, (120, 175, 255) if liked else (255, 255, 255), a)

    # SUBSCRIBE pill
    subbed = t >= t_sub + 0.12
    press = 0.0
    if t_sub - 0.05 <= t < t_sub + 0.25:
        press = math.sin(math.pi * (t - (t_sub - 0.05)) / 0.3)
    bw, bh = 560, 140
    bx, by = cx - bw / 2, cy + 200
    c.save()
    c.translate(cx, by + bh / 2)
    c.scale(1 - 0.06 * press, 1 - 0.06 * press)
    c.translate(-cx, -(by + bh / 2))
    pill = skia.RRect.MakeRectXY(skia.Rect(bx, by, bx + bw, by + bh), bh / 2, bh / 2)
    c.drawRRect(pill, P(C(0, 0, 0, 110), MaskFilter=blur(14)))
    m = min(1, max(0, (t - t_sub - 0.12) / 0.2))
    col = tuple(int(RED[j] + (GREY[j] - RED[j]) * m) for j in range(3))
    c.drawRRect(pill, P(Shader=lin((0, by), (0, by + bh), [C(*[min(255, v + 30) for v in col]), C(*col)])))
    if t >= t_sub:  # ripple from the tap point
        u = min(1, (t - t_sub) / 0.5)
        c.save()
        c.clipRRect(pill, doAntiAlias=True)
        c.drawCircle(cx + 140, by + bh / 2, 40 + 420 * ease(u), P(C(255, 255, 255, int(120 * (1 - u)))))
        c.restore()
    if subbed:
        ck = skia.Path()
        lab_w = skia.Font(FB, 52).measureText("SUBSCRIBED")
        x0 = cx - (lab_w + 64) / 2  # check + gap + label, centred together
        ck.moveTo(x0, by + 72)
        ck.lineTo(x0 + 18, by + 92)
        ck.lineTo(x0 + 46, by + 52)
        c.drawPath(ck, S(C(255, 255, 255), 10))
        _txt(c, "SUBSCRIBED", x0 + 64 + lab_w / 2, by + 90, 52, (255, 255, 255))
    else:
        _txt(c, "SUBSCRIBE", cx, by + 92, 58, (255, 255, 255))
    c.restore()

    # bell pops in and rings
    if subbed:
        bk = out_back(min(1, (t - t_sub - 0.12) / 0.3), 2.0)
        swing = 22 * spring(t, t_sub + 0.3, 3.2, 3.0)
        c.save()
        c.translate(cx, by + bh + 105)
        c.scale(bk, bk)
        c.rotate(swing)
        c.drawPath(BELL, P(Shader=lin((0, -46), (0, 34), [C(255, 225, 120), C(240, 175, 40)])))
        c.drawPath(BELL, S(C(120, 80, 10), 5))
        c.drawCircle(0, 44, 11, P(C(240, 175, 40)))
        c.restore()
        for i in range(6):
            ang = i / 6 * 2 * math.pi + t * 2
            u = (t - t_sub) % 1.2 / 1.2
            r = 90 + 30 * math.sin(u * math.pi)
            sx, sy = cx + math.cos(ang) * r, by + bh + 105 + math.sin(ang) * r * 0.6
            sp = skia.Path()
            for j in range(8):
                rr = 14 if j % 2 == 0 else 5
                aa = j / 8 * 2 * math.pi
                (sp.moveTo if j == 0 else sp.lineTo)(sx + math.cos(aa) * rr, sy + math.sin(aa) * rr)
            sp.close()
            c.drawPath(sp, P(C(255, 230, 140, 220)))
    c.restore()

    # pointer hand: glides in, taps LIKE, glides to SUBSCRIBE, taps, leaves
    p0 = (cx + 380, cy + 760)
    p1 = (tx + 150, ty + 150)
    p2 = (cx + 150, by + bh / 2 + 10)
    if t < t_like:
        u = ease(min(1, max(0, (t - (t_like - 0.7)) / 0.7)))
        hx, hy = p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u - 120 * math.sin(math.pi * u)
    elif t < t_sub:
        u = ease(min(1, max(0, (t - (t_sub - 0.6)) / 0.6)))
        hx, hy = p1[0] + (p2[0] - p1[0]) * u, p1[1] + (p2[1] - p1[1]) * u - 80 * math.sin(math.pi * u)
    else:
        u = ease(min(1, max(0, (t - (t_sub + 0.5)) / 0.6)))
        hx, hy = p2[0] + (p0[0] - p2[0]) * u, p2[1] + (p0[1] - p2[1]) * u
    tap = 0.0
    for tt in (t_like, t_sub):
        if tt - 0.08 <= t < tt + 0.2:
            tap = math.sin(math.pi * (t - (tt - 0.08)) / 0.28)
    if t > t_like - 0.7 and not (t > t_sub + 1.1):
        hand(c, hx, hy, 0.95, tap)
