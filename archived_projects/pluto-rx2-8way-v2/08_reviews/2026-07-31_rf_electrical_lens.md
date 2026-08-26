subject: pluto-rx2-8way-v2 @ 9af663f0 (working tree, 04_kicad md5 c681f1a9c6f989296a50b9a7da8ec7b4; 07_releases EMPTY — nothing sealed)
date: 2026-07-31
reviewer: redteam-agent (Opus 5, RF and electrical integrity lens)
context-given: full-tree, fresh context; prior-round verdicts treated as STALE and re-measured, not inherited
lens: RF / electrical integrity — line type, fence, tap topology, ground return, path equality, drilled features, laminate

design_verdict: SOUND
order_verdict: ORDER

## The two keys, in one paragraph

Every RF claim in my partition that the previous round called defective is
now measurably closed, and I re-derived each one with an instrument that
shares no method with the board's own. DRC on `04_kicad/` is **0 violations
/ 0 unconnected / 0 parity, RAW EXIT 0**. The RX1 pickoff is a lumped node —
`R_T1` pad 1 sits **0.0100 mm** off the `J_ANT8 -> J_RX1` through line, and
the worst-case node impedance over every passive switch state is **273.85 Ω**
against the **5.80 Ω** the old branch line presented, a factor of **47**. The
ground-stitch bound is met: my own reimplementation reproduces the gate's
**1.1769 mm** worst interior gap against **1.1910 mm** with **0 of 22
arm-sides over**, exactly. The 23 declared GND barrels are **real copper at
d = 0.0000 mm** from every declared coordinate, and pcbnew reports **0
unconnected**. In1.Cu carries **zero track copper of any net** — the RF
reference plane is unbroken. The eight arms are congruent to **2.12°** at
6 GHz against a **12.80°** budget.

I found nothing blocking. I found four things worth recording, all **P2**,
and all of them are sentences rather than copper: three claims in the
documentation are stated more strongly than the as-built geometry supports,
and one gate grades less than it measures. Specifically — the tap's published
robustness floor (**≥ 440 Ω / ≥ 25.5 dB**) is the answer for a zero-length
mid line; the as-built 1.180 mm mid line makes it **≥ 273.85 Ω / ≥ 21.45 dB**.
The board is orderable as it stands.

**One thing the caller must act on that is outside my lens but inside my
reading:** the two files `M-REV` actually grades still carry the stale reds
at lines **77-78** and **211-212**, outside the 40-line window. See §8.

---

# 1. What I measured with, and why it is not the board's own answer

| Question | Board's instrument | Mine, and how it differs |
|---|---|---|
| arm length / spread | `copper_length_audit` (chain walk) | Dijkstra shortest path over the track-endpoint graph, endpoints snapped to pad centres. A chain walk takes one traversal from a lexicographically chosen end; Dijkstra is indifferent to traversal order and reports the **snap residual**, which is how I found the ANT3/ANT7 pad-entry convention (§4). |
| ground-stitch spacing | `03_src/fence_pitch.py` | Same projection geometry, but the centreline is the Dijkstra path, the band is **swept** rather than fixed, and I added two band-free metrics (§5). |
| tap node impedance | `01_docs/DETAIL_DESIGN.md` §2, a lumped resistive divider | ABCD cascade over the **as-built** chain `R1 → line(1.180) → R2 → line(25.018) → Z_sw`, self-checked against the lumped limit at 70 MHz, and swept over **every passive** RF8 termination by two independent parameterisations (§3). |
| declared GND barrels | `route.yaml` `seed_stubs` (a config assertion) | parsed the declaration out of `route.yaml`, then went looking for the copper in the saved `.kicad_pcb` (§6). |
| laminate | prose in `ORDER_README.md` | `grep -c '(stackup'` over all 34 sealed boards (§7). |

Everything below is labelled **MEASURED** (read off the saved board or a raw
gate run), **DERIVED** (computed by me from measured inputs), or
**INHERITED** (taken from a repo document without re-measurement). Gates were
run **unpiped**, exit codes captured raw. `04_kicad/` was copied to a
scratchpad and read there; the original's md5 is **unchanged** after every
run in this review, and `git status` on the board directory is clean.

---

# 2. The foundation: what is actually on the board

**MEASURED — DRC, run by me against `04_kicad/` directly:**

```
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity
violations 0   unconnected 0   schematic parity 0   RAW EXIT 0
```

Both halves. The unconnected half is zero, and it is zero independently in
pcbnew's own connectivity API (`GetUnconnectedCount(True) = 0`).

**MEASURED — drilled features, classified:**

| class | n | geometry |
|---|---|---|
| `PCB_VIA` | **3446** | **one class only**: 0.2500 mm pad / 0.1500 mm drill. No second via class exists on this board. |
| PTH pads | **50** | drill 1.4000 mm — the ten SMA jacks × 5 |
| NPTH pads | **4** | drill 3.2000 mm — mounting |
| **min hole-to-hole, EDGE to EDGE** | | **0.3016 mm**, between a 0.150 stitch via at (29.400, 63.800) and `J_ANT4`'s 1.400 PTH at (29.200, 62.742) |

