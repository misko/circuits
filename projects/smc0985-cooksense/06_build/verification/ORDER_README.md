# ORDER README — cooksense MAIN board **v1.3** (project smc0985-cooksense)

---

## ORDERABLE — all gates green

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
   | **all copper, all layers** (pads + tracks + FILLED pours) | **2.0000 mm** | CONTACTOR_C at `J_ISOLOOP.1` → **GND zone edge**, F.Cu |
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
H1 and H2 rows are superseded), all against 6.000 mm:

| Hole | a (keypad approach) | s (SELV approach) | governing figure | verdict |
|---|---|---|---|---|
| H1 | **−0.050** (track KP_D1) | 13.631 (pad K_U1.2) | keypad-BONDED -> s alone = 13.631 | PASS |
| H2 | **−0.050** (track KP_U6) | 13.000 (pad K_STOP.1) | keypad-BONDED -> s alone = 13.000 | PASS |
| H3 | 40.933 (pad K_U1.4) | −1.450 (GND pour) | SELV-bonded -> a alone = 40.933 | PASS |
| H4 | **6.598** (pad K_STOP.3, RSTOP_MID; around the notch) | −1.450 (GND pour) | SELV-bonded -> a alone = 6.598 | PASS |

**H1 and H2 changed sign when the board was routed, and the verdict logic is why
that is still a PASS.** On track-free copper the nearest keypad copper to those
two fasteners was a pad, 2.305 mm and 3.129 mm away. On the routed board a
keypad TRACK passes under each fastener disc (a = −0.050 mm, i.e. touching), so
each fastener is now KEYPAD-BONDED and the requirement becomes the SELV approach
`s` alone — 13.631 mm and 13.000 mm, both far clear. The per-hole rule is
`a + s >= 6.000` with a negative approach meaning "bonded to that domain, so
measure the other side alone". Nothing got worse; the binding item changed.

**H4 is the tight hole at 6.598 mm** (the surface path around the isolation
notch, not a straight line — a straight line measures 4.617 mm and runs through
a through-cut). The previously reported 8.500 mm does not reproduce. Do not let
a rework shrink the notch or grow keypad copper near it.

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
an edge notch milled at x[191.50, 200.10] y[48.8, 49.8] (board coordinates).
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

## 3. JLCPCB order options

| Setting | Value |
|---|---|
| Layers | **4** (In1 = GND plane, In2 = 3V3 plane; NO plane north of y53 — keypad band, relay row, pockets and coil gaps are plane-free) |
| Dimensions | 188 × 92 mm; 12 milled 0.6 mm isolation slots on Edge.Cuts **plus the H4 east-edge notch (§1)** — confirm the fab preview keeps the slots as internal routs and the notch as outline |
| Via tier | **ADVANCED small-via option required** — 0.25 mm via / 0.15 mm drill (via-in-pad escapes). Do NOT order standard 0.45/0.30. |
| Assembly | Standard SMT, TOP side only (assembly.yaml: 0 footprints on B.Cu), qty 5 (JLC minimum for this board; A-STOCK grades stock at qty × 5). BOM + CPL regenerated at v1.3 seal — the current `06_build/fab/` set is v1.2-STALE, do not upload it. |
| CPL population | The **16** self-supplied refs (§4) carry `exclude_from_pos_files` in v1.3 source — they are OFF the CPL entirely. **189 CPL rows**, all rotation-sourced from measured per-LCSC rows and all on the pad-centre datum (worst deviation 0.0000 mm). The v1.1 instruction to "expect and ignore the unmatched-CPL warning" is OBSOLETE: if the preview shows unmatched CPL entries at v1.3, that is a real defect, stop. |

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

