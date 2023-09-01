from __future__ import annotations

import json
import re
from collections.abc import Generator
from typing import TypedDict, cast

from lxml import html
from lxml.etree import _Element
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


class BootOption(TypedDict):
    stampRallySpots: list[StampRallySpot]


class StampRallySpot(TypedDict):
    spotId: int
    spotTitle: str


def find_boot_options(driver: WebDriver) -> Generator[BootOption, None, None]:
    driver.get("https://platinumaps.jp/d/gogo-boso?list=1")
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
