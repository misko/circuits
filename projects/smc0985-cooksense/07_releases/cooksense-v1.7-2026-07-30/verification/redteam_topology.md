# cooksense v1.7 — ZERO-CONTEXT ADVERSARIAL RED TEAM, RE-GATE 4
## Lens: TOPOLOGY / PROTECTION / RATINGS. Subject: the 65 °C declaration.

```
design_verdict: SOUND
order_verdict:  BLOCKED-SOURCING
```

**P0 count: 0.**

Reviewer: zero-context, no stake. Inputs read: the staging archive at
`06_build/staging/cooksense-v1.7/` (excluding the four opinion files I was
fenced from), `01_docs/BRIEF.md`, `01_docs/ARCHITECTURE.md`,
`01_docs/decisions/`, `02_parts/`, `03_src/cooksense/rules/`, and the committed
vendor PDFs in `02_parts/`. I did not read `08_reviews/`, the journal, the
learnings, `STATUS-*`, `DISPOSITIONS.md`, `owed_skill_patches.md`, or any
`*redteam*` / `*pin-review*` / `*render-review*` file.

---

## 1. Gates I ran myself, unpiped, with raw exit codes

| gate | command | result | RAW EXIT |
|---|---|---|---|
| DRC (both halves) | `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity --exit-code-violations --format json` on `06_build/staging/cooksense-v1.7/source/cooksense.kicad_pcb` | `Found 0 violations` / `Found 0 unconnected items` / `Found 0 schematic parity issues` | **0** |
| E-TOPO | `power_topology.py projects/smc0985-cooksense --power-tree 03_src/cooksense/rules/power_tree.yaml` | `E-TOPO OK: 1/1 rail(s) topology-correct` — headroom 1329 mV vs dropout 1300; PD 410 mW vs 497 (82 %) | **0** |
| E-MARGIN | same, `--margin` | `E-MARGIN N-A: no rail declares load_uv_threshold` | **0** |
| E-OFF | same, `--off-control` | `E-OFF N-A: no self-contained energy source (source_type: external_5v_selv)` | **0** |
| E-INV | `electrical_invariants.py --netlist … --invariants 03_src/cooksense/rules/electrical_invariants.yaml` | `E-INV OK: 168/168 invariants hold` | **0** |

**DRC is classified, not counted, and BOTH halves are zero.** `--exit-code-violations`
was passed, so exit 0 is a load-bearing zero and not the default-0 trap.
There is nothing to classify: no violation class, no unconnected class, no
parity class. MEASURED by me.

Board identity MEASURED by me: `md5 9f4fd5fae810f40a52b1035df727243c` on both
`06_build/staging/cooksense-v1.7/source/cooksense.kicad_pcb` and
`04_kicad/cooksense.kicad_pcb`. The claim that copper is unchanged holds.

**INHERITED, not re-run:** `verification/stock_check.txt` exits **FAIL** —
`LOW_STOCK(5) C265111 x2 SM08B-GHS-TB expand stock=5`, 57/58 coded lines OK,
3 uncoded (self-supplied) lines ungraded. That is the single order-side blocker
and it is the one named in my brief.

---

## 2. The two attacks I was asked to press

### 2.1 Is the 65 °C declaration supported by the published numbers?

**YES, at both forms. Every digit reproduces.** MEASURED by me,
`/usr/bin/python3`, from `02_parts/AMS1117-3.3/part.yaml` (θ_JA 90 °C/W SOT-223
package figure, `Tj_max` 125 °C, `Iq_max` 11 mA) and
`03_src/cooksense/rules/power_tree.yaml`'s graded keys only (`vin_max` 5.25,
`vout_min` 3.201, `iout_max_A` 0.20) — I did not adopt the documents' arithmetic:

```
PD_pass = (5.250 - 3.201) x 0.200        = 409.800 mW      (claim 409.8)   OK
PD_q    = 5.250 x 0.011                  =  57.750 mW      (claim 57.75)   OK
rise    = 0.467550 W x 90 C/W            =  42.0795 C      (claim 42.0795) OK
Tj(65)  = 65 + 42.0795                   = 107.0795 C      (claim 107.08)  OK
margin  = 125 - 107.0795                 =  17.9205 C      (claim 17.92)   OK
Ta_ceil = 125 - 42.0795                  =  82.9205 C      (claim 82.92)   OK
honest  = 17.9205 - (1.55 .. 4.65)       =  13.27 .. 16.37 (claim 13.3-16.4) OK
ceil_h  = 82.9205 - (1.55 .. 4.65)       =  78.27 .. 81.37 (claim 78.3-81.4) OK
```

The 65 °C row, the 75 °C row, the 80 °C `−1.73 FAIL` row and the 82.92 °C
ceiling all regenerate exactly. **The CITABLE 17.92 °C and the honest
13.3…16.4 °C are both correct as stated**, and the term that separates them is
named rather than folded in, which is the property that makes the pair honest.

