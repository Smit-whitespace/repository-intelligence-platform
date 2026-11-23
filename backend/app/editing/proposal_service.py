"""Proposal workflow: propose, review, apply, validate, roll back.

Lifecycle::

    pending --apply--> applied --rollback--> rolled_back
       └-----reject--> rejected

Applying goes through ``EditingService``, so every safety check still
holds: registered roots, protected paths, a snapshot first, all-or-
nothing writes, and a conflict error if any file changed since the
proposal was made (the proposal then stays pending; propose again).
"""

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from app.editing.change_applier import ChangeApplier
from app.editing.exceptions import ProposalStateError
from app.editing.planner import EditPlanner
from app.editing.proposals import (
    EditOperation,
    EditProposal,
    EditProposalView,
    ProposalSource,
    ProposalStatus,
    ProposalStore,
    build_proposal,
)
from app.editing.service import (
    EditingService,
    require_registered_root,
)
from app.editing.validation import (
    UNTRUSTED_VALIDATION_MESSAGE,
    CommandResult,
    ValidationConfig,
    ValidationConfigView,
    ValidationReport,
    ValidationRunner,
    load_validation_config,
    save_validation_config,
)
from app.workspace.service import WorkspaceOpener


class ProposalService:
    """Create and act on edit proposals for registered projects."""

    def __init__(
        self,
        editing_service: EditingService,
        change_applier: ChangeApplier,
        validation_runner: ValidationRunner,
        planner: EditPlanner,
        workspace_opener: WorkspaceOpener,
        edit_model_label: Callable[[], str],
    ) -> None:
        self._editing_service = editing_service

        self._change_applier = change_applier

        self._validation_runner = validation_runner

        self._planner = planner

        self._workspace_opener = workspace_opener

        self._edit_model_label = edit_model_label

    def propose(
        self,
        repository_root: Path,
        operations: list[EditOperation],
        description: str,
        source: ProposalSource = ProposalSource.CLIENT,
        model: str | None = None,
        notes: str | None = None,
    ) -> EditProposalView:
        """Build and store a proposal from search/replace operations."""

        root = self._validated_root(
            repository_root,
        )

        proposal = build_proposal(
            repository_root=root,
            operations=operations,
            description=description,
            source=source,
            change_applier=self._change_applier,
            model=model,
            notes=notes,
        )

        ProposalStore(
            root,
        ).save(
            proposal,
        )

        return proposal.view()

    def plan(
        self,
        repository_root: Path,
        instruction: str,
        files: list[str],
    ) -> EditProposalView:
        """Ask the edit model for edits, and store them as a proposal."""

        root = self._validated_root(
            repository_root,
        )

        planned = self._planner.plan(
            workspace=self._workspace_opener(
                root,
            ),
            instruction=instruction,
            files=files,
        )

        return self.propose(
            repository_root=root,
            operations=planned.operations,
            description=instruction.strip(),
            source=ProposalSource.PLANNER,
            model=self._edit_model_label(),
            notes=planned.notes or None,
        )

    def list(
        self,
        repository_root: Path,
        limit: int = 50,
    ) -> list[EditProposalView]:
        root = self._validated_root(
            repository_root,
        )

        return [
            proposal.view()
            for proposal in ProposalStore(root).list(
                limit=limit,
            )
        ]

    def get(
        self,
        repository_root: Path,
        proposal_id: str,
    ) -> EditProposalView:
        return self._load(
            repository_root,
            proposal_id,
        )[1].view()

    def apply(
        self,
        repository_root: Path,
        proposal_id: str,
        validate: bool = True,
    ) -> EditProposalView:
        """Apply a pending proposal, then optionally run validation."""

        root, proposal = self._load(
            repository_root,
            proposal_id,
        )

        self._require(
            proposal,
            ProposalStatus.PENDING,
            "applied",
        )

        snapshot_id = self._editing_service.apply(
            repository_root=root,
            change_set=proposal.change_set,
        )

        # The files are written: record that (and the snapshot needed to
        # roll back) before anything else can fail.
        proposal.status = ProposalStatus.APPLIED

        proposal.snapshot_id = snapshot_id

        view = self._save(
            root,
            proposal,
        )

        if not validate:
            return view

        try:
            proposal.validation = self._validate(
                root,
            )

        except Exception as error:  # noqa: BLE001 - reported, not raised
            proposal.validation = ValidationReport(
                ran=False,
                passed=False,
                results=[
                    CommandResult(
                        name="validation",
                        argv=[],
                        passed=False,
                        duration_ms=0,
                        output=f"Validation could not run: {error}",
                    ),
                ],
            )

        return self._save(
            root,
            proposal,
        )

    def reject(
        self,
        repository_root: Path,
        proposal_id: str,
    ) -> EditProposalView:
        root, proposal = self._load(
            repository_root,
            proposal_id,
        )

        self._require(
            proposal,
            ProposalStatus.PENDING,
            "rejected",
        )

        proposal.status = ProposalStatus.REJECTED

        return self._save(
            root,
            proposal,
        )

    def rollback(
        self,
        repository_root: Path,
        proposal_id: str,
    ) -> EditProposalView:
        """Undo an applied proposal from its snapshot."""

        root, proposal = self._load(
            repository_root,
            proposal_id,
        )

        self._require(
            proposal,
            ProposalStatus.APPLIED,
            "rolled back",
        )

        assert proposal.snapshot_id is not None

        self._editing_service.rollback(
            repository_root=root,
            snapshot_id=proposal.snapshot_id,
        )

        proposal.status = ProposalStatus.ROLLED_BACK

        return self._save(
            root,
            proposal,
        )

    def validation_config(
        self,
        repository_root: Path,
    ) -> ValidationConfigView:
        return load_validation_config(
            self._validated_root(
                repository_root,
            ),
        )

    def set_validation_config(
        self,
        repository_root: Path,
        config: ValidationConfig,
    ) -> ValidationConfigView:
        root = self._validated_root(
            repository_root,
        )

        save_validation_config(
            root,
            config,
        )

        return load_validation_config(
            root,
        )

    def run_validation(
        self,
        repository_root: Path,
    ) -> ValidationReport:
        return self._validate(
            self._validated_root(
                repository_root,
            ),
        )

    def _validate(
        self,
        root: Path,
    ) -> ValidationReport:
        config = load_validation_config(
            root,
        )

        # Commands that arrived with the repository never run unapproved.
        if not config.trusted:
            return ValidationReport(
                ran=False,
                passed=False,
                results=[
                    CommandResult(
                        name="validation",
                        argv=[],
                        passed=False,
                        duration_ms=0,
                        output=UNTRUSTED_VALIDATION_MESSAGE,
                    ),
                ],
            )

        return self._validation_runner.run(
            root,
            config,
        )

    def _load(
        self,
        repository_root: Path,
        proposal_id: str,
    ) -> tuple[Path, EditProposal]:
        root = self._validated_root(
            repository_root,
        )

        return root, ProposalStore(
            root,
        ).load(
            proposal_id,
        )

    @staticmethod
    def _require(
        proposal: EditProposal,
        status: ProposalStatus,
        action: str,
    ) -> None:
        if proposal.status is not status:
            raise ProposalStateError(
                f"This proposal is {proposal.status.value}; only "
                f"{status.value} proposals can be {action}.",
            )

    @staticmethod
    def _save(
        root: Path,
        proposal: EditProposal,
    ) -> EditProposalView:
        proposal.updated_at = datetime.now(
            UTC,
        )

        ProposalStore(
            root,
        ).save(
            proposal,
        )

        return proposal.view()

    @staticmethod
    def _validated_root(
        repository_root: Path,
    ) -> Path:
        # The same registered-project check as every other edit path.
        require_registered_root(
            repository_root,
        )

        return repository_root.resolve()
