"""Rewordings + accepted transcriptions after the first voice pass (see the chat / LESSONS)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "script.txt")
s = open(p, encoding="utf-8").read()
rep = {
    "morn5|Even you would struggle. When every reflection looks the same, you'd catch yourself waving at a stranger in a shop window.":
        "morn5|Even you would struggle. When every reflection looks the same, you might wave at a stranger in a shop window.",
    "sport1|Sports would be hit the hardest. Think about Michael Phelps. He's six foot four, but his arms span six foot seven. That's part of why he won twenty eight Olympic medals.":
        "sport1|Sports would be hit the hardest. Think about Michael Phelps. He's six foot four, but his arm span is six foot seven. That's part of why he won twenty eight Olympic medals.",
    "sport3|In our new world, nobody has a natural advantage. Every hundred meter race could end in a near perfect tie.":
        "sport3|In our new world, nobody has a natural advantage. Every one hundred meter race could end in a near perfect tie.",
    "dis9|And scientists already worry about this today.":
        "dis9|Scientists already worry about this today.",
}
for a, b in rep.items():
    if a not in s:
        continue   # already applied
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
os.system(f'python "{os.path.join(HERE, "build_lines.py")}"')
L = json.load(open(os.path.join(HERE, "lines.json")))
for l in L:
    if l["key"] == "dis2":
        l["accept"] = [l["text"].replace("Gros Michel", "gromi shell"), l["text"].replace("Gros Michel", "gros michelle")]
    if l["key"] == "dis4":
        l["accept"] = [l["text"].replace("the Lumper", "the lumber")]
json.dump(L, open(os.path.join(HERE, "lines.json"), "w"), indent=1)
print("ok")
