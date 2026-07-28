# journal — verify (cooksense, MAIN board)

## 2026-07-27 18:39 — handoff

- did: RETIRED the v1.3-era STATUS-cooksense beacon frame into its proper
  append-only home. The beacon is the OVERWRITTEN live head (01_docs contract,
  canon M9/M-BEACON); it had grown 20 non-schema narrative keys — `export:`,
  `twin:`, `ropent_fix:`, `mrepro_3run:`, `do_not:` and the rest — because this
  stage had NO journal file, so the live head was doing the history's job. It
  is verbatim below; the beacon itself now carries the seven contract fields
  and names the LIVE release, cooksense-v1.4-2026-07-26.
- result: MEASURED — `status_beacon_check.py` (canon M-BEACON) graded the
  retired frame 2 findings: M-BEACON-FIELD (missing `step:`, `op_pid:`,
  `updated:`) and M-BEACON-AGE (no parseable clock at all, so it could not be
  shown fresher than the cooksense-v1.4-2026-07-26 seal). Its last write was
  274ae62, and the frame still read `stage: routed` while two further releases
  (v1.3, v1.4) had sealed above it.
- next: this file is where verify-stage entries go from here — do not put them
  back in the beacon. Nothing in the retired frame is re-asserted as current;
  it is preserved as a record of what was true when it was written, and every
  number in it belongs to the v1.3 board revision (which is what v1.4 ships:
  v1.4 is a DOCUMENTATION-ONLY supersede, board and fab payload byte-identical).
  One live gap it names and nothing else does: **there is no CHANGELOG entry
  for cooksense-v1.4** — the entries run v1.0, v1.1, interposer-v1.0, v1.3,
  interposer-v1.1. M5/M-REL requires an entry naming every release directory.

### The retired frame, verbatim (git 274ae62, `01_docs/STATUS-cooksense.md`)

