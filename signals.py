import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command

from config import BOT_TOKEN, ADMIN_IDS
from database import init_db
from scheduler import start_scheduler, scan_market

logging.basicConfig(level=logging.INFO)

dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("CryptoVIPBot запущен ✅")

@dp.message(Command("id"))
async def get_id(message: types.Message):
    await message.answer(f"Ваш ID: {message.from_user.id}\nChat ID: {message.chat.id}")

@dp.message(Command("scan"))
async def manual_scan(message: types.Message, bot: Bot):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Нет доступа")
        return
    await message.answer("Запускаю ручной анализ рынка...")
    await scan_market(bot)
    await message.answer("Анализ завершен")

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не указан BOT_TOKEN в .env")
    await init_db()
    bot = Bot(BOT_TOKEN)
    await start_scheduler(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
