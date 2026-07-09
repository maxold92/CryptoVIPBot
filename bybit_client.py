import pandas as pd
from pybit.unified_trading import HTTP
from config import config


class BybitClient:
    def __init__(self):
        kwargs = {'testnet': config.bybit_testnet}
        if config.bybit_api_key and config.bybit_api_secret:
            kwargs.update(api_key=config.bybit_api_key, api_secret=config.bybit_api_secret)
        self.session = HTTP(**kwargs)

    def get_kline(self, symbol: str, interval: str = '15', limit: int = 250) -> pd.DataFrame:
        data = self.session.get_kline(category='linear', symbol=symbol, interval=interval, limit=limit)
        rows = data.get('result', {}).get('list', [])
        if not rows:
            raise RuntimeError(f'No kline data for {symbol}')
        df = pd.DataFrame(rows, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['time'] = pd.to_datetime(pd.to_numeric(df['time']), unit='ms')
        return df.sort_values('time').reset_index(drop=True)

    def get_funding_rate(self, symbol: str) -> float:
        try:
            data = self.session.get_tickers(category='linear', symbol=symbol)
            item = data.get('result', {}).get('list', [{}])[0]
            return float(item.get('fundingRate', 0)) * 100
        except Exception:
            return 0.0

    def get_open_interest_change(self, symbol: str) -> float:
        try:
            data = self.session.get_open_interest(category='linear', symbol=symbol, intervalTime='15min', limit=2)
            rows = data.get('result', {}).get('list', [])
            if len(rows) < 2:
                return 0.0
            latest = float(rows[0].get('openInterest', 0))
            prev = float(rows[1].get('openInterest', 0))
            return 0.0 if prev == 0 else (latest - prev) / prev * 100
        except Exception:
            return 0.0


bybit = BybitClient()
