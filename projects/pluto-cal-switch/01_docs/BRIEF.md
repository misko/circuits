# BRIEF — pluto-cal-switch

A 5-port SMA RF adapter that switches two PlutoPlus RX channels between two
antennas and a TX-fed calibration loopback.

## The commission, verbatim

sha256 of the block below (exact bytes, trailing newline included):
`052961368abb7d795575a68b4b035d36ca493ecc2c661349ed3c177bcbb5fde6`

<!-- prompt-verbatim-begin -->
an adapter with 5 SMA ports, (2 RX antenna, 2 RX PlutoPlus, 1 TX pluto plus). Along with a GPIO interface to switch , 

GPIO = off
2 RX pluto plus connect to 2 RX antenna

GPIO = on
1 TX pluto plus goes through 30db attenuation and feeds back into both RX pluto ports (same path length on each run)
<!-- prompt-verbatim-end -->

- date: 2026-07-27
- channel: interactive commission (`/pcb-design`)

## Parsed requirements

| P# | Requirement | Source |
|---|---|---|
| P1 | **5 SMA ports**: 2× RX antenna in, 2× RX to PlutoPlus, 1× TX from PlutoPlus | verbatim |
| P2 | **Control interface switches between two states** | verbatim ("GPIO interface to switch") |
| P3 | **State A (control OFF)** — each RX antenna connects to its own PlutoPlus RX port | verbatim |
| P4 | **State B (control ON)** — PlutoPlus TX passes through attenuation and feeds BOTH PlutoPlus RX ports | verbatim |
| P5 | **30 dB attenuation** on the loopback path | verbatim, scoped by A2 |
| P6 | **Same path length on each loopback run** | verbatim, relaxed by A6/A7 |

## Questions and answers

| Q# | Question | A# | Answer |
|---|---|---|---|
| Q1 | Frequency range? | A1 | **70 MHz – 6 GHz**, the full PlutoPlus range |
| Q2 | Is 30 dB the attenuator pad alone, or total TX→RX? | A2 | **30 dB TOTAL, TX → each RX** |
| Q3 | Which control state is the loopback? (the follow-up answer contradicted the verbatim brief) | A3 | **As briefed: ON = loopback.** The verbatim polarity stands |
| Q4 | Power and control interface? | A4 | 5 V USB; **state controllable over USB** (asked back, answered yes) |
| Q5 | USB connector? | A5 | **Micro-USB**, 5 V *(supersedes an earlier "USB-A dongle" answer — user corrected mid-commission)* |
| Q6 | Loopback length-match tolerance? | A6 | **Not tight** — "as long as distance is precisely known, it will be software offset" |
| Q7 | — follow-up | A7 | **"but lets try to make them the exact same if possible"** |

## Decisions

| D# | Decision | Rationale |
|---|---|---|
| D1 | **Resistive 2-way splitter, not Wilkinson** | A1 forces it. A Wilkinson λ/4 at 70 MHz is ~400 mm on FR4 — physically impossible on this board. A resistive split is DC-coupled, inherently wideband, exactly symmetric, and costs 6 dB. To be confirmed against a wideband MMIC/LTCC alternative in the sourcing spike. |
| D2 | **Attenuator pad ≈ 30 dB − splitter loss − switch loss** | A2 pins the TOTAL. Exact value derived in DETAIL_DESIGN once the splitter and switch losses are measured from datasheets, not assumed. |
| D3 | **MCU owns the control line; GPIO header retained** | A4 asks for USB control; P2 asks for GPIO. Both are satisfied by an MCU that accepts either, rather than trading one for the other. Part selection in the sourcing spike. |
| D4 | **Length match: design for exact symmetry, then MEASURE and PUBLISH the residual** | A6+A7 together are not "loose" — they are a *documentation* requirement. Mirror the layout about the splitter so the runs are identical by construction; then the release must STATE each run's electrical length and their delta, because software offset is only as good as the number it is given. This becomes a release artifact, not just a routing goal. |

### D# assumptions made in the user's ABSENCE — all three flagged in the report

Per SKILL.md's SPEC-CHECK rule: take the SIMPLEST reading that satisfies the
stated requirement, record it as a `D#`, and surface it LOUDLY. **None of these
three has been confirmed by the user, and each is cheap to reverse.**

