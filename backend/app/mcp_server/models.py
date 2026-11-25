"""Proposal shapes returned to MCP clients.

Agents pay for every token they read, so these differ from the REST
views: the diff appears once (not once per file and again in full),
and listings carry no diffs at all; get_proposal returns one.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.editing.proposals import (
    EditProposalView,
    FileChange,
    ProposalSource,
    ProposalStatus,
)
from app.editing.validation import ValidationReport


class ProposalFileSummary(BaseModel):
    """What a proposal does to one file."""

    path: str

    change: FileChange

    added_lines: int

    removed_lines: int


class ProposalSummary(BaseModel):
    """A proposal without its diff."""

    proposal_id: str

    created_at: datetime

    updated_at: datetime

    status: ProposalStatus

    source: ProposalSource

    description: str

    files: list[ProposalFileSummary]

    snapshot_id: str | None = Field(
        default=None,
        description="Snapshot for rolling back, once applied.",
    )

    validation_passed: bool | None = Field(
        default=None,
        description="Whether validation passed after applying (null if it did not run).",
    )

    @classmethod
    def of(
        cls,
        view: EditProposalView,
    ) -> "ProposalSummary":
        return cls(
            proposal_id=view.proposal_id,
            created_at=view.created_at,
            updated_at=view.updated_at,
            status=view.status,
            source=view.source,
            description=view.description,
            files=[
                ProposalFileSummary(
                    path=file.path,
                    change=file.change,
                    added_lines=file.added_lines,
                    removed_lines=file.removed_lines,
                )
                for file in view.files
            ],
            snapshot_id=view.snapshot_id,
            validation_passed=(
                view.validation.passed
                if view.validation and view.validation.ran
                else None
            ),
        )


class ProposalDetail(ProposalSummary):
    """A proposal with its unified diff and validation output."""

    model: str | None = Field(
        default=None,
        description="provider/model that generated the edits (planner only).",
    )

    notes: str | None = None

    diff: str = Field(
        description="Unified diff of the whole proposal.",
    )

    validation: ValidationReport | None = None

    @classmethod
    def of(
        cls,
        view: EditProposalView,
    ) -> "ProposalDetail":
        return cls(
            **ProposalSummary.of(view).model_dump(),
            model=view.model,
            notes=view.notes,
            diff=view.diff,
            validation=view.validation,
        )


class ProposalList(BaseModel):
    """Recent proposals, newest first."""

    proposals: list[ProposalSummary]
