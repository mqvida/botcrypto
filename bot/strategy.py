"""Strategy engine and signal generation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from bot.config import BotConfig
from bot.indicators import enrich_indicators


@dataclass(slots=True)
class TradeSignal:
    strategy: str
    symbol: str
    side: str
    confidence: float
    reason: str


class StrategyEngine:
    def __init__(self, config: BotConfig) -> None:
        self.config = config

    def generate_signals(self, symbol: str, candles: pd.DataFrame, order_book: dict, cross_spread: float | None = None) -> list[TradeSignal]:
        data = enrich_indicators(candles)
        last = data.iloc[-1]
        prev = data.iloc[-2]
        signals: list[TradeSignal] = []

        if self.config.strategy_toggles.scalping:
            signal = self._scalping_signal(symbol, last, prev, order_book)
            if signal:
                signals.append(signal)

        if self.config.strategy_toggles.volatility_breakout:
            signal = self._breakout_signal(symbol, last)
            if signal:
                signals.append(signal)

        if self.config.strategy_toggles.dynamic_grid:
            signal = self._dynamic_grid_signal(symbol, data)
            if signal:
                signals.append(signal)

        if self.config.strategy_toggles.trend_following:
            signal = self._trend_signal(symbol, last)
            if signal:
                signals.append(signal)

        if self.config.strategy_toggles.arbitrage and cross_spread is not None:
            signal = self._arbitrage_signal(symbol, cross_spread)
            if signal:
                signals.append(signal)

        return signals

    def _scalping_signal(self, symbol: str, last: pd.Series, prev: pd.Series, order_book: dict) -> TradeSignal | None:
        bids = np.array([b[1] for b in order_book.get("bids", [])[:10]], dtype=float)
        asks = np.array([a[1] for a in order_book.get("asks", [])[:10]], dtype=float)
        imbalance = (bids.sum() - asks.sum()) / max((bids.sum() + asks.sum()), 1e-9)

        ema_cross_up = prev["ema_fast"] <= prev["ema_slow"] and last["ema_fast"] > last["ema_slow"]
        ema_cross_down = prev["ema_fast"] >= prev["ema_slow"] and last["ema_fast"] < last["ema_slow"]

        if last["rsi"] < 35 and ema_cross_up and last["volume_spike"] and imbalance > 0.15:
            return TradeSignal("scalping", symbol, "buy", 0.82, "RSI oversold + EMA bull cross + volume spike + book imbalance")
        if last["rsi"] > 68 and ema_cross_down and last["volume_spike"] and imbalance < -0.15:
            return TradeSignal("scalping", symbol, "sell", 0.79, "RSI overbought + EMA bear cross + volume spike + book imbalance")
        return None

    def _breakout_signal(self, symbol: str, last: pd.Series) -> TradeSignal | None:
        if last["close"] > last["bb_upper"] and last["atr"] / max(last["close"], 1e-9) > 0.007:
            return TradeSignal("volatility_breakout", symbol, "buy", 0.76, "Breakout above upper Bollinger with high ATR")
        if last["close"] < last["bb_lower"] and last["atr"] / max(last["close"], 1e-9) > 0.007:
            return TradeSignal("volatility_breakout", symbol, "sell", 0.76, "Breakout below lower Bollinger with high ATR")
        return None

    def _dynamic_grid_signal(self, symbol: str, data: pd.DataFrame) -> TradeSignal | None:
        window = data.tail(60)
        lower, upper = window["close"].quantile(0.2), window["close"].quantile(0.8)
        last_price = window["close"].iloc[-1]
        if last_price <= lower:
            return TradeSignal("dynamic_grid", symbol, "buy", 0.65, "Price reached dynamic lower grid")
        if last_price >= upper:
            return TradeSignal("dynamic_grid", symbol, "sell", 0.65, "Price reached dynamic upper grid")
        return None

    def _trend_signal(self, symbol: str, last: pd.Series) -> TradeSignal | None:
        if last["macd"] > last["macd_signal"] and last["adx"] > 25:
            return TradeSignal("trend_following", symbol, "buy", 0.72, "MACD bullish with strong ADX")
        if last["macd"] < last["macd_signal"] and last["adx"] > 25:
            return TradeSignal("trend_following", symbol, "sell", 0.72, "MACD bearish with strong ADX")
        return None

    def _arbitrage_signal(self, symbol: str, cross_spread: float) -> TradeSignal | None:
        fee_drag = self.config.exchange_fees["mexc"] + self.config.exchange_fees["okx"]
        net_edge = cross_spread - fee_drag
        if net_edge > self.config.min_arbitrage_edge:
            return TradeSignal("arbitrage", symbol, "buy", 0.88, f"Cross-exchange edge={net_edge:.4%}")
        return None
