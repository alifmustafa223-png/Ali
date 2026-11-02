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
