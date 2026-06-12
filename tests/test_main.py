import unittest
from datetime import date

from earth_imagery_watcher.main import (
    check_status,
    delay_for_point,
    normal_date_fields_from_sources,
)
from earth_imagery_watcher.ocr_reader import OcrResult


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

    def test_successful_ocr_date_fields(self) -> None:
        fields = normal_date_fields_from_sources(
            manual_normal_date=None,
            ocr_result=OcrResult(
                raw_text="Imagery Date: 2024-05-12",
                text_blocks=[],
                confidence=0.92,
                parsed_imagery_date=date(2024, 5, 12),
            ),
        )

        self.assertEqual(fields.raw_text, "Imagery Date: 2024-05-12")
        self.assertEqual(fields.parsed_date, date(2024, 5, 12))
        self.assertEqual(fields.confidence, 0.92)
        self.assertEqual(fields.source, "ocr")
        self.assertEqual(check_status(None, None, fields), "ocr")

    def test_ocr_no_date_found_fields(self) -> None:
        fields = normal_date_fields_from_sources(
            manual_normal_date=None,
            ocr_result=OcrResult(raw_text="", text_blocks=[], confidence=None, parsed_imagery_date=None),
        )

        self.assertIsNone(fields.raw_text)
        self.assertIsNone(fields.parsed_date)
        self.assertIsNone(fields.confidence)
        self.assertEqual(fields.source, "ocr")
        self.assertEqual(check_status(None, None, fields), "ocr_no_date")

    def test_ocr_malformed_text_fields(self) -> None:
        fields = normal_date_fields_from_sources(
            manual_normal_date=None,
            ocr_result=OcrResult(
                raw_text="not a date",
                text_blocks=[],
                confidence=0.41,
                parsed_imagery_date=None,
            ),
        )

        self.assertEqual(fields.raw_text, "not a date")
        self.assertIsNone(fields.parsed_date)
        self.assertEqual(fields.confidence, 0.41)
        self.assertEqual(check_status(None, None, fields), "ocr_no_date")

    def test_ocr_parser_recovery_fields(self) -> None:
        fields = normal_date_fields_from_sources(
            manual_normal_date=None,
            ocr_result=OcrResult(
                raw_text="Google\nImagery Date: May 2024",
                text_blocks=[],
                confidence=0.85,
                parsed_imagery_date=date(2024, 5, 1),
            ),
        )

        self.assertEqual(fields.parsed_date, date(2024, 5, 1))
        self.assertEqual(check_status(None, None, fields), "ocr")

    def test_manual_date_takes_precedence_over_ocr(self) -> None:
        fields = normal_date_fields_from_sources(
            manual_normal_date="June 2024",
            ocr_result=OcrResult(
                raw_text="Imagery Date: May 2024",
                text_blocks=[],
                confidence=0.99,
                parsed_imagery_date=date(2024, 5, 1),
            ),
        )

        self.assertEqual(fields.raw_text, "June 2024")
        self.assertEqual(fields.parsed_date, date(2024, 6, 1))
        self.assertIsNone(fields.confidence)
        self.assertEqual(fields.source, "manual")
        self.assertEqual(check_status("June 2024", None, fields), "manual")


if __name__ == "__main__":
    unittest.main()
