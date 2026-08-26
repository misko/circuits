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
| P5 | ~~**30 dB attenuation** on the loopback path~~ → **≥40 dB MINIMUM across 70 MHz – 6 GHz** | verbatim, scoped by A2, **raised and re-framed by A9** |
| P6 | **Same path length on each loopback run** | verbatim, relaxed by A6/A7; **A8 moves the obligation onto the two RX CABLES** (identical pair) with the board's own arm-to-arm delta still published |

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
| Q8 | *(not asked — user directive, unprompted, 2026-07-27)* | **A8** | **"lets not do the fixed bulkhead version, lets use SMA cables to connect our board to the pluto."** Plus, in the same exchange: **the PlutoPlus RF ports are SMA FEMALE (jack)** — the owner has both units in hand — and **the Pluto is in a case, so its PCB is not the mating reference at all**. Impact: ADR-0015. Kills the $101 adapter order, the board-side SMP, D6, and the ±0.05 mm rigid-mating analysis; the board becomes 5 × true SMA jacks; cable loss enters the budget; "same path length on each run" becomes TWO IDENTICAL CABLES rather than a PCB trace-match |
| Q9 | *(not asked — user directive, unprompted, 2026-07-27)* | **A9** | **Cal-path attenuation 30 dB → 40 dB, specified as a MINIMUM across 70 MHz – 6 GHz.** Reasoning is part of the answer and is recorded in ADR-0016: the pad is not there to set the operating level (the AD936x TX attenuator gives ~90 dB in 0.25 dB steps) but to **survive a misconfiguration**, so it is sized against TX MAXIMUM, never TX intended; the extra 10 dB is free in SNR terms; and the failure modes are asymmetric — too much pad costs SNR and is recoverable by averaging, too little destroys the receiver permanently. Retires D5 |

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
| ~~**D5**~~ **RESOLVED 2026-07-27 by A9 — by REFRAMING, not by answering** | ~~"30 dB total" at WHICH frequency? The chain tilts 3.09 dB across 70 MHz-6 GHz~~ | **A minimum needs no reference frequency.** ≥40 dB binds where the chain loses LEAST (70 MHz) and is met by construction everywhere else. The tilt got WORSE under A8 (3.09 → **6.13 dB**, two SMA cables) and the specification absorbed it without changing. The tilt does not matter for accuracy either: the response is **measured and published**, not assumed. ADR-0016 supersedes ADR-0013. | — |
| ~~**D6**~~ **RETIRED 2026-07-27 by A8** | ~~Which PlutoPlus? genuine span 35.04 mm vs clone 34.72 mm~~ | **The board is no longer referenced to the Pluto's geometry at all.** With SMA cables there is no span to match, no midpoint to build to, and no ±0.16 mm of float spent on an open question. **A cabled board fits the genuine unit, the clone, and any future revision.** ADR-0015 supersedes ADR-0014. | — |
| **D7** | **Which control surface WINS** when USB and the GPIO header disagree? | `RF_CTRL = HEADER_level OR USB_bit`, **plus a 10 s USB watchdog** that clears the USB bit if the host goes silent — so the header always regains authority within 10 s and the safe state is always reachable. ADR-0008. | **Firmware only.** No hardware change. **STILL OPEN** — and now the ONLY open D#. It does not gate the schematic. |

## Spec tensions (D-SPEC)

