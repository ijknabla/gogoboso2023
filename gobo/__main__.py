from asyncio import run
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec, TypeVar

import click
from openpyxl import Workbook

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
@click.argument("output", type=click.Path(dir_okay=False))
@run_decorator
async def excel(
    output: str,
) -> None:
    wb = Workbook()
    wb.save(output)


if __name__ == "__main__":
    main()