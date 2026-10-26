"""Layout helpers that prevent the most common glitches automatically (see LESSONS.md)."""
from PIL import Image, ImageDraw

from make_chocolate import title_pop
from make_short import F_MID, FONT_M, W, font, text_block

MAX_TEXT_W = W - 140


def fit_font(text, f, min_size=56):
    """Shrink a font until `text` fits on one line (Lesson 1: no wrapped titles)."""
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    size = f.size
    while size > min_size and d.textlength(text, font=font(f.path, size)) > MAX_TEXT_W:
        size -= 2
    return font(f.path, size)


def heading(img, t, title, sub=None, sub_at=1.0, f=F_MID, y=400, colors=None, sub_color=(235, 235, 240)):
    """Title on one line that pops in word by word, with the subtitle placed right under it."""
    ff = fit_font(title, f)
    title_pop(img, title, ff, y, t, colors=colors)
    if sub:
        text_block(img, sub, font(FONT_M, 50), y + int(ff.size * 1.25) + 34, t, sub_color, sub_at)
