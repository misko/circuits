# BRIEF — pluto-rx2-8way

```
status:          in-progress
prompt_sha256:   1bf0eca3306af5f4ac4556f0b23cb71b8155fde00940bb9b8b9ec8cfc2ba1573
current_release: no
```

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

**Reproduction, verified 2026-07-28** (prompt bytes byte-identical to the
commission commit `4caf0d6`): hash the bytes strictly between the two verbatim
marker lines — from the byte after the opening marker's newline to the byte
before the closing marker — **with the final newline STRIPPED**. The 01_docs
contract's runnable line keeps that newline and so yields
`21708345f8ae…` instead. Same bytes, different terminator; neither digest is
wrong, and the recorded one is the stripped form.

**Two cautions for whoever re-runs it**, both found by doing it:

1. **Do not write either marker string anywhere else in this file.** A second
   occurrence re-opens the `sed` range and the extraction swallows the rest of
   the document. That is how this note was nearly written wrong.
2. `$(...)` in a shell strips *all* trailing newlines, not one — so a
   command-substitution version and a `head -c -1` version agree only when the
   block ends in exactly one.

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
| Q6/A6 | Confirm the reversal of A3, and single 470R arm or split 2x220R? | **2026-07-28: D3 CONFIRMED, with the SPLIT-ARM variant** — the tap is a resistive pickoff built as **2 x 220 ohm in series** (C25091, JLC Basic), not a coupler and not a 6 dB split. See `decisions/0002-spec-tension-pickoff-not-coupler.md` |
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
  (T2). ~~PROPOSED, pending explicit user confirmation, because it reverses
  A3.~~ **CONFIRMED 2026-07-28 (A6), with the SPLIT-ARM variant: 2 x 220 ohm
  in series** (C25091), not one 470 ohm. Measured: tap **-19.83 dB** relative
  to the RX1 output (**-20.26 dB** relative to a plain antenna port), main-line
  insertion loss **0.432 dB**, return loss **26.28 dB**. Splitting the arm puts
  the two 0402 parasitics in SERIES (C_eff ~0.0196 pF vs ~0.0392 pF), cutting
  the 6 GHz tap tilt from **+1.69 dB to +0.43 dB** — and narrowing the band of
  what is UNKNOWN (from the +/-0.02 pF bar on C_p) from **2.73 dB to 0.83 dB**,
  which is the number that actually justifies the second resistor.
  APPLIED in `decisions/0002-*`, `03_src/rules/electrical_invariants.yaml` and
  `02_parts/0402WGF2200TCE/`.
- **D4 — the 8 path phase/loss deltas are a PUBLISHED, MEASURED release
  artifact**, not a design target. P8 permits unequal paths; it does NOT permit
  unknown or drifting ones. The obligation this creates is STABILITY, and it is
  gated at the release, mirroring pluto-cal-switch's published length delta.

## Spec tensions (D-SPEC) — flagged to the user, NOT silently resolved

| # | tension | status |
|---|---|---|
| **T1** | **Ku/Starlink (10.7-12.7 GHz) is 2x beyond the AD9363's 6 GHz ceiling.** On-PCB Ku patches are geometrically fine (lambda/2 @11.7 GHz = 12.8 mm, 8 elements ~102 mm) but downconversion is MANDATORY, and FR4 is unusable at 12 GHz (needs Rogers-class laminate). P7 and A2 cannot be one RF chain | **DEFERRED to a separate project by A5. APPLIED** — `decisions/0001-spec-tension-ku-starlink-deferred.md`. No Ku provision of any kind is carried: not even a footprint, because a vacant shunt pad on a 50 ohm line is ~0.05-0.1 pF and would cost the band this board CAN receive |
| **T2** | **A 70 MHz-6 GHz directional coupler does not exist** — 85.7:1 bandwidth against a coupled-line structure that rolls off 6 dB/octave below its design band. Deeper point: **directionality is not the property being bought.** A coupler separates forward from reverse waves; a receive antenna has one direction. The goal (preserve RX1 sensitivity) is better met by a **resistive pickoff**: -19.83 dB tap, **0.432 dB** main-line loss, 26.28 dB return loss — against 6 dB for a resistive split, or a coupler that cannot span the band | **APPLIED** — `decisions/0002-*`, D3 CONFIRMED by A6. **THE "flat DC-6 GHz" CLAIM IN THIS ROW IS WITHDRAWN**: the tap tilts +0.43 dB by 6 GHz with the split arm (+1.69 dB with a single 470R). The MAIN LINE — the half that costs RX1 sensitivity — IS flat: 0.432 -> 0.437 dB |
| **T3** | **The tapped reference dwell is LEAKAGE-limited above ~2 GHz, and no tap value fixes it.** FOUND AT STAGE 3, 2026-07-28 — T2 optimised only RX1 sensitivity and never computed what a deep tap does to the reference channel's signal-to-interference ratio. On the reference dwell RF8 carries the tapped copy at **-20.26 dB** while the seven live antennas leak into RFC through finite isolation: guaranteed-minimum SIR runs **+34.7 dB (10-100 MHz) / +20.2 / +14.4 / +7.8 / +1.2 dB (4-6 GHz)**. Ordinary antenna dwells are unaffected (**+21.7 dB**, 4.75 deg). The ceiling is the seven live ports' aggregate isolation, so even a lossless 3 dB split reaches only ~18.5 dB at the top of the band | **APPLIED, and FLAGGED TO THE USER** — `decisions/0002-*`. The confirmed 2x220R is KEPT (it costs 0.43 dB of a permanent quantity to give up ~5 dB of a recoverable one); the leakage is computable from the same frame's other seven dwells because the switch is absorptive and the coefficients are constant. **A zero-board-cost lever stays available**: populating `R_T2` as 0 ohm buys +4.84 dB of reference SIR for 0.337 dB more RX1 loss — a BOM change, decidable on order day |

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
| Input rail | USB-C VBUS **4.75 - 5.25 V** (USB 2.0 device-end limits), 0.15 A design envelope | **D-SPEC 2026-07-28** |
| Output rail | **3V3: 3.20 - 3.40 V @ 0.15 A max**, LINEAR (a switcher is refused on RF grounds) | **ADR-0004 / DETAIL_DESIGN section 5** |
| Input protection posture | **PPTC 500 mA -> 5.0 V TVS on the PROTECTED node -> ferrite -> LDO; 5.1k CC pull-downs so overvoltage is unreachable. DELIBERATELY ABSENT: no reverse-polarity block (USB-C is keyed, no second source), no UVLO (nothing stores energy), no inrush limiter (VBUS bypass held to 5.7 uF under the USB 10 uF cap), and NO ESD DEVICE AND NO DC BLOCK ON ANY OF THE TEN RF PORTS** | **ADR-0004** |
| Off-control / source | USB bus-powered; de-energized by unplugging. `source_type: usb_bus_powered_5v`, `quiescent_ua: 0` in `power_tree.yaml` — **E-OFF N-A, and the N-A is stated rather than inferred from silence** | **ADR-0004** |
| Fab tier | **`jlc_4layer_advanced`** on `JLC04161H-7628`, impedance-controlled. Forced by one line of arithmetic: PE42482A-X QFN-24 at 0.50 mm pitch, standard drill 0.30 mm leaves 0.20 mm hole-to-hole against a 0.50 mm floor | **ADR-0003** |

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

