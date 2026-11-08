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
80. **Never leave a scene empty while waiting for a cue word.** The army scene showed bare ground for 2 s
    before "elephants". Fill the wait with the "before" state (chess pieces standing in place) and
    transform it on the word (piece shrinks + poof + army unit pops in).
81. Give waiting characters life (sad wobble, sweat, bob) — a still hero for 4 s reads as a frozen frame.
82. CTA must show SUBSCRIBED + the bell for ≥ 0.5 s: check `cta_off + 3.6` against the CTA scene length
    and raise `TAIL` (not the voice) if needed — frame truncation eats ~0.15 s at the end.

## Added after the Coca-Cola video (invented as medicine)
83. **Pick topics with proven demand**: one `vidiq_outliers` call (5 credits, contentType short) on the
    channel's niche showed "products invented for a different purpose" (41x) and "who invented famous
    drinks" (25x) breaking out — the Coca-Cola-was-medicine story combines both.
84. **Anchor matching is prefix-based**: "cocaine" matched the earlier word "coca" (first 4 letters), so a cue
    fired before frame 0. Use a 2-word anchor ("had cocaine") with a negative lead to land on the word.
85. Text inside props (bottle labels) must be measured and shrunk to fit — "BRAIN TONIC" was clipped.
86. Words that slide together must not overlap: keep them apart and fade in the joining hyphen.
87. Long titles: if `fit_font` can't fit at 56 px the title wraps with an orphan — shorten the wording.
88. With the voice untouched and ≥ 63 s, start the CTA a beat early (`cta_off - 0.4`) instead of a long
    tail, so SUBSCRIBED + bell still get ≥ 0.5 s and the total stays ≤ 65 s.
89. No brand logos or trademark shapes in the art: plain apothecary bottles and glasses only.
90. **Retention: no character stands still for 2+ s.** Intro scenes start with a walk-in (`walk=` phase from
    distance, ~2–3 s), and waits get an action (a glass sliding down the counter). The half-second contact
    sheet of the FINAL file is where static stretches show up — check it for motion, not just glitches.
91. Moving props must not pass behind/through hanging signs or heads: check their end position against
    tags and `head_top()` of nearby characters.

