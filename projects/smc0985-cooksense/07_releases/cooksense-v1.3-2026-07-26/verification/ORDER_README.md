# ORDER README — cooksense MAIN board **v1.3** (project smc0985-cooksense)

---

## 🛑 NOT SEALED — H4 FAILS ITS ISOLATION REQUIREMENT (RULED 2026-07-26)

**The fab package is complete and reproduces. The board has a barrier that does
not meet its own rule, and this release is NOT sealed and NOT orderable.**

**H4's keypad-to-SELV creepage is 4.0286 mm against a 6.000 mm requirement — a
shortfall of 1.9714 mm.** The 6.598 mm this document used to print is a geodesic
around a **1.000 mm** through-slot. **Ruled: the notch does not count.** At the
declared pollution degree 3 the IEC 60664-1 minimum groove width X is **1.5 mm**,
and a gap narrower than X is measured **straight across**; the one exemption
applies only where the associated clearance is below 3 mm, and this one is 6 mm.
The 3.000 mm modelled washer also **roofs** 0.800 mm of the slot, turning it from
a drainable gap into a capillary trap in a steam environment. **Full ruling,
scope and measurements: §1.**

**Exactly one hole is affected** — H1, H2 and H3 pass on figures that cross no
void (13.6299, 13.1525, 40.9324 mm).

**DO NOT ORDER AGAINST THIS ARCHIVE.** Everything else below is accurate and
every other gate is green.

## Gate state — all green except the escalation above

`kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` on
`04_kicad/cooksense.kicad_pcb`: **0 violations / 0 unconnected / 0 schematic
parity**. Placement gate P-COLLIDE **0 pad shorts / 0 anchored courtyard
overlaps**. E-INV **83/83**. A-ROT **189/189 CPL rotations sourced from measured
per-LCSC rows**. A-POS **189/189 CPL rows on the pad-centre datum, worst
deviation 0.0000 mm**. M-REPRO **green across three from-source regenerations**
(**1047** vias each, identical track/via/footprint hashes, and all three match the
board in this archive).

**The three v1.3 P0s are closed and each one is named here because the fix
changed what you order:**

1. **P0-A — the isolated loop is now ONE connector.** `J_ESTOPLOOP` and
   `J_CONTACTOR` are merged into a single 4-pole isolated terminal block
   **`J_ISOLOOP`** (KF350-3.5-4P). Both only ever carried isolated-domain nets,
   so the merge is isolation-neutral-or-better: one isolated body with one
   2.0 mm moat and one pour keepout instead of two adjacent bodies. **Any
   earlier text naming J_ESTOPLOOP or J_CONTACTOR is obsolete — neither exists.**
   See §11 for the pole legend, which is the field-wiring gate.
2. **P0-B — `R_OPENT` was ORDERED at 6.2 kΩ where the design needs 62 kΩ.** The
   open-thermistor detect threshold would have sat at 3.1073 V, above the
   LMV393's 2.500 V common-mode ceiling, so an open, broken or unplugged
   thermistor would have read FINE instead of OVER-TEMP. Now **C37825**
   (0402WGF6202TCE, 62 kΩ ±1%). See §12.
3. **P0-C — `R_WDPETPD` was ORDERED at 100 kΩ where the design needs 1 kΩ.** The
   TPS3823's WDI input *sources* I_IL 190 µA and V_IL is 0.3·VDD = 0.99 V, so the
   largest hold-down that works is **5.21 kΩ**. At 100 kΩ the node sits above
   V_IH and **the watchdog is silently disabled** — the board's primary runaway
   backstop would not exist, and it fails only in the case it exists for. Now
   **C11702** (1 kΩ). Same root cause as P0-B: a value-authored passive with no
   pinned LCSC, resolved by a picker that returned a wrong decade. See §12.
4. **P0-D — the ISO moat is enforced on routed copper**, not just declared. The
   `opto_isolation_2mm` DRU rule (IEC 60664-1 basic insulation, 30 V working,
   pollution degree 3) is green. **State the metric beside the number — three
   different measurements of one geometry are all correct and they answer
   different questions:**

   | metric | minimum | binding pair |
   |---|---|---|
   | **all copper, all layers** (pads + tracks + FILLED pours) | **2.0000 mm** | CONTACTOR_C at `J_ISOLOOP.1` → **GND zone edge**. Re-measured per layer 2026-07-26: F.Cu 2.0000, In1.Cu 2.0000, In2.Cu 2.0000, B.Cu 2.0000 — **the minimum is 2.0000 on all four**, because the moat keepout is a 2.0 mm offset on all four and the pours are clipped to it. |
   | pad-to-pad, true polygon distance | 2.1709 mm | `U_OPTO.3[CONTACTOR_E]` ↔ `J_RH_EXHAUST.5[SHIELD_DRAIN]` |
   | pad-to-pad, bounding-box | 2.126 mm | `J_ISOLOOP.4[CONTACTOR_E]` ↔ `J_DOOR.MP[GND]` |

   **2.0000 mm is the honest headline.** The margin is 0.000 mm *by
   construction*: the `iso_moat_block` pour keepout IS defined as exactly the
   2.0 mm offset of the isolated copper, so the pour edge lands exactly on it.
   That is the rule being met precisely, not a near miss. v1.2 measured
   **0.199 mm** at this rule, and the same cross-layer scanner run unchanged
   against the sealed v1.1 board returns **915 pairs under 2.0 mm, worst
   0.0000 mm** — which is what makes the 2.0000 believable rather than merely
   printed.

**v1.0 and v1.1 remain DO-NOT-ORDER** — see `07_releases/*/SUPERSEDED.md`. Three
independent defects, any one of which is disqualifying: R_OPENT at 6.2 kΩ
defeating the open-thermistor safety detect, CE1 shipped at CPL rotation 180°
(a reversed 220 µF polarized electrolytic across a live 5 V rail), and 22 wrong
CPL rotations including the ten safety-chain SOT-23-6 gates, which at 90° out do
not connect their intended nets.

---

Cooktop safety-interlock sidecar for a Raspberry Pi: keypad reed-relay matrix
(isolated COMB — vertical relays, contact columns pocketed between pairs),
watchdog + hardware AND-chain interlock, 12× reed coil drivers, Type-K
thermocouple front-end (MAX31856), dual-comparator thermistor window
(over-temp + open-detect, new in v1.3), opto-isolated contactor dry-contact
loop on its own connector (new in v1.3). Board **188 × 92 mm**, **4 layer**,
**222 components** placed (v1.3 generate_board; 223 -> 222 on the J_ISOLOOP
merge), E-INV **83/83** on the v1.3
netlist. v1.3 is the second electrical revision (v1.2 was never sealed);
schematic deltas vs v1.2: door pull-down, open-detect comparator half,
comparator rail move, isolated-loop connector move (§2, §11).

---

## 1. ⚠️ MECHANICAL / ENCLOSURE — THE LOAD-BEARING ASSUMPTION

The board's keypad-contact domain is isolated from SELV logic by **>= 6.000 mm
creepage** (brief §4/§7, ADR-0001). That figure is only held **because the
enclosure is NON-CONDUCTIVE and no conductive plate, bracket, rail or standoff
set bonds two or more of the four mounting holes together** (user decision,
2026-07-25, ADR-0012).

Under that assumption the governing rule is **PER-HOLE**: `a_i + s_i >=
6.000 mm` for each hole, where `a` = hardware-to-keypad-copper and `s` =
hardware-to-SELV-copper, with the hardware modelled as a **3.0 mm-radius
conductive disc** (M2.5 pan head + DIN125 washer + nut). At H3 and H4 the
fastener is SELV-BONDED (the GND pour reaches 0.200 mm from the hole wall, so
s < 0) and the requirement collapses to `a` alone.

MEASURED on filled copper by the `I-HW` gate, **re-measured 2026-07-26 on the
ROUTED board** (the earlier table was taken on track-free copper and both its
H1 and H2 rows are superseded), all against 6.000 mm.

**EVERY FIGURE BELOW NOW STATES THE METHOD THAT PRODUCED IT**, because this
board has now shipped three numbers whose metric was left implicit (the ISO pair
— bbox vs true-polygon vs all-copper; this I-HW table; and the H4 geodesic that
the ruling below overturned). A creepage number without its method is not a
measurement.

| Hole | a (keypad approach) | s (SELV approach) | governing figure | method | verdict |
|---|---|---|---|---|---|
| H1 | **−0.050** (track KP_D1) | 13.631 (pad K_U1.2) | keypad-BONDED -> s alone = 13.631 | **straight line, crosses no void** | PASS |
| H2 | **−0.050** (track KP_U6) | 13.153 (pad K_STOP.1) | keypad-BONDED -> s alone = 13.153 | **straight line, crosses no void** | PASS |
| H3 | 40.933 (pad K_U1.4) | −1.450 (GND pour) | SELV-bonded -> a alone = 40.933 | **straight line; crosses a void but irrelevant at 40.9 mm** | PASS |
| ~~H4~~ | ~~6.598~~ (pad K_STOP.3, RSTOP_MID) | −1.450 (GND pour) | ~~SELV-bonded -> a alone = 6.598~~ | ~~**GEODESIC around the notch**~~ | **SUPERSEDED — see the ruling below** |
| **H4** | **4.0286** (pad K_STOP.3, RSTOP_MID) | −1.4493 (GND pour) | SELV-bonded -> a alone = **4.0286** | **straight line, notch NOT credited (PD3, X = 1.5 mm)** | **FAIL vs 6.000** |

**H1 and H2 changed sign when the board was routed, and the verdict logic is why
that is still a PASS.** On track-free copper the nearest keypad copper to those
two fasteners was a pad, 2.305 mm and 3.129 mm away. On the routed board a
keypad TRACK passes under each fastener disc (a = −0.050 mm, i.e. touching), so
each fastener is now KEYPAD-BONDED and the requirement becomes the SELV approach
`s` alone — 13.631 mm and 13.000 mm, both far clear. The per-hole rule is
`a + s >= 6.000` with a negative approach meaning "bonded to that domain, so
measure the other side alone". Nothing got worse; the binding item changed.

**H4 IS THE FAILING HOLE. Its governing figure is 4.0286 mm against 6.000 mm
required** — straight line, disc edge to **pad K_STOP.3** edge, with the notch
NOT credited. **The 6.598 mm this paragraph used to headline was the geodesic
around the notch and is RETRACTED** by the 2026-07-26 ruling below. **State the
method with every figure — that omission is what let this pass seven reviews:**

