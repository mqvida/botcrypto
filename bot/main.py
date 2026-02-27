"""Main runtime loop for the trading bot."""

from __future__ import annotations

import asyncio
from datetime import datetime

import pandas as pd
import websockets

from bot.config import load_bot_config, load_exchange_credentials
from bot.database import Database, MetricRecord, OrderRecord, TradeRecord
from bot.exchange.mexc import MexcClient
from bot.exchange.okx import OkxClient
from bot.logger import setup_logger
from bot.risk_manager import RiskManager
from bot.strategy import StrategyEngine


class TradingBot:
    def __init__(self) -> None:
        self.config = load_bot_config()
        self.logger = setup_logger()
        self.db = Database()
        self.risk = RiskManager(self.config.risk)
        self.strategy_engine = StrategyEngine(self.config)
        self.mexc = MexcClient(load_exchange_credentials("MEXC"), sandbox=self.config.mode != "live")
        self.okx = OkxClient(load_exchange_credentials("OKX"), sandbox=self.config.mode != "live")
        self.open_positions: dict[str, dict] = {}

    async def stream_market_data(self, ws_url: str) -> None:
        """Optional websocket heartbeat/stream for low-latency market updates."""
        while True:
            try:
                async with websockets.connect(ws_url, ping_interval=20, ping_timeout=20) as ws:
                    await ws.send('{"op":"ping"}')
                    await ws.recv()
            except Exception as exc:
                self.logger.warning(f"Websocket stream reconnecting: {exc}")
                await asyncio.sleep(2)

    async def run(self) -> None:
        while True:
            try:
                await self._iteration()
                if self.risk.check_kill_switch():
                    self.logger.error("Kill switch triggered: drawdown/daily loss threshold reached.")
                    break
                await asyncio.sleep(self.config.polling_interval)
            except KeyboardInterrupt:
                break
            except Exception as exc:
                self.logger.exception(f"Loop failure: {exc}")
                await asyncio.sleep(2)

        await self.mexc.close()
        await self.okx.close()

    async def _iteration(self) -> None:
        for symbol in self.config.symbols:
            mexc_ticker, okx_ticker = await asyncio.gather(self.mexc.fetch_ticker(symbol), self.okx.fetch_ticker(symbol))
            cross_spread = abs(mexc_ticker["last"] - okx_ticker["last"]) / ((mexc_ticker["last"] + okx_ticker["last"]) / 2)

            candles_raw = await self.mexc.fetch_ohlcv(symbol, timeframe="1m", limit=300)
            order_book = await self.mexc.fetch_order_book(symbol)
            candles = pd.DataFrame(candles_raw, columns=["timestamp", "open", "high", "low", "close", "volume"])

            signals = self.strategy_engine.generate_signals(symbol, candles, order_book, cross_spread=cross_spread)
            for signal in signals:
                await self._execute_signal(signal.symbol, signal.side, signal.strategy, candles.iloc[-1]["close"], candles.iloc[-1]["atr"] if "atr" in candles.columns else 0.0)

        self._print_terminal_panel()

    async def _execute_signal(self, symbol: str, side: str, strategy: str, price: float, atr: float) -> None:
        stop, take_profit, trailing = self.risk.apply_dynamic_stops(side, price, max(atr, price * 0.005))
        stop_distance = abs(price - stop)
        qty = self.risk.position_size(price, stop_distance)
        if qty <= 0:
            return

        exchange = self.mexc
        order = await exchange.create_order(symbol, side, qty)
        self.open_positions[symbol] = {
            "symbol": symbol,
            "side": side,
            "size": qty,
            "entry_price": price,
            "stop": stop,
            "tp": take_profit,
            "trailing": trailing,
        }

        with self.db.session() as session:
            session.add(OrderRecord(exchange="mexc", symbol=symbol, side=side, quantity=qty, price=price, status=order.get("status", "open")))
            session.commit()

        self.logger.info(
            f"Executed {strategy} {side} {symbol} qty={qty:.5f} @ {price:.3f}",
            extra={"symbol": symbol, "strategy": strategy, "event": "order_execution"},
        )

    def _print_terminal_panel(self) -> None:
        roi = (self.risk.equity / self.risk.initial_equity) - 1
        print("\n" + "=" * 70)
        print(f"[{datetime.utcnow().isoformat()}] BOT PANEL")
        print(f"Saldo: {self.risk.equity:,.2f} | Lucro diário: {self.risk.daily_pnl:,.2f} | ROI acumulado: {roi:.2%}")
        print(f"Operações abertas: {len(self.open_positions)} | Drawdown: {self.risk.current_drawdown:.2%}")
        for pos in self.open_positions.values():
            print(
                f" - {pos['symbol']} {pos['side']} size={pos['size']:.4f} "
                f"entry={pos['entry_price']:.3f} stop={pos['stop']:.3f} tp={pos['tp']:.3f}"
            )
        print("=" * 70)

        with self.db.session() as session:
            session.add(MetricRecord(name="equity", value=self.risk.equity))
            session.add(MetricRecord(name="daily_pnl", value=self.risk.daily_pnl))
            session.commit()


def main() -> None:
    bot = TradingBot()
    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
