from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from bybit_client import bybit
from indicators import add_indicators, trend_from_df

Direction = Literal["LONG", "SHORT", "NONE"]


@dataclass
class Signal:
    symbol: str
    direction: Direction
    price: float
    score: int
    risk: str
    funding: float
    oi_change: float
    volume_factor: float
    trend_15m: str
    trend_1h: str
    rsi: float
    tp1: float
    tp2: float
    tp3: float
    sl: float
    reasons: list[str]

    def format(self) -> str:
        if self.direction == "NONE":
            return f"⚪ {self.symbol}: сильного сигнала нет\nСила: {self.score}/100"
        icon = "🟢" if self.direction == "LONG" else "🔴"
        stars = "⭐" * max(1, round(self.score / 20))
        reasons = "\n".join(f"✅ {r}" for r in self.reasons) if self.reasons else "—"
        return (
            f"🚨 CryptoVIPBot v1.3\n\n"
            f"{icon} {self.direction}\n"
            f"Монета: {self.symbol}\n"
            f"Цена: {self.price:,.4f}\n\n"
            f"{stars} Сила сигнала: {self.score}/100\n"
            f"⚠️ Риск: {self.risk}\n"
            f"💰 Funding: {self.funding:.4f}%\n"
            f"📊 OI: {self.oi_change:+.2f}%\n"
            f"📦 Volume: x{self.volume_factor:.2f}\n"
            f"📈 Trend 15m: {self.trend_15m}\n"
            f"📈 Trend 1H: {self.trend_1h}\n"
            f"📉 RSI: {self.rsi:.1f}\n\n"
            f"Причины:\n{reasons}\n\n"
            f"🎯 TP1: {self.tp1:,.4f}\n"
            f"🎯 TP2: {self.tp2:,.4f}\n"
            f"🎯 TP3: {self.tp3:,.4f}\n"
            f"🛑 SL: {self.sl:,.4f}\n\n"
            f"Не финансовая рекомендация. Риск контролируй сам."
        )


def _risk(score: int) -> str:
    if score >= 80:
        return "Низкий"
    if score >= 65:
        return "Средний"
    return "Повышенный"


def analyze_symbol(symbol: str) -> Signal:
    df15 = add_indicators(bybit.klines(symbol, interval="15", limit=250))
    df1h = add_indicators(bybit.klines(symbol, interval="60", limit=250))
    last = df15.iloc[-1]
    prev = df15.iloc[-2]
    price = float(last["close"])
    atr = float(last["atr"] or price * 0.01)
    rsi = float(last["rsi"])
    funding = bybit.funding_rate(symbol)
    oi = bybit.open_interest(symbol)
    oi_change = float(oi["change_pct"])
    trend15 = trend_from_df(df15)
    trend1h = trend_from_df(df1h)
    volume_factor = float(last["volume"] / last["volume_ma20"]) if last["volume_ma20"] else 1.0

    long_score = 0
    short_score = 0
    long_reasons: list[str] = []
    short_reasons: list[str] = []

    if trend15 == "UP":
        long_score += 20; long_reasons.append("EMA50 выше EMA200 — тренд 15m вверх")
    elif trend15 == "DOWN":
        short_score += 20; short_reasons.append("EMA50 ниже EMA200 — тренд 15m вниз")

    if trend1h == "UP":
        long_score += 20; long_reasons.append("Тренд 1H вверх")
    elif trend1h == "DOWN":
        short_score += 20; short_reasons.append("Тренд 1H вниз")

    if last["macd"] > last["macd_signal"] and prev["macd"] <= prev["macd_signal"]:
        long_score += 18; long_reasons.append("MACD дал пересечение вверх")
    elif last["macd"] > last["macd_signal"]:
        long_score += 10; long_reasons.append("MACD подтверждает рост")

    if last["macd"] < last["macd_signal"] and prev["macd"] >= prev["macd_signal"]:
        short_score += 18; short_reasons.append("MACD дал пересечение вниз")
    elif last["macd"] < last["macd_signal"]:
        short_score += 10; short_reasons.append("MACD подтверждает снижение")

    if 35 <= rsi <= 58:
        long_score += 14; long_reasons.append(f"RSI {rsi:.1f} — зона для продолжения роста")
    if 42 <= rsi <= 65:
        short_score += 14; short_reasons.append(f"RSI {rsi:.1f} — зона для продолжения снижения")
    if rsi > 72:
        short_score += 8; short_reasons.append("RSI перегрет — возможен откат")
    if rsi < 28:
        long_score += 8; long_reasons.append("RSI перепродан — возможен отскок")

    if volume_factor >= 1.25:
        long_score += 10; short_score += 10
        long_reasons.append(f"Объем выше среднего x{volume_factor:.2f}")
        short_reasons.append(f"Объем выше среднего x{volume_factor:.2f}")

    if oi_change > 0.5:
        long_score += 10; short_score += 10
        long_reasons.append(f"Open Interest растет {oi_change:+.2f}%")
        short_reasons.append(f"Open Interest растет {oi_change:+.2f}%")
    elif oi_change < -0.5:
        long_score -= 5; short_score -= 5

    if funding > 0.05:
        long_score -= 8; short_score += 5
        short_reasons.append("Funding положительный — лонги платят шортам")
    elif funding < -0.05:
        short_score -= 8; long_score += 5
        long_reasons.append("Funding отрицательный — шорты платят лонгам")

    if long_score >= short_score:
        direction: Direction = "LONG" if long_score >= 35 else "NONE"
        score = max(0, min(100, long_score))
        reasons = long_reasons
        tp1, tp2, tp3 = price + atr * 1.0, price + atr * 1.8, price + atr * 2.7
        sl = price - atr * 1.2
    else:
        direction = "SHORT" if short_score >= 35 else "NONE"
        score = max(0, min(100, short_score))
        reasons = short_reasons
        tp1, tp2, tp3 = price - atr * 1.0, price - atr * 1.8, price - atr * 2.7
        sl = price + atr * 1.2

    return Signal(symbol, direction, price, score, _risk(score), funding, oi_change, volume_factor, trend15, trend1h, rsi, tp1, tp2, tp3, sl, reasons[:8])


def analyze_many(symbols: list[str]) -> list[Signal]:
    out: list[Signal] = []
    for s in symbols:
        try:
            out.append(analyze_symbol(s))
        except Exception as e:
            out.append(Signal(s, "NONE", 0, 0, "Ошибка", 0, 0, 0, "ERR", "ERR", 0, 0, 0, 0, 0, [f"Ошибка анализа: {e}"]))
    return sorted(out, key=lambda x: x.score, reverse=True)
