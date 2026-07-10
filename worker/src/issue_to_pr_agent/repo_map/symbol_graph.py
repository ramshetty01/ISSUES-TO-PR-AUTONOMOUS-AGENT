"""Index symbols into a lookup graph (name -> definitions)."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .tree_sitter_index import Symbol, index_symbols


class SymbolGraph:
    def __init__(self, symbols: list[Symbol]) -> None:
        self._by_name: dict[str, list[Symbol]] = defaultdict(list)
        for s in symbols:
            self._by_name[s.name].append(s)

    def lookup(self, name: str) -> list[Symbol]:
        return list(self._by_name.get(name, []))

    def names(self) -> list[str]:
        return sorted(self._by_name)

    def __len__(self) -> int:
        return sum(len(v) for v in self._by_name.values())


def build_symbol_graph(repo_dir: Path) -> SymbolGraph:
    return SymbolGraph(index_symbols(repo_dir))
