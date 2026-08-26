subject: pluto-rx2-8way-v2 @ 34b3d66b (working tree; `04_kicad/pluto_rx2_8way_v2.kicad_pcb` md5 20f3dd35e00cda51a574a36e62cafbdd, byte-identical to `06_build/staging/source/`)
date: 2026-07-31
reviewer: redteam-agent (Opus 5, fresh context)
lens: RF / electrical integrity — **SCOPED DELTA RE-CHECK** of the 2026-07-31 round-1 RF lens
baseline: `08_reviews/2026-07-31_rf_electrical_lens.md` (graded the board at 9af663f0), verdict SOUND / ORDER
delta under test: 8 GND stitching vias displaced; `min_hole_to_hole` 0.25 -> 0.315 mm

```
design_verdict: SOUND
order_verdict:  ORDER
```

**SCOPE OF THE TWO KEYS ABOVE.** They are this lens's keys, over the
RF/electrical partition only. The archive's own `ORDER_README` §1 declares
DEFECTIVE and DO-NOT-ORDER, for reasons that are entirely outside this
partition — the four contract-required red-team artifacts are absent by design
(A-EVID FAIL), three human assembly gates are owed, and the mixed-class hole
question is unanswered by the vendor. **Nothing here overrides that.** My keys
say: nothing in the RF/electrical partition blocks the order, and the round-1 RF
verdict still holds on the board that exists now.

*(The archive's keys are deliberately spelled out in prose here rather than as
`key: value` at a line start — `M-REV`'s regex allows a leading backtick, so a
quoted second verdict inside the 40-line window is a trap even when
`setdefault` happens to keep the right one.)*

## The answer, in one paragraph

**The round-1 RF verdict holds. I re-measured, and did not re-inherit, every
quantity the 8 displaced vias could touch, plus the three claims the caller
flagged.** DRC on the post-fix board is **0 violations / 0 unconnected / 0
parity, RAW EXIT 0**. The 8 vias are all GND, all 0.2500/0.1500 mm F.Cu→B.Cu
through barrels, and the realized displacement is **0.034713–0.034928 mm**, not
0.035 — a micron-snap residual of at most **0.287 µm**. Everything else on the
board is bit-identical: 199 tracks, 143 pads over 32 footprints, 6 zones with
fill areas equal to **six** decimals (not four), 4 netclasses, 40 nets, and the
`.kicad_sch` UUID-masked sha256 **08c56e16f9ebfbd2 on both sides**. In1.Cu is
**3437.156936 mm² with 0 track segments of any net**, identical pre and post.
The fence gate PASSES at **1.1769 mm worst interior gap, 22 arm-sides, 0 OVER,
RAW EXIT 0**, and the ungraded END segments did **not** regress — the only two
that moved both **improved by 0.0325 mm** (1.5203 → 1.4878 mm, ADR-0005 GREEN
either way). Arm spread is **0.165685 mm = 2.1206°** at 6 GHz against a
12.7991° ceiling, unchanged, with **0 GND vias within 0.305 mm of any arm
centreline**. All three flagged claims are confirmed and restated below; I found
**a fourth claim that also needs restating**, and I settled the 2.2152/2.2142
dispute by showing **both numbers are wrong** for the same reason.

No P0. No P1. Seven P2/P3 items, every one a sentence rather than copper.

---

# 1. What I re-measured, and with what

`04_kicad/` and `07_releases/` were never written. Both boards were copied to a
scratchpad tree (`04_kicad/` + `03_src/lib/*.pretty`, so `${KIPRJMOD}` resolves)
and read there; the original's md5 is unchanged after every run. The pre-fix
board came from `git show 9af663f0:` — never from a stash.

| question | board's instrument | mine, and how it differs |
|---|---|---|
| what moved | `git diff` on 14842 changed lines | pcbnew-level snapshot of every via/track/arc/pad/footprint/zone/netclass/net on BOTH boards, compared as multisets |
| arm geometry | `copper_length_audit` (chain walk) | Dijkstra longest simple path over the F.Cu track-endpoint graph |
| fence pitch | `03_src/fence_pitch.py` | same projection, but centreline from Dijkstra, band **swept** not fixed, and ends graded as well as interiors |
| nearest ground | round-1's 0.05 mm sampler | uniform spatial hash, sampled at 0.05 / 0.005 / 0.001 mm **and** refined to 1 µm around the maximum, from both traversal directions |
| declared barrels | `route.yaml` `seed_stubs` (an assertion) | YAML-parsed the declaration, then went looking for the copper |
| hole-to-hole | `MANIFEST.txt` census | independent 4 mm-grid pair sweep with the vendor's `+0.13 mm` PAD-hole growth applied by pair class |
| ERC | staged `erc.json` | `kicad-cli sch erc --severity-all`, run raw on **both** schematics |

