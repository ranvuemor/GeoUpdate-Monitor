# GeoUpdate Monitor

GeoUpdate Monitor is a date-only imagery update watcher for Google Earth Pro. It takes GeoJSON regions, generates sample points, opens them in Google Earth Pro through KML, captures the bottom-right imagery date area, and stores check history in SQLite. The project does not compare image pixels; it monitors imagery date changes only.

## Status: Functional MVP

Implemented:

- GeoJSON region loading
- Sample point generation
- KML creation
- Google Earth Pro navigation
- Screenshot crop capture
- PaddleOCR-based date extraction
- Date parsing and normalization
- SQLite history and change detection
- Idle-aware pre-run waiting

Planned:

- Historical Imagery automation
- CLI/config-file driven runs
- Fully integrated scheduled runs
- Notifications wired into date-change checks

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

`--capture-date-crop` saves PNG crops. Add `--ocr-date` when you want the run workflow to OCR those crops.

To capture crops and immediately OCR the normal/default imagery date:

```powershell
python -m earth_imagery_watcher.main run examples/sample_region.geojson --open-earth --capture-date-crop --ocr-date
```

When `--ocr-date` is enabled, OCR runs only after a crop is saved. The parsed OCR date is stored in the normal imagery date fields and compared using the same date-change logic as manual dates. If OCR cannot find a valid date, the app prints a warning, stores the raw OCR artifact data when available, and continues with the remaining points.

To run OCR manually against an existing crop image:

```powershell
python -m earth_imagery_watcher.main ocr screenshots\Berlin-Sample_berlin-sample-sample-1_20260529T120000Z_date_crop.png
```

OCR uses PaddleOCR. The standalone `ocr` command prints raw OCR text, detected text blocks, confidence, and the parsed imagery date. Install the optional OCR dependency with:

```powershell
pip install "earth-imagery-watcher[ocr]"
```

Historical Imagery OCR is not automated yet.

For manual smoke testing without Google Earth automation, pass a detected date:

```powershell
python -m earth_imagery_watcher.main run examples/sample_region.geojson --manual-normal-date "May 2024" --manual-historical-date "June 2024"
```

To start the bot before taking a break and let it wait until the laptop is idle:

```powershell
python -m earth_imagery_watcher.main run examples/delhi_region.geojson --wait-until-idle --idle-minutes 10 --open-earth --capture-date-crop
```

Idle waiting is currently a pre-run gate only: once the idle threshold is reached, the normal workflow starts and does not pause again if you become active. On Windows, idle detection uses the system last-input timer. On unsupported platforms, `--wait-until-idle` exits with a clear error.

For a night run, use Windows Task Scheduler to run the command at night.

## Historical Imagery Automation

Historical Imagery UI automation is not wired into the `run` workflow yet. The repository includes an experimental `EarthAutomation` helper for PyAutoGUI keyboard actions, but there is no CLI flag yet that performs the full normal-date plus historical-latest-date workflow end to end.

Current `run` behavior captures and OCRs the normal/default imagery date only:

```powershell
python -m earth_imagery_watcher.main run examples/sample_region.geojson --open-earth --capture-date-crop --ocr-date
```

Planned historical workflow:

1. Open each KML point in Google Earth Pro
2. Capture the default/normal imagery date using OCR
3. Toggle Historical Imagery
4. Move the slider to the latest/rightmost historical image
5. Capture the historical latest imagery date using OCR

Requires: `pip install "earth-imagery-watcher[automation]"`

## Configuration Helpers

The repository includes configuration dataclasses and a helper for creating a default config file from Python. Config files are not yet wired into the CLI `run` command.

```python
from earth_imagery_watcher.config import ConfigManager, create_default_config_file

create_default_config_file("config.json")
manager = ConfigManager("config.json")
config = manager.config
```

## Scheduling Helpers

The repository includes a small in-process scheduler helper. It is not yet integrated into the CLI.

```python
from earth_imagery_watcher.scheduler import SimpleScheduler

scheduler = SimpleScheduler()
scheduler.add_daily_job("morning-check", callback=check_imagery, hour=8, minute=0)
scheduler.add_interval_job("every-six-hours", callback=check_imagery, interval_minutes=360)
scheduler.run_forever(check_interval_seconds=60)
```

## Notification Helpers

The repository includes notification helper classes. They are not yet wired into automatic date-change handling in `run`.

**Webhook notifications:**
```python
from earth_imagery_watcher.notifications import NotificationSender, DateChangeEvent

sender = NotificationSender(webhook_url="https://your-server.com/webhook")
event = DateChangeEvent(...)
sender.send_webhook(event)
```

**Slack notifications:**
```python
sender.send_slack("https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK", event)
```

**Email notifications:**
```python
sender.send_email(
    event,
    recipients=["user@example.com"],
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    sender="bot@example.com",
    password="app-password",
)
```

**Event logging:**
```python
from earth_imagery_watcher.notifications import EventLogger

logger = EventLogger("imagery-events.jsonl")
logger.log_event(event)
```

## Architecture: Automation Layer

The current `EarthController` opens KML files through the OS default file association. `EarthAutomation` contains experimental PyAutoGUI helpers for future Historical Imagery interaction.

Implemented workflow:

1. Generate and open KML files
2. Capture the bottom-right imagery-date area
3. OCR the normal/default date
4. Store results in SQLite and compare date changes

Future workflow:

1. Toggle Historical Imagery via UI automation
2. Move the slider to latest/rightmost imagery
3. OCR the historical latest date
4. Notify when confirmed date changes are detected
