from __future__ import annotations

import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from bybit_client import bybit
from config import config

_last_sent: dict[str, str] = {}


def _fmt(num: float, digits: int = 2) -> str:
    if num >= 1000:
        return f'{num:,.2f}'.replace(',', ' ')
    if num >= 1:
        return f'{num:.4f}'
    return f'{num:.6f}'


def _indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['ema50'] = EMAIndicator(df['close'], window=50).ema_indicator()
    df['ema200'] = EMAIndicator(df['close'], window=200).ema_indicator()
    df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
    macd = MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['atr'] = AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
    return df


def analyze_symbol(symbol: str) -> dict | None:
    df = bybit.get_klines(symbol, interval=config.signal_timeframe, limit=250)
    df = _indicators(df).dropna()
    if len(df) < 5:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = float(last['close'])
    atr = float(last['atr'])
    funding = bybit.get_funding_rate(symbol)

    long_reasons = []
    short_reasons = []

    if last['ema50'] > last['ema200']:
        long_reasons.append('EMA50 выше EMA200 — тренд вверх')
    else:
        short_reasons.append('EMA50 ниже EMA200 — тренд вниз')

    if prev['macd'] <= prev['macd_signal'] and last['macd'] > last['macd_signal']:
        long_reasons.append('MACD пересек вверх')
    if prev['macd'] >= prev['macd_signal'] and last['macd'] < last['macd_signal']:
        short_reasons.append('MACD пересек вниз')

    if 35 <= last['rsi'] <= 55 and last['ema50'] > last['ema200']:
        long_reasons.append(f'RSI {last["rsi"]:.1f} — есть место для роста')
    if 45 <= last['rsi'] <= 65 and last['ema50'] < last['ema200']:
        short_reasons.append(f'RSI {last["rsi"]:.1f} — есть место для снижения')

    if last['close'] > prev['high']:
        long_reasons.append('Цена пробила максимум прошлой свечи')
    if last['close'] < prev['low']:
        short_reasons.append('Цена пробила минимум прошлой свечи')

    long_score = len(long_reasons)
    short_score = len(short_reasons)

    if long_score >= 3 and long_score > short_score:
        direction = 'LONG'
        reasons = long_reasons
        sl = price - atr * 1.5
        tp1 = price + atr * 1.2
        tp2 = price + atr * 2.0
        tp3 = price + atr * 3.0
        emoji = '🟢'
    elif short_score >= 3 and short_score > long_score:
        direction = 'SHORT'
        reasons = short_reasons
        sl = price + atr * 1.5
        tp1 = price - atr * 1.2
        tp2 = price - atr * 2.0
        tp3 = price - atr * 3.0
        emoji = '🔴'
    else:
        return None

    signal_id = f'{symbol}:{direction}:{round(price, 2)}'
    if _last_sent.get(symbol) == signal_id:
        return None
    _last_sent[symbol] = signal_id

    probability = min(95, 60 + max(long_score, short_score) * 8)
    return {
        'symbol': symbol,
        'direction': direction,
        'emoji': emoji,
        'price': price,
        'rsi': float(last['rsi']),
        'funding': funding,
        'probability': probability,
        'reasons': reasons,
        'tp1': tp1,
        'tp2': tp2,
        'tp3': tp3,
        'sl': sl,
    }


def format_signal(signal: dict) -> str:
    reasons = '\n'.join([f'✅ {r}' for r in signal['reasons']])
    funding_text = ''
    if signal.get('funding') not in ('', None):
        try:
            funding_text = f"\n💰 Funding: {float(signal['funding']) * 100:.4f}%"
        except Exception:
            funding_text = f"\n💰 Funding: {signal['funding']}"

    return (
        f"🚨 VIP SIGNAL\n\n"
        f"{signal['emoji']} {signal['direction']}\n"
        f"Монета: {signal['symbol']}\n"
        f"Цена: {_fmt(signal['price'])}\n"
        f"Вероятность: {signal['probability']}%"
        f"{funding_text}\n\n"
        f"Причины:\n{reasons}\n\n"
        f"🎯 TP1: {_fmt(signal['tp1'])}\n"
        f"🎯 TP2: {_fmt(signal['tp2'])}\n"
        f"🎯 TP3: {_fmt(signal['tp3'])}\n"
        f"🛑 SL: {_fmt(signal['sl'])}\n\n"
        f"⚠️ Не финсовет. Риск рассчитывай сам."
    )
