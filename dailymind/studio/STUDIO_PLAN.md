# The DailyMind Studio — analysis, creative direction and implementation plan

Status: **proposal + three sample productions** (nothing existing was removed or rewritten).
Approval checkpoints: ① this plan + the three samples → choose a direction; ② per video: script; ③ storyboard;
④ final video.

---

## 1. What we already have (inspection)

| Layer | Existing, working | Keep / change |
|---|---|---|
| Research + script | Manual research, ~950-char scripts, LESSONS.md (138 lessons) | Keep. Add a fact sheet with sources per video (§6). |
| Voice | vidIQ "Chris" (28 credits / 1,000 chars), Kokoro offline fallback, `timing.Timeline` word cues | Keep. Credits are the bottleneck (10 left until Dec 8). |
| 2D engines | PIL classic, Skia toon (`ultimate/`), Gemini-image animation | Keep for 2D cards (follow card, CTA v2). |
| 3D engine | Blender (`blender/toon3d.py` toons, `pisa3d.py` / `eiffel3d.py` scene builders): Bullet rigid bodies, volumetric dust, smoothed poses, smoothed cameras | **Becomes the core of the studio.** Factor the shared engine into `blender/engine3d.py`; scene builders stay per video. |
| Rendering | Cloud = previews only (no GPU, ~2 min/frame). Owner's RTX 4050 = finals (EEVEE ~1 s/frame) | Keep. Every video = cloud previews + one PC render pass. |
| Compositing | `make_short.base`: classic text layer, slams/stamps, gold splats, bloom/vignette/grain, CTA v2, `audio.music/sfx/master` (-14 LUFS) | Keep. It is the brand layer. |
| QC | `qa.py` (length, hook speed, pauses, loudness, black gaps, frame-0) + manual half-second contact sheets | Extend (§7). |

Honest weaknesses today:
- **Every video uses the same trick.** That's either flat 3D toons, or a 3D world with text on top.
- **No signature "Hidden Worlds" idea yet.** We tell the story *about* an object, but never show the world *inside* it.
- **Characters are cute but generic** (bean bodies). No recurring host or motif makes the channel recognizable.
- **QC catches technical faults, not weak storytelling.** For example, a 5-second stretch with no new information still passes.

## 2. Technology choice

