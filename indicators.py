import pandas as pd
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['ema50'] = EMAIndicator(df['close'], window=50).ema_indicator()
    df['ema200'] = EMAIndicator(df['close'], window=200).ema_indicator()
    df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
    macd = MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['atr'] = AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
    df['adx'] = ADXIndicator(df['high'], df['low'], df['close'], window=14).adx()
    df['volume_sma20'] = df['volume'].rolling(20).mean()
    return df.dropna().reset_index(drop=True)