I also probed the derivation's own soft spots, and all three point the same way
— **towards 65 °C being the right rung**, not away from it:

* If `θ_JA` is the lens's pessimistic 92.3 °C/W instead of the cited 90, margin
  at 65 °C is 16.84 °C citable. Still comfortable.
* If the AMS1117's ground-pin current at 0.2 A load exceeds the 11 mA the
  datasheet specifies at `(VIN−VOUT)=1.5 V` — a real question for an
  LM1117-class PNP part, and one **not covered by B1–B6** — then at 20 mA the
  margin falls to ~13.6 °C citable / 9.0…12.1 °C honest at 65 °C, but to
  3.6 °C citable / **−1.1…2.1 °C honest at 75 °C**. The narrowing buys immunity
  to this uncertainty.
* At the STAGGERED dual-heater peak the true rail current is 206.9 mA, i.e.
  **above** the declared `iout_max_A: 0.20` (the file says +6.6 mA and it is
  right). PD becomes 423.9 mW, 85.3 % of 497 — E-TOPO still passes.

Two arithmetic qualifications on the honest interval are in the findings table
as P2-1 and P2-2. Neither changes the verdict; P2-2 makes the pessimistic end
~1.1 °C worse than published at both corners, which strengthens the decision.

**A benefit nobody claimed, MEASURED by me:** ADR-0021's eFuse OVLO worst case
is taken over **−20…+70 °C** with ±100 ppm/°C resistor TCR. Under the OLD 75 °C
declaration the OVLO divider resistors reach 75 + 4.65 = 79.65 °C once the
release's own board-rise term is carried — **outside** the ±45 K window
ADR-0021 used, so the 5.3682 / 6.2394 V corners were computed at a temperature
the board could exceed. At the new 65 °C they reach 69.65 °C and the window
holds by 0.35 K. The narrowing repairs a latent corner-assumption defect in the
protection setpoint that no document mentions.

### 2.2 `pdiss_max_mw: 497` held at the 75 °C derating while declaring 65 °C

**DEFENSIBLE. It is a ratchet, not an internal inconsistency, and I would not
change it.** My reasoning, independent of ADR-0029's:

MEASURED by me:
```
75 C derating: (125-75)/90*1000 - 5.250*11 = 555.556 - 57.750 = 497.806 -> 497
65 C derating: (125-65)/90*1000 - 5.250*11 = 666.667 - 57.750 = 608.917 -> 608
PD/497 = 82.45 %   PD/608 = 67.40 %      both PASS; nothing is rescued
```

The key is **not** "a derating computed at the wrong ambient". It is a ceiling
that is numerically *stricter* than the declared corner requires, i.e. the gate
enforces `Tj ≤ 125 °C` at **Ta = 75 °C — the SURVIVE corner ADR-0029 explicitly
retains**. A gate held at the survive corner is exactly what a survive corner is
for. Calling that an inconsistency would require the premise that a graded key
must equal the declared corner, and this repo's canon is the opposite: floors
ratchet, ceilings do not relax.

**Will it mislead someone?** Three places pre-empt the back-derivation, and I
checked all three exist in the shipped artifact:
`power_tree.yaml` lines 638–641 and 664–675 (a block AT the key, in capitals,
saying "read the next paragraph before 'fixing' either"); ADR-0029 Decision 4;
and `ORDER_README.md` §0-T's "**One thing in `power_tree.yaml` will look wrong
and is not.**" That is adequate.

**The one thing that is weaker than the ADR's framing suggests** is filed as
P2-3: the ratchet is enforced by prose only. I enumerated all six ADR bounds in
this project (`LDO_DROPOUT_IBOARD_MAX`, `LDO_TJ_WORKED_EXAMPLE`,
`LDO_TA_MAX_CITED`, `COIL_PULLIN_BUDGET`, `LDO_IOUT_MAX`,
`LDO_TJ_DECLARED_AMBIENT`) and **not one reads `pdiss_max_mw`**; the two
Tj bounds regenerate from `vin_max`/`vout_min`/`iout_max_A` alone, and
`power_topology.py` consumes the key only as a comparison ceiling. A future
editor moving 497 → 608 → 720 fails nothing. ADR-0029's own owed patch P20
names precisely this gap, so the ADR is honest about it; I record it because
"structural choice" reads stronger than "convention", and it is a convention.

---

## 3. Protection topology traced from the netlist (MEASURED, not inherited)

I parsed `source/cooksense.net` into 239 components / 198 nets and walked the
chain by pad, not by document.

