# Cronos File — YouTube Shorts style guide (prompt for an AI coding agent)

Paste **Part 1** into Antigravity once (or keep this file in the project so it can read it),
then paste **Part 2** each time you want a new video.

---

## PART 1 — MASTER PROMPT (style, length, rules)

You are making YouTube Shorts for my channel **Cronos File (@CronosFile)**: the surprising
history of everyday things, in English, told like a friend telling a story. Every video must
look and sound exactly like the existing ones. **Do not invent a new style — reuse the code in
this folder.**

### The code you must use
This folder contains a working Python video engine. Read these files first:

- `make_short.py` — the engine. It renders 1080×1920 vertical video at 30 fps with Pillow and
  pipes frames into ffmpeg. It defines the shared helpers: `text_block` (centered text that
  slides up and fades in, with a soft shadow), `tag` (the rounded colored pill label at the top,
  e.g. "ABOUT 2,400 YEARS AGO"), `ease`, `gradient`, `font`, `person`, `draw_fire`, and `main()`
  (the render loop, background music, scene fades, progress bar).
- `make_icecream.py`, `make_coffee.py`, `make_salt.py`, `make_tea.py`, `make_bread.py` —
  finished videos. **Copy one of these as the template for every new video**
  (`make_coffee.py` is the newest and best). Each one imports `make_short as base`, draws its
  own illustrations with simple Pillow shapes, defines one function per scene, and sets
  `base.SCENES[:] = [(seconds, (top_rgb, bottom_rgb), scene_fn), ...]`.
- `make_salt.py` contains `draw_cta` — the animated 👍 LIKE + SUBSCRIBE + 🔔 ending.
  Reuse it via `make_salt.draw_cta(img, d, W / 2, 1250, t, off=...)`.
- `align.py voice.mp3` — prints word timings + pauses of the voiceover.
- `finish.py base.mp4 voice.mp3 final.mp4` — mixes the voice over the music.
- `fonts/` — Inter ExtraBold + Medium. Always use these (already wired in `make_short.py`).

Requirements: Python 3, `pip install pillow pocketsphinx`, and `ffmpeg` on PATH.

### Visual style (never change)
- Vertical 1080×1920, 30 fps, flat 2D vector illustrations made of simple shapes
  (no photos, no AI images, no realistic people, no copyrighted characters).
- Each scene: dark vertical gradient background, colored **tag pill** at y≈250,
  **title** (white, Inter ExtraBold, `F_BIG` at y≈430 or `F_MID` at y≈400),
  **subtitle** (`F_SMALL`, soft tinted color) below it, illustration in the lower half
  (y > ~900), gentle looping motion (steam, sparkles, bobbing, swaying, falling particles).
- The big key word of the hook is huge and colored (gold `(255,190,70)` / red `(230,40,50)`).
- Orange progress bar along the bottom (already in `main()`).
- Scenes are separated by a quick 0.2 s dip to black (already in `main()`).
- **The very first frame must already show the full hook text and picture** — no black
  intro, no empty first second (`HOOK_SKIP` in `make_short.py` does this; keep it).

### Length and structure
- **Total length 54–56 seconds.** Never over 60.
- 7–8 scenes:
  1. **Hook** (2–4 s): a shocking one-liner with one huge colored word
     ("Coffee was once ILLEGAL", "Ice cream is WAY OLDER than you think").
  2–6. **The story**, in time order, each scene with a date tag ("ABOUT 2,400 YEARS AGO",
     "YEMEN · 1400s", "1930", "TODAY"). One scene must be tagged **"THE CRAZY PART"** with the
     most surprising fact, ideally with a stamp/reveal animation landing exactly on the key word
     (see the BANNED / MYTH stamps).
  7. **Today**: how we use it now.
  8. **CTA ending** (about 5 s): "Learned something new?" + the animated LIKE and SUBSCRIBE
     from `make_salt.draw_cta`.

