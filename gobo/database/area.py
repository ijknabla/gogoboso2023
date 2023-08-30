from sqlite3 import Connection

from ..types import Area, Notation


class Database:
    connection: Connection

    def area_name(self, area: Area, notation: Notation = Notation.default) -> str:
        cursor = self.connection.cursor()
        cursor.execute(
            """
SELECT area_name
FROM area_names
WHERE area_id = ? AND notation_id = ?
            """,
            (area.value, notation.value),
        )
        match cursor.fetchone():
            case (area_name,):
                return area_name
            case _:
                raise ValueError(area, notation)
