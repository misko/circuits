# Revision checklist

Every revision passes this before it is tagged. A revision that will be
RELEASED must additionally pass the release gate at the bottom.

## Gates (mechanical — no judgement)
- [x] `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`
      → 0 violations, 0 unconnected, 0 missing footprints
- [x] generated placement/pad/electrical audits → PASS
- [x] `pad_separation.py 04_kicad/<board>.kicad_pcb --project .` → P-PADSEP
      PASS: separate-footprint copper clears the fab-tier gap and paste does
      not intrude on foreign lands
- [x] rules regenerate byte-identical from `03_src/rules/nets.yaml` (no hand-edits)
- [x] BOM ↔ `02_parts/` parity (every used part has a datasheet + facts on file)
- [x] `module_first_check.py .` → P-MOD PASS; every complex subsystem uses a
      proven module or carries an evidence-backed bare-IC exception ADR
- [x] netlist node-for-node parity after any schematic regeneration

## Judgement (a human or a fresh-context agent)
- [x] every net >1A walked end-to-end for copper cross-section
- [x] every 2-pad polarized part: pad 1's net checked against `02_parts/*/part.yaml`
      (diodes, LEDs, electrolytics, AND connectors — this is invisible to DRC)
- [x] 3D/render review: connector bodies vs mounting holes, silk collisions
- [x] `01_docs/CHANGELOG.md` entry written
- [x] anything surprising captured as an ADR in `01_docs/decisions/`
- [x] `03_src/rules/rf.yaml` explicitly records RF applicability. If enabled:
      independent RF schematic review is SOUND before placement; independent
      exact-board RF PCB review is SOUND before layout seal

## Release and publication gate

Any release, publication, ship/ready claim, or merge of material project
changes to the publication branch requires this section. An explicitly
unreviewed WIP may exist only on a clearly labelled branch/draft PR and is not
mergeable.
- [x] release inputs clean (`git_dirty: false`, scope `projects/<board>/ + skills/` via `release_git_dirty.py <board>` — a dirty sibling board does not block)
- [x] tagged
- [x] stock re-verified TODAY (not from cache)
- [x] `07_releases/<ver>-<date>/` written with MANIFEST + verification evidence
- [x] fab options in ORDER_README match the board (layers, via tier)
- [x] release design freshness: `release_freshness_check.py 07_releases/<ver>-<date> --claim design` exits 0; `--claim both` remains an order-time gate while an explicit external uploader hold is active —
      no pdf/ or fab/ artifact sha256-identical to an earlier release (a changed board
      must not ship a prior release's drawings), shipped policy_audit.md agrees with the
      MANIFEST's claimed result, no draft/placeholder markers in ORDER_README
      (usb-hub-3s-v3 v1.2 sealed with v1.1's PDFs + a FAIL audit under a 0-FAIL manifest,
      2026-07-23 — caught by external review, not by any gate)
- [x] manifest-consistency (M-CONS): `release_freshness_check.py` exit 0 on the staged
      dir AFTER the MANIFEST stamp — every count the MANIFEST's gate summary states
      matches the shipped evidence (ERC errors/warnings vs policy_audit S-ERC and
      erc.json; bom_source_check line count vs fab/bom.csv rows), and evidence paths
      name the sealed dir, not a staging path (crow-recorder-central-v2 v1.0 sealed
      with three prose/evidence disagreements, 2026-07-23). The gate's version key
      handles board-prefixed dir names (`<board>-v1.x-<date>`) — before 2026-07-24
      those silently skipped the stale-artifact check

- [x] A-POP (population set DECLARED): `assembly_coverage.py 07_releases/<ver>-<date>` exits 0 —
      `{board footprints} − {CPL designators}` EQUALS `03_src/rules/assembly.yaml`'s
      `not_assembled:` set (declared `exempt_prefixes:` honoured), no blank-LCSC BOM row
      whose refs are on the CPL, every declared-unpopulated ref carries
      `exclude_from_pos_files`, and the MANIFEST `not_assembled:` line agrees with
      assembly.yaml (it is GENERATED from it). cooksense v1.1 sealed 13 blank-LCSC parts
      onto its CPL while the MANIFEST declared 12 of them unassembled, 2026-07-24
- [x] A-STOCK (seal only against evidence that PASSES): `release_freshness_check.py 07_releases/<ver>-<date>`
      exits 0 including check (e) — the shipped stock evidence carries a PARSEABLE PASS
      verdict and every coded, placed line clears `qty x build_quantity` or names an
      `assembly.yaml` `sourcing_plan:` entry with `measured_stock` + `measured_on`. Ship
      `verification/stock_check.json` (`jlc_stock_check.py --json`): a missing or
      unparseable verdict is a FAIL, not a skip (five sealed releases shipped a `FAIL:`
      last line, one with the board's own CPU at stock 0)

- [x] BRIEF.md: every acceptance criterion `met` (with evidence link) or `dropped` citing a user D#/Q# — never release with an `unmet` criterion
- [x] BRIEF.md prompt hash verifies — note `head -c -1`: the FINAL NEWLINE is `sed`'s terminator, not part of the prompt, and the commission hashes it stripped (`sed -n "/prompt-verbatim-begin/,/prompt-verbatim-end/p" 01_docs/BRIEF.md | sed "1d;\$d" | head -c -1 | sha256sum`)

- [x] JLC twin gate: `jlc_twin.py` exits 0 with the project adjudications file — zero unadjudicated MIRRORED/PAD-MISMATCH findings; twin_report.csv copied into the release verification/

- [x] semantic M-BOM on the STAGED fab set: `bom_source_check.py fab/bom.csv circuit.json --parts 02_parts` exits 0 — per-refdes LCSC == source AND decoded MPN catalog value == BOM label (the R12/R30 wrong-part class, 2 sealed escapes 2026-07-23)

- [x] `policy_audit.py <project>` → zero FAIL; waivers evidence-backed; HUMAN items carry the fresh-context reviewers' verdicts

- [x] REVIEW LENSES scoped by release type (canon "Verification scoping"): INITIAL release of a material state = full battery (both red-team lenses + fresh pin review + render review); FIX-PASS release = diff-verified delta + targeted confirmation of each changed item + ONE integrated fresh-context lens — never the full battery on a fix-pass
- [x] all reviews ran against the PRE-SEAL staging dir; red-team design verdicts are SOUND with ZERO open P0, and the separate order verdict honestly retains the external uploader/first-article hold
- [x] N/A — the RF module is explicitly disabled for this USB fixture; USB
      differential-pair routing, impedance confirmation and first-article link/
      eye/throughput qualification are governed by the USB SI contract instead
- [x] fresh-context pin review (per the scoping line above): `pin_audit.py` dossiers generated; independent agents (no session context) per `pin-review-protocol.md`; verdicts in verification/pin_review.md with ZERO unresolved FAILs

- [x] seal follows the 2-commit procedure — 07_releases contract "Seal procedure (normative)": gates+reviews on staging → source commit S → MANIFEST stamped `git_sha: S` / `git_dirty: false` + M-REL/freshness re-run → seal commit adds ONLY the release dir (+ CHANGELOG, + SUPERSEDED.md on the predecessor)
- [ ] publication boundary: `python3 skills/pcb-design/scripts/pcb_publication_gate.py --base <publication-branch-base-sha> --head <candidate-head-sha>` exits 0; repository protection requires this check and a PR before material PCB changes can reach the publication branch
- [x] N/A for this initial release — docs-only supersede mode was not used
- [x] N/A for this initial release — no non-docs supersede mode was used
