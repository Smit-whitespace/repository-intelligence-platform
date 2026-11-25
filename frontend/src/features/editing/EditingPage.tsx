import { ApiErrorState } from "@/components/common/ApiErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import { LoadingState } from "@/components/common/LoadingState";
import { Button } from "@/components/ui/Button";
import {
  usePlanProposal,
  useProposalAction,
  useProposals,
  useRunValidation,
  useSaveValidationConfig,
  useValidationConfig,
} from "@/lib/api/queries";
import { cn } from "@/lib/utils/cn";
import { useProjectStore } from "@/stores/projectStore";
import type {
  EditProposal,
  ProposalStatus,
  ValidationReport,
} from "@/types/api";
import { Check, RefreshCw, RotateCcw, Sparkles, X } from "lucide-react";
import { useState, type ReactNode } from "react";
import { toast } from "sonner";
import { commandsToText, textToCommands } from "./commandLine";

const statusStyles: Record<ProposalStatus, string> = {
  pending: "border-[#4F8CFF]/40 text-[#8FB4FF]",
  applied: "border-[#22C55E]/40 text-[#4ADE80]",
  rejected: "border-[rgba(255,255,255,0.15)] text-[#7A8599]",
  rolled_back: "border-[#F59E0B]/40 text-[#FBBF24]",
};

const statusLabels: Record<ProposalStatus, string> = {
  pending: "Pending review",
  applied: "Applied",
  rejected: "Rejected",
  rolled_back: "Rolled back",
};

export function EditingPage() {
  const activeProject = useProjectStore((state) => state.activeProject);
  const root = activeProject?.root_directory ?? null;

  return (
    <section className="animate-fade-in space-y-8">
      <div>
        <h1 className="text-lg font-semibold text-[#F8FAFC]">Editing</h1>
        <p className="mt-1 text-sm text-[#7A8599]">
          Describe a change, review the diff, then apply it. Every apply takes a
          snapshot and can be rolled back.
        </p>
      </div>
      {root ? (
        <EditingWorkspace root={root} />
      ) : (
        <EmptyState
          title="No project open"
          description="Open a project before proposing code changes."
        />
      )}
    </section>
  );
}

function EditingWorkspace({ root }: { root: string }) {
  const proposals = useProposals(root);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const items = proposals.data?.proposals ?? [];
  const selected =
    items.find((proposal) => proposal.proposal_id === selectedId) ??
    items.at(0) ??
    null;

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
      <div className="space-y-4">
        <PlanPanel root={root} onProposed={setSelectedId} />
        {/* Keyed by root, so unsaved edits never carry over between projects. */}
        <ValidationPanel key={root} root={root} />
      </div>
      <div className="space-y-4">
        <Panel title="Proposals">
          {proposals.isLoading ? <LoadingState label="Loading proposals" /> : null}
          {proposals.isError ? <ApiErrorState error={proposals.error} /> : null}
          {proposals.data && !items.length ? (
            <p className="mt-3 text-sm text-[#7A8599]">
              No proposals yet. Describe a change, or let an agent propose one
              over MCP.
            </p>
          ) : null}
          <ul className="mt-3 space-y-2">
            {items.map((proposal) => (
              <li key={proposal.proposal_id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(proposal.proposal_id)}
                  className={cn(
                    "w-full rounded-[var(--radius-sm)] border px-3 py-2 text-left transition",
                    proposal.proposal_id === selected?.proposal_id
                      ? "border-[#4F8CFF] bg-[rgba(79,140,255,0.08)]"
                      : "border-[rgba(255,255,255,0.08)] hover:border-[rgba(255,255,255,0.2)]",
                  )}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="min-w-0 truncate text-sm text-[#F8FAFC]">
                      {proposal.description || "(no description)"}
                    </span>
                    <StatusBadge status={proposal.status} />
                  </div>
                  <p className="mt-1 text-xs text-[#7A8599]">
                    {proposal.files.length} file
                    {proposal.files.length === 1 ? "" : "s"} ·{" "}
                    {proposal.source === "planner"
                      ? `edit model ${proposal.model ?? ""}`
                      : "proposed by a client"}{" "}
                    · {new Date(proposal.created_at).toLocaleString()}
                  </p>
                </button>
              </li>
            ))}
          </ul>
        </Panel>
        {selected ? (
          // Keyed so an error or checkbox state never carries over to
          // another proposal.
          <ProposalDetail
            key={selected.proposal_id}
            root={root}
            proposal={selected}
          />
        ) : null}
      </div>
    </div>
  );
}

