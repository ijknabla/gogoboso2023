from __future__ import annotations

from typing import TYPE_CHECKING, NewType, TypedDict

if TYPE_CHECKING:
    from typing_extensions import NotRequired


class Data(TypedDict):
    spots: dict[SpotID, Spot]


SpotID = NewType("SpotID", int)


class Spot(TypedDict):
    id: SpotID
    name: str
    address: str
    uri: NotRequired[str]
