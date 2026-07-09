from __future__ import annotations

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import config
from signals import analyze_many

scheduler = AsyncIOScheduler(timezone=config.timezone)
_last_sent: dict[str, str] = {}


def _chat_id() -> str | int | None:
    if not config.group_chat_id or config.group_chat_id == "PASTE_GROUP_ID_HERE":
        return None
    try:
        return int(config.group_chat_id)
    except ValueError:
        return config.group_chat_id


async def send_morning(bot: Bot):
    chat_id = _chat_id()
    if chat_id:
        await bot.send_message(chat_id, config.morning_message)


async def scan_market(bot: Bot):
    if not config.auto_signals:
        return
    chat_id = _chat_id()
    if not chat_id:
        return
    signals = analyze_many(config.signal_symbols)
    for sig in signals:
        if sig.direction == "NONE" or sig.score < config.min_signal_score:
            continue
        key = f"{sig.symbol}:{sig.direction}"
        # антиспам: не повторяем тот же сигнал подряд
        current = f"{sig.score}:{round(sig.price, 4)}"
        if _last_sent.get(key) == current:
            continue
        _last_sent[key] = current
        await bot.send_message(chat_id, sig.format())


def setup_scheduler(bot: Bot):
    scheduler.add_job(send_morning, CronTrigger(hour=9, minute=0, timezone=config.timezone), args=[bot], id="morning", replace_existing=True)
    scheduler.add_job(scan_market, "interval", minutes=config.signal_interval_minutes, args=[bot], id="scan_market", replace_existing=True)
    scheduler.start()
