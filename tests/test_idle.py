import unittest

from earth_imagery_watcher.idle import idle_minutes_to_seconds, wait_until_idle


class IdleTests(unittest.TestCase):
    def test_idle_minutes_to_seconds(self) -> None:
        self.assertEqual(idle_minutes_to_seconds(10), 600.0)
        self.assertEqual(idle_minutes_to_seconds(1.5), 90.0)

    def test_wait_until_idle_loops_until_threshold(self) -> None:
        idle_values = iter([30.0, 120.0, 600.0])
        sleeps: list[float] = []
        messages: list[str] = []

        wait_until_idle(
            idle_seconds_required=600.0,
            check_interval_seconds=15.0,
            get_idle_seconds_fn=lambda: next(idle_values),
            sleep_fn=sleeps.append,
            print_fn=messages.append,
        )

        self.assertEqual(sleeps, [15.0, 15.0])
        self.assertIn("Waiting until system is idle for 10 minutes...", messages)
        self.assertIn("Current idle time: 0.5 minutes", messages)
        self.assertIn("Current idle time: 2.0 minutes", messages)
        self.assertIn("Current idle time: 10.0 minutes", messages)
        self.assertIn("Idle threshold reached. Starting checks.", messages)

    def test_wait_until_idle_raises_when_idle_detection_is_unsupported(self) -> None:
        with self.assertRaises(RuntimeError):
            wait_until_idle(
                idle_seconds_required=60.0,
                check_interval_seconds=15.0,
                get_idle_seconds_fn=lambda: None,
                sleep_fn=lambda seconds: None,
                print_fn=lambda message: None,
            )


if __name__ == "__main__":
    unittest.main()