| # | Tension | Status | ADR | flagged |
|---|---|---|---|---|
| T1 | 70 MHz–6 GHz vs. printed Wilkinson | **RESOLVED by D1** — resistive split, and **CONFIRMED and strengthened at design stage**: λ/4 at 70 MHz is **601 mm**, not ~400 mm, and a SECOND independent refutation applies — the required bandwidth ratio is **85.7:1** where published multi-section Wilkinsons top out near 10–20:1. Cost: 6.02 dB, accounted in D2. | [0003](decisions/0003-resistive-delta-splitter.md) | yes |
| T2 | Control polarity: verbatim brief vs. follow-up answer | **RESOLVED by A3.** Recorded because the two disagreed; the brief wins. Note the consequence: with ON = loopback, an unpowered or floating control line defaults to **antenna** mode, which is the safe default — and that is now enforced by hardware in TWO independent ways (MCU reset pull-down + an external pull-down at each switch). | [0001](decisions/0001-control-polarity-and-power-on-default.md) | yes |
| T3 | "same path length" vs "software offset" | **RESOLVED by D4** — build symmetric, publish the measured delta. EXTENDED at design stage to include AMPLITUDE, because ADR-0004 put independent parts in the two arms. | [0011](decisions/0011-length-match-is-a-published-artifact.md) | yes |
| **T4** | **"30 dB TOTAL" is a SCALAR against a chain that tilts 3.09 dB** — now **6.13 dB** with two SMA cables in it. Reading it as "30 dB at every frequency" makes it unsatisfiable by ANY design, not just this one. | **RESOLVED by A9** — the requirement became **≥40 dB MINIMUM across the band**, which needs no reference frequency, binds at 70 MHz, and got *more* robust when the tilt doubled. The release still **publishes loss vs frequency, not a scalar** — now against a floor instead of a target. ~~D5 / minimax~~ superseded. | [0016](decisions/0016-40db-minimum-across-the-band.md) (supersedes [0013](decisions/0013-spec-tension-30db-is-a-curve.md)) | **yes — LOUDLY** |
| **T5** | **The mating geometry is ambiguous**: two PlutoPlus units measured 0.32 mm apart, and "Pluto+" names three different boards (2020 V1, a genuine 2021 V2 respin, and a 2025 knock-off with different artwork). | **DISSOLVED by A8** — the board consumes no PlutoPlus geometry, so the ambiguity has nothing to bind on. Note the shape: this tension was not decided under uncertainty, it stopped being consumed. ~~D6 / the 34.88 mm midpoint~~ superseded. | [0015](decisions/0015-sma-cables-not-direct-mount.md) (supersedes [0014](decisions/0014-spec-tension-which-plutoplus.md)) | **yes — LOUDLY** |
| **T8** | **The pad was sized against the wrong quantity.** "30 dB total" was read as an operating-level spec; the AD936x TX attenuator already gives ~90 dB of operating-level control in 0.25 dB steps. What the fixed pad actually buys is **survival of a misconfiguration**, which is sized against TX MAXIMUM. And the two ratings involved had never been put in one table: at this board's own declared **+27 dBm** abuse ceiling, the 30 dB build left the user's receiver **2.7 dB** from its absolute maximum. | **RESOLVED by A9** — ≥40 dB minimum lifts that to **15.6 dB**, and both governing numbers are now CITED to the AD9363 data sheet Rev. D with page numbers instead of carried as prose. | [0016](decisions/0016-40db-minimum-across-the-band.md) | **yes** |
| **T6** | **The GPIO header cannot be read as specified.** PlutoPlus IO is **1.8 V**; RP2040's VIH is a **flat 2.0 V** (not 0.65·IOVDD), and a Zynq HR bank's worst-case VOH at VCCO=1.8 V is **1.35 V**. A direct connection reads permanently LOW — and the failure is FAIL-SAFE, so it passes every "can it spuriously enter loopback" test and surfaces only as "the GPIO control doesn't work", plausibly after seal. There is also a REVERSE hazard: RP2040 VOH 2.62–3.3 V into a Zynq pin whose absolute max is ~2.35 V. | **RESOLVED IN HARDWARE, not by downgrading P2**: the header lands on an **ADC pin** through a ÷2.5 divider, thresholded in firmware. Reads 1.8 / 3.3 / 5.0 V logic with no translator and no second rail, and is **input-only by construction** (an ADC-configured pin has its digital output disabled), so no firmware bug can drive the user's Pluto. | [0008](decisions/0008-control-surfaces-usb-and-gpio-header.md) | **yes** |
| **T7** | **">25 dB isolation" is not met on the guaranteed MINIMUM above ~5 GHz** by any cheap stocked SPDT — BGS12WN6 is 21 dB min / 28 typ and BGS12P2L6 24 min / 27 typ over 5150–5925 MHz. Typ meets it. | **STATED, not downgraded.** The only part found that brackets the whole band with >25 dB guaranteed at BOTH ends is HMC1118, at ~$15/board for two. Recorded as an available upgrade rather than silently assumed away. | [0002](decisions/0002-spdt-switch-bgs12wn6.md) | yes |

