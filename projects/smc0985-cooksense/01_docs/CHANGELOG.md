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

## cooksense-v1.4-2026-07-26 (SEAL — documentation-only supersede of v1.3)

Released: `07_releases/cooksense-v1.4-2026-07-26/`.
Supersedes: `cooksense-v1.3-2026-07-26`.

**WRITTEN LATE, 2026-07-27, AND THAT IS THE FIRST THING THIS ENTRY RECORDS.**
v1.4 sealed on 2026-07-26 and this changelog carried NO entry for it — the LIVE
release was missing from its own project changelog for a day, while entries
existed for v1.0, v1.1, interposer-v1.0, v1.3 and interposer-v1.1. `policy_audit`
M-REL had been reporting it as a FAIL (`CHANGELOG missing entry for
cooksense-v1.4-2026-07-26`) and the STATUS beacon carried it under `next:` as
"OWED IN THE TREE, not order-blocking". It is written here, at the v1.5 seal,
rather than backdated into the v1.4 archive — a sealed directory does not gain
files after the fact, and the changelog is a PROJECT document, not part of the
release payload.

**THE BOARD REVISION DID NOT CHANGE.** The F.Silkscreen still reads
`cooksense SMC0985KS sidecar v1.3`, and that is correct: `fab/`, `source/`,
`3d/` and `pdf/` are byte-identical to v1.3's, and v1.3's gerbers remain correct
and orderable. v1.4 exists to correct v1.3's **MANIFEST assembly warning at H4**,
which named the NEAR (south) notch bank at 2.200 mm where the FAR (north) bank at
3.200 mm governs, and quoted the straight-line 3.8286 mm under a *creepage*
claim. The corrected numbers: H4 creepage 6.5984 mm (surface path around the
notch), and a **REQUIRED FASTENER SPEC — max conductive OD 6.0 mm (DIN 125 A2.7),
HARD LIMIT 6.3 mm**, because at OD 6.40 the fastener bridges the notch and
creepage collapses 6.3811 -> 4.7195 mm invisibly. Never a shakeproof washer
(6.5), a DIN 9021 (8.0), or a 6 mm A/F hex standoff (6.93 across corners). The
distinction is written up in `verification/ADR-0015-creepage-is-not-clearance.md`.

