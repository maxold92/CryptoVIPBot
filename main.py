from __future__ import annotations

import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from config import config
from scheduler import setup_scheduler, signal_job


dp = Dispatcher()


def _is_admin(user_id: int) -> bool:
    return not config.admin_ids or user_id in config.admin_ids


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer('✅ CryptoVIPBot работает.\nКоманды: /status, /test_signal, /chatid')


@dp.message(Command('status'))
async def status(message: types.Message):
    await message.answer(
        '✅ Бот активен\n'
        f'Монеты: {", ".join(config.signal_symbols)}\n'
        f'Интервал: {config.signal_interval_minutes} минут\n'
        f'TF: {config.signal_timeframe}m\n'
        f'Bybit key: {"есть" if config.bybit_api_key else "нет"}'
    )


@dp.message(Command('chatid'))
async def chatid(message: types.Message):
    await message.answer(f'Chat ID: {message.chat.id}')


@dp.message(Command('test_signal'))
async def test_signal(message: types.Message, bot: Bot):
    if not _is_admin(message.from_user.id):
        await message.answer('⛔ Нет доступа')
        return
    await message.answer('🔎 Проверяю рынок...')
    await signal_job(bot)
    await message.answer('✅ Проверка завершена')


async def main():
    if not config.bot_token:
        raise RuntimeError('BOT_TOKEN is empty')
    bot = Bot(token=config.bot_token)
    setup_scheduler(bot)
    print('CryptoVIPBot started')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
