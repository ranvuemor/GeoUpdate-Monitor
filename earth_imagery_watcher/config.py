"""Configuration management for earth-imagery-watcher."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Literal


@dataclass(frozen=True)
class NotificationConfig:
    """Configuration for notifications when imagery dates change."""
    
    enabled: bool = False
    email_recipients: list[str] | None = None
    slack_webhook_url: str | None = None
    webhook_url: str | None = None
    send_on_no_change: bool = False


@dataclass(frozen=True)
class ScheduleRule:
    """A single scheduling rule for running checks."""
    
    name: str
    geojson_path: str
    frequency: Literal["hourly", "daily", "weekly", "custom"]
    interval_minutes: int | None = None
    day_of_week: int | None = None
    hour_of_day: int | None = None
    enabled: bool = True


@dataclass(frozen=True)
class EarthConfig:
    """Configuration for Google Earth Pro interaction."""
    
    open_earth_pro: bool = True
    point_delay_seconds: float = 5
    first_point_delay_seconds: float | None = None
    capture_date_crop: bool = True
    crop_output_dir: str = "screenshots"
    crop_width: int = 500
    crop_height: int = 120
    crop_bottom_offset: int = 0
    pre_screenshot_delay: float = 1.0
    capture_retries: int = 1
    capture_retry_delay_seconds: float = 2.0
    ocr_date: bool = False
    ocr_confidence_threshold: float = 0.3


@dataclass(frozen=True)
class IdleConfig:
    """Configuration for idle detection."""
    
    wait_until_idle: bool = False
    idle_minutes: float = 10
    idle_check_interval_seconds: float = 15


@dataclass(frozen=True)
class WatcherConfig:
    """Complete configuration for earth-imagery-watcher."""
    
    version: str = "1"
    db_path: str = "watcher.sqlite"
    max_points_per_region: int = 5
    range_meters: int = 100000
    
    earth: EarthConfig | dict[str, Any] = None
    idle: IdleConfig | dict[str, Any] = None
    notifications: NotificationConfig | dict[str, Any] = None
    schedule_rules: list[ScheduleRule | dict[str, Any]] | None = None
    
    def __post_init__(self):
        """Normalize nested configs."""
        if isinstance(self.earth, dict):
            object.__setattr__(self, "earth", EarthConfig(**self.earth))
        elif self.earth is None:
            object.__setattr__(self, "earth", EarthConfig())
            
        if isinstance(self.idle, dict):
            object.__setattr__(self, "idle", IdleConfig(**self.idle))
        elif self.idle is None:
            object.__setattr__(self, "idle", IdleConfig())
            
        if isinstance(self.notifications, dict):
            object.__setattr__(self, "notifications", NotificationConfig(**self.notifications))
        elif self.notifications is None:
            object.__setattr__(self, "notifications", NotificationConfig())
            
        if isinstance(self.schedule_rules, list):
            rules = []
            for rule in self.schedule_rules:
                if isinstance(rule, dict):
                    rules.append(ScheduleRule(**rule))
                else:
                    rules.append(rule)
            object.__setattr__(self, "schedule_rules", rules)


class ConfigManager:
    """Manages loading and saving watcher configuration."""
    
    def __init__(self, config_path: str | Path | None = None):
        """Initialize config manager.
        
        Args:
            config_path: Path to config file. If None, uses defaults.
        """
        self.config_path = Path(config_path) if config_path else None
        self.config = self._load_config()
    
    def _load_config(self) -> WatcherConfig:
        """Load configuration from file or return defaults."""
        if not self.config_path or not self.config_path.exists():
            return WatcherConfig()
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return WatcherConfig(**data)
        except (json.JSONDecodeError, TypeError) as exc:
            print(f"Warning: Failed to load config from {self.config_path}: {exc}")
            return WatcherConfig()
    
    def save(self, config: WatcherConfig | None = None) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration to save. If None, uses current config.
        """
        if not self.config_path:
            raise ValueError("config_path must be set to save configuration.")
        
        to_save = config or self.config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        def dataclass_to_dict(obj: Any) -> Any:
            if hasattr(obj, "__dataclass_fields__"):
                return {k: dataclass_to_dict(v) for k, v in asdict(obj).items()}
            elif isinstance(obj, list):
                return [dataclass_to_dict(item) for item in obj]
            else:
                return obj
        
        data = dataclass_to_dict(to_save)
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def get_earth_config(self) -> EarthConfig:
        """Get Earth Pro configuration."""
        return self.config.earth or EarthConfig()
    
    def get_idle_config(self) -> IdleConfig:
        """Get idle detection configuration."""
        return self.config.idle or IdleConfig()
    
    def get_notifications_config(self) -> NotificationConfig:
        """Get notifications configuration."""
        return self.config.notifications or NotificationConfig()
    
    def get_schedule_rules(self) -> list[ScheduleRule]:
        """Get schedule rules."""
        return self.config.schedule_rules or []


def create_default_config_file(output_path: str | Path) -> None:
    """Create a default configuration file at the specified path."""
    config = WatcherConfig(
        earth=EarthConfig(
            open_earth_pro=True,
            point_delay_seconds=5,
            capture_date_crop=True,
            ocr_date=False,
        ),
        idle=IdleConfig(
            wait_until_idle=False,
            idle_minutes=10,
        ),
        notifications=NotificationConfig(
            enabled=False,
        ),
        schedule_rules=[],
    )
    
    manager = ConfigManager(output_path)
    manager.config = config
    manager.save(config)
