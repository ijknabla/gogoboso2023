from enum import Enum
from typing import NewType


class Area(Enum):
    ベイ = 1
    東葛飾 = 2
    北総 = 3
    九十九里 = 4
    南房総 = 5
    かずさ_臨海 = 6


AreaID = NewType("AreaID", int)
CategoryID = NewType("CategoryID", int)
SpotID = NewType("SpotID", int)
URI = NewType("URI", str)
