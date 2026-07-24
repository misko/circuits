# Changelog — smc0985-cooksense (MAIN board: cooksense)

Multi-board project (ADR-0007): per-board releases `07_releases/cooksense-v*`.
INTERPOSER (Board C) is deferred (coupon-gated) and has no release yet.

## cooksense-v1.0 — 2026-07-23

Released: `07_releases/cooksense-v1.0-2026-07-23/`. First orderable release of
the MAIN board (252 x 92 mm, 4-layer, JLC advanced small-via).

Pre-seal batch folded in ONE rebuild (full KRT reroute race + deterministic
promoted-chain reuse): SN74HC238 decoder E3 pull-downs (safety: tri-state
float), J_MODE re-pin to the sibling 3V3/GND convention (cross-plug fail-safe),
J_TC footprint 4x dia-1.77 holes per the Omega drawing, PWR_GOOD_N -> EFUSE_FLT_N
honest rename, D_REVCLAMP moved downstream of F1. Ten review findings closed in
`verification/dispositions.md`.

Gates at seal: DRC 0/0/0 + M-REPRO, ERC 0, count_parity 191x4, audit_board PASS
(I-ISO 6.12 mm), policy_audit 0 FAIL (5 evidenced waivers), E-INV 17/17, twin
exit 0 (121 OK / 353), bom_source PASS, stock PASS, fresh zero-context lens
ORDER-OK-WITH-NOTES (both conditional P0s measured green — see
`verification/fresh_lens.md`).

Hand-solder / DO-NOT-SUBSTITUTE: 12x Standex DIP05-1A72-12L + Omega PCC-SMP-K
(ORDER_README). First-power ritual and harness labeling discipline are
NORMATIVE — read ORDER_README before ordering or powering.

## cooksense v1.1 — mechanical repack: rot0 isolation comb, 252x92 -> 188x92 mm
Released: 07_releases/cooksense-v1.1-2026-07-24
Supersedes: cooksense-v1.0-2026-07-23 (v1.0 remains electrically valid)

User directive (BRIEF D7, verbatim): "please schedule a v1.1 revision for
cooksense , lets make the board smaller." The rot90 single row was pitch-bound
at 20mm (19.90mm courtyard ALONG the row — measured, zero shrink available);
user selected the vertical-relay redesign. v1.1: relays rot0/rot180
alternating in pairs @ 15.24mm pitch — the exact orientation the DIP05
"super-column pitch" coupling figure was vetted in, with anti-parallel
adjacent coils (datasheet's own mitigation). The straight barrier becomes an
ISOLATION COMB: contact columns face shared keypad pockets (5 inter-pair + 2
ends), coil-coil gaps carry logic, 12 milled 0.6mm slots, 25 DRC deny rects.
Schematic/netlist BYTE-IDENTICAL to v1.0 (semantic_battery.txt) — placement/
outline only. Board 188x92 (was 252x92), -25% area.

Gates at seal: DRC --severity-all --refill-zones --schematic-parity 0/0/0 +
M-REPRO (2nd deterministic rebuild 0/0/0), ERC 0 err, count_parity 191x4,
audit PASS (I-ISO 6.12mm track-aware on the comb; selftest RED-capable),
placement gates P-OUT 0.30mm / P-CAP 0.21, tier_preflight 0 FAIL, E-INV
17/17 + E-ADR, net_label_survival 155/155, twin exit 0 (121 OK / 353),
bom_source PASS, stock PASS (C25744 order-day recheck noted), policy_audit
0 FAIL. Scoped re-verify per canon: carried v1.0 pin/render reviews
(netlist+parts untouched) + ONE zero-context fresh lens incl. explicit
isolation-comb review — see verification/fresh_lens.md.

NEW in ORDER_README: relay-coupling bench measurement (U+D+PRESS triple
energize, adjacent-relay operate-voltage shift) — a clean result licenses a
future <15.24mm-pitch or two-row revision.

## interposer-v1.0-2026-07-24 (Board C DESIGN SEAL — fab NOT ordered)

First release of the passive keypad interposer (ADR-0009 Path A: rigid board,
two self-supplied JST 10FDZ-BT top-entry ZIFs, GH breakout 1:1 to the main
board's J_KEY_MATRIX, 20 labeled TPs, floating keypad domain — no GND).
54x46mm 2-layer jlc_2layer_default. All gates green (DRC 0/0/0 + M-REPRO,
policy 0 FAIL, PIN/RENDER/2 red-team lenses: ORDER). USER-HELD order gates:
physical 10FDZ-BT land-pattern confirm (datasheet-derived footprint) and the
flex-jumper G1/G2 coupon (separate part). Source commit S = 3e37a02.