Everything below is **MEASURED** (read off a board or a raw gate run), **DERIVED**
(computed by me from measured inputs), or **INHERITED**. Gates were run
**unpiped**; exit codes captured raw and reported even where the gate cannot
fail.

---

# 2. The delta itself — exactly 8 objects moved, and nothing else did

**MEASURED**, pcbnew snapshot of both boards compared as multisets:

| object class | pre | post | identical? |
|---|---|---|---|
| PCB_TRACK | 199 | 199 | **yes** |
| PCB_ARC | 0 | 0 | yes |
| footprints | 32 | 32 | **yes** (ref, x, y, orientation, layer, lib id) |
| pads | 143 | 143 | **yes** (ref.pin, x, y, size x/y, drill x/y, net, attribute, shape) |
| zones | 6 | 6 | **yes**, including `GetFilledArea()` to 6 dp |
| nets | 40 | 40 | **yes** |
| netclasses | 4 | 4 | **yes** (`RF50` 0.36/0.2/0.6/0.3, `PWR` 0.4, `CTRL` 0.2, `Default` 0.2) |
| PCB_VIA | 3446 | 3446 | **3438 common, 8 displaced** |
| `m_HoleToHoleMin` | 0.250 | **0.315** | changed, as declared |
| `m_HoleClearance` | 0.150 | 0.150 | yes |

The eight, with the realized displacement **MEASURED** (not the declared 0.035):

| pre (x, y) | post (x, y) | Δ mm | dx | dy | net | pad/drill | span |
|---|---|---|---|---|---|---|---|
| 28.6000, 46.2000 | 28.6310, 46.2160 | **0.034886** | +0.0310 | +0.0160 | GND | 0.250/0.150 | F.Cu→B.Cu |
| 29.4000, 39.8000 | 29.3860, 39.7680 | **0.034928** | −0.0140 | −0.0320 | GND | 0.250/0.150 | F.Cu→B.Cu |
| 29.4000, 63.8000 | 29.4070, 63.8340 | **0.034713** | +0.0070 | +0.0340 | GND | 0.250/0.150 | F.Cu→B.Cu |
| 43.8000, 36.6000 | 43.8160, 36.6310 | **0.034886** | +0.0160 | +0.0310 | GND | 0.250/0.150 | F.Cu→B.Cu |
| 50.2000, 60.6000 | 50.2320, 60.6140 | **0.034928** | +0.0320 | +0.0140 | GND | 0.250/0.150 | F.Cu→B.Cu |
| 52.6000, 43.0000 | 52.5930, 43.0340 | **0.034713** | −0.0070 | +0.0340 | GND | 0.250/0.150 | F.Cu→B.Cu |
| 53.4000, 46.2000 | 53.3690, 46.1840 | **0.034886** | −0.0310 | −0.0160 | GND | 0.250/0.150 | F.Cu→B.Cu |
| 59.8000, 28.6000 | 59.7920, 28.6340 | **0.034928** | −0.0080 | +0.0340 | GND | 0.250/0.150 | F.Cu→B.Cu |

**min 0.034713, max 0.034928 — none is 0.035.** The emitter snaps to the
micron, so the radial 0.035 mm becomes 0.0347–0.0349 mm depending on the
direction cosine. The residual is at most **0.287 µm**, which is **0.23 % of a
125 µm via radius**. This is the same micron snap that shows up in §3.1, and it
is the honest way to state the delta.

All eight are **F.Cu→B.Cu** through barrels on **GND**, so every one of them
stitches In1.Cu and In2.Cu — they are reference-plane stitches, exactly as the
brief says.

**They moved AWAY from copper, not toward it. MEASURED**, edge-to-edge to the
nearest non-GND copper (track edge or pad edge, via radius 0.125 subtracted):
worst case **1.5637 mm → 1.5346 mm**. Against an `RF50` scoped clearance floor
of 0.14 mm and a default of 0.20 mm, the move is **7.7× outside any clearance
that binds**. It is electrically inert on clearance, and DRC agrees.

**Gates, raw:**

```
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity   (post-fix board)
  Found 0 violations / 0 unconnected items / 0 schematic parity issues     RAW_EXIT=0
```

> **A trap for the next agent, MEASURED on myself.** My first DRC run reported
> **12 violations**, all `lib_footprint_issues` — *"The footprint library
> 'pluto_rx2_8way_v2' is not enabled in the current configuration"*, one per
> SMA/MCU/switch footprint. That is not the board. `fp-lib-table` resolves the
> project library through `${KIPRJMOD}/../03_src/lib/pluto_rx2_8way_v2.pretty`,
> and my scratchpad had no `../03_src/`. Recreate the two-level tree, or DRC
> invents twelve findings. It is the same class as the 89 ERC
> `lib_symbol_issues` in §3.2 — environment, not schematic.

---

# 3. The three claims that needed fixing

## 3.1 `seed_stubs`: the denominator was wrong BEFORE the fix too

