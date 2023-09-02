from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from gobo.types import CategoryID, SpotID

if TYPE_CHECKING:
    from typing_extensions import NotRequired


class Category(TypedDict):
    id: CategoryID
    parent_id: CategoryID
    name: str
    ref: str
    spots: list[str]
    course: NotRequired[Course]


class Course(TypedDict):
    name: str
    description: str


class Spot(TypedDict):
    id: SpotID
    name: str
    address: str
    uri: NotRequired[str]
