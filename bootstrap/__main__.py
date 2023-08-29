from asyncio import run
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec, TypeVar

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
@run_decorator
async def 市町村() -> None:
    async for id, parent_id, (kanji, kana) in municipality.get_rows():
        parent = "NULL" if parent_id is None else parent_id
        print(f"    ({id:>5}, {parent:>5}, {kanji!r:　<7}, {kana!r:　<11})")


if __name__ == "__main__":
    main()