**MEASURED**, YAML-parsed from `03_src/route.yaml` and matched against the saved
boards. The `stubs` list is under `stitch.seed_stubs.stubs`:

| | entries | vias | note |
|---|---|---|---|
| pre-fix (9af663f0) | **24** | **28** | 23 single-via entries + `U_SW.25` which alone carries **5** |
| post-fix (34b3d66b, = working tree) | **32** | **36** | 8 added, **0 removed** |

**The caller's brief says "23 entries = 28 vias". MEASURED it is 24 entries =
28 vias, and round 1's own "23 declared GND barrels — 6 pin-serving and 17
fence" undercounted the same way.** 6 + 17 = 23 entries, but the list also
carries `{net: GND, pin: U_SW.25, vias: [5 coordinates]}` — the switch's
exposed-pad thermal cross. Round 1's §6 table lists six pin-serving pads and
never mentions it. So the pre-fix denominator was **28 barrels, not 23**, and
**five of them were outside the claim entirely.** (All five are real copper —
see the next table — so nothing was hidden; the *count* was.)

Realization, **MEASURED** as distance from each declared coordinate to the
nearest via on the saved board:

| board | declared vias | at d < 1e-9 mm | d ≥ 1e-9 mm | min non-zero d | **max d** |
|---|---|---|---|---|---|
| pre-fix | 36 (of the 28 then declared: 28) | 28 | 8 (not yet placed) | 0.034959 | 0.035041 |
| **post-fix** | **36** | **28** | **8** | **0.000224** | **0.000640** |

**The round-1 sentence "all 23 are real copper at d = 0.0000 mm, exactly" is no
longer true as worded, and the caller is right about why.** The eight new stubs
are declared to four decimals and the emitter writes integer microns, so they
land at **0.000224 – 0.000640 mm**. Restated correctly:

> **All 36 declared `seed_stubs` barrels over 32 entries are real
> 0.2500/0.1500 mm GND vias on the saved board. 28 sit at d = 0.0000 mm
> exactly; the 8 declared to four decimals sit at d = 0.22–0.64 µm, which is
> the emitter's 1 µm write grid and is 0.18–0.51 % of the 125 µm via radius.**

Nearest via on a different net than declared: **0**, both boards. No verdict
moves: 0.64 µm is three orders of magnitude below every clearance, hole and
fence quantity on this board.

## 3.2 ERC is 213 / 0, and 209 was never a property of either board

**MEASURED**, `kicad-cli sch erc --severity-all --format json`, run raw on each
schematic in its own tree:

| schematic | RAW EXIT | violations | `endpoint_off_grid` | `lib_symbol_issues` | errors |
|---|---|---|---|---|---|
| pre-fix (9af663f0) | 0 | **213** | **124** | **89** | **0** |
| post-fix (34b3d66b) | 0 | **213** | **124** | **89** | **0** |
| staged `verification/erc.json` (14:36) | — | **213** | **124** | **89** | **0** |

All 213 are `severity: warning`; there is no error of any severity. **213 is
confirmed on both boards and in the archive, and 209 is not a number either
board produces.** The `.kicad_sch` is the same file in substance — **UUID-masked
sha256 `08c56e16f9ebfbd2` on both sides** (raw sha differs; the `.kicad_pcb`
masked sha correctly *does* differ, 6359e7d2… → 066a4061…), so a schematic-side
delta was never possible.

**Both classes are benign, and I checked rather than assumed:**

* **89 `lib_symbol_issues`** — every one is the single string *"The current
  configuration does not include the symbol library 'elt'"*. That is the
  running KiCad's `sym-lib-table`, not the sheet. Same class as the 12
  self-inflicted `lib_footprint_issues` in §2.
* **124 `endpoint_off_grid`** — every one is *"Symbol pin or wire end off
  connection grid"*. **MEASURED**: the 124 items land on **115 distinct
  positions**, and **115/115 of them are exactly on a 25 mil (0.635 mm)
  grid**, while only **4/115** are on the 50 mil grid KiCad's ERC checks
  against. **111/115 sit at an odd multiple of 25 mil in x or y** — i.e. on the
  sheet's grid and precisely half a step off the checker's.
  *(Reading these out of the JSON needs a scale factor: `kicad-cli` 10.0.4 labels
  `coordinate_units: mm` and then writes positions and lengths in **mm/100** —
  a "Horizontal Wire, length 0.0127 mm" is a 1.27 mm wire. Multiply by 100.)*

Sheet-coordinate audit of the `.kicad_sch` itself, **MEASURED**: 78 wire
endpoints + 89 symbol placements + 46 global labels + 16 no-connects + 5
junctions = **234 coordinates, 234/234 on 25 mil**. The only off-grid vertices
in the whole file are **5 of 12 `polyline` points, and all of them are inside
`lib_symbols`** — the GND-triangle and LED-arrow glyphs, in symbol-local
coordinates, which carry no connectivity.

