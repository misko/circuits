# ADR-0018 — J_MODE leaves the JST-GH family, and COIL_EN is hardened
# against an injected pull-up (v1.7)

status: accepted
date: 2026-07-28
tags: protection, topology
supersedes-in-part: DISPOSITIONS #6 (2026-07-23 pin-review-Q J_MODE re-pinning)

## The defect this closes

v1.6 (`verification/crossplug_and_permission_defaults.md` §1, re-verified from
`source/cooksense.net` by an independent s-expression parser) established:

- `fab/bom.csv` line 45 ships **five** identical `C189896` SM05B-GHS-TB
  housings — `J_DOOR, J_ESTOP, J_MODE, J_RH_AMBIENT, J_RH_EXHAUST`. One part,
  one footprint, nothing mechanical to tell them apart.
- `COIL_EN` had exactly three nodes: `J_MODE.4`, `Q_COILDRV.1` (the 2N7002
  GATE), `R_COILENPD.1`. **No ESD device, no series element**, sole hold
  `R_COILENPD` = 100 kΩ.
- An SHT45 pod harness plugged into `J_MODE` powers up normally from pin 1 and
  lands its module SCL pull-up on `COIL_EN`: **3.000 V** at 10 kΩ, **3.152 V**
  at 4.7 kΩ, both above the 2N7002's **2.5 V max** `V_GS(th)`. The relay coil
  rail comes up with **all seven AND-chain terms and the Manual rail-cut
  bypassed** — the rail cut *is* the pin 3 → pin 4 pole, and the cross-plug
  drives pin 4 directly.
- Root cause was a MODEL error, not arithmetic: the 2026-07-23 re-pinning
  reasoned that "any cross-plug **bridge** either applies the intended gating
  or holds the rail OFF". That is the right model for three dry-contact
  harnesses and the wrong model for a harness that **sources current**.

## What was measured before choosing (the cost side)

The east connector column is SATURATED. Courtyard gaps, from the v1.6 board:

| pair | gap (mm) |
|---|---|
| H4 → J_MODE | 0.058 |
| J_MODE → J_ESTOP | 0.080 |
| J_ESTOP → J_DOOR | 0.090 |
| J_DOOR → J_ISOLOOP | 0.510 |
| J_ISOLOOP → J_RH_EXHAUST | 0.160 |
| **total column slack** | **0.898** |

and the 2.0 mm ISO moat between `J_ISOLOOP` and `J_DOOR` measures 2.126 mm —
0.126 mm over the rule. Any connector that grows the column by more than
0.898 mm is an east-edge REPACK plus a re-derivation of that moat, which cost
a bounded solve the first time (floorplan.yaml, "THE MOAT IS 2-D").

Candidate courtyards, measured from the KiCad footprints:

| footprint | column width | depth | Δcolumn vs GH-5 |
|---|---|---|---|
| `JST_GH_SM05B-GHS-TB_1x05` (today) | 10.700 | 6.400 | — |
| `JST_ZH_S4B-ZR-SM4A-TF_1x04` | **10.500** | 8.000 | **−0.200** |
| `JST_ZH_S5B-ZR-SM4A-TF_1x05` | 12.000 | 8.000 | +1.300 (does not fit) |
| `JST_PH_S4B-PH-SM4-TB_1x04` | 13.200 | 10.200 | +2.500 (does not fit) |
| `JST_GH_SM04B-GHS-TB_1x04` | 9.460 | 6.400 | −1.240 |

## Options considered

**(A) Trim `R_COILENPD` 100 kΩ → 10 kΩ.** REJECTED as insufficient, and it was
already measured insufficient in v1.6 §10.6: 3.3 · 10/20 = **1.65 V**, still
above the 2N7002's 1.0 V *minimum* `V_GS(th)`, so a weak-threshold device
conducts. Attenuation without a threshold argument is not a fix.

**(B) Move `COIL_EN` off a field connector entirely.** REJECTED on the merits.
Every variant re-derived here puts a *different* node on the field pin and the
hazard follows it:
 - Making `COIL_EN` on-board and using pole A only as a logic term replaces a
   PHYSICAL rail cut with a logic AND. BRIEF.md:88 defines Manual as "relay
   power **physically** disabled"; a gate is not that.
 - Putting pole A in the `Q_COILDRV` drain path, or having MANUAL clamp
   `HS_GATE_COIL` to its source, both expose `HS_GATE_COIL` on a field pin. A
   10 kΩ pod pull-up to 3.3 V against `R_HSG` 100 kΩ to 5 V lands that node at
   3.3 + 1.7·(10/110) = **3.45 V**, i.e. `V_GS(Q_COIL)` = **−1.55 V** on an
   AO3401A whose threshold magnitude is at most 1.0 V — **the P-FET turns on**.
   The variant only works if `R_HSG` drops to 1 kΩ, at which point it is a
   bigger change than (C)+(D) for a worse safety property.

**(C) MECHANICAL KEY — move `J_MODE` to a non-mating family. CHOSEN.**

**(D) Series element + strong pull-down divider on `COIL_EN`. ALSO CHOSEN**, as
the second layer. A key cannot fix a **mis-built** J_MODE harness, and this
board's harnesses are hand-crimped in the field.