| figure | to what | method | status |
|---|---|---|---|
| **4.0286 mm** | pad `K_STOP.3` (RSTOP_MID) | **straight line, notch not credited** | **GOVERNING — FAILS 6.000** |
| 4.6166 mm | nearest `RSTOP_MID` **TRACK**, (197.400, 45.600)→(197.000, 45.200) | straight line, crosses the through-cut | informational |
| ~~6.598 mm~~ | pad `K_STOP.3` | ~~geodesic around the notch~~ | **RETRACTED — the notch is not creditable at PD3** |
| ~~8.500 mm~~ | — | — | does not reproduce |

An earlier revision attributed both the 6.598 and the 4.617 to the same pad;
they are to different copper, which is exactly why each now names its target and
its method. All are north of the notch. Do not let
a rework shrink the notch or grow keypad copper near it.

> ## 🛑 RULED 2026-07-26 — THE NOTCH DOES NOT COUNT. **H4 IS A 4.0286 mm BARRIER AGAINST A 6.000 mm REQUIREMENT, AND IT FAILS.**
>
> **The H4 row in the table below is WRONG. Read this box instead.** The 6.598 mm
> it prints is a **GEODESIC around the isolation notch**, and the notch is not
> creditable.
>
> **The ruling.** IEC 60664-1 sets a minimum groove width **X** below which a
> groove contributes nothing to creepage — the path is measured **straight
> across**. **At pollution degree 3, X = 1.5 mm.** This notch is **1.000 mm**.
> The one exemption does not apply: X may be reduced to one third of the
> associated clearance only where that clearance is **below 3 mm**, and this
> requirement is 6 mm, so X stays 1.5 mm.
>
> | quantity | measured | method |
> |---|---|---|
> | notch | x[191.500, 200.000] y[48.800, 49.800] | Edge.Cuts vertices, **width 1.000 mm** |
> | H4 centre | (193.000, 52.000) | footprint anchor |
> | H4 centre → nearest notch edge | 2.200 mm | straight line |
> | modelled fastener disc (M2.5 pan head + DIN125) | r = 3.000 mm | assumption, §1 |
> | **disc overhang past the notch edge** | **0.800 mm** | the washer **ROOFS 80 % of the slot** |
> | nearest keypad copper | pad `K_STOP.3` (RSTOP_MID) at (197.450, 45.620), r 0.750 | filled copper |
> | centre-to-centre | 7.7786 mm | straight line |
> | **GOVERNING FIGURE** | **4.0286 mm** | **straight-line disc-edge to pad-edge, notch NOT credited** |
> | figure previously printed | 6.598 mm | geodesic around the notch — **not creditable** |
> | requirement | 6.000 mm | brief §4/§7, ADR-0001 |
> | **shortfall** | **1.9714 mm** | |
>
> **Three things reinforce the ruling and all point the same way.**
> 1. **The environment IS the pollution degree.** PD3 is declared because this is
>    steam and grease. A 1.000 mm slot in that environment fills with
>    condensate — which is the physical reason the X rule exists. This is not a
>    paper technicality applied to a clean board.
> 2. **The washer makes it worse, not better.** Overhanging the slot by 0.800 mm
>    it **roofs** it. An open slot drains and dries; a roofed 1 mm slot is a
>    **capillary trap** holding condensate against the barrier. The overhang was
>    treated as incidental geometry; it is an aggravating factor.
> 3. **The archive's own RED test already said so.** `t_ihw_prenotch` puts the
>    pre-notch board at **4.031 mm = FAIL**, so the notch converts FAIL to PASS on
>    0.5 mm of geometry the governing document says to ignore. **When a gate flips
>    verdict on something the standard says to disregard, the gate is measuring
>    the wrong thing.**
>
> **SCOPE — exactly one hole.** Re-measured all four with the bridged metric and
> the archive's own per-hole model (`a` = keypad approach, `s` = SELV approach, a
> negative approach meaning "bonded to that domain, measure the other side
> alone"):
>
> | hole | a | s | governing | straight line crosses a void? | verdict |
> |---|---|---|---|---|---|
> | H1 | −0.0500 | 13.6299 | keypad-BONDED → s alone | no | 13.6299 PASS |
> | H2 | −0.0500 | 13.1525 | keypad-BONDED → s alone | no | 13.1525 PASS |
> | H3 | 40.9324 | −1.4495 | SELV-BONDED → a alone | yes, but irrelevant at 40.9 mm | 40.9324 PASS |
> | **H4** | **4.0286** | −1.4493 | SELV-BONDED → a alone | **YES — bridged applies** | **4.0286 FAIL** |
>
> **STATUS: NOT SEALED, HELD.** The remaining choice is a schedule-versus-margin
> trade on the owner's own appliance. Until it is decided, **treat H4 as a
> 4.0286 mm barrier and do not rely on the 6.598 mm figure.**

**This table is generated from `verification/audit.txt` in this archive — if the
two ever disagree, audit.txt is the evidence and this table is stale.**

**BOLT THIS BOARD TO A METAL PLATE AND THE ISOLATION DEFECT RE-OPENS.** A
conductive plate bonding H1 (keypad side) to H4 (SELV side) makes the
governing rule the PAIRING form `min_i(a_i) + min_j(s_j)`, **which this board
FAILS** (it re-opens at **0.000 mm** — a DIRECT keypad-to-SELV bond, not a reduced clearance (measured: min_a -0.050 + min_s -1.450; see verification/audit.txt)). This is a mains-adjacent
cooking interlock: the consequence is keypad-domain contact voltage reaching
SELV logic.

**REQUIRED FASTENER SPEC — explicit line item for the assembler/integrator:**

> Mounting hardware MUST be **non-conductive (nylon/polyamide) M2.5**, OR
> metal M2.5 hardware **only** in a non-conductive enclosure where **no
> conductive plate, bracket, rail or standoff set bonds any two mounting
> holes**. Sign this off at integration; it is a safety property, not a
> preference.

**The H4 edge notch is deliberate — do not let the fab "clean it up".** H4 has
an edge notch milled at x[191.50, **200.00**] y[48.8, 49.8] (board coordinates;
200.000 IS the east board edge — an earlier revision printed 200.10, which is
0.10 mm outside the board and cannot be a notch coordinate).
It is OUTLINE geometry reaching the east board edge, NOT an internal slot, so
there is no router-bit minimum and no JLC internal-cutout surcharge. It cannot
be re-specified as an internal slot: the direct corridor there is 0.55 mm,
narrower than any router bit. Confirm in the fab preview that the notch
survives exactly as drawn.

The board carries this warning **on the silkscreen next to the mounting
holes**: "MOUNTING HW: NYLON M2.5 — OR METAL IN A NON-CONDUCTIVE ENCLOSURE
ONLY." / "A PLATE BONDING ANY 2 HOLES BREAKS THE 6mm KEYPAD ISOLATION.
ADR-0012", plus a "NYLON HW" flag at each of H1–H4.

## 2. ⚠️ MANDATORY SAFETY MITIGATIONS (both MANDATORY — the board design assumes them)

### 2-0. ⚠️ THE DOOR INPUT IS **NOT SUPERVISED** — READ THIS BEFORE COMMISSIONING

**What you commissioned** (`BRIEF.md` §92): *"Door: external NC reed + EOL (or
3-wire Hall)"* — a **supervised** input, meaning the board can tell a healthy
closed door from a fault.

**What this board implements:** a Form-A (**NO**) contact from `J_DOOR.1` (3V3)
to `J_DOOR.2/4` (DOOR_RAW), with `R_DOORPD` (10 k) holding the input low, read by
a **digital** Schmitt input (`U_SCHM.11`). **There is no EOL resistor and no
supervision.**

| door cable fault | what the board reads | safe? |
|---|---|---|
| broken / unplugged | LOW = "door open" | **YES** — fixed in v1.3; this was v1.1's fail-permissive defect |
| **shorted** (3V3 to DOOR_RAW) | HIGH = **"door closed"** | **NO — UNDETECTABLE** |

**A shorted door cable reads as a closed door, permanently and silently.** The
interlock will permit cooking with the door open.

**The aggravating factor, measured:** `J_DOOR.1` (3V3) and `J_DOOR.2` (DOOR_RAW)
are adjacent pads on a 1.25 mm-pitch JST-GH housing — **0.650 mm apart** — in a
pollution-degree-3 steam environment. That is the same 0.650 mm gap v1.3's own
P0-2 declared unacceptable for the isolated loop. A short is not hypothetical
here; it is the expected long-term failure of a wet connector.

**Until supervision is implemented, treat the door interlock as UNVERIFIED
against shorts and provide an independent means of ensuring the door is closed.**
This is a decision for the commissioning owner, not a defect the board hides:
v1.3 closes the defect it claimed (fail-permissive on wire break) and does not
claim supervision.

**v1.4 scope — it is a specification, not a patch.** Supervision needs three
distinguishable levels (open / normal / short), i.e. an **analog** read.
`DOOR_RAW` currently feeds a digital Schmitt input; **all 8 MCP3208 channels are
occupied (CH0–CH7) and all 4 comparator channels are used** (U_COMP ×2,
U_COMP2 ×2). So it requires a new analog path (a 9th channel, a mux, or a window
comparator) **plus** a new part and placement/routing **plus** the external
harness re-spec (NC reed + EOL resistor in the door assembly) **plus** firmware
to classify the three levels.


### 2a. P1-2 — Door harness spec (build the harness to THIS spec)

v1.3 fixed the door input's fail-permissive polarity IN HARDWARE:
`R_DOORPU (10 k to 3V3)` became `R_DOORPD (10 k to GND)`. Commit b9dd4a6,
verbatim: *"Now open circuit = door OPEN, matching R_ESTOPPD and R_MODEPD."*
In ≤v1.2, DOOR_RAW was the only external safety input pulled to the permissive
rail — a broken or unplugged door cable read DOOR-CLOSED and the abort
silently never happened.

**Required harness (MANDATORY):** `3V3 (J_DOOR.1) → Form-A (normally-open,
magnet-CLOSES) reed switch at the door → J_DOOR.2 (DOOR_RAW)`. Door closed =
reed closed = DOOR_RAW high = permissive. Door open, cable broken, cable
unplugged, or reed failed open = DOOR_RAW pulled to GND = **DOOR-OPEN =
fail-SAFE**.

