# journal — verify / seal

## 2026-07-25 09:00 — start (v1.4)
- did: opened v1.4 to supersede v1.3 as DO-NOT-ORDER. v1.3 ships SEVEN CPL rows
  180 deg off (U1, U2, U3, U5, U7, U8, D_USB — every fine-pitch part on the
  board) after "fixing" a non-defect: v1.0/v1.1/v1.2 all shipped them at 270 and
  were right. Root cause already fixed at source: jlc_twin.xform() had the
  opposite handedness to KiCad's real operator (1b69760), and the per-LCSC table
  had been populated FROM that broken function (e0d735c).
- result: measured baseline on the sealed v1.3 bytes — A-POP FAIL (board 203 /
  cpl 177 / unpopulated 26 / declared 0; NO-ASSEMBLY-DECL + 26
  UNDECLARED-UNPOPULATED + DECLARED-BUT-PLACED on U1), A-STOCK evidence ends in
  `FAIL: 2 coded lines with problems` including LOW_STOCK(0) on the board's own
  CPU. Board itself unchanged and clean.
- next: re-export against the UNCHANGED 04_kicad board and hold the diff to the
  seven cells before anything else.

## 2026-07-25 10:20 — iterate 1 (the acceptance gate)
- did: re-exported the whole fab set from 04_kicad into 06_build/fab_v14 with the
  corrected per-LCSC table; diffed the new CPL against v1.3's cell-by-cell.
- result: EXACTLY 7 changed cells, all Rotation, all 90.0 -> 270.0 (D_USB, U1,
  U2, U3, U5, U7, U8). 177 rows both sides, 0 added, 0 removed, header and
  designator order identical. CONTROLS Q1/Q2/U9 byte-identical (their per-LCSC
  values are 180, which the negation could not move — the fingerprint).
- next: prove the direction independently. The twin agreeing is not enough: the
  twin is the tool that produced the defect.

## 2026-07-25 11:05 — iterate 2 (independent re-derivation, canon M1)
- did: wrote 06_build/tmp/rot_remeasure.py — our pads from pcbnew, JLC's from a
  TEXT parse of JLC's own cached .kicad_mod, matched by pad NUMBER,
  centroid-aligned, RMS-scored at 0/90/180/270, with the rotation operator PROVEN
  against pcbnew over every pad of every footprint on this board before use.
  Shares no code with jlc_twin / jlc_rotation_resolve / export_jlc_package.
- result: operator max error 0.000000000 mm at all four board angles; the pre-fix
  NEGATED form errs 35.560 mm at 90 and 0.960 mm at 270 and TIES at 0/180 — the
  incident's signature reproduced on this board. All 7 corrected parts fit at 270
  with rms <= 0.0725 mm against a runner-up 15x-4811x worse (U1: 0.0025 @270 vs
  11.9812 @0 over 129 numbered pads). Q1/Q2/U9 fit at 180. 0 mismatches vs the
  shipped CPL.
- next: prove the copper did not move.

## 2026-07-25 11:40 — iterate 3 (copper identity by RE-PLOT)
- did: compared the freshly-plotted zip member-for-member against v1.3's sealed
  zip, stripping only the plot's own timestamp comments.
- result: 15/15 members identical after stripping; raw 0/15 (every member carries
  its own timestamp); per-member diff is exactly 4 lines, all timestamp comments.
  So v1.4 SHIPS v1.3's gerber zip + drills VERBATIM and the sha256 identity is
  literal: 20 payload files identical, fab/cpl.csv the only file that differs.
- next: the PCBA gates v1.3 never had.

## 2026-07-25 13:10 — iterate 4 (assembly.yaml — the population set)
- did: authored 03_src/rules/assembly.yaml from the skill template. Measured the
  26 unpopulated refs on the board first: ALL 26 already carry
  exclude_from_pos_files, so no board change was needed (and none was allowed —
  copper identity is the point of this release).
