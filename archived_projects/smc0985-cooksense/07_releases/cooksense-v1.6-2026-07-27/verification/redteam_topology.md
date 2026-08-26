> ## ⚠️ RETRACTION — READ THIS FIRST (2026-07-26, after the review)
>
> **The verdict below (`DO NOT SHIP the archive as staged`) is RETRACTED, and
> the two findings that produced it are FIXED in the board this archive ships.**
> The review is kept verbatim rather than rewritten, because a review edited to
> agree with the fix teaches nothing about how the defect was found.
>
> | finding as written | status now | fixed by |
> |---|---|---|
> | **P0** R_WDPETPD assembled at 100k | **FIXED** — pinned to C11702 (1k); BOM line reads `1kΩ,"R_SER0..7,R_WDPETPD",...,C11702` | `c9e0b3a` |
> | **P1-1** TEMP_OK pulled up on the wrong rail — marked "NOT FIXED, escalated" below | **FIXED** — `R_TEMPOK.2` is on `3V3_ANALOG`; verify in `source/cooksense.net` | `e6a78a6` |
> | **P2** `electrical_invariants.yaml` stale at 6.2k/3.107V | **FIXED** — now 62k/2.0370V | `e6a78a6` |
> | **P2** MANIFEST overstated the opto margin | **FIXED** — MANIFEST and ORDER_README now state 2.0000 mm with the metric named | this staging |
> | **P2** `stock_check.csv` stale | **FIXED** — regenerated from the shipped BOM | this staging |
> | **P1-2** door NO + no EOL | **DEFERRED to v1.4, DECLARED** — ORDER_README section 2-0, prominently | coordinator decision |
> | **P1-3** TH_CAM span 93.62/87.75 mm vs an 8 mm budget | **DEFERRED to v1.4, DECLARED** — ORDER_README section 13 | coordinator decision |
> | **P1-4** R_HYS negative feedback on U_COMP2 | **DEFERRED to v1.4, DECLARED** — dispositions.md D-2, with the reason it can wait | coordinator decision |
> | **P1-5** CH0/CH3 transfer function undocumented | **CLOSED 2026-07-26** — derived in ORDER_README section 2b (`R_ntc = 1/(1/R_par - 1/22000)`), with an 8-point error table and recomputed thresholds; no bench step. dispositions.md carries the closure | closed |
>
> Everything this review verified as CORRECT still stands and was not re-run —
> in particular the cross-layer isolation scan, which is RED-verified against the
> sealed v1.1 board (915 pairs under 2.0 mm, worst 0.0000 mm).

# Red-team lens A — SAFETY AND ELECTRICAL CORRECTNESS
cooksense v1.3, run 2026-07-26 against the staged archive + source.
Adversarial brief: find reasons NOT to ship. Read-only; no rebuild, no export.

VERDICT: **DO NOT SHIP the archive as staged.** One P0 (since fixed), five P1,
five P2.

## P0 — R_WDPETPD assembled as 100k, not the 1k the safety argument requires
FIXED at c9e0b3a (pinned to C11702). Chain measured across four artifacts:
circuit.json resistance 1000 with auto-picked codes ['C25741','C60491',
'C2906859'] — byte-identical to R_MR which IS 100000; bom_jlc.csv line 5
Comment "100kΩ / 1kΩ", 23 designators, LCSC C25741; stock_check.csv MPN
0402WGF1003TCE (1003 = 100x10^3); ledger C25741 = 100k.
Consequence from TPS3823 SLVS165O 6.5/7.3.4: WDI SOURCES I_IL 190uA max,
V_IL = 0.3*VDD = 0.99V, so R_max = 0.99/190u = 5.21k. 100k is 19x that; the
node sits ~2.4-2.6V, above V_IH 2.31V, the transition detector keeps seeing its
own internal pulse and THE WATCHDOG IS SILENTLY DISABLED. With the Pi dead and
J_PI.11 released, WD_OK stays HIGH, U_CAND1/U_CAND2 hold, the MCP23017 retains
its CONTACTOR_REQ latch, and the external cooking contactor stays energised.
Worst signature: with a live host TP_WDOK reads high. It fails only in the case
the part exists for.
Swept all 126 ledger-verifiable passives: this was the ONLY authored-value !=
ordered-part mismatch.

