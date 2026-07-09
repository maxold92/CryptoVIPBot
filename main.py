from __future__ import annotations

import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import config
from scheduler import setup_scheduler
from signals import analyze_many

bot = Bot(token=config.bot_token)
dp = Dispatcher()


def is_admin(user_id: int) -> bool:
    return not config.admin_ids or user_id in config.admin_ids


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("✅ CryptoVIPBot v1.4 запущен\nКоманды: /status, /test_signal, /analysis")


@dp.message(Command("status"))
async def status(message: types.Message):
    await message.answer(
        "✅ Бот активен\n"
        f"Монеты: {', '.join(config.signal_symbols)}\n"
        f"Интервал: {config.signal_interval_minutes} минут\n"
        f"Мин. сила сигнала: {config.min_signal_score}/100\n"
        f"Авто-сигналы: {'включены' if config.auto_signals else 'выключены'}\n"
        f"Bybit key: {'есть' if config.bybit_api_key else 'нет'}"
    )


@dp.message(Command("test_signal", "analysis"))
async def test_signal(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа")
        return
    await message.answer("🔎 Проверяю рынок v1.4...")
    signals = analyze_many(config.signal_symbols)
    for sig in signals:
        await message.answer(sig.format())
    await message.answer("✅ Проверка завершена")


async def main():
    setup_scheduler(bot)
    print("CryptoVIPBot v1.4 started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
