# CryptoVIPBot v1.4

Обновление v1.4:

- добавлен тренд 4H;
- добавлен ADX для силы тренда;
- добавлен ATR % для оценки волатильности;
- улучшена логика Open Interest;
- улучшена интерпретация Funding;
- улучшено отображение объёма;
- добавлены предупреждения по рискам;
- TP/SL рассчитываются от ATR.

## Обновление на сервере

```bash
cd /root/CryptoVIPBot
git pull
source venv/bin/activate
pip install -r requirements.txt
systemctl restart cryptovipbot
systemctl status cryptovipbot
```

Проверка в Telegram:

```text
/status
/test_signal
```
