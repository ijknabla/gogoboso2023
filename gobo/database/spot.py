from sqlite3 import Connection
from typing import DefaultDict

from ..types import URI, AreaID, SpotID


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

    @property
    def spot_areas(self) -> dict[SpotID, list[AreaID]]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
SELECT spot_id, area_id
FROM spot_areas
ORDER BY spot_id, area_index
            """
        )

        result = DefaultDict[SpotID, list[AreaID]](list)

        for spot_id, area_id in cursor.fetchall():
            result[spot_id].append(area_id)

        return dict(result)