```
board: cooksense
stage: routed
state: P0 CLOSED (R_OPENT -> C37825 62k, approved) — DRC 0/0/0, export clean, M-REPRO GREEN on 3 runs; pre-seal doc/lens battery still owed
git_sha: dddc1a1
measure: **DRC GATE GREEN.** `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` on the committed 04_kicad/cooksense.kicad_pcb = **0 violations / 0 unconnected / 0 schematic parity**. Placement gate P-COLLIDE **0 pad shorts / 0 anchored courtyard overlaps** (795 copper pads, 81 anchored parts). Route: KRT race 3/3 chains CLEAN (0 unc / 0 viol), winner c0/r9 promoted to 03_src/cooksense/route/final_chain.kicad_pcb. Stitch `gate: clean`, seed_stubs 58 pins / 0 refused, GND pad rescue 166/167, 3V3 76/76. E-INV **83/83**. Board 222 parts + 4 holes, 3902 tracks / 1045 vias.
p0_closed: **P0-A CLOSED — J_ESTOPLOOP + J_CONTACTOR merged into ONE 4-pole isolated block J_ISOLOOP (KF350-3.5-4P, C42400616)**, per the user's decision. ADR-0013 carries it. Both connectors only ever carried isolated-domain nets, so the merge is isolation-NEUTRAL-OR-BETTER: one isolated body with ONE 2.0mm moat and ONE pour keepout instead of two adjacent bodies each needing their own. Implemented in SOURCE (canon M3): 03_tscircuit tsx + manifest -> netlist -> floorplan/route.yaml -> generate_board.
east_column: THE FOUR ANCHORS ARE SOLVED, NOT CHOSEN. Available H4-courtyard-bottom 54.547 -> south edge 102.000; consumed 3x10.790 GH courtyards - 0.545 + 2.000 moat + 12.700 J_ISOLOOP pad column + 0.300 edge = 101.372 => **0.628mm of aggregate slack for FIVE margins at once**. MEASURED at J_MODE 60.00 (UNMOVED) / J_ESTOP 70.88 / J_DOOR 81.76 (all rot90 x197) / J_ISOLOOP [195.30,95.00,90]: H4 gap 0.058, J_MODE-J_ESTOP 0.090, J_ESTOP-J_DOOR 0.090, J_DOOR-J_ISOLOOP 0.500, J_ISOLOOP-J_RH_EXHAUST 0.160, **ISO->SELV copper 2.126 (+0.126 on the rule; binding pair J_ISOLOOP.4[CONTACTOR_E] <-> J_DOOR.MP[GND], still 2.126 on the ROUTED board)**, J_ISOLOOP.1 copper to south edge 0.650, block body south face flush at 102.000. THE COORDINATOR'S "~1.8mm of genuine slack" DOES NOT REPRODUCE — 0.628mm is the number, and only with the pad change below.
pad_deviation: KF350-3.5-4P uses a **2.20mm pad, not the 2P's 2.60** (annular ring 0.50mm vs JLC's 0.15mm THT floor). At 2.60 the SAME solve lands at ~0.05mm on all five margins at once; the predecessor solve that kept 2.60 reached 0.028mm aggregate and STILL measured 1.702mm on the moat (P-COLLIDE caught its butted J_ESTOP/J_DOOR courtyards; an independent ISO<->SELV pad scan caught the moat). Also raises pole-to-pole copper gap 0.90 -> 1.30mm on a 30V block. Recorded in the part.yaml `verified:` block and the footprint `descr`.
iso_moat: WRITTEN. `iso_moat_block` [192.20,86.65,200.10,102.10] + `iso_moat_opto` [186.70,85.80,192.80,94.20], `deny: [pours]` on all four layers, each the 2.0mm outward offset of the isolated copper. The block rect's north edge 86.65 is the tight one — exactly J_ISOLOOP.4's pad top minus 2.0mm, while J_DOOR's south GND shell tab ends at 86.61, so the pour still reaches and bonds that tab with 0.04mm to spare. route.yaml carries the MIRROR on User.4 (U4-a [194.00,83.60,200.10,88.85], U4-b [186.00,92.40,194.40,102.10]): the first route LEFT the moat and kicad-cli returned 2 `opto_isolation_2mm` violations at **1.9078mm** (CONTACTOR_C F.Cu vs J_DOOR.MP), because the User.2 rects keep SELV copper OUT and nothing kept the ISOLATED copper IN. Both DRU isolation rules confirmed to survive `apply_drc_policy` running LAST.
h2h_floor: **route.yaml `hole_to_hole.min_gap` 0.5 -> 0.25, with evidence.** 0.5 was the TEMPLATE default carried in uncommented; nets.yaml declares `fab_tier: jlc_4layer_advanced`, fab_tiers.yaml gives that tier 0.25, generate_rules writes 0.25 into the .kicad_pro BEFORE routing (canon R1) and that is what the DRC gate judges, and `via_site_ok` (6fcf647) checks the board's own m_HoleToHoleMin. MEASURED: the v1.1 SEALED board has 29 via pairs < 0.50mm (0 < 0.25, tightest 0.350); the v1.2 promoted chain has 82 (0 < 0.25, tightest 0.297) — **0.5 was never satisfied on this board.** It only became visible when 6fcf647 correctly made the repair pass's silent give-up fatal. The two other ADVANCED fleet boards declare 0.25; usb-hub-3s-v3 declares 0.5 and says STANDARD on the same line.
trapped_pads: FOUR plane pads needed the C_TCPA/R_SHIELD three-part treatment (explicit anchor + User.2 reservation at +-0.55mm + deterministic seed_stub via-in-pad), and the SECOND round is the lesson: fixing C_SWB.2 + R_DECDPD.2 moved the problem to C_DECUEN.1 + C_ULNA.2. Root cause is PLACEMENT (C_SWB.2's 0603 GND pad has THREE B.Cu analog nets crossing beneath it, so no via site exists anywhere on the pad). Found with a GND union-find over FILLED copper (626 items -> 5 clusters), which NAMES the stranded pad where kicad's ratsnest only says "zone <-> zone". Round two REUSED the promoted chain instead of re-racing: with the copper frozen there is no new realization to strand a new pad.
mrepro: **GREEN on the metric v1.2 used, and the caveat is measured.** Two consecutive full rebuilds from the frozen chain: footprints (226) hash 27df27524eef7f8b IDENTICAL, tracks (3902) hash b35fccb5d57160ae IDENTICAL, vias (1045) hash e0c93ceecd0ac5cb IDENTICAL. Zone FILL is not byte-stable: island counts identical (3V3/In2 1, GND/F.Cu 114, GND/In1 19, GND/B.Cu 2) and areas agree to 1 part in 4e6 (8434.792 vs 8434.791 mm2), but 28-93 tessellation vertices out of 15k-30k differ per zone. ROOT CAUSE MEASURED: `generate_board` is deterministic in every VALUE (footprint hash identical across two isolated runs) but KiCad serialises footprints in **UUID order** and the generator mints a fresh random UUID per run, so the zone filler processes copper in a different order and Clipper tessellates a few boundaries differently. Not an electrical difference — DRC is 0/0/0 on both builds. A true byte-identical M-REPRO needs deterministic UUIDs in generate_board_generic.py (fleet-wide change, NOT done here).
assembly: **16 refs not_assembled** (was 13). +J_ISOLOOP (`not_in_catalog`; stockCount 0 on all three KF350-4P lines 2026-07-25, control C474892 = 9987 the same minute). +J_LOADCELL and J_PI (`process_incompatible` — MEASURED 5/5 and 40/40 plated DRILLED pads with F.Paste on NONE, on a service=standard sides=[top] order; v1.0 AND v1.1 both shipped them as CPL placement rows — the same defect the relays and J_TC were caught for, never applied to the rest of the THT population). All three carry `exclude_from_pos_files`.
einv: **83/83** (was 79). +J_ISOLOOP.3 -> CONTACTOR_LOOP, .4 -> CONTACTOR_E, and the v1.3 top gate item is CLOSED: `part_value` asserts R_WDPETPD = 1k and R_OS = 510k. RED-VERIFIED — expecting 100k exits 1 and prints "R_WDPETPD is 1kOhm (1k), invariant requires 100k".
silk: the ISO warning has NO site at the block, MEASURED: a full scan for a free F.SilkS box against pads (+0.16), existing silk (+0.08) and every COURTYARD (silk under a body is silk nobody reads) puts the nearest visible site for "ISOLATED 30V" 41.9mm away and for a 7-character "ISO 30V" 33.6mm away — J_RH_AMBIENT/J_RH_EXHAUST/J_ISOLOOP refdes already tile the only clear band. Two captions placed at the block first were pushed clean OFF the south edge by the nudge search (y104.19-106.31), which is worse than nothing. One caption now sits in the north safety stack beside the ADR-0012 enclosure lines and names the corner: "J_ISOLOOP (SE CORNER) = ISOLATED 30V CONTACTOR LOOP -- NOT SELV" at (62.0,15.4), site measured free. Pole legend -> ORDER_README + ADR-0013. refdes on silk 216/222, crowded captions back to the pre-existing 2.
next: NOTHING below this line has been run yet. 1) ORDER_README v1.3 rewrite — drop the DO-NOT-ORDER banner, J_ISOLOOP replaces J_ESTOPLOOP/J_CONTACTOR in sections 3/4/5/6/11, 16 hand-solder refs, J_ISOLOOP added to the order-preview human gate, pole legend + the non-conductive-enclosure line; 2) fab export + A-ROT / A-POL (ship rotation_human_gate.txt) / A-POS (verify every CPL row on the pad-centre datum; cooksense's J_PI measured 24.16mm off under the old anchor emission) / A-POP / A-STOCK / P-FACT / M-BOM / bom_source_check; 3) jlc_twin REGENERATED (render path fixed in 9066ebd/828db4c — never reuse an old render); 4) policy_audit 0 FAIL + contracts_audit + tests/run_tests.sh; 5) both red-team lenses + a fresh zero-context lens over the STAGED archive; 6) 2-commit seal + SUPERSEDED.md on v1.0/v1.1 (22 wrong CPL rotations = DO-NOT-ORDER).
do_not: revert the KF350 pad to 2.60 (it costs the whole margin budget); raise `hole_to_hole.min_gap` back to 0.5 (never satisfied on this board, not this tier's number); delete the User.4 rects (the moat is symmetric and the router WILL leave it — measured 1.9078mm); un-anchor C_SWB / R_DECDPD / C_DECUEN / C_ULNA or drop their reservations; re-race without expecting a NEW pair of stranded plane pads; claim byte-identical M-REPRO without fixing generate_board's UUIDs; normalise R_WDPETPD back to 100k (1k IS the fix); add the H3/H4 pour pullback; trust a nearest-point distance as an overlap test.
p0_closed_v13b: **CLOSED dddc1a1 — R_OPENT WAS ORDERED 6.2k WHERE THE DESIGN NEEDS 62k.** The tsx authors `R_OPENT resistance="62k"` (open-thermistor detect threshold: 3V3_ANALOG -> R_OPENT -> TCAM_OPEN -> R_OPENB 100k -> GND) but the row's LCSC code C25915 IS 6.2k. Verified twice and NOT by decoding a part number: JLC selectSmtComponentList C25915 -> 0402WGF6201TCE describe "6.2kΩ"; LCSC product page C25915 -> MPN 0402WGF6201TCE resistance "6.2kΩ". The 0402WGF convention (3 sig digits + 1 multiplier) is validated against 21 already-verified ledger rows. CONSEQUENCE COMPUTED: threshold moves 2.0370 V (intent, and that figure is what identifies this node) -> 3.1073 V. An open head's sense node reads 2.2687 V, now BELOW the threshold, so the comparator never trips and AN OPEN THERMISTOR READS FINE — the precise failure v1.3's open-detect exists to remove. 3.1073 V is also ABOVE the LMV393's 2.500 V VICR ceiling, so the input is outside its guaranteed common-mode range. CORRECT PART: **C37825** (0402WGF6202TCE, 62kΩ ±1%, same UNI-ROYAL family, stock 127526). NOT changed — electrical/BOM change on a safety function, escalated. Fix path once approved: tsx supplierPartNumbers -> netlist -> generate_board -> --reuse-route rebuild (placement and land are unchanged, so the frozen chain and the 0/0/0 DRC should survive) -> re-export.
export: **A-ROT unblocked (be6e750, 57 rows OK), export EXIT=0, 189/189 CPL rotations sourced.** Coordinator's four verifications all PASS: D_KSTOP/D_REVCLAMP/D_TVS = 0.0 (the tool's pin-1 channel proposed 270 for the diodes and is wrong); U_ULNA/U_ULNB = 270.0 (^SOP-18_,0 would have been 270 out on the contactor driver bank); C67470 resolves nothing (0 rows in BOM/CPL/log); rotation_human_gate.txt written, 11 codes / 14 refs. A-POS re-derived INDEPENDENTLY of the exporter over the pad-centre-bbox datum: 189/189 on-datum, worst 0.0000mm.
twin: REGENERATED, never reused. 184 OK, 184 MODEL-REG-OK (worst 0.98mm J_LOADCELL), 31 PAD-GEOM, 9 POLARITY-FIT (6 OK / 3 BLIND), 1 MIRRORED, 1 FETCH-FAILED + 1 NO-BODY. Every class adjudicated in twin_adjudications.yaml; coverage checked BOTH ways (no finding without an adjudication, no adjudication grading a code absent from the v1.3 BOM). Key entries: C125121 U_OPTO — the twin's delta POINTS THE WRONG WAY (it compares pad1<->pad4 centre span, ours 9.530 vs JLC 10.000, but the property is the CLEAR STRIP between lead rows: ours 7.530mm vs JLC 7.000mm, so ours is 0.530mm MORE barrier and adopting JLC would erode it); C67470 RETIRED (graded U_COMP, which moved to C7984 in v1.3 — an adjudication grading a part that is not fitted is coverage that cannot fail, and it is how C7984 went ungraded); POLARITY-FIT is INVERTED (BLIND on the two polarized parts, OK on the one that is not — the channel wants a pin-1 dot or a chamfer and a cathode BAND is neither).
c5158048: CONFIRMED SYMMETRIC from the manufacturer, not a suffix. Nexperia datasheet ARCHIVED at 02_parts/PESD5V0S1BA/PESD5V0S1BA_2024-04-26.pdf. Section 5 Table 2: pin 1 = K1 "cathode (diode 1)", pin 2 = K2 "cathode (diode 2)", symbol sym045 = back-to-back zeners, no anode pin. Section 10: "suitable on lines where the signal polarities are both positive and negative with respect to ground." Both pins are cathodes => 180deg rotation is electrically identical => nothing for a human gate to confirm. Dossier `pins:` corrected K/A -> K1/K2. TRAP recorded: the same datasheet's SOD323 outline note "The marking bar indicates the cathode" is shared-outline boilerplate and cannot distinguish an orientation here. OUR SILK IS A SEPARATE DEFECT, LOGGED FOR v1.4 NOT FIXED: Diode_SMD:D_SOD-323 asserts a cathode on five refs; assembly risk nil (JLC follows the CPL) but a reviewer may "correct" a placement that was already right.
policy_audit_mistarget: A-POP / A-BODY / M-BOM FAILs on this project are MIS-TARGETED, not cooksense defects. policy_audit sets `_asm_target = latest release` / `rels[-1]`, which selects interposer-v1.0-2026-07-24 (sorts after cooksense-v1.1-2026-07-24), so cooksense's assembly.yaml is graded against the INTERPOSER board — hence "declares J_ISOLOOP not_assembled but no such footprint exists". DIRECT runs on cooksense: A-POP 1 finding (MANIFEST-UNDECLARED, expected pre-seal), M-BOM 1 finding (the R_OPENT P0). Same multi-board class the project already shadow-roots around for generate_rules and that count_parity hits too. Reported, not fixed.
fleet_tasks_logged: (1) DETERMINISTIC UUIDs in generate_board_generic.py — makes M-REPRO byte-checkable AND stops a data-only CPL fix reading as a full respin (usb-hub 81626 churned diff lines, which is what forces board_attr_plan to exist); root cause is KiCad serialising footprints in UUID order, so the zone filler tessellates differently while every VALUE is identical. (2) #31 A-POS datum: SETTLED — 24.130mm and 24.1634mm are both exact and are different quantities (along-row component vs 2-D anchor->datum shift). (3) policy_audit multi-board mis-targeting, above. (4) jlc_rotation_measure / jlc_twin have NO cathode-band channel, so both report BLIND/withheld on rectifiers whose polarity is carried by a band.
ropent_fix: **CLOSED at dddc1a1, approved by the coordinator, who reproduced every number independently.** R_OPENT -> C37825 (0402WGF6202TCE, 62k +-1%, stock 127526). THE SOURCE ALREADY CONVICTED THE VALUE and I had missed it when escalating: the tsx comment block four lines above the resistor documents 3.107V as the REJECTED FIRST CUT ("That is ABOVE the LMV393's common-mode ceiling ... so the part never compared against it ... R_OPENT/R_OPENB were inert"), so 6.2k does not miss the intent, it silently reinstates the defect the v1.3 second pass exists to remove. ROOT CAUSE: R_OPENT carried no `supplierPartNumbers`, so tscircuit coded it, and ALL THREE of its candidates for "62k" are 6.2k (C25915 0402WGF6201TCE, C137946 RC0402FR-076K2L, C2909371 FRC0402F6201TS) — it reads "62k" as RKM "6k2". Same class as R_OS ("510k" -> three candidates, all 390k), which had been caught and pinned. ALL FOUR divider resistors are now pinned and ledger-verified: R_OPENT C37825 (62k), R_OPENB C25741 (100k), R_CLMPA/R_CLMPB C25768 (22k) — the last three were right only by candidate ORDERING, which is not being right. VERIFIED: BOM row `62kΩ,R_OPENT,R_0402_1005Metric,,C37825`; netlist CONNECTIVITY IDENTICAL (192 nets, every node the same — a BOM-source change and nothing else); DRC 0/0/0; frozen chain survived exactly (fp/track/via hashes byte-identical to the pre-fix board); export EXIT=0, 189/189 rotations sourced.
mrepro_3run: **GREEN — cooksense does NOT reproduce usb-hub's nondeterminism.** Three from-source regenerations of identical source (the coordinator's decisive test after usb-hub measured 292/294/293 vias): vias **1045 / 1045 / 1045**, via hash 88c3ab97b6a5ec5f x3, track hash b35fccb5d57160ae x3 (3902 each), footprint hash 19b74787faa5dba1 x3 (226 each), island_rescue 18 x3, seed_stubs 58 pins / 0 refused x3. Zone fill identical too: islands 1/114/19/2 and areas 8434.792 / 2921.120 / 7400.062 / 8474.288 on all three. SCOPE OF THE CLAIM: these are `--reuse-route` runs, i.e. the canon-M3 authoritative path that imports the promoted frozen chain, so the track set is fixed by construction and only the stitch can vary — and this board's stochastic rescue ladder is nearly empty (pad_rescue 166/167 GND + 76/76 3V3, the rest deterministically seeded), which is exactly what the v1.2 determinism work bought. The UUID mechanism IS still present (file bytes differ per run) and an earlier build PAIR showed 1-part-in-4e6 zone-area drift with identical island and via counts; via count has never varied across 5 observed builds. So cooksense is NOT blocked on the fleet UUID fix, but the fix is still owed for the fleet.
mrepro_method_trap: a `.kicad_pcb` copied to a scratch dir WITHOUT its `.kicad_pro` alongside fills with DEFAULT netclass clearances — the netclasses live in the .kicad_pro. My first pre/post zone comparison reported a ~54mm2 fill difference that was entirely this artifact; paired correctly the same two boards agree to 1 part in 4e6. ANY zone-fill comparison must copy the .kicad_pro under a matching basename or it is measuring the fallback, not the board.
```

