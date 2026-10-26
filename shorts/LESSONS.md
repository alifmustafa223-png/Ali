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
