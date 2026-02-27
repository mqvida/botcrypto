"""Simple professional-style backtesting toolkit."""

from __future__ import annotations

import math
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from bot.indicators import enrich_indicators


@dataclass(slots=True)
class BacktestResult:
    roi: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    profit_factor: float


class Backtester:
    def __init__(self, initial_balance: float = 10_000.0) -> None:
        self.initial_balance = initial_balance

    def run(self, candles: pd.DataFrame) -> tuple[BacktestResult, pd.Series]:
        data = enrich_indicators(candles).dropna().reset_index(drop=True)
        balance = self.initial_balance
        equity_curve = []
        pnls = []

        for i in range(1, len(data)):
            row = data.iloc[i]
            prev = data.iloc[i - 1]
            ret = (row["close"] - prev["close"]) / prev["close"]

            signal = 0
            if row["macd"] > row["macd_signal"] and row["adx"] > 20:
                signal = 1
            elif row["macd"] < row["macd_signal"] and row["adx"] > 20:
                signal = -1

            pnl = balance * 0.02 * signal * ret
            balance += pnl
            pnls.append(pnl)
            equity_curve.append(balance)

        equity = pd.Series(equity_curve)
        returns = equity.pct_change().dropna()
        sharpe = float(np.sqrt(252) * returns.mean() / returns.std()) if not returns.empty and returns.std() > 0 else 0.0
        drawdown = (equity / equity.cummax() - 1).min() if not equity.empty else 0
        wins = [x for x in pnls if x > 0]
        losses = [x for x in pnls if x < 0]

        result = BacktestResult(
            roi=(balance / self.initial_balance) - 1,
            sharpe=sharpe,
            max_drawdown=abs(float(drawdown)),
            win_rate=(len(wins) / len(pnls)) if pnls else 0.0,
            profit_factor=(sum(wins) / abs(sum(losses))) if losses else math.inf,
        )
        return result, equity

    @staticmethod
    def plot_equity_curve(equity: pd.Series, out_path: str = "equity_curve.png") -> None:
        plt.figure(figsize=(10, 4))
        plt.plot(equity.values)
        plt.title("Equity Curve")
        plt.xlabel("Trades")
        plt.ylabel("Equity")
        plt.tight_layout()
        plt.savefig(out_path)
