# DISPOSITIONS — cooksense MAIN board findings ledger

Living ledger tracing every review finding to its outcome (08_reviews contract).
Sources: fresh-context PIN REVIEW (5 groups, 45+ parts) + RENDER REVIEW
(06_build/verification/{pin_review,render_review}.md, 2026-07-23; archived here
with provenance at seal) + jlc_twin network run (cook_twin2, exit 0 after
adjudication). Dispositions by the routing-stage lead, 2026-07-23. "FIXED" =
source-fixed and regenerated in the batched rebuild; evidence cited per canon M4.

| # | Finding (severity) | Disposition | Evidence / change |
|---|---|---|---|
| 1 | PWR_GOOD_N polarity: U_EFUSE.6 FLT_N is LOW=fault (HIGH=power-good) but the net's `_N` name implies LOW=power-good (pin review Q1, safety-chain priority) | FIXED — net RENAMED `EFUSE_FLT_N` (name now honest: it IS active-low fault). Logic was CORRECT: consumers traced in the netlist = R_PG pullup, TP_PGOOD testpoint, U_EXP.1 (MCP23017 GPA0, software-read) — it feeds NO hardware AND-chain input, so no polarity inversion existed in hardware. | Netlist: EFUSE_FLT_N = {R_PG.1, TP_PGOOD.1, U_EFUSE.6, U_EXP.1}; PWR_GOOD_N no longer exists. E-INV `pin_on_net U_EFUSE.6 -> EFUSE_FLT_N` locks it. TP_PGOOD refdes kept (probing semantics HIGH=good are correct for a "PGOOD" test point). |
| 2 | D_REVCLAMP (SS34) on 5V_IN UPSTREAM of F1 — reverse-hookup clamp current bypasses the board fuse (pin review Q2) | FIXED — moved to 5V_FUSED (downstream of F1). This was a genuine wiring-vs-intent bug: the tsx comment itself said "reverse input conducts, trips F1", but on 5V_IN the fault path (GND→clamp→J_PWR) never crossed F1. Now: supply→J_PWR→F1→clamp→GND — the polyfuse trips. D_ESD_IN stays at the entry (ESD transients belong at the connector). | Netlist: 5V_FUSED = {D_REVCLAMP.1, F1.2, Q_REV.3}; 5V_IN = {D_ESD_IN.1, F1.1, J_PWR.1}. E-INV `pin_on_net D_REVCLAMP.1 -> 5V_FUSED`. SS34 part.yaml stale "D1 cathode faces VSYS" prose corrected to this board's crowbar role. |
| 3 | J_PWR pin-1-vs-housing-key never confirmed against the Molex SD drawing (pin review Q3; PDF fetch blocked) | ORDER_README BRING-UP-CRITICAL — first-power ritual: multimeter the mating harness (pin 1 blade beeps to +5V, pin 2 to RTN) with the polarizing-peg orientation noted, BEFORE first power. | 02_parts/43650-0224/part.yaml gotcha added; ORDER_README line item. Keyed housing prevents reverse MATING but cannot fix a mis-assumed pin-1 side. |
| 4 | '238-float / phantom-select: DECU_G1/DECD_G1 + address nets float when SR_OE_N tri-states the 595s; floated-high E3 could enable a decoder output into the ULN (pin review Q4) | FIXED (reviewer's option a) — 100k pull-DOWNs R_DECUPD/R_DECDPD on both E3 enables: a pulled-low E3 disables all 8 outputs regardless of the floating addresses. NOTE: the reviewer's "coil rail live" premise was DISPROVEN by the netlist — COIL_EN's only sources are J_MODE.2 (the DPDT AUTO throw fed from KEY_RELAY_ALLOWED = U_AND3.4, which contains WD_OK via U_AND1) and R_COILENPD pull-down, so any WD_OK drop also de-energizes the rail (option b already exists structurally). The pull-downs still go in: floating CMOS inputs are formally out-of-spec (Nexperia 74HC238D — C5620 is Nexperia, not TI). | Netlist: DECU_G1 ⊇ {R_DECUPD}, DECD_G1 ⊇ {R_DECDPD}. E-INV net_has_part locks both. COIL_EN trace: {J_MODE (pole A), Q_COILDRV.1, R_COILENPD.1} — no watchdog-independent source. |
| 5 | J_PI mating-geometry doc contradiction (pin review FAIL): part.yaml gotcha claimed direct-stack "socket-down, mates Pi J8 BELOW" (under which the footprint would be mirrored) vs layout/ADR-0007/silk = RIBBON SIDECAR (under which it is correct) | CONFIRMED SIDECAR (design intent unambiguous: layout block + ADR-0007 + board silk "PI 40-PIN RIBBON (SIDECAR)"). Footprint KEPT (pin map verified 40/40 vs Pi J8 by the review); stale gotcha REWRITTEN; interconnect now SPECIFIED: 40-way ribbon with MALE DIL IDC transition plug at the board end (standard Pi ribbons are female-female and cannot mate this socket) + pin-1 keying discipline (unshrouded socket) + the 12.46mm stack tails protrude ~12mm below the board (trim or stand off). All three → ORDER_README line items. | 02_parts/2.54-2x20PPC104/part.yaml gotcha #1 rewritten with the full sidecar spec; no board change. NOT a respin question — direct stacking was never this board's intent. |
| 6 | J_MODE cross-plug hazard (pin review QUESTION): 3V3 on pin 3 adjacent COIL_EN on pin 2, convention differs from sibling GH connectors — a cross-plugged harness could short COIL_EN to 3V3 and energize the coil rail bypassing the AND-chain | FIXED — J_MODE RE-PINNED to the sibling convention: 1=3V3, 2=MODE_RAW (pole B), 3=KEY_RELAY_ALLOWED, 4=COIL_EN (pole A), 5=GND. COIL_EN's neighbours are now the AND-chain output and GND: any cross-plug bridge either applies the intended gating or holds the rail OFF. A J_DOOR-style harness (bridges 2-3/4-5) gives benign MODE_RAW↔KEY_RELAY_ALLOWED contention + COIL_EN→GND (safe-off). Residual (any 1-2-bridging harness into J_ESTOP forces ESTOP_RAW high) → harness labeling discipline in ORDER_README. | tsx re-pin + rebuild; netlist verified post-rebuild. |
| 7 | J_ESTOP pins 3/4 carry the contactor loop through a 1.0A/50V GH contact — cite the loop current/voltage (pin review QUESTION) | EVIDENCE, no change — the loop is the LTV-817S opto DRY CONTACT: U_OPTO collector→CONTACTOR_C→J_ESTOP.3, J_ESTOP.4→CONTACTOR_LOOP→J_CONTACTOR.1. The design bound is ≤30V/≤50mA (brief §3, authored in the tsx block comment; LTV-817 collector current abs-max 50mA is the limiting element). 50mA/30V ≪ 1.0A/50V GH rating — margin 20× on current, 1.7× on voltage. The external contactor COIL is driven by the external circuit, not through this contact pair. Cross-plug (estop harness into J_DOOR closes the loop through GND) → same ORDER_README labeling discipline as #6. | Netlist trace + brief §3 + LTV-817S rating; JST GH rating 1.0A AC/DC 50V (eGH.pdf p.1). |
| 8 | J_TC footprint MISSING the 4× Ø1.77mm holes; contact slot drills 1.70×0.90 too small for the pins (render review, REAL board defect) | FIXED in the source footprint (03_src/lib/cooksense.pretty, canon M3): contact drills → round Ø1.77 (pads 2.8mm, pad 1 rect = polarity marker); 2 NPTH Ø1.77 mounting-bracket holes added at ±7.85 (15.7mm span), 6.8mm behind the contact row (into the board — retention against plug insertion force); courtyard extended. Geometry from the Omega PCC-OST-SMP drawing p.2 (committed PDF, read at 300dpi): "Ø1.77 (0.070) 4 PLACES", contact span 7.9, bracket span 15.7, row offset 6.8, contacts 13.7 from the mouth face (bracket row lands at the body rear ≈ 20.5 of the 20.8mm body — consistent). | Footprint diff + rebuild DRC. |
| 9 | J_TC polarity: chromel(+)-lands-on-pad-1 physically unresolved from available docs; jack is keyed so a swap is unfixable at the plug (render review) | ORDER_README REQUIRED first-use check — the spec sheet's PCB-pattern view does not unambiguously mark which blade is chromel, so: before trusting readings, dip the TC in a known-temp reference (ice water / boiling water); a REVERSED junction reads inverted delta from ambient — obvious and harmless. Electrical side is verified correct (pad1→TC_POS→MAX31856 T+ with bias on T−, pin review PASS). | Disposition = deliberate documented check; part.yaml already carries the ANSI color-code polarity facts. |
| 10 | U_COMP LM393 Vicr corner: an OPEN thermistor pulls the sense node to 3.3V > the guaranteed 3.0V common-mode ceiling (VCC=5V, over temp) exactly in the broken-sensor case (render review) | EVIDENCE, no change — dual coverage: (a) the Pi-side ADC open-thermistor detect (brief C14) is the DESIGNED broken-sensor mechanism — the MCP3208 reads the same divider rail-high and firmware flags the fault regardless of the comparator; (b) LM393 typical Vicr = VCC−1.5V = 3.5V covers 3.3V at 25C, and beyond Vicr ONE input out of range gives an indeterminate but NON-DAMAGING output (TI D/S: no phase inversion, inputs rated to VCC) — the comparator may read either state, which the interlock treats conservatively only as one input of the AND chain while firmware owns open-sensor detection. Worst case = a nuisance state, not a missed shutdown, because the firmware path (a) is authoritative for open sensors. | Brief C14 + LM393 datasheet common-mode section; no netlist change. |

