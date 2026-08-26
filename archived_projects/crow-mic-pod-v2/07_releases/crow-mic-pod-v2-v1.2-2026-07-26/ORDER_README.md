# ORDER README — crow-mic-pod-v2 (remote microphone POD, board a) — v1.2

> **v1.2 is a PACKAGING supersede of v1.1, not a board change.** One difference:
> the assembly drawing ships as the single 2-page `pdf/assembly.pdf` (front,
> then back) that the release contract requires, replacing v1.1's
> `assembly_front.pdf` + `assembly_back.pdf` pair (same content, merged).
> `fab/`, `source/`, `3d/` and every `verification/` artifact are byte-identical
> to v1.1 — v1.1 gerbers/BOM/CPL remain correct and orderable as-is. Everything
> below is otherwise the v1.1 text, still accurate.

Cable-powered remote acoustic node for the CROW ACOUSTIC LOCALIZATION ARRAY.
One Cat5e home-run from the CENTRAL recorder powers, references and (for
calibration) drives it: AOM-5024 electret (MK1) → OPA1678 active-balanced
driver (U1, ~3 V/V diff) → TPD2E2U06 ESD (D1) → RJ45 (J1). CMT-8504
calibration transducer (LS1) + SS14/SMAJ6.0A clamps in an isolated beep loop.

Release **v1.1-2026-07-25**. Board **80 × 45 mm, 2 layer**.

> ### v1.1 is a PAPERWORK-ONLY release. The board did not change.
> `source/`, `pdf/`, `3d/` and all of `fab/` **except `bom.csv`** are
> **byte-identical to v1.0-2026-07-23** — same gerbers, same drills, same CPL,
> same copper. **No respin occurred.** The one file that changed in the order
> set is `fab/bom.csv`, which lost two rows it should never have carried.
> Everything else is documentation.
>
> Asserted mechanically, not claimed: `release_freshness_check.py
> --bom-only-supersede` re-checks the identity of every other file AND pins the
> shape of the one permitted change — whole rows REMOVED for designators that
> are **not on the CPL**; a row added, a row edited, or a removal for a
> still-placed designator all FAIL. Independently, the gerbers were **re-plotted
> from the staged `source/`** and compared to the shipped zip: **11/11
> identical** (`verification/payload_identity.txt`).

This board is **VERIFIED and ORDERABLE**. DRC 0 violations / 0 unconnected /
0 schematic-parity, ERC 0 errors, policy_audit 0 FAIL, JLC twin exit 0 (26/26
bodies), A-POP + A-POS PASS, A-STOCK PASS, P-FACT OK. The DRC was run against
the archive's OWN `source/`, which resolves every footprint through the
vendored `fp-lib-table` shipped beside it (V-REL-FPLIB) — that is what the
empty violation list demonstrates; kicad-cli emits no separate
`lib_footprint_issues` key. Evidence in `verification/`; per-file hashes +
provenance in `MANIFEST.txt`.

---

## 0. ⚠️⚠️ CRITICAL DEPLOYMENT CONSTRAINT — NOT ETHERNET, NEVER PLUG INTO PoE ⚠️⚠️

**THIS RJ45 IS NOT ETHERNET. It carries a CUSTOM 5 V AUDIO/POWER pinout. NEVER
plug this pod (or its cable) into an Ethernet switch, router, or ANY
Power-over-Ethernet (PoE) source.**

WHY (accepted-risk sign-off, ADR-0005 / BRIEF A1): this board's power contacts
**4,5 = +5V_AUDIO** and **7,8 = GND** alias EXACTLY onto IEEE 802.3af/at
"Alternative-B" PoE, and +5V_AUDIO ties to the OPA1678 supply pin (V+, abs-max
**40 V**) with **zero series impedance**. A PoE switch drives **44–57 V** into
V+ and forces the ESD array into ~13 W sustained conduction — **this DESTROYS
the board and is a burn/smoke hazard in an outdoor enclosure.** There is
**deliberately NO protection network and NO connector re-pin** on this rev (the
user accepted this for a controlled deployment). The ONLY mitigation is
administrative:

- The pod mates **ONLY** with the sibling CENTRAL recorder's non-PoE,
  custom-pinout ports, over the custom-crimped Cat5e home-run.
