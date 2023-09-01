from sqlite3 import Cursor

from pkg_resources import resource_string

from .platinum import BootOption


def create_and_insert(cursor: Cursor, boot_option: BootOption) -> None:
    boot_option["stampRallySpots"]

    cursor.executescript(resource_string(__name__, "spot.sql").decode("utf-8"))
