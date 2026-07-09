from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot
from config import config
from signals import analyze_symbol, format_signal


async def send_to_group(bot: Bot, text: str):
    if not config.group_chat_id:
        print('GROUP_CHAT_ID is empty, message skipped')
        return
    await bot.send_message(config.group_chat_id, text)


async def morning_job(bot: Bot):
    await send_to_group(bot, config.morning_message)


async def signal_job(bot: Bot):
    for symbol in config.signal_symbols:
        try:
            signal = analyze_symbol(symbol)
            if signal:
                await send_to_group(bot, format_signal(signal))
                print(f'Signal sent: {symbol} {signal["direction"]}')
            else:
                print(f'No signal: {symbol}')
        except Exception as exc:
            print(f'Error analyzing {symbol}: {exc}')


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=config.timezone)
    scheduler.add_job(morning_job, CronTrigger(hour=9, minute=0, timezone=config.timezone), args=[bot])
    scheduler.add_job(signal_job, IntervalTrigger(minutes=config.signal_interval_minutes), args=[bot], next_run_time=None)
    scheduler.start()
    return scheduler
