from __future__ import annotations

import re
from datetime import date


MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def parse_imagery_date(text: str | None) -> date | None:
    if not text:
        return None

    normalized = " ".join(text.strip().replace(",", " ").split())

    iso_match = re.search(r"\b(20\d{2}|19\d{2})[-/](\d{1,2})(?:[-/](\d{1,2}))?\b", normalized)
    if iso_match:
        year = int(iso_match.group(1))
        month = int(iso_match.group(2))
        day = int(iso_match.group(3) or 1)
        return date(year, month, day)

    month_year_match = re.search(
        r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2}\s+)?(20\d{2}|19\d{2})\b",
        normalized,
        flags=re.IGNORECASE,
    )
    if month_year_match:
        month_name = month_year_match.group(1).lower()
        day = int((month_year_match.group(2) or "1").strip())
        year = int(month_year_match.group(3))
        month = MONTHS.get(month_name)
        if month:
            return date(year, month, day)

    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", normalized)
    if year_match:
        return date(int(year_match.group(1)), 1, 1)

    return None


def effective_latest_date(normal: date | None, historical_latest: date | None) -> date | None:
    dates = [value for value in [normal, historical_latest] if value is not None]
    return max(dates) if dates else None
