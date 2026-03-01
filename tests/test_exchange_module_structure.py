"""Regression tests for exchange adapter module structure.

These tests prevent accidental module-level execution bugs such as
`NameError: name 'ccxt' is not defined` caused by malformed files.
"""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


class ExchangeModuleStructureTests(unittest.TestCase):
    def _load_tree(self, rel_path: str) -> ast.Module:
        src = Path(rel_path).read_text(encoding="utf-8")
        return ast.parse(src, filename=rel_path)

    def _assert_has_ccxt_import(self, tree: ast.Module) -> None:
        has_import = any(
            isinstance(node, ast.Import) and any(alias.name == "ccxt.async_support" for alias in node.names)
            for node in tree.body
        )
        self.assertTrue(has_import, "expected 'import ccxt.async_support as ccxt' at module level")

    def _assert_no_module_level_self_assignment(self, tree: ast.Module) -> None:
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                        self.fail("module-level assignment to self.<attr> found")

    def test_okx_adapter_structure(self) -> None:
        tree = self._load_tree("bot/exchange/okx.py")
        self._assert_has_ccxt_import(tree)
        self._assert_no_module_level_self_assignment(tree)

    def test_mexc_adapter_structure(self) -> None:
        tree = self._load_tree("bot/exchange/mexc.py")
        self._assert_has_ccxt_import(tree)
        self._assert_no_module_level_self_assignment(tree)


if __name__ == "__main__":
    unittest.main()
