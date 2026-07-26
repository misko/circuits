subject: usb-hub-3s-v3 @ 04_kicad/usb_hub_3s_v2.kicad_pcb (working tree, routing GATE GREEN, DRC 0/0/0; commit 4982891 lineage)
date: 2026-07-22
reviewer: redteam-agent (claude-opus-4-8, layout/thermal/power-integrity lens)
context-given: full-tree (measured directly with pcbnew) — the build's R-THERM disposition (journal 04_board.md) treated as an UNTRUSTED claim to be independently re-derived
verdict: ORDER

---

# Red-team review — layout / thermal / power-integrity

## 0. Bottom line

**ORDER.** The board is physically orderable as-routed. Every finding is P2.
There is **no P0 and no P1** — no thermal defect, no ampacity shortfall, no
power-integrity failure that measurement supports.

The single failing gate — `R-THERM FAIL` in `06_build/policy_audit.md`
(`['Q5.5(1)','Q1.5(0)','Q3.5(0)','U11.21(1)']`) — is, on measurement, **three
structural false-positives plus one minor best-practice gap**, not a copper
defect. It must still be *dispositioned* (waiver-with-evidence, using this
review) before the release can seal, but it does not gate the fab.

Method note (canon M1 — checker and checked must not share a method): I did not
accept the build's "false-positive" narrative. I re-derived it independently —
rasterised the pours to establish the per-net layer census, counted same-net
vias from the track list, computed FET/EP dissipation from datasheet Rds(on),
and scanned **every** sizeable power pad (not just the four flagged) for the
opposite error (via-starvation the 4.0 mm² threshold would hide). Scripts and
raw output are in the appendix; all numbers below are measured.

---

## 1. Board facts (measured)

| property | value |
|---|---|
| copper layers | 4 — F.Cu / **In1.Cu = GND plane (11454 mm²)** / **In2.Cu = VIN plane (11323 mm²)** / B.Cu |
| board | 130.1 × 92.1 mm, 1.6 mm |
| outer copper | 1 oz (F.Cu/B.Cu pours); inner planes 0.5 oz |
| the only two internal-plane nets | **GND (In1), VIN (In2)** — measured by zone-layer census |
| nets with NO internal plane (F/B pours only) | VBAT_F, VBAT, SW_A, SW_C, 5VA, 5VC, VBUSA1-3, CS_A, CS_C |
| converters | 2× LM5116 (C13755), RT=12.4k → fsw a few-hundred kHz (build cites ~230 kHz) |
| power FETs | Q2-Q5 = AON6354 N-ch (5.2 mΩ@4.5V, 83 A); Q1 = AON6403 P-ch (3.1 mΩ@10V, 85 A) — DFN 5×6 |
| DRC | `gate.json` / `gate_parity.json`: violations=[], unconnected=[], schematic_parity=[] → **0/0/0 confirmed** |

The decisive structural fact for the whole R-THERM question: **only GND and VIN
exist on an internal plane.** SW_A, SW_C and VBAT_F are, by design, F.Cu (±B.Cu)
pour nets with no plane anywhere in the stack.

---

## 2. R-THERM adjudication — measured verdict per pad

R-THERM (canon R6) intent, verbatim from `design-policies.md`: *"EPs and power
pads get via arrays **to the plane**…"*. The implementation counts same-net vias
within (pad ± 1 mm) and fails a >4 mm² SMD power pad with < 2. The load-bearing
words are **to the plane** — the rule presupposes a same-net plane exists to
sink into. For 3 of the 4 flagged pads, it does not.

### The heuristic proven correct on its controls (measured)

Before judging the failures, confirm the rule *works* where a plane exists:

| pad | net | plane? | vias ≤1 mm | R-THERM |
|---|---|---|---|---|
| Q2.5 | VIN | In2 ✔ | **3** | PASS |
| Q4.5 | VIN | In2 ✔ | **3** | PASS |
| U2.21 (LM5116-A EP) | GND | In1 ✔ | **3** | PASS |
| U3.9/U4.9/U5.9 (TPS2557 EP) | GND | In1 ✔ | **2** each | PASS |

