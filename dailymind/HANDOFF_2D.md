# HANDOFF for the PC session: 10-second animated test in the polished 2D style

**STATUS 2026-11-13: DONE — the owner APPROVED this style and voice** (`cove_test/style2d_test.mp4`, QC ALL PASS).
Next: full 61-65 s Shorts in this style (see CLAUDE.md, "APPROVED HOUSE STYLE + VOICE").

The owner chose the 2D "Classic+ cartoon" look. Hero frame: `dailymind/ultimate/style2d_ultimate.py`.
Make a 10 s animated test, 1080x1920, 30 fps, at TOP quality. The owner's words: "the physics, music and voice should
be top, no glitches." They do not tolerate glitches, so check everything before showing them.
Read `CLAUDE.md`, `LESSONS.md` and `dailymind/HANDOFF_PC.md` (owner feedback) first.

## Script (keep it; the narration already exists)
"This chest is full of gold... and she's about to throw it into the sea. Because every single coin in it... is fake."
Existing take: `dailymind/cove_test/vo_final.wav` + `.times.json`. You may re-generate on the GPU (see Voice).

## Animation (build `dailymind/ultimate/make_style2d_test.py`)
### Rendering approach
- Render the static layers once (sky, sea, ship, pier, chest), as `style2d_ultimate.py` does.
- Draw per frame only what moves.
### Beats
- 0-2.9 s:
  - The camera pushes in slowly from wide.
  - Both characters breathe and blink.
  - She smirks. He leans toward the chest, eyes on the gold.
  - The gold glitters (sparkles twinkle in and out, never on her face).
  - The sea glitter shimmers, the clouds drift a few px, the lantern flickers.
- "throw it into the sea":
  - His head snaps to her, eyes go wide, hands fly to his cheeks. Ease over 5-7 frames, never a 1-frame jump.
  - She raises the coin.
- "Because every coin in it": she flips the coin.
- "...is fake":
  - She catches the coin and raises one brow; the smirk grows.
  - His jaw drops further.
  - Optional comic punch on this word: a quick halftone flash or a burst. See `style2d_comic.py`.
- Title: slams in on its spoken word in the channel's classic style. No caption boxes.
### Camera
- One continuous eased move (Catmull-Rom plus smoothing).
- Render at about 1.25x and crop, so the push-in never softens the image.
- No shake except a 2-3 frame micro-shake on "fake", if it helps.

## Physics (must be real and verified)
### Coin flip
- Ballistic arc, gravity 9.81 m/s².
- Set the pixel scale from her height: about 1.6 m is her full height in pixels.
- Solve the launch velocity so the coin lands EXACTLY in her hand at the catch frame. Print the catch error; it must be under 1 px.
- Spin is a real rotation: draw the coin as an ellipse with width |cos θ|, show its edge when edge-on, and give a highlight flash when face-on.
- The arc goes to her side, never across her face. The cloud test had exactly that glitch.
### Spilled coins
- If any coin moves, it bounces with restitution of about 0.3 and settles. No coin may hover or sink into the planks.
### Secondary motion
- Hair, coat hem and rope sway use damped springs (`toon.spring`), never raw sine snaps.

## Voice (top quality, free)
- Chatterbox on the GPU: `pip install chatterbox-tts`. Script: `dailymind/tts/chatter.py`.
- Settings: exaggeration about 0.7, cfg about 0.3.
- Generate 3 takes per line (different seeds).
- Transcribe each take with faster-whisper (GPU). Keep a take only if it matches the script word for word, with no artefacts or breaths that sound wrong.
- Keep "is fake" inside a full sentence; very short lines produce artefacts. Insert the dramatic pause in post.
- Do NOT clone vidIQ's "Chris" voice.

## Music and sound (top quality, not synthesized beeps)
- Music: a real, royalty-free track that is safe for monetized YouTube.
  - Best: the YouTube Audio Library. The owner can download one: "playful / mysterious pirate / adventure", about 90-110 bpm.
  - Or Pixabay Music.
  - Or generate one with an open model that allows commercial use. Check the licence first; MusicGen is non-commercial, so don't use it.
  - Write down the source and licence in the commit.
- SFX: real recordings, CC0 (Kenney audio packs, Freesound CC0, Pixabay SFX):
  - coin flick + spin + catch clink
  - his gasp
  - gentle sea waves + gulls as an ambience bed
  - a creak of wood
  - a sparkle shimmer on the gold
- Mix:
  - voice on top, music ducked under the voice (sidechain)
  - master to -14 LUFS (two-pass loudnorm, then alimiter + loudnorm if needed: see `make_mini.py`), true peak -1.5 dBTP

## QC before showing the owner (all must pass)
- Frames: a 10 fps contact sheet of every beat, plus a frame-by-frame check around the snap, the flip and the catch. Look for:
  - pops or 1-frame jumps
  - text overlapping text or faces
  - props through bodies
  - coins hovering
  - anything off-frame that should be on
- Physics: print the coin catch error (under 1 px) and the apex height (plausible: about 0.3-0.6 m).
- Audio:
  - loudness -14 ±0.5 LUFS, no clipping
  - the whisper transcript of the final mix matches the script
  - every SFX lands on its frame (±1 frame)
- Deliver `dailymind/cove_test/style2d_test.mp4` and push to `claude/new-session-ati950`. Tell the owner what you checked.
- Add a lesson to LESSONS.md.
