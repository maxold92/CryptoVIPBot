from __future__ import annotations

import pandas as pd
from pybit.unified_trading import HTTP
from config import config


class BybitClient:
    def __init__(self):
        kwargs = {'testnet': config.bybit_testnet}
        if config.bybit_api_key and config.bybit_api_secret:
            kwargs.update(api_key=config.bybit_api_key, api_secret=config.bybit_api_secret)
        self.session = HTTP(**kwargs)

    def get_klines(self, symbol: str, interval: str = '15', limit: int = 250) -> pd.DataFrame:
        data = self.session.get_kline(category='linear', symbol=symbol, interval=interval, limit=limit)
        rows = data.get('result', {}).get('list', [])
        if not rows:
            raise RuntimeError(f'No kline data for {symbol}')
        df = pd.DataFrame(rows, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
            df[col] = df[col].astype(float)
        df['time'] = pd.to_datetime(df['time'].astype('int64'), unit='ms')
        return df.sort_values('time').reset_index(drop=True)

    def get_ticker(self, symbol: str) -> dict:
        data = self.session.get_tickers(category='linear', symbol=symbol)
        items = data.get('result', {}).get('list', [])
        return items[0] if items else {}

    def get_funding_rate(self, symbol: str) -> str:
        ticker = self.get_ticker(symbol)
        return ticker.get('fundingRate', '')


bybit = BybitClient()
