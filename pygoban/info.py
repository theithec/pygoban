from dataclasses import dataclass, field
from datetime import date

from .board import Color


@dataclass
class GameInfo:
    names: dict[Color, str] = field(default_factory=dict)
    ranks: dict[Color, str] = field(default_factory=dict)
    date_played: date = field(default_factory=date.today)
    app: str | None = None
    result: str | None = None
    ruleset: str | None = None

    @property
    def name(self):
        namespart = " vs. ".join(self.names.values())
        return " ".join((namespart, self.date_played.isoformat()))
