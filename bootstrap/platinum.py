from __future__ import annotations

import json
import re
from asyncio import Queue, gather, get_running_loop
from collections.abc import Collection, Generator
from concurrent.futures import ThreadPoolExecutor
from itertools import product
from operator import itemgetter
from typing import TypedDict, cast

from lxml import html
from lxml.etree import _Element
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .types import Spot


class BootOption(TypedDict):
    stampRallySpots: list[StampRallySpot]


class StampRallySpot(TypedDict):
    spotId: int
    spotTitle: str


def find_boot_options(driver: WebDriver) -> Generator[BootOption, None, None]:
    driver.get("https://platinumaps.jp/d/gogo-boso")
    for frame in driver.find_elements(by=By.XPATH, value="//iframe"):
        driver.switch_to.frame(frame)
        yield from _find_boot_options_from_frame(html.fromstring(driver.page_source))


async def get_spots(drivers: Collection[WebDriver], boot_option: BootOption) -> list[Spot]:
    queue: Queue[StampRallySpot] = Queue()

    for spot in sorted(boot_option["stampRallySpots"], key=itemgetter("spotId")):
        await queue.put(spot)

    with ThreadPoolExecutor(len(drivers)) as executor:
        spots: list[Spot] = sum(
            await gather(*(_each_get_spots(executor, driver, queue) for driver in drivers)), []
        )

    return sorted(spots, key=lambda spot: spot["id"])


async def _each_get_spots(
    executor: ThreadPoolExecutor, driver: WebDriver, queue: Queue[StampRallySpot]
) -> list[Spot]:
    loop = get_running_loop()
    spots: list[Spot] = []

    while not queue.empty():
        source = await queue.get()
        try:
            spot = await loop.run_in_executor(executor, _get_spot, driver, source)
            spots.append(spot)
        finally:
            queue.task_done()

    return spots


def _get_spot(driver: WebDriver, source: StampRallySpot) -> Spot:
    spot = cast(
        Spot,
        {
            "id": source["spotId"],
            "name": source["spotTitle"],
        },
    )

    driver.get(f"https://platinumaps.jp/d/gogo-boso?s={spot['id']}")
    for frame in driver.find_elements(by=By.XPATH, value="//iframe"):
        driver.switch_to.frame(frame)
        for tr in driver.find_elements(by=By.XPATH, value='//tr[@class = "poiproperties__item"]'):
            for itemlabel, a in product(
                tr.find_elements(
                    by=By.XPATH, value='child::th[@class = "poiproperties__itemlabel"]'
                ),
                tr.find_elements(by=By.XPATH, value="descendant::a"),
            ):
                match itemlabel.text:
                    case "住所":
                        spot["address"] = a.text
                    case "URL":
                        href = a.get_attribute("href")
                        assert href is not None
                        spot["uri"] = href

    return spot


def _find_boot_options_from_frame(document: _Element) -> Generator[BootOption, None, None]:
    pattern = re.compile(r"window\.__bootOptions\s*=\s*(?P<json>.*?);")
    text: str
    for text in document.xpath("//script/text()"):  # type: ignore
        searched = pattern.search(text)
        if searched is not None:
            yield cast(BootOption, json.loads(searched.group("json")))
