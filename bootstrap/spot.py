from __future__ import annotations

import re
from collections.abc import Generator, Iterable
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
