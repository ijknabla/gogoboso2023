from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self


@dataclass(frozen=True)
class DMS:
    degree: int
    minute: int
    second: float

    @classmethod
    def from_degree(cls, degree: Decimal | float) -> Self:
        if isinstance(degree, float):
            return cls.from_degree(Decimal(degree))

        d, ms = divmod(degree, 1)
        ms *= 60
        m, s = divmod(ms, 1)
        s *= 60

        return cls(degree=int(d), minute=int(m), second=float(s))

    def to_str(self) -> str:
        return f"{self.degree}°{self.minute:0>2}'{self.second:4.2f}\""


def deg2dms(latitude: float, longitude: float) -> str:
    NS = "N" if 0 <= latitude else "S"
    EW = "E" if 0 <= longitude else "W"

    abs_lat = DMS.from_degree(abs(latitude)).to_str()
    abs_lng = DMS.from_degree(abs(longitude)).to_str()

    return f"{abs_lat}{NS} {abs_lng}{EW}"
