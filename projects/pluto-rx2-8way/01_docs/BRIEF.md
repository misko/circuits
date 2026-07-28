# BRIEF — pluto-rx2-8way

An 8-way antenna-selection switch on an ADALM-PlutoPlus RX2, sequenced fast
enough that one ~500k-sample buffer contains whole sweeps, and self-timing
without calibration.

<!-- prompt-verbatim-begin -->
we want a high speed switching 8 pole on RX2. We want it to be timed to switch incredibly fast between 8 different antenna. one of which will be the RX1 split antenna. we need to figure out a good timing scheme for out ~500k buffer size at 30Mhz. We will want to spend a prefixed time X at each RX2 antenna and X/2 for RX2=RX1, this is how we will figure out timing struture without calibration. whats the fastest we can iterate and switch through antenna

this is a new board ^

I think we can aim for 8192 or 8192/2 samples per steady state between switches

We want each antenna to have SMA connectors , and if possible one PCB version with just on PCB antennas for ku band starlink
<!-- prompt-verbatim-end -->

sha256(prompt) = `1bf0eca3306af5f4ac4556f0b23cb71b8155fde00940bb9b8b9ec8cfc2ba1573`

---

## Requirements (P#)

| # | requirement | source |
|---|---|---|
| P1 | An 8-pole RF switch selects what PlutoPlus **RX2** sees | verbatim |
| P2 | One of the 8 poles carries a **tap of the RX1 antenna** — the reference | verbatim |
| P3 | Switching is **fast and timed**, not operator-driven | verbatim |
| P4 | Dwell **X** at each antenna, **X/2** at the reference slot. The asymmetry IS the timing marker — no calibration pass | verbatim |
| P5 | Must fit a **~500k-sample buffer at 30 Msps** | verbatim |
| P6 | **Every antenna gets an SMA connector** (8x SMA) | verbatim |
| P7 | A variant with **on-PCB Ku patch antennas for Starlink** — *deferred, see T1* | verbatim |
| P8 | **AoA** is the application: per-path phase may DIFFER but must be **CONSTANT** and characterized | A1 |

## Clarifying questions (Q#) and answers (A#)

| # | question | answer |
|---|---|---|
| Q1/A1 | What is the array for — does phase across paths matter? | **AoA**, but "we can offset path length / phase in software **if its constant**" |
| Q2/A2 | Band? | **70 MHz - 6 GHz**, full Pluto range |
| Q3/A3 | How to tap RX1 for pole 8? | User chose **directional coupler (-10 dB)**. **REFUTED at D-SPEC — see T2**; resistive pickoff proposed as the strictly better answer on this band |
| Q4/A4 | Sequencer clock? | **Free-running RP2040 PIO**; the X/2 marker re-syncs each frame |
| Q5/A5 | Ku strategy? | **Ship the 6 GHz SMA board now; Ku becomes a separate project** reusing only the sequencer |

## Decisions (D#)

- **D1 — the frame is CLOSED.** 8192 clean samples per antenna dwell, 4096 at the
  reference, **128 samples blanking allowance** per hop.
  frame = 7x8320 + 4224 = **62,464 samples = 2.0821 ms** (480.3 Hz sweep rate);
  **buffer = 499,712 samples = exactly 8 complete sweeps** (= 488 x 1024),
  16.657 ms at 30 Msps. Sample efficiency **98.4%**.
  Accepted cost: per-antenna revisit 480.3 Hz -> **unambiguous Doppler +/-240 Hz**,
  and a signal must persist >=2.08 ms to appear on all 8 antennas.
- **D2 — Ku/Starlink is a SEPARATE project** (A5). It shares no RF chain, no
  laminate and no switch with this board; only the sequencer/control section
  carries over.
- **D3 — the RX1 tap is a RESISTIVE PICKOFF, not a directional coupler**
  (T2). PROPOSED, pending explicit user confirmation, because it reverses A3.