> **One correction to the brief.** It asks me to confirm "474/474 coordinates".
> I cannot reproduce a 474 denominator from the file and I am not going to
> inherit one. My denominators are stated above: **234/234** sheet connectivity
> coordinates on 25 mil, and **115/115** ERC-flagged positions on 25 mil. The
> conclusion the 474 was supporting is correct; the number is not one I can
> stand behind.

## 3.3 Band-free nearest ground: **both** 2.2152 and 2.2142 are wrong, for one reason

**MEASURED and SETTLED.** Neither number is a property of a board. Both are what
a **0.05 mm sample grid** returns depending on which end of the arm it starts
from, and the true value is neither:

| ANT3, sampling | pre-fix | post-fix |
|---|---|---|
| 0.05 mm, forward from s=0 | **2.2152** | 2.2142 |
| 0.05 mm, backward from s=L | 2.2142 | **2.2152** |
| 0.005 mm | 2.2248 | 2.2248 |
| 0.001 mm | 2.2252 | 2.2251 |
| **1 µm refine around the maximum** | **2.225153** | **2.225130** |

ANT3's arclength is **13.8350 mm**, which is not a multiple of 0.05, so the
forward and backward 0.05 mm grids sample different points and land on opposite
sides of the maximum. The pre/post swap in the top two rows is my own traversal
direction flipping between the two boards (the chain's start vertex depends on
`GetTracks()` order, which the 8 vias perturb) — **not** the copper. The
binding element is **the same via at (27.0000, 59.0000) on both boards**, and it
is not one of the eight.

**The right answer: the band-free maximum over all arms is 2.2252 mm, identical
pre and post to within 23 nm.** Round 1's 2.2152 and the reimplementation's
2.2142 are both **lower bounds from a coarse grid**, understating it by
~10 µm. Neither is "right"; the dispute is an artefact of the instrument.

**And the same instrument defect is bigger elsewhere in round-1's table.**
Round 1 reports ANT6 / RX2_OUT max **1.9609 at s = 13.950** on a 14.000 mm arm.
**MEASURED**: at s = 13.9500 the nearest ground is **exactly 1.9609 mm**; at
s = 14.0000 — the arm's actual terminal point — it is **2.0081 mm**. Round 1's
grid was half-open and never sampled the last point, and *every maximum in that
table sits at a terminal point*. Same for ANT1/ANT5 (1.9597 at 13.9507 →
1.9602 at 14.0007) and ANT7 (1.8336 → 1.8608).

Corrected table, **MEASURED at 1 µm refinement, identical on both boards**:

| arm | round-1 | **corrected max** | at s | note |
|---|---|---|---|---|
| ANT3 | 2.2152 | **2.2252** | 13.821 / 0.014 | worst on the board |
| ANT4 | 2.1024 | 2.1024 | 13.850 | unchanged |
| ANT6 / RX2_OUT | 1.9609 | **2.0081** | 14.000 | +0.047, the largest correction |
| RX1_MAIN | 2.0396 | 2.0396 | 10.900 | unchanged |
| ANT2 | 1.9729 | 1.9729 | 0.000 | unchanged |
| ANT1 / ANT5 | 1.9597 | **1.9602** | 14.001 | +0.5 µm |
| ANT7 | 1.8336 | **1.8608** | 0.000 / 13.835 | +0.027 |
| RX1_TAP | 1.3038 | 1.3038 | 2.790 | unchanged |
| RX1_TAP_MID | 1.0308 | **1.0326** | 0.742 | +1.8 µm |

**The conclusion round 1 drew is unchanged and now rests on a sound number:
nowhere on any RF arm is a ground element more than 2.2252 mm (centre-to-centre;
2.100 mm to the barrel edge) away, every maximum is at a launch antipad or a
switch land, and the board's worst is 9.4 % of λ_pp.**

---

# 4. The fence — and a FOURTH claim that needs restating

## 4.1 The gate, raw, on both boards

```
/usr/bin/python3 03_src/fence_pitch.py <board>
  pre :  WORST 1.1769 mm [RX1_TAP E at s=18.97..20.15], 22 arm-sides, 0 OVER, PASS   RAW_EXIT=0
  post:  WORST 1.1769 mm [RX1_TAP E at s=18.97..20.15], 22 arm-sides, 0 OVER, PASS   RAW_EXIT=0
```

**MEASURED, and it matches the staged `verification/fence_pitch.txt` line for
line**, so the archive's fence artifact is the post-fix board's. My independent
reimplementation reproduces 1.1769 exactly from a Dijkstra centreline.

Bound **1.1910 mm** = λ_pp/20 = λ₀/√er/20 at 6 GHz — re-derived from
`gcpw_constants.txt` and not inherited: λ₀ = 49.9654, λ_pp = 23.8201,
/20 = 1.19100. Margin **1.18 %**.

