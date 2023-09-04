from __future__ import annotations

import re
from sqlite3 import Cursor

from .types import Category


def create_and_insert(cursor: Cursor, categories: list[Category]) -> None:
    cursor.execute(
        """
CREATE TABLE category_names
(
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL
)
        """
    )
    cursor.executemany(
        """
INSERT INTO category_names
VALUES (?, ?)
        """,
        [(category["id"], re.sub(r"\s+", "", category["name"])) for category in categories],
    )

    cursor.execute(
        """
CREATE TABLE course_names
(
    category_id INTEGER PRIMARY KEY,
    cource_name TEXT UNIQUE NOT NULL
)
        """
    )
    cursor.executemany(
        """
INSERT INTO course_names
VALUES (?, ?)
        """,
        [
            (category["id"], category["course"]["name"])
            for category in categories
            if "course" in category
        ],
    )

    cursor.execute(
        """
CREATE TABLE category_spots
(
    category_id INTEGER,
    spot_index INTEGER,
    spot_id INTEGER NOT NULL,
    PRIMARY KEY(category_id, spot_index)
)
        """
    )
    cursor.executemany(
        """
INSERT INTO category_spots
VALUES (?, ?, ?)
        """,
        [
            (category["id"], index, id)
            for category in categories
            for index, id in enumerate(category["spot_ids"])
        ],
    )
