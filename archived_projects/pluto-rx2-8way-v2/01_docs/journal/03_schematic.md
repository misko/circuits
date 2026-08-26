# journal: schematic (stage 4) — pluto-rx2-8way-v2

## 2026-07-30 10:30 — start
- did: authored `03_tscircuit/src/pluto_rx2_8way_v2.tsx` — the RF core and the
  control plane transcribed UNCHANGED from v1 (that is the experiment's control
  variable), the whole MCU subsystem replaced by one `U_MCU` module block, and
  the power tree reduced to four parts.
- result: `tsx_preflight` TSX-PRE PASS 5/5. First `gen_tscircuit.sh` run
  succeeded: **28 components, 27 with FPID, 130 pins, 35 wires, converter ERC
  0 errors / 182 warnings** (warnings baselined: lib_symbol_issues env note +
  named-NC isolated labels). The one component without an FPID is `U_MCU` —
  it has no `02_parts` dossier yet.
- next: run the cheap semantic battery.

## 2026-07-30 10:50 — iterate 1 (the battery, and two gates that found real defects)
- did: ran every schematic-stage gate UNPIPED and read the real exit codes.
- result:

  | gate | ID | result |
  |---|---|---|
  | `tsx_preflight` | TSX-PRE | PASS 5/5 |
  | `count_parity` | S-COUNT | PASS 28/28 over 2 source pairs |
  | `kicad-cli sch erc --severity-all` | — | **0 errors** |
  | `net_label_survival` | S-NETMERGE | PASS 23/23 labels survive |
  | `electrical_invariants` | E-INV | PASS 20/20 |
  | `electrical_invariants --adr-coverage` | E-ADR | PASS 1/1 |
  | `power_topology --margin` | E-MARGIN | PASS after a fix I caused |
  | `power_topology --off-control` | E-OFF | N-A (stated) |
  | `bom_source_check --circuit-only` | M-BOM leg C | PASS |
  | `net_reference_audit` | E-NETREF | PASS after a fix, 73/73 |
  | `adr_bound_provenance` | M-BOUND | PASS, 1 bound CITED |
  | `status_beacon_check` | M-BEACON | PASS 1/1 |
  | `power_topology` | E-TOPO | **BLOCKED** — see below |

  **Three findings worth keeping.**

  1. **E-INV rejected my first file outright** — I wrote `kind:` where the
     schema is `assert:`, and `series_chain` as a list of PARTS where it is an
     alternating list of NETS and PARTS. A LOAD ERROR, not a silent skip, which
     is the correct behaviour and is why the file is right now. Re-authored:
     20 invariants, `series_chain` used for the ferrite (`3V3_MOD -> FB_3V3 ->
     3V3`) and the pickoff (`RX1_MAIN -> R_T1 -> RX1_TAP_MID -> R_T2 ->
     RX1_TAP`), which is a STRONGER statement than the `net_has_part` I first
     reached for: it pins POSITION, and position is the failure.
  2. **E-MARGIN caught an error I authored.** I set `ir_budget_mohm: 100000`
     meaning "a generous ceiling". The field is the ACTUAL delivery resistance,
     so the gate read a 100 ohm path and failed the rail. Corrected to an
     itemised 90 mOhm declared as 100.
  3. **E-NETREF caught TWO GHOST net references, both riding in on dossiers I
     copied from v1** — `BLM21SP601SN1D` pointing at `VBUS_F` (a net that does
     not exist on a board with no VBUS) and `KH-SMA-KE-Z` pointing at
     `RF_ANT_LAUNCH` (a placeholder that is not a net on v1 either). Both are
     `keep_short` budgets, which is the exact class the canon records: a ghost
     does not fail loudly, it makes P-ADJ grade NOTHING while still counting as
     a declared budget. **This is the argument against blind dossier reuse,
     made by a gate rather than by me.** 63/65 -> 73/73.
- next: the `U_MCU` dossier — the last thing between here and the schematic
  gate, and the one artifact whose pin map must be READ off the vendor drawing
  rather than assumed.

## 2026-07-30 11:20 — iterate 2 (E-TOPO, and a decision about a part we do not own)
- did: ran E-TOPO.
- result: `E-TOPO LOAD ERROR: converter 'RP2040-Zero' not found in 02_parts`.
  Correct and expected — the dossier does not exist yet.
  **The decision behind that reference is the interesting part.** The rail's
  regulator is an RT9013-33 INSIDE a module we buy assembled. I could have
  shipped `rails: []` and collected a clean E-TOPO N-A — which is exactly the
  failure `power_topology.py`'s own docstring names on three fleet boards. The
  rail exists, it is linear, and its dropout and dissipation are citable, so it
  is declared. `dropout_mv`/`pdiss_max_mw` are PER-RAIL overrides rather than
  an RT9013 dossier, because we never order that regulator and giving it a
  dossier would invent a sourcing relationship that does not exist.
