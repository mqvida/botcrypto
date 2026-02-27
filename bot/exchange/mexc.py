"""MEXC exchange adapter."""

from __future__ import annotations

import asyncio
from typing import Any

import ccxt.async_support as ccxt

from bot.config import ExchangeCredentials


class MexcClient:
    def __init__(self, creds: ExchangeCredentials, sandbox: bool = True) -> None:
        self.exchange = ccxt.mexc(
            {
                "apiKey": creds.api_key,
                "secret": creds.secret,
                "enableRateLimit": True,
                "options": {"defaultType": "swap"},
            }
        )
        if sandbox:
            self.exchange.set_sandbox_mode(True)

    async def fetch_ohlcv(self, symbol: str, timeframe: str = "1m", limit: int = 300) -> list[list[float]]:
        return await self._retry(lambda: self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit))

    async def fetch_order_book(self, symbol: str, limit: int = 20) -> dict[str, Any]:
        return await self._retry(lambda: self.exchange.fetch_order_book(symbol, limit=limit))

    async def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        return await self._retry(lambda: self.exchange.fetch_ticker(symbol))

    async def create_order(self, symbol: str, side: str, amount: float, order_type: str = "market") -> dict[str, Any]:
        return await self._retry(lambda: self.exchange.create_order(symbol, order_type, side, amount))

    async def close(self) -> None:
        await self.exchange.close()

    async def _retry(self, fn, retries: int = 3, delay: float = 0.7):
        for attempt in range(retries):
            try:
                return await fn()
            except Exception:
                if attempt + 1 >= retries:
                    raise
                await asyncio.sleep(delay * (attempt + 1))
