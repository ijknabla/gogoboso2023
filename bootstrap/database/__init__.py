import sqlite3
from pathlib import Path

DIRECTORY = Path(__file__).parent.absolute()


def create(path: Path, overwrite: bool) -> None:
    if overwrite and path.exists():
        path.unlink()
    with sqlite3.connect(path) as connection:
        setup(connection)


def setup(connection: sqlite3.Connection) -> sqlite3.Connection:
    cursor = connection.cursor()
    for sql in DIRECTORY.glob("*.sql"):
        cursor.executescript(sql.read_text())
    connection.commit()

    return connection
