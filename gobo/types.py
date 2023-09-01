from enum import Enum
from typing import NewType


class Area(Enum):
    ベイ = 1
    東葛飾 = 2
    北総 = 3
    九十九里 = 4
    南房総 = 5
    かずさ_臨海 = 6


CategoryID = NewType("CategoryID", int)
MunicipalityID = NewType("MunicipalityID", int)


class Notation(Enum):
    default = 0
    hiragana = 1


SpotID = NewType("SpotID", int)
URI = NewType("URI", str)
