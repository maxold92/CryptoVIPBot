from __future__ import annotations

import pandas as pd
from pybit.unified_trading import HTTP
from config import config


class BybitClient:
    def __init__(self) -> None:
        kwargs = {"testnet": config.bybit_testnet}
        if config.bybit_api_key and config.bybit_api_secret:
            kwargs.update(api_key=config.bybit_api_key, api_secret=config.bybit_api_secret)
        self.session = HTTP(**kwargs)

    def ticker(self, symbol: str) -> dict:
        data = self.session.get_tickers(category="linear", symbol=symbol)
        return data["result"]["list"][0]

    def price(self, symbol: str) -> float:
        return float(self.ticker(symbol)["lastPrice"])

    def funding_rate(self, symbol: str) -> float:
        try:
            return float(self.ticker(symbol).get("fundingRate", 0.0)) * 100
        except Exception:
            return 0.0

    def klines(self, symbol: str, interval: str = "15", limit: int = 250) -> pd.DataFrame:
        data = self.session.get_kline(category="linear", symbol=symbol, interval=interval, limit=limit)
        rows = data["result"]["list"]
        df = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume", "turnover"])
        for col in ["open", "high", "low", "close", "volume", "turnover"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["time"] = pd.to_datetime(pd.to_numeric(df["time"]), unit="ms")
        return df.sort_values("time").reset_index(drop=True)

    def open_interest(self, symbol: str, interval: str = "15min") -> dict:
        try:
            data = self.session.get_open_interest(category="linear", symbol=symbol, intervalTime=interval, limit=2)
            rows = data["result"]["list"]
            if len(rows) < 2:
                val = float(rows[0]["openInterest"])
                return {"current": val, "previous": val, "change_pct": 0.0}
            latest = float(rows[0]["openInterest"])
            prev = float(rows[1]["openInterest"])
            change = ((latest - prev) / prev * 100) if prev else 0.0
            return {"current": latest, "previous": prev, "change_pct": change}
        except Exception:
            return {"current": 0.0, "previous": 0.0, "change_pct": 0.0}


bybit = BybitClient()