- Use ONLY the array's own custom cables. **Never** introduce a standard
  Ethernet patch cable.
- The silk banner **"NOT ETHERNET — CUSTOM 5V AUDIO PINOUT"** + full pinout
  legend are printed adjacent to J1 — keep them legible; do not obscure.
- Reverse-crimp (swapping 4/5 with 7/8) is equally destructive — verify the
  crimp against the legend before first power.

A future rev that must survive uncontrolled infrastructure needs a PoE-defeat
network (clamp <40 V + PPTC fuse on 5V_AUDIO) or moving 5V_AUDIO off contacts
4/5/7/8 — see ADR-0005.

---

## 1. JLCPCB order options

| Setting | Value |
|---|---|
| Layers | **2** |
| Dimensions | **80 × 45 mm** (Edge.Cuts outline centreline, measured 80.0000 × 45.0000). The 80.1 × 45.1 figure in v1.0's MANIFEST was the bounding box *including* the 0.1 mm Edge.Cuts stroke — same board, different measurement. Order against **80 × 45**. |
| Via tier | **`jlc_2layer_default`** — 0.6 mm pad / 0.3 mm drill vias; 0.127 mm track/space floor. **Standard 2-layer process; do NOT select the advanced small-via option** (not needed). |
| Impedance control | not required |
| Surface finish | HASL or ENIG (ENIG preferred for the SOT-553 D1 paste release) |
| **Build quantity** | **8** — 6 deployed pods (BRIEF.md) + 2 spares. Declared in `03_src/rules/assembly.yaml`; A-STOCK grades every line against it. |
| Assembly | **top side only, 26 SMD parts, SMT service — NO THT assembly service required.** The board's only two through-hole parts (MK1, J1) are hand-soldered by us. |
| Extended-tier parts | **5 Extended / 10 Basic** → five one-off feeder setup fees per order: C49066 (100 µF 1210), C192421 (OPA1678), C1972959 (TPD2E2U06), C22359707 (CMT-8504), C559105 (SMAJ6.0A). Measured from the `type` field of `verification/stock_check.json` (`expand`=5, `base`=10 over 15 lines). The **tier split is evidenced; the fee schedule is not** — JLC's pricing is a cost claim we do not measure. All five parts are load-bearing; accept the fees. |

Upload set (in `fab/`):
- **PCB order:** `crow_mic_pod_v2_gerbers.zip` (F/B copper, F/B mask, F/B paste,
  F/B silk, Edge_Cuts, PTH + NPTH drills). BOM/CPL are **not** in the zip.
- **Assembly BOM:** `fab/bom.csv` (`Comment,Designator,Footprint,MPN,LCSC`).
- **Assembly CPL:** `fab/cpl.csv` (`Designator,Val,Package,Mid X,Mid Y,Layer,Rotation`).

**BOM/CPL agree exactly: 26 designators each, no row on one and not the other,
and every BOM line carries a real LCSC code.** This is the v1.1 fix — see §7.

### ⏳ STOCK: order promptly. LS1 is the clock.

`verification/stock_check.json` is **PASS** for all 15 lines at quantity 8
(measured 2026-07-25). But **LS1 (CMT-8504, C22359707) is at stock 69 and
falling fast**:

| date | stock |
|---|---|
| 2026-07-18 | 182 |
| 2026-07-21 | 104 |
| **2026-07-25** | **69** |

That is **−62 % in 7 days** on a **single-source Extended part with no
qualified alternate**. It passes today with 8.6× headroom; at this rate it
reaches 8 in roughly two more weeks. **Re-run
`jlc_stock_check.py fab/bom.csv --min-stock 8` the same day you pay.** If the
array ever grows past ~20 boards, buy LS1 separately and consign it rather
than racing the queue.

---

## 2. ⚠️ REQUIRED before order — J1 pad-1 → contact-1 continuity backstop

