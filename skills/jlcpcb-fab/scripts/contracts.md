# contract: skills/jlcpcb-fab/scripts/

**Purpose** — executable order/verification tooling (gerber export, BOM/CPL,
stock, twin).

## Allowed

| Pattern | What |
|---|---|
| `*.py` | tools — network access mocked in tests via `$EASYEDA2KICAD` seam |
| `*.sh` | drivers |
| `*.csv` | data tables: `jlc_rotations_db.csv` (footprint-NAME CPL rotation corrections) and `jlc_lcsc_rotations.csv` (per-LCSC overrides, `LCSC,rotation,evidence`) |
| `contracts.md` | this file |

## Audit

- Checkers: clean + known-bad tests in `tests/` (t1_jlc_twin.py,
  t1_bom_source.py, t1_release_freshness.py, t1_assembly_gates.py).
- **The ASSEMBLY family (canon A-POP / A-STOCK) — PCBA is the deliverable,
  so the order artifacts are GATED, not just produced.**
  - `assembly_coverage.py TARGET` (A-POP), plain python3, takes a sealed
    release dir OR a project dir. It requires
    `{board footprints} − {CPL designators}` to EQUAL `assembly.yaml`'s
    `not_assembled:` set (honouring declared `exempt_prefixes:`), and FAILs
    a blank-LCSC BOM row whose refs are on the CPL, a declared-unpopulated
    ref still placed or missing `exclude_from_pos_files`, a board part
    carrying that attribute yet placed, a schema entry without
    reason/evidence/disposition, a consigned part listed as not_assembled,
    and a MANIFEST `not_assembled:` line that is absent or disagrees with
    `assembly.yaml`. Prints the per-side placement histogram.
    Its board reader (`read_footprints`) parses the `.kicad_pcb`
    s-expression DIRECTLY — no pcbnew — so the checker shares no oracle with
    `export_jlc_package.py`, which reads the same facts through the pcbnew
    API (canon M1). The two are cross-checked on a real sealed board
    (195/195 footprints agree on refdes/footprint/orientation/layer/pad
    count/attrs, 0 mismatches) and that agreement is pinned as a test, so the
    independent parser cannot rot into a second, quieter bug.
  - A-STOCK lives in `release_freshness_check.py` check (e), always on —
    see below.
  - `jlc_twin.py --assembly 03_src/rules/assembly.yaml` reads the coded
    not-assembled/consigned REF=LCSC pairs from the ONE declared home
    (`--also` still works for an ad-hoc probe).
- **A-ROT (every CPL rotation is MEASURED) is HELD, not shipped
  (2026-07-25).** `jlc_twin.xform()` — the helper that computes `jlc_offset`
  — uses the opposite handedness to `local_to_board()`, verified against
  pcbnew over 72 pads (local_to_board exact to 0.000000 mm; xform off by up
  to 23.93 mm, wrong at every 90/270 part, sign-invariant and therefore
  invisible at 0/180). Six `jlc_lcsc_rotations.csv` rows had been populated
  from it and were all 180 deg wrong. A rotation gate ranking that table as
  AUTHORITY would have frozen the negation. Rebuild it against the BOARD +
  JLC's cached model with a pcbnew-verified operator, never from
  `jlc_offset` (canon M1).
- `release_freshness_check.py <release_dir>` gates a seal: it FAILS when a
  generated fab/PDF artifact is sha256-identical to an earlier release of the
  same board (stale/inherited output), when the shipped
  `verification/policy_audit.md` result disagrees with the MANIFEST's claimed
  result (audit FAIL vs manifest 0-FAIL/PASS), or when the shipped
  `ORDER_README.md` still carries a draft/placeholder marker — the three
  defects usb-hub-3s-v3 v1.2 shipped DO-NOT-ORDER past every other gate
  (2026-07-23). Documented same-name-identical exceptions (with a reason) go
  in `<release_dir>/verification/freshness_exceptions.txt`.
