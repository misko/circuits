# journal — stage 4, schematic authoring (03_tscircuit)

## 2026-07-28 17:05 — start
- did: intake read — CLAUDE.md, pcb-design SKILL 4-6, repo ADR-0002,
  tscircuit-folder.md, BRIEF/ARCHITECTURE/DETAIL_DESIGN, the seven ADRs,
  02_parts/README.md, all three `03_src/rules/`, `floorplan.yaml`,
  `route.yaml`, both rebuild drivers, every `contracts.md`, and the 13
  part dossiers (pin maps read, not skimmed).
- result: baseline re-measured before touching anything —
  `policy_audit` **FAIL=1 HUMAN=6 N-A=26 PASS=7**, the single FAIL being
  `E-INV LOAD ERROR: no exported netlist found`, i.e. STRUCTURAL. Three
  findings that are NOT structural and must be fixed at this stage:
  1. **`03_src/route.yaml` IS A TEMPLATE LEFTOVER.** Its header still reads
     "SCHEMA EXAMPLE ... cook-loadcell route + stitch" and its
     `project.name` is `cook_loadcell`, `board:` is
     `04_kicad/cook_loadcell.kicad_pcb`. `rebuild_reuse.sh` derives BOARD
     from `floorplan.yaml` (correct, `pluto_rx2_8way`) but every
     `route_and_stitch_generic.py` step reads route.yaml — so the routing
     stage would have written a DIFFERENT board file than the one the
     rules/DRC gate reads. This is the sibling-board defect the stage-4
     brief warned about, present verbatim.
  2. **`03_src/rebuild_all.sh` is the unedited template** — `BOARD=power3s`,
     `TSX=power3s`, and it calls `03_src/audit_board.py` unconditionally
     (a file this board does not and should not have; `rebuild_reuse.sh`
     guards the same call with `-f`).
  3. **02_parts is short by two parts the design NAMES.** `floorplan.yaml`
     seeds `LED_PWR`, `LED_ST` and `SW_BOOT`; `nets.yaml` declares nets
     `LED_PWR`, `LED_STAT`, `BOOTSEL_N`, `RUN_N`; `DETAIL_DESIGN.md` sec 5
     derives `R_LED1`/`R_LED2` = 680 ohm at Vf 2.0 V. There is no dossier
     for the LED and none for the button, so both would resolve to an
     EMPTY FPID (converter) and hard-error `generate_board` at stage 5.
     The 02_parts README's claim "one dossier per part the design NAMES"
     is measured against `DETAIL_DESIGN.md` sec 8's value index, which
     lists the BALLASTS and not the indicators.
- next: D-BACK to stage 2 for those two commodity parts (delegated, runs in
  parallel), then the stage-4 work proper. The one deliberately-open design
  decision (`U_ESD` pin 5 node) gets ADR-0008 before the TSX is written,
  because `electrical_invariants.yaml` has to assert whichever arm wins.