This reproduces the brief's census exactly. 3500 drilled features considered.
3433 of the 3446 vias are on GND; the fence element set is therefore
3433 + 40 PTH = **3473**, which is what both fence instruments report.

**MEASURED — the layer stack, by what copper is on it:**

| layer | track copper by net | zones |
|---|---|---|
| F.Cu | RF arms + the control corridor (`SW_V1` 49.73 mm, `SW_V2` 46.97, `3V3` 45.95, …) | GND fill 3085.79 mm² + 1 rule area |
| **In1.Cu** | **{} — zero track copper of any net** | **GND fill 3437.16 mm², one zone** |
| In2.Cu | control routing (`SW_V3` 18.14 mm, …) | GND fill 3421.57 mm² |
| B.Cu | **{} — zero track copper** | GND fill 3437.16 mm² |

**This is the single most load-bearing fact in my lens and it holds.** The RF
reference plane is a solid unbroken GND sheet — 3437.16 mm² of a
50.10 × 73.10 = 3662.3 mm² board outline, **93.9 %**, with no net of any kind
routed through it. The control corridor that earlier rounds worried about is
on F.Cu and In2.Cu, never on the reference. `line_type.py` independently
confirms In1.Cu is continuous beneath every arm apart from the launch antipad
intervals (1.40–1.75 mm at each launch), which are deliberate.

**MEASURED — the line, re-run raw:**

`03_src/line_type.py` RAW EXIT 0. Every arm measures a GND pour at
**0.2005–0.2010 mm edge-to-edge on both sides** (g/h = 0.96), classified
GCPW over 69.0–93.2 % of its length, mean 78.9 %, 10 of 11 nets ≥ 50 % GCPW.
There is no bare-microstrip section anywhere. `gcpw_constants.py` RAW EXIT 0:
eps_eff **3.1557**, Z0 **51.249 Ω**, t_pd **5.9255 ps/mm**, λ_g 28.1269 mm,
**12.7991 °/mm**, λ_pp = 49.9654/√4.4 = **23.8201 mm**, λ_pp/20 =
**1.1910 mm**. I re-did the wavelength arithmetic by hand and it is right to
the digit. Z0 = 51.249 Ω is **+2.50 %** from 50 Ω — inside any normal
impedance-control tolerance, and worth stating because nothing else does.

The parallel-plate bound is genuinely the tightest of the four candidates
(1.1910 vs microstrip 1.3693, CBCPW guided 1.4063, free space 2.4983), so
moving to the correct cross-section made the requirement **harder**. That is
the right direction for a correction to have moved, and it is why I trust it.

---

# 3. The tap — the finding of this lens

## 3.1 The topology is what the argument needs, and the element at the junction is 220 Ω, not 440 Ω

**MEASURED**, netlist nets 13/14/15 plus pad geometry off the board:

```
RX1_MAIN  (net 13) = { J_ANT8.1 (46.5000,25.0000),  J_RX1.1 (57.5000,25.0000),  R_T1.1 (52.0000,24.9900) }
RX1_TAP_MID (15)   = { R_T1.2 (52.0000,26.0100),    R_T2.1 (52.0000,27.1900) }
RX1_TAP   (net 14) = { R_T2.2 (52.0000,28.2100),    U_SW.19 (42.2500,47.1000) }
```

* `J_ANT8.1 <-> J_RX1.1` copper path **11.0000 mm**, straight-line **11.0000 mm**, 2 segments, 0 vias.
* `R_T1.1` perpendicular offset from that through line: **0.0100 mm**, at **5.5000 mm** along — dead centre.
* `R_T1.2 <-> R_T2.1` pad centres **1.1800 mm**; `RX1_TAP_MID` copper **1.2000 mm**; `RX1_TAP` copper **25.0181 mm**.

So the branch is 0.010 mm, exactly as `floorplan.yaml` claims, and the old
9.903 mm hang is gone. **But the lumped element at the junction is `R_T1` =
220 Ω. The second 220 Ω sits 1.180 mm of 51.249 Ω line downstream — 15.10°
at 6 GHz.** `floorplan.yaml` states the robustness argument as *"With the
whole 440 ohm lumped AT the junction, Z_node = 440 + Z_x for any passive
Z_x, so |Z_node| >= 440 ohm and RL >= 25.5 dB no matter how long the tap arm
is or what the PE42482 presents at RF8 in its seven OFF states."* The whole
440 is not at the junction. That is the thing the brief asked me to verify,
and it is the one place the as-built board departs from its own argument.

## 3.2 What that costs, DERIVED

ABCD cascade, lossless lines (loss only helps), Z0 = 51.249, eps_eff = 3.1557.
Self-check: `zin_branch(0.07 GHz, 50 Ω) = 489.947 − 4.056j` against the
lumped 490.000 — the model degenerates correctly.