- `release_freshness_check.py` also runs **A-STOCK (check (e), always on)**:
  every coded BOM line with a CPL row is graded OFFLINE against the stock
  evidence the release ships — `stock >= qty x build_quantity`, or an
  `assembly.yaml` `sourcing_plan:` entry with `measured_stock` +
  `measured_on`. A MISSING OR UNPARSEABLE VERDICT IS A FAIL, NOT A SKIP
  (cooksense v1.1 ships a raw `--out` CSV report as `stock_check.txt` with
  ZERO verdict lines; crow-recorder-central-v2 v1.0-v1.3 each end in `FAIL:`
  with their own CPU at `LOW_STOCK(0)`, and nothing read it). Live re-query
  stays in the opt-in `--net` tier — a gate that needs the network is a gate
  that gets skipped. `jlc_stock_check.py --json OUT` writes the one
  machine-readable sidecar with an EXPLICIT verdict; ship it as
  `verification/stock_check.json`.
- `release_freshness_check.py <release_dir> --docs-only-supersede <prior>`
  is the mode for a DOCUMENTATION-ONLY supersede release (usb-hub-3s-v3
  v1.4, 2026-07-23), which intentionally ships fab bytes identical to its
  predecessor: declared identity is ASSERTED, not flagged — fab/, source/,
  3d/ MUST be byte-identical to the prior release (any differing, missing,
  or added file FAILS: a "docs-only" release that changes fab is lying),
  identical pdf/ is allowed, the order README + MANIFEST MUST differ from
  the prior's, and the audit==manifest + no-draft-marker checks still run.
  Default mode is byte-for-byte unchanged.
- Fetch/stock classifiers must treat any UNRECOGNIZED failure as a blocking
  failure, never as an affirmative disposition (the NO-CAD incident,
  2026-07-20).
- CPL rotation is resolved by `jlc_rotation_resolve.py` (shared, no-pcbnew, so
  unit-testable): a PER-LCSC override (`jlc_lcsc_rotations.csv`) WINS over the
  footprint-NAME DB (`jlc_rotations_db.csv`). JLC's zero-orientation is a
  per-part fact — two parts sharing a footprint NAME can need different offsets
  (measured 2026-07-24: C79924 vs C7719, both `SOT-23-5`, need 180 vs 90; the
  name key cannot hold both, and a broad `^SOT-23,180` name rule would mis-set
  every OTHER part sharing that name). Populate the per-LCSC table ONLY with
  twin-MEASURED exact-fits (cite the fit in the `evidence` column); a guessed
  row silently overrides the name DB fleet-wide. `t1_jlc_twin.py` unit-tests
  the resolver (per-LCSC-wins + name-DB fallback for un-listed parts + a
  RED-verify that reverting to name-only returns the wrong rotation).
- The fab BOM's LCSC code is the SOURCE's per-refdes code
  (`circuit.json supplier_part_numbers`), never a value+footprint match:
  `export_jlc_package.py` groups by (LCSC, footprint) so two distinct codes
  on one value+footprint stay on separate rows, and `bom_source_check.py`
  (canon M6 / policy_audit M-BOM) FAILS a merged/substituted/missing/
  dropped-vendored BOM (usb-hub-3s-v3 v1.1 shipped 25V caps for 50V,
  2026-07-23).
- Code identity is not enough: `bom_source_check.py` also runs a SEMANTIC
  value check (leg C) — for every R/C row it resolves the catalog value in
  order BOM MPN column -> vendored `02_parts/<MPN>/part.yaml` dir name ->
  vetted `references/lcsc_passives_ledger.yaml` (catalog-verified ONCE per
  code), decodes/compares OFFLINE, FAILING a VALUE-MISMATCH and FLAGGING a
  row no source resolves as UNVERIFIABLE-VALUE (never a silent pass). The
  ledger is load-bearing: real fab BOMs ship a BLANK MPN column and basic
  passives have no part.yaml, so without it the sealed usb-hub-3s-v3 v1.2
  R12 defect (C2933210 = 3.74k labeled 4.12k, 2026-07-23) is invisible —
  measured. A live catalog fetch, when in-env, is a stronger add-on but the
  offline check stands alone.
