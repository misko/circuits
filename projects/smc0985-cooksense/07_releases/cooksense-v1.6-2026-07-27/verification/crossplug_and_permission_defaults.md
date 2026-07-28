# THE THREE v1.5 P1s, RE-VERIFIED FROM THE NETLIST — cross-plug, permission defaults, re-arm

This is v1.6's whole reason to exist. The 2026-07-27 adversarial audit
(`08_reviews/2026-07-27_v1.5_redteam_adversarial.md`, report-only, committed
f8427c5) left three open P1s. All three are PAPERWORK — the copper does not move
— but a paperwork defect on a safety chain is a defect, and two of the three
were *false statements in this board's own documents*.

**Method, and why it is not the design's method (canon M1).** Every number below
was re-derived by parsing the exported netlist's s-expressions and asking set
questions about them — "which nodes are on this net", "which two-pin resistors
have exactly one end on GND or a rail". That shares no code with the tsx author,
with `generate_board_generic.py`, or with `policy_audit`. Where the
re-verification DISAGREED with the audit it is written down as a refinement, not
harmonised away.

**Which netlist.** The analysis was run against
`06_build/netlists/cooksense.net` and then RE-RUN against this archive's own
`source/cooksense.net`. The two differ in bytes (md5 `60a3326…` vs `8ebed11…` —
the export header carries a different source path, date and sheet name) and are
**SEMANTICALLY IDENTICAL**: 192 nets both sides, the same net-name set, **0 nets
with differing membership**, 222 refdes both sides, **0 refdes with a differing
value**. So every table below is a statement about the board that shipped.

---

## 1. A1 — `J_MODE` IS NOT A FAIL-SAFE CROSS-PLUG. CONFIRMED, EVERY NUMBER.

### 1.1 Five identical housings, not three

`fab/bom.csv` line 45: **one** part, **one** footprint, **five** instances —
`SM05B-GHS-TB` / `JST_GH_SM05B-GHS-TB_1x05-1MP_P1.25mm_Horizontal` / `C189896` →
`J_DOOR, J_ESTOP, J_MODE, J_RH_AMBIENT, J_RH_EXHAUST`. Nothing mechanical
distinguishes them.

| connector | pin 1 | pin 2 | pin 3 | pin 4 | pin 5 | harness |
|---|---|---|---|---|---|---|
| `J_DOOR` | `3V3` | `DOOR_RAW` | `GND` | `DOOR_RAW` | `GND` | passive, dry reed |
| `J_ESTOP` | `3V3` | `ESTOP_RAW` | `GND` | `GND` | `GND` | passive, dry NC |
| `J_MODE` | `3V3` | `MODE_RAW` | `KEY_RELAY_ALLOWED` | **`COIL_EN`** | `GND` | passive, DPDT |
| `J_RH_AMBIENT` | `3V3_SW_RHA` | `GND` | `SDA_A` | `SCL_A` | `SHIELD_DRAIN` | **POWERED pod** |
| `J_RH_EXHAUST` | `3V3_SW_RHE` | `GND` | `SDA_B` | `SCL_B` | `SHIELD_DRAIN` | **POWERED pod** |

`ORDER_README.md` §10 through v1.5 analysed the first three and concluded
"Pinouts are arranged so any single cross-plug is fail-safe". **The two it
omitted are the two that carry current.**

Physical reachability, from `fab/cpl.csv`: `J_MODE` (196.75, −60.00) east edge,
`J_RH_EXHAUST` (186.00, −96.75) south edge → **38.29 mm** apart
(√(10.75² + 36.75²)), both field-accessible, identical connectors, identical
cable. `J_RH_AMBIENT` (168.00, −96.75) is 46.66 mm away.

### 1.2 `COIL_EN` is held by one 100 kΩ resistor and nothing else

Netlist, complete membership — three nodes:

    COIL_EN  ->  J_MODE.4 , Q_COILDRV.1 (GATE) , R_COILENPD.1
    R_COILENPD = 100 kΩ to GND

**No ESD device and no series element.** `J_MODE` is the only one of the five
housings whose field pins have neither — `DOOR_RAW` carries `D_DOOR`,
`ESTOP_RAW` carries `D_ESTOP`, and `MODE_RAW` / `KEY_RELAY_ALLOWED` / `COIL_EN`
carry nothing:

    J_DOOR.2/4  DOOR_RAW           D_DOOR.1 , R_DOORPD.1 , U_SCHM.11
    J_ESTOP.2   ESTOP_RAW          D_ESTOP.1 , R_ESTOPPD.1 , U_SCHM.1
    J_MODE.2    MODE_RAW           R_MODEPD.1 , U_SCHM.5
    J_MODE.3    KEY_RELAY_ALLOWED  TP_ALLOW.1 , U_AND3.4          <- a CMOS OUTPUT, to the field
    J_MODE.4    COIL_EN            Q_COILDRV.1 , R_COILENPD.1

