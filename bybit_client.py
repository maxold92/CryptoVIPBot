from pybit.unified_trading import HTTP
import pandas as pd
from config import config


class BybitClient:
    def __init__(self):
        kwargs = {"testnet": config.bybit_testnet}
        if config.bybit_api_key and config.bybit_api_secret:
            kwargs.update(api_key=config.bybit_api_key, api_secret=config.bybit_api_secret)
        self.session = HTTP(**kwargs)

    def ticker(self, symbol: str) -> dict:
        data = self.session.get_tickers(category='linear', symbol=symbol)
        return data['result']['list'][0]

    def funding_rate(self, symbol: str) -> float | None:
        try:
            ticker = self.ticker(symbol)
            return float(ticker.get('fundingRate', 0)) * 100
        except Exception:
            return None

    def klines(self, symbol: str, interval: str = '15', limit: int = 250) -> pd.DataFrame:
        data = self.session.get_kline(category='linear', symbol=symbol, interval=interval, limit=limit)
        rows = data['result']['list']
        df = pd.DataFrame(rows, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['time'] = pd.to_datetime(pd.to_numeric(df['time']), unit='ms')
        return df.sort_values('time').reset_index(drop=True)


bybit = BybitClient()
