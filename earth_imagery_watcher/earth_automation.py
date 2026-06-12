"""Google Earth Pro automation using PyAutoGUI for Historical Imagery and slider control."""

from __future__ import annotations

import time
from typing import Literal


class EarthAutomation:
    """Automates Google Earth Pro interactions using keyboard and mouse control."""

    def __init__(self, pre_action_delay: float = 0.5, post_action_delay: float = 1.0):
        """Initialize automation controller.
        
        Args:
            pre_action_delay: Delay before sending commands to allow Earth to be ready.
            post_action_delay: Delay after sending commands to allow Earth to process.
        """
        self._pre_action_delay = pre_action_delay
        self._post_action_delay = post_action_delay
        self._pyautogui = self._import_pyautogui()

    @staticmethod
    def _import_pyautogui() -> object:
        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            return pyautogui
        except ImportError as exc:
            raise RuntimeError(
                "Earth automation requires PyAutoGUI. Install with: pip install 'earth-imagery-watcher[automation]'"
            ) from exc

    def toggle_historical_imagery(self, enable: bool = True) -> None:
        """Toggle the Historical Imagery view in Google Earth Pro.
        
        In Google Earth Pro, the Historical Imagery toggle is typically accessed via:
        - View menu → Historical Imagery, or
        - Keyboard shortcut (Alt+H on Windows), or
        - Ctrl+H in some versions
        
        Args:
            enable: True to enable, False to disable Historical Imagery view.
        """
        time.sleep(self._pre_action_delay)
        
        try:
            self._pyautogui.hotkey("ctrl", "h")
            time.sleep(self._post_action_delay)
        except Exception as exc:
            raise RuntimeError(f"Failed to toggle Historical Imagery: {exc}") from exc

    def move_historical_imagery_slider_to_latest(self) -> None:
        """Move the Historical Imagery slider to the latest (rightmost) position.
        
        This typically involves:
        1. Ensuring the slider is visible (Historical Imagery mode is on)
        2. Clicking or tabbing to the slider
        3. Pressing End key to jump to the latest imagery date
        
        Alternative approach: Click far right of slider timeline.
        """
        time.sleep(self._pre_action_delay)
        
        try:
            self._pyautogui.press("end")
            time.sleep(self._post_action_delay)
        except Exception as exc:
            raise RuntimeError(f"Failed to move Historical Imagery slider to latest: {exc}") from exc

    def move_historical_imagery_slider_to_earliest(self) -> None:
        """Move the Historical Imagery slider to the earliest (leftmost) position."""
        time.sleep(self._pre_action_delay)
        
        try:
            self._pyautogui.press("home")
            time.sleep(self._post_action_delay)
        except Exception as exc:
            raise RuntimeError(f"Failed to move Historical Imagery slider to earliest: {exc}") from exc

    def move_historical_imagery_slider_by_steps(self, steps: int) -> None:
        """Move the Historical Imagery slider by a number of steps.
        
        Positive steps move right (more recent), negative move left (older).
        Each step typically represents one imagery date in the timeline.
        """
        time.sleep(self._pre_action_delay)
        
        try:
            key = "right" if steps > 0 else "left"
            for _ in range(abs(steps)):
                self._pyautogui.press(key)
                time.sleep(0.1)
            time.sleep(self._post_action_delay)
        except Exception as exc:
            raise RuntimeError(f"Failed to move Historical Imagery slider: {exc}") from exc

    def set_pre_action_delay(self, delay: float) -> None:
        """Set delay before sending commands."""
        self._pre_action_delay = delay

    def set_post_action_delay(self, delay: float) -> None:
        """Set delay after sending commands."""
        self._post_action_delay = delay
