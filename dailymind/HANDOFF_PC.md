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
