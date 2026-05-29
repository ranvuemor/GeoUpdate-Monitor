from __future__ import annotations

from dataclasses import dataclass
from itertools import count

from .regions import Region, polygon_rings


@dataclass(frozen=True)
class SamplePoint:
    id: str
    region_id: str
    latitude: float
    longitude: float


def generate_sample_points(region: Region, max_points: int = 5) -> list[SamplePoint]:
    if max_points < 1:
        raise ValueError("max_points must be at least 1.")

    candidates: list[tuple[float, float]] = []
    for rings in polygon_rings(region):
        converted_rings = [
            [(float(lon), float(lat)) for lon, lat, *_ in ring]
            for ring in rings
        ]
        candidates.extend(_polygon_candidates(converted_rings, max_points))

    unique: list[tuple[float, float]] = []
    seen: set[tuple[float, float]] = set()
    for lon, lat in candidates:
        key = (round(lon, 7), round(lat, 7))
        if key not in seen:
            seen.add(key)
            unique.append((lon, lat))
        if len(unique) >= max_points:
            break

    return [
        SamplePoint(
            id=f"{region.id}-sample-{index}",
            region_id=region.id,
            latitude=lat,
            longitude=lon,
        )
        for index, (lon, lat) in zip(count(1), unique)
    ]


def _polygon_candidates(
    rings: list[list[tuple[float, float]]],
    max_points: int,
) -> list[tuple[float, float]]:
    outer_ring = rings[0]
    centroid = _centroid(outer_ring)
    min_lon, min_lat, max_lon, max_lat = _bounds(outer_ring)
    width = max_lon - min_lon
    height = max_lat - min_lat

    raw_candidates = [
        centroid,
        (min_lon + width * 0.25, min_lat + height * 0.25),
        (min_lon + width * 0.75, min_lat + height * 0.25),
        (min_lon + width * 0.25, min_lat + height * 0.75),
        (min_lon + width * 0.75, min_lat + height * 0.75),
    ]

    candidates = [point for point in raw_candidates if point_in_rings(point, rings)]
    if candidates:
        return candidates[:max_points]

    grid_candidates = _grid_candidates(min_lon, min_lat, max_lon, max_lat)
    candidates = [point for point in grid_candidates if point_in_rings(point, rings)]
    if candidates:
        return candidates[:max_points]

    raise ValueError("Could not generate a sample point inside polygon.")


def point_in_rings(point: tuple[float, float], rings: list[list[tuple[float, float]]]) -> bool:
    if not point_in_polygon(point, rings[0]):
        return False
    return not any(point_in_polygon(point, hole) for hole in rings[1:])


def point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    j = len(polygon) - 1

    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        intersects = (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
        if intersects:
            inside = not inside
        j = i

    return inside


def _bounds(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    lons = [point[0] for point in points]
    lats = [point[1] for point in points]
    return min(lons), min(lats), max(lons), max(lats)


def _centroid(points: list[tuple[float, float]]) -> tuple[float, float]:
    closed = points if points[0] == points[-1] else [*points, points[0]]
    area = 0.0
    cx = 0.0
    cy = 0.0

    for index in range(len(closed) - 1):
        x0, y0 = closed[index]
        x1, y1 = closed[index + 1]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross

    area *= 0.5
    if abs(area) < 1e-12:
        return points[0]

    return cx / (6.0 * area), cy / (6.0 * area)


def _grid_candidates(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
) -> list[tuple[float, float]]:
    candidates: list[tuple[float, float]] = []
    steps = 8
    for y_index in range(1, steps):
        for x_index in range(1, steps):
            lon = min_lon + (max_lon - min_lon) * x_index / steps
            lat = min_lat + (max_lat - min_lat) * y_index / steps
            candidates.append((lon, lat))
    return candidates
