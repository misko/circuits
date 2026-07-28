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

## cooksense-v1.3-2026-07-26 (SEAL)

Third electrical revision and the safety-chain revision. Supersedes v1.1 and
v1.0, **both now DO-NOT-ORDER** — see their SUPERSEDED.md for the seven defects
they carry, of which four are missing or inverted safety behaviour.

**Board:** 188 x 92 mm, 4 layer, 222 components + 4 holes, 3925 tracks /
1047 vias. DRC 0/0/0. E-INV 83/83. A-ROT 189/189 from measured rows. A-POS
189/189 on datum, worst 0.00000 mm.

**Safety changes.** The opto-isolated 30 V contactor loop left the SELV JST-GH
housing (0.650 mm from ESTOP_RAW in one harness) and now lands on ONE 4-pole
isolated block, `J_ISOLOOP`, with a 2.0 mm moat enforced as pour geometry
(measured 2.0000 mm over all copper on all layers). The door interlock became
fail-restrictive (`R_DOORPU` -> `R_DOORPD`). A hardware open-thermistor detect
was added so a broken or unplugged head reads OVER-TEMP. `R_WDPETPD` gives the
watchdog a real hold-down. `R_TEMPOK` moved to `3V3_ANALOG` so the temperature
verdict is powered by the rail whose health it reports. H4 gained an isolation
notch for mounting-hardware creepage.

**Three P0s were caught inside this cycle and none shipped:** `J_ESTOPLOOP`
placed inside `J_DOOR`; `R_OPENT` ordered at 6.2k where the design needs 62k;
`R_WDPETPD` ordered at 100k where it needs 1k. The last two were the same root
cause — a value-authored passive with no pinned LCSC, resolved by a picker that
returned a wrong decade. All four resistors of the open-detect divider and
R_WDPETPD are now pinned and ledger-verified.

**Deferred to v1.4, declared in the release:** door EOL supervision (a shorted
cable still reads "closed"); R_HYS negative feedback on the open-detect
comparator; TH_CAM sense-net span vs its declared 8 mm budget; the SOD-323
cathode band drawn on a bidirectional part.

Source commit S = 595d197.

## interposer-v1.1-2026-07-27 (Board C RE-SEAL — supersedes v1.0, fab NOT ordered)

Released: `07_releases/interposer-v1.1-2026-07-27/`.
Supersedes: `interposer-v1.0-2026-07-24`, which is **DO-NOT-ORDER**.

**The P0.** v1.0's CPL shipped `J_KEY_MATRIX` (C2683602, JST GH) at rotation
**90.0** where the measured authority says **270.0** — 180 degrees out. It fails
SILENTLY: the GH pad array is symmetric about its own centre, so at 180 every pad
still lands on a pad and the part solders perfectly, while pin 1 <-> pin 10 swaps
and **the whole ten-line keypad ribbon reverses**. The 90 came from the
footprint-NAME rule `^JST_GH_SM,180`, refuted on 2026-07-25 — the day after v1.0
sealed. v1.1 derives 270.0 from the EXACT PAD-FIT path: the measured per-LCSC row
for C2683602 is offset 0 at rms 0.0049 mm vs 5.0792 mm next-best = 1037x
separation, board_rot 270 + 0 = 270.0, re-fitted independently here by `jlc_twin`
at 0.01 mm and matching the sealed main board's own CPL.

**The second P0, and the root cause of both.** Both self-supplied through-hole
10FDZ-BT ZIFs shipped ON v1.0's CPL with a blank LCSC and no declaration
anywhere — the only defence was README prose telling a human to delete two rows.
Root cause: **the entire assembly gate family never ran on v1.0** — its
`policy_audit.md` has no A-* row at all. An absent verdict is not a pass. v1.1
carries A-POP / A-POS / A-ROT / A-POL / A-BODY / A-STOCK / A-EVID / A-RENDER,
all green, plus a new `03_src/interposer/rules/assembly.yaml` with a DATED JLC
catalog query, `exclude_from_pos_files` on the board, and a GENERATED MANIFEST
`not_assembled:` line.

**Also folded in:** a legible BOM (F-LEGIBLE FAIL -> OK: MPN resolved from the
dossier, Comment a real value, UTF-8 byte-order-mark); a `pourless:` declaration
so F-POUR can tell a deliberately pourless board from one that lost its zones;
and a SELF-CONTAINED archive — `kicad-cli pcb drc --severity-all --refill-zones
--schematic-parity` from `source/` alone returns **0/0/0** where v1.0's returns
**29** (its fp-lib-table pointed outside itself and the two unresolvable
footprints were the two ZIFs, the entire point of the board).

**The copper did not move**, measured with an aperture-resolved, order-independent
gerber comparator that shares no method with the plotter: both copper layers, both
masks, both pastes and both drill files IDENTICAL; the profile identical as an
undirected segment set; F.Silkscreen differing by 50 of 5368 atoms, all inside one
0.514 x 0.900 mm cell — the version digit.

**Board:** 54 x 46 mm, 2 layer, 23 parts + 4 holes, 183 segments / 35 vias,
0 zones. DRC 0/0/0. ERC 0/102. policy_audit FAIL=0. E-INV 50/50.

**USER-HELD, unwaived, in ORDER_README section 0:** the 10FDZ-BT POLARITY read
(M9/M10 UNMEASURED — if reversed the board still works and only the TP/KP NAMING
is wrong) and the M3 boss offset (0.190 mm of error against 0.23 mm of clearance,
and it would interfere at the boss's nominal diameter — dry-fit every connector).
The user has measured the part and decided to build with the current footprint.

Source commit S = ee5632a.
