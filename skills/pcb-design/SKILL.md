---
name: pcb-design
description: "Full PCB design pipeline entry point: takes a design brief and drives it from commission to an orderable, verified JLCPCB release (/pcb-design <the board I would like to design...>). Use when the user wants a new circuit board designed end-to-end."
---

# /pcb-design — brief to orderable release

The argument is the user's design brief, VERBATIM. You will drive the full
pipeline in `~/gits/circuits/projects/<name>/`. Load the `kicad-pcb` and
`jlcpcb-fab` skills NOW — they hold the routing/fab mechanics and the
hard-won traps; this skill is the orchestration layer only.

## 0. Commission (before any engineering)

- Pick a short kebab-case project name from the brief.
- `mkdir -p ~/gits/circuits/projects/<name>` with the numbered stage
  folders `01_docs 02_parts 03_src 04_kicad 05_firmware 06_build
  07_releases`. Copy each folder's `contracts.md` from
  `projects/usb-power-3s/` (the canonical contract set) — read them; they
  are binding.
- Write `01_docs/BRIEF.md`: the user's prompt VERBATIM between
  `<!-- prompt-verbatim-begin/end -->` markers with its sha256; then the
  parsed requirements (P#), your clarifying questions (Q#) and the user's
  answers (A#), decisions (D#) appended over time. Only user utterances
  may relax a requirement.
- If the brief is underspecified on something that changes the design
  (voltage/current envelope, port counts, protection expectations, size,
  budget/tier), ASK the user now — 2-4 questions max — and record Q#/A#.
  If the user is absent, make the conservative choice, record it as D#
  with reasoning, and flag it in the final report.

## 1-3. Design docs, parts, rules (order matters)

1. `01_docs/ARCHITECTURE.md` (topology + power math) and
   `DETAIL_DESIGN.md` (every component value derived, with margins);
   one ADR per real decision in `01_docs/decisions/` — alternatives,
   rejection reasons, live stock data for part choices.
   **Mandatory ADR: battery/input protection** (reverse polarity, fuse,
   UVLO/over-discharge, OV, TVS clamp vs downstream ratings) — a
   clean-room run once shipped a LiPo board with zero UVLO because no
   stage forced the question.
2. `02_parts/<MPN>/part.yaml` per part: pin map read from the datasheet
   FIGURE (not assumed), `verified:` note naming figure+page, LCSC code +
   alternates + stock. The PDF set MUST include the package/land-pattern
   drawing, not just electricals.
3. `03_src/rules/nets.yaml` + `generate_rules.py` BEFORE any layout.

## 4-6. Generate, place, route — all regenerable from 03_src

Build `03_src/` generators + `rebuild_all.sh` (set -euo pipefail) in the
canonical order. **Schematic authoring — tscircuit/TSX is THE standard,
schwriter2 is FALLBACK-ONLY (ADR-0002 Phases D+E, migration COMPLETE):**
(1) the go-forward path is **tscircuit/TSX**. The whole board rebuilds with ONE
command — `scripts/tsx_to_board.sh <project>` (Phase E): `tsci build` → converter
`.kicad_sch` → placement → generate_rules → KRT (reuses the promoted route chain)
→ stitch_and_fill → generate_rules LAST → DRC 0/0/0. For schematic-only render
use `gen_tscircuit.sh <project>` (default = the BRIDGE ONLY: circuit.json,
schematic.svg/.pdf, converter `.kicad_sch`, ERC + netlist-parity gate; pass
`--study` for tscircuit's own PCB/gerber/3D second-opinion render, which is never
a fab source). The converter (`circuit_json_to_kicad_sch.py`, default `--mode
layout` = WIRED, retires S6) folds canonical nets + FPIDs from `02_parts` in with
no per-board adapter — see `kicad-pcb/references/tscircuit-folder.md`. Author each
specialty part with `supplierPartNumbers={{jlcpcb:["C…"]}}` so its FPID resolves,
and add a `net_aliases.txt` line for any leading-digit rail (`12V`→`N12V`).
**Two audiences (ADR-0002 Phase A):** the human schematic document = tscircuit's
OWN render (`build/schematic.pdf`, shipped in the release); the converter
`.kicad_sch` is the machine artifact only (ERC/netlist/parity, need not be pretty).
Compose proven subcircuits from the module library (`tscircuit_modules/`) where one
exists (ADR-0002 Phase C). (2) **schwriter2 declarations** are RETAINED as the
FALLBACK for footprints tscircuit can't yet express (structure-only;
path/subcircuit/net-object API — canon S-DSL); not deleted, still valid, but no
longer the co-standard. EITHER path feeds the SAME downstream: generate_schematic
(or the converter) with no_connect flags for every sanctioned float; wire the
story-critical paths per canon S6 →
**ERC gate** (`kicad-cli sch erc --severity-all` = 0 errors) →
netlist-parity gate → generate_board — placement is hand-coded OR
**placement-as-code** (`circuit_json_to_kicad_pcb.py` lands parts at the TSX
`pcbX/pcbY`; ADR-0002 Phase B — authored coords only, NEVER tscircuit auto-place,
then legalize) → audit gate (polarity,
proximity, plane-clean, refdes-on-silk) → generate_rules BEFORE route-prep
(the route-input .kicad_pro must carry the netclasses — canon R1) → KRT
routing chain (fanout-first, track-free board, import once; promote the
final chain file to 03_src/route/ and commit it — canon M3) →
stitch_and_fill (pours + thermal vias) → **generate_rules LAST** (pcbnew
saves clobber netclasses) → DRC gate:
`kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`
must report **0 violations / 0 unconnected / 0 parity** at FULL severity.
Never hand-edit `04_kicad/`; fix the generator and rerun. Commit at each
green gate. Silkscreen carries BOTH the functional labels (terminal words,
pin map) AND every reference designator (F.SilkS, visible, de-collided) —
the audit's I8 check enforces the refdes rule; F.Fab keeps a copy for the
assembly drawing.

## 7. Verify — independent eyes, then release

Run ALL of these; each compares against a reference the design didn't
produce (checker and checked must not share a method):

- `bom_seed.py`: 22/22-style unambiguous LCSC mapping; hand-solder THT
  lines deliberately uncoded and listed.
- `jlc_stock_check.py`: every coded line in stock >= 5x need.
- `jlc_twin.py BOARD bom.csv 06_build/twin --adjudications
  03_src/rules/twin_adjudications.yaml --also <REF=LCSC,...>` (include
  hand-solder parts with known codes). Gate: exit 0 — zero unadjudicated
  MIRRORED / PAD-MISMATCH / PAD-GEOM; act on MODEL-SELF and
  POLARITY-CHECK findings; adjudications are evidence-backed per the
  jlcpcb-fab skill (pixel measurements, board_dx/board_dy nudges, NUDGE
  echo verified).
- Fresh-context PIN REVIEW: `pin_audit.py` dossiers -> new agents per
  part group following `kicad-pcb/references/pin-review-protocol.md`.
  Zero FAILs to proceed.
- Fresh-context RENDER REVIEW: a new agent reviews the twin renders +
  PDFs with no design context; triage every finding (fix or ADR-documented
  disposition).
- `export_pdfs.sh`: pcb_layers / assembly PDFs, visually verified via PNG
  export. For tscircuit-authored boards the **schematic PDF = tscircuit's own
  render** (`03_tscircuit/build/schematic.pdf`), NOT a KiCad re-render (ADR-0002
  Phase A) — ship it as `pdf/schematic.pdf`.

- POLICY AUDIT (final gate): `/usr/bin/python3
  <kicad-pcb skill>/scripts/policy_audit.py <project>` — zero FAIL; any
  WAIVED entry evidence-backed in `03_src/rules/policy_waivers.yaml`; the
  HUMAN-graded items (schematic readability S6, decoupling S7, design-math
  S5) carry verdicts from the fresh-context reviews. Ship
  `06_build/policy_audit.md` in the release's verification/.

Then cut `07_releases/v1.0-<date>/` per the release contract: gerber zip,
bom.csv, cpl.csv, pdf/, verification/ (all evidence incl. 6 twin renders),
ORDER_README (JLC options, rotation-preview checklist, hand-solder list,
first-power ritual), sha256'd MANIFEST from a CLEAN tree (`git_dirty:
false`). Releases are immutable; fixes mean a new release, a fix-claim
needs its falsifiable measurement in verification/, and superseded
releases get a SUPERSEDED.md pointer.

## Report back

Final message to the user: decisions summary (with the protection ADR
called out), gate scoreboard, release path + git sha, open items for
order day (stock re-check, JLC preview rotation confirmations), and any
D# assumptions made in their absence.