**With RF8 matched (the ON path):**

| f (GHz) | \|Z_node\| Ω | RL dB | S21 dB | S31 dB | S31 tilt vs LF |
|---|---|---|---|---|---|
| 0.070 | 489.96 | 26.2767 | −0.4322 | −20.2562 | +0.0000 |
| 1.000 | 481.99 | 26.1384 | −0.4364 | −20.1935 | +0.0627 |
| 3.000 | 422.39 | 25.0352 | −0.4797 | −20.6550 | −0.3988 |
| 4.000 | 391.48 | 24.4051 | −0.5097 | −20.9086 | −0.6524 |
| **6.000** | **338.35** | **23.2097** | **−0.5812** | **−21.6399** | **−1.3836** |

**Guaranteed floor over EVERY passive RF8 termination** — two independent
sweeps, |Γ| = 1 phase (3601 points) and pure reactance jX (12001 points),
agreeing to two decimal places at every frequency:

| f (GHz) | min \|Z_node\| Ω | worst RL dB | worst S21 dB |
|---|---|---|---|
| 0.07 | 439.88 | 25.3879 | −0.4801 |
| 2.00 | 377.57 | 24.0655 | −0.5143 |
| 4.00 | 310.45 | 22.4422 | −0.5931 |
| **6.00** | **273.85** | **21.4480** | **−0.6770** |

Because a lossless line maps the |Γ| = 1 circle onto itself, sweeping every
phase at RF8 is equivalent to sweeping every tap-arm length — so this bound
**is** length-independent, exactly as the argument claims. The argument's
*structure* is correct. Only its *number* is the L_MID = 0 answer:

| L_MID | electrical length @6 GHz | \|Z_node\| floor | RL floor |
|---|---|---|---|
| **0.000 mm** (the claim) | 0.00° | **440.00 Ω** | **25.39 dB** |
| 0.590 mm | 7.55° | 339.16 Ω | 23.27 dB |
| **1.180 mm (as built)** | **15.10°** | **273.85 Ω** | **21.45 dB** |
| 2.360 mm | 30.21° | 235.31 Ω | 20.35 dB |

**Why this is not a defect.** The 1.180 mm mid line satisfies the board's own
stated convention — it is under λ_g/20 = 1.4063 mm *and* under λ_pp/20 =
1.1910 mm, and `nets.yaml` says so explicitly. The design followed its rule;
what I measured is what that rule costs at the band edge. And the numbers it
leaves are good: **worst-case return loss 21.45 dB and worst-case through
loss 0.677 dB across 70 MHz–6 GHz against any switch state.** For scale, the
defect this replaced was a 10.107 mm branch, λ/4 at 4.1744 GHz, presenting
**5.80 Ω** at 4.06 GHz — RL **1.71 dB**, S21 **−14.41 dB**. The fix moves the
worst-case node impedance by **47×** and the worst-case through loss by
**13.7 dB**. It is a real fix, correctly reasoned, and its documented margin
is overstated by 1.61× in impedance and 3.9 dB in return loss.

## 3.3 The published numbers are low-frequency numbers carrying four significant figures

**DERIVED.** My model reproduces `DETAIL_DESIGN.md` §2 to the last digit —
RL **26.2773 dB**, S21 **−0.4322 dB**, S31 **−20.2567 dB** — confirming their
arithmetic is right for the model they state (`Rp = R_T1 + R_T2 + Z0` as a
pure lumped sum, no frequency term anywhere). The silkscreen prints
`ANT8 = RX1 TAP -20.26 dB`, one instance, unqualified.

As built at 6 GHz the same three are **−21.6399 / −0.5812 / 23.2097 dB**. The
0402 parasitics then push the tap the other way: re-deriving part.yaml's own
model (C_p = 0.0392 pF/part → C_eff = 0.0196 pF) I get **+0.4267 dB** at
6 GHz, reproducing its claimed +0.43 dB. Net, the tap coupling is
≈ **−21.2 dB** at the top of the band against **−20.26 dB** on the silk —
about **1 dB** optimistic, all of it from transmission-line transformation
that the published model does not contain.

This is the same substance as the 2026-07-30 render-review's item 18, which
predicted the departure would be "substantial" from parasitics. It is
substantial, but the parasitics are the *smaller* half (0.43 dB); the mid
line is the larger (1.38 dB) and no review has named it before. Silk cannot
change without a new release, so the fix is a qualifier in `DETAIL_DESIGN` §2
and `ORDER_README`: **≈ −20.3 dB at 70 MHz, ≈ −21.2 dB at 6 GHz**.

## 3.4 The series topology is asserted where it can be checked

**MEASURED.** `03_src/rules/electrical_invariants.yaml` carries
`assert: series_chain, chain: [RX1_MAIN, R_T1, RX1_TAP_MID, R_T2, RX1_TAP]`
plus separate `part_value` assertions on `R_T1` and `R_T2`. The middle node
is named precisely so a single-440 substitution is visible to a machine. That
is the right defence and it is in place — a good piece of design, and I say so
because I spent the section above disagreeing with a sentence next to it.

