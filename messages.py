scan_interval_seconds: 300
minimum_auto_score: 85
symbols:
  - BTCUSDT
  - ETHUSDT
timeframes:
  entry: "15"
  confirm: "60"
  macro: "240"
weights:
  trend_4h: 20
  trend_1h: 15
  ema: 15
  macd: 10
  rsi: 10
  adx: 10
  volume: 10
  open_interest: 15
  funding: 5
risk:
  atr_tp1: 1.0
  atr_tp2: 1.8
  atr_tp3: 2.6
  atr_sl: 1.2
