---
id: 0002
date: 2026-07-23
status: accepted
---
# 0002 — Active-balanced line driver topology & gain (~3 V/V diff)

## Context
The brief requires an OPA1678IDR dual op-amp "active-balanced driver,
~3 V/V diff, values from the doc's table". This CLEAN-ROOM run received the
document's SUMMARY, not its exact resistor table (D1 in BRIEF). The
load-bearing spec is the **3 V/V DIFFERENTIAL gain** from the single-ended
electret to the balanced AUDIO_P/AUDIO_N pair, on a single +5V supply.

## Options
- **Single-ended → one op-amp with gain 3, unbalanced out** — REJECTED:
  not balanced; loses the common-mode rejection the 25 ft outdoor run needs.
- **Instrumentation-amp / cross-coupled active balanced (each output
  senses the other)** — REJECTED for this pass: higher part count / more
  matched resistors than a dual delivers cleanly; the extra output-impedance
  balancing it buys is unnecessary at ~5 mA into a differential ADC input.
- **Two-op-amp symmetric split: A = non-inv +1.5, B = unity inverter of A**
  (ACCEPTED). Uses exactly the OPA1678's two channels. OUTA = VMID+1.5·Vsig,
  OUTB = VMID−1.5·Vsig ⇒ Vdiff = 3·Vsig. Symmetric ±1.5 legs give the best
  single-5V headroom and impedance match for CMRR.

## Decision
Stage A (U1A) non-inverting gain 1+R_fa/R_ga = 1+10k/20k = **1.5**.
Stage B (U1B) inverting gain −R_fb/R_inb = −10k/10k = **−1**, fed from OUTA.
Differential gain = 1.5−(−1.5) = **3.0 V/V** (G2). VMID = 2.5V (22k/22k +
10µF) is the AC reference; DC-blocking series caps (10µF) isolate the 2.5V
bias from the cable. Full value table + corner frequencies in
DETAIL_DESIGN.md. Resistors that set the ratio are 1%.

## Consequences
- **D1 assumption (flagged):** if the doc's table specifies different
  values, a respin swaps R6–R9 with no topology change — the 3 V/V diff
  target is met exactly regardless. Low-frequency corners all sit ≤1.6 Hz,
  well below the audio band, so the exact cap values are non-critical.
- Both op-amp channels are consumed; no spare amp for a VMID buffer, hence
  the RC-bypassed divider (adequate: inputs are high-Z, ~0.1 mA divider).

## Invariants emitted (E-INV)
Into `03_src/rules/electrical_invariants.yaml`, citing adr 0002:
- `series_chain` [OUTA, R_inb(R8), INB] — stage B is driven from stage A's
  output (the balance-generating path exists).
- `net_has_part` VMID carries a capacitor (the reference is bypassed).
