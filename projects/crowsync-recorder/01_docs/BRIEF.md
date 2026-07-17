# BRIEF — crowsync-recorder

Commissioned: 2026-07-16, via /pcb-design. Prompt sha256: c0a5c91cfbb3b3e2d661ba802d75b3c5e0b3dd826e8249935cd562fc0ae6177a

<!-- prompt-verbatim-begin -->
# Project goals

## Overall purpose

CrowSync is a distributed, continuously sampling acoustic recorder for
Raspberry Pi nodes. Its purpose is to give every audio sample a shared GPS time
reference so multiple microphones can be aligned for TDOA-based crow
localization.

## Functional architecture

```text
Outdoor microphone
  → bias / protection / filtering
  → TLV9062 preamplifier
  → PCM2900C VINL
  → USB audio channel 1

External GNSS PPS
  → protection / divider / AC coupling
  → PCM2900C VINR
  → USB audio channel 2

GNSS USB/UART
  → Raspberry Pi
  → labels each PPS event with UTC
```

## Target electrical behavior

- USB-powered, two-channel recorder.
- 48 kHz, 16-bit stereo capture through `PCM2900CDBR`.
- Channel 1: outdoor microphone.
- Channel 2: GPS PPS timing waveform.
- No stop/start synchronization.
- Audio sample index mapped continuously between PPS events.
- External GNSS module, not integrated onto the recorder PCB.
- Low-noise 3.3 V analog rail from `TPS7A2033PDBVR`.
- `TLV9062IDR` used for VCOM buffering and microphone gain.
- PUI electret capsule as the default production microphone candidate.
- Four-layer PCB with a continuous ground reference plane.

## Mechanical and sourcing goals

- Approximately 65 × 42 mm PCB.
- Four M2.5 mounting holes.
- USB-C cable clear of mounting hardware and enclosure walls.
- JST GH internal connectors for microphone and PPS harnesses.
- Sealed M8/EN3 field microphone connector via enclosure harness.
- Mostly top-side SMT assembly.
- JLCPCB/PCBWay-compatible BOM and placement data.

## First-article goal

- Fabricate five PCBs.
- Assemble three PCBAs.
- Retain two loose boards.
- Validate USB, oscillator, microphone, PPS, long-duration recording, and
  two-node timing before ordering more.

## Non-goals for the first PCBA

The recorder board does not include:

- Raspberry Pi
- GNSS receiver
- microphone capsule or outdoor puck
- enclosure
- storage
- cooling
- PoE/power distribution
- software image
<!-- prompt-verbatim-end -->

## Parsed requirements

- P1: USB-powered two-channel recorder around PCM2900CDBR, 48kHz/16-bit stereo.
- P2: CH1 = outdoor electret microphone: bias / protection / filtering ->
  TLV9062 preamp -> VINL. PUI capsule is the default production candidate.
- P3: CH2 = GNSS PPS waveform: protection / divider / AC coupling -> VINR.
  GNSS module is EXTERNAL (PPS arrives on an internal harness).
- P4: Low-noise 3.3V analog rail from TPS7A2033PDBVR; TLV9062IDR for VCOM
  buffer + mic gain (parts are USER-PINNED).
- P5: 4-layer PCB, continuous ground reference plane; ~65x42mm; 4x M2.5
  mounting holes; USB-C receptacle placed clear of mounting hardware and
  enclosure walls.
- P6: JST GH internal connectors (mic, PPS); sealed M8/EN3 field mic
  connector lives on the ENCLOSURE harness (off-board).
- P7: Mostly top-side SMT; JLCPCB/PCBWay-compatible BOM + CPL.
- P8: First article: fab 5 PCBs, assemble 3.
- P9: Non-goals: no Pi, GNSS, capsule, enclosure, storage, cooling, PoE,
  software on this board.

## Q / A

- Q1: Which PUI capsule is the design target (sets bias network + gain)?
  A1 (user, 2026-07-16): **Design for both** — gain set by one resistor
  pair; ship -24dB (AOM-5024L-HD-R class) values, document the -44dB
  alternate values in the ADR.
- Q2: PPS logic level on the harness?
  A2 (user, 2026-07-16): **3.3V CMOS** (typical GNSS module PPS); divider
  scales to ~1Vpp at VINR.
- Q3: Protection level for external harness lines (outdoor mic via M8, PPS)?
  A3 (user, 2026-07-16): **ESD + bias-line clamp** — TVS/ESD array on mic
  and PPS lines, series resistance, ferrite on mic bias.
- Q4: Assembly plan for connectors/USB-C?
  A4 (user, 2026-07-16): **JLC assembles everything** — standard/extended
  assembly, all SMT including JST GH + USB-C placed by JLC.

## End goal — definition of done

An orderable, verified JLCPCB release of the two-channel recorder board.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | PCM2900C 48k/16 stereo USB recorder, bus-powered | P1 | unmet |
| G2 | CH1 mic chain (bias/protection/TLV9062 -> VINL), both PUI capsules | P2/A1 | unmet |
| G3 | CH2 PPS chain (protection/divider/AC couple -> VINR), 3.3V CMOS in | P3/A2 | unmet |
| G4 | TPS7A2033 low-noise 3.3V analog rail | P4 | unmet |
| G5 | 4-layer ~65x42mm, continuous GND plane, 4x M2.5, USB-C clear of hardware | P5 | unmet |
| G6 | JST GH mic + PPS headers | P6 | unmet |
| G7 | Top-side SMT, JLC-compatible BOM/CPL, all-JLC assembly | P7/A4 | unmet |
| G8 | Order package for 5 PCBs / 3 assembled | P8 | unmet |

## Decision register

| id | decision (one line) | decided by | depth |
|---|---|---|---|
| ADR-0001 | USB + harness protection: 2x USBLC6-2SC6, 100R series, ferrite bias | agent (A3 delegation) | decisions/0001-input-protection.md |
| ADR-0002 | Codec bus-powered (fig 38); 3V3A rail scope = analog front-end only | agent (P4 delegation) | decisions/0002-bus-powered-codec-3v3a-scope.md |
| ADR-0003 | Gain pair Rf/Rg = 3k01/1k ship, 39k/1k alt; only Rf swaps | user (Q1) + agent | decisions/0003-dual-capsule-gain-plan.md |
| ADR-0004 | One continuous GND plane; A/D separation by placement | user (P5) + agent | decisions/0004-continuous-ground-plane.md |
| ADR-0005 | USB4105-GF-A + JST GH SM03B/SM02B, 100% top-side JLC SMT | user (Q4) + agent | decisions/0005-connectors-and-assembly.md |

## Log

- 2026-07-16: commissioned; folders + contracts created from usb-power-3s
  canonical set.

### A5 — 2026-07-16 — assumption (not asked)
Assumed: PCM2900C runs in the datasheet fig-38 bus-powered configuration
(internal regulators); the pinned TPS7A2033 3.3V rail powers only the
preamp + mic bias, because 3.3V is below the codec's 3.6-3.85V
external-supply window. Authority: P delegates design decisions; P4 wording
("low-noise 3.3V ANALOG rail") is consistent.
Escalate if: the user expected fig-36 high-performance codec supply.

### A6 — 2026-07-16 — assumption (not asked)
Assumed: full-scale reference point = 104 dB SPL at the capsule for both
gain builds (crow calls at close range without clipping).
Escalate if: field data shows habitual clipping or > 20 dB unused headroom.
