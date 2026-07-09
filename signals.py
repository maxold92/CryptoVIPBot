# CryptoVIPBot

Telegram Crypto VIP Bot с Bybit анализом, сигналами и утренним сообщением в группу в 09:00.

## Возможности

- Telegram-бот на aiogram 3
- Подключение к Bybit через pybit
- Команда `/analyze BTCUSDT`
- Автоматический скан рынка каждые 5 минут
- Отправка сигналов в VIP-группу
- Утреннее сообщение: `☀️ Доброе утро трейдеры)`
- SQLite база данных
- VIP-доступ и простая админ-панель

## Установка

```bash
git clone https://github.com/maxold92/CryptoVIPBot.git
cd CryptoVIPBot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

На Linux/Mac:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## Настройка `.env`

```env
BOT_TOKEN=токен_из_BotFather
VIP_GROUP_ID=-100xxxxxxxxxx
ADMIN_IDS=твой_telegram_id
BYBIT_API_KEY=
BYBIT_API_SECRET=
BYBIT_TESTNET=false
TIMEZONE=Europe/Kiev
```

Для публичного анализа Bybit ключи можно оставить пустыми. Для приватных функций ключи понадобятся позже.

## Команды

- `/start`
- `/help`
- `/vip`
- `/analyze BTCUSDT`
- `/addvip USER_ID`
- `/delvip USER_ID`
- `/send текст`

⚠️ Бот не дает финансовых гарантий. Используй риск-менеджмент.
