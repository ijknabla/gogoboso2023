from __future__ import annotations

from sqlite3 import Cursor

from .types import Spot


def create_and_insert(cursor: Cursor, spots: list[Spot]) -> None:
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
CREATE TABLE spot_uris
(
    spot_id INTEGER PRIMARY KEY,
    spot_uri TEXT NOT NULL
)
        """
    )
    cursor.executemany(
        """
INSERT INTO spot_uris
VALUES (?, ?)
        """,
        [(spot["id"], spot["link_uri"]) for spot in spots if "link_uri" in spot],
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