| D# | Question the user has not answered | Assumption taken | Cost to reverse |
|---|---|---|---|
| **D5** | **"30 dB total" at WHICH frequency?** The chain tilts **3.09 dB** across 70 MHz-6 GHz (mostly microstrip loss on the stackup the parts force), so 30 dB cannot be true at both ends. | **MINIMAX** — the pad value minimizing the worst-case deviation, privileging no frequency. **30 dB is met at ~3.0 GHz; the band span is 30.0 -1.6 / +1.4 dB** (guaranteed unit-to-unit envelope 27.2-32.9 dB). ADR-0013. | **ONE BOM line**, same footprint, 2 placements: reference 70 MHz / 648 MHz => arm pad becomes YAT-3A+; 6 GHz => drop the arm's second chip. |
| **D6** | **Which PlutoPlus?** Two physical units were measured and they DIFFER: genuine span **35.04 mm**, clone **34.72 mm**. | **Design to the 34.88 mm MIDPOINT**, so each board sits +/-0.16 mm off nominal on EITHER unit — inside SMP's +/-0.25-0.30 mm float. ADR-0014. | **One number in `floorplan.yaml`** (the three SMP anchor X coords). No part changes. But it spends +/-0.16 mm of a +/-0.25-0.30 mm budget before fab tolerance is counted. |
| **D7** | **Which control surface WINS** when USB and the GPIO header disagree? | `RF_CTRL = HEADER_level OR USB_bit`, **plus a 10 s USB watchdog** that clears the USB bit if the host goes silent — so the header always regains authority within 10 s and the safe state is always reachable. ADR-0008. | **Firmware only.** No hardware change. |

## Spec tensions (D-SPEC)

| # | Tension | Status | ADR | flagged |
|---|---|---|---|---|
| T1 | 70 MHz–6 GHz vs. printed Wilkinson | **RESOLVED by D1** — resistive split, and **CONFIRMED and strengthened at design stage**: λ/4 at 70 MHz is **601 mm**, not ~400 mm, and a SECOND independent refutation applies — the required bandwidth ratio is **85.7:1** where published multi-section Wilkinsons top out near 10–20:1. Cost: 6.02 dB, accounted in D2. | [0003](decisions/0003-resistive-delta-splitter.md) | yes |
| T2 | Control polarity: verbatim brief vs. follow-up answer | **RESOLVED by A3.** Recorded because the two disagreed; the brief wins. Note the consequence: with ON = loopback, an unpowered or floating control line defaults to **antenna** mode, which is the safe default — and that is now enforced by hardware in TWO independent ways (MCU reset pull-down + an external pull-down at each switch). | [0001](decisions/0001-control-polarity-and-power-on-default.md) | yes |
| T3 | "same path length" vs "software offset" | **RESOLVED by D4** — build symmetric, publish the measured delta. EXTENDED at design stage to include AMPLITUDE, because ADR-0004 put independent parts in the two arms. | [0011](decisions/0011-length-match-is-a-published-artifact.md) | yes |
| **T4** | **"30 dB TOTAL" is a SCALAR against a chain that tilts 3.09 dB.** Reading it as "30 dB at every frequency" makes it unsatisfiable by ANY design, not just this one. | **RESOLVED by D5** — minimax, and the release **publishes loss vs frequency, not a scalar**. Neither silently built out-of-spec nor silently downgraded. | [0013](decisions/0013-spec-tension-30db-is-a-curve.md) | **yes — LOUDLY** |
| **T5** | **The mating geometry is ambiguous**: two PlutoPlus units measured 0.32 mm apart, and "Pluto+" names three different boards (2020 V1, a genuine 2021 V2 respin, and a 2025 knock-off with different artwork). | **RESOLVED by D6** — the 34.88 mm midpoint. | [0014](decisions/0014-spec-tension-which-plutoplus.md) | **yes — LOUDLY** |
| **T6** | **The GPIO header cannot be read as specified.** PlutoPlus IO is **1.8 V**; RP2040's VIH is a **flat 2.0 V** (not 0.65·IOVDD), and a Zynq HR bank's worst-case VOH at VCCO=1.8 V is **1.35 V**. A direct connection reads permanently LOW — and the failure is FAIL-SAFE, so it passes every "can it spuriously enter loopback" test and surfaces only as "the GPIO control doesn't work", plausibly after seal. There is also a REVERSE hazard: RP2040 VOH 2.62–3.3 V into a Zynq pin whose absolute max is ~2.35 V. | **RESOLVED IN HARDWARE, not by downgrading P2**: the header lands on an **ADC pin** through a ÷2.5 divider, thresholded in firmware. Reads 1.8 / 3.3 / 5.0 V logic with no translator and no second rail, and is **input-only by construction** (an ADC-configured pin has its digital output disabled), so no firmware bug can drive the user's Pluto. | [0008](decisions/0008-control-surfaces-usb-and-gpio-header.md) | **yes** |
| **T7** | **">25 dB isolation" is not met on the guaranteed MINIMUM above ~5 GHz** by any cheap stocked SPDT — BGS12WN6 is 21 dB min / 28 typ and BGS12P2L6 24 min / 27 typ over 5150–5925 MHz. Typ meets it. | **STATED, not downgraded.** The only part found that brackets the whole band with >25 dB guaranteed at BOTH ends is HMC1118, at ~$15/board for two. Recorded as an available upgrade rather than silently assumed away. | [0002](decisions/0002-spdt-switch-bgs12wn6.md) | yes |

