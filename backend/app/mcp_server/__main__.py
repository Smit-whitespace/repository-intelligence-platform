"""Run RIP as an MCP server over stdio for one repository.

Usage::

    python -m app.mcp_server --root <repository> [--editing off|propose|apply]

The repository is fixed for the life of the process, so an agent can
never point the tools at another directory. Stdout carries the MCP
protocol only; all logging goes to stderr.
"""

import argparse
import sys
from pathlib import Path

from app.core.config.settings import settings
from app.core.logging.configuration import configure_logging
from app.core.storage.locations import is_registered_project
from app.dependencies.providers import (
    get_indexing_service,
    get_project_service,
    get_proposal_service,
    get_workspace_opener,
)
from app.mcp_server.server import (
    EditingMode,
    build_server,
)
from app.projects.exceptions import InvalidProjectError


def main(
    argv: list[str] | None = None,
) -> int:
    """Start the server; return a process exit code."""

    parser = argparse.ArgumentParser(
        prog="python -m app.mcp_server",
        description="Serve one repository's RIP tools over MCP (stdio).",
    )

    parser.add_argument(
        "--editing",
        choices=[
            mode.value
            for mode in EditingMode
        ],
        default=EditingMode.PROPOSE.value,
        help="off: no editing tools. propose (default): the agent proposes "
        "edits and a person applies them in the RIP app. apply: the agent "
        "may also apply and roll back, which runs the project's validation "
        "commands.",
    )

    parser.add_argument(
        "--root",
        required=True,
        help="Repository root to serve. Registered as a RIP project on "
        "first use (metadata only; nothing is indexed until reindex).",
    )

    arguments = parser.parse_args(
        argv,
    )

    configure_logging(
        level=settings.logging.level,
        json_logs=settings.logging.json_logs,
    )

    root = Path(
        arguments.root,
    ).expanduser().resolve()

    if not is_registered_project(
        root,
    ):
        # The user named this root in their own MCP configuration, which
        # is what registering it means. Agents cannot register roots.
        try:
            get_project_service().open_project(
                root,
            )

        except InvalidProjectError as error:
            print(
                f"rip mcp: {error}",
                file=sys.stderr,
            )

            return 2

    workspace = get_workspace_opener()(
        root,
    )

    build_server(
        workspace=workspace,
        indexing_service=get_indexing_service(),
        proposal_service=get_proposal_service(),
        editing_mode=EditingMode(
            arguments.editing,
        ),
    ).run(
        "stdio",
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main(),
    )
