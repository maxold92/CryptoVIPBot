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
    trend_4h: str
    rsi: float
    adx: float
    atr_pct: float
    tp1: float
    tp2: float
    tp3: float
    sl: float
    reasons: list[str]
    warnings: list[str]

    def format(self) -> str:
        if self.direction == "NONE":
            warn = "\n".join(f"⚠️ {w}" for w in self.warnings) if self.warnings else ""
            return f"⚪ {self.symbol}: сильного сигнала нет\nСила: {self.score}/100" + (f"\n{warn}" if warn else "")

        icon = "🟢" if self.direction == "LONG" else "🔴"
        stars = "⭐" * max(1, min(5, round(self.score / 20)))
        reasons = "\n".join(f"✅ {r}" for r in self.reasons) if self.reasons else "—"
        warnings = "\n".join(f"⚠️ {w}" for w in self.warnings) if self.warnings else "—"
        return (
            f"🚨 CryptoVIPBot v1.4\n\n"
            f"{icon} {self.direction}\n"
            f"Монета: {self.symbol}\n"
            f"Цена: {self.price:,.4f}\n\n"
            f"{stars} Сила сигнала: {self.score}/100\n"
            f"⚠️ Риск: {self.risk}\n"
            f"💰 Funding: {self.funding:.4f}% ({_funding_text(self.funding)})\n"
            f"📊 OI: {self.oi_change:+.2f}%\n"
            f"📦 Volume: x{self.volume_factor:.2f} ({_volume_text(self.volume_factor)})\n"
            f"📈 Trend 15m: {self.trend_15m}\n"
            f"📈 Trend 1H: {self.trend_1h}\n"
            f"📈 Trend 4H: {self.trend_4h}\n"
            f"📉 RSI: {self.rsi:.1f}\n"
            f"💪 ADX: {self.adx:.1f} ({_adx_text(self.adx)})\n"
            f"🌊 ATR: {self.atr_pct:.2f}%\n\n"
            f"Причины:\n{reasons}\n\n"
            f"Предупреждения:\n{warnings}\n\n"
            f"🎯 TP1: {self.tp1:,.4f}\n"
            f"🎯 TP2: {self.tp2:,.4f}\n"
            f"🎯 TP3: {self.tp3:,.4f}\n"
            f"🛑 SL: {self.sl:,.4f}\n\n"
            f"Не финансовая рекомендация. Риск контролируй сам."
        )


def _risk(score: int) -> str:
    if score >= 85:
        return "Низкий"
    if score >= 70:
        return "Средний"
    return "Повышенный"


def _adx_text(adx: float) -> str:
    if adx >= 35:
        return "сильный тренд"
    if adx >= 22:
        return "нормальный тренд"
    return "слабый тренд / флет"


def _funding_text(funding: float) -> str:
    if funding >= 0.08:
        return "лонги перегреты"
    if funding <= -0.08:
        return "шорты перегреты"
    return "нейтральный"


def _volume_text(vf: float) -> str:
    if vf >= 1.35:
        return "выше среднего"
    if vf <= 0.75:
        return "ниже среднего"
    return "средний"


def _safe_float(value, default: float = 0.0) -> float:
    try:
        v = float(value)
        if v != v:  # NaN
            return default
        return v
    except Exception:
        return default


