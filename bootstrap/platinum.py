from __future__ import annotations

import json
import re
from asyncio import gather, get_running_loop
from collections.abc import Callable, Collection, Coroutine, Generator, Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor as Executor
from functools import partial
from itertools import chain, count, product
from operator import itemgetter
from time import sleep
from typing import Concatenate, ParamSpec, TypedDict, TypeVar, cast

from lxml import html
from lxml.etree import _Element
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm

from gobo.types import CategoryID, SpotID

from .types import Category, Course, Spot

_P = ParamSpec("_P")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")

NO_URL_SPOTS = {
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

CATEGORY_LENGTH = {
    19016: 24,
    19018: 17,
    19025: 24,
    19028: 15,
    19167: 5,
    19168: 4,
    19697: 24,
    19762: 6,
    19882: 12,
    19883: 17,
    19884: 18,
    19885: 17,
    19886: 19,
    19887: 24,
    20124: 4,
    20125: 4,
    20126: 4,
    20172: 5,
    20173: 6,
    20174: 7,
    20177: 6,
    20178: 5,
    20180: 6,
    20187: 6,
    20188: 5,
    20189: 6,
    20190: 5,
    20191: 7,
    20192: 5,
    20193: 6,
    20194: 5,
    20195: 5,
    20196: 5,
    20197: 5,
    20482: 5,
}


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
    spotId: SpotID
    spotTitle: str


def find_boot_options(driver: WebDriver) -> Generator[BootOption, None, None]:
    driver.get("https://platinumaps.jp/d/gogo-boso")
    for frame in driver.find_elements(by=By.XPATH, value="//iframe"):
        driver.switch_to.frame(frame)
        yield from _find_boot_options_from_frame(html.fromstring(driver.page_source))


async def get_spots(drivers: Collection[WebDriver], boot_option: BootOption) -> list[Spot]:
    return sorted(await _get_spots(drivers, boot_option["stampRallySpots"]), key=itemgetter("id"))


async def get_categories(drivers: Collection[WebDriver], boot_option: BootOption) -> list[Category]:
    spot_ids = {spot["spotTitle"]: spot["spotId"] for spot in boot_option["stampRallySpots"]}

    return sorted(
        await _get_categories(drivers, boot_option["mapCategories"], spot_ids=spot_ids),
        key=itemgetter("id"),
    )


def _find_boot_options_from_frame(document: _Element) -> Generator[BootOption, None, None]:
    pattern = re.compile(r"window\.__bootOptions\s*=\s*(?P<json>.*?);")
    text: str
    for text in document.xpath("//script/text()"):  # type: ignore
        searched = pattern.search(text)
        if searched is not None:
            yield cast(BootOption, json.loads(searched.group("json")))


def vectorize(
    f: Callable[
        Concatenate[
            WebDriver,
            _T1,
            _P,
        ],
        _T2,
    ]
) -> Callable[
    Concatenate[
        Collection[WebDriver],
        Iterable[_T1],
        _P,
    ],
    Coroutine[None, None, list[_T2]],
]:
    async def vectorized(
        drivers: Collection[WebDriver],
        iterable: Iterable[_T1],
        /,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> list[_T2]:
        loop = get_running_loop()
        iterator = iter(tqdm(iterable))

        with Executor(len(drivers)) as executor:

            async def vectorized(driver: WebDriver) -> list[_T2]:
                return [
                    await loop.run_in_executor(executor, partial(f, driver, item, *args, **kwargs))
                    for item in iterator
                ]

            results = await gather(*(vectorized(driver) for driver in drivers))

            return list(chain.from_iterable(results))

    return vectorized


@vectorize
def _get_spots(driver: WebDriver, spot: StampRallySpot) -> Spot:
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

            if True and "address" in result and ("uri" in result or spot["spotId"] in NO_URL_SPOTS):
                break

            if i <= 30:
                sleep(1)
                continue

            print(driver.current_url)
            break

    return result


@vectorize
def _get_categories(
    driver: WebDriver, category: MapCategory, spot_ids: Mapping[str, SpotID]
) -> Category:
    result = Category(
        id=category["categoryId"],
        parent_id=category["parentCategoryId"],
        name=category["categoryName"],
        ref=category["mapCategoryGroup"],
        spots=[],
    )

    driver.get(f"https://platinumaps.jp/d/gogo-boso?c={result['ref']}&list=1")
    for frame in driver.find_elements(by=By.XPATH, value="//iframe"):
        driver.switch_to.frame(frame)

        for div in driver.find_elements(by=By.XPATH, value='//div[@class = "spotlist__itemtitle"]'):
            result["spots"].append(div.text)
            print(result["name"], div.text)

    match category["shapes"]:
        case (shape,):
            result["course"] = Course(name=shape["name"], description=shape["description"])

    return result