---

# 4. Path-length equality across the eight arms

**MEASURED**, Dijkstra pad-to-pad over F.Cu:

| arm | endpoints | copper (mm) | Δ from mean | Δφ @6 GHz | vias | layers |
|---|---|---|---|---|---|---|
| ANT1 | U_SW.24 → J_ANT1.1 | 14.0007 | +0.0418 | +0.535° | 0 | F.Cu |
| ANT2 | J_ANT2.1 → U_SW.2 | 14.0000 | +0.0411 | +0.526° | 0 | F.Cu |
| ANT3 | U_SW.4 → J_ANT3.1 | **13.8350** | −0.1239 | −1.586° | 0 | F.Cu |
| ANT4 | U_SW.6 → J_ANT4.1 | 14.0000 | +0.0411 | +0.526° | 0 | F.Cu |
| ANT5 | U_SW.13 → J_ANT5.1 | 14.0007 | +0.0418 | +0.535° | 0 | F.Cu |
| ANT6 | U_SW.15 → J_ANT6.1 | 14.0000 | +0.0411 | +0.526° | 0 | F.Cu |
| ANT7 | U_SW.17 → J_ANT7.1 | **13.8350** | −0.1239 | −1.586° | 0 | F.Cu |
| RX2_OUT | U_SW.22 → J_RX2.1 | 14.0000 | +0.0411 | +0.526° | 0 | F.Cu |

**Spread 0.1657 mm = 2.12° at 6 GHz**, against `max_spread_mm: 1.0`
(= 12.80°, itself ≈ 1× the PE42482A-X's own 13.2° part-to-part window). This
is the *exact* number `nets.yaml` records for the no-meander race — my
independent method reproduces it to four decimals. Every arm carries **zero
vias**, all copper on F.Cu, all width 0.360 mm. `no_vias: true` holds.

**A convention worth naming.** `ANT3` and `ANT7` are the two short ones, and
their tracks stop **0.4000 mm short of the SMA pad centre** (snap residual
0.4000; the other six snap to 0.0000). The `J_ANT*.1` pads are 1.900 mm round
on a 1.400 mm drill, so a track endpoint 0.400 mm from centre sits inside the
barrel; the connection is made at the annulus and DRC agrees (0 unconnected).
Measured **to the pad centre** instead, ANT3/ANT7 are **14.2350 mm** — i.e.
**long** by 0.2343 mm, spread **0.2350 mm = 3.01°**. The sign of the outlier
flips with the convention. Both conventions are 4–6× inside the budget, so
nothing turns on it, but a reader who takes 13.8350 at face value will believe
ANT3 is short when its conductor to the SMA pin is the long one. The
geometric radii (switch land centre → jack pad centre) are all
**14.0000/14.0007 mm** — the floorplan is exactly congruent; this is purely a
router pad-entry artefact.

---

# 5. The fence — the bound is met, and the metric grades less than it measures

## 5.1 The gate, and my reimplementation of it

**MEASURED.** `03_src/fence_pitch.py` RAW EXIT 0, `VERDICT: PASS`, worst
interior along-arm gap **1.1769 mm** vs bound **1.1910 mm**, 22 arm-sides,
**0 OVER**. It exits 1 on FAIL (I read the code) — it is a gate that can fail,
and it has failed on this board before.

My independent implementation — Dijkstra centreline instead of chain walk —
reproduces **1.1769 mm worst, 22 arm-sides, 0 OVER** at band ±2.5 exactly.
(I attribute the worst to `RX1_TAP` side W where the gate says side E; that is
a cross-product sign convention, and the *value* agrees to four decimals.)

**MEASURED.** `03_src/fence_apertures.py` needs a lattice pitch as `argv[2]`;
run with the declared **0.80** it reports `3433 PCB_VIA GND + 40 PTH GND
post(s) = 3473` and emits **no aperture line at all**, RAW EXIT 0.
*Caveat, from the file's own header:* this tool **exits 0 by construction** —
it only names causes and never blocks. Its exit code is not evidence. The
absence of GAP lines is, and it agrees with the gate.

## 5.2 The PASS has 1.2 % margin and it moves with the band

**MEASURED**, my implementation, band swept:

| band ±mm | worst interior gap | where | arm-sides OVER 1.1910 | PTH posts admitted |
|---|---|---|---|---|
| 2.00 | **2.3000** | ANT4 W | **6** | 2 |
| **2.50 (shipped)** | **1.1769** | RX1_TAP | **0** | 4 |
| 2.60 | 1.2600 | ANT4 W | 1 | 20 |
| 3.00 | 1.2600 | ANT4 W | 1 | 22 |

`BAND = 2.5` is a *default constant* in `fence_pitch.py`
(`float(sys.argv[2]) if len(sys.argv) > 2 else 2.5`), not derived from the
geometry. **MEASURED**: every SMA GND post on a graded arm sits at
perpendicular **2.5400 mm** (ANT3/ANT7: 2.2572 and 2.8228) — **0.0400 mm
outside the band**. The 2026-07-30 layout lens raised precisely this as L9;
it is still open, and it is now load-bearing in a way it was not then, because
the verdict flipped from FAIL to PASS in the interval.

**The mechanism, measured rather than assumed** (a widening band ordinarily
only shrinks gaps): at ±2.60 mm, ANT4 W admits an 11th element at s = 11.460 —
`J_ANT4.5`, an SMA GND post at perpendicular 2.5400 — which **extends the
graded span** from 2.860–10.200 to 2.860–11.460 and exposes a 1.2600 mm gap
the ±2.5 band never looked at. Adding a point beyond the current extremes can
grow the maximum consecutive gap; there is no contradiction, but there is a
conclusion: **the verdict is decided by which elements the band admits at the
arm ENDS.**

## 5.3 Lead-in and run-out are printed and not graded

**MEASURED, from the gate's own source.** `fence_pitch.py`'s verdict is
`worst = max(interior gaps)`. `lead-in` (`pts[0]`) and `run-out`
(`L - pts[-1]`) are printed in their own columns and enter no comparison.
Eight arm-sides carry an end segment longer than the 1.1910 mm bound. I
classified every one by what ground is actually there, rather than counting
them:

| arm/side | segment | length | nearest SAME-SIDE ground inside it |
|---|---|---|---|
| ANT4 W | run-out | **3.8000** | PTH `J_ANT4.5` at perp **2.5400** — 0.0400 mm outside the band |
| ANT4 W | lead-in | **2.8600** | via at perp **3.7000** — genuinely distant |
| ANT7 W | lead-in | 2.3730 | via at perp 2.5385 |
| ANT3 W | run-out | 2.2270 | via at perp 2.5809 |
| ANT7 W | run-out | 2.0150 | via at perp 2.7931 |
| ANT5 E | lead-in | 1.9300 | via at perp 3.0123 |
| ANT6 E / RX2_OUT W | run-out | 1.9000 | via at perp 2.5500 |
| ANT1 W / ANT5 E | run-out | 1.5200 | via at perp 2.7224 |
| ANT3 W | lead-in | 1.4390 | **none at any lateral distance** |
| RX1_TAP E | lead-in | 1.2400 | **none at any lateral distance** |

Against ADR-0005's own bands (green ≤ 1.588, amber ≤ 1.985, red ≤ 3.970,
veto > 3.970 mm): the two segments with genuinely no same-side ground are
both **GREEN** (accept unconditionally). Six of the rest are band artefacts —
the ground is there, at 2.54–3.01 mm, just outside a 2.5 mm constant. **One is
real: `ANT4` side W, lead-in 2.860 mm with the nearest same-side ground at
3.7000 mm — λ_pp/8.33, ADR-0005 RED.** ADR-0005's condition C1 (opposite flank
compliant over ±L_a) holds for it: ANT4 side E has max interior gap 0.8000 mm
with lead-in 0.320 and run-out 0.450.

