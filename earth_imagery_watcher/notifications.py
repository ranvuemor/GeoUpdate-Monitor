"""Notification system for imagery date changes."""

from __future__ import annotations

import json
import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DateChangeEvent:
    """Represents a detected imagery date change."""
    
    region_name: str
    sample_id: str
    latitude: float
    longitude: float
    old_normal_date: str | None
    new_normal_date: str | None
    old_historical_date: str | None
    new_historical_date: str | None
    timestamp: str


class NotificationSender:
    """Sends notifications about imagery date changes."""
    
    def __init__(self, webhook_url: str | None = None, email_config: dict[str, Any] | None = None):
        """Initialize notification sender.
        
        Args:
            webhook_url: Generic webhook URL for change events.
            email_config: Dict with 'smtp_server', 'smtp_port', 'sender', 'password' for email.
        """
        self.webhook_url = webhook_url
        self.email_config = email_config or {}
    
    def send_webhook(self, event: DateChangeEvent, custom_data: dict[str, Any] | None = None) -> bool:
        """Send change event to webhook.
        
        Args:
            event: The date change event.
            custom_data: Optional additional data to send.
            
        Returns:
            True if sent successfully, False otherwise.
        """
        if not self.webhook_url:
            return False
        
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError(
                "Webhook notifications require requests library. Install with: pip install requests"
            ) from exc
        
        payload = {
            "event_type": "imagery_date_change",
            "region": event.region_name,
            "sample_id": event.sample_id,
            "location": {"lat": event.latitude, "lon": event.longitude},
            "changes": {
                "normal_imagery": {
                    "old": event.old_normal_date,
                    "new": event.new_normal_date,
                },
                "historical_imagery": {
                    "old": event.old_historical_date,
                    "new": event.new_historical_date,
                },
            },
            "timestamp": event.timestamp,
        }
        
        if custom_data:
            payload.update(custom_data)
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return True
        except Exception as exc:
            print(f"Warning: Webhook notification failed: {exc}")
            return False
    
    def send_slack(self, webhook_url: str, event: DateChangeEvent) -> bool:
        """Send Slack notification about date change.
        
        Args:
            webhook_url: Slack incoming webhook URL.
            event: The date change event.
            
        Returns:
            True if sent successfully, False otherwise.
        """
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError(
                "Slack notifications require requests library. Install with: pip install requests"
            ) from exc
        
        normal_change = ""
        if event.old_normal_date != event.new_normal_date:
            normal_change = f"\n• Normal imagery: {event.old_normal_date} → {event.new_normal_date}"
        
        historical_change = ""
        if event.old_historical_date != event.new_historical_date:
            historical_change = f"\n• Historical imagery: {event.old_historical_date} → {event.new_historical_date}"
        
        message = {
            "text": f"🌍 Imagery Date Change: {event.region_name}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📍 {event.region_name}* (Sample: {event.sample_id})\n"
                               f"Location: {event.latitude:.4f}, {event.longitude:.4f}"
                               f"{normal_change}"
                               f"{historical_change}",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Detected at {event.timestamp}",
                        }
                    ],
                },
            ],
        }
        
        try:
            response = requests.post(
                webhook_url,
                json=message,
                timeout=10,
            )
            response.raise_for_status()
            return True
        except Exception as exc:
            print(f"Warning: Slack notification failed: {exc}")
            return False
    
    def send_email(
        self,
        event: DateChangeEvent,
        recipients: list[str],
        smtp_server: str | None = None,
        smtp_port: int | None = None,
        sender: str | None = None,
        password: str | None = None,
    ) -> bool:
        """Send email notification about date change.
        
        Args:
            event: The date change event.
            recipients: List of email addresses to send to.
            smtp_server: SMTP server address. Falls back to config if not provided.
            smtp_port: SMTP port. Falls back to config if not provided.
            sender: Sender email address. Falls back to config if not provided.
            password: SMTP password. Falls back to config if not provided.
            
        Returns:
            True if sent successfully, False otherwise.
        """
        if not recipients:
            return False
        
        smtp_server = smtp_server or self.email_config.get("smtp_server")
        smtp_port = smtp_port or self.email_config.get("smtp_port", 587)
        sender = sender or self.email_config.get("sender")
        password = password or self.email_config.get("password")
        
        if not all([smtp_server, sender, password]):
            print("Warning: Email configuration incomplete. Skipping email notification.")
            return False
        
        normal_change = ""
        if event.old_normal_date != event.new_normal_date:
            normal_change = f"\n• Normal imagery date: {event.old_normal_date} → {event.new_normal_date}"
        
        historical_change = ""
        if event.old_historical_date != event.new_historical_date:
            historical_change = f"\n• Historical imagery date: {event.old_historical_date} → {event.new_historical_date}"
        
        body = f"""Imagery Date Change Detected

Region: {event.region_name}
Sample: {event.sample_id}
Location: {event.latitude:.4f}, {event.longitude:.4f}

Changes:{normal_change}{historical_change}

Detected at: {event.timestamp}
"""
        
        try:
            msg = MIMEMultipart()
            msg["From"] = sender
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = f"🌍 Imagery Update: {event.region_name}"
            msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)
            
            return True
        except Exception as exc:
            print(f"Warning: Email notification failed: {exc}")
            return False


class EventLogger:
    """Logs imagery date change events to file."""
    
    def __init__(self, log_path: str | Path | None = None):
        """Initialize event logger.
        
        Args:
            log_path: Path to log file. If None, logging is disabled.
        """
        self.log_path = Path(log_path) if log_path else None
    
    def log_event(self, event: DateChangeEvent) -> bool:
        """Log a change event to file.
        
        Args:
            event: The event to log.
            
        Returns:
            True if logged successfully, False otherwise.
        """
        if not self.log_path:
            return False
        
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            
            event_dict = {
                "region_name": event.region_name,
                "sample_id": event.sample_id,
                "latitude": event.latitude,
                "longitude": event.longitude,
                "old_normal_date": event.old_normal_date,
                "new_normal_date": event.new_normal_date,
                "old_historical_date": event.old_historical_date,
                "new_historical_date": event.new_historical_date,
                "timestamp": event.timestamp,
            }
            
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_dict) + "\n")
            
            return True
        except Exception as exc:
            print(f"Warning: Failed to log event: {exc}")
            return False
