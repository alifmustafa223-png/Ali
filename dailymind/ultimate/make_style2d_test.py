"""10-second animated test of the polished 2D "Classic+ cartoon" style (hero frame: style2d_ultimate.py).

  python make_style2d_test.py frames  [VO_JSON] [WORDS_JSON]     -> renders ../cove_test/style2d/frames/%04d.png
  python make_style2d_test.py stills 1,90,180                     -> a few frames for checks
1080x1920, 30 fps. Static layers are drawn once at 1.25x (1350x2400) so the camera push-in is a crop, never an upscale;
only moving things are drawn per frame. Timing comes from the narration: VO_JSON (line starts) + WORDS_JSON (word times
from faster-whisper). Physics: the flip is a real ballistic arc (g = 9.81 m/s^2, 1.6 m = her height in px) solved so the
coin lands exactly in her hand on the catch frame; the spin is a real rotation (ellipse width |cos theta|).
"""
import json
import math
import os
import random
import sys
from multiprocessing import Pool

import numpy as np
import skia
from PIL import Image, ImageFilter

import toon as T

HERE = os.path.dirname(os.path.abspath(__file__))
CT = os.path.join(HERE, "..", "cove_test")
WORK = os.path.join(CT, "style2d")
FPS, DUR = 30, 10.0
NF = int(FPS * DUR)
W, H = 1080, 1920              # output
K = 1.25                       # world supersample: the push-in is a crop of a 1350x2400 render
WW, WH = int(W * K), int(H * K)
C, P, S = T.C, T.P, T.S
for f in ("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", "C:/Windows/Fonts/seguibl.ttf"):
    if os.path.exists(f):
        T.FB = skia.Typeface.MakeFromFile(f)
        break
SUN = (760, 820)
HOR = 940
BLUR = lambda r: skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r)  # noqa: E731

# ------------------------------------------------------------------------------------------------- timing (from the voice)
VO_JSON = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "frames" else os.path.join(CT, "vo_final.wav.times.json")
WORDS_JSON = sys.argv[3] if len(sys.argv) > 3 and sys.argv[1] == "frames" else os.path.join(WORK, "words.json")
VO = json.load(open(os.environ.get("S2D_VO", VO_JSON)))
WORDS = json.load(open(os.environ.get("S2D_WORDS", WORDS_JSON))) if os.path.exists(os.environ.get("S2D_WORDS", WORDS_JSON)) else {}
T_GOLD = WORDS.get("gold", VO["gold"] + 1.0)
T_THROW = WORDS.get("throw", VO["throw"] + 0.55)
T_COIN = WORDS.get("coin", VO["because"] + 0.95)
T_FAKE = WORDS["fake"] if "fake" in WORDS else VO["fake"]
T_SNAP = T_THROW                           # his head snaps on "throw it into the sea"
F_CATCH = int(round(T_FAKE * FPS))         # she catches it ON "fake"
N_FLIGHT = 18                              # 0.6 s flight
F_LAUNCH = F_CATCH - N_FLIGHT


def fr_t(f):
    return f / FPS


def smooth(x):
    return T.ease(x)


def ramp(t, t0, dur):
    return smooth((t - t0) / dur)


def snap(t, t0, frames=6, over=1.4):
    """0 -> 1 over `frames` frames with a small overshoot (out_back), never a 1-frame jump."""
    return T.out_back((t - t0) / (frames / FPS), over)


def lerp(a, b, u):
    return a + (b - a) * u


def lerp2(a, b, u):
    return tuple(lerp(x, y, u) for x, y in zip(a, b))


def noise1(t, seed, speed=1.0):
    """Smooth value noise in [-1, 1] (cosine-interpolated random knots)."""
    r = random.Random(seed)
    knots = [r.uniform(-1, 1) for _ in range(64)]
    x = t * speed
    i = int(math.floor(x))
    u = (1 - math.cos(math.pi * (x - i))) / 2
    return lerp(knots[i % 64], knots[(i + 1) % 64], u)


# ------------------------------------------------------------------------------------------------- characters + poses
HER = dict(skin=(150, 95, 65), hair="curly", hair_col=(40, 25, 20), coat=(245, 245, 240), pants=(60, 90, 150), nose="small", collar=(70, 170, 190))
HIM = dict(skin=(200, 140, 100), hair="neat", hair_col=(40, 28, 22), coat=(80, 80, 90), pants=(90, 95, 110), nose="long")
HX, HY, HS = 245, 1560, 1.45       # him (feet), design px
SX, SY, SS = 800, 1800, 1.75       # her
COIN_R = 34
COIN_OFF = (6, -50)                # coin centre relative to her left hand (held up between the fingers)
HER_HEIGHT_PX = 456 * SS           # feet to the top of the curls
PPM = HER_HEIGHT_PX / 1.6          # px per metre (she is ~1.6 m)
G_PX = 9.81 * PPM


def her_left_hand(t):
    """Her coin hand (shoulder-relative, local units). Low at the hip -> raised beside her chest (well clear of her face)."""
    low, up = (-25, 135), (-114, -100)
    u = ramp(t, T_SNAP + 0.1, 0.55)
    x, y = lerp2(low, up, u)
    tl = fr_t(F_LAUNCH)
    y += 26 * math.exp(-((t - (tl - 0.12)) / 0.06) ** 2)          # dip ...
    y -= 18 * math.exp(-((t - tl) / 0.04) ** 2)                    # ... flick
    tc = fr_t(F_CATCH)
    if t >= tc:                                                    # catch: the hand gives a little, then settles
        k = t - tc
        y += 14 * math.exp(-9 * k) * math.sin(min(math.pi, k * 14))
        x -= 6 * smooth(k / 0.25)
    else:
        x -= 6 * smooth((t - tl) / max(1e-3, tc - tl)) if t > tl else 0
    return (x, y)


