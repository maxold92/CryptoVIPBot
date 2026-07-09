import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _int_list(value: str):
    return [int(x.strip()) for x in value.replace(" ", "").split(",") if x.strip()]

@dataclass
class Config:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    group_chat_id: str = os.getenv("GROUP_CHAT_ID", "")
    admin_ids: list[int] = None
    bybit_api_key: str = os.getenv("BYBIT_API_KEY", "")
    bybit_api_secret: str = os.getenv("BYBIT_API_SECRET", "")
    bybit_testnet: bool = os.getenv("BYBIT_TESTNET", "false").lower() == "true"
    timezone: str = os.getenv("TIMEZONE", "Europe/Kyiv")
    morning_message: str = os.getenv("MORNING_MESSAGE", "☀️ Доброе утро трейдеры)")
    signal_symbols: list[str] = None
    signal_interval_minutes: int = int(os.getenv("SIGNAL_INTERVAL_MINUTES", "15"))
    min_auto_score: int = int(os.getenv("MIN_AUTO_SCORE", "80"))
    auto_signals: bool = os.getenv("AUTO_SIGNALS", "false").lower() == "true"

    def __post_init__(self):
        self.admin_ids = _int_list(os.getenv("ADMIN_IDS", ""))
        self.signal_symbols = [x.strip().upper() for x in os.getenv("SIGNAL_SYMBOLS", "BTCUSDT,ETHUSDT").split(",") if x.strip()]

config = Config()
