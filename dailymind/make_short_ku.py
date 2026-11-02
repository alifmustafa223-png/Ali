"""Render a 1080x1920 YouTube Short: "How Humans Learned to Cook"."""
import math
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
OUT = sys.argv[1]
FONT_B = "/tmp/claude-0/-home-user-Ali/955cd42a-5c7a-5245-9eb6-e7b2c7d4935c/scratchpad/fonts/vz/package/fonts/ttf/Vazirmatn-ExtraBold.ttf"
FONT_M = "/tmp/claude-0/-home-user-Ali/955cd42a-5c7a-5245-9eb6-e7b2c7d4935c/scratchpad/fonts/vz/package/fonts/ttf/Vazirmatn-Medium.ttf"
RTL = dict(direction="rtl", language="ckb")


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)


F_BIG, F_MID, F_SMALL, F_TAG = font(FONT_B, 92), font(FONT_B, 70), font(FONT_M, 50), font(FONT_B, 40)


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def gradient(top, bottom):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)))
    return img


def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f, **RTL) <= maxw:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def text_block(img, text, f, y, t, color=(255, 255, 255), delay=0.0):
    """Slide-up + fade-in text, centered, with a soft shadow."""
    a = ease((t - delay) / 0.5)
    if a <= 0:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lines = wrap(d, text, f, W - 140)
    lh = f.size * 1.55
    oy = (1 - a) * 60
    for i, ln in enumerate(lines):
        x = (W - d.textlength(ln, font=f, **RTL)) / 2
        yy = y + i * lh + oy
        d.text((x + 4, yy + 5), ln, font=f, fill=(0, 0, 0, int(140 * a)), **RTL)
        d.text((x, yy), ln, font=f, fill=color + (int(255 * a),), **RTL)
    img.alpha_composite(layer)


def tag(img, label, t, color):
    a = ease(t / 0.4)
    d = ImageDraw.Draw(img)
    tw = d.textlength(label, font=F_TAG, **RTL)
    x0 = (W - tw) / 2 - 36
    y0 = 250 - (1 - a) * 40
    d.rounded_rectangle([x0, y0, x0 + tw + 72, y0 + 90], radius=42, fill=color + (int(235 * a),))
    d.text((x0 + 36, y0 + 10), label, font=F_TAG, fill=(255, 255, 255, int(255 * a)), **RTL)


# ---------- illustrations ----------

def draw_fire(d, cx, cy, t, s=1.0):
    for i in range(3):
        d.line([(cx - 170 * s, cy + 40 * s + i * 30), (cx + 170 * s, cy - 20 * s + i * 30)], fill=(92, 58, 34), width=int(34 * s))
    for layer, (col, scale) in enumerate([((230, 70, 30), 1.0), ((255, 150, 40), 0.72), ((255, 225, 120), 0.42)]):
        pts = []
        n = 28
        for k in range(n + 1):
            ang = math.pi * k / n
            r = 160 * s * scale
            flick = 1 + 0.35 * math.sin(t * 9 + k * 1.7 + layer) * math.sin(ang) ** 2
            h = (330 * s * scale) * (math.sin(ang) ** 3) * flick
            x = cx - math.cos(ang) * r
            y = cy - h * (0.4 + 0.6 * math.sin(ang * 0.5 + 0.8))
            pts.append((x, y))
        d.polygon(pts + [(cx + 160 * s * scale, cy + 10), (cx - 160 * s * scale, cy + 10)], fill=col)
    for k in range(10):  # sparks
        ph = (t * 0.8 + k * 0.13) % 1
        x = cx + math.sin(k * 7.3 + t * 2) * 120 * s
        y = cy - 200 * s - ph * 500 * s
        r = 7 * (1 - ph) * s
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 200, 90))


def draw_meat_stick(d, cx, cy, t):
    d.line([(cx - 330, cy - 160), (cx + 330, cy - 230)], fill=(120, 80, 45), width=18)
    bob = math.sin(t * 2) * 6
    d.ellipse([cx - 110, cy - 280 + bob, cx + 110, cy - 130 + bob], fill=(150, 70, 40))
    d.ellipse([cx - 70, cy - 250 + bob, cx + 20, cy - 200 + bob], fill=(190, 105, 60))


