from sqlite3 import Connection

from ..types import AreaID


class Database:
    connection: Connection

    @property
    def area_names(self) -> dict[AreaID, str]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
SELECT *
FROM area_names
            """
        )
        return dict(cursor.fetchall())