## P1-1 — TEMP_OK is pulled up on the WRONG RAIL: single-point failure to permissive
R_TEMPOK.2 -> 3V3, but U_COMP.8 and U_COMP2.8 -> 3V3_ANALOG, whose sole source
is ferrite FB1 (FB1.1 3V3 / FB1.2 3V3_ANALOG). FB1 open -> all four open-drain
comparator outputs unpowered -> R_TEMPOK pulls TEMP_OK HIGH = "temperature
fine" = PERMISSIVE, while the divider top rail and the MCP3208 VDD/VREF die in
the same instant so the software readback is gone too.
Tying R_TEMPOK.2 to 3V3_ANALOG makes it fail-safe: with that rail dead the
TH_CAM nodes sit at 0V through R_CLMPA/B and R_HYS1/R_HYS2 (2x1M) pull TEMP_OK
to ~0V = restrictive.
TEMP_OK is the ONLY permission in the chain actively pulled toward permissive;
all 12 others are pulled restrictive (REARM_N correctly pulled up).
NOT FIXED — an electrical change on the safety chain, escalated for decision.

## P1-2 — Door input is not supervised the way the brief commissions it
BRIEF.md:92 says "Door: external NC reed + EOL". Implemented: Form-A (NO) reed
+ R_DOORPD 10k, NO end-of-line resistor. Open cable -> DOOR_OK=0 (the v1.3 fix,
correct) but a SHORT is undetectable and fails permissive, and J_DOOR.1 (3V3)
is adjacent to J_DOOR.2 (DOOR_RAW) at the same 0.650mm pad gap v1.3's own P0-2
declared unacceptable, in a pollution-degree-3 steam environment. The tsx block
header still says "DOOR (NC reed+EOL)" while the code below is NO + no EOL.
DOOR_OK gates OS_CLR_N only, not the contactor directly.

## P1-3 — Interlock sense nets exceed their declared P-ADJ budget ~12x, unenforced
LMV393IDR part.yaml declares keep_short max_span_mm: 8 for TH_CAM_A/B. Measured
on the board: TH_CAM_A 93.62mm routed / 39.62mm pad-to-pad; TH_CAM_B 87.75 /
39.22. Source impedance at the open trip is 10k||16.1k = 6.2k and the
comparators tap BEFORE R_SER0/C_FLT0, so no local filter. Closest same-layer
aggressor SPI_SCLK at 0.206mm from TH_CAM_A copper. audit_board's I-PROX is a
hand-maintained 25-row list with NO span/keep_short check at all. Direction is
fail-safe (glitch -> TEMP_OK low -> latched lockout), so robustness not hazard.

## P1-4 — R_HYS1/R_HYS2 give U_COMP2 NEGATIVE feedback; the open-detect has no hysteresis
The 1M resistors run TEMP_OK -> TH_CAM, which is U_COMP's IN+ (positive fb,
correct) but U_COMP2's IN-. Measured: head open with TEMP_OK low moves the node
2.2687 -> 2.2533V (-15.5mV) against 232mV overdrive, so a real open still
latches solidly. At the -10.4C nuisance boundary it is a zero-hysteresis,
negatively-fed comparator on a 6.2k node, and any TEMP_OK chatter SETS the
level-sensitive latch into a hard lockout.

## P1-5 — CH0/CH3 ADC transfer function changed; documented nowhere
The 22k clamps mean the two camera channels no longer share the other six
channels' conversion. DETAIL_DESIGN.md is titled "cooksense v1.2 electrical
corrections" and grep across 01_docs/*.md returns ZERO hits for R_CLMP / clamp
/ bleed / 22k / open-therm. If the host applies the unmodified 10k/NTC model
(B=3987, R25=10k): true 0C -> reports 18.7C; 25C -> 33.6C; 70C -> 72.3C.
Over-reads (conservative for the software limit) but destroys absolute accuracy
and any cross-channel plausibility check.

## P2
- electrical_invariants.yaml is STALE on the function it guards: the U_COMP2
  entries still say "R_OPENT 6.2k / R_OPENB 100k -> 3.107V" and "output goes LOW
  when the node rises ABOVE 3.107V". Shipped design is 62k/100k -> 2.0370V. Only
  the U_COMP2.8 entry was updated. LMV393IDR part.yaml has the same drift.