## Mating fact-lock (D-MATE)

This board connects to hardware this repo did not design: an ADALM-PlutoPlus
whose vendor publishes **no PCB source** — three PDFs, no KiCad/Altium, no DXF,
no STEP, no dimensioned drawing. Everything it consumes from that device
therefore enters from outside and carries its **M-IMPORT grade**.

The facts live ONCE, in `spf/plutoplus_hardware/` (`README.md` is the record,
`facts.yaml` its machine index). The machine copy of this table is
`03_src/rules/mates.yaml`, graded by
`skills/kicad-pcb/scripts/import_provenance_check.py .` — **18/18 facts
graded, 0 fails, 2026-07-27.**

> **A8 CHANGED THE SHAPE OF THIS TABLE, not just its contents.** With SMA
> cables between the two boards, **NO GEOMETRY crosses the boundary at all** —
> thirteen of the fifteen original consumptions retire in one stroke. What
> crosses instead is ELECTRICAL: the receiver's damage threshold and the
> transmitter's maximum, which are what the ≥40 dB pad is sized against and
> which had been living as ungraded prose in `DETAIL_DESIGN.md` with the words
> "SECONDARY SOURCE" attached. **The retired rows are kept, marked, with their
> cause** — a consumption that vanishes silently is indistinguishable from one
> that was never declared.

### Consumed (5)

| Fact (`spf/plutoplus_hardware` id) | Grade | Evidence | Where it is spent |
|---|---|---|---|
| `port_order` | **MEASURED** | silk on both units + schematic nets | which cable carries RX1 / RX2 / TX, and therefore which of our five SMA jacks is which. Get it wrong and the two channels report transposed — invisible to every gate on this board |
| `sma_gender` | **MEASURED** *(was ESTIMATED)* | **the owner states both physical units have SMA jacks (female)** — A8 | the ADR-0015 gender chain: Pluto JACK → cables MALE–MALE → **our board JACK**. See below for how much smaller the exposure now is |
| `ad936x_rx_abs_max_input` **+2.5 dBm** | **CITED** | AD9363 data sheet **Rev. D, printed p.15 of 32**, ABSOLUTE MAXIMUM RATINGS, row `RF Inputs (Peak Power)` | the SURVIVAL side of ADR-0016. **It is a PEAK rating**; the cal stimulus is a CW tone, so peak = average here |
| `ad936x_tx_max_output_power` **+8 dBm** | **CITED** | AD9363 **Rev. D, printed p.4 of 32**, TRANSMITTERS 800 MHz, `Maximum Output Power`, *"1 MHz tone into 50 Ω load"* | the DRIVE side of the same sizing. **8 / 7.5 / 7.0 dBm at 800 MHz / 2.4 GHz / 3.5 GHz — so the "≈+7 dBm" this brief carried was the WORST characterized band, not the ceiling.** 70 MHz and 6 GHz are not characterized at all |
| `plutoplus_tx_frontend_active` | **OWED** | — | the gap between the transceiver's maximum and the SMA PORT's. The cited +8 dBm bounds the port only if the path between is passive, and nobody has established that on a PlutoPlus. What the design assumes meanwhile: DETAIL_DESIGN §6.1 |

### Retired 2026-07-27 by A8 / ADR-0015 (13)