Cross-cutting ORDER_README items collected from the above: J_PWR pin-1 harness
check (#3); J_TC known-temp first-use check (#9); J_PI ribbon spec (male DIL IDC
transition) + pin-1 keying + tail trim/standoff (#5); harness LABELING discipline
for the unkeyed 5-pin GH family (#6, #7); KEY_RESET_N floats during Pi boot —
R_OE holds 595 outputs disabled, low risk, bring-up note (pin review minor);
self-supplied DO-NOT-SUBSTITUTE table (reed **DIP05-1A72-13L** ×12 + PCC-SMP-K
— *code corrected 2026-07-30 per B30-17; this line said `-12L`, the superseded
pin-out, until then*);
order-day stock rechecks (C2653844=160, C89650=244, C587657=778, C16939=223).
| 12 | v1.1 fresh lens P2-1: comb creepage floor 6.120mm intra-relay (0.12mm over spec) | Accept-with-note — floor fixed by the DIP05 footprint (same as sealed v1.0); cannot erode (DRC deny comb). Future spec-tightening note. | 2026-07-24_v1.1_fresh_lens.md; v1.1 verification/dispositions.md #1 |
| 13 | v1.1 fresh lens P2-2: east-end pocket lacks a south slot (asymmetry) | Accept-with-note — 6.63mm measured at the east mouth; slot skipped for edge-web integrity (<3mm to edge); lens: passes as-is | v1.1 verification/dispositions.md #2 |
| 14 | v1.1 fresh lens P2-3: CPL carries 14 hand-solder rows -> JLC preview warning | ORDER_README Assembly row: expect and IGNORE; do not let JLC fix | v1.1 verification/dispositions.md #3 |
| 15 | v1.1 fresh lens P2-4: ERC 1169 warnings / 0 errors (generated schematic) | Accept — compensating gates E-INV/count_parity/label-survival/netlist-identity | v1.1 verification/dispositions.md #4 |
| 16 | v1.1 fresh lens P2-5: volatile stock (F1 244; C25744 fell 192k->12.6k/day) | ORDER_README §3 order-day recheck MANDATORY + 10k substitute class listed | v1.1 verification/dispositions.md #5 |
| 17 | v1.1 fresh lens P2-6: netlist-identity claim documentation | Documented (semantic_battery.txt byte-diff + parity.md) — licenses the scoped re-verify | v1.1 verification/dispositions.md #6 |

# DISPOSITIONS — interposer (Board C) v1.0, 2026-07-24

Sources: 2026-07-24_interposer-v1.0_{pin-review_connectors, render-review_full,
redteam_topology, redteam_layout}.md. Dispositions by the interposer board lead,
2026-07-24, all pre-seal (findings cost edits, not supersedes).

| # | Finding (severity) | Disposition | Evidence / change |
|---|---|---|---|
| I1 | No seated-visible pin-1 marker on the hand-solder ZIFs (render P2) | FIXED — "1"/"10" silk numerals added to the 10FDZ footprint, outside the housing outline so they stay visible with the connector seated; captions relocated to clear them; DRC re-measured 0/0/0 | commit 4358b0c + follow-ups; render pair regenerated |
| I2 | GH ribbon harness under-specified — same-side vs opposite-side crimp variants silently swap pin1<->pin10 (lens-a P1) | FIXED-IN-DOCS — ORDER_README "KEYPAD RIBBON" section specifies: 10-way GHR-10V-S both ends, contact-k -> contact-k, both housings crimped on the SAME conductor face with pin 1 on the SAME cable edge, planar U-bend mate; continuity-verify 1->1 and 10->10 before first use | ORDER_README.md (this release) |
| I3 | 10FDZ-BT land pattern is datasheet-derived, physical fit + circuit-1/boss end unconfirmed (lens-a P1 = pin-review QUESTION; the declared order gate) | DEFERRED (USER-HELD ORDER GATE) — LOUD ORDER_README bring-up ritual: verify drill pattern + polarization-peg position + circuit-1 end against a physical 10FDZ-BT BEFORE ordering fab; same class as v1.0 J_TC/J_PWR rituals (D9, ADR-0009) | 02_parts/10FDZ-BT/part.yaml NEEDS-PHYSICAL-CONFIRM; ORDER_README |
| I4 | SM10B-GHS-TB layout.notes contradicted the corrected pins.MP float rule (pin-review LOW, lens-a P2) | FIXED — stale tie-to-isolated-ground sentence replaced with the float rule | commit 4358b0c |
| I5 | Uncoded 10FDZ rows ride bom_jlc/cpl_jlc; GH Comment column carries the LCSC code (lens-a P2) | RECORDED + ORDER_README — hand-solder lines are DELIBERATELY uncoded per the fab skill; ORDER_README instructs deleting the two 10FDZ rows from any JLC assembly upload (fab is bare-board + 1 SMD part or full hand-solder) | ORDER_README hand-solder list |
| I6 | TP labels staggered between rows, count-across ambiguity (render P2) | RECORDED — next-rev candidate (per-pad callout layout); rows are on-column with the connector pin numbers 1..10 W->E and the 1/10 numerals (I1) anchor the count | render review #2 |
| I7 | No back-side silk ID (render P2) | RECORDED — next-rev candidate; floorplan captions are F.SilkS-only in the generic backend today | render review #3 |
| I8 | J_KEY_MATRIX refdes near edge clips at oblique angles (render P2) | RECORDED — legible in orthographic views; cosmetic | render review #4 |
| I9 | 3 near-zero-angle same-net junctions; via annular 0.15 vs 0.13 floor; GH fanout wedges (lens-b P2 x3) | RECORDED — all DRC-silent, measured cosmetic; annular meets the declared jlc_2layer_default tier floor | redteam_layout |
| 13 | EXTERNAL v1.1 review F1 (BLOCKING): 4 of 5 sensor buses on header pins with NO I2C alt function (GPIO16/18/19/24/26) | FIXED in v1.2 — re-pinned to VERIFIED native pairs (I2C2 GPIO4/5, I2C3 GPIO14/15; RP1 DS RP-008370 fsel table + kernel i2c*-pi5 overlays re-verified by the v1.2 lead); RH pods join the cam buses, RESTORING the brief §3 verbatim two-bus plan; KEY_DATA re-homed GPIO5→GPIO16; pin map published 01_docs/pin_map.md | ADR-0010; 8 E-INV pin_on_net asserts pin the map; 08_reviews/2026-07-24_v1.1_external-llm_full.md |
| 14 | EXTERNAL F2 (BLOCKING/SAFETY): TCAM_THRESH 10k/10k = 1.65V = NTC node at 25C — no 70-75C hard stop existed | FIXED in v1.2 — 68k/10k → 0.4231V → 74.9C with the committed KNTC0603/10KF3950 (B25/85=3987K); solder-select field 8.2k=81/10k=75/12k=69/15k=63C; TP_TCTH added; 60/65/70/75C dual-channel fixture validation = NORMATIVE bring-up gate | ADR-0011 §1; DETAIL_DESIGN #1; ORDER_README v1.2 §3.2 |
| 15 | EXTERNAL F3 (BLOCKING/SAFETY): TEMP_OK absent from latch set; contactor ungated; K_STOP on the fault-killed rail | FIXED in v1.2 — (a) U_FAULTAND.C = TEMP_OK (was N3V3); (b) CONTACTOR_DRV = REQ·WD·ESTOP·TEMP·LATCH_CLEAR via U_CAND1/2; (c) K_STOP coil on new UNGATED 5V_STOP rail + dedicated Q_STOPDRV/D_KSTOP | ADR-0011 §2/§3/§4; E-INV (U_FAULTAND.6, U_CAND*, K_STOP.1=5V_STOP, series chain); red-tested vs v1.1 netlist |
| 16 | EXTERNAL F4 (BLOCKING): STOP did not preempt an active press (one-shot clear = DOOR_OK only; decoders unaffected) | FIXED in v1.2 — STOP_REQ = direct GPIO26; OS_CLR_N = DOOR_OK·STOP_REQ_N; DECx_G1 = DECx_G1_RAW·STOP_REQ_N; U_SR2 deleted; sequence encoded in DETAIL_DESIGN #3 | ADR-0011 §5; E-INV |
| 17 | EXTERNAL F5 (BLOCKING): SN74LVC1G123 retriggerable — ≤500ms not a hard bound; addresses mutable mid-press | FIXED in v1.2 — CD74HC221M96 (non-retriggerable, SCHS166F verbatim quoted in part.yaml; tw 286-436ms worst-band < 500ms); KEY_LATCH_G = KEY_LATCH·PRESS_TIMED_N freezes addresses during PRESS | ADR-0011 §6; 02_parts/CD74HC221M96; E-INV |
| 18 | EXTERNAL "other corrections" pulls item (user scoped IN as priority 7) | FIXED in v1.2 — 100k pull-downs: HOST_AUTH, MCU_RELAY_ENABLE, KEY_RESET_N, RAIL_EN_A/B/RHA/RHE, CONTACTOR_REQ, STOP_REQ; pull-UP: REARM_N | ADR-0011 §7; E-INV direction asserts |
| 19 | EXTERNAL items 8-12 (Ioff power sequencing, DNP pullups/shield options, I2C cable ESD/damping, door EOL truth table, watchdog 1.6s-vs-brief, aux-NTC connector, OVLO ~9.2V) | OPEN — explicitly OUT of v1.2 scope (user disposition); journaled v-next with BRIEF cites (03_schematic journal 2026-07-24); watchdog + OVLO carried as ORDER_README known deviations needing user decision | 01_docs/journal/03_schematic_cooksense.md; ORDER_README v1.2 §4 |
| 20 | EXTERNAL F6: "Board C missing" | STALE at receipt — interposer-v1.0-2026-07-24 was design-SEALED the same day (fab + G2 coupon user-held). System dependency REAL: v1.2 ORDER_README leads with the DO-NOT-CONNECT gate | ORDER_README v1.2 §0; interposer release dir |

---

## v1.2 — safety-chain TRUTH-TABLE lens, 2026-07-25

Source review: `2026-07-25_v1.2_redteam_topology.md` (zero-context redteam-agent,
safety-chain truth-table lens, two rounds; round-1 verdict DO-NOT-ORDER on P0-1,
round-2 verdict **ORDER — conditional** after the fix). Every finding was
independently VERIFIED against the netlist / datasheet before disposition.

**SCOPE DECISION (project owner, explicit): v1.2 fixes P0 ONLY.** Every P1 and P2
below is DEFERRED to v1.3 with a written disposition and, where the reviewer
required one, a MANDATORY order-document mitigation. Nothing here is silently
shipped as fixed.

| id | review file | finding (one line) | severity | verification | disposition |
|---|---|---|---|---|---|
| V12-P0-1 | 2026-07-25_v1.2_redteam_topology.md | WD_PET WDI hold resistor was 100 kΩ where TI specifies 1 kΩ — the supervisor pets itself and the watchdog is silently disabled whenever the host pin goes high-impedance | P0 | **confirmed** — SLVS165O §7.3.4 read verbatim from the committed PDF ("place a 1kΩ resistor from WDI to ground"); §6.5 I_IL at WDI = 140 typ / **190 max µA**, so R_max = V_IL/I_IL = 0.99 V / 190 µA ≈ 5.2 kΩ. 100 kΩ leaves the node at ≈VDD | **fixed — 929b089** (`R_WDPETPD` = 1 kΩ, 0.19 V, 81 % margin). Note this finding is a correction to the ORIGINAL v1.2 P0 fix (ab94de3), which added the resistor at the wrong value. Bench proof is MANDATORY in ORDER_README §5.6 |
| V12-P1-1 | 2026-07-25_v1.2_redteam_topology.md | Watchdog window is 0.9–2.5 s; brief §3 asks 300–500 ms. No fast supervisor exists (the '221's second half is hard-disabled) | P1 | **confirmed** — SLVS165O §6.7 t_tout = 0.9/1.6/2.5 s; netlist shows U_ONESHOT section 2 tied off (2A_N=3V3, 2B=GND, 2R_N=GND, 2Q/2Q_N unconnected) | **deferred — v1.3.** Accepted with reasoning: PRESS is independently hard-bounded to ≈357 ms by the CD74HC221, so the residual is ≤2.8 s of extra contactor-closed time after heartbeat loss, not an unbounded keypress. ORDER_README §8 requires measuring and logging actual t_tout at G4 |
| V12-P1-2 | 2026-07-25_v1.2_redteam_topology.md | Door interlock is INERT — `R_DOORPU` 10 kΩ pulls DOOR_RAW to **3V3** where ESTOP_RAW and MODE_RAW both pull to GND; J_DOOR.2 and .4 are the same net | P1 | **confirmed** — netlist DOOR_RAW = {J_DOOR.2, J_DOOR.4, R_DOORPU→3V3, D_DOOR, U_SCHM.11}; U_SCHM double-inverts so DOOR_OK = DOOR_RAW | **deferred — v1.3** (move R_DOORPU to GND, adopt the E-stop harness convention, and gate selectors/contactor on DOOR_OK). **MANDATORY mitigation, ORDER_README §6.1:** Form-B (magnet-OPENS) reed wired J_DOOR.2→J_DOOR.3 (GND), never to J_DOOR.1; G4 must DEMONSTRATE DOOR_OK=1 closed / 0 open; README states plainly that a broken door cable reads PERMISSIVE this revision. The harness spec is what decides between "inert" and "non-functional" |
| V12-P1-3 | 2026-07-25_v1.2_redteam_topology.md | Hardware over-temp inhibit is fail-permissive on an open/unplugged camera thermistor — node pulls to 3.3 V, TEMP_OK stays HIGH; also outside the LM393 common-mode ceiling (VCC−2 V ≈ 2.93 V) | P1 | **confirmed** — netlist TH_CAM_A = {J_THERM_A.5, R_REF0→3V3_ANALOG, R_SER0, R_HYS1, U_COMP.3}, NTC is off-board; trip threshold 0.4231 V | **deferred — v1.3, FIRST item** (the reviewer's own ranking: its mitigation is runtime software, structurally weaker than every other mitigation here). **MANDATORY mitigation, ORDER_README §6.2:** host cross-checks TEMP_OK against MCP3208 CH0/CH3 every sample and refuses to arm on disagreement; G4 must DEMONSTRATE that an unplugged head blocks arming; README states the LM393 inhibit does not detect an open sensor and the OEM thermal cutoffs remain primary |
| V12-P1-4 | 2026-07-25_v1.2_redteam_topology.md | 595 storage register is undefined when SR_OE_N releases → possible random OEM keypress for ≈357 ms at the instant authorisation is granted; PRESS_REQ has no pull at all | P1 | **confirmed** — SR_OE_N = NAND(MCU_RELAY_ENABLE, WD_OK) only; 74HC595 SRCLR_N clears the shift stages, not the storage register; PRESS_REQ = {U_SR1.7, U_ONESHOT.2} | **deferred — v1.3** (gate SR_OE_N with a term that lags the rail, add a 100 kΩ pulldown on PRESS_REQ). **MANDATORY mitigation, ORDER_README §6.3:** driver invariant — assert KEY_RESET_N low, pulse KEY_LATCH to load zeros, confirm TP_USEL/TP_DSEL open, only then raise MCU_RELAY_ENABLE; G5 fixture test of 20 power-cycle-and-enable rounds with zero relay closures |
| V12-P1-5 | 2026-07-25_v1.2_redteam_topology.md | eFuse OVLO divider trips at ≈9.2 V, not the intended ≈5.7 V — 7.5–9.2 V input is not cut off and D_TVS becomes sacrificial | P1 | **confirmed** — EF_OVLO = R_OVT 100 kΩ / R_OVB 15 kΩ; SLVSE57C §6.5 V_OVLO(R) = 1.20 V typ → 1.20 × 115/15 = 9.20 V. DIP05 coil max is 7.5 V | **deferred — v1.3** (R_OVB 15 kΩ → 26.7 kΩ, one resistor). **MANDATORY mitigation, ORDER_README §5.2:** J_PWR specified as 5 V ±5 % SELV, ≥2 A, keyed Micro-Fit 2-pin ONLY; README records that 12 V IS caught but 7.5–9.2 V is not, and that D_TVS is sacrificial in that window |
| V12-P1-6 | 2026-07-25_v1.2_redteam_topology.md | The opto "dry contact" guarantees only ≈2 mA against a stated ≤30 V/50 mA rating — at 2 mA the phototransistor is not saturated, so a directly-driven contactor can chatter | P1 | **confirmed** — CONTACTOR_DRV (LVC1G11 @3V3) → R_OPTOLED 330 Ω → LED gives I_F ≈ 3.9 mA worst case; LTV-817S TA1 reel is unbinned so CTR_min = 50 % → I_C ≈ 1.95 mA | **deferred — v1.3** (R_OPTOLED → ~150 Ω plus a CTR-binned part). **MANDATORY mitigation, ORDER_README §6.4:** drive the contactor through an interposing relay/SSR with a high-impedance input; never connect a contactor coil to J_CONTACTOR |
| V12-P1-7 | 2026-07-25_v1.2_redteam_topology.md | The isolated contactor loop shares the 1.25 mm-pitch J_ESTOP with SELV logic — CONTACTOR_C (pin 3) sits beside ESTOP_RAW (pin 2), reducing the LTV-817S 5 kVrms barrier to 1.25 mm | P1 | **confirmed** — J_ESTOP (SM05B-GHS-TB, 1.25 mm): 1=3V3, 2=ESTOP_RAW, 3=CONTACTOR_C, 4=CONTACTOR_LOOP, 5=GND | **deferred — v1.3** (move the loop to its own KF350 terminal block). **MANDATORY mitigation, ORDER_README §6.4, written as ONE clause with P1-6** because the P1-6 fix makes this worse: the contactor loop — *including the interposing relay's own coil supply* — is SELV, ≤30 V, never bonded to mains or a mains-referenced common; conformal-coat J_ESTOP |
| V12-P1-8 | 2026-07-25_v1.2_redteam_topology.md | I2C pull-ups sit on the SWITCHED sensor rails, so both buses are held low at power-on and per-rail stuck-bus recovery (brief C6/C7) cannot work | P1 | **confirmed** — R_SDAA/R_SCLA → 3V3_SW_A, R_SDAB/R_SCLB → 3V3_SW_B, while J_RH_AMBIENT shares bus A but is powered from 3V3_SW_RHA | **deferred — v1.3** (move the four pull-ups to the permanent 3V3 rail). **MANDATORY mitigation, ORDER_README §6.3:** host enables RAIL_EN_A/B/RHA/RHE before any I2C transaction; README states that per-rail stuck-I2C recovery is UNAVAILABLE this revision and a wedged bus needs a full board power cycle |
| V12-P2-1 | 2026-07-25_v1.2_redteam_topology.md | Floating CMOS inputs with no actuator consequence (PRESS_REQ has no pull; decoder address lines, Pi control lines, chip selects) | P2 | **confirmed**, and the reviewer's own hunt shows none can energise an actuator: SR_OE_N shares both its terms with KEY_RELAY_ALLOWED, so the rail can never be up while the 595 is tri-stated | **recorded** — add the pulldowns in v1.3 (PRESS_REQ's is folded into the P1-4 fix). Also flagged: the SN74HC595 part.yaml gotcha about "ULN2803 inputs held off by their internal base network" is STALE in v1.2 (the 595 now feeds '238/'221 CMOS inputs) — part.yaml correction queued for v1.3 |
| V12-P2-2 | 2026-07-25_v1.2_redteam_topology.md | 100 kΩ default-state pulldowns sit at the LVC worst-case leakage limit (2 × 5 µA × 100 kΩ = 1.0 V vs V_IL(max) 0.8 V) | P2 | **confirmed** — SCES487I §5.5 I_I = ±5 µA max; MCU_RELAY_ENABLE and STOP_REQ each drive two LVC inputs | **recorded** — typical leakage is orders of magnitude below the limit, so it works in practice; v1.3 drops these two to 10 kΩ for 10x margin |
| V12-P2-3 | 2026-07-25_v1.2_redteam_topology.md | Over-temp comparator hysteresis is ≈3.9 mV (0.32 K), below the LM393's own ±5 mV offset spec; a dither edge latches the board off | P2 | **confirmed** — R_HYS 1 MΩ against a 1.282 kΩ source impedance at the trip point; divider slope −12.1 mV/K | **recorded** — direction of failure is PROTECTIVE (nuisance latch, not a missed trip). v1.3 drops R_HYS to ~150 kΩ for ≈2 K |
| V12-P2-4 | 2026-07-25_v1.2_redteam_topology.md | Relay pull-in headroom is ≈0.36 V at a 5 % low supply; below ≈4.4 V input pull-in is not guaranteed | P2 | **confirmed** — DIP05 pull-in ≤3.5 V; ULN2803A V_CE(sat) ≈0.85 V at 10 mA gives coil ≈3.86 V at 4.75 V in | **recorded** — covered by the same ±5 % supply spec as P1-5 (ORDER_README §5.2); measure TP_5VKR at G5 |
| V12-P2-5 | 2026-07-25_v1.2_redteam_topology.md | EFUSE_FLT_N is pulled to 5V_PROTECTED into a 3.3 V MCP23017 input — an abs-max exceedance held off by the input clamp | P2 | **confirmed** — R_PG 100 kΩ to 5V_PROTECTED; DS20001952C abs-max VDD+0.6 = 3.9 V; clamp current (5.0−3.9)/100 kΩ = 11 µA, far inside the ±20 mA I_IK rating | **recorded** — no damage mechanism at 11 µA; v1.3 moves R_PG to 3V3 |
| V12-P2-6 | 2026-07-25_v1.2_redteam_topology.md | KEY_LATCH_G produces a spurious RCLK edge when the one-shot ends if the host left KEY_LATCH high | P2 | **confirmed** — U_LATCHG = AND(KEY_LATCH, PRESS_TIMED_N, 3V3); the freeze is correct, the un-freeze is not edge-safe | **recorded** — driver invariant in ORDER_README §8: drop KEY_LATCH low before or during the press |
| V12-P2-7 | 2026-07-25_v1.2_redteam_topology.md | No fast, bus-independent host path to drop the external contactor — CONTACTOR_REQ is I2C-only and STOP_REQ is in neither contactor gate | P2 | **confirmed** — CONTACTOR_REQ reaches U_CAND2.6 only from MCP23017 GPA4; STOP_REQ appears in neither U_CAND1 nor U_CAND2 | **recorded** — v1.3 candidate: AND STOP_REQ_N into CONTACTOR_DRV, or home CONTACTOR_REQ on a spare direct GPIO (J_PI 12/18/35 are free) |
| V12-P2-8 | 2026-07-25_v1.2_redteam_topology.md | TEMP_OK's permissive level is produced passively, so a dead or unpopulated LM393 reads "safe" | P2 | **confirmed** — wired-AND of two open-collector outputs with R_TEMPOK 10 kΩ to 3V3 | **recorded** — inherent to open-collector. Covered operationally by the same host cross-check as P1-3 (ORDER_README §6.2), which compares TEMP_OK against the ADC |
| V12-P2-9 | 2026-07-25_v1.2_redteam_topology.md | Nine brief deviations: TH_ENCLOSURE/TH_SPARE have no connector; no per-channel thermistor ESD; MODE_RAW/COIL_EN/KEY_RELAY_ALLOWED leave the board with no ESD or series R; Pi series resistors only on LC_DAT/LC_CLK; R_KEY/R_STOP are fitted 0 Ω not a solder-select field; SHIELD_DRAIN hard-bonded; K_STOP live in MANUAL | P2 | **confirmed** individually against the netlist | **recorded** — ORDER_README §11 carries the list. K_STOP-live-in-MANUAL is DELIBERATE (ADR-0011 §4: the STOP relay must survive the faults it answers). The reviewer's own note that the U/D+PRESS series topology means no single welded selector can press a key is recorded as a design strength |

**Cross-cutting order-document items generated by this review:** ORDER_README
§5.2 (supply ±5 % SELV), §5.6 (watchdog bench proof), §6.1 (J_DOOR Form-B harness
spec), §6.2 (host thermistor cross-check), §6.3 (595 zero-load sequence, I2C rail
enable order), §6.4 (interposing relay + SELV declaration + conformal coat), §7
(the new MANDATORY bring-up ORDER the watchdog fix creates), §8 (t_tout
measurement, KEY_LATCH edge discipline), §11 (recorded deviations).

---

## v1.2 — LAYOUT / THERMAL / POWER-INTEGRITY lens, 2026-07-25 — **TWO P0s, SEAL BLOCKED**

Source review: `2026-07-25_v1.2_redteam_layout.md` (zero-context redteam-agent,
board-and-parts-only). Verdict **DO-NOT-ORDER**. Both P0s were RE-MEASURED
independently by the board lead before acceptance; both reproduce exactly.

| id | review file | finding (one line) | severity | verification | disposition |
|---|---|---|---|---|---|
| V12L-P0-1 | 2026-07-25_v1.2_redteam_layout.md | Mounting hardware bridges keypad↔SELV: H4's keypad→screw→SELV path is 5.879 mm, under the board's own 6.000 mm, with no hardware fitted | P0 | **confirmed** — lead re-measured hole-wall to nearest keypad copper and nearest SELV pour on all 4 layers: H4 (193,52) → RSTOP_MID 5.679 mm, → GND pour 0.200 mm, total **5.879 mm**. H1/H2 keypad-side (3.96/4.61 mm) and 37.65 mm from SELV; H3/H4 SELV-side at 0.200 mm — a chassis plate across them is a galvanic short. Invisible to DRC (an NPTH is a hole, not a conductor) | **OPEN — BLOCKS THE SEAL.** Needs a board change (move/delete H4, or a keepout ring), or an evidenced all-nylon-hardware constraint plus a board marking, which would downgrade it to P1. Neither exists today. v1.3 |
| V12L-P0-2 | 2026-07-25_v1.2_redteam_layout.md | The opto contactor barrier is nullified: 0.175 mm from the isolated secondary to SELV, with all four planes filled under the package | P0 | **confirmed** — lead re-measured with an exact-shape binary search over every CONTACTOR_C/E/LOOP item vs every other net, layer-aware: **min gap 0.175 mm, CONTACTOR_C track ↔ DOOR_RAW via**. Beneath the U_OPTO body: GND fill on F.Cu/In1/B.Cu, 3V3 fill on In2, 5 GND vias, and SDA_B / SCL_B / SHIELD_DRAIN / 3V3_SW_RHE tracks. `02_parts/LTV-817S-TA1/part.yaml` forbids exactly this in its own words | **OPEN — BLOCKS THE SEAL.** Needs a layout change: pour keepouts under and around the opto secondary, the loop moved off the shared 1.25 mm J_ESTOP, and CONTACTOR_C/LOOP routed clear of DOOR_RAW/ESTOP_RAW. v1.3 |
| V12L-P1-1 | 2026-07-25_v1.2_redteam_layout.md | Reed pull-in margin ~6 % at 50 °C, negative at the relay's own 70 °C rating — the ULN2803 Darlington drop, not the copper | P1 | confirmed by the reviewer's routed-resistance graph (copper is 122 mV of a 1.12 V total loss) | deferred — v1.3 (MOSFET array or 12 V coil). Fails SAFE (relay does not pull in). Converges with the topology lens's P2-4 |
| V12L-P1-2 | 2026-07-25_v1.2_redteam_layout.md | The eFuse has NO input capacitor anywhere between J_PWR and U_EFUSE; its keep_short names a net (`5V_SELV`) that does not exist, so a gate reading it passes vacuously | P1 | confirmed — `5V_RPP` = {Q_REV.2, R_OVT.1, U_EFUSE.3, U_EFUSE.4}; all bulk is on the OUTPUT net | deferred — v1.3 (add Cin at the IN pin; fix the part.yaml net name so the budget is checkable). Second instance on this board of intent that no gate can see |
| V12L-P1-3 | 2026-07-25_v1.2_redteam_layout.md | Nothing in the DRC deck enforces the 6 mm isolation — `KEYPAD_ISO` clearance is 0.12 mm, same as Default; separation is held by footprint pitch alone at 2 % margin | P1 | confirmed — `.kicad_dru` holds only width rules; governing minimum is the 6.120 mm intra-relay pad gap | deferred — v1.3, HIGH priority. This is the canon's own "a gate that cannot fail is worthless" applied to the board's headline safety property |
| V12L-P1-4..10 | 2026-07-25_v1.2_redteam_layout.md | eFuse local-passive budgets blown ×4; 8/28 decoupling pairs over budget (worst U_CAND2 12.46 mm); MAX31856 T+ filter 2.4× asymmetric; 12 × 0.60 mm slots with no fab capability model; opto ~3.2 mA vs 50 mA stated; 49 silk-over-pad with those DRC classes disabled; committed drc.json predated the board bytes | P1 | each confirmed with numbers in the review | deferred — v1.3. The opto one converges with topology P1-6; the silk one needs de-collision, not a severity override; the drc.json staleness is fixed by re-running the gate as the last step before staging |
| V12L-P2-1..6 | 2026-07-25_v1.2_redteam_layout.md | Zero annular margin on 1086 vias; 2 unplugged vias in the eFuse EP (POFV is paid); 6 SMD pegs at exactly 0.300 mm from the routed edge; **the milled slots are not on the governing creepage path**; no reference plane over 47 % of the board (by design); acute joints + sub-mm² islands | P2 | confirmed | recorded. P2-4 matters for the next revision: 12 slots are belt-and-braces, NOT the isolation evidence — the barrier is the intra-relay pad gap |

## v1.2 — closing measurement for the R_OS BOM defect (coordinator request)

| id | source | finding | severity | verification | disposition |
|---|---|---|---|---|---|
| V12-BOM-1 | `bom_source_check.py` leg C, 2026-07-25 | R_OS labelled 510 kΩ but coded C25782; the one-shot timing resistor | P1 (would have shipped) | **confirmed against the live JLC catalog**: C25782 = `0402WGF3903TCE` = **390 kΩ**, and BOTH of tscircuit's other auto-selected alternates are also 390 kΩ (C163467 = RC0402FR-07390KL, C2906936 = FRC0402J394). At 390 kΩ, t_w = 0.7·R·C falls from **357 ms to 273 ms** — below the brief's 300–500 ms window, i.e. a press too short for the OEM controller to register | **fixed — 2589dff.** C137961 (RC0402FR-07510KL, 510 kΩ ±1 % 0402, stock 554 618 measured 2026-07-25) pinned explicitly in the tsx so a timing resistor never inherits the auto-picker's choice. C25834 (68 kΩ) and C17902 (10 kΩ) also catalog-verified and appended to the passives ledger. bom_source_check FAIL(3) → **PASS** |

## interposer v1.1 — 2026-07-27 (Board C re-seal, FIX-PASS breadth)

Source review: `2026-07-27_interposer-v1.1_redteam_integrated.md` (zero-context
redteam-agent, ONE integrated lens covering both required lenses — fix-pass
breadth per canon "Verification scoping", because the copper state was fully
reviewed at v1.0 and is PROVEN geometrically unchanged). Verdicts **ORDER /
ORDER**, **0 P0**. Full ledger incl. v1.0's I1..I9 restated:
`07_releases/interposer-v1.1-2026-07-27/verification/dispositions.md`.

| id | review file | finding (one line) | severity | verification | disposition |
|---|---|---|---|---|---|
| I11-R1 | 2026-07-27_interposer-v1.1_redteam_integrated.md | The staging archive failed its own required-artifact gate: 8 REQUIRED artifacts absent, and `source/assembly.yaml` load-bears on ORDER_README sections that did not exist yet | P1 | confirmed — `release_required_check.py` exit 1, "A-EVID FAIL: 8 required artifact(s) missing" | **CLOSED PRE-SEAL.** All eight written, gate re-run to exit 0 and re-shipped. The reviewer read the archive mid-stage and reported the true state rather than assuming it would be filled — correct behaviour |
| I11-R2 | same | The uncoded self-supply BOM row ships a BLANK MPN: `10FDZ-BT` with no `(S)(LF)(SN)` suffix, while the archive's own assembly.yaml warns the `-M` and `-ST` variants are scrap-on-arrival | P2 | confirmed — `fab/bom.csv` row 1 has MPN and LCSC both empty; `02_parts/10FDZ-BT/part.yaml` `mpn: 10FDZ-BT(S)(LF)(SN)` | **MITIGATED IN DOCS + RAISED.** ORDER_README section 2 now names the full MPN with the DO-NOT-SUBSTITUTE variants. NOT fixed in the BOM: F-LEGIBLE grades the MPN column on CODED rows only, so an uncoded row's blank MPN is structurally unreachable by the gate. Fixing it is an `export_jlc_package.py` change — fleet-wide, out of scope for a board respin, raised as a background task |
| I11-R3 | same | The M3 boss-offset open item is UNDER-STATED as "0.04 mm low" — that is the distance to the PASS-band edge; against the drilled nominal the error is 0.19 mm | P2 (re-rating) | confirmed, and the reviewer's slack figure used the boss's ø1.70 NOMINAL where the part MEASURES ø1.60 | **ACCEPTED AND WRITTEN INTO THE ORDER PAPERWORK.** ORDER_README section 0 now leads with 0.190 mm of error against 0.23 mm of clearance (83% of budget) — AND carries the reviewer's more dangerous number: at ø1.70 nominal the total is 0.18 mm and the boss INTERFERES by ~0.01 mm. Bring-up now says dry-fit EVERY connector, not just the first. **A margin that exists only because this lot measured favourably is a per-lot margin, not a design margin** |
| I11-R4 | same | Absolute confirmation of CPL rotation 270 is not obtainable from the curated inputs — it rests on the measured per-LCSC row plus cross-board consistency | P2 (info) | correct; no artifact in this repo can prove JLC's library zero absolutely | **RECORDED; the ritual already exists.** The full evidence chain is in ORDER_README section 3b (pad-fit rms 0.0049 mm vs 5.0792 mm next-best = 1037x separation; jlc_twin re-fit at 0.01 mm, `jlc_offset=0`; the sealed main board shipping the same code at the same orientation at 270.0), closing with the JLC placement-preview look. A-POL raises no single-channel human gate for C2683602 — its row records a NUMBERING-FREE second channel (the unnumbered MP tabs) |
| I11-R5 | verification/pin_review.md | 10FDZ-BT polarity (which housing end carries circuit 1) is UNMEASURED — "pin 1 = the boss end" is DECLARED, not CONFIRMED against the OEM's CN1 | open item | the user measured the part but did not take M9/M10 | **DECLARED AS A NAMED OPEN ITEM, not silently carried.** ORDER_README section 0 open item 2, with the 5.30/8.10 mm discriminator and the statement that the board still WORKS if reversed — only the `TP_M_*`/`KP_*` NAMING would be wrong |

---

## cooksense v1.5 — ADVERSARIAL AUDIT, 2026-07-27 → dispositioned at the v1.6 seal

Source review: `2026-07-27_v1.5_redteam_adversarial.md` (report-only, committed
f8427c5). 0 new P0, 7 P1. **A12 was closed without a reseal in 539ecf0**; A1,
A2 and A3 are closed here, in `cooksense-v1.6-2026-07-27`, a
**DOCUMENTATION-ONLY supersede** — every one of them is a paperwork defect and
none of them moves copper. Each was RE-VERIFIED against the exported netlist by
the v1.6 lead before acceptance, by an s-expression set query that shares no
method with the tsx author, the board generator or `policy_audit` (canon M1);
where the re-verification DISAGREED with the audit it is recorded as a
refinement rather than quietly harmonised.

| id | finding (one line) | severity | verification | disposition |
|---|---|---|---|---|
| A1 | An SHT45 pod harness cross-plugged into `J_MODE` energises the coil rail with all seven AND-chain terms **and** the Manual rail-cut bypassed; ORDER_README §10 modelled 3 of the 5 identical unkeyed GH housings and claimed "any single cross-plug is fail-safe" | **P1** | **CONFIRMED, every number.** `COIL_EN = {J_MODE.4, Q_COILDRV.1, R_COILENPD.1}` — three nodes, no ESD device, no series element, sole hold `R_COILENPD` **100 kΩ** (vs 10 kΩ on `R_DOORPD`/`R_ESTOPPD`/`R_MODEPD`). Five `C189896` SM05B-GHS-TB instances confirmed from the BOM and the netlist; `J_MODE` (196.75, −60.00) is **38.29 mm** from `J_RH_EXHAUST` (186.00, −96.75), both field-accessible. Pod pull-up 10 kΩ (`DETAIL_DESIGN.md:114`) → **3.000 V** on the 2N7002 gate; 4.7 kΩ (BRIEF C7) → **3.152 V**; both above the part's 2.5 V max `V_GS(th)`, so the hazard needs no subthreshold assumption. **REFINEMENT:** the audit's `R ≤ 175 kΩ` bound is correct arithmetic but rests on a 1.2 V minimum-threshold assumption — it is the worst-case-hazard bound and is recorded as such, weaker evidence than the 10 k/4.7 k result. **ROOT CAUSE, newly identified:** the pin-review-Q re-pinning (DISPOSITIONS #6) modelled a cross-plug as a passive BRIDGE between pins — the right model for three dry-contact harnesses, the wrong model for a harness that SOURCES current | **CLOSED IN DOCS, hazard OPEN in copper.** ORDER_README §10 fully rewritten: five housings named, the false fail-safe claim **WITHDRAWN in terms**, a complete **20-cell cross-plug matrix**, a mandatory discipline (§10.5) and the copper fixes explicitly deferred (§10.6). New declared gap 19. **`R_COILENPD` = 100k is now machine-checked** (E-INV `part_value`, RED-verified) so the published 175 kΩ bound cannot drift away from the board. **The copper fix — a keyed/different housing for `J_MODE`, or `COIL_EN` off a field connector — is a USER DECISION for the next electrical revision.** §10.6 records that the obvious 100k→10k trim is NOT sufficient on its own (3.3·10/20 = 1.65 V still turns the FET on) |
| A2 | `WD_OK` / `ESTOP_OK` / `MODE_AUTO_HW` / `DOOR_OK` have no pull resistor at all, falsifying the tsx's claim that "the other twelve are pulled restrictive" | **P1** | **CONFIRMED and EXTENDED — and the audit's characterisation of the false claim is CORRECTED.** All four carry zero pull resistors (netlist set query). Broader measurement: of the **18** nets feeding a permission/gating input, **7 carry a pull and 11 carry none** — the four permissions plus `AND1`, `AND2`, `CTR_SAFE`, `FAULT`, `FAULT_SET_N`, `FAULT_LATCH_CLEAR`, `STOP_REQ_N`. **REFUTATION OF THE AUDIT'S FRAMING:** the twelve the tsx counts are exactly BRIEF D10 item 8's Pi/expander authorization lines (`HOST_AUTH`, `MCU_RELAY_ENABLE`, `CONTACTOR_REQ`, `KEY_RESET_N`, `STOP_REQ`, `RAIL_EN_A/B/RHA/RHE`, `DECU_G1_RAW`, `DECD_G1_RAW`, `REARM_N`) and **all twelve genuinely ARE pulled restrictive** — 11 × 100 kΩ to GND plus `REARM_N` 100 kΩ to 3V3 on an active-low line. The claim is wrong in SCOPE, not in arithmetic. **REFINEMENT:** no single part floats all four — `U_SCHM` (SN74HC14) accounts for `ESTOP_OK`+`MODE_AUTO_HW`+`DOOR_OK`, `U_WD` (TPS3823) for `WD_OK`. **NEW FINDING found while verifying:** MCP23017 DS20001952C §3.5.7 — a `GPPUB` write enables a **100 kΩ internal pull-up** on GPB1/2/3/7, which are exactly these four nets; POR is `0x00` (safe), but one register write converts an indeterminate float into a **deterministic PERMISSIVE** reading of all four. There is no software way to add a pull-DOWN | **CLOSED IN DOCS + FIRMWARE RULE; hardware fix OPEN.** New declared gap 20 states the 11-of-18 measurement, both single-part cases and the scope correction. New **§7a-2** makes `GPPUB = 0x00` a REQUIRED host-firmware invariant. **Four 0402 pull-downs (eleven for the whole chain) are the hardware fix and are a USER DECISION** — copper, therefore not in a docs-only release. **NOT DONE HERE, and it is named rather than hidden:** the false clause still stands verbatim in `03_tscircuit/src/cooksense.tsx:551`, because that file is inside the docs-only supersede's byte-identity set (see the v1.6 CHANGELOG for the reasoning); it is OWED to the revision that adds the pull-downs — the same change that makes the sentence true |
| A3 | `REARM_N` held low forces the NAND latch's forbidden state and permanently defeats the fault latch | **P1** | **CONFIRMED, and its persistence is worse than the audit stated.** `REARM_N = {R_REARMPU.1, U_EXP.26 (GPA5), U_LATCHB.1}` — one driver, no button, no connector pin, no test point. Held low: `U_LATCHB` = NAND(0, ·) = 1 → `FAULT_LATCH_CLEAR` permanently HIGH at `U_AND3.C` and `U_CAND2.B`; with a fault also present both /S and /R are low = Q = /Q = 1, the forbidden state; `U_LATCHA` degenerates to `FAULT` = NOT(`FAULT_SET_N`), a combinational repeater with no memory. The live terms still gate; the MEMORY is lost. **CONFIRMED the power-up property the audit credits:** `WD_OK` is low for the TPS3823 t_d (120/200/300 ms) → latch FORCED SET at every power-up, and MCP23017 `IODIR` POR = `1111 1111` (DS20001952C) means GPA5 is an INPUT at power-on so `R_REARMPU` restores the high. **NEW:** the defeat therefore does NOT survive a 3V3 power cycle but **DOES survive every Pi reboot**, because `EXP_RST_N = {R_EXPRST.1, U_EXP.18}` has **no driver** — nothing on this board can reset the expander. That mechanism was already written into this board's own `R_WDPETPD` invariant and had never been applied to `REARM_N` | **CLOSED IN DOCS.** New **§7a-1** states the driver invariant, the full latch analysis and a **REQUIRED negative bring-up test** (hold `REARM_N` low, induce and clear a fault; the rail must not return — on this revision it will, and the tester is told to expect that and record it). §7 step 3 now says PULSE, in bold, with the §7a-1 pointer. New declared gap 21. **`R_REARMPU` = 100k is now machine-checked** (E-INV `part_value`, RED-verified). Hardware fix — an edge-detect / one-shot on `REARM_N` — deferred to the next electrical revision |
| A12 | The S-VER waiver cited a pin review that does not say what the waiver claimed | **P1** | confirmed by the audit and independently at the fix | **CLOSED WITHOUT A RESEAL — 539ecf0.** The waiver's `why:` now rests on the machine checks `pin_review.md` actually records and drops the fabricated narrative citation. S-VER stays WAIVED, honestly |
| — | **BONUS, found by the v1.6 re-verification, not by the audit** | P2 ×2 | (a) `02_parts/SN74HC14DR/part.yaml` says "unused inputs 3A/4A/5A/6A tied GND, outputs NC" — on this board **all six gates are used** (E-stop, mode, door), a survivor of the v1.0/v1.1 build. (b) `cooksense.tsx:632` and `cooksense.tsx:637-638` **contradict each other** about which `J_MODE` pole is which; the netlist says pins 1-2 = 3V3/MODE_RAW and pins 3-4 = KEY_RELAY_ALLOWED/COIL_EN, so line 632 is the stale one. A harness built from line 632 leaves `COIL_EN` open — fail-safe, but the machine would never arm | **RECORDED as declared gaps 22 and 23**, with ORDER_README §10.1's table named as the harness authority in place of the source comment. Both are prose-only defects in files inside the docs-only identity set or in `02_parts/`; the `part.yaml` correction is deliberately grouped with the tsx correction so one revision fixes the whole inherited-prose family rather than three releases fixing one line each |

**The pattern across A1, A2, A12 and both bonus findings is one pattern:**
prose that was TRUE when written, generalised past its evidence, and then
inherited by the next document that quoted it. The board is correct; four of the
five documents describing it were not. The v1.6 answer is to move the
load-bearing numbers into machine-checked homes (two new E-INV `part_value`
asserts) and to publish the connector table in ORDER_README as the harness
authority, so the next reader does not have to trust a comment.

## v1.7 review battery — 2026-07-28. **RELEASE BLOCKED: 2 CONFIRMED P0s.**

Four lenses ran CONCURRENTLY against the pre-seal staging archive with curated
independent input. Full ledger with the lead's own re-derivation of every
finding: `06_build/tmp/cooksense-v1.7-BLOCKED-2026-07-28/verification/dispositions.md`.

| lens | file | verdict |
|---|---|---|
| red-team topology/protection/ratings | `2026-07-28_v1.7_redteam_topology.md` | **DO-NOT-ORDER** (RT-01, RT-02 = P0) |
| red-team layout/thermal/power-integrity | `2026-07-28_v1.7_redteam_layout.md` | **DO-NOT-ORDER** (P0-1) |
| fresh-context PIN review | `2026-07-28_v1.7_pin-review_changed-and-safety-chain.md` | PASS (4 Q, 3 process) |
| fresh-context RENDER review | `2026-07-28_v1.7_render-review_full.md` | FAIL (R-01 = P0) |

| id | review file | finding (one line) | severity | verification | disposition |
|---|---|---|---|---|---|
| V17-1 | redteam_layout (P0-1) **and** redteam_topology (RT-02), found INDEPENDENTLY | the eFuse OV cutoff is set at **9.20 V** (8.49–9.93 V worst case) by `R_OVT` 100 k / `R_OVB` 15 k, where three documents say 5.5–6 V | **P0** | **CONFIRMED by the lead** from `02_parts/TPS259573DSGR/SLVSE57C.pdf` EC table: `V_OVLO(R)` = 1.13/1.20/1.27 V; ratio 15/115 = 0.130435 ⇒ 9.200 V nominal. Above the DIP05 coil's **7.5 V max** (12+1 relays) and above `D_TVS` SMBJ5.0A's **6.40 V** V_BR min | **BLOCKS THE SEAL. ESCALATED, NOT APPLIED.** Both lenses proposed fixes and **neither is correct**: 22 k breaks the TVS constraint, 57.6 k nuisance-trips at the declared `vin_max` 5.5 V. At `vin_max` 5.5 the admissible ratio window is 1.0354× wide against a 1.0404× ±1 % spread — **no ±1 % divider fits.** Needs a supply-tolerance decision (the same undeclared tolerance behind the E-TOPO gap), or a higher-standoff TVS, or 0.5 % parts |
| V17-2 | redteam_topology (RT-01) | one I²C write (`IODIRB.7=0, OLATB.7=1`) drives `WD_OK` HIGH from `U_EXP.8` against a 1.2 mA-rated supervisor output, defeating the watchdog term in the coil chain, the contactor chain, the fault latch and the '595 output-enable — **and, since v1.7, the expander reset ADR-0020 added** | **P0** | **CONFIRMED by the lead** from the netlist: `WD_OK ⊇ {U_EXP.8 (GPB7, bidirectional), U_EXP.18 (RESET_N), U_WD.1}`. v1.6 had `U_EXP.18` on `EXP_RST_N`; ADR-0020 moved it onto `WD_OK`, so ADR-0020 Decision B's claim is falsified in its own case | **BLOCKS THE SEAL. ESCALATED, NOT APPLIED.** Fix is one 0402 on an existing BOM line — 10 kΩ (C60490) in series to `U_EXP.8` only, leaving `U_EXP.18` and the five gate inputs on the raw net. Also repairs §7a-3's degenerate readback for free |
| V17-3 | render-review (R-01) | `J_ESTOP` / `J_DOOR` are an identical unkeyed pin-compatible GH pair 10.88 mm apart; a swap moves the E-stop off the coil-rail AND chain onto the one-shot clear | **P0 → P1** | **CONFIRMED from the board** (same lib, same LCSC; `ESTOP_OK` → 4 consumers incl. `U_AND1.6`/`U_CAND1.3`/`U_FAULTAND.3`, `DOOR_OK` → `U_OSCLR.1` only). **DOWNGRADED because ORDER_README §10.4 already grades both cells `✗ FALSE-CLEAR` in a published 20-cell matrix** and the reviewer was deliberately denied that document | **P1, next revision.** §10.4/§10.5 disclose and mitigate it; the real fix is a second housing family, which is what ADR-0018 just did for `J_MODE` and did not do here. Independently re-raised as RT-15 |
| V17-4 | render-review (R-04) | the board-side half of the §10.5 mitigation is broken: `J_DOOR`'s silk label is **2.80 mm from J_ESTOP and 2.87 mm from J_DOOR**; `J_ISOLOOP`'s is 0.80 mm from `J_RH_EXHAUST`; 163/228 refdes are >3 mm from their part | **P1** | reviewer measured from the board; 16 refdes sit nearer a different part than their own | **OPEN.** A mitigation that leans on a label pointing at the wrong part is not a mitigation |
| V17-5 | render-review (R-02) | **`J_MODE` and `D_COILEN` refdes are printed into a milled slot and will not exist on the board** | **P1, v1.7-INTRODUCED** | **CONFIRMED by the lead**: notch void x[191.50..200.05] y[48.80..49.80]; `J_MODE` refdes bbox x[194.099..197.801] y[48.386..49.614] **entirely inside**; `D_COILEN` tail inside. `silk_edge_clearance` — the exact rule for this — is one of four silk DRC checks set to `ignore` | **OPEN.** These are ADR-0018's two headline parts, and `D_COILEN` is also POLARITY-FIT-BLIND. Source-side fix in `floorplan.yaml`; must ride the same re-gate as the P0s |
| V17-6 | pin-review | `U_EXP.8` and `U_EXP.18` share `WD_OK`, so GPB7 can never read 0 — the watchdog readback is degenerate | **P1, v1.7-INTRODUCED** | **CONFIRMED by the lead** against both boards | **DOCUMENTED** as new ORDER_README **§7a-3** with the `IODIR`-readback replacement and a bring-up test. Superseded in effect by V17-2's fix |
| V17-7 | redteam_layout (P1-1) | `power_tree.yaml` clears the LDO's 690 mW against "the tab is flooded with 3V3 copper"; the measured F.Cu 3V3 island containing the tab is **7.365 mm² — the pad and nothing else**, 2 vias, ≈99 K/W to In2 | P1 | reviewer's measurement with method stated | **OPEN.** Re-pour + vias, or measure the real 3V3 draw and re-declare `iout_max_A`. Reviewer's own escalation trigger: >~0.2 A ⇒ P0 |
| V17-8 | redteam_layout (P1-2) | the eFuse has **no input capacitor at all** on `5V_RPP`/`5V_FUSED`/`5V_IN`, against SLVSE57C §11's mandated 0.01 µF+ at IN/GND | P1 | reviewer traced the whole input chain | **OPEN.** One 0402. The `keep_short` budget that should have caught it names `5V_SELV`, a net that does not exist here — P-ADJ-UNREACHED landing on the only protection IC |
| V17-9 | redteam_topology (RT-06) | over-temperature trip is **72.81 °C**, not the published 74.89 °C — `DETAIL_DESIGN.md` §1 omits `R_CLMPA/B` 22 kΩ from the sensing chain; hysteresis is over-stated ~8× (0.35 °C, **smaller than the LMV393's own ±7 mV V_IO**) | P1 | reviewer reproduced the doc's 74.89 °C exactly with the documented chain, then recomputed as built | **OPEN.** Worst-case band 69.5–76.1 °C against BRIEF's 70/75 °C — **both edges breached.** Re-centre `R_TH2` and re-publish |
| V17-10 | redteam_topology (RT-07) | `R_PG` pulls `U_EXP.1` (3.3 V I/O, abs max 3.6 V) up to **5 V** — 11 µA into the ESD clamp continuously | P1 | reviewer; `R_PG.2` on `5V_PROTECTED` | **OPEN.** Move `R_PG.2` to `3V3`; the TPS2595 FLT pin is indifferent |
| V17-11 | redteam_topology (RT-13) | the watchdog window is **0.9–2.5 s** against BRIEF's 300–500 ms; the SN74LVC1G123 the dossier points at is not on the BOM, there is no reconciling ADR, and **ADR-0020 consumed the CD74HC221 section that was the cheapest path to it** | P1 | reviewer; TPS3823 dossier `limits.t_watchdog` | **OPEN and newly urgent** — v1.7 closed the implementation path while leaving the gap |
| V17-12 | redteam_topology (RT-03) | `electrical_invariants.yaml:612` states "J_DOOR and J_ESTOP have [a series element]" — **false**; all three RAW inputs are connector-pin/TVS/pull-down/HC14 on one node, and `MODE_RAW` has no ESD device | P1 | reviewer read the netlist against the invariant's own `why:` | **OPEN.** A false statement inside a machine-read invariant's rationale is the inherited-prose class again |
| V17-13 | redteam_topology (RT-14) | a pin1→pin4 short inside the **same** `J_MODE` harness arms the coil rail; the mechanical key cannot help because it is a same-connector fault | P1 | reviewer; ADR-0018 states the hard-short residual but not that 3V3 is three pins away | **OPEN.** 2.2 kΩ (C25879, existing line) in series with the 3V3 feed to `J_MODE.1` ⇒ 0.779 V, row 3 of ADR-0018's own rejection table |
| V17-14 | redteam_topology (RT-04) | the 100 kΩ ADR-0019 defaults land at **1.650 V** against a 100 kΩ `GPPU` — between V_IL 0.800 and V_IH 2.000, i.e. indeterminate, not restrictive | P1 | reviewer | **OPEN.** 10 kΩ (existing line) on the four expander-readback permissions ⇒ 0.300 V, guaranteed LOW. ADR-0019's zero-new-lines argument still holds |
| V17-15 | redteam_topology (RT-05) / pin-review | `TEMP_OK` is an open-drain wire-OR pulled up — an absent comparator pair reads **permissive** into three chains, and it is not among ADR-0019's eleven | P1 | **CONFIRMED by the lead** from `02_parts/LMV393IDR/part.yaml`: "outputs are OPEN-DRAIN NPN (Sec.6.3 p.9)" | **OPEN.** A pull-down cannot fix a wired-OR; needs a supervised bias or a push-pull stage |
| V17-16 | render-review (R-07) | the twelve creepage-comb slots are **0.60 mm** wide against JLC's 1.0 mm standard minimum; the board's own east notch is 1.0 mm | P1 | reviewer measured from `Edge_Cuts.gm1` | **OPEN, ORDER-DAY QUESTION.** The slots ARE the comb; a fab that widens or omits them changes the ≥6 mm claim printed on the board |
| V17-17 | redteam_topology (RT-11) | the reverse-polarity crowbar `D_REVCLAMP` is not guaranteed to trip F1 (I_hold 2.0 / I_trip 4.0 A against a "≥2 A, pref 3 A" supply) and `Q_REV` already blocks reverse polarity without it | P1 | reviewer; SS34 dissipates 1.5 W at 3 A with no trip | **OPEN.** Delete it, or size F1 so crowbar current ≥2× I_hold |
| V17-18 | redteam_topology (RT-10, RT-12, RT-16, RT-17, RT-18) | TVS on the wrong side of the eFuse; contactor loop with no clamp and 3.0 mA of CTR-min drive; no damping/ESD/test-points on the Pi sensor buses and **no "Ioff buffers" despite `ARCHITECTURE.md:49`**; `TH_ENCLOSURE` commissioned with no sensor; no EOL supervision on the door | P1 ×5 | reviewer, each traced from the netlist | **OPEN**, next revision work order |
| V17-19 | render-review (S5, S6) | schematic **design-math FAIL** (zero text items, zero text boxes — no threshold or divider annotated anywhere) and **readability FAIL** (one 900×450 pt page, 235 parts, 0 sheets, 601 global labels / 0 local) | P1 | reviewer counted `(text` = 0, `(text_box` = 0 | **RECORDED as the graded human items.** S5 is also the ROOT CAUSE of V17-1: had the OVLO divider's arithmetic ever been written down, this release would not have needed a P0 to find it |
| V17-20 | render-review (S7) | decoupling **PASS** — every IC with a named supply pin has a dedicated local bypass; **zero unbypassed power pins** | — | reviewer enumerated 17 logic ICs + U_LDO + U_EFUSE + both ULN COM rails | **PASS** |
| V17-P | pin-review process finding | `pin_audit.py:130` joins `parts / mpn / "part.yaml"` literally and falls through silently — **16 of 54 dossiers on this board have `(not in yaml)` on every pin, including `U_EXP`, the one IC this revision re-targeted** | P1 | **CONFIRMED by the lead**; `MCP23017-E-SS/part.yaml` even carries `note_dirname:` for this exact case and nothing reads it | **REPORTED to skills/**, not applied (this agent may not edit `skills/`) |

---

# v1.7b — SECOND review battery (2026-07-28/29). **SEAL BLOCKED: 2 P0s.**

The v1.7 battery of 2026-07-28 (dispositions in `DISPOSITIONS_v1.7.md`, which
this file supersedes as the living ledger — the 08_reviews contract permits
exactly one `DISPOSITIONS.md`) returned four blocking verdicts. Three were fixed
in source and the fourth (silk) was fixed this session, the board was rebuilt to
**DRC 0/0/0** with the full fab battery green, and a FRESH battery of four
zero-context lenses was run against the rebuilt board with input CURATED
(`journal/`, `learnings/`, `STATUS*.md` and `08_reviews/` withheld from all four).

| lens | verdict |
|---|---|
| pin review (FRESH LENS) | **FAIL** — 1 blocking, 8 questions |
| render | **DO-NOT-ORDER** — 1 P0, 4 P1s |
| topology / protection / ratings | **ORDER-OK-WITH-NOTES** — 0 P0, 2 P1s |
| layout / thermal / PI / DFM | **ORDER-OK-WITH-NOTES** — 0 P0, 4 P1s |

**v1.7 IS NOT SEALED. `07_releases/` remains untouched. cooksense-v1.6-2026-07-27
and every release back to v1.0 remain DO-NOT-ORDER (they carry the pin-out-12
relay land).**

## What the battery CONFIRMED — the two headline v1.7 claims both survived

- **The relay land is CORRECT.** Two lenses independently rendered DS p.3 at
  400 dpi and counted the leads on sub-figure **13**: FOUR leads, contact
  14<->8 on one row, coil 2<->6 on the other, row spacing 3 grid units =
  7.62 mm. The land's pads map exactly (pad1=lead 2, pad2=lead 6, pad3=lead 8,
  pad4=lead 14). All 12 instances net correctly and **the coil node set and the
  contact node set are DISJOINT** — `5V_KEY_RELAY` appears on no contact pad and
  `U_SEL_BUS` on no coil pad. The pinout-12 short is GONE. Minimum coil-to-contact
  pad distance over all 48 pads: **8.032 mm**. The render lens adds that the land
  is **CHIRAL** (holes at DIP 2/6/8/14 map to 13/9/7/1 under 180 degrees), so a
  relay physically cannot be inserted backwards.
- **The >=6.0 mm keypad<->SELV isolation claim HOLDS, and the new land IMPROVED
  it.** The layout lens measured it with KiCad's own geometry kernel, zones
  FILLED IN MEMORY (`audit_board.py:154` deliberately excludes pours, so this is
  a genuinely independent method, canon M1), per-layer over 10 322 copper shapes:
  minimum **6.2200 mm** vs the 6.000 floor, on F.Cu, `K_D1.4` (`D_SEL_BUS`) to the
  `COIL_D1_N` track — with a closed-form re-derivation agreeing to 0.0000 mm. The
  intra-package coil<->contact barrier went **6.1200 -> 6.3494 mm** because
  staggering the coil column puts the gap on a diagonal.

## BLOCKING

| id | finding | disposition |
|---|---|---|
| **PIN-P0-1** *(and TOPO P1-1 — THE SAME DEFECT, FOUND BY TWO LENSES WITH NO SHARED METHOD)* | **The v1.7 `U_EXP` pad-1 divider is sized as if the node were a stiff 5 V source, and it is not.** `EFUSE_FLT_N` has exactly four nodes — `U_EFUSE.6` (OPEN-DRAIN), `TP_PGOOD.1`, `R_PG.1`, `R_FLTDIVT.1` — so its ONLY source is `R_PG` = **100 kOhm**. The real chain is 100k + 10k over 22k, ratio **22/132, not 22/32**: the tap sits at **0.833 V** nominal (0.792-0.875 V over the sanctioned 4.754-5.25 V rail). MCP23017 DS20001952C D031/D041 at VDD 3.3 V: V_IL(max) **0.660 V**, V_IH(min) **2.640 V**. The power-good state is 173 mV ABOVE V_IL(max) and 1.807 V BELOW V_IH(min) — the indeterminate band, never a guaranteed HIGH, and on a Schmitt input it reads LOW, i.e. **identical to the fault state. The readback is degenerate: the pin is protected and dead.** Enabling the internal GPPU does not save it (1.216 V / 0.212 V). Second-order: `TP_PGOOD`, deliberately left on the raw node "so the instrument sees the real node", now rests at **1.212 V**, so that rationale is false as built. | **ACCEPTED — FIX REQUIRED, AND IT IS A DESIGN CHOICE, NOT A VALUE TWEAK.** With `R_PG` at 100k there is **no R_top > 0 solution**. Two quantified options: (a) move `R_PG`'s top end from `5V_PROTECTED` to **`3V3`** and DELETE both divider resistors — the TPS259573 `/FLT` is open-drain and indifferent to the pull-up rail, the node then rests at 3.3 V which needs no divider at all, and `TP_PGOOD` reads the real node again; or (b) keep 5 V and delete `R_FLTDIVT`, setting `R_FLTDIVB` ~ 150 kOhm (tap 3.000 V; admissible window 112-257 kOhm), or make `R_PG` <= 9.67 kOhm. **(a) is the recommendation** — it removes two parts instead of adding a constraint. **AND THE ASSERT MUST GROW A LEVEL TERM:** `electrical_invariants.yaml` `part_value`/`pin_on_net` asserts all go GREEN on the broken board, because they check that the divider EXISTS, not that the level WORKS. E-INV was RED-verified 21/21 and still missed this — topology asserts cannot catch an arithmetic error. |
| **RENDER-P0-1** | **`J_ISOLOOP` — the NOT-SELV 30 V contactor terminal — has NO ARTWORK AT THE TERMINAL.** Silk body x[191.82..198.97] y[87.92..102.08]; text printed inside it: **none**; pole legend: **none** (0 of 4). Its own refdes at (189.30, 101.00) measures **4.900 mm** to J_ISOLOOP and **1.300 mm** to `J_RH_EXHAUST` — lead **-3.600 mm**, printed under a different connector, on the same y=101.00 baseline and at h=0.45 against J_RH_EXHAUST's h=0.60, i.e. it is also the less prominent of the two. The only "ISOLATED 30V ... NOT SELV" caption is **155.3 mm away** on a 188x92 board. | **ACCEPTED — FIX REQUIRED, and the previous refusal is WITHDRAWN.** `fix_silk_placement.py` and this session's journal both record that J_ISOLOOP cannot be fixed because "the SE corner is saturated; the nearest site is 33.6/41.9 mm away". **THAT JUSTIFICATION DOES NOT REPRODUCE.** The render lens rebuilt the sweep under the stated constraint set (pads +0.16, silk +0.08, filled courtyards, 0.25 mm edge clearance, 0.1 mm grid, summed-area table) and found `ISO 30V` fits at **(189.05, 93.35) = 6.46 mm** from the block and `30V` at **5.08 mm**, visually confirming ~6x3 mm of blank silk immediately west of it. This is the inherited-defect pattern in its purest form: a measured "impossible" was carried forward across sessions without being re-measured, and it was wrong. Add the caption AND the 1/2/3/4 pole legend at the terminal. |

## Recorded, not blocking — but two of these are OURS

| id | finding | disposition |
|---|---|---|
| **LAYOUT P1-1 / RENDER P1-1 — FOUND BY BOTH LENSES** | **Six safety-connector designators ship at 0.130 mm silk stroke, below the 0.150 mm floor** — `J_ESTOP`, `J_DOOR`, `J_MODE`, `D_DOOR`, `R_DOORPD`, `D_COILEN`, all h=0.450 / stroke 0.130, against 0.150 on the other 243 texts. Gerber confirms sub-floor apertures (`%ADD11C,0.1125`, `%ADD12C,0.120`). | **ACCEPTED — OURS, AND EMBARRASSING.** Cause is `fix_silk_placement.py`'s own `max(0.13, sz*0.2)` at sz=0.45. **The six are EXACTLY the refs passes B and C exist to fix** — the pass that repairs the safety labels is the pass that makes them the thinnest on the board. It also contradicts the tier's `min_silk_stroke: 0.15`, the board's `min_text_thickness: 0.15`, this project's own `SILK-TEXT-THICKNESS` waiver ("thinner would not print"), and the `P-SILK-FN` waiver written THIS SESSION, which calls 0.13-0.15 "at or above the floor" — it is not. One-line fix: floor the stroke at 0.15. Uncaught because `text_thickness` is one of the four DRC classes this project sets to `ignore`. |
| **LAYOUT P1-2 / RENDER P1-4 / V17-16 — THIRD SIGHTING** | 12 fully-internal milled slots at **0.600 mm** against JLC's published 1.0 mm minimum routed slot. No slot-width floor is declared in `fab_tiers.yaml`, `design-policies.md` or any project rule, and **no gate measures one**. | **OPEN, and now escalated.** The slots ARE the isolation comb, so a fab that widens or omits them changes the >=6 mm claim printed on the board. Layout lens verified widening to 1.000 mm is geometrically FREE (stays inside the `iso_gapN`/`iso_pktS` keepouts, nearest copper > 2.4 mm). Escalates to P0 if the capability page confirms 1.0 mm. |
| **TOPO P1-2 (NEW)** | **The reed coil's pull-in margin is computed nowhere and fails the board's own temperature envelope.** DS p.2 Coil Data (pin-outs 10-13): pull-in max **3.5 V**, plus a footnote nothing in this tree carries — "Pull-In, Drop-Out Voltage and Coil Resistance will change at rate of 0.4 %/K". So V_PI = 3.920 V at 50 C (BRIEF's own enclosure level) and **4.200 V at 70 C** (the relay's own max). Available = `5V_KEY_RELAY` vout_min **4.740 V** minus the ULN2803 V_CE(sat) — and `02_parts/ULN2803ADWR/part.yaml` records **no saturation voltage at all and commits no datasheet**; SLRS049's lowest specified point is 100 mA against this board's ~8-10 mA. At the Darlington floor (0.60-0.90 V) the margin is **+220 mV to -80 mV at 50 C and -60 mV to -360 mV at 70 C**. | **OPEN — the most consequential non-P0 in this battery.** It is P1 only because the failure direction is a relay that does not close (restrictive). Owed: commit the ULN2803 datasheet, get a V_CE(sat) at 10 mA, and either re-derive the margin or move the coil rail. Note `K_STOP` is NOT exposed — it is MOSFET-driven off the ungated 5V_STOP rail, +450 mV at 70 C (self-refutation recorded by the lens). |
| **LAYOUT P1-3** | The AMS1117 dissipation PASS is cited against a mounting the board does not have. `power_tree.yaml` claims the tab "is flooded with 3V3 copper ... 55-65 C/W". MEASURED: tab-layer (F.Cu) 3V3 copper within 10 mm = **13.96 mm2**; In1/B.Cu 3V3 = **0.00 mm2**; the 8386 mm2 3V3 plane is on In2 and reached by **2 vias**. 55-65 C/W corresponds to ~645 mm2 of tab-layer copper. | **OPEN.** Same class as the v1.7 battery's P1-c (~104 K/W), now with the copper area measured. Failure direction SAFE (thermal shutdown collapses 3V3, every pull-down asserts). E-TOPO's 51 % PD PASS does not depend on this number, but the rationale in `power_tree.yaml` does. |
| **LAYOUT P1-4** | H4's SELV creepage leg fell from ~3.37 mm to **0.607 mm** because v1.7 placed `D_COILEN` in the corridor ADR-0015 declares load-bearing. Total still passes (~7.21 mm) and the lens's disc model reproduces ADR-0015's own 4.0286 mm keypad leg exactly. | **OPEN.** The total passes; the FASTENER-OD derivation in ADR-0015 and the ORDER_README is now stale and must be re-derived before it is quoted again. |
| **RENDER P1-2** | `J_ESTOP`'s designator leads its rival by only **0.608 mm** (2.300 own / 2.908 to J_DOOR), against +7.94 mm and h=0.60 for the two non-safety RH connectors — the mitigation is weakest exactly where the hazard is greatest. | **RECORDED.** The lens SELF-REFUTED this as a P0: it read all four GH housings' pin nets and every cross-plug permutation fails SAFE under ADR-0019's restrictive pull-downs, so the designator is not the sole mitigation. Fold into the same silk pass as RENDER-P0-1. |
| **RENDER P1-3** | `J_PI` (C35165) and `J_LOADCELL` (C157991) carry LCSC codes in `bom_jlc.csv` but appear on **no CPL row** — JLC is told to buy two parts it is never told to place. The other 14 BOM-not-CPL refs correctly carry a blank LCSC. | **OPEN.** Inverse of canon A-POP (which catches a CPL row with a blank BOM LCSC). A-POP passed here because it only tests that direction. |
| **PIN Q-1** | Every document and invariant in the v1.7 P0-b work calls `U_EXP` pad 1 **"GPA0"**. Pad 1 is **GPB0**; GPA0 is pad 21, which on this board is `RAIL_EN_A`, an OUTPUT. | **ACCEPTED — copper is right, the paperwork is wrong.** Fix in `electrical_invariants.yaml`, the tsx comment and the beacon before anyone writes firmware from it. |
| **PIN Q-2..Q-8** | `EXP_INTB` is a single-node net (B-port carries all six safety readbacks, only INTA reaches the Pi — needs IOCON.MIRROR); GPB6/`TC_FAULT_N` is the only expander input with no series R and no pull-up; `/RESET` on `WD_OK` means every watchdog event wipes IODIR/GPPU/IOCON with no documented re-init; no board I2C pull-ups; **18 of 46 dossiers have no committed datasheet, 7 of them pin-map-load-bearing** (MAX31856, ULN2803, HC595, HC14, LVC1G00, LTV-817S, AMS1117); `SN74HC14DR` part.yaml names pin 12 `6A_Y`; `J_LOADCELL.1` = 5V_PROTECTED sits beside `LC_DAT`/`LC_CLK` which run through 33 Ohm straight to Pi GPIO with only a 5.0 V-standoff PESD — the same defect class v1.7 just fixed, moved to a connector. | **OPEN**, next-revision work order. Q-6 and Q-8 are the two worth doing first. |
| **PIN Q-7b / TOPO P2** | `DIP05-1A72-13L/part.yaml` keys `pins:` by PHYSICAL DIP lead (2/6/8/14) while the footprint and netlist use renumbered pads 1-4 — and the two keyings **COLLIDE**: yaml key `2` = COIL_A, pad `2` = COIL_B. | **ACCEPTED, harmless TODAY only because the coil is non-polar.** Re-key the dossier to the land's pads with the DIP lead as a comment, exactly as the footprint `descr` already does. |

## Self-refutations recorded (canon: record, do not delete)
The layout lens's first copper-to-edge reading of 0.2500 mm was **its own bug** —
off by exactly the 0.05 mm Edge.Cuts half-stroke; the true figure is 0.3000 mm,
at the floor. Topology self-refuted the /SR latch's 7 ms forbidden-state window
(the same term that set it gates U_AND1/U_AND2/U_CAND1 directly, so nothing can
arm), K_STOP's exposure to the coil-margin finding, and a 5 V injection path via
J_LOADCELL (cook-loadcell runs the HX711 DVDD from 3V3). Render self-refuted
J_ESTOP's ownership gap as a P0, and confirmed the relay land is chiral, that
U_EFUSE's EP does get paste (65 % via two unnamed sub-pads), and that `J_MODE` is
genuinely off the GH family in v1.7 (ZH, 1.50 mm, 4-pos) — so the brief's "five
inter-mateable housings" is now **four**.

Also verified clean and worth carrying forward: **all 9 v1.7 stubs present at
their declared coordinates, in-pad, correct net, hole-to-copper 0.2505 /
hole-to-hole >= 0.5011 / annulus 0.0500; 0 unconnected (nothing trapped); 0
courtyard overlaps; both inner planes single unbroken polygons; 0 text-on-text
collisions across 248 texts; 0 texts within 0.20 mm of the outline, the 12 slots
or the east notch (the v1.7 notch regression IS fixed — 0 of 239 refdes overlap
any of the 13 milled voids); board-vs-netlist pad parity 0 mismatches over 827
pads; and the revision silk reads `cooksense SMC0985KS sidecar v1.7`, correct.**

---

# BATTERY OF 2026-07-30 — the FRESH four-lens battery on the post-ADR-0025 board

**Subject:** `06_build/staging/cooksense-v1.7`, board md5
`9f4fd5fae810f40a52b1035df727243c`, netlist md5 `6d83ebe75fd014aa9c3697ad0bd9fc93`.
Four zero-context lenses, `08_reviews/` + journals + STATUS + CHANGELOG denied to
every one of them, so no lens could grade its own or a predecessor's verdict.

| lens | file | verdict |
|---|---|---|
| topology / protection / ratings | `2026-07-30_v1.7_redteam_topology.md` | **DO-NOT-ORDER** |
| layout / thermal / power-integrity | `2026-07-30_v1.7_redteam_layout.md` | ORDER |
| pin review (53/53 dossiers) | `2026-07-30_v1.7_pin-review_FRESH-LENS.md` | ORDER |
| render review | `2026-07-30_v1.7_render-review_FRESH-LENS.md` | ORDER |

**THE 2026-07-29T18:04 BATTERY IS SUPERSEDED, NOT REFUTED.** It graded a board
that no longer exists (J_DOOR still in the netlist, pre-silk-ownership-fix,
pre-bond, fab_v21). Its four DO-NOT-ORDER verdicts are history.

**v1.7 DOES NOT SEAL.** One CONFIRMED P0 with no `fixed` disposition, and a
`DO-NOT-ORDER` on a required red-team lens — the `08_reviews` contract blocks the
seal on either count independently.

| id | review file | finding (one line) | severity | verification | disposition |
|---|---|---|---|---|---|
| B30-01 | redteam_topology | `J_THERM_A/B` specify `C265111`; LCSC stock **5**, `build_quantity` 5 x qty 2 = **10 needed**; `jlc_stock_check` exits 1 | **P0** | **CONFIRMED — STILL OPEN, re-read LIVE a THIRD time 2026-07-30T21:02Z**: `LOW_STOCK(5) C265111 x2 SM08B-GHS-TB stock=5`, A-STOCK **EXIT=1**, verdict line `FAIL: 57/58 coded BOM lines`. Independently re-queried straight off `selectSmtComponentList` (not through the gate) — same number. **NEW AND DECISION-CHANGING: `minPurchaseNum` is 21 against a `stockCount` of 5, so the genuine JST part is not merely SHORT, it is UNBUYABLE AT ANY QUANTITY TODAY** — you cannot order 21 pieces when 5 exist. The restock threshold that actually unblocks option (1) is therefore **21, not 10**; the ORDER_README's earlier framing of "one reel clears it twice over" is true only *after* a reel lands. Trend 0 (07-29) -> 5 (07-30) still says restocking, not discontinued | **WAIVED WITH EVIDENCE — 2026-07-30, USER DECISION. THE SEALED BOM NAMES THE GENUINE `C265111`; THE SUBSTITUTION IS AN ORDER-TIME PATH.** *The argument, which is canon M4's and not a rationale:* **a stock gate measures the WORLD, not the BOARD.** It is red on a fact that changes hourly (0 on 07-29, 5 on 07-30) and that **no edit to this design can fix** — the only in-design "fix" is to specify a different part, which is a purchase, not a repair. *The evidence:* (a) the dated live reading, re-taken by the sealing pass at **2026-07-30T21:33:59Z** both through the gate and independently of it — `C265111` stock **5** MOQ **21**, `C42376901` stock **6030** MOQ **1**, `C22391766` stock **0** MOQ **444**, control `C5620` = **5212**; and (b) **the design is INVARIANT under the remedy, re-measured by a method that is not `jlc_twin`** (canon M1): JLC's own recommended land for each code read out of the EasyEDA `packageDetail` PAD records, this board's copper read with `pcbnew`, translation-only rigid fit — genuine **0.0002 mm**, clone **0.0100 mm** on signal pads 1-8 and **0.0399 mm** on the mechanical tabs, non-mirrored (pin1->pin8 sweeps +8.750 mm on both), pitch 1.2499 vs the board's 1.2500, tab \|x\| 6.2249 vs 6.2250. The 0.0100 REPRODUCES the inherited jlc_twin residual independently; two terms it did not carry are now decomposed — the clone's land is 0.100x0.100 mm larger per pad and its signal-row-to-tab-row separation is 3.1501 mm vs the board's 3.2000, and JLC's two lands **number the mechanical tabs oppositely** (null here, because both tabs are on `GND` on both refs, measured off the board). **A SWAP TOUCHES NO GEOMETRY AND NO GERBER — COUNTED, NOT ESTIMATED:** `C265111` occurs in `fab/bom.csv` (1 row), `fab/bom_jlc.csv` (1), `fab/cpl.csv` (2) and `fab/cpl_jlc.csv` (2), and in **ZERO** of the 11 gerbers and 2 drill files — so at most **8 cells across 4 CSV files**, with `J_THERM_A` staying at (32.0, -96.75, top, 0.0) and `J_THERM_B` at (54.0, -96.75, top, 0.0) either way. *(An earlier version of this row said 'zero bytes of the fab set'; corrected here rather than reworded — this board's CPL emitter writes the LCSC code into the `Val` column.)* **AND THE INHERITED `0.01 mm` WAS NOT EVIDENCE, WHICH IS WHY RE-MEASURING MATTERED:** that figure's whole triple — `0.01` / `jlc_offset=0` / both refs — is **verbatim the GENUINE part's own rows** in this archive's twin log (`twin_run.log:440-441`, `C265111 J_THERM_A OK fit=0.01mm jlc_offset=0`), and a search of all of `06_build/` finds **no jlc_twin artifact for C42376901 anywhere**. `fit=` is jlc_twin's max per-pad residual at `%.2f`, so it prints `0.01` for the genuine part too and **cannot discriminate the two**. The conclusion survives because it was re-measured, not because the inherited number was right (canon M4's headline defect, found in this board's own waiver). *Why NOT the clone now:* choosing it would bake an **UNVERIFIED mechanical retention risk** (does a genuine GHR-08V pod pigtail seat and RETAIN in a clone shroud?) into an immutable release, on the thermistor-pod connectors, and buy nothing — nobody is ordering today. *Why not `not_assembled`:* it forces a board regeneration for a sourcing problem. Naming the genuine part preserves both options at zero cost. *Where it lands:* `ORDER_README` **§5-0** (buyer-facing: the dated numbers, MOQ 21 > stock 5 = UNBUYABLE not merely short, the measured drop-in, and the mate/pull check stated plainly as the one thing a substituting buyer must do), `assembly.yaml sourcing_plan` (the machine-read home, `measured_stock: 5` / `measured_on: 2026-07-30`), and `verification/A-STOCK_waiver.md` (the full argument with raw command output). **The gate is NOT silenced and NOT weakened: `jlc_stock_check` still exits 1 and its FAIL verdict ships verbatim in the archive.** The structural gap — that a seal must assert *"correct"* and *"orderable today"* as one claim — is filed as proposed skill patch **P1** in `verification/owed_skill_patches.md`, not implemented |
| B30-02 | redteam_topology | The LDO dropout margin that turned E-TOPO from FAIL to PASS counts **zero board copper**; +55 mV becomes +16.3 mV (20 C) / +8.6 mV (70 C) | P1 | **confirmed** — orchestrator re-measured the routed copper independently: `5V_IN` **21.74 mOhm** against the lens's 21.75 (0.05 % agreement on the one net that is a simple series run), and 314.53 mOhm summed over all four PWR_IN nets as an upper bound. `power_tree.yaml` lines 85-130 count F1 + Q_REV + eFuse = 190.5 mOhm and no copper at all | deferred — ORDER_README bench measurement (V_IN − V_OUT at U_LDO at 0.3 A, and V(J_PWR) − V(`U_LDO.3`) at full load, which measures the omitted term directly) + `ir_budget_mohm` in `power_tree.yaml` next revision. The rail is unlikely to fail because the 1.300 V dropout is the datasheet's 0.8 A figure applied at 0.3 A — but that conservatism is `power_tree.yaml`'s own declared **OWED** measurement, so the PASS rests on an unquantified term |
| B30-03 | redteam_topology | Over-temp trip is **72.8 C**, not the published 74.9 C, because the fitted `R_CLMPA/B` 22k is not in the documents' arithmetic | P1 | **confirmed, AND IT ADJUDICATES A DISAGREEMENT BETWEEN TWO LENSES.** The render lens re-derived TEMP_OK at **74.89 C** and called it a match; the topology lens got **72.79 C** and called it wrong. **Both are correct arithmetic on different circuits.** Orchestrator traced the netlist: `TCAM_THRESH` = `R_TH1` 68k / `R_TH2` 10k into `U_COMP.2/.6` with **no clamp**, so the threshold VOLTAGE is 0.4231 V and the render lens is right about the voltage; `TH_CAM_A` = `J_THERM_A.5` + `R_REF0` 10k + **`R_CLMPA` 22k** + `R_HYS1` + `R_SER0` + `U_COMP.3`, so the clamp IS on the SENSE node and the TEMPERATURE that reaches 0.4231 V is shifted. Solved: R_par at trip 1470.6 Ohm; with the 22k in parallel the NTC must be **1575.9 Ohm = 72.81 C**, without it 1470.6 Ohm = **74.90 C**. The render lens reproduced the DOCUMENT's model, the topology lens reproduced the BOARD | deferred — ORDER_README + `DETAIL_DESIGN`/ADR-0011/`ARCHITECTURE` correction next revision. **NOT a P0: 72.8 C is inside the brief's own 70-75 C window**, so the board trips where it is allowed to; what is wrong is the published number and the solder-select table derived from it |
| B30-04 | redteam_layout | **H4 mounting hole is four defects at one feature**: 0.850 mm web to the east notch, courtyard overlapping a milled slot, 0.200 mm copper clearance on all four layers incl. the In2 3V3 plane, and no room for a standard washer | P1 | **confirmed, and it CORRECTS THE ORCHESTRATOR'S OWN MEASUREMENT.** I had measured the twelve comb slots and reported a 1.000 mm minimum web; that was slot-END-to-OUTLINE only and **missed the hole-wall-to-notch pair entirely**. Re-measured: `H4` Ø2.700 at (193.000, 52.000), wall to the notch segment (191.5,49.8)-(200.0,49.8) = **0.8500 mm** exactly. H1/H2 2.650, H3 3.650 | deferred — **the ORDER_README DFM query is now about 0.850 mm, not 1.000 mm**, and H4 gains a DO-NOT-FIT-A-SCREW note. A metal M2.5 at H4 sits 0.1 mm from a GND/3V3 sandwich and DRC cannot see it because `min_hole_clearance` is itself 0.2 mm while JLC publishes 0.254 mm |
| B30-05 | redteam_layout | `U_LDO`'s only heat path is 7.600 mm2 of pad and three 0.15 mm vias; **3V3 copper poured on F.Cu = 0.000 mm2 board-wide** against the AMS1117 dossier's own flood-the-tab directive; Tj at TA 70 C reaches 131.1 C at theta_JA 100 | P1 | confirmed-by-report (orchestrator did not re-measure the pad area; the 0.000 mm2 F.Cu 3V3 pour is consistent with the orchestrator's own independent finding that **there are ZERO zones on any PWR_IN net** and that In2 alone carries 3V3) | deferred — ORDER_README bring-up thermal measurement + a poured VOUT tab next revision. Compounds B30-02: the same rail |
| B30-06 | redteam_layout | **21 of 38 `keep_short` budgets name nets that do not exist on this board**, so the gate structurally cannot fail; six ICs would violate, measured `U_SR1` 11.337 mm against a 5 mm budget | P1 | confirmed-by-report, and it is the SAME CLASS the policy audit already WAIVES as `P-ADJ-UNREACHED` (23/38 "budgets DECLARED but graded by NOTHING") — the lens found it independently from the copper rather than from the waiver | deferred — next revision; the waiver is evidence-backed and already declares the blind spot by name. Canon G-VACUOUS territory: a declared blind spot with no fixture reads as diligence and grades nothing |
| B30-07 | redteam_layout | **The K-type thermocouple pair is not a pair**: 132.79 mm2 of enclosed differential loop, mean separation 3.289 mm, split across F.Cu and B.Cu, into a MAX31856 whose LSB is ~0.32 uV | P1 | confirmed-by-report. Ungraded by any gate because its three budgets are among the 21 in B30-06 — a physical defect that a vacuous gate let through, which is the exact shape canon G-VACUOUS names | deferred — next revision (route `TC_POS`/`TC_NEG` as a tight pair on one layer). Bring-up: characterise the cold-junction reading against a known-temperature reference before trusting it |
| B30-08 | redteam_layout | No copper weight declared anywhere: `stackup` count in the `.kicad_pcb` is **0**, absent from `.kicad_pro`, **no `.gbrjob`** in the gerber zip — every ampacity number is unverifiable against what the fab builds | P1 | confirmed-by-report; independently consistent with the orchestrator's A-AMP work, which had to ASSUME 1 oz to compute anything | deferred — ORDER_README states 1 oz explicitly as an ORDER OPTION the human must select, and the next revision ships a `.gbrjob` |
| B30-09 | redteam_topology | `nets.yaml` says the 5 V trunk rides pours; **measured, no 5 V pour exists** — the file disagrees with its own R-POUR waiver, and A-AMP is RED | P1 | **confirmed — INDEPENDENTLY AND FIRST by the orchestrator**, before this lens reported: zero zones on all four PWR_IN nets, 319.5 mm of copper all at 0.5 mm bar the declared eFuse neck. See `verification/build_gates.md`, which also carries the second-gate corroboration: `power_topology` E-TOPO's own advisory says the declared 2 A is **>2x the derived need 0.3 A** | deferred — the patch is written out verbatim in `build_gates.md` and deliberately NOT applied, because a source edit mid-battery changes the bytes four lenses are grading. **The copper is adequate at every reachable current**: `R_ILM` 1.2k sets the eFuse hard limit at 1.79 A, and IPC-2221 gives dT +0.9 C at the 0.50 A operating worst case and +16.2 C at that 1.79 A ceiling, against a 1.93 A 20 C-rise capacity |
| B30-10 | redteam_topology | The eFuse current-limit setpoint is declared nowhere; the declared rail budget (2.0 A) **exceeds** it (~1.79 A) | P1 | **confirmed** — orchestrator derived 2152/1200 = 1.79 A from `R_ILM` = 1.2k (`C138040`, BOM row 4) against the dossier's own 487 Ohm = 4.42 A anchor, independently of this lens. The render lens flagged the same gap from the opposite side (S5: "`R_ILM` = 1.2 kOhm has no derivation anywhere ... UNVERIFIED") | deferred — `power_tree.yaml` gains `ilim_A` with its derivation next revision; ORDER_README states it. **Three lenses and the orchestrator converged on this one number from four directions** |
| B30-11 | redteam_topology | Release identity: the archive is `v1.7`, `source/cooksense.tsx` says **v1.8** in 12 places, the artifacts carry `rev "dev"`, and `power_tree.yaml` refers to a *different* "BLOCKED v1.7 staging" | P1 | confirmed-by-report; the orchestrator confirms the title-block `rev "dev"` and that a `06_build/tmp/cooksense-v1.7-BLOCKED-2026-07-28/` directory exists in the tree | **DECIDED 2026-07-30 — THE RELEASE IS `v1.7`. EXECUTION DEFERRED TO THE SEALING PASS, DELIBERATELY.** *The ruling:* no release has ever sealed as v1.7 (`07_releases/` holds exactly v1.0, v1.1, v1.3, v1.4, v1.5, v1.6 — the numbering already skips v1.2, so gaplessness is not a property this board has), so the number is unclaimed and immutability — which binds only SEALED releases — is not engaged. The decisive constraint is the other way round: **the four fresh lens reviews are APPEND-ONLY VERBATIM EVIDENCE** (08_reviews contract) and their `subject:` headers name *"cooksense v1.7 CANDIDATE, board md5 9f4fd5fa…"*. Renumbering to v1.8 would leave the battery grading a release that does not exist, with **no legal way to edit those headers**, so the seal gate "both red-team lenses present with ORDER" could never be satisfied for v1.8 without re-running the whole battery. Renumbering costs a battery; keeping v1.7 costs nothing. *Consequences recorded:* (a) the **12 `v1.8` strings in `03_tscircuit/src/cooksense.tsx` are ALL COMMENTS** — verified line by line, not one is a version field — describing ADR-0023/24/25 work that ships IN v1.7; they are retired in-flight numbering and are hereby **NON-NORMATIVE**: release identity is set by CHANGELOG + archive + `MANIFEST.txt`, never by source comments; (b) `06_build/tmp/cooksense-v1.7-BLOCKED-2026-07-28/` is a *superseded candidate* in scratch, not a release, and its own README already says so. *Why execution waits:* editing the `.tsx` comments changes `source/cooksense.tsx` md5 `c42fada9…`, which all four lenses recorded — i.e. a **comment cleanup would invalidate the battery**. The `rev "dev"` title block comes from `circuit_json_to_kicad_sch.py --rev` (default `"dev"`) and needs a schematic regeneration; the seal ritual stages and stamps but does NOT regenerate. So the reconciliation is ONE atomic rebuild that must be run in the same pass as the seal, together with whatever the B30-01 sourcing decision forces, and graded ONCE. **EXECUTED AND CLOSED 2026-07-30 IN THE SEALING PASS.** The rebuild was run ONCE, folding both halves. *(a) The comment cleanup:* the count is **13, not 12** — re-verified by a METHOD rather than by eye (a comment-span parser over JSX `{/* */}`, block `/* */` and line `//` spans placed all 13 occurrences inside comments), and all 13 now read `v1.7`. *(b) The title block:* `circuit_json_to_kicad_sch.py --rev` is now passed explicitly by `03_src/cooksense/rebuild_schematic.sh` — fixed in SOURCE, never by hand-editing `04_kicad/` (canon M3) — and the sealed sheet reads `(title_block (title "cooksense") (date "2026-07-30") (rev "v1.7")`. **THE NETLIST md5 CHANGED AND THE NETLIST DID NOT, PROVEN RATHER THAN ASSERTED:** 198 nets both sides, 239 components, 806 nodes, **0** nets with a differing node set, **0** components with a differing (value, footprint), and the `tstamps`/`date`/`rev`/`tool`-normalised md5 is byte-identical at `900941caafe43eb6de7347171a8eb443` — the whole delta is the title block plus KiCad's per-run UUIDs. `cooksense.kicad_pcb` md5 **`9f4fd5fa…` UNCHANGED**. The driver's own safety-chain sanity check passed **22/22** (17 node-count assertions + 5 must-not-exist nets); DRC re-run **0/0/0 exit 0**; `policy_audit` **exit 0, FAIL=0**. Fleet consequence measured and filed as skill patch **P3**: **33 of 33** sealed release schematics in this repo carry `(rev "dev")` — v1.7 is the first that does not |
| B30-12 | redteam_topology | The last field permission is a single-die SPOF: all four stops now originate in `U_SCHM` stages 1-2, `MODE_AUTO_HW` is stages 3-4 of the same package, `MODE_RAW` is the only field input with neither series element nor clamp, and the expander readback samples the same net so software reads the lie back | P1 | confirmed-by-report; ADR-0025 lines 545-546 carry the residual forward explicitly, so this is a KNOWN and ACCEPTED residual rather than a discovery | deferred — the cheap mitigation is one source line (680 Ohm + PESD on `MODE_RAW`, matching `ESTOP_RAW_IN` and `COIL_EN_IN`, both parts already on the BOM). ORDER_README + next revision |
| B30-13 | redteam_topology | Brief's 300-500 ms watchdog is not implemented; the only watchdog is the TPS3823's 0.9/1.6/**2.5 s** | P1 | confirmed-by-report | deferred — ORDER_README declares the real timeout; a brief amendment or an added `SN74LVC1G123` is a next-revision decision |
| B30-14 | redteam_topology | No Ioff buffers and no 22-100 Ohm series elements on `J_PI`, which `BRIEF` and `ARCHITECTURE:58` both claim | P1 | confirmed-by-report | deferred — ORDER_README + next revision |
| B30-15 | redteam_topology | Contactor loop declared <=30 V / <=50 mA; the opto can guarantee **2.66 mA** (19x short) and there is no freewheel path anywhere on the isolated side for an inductive load | P1 | confirmed-by-report | deferred — ORDER_README: the loop drives a HIGH-IMPEDANCE input only, and any inductive load needs an external freewheel. Next revision re-sizes `R_OPTOLED` |
| B30-16 | redteam_topology | Six of eleven protection refs have dossiers with **no `limits:` block at all**, so their clamp-vs-protected pairs are UNVERIFIABLE | P1 | confirmed-by-report | deferred — `02_parts` dossier debt, next revision. Honest UNVERIFIABLE beats an assumed pass |
| B30-17 | redteam_topology | The v1.7 commission fact-lock names `DIP05-1A72-12L x13` — the board is `-13L x12`, and `-12L` is the pin-out its own dossier says shorts the coil rail to the keypad bus | P1 | confirmed-by-report. **This is the DO-NOT-ORDER defect of v1.0-v1.6 surviving in the paperwork of the release that fixes it** | **FIXED 2026-07-30** — `01_docs/BRIEF.md` fact-lock row "hard-cell sourcing class" corrected `DIP05-1A72-12L ×13` -> **`DIP05-1A72-13L` ×12** (both fields were wrong). Re-measured against the artifacts before editing: `fab/bom.csv` row 37 = `DIP05-1A72-13L` over exactly **12** designators (K_D1–K_D4, K_PRESS, K_STOP, K_U1–K_U6), footprint `Relay_StandexDIP_1A_pinout13`, and `02_parts/` contains **only** the `-13L` dossier. The corrected row now also carries the fact the dossier had been keeping to itself: **every distributor quote recorded in this tree (Mouser 876-DIP05-1A72-12L, DigiKey DIP05-1A72-12L-ND) is keyed to `-12L` and DOES NOT TRANSFER**, no `-13L` distributor stock has ever been read, so **distributor sourcing for the correct code is still OWED** — the wrong code was also the only one with a purchasing path, which is why this row could have been acted on. Correcting entry appended to `01_docs/journal/01_commission.md` (append-only; the 2026-07-22 entry naming `-12L` is historically correct and was NOT edited). The stale `-12L` in this ledger's own cross-cutting list fixed in the same pass. **Netlist impact NONE** — `BRIEF.md` is not a build input and is not in the staging archive; board md5 `9f4fd5fa…` unchanged, DRC re-run **0/0/0 exit 0** afterwards |
| B30-18 | redteam_topology | A-POP FAIL in the archive: no MANIFEST declares the 16 not-assembled refs | P1 | **confirmed and TIMING-EXPLAINED** — the lens read the archive before the orchestrator wrote `MANIFEST.txt`, which is written at STAMP time by the seal ritual. The CPL itself is correct and the lens verified all 16 refs absent from its 206 rows | deferred to the stamp step — resolves automatically once the MANIFEST exists. Recorded rather than dismissed because the gate was genuinely RED on the bytes graded |
| B30-19 | render-review | `J_PWR` owns no legend: `5V SELV IN` is 7.80 mm from `J_PWR` (rank 6 of 243) and **1.28 mm from `F1`**; the nearest silk word to `J_PWR` is `U_LDO` at 0.58 mm | P1 | confirmed-by-report; canon P-SILK-OWN class, and `policy_audit` already WAIVES P-SILK-OWN with three named centroid artifacts — **this is a fourth the waiver does not name** | deferred — ORDER_README carries the power-entry identification explicitly; silk fix next revision. A legend nearer another connector misdirects whoever plugs the cable in, which is the exact reason the rule exists |
| B30-20 | render-review | The NOT-SELV pole map `1C2L3L4E` is **0.69 mm from `J_RH_EXHAUST`** and 2.71 mm from `J_ISOLOOP`, tying `J_RH_EXHAUST`'s own refdes, same height and baseline 5.27 mm apart — the bottom silk line reads `J_RH_EXHAUST   1C2L3L4E` | P1 | confirmed-by-report. **This is the SAME CLASS as the SE-corner P0 that ADR-0025 was partly written to close** (a 30 V NOT-SELV legend printing next to a low-voltage sensor connector), reappearing on a different text object | deferred — not P0 because the block itself is correctly marked `NOT SELV` / `ISO 30V` (both measured adjacent by this same lens) and pad 1 is square. ORDER_README §11 pole legend is the authority; silk fix next revision |
| B30-21 | render-review | **Four refdes print nowhere**: `R_REF4`, `R_SER2`, `R_SER3` and **`R_MODEPD`** are invisible on F.Silkscreen and have **no F.Fab duplicate** — F.Fab carries the Value (`10kΩ`, shared by 20 parts) | P1 | **confirmed by an exact independent cross-check.** `waiver_provenance` in this same pass reported `4 UNBACKED W-MACHINE` refdes waived by `04_kicad/refdes_waiver.json` — and the four names are **`R_MODEPD`, `R_REF4`, `R_SER2`, `R_SER3`, identical to the lens's list**. Two methods, one from the silkscreen pixels and one from the waiver file, naming the same four parts | deferred — `R_MODEPD` is an ADR-0019 restrictive-default pull on the safety chain and it cannot be identified on the assembled board. ORDER_README names the four with their coordinates; canon P4 (silk AND fab) fix next revision. **The machine waiving its own output and `policy_audit` reading that back as evidence is canon M1's own failure mode and it is already named as debt** |
| B30-22 | render-review | The whole PDF package is unidentified: all 11 pages of `pcb_layers.pdf` and both of `assembly.pdf` have blank Title/Sheet/Date/Rev, and no page names the layer it plots | P1 | **confirmed, and it is the ORCHESTRATOR'S OWN ARTIFACT** — I regenerated both PDFs on 2026-07-30 with `--include-border-title`, but the board's title block is empty and `rev "dev"` (B30-11), so the border renders blank. `--mode-multipage` does not label pages | deferred — compounds B30-11. Fix is the title block in source plus `--mode-separate` (one file per named layer), and a layer index in the ORDER_README meanwhile |
| B30-23 | render-review | S6 schematic readability: **EFFORTFUL.** The 5 V protection chain is four net-label string hops with no drawn path; `GND` is 104 independent stubs; ink occupies 59 % of the page width | P1 (S6 HUMAN row) | confirmed-by-report | deferred — this is the canon S6 HUMAN verdict for `policy_audit`. Recorded as EFFORTFUL, not PASS |
| B30-24 | render-review | S7 decoupling adjacency: **FARMED / FAIL.** Median IC-to-its-decoupler 54 mm on a 129.5 mm-wide drawing; best pair 27.3 mm; no pair adjacent | P1 (S7 HUMAN row) | confirmed-by-report, and it is the SCHEMATIC's layout, not the board's — the physical decoupling distances are B30-06's separate finding | deferred — this is the canon S7 HUMAN verdict. **FAIL, recorded as FAIL** |
| B30-25 | pin-review | `J_PI` `part.yaml` `mates:` says the socket receives Pi J8 posts "from below", contradicting its own gotchas, the board silk `PI 40-PIN RIBBON (SIDECAR)`, the title block and `floorplan.yaml`. Built as a direct stack every odd/even pair swaps: **5 V onto the 3V3 MCP23017's SDA** | QUESTION (P1) | confirmed-by-report; and this is a RECURRENCE — ledger row 5 above dispositioned the same contradiction on 2026-07-23 by rewriting the gotcha, and the `mates:` field kept the wrong claim | deferred — **the `mates:` field must be corrected**; the board is right under the sidecar reading, which every other artifact states. A doc contradiction that survived one disposition pass is a doc contradiction that will survive another unless the field itself moves |
| B30-26 | pin-review | A GH-5 pod plug seats at 0 mm post offset in the GH-10 `J_KEY_MATRIX` shroud and lands `3V3_SW`->KP_U1, `GND`->KP_U2, `SDA`->KP_U3, `SCL`->KP_U4, `SHIELD`->KP_U5 — **bonding SELV to the isolated keypad domain** | QUESTION (P1) | confirmed-by-report. Reaches no permission, but reaches the ISOLATION BARRIER, which is this board's one physical safety claim | deferred — ORDER_README harness-labeling discipline (§10) gains the keypad connector explicitly; a mechanical key on `J_KEY_MATRIX` is the next-revision fix. **The layout lens independently proved the barrier holds at 6.3100 mm against BOARD copper — this is a HARNESS path, which no copper measurement can see** |
| B30-27 | pin-review | `U_ULNB` pins 5-8 (IN5-IN8) float while spare IN4 is tied to GND; no "input open" behaviour is specified for the TBD62083A | QUESTION (P2) | confirmed-by-report; bounded — OUT4-OUT8 are unconnected | recorded — bounded by construction. Tie them in the next revision for symmetry with IN4 |
| B30-28 | pin-review | `U_TC`'s pin map comes from **EasyEDA CAD, not the datasheet**; `part.yaml` marks it PENDING *this* review and it cannot be closed (three MAX31856 fetches timed out; a scratchpad PDF turned out to be a wiki page and was rejected) | QUESTION (P1) | confirmed-by-report — **and the rejection is the finding working.** A reviewer that discarded a wrong document rather than reading it is doing the job | deferred — the MAX31856 datasheet must be committed to `02_parts/` and the pin map re-derived. UNVERIFIED, stated, not silently passed |
| B30-29 | pin-review | `U_EXP` pin 19 (INTB) sits on `EXP_INTB`, the **only single-node net on the board**; all 31 other deliberate opens use `unconnected-*`, so this one is invisible to a DRC unconnected count | QUESTION (P2) | confirmed-by-report | recorded — deliberate open that does not declare itself as one. Rename to `unconnected-*` next revision so the DRC can count it |
| B30-30 | pin-review | 6 of 53 dossiers carry `(not in yaml)` for every pin function despite complete maps in `02_parts/`; for the 12 `K_*` the cause is diagnosed — `part.yaml` keys by DIP lead (2,6,8,14), the land uses pads 1-4, and nothing bridges them. `J_TC` and 12 `Q_*` have no dossier at all | QUESTION (P1, gate defect) | confirmed-by-report; same family as the `pin_audit` `>3 pads` filter already recorded in the routing journal | deferred — **an OWED `skills/` patch** (`pin_audit.py` lead-vs-pad key bridging), reported not applied |
| B30-31 | redteam_topology | ADR-0023's coil table has two arithmetically wrong cells (V_PI(+55) = 3.990 not 4.140; V_PI(+65) = 4.130 not 4.320) and is non-monotonic | P2 | confirmed-by-report — the lens then **re-derived the whole decision independently from the real rail floor (4.6937 V, not 4.740) and got +443 mV at +70 C**, ampere-turn cross-check 7.738 mA vs 7.00 mA required | recorded — conservative errors, verdict unaffected. **The ADR-0023 decision is SOUND and was re-derived by a lens that could not see it being made.** Table cells corrected next revision |

## v1.7 TOPOLOGY RE-GATE, 2026-07-30 — `verdict: DO-NOT-ORDER`, `P0-1: NOT RESOLVED`

Review: `2026-07-30_v1.7_redteam_topology_REGATE.md`. Targeted re-gate of B30-01
only, run by a lens given the prior topology review and told to reach its own
verdict. **It blocked the seal, and it was right to.** It reproduced every
number in the archive independently — DRC 0/0/0 exit 0 standing alone, the live
stock/MOQ read, and the land-pattern fit to four decimals — and then found
**five things the archive got wrong, one of them in the remedy instruction the
whole sourcing block exists to give.**

| id | finding | severity | verification | disposition |
|---|---|---|---|---|
| **RG-P0** | **B30-01 is NOT RESOLVED.** P0-1's own exit conditions were "a re-query or a mate-verified substitution". The re-query was performed and made the finding WORSE (`stockCount` 5 vs `minPurchaseNum` 21 = unbuyable at any quantity, not short by five); the substitution is correctly NOT mate-verified because nobody has physical parts; and the documented remedy was mis-instructed (RG-P1-1) | **P0** | **confirmed independently** — the lens re-read the catalog with its own parser at 2026-07-30T21:48:40Z and reproduced stock 5 / MOQ 21 / clone 6030 / control 5212, then swept **all 58 coded lines** and confirmed `C265111` is the only one with MOQ > stock | **OPEN — THE SEAL DID NOT HAPPEN.** The lens states in its own words that it *"would accept the seal"* — the M4 argument in `A-STOCK_waiver.md` §1 is sound — but that the verdict field it must fill asks whether the release can be ORDERED, and it cannot. **That gap is the finding**: the release model has ONE verdict for TWO claims. Filed as skill patch P1; NOT worked around here. The unsealed release directory that had been staged under `07_releases/` was REMOVED rather than left implying a seal, so `07_releases/` still holds exactly the six sealed cooksense releases v1.0-v1.6 and no v1.7 |
| **RG-P1-1** | **§5-0's remedy edits the wrong file.** It said *"you edit one cell of `fab/bom.csv`"* — but JLC receives **`bom_jlc.csv` and `cpl_jlc.csv`** (`export_jlc_package.py`'s own header says so), and the CPL's `Val` column carries the LCSC code because `fp.GetValue()` on these two footprints IS `C265111`. A buyer following the instruction exactly edits a file JLC never sees and orders the unbuyable part | **P1** | **confirmed by cell census, twice independently** — the sealing pass found 6 cells across 4 files while writing the block; the lens reproduced the census to the line and column AND identified the upload-path half, which the sealing pass had missed entirely | **FIXED 2026-07-30.** `ORDER_README` §5-0 now (a) marks which two files JLC actually receives, (b) publishes the full 6-cell census with line and column, (c) states that the CORRECT remedy is to change `03_tscircuit/src/cooksense.tsx` lines 1216/1218 and REGENERATE (canon M3), with hand-editing all six cells as the fallback, and (d) retracts the wrong instruction in place rather than rewording it. Same correction in `assembly.yaml sourcing_plan` and `A-STOCK_waiver.md` |
| **RG-P2-1** | *"changes ZERO BYTES of the fab set / CPL is invariant"* is false as measured | P2 | confirmed — and the lens confirms the **geometric** half in full: 0 occurrences of the code in all 13 zip members, **0 drilled pads** in either `J_THERM` footprint so no hole can move, footprint unchanged, and every CPL coordinate/layer/rotation a function of the board | **FIXED** — the claim now reads "zero bytes of the **gerbers, drill and CPL geometry**", which is true and is sufficient for the waiver's argument. The "zero bytes of the fab set" form is RETRACTED in all four places it appeared |
| **RG-P2-2** | The fit table omits mechanical-tab pad SIZE — the one term governing a retention tab, on the exact axis the waiver declares unverified. Board tab **1.000 × 2.700**; JLC's land for the **genuine** part **1.210 × 2.700** (board 17.4 % narrow); the clone's **1.000 × 2.500** — **the board's tab width matches the CLONE, not the genuine part** | P2 | confirmed — a translation-only residual is structurally blind to pad size; the sealing pass had measured the size deltas and then failed to carry them into its own tables | **FIXED** — tab sizes published in the `ORDER_README` §5-0 table, the `A-STOCK_waiver.md` §3 table and `assembly.yaml`, each stating that "the board IS the genuine part's land" holds on the eight signal pads and fails on both tabs. Pre-existing library difference, independent of the substitution, and it cuts TOWARD the clone |
| **RG-P2-3** | §5-0 stated a safety consequence **backwards, in the alarming direction**: *"a pod that falls out removes the `TEMP_OK` term from the safety chain."* It **asserts** the term restrictively | P2 | **confirmed by measurement on the board's own values** — pod out gives `TH_CAM` = 22/(10+22) = 0.68750 of rail against an open-detect threshold of 100/(62+100) = 0.61728, margin **0.07022 × V_rail = 231.7 mV at 3.300 V and 224.8 mV at the 3.201 V corner, rail-independent and positive everywhere** ⇒ `TEMP_OK` LOW ⇒ `KEY_RELAY_ALLOWED` and `CTR_SAFE` drop and the latch sets. `R_CLMPA` exists to make exactly this happen | **FIXED** — §5-0 now carries the arithmetic and states the real cost: **nuisance latched stops**, not a defeated interlock. A safety claim wrong in the SAFE direction is still a defect in a buyer-facing document, and it is retracted in place |
| **RG-P2-4** | `ORDER_README` line 273 was an H2 reading **"ORDERABLE — v1.7"**, 693 lines above the section saying it is not orderable; the top-of-document banner carried nothing about sourcing at all | P2 | confirmed by line number | **FIXED** — the heading now reads **"DESIGN-CLEAN"** with an explicit note that it is about the design and not about buyability, and the top-of-document banner slot now carries the sourcing block and points at §5-0 before any other section |
| **RG-P2-5** | Three more BOM lines carry a reel MOQ far above the build need — `C25076` MOQ 837 vs need 10, `C11702` MOQ 914 vs need 45, `C25105` MOQ 887 vs need 10 — disclosed nowhere | P2 | confirmed by a live sweep of all 58 coded lines, which **also proves `C265111` is the only line where MOQ exceeds STOCK** — new evidence that strengthens the B30-01 disposition rather than weakening it | **recorded** — cost-only on 0402 passives, not blocking. Folded into skill patch **P4** (A-STOCK has no MOQ term) so the patch is scoped to the real population rather than one line. `J_PWR` `C587657` also drifted 140 → 130 between the two reads, which is the ordinary catalog churn the block already warns about |

## What the battery did NOT find, stated because a silent pass is not a result

- **No consistently-wrong-together artifact set.** The topology lens hunted for
  exactly that class from pads rather than prose: `D_TVS` pad 1 = cathode on
  `5V_PROTECTED`; `Q_REV` drain-to-supply, the only P-FET handedness that blocks
  reverse polarity; `Q_COIL` deliberately the opposite handedness for a load
  switch; `D_REVCLAMP` downstream of F1 so a reverse hookup trips the PTC.
- **The keypad barrier holds at 6.3100 mm with ZERO domain crossings**, measured
  by the layout lens's own polygon engine over raw copper with the DRU never run
  — and it CHECKED the rule's `J_KEY_MATRIX` exemption instead of trusting it.
- **The new coil driver maps 18/18** against its datasheet figure, a 90-degree
  rotation with no mirror, both instances byte-identical, all 11 coil outputs
  `INn` <-> `OUTn` correct through the netlist.
- **The 12 reed coil and contact domains are provably disjoint** (14 nets each,
  intersection empty, and the contact set's closure through every resistor on the
  board touches no rail), and the 4-hole pattern is not 180-degree symmetric, so a
  backwards relay physically will not fit.
- **The door channel is completely gone** — 0 `DOOR_*` nets in the 198-net list —
  and unfitted `J_ESTOP` measures **1.62 mV** on `ESTOP_RAW`, stopping the board
  four independent ways.

---

# ⬇ FOLDED IN 2026-07-30 AT THE v1.7 SEAL — the v1.7 review-battery ledger

**Why this is here and not in its own file.** `DISPOSITIONS_v1.7.md` existed as a
SECOND findings ledger beside this one from 2026-07-28. The `08_reviews`
contract permits exactly one — `DISPOSITIONS.md`, "the living findings ledger" —
and `contracts_audit.py --projects` reports the extra file as a C-ALLOW
violation. It is the same second-home shape this repo keeps paying for
(`lcsc_mpn_map.csv` restating the MPN `02_parts/` already held; cooksense v1.1's
13 CPL rows contradicting its own MANIFEST; four fleet beacons naming the wrong
release). **The preferred fix is always to delete the restatement, not to
machine-check it**, so the content below is moved VERBATIM into the one home and
the second file is removed. Nothing is paraphrased and nothing is dropped.

# v1.7 candidate — review battery dispositions (2026-07-28)

FOUR independent zero-context lenses, launched concurrently, input CURATED
(journal/, learnings/, STATUS*.md and 08_reviews/ withheld from all four).

| lens | verdict |
|---|---|
| topology / protection / ratings | **DO-NOT-ORDER** (P0-1) |
| render | **DO-NOT-ORDER** (P0-A, P0-B) |
| layout / thermal / PI | **DO-NOT-ORDER** (P1-b; no P0) |
| pin review (FRESH LENS) | **FAIL** — 1 blocking pin-map FAIL x12 instances, 1 blocking electrical |

**SEAL BLOCKED. v1.7 is NOT sealed. cooksense-v1.6-2026-07-27 remains LIVE — BUT SEE PIN-P0, WHICH IMPLICATES v1.0-v1.6 TOO.**

**CORRECTION, recorded rather than quietly edited:** the first cut of this file
said "pin review PASS". That was the main loop misreading
`2026-07-28_v1.7_pin-review_changed-and-safety-chain.md` — a DIFFERENT review,
committed earlier in `9a02c52` against an earlier v1.7 state — as the output of
this session's fresh lens. The fresh lens returned **FAIL**. Both files are kept;
neither supersedes the other.

## Blocking

| id | finding | disposition |
|---|---|---|
| **TOPO P0-1** | v1.7 added `R_WDOKSER` to `U_EXP.8` only; GPB1-GPB5 sit directly on MODE_AUTO_HW / ESTOP_OK / DOOR_OK / TEMP_OK / FAULT. One I2C transaction defeats four safety terms. Contention 0.863 V weakest / 2.055 V realistic vs LVC1G11 V_IL 0.8 V — no datasheet corner gives a guaranteed LOW. TEMP_OK worst: 2.48 V, feeds coil rail + contactor + fault-SET, and is the only term with no independent physical backup. | **ACCEPTED — FIX REQUIRED.** 10k (C60490, existing line) in series into U_EXP.2/.3/.4/.5/.6, consumers on the raw nets; plus matching pin_on_net asserts, RED-verified. |
| **RENDER P0-A** | J_ESTOP / J_DOOR inter-mateable C189896, labels discriminate by **0.069 mm**; `D_DOOR` (h 0.60, 33% taller) sits 0.353 mm from the E-STOP connector and 6.411 mm from its own diode. | **ACCEPTED — FIX REQUIRED.** Silk-only, respin-only. Extend `fix_silk_placement.py` to enforce label OWNERSHIP, not just void avoidance. |
| **RENDER P0-B** | `P-SILK-FN` matched `^(J|F|TP)[0-9]` -> exactly ONE ref (`F1`) of 35 touchpoints. The only machine gate on connector silk could not fail. | **FIXED 2026-07-28** in `skills/kicad-pcb/scripts/policy_audit.py`, default now `^(J|F|TP)([0-9]\|_)`. Measured: cooksense 1->31, interposer 0->23, pluto-rx2-8way 0->12, pluto-cal-switch 1->8, crow-rc-v2 30->32. Now FAILS on unlabeled test points — a real finding it could never previously report. Known-bad fixture OWED. |
| **LAYOUT P1-b** | `J_ISOLOOP` (the NOT-SELV connector) silk label printed 0.353 mm OUTSIDE its own courtyard and fully inside `J_RH_EXHAUST`'s; 4.900 mm to own pads vs 1.412 mm to the neighbour's — a 3.5x inversion. | **ACCEPTED — FIX REQUIRED.** Same silk pass as P0-A. **INDEPENDENTLY FOUND BY TWO LENSES** with no shared method (render measured 0.314 vs 0.373 mm from the other direction). |

| **PIN P0 (VERIFIED BY THE MAIN LOOP)** | The 12 DIP05 reed relays' footprint has 4 pads on DIP 1/7/8/14, but datasheet p.3 sub-figure **12** shows **EIGHT** leads with **1<->14 one contact node** and **7<->8 the other**, coil on the INNER pins. Netlist confirms: pad1=`5V_KEY_RELAY` and pad4=`U_SEL_BUS` are the SAME internal node; pad2=`COIL_U1_N` and pad3=`KP_U1` likewise. So `5V_KEY_RELAY` is hard-shorted to the select bus, every ULN2803 output is shorted to its keypad line, **the coil has no holes at all**, and the array is non-functional. The 1.5 kVDC coil/contact isolation boundary cited to ADR-0002 does not exist in pinout 12 — the split runs along the long axis, not between rows. | **ACCEPTED — FIX REQUIRED, and it is NOT v1.7-scoped.** The footprint predates v1.7 and ships in **sealed v1.0-v1.6**. Re-author against sub-figure 12 (8 pads), re-derive the isolation geometry, re-run placement/route. `part.yaml`'s prose matches sub-figure **13**, the 4-lead variant — the wrong sub-figure was read. |
| **PIN P0-b** | `U_EXP` pin 1 (GPB0) idles at **5.0 V** into a 3.3 V part (abs-max 3.6 V): `EFUSE_FLT_N` is pulled up to `5V_PROTECTED` through `R_PG` 100k. ~14 uA of continuous injection into 3V3. | **ACCEPTED — FIX REQUIRED.** Divider, or move the pull-up to 3V3. |

## Recorded, not blocking

- **LAYOUT P1-a — the moat's tightest point is confirmed by nothing.** KiCad DRC does not test zone-fill-vs-pad clearance; PROVED by raising the rule to 8/12 mm and observing 514 violations with `(Zone,pad) = 0`. The moat measures exactly **2.0000 mm** on all four layers and passes, but that number rests on a hand-typed keepout. Gate gap -> v1.8.
- **LAYOUT P1-c — the LDO's 45 C/W is not supported by attached copper** (~6 mm2 spreading, 2 tab vias, ~104 K/W). Failure direction SAFE (thermal shutdown collapses 3V3, every pull-down asserts). -> v1.8.
- **TOPO P1-1 — the power tree does not balance**: 3V3 declares 0.3 A then declares children summing to 0.45 A. At the file's own numbers both E-TOPO criteria invert (PD 128%, headroom short 24.5 mV). The E-TOPO PASS this revision obtained is arithmetic that contradicts its own child table.
- **TOPO P1-2 — `vin_min` omits every ohm of PCB copper.** Measured 89.9 mOhm J_PWR->LDO; 45.0 mV at 0.50 A = **82% of the declared 55 mV margin**, 53.8 mV at 70 C. The margin ADR-0021 was made to obtain does not survive the board's own copper. Owed: the bench dropout measurement.
- **TOPO P1-3 — `TEMP_OK`'s default is PERMISSIVE and ADR-0019 does not name it.** All eleven ADR-0019 directions re-derived CORRECT, including the two counter-intuitive ones. But TEMP_OK is a twelfth permission input and an open-drain wired-AND structurally cannot carry a restrictive pull-down.
- **TOPO P1-4** — the opto's published 30 V/50 mA is ~18x the guaranteed LED drive (Ic >= 2.8 mA). Fail-safe direction; a false published rating.
- **PIN — 4 QUESTIONs** open for adjudication (J_MODE harness-end circuit 1, U_ONESHOT, U_LATCHG, U_EXP) plus 3 process findings. No FAIL.
- **P2s**: 11 from topology, 9 from layout, 4 from render. See the individual archives.

## Refutations recorded (canon: record, do not delete)
Topology self-refuted `D_ESD_IN` upstream of F1 (correct practice) and the 7 ms
FLC window (largely). Layout withdrew via-in-pad (SKILL.md records 0.25/0.15 as
proven orderable), withdrew "J_MODE 0.0000 mm pad gap" as **its own bug**
(`GetSize()` is unrotated; true gap 0.80 mm, and the GH->ZH change WIDENED it
from 0.55), and withdrew the D_KSTOP flyback loop. Render refuted BOTH its own
overlay exits with an independent classifier. **All three lenses confirmed the
v1.7 J_MODE GH->ZH change is correct** — it cannot mate with any GH harness.

---

# 2026-07-29 — the three blockers closed, and a fourth that blocks instead

No new lenses were run. This section records the DISPOSITION of the carried
findings, with the measurement that closed each one.

| id | disposition | evidence |
|---|---|---|
| **PIN-P0-1 / TOPO P1-1** — U_EXP.1 readback dead at 0.833 V | **CLOSED** | ADR-0022: `R_PG` pull-up 5V_PROTECTED → 3V3, `R_FLTDIVT`/`R_FLTDIVB`/`EFUSE_FLT_DIV` deleted. `node_level` reports **3.300 V at U_EXP.1** vs V_IH 2.640. E-INV 136/136, 5 new asserts RED-verified |
| **RENDER-P0-1** — J_ISOLOOP no artwork | **CLOSED for the caption, PARTIAL for the legend** | `ISO 30V` at **0.085 mm** from the block body, `NOT SELV` at 7.892 mm, both h0.600/0.150. Pole legend does NOT fit at the terminal and rides the north-stack caption |
| **RENDER P1-1 / P0-A** — six designators at 0.130 mm, label ownership | **CLOSED** | 250 texts re-measured: 0 below the 0.1125 mm tier floor, 0 storing an unachievable stroke, 11/11 safety texts at h0.600/0.150. Ownership leads J_DOOR +3.087, J_ESTOP +0.659, J_MODE +10.685 mm |
| **RENDER P0-B** — P-SILK-FN could not fail | **already FIXED upstream**; the project's own waiver text is now corrected too |
| **TOPO P1-2** — coil pull-in margin | **CLOSED 2026-07-29 (was ESCALATED TO P0)** | ADR-0023: `U_ULNA`/`U_ULNB` ULN2803ADWR (C9683) → **TBD62083AFWG (C165895)**, a pin-identical DMOS array — pin map from the p.2 pin TABLE, land from the p.9 drawing at 300 dpi (TI's DW 11.50×7.50 sits dead centre of Toshiba's 11.35–11.68 × 7.37–7.62 band), COM clamp diode confirmed from the p.2 equivalent-circuit FIGURE because the coils have no external flyback. R_ON is a GUARANTEED EC-table max, 3.25 Ω, identical at all three published current points, so 7 mA × 6.50 Ω (2×, hot bound) = **46 mV** against the Darlington's 670–880 mV. Margin **+0.774 V at +50 °C and +0.424 V at +75 °C**, positive at every corner; ampere-turn cross-check **7.815 mA vs 7.00 mA required at +70 °C, +11.6 %** (was 6.81 mA, −2.7 %). DRC 0/0/0, E-INV 140/140, zero geometric change. The `node_level` assert that pins it measures **0.056 V vs a 0.540 V budget = PASS with the DMOS, 0.895 V = FAIL with the Darlington** — PROVEN, but NOT LANDED: `node_level` joins dossiers by LCSC code and the self-supplied relays carry an MPN, so it needs a 4-line checker patch (verify journal) |
| **PIN Q-1** — pad 1 called GPA0 | **CLOSED** | It is GPB0; GPA0 is pad 21 (`RAIL_EN_A`, an output). Copper was always right |

## Findings this session made, that no lens reported

| # | finding |
|---|---|
| 1 | `electrical_invariants.yaml` declared `supplies: {… N3V3: 3.3}` — the tsx author-prefix form. **No net `N3V3` exists in the netlist**, so the 3V3 rail was invisible to every `node_level` grade. Found by reading the netlist, not by a gate |
| 2 | `node_level` grades a LOGIC LEVEL, not an ABS-MAX. Moving `R_PG` back to 5 V leaves it PASSING at 5.000 V; only the `pin_on_net R_PG.2` assert catches it. Two different claims, and the RED-verification is what exposed the difference |
| 3 | The **6.46 mm** "ISO 30V fits here" re-run that the fix list inherited **does not reproduce** either — that site is blocked by `U_OPTO`'s body and `J_RH_EXHAUST`'s body; the clear band is 0.87 mm and a 0.45 mm text needs 0.92 mm. Third unreproduced "nearest site" number on this corner in three sessions |
| 4 | The real obstruction at the block was never geometry: it was `C_LATCHB`'s and `U_OPTO`'s **designators**, parked first-come-first-served. A 0402's reference does not outrank the only NOT-SELV warning on a 30 V terminal |
| 5 | A per-pole legend at J_ISOLOOP is **geometrically impossible**, stated precisely: the pads sit at the CENTRE of the KF350 body in x, so every square millimetre either side of a pole is under the moulding once the block is fitted |
| 6 | The **1.5 mm ownership margin is not affordable at 0.60 mm text** — it was measured at 0.45 mm and a 0.60 mm box needs 78% more area. `J_ESTOP` has ZERO qualifying slots and landed at a degraded 0.5 mm demand, measured lead +0.659 mm |
| 7 | `route.yaml` had **predicted its own next failure** ("a site legal by 0.00 mm is a site the next reroute takes away") and not reserved against it. The `U_TC.8` stub refused on the first race after the netlist changed |
| 8 | Deterministic plane-bond sites were being chosen by **proximity**; the nearest legal site for `Q_SWDRVB.2` and `U_TC.5` both scored **growth 0.00** — legal by nothing. Sites are now chosen by **max growth**. Slack survives a re-route; distance to the pad centre does not |
| 9 | **`C506653` (MCP23017-E/SS, `U_EXP`) is at ZERO LCSC stock**, where the same gate read 56/56 PASS last session. **CLOSED 2026-07-29** → `C558584` MCP23017T-E/SS, stock 7490: not an alternate but the SAME device, DS20001952C's PRODUCT IDENTIFICATION SYSTEM listing (f) `-E/SS` and (g) `T-E/SS` with the `T` as the tape-and-reel identifier only. jlc_stock_check **PASS 56/56** |
| 10 | **`02_parts/` IS THE MPN AUTHORITY FOR EVERY RELEASE, THE ALREADY-SHIPPED ONES INCLUDED — and this session broke that and got caught by the test suite, not by a review.** Deleting the superseded `ULN2803ADWR` dossier and moving the MCP dossier's `sourcing.lcsc` off `C506653` made the **LIVE sealed release v1.6 ILLEGIBLE**: `t1_fleet_regrade.py` went RED with "LCSC C9683 resolves NO MPN from any authority". The contract's "rejected candidates never get a committed PDF" is about candidates that were NEVER USED; a part that SHIPPED is a different class. Both restored, both recorded in the dossiers |
| 11 | **One field, two incompatible readings.** `bom_legibility_check.py` reads `sourcing.alternates` as `{lcsc:, mpn:}` MAPPINGS and SILENTLY SKIPS bare code strings; `electrical_invariants.py::_load_part_electrical` reads the same field as BARE STRINGS. The 02_parts contract's own example shows the bare form — i.e. the contract documents the form F-LEGIBLE cannot read. `C47023` had been latently unresolvable here for the life of the file |
| 12 | `status_beacon_check.py`'s `_SEALED_RE = re.compile(r"sealed", re.I)` is a SUBSTRING match, so a beacon reading `stage: NOT-SEALED-REVIEW-OWED` / "IS NOT SEALED" was graded as CLAIMING a completed seal and FAILED M-BEACON-REL. A beacon that explicitly disclaims a seal must not be read as claiming one |

## Verdict

**SEAL STILL BLOCKED, BUT NO LONGER ON A DESIGN DEFECT. `07_releases/` is
untouched and v1.0–v1.6 remain DO-NOT-ORDER.** As of 2026-07-29 every carried
P0 is CLOSED: the coil pull-in margin by ADR-0023 (driver technology — option
(b) of the three, with (a) the coil rail refuted arithmetically and (c) a
narrower envelope refused because the 45.7 °C crossover is BELOW the brief's own
≤50 °C normal band), and the `C506653` stock-zero by `C558584`. What remains is
process, not engineering: the fresh four-lens battery, two measured rotation
ledger rows that live outside this project's pathspec, the 4-line `node_level`
join patch, one manifest `not_assembled:` line, and the seal.

**A fresh four-lens battery is OWED, not skipped.** It was not run because a
confirmed P0 already blocks and closing it will change the power tree or the
coil driver — a material change that needs its own battery. Running four lenses
against a board that must change again would spend it twice.

---

# 2026-07-29 (third) — THE FRESH FOUR-LENS BATTERY, RUN AT LAST, AND IT BLOCKS

The battery deferred twice — correctly, both times, because a confirmed P0 was
open and closing it changed the driver — was run here against the pre-seal
staging archive. Four zero-context lenses, launched concurrently, input CURATED
(`journal/`, `learnings/`, `STATUS*.md`, `CHANGELOG.md`, `08_reviews/` and
`07_releases/` withheld from all four; no `git log`).

| lens | verdict |
|---|---|
| render / silk (FRESH LENS) | **DO-NOT-ORDER** — 2 P0 |
| topology / protection / ratings | **DO-NOT-ORDER** — 0 P0, 7 P1, 13 P2 |
| layout / thermal / power integrity | **DO-NOT-ORDER** — 7 P1, one of them the order-blocker |
| pin review (FRESH LENS) | **FAIL** — 0 pin-map FAILs, 2 evidence-grade FAILs; connector group OWED and requested |

**v1.7 IS NOT SEALED. `07_releases/` IS UNTOUCHED. v1.0-v1.6 REMAIN
DO-NOT-ORDER.** Nothing was staged into `07_releases/`; the archive sat in
`06_build/staging/cooksense-v1.7/` throughout, where it could not make itself
the live release.

## The two order-blockers

| id | finding | disposition |
|---|---|---|
| **RENDER P0 — LABEL OWNERSHIP ON CROSS-MATEABLE SAFETY CONNECTORS. This is the SAME defect v1.7's battery raised as RENDER P0-A and marked FIX REQUIRED; the fix landed and DOES NOT REACH THESE REFS.** Measured by the main loop on the current board, box EDGE-to-EDGE, independently of the lens: the string **`J_ISOLOOP` is printed 0.161 mm from `J_RH_EXHAUST`** and 2.739 mm from J_ISOLOOP — the 30 V NOT-SELV terminal's own designator labels a humidity-sensor header. **`J_ESTOP`'s designator is 0.161 mm from BOTH `J_ESTOP` and `J_DOOR`**, an exact tie, and those two are the SAME part (`JST_GH_SM05B-GHS-TB_1x05`, C189896) — physically cross-mateable, two of the four such headers being safety inputs. `J_DOOR`'s own designator is 5.66 mm from J_DOOR and 4.23 mm from `D_DOOR`. The generator states it itself: the rebuild log prints `WARN silk ownership ... no owned slot in the 4x84 search` for J_DOOR, J_ESTOP, J_ISOLOOP, J_MODE and 52 others and then places them anyway — **179/241 owned, 56 degraded, 6 unplaced.** | **ACCEPTED — BLOCKS. NOT FIXED HERE, AND DELIBERATELY NOT ATTEMPTED.** The cause is PLACEMENT DENSITY: J_ISOLOOP + J_DOOR + J_RH_EXHAUST + U_OPTO + R_OPTOLED inside ~15 mm of the SE corner. No silk-only pass can create space that does not exist — this one already evicts three foreign labels to fit `ISO 30V` at 0.561 mm. A floorplan change re-races the router, which would spend this battery a third time, so it belongs to the next revision as one deliberate pass. **Consider that the honest fix is partly a PART change:** four identical 5-pin GH headers on one board, two of them safety inputs, is the defect underneath the silk. |
| **LAYOUT P1-PI-2 — NO CAPACITOR ANYWHERE ON THE eFUSE INPUT SIDE, and the layout rule written to protect it names a net that does not exist.** `5V_IN` / `5V_FUSED` / `5V_RPP` carry **zero** capacitors; `C_IN1`/`C_IN2` are on the eFuse OUTPUT. The `keep_short` budget meant to hold the input cap local is addressed to net **`5V_SELV`**, which is not a net on this board. | **ACCEPTED — BLOCKS.** The lens's own reasoning is adopted verbatim: a missing input capacitor on the protection stage of a mains-adjacent board cannot be added to a fabricated panel. Everything else it found is a document fix, a fabricator question, or characterisable at bring-up; this one is copper. |

## Confirmed by the main loop, generalising a lens finding

**TEN net names referenced by this board's rule files and part dossiers DO NOT
EXIST IN THE NETLIST** — measured by walking every `net:` / `nets:` /
`vdd_net:` key in `03_src/cooksense/rules/*.yaml` + `02_parts/*/part.yaml`
against the 412 nets in `06_build/netlists/cooksense.net`: 10 of 123 referenced
names (8%) are ghosts. `5V_SELV` (TPS259573DSGR) is the one that hid the missing
input capacitor; the others are `+5V`, `3V3_DIGITAL`, `HS_GATE`, `LED_DRIVE`,
`N3V3`, `OPTO_LED`, `RCEXT`, `T_MINUS`, `T_PLUS`. Some are generic
datasheet-side placeholder names rather than board claims — **and that is the
point: nothing distinguishes a placeholder from a ghost, so a dead budget is
indistinguishable from a satisfied one.** Third instance of this class in two
sessions (`supplies: {N3V3: 3.3}`, `GND_ISO` on the silk and in the padmap, now
these ten). Proposed as a gate upstream.

## Closed by this pass — do not re-open

| id | disposition | evidence |
|---|---|---|
| **The 0.600 mm comb slots — FOURTH sighting, and it was a real P0** | **CLOSED, FIXED** | JLCPCB's own capability page: **"Min. Non-Plated Slots: 1.0mm"**, read twice and corroborated independently. Twelve unplated internal slots were 40% under it. Widened to **1.000 mm** (y25.8-26.8 / y49.1-50.1) after measuring it free: nearest copper on any of four layers with pours filled **2.8500 mm** north (2.5500 at r11r12), **2.7300 mm** south, against the 0.200 mm JLC asks. Verified in the board's Edge_Cuts horizontals. DRC 0/0/0. Cost stated: refdes-on-silk 235/241 with 6 waived to F.Fab (was 5) |
| **The ADR-0023 coil-margin assert — proven but ungated** | **CLOSED, LANDED** | Eleven `node_level` asserts, one per DMOS-driven reed. **E-INV 140/140 -> 151/151.** RED-verified in place at BOTH Darlington corners (95.7 ohm -> 0.714 V, 125.7 ohm -> 0.895 V, 11 FAILs each against the 0.540 V pull-in budget, exit 1), restored byte-identical. Landing it found that only pad "18" carried the hot-corner 6.50 ohm, so ten of eleven asserts would have graded at the 25 C 3.25 ohm default — all eleven driven channels now declare it (M-WIDTH). **The relay count is TWELVE, not the thirteen three files say**; eleven on the arrays, K_STOP excluded BY NAME |
| **`J_PI` (C35165) / `J_LOADCELL` (C157991) — coded but on no CPL row** | **CLOSED — the first branch, with evidence already in place** | `assembly.yaml` declares both `process_incompatible` with a MEASURED justification (5 and 40 plated DRILLED pads, F.Paste on none, against a `service=standard sides=[top]` reflow-only order). They are correctly OFF the CPL (0 rows) and stay in the BOM as self-supplied lines so the order sheet still says what to buy. The MANIFEST `not_assembled:` line is computed — 16 refs — and closes A-POP's one FAIL |
| **`GND_ISO`, in two places** | **CLOSED, both corrected** | The SILK printed "GND_ISO ONLY" and `parity_padmap.txt` claimed J_KEY_MATRIX's MP tabs are "reflowed to GND_ISO". `grep -c GND_ISO` = **0**. The board was right and both documents were wrong: those tabs are netless BY DESIGN because J_KEY_MATRIX is the only connector on the isolated side of the reed barrier. Measured: **19.407 mm** to the nearest SELV copper against >= 6.000 mm. Caption now reads NO GND BOND |
| **The `1C2L3L4E` pole legend** | **CLOSED, FIXED AT THE ROOT** | It sat **0.161 mm from J_RH_EXHAUST** against 5.512 mm from its attributed owner, because `fix_silk_placement.py` bounded a caption's distance to its OWN part and tested nothing about the others. It now refuses an unowned site and reports DOES NOT FIT (no owned site exists at that corner). Found by the new P-SILK-OWN row and by the render lens, two methods, no shared code |
| **A-RENDER, never run on this board before** | **CLOSED — PASS, and its two FAILs were its input's resolution** | At jlc_twin's hard-coded 1600x1000 (**8.34 px/mm** on a 188 mm board) it FAILED on `U_LDO` (centre delta 1.248 mm) and `Q_SWDRVRHA` (13 body px). Re-rendered at **15.3961 px/mm**: exit 0, 53 measured / 210, **zero** resolvable-but-unmeasured, U_LDO **0.111 mm**, Q_SWDRVRHA **0.086 mm** (872 px). A gate whose verdict flips with the resolution of its input must say so — reported upstream |
| **`kicad_sch_parity` FAIL 1/169** | **DISPOSITIONED, not waived** | The single `('J_KEY_MATRIX','MP')` no-connect, and the IDENTICAL finding appears against **sealed v1.6** (1/161) — inherited, not new. It is a checker gap: a mechanical pad unbonded BY DESIGN has no way to say so |
| **`W-FOREIGN` on this board's own S-OCCL waiver** | **CLOSED** | `derived_from: [crow-recorder-central-v2, crow-mic-pod-v2]` DECLARED, with the note that only the waiver CLASS is inherited and the 77-site measurement is native. Scoped verdict **PASS, 12/12 independently reasoned** |
| **The 2N7002 datasheet** | **DEVIATION DECLARED, not closed** | LCSC serves HTML, not the PDF (two URL forms tried, both 200-with-HTML). K_STOP's margin re-derived from the rail rather than inherited: 5V_STOP `vout_min` **4.754 V**, so +70 C margin is **+0.454 V** at the estimated 0.10 V V_DS and still **+0.054 V** at 0.50 V. Not load-bearing; K_STOP is excluded BY NAME from the coil-assert family |
| **The west comb slot's web** | **CARRIED as a DFM query, with the reason it is not a respin** | 1.000 mm web to the board edge while the same file skips the east pocket for "<3mm ... too fragile" — a self-contradiction, INDEPENDENTLY found by the layout lens (P1-MECH-2). JLC publishes no remaining-wall minimum; their own Q&A asking it is UNANSWERED. Extending the slot through the edge would change the mechanical outline of a board whose enclosure interface is specified |

## Carried to the next revision, each with its number

- **The LDO thermal story, now measured twice and worse than carried.** Carried
  as "13.96 mm2 against ~645 mm2"; the layout lens measures **~3.1 mm2** of
  top-layer 3V3 at the tab, 2x0.15 mm vias, 44.8 K/W tab-to-plane, theta_JA ~75
  against the cited 55-65, **Tj 110-122 C at Ta 70 C** — and **no operating
  ambient is declared anywhere on this board**, so no junction temperature can
  be closed at all. That last item is owed regardless of everything else.
- **The 3V3 rail's own arithmetic, re-derived by the main loop from the file.**
  `3V3` declares `iout_max_A: 0.3` and annotates it "logic:
  595/238/HC14/1G-family/MCP23017/watchdog/one-shot" — its DECLARED CHILDREN
  (`3V3_ANALOG` 0.05 + four `3V3_SW_*` at 0.10) draw a further **0.45 A from
  it**. At the true 0.75 A: **PD = (5.250-3.201) x 0.75 = 1.537 W against a
  1.200 W budget = 128%**, and dropout headroom **fails by 24 mV**. E-TOPO
  reports PASS on the understated denominator, so this is a GATE defect as well
  as a rail defect. Third battery in a row to report it.
- `D_ESD_IN` (PESD5V0S1BA, V_BR 5.5 V min) is upstream of F1 and becomes the
  ONLY clamp in circuit once the eFuse opens: 630 mW at 9 V, 1.56 W at 12 V.
- The contactor opto delivers **~2.4 mA** against a declared "<=30 V / 50 mA",
  and the 30 V inductive loop has no snubber against V_CEO 35 V.
- The brief's **Ioff buffers and 22-100 ohm series resistors DO NOT EXIST** on
  the BOM, while `ARCHITECTURE.md` states they do.
- The TPS3823 watchdog is **0.9 / 1.6 / 2.5 s fixed** against a commissioned
  300-500 ms, with no ADR waiving it.
- **Door EOL supervision is unimplementable as built**: `J_DOOR` pins 2 and 4
  are ONE net and the receiver is a single HC14 threshold, not a window.
- External I2C runs carry no ESD and no series damping; pull-ups are fixed 2.2 k.
- **P1-MECH-1**: the declared max conductive fastener OD (6.000 mm) lands on
  keypad copper at H1/H2 — copper at 2.950 mm radius, overlap 0.050 mm, max safe
  OD **5.900 mm**; it would bridge `KP_U2` to `KP_U6`, two matrix rows.
- `power_tree.yaml`'s series budget contains **no PCB copper at all**: 96.939
  mOhm measured against a 190.5 mOhm device-only budget, headroom **+18.7 mV not
  the declared +55 mV**, and the file's own 0.60 A stress case inverts to
  **-4.3 mV FAIL**.
- The LDO compensation cap is **9.200 mm** away against a 5.0 mm budget, reached
  through three 0.15 mm vias and the plane; `EF_OVLO` is **8.473 mm** against
  5.0 mm; and **no gate measures `keep_short` at all** — 7 of 11 budgets
  violated.
- All 1052 vias are 0.25/0.15 with a 0.050 mm ring while the netclasses declare
  0.60/0.30 — and the DRC floors were set to the values used.
- **Two evidence-grade FAILs from the pin lens.** 26 of 54 dossiers point at NO
  committed datasheet PDF, and `SN74LVC1G00DCKR`'s `doc_id` (SCES214)
  contradicts the real document (SCES212AB) which the same file's
  `layout.source` names correctly. And **`pin_audit.py` silently emits
  content-free dossiers for 16 of 54 parts, including ALL TWELVE RELAYS** — the
  one land pattern whose predecessor was drawn against the wrong datasheet
  sub-figure is exactly the one the dossier generator blanks, so a reviewer
  working only from the dossiers, as the protocol instructs, could not have
  performed the check at all. A CHECKER defect; reported upstream.
- **Silk legibility, with the emitter named.** 249 texts: 173 at h 0.600 /
  stroke 0.150 (all 11 safety texts among them) and 71 at h 0.450 / stroke
  0.1125 — the REFDES de-collision emitter's floor at that height. Against
  JLC's published `Minimum Line Width >=0.15mm` and `Minimum text height 40 mil
  (1.0mm)` this is the order-day DFM judgement canon G-SELFCON already records
  (61 of pluto-rx2-8way's 64 refdes sit below the published stroke), NOT a new
  P0: the tier's 0.45 mm height is annotated *proven by ordering*, and taller
  glyphs strand more refdes off silk entirely. Recorded with both numbers.
- **4 silk-to-pad gaps below JLC's published 0.150 mm**, three of them 0.0000:
  two PINNED captions print over `Q_SWDRVA` pads 1/2/3 and over `TP_RKEY.1`.
  Cheap to fix (a coordinate nudge) and deliberately deferred into the same pass
  as the P0, because a placement change moves silk again.

## Refutations recorded (canon: record, do not delete)

The layout lens validated its own resistance solver against a hand-computable
net (21.549 vs 21.741 mOhm, the difference being a parallel stub), reproduced
DRC independently at 0/0/0, reproduced ADR-0015's H4 creepage at **4.029 mm vs
its 4.0286 mm by a different construction**, and KILLED ITS OWN BEST P0
CANDIDATE: `HS_GATE_COIL` crosstalk at 10.169 mm delivers ~3 pC where V_GS(th)
needs 250 pC — two orders short. It could not break the isolation work: keypad
comb **6.2344 mm** on its worst layer pours-filled, the 30 V moat **2.0005 mm**
on all four layers, the opto barrier **7.530 mm** pad-to-pad, In1.Cu ground one
**8476.6 mm2** island. Topology refuted 16 of its own hypotheses including the
P-FET orientation, the crowbar's position, the coil freewheel path, the
open-thermistor detect (which WORKS), the `J_MODE` 3-4 short, and **E-OFF, which
passes with its off-control traced as a real series element** — and found no
permissive default anywhere in the seven-term chain, the fault latch, the re-arm
or the STOP path. Render refuted five of its own, including the claim that the
1.00 mm comb web breaks the ">=6mm creepage" silk (min straight-line F.Cu gap
straddling the comb is **6.53 mm**), and confirmed **all nine diodes and CE1
polarity-correct two independent ways**. The pin lens found **zero pin-map
FAILs** across 41 graded parts, re-derived the relay land from the datasheet
figure without reference to the footprint (**PASS x12**), and confirmed
`01_docs/pin_map.md` against all 40 Pi header pins with zero mismatches.

## ADDENDUM — the pin lens's connector group, requested and delivered, and it makes the connector corner a THIRD blocker

The pin lens's first report left `Connectors | 12 x J_*` marked *pending*. It was
asked to finish, told only that four of them are the same part and that the
question is what the board DOES on a mis-plug — not what to conclude. It came
back with the mechanism, and the main loop then re-derived it from the netlist.

| id | finding | disposition |
|---|---|---|
| **PIN C1 — CROSS-PLUGGING A SENSOR POD INTO THE DOOR INTERLOCK CAN ASSERT `DOOR_OK`.** `J_DOOR` pin 4 is `DOOR_RAW`; on the identical `J_ESTOP` pin 4 is GND, and on the identical `J_RH_*` pods pin 4 is `SCL_*`. So a pod harness in `J_DOOR` lands a PULLED-UP I2C clock on `DOOR_RAW`, which is held only by `R_DOORPD` 10k. The lens computes 1.650 V from a 10k pod pull-up against SCLS085L's conservative 4.5 V row, V_T+ MIN **1.55 V**. **RE-DERIVED BY THE MAIN LOOP, AND IT IS WORSE THAN THE LENS SAID, TWICE OVER:** `U_SCHM` pin 14 is on **3V3**, not 5 V, so the applicable V_T+ MIN is BELOW the 4.5 V row's 1.55 V (the 2.0 V row is ~0.7 V), i.e. the injected level clears the threshold by MORE; and this board's own I2C pull-ups are **2.2k**, which on the same divider gives **3.3 x 10/(10+2.2) = 2.70 V**, not 1.650 V. A conforming HC14 reads the door **CLOSED with no door attached**. `J_DOOR` pins **2 and 4 are ONE net**, which is separately why the topology lens found EOL supervision unimplementable (T-06) — the same wiring, found from two directions. | **ACCEPTED — BLOCKS, and it is the one with a KNOWN fix shape.** ADR-0018 closed this exact class on `COIL_EN_IN` with a 680 ohm series element and it was NOT carried across to the other externally-cabled safety inputs. That makes the next revision's connector work electrical as well as geometric, and it is why "move the labels apart" was never going to be the whole answer. |
| **PIN C2** — a `J_DOOR`<->`J_ESTOP` swap (identical housings, courtyards **0.090 mm** apart) leaves `ESTOP_OK` HIGH: the contactor still opens, but nothing latches a fault and the coil rail stays up | ACCEPTED — same pass |
| **PIN C5 / C6** — `J_PWR`'s pin-1-versus-key is confirmed by NO artifact in this tree; `J_ISOLOOP`'s NOT-SELV land is derived from the project's OWN 2P footprint (canon M1: checker and checked share a method) | ACCEPTED — C5 to the bring-up ritual, C6 needs an outside authority |
| **PIN C9 / §6** — **`J_TC`, the thermocouple input, had NO dossier and was assigned to no reviewer**: it is dropped by `pin_audit.py`'s `>3 pads` filter. Symmetric land, the silk `+` sits under the housing once fitted, and a reversed thermocouple raises no fault flag | ACCEPTED — and it is the 17th ref that gate silently omits |
| **PIN Q1** — all eight `U_EXP` status inputs are on **port B** and `EXP_INTB` (pin 19) is the board's ONLY named single-node net, while the Pi watches **INTA** (pin 20). Dead alert path unless `IOCON.MIRROR = 1`, documented nowhere | ACCEPTED — a firmware-visible contract that must be written down or wired |
| **PIN F1** — `SN74LVC1G00DCKR` has no committed PDF and its `doc_id` `SCES214` contradicts the real `SCES212AB`, which the same file's `layout.source` names correctly. Four safety-chain gates rested on "the 1G-family convention" | ACCEPTED. The lens fetched SCES212AB, read the §6 **DCK** figure (deliberately avoiding the DPW figure on the same page, which has A and B swapped) and the map is CORRECT — copper right, provenance not what the tree claims |

**AND THE THING THIS BOARD WAS MOST AFRAID OF DID NOT HAPPEN.** The relay land is
RIGHT, proved the hard way and independently of the footprint: sub-figure 13 read
off DS p.3 at 600 dpi, its grid measured (contact = leads 14/8 at the row
extremes, coil = leads 2/6 inset one pitch, rows 7.62 mm apart), then the
FIGURE's lead coordinates transformed into the footprint frame — **pure +90
degree rotation, NO reflection, every residual <= 0.05 mm**, pin-1 silk dot on
the correct corner. Coil and contact net domains **provably disjoint across all
198 nets**, the contact domain touching only `J_KEY_MATRIX`, two resistors and
three test points — no rail, no ground, no logic. Driver channel mapping 11/11.
The decoders are the active-HIGH '238, not the '138 that would have fired eleven
coils at once. 21 distinct MPNs opened at figure resolution covering 50 of 54
refs; **0 mirrored footprints, 0 pad-to-net contradictions against any datasheet
that could be read.**

---

# 2026-07-30 SEAL PASS — the ninth, and the first with a vocabulary for the answer

The eight declines before this one were not disagreements about the board. Every
one of them read DRC 0/0/0 and `policy_audit` FAIL=0 and then declined, because
the review model had ONE `verdict:` field and that field meant ORDERABLE. Commit
`217ea175` split it into `design_verdict` (read by the SEAL gate) and
`order_verdict` (read by ORDER_README), so a lens can now say *this board is
right and you cannot buy it today* without either half contaminating the other.

## Re-gates run for this seal

| id | review file | finding (one line) | severity | verification | disposition |
|---|---|---|---|---|---|
| RG2-TOPO | `2026-07-30_v1.7_redteam_topology_REGATE2.md` | full topology/protection/ratings re-gate, fresh context, on the two-key vocabulary; sourcing state established by the lens's OWN live catalog read | — | see the file | `design_verdict: SOUND` / `order_verdict: BLOCKED-SOURCING` |
| RG2-LAYOUT | `2026-07-30_v1.7_redteam_layout_REGATE2.md` | full layout/thermal/power-integrity re-gate, fresh context, on the two-key vocabulary | — | see the file | `design_verdict: DEFECTIVE` / `order_verdict: BLOCKED-SOURCING` |

**WHY THE LAYOUT LENS WAS RE-GATED TOO, WHEN ONLY TOPOLOGY HAD DECLINED.** Its
2026-07-30 review carries the legacy single `verdict: ORDER`, which M-REV
retrofits to `order_verdict: ORDER` — and M-REV cross-checks `order_verdict`
against the release's own shipped stock evidence **in both directions**. On a
release measured `SOURCING: BLOCKED-1`, `ORDER` fires
`REVIEW-ORDER-CONTRADICTS-EVIDENCE`: *a lens may not certify an order the archive
it graded cannot place.* The retrofit is deliberately conservative and never
converts a refusal into an acceptance, but it cannot invent a `BLOCKED-SOURCING`
that the reviewer did not write. So the honest move was to re-ask the lens under
the vocabulary that can express the answer, not to reinterpret its old field.

## The prior re-gate's own findings — all five CONFIRMED and closed before this seal

The 2026-07-30 topology re-gate (`..._REGATE.md`) returned `DO-NOT-ORDER` under
the old vocabulary, and it EARNED that verdict on five specific things this
board's paperwork had wrong. All five are fixed in the sealed archive:

| id | finding | verification | disposition |
|---|---|---|---|
| **RG-P1-1** | §5-0 told a buyer to "edit one cell of `fab/bom.csv`" — **a file JLC never receives.** The assembly step takes `bom_jlc.csv`/`cpl_jlc.csv`, and the CPL `Val` column carries the LCSC code because `fp.GetValue()` on these two footprints IS the string `C265111`. Following it exactly would have ordered the unbuyable part. | confirmed — 6 cells across 4 files, census in §5-0; `fab/bom.csv` and `fab/bom_jlc.csv` are byte-identical today, so nothing would have warned the buyer they had edited the wrong one | **FIXED.** §5-0's remedy is now "change `03_tscircuit/src/cooksense.tsx` lines 1216/1218 and REGENERATE (canon M3)", with the hand-edit path kept only as a labelled fallback that names all six cells. RE-VERIFIED at seal time: those two lines do carry `supplierPartNumbers={{ jlcpcb: ["C265111"] }}`, and the archived `source/cooksense.tsx` is md5-identical to the live `03_tscircuit/src/cooksense.tsx`. |
| **RG-P2-1** | "zero bytes of the fab set" was false | confirmed | **FIXED** — the surviving claim is "zero bytes of the gerbers, drill and CPL GEOMETRY", and the 13 zip members were re-verified byte-identical to the loose `fab/` copies at seal time |
| **RG-P2-2** | the land-pattern fit table omitted tab pad SIZE | confirmed — board `1.000 x 2.700`, genuine `1.210 x 2.700`, clone `1.000 x 2.500` | **FIXED and CARRIED FORWARD AS AN OPEN GAP.** The table is in §5-0, in `A-STOCK_waiver.md` §3, in ORDER_README §13 gap 0a and in `MANIFEST.txt`. The board's retention tab matches the CLONE, not the part the BOM names, on the exact axis §5-0 declares unverified. **This is UNRESOLVED and is sealed as unresolved** — not closed. |
| **RG-P2-3** | §5-0 stated a safety consequence BACKWARDS: a dropped pod does not remove `TEMP_OK`, it ASSERTS it | confirmed — margin 0.07022 of rail = 231.7 mV at 3.300 V, rail-independent | **FIXED** — the corrected box says the cost is nuisance latched stops, not a defeated interlock, and shows the arithmetic |
| **RG-P2-4** | an H2 "ORDERABLE" heading 693 lines above the section saying it is not | confirmed | **FIXED** — the heading now reads "DESIGN-CLEAN" and states that it is about the design, not about whether you can buy it |

## Findings raised by the SEAL PASS itself

| id | finding | verification | disposition |
|---|---|---|---|
| **SEAL-1** | the staged archive **did not stand alone**: `source/fp-lib-table` pointed OUTSIDE it (`${KIPRJMOD}/../03_src/lib/…`) and a standalone DRC returned **14 `lib_footprint_issues`** | confirmed, then re-confirmed by me: `source/` copied to a directory outside the repository now returns **0/0/0, raw exit 0**, resolving `${KIPRJMOD}/cooksense.pretty` from the five vendored `.kicad_mod` files in the archive | **FIXED** in the sealed archive. A fleet sweep finds the same defect in **5 of 33** sealed archives — immutable, RECORDED, not repaired. Nothing in the repo gates this; owed skill patch P9. |
| **SEAL-2** | `E-NETREF` exit 1 — 21 ghost net references | confirmed by me; **all 21 are kind K7** (`layout.keep_short[].net`), every other reference kind is 0 ghost including 140/140 invariant nets and 40/40 netclass memberships | **RECORDED, not fixed.** No ghost reaches copper, silk, netlist or BOM; the same sites are inside `policy_audit`'s evidenced `P-ADJ-UNREACHED` waiver (23/38 — a superset, since an absent net has 0 pads). Pre-existing `02_parts/` debt; fixing it means 21 dossier edits, i.e. moving the part-selection inputs of a board whose fab set is frozen. Next rev. |
| **SEAL-3** | **A-RENDER's verdict is a function of its input's RESOLUTION.** Same board, three renders: FAIL on `U_LDO` + `Q_SWDRVRHA` at 5.1356 px/mm; FAIL on a **different** ref (`J_KEY_MATRIX`) at 9.7448 px/mm; PASS at 15.3907 px/mm | confirmed by me from a fresh render, independently reproducing the 2026-07-28 disposition (15.3961 px/mm). **The failing REF changes with resolution**, so the low-res FAIL was never about U_LDO — it was about pixels | **RECORDED + reported upstream.** The high-resolution report ships as `twin_overlay.md` **and the low-resolution one ships beside it** as `twin_overlay_lowres.md`: deleting the run that failed would be choosing the resolution that gives the answer you want. |
| **SEAL-4** | three gates were being invoked with wrong/default paths on this two-board project, and **a gate pointed at the wrong file does not fail safe — it fails LOUDLY AND WRONGLY** | measured: `assembly_coverage` with the default `03_src/rules/assembly.yaml` reports **37 UNDECLARED-UNPOPULATED refs** that are an artifact of the invocation; with `--assembly 03_src/cooksense/rules/assembly.yaml` the only finding is the missing MANIFEST. `waiver_provenance` given a project path reports `0/0 graded` and FAILs the zero denominator; given the `projects` root + `--project`, PASS 12/72. `count_parity` **refuses** without `--board` rather than guessing | **RECORDED.** `count_parity`'s refusal is the correct shape and the other two should copy it. A number copied out of a mis-invoked run into a report is indistinguishable from a real one. |
| **SEAL-5** | `git_dirty` is TRUE at seal time from **`skills/` paths that are another agent's in-flight work** | measured by `release_git_dirty.py smc0985-cooksense` | **ESCALATED, NOT WORKED AROUND.** Board agents are bound out of `skills/` and committing another agent's half-landed gate under this seal is worse than editing it. See the seal record for the exact paths. |

## THE SEAL WAS DECLINED — the two P0s that stopped it

`design_verdict: DEFECTIVE` from `2026-07-30_v1.7_redteam_layout_REGATE2.md`.
Per the 08_reviews contract and SKILL.md stage 7, a P0 blocks the release and a
DEFECTIVE design verdict blocks the seal until re-gated or superseded. **The
candidate was moved back to `06_build/staging/cooksense-v1.7/`, `07_releases/`
was left untouched, and the `SUPERSEDED.md` drafted for v1.6 was REMOVED,
because nothing superseded it.**

| id | review file | finding (one line) | severity | verification | disposition |
|---|---|---|---|---|---|
| **RG2-L-P0-1** | `..._redteam_layout_REGATE2.md` | `power_tree.yaml` grades the AMS1117 at `iout_max_A: 0.3` while the same file declares four 0.1 A switched sensor rails downstream of it, under a `linear_rails:` key it labels "Documentation-only (ignored by power_topology.py)". Declared LDO load is 0.70 A; at the file's own constants PD = 1.434 W = **120 % of the 1200 mW ceiling** (graded 51 %) and dropout headroom = **−15 mV** (graded +55 mV). Even at a realistic 0.36 A, PD is 20 % above the reported 0.615 W inside a 55 mV margin. | **P0** | **confirmed — RE-MEASURED BY THE SEALING AGENT with `pcbnew` on `source/cooksense.kicad_pcb`, independently of the lens and of the yaml: `Q_SWA`/`Q_SWB`/`Q_SWRHA`/`Q_SWRHE` pad 2 = `3V3` on all four, drains = `J_THERM_A.1`/`J_THERM_B.1`/`J_RH_AMBIENT.1`/`J_RH_EXHAUST.1`** | **BLOCKS THE SEAL — OPEN.** Fix is NOT layout: state the LDO's real total load with a cited current per sensor rail, re-run E-TOPO, and see whether it still passes. It may. It has not been asked. |
| **RG2-L-P0-2** | `..._redteam_layout_REGATE2.md` | `pdiss_max_mw: 1200` is a 25 °C figure (θ_JA implied 83.3 °C/W) applied with no ambient term, on a board `BRIEF.md` line 117 places at `enclosure <=50/55/65/75`. Re-derived ceilings 0.900 / 0.840 / 0.720 / **0.600 W** — the release's own 615 mW is OVER at the hard limit, the realistic 738 mW is over at the stop threshold. The file's θ_JA justification ("the tab is flooded with 3V3 copper → 55–65 °C/W") describes a different mounting. | **P0** | **confirmed — RE-MEASURED BY THE SEALING AGENT: every zone on the board enumerated, and the ONLY zone on net `3V3` anywhere is on `In2.Cu`. There is NO F.Cu `3V3` zone. The citation's mechanism is REFUTED.** | **BLOCKS THE SEAL — OPEN.** Add an ambient term and a `theta_ja` to the AMS1117 dossier. Retired by one bench measurement at bring-up: load `3V3` to its real total, measure the tab against a known ambient. The same session closes the 0.3 A dropout figure the file already owes. |
| RG2-L-P1-1 | `..._redteam_layout_REGATE2.md` | the 3.000 mm fastener-disc creepage model was derived at H4 and applied nowhere else. Applied everywhere: **H1 → `KP_D1` at 2.9500 mm = −0.0500 mm**; H4 → `5V_STOP` track at 2.8500 mm. A ≥6.5 mm OD washer at H1 bridges a U-select and a D-select membrane line = a permanently pressed key, downstream of every hardware gate. | P1 | confirmed by the lens | **DEFERRED to v1.8 + ORDER_README.** Not re-measured by me. |
| RG2-L-P1-2 | `..._redteam_layout_REGATE2.md` | `grep -c stackup` = 0 on both `.kicad_pcb` and `.kicad_pro`, and no gerber job file — every ampacity floor and both creepage rules are unverifiable at the fab. `PWR_IN` 0.5 mm gives ≈2.0 A at 1 oz but ≈1.2 A at 0.5 oz. | P1 | confirmed by the lens | **DEFERRED to v1.8.** Interacts with the A-AMP `PWR_IN` finding `rules_audit` already reports. |
| RG2-T-P1-A | `..._redteam_topology_REGATE2.md` | the PRESS one-shot's 500 ms HARD bound (BRIEF §4) is published in four documents from a stack using `C+10%`, the 25 °C PART tolerance. `C_OS` is X5R: ±15 % over −55…+85 °C, multiplicative and omitted. `C_max` = 1.265 µF ⇒ **501.7 ms**, and with the datasheet's own K spread **510.9–524.5 ms**. Claimed headroom 64 ms; the omitted term is ±65 ms. | P1 | confirmed by recomputation | **DEFERRED to v1.8 + ORDER_README §14.** Remedy: C0G/NP0 timing cap, or `R_OS` → ~430 kΩ. |
| RG2-T-P1-B | `..._redteam_topology_REGATE2.md` | the LDO dropout margin that unblocked E-TOPO goes NEGATIVE once board copper and a cited connector resistance are counted: +55 mV declared → +15.4 mV → +5.4 mV → **−2.5 mV at 70 °C** → −5.5 mV on the eFuse's wide-temperature RON. | P1 | confirmed, two independent methods agree (+15.4 / +16.3 mV) | **DEFERRED + PROMOTES ORDER_README §0 step 2 from encouraged to MANDATORY.** Note this is the SAME rail as P0-1 from the other lens, reached independently — which is why P0-1 is not absorbable as paperwork. |
| RG2-T-P1-C | `..._redteam_topology_REGATE2.md` | **E-MARGIN cannot fail on this board**: `policy_audit` prints N-A because no rail declares `load_uv_threshold`, while the board has at least six fixed-brownout loads. And the rail it would have graded tightest declares `vin_min 3.201 / vout_min 3.2` at 0.1 A = a 10 mΩ switch; the `AO3401A` is 60 mΩ MAX at V_GS −4.5 V and these four run at **V_GS = −3.3 V**, below any specified point. | P1 | confirmed | **DEFERRED to v1.8.** This is the `jlc_twin`-exit-0 shape in the power gate: a green-looking N-A that never had the chance to be red. |
| RG2-T-P2-k | `..._redteam_topology_REGATE2.md` | `fab/bom.csv` row 55 names `SN74HC238DR` (TI) beside `C5620`, and `C5620` is `74HC238D,653` (Nexperia). JLC matches on the CODE. | P2 | confirmed live | **RECORDED + ORDER_README §14.** Pin- and function-compatible, so paperwork rather than electrical — but `02_parts/SN74HC238DR/part.yaml` is the TI dossier and it is what every V_OH/V_IH argument about the decoder reads from. |

Remaining P2s (a–j, l from topology; 1–5 from layout) are recorded verbatim in
the two review files, which ship in the candidate's `verification/`.

---

## 2026-07-30 — REVIEW ARCHIVE RESCUE + CONTRACT-NAME PROVENANCE (ADR-0028 pass)

**FIVE reviews existed only under `06_build/` — the folder this repo declares
THROWAWAY — or only in a session scratchpad.** None was byte-identical to
anything in this folder (checked by md5 against every `08_reviews/*.md`). They
are now archived VERBATIM here; the md5 of each archived copy equals the md5 of
its source, so "verbatim" is a measurement and not a claim.

| archived as | md5 | design_verdict | where it was found |
|---|---|---|---|
| `..._redteam_topology_REGATE2b.md` | `936dcec0…` | **DEFECTIVE** | a session scratchpad ONLY. It had been written to the contract name `redteam_topology.md` and was then DISPLACED by a later review. One more scratchpad clean and the round-2 DEFECTIVE topology verdict would not have existed anywhere. |
| `..._redteam_topology_REGATE3.md` | `ed78477e…` | **DEFECTIVE** | staging `verification/`, dated name |
| `..._redteam_topology_REGATE3b.md` | `af10f549…` | SOUND | staging `verification/`, occupying the contract name `redteam_topology.md` |
| `..._redteam_layout_REGATE3.md` | `680229e7…` | **DEFECTIVE** | staging `verification/`, dated name |
| `..._redteam_layout_REGATE3b.md` | `b487fd16…` | SOUND | staging `verification/`, occupying the contract name `redteam_layout.md` |

**WHICH REVIEW EACH CONTRACT NAME CARRIES, STATED PLAINLY BECAUSE M-REV READS
ONLY THOSE TWO NAMES.** As of this pass both contract-named files carry **SOUND**
reviews (`REGATE3b` topology, `REGATE3b` layout), while **two `DEFECTIVE`
re-gate-3 lenses sit beside them under dated names** (`REGATE3` topology,
`REGATE3` layout). A gate that parses one filename cannot see the other four
documents, so the archive is where the disagreement has to be legible.

**THIS PASS DOES NOT RESOLVE WHICH VERDICT GOVERNS, AND THAT IS DELIBERATE** —
choosing what the contract name carries IS the seal decision, and this pass is
explicitly not a seal pass and not a re-gate. What it does is make the choice
IMPOSSIBLE TO MAKE BY ACCIDENT: five documents, five md5s, five verdicts, all in
the append-only folder, none of them reachable only through a build directory.

**THE TWO TOPOLOGY LENSES DISAGREE ON SEVERITY, NOT ON FACTS.** Both found the
`power_tree.yaml` dissipation worked example computing at `0.150 A` — a key
`power_topology.py` does not read — and publishing `Tj 107.9 °C / 17.1 °C
margin` against the graded `117.08 °C / 7.92 °C`. `REGATE3` graded it **P0**
(a load-bearing number WRONG in the canonical file); `REGATE3b` graded it
**P1**. Same measurement, same arithmetic, different severity. **It is fixed
either way** (ADR-0028 Decision 1, plus the `LDO_TJ_WORKED_EXAMPLE` bound that
regenerates all four numbers from the graded keys and goes red in both drift
directions), so the severity split changes nothing about the remedy and is
recorded here for the re-gate to settle rather than argued.

| # | Finding (severity) | Disposition | Evidence / change |
|---|---|---|---|
| RG3-T-P0/P1-1 | worked example reads `linear_rails[5V_KEY_RELAY].iout_max_A` (0.150 A), publishing a thermal margin **2.16×** the true one, and re-asserts a `+3.8 °C` excursion ADR-0027 §4 deletes. Graded **P0** by `REGATE3`, **P1** by `REGATE3b`. | **FIXED** — recomputed from `rails[3V3]`'s own keys; the `+3.8 °C` line deleted, not re-argued. Made structural: a `worked_example:` line is the only second copy and a bound regenerates it. | ADR-0028 Decision 1; bound `LDO_TJ_WORKED_EXAMPLE` CITED, red-tested in BOTH drift directions (revert the line → 999; move the key → 999). |
| RG3-T-P1-1 | the series sum starts at a PCB pad while ADR-0021 specifies the supply AT THE CONNECTOR — 20–60 mΩ of Micro-Fit contact resistance, **28–83 % of the whole margin**, in no sum, no dossier and no OWED list. The prior round's ORDER_README ladder already had a "with the connector" row **that went negative**. | **RECORDED + DOSSIER FIXED.** The node ambiguity is NOT resolved by this pass (it is an ADR-0021 question); the resistance is now in `02_parts/43650-0224/part.yaml` `limits:` with CITED and INHERITED graded apart, so the next sum cannot omit it by not knowing. | ADR-0028 Decision 3 + the margin-vs-ambient ladders. |
| RG3-T-P1-3 | `D_ESD_IN` (PESD5V0S1BA) is the lowest-breakdown clamp on the board, `V_BR` **min 5.5 V** against a 5.25 V ceiling, upstream of F1 and the eFuse with nothing in series, and its dossier had **no `limits:` block at all**. | **JUDGED, NOT WAIVED:** placement DEFENSIBLE (ESD belongs at the connector; `D_REVCLAMP`'s downstream rule is about a SUSTAINED crowbar that must trip F1 — different job); derating NOT defensible; `limits:` added; a 6.0/6.8 V stand-off SOD-323 recorded as a v-next part change. | ADR-0028 Decision 5; `02_parts/PESD5V0S1BA/part.yaml` `limits.derating_note` + `limits.placement_verdict`. |
| RG3-T-P1 (coil) | the ADR-0023 reed pull-in invariant still carried `v_il_max 0.540 / vdd 4.740` derived from a rail floor ADR-0027 re-derived to **4.691 V** — a SAFETY gate **49 mV too loose in the PERMISSIVE direction**, which would have accepted a coil at 4.151 V against a 4.200 V must-operate. | **FIXED** — 0.491 / 4.691 propagated, both margin tables re-derived (all rows still positive, +0.445 V at +70 °C), `K_STOP`'s insensitivity claim corrected rather than carried. Made structural. | ADR-0028 Decision 8; bound `COIL_PULLIN_BUDGET` CITED, red-tested (revert the dossier → 999; and at the stale 0.540 the coil evaluates to 4.151 V, firing B-CORNER). MEASURED node 0.056 V — the board was never at risk, the gate was. |
| RG3-L-P0 | the 328.29 mΩ series sum derates ONLY the copper; 58 % of it is components at 23 °C / a 70 °C junction / ≤85 °C, and `F1` is a **PTC with no published R-vs-T**. Break-even F1 ×1.82. | **RECORDED, WITH A BOUND ON THE ASSUMPTION.** Citable corrections give +29.1 → +23.1 mV. Bourns' own `Ihold` derating table, inverted under a NAMED assumption, puts `R(85 °C)/R(23 °C)` at **1.0–1.15** and makes ×1.82 imply a 278 °C polymer switching temperature. Still UN-CITABLE; on the bench list. | ADR-0028, the three-grade section. |
| RG3-L-P1-1 | `Tj = Ta + PD·θ_JA` omits the board's other **0.958 W** — +1.55…+4.65 °C, i.e. **20–59 %** of the declared 7.92 °C margin. | **RECORDED AND CARRIED SEPARATELY**, not folded into a graded number (it is a model output, not a citation). The honest margin at Ta 75 °C is **3.3–6.4 °C**, and the citable ambient ceiling 82.9 °C is known-optimistic by 2.8–4.7 °C. | ADR-0028 thermal ladder + bound `LDO_TA_MAX_CITED`. |
| RG3-L-P1-2 | ADR-0026's options table for the LDO tab enumerated a 3V3 pour and "state the path", and **never counted the vias** — 6 more in the existing pad is **−18.0 °C/W / +8.4 °C** for no BOM, schematic or netlist change. | **RECORDED as the cheapest item in the options pricing**, for the next copper revision beside ADR-0027's deferred 5 V pour. | ADR-0028 Options (b). |
