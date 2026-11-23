"""Repository ignore rules.

Two layers decide what scanning, indexing and the workspace tools skip:

1. A fixed list of directory names RIP always skips (VCS metadata, RIP's
   own storage, virtual environments, caches, ``node_modules``).
2. The repository's own git ignore rules: every ``.gitignore`` (each
   relative to its directory, deeper files taking precedence) and
   ``.git/info/exclude``, matched with git's semantics by ``pathspec``.

Ignored paths are skipped while walking. An ignored directory is never
entered, matching git, where a file inside an excluded directory cannot
be re-included. Reading a specific path is not affected: these rules
decide what is listed, searched and indexed, not what is accessible.
"""

from pathlib import Path, PurePosixPath

from pathspec import GitIgnoreSpec

from app.core.storage.locations import is_link

_INTERNAL_EXCLUDED_NAMES = {
    ".git",
    ".repository-intelligence-platform",
    ".local_openclaw",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "node_modules",
}

NOT_INDEXED_FILE_NAMES = frozenset(
    {
        "package-lock.json",
        "npm-shrinkwrap.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "bun.lockb",
        "uv.lock",
        "poetry.lock",
        "pdm.lock",
        "Pipfile.lock",
        "Cargo.lock",
        "Gemfile.lock",
        "composer.lock",
        "go.sum",
    },
)
"""Generated dependency lock files: committed, so git does not ignore
them, but machine-written and huge. They stay listable and searchable
("which version of X?" is a fair question) and are only left out of the
semantic index, where they would be costly noise."""


def is_indexable_file_name(
    name: str,
) -> bool:
    """Return whether a file belongs in the semantic index by name."""

    return name not in NOT_INDEXED_FILE_NAMES


MAX_IGNORE_FILE_BYTES = 1_000_000

MAX_WILDCARDS_PER_SEGMENT = 3
"""Patterns are compiled to backtracking regular expressions; matching
time grows exponentially with the number of ``*`` in one path segment
(``*a*a*a*a*a*a*a*a*b`` takes over a minute per file name). Three keep
every check in milliseconds and cover real-world patterns."""


def _is_safe_pattern(
    line: str,
) -> bool:
    """Skip patterns too complex to match quickly (as git skips bad lines)."""

    return all(
        segment.replace("**", "").count("*") <= MAX_WILDCARDS_PER_SEGMENT
        for segment in line.split("/")
    )


_GITIGNORE_FILE_NAME = ".gitignore"

_INFO_EXCLUDE_PATH = Path(".git/info/exclude")


def should_ignore(
    path: Path,
) -> bool:
    """Return whether a path has a name RIP always skips."""

    return path.name in _INTERNAL_EXCLUDED_NAMES


class RepositoryIgnoreRules:
    """Ignore rules for one repository, including its git ignore files.

    Create one per walk: ``.gitignore`` files are read lazily and cached
    for the instance's lifetime, so a later walk sees edited rules.
    """

    def __init__(
        self,
        root: Path,
    ) -> None:
        self._root = root.resolve()

        self._specs: dict[PurePosixPath, GitIgnoreSpec | None] = {}

        self._info_exclude = self._load(
            self._root / _INFO_EXCLUDE_PATH,
        )

    def is_ignored(
        self,
        path: Path,
        is_directory: bool,
    ) -> bool:
        """Return whether a path under the root is ignored."""

        if should_ignore(
            path,
        ):
            return True

        try:
            relative = PurePosixPath(
                path.relative_to(
                    self._root,
                ).as_posix(),
            )

        except ValueError:
            return False

        # Deeper .gitignore files take precedence over shallower ones,
        # and every .gitignore over .git/info/exclude, as in git. The
        # first file with a matching pattern (ignore or "!" re-include)
        # decides.
        for base in self._ancestors(
            relative,
        ):
            decision = self._check(
                self._spec_for(
                    base,
                ),
                relative.relative_to(
                    base,
                ),
                is_directory,
            )

            if decision is not None:
                return decision

        decision = self._check(
            self._info_exclude,
            relative,
            is_directory,
        )

        return bool(
            decision,
        )

    @staticmethod
    def _ancestors(
        relative: PurePosixPath,
    ) -> list[PurePosixPath]:
        """Directories that may hold a .gitignore for a path, deepest first."""

        return list(
            relative.parents,
        )

    def _spec_for(
        self,
        directory: PurePosixPath,
    ) -> GitIgnoreSpec | None:
        if directory not in self._specs:
            self._specs[directory] = self._load(
                self._root
                / directory
                / _GITIGNORE_FILE_NAME,
            )

        return self._specs[directory]

    @staticmethod
    def _load(
        path: Path,
    ) -> GitIgnoreSpec | None:
        # Ignore files are repository content, so a hostile repository
        # controls them: never follow a link out of the project, and
        # refuse absurdly large files.
        try:
            if is_link(path) or path.stat().st_size > MAX_IGNORE_FILE_BYTES:
                return None

            # utf-8-sig: editors on Windows often save a byte order mark,
            # which would otherwise corrupt the first pattern.
            lines = [
                line
                for line in path.read_text(
                    encoding="utf-8-sig",
                    errors="replace",
                ).splitlines()
                if _is_safe_pattern(
                    line,
                )
            ]

        except OSError:
            return None

        try:
            return GitIgnoreSpec.from_lines(
                lines,
            )

        except ValueError:
            # One malformed pattern must not break every scan: keep the
            # patterns that parse on their own, as git skips bad lines.
            valid_lines: list[str] = []

            for line in lines:
                try:
                    GitIgnoreSpec.from_lines(
                        [
                            line,
                        ],
                    )

                except ValueError:
                    continue

                valid_lines.append(
                    line,
                )

            return GitIgnoreSpec.from_lines(
                valid_lines,
            )

    @staticmethod
    def _check(
        spec: GitIgnoreSpec | None,
        relative: PurePosixPath,
        is_directory: bool,
    ) -> bool | None:
        """True (ignored), False (re-included) or None (no pattern matched)."""

        if spec is None:
            return None

        # Directory patterns such as "dist/" only match a trailing slash.
        candidate = relative.as_posix() + ("/" if is_directory else "")

        return spec.check_file(
            candidate,
        ).include
