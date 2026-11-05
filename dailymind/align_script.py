"""Forced alignment for long videos: give every word of the script a time in the voice track.

The speech recognizer (timing.Timeline / pocketsphinx) mishears many words ("Candler" -> "handler"), so instead of
searching for single anchors we align the whole recognized word list to the whole script with dynamic programming
(Needleman-Wunsch with a fuzzy word similarity). Matched script words take the recognizer's time; unmatched ones
are interpolated between their matched neighbours.

    python align_script.py voice.mp3 script.txt out.json   -> {"words": [[t, "Word", para_index], ...], "paras": [[start, end], ...]}
    also writes out.srt (YouTube captions, ~7 words per line, never across paragraphs)
"""
import json
import re
import sys

from timing import Timeline

NUM = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"}


def norm(w):
    w = w.lower().replace("’", "'")
    w = re.sub(r"[^a-z0-9']", "", w)
    return w


def sim(a, b):
    """0..1 similarity between a script word and a recognized word."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a.rstrip("'s") == b.rstrip("'s"):
        return 0.9
    n = min(len(a), len(b))
    pre = 0
    while pre < n and a[pre] == b[pre]:
        pre += 1
    if pre >= 3:
        return 0.6 + 0.3 * pre / max(len(a), len(b))
    # character overlap (cheap edit-distance proxy)
    sa, sb = set(a), set(b)
    j = len(sa & sb) / len(sa | sb)
    return 0.5 * j if j > 0.5 else 0.0


def align(script_words, rec):
    n, m = len(script_words), len(rec)
    GAP = -0.25
    score = [[0.0] * (m + 1) for _ in range(n + 1)]
    back = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        score[i][0] = i * GAP
        back[i][0] = 1
    for j in range(1, m + 1):
        score[0][j] = j * GAP
        back[0][j] = 2
    for i in range(1, n + 1):
        a = script_words[i - 1]
        for j in range(1, m + 1):
            s = sim(a, rec[j - 1][1])
            best, b = score[i - 1][j - 1] + (s if s > 0 else -0.6), 0
            if score[i - 1][j] + GAP > best:
                best, b = score[i - 1][j] + GAP, 1
            if score[i][j - 1] + GAP > best:
                best, b = score[i][j - 1] + GAP, 2
            score[i][j] = best
            back[i][j] = b
    match = [None] * n
    i, j = n, m
    while i > 0 and j > 0:
        b = back[i][j]
        if b == 0:
            if sim(script_words[i - 1], rec[j - 1][1]) >= 0.5:
                match[i - 1] = rec[j - 1][0]
            i, j = i - 1, j - 1
        elif b == 1:
            i -= 1
        else:
            j -= 1
    return match


def main(voice, script_path, out):
    tl = Timeline(voice)
    paras = [p.strip() for p in open(script_path).read().strip().split("\n\n") if p.strip()]
    words, pid = [], []
    for k, p in enumerate(paras):
        for w in p.split():
            words.append(w)
            pid.append(k)
    nw = [norm(w) for w in words]
    rec = [(t, norm(w)) for t, w in tl.words]
    match = align(nw, rec)
    # interpolate unmatched words (monotonic)
    times = list(match)
    known = [(i, t) for i, t in enumerate(times) if t is not None]
    if not known:
        raise SystemExit("alignment failed")
    for i in range(len(times)):
        if times[i] is None:
            prev = max((k for k in known if k[0] < i), default=None, key=lambda k: k[0])
            nxt = min((k for k in known if k[0] > i), default=None, key=lambda k: k[0])
            if prev and nxt:
                times[i] = prev[1] + (nxt[1] - prev[1]) * (i - prev[0]) / (nxt[0] - prev[0])
            elif prev:
                times[i] = prev[1] + 0.3 * (i - prev[0])
            else:
                times[i] = max(0.0, nxt[1] - 0.3 * (nxt[0] - i))
    for i in range(1, len(times)):  # strictly non-decreasing
        times[i] = max(times[i], times[i - 1])
    matched = sum(1 for t in match if t is not None)
    para_spans = []
    for k in range(len(paras)):
        idx = [i for i in range(len(words)) if pid[i] == k]
        start = times[idx[0]]
        end = times[idx[-1]] + 0.45
        para_spans.append([round(start, 3), round(end, 3)])
    json.dump({"length": tl.length, "matched": matched, "total": len(words),
               "words": [[round(t, 3), w, p] for t, w, p in zip(times, words, pid)], "paras": para_spans,
               "pauses": tl.pauses}, open(out, "w"), indent=0)
    # captions
    srt, n = [], 1

    def ts(x):
        h, r = divmod(x, 3600)
        mi, s = divmod(r, 60)
        return f"{int(h):02d}:{int(mi):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"
    i = 0
    while i < len(words):
        j = i
        while j < len(words) and j - i < 7 and pid[j] == pid[i]:
            j += 1
            if words[j - 1].endswith((".", "?", "!")) and j - i >= 3:
                break
        a = times[i]
        b = times[j] if j < len(words) and pid[j] == pid[i] else para_spans[pid[i]][1]
        srt.append(f"{n}\n{ts(a)} --> {ts(max(b, a + 0.6))}\n{' '.join(words[i:j])}\n")
        n += 1
        i = j
    open(out.rsplit(".", 1)[0] + ".srt", "w").write("\n".join(srt))
    print(f"matched {matched}/{len(words)} words; {len(paras)} paragraphs; length {tl.length:.1f}s")


if __name__ == "__main__":
    main(*sys.argv[1:4])
