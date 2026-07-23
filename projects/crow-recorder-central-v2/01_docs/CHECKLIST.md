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

- [ ] BRIEF.md: every acceptance criterion `met` (with evidence link) or `dropped` citing a user D#/Q# — never release with an `unmet` criterion
- [ ] BRIEF.md prompt hash verifies (`sed -n "/prompt-verbatim-begin/,/prompt-verbatim-end/p" 01_docs/BRIEF.md | sed "1d;\$d" | sha256sum`)

- [ ] JLC twin gate: `jlc_twin.py` exits 0 with the project adjudications file — zero unadjudicated MIRRORED/PAD-MISMATCH findings; twin_report.csv copied into the release verification/

- [ ] Fresh-context pin review: `pin_audit.py` dossiers generated; independent agents (no session context) reviewed every active part per `pin-review-protocol.md`; verdicts in the release verification/pin_review.md with ZERO unresolved FAILs
