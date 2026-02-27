"""Risk management primitives."""

from __future__ import annotations

from dataclasses import dataclass

from bot.config import RiskConfig


@dataclass(slots=True)
class Position:
    symbol: str
    side: str
    size: float
    entry_price: float
    stop_loss: float
    take_profit: float
    trailing_stop: float


class RiskManager:
    def __init__(self, config: RiskConfig, initial_equity: float = 10_000.0) -> None:
        self.config = config
        self.initial_equity = initial_equity
        self.equity = initial_equity
        self.high_watermark = initial_equity
        self.current_drawdown = 0.0
        self.daily_pnl = 0.0

    def update_pnl(self, pnl: float) -> None:
        self.equity += pnl
        self.daily_pnl += pnl
        self.high_watermark = max(self.high_watermark, self.equity)
        self.current_drawdown = 1 - (self.equity / self.high_watermark)

    def check_kill_switch(self) -> bool:
        drawdown_hit = self.current_drawdown >= self.config.max_drawdown
        daily_loss_hit = (-self.daily_pnl / self.initial_equity) >= self.config.kill_switch_daily_loss
        return drawdown_hit or daily_loss_hit

    def position_size(self, price: float, stop_distance: float) -> float:
        risk_capital = self.equity * self.config.risk_per_trade
        if stop_distance <= 0:
            return 0.0
        return max(risk_capital / stop_distance / price, 0.0)

    def apply_dynamic_stops(self, side: str, entry_price: float, atr: float) -> tuple[float, float, float]:
        stop_offset = atr * self.config.stop_loss_atr_multiplier
        if side == "buy":
            stop = entry_price - stop_offset
            take_profit = entry_price * (1 + self.config.take_profit_levels[0])
            trailing = entry_price * (1 - self.config.trailing_stop_pct)
        else:
            stop = entry_price + stop_offset
            take_profit = entry_price * (1 - self.config.take_profit_levels[0])
            trailing = entry_price * (1 + self.config.trailing_stop_pct)
        return stop, take_profit, trailing
