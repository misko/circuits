# ORDER README — crow-mic-pod-v2 (remote microphone POD, board a)

Cable-powered remote acoustic node for the CROW ACOUSTIC LOCALIZATION ARRAY.
One Cat5e home-run from the CENTRAL recorder powers, references and (for
calibration) drives it: AOM-5024 electret (MK1) → OPA1678 active-balanced
driver (U1, ~3 V/V diff) → TPD2E2U06 ESD (D1) → RJ45 (J1). CMT-8504
calibration transducer (LS1) + SS14/SMAJ6.0A clamps in an isolated beep loop.
Release **v1.0-2026-07-23**. Board **80 × 45 mm, 2 layer**.

This board is **VERIFIED and ORDERABLE**. DRC 0/0/0, policy_audit 0 FAIL, JLC
twin exit 0, fresh 4-lens red-team ORDER/SHIP (topology ORDER, layout ORDER,
pin 7-PASS, render/twin SHIP — no P0/P1). Evidence in `verification/`; per-file
hashes + provenance in `MANIFEST.txt`.

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
| Dimensions | **80 × 45 mm** |
| Via tier | **`jlc_2layer_default`** — 0.6 mm pad / 0.3 mm drill vias; 0.127 mm track/space floor. **Standard 2-layer process; do NOT select the advanced small-via option** (not needed). |
| Impedance control | not required |
| Surface finish | HASL or ENIG (ENIG preferred for the SOT-553 D1 paste release) |

Upload set (in `fab/`):
- **PCB order:** `crow_mic_pod_v2_gerbers.zip` (F/B copper, F/B mask, F/B paste,
  F/B silk, Edge_Cuts, PTH + NPTH drills). BOM/CPL are **not** in the zip.
- **Assembly BOM:** `fab/bom.csv` (`Comment,Designator,Footprint,MPN,LCSC`).
- **Assembly CPL:** `fab/cpl.csv` (`Designator,Val,Package,Mid X,Mid Y,Layer,Rotation`
  — JLC-upload format, rotation-DB-corrected).

Re-run a same-day stock check before paying — CMT-8504 (C22359707), OPA1678
(C192421), TPD2E2U06 (C1972959), SMAJ6.0A **D3 (C559105, extended tier)**.
Stock moves.

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

## 3. Hand-solder parts (NOT JLC-assembled — off-CPL, in BOM for reference)

| Ref | Part | Source | Note |
|---|---|---|---|
| MK1 | AOM-5024L-HD-R electret | Digi-Key **668-1538-ND** | not in JLC catalog; hand-wire (pad1 "+" → R2, pad2 → GND) |
| J1 | RJHSE-5384 RJ45 jack | LCSC **C9900035627** (consign only, stock 0) | hand-solder; consign or source separately |

D2 (SS14), **D3 (SMAJ6.0A — POPULATED this rev)**, D1, U1, LS1, and all passives
ARE machine-placed by JLC (twin-verified). D3 was DNP in the release candidate;
it is now a populated redundant beep-loop over-clamp (ADR-0001 D5) — this
resolves the earlier BOM-without-CPL assembly-file defect.

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

## 6. Next-rev work order (P2, non-blocking)

- Route AUDIO_P/AUDIO_N as a matched pair (current ~2:1 length asym; low-Z
  outputs, immaterial at audio freq).
- (Optional) move 5V_AUDIO off the PoE-alias contacts or add a PoE-defeat
  network if the deployment ever leaves controlled infrastructure (ADR-0005).
