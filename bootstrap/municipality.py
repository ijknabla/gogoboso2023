from collections.abc import AsyncGenerator, Generator, Iterator
from contextlib import AsyncExitStack
from sqlite3 import Cursor

from aiohttp import ClientSession
from lxml import html
from lxml.etree import _Element

from gobo.types import Notation

URI = "http://www.tt.rim.or.jp/~ishato/tiri/code/rireki/12tiba.htm"
ORDER = [
    "野田市",
    "流山市",
    "柏市",
    "我孫子市",
    "松戸市",
    "浦安市",
    "市川市",
    "鎌ヶ谷市",
    "白井市",
    "船橋市",
    "八千代市",
    "印西市",
    "習志野市",
    "若葉区",
    "中央区",
    "美浜区",
    "緑区",
    "稲毛区",
    "花見川区",
    "四街道市",
    "佐倉市",
    "栄町",
    "酒々井町",
    "成田市",
    "八街市",
    "富里市",
    "神崎町",
    "東庄町",
    "多古町",
    "香取市",
    "銚子市",
    "旭市",
    "芝山町",
    "横芝光町",
    "九十九里町",
    "匝瑳市",
    "山武市",
    "東金市",
    "大網白里市",
    "市原市",
    "大多喜町",
    "御宿町",
    "長柄町",
    "白子町",
    "長南町",
    "睦沢町",
    "長生村",
    "一宮町",
    "茂原市",
    "袖ヶ浦市",
    "木更津市",
    "富津市",
    "君津市",
    "いすみ市",
    "鋸南町",
    "鴨川市",
    "勝浦市",
    "南房総市",
    "館山市",
]


def create_and_insert(cursor: Cursor, document: _Element) -> None:
    rows = list(iter_rows(document))
    kanji = {kanji: id for id, _, (kanji, _) in rows}

    cursor.execute(
        """
CREATE TABLE municipality_names
(
    municipality_id INTEGER NOT NULL,
    notation_id INTEGER NOT NULL,
    municipality_name TEXT UNIQUE NOT NULL,
    PRIMARY KEY(municipality_id, notation_id)
)
        """
    )
    cursor.executemany(
        """
INSERT INTO municipality_names
(
    municipality_id, notation_id, municipality_name
)
VALUES
(
    ?, ?, ?
)
        """,
        (
            (id, notation.value, name)
            for id, _, names in rows
            for notation, name in zip(Notation, names)
        ),
    )

    cursor.execute(
        """
CREATE TABLE municipality_tree
(
    parent_id INTEGER NULL,
    child_id INTEGER NOT NULL
)
        """
    )
    cursor.executemany(
        """
INSERT INTO municipality_tree
(
    parent_id, child_id
)
VALUES
(
    ?, ?
)
        """,
        ((parent_id, child_id) for child_id, parent_id, _ in rows),
    )

    cursor.execute(
        """
CREATE TABLE municipality_list
(
    `index` INTEGER PRIMARY KEY,
    id INTEGER UNIQUE NOT NULL
)
        """
    )
    cursor.executemany(
        """
INSERT INTO municipality_list
(
    `index`, id
)
VALUES
(
    ?, ?
)
        """,
        ((i, kanji[s]) for i, s in enumerate(ORDER, start=1)),
    )


def iter_rows(document: _Element) -> Generator[tuple[int, int | None, tuple[str, str]], None, None]:
    table: _Element
    (table,) = document.xpath("//table")  # type: ignore

    rows = list(flatten(table))
    parents = {child: code for code, _, child in rows}
    for code, parent, child in rows:
        if parent is None:
            yield code2int(code), None, child
        else:
            yield code2int(code), code2int(parents[parent]), child


async def get_rows(
    uri: str = URI,
) -> AsyncGenerator[tuple[int, int | None, tuple[str, str]], None]:
    async with AsyncExitStack() as stack:
        enter = stack.enter_async_context
        session = await enter(ClientSession())
        response = await enter(session.get(uri))
        document = html.fromstring(await response.text(encoding="cp932"))
        table: _Element
        (table,) = document.xpath("//table")  # type: ignore

        rows = list(flatten(table))
        parents = {child: code for code, _, child in rows}
        for code, parent, child in rows:
            if parent is None:
                yield code2int(code), None, child
            else:
                yield code2int(code), code2int(parents[parent]), child


def flatten(
    table: _Element,
) -> Generator[tuple[tuple[int, int], tuple[str, str] | None, tuple[str, str]], None, None]:
    pref = ("千葉県", "ちばけん")
    yield (12, 000), None, pref

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
            yield code, pref, parent
        else:
            position = f"position() = {4 - shift} or position() = {5 - shift}"
            kanji, kana = tr.xpath(f"td[{position}]/text()")  # type: ignore
            child = kanji, kana
            yield code, parent, child


def code2int(code: tuple[int, int]) -> int:
    return code[0] * 1000 + code[1]