| Fact | Grade (unchanged) | What it USED to be spent on |
|---|---|---|
| `sma_span_genuine` · `sma_span_clone` | MEASURED | the 34.88 mm midpoint the three SMP anchor X coords were built to (D6) |
| `pitch_*_genuine` · `pitch_*_clone` (6 rows) | MEASURED | per-gap SMP anchor spacing — the pitch is NOT uniform on either unit |
| `barrel_od` | MEASURED | the D-subtraction behind the two outer pitches |
| `connector_outline_width` | ESTIMATED ±1.5 % | keep-out envelope around each Pluto-side connector body. **This was the file's only ESTIMATED-used-DIMENSIONALLY row, i.e. the only thing M-BAR had to grade** |
| `cad_span_plot` (35.60 mm) | ESTIMATED ±1.5 % | comparison only; kept visible because it IS the incident |
| `rf_axis_height_above_pcb` | **OWED** | the board's Z position — and formerly **the ONE BLOCKING mechanical item on this design** |
| `mounting_hole_positions` | **OWED** | the optional load-relief bracket, for a push-on force that no longer exists |

**Why this table exists at all (ADR-0005).** The span was first taken from the
undimensioned vector assembly plot at **35.60 mm**, and three independent
extractions agreed to **0.003 mm**. A floorplan was ready to be built on it.
The caliper then read **35.04** (genuine) and **34.72** (clone) — 1.6 % and
2.5 % off, against a rigid-SMA thread-start window of **±0.05 mm**. Precision
about a proxy is not accuracy about the object.

**And what A8 did to that story, which is worth more than the retirement
itself:** the 0.32 mm disagreement between two units both sold as "PlutoPlus"
— the headline finding of the device record — **now costs this design nothing.**
A cabled board is referenced to neither unit. Likewise the gender: it decided a
**$101** adapter order under ADR-0006, and with a cable in the path it decides
only **which cable to buy**, because our port gender is set by what a standard
male cable end mates with. The fact is still consumed. The money is not riding
on it.

## Commission fact-lock

| Row | Value | Locked by |
|---|---|---|
| RF frequency range | 70 MHz – 6 GHz | A1 |
| Loopback loss, TX → each RX | **≥ 40 dB MINIMUM across 70 MHz – 6 GHz, worst-case unit, cables credited at ZERO.** Guaranteed minimum **40.07 dB** (binds at 6 GHz); typical **44.6 dB @70 MHz → 50.2 dB @6 GHz** | A2, **raised and re-framed by A9** (ADR-0016) |
| Control polarity | ON = loopback, OFF = antenna | A3 |
| Input envelope | 5 V, micro-USB | A4, A5 |
| Control surface | USB (CDC) **and** GPIO header | A4, D3 |
| Length-match obligation | the two RX **CABLES** are an identical pair; the board's own arm-to-arm delta stays symmetric by construction with the **measured delta published** | A6, A7, D4, **A8** |
| **Board-to-Pluto interface** | **3 × SMA male–male CABLES, user-supplied**; the board carries **5 × KH-SMA-KE-Z SMA JACKS** | **A8** (ADR-0015) |
| TX drive level | **+8 dBm max, CITED** — AD9363 Rev. D p.4 of 32, `Maximum Output Power` 800 MHz. ⚠️ Still carries ONE gap: that is the TRANSCEIVER's maximum, and it bounds the SMA PORT only if the Pluto's TX front end is passive — OWED (`plutoplus_tx_frontend_active`). ≥40 dB absorbs 19 dB of undiscovered TX gain before the RX rating is reached | **A9** + `spf/` |
| RX damage threshold | **+2.5 dBm PEAK, CITED** — AD9363 Rev. D p.15 of 32, ABSOLUTE MAXIMUM RATINGS, `RF Inputs (Peak Power)` | **A9** + `spf/` |
| Impedance | 50 Ω, **controlled impedance REQUESTED** | pinned by ADR-0010: 4-layer `JLC04161H-7628`, 0.36 mm microstrip on the 0.2104 mm top prepreg |
| ~~Reference frequency for the 30 dB~~ | **N/A — a MINIMUM needs none.** Binds at 70 MHz by construction | **A9 retires D5** |
| ~~PlutoPlus port span~~ | **N/A — not consumed.** The board is referenced to no Pluto dimension | **A8 retires D6** |
| Control resolution (USB vs header) | OR + 10 s USB watchdog | **D7 — assumed, user ABSENT. The last open one** |
| GPIO header logic level | **1.8 / 3.3 / 5.0 V all accepted** (÷2.5 divider into an ADC pin) | D3 + ADR-0008; the 1.8 V case is what forced it |
| Board TX absolute ceiling | **+27 dBm** (0.5 W), binding element PAD_A1 at 1.7 W | derived, DETAIL_DESIGN §4.3 |
| Fab tier (D-TIER) | `jlc_4layer_advanced` — 0.25/0.15 mm vias | ADR-0010; forced independently by the BGS12WN6 ground via AND the RP2040 escape |
| Assembly service | JLC **Standard** PCBA, top side only | ADR-0010 + `assembly.yaml`: THT parts and a non-default stackup both exclude Economic |

