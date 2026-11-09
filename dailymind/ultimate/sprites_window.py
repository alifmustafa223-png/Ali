"""Animated toon-character sprite sequences for the real-3D (Blender) airplane-windows video.

Each sprite = PNG sequence (transparent, 500x750, feet at bottom centre, 30 fps over the scene) rendered with the
classic toon person(), with expressions/arms changing on the spoken-word cues from ../window/plan.json.
Blender maps each sequence onto a camera-facing plane (flat character in a real 3D world).
Usage (in dailymind/ultimate): python sprites_window.py [out_dir]
"""
import json
import math
import os
import sys

import skia

sys.path.insert(0, "..")
from toon import person  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "../window3d/sprites"
PLAN = json.load(open("../window/plan.json"))
D, CUE = PLAN["durs"], PLAN["cues"]
FPS = 30
SW, SH = 500, 750

PAX = [dict(skin=(235, 195, 160), hair="neat", hair_col=(60, 40, 25), coat=(240, 120, 60), pants=(40, 50, 80), nose="small"),
       dict(skin=(200, 150, 110), hair="curly", hair_col=(30, 20, 15), coat=(90, 180, 220), pants=(50, 50, 60), nose="small"),
       dict(skin=(240, 210, 185), hair="pigtails", hair_col=(200, 150, 70), coat=(200, 90, 160), pants=(40, 40, 60), nose="small"),
       dict(skin=(220, 175, 140), hair="neat", hair_col=(20, 15, 10), coat=(90, 190, 120), pants=(40, 40, 60), nose="small"),
       dict(skin=(235, 200, 170), hair="grey", hair_col=(185, 185, 190), coat=(150, 120, 200), pants=(50, 45, 40), glasses=True, nose="long")]
OLD = [dict(skin=(235, 200, 170), hair="neat", hair_col=(70, 50, 35), hat="bowler", coat=(70, 60, 55), pants=(50, 45, 45), nose="small"),
       dict(skin=(240, 210, 185), hair="curly", hair_col=(120, 70, 40), coat=(130, 60, 90), dress=(130, 60, 90), collar=(240, 235, 230),
            pants=(60, 50, 50), nose="small"),
       dict(skin=(225, 185, 150), hair="neat", hair_col=(30, 25, 20), hat="tophat", coat=(35, 35, 45), pants=(35, 35, 45), mustache=True,
            nose="long")]
ENG = [dict(skin=(235, 200, 170), hair="neat", hair_col=(80, 60, 40), coat=(245, 245, 240), pants=(60, 60, 70), glasses=True, mustache=True,
            nose="long"),
       dict(skin=(215, 170, 130), hair="grey", hair_col=(170, 170, 175), coat=(245, 245, 240), pants=(60, 60, 70), nose="small")]
DOWN = [(-30, 150), (30, 150)]
CHEER = [(-70, -180), (70, -180)]


def blink(t, ph):
    return ((t + ph) % 3.1) < 0.11


def seq(name, who, dur, pose_fn, ph=0.0, scale=1.0):
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    n = int(math.ceil(dur * FPS)) + 2
    for f in range(n):
        t = f / FPS
        surf = skia.Surface(SW, SH)
        c = surf.getCanvas()
        c.clear(skia.ColorTRANSPARENT)
        pose = pose_fn(t)
        pose.setdefault("blink", blink(t, ph))
        pose.setdefault("tilt", 2 * math.sin(t * 1.6 + ph * 3))
        person(c, SW / 2, SH - 10, 1.3 * scale, who, pose, t + ph)
        surf.makeImageSnapshot().save(os.path.join(d, f"{f + 1:04d}.png"), skia.kPNG)
    return n


