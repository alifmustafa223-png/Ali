"""2.5D/3D camera for the Skia toon videos: real perspective projection so the classic toon characters and props live
in a 3D set and the camera can orbit, dolly, crane, tilt and roll around them (flat characters in a deep world).

World axes: X right, Y DOWN (like the screen), Z forward/into the screen. Units ~ pixels at distance F.

    cam = Cam.orbit(center=(0, 0, 0), radius=900, yaw=0.3, height=-250, roll=0, f=1000)
    w = World()
    w.floor(x0, x1, z0, z1, y, cols, plank=120)        # perspective planks / tiles
    w.box((x0, y0, z0), (x1, y1, z1), col)              # solid box, back faces culled, shaded by face direction
    w.panel(pts3d, col) / w.shape(pts3d, col)           # any planar polygon (e.g. a rounded window outline)
    w.sprite((X, Y, Z), draw_fn, layer="main")          # draw_fn(c, sx, sy, s): toon person, prop... at scale s
    w.render(c, cam, fog=(r,g,b), fog_near, fog_far, bg_blur=6)   # painter's sort, fog, depth-of-field on 'bg'
Every function is pure in its inputs (frames render independently).
"""
import math

import skia

from toon import C, P, blur

W, H = 1080, 1920


class Cam:
    def __init__(self, pos=(0.0, 0.0, -1000.0), yaw=0.0, pitch=0.0, roll=0.0, f=1000.0, cx=W / 2, cy=H / 2):
        self.x, self.y, self.z = pos
        self.yaw, self.pitch, self.roll, self.f = yaw, pitch, roll, f
        self.cx, self.cy = cx, cy
        self.cy_, self.sy_ = math.cos(yaw), math.sin(yaw)
        self.cp_, self.sp_ = math.cos(pitch), math.sin(pitch)

    @staticmethod
    def orbit(center, radius, yaw, height=0.0, roll=0.0, f=1000.0, cy=H / 2, look_y=0.0):
        """Camera on a circle around `center` (radius in XZ), `height` above it (negative = higher, Y is down),
        always looking at center (+look_y)."""
        cx, cyw, cz = center
        px = cx - radius * math.sin(yaw)
        pz = cz - radius * math.cos(yaw)
        py = cyw + height
        pitch = math.atan2((cyw + look_y) - py, radius)
        return Cam((px, py, pz), yaw, pitch, roll, f, cy=cy)

    def to_cam(self, X, Y, Z):
        dx, dy, dz = X - self.x, Y - self.y, Z - self.z
        x1 = dx * self.cy_ - dz * self.sy_
        z1 = dx * self.sy_ + dz * self.cy_
        return x1, dy * self.cp_ - z1 * self.sp_, dy * self.sp_ + z1 * self.cp_

    def proj_cam(self, x, y, z):
        s = self.f / z
        return self.cx + x * s, self.cy + y * s, s, z

    def clip_poly(self, pts, near=40.0):
        """Camera-space polygon clipped to z >= near (Sutherland-Hodgman), projected. [] if fully behind."""
        cp = [self.to_cam(*q) for q in pts]
        out = []
        n = len(cp)
        for i in range(n):
            a, b = cp[i], cp[(i + 1) % n]
            ina, inb = a[2] >= near, b[2] >= near
            if ina:
                out.append(a)
            if ina != inb:
                k = (near - a[2]) / (b[2] - a[2])
                out.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, near))
        return [self.proj_cam(*q) for q in out]

    def project(self, X, Y, Z):
        dx, dy, dz = X - self.x, Y - self.y, Z - self.z
        x1 = dx * self.cy_ - dz * self.sy_
        z1 = dx * self.sy_ + dz * self.cy_
        y2 = dy * self.cp_ - z1 * self.sp_
        z2 = dy * self.sp_ + z1 * self.cp_
        if z2 < 30:
            return None
        s = self.f / z2
        return self.cx + x1 * s, self.cy + y2 * s, s, z2


def _mix(col, fog, k):
    return tuple(int(col[i] + (fog[i] - col[i]) * k) for i in range(3))


