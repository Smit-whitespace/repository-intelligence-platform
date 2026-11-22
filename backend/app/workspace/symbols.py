"""Python symbol extraction.

Definitions come from Python's own ``ast`` module, so they are exact for
Python. Other languages are not covered yet; results say which languages
were searched, so a client never mistakes "not found" for "does not
exist".
"""

import ast
from dataclasses import dataclass
from pathlib import Path

from app.workspace.models import (
    Symbol,
    SymbolKind,
)

PYTHON_SUFFIXES = frozenset(
    {
        ".py",
        ".pyi",
    },
)


@dataclass(frozen=True)
class _CacheKey:
    path: Path
    modified_ns: int
    size: int


class PythonSymbolExtractor:
    """Extract class, function and method definitions from Python files.

    Parsed results are cached per file and reused until the file's
    modification time or size changes, so repeated lookups on a large
    repository only re-parse edited files.
    """

    def __init__(
        self,
    ) -> None:
        self._cache: dict[Path, tuple[_CacheKey, list[Symbol] | None]] = {}

    def extract(
        self,
        absolute_path: Path,
        relative_path: str,
        source: str,
    ) -> list[Symbol] | None:
        """Return the file's symbols, or ``None`` if it does not parse."""

        stat = absolute_path.stat()

        key = _CacheKey(
            path=absolute_path,
            modified_ns=stat.st_mtime_ns,
            size=stat.st_size,
        )

        cached = self._cache.get(
            absolute_path,
        )

        if cached is not None and cached[0] == key:
            return cached[1]

        symbols: list[Symbol] | None

        try:
            module = ast.parse(
                source,
                filename=relative_path,
            )

        except (SyntaxError, ValueError):
            symbols = None

        else:
            symbols = []

            self._visit(
                nodes=module.body,
                prefix="",
                inside_class=False,
                relative_path=relative_path,
                symbols=symbols,
            )

        self._cache[absolute_path] = (
            key,
            symbols,
        )

        return symbols

    def _visit(
        self,
        nodes: list[ast.stmt],
        prefix: str,
        inside_class: bool,
        relative_path: str,
        symbols: list[Symbol],
    ) -> None:
        """Collect module-level and class-level definitions.

        Functions nested inside functions are skipped: they cannot be
        referenced from outside, so they are rarely what a lookup wants.
        """

        for node in nodes:
            if isinstance(
                node,
                ast.ClassDef,
            ):
                kind = SymbolKind.CLASS

            elif isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                kind = (
                    SymbolKind.METHOD
                    if inside_class
                    else SymbolKind.FUNCTION
                )

            else:
                continue

            qualified_name = f"{prefix}{node.name}"

            start_line = min(
                [
                    node.lineno,
                    *(
                        decorator.lineno
                        for decorator in node.decorator_list
                    ),
                ],
            )

            symbols.append(
                Symbol(
                    name=node.name,
                    qualified_name=qualified_name,
                    kind=kind,
                    is_async=isinstance(
                        node,
                        ast.AsyncFunctionDef,
                    ),
                    path=relative_path,
                    start_line=start_line,
                    end_line=node.end_lineno or node.lineno,
                ),
            )

            if kind is SymbolKind.CLASS:
                self._visit(
                    nodes=node.body,
                    prefix=f"{qualified_name}.",
                    inside_class=True,
                    relative_path=relative_path,
                    symbols=symbols,
                )