function PlanPanel({
  root,
  onProposed,
}: {
  root: string;
  onProposed: (proposalId: string) => void;
}) {
  const plan = usePlanProposal();
  const [instruction, setInstruction] = useState("");
  const [files, setFiles] = useState("");

  return (
    <Panel title="Describe a change">
      <form
        className="mt-3 space-y-3"
        onSubmit={(event) => {
          event.preventDefault();
          plan.mutate(
            {
              repository_root: root,
              instruction,
              files: files
                .split(/[\n,]/)
                .map((file) => file.trim())
                .filter(Boolean),
            },
            {
              onSuccess: (proposal) => {
                onProposed(proposal.proposal_id);
                setInstruction("");
                toast.success("Proposal ready for review");
              },
            },
          );
        }}
      >
        <textarea
          value={instruction}
          onChange={(event) => setInstruction(event.target.value)}
          placeholder="e.g. Add input validation to create_user in backend/app/users.py"
          rows={4}
          className={inputClass}
        />
        <input
          value={files}
          onChange={(event) => setFiles(event.target.value)}
          placeholder="Files to change (optional, comma-separated)"
          className={inputClass}
        />
        <Button type="submit" disabled={!instruction.trim() || plan.isPending}>
          {plan.isPending ? (
            <RefreshCw className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Sparkles className="h-4 w-4" aria-hidden="true" />
          )}
          Propose edits
        </Button>
        {plan.isError ? (
          <p className="whitespace-pre-wrap text-sm text-[#EF4444]">
            {plan.error.message}
          </p>
        ) : null}
        <p className="text-xs text-[#7A8599]">
          Uses the edit model shown in Settings. Nothing is written until you
          apply the proposal.
        </p>
      </form>
    </Panel>
  );
}

