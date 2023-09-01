import json
import re
from collections.abc import Generator
from typing import TypedDict, cast

import click
from lxml import html
from lxml.etree import _Element
from selenium import webdriver
from selenium.webdriver.common.by import By

from gobo.__main__ import run_decorator


@click.command
@click.option("--headed/--headless", default=False)
@run_decorator
async def main(headed: bool) -> None:
    options = webdriver.ChromeOptions()
    # 日本語に指定するオプションを入れないと、すべてのスポットの情報が見られない
    options.add_argument("--lang=ja-JP")  # type: ignore

    if not headed:
        options.add_argument("--headless")  # type: ignore

    options.add_experimental_option("prefs", {"intl.accept_languages": "ja"})

    driver = webdriver.Chrome(options=options)
    driver.get("https://platinumaps.jp/d/gogo-boso?list=1")
    driver.get("https://platinumaps.jp/d/gogo-boso")
    (frame,) = driver.find_elements(by=By.XPATH, value="//iframe")
    driver.switch_to.frame(frame)

    (boot_option,) = find_boot_options(html.fromstring(driver.page_source))

    print(json.dumps(boot_option, indent=2))


class BootOption(TypedDict):
    ...


def find_boot_options(document: _Element) -> Generator[BootOption, None, None]:
    pattern = re.compile(r"window\.__bootOptions\s*=\s*(?P<json>.*?);")
    text: str
    for text in document.xpath("//script/text()"):  # type: ignore
        searched = pattern.search(text)
        if searched is not None:
            yield cast(BootOption, json.loads(searched.group("json")))


if __name__ == "__main__":
    main()
