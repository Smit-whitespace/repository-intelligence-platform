"""Repository Editing endpoints."""

from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Response
from fastapi import status

from app.api.response_docs import (
    BAD_REQUEST_RESPONSE,
    CONFLICT_RESPONSE,
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    SERVER_ERROR_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from app.api.routes.editing_schemas import (
    ApplyProposalRequest,
    ApplyRequest,
    ApplyResponse,
    PlanEditRequest,
    ProposalActionRequest,
    ProposalListResponse,
    ProposeEditsRequest,
    RollbackRequest,
    ValidationConfigRequest,
)
from app.dependencies.providers import (
    get_editing_service,
    get_proposal_service,
)
from app.editing.proposal_service import ProposalService
from app.editing.proposals import EditProposalView
from app.editing.validation import (
    ValidationConfigView,
    ValidationReport,
)
from app.editing.models import (
    EditRequest,
    EditResponse,
)
from app.editing.service import (
    EditingService,
)

router = APIRouter(
    prefix="/editing",
    tags=["Editing"],
)


@router.post(
    "/edit",
    response_model=EditResponse,
    operation_id="planEdit",
    summary="Plan repository edit",
    description=(
        "Generate a ChangeSet for client review without mutating the "
        "repository."
    ),
    response_description="Planned ChangeSet for review.",
    responses={
        **BAD_REQUEST_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
def edit_repository(
    request: EditRequest,
    editing_service: EditingService = Depends(
        get_editing_service,
    ),
) -> EditResponse:
    """Generate repository modifications."""

    return editing_service.edit(
        request,
    )


@router.post(
    "/apply",
    response_model=ApplyResponse,
    operation_id="applyChangeSet",
    summary="Apply ChangeSet",
    description=(
        "Create a snapshot, persist it, and explicitly apply a reviewed "
        "ChangeSet."
    ),
    response_description="Generated snapshot identifier for rollback.",
    responses={
        **BAD_REQUEST_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **SERVER_ERROR_RESPONSE,
    },
)
def apply_changes(
    request: ApplyRequest,
    editing_service: EditingService = Depends(
        get_editing_service,
    ),
) -> ApplyResponse:
    """Apply a previously planned ChangeSet."""

    snapshot_id = editing_service.apply(
        repository_root=request.repository_root,
        change_set=request.change_set,
    )

    return ApplyResponse(
        snapshot_id=snapshot_id,
    )


@router.post(
    "/rollback",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="rollbackChangeSet",
    summary="Rollback applied ChangeSet",
    description=(
        "Restore repository files from a previously persisted snapshot."
    ),
    response_description="Rollback completed successfully.",
    responses={
        **BAD_REQUEST_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **SERVER_ERROR_RESPONSE,
    },
)
def rollback_changes(
    request: RollbackRequest,
    editing_service: EditingService = Depends(
        get_editing_service,
    ),
) -> Response:
    """Restore files from a previously captured snapshot."""

    editing_service.rollback(
        repository_root=request.repository_root,
        snapshot_id=request.snapshot_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


# --- Proposals -----------------------------------------------------------
#
# The preferred flow: propose (from operations or an instruction), review
# the stored diff, then apply *by id*. Contents are never re-sent at apply
# time, so what was reviewed is exactly what is written.

_PROPOSAL_RESPONSES = {
    **BAD_REQUEST_RESPONSE,
    **FORBIDDEN_RESPONSE,
    **VALIDATION_ERROR_RESPONSE,
}


@router.post(
    "/proposals",
    response_model=EditProposalView,
    operation_id="proposeEdits",
    summary="Propose edits",
    description=(
        "Turn search/replace operations into a stored proposal with a "
        "unified diff. Nothing is written to the repository. Each search "
        "text must occur exactly once in its file."
    ),
    response_description="The stored proposal.",
    responses=_PROPOSAL_RESPONSES,
)
def propose_edits(
    request: ProposeEditsRequest,
    proposal_service: ProposalService = Depends(
        get_proposal_service,
    ),
) -> EditProposalView:
    """Create a proposal from explicit operations."""

    return proposal_service.propose(
        repository_root=request.repository_root,
        operations=request.edits,
        description=request.description,
    )


@router.post(
    "/proposals/plan",
    response_model=EditProposalView,
    operation_id="planEditProposal",
    summary="Plan edits with the edit model",
    description=(
        "Ask RIP's edit model (the edit.plan task) for edits that carry "
        "out an instruction, and store them as a proposal. Nothing is "
        "written to the repository."
    ),
    response_description="The stored proposal.",
    responses={
        **_PROPOSAL_RESPONSES,
        **SERVER_ERROR_RESPONSE,
    },
)
def plan_edit_proposal(
    request: PlanEditRequest,
    proposal_service: ProposalService = Depends(
        get_proposal_service,
    ),
) -> EditProposalView:
    """Create a proposal from an instruction."""

    return proposal_service.plan(
        repository_root=request.repository_root,
        instruction=request.instruction,
        files=request.files,
    )


@router.get(
    "/proposals",
    response_model=ProposalListResponse,
    operation_id="listEditProposals",
    summary="List proposals",
    description="Return the project's proposals, newest first.",
    response_description="Proposals.",
    responses=_PROPOSAL_RESPONSES,
)
def list_edit_proposals(
    root_directory: Path = Query(
        ...,
        description="Absolute path of a registered RIP project root.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    proposal_service: ProposalService = Depends(
        get_proposal_service,
    ),
) -> ProposalListResponse:
    """List proposals."""

    return ProposalListResponse(
        proposals=proposal_service.list(
            repository_root=root_directory,
            limit=limit,
        ),
    )


@router.get(
    "/proposals/{proposal_id}",
    response_model=EditProposalView,
    operation_id="getEditProposal",
    summary="Get proposal",
    description="Return one proposal with its diff and status.",
    response_description="The proposal.",
    responses={
        **_PROPOSAL_RESPONSES,
        **NOT_FOUND_RESPONSE,
    },
)
def get_edit_proposal(
    proposal_id: str,
    root_directory: Path = Query(
        ...,
        description="Absolute path of a registered RIP project root.",
    ),
    proposal_service: ProposalService = Depends(
        get_proposal_service,
    ),
) -> EditProposalView:
    """Return one proposal."""

    return proposal_service.get(
        repository_root=root_directory,
        proposal_id=proposal_id,
    )


@router.post(
    "/proposals/{proposal_id}/apply",
    response_model=EditProposalView,
    operation_id="applyEditProposal",
    summary="Apply proposal",
    description=(
        "Apply a pending proposal (with a snapshot for rollback), then run "
        "the project's validation commands unless validate_after is false. "
        "Returns 409 if a file changed since the proposal was made."
    ),
    response_description="The applied proposal, with validation results.",
    responses={
        **_PROPOSAL_RESPONSES,
        **NOT_FOUND_RESPONSE,
        **CONFLICT_RESPONSE,
        **SERVER_ERROR_RESPONSE,
    },
)
def apply_edit_proposal(
    proposal_id: str,
    request: ApplyProposalRequest,
    proposal_service: ProposalService = Depends(
        get_proposal_service,
    ),
) -> EditProposalView:
    """Apply a proposal."""

    return proposal_service.apply(
        repository_root=request.repository_root,
        proposal_id=proposal_id,
        validate=request.validate_after,
    )


@router.post(
    "/proposals/{proposal_id}/reject",
    response_model=EditProposalView,
    operation_id="rejectEditProposal",
    summary="Reject proposal",
    description="Mark a pending proposal as rejected.",
    response_description="The rejected proposal.",
    responses={
        **_PROPOSAL_RESPONSES,
        **NOT_FOUND_RESPONSE,
        **CONFLICT_RESPONSE,
    },
)
def reject_edit_proposal(
    proposal_id: str,
    request: ProposalActionRequest,
    proposal_service: ProposalService = Depends(
        get_proposal_service,
    ),
) -> EditProposalView:
    """Reject a proposal."""

    return proposal_service.reject(
        repository_root=request.repository_root,
        proposal_id=proposal_id,
    )


@router.post(
    "/proposals/{proposal_id}/rollback",
    response_model=EditProposalView,
    operation_id="rollbackEditProposal",
    summary="Roll back proposal",
    description=(
        "Undo an applied proposal from its snapshot. Returns 409 if a file "
        "changed after it was applied."
    ),
    response_description="The rolled-back proposal.",
    responses={
        **_PROPOSAL_RESPONSES,
        **NOT_FOUND_RESPONSE,
        **CONFLICT_RESPONSE,
        **SERVER_ERROR_RESPONSE,
    },
)
def rollback_edit_proposal(
    proposal_id: str,
    request: ProposalActionRequest,
    proposal_service: ProposalService = Depends(
        get_proposal_service,
    ),
) -> EditProposalView:
    """Roll back a proposal."""

    return proposal_service.rollback(
        repository_root=request.repository_root,
        proposal_id=proposal_id,
    )


# --- Validation ----------------------------------------------------------


@router.get(
    "/validation",
    response_model=ValidationConfigView,
    operation_id="getValidationConfig",
    summary="Get validation commands",
    description=(
        "Return the project's validation commands (from "
        ".local_openclaw/validation.json)."
    ),
    response_description="Validation commands.",
    responses=_PROPOSAL_RESPONSES,
)
def get_validation_config(
    root_directory: Path = Query(
        ...,
        description="Absolute path of a registered RIP project root.",
    ),
    proposal_service: ProposalService = Depends(
        get_proposal_service,
    ),
) -> ValidationConfigView:
    """Return validation commands."""

    return proposal_service.validation_config(
        root_directory,
    )


@router.put(
    "/validation",
    response_model=ValidationConfigView,
    operation_id="updateValidationConfig",
    summary="Set validation commands",
    description=(
        "Save the project's validation commands. They run without a shell, "
        "in the repository root, after applying a proposal."
    ),
    response_description="Saved validation commands.",
    responses=_PROPOSAL_RESPONSES,
)
def update_validation_config(
    request: ValidationConfigRequest,
    proposal_service: ProposalService = Depends(
        get_proposal_service,
    ),
) -> ValidationConfigView:
    """Save validation commands."""

    return proposal_service.set_validation_config(
        repository_root=request.repository_root,
        config=request.config,
    )


@router.post(
    "/validation/run",
    response_model=ValidationReport,
    operation_id="runValidation",
    summary="Run validation",
    description="Run the project's validation commands now.",
    response_description="Validation results.",
    responses=_PROPOSAL_RESPONSES,
)
def run_validation(
    request: ProposalActionRequest,
    proposal_service: ProposalService = Depends(
        get_proposal_service,
    ),
) -> ValidationReport:
    """Run validation commands."""

    return proposal_service.run_validation(
        request.repository_root,
    )