```
/usr/bin/python3 03_src/fence_apertures.py <board> 0.80
  pre : 3433 PCB_VIA GND + 40 PTH = 3473 elements,  GAP lines: 0
  post: 3433 PCB_VIA GND + 40 PTH = 3473 elements,  GAP lines: 0
```
**The exit code is 0 by construction and is NOT evidence** — the file says so
itself. The evidence is the **grep count of `GAP` lines: 0 on both**, and the
script *does* traceback without `argv[2]`, so the pitch was supplied (0.80,
the declared `stitch_grid` lattice).

## 4.2 The FOURTH claim: "every fence number is unchanged to four decimals" is not true

The fix commit (34b3d66b) states *"Every fence number is unchanged to four
decimals."* **MEASURED, that holds for the headline and not for the table.**
Diffing the two raw `fence_pitch.py` runs, **3 of 22 arm-side rows changed:**

| arm-side | max interior gap | lead-in | run-out | offset rows |
|---|---|---|---|---|
| ANT1 E | **1.1314 → 1.1639** (+0.0325) | **1.520 → 1.488** (−0.032) | 0.382 → 0.382 | 8 → 9 |
| ANT2 W | 0.8000 → 0.8000 | 0.300 | 0.390 | 7 → 8 |
| ANT5 E | **1.1505 → 1.1639** (+0.0134) | 1.930 | **1.520 → 1.488** (−0.032) | 5 → 6 |

Plus the lattice summary (distinct columns 131 → 139, rows 163 → 171 — the 8
displaced vias now sit off-lattice, which is the point). Every other row is
bit-identical.

**Restated honestly:** *the fence VERDICT, the worst interior gap (1.1769 mm at
RX1_TAP E), the arm-side count (22) and the OVER count (0) are unchanged to four
decimals. Two arm-side maxima moved, by +0.0325 and +0.0134 mm, both to
1.1639 mm — still 2.3 % inside the bound and no longer the worst on the board.*
This is a **P2 claim defect in a commit body**, not copper, and it does not
change any verdict. But "unchanged" is the kind of sentence that travels, and
this one is 0.0325 mm off.

## 4.3 The ungraded END segments did NOT regress — they improved

This is the question the caller most wanted answered, because deleting the eight
instead of moving them would have scored identically on the graded metric while
growing two ends from 1.520 mm to 2.652 mm.

**MEASURED**, my own end-segment table at band 2.5 on both boards
(labels are traversal-dependent; the value SETS are what I compare):

| | pre | post |
|---|---|---|
| arm-sides with an END segment over 1.1910 | **8 / 22** | **8 / 22** |
| worst end | **3.8000 mm** (ANT4 W run-out) | **3.8000 mm** (ANT4 W run-out) |
| the two ends that moved | **1.5203, 1.5203** | **1.4878, 1.4878** |
| every other lead-in / run-out | — | **bit-identical** |

**The only two end segments that changed both got 0.0325 mm SHORTER.** Those are
exactly the ANT1/ANT5 ends the commit identified as at risk: 1.5203 → 1.4878 mm,
both **inside ADR-0005's GREEN band (≤ λ_pp/15 = 1.588 mm, accept
unconditionally)** before and after, and nowhere near the 2.652 mm the delete
alternative would have produced (ADR-0005 RED, full-wave required). **The move
bought hole clearance and improved the ungraded metric at the same time.
No ungraded regression exists.**

The eight over-bound ends are unchanged and are carried forward from round-1's
RF-4: ANT4 W (lead-in 2.8600, run-out 3.8000 = λ_pp/6.27), ANT3, ANT5 E, ANT7,
ANT1, ANT6 E, RX2_OUT W, RX1_TAP E.

## 4.4 The `BAND = 2.5` blind spot, now with a number on it

**MEASURED**, sweeping the band constant on the post-fix board (identical on
the pre-fix board):

| band (mm) | worst interior gap | OVER | verdict |
|---|---|---|---|
| 2.400 | 2.3000 (ANT4 W) | 1 | FAIL |
| 2.460 | 2.3000 (ANT4 W) | 1 | **FAIL** |
| **2.465 … 2.539** | **1.1769** (RX1_TAP) | **0** | **PASS** |
| **2.540** | **1.2600** (ANT4 W) | **1** | **FAIL** |
| 2.560 | 1.2600 (ANT4 W) | 1 | FAIL |

**The PASS window in the band constant is (2.460, 2.540) mm — 0.080 mm wide,
with the hardcoded 2.5 default sitting at its exact centre.** And the upper wall
is not arbitrary: **MEASURED, 16 SMA GND posts sit at a perpendicular offset of
exactly 2.5400 mm from an arm** (J_ANT1.3/.4, J_ANT2.4/.5, J_ANT4.2/.5,
J_ANT5.2/.5, J_ANT6.2/.3, J_RX2.3/.4, J_ANT8.4/.5, J_RX1.2/.3). The gate's
verdict is decided by a constant **1.6 % below a real, 16-element ground
population**.

