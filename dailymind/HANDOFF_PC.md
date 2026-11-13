# Handoff: continue the full-3D style tests on the RTX 4050 PC

The owner wants fast iterations: 10-second test clips, repeated until they say "this style and this voice".

## Where we are
- Style chosen: film-quality 3D characters acting in a real 3D set.
  - Characters: Blender Studio rigs Rain + Snow, CC-BY. Credit line in every description: "Rain & Snow rigs © Blender Foundation | studio.blender.org".
  - Set: Poly Haven assets.
  - Code:
    - `dailymind/blender/cove_style.py`: the set, cast and lights.
    - `dailymind/blender/cove_anim.py`: the 10 s animation, coin-flip physics, camera, and GPU auto-select (OPTIX, else CUDA).
- Rig control notes are in `dailymind/studio/REFERENCE_RICKS_CLIPS.md` (bottom section).
- Voice: free Chatterbox (MIT). Script: `dailymind/tts/chatter.py`.
  - Test narration: `dailymind/cove_test/vo_final.wav` plus `.times.json`.
  - Install on the PC: `pip install chatterbox-tts`. On a GPU it is about 10× faster.
- Finishing (voice, music, SFX, -14 LUFS, CRF 16): `dailymind/ultimate/make_cove_test.py FRAMES_DIR OUT.mp4`.

## Render the current test on the GPU
```
git pull
cd dailymind/blender
blender -b -P cove_anim.py -- ../cove_test/frames 100 64
cd ../ultimate
python make_cove_test.py ../cove_test/frames ../cove_test/cove_test.mp4
```
- The log must print "GPU OPTIX" or "GPU CUDA".
- The first run downloads the rigs (about 300 MB) and Poly Haven assets into `dailymind/assets_cache`.

## Rules
- Read `CLAUDE.md` and `LESSONS.md`.
- No glitches: check frames at every beat before delivering.
- Commit and push to `claude/new-session-ati950`.

## What the owner said in the cloud session (it's not in any other file)
- Rejected:
  - 2D toon characters pasted over 3D. "Characters look bad, 2D on 3D doesn't fit, background is wrong, captions/text."
  - Code-built 3D characters, which looked like wooden toys.
  - The miniature-town/giant-watch look as the main style. It "felt empty": too few, too small people.
- Wants:
  - full 3D, film-quality characters with readable, acting faces, in a rich, full set
  - smooth camera, real physics, zero glitches
  - fast iteration
- Reference channel: Ricks Clips, "How Mine Salting Worked". Breakdown in `dailymind/studio/REFERENCE_RICKS_CLIPS.md`.
  Takeaways: one story with a twist, characters big in frame with expressive faces, a new framing every 1.5-2 s, present-tense casual narration.
- Captions: the owner disliked the one-word caption mock. Ask before adding any text style, and propose one in the next test.
- Voice:
  - wants free and better than vidIQ. Chatterbox chosen (MIT).
  - Do NOT clone vidIQ's "Chris" voice.
  - Current settings: exaggeration 0.7, cfg 0.3. Short lines (e.g. "is fake.") produce artifacts, so keep the twist inside a full sentence and insert the pause in post.
- Test clip script: "This chest is full of gold... and she's about to throw it into the sea. Because every single coin in it... is fake."
- Bone axis gotcha: Snow's FK-UpperArm Z sign is opposite to Rain's. Snow's FK-Head Y is positive when turning toward Rain.
- A cloud render (40 % res, 10 samples) of this same clip was in progress as a fallback.

## Speed for test iterations (the owner wants fast)
- Cycles at 100 % / 64 samples takes about 75 min for 10 s on the RTX 4050. Too slow for tests.
- For TESTS use EEVEE with env `DM_ENGINE=EEVEE`, e.g. 64 samples at 100 %. Expect a few minutes.
  - PowerShell: `$env:DM_ENGINE="EEVEE"; blender -b -P cove_anim.py -- ../cove_test/frames 100 64`
- Keep Cycles for the approved final only, or use Cycles at 50 % / 24 samples (about 4x faster).

## Fixed after the cloud test (pull before rendering)
- The flipped coin crossed her face and showed as a flat white disc.
  - Her coin hand is now at chest height.
  - The flip arcs out to her side.
  - The gold is less mirror-like.
- Still to watch: the coin in flight reads pale against the bright sky. Check the 10 fps frames of the toss.
