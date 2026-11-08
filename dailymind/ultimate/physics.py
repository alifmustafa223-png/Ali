"""Small deterministic physics for the toon videos (every function is a pure function of time t,
so any frame can be rendered on its own and parallel renders always agree).

    ball_path(t, x0, y0, vx, vy, floor, ...)  -> (x, y, rot, squash)  bouncing ball with gravity, restitution,
                                                  rolling friction and squash-and-stretch on impact
    draw_ball(c, x, y, r, rot, squash)         -> football (pentagon pattern, shading, motion squash)
    confetti(c, t, t0, x, y, n, seed)          -> burst of paper confetti: gravity, air drag, 3D tumble
    cloth(c, t, x, y, w, h, wind, ...)         -> a hanging sheet (napkin) simulated with Verlet + constraints
    spring_v(t, at, amp, freq, damp)           -> damped spring value (overshoot + settle)
    jiggle(t, at, k)                           -> squash factor for soft bodies after a hit
    dust(c, t, t0, x, y)                       -> impact dust puff (expanding, fading, drifting up)
"""
import math
import random

import skia

from toon import C, P, S, blur, ease, lin, rad

G = 2600.0  # px/s^2


def spring_v(t, at, amp=1.0, freq=3.0, damp=4.0):
    k = t - at
    return 0.0 if k < 0 else amp * math.exp(-damp * k) * math.cos(2 * math.pi * freq * k)


def jiggle(t, at, k=0.18):
    return k * spring_v(t, at, 1.0, 4.0, 6.0)


def ball_path(t, x0, y0, vx, vy, floor, r=40, e=0.62, mu=0.88, dt=1 / 240, t_start=0.0):
    """Simulate from t_start; returns (x, y, rot_degrees, squash 0..0.35, last_impact_time)."""
    x, y = x0, y0
    s = 0.0
    squash, last_hit = 0.0, -10.0
    k = t - t_start
    if k <= 0:
        return x0, y0, 0.0, 0.0, -10.0
    rot = 0.0
    while s < k:
        vy += G * dt
        x += vx * dt
        y += vy * dt
        rot += vx * dt / r * 57.3
        if y > floor - r and vy > 0:
            y = floor - r
            if abs(vy) > 60:
                last_hit = t_start + s
            vy = -vy * e
            vx *= mu
            if abs(vy) < 40:
                vy = 0
        s += dt
    since = t - last_hit
    if 0 <= since < 0.18:
        squash = 0.3 * (1 - since / 0.18)
    return x, y, rot, squash, last_hit


def draw_ball(c, x, y, r, rot=0.0, squash=0.0, shadow_floor=None):
    if shadow_floor is not None:
        h = max(0.0, shadow_floor - (y + r))
        a = int(120 * max(0.15, 1 - h / 600))
        sw = r * (1.2 - min(0.7, h / 900))
        c.drawOval(skia.Rect(x - sw, shadow_floor - r * 0.18, x + sw, shadow_floor + r * 0.18), P(C(0, 0, 0, a), MaskFilter=blur(8)))
    c.save()
    c.translate(x, y + r * squash * 0.6)
    c.scale(1 + squash, 1 - squash)
    c.rotate(rot)
    c.drawCircle(0, 0, r, P(Shader=rad(-r * 0.35, -r * 0.4, r * 1.6, [C(255, 255, 255), C(230, 232, 238), C(150, 155, 170)], [0, 0.55, 1])))
    for k in range(5):  # pentagon patches
        a = k / 5 * 2 * math.pi
        px, py = math.cos(a) * r * 0.62, math.sin(a) * r * 0.62
        p = skia.Path()
        for j in range(5):
            aa = a + j / 5 * 2 * math.pi
            (p.moveTo if j == 0 else p.lineTo)(px + math.cos(aa) * r * 0.2, py + math.sin(aa) * r * 0.2)
        p.close()
        c.drawPath(p, P(C(30, 30, 40)))
    p = skia.Path()
    for j in range(5):
        aa = j / 5 * 2 * math.pi - math.pi / 2
        (p.moveTo if j == 0 else p.lineTo)(math.cos(aa) * r * 0.26, math.sin(aa) * r * 0.26)
    p.close()
    c.drawPath(p, P(C(30, 30, 40)))
    c.drawCircle(0, 0, r, S(C(40, 40, 50), max(2, r * 0.07)))
    c.restore()
    c.drawOval(skia.Rect(x - r * 0.55, y - r * 0.7, x - r * 0.1, y - r * 0.4), P(C(255, 255, 255, 150)))


CONF_COLS = [(255, 80, 90), (255, 200, 60), (80, 200, 255), (120, 230, 140), (220, 120, 255), (255, 255, 255)]


