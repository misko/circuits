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

## Decision register

(D# appended as decisions are made; mirrors 01_docs/decisions/)

## Log

- 2026-07-16: commissioned; folders + contracts created from usb-power-3s
  canonical set.
