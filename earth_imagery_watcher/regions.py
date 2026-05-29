from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class Region:
    id: str
    name: str
    geometry_type: str
    coordinates: Any
    properties: dict[str, Any]


SUPPORTED_GEOMETRIES = {"Polygon", "MultiPolygon"}


def load_geojson(path: str | Path) -> list[Region]:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if data.get("type") == "FeatureCollection":
        features = data.get("features", [])
    elif data.get("type") == "Feature":
        features = [data]
    else:
        raise ValueError("GeoJSON must be a Feature or FeatureCollection.")

    regions: list[Region] = []
    for index, feature in enumerate(features, start=1):
        geometry = feature.get("geometry") or {}
        geometry_type = geometry.get("type")
        if geometry_type not in SUPPORTED_GEOMETRIES:
            continue

        properties = feature.get("properties") or {}
        feature_id = str(feature.get("id") or properties.get("id") or f"region-{index}")
        name = str(properties.get("name") or feature_id)
        regions.append(
            Region(
                id=feature_id,
                name=name,
                geometry_type=geometry_type,
                coordinates=geometry.get("coordinates"),
                properties=properties,
            )
        )

    if not regions:
        raise ValueError("No supported Polygon or MultiPolygon features found.")
    return regions


def polygon_rings(region: Region) -> Iterable[list[list[float]]]:
    if region.geometry_type == "Polygon":
        yield from [region.coordinates]
        return

    for polygon in region.coordinates:
        yield polygon