## 2026-07-28 18:20 — iterate 1
- did: ADR-0008 written and its three invariants emitted; `03_src/route.yaml`
  REPLACED (it was cook-loadcell's schema example verbatim, `project.name:
  cook_loadcell`); `rebuild_all.sh` knobs set + `audit_board.py` guarded;
  `floorplan.yaml` seeds revised (U_ESD moved to the D+/D- escape, 24 new
  seeds, U_MCU rotated 180 so the QSPI spur source faces AWAY from the receive
  fan); the TSX authored; manifest / net_aliases / parity_padmap / package.json
  / README / GENERATE written.
- result: **TSX-PRE PASS 13/13** (8 multi-pin) BEFORE the first build.
  `tsci build` OK; converter **64 components (60 with FPID), 269 pins, 197
  wires**; **ERC 0 errors / 430 warnings**, all three in the documented
  parametric classes (endpoint_off_grid 207, lib_symbol_issues 163,
  footprint_link_issues 60). Battery: **S-COUNT 3/3 over 64 refdes**,
  **S-NETMERGE 44/44 labels survive (74 nets)**, **E-INV 24/24**,
  **E-ADR 5/5**, **E-TOPO 1/1**, E-MARGIN N-A, E-OFF N-A.
  **`policy_audit` FAIL=0 HUMAN=6 N-A=26 PASS=8** — the structural E-INV FAIL
  is gone, which was the point of this stage.
- next: two reds remain. (a) 4 of 64 components have an EMPTY FPID — the LED
  and the pushbutton, whose dossiers are the delegated stage-2 back-fill.
  (b) `bom_source_check --circuit-only` exits 1.

## 2026-07-28 18:35 — iterate 2 (the finding that was worth the detour)
- did: chased `bom_source_check --circuit-only`'s 10 UNVERIFIABLE-VALUE
  findings instead of waiving them, and queried the JLC catalog directly for
  each code.
- result: **tscircuit's parts engine had silently assigned an LCSC code to
  ALL 38 un-coded passives.** Two consequences, and the second is a real
  defect, not a process nit:
  1. `tsci build` is NON-DETERMINISTIC, so those BOM lines were a BUILD-TIME
     choice rather than a design decision — a board that cannot reproduce its
     own BOM from source is a canon-M3 violation nothing was checking.
  2. **Its 47 ohm pick was C25118 (0402WGF470JTCE) at STOCK 10, EXTENDED** —
     for the part this board uses FOUR times and whose value ADR-0005
     machine-asserts because it is what holds PE42482A-X's 3.6 V digital
     absolute maximum. MEASURED against the JLC API 2026-07-28. Replaced with
     **C137864 (RC0402JR-0747RL, 47R +/-5%) at stock 86,783**. Its 680 ohm
     pick (C25130) was likewise unvetted where the repo's own ledger already
     carries C137948; replaced.
  Every commodity passive is now PINNED in the TSX with a code read from the
  JLC catalog (stock + library tier + describe string), not inferred.
  `bom_source_check --circuit-only` 10 -> **8**, one class, three codes:
  C137864 (47R x4), C1548 (15pF C0G x2), C274349 (27.4R x2).
- next: those three codes have no home. The gate's own remedy is to append
  them to `skills/jlcpcb-fab/references/lcsc_passives_ledger.yaml`, which this
  agent may not edit — so they get `02_parts` dossiers instead, which is the
  contract-correct home anyway for a passive whose value is machine-asserted
  (47R), datasheet-mandated at 1% E96 (27.4R), or whose DIELECTRIC is part of
  the spec (15 pF C0G — "15 pF 0402" is orderable as X7R).

## 2026-07-28 19:05 — finish
- did: the delegated stage-2 back-fill landed (`KT-0603R` C2286 and
  `TS-1187A-B-A-B` C318884, both **JLC BASE** with 7.6 M / 1.36 M assembly
  stock and both with the manufacturer document committed — the board goes from
  11-of-12 extended lines to 11-of-14). Two things it found changed MY authoring
  rather than just its own files:
  1. **The switch has FOUR feet and TWO pad NUMBERS.** KiCad's
     `SW_Push_1P1T_XKB_TS-1187A` gives pad "1" to two feet and pad "2" to the
     other two. The TSX had authored pins 1/2/3/4; pins 3 and 4 would have had
     no pad on the real footprint, and NOTHING at this gate can see that — ERC
     is happy (both pins have nets), S-COUNT is happy (the refdes SET is
     unchanged), the netlist is self-consistent. It surfaces only as a
     `--schematic-parity` diff after the board is generated. Fixed to a 2-node
     model. Its consequence at stage 6 is now a CHECKLIST line: those duplicate
     pads are NOT jumpers, so each node's two feet need ~6 mm of copper, four
     traces across the two buttons, and the netlist cannot ask for them.
  2. **The LED vendor drawing numbers its terminals the OPPOSITE way to KiCad**
     (the '+' is printed at terminal 1; KiCad's pad 1 is the CATHODE). A
     faithful transcription of the vendor figure would have reversed both
     indicators against the board's own silk, and a reversed LED at V_R 5 V on a
     3.3 V rail is DARK AND UNDAMAGED — the board arrives, works, and has two
     dead lights nobody can explain. The dossier had WITHHELD its
     `pad1_net_polarity` assert because the answer depended on which side the
     ballast sat, which was still open. It is now fixed (ballast on the ANODE
     side, so pad 1 is on GND on both), so the assert is ENABLED here rather
     than left owed.
- result: **THE SCHEMATIC GATE, every number measured, in order** —
  `TSX-PRE` **PASS 15/15** (8 multi-pin) · `kicad-cli sch erc --severity-all`
  **0 ERRORS** / 425 warnings (endpoint_off_grid 200, lib_symbol_issues 161,
  footprint_link_issues 64 — the three documented parametric classes, nothing
  else) · netlist parity **N/A, no sealed `04_kicad` board exists yet** ·
  `net_label_survival` **PASS 44/44 labels survive, 74 nets** ·
  `electrical_invariants` **E-INV 24/24** · `--adr-coverage` **E-ADR 5/5** ·
  `power_topology` **E-TOPO 1/1**, **E-MARGIN N-A**, **E-OFF N-A** ·
  `count_parity` **S-COUNT 3/3 source pairs over 64 refdes** ·
  `bom_source_check --circuit-only` **FAIL(8)** — the one red, see below ·
  `policy_audit` **FAIL=0 HUMAN=6 N-A=26 PASS=8** (was FAIL=1 for two stages;
  the structural E-INV is green, which is what this stage existed to do) ·
  `contracts_audit --projects` **0 violations in this board's scope** ·
  `status_beacon_check` **M-BEACON PASS 1/1**.
  Converter: **64 components, 64 with FPID**, 265 pins, 188 wires, 100
  tscircuit labels + 3 safety labels, 13 junctions.
  Independent spot-check straight off the netlist (canon M1 — a different
  method from the gate that already passed): A6=B6=USB_DP and A7=B7=USB_DM;
  SBU1/SBU2 no-connect with no trace; SH+A1+A12+B1+B12=GND; D_TVS.1(K)=VBUS_F;
  F_IN VBUS->VBUS_F; FB_IN VBUS_F->VBUS_LDO with U_LDO.VIN on VBUS_LDO;
  U_ESD.5=VBUS_F, .2=GND, C_ESD.1=VBUS_F; VREG_VOUT(45)=DVDD(23)=DVDD(50)=
  DVDD_1V1; U_MCU EP(57)=GND; U_SW LS(1)=GND, NC(20)=GND, EP(25)=GND,
  RF1(24)=ANT1, RF8(19)=RX1_TAP, RFC(22)=RX2_OUT; the pickoff chain
  RX1_MAIN->RX1_TAP_MID->RX1_TAP with J_ANT8 and J_RX1 on the SAME node.
- next: **STOP — this is a declared handoff boundary.** ONE red carries
  forward and it is not fixable from inside this project: `bom_source_check
  --circuit-only` exits 1 with 8 `UNVERIFIABLE-VALUE` findings on three LCSC
  codes the fleet's vetted passives ledger does not carry (C137864 47R x4,
  C1548 15pF C0G x2, C274349 27.4R x2). The gate's OWN remedy is to append them
  to `skills/jlcpcb-fab/references/lcsc_passives_ledger.yaml`, and this stage
  was scoped not to edit `skills/`. All three were catalog-read on 2026-07-28
  and the exact rows are in the report; a `02_parts` dossier would also close
  it but would be a SECOND home for a fact the ledger already owns.
