"""Second content pass: the first voice came to 7:43; these sourced additions bring it to ~10 minutes."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "script.txt")
s = open(p, encoding="utf-8").read()
after = {
    "morn5": ["morn6|There is one group that would barely notice. Newborn babies already recognize their mother's voice, because they hear it for months before they're born.",
              "morn7|So families would lean on voices, laughs, and little habits, the same way you can recognize someone you love in the dark."],
    "id7": ["# crime",
            "crime1|Now imagine trying to solve a crime. Today, one of the strongest pieces of evidence police can find is DNA.",
            "crime2|But in our world, everyone has the same body. And police have already met this problem, with identical twins.",
            "crime3|In two thousand nine, thieves broke into a famous department store in Berlin and stole jewelry worth millions.",
            "crime4|Police found DNA on a glove left at the scene. It matched a pair of identical twin brothers, but the tests could not tell which brother it came from.",
            "crime5|The court couldn't prove which twin did it, so both brothers walked free. Now imagine that problem with eight billion people.",
            "crime6|Detectives would go back to old school methods. Fingerprints, voices, receipts, phone records, and witnesses who remember how someone walks.",
            "crime7|And in a world of identical faces, the perfect disguise would be walking down the street as yourself."],
    "sport5": ["sport5b|Coaches would become the real superstars, because the right plan would matter more than any body."],
    "job3": ["job3b|And there's another twist. In studies, people rated as better looking tend to earn a few percent more, on average. Economists call it the beauty premium.",
             "job3c|In our new world, the beauty premium disappears overnight. Nobody gets hired, or ignored, because of their face."],
    "dis7": ["dis7b|That's also why doctors want diverse groups in medical studies. A medicine can work well for one group, and very differently for another."],
    "end5": ["end5b|Your jokes, your kindness, your stories, and the way you treat people would still be completely yours."],
    "end6": ["end6b|So the next time you look in the mirror, remember. Your face is just the cover. The story is you."],
}
out = []
for line in s.splitlines():
    out.append(line)
    k = line.split("|", 1)[0]
    if k in after:
        out.extend(after.pop(k))
assert not after, after
open(p, "w", encoding="utf-8").write("\n".join(out) + "\n")
print("added")