## End goal — definition of done

An orderable, assembled PCBA that puts one of eight antennas on PlutoPlus RX2
under free-running parallel control, fast enough that one 499,712-sample buffer
holds exactly eight complete sweeps, with the eighth element shared with RX1
through a tap that costs RX1 less than half a dB — and which ships the measured
per-path phase/loss table that makes the array usable for AoA.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | 8 antennas selectable onto RX2, one at a time | P1 | unmet — no board yet |
| G2 | element 8 is a tap of the RX1 antenna, RX1 keeps its own path | P2 | unmet (designed: `decisions/0002-*`, RX1 through-loss 0.66 dB @70 MHz / 1.17 dB @6 GHz) |
| G3 | switching is sequenced, not operator-driven | P3 | unmet (designed: `decisions/0005-*`) |
| G4 | dwell X on each element, X/2 on the reference, and the asymmetry is the frame marker | P4 | unmet (designed: D1, 8192/4096 + 128) |
| G5 | one ~500k buffer holds whole sweeps at 30 Msps | P5 | unmet (designed: 499,712 = exactly 8 sweeps) |
| G6 | every antenna has an SMA connector | P6 | unmet (designed: 10 jacks) |
| G7 | on-PCB Ku patches for Starlink | P7 | **dropped — A5** (`decisions/0001-*`) |
| G8 | per-path phase/loss deltas are CONSTANT and PUBLISHED | P8/A1 | unmet — the artifact is specified in `decisions/0006-*` and is a release gate |
| G9 | orderable + assembled at the declared tier | D-TIER | unmet (tier decided: `decisions/0003-*`) |

## Decision register

| id | decision (one line) | decided by | depth |
|---|---|---|---|
| — | frame closed at 8192/4096 + 128, buffer = 8 sweeps | agent (D1, P-delegation) | BRIEF D1 |
| — | Ku is a separate project | user (A5) | `decisions/0001-spec-tension-ku-starlink-deferred.md` |
| — | the RX1 tap is a split-arm resistive pickoff, 2x220R | user (A6, reversing A3) | `decisions/0002-spec-tension-pickoff-not-coupler.md` |
| — | 4-layer JLC04161H-7628 at `jlc_4layer_advanced` | agent (D-TIER) | `decisions/0003-stackup-and-fab-tier.md` |
| — | input-protection posture, incl. what is deliberately absent | agent (mandatory ADR) | `decisions/0004-input-protection-posture.md` |
| — | parallel 3-bit control, pulled-down defaults, LS grounded, 47R source-terminated | agent (A4 + DERIVED) | `decisions/0005-control-plane-and-power-on-default.md` |
| — | the 8 path deltas are a published measurement; RF8 carries the reference | agent (P8/A1, D4) | `decisions/0006-path-deltas-are-a-published-measurement.md` |
| — | radial-star floorplan inside a rectangular outline | agent (D-LAYOUT) | `decisions/0007-radial-star-floorplan.md` |

## Status

**Stage 3 DONE (design docs + ADRs + rules), 2026-07-28.** Seven ADRs, ARCHITECTURE
and DETAIL_DESIGN written, all three `03_src/rules/` files replaced (they were
still verbatim skill templates describing other boards), `floorplan.yaml`
written from the D-LAYOUT geometry, and both missing datasheets fetched and
committed so the project is standalone for every part that has a dossier.

Gates at this stage: `contracts_audit` 0 violations; **`P-TIER` PASS** (was the
headline FAIL); `P-ESC` 4/4; `S-VER` 4/4; **`E-ADR` 4/4**; `E-TOPO` N-A earned
against `02_parts`; `E-OFF` N-A. `E-INV` cannot pass before a netlist exists.

Next: stage 2 continuation — the nine remaining part dossiers (`U_LDO` first,
it carries three derived hard constraints), then the two OWED footprints, then
`03_tscircuit/` authoring.