**(E) Pin-count key inside the GH family (`SM04B-GHS-TB`, 4 circuits).**
REJECTED ON SOURCING, and the sourcing is decisive rather than aesthetic:
genuine JST reads **C20584968 stockCount 0** and **C189895 stockCount 1**
(live catalog, 2026-07-28). The only stocked 4-circuit GH is
`XY-SM04B-GHS-TB` (XYECONN, stock 19 186) — a clone on the one connector whose
mis-mate arms a cooking machine, against an ORDER_README that is otherwise
DO-NOT-SUBSTITUTE. It would have been the cheapest option on placement
(−1.240 mm of column, zero added depth); it is not available as a genuine part.

## The decision

### C — `J_MODE` becomes a JST **ZH** 4-circuit side-entry SMD header

`S4B-ZR-SM4A-TF`, **LCSC C485354**, genuine JST, **stockCount 10 760,
minPurchaseNum 1** (live catalog read 2026-07-28).

Pinout — 4 circuits is exactly what a dry DPDT needs, and the 5th (GND/shield)
pin the GH housing carried was never used by the mode harness:

| pin | net | pole |
|---|---|---|
| 1 | `3V3` | pole B feed (mode sense) |
| 2 | `MODE_RAW` | pole B return |
| 3 | `KEY_RELAY_ALLOWED` | pole A feed (the physical rail cut) |
| 4 | `COIL_EN_IN` | pole A return |

**WHY THE MIS-MATE IS PHYSICALLY IMPOSSIBLE IN THE DIRECTION THAT MATTERS —
the two JST drawings, cited.** The hazard direction is a *GH plug into
`J_MODE`* (both ☠ cells, and the two ○ cells):

- `eGH.pdf` p.2 Housing table: `GHR-05V-S` is A = 5.00, B = 7.50, and the
  housing cross-section on that drawing is **4.15 mm** (height) × 5.7 mm.
- `eZH.pdf` p.4 Header/SMT/SM4 table: `S4B-ZR-SM4A-TF` is A = 4.5, B = 9.0, and
  the side-entry header drawing's height dimension is **3.70 mm**; its cavity
  holds a `ZHR-4` housing whose drawing height is **3.40 mm**.

A 4.15 mm-tall GH plug cannot enter a header whose **entire outer height is
3.70 mm** — a 0.45 mm interference against the outer envelope and 0.75 mm
against the cavity. Independently, the pitches differ (1.25 vs 1.50 mm), so
even a hypothetical entry aligns at most one circuit.

**WHAT THIS DOES *NOT* BLOCK, STATED PLAINLY.** `GHR-05V-S` and `ZHR-4` have
the *same* overall housing width, B = 7.50 mm on both drawings, and the ZH
plug is smaller in every other dimension. So the REVERSE direction — the
J_MODE ZH plug pushed into a GH socket — is **degraded, not blocked**: it
cannot latch, and its 1.50 mm contacts cannot engage 1.25 mm posts on more
than one circuit, but it is not a mechanical interference. That direction is
the benign one: a MODE harness is dry contacts, and in a pod socket it can only
short a current-limited switched rail (⚡, loud) and in `J_DOOR`/`J_ESTOP` only
mis-report a permission (✗). **The claim this ADR makes is bounded to the
direction it proves**, which is the failure of the claim v1.6 withdrew.

Cross-plug matrix effect, against v1.6 ORDER_README §10.4's twenty cells:

| class | v1.6 | v1.7 | why |
|---|---|---|---|
| ☠ energises the coil rail | 2 | **0** | GH plug cannot enter the ZH shroud |
| ○ input falsified, rail cannot arm | 2 | **0** | same |
| ⚡ rail short | 7 | 7 (4 unlatched) | reverse direction, degraded only |
| ✗ permission forced permissive | 3 | 3 (2 unlatched) | reverse direction, degraded only |
| ? driven into the threshold band | 4 | 4 | pod → J_DOOR/J_ESTOP, untouched |
| ↔ silent pod transposition | 2 | 2 | untouched — both pods are still GH-5 |

**RATINGS — checked, and NOT a regression.** ZH is 1.0 A / 50 V (eZH p.1),
identical to GH's 1.0 A / 50 V (eGH p.1). Temperature range is ZH **−25 to
+85 °C** against GH's −40 to +105 °C, which is narrower *for the connector* —
but the board's own binding envelope is **`DIP05-1A72-12L` at −20 to +70 °C**
(`02_parts/DIP05-1A72-12L/part.yaml`, the twelve reed relays), tighter than the
ZH connector at both ends. **The board's operating envelope does not move.**

