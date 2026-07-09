from modules.indicators import ema, rsi, macd

class MarketAnalyzer:
    def analyze(self, symbol: str, candles: list[dict]):
        if len(candles) < 60:
            return None

        closes = [c["close"] for c in candles]
        volumes = [c["volume"] for c in candles]
        price = closes[-1]
        ema20 = ema(closes[-60:], 20)
        ema50 = ema(closes[-80:], 50)
        rsi14 = rsi(closes, 14)
        macd_value = macd(closes)
        avg_volume = sum(volumes[-30:-1]) / 29
        volume_now = volumes[-1]

        long_score = 0
        short_score = 0
        reasons = []

        if ema20 and ema50 and ema20 > ema50:
            long_score += 25
            reasons.append("EMA20 выше EMA50 — тренд вверх")
        elif ema20 and ema50:
            short_score += 25
            reasons.append("EMA20 ниже EMA50 — тренд вниз")

        if rsi14 is not None:
            if rsi14 < 35:
                long_score += 20
                reasons.append(f"RSI {rsi14:.1f} — зона перепроданности")
            elif rsi14 > 65:
                short_score += 20
                reasons.append(f"RSI {rsi14:.1f} — зона перекупленности")

        if macd_value is not None:
            if macd_value > 0:
                long_score += 15
                reasons.append("MACD выше нуля")
            else:
                short_score += 15
                reasons.append("MACD ниже нуля")

        if volume_now > avg_volume * 1.5:
            long_score += 10
            short_score += 10
            reasons.append("Объем выше среднего — есть импульс")

        side = "LONG" if long_score >= short_score else "SHORT"
        score = max(long_score, short_score)

        if score < 45:
            return None

        if side == "LONG":
            tp1 = price * 1.01
            tp2 = price * 1.02
            sl = price * 0.99
        else:
            tp1 = price * 0.99
            tp2 = price * 0.98
            sl = price * 1.01

        return {
            "symbol": symbol,
            "side": side,
            "score": min(score, 95),
            "entry": price,
            "tp1": tp1,
            "tp2": tp2,
            "sl": sl,
            "reasons": reasons,
            "rsi": rsi14,
            "ema20": ema20,
            "ema50": ema50,
        }
