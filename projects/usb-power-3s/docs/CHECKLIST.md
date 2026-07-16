# Revision checklist

Every revision passes this before it is tagged. A revision that will be
RELEASED must additionally pass the release gate at the bottom.

## Gates (mechanical — no judgement)
- [ ] `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`
      → 0 violations, 0 unconnected, 0 missing footprints
- [ ] `src/audit_board.py` → PASS (placement/pad invariants)
- [ ] rules regenerate byte-identical from `src/rules/nets.yaml` (no hand-edits)
- [ ] BOM ↔ `parts/` parity (every used part has a datasheet + facts on file)
- [ ] netlist node-for-node parity after any schematic regeneration

## Judgement (a human or a fresh-context agent)
- [ ] every net >1A walked end-to-end for copper cross-section
- [ ] every 2-pad polarized part: pad 1's net checked against `parts/*/part.yaml`
      (diodes, LEDs, electrolytics, AND connectors — this is invisible to DRC)
- [ ] 3D/render review: connector bodies vs mounting holes, silk collisions
- [ ] `docs/CHANGELOG.md` entry written
- [ ] anything surprising captured as an ADR in `docs/decisions/`

## Release gate (only when ordering)
- [ ] working tree clean (`git_dirty: false`)
- [ ] tagged
- [ ] stock re-verified TODAY (not from cache)
- [ ] `releases/<ver>-<date>/` written with MANIFEST + verification evidence
- [ ] fab options in ORDER_README match the board (layers, via tier)
