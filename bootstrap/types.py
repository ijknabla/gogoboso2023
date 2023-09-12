from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from gobo.types import CategoryID, SpotID

if TYPE_CHECKING:
    from typing_extensions import NotRequired


class BootOption(TypedDict):
    mapCategories: list[MapCategory]
    stampRallies: list[StampRally]
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


class StampRally(TypedDict):
    subAreaCodes: list[SubAreaCode]


class SubAreaCode(TypedDict):
    Value: str
    Text: str


class StampRallySpot(TypedDict):
    spotLng: float
    spotLat: float
    spotId: SpotID
    spotTitle: str


class Spot(TypedDict):
    id: SpotID
    name: str
    subtitle: NotRequired[str]
    description: str
    address: str
    googlemap_uri: str
    link_uri: NotRequired[str]


class Category(TypedDict):
    id: CategoryID
    parent_id: CategoryID
    name: str
    ref: str
    spot_ids: list[SpotID]
    course: NotRequired[Course]


class Course(TypedDict):
    name: str
    description: str
