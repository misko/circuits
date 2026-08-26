---
id: 0001
date: 2026-07-28
status: accepted
tags: [spec-tension, scope]
---
# 0001 — Ku/Starlink is a SEPARATE project, not a variant of this board

## Context

The commission's last sentence (P7, verbatim): *"if possible one PCB version
with just on PCB antennas for ku band starlink"*. Read against the rest of the
same prompt (A2: **70 MHz – 6 GHz**, the full Pluto range) this is not a
board OPTION — it is a second RF chain that shares no component with the first.
Three facts settle it, and none of them is a preference:

1. **The receiver cannot reach the band.** Starlink's user downlink is
   **10.7 – 12.7 GHz**. The ADALM-Pluto's AD9363 tops out at **6 GHz**
   (the ADI-supported ceiling; the "AD9364 hack" reaches 6 GHz, not 12).
   The band centre is **1.94×** the receiver's ceiling. No layout, no
   connector and no switch closes that gap — **a downconverter is
   MANDATORY**, and a downconverter is an active RF subsystem with its own
   LO, its own reference and its own spurious plan.
2. **The laminate cannot carry the band.** This board is `JLC04161H-7628`
   FR4 (ADR-0003). Measured against its own derived loss constant
   (DETAIL_DESIGN §1): **0.036 dB/mm at 6 GHz**, and FR4's dielectric loss
   term scales with frequency — at 11.7 GHz it is ≈**0.055 dB/mm**, so the
   16 mm radial arm on THIS board would cost 0.9 dB before the switch.
   Worse, FR4's Dk is neither controlled nor stable at Ku (glass-weave
   skew alone moves ε_eff by several percent across a 7628 weave pitch),
   and a patch antenna's resonant frequency IS its dimension: an
   uncontrolled Dk is an uncontrolled centre frequency. **Ku needs a
   Rogers-class laminate** (RO4350B or better), which is a different fab
   process, a different tier, and not a JLC default stackup.
3. **The switch would also have to change.** PE42482A-X is guaranteed to
   **8 GHz** (Table 3, PDF p4). At 11.7 GHz it is off the end of every
   published row — not marginal, absent.

The user was asked (Q5) and answered (A5): **ship the 6 GHz SMA board now;
Ku becomes a separate project reusing only the sequencer.**

## Options

- **One board, two populations (an "RF variant").** REJECTED. There is no
  shared part. The laminate differs, the switch differs, the connectors
  differ (Ku wants no coaxial hop at all — the patch feeds the LNA
  directly), and a downconverter must be inserted between antenna and
  switch. A "variant" whose every component differs is two boards sharing a
  filename.
- **One board, Ku-ready footprints left unpopulated.** REJECTED, and the
  reason generalises (see also ADR-0004): an unpopulated RF footprint is not
  electrically absent. A vacant shunt pad on a 50 Ω line is ~0.05–0.1 pF to
  ground — at 6 GHz that is a 265–530 Ω shunt, costing 21–27 dB of return
  loss on a path whose CONSTANCY is this board's entire product (ADR-0006).
  Provisioning for a band this board cannot receive would degrade the band
  it can.
- **Design the 6 GHz board now; open a separate Ku project.** CHOSEN (A5).
- **Design the Ku board first.** REJECTED: it needs a downconverter design
  that does not exist, and the sequencer/timing work (BRIEF D1) is the part
  the user needs first and the part that carries over.

## Decision

**P7 is DEFERRED to a separate project.** This board is 70 MHz – 6 GHz, SMA
only, on FR4. No Ku provision of any kind is carried — no footprints, no
pads, no keep-outs, no stackup compromise.

**What carries over, recorded here so the next project does not re-derive
it:**

| carried | not carried |
|---|---|
| the sequencer section (RP2040 + parallel 3-bit select + pull-downs, ADR-0005) | the RF chain |
| the frame arithmetic (BRIEF D1: 8192/4096 + 128 blank, 62,464-sample frame, 499,712 = 8 sweeps) | the laminate |
| the phase/loss publication policy (ADR-0006) | the switch |
| the radial-star placement archetype (ADR-0007) | the connectors |

**The geometry that makes the Ku project viable, so it is not lost:**

- λ₀ at 11.7 GHz (band centre of 10.7–12.7 GHz) = c/f = **25.6 mm**.
- **λ/2 = 12.8 mm** — the standard AoA element spacing (the largest spacing
  that is unambiguous for a broadside array).
- 8 elements at λ/2 → an aperture of 7 × 12.8 = 89.6 mm, and with a
  half-element margin at each end an outline of about **102 mm** in the
  array axis. That is inside every low-cost panel size, so **the array is
  geometrically comfortable — the electronics, not the geometry, is what
  defers it.**
- At the band EDGES the same 12.8 mm spacing is 0.456 λ (10.7 GHz) and
  0.541 λ (12.7 GHz). The upper edge is **past λ/2**, so a 12.8 mm array
  grates at 12.7 GHz for scan angles beyond ±67°. If the Ku project wants
  the whole downlink unambiguous to endfire, space on the HIGH edge:
  λ/2 at 12.7 GHz = **11.8 mm**, aperture 82.6 mm, outline ≈ **95 mm**.

## Consequences

- **The BRIEF's acceptance criterion for P7 is `dropped — A5`**, and only a
  user utterance could have dropped it. It is recorded as deferred, not met.
- **A patch array cannot use the SMA-per-element rule (P6).** On the Ku
  board each element feeds its LNA on the same laminate; there is nothing to
  connect an SMA to. P6 is a property of THIS board's architecture, not a
  standing requirement — the Ku project must re-ask it.
- **The downconverter's LO becomes the phase reference problem all over
  again**, and harder: eight elements downconverted by one LO is fine, but
  the LO distribution network then owns the constancy requirement that
  ADR-0006 assigns to the switch here.
- **Nothing on this board is allowed to be justified by "it helps Ku
  later".** That is the failure mode this ADR exists to close: a deferred
  requirement that keeps buying real estate.
