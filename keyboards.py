from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Проверить рынок", callback_data="check_market"), InlineKeyboardButton(text="🔥 Лучшие сигналы", callback_data="best_signals")],
        [InlineKeyboardButton(text="📈 BTC", callback_data="symbol:BTCUSDT"), InlineKeyboardButton(text="📉 ETH", callback_data="symbol:ETHUSDT")],
        [InlineKeyboardButton(text="🚀 Все монеты Bybit", callback_data="scan_all"), InlineKeyboardButton(text="📡 Авто режим", callback_data="auto_mode")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"), InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")],
    ])


def signal_buttons(symbol: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"symbol:{symbol}"), InlineKeyboardButton(text="📊 Подробнее", callback_data=f"details:{symbol}")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])


def settings_menu(auto_enabled: bool, min_score: int, interval: int) -> InlineKeyboardMarkup:
    auto_text = "🟢 Авто: Вкл" if auto_enabled else "🔴 Авто: Выкл"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=auto_text, callback_data="toggle_auto")],
        [InlineKeyboardButton(text=f"⭐ Мин. сила: {min_score}", callback_data="noop")],
        [InlineKeyboardButton(text="-5", callback_data="score:-5"), InlineKeyboardButton(text="+5", callback_data="score:+5")],
        [InlineKeyboardButton(text=f"⏱ Интервал: {interval} мин", callback_data="noop")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])
