from __future__ import annotations

import json
import re
from asyncio import gather, get_running_loop
from collections.abc import Callable, Collection, Coroutine, Generator, Iterable
from concurrent.futures import ThreadPoolExecutor as Executor
from contextlib import AbstractContextManager
from functools import partial
from itertools import chain, product
from operator import itemgetter
from time import sleep
from typing import Concatenate, ParamSpec, TypeVar, cast
from warnings import warn

from lxml import html
from lxml.etree import _Element
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm

from gobo.types import SpotID

from .types import BootOption, Category, Course, MapCategory, Spot

_P = ParamSpec("_P")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")
_T3 = TypeVar("_T3")

INTERVAL = 1.0
REPEAT = 30

MISISNG_SPOTS = [
    209076,
    209077,
    209078,
    209079,
    209080,
    209081,
    209082,
    209083,
    209084,
    209085,
    209086,
    209087,
    209088,
    209089,
    209090,
    209091,
]

NO_SUBTITLE_SPOTS = {
    209076,
    209077,
    209078,
    209079,
    209080,
    209081,
    209082,
    209083,
    209084,
    209085,
    209086,
    209087,
    209088,
    209089,
    209090,
    209091,
}

NO_LINK_URL_SPOTS = {
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
    208662,
    208663,
    209089,
    212666,
    212679,
    213161,
    213162,
    213163,
}

CATEGORY_LENGTH = {
    19016: 525,
    19018: 51,
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


def find_boot_options(driver: WebDriver) -> Generator[BootOption, None, None]:
    driver.get("https://platinumaps.jp/d/gogo-boso")
    for frame in driver.find_elements(by=By.XPATH, value="//iframe"):
        driver.switch_to.frame(frame)
        yield from _find_boot_options_from_frame(html.fromstring(driver.page_source))


async def get_spots(drivers: Collection[WebDriver], boot_option: BootOption) -> list[Spot]:
    spot_ids = sorted(
        set(chain(map(itemgetter("spotId"), boot_option["stampRallySpots"]), MISISNG_SPOTS))
    )

    return sorted(await _get_spot(drivers, spot_ids), key=itemgetter("id"))


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
def _get_spot(
    driver: WebDriver,
    id: SpotID,
    repeat: int = REPEAT,
    interval: float = INTERVAL,
) -> Spot:
    driver.get(f"https://platinumaps.jp/d/gogo-boso?s={id}")
    for frame in driver.find_elements(by=By.XPATH, value="//iframe"):
        driver.switch_to.frame(frame)

        required = set(Spot.__annotations__)

        if id in NO_SUBTITLE_SPOTS:
            required.remove("subtitle")
        if id in NO_LINK_URL_SPOTS:
            required.remove("link_uri")

        for _ in range(repeat):
            spot = _pickup_spot_id(driver, id)

            if required <= set(spot):
                break

            sleep(interval)
        else:
            print(driver.current_url)

    return spot


def _pickup_spot_id(driver: WebDriver, id: SpotID) -> Spot:
    spot = cast(Spot, {"id": id})

    for div in driver.find_elements(by=By.XPATH, value='//div[@class = "detail__title"]'):
        spot["name"] = div.text

    for div in driver.find_elements(by=By.XPATH, value='//div[@class = "detail__subtitletext"]'):
        spot["subtitle"] = div.text

    for div in driver.find_elements(
        by=By.XPATH, value='//div[@class = "ptmdescription__text"]/div[1]'
    ):
        spot["description"] = div.text

    for tr in driver.find_elements(by=By.XPATH, value='//tr[@class = "poiproperties__item"]'):
        for label, a in product(
            tr.find_elements(by=By.XPATH, value='child::th[@class = "poiproperties__itemlabel"]'),
            tr.find_elements(by=By.XPATH, value="descendant::a"),
        ):
            match label.text:
                case "住所":
                    spot["address"] = a.text
                    href = a.get_attribute("href")
                    assert href is not None
                    spot["googlemap_uri"] = href
                case "URL":
                    href = a.get_attribute("href")
                    assert href is not None
                    spot["link_uri"] = href

    return cast(
        Spot, dict(sorted(spot.items(), key=lambda kv: list(Spot.__annotations__).index(kv[0])))
    )


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
                spot_ids[:] = _pickup_spot_ids(driver)

                if len(spot_ids) >= expected_spot_ids_length:
                    break

                driver.set_window_size(width, 65536)
                sleep(interval)

            if expected_spot_ids_length != len(spot_ids):
                warn(CategoryLengthMismatch(result["id"], expected_spot_ids_length, len(spot_ids)))

    match category["shapes"]:
        case (shape,):
            result["course"] = Course(name=shape["name"], description=shape["description"])

    return result


def _pickup_spot_ids(driver: WebDriver) -> list[SpotID]:
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
