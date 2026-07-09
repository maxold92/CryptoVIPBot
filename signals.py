import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from bybit_client import bybit
from config import config


def _fmt_price(x: float) -> str:
    if x >= 1000:
        return f"{x:,.2f}".replace(',', ' ')
    if x >= 1:
        return f"{x:.4f}"
    return f"{x:.6f}"


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['ema50'] = EMAIndicator(df['close'], window=50).ema_indicator()
    df['ema200'] = EMAIndicator(df['close'], window=200).ema_indicator()
    df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
    macd = MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['atr'] = AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
    df['vol_ma20'] = df['volume'].rolling(20).mean()
    return df


def analyze_symbol(symbol: str, interval: str = '15') -> dict:
    df = add_indicators(bybit.klines(symbol, interval=interval, limit=250))
    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = float(last['close'])
    atr = float(last['atr']) if pd.notna(last['atr']) and last['atr'] > 0 else price * 0.01
    funding = bybit.funding_rate(symbol)

    long_score = 0
    short_score = 0
    long_reasons = []
    short_reasons = []

    if last['ema50'] > last['ema200']:
        long_score += 25
        long_reasons.append('EMA50 выше EMA200 — тренд вверх')
    else:
        short_score += 25
        short_reasons.append('EMA50 ниже EMA200 — тренд вниз')

    if 35 <= last['rsi'] <= 62:
        long_score += 15
        long_reasons.append(f'RSI {last["rsi"]:.1f} — зона для продолжения роста')
    if 38 <= last['rsi'] <= 65:
        short_score += 8
    if last['rsi'] > 68:
        short_score += 18
        short_reasons.append(f'RSI {last["rsi"]:.1f} — перегрев')
    if last['rsi'] < 32:
        long_score += 18
        long_reasons.append(f'RSI {last["rsi"]:.1f} — перепроданность')

    macd_up = prev['macd'] <= prev['macd_signal'] and last['macd'] > last['macd_signal']
    macd_down = prev['macd'] >= prev['macd_signal'] and last['macd'] < last['macd_signal']
    if macd_up or last['macd'] > last['macd_signal']:
        long_score += 20
        long_reasons.append('MACD подтверждает рост')
    if macd_down or last['macd'] < last['macd_signal']:
        short_score += 20
        short_reasons.append('MACD подтверждает снижение')

    if last['volume'] > last['vol_ma20'] * 1.2:
        long_score += 12
        short_score += 12
        long_reasons.append('Объём выше среднего')
        short_reasons.append('Объём выше среднего')

    # Простая оценка импульса последних 3 свечей
    last3 = df.tail(3)
    if last3['close'].iloc[-1] > last3['close'].iloc[0]:
        long_score += 10
        long_reasons.append('Последние свечи дают импульс вверх')
    else:
        short_score += 10
        short_reasons.append('Последние свечи дают давление вниз')

    direction = 'LONG' if long_score >= short_score else 'SHORT'
    score = max(long_score, short_score)
    reasons = long_reasons if direction == 'LONG' else short_reasons

    if direction == 'LONG':
        sl = price - atr * 1.2
        tp1 = price + atr * 1.0
        tp2 = price + atr * 1.8
        tp3 = price + atr * 2.7
        emoji = '🟢'
    else:
        sl = price + atr * 1.2
        tp1 = price - atr * 1.0
        tp2 = price - atr * 1.8
        tp3 = price - atr * 2.7
        emoji = '🔴'

    return {
        'symbol': symbol,
        'direction': direction,
        'emoji': emoji,
        'score': int(min(score, 100)),
        'price': price,
        'rsi': float(last['rsi']),
        'atr': atr,
        'funding': funding,
        'tp1': tp1,
        'tp2': tp2,
        'tp3': tp3,
        'sl': sl,
        'reasons': reasons[:6],
        'has_signal': score >= config.min_signal_score,
    }


def format_signal(result: dict, force: bool = False) -> str:
    if not result['has_signal'] and not force:
        return ''
    funding_text = 'нет данных' if result['funding'] is None else f"{result['funding']:.4f}%"
    reasons = '\n'.join([f"✅ {r}" for r in result['reasons']]) or '—'
    quality = 'Высокий' if result['score'] >= 85 else 'Средний' if result['score'] >= 70 else 'Низкий'

    return (
        f"🚨 CryptoVIPBot v1.2\n\n"
        f"{result['emoji']} {result['direction']}\n"
        f"Монета: {result['symbol']}\n"
        f"Цена: {_fmt_price(result['price'])}\n\n"
        f"⭐ Сила сигнала: {result['score']}/100\n"
        f"⚠️ Риск: {quality}\n"
        f"💰 Funding: {funding_text}\n\n"
        f"Причины:\n{reasons}\n\n"
        f"🎯 TP1: {_fmt_price(result['tp1'])}\n"
        f"🎯 TP2: {_fmt_price(result['tp2'])}\n"
        f"🎯 TP3: {_fmt_price(result['tp3'])}\n"
        f"🛑 SL: {_fmt_price(result['sl'])}\n\n"
        f"Не финансовая рекомендация. Риск контролируй сам."
    )


def analyze_all(force: bool = False) -> list[str]:
    messages = []
    for symbol in config.signal_symbols:
        try:
            result = analyze_symbol(symbol, interval='15')
            msg = format_signal(result, force=force)
            if msg:
                messages.append(msg)
        except Exception as e:
            messages.append(f"⚠️ Ошибка анализа {symbol}: {e}")
    return messages
