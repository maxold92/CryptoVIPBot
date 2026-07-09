from dataclasses import dataclass
from typing import List
import pandas as pd
import ta
from bybit_client import bybit

@dataclass
class Signal:
    symbol: str
    direction: str
    price: float
    score: int
    risk: str
    funding: float
    oi_change: float
    volume_factor: float
    trend_15m: str
    trend_1h: str
    trend_4h: str
    rsi: float
    adx: float
    atr_pct: float
    tp1: float
    tp2: float
    tp3: float
    sl: float
    reasons: List[str]
    warnings: List[str]


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["ema200"] = ta.trend.ema_indicator(df["close"], window=200)
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)
    macd = ta.trend.MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["atr"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=14)
    adx = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14)
    df["adx"] = adx.adx()
    df["vol_ma"] = df["volume"].rolling(20).mean()
    return df


def _trend(symbol: str, tf: str) -> str:
    try:
        df = _prepare(bybit.klines(symbol, interval=tf, limit=220))
        last = df.iloc[-1]
        return "UP" if last["ema50"] > last["ema200"] else "DOWN"
    except Exception:
        return "UNKNOWN"


def analyze_symbol(symbol: str) -> Signal | None:
    df = _prepare(bybit.klines(symbol, interval="15", limit=220))
    last = df.iloc[-1]
    price = float(last["close"])
    rsi = float(last["rsi"])
    adx = float(last["adx"])
    atr = float(last["atr"])
    atr_pct = (atr / price) * 100 if price else 0
    volume_factor = float(last["volume"] / last["vol_ma"]) if last["vol_ma"] and last["vol_ma"] > 0 else 0
    funding = bybit.funding_rate(symbol)
    oi_change = bybit.open_interest_change(symbol)

    trend_15m = "UP" if last["ema50"] > last["ema200"] else "DOWN"
    trend_1h = _trend(symbol, "60")
    trend_4h = _trend(symbol, "240")

    long_score = 0
    short_score = 0
    reasons_long, reasons_short = [], []
    warnings = []

    if trend_15m == "UP":
        long_score += 15; reasons_long.append("EMA50 выше EMA200 — тренд 15m вверх")
    else:
        short_score += 15; reasons_short.append("EMA50 ниже EMA200 — тренд 15m вниз")
    if trend_1h == "UP":
        long_score += 12; reasons_long.append("Тренд 1H вверх")
    elif trend_1h == "DOWN":
        short_score += 12; reasons_short.append("Тренд 1H вниз")
    if trend_4h == "UP":
        long_score += 15; reasons_long.append("Тренд 4H вверх")
    elif trend_4h == "DOWN":
        short_score += 15; reasons_short.append("Тренд 4H вниз")

    if last["macd"] > last["macd_signal"]:
        long_score += 10; reasons_long.append("MACD подтверждает рост")
    else:
        short_score += 10; reasons_short.append("MACD подтверждает снижение")

    if 35 <= rsi <= 58:
        long_score += 8; reasons_long.append(f"RSI {rsi:.1f} — зона для продолжения роста")
    if 42 <= rsi <= 65:
        short_score += 8; reasons_short.append(f"RSI {rsi:.1f} — зона для продолжения снижения")

    if adx >= 25:
        long_score += 8 if trend_15m == "UP" else 0
        short_score += 8 if trend_15m == "DOWN" else 0
    else:
        warnings.append("ADX ниже 25 — тренд слабый")

    if volume_factor >= 1.2:
        if trend_15m == "UP": long_score += 8
        if trend_15m == "DOWN": short_score += 8
    elif volume_factor < 0.7:
        warnings.append("Объём ниже среднего")

    if oi_change > 0.2:
        if trend_15m == "UP": long_score += 10
        if trend_15m == "DOWN": short_score += 10
    elif oi_change < -0.2:
        warnings.append("OI снижается — движение может быть слабее")

    if funding > 0.08:
        long_score -= 8; warnings.append("Funding высокий — long может быть перегрет")
    elif funding < -0.08:
        short_score -= 8; warnings.append("Funding отрицательный — short может быть перегрет")
    else:
        long_score += 4; short_score += 4

    if long_score >= short_score:
        direction = "LONG"
        score = max(0, min(100, long_score))
        reasons = reasons_long
        tp1 = price + atr * 1.0; tp2 = price + atr * 1.8; tp3 = price + atr * 2.8; sl = price - atr * 1.2
    else:
        direction = "SHORT"
        score = max(0, min(100, short_score))
        reasons = reasons_short
        tp1 = price - atr * 1.0; tp2 = price - atr * 1.8; tp3 = price - atr * 2.8; sl = price + atr * 1.2

    risk = "Низкий" if score >= 75 and len(warnings) == 0 else "Средний" if score >= 55 else "Повышенный"

    return Signal(symbol, direction, price, score, risk, funding, oi_change, volume_factor, trend_15m, trend_1h, trend_4h, rsi, adx, atr_pct, tp1, tp2, tp3, sl, reasons, warnings)


def format_signal(sig: Signal) -> str:
    emoji = "🟢" if sig.direction == "LONG" else "🔴"
    stars = "⭐" * max(1, min(5, round(sig.score / 20)))
    reasons = "\n".join([f"✅ {r}" for r in sig.reasons[:6]]) or "—"
    warns = "\n".join([f"⚠️ {w}" for w in sig.warnings])
    if warns:
        warns = "\n\nРиски:\n" + warns
    return (
        f"🚨 CryptoVIPBot v2.0\n\n"
        f"{emoji} {sig.direction}\n"
        f"Монета: {sig.symbol}\n"
        f"Цена: {sig.price:,.4f}\n\n"
        f"{stars} Сила сигнала: {sig.score}/100\n"
        f"⚠️ Риск: {sig.risk}\n"
        f"💰 Funding: {sig.funding:.4f}%\n"
        f"📊 OI: {sig.oi_change:+.2f}%\n"
        f"📦 Volume: x{sig.volume_factor:.2f}\n"
        f"📈 Trend 15m: {sig.trend_15m}\n"
        f"📈 Trend 1H: {sig.trend_1h}\n"
        f"📈 Trend 4H: {sig.trend_4h}\n"
        f"📉 RSI: {sig.rsi:.1f}\n"
        f"💪 ADX: {sig.adx:.1f}\n"
        f"🌊 ATR: {sig.atr_pct:.2f}%\n\n"
        f"Причины:\n{reasons}"
        f"{warns}\n\n"
        f"🎯 TP1: {sig.tp1:,.4f}\n"
        f"🎯 TP2: {sig.tp2:,.4f}\n"
        f"🎯 TP3: {sig.tp3:,.4f}\n"
        f"🛑 SL: {sig.sl:,.4f}\n\n"
        f"Не финансовая рекомендация. Риск контролируй сам."
    )
