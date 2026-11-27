# ADR-0019: Signed State in Project Storage

> **Amended by [ADR-0021](adr-0021-rip-storage-and-settings-names.md):** the storage directory is now `.rip` and the environment prefix `RIP_`. `.local_openclaw` and `LOC_` below are the former names.

**Status:** Adopted

**Context:**

Per ADR-0010, RIP keeps project state in `<root>/.local_openclaw/`: the index, project metadata, editing snapshots and, since the editing workflow, edit proposals and validation commands. That directory is ordinary repository content. A repository can ship its own `.local_openclaw/`, and cloning it brings that directory along.

A security review confirmed two exploits:

1. A repository shipped `.local_openclaw/validation.json`. The first time someone applied any edit (validation runs by default), the attacker's command ran.
2. A repository shipped a proposal whose displayed diff (`-print(1) +print(2)`) differed from its stored contents (`os.system(...)`). Applying it wrote the hidden contents.

**Decision:**

Keep the storage location, and make RIP's security-relevant state tamper-evident:

- Sign every proposal, snapshot and validation configuration RIP writes with HMAC-SHA256, using a per-user key outside any repository (`~/.local_openclaw/integrity.key`, created on first use; `LOC_INTEGRITY_KEY_PATH` overrides it).
- Bind each signature to the file's purpose (`proposal`, `snapshot`, `validation`) and to the resolved project root, so a signed file can be neither repurposed nor copied into another project.
- Refuse unsigned or mismatched proposals and snapshots (HTTP 403), and leave them out of listings.
- Show unsigned validation commands for review, but never run them. Saving them in the RIP app signs them, which is the approval.
- Refuse a `validation.json` that is a symlink or junction.

**Consequences:**

Positive:
- A cloned repository cannot run commands or apply hidden contents through RIP.
- ADR-0010's project-local storage is unchanged: no migration, and everything stays in one place per project.

Negative:
- Snapshots and proposals created before this change, or on another machine, are refused. Rolling them back has to be done by hand.
- Anyone who can read the key file can forge signatures. That party already runs as the user, so this is outside the threat model, which is repository content.
- The index is not signed. A shipped index can make semantic search return attacker-chosen text. That is data shown to people and agents, not executed; reindexing replaces it.

**Alternatives Considered:**

- Move proposals, snapshots and validation commands to per-user storage keyed by project root: rejected for now because it reopens ADR-0010. It would also fix the problem, and would keep full file contents in proposals out of the repository directory.
- Refuse any `.local_openclaw` content that git tracks: rejected; it depends on git being installed and the repository being a git checkout, and it misses repositories distributed as archives.
