import unittest
import xml.etree.ElementTree as ET

from earth_imagery_watcher.kml import render_point_kml
from earth_imagery_watcher.sampling import SamplePoint


class KmlTests(unittest.TestCase):
    def test_default_kml_contains_coordinates_and_range(self) -> None:
        point = SamplePoint(id="sample-id", region_id="region-1", latitude=52.5, longitude=13.4)

        kml = render_point_kml(point)

        self.assertIn("13.40000000,52.50000000,0", kml)
        self.assertIn("<range>100000</range>", kml)

    def test_kml_contains_lookat_section(self) -> None:
        point = SamplePoint(id="sample-id", region_id="region-1", latitude=52.5, longitude=13.4)

        kml = render_point_kml(point)

        self.assertIn("<LookAt>", kml)
        self.assertIn("</LookAt>", kml)

    def test_kml_is_parseable_google_earth_structure(self) -> None:
        point = SamplePoint(id="sample-id", region_id="region-1", latitude=52.5, longitude=13.4)

        root = ET.fromstring(render_point_kml(point))
        namespace = {"kml": "http://www.opengis.net/kml/2.2"}

        self.assertEqual(root.tag, "{http://www.opengis.net/kml/2.2}kml")
        self.assertIsNotNone(root.find(".//kml:Placemark", namespace))
        self.assertIsNotNone(root.find(".//kml:Placemark/kml:LookAt", namespace))
        self.assertIsNotNone(root.find(".//kml:Placemark/kml:Point/kml:coordinates", namespace))


if __name__ == "__main__":
    unittest.main()
