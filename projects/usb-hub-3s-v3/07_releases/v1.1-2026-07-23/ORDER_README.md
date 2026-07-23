# ORDER README — usb-hub-3s-v3 **v1.1** (internal board name `usb_hub_3s_v2`)

> DRAFT for the v1.1 seal (staged in `06_build/verification/`). At seal time this
> moves to the release root `07_releases/v1.1-2026-07-23/ORDER_README.md`.

3S-LiPo powered power-distribution board: XT60 pack in -> 10 A MINI-blade fuse ->
dual synchronous bucks (LM5116) -> 3x USB-A (5 V charging, no-data) + 1x
Pi-dedicated USB-C (5 V/5 A, **eFuse-protected**). **NOT a USB hub, NOT USB-PD.**
Release **v1.1-2026-07-23**. Board **130.1 x 92.1 mm**, **4 layer**, **115 parts**.

**v1.1 supersedes v1.0-2026-07-22** — adds the protected-VBUS eFuse cell,
sense-at-connector 5.151 V setpoint, a master-off switch, and 50 V/10 V caps
(external-review fixes; see §5 and `08_reviews/2026-07-23_v1.1_fix_confirmation.md`).

Gates at this draft: DRC **0/0/0** (incl. schematic-parity 0), policy_audit **0
FAIL**, E-INV 16/16, JLC twin **exit 0** (88 OK/232), pin + render review PASS.

---

## 1. JLCPCB order options
| Setting | Value |
|---|---|
| Layers | **4** |
| Dimensions | 130.1 x 92.1 mm |
| Via tier | **`jlc_4layer_standard`** — uniform 0.45 mm pad / 0.30 mm drill. **Standard process is sufficient — do NOT select the advanced small-via option.** |
| Impedance | not required |
| Finish | HASL or ENIG (ENIG preferred for the 0.4 mm-pitch parts) |

Upload set (in `fab/`): `usb_hub_3s_v2_gerbers.zip` (13 files) -> PCB order;
`bom.csv` + `cpl.csv` -> assembly. Re-run a same-day stock check before paying.

---

## 2. PRE-ORDER items (v1.1)
1. **SW-node snubbers R34/R35/C53/C54 = DNP-by-design (bench-tune footprints).**
   These are OPTIONAL SW-node RC snubbers (2.2 ohm 1206 + 1 nF C0G 0805), fitted
   ONLY if a bench scope shows switch-node ringing (R ~= sqrt(Lpar/Cpar) tune).
   **They are REMOVED from `fab/bom.csv` + `fab/cpl.csv` at this seal — JLC does
   NOT populate them.** Their **pads remain in the gerbers** (unpopulated), so
   they can be hand-fitted during bring-up if ringing is observed. (The source
   states this intent in comments but did not set `doNotPopulate`; encoding it in
   the tsx is a next-rev item, §8. If you WANT them populated, re-add the 4 refs:
   R34/R35 = C137327 (2.2 ohm), C53/C54 = C62774 (1 nF).)
2. **SW1 (SS12D07VG6) pin pitch — MANDATORY order-preview confirm.** Our footprint
   is **2.5 mm** (standard SS-12D07,
   8.7 mm body + end mounting posts). JLC's assembly 3D model is the mislabeled
   **VG4** variant (2.0 mm). **Confirm the VG6 pitch on the JLC order preview /
   the C2939728 datasheet drawing.** If it is 2.0 mm, use the jumper fallback
   (2.54 mm header + shunt across ENKILL<->GND). Hand-solder mechanical part.
3. **eFuse divider LCSC codes** (assigned this draft, 1% 0603): R30 3.09k=C22992,
   R31 47.5k=C23061, R32 12.1k=C22864, R36 150k=C22807. Confirm value/tol at order.
4. **Low-stock at order:** U13 TPS26631 (C2866319) stock ~112, U6/U7 (C473910) ~75
   — re-check same-day; U13 fallbacks TPS26633/35PWPR (pin-compatible, pin8=PLIM).

---

## 3. REQUIRED Raspberry Pi CONFIG — USB-C 5 A needs an EEPROM setting
**J5 delivers 5 V / 5 A only with `PSU_MAX_CURRENT=5000` in the Pi 5 bootloader
EEPROM** (ADR-0001). Without it the Pi caps USB draw at ~600 mA.
```
sudo rpi-eeprom-config --edit    # add:  PSU_MAX_CURRENT=5000  ; save; reboot
```
- **Pi-DEDICATED, non-PD.** CC Rp resistors (R28/R29) advertise a plain 5 V source;
  a generic USB-C device/laptop sees no PD contract and will not draw 5 A.
- The rail is now **eFuse-protected** (see §6) and regulated **at the connector to
  5.151 V** (>=5.0 V worst-low), so the Pi sees a clean 5 V under the full 5 A.
- Use a **short, 5 A-rated USB-C cable**.

---

## 4. HAND-SOLDER / installer-fit list (NOT on the CPL)
| Item | Part | Action |
|---|---|---|
| **F1 fuse ELEMENT** | **10 A MINI blade — Littelfuse 0297010** (or equiv. fast-acting automotive MINI) | Assembler drops the blade into the F1 holder. The 10 A element is a consumable, **not** a BOM/CPL line. |

