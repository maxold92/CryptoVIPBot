import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> list[str]:
    return [x.strip() for x in value.split(',') if x.strip()]


def _split_ints(value: str) -> list[int]:
    result = []
    for item in value.replace(' ', '').split(','):
        if item:
            result.append(int(item))
    return result


@dataclass(frozen=True)
class Config:
    bot_token: str = os.getenv('BOT_TOKEN', '')
    group_chat_id: str = os.getenv('GROUP_CHAT_ID', '')
    admin_ids: list[int] = None
    bybit_api_key: str = os.getenv('BYBIT_API_KEY', '')
    bybit_api_secret: str = os.getenv('BYBIT_API_SECRET', '')
    bybit_testnet: bool = os.getenv('BYBIT_TESTNET', 'false').lower() == 'true'
    timezone: str = os.getenv('TIMEZONE', 'Europe/Kyiv')
    morning_message: str = os.getenv('MORNING_MESSAGE', '☀️ Доброе утро трейдеры)')
    signal_symbols: list[str] = None
    signal_interval_minutes: int = int(os.getenv('SIGNAL_INTERVAL_MINUTES', '15'))
    signal_timeframe: str = os.getenv('SIGNAL_TIMEFRAME', '15')

    def __post_init__(self):
        object.__setattr__(self, 'admin_ids', _split_ints(os.getenv('ADMIN_IDS', '')))
        object.__setattr__(self, 'signal_symbols', _split_csv(os.getenv('SIGNAL_SYMBOLS', 'BTCUSDT,ETHUSDT')))


config = Config()
