---
id: 0013
date: 2026-07-27
status: accepted
tags: [spec-tension]
---
# 0013 — SPEC TENSION T4: "30 dB total" is a scalar; the chain tilts 3.09 dB

## Context

BRIEF A2 fact-locks **30 dB TOTAL, TX → each RX** as a single number, over a
band (A1) of **70 MHz – 6 GHz** — an 85.7:1 span.

D-SPEC requires every numeric requirement to be tested against the
sourceable-part envelope BEFORE architecture. Doing that here produces a
tension the commission did not anticipate: **no chain built from stocked parts
is flat across 85.7:1.** The measured, datasheet-derived non-pad loss is
**6.54 dB at 70 MHz and 9.63 dB at 6 GHz** (DETAIL_DESIGN §3.1), a
**3.09 dB tilt** that is irreducible:

| contributor | 6 GHz share |
|---|---|
| microstrip on the stackup the parts force | 1.91 dB |
| coax interfaces (2 adapters + 2 SMP + 2 launches) | 0.70 dB |
| SPDT insertion loss | 0.65 dB |
| splitter mounting parasitics | 0.35 dB |

Adding a fixed pad shifts the whole curve; it cannot flatten it. **"30 dB"
cannot be true at both band edges**, and reading the requirement as "30 dB at
every frequency" makes it unsatisfiable by ANY design, not just this one.

## Options

- **Silently build to 70 MHz** (pad 23.5 dB): 29.4 dB at the bottom, 32.5 dB at
  the top. REJECTED as a silent choice — but see below, it is one of the three
  legitimate readings.
- **Silently build to 6 GHz** (pad 20.4 dB): 26.5 / 29.6 dB. Undershoots most
  of the band; guarantees ≥30 dB nowhere.
- **Build to the geometric mean, 648 MHz** (pad 23.1 dB). The natural centre of
  a log-frequency span, but it privileges the bottom decade in linear terms.
- **Downgrade the requirement to "≈30 dB"** and move on. REJECTED — D-SPEC
  forbids silently downgrading a requirement as firmly as it forbids silently
  building out of spec.
- **Add active gain flattening / an equaliser.** REJECTED: it makes a passive
  calibration reference active, adds a noise and stability contributor to the
  path whose accuracy is the product, and needs a part that does not exist in
  the LCSC catalogue for this band.
- **MINIMAX: choose the pad that minimizes the worst-case deviation from
  30 dB, privileging no frequency.** CHOSEN, as **D5**.

## Decision

**The pad is `P = 30 − (L(70 MHz) + L(6 GHz))/2 = 21.92 dB`, realized as
21.90 dB at 70 MHz falling to 21.74 dB at 6 GHz** (`YAT-10A+` pre-split,
`YAT-10A+ + YAT-2A+` per arm — ADR-0004).

**30 dB is met at ≈3.0 GHz. The band span is 30.0 −1.6 / +1.4 dB**, and the
guaranteed unit-to-unit envelope across the band is **27.2 – 32.9 dB**.

**The release PUBLISHES loss versus frequency, not a scalar** — the same
reasoning that turned brief D4's length match into a published artifact
(ADR-0011). A calibration board's product is a known number; a number that is
known to be a curve must be shipped as a curve.

**This is an ASSUMPTION MADE IN THE USER'S ABSENCE and it is flagged in the
report.** Per SKILL.md's SPEC-CHECK rule, the simplest reading that satisfies
the stated requirement is taken, recorded as a `D#`, and surfaced loudly.

## Consequences

- **The decision is CHEAP TO REVERSE — one BOM line, same footprint, two
  placements.** Only the arm chain's SECOND part changes:

  | user's reference frequency | build | 70 MHz | 6 GHz | RX1↔RX2 isolation |
  |---|---|---|---|---|
  | 70 MHz or 648 MHz | A2 += **YAT-3A+** | 29.4 dB | 32.5 dB | 31.8 dB |
  | **≈3.0 GHz (minimax — CHOSEN)** | A2 += **YAT-2A+** | 28.4 dB | 31.4 dB | 29.8 dB |
  | 6 GHz | A2 = **YAT-10A+ alone** | 26.5 dB | 29.6 dB | 26.0 dB |

  **Because it is this cheap, it is worth asking rather than assuming
  permanently.** The question to put to the user is: *"at what frequency do you
  want the 30 dB to be exact?"*
- **Erring to MORE attenuation is the safe direction for the RX**, so the
  minimax choice's +1.4 dB at the top is the harmless half of the error.
- **The pad value rests on estimated interconnect loss** and must be re-derived
  after routing (DETAIL_DESIGN §3.6). The build survives any single estimate
  being wrong by 2×; it changes only if all three are wrong the same way.
- **A second, quieter tension is recorded here rather than lost**: the loss
  budget is stated at the **Pluto's own SMA jacks**, so it includes the two
  SMA→SMP adapters, which are NOT on this board's BOM and whose insertion loss
  neither vendor publishes. If the user measures at the board's own SMP
  connectors instead, every number above improves by ~0.1 dB at 70 MHz and
  ~0.3 dB at 6 GHz. **The measurement plane must be stated with the number.**