def draw_brain(d, cx, cy, t):
    grow = 1 + 0.08 * math.sin(t * 3)
    for i, (dx, dy, r) in enumerate([(-90, -40, 120), (60, -60, 130), (130, 40, 100), (-110, 70, 100), (10, 60, 120)]):
        r *= grow
        d.ellipse([cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r], fill=(240, 150, 175), outline=(200, 100, 135), width=8)
    d.line([(cx, cy - 170), (cx - 20, cy + 160)], fill=(200, 100, 135), width=8)


def draw_pot(d, cx, cy, t, fire=True):
    if fire:
        draw_fire(d, cx, cy + 300, t, 0.6)
    d.ellipse([cx - 260, cy - 60, cx + 260, cy + 40], fill=(110, 60, 35))
    d.chord([cx - 260, cy - 260, cx + 260, cy + 280], 0, 180, fill=(170, 95, 55))
    d.ellipse([cx - 230, cy - 50, cx + 230, cy + 30], fill=(205, 140, 60))
    for k in range(6):  # bubbles
        ph = (t * 1.3 + k * 0.17) % 1
        x = cx - 160 + k * 64
        r = 10 + 12 * ph
        d.ellipse([x - r, cy - 10 - r, x + r, cy - 10 + r], outline=(250, 200, 110), width=5)
    for k in range(3):  # steam
        pts = []
        for j in range(14):
            yy = cy - 90 - j * 22
            xx = cx - 120 + k * 120 + math.sin(j * 0.5 + t * 3 + k) * 26
            pts.append((xx, yy))
        d.line(pts, fill=(255, 255, 255, 120), width=14)


def draw_tablet(d, cx, cy, t):
    d.rounded_rectangle([cx - 260, cy - 330, cx + 260, cy + 330], radius=50, fill=(196, 160, 112), outline=(150, 115, 75), width=10)
    rows = int(min(10, t * 4))
    for r in range(rows):
        y = cy - 260 + r * 54
        for c in range(9):
            x = cx - 210 + c * 50 + (r % 2) * 12
            d.polygon([(x, y), (x + 26, y + 8), (x, y + 18)], fill=(120, 88, 55))
            d.line([(x + 26, y + 8), (x + 38, y + 8)], fill=(120, 88, 55), width=5)


def person(d, cx, cy, s, shirt, skin=(225, 175, 135)):
    d.ellipse([cx - 60 * s, cy - 260 * s, cx + 60 * s, cy - 140 * s], fill=skin)
    d.rounded_rectangle([cx - 95 * s, cy - 130 * s, cx + 95 * s, cy + 150 * s], radius=int(60 * s), fill=shirt)


def draw_family(d, cx, cy, t):
    person(d, cx - 200, cy + 60, 1.2, (150, 60, 90))
    person(d, cx + 220, cy + 160, 0.8, (60, 120, 200))
    sw = math.sin(t * 4) * 30
    d.line([(cx - 90, cy - 30), (cx + 10 + sw, cy + 50)], fill=(225, 175, 135), width=26)
    d.line([(cx + 150, cy + 60), (cx + 40 + sw, cy + 90)], fill=(225, 175, 135), width=20)
    draw_pot(d, cx + 20, cy + 230, t, fire=False)


