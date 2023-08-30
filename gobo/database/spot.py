from sqlite3 import Connection

from ..types import URI, Notation, SpotID


class Database:
    connection: Connection

    @property
    def spots(self) -> list[SpotID]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
SELECT DISTINCT spot_id
FROM spot_names
ORDER BY spot_id
            """
        )
        return [SpotID(id) for id, in cursor.fetchall()]

    def spot_name(self, id: SpotID, notation: Notation = Notation.default) -> str:
        cursor = self.connection.cursor()
        cursor.execute(
            """
SELECT spot_name
FROM spot_names
WHERE spot_id = ? AND notation_id = ?
            """,
            (id, notation.value),
        )
        match cursor.fetchone():
            case (name,):
                return name
            case _:
                raise ValueError(id, notation)

    def spot_uri(self, id: SpotID) -> URI:
        cursor = self.connection.cursor()
        cursor.execute(
            """
SELECT spot_uri
FROM spot_uris
WHERE spot_id = ?
            """,
            (id,),
        )
        match cursor.fetchone():
            case (uri,):
                return URI(uri)
            case _:
                raise ValueError(id)