```
J_PWR.1 ──5V_IN──┬── D_ESD_IN.1  (PESD5V0S1BA, bidir, K1/K2, 2 -> GND)
                 └── F1.1  (MF-MSMF200L-2 PPTC)
   F1.2 ──5V_FUSED──┬── D_REVCLAMP.1  (SS34, K on rail, A -> GND)  CROWBAR
                    └── Q_REV.3  = DRAIN
   Q_REV.2 = SOURCE ──5V_RPP──┬── U_EFUSE.3/.4 (IN, bonded)
                              ├── R_OVT.1 (100k, OVLO top leg)
                              └── C_EFIN.1 (100nF)
   Q_REV.1 = GATE ── GND   (direct tie, no resistor, no zener)
   U_EFUSE.5 ──5V_PROTECTED──┬── D_TVS.1 (SMBJ5.0A, K on rail, A -> GND)
                             ├── U_LDO.3, CE1, C_LDOIN, C_IN1, C_IN2
                             ├── Q_COIL.2, R_STOPRAIL.1, R_HSG.2
                             └── J_LOADCELL.1 (off-board, Board D)
```

**Reverse-polarity behaviour — CORRECT, and I checked the orientation from
first principles rather than from the dossier.** A P-channel body diode conducts
DRAIN→SOURCE. For a high-side reverse-polarity guard with the gate at GND the
FET must be installed "backwards" relative to a load switch: drain toward the
supply so the body diode conducts in the *normal* direction, source toward the
load so that under reverse polarity `Vgs = 0` and the body diode is
reverse-biased. MEASURED: `Q_REV.3 (DRAIN) = 5V_FUSED` (supply side),
`Q_REV.2 (SOURCE) = 5V_RPP` (load side), `Q_REV.1 (GATE) = GND`. **Correct.**
`Vgs` at the sanctioned ceiling is −5.25 V against an AO3401A ±12 V abs max
(2.3×), and even at `D_ESD_IN`'s 10 V clamp point it is −10 V, inside. The bare
gate-to-GND tie is legitimate at 5 V; no zener is needed.

**Crowbar coordination — CORRECT.** `D_REVCLAMP` is on `5V_FUSED`,
**downstream** of F1, so a sustained reverse-hookup fault current passes through
and trips the polyfuse. Had it been on `5V_IN` the clamp current would bypass
the fuse and be bounded only by the supply. `electrical_invariants.yaml` pins
this node, and E-INV passes 168/168.

**TVS directionality — CORRECT, and the ordering is right.** `D_TVS` is an
SMBJ5.0**A** (unidirectional; the `C` that would make it bidirectional is
absent), cathode on the rail. MEASURED from the committed
`LITTELFUSE-SMBJ-SERIES-v4-2025-07-04.pdf` (sha256 matches the dossier), SMBJ5.0A
row: `V_R 5.0 / V_BR 6.40–7.00 @ I_T 10 mA / V_C 9.2 @ I_PP 65.3 A /
I_R 800 µA / α_VBR 0.041 %/°C`. It sits **downstream of the eFuse**, so the
failure mode the dossier warns about — a sustained over-voltage turning a 600 W
transient part into a DC regulator — is structurally impossible: OVLO
disconnects the rail the TVS is on.

**OVLO setpoint — I re-derived ADR-0021's corners independently and they
reproduce to the last digit.** `V_OVLO(R)` 1.13/1.20/1.27 V, `R_OVT` 100 k ±0.5 %,
`R_OVB` 26.1 k ±0.5 %, ±100 ppm/°C over ±45 K, `I_EN` ±0.1 µA across the
Thevenin source:

```
nominal        1.20 / (26.1/126.1)                        = 5.7977 V   (5.798)
earliest trip  1.13 / k_max(+0.95%) - I_EN*R_th/k_max     = 5.3682 V   (5.3682)
latest  trip   1.27 / k_min(-0.95%) + I_EN*R_th/k_min     = 6.2393 V   (6.2394)
```

Ordering at the corners: earliest trip 5.3682 V is **+118 mV above** the
sanctioned 5.250 V ceiling (no nuisance trip); latest trip 6.2393 V is
**−42.6 mV below** the TVS `V_BR` min at −20 °C (6.2819 V) and −1261 mV below
the DIP05 coil's 7.5 V max. The chain is ordered correctly. From the cited
0.041 %/°C the ordering inverts at **Ta ≈ −36.2 °C**, and the consequence of
inversion is mild (~10 mA / 62 mW in an SMB). See P2-5 on the undeclared floor.

**`D_ESD_IN` — a real, already-quantified gap, correctly dispositioned.**
MEASURED: it is on `5V_IN`, ahead of F1 and ahead of the eFuse, with nothing in
series, and it is the lowest-breakdown clamp on the board (`V_BR` min 5.5 V vs
the SMBJ's 6.40 V and the OVLO's earliest 5.3682 V). Above ~5.5 V it is the
first device to conduct and its current is bounded only by the supply. I agree
with `02_parts/PESD5V0S1BA/part.yaml`'s own `placement_verdict`: the *position*
is right (an ESD clamp belongs at the connector), the *derating* is not
(250 mV between the sanctioned ceiling and `V_BR` min, and 5.5 V is a 25 °C
number). This is a v-next BOM change, not a v1.7 blocker — the fault requires an
adapter outside the MANDATORY declared input spec. I add one number the dossier
does not carry: with `V_CL` 10.0 V at 1 A the dynamic resistance is ~4.5 Ω, so a
6.0 V adapter drives ~111 mA / 0.67 W into a SOD-323. It self-destructs; nothing
downstream is harmed, because OVLO has already opened.