def confetti(c, t, t0, x, y, n=60, seed=1, power=1.0, floor=1900):
    """Paper confetti burst at (x, y) from t0: each piece has gravity, quadratic air drag and a 3D flip."""
    k = t - t0
    if k <= 0:
        return
    r = random.Random(seed)
    for i in range(n):
        ang = r.uniform(-math.pi * 0.95, -math.pi * 0.05)
        sp = r.uniform(600, 1500) * power
        vx, vy = math.cos(ang) * sp, math.sin(ang) * sp
        drag = r.uniform(1.6, 2.6)
        # closed-form motion with linear drag + terminal velocity
        e = math.exp(-drag * k)
        vt = G / drag * 0.12
        px = x + vx / drag * (1 - e) + 30 * math.sin(k * r.uniform(3, 6) + i)
        py = y + vy / drag * (1 - e) + vt * (k - (1 - e) / drag)
        if py > floor:
            py = floor
        flip = math.cos(k * r.uniform(6, 14) + i)
        w, h = r.uniform(10, 18), r.uniform(6, 10)
        col = CONF_COLS[i % len(CONF_COLS)]
        a = int(255 * max(0.0, min(1.0, (3.2 - k) / 0.8)))
        c.save()
        c.translate(px, py)
        c.rotate(k * r.uniform(-400, 400))
        c.drawRect(skia.Rect(-w / 2, -h / 2 * abs(flip) - 0.5, w / 2, h / 2 * abs(flip) + 0.5), P(C(*[int(v * (0.7 + 0.3 * abs(flip))) for v in col], a)))
        c.restore()


def cloth(c, t, x, y, w, h, wind=1.0, pins="top", col=(250, 248, 240), ink=None, nx=8, ny=6, steps=None):
    """A sheet hanging from its top edge (pins='top') or held at the two top corners ('corners'), drawn as a mesh.
    Verlet integration from rest each call (deterministic in t). ink(c, u, v) -> optional pen lines in sheet coords."""
    dt = 1 / 120
    n_steps = steps or int(min(2.0, t) / dt) + 30
    pts = [[x - w / 2 + w * i / (nx - 1), y + h * j / (ny - 1)] for j in range(ny) for i in range(nx)]
    prev = [p[:] for p in pts]
    rest_x, rest_y = w / (nx - 1), h / (ny - 1)
    pinned = set(range(nx)) if pins == "top" else {0, nx - 1}
    base = [p[:] for p in pts]
    for s in range(n_steps):
        tt = t - (n_steps - s) * dt
        gust = wind * (180 * math.sin(tt * 2.1) + 90 * math.sin(tt * 5.3 + 1))
        for i, p in enumerate(pts):
            if i in pinned:
                p[0], p[1] = base[i][0], base[i][1]
                continue
            vx, vy = (p[0] - prev[i][0]) * 0.985, (p[1] - prev[i][1]) * 0.985
            prev[i] = p[:]
            row = i // nx
            p[0] += vx + gust * dt * dt * (row / ny)
            p[1] += vy + 900 * dt * dt
        for _ in range(3):
            for j in range(ny):
                for i in range(nx):
                    a = j * nx + i
                    for b, rest in ((a + 1, rest_x) if i < nx - 1 else (None, 0), (a + nx, rest_y) if j < ny - 1 else (None, 0)):
                        if b is None:
                            continue
                        dx, dy = pts[b][0] - pts[a][0], pts[b][1] - pts[a][1]
                        d = math.hypot(dx, dy) or 1e-6
                        diff = (d - rest) / d * 0.5
                        if a not in pinned:
                            pts[a][0] += dx * diff
                            pts[a][1] += dy * diff
                        if b not in pinned:
                            pts[b][0] -= dx * diff
                            pts[b][1] -= dy * diff
    # draw as quads with simple shading from the normal tilt
    for j in range(ny - 1):
        for i in range(nx - 1):
            a, b, d, e = j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i
            q = skia.Path()
            q.moveTo(*pts[a])
            q.lineTo(*pts[b])
            q.lineTo(*pts[d])
            q.lineTo(*pts[e])
            q.close()
            shade = 0.82 + 0.18 * math.cos((pts[b][0] - pts[a][0]) / rest_x * 1.2)
            c.drawPath(q, P(C(*[int(v * shade) for v in col])))
    outline = skia.Path()
    edge = [j * nx for j in range(ny)][::-1] + list(range(nx)) + [j * nx + nx - 1 for j in range(ny)] + [(ny - 1) * nx + i for i in range(nx)][::-1]
    outline.moveTo(*pts[edge[0]])
    for k in edge[1:]:
        outline.lineTo(*pts[k])
    c.drawPath(outline, S(C(150, 140, 120), 3))
    if ink:
        ink(c, pts, nx, ny)
    return pts


def dust(c, t, t0, x, y, col=(220, 210, 190), n=7):
    k = t - t0
    if not 0 <= k < 0.9:
        return
    for i in range(n):
        a = math.pi + i / (n - 1) * math.pi
        r = 30 + 160 * (1 - math.exp(-4 * k))
        c.drawCircle(x + math.cos(a) * r, y + math.sin(a) * r * 0.35 - 60 * k, 18 + 30 * k, P(C(*col, int(150 * (1 - k / 0.9))), MaskFilter=blur(10)))