## Decision register

Every ADR appears in exactly one row; every row's depth link exists.

| id | decision | decided by | depth |
|---|---|---|---|
| D1 | Resistive splitter, not Wilkinson | agent (P-delegation) | [ADR-0003](decisions/0003-resistive-delta-splitter.md) |
| D2 | Pad derived from measured splitter + switch loss | agent (P-delegation) | [ADR-0004](decisions/0004-attenuation-value-and-placement.md) *(superseded-by-0016; the PLACEMENT half is carried forward)* |
| D3 | MCU owns the control line; GPIO header retained | agent (P-delegation) | [ADR-0008](decisions/0008-control-surfaces-usb-and-gpio-header.md) |
| D4 | Length match published, not toleranced | agent (P-delegation) | [ADR-0011](decisions/0011-length-match-is-a-published-artifact.md) |
| ~~**D5**~~ | ~~30 dB referenced by minimax ⇒ ≈3.0 GHz~~ **RESOLVED by A9 (reframed as a minimum)** | agent → **user (A9)** | [ADR-0013](decisions/0013-spec-tension-30db-is-a-curve.md) *(superseded-by-0016)* |
| ~~**D6**~~ | ~~Build to the 34.88 mm PlutoPlus midpoint~~ **RETIRED by A8 (no geometry is consumed)** | agent → **user (A8)** | [ADR-0014](decisions/0014-spec-tension-which-plutoplus.md) *(superseded-by-0015)* |
| **D7** | Control resolution = OR + 10 s USB watchdog | **agent, user ABSENT — still open** | [ADR-0008](decisions/0008-control-surfaces-usb-and-gpio-header.md) |
| **A8** | **SMA CABLES, not direct-mount; 5 × SMA jacks on the board** | **user (A8)** | [ADR-0015](decisions/0015-sma-cables-not-direct-mount.md) |
| **A9** | **≥40 dB MINIMUM across the band, sized against TX maximum** | **user (A9)** | [ADR-0016](decisions/0016-40db-minimum-across-the-band.md) |
| — | Control polarity + power-on state = ANTENNA, in hardware | user (A3) + agent | [ADR-0001](decisions/0001-control-polarity-and-power-on-default.md) |
| — | SPDT = BGS12WN6, BGS12P2L6 as a same-land dual source | agent (P-delegation) | [ADR-0002](decisions/0002-spdt-switch-bgs12wn6.md) |
| — | DC blocks on the ANTENNA ports only | agent (P-delegation) | [ADR-0005](decisions/0005-dc-coupling-posture.md) |
| — | ~~Mating: SMA→SMP adapters + edge-launch SMP on-board~~ — the record of WHY rigid direct-mount is impossible; the three proofs still stand | agent (P-delegation) | [ADR-0006](decisions/0006-mating-strategy-sma-to-smp.md) *(superseded-by-0015)* |
| — | SMA = KH-SMA-KE-Z ×5, and the launch rules are OURS | agent (P-delegation) | [ADR-0007](decisions/0007-sma-antenna-connector-and-launch.md) *(extended by 0015, not superseded)* |
| — | Input protection: what is fitted and what is deliberately absent | agent (P-delegation) | [ADR-0009](decisions/0009-input-protection-posture.md) |
| — | Stackup + fab tier: 4-layer JLC04161H-7628, ADVANCED | agent (D-TIER) | [ADR-0010](decisions/0010-stackup-and-fab-tier.md) |
| — | MCU = RP2040; CH32X035 datasheet-verified and BLOCKED | agent (P-delegation) | [ADR-0012](decisions/0012-mcu-selection-rp2040.md) |

