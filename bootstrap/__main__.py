import sys
from asyncio import run
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import IO, Any, ParamSpec, TypeVar

import click

from . import municipality

P = ParamSpec("P")
T = TypeVar("T")


def run_decorator(f: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, T]:
    @wraps(f)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        return run(f(*args, **kwargs))

    return wrapped


@click.group
def main() -> None:
    ...


@main.command
@click.option("-o", "--output", type=click.File("a", encoding="utf-8"), default=sys.stdout)
@run_decorator
async def 市町村(output: IO[str]) -> None:
    rows = [row async for row in municipality.get_rows()]

    print(
        """
CREATE TABLE municipality_names
(
    id INTEGER PRIMARY KEY,
    kanji TEXT UNIQUE NOT NULL,
    kana TEXT UNIQUE NOT NULL
);

INSERT INTO municipality_names
(
        id, kanji, kana
)
VALUES
        """.strip(),
        file=output,
    )

    print(
        *(f"    ({id:>5}, {kanji!r}, {kana!r})" for id, _, (kanji, kana) in rows),
        sep=",\n",
        end=";\n",
        file=output,
    )

    print(file=output)

    print(
        """
CREATE TABLE municipality_parents
(
    id INTEGER NOT NULL,
    parent_id INTEGER NOT NULL
);

INSERT INTO municipality_parents
(
        id, parent_id
)
VALUES
        """.strip(),
        file=output,
    )

    print(
        *(f"    ({id:>5}, {parent_id:>5})" for id, parent_id, _ in rows if parent_id is not None),
        sep=",\n",
        end=";\n",
        file=output,
    )


if __name__ == "__main__":
    main()
