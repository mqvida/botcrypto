"""Indicator calculations used by trading strategies."""

from __future__ import annotations

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import ADXIndicator, EMAIndicator, MACD
from ta.volatility import AverageTrueRange, BollingerBands


def enrich_indicators(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["ema_fast"] = EMAIndicator(close=data["close"], window=9).ema_indicator()
    data["ema_slow"] = EMAIndicator(close=data["close"], window=21).ema_indicator()
    data["rsi"] = RSIIndicator(close=data["close"], window=14).rsi()

    macd = MACD(close=data["close"])
    data["macd"] = macd.macd()
    data["macd_signal"] = macd.macd_signal()

    data["adx"] = ADXIndicator(high=data["high"], low=data["low"], close=data["close"], window=14).adx()
    data["atr"] = AverageTrueRange(high=data["high"], low=data["low"], close=data["close"], window=14).average_true_range()

    bb = BollingerBands(close=data["close"], window=20, window_dev=2)
    data["bb_upper"] = bb.bollinger_hband()
    data["bb_lower"] = bb.bollinger_lband()
    data["bb_mid"] = bb.bollinger_mavg()

    data["vol_mean"] = data["volume"].rolling(20).mean()
    data["volume_spike"] = data["volume"] > (data["vol_mean"] * 1.8)
    return data
