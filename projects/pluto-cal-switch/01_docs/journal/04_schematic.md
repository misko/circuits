# journal — stage 4 (schematic authoring)

## 2026-07-28 09:05 — start
- did: read the binding canon (repo `CLAUDE.md`, `skills/pcb-design/SKILL.md`
  §4-6 + journal/beacon discipline, repo ADR-0001/0002,
  `references/tscircuit-folder.md`, all 8 project `contracts.md`), then the
  project's `BRIEF`/`ARCHITECTURE`/`DETAIL_DESIGN`, 16 ADRs, `02_parts/` (10
  dossiers) and `03_src/rules/` (5 files).
- result: the authoring target is FULLY PINNED by
  `03_src/rules/electrical_invariants.yaml` — 34 assertions name the exact
  refdes (`U_SW1/2`, `U_PAD_A1/A2A/A2B`, `R_DELTA1..3`, `C_DCBLK1/2`,
  `R_CTRL_PD1/2`, `R_HDR_S`, `J_SMA_RX1/RX2/TX`, `U_MCU`, `U_LDO`, `F1`) and
  the exact net names the netlist must carry. TWO INPUT DEFECTS FOUND BEFORE
  WRITING A LINE:
  (1) four RF net names that E-INV requires — `RX_ANT1_EXT`, `RX_ANT2_EXT`,
  `LOOP_ARM1_SW`, `LOOP_ARM2_SW` — appear in NO netclass in
  `03_src/rules/nets.yaml`, so they would fall to the 0.25 mm default class.
  0.25 mm on this stackup is ~55 ohm, not 50: a netclass omission is an
  IMPEDANCE defect on four of the board's RF segments, and no schematic gate
  can see it.
  (2) `02_parts/USBLC6-2SC6/part.yaml` and `02_parts/W25Q16JVSSIQ/part.yaml`
  carry `pins: {}` (declared OWED at stage 2). A schematic cannot be authored
  against an empty pin map without fabricating one.
- next: close the two OWED pin maps from primary datasheets (never from
  memory), correct `nets.yaml`, then author `03_tscircuit/src/pluto_cal_switch.tsx`
  against the generic backend. D7 (control arbitration) stays FLAGGED and
  firmware-only — the board is authored to `RF_CTRL = HEADER OR USB` + a 10 s
  watchdog, which consumes no hardware.

## 2026-07-28 09:50 — iterate 1 (parts IOUs come due)
- did: closed the two OWED pin maps from PRIMARY datasheets rather than from
  memory, and closed the deferred crystal sourcing item.
- result: **W25Q16JVSSIQ** — Winbond PDF fetched (Rev H, sha256 `81af3f69…`),
  vendored, pin map read from Figure 1a + the §3.3 table on printed p.5.
  **USBLC6-2SC6** — st.com refused an automated fetch (HTTP/2 `INTERNAL_ERROR`;
  the CCC mirror times out), so the byte-identical copy already in this repo
  (`usb-hub-3s-v3`, sha256 `8ba7ab4e…`) was used and its Figure 1 read. That
  read produced a fact the schematic would otherwise have got wrong: **pins 1
  and 6 carry the SAME label `I/O1`, and 3/4 the same `I/O2` — each pair is ONE
  internal node.** "Route in one pin and out the other" is a COPPER rule, not
  two nets; splitting `USB_DP` across pins 1 and 6 would have drawn a part that
  does not exist and made a shunt clamp read as a series element.
  **Crystal** — ADR-0012 resolution **(a)** taken: `ABM8-272-T3` (JLC
  `C20625731`, 17 567 in stock), CL 10 pF / ESR **50 Ω max** = exactly the
  RP2040 vendor's limits, and its own datasheet p.(2) states *"Crystal approved
  for use with Raspberry Pi's RP2040"*. So the reference circuit ships
  unmodified (2 × 15 pF derived, 1 kΩ damping) and **no start-up test at
  temperature extremes enters the release gate**, which resolution (b) would
  have required.
- next: correct the two stage-3 rules files, which authoring has just proved
  wrong in four places.

## 2026-07-28 10:10 — iterate 2 (the stage-3 rules were UNSATISFIABLE)
- did: reconciled `electrical_invariants.yaml` and `nets.yaml` against the
  circuit they describe. This was not tidying — the file could not be satisfied
  by any board.
