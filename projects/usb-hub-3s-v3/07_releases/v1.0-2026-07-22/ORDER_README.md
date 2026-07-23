# ORDER README — usb-hub-3s-v3 (internal board name `usb_hub_3s_v2`)

3S-LiPo powered 3-port USB hub: XT60 pack in → 10 A MINI-blade fuse → dual
synchronous bucks (LM5116) → 3× USB-A (5 V) + 1× Pi-dedicated USB-C (5 V/5 A).
Release **v1.0-2026-07-22**. Board **130.1 × 92.1 mm**, **4 layer**.

This board is **VERIFIED and ORDERABLE**. DRC 0/0/0, policy_audit 0 FAIL, JLC
twin exit 0, both red-team lenses ORDER (topology re-confirmed by an independent
zero-context re-review), pin + render review PASS. Evidence is in
`verification/`; provenance + per-file hashes in `MANIFEST.txt`.

---

## 1. JLCPCB order options

| Setting | Value |
|---|---|
| Layers | **4** |
| Dimensions | 130.1 × 92.1 mm |
| Via tier | **`jlc_4layer_standard`** — all 240 vias are a uniform **0.45 mm pad / 0.30 mm drill**. Min feature ≥ standard-tier floor, so the **standard 4-layer process is sufficient — do NOT select the advanced small-via option** (not needed; 0.3 mm drill is within standard). |
| Impedance control | not required |
| Surface finish | HASL or ENIG (installer's choice; ENIG preferred for the 0.4 mm-pitch parts' paste release) |

Upload set (in `fab/`):
- **PCB order:** `usb_hub_3s_v2_gerbers.zip` (13 files: F/In1/In2/B copper, F/B
  mask, F/B paste, F/B silk, Edge_Cuts, PTH + NPTH drills). BOM/CPL are **not**
  in the zip.
- **Assembly BOM:** `fab/bom.csv` (`Comment,Designator,Footprint,MPN,LCSC`).
- **Assembly CPL:** `fab/cpl.csv` (`Designator,Val,Package,Mid X,Mid Y,Layer,Rotation`
  — the JLC-upload format with rotation-DB-corrected angles; **not** the
  twin-format `verification`-style CPL).

Re-run a same-day stock check before paying (stock moves).

---

## 2. ⚠️ REQUIRED Raspberry Pi CONFIG — the USB-C port needs an EEPROM setting

**The USB-C port (J5) delivers 5 V / 5 A ONLY when the host Raspberry Pi 5 has
`PSU_MAX_CURRENT=5000` set in its bootloader EEPROM** (per ADR-0001). Without it,
the Pi negotiates the port down and **caps USB draw at ~600 mA**, and the hub's
downstream 5 A budget is never available.

```
# On the Pi 5, one-time:
sudo rpi-eeprom-config --edit      # add the line:
PSU_MAX_CURRENT=5000
# save, reboot.
```

- **This USB-C port is Pi-DEDICATED, not a generic USB-C source.** It presents a
  **non-PD 3 A-advertised source** (CC Rp resistors R28/R29) — a generic USB-C
  device or laptop plugged in sees a plain 5 V source, **not** a PD contract, and
  will not get 5 A. Only a Pi configured as above uses the full budget.
- Use a **short, 5 A-rated USB-C cable** (5 A e-marked or a short heavy-gauge
  passive cable). A thin 3 A cable throttles/​heats at 5 A.

---

## 3. HAND-SOLDER / installer-fit list (NOT on the CPL)

| Item | Part | Action |
|---|---|---|
| **F1 fuse ELEMENT** | **10 A MINI blade fuse — Littelfuse 0297010** (or equivalent fast-acting automotive MINI blade) | **The assembler drops the blade into the F1 holder.** The 10 A *element* is a consumable and is **NOT** a BOM/CPL line. |

**Assembly split for F1 (important):** the **holder** (Keystone 3568-class,
`Fuseholder_Blade_Mini_Keystone_3568`, LCSC **C5249699**) **IS** on the BOM/CPL —
JLC machine-places the holder. Only the **replaceable 10 A blade element** is
hand-fitted. Fitting the correct blade is safety-critical: the board silk reads
`FUSE 10A MINI`; **do not** fit a 20 A blade (the prior stale spec — RT-T1, now
corrected: 10 A = 1.47× the 6.8 A worst-case trunk, independently re-confirmed).

*(No THT connectors are hand-solder on this board — XT60 (J1), USB-A (J2/J3/J4),
and USB-C (J5) are all on the CPL and were JLC-twin verified.)*

---

## 4. ROTATION / POLARITY preview checklist (JLC 3D preview, before paying)