**Residual permissive case, named:** a conductor-to-conductor SHORT between
harness wires 1 and 2 (3V3 to DOOR_RAW — chafe, pinch, moisture bridge) reads
DOOR-CLOSED regardless of the actual door. No pull direction can remove this
case. Mitigate with harness inspection at integration and the labeling
discipline of §10.

### 2b. P1-3 — Host runtime thermistor cross-check (ACCEPTANCE ITEM)

The hardware window (U_COMP over-temp + U_COMP2 open-detect, both LMV393 on
3V3_ANALOG) is the backstop, not the monitor. **The host software MUST
cross-check the two thermistor channels against each other and against the
MCP3208 ADC readings at runtime, every control cycle, and refuse HOST_AUTH on
disagreement.** Acceptance: demonstrate that (a) an unplugged NTC harness and
(b) a shorted NTC each drop TEMP_OK in hardware AND are independently detected
and reported by the host from the ADC path before the hardware trip.

Measured v1.3 open-detect facts (commit 16ae67b / STATUS):
- Open-circuit sense node reads **2.2687 V** (worst-high 2.2829 V) against the
  LMV393 VICR ceiling of **2.500 V** at VCC 3.3 V — **+217 mV margin**. Every
  reading either comparator sees, open included, is inside VICR.
- Open-detect threshold **2.0370 V**; worst-case separation to an open reading
  **193 mV** vs the LMV393 VIO of **9 mV**.
- Nuisance-trip floor **−10.4 °C typical / −7.4 °C worst** (a connected NTC
  colder than that trips the open-half — irrelevant in a cooktop enclosure).
- Over-temp trip **72.80 °C** on the unchanged 68 k / 10 k divider, inside the
  brief's 70–75 °C window.
- Do NOT "clean up" R_CLMPA/R_CLMPB (22 k sense-node bleeds): they are what
  keep an open reading inside VICR. Without them the open-detect is INERT.

#### ⚠️ CH0 and CH3 DO NOT USE THE SAME TRANSFER FUNCTION AS THE OTHER SIX

The 22 k bleeds sit ACROSS the camera-A/B thermistors, so those two channels
divide differently from CH1/CH2/CH4–CH7. **If you implement this acceptance test
with the plain 10 k/NTC model it will not work, and it will fail in the
direction that matters.**

Divider, CH0 and CH3 only:

```
3V3_ANALOG --[ R_REF 10k ]--+-- node --[ R_SER 1k ]-- ADC (high-Z, no DC load)
                            |
                            +--[ NTC 10k B25/85=3987 ]-- GND
                            +--[ R_CLMP 22k ]---------- GND
```

**Correct host inversion for CH0/CH3 — use this, not the naive one:**

```
R_par = 10000 * V / (3.3 - V)              # what the naive model stops at
R_ntc = 1 / (1/R_par - 1/22000)            # THE STEP THE NAIVE MODEL OMITS
T_C   = 1/(1/298.15 + ln(R_ntc/10000)/3987) - 273.15
```

**Error if you omit the clamp term** (computed, B25/85 = 3987):

| true °C | node V | naive model reports | error |
|---|---|---|---|
| 0.0 | 1.8872 | 18.7 | **+18.7** |
| 10.0 | 1.6949 | 23.8 | +13.8 |
| 25.0 | 1.3444 | 33.6 | +8.6 |
| 40.0 | 0.9845 | 45.4 | +5.4 |
| 55.0 | 0.6804 | 58.4 | +3.4 |
| 70.0 | 0.4564 | 72.3 | +2.3 |
| 72.8 (hw trip) | 0.4231 | 74.9 | +2.1 |
| 85.0 | 0.3041 | 86.5 | +1.5 |

**AND THIS IS WHY IT MATTERS FOR TEST (a).** An OPEN NTC drives the node to
**2.2687 V** — which the derivation above reproduces exactly, confirming the
model. Fed to the naive inversion that reads as **8.4 °C**: a plausible, healthy,
cold reading. **The host would not report a fault, and acceptance test (a) —
"an unplugged NTC harness is independently detected and reported by the host from
the ADC path before the hardware trip" — would pass a board on which the host
detects nothing.** With the corrected inversion, `1/R_par − 1/22000 → 0`, so
R_ntc → ∞ and the open is unmistakable.

**Recomputed accept/reject thresholds for the host, CH0/CH3:**

| condition | node V | corrected R_ntc | host must |
|---|---|---|---|
| open / unplugged | **≥ 2.2000** | ≥ **220 kΩ** | declare FAULT, refuse HOST_AUTH |
| plausible operating band 0–85 °C | 0.3040 – 1.8876 | **1.06 kΩ – 34.06 kΩ** | accept |
| shorted NTC | ≤ 0.05 | ≤ **155 Ω** | declare FAULT, refuse HOST_AUTH |

> **⚠️ CORRECTED 2026-07-26 — the resistance column of this table was WRONG in
> two rows, and both errors pushed a host toward the unsafe or the useless. Use
> the VOLTAGE column as the primary test.**
>
> **Row 2 said `3.0 k – 32.6 k`.** Recomputed with this section's own inversion,
> the 0–85 °C band is **1063.7 Ω to 34 057 Ω** (equivalently, the voltage
> endpoints 0.3040 V and 1.8876 V invert to 1047.6 Ω and 34 307 Ω). The old
> band `3.0 k – 32.6 k` corresponds to **54.5 °C … 0.79 °C** — so a host
> implementing it literally would declare FAULT and refuse HOST_AUTH for any
> camera thermistor above **54.5 °C, i.e. 18 °C BELOW the 72.80 °C hardware
> trip.** The appliance would refuse to cook once merely warm, and the
> technician chasing that nuisance lockout is exactly the person who would
> widen or disable the board's only software backstop.
>
> **Row 1 said `→ ∞ (≥ 1 MΩ)` beside `≥ 2.20 V`. Those are not the same test.**
> V = 2.2000 inverts to **R_ntc = 220 kΩ**, not 1 MΩ — a factor of 4.5. Going
> the other way, **R_ntc ≥ 1 MΩ requires V ≥ 2.2533 V**, and the worst-case open
> reading with ±1 % on R_REF (10 k) and R_CLMP (22 k) is
> `3.3 · 21780/(10100+21780) =` **2.2545 V**, which the nominal inversion turns
> into 1.089 MΩ. That is **1.2 mV of margin** before ADC INL — so a host
> implementing the RESISTANCE form can miss an unplugged NTC on a
> worst-case-tolerance board. **That is acceptance test (a) failing in exactly
> the way this section was written to prevent.** The voltage form has **54 mV**
> of margin (2.2545 worst-low against a 2.2000 threshold). **Implement the
> voltage test; treat the resistance column as explanatory.**

CH1/CH2/CH4–CH7 keep the unclamped model: `R = 10000·V/(3.3−V)`, same B and R25.
Deriving one curve and applying it to all eight is the mistake this box exists to
prevent. **This is arithmetic, not calibration — no bench step is required.**

## 3. JLCPCB order options

| Setting | Value |
|---|---|
| Layers | **4** (In1 = GND plane, In2 = 3V3 plane; NO plane north of y53 — keypad band, relay row, pockets and coil gaps are plane-free) |
| Dimensions | 188 × 92 mm; 12 milled 0.6 mm isolation slots on Edge.Cuts **plus the H4 east-edge notch (§1)** — confirm the fab preview keeps the slots as internal routs and the notch as outline |
| Via tier | **ADVANCED small-via option required** — 0.25 mm via / 0.15 mm drill (via-in-pad escapes). Do NOT order standard 0.45/0.30. |
| Assembly | Standard SMT, TOP side only (assembly.yaml: 0 footprints on B.Cu), qty 5 (JLC minimum for this board; A-STOCK grades stock at qty × 5). BOM + CPL regenerated at v1.3 seal — the current `06_build/fab/` set is v1.2-STALE, do not upload it. |
| CPL population | The **16** self-supplied refs (§4) carry `exclude_from_pos_files` in v1.3 source — they are OFF the CPL entirely. **189 CPL rows**, all rotation-sourced from measured per-LCSC rows and all on the pad-centre datum (worst deviation 0.0000 mm). **READ THIS PRECISELY — the two directions are not the same.** A CPL row with no matching BOM line is a real defect: **stop.** The REVERSE is expected and must NOT stop the order: the BOM carries **205** designators and the CPL **189**, so **16 designators are on the BOM with no placement row, by design** — `J_ISOLOOP`, `J_LOADCELL`, `J_PI`, `J_TC` and the **12 reed relays** (K_U1-K_U6, K_D1-K_D4, K_PRESS, K_STOP). JLC reports that class too. An earlier revision said only "unmatched CPL entries ... stop", which a reader could act on by aborting a good order or, worse, by re-adding THT placements to an SMT-only run. |

**Order-day gate:** (a) stock recheck per §5; (b) preview shows all 12 slots
as internal routs AND the H4 edge notch intact; (c) ADVANCED 0.25/0.15 via
option selected; (d) the §6 human gate signed off.

## 4. ⚠️ SELF-SUPPLIED / HAND-SOLDER — 16 REFS, 14 OF THEM DO-NOT-SUBSTITUTE

**Sixteen** refdes are not JLC-assembled. They fall into three classes and the
class decides whether you may substitute — the earlier "thirteen ... both
classes" wording predates J_ISOLOOP, J_LOADCELL and J_PI joining the list and
was self-contradictory against this section's own heading. They are self-supplied and
hand-soldered at integration. The release MANIFEST's `not_assembled:` line is
GENERATED from `03_src/cooksense/rules/assembly.yaml` as a bare refdes list
(canon A-POP: refdes only in manifest lines, no prose).

The 16 refdes, in three classes — the class matters, because only two of them
are DO-NOT-SUBSTITUTE:

```
K_U1 K_U2 K_U3 K_U4 K_U5 K_U6 K_D1 K_D2 K_D3 K_D4 K_PRESS K_STOP   (12 reeds)
J_TC                                                               (TC jack)
J_ISOLOOP                                                          (NEW in v1.3)
J_LOADCELL  J_PI                                                   (NEW to this list)
```

