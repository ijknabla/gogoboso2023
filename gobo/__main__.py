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

    spot_sheet = wb.create_sheet("スポット")
    spot_sheet["A1"] = "ID"
    spot_sheet["B1"] = "達成"
    spot_sheet["C1"] = "名前(クリックするとページを表示)"

    for i, spot_id in enumerate(db.spots, start=2):
        spot_sheet[f"A{i}"] = spot_id
        spot_sheet[f"B{i}"] = False
        spot_sheet[f"C{i}"].value = db.spot_name(spot_id).replace("\u3000", " ")
        spot_sheet[f"C{i}"].hyperlink = db.spot_uri(spot_id)

    spot_sheet.auto_filter.ref = spot_sheet.dimensions

    municipality_sheet = wb.create_sheet("市町村")

    municipality_sheet["A1"] = "ID"
    municipality_sheet["B1"] = "名前"
    for i, municipality_id in enumerate(db.municipalities, start=2):
        municipality_sheet[f"A{i}"] = municipality_id
        municipality_sheet[f"B{i}"] = "".join(
            map(
                partial(db.municipality_name, notation=Notation.default),
                db.municipality_parts(municipality_id)[1:],
            )
        )

    wb.remove(wb.worksheets[0])
    wb.save(output)


if __name__ == "__main__":
    main()
