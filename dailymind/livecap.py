"""Live captions for the whole video (added for the fork video).

Speech recognition misspells words, so captions use the real script text; only the timing comes
from the recognizer. Each scene's script is spread across that scene's speech in proportion to
word length (punctuation adds a little pause), then cut into short chunks of up to 4 words.

    chunks = build(tl, scene_texts)          # scene_texts[i] = script spoken in scene i ("" = none)
    draw(img, t_global, chunks, y=600)       # current chunk, current word highlighted
"""
from PIL import ImageDraw

from make_short import FONT_B, W, font


def build(tl, scene_texts, max_words=4):
    starts = tl.starts + [tl.length + 5]
    chunks = []
    for i, text in enumerate(scene_texts):
        words = text.split()
        if not words:
            continue
        heard = [t for t, _ in tl.words if starts[i] <= t < starts[i + 1]]
        if not heard:
            continue
        t0, t1 = heard[0], heard[-1] + 0.35
        weights = []
        for w in words:
            weights.append(len(w) + 1 + (4 if w.endswith(("...", ".", "!", "?")) else 2 if w.endswith(",") else 0))
        total = sum(weights)
        times, acc = [], 0
        for wgt in weights:
            times.append(t0 + (t1 - t0) * acc / total)
            acc += wgt
        cur = []
        for t, w in zip(times, words):
            cur.append((t, w))
            if len(cur) >= max_words or w.endswith((".", "!", "?", ",", "...")):
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
    return chunks


def draw(img, t, chunks, y=600, size=58):
    cur = None
    for k, ch in enumerate(chunks):
        end = chunks[k + 1][0][0] if k + 1 < len(chunks) else ch[-1][0] + 1.0
        if ch[0][0] - 0.05 <= t < end:
            cur = ch
            break
    if not cur:
        return
    d = ImageDraw.Draw(img, "RGBA")
    f = font(FONT_B, size)
    space = d.textlength(" ", font=f)
    widths = [d.textlength(w, font=f) for _, w in cur]
    total = sum(widths) + space * (len(cur) - 1)
    x = (W - total) / 2
    d.rounded_rectangle([x - 24, y - 12, x + total + 24, y + size + 18], radius=22, fill=(0, 0, 0, 150))
    active = max([i for i, (tm, _) in enumerate(cur) if t >= tm], default=-1)
    for i, ((tm, w), ww) in enumerate(zip(cur, widths)):
        if i == active:
            d.rounded_rectangle([x - 8, y - 6, x + ww + 8, y + size + 12], radius=14, fill=(255, 215, 60))
            d.text((x, y), w, font=f, fill=(30, 20, 10))
        else:
            d.text((x, y), w, font=f, fill=(255, 255, 255) if i < active else (255, 255, 255, 170))
        x += ww + space
