---
id: 0007
date: 2026-07-21
status: accepted
---
# 0007 — LX clamp / FET coordination: 60 V AON6262E + per-node TVS (SMAJ15A in, SMAJ24A out)

## Context
v1.0 fitted 30 V AON6354 FETs (Vds 30 V, Vspike10µs 36 V) on LX1/LX2 with
SMAJ30A clamps whose measured table row is VBR 33.3–36.8 V / VC(max) 48.4 V
@ 8.3 A — the TVS begins conducting at/above the FET's spike rating and
clamps 18 V above it. "The FETs protect the TVS, not vice versa" (red-team
A P2-2; external review X3). IP6559 limits that bound any fix: VIN abs 34 V,
BST abs 42 V, VLX abs "−0.3 ~ VIN+0.3" (read as the 34 V VIN rating — the
literal per-pin reading would forbid the chip's own boost topology, where
LX1 legitimately swings to VOUT 21 V > VIN+0.3).

## Options
1. **60 V FETs, keep SMAJ30A** — FET guaranteed (48.4 < 60) but the chip's
   LX/BST pins see up to 48.4/53.7 V in a max clamp event — far over 34/42.
   REJECTED alone.
2. **40 V FETs + lower clamps** — output pair SMAJ24A VC(max) 38.9 V vs
   40 V = 1.03× margin. Guaranteed only on paper. REJECTED (the margin the
   review demanded is exactly what this lacks).
3. **60 V FETs AND per-node lower clamps** — CHOSEN (both margins at once).

## Decision
- **Q4–Q7 (and Q8, same part): AON6262E** — 60 V, DFN5x6 drop-in for
  AON6354, Rds(on) max 8.5 mΩ @ 4.5 V (typ 6.2), Qg(4.5 V) 15 nC,
  Ciss 1.65 nF, Vspike(10 µs) 72 V, LCSC C431185 (stock 3277 at decision
  time). Q8's upgrade also closes the D3-clamp-vs-Q8 leg of X8
  (38.9 V < 60 V).
- **D6 (LX2, input half-bridge, node ≤ VIN 12.6 V): SMAJ15A** — VR 15,
  VBR 16.7–18.5, VC(max) 24.4 V @ 16.4 A (LCSC C148216).
- **D7 (LX1, output half-bridge, node ≤ VOUT 21 V): SMAJ24A** — VR 24,
  VBR 26.7–29.5, VC(max) 38.9 V @ 10.3 A (LCSC C148222; same MPN as D3).

## Coordination table (worst-case corners, sources: part.yamls)
| Stress | Input node (LX2) | Output node (LX1) | Limit it must clear |
|---|---|---|---|
| Normal switching | ≤ 12.6 V + ring | ≤ 21 V + ring | TVS standoff 15 / 24 ✓ |
| TVS breakdown starts | 16.7–18.5 V | 26.7–29.5 V | chip VLX-as-34 V ✓ both; FET 60 V ✓✓ |
| Max clamp (surge) | 24.4 V | 38.9 V | FET 60 V: ×2.46 / ×1.54 ✓; chip 34 V: input ✓, output EXCEEDED (surge-only; recorded) |
| BST = LX + ~5.3 V | ≤ 29.7 V | ≤ 44.2 V (surge-only) | abs 42 V: input ✓; output exceeded ONLY at max-current surge (breakdown-level 34.8 ✓); recorded |

Residual (documented, not waived silently): a maximum-rated surge on LX1
can carry the IP6559's LX/BST pins above abs-max for the surge duration.
No discrete clamp can fit the 21 V-working / 34 V-abs window closer than
SMAJ24A does; the snubbers (R17/C24) + the FETs' 72 V spike tolerance are
the normal-operation defense, and the TVS now protects the FET with real
margin instead of pretending to.

## Consequences
- Conduction loss rises ~0.5 W/always-on FET at the 100 W/9 V corner
  (8.5 vs 5.2 mΩ max at 4.5 V) — folded into the ADR-0008 thermal math.
- SMAJ30A leaves the BOM (02_parts/SMAJ30A removed; numbers preserved in
  the proven-parts harvest and git history).
- part.yamls carry vbr_min/vbr_max/vclamp_max/ipp for every TVS on the
  board (work-order requirement).

## Bench validation (ORDER_README first-power ritual)
Probe VDS of Q4/Q7 and both LX nodes with a 500 MHz+ scope, short ground
spring, at: 5 V/3 A, 9 V-in/20 V/5 A (boost corner), 12.6 V-in/5 V (buck
corner), and during load steps 0↔5 A. PASS: ring peaks < TVS VBR(min)
(16.7 / 26.7 V) — the clamps must NOT conduct in normal service; tune
R28–R31 if they do.