**J_LOADCELL and J_PI are new to this list and that is a v1.0/v1.1 CORRECTION,
not a v1.3 change.** Both are pure through-hole (MEASURED: 5/5 and 40/40 plated
drilled pads, F.Paste on none) on a `service: standard, sides: [top]` order,
which is reflow SMT only — no process solders them. Both sealed releases
nevertheless shipped them as CPL placement rows. They keep their LCSC codes on
the BOM so the order sheet still says what to buy; they simply stop being
machine-placement instructions. **Substitution IS allowed for these two** (any
B5B-XH-A equivalent; any 2x20 2.54 mm female header).

| Ref(s) | Part | Notes |
|---|---|---|
| K_U1..K_U6, K_D1..K_D4, K_PRESS, K_STOP (×12) | **Standex DIP05-1A72-12L** reed relay | JLC C1561362 stock 0 (and 0 on all five DIP05-1A72 variants, 2026-07-25). Footprint is pinout-12-specific (Relay_StandexDIP_1A_pinout12). **No substitutes** — the isolation-comb creepage (6.12 mm track-aware, measured) and the coil/contact column pinout are the safety argument (ADR-0006). Approved alternate: DIP05-1A72-12D (identical pinout, internal coil diode). Order 16 (12 + 4 spares). THT hand-solder. |
| J_TC | **Omega PCC-SMP-K** panel Type-K jack | All 7 catalog hits stock 0 (2026-07-25). Ø1.77 mm PC pins + 2 NPTH bracket holes match the Omega PCC-OST-SMP drawing. **No substitutes** — the chromel/alumel jack contacts ARE the cold-junction interface; a brass lookalike injects a parasitic junction. THT hand-solder. |

## 5. ⚠️ MANDATORY ORDER-DAY STOCK RECHECK

Re-run `jlc_stock_check` on order day against `fab/bom.csv`. **Every figure below
is quoted from `verification/stock_check.csv` in THIS archive** (one snapshot,
2026-07-26) — earlier revisions of this table quoted a v1.2 run and disagreed
with the shipped file in twelve values.

| Ref | LCSC | stock (2026-07-26) | note |
|---|---|---|---|
| U_EFUSE (TPS259573) | C2653844 | 160 | thin |
| F1 polyfuse | C89650 | 244 | thin |
| U_ADC (MCP3208) | C16939 | **128** | thin |
| J_PWR Micro-Fit | C587657 | 778 | |
| U_COMP / U_COMP2 (LMV393IDR) | C7984 | 15896 | second source ST C283325 is pinout drop-in but its datasheet lacks TI's out-of-common-mode table — prefer C7984 |
| **R_OPENT (62 kΩ)** | **C37825** | 127526 | **NOT C25915 — see §12** |
| **R_WDPETPD (1 kΩ)** | **C11702** | 1432157 | **NOT C25741 — see §12** |
| R_CLMPA/B (22 kΩ) | C25768 | 1506629 | |
| J_ISOLOOP (KF350-3.5-4P) | C42400616 | **0** | self-supplied, off the CPL; JLC stocks no KF350 4P line and has no CAD for it |

A-STOCK grades every coded, PLACED line at stock >= qty x build_quantity (5).
The only line that fails is C42400616, which is unplaced by design.

## 6. ⚠️ ORDER-PREVIEW HUMAN GATE — tick EVERY row against the JLC assembly preview BEFORE paying

CPL rotation is this board's proven failure mode (v1.0/v1.1 banner). **Every
one of the 189 CPL rotations resolves from a per-LCSC row in the authority
table** — A-ROT green, `jlc_rotation_audit --table` 61 rows OK, and no
`--allow-unsourced-rotations`, so not one row fell back to the name-keyed DB.

**Two honest qualifiers on that sentence, because an earlier revision of this
paragraph said "nothing below is guesswork any more" and that claimed more than
the archive can show you:**

1. **You cannot re-derive it from this archive alone.** The 61-row authority
   table lives in the fleet repo, not here. What ships here is
   `verification/rotation_measurements_v13.txt` — the **15** codes measured for
   this revision, covering **26 of the 189** CPL rows out of 51 distinct codes.
   **And that overstates the in-archive evidence: 13 of those 15 read
   `ROW: (WITHHELD — single-channel)`.** Only **C6186 (U_LDO) and C8185**
   (4 refs) were landed as authority rows from measurements that ship here, so
   the in-archive LANDED provenance is **2 codes / 5 CPL rows**, not 15/26. The
   13 withheld codes are all covered either by the §6 A-POL human gate or by the
   bidirectional-part exclusion, so nothing is unguarded — but a withheld
   measurement must not be mistaken for a landed one. For the other 36 codes you
   are trusting a table you cannot open. That is why §6 exists at all.
2. **One disagreement inside this archive is now RESOLVED, and the resolution
   was against my own earlier measurement.**
   `verification/rotation_C22046_measurement.md` reports a second operator that
   disagreed by 180° with the authority table on **C189896** (J_DOOR, J_ESTOP,
   J_MODE, J_RH_AMBIENT, J_RH_EXHAUST) and **C2683602** (J_KEY_MATRIX), and by
   **180°** on **C125121** (U_OPTO, the isolation part — that operator returned
   90 where the table says 270). **Re-measured 2026-07-26:
   the authority table is right and that second operator was wrong.** It applied
   a standard counter-clockwise rotation matrix to KiCad coordinates, whose Y
   axis points DOWN — which mirrors the fit and therefore swaps 0 with 180 and
   90 with 270. Verified empirically against pcbnew on `J_KEY_MATRIX` at
   orientation −90°: pcbnew puts pad 1 at (+1.850, −5.625) from the anchor, the
   y-down matrix reproduces it exactly and the CCW matrix returns
   (−1.850, +5.625). Re-run with the correct matrix, a comparison of the two
   raw `.kicad_mod` files — **no board frame and no operator involved** — agrees
   with the landed table on **all seven** codes:

   | LCSC | rms 0 / 90 / 180 / 270 | best | separation | landed | |
   |---|---|---|---|---|---|
   | C189896 | 0.0000 / 2.5000 / 3.5355 / 2.5000 | 0 | exact | 0 | AGREE |
   | C265111 | 0.0050 / 4.0520 / 5.7304 / 4.0520 | 0 | 810x | 0 | AGREE |
   | C2683602 | 0.0049 / 5.0792 / 7.1831 / 5.0792 | 0 | 1037x | 0 | AGREE |
   | C157991 | 7.1276 / 5.0402 / 0.0566 / 5.0402 | 180 | 89x | 180 | AGREE |
   | C587657 | 2.7500 / 1.9526 / 0.2500 / 1.9526 | 180 | 8x | 180 | AGREE |
   | C125121 | 7.1366 / 10.0899 / 7.1366 / 0.2350 | 270 | 30x | 270 | AGREE |
   | C2887273 | 0.0300 / 3.7972 / 5.3700 / 3.7972 | 0 | 127x | 0 | AGREE |

   **Nothing in the CPL changes.** The shipped CPL was already correct on all
   seven. What changed is that a documented open disagreement is now closed, and
   closed by a method that shares no code with either operator (canon M1).

What remains is a narrower and sharper obligation.

**A-POL SINGLE-CHANNEL — 10 codes across 13 refs.** For these, the rotation was
fitted by pad NUMBER and **no numbering-free channel could corroborate it**,
because a dual-row SOIC/TSSOP/SSOP pad cloud is its own 180° reflection. A high
fit margin is not confidence: on another board this same fit returned 180° at a
17.7x margin and the true answer was 0°. The generated list ships as
`fab/rotation_human_gate.txt` — **that file is the checklist, and it is a list,
not a sentence**:

```
C10092: U_SR1              C2653162: U_TC        C6820:  U_SCHM
C133954: U_ONESHOT         C2653844: U_EFUSE     C7984:  U_COMP, U_COMP2
C16939: U_ADC              C506653:  U_EXP       C9683:  U_ULNA, U_ULNB
C5620: U_DECD, U_DECU
```

(C5158048 was on this list until its datasheet was read: the PESD5V0S1BA is
**bidirectional — both pins are cathodes** — so it has no orientation for a human
to confirm and it is excluded. Its five refs are D_DOOR, D_ESD_IN, D_ESTOP,
D_LCCLK, D_LCDAT. Note our footprint still draws a cathode band; that is a
cosmetic defect logged for v1.4, not an assembly risk.)

A human must confirm each item below in JLC's rendered assembly preview against
our silk/fab layers:

