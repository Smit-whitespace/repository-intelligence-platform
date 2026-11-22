"""Validation after edits: run the project's own checks.

Commands come only from ``<root>/.local_openclaw/validation.json``. That
directory is protected, so no edit (and no agent) can write it: an agent
can never choose what gets executed. People configure it from the RIP
app or by editing the file.

Commands run without a shell (an argv list, so nothing is interpolated),
in the repository root, one after another, each with a timeout, and only
the end of their output is kept. They still run the repository's code
(that is what tests do), which is why applying edits from an agent is a
separate, explicit opt-in.
"""

import json
import shutil
import subprocess
import time
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from app.core.storage.locations import project_storage_directory
from app.editing.exceptions import EditingError

VALIDATION_CONFIG_FILE_NAME = "validation.json"

MAX_OUTPUT_CHARACTERS = 8_000


class ValidationCommand(BaseModel):
    """One check, such as a test or lint command."""

    name: str = Field(
        min_length=1,
        examples=[
            "tests",
        ],
    )

    argv: list[str] = Field(
        min_length=1,
        description="Program and arguments, run without a shell.",
        examples=[
            ["pytest", "-q"],
        ],
    )

    timeout_seconds: float = Field(
        default=300,
        gt=0,
        le=3600,
    )


class ValidationConfig(BaseModel):
    """The project's validation commands."""

    commands: list[ValidationCommand] = Field(
        default_factory=list,
        max_length=20,
    )


class CommandResult(BaseModel):
    """Outcome of one validation command."""

    name: str

    argv: list[str]

    passed: bool

    exit_code: int | None = None

    timed_out: bool = False

    duration_ms: int

    output: str = Field(
        description="The last part of combined stdout and stderr.",
    )


class ValidationReport(BaseModel):
    """Outcome of all validation commands."""

    ran: bool = Field(
        description="False when the project has no validation commands.",
    )

    passed: bool

    results: list[CommandResult] = Field(
        default_factory=list,
    )


def validation_config_path(
    repository_root: Path,
) -> Path:
    return project_storage_directory(
        repository_root,
    ) / VALIDATION_CONFIG_FILE_NAME


def load_validation_config(
    repository_root: Path,
) -> ValidationConfig:
    """Return the project's validation commands (none if not configured)."""

    path = validation_config_path(
        repository_root,
    )

    if not path.is_file():
        return ValidationConfig()

    try:
        return ValidationConfig.model_validate(
            json.loads(
                path.read_text(
                    encoding="utf-8",
                ),
            ),
        )

    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise EditingError(
            f"The validation configuration is invalid: {error}",
        ) from error


def save_validation_config(
    repository_root: Path,
    config: ValidationConfig,
) -> None:
    path = validation_config_path(
        repository_root,
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            config.model_dump(
                mode="json",
            ),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


class ValidationRunner:
    """Run validation commands in a repository."""

    def run(
        self,
        repository_root: Path,
        config: ValidationConfig,
    ) -> ValidationReport:
        if not config.commands:
            return ValidationReport(
                ran=False,
                passed=True,
            )

        results = [
            self._run_command(
                repository_root.resolve(),
                command,
            )
            for command in config.commands
        ]

        return ValidationReport(
            ran=True,
            passed=all(
                result.passed
                for result in results
            ),
            results=results,
        )

    @staticmethod
    def _run_command(
        root: Path,
        command: ValidationCommand,
    ) -> CommandResult:
        started = time.monotonic()

        def elapsed_ms() -> int:
            return int(
                (time.monotonic() - started) * 1000,
            )

        # Resolve the program explicitly: without a shell, Windows does
        # not search PATHEXT for "pytest" -> "pytest.exe" on its own.
        program = shutil.which(
            command.argv[0],
        ) or command.argv[0]

        try:
            completed = subprocess.run(
                [
                    program,
                    *command.argv[1:],
                ],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=command.timeout_seconds,
                check=False,
            )

        except subprocess.TimeoutExpired as error:
            partial = _decode(error.stdout) + _decode(error.stderr)

            return CommandResult(
                name=command.name,
                argv=command.argv,
                passed=False,
                timed_out=True,
                duration_ms=elapsed_ms(),
                output=_tail(
                    partial
                    + f"\n[stopped after {command.timeout_seconds:g} seconds]",
                ),
            )

        except OSError as error:
            return CommandResult(
                name=command.name,
                argv=command.argv,
                passed=False,
                duration_ms=elapsed_ms(),
                output=f"Could not start {command.argv[0]!r}: {error}",
            )

        return CommandResult(
            name=command.name,
            argv=command.argv,
            passed=completed.returncode == 0,
            exit_code=completed.returncode,
            duration_ms=elapsed_ms(),
            output=_tail(
                (completed.stdout or "") + (completed.stderr or ""),
            ),
        )


def _decode(
    value: str | bytes | None,
) -> str:
    if value is None:
        return ""

    if isinstance(value, bytes):
        return value.decode(
            "utf-8",
            errors="replace",
        )

    return value


def _tail(
    output: str,
) -> str:
    if len(output) <= MAX_OUTPUT_CHARACTERS:
        return output

    return "…" + output[-MAX_OUTPUT_CHARACTERS:]
