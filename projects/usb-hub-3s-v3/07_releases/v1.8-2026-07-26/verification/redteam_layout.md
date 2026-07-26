# redteam_layout — contract-named copy

> **PROVENANCE.** This is the CURRENT layout red-team for this board, shipped under the name
`07_releases/contracts.md` requires. It is a VERBATIM COPY of
`08_reviews/2026-07-25_v1.5_redteam_layout.md`, which remains in place — dated
history lives in `08_reviews/`, the contract name ships in the release, and the
file is COPIED rather than moved so the provenance survives in both places.

Lineage: this v1.5 layout red-team supersedes `2026-07-22_v1.0_redteam_layout.md`
(also carried in this directory under its dated name). Both are retained; the v1.5
pass is the one that graded the copper this release ships.
>
> Source: `08_reviews/2026-07-25_v1.5_redteam_layout.md` (sha256 in this release's MANIFEST under both names).

---

subject: usb-hub-3s-v3 v1.5-2026-07-25 (copper as sealed since v1.3)
date: 2026-07-25
reviewer: redteam-agent (layout / thermal / power-integrity lens)
context-given: full-tree
verdict: ORDER

---

# Red-team review — layout / thermal / power-integrity lens

**Board under review**
`04_kicad/usb_hub_3s_v2.kicad_pcb`, md5 `095a65f43630cd9d35a93301ebb112e0` —
**byte-identical** to `07_releases/v1.5-2026-07-25/source/usb_hub_3s_v2.kicad_pcb`
(md5 verified equal). 130.10 × 92.10 mm, 4 layers (F.Cu / In1=GND / In2=VIN /
B.Cu), 124 footprints, 791 track segments, 280 vias, 46 zones.

**Why this review exists.** The only prior layout/thermal lens
(`2026-07-22_v1.0_redteam_layout.md`, verdict ORDER) was written against v1.0
copper. I independently re-confirmed the gap by grep over that file: **zero
occurrences** of Q6, Q7, F2, D5, R30, R34, R35, C53, C54, SW1, PMID, VBUSC, QG,
snubber, PPTC, polyfuse. Its own §4 ampacity table lists the plane-less nets as
`VBAT_F, VBAT, SW_A, SW_C, 5VA, 5VC, VBUSA1-3, CS_A, CS_C` — **PMID and VBUSC are
absent because they did not exist**. The discrete USB-C VBUS protection chain and
both SW-node snubbers have therefore never been layout- or thermally reviewed.
That cluster was my priority and it is where the findings landed.

**Verdict: ORDER.** No P0. The board works and the project's own E-MARGIN gate
still passes — but with materially less slack than the design documents claim,
and with one build hazard that must reach the assembly instructions.

---

## 1. Findings

| id | sev | finding | MEASURED evidence | recommendation |
|---|---|---|---|---|
| **RL-1** | **P1** | **PMID's F.Cu pour is bisected by the QG gate route.** The entire 5 A USB-C rail crosses from Q6's source to F2's input through **two 0.30 mm vias in series** — a verified sole path with zero redundancy. | Polygon booleans: PMID F.Cu = **2 disjoint outlines** — `#0` 18.28 mm² bbox (105.50,87.50)-(108.95,94.78) holds Q6.1/2/3 + R30.1; `#1` 27.30 mm² bbox (107.52,87.28)-(113.00,94.50) holds F2.1. `neck(Q6.S→F2.1)` on F.Cu = **DISCONNECTED**. The only bridge is via (105.840,88.900) → B.Cu → via (108.070,88.200). **Independently confirmed with KiCad's own connectivity engine**: deleting *either* via and re-filling gives unconnected 0 → 1. Cause is visible in the F.Cu plot: the 0.200 mm QG track (Q6.4 → (107.4,88.7) → (109.3,90.6) → (109.3,94.0) → R30.2) slices the pour top-to-bottom. Measured PMID hop resistance **4.914 mΩ** (2.74 mΩ of it the two barrels, analytic). | Reroute QG out of the PMID pour (e.g. drop it to B.Cu for the 6 mm crossing) so PMID is one F.Cu island; failing that, add a 4–6 via array at the crossing. Source fix in `03_src/route.yaml`, not a hand edit. |
| **RL-2** | **P1** | **The 5 A path's board copper is 3–4× the documented allowance**, cutting the E-MARGIN slack the project already calls "thin" by roughly two-thirds. | Numerical mesh solve (SOR, 0.3 mm cells, F.Cu+B.Cu+vias, solver validated against analytic bars — see §4): 5VC L2.2→Q6 tab **2.198 mΩ**, PMID Q6.S→F2.1 **4.914 mΩ**, VBUSC F2.2→J5 **2.209 mΩ** → **total ≥ 9.32 mΩ**. `DETAIL_DESIGN.md:380` budgets `board pours ~3 mOhm`. Solver bias is −10 %…−20 % (low) on known geometry, so the true figure is ≈ **10.4–11.6 mΩ**. Re-running the project's own arithmetic: total 88 → 95.4–96.7 mΩ; required (×1.20) 528 → **572–580 mV**; against the documented 597 mV headroom the slack falls from **69 mV to 17–25 mV**. Gate still PASSES. | Land the corrected IR budget in `DETAIL_DESIGN.md` §4 and make ORDER_README gate **Q3/Q4** (cable-end voltage at 5 A) a *blocking* bench measurement, not advisory. Fixing RL-1 recovers ≈2.7 mΩ of it. |
| **RL-3** | **P1** | **H3 mounting hole straddles the 5VA/GND pour boundary.** An M3 screw head or washer bridges the 6 A USB-A rail to GND through solder mask only, on **both** outer layers. | H3 is a 3.20 mm NPTH at (106.0,24.0); hole edge r = 1.60 mm. Radial scan: **5VA copper starts at r = 1.80 mm and GND copper starts at r = 1.80 mm, on F.Cu *and* B.Cu**. Within a 3.0 mm-radius screw-head footprint: 5VA occupies 7.04 mm² F.Cu + 7.04 mm² B.Cu of an 18.1 mm² annulus (39 %), GND the rest. Within a 3.5 mm washer: 11.33 mm² each. Cause: the 5VA zone's top edge is y = 24.80, only 0.80 mm below the hole centre. Confirmed visually in the F.Cu plot — the hole punches straight through the net boundary. H1/H2/H4 are GND-only inside r = 3.0 mm (H4's VBUSA3 starts at r = 4.19 mm). | **Order paperwork + assembly instructions: nylon/shoulder washer at H3, or leave H3 unfitted.** Next spin: pull the 5VA zone edge back and add a ≥3.5 mm keepout at all four holes. |
| **RL-4** | **P1** | **J5's four VBUS contacts are unequally fed**: the right-hand pair reaches the board through a single via, so the left pair carries 60 % of the current. | Island map: J5.A4/B9 (x=117.550) sit on VBUSC F.Cu `#0` (direct pour from F2.2); J5.A9/B4 (x=122.450) sit on F.Cu `#1` (15.66 mm²) whose **only** link is via (122.970,103.000) — sole path confirmed by connectivity-engine removal (0 → 1 unconnected). Mesh solve at 5.00 A total: **left pair 2.91 A (60.5 %), right pair 1.90 A (39.5 %)** → **1.46 A per contact** on the left vs the **1.25 A/contact** implied by `part.yaml`'s `current_vbus: "5A across 4 VBUS pins"`. Worst contact runs **117 %** of its share; the single via carries 1.90 A. | Add 2–3 vias under the right-hand VBUS island (or extend F.Cu `#0` to reach A9/B4) so the four contacts share evenly. Until then, treat the connector as a 4 A-class part, or verify contact temperature at the Q4 thermal soak. |
| **RL-5** | **P1** | **Twelve sole-path power/sense vias** with no redundancy. One of them (5VA) is *fail-high*: its loss takes buck-A's feedback with it. | Connectivity-engine removal test, 16 vias tried, **12 break their net**: PMID (105.840,88.900) & (108.070,88.200); VBUSC (122.970,103.000); VBUSA1 (109.450,34.325); VBUSA2 (109.450,56.325); VBUSA3 (109.450,78.325); 5VA (97.925,46.000) & (52.070,44.850); 5VC (95.920,86.000), (86.520,62.270) & (57.940,78.925); SW_A (62.862,35.075). Redundant: VBUSC ×3, VIN ×1. **5VA (97.925,46.000) is the *only* connection between the buck-A output pour (F.Cu island `#0`, 1179 mm², holding L1.2 and all three TPS2557 IN pins) and B.Cu island `#0`, which carries U2.10 (VOUT) *and* the R3/R4 FB divider.** If it opens, FB is pulled to GND by R4 → LM5116 drives maximum duty → 5VA runs toward V_IN into three USB-A ports. VBUSA1/2/3 each pass their TPS2557's full output (nominal 2 A; current limit 2.72–3.29 A) through one 0.30 mm barrel. | Duplicate every sole-path power via (a 2-via minimum on any net carrying >1 A is the cheap rule). Prioritise 5VA (97.925,46.000) — that one is a fail-dangerous single point, not merely a reliability one. |
| **RL-6** | P2 | **F2 (0.775 W — the hottest element on the C path) has zero thermal vias on either pad**, and its two pads see an 8:1 copper asymmetry. | F2 pads measured 10.43 mm² each, F.Cu-only, **0 vias in either pad** (exact polygon containment). Input side = PMID F.Cu island `#1`, **27.30 mm²**; output side = VBUSC F.Cu `#0`, **218.45 mm²**. Same scan: **L1.1/L1.2/L2.1/L2.2 (17.82 mm² each) — 0 vias; Q3.5 (SW_A) — 0; Q6.5 (5VC) — 0; D5.1 — 0; Q5.5 (SW_C) — 1**. Estimated F2 rise 0.775 W × 40–50 °C/W ≈ **31–39 °C** above local board temperature (2920 on ~250 mm² of 1 oz with the In1 plane 0.2 mm below as spreader). No `Pd` or surface temperature for the *tripped* state exists anywhere in the tree, and no keep-away is defined around it. | Add a 4-via array under each F2 pad next spin. Record F2's tripped-state dissipation and surface temperature in `02_parts/SMD2920-700/part.yaml`, and put a keep-away note on it. Measure F2 body temperature at the Q4 soak. |
| **RL-7** | P2 | **VBUSA1/2/3 run 8.5 mm of bare 0.500 mm B.Cu track** between each TPS2557 output and its pour — at the class floor, and hot in the current-limit case. | `VBUSA*` routing is 1 × 0.500 mm F.Cu stub (0.7 mm) + 1 × 0.500 mm B.Cu track (13.6 mm), of which x = 109.45→118 (**8.5 mm**) is outside the B.Cu pour. Cross-section 0.500 × 0.035 = 0.0175 mm². IPC-2221 external: ΔT ≈ **21 °C at 2 A**, **35 °C at the 2.5 A class current**, **65 °C at the TPS2557 limit (3.29 A)** — bounded by OTSD at 135 °C. `nets.yaml` declares `VBUS current: "2.5 A"` against `min_width: 0.5mm`, so the copper is rule-consistent; the rule is the aggressive part. | Widen to ≥1.0 mm or pour VBUSA over the gap. Re-derive the `VBUS` netclass floor from IPC-2152 at the *fault* current, not the nominal. |
| **RL-8** | P2 | **The CS/CSG pairs are not true Kelvin**: CSG taps the shared GND return pour, not the shunt pad, and the two halves of each pair differ 2.3× in length. | R10.1 (buck-A CSG tap) sits at (75.17,47.00) — **3.93 mm** from RS1.2 (72.00,48.96), in the pour that carries the full LS return. R9.1 (CS tap) sits at (67.28,43.70) — **4.72 mm** from RS1.1, but in a quiet side-lobe of the CS_A pour, which is correct practice. Routed lengths **CSF_A 7.4 mm vs CSGF_A 17.4 mm**; CSGF runs **7.1 mm unpaired** from (69.7,43.8) to (76.8,47.0). Identical geometry on buck-C. DC error from the tap offset ≈ 0.19 mΩ spreading × 6 A ≈ **1.1 mV on a 60 mV shunt signal (~2 %, trips early)**. AC pickup is bounded because both traces run on F.Cu 0.2 mm above the solid In1 GND plane (differential loop to reference ≈ 1.4 mm²). | Not worth a re-spin — the 2 % error is inside the LM5116's own threshold tolerance. Next spin: move R10/R19 adjacent to the shunt and tap RS*.2's pad corner, and route CSF/CSG as a tight pair the whole way. |
| **RL-9** | P2 | **Both buck feedback/VOUT sense paths are long B.Cu runs referenced to the VIN plane**, crossing under their own power stage. | 5VA: **174 collinear 0.400 mm B.Cu segments forming one run at y = 46.000 from x = 54.425 to x = 97.925 — a 43.50 mm span** — passing directly under RS1 (72,46) and the CS_A pour. 5VC: the same at y = 86.000, x = 58.425→95.925, **37.50 mm**. B.Cu's nearest plane is **In2 = VIN**, not GND, so these carry no GND reference. Ampacity is a non-issue (LM5116 VOUT/FB draw is µA), noise is not. | Route the VOUT/FB sense on F.Cu (over the GND plane) or add a GND guard/stitch alongside. Recorded — this is the same class as the v1.0 review's L-5. |
| **RL-10** | P2 | **~211 mm² of switch-node copper on B.Cu per buck, directly over the VIN plane** — an unnecessary dV/dt injector into VIN. | SW_A: F.Cu 122.10 mm² + **B.Cu 211.41 mm²**; SW_C: F.Cu 199.42 + **B.Cu 211.78**. B.Cu↔In2 spacing 0.2 mm → **40.2 pF (SW_A) and 40.3 pF (SW_C) of switching capacitance onto the VIN plane**; totals 63.5 pF and 78.3 pF per node. The SW trunk already rides F.Cu between Q2/Q3 and L1, so the B.Cu pour adds no needed ampacity. Loss is negligible (C·V²·f ≈ 3 mW); the concern is conducted noise and radiated EMI. | Delete or shrink the B.Cu SW pours in the floorplan. Cheap, zero risk, meaningful EMI win. |
| **RL-11** | P2 | **The R-THERM waiver's prose is stale and over-reaches onto parts it never measured.** | The waiver says *"U11.21 … with 1 direct via (vs 3 on the sister EP U2.21)"* and carries a *"Next-rev work order: add a >=4x 0.3mm via array under BOTH LM5116 EPs."* **Measured on the shipped copper: U2.21 and U11.21 each have 7 GND vias inside the exposed pad** (regular 3×2+centre array at ±0.85 mm / ±2.1 mm). The work order is **already done**; the waiver text describes copper that no longer exists. Separately, the waiver extends the v1.0 adjudication onto **Q6.5/5VC and Q6.1-3/PMID** — but the cited review measured neither (Q6 did not exist on v1.0), and its quoted "170-390 mm² pours" are the v1.0 VBAT_F/SW_A/SW_C numbers. Q6's actual numbers, measured here: tab 17.39 mm², **0 vias**, on a 237.90 mm² 5VC F.Cu island → 0.107 W × ~55-70 °C/W ≈ **6-8 °C ΔTj**. The waiver's *conclusion* holds; its *evidence* does not. | Rewrite R-THERM against measured v1.3+ copper: drop the stale U11.21 sentence and the completed work order, and cite the Q6/PMID numbers above rather than inheriting v1.0's. This is exactly the "inherited defect" failure mode in CLAUDE.md. |
| **RL-12** | P2 | **LM5116 timing/compensation parts are 5–6 mm from their pins**, against a datasheet that asks for "as close as possible". | Centre-to-centre pad spans: **RT 5.50 mm** (R2.1↔U2.3), **RAMP 5.82 mm** (C3.1↔U2.5), **SS 5.11 mm**, **COMP 6.45 mm** (routed 10.8 / 13.4 mm), **UVLO 5.46 mm**, **FB span 9.37 mm (routed 20.8 mm)**. All on F.Cu over the solid In1 GND plane, and all AGND-side parts return to U2.6/U11.6 as the datasheet asks. | Recorded. Tighten on the next placement pass — the GND plane underneath is what makes this survivable, so do not remove it. |