## 5.4 The band-free cross-check, which is what settles it

**MEASURED** — no band, no side, no first/last truncation: distance from every
0.05 mm sample of every arm to the nearest GND element on the board.

| arm | median | p95 | **MAX** | at s | where |
|---|---|---|---|---|---|
| ANT3 | 0.8580 | 1.7436 | **2.2152** | 13.800 | jack end |
| ANT4 | 0.9014 | 1.6225 | 2.1024 | 13.850 | jack end |
| RX1_MAIN | 1.2258 | 1.9416 | 2.0396 | 10.900 | jack end |
| ANT2 | 1.1597 | 1.6985 | 1.9729 | 0.000 | switch end |
| ANT6 / RX2_OUT | 0.6964 | 1.3647 | 1.9609 | 13.950 | jack end |
| ANT1 / ANT5 | 0.7456 | 1.4842 | 1.9597 | 14.000 | jack end |
| ANT7 | 0.6386 | 1.3949 | 1.8336 | 13.800 | jack end |
| RX1_TAP | 0.6519 | 1.0263 | 1.3038 | 2.790 | — |
| RX1_TAP_MID | 0.8262 | 1.0198 | 1.0308 | 0.750 | — |

**Nowhere on any RF arm is a ground element more than 2.2152 mm away**
(2.09 mm to the barrel edge), and every single maximum sits at s ≈ 0 or
s ≈ L — the launch antipad or the switch land, the two places a via is
forbidden for a reason. Median ground proximity is 0.64–1.23 mm.

For provenance: the 2026-07-30 layout lens ran the same band-free
cross-check and got RX1_MAIN 2.3230, ANT2 2.3162, ANT6 2.2947, ANT7 2.2444.
Today the worst is 2.2152 and RX1_MAIN is 2.0396. **The board improved on
this metric too, and it improved on the metric nobody was optimising against**
— which is the strongest single piece of evidence I have that the fence work
was physical rather than parametric.

