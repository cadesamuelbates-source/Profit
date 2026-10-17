"""US federal holidays, including observed dates (5 U.S.C. 6103).

A holiday that falls on a Saturday is observed the Friday before; one that falls
on a Sunday is observed the Monday after. New Year's Day on a Saturday is
therefore observed on December 31 of the *previous* year.
"""

from __future__ import annotations

import datetime as dt
from functools import lru_cache

MON, TUE, WED, THU, FRI, SAT, SUN = range(7)


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> dt.date:
    first = dt.date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + dt.timedelta(days=offset + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> dt.date:
    nxt = dt.date(year + (month == 12), month % 12 + 1, 1)
    last = nxt - dt.timedelta(days=1)
    return last - dt.timedelta(days=(last.weekday() - weekday) % 7)


def _observed(day: dt.date) -> dt.date:
    if day.weekday() == SAT:
        return day - dt.timedelta(days=1)
    if day.weekday() == SUN:
        return day + dt.timedelta(days=1)
    return day


def _actual_holidays(year: int) -> dict[dt.date, str]:
    days = {
        dt.date(year, 1, 1): "New Year's Day",
        _nth_weekday(year, 1, MON, 3): "Birthday of Martin Luther King, Jr.",
        _nth_weekday(year, 2, MON, 3): "Washington's Birthday",
        _last_weekday(year, 5, MON): "Memorial Day",
        dt.date(year, 7, 4): "Independence Day",
        _nth_weekday(year, 9, MON, 1): "Labor Day",
        _nth_weekday(year, 10, MON, 2): "Columbus Day",
        dt.date(year, 11, 11): "Veterans Day",
        _nth_weekday(year, 11, THU, 4): "Thanksgiving Day",
        dt.date(year, 12, 25): "Christmas Day",
    }
    if year >= 2021:
        days[dt.date(year, 6, 19)] = "Juneteenth National Independence Day"
    return days


@lru_cache(maxsize=64)
def federal_holidays(year: int) -> dict[dt.date, str]:
    """All actual and observed federal holiday dates that fall in `year`."""
    result: dict[dt.date, str] = {}
    for y in (year - 1, year, year + 1):
        for day, name in _actual_holidays(y).items():
            for candidate, label in ((day, name), (_observed(day), f"{name} (observed)")):
                if candidate.year == year:
                    result.setdefault(candidate, label)
    return result


def is_federal_holiday(day: dt.date) -> bool:
    return day in federal_holidays(day.year)