## 2026-07-28 — start (ELECTRICAL REVISION v1.7, authorized by the user)
- did: intake for the v1.6-deferred hardware fixes. Read CLAUDE.md, pcb-design SKILL,
  CHANGELOG, v1.6 ORDER_README sections 0/2a/7a/10, verification/crossplug_and_permission_defaults.md,
  STATUS beacon, cooksense.tsx blocks 2/3/4 + connector block, floorplan east-column solve.
- result: FOUR items confirmed and scoped. (1) COIL_EN cross-plug: J_MODE is 1 of FIVE
  identical C189896 GH housings; COIL_EN = {J_MODE.4, Q_COILDRV.1(G), R_COILENPD.1}, sole hold
  100k, no series element, no ESD. (2) 11 of 18 safety-chain nets carry no restrictive default.
  (3) REARM_N has one driver and EXP_RST_N has NONE. (4) three stale source/doc statements.
  KEY SPATIAL FACT for the keying adjudication: the east connector column is SATURATED —
  measured courtyard gaps H4->J_MODE 0.058, J_MODE->J_ESTOP 0.080, J_ESTOP->J_DOOR 0.090,
  J_DOOR->J_ISOLOOP 0.510, J_ISOLOOP->J_RH_EXHAUST 0.160 = 0.898 mm of TOTAL slack in the
  column, against a JST-PH 5-pin that is ~+3 mm wider than the GH it would replace. A
  same-position family swap to PH is therefore NOT free; it is an east-edge repack plus a
  re-derivation of the 2.0 mm ISO moat that took a bounded solve to close.