**Gates at seal** (quoted from the sealed archive's own MANIFEST): DRC
`--severity-all --refill-zones --schematic-parity` 0/0/0; ERC 0 errors,
1303 warnings; P-COLLIDE 0 pad shorts / 0 courtyard overlaps; E-INV 83/83;
A-ROT 189/189 from authority-table rows; A-POS 189/189 pad-centre-bbox datum,
worst 0.00000 mm; A-POP 226 board / 189 CPL / 37 unpopulated.

v1.1 and v1.0 remain **DO-NOT-ORDER** (22 wrong CPL rotations).

## cooksense-v1.5-2026-07-27 (SEAL — a BUYABLE BOM, and the LDO rail nobody had graded)

Released: `07_releases/cooksense-v1.5-2026-07-27/`.
Supersedes: `cooksense-v1.4-2026-07-26`.

**THE COPPER DID NOT MOVE, AND ON THIS BOARD THAT CLAIM CARRIES NUMBERS.** The
`.kicad_pcb` is md5-identical (`420445b5141dd1111eccab038c68511b`) to v1.4's, to
v1.3's, and to `04_kicad/`'s. Re-plotted from that same board, 11 of 13 gerber /
drill members are GEOMETRICALLY IDENTICAL under an aperture-resolved,
order-independent comparator that shares no method with the plotter; the two
copper layers that differ do so by **3 duplicate / sub-nanometre-collinear G36
vertices out of 29 587**, and the poured-copper AREA is equal to 6 decimal places
on all four copper layers (B 7379.912432, F 2838.968914, In1 8475.761683,
In2 8435.827928 mm², 13/106/1/1 regions on both). `fab/cpl.csv` is byte-identical,
so every A-ROT rotation and A-POS coordinate carries forward untouched.

**HALF ONE — TWO BOM LINES JLC CANNOT SUPPLY.** Read live 2026-07-27
(`selectSmtComponentList`, exact `componentCode` match):

| out | in | why |
|---|---|---|
| `C25744` 0402WGF1002TCE UNI-ROYAL, **stockCount 0** (17 refs: R_BID0/1, R_DOORPD, R_ESTOPPD, R_EXPRST, R_MODEPD, R_OE, R_OS2, R_REF0-7, R_TEMPOK) | `C60490` **RC0402FR-0710KL** YAGEO, stock 8 404 363 | the SAME code and the SAME shortage that forced usb-hub-3s-v3 v1.11 hours earlier, on a different board — a CATALOG event, not a cooksense one |
| `C25862` 0402WGF1201TCE UNI-ROYAL (R_ILM) | `C138040` **RC0402FR-071K2L** YAGEO, stock 472 208 | not out of stock — **unorderable in this quantity**: `minPurchaseNum` 7463 against a `stockCount` that read 25 / 65 / 90 across one afternoon, and the naive `stock >= 5 x qty` test PASSES it |

Both replacements' catalog `describe` strings are **CHARACTER-IDENTICAL** to the
parts they replace, compared AS STRINGS; `componentSpecificationEn` 0402 on both
sides; `leastPatchNumber` 20 on both sides. Both are EXTENDED parts — C25744 was
the only basic-library 10k 0402, so the one-time feeder fee is a property of the
shortage, not of the choice. **CHANGED AT SOURCE, NEVER IN THE CSV** (canon M3):
12 `supplierPartNumbers` sites in `03_tscircuit/src/cooksense.tsx`, `circuit.json`
regenerated by `tsci build`, the BOM regenerated by `export_jlc_package.py`.
v1.0-v1.4 left these refs as bare `<resistor>` for tscircuit's parts engine to
resolve, which is how a catalog snapshot became a BOM line nobody decided; they
are pinned now. New dossiers: `02_parts/RC0402FR-0710KL/`, `RC0402FR-071K2L/`.

**HALF TWO — A BOM ITS RECIPIENT CAN READ.** v1.4's `fab/bom.csv` graded
**F-LEGIBLE FAIL, 83 findings, 0 checks passed**: 55 F-MPN (every coded row ships
a BLANK MPN, so JLC's matcher leaves it at "No Part Selected"), 26 F-WORDS (the
Comment is the LCSC code again), 2 F-ENCODE (`Ω` with no UTF-8 byte-order-mark —
a reader defaulting to cp936 sees `惟`). v1.5: **0 findings, 56 checks**. Nothing
was invented: 54/54 coded rows resolve their MPN against 40 dossiers + 146 vetted
ledger codes, both of which already held the answer.

**HALF THREE — THE 3V3 RAIL, GRADED FOR THE FIRST TIME, AND IT DOES NOT PASS.**
`power_topology.py` gained `LINEAR` on 2026-07-27. v1.4 declared `rails: []` with
the envelopes parked in a parallel `linear_rails:` key the checker ignores by
design, so E-TOPO graded **0 of 1** converters — an LDO-only board reached a green
gate by showing it nothing. v1.5 moves the AMS1117-3.3 rail into `rails:` with
both required numbers CITED to AMS ds1117 (2009-08 RoHS):

- **dropout 1300 mV** — p.3, "Dropout Voltage (VIN - VOUT)", MAX, at **IOUT = 0.8 A**
  (Note 4). Corroborated by C6186's catalog `describe`: `1.1V@(800mA)`.
- **PD 1200 mW** — p.3 Note 2, "maximum power dissipation of 1.2 W for SOT-223".
- **Vout 3.201 / 3.399 V** — p.2, AMS1117-3.3 at VIN = 4.8 V, boldface (full
  operating temperature range). v1.4 carried 3.234/3.366, which is nominal ±2% —
  a plausible-looking number that is not in the datasheet.

  DISSIPATION  PD 690 mW / 1200 mW = **57%, PASS**
  DROPOUT      headroom 1101 mV (Vin_min 4.500 − Vout_max 3.399) vs 1300 mV
               → **FAIL, short by 199 mV**

**THIS RAIL DRAWS 0.3 A AND THE DATASHEET PUBLISHES NO DROPOUT FIGURE THERE.**
p.1 says only that dropout is "guaranteed maximum 1.3V, **decreasing at lower
load currents**"; Note 4 bounds the HIGH side only; and the TYPICAL PERFORMANCE
CHARACTERISTICS page (p.6) has six curves, none of them dropout-vs-load. So the
0.3 A dropout is **OWED** (canon M-OWED), the number declared is the only CITED
one at **2.67× this rail's load**, and `vin_min` was deliberately LEFT at 4.5 —
raising it to 4.75 makes E-TOPO pass with 51 mV to spare, which would be fitting
a number to a gate. **What the arithmetic actually says, and what a human must
decide:** for guaranteed regulation the LDO input needs ≥ 3.399 + 1.300 =
**4.699 V**, so "5 V SELV" (BRIEF §3.5, no tolerance stated) is an
UNDER-SPECIFICATION of this board's supply. Even a ±5% supply (4.75 V) lands at
~4.67 V after the F1/Q_REV/eFuse chain drop. **This is a supply-specification
decision, not a copper defect, and it is not order-blocking** — the boards are
fabbable and assemblable exactly as v1.4 was. It is written into ORDER_README
§0 and it is the ONE `policy_audit` row that does not pass.

**ALSO CLOSED.** M-BOM `UNVERIFIABLE-VALUE` on `220uF [CE1]` (`C2887273`): the
2026-07-23 ledger seed missed it while its own one-digit-away sibling
`C2887276` was already there; the catalog `describe` says `220uF` verbatim and
now so does the ledger. A-BODY: v1.4's `missing_models.txt` was generated with no
`--cpl`, so its denominator was 186 BOARD footprints rather than the 189 CPL
placements, and it counted `J_ISOLOOP` — which is `not_assembled` /
`exclude_from_pos_files` and **is not on the CPL at all**. Regenerated against
`fab/cpl.csv`, the population is the placements JLC will actually run.
`C42400616` (KF350-3.5-4P, J_ISOLOOP) is **still stockCount 0 and still not
substituted**: it is self-supplied, hand-soldered, off the CPL, and the board
would need a footprint change to take any other 3.5 mm 4-pole block — see
ORDER_README.

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
