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
- Generated current `04_kicad/` snapshots are mutable only through
  regeneration/promotion and follow their project contract. Immutable PCB and
  enclosure release entries are governed by their release-stream contract;
  adding or editing payload after seal is forbidden.
- `.secrets/` is deliberately absent from the table: it is gitignored, so no
  file in it is in the audit's universe (`git ls-files`) and none may ever be.
  It is the ONE home for API keys — mode 600, one `<service>.env` per service,
  read at runtime by name and never hardcoded into a skill.
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
| `.github/` | repository automation and publication checks (own contract) |
| `improvements.md` | repository-wide pipeline/process improvement ledger harvested from project stages | entries remain visible until completed or rejected with evidence |
| `skills/` | the product: pcb-design, kicad-pcb, jlcpcb-fab, pcb-enclosure, shopping-list (own contract) |
| `docs/` | repo-level canon: ADRs + proof docs (own contract) |
| `examples/` | frozen evidence snapshots skills may cite (own contract) |
| `scripts/` | repo-level tooling, e.g. this audit (own contract) |
| `tests/` | the test suite (own contract) |
| `projects/` | ACTIVE boards, one folder each (own contract) |
| `archived_projects/` | completed/retired boards + frozen e2e regression fixtures (own contract) |
| `external_hardware/` | measured reference data about THIRD-PARTY hardware we must mate to, one folder per device (own contract) |

## Audit

- Structure: `scripts/contracts_audit.py` = 0 violations (tests enforce the
  non-projects scope; `--projects` grades the boards honestly).
- Content gates per subtree: see each folder's own contract.