The HS FET drains (Q2/Q4) sit on VIN, drop into the In2 VIN plane through 3 vias
each, and pass. Same part, same 14.9 mm² pad as the *flagged* LS drains — the
only difference is whether the net has a plane. That asymmetry is the whole
story.

### FLAGGED pad 1 — Q1.5 (VBAT_F, AON6403 reverse-polarity P-FET drain) — **FALSE POSITIVE**

- Measured: pad 3.81×3.91 = **14.9 mm²**, F.Cu only, pos (35.3, 66.0).
- **VBAT_F copper is F.Cu-only** (170 mm², 0 internal, 0 B.Cu) → same-net vias on
  the whole net: **0**. A thermal via here would land on bare laminate; the
  heuristic is **structurally unsatisfiable**.
- Dissipation: I = 6.8 A worst case (55 W / 0.9 / 9 V), Rds 3.1 mΩ →
  **P ≈ 0.14 W** conduction (always-on FET, no switching loss). DFN 5×6 θ_JA
  ≈ 40-60 °C/W → ΔTj ≈ 6-9 °C into a 14.9 mm² pad on a 170 mm² pour.
- **Verdict: not a thermal defect.** No plane to sink into by design (short
  XT60→fuse→Q1 trunk); < 0.15 W dissipation. See §4 for the separate — and also
  passing — VBAT_F *ampacity* check.

### FLAGGED pad 2 — Q3.5 (SW_A, AON6354 buck-A LS drain) — **FALSE POSITIVE**

- Measured: 14.9 mm², F.Cu, pos (76.7, 38.0). Same-net vias ≤1 mm: **0**; within
  5 mm: 2. SW_A copper = F.Cu 193 mm² + **B.Cu 195 mm²**, joined by 4 stitch vias
  — **no internal plane** (correct: a switch node must not be poured onto a
  plane).
- Dissipation: LS rms = 6·√(1-D), worst at Vin 12.6 (D=0.40) → 4.65 A; Rds 5.2 mΩ
  → **P ≈ 0.11 W** + dead-time body-diode. Pad on ~388 mm² of 2-layer copper.
- The rule wants "2 same-net **plane** vias"; SW has no plane and *should* not.
  The intentional minimal-via count is the dV/dt-management choice named in
  `nets.yaml` (SWITCH_NODE: *"Keep loop area minimal"*). **Verdict: not a defect.**

### FLAGGED pad 3 — Q5.5 (SW_C, AON6354 buck-C LS drain) — **FALSE POSITIVE**

- Measured: 14.9 mm², F.Cu, pos (76.7, 76.0). Same-net vias ≤1 mm: **1**. SW_C =
  F.Cu 100 + B.Cu 100 mm², 2 vias. No internal plane.
- Dissipation: 5 A rail → LS rms 3.87 A → **P ≈ 0.08 W**. Lowest of the three.
- **Verdict: not a defect** — identical reasoning to Q3.5; already has 1 F↔B
  stitch via bridging its two pours.

### FLAGGED pad 4 — U11.21 (LM5116 buck-C GND exposed pad) — **REAL BUT MINOR (P2)**

This one is *different* and I am not waving it away: GND **does** have an
internal plane (In1), so the rule legitimately applies.

- Measured: EP 3.40×6.50 = **22.1 mm²**, net GND. Same-net vias ≤1 mm: **1**;
  **within 5 mm: 11**. Sister EP **U2.21 (buck A) has 3 ≤1 mm / 15 within 5 mm**
  and passes.
- Root cause (confirmed against journal + footprint history): the STANDARD-tier
  swap dropped the LM5116 ThermalVias footprint (0.2 mm baked vias failed the
  0.3 mm drill floor); `pad_rescue` then re-seeds exactly one via-in-pad, and the
  stitch grid happened to drop a 2nd near U2.21 but not U11.21. It is grid luck,
  not intent.
