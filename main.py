from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from config import config
from database import upsert_user, set_vip, is_vip
from signals import analyze_symbol

bot = Bot(token=config.bot_token, parse_mode='HTML')
dp = Dispatcher()


def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids


@dp.message(Command('start'))
async def start(message: Message):
    await upsert_user(message.from_user.id, message.from_user.username)
    await message.answer('Привет! Я CryptoVIPBot. Команды: /analyze BTCUSDT, /vip, /help')


@dp.message(Command('help'))
async def help_cmd(message: Message):
    await message.answer(
        'Команды:\n'
        '/analyze BTCUSDT — анализ монеты\n'
        '/vip — проверить VIP доступ\n'
        '/addvip USER_ID — выдать VIP, только админ\n'
        '/delvip USER_ID — убрать VIP, только админ\n'
        '/send TEXT — отправить текст в VIP группу, только админ'
    )


@dp.message(Command('vip'))
async def vip_cmd(message: Message):
    vip = await is_vip(message.from_user.id)
    await message.answer('✅ VIP активен' if vip else '❌ VIP не активен')


@dp.message(Command('addvip'))
async def add_vip(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer('Нет доступа')
    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer('Пример: /addvip 123456789')
    await set_vip(int(parts[1]), True)
    await message.answer('VIP выдан')


@dp.message(Command('delvip'))
async def del_vip(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer('Нет доступа')
    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer('Пример: /delvip 123456789')
    await set_vip(int(parts[1]), False)
    await message.answer('VIP отключен')


@dp.message(Command('send'))
async def send_group(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer('Нет доступа')
    text = message.text.replace('/send', '', 1).strip()
    if not text:
        return await message.answer('Напиши текст после /send')
    await bot.send_message(config.vip_group_id, text)
    await message.answer('Отправлено в группу')


@dp.message(Command('analyze'))
async def analyze_cmd(message: Message):
    parts = message.text.split()
    symbol = parts[1].upper() if len(parts) > 1 else 'BTCUSDT'
    await message.answer(f'Анализирую {symbol}...')
    try:
        signal = analyze_symbol(symbol)
        await message.answer(signal.format())
    except Exception as e:
        await message.answer(f'Ошибка анализа: {e}')