| Option | Quality | Consistency | Render time | Cost | Verdict |
|---|---|---|---|---|---|
| **Blender + Python (current)** | Real lighting, DOF, motion blur, volumetrics, physics | Total (it's code) | ~30-40 min per Short on the RTX 4050 | Free | **Core.** |
| Three.js / React Three Fiber | Good real-time look, weaker GI/DOF/volumes | Total | Fast | Free | Not better than Blender for offline video; would duplicate the engine. Useful later for interactive web teasers only. |
| Remotion | Great for typography/data overlays | Total | Fast | Free/licensed | Our Python compositor already does this job; not worth a rewrite. |
| AI video generation | Pretty single shots | **Poor**: characters drift, facts can't be controlled, looks like every other AI channel | Fast | Credits | Not for core shots. Possible later for textures/skies only. |
| AI images (Gemini) | Good stills | Medium | — | Free | Keep as optional texture/painting source (style 2 still works). |
| AI voice (Chris) | Natural | Same voice every time | — | 28 credits / Short | Keep; Kokoro fallback. |

Decision: **Blender (3D) + Python compositor (brand layer) + Chris voice.** No new frameworks.

## 3. Creative direction: "Hidden Worlds"

> *Every ordinary object hides an extraordinary world.*

The DailyMind signature is a **scale journey**:
1. The story opens on a **real-scale everyday object**.
2. The camera finds a way **into** it, through a seam, a grille, a dial or a crack.
3. Inside is a **living miniature world of the past**.
4. The story ends by **pulling back out** to the object, now seen differently: the payoff.

Recognizable brand motifs (used lightly, never forced):
- **The Gold Seam.** A thin line of molten gold light marks every passage between worlds and eras. It's the brand's black-and-gold, used as light.
- **Macro and miniature optics.** Shallow DOF, tilt-shift blur at the frame edges, high camera angles on miniatures, and warm "desk lamp" pools of light in the present.
- **Era palettes.** Every era gets its own colours; the present is dark with gold. For example: 1889 is sepia and amber gaslight, WWI is cold blue with searchlights.
- **One recurring guide character.** A tiny brass-and-black **"Curio" figure**: a pocket-watch-sized explorer, never human-realistic. Curio can appear in any era, which keeps continuity without repeating people. It's optional per video.
- **Classic text layer**, as the owner prefers: title, subtitle on the spoken word, slams, stamps, gold splat transitions.

Techniques library (pick 2-3 per topic; never the same set twice in a row):
- The object opens into a miniature world.
- The camera flies through the object's internal structure.
- A Time Seam wipes one era into another.
- An exploded-view blueprint assembles into the real thing.
- Scale shock: a real coin lands next to a 1 cm crowd.
- An animated 3D timeline ruler.
- A before/after slice.
- A one-take crane through history.

## 4. Retention system (applied to every script and storyboard)

Research sources: see the end of this file. Treat vendor numbers as guidance, not law.
- **0-2 s:** a visual *event*, not a setup. Something moves, breaks or transforms on frame 0, and the claim is on screen from frame 0. The key word slams in on the spoken word. Open loop: "…and a radio saved it."
- **Every 3-5 s:** a new visual idea. That means a new shot, a new scale, a new era or a new reveal. A camera move alone doesn't count. The QC "novelty timeline" flags gaps (§7).
- **Every 10-15 s:** a mini-payoff that answers a small question and opens the next one. "Only 20 years… so how did it survive?"
- **Show, don't narrate.** Each spoken fact gets a visual demonstration: the permit unrolls, the antenna rises, the message is caught.
- **Ending:** answer the main question in the final 10 s, plus one extra fact. For example, it became the most visited paid monument. Pull back out of the hidden world, then the CTA.
- **Never:** fabricated facts, misleading hooks, logo intros, greetings or filler.

## 5. Production workflow (with approval checkpoints)

1. Research. Build a fact sheet: every claim gets a source. Disputed claims get softened or cut.
2. Choose the angle: famous subject + unknown twist (our best performers: chess, Mona Lisa, Pisa).
3. **Script** (~950 chars, natural Chris read) → **CHECKPOINT ②**.
4. Generate the voice. Get word cues with `timing.Timeline`. Cut scenes at pauses.
5. **Storyboard:** one line per scene with technique, scale, era, palette, camera move and "new thing shown". Then render cloud preview stills (4 per scene) → **CHECKPOINT ③**.
6. Build: scene builder for the video on `engine3d`, characters from `toon3d` presets, physics, smoothed cameras.
7. PC render (one paste, ~30-40 min).
8. Composite: brand layer, music, SFX, -14 LUFS.
9. QC (§7) + half-second frame review. Fix, re-render only what changed.
10. **Final video + post text** → **CHECKPOINT ④**. Add a lesson to LESSONS.md.

## 6. Character and world consistency

- `toon3d.py` gets **named presets** (a cast file): Gustave, Curio, soldier, worker, tourist sets.
  - Each preset fixes face, colours, hat, scale and outline.
  - Scenes reference presets by name, so nobody changes appearance between scenes.
- Era palettes and lighting rigs become presets (`present_desk`, `gaslight_1889`, `wwi_night`, `golden_hour`).
- Camera presets: `macro_dive`, `miniature_high`, `crane_reveal`, `orbit_reveal`, `one_take_seam`.
  - All of them go through the zero-lag path smoother, so there are no jerks.

## 7. Automated quality control (extensions to qa.py)

The current checks stay. These are added:
- **Novelty timeline.** Per 0.5 s, measure frame-to-frame visual change and title changes. Flag any stretch over 4 s without a new shot, scale or reveal ("weak scene").
- **Motion smoothness.** Per-frame optical-flow magnitude on the plates. Flag sudden spikes (camera jerks, pose snaps) outside planned impact moments.
- **Character consistency.** Compare the colour histograms of each character crop between scenes. *Planned; needs character masks from Blender's object-index pass.*
- **Readability.** Measure text widths before rendering (slam ≤ 940 px) and contrast of text against the plate under it.
- **Audio sync.** Every slam/stamp cue sits within ±0.1 s of its word. Loudness -14 LUFS.
- **Facts.** The fact sheet must list a source for every on-screen claim, or the build stops.
- **Repetition.** Compare the techniques used against the last 3 videos and warn when they repeat.
- **Report.** QC writes a report that marks scenes PASS / WEAK with a suggested fix. Nothing is auto-approved.

## 8. Formats

- Shorts 9:16 1080x1920 now. The engine renders any resolution, so 16:9 long-form only needs storyboards with wider framing.
- `long_engine.py` already handles 16:9 2D. The 3D plates plug into the same compositor.

## 9. Competitive analysis (niche: origins of everyday things / history Shorts)

Common strengths in the niche:
- Instant claim hooks.
- Fast cuts.
- Stock footage or AI images with captions.
- Strong curiosity titles.

Common weaknesses:
- Interchangeable visuals: stock clips, AI slideshows, the same caption template.
- Visuals that **illustrate** words instead of **demonstrating** them.
- Generic AI characters that change from shot to shot.
- No recognizable world.

Our opportunity: *demonstration through a hidden world*. Every fact becomes a physical event in a miniature world. Consistent, toy-like original characters, real physics and cinematic light. That's very hard to copy with stock footage or AI slideshows.

## 10. The three sample productions (same topic, fair comparison)

All three use the **same 31-second Chris narration** (six sentences cut at natural pauses from the existing Eiffel voice; no new credits) and the same brand layer. Only the visual approach differs:

| | A — "Object Portal" | B — "Living Blueprint" | C — "Time Seam" |
|---|---|---|---|
| Idea | A souvenir tower + old radio on a desk. The camera dives through the radio grille into a living miniature 1889-1914 Paris, then pulls back out at the end. | The story drawn and built as glowing gold engineering lines on a navy drafting table: exploded views, a 3D timeline ruler, wave diagrams. | One continuous camera move through a single place while a molten-gold seam wipes the eras (1909 → 1889 → 1909 → 1914 → today) around it. |
| Hidden-Worlds fit | Strongest (literal) | Medium (inside the *design*) | Strong (inside *time*) |
| Risk | Scale cues must read instantly | Can feel like a diagram if too abstract | Seam must look clean, not glitchy |

Files: `blender/samples_eiffel.py`, `ultimate/make_samples.py`, outputs in `samples/`.

## Sources (research)
- Retention / hooks (vendor guidance, unverified numbers):
  - gofaceless.ai, YouTube Shorts retention strategy
  - fluxnote.io, retention tips 2026
  - opus.pro, Shorts length & hook formulas
  - dev.to, Hook engineering 2026
  - vidiq.com, More views on Shorts 2026
- Miniature / tilt-shift language:
  - Wikipedia, Miniature faking
  - Maxon, "Toying with iconic cinema moments"
- Facts:
  - toureiffel.paris: how radio saved the tower; the Eiffel Tower laboratory
  - ASME Landmark #237, Eiffel drop-test machine (1903, cable from the 2nd level)
  - history.com: 10 things about the Eiffel Tower; Mata Hari (Jan 1917 intercepted H-21 messages)
  - cheminsdememoire.gouv.fr: Gustave Ferrié