For scale: the three passive-harness safety inputs `R_DOORPD` / `R_ESTOPPD` /
`R_MODEPD` are all **10 kΩ**. The one pin that directly enables the relay rail is
held **ten times more weakly** than the pins that merely report a switch.

### 1.3 The pod's SCL pull-up lands on that gate

Pod harness = `1 VCC, 2 GND, 3 SDA, 4 SCL, 5 SHIELD`. In `J_MODE`:
wire 1 → `3V3` (**the pod powers up normally**), wire 2 → `MODE_RAW`, wire 3 →
`KEY_RELAY_ALLOWED`, **wire 4 → `COIL_EN`**, wire 5 → `GND`.

The module's SCL pull-up returns to the module's **VDD pin**, which wire 1 has
tied to the real 3.3 V rail — so it is a clean pull-up to 3.3 V no matter where
the pod's local ground floated to:

| pod pull-up | source | V(`COIL_EN`) = 3.3 · 100/(100+R) |
|---|---|---|
| 10 kΩ | `01_docs/DETAIL_DESIGN.md:114` "SHT pods carry module 10k pullups" | **3.000 V** |
| 4.7 kΩ | `01_docs/BRIEF.md` C7, Adafruit-class module | **3.152 V** |

2N7002 `V_GS(th)` is specified **1.0 V min / 2.5 V max** at I_D = 250 µA, so at
3.00 V **every device in the specification window is fully on** — this result
needs no subthreshold argument at all.

### 1.4 The chain from there, and what it bypasses

    Q_COILDRV (2N7002)  G=COIL_EN  S=GND  D=HS_GATE_COIL      -> ON
    HS_GATE_COIL        R_HSG 100 kOhm UP to 5V_PROTECTED     -> pulled down
    Q_COIL (AO3401A)    G=HS_GATE_COIL  S=5V_PROTECTED  D=5V_KEY_RELAY
    5V_KEY_RELAY        K_U1..U6 , K_D1..D4 , K_PRESS coils + U_ULNA.10 / U_ULNB.10 commons

Sink current `Q_COILDRV` must provide: `(5.0 − 4.0)/100 kΩ = **10 µA**` to bring
`HS_GATE_COIL` to 4.0 V (`Q_COIL` `V_GS` = −1.0 V), `(5.0 − 0.5)/100 kΩ =
**45 µA**` to hold it at 0.5 V — `V_GS` = −4.5 V, the condition the AO3401A
dossier's `R_DS(on)` < 60 mΩ figure is specified at.

**Bypassed:** all seven AND-chain terms — `MODE_AUTO_HW`, `WD_OK`, `ESTOP_OK`,
`TEMP_OK`, `MCU_RELAY_ENABLE`, `HOST_AUTH`, `FAULT_LATCH_CLEAR` — **and the
Manual/Auto physical rail cut with them**, because the rail cut IS the `J_MODE`
pin 3 → pin 4 pole and this cross-plug drives pin 4 directly.
`01_docs/BRIEF.md:88` calls that rail cut the manual-mode guarantee: "MANUAL =
OEM membrane operational + relay power physically disabled".

### 1.5 REFINEMENT — the 175 kΩ bound is softer than the rest of this section

The audit's general bound solves 3.3 · 100/(100 + R) ≥ **1.2 V** → **R ≤ 175 kΩ**.
The arithmetic is right (330/(100+R) = 1.2 → R = 175). The **1.2 V** rests on a
minimum-threshold 2N7002 conducting ~10 µA in subthreshold, which is a
worst-case-hazard assumption, not a datasheet guarantee. It is quoted in
ORDER_README §10.2 *as* the worst-case bound and labelled as such. The 10 kΩ and
4.7 kΩ results in §1.3 are the firm ones.

### 1.6 ROOT CAUSE — the model, not the arithmetic (NEW, not in the audit)

`03_tscircuit/src/cooksense.tsx` lines 633-641, the pin-review-Q re-pinning of
2026-07-23, reasoned:

> "COIL_EN's neighbours are now the AND-chain output (3) and GND (5): any
> cross-plug bridge either applies the intended gating or holds the rail OFF."