- **D4 — the 8 path phase/loss deltas are a PUBLISHED, MEASURED release
  artifact**, not a design target. P8 permits unequal paths; it does NOT permit
  unknown or drifting ones. The obligation this creates is STABILITY, and it is
  gated at the release, mirroring pluto-cal-switch's published length delta.

## Spec tensions (D-SPEC) — flagged to the user, NOT silently resolved

| # | tension | status |
|---|---|---|
| **T1** | **Ku/Starlink (10.7-12.7 GHz) is 2x beyond the AD9363's 6 GHz ceiling.** On-PCB Ku patches are geometrically fine (lambda/2 @11.7 GHz = 12.8 mm, 8 elements ~102 mm) but downconversion is MANDATORY, and FR4 is unusable at 12 GHz (needs Rogers-class laminate). P7 and A2 cannot be one RF chain | **DEFERRED to a separate project by A5.** ADR owed |
| **T2** | **A 70 MHz-6 GHz directional coupler does not exist** — 85.7:1 bandwidth against a coupled-line structure that rolls off 6 dB/octave below its design band. Deeper point: **directionality is not the property being bought.** A coupler separates forward from reverse waves; a receive antenna has one direction. The goal (preserve RX1 sensitivity) is better met by a **resistive pickoff**: -20 dB tap, **0.42 dB** main-line loss, 26 dB return loss, flat DC-6 GHz — against 6 dB for a resistive split, or a coupler that cannot span the band | **ADR owed; D3 proposed.** Awaiting user confirm |

## Commission fact-lock

| row | value | grade |
|---|---|---|
| RF band | 70 MHz - 6 GHz | **A2** (user) |
| Ports | 8x SMA antenna + RX1 in + RX1 out + RX2 out | **P6** (user) |
| Application | AoA; constant-but-unequal path phase permitted | **A1** (user) |
| Sample rate / buffer | 30 Msps, 499,712 samples = 8 sweeps | **D1** |
| Dwell structure | 8192 / 4096 clean + 128 blank | **user + D1** |
| Sequencer | free-running RP2040 PIO, 3-bit parallel select | **A4** |
| Control interface | **parallel 3-bit, NEVER SPI** — SPI latency (1-10 us) exceeds the entire blanking budget | **DERIVED** |
| Input protection posture | OWED | **OWED** |
| Off-control / source | USB-powered, unplug = de-energized (E-OFF N-A expected) | **assumed, ADR owed** |
| Fab tier | OWED — pending switch-package escape check (D-ESC/D-TIER) | **OWED** |

## Mating fact-lock (D-MATE)

**This board mates to nothing foreign.** All Pluto-facing interfaces are SMA
male-male cables, which absorb the mechanical interface entirely — the same
conclusion pluto-cal-switch reached the expensive way (its ADR-0015 / A8, after
a $101 adapter order built on a 35.60 mm figure that a caliper read as 35.04 and
34.72 on two units sold under one name). **No `03_src/rules/mates.yaml` is
carried**, deliberately: an empty one fails `import_provenance_check.py` as
M-COVER. Silence is not a declaration, so this paragraph is the declaration.

## Receiver configuration this design DEPENDS on (firmware/host, not the board)

The 128-sample blanking allowance is only valid if the host configures RX2 as:

- **MGC, not AGC** — AGC settling is 10s of microseconds and would swamp the budget
- **RX FIR bypassed or short** — a 128-tap FIR at 30 Msps smears ~128 samples
  (4.27 us), which is the entire allowance; bypassed, the halfband chain needs ~30
- **DC-offset and quadrature tracking FROZEN** — otherwise the loops chase each
  antenna's offset on every hop

These are stated here because they are DESIGN INPUTS, not user preferences: the
frame arithmetic in D1 is false without them.

## Status

Stage 0 COMMISSION. Scaffold seeded from the skill templates; no engineering spent.
Next: D-SPEC sourcing spike (SP8T at 70 MHz-6 GHz vs an SPDT tree), then stage 1.
