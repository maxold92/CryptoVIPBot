from __future__ import annotations

import pandas as pd
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    close = df["close"]
    high = df["high"]
    low = df["low"]
    df["ema50"] = EMAIndicator(close=close, window=50).ema_indicator()
    df["ema200"] = EMAIndicator(close=close, window=200).ema_indicator()
    df["rsi"] = RSIIndicator(close=close, window=14).rsi()
    macd = MACD(close=close)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["atr"] = AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
    df["adx"] = ADXIndicator(high=high, low=low, close=close, window=14).adx()
    df["volume_ma20"] = df["volume"].rolling(20).mean()
    return df


def trend_from_df(df: pd.DataFrame) -> str:
    last = df.iloc[-1]
    if last["ema50"] > last["ema200"]:
        return "UP"
    if last["ema50"] < last["ema200"]:
        return "DOWN"
    return "FLAT"
