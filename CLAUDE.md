# The DailyMind. — YouTube Shorts toolkit (read this first)

Owner: makes YouTube Shorts for the channel **The DailyMind.** (@thedailymind0, formerly "Cronos File").
Format: surprising history of everyday things, English, natural male narrator.

## Owner's rules (non-negotiable)
- Length **61–65 s**. Ends with "Learned something new? Like and subscribe" (animated LIKE + SUBSCRIBE).
- **No glitches** — check frames before delivering (qa.py + zoomed stills at every slam/stamp/transition).
- **Improve every video** in every aspect; add a lesson to LESSONS.md after each video (read it first!).
- Hook must stop the scroll in the first 2 s (claim from frame 0, key word slams in on the spoken word, open loop).
- Preferred look: **classic ketchup-video style** — dark scenes, title + subtitle (subtitle appears on its
  spoken words), slams/stamps, gold splat transitions, vignette, dust, NO caption boxes, music + SFX, -14 LUFS.
- Full HD 1080x1920, export with `base.CRF = 16`.
- Always give ready-to-post title, description, tags.

## APPROVED HOUSE STYLE + VOICE (owner approved 2026-11-13) — use this for every new video
- **Style: 2D "Classic+ cartoon"** — hero frame `ultimate/style2d_ultimate.py`, animated by `ultimate/make_style2d_test.py`
  (static layers once at 1.25x, the push-in is a crop; cel shade + rim light + cast shadows; bloom, grade, vignette, grain;
  title slams on its spoken word, no caption boxes). Reference result: `cove_test/style2d_test.mp4`.
- **Voice: Chatterbox (free, MIT) on the PC GPU**, exaggeration 0.7 / cfg 0.3, best of 3 takes per line verified by
  faster-whisper: `tts/chatter_takes.py lines.json out.wav 3 0.7 0.3` (venv `C:/Users/AliFM/tts_env`). Word timestamps drive
  every animation cue and SFX. Do NOT clone vidIQ's "Chris".
- **Voice update (owner, 2026-11-15): use the vidIQ "Chris" voice while vidIQ credits last** (vidIQ account alividiq99,
  150 credits/month, resets on the 15th). Cost: 28 credits per 1,000 characters, ROUNDED UP PER CALL/LINE -> keep each
  script <= 1,000 chars and send it as ONE `script` (never `scriptLines`: each line rounds up on its own). ~5 videos/month.
  Re-takes cost again. When credits run out, fall back to free Chatterbox (above).
- **Sound:** real CC0 foley (`cove_test/sfx/`, BigSoundBank) placed on frames, `ultimate/make_style2d_audio.py`
  (mastered + verified on the encoded MP4). Music optional (the approved test had none).
- **QC:** `ultimate/qc_style2d.py` must print ALL PASS, then look at its sheets/strips. Physics is solved and asserted in code.
- Superseded: the 3D Rain/Snow cove test and the miniature-universe look were NOT chosen.

## Three production styles (all built)
1. **Code-drawn Skia toon** (latest, owner asked for it): `ultimate/toon.py` (characters, props) +
   `ultimate/make_toon.py` (12 scenes) + `ultimate/ultimate.py` (stage, mascot pineapple, coins physics, bloom).
2. **Gemini illustrations animated**: owner makes ~10 images in Gemini (9:16, no text, dark empty top third,
   same style block + identical character descriptions in every prompt, NEW Gemini chat). `pineapple/make_pineapple.py`
   (camera, lights, particles) + `pineapple/motion.py` (puppet mesh-warp character motion).
3. Older PIL code-drawn videos: make_*.py (make_fork_classic.py = classic template).

## Pipeline
- Script ~1,000 chars → voice. vidIQ voice "Chris" (voiceId iP95p4xoKVk53GoZ742B, 14 credits / 1000 chars) when
  credits exist; otherwise free offline **Kokoro** (`tts/say.py script.txt am_michael 1.16 voice.wav`, writes
  paragraph timings to voice.wav.paras.json). Kokoro model files: download from
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/{kokoro-v1.0.onnx,voices-v1.0.bin}
  into tts/. Then: highpass + light compressor → voice.mp3.
