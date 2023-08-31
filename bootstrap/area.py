from sqlite3 import Cursor

from pkg_resources import resource_string


def create_and_insert(cursor: Cursor) -> None:
    cursor.executescript(resource_string(__name__, "area.sql").decode("utf-8"))
