# Miniature Cinematic Universe + Surreal Macro 3D — sample evaluation

Status (honest):
- **Built and working:**
  - asset library (`blender/dm_assets.py`)
  - figurine characters (`blender/figurine.py`)
  - three sample builders (`blender/mini3d.py` S1/S2/S3)
  - preview stills verified in the cloud
- **Not done yet:** the three 12 s full-HD MP4s. They render on the RTX PC (see `RENDER_ON_PC.md`). Nothing below
  claims a final-video result until those MP4s exist and have been reviewed frame by frame.

## What was built

| Module | What it does | Verified |
|---|---|---|
| `dm_assets.py` | Downloads and caches Poly Haven CC0 models (with their textures), PBR textures (box-projected, tintable) and HDRIs. Parallel-safe. | Yes: pocket watch, radio, street lamps, wrench, drill, candleholders, crates, pipes, industrial lamps; 12 texture sets; 4 HDRIs. |
| `figurine.py` | Hand-painted miniature figures at true 1:100 scale (1.75 cm), with realistic proportions, matte acrylic paint with colour noise and painted faces. Hats: cap, top hat, bowler, helmet; plus apron and long coat. Actions: walk, carry, hammer, lever, point, wave, look; all channels zero-lag smoothed. | Yes, macro test render. |
| `mini3d.py` | Three 12 s samples built at true miniature scale, so depth of field is real macro optics. Includes a smoothed macro camera with rack focus, volumetric steam, spark bursts, lattice generator, gear generator, procedural houses. | Preview stills only. |

## The three samples

1. **S1, a miniature historical world: 1889 Paris building site on a workbench.**
   - The camera dollies at figure height past workers carrying a girder, a riveter throws sparks, and a steam crane lifts iron.
   - It rises to reveal the half-built tower, and that the whole world is a model beside a giant wrench and candleholder.
2. **S2, a surreal giant everyday object: a real pocket watch standing in a 1:100 town square.**
   - Townsfolk stroll, a child points, and a cleaner on a ladder polishes the glass.
   - Then the hands spin and the sky falls from golden hour to night while every window lights up.
3. **S3, a cinematic miniature industrial world: a tiny factory.**
   - A conveyor carries crates under a stamping press (sparks and steam on each hit), and gears and pistons turn.
   - Workers pull a lever, push a cart and weld; hanging lamps sway.

## Evaluation from preview stills (25 % resolution, 16 samples, no motion blur)

| | Visual quality | Originality | Render cost (cloud, per 25 % frame) | Feasibility |
|---|---|---|---|---|
| S2 Giant watch | **Highest.** Real engraved watch model, convincing miniature town at night, strong surreal image. | **High.** "Everyday object as a monument in a tiny world" is a recognizable, repeatable signature. | 15-50 s | High: one hero asset + a reusable town kit. |
| S1 1889 diorama | Good in the wide reveal (model on a workbench with giant tools). Opening shots needed focus and material fixes (done, not yet re-verified). | High: history as a living diorama. | 50-70 s | Medium: every topic needs a new period set. |
| S3 Factory | Weakest. Machines read as simple blocks. Lighting fixed after the first pass (it was black). | Medium: factories are common in miniature content. | 17-20 s | Medium-high, but needs much more modelled machinery to look rich. |

Render performance:
- **Cloud:** no GPU. Full HD is impractical (days).
- **RTX 4050:** EEVEE estimate is 1-3 s per full-HD frame for these scenes, so about 10-15 min per 12 s sample. To be measured on the PC run.

## Remotion evaluation (tested here, not assumed)

- Installed Remotion 4.0.250 with React 18 and rendered a 1080x1920, 60-frame composition (spring-animated title over a miniature plate) **in 7 s** using the pre-installed headless Chromium.
- **Strengths:**
  - Much faster and more flexible typography and motion design than our PIL/Skia text layer: CSS, web fonts, springs.
  - Live preview in the browser.
  - Easy reusable caption and transition components.
- **Costs:**
  - The brand layer has to be ported: slams, stamps, gold splats, CTA v2 and audio mixing.
  - It adds a Node toolchain.
  - License: free for individuals and small teams (up to 3 people), otherwise a company license.
- **Recommendation:**
  - Adopt Remotion for **composition only**: titles, subtitles, transitions, end card.
  - Port the brand look once, keep `audio.py` for the -14 LUFS master, and keep Blender for all 3D.
  - Don't switch until the brand layer port is pixel-checked against the current style.

## Recommendation (provisional, pending the PC renders)

**Lead with S2's idea: "the everyday object as a giant in a miniature world".** It matches the channel's promise (where everyday things came from) and gives every video a hero object. That object is both the topic and the portal. Use S1's living historical dioramas for the "how it began" beats. Keep S3's machinery only for topics about manufacturing.

## Must improve before building the full production system

1. **Figurines.** More expressive acting: weight shifts, hand props attached to hands, and two to three reusable walk styles. Add an optional face close-up variant for hero shots.
2. **Set richness.** More modelled period props per era (carts, signage, awnings, cobbled kerbs). Instanced scatter for small detail.
3. **Machinery kit (S3).** Proper modelled presses, belts with moving texture and boilers. Blocks read as placeholders.
4. **Camera language.** Reusable presets (macro dolly, rack focus, scale-reveal crane, orbit). Focus targets bound to subjects automatically.
5. **Lighting presets.** Workbench lamp, golden hour, night practicals, factory haze, each tested once at full quality on the PC.
6. **Audio for miniatures.** Small-world foley: ticking, tiny footsteps, rivets, steam. Plus music.
7. **QC.** Render one frame per second at full quality on the PC before the full render, and add the half-second sheet review to the final check.