- Is it a defect? **Thermally, no.** The LM5116 is a *controller* (external
  FETs): dissipation ≈ gate-drive (2·Qg·Vdrv·fsw) + Iq ≈ **0.15-0.20 W**. The EP
  is continuous with the F.Cu GND pour (5945 mm²) and bonded to the In1 plane by
  1 direct via **plus 11 GND vias within 5 mm**. Junction rise is negligible.
- **Electrically**, the EP is the AGND/PGND/LO-driver return reference; best
  practice (and the backfilled datasheet layout block) wants a via *array*, not a
  single direct via. With the surrounding via field it is adequate at ~230 kHz,
  but it is below the standard the sister buck meets.
- **Verdict: P2.** Add a 0.3 mm EP via array (≥ 4) under **both** LM5116 EPs on
  the next spin for symmetry + PGND-inductance margin. Not an order blocker.

### False-NEGATIVE scan (the adversarial inverse)

R-THERM skips pads < 4.0 mm². The STANDARD footprint swap that stripped
ThermalVias from the LM5116 **and** the TPS2557 raised the obvious worry that a
via-starved EP is hiding just under the threshold (the canon's own cautionary
example is *"TPS2557 EPs shipped with zero in-pad vias"*). Measured — it is not:

- TPS2557 EPs **U3.9/U4.9/U5.9** = 4.00 mm², GND, **2 stitch vias each** (4-5
  within 5 mm). Adequate; the canon failure mode is **not** reproduced here.
- Every sub-threshold GND/VIN pad (decouplers, shunt GND, D1, C1/C2) carries ≥ 1
  plane via plus a local via field. Nothing on a plane net is stranded.
- Every sub-threshold pad with **0** vias is on a **non-plane pour net**
  (5VA/5VC output caps, CS shunt sense) where a via would serve nothing.

**Conclusion:** the flag set is exactly {no-plane-by-design ×3} ∪ {grid-shorted
GND EP ×1}. R-THERM is behaving as a blunt instrument that cannot express "this
net has no plane"; it is not surfacing a hidden thermal problem, and it is not
missing one.

---

## 3. Buck hot-loop / switch-node integrity (measured)

Commutation-loop pad spans (both bucks identical by construction):

| span | Buck A | Buck C |
|---|---|---|
| HS drain (VIN) ↔ HF Cin (C13/C28) | 4.82 mm | 4.82 mm |
| HS drain ↔ LS source (CS return) | 6.41 mm | 6.41 mm |
| SW handoff HS.S ↔ LS.D | 6.41 mm | 6.41 mm |
| LS source ↔ Cin (loop return leg) | 11.12 mm | 11.12 mm |

- The high-di/dt loop closes vertically into the **In1 GND plane one dielectric
  (~0.1-0.2 mm) below F.Cu**, so the effective loop *area* is small despite the
  ~11 mm lateral return — the return current mirrors under the F.Cu run. At a
  few-hundred kHz with these non-GaN FETs this is comfortable.