**RETENTION — a real loss, and it fails in the safe direction.** GH's selling
point over ZH is a positive outer latch (eGH p.1, "Secure lock mechanism…
Large outer latch for positive lock"); ZH is a housing-lance friction retention
(eZH p.1). If the `J_MODE` plug backs out: `COIL_EN_IN` is held at 0 V by
`R_COILENPD` → coil rail OFF, and `MODE_RAW` falls → `MODE_AUTO_HW` = 0 →
the AND-chain drops anyway. **An unplugged J_MODE is fail-safe; the cost is
availability, not safety.** ORDER_README §10.5 item 2 already mandates a
permanent mechanical marker at that housing; it now also carries a cable-tie
strain relief requirement.

**PLACEMENT COST, measured.** `J_MODE` anchor moves 197.00 → **195.70** so the
mouth face lands 199.70 (v1.6's GH mouth: 199.45) and the courtyard occupies
x[192.20, 200.20] — the same east limit the GH held. The column gets 0.200 mm
*wider* slack. Westward the courtyard grows 1.85 mm into a strip whose only
occupant is `R_MODEPD`, a 0402 with a movable anchor. **No other part moves;
the ISO moat is untouched.**

### D — the `COIL_EN` front end

`COIL_EN` is SPLIT at a series element:

    J_MODE.4 ── COIL_EN_IN ──┬── R_COILENPD 680R ── GND
                             ├── D_COILEN (PESD5V0S1BA) ── GND
                             └── R_COILENS 680R ── COIL_EN ── Q_COILDRV.1 (G)

The pull-down sits **at the connector pin, not at the gate**, and that ordering
is the whole trick: the gate draws no DC, so the series resistor drops **zero
volts on the legitimate path** while the divider acts in full on an injected
source.

**WORST CASE, LEGITIMATE DRIVE — must clear `V_GS(th)` MAX = 2.5 V.**
`U_AND3.Y` (SN74LVC1G11) → `J_MODE.3` → DPDT pole A → `J_MODE.4`.
The rail is taken at its LOW end, **3.201 V** (the AMS1117-3.3
datasheet-cited `vout_min` already in `power_tree.yaml`), because a low rail is
the worst case for clearing a threshold. The '1G11 output is
modelled at its own datasheet floor, V_OH ≥ 2.4 V at I_OH = 12 mA and
V_CC = 3.0 V ⇒ R_on ≤ 50 Ω:

    V(COIL_EN) = 3.201 · 680/(680 + 50) = 2.982 V
    margin over V_GS(th) max 2.5 V       = +482 mV  (19%)

and the FET only has to sink 45 µA (5.0 V − 0.5 V over `R_HSG` 100 kΩ). A
worst-case 2.5 V-threshold 2N7002 at V_GS = 2.98 V has 0.48 V of overdrive;
scaling from its own I_D(on) point (0.5 A at V_GS = 10 V ⇒ K ≈ 8.9 mA/V²) gives
I_D ≈ 8.9 m · 0.48² ≈ **2.05 mA**, **45×** the 45 µA required. Load on the gate
driver is 3.201/680 = **4.7 mA**, against ±32 mA of '1G11 drive.

**WORST CASE, INJECTED PULL-UP — must stay under `V_GS(th)` MIN = 1.0 V**, the
level at which even the weakest device in the specification window reaches its
250 µA definition current:

| injected pull-up | source | V(`COIL_EN_IN`) = 3.3 · 680/(680+R) | v1.6 (100 kΩ) |
|---|---|---|---|
| 10 kΩ | `DETAIL_DESIGN.md:114`, "SHT pods carry module 10k pullups" | **0.210 V** | 3.000 V |
| 4.7 kΩ | `BRIEF.md` C7, Adafruit-class module | **0.417 V** | 3.152 V |
| 2.2 kΩ | **this board's own I2C pull-up value** (`R_SCLA`/`R_SDAA`…) | **0.779 V** | 3.229 V |

General bound: V ≤ 1.0 V ⇒ **R ≥ 1 564 Ω**. Every realistic I2C pull-up is
rejected. The same bound at 100 kΩ was R ≥ 230 kΩ — i.e. **nothing** was
rejected. `R_COILENS` = 680 Ω (same value, so **one** new BOM line covers both
refs) is the series element and the ESD current limit; `D_COILEN`
(PESD5V0S1BA, `C5158048`) is the ESD device `J_DOOR` and `J_ESTOP` already
carry and `J_MODE` did not — an existing BOM line, a 6th ref.

**WHAT THE DIVIDER STILL CANNOT DO, STATED.** A **hard short** of
`COIL_EN_IN` to 3V3 (zero source impedance) still arms the rail. No resistor
value defends against that, which is precisely why the mechanical key is the
PRIMARY fix and the divider is the second layer, not the other way round.

## Invariants emitted (E-INV / E-ADR)

- `part_value` `R_COILENPD` = `680` — the number the whole rejection bound is
  computed from; a silent decade change would move a published safety figure
  while every existence assert stayed green (this is exactly how `R_WDPETPD`
  and `R_OPENT` were nearly shipped wrong).
- `part_value` `R_COILENS` = `680`.
- `pin_on_net` `J_MODE.4` = `COIL_EN_IN` — the connector pin is on the INPUT
  side of the series element, never on the gate node.
- `pin_on_net` `Q_COILDRV.1` = `COIL_EN` — and `COIL_EN` reaches the field only
  through `R_COILENS`.
- `net_has_part` `COIL_EN_IN` diode ≥ 1 — the ESD device exists.
