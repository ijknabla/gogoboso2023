import sys
from asyncio import run
from collections.abc import Callable, Coroutine
from contextlib import AsyncExitStack
from functools import wraps
from pathlib import Path
from sqlite3 import connect
from typing import IO, Any, ParamSpec, TypeVar

import click

from gobo.types import URI

from . import area, municipality
from .cache import Cache

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
@run_decorator
@click.option("-o", "--output", type=click.File("w", encoding="utf-8"), default=sys.stdout)
@click.option(
    "--cache-path", type=click.Path(dir_okay=False, path_type=Path), default=Path(".cache.pickle")
)
async def database(output: IO[str], cache_path: Path) -> None:
    async with AsyncExitStack() as stack:
        enter = stack.enter_context
        connection = enter(connect(":memory:"))

        cache = enter(Cache(cache_path))

        cursor = connection.cursor()
        municipality.create_and_insert(
            cursor,
            await cache.get_html(
                URI("http://www.tt.rim.or.jp/~ishato/tiri/code/rireki/12tiba.htm"), "cp932"
            ),
        )
        area.create_and_insert(cursor)

        for sql in connection.iterdump():
            print(sql, file=output)


if __name__ == "__main__":
    main()