### Voiceover
- Voice: **"Chris – Charming, Down-to-Earth"** (ElevenLabs premade voice ID
  `iP95p4xoKVk53GoZ742B`; also available in vidIQ's voiceover tool). Same voice every video.
- Script: **780–850 characters** (this gives ~53–59 s; stay under 1,000 characters).
- Tone: casual, like telling a friend, NOT like reading. Use: "Okay, so...", "And get this...",
  "And here's the crazy part.", "And today?", short sentences, "..." for pauses, questions.
- Write numbers as words ("twenty-four hundred years ago", "fifteen eleven").
- Always end with: **"If you learned something new, hit like... and subscribe for more!"**
- Facts must be true. If something is a legend or disputed, say "the story goes" / "legend says".
- If the voice is longer than 56 s, speed it up slightly with ffmpeg `atempo` (max 1.10).

### Production steps (follow every time)
1. Write the script (780–850 chars). Show it to me for approval.
2. I generate the voice and save it as `voice.mp3` in this folder.
3. Run `python align.py voice.mp3`. Put every scene cut in the **middle of a pause** between
   sentences, so a scene always starts with its own sentence. Time stamps/reveals so they land
   on the exact spoken word (e.g. the stamp appears when the narrator says "banned").
4. Copy `make_coffee.py` to `make_<topic>.py`, change the drawings/text/colors per scene.
5. Render: `python make_<topic>.py base.mp4 "d1,d2,d3,..."` (the durations from step 3; the last
   scene ends ~1.2 s after the voice ends).
6. Mix: `python finish.py base.mp4 voice.mp3 final.mp4`.
7. **Glitch check before saying it's done** — extract frames with
   `ffmpeg -ss <sec> -i final.mp4 -frames:v 1 frame.png` at: frame 0, the middle of every
   scene, every stamp/reveal moment, and the ending. Look at each one and fix:
   - subtitle overlapping a title that wrapped to 2 lines (move the subtitle down to y≈640–760),
   - illustrations, steam or particles crossing text,
   - shapes drawn in a fixed color on top of a gradient (visible boxes),
   - anything cut off at the screen edges,
   - text that wraps awkwardly ("...was / once"),
   - a dark/empty first frame.
   Re-render until every checked frame is clean.

### Upload details to give me with every video
- Title: short, shocking, with emoji + `#shorts` (e.g. "Coffee Was Once ILLEGAL?! ☕ #shorts").
- Description: 2 short hook lines + a question for comments + 5 hashtags.
- Tags (comma separated) and which earlier video to set as "Related video".
- Which frame to use as the cover (always the hook frame).

---

## PART 2 — NEW VIDEO PROMPT (example: chocolate)

Make the next Cronos File Short following PART 1 exactly.

**Topic:** "Chocolate Was Once MONEY?!" 🍫

**Scenes (about 55 s total):**
1. **Hook:** "Chocolate was once used as MONEY" — "MONEY" huge in gold. Show a chocolate bar
   with a gold sparkle.
2. **ABOUT 3,000+ YEARS AGO · MESOAMERICA:** people in what is now Mexico and Central America
   first used cacao. Draw a cacao tree with big orange/red pods.
3. **A BITTER DRINK:** the Maya and Aztecs drank it bitter and spicy — with chili, no sugar.
   Draw a cup with frothy chocolate being poured from high up, chili peppers next to it.
4. **THE CRAZY PART:** the Aztecs used **cacao beans as money** — you could buy food with them.
   Animate beans dropping onto a market scale / stacking like coins; a gold "MONEY" stamp
   lands exactly when the narrator says "money".
5. **THE 1500s · EUROPE:** the Spanish brought cacao to Europe and added sugar; it became a
   luxury drink for the rich. Draw a fancy cup with a crown above it.
6. **1847:** the first modern chocolate bar was made in England (by J.S. Fry & Sons).
   Draw a chocolate bar being snapped, with pieces bouncing.
7. **TODAY:** chocolate is everywhere — a counter / falling bars.
8. **CTA ending** with the animated LIKE + SUBSCRIBE (`make_salt.draw_cta`).

**Draft script (~800 characters — check the length, keep it within 780–850):**

> Chocolate... was once used as money.
>
> Okay, so... more than three thousand years ago, people in what's now Mexico and Central
> America discovered the cacao tree.
>
> But they didn't eat chocolate bars. They drank it... bitter, foamy, and spicy, with chili!
> No sugar at all. Legend says the Aztec ruler Montezuma drank cups of it every single day.
>
> And here's the crazy part. The Aztecs valued cacao beans so much, they used them as money.
> You could actually buy food with them!
>
> Then in the fifteen hundreds, the Spanish brought cacao to Europe, added sugar... and it
> became a luxury drink for the rich.
>
> In eighteen forty-seven, a company in England made the first modern chocolate bar.
>
> And today? We eat millions of tons of it every year.
>
> If you learned something new, hit like... and subscribe for more!

**Upload details:**
- Title: `Chocolate Was Once MONEY?! 🍫 #shorts`
- Description:
  ```
  Before chocolate bars existed, people drank it bitter and spicy... and the Aztecs used cacao beans as MONEY 🍫

  The surprising 3,000-year story of chocolate.

  Would you rather have chocolate or money? 👇

  #chocolate #history #facts #didyouknow #shorts
  ```
- Tags: `chocolate history, cacao money, aztec chocolate, who invented chocolate, food history, shorts`
- Related video: the coffee Short. Cover: the hook frame.
