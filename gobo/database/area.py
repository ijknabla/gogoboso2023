from sqlite3 import Connection

from bidict import bidict

from ..types import AreaID


class Database:
    connection: Connection

    @property
    def area_names(self) -> bidict[AreaID, str]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
SELECT *
FROM area_names
            """
        )
        return bidict(cursor.fetchall())