| # | Item | What to look at |
|---|---|---|
| 1 | **U_OPTO** (LTV-817S, C125121, SMDIP-4) | Pin-1 dot on the JLC render matches OUR silk pin-1 (LED side, west). **The three-way disagreement earlier revisions recorded here (name-DB 0 / twin 270 / independent fit 90) is RESOLVED:** the independent operator had a Y-axis frame error, and the operator-free re-fit gives **270 at 30x**, agreeing with the shipped CPL (§6 preamble). Check it anyway — this is the isolation part and the board's only 90/270-class rotation. A rotated opto swaps LED and transistor sides across the isolation barrier. |
| 2 | **J_DOOR** (JST-GH SM05B, C189896) | Mouth faces EAST (board edge); pin-1 position matches silk. |
| 3 | **J_ESTOP** (JST-GH SM05B, C189896) | Mouth EAST; pin 1 = 3V3 end per silk. |
| 4 | **J_MODE** (JST-GH SM05B, C189896) | Mouth EAST; pin-1 matches silk. |
| 5 | **J_RH_AMBIENT** (JST-GH SM05B, C189896) | Mouth SOUTH; pin-1 matches silk. |
| 6 | **J_RH_EXHAUST** (JST-GH SM05B, C189896) | Mouth SOUTH; pin-1 matches silk. |
| 7 | **J_THERM_A** (JST-GH SM08B, C265111) | Mouth SOUTH; pin-1 matches silk. |
| 8 | **J_THERM_B** (JST-GH SM08B, C265111) | Mouth SOUTH; pin-1 matches silk. |
| 9 | **J_KEY_MATRIX** (JST-GH SM10B, C2683602) | Mouth WEST (keypad ribbon); pin-1 matches silk. Formerly one of the three disputed codes; the dispute was **resolved 2026-07-26 in the authority table's favour** (offset 0, 1037x separation, operator-free file comparison — see the §6 preamble). Still on this gate, because a resolved dispute is a reason to look, not a reason to stop looking. |
| 10 | **J_PWR** (Molex Micro-Fit, C587657) | Polarizing peg orientation AND pin-1 (5 V) position vs silk. Suggested-180 measurement did not separate (2.9×) — the preview decides. |
| 11 | **J_LOADCELL** (JST-XH B5B-XH-A, C157991) | **WILL NOT APPEAR IN THE PREVIEW — it is off the CPL** (`exclude_from_pos_files`; one of the 37 excluded refs, see §3/§4). There is nothing to tick here at JLC. Confirm instead that the preview shows NOTHING placed at J_LOADCELL, and check pin-1 vs silk **on the bare board at hand-solder time**. |
| 12 | **CE1** (220 µF POLARIZED electrolytic, C2887273) | **v1.0 AND v1.1 shipped this cap at rotation 180 = REVERSED across a live 5 V rail.** Confirm the "+" / crescent on the render matches OUR pad 1 (west end, net 5V_PROTECTED). The measured `C2887273,0` row now governs and the export deliberately raises ROT-XCHECK-180 against the stale name-DB rule. Independent fit says 0 at 126.6×; "polarized part shipped reversed" is verbatim the usb-hub-3s-v3 v1.5 incident. |
| 13 | **J_PI** (2×20 socket, C35165) | **WILL NOT APPEAR IN THE PREVIEW — it is off the CPL** (same exclusion list). Carried from v1.1: JLC's library winds pin numbering by ROW where ours winds by COLUMN (adjudicated MIRRORED finding — symmetric hole grid, no physical mirror possible). Nothing to tick at JLC; pin-1 identity comes from our netlist + silk, not JLC's numbering, and is checked **on the bare board**. |
| 14 | **SOIC-16 — THREE parts, two codes** (**C5620 = U_DECD + U_DECU**; **C10092 = U_SR1**, SN74HC595DR) | Carried from v1.1: ROT-DB-SUGGEST 90° class — confirm pin-1 on **all three**. An earlier revision printed "U_DECU/U_DECD, C5620/C10092" as if both codes were the decoders; **C10092 is U_SR1**, which is separately on the A-POL single-channel list, so a reviewer following the old text would have skipped it. |
| 15 | **Diode cathode bands — the FIVE that have a cathode** (D_REVCLAMP, D_TVS, **D_KSTOP**, and the two ESD parts only insofar as they are seated square) | Band matches silk. **DO NOT "correct" D_ESD_IN, D_ESTOP, D_DOOR, D_LCCLK or D_LCDAT for band direction — they are PESD5V0S1BA, which is BIDIRECTIONAL: both pins are cathodes** (JLC's own model name ends `_BI`; see §13 gap 4). An earlier revision demanded "band matches silk on every one" for all eight, which invites a false-reject on five parts that have no polarity to get wrong. **D_KSTOP is the K_STOP coil flyback** (`.1 -> 5V_STOP`, `.2 -> COIL_STOP_N`): reversed it is a forward-biased short from the STOP rail into the coil driver and the STOP relay loses its clamp. It was missing from this list until 2026-07-26. **CORRECTED 2026-07-26 — why D_KSTOP (C8678) and D_TVS (C113974) are NOT in the A-POL list above but ARE here.** An earlier revision said these two "HAVE" a numbering-free channel and "carry `two-channel` rows". **That was false and this archive's own evidence contradicts it:** `verification/rotation_measurements_v13.txt` records both as `polarity=single-channel`, `NO usable numbering-free channel`, `ROW: (WITHHELD — single-channel)`, and `verification/twin_report.csv` marks C8678/D_KSTOP, C8678/D_REVCLAMP and C113974/D_TVS as **POLARITY-FIT-BLIND** — *"the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal."* No cathode-band shape measurement exists for either code. **They are absent from the generated A-POL list because the generated list is keyed to codes the twin could FIT and these three could not be fitted at all — which is worse, not better.** Counting them, the true single-channel population is **12 codes / 16 refs**, not the 10/13 the generated `fab/rotation_human_gate.txt` prints. **Treat THIS row as the only defence for these three refs.** |
| 16 | **The 10 SOT-23-6 gates** (U_AND1-3, U_CAND1-2, U_DECUEN, U_DECDEN, U_FAULTAND, U_LATCHG, U_OSCLR, C22046) | The measured C22046,180 rotation row must be in effect (v1.2 re-export proved exactly 10 changed cells, 270→180). Confirm pin-1 on at least U_AND1 in the preview. |
| 17 | **J_ISOLOOP** (KF350-3.5-4P, C42400616) | **Will NOT appear in the preview** — it is off the CPL and JLC has no CAD for the part. Confirm instead that the preview shows NOTHING placed at the south-east corner block, and that the 4 poles are bare. Wiring is a human job: §11 pole legend. |

## 7. BRING-UP ORDER — an ordered ritual, in THIS sequence

Pre-power (carried from v1.1, still binding):

1. **J_PWR pin-1 harness check (BRING-UP-CRITICAL):** multimeter the mating
   harness: pin 1 blade must beep to +5 V, pin 2 to RTN, peg orientation
   noted. The keyed housing prevents reverse MATING only — it cannot fix a
   mis-assumed pin-1 side.
2. Continuity: 5V_IN → F1 → 5V_FUSED → Q_REV → 5V_RPP → U_EFUSE →
   5V_PROTECTED.
3. **Isolation spot-check:** with relays UNPOPULATED, megger/DMM between any
   keypad net (J_KEY_MATRIX pin) and GND — must be open (the comb carries no
   galvanic path; only the reed contacts bridge domains).
4. Power at current-limited 5 V / 0.5 A; check 3V3 (U_LDO) and 3V3_ANALOG.
5. Pi host config before any arming (from `01_docs/pin_map.md`, verified
   against RP1 datasheet + kernel overlays):

   ```ini
   # /boot/firmware/config.txt — cooksense v1.2+ pin map
   dtparam=i2c_arm=on                 # I2C1 GPIO2/3  (MCP23017 0x20)
   dtoverlay=i2c2-pi5                 # I2C2 GPIO4/5  (cam A 0x33 + ambient SHT45 0x44)
   dtoverlay=i2c3-pi5,pins_14_15      # I2C3 GPIO14/15 (cam B 0x33 + exhaust SHT45 0x44)
   enable_uart=0                      # GPIO14/15 default to UART0 — console MUST stay off
   dtparam=i2c_arm_baudrate=100000
   ```
   Also remove `console=serial0,...` from cmdline.txt.

**The arming ritual. Four steps, in this exact order — each step proves one
AND-chain input while the later inputs are still held safe by their
pull-downs:**

1. **HEARTBEAT.** Start the host heartbeat toggling WD_PET (GPIO17, phys
   pin 11 → TPS3823 WDI through the 1 k R_WDPETPD).
   *Proves:* host software owns the pet pin and can drive it against the 1 k
   hold-down (≈3.3 mA while high — that current is a safety property, see the
   TPS3823 dossier; do NOT "normalise" R_WDPETPD to 100 k, a 100 k hold lets
   the supervisor pet ITSELF and silently disables the watchdog).
   *Failure means:* wrong GPIO, config, or drive strength — nothing downstream
   can be trusted yet.
2. **TP_WDOK steady > 2.5 s.** Watch TP_WDOK with the heartbeat running: it
   must come up and stay steady for longer than **2.5 s = the TPS3823 maximum
   watchdog timeout** (t_WD 0.9 / 1.6 / 2.5 s min/typ/max, datasheet §6.8).
   Steady beyond the max timeout proves the watchdog is being GENUINELY petted,
   not coasting. Then run the negative test: set the heartbeat GPIO to input —
   **WD must bite (TP_WDOK drop / RESET assert) within 2.5 s.**
   *Failure means:* if TP_WDOK never comes up, the pet edge is not reaching
   WDI; if TP_WDOK stays high with the heartbeat STOPPED, the watchdog is
   self-petting (the R_WDPETPD-value defect) — **STOP, the board's primary
   runaway backstop does not exist.**
3. **REARM_N.** Pulse REARM_N low (MCP23017 U_EXP output; R_REARMPU pull-UP,
   so a floating expander cannot clear the latch) to clear the hardware fault
   latch.
   *Proves:* every latch SET input is clear — WD_OK (step 2), ESTOP_OK
   (E-stop loop closed), TEMP_OK (both NTCs connected and cool; note the v1.3
   open-detect means an UNPLUGGED thermistor harness is a latched fault BY
   DESIGN).
   *Failure means:* one SET input is still faulted — read TP_ESTOP, TP_TEMPOK,
   TP_FAULT to find which; do not proceed by jumpering anything.
4. **HOST_AUTH.** Drive HOST_AUTH high (GPIO22, phys pin 15; 100 k pull-down —
   the default is unauthorized). This is the last AND-chain input:
   KEY_RELAY_ALLOWED (TP_ALLOW) must go true and the coil rail becomes
   available.
   *Proves:* the full 7-condition chain end-to-end.
   *Failure means:* with steps 1–3 green the fault is isolated to the AND
   chain itself (the ten §6-item-16 gates) or MCU_RELAY_ENABLE — check
   TP_ALLOW and TP_RKEY.

First-use functional checks (after the ritual, folded from v1.1):

- **J_TC thermocouple polarity:** dip the probe in a known reference (ice
  water / boiling water) — a REVERSED junction reads an inverted delta from
  ambient: obvious and harmless. Swap at the MAX31856 inputs if needed.
- **KEY_RESET_N floats during Pi boot** — R_OE holds the 595 outputs disabled;
  no relay can fire until the Pi drives the interface. Observe on first boot.
- **Door input direction (§2a):** with the door harness unplugged the board
  must read DOOR-OPEN (non-permissive). If it reads closed, the harness or the
  pull is wrong — stop.

## 8. ⚠️ RELAY-COUPLING BENCH MEASUREMENT (carried from v1.1 — licenses any future denser repack)

This board places the reeds at the **15.24 mm coupling-vetted pitch in the
rot0 orientation the figure came from, with anti-parallel adjacent coils**
(the datasheet's own alternate-orientation mitigation). To license any FUTURE
revision below 15.24 mm pitch or a two-row repack, measure ON THIS BOARD:
- Energize a **U + D + PRESS triple** (worst-case simultaneous neighbours,
  e.g. K_U6 + K_D1 + K_PRESS via the decoder/one-shot paths).
- For the relay ADJACENT to each energized one, sweep its coil voltage and
  record the **operate (pull-in) voltage shift** vs the datasheet 3.5 V max in
  isolation, both coil polarities.
- A shift < 10% of the 1.5 V worst-case margin (operate stays ≤ 3.65 V) is a
  CLEAN result → record it in 01_docs/decisions/ as the coupling evidence.
  Any larger shift: keep ≥ 15.24 mm forever and note the -12M/Q/R/S
  magnetic-shield variants as the fallback for denser layouts.

## 9. Pi interconnect (J_PI — ribbon SIDECAR, NOT a direct stack)

- Use a 40-way ribbon with a **MALE DIL-IDC transition plug at the board end**
  — standard Pi ribbons are FEMALE-FEMALE and cannot mate this board's socket.
- The socket is UNSHROUDED: mark pin 1 on both ribbon ends and observe strict
  pin-1 keying discipline at every mating.
- The socket's stack tails protrude ~12 mm below the board — trim them or fit
  standoffs of at least that height.

## 10. Harness labeling discipline (unkeyed 5-pin GH family)

J_MODE / J_DOOR / J_ESTOP share the same unkeyed 5-pin JST-GH housing and a
common 3V3(1)/GND(5) convention. Pinouts are arranged so any single cross-plug
is fail-safe, **and v1.3 removed the worst cross-plug consequence**: J_ESTOP
is now SELV-ONLY (pins 3/4 are GND — see §11), so a cross-plugged harness can
no longer close the contactor loop through GND. The discipline stands anyway:
**label every harness at both ends and match labels before power** — a
cross-plug still swaps safety inputs, and the §2a door-short residual is a
harness-quality failure.

## 11. ⚠️ THE ISOLATED LOOP — ONE CONNECTOR, `J_ISOLOOP`, AND ITS POLE LEGEND

**Any v1.0/v1.1 statement that "J_ESTOP pins 3/4 carry the contactor loop" is
WRONG, and so is any earlier v1.3 text naming `J_ESTOPLOOP` or `J_CONTACTOR` —
neither connector exists.** J_ESTOP pins 3/4 are GND and that housing is
SELV-only. The opto-isolated loop left the SELV connector because ESTOP_RAW and
CONTACTOR_C sat 0.650 mm apart on 1.25 mm pitch in ONE field harness, making a
single damaged harness a common-cause failure across the isolation boundary.

The whole isolated domain now lands on **ONE** 4-pole 3.5 mm screw terminal,
`J_ISOLOOP` (KF350-3.5-4P, south-east corner, mouth EAST). Merging the two
2-pole blocks is isolation-neutral-or-better: both only ever carried
isolated-domain nets, so this is one isolated body with one 2.0 mm moat and one
pour keepout to defend instead of two adjacent bodies each needing their own.

### THE POLE LEGEND — THIS IS THE GATE

`J_ISOLOOP` is hand-soldered and OFF the CPL, so there is no machine rotation to
get wrong. **The entire risk is a person landing four wires.** Pole 1 is the
SOUTH-most pole (the square pad); wiring runs SOUTH to NORTH.

| pole | board net | function | board Y |
|---|---|---|---|
| **1** | CONTACTOR_C | opto collector out -> E-stop pole B **in** | 100.250 |
| **2** | CONTACTOR_LOOP | E-stop pole B **out** (return) | 96.750 |
| **3** | CONTACTOR_LOOP | -> contactor circuit | 93.250 |
| **4** | CONTACTOR_E | contactor circuit return -> opto emitter | 89.750 |

External loop, in order: `1 -> E-stop dry pole B -> 2`, then `3 -> contactor
permission circuit -> 4`.

**Poles 2 and 3 are ONE board net on TWO screws, deliberately.** On a safety
interlock a single loosening screw must not be able to drop both the E-stop
return and the contactor feed. Do not "tidy" this by landing both wires in one
screw — that reintroduces the single point of failure the two screws exist to
remove. Asserted in `electrical_invariants.yaml` (`J_ISOLOOP.3 -> CONTACTOR_LOOP`).

Silk reads `J_ISOLOOP (SE CORNER) = ISOLATED 30V CONTACTOR LOOP -- NOT SELV` in
the north caption band. It is deliberately NOT beside the block: a scan for a
free silkscreen box against pads, existing silk and every courtyard found no
site within 41.9 mm, and the caption in fact ended up **155.3 mm** from the
block — at (62.000, 15.400) against J_ISOLOOP at (195.300, 95.000), diagonally
opposite. **Within 25 mm of the block the ONLY J_ISOLOOP silk is its outline box
and the refdes at (189.300, 101.000). Use this legend, not the board, to
identify the poles** — the one physical cue at the block is that **pole 1 is the
only RECTANGULAR pad**; poles 2, 3 and 4 are round.

> **⚠️ THE LOOP IS POLARISED. POLE 1 IS POSITIVE. It is NOT a dry contact.**
> `CONTACTOR_C = [J_ISOLOOP.1, U_OPTO.4]` is the phototransistor **COLLECTOR**;
> `CONTACTOR_E = [J_ISOLOOP.4, U_OPTO.3]` is its **EMITTER**. Earlier revisions
> of this section called the output a "DRY CONTACT" — language that means
> polarity-free, and it is wrong. **Current must flow IN at pole 1 and OUT at
> pole 4.** Wired backwards the loop simply never conducts (contactor never
> closes — discovered after the harness is built), and a reversed **30 V** sits
> across an emitter-collector junction rated about **6 V**, an order of
> magnitude over. A phototransistor that fails from reverse breakdown fails
> **SHORT**, and short is the **PERMISSIVE** state. Forward, the part is safe by
> a wide margin: even at the CTR 600 % bin ceiling I_C self-limits to
> 600 % x 6.364 mA = **38.2 mA**, under the 50 mA absolute maximum.
>
> **⚠️ POLES 2 AND 3 ARE THE SAME NET — AND THAT MEANS A SPECIFIC WIRING
> MISTAKE IS SILENT.** `CONTACTOR_LOOP = [J_ISOLOOP.2, J_ISOLOOP.3]`: two screws
> on one node, deliberately, so the loop passes through the field device in
> series (2 → device → 3). **If you land BOTH wires of that device on poles 2
> and 3 in the wrong sense — or bridge 2 to 3 — you SHORT the device out of the
> loop and the loop still reads CLOSED.** For the E-stop that is a **permissive**
> failure: the interlock reports healthy with the E-stop electrically absent.
> Nothing on the board can detect it. Verify continuity through the device
> between poles 2 and 3 with the device OPEN before energising: an open device
> must read OPEN across 2-3.

**Rating — CORRECTED, and the old number was the dangerous half of the pair.**
The loop is the LTV-817S opto DRY CONTACT. Earlier revisions of this section
printed only "**<= 30 V / <= 50 mA**". That is the **ABSOLUTE MAXIMUM** — a
do-not-exceed limit — and quoting it alone invites an integrator to design a
loop that draws tens of milliamps. **The current this loop can actually SINK is
15x smaller and is set by the LED drive, not by the collector rating:**

| quantity | value | where it comes from |
|---|---|---|
| LED drive rail | 3.3 V | `CONTACTOR_DRV`, `U_CAND2.4`, 3V3 CMOS |
| series resistor | **330 Ω** | `R_OPTOLED`, LCSC **C23138**, measured off the shipped board and BOM |
| LED forward drop | ~1.2 V | LTV-817S V_F at a few mA |
| **I_F** | **(3.3 − 1.2)/330 = 6.36 mA** | |
| CTR, **worst-case bin minimum** | **50 %** | `02_parts/LTV-817S-TA1/part.yaml` `limits.ctr: "50-600% (TA1 bin)"` |
| **I_C GUARANTEED** | **6.36 × 0.50 = 3.18 mA** | |

**DESIGN THE FIELD LOOP TO NEED <= 3.0 mA, not 50 mA.** A loop built to the
50 mA figure — a relay coil, a long line with a low-value pull-up, an input with
a milliamp-class threshold — will read as *permanently open* on a worst-case-CTR
device, and the contactor will simply never close. The failure is in the safe
direction, but it presents at commissioning after the harness is built.

**V_CEO is 35 V against a 30 V working loop — 17 % margin, and there is no
clamp.** `CONTACTOR_C`/`CONTACTOR_E` carry no snubber or TVS on this board.
**The field loop MUST be non-inductive, or you must snub it at the load.** An
unclamped inductive kick past 35 V fails a phototransistor SHORT, and a shorted
opto output is the **PERMISSIVE** state — it asserts the interlock the board
exists to withhold. This is the one failure mode in the isolated domain that is
not fail-safe; the board cannot defend against it, so the harness must.

Do not repurpose this loop to switch a contactor coil directly. The
nets carry the ISO_CONTACTOR netclass and the `opto_isolation_2mm` DRU rule
(IEC 60664-1 basic insulation, 30 V working, pollution degree 3, material group
IIIa), which is **GREEN on v1.3 routed copper**. Minimum over ALL copper on ALL
layers (pads, tracks and filled pours) is **2.0000 mm** — **method: true-polygon
copper clearance, all four layers, filled pours included** — at CONTACTOR_C on
`J_ISOLOOP.1` against the **GND zone edge**, and it is 2.0000 mm on each of
F.Cu / In1.Cu / In2.Cu / B.Cu independently — margin 0.000 mm by
construction, because the pour keepout IS the 2.0 mm offset. Pad-to-pad only,
the minimum is 2.1709 mm (`U_OPTO.3` <-> `J_RH_EXHAUST.5`, true polygon
distance). v1.2 measured 0.199 mm at this rule.

## 12. ⚠️ R_OPENT IS 62 kOhm — ORDER C37825, NOT C25915

The open-thermistor detect threshold divider is `3V3_ANALOG -> R_OPENT ->
TCAM_OPEN -> R_OPENB (100 kOhm) -> GND`. Its job is that an open, broken or
unplugged thermistor reads **OVER-TEMP**, not "fine".

**v1.3 was first coded with the wrong part and it was caught before release.**
The row carried **C25915, which is 6.2 kOhm** — one decade low. Verified twice,
from the catalog rather than by decoding a part number: JLC
`selectSmtComponentList` returns MPN `0402WGF6201TCE`, describe "6.2kOhm"; the
LCSC product page for C25915 says the same.

| | R_OPENT | TCAM_OPEN threshold |
|---|---|---|
| design intent | 62 kOhm | **2.0370 V** |
| C25915 as first coded | 6.2 kOhm | **3.1073 V** |

At 6.2 kOhm an open head reads 2.2687 V — *below* the 3.1073 V threshold — so
the comparator never trips. 3.1073 V is also above the LMV393's 2.500 V
common-mode ceiling, so the input sits outside its guaranteed range. The tsx
comment block above these resistors already documented 3.107 V as the REJECTED
first cut, so the wrong code silently reinstated the exact defect the v1.3
second pass exists to remove.

**Root cause, and it is the transferable one.** R_OPENT carried no pinned LCSC,
so the part was coded by an automatic picker, and **all three** of its candidates
for "62k" are 6.2 kOhm (`C25915` 0402WGF6201TCE, `C137946` RC0402FR-07**6K2**L,
`C2909371` FRC0402F**6201**TS) — it reads "62k" as RKM "6k2". The same picker
returned three candidates for "510k" that were all 390 kOhm on R_OS, and put
`R_WDPETPD` on a 100 kOhm line where the design needs 1 kOhm. **That is three
times on this board alone.** The other three resistors in this divider were correct only because of
the order the candidate list happened to come back in, **which is not the same
as being right** — so all four are now pinned explicitly and catalog-verified:

| ref | value | LCSC |
|---|---|---|
| R_OPENT | 62 kOhm | **C37825** |
| R_OPENB | 100 kOhm | C25741 |
| R_CLMPA, R_CLMPB | 22 kOhm | C25768 |

**Order-day checks — BOTH of them, on the BOM you upload:**

| ref | must read | if it reads | consequence |
|---|---|---|---|
| `R_OPENT` | **C37825** (62 kΩ) | C25915 (6.2 kΩ) | open-thermistor detect does not exist |
| `R_WDPETPD` | **C11702** (1 kΩ) | C25741 (100 kΩ) | **watchdog silently disabled** |

Either one reading wrong: **STOP.** Both are wrong-decade substitutions from the
same automatic picker, and neither is visible in the board, the netlist, the CPL
or any geometry check.

**Generalise it:** a coded passive with no pinned LCSC is resolved by a picker
that has now twice returned a wrong decade. Any value-authored passive whose
value matters — a threshold, a timing constant, a current limit — should carry
its code explicitly and be listed in `lcsc_passives_ledger.yaml` so
`bom_source_check` leg C can verify it offline forever.

## 13. VERIFICATION STATUS AND DECLARED GAPS

Everything below is a measured number, including the gaps. A gap that has been
counted is a finding; a gap nobody counted is how things drift.

| gate | result |
|---|---|
| DRC (`--severity-all --refill-zones --schematic-parity`) | **0 / 0 / 0** — see the qualifier immediately below; **9 checks are set to `ignore`** |
| P-COLLIDE (placement) | 0 pad shorts, 0 anchored courtyard overlaps |
| E-INV | **83 / 83** |
| A-ROT | 189 / 189 CPL rotations from measured rows |
| A-POS | 189 / 189 CPL rows on the pad-centre datum, worst 0.0000 mm |
| A-POL | **10 codes / 13 refs GENERATED; TRUE population 12 codes / 16 refs** -> §6 human gate item 15. The three extra refs (D_KSTOP, D_REVCLAMP on C8678; D_TVS on C113974) are `POLARITY-FIT-BLIND` in `twin_report.csv` — the twin could not fit them at all, so they never reached the generated list |
| I-HW (mounting-hardware creepage) | **FAIL at H4: 4.0286 mm vs 6.000 required** (straight line, notch not credited — see the §1 ruling). H1 13.6299 / H2 13.1525 / H3 40.9324 all PASS, all straight-line and crossing no void |
| ISO barrier (`opto_isolation_2mm`) | **2.0000 mm**, all copper all layers incl. filled pours (GND zone edge at J_ISOLOOP.1). Pad-to-pad true polygon: 2.1709 mm. Margin 0.000 by construction — the moat keepout IS the 2.0 mm offset. |
| M-REPRO | 3 from-source rebuilds, **1047** vias each, identical fp/track/via hashes, matching the shipped board |
| Stranded pour islands | **121 islands** on the fill THAT SHIPS (GND F.Cu 106, GND B.Cu 13, GND In1.Cu 1, 3V3 In2.Cu 1), **121 bonded, 0 stranded**. The 136 printed in earlier revisions came from a refill-in-memory, not from the stored fill — same conclusion, wrong population. |
| jlc_twin | 420 rows: 184 OK, 184 MODEL-REG-OK, 31 PAD-GEOM, 9 POLARITY-CHECK, **6 POLARITY-FIT-OK, 3 POLARITY-FIT-BLIND**, 1 MIRRORED, 1 FETCH-FAILED, 1 NO-BODY — **all adjudicated**. Earlier revisions collapsed the two POLARITY-FIT classes into one "9 POLARITY-FIT", which hid the **3 BLIND** rows (C8678/D_KSTOP, C8678/D_REVCLAMP, C113974/D_TVS) — the ones with no numbering-free channel at all. They are §6 item 15. |
| contracts_audit | 189 files, 0 violations |

### ⚠️ THE DRC CLAIM HAS A QUALIFIER — nine checks are OFF

`0/0/0 at --severity-all` is true and **incomplete**. `source/cooksense.kicad_pro`
sets these nine to `ignore`, so `--severity-all` never reports them:

```
silk_overlap        silk_over_copper     silk_edge_clearance    text_thickness
missing_courtyard   footprint_filters_mismatch   footprint_type_mismatch
track_not_centered_on_via   tuning_profile_track_geometries
```

**MEASURED with the four SILK checks turned back on** (extract `source/` to a
bare directory, set them to `warning`, re-run): **78 violations** —
`silk_over_copper` 49, `text_thickness` 24, `silk_edge_clearance` 3,
`silk_overlap` 2. They are off as documented fleet policy (silk is resolved at
fab silk-finalisation), and they remain off for v1.3.

**Why you should care anyway:** this board's ADR-0012 safety warnings are on
silk, and §6's human gate asks you to compare the JLC render against our silk.
**Silk legibility is therefore UNGATED on a board that depends on it twice.**
Judge the silk visually from `pdf/assembly.pdf` and
`verification/render_top_bare.png` before ordering, and treat the §6 gate as the
place where silk quality actually gets checked.

### Declared gaps — known, bounded, and NOT fixed in v1.3

1. **P-FACT coverage is 4 of 41 part.yaml.** Only four dossiers declare an
   executable `asserts:` block (the twelve reeds, J_TC, CE1, U_OPTO). The other
   37 carry their facts as prose that no gate reads. Backfilling all 41 is a
   fleet campaign, not a board task; the four chosen are the ones where an
   assert would have caught a defect that actually shipped.
2. **`keepout_region` is declared but ungradeable.** U_OPTO's 5000 Vrms barrier
   is asserted in its part.yaml, and P-FACT reports it DEFERRED because the
   checker cannot yet read board geometry. The barrier is held by three other
   mechanisms (`opto_barrier` 4-layer keepout, the `opto_isolation_2mm` DRU
   rule — **and the metric belongs beside the number**: all-copper-all-layers
   minimum **2.0000 mm** (the binding figure), pad-to-pad true polygon 2.1709 mm,
   pad-to-pad bounding-box 2.126 mm. Earlier revisions quoted only the 2.126
   bounding-box figure here, the loosest of the three, inside a safety
   justification — and the land's own 7.530 mm clear strip).
3. **P-FACT has no kind for "off the CPL but on the BOM as a buy-line."**
   Three of the 16 self-supplied refs (J_ISOLOOP, J_LOADCELL, J_PI) are
   deliberately coded on the BOM and excluded from the CPL. The nearest assert,
   `not_on_assembly_bom`, conflates "not placed" with "not purchased".
4. **Our SOD-323 land draws a cathode band on a bidirectional part** (D_DOOR,
   D_ESD_IN, D_ESTOP, D_LCCLK, D_LCDAT). Assembly risk is nil — JLC places from
   the CPL, not our silk — but a reviewer hand-checking the board may "correct"
   a placement that was already right. v1.4.
5. **CLOSED, not deferred — the CH0/CH3 transfer function is now derived in
   §2b.** The 22 k clamps put CH0 and CH3 on a different divider from the other
   six channels. This was a declared gap until 2026-07-26; it is now arithmetic
   in §2b with the corrected inversion, an 8-point error table and recomputed
   accept/reject thresholds. Recorded here because the reason it could not stay
   a gap is general: §2b is a **MANDATORY acceptance test**, and a mandatory
   procedure specified against a knowingly wrong curve is worse than no
   procedure — whoever runs it fails a good board or passes a bad one and trusts
   the result either way. The sharp case: an open NTC reads 8.4 °C under the
   naive model, so acceptance test (a) would have passed a board on which the
   host detects nothing.
6. **The open-detect comparator has no hysteresis (`R_HYS` is negative feedback
   on U_COMP2).** `TH_CAM_A` is one node feeding U_COMP's IN+ and U_COMP2's IN−,
   so a single 1 M resistor cannot be positive feedback for both. A real open
   still latches solidly (the node moves 15.5 mV against 232 mV of overdrive);
   the exposure is chatter at the −10.4 °C nuisance boundary, and the direction
   is **lockout, not permissive**. Fixing it needs a new part that re-specs the
   threshold to ~2.0836 V. v1.4.
7. **The thermistor sense nets are ~12× their declared length budget.**
   `TH_CAM_A` routes **93.62 mm** and `TH_CAM_B` **87.75 mm** against a declared
   `keep_short max_span_mm: 8` in the LMV393 dossier; closest same-layer
   aggressor is `SPI_SCLK` at **0.206 mm**. Direction is fail-safe (a glitch
   drives TEMP_OK low → latched lockout). Needs re-placement; v1.4. Note the
   budget was never enforced — `audit_board`'s I-PROX has no span check.
8. **The digital twin does not cover 2 of the 54 coded BOM lines.** MEASURED,
   by comparing `fab/bom_jlc.csv` against `verification/twin_report.csv`:
   52 of 54 coded lines were twin-checked; the two that were not are
   **C25768** (`R_CLMPA`, `R_CLMPB` — the 22 kΩ sense bleed) and **C37825**
   (`R_OPENT` — the 62 kΩ open-detect threshold). Both entered the BOM after the
   twin run: C37825 in the R_OPENT decade fix, C25768 when the divider was
   pinned. Their JLC land pattern and 3D body were never compared against ours.
   (Lens A estimated six affected parts by REFDES; by CODE the true figure is
   two, because R_OPENB, C_COMP2 and R_DOORPD share already-checked codes. The
   measured number is the one that belongs here.)
   Not a blocker: both are 0402 chip passives on the `R_0402_1005Metric` land
   class the twin checked 30+ times on this board, both resolve from measured
   A-ROT rows, and both catalog values match their tsx value props under the
   circuit-only check. But it IS a gap, and the twin's whole value is that it
   does not assume — so it is declared rather than rounded away.
9. **The narrative pin and render reviews were NOT re-run for v1.3.** Their
   MACHINE halves are current and ship: 74 pin_audit dossiers regenerated from
   this board, `audit_board` I-POL 18/18, P-FACT `pad1_net_polarity` executing on
   CE1, schematic-parity 0, E-INV 83/83, and renders regenerated from this
   board. Their NARRATIVE halves — a human-equivalent reading of every pin map
   and of the silk — were last run at v1.0/v1.2 and are **not** reproduced;
   `pin_review.md` and `render_review.md` each say so in their first paragraph.
   **What covers the gap instead:** this board has had **four independent
   reviews since**, two adversarial red-team lenses (topology and layout) and
   two zero-context cold lenses over the frozen archive, whose findings are in
   `redteam_topology.md`, `redteam_layout.md`, `fresh_lens.md` and
   `dispositions.md`. That is different from "nobody looked", and it is also
   different from a completed narrative pin review. If your process requires the
   latter, this release does not provide it.
10. **The 61-row rotation authority table is NOT in this archive.** A-ROT is
   green and no row fell back to the name-keyed DB, but the table it resolves
   against lives in the fleet repo. What ships here is
   `verification/rotation_measurements_v13.txt`: the **15** rows measured for
   this revision, covering **26 of 189** CPL rows across 15 of the 51 distinct
   LCSC codes. For the remaining 36 codes a reader holding only this archive is
   trusting a document they cannot open. Partially offset by the operator-free
   re-measurement of seven codes recorded in
   `verification/rotation_C22046_measurement.md` (all seven agree with the
   table, including U_OPTO and CE1), and by §6, which puts every rotation-risky
   part in front of a human at the JLC preview. **Shipping the resolved 189-row
   provenance list as an artifact is the v1.4 fix.**
11. **`verification/parity.md` in this archive reads `REAL DISCREPANCIES: 1 ->
   FAIL`, and here is what that one is.** It is **`J_KEY_MATRIX` pad `MP`** —
   the two mechanical solder tabs on the 10-pin keypad connector.
   `source/parity_padmap.txt` line 14 declares a board-stage bond
   `SM10B-GHS-TB MP GND_ISO`; **on the shipped board those two pads carry NO
   NET.** Every other connector's tabs ARE bonded (J_DOOR, J_ESTOP, J_MODE,
   J_RH_AMBIENT, J_RH_EXHAUST, J_THERM_A, J_THERM_B, J_PWR — all `GND`,
   measured). J_KEY_MATRIX alone was missed.

   **MEASURED CONSEQUENCE — it is NOT an isolation defect, and the measurement
   is the reason to believe that rather than the argument:**

   | path | measured | requirement |
   |---|---|---|
   | path | measured | method | requirement |
   |---|---|---|---|
   | KEYPAD_ISO → all other netted copper (the rule as written) | **6.1200 mm** | true polygon, copper clearance, all four layers incl. filled pours; **not creepage — see the blind-spot note below** | >= 6.000 |
   | floating MP → KEYPAD_ISO copper | 0.5810 mm | true polygon, copper clearance | — |
   | floating MP → all other netted copper | **13.3151 mm** | true polygon, copper clearance | — |
   | **two-hop KEYPAD_ISO → floating MP → other** | **13.8960 mm** | sum of the two hops above | >= 6.000 |

   A floating conductor inside a barrier is only dangerous when it *splits* the
   gap; this one sits **0.581 mm** from the keypad domain and **13.315 mm** from
   everything else, so it is electrically part of the keypad side and adds
   nothing to any leakage path. What is actually lost is the **ESD/shield drain
   for that connector's shell** — the tabs float instead of returning to
   `GND_ISO`.

   **THE FLOATING TAB IS CORRECT AND MUST STAY FLOATING. Do not "fix" it.**
   An earlier revision of this item called for bonding it to `GND_ISO` in v1.4.
   **That instruction was wrong twice over and is retracted:**

   - **`GND_ISO` DOES NOT EXIST.** Measured: 0 occurrences in
     `source/cooksense.net` and 0 in `source/cooksense.kicad_sch`. The only
     ground net on this board is `GND`. The name survives in exactly two places,
     both of which are now known defects: `source/parity_padmap.txt` line 14,
     and the F.Silkscreen caption at (106.000, 21.000) reading
     "KEYPAD ISOLATION COMB >=6mm creepage **GND_ISO ONLY**". **Both name a net
     that was never created.**
   - **Bonding the tab to the ground that DOES exist would BREAK the barrier.**
     The tab sits **0.5810 mm** from KEYPAD_ISO copper. Put `GND` on it and
     `keypad_isolation_6mm` fires at 0.581 mm against a 6.000 mm requirement —
     **a 10.3x violation**, and the worst one on the board. The tab is floating
     *because* there is nowhere safe to land it.

   **What is actually true:** the keypad connector's shell has no ESD drain, and
   it cannot have one until an isolated ground net exists. That is an
   isolation-topology change, not a re-route. **v1.4 items:** (a) delete the
   `GND_ISO` token from `parity_padmap.txt` and from the silk caption, or create
   the net properly; (b) drop the `B.NetName != ''` clause from the barrier
   rules so floating copper is in scope.

   **Why no gate caught the naming defect:** that trailing `B.NetName != ''`
   **exempts unnetted copper by construction** — DRC is structurally unable to
   see a floating pad, so `0 violations` was never evidence about it. The
   converter-parity check DID see it and said FAIL; the artifact shipped and
   nothing read it until the fifth review.
12. **Silkscreen: the safety captions are 0.60 mm character height, and NOTHING
   IN THIS ARCHIVE CHECKS TEXT HEIGHT AGAINST A FAB FLOOR.** Every gate that
   looked at silk checked **stroke width** (0.150 mm, exactly on JLCPCB's 0.15 mm
   floor). JLCPCB publishes a minimum silkscreen **character height** of about
   **1 mm**; all seven ADR-0012 safety captions are **0.60 mm**. They may print
   thin, broken or not at all. **The captions are a backup to this document, not
   the other way round — treat ORDER_README §11 and §1 as the authority for
   field wiring and enclosure, and inspect the first article's silk before
   assuming any board-level warning is legible.** Related, and previously
   undisclosed: **both** J_ISOLOOP silk features are inside the 78 ignored silk
   violations — its refdes at (189.300, 101.000) is one of the 24
   `text_thickness` items (0.45 mm height / 0.150 mm stroke), and its outline box
   is **all three** `silk_edge_clearance` items. The earlier disclosure said
   "zero of the 78 involve a safety caption", which is true and was verified, but
   it never checked the two silk features on the isolated 30 V block itself.
13. **The gerbers were plotted WITH drill marks; a default `kicad-cli pcb export
   gerbers` does not reproduce them byte-for-byte.** F.Cu/In1/In2/B.Cu each carry
   1047 extra 0.150 mm and 105 extra 0.350 mm dark flashes, and F.Mask/B.Mask 105
   extra 0.350 mm openings. Every mark was verified concentric inside an existing
   via pad, PTH pad or NPTH hole, so all are inert — but a reviewer re-exporting
   to compare must enable drill marks or they will see thousands of spurious
   differences.
14. **Documents this archive CITES but does not CONTAIN.** ADR-0001, ADR-0006,
   ADR-0012, ADR-0013, `BRIEF.md`, `01_docs/pin_map.md`,
   `02_parts/LTV-817S-TA1/part.yaml` (the CTR 50 % bin the whole §11 current
   budget rests on), `electrical_invariants.yaml` (the assert §11 cites as the
   two-screw guarantee), `floorplan.yaml`, and the `SUPERSEDED.md` files of the
   earlier releases. Individually minor; **collectively, several load-bearing
   safety numbers cannot be re-checked from inside this archive.** v1.4 should
   ship the cited ADRs and part.yaml files.
15. **THE DRC GATE CANNOT SEE CREEPAGE AT ALL, AND THAT IS WHY H4 SHIPPED GREEN
   THROUGH SEVEN REVIEWS.** `keypad_isolation_6mm` is a **DRU rule measuring
   copper-to-copper CLEARANCE**. Creepage is a **surface path**, and whether a
   slot interrupts that path is a question about board outline and pollution
   degree that a clearance rule has no way to express. So DRC returned
   **0 violations** on a board whose keypad-to-SELV creepage at H4 is
   **4.0286 mm against 6.000 mm required** — and the 0/0/0 was never evidence
   about this property. The `I-HW` gate, which does model the fastener, computed
   a **geodesic around the notch** and so encoded the wrong physics rather than
   no physics.

   **This is the same family as the two blind spots already recorded in this
   release:** `A-EVID` could not see a required artifact that was absent because
   the check was keyed to what was present, and the `row_kind` blind spot graded
   a field the generator never populated. **The pattern is a gate whose
   measurement is not the property.** A gate that cannot fail on a property is
   not evidence about that property, however green it reads.

   **v1.4 gate work, independent of the geometry fix:** teach `I-HW` the
   pollution-degree X-dimension so a groove narrower than X is bridged rather
   than walked around, and make it report **both** figures with their methods
   named. Until then, no creepage number on this board should be read without
   the method beside it.
16. **M-REPRO is green by metric, not by bytes.** Three from-source rebuilds are
   geometrically identical, but the files differ because the generator mints
   fresh UUIDs and KiCad serialises footprints in UUID order. A fleet-level fix
   is owned elsewhere; on this board the nondeterminism never reaches a via
   decision (via count has not varied across 5 observed builds).
