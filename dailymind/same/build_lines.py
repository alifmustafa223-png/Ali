"""script.txt -> lines.json for tts/chatter_takes.py (chapter breaks get a longer pause)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
L, ch, first = [], None, False
for line in open(os.path.join(HERE, "script.txt"), encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    if line.startswith("#"):
        ch, first = line[1:].strip(), True
        continue
    k, t = line.split("|", 1)
    L.append({"key": k, "text": t, "gap_before": 2.6 if first else 0.95, "chapter": ch})
    first = False
L[0]["gap_before"] = 0.2
json.dump(L, open(os.path.join(HERE, "lines.json"), "w"), indent=1)
w = sum(len(x["text"].split()) for x in L)
c = sum(len(x["text"]) for x in L)
print(len(L), "lines,", w, "words,", c, "chars; estimated", round(c / 17.3 + sum(x["gap_before"] for x in L)), "s")
