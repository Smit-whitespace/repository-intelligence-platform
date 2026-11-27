"""Validation after edits: run the project's own checks.

Commands come only from ``<root>/.rip/validation.json``. That
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
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from app.core.storage.integrity import sign, verify
from app.core.storage.locations import (
    is_link,
    project_storage_directory,
)
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


UNTRUSTED_VALIDATION_MESSAGE = (
    "Validation did not run: these commands were not set in this RIP "
    "installation (for example, they came with a cloned repository). "
    "Review them in the Editing page and save them to approve."
)


class ValidationConfigView(ValidationConfig):
    """Validation commands, and whether they may run."""

    trusted: bool = Field(
        description="True when the commands were saved by this RIP "
        "installation. Commands that arrived with a repository are shown "
        "for review but never run until someone saves them.",
    )


def load_validation_config(
    repository_root: Path,
) -> ValidationConfigView:
    """Return the project's validation commands (none if not configured).

    The file sits in the repository's ``.rip`` directory, which
    a cloned repository can supply. Only a file signed by this
    installation is trusted; see ``app/core/storage/integrity.py``.
    """

    root = repository_root.resolve()

    path = validation_config_path(
        root,
    )

    _refuse_link(
        path,
    )

    if not path.is_file():
        return ValidationConfigView(
            trusted=True,
        )

    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8",
            ),
        )

        signature = data.pop(
            "signature",
            None,
        ) if isinstance(data, dict) else None

        config = ValidationConfig.model_validate(
            data,
        )

    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise EditingError(
            f"The validation configuration is invalid: {error}",
        ) from error

    return ValidationConfigView(
        commands=config.commands,
        trusted=verify(
            config.model_dump(
                mode="json",
            ),
            signature,
            "validation",
            root,
        ),
    )


def save_validation_config(
    repository_root: Path,
    config: ValidationConfig,
) -> None:
    """Save and sign validation commands, which approves them to run."""

    root = repository_root.resolve()

    path = validation_config_path(
        root,
    )

    _refuse_link(
        path,
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = ValidationConfig(
        commands=config.commands,
    ).model_dump(
        mode="json",
    )

    payload = json.dumps(
        {
            **data,
            "signature": sign(
                data,
                "validation",
                root,
            ),
        },
        indent=2,
    ) + "\n"

    # Write a new file and rename it over the old one: the rename replaces
    # a directory entry and never writes through a link.
    temporary = path.with_name(
        f".{path.name}.{os.getpid()}.tmp",
    )

    try:
        temporary.write_text(
            payload,
            encoding="utf-8",
        )

        temporary.replace(
            path,
        )

    finally:
        if temporary.exists():
            temporary.unlink()


def _refuse_link(
    path: Path,
) -> None:
    """Refuse a validation.json that is a symlink or junction.

    A repository could ship one pointing elsewhere; reading or saving
    through it would touch a file outside the project.
    """

    if is_link(
        path,
    ):
        raise EditingError(
            "The validation configuration is a link; RIP does not follow "
            "it. Delete .rip/validation.json and set the "
            "commands again.",
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

        try:
            # Resolve the program explicitly: without a shell, Windows
            # does not search PATHEXT for "pytest" -> "pytest.exe" itself.
            # (Inside the try: a NUL byte makes even this raise.)
            program = shutil.which(
                command.argv[0],
            ) or command.argv[0]

            # A new process group (Windows) or session (POSIX) lets a
            # timeout kill the whole tree. Killing only the direct child
            # is not enough: "npm test" runs npm.cmd -> cmd.exe -> node,
            # and a surviving grandchild keeps the output pipe open.
            process = subprocess.Popen(
                [
                    program,
                    *command.argv[1:],
                ],
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                **_process_group_options(),
            )

        except (OSError, ValueError) as error:
            return CommandResult(
                name=command.name,
                argv=command.argv,
                passed=False,
                duration_ms=elapsed_ms(),
                output=f"Could not start {command.argv[0]!r}: {error}",
            )

        try:
            output, _ = process.communicate(
                timeout=command.timeout_seconds,
            )

        except subprocess.TimeoutExpired:
            _kill_tree(
                process,
            )

            try:
                output, _ = process.communicate(
                    timeout=5,
                )

            except subprocess.TimeoutExpired:
                output = ""

            return CommandResult(
                name=command.name,
                argv=command.argv,
                passed=False,
                timed_out=True,
                duration_ms=elapsed_ms(),
                output=_tail(
                    (output or "")
                    + f"\n[stopped after {command.timeout_seconds:g} seconds]",
                ),
            )

        return CommandResult(
            name=command.name,
            argv=command.argv,
            passed=process.returncode == 0,
            exit_code=process.returncode,
            duration_ms=elapsed_ms(),
            output=_tail(
                output or "",
            ),
        )


def _process_group_options() -> dict:
    if sys.platform == "win32":
        return {
            "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP,
        }

    return {
        "start_new_session": True,
    }


def _kill_tree(
    process: subprocess.Popen,
) -> None:
    """Kill a command and everything it started."""

    if sys.platform == "win32":
        subprocess.run(
            [
                "taskkill",
                "/F",
                "/T",
                "/PID",
                str(process.pid),
            ],
            capture_output=True,
            timeout=30,
            check=False,
        )

    else:
        try:
            os.killpg(
                process.pid,
                signal.SIGKILL,
            )

        except OSError:
            pass

    process.kill()


def _tail(
    output: str,
) -> str:
    if len(output) <= MAX_OUTPUT_CHARACTERS:
        return output

    return "…" + output[-MAX_OUTPUT_CHARACTERS:]
