from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .database import CheckResult, Database, utc_now_iso
from .date_parser import effective_latest_date, parse_imagery_date
from .kml import write_temp_kml
from .regions import load_geojson
from .sampling import SamplePoint, generate_sample_points


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="earth-imagery-watcher",
        description="Date-only Google Earth Pro imagery update monitor.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Check GeoJSON regions once.")
    run_parser.add_argument("geojson", type=Path, help="Path to a GeoJSON FeatureCollection.")
    run_parser.add_argument("--db", type=Path, default=Path("watcher.sqlite"), help="SQLite database path.")
    run_parser.add_argument("--max-points", type=int, default=5, help="Maximum sample points per region.")
    run_parser.add_argument("--range", type=int, default=1200, dest="range_meters", help="Google Earth LookAt range in meters.")
    run_parser.add_argument("--dry-run", action="store_true", help="Generate KML and skip date storage.")
    run_parser.add_argument(
        "--manual-date",
        help="Temporary MVP input for a detected imagery date, for example 'May 2024'.",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    regions = load_geojson(args.geojson)
    database = Database(args.db)
    if not args.dry_run:
        database.initialize()

    print(f"Loaded {len(regions)} region(s) from {args.geojson}")

    for region in regions:
        points = generate_sample_points(region, max_points=args.max_points)
        print(f"{region.name}: generated {len(points)} sample point(s)")

        for point in points:
            kml_path = write_temp_kml(point, range_meters=args.range_meters)
            print(f"  {point.id}: KML -> {kml_path}")

            if args.dry_run:
                continue

            normal_date = parse_imagery_date(args.manual_date)
            historical_date = None
            latest = effective_latest_date(normal_date, historical_date)
            previous = database.latest_for_sample(point.id)
            changed = _is_newer(latest, _date_from_iso(previous.effective_latest_date) if previous else None)

            database.save_check(
                CheckResult(
                    region_id=point.region_id,
                    sample_id=point.id,
                    latitude=point.latitude,
                    longitude=point.longitude,
                    normal_date=_date_to_iso(normal_date),
                    historical_latest_date=_date_to_iso(historical_date),
                    effective_latest_date=_date_to_iso(latest),
                    ocr_confidence=None,
                    zoom_range_meters=args.range_meters,
                    checked_at=utc_now_iso(),
                )
            )

            _print_change_status(point, latest, previous, changed)

    return 0


def _print_change_status(
    point: SamplePoint,
    latest: date | None,
    previous: CheckResult | None,
    changed: bool,
) -> None:
    previous_date = previous.effective_latest_date if previous else None
    if changed:
        print(f"  {point.id}: newer imagery date detected ({previous_date} -> {_date_to_iso(latest)})")
    else:
        print(f"  {point.id}: no newer date (latest={_date_to_iso(latest)}, previous={previous_date})")


def _is_newer(current: date | None, previous: date | None) -> bool:
    return current is not None and (previous is None or current > previous)


def _date_to_iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _date_from_iso(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "run":
        return run(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
