# Revision checklist

## Current unrouted-placement candidate — 2026-08-13

- [x] architecture ADRs accepted and exact part codes selected
- [x] exact-code manufacturer facts and dated two-source/JLC checks recorded
- [x] power, surge/capacitor, module-first, package-escape and source-rule gates pass
- [x] fail-safe RF truth table and framed dwell decoder contract are executable
- [x] JLC four-layer stackup and live-calculator RF source geometry retained: 0.295-mm width / 0.200-mm CPWG gap / 49.972 ohm
- [x] generated four-page schematic agrees 29/29 across source and exports
- [x] source pin-map 131/131, electrical invariants 32/32, ERC errors 0 and checkpoint 7/7 pass
- [x] exact-PDF topology/readability reviews and independent RF schematic review are SOUND
- [x] schematic pause completed before any PCB artifact was generated
- [x] D12 confirms all nine SMA connectors as Amphenol RF 901-143-6RFX female right-angle THT
- [x] exact Amphenol Rev-C drawing and no-form/fit-change PCN retained; stale drawing association and wrong ground-hole diameter corrected
- [x] exact Amphenol, pSemi and GCT footprints realized and compared with fresh exact-code JLC CAD
- [x] D14 90 x 65 mm outline, four M3 holes, three fiducials and cyclic
      non-crossing open-U RF edge order commissioned
- [x] all nine SMA mating-face datums and the USB PCB-edge datum measure exactly on the outline
- [x] generated board places 29/29 parts and nine selective U1 EP POFV vias; P-COLLIDE and P-PADSEP pass
- [x] placement DRC: 0 violations, 39 expected track-free unconnected items, 0 schematic-parity findings
- [x] physical pin-map gate passes 127 declared identities across 15 multi-pin refs
- [x] critical-pair gate explicitly grades 0 differential pairs with a single-ended RF reason
- [x] D15 compact top, oblique and edge placement review renders generated;
      the five-top/two-per-side SMA arrangement is visibly clear and U2, U3,
      U4, D1, F1 and every fitted R/C package are now visibly populated
- [x] `model_coverage_check.py` independently reopens the saved board and
      resolves 29/29 fitted bodies from project-owned paths
- [x] exact GCT USB, Samtec J11 and native exact-code SMA bodies resolve in the
      headless render; SMA legs align with the five-hole manufacturer pattern
      and all nine mating directions face outward at their board edges
- [x] R-PREFLIGHT source-known correction: common clearance 0.20 mm,
      ordinary via 0.45/0.20 mm (8:1 nominal aspect), and 0.58-mm legalizer
      pocket; 0 FAIL / 0 WARN and track-free board hash unchanged
- [x] D15 user approval binds compact connector access, RF planning corridors
      and operational silk to board SHA-256 `3fffbc690051998618880c63afcc559ddd37370e516f4869f670cf51288f2c42`
- [x] D16 route-wave/prep contract is complete; exact prep emits 23 RF
      segments with zero RF vias, six U1 ground-to-EP links and 22 ordinary
      rescue vias; all 32/32 SMD GND pads are served before KRT
- [ ] obtain fresh pin/layout/render and A-RENDER placement witnesses against
      the exact D15 board and D16 prepared-route contract
- [ ] sign a new canonical placement checkpoint only after the complete
      placement review; the superseded pre-D13 certificate is retained as
      `06_build/checkpoints/placement-pre-D13.json`

Every revision passes this before it is tagged. A revision that will be
RELEASED must additionally pass the release gate at the bottom.

## Gates (mechanical — no judgement)
- [ ] `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`
      → 0 violations, 0 unconnected, 0 missing footprints
- [x] shared `placement_gates.py` → PASS (P-OUT/P-CAP/P-BODYCLR)
- [x] `model_coverage_check.py 04_kicad/<board>.kicad_pcb` → P-MODEL
      PASS: 29/29 fitted footprints have renderer-resolvable bodies
- [x] `pad_separation.py 04_kicad/<board>.kicad_pcb --project .` → P-PADSEP
      PASS: separate-footprint copper clears the fab-tier gap and paste does
      not intrude on foreign lands
- [x] rules regenerate byte-identical from `03_src/rules/nets.yaml` (no hand-edits)
- [ ] BOM ↔ `02_parts/` parity (every used part has a datasheet + facts on file)
- [ ] `module_first_check.py .` → P-MOD PASS; every complex subsystem uses a
      proven module or carries an evidence-backed bare-IC exception ADR
- [x] placement-stage schematic parity → 0 findings

## Judgement (a human or a fresh-context agent)
- [ ] every net >1A walked end-to-end for copper cross-section
- [ ] every 2-pad polarized part: pad 1's net checked against `02_parts/*/part.yaml`
      (diodes, LEDs, electrolytics, AND connectors — this is invisible to DRC)
