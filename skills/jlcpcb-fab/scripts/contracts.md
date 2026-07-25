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
  t1_bom_source.py, t1_release_freshness.py).
- `release_freshness_check.py <release_dir>` gates a seal: it FAILS when a
  generated fab/PDF artifact is sha256-identical to an earlier release of the
  same board (stale/inherited output), when the shipped
  `verification/policy_audit.md` result disagrees with the MANIFEST's claimed
  result (audit FAIL vs manifest 0-FAIL/PASS), or when the shipped
  `ORDER_README.md` still carries a draft/placeholder marker — the three
  defects usb-hub-3s-v3 v1.2 shipped DO-NOT-ORDER past every other gate
  (2026-07-23). Documented same-name-identical exceptions (with a reason) go
  in `<release_dir>/verification/freshness_exceptions.txt`.
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
