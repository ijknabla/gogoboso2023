import json
import sys
from asyncio import run
from collections.abc import Callable, Coroutine, Generator
from contextlib import AsyncExitStack, contextmanager
from functools import wraps
from pathlib import Path
from sqlite3 import connect
from typing import IO, Any, ParamSpec, TypeVar

import click
from selenium import webdriver

from gobo.types import URI

from . import area, municipality, platinum, spot
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


@main.command(name="json")
@click.option("-o", "--output", type=click.File("w", encoding="utf-8"), default=sys.stdout)
@click.option("--indent", type=int)
def json_command(output: IO[str], indent: int | None) -> None:
    with open_chrome_driver() as driver:
        (boot_option,) = platinum.find_boot_options(driver)
    json.dump(boot_option, output, indent=indent)


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

        with open_chrome_driver() as driver:
            (boot_option,) = platinum.find_boot_options(driver)

        cursor = connection.cursor()
        municipality.create_and_insert(
            cursor,
            await cache.get_html(
                URI("http://www.tt.rim.or.jp/~ishato/tiri/code/rireki/12tiba.htm"), "cp932"
            ),
        )
        area.create_and_insert(cursor)
        spot.create_and_insert(cursor, boot_option)

        for sql in connection.iterdump():
            print(sql, file=output)


@contextmanager
def open_chrome_driver() -> Generator[webdriver.Chrome, None, None]:
    options = webdriver.ChromeOptions()

    options.add_argument("--headless")  # type: ignore

    # 日本語指定しておく
    options.add_argument("--lang=ja-JP")  # type: ignore
    options.add_experimental_option("prefs", {"intl.accept_languages": "ja"})

    driver = webdriver.Chrome(options=options)
    try:
        yield driver
    finally:
        driver.close()


if __name__ == "__main__":
    main()