- result: A-POP PASS (declared 10, consigned 1, exempt H/TP 16). Three decisions
  that took actual measurement rather than inheritance:
  * U1 -> `consigned:`, NOT `not_assembled:`. v1.3's manifest said
    "not_assembled: ... U1 (XU316 consign)" while U1 was ON the CPL. Consigned
    means POPULATED — we ship the part, JLC places it. It also needs `msl:`,
    which meant reading the datasheet: XU316 ds v2.0.0 s14.5 p33, MSL 3 / 168h
    floor life / bake per J-STD-033D. That row was MISSING from this project's
    part.yaml while the sibling crow-recorder-central board's copy had it —
    backfilled into limits: here.
  * J3-J10 -> `not_in_catalog`, with the catalog query as evidence: C9900035627
    and C9900056698 are both C99* consign-only codes at stock 0 with no CAD; the
    nearest stocked jack C464587 was MEASURED 2026-07-23 as not a land drop-in
    (pad 1<->13 ours 3.67 mm vs theirs 11.74 mm). A wall we hit and measured.
  * JP_INJ/J_DBG -> `dnp_by_design`, NOT "hand-solder". v1.3 called them
    "uncoded, hand-solder", which reads as scarcity. Queried it: JLC stocks 2.54
    mm THT headers (C2337 stock 86244, C52016391 stock 29861). There is no wall;
    they are deliberately unstuffed bring-up aids. "Hand-solder" is a wall you
    PROVE you hit, not a style — including proving you did NOT hit one.
- next: A-STOCK.

## 2026-07-25 13:55 — iterate 5 (A-STOCK)
- did: jlc_stock_check.py --json at build_quantity 5, shipped as
  verification/stock_check.json.
- result: the raw verdict line still reads FAIL — on exactly two lines, and
  neither accuses this release. C6938291 (the XU316) stock MEASURED 0, PLACED,
  covered by an assembly.yaml sourcing_plan entry saying plainly that it is
  CONSIGNED so JLC stock is irrelevant for that line. C9900035627 stock 0 but NOT
  placed. Every other coded+placed line clears 5x its per-board quantity; closest
  are C5224055 (383 vs 10) and C882626 (496 vs 5). release_freshness check (e)
  grades this PASS with both lines named. v1.0-v1.3 all shipped that same FAIL
  line with nothing parsing it.
- next: archive self-containment, then the full gate battery.

## 2026-07-25 14:30 — iterate 6 (archive self-containment)
- did: checked whether this board has the usb-hub-3s-v3 v1.3/v1.4 defect (a
  source/fp-lib-table pointing OUT of the release). Copied source/ alone into a
  scratch dir and ran DRC on it.
- result: it does NOT. Both vendored libraries resolve through ${KIPRJMOD} and
  ship inside source/; the rest are ${KICAD10_FOOTPRINT_DIR} (toolchain, not the
  archive). Standalone DRC 0/0/0 with ZERO lib_footprint_issues. Shipped as
  verification/standalone_archive_drc.json.
- next: full battery + fresh lens + the 2-commit seal.

## 2026-07-25 15:50 — finish (gates green on the staged archive)
- did: ran the whole battery against the staged v1.4 bytes.
- result: DRC 0/0/0 . standalone-archive DRC 0/0/0 . ERC 0 err / 1211 warn .
  parity 0 (116 nets, 598 nodes both sides) . count_parity 199x4 .
  check_port_nets 115/115 + 8/8 . audit_board PASS (USB spread 0.110 mm, U1-EP
  16 vias) . twin exit 0, 175 OK / 369 checked, 0 ROT-DB-SUGGEST, all ten
  per-LCSC rows OK src=lcsc . missing_models 177/177/0 . bom_source_check PASS
  (49 lines) . A-POP PASS . A-STOCK PASS at qty 5 . policy_audit 0 FAIL after
  the stamp . contracts_audit PASS.
- next: fresh-context lens over the staged bytes, then source commit S, stamp,
  seal commit.

