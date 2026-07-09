from dataclasses import dataclass, field
from bybit_client import bybit
from indicators import enrich


@dataclass
class Signal:
    symbol: str
    direction: str
    score: int
    entry: float
    tp1: float
    tp2: float
    tp3: float
    sl: float
    risk: str
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    indicators: dict = field(default_factory=dict)


def _trend(row) -> str:
    if row['ema50'] > row['ema200']:
        return 'UP'
    if row['ema50'] < row['ema200']:
        return 'DOWN'
    return 'FLAT'


def analyze_symbol(symbol: str) -> Signal:
    df15 = enrich(bybit.get_kline(symbol, '15'))
    df1h = enrich(bybit.get_kline(symbol, '60'))
    df4h = enrich(bybit.get_kline(symbol, '240'))
    r15, r1h, r4h = df15.iloc[-1], df1h.iloc[-1], df4h.iloc[-1]

    price = float(r15['close'])
    atr = float(r15['atr'])
    trend15, trend1h, trend4h = _trend(r15), _trend(r1h), _trend(r4h)
    funding = bybit.get_funding_rate(symbol)
    oi_change = bybit.get_open_interest_change(symbol)
    volume_factor = float(r15['volume'] / r15['volume_sma20']) if r15['volume_sma20'] else 1.0

    long_score = short_score = 0
    reasons, warnings = [], []

    if trend4h == 'UP': long_score += 20; reasons.append('4H тренд вверх')
    if trend4h == 'DOWN': short_score += 20; reasons.append('4H тренд вниз')
    if trend1h == 'UP': long_score += 15; reasons.append('1H тренд вверх')
    if trend1h == 'DOWN': short_score += 15; reasons.append('1H тренд вниз')
    if trend15 == 'UP': long_score += 15; reasons.append('EMA50 выше EMA200 на 15m')
    if trend15 == 'DOWN': short_score += 15; reasons.append('EMA50 ниже EMA200 на 15m')

    if r15['macd'] > r15['macd_signal']: long_score += 10; reasons.append('MACD за LONG')
    if r15['macd'] < r15['macd_signal']: short_score += 10; reasons.append('MACD за SHORT')
    if 35 <= r15['rsi'] <= 60: long_score += 10; reasons.append(f"RSI {r15['rsi']:.1f} норм для LONG")
    if 40 <= r15['rsi'] <= 65: short_score += 10; reasons.append(f"RSI {r15['rsi']:.1f} норм для SHORT")

    if r15['adx'] >= 20:
        long_score += 5; short_score += 5; reasons.append(f"ADX {r15['adx']:.1f}: тренд есть")
    else:
        warnings.append(f"ADX {r15['adx']:.1f}: возможен флэт")

    if volume_factor >= 1.2:
        long_score += 5; short_score += 5; reasons.append(f'Объем x{volume_factor:.2f}')
    if oi_change > 0.5:
        if trend15 == 'UP': long_score += 15
        if trend15 == 'DOWN': short_score += 15
        reasons.append(f'Open Interest +{oi_change:.2f}%')
    if funding > 0.15:
        short_score += 5; warnings.append(f'Funding {funding:.3f}%: LONG перегрет')
    elif funding < -0.05:
        long_score += 5; warnings.append(f'Funding {funding:.3f}%: SHORT перегрет')
    else:
        reasons.append(f'Funding {funding:.3f}%: нейтральный')

    direction = 'LONG' if long_score >= short_score else 'SHORT'
    score = int(min(max(long_score, short_score), 100))
    risk = 'Низкий' if score >= 85 else 'Средний' if score >= 70 else 'Высокий'

    if direction == 'LONG':
        tp1, tp2, tp3, sl = price + atr*1.0, price + atr*1.8, price + atr*2.6, price - atr*1.2
    else:
        tp1, tp2, tp3, sl = price - atr*1.0, price - atr*1.8, price - atr*2.6, price + atr*1.2

    return Signal(symbol, direction, score, price, tp1, tp2, tp3, sl, risk, reasons[:8], warnings[:5], {
        'trend15': trend15, 'trend1h': trend1h, 'trend4h': trend4h,
        'rsi': float(r15['rsi']), 'adx': float(r15['adx']), 'atr': atr,
        'funding': funding, 'oi_change': oi_change, 'volume_factor': volume_factor,
    })


def format_signal(sig: Signal) -> str:
    icon = '🟢' if sig.direction == 'LONG' else '🔴'
    reasons = '\n'.join(f'• {r}' for r in sig.reasons) or '• Нет причин'
    warnings = ('\n\n⚠️ Риски:\n' + '\n'.join(f'• {w}' for w in sig.warnings)) if sig.warnings else ''
    return (
        f'{icon} <b>{sig.symbol} {sig.direction}</b>\n\n'
        f'Сила: <b>{sig.score}/100</b>\n'
        f'Риск: <b>{sig.risk}</b>\n\n'
        f'Вход: <code>{sig.entry:.6f}</code>\n'
        f'TP1: <code>{sig.tp1:.6f}</code>\n'
        f'TP2: <code>{sig.tp2:.6f}</code>\n'
        f'TP3: <code>{sig.tp3:.6f}</code>\n'
        f'SL: <code>{sig.sl:.6f}</code>\n\n'
        f'Причины:\n{reasons}'
        f'{warnings}'
    )
