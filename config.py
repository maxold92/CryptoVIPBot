import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _admin_ids(value: str) -> list[int]:
    result: list[int] = []
    for item in (value or "").replace(";", ",").split(","):
        item = item.strip()
        if item:
            result.append(int(item))
    return result


@dataclass(frozen=True)
class Config:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    group_chat_id: str = os.getenv("GROUP_CHAT_ID", "")
    admin_ids: list[int] = None
    bybit_api_key: str = os.getenv("BYBIT_API_KEY", "")
    bybit_api_secret: str = os.getenv("BYBIT_API_SECRET", "")
    bybit_testnet: bool = _bool(os.getenv("BYBIT_TESTNET", "false"))
    timezone: str = os.getenv("TIMEZONE", "Europe/Kyiv")
    morning_message: str = os.getenv("MORNING_MESSAGE", "☀️ Доброе утро трейдеры)")
    signal_symbols: list[str] = None
    signal_interval_minutes: int = int(os.getenv("SIGNAL_INTERVAL_MINUTES", "15"))

    def __post_init__(self):
        object.__setattr__(self, "admin_ids", _admin_ids(os.getenv("ADMIN_IDS", "")))
        symbols = [x.strip().upper() for x in os.getenv("SIGNAL_SYMBOLS", "BTCUSDT,ETHUSDT").split(",") if x.strip()]
        object.__setattr__(self, "signal_symbols", symbols)


config = Config()