## 5.5 Verdict on the fence

The bound is met by the gate, by my reimplementation, and by the ADR-0005
criterion applied to the ungraded ends. The residual is a **metric** finding,
not a copper one: a 1.2 % margin decided by a 2.5 mm constant that sits
0.04 mm inside the SMA post ring, and an end-segment class the gate prints
and does not judge.

---

# 6. The declared GND barrels are copper, not configuration

**MEASURED.** I parsed all `seed_stubs` entries out of `03_src/route.yaml` —
**23** GND barrels, 6 pin-serving (named pad) and 17 fence — and then went
looking for each in the saved `.kicad_pcb`.

**All 23 are present as real 0.2500/0.1500 mm GND vias at d = 0.0000 mm from
the declared coordinate.** Not "within tolerance" — exact.

The six pin-serving pads, individually:

| pad | pad centre | size (mm) | vias inside pad | declared site in In1.Cu GND fill | pad centre in F.Cu GND fill |
|---|---|---|---|---|---|
| R_PD1.2 | (40.200, 53.110) | 0.540 × 0.640 | **1** | **True** | True |
| R_PD2.2 | (41.500, 53.110) | 0.540 × 0.640 | **1** | **True** | True |
| C_SW1.2 | (42.800, 53.080) | 0.560 × 0.620 | **1** | **True** | True |
| R_PD3.2 | (41.200, 55.310) | 0.540 × 0.640 | **1** | **True** | True |
| R_PD4.2 | (42.500, 55.310) | 0.540 × 0.640 | **1** | **True** | True |
| C_SW2.2 | (40.825, 57.000) | 0.900 × 0.950 | **1** | **True** | True |

Each has exactly one barrel bonding it to the solid In1.Cu plane. Board-wide:
pcbnew connectivity **unconnected = 0**, and my own sweep of every GND
terminal for "no fill, no via-in-pad, no track endpoint" returns **0**.

The brief said "six barrel windows"; the board carries six *pin-serving*
barrels covering all six pocket terminals — not only the two that happened to
strand on one route draw, which `route.yaml` explains is deliberate because
*which* two strand is a property of the route race. That is the right
generalisation and it is executed. **This is a declaration that was
discharged in copper, and it is verifiable without trusting the config that
made it.**

---

# 7. The laminate: no `(stackup)` block anywhere, and my judgement on it

**MEASURED.** `grep -c '(stackup'` returns **0** on the working
`04_kicad/pluto_rx2_8way_v2.kicad_pcb` and **0 on all 34 sealed
`projects/*/07_releases/**/*.kicad_pcb`**. The brief's fleet-wide claim is
confirmed by my own sweep.

**Is that acceptable for an impedance-controlled board? Yes, for this order —
with one thing named.**

What argues for acceptance, all MEASURED in `06_build/staging/ORDER_README.md`:

* the laminate is named as **REQUIRED, not a preference** — `JLC04161H-7628`,
  h = 0.2104 mm, Dk = 4.4, t = 0.035 mm — with the full derivation chain to
  RF50 = 0.36 mm and λ_pp/20 = 1.1910 mm, and an explicit instruction not to
  accept a substitute without re-running `gcpw_constants.py`;