## Open

Numbered so the report and `ARCHITECTURE.md` §12 can point at them.

**Six of the eleven items that stood here on 2026-07-27 morning are CLOSED by
A8 and A9.** What remains:

- **D7 — which control surface wins.** The only open D#, firmware-only, does
  not gate the schematic (ADR-0008).
- **Is there ACTIVE gain between the AD936x TX and the Pluto's TX SMA?**
  `OWED` in `spf/plutoplus_hardware/`. The cited +8 dBm is the transceiver's
  maximum and bounds the PORT only if that path is passive. What the design
  assumes meanwhile, and how much it absorbs: DETAIL_DESIGN §6.1. Five minutes
  with a power meter at 0 dB commanded attenuation closes it.
- **Standard SMA vs RP-SMA on the PlutoPlus.** The JACK half is now MEASURED
  (A8: the owner has both units). The centre-contact polarity is a DIFFERENT
  property and nobody has looked. Consequence if wrong: buy different cables.
- **Are the PlutoPlus RF ports DC-free?** Asserted nowhere. All RF ports on
  both switches plus all three splitter ports are ONE galvanic node, and a
  cable is as DC-continuous as an adapter was. If they are not DC-free, blocks
  become mandatory on the three Pluto-facing SMA ports too (ADR-0005).
- **The 12 MHz crystal is deliberately not selected.** The JLC Basic part
  violates BOTH of the vendor's crystal limits (ADR-0012).
- **A stock query on the mid-value YAT parts**, before the schematic. A single
  YAT-15A+/12A+ would collapse PAD_A1 from five chips to two and lift the
  20-board ceiling. Its datasheet MIN column must be read, not assumed —
  ADR-0016's guarantee is built on min columns.
- **The ground bridge got WORSE, not better.** Three coax shields now bond this
  board's ground to the Pluto's over a cable-position-dependent geometry, on
  top of the second-USB loop ADR-0009 already recorded. The coupling differs
  between the calibration run and the measurement run. No mitigation is
  designed in — the right one depends on the user's bench — but **dressing the
  cables identically between the two runs belongs in the user documentation.**
- Enclosure / mounting: unstated. Assumed bare board with mounting holes until
  told otherwise. **The PlutoPlus's own enclosure is no longer our problem** —
  A8 confirmed it is cased, and a cable does not care.

**CLOSED by A8/A9:** the RF-axis height above the Pluto's PCB (was the one
BLOCKING mechanical item); the SMA gender's $101 exposure; the port span / D6;
the JLC-DFM question on the edge-launch SMP; the reference frequency / D5; and
the unlocked TX drive level, which is now CITED at +8 dBm.

## Status

**Stages 1–3 COMPLETE** (design docs, parts, rules) — 2026-07-27,
**re-spec'd the same day for A8 + A9**. `ARCHITECTURE.md` +
`DETAIL_DESIGN.md` + **16 ADRs** (4 superseded, 1 extended) + **10 `02_parts/`
entries** + `nets.yaml` / `power_tree.yaml` / `electrical_invariants.yaml` /
`assembly.yaml` / `mates.yaml`. **Stopped deliberately BEFORE the schematic.**

The re-spec is an EDIT, not a supersede: nothing on this board is sealed —
`04_kicad/` and `07_releases/` hold only their `contracts.md`.

Next: stage 4 authoring. **No hardware question blocks it.** D7 is
firmware-only.
