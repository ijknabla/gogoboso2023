from enum import Enum
from typing import NewType

MunicipalityID = NewType("MunicipalityID", int)


class Notation(Enum):
    kanji = 0
    hiragana = 1