The RJ45 footprint (`RJ45_Amphenol_RJHSE538X`) has been **CERTIFIED CORRECT
(not a contact mirror)** by a row-parity + chirality analysis of the Amphenol
dwg P-RJHSE-538X Rev K component-side layout, independently re-confirmed by the
fresh pin review (ADR-0003, J1 part.yaml). Because the jack's hole pattern is
mechanically mirror-symmetric, that certification rests on the manufacturer's
printed contact labels. As **defense-in-depth** (same discipline as the LED-
polarity + first-power rituals), on the FIRST assembled board **multimeter pad-1
copper (the rect pad, AUDIO+) → the physical contact-1 blade** on a real
RJHSE-5384 before committing the array. This is a one-time coupon check, NOT an
expected failure — if it mirrors, a corrected project-local footprint is needed.

---

## 3. Hand-solder parts — NOT on the assembly BOM, NOT on the CPL

Declared in `03_src/rules/assembly.yaml` (`reason: user_supplied`) and graded by
A-POP. **They are deliberately absent from `fab/bom.csv`** — do not add them
back. JLC is not asked to source or place either one.

| Ref | Part | Source | Why not assembled (measured 2026-07-25) |
|---|---|---|---|
| MK1 | AOM-5024L-HD-R electret | **Digi-Key 668-1538-ND** | In JLC's catalog as C3273706 but **stock 0**, and so are both siblings (C3273730, C20107634). Also through-hole on an SMT-only order. |
| J1 | RJHSE-5384 RJ45 jack | source separately | C9900035627 and its duplicate C9900056698 are **both stock 0** consign-only stub codes at $0.0392 — never orderable stock. The in-stock C3179625 is a **right-angle** variant, not a drop-in. Through-hole. |

> **v1.0 said MK1 was "not in the JLC catalog". That was never measured and it
> is FALSE** — the exact MPN is C3273706. The true wall is stock 0 plus
> THT-on-an-SMT-order. Corrected here and in the part dossier.

### 🔥 HAND-SOLDER THERMAL LIMITS — MK1 (BINDING)

From the AOM-5024 datasheet p.4 "Microphone Handling Precautions", **verbatim**:

> - Ensure the power rating of the soldering iron is **below 90 watts**
> - The temperature of the soldering iron must be limited to **360 °C ±10 °C** (680 °F ±50 °F)
> - Soldering duration for each terminal shall be **at or under 2 seconds**

**Exceeding these degrades capsule sensitivity SILENTLY** — no visible damage,
just a permanently quieter microphone, discovered only when the array is
calibrated. Put this in front of whoever holds the iron.
Wiring: pad 1 "+" → R2, pad 2 → GND.

### 💧 MSL 3 / MOISTURE FLOOR LIFE — LS1 (JLC's responsibility, state it on the order)

> **LS1 (C22359707, CMT-8504-100-SMT-TR) is MSL 3 with a 48-hour floor life.
> Put this in the order notes.**

LS1 **is machine-placed** (`fab/cpl.csv` row 15), so this is a constraint on
the assembler, not on us — which is exactly why it belongs in the order
paperwork. From the CMT-8504 datasheet rev 1.04 SOLDERABILITY table, **verbatim**:

> **Note 2.** It is recommended to reflow solder within **48 hours** from
> opening vacuum packaging at a temperature <30 °C & relative humidity <60 %.
>
> **Note 3.** When out of packaging for more than 48 hours → drying conditions:
> **bake at 40 °C for 24 hours**.
>
> reel storage: at relative humidity <60 %. Reflow peak **260 °C max**.

Unbounded floor time risks **popcorning/delamination of a coil transducer
sealed inside an outdoor pod** — a latent failure found after deployment, not
at test. Add a line to the order notes asking JLC to observe the 48 h floor
life / 40 °C 24 h bake for C22359707.

D2 (SS14), **D3 (SMAJ6.0A — POPULATED this rev)**, D1, U1, LS1, and all
passives ARE machine-placed by JLC (twin-verified, 26/26 bodies).

---

## 3b. ⚠️ A-POL — HUMAN ORDER-PREVIEW GATE: eyeball U1 pin-1 on JLC's preview

Every one of the 26 rotations resolves from a MEASURED per-LCSC row in the
fleet authority table (61 rows at seal; this board's 4 rows landed 2026-07-26,
commit f9eee3f), and **all 26 match what the CPL already ships** — nothing here
is a suspected error. Three of the four newly measured rows are TWO-CHANNEL
(a function-tied, numbering-free mark confirms the pad-number fit):