**Safety-chain restrictive defaults — verified against the netlist, correct.**
`ESTOP_RAW_IN` unplugged sits at 0 V through `R_ESTOPPD` 470 Ω, giving
`ESTOP_OK` LOW through the two HC14 inverters, which takes `AND1`, `CTR_SAFE`
and `FAULT_SET_N` down: the chain goes inert, which is the safe direction
(ADR-0025). `J_DOOR` is **absent from the netlist** (0 occurrences) — deleted,
not DNP, as ADR-0025 claims. `MODE_RAW` low ⇒ `MODE_AUTO_HW` low ⇒
`KEY_RELAY_ALLOWED` low. Every default I traced fails safe.

**Clamp-vs-protected rating pairs I checked and found sound:**

| pair | measured | verdict |
|---|---|---|
| `D_TVS` V_C 9.2 V vs AMS1117 abs-max `vin 15 V` | 1.63× | OK |
| `D_TVS` V_C 9.2 V vs TPS259573 abs-max 20 V | 2.17× | OK |
| `EF_OVLO` node at 20 V input vs pin abs-max 7 V | 20 × 26.1/126.1 = 4.14 V | OK |
| `Q_REV` Vgs at 5.25 V / at 10 V clamp vs ±12 V | −5.25 / −10 V | OK |
| `CE1` 16 V vs 5V_PROTECTED max 5.25 V | 3.05× | OK |
| MAX31856 TC inputs vs `AGND−0.3…AVDD+0.3` | 100 Ω/leg + 100 nF diff + 10 nF/leg = Maxim's own Typical App filter, implemented exactly (`R_TCP`/`R_TCN` 100 Ω, `C_TCD`, `C_TCPA`, `C_TCNA`) | OK — no finding |
| TPS3823-33 `V_IT−` max 3.00 V vs rail `vout_min` 3.201 V | +201 mV | OK, no nuisance reset |
| MAX31856 `vdd` min 3.0 V vs rail `vout_min` 3.201 V | +201 mV | OK |
| DIP05 contact 0.5 A switch vs 10FDZ-BT 50 mA/contact keypad | keypad currents are µA | OK |

---

## 4. E-MARGIN and E-OFF — judged, not just run

**E-MARGIN: `N-A` is the CORRECT verdict, and I confirmed it by hand rather than
accepting the gate's silence.** The gate's motivating case is a regulated rail
feeding a load with a fixed brownout threshold (the usb-hub-3s Pi-5 incident).
MEASURED from the netlist: **`J_PI` pins 1, 2, 4 and 17 are all unconnected** —
this board neither powers the Pi nor draws from the Pi's rails, so the
motivating topology does not exist here. I then walked every rail to its
lowest-Vcc consumer by hand:

* `3V3` (min 3.201 V) → MAX31856 needs 3.0 V (+201 mV); TPS3823-33 `V_IT−` max
  3.00 V (+201 mV); MCP23017/MCP3208/HC/LVC families all ≥ 2.0–2.7 V.
* `3V3_SW_A/B` → Adafruit 4407 breakout regulates locally with an AP2112K-3.3;
  the AO3401A drop at 31.4 mA is 2.3 mV.
* `3V3_SW_RHA/RHE` → SHT45, 1.08–3.6 V.
* `5V_PROTECTED` → `J_LOADCELL.1` feeds an HX711 (2.6–5.5 V) at 4.711 V.
* `5V_KEY_RELAY` → the reed coils, which are the one real setpoint-vs-load
  margin on this board and are graded by `COIL_PULLIN_BUDGET` rather than by
  E-MARGIN. I re-derived it: `4.691 − 0.046 − 3.500×(1+0.004(T−20))` is
  **+0.445 V at 70 °C**, and crosses zero only at a coil temperature of
  **101.8 °C**. Ampere-turn cross-check `4.691/(600+6.5) = 7.734 mA` against
  `I_PI = 3.5/500 = 7.00 mA` required, +10.5 %. Both views agree. Sound.

So E-MARGIN's `N-A` is a true negative, not a gate hole. (I note that
`ORDER_README` §14 P1-C already says the gate "cannot fail on this board" — I
reached the same place independently and by a different route, the pad-level
walk above.)

**E-OFF: `N-A` is the CORRECT verdict, and the declaration is true.** MEASURED
from the netlist: the only energy stores on the board are `CE1` 220 µF plus
21 MLCCs on `5V_PROTECTED`/`3V3` and the twelve reed-coil inductances. Stored
energy in `CE1` at 5.25 V is **3.03 mJ**; it bleeds through the always-present
`R_OVT`+`R_OVB` (126.1 kΩ) and the LDO's own quiescent path in milliseconds.
There is no battery, cell, pack or supercap anywhere in the BOM (I checked all
62 BOM lines). The reed coils de-energize the instant input is removed, and the
contacts open — which is the fail-safe direction for a keypad interceptor.
`source_type: external_5v_selv` is authoritative and correct; de-energization is
by unplugging `J_PWR`. **There is no stored quiescent drain to bound.**