- HF input cap 4.82 mm from the HS drain — good.
- SW node: F.Cu-primary (193/100 mm²) with a parallel B.Cu pour. B.Cu SW couples
  dV/dt into the **In2 VIN plane** beneath it, but VIN is heavily bypassed
  (2×100 µF polymer + 4×10 µF/buck) i.e. an AC-quiet node; coupling est. ~40 pF →
  ~20 mA displacement. The B.Cu SW pour is a net *help* to Q3/Q5 drain heat-
  spreading (reinforcing §2's FET verdicts). Acceptable.
- **Note (P2):** the ~6.4 mm lateral HS↔LS / SW spans are looser than ideal;
  fine at this fsw, worth tightening if the cells are ever re-placed.

---

## 4. Ampacity (measured pour cross-sections + via parallelism)

| net | worst I | F.Cu | B.Cu | vias | on-path neck | verdict |
|---|---|---|---|---|---|---|
| **5VC** (USB-C, the 5 A headline) | 5 A | 1055 mm² | 1116 mm² | **11** | ~6 mm | **PASS** — 6 mm 1 oz alone ≈ 5 A @ ~8 °C; B.Cu in parallel + 11 vias = large margin |
| 5VA (USB-A rail) | 6 A | 1052 mm² | 1143 mm² | 7 | ~10.6 mm trunk (3.6 mm is a no-current Kelvin spur) | PASS |
| VBUSA1/2/3 | 2.5 A ea | ~300 | ~345 | 3 ea | 0.5 mm floor + pour | PASS |
| VIN | 6.8 A | 620 mm² | (In2 plane 11323) | 29 | plane | PASS |
| **VBAT_F** (full input) | 6.8 A | **170 mm² F.Cu-only** | none | **0** | **3.6 mm @ x=38** | PASS, least margin → **P2** |

VBAT_F is the only power net worth a second look: single-layer, zero vias, and a
genuine on-path waist. I profiled the pour column-by-column — the fuse→Q1 channel
narrows to a **3.6 mm** vertical crossing at x=38 (between the Q1-drain blob and
the fuse pads). At 6.8 A worst case on 1 oz that is ΔT ≈ 13-15 °C (IPC-2221
external); nominal 3S (11.1 V → 5.5 A) is ~8 °C. **It meets ampacity** — but it
is the thinnest-margin power path on the board and shares its remedy with the
Q1.5 R-THERM flag: a B.Cu VBAT_F pour + 2-3 stitch vias would halve the current
density and drop the Q1 drain temperature. **P2, next spin.** The 5 A USB-C
deliverable itself (5VC) is not close to any limit.

---

## 5. Gate-drive dress (measured)

| net | length | width | layers | vias |
|---|---|---|---|---|
| HO_A | 20.2 mm | 0.30 | F+B | 2 |
| HO_C | **24.1 mm** | 0.30 | F | 0 |
| LO_A / LO_C | 11.1 / 11.2 mm | 0.30 | F | 0 |
| BOOT_A / BOOT_C | 14.4 / 12.0 mm | 0.30 | F | 0 |

No series gate resistor (LM5116 has internal drivers — standard). HO_C at 24 mm
is the longest single gate run (~24 nH loop); at a few-hundred kHz into AON6354
(~25-30 nC) this rings modestly but is not a hazard. **Note (P2):** shorten HO_C
/ HO_A if the buck-C control cluster is re-placed. Not an order blocker.

---

## 6. Stackup / return-path note (P2, informational)

In2 is a **VIN** plane, not a second GND. Therefore a *single-ended* signal
routed on **B.Cu** references VIN, not GND — a return-path discontinuity in the
abstract. For this board's B.Cu signal set (short gate/sense stubs and
differential USB pairs, which self-reference) the consequence is negligible, and
GND (In1) is directly under the F.Cu where the sensitive analog actually lives.
Recorded so a future high-speed single-ended net on B.Cu is not added blind.

---

## 7. Findings ledger (all P2 — nothing blocks the order)

| id | finding | severity | verification | recommended disposition |
|---|---|---|---|---|
| L-1 | R-THERM Q1.5(VBAT_F)/Q3.5(SW_A)/Q5.5(SW_C) are structural false-positives: nets have no internal plane (measured In1=GND, In2=VIN only); FET dissipation < 0.15 W into 14.9 mm² pads | P2 | confirmed (zone-layer census; via list; Rds datasheet) | **waived — this review** (add `R-THERM` entry to `03_src/rules/policy_waivers.yaml` citing §2 → flips FAIL→WAIVED) |
| L-2 | U11.21 LM5116 buck-C GND EP has 1 direct via vs 3 on U2.21; adequate (1 direct + 11 GND vias ≤5 mm + In1 plane; controller ~0.15 W) but below the EP-array standard the sister buck meets | P2 | confirmed (via count both EPs) | recorded — add 0.3 mm EP via-array (≥4) under **both** LM5116 EPs, next spin |
| L-3 | VBAT_F single-layer F.Cu-only 6.8 A trunk, 170 mm², on-path 3.6 mm neck, 0 vias — meets worst-case ampacity (~13-15 °C) but least-margin power net | P2 | confirmed (column profile @ x=38) | recorded — add B.Cu VBAT_F pour + 2-3 stitch vias, next spin (also drops Q1 drain temp) |
| L-4 | HO_C 24 mm longest gate run; buck lateral loop spans ~6.4 mm — fine at fsw | P2 | confirmed (track length; pad spans) | recorded — tighten if buck-C re-placed |
| L-5 | In2 = VIN plane; B.Cu single-ended signals reference VIN not GND (low consequence for this signal set) | P2 | confirmed (layer census) | recorded — informational |

