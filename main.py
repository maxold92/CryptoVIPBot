import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from config import config
from database import init_db
from scheduler import setup_scheduler, scan_market


dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: types.Message) -> None:
    await message.answer("CryptoVIPBot запущен ✅")


@dp.message(Command("id"))
async def get_id(message: types.Message) -> None:
    await message.answer(f"Ваш ID: {message.from_user.id}\nChat ID: {message.chat.id}")


@dp.message(Command("test"))
async def test(message: types.Message) -> None:
    if config.admin_ids and message.from_user.id not in config.admin_ids:
        return
    await message.answer("Тестовое сообщение ✅")


@dp.message(Command("scan"))
async def scan(message: types.Message) -> None:
    if config.admin_ids and message.from_user.id not in config.admin_ids:
        return
    await message.answer("Сканирую рынок...")
    await scan_market(message.bot)
    await message.answer("Сканирование завершено ✅")


async def main() -> None:
    if not config.bot_token:
        raise RuntimeError("BOT_TOKEN не заполнен в .env")

    await init_db()
    bot = Bot(token=config.bot_token)
    scheduler = setup_scheduler(bot)
    scheduler.start()

    print("CryptoVIPBot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
