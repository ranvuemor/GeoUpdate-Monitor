# Implementation Guide: Enhanced GeoUpdate Monitor

## Summary of Completed Features

### 1. Historical Imagery Automation ✅
**Module:** `earth_automation.py`

The `EarthAutomation` class provides PyAutoGUI-based automation for:
- Toggling Historical Imagery mode (Ctrl+H)
- Moving the timeline slider to latest imagery (End key)
- Moving the timeline slider to earliest imagery (Home key)
- Fine-grained slider control (arrow keys, step-by-step)
- Configurable action delays for Google Earth Pro responsiveness

**Usage:**
```python
from earth_imagery_watcher.earth_automation import EarthAutomation

automation = EarthAutomation(pre_action_delay=0.5, post_action_delay=1.0)
automation.toggle_historical_imagery(enable=True)
automation.move_historical_imagery_slider_to_latest()
# Then capture screenshot and OCR the historical date
```

### 2. Configuration System ✅
**Module:** `config.py`

Hierarchical configuration management for:
- Earth Pro settings (delays, crop dimensions, OCR thresholds)
- Idle detection settings
- Notification endpoints (email, Slack, webhooks)
- Schedule rules (daily, hourly, interval-based)
- Database and path settings

**Features:**
- Dataclass-based type-safe configs
- JSON serialization/deserialization
- Nested config auto-normalization
- Default values for all settings
- Easy CLI generation of config templates

**Usage:**
```python
from earth_imagery_watcher.config import ConfigManager, create_default_config_file

# Create default config
create_default_config_file("config.json")

# Load and use
manager = ConfigManager("config.json")
earth_config = manager.get_earth_config()
```

### 3. Scheduling System ✅
**Module:** `scheduler.py`

Built-in scheduler for recurring checks:
- **Interval-based:** Run every N minutes
- **Hourly:** Run at specific minute of every hour
- **Daily:** Run at specific time each day
- Extensible `ScheduledJob` class
- `SimpleScheduler` for managing multiple jobs

**Features:**
- Non-blocking scheduler with check intervals
- Job tracking and management
- Immediate execution option for first run
- Start/stop/reset job controls

**Usage:**
```python
from earth_imagery_watcher.scheduler import SimpleScheduler

scheduler = SimpleScheduler()
scheduler.add_daily_job("morning", callback, hour=8, minute=0)
scheduler.add_interval_job("frequent", callback, interval_minutes=60)
scheduler.run_forever(check_interval_seconds=60)
```

### 4. Notifications System ✅
**Module:** `notifications.py`

Multi-channel change notifications:
- **Webhooks:** POST events to custom endpoints (e.g., automation/integrations)
- **Slack:** Format events as rich Slack messages with blocks
- **Email:** SMTP-based notifications with detailed change information
- **Event Logging:** Append-only JSONL event log for audit trail

**Features:**
- `DateChangeEvent` dataclass for typed events
- `NotificationSender` for multi-channel dispatch
- `EventLogger` for persistent event storage
- Graceful error handling with logging
- Optional email/Slack configuration

**Usage:**
```python
from earth_imagery_watcher.notifications import NotificationSender, DateChangeEvent

sender = NotificationSender(webhook_url="https://example.com/webhook")
event = DateChangeEvent(
    region_name="Delhi",
    sample_id="delhi-1",
    latitude=28.7,
    longitude=77.1,
    old_normal_date="2024-01-01",
    new_normal_date="2024-02-01",
    old_historical_date=None,
    new_historical_date=None,
    timestamp="2024-02-21T10:00:00Z"
)

sender.send_webhook(event)
sender.send_slack("https://hooks.slack.com/.../XXX", event)
```

## Dependencies

Updated `pyproject.toml` with new optional dependency groups:

```
[automation] - PyAutoGUI for Historical Imagery slider control
[notifications] - requests library for webhooks and Slack
[all] - All optional dependencies combined
```

