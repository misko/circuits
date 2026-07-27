# redteam_layout (layout / thermal / power-integrity axis) — contract-named copy

> **PROVENANCE.** `07_releases/contracts.md` requires TWO red-team files —
`redteam_topology.md` (topology / protection / ratings) and `redteam_layout.md`
(layout / thermal / power-integrity). **v1.9's red-team was run as ONE INTEGRATED
LENS covering both axes plus fix confirmation**, so both contract names carry the
same VERBATIM COPY of `08_reviews/2026-07-27_v1.9_redteam_fix-lens.md`. Stated
here rather than left for a reader to discover two identical files: it is one
review, deliberately, because the fix under review (the copper pour) is a
layout fact whose consequences are topology facts, and splitting it would have
given two lenses each missing half the evidence.
>
> **VERDICT: ORDER. 0 P0**, 1 P1, 8 P2.
>
> The prior per-axis lenses are NOT deleted and remain in this directory as dated
evidence: `2026-07-25_v1.5_redteam_layout.md` (the first layout/thermal lens ever
run against this copper) and `2026-07-23_v1.3_redteam_fresh-lens.md` +
`2026-07-22_v1.0_redteam_topology_rereview.md` (topology). The copper they
reviewed is unchanged apart from the pour restoration this release exists for.
>
> **P1-1** (the E-OFF quiescent budget omitting 443 uA of always-on UVLO divider,
which would have made bench gate Q6 **condemn a good board**) and the four P2s
that were FALSE STATEMENTS in shipped documents (P2-1 the Kelvin claim, P2-4 the
stale R-THERM waiver, P2-5 the missing 2.72 A hardware ceiling, P2-8 the 5VA
corner vs the ceiling cited against it) were **all FIXED before this seal**, at
SOURCE, because `07_releases/` becomes immutable at the seal commit. P2-2 and
P2-3 are COPPER findings and are RECORDED with their measurements and deferred —
re-routing would void every verdict this release collected. Per-finding
disposition: `08_reviews/DISPOSITIONS.md`.

---

# v1.9 zero-context adversarial red-team — integrated fix lens

| | |
|---|---|
| **Date** | 2026-07-27 |
| **Lens** | zero-context adversarial red-team, integrated (fix confirmation + layout/thermal/PI + topology/protection/ratings) |
| **Release under review** | `07_releases/v1.9-2026-07-27/` (board `usb_hub_3s_v2`, 4-layer, 130.1 × 92.1 mm) |
| **Reviewer inputs** | the staged release directory (read-only), `01_docs/{BRIEF,ARCHITECTURE,DETAIL_DESIGN,CHANGELOG}.md`, `01_docs/decisions/`, `02_parts/*/part.yaml` + datasheet PDFs, `03_src/` (`floorplan.yaml`, `route.yaml`, `rules/*.yaml`) |
| **Deliberately NOT read** | `01_docs/journal/`, `01_docs/learnings/`, `01_docs/STATUS.md`, every prior `08_reviews/*` file (independence) |
| **Board identity** | `04_kicad/usb_hub_3s_v2.kicad_pcb` and `<release>/source/usb_hub_3s_v2.kicad_pcb` are md5-identical (`83af8e5a5596a51cf139dd06e8903d47`). All pcbnew work was done on the `04_kicad/` copy **in place** so the sibling `.kicad_pro` supplies the real netclasses. Nothing was written into `04_kicad/` or `07_releases/`. |

### Method (four independent instruments, each stated so it can be disagreed with)

1. **Stranded-island graph** (`island_check.py`). A geometric connectivity graph over
   *every* copper item of each net — zone islands (one node per filled outline), tracks,
   vias, pads — with an edge wherever two items share a copper layer and their filled
   geometry intersects by more than 1e-4 mm². An island is BONDED iff its connected
   component contains at least one PAD of its own net. Copper layer membership comes
   from `LSET.CuStack()`, never an id range: on this board **F.Cu = 0, B.Cu = 2,
   In1.Cu = 4, In2.Cu = 6**, so any `TopLayer() <= L <= BottomLayer()` test spans only
   [0,2] and would falsely report both inner planes stranded.
2. **Gerber-payload parse** (`gerb_area.py`). Independent text parse of the *shipped*
   `usb_hub_3s_v2_gerbers.zip`: count `G36…G37` regions per copper layer and shoelace
   their polygon areas. Does not use pcbnew at all.
3. **DC sheet-resistance SOR solve** (`rsolve.py` / `probe.py`). Rasterise a net's filled
   copper per layer, couple layers where a via of that net exists (0.5 mΩ per barrel),
   Dirichlet BCs on the source/sink pads, SOR to residual ≤1e-11. This is deliberately
   **not** `nets.yaml`'s perpendicular cross-section sweep (canon M1). Sheet resistance
   ρ = 1.724e-8 Ω·m, **1 oz (34.8 µm) outer / 0.5 oz (17.4 µm) inner** — the JLC 4-layer
   STANDARD default, because **the board declares no stackup** (see P2-7).
   **Solver validated against analytic bars** (`R = Rsq·L/W`) before use:

   | bar | cell | solved | analytic | error |
   |---|---|---|---|---|
   | 10.000 × 1.000 mm | 0.250 | 4.8302 mΩ | 4.9540 mΩ | −2.50 % |
   | 10.000 × 1.000 mm | 0.125 | 4.8921 mΩ | 4.9540 mΩ | −1.25 % |
   | 13.554 × 0.800 mm | 0.200 | 8.2980 mΩ | 8.3934 mΩ | −1.14 % |
   | 13.554 × 0.800 mm | 0.100 | 8.3599 mΩ | 8.3934 mΩ | −0.40 % |
   | 20.000 × 4.000 mm | 0.250 | 2.4460 mΩ | 2.4770 mΩ | −1.25 % |

   **Every resistance below is therefore a LOWER bound, biased low by roughly
   (cell/length) — 0.4 % to 5 %.** The bias is a half-cell end effect at each Dirichlet
   boundary and it is stated rather than corrected.
4. **Bottleneck (widest-path) width** (`neck.py`). 0.05 mm raster + distance transform +
   max-heap Dijkstra maximising the minimum edge distance. Used only to *localise* necks;
   it is per-layer and cannot follow a via, so it is not used for ampacity verdicts.

---

## 1. FIX CONFIRMATION — is the pour back, and is any of it stranded?