function ProposalDetail({
  root,
  proposal,
}: {
  root: string;
  proposal: EditProposal;
}) {
  const action = useProposalAction(root);
  const [validateAfter, setValidateAfter] = useState(true);

  const run = (kind: "apply" | "reject" | "rollback") =>
    action.mutate(
      { proposalId: proposal.proposal_id, action: kind, validateAfter },
      {
        onSuccess: (updated) => {
          const messages = {
            apply: "Proposal applied",
            reject: "Proposal rejected",
            rollback: "Proposal rolled back",
          };
          toast.success(messages[kind]);
          if (updated.validation?.ran && !updated.validation.passed) {
            toast.error("Validation failed after applying");
          }
        },
      },
    );

  return (
    <Panel title={proposal.description || "Proposal"}>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-[#7A8599]">
        <StatusBadge status={proposal.status} />
        <span className="font-mono">{proposal.proposal_id}</span>
      </div>
      {proposal.notes ? (
        <p className="mt-3 whitespace-pre-wrap text-sm text-[#AAB4C5]">
          {proposal.notes}
        </p>
      ) : null}
      <div className="mt-4 flex flex-wrap items-center gap-3">
        {proposal.status === "pending" ? (
          <>
            <Button onClick={() => run("apply")} disabled={action.isPending}>
              <Check className="h-4 w-4" aria-hidden="true" />
              Apply
            </Button>
            <Button
              variant="secondary"
              onClick={() => run("reject")}
              disabled={action.isPending}
            >
              <X className="h-4 w-4" aria-hidden="true" />
              Reject
            </Button>
            <label className="flex items-center gap-2 text-sm text-[#AAB4C5]">
              <input
                type="checkbox"
                checked={validateAfter}
                onChange={(event) => setValidateAfter(event.target.checked)}
              />
              Run validation after applying
            </label>
          </>
        ) : null}
        {proposal.status === "applied" ? (
          <Button
            variant="secondary"
            onClick={() => run("rollback")}
            disabled={action.isPending}
          >
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            Roll back
          </Button>
        ) : null}
      </div>
      {action.isError ? (
        <p className="mt-3 whitespace-pre-wrap text-sm text-[#EF4444]">
          {action.error.message}
        </p>
      ) : null}
      {proposal.validation ? (
        <div className="mt-4">
          <ValidationResults report={proposal.validation} />
        </div>
      ) : null}
      <div className="mt-4 space-y-4">
        {proposal.files.map((file) => (
          <div key={file.path}>
            <p className="break-anywhere mb-1 font-mono text-xs text-[#AAB4C5]">
              {file.path}{" "}
              <span className="text-[#4ADE80]">+{file.added_lines}</span>{" "}
              <span className="text-[#F87171]">-{file.removed_lines}</span>
              {file.change === "create" ? (
                <span className="ml-2 text-[#7A8599]">(new file)</span>
              ) : null}
            </p>
            <DiffView diff={file.diff} />
          </div>
        ))}
      </div>
    </Panel>
  );
}

function DiffView({ diff }: { diff: string }) {
  const lines = diff.replace(/\n$/, "").split("\n");

  return (
    <pre className="max-h-[480px] overflow-auto rounded-[var(--radius-sm)] border border-[rgba(255,255,255,0.06)] bg-[#0A0F1E] p-3 font-mono text-xs leading-relaxed">
      {lines.map((line, index) => (
        <div
          key={index}
          className={cn(
            "whitespace-pre",
            line.startsWith("+++") || line.startsWith("---")
              ? "text-[#7A8599]"
              : line.startsWith("@@")
                ? "text-[#8FB4FF]"
                : line.startsWith("+")
                  ? "bg-[rgba(34,197,94,0.08)] text-[#4ADE80]"
                  : line.startsWith("-")
                    ? "bg-[rgba(239,68,68,0.08)] text-[#F87171]"
                    : "text-[#AAB4C5]",
          )}
        >
          {line || " "}
        </div>
      ))}
    </pre>
  );
}

function ValidationPanel({ root }: { root: string }) {
  const config = useValidationConfig(root);
  const save = useSaveValidationConfig(root);
  const runNow = useRunValidation(root);
  const [text, setText] = useState<string | null>(null);

  const saved = config.data ? commandsToText(config.data.commands) : "";

  const value = text ?? saved;
  const untrusted = config.data?.trusted === false;

  return (
    <Panel title="Validation commands">
      <p className="mt-1 text-sm text-[#7A8599]">
        One command per line, run in the repository root after applying
        (without a shell). Only commands saved here ever run; agents and
        repositories cannot set them.
      </p>
      {untrusted ? (
        <p className="mt-3 rounded-[var(--radius-sm)] border border-[#F59E0B]/40 p-2 text-sm text-[#FBBF24]">
          These commands came with the repository (they were not saved in
          this RIP installation), so they will not run. Review them
          carefully, then save to approve them.
        </p>
      ) : null}
      <textarea
        value={value}
        onChange={(event) => setText(event.target.value)}
        placeholder={"pytest -q\nruff check ."}
        rows={3}
        className={cn(inputClass, "mt-3 font-mono")}
      />
      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          variant="secondary"
          disabled={
            save.isPending ||
            (!untrusted && (text === null || text === saved))
          }
          onClick={() =>
            save.mutate(
              {
                commands: textToCommands(value, config.data?.commands ?? []),
              },
              {
                onSuccess: () => {
                  setText(null);
                  toast.success(
                    untrusted
                      ? "Validation commands approved"
                      : "Validation commands saved",
                  );
                },
              },
            )
          }
        >
          Save
        </Button>
        <Button
          variant="ghost"
          disabled={!saved || untrusted || runNow.isPending}
          onClick={() => runNow.mutate()}
        >
          {runNow.isPending ? (
            <RefreshCw className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : null}
          Run now
        </Button>
      </div>
      {save.isError ? (
        <p className="mt-3 text-sm text-[#EF4444]">{save.error.message}</p>
      ) : null}
      {runNow.isError ? (
        <p className="mt-3 text-sm text-[#EF4444]">{runNow.error.message}</p>
      ) : null}
      {runNow.data ? (
        <div className="mt-3">
          <ValidationResults report={runNow.data} />
        </div>
      ) : null}
    </Panel>
  );
}

function ValidationResults({ report }: { report: ValidationReport }) {
  if (!report.ran) {
    // Not run: either nothing is configured, or the commands were not
    // approved (the reason is in the first result).
    return (
      <p
        className={cn(
          "text-sm",
          report.results.length ? "text-[#FBBF24]" : "text-[#7A8599]",
        )}
      >
        {report.results.at(0)?.output ??
          "No validation commands are configured for this project."}
      </p>
    );
  }

  return (
    <div className="space-y-2">
      <p
        className={cn(
          "text-sm font-medium",
          report.passed ? "text-[#4ADE80]" : "text-[#F87171]",
        )}
      >
        Validation {report.passed ? "passed" : "failed"}
      </p>
      {report.results.map((result, index) => (
        <details
          key={`${index}-${result.name}`}
          open={!result.passed}
          className="rounded-[var(--radius-sm)] border border-[rgba(255,255,255,0.06)] p-2"
        >
          <summary className="break-anywhere cursor-pointer text-sm text-[#AAB4C5]">
            <span className={result.passed ? "text-[#4ADE80]" : "text-[#F87171]"}>
              {result.passed ? "✓" : "✗"}
            </span>{" "}
            {result.name}{" "}
            <span className="text-xs text-[#7A8599]">
              {result.timed_out
                ? "timed out"
                : `exit ${result.exit_code ?? "?"}`}{" "}
              · {(result.duration_ms / 1000).toFixed(1)}s
            </span>
          </summary>
          <pre className="break-anywhere mt-2 max-h-64 overflow-auto whitespace-pre-wrap font-mono text-xs text-[#AAB4C5]">
            {result.output || "(no output)"}
          </pre>
        </details>
      ))}
    </div>
  );
}

function StatusBadge({ status }: { status: ProposalStatus }) {
  return (
    <span
      className={cn(
        "shrink-0 rounded-full border px-2 py-0.5 text-xs",
        statusStyles[status],
      )}
    >
      {statusLabels[status]}
    </span>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-[var(--radius)] border border-[rgba(255,255,255,0.06)] bg-[#111827] p-5">
      <h3 className="break-anywhere text-sm font-semibold text-[#F8FAFC]">{title}</h3>
      {children}
    </section>
  );
}

const inputClass =
  "w-full rounded-[var(--radius-sm)] border border-[rgba(255,255,255,0.1)] bg-[#0A0F1E] px-3 py-2 text-sm text-[#F8FAFC] outline-none transition placeholder:text-[#4B5568] focus:border-[#4F8CFF]/50";