**The failure mechanism, MEASURED, is the blind spot itself.** ANT4 W has
pts[-1] at s = 10.200 and a **3.800 mm run-out that nothing grades**. Admitting
J_ANT4.5 at s = 11.460 does not close a gap — it *extends the interior region*,
converting the first **11.460 − 10.200 = 1.2600 mm** of that ungraded run-out
into a graded interior gap that fails by 5.8 %. Widening the band makes the
metric worse, which no correct measure of "is the wall solid" should do.

**This is round-1's RF-4, unchanged by the delta, now quantified.** It is a
metric finding, not copper: the band-free cross-check in §3.3 says the physical
worst is 2.2252 mm of ground proximity, and ADR-0005's criterion adjudicates
ANT4 W's lead-in on the record. I propose no change to `skills/` here; the
proposal is in §7.

---

# 5. The reference plane and the arms — unmoved

## 5.1 In1.Cu

**MEASURED**, `GetFilledArea()` and a per-layer segment census, both boards:

| layer | filled GND (mm²) | track/arc segments | nets on the layer |
|---|---|---|---|
| F.Cu | 3085.794377 | 173 | 23 signal nets |
| **In1.Cu** | **3437.156936** | **0** | **none** |
| In2.Cu | 3421.569355 | 26 | 3V3, SW_V1–V4, LED_STAT_A |
| B.Cu | 3437.156936 | **0** | none |

**Identical pre and post to six decimals**, which is expected and worth saying
explicitly: the 8 moved vias are on GND inside a GND pour, so they carry no
antipad and displacing them cannot change a fill area. There are also **0
graphic or text items on either inner copper layer**.

**One correction to the round-1 percentage.** Round 1 reports *"3437.16 mm² of a
50.10 × 73.10 = 3662.3 mm² board outline, 93.9 %"*. **MEASURED**: 50.10 × 73.10
is the Edge_Cuts **bounding box**, which is inflated by the 0.05 mm cut-line
width on each side. `GetBoardPolygonOutlines()` gives the true outline area as
**3650.0000 mm²** (50.00 × 73.00). So In1.Cu is **94.1687 %** of the board, not
93.9 % — 93.85 % is what you get dividing by the bbox. **P3.** Either way the
conclusion is untouched: **the RF reference plane carries no routed copper of
any net.** It is punctured only by the 10 SMA centre-pin PTH barrels
(ANT1–ANT7, RX1_MAIN ×2, RX2_OUT), 40 GND posts and 4 NPTH M3 holes — all
already netted out of the 3437.156936 figure.

## 5.2 Arms

**MEASURED**, Dijkstra longest simple path over each net's F.Cu track graph,
identical on both boards:

| arm | length (mm) | ° at 6 GHz |
|---|---|---|
| ANT1, ANT5 | 14.00068 | 179.1965 |
| ANT2, ANT4, ANT6, RX2_OUT | 14.00000 | 179.1874 |
| ANT3, ANT7 | 13.83500 | 177.0759 |

**8-arm spread = 0.165685 mm = 2.1206° at 12.7991°/mm**, against the 1.0 mm /
12.7991° ceiling `nets.yaml` `RF_ARMS.max_spread_mm` declares — **16.6 % of
budget, 6.03× margin**. The caller's "0.1657–0.1660" range is a display
artefact: 0.1660 is what you get subtracting the gate's 4-significant-figure
printed lengths (14.001 − 13.835); the full-precision spread is **0.165685**.

**GND vias whose centre lies within (w/2 + via radius) = 0.305 mm of any arm
centreline: 0, on both boards.** No via touches an arm; the delta could not
have put one there and did not.

## 5.3 The tap topology, spot-checked rather than inherited

Pads are bit-identical between the boards, so this cannot have moved — but a
scoped re-check that quietly re-inherits is worthless, so I re-measured it:

| quantity | MEASURED |
|---|---|
| R_T1.1 (RX1_MAIN) → nearest RX1_MAIN centreline | **0.0100 mm** — a lumped node |
| R_T1.2, R_T2.1 → RX1_TAP_MID centreline | 0.0000 mm both |
| R_T2.2 → RX1_TAP centreline | 0.0071 mm |
| R_T1.2 → R_T2.1 pad-centre separation | **1.1800 mm** |
| RX1_TAP_MID F.Cu copper | 1 segment, **1.2000 mm**, width 0.36 |
| electrical length of the mid line | 1.1800 × 12.7991 = **15.103°** at 6 GHz |

**Confirmed: only R_T1 = 220 Ω is at the junction; R_T2 = 220 Ω is 1.180 mm /
15.10° downstream.** The topology behind the 273.85 Ω / 21.45 dB floor is the
as-built geometry.

---

# 6. Did the corrections land, and do they read honestly?

