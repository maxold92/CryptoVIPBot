import pandas as pd
from pybit.unified_trading import HTTP
from config import config

class BybitClient:
    def __init__(self):
        kwargs = {"testnet": config.bybit_testnet}
        if config.bybit_api_key and config.bybit_api_secret:
            kwargs.update(api_key=config.bybit_api_key, api_secret=config.bybit_api_secret)
        self.session = HTTP(**kwargs)

    def klines(self, symbol: str, interval: str = "15", limit: int = 200) -> pd.DataFrame:
        data = self.session.get_kline(category="linear", symbol=symbol, interval=interval, limit=limit)
        rows = data.get("result", {}).get("list", [])
        df = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume", "turnover"])
        for col in ["open", "high", "low", "close", "volume", "turnover"]:
            df[col] = df[col].astype(float)
        df["time"] = pd.to_datetime(df["time"].astype(int), unit="ms")
        return df.sort_values("time").reset_index(drop=True)

    def ticker(self, symbol: str) -> dict:
        data = self.session.get_tickers(category="linear", symbol=symbol)
        return data.get("result", {}).get("list", [{}])[0]

    def funding_rate(self, symbol: str) -> float:
        try:
            t = self.ticker(symbol)
            return float(t.get("fundingRate", 0)) * 100
        except Exception:
            return 0.0

    def open_interest_change(self, symbol: str, interval: str = "15min") -> float:
        try:
            data = self.session.get_open_interest(category="linear", symbol=symbol, intervalTime=interval, limit=2)
            rows = data.get("result", {}).get("list", [])
            if len(rows) < 2:
                return 0.0
            newest = float(rows[0].get("openInterest", 0))
            older = float(rows[1].get("openInterest", 0))
            if older == 0:
                return 0.0
            return (newest - older) / older * 100
        except Exception:
            return 0.0

bybit = BybitClient()
