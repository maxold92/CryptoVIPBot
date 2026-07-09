# CryptoVIPBot v2.1.0

Sprint 1: VIP-доступ, база пользователей, админ-команды, Bybit-анализ, авто-сообщение в 09:00.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python main.py
```

## Команды

- `/start` — меню
- `/menu` — меню
- `/status` — статус
- `/addvip USER_ID 30` — выдать VIP, только админ
- `/delvip USER_ID` — убрать VIP, только админ

## Что добавить в .env

- `BOT_TOKEN`
- `GROUP_CHAT_ID`
- `ADMIN_IDS`
- `PAYMENT_DETAILS`

Bybit API ключи можно оставить пустыми для публичных данных.