## Commission fact-lock

| Row | Value | Locked by |
|---|---|---|
| RF frequency range | 70 MHz – 6 GHz | A1 |
| Loopback total loss, TX → each RX | 30 dB | A2 |
| Control polarity | ON = loopback, OFF = antenna | A3 |
| Input envelope | 5 V, micro-USB | A4, A5 |
| Control surface | USB (CDC) **and** GPIO header | A4, D3 |
| Length-match obligation | symmetric by construction; **measured delta published** | A6, A7, D4 |
| TX drive level | ⚠️ **NOT LOCKED** — PlutoPlus TX max is ~+7 dBm; needs confirmation for attenuator power rating and RX overload margin | — |
| Impedance | 50 Ω, **controlled impedance REQUESTED** | pinned by ADR-0010: 4-layer `JLC04161H-7628`, 0.35 mm microstrip on the 0.2104 mm top prepreg |
| Reference frequency for the 30 dB | **≈3.0 GHz** (minimax); span 30.0 −1.6 / +1.4 dB | **D5 — assumed, user ABSENT** |
| PlutoPlus port span | **34.88 mm** (midpoint of genuine 35.04 / clone 34.72) | **D6 — assumed, user ABSENT** |
| Control resolution (USB vs header) | OR + 10 s USB watchdog | **D7 — assumed, user ABSENT** |
| GPIO header logic level | **1.8 / 3.3 / 5.0 V all accepted** (÷2.5 divider into an ADC pin) | D3 + ADR-0008; the 1.8 V case is what forced it |
| Board TX absolute ceiling | **+27 dBm** (0.5 W), binding element PAD_A1 at 1.7 W | derived, DETAIL_DESIGN §4.3 |
| Fab tier (D-TIER) | `jlc_4layer_advanced` — 0.25/0.15 mm vias | ADR-0010; forced independently by the BGS12WN6 ground via AND the RP2040 escape |
| Assembly service | JLC **Standard** PCBA, top side only | ADR-0010 + `assembly.yaml`: THT parts and a non-default stackup both exclude Economic |

## Decision register

Every ADR appears in exactly one row; every row's depth link exists.