def her_pose(t):
    smirk = lerp(0.85, 1.0, ramp(t, 0.3, 1.2)) + 0.28 * snap(t, T_FAKE - 0.03, 7, 1.2)
    tilt = 7 - 3 * ramp(t, T_SNAP, 0.4) + 6 * ramp(t, T_FAKE - 0.05, 0.3) + 1.5 * T.spring(t, T_FAKE + 0.25, 1.6, 3.5)
    hl = her_left_hand(t)
    return dict(eyes="squint", brows="smug", mouth="grin", mouth_amt=smirk, look=(-0.6, 0),
                hands=[hl, (36, 112)], bends=(1, -1), lean=2 + 0.6 * math.sin(t * 1.3), tilt=tilt,
                brow_lift=(0, 15 * snap(t, T_FAKE, 6, 1.6)))


def his_pose(t):
    u = snap(t, T_SNAP, 6, 1.6)                  # the snap (overshoots a touch, then settles)
    uh = snap(t, T_SNAP + 0.05, 7, 1.5)          # hands fly to his cheeks a beat later
    lean = lerp(5 + 0.8 * math.sin(t * 1.1), -3, u)          # leaning toward the gold -> recoils
    tilt = lerp(6, -8, u) + 1.2 * T.spring(t, T_SNAP + 0.2, 2.2, 4.0)
    look = lerp2((0.75, 0.55), (0.85, 0.05), u)
    eyes = min(1.25, max(0.0, u))
    jaw = lerp(0.35, 1.0, u) + 0.55 * snap(t, T_FAKE, 6, 1.5)
    hands = [lerp2((-18, 140), (5, -55), uh), lerp2((18, 140), (-5, -55), uh)]
    bends = (lerp(1, -1, min(1, max(0, uh))), lerp(-1, 1, min(1, max(0, uh))))
    blift = lerp(-8, 5, u) + 4 * snap(t, T_FAKE, 6, 1.4)
    return dict(eyes=eyes, brows="up", brow_lift=(blift, blift), mouth="O", mouth_amt=jaw, look=look, hands=hands, bends=bends,
                lean=lean, tilt=tilt)


BLINKS_HIM = (1.25, 4.6, 8.3)
BLINKS_HER = (2.05, 6.4)


def blinking(t, times):
    return any(0 <= t - b < 3 / FPS for b in times)


# ------------------------------------------------------------------------------------------------- coin flip physics
def hand_coin_screen(t):
    pose = her_pose(t)
    hx, hy = T.hand_pos(SX, SY, SS, pose, -1)
    return hx + COIN_OFF[0], hy + COIN_OFF[1]


P0 = np.array(hand_coin_screen(fr_t(F_LAUNCH)))
P1 = np.array(hand_coin_screen(fr_t(F_CATCH)))
TF = N_FLIGHT / FPS
V0 = np.array([(P1[0] - P0[0]) / TF, (P1[1] - P0[1] - 0.5 * G_PX * TF * TF) / TF])    # solved launch velocity (y down)
OMEGA = 7 * math.pi / TF                                                               # 3.5 turns: face-on at launch and catch


def coin_flight(t):
    k = t - fr_t(F_LAUNCH)
    pos = P0 + V0 * k + np.array([0.0, 0.5 * G_PX * k * k])
    return pos, OMEGA * k


def physics_report():
    end, _ = coin_flight(fr_t(F_CATCH))
    err = float(np.hypot(*(end - P1)))
    apex_px = V0[1] ** 2 / (2 * G_PX)
    side = max(coin_flight(fr_t(F_LAUNCH) + i / 300 * TF)[0][0] for i in range(301))
    face_left = SX - (88 * 1.03 + 33) * SS
    return dict(catch_error_px=round(err, 4), apex_m=round(apex_px / PPM, 3), apex_px=round(apex_px, 1), ppm=round(PPM, 1),
                flight_s=TF, launch_frame=F_LAUNCH, catch_frame=F_CATCH, coin_max_x=round(side + COIN_R, 1), hair_left_x=round(face_left, 1))


# ------------------------------------------------------------------------------------------------- helpers
def surf():
    s = skia.Surface(WW, WH)
    c = s.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    c.scale(K, K)
    return s, c


def arr(s):
    return s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32) / 255.0   # premultiplied


def over(dst, src):
    """Exactly the hero frame's blend (style2d_ultimate.over): skia hands us premultiplied colour and the hero multiplies
    by alpha again. That softens every glow; a 'correct' premultiplied over made the lantern and gold pools blow out."""
    a = src[..., 3:4]
    dst[..., :3] = src[..., :3] * a + dst[..., :3] * (1 - a)
    dst[..., 3:4] = a + dst[..., 3:4] * (1 - a)
    return dst