def main():
    jobs = []
    up = CUE["up"]
    mk = CUE["mistake"]
    for i in range(5):  # hook passengers: calm, then panic on "mistake"
        jobs.append((f"s0_pax{i}", PAX[i], D[0], lambda t, i=i: dict(eyes="wide" if t > mk - 0.1 else "open",
                                                                        mouth="O" if t > mk - 0.1 else "smile",
                                                                        brows="up" if t > mk - 0.1 else "flat",
                                                                        look=(0.2 * (i - 2) / 2, -0.4 if t > mk else -0.1), hands=DOWN), i * 0.7))
    fs, lv = CUE["fast"], CUE["loved"]
    for i in range(3):  # 1952 crowd: amazed on "fast", cheering on "loved it"
        jobs.append((f"s1_old{i}", OLD[i], D[1], lambda t, i=i: dict(eyes="closed" if t > lv else ("wide" if t > fs else "open"),
                                                                        mouth="laugh" if t > lv else ("O" if t > fs else "smile"),
                                                                        brows="up", look=(-0.6, -0.3),
                                                                        hands=CHEER if (t > lv and (i + int(t * 2)) % 2 == 0) or t > lv + 0.6 else DOWN),
                     i * 0.9))
    gr, nb = CUE["grounded"], CUE["nobody"]
    for i in range(2):  # puzzled engineers in the hangar
        jobs.append((f"s3_eng{i}", ENG[i], D[3], lambda t, i=i: dict(eyes="open", mouth="frown", brows="sad", look=(0, -0.4),
                                                                        hands=([(-30, 150), (40, -160)] if i == 0 else [(-40, -160), (30, 150)])
                                                                        if t > nb - 0.2 else DOWN), i * 1.1))
    up = CUE["up"]
    jobs.append(("s4_eng0", ENG[0], D[4], lambda t: dict(eyes="wide" if t > up else "open", mouth="O" if t > up else "smile", brows="up",
                                                          look=(0.6, -0.3), hands=[(-30, 150), (60, 40)]), 0.3))
    jobs.append(("s4_eng1", ENG[1], D[4], lambda t: dict(eyes="open", mouth="smile", brows="flat", look=(-0.6, -0.3), hands=DOWN), 1.4))
    bl = CUE["balloon"]
    jobs.append(("s6_kid", PAX[1], D[6], lambda t: dict(eyes="wide" if t > bl else "open", mouth="O" if t > bl else "smile", brows="up",
                                                         look=(-0.5, -0.5), hands=DOWN), 0.5))
    rd = CUE["rounded"]
    jobs.append(("s9_kid", PAX[2], D[9], lambda t: dict(eyes="wide" if t > rd else "open", mouth="grin", brows="up", look=(-1, -0.3),
                                                         hands=DOWN), 0.2))
    jobs.append(("s11_a", PAX[0], D[11], lambda t: dict(eyes="open", mouth="grin", brows="up", look=(-0.6, -0.2), hands=DOWN), 0.1))
    jobs.append(("s11_b", PAX[2], D[11], lambda t: dict(eyes="open", mouth="smile", brows="up", look=(0.6, -0.2), hands=DOWN), 0.9))
    # flight counter board (s4) and soft cloud textures (s3 / sky windows)
    d = os.path.join(OUT, "s4_counter")
    os.makedirs(d, exist_ok=True)
    fb = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-Bold.otf")
    for f in range(int(math.ceil(D[4] * FPS)) + 2):
        t = f / FPS
        k = max(0.0, (t - up) / 4.5)
        n = int(3000 * (k * k * (3 - 2 * k) if k < 1 else 1.0))
        surf = skia.Surface(600, 320)
        c = surf.getCanvas()
        c.clear(skia.Color(18, 18, 22))
        c.drawRect(skia.Rect(8, 8, 592, 312), skia.Paint(Color=skia.Color(90, 90, 100), Style=skia.Paint.kStroke_Style, StrokeWidth=8))
        f1, f2 = skia.Font(fb, 56), skia.Font(fb, 150)
        c.drawString("FLIGHTS", 300 - f1.measureText("FLIGHTS") / 2, 92, f1, skia.Paint(Color=skia.Color(200, 200, 210)))
        txt = f"{n:,}"
        c.drawString(txt, 300 - f2.measureText(txt) / 2, 262, f2, skia.Paint(Color=skia.Color(120, 255, 140)))
        surf.makeImageSnapshot().save(os.path.join(d, f"{f + 1:04d}.png"), skia.kPNG)
    d = os.path.join(OUT, "clouds")
    os.makedirs(d, exist_ok=True)
    import random
    for k in range(3):
        r = random.Random(k + 5)
        surf = skia.Surface(800, 500)
        c = surf.getCanvas()
        c.clear(skia.ColorTRANSPARENT)
        p = skia.Paint(Color=skia.Color(255, 255, 255), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 28))
        for i in range(14):
            c.drawCircle(r.uniform(180, 620), r.uniform(220, 330), r.uniform(70, 140), p)
        surf.makeImageSnapshot().save(os.path.join(d, f"cloud{k}.png"), skia.kPNG)
    total = 0
    for name, who, dur, fn, ph in jobs:
        total += seq(name, who, dur, fn, ph)
        print(name, "ok", flush=True)
    print("frames:", total)


if __name__ == "__main__":
    main()
