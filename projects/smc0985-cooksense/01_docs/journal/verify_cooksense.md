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
  Exposure: 12 DIP05-1A72-12L reed coils at **7.5 V max** and D_TVS SMBJ5.0A
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

## 2026-07-28 — start (v1.7 UNBLOCK: the user has decided BOTH P0s)

- did: read the beacon, the DISPOSITIONS ledger, the four v1.7 verdicts, ADR-0020,
  `power_tree.yaml`, `07_releases/contracts.md` and `git show 9a02c52 / 7f2fcbd`;
  then re-derived both P0 setpoints from PRIMARY documents before touching source.
  USER DECISIONS carried in: (A) the supply becomes a SPECIFIED **4.85-5.25 V**
  commission fact, not a mitigation note, propagated to every home; (B) a **10 k**
  series resistor on `U_EXP.8` ONLY, plus an honest correction of ADR-0020.
- result: FOUR primary-source results, all reproduced by arithmetic in this entry's
  scratch script.
  **1. THE PREVIOUS PASS'S "NO +-1% DIVIDER FITS" CLAIM IS HALF WRONG, AND THE
  HALF THAT IS WRONG IS THE ALGEBRA.** The admissible window at `vin_max` 5.5 was
  computed correctly (k in (0.198437, 0.205455) = 1.0354x). The +-1% SPREAD was
  not: it was taken as (1.01/0.99)^2 = 1.0408x, which is the spread of a RATIO OF
  TWO INDEPENDENT RESISTORS. A DIVIDER's k = RB/(RT+RB) has RB in BOTH numerator
  and denominator, so its spread is (1.01/0.99)*(1.01r+0.99)/(0.99r+1.01) =
  **1.0322x** at r = 3.83. A +-1% divider therefore DID fit at 5.5 V on tolerance
  alone. It does NOT fit once the +-100 ppm/C TCR term (+-0.45% over -20..+70 C) is
  carried: earliest trip falls to 5.326 V, below the old 5.5 V ceiling. **The
  conclusion was right; the stated reason was not** — and the real reason is a term
  neither lens carried.
  **2. THE OV DIVIDER THAT FITS AT 5.25 V: `R_OVT` 100k UNCHANGED, `R_OVB` 15k ->
  26.1k, BOTH LEGS +-0.5%.** k_nom 0.206979 -> trip **5.798 V nominal**, inside the
  5.5-6 V intent three documents state. Worst case over -20..+70 C with +-0.5%
  +-100 ppm/C and SLVSE57C's `I_EN` +-0.1 uA (2.07 mV on a 20.698 k source):
  EARLIEST possible trip **5.3682 V** (spec max 5.25 -> **+118 mV**), LATEST
  guaranteed trip **6.2394 V** (SMBJ5.0A V_BR min 6.40 -> **+161 mV**; at -20 C the
  TVS's own +0.041 %/C moves V_BR min to 6.2819 -> still **+43 mV**; DIP05 coil
  7.5 V max -> **+1261 mV**). TVS conduction at the latest trip, from the two
  published points (I_R 800 uA @ 5.00 V, I_T 10 mA @ V_BR): **7.5 mA / 47 mW** at
  25 C, 9.3 mA / 58 mW at -20 C. As built (100k/15k) the same arithmetic gives
  9.996 V latest and **6.6 A / 66 W** through the TVS — that is the P0.
  **3. E-TOPO, RE-DERIVED, PASSES — AND THE "59 mV" WAS NEVER IN ORDER_README S7.**
  It is in the v1.6 `redteam_adversarial.md` (Sec.E part 3) and CHANGELOG:465. Its
  terms: 4.850 V at `J_PWR` minus an **ESTIMATED 92 mV** of series drop (F1 ~34 +
  Q_REV ~38 + eFuse ~20 mV at ~0.45 A), none of which had a cited maximum. I
  replaced all three with CITED maxima — Bourns MF-MSMF Series R1Max **70 mOhm**,
  AOS AO3401A R_DS(on) max **60 mOhm** @V_GS -4.5 V scaled by the datasheet's OWN
  hot ratio (50->75 mOhm 25->125 C = 1.50x) to **73.5 mOhm** at 70 C, TI SLVSE57C
  R_ON max **47 mOhm** (-40..85 C) — total **190.5 mOhm**, and at a 0.50 A
  whole-board worst case that is **95.2 mV**, not 92. So V(5V_PROTECTED) = 4.7547 V,
  headroom 1355.7 mV vs the cited 1300 mV dropout -> **PASS by 55.7 mV** (and still
  +36.7 mV at 0.60 A). PD falls to 614.7 mW / 51% because `vin_max` drops 5.5->5.25.
  **4. P0-B, THE 10k, WITH NUMBERS.** TPS3823-33 V_OL <= 0.4 V at I_OL 1.2 mA
  (SLVS165O 6.5) => guaranteed sink impedance <= 333.3 Ohm. GPB7 at 3.3 V through
  9.90 k (10k -1%) into 333.3||100k = 332.2 Ohm gives **WD_OK <= 0.114 V** incl.
  21 uA of aggregate input leakage, against MCP23017 RESET V_IL 0.2*VDD =
  **0.660 V** and LVC V_IL **0.800 V** — margins 546 mV and 686 mV, and the
  contention current is 0.323 mA = 27% of the spec point and 6.5% of the +-5 mA
  abs max. Un-resisted, GPB7 sources up to 25 mA into an output specified to
  1.2 mA: no datasheet predicts the node, and the loop needs <0.66 V to break.
- next: apply in source only — `power_tree.yaml`, BRIEF fact-lock, tsx (R_OVB
  value+code, R_OVT code, new `R_WDOKSER`), ADR-0020 correction + a new ADR for the
  supply spec, floorplan (J_MODE / D_COILEN refdes out of the east notch, J_DOOR
  label re-anchored), E-INV asserts RED-verified. Then full rebuild, DRC, full gate
  battery, full review battery. A P0 blocks again.

## 2026-07-28 — iterate 1 (source applied; TWO TOOL WALLS hit and both are MEASURED)

- did: applied every source change for both P0s + the supply spec, then rebuilt
  tsx -> circuit.json -> kicad_sch -> netlist -> board.
