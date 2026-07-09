from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from config import config
from signals import analyze_symbol


async def send_morning(bot) -> None:
    if config.group_chat_id:
        await bot.send_message(config.group_chat_id, config.morning_message)


async def scan_market(bot) -> None:
    if not config.group_chat_id:
        return
    for symbol in config.signal_symbols:
        try:
            signal = analyze_symbol(symbol)
            if signal:
                await bot.send_message(config.group_chat_id, signal)
        except Exception as e:
            print(f"Signal error {symbol}: {e}")


def setup_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=config.timezone)
    scheduler.add_job(send_morning, CronTrigger(hour=9, minute=0), args=[bot], id="morning", replace_existing=True)
    scheduler.add_job(scan_market, IntervalTrigger(minutes=config.signal_interval_minutes), args=[bot], id="signals", replace_existing=True)
    return scheduler