- [x] targeted 3D/render review: J11 body/keying and SMA body/leg/edge alignment
- [ ] complete placement review: RF spoke corridors, all body clearances and
      operational silk readability
- [ ] `01_docs/CHANGELOG.md` entry written
- [ ] anything surprising captured as an ADR in `01_docs/decisions/`
- [ ] `03_src/rules/rf.yaml` explicitly records RF applicability. If enabled:
      independent RF schematic review is SOUND before placement; independent
      exact-board RF PCB review is SOUND before layout seal
- [ ] order-stage JLC assembly DFM explicitly accepts the manufacturer-land
      SMA drills (1.50/1.70 mm) against JLC C429844 CAD (1.60/1.80 mm); do not
      silently replace the Amphenol Rev-C footprint

## Release and publication gate

Any release, publication, ship/ready claim, or merge of material project
changes to the publication branch requires this section. An explicitly
unreviewed WIP may exist only on a clearly labelled branch/draft PR and is not
mergeable.
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
- [ ] BRIEF.md prompt hash verifies — note `head -c -1`: the FINAL NEWLINE is `sed`'s terminator, not part of the prompt, and the commission hashes it stripped (`sed -n "/prompt-verbatim-begin/,/prompt-verbatim-end/p" 01_docs/BRIEF.md | sed "1d;\$d" | head -c -1 | sha256sum`)

- [ ] JLC twin gate: `jlc_twin.py` exits 0 with the project adjudications file — zero unadjudicated MIRRORED/PAD-MISMATCH findings; twin_report.csv copied into the release verification/

- [ ] semantic M-BOM on the STAGED fab set: `bom_source_check.py fab/bom.csv circuit.json --parts 02_parts` exits 0 — per-refdes LCSC == source AND decoded MPN catalog value == BOM label (the R12/R30 wrong-part class, 2 sealed escapes 2026-07-23)

- [ ] `policy_audit.py <project>` → zero FAIL; waivers evidence-backed; HUMAN items carry the fresh-context reviewers' verdicts

- [ ] REVIEW LENSES scoped by release type (canon "Verification scoping"): INITIAL release of a material state = full battery (both red-team lenses + fresh pin review + render review); FIX-PASS release = diff-verified delta + targeted confirmation of each changed item + ONE integrated fresh-context lens — never the full battery on a fix-pass
- [ ] all reviews ran against the PRE-SEAL staging dir (a finding costs an edit, not a supersede); red-team verdicts ORDER with ZERO open P0 BEFORE the seal commit
- [ ] when RF is enabled, exact-Gerber RF fab review reports
      `fab_package_verdict: READY`; prototype order is distinct from production,
      which remains HOLD until first-article VNA/TDR acceptance passes
- [ ] fresh-context pin review (per the scoping line above): `pin_audit.py` dossiers generated; independent agents (no session context) per `pin-review-protocol.md`; verdicts in verification/pin_review.md with ZERO unresolved FAILs

- [ ] seal follows the 2-commit procedure — 07_releases contract "Seal procedure (normative)": gates+reviews on staging → source commit S → MANIFEST stamped `git_sha: S` / `git_dirty: false` + M-REL/freshness re-run → seal commit adds ONLY the release dir (+ CHANGELOG, + SUPERSEDED.md on the predecessor)
- [ ] publication boundary: `python3 skills/pcb-design/scripts/pcb_publication_gate.py --base <publication-branch-base-sha> --head <candidate-head-sha>` exits 0; repository protection requires this check and a PR before material PCB changes can reach the publication branch
- [ ] docs-only supersede (when the release changes ONLY documentation): `release_freshness_check.py 07_releases/<ver>-<date> --docs-only-supersede 07_releases/<prior>` exits 0 — fab/source/3d byte-identical to the prior ASSERTED, ORDER_README + MANIFEST differ; never waive fab-identical files one-by-one
- [ ] a supersede that is NOT docs-only uses the mode matching the SHAPE of the fix, never a hand-written `--allow-identical` waiver set (usb-hub-3s-v3 v1.11 shipped seven, all machine-checkable): `--bom-only-supersede` (a row LEAVES, A-POP) · `--cpl-only-supersede` (a coordinate moves, A-POS) · `--legible-bom-supersede` (how the BOM READS, F-LEGIBLE) · `--sourcing-supersede` (WHICH PART is bought, M8) · `--value-change-supersede … --designators R4,R5` (a part's VALUE moves on already-placed parts: gerbers/drills identical after the plot-timestamp strip, CPL delta confined to `Val` cells, BOM delta confined to the DECLARED refs). Full statements: 07_releases contract
