import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from zoneinfo import ZoneInfo

from config import config
from signals import analyze_all

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

bot = Bot(token=config.bot_token)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=ZoneInfo(config.timezone))


def is_admin(user_id: int) -> bool:
    return not config.admin_ids or user_id in config.admin_ids


async def send_to_group(text: str):
    if config.group_chat_id:
        await bot.send_message(config.group_chat_id, text)


async def market_scan(force: bool = False):
    messages = analyze_all(force=force)
    if not messages:
        return
    for msg in messages:
        await send_to_group(msg)
        await asyncio.sleep(1)


async def morning_job():
    await send_to_group(config.morning_message)


@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    await message.answer(
        "✅ CryptoVIPBot работает\n\n"
        "Команды:\n"
        "/status — статус\n"
        "/test_signal — тестовый анализ\n"
        "/analysis — показать анализ прямо здесь"
    )


@dp.message(Command('status'))
async def cmd_status(message: types.Message):
    bybit_status = 'есть' if config.bybit_api_key and config.bybit_api_secret else 'нет'
    group_status = config.group_chat_id or 'не указан'
    await message.answer(
        f"✅ Бот активен\n"
        f"Монеты: {', '.join(config.signal_symbols)}\n"
        f"Интервал: {config.signal_interval_minutes} минут\n"
        f"Мин. сила сигнала: {config.min_signal_score}/100\n"
        f"Bybit key: {bybit_status}\n"
        f"Группа: {group_status}"
    )


@dp.message(Command('test_signal'))
async def cmd_test_signal(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer('Нет доступа')
    await message.answer('🔎 Проверяю рынок...')
    messages = analyze_all(force=True)
    if not messages:
        await message.answer('Сигналов нет')
        return
    for msg in messages:
        await message.answer(msg)
    await message.answer('✅ Проверка завершена')


@dp.message(Command('analysis'))
async def cmd_analysis(message: types.Message):
    await cmd_test_signal(message)


async def main():
    if not config.bot_token:
        raise RuntimeError('BOT_TOKEN is empty')

    scheduler.add_job(morning_job, CronTrigger(hour=9, minute=0, timezone=ZoneInfo(config.timezone)))
    scheduler.add_job(market_scan, IntervalTrigger(minutes=config.signal_interval_minutes), kwargs={'force': False})
    scheduler.start()

    logging.info('CryptoVIPBot v1.2 started')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