def draw_phone(d, cx, cy, t):
    d.rounded_rectangle([cx - 200, cy - 380, cx + 200, cy + 380], radius=50, fill=(25, 25, 35))
    d.rounded_rectangle([cx - 175, cy - 340, cx + 175, cy + 340], radius=30, fill=(250, 245, 235))
    d.rectangle([cx - 175, cy - 250, cx + 175, cy + 20], fill=(255, 120, 60))
    tri = 40
    d.polygon([(cx - tri, cy - 160), (cx - tri, cy - 70), (cx + tri, cy - 115)], fill=(255, 255, 255))
    prog = (t * 0.25) % 1
    d.rectangle([cx - 175, cy + 20, cx - 175 + 350 * prog, cy + 32], fill=(230, 40, 40))
    for k in range(3):
        y = cy + 80 + k * 70
        d.rounded_rectangle([cx - 140, y, cx + 140 - k * 50, y + 30], radius=15, fill=(220, 210, 195))
    for k in range(5):  # floating hearts as dots
        ph = (t * 0.6 + k * 0.2) % 1
        x = cx + 240 + math.sin(k + t * 2) * 30
        y = cy + 300 - ph * 600
        r = 22 * (1 - ph * 0.5)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 80, 110))


def draw_loop(d, cx, cy, t):
    labels = ["سەیرکە", "تاقیکە", "تامکە", "دووبارە"]
    cols = [(255, 120, 60), (90, 170, 255), (120, 210, 120), (240, 90, 160)]
    rot = t * 0.9
    d.ellipse([cx - 300, cy - 300, cx + 300, cy + 300], outline=(255, 255, 255, 90), width=8)
    for i, (lab, col) in enumerate(zip(labels, cols)):
        a = rot + i * math.pi / 2
        x, y = cx + math.cos(a) * 300, cy + math.sin(a) * 300
        d.ellipse([x - 120, y - 120, x + 120, y + 120], fill=col)
        tw = d.textlength(lab, font=F_TAG, **RTL)
        d.text((x - tw / 2, y - 34), lab, font=F_TAG, fill=(255, 255, 255), **RTL)


# ---------- scenes: (seconds, bg, renderer) ----------

def s_hook(img, d, t):
    draw_fire(d, W / 2, 1380, t, 1.2)
    text_block(img, "مرۆڤ چۆن فێری", F_MID, 420, t)
    a = ease((t - 0.4) / 0.4)
    size = int(120 + 30 * math.sin(min(t, 1.5) * 4) * (1 - min(t / 1.5, 1)))
    f = font(FONT_B, max(60, size))
    if a > 0:
        dd = ImageDraw.Draw(img)
        tw = dd.textlength("چێشت لێنان بوو؟", font=f, **RTL)
        dd.text(((W - tw) / 2, 600), "چێشت لێنان بوو؟", font=f, fill=(255, 190, 70, int(255 * a)), **RTL)


def s_fire(img, d, t):
    tag(img, "زیاتر لە ١ ملیۆن ساڵ لەمەوبەر", t, (200, 70, 30))
    draw_fire(d, W / 2, 1450, t)
    draw_meat_stick(d, W / 2, 1450, t)
    text_block(img, "هەمووی بە ئاگر دەستی پێکرد.", F_BIG, 430, t, delay=0.2)
    text_block(img, "مرۆڤە سەرەتاییەکان گۆشتیان لەسەر ئاگر دادەنا، و تامی خۆشتر بوو.", F_SMALL, 760, t, (255, 225, 190), 0.9)


def s_brain(img, d, t):
    tag(img, "گۆڕانکارییە گەورەکە", t, (170, 60, 110))
    draw_brain(d, W / 2, 1350, t)
    text_block(img, "خواردنی لێنراو ئاسانتر هەرس دەبێت.", F_MID, 430, t, delay=0.2)
    text_block(img, "زانایان پێیان وایە ئەو وزەیە یارمەتی دا مێشکمان گەورەتر بێت.", F_SMALL, 720, t, (255, 220, 235), 1.0)


def s_pot(img, d, t):
    tag(img, "نزیکەی ٢٠،٠٠٠ ساڵ لەمەوبەر", t, (160, 90, 40))
    draw_pot(d, W / 2, 1330, t)
    text_block(img, "دواتر مەنجەڵی گڵ هات.", F_BIG, 430, t, delay=0.2)
    text_block(img, "ئیتر دەمانتوانی شۆربا و خواردنی جۆراوجۆر لێبنێین.", F_SMALL, 760, t, (255, 230, 200), 0.9)


