import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "y", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except ValueError:
        return default


def _list(name: str, default: str) -> list[str]:
    return [x.strip().upper() for x in os.getenv(name, default).split(",") if x.strip()]


def _admin_ids() -> list[int]:
    raw = os.getenv("ADMIN_IDS", "")
    ids: list[int] = []
    for item in raw.replace(" ", "").split(","):
        if item and item.lstrip("-").isdigit():
            ids.append(int(item))
    return ids


@dataclass(frozen=True)
class Config:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    group_chat_id: str = os.getenv("GROUP_CHAT_ID", "")
    admin_ids: list[int] = None
    bybit_api_key: str = os.getenv("BYBIT_API_KEY", "")
    bybit_api_secret: str = os.getenv("BYBIT_API_SECRET", "")
    bybit_testnet: bool = _bool("BYBIT_TESTNET", False)
    timezone: str = os.getenv("TIMEZONE", "Europe/Kyiv")
    morning_message: str = os.getenv("MORNING_MESSAGE", "☀️ Доброе утро трейдеры)")
    signal_symbols: list[str] = None
    signal_interval_minutes: int = _int("SIGNAL_INTERVAL_MINUTES", 15)
    min_signal_score: int = _int("MIN_SIGNAL_SCORE", 65)
    auto_signals: bool = _bool("AUTO_SIGNALS", True)

    def __post_init__(self):
        object.__setattr__(self, "admin_ids", _admin_ids())
        object.__setattr__(self, "signal_symbols", _list("SIGNAL_SYMBOLS", "BTCUSDT,ETHUSDT"))


config = Config()
