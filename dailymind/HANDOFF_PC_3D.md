# HANDOFF for the PC session (RTX 4050): the canary style, now with REAL 3D camera moves

You are running on the owner's laptop. Read `CLAUDE.md` and `dailymind/LESSONS.md` first (all rules apply: 61–65 s, hook in the
first 2 s, no glitches, −14 LUFS, 1080x1920, LIKE + SUBSCRIBE end card via `ultimate/cta2.py`, title/description/tags as
separate copy-boxes with one box per tag).

## The approved look (keep it)
- The look is the **canary / molasses v2 style**: the channel's 2D toon characters (`ultimate/toon.py`) inside real, lit
  3D Blender sets, with the approved 2D engine finish (`ultimate/style2d_engine.py`: cel shade, rim light, cast shadows,
  bloom, grade, vignette, grain).
- Text: title slams + rubber stamps on their spoken words, and gold-splat transitions. No caption boxes.
- References:
  - `ultimate/make_canary.py`: `canary/canary_upload.mp4`.
  - `ultimate/make_molasses2.py` + `blender/boston_plates.py`: `molasses2/molasses2_upload.mp4`.
- The owner rejected:
  - 2D-only
  - the Three.js page look
  - miniature towns
  - 3D Rain/Snow rigs
  - stickmen

## What the GPU must add (why we moved to the PC)
The cloud had no GPU, so each 3D set was ONE still image. That meant the camera could only crop or zoom, and the
molasses, sea and burst were frozen. On the PC, do better:

1. **Render every frame in Blender** (EEVEE on the RTX 4050, or Cycles for hero shots). Keyframe a real camera:
   - orbits of 15–45°, dolly push-ins, low angles, crane reveals
   - one continuous eased move per shot (Catmull-Rom plus smoothing; see `blender/mini3d.py` `catmull` / `smooth_seq`)
   - shake only on impacts
2. **Animate the world in 3D**: waves, liquids, bursting objects, rolling things. Use real physics (Bullet rigid bodies
   or solved ballistic arcs), asserted in code: things rest exactly on the floor, never hover, never sink.
3. **Keep the toon characters 2D, but track them to the 3D camera:**
   - Export each character's 3D foot position.
   - Project it per frame (`bpy_extras.object_utils.world_to_camera_view`) to get screen x/y and scale.
   - Composite the toon there, plus the cast shadow from `E.light_char`.
   - Never draw the character at a fixed screen spot when the camera moves.
4. Render passes as PNG (or JPG q96: about 3 MB per PNG frame) into `<video>/plates_anim/%04d`. The compositor reads the
   frame that matches each video frame.

## Voice
- vidIQ "Chris" (voiceId `iP95p4xoKVk53GoZ742B`) while credits last. Account alividiq99: about 122 credits left; it
  resets on the 15th.
- Cost is **28 credits per 1,000 characters, rounded up per call**:
  - Keep the whole script **≤ 1,000 characters**.
  - Send it as ONE `script` (never `scriptLines`).
  - Each video costs about 28 credits.
- Get word timings with faster-whisper (see `molasses2/chris_timing.py`), and verify the transcript. Whisper hears
  Chris's "Learned" as "learn": that's OK.
- If credits run out: use free Chatterbox (`tts/chatter_takes.py`, best of 3 takes).

## Workflow (the owner wants fewer rebuilds)
1. Propose a topic. It must be a true story with a person and a twist, about the surprising history of an everyday
   thing, and not already in the "Videos made so far" list.
2. Write the script (≤ 1,000 chars) and a scene list. **Get the owner's OK.**
3. Render ONE hero still of the first shot. **Get the owner's OK on the look.**
4. Then make the voice and build every scene. Render the full video on the GPU.
5. Mix with real CC0 foley (`cove_test/sfx`) and master to −14 LUFS (see `ultimate/make_molasses2_audio.py`).
6. QC: adapt `ultimate/qc_molasses2.py`. It must print ALL PASS. Then look at every contact sheet and cut strip yourself.
   The QC misses things the eye catches: objects in the lens, a button before its card, text over faces.
7. Deliver:
   - a phone copy (720p, ≤ 15 MB)
   - an upload copy (≤ 100 MB for GitHub)
   - a thumbnail, built from a subtitle-free render
   - title / description / tags
8. Add a lesson to LESSONS.md. Commit and push to `claude/new-session-ati950`.
