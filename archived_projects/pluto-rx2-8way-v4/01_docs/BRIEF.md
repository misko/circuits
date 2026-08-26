# BRIEF — pluto-rx2-8way-v4

```
status:          in-progress
prompt_sha256:   c629e0cf835eb12aa6c8df853e2e8140d38eb027c663d4eabbd81d439a456f48
current_release: no
```

## Original prompt

<!-- prompt-verbatim-begin -->
Can you please launch a new board rx2 8way v4 , please launch it in a new agent , it can re-use previous parts but doesnt have to , it should make the best choices as it goes
<!-- prompt-verbatim-end -->

- date: 2026-07-31
- channel: Codex task

## Binding prompt amendment

<!-- prompt-amendment-verbatim-begin -->
please use the RP2040 module, not the bare RP2040 chip
<!-- prompt-amendment-verbatim-end -->

- date: 2026-07-31
- sha256 with no trailing newline: `d36dd0085b1e4c54b5a1b7a96ce2d823fa2dd880d7cb42f38ebd4aec7e6523f3`
- effect: adds P9 and supersedes the initial bare-RP2040 architecture choice.

## End goal — definition of done

A fabrication-reviewable v4 board selects one of eight 70 MHz–6 GHz antenna
states into PlutoPlus RX2, preserves a simultaneously usable RX1 path, and
runs a deterministic USB-programmable switching schedule. It is independently
reconstructed from current evidence; earlier revisions are incident evidence,
not authority.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | Eight RF states feed one RX2 output through SMA interfaces | inherited functional intent A1 | in progress |
| G2 | State 8 is a two-220-ohm resistive pickoff from the RX1 antenna path | inherited user decision A2 | in progress |
| G3 | 8192 clean samples per ordinary state, 4096 reference samples, and 128 blank samples per hop at 30 Msps | inherited user decision A3 | firmware pending |
| G4 | A 499,712-sample buffer contains exactly eight 62,464-sample sweeps | derived from A3 | firmware pending |
| G5 | A prebuilt RP2040 module supplies USB-C, flash, clock, regulation and four consecutive PIO GPIOs | P9 / D1 | in progress |
| G6 | JLC assembles the carrier and through-hole SMA line; the module is explicitly user-fitted because its populated underside prevents direct reflow seating | D2 | in progress |
| G7 | Release includes DRC/ERC, sourcing, impedance, route-length, and RF characterization evidence | process contract | unmet |

## Spec tensions

| # | Requirement | Standard / parts cap it exceeds | Resolution | User flagged |
|---|---|---|---|---|
| T1 | Integrated RP2040 module on an RF receive board | Raspberry Pi Pico uses a variable-mode RT6150 switcher; RP2040-Zero has carrier-facing parts and no credible direct-reflow joint | Select LDO-regulated RP2040-Zero; user-fit it after JLC assembly with an underside keepout; ADR-0001/0002 | yes |
| T2 | A flat reference tap over 70 MHz–6 GHz | Real directional couplers cannot span 85.7:1 bandwidth; switch isolation limits reference SIR at the high end | Keep the confirmed 2x220-ohm pickoff and publish measured correction data; ADR-0003 | yes, inherited decision |
| T3 | Ku/Starlink on the same receive board | Pluto RF ceiling is 6 GHz and Ku needs downconversion plus low-loss laminate | Out of scope; separate board | yes, inherited decision |

## Commission fact-lock

| Fact | Value | Locked by |
|---|---|---|
| RF band and ports | 70 MHz–6 GHz; 8 antenna SMA, RX1 output SMA, RX2 output SMA | A1 |
| Timing | 8192/4096 clean samples plus 128 blank per hop; 30 Msps | A3 |
| Input envelope | USB vSafe5V through the RP2040-Zero module's only USB-C; module 3V3 output is the carrier source | P9 / D1 |
| 3V3 rail | RT9013-33 module rail, filtered by BLM21SP601SN1D before the RF switch | D1 |
| Protection | Module owns USB entry; carrier adds no parallel power path. Ferrite + local ceramic isolate switch VDD. RF ports intentionally have no shunt ESD | D2 |
| Off-control / storage | De-energized when USB is unplugged; no battery and no alternate source | D2 |
| Hard-cell parts | RP2040-Zero module, PE42482A-X, KH-SMA-KE-Z | current dossiers and module selection evidence |
| RF interface envelope | Every SMA is 50 ohm, passive receive-only, +18 dBm CW max and 0 VDC in powered/unpowered/fault states; no bias tee, active antenna, transmit path or DC offset | D5 / ADR-0003 |
| Switching envelope | Hopping/hot switching only 100 MHz–6 GHz; 70–<100 MHz requires RF removed, static selection and settling before RF is reapplied | D5 / ADR-0003 |
| Handling / power envelope | ESD-controlled bench equipment. Supported firmware keeps the module WS2812 dark; total module-LDO load <=125 mA at TA<=50 C. Physical current/thermal qualification remains open; arbitrary firmware is unsupported | D5/D6 |

## Mating fact-lock

None — this board does not rigidly mate to foreign hardware. Pluto-facing RF
connections use SMA cables, so no `mates.yaml` is carried.

## Log

- A1 — Preserve the proven core function: eight-state PlutoPlus RX2 selector,
  70 MHz–6 GHz, ten SMA jacks total, and constant-but-characterizable path
  phase for AoA.
- A2 — Preserve the explicitly confirmed split-arm reference pickoff: two
  220-ohm 0402 resistors in series.
- A3 — Preserve the confirmed timing frame and free-running RP2040 PIO model.
- A4 — Use the module's USB-C as the only input; support <=125 mA total
  module-LDO load at TA<=50 C with the module WS2812 dark. Physical current and
  thermal qualification is required; arbitrary firmware is unsupported.
- P9 — Binding user amendment: use an RP2040 module, not the bare chip.
- A5 — Apply the user's module-first preference to total design, verification,
  routing, sourcing and bring-up complexity, not BOM price/area alone.
- D1 — Use Waveshare RP2040-Zero: LDO-regulated, integrated USB-C, flash,
  crystal and buttons, with GP0–GP3 physically ordered for one PIO write.
- D2 — The module is user-fitted after carrier assembly; vendor STEP evidence
  shows a populated carrier-facing surface and no direct-reflow seating plane.
- D3 — Use the absorptive PE42482A-X and the same broadband pickoff physics;
  these are still the best fit after re-checking the requirements.
- D4 — Use `jlc_4layer_advanced`, controlled impedance, solid L2 ground, L3
  control routing, and bottom ground. The RF switch forces the tier.
- D5 — Bind every SMA to 50 ohm, +18 dBm CW maximum, 0 VDC and passive
  receive-only operation; hot switching only at 100 MHz–6 GHz, cold/static
  selection at 70–<100 MHz, and ESD-controlled de-energized cable handling.
- D6 — Released firmware keeps the WS2812 dark; <=125 mA at TA<=50 C is a
  supported envelope pending physical current/thermal qualification.

## Decision register

| id | decision | decided by | depth |
|---|---|---|---|
| ADR-0001 | module-first selection of RP2040-Zero | P9 and total-complexity evidence | architecture |
| ADR-0002 | user-fitted module and module-owned USB/power boundary | measured module underside and JLC evidence | assembly |
| ADR-0003 | PE42482A-X plus 2x220R reference pickoff | inherited user-confirmed physics, revalidated | architecture |
| ADR-0004 | four-layer advanced controlled-impedance stack | RF-switch escape and RF return requirements | fabrication |
