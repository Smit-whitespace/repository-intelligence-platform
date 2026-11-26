"""Score chat answers against the evaluation questions.

The search questions already say which files, symbols and concepts a
question is about. A good answer cites those files, names those symbols
and explains those concepts, and invents nothing. Scoring is deterministic
so two prompt versions can be compared on the same footing. Keyword
coverage only stands in for "a useful explanation", so read the answers
too: every run can write them to a JSON report.
"""

import os
import re
import time
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from app.chat.models import ChatRequest
from app.chat.service import ChatService
from eval.models import RetrievalTestCase

# Folders that are never part of the repository's own code or docs.
_SKIPPED_DIRECTORIES = {
    ".git",
    ".local_openclaw",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
}

_TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

_PATH = re.compile(
    r"[\w./\\-]+\.(?:" + "|".join(s[1:] for s in sorted(_TEXT_SUFFIXES)) + r")\b",
)

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")

_INLINE_CODE = re.compile(r"`([^`\n]+)`")

_FENCED_CODE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)

_WORD = re.compile(r"[a-z0-9]+")

REFUSAL = "couldn't find enough evidence"


@dataclass(frozen=True)
class Repository:
    """What exists in the repository, to tell real names from invented ones."""

    files: frozenset[str]
    """Every text file, as a POSIX path relative to the root."""

    identifiers: frozenset[str]
    """Every identifier-like word in those files."""

    @property
    def basenames(self) -> frozenset[str]:
        return frozenset(path.rsplit("/", 1)[-1] for path in self.files)


def load_repository(
    root: Path,
) -> Repository:
    """Read the file list and identifiers of a repository on disk."""

    files: set[str] = set()
    identifiers: set[str] = set()

    for directory, subdirectories, names in os.walk(root):
        subdirectories[:] = [
            name for name in subdirectories if name not in _SKIPPED_DIRECTORIES
        ]

        for name in names:
            path = Path(directory, name)

            if path.suffix not in _TEXT_SUFFIXES:
                continue

            files.add(path.relative_to(root).as_posix())

            try:
                text = path.read_text(encoding="utf-8", errors="ignore")

            except OSError:
                continue

            identifiers.update(_IDENTIFIER.findall(text))

    return Repository(
        files=frozenset(files),
        identifiers=frozenset(identifiers),
    )


def _cited(
    answer: str,
    path: str,
) -> bool:
    """A file counts as cited by its full path or by its file name."""

    return path in answer or path.rsplit("/", 1)[-1] in answer


def _stem(
    word: str,
) -> str:
    # Short enough that "storage" meets "stores" and "streaming" meets
    # "stream", long enough that most unrelated words do not collide.
    return word[: 4 if len(word) <= 7 else 6]


def _explains(
    answer_stems: set[str],
    concept: str,
) -> bool:
    """A concept counts as covered when every word of it appears, loosely."""

    words = [w for w in _WORD.findall(concept.lower()) if len(w) >= 3]

    return bool(words) and all(_stem(w) in answer_stems for w in words)


def _share(
    hits: int,
    total: int,
) -> float | None:
    return hits / total if total else None


def invented_paths(
    answer: str,
    repository: Repository,
) -> list[str]:
    """File paths the answer mentions that are not in the repository."""

    invented: list[str] = []

    for match in _PATH.findall(answer):
        path = match.replace("\\", "/").strip("./")

        if "/" in path:
            known = any(
                file == path or file.endswith("/" + path)
                for file in repository.files
            )
        else:
            known = path in repository.basenames

        if not known and path not in invented:
            invented.append(path)

    return invented


def invented_identifiers(
    answer: str,
    repository: Repository,
) -> list[str]:
    """Names in the answer's code spans that appear nowhere in the repository."""

    code = _INLINE_CODE.findall(answer) + _FENCED_CODE.findall(answer)

    invented: list[str] = []

    for span in code:
        # Paths are checked by invented_paths; their parts are not names.
        span = _PATH.sub(" ", span)

        for name in _IDENTIFIER.findall(span):
            if name not in repository.identifiers and name not in invented:
                invented.append(name)

    return invented


@dataclass
class AnswerScore:
    """How one answer measures up to its question's expectations."""

    query: str
    answer: str
    seconds: float
    file_coverage: float | None
    symbol_coverage: float | None
    concept_coverage: float | None
    invented_paths: list[str] = field(default_factory=list)
    invented_identifiers: list[str] = field(default_factory=list)

    @property
    def refused(self) -> bool:
        return REFUSAL in self.answer.lower().replace("’", "'")

    @property
    def words(self) -> int:
        return len(self.answer.split())

    @property
    def coverage(self) -> float:
        """The mean of whichever coverages the question defines."""

        parts = [
            part
            for part in (
                self.file_coverage,
                self.symbol_coverage,
                self.concept_coverage,
            )
            if part is not None
        ]

        return sum(parts) / len(parts) if parts else 0.0

    @property
    def invented(self) -> int:
        return len(self.invented_paths) + len(self.invented_identifiers)


def score_answer(
    case: RetrievalTestCase,
    answer: str,
    repository: Repository,
    seconds: float = 0.0,
) -> AnswerScore:
    """Score one answer against its question."""

    text = answer.replace("\\", "/")

    answer_stems = {_stem(w) for w in _WORD.findall(text.lower())}

    files = case.expected_file_paths
    symbols = case.expected_symbols or []
    concepts = case.expected_concepts or []

    return AnswerScore(
        query=case.query,
        answer=answer,
        seconds=seconds,
        file_coverage=_share(sum(_cited(text, f) for f in files), len(files)),
        symbol_coverage=_share(sum(s in text for s in symbols), len(symbols)),
        concept_coverage=_share(
            sum(_explains(answer_stems, c) for c in concepts),
            len(concepts),
        ),
        invented_paths=invented_paths(text, repository),
        invented_identifiers=invented_identifiers(text, repository),
    )


def _mean(
    values: Iterable[float | None],
) -> float | None:
    present = [v for v in values if v is not None]

    return sum(present) / len(present) if present else None


def summarize_scores(
    scores: list[AnswerScore],
) -> dict[str, float | None]:
    """Averages across a set of answers."""

    total = max(len(scores), 1)

    return {
        "answers": len(scores),
        "coverage": _mean(s.coverage for s in scores),
        "file_coverage": _mean(s.file_coverage for s in scores),
        "symbol_coverage": _mean(s.symbol_coverage for s in scores),
        "concept_coverage": _mean(s.concept_coverage for s in scores),
        "answers_with_invented_names": sum(1 for s in scores if s.invented) / total,
        "invented_names_per_answer": sum(s.invented for s in scores) / total,
        "refusals": sum(1 for s in scores if s.refused) / total,
        "words": _mean(float(s.words) for s in scores),
        "seconds": _mean(s.seconds for s in scores),
    }


def evaluate_answers(
    chat_service: ChatService,
    cases: list[RetrievalTestCase],
    root: Path,
    repository: Repository | None = None,
) -> list[AnswerScore]:
    """Ask every question through the chat service and score each answer."""

    repository = repository or load_repository(root)

    scores: list[AnswerScore] = []

    for case in cases:
        started = time.perf_counter()

        response = chat_service.chat(
            ChatRequest(
                query=case.query,
                root_directory=str(root),
            ),
        )

        scores.append(
            score_answer(
                case,
                response.content,
                repository,
                seconds=time.perf_counter() - started,
            ),
        )

    return scores