| Ref | LCSC | Measured | Fit | Numbering-free confirmation |
|---|---|---|---|---|
| D2 | C2480 | 0 | rms 0.0400 vs 2.8003 next | JLC silk diode GLYPH: apex + cathode bar at −x = pad-1 end; our D_SMA band also pad-1 end |
| D3 | C559105 | 0 | rms 0.1900 vs 2.9658 next | JLC cathode band line x=−1.20 + two filled cathode-end marks flanking pad 1; ours pad-1 end |
| LS1 | C22359707 | 0 | electrical pads 1/2 exact at 0 | '+' mark: JLC model `fp_text` at (−2.50,−1.00), ours at (−5.60,−3.50) — both beside their own pad 1. (JLC numbers the NC mechanical pads 3/4 opposite to ours; electrically moot.) |

One row is **SINGLE-CHANNEL**, and a single-channel row is exactly where a
pad-number fit can be *confidently* wrong (on usb-hub's LEDs the same fit
returned 180 at a 17.7× margin when the true answer was 0):

| Ref | LCSC | Measured | Fit | Why single-channel |
|---|---|---|---|---|
| **U1** | C192421 | **270** | rms 0.2351 vs 4.1820 next (17.8×) | SOIC-8 has no function-tied mark; the pin-1 dot follows numbering. Corroborated independently: cooksense's C7984 uses a byte-identical JLC land, measured 270. jlc_twin's fitted 90 is the negated-handedness signature (exactly 180 off at 90/270) and is excluded by the fit distance. |

**On JLC's order preview, confirm U1's pin-1 dot sits at the pad-1 corner of
the SOIC-8 land (CPL rotation 270).** The machine-readable form of this gate is
`verification/rotation_human_gate.txt` (regenerated at seal: names exactly
C192421/U1). D2/D3/LS1 need no eyeball — but the first-power ritual (§5 step 2)
still re-checks the diode bands for free.