## 2026-07-28 11:05 — start (CAL-1 cross-board drive-level fix, CENTRAL end)
- did: opened the cross-board CAL-1 assignment. The pod's preamp clips on its own
  calibration burst (106.817 dB SPL at MK1 vs a 101.31 dB worst-case OPA1678
  input-common-mode ceiling, shortfall 5.51 dB). The user's chosen fix is to cut
  the LS1 drive ~6 dB AT CENTRAL rather than respin the pod. First question:
  HOW does central set that level?
- result: read `03_tscircuit/src/crow_recorder_central_v2.tsx` lines 189-196 and
  the 8-port map at 325-340. The beep drive is a HARD-SWITCHED, FIXED 5 V
  low-side chop with NO analog level control anywhere: `PLUS5V_BEEP` = `N5V`
  through FB_BEEP (600R@100MHz bead, ~0 ohm DC) + C_BEEP 47uF, always on; Q2
  AO3400A N-FET S=GND, D=`BEEP_RETURN`; gate from XU316 pin 122 `BEEP_GATE`
  through R_bg1 1k with C_bg 4.7nF + R_bg2 100k. No series resistor in the coil
  loop, no adjustable supply, no DAC. ALL EIGHT PORTS share the ONE
  `PLUS5V_BEEP` net and the ONE `BEEP_RETURN` net (BRIEF D1) -> one FET fires
  every pod together. So the ONLY reachable level control is the GPIO WAVEFORM,
  i.e. FIRMWARE. And `05_firmware/` on this board (and on every board in this
  tree) contains ONLY the template `contracts.md` - 1849 bytes, no code.
- next: re-derive the required reduction, model duty-cycle -> 4 kHz fundamental
  honestly (the CMT-8504 datasheet has NO SPL-vs-drive curve), check the far end
  of the link budget, then land the constant + the binding cross-board constraint.

## 2026-07-28 11:40 — iterate 1 (the arithmetic, the model, and the far end)
- did: re-derived every number the fix depends on rather than inheriting it,
  then modelled duty-cycle -> 4 kHz acoustic output honestly, then checked the
  OTHER end of the link budget (the risk in this fix: LS1 is shared, so any
  reduction hits every receiving pod, not just the near one that clips).
- result: MEASURED. Geometry, from pcbnew on a COPY of the SEALED pod v1.3
  board (sha256 2f936fd8... unchanged): LS1 (33.000, 46.000), MK1 (74.000,
  26.000), |d| = 45.61798 mm -> burst 106.8173 dB SPL. Pod mic at ITS load
  80.680 mV/Pa. Worst-case OPA1678 input-common-mode ceiling 101.3144 dB.
  SHORTFALL 5.5028 dB.
  MODEL: output follows the 4 kHz FUNDAMENTAL, not the RMS - the CMT-8504 ds
  rev 1.04 p.3 response curve is a sharp resonance peaking ~104 dB at ~3.9 kHz,
  and a resonator passes the component AT resonance. A 1/6-duty square is only
  -4.8 dB RMS but exactly -6.02 dB in fundamental. sin(pi*D) holds at BOTH ends
  of the UNSPECIFIED coil inductance (L->0 square current; L->inf triangle
  ripple, the D(1-D) cancels); numerical integration of i'=(v-iR)/L with the
  SS14 freewheel over L = 20uH..3mH gives -6.02..-6.68 dB at D=1/6, so the law
  is a CONSERVATIVE bound. M1 sanity by a second method: ds MEASURED 150 mA at
  1/2 duty vs ANALYTIC volt-second balance 151.7 mA, 1.1% apart.
  Electrical->acoustic is ESTIMATED, not specified - the ds has NO SPL-vs-drive
  curve, one trace at one level. Linear-in-current is the conservative pick
  (compression or square-law both deliver MORE reduction).
  FAR END: 6 dB does NOT break it, by a wide margin. All six pods fire from the
  ONE FET, so each pod's dominant path is its OWN LS1 at 45.6 mm; the five
  others on a 7.62 m-radius array (separations 7.62/13.20/15.24 m) power-sum to
  67.0 dB SPL - 39.8 dB BELOW the local path. Matched-filtered on a 20 ms burst
  (50 Hz noise bw), far-pod SNR after -6 dB is 48.7 dB at a 25 dB(1/3-oct)
  ambient and 28.7 dB at 45 dB, timing sigma 0.15-1.5 us vs a 20.83 us sample.
  Pod noise floor is the CAPSULE (14 dB(A), self-noise) not the electronics
  (-1.9 dB SPL over 20 kHz from 9.19 nV/rtHz).
  NEW, and it does not fit in CAL-1: the 5.50 dB shortfall uses LS1's ds
  MINIMUM. A unit on the ds's own TYPICAL curve (~104 dB @10cm) lands at
  110.8173 dB and stays 3.48 dB OVER the ceiling even after -6.02 dB.
