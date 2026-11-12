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
