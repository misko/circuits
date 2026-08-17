# Temporary-worktree recovery, 2026-08-15

This untracked directory preserves the only non-Git state judged worth retaining
before the repository's authoritative `main` checkout was moved out of `/tmp`.

- `pi-usb-main-ignored-build/` is the ignored `06_build/` state from the clean
  `/tmp/circuits-pi-usb-release` main worktree at commit `a8659927`.
- `pluto-v5-v0.1.0-preseal/` is the untracked, superseded Pluto v5 `v0.1.0`
  release snapshot from detached commit `c9a59c15`. It differs from the sealed
  and committed `v0.1.0` release and is retained only as recovery evidence.

The current releases, source files, skills, and improvement ledger are already
tracked on `main`. Downloaded toolchains, package installs, caches, and scratch
renders were intentionally not retained because they are reproducible and are
not release authority.

The rejected Pluto firmware experiment remains recoverable separately from the
branch `codex/pluto-rx2-8way-v5` and its named stash; it was not copied here.