def analyze_symbol(symbol: str) -> Signal:
    df15 = add_indicators(bybit.klines(symbol, interval="15", limit=260))
    df1h = add_indicators(bybit.klines(symbol, interval="60", limit=260))
    df4h = add_indicators(bybit.klines(symbol, interval="240", limit=260))

    last = df15.iloc[-1]
    prev = df15.iloc[-2]
    price = _safe_float(last["close"])
    atr = _safe_float(last["atr"], price * 0.01) or price * 0.01
    atr_pct = atr / price * 100 if price else 0.0
    rsi = _safe_float(last["rsi"], 50.0)
    adx = _safe_float(last["adx"], 0.0)
    funding = bybit.funding_rate(symbol)
    oi = bybit.open_interest(symbol)
    oi_change = float(oi["change_pct"])
    trend15 = trend_from_df(df15)
    trend1h = trend_from_df(df1h)
    trend4h = trend_from_df(df4h)
    volume_factor = float(last["volume"] / last["volume_ma20"]) if _safe_float(last["volume_ma20"]) else 1.0

    long_score = 0
    short_score = 0
    long_reasons: list[str] = []
    short_reasons: list[str] = []
    long_warnings: list[str] = []
    short_warnings: list[str] = []

    # Trend 15m / 1H / 4H
    if trend15 == "UP":
        long_score += 18; long_reasons.append("EMA50 выше EMA200 — тренд 15m вверх")
    elif trend15 == "DOWN":
        short_score += 18; short_reasons.append("EMA50 ниже EMA200 — тренд 15m вниз")

    if trend1h == "UP":
        long_score += 18; long_reasons.append("Тренд 1H вверх")
        short_warnings.append("1H против шорта")
    elif trend1h == "DOWN":
        short_score += 18; short_reasons.append("Тренд 1H вниз")
        long_warnings.append("1H против лонга")

    if trend4h == "UP":
        long_score += 18; long_reasons.append("Тренд 4H вверх — старший ТФ подтверждает")
        short_score -= 8; short_warnings.append("4H против шорта")
    elif trend4h == "DOWN":
        short_score += 18; short_reasons.append("Тренд 4H вниз — старший ТФ подтверждает")
        long_score -= 8; long_warnings.append("4H против лонга")

    # MACD
    macd = _safe_float(last["macd"])
    macd_sig = _safe_float(last["macd_signal"])
    prev_macd = _safe_float(prev["macd"])
    prev_sig = _safe_float(prev["macd_signal"])
    if macd > macd_sig and prev_macd <= prev_sig:
        long_score += 16; long_reasons.append("MACD дал пересечение вверх")
    elif macd > macd_sig:
        long_score += 9; long_reasons.append("MACD подтверждает рост")
    if macd < macd_sig and prev_macd >= prev_sig:
        short_score += 16; short_reasons.append("MACD дал пересечение вниз")
    elif macd < macd_sig:
        short_score += 9; short_reasons.append("MACD подтверждает снижение")

    # RSI
    if 36 <= rsi <= 58:
        long_score += 12; long_reasons.append(f"RSI {rsi:.1f} — зона для продолжения роста")
    elif rsi > 70:
        long_score -= 8; long_warnings.append("RSI перегрет для лонга")
    if 42 <= rsi <= 64:
        short_score += 12; short_reasons.append(f"RSI {rsi:.1f} — зона для продолжения снижения")
    elif rsi < 30:
        short_score -= 8; short_warnings.append("RSI перепродан для шорта")

    # ADX trend strength filter
    if adx >= 25:
        long_score += 8; short_score += 8
        long_reasons.append(f"ADX {adx:.1f} — тренд достаточно сильный")
        short_reasons.append(f"ADX {adx:.1f} — тренд достаточно сильный")
    elif adx < 18:
        long_score -= 10; short_score -= 10
        long_warnings.append("ADX низкий — возможен флет")
        short_warnings.append("ADX низкий — возможен флет")

    # Volume
    if volume_factor >= 1.35:
        long_score += 10; short_score += 10
        long_reasons.append(f"Объем выше среднего x{volume_factor:.2f}")
        short_reasons.append(f"Объем выше среднего x{volume_factor:.2f}")
    elif volume_factor <= 0.75:
        long_score -= 6; short_score -= 6
        long_warnings.append(f"Объем слабый x{volume_factor:.2f}")
        short_warnings.append(f"Объем слабый x{volume_factor:.2f}")

    # OI context
    if oi_change > 0.6:
        if trend15 == "UP":
            long_score += 12; long_reasons.append(f"OI растет {oi_change:+.2f}% вместе с ростом цены")
        elif trend15 == "DOWN":
            short_score += 12; short_reasons.append(f"OI растет {oi_change:+.2f}% вместе со снижением")
        else:
            long_score += 5; short_score += 5
    elif oi_change < -0.6:
        long_score -= 6; short_score -= 6
        long_warnings.append(f"OI падает {oi_change:+.2f}% — движение может ослабевать")
        short_warnings.append(f"OI падает {oi_change:+.2f}% — движение может ослабевать")

    # Funding context
    if funding > 0.08:
        long_score -= 10; short_score += 6
        long_warnings.append("Funding высокий — лонги могут быть перегреты")
        short_reasons.append("Funding высокий — возможен откат против лонгов")
    elif funding < -0.08:
        short_score -= 10; long_score += 6
        short_warnings.append("Funding отрицательный — шорты могут быть перегреты")
        long_reasons.append("Funding отрицательный — возможен отскок против шортов")

    # Volatility context
    if atr_pct < 0.25:
        long_score -= 5; short_score -= 5
        long_warnings.append("ATR низкий — слабая волатильность")
        short_warnings.append("ATR низкий — слабая волатильность")
    elif atr_pct > 2.5:
        long_warnings.append("ATR высокий — риск резких выносов")
        short_warnings.append("ATR высокий — риск резких выносов")

    if long_score >= short_score:
        direction: Direction = "LONG" if long_score >= 38 else "NONE"
        score = max(0, min(100, int(round(long_score))))
        reasons = long_reasons
        warnings = long_warnings
        tp1, tp2, tp3 = price + atr * 1.0, price + atr * 1.8, price + atr * 2.8
        sl = price - atr * 1.25
    else:
        direction = "SHORT" if short_score >= 38 else "NONE"
        score = max(0, min(100, int(round(short_score))))
        reasons = short_reasons
        warnings = short_warnings
        tp1, tp2, tp3 = price - atr * 1.0, price - atr * 1.8, price - atr * 2.8
        sl = price + atr * 1.25

    return Signal(symbol, direction, price, score, _risk(score), funding, oi_change, volume_factor, trend15, trend1h, trend4h, rsi, adx, atr_pct, tp1, tp2, tp3, sl, reasons[:9], warnings[:5])


def analyze_many(symbols: list[str]) -> list[Signal]:
    out: list[Signal] = []
    for s in symbols:
        try:
            out.append(analyze_symbol(s))
        except Exception as e:
            out.append(Signal(s, "NONE", 0, 0, "Ошибка", 0, 0, 0, "ERR", "ERR", "ERR", 0, 0, 0, 0, 0, 0, 0, [f"Ошибка анализа: {e}"], []))
    return sorted(out, key=lambda x: x.score, reverse=True)
