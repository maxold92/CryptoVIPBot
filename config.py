def format_signal(signal: dict) -> str:
    stars = "⭐" * max(1, min(5, signal["score"] // 20))
    reasons = "\n".join([f"✅ {r}" for r in signal["reasons"]])
    return (
        f"🚨 VIP СИГНАЛ {signal['side']} {stars}\n\n"
        f"Монета: {signal['symbol']}\n"
        f"Вероятность: {signal['score']}%\n\n"
        f"Вход: {signal['entry']:.6f}\n"
        f"TP1: {signal['tp1']:.6f}\n"
        f"TP2: {signal['tp2']:.6f}\n"
        f"SL: {signal['sl']:.6f}\n\n"
        f"Причины:\n{reasons}\n\n"
        f"⚠️ Не финансовая рекомендация. Соблюдай риск-менеджмент."
    )
