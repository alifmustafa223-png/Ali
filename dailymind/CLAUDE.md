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
chewing gum (Skia toon, `ultimate/make_gum.py`), ice / Frederic Tudor (Skia toon, `ultimate/make_ice.py`), chess / the queen (Skia toon, `ultimate/make_chess.py`), Coca-Cola as medicine (Skia toon, `ultimate/make_cola.py`), bubble wrap as wallpaper (Skia toon, `ultimate/make_bubble.py`), purple / snail dye / Perkin (Skia toon + CTA v2, `ultimate/make_purple.py`), Monopoly / Lizzie Magie (Skia toon + CTA v2, `ultimate/make_monopoly.py`).
END CARD: use `ultimate/cta2.py` (draw_cta2) for every new video — the owner did not like the old one.
LONG-FORM (16:9, 10 min): "What If You Got $1 Every Time Someone Thought About You?" (`ultimate/make_thoughts.py` + `long_engine.py`).
Don't repeat topics.
