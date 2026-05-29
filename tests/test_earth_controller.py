import unittest
from pathlib import Path

from earth_imagery_watcher.earth_controller import build_open_command


class EarthControllerTests(unittest.TestCase):
    def test_windows_uses_startfile_path(self) -> None:
        self.assertIsNone(build_open_command(Path("point.kml"), system="Windows"))

    def test_macos_open_command(self) -> None:
        self.assertEqual(build_open_command(Path("point.kml"), system="Darwin"), ["open", "point.kml"])

    def test_linux_xdg_open_command(self) -> None:
        self.assertEqual(build_open_command(Path("point.kml"), system="Linux"), ["xdg-open", "point.kml"])

    def test_unsupported_platform_raises(self) -> None:
        with self.assertRaises(RuntimeError):
            build_open_command(Path("point.kml"), system="Plan9")


if __name__ == "__main__":
    unittest.main()
