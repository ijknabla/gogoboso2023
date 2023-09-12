from __future__ import annotations

import re
from collections.abc import Generator, Iterable
from datetime import date
from sqlite3 import Cursor
from typing import TypeVar

from .area import get_areas
from .types import BootOption, Spot

_T = TypeVar("_T")


def create_and_insert(
    cursor: Cursor,
    boot_option: BootOption,
    spots: list[Spot],
) -> None:
    cursor.execute(
        """
CREATE TABLE spot_addresses
(
    spot_id INTEGER PRIMARY KEY,
    spot_address TEXT NOT NULL
)
        """
    )
    cursor.executemany(
        """
INSERT INTO spot_addresses
VALUES (?, ?)
        """,
        [(spot["id"], spot["address"]) for spot in spots],
    )

    cursor.execute(
        """
CREATE TABLE spot_areas
(
    spot_id INTEGER,
    area_index INTEGER,
    area_id INTEGER NOT NULL,
    PRIMARY KEY(spot_id, area_index)
)
        """
    )

    areas = {k: v for v, k in get_areas(boot_option).items() if k not in {"千葉市"}}
    pattern = re.compile("|".join(areas))
    cursor.executemany(
        """
INSERT INTO spot_areas
VALUES (?, ?, ?)
        """,
        [
            (spot["id"], index, areas[area])
            for spot in spots
            for index, area in enumerate(
                iter_unique(pattern.findall(_normalize_address(spot["address"])))
            )
        ],
    )

    cursor.execute(
        """
CREATE TABLE spot_googlemap_uris
(
    spot_id INTEGER PRIMARY KEY,
    spot_googlemap_uri TEXT NOT NULL
)
        """
    )
    cursor.executemany(
        """
INSERT INTO spot_googlemap_uris
VALUES (?, ?)
        """,
        [(spot["id"], spot["googlemap_uri"]) for spot in spots],
    )

    cursor.execute(
        """
CREATE TABLE spot_latitudes
(
    spot_id INTEGER PRIMARY KEY,
    spot_latitude REAL NOT NULL
)
        """
    )
    cursor.executemany(
        """
INSERT INTO spot_latitudes
VALUES (?, ?)
        """,
        [(spot["spotId"], spot["spotLat"]) for spot in boot_option["stampRallySpots"]],
    )

    cursor.execute(
        """
CREATE TABLE spot_link_uris
(
    spot_id INTEGER PRIMARY KEY,
    spot_link_uri TEXT NOT NULL
)
        """
    )
    cursor.executemany(
        """
INSERT INTO spot_link_uris
VALUES (?, ?)
        """,
        [(spot["id"], spot["link_uri"]) for spot in spots if "link_uri" in spot],
    )

    cursor.execute(
        """
CREATE TABLE spot_longitudes
(
    spot_id INTEGER PRIMARY KEY,
    spot_longitude REAL NOT NULL
)
        """
    )
    cursor.executemany(
        """
INSERT INTO spot_longitudes
VALUES (?, ?)
        """,
        [(spot["spotId"], spot["spotLng"]) for spot in boot_option["stampRallySpots"]],
    )

    cursor.execute(
        """
CREATE TABLE spot_names
(
    spot_id INTEGER PRIMARY KEY,
    spot_name TEXT NOT NULL
)
        """
    )
    cursor.executemany(
        """
INSERT INTO spot_names
VALUES (?, ?)
        """,
        [(spot["id"], spot["name"]) for spot in spots],
    )

    cursor.execute(
        """
CREATE TABLE spot_subtitles
(
    spot_id INTEGER PRIMARY KEY,
    spot_subtitle TEXT NOT NULL
)
        """
    )
    cursor.executemany(
        """
INSERT INTO spot_subtitles
VALUES (?, ?)
        """,
        [(spot["id"], spot["subtitle"]) for spot in spots if "subtitle" in spot],
    )

    cursor.execute(
        """
CREATE TABLE spot_periods
(
    spot_id INTEGER,
    spot_period_index INTEGER NOT NULL,
    spot_period_begin DATE NOT NULL,
    spot_period_end DATE NOT NULL,
    PRIMARY KEY(spot_id, spot_period_index)
)
        """
    )
    cursor.executemany(
        """
INSERT INTO spot_periods
VALUES (?, ?, ?, ?)
        """,
        [
            (spot["id"], index, begin, end)
            for spot in spots
            if "subtitle" in spot and "開催期間" in spot["subtitle"]
            for index, (begin, end) in enumerate(sorted(iter_unique(iter_period(spot["subtitle"]))))
        ],
    )


def _normalize_address(address: str) -> str:
    return address.replace("ヶ", "ケ").replace("舘", "館").replace("印西市中央区", "印西市中央")


def iter_unique(iterable: Iterable[_T]) -> Generator[_T, None, None]:
    already = set[_T]()
    for item in iterable:
        try:
            if item not in already:
                yield item
        finally:
            already.add(item)


def iter_period(subtitle: str) -> Generator[tuple[date, date], None, None]:
    begin = None

    year = "2023"

    for matched in re.finditer(
        r"(?P<is_end>～)?((?P<year>\d+)年)?((?P<month>\d+)月)?((?P<day>\d+)日)?", subtitle
    ):
        match matched.group():
            case "":
                continue
            case "～":
                continue
        match matched.group("year"):
            case None:
                ...
            case year:
                ...

        match matched.group("month"):
            case None:
                ...
            case month:
                ...

        if (year, month) == ("2024", "3"):
            year, month, day = "2024", "3", "31"
        else:
            match matched.group("day"):
                case None:
                    raise NotImplementedError()
                case day:
                    ...

        current = date(int(year), int(month), int(day))

        match matched.group("is_end"):
            case None:
                if begin is not None:
                    yield begin, begin
                begin = current
            case _:
                assert begin is not None
                yield begin, current
                begin = None

    if begin is not None:
        yield begin, begin
