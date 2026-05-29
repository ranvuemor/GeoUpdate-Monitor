import unittest

from earth_imagery_watcher.screenshot_capture import bottom_right_crop_box


class ScreenshotCaptureTests(unittest.TestCase):
    def test_bottom_right_crop_box_uses_requested_size(self) -> None:
        self.assertEqual(bottom_right_crop_box(1920, 1080, 500, 120), (1420, 960, 1920, 1080))

    def test_bottom_right_crop_box_clamps_to_image_size(self) -> None:
        self.assertEqual(bottom_right_crop_box(400, 90, 500, 120), (0, 0, 400, 90))

    def test_bottom_right_crop_box_rejects_invalid_crop_size(self) -> None:
        with self.assertRaises(ValueError):
            bottom_right_crop_box(1920, 1080, 0, 120)

    def test_bottom_right_crop_box_rejects_invalid_image_size(self) -> None:
        with self.assertRaises(ValueError):
            bottom_right_crop_box(0, 1080, 500, 120)


if __name__ == "__main__":
    unittest.main()
