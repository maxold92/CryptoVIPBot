import yaml
from pathlib import Path
from analysis.indicators import enrich
from analysis.models import Signal
from bybit_api.client import BybitClient

class AnalysisEngine:
    def __init__(self):
        self.bybit = BybitClient()
        self.settings = yaml.safe_load(Path("config/settings.yaml").read_text(encoding="utf-8"))

    def _trend(self, row) -> str:
        if row["ema50"] > row["ema200"]:
            return "UP"
        if row["ema50"] < row["ema200"]:
            return "DOWN"
        return "FLAT"

    def analyze_symbol(self, symbol: str) -> Signal:
        tf = self.settings["timeframes"]
        df15 = enrich(self.bybit.get_kline(symbol, tf["entry"]))
        df1h = enrich(self.bybit.get_kline(symbol, tf["confirm"]))
        df4h = enrich(self.bybit.get_kline(symbol, tf["macro"]))
        r15, r1h, r4h = df15.iloc[-1], df1h.iloc[-1], df4h.iloc[-1]
        price = float(r15["close"])
        atr = float(r15["atr"])
        trend15, trend1h, trend4h = self._trend(r15), self._trend(r1h), self._trend(r4h)
        funding = self.bybit.get_funding_rate(symbol)
        oi_change = self.bybit.get_open_interest_change(symbol)
        volume_factor = float(r15["volume"] / r15["volume_sma20"]) if r15["volume_sma20"] else 1.0

        long_score = short_score = 0
        reasons, warnings = [], []
        w = self.settings["weights"]

        if trend4h == "UP": long_score += w["trend_4h"]; reasons.append("4H trend UP")
        if trend4h == "DOWN": short_score += w["trend_4h"]; reasons.append("4H trend DOWN")
        if trend1h == "UP": long_score += w["trend_1h"]; reasons.append("1H trend UP")
        if trend1h == "DOWN": short_score += w["trend_1h"]; reasons.append("1H trend DOWN")
        if trend15 == "UP": long_score += w["ema"]; reasons.append("EMA50 > EMA200 на 15m")
        if trend15 == "DOWN": short_score += w["ema"]; reasons.append("EMA50 < EMA200 на 15m")
        if r15["macd"] > r15["macd_signal"]: long_score += w["macd"]; reasons.append("MACD LONG")
        if r15["macd"] < r15["macd_signal"]: short_score += w["macd"]; reasons.append("MACD SHORT")
        if 35 <= r15["rsi"] <= 60: long_score += w["rsi"]; reasons.append(f"RSI {r15['rsi']:.1f} good for LONG")
        if 40 <= r15["rsi"] <= 65: short_score += w["rsi"]; reasons.append(f"RSI {r15['rsi']:.1f} good for SHORT")
        if r15["adx"] >= 20:
            long_score += w["adx"] // 2; short_score += w["adx"] // 2; reasons.append(f"ADX {r15['adx']:.1f}: тренд есть")
        else:
            warnings.append(f"ADX {r15['adx']:.1f}: рынок может быть во флэте")
        if volume_factor >= 1.2:
            long_score += w["volume"] // 2; short_score += w["volume"] // 2; reasons.append(f"Volume x{volume_factor:.2f}: выше среднего")
        if oi_change > 0.5:
            if trend15 == "UP": long_score += w["open_interest"]
            if trend15 == "DOWN": short_score += w["open_interest"]
            reasons.append(f"Open Interest +{oi_change:.2f}%")
        if funding > 0.15:
            short_score += w["funding"]; warnings.append(f"Funding {funding:.3f}%: LONG перегрет")
        elif funding < -0.05:
            long_score += w["funding"]; warnings.append(f"Funding {funding:.3f}%: SHORT перегрет")
        else:
            reasons.append(f"Funding {funding:.3f}%: нейтральный")

        direction = "LONG" if long_score >= short_score else "SHORT"
        score = int(min(max(long_score, short_score), 100))
        risk = "Низкий" if score >= 85 else "Средний" if score >= 70 else "Высокий"
        rr = self.settings["risk"]
        if direction == "LONG":
            tp1, tp2, tp3, sl = price + atr*rr["atr_tp1"], price + atr*rr["atr_tp2"], price + atr*rr["atr_tp3"], price - atr*rr["atr_sl"]
        else:
            tp1, tp2, tp3, sl = price - atr*rr["atr_tp1"], price - atr*rr["atr_tp2"], price - atr*rr["atr_tp3"], price + atr*rr["atr_sl"]
        return Signal(symbol, direction, score, price, tp1, tp2, tp3, sl, risk, reasons[:8], warnings[:5], {
            "trend15": trend15, "trend1h": trend1h, "trend4h": trend4h, "rsi": float(r15["rsi"]),
            "adx": float(r15["adx"]), "atr": atr, "funding": funding, "oi_change": oi_change, "volume_factor": volume_factor
        })