| id | decision | decided by | depth |
|---|---|---|---|
| D1 | Resistive splitter, not Wilkinson | agent (P-delegation) | [ADR-0003](decisions/0003-resistive-delta-splitter.md) |
| D2 | Pad derived from measured splitter + switch loss | agent (P-delegation) | [ADR-0004](decisions/0004-attenuation-value-and-placement.md) |
| D3 | MCU owns the control line; GPIO header retained | agent (P-delegation) | [ADR-0008](decisions/0008-control-surfaces-usb-and-gpio-header.md) |
| D4 | Length match published, not toleranced | agent (P-delegation) | [ADR-0011](decisions/0011-length-match-is-a-published-artifact.md) |
| **D5** | 30 dB referenced by minimax ⇒ ≈3.0 GHz | **agent, user ABSENT** | [ADR-0013](decisions/0013-spec-tension-30db-is-a-curve.md) |
| **D6** | Build to the 34.88 mm PlutoPlus midpoint | **agent, user ABSENT** | [ADR-0014](decisions/0014-spec-tension-which-plutoplus.md) |
| **D7** | Control resolution = OR + 10 s USB watchdog | **agent, user ABSENT** | [ADR-0008](decisions/0008-control-surfaces-usb-and-gpio-header.md) |
| — | Control polarity + power-on state = ANTENNA, in hardware | user (A3) + agent | [ADR-0001](decisions/0001-control-polarity-and-power-on-default.md) |
| — | SPDT = BGS12WN6, BGS12P2L6 as a same-land dual source | agent (P-delegation) | [ADR-0002](decisions/0002-spdt-switch-bgs12wn6.md) |
| — | DC blocks on the ANTENNA ports only | agent (P-delegation) | [ADR-0005](decisions/0005-dc-coupling-posture.md) |
| — | Mating: SMA→SMP adapters + edge-launch SMP on-board | agent (P-delegation) | [ADR-0006](decisions/0006-mating-strategy-sma-to-smp.md) |
| — | Antenna SMA = KH-SMA-KE-Z, and the launch rules are OURS | agent (P-delegation) | [ADR-0007](decisions/0007-sma-antenna-connector-and-launch.md) |
| — | Input protection: what is fitted and what is deliberately absent | agent (P-delegation) | [ADR-0009](decisions/0009-input-protection-posture.md) |
| — | Stackup + fab tier: 4-layer JLC04161H-7628, ADVANCED | agent (D-TIER) | [ADR-0010](decisions/0010-stackup-and-fab-tier.md) |
| — | MCU = RP2040; CH32X035 datasheet-verified and BLOCKED | agent (P-delegation) | [ADR-0012](decisions/0012-mcu-selection-rp2040.md) |

## Open

Numbered so the report and `ARCHITECTURE.md` §12 can point at them.

- **TX drive level** — still the only user-facing fact-lock row open. At +7 dBm each RX sees −21 to −24 dBm, **22.7 dB below the AD936x abs max even in the worst case**. The board's own ceiling is now derived and stated at **+27 dBm** (DETAIL_DESIGN §4.3), so an external PA on TX is bounded rather than unbounded.
- **The three physical measurements this design is waiting on**, all five minutes each on a real PlutoPlus, and none of them blocks any RF work:
  1. **RF axis height above the Pluto's PCB** — not established. Our half IS now cited (2.00 mm above our board's top surface). Gates the board's Z position only.
  2. **SMA gender on the PlutoPlus** — INFERRED, not cited. The schematic says only `SMA-L`. $101 of adapters rides on it.
  3. **Port span** — caliper the three gaps and D6 retires entirely.
- **Are the PlutoPlus RF ports DC-free?** Asserted nowhere. All RF ports on both switches plus all three splitter ports are ONE galvanic node. If they are not DC-free, blocks become mandatory on the three SMP ports too (ADR-0005).
- **Will JLC place an edge-launch SMP?** In-library and purchasable is not placeable. Submit real gerbers + CPL to DFM before committing; the vertical fallback is pre-designed (ADR-0006).
- **The 12 MHz crystal is deliberately not selected.** The JLC Basic part violates BOTH of the vendor's crystal limits (ADR-0012).
- **A second USB cable makes this fixture a ground bridge** through the coax shields, and the coupling is cable-position-dependent — i.e. it differs between the calibration run and the measurement run. Mitigations exist; none is designed in, because the right one depends on the user's bench (ADR-0009).
- Enclosure / mounting: unstated. Assumed bare board with mounting holes until told otherwise.

## Status

**Stages 1–3 COMPLETE** (design docs, parts, rules) — 2026-07-27.
`ARCHITECTURE.md` + `DETAIL_DESIGN.md` + 14 ADRs + 11 `02_parts/` entries +
`nets.yaml` / `power_tree.yaml` / `electrical_invariants.yaml` / `assembly.yaml`.
**Stopped deliberately BEFORE the schematic.** Next: stage 4 authoring.