- MANIFEST OVERSTATES THE OPTO MARGIN. It claims "2.126mm measured on routed
  copper". Independently measured minimum ISO_CONTACTOR -> any named net over
  all layers: 2.0000mm (CONTACTOR_C at J_ISOLOOP.1 -> GND zone, F.Cu). 2.126 is
  pad-to-pad and misses the pour edge, which sits exactly on the moat keepout.
  Passes the rule; real margin is 0.000mm, not +0.126mm.
- verification/stock_check.csv is stale: 53 rows vs the BOM's 57, no row for
  R_OPENT/R_OPENB/C37825 — generated before the R_OPENT fix.
- floorplan.yaml says a bonded chassis "re-opens the defect at 3.000mm";
  audit_board's own I-HW line in the same release measures that case at 0.000mm
  (min_a -0.050 + min_s -1.450). The silk text is right; the floorplan is not.
- C_CAND2 is 12.06mm from U_CAND2 (the gate producing CONTACTOR_DRV), the
  loosest decoupler on the board, with no I-PROX row.

## CHECKED AND CORRECT (bounds the coverage)
Open-thermistor arithmetic, every claimed number re-derived and matched:
TCAM_OPEN 2.03704V; open node 2.26875V; worst separation 193mV; worst-high open
2.2829V vs the 2.500V VICR ceiling = +217mV; nuisance trip -10.35C; over-temp
72.81C inside the 70-75C window. Every reading the comparators see is inside
0..VCC-0.7/0.8.
Comparator polarity read from the netlist: U_COMP IN+=TH_CAM, IN-=TCAM_THRESH;
U_COMP2 IN-=TH_CAM, IN+=TCAM_OPEN; four open-drain outputs = 4-way wired-AND.
Watchdog topology: R_WDPETPD is a pull-DOWN, correct direction; only the ordered
value was wrong.
AND-chain algebra matches the documented intent including
FAULT_SET_N = WD_OK.ESTOP_OK.TEMP_OK.
NAND-SR illegal state examined and NOT exploitable: whenever it exists CTR_SAFE
is also 0, so CONTACTOR_DRV is 0 regardless.
CROSS-LAYER ISOLATION — the check KiCad structurally cannot make (clearance
rules are same-layer only). Rebuilt all 9328 copper polygons and measured every
ISO-vs-other pair on every layer combination: ISO_CONTACTOR min 2.0000mm,
KEYPAD_ISO min 6.1200mm, 0 pairs under either rule; independently reproduces
audit_board's 6.12mm I-ISO.
THE SCAN IS PROVEN ABLE TO FAIL: run unchanged against the v1.1 SEALED board it
returns 915 ISO_CONTACTOR pairs under 2.0mm, worst 0.0000mm (GND/3V3 pours
straight under U_OPTO on In1/In2/B.Cu) and 0.1750mm same-layer to
DOOR_RAW/ESTOP_RAW — exactly the figure nets.yaml documents.
The DRU `B.NetName != ''` exemption checked: no exempt conductor creates a
sub-6mm summed path. The H4 notch really is in the sealed Edge.Cuts (5 segments,
x191.5->200.0, y48.8->49.8) and it does cut the straight H4->K_STOP.3 line.
Silk safety warnings all present. DRC 0/0/0 with both isolation DRU rules in
source/cooksense.kicad_dru. ERC 0 errors / 1303 warnings.
All other 126 passive values match their ordered LCSC code.

## COULD NOT CHECK
- CE1 (C2887273) is not in the passives ledger — the only board value not
  cross-checkable offline. Not safety-critical.
- WHETHER THE OPTO DRIVE IS ADEQUATE FOR THE FIELD CIRCUIT. R_OPTOLED 330R off
  3V3 -> I_F ~6.4mA; part.yaml CTR 50-600% (TA1 bin) -> guaranteed I_C ~3.2mA
  worst-bin before ageing derate, against a J_ISOLOOP marked 30V / 50mA. No
  current budget for the external loop exists anywhere in 01_docs. The 50mA
  marking is not achievable and nothing in the repo reconciles the two.
- OPTO V_CEO MARGIN. 35V against a 30V working loop (17%), with no clamp or
  snubber on CONTACTOR_C/CONTACTOR_E. If the field circuit is inductive the
  break spike exceeds 35V, and the overvoltage failure mode of a phototransistor
  is a SHORT = permissive. Whether the field circuit is inductive is outside the
  repo.
- No rebuild/re-export/DRC/router was run (read-only).
- Datasheet PDFs not re-read; extracted facts taken from 02_parts/*/part.yaml.
