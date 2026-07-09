from __future__ import annotations

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from bybit_client import bybit


def analyze_symbol(symbol: str) -> str | None:
    df = bybit.klines(symbol, interval="15", limit=200)
    if len(df) < 100:
        return None

    close = df["close"]
    volume = df["volume"]
    last_price = float(close.iloc[-1])

    ema50 = EMAIndicator(close, window=50).ema_indicator()
    ema200 = EMAIndicator(close, window=200).ema_indicator()
    rsi = RSIIndicator(close, window=14).rsi()
    macd = MACD(close).macd_diff()

    vol_avg = volume.tail(30).mean()
    vol_now = volume.iloc[-1]
    funding = bybit.funding_rate(symbol)

    score_long = 0
    score_short = 0
    reasons_long: list[str] = []
    reasons_short: list[str] = []

    if ema50.iloc[-1] > ema200.iloc[-1]:
        score_long += 25
        reasons_long.append("EMA50 выше EMA200")
    else:
        score_short += 25
        reasons_short.append("EMA50 ниже EMA200")

    if rsi.iloc[-1] < 35:
        score_long += 20
        reasons_long.append(f"RSI низкий: {rsi.iloc[-1]:.1f}")
    elif rsi.iloc[-1] > 65:
        score_short += 20
        reasons_short.append(f"RSI высокий: {rsi.iloc[-1]:.1f}")

    if macd.iloc[-1] > 0:
        score_long += 20
        reasons_long.append("MACD в пользу LONG")
    else:
        score_short += 20
        reasons_short.append("MACD в пользу SHORT")

    if vol_now > vol_avg * 1.5:
        score_long += 10
        score_short += 10
        reasons_long.append("объем выше среднего")
        reasons_short.append("объем выше среднего")

    if funding is not None:
        if funding < 0:
            score_long += 10
            reasons_long.append(f"Funding отрицательный: {funding:.4%}")
        elif funding > 0.0005:
            score_short += 10
            reasons_short.append(f"Funding положительный: {funding:.4%}")

    if score_long >= 65 and score_long >= score_short + 10:
        direction = "🟢 LONG"
        score = min(score_long, 95)
        reasons = reasons_long
    elif score_short >= 65 and score_short >= score_long + 10:
        direction = "🔴 SHORT"
        score = min(score_short, 95)
        reasons = reasons_short
    else:
        return None

    tp1 = last_price * (1.012 if direction.endswith("LONG") else 0.988)
    tp2 = last_price * (1.025 if direction.endswith("LONG") else 0.975)
    sl = last_price * (0.988 if direction.endswith("LONG") else 1.012)

    reasons_text = "\n".join(f"✅ {r}" for r in reasons)
    return (
        f"{direction}\n\n"
        f"Монета: {symbol}\n"
        f"Цена: {last_price:.6g}\n"
        f"Вероятность: {score}%\n\n"
        f"Причины:\n{reasons_text}\n\n"
        f"TP1: {tp1:.6g}\n"
        f"TP2: {tp2:.6g}\n"
        f"SL: {sl:.6g}\n\n"
        f"⚠️ Не финансовая рекомендация. Соблюдай риск-менеджмент."
    )