- next: adjudicate the keying option against that measurement (a NARROWER non-mating
  connector is the only one that lands without a repack), verify JLC stock for the
  candidates, then write ADRs before touching the tsx.

## 2026-07-28 — handoff (PLANNED, at the declared routing-gate boundary)
- did: took the v1.7 electrical revision from source through DRC 0/0/0, then ran the
  fab export once to find out exactly what the release stage still owes.
- result: **DRC --severity-all --refill-zones --schematic-parity = 0/0/0.**
  export_jlc_package exits **A-ROT BLOCKED on exactly ONE placement** — `C485354`
  (J_MODE, the new JST ZH header) has no MEASURED row in the fleet authority table
  `skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv`; every other placement on the
  board resolves from an existing measured row. The row IS measured (offset 180,
  two-channel, CPL 270) and is saved verbatim in
  `06_build/verify/arot_C485354_measured_row.txt` together with its raw four-angle
  channels and the PIN-1-MARK dissent. THIS AGENT WAS INSTRUCTED NOT TO EDIT
  `skills/`, so the row is REPORTED rather than applied — it is the single
  mechanical step between this tree and a fab package.
  Also emitted by the export and unchanged from v1.6: A-POL SINGLE-CHANNEL on 10
  codes (order-preview human gate), and the three advisory ROT-XCHECK notes.
