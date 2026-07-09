import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery

from config import config
from database import db
from keyboards import main_menu, signal_buttons, buy_vip_menu, admin_menu, approve_vip_menu
from scheduler import setup_scheduler
from signals import analyze_symbol, format_signal

bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids


async def menu_for(message_or_call):
    user = message_or_call.from_user if isinstance(message_or_call, Message) else message_or_call.from_user
    await db.upsert_user(user)
    vip = await db.is_vip(user.id)
    text = (
        '🤖 <b>CryptoVIPBot v2.1.1</b>\n\n'
        f"VIP: {'✅ активен' if vip else '❌ нет доступа'}\n"
        'Выбери действие кнопками ниже.'
    )
    markup = main_menu(vip, is_admin(user.id))
    if isinstance(message_or_call, Message):
        await message_or_call.answer(text, reply_markup=markup)
    else:
        await message_or_call.message.answer(text, reply_markup=markup)


async def analyze_and_send(chat_id, symbols=None, min_score=0, only_best=False):
    symbols = symbols or config.signal_symbols
    found = 0
    for symbol in symbols:
        try:
            sig = analyze_symbol(symbol)
            if sig and sig.score >= min_score:
                found += 1
                await bot.send_message(chat_id, format_signal(sig), reply_markup=signal_buttons(symbol))
            elif not only_best:
                await bot.send_message(chat_id, f'⚪ {symbol}: сильного сигнала нет\nСила: {sig.score if sig else 0}/100')
        except Exception as e:
            await bot.send_message(chat_id, f'⚠️ Ошибка анализа {symbol}: {e}')
    if found == 0 and only_best:
        await bot.send_message(chat_id, '⚪ Сильных сигналов сейчас нет')


@dp.message(Command('start'))
async def cmd_start(message: Message):
    await menu_for(message)


@dp.message(Command('menu'))
async def cmd_menu(message: Message):
    await menu_for(message)


@dp.message(Command('myid'))
async def cmd_myid(message: Message):
    await db.upsert_user(message.from_user)
    await message.answer(f'Твой Telegram ID: <code>{message.from_user.id}</code>')


@dp.message(Command('vip'))
async def cmd_vip(message: Message):
    await db.upsert_user(message.from_user)
    vip = await db.is_vip(message.from_user.id)
    until = await db.vip_until(message.from_user.id)
    await message.answer(f"VIP: {'✅ активен' if vip else '❌ нет'}\nVIP до: {until or '-'}", reply_markup=buy_vip_menu() if not vip else main_menu(True, is_admin(message.from_user.id)))


@dp.message(Command('status'))
async def cmd_status(message: Message):
    await db.upsert_user(message.from_user)
    vip = await db.is_vip(message.from_user.id)
    until = await db.vip_until(message.from_user.id)
    await message.answer(
        '✅ Бот активен\n'
        f"VIP: {'активен' if vip else 'нет'}\n"
        f"VIP до: {until or '-'}\n"
        f"Монеты: {', '.join(config.signal_symbols)}\n"
        f"Авто режим: {'Вкл' if config.auto_signals else 'Выкл'}\n"
        f"Bybit key: {'есть' if config.bybit_api_key else 'нет'}",
        reply_markup=main_menu(vip, is_admin(message.from_user.id)),
    )


