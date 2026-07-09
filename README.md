# CryptoVIPBot v1.2

Telegram-бот для Bybit: статус, тестовый анализ, автоматическая проверка рынка, утреннее сообщение.

## Команды

- `/start`
- `/status`
- `/test_signal`
- `/analysis`

## Обновление на сервере

```bash
cd /root/CryptoVIPBot
git pull
source venv/bin/activate
pip install -r requirements.txt
systemctl restart cryptovipbot
systemctl status cryptovipbot
```
