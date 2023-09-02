from __future__ import annotations

import json
import re
from asyncio import gather, get_running_loop
from collections.abc import Collection, Generator, Iterable
from concurrent.futures import ThreadPoolExecutor as Executor
from itertools import count, product
from time import sleep
from typing import TypedDict, cast

from lxml import html
from lxml.etree import _Element
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm

from gobo.types import CategoryID

from .types import Category, Spot


class BootOption(TypedDict):
    mapCategories: list[MapCategory]
    stampRallySpots: list[StampRallySpot]


class MapCategory(TypedDict):
    parentCategoryId: CategoryID
    categoryId: CategoryID
    shapes: list[Shape]
    mapCategoryGroup: str
    categoryName: str


class Shape(TypedDict):
    description: str
    name: str


class StampRallySpot(TypedDict):
    spotId: int
    spotTitle: str


def find_boot_options(driver: WebDriver) -> Generator[BootOption, None, None]:
    driver.get("https://platinumaps.jp/d/gogo-boso")
    for frame in driver.find_elements(by=By.XPATH, value="//iframe"):
        driver.switch_to.frame(frame)
        yield from _find_boot_options_from_frame(html.fromstring(driver.page_source))


def _find_boot_options_from_frame(document: _Element) -> Generator[BootOption, None, None]:
    pattern = re.compile(r"window\.__bootOptions\s*=\s*(?P<json>.*?);")
    text: str
    for text in document.xpath("//script/text()"):  # type: ignore
        searched = pattern.search(text)
        if searched is not None:
            yield cast(BootOption, json.loads(searched.group("json")))


async def get_spots(drivers: Collection[WebDriver], boot_option: BootOption) -> list[Spot]:
    iterator = iter(tqdm(boot_option["stampRallySpots"]))

    with Executor(len(drivers)) as executor:
        spots: list[Spot] = sum(
            await gather(*(_each_get_spots(executor, driver, iterator) for driver in drivers)), []
        )

    return sorted(spots, key=lambda spot: spot["id"])


async def _each_get_spots(
    executor: Executor, driver: WebDriver, spots: Iterable[StampRallySpot]
) -> list[Spot]:
    loop = get_running_loop()
    return [await loop.run_in_executor(executor, _get_spot, driver, spot) for spot in spots]


def _get_spot(driver: WebDriver, spot: StampRallySpot) -> Spot:
    result = cast(
        Spot,
        {
            "id": spot["spotId"],
            "name": spot["spotTitle"],
        },
    )

    driver.get(f"https://platinumaps.jp/d/gogo-boso?s={result['id']}")
    for frame in driver.find_elements(by=By.XPATH, value="//iframe"):
        driver.switch_to.frame(frame)

        for i in count(1):
            for tr in driver.find_elements(
                by=By.XPATH, value='//tr[@class = "poiproperties__item"]'
            ):
                for itemlabel, a in product(
                    tr.find_elements(
                        by=By.XPATH, value='child::th[@class = "poiproperties__itemlabel"]'
                    ),
                    tr.find_elements(by=By.XPATH, value="descendant::a"),
                ):
                    match itemlabel.text:
                        case "住所":
                            result["address"] = a.text
                        case "URL":
                            href = a.get_attribute("href")
                            assert href is not None
                            result["uri"] = href

            if (
                True
                and "address" in result
                and (
                    "uri" in result
                    or spot["spotId"]
                    in {
                        208399,
                        208417,
                        208428,
                        208448,
                        208449,
                        208470,
                        208478,
                        208495,
                        208496,
                        208568,
                        208581,
                        208615,
                        208616,
                        208639,
                        208642,
                        208663,
                    }
                )
            ):
                break

            if i <= 30:
                sleep(1)
                continue

            print(driver.current_url)
            break

    return result


async def get_categories(drivers: Collection[WebDriver], boot_option: BootOption) -> list[Category]:
    return []