**YES, MEASURED in `06_build/staging/ORDER_README.md`.**

* **§8a** states the 440 Ω claim is *"overstated by 1.61×"*, names the
  mechanism (R_T1 at the junction, R_T2 1.180 mm / 15.10° downstream), gives
  the corrected floor **273.85 Ω / RL 21.45 dB at 6 GHz** against the published
  440 Ω / 25.39 dB, and — importantly — **keeps the 47× in its correct frame**:
  *"the defect this topology superseded presented 5.80 Ω / RL 1.71 dB … a 47×
  improvement in the worst case, and the tap is SOUND."* It also states the fix
  is owed to `floorplan.yaml`'s intent block at the next revision rather than
  claiming it already happened. **This reads honestly.**
* **§8b** carries the frequency qualifier: the published −20.26 / 0.4322 /
  26.2773 dB are *"exact at 70 MHz"* and measure −21.6399 / −0.5812 / 23.2097 dB
  at 6 GHz, split into ~1.38 dB from the mid line and ~0.43 dB from the 0402
  parasitics, with the recommendation *"coupling ≈ −20.3 dB at 70 MHz, ≈ −21.6 dB
  at 6 GHz"* and the note that the departure is in the safe direction.
* **The silk itself still reads `ANT8 = RX1 TAP -20.26 dB`, unqualified.**
  **MEASURED** on F.Silkscreen of the post-fix board. That is **correct and not
  a finding** — silk cannot change without a new release, and §8b says so and
  carries the qualifier in the one artifact that can.

**Cross-check that the archive describes THIS board**, not the pre-fix one:

| | MEASURED |
|---|---|
| `06_build/staging/source/*.kicad_pcb` vs `04_kicad/` | md5 **identical** (20f3dd35…) |
| MANIFEST sha256 for the pcb / sch | **670fd942… / bdc66687…**, both **match** the files on disk |
| staged `drc.json` (14:35) and `standalone_archive_drc.json` (14:50) | 0 / 0 / 0 |
| staged `fence_pitch.txt` | 1.1769, 22 arm-sides, 0 OVER, PASS — **matches my post-fix run line for line** |
| staged `erc.json` (14:36) | 213 = 124 + 89, 0 errors |
| ORDER_README header | explicitly declares the copper moved and that the four 2026-07-31 lenses graded a different board |

And the fix's own justification, re-derived independently — **MEASURED**, my own
4 mm-grid pair sweep with the vendor's `+0.13 mm` PAD-hole growth applied per
pair class, which reproduces `MANIFEST.txt`'s census exactly:

| pair class | pre nominal → max material | post nominal → max material |
|---|---|---|
| VIA ↔ PTH | **0.3016 → 0.2366** | **0.3265 → 0.2615** |
| VIA ↔ VIA | 0.3785 → 0.3785 | 0.3785 → 0.3785 |
| NPTH ↔ VIA | 0.3768 → 0.3118 | 0.3768 → 0.3118 |
| **pairs under 0.25 mm at max material** | **8** | **0** |

3500 holes on both boards (3446 VIA / 50 PTH / 4 NPTH). The binding pair moved
from `via ↔ J_ANT3.3` to `via ↔ J_ANT8.3`, exactly as the commit predicted the
metric would saturate.

---

# 7. Findings — none blocking

