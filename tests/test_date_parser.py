from datetime import date
import unittest

from earth_imagery_watcher.date_parser import effective_latest_date, parse_imagery_date


class DateParserTests(unittest.TestCase):
    def test_month_year(self) -> None:
        self.assertEqual(parse_imagery_date("May 2024"), date(2024, 5, 1))

    def test_imagery_date_month_year(self) -> None:
        self.assertEqual(parse_imagery_date("Imagery Date: May 2024"), date(2024, 5, 1))

    def test_slash_month_year(self) -> None:
        self.assertEqual(parse_imagery_date("5/2024"), date(2024, 5, 1))

    def test_year_month(self) -> None:
        self.assertEqual(parse_imagery_date("2024-05"), date(2024, 5, 1))

    def test_year_month_day(self) -> None:
        self.assertEqual(parse_imagery_date("2024-05-12"), date(2024, 5, 12))

    def test_us_non_ambiguous_slash_date(self) -> None:
        self.assertEqual(parse_imagery_date("12/14/2024"), date(2024, 12, 14))

    def test_eu_non_ambiguous_slash_date(self) -> None:
        self.assertEqual(parse_imagery_date("14/12/2024"), date(2024, 12, 14))

    def test_ambiguous_slash_date_returns_none(self) -> None:
        self.assertIsNone(parse_imagery_date("05/06/2024"))

    def test_year_only(self) -> None:
        self.assertEqual(parse_imagery_date("2024"), date(2024, 1, 1))

    def test_effective_latest_ignores_missing_values(self) -> None:
        self.assertEqual(effective_latest_date(None, date(2024, 6, 1)), date(2024, 6, 1))
        self.assertEqual(effective_latest_date(date(2024, 5, 1), None), date(2024, 5, 1))
        self.assertIsNone(effective_latest_date(None, None))


if __name__ == "__main__":
    unittest.main()
