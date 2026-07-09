from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu(is_vip: bool = False, is_admin: bool = False) -> InlineKeyboardMarkup:
    vip_text = '⭐ VIP сигналы' if is_vip else '🔒 VIP сигналы'
    rows = [
        [InlineKeyboardButton(text='📊 Анализ рынка', callback_data='check_market'), InlineKeyboardButton(text='🔥 Лучшие сигналы', callback_data='best_signals')],
        [InlineKeyboardButton(text='📈 BTC', callback_data='symbol:BTCUSDT'), InlineKeyboardButton(text='📉 ETH', callback_data='symbol:ETHUSDT')],
        [InlineKeyboardButton(text=vip_text, callback_data='vip_signals'), InlineKeyboardButton(text='💎 Купить VIP', callback_data='buy_vip')],
        [InlineKeyboardButton(text='👤 Мой VIP', callback_data='my_vip'), InlineKeyboardButton(text='ℹ️ Помощь', callback_data='help')],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text='🛠 Админ панель', callback_data='admin')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def signal_buttons(symbol: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔄 Обновить', callback_data=f'symbol:{symbol}')],
        [InlineKeyboardButton(text='🏠 Меню', callback_data='menu')],
    ])


def buy_vip_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Я оплатил', callback_data='paid_vip')],
        [InlineKeyboardButton(text='👤 Мой VIP', callback_data='my_vip'), InlineKeyboardButton(text='🏠 Меню', callback_data='menu')],
    ])


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📊 Статистика', callback_data='admin_stats')],
        [InlineKeyboardButton(text='👥 Последние пользователи', callback_data='admin_users')],
        [InlineKeyboardButton(text='➕ Выдать VIP', callback_data='admin_help_addvip')],
        [InlineKeyboardButton(text='🏠 Меню', callback_data='menu')],
    ])


def approve_vip_menu(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Выдать 30 дней', callback_data=f'approve_vip:{user_id}:30')],
        [InlineKeyboardButton(text='✅ Выдать 7 дней', callback_data=f'approve_vip:{user_id}:7')],
    ])