* **impedance control is REQUESTED** as a line item, with the reason ("the
  board's product IS impedance");
* copper weight is pinned to **1 oz / 35 µm**, which is the `t` the constant
  set was solved at, and the document says why 2 oz would invalidate it;
* the absence of the `(stackup)` block is **disclosed in the document itself**,
  measured fleet-wide, and booked as an open item in its §7 rather than
  hand-patched into a generated board (canon M3).

The operative reason it is acceptable is that **JLCPCB's impedance-control
flow is driven by the order form and the stackup selected there, not by the
`.kicad_pcb`'s stackup block.** `JLC04161H-7628` is a JLC-published stackup,
0.2104 mm is its top prepreg, and the fab will read the laminate where this
release states it. Nothing in the fabrication path consumes the missing block.

**What is genuinely lost, and it is a process cost rather than an order
risk:** nothing *machine-readable inside the archive* states the laminate, so
a future regeneration cannot be gate-checked against the geometry it was
solved for. A 0.36 mm line on a different prepreg thickness is a different
impedance and no instrument in this repo would notice. The board's own
`line_type.py` and `gcpw_constants.py` both take `h` as a **declared** input
they print and never verify — they say so in their headers. That is the real
gap and the ORDER_README already names it.

One number nobody states: the derived **Z0 = 51.249 Ω is +2.50 % from 50 Ω**.
Inside any normal ±10 % impedance-control tolerance, but it should be the
number written on the order form, not 50.

---

# 8. Coupling, and two prior findings re-measured

**MEASURED**, F.Cu, edge-to-edge between RF nets:

| pair | closest approach | GND pour on the connector |
|---|---|---|
| ANT3 ↔ ANT4 | 0.6299 mm | at the switch fan-out |
| ANT1↔RX2_OUT, ANT2↔ANT3, ANT5↔ANT6, ANT6↔ANT7 | 0.6400 mm | yes |
| RX1_MAIN ↔ RX1_TAP_MID, RX1_TAP ↔ RX1_TAP_MID | 0.6400 mm | across the resistor bodies — the intended series elements, not coupling |
| ANT7 ↔ RX1_TAP | 0.9610 mm | yes |
| RX2_OUT ↔ RX1_TAP | 1.1400 mm | yes |

**REFUTED — the 2026-07-30 render-review item 18's coupled path.** It stated
that "on F.Cu `RX1_MAIN` and `RX1_TAP` run parallel for ~12 mm at ~0.75 mm
pitch (measured near x = 46 mm)". On the current board **`RX1_MAIN` spends
0.000 mm of its 11.000 mm within 1.5 mm of `RX1_TAP`** — 0.0 %. The tap now
leaves the through line perpendicular at x = 52.0 and detours north-west. That
finding is stale and the layout change closed it.

**Still true, and recorded rather than raised:** `RX1_TAP` runs within 1.5 mm
of `ANT7` for **7.550 mm of its 25.018 mm (30.2 %)**, closest approach
0.9610 mm edge-to-edge with GND pour between them (6 of 19 midline samples
inside the F.Cu GND fill). Both are grounded coplanar lines with a 0.2005 mm
pour gap on each side, which is what suppresses this; `RX1_TAP` is also the
one RF net deliberately excluded from the graded phase table, so the coupled
length is on the ungraded side. Not a finding — stated so a successor does not
have to re-measure it.

## The thing the caller must act on

Outside my lens, but I read it while locating the verdict-key window and it
bears directly on why this round exists. `M-REV`
(`skills/jlcpcb-fab/scripts/release_freshness_check.py`) grades exactly two
filenames — `_REVIEW_LENS_FILES = ("redteam_topology.md",
"redteam_layout.md")` — and reads only `_REVIEW_HEADER_LINES = 40`.

**MEASURED** in `06_build/staging/verification/`:

| file | verdict keys at line | value |
|---|---|---|
| `redteam_layout.md` | **77–78** (of 78) | `design_verdict: DEFECTIVE` / `order_verdict: DO-NOT-ORDER` |
| `redteam_topology.md` | **211–212** (of 212) | `design_verdict: DEFECTIVE` / `order_verdict: DO-NOT-ORDER` |

Both are outside the 40-line window, so M-REV will score
**REVIEW-NO-VERDICT twice** — and a missing verdict is a FAIL, never a skip.
Two consequences: (i) the task-#66 failure mode is still live and unfixed on
the files that matter; (ii) **this file's name is not in `_REVIEW_LENS_FILES`,
so my keys reach M-REV only if this content also lands in one of those two
exact filenames.** I have put my keys at lines 7–8 regardless.

---

# 9. Findings

| id | finding | severity | evidence | what closes it |
|---|---|---|---|---|
| **RF-1** | `floorplan.yaml`'s tap robustness claim — *"\|Z_node\| >= 440 ohm and RL >= 25.5 dB no matter how long the tap arm is"* — is the answer for a **zero-length** mid line. As built, `R_T1` (220 Ω) is at the junction and `R_T2` (220 Ω) is 1.180 mm / 15.10° downstream, so the floor over every passive RF8 state is **273.85 Ω / 21.4480 dB / −0.6770 dB**, not 440 Ω / 25.5 dB. The argument's *structure* (a resistor at the junction makes the floor length-independent) is correct and I confirmed it. | **P2** | §3.2; ABCD cascade self-checked to 489.947 Ω at 70 MHz against the lumped 490.000; two independent worst-case sweeps agreeing to 2 dp; L_MID → 0 reproduces exactly 440.00 Ω | One sentence in `floorplan.yaml` and `ARCHITECTURE`: state the as-built floor with its mid-line term. No copper change — 21.45 dB worst-case RL is a good number, and the alternative (co-locating both resistors) would forfeit the series-parasitic property that is the reason there are two |
| **RF-2** | `DETAIL_DESIGN` §2 and the silkscreen publish −20.26 / 0.4322 / 26.2773 dB to four significant figures with **no frequency qualifier**. They are exact at 70 MHz and ~1 dB optimistic at 6 GHz: measured as-built −21.6399 / −0.5812 / 23.2097 dB, with the 0402 parasitics returning +0.4267 dB of the tap. The mid line contributes **1.38 dB** of the departure and the parasitics **0.43 dB** — the larger half has not been named before | **P2** | §3.3; my model reproduces all three published numbers to 4 dp, and part.yaml's +0.43 dB tilt independently | A qualifier, not a number change: *"≈ −20.3 dB at 70 MHz, ≈ −21.2 dB at 6 GHz"*. Silk cannot change without a new release; `ORDER_README` can carry it now. Duplicate-in-substance of render-review item 18, which is still open |
| **RF-3** | The fence PASS has **1.2 % margin** (1.1769 vs 1.1910) and moves with a band that is a hardcoded default: ±2.60 mm → 1 arm-side over at 1.2600; ±2.00 mm → **6** over, worst 2.3000. Every SMA GND post sits at perpendicular **2.5400 mm**, 0.0400 mm outside the ±2.5 band | **P2** | §5.2, my own implementation; mechanism traced to `J_ANT4.5` entering ANT4 W's graded span at s = 11.460 | Derive the band from the geometry (post radius + margin ⇒ ~2.60 mm) and re-state the verdict there, or record why 2.5 governs. Re-raises 2026-07-30 layout finding **L9**, which was never closed and now decides a verdict it did not decide then |
| **RF-4** | `fence_pitch.py` grades **max interior gap only**; lead-in and run-out are printed and enter no comparison. Eight arm-sides carry an end segment over the bound, worst **ANT4 W run-out 3.800 mm** (λ_pp/6.27). Classified: six are band artefacts (same-side ground at 2.54–3.01 mm), two are inside ADR-0005 GREEN, and **one is real — ANT4 W lead-in 2.860 mm with nearest same-side ground at 3.7000 mm**, λ_pp/8.33, ADR-0005 RED with C1 satisfied | **P2** | §5.3, §5.4; band-free maximum over all arms is **2.2152 mm**, every maximum at an arm end | Either grade the ends against ADR-0005's bands inside the gate, or state in `ARCHITECTURE` §6 that the verdict covers interior gaps only and give the end-segment table. ANT4 W's lead-in wants an ADR-0005 C1–C5 adjudication on the record |
| **RF-5** | `RX1_TAP` runs within 1.5 mm of `ANT7` for 7.550 mm of 25.018 mm (30.2 %), closest 0.9610 mm, GND pour between | note | §8 | Nothing. Recorded so it is not re-discovered. The competing finding it replaces — RX1_MAIN ∥ RX1_TAP for ~12 mm — is **REFUTED**: 0.000 mm of 11.000 |

**No P0. No P1.**

---

# 10. Why SOUND / ORDER

The board's RF deliverable is nine equal-radius grounded-coplanar arms whose
relative phase is published, tapped by a resistive pickoff. Measured, in my
own instruments:

* the arms are congruent to **2.12°** at 6 GHz against a **12.80°** budget,
  carry **zero vias**, and their geometric radii are identical to 0.7 µm;
* the reference plane beneath them is a **single unbroken GND sheet with zero
  routed copper on it**, 93.9 % of the board outline;
* the coplanar wall is **0.2005–0.2010 mm** on both sides of every arm, and
  the fence that shorts it to that plane meets the correct, tightest of four
  candidate bounds, verified by an instrument I wrote;
* the tap is a lumped node at **0.0100 mm** branch, with a worst-case node
  impedance **47× better** than the defect it replaced and a worst-case
  through loss of **0.677 dB** across the whole band and every switch state;
* the ground declaration that closed the stranded pads is **copper at
  d = 0.0000 mm**, and the board reports **0 unconnected** by two methods;
* DRC is **0 / 0 / 0, RAW EXIT 0**, both halves.

The four P2s are all of one kind: **documents that state a bound more
strongly than the geometry supports, and one gate that measures more than it
grades.** Not one of them is a defect in copper, and not one of them changes
what the board does when it is powered. A first article built to these
gerbers will work, and it will work close to its published numbers — within
about 1 dB on the tap at the top of the band, which is worth writing down and
is not worth a respin.

I looked hard for a reason to withhold ORDER and did not find one. Reporting
that plainly is the finding.

---

## Provenance

Instruments I wrote for this review (scratchpad, not committed):
`indep_measure.py` (pad-graph Dijkstra, via census, hole-to-hole),
`arm_ends.py` (pad-entry geometry), `tap_rf2.py` (ABCD cascade + worst-case
sweeps), `verify_stubs.py` (declaration → copper), `fence_indep.py`
(band sweep), `fence_bandfree.py` (nearest-ground + band mechanism),
`aperture_free.py`, `runout.py`, `coupling2.py`.

Board gates re-run raw, unpiped: `kicad-cli pcb drc` (exit 0),
`03_src/line_type.py` (exit 0), `03_src/gcpw_constants.py` (exit 0),
`03_src/fence_pitch.py` (exit 0, PASS), `03_src/fence_apertures.py`
(exit 0 with `argv[2] = 0.80`; **it exits 0 by construction and its exit code
is not evidence**).

`04_kicad/` and `07_releases/` were opened read-only. `04_kicad/`'s md5 is
`c681f1a9c6f989296a50b9a7da8ec7b4` before and after every run in this review.
No file under `skills/` was modified.