- next: E-TOPO closes when the module dossier lands with a `type:` that names
  its internal regulator class.

## 2026-07-30 12:05 — finish (SCHEMATIC GATE GREEN)
- did: authored `02_parts/RP2040-Zero/part.yaml` — the one part no board in this
  fleet has used — then rebuilt and ran the whole battery UNPIPED.
- result: **every gate exit 0.**

  | gate | ID | result |
  |---|---|---|
  | `kicad-cli sch erc --severity-all` | — | **0 errors**, 183 warnings (baselined) |
  | `tsx_preflight` | TSX-PRE | PASS 6/6 (3 multi-pin) |
  | `count_parity` | S-COUNT | PASS **28/28 over 3 source pairs** |
  | `net_label_survival` | S-NETMERGE | PASS 23/23 labels survive |
  | `electrical_invariants` | E-INV | PASS **20/20** |
  | `electrical_invariants --adr-coverage` | E-ADR | PASS 1/1 |
  | `power_topology` | E-TOPO | PASS 1/1 rails, 1/1 converters; PD 202 mW of 400 (50 %) |
  | `power_topology --margin` | E-MARGIN | PASS |
  | `power_topology --off-control` | E-OFF | N-A, STATED not inferred |
  | `bom_source_check --circuit-only` | M-BOM leg C | PASS |
  | `net_reference_audit` | E-NETREF | PASS **78/78, 0 ghost** |
  | `adr_bound_provenance` | M-BOUND | PASS, 1 bound **CITED** |
  | `status_beacon_check` | M-BEACON | PASS 1/1 |
  | `contracts_audit` | C-* | 0 violations |

  The converter now resolves **28 of 28** FPIDs (was 27, blocked on the module
  dossier). E-TOPO's resolution is the one worth re-reading: the rail's
  converter is a regulator inside a module we buy assembled, and it grades
  because the module dossier's `type:` names its internal regulator class. The
  alternative was a vacuous N-A.

- **PLANNED HANDOFF at the declared boundary.** Context past the threshold; the
  schematic gate is the scheduled split point and nothing is in flight.

### What the next agent must NOT inherit

1. **`03_src/floorplan.yaml` and `route.yaml` DO NOT EXIST, deliberately.** The
   seeded templates were deleted rather than half-filled. v2's star
   surroundings are NOT v1's — the MCU field collapsed from a QFN-56 plus
   flash, crystal, USB-C, two switches and ten decouplers to one 18 x 23.5 mm
   module — so a copied floorplan would be a copied answer to a different
   question. **The FIRST act of stage 5 is the OCTILINEAR FLOOR computed from
   v2's OWN pads** (`max(dx,dy) + 0.4142*min(dx,dy)`), plus min landable width
   per pad. Both are milliseconds of pad arithmetic; v1 found both by routing
   for hours. **Do not inherit v1's 1.4966 mm** — it is a property of v1's
   floorplan.
2. **`scoped_clearances` is empty on purpose** (`nets.yaml` says why at length).
   When a launch will not route, the ranked remedy is GRID, then clearance,
   then width — on v1 the real cause was the grid (`grid_step: 0.05` routed
   11/11 at the full 0.36 mm width; a neck-down was measured and REFUTED).
3. **The via-fence pitch is 1.35 mm, not v1's 1.37**, from v2's own derived
   eps_eff 3.3286. ADR-0003 carries the regenerating command.

### OWED, named rather than left silent

- **The footprint `pluto_rx2_8way_v2:RP2040_Zero_LCC23_18x23.5` is REFERENCED
  and DOES NOT EXIST.** It must be authored in `03_src/lib/` before
  `generate_board_generic` runs. Geometry is in the dossier: 23 pads, 2.54 mm,
  9 left / 5 bottom / 9 right, lands straddling the module edge, USB-C edge at
  the top carrying no pads.
- **The two Waveshare PDFs are not committed** into `02_parts/RP2040-Zero/`
  (`datasheet.local: OWED`). The project is not standalone for this part.
- **Whether the module's WS2812B power can be gated** — a schematic question,
  recorded in the dossier's notes and in ADR-0001's consequences.
- **`msl:` for the consigned module** — nobody publishes it; the mitigation is
  written, the number is not invented.
