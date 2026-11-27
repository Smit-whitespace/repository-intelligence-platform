"""Settings come from ``RIP_*`` variables; the former ``LOC_*`` still work."""

from pathlib import Path

import pytest

from app.core.config.provider import read_environment


@pytest.fixture(autouse=True)
def _clean_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("RIP_OLLAMA_CHAT_MODEL", "LOC_OLLAMA_CHAT_MODEL"):
        monkeypatch.delenv(name, raising=False)


def test_rip_variables_are_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RIP_OLLAMA_CHAT_MODEL", "llama3:8b")

    assert read_environment(env_file=None).ollama_chat_model == "llama3:8b"


def test_a_legacy_loc_variable_still_works_and_warns(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("LOC_OLLAMA_CHAT_MODEL", "llama3:8b")

    with caplog.at_level("WARNING"):
        environment = read_environment(env_file=None)

    assert environment.ollama_chat_model == "llama3:8b"
    assert "LOC_OLLAMA_CHAT_MODEL" in caplog.text
    assert "RIP_OLLAMA_CHAT_MODEL" in caplog.text


def test_rip_wins_over_loc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RIP_OLLAMA_CHAT_MODEL", "new:1b")
    monkeypatch.setenv("LOC_OLLAMA_CHAT_MODEL", "old:1b")

    assert read_environment(env_file=None).ollama_chat_model == "new:1b"


def test_legacy_names_in_an_env_file_still_work(
    tmp_path: Path,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("LOC_OLLAMA_CHAT_MODEL=llama3:8b\n", encoding="utf-8")

    assert read_environment(env_file=env_file).ollama_chat_model == "llama3:8b"


def test_without_either_the_default_applies() -> None:
    assert read_environment(env_file=None).ollama_chat_model == "qwen3:8b"
