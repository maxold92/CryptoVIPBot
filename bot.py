from pybit.unified_trading import HTTP
from config import BYBIT_API_KEY, BYBIT_API_SECRET, BYBIT_TESTNET

class BybitClient:
    def __init__(self):
        self.session = HTTP(
            testnet=BYBIT_TESTNET,
            api_key=BYBIT_API_KEY or None,
            api_secret=BYBIT_API_SECRET or None,
        )

    def klines(self, symbol: str, interval: str = "15", limit: int = 200):
        data = self.session.get_kline(category="linear", symbol=symbol, interval=interval, limit=limit)
        rows = data.get("result", {}).get("list", [])
        rows = list(reversed(rows))
        candles = []
        for r in rows:
            candles.append({
                "time": int(r[0]),
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "volume": float(r[5]),
            })
        return candles

    def ticker(self, symbol: str):
        data = self.session.get_tickers(category="linear", symbol=symbol)
        item = data.get("result", {}).get("list", [{}])[0]
        return item