- next (for the successor, in order): (1) land the C485354 row; (2) re-run
  export_jlc_package -> bom_source_check / bom_legibility (F-LEGIBLE) /
  jlc_stock_check / jlc_twin + twin_overlay (A-RENDER) / part_facts_check;
  (3) A-POP/A-POS/A-ROT/A-BODY; (4) policy_audit --board cooksense (E-TOPO stays
  the one FAIL, deliberate); (5) scoped review lenses per canon "Verification
  scoping" — this is a MATERIAL design change, so BOTH red-team lenses plus a pin
  review of the changed parts; (6) seal cooksense-v1.7 + SUPERSEDED.md on v1.6 +
  CHANGELOG entry + beacon refresh + status_beacon_check.

## 2026-07-28 — start (v1.7 RELEASE STAGE, resumed from the planned handoff)
- did: scoped intake per the skill rule — STATUS beacon, the TAIL of this journal,
  CLAUDE.md, pcb-design SKILL stage 7, jlcpcb-fab SKILL pipeline + assembly battery,
  the 07_releases contract "Seal procedure (normative — the 2-commit seal)", and the
  three handoff commits ae80e37 (source) / 8553b89 (route) / 8b814ae (handoff).
- result: **the A-ROT blocker is CLEARED upstream.** `C485354` now has a MEASURED row
  at `skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv:66` — offset 180, CPL 270.0,
  two-channel, landed by 772b152 which ALSO fixed the tool-frame bug behind the
  recorded PIN-1 dissent (the pin-1 channel had been reading our marks in the BOARD
  frame and JLC's in the LOCAL frame, so it was exactly board_rot out of step). The
  dissent is resolved and is NOT to be re-litigated; the HUMAN GATE on J_MODE stands
  on its own footing (near-symmetric contact array => a 180 error solders perfectly
  and reverses the harness = interposer v1.0's failure), and must appear in ORDER_README.
  Tree state confirmed: 07_releases/ untouched, v1.6 still live, working tree clean
  for this project (the one dirty path is a SIBLING board, which does not block).
- next: export the fab package, run the full fab/assembly gate battery against the
  STAGED archive, launch the four review lenses CONCURRENTLY (both red-team lenses +
  fresh-context PIN and RENDER reviews) against curated input, then the 2-commit seal.

## 2026-07-28 — iterate (fab package + gate battery; ONE fix taken before the reviews)
- did: cleared A-ROT, ran the fab/assembly battery against staging, and took one
  defect the battery surfaced rather than shipping it into the review lenses.
- result: **export EXIT=0, A-ROT OK on all 202 CPL rotations.** `J_MODE` resolves
  `90 + 180 -> 270` from the landed C485354 row. A-POL SINGLE-CHANNEL on the same
  10 codes as v1.6 (unchanged), three advisory ROT-XCHECK notes unchanged.
  **SILK REVISION BUMP, and it was OWED.** The board silk read `sidecar v1.3`.
  v1.4/v1.5/v1.6 were docs/BOM-only supersedes over a board md5-identical to
  v1.3's, so the string was honest through all three — v1.7 MOVES COPPER, so a
  field board saying v1.3 would send anyone diffing it against the sealed v1.3
  archive to the wrong netlist. This is the same defect BOTH red-team lenses
  caught at v1.2->v1.3 (floorplan.yaml:860 records it). Bumped in floorplan.yaml
  and REBUILT FROM SOURCE. **The rebuild is a copper IDENTITY, measured:** tracks
  4166 hash 16d81d6b2d1634d6, vias 1104 hash 5cc95d962b455a39, footprints 239
  hash a4cfa2956c816c70 — all three byte-identical to the pre-bump board; DRC
  re-measures 0/0/0. Same 4-character token, so the stroke-font bbox is unchanged
  and the pinned caption displaced no neighbour (refdes on silk 228/235, the same
  2 pre-existing crowded captions). It also re-confirms M-REPRO: a full
  from-source rebuild reproduced this board's copper exactly.
  **TWO GATE DEFECTS IN `jlc_twin.py`, both MEASURED on this board, both owed to
  skills/ (this agent was told not to edit skills/, so they are reported):**
  (1) PAD-GEOM is a KNIFE EDGE. `PAD_GEOM_TOL = 0.3` is compared with a strict
  `>` against a delta that IS exactly 0.300, so the six IDENTICAL `Diode_SMD:D_SOD-323`
  refs against JLC's SOD-323 land split 3-fire / 3-silent on the last bit of
  math.hypot over BOARD-frame doubles: D_COILEN 0.300000000000006, D_ESD_IN
  0.300000000000002, D_ESTOP 0.300000000000006 fire; D_DOOR / D_LCCLK / D_LCDAT
  0.299999999999977 do not. Same footprint, same JLC land, same 2.100-vs-2.400
  pad1<->2 delta — the only variable is where the part sits on the board.
  (2) `marker_side()` HAS THE FRAME BUG THAT WAS JUST FIXED NEXT DOOR. It takes
  the pad axis from `opads_raw`, computed with the footprint temporarily
  DEROTATED to 0, but reads `fp.GraphicalItems()` at the footprint's REAL board
  orientation. At board rot 0 the two frames coincide; at 90 the graphics project
  onto an axis perpendicular to the pad axis and the overhangs collapse
  symmetric. MEASURED: D_COILEN (board rot 90) over_a = over_b = -0.2000, margin
  0.0000 -> POLARITY-FIT-BLIND, against margin 0.5600 -> pad 1 on the five
  identical refs at rot 0. So D_COILEN's BLIND is a TOOL ARTEFACT, not a missing
  mark — same class as the `jlc_rotation_measure.py` pin-1 bug fixed at 772b152,
  still live in jlc_twin.
  **A THIRD, in `twin_overlay.py` + `jlc_twin.py`'s hard-coded render size.**
  A-RENDER's `MIN_BODY_PX = 20` is an ABSOLUTE pixel floor while its tolerance is
  in mm, and jlc_twin renders at a hard-coded 1600x1000. At that size this board
  produced ONE false unfaithful (`U_LDO` centre 1.248 mm, 576 body px) and ONE
  false unmeasured (`Q_SWDRVRHA`, 13 px vs floor 20). Re-rendered at 3200x2000
  the SAME board gives U_LDO 0.140 mm / 3425 px and Q_SWDRVRHA 0.047 mm / 338 px,
  0 unfaithful, 0 unmeasured, coverage 52 -> 53. VERIFIED INDEPENDENTLY of the
  tool (canon M1) with a pure-PIL column scan of twin_top.png over U_LDO's
  courtyard: the three SOT-223 gull-wing leads render as bright metal across
  x 17.61..19.75 mm and the tab across 23.27..25.80, i.e. the picture spans the
  full EXPECTED 18.255..25.365 box — the extractor was excluding the three thin
  leads while including the one large tab, which is what shifted the measured
  centre 1.05 mm toward the tab. The RENDER was faithful; the SEGMENTATION was
  resolution-limited.
  Gate results against staging: DRC 0/0/0. ERC 0 errors / 411 warnings (410
  lib_symbol_issues + 1 isolated_pin_label). E-INV 109/109, E-ADR 8/8.
  net_label_survival 162/162 over 192 nets. S-COUNT 4/4 over 235 refdes (run in a
  SHADOW ROOT — `count_parity.py` globs `*.kicad_sch` / `*.net` and picked the
  INTERPOSER's on a two-board project; the multi-board mis-targeting class again).
  audit_board PASS (I-ISO 6.12 mm, I-OUT 0.35 mm). placement_gates PASS (P-OUT
  0.30 mm pad datum; the `--courtyard` variant reports 6 edge-connector
  overhangs BY DESIGN and is not this board's gate). bom_source_check PASS, leg C
  26/26. F-LEGIBLE OK 57 checks / 0 findings. P-FACT OK, 5 graded of 6 dossiers
  declaring asserts, 1 DEFERRED. A-STOCK **PASS 55/55** coded lines, verdict line
  parsed from the JSON sidecar. jlc_twin EXIT 0 (203 OK / 461 rows, bodies
  204/205). A-RENDER OK. A-POS worst 0.00000 mm over all 202 rows.
  **PARITY IS 1/163 AND IT IS THE SAME ONE v1.6 SHIPPED, now MEASURED rather than
  restated:** `('J_KEY_MATRIX','MP')`. Both SM10B-GHS-TB mechanical shell tabs are
  on NO NET, where `03_tscircuit/parity_padmap.txt` declares them bonded to
  GND_ISO. Every OTHER connector's MP tabs are on GND (measured, all 20 of them).
  Bounded: the tabs sit 3.696 mm from the nearest signal pad (KP_U1) and 25.5 /
  40.5 mm from the nearest filled zone of any net, so there is no creepage path
  for a floating intermediate conductor to split. P2, pre-existing since v1.0,
  NOT introduced by v1.7, deferred with the numbers.
- next: policy_audit, the four review lenses (launched concurrently), then
  ORDER_README + MANIFEST + the 2-commit seal.

## 2026-07-28 — iterate (staging complete; four review lenses running concurrently)
- did: closed the policy_audit FAILs that were closeable, staged the full archive,
  wrote the ORDER_README/CHANGELOG/SUPERSEDED, and launched the review battery.
- result: **policy_audit FAIL 5 -> 3**, and the two that closed are worth naming.
  A-BODY was reporting "1 of 205 CPL placements have NO 3D body: J_ISOLOOP" — a
  FAILURE I MANUFACTURED. v1.7 re-authors J_ISOLOOP BY MPN (deliberate source
  change: `C42400616` has stockCount 0 on every KF350 4-pole line and JLC has no
  CAD, so naming it on a JLC ASSEMBLY BOM asks the fab to source what it does not
  carry), so it is UNCODED and correctly out of the twin's population. I had been
  forcing it back in with `--also`, which inserted an off-CPL hand-soldered THT
  screw terminal into the A-BODY denominator. Shipped evidence is the run WITHOUT
  `--also`: **bodies mounted 204/204**. The `--also` probe is kept as SEPARATE
  evidence (verification/twin_isoloop_probe.md) because dropping the ref would
  otherwise quietly retire the FETCH-FAILED adjudication's claim that the part is
  genuinely absent from JLC's library — re-probed live today, **absence
  REPRODUCED**, so both adjudications stay in the register on live evidence.
  **P-ADJ-UNREACHED is a NEW upstream check (fd1fe57, landed today) and it fires
  hard: 25 of 37 declared keep_short budgets across 02_parts/ name a net that does
  not exist on this board.** Before it existed P-ADJ reported PASS over budgets it
  had never evaluated. Full 37-row census measured and shipped. Classified:
  (A) 13 RAIL-PIN budgets (`VCC` x4, `VDD` x2, `VREF`, `N3V3`, `3V3_DIGITAL`,
  `+5V`, `5V_SELV`, ...) — per-instance LOCAL budgets written as a PIN name;
  renaming them to `3V3` is a FAKE GRADE, measured: that rail is 76 pads / ~150 mm
  and the EXISTING P-ADJ waiver already documents it as geometrically unreachable,
  so a rename converts 13 honest "never evaluated" into 13 instant violations
  absorbed by an existing waiver — which policy_audit's own source says is the
  inherited-defect pattern it exists to stop. (B) 7 REFERENCE-DESIGN net names on
  fitted parts, and I measured what each rename WOULD have scored so the omission
  is auditable: HS_GATE -> HS_GATE_COIL 10.169 / SWG_A 4.128 / SWG_B 6.445 /
  SWG_RHA 6.445 / SWG_RHE 7.429 (budget 6); OPTO_LED -> OPTO_LED_A 5.722 (PASSES);
  EN_OVLO_N -> EF_OVLO 8.473; ILM -> EF_ILM 6.982; dVdt -> EF_DVDT 4.524; +5V ->
  5V_IN 18.106; 5V_SELV -> 5V_RPP 15.581; T_PLUS/T_MINUS -> TC_POS 13.640 /
  TC_NEG 8.967. NOT renamed: a rename without a RE-PLACE trades 7 unreached for 10
  violations on a placement this revision did not author, and re-placing
  invalidates a route measuring 0/0/0. (C) 5 on parts NOT FITTED here (AQY212GS,
  SN74HC138DR, SN74HC139DR, LM393DR, SN74LVC1G123DCTR x2 — the superseded
  comparator and the superseded one-shot). Waived under its OWN id with the census
  attached and the electrical intent cross-verified by a DIFFERENT instrument
  (audit_board I-PROX, 28 proximity checks, every IC decoupler 2-5 mm from its
  own package pin). The schema fix — a per-INSTANCE budget form — is OWED to
  skills/ and reported, not applied.
  **E-INV RED VERIFICATION REGENERATED, not inherited.** The shipped file was
  v1.3-era and proved 83 invariants could fail; this release ships 109. Four new
  mutations, one per NEW invariant family: R_COILENPD 680->100k (ADR-0018 value),
  J_MODE.4 COIL_EN_IN->COIL_EN (ADR-0018 topology — the "simplification" that
  deletes R_COILENS), R_FAULTPU.2 off 3V3 (ADR-0019 DIRECTION — the blanket
  pull-down), U_LATCHB.1 REARM_PULSE_N->REARM_N (ADR-0020 edge bypassed). All
  four made the checker exit 1; all four restored to a byte-identical file with
  109/109 and `git status` clean on the invariants file.
  A-EVID: 26 of 32 required artifacts present; the 6 outstanding are MANIFEST.txt
  and the four review verdicts + policy_audit, all of which come last by design.
- next: join the four lenses, disposition every finding, then stamp and seal.

## 2026-07-28 — iterate (PIN REVIEW landed: PASS, and it found a v1.7 REGRESSION)
- did: joined the fresh-context pin review (20 parts: the new J_MODE, the one-shot
  and latch group, the safety-chain gates + expander, the isolation/drive parts),
  archived it VERBATIM, and re-derived every finding from the board myself.
- result: **VERDICT PASS. No mirror, no mis-mapped pin, no wrong power/gate/enable
  net.** The reviewer also diffed all 20 placed footprints against the stock KiCad
  library and found them pad-for-pad identical, which closes the mirror class on
  this set independently of our own generator. Four QUESTIONs, all CONFIRMED by my
  own netlist query, and **one of them is a REGRESSION THIS REVISION INTRODUCED**:
  **`U_EXP.8` (GPB7, the WD_OK READBACK) and `U_EXP.18` (RESET_N) are now the SAME
  NET.** MEASURED both ways: v1.6 had U_EXP.8 = WD_OK and U_EXP.18 = EXP_RST_N;
  ADR-0020 moved .18 onto WD_OK, so now WD_OK high => expander out of reset =>
  GPB7 necessarily reads 1, and WD_OK low => expander IN reset => cannot be read.
  **GPB7 can never report "not OK", and the other seven status bits go dark at the
  moment they matter most.** Graded P1, not P0, and NOT reverted: reverting
  restores the defect ADR-0020 exists to close (driverless EXP_RST_N => the
  expander's registers held across every Pi reboot => a held-low REARM_N survived
  a reboot). The trade is a sampled diagnostic bit for a hardware reset path that
  forces every RAIL_EN / CONTACTOR_REQ / REARM_N to POR on any watchdog timeout.
  The diagnostic is RECOVERABLE and in a better form: MCP23017 IODIRA/IODIRB POR
  to 0xFF, so a host that reads IODIRA back and finds 0xFF where it wrote outputs
  has a LATCHED watchdog-event indication where GPB7 was a sampled one. Written up
  as new ORDER_README **§7a-3** with the bring-up test, and §7a's header rewritten
  (2 firmware invariants -> 3 obligations, one of which v1.7 moved into hardware).
  Other three QUESTIONs, all confirmed and all PRE-EXISTING: `KEY_LATCH =
  {J_PI.32, U_LATCHG.1}` with no default (the only Pi-sourced input without one,
  and it clocks U_SR1's RCLK); `PRESS_REQ = {U_ONESHOT.2, U_SR1.7}` floats at
  power-on because U_SR1's outputs are Hi-Z via R_OE; `J_MODE.1 = 3V3` and
  `J_MODE.3 = KEY_RELAY_ALLOWED` leave the enclosure bare while `.2` and `.4` are
  protected — ADR-0018's scope was the ARMING net and the failure direction on
  pin 1 is restrictive (rail collapse => everything de-asserts), so P2.
  **AND A REAL skills/ DEFECT, which I reproduced: `pin_audit.py:130` joins
  `parts / mpn / "part.yaml"` LITERALLY and falls through in silence.** MEASURED:
  **16 of 54 dossiers on this board carry `(not in yaml)` on every pin** — U_EXP
  (`MCP23017-E/SS`, '/' illegal in a path), J_PI (`2.54-2*20PPC104`), J_LOADCELL
  (a `(LF)(SN)` suffix), and the thirteen uncoded self-supplied refs (twelve reeds
  + J_ISOLOOP) whose MPN column is EMPTY. **The one IC whose reset pin this
  revision re-targeted is in that set**, so the reviewer checking U_EXP.18 had an
  empty function column to check it against and caught the regression anyway. The
  MCP23017 part.yaml even carries `note_dirname:` documenting the exact mismatch
  and NOTHING READS IT. Reported, not applied.
- next: the two red-team lenses and the render review are still running.

## 2026-07-28 — finish (BLOCKED: the review battery returned TWO CONFIRMED P0s; v1.7 NOT SEALED)
- did: joined all four lenses, archived every verdict VERBATIM, and re-derived
  every finding from primary sources before dispositioning it.
- result: **STOPPED AT THE SEAL. `07_releases/cooksense-v1.7-2026-07-28/` is
  MUTABLE STAGING and stays uncommitted.** Verdicts: redteam-topology
  **DO-NOT-ORDER** (2 P0), redteam-layout **DO-NOT-ORDER** (1 P0), render-review
  **FAIL** (1 P0), pin-review **PASS**.
  **P0-A — THE eFUSE OV CUTOFF IS AT 9.2 V ON A RAIL FEEDING 7.5 V COILS, AND
  BOTH RED-TEAM LENSES FOUND IT INDEPENDENTLY.** R_OVT 100k / R_OVB 15k, ratio
  0.130435, against SLVSE57C's V_OVLO(R) 1.13/1.20/1.27 V -- the datasheet IS in
  02_parts/ and the layout lens could not open it, so it reported the setpoint
  UNVERIFIED; the topology lens read it and reported it WRONG; I read it and
  confirm 9.200 V nominal, 8.492-9.933 V worst case. Intent per the part.yaml
  gotcha, power_tree.yaml:130, ARCHITECTURE.md:41 and BRIEF.md:77 is 5.5-6 V.
  Exposure: 13 DIP05-1A72-12L reed coils at **7.5 V max** and D_TVS SMBJ5.0A
  whose V_BR starts at **6.40 V** (so on a sustained OV the 600 W transient part
  becomes the DC regulator). **AND THE MOST USEFUL OUTPUT IS THAT BOTH LENSES'
  PROPOSED FIXES ARE WRONG**, which only three-way arithmetic shows: my first cut
  (R_OVB->22k) tops out at 7.159 V, above the TVS; the topology lens's
  (R_OVT->57.6k) puts V_pin at 1.1545 V against a 1.13 V threshold at the
  DECLARED vin_max 5.5 V, i.e. nuisance-trips. The admissible window at vin_max
  5.5 is ratio in (0.198437, 0.205455) = 1.0354x wide, against a 1.0404x spread
  from two +-1% legs: **NO +-1% DIVIDER FITS.** The supply envelope, the TVS
  standoff and the OVLO requirement are mutually incompatible AS DECLARED, and
  the root cause is the same undeclared supply tolerance that produces the
  E-TOPO dropout gap. That is a user decision, not an agent patch.
  **P0-B — ONE I2C WRITE DEFEATS THE WATCHDOG IN BOTH CHAINS, AND v1.7 MADE IT
  WORSE.** WD_OK carries U_EXP.8 (GPB7, a BIDIRECTIONAL MCP23017 I/O rated
  25 mA) on the same node as U_WD.1 (TPS3823, V_OL specified only to 1.2 mA) and
  -- since ADR-0020 -- U_EXP.18 (RESET_N). `IODIRB.7=0, OLATB.7=1` forces the net
  high; recovery needs the node below 0.66 V so the contention is
  SELF-SUSTAINING. It removes the watchdog term from U_AND1.3, U_CAND1.1,
  U_FAULTAND.1 and U_OENAND.2 at once. MEASURED both boards: v1.6 had U_EXP.18
  on EXP_RST_N, so **ADR-0020 is what put the reset on the net its own defeat
  disables, and Decision B's claim ("the expander's outputs cannot persist
  across a watchdog timeout") is false in exactly its own case.** The PIN review
  reached the SAME NET from the other side (a degenerate GPB7 readback, written
  up as ORDER_README section 7a-3) -- two lenses, one node, and the more serious
  reading is the right one. Fix is one 0402 on an existing line: 10k (C60490) in
  series to U_EXP.8 ONLY, leaving U_EXP.18 and the five gate inputs on the raw
  net, which also repairs the readback for free.
  **THE RENDER LENS'S P0 IS DOWNGRADED TO P1 WITH EVIDENCE, NOT DISMISSED.**
  R-01 (J_ESTOP/J_DOOR identical unkeyed pin-compatible pair) is CONFIRMED from
  the board and its mechanism is real -- but ORDER_README section 10.4 already
  grades both cells `FALSE-CLEAR` in a published 20-cell matrix whose own summary
  is "not one of the twenty is fail-safe", and the reviewer was deliberately
  denied that document. A zero-context lens re-deriving a disclosed hazard is the
  system working. What IS new is R-04: the mitigation section 10.5 leans on is the
  silk refdes, and `J_DOOR`'s label measures 2.80 mm from J_ESTOP against 2.87 mm
  from J_DOOR -- **closer to the wrong connector** (163 of 228 refdes are >3 mm
  from their part; 16 sit nearer a different part). A label that points at the
  wrong part is not a mitigation.
  **AND ONE CLEAN v1.7 REGRESSION I CONFIRMED MYSELF:** the `J_MODE` and
  `D_COILEN` refdes are printed INTO the east-edge milled notch. Notch void
  x[191.50..200.05] y[48.80..49.80]; J_MODE's refdes bbox x[194.099..197.801]
  y[48.386..49.614] is ENTIRELY inside it. **ADR-0018's two headline parts will
  ship with no designator**, and D_COILEN is simultaneously POLARITY-FIT-BLIND.
  Nothing caught it because `silk_edge_clearance` -- the exact rule -- is one of
  the four silk DRC checks this board sets to `ignore`, which ORDER_README
  section 13 already warns about in the abstract. This release is the instance.
- do_not: seal on the strength of the green gates. Every mechanical gate in this
  release passes and the battery still found two P0s -- that IS the argument for
  the battery. Do not "fix" either P0 by picking one of the two proposed
  resistor values: neither satisfies all three constraints, and the third
  constraint (the SMBJ5.0A's 6.40 V V_BR) only appeared because a SECOND
  independent lens looked. Do not revert ADR-0020's U_EXP.18 move to recover the
  readback -- that restores the driverless EXP_RST_N the ADR exists to close;
  isolate GPB7 instead. Do not put 680R on J_MODE.3 with the RT-03 fix (1.543 V,
  below V_GS(th) max -- it would brick the coil rail).
