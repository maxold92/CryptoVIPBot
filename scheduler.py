import asyncio
from config import config
from database import init_db
from bot import bot, dp
from scheduler import setup_scheduler

async def main():
    config.validate()
    await init_db()
    setup_scheduler()
    print('CryptoVIPBot запущен')
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
