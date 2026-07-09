import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from config import config
from keyboards import main_menu, signal_buttons, settings_menu
from scheduler import setup_scheduler
from signals import analyze_symbol, format_signal

bot = Bot(token=config.bot_token)
dp = Dispatcher()

runtime = {
    "auto_enabled": config.auto_signals,
    "min_score": config.min_auto_score,
    "interval": config.signal_interval_minutes,
}

async def send_menu(target):
    text = (
        "🤖 CryptoVIPBot v2.0\n\n"
        "Выбери действие кнопками ниже.\n"
        "Бот анализирует Bybit Futures и показывает сигналы по рынку."
    )
    if isinstance(target, Message):
        await target.answer(text, reply_markup=main_menu())
    else:
        await target.message.edit_text(text, reply_markup=main_menu())

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await send_menu(message)

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    await send_menu(message)

@dp.message(Command("status"))
async def cmd_status(message: Message):
    await message.answer(
        "✅ Бот активен\n"
        f"Монеты: {', '.join(config.signal_symbols)}\n"
        f"Интервал: {config.signal_interval_minutes} минут\n"
        f"TF: 15m + 1H + 4H\n"
        f"Минимум авто-сигнала: {config.min_auto_score}/100\n"
        f"Авто режим: {'Вкл' if config.auto_signals else 'Выкл'}\n"
        f"Bybit key: {'есть' if config.bybit_api_key else 'нет'}",
        reply_markup=main_menu(),
    )

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
                await bot.send_message(chat_id, f"⚪ {symbol}: сильного сигнала нет\nСила: {sig.score if sig else 0}/100")
        except Exception as e:
            await bot.send_message(chat_id, f"⚠️ Ошибка анализа {symbol}: {e}")
    if found == 0 and only_best:
        await bot.send_message(chat_id, "⚪ Сильных сигналов сейчас нет")

@dp.message(Command("test_signal"))
async def cmd_test(message: Message):
    await message.answer("🔎 Проверяю рынок v2.0...")
    await analyze_and_send(message.chat.id)
    await message.answer("✅ Проверка завершена", reply_markup=main_menu())

@dp.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery):
    await call.answer()
    await send_menu(call)

@dp.callback_query(F.data == "check_market")
async def cb_check(call: CallbackQuery):
    await call.answer("Проверяю рынок...")
    await call.message.answer("🔎 Проверяю рынок v2.0...")
    await analyze_and_send(call.message.chat.id)
    await call.message.answer("✅ Проверка завершена", reply_markup=main_menu())

@dp.callback_query(F.data == "best_signals")
async def cb_best(call: CallbackQuery):
    await call.answer("Ищу лучшие сигналы...")
    await call.message.answer(f"🔥 Ищу сигналы от {config.min_auto_score}/100...")
    await analyze_and_send(call.message.chat.id, min_score=config.min_auto_score, only_best=True)

@dp.callback_query(F.data.startswith("symbol:"))
async def cb_symbol(call: CallbackQuery):
    symbol = call.data.split(":", 1)[1]
    await call.answer(f"Анализ {symbol}")
    await analyze_and_send(call.message.chat.id, [symbol])

@dp.callback_query(F.data.startswith("details:"))
async def cb_details(call: CallbackQuery):
    symbol = call.data.split(":", 1)[1]
    await call.answer("Обновляю подробный анализ")
    await analyze_and_send(call.message.chat.id, [symbol])

@dp.callback_query(F.data == "scan_all")
async def cb_scan_all(call: CallbackQuery):
    await call.answer()
    await call.message.answer("🚀 Сканер всех монет Bybit будет добавлен в v2.1. Сейчас доступны монеты из SIGNAL_SYMBOLS.", reply_markup=main_menu())

@dp.callback_query(F.data == "auto_mode")
async def cb_auto(call: CallbackQuery):
    await call.answer()
    await call.message.answer(
        "📡 Автоматический режим управляется через .env:\n"
        "AUTO_SIGNALS=true/false\n"
        "MIN_AUTO_SCORE=80\n\n"
        "В следующей версии сделаем сохранение настроек прямо кнопками.",
        reply_markup=main_menu(),
    )

@dp.callback_query(F.data == "settings")
async def cb_settings(call: CallbackQuery):
    await call.answer()
    await call.message.answer(
        "⚙️ Настройки CryptoVIPBot\n\n"
        f"Монеты: {', '.join(config.signal_symbols)}\n"
        f"Интервал: {runtime['interval']} мин\n"
        f"Мин. сила: {runtime['min_score']}/100\n"
        f"Авто: {'Вкл' if runtime['auto_enabled'] else 'Выкл'}",
        reply_markup=settings_menu(runtime['auto_enabled'], runtime['min_score'], runtime['interval'])
    )

@dp.callback_query(F.data == "toggle_auto")
async def cb_toggle_auto(call: CallbackQuery):
    runtime["auto_enabled"] = not runtime["auto_enabled"]
    await call.answer("Переключено")
    await call.message.edit_text(
        "⚙️ Настройки CryptoVIPBot\n\n"
        f"Авто: {'Вкл' if runtime['auto_enabled'] else 'Выкл'}\n"
        "Пока это переключение работает в текущей сессии. Постоянное сохранение добавим дальше.",
        reply_markup=settings_menu(runtime['auto_enabled'], runtime['min_score'], runtime['interval'])
    )

@dp.callback_query(F.data.startswith("score:"))
async def cb_score(call: CallbackQuery):
    delta = int(call.data.split(":", 1)[1])
    runtime["min_score"] = max(0, min(100, runtime["min_score"] + delta))
    await call.answer("Изменено")
    await call.message.edit_text(
        "⚙️ Настройки CryptoVIPBot\n\n"
        f"Мин. сила: {runtime['min_score']}/100",
        reply_markup=settings_menu(runtime['auto_enabled'], runtime['min_score'], runtime['interval'])
    )

@dp.callback_query(F.data == "help")
async def cb_help(call: CallbackQuery):
    await call.answer()
    await call.message.answer(
        "ℹ️ Помощь\n\n"
        "📊 Проверить рынок — анализ BTC/ETH.\n"
        "🔥 Лучшие сигналы — показывает только сильные сигналы.\n"
        "📈 BTC / 📉 ETH — анализ конкретной монеты.\n"
        "⚙️ Настройки — параметры бота.\n\n"
        "Команды: /start /menu /status /test_signal",
        reply_markup=main_menu(),
    )

@dp.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()

async def main():
    setup_scheduler(bot)
    print("CryptoVIPBot v2.0 started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
