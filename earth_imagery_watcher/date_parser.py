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
    normalized = re.sub(r"(?i)\bimagery\s+date\s*:\s*", "", normalized).strip()

    iso_match = re.search(r"\b(20\d{2}|19\d{2})[-](\d{1,2})(?:[-](\d{1,2}))?\b", normalized)
    if iso_match:
        year = int(iso_match.group(1))
        month = int(iso_match.group(2))
        day = int(iso_match.group(3) or 1)
        return _safe_date(year, month, day)

    slash_full_match = re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2}|19\d{2})\b", normalized)
    if slash_full_match:
        first = int(slash_full_match.group(1))
        second = int(slash_full_match.group(2))
        year = int(slash_full_match.group(3))
        if first <= 12 and second <= 12:
            return None
        if first > 12 and second <= 12:
            return _safe_date(year, second, first)
        if second > 12 and first <= 12:
            return _safe_date(year, first, second)
        return None

    slash_month_year_match = re.search(r"\b(\d{1,2})/(20\d{2}|19\d{2})\b", normalized)
    if slash_month_year_match:
        month = int(slash_month_year_match.group(1))
        year = int(slash_month_year_match.group(2))
        return _safe_date(year, month, 1)

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
            return _safe_date(year, month, day)

    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", normalized)
    if year_match:
        return date(int(year_match.group(1)), 1, 1)

    return None


def effective_latest_date(normal: date | None, historical_latest: date | None) -> date | None:
    dates = [value for value in [normal, historical_latest] if value is not None]
    return max(dates) if dates else None


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None
