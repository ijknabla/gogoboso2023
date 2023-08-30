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