That models a cross-plug as a passive **BRIDGE** between pins. It is the correct
model for the three dry-contact harnesses and the **wrong model for a harness
that SOURCES current onto a pin**. The re-pinning itself was a real improvement
and is not being reversed; its CONCLUSION was generalised past its evidence, and
`ORDER_README` §10 then inherited the generalisation.

### 1.7 The complete 20-cell matrix

Shipped in `ORDER_README.md` §10.4, cell by cell. Five harnesses into five
sockets = 25 matings, 5 correct, **20 cross-plugs**. Class totals:

| class | count | which |
|---|---|---|
| **☠ energises the coil rail** | **2** | either pod harness into `J_MODE` |
| **⚡ rail short / unlimited over-current** | **7** | any dry-contact harness into either pod socket (6) + MODE into `J_DOOR`, where both DPDT poles close 3V3 to GND in series (1) |
| **✗ a safety input forced PERMISSIVE** | **3** | DOOR→`J_ESTOP` (door closed ⇒ E-stop reads clear), ESTOP→`J_DOOR` (E-stop clear ⇒ door reads closed), MODE→`J_ESTOP` (AUTO ⇒ E-stop reads clear) |
| **? driven into the threshold band** | **4** | either pod into `J_DOOR` (module SCL pull-up puts `DOOR_RAW` at 3.3·10/20 = **1.65 V**, inside the SN74HC14's V_T+ spread at 3.3 V) or into `J_ESTOP` (the pod's return current through `R_ESTOPPD` 10 kΩ lifts `ESTOP_RAW` by an unbounded, part-dependent amount) |
| **○ input falsified but the rail cannot arm** | **2** | DOOR or ESTOP into `J_MODE` — `COIL_EN` is unconnected, so `R_COILENPD` holds the rail off |
| **↔ silent channel transposition** | **2** | the two pod harnesses exchanged: both buses work, both SHT45s are 0x44 on their own bus, and the ambient/exhaust readings are swapped with nothing to detect it |

**Zero of the twenty are fail-safe in the sense the withdrawn claim asserted for
all of them.** The 7 shorts and the 2 cannot-arm cells announce themselves; the
2 ☠ cells announce themselves by ARMING; the 3 ✗ and 4 ? cells are **silent**,
and their only defences are the harness labels and the §7 bring-up steps that
exercise the E-stop and door directly.

---

## 2. A2 — FOUR PERMISSIONS HAVE NO PULL. CONFIRMED, EXTENDED, AND THE AUDIT'S CHARACTERISATION CORRECTED.

### 2.1 The four, confirmed

Complete netlist membership. **No resistor appears on any of them.**

    WD_OK         -> TP_WDOK.1 , U_AND1.3 , U_CAND1.1 , U_EXP.8 , U_FAULTAND.1 , U_OENAND.2 , U_WD.1
    ESTOP_OK      -> TP_ESTOP.1 , U_AND1.6 , U_CAND1.3 , U_EXP.3 , U_FAULTAND.3 , U_SCHM.4
    MODE_AUTO_HW  -> U_AND1.1 , U_EXP.2 , U_SCHM.8
    DOOR_OK       -> U_EXP.4 , U_OSCLR.1 , U_SCHM.12

