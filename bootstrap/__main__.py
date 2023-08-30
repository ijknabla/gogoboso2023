import sys
from asyncio import run
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import IO, Any, ParamSpec, TypeVar

import click

from gobo.types import Notation

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


@main.command(name="municipality")
@click.option("-o", "--output", type=click.File("w", encoding="utf-8"), default=sys.stdout)
@run_decorator
async def municipality_command(output: IO[str]) -> None:
    rows = [row async for row in municipality.get_rows()]
    kanji = {kanji: id for id, _, (kanji, _) in rows}

    print(
        """
CREATE TABLE municipality_names
(
    municipality_id INTEGER NOT NULL,
    notation_id INTEGER NOT NULL,
    `name` TEXT UNIQUE NOT NULL,
    PRIMARY KEY(municipality_id, notation_id)
);

INSERT INTO municipality_names
(
    municipality_id, notation_id, `name`
)
VALUES
        """.strip(),
        file=output,
    )

    print(
        *(
            f"    ({id:>5}, {notation.value}, {name!r})"
            for id, _, names in rows
            for notation, name in zip(Notation, names)
        ),
        sep=",\n",
        end=";\n",
        file=output,
    )

    print(file=output)
    print(
        """
CREATE TABLE municipality_tree
(
    parent_id INTEGER NULL,
    child_id INTEGER NOT NULL
);

INSERT INTO municipality_tree
(
    parent_id, child_id
)
VALUES
        """.strip(),
        file=output,
    )

    NULL = "NULL"

    print(
        *(
            f"    ({NULL if parent_id is None else parent_id:>5}, {child_id:>5})"
            for child_id, parent_id, _ in rows
        ),
        sep=",\n",
        end=";\n",
        file=output,
    )

    print(file=output)
    print(
        """
CREATE TABLE municipality_list
(
    `index` INTEGER PRIMARY KEY,
    id INTEGER UNIQUE NOT NULL
);

INSERT INTO municipality_list
(
    `index`, id
)
VALUES
        """.strip(),
        file=output,
    )
    print(
        *(f"    ({i:>2}, {kanji[s]:>5})" for i, s in enumerate(municipality.ORDER, start=1)),
        sep=",\n",
        end=";\n",
        file=output,
    )


if __name__ == "__main__":
    main()
