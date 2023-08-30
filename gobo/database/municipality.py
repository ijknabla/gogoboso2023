from sqlite3 import Connection

from ..types import MunicipalityID, Notation


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

    def municipality_parts(self, id: MunicipalityID) -> tuple[MunicipalityID, ...]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
SELECT parent_id
FROM municipality_tree
WHERE child_id = ?
            """,
            (id,),
        )

        match cursor.fetchone():
            case (None,):
                return (id,)
            case (parent_id,):
                return (*self.municipality_parts(parent_id), id)
            case _:
                raise ValueError(id)

    def municipality_name(self, id: MunicipalityID, notation: Notation) -> str:
        cursor = self.connection.cursor()
        cursor.execute(
            """
SELECT `name`
FROM municipality_names
WHERE municipality_id = ? AND notation_id = ?
            """,
            (id, notation.value),
        )
        match cursor.fetchone():
            case (name,):
                return name
            case _:
                raise ValueError(id)