## Added after the first 10-minute video ("What If You Got $1 Every Time Someone Thought About You?")
92. **Long-form = 16:9, one shot per script paragraph** (74 shots for 9:43). Use `align_script.py` (forced
    alignment of the WHOLE script, DP over the recognizer's words) instead of single anchors: 87% of words match
    directly, the rest are interpolated, and every cue is `Q.at(word, n)` inside a paragraph.
93. vidIQ voiceover max 5,000 chars: split the script at a chapter start (not mid-scene), record two parts,
    join with 0.9 s of padding. The download host changed to `assets.vidiq.com`, which this environment's
    network policy blocks: ask the owner to allow it, or to download the MP3s and upload them.
94. **Guards against the two worst glitches, built in**: `safe_hands()` moves any hand that would land on the face
    to the chest; `TEXT_MIN_Y` keeps every title below the balance counter / notification card (one card at a time).
95. Run `make_thoughts.py check` first: it renders 4 frames per shot and catches every missing cue word and code
    error in ~90 s before a 30-minute render (it caught 43 problems in the first pass).
96. Review a mid-shot contact sheet for ALL shots (3 sheets of 25), fix, re-render the sheet — two rounds found
    titles overlapping chalkboard text, arms crossing faces, and a thumbnail word cut off at the edge.
97. Thumbnail for long-form: shocked face + glowing object + max 4 words + one red money banner; measure text
    and shrink to fit (first try cut "THOUGHT?!" off the frame).
98. **Long-form needs live captions** (current word in gold, outlined text over a soft bottom shadow, no box):
    the first full render had 3-6 s stretches with no text while titles waited for late cue words — the exact
    spots where long-form viewers leave. Captions also carry muted viewers. Colour-only highlight: scaling the
    active word made neighbouring words touch.
99. Final files over 100 MB (a 10-minute 1080p video is ~180 MB) can't go to GitHub: keep them in .gitignore
    and deliver with SendUserFile; the code + voice + align.json in git can rebuild them.

## Added after the bubble wrap video (invented as wallpaper)
100. **Satisfying = hard to scroll past.** A reusable POP system (`popfx` ring + shards, `comic_pop` starburst,
     `bubble_wall` with per-bubble pop times, finger press-squish 0.12 s before each pop) and every pop is collected
     into `POPS` so the SFX track gets a real pop sound on the exact frame. The hook pops from frame 0.
101. Reaching hands: keep targets within arm's reach (~250 px at scale 1.55 from the shoulder) — the IK clamps the
     elbow but the sleeve is still drawn to the target, so far targets make rubber arms.
102. Big repeated-pattern backgrounds (bubble walls) + bloom wash out to white: use a dark tint, low bubble alpha and a
     dark top gradient so titles stay readable (classic dark style).
103. Light skies behind white titles fail contrast — use evening/sunset skies in daytime scenes.
104. vidIQ now serves voiceovers from assets.vidiq.com: the "Ali (DailyMind videos)" environment allows it, so new
     sessions can download voices directly. Note: this 953-char voiceover was charged 28 credits (not 14).

## Added after the purple video (worth more than gold, made from snail slime)
105. **New end card (owner disliked the old LIKE/SUBSCRIBE): `cta2.draw_cta2`** — everything is Skia vectors drawn on
     the final frame (no bloom/grain over it, no PIL bitmaps): glass card with a gradient border, avatar + handle,
     thumbs-up path that fills blue with a spring + burst, SUBSCRIBE pill with ripple that morphs to grey SUBSCRIBED
     with a drawn check, a ringing bell, and a pointer hand that glides on a curve and dips on each tap. Taps land on
     the spoken "like" and 0.75 s later; SUBSCRIBED + bell stay ≥ 1.2 s.
106. Retention check on the FINAL file's half-second sheet: any character standing still for ≥ 3 s gets an action
     (servants walk in carrying silk, the chemist stirs with steam, barrels roll out of the factory, the snail crawls
     in from frame 0 instead of popping in late).
107. Saturated bright costumes (pink/lilac dresses) + bloom = white blob: use deeper tones (mauve 140,75,175).

## Added after the Monopoly video (follow-up to the best performer: chess)
108. **Why chess won and how to repeat it:** a famous GAME (huge audience) + a hidden-origin twist + game pieces as
     characters with faces. Monopoly reuses the recipe: houses/hotels with faces, a villain top-hat token that chomps
     houses on the hook word, a generic board (no trademarked logo/mascot/board art).
109. vidIQ voiceovers now cost 28 credits per ~1,000 chars (they were 14). Check `vidiq_balance` before recording.
     A short take (58.3 s) can be fixed with a barely audible `atempo=0.985` + a slightly longer end card (TAIL 2.2).
110. skia ColorFilters.Matrix offsets are in 0..1, not 0..255 — an offset of 20 turned a bronze statue neon yellow.
111. Motion check on the final file again found 4 still stretches (rules, homemade boards, $500 wait, Darrow): fixed with
     flipping rule books, houses popping onto the drawn board, an envelope drifting down, and a sneaky look-around.
112. `ultimate/physics.py` = deterministic physics (every function is pure in t, so parallel/still renders agree):
     ball_path/draw_ball (gravity, restitution, spin, squash), cloth (Verlet napkin + ink in sheet uv), confetti
     (drag + 3D flip), spring_v/jiggle, dust. SFX "pop"s can be computed from ball_path impact times -> perfect sync.
113. Don't reuse `crowd_look()` for children: it gives powdered wigs and dresses (looked like grandparents). Use kid dicts.
114. Props must avoid faces: napkin over Leo's head, a heart on a mouth, a name card over the dad's face, trophies landing
     on players — all caught on stills. Measure label text (`Font.measureText`) and size the card around it.
115. A gavel must pivot at the hand end with the head striking the block (rotating around the head base looked wrong).
116. Draw the floor BEFORE the characters standing on it, or it cuts them in half (vote scene).