- result: FOUR defects, each fixed at source:
  1. **`U_SW1.1` was asserted on `LOOP_ARM1`** while the ADR-0004 chain asserts
     `[LOOP_ARM1, <arm pad>, LOOP_ARM1_SW]`. Both cannot hold. Asserting RF2 on
     the splitter-side net demands a board where the arm pad is NOT between the
     splitter and the switch — precisely the topology ADR-0004 rejects on four
     independent counts. Corrected to `LOOP_ARM1_SW` (and channel 2).
  2. **Three names for two nodes on each antenna path.** `RX_ANT1_EXT` appeared
     in no netclass, no part.yaml and no architecture table, while `SW1_ANT`
     (which all three DO carry, and which the `U_SW1.3` assertion requires) had
     nothing connecting it to the DC block. Chain is now
     `[RX_ANT1, C_DCBLK1, SW1_ANT]`.
  3. **`LOOP_IN` and `LOOP_SPLIT` were two names for ONE node** — PAD_A1's
     output IS the delta's input vertex. `LOOP_IN` retired.
  4. **The pad chains still named ONE part each** (`U_PAD_A1`, `U_PAD_A2A/B`),
     true under the 30 dB build. A9 made PAD_A1 five chips and each arm pad two,
     and this file was never re-spec'd with the prose — so E-INV would have
     FAILED a correct netlist, the failure mode that teaches people to weaken
     gates. Now asserted CHIP BY CHIP, which is strictly stronger: it pins the
     ORDER too, and the FIRST chip being a YAT-10A+ is what DETAIL_DESIGN §4.3
     computes the +27 dBm ceiling against.
  Plus `[VBUS, F1, VBUS_F]` → `[VBUS, F1, FB1, VBUS_F]`: the old chain would
  have failed the correct board AND passed one with the ferrite missing.
  `nets.yaml` gained the nets those corrections imply — most importantly
  `PAD_A1_1..4` and the arm-pad internals, which are 50 Ω RF segments that
  would otherwise have routed at the 0.25 mm default class (~55 Ω). **A
  netclass omission is an impedance defect and no schematic gate can see it.**
- next: author the tsx.

## 2026-07-28 10:47 — iterate 3 (first build; the FPID count earned its keep)
- did: ran TSX-PRE, then the bridge.
- result: **TSX-PRE PASS 17/17**, ERC **0 errors**, but the converter reported
  **73 components (72 with FPID)**. The one miss was `F1`: the PPTC had no
  `02_parts` dossier at all. That is the entire value of the check — an
  unresolved FPID is invisible in ERC, in parity and in every render, and it
  hard-errors `generate_board` three stages later. Dossier written
  (`MINISMDC050F-2`, PDF adopted from `crow-recorder-central-v2` with the
  provenance stated); rebuild gives **73/73 with FPID**.
- next: the semantic battery.

## 2026-07-28 11:05 — iterate 4 (leg C found the catalog-drift class)
- did: ran `bom_source_check --circuit-only`.
- result: **FAIL (9)**, two distinct causes, both real:
  * the two C0G caps I had pinned (`0402CG###J500NT`, FH) are **undecodable by
    `mpn_capacitance`** — its regex needs the tolerance letter followed by a
    NON-digit, and in `…CG102J500NT` the `J` is followed by the voltage `500`.
    The vetted ledger already works around this three times with explicit
    `value:` entries, which is the evidence it is a DECODER gap, not a part
    problem. Repointed to Samsung `CL05C102JB5NNNC` / `CL05C150JB5NNNC`, which
    decode cleanly. Proposed decoder patch reported upstream.
  * **three passives tscircuit's parts engine had coded by itself** were
    unresolvable — and one of them, `C25890` for the 3.3 kΩ divider leg, read
    **stockCount 31**: one board's margin over a 20-board build. That is the
    cooksense v1.5 class exactly (auto-chosen `C25744` at stock 0). **Every
    passive LCSC code is now PINNED in the tsx**, ledger-vetted or dossiered.
- result after: **leg C PASS** — every coded R/C's catalog value == its tsx
  value prop.
- next: finish the battery and the docs.