**Result: the pour is back, no island is stranded, and the copper in the fab payload is
the copper in the board.**

### 1.1 Island census (pcbnew, in place)

**106 filled islands, 44 282.1 mm² total.**

| net | layer | islands | mm² |
|---|---|---|---|
| GND | In1.Cu | 1 | 11 406.266 |
| VIN | In2.Cu | 1 | 11 276.876 |
| GND | B.Cu | 4 | 7 875.720 |
| GND | F.Cu | 54 | 6 225.577 |
| 5VA | F.Cu / B.Cu | 3 / 1 | 1 130.904 / 1 111.670 |
| VIN | F.Cu | 7 | 634.370 |
| VBAT | F.Cu | 1 | 352.620 |
| VBUSA1/2/3 | B.Cu | 1 each | 344.701 / 344.701 / 334.816 |
| SW_A / SW_C | B.Cu | 1 each | 195.985 / 195.985 |
| SW_C / SW_A | F.Cu | 1 each | 194.811 / 85.741 |
| CS_A / CS_C | F.Cu | 1 each | 127.640 / 127.598 |
| (remainder: 5VC, VBUSC, VBAT_F, PMID, VBUSA F.Cu) | | | |

**STRANDED ISLANDS: NONE.** Every filled island's connected component contains at least
one pad of its own net.

### 1.2 Proving the check can FAIL (negative controls)

A clean result from a check that cannot fail is worthless. Three controls, all run on the
same board in memory:

| control | result |
|---|---|
| strip the **34 VIN vias**, leave everything else | **STRANDED: VIN In2.Cu, 11 276.8758 mm², component size 1** ✅ the check fails when it should |
| strip the **178 GND vias**, leave THT pads | clean — correctly, because **15 GND THT pads** (J1.1, J2/J3/J4 GND+SH, J5 GND, SW1.1, H1/H3) span all four copper layers and still bond In1.Cu |
| strip the 178 GND vias **and** restrict every pad to F.Cu/B.Cu | **STRANDED: GND In1.Cu, 11 406.2661 mm²** ✅ |
| restrict every pad to F.Cu/B.Cu, **vias intact** | clean ✅ — the check is discriminating, not vacuous |

The two controls that fire are exactly the false-P0 shape the brief warned about (the
inner planes), and they fire only when the bond is genuinely removed.

**Honest qualifier:** all 36 non-rule-area zones carry `island_removal_mode = ALWAYS`
(`GetIslandRemovalMode() == 0`), so KiCad itself removes unbonded islands at fill time
with a similar criterion. My check therefore *confirms KiCad honoured that in the SAVED
fill* — which is precisely what v1.6/v1.7/v1.8 failed at — rather than discovering
something KiCad could not have known.

### 1.3 Gerber-payload cross-check (does not use pcbnew)

| gerber | `%TF.FileFunction%` | G36 regions | Σ region area |
|---|---|---|---|
| `usb_hub_3s_v2-F_Cu.gtl` | Copper,L1,Top | **87** | 10 402.7 mm² |
| `usb_hub_3s_v2-B_Cu.gbl` | Copper,L4,Bot | **17** | 11 196.2 mm² |
| `usb_hub_3s_v2-In1_Cu.g1` | Copper,L2,Inr | **1** | 11 406.3 mm² |
| `usb_hub_3s_v2-In2_Cu.g2` | Copper,L3,Inr | **1** | 11 276.9 mm² |

The region **counts** match the pcbnew island counts island-for-island (F.Cu 87, B.Cu 17,
In1 1, In2 1 — total 106 = 106). The F.Cu **area** matches to 0.001 mm²
(pcbnew Σ = 10 402.721, gerber Σ = 10 402.7); In1 11 406.266 vs 11 406.3; In2 11 276.876
vs 11 276.9; B.Cu's 5VA island 1 111.670 vs 1 111.7; VBAT 352.620 vs 352.6. Zero
clear-polarity (`%LPC%`) regions on any copper layer, so nothing is being subtracted.

The release's own `fab_payload_census.txt` grades v1.8 FAIL / v1.9 OK on this same axis
and shows the gate failing on the sealed defect — a gate that is demonstrated able to
fail. I reproduce its verdict by a different parser.

### 1.4 GND plane integrity / return-path continuity

In1.Cu GND: **one outline, 6 334 points, 11 406.266 mm², zero separate islands.** No
slots. Coverage by 0.25 mm sampling:

| region | In1 GND coverage |
|---|---|
| buck-A hot-loop rectangle (70–82, 22–50) | **97.5 %** (5243/5376) |
| buck-C hot-loop rectangle (70–82, 60–88) | **98.0 %** |
| USB-A port area (100–145, 25–90) | 93.9 % |
| USB-C area (100–145, 85–112) | 94.1 % |

In2.Cu VIN plane coverage under the buck-A loop 97.6 %, under the B.Cu SW_A island 98.9 %.
**No return current is forced to detour** — the only voids are via antipads and the four
`hole_vin_H*` rule areas on In2 around the mounting holes.

---

## 2. FINDINGS

Severity: **P0 blocks the release**, P1 must be corrected before the affected gate is run,
P2 is recorded.

