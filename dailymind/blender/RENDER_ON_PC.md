# Render the real-3D airplane video on the RTX PC

1. Install **Blender 4.2+** (free, blender.org) and **Git**. Update the NVIDIA driver.
2. `git clone https://github.com/alifmustafa223-png/Ali.git` and `git checkout claude/new-session-ati950`
3. In the `dailymind/blender` folder run (Windows, adjust the Blender path if needed):

```
set PLATE_FMT=MP4
for %s in (0 1 2 3 4 5 6 7 8 9 11) do "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" -b -P window3d.py -- %s ..\window3d\plates 100 32 EEVEE
```

   (RTX 4050, plugged in: roughly 15-30 minutes for all scenes. Keep the laptop on the charger.)
4. Commit and push the 11 files `dailymind/window3d/plates/s*.mp4`; Claude composites the titles, slams,
   splats, music and the end card in the cloud (`ultimate/make_window3d.py`) and runs qa.py.

# Render the Leaning Tower of Pisa video (real 3D v2) on the RTX PC

Same setup. Pull the branch first (`git pull origin claude/new-session-ati950`). In `dailymind/blender` run:

```
set PLATE_FMT=MP4
for %s in (0 1 2 3 4 5 6 7 8 9 11) do "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" -b -P pisa3d.py -- %s ..\pisa3d\plates 100 64 EEVEE
```

Each scene first bakes its rigid-body physics (a few seconds), then renders with motion blur. Use whatever Blender
4.2+ version is installed (adjust the path). Check one frame of scene 0 looks right before waiting for the rest.
Then commit and push the 11 files `dailymind/pisa3d/plates/s*.mp4` (nothing else); Claude composites the classic
layer (`ultimate/make_pisa3d.py`), runs qa.py and reviews every frame.

# Render the Eiffel Tower video (real 3D v3) on the RTX PC

Pull the branch first (`git pull origin claude/new-session-ati950`). In `dailymind/blender` run:

```
set PLATE_FMT=MP4
for %s in (0 1 2 3 4 5 6 7 8 9 11) do "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" -b -P eiffel3d.py -- %s ..\eiffel3d\plates 100 64 EEVEE
```

Then commit and push only the 11 files `dailymind/eiffel3d/plates/s*.mp4`; Claude composites the classic layer
(`ultimate/make_eiffel3d.py`), runs qa.py and reviews every frame.

# Render the THREE STUDIO SAMPLES (A Object Portal, B Living Blueprint, C Time Seam) on the RTX PC

Pull the branch first (`git pull origin claude/new-session-ati950`). In `dailymind/blender` run:

```
set PLATE_FMT=MP4
for %s in (A0 A1 A2 A3 A4 A5 B0 B1 B2 B3 B4 B5 C0 C1 C2 C3 C4 C5) do "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" -b -P samples_eiffel.py -- %s ..\samples\plates 100 64 EEVEE
```

18 short scenes (~105 s of footage, roughly 45-60 minutes). Then commit and push only the 18 files
`dailymind/samples/plates/s*.mp4`; Claude composites the three MP4s (`ultimate/make_samples.py A|B|C`), runs QC
and compares them.

# Render the MINIATURE CINEMATIC UNIVERSE samples (S1 1889 diorama, S2 giant pocket watch, S3 miniature factory)

Needs internet on the PC: the first run downloads the CC0 Poly Haven models/textures/HDRIs (~200 MB) into
`dailymind/assets_cache/` (git-ignored, reused afterwards). Pull the branch first, then in `dailymind/blender`:

```
set PLATE_FMT=MP4
for %s in (S1 S2 S3) do "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" -b -P mini3d.py -- %s ..\miniature\renders 100 64
```

Three 12-second shots (1,080 frames) with motion blur and macro depth of field: roughly 30-45 minutes.
Then commit and push only `dailymind/miniature/renders/S1.mp4`, `S2.mp4`, `S3.mp4`.