@dp.message(Command('addvip'))
async def cmd_addvip(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer('⛔ Нет доступа')
    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer('Формат: /addvip USER_ID DAYS\nПример: /addvip 123456789 30')
    user_id = int(parts[1])
    days = int(parts[2]) if len(parts) >= 3 else 30
    until = await db.add_vip(user_id, days, note=f'admin:{message.from_user.id}')
    await message.answer(f'✅ VIP выдан пользователю {user_id} до {until}')
    try:
        await bot.send_message(user_id, f'✅ VIP доступ активирован на {days} дней.')
    except Exception:
        pass


@dp.message(Command('delvip'))
async def cmd_delvip(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer('⛔ Нет доступа')
    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer('Формат: /delvip USER_ID')
    await db.remove_vip(int(parts[1]))
    await message.answer('✅ VIP отключен')


@dp.callback_query(F.data == 'menu')
async def cb_menu(call: CallbackQuery):
    await call.answer()
    await menu_for(call)


@dp.callback_query(F.data == 'check_market')
async def cb_check(call: CallbackQuery):
    await call.answer('Проверяю рынок...')
    await analyze_and_send(call.message.chat.id)


@dp.callback_query(F.data == 'best_signals')
async def cb_best(call: CallbackQuery):
    await call.answer('Ищу лучшие сигналы...')
    await analyze_and_send(call.message.chat.id, min_score=config.min_auto_score, only_best=True)


@dp.callback_query(F.data.startswith('symbol:'))
async def cb_symbol(call: CallbackQuery):
    symbol = call.data.split(':', 1)[1]
    await call.answer(f'Анализ {symbol}')
    await analyze_and_send(call.message.chat.id, [symbol])


@dp.callback_query(F.data == 'vip_signals')
async def cb_vip_signals(call: CallbackQuery):
    await db.upsert_user(call.from_user)
    if not await db.is_vip(call.from_user.id):
        await call.answer('Нужен VIP доступ', show_alert=True)
        return await call.message.answer('🔒 Это раздел только для VIP. Нажми «Купить VIP».', reply_markup=buy_vip_menu())
    await call.answer('VIP анализ')
    await analyze_and_send(call.message.chat.id, min_score=config.min_auto_score, only_best=True)


@dp.callback_query(F.data == 'buy_vip')
async def cb_buy_vip(call: CallbackQuery):
    await db.upsert_user(call.from_user)
    await call.answer()
    await call.message.answer(
        f'💎 <b>Покупка VIP</b>\n\n{config.vip_price_text}\n\n{config.payment_details}',
        reply_markup=buy_vip_menu(),
    )


@dp.callback_query(F.data == 'paid_vip')
async def cb_paid_vip(call: CallbackQuery):
    await db.upsert_user(call.from_user)
    await call.answer('Заявка отправлена')
    await db.create_payment_request(call.from_user.id, 30)
    await call.message.answer('✅ Заявка отправлена админу. После проверки тебе включат VIP.')
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                f'💰 Заявка на VIP\nUser ID: <code>{call.from_user.id}</code>\nUsername: @{call.from_user.username}\n\nМожно выдать командой: /addvip {call.from_user.id} 30',
                reply_markup=approve_vip_menu(call.from_user.id)
            )
        except Exception:
            pass


@dp.callback_query(F.data == 'my_vip')
async def cb_my_vip(call: CallbackQuery):
    await db.upsert_user(call.from_user)
    vip = await db.is_vip(call.from_user.id)
    until = await db.vip_until(call.from_user.id)
    await call.answer()
    await call.message.answer(f"👤 Мой VIP\n\nСтатус: {'✅ активен' if vip else '❌ нет доступа'}\nVIP до: {until or '-'}\nID: <code>{call.from_user.id}</code>", reply_markup=buy_vip_menu() if not vip else main_menu(True, is_admin(call.from_user.id)))


@dp.callback_query(F.data == 'settings')
async def cb_settings(call: CallbackQuery):
    await call.answer()
    vip = await db.is_vip(call.from_user.id)
    await call.message.answer(
        f"⚙️ Настройки\n\nМонеты: {', '.join(config.signal_symbols)}\nМин. сила: {config.min_auto_score}/100\nАвто: {'Вкл' if config.auto_signals else 'Выкл'}\nVIP: {'активен' if vip else 'нет'}"
    )


@dp.callback_query(F.data == 'help')
async def cb_help(call: CallbackQuery):
    await call.answer()
    await call.message.answer('Команды: /start /menu /status /vip /myid /addvip /delvip')


@dp.callback_query(F.data == 'admin')
async def cb_admin(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Нет доступа', show_alert=True)
        return
    await call.answer()
    await call.message.answer('🛠 Админ панель', reply_markup=admin_menu())


@dp.callback_query(F.data == 'admin_stats')
async def cb_admin_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Нет доступа', show_alert=True)
        return
    stats = await db.stats()
    await call.answer()
    await call.message.answer(f"📊 Статистика\n\nПользователей: {stats['users']}\nАктивных VIP: {stats['active_vip']}\nЗаявок на оплату: {stats['pending']}")




@dp.callback_query(F.data == 'admin_users')
async def cb_admin_users(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Нет доступа', show_alert=True)
        return
    users = await db.list_users(10)
    lines = ['👥 Последние пользователи']
    for u in users:
        name = u.get('username') or u.get('first_name') or '-'
        lines.append(f"{u['user_id']} | {name} | VIP: {u.get('vip_until') or '-'}")
    await call.answer()
    await call.message.answer('\n'.join(lines))


@dp.callback_query(F.data.startswith('approve_vip:'))
async def cb_approve_vip(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Нет доступа', show_alert=True)
        return
    _, user_id, days = call.data.split(':')
    until = await db.add_vip(int(user_id), int(days), note=f'button_admin:{call.from_user.id}')
    await call.answer('VIP выдан')
    await call.message.answer(f'✅ VIP выдан пользователю {user_id} до {until}')
    try:
        await bot.send_message(int(user_id), f'✅ VIP доступ активирован на {days} дней.')
    except Exception:
        pass

@dp.callback_query(F.data == 'admin_help_addvip')
async def cb_admin_help_addvip(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Нет доступа', show_alert=True)
        return
    await call.answer()
    await call.message.answer('Команды:\n/addvip USER_ID 30\n/delvip USER_ID')


async def main():
    if not config.bot_token:
        raise RuntimeError('BOT_TOKEN пустой. Заполни .env')
    await db.init()
    setup_scheduler(bot)
    print('CryptoVIPBot v2.1.1 started')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