def gblur(x, r):
    im = Image.fromarray(np.clip(x * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255.0


def path(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


# ------------------------------------------------------------------------------------------------- static layers (once)
CX, CY = 540, 1430                     # chest
LX, LY = 905, 1215                     # lantern
GLITTER = []
SPARKS = []


def build_static():
    rr = random.Random(11)
    L = {}
    # --- sky back: gradient, god rays, sun
    s, c = surf()
    c.drawRect(skia.Rect(0, 0, W, HOR + 10), P(Shader=T.lin((0, 0), (0, HOR), [C(28, 22, 70), C(92, 45, 110), C(196, 82, 112), C(250, 140, 96),
                                                                            C(255, 196, 130)], [0, 0.3, 0.58, 0.82, 1])))
    for k in range(14):
        a0 = math.radians(-170 + k * 13 + rr.uniform(-3, 3))
        a1 = a0 + math.radians(rr.uniform(3, 6))
        Lr = 1600
        c.drawPath(path([SUN, (SUN[0] + Lr * math.cos(a0), SUN[1] + Lr * math.sin(a0)), (SUN[0] + Lr * math.cos(a1), SUN[1] + Lr * math.sin(a1))]),
                   P(C(255, 220, 160, 26), MaskFilter=BLUR(10)))
    c.drawCircle(*SUN, 420, P(Shader=T.rad(*SUN, 420, [C(255, 220, 150, 120), C(255, 170, 110, 0)])))
    c.drawCircle(*SUN, 150, P(Shader=T.rad(*SUN, 150, [C(255, 245, 210, 255), C(255, 225, 150, 0)])))
    c.drawCircle(*SUN, 92, P(C(255, 244, 205)))
    L["skyb"] = arr(s)
    # --- clouds (own layer: they drift)
    s, c = surf()
    for band, (y0, n, sc, col_top, col_bot) in enumerate(((210, 5, 1.3, (120, 70, 140), (255, 160, 150)), (420, 6, 1.0, (150, 80, 130), (255, 180, 140)),
                                                          (640, 6, 0.75, (190, 100, 120), (255, 205, 150)))):
        for k in range(n):
            x = rr.uniform(-150, W)
            y = y0 + rr.uniform(-40, 40)
            w = rr.uniform(260, 460) * sc
            cl = skia.Path()
            for j in range(7):
                bx = x + j * w / 8
                br = rr.uniform(0.18, 0.32) * w
                cl.addOval(skia.Rect(bx - br * 0.6, y - br * rr.uniform(0.5, 0.9), bx + br * 0.6, y + br * 0.25))
            c.drawPath(cl, P(Shader=T.lin((0, y - 0.3 * w), (0, y + 0.1 * w), [C(*col_top, 150), C(*col_bot, 230)]), MaskFilter=BLUR(2)))
            cl = skia.Op(cl, skia.Path(), skia.PathOp.kUnion_PathOp) or cl
            c.drawPath(cl, S(C(255, 225, 190, 70), 2.5))
    L["clouds"] = arr(s)
    for k in range(6):
        rr.uniform(-15, 15), rr.uniform(-30, 30), rr.uniform(8, 13)   # (keep the hero's random sequence: birds are drawn per frame)
    # --- sky front: cliffs, lighthouse, sea, waves, ship + reflection
    s, c = surf()
    for layer, (yb, amp, col) in enumerate(((870, 50, (150, 90, 130)), (900, 70, (110, 60, 105)))):
        pts = [(0, HOR)] + [(x, yb - amp * (0.6 + 0.4 * math.sin(x / (120 + 40 * layer) + layer)) - (40 if x < 380 else 0) * (1 - x / 380))
                            for x in range(0, W + 1, 20)] + [(W, HOR)]
        c.drawPath(path(pts), P(C(*col)))
    c.drawPath(path([(0, HOR), (0, 700), (90, 690), (200, 730), (330, 780), (430, 860), (470, HOR)]), P(C(80, 42, 80)))
    c.drawRect(skia.Rect(118, 640, 132, 692), P(C(240, 230, 220)))
    c.drawRect(skia.Rect(115, 632, 135, 642), P(C(60, 30, 50)))
    c.drawCircle(125, 628, 6, P(C(255, 240, 180)))
    c.drawPath(path([(125, 628), (0, 600), (0, 650)]), P(C(255, 235, 170, 60), MaskFilter=BLUR(4)))
    c.drawRect(skia.Rect(0, HOR, W, H), P(Shader=T.lin((0, HOR), (0, 1350), [C(150, 80, 120), C(70, 50, 105), C(30, 40, 90)], [0, 0.4, 1])))
    for k in range(70):   # the sun-glitter path is drawn per frame (it shimmers); keep its random draws in order
        y = HOR + 6 + k * 5.5
        w = max(8, (75 - k) * 2.6 + rr.uniform(-20, 40))
        xc = SUN[0] + rr.uniform(-25, 25) * (1 + k / 40)
        GLITTER.append((xc, y, w, max(30, 200 - k * 2)))
    for k in range(55):
        y = HOR + 20 + (k / 55) ** 1.6 * 420
        x = rr.uniform(-50, W)
        w = 20 + (y - HOR) * 0.25
        c.drawLine(x, y, x + w, y, S(C(190, 120, 160, 70), 2 + (y - HOR) / 160))
    sea = arr(s)
    s, sc_ = surf()
    sx, sy = 255, 925
    hull = path([(sx - 170, sy - 45), (sx + 175, sy - 50), (sx + 150, sy + 8), (sx - 140, sy + 10)])
    sc_.drawPath(hull, P(C(45, 25, 40)))
    for k in range(4):
        sc_.drawLine(sx - 160 + k * 4, sy - 34 + k * 10, sx + 165 - k * 6, sy - 38 + k * 10, S(C(80, 45, 55), 2))
    for k in range(6):
        sc_.drawCircle(sx - 110 + k * 45, sy - 25, 5, P(C(255, 200, 120)))
    sc_.drawPath(path([(sx - 175, sy - 50), (sx - 210, sy - 75), (sx - 160, sy - 60)]), P(C(45, 25, 40)))
    masts = [(sx - 70, 210), (sx + 40, 250), (sx + 135, 170)]
    for mx, mh in masts:
        sc_.drawLine(mx, sy - 45, mx, sy - 45 - mh, S(C(50, 28, 40), 7))
        for j, (sw, sh) in enumerate(((95, 70), (80, 55), (60, 40))):
            yt = sy - 45 - mh + 20 + j * (sh + 10)
            sail = skia.Path()
            sail.moveTo(mx - sw / 2, yt)
            sail.lineTo(mx + sw / 2, yt)
            sail.quadTo(mx + sw / 2 + 12, yt + sh / 2, mx + sw / 2 - 4, yt + sh)
            sail.lineTo(mx - sw / 2 + 4, yt + sh)
            sail.quadTo(mx - sw / 2 + 14, yt + sh / 2, mx - sw / 2, yt)
            sc_.drawPath(sail, P(Shader=T.lin((mx - sw / 2, 0), (mx + sw / 2, 0), [C(190, 140, 140), C(255, 215, 175)])))
            sc_.drawPath(sail, S(C(60, 30, 45), 2))
        sc_.drawPath(path([(mx, sy - 45 - mh), (mx + 30, sy - 45 - mh + 8), (mx, sy - 45 - mh + 16)]), P(C(200, 40, 50)))
    for a_, b_ in ((masts[0], masts[1]), (masts[1], masts[2])):
        sc_.drawLine(a_[0], sy - 45 - a_[1], b_[0], sy - 45 - b_[1], S(C(50, 28, 40, 200), 1.5))
    for mx, mh in masts:
        sc_.drawLine(mx, sy - 45 - mh, sx - 205, sy - 72, S(C(50, 28, 40, 150), 1.2))
        sc_.drawLine(mx, sy - 45 - mh, sx + 170, sy - 48, S(C(50, 28, 40, 150), 1.2))
    ship = arr(s)
    refl = ship[::-1].copy()
    refl = np.roll(refl, WH - 2 * int((sy + 10) * K), axis=0)
    refl *= 0.35
    refl = gblur(refl, 2.5 * K)
    for yy in range(0, WH, int(6 * K)):
        refl[yy:yy + int(2 * K)] *= 0.3
    refl *= (np.arange(WH)[:, None, None] > (sy + 8) * K)
    over(sea, refl)
    over(sea, ship)
    L["skyf"] = sea
    # --- deck: planks, posts, coiled rope (the hanging rope between the posts is drawn per frame: it sways)
    s, c = surf()
    VT, VL, VR = 1180, 300, 760
    BL, BR = -260, W + 260
    N = 14
    c.drawPath(path([(VL, VT), (VR, VT), (BR, H), (BL, H)]), P(C(30, 16, 10)))
    for i in range(N):
        u0, u1 = i / N, (i + 1) / N
        gap = 0.012
        p0 = (VL + (VR - VL) * (u0 + gap), VT)
        p1 = (VL + (VR - VL) * (u1 - gap), VT)
        p2 = (BL + (BR - BL) * (u1 - gap * 0.3), H)
        p3 = (BL + (BR - BL) * (u0 + gap * 0.3), H)
        tone = rr.uniform(0.85, 1.12)
        c.drawPath(path([p0, p1, p2, p3]), P(Shader=T.lin((0, VT), (0, H), [C(150 * tone, 100 * tone, 62 * tone), C(98 * tone, 60 * tone, 36 * tone)])))
        for g in range(5):
            f = rr.uniform(0.15, 0.85)
            a_ = (p0[0] + (p1[0] - p0[0]) * f, VT)
            b_ = (p3[0] + (p2[0] - p3[0]) * f, H)
            gp = skia.Path()
            gp.moveTo(*a_)
            gp.quadTo((a_[0] + b_[0]) / 2 + rr.uniform(-8, 8), (VT + H) / 2, *b_)
            c.drawPath(gp, S(C(70, 40, 24, 70), rr.uniform(1, 2.5)))
        for seam in range(2):
            t_ = rr.uniform(0.15, 0.9) ** 1.5
            y = VT + (H - VT) * t_
            xa = p3[0] + (p0[0] - p3[0]) * (1 - t_)
            xb = p2[0] + (p1[0] - p2[0]) * (1 - t_)
            c.drawLine(xa, y, xb, y, S(C(40, 22, 14, 200), 2 + 3 * t_))
            for xn in (xa + (xb - xa) * 0.25, xa + (xb - xa) * 0.75):
                c.drawCircle(xn, y - 4 - 6 * t_, 1.5 + 3 * t_, P(C(40, 30, 30)))
    for x, top in ((330, 990), (740, 990)):
        c.drawRoundRect(skia.Rect(x - 20, top, x + 20, VT + 30), 6, 6, P(Shader=T.lin((x - 20, 0), (x + 20, 0), [C(60, 36, 24), C(110, 70, 44), C(55, 32, 20)])))
        c.drawRoundRect(skia.Rect(x - 24, top - 12, x + 24, top + 6), 6, 6, P(C(95, 60, 36)))
    for k in range(6):
        r0 = 95 - k * 9
        c.drawOval(skia.Rect(240 - r0, 1735 - k * 9 - r0 * 0.32, 240 + r0, 1735 - k * 9 + r0 * 0.32), S(C(110, 85, 50), 15))
        c.drawOval(skia.Rect(240 - r0, 1733 - k * 9 - r0 * 0.32, 240 + r0, 1733 - k * 9 + r0 * 0.32), S(C(215, 180, 125), 8))
    L["deck"] = arr(s)
    # --- front: lantern, chest, gold, gems, pearls, spilled coins
    s, c = surf()
    c.drawCircle(LX, LY, 300, P(Shader=T.rad(LX, LY, 300, [C(255, 190, 90, 110), C(255, 160, 60, 0)])))
    c.drawRoundRect(skia.Rect(LX - 38, LY - 60, LX + 38, LY + 55), 12, 12, P(Shader=T.rad(LX, LY, 60, [C(255, 245, 190), C(255, 190, 80)])))
    for xx in (LX - 38, LX, LX + 38):
        c.drawLine(xx, LY - 60, xx, LY + 55, S(C(45, 30, 25), 5))
    c.drawRoundRect(skia.Rect(LX - 46, LY - 78, LX + 46, LY - 58), 6, 6, P(C(45, 30, 25)))
    c.drawRoundRect(skia.Rect(LX - 46, LY + 52, LX + 46, LY + 66), 6, 6, P(C(45, 30, 25)))
    c.drawArc(skia.Rect(LX - 22, LY - 110, LX + 22, LY - 66), 180, 180, False, S(C(45, 30, 25), 5))
    cx, cy = CX, CY
    cb = skia.Rect(cx - 235, cy - 115, cx + 235, cy + 115)
    c.drawOval(skia.Rect(cx - 300, cy + 80, cx + 300, cy + 160), P(C(20, 10, 10, 120), MaskFilter=BLUR(18)))
    lid = skia.Path()
    lid.moveTo(cx - 245, cy - 112)
    lid.lineTo(cx - 205, cy - 340)
    lid.quadTo(cx, cy - 415, cx + 205, cy - 340)
    lid.lineTo(cx + 245, cy - 112)
    lid.close()
    c.drawPath(lid, P(Shader=T.lin((0, cy - 415), (0, cy - 112), [C(90, 48, 24), C(130, 72, 38)])))
    c.drawPath(path([(cx - 225, cy - 125), (cx - 195, cy - 320), (cx + 195, cy - 320), (cx + 225, cy - 125)]), P(C(60, 30, 18)))
    for xb in (cx - 150, cx + 150):
        c.drawPath(path([(xb - 16, cy - 112), (xb - 14 + (xb - cx) * 0.12, cy - 360), (xb + 14 + (xb - cx) * 0.12, cy - 360), (xb + 16, cy - 112)]),
                   P(C(85, 80, 80)))
    c.drawPath(lid, S(T.OUT, 8))
    heap = skia.Path()
    heap.moveTo(cx - 228, cy - 108)
    heap.quadTo(cx - 60, cy - 300, cx + 40, cy - 250)
    heap.quadTo(cx + 150, cy - 210, cx + 228, cy - 108)
    heap.close()
    c.drawPath(heap, P(Shader=T.lin((0, cy - 290), (0, cy - 105), [C(255, 236, 140), C(225, 150, 40)])))
    for k in range(70):
        u = rr.uniform(-0.95, 0.95)
        top = cy - 108 - (1 - u * u) * 165
        T.coin(c, cx + u * 215, rr.uniform(top + 8, cy - 105), rr.uniform(13, 22))
    for k, col in enumerate(((220, 30, 60), (40, 190, 110), (60, 120, 230), (220, 30, 60), (170, 60, 220))):
        gx, gy = cx + rr.uniform(-170, 170), cy - 130 - rr.uniform(0, 110)
        gem = path([(gx, gy - 16), (gx + 14, gy - 4), (gx + 9, gy + 13), (gx - 9, gy + 13), (gx - 14, gy - 4)])
        c.drawPath(gem, P(Shader=T.lin((gx - 14, gy - 16), (gx + 14, gy + 13), [C(*[min(255, v + 90) for v in col]), C(*col), C(*[v // 2 for v in col])])))
        c.drawPath(gem, S(C(30, 15, 20), 2.5))
        c.drawCircle(gx - 4, gy - 6, 3, P(C(255, 255, 255, 220)))
    pearl = skia.Path()
    pearl.moveTo(cx + 120, cy - 130)
    pearl.cubicTo(cx + 210, cy - 40, cx + 230, cy + 60, cx + 290, cy + 130)
    meas = skia.PathMeasure(pearl, False)
    Lp = meas.getLength()
    for k in range(26):
        pos, _ = meas.getPosTan(Lp * k / 25)
        c.drawCircle(pos.x(), pos.y(), 8, P(Shader=T.rad(pos.x() - 3, pos.y() - 3, 9, [C(255, 255, 250), C(215, 205, 200)])))
    c.drawRoundRect(cb, 16, 16, P(Shader=T.lin((0, cy - 115), (0, cy + 115), [C(160, 92, 48), C(100, 55, 28)])))
    for k in range(1, 4):
        c.drawLine(cx - 235, cy - 115 + k * 57, cx + 235, cy - 115 + k * 57, S(C(70, 36, 18, 180), 3))
    for xb in (cx - 150, cx + 150):
        c.drawRect(skia.Rect(xb - 20, cy - 115, xb + 20, cy + 115), P(Shader=T.lin((xb - 20, 0), (xb + 20, 0), [C(70, 66, 66), C(140, 135, 130), C(60, 56, 56)])))
        for k in range(5):
            c.drawCircle(xb, cy - 95 + k * 47, 5, P(C(200, 195, 185)))
    c.drawRect(skia.Rect(cx - 235, cy - 125, cx + 235, cy - 100), P(Shader=T.lin((0, cy - 125), (0, cy - 100), [C(150, 145, 140), C(70, 66, 66)])))
    c.drawRoundRect(skia.Rect(cx - 34, cy - 100, cx + 34, cy - 30), 10, 10, P(Shader=T.lin((cx - 34, 0), (cx + 34, 0), [C(200, 150, 60), C(255, 215, 110), C(170, 120, 40)])))
    c.drawCircle(cx, cy - 72, 8, P(C(40, 25, 15)))
    c.drawRect(skia.Rect(cx - 3, cy - 72, cx + 3, cy - 52), P(C(40, 25, 15)))
    c.drawRoundRect(cb, 16, 16, S(T.OUT, 8))
    for k in range(12):   # spilled coins lie flat ON the planks (resting, no hover)
        T.coin(c, cx + rr.uniform(-360, 340), cy + 160 + rr.uniform(0, 260), rr.uniform(16, 26), flat=True)
    L["front"] = arr(s)
    return L


def sparkle_sites():
    r = random.Random(5)
    out = []
    for k in range(14):        # on the heap, left part (her arm/body is drawn over the right part anyway)
        u = r.uniform(-0.9, 0.35)
        top = CY - 108 - (1 - u * u) * 165
        out.append((CX + u * 215, r.uniform(top + 10, CY - 112), r.uniform(9, 20), r.uniform(0, 10), r.uniform(0.9, 1.6)))
    return out


# ------------------------------------------------------------------------------------------------- camera
CAM_KEYS = [(0.0, 1.0, 540, 960), (T_SNAP, 1.04, 540, 985), (fr_t(F_LAUNCH), 1.06, 538, 1010), (T_FAKE, 1.075, 535, 1022), (DUR, 1.08, 530, 1030)]   # end framing keeps his whole head + hands in shot


def catmull(keys, t):
    ts = [k[0] for k in keys]
    i = max(0, min(len(keys) - 2, int(np.searchsorted(ts, t, side="right")) - 1))
    p0, p1, p2, p3 = keys[max(0, i - 1)], keys[i], keys[i + 1], keys[min(len(keys) - 1, i + 2)]
    u = 0 if p2[0] == p1[0] else (t - p1[0]) / (p2[0] - p1[0])
    u = max(0.0, min(1.0, u))
    out = []
    for j in range(1, 4):
        a, b, c_, d = p0[j], p1[j], p2[j], p3[j]
        out.append(0.5 * ((2 * b) + (-a + c_) * u + (2 * a - 5 * b + 4 * c_ - d) * u * u + (-a + 3 * b - 3 * c_ + d) * u ** 3))
    return out


def camera_track():
    raw = np.array([catmull(CAM_KEYS, fr_t(f)) for f in range(NF + 30)])
    pad = np.vstack([np.repeat(raw[:1], 15, 0), raw])
    ker = np.hanning(31)
    ker /= ker.sum()
    sm = np.stack([np.convolve(pad[:, j], ker, mode="valid")[:NF] for j in range(3)], 1)
    return sm


CAM = camera_track()


def shake(t):
    k = t - T_FAKE
    if 0 <= k < 3 / FPS:          # 3-frame micro-shake on "fake"
        f = min(2, int(k * FPS + 1e-6))
        return ((4, -3), (-3, 2), (1, -1))[f]
    return (0, 0)


# ------------------------------------------------------------------------------------------------- per-frame drawing
def draw_sky_dyn(t):
    s, c = surf()
    for i, (xc, y, w, a) in enumerate(GLITTER):           # glitter shimmers (each stroke breathes on its own smooth noise)
        m = 0.55 + 0.45 * noise1(t, 100 + i, 2.2)
        dx = 4 * noise1(t, 300 + i, 0.8)
        c.drawRoundRect(skia.Rect(xc - w / 2 + dx, y, xc + w / 2 + dx, y + 2.6), 1.3, 1.3, P(C(255, 220, 160, a * m)))
    r = random.Random(3)
    for k in range(6):                                     # gulls: slow drift, wings flap
        bx = 520 + k * 48 + r.uniform(-15, 15) + t * (6 + k)
        by = 650 + r.uniform(-30, 30) + 3 * math.sin(t * 0.9 + k)
        sz = r.uniform(8, 13)
        fl = 0.6 * math.sin(t * (7 + k * 0.6) + k * 1.7)
        b = skia.Path()
        b.moveTo(bx - sz, by + sz * fl * 0.5)
        b.quadTo(bx - sz / 2, by - sz * (0.6 - fl * 0.4), bx, by)
        b.quadTo(bx + sz / 2, by - sz * (0.6 - fl * 0.4), bx + sz, by + sz * fl * 0.5)
        c.drawPath(b, S(C(50, 25, 50, 200), 3))
    return arr(s)


ROPE = None


def rope_sim():
    """Hanging rope between the posts: a damped spring driven by a gusty breeze (no raw sine)."""
    dt = 1 / (FPS * 4)
    x = v = 0.0
    out = []
    for i in range(NF * 4):
        t = i * dt
        wind = 220 * noise1(t, 77, 0.5) + 90 * noise1(t, 78, 1.7)
        a = -38 * x - 2.4 * v + wind * 0.1
        v += a * dt
        x += v * dt
        if i % 4 == 0:
            out.append(x)
    return out


def draw_rope(t, f):
    s, c = surf()
    sway = ROPE[f]
    rope = skia.Path()
    rope.moveTo(330, 1015)
    rope.quadTo(535 + sway * 3, 1080 + sway * 1.2, 740, 1015)
    c.drawPath(rope, S(C(120, 95, 60), 9))
    c.drawPath(rope, S(C(210, 180, 130), 5))
    return arr(s)


def draw_sparkles(t):
    s, c = surf()
    for (x, y, r, ph, sp) in SPARKS:          # twinkle in and out, never on her face (drawn under the characters)
        u = (t * sp + ph) % 2.2
        a = math.sin(math.pi * u / 0.7) if u < 0.7 else 0.0
        if a > 0.02:
            T.sparkle(c, x, y, r * (0.6 + 0.4 * a), int(235 * a))
    k = t - T_GOLD                           # a brighter ripple of sparkles across the heap on "gold"
    if 0 < k < 0.8:
        for i in range(5):
            u = (k - i * 0.1) / 0.35
            if 0 < u < 1:
                T.sparkle(c, CX - 180 + i * 60, CY - 150 - 40 * math.sin(i * 1.3), 18, int(255 * math.sin(math.pi * u)))
    return arr(s)


def draw_char(look, x, y, s_, pose, t, coin=None):
    s, c = surf()
    T.person(c, x, y, s_, look, pose, t)
    if coin is not None:
        hero_coin(c, coin[0], coin[1], coin[2])
        if coin[3] > 0:   # landing glint: a small hot spot on the face (a big sparkle bloomed into a white blob)
            c.drawOval(skia.Rect(coin[0] - 14, coin[1] - 22, coin[0] + 4, coin[1] - 6), P(C(255, 255, 240, int(230 * coin[3])), MaskFilter=BLUR(2)))
    return arr(s)


def hero_coin(c, x, y, face):
    """Her coin: a dark ink rim so it reads against the gold heap behind it."""
    w = max(4, COIN_R * abs(face))
    c.drawOval(skia.Rect(x - w - 3, y - COIN_R - 3, x + w + 3, y + COIN_R + 3), P(C(45, 22, 20)))
    T.coin(c, x, y, COIN_R, face)
    c.drawOval(skia.Rect(x - w * 0.62, y - COIN_R * 0.62, x + w * 0.62, y + COIN_R * 0.62), S(C(170, 110, 20, 200), 3))


def light_char(ch, img, yfeet, gd):
    A = ch[..., 3]
    sil = Image.fromarray((A * 255).astype(np.uint8))
    h0 = int(yfeet * K)
    top = sil.crop((0, 0, WW, h0)).transpose(Image.FLIP_TOP_BOTTOM).resize((WW, int(h0 * 0.28)))
    sh = Image.new("L", (WW, WH), 0)
    sh.paste(top, (int(-18 * K), h0 - int(6 * K)))
    sh = np.asarray(sh.filter(ImageFilter.GaussianBlur(9 * K))).astype(np.float32) / 255
    img[..., :3] *= (1 - 0.55 * sh[..., None] * np.array([1.0, 1.05, 0.9], np.float32))
    dx, dy = int(14 * K), int(10 * K)
    shade = np.clip(A - np.roll(np.roll(A, -dy, 0), dx, 1), 0, 1)
    shade = gblur(np.dstack([shade] * 4), 1.2 * K)[..., 0]
    ch[..., :3] *= (1 - 0.32 * shade[..., None] * np.array([1.0, 0.95, 0.75], np.float32))
    rim = np.clip(A - np.roll(np.roll(A, int(7 * K), 0), -int(9 * K), 1), 0, 1)
    ch[..., :3] = np.clip(ch[..., :3] + 0.55 * rim[..., None] * np.array([1.0, 0.75, 0.45], np.float32), 0, 1)
    ch[..., :3] = np.clip(ch[..., :3] + gd[..., None] * 0.25 * np.array([1.0, 0.75, 0.3], np.float32) * A[..., None], 0, 1)
    return over(img, ch)


def coin_state(t, f):
    """(x, y, face width factor, highlight) of her coin, or None when it is drawn in flight."""
    if F_LAUNCH < f < F_CATCH:
        return None
    x, y = hand_coin_screen(t)
    hl = 0.0
    if f >= F_CATCH:
        hl = max(0.0, 1 - (t - fr_t(F_CATCH)) / 0.35)      # glint as it lands face-on
    return (x, y, 1.0, hl)


def draw_flight(t, f):
    s, c = surf()
    if not (F_LAUNCH < f < F_CATCH):
        return None
    # motion blur: 5 sub-samples across a 180-degree shutter
    for j, w_ in enumerate((0.15, 0.2, 0.25, 0.3, 1.0)):
        tt = t - (4 - j) * (0.5 / FPS) / 4
        (x, y), th = coin_flight(tt)
        cw = math.cos(th)
        a = int(255 * w_) if j == 4 else int(110 * w_)
        lay = c.saveLayerAlpha(None, a) if j < 4 else None
        if abs(cw) < 0.16:      # edge-on: a ridged gold edge
            c.drawRoundRect(skia.Rect(x - 5, y - COIN_R, x + 5, y + COIN_R), 4, 4, P(Shader=T.lin((x - 5, 0), (x + 5, 0), [C(150, 95, 20), C(255, 215, 110), C(150, 95, 20)])))
            c.drawRoundRect(skia.Rect(x - 5, y - COIN_R, x + 5, y + COIN_R), 4, 4, S(C(45, 22, 20), 3.5))
        else:
            hero_coin(c, x, y, abs(cw))
            if cw < 0:          # the back face is a touch darker
                c.drawOval(skia.Rect(x - COIN_R * abs(cw), y - COIN_R, x + COIN_R * abs(cw), y + COIN_R), P(C(90, 50, 0, 50)))
        if lay is not None:
            c.restore()
    (x, y), th = coin_flight(t)
    if abs(math.cos(th)) > 0.93:   # face-on: catches the sun
        T.sparkle(c, x + 8, y - 12, 11, 190)
    return arr(s)


def draw_burst(t):
    if not (0 <= t - T_FAKE < 0.75):
        return None
    s, c = surf()
    x, y = hand_coin_screen(t)
    p = (t - T_FAKE) / 0.75
    # a ring of crisp stars starting 55 px out. T.burst starts every sparkle on one point and each has a glow halo:
    # stacked, they bloomed into a white blob on the coin.
    for i in range(8):
        a = i / 8 * 2 * math.pi + 0.3
        r = 55 + 160 * T.ease(min(1, p * 1.4)) * (0.8 + 0.2 * math.sin(i * 2.3))
        sx_, sy_, rs = x + math.cos(a) * r, y + math.sin(a) * r, 9 * (1 - p) + 3
        star = path([(sx_, sy_ - rs * 2), (sx_ + rs * 0.4, sy_ - rs * 0.4), (sx_ + rs * 2, sy_), (sx_ + rs * 0.4, sy_ + rs * 0.4),
                     (sx_, sy_ + rs * 2), (sx_ - rs * 0.4, sy_ + rs * 0.4), (sx_ - rs * 2, sy_), (sx_ - rs * 0.4, sy_ - rs * 0.4)])
        c.drawPath(star, P(C(255, 236, 160, 230 * (1 - p) ** 1.3)))
    return arr(s)


def draw_title(t):
    s = skia.Surface(W, H)
    c = s.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    lines = (("EVERY COIN...", 96, 300, [C(255, 255, 255), C(235, 225, 255)], T_COIN), ("IS FAKE", 170, 470, [C(255, 236, 140), C(255, 170, 40)], T_FAKE))
    for txt, size, y, grad, at in lines:
        k = t - at
        if k < 0:
            continue
        u = T.out_back(k / (6 / FPS), 2.2)              # slam: 1.7x -> 1.0 with a little bounce, ~6 frames
        sc = 1.7 - 0.7 * u
        a = min(1.0, k / (3 / FPS))
        f = skia.Font(T.FB, size)
        w = f.measureText(txt)
        assert w <= 960, (txt, w)
        x0 = (W - w) / 2
        c.save()
        c.translate(W / 2, y - size * 0.35)
        c.scale(sc, sc)
        c.translate(-W / 2, -(y - size * 0.35))
        lay = c.saveLayerAlpha(None, int(255 * a))
        c.drawString(txt, x0 + 6, y + 8, f, P(C(10, 0, 20, 160), MaskFilter=BLUR(6)))
        c.drawString(txt, x0, y, f, S(C(25, 10, 30), size * 0.17))
        c.drawString(txt, x0, y, f, P(Shader=T.lin((0, y - size), (0, y), grad)))
        c.restore()
        c.restore()
    return s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32) / 255.0


# ------------------------------------------------------------------------------------------------- frame
G = {}


def init_worker():
    global ROPE, SPARKS
    for k in ("skyb", "clouds", "skyf", "deck", "front"):
        G[k] = np.load(os.path.join(WORK, f"L_{k}.npy"), mmap_mode="r")
    GLITTER.extend(json.load(open(os.path.join(WORK, "glitter.json"))))
    ROPE = json.load(open(os.path.join(WORK, "rope.json")))
    SPARKS = sparkle_sites()
    yy, xx = np.mgrid[0:WH, 0:WW].astype(np.float32) / K
    G["gd"] = np.exp(-(((xx - CX) / 330.0) ** 2 + ((yy - (CY - 170)) / 230.0) ** 2)).astype(np.float32)
    G["ld"] = np.exp(-(((xx - LX) / 260.0) ** 2 + ((yy - LY) / 260.0) ** 2)).astype(np.float32)
    oy, ox = np.mgrid[0:H, 0:W].astype(np.float32)
    G["vig"] = (1 - 0.42 * np.clip((((ox - W / 2) / (W * 0.75)) ** 2 + ((oy - H * 0.56) / (H * 0.62)) ** 2), 0, 1))[..., None]


def render(f, out=None):
    t = fr_t(f)
    img = np.array(G["skyb"])
    cl = G["clouds"]
    dx = 0.6 * t * K                                         # clouds drift ~6 px over the clip (sub-pixel resample)
    rows = int(820 * K)
    sh = Image.fromarray(np.clip(np.asarray(cl[:rows]) * 255, 0, 255).astype(np.uint8)).transform(
        (WW, rows), Image.AFFINE, (1, 0, -dx, 0, 1, 0), resample=Image.BILINEAR)
    over(img[:rows], np.asarray(sh).astype(np.float32) / 255.0)
    over(img, np.asarray(G["skyf"]))
    over(img, draw_sky_dyn(t))
    over(img, np.asarray(G["deck"]))
    over(img, draw_rope(t, f))
    over(img, np.asarray(G["front"]))
    over(img, draw_sparkles(t))
    hp, sp = his_pose(t), her_pose(t)
    hp["blink"] = blinking(t, BLINKS_HIM)
    if blinking(t, BLINKS_HER):
        sp = dict(sp, eyes="closed")
    img = light_char(draw_char(HIM, HX, HY, HS, hp, t), img, HY, G["gd"])
    img = light_char(draw_char(HER, SX, SY, SS, sp, t, coin_state(t, f)), img, SY, G["gd"])
    flick = 1 + 0.10 * noise1(t, 9, 6) + 0.05 * noise1(t, 10, 13)       # lantern flicker
    img[..., :3] += G["gd"][..., None] * 0.22 * np.array([1.0, 0.72, 0.28], np.float32)
    img[..., :3] += G["ld"][..., None] * 0.12 * flick * np.array([1.0, 0.7, 0.35], np.float32)
    for lay in (draw_flight(t, f), draw_burst(t)):
        if lay is not None:
            over(img, lay)
    # camera: crop (zoom >= 1 on a 1.25x render = never an upscale) + micro-shake
    z, ccx, ccy = CAM[f]
    sx_, sy_ = shake(t)
    vw, vh = W / z, H / z
    x0 = min(max(0, ccx - vw / 2 + sx_), W - vw) * K
    y0 = min(max(0, ccy - vh / 2 + sy_), H - vh) * K
    src = Image.fromarray(np.clip(img[..., :3] * 255, 0, 255).astype(np.uint8))
    frame = src.transform((W, H), Image.EXTENT, (x0, y0, x0 + vw * K, y0 + vh * K), resample=Image.BICUBIC)
    rgb = np.asarray(frame).astype(np.float32) / 255.0
    ttl = draw_title(t)
    rgb = rgb * (1 - ttl[..., 3:4]) + ttl[..., :3] * ttl[..., 3:4]      # same blend as the hero title
    # finish: bloom, grade, vignette, animated grain
    bright = np.clip((rgb - 0.72) / 0.28, 0, 1) * rgb
    b4 = np.dstack([bright, np.ones((H, W, 1), np.float32)])
    rgb = rgb + 0.55 * gblur(b4, 22)[..., :3] + 0.25 * gblur(b4, 6)[..., :3]
    lum = rgb.mean(axis=2, keepdims=True)
    rgb = rgb + (1 - lum) * 0.04 * np.array([-0.4, 0.0, 0.6], np.float32) + lum * 0.05 * np.array([0.6, 0.2, -0.5], np.float32)
    rgb = rgb * G["vig"]
    rgb = rgb + np.random.default_rng(1000 + f).normal(0, 0.010, (H, W, 1)).astype(np.float32)
    Image.fromarray(np.clip(rgb * 255, 0, 255).astype(np.uint8)).save(out or os.path.join(WORK, "frames", f"{f + 1:04d}.png"))
    return f


def prepare():
    os.makedirs(os.path.join(WORK, "frames"), exist_ok=True)
    L = build_static()
    for k, v in L.items():
        np.save(os.path.join(WORK, f"L_{k}.npy"), v)
    json.dump(GLITTER, open(os.path.join(WORK, "glitter.json"), "w"))
    json.dump(rope_sim(), open(os.path.join(WORK, "rope.json"), "w"))
    rep = physics_report()
    rep.update(t_gold=T_GOLD, t_snap=T_SNAP, t_coin=T_COIN, t_fake=T_FAKE)
    json.dump(rep, open(os.path.join(WORK, "physics.json"), "w"), indent=1)
    print("PHYSICS", rep)
    assert rep["catch_error_px"] < 1.0, "coin does not land in her hand"
    assert 0.3 <= rep["apex_m"] <= 0.6, "implausible flip height"
    assert rep["coin_max_x"] < rep["hair_left_x"], "the flip would cross her face/hair"


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "frames"
    prepare()
    if mode == "stills":
        init_worker()
        for f in [int(x) for x in sys.argv[2].split(",")]:
            render(f, os.path.join(WORK, f"still_{f:04d}.png"))
            print("still", f)
    else:
        with Pool(int(os.environ.get("S2D_PROCS", "5")), initializer=init_worker) as pool:
            todo = [f for f in range(NF) if os.environ.get("S2D_SKIP") != "1" or not os.path.exists(os.path.join(WORK, "frames", f"{f + 1:04d}.png"))]
            for i, f in enumerate(pool.imap_unordered(render, todo)):
                if i % 30 == 0:
                    print("frame", i, "/", NF, flush=True)
        print("done", NF, "frames ->", os.path.join(WORK, "frames"))