| id | finding | sev | evidence | proposed action (NOT applied) |
|---|---|---|---|---|
| **D-1** | Commit 34b3d66b's *"Every fence number is unchanged to four decimals"* is false at the row level: ANT1 E max interior gap 1.1314 → **1.1639**, ANT5 E 1.1505 → **1.1639**, ANT2 W offset-row count 7 → 8. The verdict, the worst gap (1.1769), the 22 arm-sides and the 0 OVER **are** unchanged | **P2** | §4.2, raw `fence_pitch.py` diff on both boards | The claim is in a commit body and cannot be edited. Restate it in the next `ORDER_README` revision or the seal note: *"the fence VERDICT and worst interior gap are unchanged; two arm-side maxima moved to 1.1639 mm, still 2.3 % inside bound"* |
| **D-2** | The pre-fix `seed_stubs` denominator was **24 entries / 28 vias**, not 23. Round 1's §6 omitted the `U_SW.25` entry and its **5** barrels from both the count and the pin-serving table | **P2** | §3.1, YAML parse of both route.yaml revisions | Correct the denominator wherever it is quoted; the post-fix figure is **32 entries / 36 vias** |
| **D-3** | Round 1's band-free table was computed on a **half-open** 0.05 mm sample grid, so the arm's terminal point — where every maximum lives — was never sampled. Largest instance: ANT6 / RX2_OUT **1.9609 → 2.0081**. The 2.2152 vs 2.2142 dispute is the same defect seen through the grid's phase | **P2** | §3.3; both values reproduced by choosing the sampling direction; 1 µm refinement gives **2.2252** on both boards | Publish **2.2252 mm** as the band-free maximum. If this metric is ever promoted into a gate, sample closed-interval and refine, or the number is instrument-dependent |
| **D-4** | `fence_pitch.py`'s PASS holds only for band ∈ **(2.460, 2.540)** mm — 0.080 mm wide — and the upper wall is **16 SMA GND posts at exactly 2.5400 mm**. At 2.540 the gate reports 1 OVER at 1.2600 mm, which is the first 1.26 mm of ANT4 W's ungraded 3.800 mm run-out becoming interior. Widening the band makes the metric worse | **P2** (carried from round-1 RF-4, now quantified; unchanged by the delta) | §4.4, band sweep on both boards | Two options, neither applied: (a) grade lead-in/run-out against ADR-0005's bands inside the gate, or (b) state in `ARCHITECTURE` §6 that the verdict covers interior gaps only, print the end table, and record BAND's derivation. **Do not simply raise BAND** — 2.54 fails |
| **D-5** | Round 1's In1.Cu coverage **93.9 %** divides by the Edge_Cuts **bounding box** (3662.31 mm²) rather than the outline polygon (**3650.0000 mm²**). The correct figure is **94.1687 %** | **P3** | §5.1 | One number in the next revision |
| **D-6** | The caller-supplied "474/474 schematic coordinates on 25 mil" is not reproducible from the file. My denominators: **234/234** sheet connectivity coordinates and **115/115** ERC-flagged positions | **P3** | §3.2 | Use a stated denominator or drop the number; the conclusion stands on either of mine |
| **D-7** | Running DRC on a copy of `04_kicad/` **without** recreating `../03_src/lib/*.pretty` yields **12 phantom `lib_footprint_issues`**. The 89 ERC `lib_symbol_issues` are the same class on the schematic side | **P3**, process | §2, §3.2 | A line in `skills/kicad-pcb/references/` on how to stage a board for out-of-tree DRC/ERC. **Proposed, not applied** — `skills/` is outside this partition |

**Round-1's four P2s (RF-1…RF-4) all still stand, all still P2**: RF-1 and RF-2
are now discharged into `ORDER_README` §8a/§8b (§6 above); RF-3 is untouched by
this delta; RF-4 is D-4, quantified.

---

# 8. Why the verdict holds, stated plainly

**The round-1 RF verdict of SOUND / ORDER still holds on this board.** What I
re-measured to justify that, rather than inherit it:

1. **DRC raw on the post-fix board: 0 / 0 / 0, exit 0** — both halves, classified
   (the only findings I ever saw were 12 environment artifacts of my own making).
2. **The delta is exactly 8 objects**, verified by comparing every via, track,
   arc, pad, footprint, zone, netclass and net on both boards as multisets —
   199 / 143 / 32 / 6 / 4 / 40 all identical, zone fills equal to **6** decimals.
3. **The 8 are GND F.Cu→B.Cu through barrels**, realized at **0.034713–0.034928 mm**
   (not 0.035), and their worst clearance to non-GND copper is **1.5346 mm**
   against a 0.14 mm floor.
4. **The fence gate passes raw** at 1.1769 / 22 / 0 OVER, my independent
   reimplementation reproduces it, and `fence_apertures.py` emits **0 GAP
   lines** (its exit code disregarded).
5. **The ungraded end segments improved**, 1.5203 → 1.4878 mm on the two that
   moved, all others bit-identical, 8 / 22 over bound before and after, worst
   end 3.8000 mm before and after. **The blind spot the design nearly fell into
   was not re-entered.**
6. **In1.Cu is 3437.156936 mm² with 0 track segments**, identical to 6 dp.
7. **Arm spread 0.165685 mm = 2.1206°**, 0 vias on any arm, both boards.
8. **The tap is still a lumped node** — R_T1 pad 0.0100 mm off the through line,
   R_T2 1.1800 mm / 15.103° downstream — so 273.85 Ω / 21.45 dB is the as-built
   floor, and `ORDER_README` §8a/§8b now say so honestly.
9. **ERC 213 = 124 + 89, 0 errors, on both schematics and in the archive**, with
   both classes traced to their causes; the schematic is the same file
   UUID-masked.

**What would change my verdict:** an ungraded end crossing ADR-0005's amber
(1.985 mm) — nothing is within 0.5 mm of that except the eight long-standing
ends, unchanged; a via appearing on an arm — zero, both boards; or copper on
In1.Cu — zero, both boards.

**What I did not check**, and is somebody else's partition: sourcing and stock,
BOM/CPL correctness, the vendor's unanswered mixed-class hole rule
(`ORDER_README` §7 item 4 — a real DFM item), the three owed human assembly
gates, silkscreen legibility, and the archive's A-EVID/A-POP/`git_dirty` state.
**The archive's own `DO-NOT-ORDER` rests on those, and this review does not
move it.**