Each is driven by exactly one **push-pull** output — `U_WD.1` is push-pull by
part.yaml and datasheet ("RESET is active-LOW PUSH-PULL; the open-drain family
member is TPS3828"), `U_SCHM` is an SN74HC14 with CMOS outputs. LVC/HC inputs
have no bus-hold, so an unfitted, tombstoned or cracked driver leaves an
INDETERMINATE level that may read HIGH = permissive.

### 2.2 EXTENSION — it is 11 of 18, not 4

Every net feeding a permission/gating input on this board, with its pull:

| net | consumers in the chain | pull |
|---|---|---|
| `AND1` | U_AND3.1 | **NONE** |
| `AND2` | U_AND3.3 | **NONE** |
| `COIL_EN` | Q_COILDRV.1 | R_COILENPD 100 kΩ DOWN |
| `CONTACTOR_REQ` | U_CAND2.6 | R_CTRREQPD 100 kΩ DOWN |
| `CTR_SAFE` | U_CAND2.1 | **NONE** |
| `DOOR_OK` | U_OSCLR.1 | **NONE** |
| `ESTOP_OK` | U_AND1.6, U_CAND1.3, U_FAULTAND.3 | **NONE** |
| `FAULT` | U_LATCHB.2 | **NONE** |
| `FAULT_LATCH_CLEAR` | U_AND3.6, U_CAND2.3, U_LATCHA.2 | **NONE** |
| `FAULT_SET_N` | U_LATCHA.1 | **NONE** |
| `HOST_AUTH` | U_AND2.6 | R_HOSTAUTHPD 100 kΩ DOWN |
| `HS_GATE_COIL` | Q_COIL.1 | R_HSG 100 kΩ UP (5V_PROTECTED) |
| `MCU_RELAY_ENABLE` | U_AND2.3, U_OENAND.1 | R_MCUENPD 100 kΩ DOWN |
| `MODE_AUTO_HW` | U_AND1.1 | **NONE** |
| `REARM_N` | U_LATCHB.1 | R_REARMPU 100 kΩ UP (3V3) |
| `STOP_REQ_N` | U_OSCLR.3 | **NONE** |
| `TEMP_OK` | U_AND2.1, U_CAND1.6, U_FAULTAND.6 | R_TEMPOK 10 kΩ UP (3V3_ANALOG) |
| `WD_OK` | U_AND1.3, U_CAND1.1, U_FAULTAND.1, U_OENAND.2 | **NONE** |

**7 pulled, 11 not.** The four the audit named are the ones driven from OUTSIDE
the AND-gate cluster; the other seven are internal nodes driven by the chain's
own gates, and they fail the same way.

Sharpest single-part cases, measured rather than asserted:

- **`U_SCHM` (SN74HC14, SOIC-14)** dead → `ESTOP_OK` + `MODE_AUTO_HW` +
  `DOOR_OK` float **simultaneously**. `U_AND1 = MODE_AUTO_HW · WD_OK ·
  ESTOP_OK` can then be TRUE with the E-stop mushroom pressed, and the expander
  readbacks `U_EXP.2/3/4` sample the SAME floating nets, so software sees the
  same wrong answer with no independent cross-check.
- **`U_LATCHB` (SN74LVC1G00, SOT-23-5)** dead → `FAULT_LATCH_CLEAR` floats into
  BOTH `U_AND3.6` and `U_CAND2.3` — one 5-pin part removes the fault-latch
  permission from the coil rail and the external contactor at once.
- **`U_WD` (TPS3823, SOT-23-5)** dead → `WD_OK` floats into five CMOS inputs.

**REFINEMENT:** no single part floats all four permissions. `U_SCHM` accounts
for three; `U_WD` for the fourth.

### 2.3 CORRECTION — the source's claim is wrong in SCOPE, not in arithmetic

`03_tscircuit/src/cooksense.tsx:550-552`, verbatim:

> "CONTEXT WORTH KEEPING: TEMP_OK was the ONLY permission in the safety chain
> actively pulled toward permissive. **The other twelve are pulled restrictive**,
> and REARM_N is correctly pulled up."

The audit calls this FALSE. Checked here, that is not quite the right verdict.
**Those twelve are exactly BRIEF D10 item 8's "deterministic pulls on every
Pi/expander authorization line (pull-UP on REARM_N)", and all twelve genuinely
ARE pulled restrictive:**

| # | net | pull | restrictive? |
|---|---|---|---|
| 1 | `HOST_AUTH` | R_HOSTAUTHPD 100 kΩ DOWN | yes |
| 2 | `MCU_RELAY_ENABLE` | R_MCUENPD 100 kΩ DOWN | yes |
| 3 | `CONTACTOR_REQ` | R_CTRREQPD 100 kΩ DOWN | yes |
| 4 | `KEY_RESET_N` | R_KRSTPD 100 kΩ DOWN | yes |
| 5 | `STOP_REQ` | R_STOPPD 100 kΩ DOWN | yes |
| 6 | `RAIL_EN_A` | R_RAENAPD 100 kΩ DOWN | yes |
| 7 | `RAIL_EN_B` | R_RAENBPD 100 kΩ DOWN | yes |
| 8 | `RAIL_EN_RHA` | R_RAENRHAPD 100 kΩ DOWN | yes |
| 9 | `RAIL_EN_RHE` | R_RAENRHEPD 100 kΩ DOWN | yes |
| 10 | `DECU_G1_RAW` | R_DECUPD 100 kΩ DOWN | yes |
| 11 | `DECD_G1_RAW` | R_DECDPD 100 kΩ DOWN | yes |
| 12 | `REARM_N` | R_REARMPU 100 kΩ **UP** | yes — the line is active-LOW |

Twelve, plus `TEMP_OK` = the thirteen the sentence counts. The sentence is not
wrong about its twelve. **It is wrong as a statement about "the safety chain",
because it counts only the SOFTWARE-driven lines, and the four HARDWARE-derived
permissions are in neither group.** That distinction matters: the audit's
"FALSIFIED" would send a reader looking for a missing pull-down among the twelve,
and there isn't one.

### 2.4 NEW FINDING — one register write makes the float DETERMINISTICALLY permissive

Found while verifying A2, not in the audit. All four permissions are read back
by the expander: `U_EXP.8` = GPB7 = `WD_OK`, `U_EXP.3` = GPB2 = `ESTOP_OK`,
`U_EXP.2` = GPB1 = `MODE_AUTO_HW`, `U_EXP.4` = GPB3 = `DOOR_OK`.

Microchip **DS20001952C §3.5.7** (the PDF is in `02_parts/MCP23017-E-SS/`),
verbatim: *"The GPPU register controls the pull-up resistors for the port pins.
If a bit is set and the corresponding pin is configured as an input, the
corresponding port pin is internally pulled up with a 100 kΩ resistor."* POR
value `0000 0000`.

With the driver alive, a 100 kΩ pull-up is invisible — a push-pull output wins
easily. **In the failure case it is decisive:** it converts an indeterminate
float into a deterministic HIGH = PERMISSIVE on all four permissions at once,
including "E-stop clear" with the mushroom pressed. And the asymmetry is total:
**there is no software way to add a pull-DOWN.** The register can only make the
default worse.

Shipped as a REQUIRED host-firmware invariant: `ORDER_README` §7a-2 —
`GPPUB` must be written `0x00` explicitly, not merely left at POR, and any
MCP23017 library that enables pull-ups by default must be configured off.

### 2.5 What the fix costs, and why it is not in this release

Four 0402 pull-downs for the permissions; eleven for the whole chain. **That is
copper**, so it is a USER DECISION and an ELECTRICAL revision, not a docs-only
supersede. The design already knows the rule — `R_DECUPD` / `R_DECDPD` were
added at pin review Q4 for exactly this reason ("floating CMOS inputs stay
out-of-spec: belt AND braces") — it was simply never applied to the safety
permissions themselves.

---

## 3. A3 — `REARM_N` HELD LOW DEFEATS THE FAULT LATCH. CONFIRMED, AND THE PERSISTENCE IS WORSE THAN STATED.

### 3.1 Topology, from the netlist

    U_LATCHA (SN74LVC1G00 NAND)  A=FAULT_SET_N        B=FAULT_LATCH_CLEAR  Y=FAULT
    U_LATCHB (SN74LVC1G00 NAND)  A=REARM_N            B=FAULT              Y=FAULT_LATCH_CLEAR
    U_FAULTAND                   WD_OK · ESTOP_OK · TEMP_OK -> FAULT_SET_N

A cross-coupled /S-/R NAND latch: /S = `FAULT_SET_N`, /R = `REARM_N`,
Q = `FAULT`, /Q = `FAULT_LATCH_CLEAR`.

    REARM_N -> R_REARMPU.1 , U_EXP.26 (GPA5) , U_LATCHB.1

**One driver.** No button, no connector pin, no test point, no jumper.
`01_docs/BRIEF.md:85-86` requires "explicit manual re-arm"; in this build that is
a register write from the same Pi the hardware chain exists to bound (brief §12
threat model, T6).

### 3.2 Held low

- /R asserted → `FAULT_LATCH_CLEAR` forced **HIGH permanently** — permissive at
  `U_AND3.6` (coil rail) and `U_CAND2.3` (external contactor) at all times;
- with a fault also present, /S and /R are both low → Q = /Q = 1, the NAND
  latch's **forbidden state**, `FAULT` and `FAULT_LATCH_CLEAR` asserted together;
- `U_LATCHA` degenerates to `FAULT` = NOT(`FAULT_SET_N`) — a combinational
  repeater. **The latch never latches.**

**What survives:** the LIVE terms. `WD_OK`, `ESTOP_OK`, `TEMP_OK` still gate the
rail and the contactor *while the fault is present*. **What is lost is MEMORY** —
a fault that clears (a camera cooling by 1 °C, a watchdog restored, an E-stop
released) re-permits cooking with no re-arm. That is precisely what ADR-0011 §2
and the v1.2 TEMP_OK-into-SET fix exist for.

`ORDER_README` §7 step 3 says "Pulse REARM_N low". **Nothing in hardware
enforces a pulse.**

### 3.3 The power-up property the audit credits — CONFIRMED, with its two datasheet facts

At every power-up `WD_OK` is LOW for the TPS3823 reset delay (t_d = 120 / 200 /
300 ms, datasheet §6.8 via `02_parts/TPS3823-33DBVR/part.yaml`) → `FAULT_SET_N`
low → the latch is **FORCED SET**, so the coil rail cannot come up after any
power interruption without an explicit re-arm.

The second fact that makes it work: MCP23017 `IODIR` POR value is `1111 1111`
(DS20001952C register tables), so **GPA5 is an INPUT at power-on** and
`R_REARMPU` holds `REARM_N` high. Neither fact was written down anywhere on this
board before v1.6.

### 3.4 NEW — the defeat survives every Pi reboot

    EXP_RST_N -> R_EXPRST.1 , U_EXP.18

**No driver.** Nothing on this board can reset the expander; its registers hold
until 3V3 drops. So a held-low `REARM_N` does NOT survive a 3V3 power cycle
(§3.3) but **does survive every Pi reboot**. This board's own
`electrical_invariants.yaml` already records that mechanism — in the `why:` for
`R_WDPETPD`, about the retained `CONTACTOR_REQ` latch — and it had never been
applied to `REARM_N`.

### 3.5 What v1.6 ships

`ORDER_README` §7a-1: the driver invariant, this analysis, and a **REQUIRED
negative bring-up test** — hold `REARM_N` low, induce a fault, clear it, and the
rail must not return. On this revision it will; the tester is told to expect that
and to record the result. §7 step 3 now says PULSE in bold with a pointer.
Hardware fix (an edge-detect / one-shot on `REARM_N`) is deferred to the next
electrical revision.

---

## 4. WHAT IS NOW MACHINE-CHECKED THAT WAS NOT

`03_src/rules/electrical_invariants.yaml` gains two `part_value` asserts, taking
E-INV from **83/83 to 85/85**:

| invariant | why it is load-bearing |
|---|---|
| `R_COILENPD` equals `100k` | §10.2's published `R ≤ 175 kΩ` bound is COMPUTED from this value. A silent decade change moves the published number while every existence and direction assert stays green. |
| `R_REARMPU` equals `100k` | the only restraint on the re-arm line, and the resistor that makes §3.3's power-up-forced-SET property work. |

**RED-VERIFIED** (canon "test the checkers"): substituting `10k` for either
expected value makes `electrical_invariants.py` report
`E-INV FAIL: 2/85 invariants violated`, naming both parts and both actual
values. Restored; the shipped file asserts `100k` and the gate reads 85/85.

---

## 5. WHAT IS **NOT** CLOSED, NAMED RATHER THAN HIDDEN

1. **The copper.** A1's real fix (keyed/different housing for `J_MODE`, or
   `COIL_EN` off a field connector), A2's four-to-eleven pull-downs and A3's
   `REARM_N` edge-detect are all board changes. This is a documentation-only
   supersede: `fab/`, `source/` and `3d/` are byte-identical to v1.5's.
   **All three are USER DECISIONS for the next electrical revision.**
2. **`03_tscircuit/src/cooksense.tsx:551` still carries the falsified clause.**
   That file is inside the docs-only supersede's byte-identity set; the reasoning
   for leaving it, and the alternative that was considered and rejected, is in
   the v1.6 CHANGELOG entry. The clause is corrected in `ORDER_README` §13 gap 20
   and in this file, and it is OWED to the revision that adds the pull-downs —
   the same change that makes the sentence true.
3. **`02_parts/SN74HC14DR/part.yaml`'s gotcha is stale** ("unused inputs
   3A/4A/5A/6A tied GND" — all six gates are used). Recorded as declared gap 22;
   grouped with item 2 so one revision fixes the whole inherited-prose family.
4. **`cooksense.tsx:632` contradicts `cooksense.tsx:637-638`** about which
   `J_MODE` pole is which; the netlist says line 632 is the stale one. Recorded
   as declared gap 23, with `ORDER_README` §10.1's table named as the harness
   authority in its place.

*Tools: a hand-written s-expression tokeniser/parser over `cooksense.net`, plus
set arithmetic. Datasheet facts read from the PDFs and dossiers in `02_parts/`
(`pdftotext -layout` on DS20001952C). None of them is the generator, the
exporter, or `policy_audit` (canon M1).*
