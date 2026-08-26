---
id: 0008
date: 2026-08-11
status: accepted
---
# 0008 — Omit feed-forward capacitors from the mixed output banks

## Context

The fresh pre-route topology review found that ADR-0006 copied the 22pF CFF
recommendations from the 5V table without reconciling them with the actual
output-capacitor populations. U1 includes C22, an exact APAQ
160AV5K101M0606C 100uF polymer whose specified ESR is at most 24mohm.
At that permitted corner its ESR zero is about 66kHz. TPSM63610 Rev. A section
8.2.1.2.6 explicitly says not to use CFF when the output-capacitor ESR zero is
below 200kHz. R25/C27 therefore contradicted the same datasheet they were
intended to follow.

U2 has no identical 200kHz prohibition, but TI recommends its 22pF CFF when
output capacitance is close to the minimum. C9-C11 already provide 40.392uF
effective ceramic capacitance against 30uF required, and C23 adds substantial
low-ESR polymer bulk for TPS25810 cold-socket behavior. Applying the
close-to-minimum compensation example to that mixed bank without a loop model
or measurement is not justified.

## Decision

Remove R25, C27 and C28. Keep both characterized ceramic minimum banks and both
polymer bulk capacitors. The feedback divider ratios are unchanged. First
article must measure frequency response and load-step/startup behavior across
input, load and temperature; no release claim may infer loop stability merely
from a recommended-value table.

For future designs, evaluate the complete fitted output bank before copying a
feed-forward capacitor: minimum ceramic requirement, every additional
ceramic/polymer part, ESR-zero restrictions, CFF zero/pole placement, switching
frequency and placement parasitics are one control-loop decision.

## Consequences

The schematic and PCB lose three fitted passives and the `CFF_A` net. The
current generated artifacts and both pre-route reviews become stale and must be
rebuilt/repeated. U1 now follows TI's explicit prohibition at the admitted
polymer corner; U2 takes the simpler no-CFF state because its bank is not close
to minimum. Exact loop response remains a first-article qualification rather
than a paper-only guarantee.
