"""Python parser utilities."""

import ast

from app.repository.models import RepositoryDocument


class PythonParser:
    """Parse Python repository documents."""

    def parse(
        self,
        document: RepositoryDocument,
    ) -> ast.Module:
        """Parse a repository document."""

        return ast.parse(
            document.content,
        )