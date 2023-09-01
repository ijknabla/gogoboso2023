import json

import click
from selenium import webdriver

from bootstrap.platinum import find_boot_options
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

    (boot_option,) = find_boot_options(driver)

    print(json.dumps(boot_option, indent=2))


if __name__ == "__main__":
    main()
