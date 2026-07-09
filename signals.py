from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import config
from signals import analyze_symbol, format_signal


async def send_morning(bot):
    if config.group_chat_id:
        await bot.send_message(config.group_chat_id, config.morning_message)


async def auto_scan(bot):
    if not config.auto_signals or not config.group_chat_id:
        return
    for symbol in config.signal_symbols:
        try:
            sig = analyze_symbol(symbol)
            if sig and sig.score >= config.min_auto_score:
                await bot.send_message(config.group_chat_id, format_signal(sig))
        except Exception as e:
            print(f'auto_scan error {symbol}: {e}')


def setup_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone=config.timezone)
    scheduler.add_job(send_morning, CronTrigger(hour=9, minute=0), args=[bot])
    scheduler.add_job(auto_scan, 'interval', minutes=config.signal_interval_minutes, args=[bot])
    scheduler.start()
    return scheduler
