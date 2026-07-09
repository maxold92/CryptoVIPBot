# CryptoVIPBot v1.3

Telegram-бот для анализа Bybit USDT-фьючерсов.

## Новое в v1.3

- Open Interest
- Funding в рейтинге сигнала
- Volume factor
- Подтверждение тренда 15m + 1H
- Рейтинг сигнала /100
- Автоматическая отправка только сильных сигналов

## Команды

- `/start`
- `/status`
- `/test_signal`
- `/analysis`

## Запуск

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env
nano .env
python3 main.py
```
