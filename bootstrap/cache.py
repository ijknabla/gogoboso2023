from __future__ import annotations

from contextlib import ExitStack, closing, suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from typing_extensions import Self

import pickle


@dataclass(frozen=True)
class Cache:
    class Content(TypedDict):
        ...

    path: Path
    content: Content = field(init=False, default_factory=Content)

    def __post_init__(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(suppress(FileNotFoundError))
            self.content.update(pickle.load(stack.enter_context(self.path.open("rb"))))

    def __enter__(self) -> Self:
        return closing(self).__enter__()

    def __exit__(self, *args: Any) -> Any:
        return closing(self).__exit__(*args)

    def close(self) -> None:
        with ExitStack() as stack:
            pickle.dump(self.content, stack.enter_context(self.path.open("wb")))
