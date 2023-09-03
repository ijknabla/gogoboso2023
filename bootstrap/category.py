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
