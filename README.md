# Earth Imagery Watcher

Cross-platform Python MVP for monitoring Google Earth Pro imagery dates for GeoJSON regions.

This project is intentionally date-only. It does not compare imagery pixels.

## Current MVP

- Loads GeoJSON Polygon and MultiPolygon regions.
- Generates sample points inside each region.
- Generates temporary KML files with `LookAt` coordinates.
- Uses a default Google Earth range of 100 km / 100000 meters.
- Can open generated KML files through the OS default file association.
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

For manual smoke testing without Google Earth automation, pass a detected date:

```powershell
python -m earth_imagery_watcher.main run examples/sample_region.geojson --manual-normal-date "May 2024" --manual-historical-date "June 2024"
```

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
