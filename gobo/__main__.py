from asyncio import run
from collections.abc import Callable, Coroutine
from enum import Enum

# from contextlib import suppress
from functools import wraps
from typing import Any, ParamSpec, TypeVar

import click
from openpyxl import Workbook

from .database import db

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


class SpotColumn(Enum):
    ID = id = "A"
    名前 = name = "B"
    市町村 = area = "C"

    def index(self, i: int) -> str:
        return f"{self.value}{i}"


CLEARED = "A"
NAME = "B"
MUNICIPALITY = "C"


@main.command
@click.argument("output", type=click.Path(dir_okay=False))
@run_decorator
async def excel(
    output: str,
) -> None:
    wb = Workbook()

    (category,) = db.find_category_by_name("デジタルポイントラリー")
    spot_order = db.category_spots[category]

    spot_db_sheet = wb.create_sheet("スポットデータベース")
    for col in SpotColumn:
        spot_db_sheet[col.index(1)] = col.name

    for row, spot_id in enumerate(spot_order, start=2):
        spot_db_sheet[SpotColumn.id.index(row)] = spot_id
        spot_db_sheet[SpotColumn.name.index(row)] = db.spot_names[spot_id]
        spot_db_sheet[SpotColumn.area.index(row)] = ";".join(
            db.area_names[area_id] for area_id in db.spot_areas[spot_id]
        )

    # spot_sheet = wb.create_sheet("スポット")
    # spot_sheet[f"{CLEARED}1"] = "達成"
    # spot_sheet[f"{NAME}1"] = "名前"
    # spot_sheet[f"{MUNICIPALITY}1"] = "市町村"

    # for i, spot_id in enumerate(db.spots, start=2):
    #     spot_sheet[f"{CLEARED}{i}"] = False
    #     spot_sheet[f"{NAME}{i}"].value = db.spot_name(spot_id).replace("\u3000", " ")
    #     spot_sheet[f"{MUNICIPALITY}{i}"] = scraping_address(spot_id)
    #     spot_sheet[f"D{i}"].value = "リンク(GoGo房総)"
    #     spot_sheet[f"D{i}"].hyperlink = f"https://platinumaps.jp/d/gogo-boso?s={spot_id}"
    #     with suppress(ValueError):
    #         spot_sheet[f"E{i}"].hyperlink = db.spot_uri(spot_id)
    #         spot_sheet[f"E{i}"].value = "リンク(施設)"

    # spot_sheet.auto_filter.ref = spot_sheet.dimensions

    # spot_clear_range = f"スポット!${CLEARED}${1+1}:${CLEARED}${1+len(db.spots)}"
    # spot_area_range = f"スポット!${MUNICIPALITY}${1+1}:${MUNICIPALITY}${1+len(db.spots)}"

    # total_sheet = wb.create_sheet("集計")
    # total_sheet["A1"] = "市町村"
    # total_sheet["B1"] = "達成数"
    # total_sheet["C1"] = "総数"
    # total_sheet["D1"] = "達成率"
    # for i, municipality_id in enumerate(db.municipalities, start=2):
    #     total_sheet[f"A{i}"] = db.municipality_name(municipality_id)
    #     total_sheet[f"B{i}"] = (
    #         f"=COUNTIFS({spot_area_range}, "
    #         f'"*{db.municipality_name(municipality_id)}*", {spot_clear_range}, TRUE)'
    #     )
    #     total_sheet[
    #         f"C{i}"
    #     ] = f'=COUNTIFS({spot_area_range}, "*{db.municipality_name(municipality_id)}*")'
    #     total_sheet[f"D{i}"] = f"=100 * $B${i} / $C${i}"

    wb.remove(wb.worksheets[0])
    wb.save(output)


if __name__ == "__main__":
    main()
