# Revision checklist

Every revision passes this before it is tagged. A revision that will be
RELEASED must additionally pass the release gate at the bottom.

Run commands from the project root after setting
`CIRCUITS_ROOT="$(git rev-parse --show-toplevel)"`. A line described as a
conductor-owned predicate is checked by `03_src/rebuild_all.sh`; it is not an
invitation to invent a missing project-local script.

## Gates (mechanical — no judgement)
- [ ] `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity --exit-code-violations 04_kicad/<board>.kicad_pcb`
      → 0 violations, 0 unconnected, 0 missing footprints
- [ ] the conductor's placement/pad audit → PASS; if the project deliberately
      adds `03_src/audit_board.py`, that project-local check must pass too
- [ ] `python3 "$CIRCUITS_ROOT/skills/kicad-pcb/scripts/pad_separation.py" 04_kicad/<board>.kicad_pcb --project .` → P-PADSEP
      PASS: separate-footprint copper clears the fab-tier gap and paste does
      not intrude on foreign lands
- [ ] rules regenerate byte-identical from `03_src/rules/nets.yaml` (no hand-edits)
- [ ] BOM ↔ `02_parts/` parity (every used part has a datasheet + facts on file)
- [ ] `python3 "$CIRCUITS_ROOT/skills/kicad-pcb/scripts/module_first_check.py" .` → P-MOD PASS; every complex subsystem uses a
      proven module or carries an evidence-backed bare-IC exception ADR
- [ ] netlist node-for-node parity after any schematic regeneration

## Judgement (a human or a fresh-context agent)
- [ ] every net >1A walked end-to-end for copper cross-section
- [ ] every 2-pad polarized part: pad 1's net checked against `02_parts/*/part.yaml`
      (diodes, LEDs, electrolytics, AND connectors — this is invisible to DRC)
- [ ] 3D/render review: connector bodies vs mounting holes, silk collisions
- [ ] `01_docs/CHANGELOG.md` entry written
- [ ] anything surprising captured as an ADR in `01_docs/decisions/`
- [ ] `03_src/rules/rf.yaml` explicitly records RF applicability. If enabled:
      independent RF schematic review is SOUND before placement; independent
      exact-board RF PCB review is SOUND before layout seal

## Release-seal and publication gate

Any release, publication, ship/ready claim, or merge of material project
changes to the publication branch requires this section. An explicitly
unreviewed WIP may exist only on a clearly labelled branch/draft PR and is not
mergeable.
- [ ] release inputs clean (`git_dirty: false`, scope `projects/<board>/ + skills/` via `python3 "$CIRCUITS_ROOT/skills/kicad-pcb/scripts/release_git_dirty.py" "$PWD"` — a dirty sibling board does not block)
- [ ] tagged
- [ ] `07_releases/<ver>-<date>/` written with MANIFEST + verification evidence
- [ ] DRAFT declaration initialized before staging gates; final mutable staging
      has an `ACCEPTED`, still-current `release_rehearsal.py` receipt and seal
      admission outside the release directory
- [ ] fab options in ORDER_README match the board (layers, via tier)
- [ ] release freshness: `python3 "$CIRCUITS_ROOT/skills/jlcpcb-fab/scripts/release_freshness_check.py" 07_releases/<ver>-<date>` exits 0 —
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

- [ ] A-POP (population set DECLARED): `python3 "$CIRCUITS_ROOT/skills/jlcpcb-fab/scripts/assembly_coverage.py" 07_releases/<ver>-<date>` exits 0 —
      `{board footprints} − {CPL designators}` EQUALS `03_src/rules/assembly.yaml`'s
      `not_assembled:` set (declared `exempt_prefixes:` honoured), no blank-LCSC BOM row
      whose refs are on the CPL, every declared-unpopulated ref carries
      `exclude_from_pos_files`, and the MANIFEST `not_assembled:` line agrees with
      assembly.yaml (it is GENERATED from it). cooksense v1.1 sealed 13 blank-LCSC parts
      onto its CPL while the MANIFEST declared 12 of them unassembled, 2026-07-24
- [ ] A-CATALOG (advisory): `python3 "$CIRCUITS_ROOT/skills/jlcpcb-fab/scripts/jlc_stock_check.py" 06_build/fab/bom.csv --json 06_build/verification/stock_check.json` grades LCSC catalog
      identity/stock as a cheap negative filter. Its PASS is not JLCPCB PCBA
      availability and cannot produce `SOURCING: CLEAR`.
- [ ] sourcing evidence is current enough to state either `SOURCING: CLEAR` or
      an explicit `SOURCING: BLOCKED`; a blocked design-sound candidate may seal
      only as `DO-NOT-ORDER` and cannot imply availability.

- [ ] BRIEF.md: every acceptance criterion `met` (with evidence link) or `dropped` citing a user D#/Q# — never release with an `unmet` criterion
- [ ] BRIEF.md prompt hash verifies — note `head -c -1`: the FINAL NEWLINE is `sed`'s terminator, not part of the prompt, and the commission hashes it stripped (`sed -n "/prompt-verbatim-begin/,/prompt-verbatim-end/p" 01_docs/BRIEF.md | sed "1d;\$d" | head -c -1 | sha256sum`)

