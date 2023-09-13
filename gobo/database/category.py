from collections.abc import Generator
from operator import itemgetter
from sqlite3 import Connection
from typing import DefaultDict

from ..types import CategoryID, SpotID


class Database:
    connection: Connection

    def find_category_by_name(self, name: str) -> Generator[CategoryID, None, None]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
SELECT category_id
FROM category_names
WHERE category_name = ?
ORDER BY category_id
            """,
            (name,),
        )
        while True:
            match cursor.fetchmany():
                case []:
                    return
                case values:
                    yield from map(itemgetter(0), values)

    @property
    def category_spots(self) -> dict[CategoryID, list[SpotID]]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
SELECT category_id, spot_id
FROM category_spots
ORDER BY category_id, spot_index
            """
        )
        result = DefaultDict[CategoryID, list[SpotID]](list)

        for category_id, spot_id in cursor.fetchall():
            result[category_id].append(spot_id)

        return dict(result)
