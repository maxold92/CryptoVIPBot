import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _int_list(value: str) -> list[int]:
    return [int(x.strip()) for x in value.split(',') if x.strip()]


@dataclass(frozen=True)
class Config:
    bot_token: str = os.getenv('BOT_TOKEN', '')
    vip_group_id: int = int(os.getenv('VIP_GROUP_ID', '0'))
    admin_ids: list[int] = None
    bybit_api_key: str = os.getenv('BYBIT_API_KEY', '')
    bybit_api_secret: str = os.getenv('BYBIT_API_SECRET', '')
    bybit_testnet: bool = os.getenv('BYBIT_TESTNET', 'false').lower() == 'true'
    timezone: str = os.getenv('TIMEZONE', 'Europe/Kiev')
    morning_message: str = os.getenv('MORNING_MESSAGE', '☀️ Доброе утро трейдеры)')
    scan_symbols: list[str] = None
    scan_interval_minutes: int = int(os.getenv('SCAN_INTERVAL_MINUTES', '5'))
    signal_min_score: int = int(os.getenv('SIGNAL_MIN_SCORE', '70'))

    def __post_init__(self):
        object.__setattr__(self, 'admin_ids', _int_list(os.getenv('ADMIN_IDS', '')))
        symbols = [s.strip().upper() for s in os.getenv('SCAN_SYMBOLS', 'BTCUSDT,ETHUSDT').split(',') if s.strip()]
        object.__setattr__(self, 'scan_symbols', symbols)

    def validate(self) -> None:
        if not self.bot_token:
            raise RuntimeError('BOT_TOKEN не указан в .env')
        if not self.vip_group_id:
            raise RuntimeError('VIP_GROUP_ID не указан в .env')

config = Config()
