"""Lightweight runtime smoke checks without importing heavy deps."""

from __future__ import annotations

from pathlib import Path
import unittest


class RuntimeSmokeTests(unittest.TestCase):
    def test_main_imports_okx_client(self) -> None:
        content = Path("bot/main.py").read_text(encoding="utf-8")
        self.assertIn("from bot.exchange.okx import OkxClient", content)

    def test_readme_has_troubleshooting_for_ccxt_nameerror(self) -> None:
        content = Path("README.md").read_text(encoding="utf-8")
        self.assertIn("NameError: name 'ccxt' is not defined", content)


if __name__ == "__main__":
    unittest.main()
