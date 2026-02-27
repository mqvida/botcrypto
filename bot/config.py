"""Configuration management for the trading bot."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class StrategyToggles:
    scalping: bool = True
    volatility_breakout: bool = True
    arbitrage: bool = True
    dynamic_grid: bool = True
    trend_following: bool = True


@dataclass(slots=True)
class RiskConfig:
    risk_per_trade: float = 0.01
    max_drawdown: float = 0.2
    max_total_exposure: float = 0.4
    trailing_stop_pct: float = 0.015
    stop_loss_atr_multiplier: float = 1.8
    take_profit_levels: List[float] = field(default_factory=lambda: [0.01, 0.02, 0.03])
    kill_switch_daily_loss: float = 0.08


@dataclass(slots=True)
class BotConfig:
    mode: str
    symbols: List[str]
    futures_enabled: bool
    leverage: int
    polling_interval: float
    base_currency: str
    strategy_toggles: StrategyToggles
    risk: RiskConfig
    exchange_fees: Dict[str, float]
    min_arbitrage_edge: float


@dataclass(slots=True)
class ExchangeCredentials:
    api_key: str
    secret: str
    passphrase: str | None = None


def _as_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def load_bot_config() -> BotConfig:
    """Load runtime configuration from environment variables."""
    mode = os.getenv("BOT_MODE", "paper")
    symbols = [s.strip().upper() for s in os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT,SOL/USDT").split(",")]
    return BotConfig(
        mode=mode,
        symbols=symbols,
        futures_enabled=_as_bool("FUTURES_ENABLED", True),
        leverage=int(os.getenv("LEVERAGE", "3")),
        polling_interval=float(os.getenv("POLLING_INTERVAL", "5")),
        base_currency=os.getenv("BASE_CURRENCY", "USDT"),
        strategy_toggles=StrategyToggles(
            scalping=_as_bool("STRATEGY_SCALPING", True),
            volatility_breakout=_as_bool("STRATEGY_BREAKOUT", True),
            arbitrage=_as_bool("STRATEGY_ARBITRAGE", True),
            dynamic_grid=_as_bool("STRATEGY_GRID", True),
            trend_following=_as_bool("STRATEGY_TREND", True),
        ),
        risk=RiskConfig(
            risk_per_trade=float(os.getenv("RISK_PER_TRADE", "0.01")),
            max_drawdown=float(os.getenv("MAX_DRAWDOWN", "0.2")),
            max_total_exposure=float(os.getenv("MAX_TOTAL_EXPOSURE", "0.4")),
            trailing_stop_pct=float(os.getenv("TRAILING_STOP_PCT", "0.015")),
            stop_loss_atr_multiplier=float(os.getenv("STOP_LOSS_ATR_MULTIPLIER", "1.8")),
            take_profit_levels=[float(x) for x in os.getenv("TP_LEVELS", "0.01,0.02,0.03").split(",")],
            kill_switch_daily_loss=float(os.getenv("KILL_SWITCH_DAILY_LOSS", "0.08")),
        ),
        exchange_fees={
            "mexc": float(os.getenv("MEXC_FEE", "0.001")),
            "okx": float(os.getenv("OKX_FEE", "0.001")),
        },
        min_arbitrage_edge=float(os.getenv("MIN_ARBITRAGE_EDGE", "0.008")),
    )


def load_exchange_credentials(prefix: str) -> ExchangeCredentials:
    """Load exchange credentials for a prefix like MEXC / OKX."""
    api_key = os.getenv(f"{prefix}_API_KEY", "")
    secret = os.getenv(f"{prefix}_API_SECRET", "")
    passphrase = os.getenv(f"{prefix}_PASSPHRASE")
    return ExchangeCredentials(api_key=api_key, secret=secret, passphrase=passphrase)
