from __future__ import annotations

import json
import re
from asyncio import gather, get_running_loop
from collections.abc import Callable, Collection, Coroutine, Generator, Iterable
from concurrent.futures import ThreadPoolExecutor as Executor
from contextlib import AbstractContextManager
from functools import partial
from itertools import chain, count, product
from operator import itemgetter
from time import sleep
from typing import Concatenate, ParamSpec, TypedDict, TypeVar, cast
from warnings import warn

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
_T3 = TypeVar("_T3")

INTERVAL = 1.0
REPEAT = 30

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
    19016: 491,
    19018: 17,
    19025: 490,
    19028: 15,
    19167: 5,
    19168: 4,
    19697: 97,
    19762: 6,
    19882: 12,
    19883: 17,
    19884: 18,
    19885: 17,
    19886: 19,
    19887: 31,
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


class CategoryLengthMismatch(Warning):
    ...


class UnableSpot(Warning):
    ...


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


async def get_categories(
    open_drivers: Collection[Callable[[], AbstractContextManager[WebDriver]]],
    boot_option: BootOption,
) -> list[Category]:
    result: list[Category]
    result = sorted(
        await _get_category(open_drivers, boot_option["mapCategories"]), key=itemgetter("id")
    )
    for missing in sorted(
        set(id for c in result for id in c["spot_ids"])
        - set(s["spotId"] for s in boot_option["stampRallySpots"])
    ):
        warn(UnableSpot(missing))

    return result


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
            _T1,
            _T2,
            _P,
        ],
        _T3,
    ]
) -> Callable[Concatenate[Collection[_T1], Iterable[_T2], _P,], Coroutine[None, None, list[_T3]],]:
    async def vectorized(
        collection: Collection[_T1],
        iterable: Iterable[_T2],
        /,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> list[_T3]:
        loop = get_running_loop()
        iterator = iter(tqdm(iterable))

        with Executor(len(collection)) as executor:

            async def vectorized(item_1: _T1) -> list[_T3]:
                return [
                    await loop.run_in_executor(
                        executor, partial(f, item_1, item_2, *args, **kwargs)
                    )
                    for item_2 in iterator
                ]

            results = await gather(*(vectorized(driver) for driver in collection))

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
def _get_category(
    open_driver: Callable[[], AbstractContextManager[WebDriver]],
    category: MapCategory,
    repeat: int = REPEAT,
    interval: float = INTERVAL,
) -> Category:
    result = Category(
        id=category["categoryId"],
        parent_id=category["parentCategoryId"],
        name=category["categoryName"],
        ref=category["mapCategoryGroup"],
        spot_ids=[],
    )
    spot_ids = result["spot_ids"]

    expected_spot_ids_length = CATEGORY_LENGTH[result["id"]]

    with open_driver() as driver:
        driver.get(f"https://platinumaps.jp/d/gogo-boso?c={result['ref']}&list=1")

        width, height = driver.get_window_size().values()

        for frame in driver.find_elements(by=By.XPATH, value="//iframe"):
            driver.switch_to.frame(frame)

            for i in range(repeat):
                spot_ids[:] = pickup_spot_ids(driver)

                if len(spot_ids) >= expected_spot_ids_length:
                    break

                driver.set_window_size(width, height * 2**i)
                sleep(interval)

            if expected_spot_ids_length != len(spot_ids):
                warn(CategoryLengthMismatch(result["id"], expected_spot_ids_length, len(spot_ids)))

    match category["shapes"]:
        case (shape,):
            result["course"] = Course(name=shape["name"], description=shape["description"])

    return result


def pickup_spot_ids(driver: WebDriver) -> list[SpotID]:
    result: dict[int, SpotID] = {}
    for div in driver.find_elements(
        by=By.XPATH,
        value="//div[@data-cell-index and @data-spot-id]",
    ):
        div.id
        data_cell_index = div.get_attribute("data-cell-index")
        data_spot_id = div.get_attribute("data-spot-id")
        assert data_spot_id is not None and data_cell_index is not None

        result[int(data_cell_index)] = SpotID(int(data_spot_id))

    return [v for _, v in sorted(result.items())]
