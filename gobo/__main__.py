from asyncio import run
from collections.abc import Callable, Coroutine
from functools import partial, wraps
from typing import Any, ParamSpec, TypeVar

import click
from openpyxl import Workbook

from .database import db
from .types import Notation

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

    municipality_sheet = wb.create_sheet("市町村")

    municipality_sheet["A1"] = "ID"
    municipality_sheet["B1"] = "名前"
    for i, municipality_id in enumerate(db.municipalities, start=2):
        municipality_sheet[f"A{i}"] = municipality_id
        municipality_sheet[f"B{i}"] = "".join(
            map(
                partial(db.municipality_name, notation=Notation.kanji),
                db.municipality_parts(municipality_id)[1:],
            )
        )

    municipality_sheet.auto_filter.ref = municipality_sheet.dimensions

    wb.save(output)


if __name__ == "__main__":
    main()
