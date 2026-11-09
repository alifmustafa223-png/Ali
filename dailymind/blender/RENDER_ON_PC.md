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
