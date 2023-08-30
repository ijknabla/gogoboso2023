from enum import Enum
from typing import NewType

MunicipalityID = NewType("MunicipalityID", int)


class Notation(Enum):
    default = 0
    hiragana = 1


SpotID = NewType("SpotID", int)
URI = NewType("URI", str)