- next: land the constant, then the constraint on both boards, then gates.

## 2026-07-28 12:10 — finish (fix landed, firmware+docs only)
- did: landed the drive level as a named, derived constant with a host test;
  recorded the constraint on BOTH boards; ran the gates.
- result: `05_firmware/cal_burst.c` CAL_BURST_DUTY_NUM/DEN = 1/6 ->
  20*log10(sin(pi/6)) = -6.0206 dB -> 100.7967 dB at the capsule, clearing the
  101.3144 dB ceiling by 0.5178 dB. `make test` PASS 0 failures, and
  RED-VERIFIED: rebuilt on a COPY at the pre-fix DEN=2 it reports 5 failures
  including MARGIN -5.5028 dB and exits 1 - the gate can fail.
  Also landed: Makefile (MCU a VARIABLE per the folder contract), README.md
  (states build, connector, and the UNPROGRAMMED-BOARD behaviour - SILENT,
  because R_bg2 100k holds Q2's gate low; the dangerous default is the SOFTWARE
  one, a naive 50% duty). ARCHITECTURE.md + DETAIL_DESIGN.md carry the
  constraint and the full arithmetic; CHANGELOG v1.8 firmware+docs only.
  NO copper, BOM, netlist or release moved. 04_kicad/ and 07_releases/ not
  written; v1.7 stays sealed, live and orderable. contracts_audit: the two
  boards hold at their 10-file pre-existing baseline, 0 added.
- next: the operator-facing copy is OWED to the NEXT release's ORDER_README
  (every existing one is inside an immutable sealed release). And the residual
  is the user's: -6 dB clears a MINIMUM-output LS1 by 0.52 dB and leaves a
  TYPICAL-output one 3.48 dB over - trim against a measurement at bring-up.

## 2026-07-28 13:20 — iterate 2 (retune 1/6 -> 1/12; the bound REFUTED at the new duty)
- did: USER DECISION — retune to duty 1/12 AND move the acceptance criterion
  from "clears a minimum-spec LS1" to "clears a unit on the ds TYPICAL curve".
  Instruction was explicit: re-verify the sin(pi*D) bound AT THE NEW DUTY and
  do not carry the old conclusion forward. Re-ran the L-R integration with an
  EXACT per-step exponential (not Euler) over L = 10 uH .. 3 mH.
