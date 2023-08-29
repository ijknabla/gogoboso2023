from collections.abc import Generator, Iterator
from contextlib import AsyncExitStack

from aiohttp import ClientSession
from lxml import html
from lxml.etree import _Element

URI = "http://www.tt.rim.or.jp/~ishato/tiri/code/rireki/12tiba.htm"


async def get_rows(uri: str = URI) -> None:
    async with AsyncExitStack() as stack:
        enter = stack.enter_async_context
        session = await enter(ClientSession())
        response = await enter(session.get(uri))
        document = html.fromstring(await response.text(encoding="cp932"))
        table: _Element
        (table,) = document.xpath("//table")  # type: ignore
        print(list(flatten(table)))


def flatten(
    table: _Element,
) -> Generator[tuple[tuple[int, int], tuple[str, str], tuple[str, str] | None], None, None]:
    tr_iterator: Iterator[_Element]
    tr_iterator = iter(table.xpath("tr"))  # type: ignore
    for tr in tr_iterator:
        try:
            code0: int
            code1: int
            code0, code1 = map(int, tr.xpath("td[position() <= 2]/text()"))  # type: ignore
        except ValueError:
            continue

        code = code0, code1

        shift = 0
        while tr.xpath("td[3]/*/text()") == ["変更"]:
            shift = 2
            tr = next(tr_iterator)

        kanji: str
        kana: str

        if tr.xpath("td[@colspan=2]"):
            kanji, kana = tr.xpath("td[position() = 4 or position() = 6]/text()")  # type: ignore
            parent = kanji, kana
            yield code, parent, None
        else:
            position = f"position() = {4 - shift} or position() = {5 - shift}"
            kanji, kana = tr.xpath(f"td[{position}]/text()")  # type: ignore
            child = kanji, kana
            yield code, parent, child
