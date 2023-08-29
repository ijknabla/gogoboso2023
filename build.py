import pathlib
import typing

import bootstrap.database

HERE = pathlib.Path(__file__).parent.absolute()


def build(_: typing.Any) -> None:
    bootstrap.database.create(HERE / "gobo/database/gobo.db", overwrite=True)


if __name__ == "__main__":
    build({})
