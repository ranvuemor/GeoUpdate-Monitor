import unittest
from datetime import date

from earth_imagery_watcher.ocr_reader import parse_paddleocr_output


class OcrReaderTests(unittest.TestCase):
    def test_parse_legacy_paddleocr_output(self) -> None:
        raw_output = [
            [
                [[[0, 0], [100, 0], [100, 20], [0, 20]], ("Imagery Date: May 2024", 0.91)],
                [[[0, 25], [80, 25], [80, 45], [0, 45]], ("Google", 0.75)],
            ]
        ]

        result = parse_paddleocr_output(raw_output)

        self.assertEqual(result.raw_text, "Imagery Date: May 2024\nGoogle")
        self.assertEqual(len(result.text_blocks), 2)
        self.assertAlmostEqual(result.confidence or 0, 0.83)
        self.assertEqual(result.parsed_imagery_date, date(2024, 5, 1))

    def test_parse_dict_paddleocr_output(self) -> None:
        raw_output = [
            {
                "rec_texts": ["Imagery Date:", "2024-05-12"],
                "rec_scores": [0.8, 0.95],
                "rec_boxes": [[0, 0, 100, 20], [110, 0, 220, 20]],
            }
        ]

        result = parse_paddleocr_output(raw_output)

        self.assertEqual(result.raw_text, "Imagery Date:\n2024-05-12")
        self.assertEqual(len(result.text_blocks), 2)
        self.assertAlmostEqual(result.confidence or 0, 0.875)
        self.assertEqual(result.parsed_imagery_date, date(2024, 5, 12))

    def test_parse_empty_output(self) -> None:
        result = parse_paddleocr_output([])

        self.assertEqual(result.raw_text, "")
        self.assertEqual(result.text_blocks, [])
        self.assertIsNone(result.confidence)
        self.assertIsNone(result.parsed_imagery_date)


if __name__ == "__main__":
    unittest.main()