**Counts: P0 = 0, P1 = 5, P2 = 7.**

---

## 2. What I checked and found CLEAN (numbers that make it fine)

These are the things a layout reviewer is obliged to check. They passed; the
measurements are here so the next reviewer does not have to redo them.

**Reference planes — both solid, no splits.**
`GND` on In1: **1 outline, 11 521.5 mm² = 96.2 % of the 11 982 mm² board bbox**,
measured neck across the board (fuse area → J5) **3.287 mm**, U2 EP → U11 EP
**5.531 mm**. `VIN` on In2: **1 outline, 11 310.6 mm² = 94.4 %**, span neck
**2.971 mm**. There is no split under anything.

**No high-speed data exists on this board — so impedance, skew and the DMC
layer change are electrically irrelevant.** I traced every D+/D- net: they
terminate only at connectors, USBLC6 ESD arrays, TPS2513 DCP controllers, and —
for the C port — **R27, a 0 Ω link shorting DPC to DMC** (BC1.2 DCP
advertisement). **There is no host controller, hub IC or USB PHY anywhere in the
netlist.** So although the pairs are badly matched by HS standards (DP_A2 48.26 mm
vs DM_A2 41.66 mm = 6.60 mm skew; DPC 24.86 mm vs DMC 31.84 mm = 6.98 mm; and DMC
alone takes 2 vias and 5.73 mm on B.Cu where it references VIN instead of GND),
**none of it matters** — these are DC advertisement lines. Not a finding. I am
recording it explicitly so a future reviewer does not raise it as one.

