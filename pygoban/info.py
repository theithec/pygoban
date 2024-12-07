from dataclasses import dataclass, field
from datetime import date

from .board import Color


@dataclass
class GameInfo:
    names: dict[Color, str] = field(default_factory=dict)
    ranks: dict[Color, str] = field(default_factory=dict)
    date_played: date = field(default_factory=date.today)
    name: str = "B vs. W"
    app: str | None = None
