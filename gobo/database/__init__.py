import atexit
from dataclasses import dataclass
from functools import cache
from sqlite3 import Connection, connect

from pkg_resources import resource_filename

from . import municipality


@dataclass(frozen=True)
class Database(municipality.Database):
    connection: Connection

    def close(self) -> None:
        self.connection.close()


@cache
def _get_db() -> Database:
    db = Database(connect(resource_filename(__name__, "gobo.db")))
    atexit.register(db.close)
    return db


db = _get_db()