## 2026-07-28 11:30 — finish (schematic gate)
- did: ran the full gate in order and fixed the stale O8 row.
- result, all MEASURED:
  | gate | id | result |
  |---|---|---|
  | `tsx_preflight.py` | TSX-PRE | **PASS 20/20** part.yaml (13 multi-pin) |
  | `kicad-cli sch erc --severity-all` | S1/S4 | **0 errors** / 542 warnings — 284 `endpoint_off_grid`, 185 `lib_symbol_issues`, 73 `footprint_link_issues`, all three parametric and baselined |
  | netlist parity vs sealed `04_kicad` | S2 | **N/A — no sealed board exists.** First schematic on this project; stated as N/A, not reported as a pass |
  | `net_label_survival.py` | S-NETMERGE | **PASS 48/48** |
  | `electrical_invariants.py` | E-INV | **OK 40/40** |
  | `--adr-coverage` | E-ADR | **FAIL 11/12 — the DECLARED O8b gap** |
  | `power_topology.py` | E-TOPO | **OK 1/1** rail, 1/1 converter |
  | `--margin` | E-MARGIN | **N-A** (no `load_uv_threshold`) |
  | `--off-control` | E-OFF | **N-A** (`source_type: usb`) |
  | `count_parity.py` | S-COUNT | **PASS 3/3** over **73 refdes** |
  | `bom_source_check --circuit-only` | M-BOM leg C | **PASS** |
  | `contracts_audit.py` | C-* | **243 files, 0 violations** |
  | `import_provenance_check.py` | M-IMPORT | **PASS 18/18** |
  | `policy_audit.py` | — | FAIL=2 HUMAN=6 N-A=23 **PASS=9** |
- **O8 is CLOSED and the row is corrected.** `power_topology.py:normalize_type()`
  gained `LINEAR` on 2026-07-27 and the module docstring names this board as the
  case that forced it. Verified here, measured: `required=BUCK, declared=LINEAR
  (ME6211C33M5G-N) -> step-down requirement MET by a linear pass element`, then
  **headroom 1034 mV vs dropout 120 mV** and **PD 202 mW vs 300 mW (67 %)** —
  both PASS. This board's LDO rail therefore grades as a **LINEAR
  implementation of a BUCK requirement**, fully graded, not waived.
- **Two gates are RED and NEITHER is waived, deliberately:**
  * **E-ADR 11/12** — O8b. `protection_adrs()` does not read `status:`, so it
    still demands invariants from ADR-0006 whose decision was REVERSED by
    ADR-0015. One line would make it green (retag the ADR) and that is exactly
    why it is left red.
  * **S-OCCL 25** — label-vs-label overlaps in the CONVERTER `.kicad_sch`, the
    machine artifact ADR-0002 says "need not be pretty". Three fleet boards
    carry a waiver for this class. **It is NOT written here**, because that
    waiver's evidence is a fresh-context RENDER REVIEW of the shipped tscircuit
    PDF, and no such review has happened at the schematic gate. A waiver copied
    without its evidence is an inherited defect (canon M4). It belongs at stage 7.
- S-VER went 11/13 → **13/13**, and the fix is worth recording because it was
  NOT a documentation improvement: `policy_audit` greps the raw file for the
  first literal `verified:` and reads 300 characters after it, so a
  cross-reference to `verified:` **inside a comment** shadows the real key and
  the gate grades comment text. Two files did that (one mine, one pre-existing
  on `KH-SMA-KE-Z`); both cross-references reworded. Proposed patch reported.
- Human schematic document rendered: `03_tscircuit/build/schematic.pdf`
  (88 KB, tscircuit's own render). It is genuinely wired, not a label blob.
  Its LAYOUT is tscircuit's auto-placement; S6 readability is a HUMAN grade at
  stage 7, and if it grades poorly the remedy is schematic placement hints in
  the TSX — never a KiCad re-render (that is polishing the machine artifact).
- next: **STOP. Schematic gate is the declared handoff boundary.** Stage 5 owns
  `03_src/lib/pluto_cal_switch.pretty/` (nine non-stock land patterns, none
  authored) and `03_src/floorplan.yaml` placement. Both `floorplan.yaml` and
  `route.yaml` were re-identified to this board at stage 4 — they were still
  the cook-loadcell template verbatim, and `rebuild_reuse.sh` derives the board
  NAME from `floorplan.yaml`, so a rebuild would have emitted
  `04_kicad/cook_loadcell.kicad_pcb` from this board's netlist.
