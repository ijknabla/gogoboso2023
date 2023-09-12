from __future__ import annotations

import re
from sqlite3 import Cursor

from .area import get_areas
from .types import BootOption, Spot


def create_and_insert(
    cursor: Cursor,
    boot_option: BootOption,
    spots: list[Spot],
) -> None:
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
CREATE TABLE spot_names
(
    spot_id INTEGER,
    notation_id INTEGER,
    spot_name TEXT NOT NULL,
    PRIMARY KEY(spot_id, notation_id)
)
        """
    )
    cursor.executemany(
        """
INSERT INTO spot_names
VALUES (?, ?, ?)
        """,
        [(spot["id"], 0, spot["name"]) for spot in spots],
    )

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

    areas = {k: v for v, k in get_areas(boot_option).items() if k not in {"千葉市"}}
    pattern = re.compile("|".join(areas))

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
    cursor.executemany(
        """
INSERT INTO spot_areas
VALUES (?, ?, ?)
        """,
        [
            (spot["id"], index, areas[area])
            for spot in spots
            for index, area in enumerate(pattern.findall(_normalize_address(spot["address"])))
        ],
    )


def _normalize_address(address: str) -> str:
    return address.replace("ヶ", "ケ").replace("舘", "館")
