import unittest

from earth_imagery_watcher.main import delay_for_point


class MainTests(unittest.TestCase):
    def test_first_point_uses_first_point_delay_when_provided(self) -> None:
        self.assertEqual(
            delay_for_point(
                point_index=0,
                point_delay_seconds=8.0,
                first_point_delay_seconds=15.0,
            ),
            15.0,
        )

    def test_later_points_use_regular_point_delay(self) -> None:
        self.assertEqual(
            delay_for_point(
                point_index=1,
                point_delay_seconds=8.0,
                first_point_delay_seconds=15.0,
            ),
            8.0,
        )

    def test_all_points_use_regular_delay_when_first_point_delay_is_none(self) -> None:
        self.assertEqual(
            delay_for_point(
                point_index=0,
                point_delay_seconds=8.0,
                first_point_delay_seconds=None,
            ),
            8.0,
        )
        self.assertEqual(
            delay_for_point(
                point_index=3,
                point_delay_seconds=8.0,
                first_point_delay_seconds=None,
            ),
            8.0,
        )


if __name__ == "__main__":
    unittest.main()