**Mechanical / connector overhang — intentional and clean.** Edge.Cuts is a plain
20,20–150,112 rectangle with no notches. J1, J2-J4 and J5 courtyards overhang by
6.84 / 2.48 / 1.14 mm respectively — that is the `_EdgeTrim` / horizontal
through-hole footprint style working as designed. **Every pad is inside the
outline**; the tightest is J5's shell at **+1.200 mm**, then C12 at **+1.700 mm**.
No component body lands where a connector shell sits. H1/H2/H4 keepout is clean
(nearest non-GND copper: H4 → VBUSA3 at r = 4.19 mm; H1/H2 → GND only). H3 is
RL-3.

**Thermal — measured dissipation vs measured copper.** Every large pad was scanned
for in-pad vias by exact polygon containment.

| part | P (project's own R) | pad / copper measured | vias in pad | estimated ΔT |
|---|---|---|---|---|
| F2 PPTC | 0.775 W (5²×31 mΩ hot) | 10.43 mm² ×2; PMID side 27.3 mm², VBUSC side 218.5 mm² | **0 / 0** | 31–39 °C — RL-6 |
| L1 | 0.486 W (6²×13.5 mΩ) | 17.82 mm² ×2 on 122 mm² SW_A / 1179 mm² 5VA | **0 / 0** | ~12–17 °C |
| L2 | 0.338 W | 17.82 mm² ×2 on 199 mm² SW_C / 238 mm² 5VC | **0 / 0** | ~8–12 °C |
| RS1 (2512, 1 W) | 0.36 W | 4.05 mm² on 127 mm² CS_A pour / GND | 1 (GND side) | ~13–18 °C, well inside 1 W |
| RS2 | 0.25 W | as RS1 | 1 | ~9–13 °C |
| Q1 AON6403 | 0.218 W @ 7.12 A | tab 17.39 mm²; VBAT_F F.Cu 169.7 + **B.Cu 195.6 mm², 7 vias** | **2** | ~11 °C |
| Q2 / Q4 (HS) | switching + cond. | tab 17.39 mm² onto the In2 VIN plane | **4 / 5** | best-served pads on the board |
| Q3 / Q5 (LS) | 0.11 / 0.08 W | tab 17.39 mm² on 122+211 / 199+212 mm² SW pours | **0 / 1** | ~6 °C |
| Q6 AON6403 | 0.107 W | tab 17.39 mm² on 237.9 mm² 5VC island | **0** | ~6–8 °C |
| U2 / U11 EP | ~0.15–0.20 W | 22.10 mm², RθJC(bot) 1.7 °C/W | **7 / 7** | negligible |
| U3 / U4 / U5 EP | ~0.10–0.14 W @ 2 A | 3.96 mm², RθJA 41.5 °C/W | **1 each** | ~4–6 °C |

Nothing here is thermally marginal at nameplate load. **Notably, two v1.0 work
orders have already been implemented in the shipped copper and nobody recorded
it**: L-2 (≥4 × 0.3 mm EP via array under both LM5116s) is done — 7 vias each;
L-3 (B.Cu pour + stitch vias on VBAT_F) is done — B.Cu 195.6 mm² and 7 vias
where v1.0 measured 0.

**The two PMID/VBUSC vias are *not* a thermal problem** — I want to be explicit
because it would be easy to overclaim. Barrel model: 0.30 mm finished hole,
20 µm plating → A = 0.02011 mm², R = 1.369 mΩ, and at 5 A the current density is
**249 A/mm²**, which sounds alarming. But the barrel is 1.6 mm long and bonded to
copper at both ends: P = 34.3 mW, and ΔT_max = PL/(8kA) ≈ **0.85 K** above its
own pads. RL-1/RL-5 are reliability and IR findings, not thermal ones.

**Ampacity — trunk necks are adequate.** Widest-bottleneck erosion measurements
between pour-interior points: 5VA L1.2→U3/U4/U5 IN **2.713 mm** (6 A → ~16 °C by
IPC-2221, and it is a pour so the real rise is lower); 5VC C30→Q6 tab **2.291 mm**
(5 A → ~14 °C); VBAT J1→F1 **3.398 mm**; VBAT_F F1→Q1 **3.035 mm** (v1.0 measured
3.6 mm and graded it PASS at 13–15 °C — unchanged in class); PMID B.Cu interior
**0.996 mm**; VBUSC F2.2→J5 **1.295 mm**.

**`pad_rescue_stubs` — genuinely short pad stubs, not thinned trunks.** The rule
permits 0.300 mm on GND/VIN inside named rule areas. There are **7 such rule
areas, each 1.0–1.7 mm across**, and exactly **8 tracks** use the allowance:
3 VIN (1.265, 1.265, 1.560 mm — all at Q2/Q4 drain pads, where the stub lands
inside the FET's own 3.81 × 3.91 mm tab, which itself carries 4–5 vias into the
In2 plane) and 5 GND (1.201–1.221 mm, at C41/C42/C43, D3 and C5). **Every one is
a real pad stub. No trunk got thin through this rule.** This is disciplined and I
could not fault it.

---

## 3. What I measured, and how

- **Geometry.** `pcbnew` 10.0.4 Python. For each net and layer I built the exact
  union of zone fill polygons + track shapes + pad shapes via
  `SHAPE_POLY_SET.BooleanAdd`, then used `OutlineCount()` and
  `Contains(point, outline)` to determine which physical island each pad, via and
  probe point lands on. This is exact geometry, not rasterisation.
- **Neck widths.** Binary search on `SHAPE_POLY_SET.Inflate(-d)` until the two
  probe points fall in different outlines; the reported neck is `2d`. Because
  erosion removes *all* channels narrower than `2d`, this returns the **widest
  available** bottleneck across every parallel path — the correct quantity. I
  discarded four early measurements where the probe point was a component pad
  rather than pour interior (the pad's own width, not a pour neck) and re-ran
  them against interior points; only the interior numbers are quoted above.
- **Resistance.** Finite-difference resistor mesh over F.Cu and B.Cu (0.25–0.3 mm
  cells), ρ = 1.72 × 10⁻⁵ Ω·mm, t = 0.035 mm outer, vias as explicit inter-layer
  conductances at R = 1.369 mΩ, solved by SOR (ω = 1.9, 4000 sweeps). **I
  validated the solver against three uniform bars with analytically known
  resistance: it reads −11.1 %, −10.0 % and −20.0 % low.** Every resistance in
  this review is therefore a **lower bound**; I have stated the bias-corrected
  range wherever the number carries a conclusion (RL-2).
- **Connectivity — independent method (canon M1).** The sole-path claims are not
  from my polygon code. I loaded the board fresh in a separate process, removed
  one via, re-filled all zones with `ZONE_FILLER`, and asked **KiCad's own
  `CONNECTIVITY_DATA.GetUnconnectedCount()`** whether the net broke. 16 vias
  tested, 12 broke. All in memory; **nothing was written to the board.**
- **Visual corroboration — independent renderer.** `kicad-cli pcb export svg` for
  F.Cu and B.Cu, rasterised with `rsvg-convert`. The QG track bisecting the PMID
  pour (RL-1) and the H3 hole straddling the 5VA/GND boundary (RL-3) are both
  directly visible in that plot, produced by KiCad's plotter rather than my code.
- **Thermal.** P = I²R using the project's own resistance values
  (`DETAIL_DESIGN.md` §1/§4, `power_tree.yaml`); ΔT from package θ values quoted
  in `02_parts/*/part.yaml` and the datasheets (LM5116 RθJC(bot) 1.7 °C/W,
  RθJA 40.6; TPS2557 RθJA 41.5, RθJC(bot) 3.6; AON6403 RθJA 40 typ / 55 max);
  trace rises from IPC-2221 (`I = k·ΔT^0.44·A^0.725`, k = 0.048 external).
- **Coupling.** Parallel-plate, ε_r = 4.3, F.Cu↔In1 and B.Cu↔In2 = 0.2 mm prepreg.
- DRC was **not** re-run, per the commission.

## 4. What I could NOT measure, and why it matters

- **The stackup is not in the board file.** `GetStackupDescriptor()` returns no
  layer list and there is no `(stackup ...)` block in the `.kicad_pcb`. I assumed
  the JLC 4-layer 1.6 mm standard (1 oz outer / 0.5 oz inner, 0.2 mm prepreg
  F↔In1 and In2↔B, ~1.065 mm core In1↔In2) — the same assumption the v1.0 review
  made. **Every resistance, ΔT and capacitance above scales with that
  assumption.** If the fab ships a different stackup the numbers move.
- **Via barrel plating.** I used 20 µm (JLC specifies ≥18 µm). At the 18 µm floor
  the two PMID barrels are 1.52 mΩ each instead of 1.37, and RL-2 gets worse.
- **Ambient / enclosure temperature is undefined anywhere in the project.**
  `ARCHITECTURE.md` has zero thermal content; `DETAIL_DESIGN.md` says only "the
  hottest expected ambient" and defers to bench gate Q4. Total board loss is
  `64.08 − 57.67 = 6.41 W`. **Without an ambient I can report ΔT above local board
  temperature but not absolute junction or body temperatures.** This is the single
  biggest gap for a thermal review and it is a *documentation* gap, not a copper
  one.
- **F2's tripped-state dissipation and surface temperature are recorded nowhere**
  — not in `part.yaml` (which has no datasheet PDF at all for this part), not in
  the docs. A tripped 2920 PPTC typically holds ~0.9–1.4 W at 100–125 °C surface.
  Nothing in the project bounds it or keeps anything away from it. I could not
  verify what sits next to a tripped F2 because the number does not exist.
- **J5 has no per-contact current rating.** `part.yaml` records only
  `"5A across 4 VBUS pins (HRO rating, ledger)"`, and the datasheet PDF is a pure
  drawing (57 bytes of extractable text). RL-4's "1.25 A/contact" is that total
  divided by four, not a vendor number. The imbalance I measured is real; the
  threshold it is compared against is inferred.
- **Solder-mask integrity under fastener torque (RL-3)** cannot be measured from
  the board. Whether the H3 short actually occurs depends on mask thickness,
  washer type and torque. That is precisely why it needs a build instruction
  rather than an argument.
- **Absolute EMI.** RL-10 gives coupling capacitance, not emissions. Only a
  chamber or a near-field probe settles that.

---

## 5. Gate note

Per `08_reviews/contracts.md`, this file is the layout/thermal/power-integrity
red-team lens for v1.5 and carries `verdict: ORDER`. Every row above needs a
`DISPOSITIONS.md` entry; the five P1s need dispositions before seal, and RL-3
specifically must reach ORDER_README and the assembly instructions, not just the
ledger. RL-11 is a *process* finding — the R-THERM waiver currently states
copper conditions that measurement contradicts in both directions (one claim
stale-pessimistic, one inherited without evidence), which is the "waiver copied
from another board is an inherited defect" pattern CLAUDE.md warns about.
