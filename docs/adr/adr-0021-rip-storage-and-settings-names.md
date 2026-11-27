# ADR-0021: `.rip` Storage and `RIP_` Settings

**Status:** Adopted (amends 0010, 0018, 0019, 0020)

**Context:**

RIP began as "Local OpenClaw". When it was renamed, two internal names were kept so nothing would break: the storage directory `.local_openclaw` (in every project, and in the user's home folder for the API token, the integrity key and `models.json`) and the `LOC_` prefix of every environment variable. Both are visible to every user, in their repositories, their home folder and their `.env` files, and both name a project that no longer exists.

The storage directory holds state that must not be lost in a rename: the index, the editing snapshots that rollback depends on, the API token the app signs in with, and the integrity key that every signed proposal, snapshot and validation file is checked against (ADR-0019). A new key would make all of them fail verification.

**Decision:**

- The storage directory is `.rip`: `<project root>/.rip/` and `~/.rip/`.
- A directory still named `.local_openclaw` is renamed to `.rip` the first time RIP resolves the location (`project_storage_directory`, `user_storage_directory` in `app/core/storage/locations.py`), so the app, the MCP server and any other entry point see the same folder whichever runs first. If `.rip` already exists, the old directory is left alone. A `.local_openclaw` that is a symlink or junction is not moved; RIP refuses linked storage anyway.
- A rename that fails (typically: another process holds a file open on Windows) raises `StorageMigrationError` with what to do. RIP never carries on with a fresh, empty `.rip`.
- `.local_openclaw` stays protected and is never indexed, like `.rip`, so a leftover copy, or one that arrives with a cloned repository, is never read as repository content.
- Environment variables use the prefix `RIP_`. A setting given only under its former `LOC_` name, in the environment or in `.env`, is still used, with a warning naming the variable to rename; a `RIP_` value always wins.

**Consequences:**

Positive:
- The names users see match the product.
- Existing installs carry over with no action: index, snapshots, sign-in, integrity key, model settings and `.env` files all keep working.

Negative:
- The first start after upgrading renames folders the user did not touch. It is logged (`Moved … to …`).
- A repository that lists `.local_openclaw/` in its `.gitignore` needs `.rip/` added, or the moved index could be committed.
- The `LOC_` fallback and the legacy directory name are code to keep until the fallback is removed in a later major version.

**Alternatives Considered:**

- **Start fresh** (ignore old folders): simplest, but it loses rollback snapshots and invalidates every signed file, and forces a new sign-in. Rejected.
- **Read both names permanently** instead of moving: every path lookup would have to choose between two folders forever, and the two could diverge. Rejected.
- **Move once at application startup only**: the MCP server and scripts start differently, and a per-user file read before the move would create a new integrity key. Rejected in favor of moving wherever the location is resolved.
- **`.repository-intelligence-platform`**: already used by stale data from before Sprint 13 (ADR-0010), and long. `.rip` matches the name used everywhere else.
