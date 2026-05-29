# Earth Imagery Watcher

Cross-platform Python MVP for monitoring Google Earth Pro imagery dates for GeoJSON regions.

This project is intentionally date-only. It does not compare imagery pixels.

## Current MVP

- Loads GeoJSON Polygon and MultiPolygon regions.
- Generates sample points inside each region.
- Generates temporary KML files with `LookAt` coordinates.
- Uses a default Google Earth range of 100 km / 100000 meters.
- Can open generated KML files through the OS default file association.
- Can capture a bottom-right screenshot crop where Google Earth Pro displays the imagery date.
- Stores checks in SQLite.
- Stores separate normal/default and historical/latest imagery date fields.
- Compares the latest detected date against the previous stored date.
- Leaves Google Earth Pro automation behind an `EarthController` interface.

## CLI

```powershell
python -m earth_imagery_watcher.main run examples/sample_region.geojson --db watcher.sqlite --dry-run
```

`--dry-run` generates points and KML but does not try to open Google Earth or OCR screenshots.

To open each generated KML in Google Earth Pro through your OS file association:

```powershell
python -m earth_imagery_watcher.main run examples/sample_region.geojson --open-earth --point-delay-seconds 5 --dry-run
```

`--open-earth` only opens the KML files. It does not perform OCR, Historical Imagery slider control, or PyAutoGUI automation.

To open each point, wait for Google Earth Pro to settle, then save the bottom-right date crop:

```powershell
python -m earth_imagery_watcher.main run examples/sample_region.geojson --open-earth --point-delay-seconds 8 --capture-date-crop --crop-output-dir screenshots
```

Google Earth Pro may need extra time on the first point while the app opens, restores state, loads imagery, and finishes navigation. Use a longer first-point delay and optional retry captures when needed:

```powershell
python -m earth_imagery_watcher.main run examples/delhi_region.geojson --open-earth --first-point-delay-seconds 15 --point-delay-seconds 8 --capture-date-crop --capture-retries 2 --capture-retry-delay-seconds 2 --crop-output-dir screenshots
```

Screenshot capture uses Pillow/ImageGrab. On Windows, the preferred auto-hide taskbar handling is to move the mouse away from the bottom edge and crop from the detected Google Earth Pro window instead of the full screen. If the Google Earth window cannot be detected, the app prints a warning and falls back to a full-screen crop.

Install the optional screenshot dependencies with:

```powershell
pip install "earth-imagery-watcher[screenshot]"
```

`--crop-bottom-offset` is available as an advanced fallback, but it is not the main taskbar solution. Setting it too high can crop above the Google Earth imagery date/status bar and miss the date entirely.

`--capture-date-crop` saves PNG crops only. OCR is still not implemented.

For manual smoke testing without Google Earth automation, pass a detected date:

```powershell
python -m earth_imagery_watcher.main run examples/sample_region.geojson --manual-normal-date "May 2024" --manual-historical-date "June 2024"
```

To start the bot before taking a break and let it wait until the laptop is idle:

```powershell
python -m earth_imagery_watcher.main run examples/delhi_region.geojson --wait-until-idle --idle-minutes 10 --open-earth --capture-date-crop
```

Idle waiting is currently a pre-run gate only: once the idle threshold is reached, the normal workflow starts and does not pause again if you become active. On Windows, idle detection uses the system last-input timer. On unsupported platforms, `--wait-until-idle` exits with a clear error.

For a night run, use Windows Task Scheduler to run the command at night. Full built-in scheduling is planned for later.

## Planned Automation Layer

The `EarthController` interface is where the later PyAutoGUI/OpenCV/Tesseract workflow belongs:

1. Open Google Earth Pro with generated KML.
2. Screenshot the viewport.
3. Crop the bottom-right imagery-date area.
4. OCR the normal/default date.
5. Enable Historical Imagery.
6. Move slider to the latest/rightmost image.
7. OCR the historical latest date.

Historical Imagery automation is planned but not implemented yet.
