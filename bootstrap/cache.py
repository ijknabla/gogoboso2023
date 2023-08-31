from __future__ import annotations

from contextlib import AsyncExitStack, ExitStack, closing, suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict

from aiohttp import ClientSession
from lxml import html
from lxml.etree import _Element

from gobo.types import URI

if TYPE_CHECKING:
    from typing_extensions import Self, NotRequired

import pickle


@dataclass(frozen=True)
class Cache:
    class Content(TypedDict):
        html: NotRequired[dict[URI, str]]

    path: Path
    content: Content = field(init=False, default_factory=lambda: Cache.Content())

    def __post_init__(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(suppress(FileNotFoundError))
            self.content.update(pickle.load(stack.enter_context(self.path.open("rb"))))

    @property
    def html(self) -> dict[URI, str]:
        html = self.content.get("html", {})
        self.content["html"] = html
        return html

    def __enter__(self) -> Self:
        return closing(self).__enter__()

    def __exit__(self, *args: Any) -> Any:
        return closing(self).__exit__(*args)

    def close(self) -> None:
        with ExitStack() as stack:
            pickle.dump(self.content, stack.enter_context(self.path.open("wb")))

    async def get_html(self, uri: URI, encoding: str | None) -> _Element:
        if uri not in self.html:
            async with AsyncExitStack() as stack:
                enter = stack.enter_async_context
                session = await enter(ClientSession())
                response = await enter(session.get(uri))
                self.html[uri] = await response.text(encoding=encoding)

        return html.fromstring(self.html[uri])
