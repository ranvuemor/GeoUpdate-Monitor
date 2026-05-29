from __future__ import annotations

import argparse
import time
from datetime import date
from pathlib import Path

from .database import CheckResult, Database, utc_now_iso
from .date_parser import effective_latest_date, parse_imagery_date
from .earth_controller import DefaultFileAssociationEarthController
from .idle import idle_minutes_to_seconds, wait_until_idle
from .kml import write_temp_kml
from .regions import load_geojson
from .sampling import SamplePoint, generate_sample_points
from .screenshot_capture import (
    capture_bottom_right_crop,
    find_google_earth_window,
    prepare_for_screenshot,
)


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
    run_parser.add_argument("--range", type=int, default=100000, dest="range_meters", help="Google Earth LookAt range in meters.")
    run_parser.add_argument("--dry-run", action="store_true", help="Generate KML and skip date storage.")
    run_parser.add_argument("--open-earth", action="store_true", help="Open each generated KML using the OS default file association.")
    run_parser.add_argument(
        "--capture-date-crop",
        action="store_true",
        help="Capture and save the bottom-right imagery date area after opening each KML.",
    )
    run_parser.add_argument(
        "--crop-output-dir",
        type=Path,
        default=Path("screenshots"),
        help="Directory for saved bottom-right date crops.",
    )
    run_parser.add_argument("--crop-width", type=int, default=500, help="Width of the bottom-right crop in pixels.")
    run_parser.add_argument("--crop-height", type=int, default=120, help="Height of the bottom-right crop in pixels.")
    run_parser.add_argument(
        "--crop-bottom-offset",
        type=int,
        default=0,
        help="Advanced fallback: pixels to move the crop upward from the target bottom edge.",
    )
    run_parser.add_argument(
        "--pre-screenshot-delay",
        type=float,
        default=1.0,
        help="Delay after moving the mouse away from the bottom edge and before taking a screenshot.",
    )
    run_parser.add_argument(
        "--point-delay-seconds",
        type=float,
        default=5,
        help="Delay between opening sample points when --open-earth is used.",
    )
    run_parser.add_argument(
        "--first-point-delay-seconds",
        type=float,
        default=None,
        help="Optional extra delay before capturing the first sample point.",
    )
    run_parser.add_argument(
        "--capture-retries",
        type=int,
        default=1,
        help="Number of date crop capture attempts per point.",
    )
    run_parser.add_argument(
        "--capture-retry-delay-seconds",
        type=float,
        default=2.0,
        help="Delay between date crop capture retry attempts.",
    )
    run_parser.add_argument(
        "--manual-normal-date",
        help="Temporary MVP input for the normal/default imagery date, for example 'May 2024'.",
    )
    run_parser.add_argument(
        "--manual-historical-date",
        help="Temporary MVP input for the latest historical imagery date, for example 'June 2024'.",
    )
    run_parser.add_argument(
        "--wait-until-idle",
        action="store_true",
        help="Wait until the system has been idle before opening Google Earth or capturing crops.",
    )
    run_parser.add_argument(
        "--idle-minutes",
        type=float,
        default=10,
        help="Required system idle time before starting checks when --wait-until-idle is used.",
    )
    run_parser.add_argument(
        "--idle-check-interval-seconds",
        type=float,
        default=15,
        help="Polling interval while waiting for system idle time.",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    if args.wait_until_idle:
        wait_until_idle(
            idle_seconds_required=idle_minutes_to_seconds(args.idle_minutes),
            check_interval_seconds=args.idle_check_interval_seconds,
        )

    regions = load_geojson(args.geojson)
    database = Database(args.db)
    earth_controller = DefaultFileAssociationEarthController() if args.open_earth else None
    if not args.dry_run:
        database.initialize()

    print(f"Loaded {len(regions)} region(s) from {args.geojson}")
    point_index = 0

    for region in regions:
        points = generate_sample_points(region, max_points=args.max_points)
        print(f"{region.name}: generated {len(points)} sample point(s)")

        for point in points:
            selected_delay = delay_for_point(
                point_index=point_index,
                point_delay_seconds=args.point_delay_seconds,
                first_point_delay_seconds=args.first_point_delay_seconds,
            )
            kml_path = write_temp_kml(point, range_meters=args.range_meters)
            print(f"  {point.id}: KML -> {kml_path}")

            if earth_controller:
                print(f"  {point.id}: opening KML with OS default application")
                earth_controller.open_kml(kml_path)
                if selected_delay > 0:
                    print(f"  {point.id}: waiting {selected_delay:g} second(s) before capture/check")
                    time.sleep(selected_delay)

            if args.capture_date_crop:
                window = find_google_earth_window()
                if window:
                    print(
                        f"  {point.id}: using Google Earth window crop "
                        f"title={window.title!r}, bounds=({window.left}, {window.top}, {window.width}, {window.height})"
                    )
                else:
                    print(f"  {point.id}: Google Earth window not found; using full-screen crop fallback")
                print(
                    f"  {point.id}: crop settings width={args.crop_width}, "
                    f"height={args.crop_height}, bottom_offset={args.crop_bottom_offset}"
                )
                for attempt in range(1, args.capture_retries + 1):
                    if attempt > 1 and args.capture_retry_delay_seconds > 0:
                        print(
                            f"  {point.id}: waiting {args.capture_retry_delay_seconds:g} "
                            "second(s) before retry"
                        )
                        time.sleep(args.capture_retry_delay_seconds)
                    print(f"  {point.id}: capture attempt {attempt}/{args.capture_retries}")
                    prepare_for_screenshot(window, delay_seconds=args.pre_screenshot_delay)
                    capture_result = capture_bottom_right_crop(
                        output_dir=args.crop_output_dir,
                        region_name=region.name,
                        sample_id=point.id,
                        crop_width=args.crop_width,
                        crop_height=args.crop_height,
                        crop_bottom_offset=args.crop_bottom_offset,
                        window_bounds=window,
                        attempt=attempt if args.capture_retries > 1 else None,
                    )
                    mode = "window" if capture_result.used_window_crop else "full-screen fallback"
                    print(f"  {point.id}: capture mode={mode}, crop_box={capture_result.crop_box}")
                    print(f"  {point.id}: saved date crop -> {capture_result.path}")

            point_index += 1

            if args.dry_run:
                continue

            normal_date = parse_imagery_date(args.manual_normal_date)
            historical_date = parse_imagery_date(args.manual_historical_date)
            latest = effective_latest_date(normal_date, historical_date)
            previous = database.latest_for_sample(point.id, region_id=region.id)
            changed = _is_newer(latest, _date_from_iso(previous.effective_latest_date) if previous else None)
            status = "manual" if args.manual_normal_date or args.manual_historical_date else "no_date"

            database.save_check(
                CheckResult(
                    region_id=point.region_id,
                    region_name=region.name,
                    sample_id=point.id,
                    latitude=point.latitude,
                    longitude=point.longitude,
                    normal_imagery_date=_date_to_iso(normal_date),
                    historical_latest_date=_date_to_iso(historical_date),
                    effective_latest_date=_date_to_iso(latest),
                    normal_raw_text=args.manual_normal_date,
                    historical_raw_text=args.manual_historical_date,
                    normal_confidence=None,
                    historical_confidence=None,
                    status=status,
                    zoom_range_m=args.range_meters,
                    checked_at=utc_now_iso(),
                )
            )

            _print_change_status(point, latest, previous, changed)

    return 0


def delay_for_point(
    point_index: int,
    point_delay_seconds: float,
    first_point_delay_seconds: float | None,
) -> float:
    if point_index == 0 and first_point_delay_seconds is not None:
        return first_point_delay_seconds
    return point_delay_seconds


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
    if getattr(args, "capture_date_crop", False) and not getattr(args, "open_earth", False):
        parser.error("--capture-date-crop requires --open-earth so the crop follows a generated KML open.")
    if getattr(args, "crop_bottom_offset", 0) < 0:
        parser.error("--crop-bottom-offset must be zero or greater.")
    if getattr(args, "pre_screenshot_delay", 0) < 0:
        parser.error("--pre-screenshot-delay must be zero or greater.")
    if getattr(args, "first_point_delay_seconds", None) is not None and args.first_point_delay_seconds < 0:
        parser.error("--first-point-delay-seconds must be zero or greater.")
    if getattr(args, "point_delay_seconds", 0) < 0:
        parser.error("--point-delay-seconds must be zero or greater.")
    if getattr(args, "capture_retries", 1) < 1:
        parser.error("--capture-retries must be at least 1.")
    if getattr(args, "capture_retry_delay_seconds", 0) < 0:
        parser.error("--capture-retry-delay-seconds must be zero or greater.")
    if getattr(args, "idle_minutes", 0) < 0:
        parser.error("--idle-minutes must be zero or greater.")
    if getattr(args, "idle_check_interval_seconds", 0) < 0:
        parser.error("--idle-check-interval-seconds must be zero or greater.")
    if args.command == "run":
        return run(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
