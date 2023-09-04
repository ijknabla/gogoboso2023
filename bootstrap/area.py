import re
from sqlite3 import Cursor

from .types import BootOption


def create_and_insert(cursor: Cursor, boot_option: BootOption) -> None:
    cursor.execute(
        """
CREATE TABLE area_names
(
    area_id INTEGER PRIMARY KEY,
    area_name TEXT UNIQUE NOT NULL
)
        """
    )
    values = {
        _parse_value(sub_area_code["Value"]): sub_area_code["Text"].replace("ヶ", "ケ")
        for stamp_rally in boot_option["stampRallies"]
        for sub_area_code in stamp_rally["subAreaCodes"]
    } | {
        121011: "中央区",
        121029: "花見川区",
        121037: "稲毛区",
        121045: "若葉区",
        121053: "緑区",
        121061: "美浜区",
    }
    cursor.executemany(
        """
INSERT INTO area_names
VALUES (?, ?)
        """,
        sorted(values.items()),
    )


def _parse_value(value: str) -> int:
    match re.match(r"JP-(\d+)", value):
        case matched if matched is not None:
            return int(matched.group(1))

    raise ValueError(value)
