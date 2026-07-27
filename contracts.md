# contract: repo root

**Purpose** — the circuits repo: skills (the product), the boards they
produced, the canon that binds both, and the tests that keep every gate able
to fail. This file is the top of the governance chain: every folder in the
repo is governed by a `contracts.md` — its own, or the nearest ancestor's
via an explicit pattern (see the coverage rule below).

## The coverage rule (canon M7)

- A file is governed by the NEAREST `contracts.md` at or above it, and must
  match a pattern in that contract's `## Allowed` table.
- A subfolder listed as `dir/` must carry its OWN `contracts.md`; one listed
  as `dir/**` is covered wholesale by this contract (used for snapshots and
  fixture trees whose internals are data, not structure).
- Sealed folders (a project's `04_kicad/`, `07_releases/`) are covered by
  their parent's patterns — adding any file to them, including a contract,
  is forbidden.
- Machine-checked: `/usr/bin/python3 scripts/contracts_audit.py`
  (C-COV coverage, C-ALLOW patterns, C-ISO skills→projects isolation);
  run by `tests/run_tests.sh`. Every `## Allowed` first column is parsed —
  keep it a real pattern, not prose.

## Allowed

| Pattern | What |
|---|---|
| `README.md` | what this repo is |
| `CLAUDE.md` | binding agent instructions |
| `contracts.md` | this file |
| `.gitignore` | build/cache exclusions |
| `resume_state.md` | session-resume snapshot (superseded by commits as they land) |
| `skills/` | the product: pcb-design, kicad-pcb, jlcpcb-fab (own contract) |
| `docs/` | repo-level canon: ADRs + proof docs (own contract) |
| `examples/` | frozen evidence snapshots skills may cite (own contract) |
| `scripts/` | repo-level tooling, e.g. this audit (own contract) |
| `tests/` | the test suite (own contract) |
| `projects/` | ACTIVE boards, one folder each (own contract) |
| `archived_projects/` | completed/retired boards + frozen e2e regression fixtures (own contract) |
| `tscircuit_modules/` | shared tscircuit module library (own contract) |
| `spf/` | measured reference data about THIRD-PARTY hardware we must mate to, one folder per device (own contract) |

## Audit

- Structure: `scripts/contracts_audit.py` = 0 violations (tests enforce the
  non-projects scope; `--projects` grades the boards honestly).
- Content gates per subtree: see each folder's own contract.