No P0. No P1. All five are P2 (recorded / waived).

## 8. Verdict

**ORDER.** DRC 0/0/0 is real; the R-THERM FAIL is 3 measured structural false-
positives + 1 minor grid artifact, none a copper defect. Before the release
seals, disposition L-1 as a waiver-with-evidence (this review) so `policy_audit`
goes green honestly, and carry L-2/L-3 into the next-rev work order. The physical
board as routed is good to fab.

Gate reminder (08_reviews/contracts.md): a sealed release needs BOTH red-team
lenses at ORDER — this layout/thermal/PI file plus the topology/protection file —
and every row above transcribed into `DISPOSITIONS.md`.

---

## Appendix A — reproduction

Read-only pcbnew measurement (KiCad-bundled `/usr/bin/python3`), scripts in the
review session scratchpad:
- `rt_measure.py` — stackup, zone/net/layer census, flagged-pad + comparator via
  counts, via census, hot-loop spans, SW pour areas, ampacity, gate dress.
- `rt_neck.py` — pad-membership per power net + rasterised pour necks.
- `rt_vbatf.py` — VBAT_F column/row fill profile (locates the x=38 3.6 mm waist).
- `rt_scan.py` — all SMD pads ≥ 3 mm² on power/GND nets vs same-net via support
  (the false-negative sweep) + internal-plane-net set.

## Appendix B — key raw measurements

    internal-plane nets (zone census): GND (In1, 11454 mm²), VIN (In2, 11323 mm²) — ONLY these two
    VBAT_F copper: F.Cu 170 mm², B.Cu 0, internal 0, vias 0
    SW_A: F.Cu 193 + B.Cu 195 mm², vias 4, no plane
    SW_C: F.Cu 100 + B.Cu 100 mm², vias 2, no plane

    flagged pads (net / area / vias ≤1 mm / within 5 mm):
      Q1.5  VBAT_F 14.9 mm²  0 / 0      (no plane on net)
      Q3.5  SW_A   14.9 mm²  0 / 2      (no plane on net)
      Q5.5  SW_C   14.9 mm²  1 / 1      (no plane on net)
      U11.21 GND   22.1 mm²  1 / 11     (In1 plane exists)
    comparators (pass):
      Q2.5  VIN    14.9 mm²  3 / 5      (In2 plane)
      Q4.5  VIN    14.9 mm²  3 / 4      (In2 plane)
      U2.21 GND    22.1 mm²  3 / 15     (In1 plane)
      U3/4/5.9 GND  4.0 mm²  2 / 4-5    (TPS2557 EP — vias present)

    dissipation (worst case, datasheet Rds):
      Q1 AON6403  6.8 A  3.1 mΩ  ~0.14 W   (VBAT_F, always-on)
      Q3 AON6354  4.65 A 5.2 mΩ  ~0.11 W   (SW_A LS)
      Q5 AON6354  3.87 A 5.2 mΩ  ~0.08 W   (SW_C LS)
      U2/U11 LM5116 controller   ~0.15-0.20 W (EP)

    ampacity necks:  5VC ~6 mm (F+B ~2170 mm², 11 vias) ;  VBAT_F 3.6 mm @ x=38 (1 oz, ~13-15 °C @ 6.8 A)
    hot loop: HSdrain↔Cin 4.82 mm ; HSdrain↔LSsource 6.41 mm ; return leg 11.12 mm (mirrors in In1 GND under F.Cu)
    gate: HO_A 20.2 / HO_C 24.1 / LO 11.1-11.2 / BOOT 12.0-14.4 mm, all 0.30 mm
    DRC gate.json: violations=[] unconnected_items=[] schematic_parity=[]  → 0/0/0