All four classes below are twin-adjudicated (`verification/twin_adjudications.yaml`,
twin exit 0) — the JLC order-preview is the final confirm step. **SMD preview
rotation is exactly what the machine does — fix it in the preview, don't
rationalize it.**

1. **AON PowerPAK SO-8 FETs (Q1–Q5, merged-drain pad-5)** — the merged drain pad
   is a single wide finger vs JLC's split fingers; confirm the body sits square
   on the pads at the CPL rotation (Q1/Q2/Q4 → 90°, Q3/Q5 → 270°). This is the
   one that dead-boards if mirror-numbered — eyeball pin-1/source orientation.
2. **MWSA1206S inductors (L1, L2)** — Sunlord MWSA1206S; 3D model may render as
   empty space (cosmetic, part still mounts). Confirm footprint outline + that
   they're placed, not the height.
3. **Diodes D1 / D2 / D3 / D4 — polarity** — confirm cathode band vs the JLC
   model's pin-1 marker matches board silk. Diode reel orientations vary per
   part and are NOT in the rotation DB.
4. **Electrolytics C1 / C2 — polarity** — CP_Elec_6.3×7.7 (C2982822), CPL
   rotation 270°. Confirm the polymer-can polarity mark / base bevel = the
   positive (VIN) side against board silk.

---

## 5. NEXT-REV work order (all P2 — non-blocking, recorded, do NOT gate v1.0)

Fold these into the next revision; none blocks this order.

| ID | Finding | Next-rev action |
|---|---|---|
| **F-2.1** | LM5116 UVLO turns on at **≈ 9.65 V rising / 8.84 V falling**, above the BRIEF's 9.0 V nominal floor. **User decision: SEAL AS-IS** — cold-start from a 9.0–9.65 V pack is **not a requirement**, and the elevated UVLO **doubles as LiPo deep-discharge protection**. | Optional: amend the spec to state the 9.65 V cold-start floor, or lower the UVLO divider if 9.0 V cold-start ever becomes firm. |
| **RT-T2** | Buck **input ceramics are 25 V**, resting on the 24.4 V corner of the SMBJ15A TVS clamp — thin margin. | Move input ceramics to **50 V**. |
| **RT-T5** | Output **ceramics are 6.3 V on the 5 V rail** — X5R/X7R DC-bias derating eats real capacitance at 5 V. | Move output ceramics to **10 V / 16 V**. |
| **RT-T4** | USB-C VBUS has **no port-local current limit / reverse blocking**. The re-review notes a *powered* source mis-plugged into the USB-C **output** can back-feed VIN through the sync buck. | Fit the **optional USB-C VBUS e-fuse with reverse-blocking** if a non-Pi / back-feed source risk exists in the deployment. |
| **AON6354 hygiene** | `02_parts/AON6354/part.yaml` carries **stale IP6559 / snubber / "7-pcs" text** (also the misleading 2100 µF-vs-actual-100 µF bulk-cap MPN string). Data-only; **does not affect the board**. | Clean the part.yaml text next rev. |
| **Layout L-3/L-4** | Thermal / power-integrity headroom. | Add **≥ 4× 0.3 mm via arrays under BOTH LM5116 EPs**, and a **B.Cu VBAT_F pour**. |

---

## 6. FIRST-POWER ritual (when boards arrive — before any real pack)

1. **Continuity/polarity first, no power:** multimeter the XT60 (J1) blades vs
   board nets — VIN to the F1 holder input, GND continuity. Thirty seconds of
   beeping catches a polarity bug that every upstream check is blind to.
2. **Fit the 10 A blade** into F1 (see §3). Confirm silk reads `FUSE 10A MINI`.
3. **Current-limited bench supply**, set ~9–12.6 V, current limit ~0.5 A first.
   Power up. **Watch for smoke / heat; no rail should pull the limiter to 0 V.**
4. **Check the rails:** measure **5VA** (USB-A rail) and **5VC** (USB-C rail) —
   both should come up to ~5 V. If a rail is dead or the supply current-limits,
   kill power and inspect before raising the limit.
5. Raise the limit toward load only once both rails are clean at 5 V.

---

## Provenance

- git_sha in `MANIFEST.txt` (exact commit); `git_dirty: false`.
- KiCad 10.0.4. Authoring source: tscircuit `source/usb_hub_3s_v2.tsx`
  (ADR-0002). Standalone re-measure: `kicad-cli pcb drc
  source/usb_hub_3s_v2.kicad_pcb` → 0/0/0 (fp-lib-table + vendored
  `usb_hub_3s.pretty` ship in `source/`).
