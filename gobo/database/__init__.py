import atexit
from dataclasses import dataclass
from functools import cache
from sqlite3 import Connection, connect

from pkg_resources import resource_string

from . import area, category, spot


@dataclass(frozen=True)
class Database(area.Database, category.Database, spot.Database):
    connection: Connection

    def close(self) -> None:
        self.connection.close()


@cache
def _get_db() -> Database:
    connection = connect(":memory:")
    connection.cursor().executescript(resource_string(__name__, "gobo.sql").decode("utf-8"))

    db = Database(connection)
    atexit.register(db.close)
    return db


db = _get_db()