- result: **THE LAW IS NOT A CONSERVATIVE BOUND AT 1/12.** It was at 1/6
  (-6.02..-6.68 dB at every corner vs the law's -6.021). At 1/12 it fails, and
  for TWO reasons, only one of which was predicted:
  (a) L-R REGIME CHANGE (predicted): the 20.8 us pulse no longer lets current
      build, the long freewheel tail dominates, and the L=3mH corner returns
      -10.905 dB against the law's -11.740 -> NON-CONSERVATIVE by +0.835 dB.
  (b) GATE-RC DUTY BIAS (NOT predicted, and the DOMINANT term): turn-ON waits
      only for the gate to CLIMB to Vgs(th) (20-44% of the 3.3V drive) but
      turn-OFF waits for it to FALL from ~3.26V DOWN to Vgs(th) (56-80% of the
      way). Asymmetric -> the conduction window is STRETCHED by +1.11 us
      (Vth 1.45) to +6.47 us (Vth 0.65). It is an ABSOLUTE time, so its
      fractional cost grows as duty shrinks: 5% of the pulse at D=1/2, 31% at
      D=1/12. DETAIL_DESIGN documents this RC ONLY as an EMI slew-limiter;
      nobody noticed it also biases the duty UPWARD, which only becomes a
      defect once duty is used to control LEVEL.
  COMBINED WORST CASE over L in {20u,100u,500u,3m} x Vth in {0.65,1.05,1.45}:
  **-8.71 dB, not -11.74 dB. Slack +3.03 dB.**
  MARGINS: criterion shortfall vs the TYPICAL unit = 9.5028 dB (110.8173 -
  101.3144). At 1/12 nominal: typical +2.2372 dB PASS, minimum-spec +6.2372.
  At 1/12 WORST CASE: typical **-0.79 dB, STILL CLIPS**; minimum-spec +3.21 dB.
  So the structural finding is: the OPEN-LOOP UNCERTAINTY (~3 dB) EXCEEDS THE
  CRITERION (2.24 dB). This level cannot be set open-loop to the accuracy the
  criterion demands. den=14 is the first value clearing worst case (+0.11 dB);
  16 -> +0.93, 20 -> +2.41. Trim floor raised 16 -> 24 (the old floor forbade
  exactly the values that fix the worst case; at 1/24 the gate still peaks at
  2.94 V vs the AO3400A's 2.5 V Rdson spec point).
- next: land 1/12 with BOTH models declared, move the test to the new
  criterion, re-RED-verify, propagate to both boards.

## 2026-07-28 13:55 — finish (retune landed; residual recorded OPEN, not smoothed)
- did: landed DEN=12, moved the test's acceptance criterion to the TYPICAL
  unit, added always-run inline known-bad fixtures for BOTH superseded values,
  and pinned the declared worst-case constant to the model so a future retune
  cannot leave it stale.
- result: `make test` **PASS, 0 failures**, and it prints the residual in the
  clear ("criterion met NOMINALLY +2.24 dB; under the WORST-CASE model MISSED
  by 0.79 dB"). RED-VERIFIED against the NEW criterion by recompilation:
  DEN=2 -> 6 failures, exit 1; DEN=6 -> 6 failures, exit 1 (TYPICAL-unit margin
  -9.5028 and -3.4822). Both are ALSO checked inline on every run, so the gate
  proves it can fail without a recompile.
  One thing the retune changed that I did not expect beyond the bound: the
  TIMER QUANTIZATION error grew from -0.0006 dB at 1/6 to -0.0014 dB at 1/12,
  because sin(pi*D) is steeper at small D. Still negligible; the test's
  tolerance is now stated against that physics (0.01 dB, ~300x below the 3 dB
  open-loop uncertainty) rather than an arbitrary round number.
  Side effects at 1/12: coil average current ~10-25 mA (deep DCM, peak
  33-307 mA depending on L), shared Q2 ~60-150 mA, pod cable IR ~0.02 V, MK1
  headroom to its 110 dB THD limit 10.92 dB typical / 14.92 dB minimum-spec.
  FAR END re-checked at the new duty and still fine: far-pod matched-filter SNR
  42.95 dB at 25 dB(1/3-oct) ambient, 22.95 dB at 45 dB, timing sigma
  0.28-2.83 us against a 20.83 us sample; local path 95.077 dB SPL, 81.1 dB
  above the mic's own self-noise.
  NO copper, BOM, netlist or release moved. 04_kicad/ and 07_releases/ not
  written on either board; central v1.7 and pod v1.3 stay sealed and live.
- next: USER CALL on the worst-case residual — trim against a measurement at
  bring-up (scoping BEEP_RETURN at TP11 against the commanded pulse reads the
  gate-RC stretch directly and collapses most of the 3 dB), or take DEN=14
  open-loop. Still owed: the operator-facing copy in the NEXT release's
  ORDER_README.
