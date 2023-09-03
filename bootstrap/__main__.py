import json
import sys
from asyncio import gather, get_running_loop, run
from collections.abc import AsyncGenerator, Callable, Coroutine, Generator
from concurrent.futures import ThreadPoolExecutor as Executor
from contextlib import asynccontextmanager, contextmanager
from functools import wraps
from sqlite3 import connect
from typing import IO, Any, ParamSpec, TypeVar, cast

import click
from selenium import webdriver

from . import area, category, platinum, spot, types
from .types import BootOption

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


@main.command(name="boot-option")
@click.option("-o", "--output", type=click.File("w", encoding="utf-8"), default=sys.stdout)
@click.option("--indent", type=int, default=2)
def boot_option_command(output: IO[str], indent: int | None) -> None:
    with _open_chrome_driver() as driver:
        (boot_option,) = platinum.find_boot_options(driver)
    json.dump(boot_option, output, indent=indent, ensure_ascii=False)


@main.command(name="spot")
@run_decorator
@click.argument("boot-option-json", type=click.File("r", encoding="utf-8"))
@click.option("-o", "--output", type=click.File("w", encoding="utf-8"), default=sys.stdout)
@click.option("-j", type=int, default=4)
@click.option("--indent", type=int, default=2)
async def spot_command(
    boot_option_json: IO[str],
    output: IO[str],
    indent: int | None,
    j: int,
) -> None:
    boot_option = cast(BootOption, json.load(boot_option_json))

    async with _aopen_chrome_drivers(max(1, j), headless=False) as drivers:
        spots = await platinum.get_spots(drivers, boot_option)

    json.dump(spots, output, indent=indent, ensure_ascii=False)


@main.command(name="category")
@run_decorator
@click.argument("boot-option-json", type=click.File("r", encoding="utf-8"))
@click.option("-o", "--output", type=click.File("w", encoding="utf-8"), default=sys.stdout)
@click.option("-j", type=int, default=2)
@click.option("--indent", type=int, default=2)
async def category_command(
    boot_option_json: IO[str],
    output: IO[str],
    indent: int | None,
    j: int,
) -> None:
    boot_option = cast(BootOption, json.load(boot_option_json))

    categories = await platinum.get_categories([_open_chrome_driver] * max(1, j), boot_option)

    json.dump(categories, output, indent=indent, ensure_ascii=False)


@main.command
@run_decorator
@click.argument("boot_json", type=click.File("r", encoding="utf-8"))
@click.argument("spot_json", type=click.File("r", encoding="utf-8"))
@click.argument("category_json", type=click.File("r", encoding="utf-8"))
@click.option(
    "-o", "--output", "output_file", type=click.File("w", encoding="utf-8"), default=sys.stdout
)
async def database(
    boot_json: IO[str],
    spot_json: IO[str],
    category_json: IO[str],
    output_file: IO[str],
) -> None:
    boot = cast(BootOption, json.load(boot_json))
    spots = cast(list[types.Spot], json.load(spot_json))
    categories = cast(list[types.Category], json.load(category_json))

    with connect(":memory:") as connection:
        cursor = connection.cursor()
        area.create_and_insert(cursor, boot)
        spot.create_and_insert(cursor, spots)
        category.create_and_insert(cursor, categories)

        for sql in connection.iterdump():
            print(sql, file=output_file)


@contextmanager
def _open_chrome_driver(headless: bool = False) -> Generator[webdriver.Chrome, None, None]:
    driver = _get_chrome_driver(headless=headless)
    try:
        yield driver
    finally:
        driver.close()


@asynccontextmanager
async def _aopen_chrome_drivers(
    n: int, headless: bool = False
) -> AsyncGenerator[list[webdriver.Chrome], None]:
    loop = get_running_loop()
    with Executor(n) as executor:
        drivers = await gather(
            *(loop.run_in_executor(executor, _get_chrome_driver, headless) for _ in range(n))
        )
        try:
            yield drivers
        finally:
            await gather(*(loop.run_in_executor(executor, driver.close) for driver in drivers))


def _get_chrome_driver(headless: bool) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()

    if headless:
        options.add_argument("--headless")  # type: ignore

    # 日本語指定しておく
    options.add_argument("--lang=ja-JP")  # type: ignore
    options.add_experimental_option("prefs", {"intl.accept_languages": "ja"})

    return webdriver.Chrome(options=options)


if __name__ == "__main__":
    main()
