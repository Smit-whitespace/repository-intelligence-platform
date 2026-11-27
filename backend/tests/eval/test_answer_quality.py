"""Tests for answer scoring."""

from pathlib import Path

from eval.answer_quality import Repository
from eval.answer_quality import invented_identifiers
from eval.answer_quality import invented_paths
from eval.answer_quality import load_repository
from eval.answer_quality import score_answer
from eval.answer_quality import summarize_scores
from eval.models import RetrievalTestCase

REPOSITORY = Repository(
    files=frozenset(
        {
            "backend/app/projects/initialization_service.py",
            "frontend/src/stores/authStore.ts",
        },
    ),
    identifiers=frozenset(
        {"ProjectInitializationService", "open_project", "build_index", "root"},
    ),
    mentioned_paths=frozenset({"rip/project.json", "credentials.json"}),
)

CASE = RetrievalTestCase(
    query="What does ProjectInitializationService do?",
    expected_file_paths=["backend/app/projects/initialization_service.py"],
    expected_symbols=["ProjectInitializationService", "open_project"],
    expected_concepts=["project initialization", "orchestration"],
)


class TestScoreAnswer:
    def test_full_answer_covers_everything(self) -> None:
        answer = (
            "`ProjectInitializationService` in "
            "`backend/app/projects/initialization_service.py` orchestrates "
            "initializing a project: `open_project` calls `build_index`."
        )

        score = score_answer(CASE, answer, REPOSITORY)

        assert score.file_coverage == 1.0
        assert score.symbol_coverage == 1.0
        assert score.concept_coverage == 1.0
        assert score.coverage == 1.0
        assert score.invented == 0
        assert not score.refused

    def test_file_name_alone_counts_as_a_citation(self) -> None:
        score = score_answer(CASE, "See initialization_service.py.", REPOSITORY)

        assert score.file_coverage == 1.0

    def test_windows_separators_count_as_a_citation(self) -> None:
        answer = r"See backend\app\projects\initialization_service.py."

        score = score_answer(CASE, answer, REPOSITORY)

        assert score.file_coverage == 1.0
        assert score.invented_paths == []

    def test_partial_answer_scores_partially(self) -> None:
        score = score_answer(CASE, "It initializes a new project.", REPOSITORY)

        assert score.file_coverage == 0.0
        assert score.symbol_coverage == 0.0
        assert score.concept_coverage == 0.5
        assert score.coverage == (0.0 + 0.0 + 0.5) / 3

    def test_missing_expectations_are_left_out_of_coverage(self) -> None:
        case = RetrievalTestCase(
            query="Where is the token kept?",
            expected_file_paths=["frontend/src/stores/authStore.ts"],
        )

        score = score_answer(case, "In authStore.ts.", REPOSITORY)

        assert score.symbol_coverage is None
        assert score.concept_coverage is None
        assert score.coverage == 1.0

    def test_refusal_is_detected_with_a_curly_apostrophe(self) -> None:
        answer = "I couldn’t find enough evidence in the indexed repository."

        assert score_answer(CASE, answer, REPOSITORY).refused


class TestInventedNames:
    def test_unknown_path_is_invented(self) -> None:
        answer = "See backend/app/projects/loader.py and initialization_service.py."

        assert invented_paths(answer, REPOSITORY) == ["backend/app/projects/loader.py"]

    def test_unknown_name_in_code_is_invented(self) -> None:
        answer = "Call `ProjectLoader.load_all()` after `open_project`."

        assert invented_identifiers(answer, REPOSITORY) == ["ProjectLoader", "load_all"]

    def test_names_in_fenced_code_are_checked(self) -> None:
        answer = "```python\nservice.open_project(root)\n```"

        assert invented_identifiers(answer, REPOSITORY) == ["service"]

    def test_runtime_files_the_code_mentions_are_not_invented(self) -> None:
        answer = (
            "Stored in `.rip/project.json` and "
            "`backend/.rip/project.json`; `credentials.json` is a secret."
        )

        assert invented_paths(answer, REPOSITORY) == []

    def test_a_mentioned_name_does_not_vouch_for_an_invented_folder(self) -> None:
        answer = "Stored in `a_typo/project.json`."

        assert invented_paths(answer, REPOSITORY) == ["a_typo/project.json"]

    def test_names_differing_only_in_edge_underscores_are_known(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "prompt.py").write_text("_INSTRUCTION = 1\n")

        repository = load_repository(tmp_path)

        assert invented_identifiers("`INSTRUCTION`", repository) == []

    def test_prose_is_not_checked_for_names(self) -> None:
        assert invented_identifiers("A ProjectLoader loads things.", REPOSITORY) == []


class TestLoadRepository:
    def test_reads_files_and_identifiers_and_skips_build_folders(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "main.py").write_text("def start_app(): pass\n")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "lib.js").write_text("function hidden() {}\n")
        (tmp_path / "logo.png").write_bytes(b"\x89PNG")

        repository = load_repository(tmp_path)

        assert repository.files == {"app/main.py"}
        assert "start_app" in repository.identifiers
        assert "hidden" not in repository.identifiers

    def test_ignored_folders_are_left_out(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "eval").mkdir()
        (tmp_path / "eval" / "examples.py").write_text("MADE_UP = 'x/made_up.py'\n")
        (tmp_path / "evaluate.py").write_text("real_name = 1\n")

        repository = load_repository(tmp_path, ignore=["eval"])

        assert repository.files == {"evaluate.py"}
        assert "MADE_UP" not in repository.identifiers
        assert repository.mentioned_paths == frozenset()

    def test_an_ignored_file_still_exists_with_the_names_it_defines(
        self,
        tmp_path: Path,
    ) -> None:
        # The scorer is a real file with real classes; only the made-up
        # examples in its strings and comments must not look real.
        (tmp_path / "scorer.py").write_text(
            "LIMIT = 3\n"
            "class Score:\n"
            "    def check(self):\n"
            "        return 'see FakeStore in x/made_up.py'  # or OtherFake\n",
        )

        repository = load_repository(tmp_path, ignore=["scorer.py"])

        assert repository.files == {"scorer.py"}
        assert {"LIMIT", "Score", "check"} <= repository.identifiers
        assert "FakeStore" not in repository.identifiers
        assert "OtherFake" not in repository.identifiers
        assert repository.mentioned_paths == frozenset()

    def test_collects_paths_the_text_mentions(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "store.py").write_text(
            'PATH = "~/.rip/models.json"  # see .\\notes\\todo.md\n',
        )

        repository = load_repository(tmp_path)

        assert repository.mentioned_paths == {
            "rip/models.json",
            "notes/todo.md",
        }


class TestSummarize:
    def test_averages_and_rates(self) -> None:
        good = score_answer(
            CASE,
            "`ProjectInitializationService` (initialization_service.py) "
            "orchestrates project initialization via `open_project`.",
            REPOSITORY,
            seconds=2.0,
        )
        bad = score_answer(CASE, "Use `MadeUpThing`.", REPOSITORY, seconds=4.0)

        summary = summarize_scores([good, bad])

        assert summary["answers"] == 2
        assert summary["coverage"] == (1.0 + 0.0) / 2
        assert summary["answers_with_invented_names"] == 0.5
        assert summary["invented_names_per_answer"] == 0.5
        assert summary["refusals"] == 0.0
        assert summary["seconds"] == 3.0

    def test_empty_set(self) -> None:
        summary = summarize_scores([])

        assert summary["answers"] == 0
        assert summary["coverage"] is None