- [ ] JLC twin gate: `python3 "$CIRCUITS_ROOT/skills/jlcpcb-fab/scripts/jlc_twin.py" 04_kicad/<board>.kicad_pcb 06_build/fab/bom.csv 06_build/twin --cpl 06_build/fab/cpl.csv --assembly 03_src/rules/assembly.yaml --adjudications 03_src/rules/twin_adjudications.yaml` exits 0 when adjudications are owed — zero unadjudicated MIRRORED/PAD-MISMATCH findings; every orientation-declared connector has `P-MATE-REG-OK` in `connector_datum_receipt.json`; twin report and receipt copied into release verification/

- [ ] semantic M-BOM on the STAGED fab set: `python3 "$CIRCUITS_ROOT/skills/jlcpcb-fab/scripts/bom_source_check.py" 06_build/fab/bom.csv 03_tscircuit/build/circuit.json --parts 02_parts --board 04_kicad/<board>.kicad_pcb` exits 0 — per-refdes LCSC == source AND decoded MPN catalog value == BOM label (the R12/R30 wrong-part class, 2 sealed escapes 2026-07-23)

- [ ] `python3 "$CIRCUITS_ROOT/skills/kicad-pcb/scripts/policy_audit.py" .` → zero FAIL; waivers evidence-backed; HUMAN items carry the fresh-context reviewers' verdicts

- [ ] REVIEW LENSES scoped by release type (canon "Verification scoping"): INITIAL release of a material state = full battery (both red-team lenses + fresh pin review + render review); FIX-PASS release = diff-verified delta + targeted confirmation of each changed item + ONE integrated fresh-context lens — never the full battery on a fix-pass
- [ ] all reviews ran against the PRE-SEAL staging dir (a finding costs an edit,
      not a supersede); integrated review is accepted for its declared scope
      with ZERO open P0 before the seal commit
- [ ] when RF is enabled, exact-Gerber RF fab review reports
      `fab_package_verdict: READY`; prototype order is distinct from production,
      which remains HOLD until first-article VNA/TDR acceptance passes
- [ ] fresh-context pin review (per the scoping line above): `python3 "$CIRCUITS_ROOT/skills/kicad-pcb/scripts/pin_audit.py" 04_kicad/<board>.kicad_pcb 06_build/fab/bom.csv 02_parts 06_build/pin_audit` generates dossiers; independent agents (no session context) per `pin-review-protocol.md`; verdicts in verification/pin_review.md with ZERO unresolved FAILs

- [ ] seal follows the 2-commit procedure — 07_releases contract "Seal procedure (normative)": gates+reviews on staging → source commit S → MANIFEST stamped `git_sha: S` / `git_dirty: false` + M-REL/freshness re-run → seal commit adds ONLY the release dir (+ CHANGELOG, + SUPERSEDED.md on the predecessor)
- [ ] publication boundary: `python3 "$CIRCUITS_ROOT/skills/pcb-design/scripts/pcb_publication_gate.py" --base <publication-branch-base-sha> --head <candidate-head-sha>` exits 0; repository protection requires this check and a PR before material PCB changes can reach the publication branch
- [ ] docs-only supersede (when the release changes ONLY documentation): `python3 "$CIRCUITS_ROOT/skills/jlcpcb-fab/scripts/release_freshness_check.py" 07_releases/<ver>-<date> --docs-only-supersede 07_releases/<prior>` exits 0 — fab/source/3d byte-identical to the prior ASSERTED, ORDER_README + MANIFEST differ; never waive fab-identical files one-by-one
- [ ] a supersede that is NOT docs-only uses the mode matching the SHAPE of the fix, never a hand-written `--allow-identical` waiver set (usb-hub-3s-v3 v1.11 shipped seven, all machine-checkable): `--bom-only-supersede` (a row LEAVES, A-POP) · `--cpl-only-supersede` (a coordinate moves, A-POS) · `--legible-bom-supersede` (how the BOM READS, F-LEGIBLE) · `--sourcing-supersede` (WHICH PART is bought, M8) · `--value-change-supersede … --designators R4,R5` (a part's VALUE moves on already-placed parts: gerbers/drills identical after the plot-timestamp strip, CPL delta confined to `Val` cells, BOM delta confined to the DECLARED refs). Full statements: 07_releases contract

## Order admission (separate from release seal)

Required only before an actual fabrication/assembly order or a `READY-TO-ORDER`
claim. Passing this section does not alter the immutable release.

- [ ] stock re-verified today from live order-phase evidence, not cache
- [ ] J-PCBA-PRELAYOUT evidence was `AVAILABLE` before placement/routing and its
      procurement policy/cost bounds were accepted
- [ ] J-PCBA-FINAL reopens the exact sealed `fab/bom.csv`, every line is
      `ALLOCATED`, quantities/costs are accepted, and no substitution or stale
      receipt remains
- [ ] uploader selections and fab options are independently checked against the
      exact sealed release and recorded outside that immutable directory