---

## 5. Findings

| # | finding | sev | evidence (cited: file+line, or a number I measured) | disposition |
|---|---|---|---|---|
| **P1-1** | **The board's NARROWEST operating-temperature rating is absent from the envelope decision, and it makes §7b's "may reopen 75 °C" clause unsound.** `DIP05-1A72-13L` is rated **−20…+70 °C** (`02_parts/DIP05-1A72-13L/part.yaml:42` `limits.t_op` and `:58` `electrical.t_op: [-20, 70]`), and twelve of them are on this board including `K_STOP`. It appears in **neither** ADR-0028's "what binds" table (`0028-….md:151-158`, which lists `U_LDO` Tj, `F1` −40…+85, `J_PWR` −40…+105, `U_EFUSE` −40…+125 and the dropout — but not the relay), **nor** ADR-0029's justification (`0029-….md:42-46` names `F1`'s −40…+85 °C as the ceiling 65 °C "sits below with room"), **nor** `ORDER_README` §0-T. The tree already knows: `02_parts/S4B-ZR-SM4A-TF/part.yaml:46-47` says verbatim that `DIP05-1A72-13L … is -20..+70C` and is "THIS BOARD'S BINDING LIMIT". Consequences: **(a)** at the declared 65 °C the relay headroom is 5 °C nominal and **0.35…3.45 °C** once the release's own +1.55…+4.65 °C board-rise term is carried — thinner than the 13.3…16.4 °C the release publishes as its worst honest margin, and the relays are the *source* of 0.705 W of that 0.958 W, so the local rise in the relay field is plausibly larger than the LDO-tab figure I used as a proxy. Nothing in the tree computes it. **(b)** §7b's "**PASSING B1–B6 MAY REOPEN 75 °C**" is false as a sufficient condition: B1–B6 measure `F1` R-vs-T, Micro-Fit contacts, AMS1117 dropout at 0.2 A, `θ_JA`, `ΔT_board` and the SOT-223 time constant — **none of them can move a catalogue relay rating**, and 75 °C is 5 °C above it *before* any board rise. **(c)** the `+70 °C` that has been doing the work in this tree IS the relay's ceiling, but `ORDER_README.md:171` calls it "**the brief's +70 °C envelope top**" — the BRIEF's enclosure ladder is 50/55/65/75 with no 70 rung (`BRIEF.md:117`; 70 is the *camera*'s stop rung), and after ADR-0029 the declared top is 65 and the survive corner 75. The coil-margin table's row labels ("+70 C ← top of the declared envelope", "+75 C ← hard limit") are now stale. | **P1** | `02_parts/DIP05-1A72-13L/part.yaml:42,58`; `02_parts/S4B-ZR-SM4A-TF/part.yaml:46-47`; `0028-….md:151-158`; `0029-….md:42-46`; `ORDER_README.md:171` and §0-T; MEASURED headroom 70 − (65 + 1.55…4.65) = **0.35…3.45 °C** | **OPEN.** Does not block v1.7: 65 °C is inside the rating. **Must be recorded before §7b is ever exercised** — the reopen clause needs a relay-rating precondition, or 75 °C needs a code-13 extended-temperature relay. Cheapest correct fix: add the DIP05 row to ADR-0028's binding table via a new ADR, and amend the §7b bullet to "B1–B6 are NECESSARY, not SUFFICIENT; 75 °C additionally requires a relay rated above it." |
| **P1-2** | **A CITED protection rating in `02_parts` is wrong by 2×, in the permissive direction, and the committed PDF the dossier itself names refutes it.** `02_parts/MF-MSMF200L-2/part.yaml:9-11` asserts "the ELECTRICAL row is MF-MSMF200/**16X** (16 V)" and `limits.vmax: "16 V"`. MEASURED by me from that dossier's own `BOURNS-MF-MSMF-SERIES.pdf` (sha256 `a84b990157…` — I verified it matches the declared hash), **Part Identification table**: `MF-MSMF200/8X = **L**`, `MF-MSMF200/12X & 200/16X = A`. The fitted MPN `MF-MSMF200**L**-2` carries the L, so F1 is the **8 V** row, not 16 V. The `ihold_vs_temp` table in the dossier is likewise the /16X row (…1.43 at 70, 1.25 at 85) where /8X is (…1.45 at 70, **1.29** at 85). **ADR-0028:187, ADR-0029 B1 and `ORDER_README` §7b B1 all say /8X and are RIGHT; the dossier is the outlier.** No margin on this board moves — `R1Max 0.070`, `Ihold 2.00` and `Itrip 3.50` are identical across all three variants (PDF lines 129–131), and the rail never exceeds ~6.24 V before OVLO opens. The one path that would ask F1 to hold off more than 8 V is a reverse-polarity crowbar event with an out-of-spec adapter. | **P1** | `02_parts/MF-MSMF200L-2/part.yaml:9-11,26`; `BOURNS-MF-MSMF-SERIES.pdf` Part Identification ("MF-MSMF200/8X = L") and Electrical Characteristics rows 129–131; `0028-….md:187` | **Dossier correction owed** (`vmax` 16 → 8 V; `ihold_vs_temp` → the /8X row). Not an order blocker. Note the direction: the *analysis* is right and the *dossier* is wrong, which is the reverse of the usual failure and worth saying out loud. |
| **P2-1** | **Two accepted, non-superseding ADRs publish different intervals for the same quantity.** ADR-0029 publishes the honest margin as **13.3…16.4 °C** (65 °C) and the honest ceiling as **78.3…81.4 °C**, using `h = 18…6`. ADR-0028's own table (`:137-142`) has only `h=10 (+2.79)` and `h=6 (+4.65)` columns, its summary says the declared ambient "is inside it by **3.3–5.1 °C**" (`:161`), and its bound `LDO_TA_MAX_CITED` says the honest ceiling is "**78.3...80.1 C**" (`:541`). ADR-0029 is the *more complete* one — ADR-0028's own prose at `:145` already publishes the 1.55…4.65 range — but ADR-0029 states that ADR-0028's bounds regenerate "unchanged and **true**", and `LDO_TA_MAX_CITED`'s claim text also still reads "**The declared ambient is 75 C**", which ADR-0029 made false. The *value* (82.92) is unchanged and true; the *prose* is not. | P2 | `0029-….md:117-136`; `0028-….md:137-147,161`; `0028-….md:534-545` (bound claim) | Append-only decisions cannot be edited, so this is structural. A one-line forward note in the next ADR ("`LDO_TA_MAX_CITED`'s claim prose predates ADR-0029; its value is unaffected") closes it. |
| **P2-2** | **The pessimistic corner is under-computed by ~1.1 °C at both ambients, because two terms driven by the same physical parameter are combined at different values of it.** `ΔT_board` (+1.55…+4.65 °C) and the lens's `θ_JA` (81.6…92.3 °C/W) are **both** functions of `h = 18…6`. The release combines `ΔT_board` at `h=6` with the **cited** `θ_JA` 90, not with `h=6`'s own 92.3. MEASURED by me: at `h=6`, rise = 0.46755 W × 92.3 °C/W = **43.155 °C**, plus 4.65 → `Tj(65) = 112.81 °C`, margin **12.19 °C** (published 13.27) and at 75 °C **2.19 °C** (published 3.27). | P2 | `0028-….md:146`; MEASURED by me, `/usr/bin/python3` | **Direction is favourable**: it makes the 65 °C choice more right and ADR-0029's rejected option (e) (seal at 75 on the bench gate alone) more clearly wrong. Record; no action. |
| **P2-3** | **The `pdiss_max_mw` ratchet is a convention, not a gate.** MEASURED: I enumerated all six ADR bounds in this project and **none reads `pdiss_max_mw`**; `LDO_TJ_DECLARED_AMBIENT` and `LDO_TJ_WORKED_EXAMPLE` regenerate from `vin_max`/`vout_min`/`iout_max_A` only, and `power_topology.py` consumes the key solely as a comparison ceiling (`:526-542`). A future editor raising 497 → 608 → 720 fails nothing. | P2 | `grep -rn "<!-- bound:" 01_docs/decisions/*.md` = 6 bounds, none reading the key; `skills/kicad-pcb/scripts/power_topology.py:526-542` | ADR-0029's own owed patch **P20** already names this exactly. No new action; recorded so "the load-bearing structural choice in this ADR" is read as the convention it is. |
| **P2-4** | **An arithmetic slip inside a protection dossier's cited-tempco line.** `02_parts/SMBJ5.0A/part.yaml:28` says `V_BR` min "falls to 6.2819 V at −20 C and **6.0975 V at −40 C**". MEASURED from the committed `LITTELFUSE-SMBJ-SERIES-v4-2025-07-04.pdf` (SMBJ5.0A row: 5.0 / 6.40 / 7.00 / 10 / 9.2 / 65.3 / 800 / **0.041**): with the cited 0.041 %/°C, `6.40 × (1 − 0.00041 × 65) = **6.2294 V**`, not 6.0975. The −20 °C figure is correct (6.2819 ✓). The −40 figure implies 0.0727 %/°C. | P2 | `02_parts/SMBJ5.0A/part.yaml:28`; PDF row measured by me via `pdftotext -layout` | Direction is **pessimistic** and nothing in the tree cites the −40 figure, so no verdict moves. Fix the line. |
| **P2-5** | **The declaration is one-sided: a ceiling with no floor, on a board whose protection ordering binds at the cold corner.** ADR-0029 declares only `Ta = 65 °C` max (plus a 75 °C survive corner). ADR-0021's OVLO worst case, `02_parts/SMBJ5.0A`'s tempco, and `DIP05`'s `t_op` all carry a **−20 °C** low corner that no document declares. MEASURED by me: the OVLO-vs-TVS ordering holds by **+42.6 mV** at −20 °C and inverts at **Ta ≈ −36.2 °C** (from the cited 0.041 %/°C). | P2 | `0029-….md:88-93`; `power_tree.yaml:797`; `electrical_invariants.yaml:677`; MEASURED inversion temperature | Consequence of inversion is mild (~10 mA / 62 mW in an SMB, vs the 6.6 A the v1.2–v1.6 setting would have passed). Declare `−20 °C` as the operating floor in the same fact-lock row that carries 65/75. |
| **P2-6** | **The bulk electrolytic has no `limits:` block at all — the same class ADR-0028 Decision 4 closed on `PESD5V0S1BA` two days ago, not swept.** `02_parts/RVT220UF16V67RV0015/part.yaml` records pins, a polarity assert and sourcing, and **no voltage, temperature, endurance or ripple rating**. MEASURED from `skills/jlcpcb-fab/references/lcsc_passives_ledger.yaml:162` (JLC `describe`, exact componentCode match): `-55℃~+105℃ 110mA@120Hz 16V **2000hrs@105℃** 220uF ±20%`. DERIVED by me: `2000 × 2^((105−T)/10)` at the declared 65 °C plus the release's own +1.55…+4.65 °C rise = **23,100…28,800 h (2.6–3.3 yr continuous)**; at the 75 °C SURVIVE corner **11,600 h (1.3 yr)**. | P2 | `02_parts/RVT220UF16V67RV0015/part.yaml` (no `limits:`); `lcsc_passives_ledger.yaml:162`; arithmetic mine | No requirement is violated — the BRIEF declares no service life — but the declared ambient's **largest single lifetime consequence** sits on the one part with no ratings block, and `CE1`'s ESR rise degrades the eFuse's inrush behaviour and the LDO's input decoupling. Add a `limits:` block; state a service-life expectation in the BRIEF. |
| **P2-7** | **The AMS1117's frequency-compensation capacitor has no recorded voltage rating and no DC-bias analysis.** ds1117's *Stability* section makes `COUT` part of the device's loop compensation, and `02_parts/AMS1117-3.3/part.yaml:39` demands a "**≥22 µF-class**" cap hard against VOUT. MEASURED: the tree records **value only** for `C_LDOOUT` = `C45783` / `CL21A226MAQNNNE` — `lcsc_passives_ledger.yaml:122`, `verification/stock_check.json` and `verification/bom_legibility.txt:27` all carry MPN + `"22uF"` and **no voltage rating, no dielectric code, no describe string** — and `grep -i "dc.bias"` over `ORDER_README.md`, `DETAIL_DESIGN.md`, `01_docs/decisions/*.md` and `03_src/cooksense/rules/*.yaml` returns exactly one hit, and it is about the one-shot timing cap, not this one. An X5R 0805 22 µF at 3.3 V DC bias retains roughly 85 % (25 V part) down to ~40 % (6.3 V part) of nominal. | P2 | `lcsc_passives_ledger.yaml:122`; `verification/bom_legibility.txt:27`; `verification/stock_check.json` (no `describe`); `02_parts/AMS1117-3.3/part.yaml:39` | **"≥22 µF-class" is not verifiable from the tree** for the one capacitor the datasheet puts inside the control loop. Read the JLC `describe` for `C45783` and record voltage + dielectric; if it is a 6.3 V part, this becomes P1. |
| **P2-8** | **`J_MODE` is hardened on one of its two field-fed pins.** MEASURED from the netlist: `COIL_EN_IN` (`J_MODE.4`) = `{D_COILEN (PESD5V0S1BA), R_COILENS 680 Ω series, R_COILENPD 680 Ω}` — clamp + series + pull-down, exactly ADR-0018's remedy. `MODE_RAW` (`J_MODE.2`) = `{J_MODE.2, R_MODEPD 10 kΩ, U_SCHM.5}` — **no clamp, no series element**, straight into an SN74HC14 input, on the same connector, feeding the same safety chain (`MODE_RAW → MODE_NI → MODE_AUTO_HW → U_AND1.1`). ADR-0018's mechanical key defeats the cross-plug case but not an ESD strike on a panel-switch wire. No ADR records the asymmetry as a decision. | P2 | netlist: `MODE_RAW = ['J_MODE.2','R_MODEPD.1','U_SCHM.5']`; BOM `R_MODEPD = 10 kΩ C60490`, `R_COILENS/R_COILENPD = 680 Ω C137948`; `0024-….md` preamble | **Not a single-fault enable path**: the restrictive default is correct (LOW ⇒ chain inert) and `KEY_RELAY_ALLOWED` additionally requires `WD_OK·ESTOP_OK·TEMP_OK·MCU_RELAY_ENABLE·HOST_AUTH·FAULT_LATCH_CLEAR`. Record. This is the **fourth** instance of the "remedy computed, applied to one of N" shape ADR-0024's own preamble names as recurring. |
| **P2-9** | **E-TOPO's advisory output states a false fact about a protection part.** MEASURED (my run): `OVER-BUILT (advisory): fuse rated 0.5 A is >2x the derived need 0.2 A — over-provisioned [read from ORDER_README.md: `Q_REV` 73.5 + eFuse 47.0 = 190.5 mΩ at 0.50 A). All three are right; two whole]`. F1 is a **2.0 A-hold** PPTC. The gate scraped `0.50 A` out of a prose sentence in `ORDER_README.md` and reported it as a fuse rating, quoting a truncated mid-sentence fragment as its provenance. | P2 | my E-TOPO run, stdout above; `02_parts/MF-MSMF200L-2/part.yaml:24` `ihold: "2.00 A at 23 C"` | Advisory-only; changes no verdict and no exit code. But a gate that invents a protection-part rating from prose is the class this repo has paid for before. Skill-side; outside this board's partition. |

---

## 6. Observations (not findings)

* **The "pre-seal" framing is stale.** `07_releases/cooksense-v1.7-2026-07-30/`
  already exists (created 21:46, **untracked in git**) with an ORDER_README.md
  byte-identical to staging (`md5 e9276226dad286df6d20c35f39f4a8df` both) and an
  identical fab set; the only differences are nine verification `.txt`/`.md`
  files plus an `adr_bound_provenance.txt` present only in the release. Under
  CLAUDE.md's immutability rule, any correction from this review is a NEW
  version plus `SUPERSEDED.md`, not an edit.
* **The staging archive was being written while I reviewed it.**
  `verification/stock_check.txt`'s last line names *my own session's* scratchpad
  path, i.e. a sibling agent regenerated it during this review. My gate results
  are timestamped by their own runs and are unaffected, but the archive is not
  quiescent.
* **What I checked and found sound, stated so silence is not read as absence of
  effort:** reverse-polarity FET orientation from first principles; crowbar
  placement relative to F1; TVS directionality and its position relative to the
  eFuse; the full OVLO corner stack re-derived to the last digit; Q_REV/eFuse/
  AMS1117/TVS/CE1 abs-max pairs; the MAX31856 TC front end against Maxim's own
  Typical App circuit; every restrictive default on the safety chain;
  `J_DOOR`'s absence from the netlist; all 62 BOM lines for a self-contained
  energy source; and every resistor value the `power_tree.yaml` load
  itemisation cites, cross-read against `fab/bom.csv` (`R_ESTOPPD` 470 Ω,
  `R_COILENPD` 680 Ω, `R_OPTOLED` 330 Ω, `R_OVT` 100 k, `R_OVB` 26.1 k,
  `R_ILM` 1.2 k, `R_OPENT` 62 k, `R_MODEPD`/`R_BID1`/`R_OE`/`R_OS2` 10 k,
  `R_OS` 510 k, 2.2 k bus pull-ups) — **all twenty-one match**.
* `02_parts/AQY212GS/` is an orphan dossier: zero occurrences in the netlist and
  zero in the BOM. Not a defect (02_parts is the MPN authority for sealed
  releases), but worth knowing it describes nothing on this board.

---

## 7. Verdict

**The artifact is CORRECT.** Copper, netlist, BOM and CPL are unchanged and
verified so by md5. DRC is 0/0/0 on **both halves** with `--exit-code-violations`
passed. E-TOPO, E-MARGIN, E-OFF and E-INV all exit 0 under my own invocations,
and I judged the two `N-A` verdicts by hand rather than accepting them: both are
true negatives. The 65 °C declaration reproduces **exactly** from the cited
constants and the graded keys, at both the citable and the honest form, and
every soft spot I probed in its derivation makes 65 °C *more* right rather than
less. Holding `pdiss_max_mw` at 497 is a ratchet at the retained survive corner,
not an internal inconsistency, and three places in the shipped artifact
pre-empt the misreading.

**No P0.** The two P1s are documentation defects, not artifact defects: a
catalogue relay rating missing from the envelope reasoning (which makes a
forward-looking reopen clause unsound but leaves the *declared* 65 °C inside
every part rating on the board), and a cited voltage rating in one dossier that
the dossier's own committed PDF refutes. Neither prevents the board being built
or bought.

**Order side:** the sole blocker is `C265111` (JST `SM08B-GHS-TB`,
`J_THERM_A`/`J_THERM_B`) at stock 5 with `minPurchaseNum` 21 — unbuyable at any
quantity today. That is a supply fact, not a design fact, and it has not been
allowed to contaminate `design_verdict`.

```
design_verdict: SOUND
order_verdict:  BLOCKED-SOURCING
```
