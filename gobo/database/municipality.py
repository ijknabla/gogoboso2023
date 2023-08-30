from sqlite3 import Connection

from ..types import MunicipalityID


class Database:
    connection: Connection

    def municipality_by_name(self, name: str) -> MunicipalityID:
        cursor = self.connection.cursor()
        cursor.execute(
            """
SELECT municipality_id
FROM municipality_names
WHERE `name` = ?
        """,
            (name,),
        )

        (id,) = map(MunicipalityID, cursor.fetchone())
        return id
