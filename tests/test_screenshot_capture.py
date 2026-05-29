import unittest

from earth_imagery_watcher.screenshot_capture import WindowBounds, bottom_right_crop_box


class ScreenshotCaptureTests(unittest.TestCase):
    def test_bottom_right_crop_box_uses_requested_size(self) -> None:
        self.assertEqual(bottom_right_crop_box(1920, 1080, 500, 120), (1420, 960, 1920, 1080))

    def test_bottom_right_crop_box_without_window_uses_full_screen(self) -> None:
        self.assertEqual(
            bottom_right_crop_box(1920, 1080, 500, 120, window_bounds=None),
            (1420, 960, 1920, 1080),
        )

    def test_bottom_right_crop_box_uses_bottom_offset(self) -> None:
        self.assertEqual(
            bottom_right_crop_box(1920, 1080, 500, 120, crop_bottom_offset=60),
            (1420, 900, 1920, 1020),
        )

    def test_bottom_right_crop_box_uses_window_bounds(self) -> None:
        window = WindowBounds(left=100, top=50, width=800, height=600, title="Google Earth Pro")

        self.assertEqual(
            bottom_right_crop_box(1920, 1080, 500, 120, window_bounds=window),
            (400, 530, 900, 650),
        )

    def test_bottom_right_crop_box_uses_window_bounds_with_offset(self) -> None:
        window = WindowBounds(left=100, top=50, width=800, height=600, title="Google Earth Pro")

        self.assertEqual(
            bottom_right_crop_box(
                1920,
                1080,
                500,
                120,
                crop_bottom_offset=30,
                window_bounds=window,
            ),
            (400, 500, 900, 620),
        )

    def test_bottom_right_crop_box_clamps_to_image_size(self) -> None:
        self.assertEqual(bottom_right_crop_box(400, 90, 500, 120), (0, 0, 400, 90))

    def test_bottom_right_crop_box_clamps_when_crop_larger_than_window(self) -> None:
        window = WindowBounds(left=100, top=50, width=800, height=600, title="Google Earth Pro")

        self.assertEqual(
            bottom_right_crop_box(1920, 1080, 1000, 1000, window_bounds=window),
            (100, 50, 900, 650),
        )

    def test_bottom_right_crop_box_clamps_with_oversized_crop_and_offset(self) -> None:
        self.assertEqual(
            bottom_right_crop_box(400, 90, 500, 120, crop_bottom_offset=20),
            (0, 0, 400, 70),
        )

    def test_bottom_right_crop_box_rejects_offset_larger_than_image_height(self) -> None:
        with self.assertRaises(ValueError):
            bottom_right_crop_box(1920, 1080, 500, 120, crop_bottom_offset=1080)

    def test_bottom_right_crop_box_rejects_invalid_crop_size(self) -> None:
        with self.assertRaises(ValueError):
            bottom_right_crop_box(1920, 1080, 0, 120)

    def test_bottom_right_crop_box_rejects_invalid_image_size(self) -> None:
        with self.assertRaises(ValueError):
            bottom_right_crop_box(0, 1080, 500, 120)


if __name__ == "__main__":
    unittest.main()