(A pin-1 dot or mark FOLLOWS pad numbering, so U1's agreeing pin-1 channel
corroborates nothing a mirrored-numbered library would not also fake — that is
WHY U1 is single-channel despite two agreeing readings. The full channel
history and today's tool output: `verification/rotation_measurements.txt`.)

---

## 4. Enclosure / mechanical — OPEN dependency (confirm before order)

The RJ45 mating face sits **1.05 mm behind the PCB's own west edge** (measured).
There is **no enclosure CAD in this repo**, so plug/panel fit is UNVERIFIED.
Before ordering the enclosure (or if a panel already exists): confirm the RJ45
mouth clears the panel cutout (datasheet recommended cutout **16.89 × 13.46 mm**)
and that the 1.05 mm PCB overhang does not foul the cable boot — or notch the
board edge at the mouth. Not a PCB-order blocker; an assembly/enclosure check.

---

## 5. First-power ritual (when boards arrive)

1. **Before any power:** multimeter the RJ45 contacts against the board nets —
   confirm the custom pinout (1,2 = AUDIO±; 3,6 = 5V_BEEP/RET; 4,5 = +5V; 7,8 =
   GND) and the pad-1→contact-1 continuity (section 2).
2. Confirm D2/D3 cathode band → 5V_BEEP (pad 1), D1 orientation.
3. Apply +5 V on 4,5 / GND on 7,8 from the CENTRAL board ONLY (never a PoE
   source, section 0). Verify VMID ≈ 2.5 V at TP7, U1 V+ ≈ 5 V.
4. Inject an audio tone at the mic; confirm the balanced pair at TP3/TP4.

---

## 6. Known operating limit — U1 input common-mode ceiling (ACCEPTED, not a defect)

Recorded so the next reviewer does not rediscover it. **No action required.**

OPA1678 linear common-mode input range is **(V−)+0.5 to (V+)−2** (SBOS855E
Electrical Characteristics). With V−=GND and V+=5 V that window is
**0.500–3.000 V**. VMID = 5.000 × 22k/(22k+22k) = **2.5000 V** (R4=R5=22k), so
the **positive** headroom is only **0.500 Vpk** against 2.000 V on the negative
side — asymmetric by 4×. Input CM therefore binds **3.1× before** the output
clips (1.53 Vpk).

Onset ≈ **108.9 dB SPL** typ, **105.9** at +3 dB mic sensitivity, **103.4**
worst-case (+3 dB at V+=4.75 V) — i.e. **below the AOM-5024's own 110 dB
rating**: the mic can deliver more than U1 can linearly accept.

**Why this ships as-is:** SBOS855E §7.3.1 — the OPA167x has **internal
phase-reversal protection**, so at over-range it clips at the rail rather than
inverting. Graceful; nothing is damaged (abs-max is (V−)−0.5 to (V+)+0.5, far
away). A crow call at the pod is ~70–90 dB SPL, **15–20 dB below the ceiling**.
Effect if ever exceeded: positive peaks of the loudest close transients
compress asymmetrically, so the balanced pair briefly loses balance and
localization accuracy degrades on that event.

**If a field recording ever shows clipped POSITIVE peaks:** re-centre VMID with
R4=33k / R5=18k → 1.76 V (the output still fits). That is a next-rev change, not
a reason to hold this order. Recorded in `02_parts/OPA1678IDR/part.yaml`
(`limits.vcm_range`).

---

## 7. What changed in v1.1, and why it mattered

**The order blocker.** v1.0's `fab/bom.csv` carried 28 designators over 17 data
lines while the CPL carried 26. The two extra were **MK1** — whose MPN *and*
LCSC columns were **both empty**, so it resolved to no part number at all — and
**J1** at live stock 0. JLC was being told to source two parts it cannot source,
for two positions it is never told to place. That stalls the upload at JLC's
BOM/CPL matcher before any money is spent. Both rows are gone; the sets now
match exactly at 26/26 and every line is coded. This also closes v1.0's own render/twin **HOLD**
(`verification/render_review.md` line 44), which named **TWO** conditions:
*fix the MK1 LCSC field* **and** *give D3 an explicit DNP marker before
uploading*. Both are now closed, by different routes — D3's condition
**dissolved** when D3 was POPULATED in the v1.0 fix pass (there is no DNP state
left to mark, and D3 is machine-placed on the CPL), and MK1's is closed here by
removing the row entirely, which is strictly stronger than fixing the field.
See `verification/DISPOSITIONS.md` item AJ.

**Also corrected in the paperwork (no copper implication):**

- **Population is now DECLARED**, not emergent — `03_src/rules/assembly.yaml`
  covers all 13 unpopulated refs with closed-vocabulary reasons and dated
  evidence. The MANIFEST `not_assembled:` line is **generated** from it.
- **Stock evidence now ships** (`verification/stock_check.json`, verdict PASS
  at quantity 8). v1.0 sealed with none at all.
- **LS1's twin waiver was geometrically impossible** and is restated from a
  corrected reading, with an oriented fit (`verification/ls1_pad_correspondence.txt`).
  The shipped CPL rotation was, and remains, right.
- **`policy_audit.md` shipped corrupt** in v1.0 (a stdout line spliced into the
  table, deleting the P-TIER row); the writer is fixed and the report now
  verifies against its own table before sealing.
- **Two of four `.kicad_dru` rules cannot fire.** Real, measured, and **waived
  for this docs-only release** — fixing it means regenerating the board, which
  would make this a respin. Physical effect is nil (3 tracks 0.08 % under a
  floor that was never in force; the tier floor holds with 1.97× margin). See
  §8 and `verification/rules_audit.txt`. **Required at the next respin** — the
  rebuild now fails until it is fixed.

---

## 8. Next-rev work order (P2, non-blocking)

- **Regenerate the `.kicad_dru` so every rule can fire** (drop `AUDIO_width`
  and `pad_rescue_stubs`, or create the netclass/rule area they name).
  `03_src/rebuild_all.sh` now gates on `rules_audit.py`, so the next rebuild of
  this board FAILS until this is done. Carried as an evidence-backed waiver in
  v1.1 only.
- Route AUDIO_P/AUDIO_N as a matched pair (current ~2:1 length asym; low-Z
  outputs, immaterial at audio freq).
- (Optional) re-centre VMID (§6) only if field recordings justify it.
- (Optional) move 5V_AUDIO off the PoE-alias contacts or add a PoE-defeat
  network if the deployment ever leaves controlled infrastructure (ADR-0005).
