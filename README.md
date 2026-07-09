# CryptoVIPBot

Telegram-бот для криптовалютных сигналов с подключением к Bybit.

## Установка на сервере

```bash
git clone https://github.com/maxold92/CryptoVIPBot.git
cd CryptoVIPBot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python3 main.py
```

## Команды Telegram

- `/start` — проверка запуска
- `/id` — узнать свой ID и ID группы
- `/test` — тестовое сообщение
- `/scan` — ручной скан рынка

## Важно

Файл `.env` не загружай на GitHub. Там хранятся токены и ключи.
