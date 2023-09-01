from __future__ import annotations

import json
import re
from collections.abc import Generator
from typing import TypedDict, cast

from lxml import html
from lxml.etree import _Element
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm

from .types import Data, Spot, SpotID


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


def scraping(driver: WebDriver, boot_option: BootOption) -> Data:
    spots: dict[SpotID, Spot] = {}
    for stampRallySpot in tqdm(
        sorted(boot_option["stampRallySpots"], key=lambda spot: spot["spotId"])
    ):
        spot = cast(Spot, {"id": stampRallySpot["spotId"], "name": stampRallySpot["spotTitle"]})
        spots[spot["id"]] = spot

        driver.get(f"https://platinumaps.jp/d/gogo-boso?s={spot['id']}")

        for frame in driver.find_elements(by=By.XPATH, value="//iframe"):
            driver.switch_to.frame(frame)
            for tr in driver.find_elements(
                by=By.XPATH, value='//tr[@class = "poiproperties__item"]'
            ):
                (itemlabel,) = tr.find_elements(
                    by=By.XPATH, value='child::th[@class = "poiproperties__itemlabel"]'
                )
                match itemlabel.text:
                    case "住所":
                        (a,) = tr.find_elements(by=By.XPATH, value="descendant::a")
                        spot["address"] = a.text
                    case "URL":
                        (a,) = tr.find_elements(by=By.XPATH, value="descendant::a")
                        href = a.get_attribute("href")
                        assert href is not None
                        spot["uri"] = href

    return Data(spots=spots)


def _find_boot_options_from_frame(document: _Element) -> Generator[BootOption, None, None]:
    pattern = re.compile(r"window\.__bootOptions\s*=\s*(?P<json>.*?);")
    text: str
    for text in document.xpath("//script/text()"):  # type: ignore
        searched = pattern.search(text)
        if searched is not None:
            yield cast(BootOption, json.loads(searched.group("json")))
