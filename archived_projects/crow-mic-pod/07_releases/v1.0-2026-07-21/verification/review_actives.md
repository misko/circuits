# Fresh-context pin review — actives group (U1, D1, D2)

Reviewer: fresh-context agent, no design-session context. Expectations derived
independently from the datasheet figures below; board nets judged against them.
Board topology inferred ONLY from net membership in the sealed
`04_kicad/crow_mic_pod.kicad_pcb` (read-only) and the conclusion-free dossiers.

## U1 — OPA1678IDR, SOIC-8 (Package_SO:SOIC-8_3.9x4.9mm_P1.27mm)

Datasheet reference: Figure 5-3 "OPA1678: D Package, 8-Pin SOIC and DGK
Package, 8-Pin VSSOP (Top View)", page 4, SBOS855E (rev Dec 2022), plus the
"Pin Functions: OPA1678" table on the same page.

Expected (top view): pin 1 top-left; left side top-to-bottom 1..4 =
OUT A, -IN A, +IN A, V-; right side bottom-to-top 5..8 = +IN B, -IN B,
OUT B, V+. Winding CCW.

Winding check: dossier computes CCW; pad table (+y down) puts pad 1 at W/top,
pad 4 W/bottom, pad 5 E/bottom, pad 8 E/top — exactly the figure, no mirror.
**PASS**.

Derived stage topology from net membership (independent of any schematic):
- AIN: C3.2 (AC coupling), R3.1 (R3.2 -> VMID bias), U1.3 — non-inverting mic input.
- FB_A: R6.2 (R6.1 -> A_OUT feedback), R7.1 (R7.2 -> VMID), U1.2 — gain divider.
- A_OUT: U1.1, R6.1 (fb), R8.1 (into inverter), R10.1 (series out to choke/AUDIO_P leg).
- FB_B: R8.2 (input R from A_OUT), R9.1 (R9.2 -> B_OUT feedback), U1.6 — inverter node.
- B_OUT: U1.7, R9.2, R11.1 (series out to choke/AUDIO_N leg).
- VMID: R4/R5 divider (R4.1 from filtered 5VF), C4/C5, R3.2, R7.2, U1.5.

| pin | function (datasheet) | board net | verdict | reason |
|---|---|---|---|---|
| 1 | OUT A | A_OUT | PASS | stage-A output; feeds R6 feedback, R8 inverter input, R10 series output — correct output node |
| 2 | -IN A | FB_A | PASS | R6/R7 feedback divider node referenced to VMID — correct inverting input for non-inverting stage |
| 3 | +IN A | AIN | PASS | AC-coupled (C3) mic input with R3 bias to VMID — correct non-inverting input |
| 4 | V- | GND | PASS | single-supply operation; V- to ground is correct |
| 5 | +IN B | VMID | PASS | unity-inverter non-inverting input tied to midrail reference — correct |
| 6 | -IN B | FB_B | PASS | virtual-ground node with R8 input / R9 feedback — correct inverting-stage summing node |
| 7 | OUT B | B_OUT | PASS | inverter output; feeds R9 feedback and R11 series output — correct |
| 8 | V+ | 5V | PASS | positive rail on supply pin. Note (observation, not a fault): op-amp is on raw 5V while VMID/mic bias use filtered 5VF — a design choice, electrically valid |

U1 VERDICT: PASS

## D1 — TPD2E2U06DRLR, DRL (SOT-553 / 5-pin SOT)

Datasheet reference: Section 5 "Pin Configuration and Functions", "DRL Package
5-Pin SOT Top View" figure + Pin Functions table, page 3, SLLSEG9C (rev Dec 2019).

Expected (top view): 1 top-left NC, 2 mid-left NC, 3 bottom-left IO1,
4 bottom-right GND, 5 top-right IO2. NC "not connected... left floating,
grounded, or connected to VCC". IO pins "connect as close to the connector
as possible".

Winding check: dossier pad table (+y down): 1 W/top, 2 W/mid, 3 W/bottom,
4 E/bottom, 5 E/top — matches the figure 1:1, CCW, no mirror. **PASS**.

| pin | function (datasheet) | board net | verdict | reason |
|---|---|---|---|---|
| 1 | NC | unconnected | PASS | datasheet allows floating NC |
| 2 | NC | unconnected | PASS | datasheet allows floating NC |
| 3 | IO1 | AUDIO_P | PASS | protected channel on balanced line; AUDIO_P is on J1.1 (connector side of choke L1) — placement per datasheet intent |
| 4 | GND | GND | PASS | ground pin on ground |
| 5 | IO2 | AUDIO_N | PASS | protected channel on the other balanced line (J1.2) — symmetric with IO1 |

Working voltage 6 V vs lines biased near VMID (~2.5 V) swinging within the
5 V rail: within rating.

D1 VERDICT: PASS

## D2 — SS14 schottky, SMA (Diode_SMD:D_SMA)

Datasheet reference: SS12-SS1200 MDD datasheet page 1, Mechanical Data
("Polarity: Color band denotes cathode end") + DO-214AC/SMA outline drawing.
KiCad `Diode_SMD:D_SMA` convention: pad 1 = cathode (band end). part.yaml
pad 1 function = K — conventions agree.

Independently derived drive topology from net membership:
BEEP_5V (J1.3, from the far end over the cable) -> R12 -> BZ_P -> BZ1(+) ...
BZ1(-) -> BEEP_RET -> J1.6 (return to far end). So the transducer is fed
switched 5 V on the BZ_P side and returns on BEEP_RET; on-state polarity is
BZ_P positive, BEEP_RET low.

Required flyback orientation: the diode across the winding must be
reverse-biased in the on-state, i.e. **cathode must face BZ_P** (the
positive/driven node), anode on BEEP_RET. At switch-off the winding pulls its
driven end negative (high-side switch case) or its return end positive
(low-side switch case); in BOTH cases anode=BEEP_RET / cathode=BZ_P is the
clamping orientation, so the verdict is robust to which end the far-end
switch interrupts.

| pad | function | board net | verdict | reason |
|---|---|---|---|---|
| 1 | K (cathode, band end per D_SMA convention) | BZ_P | PASS | cathode faces the driven/positive node — reverse-biased in on-state, clamps the inductive kick at turn-off |
| 2 | A (anode) | BEEP_RET | PASS | anode on the return side — freewheel current path BEEP_RET -> BZ_P through the winding |

Ratings: SS14 VRRM 40 V / IF 1.0 A vs a 5 V, small-signal magnetic transducer:
ample margin. (A TVS D3 also sits across the same pair — outside this group.)

D2 VERDICT: PASS

---

GROUP VERDICT: PASS
