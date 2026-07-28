# Revision checklist

Every revision passes this before it is tagged. A revision that will be
RELEASED must additionally pass the release gate at the bottom.

## Gates (mechanical — no judgement)
- [ ] `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`
      → 0 violations, 0 unconnected, 0 missing footprints
- [ ] `03_src/audit_board.py` → PASS (placement/pad invariants)
- [ ] rules regenerate byte-identical from `03_src/rules/nets.yaml` (no hand-edits)
- [ ] BOM ↔ `02_parts/` parity (every used part has a datasheet + facts on file)
- [ ] netlist node-for-node parity after any schematic regeneration

## Judgement (a human or a fresh-context agent)
- [ ] every net >1A walked end-to-end for copper cross-section
- [ ] every 2-pad polarized part: pad 1's net checked against `02_parts/*/part.yaml`
      (diodes, LEDs, electrolytics, AND connectors — this is invisible to DRC)
- [ ] 3D/render review: connector bodies vs mounting holes, silk collisions
- [ ] `01_docs/CHANGELOG.md` entry written
- [ ] anything surprising captured as an ADR in `01_docs/decisions/`

## Release gate (only when ordering)
- [ ] release inputs clean (`git_dirty: false`, scope `projects/<board>/ + skills/` via `release_git_dirty.py <board>` — a dirty sibling board does not block)
- [ ] tagged
- [ ] stock re-verified TODAY (not from cache)
- [ ] `07_releases/<ver>-<date>/` written with MANIFEST + verification evidence
- [ ] fab options in ORDER_README match the board (layers, via tier)
- [ ] release freshness: `release_freshness_check.py 07_releases/<ver>-<date>` exits 0 —
      no pdf/ or fab/ artifact sha256-identical to an earlier release (a changed board
      must not ship a prior release's drawings), shipped policy_audit.md agrees with the
      MANIFEST's claimed result, no draft/placeholder markers in ORDER_README
      (usb-hub-3s-v3 v1.2 sealed with v1.1's PDFs + a FAIL audit under a 0-FAIL manifest,
      2026-07-23 — caught by external review, not by any gate)
- [ ] manifest-consistency (M-CONS): `release_freshness_check.py` exit 0 on the staged
      dir AFTER the MANIFEST stamp — every count the MANIFEST's gate summary states
      matches the shipped evidence (ERC errors/warnings vs policy_audit S-ERC and
      erc.json; bom_source_check line count vs fab/bom.csv rows), and evidence paths
      name the sealed dir, not a staging path (crow-recorder-central-v2 v1.0 sealed
      with three prose/evidence disagreements, 2026-07-23). The gate's version key
      handles board-prefixed dir names (`<board>-v1.x-<date>`) — before 2026-07-24
      those silently skipped the stale-artifact check

- [ ] A-POP (population set DECLARED): `assembly_coverage.py 07_releases/<ver>-<date>` exits 0 —
      `{board footprints} − {CPL designators}` EQUALS `03_src/rules/assembly.yaml`'s
      `not_assembled:` set (declared `exempt_prefixes:` honoured), no blank-LCSC BOM row
      whose refs are on the CPL, every declared-unpopulated ref carries
      `exclude_from_pos_files`, and the MANIFEST `not_assembled:` line agrees with
      assembly.yaml (it is GENERATED from it). cooksense v1.1 sealed 13 blank-LCSC parts
      onto its CPL while the MANIFEST declared 12 of them unassembled, 2026-07-24
- [ ] A-STOCK (seal only against evidence that PASSES): `release_freshness_check.py 07_releases/<ver>-<date>`
      exits 0 including check (e) — the shipped stock evidence carries a PARSEABLE PASS
      verdict and every coded, placed line clears `qty x build_quantity` or names an
      `assembly.yaml` `sourcing_plan:` entry with `measured_stock` + `measured_on`. Ship
      `verification/stock_check.json` (`jlc_stock_check.py --json`): a missing or
      unparseable verdict is a FAIL, not a skip (five sealed releases shipped a `FAIL:`
      last line, one with the board's own CPU at stock 0)

- [ ] BRIEF.md: every acceptance criterion `met` (with evidence link) or `dropped` citing a user D#/Q# — never release with an `unmet` criterion
- [ ] BRIEF.md prompt hash verifies (`sed -n "/prompt-verbatim-begin/,/prompt-verbatim-end/p" 01_docs/BRIEF.md | sed "1d;\$d" | sha256sum`)

- [ ] JLC twin gate: `jlc_twin.py` exits 0 with the project adjudications file — zero unadjudicated MIRRORED/PAD-MISMATCH findings; twin_report.csv copied into the release verification/

- [ ] semantic M-BOM on the STAGED fab set: `bom_source_check.py fab/bom.csv circuit.json --parts 02_parts` exits 0 — per-refdes LCSC == source AND decoded MPN catalog value == BOM label (the R12/R30 wrong-part class, 2 sealed escapes 2026-07-23)

- [ ] `policy_audit.py <project>` → zero FAIL; waivers evidence-backed; HUMAN items carry the fresh-context reviewers' verdicts

- [ ] REVIEW LENSES scoped by release type (canon "Verification scoping"): INITIAL release of a material state = full battery (both red-team lenses + fresh pin review + render review); FIX-PASS release = diff-verified delta + targeted confirmation of each changed item + ONE integrated fresh-context lens — never the full battery on a fix-pass
- [ ] all reviews ran against the PRE-SEAL staging dir (a finding costs an edit, not a supersede); red-team verdicts ORDER with ZERO open P0 BEFORE the seal commit
- [ ] fresh-context pin review (per the scoping line above): `pin_audit.py` dossiers generated; independent agents (no session context) per `pin-review-protocol.md`; verdicts in verification/pin_review.md with ZERO unresolved FAILs

- [ ] seal follows the 2-commit procedure — 07_releases contract "Seal procedure (normative)": gates+reviews on staging → source commit S → MANIFEST stamped `git_sha: S` / `git_dirty: false` + M-REL/freshness re-run → seal commit adds ONLY the release dir (+ CHANGELOG, + SUPERSEDED.md on the predecessor)
- [ ] docs-only supersede (when the release changes ONLY documentation): `release_freshness_check.py 07_releases/<ver>-<date> --docs-only-supersede 07_releases/<prior>` exits 0 — fab/source/3d byte-identical to the prior ASSERTED, ORDER_README + MANIFEST differ; never waive fab-identical files one-by-one
- [ ] a supersede that is NOT docs-only uses the mode matching the SHAPE of the fix, never a hand-written `--allow-identical` waiver set (usb-hub-3s-v3 v1.11 shipped seven, all machine-checkable): `--bom-only-supersede` (a row LEAVES, A-POP) · `--cpl-only-supersede` (a coordinate moves, A-POS) · `--legible-bom-supersede` (how the BOM READS, F-LEGIBLE) · `--sourcing-supersede` (WHICH PART is bought, M8) · `--value-change-supersede … --designators R4,R5` (a part's VALUE moves on already-placed parts: gerbers/drills identical after the plot-timestamp strip, CPL delta confined to `Val` cells, BOM delta confined to the DECLARED refs). Full statements: 07_releases contract