| # | finding | sev | evidence (measured) | suggested disposition |
|---|---|---|---|---|
| **P1-1** | **E-OFF stored quiescent draw is understated 2.6×: the two LM5116 UVLO dividers are permanently across VIN and are not in the budget.** | **P1** | Netlist: `UVLO_A = R6.2 + R7.1 + U2.2`, `R6.1 → VIN`, `R7.2 → GND` ⇒ **56.88 kΩ VIN→GND**, unswitched. Same for `R15/R16` on UVLO_C. At 12.6 V: **2 × 221.5 = 443.0 µA**. `SW1` gates only ENABLE (pads: 1 = T1→GND, 2 = COM→ENKILL, 3 = T2 = `unconnected-(SW1-T2-Pad3)`) — no pole touches VBAT/VBAT_F/VIN, so both dividers conduct in storage. `power_tree.yaml quiescent_ua: 271` enumerates only 252 (R8‖R17 ENKILL pull-ups) + 18 (2 × LM5116 shutdown Iq) + ≤1 (Q8). Corrected typical ≈ **714 µA**; worst ≈ **748 µA** (LM5116 Iq at the 20 µA datasheet max, plus the D2/R1 zener leg at up to (12.6−11.4)/100 k = **12 µA** and D1 SMBJ15A reverse leakage ≤1 µA, both also uncounted; C1/C2 polymer leakage is uncounted **and unbounded in the record** — `KNM2100UF35V/part.yaml limits:` has no leakage entry). Consequence: the declared bench acceptance **"PASS ≤ 300 µA" would FAIL a correctly-built board**; 5000 mAh 3S storage life is ~292 d to flat / ~234 d to the 20 % LiPo floor, not the ~769 d / ~615 d that 271 µA implies. Why nothing caught it: `skills/kicad-pcb/scripts/power_topology.py::grade_off_control()` only checks that `quiescent_ua` is **declared** — it never reconciles the number with the netlist. | Correct `quiescent_ua` to ~714 µA (or a bounded range 700–750 µA + "cap leakage unmeasured"), re-base the ORDER_README bench threshold, and decide explicitly whether 714 µA is acceptable or R6/R15 move behind the switch. **Paperwork + gate defect; no copper change. Does not block the order — but must be fixed before the bench gate is run, or it will condemn a good board.** |
| **P2-1** | **CSG is not a Kelvin connection; `DETAIL_DESIGN` sec.2.5's "no shared trunk copper enters the sense loop" is falsified by measurement.** | P2 | `R10.1` (buck-A CSG 0 Ω link) lands on the **GND net** at (75.175, 47.000) — 3.75 mm from `RS1.2` (72.000, 48.962) — i.e. it taps the *plane*, not the shunt terminal. SOR on GND copper (4 layers, via-coupled), source `RS1.2`, sink the five buck-A input-cap GND pads: **R = 1.002 mΩ**, and **V(R10.1) = 0.6418** ⇒ **35.8 % of the buck's input-return drop = 0.359 mΩ of shared trunk copper is inside the sense loop.** Buck-C identical: R = 1.012 mΩ, V(R19.1) = 0.6239 ⇒ 0.381 mΩ. CS side is far better: V(R9.1) = 0.0188 of the 6.578 mΩ `Q3.S→RS1.1` pour drop = 0.124 mΩ; V(R18.1) = 0.0833 of 2.083 mΩ = 0.174 mΩ. **Net sense error at 6 A = +2.89 mV on a 60 mV full-scale shunt signal = +4.8 %; the 11.0 A valley current limit becomes ≈10.5 A.** The shared path is also inductive and carries the buck's pulsed return, and there is **no differential filter** — R9/R10/R18/R19 are 0 Ω and the netlist contains **no capacitor between CSF_x and CSGF_x**. | Not a blocker at 6 A (4.8 % on a limit that is 1.8× the load). Next revision: run CSG to `RS1.2`/`RS2.2`'s own pad as a dedicated trace and add the CS RC filter the 0 Ω links were provisioned for. **Correct sec.2.5's claim now** — it is stated as fact and it is not one. |
| **P2-2** | **Buck-A's pour copper is 2.7–3.2× more resistive than the nominally identical buck-C cell, and the declared switch-node margin is method-dependent.** | P2 | SOR: `SW_A Q2.S→L1.1` = **0.774 mΩ** vs `SW_C Q4.S→L2.1` = **0.287 mΩ**; `CS_A Q3.S→RS1.1` = **6.578 mΩ** vs `CS_C Q5.S→RS2.1` = **2.083 mΩ**. Resistance-equivalent 1 oz outer widths over the straight-line span: SW_A **4.241 mm**, SW_C **11.429 mm**. IPC-2221 needs **4.399 mm** for 7 A at ΔT 10 °C external ⇒ by *resistance* buck-A's switch node is **0.96×**, not the **1.38×** `nets.yaml` reports from a summed perpendicular cross-section. Localised cause (0.05 mm raster): both CS pours neck to **0.300 mm over ≈0.8 mm** at x ≈ 74.3–74.6 where the CSGF/COMP escapes cross; buck-A has more foreign copper crossing there and no equally wide bypass. Thermally irrelevant either way: SW_A dissipates **37.9 mW** at 7 A, CS_A **143 mW** at the 4.66 A LS-FET RMS (6 A × √0.603). | Keep the copper. **State the method with the number** — 1.38× is a cross-section ratio, not a resistance ratio, and the two disagree by 44 % on this board. Next revision: widen the CS neck and find out why two mirrored cells differ 3×. |
| **P2-3** | **High-side gate loops are not tight, against the AON6354 part.yaml layout note ("gate trace short + direct to the LM5116 HO/LO driver pin").** | P2 | Routed: `HO_A` **20.253 mm** (18.813 F.Cu + 1.440 B.Cu, 2 vias — the gate changes layer mid-run); `HO_C` **24.151 mm** F.Cu; `BOOT_A` 14.533, `BOOT_C` 12.118; `LO_A`/`LO_C` 11.255 each. Measured **mean same-layer gap to the nearest SW copper (pour + track + pads)**, sampled every 0.25 mm with a bisected clearance query: HO_A **1.966 mm** (max 4.133), HO_C **2.510 mm** (max 5.406), BOOT_A 2.405, BOOT_C 2.475. Enclosed loop ≈ **40 mm² (A) / 61 mm² (C)** ⇒ two-conductor estimate **25–34 nH**. With Ciss ≈ 4 nF and the LM5116's ~2–3 Ω driver: Z₀ ≈ 2.5–2.9 Ω, **Q ≈ 0.8–1.0** (near-critically damped), ring ≈ 14–16 MHz. LO loops are fine — LO_A/LO_C run coplanar inside the CS pour at a **0.787 / 0.788 mm** mean gap. | Reads as switching-loss / EMI, **not** shoot-through (Q ≈ 1). Add Vgs at Q2/Q4 to the ORDER_README scope gate (Q3 already scopes the SW nodes). Next revision: route HO/SW as a pair. |
| **P2-4** | **The R-THERM waiver's evidence describes a board that no longer exists.** | P2 | `03_src/rules/policy_waivers.yaml` states *"U11.21 … with 1 direct via (vs 3 on the sister EP U2.21)"* and carries *"Next-rev work order: add a ≥4× 0.3 mm via array under BOTH LM5116 EPs."* **MEASURED on v1.9 (vias whose centre lies inside the pad polygon): U2.21 = 7 GND vias, U11.21 = 7 GND vias.** The work order is done; the waiver's numbers are stale. The same waiver's dissipation figures still cite the superseded 15.5 A Q1 / 5 A Q6 envelope. Also **unmentioned by any waiver**: `U3.9 / U4.9 / U5.9` (TPS2557 EPs) have **exactly 1 via each**, against `TPS2557DRBR/part.yaml`'s own gotcha *"EP needs thermal vias (R-THERM; TPS2557-class EPs shipped with zero once)"*. Thermally acceptable — at 2 A, P = 2²×35 mΩ(max over −40…125 °C) = **140 mW**; at the guaranteed-non-trip 2.72 A, **259 mW**; VSON-8 DRB ≈ 48.7 °C/W ⇒ 7–13 °C — but far below TI's layout example. | Re-measure and rewrite the waiver body. Canon says a waiver needs evidence; **stale evidence is the same failure mode as no evidence**. Add the TPS2557 EPs to the waiver text (they are currently silently covered by a waiver that never names them). |
| **P2-5** | **"2 A continuous per port" is a load budget; the hardware ceiling is 2.72 A, and that changes the VBUS ampacity answer.** | P2 | `R20/R21/R22 = 36.5 kΩ` ⇒ I_OS(min) = 127981/36.5^1.0708 = **2717 mA** (independently reproduced), I_OS(max) 3.29 A. The TPS2557 is **guaranteed not to limit below 2.72 A**, so 2.72 A is the current a port can carry indefinitely. On the 0.800 mm × 13.554 mm B.Cu feed that is **ΔT = 19.4 °C** (IPC-2221, 1 oz external) and wants **1.132 mm** — not the 9.6 °C / 16.0 °C pair `nets.yaml` states for 2.0 / 2.5 A. Aggregate: 3 × 2.72 = **8.16 A** on a rail budgeted at 6 A, below the LM5116's 11 A valley limit so **nothing intervenes**. Survivability checked: L1 Irms 10 A / Isat 15.2 A ✓; RS1 8.16² × 10 mΩ = **0.67 W in a 1 W 2512** ✓; F1 still ≈7.2 A of 10 A because the C rail is now 3 A ✓. | Not a defect — the board survives it. **Put 2.72 A next to the 2 A in `nets.yaml`'s `current:`** so the class does not imply a limit nothing enforces, and size the recorded v-next widening on 2.72 A (≈1.15 mm), not on 2.5 A (1.10 mm). |
| **P2-6** | **E-MARGIN was never computed for the 5VA / USB-A rail**, which feeds three known 2 A loads. | P2 | `power_tree.yaml` and `DETAIL_DESIGN` sec.4 run E-MARGIN only on 5VC. I computed it (§4 below): **PASS, slack +151.8 mV** at the receptacle under the project's own 1.20 derate; **+7.8 mV** if the two 30 mΩ USB-A mating contacts are charged to the board's budget. | Add the 5VA rail to `power_tree.yaml` with the derivation. Nothing changes on the board. |
| **P2-7** | **The board declares no stackup**, so every ampacity claim's copper weight is a fab default. | P2 | `usb_hub_3s_v2.kicad_pcb` and `.kicad_pro` contain **zero** `stackup` entries. JLC's 4-layer 1.6 mm default is 1 oz outer / **0.5 oz inner**, so the In1 GND and In2 VIN planes carry **half** the copper `nets.yaml`'s "1 oz external" arithmetic assumes. It changes no conclusion (VIN's tightest section is 38.4 mm of plane and its 1.99× margin is attributed to VBAT on F.Cu, correctly), but the inner weight is unpinned. | Declare the stackup in the board, or state the assumed inner weight in `nets.yaml` beside the plane cross-sections. |
| **P2-8** | **5VA's worst static corner (5.273 V) exceeds the 5.25 V ceiling `DETAIL_DESIGN` sec.2.11 cites as its own reason not to raise the rail — and exceeds USB 2.0's 5.25 V receptacle maximum.** | P2 | sec.2.11: *"5VA is not raised, because the USB-A window ceiling is 5.25 V and a proportional bump would push its no-load corner to 5.35 V — over the port limit."* sec.4's own table then gives 5VA worst max **5.273 V**. I independently reproduce it: `1.215×1.015 × (1 + (3.92×1.001)/(1.21×0.99))` = **5.2731 V** (R3 3.92 k ±0.1 %, R4 1.21 k ±1 %, Vref ±1.5 %). USB 2.0 §7.2.1: a self-powered hub's downstream port supplies **4.75–5.25 V at the connector**. sec.5.3 catches the USBLC6 side of this (+23 mV over U8/U9/U10's 5.25 V characterised point) and dispositions it correctly; **nothing catches the USB-2.0-spec side.** No-load, all-tolerance-extremes corner only. | Record it in sec.2.11 so the sentence stops contradicting sec.4's table. No hardware change warranted for a 23 mV no-load corner. |
| **I-1** | *(informational — already correctly dispositioned; I confirm rather than re-raise)* USBLC6-2SC6 V_BUS operating above its 5.25 V characterised point on both rails. | — | I independently reproduce **5VA 5.032 / 5.151 / 5.273 V** and **5VC 5.227 / 5.352 / 5.479 V**. `DETAIL_DESIGN` sec.5.3 reads the ST datasheet correctly (**no V_BUS entry in Table 1 Absolute Ratings**; 5.25 V is the I_RM *test condition*; the device limit is **V_BR = 6.0 V min at 1 mA**), bounds the exposure at ≈4.5 µA / 25 µW over temperature, and records **ACCEPT + MEASURE** with R42 as an unpopulated trim lever. sec.5.4 records that U12 breaks down before D5. **I agree with the reading and the disposition.** | none — carry as-is. |

**No P0.**

---

## 3. A-AMP ADJUDICATION — my independent verdict on the three `nets.yaml` judgements

### Q1 — Is the 7 A battery trunk and the 7 A switch-node current genuinely carried by plane/pour copper rather than by a track?

**VERDICT: AGREE on the conclusion. DISAGREE on one margin figure, because the two methods measure different things.**

*Is it pour-carried?* Yes, and I verify it three ways rather than by re-running their sweep:

- **Track census** (every track on the board, by net/layer/width): `VBAT` and `VBAT_F` have
  **zero** routed track. `VIN` has **2.825 mm of 0.300 mm** total — exactly the UVLO
  dividers plus the two controller bias pins the file claims. `SW_A` has 31.660 mm (B.Cu)
  + 4.524 mm (F.Cu) of 0.600 mm and `SW_C` 17.063 + 19.249 mm; `nets.yaml` says
  "26.5 mm of exposed 0.600 mm SW_A B.Cu track", which is the *exposed* subset of my 31.660 mm total.
- **Point-in-filled-polygon on every claimed pad.** All eleven switch-loop power pads
  (`Q2.1/2/3`, `Q3.5`, `L1.1`, `Q4.1/2/3`, `Q5.5`, `L2.1`) sit **ON the pour on both F.Cu
  and B.Cu**; all trunk pads (`J1.2`, `F1.1/2`, `Q1.1/2/3/5`, `Q2.5`, `Q4.5`) sit on the
  pour, with `Q1.1/2/3`, `Q2.5`, `Q4.5` additionally on the **In2.Cu VIN plane**. Of the
  49 pads I audited, the **only** ones that come back NOT-ON-POUR are the six TPS2557 OUT
  pins — which is exactly what the VBUS class declares (see Q2). The claim is verified,
  not merely asserted.
- **Resistance** (my SOR, biased ≤5 % low):

  | segment | R | IR at 7 A | I²R at 7 A | R-equivalent 1 oz width |
  |---|---|---|---|---|
  | VBAT `J1.2 → F1.1` | 0.858 mΩ | 6.00 mV | 42.0 mW | 12.414 mm |
  | VBAT_F `F1.2 → Q1.5` | 0.968 mΩ | 6.77 mV | 47.4 mW | 7.176 mm |
  | VIN `Q1.S → Q2.5` | 2.218 mΩ | 15.52 mV | 108.7 mW | 11.312 mm |
  | VIN `Q1.S → Q4.5` | 2.266 mΩ | 15.86 mV | 111.0 mW | 7.650 mm |
  | **trunk total J1 → Q2** | **4.044 mΩ** | **28.3 mV** | **198 mW** | — |
  | SW_A `Q2.S → L1.1` | 0.774 mΩ | 5.42 mV | 37.9 mW | **4.241 mm** |
  | SW_C `Q4.S → L2.1` | 0.287 mΩ | 2.01 mV | 14.1 mW | 11.429 mm |

  IPC-2221 for 7 A at ΔT 10 °C, 1 oz external = **4.399 mm**. Every trunk segment is
  ≥1.63× by resistance-equivalent width. **The switch node is the exception: SW_A comes
  out at 0.96×, not 1.38×.** That is not a contradiction of their measurement — a summed
  perpendicular cross-section and a one-port resistance are different quantities, and mine
  is the one that predicts heating. At 37.9 mW spread over 281.7 mm² of SW_A pour the
  thermal question is closed regardless.

**What I would change in the file:** say *"1.38× by summed cross-section; 0.96× by
resistance-equivalent width on SW_A"* rather than a bare 1.38×.

### Q2 — VBUS: is 0.800 mm adequate at 2 A and 2.5 A, and is "2 A continuous" defensible given I_OS 2.72–3.29 A?

**VERDICT: the arithmetic is correct to every digit and the honesty about not being
pour-fed is verified. The *declared current* is the weak part — the enforced ceiling is
2.72 A, not 2.5 A.**

*Arithmetic — I reproduce all four of their numbers independently* (IPC-2221, k = 0.048
external, 1 oz = 1.378 mil, A in mil²):

| | their figure | mine |
|---|---|---|
| width required at 2.0 A, ΔT 10 °C | 0.781 mm | **0.7813 mm** |
| width required at 2.5 A, ΔT 10 °C | 1.063 mm | **1.0628 mm** |
| ΔT on 0.800 mm at 2.0 A | 9.6 °C | **9.625 °C** |
| ΔT on 0.800 mm at 2.5 A | 16.0 °C | **15.98 °C** |

*Is the class genuinely not pour-fed?* **Verified independently.** `U3.6/U3.7`,
`U4.6/U4.7`, `U5.6/U5.7` are the only NOT-ON-POUR results in my whole 49-pad audit, while
`J2.1/J3.1/J4.1` and `U8.5/U9.5/U10.5` are all on the pour on both outer layers. Refusing
to write `pour_fed:` here was the right call and it is the most defensible judgement in
the file.

*Is 0.800 mm adequate?* **At the design load, yes:** 2.0 A gives ΔT 9.625 °C, i.e.
1.024× the IPC width, on a segment terminated on the TPS2557 OUT pads at one end and a
344.70 mm² B.Cu + 275 mm² F.Cu pour (3 vias) at the other. **At 2.5 A burst,** 15.98 °C
on 8.810 mm of standalone copper is acceptable for a burst.

*Is "2 A continuous" defensible?* **Partly, and I would not leave it as written.** 2 A is
self-consistent as a *budget* (3 × 2 A = 6 A = buck-A's `iout_max_A`) but it is a statement
about the load, not about the hardware. The TPS2557 is guaranteed **not to limit below
2.72 A**, so 2.72 A is what a port can carry indefinitely, and at 2.72 A the feed sits at
**ΔT 19.4 °C** and wants **1.132 mm** — a number that appears nowhere. The width is still
fine (19.4 °C on a 1 oz outer trace, heat-sunk at both ends, is ordinary practice), so this
does not change the ORDER verdict; but the class currently reads as though something limits
the port to 2.5 A and nothing does. **Put 2.72 A in the declaration and size the recorded
v-next widening on it.**

### Q3 — GATE: 0.276 A RMS from 2 A peak at 1.9 % duty, Qg 76 nC, fsw 250 kHz

**VERDICT: AGREE with the number and with the conclusion. DISAGREE with the provenance of
Qg — it is circular, and the real gap is that the AON6354 part.yaml has no Qg at all.**

*Arithmetic — reproduced exactly:*

```
duty  = 2 edges × (76 nC / 2 A) × 250 kHz = 2 × 38 ns × 250 kHz = 0.01900   ✓
I_rms = 2 A × √0.019 = 2 × 0.137840 = 0.27568 A  → 0.276 A                  ✓
IPC-2221 width for 0.276 A, ΔT 10 °C, 1 oz ext   = 0.0509 mm  (they say 0.051) ✓
ΔT of 0.276 A on 0.300 mm, 1 oz ext              = 0.5372 °C  (they say 0.54)  ✓
5.9× margin (0.300 / 0.0509 = 5.89)                                          ✓
```

*Where the derivation is weak:*

1. **Qg ≤ 76 nC is back-derived from a capacitor that was chosen for a different reason.**
   `C_HB = 1 µF` came from TI's *"at least 0.1 µF"* guidance (sec.2.8), so inverting
   `C_HB ≥ Qg/ΔV_HB` to bound Qg is circular — any C_HB you pick yields a "bound".
2. **The 7.6 V HB rail is wrong.** `LM5116/part.yaml limits: {vcc: 7.4V internal}` and the
   HB rail sits at VCC − Vf(D3) ≈ **6.7 V**, so 1 % droop is 67 mV, not 76 mV.
3. **The actual gap:** `AON6354/part.yaml limits:` carries vds, vgs, id_25C, rds_10V,
   rds_4V5, vspike_10us — and **no Qg and no Ciss**. The datasheet parameter the derivation
   needs is simply not on file, which is why it had to be inferred from a capacitor.

*Direction of the error is conservative*, so the conclusion survives: a real AON6354 Qg is
~30–40 nC at 10 V ⇒ duty ≈ 0.0088, I_rms ≈ 0.19 A, and the margin grows to ~8×. And the
file is right that **0.300 mm is set by dI/dt loop area, not by ampacity** — which is the
correct reason for a gate-drive width. The uncomfortable part is that the dI/dt
justification is the one carrying the weight and **nobody had measured the loop**: it is
25–34 nH with the return 2.0–2.5 mm away (P2-3). I would put that measurement in the class
comment instead of the RMS arithmetic, which is not what decides anything here.

---

## 4. MANDATORY CHECKS

### E-MARGIN — every regulated rail feeding a known load

**5VC → Raspberry Pi 4 (3 A).** Reproduced: `vout_min = 1.215×0.985 × (1 + (4.12×0.999)/(1.21×1.01))` = **5.2271 V**; headroom = 5.227 − 4.63 = **597.0 mV**; `98 mΩ × 3 A × 1.20` = **352.8 mV**; **slack +244.2 mV → PASS.** The `ir_budget_mohm: 98` decomposition (Q6 4.3 + F2 31 hot + board 12 + GND return 0.956 + connector 5 + cable 45) adds to 98.3 ✓.

> **Disagreement I cannot resolve from the artifacts I am allowed to read.** My independent SOR of the same three board segments reads **3.009 mΩ** (5VC L2.2→Q6.5 **1.712**, PMID Q6.S→F2.1 **0.482**, VBUSC F2.2→J5 **0.815**) against the RL-2 solve's **9.32 mΩ** and the **12 mΩ** carried in the budget. My solver validated at 0.4–5 % low on analytic bars, so this is not a scale error in my core. If my number is right the budget is conservative by ~9 mΩ (27 mV at 3 A) and slack becomes **+276.6 mV** — safe direction either way, which is why I report it as a disagreement rather than a correction. Flagged as the thing I am least sure of.

**5VA → three USB-A ports (2 A each).** Not computed anywhere in the release (P2-6). Mine:

- `vout_min` = `1.215×0.985 × (1 + (3.92×0.999)/(1.21×1.01))` = **5.0318 V**
- Load floor: USB 2.0 §7.2.1 — a self-powered hub's downstream port supplies **≥4.75 V at the connector**. Headroom = **282.0 mV**.
- IR budget at 2 A/port (6 A on the shared pour), worst port U5/J4:

  | term | value | at 2 A |
  |---|---|---|
  | 5VA pour `L1.2 → U5.2/3` (MEASURED, full 6 A charged conservatively) | 1.895 mΩ | 11.4 mV |
  | TPS2557 rDS(on), max over −40…125 °C (SLVS931B) | 35 mΩ | 70.0 mV |
  | VBUSA feed: 13.554 mm × 0.800 mm B.Cu (9.71 mΩ hot) + 0.650 mm × 0.500 mm F.Cu bond (0.64) + 3 vias ‖ (0.17) + port pour (≈1.5) | ≈12.0 mΩ | 24.1 mV |
  | board GND return (same class as the measured 1.002 mΩ) | ≈1.5 mΩ | 3.0 mV |
  | **board total** | **≈54.3 mΩ** | **108.5 mV** |
  | + 2 × USB-A mating contact, 30 mΩ max each (USB 2.0) | 60 mΩ | 120.0 mV |

- **At the receptacle (the spec point):** `282.0 ≥ 108.5 × 1.20 = 130.2` → **PASS, slack +151.8 mV.** Delivered 4.923 V.
- **If the two mating contacts are charged to the board:** `282.0 ≥ 228.5 × 1.20 = 274.2` → **PASS, slack +7.8 mV.** Delivered 4.804 V.
- At the hardware ceiling of 2.72 A/port: 4.885 V at the receptacle (still ≥4.75 V), 4.722 V past the contacts.
- Not the board's budget, but stated so nobody is surprised: a 1 m 28 AWG USB-A cable is ≈380 mΩ round trip = **760 mV at 2 A**, which puts the device end at ~4.04 V, below USB 2.0's 4.40 V function minimum. That is a property of cheap cables, not of this board — but the 5VC budget explicitly carries its cable and the 5VA budget does not exist at all.

**VCC_A / VCC_C** are internal 7.4 V LDO rails feeding only the gate drivers; no external load, no E-MARGIN obligation.

### E-OFF — does the declared off_control actually exist in the netlist?

**YES — the enable path is real and traceable node by node.**

- `SW1` = SS12D07VG6-087 slide, **pad 1 (T1) → GND**, **pad 2 (COM) → ENKILL**, **pad 3 (T2) → `unconnected-(SW1-T2-Pad3)`**. Slide to T1 grounds ENKILL.
- `ENKILL = {Q7.1[G], Q8.1[G], R17.2, R8.2, SW1.2[COM], U11.4[EN], U2.4[EN]}` — exactly the E-INV assertion, no extra nodes.
- Both LM5116 EN pins are on it (pin 4 = EN confirmed against `LM5116/part.yaml pins:`, which records the map as read from SNVS499I Fig. 4-1).
- Q6 chain verified: `QG = {Q6.4[G], Q7.3[D], R30.2}`, `R30.1 → PMID`, `Q7.2[S] → GND`. ENKILL low ⇒ Q7 off ⇒ R30 (100 kΩ) pulls QG to PMID ⇒ Vgs(Q6) = 0 ⇒ Q6 off. Q6 body diode anode = D = 5VC, cathode = S = PMID ⇒ **blocks PMID→5VC back-feed**, which is the stated intent and the correct orientation.
- **It is an ENABLE gate, not a series power switch.** VBAT/VBAT_F/VIN stay energised whenever the XT60 is mated — no pole of SW1 touches any of them. That is precisely why the stored draw matters.

**Stored quiescent draw: DECLARED 271 µA, MEASURED-BY-DERIVATION ≈714 µA typ / ≈748 µA worst.** See **P1-1**. The E-OFF gate passes because `power_topology.py` only checks that the field is *declared*.

### Protection chain, TVS directionality, clamp-vs-protected-part ratings

Traced from `<release>/source/usb_hub_3s_v2.net`:

| element | check | result |
|---|---|---|
| **Q1 AON6403 reverse-polarity block** | For a high-side P-FET block the **drain** must face the battery. `Q1.5[D] → VBAT_F` (battery side), `Q1.1/2/3[S] → VIN` (load side). | **CORRECT.** Body diode (anode = D) conducts VBAT_F→VIN on first contact, then R1 (100 kΩ, gate→GND) enhances it. On reversal the body diode is reverse-biased **and** Vgs ≈ 0. Blocking stress ≤12.6 V vs V_DS 30 V. |
| **D2 BZT52C12 gate clamp** | `D2.1[K] → VIN` (= Q1 source), `D2.2[A] → RPP_G` (= gate). | **CORRECT and not optional.** Without it, a D1 clamp event at V_CL 24.4 V gives Vgs = −24.4 V against a ±20 V gate. Clamp current (24.4−12)/100 k = 124 µA. |
| **D1 SMBJ15A input TVS** | `D1.1[K] → VIN` (i.e. **after** Q1), `D1.2[A] → GND`. | **CORRECT.** On VBAT_F it would be a crowbar across a reversed pack through a 10 A fuse. Standoff 15.0 V > 12.6 V ✓; V_BR 16.7–18.5 V clear of the rail ✓; V_CL 24.4 V vs AON6354 V_DS 30 V / V_spike 36 V, AON6403 30 V, C1/C2 35 V, C9-C12 50 V, LM5116 VIN 100 V — **all clear**. |
| **D5 SMBJ6.0A VBUSC clamp** | `D5.1[K] → VBUSC`, `D5.2[A] → GND`. Uni-directional required (a bidirectional part has no cathode). | **CORRECT.** Fitted part C113976 is JLC-catalog-verified uni-directional; C140903 is explicitly `do_not_use` for being listed bidirectional. V_WM 6.0 V clears the 5.479 V no-load corner by **521 mV**. V_CL 10.3 V is above the Pi's 6.0 V ceiling — recorded as best-effort/crowbar in ADR-0002 and sec.5.1, and I agree with that framing. |
| **U12 / U8-U10 USBLC6-2SC6** | V_BUS pin vs rail corners. | See **I-1**: operating above the 5.25 V characterised point (5.479 V worst on VBUSC, 5.273 V on 5VA), below the 6.0 V V_BR minimum. Correctly read and dispositioned in sec.5.3/5.4. |
| **F2 SMD2920-700 PPTC** | 7 A hold (≈5.6 A at 50 °C) vs 5 A provisioned / 3 A actual; V_max 16 V vs a 12.6 V buck-fail-high. | **CORRECT sizing**, and the 6 A alternative is correctly rejected (4.8 A at 50 °C < 5 A). 4 vias per pad. |
| **R28/R29 USB-C Rp** | `R28.1 → CC1`, `R29.1 → CC2`, both `.2 → VBUSC`. 10 kΩ ±1 % (0402WGF1002TCE, C25744). | **CORRECT for 3.0 A.** USB Type-C Rp with a 4.75–5.5 V pull-up: 56 k = default, 22 k = 1.5 A, **10 k ±5 % = 3.0 A**; ±1 % is inside it, and VBUSC's 5.227–5.479 V window is inside 4.75–5.5 V. Matches the Pi 4's 3 A per ADR-0004. *Deviation, deliberate:* VBUS is applied before attach (no CC-gated VBUS switch) — the always-on-charger shortcut, not a compliant Type-C source. |
| **RS1/RS2 + current limit** | 10 mΩ, V_CS(TH) 0.11 V (VCCX = GND ✓, pin 17 → GND on both). | I_LIM = 11.0 A ✓; TI eq. (11) satisfied (13.3 / 15.1 mΩ allowed) ✓; P = 0.36 / 0.25 W in a 1 W 2512 ✓. Sense **accuracy** degraded by P2-1. |
| **U7 unused DCP channel** | `U7.3[DP2]`, `U7.4[DM2]`. | Both carry proper no-connect flags (`unconnected-(U7-DP2-Pad3)` / `-DM2-Pad4)`). ✓ Along with U3/U4/U5 FAULT and J5 SBU1/SBU2 — 8 NC nets, all flagged. |

### Docs ↔ implemented BOM/netlist diff

- **Netlist ↔ BOM: exact.** 122 designators, zero refs in the netlist missing from the BOM, zero BOM refs absent from the netlist.
- **BOM ↔ CPL:** 3 designators in BOM but not CPL — **F1** (blade-fuse holder, no JLC placement model), **SW1**, **R42** (DNP setpoint-trim strap). All three are declared `not_assembled` with dated evidence in `03_src/rules/assembly.yaml`. **No undocumented mismatch.** I confirm R42 is a 160 kΩ 0402 in **parallel** with R12 that, if fitted, moves 5VC 5.352 → 5.249 V; it is correctly off the CPL, and the rail corners in `power_tree.yaml` correctly assume it unpopulated.
- **DETAIL_DESIGN vs netlist:** every value in the sec.7 traceability table matches the netlist. The one substantive divergence is sec.2.5's Kelvin claim (P2-1); the one internal contradiction is sec.2.11 vs sec.4 on the 5.25 V ceiling (P2-8).

### Buck hot loop, layer adjacency, thermal

- **Hot-loop perimeter, HF cap → HS → SW → LS → shunt → shunt GND → HF cap GND: 59.20 mm** on *both* bucks (identical to 0.01 mm — the cells are geometrically mirrored). Segments (buck-A): C13.1→Q2.5 5.38, Q2.5→Q2.S 5.39, Q2.S→Q3.5 6.10, Q3.5→Q3.S 5.39, Q3.S→RS1.1 7.07, RS1.1→RS1.2 5.92, **RS1.2→C13.2 23.94**. The LM5116's source-side shunt is what stretches it: RS1 sits 5.83 mm below Q3 and its GND end is 23.94 mm from the nearest HF ceramic's ground pad.
- **This is redeemed by the plane, and the plane is intact.** In1.Cu GND is 97.5 % solid under the loop with no slots, 0.2104 mm below F.Cu on JLC's default 4-layer stack, so the return images under the forward path: effective loop inductance ≈ **2.3 nH** (µ₀·h·l/w with l ≈ 35 mm, w ≈ 4 mm), giving ≈1.1 V of L·di/dt at 7 A / 15 ns before package and cap ESL — comfortably inside AON6354's 30 V V_DS, and the R34/C53 and R35/C54 snubbers (2.2 Ω + 1 nF) are fitted. Measured DC return `RS1.2 → Cin GND` = **1.002 mΩ** (buck-C 1.012 mΩ).
- **Layer adjacency:** F.Cu references In1 GND (0.2104 mm) ✓; B.Cu references **In2 VIN** (0.2104 mm), so the B.Cu SW islands' image lands in the VIN plane. Cost measured rather than argued: C = ε₀ε_r·A/d = 8.854e-12 × 4.3 × 195.985 mm² / 0.2104 mm = **35.5 pF** per switch node, and C·V²·f = 35.5 pF × 12.6² × 251.8 kHz = **1.42 mW**. Negligible, and VIN is an AC ground behind 32 µF of local ceramic.
- **Switch-node area is justified, not excessive:** SW_A 281.7 mm², SW_C 390.8 mm². The PowerPAK tab is the **drain**, so the SW node is the LS FET's only heatsink (Q3 conduction ≈ 0.11 W at 6 A). Q3.5 has **0 vias** and Q5.5 has **1**, which the R-THERM waiver covers correctly on mechanism (SW is not a plane net, so the ≥2-plane-via heuristic is unsatisfiable).
- **Thermal vias, measured (centre inside the pad polygon):** U2.21 **7**, U11.21 **7**, U3.9/U4.9/U5.9 **1 each**, Q1.5 **2**, Q2.5 **5**, Q4.5 **5**, Q6.5 **0**, L1.2/L2.2 **0**, F2.1/F2.2 **4 each**, RS1.2/RS2.2 **1 each**. Dissipation vs path: LM5116 LDO (12.6−7.4) × ~43 mA = **224 mW** into a 22.1 mm² EP with 7 vias ≈ 8 °C ✓; TPS2557 140 mW at 2 A / 259 mW at 2.72 A into a 1-via EP on the F.Cu GND pour ≈ 7–13 °C ✓; Q6 at the Pi 4's 3 A = 3² × 4.3 mΩ = **39 mW** ✓.
- **ENKILL susceptibility — checked and largely cleared.** 132.969 mm of 0.200 mm F.Cu track on a 50 kΩ (R8‖R17) node driving both EN pins with **no filter capacitor anywhere on the net**. But measured minimum same-layer gap to SW_A/SW_C copper is **6.048 mm**, zero millimetres run within 1.0 mm, and it crosses no SW/VBAT/VIN pour on its own layer, running instead over the solid In1 GND plane. Recorded as a robustness note, not a finding.

---

## 5. WHAT I AM LEAST COMFORTABLE WITH

Two things, in order.

1. **The buck-A / buck-C copper asymmetry, and the fact that nothing measured it.** Two
   nominally identical, mirrored cells whose pour copper differs by **2.7× on the switch
   node (0.774 vs 0.287 mΩ)** and **3.2× on the LS-source node (6.578 vs 2.083 mΩ)**, with
   the worse one landing at 0.96× of the IPC-2221 7 A line by resistance-equivalent width.
   Nothing here is thermally dangerous — 38 mW and 143 mW respectively — but it says the
   pour result is not deterministic across mirrored cells, and a cross-section sweep is
   blind to it by construction, because a 0.300 mm neck 0.8 mm long barely moves a
   cross-section sum while tripling a resistance.
2. **My 3.009 mΩ vs RL-2's 9.32 mΩ on the identical three 5VC delivery segments.** Both are
   SOR mesh solves; mine is validated against analytic bars at 0.4–5 % low; I cannot
   reconcile a 3× disagreement from the artifacts I am permitted to read. It is in the safe
   direction (the shipped budget is the pessimistic one), which is the only reason it is not
   a finding — but two solvers disagreeing 3× on the same copper is exactly the kind of
   thing that should be settled by the bench, not by whichever number reached the file first.

Also worth naming: my resistance numbers carry a stated 0.4–5 % low bias, and my E-OFF
figure is an **arithmetic derivation from the netlist, not a measurement** — the ORDER_README
bench gate remains the thing that qualifies it, which is precisely why its threshold has to
be corrected first.

---

## 6. VERDICT

The defect this release exists to fix is **fixed and independently falsifiable**: 106 filled
islands / 44 282.1 mm² in the board, the same 106 regions and the same areas in the shipped
gerbers, zero stranded islands, and a stranded-island check proven able to fail on both
inner planes. Placement and connectivity are unchanged (CPL byte-identical, netlist parity
0), DRC is 0/0/0, and the BOM/CPL/netlist reconcile with no undocumented mismatch. The
protection chains, TVS directionalities and clamp-vs-part rating pairs all check out, and
the one rating exceedance that exists (USBLC6 V_BUS) was already read correctly from the
datasheet and dispositioned with evidence.

**No P0.** The P1 is a paperwork-and-gate defect that changes no copper: the E-OFF quiescent
figure is 2.6× low because two 56.88 kΩ UVLO dividers sit permanently across VIN and were
never counted, which would make the ≤300 µA bench gate condemn a good board. Fix the number
and the threshold before the bench runs; nothing about the order changes.

Two pre-order conditions already declared by the release stand and are not mine to waive:
the A-POL single-channel **JLC order-preview human gate** (`rotation_human_gate.txt`:
C130056, C13755, C473910, C7519, C98732) and the order-day stock recheck on the
Extended-tier parts (C6165170 F2, C113976 D5).

**VERDICT: ORDER**
