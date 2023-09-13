from sqlite3 import Connection

from ..types import URI, Area, SpotID


class Database:
    connection: Connection

    @property
    def spot_names(self) -> dict[SpotID, str]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
SELECT *
FROM spot_names
ORDER BY spot_id
            """
        )
        return dict(cursor.fetchall())

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

    def spot_area(self, id: SpotID) -> Area:
        cursor = self.connection.cursor()
        cursor.execute(
            """
SELECT area_id
FROM spot_areas
WHERE spot_id = ?
            """,
            (id,),
        )
        match cursor.fetchone():
            case (area_id,):
                return Area(area_id)
            case _:
                raise ValueError(id)