- result: **TWO TOOL FAILURES, neither a design problem, both bisected rather
  than worked around blind.**
  **(1) tscircuit's schematic pack solver DIES if `U_EXP.8` leaves `WD_OK`.**
  `tsci build` throws `Matchpack layout solver failed: PackSolver2 failed: null`
  after 22343 iterations and emits NO circuit.json at all, so the whole chain
  stops. BISECTED over 11 variants of the same file: committed tsx PASSES; +the
  OVLO value/code change PASSES; +a new resistor with NO new net PASSES; +a new
  net carrying only the resistor PASSES; and moving `U_EXP.8` off `WD_OK` by ANY
  route FAILS deterministically — to the new net, to `EFUSE_FLT_N`, to `3V3`,
  with or without a test point on the new net, with or without `TP_WDOK`, with
  the resistor declared in either block and with its pins either way round.
  **THE FIX IS A SPELLING, NOT A COMPROMISE:** wiring GPB7 as a DIRECT PIN
  REFERENCE — `<resistor ... connections={{ pin1: "net.WD_OK", pin2:
  ["U_EXP.pin8", "net.WD_OK_EXP"] }} />` — converges, and the solver's own debug
  names the distinction (`hasDirectConnections` vs `hasNetConnections`). The
  exported netlist is identical either way. Recorded verbatim at the call site so
  nobody "tidies" it back into the pinLabels map.
  **(2) THE CONVERTER'S LAYOUT MODE SHORTS A SAFETY NET TO 3V3, AND ITS OWN
  CROSS-NET GUARD DID NOT FIRE.** With the new netlist,
  `circuit_json_to_kicad_sch.py --mode layout` (the default) reported "4 segs
  dropped as cross-net" and then produced a netlist with **NO net `AND1` AT
  ALL**: its three nodes — `R_AND1PD.1`, `U_AND1.4` (the AND gate's OUTPUT) and
  `U_AND3.1` — appear inside `3V3`, a 79-node rail. `AND1 = MODE_AUTO_HW .
  WD_OK . ESTOP_OK`, so **three of the seven `KEY_RELAY_ALLOWED` terms would have
  been permanently TRUE.** `--mode grid` gives 193 nets with `AND1` = the correct
  3 nodes and `3V3` = 76. The board has always been built from grid (the guard
  fell back to it on the pre-change input, on `['SHIELD_DRAIN','TH_CAM_A']`), so
  this is the same output obtained deterministically instead of by luck.
  Same family as fd76c6d. REPORTED to skills/, not patched.
  **BOTH ARE NOW COMMITTED SOURCE, not a chat note:** new
  `03_src/cooksense/rebuild_schematic.sh` drives the schematic stage, forces
  `--mode grid`, and ends with a SAFETY-CHAIN SPOT-CHECK that asserts the node
  COUNT of 11 named nets (`AND1`, `AND2`, `KEY_RELAY_ALLOWED`, `CTR_SAFE`,
  `FAULT_SET_N`, `FAULT_LATCH_CLEAR`, `WD_OK`, `WD_OK_EXP`, `EF_OVLO`,
  `COIL_EN`, `COIL_EN_IN`) and exits 1 on any disagreement — the gate that would
  have caught this class. First run: **193 nets, spot-check 11/11, ERC 0 errors
  / 648 warnings.**
  **SILK: the notch/ownership repair is also source.** New
  `03_src/cooksense/fix_silk_placement.py`, wired into `rebuild_all.sh` as step
  1b. It takes the TRUE Edge_Cuts polygon (`GetBoardPolygonOutlines`, 8 outline
  points + 12 slot holes) instead of the generator's outer-frame rectangle, and
  re-places any refdes whose bbox+0.25 mm is not wholly on the board. On the
  pre-rebuild board it moved 4: `D_COILEN` and `J_MODE` out of the notch, and
  `J_DOOR`/`J_ESTOP` for OWNERSHIP. Ownership is graded on CENTRE distance with a
  1.5 mm lead, and the threshold is set FROM a full sweep, not chosen: the best
  lead the board affords is +2.353 mm (J_DOOR), +1.742 (J_ESTOP), +10.784
  (J_MODE). **`J_ISOLOOP` is NOT in the list and the omission is measured:** all
  31 legal positions for it score a NEGATIVE lead (best -2.955 mm) because the
  only clear silk band lies west of J_ISOLOOP and south of J_RH_EXHAUST — and it
  is a KF350 screw terminal that cannot be cross-plugged with a GH pod anyway, so
  its designator is not a mitigation for anything. Recorded as residual, not
  "fixed" by moving a label and calling it better.
- next: DRC on the rerouted board, promote the chain, then the full gate battery.

## 2026-07-28 — iterate 2 (the two numbers the user asked for, both MEASURED)

- did: ran the two gates the P0 decisions were supposed to unblock, against the
  regenerated netlist and the new `power_tree.yaml`, before the board finished
  re-routing (neither depends on copper).
- result: **E-TOPO PASSES — the first green E-TOPO on this board since the gate
  learned LINEAR on 2026-07-27.** Verbatim:
  `E-TOPO OK: 1/1 rail(s) topology-correct ... rail '3V3' LINEAR (AMS1117-3.3):
  headroom 1355 mV (Vin_min 4.754 - Vout_max 3.399) vs dropout 1300 mV; PD 615 mW
  ((Vin_max 5.25 - Vout_min 3.201) x 0.3 A) vs rating 1200 mW (51%) -> PASS`,
  exit 0. It carries two OVER-BUILT ADVISORIES (2 A trunk / 2 A fuse vs a derived
  0.3 A need) which are advisory-only and were masked while the rail FAILED —
  they are correct and intentional: the derived need counts only the graded 3V3
  rail, not the 0.15 A coil rail or the 0.02 A STOP rail that share the trunk.
  **THE "59 mV" IS TRACED AND REPLACED.** It is NOT in ORDER_README section 7 —
  it is in the v1.6 `redteam_adversarial.md` section E part 3, echoed at
  CHANGELOG:465. Its terms were 4.850 V minus an ESTIMATED 92 mV of series drop
  (F1 ~34 + Q_REV ~38 + eFuse ~20 mV at ~0.45 A), and **not one of the three had a
  cited maximum anywhere in this tree**. All three now do, and their datasheets
  are COMMITTED to 02_parts/ (Bourns MF-MSMF Series, AOS AO3401A Rev3.1,
  Littelfuse SMBJ Series — the last one so the TVS number the P0 turns on is
  citable at all): F1 R1Max **70.0 mOhm**, Q_REV **73.5 mOhm** (60 mOhm max at
  V_GS -4.5 V/25 C scaled by the datasheet's OWN 50->75 mOhm 25->125 C ratio,
  interpolated to 70 C), eFuse **47.0 mOhm** = **190.5 mOhm**. At 0.50 A that is
  **95.2 mV, not 92**, so V(5V_PROTECTED) = 4.7548 -> declared 4.754.
  **E-INV 115/115 (was 109) and E-ADR 9/9 (was 8/8) — ADR-0021 closes its own
  loop.** SIX new invariants, and ALL SIX RED-VERIFIED this pass, each mutation
  being the specific defect the assert exists to catch, each restored to md5
  `aa1115d218b9dee5d67fc3aa2ffefa55`: R_OVB 26.1k->15k (the P0 value itself),
  R_OVT 100k->57.6k (the refuted lens proposal), the OVLO series_chain re-homed
  from 5V_RPP to 5V_PROTECTED (the eFuse OUTPUT — which would turn a hysteretic
  cutoff into an oscillator while both value asserts stay green), R_WDOKSER
  10k->0 (the "it is only a readback" 0R link), U_EXP.8 back on the raw WD_OK
  (the P0 restored), and R_WDOKSER.1 moved to WD_OK_EXP (the resistor becomes a
  stub). All six exit 1 and NAME the invariant; all six restore to 115/115.
- next: DRC on the rerouted board, promote the chain, full battery, four lenses.

## 2026-07-28 — iterate 3 (first reroute measured DIRTY; the cause is the legalizer, not the router)

- did: DRC'd the first full reroute, diffed the placement against the BLOCKED
  v1.7 board, and fixed the cause rather than re-racing at it.
- result: **DRC 1 violation / 6 unconnected / 3 parity.** The 3 parity items were
  a stale `04_kicad/cooksense.kicad_sch` (the converter writes to
  `03_tscircuit/kicad/`); refreshed -> **parity 0**, and the other two stand:
  * 1 clearance, `TH_CAM_A` vs `ADC_CH4` on B.Cu, **0.1191 mm against a
    0.1200 mm Default rule** — cross-net, 0.9 um short, above the fab floor but
    the gate is 0, not "0 real".
  * 6 unconnected, all pad-or-via <-> pour: GND at `U_WD.2`, `R_AND2PD.2`,
    `R_MODEPD.2`; 3V3 fragmented around `R_FAULTPU.2` / `U_LATCHA.5` /
    `C_AND2.1`. Exactly the plane-pad class route.yaml's reservations +
    seed_stubs exist for.
  **THE PLACEMENT DIFF IS ONE PART, AND THAT ONE PART MOVED A NEIGHBOUR.**
  Measured against `git HEAD:04_kicad/cooksense.kicad_pcb`: 239 -> 240
  footprints, **added `R_WDOKSER`, removed none, and exactly ONE part moved** —
  `TP_3V3` (111.500,70.000) -> (109.000,67.000), **3.905 mm**. Same ripple the
  route commit already recorded twice (C_WD/R_MR 2026-07-24; eight floaters
  re-solved when the eleven ADR-0019 pull-downs landed).
  **AND THE NEW PART ITSELF LANDED 24 mm FROM THE PIN IT PROTECTS.** Left
  floating, `R_WDOKSER` legalized to (112.400, 69.500) while `U_EXP` pad 8 sits
  at (136.500, 82.325). It would function there — 1 uA through 10k — but a
  series ISOLATOR 24 mm from the pin it isolates is a finding, and it is what
  displaced TP_3V3.
  **FIX AT SOURCE, BOTH IN ONE EDIT:** `R_WDOKSER` ANCHORED at (133.0, 82.325),
  3.5 mm due west of U_EXP.8, in measured-clear space (U_EXP courtyard starts at
  x135.275 = 1.33 mm to the 0402's east edge; nearest other body C_STOPINV ends
  at x129.94; OUT of U_EXP's south escape corridor x135.3..144.7). `TP_3V3`
  PINNED at the coordinate v1.6 and the v1.7 staging shipped. **The placement
  delta is now EXACTLY what this revision changed: one added part.**
- next: re-race and re-stitch from the anchored placement, then re-measure. If
  the plane-pad opens survive, they get User.2 reservations + seed_stubs per the
  precedent in route.yaml, not a re-race lottery.

## 2026-07-28 — iterate 4 (the clearance is NOT a race lottery — six candidates, one identical gap)

- did: re-DRC'd after anchoring, then measured the residuals instead of re-racing
  at them.
- result: **1 violation / 4 unconnected / 0 parity** (was 1 / 6 / 3 — the
  anchoring closed two of the opens and the schematic refresh closed parity).
  **THE CLEARANCE IS DETERMINISTIC AND THAT IS THE FINDING.** Two INDEPENDENT
  KRT races, three candidates each, **all six** landed the SAME 0.1191 mm
  cross-net gap at the SAME coordinates: `ADC_CH4` B.Cu (58.410, 84.9687) ->
  (58.021, 85.358) against the `TH_CAM_A` B.Cu stub (59.300, 85.400) ->
  (58.500, 85.400) running into `R_SER0.1`, in the dense MCP3208 filter field.
  Re-derived independently with a segment-to-segment scan over both nets: min
  edge gap **0.1191 mm** — the same number kicad-cli reports, against a 0.1200 mm
  Default rule. **On the v1.6/v1.7-staging board the same two nets are 0.8500 mm
  apart**, so this is not a placement pinch that has always been there; it is
  this route's own artefact, and it is reproducible.
  **ROOT CAUSE, MEASURED: the router's clearance model is ~0.031 mm optimistic
  on a 45-degree crossing.** KRT was routing to a 0.15 mm target and produced
  0.1191. So a re-race is a lottery that has now come up the same way six times,
  and the fix is headroom: `route.common.clearance` **0.15 -> 0.18**, at which
  the same artefact lands at ~0.149. **This is the router's SEARCH clearance, not
  a fab or netclass floor** — nets.yaml still declares 0.12 and DRC still grades
  0.12, so the change cannot launder a real violation.
  **THE FOUR OPENS ARE THE TRAPPED-PLANE-PAD CLASS, and they get the remedy
  route.yaml already uses twenty times**: `R_AND2PD.2` / `R_MODEPD.2` (GND) and
  `R_FAULTPU.2` / `U_LATCHA.5` (3V3). Each got a User.2 reservation rect so ANY
  re-race leaves the site clear, plus a deterministic seed_stub via-in-pad.
  **Sites MEASURED, not guessed**, with the pass's own primitive
  (`pcb_toolkit.via_site_ok`, via 0.25/0.15, clearance 0.13) over a 21x21 0.03 mm
  on-pad grid: 135 / 125 / 284 / 183 legal points respectively; the site taken is
  the one nearest the pad centre in each case (three ARE the centre), and each
  survives a via-growth sweep to 0.25 / 0.27 / 0.87 / 0.61 mm. seed_stubs 61 -> 65.
- next: third full reroute with both changes, then re-measure. If the gap
  survives 0.18 the next lever is placement, not the router.

## 2026-07-28 — iterate 5 (0.18 bought the clearance and PAID for it in coverage)

- did: ran the third reroute at `route.common.clearance` 0.18 and measured the
  race before letting the 25-minute stitch run on it.
- result: **0.18 IS TOO MUCH, and the measurement is clean:** all three
  candidates came back **0 copper violations / 5 UNCONNECTED routed nets**
  (previously, at 0.15, six candidates over two races were all **0 unconnected /
  1 clearance**). The router bought the margin out of coverage. The stitch was
  KILLED rather than run — a 25-minute pour pass on a chain with five open
  signal nets measures nothing, and the killed run's `*.stitch_state.json` was
  removed (the tracked-copy trap this repo has hit before).
  **THE LEVER IS THE WRONG SIZE, NOT THE WRONG LEVER.** The shortfall being
  repaired is **0.0009 mm** (0.1191 against 0.1200). 0.18 adds 0.030 mm — 33x
  the miss. **0.16** adds 0.010 mm, eleven times the miss, and perturbs the
  search by a third as much. Both data points are recorded in route.yaml next to
  the value so the next reader does not re-run either experiment:
      0.15 -> 0 unconnected, 1 clearance at 0.1191   (six candidates, two races)
      0.18 -> 0 clearance,   5 unconnected           (three candidates)
  **CONCURRENCY, deliberately:** the TOPOLOGY red-team lens and the fresh-context
  PIN review were launched against the FINAL NETLIST while the board re-routes.
  Neither grades copper and the reroute cannot change the netlist, so their
  verdicts are valid for the board that comes out — and it takes ~40 minutes of
  wall clock off the critical path. The LAYOUT and RENDER lenses wait for final
  copper, because they DO grade it.
- next: fourth reroute at 0.16. If it lands 0 unconnected AND 0 violations, the
  chain gets promoted and the battery runs. If it splits the difference again,
  the next lever is PLACEMENT in the MCP3208 filter field, not the router.

## 2026-07-28 — iterate 6 (the clearance/coverage trade is 1:3, so stop pulling that lever)

- did: measured the router at three search clearances instead of guessing, and
  NAMED the nets each setting costs.
- result: **THE TRADE CURVE, all on three candidates per point:**
      0.15 -> 0 unconnected, 1 clearance at 0.1191 mm   (six candidates, two races)
      0.16 -> 0 clearance,   3 unconnected
      0.18 -> 0 clearance,   5 unconnected
  Buying 0.0009 mm of clearance costs three routed nets. That is not a clearance
  problem any more, it is an EFFORT problem — so the three opens at 0.16 were
  NAMED rather than treated as noise: **`5V_PROTECTED` x1 (pwr wave),
  `5V_RPP` x1 (efuse wave), `RAIL_EN_B` x1 (sig wave)**, one ratsnest each, on
  ALL THREE candidates. That is the exact "ran out of ripup budget on the last
  net" signature this file already records from task#21 — a different net per
  race would be a hard block; the same one net per wave is a budget.
  **THE `pwr` WAVE HAD NO `max_ripup` AT ALL**, so it could not back out of a bad
  ordering. Fixed at source with the lever the route journal already harvested:
  efuse 50 -> 120 ripup / 0.8M -> 1.5M iterations; pwr NO-BUDGET -> 80 ripup /
  0.5M -> 1.2M iterations; sig 120 -> 170 ripup. Search clearance stays at 0.16.
  Both dirty stitches were KILLED before running (25 minutes each on a chain that
  cannot reach 0) and their `*.stitch_state.json` removed each time.
- next: fifth reroute. The race result is the early read — if it lands 0/0 the
  stitch is worth its 25 minutes; if it does not, the next lever is PLACEMENT in
  the MCP3208 filter field and this stops being a routing problem.

## 2026-07-28 — iterate 7 (put the headroom in the wave that has the problem)

- did: raised the efuse/pwr/sig wave effort and re-raced at 0.16; measured; then
  changed the SHAPE of the fix rather than its size again.
- result: **MORE EFFORT DID NOT RECOVER THE THREE NETS.** efuse ripup 50 -> 120
  and 0.8M -> 1.5M iterations, pwr from NO ripup budget at all to 80 and 0.5M ->
  1.2M, sig 120 -> 170: all three candidates still came back **0 violations /
  3 unconnected**, the same `5V_PROTECTED` / `5V_RPP` / `RAIL_EN_B`. So the cost
  of a 0.16 global search clearance is STRUCTURAL, not budgetary, and the raised
  budgets stay (they cost nothing and the pwr wave having no ripup budget at all
  was a latent defect either way).
  **AND NONE OF THE THREE NETS IT COSTS IS IN THE WAVE THAT HAS THE PROBLEM.**
  `TH_CAM_A` and `ADC_CH4` are BOTH `analog`-wave nets. KRT takes a **per-wave
  `--clearance`** (`_KRT_FLAGMAP` in route_and_stitch_generic), so the headroom
  belongs on that wave and nowhere else: `route.common.clearance` returns to
  **0.15** — where six candidates over two races routed with ZERO unconnected —
  and the `analog` wave alone carries **`clearance: 0.16`**. pwr/efuse/sig never
  see the tighter search. Same 0.010 mm of headroom on the crossing that misses
  by 0.0009 mm, without the three-net bill.
  **ALSO RECORDED, because it is a fact about this tree and not about the
  board:** a CONCURRENT AGENT working other boards swept this board's
  in-progress files into its own commit `d91dfb8` ("archive the four superseded
  boards"), including a MID-REBUILD `04_kicad/cooksense.kicad_pcb` and a stray
  `cooksense.kicad_pcb.kicad_pro` droppings file. Nothing was lost and no sealed
  release was touched (cooksense's `07_releases/` is intact and v1.6 is still
  live), but the seal's own source commit S must therefore also DELETE that
  stray, and a pathspec-scoped commit is only half the discipline — the other
  half is not sweeping `git add -A` across a tree someone else is mid-build in.
- next: sixth reroute, per-wave clearance. Early read is the race verdict.

## 2026-07-28 — iterate 8 (per-wave clearance CLEARED the copper violation; two opens left, both named)

- did: re-raced with `clearance: 0.16` on the `analog` wave ONLY and
  `common.clearance` back at 0.15, then ran the stitch and the full gate.
- result: **DRC 0 violations / 0 schematic parity / 2 unconnected.** The copper
  violation that survived six candidates over two races is **GONE** — the
  headroom went into the wave that owned both offending nets and cost the other
  waves nothing. Race: **0 violations / 1 unconnected on all three candidates**
  (vs 3 at a global 0.16, and 1 clearance at a global 0.15).
  The two survivors, both MEASURED and both named rather than counted:
  * **`TH_PORT_B`**, `R_REF5.2` (51.710, 80.600) to a track at (60.600, 84.200) —
    the ONE routed-net open, the SAME net on all three candidates. That is the
    last-net budget signature INSIDE the wave whose search just got tighter, so
    the budget is the lever: analog ripup **160 -> 230**, iterations 1.5M -> 2.0M,
    probe 100k -> 150k. (The same lever did nothing on efuse/pwr/sig at a global
    0.16, which is how this one is known to be different.)
  * **`3V3` at `U_TC.8`** (65.8625, 78.950) against the C_TCAV.1 stub via at
    (63.220, 80.900) — a plane pad the pour could not reach. **It gets a STUB,
    not a via-in-pad, and the difference is measured: the MAX31856's
    1.475 x 0.400 mm pad has ZERO legal on-pad via sites** (25x25 scan at 0.02 mm
    with `via_site_ok` 0.25/0.15/0.13 — a 0.25 via plus clearance does not fit
    inside a 0.400 mm pad). So: a 0.25 mm F.Cu segment east to (66.162, 78.900),
    the nearest of **160** sites where BOTH the via site AND the whole stub path
    are clear, plus a via there. The `U_EFUSE.4` `segments:` pattern applied to a
    plane pad. seed_stubs 65 -> 66.
- next: seventh reroute. If it lands 0/0/0 the chain is promoted and the battery
  runs.

## 2026-07-28 — start (v1.7 continuation: -13L sweep, silk, rebuild, fresh review battery)

- state at pickup: source is CLEAN and COMMITTED through `3e48d34`; `04_kicad/`
  is STALE (its `cooksense.kicad_sch` still carries
  `cooksense:Relay_StandexDIP_1A_pinout12`, the footprint that no longer
  exists). `07_releases/` untouched; v1.6 still live and DO-NOT-ORDER.
- owed: (A) finish the -12L -> -13L reference sweep, (B) the silk blocker
  (RENDER P0-A / LAYOUT P1-b) plus the newly-un-muzzled P-SILK-FN, (C) rebuild
  + reroute + full battery, (D) a FRESH four-lens review round, (E) seal.
- **-13L sourcing, RE-READ TODAY rather than relabelled.** `assembly.yaml`'s
  `not_assembled` evidence was a DATED 2026-07-25 query keyed on the *-12L*
  code; that evidence does not transfer to a different orderable part. Fresh
  query, same endpoint `jlc_stock_check.py` uses
  (`selectSmtComponentList`), 2026-07-28:
  * keyword `DIP05-1A72-13L` -> **1 hit, C1524853 STANDEXMEDER DIP05-1A72-13L,
    stockCount 0, library `expand`**
  * keyword `C1524853` -> the same single hit, stock 0
  * keyword `DIP05-1A72` -> 5 hits (C1524803 -11D, C1524847 -11L, **C1524853
    -13L**, C1561362 -12L, C1561371 -12D), stockCount **0 on every one**
  * CONTROLS the same minute: `C5620` -> 5414, `C25741` -> 465129. The zeros
    are the library's answer, not a dead field.
  So the `not_in_catalog` disposition SURVIVES the part change on its own
  fresh evidence. The DISTRIBUTOR read is a separate question and is still
  OWED: `manual_quotes.yaml` and `shopping-list-2026-07-27.md` carry Mouser
  876-DIP05-1A72-12L (132) and DigiKey DIP05-1A72-12L-ND (56) — both keyed to
  the *-12L* code, both now inapplicable. Recorded as OWED, not renamed.

## 2026-07-28 — iterate 9 (the -13L sweep landed; E-INV grew 115 -> 136, all RED-verified)

- **A. -12L reference sweep, DONE and it was not a rename.** Config/prose hits
  updated: `floorplan.yaml` (the D7 pitch comment now names the family, not a
  dead code), `policy_waivers.yaml` SILK-OVER-COPPER, `02_parts/README.md` x3,
  `S4B-ZR-SM4A-TF` (the -20..+70 C binding-envelope cross-ref),
  `AQY212GS` (ADR-0006 selector-alternate cross-ref), `03_src/lib/contracts.md`.
  Four things needed JUDGEMENT rather than sed, and all four are recorded:
  * `03_tscircuit/parity_padmap.txt` — the block was a REAL remap
    (tsx 1,2,3,4 -> land 1,7,8,14) written against a land that no longer
    exists. The pinout13 `.kicad_mod` bakes the renumber in, so the map is now
    the IDENTITY. Rewritten as identity WITH the DIP-lead provenance on each
    line, and the change is stated in the block header rather than the old
    lines being quietly relabelled. (The relay lines were always
    tsx_preflight-only tokens, never parity tokens — confirmed against
    `parse_padmap`, which keys on `ref:pin=pad` — so nothing downstream moved.)
  * `02_parts/DIP05-1A72-13L/part.yaml` — its `gotchas:` and `layout.notes`
    STILL CARRIED THE CODE-12 MAP ("coil pins 1/7 vs contact pins 8/14",
    "coil and contact INTERLEAVE ALONG THE PACKAGE", `layout.source` citing
    "code 12"). The `pins:` block had been corrected and the prose around it
    had not — a part dossier that contradicts itself. Rewritten to code 13,
    with the code-12 interleave kept explicitly as HISTORY (it is why the part
    number changed) instead of as a live claim.
  * **The `DIP05-1A72-12D` alternate is WITHDRAWN, and this is a new finding.**
    ADR-0006 approved it as "same pinout, internal diode". That was true of
    -12L and is FALSE of -13L: 12 and 13 are different PIN-OUT CODES, not diode
    options on one code. Fitting a -12D to the v1.7 land would reproduce the
    exact short v1.7 exists to fix. `sourcing.alternates` is now `[]`,
    `assembly.yaml`'s disposition says so, and ADR-0006 carries an amendment.
  * `03_src/lib/contracts.md` also said cooksense "owns exactly TWO" footprints
    while the `.pretty` holds FIVE (the ZIF and the two KF350 terminals were
    vendored later and the contract never caught up). Corrected and all five
    listed; a validate rule was added that grades the relay land by its PAD
    COORDINATES (pads 1/2 at x -3.810, 3/4 at x +3.810), so "is this a code-12
    land" is now answerable from the file instead of from its name.
- ADR-0006 gets an AMENDMENT (not an edit): decision unchanged, pin-out code
  corrected, -12D withdrawn, sourcing consequence stated. ADR-0018/0021 and
  ARCHITECTURE.md had DANGLING PATH citations to `02_parts/DIP05-1A72-12L/`;
  repointed. Every electrical number they rest on (7.5 V max coil, 500 R,
  -20..+70 C, 1.5 kVDC) is a DIP05-1A72 FAMILY fact and is unaffected — checked
  against the datasheet rather than assumed.
- **Schematic stage rebuilt**: 243 components (243 with FPID), 820 pins,
  **199 nets** (was 193 — the five `*_EXP` isolation nets plus `EFUSE_FLT_DIV`),
  converter ERC **0 errors / 663 warnings**, safety-chain spot-check **11/11**.
- **E-INV 115 -> 136** and every one of the 21 new invariants is RED-VERIFIED,
  each mutation being the defect the assert exists to catch:
  * 5 x `part_value <R_*SER> = 10k` mutated to 0R ("it is only a readback") -> RED
  * 5 x `pin_on_net U_EXP.<2..6> = <TERM>_EXP` mutated back onto the RAW
    permission (the delete-the-resistor simplification) -> RED
  * 5 x `pin_on_net R_*SER.1 = <TERM>` mutated to the _EXP side, i.e. the
    resistor becomes a STUB with both other asserts still green -> RED
  * `R_FLTDIVT` 10k -> 100k, `R_FLTDIVB` 22k -> 100k -> RED
  * `R_FLTDIVT.1` off `EFUSE_FLT_N`, `R_FLTDIVB.2` off `GND` -> RED
  * `U_EXP.1` re-wired back to the 5 V `EFUSE_FLT_N` — THE P0-b defect, with
    both resistors still present and still correct -> RED
  * `TP_PGOOD.1` moved onto the DIVIDED tap (the instrument must see the real
    node) -> RED
  21/21. Source netlist md5 `20707e29ab0bdf848f6e8e34603b1424` before and after
  — every mutation ran against a scratch copy.
- **B (silk), PASS C added.** The ownership pass (v1.7) made J_DOOR/J_ESTOP/
  J_MODE own their labels and it structurally could not see the other half of
  RENDER P0-A: the confusing text at the E-STOP housing was never J_DOOR's
  designator, it was **`D_DOOR`** — the flyback diode's — 0.353 mm from J_ESTOP,
  6.411 mm from the diode it names, at h=0.60 against the connectors' 0.45. Pass
  B graded `J_`-prefixed labels against `J_`-prefixed rivals. Pass C is the
  converse and is quantified over EVERY footprint: no refdes of any kind may sit
  nearer a SAFETY connector (J_ESTOP/J_DOOR/J_MODE/J_ISOLOOP) than it sits to the
  part it names, 1.5 mm margin, re-derived over the whole board after all moves.
- next: DRC on the rebuilt board, then the fab/assembly battery, then P-SILK-FN.

## 2026-07-28 — iterate 10 (the race was clean; the STITCH GATE caught a stale pinned coordinate)

- **Reroute race: 3 candidates, `c0/r9`, `c1`, `c2` — ALL THREE 0 unconnected /
  0 violations (CLEAN).** No lottery this time; the per-wave `analog` clearance
  0.16 from iterate 8 held with the six new nets in the netlist.
- **The stitch `gate` pass FAILED, and it failed correctly:**
  `seed_stub 3V3 U_TC.8: REFUSED — via (66.162,78.9) collides foreign copper`.
  The coordinate was measured on the PREVIOUS race's copper (iterate 8) and the
  race is STOCHASTIC — a pinned stub coordinate is only valid against the chain
  it was measured on. `seed_stubs` refused, and the gate REPORTED rather than
  shipping a plane pad the pour never reaches. That is the pass doing its job;
  the defect was mine for not re-freezing the pair.
- **Fix = re-measure AND freeze together.** The winning chain `c0/r9` is
  promoted to `03_src/cooksense/route/final_chain.kicad_pcb`
  (md5 `864a5e8400e0d97ea334817fe27dca09`, carries 12 `pinout13` footprints),
  and the stub is re-derived against THAT board:
  * scan: 141x91 grid at 0.025 mm out to 1.6 mm with the pass's own primitive
    (`pcb_toolkit.via_site_ok`, via 0.25/0.15, hole-to-copper 0.13)
  * **537 legal OFF-PAD sites** with a clear 0.30 mm stub path; chosen
    `(64.9875, 78.950)` — the NEAREST at **0.8750 mm**, COLLINEAR with the pad
    centre (straight west along the pad's own centreline), via-growth margin
    **0.60 mm** i.e. 0.35 mm of slack beyond the 0.25 design
  * it stays a STUB although this route now offers **753 legal ON-PAD sites**
    where the previous route had ZERO: the MAX31856 pad is 0.400 mm wide and a
    0.25 via leaves a 0.075 mm annulus each side — not a margin worth taking on
    a solder pad when 0.875 mm away buys a fully off-pad bond
  * stub clearance at the 0.30 mm design width, REAL-SHAPE: bare
    copper-to-copper **0.3000 mm** against a 0.130 mm DRU floor (2.3x); it
    could widen to 0.64 mm before violating and 0.90 mm before touching. The
    two blockers at that limit are the `U_TC.9` (TC_CS_N) pad and a `TEMP_OK`
    track.
  * **A wrong number is recorded rather than deleted:** the first cut of that
    clearance measurement approximated pads as discs of radius max(w,h)/2 and
    reported `U_TC.9` at **-0.0875 mm** — which reads as a SHORT. It is an
    artefact of treating a 1.475 x 0.400 TSSOP pad as a circle; the real-shape
    collide (which `via_site_ok` had already used to approve the path) says
    0.3000 mm. Circular pad approximations do not belong in a clearance claim.
- Also fixed: `rebuild_all.sh` printed `line 92: fill: command not found` twice
  every run — two `echo "..."` lines contained backticks around `fill`, so bash
  COMMAND-SUBSTITUTED them. Harmless only by luck; a backtick in an echo is an
  execution. Single-quoted.
- next: deterministic rebuild from the promoted chain, then DRC.

## 2026-07-28 — iterate 11 (the silk rule was WRONG TWICE, and the pass said so both times)

RENDER P0-A / LAYOUT P1-b. The fix is a new PASS C in
`03_src/cooksense/fix_silk_placement.py`. It took three statements of the rule
and the two rejected ones are recorded IN THE FILE, because each was caught by
the pass failing loudly rather than by anyone reading it.

- **Cut 1 — "no refdes may sit nearer a SAFETY connector than the part it
  names."** Broad, closed the class, and FAILED THE BUILD:
  `FATAL: no clear silk position for ['R_COILENPD']`. The failure was correct
  and the RULE was wrong. MEASURED: R_COILENPD's own PART sits **4.791 mm** from
  J_MODE because it IS J_MODE's pin pull-down; `C_LATCHB` likewise. Neither
  label is confusable with a harness, so demanding they retreat was tidiness
  enforced at the price of a build, not a safety property.
- **Cut 2 — the TOKEN rule:** a label carrying a safety connector's identity
  token (ESTOP / DOOR / MODE / ISOLOOP) must be NEAREST that connector. Correct
  in kind, and it failed the build again on SIX refs — because it had no
  proximity gate. It reported `R_DOOROKSER` as cross-named at **90.150 mm** from
  J_MODE versus 93.807 mm from J_DOOR. Arithmetically true, meaningless: nobody
  reads a label 9 cm away as belonging to the housing in their hand.
- **Cut 3 — token rule + an 8.0 mm housing radius**, and the number is NOT
  invented for this file: it is `silk_fn_radius_mm`, the radius P-SILK-FN itself
  uses to decide whether a silk text belongs to a part. With it the rule reports
  EXACTLY the two labels the render lens found and nothing else:
  * `D_DOOR`   — 6.227 mm from J_ESTOP vs 9.675 mm from J_DOOR -> moved
    (191.500,73.800) -> (190.250,79.300)
  * `R_DOORPD` — 5.200 mm from J_ESTOP vs 12.041 mm from J_DOOR -> moved
    (191.800,70.900) -> (190.800,77.150)
  `D_ESTOP` was reported by cut 2 and is correctly SILENT under cut 3: it is
  7.048 mm from its own J_ESTOP and 8.016 mm from J_MODE — already nearest the
  right housing, and the foreign one is outside the radius.
- Pass B (ownership) result unchanged and re-verified from the final board:
  J_DOOR 5.483 own vs 7.836 J_ESTOP; J_ESTOP 6.562 vs 8.304; J_MODE 8.097 vs
  18.881 — all OWN THEIR LABEL. Total 6 refdes relocated, 247 verified on-board.
- **RESIDUAL, printed and NOT blocking** (the class stays visible instead of
  being narrowed out of existence): `C_LATCHB` (11.314 mm own vs 6.292 mm
  J_DOOR) and `R_COILENPD` (8.485 mm own vs 6.817 mm J_MODE). Neither carries a
  connector name.
- **`J_ISOLOOP` is still NOT fixed and the omission is still MEASURED**, not an
  oversight — the earlier full sweep found 31 legal positions whose BEST
  achievable lead over J_RH_EXHAUST is **-2.955 mm**. There is nowhere on this
  board where that label wins. It is also not the same hazard class (a KF350
  4-pole screw terminal and a 5-pin GH cannot be cross-plugged). Carried as a
  residual P2 and stated in the CHANGELOG rather than "fixed" by moving a label
  5 mm.
- Reminder for the CHANGELOG: the user chose to leave `silk_edge_clearance`
  OFF, so this whole class remains GATE-LESS at DRC — this deterministic source
  pass is the only thing standing between the generator and a silkscreen that
  points at the wrong connector.

## 2026-07-28 — iterate 12 (DRC found a STALE HAND-COPIED SHEET and 7 trapped plane pads)

First full DRC on the rebuilt board: **0 violations / 6 unconnected / 37
schematic parity**. Both non-zero numbers were real and neither was a routing
failure.

- **37 parity issues = a canon M3 violation that had been sitting in the tree.**
  24 of the 37 were the twelve relays: `cooksense:Relay_StandexDIP_1A_pinout13`
  on the board vs `...pinout12` in the sheet, plus a Value mismatch each.
  ROOT CAUSE: `04_kicad/cooksense.kicad_sch` — the file
  `kicad-cli pcb drc --schematic-parity` actually grades the board against — was
  **never written by any script**. `rebuild_schematic.sh` produced
  `03_tscircuit/kicad/cooksense.kicad_sch` and the netlist and stopped; the
  04_kicad copy had been made BY HAND in some earlier session and then went
  stale the moment the part changed. A hand-copied file in `04_kicad/` is
  precisely what canon M3 forbids. `rebuild_schematic.sh` now publishes the
  sheet as its step 5/5, so the directory is regenerable again.
  **Parity after: 0 issues.** No board change was needed — the board was right
  and the paperwork was stale, which is the failure mode that makes parity worth
  running at all.
- **6 unconnected = 7 TRAPPED PLANE PADS**, and the race is not wrong about
  them: all three candidates reported 0 unconnected because the race grades
  ROUTED NETS, while these are pads the fill fenced off from a plane that
  "already owns" them. Two of the six were pad-to-pad within a pair
  (`C_AND1.1`<->`U_AND1.5`, `C_AND2.1`<->`U_AND2.5`), i.e. BOTH members
  separately fenced — one via each, because bonding one would drop the DRC count
  without the defect going away.
  Remedy = the deterministic via-in-pad this file already uses twenty-odd times,
  every site MEASURED with `pcb_toolkit.via_site_ok` (0.25/0.15, hole-to-copper
  0.13) over the pad's own extent via `pad.HitTest`:
  | pad | net | legal on-pad sites | chosen | via-growth margin |
  |---|---|---|---|---|
  | `R_AND1PD.2` | GND | 335 | PAD CENTRE | 0.65 mm |
  | `C_AND3.2`   | GND | 362 | PAD CENTRE | 0.80 mm |
  | `C_OSV.1`    | 3V3 | 369 | PAD CENTRE | 0.80 mm |
  | `C_AND1.1`   | 3V3 | 280 | PAD CENTRE | 0.50 mm |
  | `C_AND2.1`   | 3V3 | 360 | PAD CENTRE | 0.75 mm |
  | `U_AND1.5`   | 3V3 | 155 | 0.400 mm off centre | **1.00 mm** |
  | `U_AND2.5`   | 3V3 | 465 | 0.349 mm off centre | 0.75 mm |
  The two SOIC-14 pin-5 pads take the best-MARGIN site rather than the NEAREST,
  and the difference is measured: U_AND1.5's nearest legal site has 0.40 mm of
  growth and the chosen one has 1.00 mm, bought with 0.400 mm of offset that
  costs nothing. The growth margin is quoted on every row on purpose — a site
  legal by 0.00 mm is a site the next reroute takes away, which is exactly how
  the U_TC.8 stub went stale two iterations ago.
- seed_stubs 66 -> 73.

## 2026-07-28 — iterate 13 (DRC 0/0/0 and the full battery; ONE red, and it is honest)

- **DRC `--severity-all --refill-zones --schematic-parity`: 0 violations /
  0 unconnected / 0 schematic parity.** seed_stubs 73 pins served, 0 refused.
- Fab / assembly battery, every number measured against the STAGED archive at
  `06_build/staging/cooksense-v1.7/` (never under 07_releases — an unsealed
  archive there makes itself the live release and reddens t1_fleet_regrade
  fleet-wide):
  | gate | result |
  |---|---|
  | export_jlc_package | **exit 0** — gerbers 11 layers + drills, zip 13 files, BOM 59 lines (3 uncoded), CPL **210** parts |
  | A-ROT | **OK, all 210 CPL rotations sourced** (measured per-LCSC row or 180-symmetric footprint) |
  | F-LEGIBLE | **59/59** BOM lines carry a resolved MPN + human-readable Comment; bom_legibility **OK, 58 checks** |
  | bom_source_check (staged BOM) | **PASS** — every BOM LCSC == source; coverage leg C 27/27 |
  | jlc_stock_check | **VERDICT: PASS**, 56/56 coded lines at stock >= 5x qty; 3/59 uncoded and not graded |
  | jlc_twin | **211 OK / 475 rows**, rotation-fitted 211, **bodies mounted 210/210** |
  | twin_overlay (A-RENDER) | **OK** — see the resolution note below |
  | part_facts_check (P-FACT) | **OK**, 5 asserts graded, 1 DEFERRED (LTV-817 keepout, needs geometry the checker lacks) |
  | audit_board | **PASS** — 18 polarity, 28 proximity, 13 edge; **I-ISO 6.22 mm** (>= 6.0), I-OUT 0.35 mm, 0 strip intruders |
  | placement_gates | **PASS** 0 fails / 0 warns; P-OUT 0.30 mm, P-CAP ratio 0.29 (fail > 0.5) |
  | count_parity --board cooksense | **S-COUNT PASS 4/4** over **243** refdes (board / circuit.json / kicad_sch / netlist all == manifest) |
  | E-INV | **136/136** (was 115), all 21 new RED-VERIFIED |
  | E-ADR | **9/9** |
  | E-TOPO | **PASS** — 3V3 LINEAR headroom 1355 mV vs dropout 1300; PD 615 mW vs 1200 (51%) |
  | policy_audit --board cooksense | **FAIL=1, WAIVED=5, PASS=25, HUMAN=6, N-A=4** |
- **A-RENDER needed the KNOWN gate defect worked around, and the workaround was
  RE-VERIFIED not assumed.** At `jlc_twin`'s hard-coded 1600x1000 the overlay
  reported `OVERLAY FAIL: 1 unfaithful (U_LDO, centre 1.25 mm)` +
  `1 resolvable-but-unmeasured (Q_SWDRVRHA)` — the same two refs, the same way,
  as the last revision: `MIN_BODY_PX = 20` is an ABSOLUTE pixel floor while the
  tolerance is in mm. Re-rendered at **3200x2000**: **OVERLAY OK, all 53
  measurable bodies within 1.00 mm, 0 unfaithful, 0 unmeasured**, coverage
  53/212 measured, 159 unresolvable, 247 courtyards drawn. Still owed to
  `skills/` (this agent may not edit it): the pixel floor should scale with the
  render, or jlc_twin should not hard-code its render size.
- **P-SILK-FN: FAIL -> WAIVED, with a measurement, and the waiver is scoped to
  23 named refs.** The gate's default pattern was widened from `^(J|F|TP)[0-9]`
  to `^(J|F|TP)([0-9]|_)` upstream, taking this board from 1 graded ref to 31 —
  and it then failed on 23. It was measured before it was waived: **23 of 23
  carry a VISIBLE refdes ON SILK at >= 0.45 mm** (13 at 0.60, 3 at 0.45,
  strokes 0.13-0.15, at or above the fab legibility floor); **NONE** is
  illegible; **11 of 23 literally name a net the part touches**
  (TP_WDOK->WD_OK, TP_TEMPOK->TEMP_OK, TP_TCDRDY->TC_DRDY_N, J_DOOR->DOOR_RAW,
  J_TC->TC_NEG_IN, ...) and the other 12 name a FUNCTION, which is the correct
  thing for a connector to be called. The check only inspects board-level
  PCB_TEXT and structurally CANNOT SEE footprint reference text, so its premise
  — opaque `J1`/`TP7` designators needing a separate caption — is inverted on
  this board. It is not a blanket pass on connector silk: the hazard it exists
  to catch is graded here by `fix_silk_placement.py` passes B and C, which DID
  fail this revision and DO fail the build.
- **The ONE remaining FAIL is M-BOM, and it is the gate being right.**
  `policy_audit` grades M-BOM against the LATEST SEALED RELEASE, which is still
  v1.6. PROVEN by reading both files rather than asserting it:
  | ref | v1.6 SEALED BOM | v1.7 STAGED BOM |
  |---|---|---|
  | `R_COILENPD` | merged into 100k `C25741` | **680R `C137948`** (the ADR-0018 series element) |
  | `R_OVT` | merged into 100k `C25741` | **100k `C270658`** (the +-0.5% code-pinned setpoint) |
  | `R_OVB` | 15k `C25756` | **26.1k `C407739`** (the ADR-0021 OV setpoint) |
  | `J_MODE` | GH `C189896` | **ZH `C485354`** (the cross-plug fix) |
  Every one of those four IS a v1.7 change, and `bom_source_check` against the
  STAGED v1.7 BOM returns PASS. M-BOM is reporting "the live release no longer
  matches source" — true, and the reason to seal. It must re-read clean against
  the sealed v1.7; that is a post-seal check, not a waiver.
- next: four FRESH review lenses (curated input), then the 2-commit seal.

## 2026-07-29 — finish (SEAL BLOCKED: the fresh battery found TWO new P0s, neither of them the relay)

Four zero-context lenses, launched concurrently against the rebuilt board, input
CURATED (`journal/`, `learnings/`, `STATUS*.md`, `08_reviews/` withheld from all
four). Full dispositions in `08_reviews/DISPOSITIONS.md` under "v1.7b".

| lens | verdict |
|---|---|
| pin review (FRESH LENS) | **FAIL** — 1 blocking, 8 questions |
| render | **DO-NOT-ORDER** — 1 P0, 4 P1s |
| topology / protection / ratings | **ORDER-OK-WITH-NOTES** — 0 P0, 2 P1s |
| layout / thermal / PI / DFM | **ORDER-OK-WITH-NOTES** — 0 P0, 4 P1s |

**BOTH HEADLINE v1.7 CLAIMS SURVIVED, and that is the good news.** The relay
land is CORRECT — two lenses independently rendered DS p.3 at 400 dpi, counted
FOUR leads on sub-figure 13, and confirmed from the netlist that the coil and
contact node sets are DISJOINT (min coil-to-contact pad distance 8.032 mm over
48 pads); the render lens added that the land is CHIRAL, so a relay cannot even
be inserted backwards. The >=6.0 mm isolation claim MEASURES **6.2200 mm** by an
independent method (pours FILLED, which `audit_board.py:154` deliberately
excludes — canon M1 satisfied), and the intra-package coil<->contact gap
IMPROVED 6.1200 -> 6.3494 mm because staggering the coil column puts the gap on
a diagonal. ADR-0002's isolation claim went from FALSE to TRUE.

**AND THEN THE BATTERY DID ITS JOB ON MY OWN WORK.** Both P0s are v1.7 changes,
and one of them is a fix I wrote this session:

1. **PIN-P0-1 / TOPO P1-1 — the divider I added is arithmetically wrong, and
   TWO lenses found it by different routes.** `EFUSE_FLT_N` is an open-drain
   node whose ONLY driver-high is `R_PG` = 100k. The chain is therefore
   100k + 10k over 22k — ratio **22/132, not 22/32** — and the tap sits at
   **0.833 V** against MCP23017 V_IH(min) 2.640 V / V_IL(max) 0.660 V: the
   indeterminate band. **The readback is degenerate — the pin is protected and
   dead**, and `TP_PGOOD`, which I deliberately left on the raw node "so the
   instrument sees the real node", now rests at 1.212 V, making that rationale
   false as built. THE ARITHMETIC WAS IN MY OWN `why:` TEXT: I wrote
   "22k/(10k+22k) x 5.25 = 3.609 V ... still marginal" and treated a node behind
   100k as a stiff 5 V source. I even flagged it as marginal and did not follow
   the thought. **And E-INV, 136/136 with 21 fresh RED-verified mutations, went
   green on it** — because every assert checks that the divider EXISTS, not that
   the level WORKS. That is the lesson worth keeping: a topology invariant
   cannot catch an arithmetic error, and RED-verifying 21 of them does not make
   the 22nd exist.
2. **RENDER-P0-1 — `J_ISOLOOP` has no artwork at the terminal, and the reason I
   didn't fix it was WRONG.** No text inside its silk body, no pole legend
   (0 of 4), its own designator 1.300 mm from `J_RH_EXHAUST` against 4.900 mm
   from itself. `fix_silk_placement.py` and iterate 11 of this journal both
   record that it CANNOT be fixed — "31 candidates, best lead -2.955 mm", "the
   SE corner is saturated, nearest site 33.6/41.9 mm away". **That did not
   reproduce.** The lens rebuilt the sweep under the same stated constraint set
   and found `ISO 30V` fits at (189.05, 93.35), **6.46 mm** from the block, with
   ~6x3 mm of blank silk immediately west of it. I carried a measured
   "impossible" across sessions and repeated it in a journal entry instead of
   re-measuring it. That is the inherited-defect pattern this repo exists to
   stop, and I reproduced it in the same session in which I wrote a commit
   message about not reproducing it.

**AND THE SILK PASS ITSELF SHIPPED A DEFECT.** Both red-team lenses independently
measured that six designators — `J_ESTOP`, `J_DOOR`, `J_MODE`, `D_DOOR`,
`R_DOORPD`, `D_COILEN` — carry a **0.130 mm stroke** against 0.150 on the other
243 texts, below the tier floor, the board's own `min_text_thickness`, and this
project's own `SILK-TEXT-THICKNESS` waiver. Cause: `fix_silk_placement.py`'s
`max(0.13, sz*0.2)` at sz=0.45. **Those six are EXACTLY the refs passes B and C
exist to fix** — the pass that repairs the safety labels made them the thinnest
silk on the board. Worse, the `P-SILK-FN` waiver I wrote THIS SESSION asserts
that 0.13-0.15 is "at or above the floor". It is not; that sentence is wrong and
is recorded as wrong rather than quietly edited.

DECISION: **NOT SEALED.** `07_releases/` is untouched; v1.6 and every release
back to v1.0 remain DO-NOT-ORDER (they carry the pinout-12 land) and carry NO
`SUPERSEDED.md`, because nothing supersedes them yet. The staged archive stays
at `06_build/staging/cooksense-v1.7/` where it cannot make itself the live
release. PIN-P0-1 is not the agent's to close: with `R_PG` at 100k there is no
R_top > 0 solution, so it is a design choice between moving the pull-up to 3V3
(and deleting both resistors) and re-sizing the network — recorded with both
options quantified rather than picked.

What IS committed is sound and self-consistent: the -13L sweep, the corrected
part dossier and ADR-0006 amendment, the identity padmap, the contract fixes,
the silk ownership + cross-name passes, the 7 plane bonds, the re-derived U_TC.8
stub, E-INV 136/136, and a board that measures **DRC 0/0/0** with the full fab
battery green. `04_kicad/` was built FROM this source; nothing is stale.

---

## 2026-07-29 — v1.7 unblock: the three P0s, and two more "impossible"s that were not

**START.** Inherited state: the relay defect FIXED and proven (DIP05-1A72-13L,
pin-out code 13, coil/contact node sets disjoint at 8.032 mm over 48 pads,
keypad<->SELV barrier 6.2200 mm with pours filled), board DRC 0/0/0, whole fab
battery green, `07_releases/` untouched, v1.0-v1.6 DO-NOT-ORDER. THREE blockers
left, each now with a machine-checkable definition of done.

### FIX 1 — the dead fault readback (PIN-P0-1 / TOPO P1-1). CLOSED.

`E-INV` was RED on exactly one assert and that red was the acceptance test:

```
node_level (ADR 0022): EFUSE_FLT_DIV reads 0.833 V at U_EXP.1, required
logic high against V_IH(min) 2.640 V — 5.000 V via 5V_PROTECTED through
110k [R_FLTDIVT=10k + R_PG=100k] over 22k [R_FLTDIVB=22k] -> 0.833 V
```

The user's chosen fix, applied in `03_tscircuit/src/cooksense.tsx`: **`R_PG`'s
top end moves from `5V_PROTECTED` to `3V3` and BOTH divider resistors are
deleted.** `R_FLTDIVT`, `R_FLTDIVB` and the net `EFUSE_FLT_DIV` no longer exist;
`U_EXP.1` and `TP_PGOOD` sit directly on `EFUSE_FLT_N`. Recorded as **ADR-0022**
(`01_docs/decisions/0022-the-efuse-flag-lives-on-3v3.md`) with the no-solution
proof: at `R_PG` = 100k, 5 x R_b/(100k + R_t + R_b) >= 2.64 needs R_b >= 111.9k
AND R_t ~ 0, so no R_top > 0 solution exists.

MEASURED after the fix, from the gate and not from the argument:

```
node_level (ADR 0022): EFUSE_FLT_N reads 3.300 V at U_EXP.1 —
3.300 V via 3V3 through 100k [R_PG=100k], no resistive path to GND
-> pulled to the rail, 3.300 V     (V_IH(min) 2.640 V)
E-INV OK: 136/136        E-ADR OK: 9/9
```

**FIVE NEW ASSERTS, ALL RED-VERIFIED** on a scratch copy (source netlist md5
`5bc8eaf9225b5b551fca3b4872dd21b2` identical before and after), each mutation
being the defect the assert exists to catch:

| mutation | what fired |
|---|---|
| `R_PG.2` 3V3 -> 5V_PROTECTED | `pin_on_net R_PG.2` — and NOT `node_level`, which reads 5.000 V and still passes `logic_high`. Recorded: `node_level` grades a LOGIC LEVEL, not an abs-max. The rail assert is the abs-max guard and they are different claims |
| `R_PG.1` off `EFUSE_FLT_N` | `pin_on_net` + `UNREACHED node_level` (no resistive path to any rail) |
| `U_EXP.1` -> GND | `pin_on_net` + `node_level` receiver-on-wrong-net |
| `TP_PGOOD.1` -> 3V3 | `pin_on_net` |
| `R_PG` 100k -> 10k | `part_value` |

**AND A CHECKER DEFECT FOUND WHILE LANDING IT, worth more than the fix.**
`electrical_invariants.yaml` line 1 declared `supplies: {5V_PROTECTED: 5.0,
N3V3: 3.3}` — the TSX author-prefix form. **No net named `N3V3` exists in the
netlist**; the converter strips the N. So the 3V3 rail was INVISIBLE to every
`node_level` grade and the checker's rail search had one rail where it should
have had two. It did not misreport the divider (that network genuinely hung off
5V_PROTECTED) but it would have reported UNREACHED on this fix. Found by reading
the netlist, not by any gate. Corrected to `3V3: 3.3`.

Also closed PIN Q-1 in the same edit: every document in the P0-b work called
`U_EXP` pad 1 "GPA0". It is **GPB0**; GPA0 is pad 21 and carries `RAIL_EN_A`, an
OUTPUT. Copper was always right.

### FIX 2 / FIX 3 — the silk pass, and THE SECOND UNREPRODUCED MEASUREMENT

The fix list said the "SE corner is saturated, nearest site 33.6/41.9 mm"
justification did not reproduce, and that a re-run found `ISO 30V` at
(189.05, 93.35), 6.46 mm from the block. **THAT NUMBER DOES NOT REPRODUCE
EITHER.** Re-measured with a body-aware obstacle set (pads +0.16, silk +0.08,
every footprint BODY +0.05 — silk under a mounted block is silk nobody reads):

* (189.05, 93.35) at h 0.60 is blocked by `U_OPTO`'s body AND graphics AND by
  `J_RH_EXHAUST`'s body; at h 0.45 still blocked by `J_RH_EXHAUST`. The clear
  band there is U_OPTO bottom 92.86 -> J_RH_EXHAUST top 93.73 = **0.87 mm**, and
  a 0.45 mm text needs a 0.92 mm box. The site does not exist.

So THREE sessions have now carried a "nearest site" number on this corner
without re-deriving it, and the third was mine to inherit. The remedy is that
the number is now PRODUCED BY THE PASS at every run instead of being written in
`floorplan.yaml`.

**What was actually blocking it was not geometry.** It was `C_LATCHB`'s and
`U_OPTO`'s designators, parked in the only channel first-come-first-served by
the generator's de-collider. With a **hazard-caption reserve** armed around the
block BEFORE any label is placed (PASS D0), `ISO 30V` places at
(190.750, 86.500), h 0.600 / stroke 0.150, **0.561 mm from the block body** —
against a recorded "impossible" of 33.6 mm and an inherited 6.46 mm.

Honest residuals, reported by the pass rather than dropped from its list:
`NOT SELV` and the pole legend have **no site within 8 mm** (nearest 11.086 mm)
— the block affords exactly one caption. And a legend BESIDE EACH POLE is
genuinely impossible and now says so precisely: the poles sit at x = 195.30 and
the KF350 body spans x[191.57, 199.22], so the pads are at the CENTRE of the
block in x and every square millimetre either side of a pole is under the
moulding once it is fitted. The pole map therefore rides the north-stack
sentence, in pole order: `POLES 1=C 2=LOOP 3=LOOP 4=E`.

**FIX 3 — the stroke floor, and the floor moved.** `fab_tiers.yaml` used to
declare `min_silk_text_height: 0.45` AND `min_silk_stroke: 0.15`, which KiCad
makes unsatisfiable (stroke <= 0.25 x height, so 0.45 mm text carries at most
0.1125 mm). ADR-0007 set `min_silk_stroke` to **0.1125** with the corollary that
JLC's published 0.150 needs >= 0.60 mm text. So the pass now enforces two
different things:

1. EVERY silk text: stroke = 0.25 x height **exactly**. Not `max(0.13, sz*0.2)`.
   29 refdes stored 0.150 on 0.45 mm text — a number KiCad prints at 0.1125.
   Making the file say what the plotter does is the point.
2. EVERY SAFETY text: h >= 0.600, hence stroke 0.150 — JLC's published floor.

The safety class is enumerated FROM A RULE and printed every run: the four
safety connectors, every label printed within 8.0 mm of a safety housing, and
the ADR-0018 interlock parts. **10 members.** A first cut used a name-token rule
and swept in 27 including `C_STOPR` and `R_MODEHWSER` — pull-downs nobody reads
under stress; scoped to the property instead.

Three things had to be learned to make it satisfiable, each recorded in the
file: heights are raised FIRST (a first cut ran after the ownership passes and
`D_COILEN` / `J_ESTOP` / `R_COILENPD` had NO legal 0.60 mm position left);
safety labels may EVICT non-safety designators, because a 0402's reference does
not outrank the label a human reads while landing a harness (every eviction is
printed with the victim's before/after); and among candidates that already clear
the ownership margin the pass takes the NEAREST, not the largest lead — sorting
on lead put `J_DOOR` 9.708 mm from J_DOOR to win a +3.617 mm it did not need.

Also corrected, because a false waiver is how the next one gets believed: the
`P-SILK-FN` waiver's claim that 0.13-0.15 mm is "at or above the floor" and its
"SE corner saturated / 41.9 mm" line, plus the `SILK-TEXT-THICKNESS` waiver's
"0.15mm stroke = JLCPCB's silk floor". All three are struck through in
`03_src/cooksense/rules/policy_waivers.yaml` WITH the replacement measurement.

### THE REBUILD, AND FOUR THINGS THAT ONLY A REAL RE-RACE FINDS

`rebuild_all.sh --reroute` was run **six times**. The first five failed loudly,
which is the point of a fail-loud pass, and each failure was a different real
defect rather than the same one:

1. **`fix_silk_placement` PASS D0 evicted a label and it came straight back.**
   `D_DOOR` was evicted from the J_ISOLOOP hazard-caption reserve, the
   radius-sorted ladder put it 0.5 mm away still inside the reserve, and
   `ISO 30V` then had no site at 11.086 mm. An eviction that does not FORBID
   the band it evicts from is not an eviction. `forbid=` added.
2. **An evicted victim had nowhere to go.** `J_ESTOP` displaced `R_MODEPD`;
   `R_MODEPD` had no legal slot even at a 10 mm leash and the pass died. A
   priority rule that can strand its victim is unsound, so eviction now
   requires a MOVABILITY PROBE — a dry run of the same search for the victim,
   restored afterwards — as a PRECONDITION of the candidate.
3. **Ordering, twice.** Connectors-before-the-rest was not enough: within the
   connectors, tuple order gave `J_DOOR` its slot before `J_ESTOP` looked, and
   J_ESTOP has **ZERO** free 0.60 mm positions clearing the 1.5 mm ownership
   margin once the captions and the void pass have taken theirs. Both the
   height pass and the ownership pass are now MOST-CONSTRAINED-FIRST, with the
   scarcity measured and printed (`J_ESTOP=0, J_DOOR=1, J_MODE=24`).
4. **The 1.5 mm ownership margin is not affordable at 0.60 mm text.** It was
   measured when the safety designators were 0.45 mm high; a 0.60 mm box needs
   78% more area. Rather than trade a real legibility gain for a real ownership
   gain and get neither, the demand now steps down 1.5 -> 1.0 -> 0.5 -> 0.1 and
   the pass PRINTS the margin it actually obtained. **A positive lead stays
   mandatory.** `J_ESTOP` landed at a degraded 0.5 mm demand with a measured
   **+0.659 mm** lead; `J_DOOR` +3.087 mm; `J_MODE` +10.685 mm.

Then the ROUTE found three more, all of the same family and all only visible
because the netlist changed:

5. **`seed_stub 3V3 U_TC.8: REFUSED — collides foreign copper.`** `route.yaml`
   had already PREDICTED this in its own comment ("a site legal by 0.00 mm is a
   site that the next reroute takes away — which is exactly how the U_TC.8 stub
   went stale"). Predicting a failure twice and not reserving against it is the
   same class of miss as an unexecuted claim. The stub PATH now carries the
   User.2 reservation every via site already had, x[64.40,66.60] y[78.60,79.50],
   with y0 clipped to 78.60 off U_TC.9's pad.
6. **Three more TRAPPED PLANE PADS** — DRC read 0 violations / 0 parity and
   **3 unconnected**: `Q_SWDRVB.2` [GND] vs the F.Cu GND zone, `U_TC.5` [3V3]
   vs a 3V3 via, `U_LATCHB.5` [3V3] vs `C_LATCHB.1`. Deterministic bonds, not a
   re-race: re-racing changes WHICH pads are trapped, not THAT pads are trapped.
   **AND THE SITE-CHOICE METHOD IS CORRECTED**: sites are now picked by MAX
   GROWTH, not by proximity to the pad centre. The nearest legal site for
   `Q_SWDRVB.2` (0.140 mm off centre) and for `U_TC.5` (0.020 mm) both scored
   **growth 0.00** — legal by nothing, i.e. exactly the site the file warns the
   next reroute takes away. Re-scored by slack the same pads give 0.75 and 0.20.
7. **And then one more, exactly as route.yaml's own note warned:** bonding
   `U_LATCHB.5` alone left the pair unconnected TO EACH OTHER. DRC went
   3 -> 1 and the survivor was `C_LATCHB.1`. One via per FENCED PAD, not per pair.

### GATES — the sixth rebuild, exit 0

```
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity
   0 violations / 0 unconnected / 0 schematic parity
E-INV            136/136          E-ADR 9/9
E-TOPO           PASS  (headroom 1355 mV vs dropout 1300; PD 615 mW / 1200, 51%)
audit_board      PASS  18 polarity / 28 proximity / 13 edge / 245 silk
                       I-ISO 6.22 mm, I-OUT 0.35 mm (J_DOOR.MP)
placement_gates  PASS  0 fails 0 warns; P-OUT 0.30 mm, P-CAP ratio 0.29
count_parity     S-COUNT PASS 4/4 over 241 refdes   (--board cooksense)
export_jlc       exit 0; A-ROT 208/208 sourced; F-LEGIBLE 59/59 + 58 checks
bom_source_check PASS (every BOM LCSC == source), leg C 27/27
ERC              0 errors / 417 warnings
SILK             250 texts: 0 below the 0.1125 tier floor, 0 storing a stroke
                 KiCad would clamp away, 11/11 safety texts at h0.600/0.150
J_ISOLOOP        'ISO 30V' 0.085 mm from the block body; 'NOT SELV' 7.892 mm
```

`count_parity` went 243 -> **241** and `03_tscircuit/manifest.yaml` was edited to
match — the manifest is the AUTHOR's declared intent, so deleting two parts from
the design without deleting them from the manifest would have been the gate
working correctly.

### TWO GATES ARE NOT GREEN, AND BOTH ARE REPORTED RATHER THAN WAIVED

* **`policy_audit` FAIL=1 / WAIVED=5 / PASS=25 / HUMAN=6 / N-A=4.** The single
  FAIL is `M-BOM`, and it is the same non-defect as last session: M-BOM grades
  the LATEST SEALED release's BOM (v1.6) against current source, and source has
  moved. PROVEN not asserted: `bom_source_check` run directly against the
  STAGED v1.7 BOM returns **PASS — every BOM LCSC == source**, 210 coded refdes,
  leg C 27/27. It resolves at the seal.
* **`jlc_stock_check` FAIL — and this one is NEW and REAL.**
  **`C506653` MCP23017-E/SS (`U_EXP`) reads stockCount = 0.** 55/56 coded lines
  clear the 5x floor; this one has nothing. Last session the same gate read
  56/56 PASS, so this is a live change, not an inherited number. It is a
  SOURCING blocker, not a design defect, and it does not change the verdict
  below — but the board cannot be assembled by JLC while its GPIO expander has
  no stock.

## THE VERDICT: **v1.7 IS NOT SEALED, AND THE REASON IS A NEW P0**

### TOPO P1-2 ESCALATES TO P0 — the reed coils are not guaranteed to close hot

The carried finding was that the pull-in margin is computed NOWHERE and might go
negative. **It is computed now, and it does go negative.** The ULN2803A datasheet
(SLRS049G) is COMMITTED to `02_parts/ULN2803ADWR/` (sha256
`84ec37810a5cef7c352a320852a6b21bdbe709d2fb60b4d6e7ad6d93ec324a4d`), with an
honest provenance deviation registered in `02_parts/README.md`: **every ti.com
URL for this part 404s** while a sibling dossier's TI URL returned 200 the same
minute, so it came from a mirror — verified TI-origin by PDF metadata
(`Author "Texas Instruments, Incorporated [SLRS049,G]"`, TopLeaf compositor) and
cross-checked byte-for-byte against a SECOND independent host, differing only in
the auto-generated package-addendum date stamp.

The EC table specifies V_CE(sat) only at 100/200/350 mA — two orders above the
~7 mA coil — so **Figure 1 (p.5) was digitized at 900 dpi** against its own
gridlines: 0.629-0.674 V at 10 mA. Three figures are carried, each labelled for
what it is: **0.67 V** Fig.1 typ, **0.88 V** derived worst case (typ x the EC
table's own worst max/typ ratio 1.30 — NOT a datasheet guarantee), **1.10 V**
hard monotonic bound (the 100 mA MAX).

The reference temperature is **20 °C, not 25 °C** — the Standex footnote sits
under a table headed "Coil Data (at 20°C)". So
`V_PI(T) = 3.500 x (1 + 0.004 x (T - 20))`, and with the rail floor
`5V_KEY_RELAY` vout_min = 4.740 V:

| T | V_PI | margin @0.67 typ | @0.88 w-c | @1.10 bound |
|---|---|---|---|---|
| -20 °C | 2.940 V | **+1.130** | +0.920 | +0.700 |
| +25 °C | 3.570 V | **+0.500** | +0.290 | +0.070 |
| +50 °C | 3.920 V | **+0.150** | **-0.060** | -0.280 |
| +70 °C | 4.200 V | **-0.130** | **-0.340** | -0.560 |

**NEGATIVE AT +70 °C ON THE TYPICAL DRIVER DROP, and from +50 °C up on the
worst case.** Re-derived independently by the lead and agreeing to the digit:
V_PI(70) = 3.5 x 1.2 = 4.200; 4.740 - 0.67 - 4.200 = -0.130.

The current view is the SAME fact, not a second derate: 0.4 %/K IS the copper
tempco, pull-in is an ampere-turn condition so `I_PI = 3.5/500 = 7.00 mA` and is
temperature-independent, while delivered current FALLS as the coil heats —
9.64 / 7.98 / 7.29 / **6.81** mA at -20/+25/+50/+70 °C. At +70 °C
**6.81 mA < 7.00 mA must-operate.** Both views agree. Hot is worst in both terms
at once, and **-20 °C is comfortable, so a bench test at room temperature will
not find this.**

`K_STOP` is the one relay NOT exposed, and the review's number reproduces
exactly: it is not on a Darlington but on a dedicated 2N7002 off the ungated
`5V_STOP`, margins +1.714 / +1.084 / +0.734 / **+0.454** V. Caveat recorded
because it is the same class of gap: the 2N7002 datasheet is ALSO not committed,
so its 0.10 V V_DS is an estimate — not load-bearing (even at 0.50 V the +70 °C
margin is +0.054 V) but it should be cited before anyone leans on it.

**Twelve reed relays on a cooking appliance are not guaranteed to close at the
top of the board's own declared envelope. That is a P0 and it blocks.** The
remedy — raise the coil rail, drop the driver saturation (a MOSFET array instead
of a Darlington), or narrow the declared envelope — is a TOPOLOGY DECISION and
is deliberately NOT made here, exactly as the `R_PG` rail choice was not.

### THE FRESH REVIEW BATTERY IS OWED, NOT SKIPPED

Four fresh lenses were NOT run this session, and the reason is stated rather
than elided: a confirmed P0 already blocks the seal, and closing it will change
the power tree or the coil driver — a MATERIAL change that needs its own
battery. Running four lenses now would grade a board that must change again and
spend the battery twice. It is OWED against whatever revision fixes the coil
margin, and this entry is the record of that debt.

### WHAT IS COMMITTED AND SOUND

ADR-0022 and its five RED-verified asserts; the `supplies:` netlist-name fix;
the silk pass with its stroke floor, hazard-caption reserve, movability probe
and measured orderings; the J_ISOLOOP artwork at 0.085 mm; three corrected
waivers; the corrected `floorplan.yaml` "no silk site" claim; the U_TC.8 stub
reservation; four trapped-plane-pad bonds chosen by slack; the committed
ULN2803A datasheet and the two `electrical:` blocks; and a board that measures
**DRC 0/0/0** built entirely from `03_src/` + `03_tscircuit/`.
`07_releases/` is UNTOUCHED. v1.0-v1.6 remain DO-NOT-ORDER.

### DETERMINISM PROVEN, not assumed (canon M3)

The winning chain `06_build/route/race/c0/r9.kicad_pcb` was promoted to
`03_src/cooksense/route/final_chain.kicad_pcb`, and `rebuild_all.sh` was then
run in its DEFAULT (promoted-chain, no race) mode from that source alone:

```
DET_REBUILD_EXIT=0
DRC: 0 violations / 0 unconnected / 0 schematic parity
E-INV 136/136 · S-COUNT 4/4 over 241 · audit_board PASS (I-ISO 6.22 mm)
placement_gates PASS · silk 250 texts / 0 under floor / 11-11 safety at 0.600/0.150
J_ISOLOOP: 'ISO 30V' 0.085 mm, 'NOT SELV' 7.892 mm
```

The board file's md5 differs between the two builds (`e5565da5…` vs
`17cfca47…`) and that is expected and NOT a determinism failure: KiCad mints
fresh UUIDs and timestamps on every save. Per `tests/README.md` the assertion is
on PROPERTIES, never on bytes — and every graded property reproduced exactly.

## 2026-07-29 16:20 — iterate (v1.8: ADR-0023 part swap, full battery, NOT SEALED)
- did: rebuilt from source after the ADR-0023 coil-driver swap and the C558584
  sourcing fix, then ran the fab/assembly battery. `rebuild_schematic.sh` then
  `rebuild_all.sh` — **the DEFAULT deterministic path, NOT `--reroute`**, and
  that is a deliberate deviation with a measurement behind it: `git diff` on
  `03_tscircuit/verification/converter_netlist.net` is 245 insertions / 245
  deletions of which exactly **THREE are semantic** —
  `(value "C9683")`x2 -> `C165895` and `(value "C506653")` -> `C558584`. Every
  other changed line is a tstamp/uuid. The NET SET, the pin membership and both
  footprints are byte-identical, and `rebuild_all.sh`'s own header says
  `--reroute` is for "when placement/nets change". Neither did. Rerouting a
  frozen net set would have discarded the promoted authoritative chain
  (`03_src/cooksense/route/final_chain.kicad_pcb`, canon M3) and replaced it
  with a fresh stochastic draw for no gain. The promoted chain is therefore
  UNCHANGED and needs no re-promotion.
- result: **DRC 0 violations / 0 unconnected / 0 schematic parity**
  (`--severity-all --refill-zones --schematic-parity`, exit 0,
  `06_build/proof/drc_v18.rpt`). E-INV **140/140** (was 136/136 — four new
  ADR-0023 asserts). E-ADR 9/9. E-TOPO PASS (headroom 1355 mV vs dropout
  1300 mV; PD 615 mW / 1200 mW, 51%). audit_board PASS (18 polarity /
  28 proximity / 13 edge / 245 silk, I-ISO 6.22 mm, I-OUT 0.35 mm, 4 hw holes).
  placement_gates PASS 0 fails 0 warns (P-OUT 0.30 mm, P-CAP 0.29).
  count_parity **S-COUNT PASS 4/4 over 241 refdes**. contracts_audit 0
  violations in its graded scope, and the two NEW paths
  (`02_parts/TBD62083AFWG/`, `01_docs/decisions/0023-*`) draw ZERO findings even
  under `--projects`. M-BEACON PASS 2/2.
  FAB: export_jlc_package **exit 0, A-ROT OK all 208 CPL rotations sourced,
  F-LEGIBLE OK 59/59**; bom_legibility 58 checks OK (F-MPN row 57
  `C165895 = TBD62083AFWG` resolves out of the new dossier); bom_source_check
  **PASS** (leg C 27/27, 210 coded refdes); jlc_twin **209 OK / 471 rows,
  bodies mounted 208/208**; ERC 0 errors / 658 warnings on the grid sheet;
  A-POS 208 rows on the pad-array centre, worst **0.00000 mm**.
  *** THE BLOCKER-2 GATE IS NOW GREEN: jlc_stock_check **PASS, verdict line
  parsed, 56/56 coded BOM lines >= 5x qty**, 3/59 uncoded and not graded
  (`06_build/proof/stock_v18.json` `"verdict": "PASS"`). C165895 stock 2334,
  C558584 stock 7490. *** THINNEST line is C2653844 TPS259573DSGR at **103**
  (qty 1) — clears the floor 20x over but it is the one to re-read before an
  order.
  TWO GATES NOT GREEN, BOTH UNCHANGED PRE-SEAL STATES, NEITHER A v1.8 DEFECT:
  policy_audit FAIL=1 / WAIVED=5 / PASS=25 / HUMAN=6 / N-A=4 — the FAIL is
  M-BOM, and it is grading `07_releases/cooksense-v1.6-2026-07-27/fab/bom.csv`,
  which still contains **C9683**; measured directly, the fresh v1.8 BOM has
  ZERO occurrences of C9683 and bom_source_check on it PASSES. Resolves at the
  seal. assembly_coverage A-POP FAIL=1, `MANIFEST-UNDECLARED` — the release
  MANIFEST carries no `not_assembled:` line; a release-paperwork item, the same
  "expected pre-seal" finding recorded on 2026-07-28.
  ROTATIONS, MEASURED NOT INHERITED (canon A-ROT): the export BLOCKED on the two
  NEW codes, correctly. `jlc_rotation_measure.py` against the JLC cached models
  with the pcbnew-verified operator:
    C165895 SOIC-18W: offset **270**, pad-number rms **0.1500 mm** vs 8.1344
      next best (0/180 both 8.1344, 90 11.5027) = **54x**;
    C558584 SSOP-28: offset **270**, rms **0.0403 mm** vs 6.1624 = **153x**.
  Both are byte-identical to the rows their predecessors (C9683, C506653) carry
  — which they MUST be, same board footprint and same JLC model file — and the
  point of measuring rather than copying is that the identity is a RESULT.
  Both DECLARED `single-channel` (dual-row packages are their own 180
  reflection, pad cloud degenerate at 90/270, no size-class channel, pin-1
  marking not admissible) so both oblige the JLC order-preview human gate, as
  their predecessors do. The two paste-ready rows are in
  `06_build/proof/rotation_rows_v18.csv`. **THEY ARE NOT LANDED**: the ledger
  is `skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv` and this agent may not
  edit `skills/`, so the clean export was proven through the resolver's OWN
  `JLC_LCSC_ROTATIONS` env override pointing at a copy. This is the ONE item
  outside the `projects/smc0985-cooksense/` pathspec, and A-ROT will block again
  until it lands.
- next: the fresh four-lens review battery (deliberately NOT run — a separate
  scoped job), the manifest `not_assembled:` line, the two rotation rows, and
  the seal. See the node_level entry below before anyone calls the margin done.

## 2026-07-29 16:35 — iterate (the coil-margin node_level: RED/GREEN PROVEN, NOT LANDED)
- did: authored the ADR-0007 `node_level` assert that turns the reed pull-in
  margin from a table in an ADR into a machine check, and RED-verified it.
  The form (also in ADR-0023):

      - assert: node_level
        net: COIL_U1_N
        receiver: K_U1.2            # DIP05 pad2 = COIL_B, the driven end
        driver_state: contended
        aggressor: K_U1.1           # the coil, pulling UP to 5V_KEY_RELAY
        defender: U_ULNA.18         # the DMOS channel, pulling DOWN
        must_be: logic_low
        adr: "0023"

  `v_il_max: 0.540` on the DIP05 dossier's pad 2 is **THE PULL-IN BUDGET, not a
  logic threshold**: node <= 0.540 V  <=>  coil sees >= 4.740 - 0.540 = 4.200 V
  = V_PI(+70 C). The equivalence is exact. Aggressor r_on = 540 ohm (the coil's
  MINIMUM hot resistance, 450 x 1.20 — minimum is the worst case for the
  driver's share); defender r_on = 6.50 ohm (2x the 25 C EC max).
- result: MEASURED, against `06_build/netlists/cooksense.net`:
  | driver dossier fact | node at K_U1.2 | vs 0.540 V budget | verdict |
  |---|---|---|---|
  | TBD62083AFWG, r_on 6.50 ohm hot bound | **0.056 V** | -0.484 V | **PASS** |
  | ULN2803A worst case, 0.88 V / 7 mA = 125.7 ohm chord | **0.895 V** | +0.355 V | **FAIL** |
  | ULN2803A TYPICAL, 0.67 V / 7 mA = 95.7 ohm chord | **0.714 V** | +0.174 V | **FAIL** |
  So the assert reproduces the whole finding from the netlist plus two dossiers,
  and it fails on the TYPICAL Darlington drop as well as the worst case. (The
  Darlington is modelled as a CHORD resistance at the operating current — exact
  for the DMOS, a linearization for the Darlington, and stated as such: it is
  the REJECTED part, and the check's job is to grade the chosen one.)
  *** IT IS NOT IN `electrical_invariants.yaml`, AND THE REASON IS A CHECKER
  GAP, NOT A DESIGN DOUBT. *** `_load_part_electrical()` joins a dossier to a
  netlist component through `sourcing.lcsc` + `sourcing.alternates` — i.e.
  through an LCSC CODE. The twelve reed relays are SELF-SUPPLIED: JLC stocks
  none of them, so K_U1's netlist `value` is the MPN `DIP05-1A72-13L` and NO
  LCSC code identifies it. Run against the shipped checker the same assert
  returns, verbatim:
      UNREACHED node_level (ADR 0023): receiver K_U1.2 (code 'DIP05-1A72-13L')
      declares no input thresholds — add an `electrical:` block to its 02_parts
      dossier. Reported UNREACHED, not passed (canon M-COVER)
  — and note the message BLAMES THE DOSSIER, which does have that block with
  those thresholds. Committing it would take E-INV from 140/140 to a red gate on
  a limitation rather than a defect.
  REJECTED WORKAROUND, recorded so nobody re-proposes it: writing
  `DIP05-1A72-13L` into the relay's `sourcing.alternates:` forces the join in
  one line. That field means "pin-compatible substitute"; this relay is
  DO-NOT-SUBSTITUTE (spec 15.4) and its own note already records an alternate
  WITHDRAWN for being a different pin-out code. Making a gate green by writing
  something false into a dossier is the failure mode this repo keeps paying for.
  PROPOSED SKILLS PATCH (4 lines, `skills/kicad-pcb/scripts/`
  `electrical_invariants.py`, in `_load_part_electrical`, before the `lcsc`
  append) — this is what the GREEN column above was measured with:
      if d.get("mpn"):                   # a SELF-SUPPLIED part has no LCSC code,
          codes.append(str(d["mpn"]))    # so the netlist `value` that identifies
                                         # it is its MPN.
  It is not a cooksense workaround: ADR-0007's own worked example is "reed coil
  pull-in margin at 70 C", so the kind was DESIGNED for this case and the join
  is what cannot reach it. Class width: every self-supplied / hand-solder part
  in the fleet is outside `node_level`'s reach today.
  THE OTHER KNOWN PATCH LANDED WHILE THIS SESSION RAN, upstream and wider than
  proposed: commit fa22228 hardened `encoding="utf-8-sig"` at **all 124 read
  sites across 29 files in three skills**, not just the `bom_source_check.py`
  line that crashed — and in the same commit made `supplies:` reject a rail
  DECLARED but absent from the netlist. Re-verified against it here: E-INV still
  **140/140** (this board's `supplies: {5V_PROTECTED, 3V3}` both resolve).
  So the owed patch list is the MPN join above, plus the two schema/regex
  findings recorded in the next entry.
- next: land the 4-line join patch, then move the assert out of ADR-0023 into
  `03_src/cooksense/rules/electrical_invariants.yaml` and re-run the RED verify
  in place. Until then the margin is proven but not gated, and that distinction
  belongs in the seal paperwork.

## 2026-07-29 16:55 — iterate (I BROKE THE LIVE RELEASE BY TIDYING UP, and the test suite caught it)
- did: ran `tests/run_tests.sh` as the backstop after the swap. **755 passed,
  1 FAILED** — `t1_fleet_regrade.py :: regrade_confirms_the_clean_boards_are_clean`:
      smc0985-cooksense cooksense-v1.6-2026-07-27 is the LIVE release and
      F-LEGIBLE fails it.
  Reproduced directly against the sealed BOM:
      FAIL F-MPN row 56 (U_ULNA,U_ULNB): LCSC C9683 resolves NO MPN from any
        authority (41 code(s) from 02_parts + 151 from the ledger)
      FAIL F-MPN row 39 (U_EXP): LCSC C506653 resolves NO MPN from any authority
  **BOTH WERE MINE, AND BOTH FROM THE SAME MISTAKE: `02_parts/` IS THE MPN
  AUTHORITY FOR EVERY RELEASE, INCLUDING SEALED ONES.** I deleted
  `02_parts/ULN2803ADWR/` citing the contract's "rejected candidates never get a
  committed PDF", and I moved `MCP23017-E-SS`'s `sourcing.lcsc` from C506653 to
  C558584. C9683 and C506653 are in the BOM of SIX SEALED RELEASES. The contract
  line is about candidates that were NEVER USED; a part that SHIPPED is a
  different class, and deleting its dossier makes a sealed release ILLEGIBLE
  RETROACTIVELY. Nothing about the current board was wrong — this is a
  history-legibility defect, and it is exactly the shape of the thing the
  release-freshness gates exist to catch.
- result: FIXED, and both fixes are recorded where the next person will stand.
  (1) `02_parts/ULN2803ADWR/` RESTORED, with a header block, `superseded_by:
  TBD62083AFWG` and `on_live_board: false`, and a README register row that says
  DO NOT DELETE and why. (2) The MCP dossier's `alternates:` moved from the BARE
  LIST form `[C506653, C47023]` to the MAPPING form
  `[{lcsc: C506653, mpn: MCP23017-E/SS}, ...]` — **the form is load-bearing, not
  style**: `bom_legibility_check.py` reads alternates as `{lcsc:, mpn:}` and
  SILENTLY SKIPS bare strings, so the bare form this file had always carried
  resolved NOTHING (C47023 was latently unresolvable too; it just was not in any
  BOM). RE-MEASURED: sealed v1.6 BOM **F-LEGIBLE OK 56/56**, fresh v1.8 BOM
  **F-LEGIBLE OK 58 checks**, `t1_fleet_regrade.py` **5 passed / 0 failed**,
  E-INV still 140/140, bom_source_check still PASS, part_facts P-FACT OK,
  contracts_audit 0 violations in its graded scope.
  SCHEMA DIVERGENCE FOUND ON THE WAY, and it is a third proposed patch:
  `bom_legibility_check.py` reads `sourcing.alternates` as MAPPINGS while
  `electrical_invariants.py::_load_part_electrical` reads the SAME field as BARE
  STRINGS. One field, two incompatible readings, and each one silently ignores
  the other's form. The 02_parts contract's example shows the bare form
  (`alternates: [C2650259, C3188678]`), i.e. the contract documents the form
  that F-LEGIBLE cannot read.
  FOURTH PROPOSED PATCH, found while re-greening the beacon:
  `status_beacon_check.py`'s `_SEALED_RE = re.compile(r"sealed", re.I)` matches
  the substring, so `stage: NOT-SEALED-REVIEW-OWED` + a `step:` reading "IS NOT
  SEALED" was graded as CLAIMING a completed seal of v1.8 and FAILED
  M-BEACON-REL. A beacon that explicitly disclaims a seal must not be read as
  claiming one; the pattern needs a negation guard (or to key off `stage:`
  tokens rather than a substring). Worked around here by rewording to
  `PRE-SEAL-REVIEW-OWED`, which is a WORKAROUND and should not stand as the fix.
  CROSS-AGENT HAZARD, RECORDED BECAUSE IT COST ME THE RESTORE: my `git rm` of
  the ULN dossier sat STAGED while another agent committed, and commit 85e4d28
  (pluto-cal-switch) swept it in — the very defect d917ca7's own message
  records ("`git add -- <path>` does not scope `git commit`"). The restore had to
  come from `git checkout 95e6c01 -- <path>`, not from the index. **Do not leave
  anything staged in a shared tree.**
- next: unchanged — four-lens battery, two rotation rows, the node_level join
  patch, manifest line, seal.

## 2026-07-29 17:10 — start (SEAL RUN: the fresh four-lens battery, the carried items, and v1.7)
- did: read CLAUDE.md, SKILL.md stage 7 + the seal ritual, design-policies.md,
  STATUS-cooksense.md, DISPOSITIONS_v1.7.md, CHANGELOG's DO-NOT-ORDER banner,
  ADR-0023 and 57044c0/95e6c01/de58693/9f516e4. Confirmed the three skill
  landings this run depends on: **both A-ROT rows ARE in
  `jlc_lcsc_rotations.csv`** (C165895 -> 270 rms 0.1500 vs 8.1344; C558584 ->
  270 rms 0.0403 vs 6.1624, both `single-channel`, both naming the JLC
  order-preview human gate).
- **FIRST FINDING, BEFORE ANY GATE RAN: `06_build/fab_v18/` — the payload I was
  told to stage from — IS A 2-LAYER EXPORT OF A 4-LAYER BOARD.** It holds 11
  gerbers and its zip holds 11; `cooksense-In1_Cu.g1` and `cooksense-In2_Cu.g2`
  are ABSENT. The board's own layer stack (`04_kicad/cooksense.kicad_pcb` line
  10) declares `F.Cu / In1.Cu / In2.Cu / B.Cu`, sealed v1.6's `fab/` ships 13
  gerbers including both inner layers, and `06_build/fab_v17/` ships 13 too.
  `export_jlc_package.py --layers` defaults to 4, so fab_v18 was invoked with
  `--layers 2`. Staging it would have shipped a 4-layer design to JLC with no
  inner copper in the zip: both GND/3V3 planes and every plane-bond via's
  destination silently gone. Not staged. Re-exporting at `--layers 4`.
- next: DRC re-measure from the committed board, re-export the fab payload,
  stage the archive, then launch the four fresh-context lenses against it.

## 2026-07-29 17:30 — iterate (THE COMB SLOTS WERE A REAL P0, AND THE COIL MARGIN IS NOW GATED)
- **P0-SLOT — SETTLED AGAINST JLC'S OWN CAPABILITY PAGE, AND FIXED.** The fourth
  carried sighting was correct and it was never a risk assessment.
  jlcpcb.com/capabilities/pcb-capabilities, read 2026-07-29 (twice, and
  corroborated by an independent search): **"Min. Non-Plated Slots: 1.0mm"** —
  "The minimum Non-Plated Slot Width is 1.0mm, please draw the slot outline in
  the mechanical layer(GM1 or GKO)". The twelve comb slots were 0.600 mm, i.e.
  **40% under the fabricator's published floor**, and the same page adds
  "Rectangular holes and slots without rounded corners are not supported", which
  a 1.0 mm bit satisfies by construction and a 0.6 mm feature does not.
  MEASURED FREE FIRST, then changed: at the new 1.000 mm band the nearest copper
  item on any of the four layers with pours filled is **2.8500 mm** (north,
  2.5500 at r11r12 to trk RSTOP_MID) and **2.7300 mm** (south, to the K_* contact
  pads), where JLC asks 0.200 mm. Both comb keepout families already spanned the
  widened bands (north 23.2-29.4, south 46.9-52.9), and widening a void only
  LENGTHENS a surface path, so every creepage derivation stands unchanged.
  Widened symmetrically about the same centre-lines: y26.0-26.6 -> **y25.8-26.8**,
  y49.3-49.9 -> **y49.1-50.1**. VERIFIED IN THE BOARD, not just the source: the
  Edge_Cuts horizontal set is now [10.0, 25.8, 26.8, 48.8, 49.1, 49.8, 50.1,
  102.0] — the H4 notch (48.8-49.8) was already 1.000 mm and is outline geometry
  anyway. Full from-source rebuild, **DRC 0 violations / 0 unconnected / 0
  schematic parity** (`06_build/proof/drc_v20.json`).
  RECORDED, NOT FIXED: the WEST end pocket slot leaves a **1.00 mm web** to the
  board edge while the file's own comment justifies skipping the EAST end pocket
  as "<3mm to the board edge, web too fragile" — a self-contradiction. JLC
  publishes no remaining-wall minimum (their Q&A #176 asks exactly this and is
  UNANSWERED), so there is no number to measure against; carried to ORDER_README
  as a DFM query rather than a silent outline change.
  COST OF THE CHANGE, stated: the silk lost one designator slot —
  refdes-on-silk 235/241 with **6** waived to F.Fab (was 5). Generator output,
  regenerated deterministically, and the assembly drawing still carries all six.
- **THE COIL-MARGIN ASSERT IS LANDED AND RED-VERIFIED IN PLACE.** Eleven
  `node_level` asserts in `03_src/cooksense/rules/electrical_invariants.yaml`,
  one per DMOS-driven reed. **E-INV 140/140 -> 151/151.** RED verify
  (`06_build/proof/einv_red_verification_coil_margin.txt`): putting the
  superseded Darlington's drop back as its equivalent resistance at the same
  7.0 mA coil current — 0.670/0.007 = 95.7 ohm and 0.880/0.007 = 125.7 ohm —
  gives **E-INV FAIL 11/151 at 0.714 V** and **FAIL 11/151 at 0.895 V**, both
  against the 0.540 V pull-in budget, exit 1 each time; restored, GREEN again,
  dossier byte-identical after (`diff` clean). The two numbers reproduce the
  hand computation to the millivolt.
  ONE DEFECT FOUND WHILE LANDING IT, and it would have made ten of the eleven
  asserts quietly optimistic: only pad **"18"** of the TBD62083AFWG dossier
  carried the hot-corner `r_on_ohm_max: 6.50`; every other output pin would have
  fallen back to `defaults.r_on_ohm_max: 3.25`, the **25 C** figure. All eleven
  driven channels now declare 6.50 explicitly (canon M-WIDTH).
  ALSO CORRECTED: the count is **TWELVE** reed relays (K_U1-6, K_D1-4, K_PRESS,
  K_STOP), not thirteen as this journal, the beacon and ADR-0023 all say. Eleven
  hang off the two arrays; K_STOP is on a 2N7002 and is EXCLUDED BY NAME.
- **A-RENDER (twin_overlay) HAS NEVER BEEN RUN ON THIS BOARD, AND ITS FIRST RUN
  FAILED FOR A REASON THAT IS NOT THE BOARD.** At jlc_twin's own render size
  (1600x1000 = **8.34 px/mm** on a 188 mm board) it reported FAIL on `U_LDO`
  (centre delta **1.248 mm**) and `Q_SWDRVRHA` "should have been measurable and
  was not" (13 body px against a floor of 20). Re-rendered at 4800x3000 =
  **15.3961 px/mm** and re-run: **exit 0, 53 measured / 210, ZERO
  resolvable-but-not-measured**, `U_LDO` **0.111 mm** and `Q_SWDRVRHA`
  **0.086 mm** (872 px). Both failures were EXTRACTION artifacts of an
  under-resolved render, and the proof is a re-measurement at 1.85x, not an
  argument. The U_LDO signature said so before the re-run: three edges within
  0.68 mm and the LEAD side alone off by 1.87 mm, i.e. gull-wing leads on silver
  pads classified as pad rather than body. **PROPOSED SKILL PATCH (new, not one
  of the two already owed): `twin_overlay.py` should REFUSE or loudly warn below
  a px/mm floor, and `jlc_twin.py`'s hard-coded 1600x1000 is too coarse for
  A-RENDER on any board over ~120 mm.** A gate whose verdict flips with the
  resolution of its input must say so.
  Bottom side: overlay correctly REFUSED (nothing on B.CrtYd, 245 courtyards on
  the other side) — single-sided assembly, so A-RENDER bottom is N/A by
  construction and is named rather than skipped.
- MEASURED, unchanged: stock **PASS 56/56**, thinnest line C2653844 TPS259573DSGR
  still at **103** on a fresh read. Twin **209 OK / 471 rows, bodies 208/208**,
  exit 0. Export **A-ROT OK 208/208**, **F-LEGIBLE OK 59/59**, A-POL single-channel
  10 codes -> the order-preview human gate. K_STOP's own margin re-derived from
  the rail rather than inherited: 5V_STOP vout_min **4.754** V, so +70 C margin is
  **+0.454 V** at the estimated 0.10 V V_DS and **+0.054 V** even at 0.50 V.
- next: stage the archive from `06_build/fab_v20/`, then the four fresh lenses.

## 2026-07-29 18:05 — iterate (P-SILK-OWN'S FIRST RUN CAUGHT A REAL MISLABEL, AND A SILK CAPTION NAMED A NET THAT DOES NOT EXIST)
- **A 30 V POLE LEGEND WAS PRINTED 0.161 mm FROM A SENSOR CONNECTOR.** The new
  P-SILK-OWN row reported `J_RH_AMBIENT: silk '1C2L3L4E' 13.841 mm own vs
  J_RH_EXHAUST 6.210 mm`. Re-measured EDGE-to-EDGE: the token — J_ISOLOOP's
  four-pole legend for the NOT-SELV 30 V terminal — sat **0.161 mm from
  `J_RH_EXHAUST`**, a 5-pole JST-GH humidity header, against 5.512 mm from the
  part the gate attributed it to. As printed it reads as that connector's pin
  legend: four pole letters beside a five-pole sensor header.
  ROOT CAUSE, and it is a rule that was never written: `fix_silk_placement.py`
  bounded each hazard caption's distance to **its own part** (`ISO_MAX_GAP_MM`
  8.0) and tested NOTHING about the other parts nearby, so 7.960 mm from the
  block was "legal" by its own rule. It now REJECTS any candidate site where
  J_ISOLOOP is not the nearest connector/fuse/test-point, and the token takes the
  block's existing "DOES NOT FIT ... reported, not dropped" path: after the
  rebuild it prints `nearest legal site inf mm away` — there is NO owned site
  anywhere near that corner, which is the honest answer. The information is
  carried IN FULL and SELF-IDENTIFIED by the north-stack caption
  "J_ISOLOOP (SE CORNER) = ISOLATED 30V CONTACTOR LOOP -- NOT SELV -- POLES
  1=C 2=LOOP 3=LOOP 4=E". Two methods, no shared code, same finding.
- **THE SILK PRINTED `GND_ISO ONLY` — A NET THAT DOES NOT EXIST.** The keypad
  caption read "KEYPAD ISOLATION COMB >=6mm creepage **GND_ISO ONLY** (contact
  columns face pockets)". `grep -c GND_ISO` on the netlist is **0**; the only
  ISO-bearing net name on this board is `SPI_MISO`, matched by substring. Same
  ghost as `supplies: {N3V3: 3.3}`, except this one was printed ON THE PRODUCT:
  an integrator was told to bond the isolated keypad domain to a net nobody
  authored. Corrected to **NO GND BOND** — one character shorter, so the pinned
  caption's bbox cannot displace a neighbour. The truth it now states is the
  design: the isolated keypad domain has NO ground, which is what makes the
  1.5 kVDC reed barrier mean anything.
- **THE SAME GHOST WAS IN `parity_padmap.txt`, AND IT IS WHY A GATE HAS BEEN
  FAILING SINCE BEFORE v1.6.** The file said J_KEY_MATRIX's two MP tabs are
  "reflowed to GND_ISO". MEASURED: they carry NO net; every one of the eight
  OTHER connectors' MP tabs is on `GND`; and the netlist authors an `MP` node for
  all eight and NOT for J_KEY_MATRIX — a decision, not an omission. It has to be:
  J_KEY_MATRIX is the only connector on the ISOLATED side of the reed barrier, so
  reflowing its shell tabs to the SELV plane would short the isolated domain to
  SELV at the one connector that carries the isolated nets off-board. **The board
  is right and the document was wrong.** MEASURED consequence of floating tabs
  (pours filled, four layers): nearest SELV-net copper **19.407 mm** (other tab
  28.181) against a >= 6.000 mm requirement, 39.975 mm to any plane; nearest
  netted neighbour is a keypad-domain track at 0.450 mm, same domain.
  `kicad_sch_parity.py` therefore reports **1/169 nets FAIL** on the single
  `('J_KEY_MATRIX','MP')` no-connect — and it reports the IDENTICAL finding
  against **SEALED v1.6** (1/161), so it is inherited, not new. Dispositioned
  with those numbers, not waived; it is a checker gap (a mechanical pad unbonded
  BY DESIGN has no way to say so).
- **P-SILK-OWN: waived, with a measurement the gate does not make.** The other
  five entries are artifacts of the gate's CENTROID-to-text metric on large
  bodies. Re-measured box-EDGE-to-EDGE: J_ISOLOOP OWNS 'ISO 30V' by **+0.499 mm**
  (0.561 vs J_DOOR 1.060) where the gate saw 9.641 vs 7.844; TP_RKEY owns the
  keypad caption by **+2.406 mm** (0.000 overlap vs 2.406); TP_USEL ties
  **1.304/1.304** on the BOARD TITLE; TP_PGOOD's nearest caption '5V SELV IN' is
  correctly F1's (1.008 mm — F1 is the input polyfuse ON that rail);
  J_RH_EXHAUST owns none, its nearest being J_ISOLOOP's 'ISO 30V' at 6.661 mm
  against the true owner's 0.561 — an 11.9x lead. All five measured on this
  board today, by a method independent of the gate's.
- **W-FOREIGN, and it was cooksense's own inherited-waiver flag.**
  `waiver_provenance.py` FAILED the S-OCCL waiver for naming crow-mic-pod-v2 with
  no `derived_from`. The waiver's EVIDENCE is native (77 sites at 12 px/mm on this
  board's own schematic), so `derived_from: [crow-recorder-central-v2,
  crow-mic-pod-v2]` is DECLARED with a note that only the waiver CLASS is
  inherited — the citation is a real precedent and deleting it to green a gate
  would have been the worse move. Scoped verdict now **PASS, 12/12 waivers, all
  independently reasoned**. The remaining fleet FAIL is
  crow-recorder-central-v2's own S-OCCL, a SIBLING board — reported, not touched.
- **A REPRODUCIBILITY MEASUREMENT, INCLUDING MY OWN WRONG FIRST READING.** Two
  exports of the SAME board file first looked NON-deterministic; that was MY
  measurement error — I stripped `Created by KiCad` and not the second timestamp,
  `%TF.CreationDate`. With BOTH stripped, two exports are **BYTE-IDENTICAL on all
  eleven gerbers**. What IS real: rebuilding from source with a SILK-ONLY source
  delta moved copper by **11 D01 vertices on F.Cu and 4 on B.Cu** (In1/In2
  order-only, F_Mask / Edge_Cuts / pastes byte-identical, CPL and BOM identical) —
  a zone-fill tie-break in the refill. So the pipeline is SEMANTICALLY
  reproducible and not BYTE-reproducible across runs, and the MANIFEST will say
  so rather than imply otherwise.
- MEASURED after the silk fix: DRC **0/0/0** (`06_build/proof/drc_v21.json`),
  E-INV **151/151**, E-ADR **9/9**, audit_board PASS (I-ISO 6.22 mm, I-OUT
  0.35 mm), placement_gates PASS 0/0, S-COUNT **4/4 over 241**, twin **209 OK /
  471 rows, bodies 208/208** exit 0, A-RENDER hires **exit 0, 53 measured / 210,
  0 resolvable-but-unmeasured**, export **A-ROT 208/208** + **F-LEGIBLE 59/59**,
  F-LEGIBLE on the staged bytes **OK 58 checks**, bom_source_check **PASS** (leg C
  27/27 over 59 rows), P-FACT **OK 5/5 graded, 0 unreached**, rotation table
  **OK 64 rows**, stock **PASS 56/56** with `stock_check.csv` a REAL map (56 rows,
  `mpn` column, ZERO blank MPNs on coded rows), ERC 0 errors. policy_audit
  **FAIL=1 / WAIVED=6 / PASS=22 / HUMAN=6 / N-A=9** — the one FAIL is M-BOM
  grading SEALED v1.6's BOM against current source (it names C506653 for U_EXP,
  which is v1.6's code), and it is expected to clear when v1.7 becomes the
  resolved release. That will be PROVEN at the seal, not predicted.
- next: re-stage from `06_build/fab_v21`, join the four lenses, then the seal.

## 2026-07-29 18:20 — finish (THE BATTERY IS RUN AND IT BLOCKS; v1.7 IS NOT SEALED)
- did: joined all four fresh-context lenses. **render DO-NOT-ORDER (2 P0),
  topology DO-NOT-ORDER (0 P0 / 7 P1 / 13 P2), layout DO-NOT-ORDER (7 P1, one
  order-blocking), pin FAIL (0 pin-map FAILs, 2 evidence-grade FAILs, connector
  group owed and requested).** Ledger with every number:
  `08_reviews/DISPOSITIONS_v1.7.md` section "2026-07-29 (third)".
- result: **NOT SEALED, ON PURPOSE.** Two order-blockers, neither fixable after
  fabrication and neither a paperwork item:
  (1) LABEL OWNERSHIP on cross-mateable safety connectors — `J_ISOLOOP` printed
  0.161 mm from `J_RH_EXHAUST`, `J_ESTOP` tied at 0.161 mm to `J_DOOR` (same
  part, C189896), `J_DOOR` nearer `D_DOOR`. Same defect as v1.7's RENDER P0-A,
  marked FIX REQUIRED, and the ownership pass that landed does not reach these
  refs — the generator says so itself, 56 degraded. Cause is PLACEMENT DENSITY,
  so it is a floorplan change and a re-race. NOT attempted here: it would spend
  the battery a third time, and that is exactly the trap the last two sessions
  avoided.
  (2) **NO CAPACITOR ANYWHERE ON THE eFUSE INPUT SIDE** (`5V_IN`/`5V_FUSED`/
  `5V_RPP` = zero caps; `C_IN1`/`C_IN2` are on the OUTPUT), and the `keep_short`
  budget written to hold it local is addressed to `5V_SELV`, WHICH IS NOT A NET
  ON THIS BOARD.
  THE GHOST-NET CLASS IS NOW MEASURED AT FULL WIDTH, and it is the third
  instance in two sessions: walking every `net:`/`nets:`/`vdd_net:` key in
  `03_src/cooksense/rules/*.yaml` + `02_parts/*/part.yaml` against the netlist's
  412 nets, **10 of 123 referenced names (8%) DO NOT EXIST** — `5V_SELV`, `+5V`,
  `3V3_DIGITAL`, `HS_GATE`, `LED_DRIVE`, `N3V3`, `OPTO_LED`, `RCEXT`, `T_MINUS`,
  `T_PLUS`. Some are datasheet-side placeholders rather than board claims, and
  THAT IS THE POINT: nothing distinguishes a placeholder from a ghost, so a dead
  budget is indistinguishable from a satisfied one. Proposed as a gate.
- **`07_releases/` WAS NEVER TOUCHED.** The candidate lived at
  `06_build/staging/cooksense-v1.7/` for the whole pass, where it cannot make
  itself the live release. CHANGELOG banner rewritten to say without ambiguity
  that all SIX sealed releases are DO-NOT-ORDER and that v1.7 is a CANDIDATE
  that never sealed — the previous wording ("v1.0 THROUGH v1.6") invited the
  reading that something newer was good.
- next: ONE deliberate revision pass, in this order — the eFuse input capacitor
  (schematic/BOM), then the SE-corner placement so the four cross-mateable GH
  headers and the KF350 own their designators (consider whether the real fix is
  four IDENTICAL 5-pin headers becoming not-identical), then the two pinned
  captions off `Q_SWDRVA`/`TP_RKEY.1` pads, then declare the operating AMBIENT
  (no junction temperature on this board can be closed without it) and re-open
  the LDO tab copper with it. Then re-race, re-gate, and run the battery AGAIN.

## 2026-07-29 18:30 — finish (the connector group came back, and it is a THIRD blocker with a known fix shape)
- did: the pin lens's `Connectors` group had been left *pending*; requested and
  delivered. It found the mis-plug MECHANISM, and I re-derived it from the
  netlist rather than accept it: `J_DOOR` pin 4 is `DOOR_RAW`, while on the
  IDENTICAL `J_RH_*` pods pin 4 is `SCL_*` and on the identical `J_ESTOP` it is
  GND. A pod harness in `J_DOOR` therefore lands a PULLED-UP I2C clock on
  `DOOR_RAW`, held only by `R_DOORPD` 10k. **The lens said 1.650 V; it is worse
  than that, twice over.** `U_SCHM` pin 14 is on **3V3**, not 5 V, so the
  applicable SCLS085L V_T+ MIN is BELOW the 4.5 V row's 1.55 V; and this board's
  own I2C pull-ups are **2.2k**, giving 3.3 x 10/(10+2.2) = **2.70 V**. A
  conforming HC14 reads the door **CLOSED with no door attached.** `J_DOOR` pins
  2 and 4 are ONE net, which is independently why the topology lens found EOL
  supervision unimplementable — same wiring, two directions.
  **ADR-0018 CLOSED THIS EXACT CLASS on `COIL_EN_IN` with a 680 ohm series
  element AND IT WAS NOT CARRIED ACROSS.** So the connector work in the next
  revision is ELECTRICAL as well as geometric, and "move the labels apart" was
  never going to be the whole answer.
- also: `J_TC`, the THERMOCOUPLE input, had no dossier and was assigned to no
  reviewer — `pin_audit.py` drops it on the `>3 pads` filter. It is the 17th ref
  that gate silently omits. Symmetric land, silk `+` under the housing once
  fitted, and a reversed thermocouple raises no fault flag.
- and the negative result that matters most: **THE RELAY LAND IS RIGHT, PROVED
  INDEPENDENTLY OF THE FOOTPRINT.** Sub-figure 13 read at 600 dpi, its lead grid
  measured, and the FIGURE's coordinates transformed into the footprint frame:
  **pure +90 degree rotation, NO reflection, every residual <= 0.05 mm.** Coil
  and contact domains provably disjoint across all 198 nets. 21 MPNs opened at
  figure resolution over 50 of 54 refs; **0 mirrored footprints, 0 pad-to-net
  contradictions against any datasheet that could be read.** The thing this board
  was re-spun for is closed by a lens that could not see the re-spin.
- result: **v1.7 NOT SEALED. THREE order-blockers, all recorded with numbers.**
  M-BEACON PASS 2/2 with the beacon naming all three.

## 2026-07-30 — the FRESH four-lens battery, and the sixth correct refusal to seal

- **subject**: `06_build/staging/cooksense-v1.7` REFRESHED from current source
  (the archive on disk was 2026-07-29T17:31 — pre-ADR-0025, `J_DOOR` still in the
  netlist, pre-bond copper, `fab_v21`). Board md5 `9f4fd5fae810f40a52b1035df727243c`.
  `pdf/`, `3d/` and the bare renders REGENERATED today; `fab_v22` copied in.
- **gates, all unpiped, exit codes raw** — 17 green, 3 non-zero. DRC **0/0/0**;
  `policy_audit` **FAIL=0 PASS=28 WAIVED=6 HUMAN=6 N-A=5**; E-INV **167/167**;
  E-ADR **11/11**; S-COUNT **4/4 over 239**; `jlc_twin` **exit 0, 208/208 bodies**.
- **three of the brief's inherited numbers did not survive**: PASS=28 not 27,
  E-INV 167/167 not 180/180, E-ADR 11/11 not 10/10. Every one still a PASS with a
  different denominator — but a number that travels through a brief unmeasured is
  the class the INHERITED rule was written for, and it travelled three times.
- **jlc_twin exited 1, then 0, on ONE MISSING SYMLINK.** `03_src/rules/` is a
  symlink farm over `03_src/cooksense/rules/`; five files are linked and
  `twin_adjudications.yaml` is not. SKILL.md's documented invocation therefore
  runs the twin UNADJUDICATED — 32 PAD-GEOM + 1 MIRRORED unexcused — and the
  previous run's log carries **no verdict line at all**, which under this repo's
  own rule is a FAIL that had been reading as a pass.
- **A-AMP: two DECLARATION defects, `nets.yaml` untouched since 2026-07-23**, i.e.
  BEFORE v1.6 sealed. Not a regression — the gate got stricter. And the copper is
  fine: `R_ILM` 1.2k sets the eFuse hard limit at **1.79 A**, so IPC-2221 gives
  dT +0.9 C at the 0.50 A operating case and +16.2 C at the silicon ceiling
  against a 1.93 A 20 C-rise capacity. `power_topology`'s own advisory says the
  same thing backwards: the declared 2 A is **>2x the derived need 0.3 A**.
- **the battery**: topology **DO-NOT-ORDER**, layout ORDER, pin ORDER, render
  ORDER. 1 P0, 24 P1, 6 P2/QUESTION, all in `08_reviews/DISPOSITIONS.md`.
- **the P0 is a catalogue, not copper**: `C265111` stock **5** against 10 needed.
  It read 0 yesterday. Every remedy needs a decision that is the user's.
- **the one disagreement between lenses adjudicated by tracing the netlist**:
  render said the over-temp trip is 74.89 C (matches the docs), topology said
  72.79 C (docs wrong by 2.1 C). Both right, different circuits — `TCAM_THRESH`
  has no clamp so the THRESHOLD VOLTAGE is 0.4231 V, but `R_CLMPA` 22k IS on the
  `TH_CAM_A` SENSE node so the TEMPERATURE that reaches it moves: 1575.9 Ohm =
  **72.81 C** with the clamp, 1470.6 Ohm = 74.90 C without. The render lens
  reproduced the DOCUMENT, the topology lens reproduced the BOARD. Still inside
  the brief's 70-75 C window, so P1 not P0.
- **a finding that corrected MY OWN measurement**: I scanned the twelve comb
  slots and published a 1.000 mm minimum web. The layout lens found **0.850 mm**
  at `H4` — hole wall to the east notch — which my scan structurally could not
  see, because it only considered slot-END-to-OUTLINE pairs. Re-measured and
  confirmed to four decimals. The ORDER_README DFM query is now about 0.850 mm.
- **two methods, four identical names**: the render lens found `R_REF4`,
  `R_SER2`, `R_SER3`, `R_MODEPD` printing nowhere on silk with no F.Fab
  duplicate; `waiver_provenance` in the same pass reported exactly those four as
  UNBACKED W-MACHINE refdes waived by `04_kicad/refdes_waiver.json`. Silkscreen
  pixels and a waiver file, same four parts. `R_MODEPD` is an ADR-0019
  restrictive-default pull that cannot be identified on the assembled board.
- **result: v1.7 NOT SEALED.** The `08_reviews` contract blocks it twice over —
  a confirmed P0 without a `fixed` disposition, and a required red-team lens
  carrying DO-NOT-ORDER. Six agents have now declined; this is the sixth.

## 2026-07-30 21:35 — finish (pre-seal pass): A-STOCK re-read LIVE, two paperwork items closed, NOT SEALED
- did: (1) re-read A-STOCK live as the first action, per brief; (2) re-verified
  the headline gates myself rather than inheriting them; (3) re-derived three
  inherited load-bearing numbers straight off the board; (4) fixed B30-17 and
  RULED on B30-11; (5) proved the netlist did not move.
- result — **A-STOCK, THE BLOCKER, STILL RED**: `jlc_stock_check` EXIT **1**,
  verdict line verbatim `FAIL: 57/58 coded BOM lines have stock >= 5 x qty
  (1 with problems); 3/61 lines carry NO LCSC`. `C265111` stock **5**, need 10.
  Re-queried independently off `selectSmtComponentList` (not through the gate)
  — same number. **NEW AND DECISION-CHANGING: `minPurchaseNum` = 21 against
  stock 5.** The genuine JST part is not merely short, it is **unbuyable at any
  quantity today**; the restock threshold to watch is **21, not 10**. Live
  comparators: `C42376901` stock 6030 (was 6086) MOQ 1; `C2653844` stock 103.
- result — gates re-measured, unpiped: DRC `--severity-all --refill-zones
  --schematic-parity` **0/0/0 EXIT 0**; `policy_audit` **EXIT 0, PASS=28
  WAIVED=6 HUMAN=6 N-A=5**; M-BEACON PASS 2/2.
- result — **three inherited numbers re-derived from the board; all three
  confirm the brief and one CORRECTS the previous beacon**:
    (a) `J_ESTOP` 1=GND / 2=**3V3** / 3=ESTOP_RAW_IN, pitch **1.0000 mm** — a
        1-2 bridge is a dead short of the main logic rail, no series FET.
    (b) **minimum web = 0.8500 mm at H4** (Ø2.700 NPTH wall to Edge_Cuts),
        smallest of **105** drilled holes; next is `J_ISOLOOP.1` at 1.150.
        The previous beacon's "minimum web 1.000 mm" was measuring COMB-SLOT
        webs — a different feature that structurally could not see H4. The
        0.850 figure is right and ORDER_README §3a already carries it.
    (c) H4 sits **0.2005 mm** from FILLED copper on ALL FOUR layers — GND on
        F.Cu/B.Cu/In1.Cu and **3V3 on In2.Cu**. Measured against filled polys;
        measuring against zone OUTLINES gives negative nonsense (−0.45 mm) and
        is the wrong method. A conductive fastener at H4 bridges both planes.
- result — **THE NETLIST DID NOT MOVE, PROVEN BY md5 RATHER THAN ASSERTED.**
  Every artifact hash the four lenses recorded in their own headers is
  byte-identical: `cooksense.net` 6d83ebe7…, `cooksense.kicad_pcb` 9f4fd5fa…,
  `cooksense.tsx` c42fada9…, `bom.csv` c491dd00…, `cpl.csv` 38a332bd…; and
  `03_tscircuit/`+`04_kicad/` are byte-identical to the archive copies.
  Nothing I edited (`BRIEF.md`, this journal, `DISPOSITIONS.md`,
  `ORDER_README.md`) is a build input. **THE BATTERY THEREFORE STANDS.**
- closed: **B30-17 FIXED** — `BRIEF.md` fact-lock `DIP05-1A72-12L ×13` ->
  **`DIP05-1A72-13L` ×12**, both fields wrong, on the row a BUYER reads for a
  self-supplied DO-NOT-SUBSTITUTE part whose wrong code is the exact land
  defect that makes v1.0–v1.6 DO-NOT-ORDER. Surfaced into the fact-lock the
  fact the part dossier had been keeping to itself: every distributor quote in
  this tree is keyed to `-12L` and does NOT transfer, so `-13L` distributor
  sourcing is still OWED.
- closed: **B30-11 DECIDED — the release is `v1.7`.** The number is unclaimed
  (nothing ever sealed as v1.7; the series already skips v1.2). Decisive
  constraint: the four lens reviews are APPEND-ONLY VERBATIM EVIDENCE whose
  `subject:` headers name v1.7 + md5 9f4fd5fa, so renumbering to v1.8 strands
  the battery on a release that does not exist with **no legal way to edit
  those headers** — renumbering costs a battery, keeping v1.7 costs nothing.
  The 12 `v1.8` strings in `cooksense.tsx` are **all comments**, verified line
  by line; declared NON-NORMATIVE.
- **NOT DONE, DELIBERATELY**: no regeneration. Editing those comments changes
  the `.tsx` md5 all four lenses recorded — a comment cleanup would invalidate
  the battery — and `rev "dev"` needs a schematic regen
  (`circuit_json_to_kicad_sch.py --rev` defaults to `"dev"`), which the seal
  ritual does not do. Run ONE atomic rebuild in the sealing pass, together with
  whatever B30-01 forces, and grade it once. Regenerating now would mean
  grading twice and re-running a battery for a board that still cannot ship.
- stuck/blocked: **B30-01 is a USER decision and this pass declines to take
  it**, per `assembly.yaml`'s own words. **v1.7 IS NOT SEALED.** The
  `08_reviews` contract blocks it twice: a CONFIRMED P0 without a `fixed`
  disposition, and the topology lens carrying `verdict: DO-NOT-ORDER` (its
  single P0 is P0-1, this same sourcing state — verified by reading the
  review's own P0 section: exactly one entry).
- next: user answers B30-01. Then ONE rebuild closes B30-11 execution, the
  topology lens is re-gated on its own resolved finding, MANIFEST closes
  B30-18, and the 2-commit seal runs.

## 2026-07-30 22:0x — SEALING PASS: ONE atomic rebuild landed; the re-gate BLOCKED the seal. v1.7 IS NOT SEALED (eighth decline)
- did: (1) folded B30-11's comment cleanup and the `rev "dev"` schematic
  regeneration into ONE rebuild and graded it ONCE; (2) re-measured the live
  stock state, the land-pattern equivalence and the H4/J_ESTOP facts MYSELF
  rather than inheriting them; (3) wrote the A-STOCK M4 waiver on the argument
  plus a buyer-facing `ORDER_README` §5-0; (4) re-gated the topology lens on its
  own finding; (5) **stood down when it returned DO-NOT-ORDER.**
- result — **THE ATOMIC REBUILD IS DONE AND CLEAN.** `rebuild_schematic.sh` now
  passes `--rev` (fixed in SOURCE, not by hand-editing `04_kicad/` — canon M3),
  so the sheet reads `(rev "v1.7")` where every prior one read `"dev"`. The 13
  `v1.8` strings — **13, not the 12 the beacon carried** — are all inside
  comment spans, verified by a PARSER rather than by eye, and now read `v1.7`.
  **THE NETLIST md5 MOVED AND THE NETLIST DID NOT:** 198 nets / 239 components /
  806 nodes both sides, **0** nets with a differing node set, **0** components
  with a differing (value, footprint), normalised md5 identical at
  `900941caafe43eb6de7347171a8eb443`; the delta is the title block plus KiCad's
  per-run UUIDs. `cooksense.kicad_pcb` md5 **`9f4fd5fa…` UNCHANGED**.
- result — gates, unpiped, raw exits: DRC `--severity-all --refill-zones
  --schematic-parity` **0/0/0 EXIT 0**; `policy_audit` **EXIT 0, FAIL=0**
  (PASS=28 WAIVED=6 HUMAN=6 N-A=5); ERC **0 errors / 411 warnings**; S-COUNT
  **4/4 over 239 refdes**; E-INV **167/167**; E-ADR **11/11**; M-BOM **PASS**;
  M-DEPEND **PASS**; contracts_audit **0 violations**; A-STOCK **EXIT 1**
  (waived with evidence, see below); the driver's own safety-chain sanity check
  **22/22**.
- result — **A REAL ARCHIVE DEFECT CAUGHT BY THE STAGING RE-MEASURE.** The
  archive did not stand alone: `kicad-cli pcb drc source/cooksense.kicad_pcb`
  returned **14 violations, all `lib_footprint_issues`**, because
  `source/fp-lib-table` had been copied byte-for-byte from `04_kicad/` and its
  vendored-library URI `${KIPRJMOD}/../03_src/lib/cooksense.pretty` points
  OUTSIDE the archive. The `.pretty` was vendored; the table that finds it was
  not rewritten. **A REGRESSION against this board's own sealed v1.6**, which
  gets it right. One URI rewritten -> **0/0/0 standing alone**. Fleet sweep:
  **5 of 33** sealed archives point outside themselves (cooksense-v1.1,
  interposer-v1.0, usb-hub-3s-v3 v1.3/v1.4/v1.6) — immutable, recorded, not
  repaired. No gate exists for it; filed as a skill patch.
- result — **B30-01 WAIVED WITH EVIDENCE, and the evidence is mine.** Live at
  **2026-07-30T21:33:59Z**, both through `jlc_stock_check` and independently of
  it: `C265111` stock **5** / MOQ **21**; `C42376901` 6030/1; `C22391766` 0/444;
  control `C5620` 5212. **MOQ 21 > stock 5 = unbuyable at any quantity**; the
  threshold to watch is 21, not the gate's 10. Land-pattern equivalence
  re-derived by a method that is NOT `jlc_twin` (raw EasyEDA `PAD~` records +
  `pcbnew`, translation-only rigid fit): genuine **0.0002 mm**, clone
  **0.0100 mm** signal / **0.0399 mm** tabs, non-mirrored.
- result — **THE INHERITED `0.01 mm` WAS NOT EVIDENCE, and that is why
  re-measuring mattered.** Its whole triple — `0.01` / `jlc_offset=0` / both
  refs — is **verbatim the GENUINE part's own rows** in this archive's twin log
  (`twin_run.log:440-441`, `C265111 J_THERM_A OK fit=0.01mm jlc_offset=0`), and
  a search of all of `06_build/` finds **no jlc_twin artifact for C42376901
  anywhere**. `fit=` is the max per-pad residual at `%.2f`, so it prints `0.01`
  for the genuine part too and **cannot discriminate the two**. Canon M4's
  headline defect, found in this board's own waiver.
- result — **THE RE-GATE BLOCKED THE SEAL: `verdict: DO-NOT-ORDER`,
  `P0-1: NOT RESOLVED`.** The lens reproduced every number here independently
  and then found **five things this archive got wrong**. The decisive one,
  RG-P1-1: **§5-0 told a buyer to "edit one cell of `fab/bom.csv`" — and
  `fab/bom.csv` is not the file JLC receives.** The assembly step takes
  `bom_jlc.csv` and `cpl_jlc.csv`, and the CPL's `Val` column carries the LCSC
  code because `fp.GetValue()` on these footprints IS `C265111`. A buyer
  following my instruction exactly would have ordered the unbuyable part. Also
  RG-P2-1 (the "zero bytes of the fab set" claim is false — 6 cells across 4
  files; the surviving form is "zero bytes of the gerbers, drill and CPL
  GEOMETRY"), RG-P2-2 (the fit table omitted tab pad SIZE — board 1.000x2.700,
  genuine JLC land 1.210x2.700, clone 1.000x2.500, so the board's retention tab
  matches the CLONE and "the board IS the genuine part's land" holds on the
  signal pads only), RG-P2-3 (**my §5-0 stated a safety consequence BACKWARDS**:
  a dropped pod does not remove `TEMP_OK`, it ASSERTS it — margin 0.07022 of
  rail = 231.7 mV at 3.300 V, rail-independent — so the real cost is nuisance
  latched stops, not a defeated interlock), RG-P2-4 (an H2 heading "ORDERABLE"
  693 lines above the section saying it is not). **All five FIXED in staging.**
- result — **v1.7 IS NOT SEALED. This is the eighth decline, and it is the first
  one where the blocker is NOT the board and NOT the paperwork.** The lens wrote
  that it *"would accept the seal"* — the M4 argument is sound — but that
  *"sealing is not the question this verdict field asks."* The gate reads
  `verdict:`, `verdict:` means ORDERABLE, and this release is not orderable
  today. **Nothing physical is in dispute.** `07_releases/` was left untouched
  and the staged `cooksense-v1.7-2026-07-30/` directory was REMOVED rather than
  left implying a seal.
- **SIX PROPOSED SKILL PATCHES FILED, `skills/` DELIBERATELY UNTOUCHED**
  (`06_build/staging/cooksense-v1.7/verification/owed_skill_patches.md`, P1-P10,
  four of them restated debt): **P1** stock belongs at ORDER time and a seal
  must be able to state "correct" and "orderable" separately; **P10** its
  review-side twin, a `design_verdict` / `order_verdict` split, filed because a
  lens said in as many words that it would seal and could not say so in the
  field the gate reads; **P3** `--rev` defaults to `"dev"` and **33 of 33**
  sealed schematics in this repo say so; **P4** A-STOCK has no MOQ term (scoped
  by the lens's sweep: `C265111` is the ONLY line where MOQ > stock, but
  `C25076`/`C11702`/`C25105` carry reel MOQs of 837/914/887 against needs of
  10/45/10); **P9** nothing checks that an archive can find its own vendored
  footprint library, 5 of 33 cannot; **P2** `jlc_twin` emits no parseable
  verdict line.
- next: the board is DONE and the paperwork is now correct. What is owed is not
  work on this board — it is either **stock `C265111` >= 21**, or a
  **mate-verified** clone substitution (needs physical parts), or **P1/P10** so
  a seal can say "this design is correct" without also having to claim "and you
  can buy it today".
- **THE REPO SUITE IS EXIT 1 WITH SEVEN FAILURES AND NONE OF THEM IS THIS
  BOARD'S — recorded by name rather than waited on.** Re-run per file by me,
  raw exit codes: `t1_escape_tier` **exit 1**, 2 FAIL (P-LAND known-bad fixture,
  `got 5, want 11`, on `pluto_cal_switch.kicad_pcb`); `t1_layout_precedent`
  **exit 0**, 1 FAIL (`PREC_GRADED_FLOOR`); `t1_adr_bounds` **exit 1**, 2 FAIL
  (`CITED_FLOOR`, 37 of 38 bound-publishing ADRs OWED fleet-wide);
  `t1_schema_reader` **exit 1**, 2 FAIL (`G-ORPHAN`, 307/307 keys graded and
  **1 orphan** — `pluto-rx2-8way-v2/02_parts/RP2040-Zero/part.yaml`
  `mechanical`). Seven total, reproducing the reported count exactly.
  **Attribution CHECKED, not assumed:** every failing assertion names its own
  subject and none names a cooksense artifact — cooksense ADRs appear only in
  `t1_adr_bounds`' OWED listing, which is pre-existing debt, not the failing
  assertion; and nothing this pass changed declares a schema key or publishes an
  ADR bound, so none of them can reach these checks. **None of the seven blocked
  this pass** — the blocker was the topology re-gate.
- **AND ONE OF THE SEVEN CANNOT BE SEEN FROM AN EXIT CODE.**
  `tests/t1_layout_precedent.py` prints `10 passed, 1 failed` and **exits 0** —
  reproduced twice with `$?` captured. A test file that reports a failure and
  returns success is exactly what the testing contract forbids (the `jlc_twin`
  exit-0-on-11-unverified-parts shape): anything gating on its exit code sees
  green while it says red. NOT fixed here — different board's owner, and a
  diagnosing agent is already assigned — but named, because it is the difference
  between a suite that is 7-red and one that reports 7-red while one of them is
  skippable by whoever reads `$?`.

## 2026-07-30 17:00 — start (v1.7 SEAL pass, the ninth attempt and the first with a vocabulary for the answer)

- did: loaded `pcb-design` / `kicad-pcb` / `jlcpcb-fab` and CLAUDE.md, read
  `217ea175` (the commit that split the release verdict into two claims), and
  re-measured EVERY gate myself, UNPIPED, with raw exit codes captured — the
  beacon's numbers were treated as INHERITED and re-derived rather than carried.
  Staged the archive into `07_releases/cooksense-v1.7-2026-07-30/` (MUTABLE
  until the seal commit, per the 07_releases contract) and launched BOTH
  red-team lenses as concurrent zero-context re-gates on the new two-key
  vocabulary.
- result: **DESIGN-SIDE GATES ALL GREEN, MEASURED BY ME.** DRC 0/0/0 exit 0 on
  the live board AND, separately, on `source/` copied OUTSIDE the repository
  (the archive stands alone). policy_audit exit 0 FAIL=0. ERC exit 0, 411
  violations **all severity `warning`, 0 errors** — computed from the severity
  histogram in `erc.json`, not read off the "Found 411 violations" headline.
  S-COUNT 4/4 over 239 refdes; E-INV 167/167; E-ADR 11/11; M-BOM PASS;
  F-LEGIBLE 60 checks; P-FACT 6/6 reached a comparison; M-DEPEND PASS; M4
  waiver_provenance PASS; placement_gates PASS; A-ROT/A-POL 64 measured rows;
  contracts_audit 0 violations; M-BEACON PASS. **jlc_twin exit 0**, 207 OK / 465
  finding rows, **206/206 bodies mounted against the CPL**. **A-STOCK exit 1 on
  exactly one line.**
- next: the two lens verdicts, then MANIFEST + the 2-commit seal.

## 2026-07-30 17:00 — iterate 1 (three things the re-measure found that the inherited state did not say)

- did: took nothing on faith, including which arguments the gates wanted.
- result: **(a) `count_parity.py` REFUSES this project without `--board`** —
  raw exit 1, `2 kicad_sch artifacts and no --board: ['cooksense',
  'interposer']`. That refusal is the check working: `rels[-1]` over a two-board
  project graded the wrong archive in four gates at once on 2026-07-27, and this
  is the same class caught at the CLI. Re-run with `--board cooksense`: exit 0.
  **(b) A-POP and F-LEGIBLE and the freshness gate all need `--assembly
  03_src/cooksense/rules/assembly.yaml` / `--parts 02_parts` explicitly** on
  this project, because the per-board rules live under `03_src/<board>/rules/`
  and the default probe looks at `03_src/rules/`. Run with the default, A-POP
  reports 37 UNDECLARED-UNPOPULATED refs — a number that is an ARTIFACT OF THE
  INVOCATION, not of the board. Run correctly: the only finding is the missing
  MANIFEST. **A gate pointed at the wrong file does not fail safe; it fails
  LOUDLY AND WRONGLY, and a number copied out of that run into a report is
  indistinguishable from a real one.** (c) `waiver_provenance.py` takes the
  `projects` ROOT plus `--project`, not a project path; given the project path
  it reports `0/0 waivers graded` and FAILs on the zero denominator (canon
  M-COVER doing its job). Correct invocation: PASS, 12/72 graded.
- next: A-RENDER, which is the gate whose verdict is not a property of the board.

## 2026-07-30 17:00 — iterate 2 (A-RENDER's verdict is a function of its INPUT's resolution, reproduced from scratch)

- did: re-ran `jlc_twin` into a fresh directory with the EasyEDA cache seeded
  from the prior run (exit 0), then ran `twin_overlay.py` against three
  different renders of the same unchanged board.
- result: the gate returns THREE DIFFERENT VERDICTS on one board.
  At jlc_twin's own built-in render (**5.1356 px/mm**): FAIL — `U_LDO` centre
  1.25 mm, and `Q_SWDRVRHA` resolvable-but-unmeasured at 13 body pixels against
  a floor of 20. At **9.7448 px/mm**: still FAIL, but on a DIFFERENT ref —
  `J_KEY_MATRIX`, centre 1.11 mm, outward 0.02 mm — while U_LDO and
  Q_SWDRVRHA both clear. At **15.3907 px/mm**: **exit 0**, 52 measured / 208
  with an expected body, **0 resolvable-but-unmeasured**, every measurable body
  within the 1.00 mm tolerance. This INDEPENDENTLY reproduces the disposition
  recorded on 2026-07-28 (which measured 15.3961 px/mm and 53/210 — the small
  denominator difference is mine being scoped by `--cpl`), so the finding is
  confirmed twice by two agents from two renders. **The point that survives:
  the failing REF changes with resolution, so the low-resolution FAIL was never
  about U_LDO — it was about pixels.** The board never moved; only the picture
  did. Shipped as `verification/twin_overlay.md` (15.39 px/mm, exit 0) WITH
  `twin_overlay_lowres.md` beside it, because deleting the run that failed
  would be choosing the resolution that gives the answer you want.
- next: MANIFEST, then the seal — and the `git_dirty` wall that is not mine.

## 2026-07-30 17:55 — stuck / STAND-DOWN (the seal was declined, and this time by the board)

- did: re-gated BOTH red-team lenses fresh-context on the two-key vocabulary —
  the topology one because it is the one that had declined eight times, and the
  LAYOUT one for what looked like a bookkeeping reason: its legacy
  `verdict: ORDER` retrofits to `order_verdict: ORDER`, and M-REV cross-checks
  that against the measurement, so `ORDER` on a release measured
  `SOURCING: BLOCKED` fires `REVIEW-ORDER-CONTRADICTS-EVIDENCE`.
- result: **topology returned `design_verdict: SOUND` + `order_verdict:
  BLOCKED-SOURCING` — exactly the sentence eight passes had no field for, and no
  design P0.** **LAYOUT returned `design_verdict: DEFECTIVE` with TWO P0s.**
  I re-measured both before standing down, and both CONFIRMED:
  **(P0-1)** `power_tree.yaml` grades the AMS1117 at `iout_max_A: 0.3` while the
  same file declares four 0.1 A switched sensor rails under a `linear_rails:`
  key it labels "ignored by power_topology.py". With `pcbnew` on the archive's
  own board — not the yaml, not the lens's word — `Q_SWA`/`Q_SWB`/`Q_SWRHA`/
  `Q_SWRHE` pad 2 is `3V3` on **all four**, and the drains are `J_THERM_A.1`,
  `J_THERM_B.1`, `J_RH_AMBIENT.1`, `J_RH_EXHAUST.1`. Declared load 0.70 A; the
  graded 0.3 is **43 %** of it. At the file's own constants PD = 1.434 W = 120 %
  of ceiling and dropout headroom = −15 mV.
  **(P0-2)** `pdiss_max_mw: 1200` is a 25 °C figure with no ambient term on a
  board the BRIEF puts at 50–75 °C; at the 75 °C hard limit the ceiling is
  0.600 W, under the release's own 615 mW. I enumerated every zone on the board:
  **the only zone on net `3V3` anywhere is on `In2.Cu` — there is NO F.Cu `3V3`
  zone at all**, so the file's "the tab is flooded with 3V3 copper → 55–65 °C/W"
  is refuted as written.
- next: **STOOD DOWN, not argued.** The candidate moved back to
  `06_build/staging/cooksense-v1.7/`; `07_releases/` untouched; the
  `SUPERSEDED.md` drafted for v1.6 REMOVED, because nothing superseded it. The
  fix is `power_tree.yaml` + the AMS1117 dossier, then re-run E-TOPO — **not a
  layout change** — and one bench measurement at bring-up retires both. If
  E-TOPO still passes at a defensible 0.36–0.40 A with an ambient term, the next
  pass seals; if it does not, that is a real engineering decision and belongs to
  a v1.8 revision.

## 2026-07-30 17:55 — the process note worth keeping

The ninth decline is NOT the eighth repeated, and the difference is the one
thing to carry forward: **the layout lens was re-asked only because a verdict
FIELD would not validate.** Nobody suspected its design content — its previous
pass had said ORDER. Widening the re-gate from "the lens that declined" to
"both lenses" is what found two P0s that eight passes and four graded lenses had
walked past. The general form: when a review's VOCABULARY changes, every lens's
verdict is stale, not just the one whose answer you disliked — and a lens
re-asked for a bookkeeping reason still gets to look at the board.

Second note, on the shape of both P0s: each is a number the gate was GIVEN
rather than a number the gate got wrong. E-TOPO passed correctly on
`iout_max_A: 0.3`; the defect is that 0.3 omits 0.4 A the same file declares in
a section the checker is documented to ignore. That is the P-ADJ-UNREACHED
shape (a budget written where nothing reads it) and the E-MARGIN shape (a gate
optional-activated by a key nobody wrote, printing N-A) appearing a third time
in one file. A declaration the checker cannot reach is not a weaker check — it
is a check that cannot fail.
