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

## Spec tensions (D-SPEC)

| # | Tension | Status |
|---|---|---|
| T1 | 70 MHz–6 GHz vs. printed Wilkinson | **RESOLVED by D1** — resistive split. Cost: 6 dB, accounted in D2. |
| T2 | Control polarity: verbatim brief vs. follow-up answer | **RESOLVED by A3.** Recorded because the two disagreed; the brief wins. Note the consequence: with ON = loopback, an unpowered or floating control line defaults to **antenna** mode, which is the safe default. |
| T3 | "same path length" vs "software offset" | **RESOLVED by D4** — build symmetric, publish the measured delta. |

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
| Impedance | 50 Ω, controlled | implied by SMA + RF; to be pinned with the stackup |

## Open

- **TX drive level** — the one fact-lock row still open. At +7 dBm and 30 dB total, each RX sees ~−23 dBm, comfortably safe. If the user drives the Pluto TX harder, the pad and the RX margin both need re-checking.
- Enclosure / mounting: unstated. Assumed bare board with mounting holes until told otherwise.

## Status

Stage 0 (commission) — scaffold and BRIEF landed. Sourcing spike next.