The **holder** (Keystone 3568-class, LCSC **C5249699**) IS on the BOM/CPL. Silk
reads `FUSE 10A MINI` — **do not** fit a 20 A blade (10 A = 1.47x the 6.8 A trunk).
XT60/USB-A/USB-C are all on the CPL (twin-verified). SW1 is machine-place-able
but see §2.2 (pitch) — hand-solder is the safe default for this slide switch.

---

## 5. FIXED in v1.1 (external-review resolutions — no longer next-rev)
| Was | v1.1 fix | Proof |
|---|---|---|
| Blocker-2: USB-C 4.97 V too low | FB senses **VBUSC** (post-eFuse), R12=3.92k -> **5.151 V at connector** | E-MARGIN PASS (521 mV vs Pi 4.63 V) |
| RT-T4: no USB-C current-limit / reverse-block | **TPS26631 eFuse** + Q6/Q7 reverse-block; **5.83 A ILIM**, **5.91 V OVP** | E-INV 16/16; twin U13 fit 0.01 mm |
| self-drain in storage | **master-off SW1** grounds both LM5116 EN | E-OFF PASS (270 uA) |
| RT-T2: 25 V input caps vs 24.4 V clamp | input MLCC **50 V** (C77102) | BOM |
| RT-T5: 6.3 V output caps on 5 V | output MLCC **10 V** (C84455) | BOM |
| RT-T6: invariants file absent | `electrical_invariants.yaml` emitted | E-INV PASS |

New part vs v1.0: **BSS138 (Q7)** = the eFuse's fast gate-pulldown FET (the TI
"Q2", SLVSE94G 8.3.5) — required with Q6 for true reverse blocking.

---

## 6. ROTATION / POLARITY preview checklist (JLC 3D preview, before paying)
Twin-adjudicated (`source/twin_adjudications.yaml`, twin exit 0); the preview is
the final confirm. **SMD preview rotation is what the machine does.**
1. **AON PowerPAK SO-8 FETs Q1-Q6** (merged-drain pad-5, includes the new eFuse
   block-FET **Q6**) — body square on pads; eyeball pin-1/source (dead-boards if
   mirror-numbered). Q1/Q2/Q4 -> 90°, Q3/Q5/Q6 -> 270°.
2. **U13 eFuse (HTSSOP-20 + EP)** — same land family as U2/U11 (LM5116); confirm
   pin-1 + EP paste; CPL rot 90° (ROT-DB suggestion, verify in preview).
3. **Q7 BSS138 (SOT-23)** — confirm G/S/D orientation (twin fit 0.08 mm, CPL 270°).
4. **SW1 slide** — see §2.2 (pitch); confirm body seats on the 3 holes.
5. **Diodes D1-D4, electrolytics C1/C2 — polarity** — cathode band / can bevel vs
   silk (P-POL machine-verified; preview is the eyeball confirm).
6. **Inductors L1/L2** (Sunlord MWSA1206S) — model may render empty (cosmetic).

---

## 7. BENCH bring-up items (v1.1 — analysis-clean, confirm on hardware)
- **Loop stability with the eFuse in-loop:** analysis puts the eFuse+Q6 pole
  (~234 kHz) far above the ~20 kHz crossover, so the Type-II comp is undisturbed —
  **confirm with a Bode plot at 5 A** across the sense-at-connector loop.
- **OVP no-false-trip at 5 A:** 5VC floats to ~5.32-5.39 V @5 A vs the 5.91 V OVP
  trip (~0.5 V margin) — **confirm OVP does not chatter at 5 A hot.**

---

## 8. NEXT-REV work order (P2, non-blocking)
- **F-2.1** LM5116 UVLO ~9.65 V cold-start > 9.0 V — SEAL AS-IS (doubles as LiPo
  deep-discharge protection); spec/silk "9-12.6 V".
- **AON6354 part.yaml hygiene** — stale IP6559/snubber text (data-only).
- **LM5116 EP via-arrays** (>=4x 0.3 mm under both EPs) + **B.Cu VBAT_F pour**.
- Encode the snubber **DNP** intent in source (`doNotPopulate`) so it stops
  reaching the BOM as populated (see §2.1).

---

## 9. FIRST-POWER ritual (when boards arrive — before any real pack)
1. **No power:** multimeter XT60 (J1) blades vs board nets (VIN->F1 input, GND).
2. **Fit the 10 A blade** (F1); confirm silk `FUSE 10A MINI`.
3. **Confirm the master-off:** with SW1 to the OFF (T1/GND) position, both bucks
   stay down (no 5VA/5VC); flip ON to enable.
4. **Current-limited supply** ~9-12.6 V, limit ~0.5 A; power up; watch for heat.
5. **Rails:** 5VA and 5VC ~5 V; USB-C VBUSC (post-eFuse) ~5.15 V no-load.
6. Raise the limit toward load only once both rails are clean.

---

## Provenance
git_sha in `MANIFEST.txt`; KiCad 10.0.4; tscircuit source `source/usb_hub_3s_v2.tsx`
(ADR-0002). Standalone re-measure `kicad-cli pcb drc source/usb_hub_3s_v2.kicad_pcb`
-> 0/0/0 at seal.
