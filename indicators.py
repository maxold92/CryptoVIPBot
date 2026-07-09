from dataclasses import dataclass, field

@dataclass
class Signal:
    symbol: str
    direction: str
    score: int
    entry: float
    tp1: float
    tp2: float
    tp3: float
    sl: float
    risk: str
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    indicators: dict = field(default_factory=dict)

    @property
    def is_trade_signal(self) -> bool:
        return self.direction in {"LONG", "SHORT"} and self.score >= 60