class World:
    def __init__(self):
        self.items = []  # (kind, data, layer)

    def panel(self, pts, col, layer="main", alpha=255, outline=None, light=1.0, bias=0.0):
        self.items.append(("poly", (pts, col, alpha, outline, light), layer, bias))

    def custom(self, pts, fn, layer="main", bias=0.0):
        """fn(c, cam, path, fk): draw anything inside/along the projected polygon `pts` (e.g. sky seen through a window)."""
        self.items.append(("custom", (pts, fn), layer, bias))

    shape = panel

    def box(self, p0, p1, col, layer="main", outline=(30, 22, 18), top_light=1.12, side_dark=0.78, alpha=255, bias=0.0):
        x0, y0, z0 = p0
        x1, y1, z1 = p1
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        faces = [((0, 1, 2, 3), 1.0), ((5, 4, 7, 6), 0.7), ((4, 0, 3, 7), side_dark), ((1, 5, 6, 2), side_dark),
                 ((4, 5, 1, 0), top_light), ((3, 2, 6, 7), 0.6)]
        for idx, sh in faces:
            self.items.append(("face", ([v[i] for i in idx], col, sh, outline, alpha), layer, bias))

    def floor(self, x0, x1, z0, z1, y, cols, plank=120.0, depth_step=None, layer="main", gap=(0, 0, 0)):
        """Planks running along Z (like a deck / aisle). cols = list of colours cycled per plank."""
        n = int((x1 - x0) / plank)
        dz = depth_step or (z1 - z0)
        for i in range(n):
            xa, xb = x0 + i * plank, x0 + (i + 1) * plank - 4
            z = z0
            k = 0
            while z < z1:
                zb = min(z1, z + dz)
                col = cols[(i + k) % len(cols)]
                self.items.append(("poly", ([(xa, y, z), (xb, y, z), (xb, y, zb), (xa, y, zb)], col, 255, gap, 1.0), layer, 0.0))
                z = zb
                k += 1

    def sprite(self, pos, fn, layer="main", bias=0.0):
        self.items.append(("sprite", (pos, fn), layer, bias))

    # ---------- render ----------
    def _depth(self, cam, item):
        kind, d, _, bias = item
        if kind == "sprite":
            p = cam.project(*d[0])
            return p[3] - bias if p else -1
        cl = cam.clip_poly(d[0])
        if len(cl) < 3:
            return -1
        return sum(q[3] for q in cl) / len(cl) - bias

    def render(self, c, cam, fog=(10, 10, 20), fog_near=1500, fog_far=9000, bg_blur=0.0, fog_max=0.85):
        order = []
        for it in self.items:
            z = self._depth(cam, it)
            if z > 0:
                order.append((z, it))
        order.sort(key=lambda a: -a[0])
        c.save()
        c.translate(cam.cx, cam.cy)
        c.rotate(cam.roll)
        c.translate(-cam.cx, -cam.cy)
        for layer in ("bg", "main"):
            if layer == "bg" and bg_blur > 0.5:
                c.saveLayer(None, P(ImageFilter=skia.ImageFilters.Blur(bg_blur, bg_blur)))
            for z, (kind, d, ly, _b) in order:
                if ly != layer:
                    continue
                fk = max(0.0, min(fog_max, (z - fog_near) / (fog_far - fog_near)))
                if kind == "sprite":
                    p = cam.project(*d[0])
                    d[1](c, p[0], p[1], p[2], fk)
                    continue
                pts2 = cam.clip_poly(d[0])
                if len(pts2) < 3:
                    continue
                path = skia.Path()
                path.moveTo(pts2[0][0], pts2[0][1])
                for q in pts2[1:]:
                    path.lineTo(q[0], q[1])
                path.close()
                if kind == "custom":
                    c.save()
                    d[1](c, cam, path, fk)
                    c.restore()
                    continue
                if kind == "face":
                    m = len(pts2)
                    area = sum(pts2[i][0] * pts2[(i + 1) % m][1] - pts2[(i + 1) % m][0] * pts2[i][1] for i in range(m))
                    _, col, sh, outline, alpha = d
                    if area <= 0 and alpha == 255:  # back face (see-through boxes keep them)
                        continue
                    cc = _mix(tuple(min(255, v * sh) for v in col), fog, fk)
                    c.drawPath(path, P(C(*cc, alpha)))
                    if outline:
                        c.drawPath(path, P(C(*_mix(outline, fog, fk), max(alpha, 120)), Style=skia.Paint.kStroke_Style,
                                           StrokeWidth=max(1.5, 4 * pts2[0][2]), StrokeJoin=skia.Paint.kRound_Join))
                else:
                    _, col, alpha, outline, light = d
                    cc = _mix(tuple(min(255, v * light) for v in col), fog, fk)
                    c.drawPath(path, P(C(*cc, alpha)))
                    if outline:
                        c.drawPath(path, P(C(*_mix(outline, fog, fk), alpha), Style=skia.Paint.kStroke_Style,
                                           StrokeWidth=max(1.0, 3 * pts2[0][2])))
            if layer == "bg" and bg_blur > 0.5:
                c.restore()
        c.restore()


def rounded_rect_pts(cx, cy, w, h, r, z=None, plane="xy", n=6):
    """Outline points of a rounded rectangle in a world plane (plane 'xy' at depth z, or 'zy' at x=cx)."""
    pts = []
    corners = [(w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180)]
    for ox, oy, a0 in corners:
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            u, v = ox + math.cos(a) * r, oy + math.sin(a) * r
            pts.append((cx + u, cy + v, z) if plane == "xy" else (cx, cy + v, z + u))
    return pts


def path2d(cam, pts):
    p = skia.Path()
    first = True
    for q in pts:
        r = cam.project(*q)
        if r is None:
            return None
        (p.moveTo if first else p.lineTo)(r[0], r[1])
        first = False
    p.close()
    return p


def fogged(col, fk, fog=(10, 10, 20)):
    return _mix(col, fog, fk)


def shake(t, at, amp=18.0, dur=0.35):
    """Camera shake offset (dx, dy, droll) after an impact at `at`: decaying noise."""
    k = t - at
    if not 0 <= k < dur:
        return 0.0, 0.0, 0.0
    e = (1 - k / dur) ** 2
    return amp * e * math.sin(k * 90), amp * e * math.cos(k * 77), 1.2 * e * math.sin(k * 60)


def blurred_sprite(c, sigma, fn):
    """Draw fn() into a blurred layer (depth of field for one object)."""
    if sigma < 0.6:
        fn()
        return
    c.saveLayer(None, P(ImageFilter=skia.ImageFilters.Blur(sigma, sigma)))
    fn()
    c.restore()


_ = blur  # re-export convenience