def s_tablet(img, d, t):
    tag(img, "نزیکەی ٣٧٠٠ ساڵ لەمەوبەر", t, (120, 90, 60))
    draw_tablet(d, W / 2, 1300, t)
    text_block(img, "یەکەم ڕێچەتەی نووسراو", F_MID, 400, t, delay=0.2)
    text_block(img, "لەسەر تەختەی گڵ، لە میزۆپۆتامیا — هەر لێرە، نزیک خۆمان!", F_SMALL, 620, t, (255, 235, 210), 0.9)


def s_family(img, d, t):
    tag(img, "بۆ هەزاران ساڵ", t, (150, 60, 90))
    draw_family(d, W / 2, 1250, t)
    text_block(img, "بەڵام زیاتر لە خێزانەوە فێر بووین.", F_MID, 400, t, delay=0.2)
    text_block(img, "سەیرکردن. لاسایی کردنەوە. تامکردن.", F_SMALL, 640, t, (255, 225, 230), 1.0)


def s_phone(img, d, t):
    tag(img, "ئەمڕۆ", t, (230, 60, 60))
    draw_phone(d, W / 2, 1320, t)
    text_block(img, "هەر کەسێک دەتوانێت لە ڤیدیۆیەکەوە فێر بێت.", F_MID, 400, t, delay=0.2)


def s_loop(img, d, t):
    draw_loop(d, W / 2, 1300, t)
    text_block(img, "بەڵام ڕێگاکە هەر وەک خۆیەتی:", F_MID, 400, t, delay=0.1)
    text_block(img, "فۆڵۆمان بکە بۆ زیاتر!", F_SMALL, 1720, t, (255, 210, 120), 1.8)


SCENES = [
    (3.0, ((40, 15, 10), (10, 5, 5)), s_hook),
    (4.5, ((60, 25, 15), (15, 8, 5)), s_fire),
    (4.5, ((60, 25, 55), (20, 8, 25)), s_brain),
    (4.5, ((70, 45, 25), (25, 15, 8)), s_pot),
    (4.5, ((75, 60, 40), (30, 22, 14)), s_tablet),
    (4.5, ((80, 40, 50), (30, 12, 20)), s_family),
    (4.0, ((30, 40, 70), (10, 12, 28)), s_phone),
    (5.0, ((25, 30, 45), (8, 10, 18)), s_loop),
]


def main():
    if len(sys.argv) > 2:  # optional per-scene durations, e.g. "3.1,6.2,..."
        durs = [float(x) for x in sys.argv[2].split(",")]
        SCENES[:] = [(d,) + s[1:] for d, s in zip(durs, SCENES)]
    bgs = [gradient(*s[1]).convert("RGBA") for s in SCENES]
    total = sum(s[0] for s in SCENES)
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-f", "lavfi", "-i",
         # soft ambient pad: A minor chord with slow tremolo
         f"aevalsrc='0.06*(sin(2*PI*220*t)+sin(2*PI*261.63*t)+sin(2*PI*329.63*t)+0.5*sin(2*PI*110*t))*(0.7+0.3*sin(2*PI*0.25*t))':s=44100:d={total}",
         "-af", f"afade=t=in:d=1.5,afade=t=out:st={total - 2}:d=2",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
         "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", OUT],
        stdin=subprocess.PIPE,
    )
    for idx, (dur, _, fn) in enumerate(SCENES):
        n = int(dur * FPS)
        for i in range(n):
            t = i / FPS
            img = bgs[idx].copy()
            d = ImageDraw.Draw(img, "RGBA")
            fn(img, d, t)
            # fade from black at scene start, to black at scene end
            fade = min(ease(t / 0.3), ease((dur - t) / 0.3))
            if fade < 1:
                img = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, fade)
            # progress bar
            dd = ImageDraw.Draw(img)
            elapsed = sum(s[0] for s in SCENES[:idx]) + t
            dd.rectangle([0, H - 14, W * elapsed / total, H], fill=(255, 170, 60))
            proc.stdin.write(img.convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
