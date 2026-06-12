"""Tests for earth automation module."""

import unittest
from unittest.mock import MagicMock, patch

from earth_imagery_watcher.earth_automation import EarthAutomation


class EarthAutomationTests(unittest.TestCase):
    @patch("earth_imagery_watcher.earth_automation.EarthAutomation._import_pyautogui")
    def test_earth_automation_initialization(self, mock_pyautogui) -> None:
        mock_pyautogui.return_value = MagicMock()
        automation = EarthAutomation(pre_action_delay=0.1, post_action_delay=0.1)
        
        self.assertEqual(automation._pre_action_delay, 0.1)
        self.assertEqual(automation._post_action_delay, 0.1)

    @patch("earth_imagery_watcher.earth_automation.EarthAutomation._import_pyautogui")
    def test_toggle_historical_imagery(self, mock_pyautogui) -> None:
        mock_pag = MagicMock()
        mock_pyautogui.return_value = mock_pag
        
        automation = EarthAutomation(pre_action_delay=0, post_action_delay=0)
        automation.toggle_historical_imagery(enable=True)
        
        mock_pag.hotkey.assert_called_with("ctrl", "h")

    @patch("earth_imagery_watcher.earth_automation.EarthAutomation._import_pyautogui")
    def test_move_slider_to_latest(self, mock_pyautogui) -> None:
        mock_pag = MagicMock()
        mock_pyautogui.return_value = mock_pag
        
        automation = EarthAutomation(pre_action_delay=0, post_action_delay=0)
        automation.move_historical_imagery_slider_to_latest()
        
        mock_pag.press.assert_called_with("end")

    @patch("earth_imagery_watcher.earth_automation.EarthAutomation._import_pyautogui")
    def test_move_slider_to_earliest(self, mock_pyautogui) -> None:
        mock_pag = MagicMock()
        mock_pyautogui.return_value = mock_pag
        
        automation = EarthAutomation(pre_action_delay=0, post_action_delay=0)
        automation.move_historical_imagery_slider_to_earliest()
        
        mock_pag.press.assert_called_with("home")

    @patch("earth_imagery_watcher.earth_automation.EarthAutomation._import_pyautogui")
    def test_move_slider_by_steps(self, mock_pyautogui) -> None:
        mock_pag = MagicMock()
        mock_pyautogui.return_value = mock_pag
        
        automation = EarthAutomation(pre_action_delay=0, post_action_delay=0)
        automation.move_historical_imagery_slider_by_steps(3)
        
        self.assertEqual(mock_pag.press.call_count, 3)
        mock_pag.press.assert_called_with("right")

    @patch("earth_imagery_watcher.earth_automation.EarthAutomation._import_pyautogui")
    def test_move_slider_negative_steps(self, mock_pyautogui) -> None:
        mock_pag = MagicMock()
        mock_pyautogui.return_value = mock_pag
        
        automation = EarthAutomation(pre_action_delay=0, post_action_delay=0)
        automation.move_historical_imagery_slider_by_steps(-2)
        
        self.assertEqual(mock_pag.press.call_count, 2)
        mock_pag.press.assert_called_with("left")

    @patch("earth_imagery_watcher.earth_automation.EarthAutomation._import_pyautogui")
    def test_set_delays(self, mock_pyautogui) -> None:
        mock_pyautogui.return_value = MagicMock()
        
        automation = EarthAutomation()
        automation.set_pre_action_delay(1.5)
        automation.set_post_action_delay(2.5)
        
        self.assertEqual(automation._pre_action_delay, 1.5)
        self.assertEqual(automation._post_action_delay, 2.5)


if __name__ == "__main__":
    unittest.main()
