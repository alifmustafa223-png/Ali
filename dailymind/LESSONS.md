# Cronos File — lessons learned (read before every video, add to it after every video)

## Text & layout
1. **Titles must fit on one line.** Wrapped titles collided with subtitles in pizza, chocolate,
   carrot, honey, lobster. → Use `style.heading()`, which shrinks the title to fit and places the
   subtitle under the title's real height.
2. **No orphan words** ("...was / once", "jam!"). Split hook text into deliberate lines.
3. **Keep art below y≈880** when a subtitle exists; stamps go in the gap between text and art,
   never over characters, crowns or food.
4. Text that sits on art must be removed/hidden when the art moves (falling bottles' "?").

## Drawing
5. **Never draw see-through shapes on top of other art with ImageDraw** — on RGBA images it
   *replaces* pixels, punching holes (bokeh dots, tomb light rays, calendar pages).
   → Draw glows/rays/beams on their own layer and `alpha_composite` it.
6. **Never draw with alpha 0** (it erases). `back()` now returns exactly 0 before an animation
   starts; keep `if p <= 0: continue` guards.
7. Only solid shapes cast shadows (camera shadow ignores alpha < 200).
8. Polygons must not cross themselves (capsule "candy cane" bug) — order the points around the shape.
9. Characters: hats/monocles/faces must be positioned from the head formula
   (head centre = cy - 200·s in `person()`); stripes/clothes start below the head.
10. Moving things (trains, ships) must be on screen when the narrator talks about them.

## Hook (first 2 seconds)
11. **No pause before or inside the first sentence** — the claim is spoken in ~1.5 s.
12. Frame 0 shows the hook text + moving art. The key word **slams** in on the spoken word.
13. A second surprise lands at ~2–3 s (counter, price tag, flip).

## Timing
14. Run `align.py` on the voice; cut scenes in pauses; time stamps/pop-ins to the exact word.
15. Length 61–65 s: script 900–930 characters (≤ 1,000 so it costs 14 credits);
    use `atempo` 0.97–1.03 to land inside the range.

## Every video
16. Run `qa.py final.mp4 "durations"` and look at every tile of `qa_sheet.png`,
    plus extra frames at every stamp/slam/transition moment.
17. After the video: add any new glitch and its fix to this file.

## Added after the potato video
18. **Show things when they're mentioned, not before** (guards appeared before "put guards").
    Introduce the person first; pop objects in on their word.
19. **Short scenes need fast motion**: anything travelling (ship, train) must arrive within the
    scene's length — base the easing on the scene duration, not a fixed number.
20. Long title text in a slam: measure it first (slam text must be <= 940 px wide).

## Added after the nutmeg video
21. **Use `timing.Timeline` for every cut and cue** — it matched hand timing to 0.01 s.
    Speech recognition mishears some words ("and here's" → "and years", "plague" → "played"),
    so anchor on plain words; the tool stops with an error instead of guessing.
22. Things that pop in during the hook's second beat must stay **below y≈880**, clear of the
    hook text and slam (the New York skyline grew into "MORE THAN GOLD").
23. Hook top-lines get `fit_font()` too — long ones touched the screen edges.
24. Use `fx.overlay()` for smoke/glows; use `fx.impact()` when a slam or stamp lands.

## Added after the popcorn video
25. **Sound design is part of every video now** (`audio.py`): real music that ducks under the
    voice, whoosh on every cut, thud on slams/stamps, pop on pop-ins, click/ding on the CTA.
26. **Master to -14 LUFS.** Videos 1–14 were at -18.8 LUFS (≈5 dB quieter than other Shorts —
    YouTube turns loud videos down but never turns quiet ones up). `qa.py` now checks this.
27. Timing anchors can list alternatives the recognizer may hear: `"then|than the"`.
28. Accessories go where they belong on the body: bow ties at the collar (head-formula − 120·s),
    not under the face — on a small face they read as a tongue.
29. Stamps must not cover the scene's main object; put them in the gap under the subtitle.

## Added after the banana video (stop-the-scroll hook)
30. **Stop-the-scroll formula**: bright, *contrasting* hook background (most Shorts are dark);
    address the viewer ("you've"); full sentence on screen from frame 0 as captions (works muted);
    a visual of the claim at once (copy-paste clones); a stakes beat at ~2–3 s.
31. **Hero object must contrast with the background** — yellow bananas vanished on yellow;
    on complementary blue they pop. qa.py's frame-0 "detail" check caught the flat frame.
32. **Karaoke captions: highlight the current word with a box, never resize words** — growing
    words collided with their neighbours ("Everybanana").
33. Use exact recognized word times for captions when the word count matches; otherwise spread.
34. Run `Timeline.check([...all anchors and cues...])` before rendering — one pass, no retries.

## Added after the toothpaste video
35. Long hook sentences wrap to 3 caption lines — place the slam **below the last caption line**
    (captions end ≈ y 300 + lines·100), not at a fixed y.
36. Small props need contrast and space: put ingredients on their own dark plates in a clear row,
    never on top of busy background art (eggshells vanished on the pyramid).
37. In timing anchors, `|` gives alternatives **per word**, not per phrase
    ("and actually|and it" splits wrongly — use separate plain phrases).
38. A make_*.py now runs `Timeline.check()` itself and stops with the heard words on any miss.

## Added after the fork video
39. **Live captions for the whole video** (`livecap.py`): script text (never the recognizer's
    spelling), timed per scene, ≤4-word chunks, current word highlighted, placed mid-screen
    (y≈600) because YouTube's own UI covers the bottom of Shorts.
40. **Open-loop hook**: sentence 2 promises a payoff that only arrives later
    ("...and one princess paid for it with her life!").
41. **Loop ending**: the CTA sits on a solid panel over the hook scene, then fades out for the last
    second so the final frame matches frame 0 and replays flow seamlessly.
42. Semi-transparent CTA panels let art "ghost" through — keep them ≥ 90 % opaque.
43. Hands holding things: palm + finger shapes + thumb; a plain rectangle reads as a bottle.

## USER PREFERENCE (after the fork video) — overrides lessons 30, 32, 39
44. **The owner prefers the classic ketchup-video look**: dark scenes, title + subtitle (subtitle
    appears on its spoken words), vignette and dust, no caption boxes, no bright hook frame,
    classic "Learned something new?" ending. Keep the slam, open loop, impact, splats, sound
    design and -14 LUFS. Template: `make_fork_classic.py`.

## Added after the animation upgrade (fork v2)
45. **Art pass for every video** (`look.camera`): automatic cartoon outlines + lower-right shade +
    upper-left highlight on every drawn object; use `look.backdrop()` for subtle scene depth
    (hall / street / table) and `look.Talk` + `talking_mouth()` so on-screen speakers' mouths
    follow the voice loudness.
46. Lesson 5 applies to backdrops too: they must be drawn on their own layer (first try came out
    as solid black arches and glaring white bricks).

## Added after the pineapple video (first one made from Gemini illustrations)
47. **AI-picture workflow**: ~10 Gemini images (9:16, no text, dark empty top third, same style
    block + identical character descriptions in every prompt). Animate with `shot()` (slow
    push-in/pull-out toward the subject), then put living light *on the real objects*
    (candles, lanterns, fire flicker), weather/particles (snow, steam, flies, stars, sparkles), and
    small character tricks (eyelid blink painted from sampled skin colour). Map features first with
    a gridded contact sheet of every picture (source-pixel coordinates).
48. Paste prompts into a **new Gemini chat** — with an old picture open, Gemini edits it instead
    (the "green-screen cut-outs" came back as green paint over the market picture).
49. **Free voice when vidIQ credits run out**: Kokoro (offline, `scratchpad/tts/say.py`, voice
    am_michael, speed 1.16) — generate per paragraph and save exact paragraph start/end times, so
    scene cuts need no speech recognition.
50. **Loudness: master in two passes** (measure, then `loudnorm linear=true` with the measured
    values). The single pass landed at -16.6 LUFS on this voice; now -14.7.
51. Stamps sit at y≈720 with **one-line subtitles only** — measure every subtitle (≤ 940 px at 50 px);
    two-line subtitles ran into the stamp ("MANURE!" under "EWW!").
52. **Characters move** (`motion.py`, puppet-style mesh warp with OpenCV): heads tilt/nod/shake
    around the neck, arms lift around the shoulder, chests breathe, props swing (watch, lantern,
    shovel), legs kick. Rigid core + soft edge (smoothstep) so bodies bend, never tear. Keep angles
    small (heads 2-4°, arms 3-5°, light props up to 14°); check close-up crops at extreme poses
    before rendering; make lights follow moving props (the lantern glow swings with the lantern).
53. **Title pop has no overshoot** (`title_pop` scale capped at 1.0): the bouncing words grew into
    each other mid-pop ("Thedisgustingtrick") — invisible on sheets, caught on frame-by-frame zoom.
    The first scene of any clip opens with a splat reveal so no title is ever half-drawn on frame 0.
54. Thrown particles (manure, sweat) must start **on the object** they come from and use its colour
    with a highlight; dark round blobs far from the shovel read as olives.
55. **Skia engine for code-drawn art** (`ultimate/ultimate.py`): anti-aliased bezier shapes, real
    gradients, blurred soft shadows/glows, a volumetric spotlight, bloom (threshold colour matrix +
    blur + additive), vignette and film grain — far beyond PIL. Coins use a real physics simulation
    (gravity, bounce, spin, motion stretch) and lie FLAT once they land (edge-on coins read as sticks).
    Never blink during a reaction beat (the shocked face blinked on "$8,000").
56. **Full code-drawn videos with the toon kit** (`ultimate/toon.py` + `make_toon.py`): chibi characters
    with IK arms, poses and expressions; Skia art per scene, then the classic PIL text layer and gold
    splats on top. Check one still per scene before the 25-minute render. Export with `base.CRF = 16`
    (slow preset) for sharper Full HD after YouTube's compression.
57. Never reuse a short helper name (`S`, `P`, `C`) as a variable in `__main__` — `S = starts`
    shadowed the stroke helper and crashed the render on frame 1 (stills mode didn't catch it).

## Added after the pineapple re-voice (vidIQ "Chris")
58. **Chris reads ~996 chars in ~59 s** — too short on its own. Slow it with `atempo=0.97` (before the
    highpass/compressor) to land at ~61 s of voice / ~63 s total, then rescale the paragraph timings.
59. **Re-run speech recognition after any tempo change** — the recognizer hears different words on the
    slowed take ("heated"→"heeded", "fast ships"→"friendships", "went bad"→"been to a one bed").
    Add the misheard words as `|` alternatives in the cue anchors; never guess times by hand.
60. Paragraph cuts for a vidIQ voice come from the word list + `silencedetect` (every sentence and some
    commas also pause, so match paragraph first-words to the pause just before them).

## Added after the chewing-gum video (Skia toon, vidIQ "Chris")
61. **Long Chris takes: tighten pauses, don't speed up.** `tighten.py in.mp3 out.wav 0.65` cuts every
    pause longer than 0.65 s from its middle (20 ms crossfades). 999 chars came back at 64.2 s;
    tightened to 61.6 s with the natural pace kept.
62. **A stamp/slam near the end of a scene needs ~0.6 s of full visibility before the splat.**
    "FAILED", "AN ARMY?!" and "EMPIRE!" were readable for only 0.3 s. Fixes: insert 0.35–0.5 s of
    silence after the key word, and cut late in the pause (`max(mid, pause_end - 0.25)`).
63. **Anchors: one `|` list per word**, e.g. `"they|then saw"` — never `"they saw|then he saw"`
    (it splits on spaces). Short anchors match longer words ("so" matched "soap"): add a 2nd word.
64. **Lip-sync from the real voice**: `load_vox()` = RMS per frame (30 fps) normalised to the 95th
    percentile → `mouth="talk", talk=vox(global_t)` only while the character is "speaking" a quote.
65. **New toon features** (`toon.py`): `walk=phase` (legs swing around the hip, body bobs; derive
    phase from distance travelled so feet never slide), `mouth="chew", talk=t`, hats
    (`bicorne`, `bowler`, `laurel`) with `hat_bounce` spring, `sideburns`, `pigtails`,
    `epaulettes`/`medals`/`sash` (chest items under the arms, epaulettes over them).
66. Check **every pose's hand side**: hands = [left, right]; the girl raised the wrong hand and held
    the coin over her own face. Things that fly (gum balls) must never cross a face on their path.
67. Particles that rain (coins) go **behind** the hero character, or they cover his face.
68. A thought bubble's trail must not touch the speaker's hat; put the bubble beside the head.
69. Keep wall art (maps, frames) below the slide-in path of text blocks (they slide up 60 px).

## Added after the ice video (Frederic Tudor, the Ice King)
70. **Natural voice = untouched voice.** The owner heard the gum voice as less natural: cutting pauses
    (`tighten.py`) and inserting digital silence break the speaker's breathing rhythm. Now: write the
    script so Chris lands at 59–63 s on his own (997 chars with "..." and short sentences = 63.1 s),
    use it exactly as generated, only `highpass=f=70` + a gentle `acompressor` (ratio 1.6).
    Shorten the CTA tail (`TAIL = 1.75`) instead of editing the voice when it runs long.
    Write years as words ("eighteen-oh-six") and use contractions/short sentences for a talking feel.
71. **Long hair glitch (owner report):** `hair_back` was drawn AFTER the torso, so long hair lay on top
    of the shoulders/arms, and the curly style stacked all its back curls on one side like a braid over
    the left arm. Now `person()` draws the back hair behind the body, and curly hair is a symmetric
    halo ending at the jaw. Test sheet: every hairstyle × poses (down/up/hands-on-head/side/scratch).
72. Props held at the chest (buckets, shakers, ice blocks) must sit **below the chin**: check
    `hand_pos` y against the head centre (`y - 332*s`); a raised hand + prop covered two faces.
73. A flying prop (newspaper) must settle **above** the crowd's head tops (`head_top(y, s)`).
74. Glows on bright props: keep the glow alpha low (≤ 70) or the bloom pass turns the prop into a white blob.

## Added after the chess video (the queen used to be the weakest piece)
75. **Board scenes: pieces must be big enough to read their faces** — first pass used 0.5x pieces on a
    1,060 px board and they were unreadable dots. Rule of thumb: the hero piece ≥ 380 px tall on screen,
    others ≥ 250 px; use fewer pieces rather than smaller ones. `Board.sq()` returns a depth scale `k`.
76. Spotlight the hero piece (soft beam + floor glow) so viewers know who the story is about in the hook.
77. Animals: check they read correctly at a glance — the first horse (vertical neck) read as a llama.
    Horses need a forward-leaning thick neck, a long head angled down, ears and a mane.
78. Don't stack glow sources (piece glow + burst sparkles + bloom) on one object — it turns white.
79. The recognizer heard "like" as "within": always list alternatives for the CTA anchor too.
