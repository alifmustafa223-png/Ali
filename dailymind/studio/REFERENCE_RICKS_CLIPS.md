# Reference breakdown — Ricks Clips, "How Mine Salting Worked" (61.1 s, 1080x1920, -14.0 LUFS)

Analysed from the file the owner downloaded (2 fps contact sheets, cut detection, loudness). The video file itself is not
kept in the repo.

## Story (reconstructed from the word captions)
A miner loads a shotgun with gold and fires it into his own mine walls; his buddy watches the gold vanish into the rock.
"You see, it's called salting." Ten years of digging found nothing but rock; a newspaper says a millionaire comes
tomorrow to buy a mine, so he spent his last bucks on gold dust. Morning: the rich man rolls in, white suit, with an
expert. The expert isn't stupid — pans a chunk of wall: under a magnifying glass every flake is FLAT. "Somebody shot
this gold into the wall." The rich guy laughs: "Why would anyone shoot gold into a wall? Insane." The buddy nods:
"Completely insane." He pays up anyway... stays behind, finds a stick of dynamite, has never used one, tosses it like a
firecracker and runs. The dust clears: a vein of REAL gold as thick as your arm, ten feet past where they gave up.

## Why it works
1. **A con with a twist ending.** Villain-ish hero, a doubter, a smarter opponent, irony at the end. Viewers stay to
   see if the trick works.
2. **Big expressive faces.** 2D stick figures with huge heads: wink, smug closed-eye grin, side-eye, open-mouth shock.
   The emotion changes on almost every line and reads at phone size. Characters fill 40-70 % of frame height.
3. **Cheap characters, rich world.** Flat 2D characters composited over warm, lit, detailed 3D sets (mine, western
   town, office). Prop inserts in macro (gold blob flying, pan swirl, dynamite fuse sparks, bank notes, gold dust plate).
4. **One-word captions** — bold white, black outline, centre-lower, one word at a time on the spoken word.
   No title cards, no stamps.
5. **Pacing.** Only 14 hard cuts (~1 per 4.4 s), but a new framing every ~1.5-2 s via push-ins / reframes / inserts.
6. **Voice.** Present tense, conversational third person ("You see, ..."), short sentences, dialogue lines with a
   reaction shot after each ("Completely insane.").
7. **Small extras.** Hand-drawn chalk annotation ("10 FT ↑") for the payoff; -14 LUFS like ours.

## What The DailyMind takes from it (without copying their characters)
- Every video = **one person's story with a twist**, told in present tense, with a doubter and a payoff.
- A **hero character with a big readable face** in most shots (our own design), plus macro prop inserts — the
  miniature worlds stay our signature backdrop.
- A/B test **word-by-word captions** against title + subtitle.
- Payoff annotations drawn in chalk style.

## Decision (owner): full 3D characters
The owner rejected 2D toons over the miniature world. Direction now: film-quality 3D characters acting inside real 3D
sets. Characters = Blender Studio's free rigs **Rain** and **Snow** (CC-BY 4.0 — every video description must credit:
"Rain & Snow rigs © Blender Foundation | studio.blender.org"). Rigs are downloaded into `assets_cache/rigs/` (git-ignored).
Style frame builder: `blender/cove_style.py` (smugglers' pier at sunset, open treasure chest, Rain smug / Snow shocked).
Face controls found by probing — Rain (CloudRig): MSTR-Jaw rot X opens the mouth; ACT-Lips_Corner.* loc Y = smile;
ACT-Eyelid_Upper.* loc -Y = lids down; MSTR-Eyebrow.* loc Y = brows up; set Properties_IKFK ik_arm_* = 0 for FK arms;
FK-Upperarm.R rot Z +70 = arm down (L: negative). Snow: Jaw, MSTR-Eyelid_Upper.*, MSTR-Eyebrow.*; Properties
ik_*_upperarm = 0; FK-UpperArm.R rot Z NEGATIVE = arm down (opposite of Rain).
`blender/hero3d.py` = an abandoned code-built character attempt (read as wooden toys) — kept for reference only.