- `timing.Timeline(voice)` (pocketsphinx) for word cues; scene cuts from paragraph timings.
- `audio.music / sfx / master` (two-pass loudnorm to -14 LUFS).
- `qa.py final.mp4 "durations" voice.mp3` → must be ALL PASS; then review qa_sheet.png and zoomed stills.
- Python deps: pillow numpy pocketsphinx opencv-python-headless skia-python (needs `apt-get install libegl1`)
  kokoro-onnx soundfile. Fonts: Inter (fonts/ folder; make_short.py expects /usr/share/fonts/opentype/inter/).

## Videos made so far
cooking, bread, tea, ice cream, salt, coffee, pizza, chocolate, ketchup, carrot, honey, lobster, potato,
nutmeg, popcorn, banana, toothpaste, fork, pineapple (Gemini version + code-drawn Skia version + Chris re-voice),
chewing gum (Skia toon, `ultimate/make_gum.py`), ice / Frederic Tudor (Skia toon, `ultimate/make_ice.py`), chess / the queen (Skia toon, `ultimate/make_chess.py`), Coca-Cola as medicine (Skia toon, `ultimate/make_cola.py`), bubble wrap as wallpaper (Skia toon, `ultimate/make_bubble.py`), purple / snail dye / Perkin (Skia toon + CTA v2, `ultimate/make_purple.py`), Monopoly / Lizzie Magie (Skia toon + CTA v2, `ultimate/make_monopoly.py`), Messi vs Ronaldo childhood facts (Skia toon + `physics.py`, `ultimate/make_goat.py`), Mona Lisa theft 1911 (Skia toon + physics, `ultimate/make_mona.py`), airplane windows / Comet (REAL 3D: Blender plates `blender/window3d.py` + `ultimate/make_window3d.py`; old fake-3D `make_window.py`), Leaning Tower of Pisa (REAL 3D v2: 3D toons `blender/toon3d.py` + Bullet physics `blender/pisa3d.py` + `ultimate/make_pisa3d.py`), Eiffel Tower / a radio saved it (MINIATURE CINEMATIC UNIVERSE — earlier style, superseded: `blender/eiffel_mini.py` + figurine.py + town_kit.py + dm_assets.py, `ultimate/make_eiffel_mini.py`).
END CARD: use `ultimate/cta2.py` (draw_cta2) for every new video — the owner did not like the old one.
LONG-FORM (16:9, 10 min): "What If You Got $1 Every Time Someone Thought About You?" (`ultimate/make_thoughts.py` + `long_engine.py`).
Canary in the coal mine; Great Molasses Flood v2; chip can / Fred Baur buried in his can (FINAL = all-2D fortune-cookie style, `ultimate/make_pringles.py`, audio `make_pringles_audio.py`, QC `qc_pringles.py`).
What If Everything Was Free? (what-if explainer, fortune 2D style, `ultimate/make_free.py`, audio `make_free_audio.py`, QC `qc_free.py`).
What If the Internet Shut Down for a Day? (what-if #2, fortune 2D style, `ultimate/make_offline.py`, audio `make_offline_audio.py`, QC `qc_offline.py`).
What If Everyone Stopped Sleeping? (what-if #3, fortune 2D style, `ultimate/make_sleep.py`, audio `make_sleep_audio.py`, QC `qc_sleep.py`).
OWNER PREFERS THE FORTUNE-COOKIE 2D STYLE (2026-11-16): use `make_fortune.py` / `make_pringles.py` as the template for new videos.
Fortune cookies are Japanese (APPROVED 2D style, `ultimate/make_fortune.py` + `make_fortune_audio.py`, QC `qc_fortune.py`).
Don't repeat topics.
