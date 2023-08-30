from asyncio import run
from collections.abc import Callable, Coroutine
from functools import partial, wraps
from typing import Any, ParamSpec, TypeVar

import click
from openpyxl import Workbook

from .database import db
from .types import Area, Notation

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
    spot_sheet["D1"] = "エリア"

    for i, spot_id in enumerate(db.spots, start=2):
        spot_sheet[f"A{i}"] = spot_id
        spot_sheet[f"B{i}"] = False
        spot_sheet[f"C{i}"].value = db.spot_name(spot_id).replace("\u3000", " ")
        spot_sheet[f"C{i}"].hyperlink = db.spot_uri(spot_id)
        spot_sheet[f"D{i}"] = db.area_name(db.spot_area(spot_id))

    spot_sheet.auto_filter.ref = spot_sheet.dimensions

    spot_clear_range = f"スポット!$B{1+1}:$B{1+len(db.spots)}"
    spot_area_range = f"スポット!$D{1+1}:$D{1+len(db.spots)}"

    total_sheet = wb.create_sheet("集計")
    total_sheet["A1"] = "エリア"
    total_sheet["B1"] = "達成数"
    total_sheet["C1"] = "総数"
    total_sheet["D1"] = "達成率"
    for i, area in enumerate(Area, start=2):
        total_sheet[f"A{i}"] = db.area_name(area)
        total_sheet[
            f"B{i}"
        ] = f'=COUNTIFS({spot_area_range}, "={db.area_name(area)}", {spot_clear_range}, TRUE)'
        total_sheet[f"C{i}"] = f'=COUNTIFS({spot_area_range}, "={db.area_name(area)}")'
        total_sheet[f"D{i}"] = f"=100 * $B${i} / $C${i}"

    municipality_sheet = wb.create_sheet("市町村データベース")

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
