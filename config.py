import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> list[str]:
    return [x.strip().upper() for x in value.split(',') if x.strip()]


def _admin_ids(value: str) -> list[int]:
    ids = []
    for item in value.replace(' ', '').split(','):
        if item.isdigit():
            ids.append(int(item))
    return ids


@dataclass
class Config:
    bot_token: str = os.getenv('BOT_TOKEN', '').strip()
    group_chat_id: str = os.getenv('GROUP_CHAT_ID', '').strip()
    admin_ids: list[int] = None
    bybit_api_key: str = os.getenv('BYBIT_API_KEY', '').strip()
    bybit_api_secret: str = os.getenv('BYBIT_API_SECRET', '').strip()
    bybit_testnet: bool = os.getenv('BYBIT_TESTNET', 'false').lower() == 'true'
    timezone: str = os.getenv('TIMEZONE', 'Europe/Kyiv')
    morning_message: str = os.getenv('MORNING_MESSAGE', '☀️ Доброе утро трейдеры)')
    signal_symbols: list[str] = None
    signal_interval_minutes: int = int(os.getenv('SIGNAL_INTERVAL_MINUTES', '15'))
    min_signal_score: int = int(os.getenv('MIN_SIGNAL_SCORE', '70'))

    def __post_init__(self):
        self.admin_ids = _admin_ids(os.getenv('ADMIN_IDS', ''))
        self.signal_symbols = _split_csv(os.getenv('SIGNAL_SYMBOLS', 'BTCUSDT,ETHUSDT'))


config = Config()