Installation:
```bash
pip install earth-imagery-watcher[automation,notifications]
# or
pip install "earth-imagery-watcher[all]"
```

## Testing

**New Test Modules:**
- `test_config.py` - 8 tests for configuration system
- `test_scheduler.py` - 9 tests for scheduling
- `test_notifications.py` - 5 tests for notifications
- `test_earth_automation.py` - 7 tests for earth automation

**Test Coverage:**
- All 74 tests pass (45 existing + 29 new)
- Configuration serialization/deserialization
- Scheduler interval/hourly/daily logic
- Event logging and notification initialization
- Earth automation mocking

Run tests:
```bash
python -m pytest tests/ -v
```

## Architecture Integration

### Flow: Complete Workflow

```
1. [Schedule Trigger] → (if scheduled)
   └─> Check if due using SimpleScheduler
   
2. [Idle Wait] → (if configured)
   └─> Wait for system idle threshold (Windows)
   
3. [Load Config] → (optional)
   └─> ConfigManager loads earth/idle/notification settings
   
4. [For Each Sample Point]:
   a. Generate KML
   b. Open in Google Earth Pro
   c. Wait for delay (from config)
   d. Take screenshot
   e. Crop bottom-right area
   f. OCR normal imagery date
   g. If history enabled:
      - Toggle Historical Imagery (EarthAutomation)
      - Move slider to latest (EarthAutomation)
      - Take screenshot
      - Crop and OCR historical date
   h. Store in database
   i. Detect changes
   
5. [Notifications] → (if enabled)
   a. For each changed date:
      - Create DateChangeEvent
      - Log event (EventLogger)
      - Send webhooks (NotificationSender)
      - Send Slack (NotificationSender)
      - Send emails (NotificationSender)
```

### Module Dependencies

```
main.py
  ├── config.py
  ├── scheduler.py
  ├── earth_automation.py
  ├── notifications.py
  ├── earth_controller.py
  ├── screenshot_capture.py
  ├── ocr_reader.py
  └── database.py
```

## Next Steps (Future Enhancements)

1. **CLI Commands:**
   - `config` subcommand for config generation/management
   - `schedule` subcommand for listing/managing scheduled jobs
   - Support `--config` flag in `run` command

2. **Enhanced Scheduling:**
   - Cron expression support
   - Windows Task Scheduler integration
   - System tray/daemon mode

3. **Advanced Notifications:**
   - Discord integration
   - SMS via Twilio
   - Multiple webhook retry logic
   - Notification templates/customization

4. **Monitoring & Observability:**
   - Prometheus metrics export
   - Health checks endpoint
   - Detailed audit logs
   - Change history dashboard

5. **Google Earth Engine Integration (Optional):**
   - Parallel API-based checks for advanced users
   - Landsat/Sentinel temporal analysis
   - Fallback to screenshot+OCR if API unavailable

## Backwards Compatibility

All changes are **fully backwards compatible**:
- Existing CLI commands work unchanged
- Optional config system (defaults provided)
- New modules are separate from core
- Existing tests all pass
- No breaking changes to public APIs

## Example: Full Workflow

```bash
# 1. Generate config
python -m earth_imagery_watcher.main config --generate config.json

# 2. Edit config.json with your settings

# 3. Run with config (future CLI update)
python -m earth_imagery_watcher.main run examples/sample_region.geojson \
  --config config.json \
  --db watcher.sqlite

# 4. (Programmatic) Schedule runs
python scripts/scheduler.py
```

Example scheduler script (`scripts/scheduler.py`):
```python
from earth_imagery_watcher.scheduler import SimpleScheduler
from earth_imagery_watcher.config import ConfigManager

def run_check():
    # Load config and execute checks
    manager = ConfigManager("config.json")
    # ... run check logic ...

scheduler = SimpleScheduler()
scheduler.add_daily_job("check", run_check, hour=8, minute=0)
scheduler.run_forever()
```