CPL rotation is this board's proven failure mode (v1.0/v1.1 banner). **That
investigation is now CLOSED: every one of the 189 CPL rotations resolves from a
MEASURED per-LCSC row** (A-ROT green, `jlc_rotation_audit --table` 61 rows OK),
so nothing below is guesswork any more. What remains is a narrower and sharper
obligation.

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
| 1 | **U_OPTO** (LTV-817S, C125121, SMDIP-4) | Pin-1 dot on the JLC render matches OUR silk pin-1 (LED side, west). Measured rotations disagree three ways (name-DB 0 / twin 270 / independent fit 90) — the preview IS the adjudication. A rotated opto swaps LED and transistor sides across the isolation barrier. |
| 2 | **J_DOOR** (JST-GH SM05B, C189896) | Mouth faces EAST (board edge); pin-1 position matches silk. |
| 3 | **J_ESTOP** (JST-GH SM05B, C189896) | Mouth EAST; pin 1 = 3V3 end per silk. |
| 4 | **J_MODE** (JST-GH SM05B, C189896) | Mouth EAST; pin-1 matches silk. |
| 5 | **J_RH_AMBIENT** (JST-GH SM05B, C189896) | Mouth SOUTH; pin-1 matches silk. |
| 6 | **J_RH_EXHAUST** (JST-GH SM05B, C189896) | Mouth SOUTH; pin-1 matches silk. |
| 7 | **J_THERM_A** (JST-GH SM08B, C265111) | Mouth SOUTH; pin-1 matches silk. |
| 8 | **J_THERM_B** (JST-GH SM08B, C265111) | Mouth SOUTH; pin-1 matches silk. |
| 9 | **J_KEY_MATRIX** (JST-GH SM10B, C2683602) | Mouth WEST (keypad ribbon); pin-1 matches silk. One of the three disputed codes — check with care. |
| 10 | **J_PWR** (Molex Micro-Fit, C587657) | Polarizing peg orientation AND pin-1 (5 V) position vs silk. Suggested-180 measurement did not separate (2.9×) — the preview decides. |
| 11 | **J_LOADCELL** (JST-XH B5B-XH-A, C157991) | Pin-1 vs silk; boss/keying orientation. Suggested-180 at 1.4× — noise; preview decides. |
| 12 | **CE1** (220 µF POLARIZED electrolytic, C2887273) | **v1.0 AND v1.1 shipped this cap at rotation 180 = REVERSED across a live 5 V rail.** Confirm the "+" / crescent on the render matches OUR pad 1 (west end, net 5V_PROTECTED). The measured `C2887273,0` row now governs and the export deliberately raises ROT-XCHECK-180 against the stale name-DB rule. Independent fit says 0 at 126.6×; "polarized part shipped reversed" is verbatim the usb-hub-3s-v3 v1.5 incident. |
| 13 | **J_PI** (2×20 socket, C35165) | Carried from v1.1: JLC's library winds pin numbering by ROW where ours winds by COLUMN (adjudicated MIRRORED finding — symmetric hole grid, no physical mirror possible). Confirm the part sits ON the grid; pin-1 identity comes from our netlist + silk, not JLC's numbering. |
| 14 | **SOIC-16 (U_DECU/U_DECD, C5620/C10092)** | Carried from v1.1: ROT-DB-SUGGEST 90° class — confirm pin-1. |
| 15 | **All diode cathode bands — ALL EIGHT** (D_ESD_IN, D_ESTOP, D_DOOR, D_LCCLK, D_LCDAT, D_REVCLAMP, D_TVS, **D_KSTOP**) | Band matches silk on every one. **D_KSTOP is the K_STOP coil flyback** (`.1 -> 5V_STOP`, `.2 -> COIL_STOP_N`): reversed it is a forward-biased short from the STOP rail into the coil driver and the STOP relay loses its clamp. It was missing from this list until 2026-07-26. **Note why D_KSTOP (C8678) and D_TVS (C113974) are NOT in the A-POL list above but ARE here:** the A-POL list names parts with NO numbering-free channel; these two HAVE one — their cathode band was measured as a SHAPE on both libraries and they carry `two-channel` rows. This row is the separate obligation to eyeball a POLARIZED part. Two different questions; conflating them is what once left D_KSTOP off. |
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
the north caption band. It is deliberately NOT beside the block: a full scan for
a free silkscreen box against pads, existing silk and every courtyard put the
nearest visible site 41.9 mm away, because that corner is saturated. **Use this
legend, not the board, to identify the poles.**

