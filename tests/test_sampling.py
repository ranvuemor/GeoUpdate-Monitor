import unittest

from earth_imagery_watcher.regions import Region
from earth_imagery_watcher.sampling import generate_sample_points, point_in_polygon


class SamplingTests(unittest.TestCase):
    def test_sample_points_are_inside_polygon(self) -> None:
        region = _square_region()

        points = generate_sample_points(region, max_points=5)
        polygon = [(13.0, 52.0), (14.0, 52.0), (14.0, 53.0), (13.0, 53.0), (13.0, 52.0)]

        self.assertEqual(len(points), 5)
        for point in points:
            self.assertTrue(point_in_polygon((point.longitude, point.latitude), polygon))

    def test_max_points_limits_samples(self) -> None:
        points = generate_sample_points(_square_region(), max_points=3)

        self.assertEqual(len(points), 3)


def _square_region() -> Region:
    return Region(
        id="region-1",
        name="Region One",
        geometry_type="Polygon",
        coordinates=[
            [
                [13.0, 52.0],
                [14.0, 52.0],
                [14.0, 53.0],
                [13.0, 53.0],
                [13.0, 52.0],
            ]
        ],
        properties={},
    )


if __name__ == "__main__":
    unittest.main()