Rating (unchanged): the loop is the LTV-817S opto DRY CONTACT — design bound
**<= 30 V / <= 50 mA** (LTV-817 collector abs-max 50 mA is the limiting
element). Do not repurpose this loop to switch a contactor coil directly. The
nets carry the ISO_CONTACTOR netclass and the `opto_isolation_2mm` DRU rule
(IEC 60664-1 basic insulation, 30 V working, pollution degree 3, material group
IIIa), which is **GREEN on v1.3 routed copper**. Minimum over ALL copper on ALL
layers (pads, tracks and filled pours) is **2.0000 mm**, at CONTACTOR_C on
`J_ISOLOOP.1` against the **GND zone edge** on F.Cu — margin 0.000 mm by
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
| A-POL | 10 codes / 13 refs single-channel -> §6 human gate |
| I-HW (mounting-hardware creepage) | PASS, H4 the tight hole at 6.598 mm |
| ISO barrier (`opto_isolation_2mm`) | **2.0000 mm**, all copper all layers incl. filled pours (GND zone edge at J_ISOLOOP.1). Pad-to-pad true polygon: 2.1709 mm. Margin 0.000 by construction — the moat keepout IS the 2.0 mm offset. |
| M-REPRO | 3 from-source rebuilds, **1047** vias each, identical fp/track/via hashes, matching the shipped board |
| Stranded pour islands | 136 islands, **136 bonded, 0 stranded** |
| jlc_twin | 184 OK, 184 MODEL-REG-OK, 31 PAD-GEOM + 9 POLARITY-FIT + 1 MIRRORED + 1 FETCH-FAILED/NO-BODY, **all adjudicated** |
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
   rule at 2.126 mm measured, and the land's own 7.530 mm clear strip).
3. **P-FACT has no kind for "off the CPL but on the BOM as a buy-line."**
   Three of the 16 self-supplied refs (J_ISOLOOP, J_LOADCELL, J_PI) are
   deliberately coded on the BOM and excluded from the CPL. The nearest assert,
   `not_on_assembly_bom`, conflates "not placed" with "not purchased".
4. **Our SOD-323 land draws a cathode band on a bidirectional part** (D_DOOR,
   D_ESD_IN, D_ESTOP, D_LCCLK, D_LCDAT). Assembly risk is nil — JLC places from
   the CPL, not our silk — but a reviewer hand-checking the board may "correct"
   a placement that was already right. v1.4.
5. **⚠️ THE 22 k CLAMPS CHANGED THE CH0/CH3 ADC TRANSFER FUNCTION, AND §2b's
   MANDATORY HOST CHECK IS SPECIFIED AGAINST THE OLD CURVE.** `R_CLMPA`/`R_CLMPB`
   (22 k to GND) were added to keep an open head inside the comparator's
   common-mode range. They also load the camera-A/B thermistor dividers, so
   **ADC CH0 and CH3 no longer share the conversion the other six channels use.**
   If the host applies the unmodified 10 k/NTC model (B25/85 = 3987, R25 = 10 k):

   | true | reported |
   |---|---|
   | 0 °C | 18.7 °C |
   | 25 °C | 33.6 °C |
   | 70 °C | 72.3 °C |

   It over-reads, which is conservative for a limit test, but it destroys
   absolute accuracy and any cross-channel plausibility check — and §2b makes a
   host runtime thermistor cross-check a **MANDATORY acceptance item**. **Derive
   the CH0/CH3 curve with the 22 k clamp in the model before you rely on §2b.**
   No document in this archive states the corrected curve; that is the gap.
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
9. **M-REPRO is green by metric, not by bytes.** Three from-source rebuilds are
   geometrically identical, but the files differ because the generator mints
   fresh UUIDs and KiCad serialises footprints in UUID order. A fleet-level fix
   is owned elsewhere; on this board the nondeterminism never reaches a via
   decision (via count has not varied across 5 observed builds).
