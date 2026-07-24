# ORDER README — usb-hub-3s-v3 **v1.4** (internal board name `usb_hub_3s_v2`)

3S-LiPo powered power-distribution board: XT60 pack in -> 10 A MINI-blade fuse ->
dual synchronous bucks (LM5116) -> 3x USB-A (5 V charging, no-data) + 1x
Pi-dedicated USB-C (5 V/5 A, **discrete-protected**). **NOT a USB hub, NOT USB-PD.**
Release **v1.4-2026-07-23**. Board **130.1 x 92.1 mm**, **4 layer**, **110 parts**.

**v1.4 is a DOCS-ONLY supersede of v1.3-2026-07-23.** The board, BOM, CPL,
gerbers, source and PDFs are **byte-identical** to sealed v1.3 (sha256-verified
in the MANIFEST) — the copper and part selection are electrically correct
(R12/D5/R30 all fixed and verified in v1.3). What v1.4 corrects, driven by a
post-seal external review (08_reviews/2026-07-23_v1.3_external-user_full.md,
dispositions EXT13-1..8):
- **SW1 fallback-header shunt polarity was REVERSED** in the v1.3 README
  (said "shunted = ON"). Correct: **COM-T1 shunted = OFF; shunt removed = ON.**
- **F1 was misdescribed** as "KH-AF90DIP-112" (that is the USB-A connector
  family). F1 is the **Keystone 3568 MINI-blade fuse holder, C5249699**.
- **The rail worst-case math omitted the divider-bottom ±1 % tolerance**
  (R13/R4 = C5126242, FRC0603F1211TS, 1.21 k **±1 %**). The tolerance-inclusive
  table below replaces the Vref-only numbers. Conclusion unchanged: PASS.
- **Hand-solder packaging note**: F1/SW1 are on the BOM but off the CPL —
  expect 2 unmatched designators at JLC upload (instructions below).
- **Bench qualification criteria tightened** (adopted from the review).

Order from THIS directory. v1.3 carries a SUPERSEDED.md pointing here.

---

## ⚠️ DEPLOYMENT GATE — REQUIRED PRE-PI-CONNECTION BENCH QUALIFICATION

**Do not connect a Pi until ALL of these pass.** This is a documented deployment
gate (same contract as pod-v2's continuity check). The board is a supervised
prototype whose over-voltage protection is SECONDARY/best-effort (ADR-0002): these
tests are what stands between an assembly/derivation error and the Pi.

| # | Test | Pass criterion | Reject / action |
|---|---|---|---|
| **Q0** | **Visual + ohmmeter check of R12 AND R30 BEFORE first power.** R12: 0603 next to U11 (buck-C FB-top). R30: 0603 at Q6/Q7 (Q6 gate pull-up to PMID). | R12 reads **~4.12 kΩ** (in-circuit ≥ ~3.4 k due to the R13 path is investigable; a clean 4.1 k read passes). R30 reads **~100 kΩ** (in-circuit lower is investigable; a clean ~100 k read passes). | **REJECT if R12 reads ~3.74 kΩ** (v1.2 wrong-part C2933210 — 5VC would regulate ~4.97 V). **REJECT if R30 reads ~3.09 kΩ** (v1.2 wrong-part C2933195). Rework before proceeding. |
| **Q1** | **No-load static rails.** Measure 5VA, 5VC and VBUSC at ZERO load before connecting anything. | 5VC within **5.23-5.48 V** (tolerance-inclusive static range, table below); **VBUSC no-load ≤ 5.45 V FIRM CEILING**; 5VA within 5.03-5.28 V. | VBUSC above 5.45 V no-load: stop — measure R12/R13 and the FB node before any load testing. |
| **Q2** | **8-24 h at max load on an ELECTRONIC LOAD** — 5 A on USB-C (VBUSC) + 6 A total on the USB-A ports, NOT the Pi | **VBUSC at the board ≥ 5.00 V at 5 A** (tightened from 4.9x — the tolerance-inclusive low corner supports it), stable, no F2 nuisance trip, no thermal runaway | Any trip/droop/drift: diagnose before any Pi contact. |
| **Q3** | **Scope BOTH switch nodes (SW_A, SW_C) at Vin = 12.6 V** during startup, shutdown (SW1), abrupt load steps (0→5 A→0), **and CAPTURE VBUSC during a 5 A→0 A load release** | Ringing within FET ratings, clean monotonic soft-start; **load-release overshoot on VBUSC ≤ 5.45 V** (same firm ceiling as no-load) | Overshoot reaching the ceiling: stop; snubber/compensation rework. |
| **Q4** | **Thermal soak at the hottest expected ambient** at full load (IR camera or thermocouples: L1/L2, Q2-Q5, U2/U11, F2) | Steady-state temps in rating with margin; F2 below trip-derate at 5 A | Overheating: derate the load spec or rework before deployment. |
| **Q5** | **Verify VBUSC at the END of the actual USB-C cable** (the very cable that will feed the Pi), at 5 A electronic load, thermally settled (hot) | **≥ 4.80-4.85 V at the cable end, hot** (tightened from 4.75 V; Pi UV supervisor trips ~4.63 V ±5 % — margin required); no undervoltage events during fast load transitions | Below: use a shorter/better 5 A cable, or apply the documented R12 4.12k→4.22k mitigation (power_tree.yaml) and re-derive. |
| **Q6** | **SW1 / fallback-header logic by CONTINUITY METER before power, then functionally.** | Continuity COM-T1 (shunt fitted / slide to T1) = ENKILL-to-GND = **both bucks OFF**; open = ON. Functional: with the shunt fitted the rails stay dead; remove it and the rails come up. | Any inversion vs this table: re-check the fitted part orientation against the land before power. |
| **Q7** | **Pi stress test (final, after Q0-Q6):** monitor **`vcgencmd get_throttled`** continuously through the full stress run | `get_throttled` = 0x0 throughout (no under-voltage bit 0, no throttling) | Any UV/throttle flag: capture VBUSC at the Pi end under the failing load; revisit cable/setpoint per Q5. |

Only after Q0-Q7 pass may a Pi be connected — and it should be a **replaceable** Pi
(supervised-prototype context, BRIEF A3/D3). Escalation boundary (verbatim): "add
active OVP if the system becomes unattended, hard-access, carries valuable storage,
or powers expensive SDR".

---

## ⚠️ TOLERANCE-INCLUSIVE WORST-CASE RAIL TABLE (replaces the v1.3 Vref-only numbers)

The v1.3 math applied only the LM5116 Vref ±1.5 % (giving 5VC 5.272-5.432 V).
The divider-bottom resistors R13 and R4 are **C5126242 = FRC0603F1211TS =
1.21 kΩ ±1 %** (ledger-decoded: the FRC0603**F** series is 1 %), and that
tolerance belongs in the corners. Full derivation, Vout = Vref × (1 + Rtop/Rbot):

| Rail | Divider | Nominal | Worst-case MIN | Worst-case MAX |
|---|---|---|---|---|
| **5VC** (buck-C, feeds USB-C) | R12 4.12 k **±0.1 %** (C2984354) / R13 1.21 k **±1 %** (C5126242), Vref 1.215 V **±1.5 %** | **5.352 V** = 1.215×(1+4.12/1.21) | **5.227 V** = 1.215×0.985 × (1 + 4.12×0.999 / 1.21×1.01) | **5.479 V** = 1.215×1.015 × (1 + 4.12×1.001 / 1.21×0.99) |
| **5VA** (buck-A, feeds 3x USB-A) | R3 3.92 k **±0.1 %** (C728591) / R4 1.21 k **±1 %** (C5126242), Vref ±1.5 % | **5.151 V** | **5.032 V** | **5.273 V** |

**Low corner (undervoltage) — still PASS:** 5VC min 5.227 V − Pi UV threshold
4.63 V = **597 mV** headroom vs the modeled 5 A IR budget of **440 mV**
(88 mΩ path: Q6 4.3 + F2 18 cold/31 hot + board 3 + conn 5 + cable 45) —
**157 mV slack**. Worst-case cable-end estimate 5.227 − 0.44 = **4.79 V**,
above the Pi's 4.63 V ±5 % UV trip. Thinner than the v1.3-claimed 640 mV
(which was the Vref-only corner) — hence the tightened Q2/Q5 bench criteria
above: the cable-end measurement is the gate, not this table.

**High corner (no-load static):** 5VC can statically reach **5.479 V** at the
receptacle before transient overshoot — do NOT accept this on paper; gate Q1
measures the real no-load output against the **5.45 V firm ceiling**, and Q3
captures load-release overshoot. **USB-A note:** the 5VA top corner **5.273 V
slightly exceeds the intended 5.25 V USB-A ceiling** (R4 is the same ±1 % part).
Acceptable for the no-data charging ports this board serves; a next-rev option
is 0.1 % parts for R13/R4 (static ranges tighten to ≈5.264-5.441 V on 5VC),
recorded in DISPOSITIONS EXT13-3 — not required, margins pass as-built.

---

## ⚠️ MANDATORY ORDER-DAY STOCK RECHECK (three Extended-tier parts)

Re-run `jlc_stock_check` on order day and confirm BEFORE placing the order:

| Ref | Function | LCSC | MPN | Confirm | Fallback |
|---|---|---|---|---|---|
| **R12** | buck-C FB-top 4.12 k 0.1 % | **C2984354** | AR03BTCX4121 (0603) | **4.12 kΩ ±0.1 %** + in stock (15 353 on 2026-07-23). **NEVER C2933210 (3.74 k).** | **C861436** (Yageo RT0603BRD074K12L, same 4.12 k/0.1 %/25 ppm, verified). If both OOS: any 1 % 4.12 k 0603 (≈30 mV worse corner) — never 3.92 k / 3.74 k. |
| **F2** | VBUS over-current PPTC | **C6165170** | SMD2920-700/16N (2920) | **7 A hold + 16 V Vmax + 18 mΩ R1max** (catalog-confirmed 2026-07-23, stock 3 329). 7 A (not 6 A): a 6 A hold derates to ~4.8 A @50 °C < the 5 A continuous load. | **C3762416** (Littelfuse 2920L600/16MR-A, 6 A/16 V) — nuisance-trips at 5 A @50 °C (**degraded**; user decision required). |
| **D5** | VBUS over-voltage TVS | **C113976** | SMBJ6.0A (SMB/DO-214AA) | **UNIDIRECTIONAL** in the JLC description + Vwm 6.0 V + in stock (74 758 on 2026-07-23). | **C83270** (SMBJ6.0A uni-dir alt). **NEVER C140903** (JLC lists it BIDIRECTIONAL). |

All other LCSC codes are library-standard / previously-shipped and pass M-BOM.

---

## 1. JLCPCB order options
| Setting | Value |
|---|---|
| Layers | **4** |
| Dimensions | 130.1 x 92.1 mm |
| Via tier | **`jlc_4layer_standard`** — 0.45 mm pad / 0.30 mm drill. Standard process is sufficient — do NOT select the advanced small-via option. |
| Assembly | BOM `fab/bom.csv` + CPL `fab/cpl.csv` (JLC-upload format, per-refdes LCSC keyed off circuit.json; built from 06_build/fab/{bom_jlc,cpl_jlc}.csv). Hand-solder list below. |

**EXPECT 2 UNMATCHED DESIGNATORS AT UPLOAD — this is intentional.** `fab/bom.csv`
carries **F1** (C5249699) and **SW1** (C2939728) but `fab/cpl.csv` deliberately
omits both (hand-solder, `FP_EXCLUDE_FROM_POS_FILES` at source). In the JLC
order review, **mark F1 and SW1 as DNP / "do not place"** when the interface
flags them — do NOT let JLC "helpfully" add placement data for either. The
codes stay on the BOM so the parts arrive with the order for hand fitting.

## 2. Hand-solder / off-CPL list + purchasing
| Ref | Part | Why off-CPL |
|---|---|---|
| **F1** | **Keystone 3568 MINI-blade fuse HOLDER (C5249699)** | THT, no JLC placement model (as in v1.1/v1.2). *(The v1.3 README misnamed this "KH-AF90DIP-112" — that is the USB-A connector family.)* |
| **SW1** | SS12D07 master-off slide (C2939728) | **Removed from automated assembly (v1.3)** — the SS12D07 **VG4-vs-VG6 pin-pitch variant is not physically confirmed** against the board's vendored land. Hand-solder after verifying the received part's pitch against the pads. **Fallback if the pitch is wrong:** fit a 2.54 mm 3-pin header + shunt on the same land — **COM-T1 shunted = OFF; shunt removed = ON** (COM = pin 2 = ENKILL, T1 = pin 1 = GND; shunting grounds ENKILL, which shuts BOTH bucks down and opens Q6 — *the v1.3 README had this REVERSED*). Verify by continuity per gate Q6; the switch can be fitted on a later revision. |

**Hand-fit purchasing list (NOT in the JLC order):**
- 1x **10 A MINI (ATM) blade fuse** — the consumable element for F1
  (deliberately off-BOM; buy locally, keep spares).
- (fallback only) 1x 2.54 mm 3-pin header + 1x shunt/jumper for the SW1 land.

## 3. Required Pi setting (ADR-0001)
The USB-C port is a **plain 5 V/5 A rail, NOT USB-PD**. The Pi MUST draw 5 A
without PD: set **`PSU_MAX_CURRENT=5000`** in the bootloader EEPROM (or
`usb_max_current_enable=1` in `config.txt`). Without it the Pi caps downstream USB
at 600 mA (still boots). A generic USB-C device sees a non-PD 3 A-advertised source.

## 4. Cable note
Use a short (0.3-0.5 m), **5 A-rated USB-C cable** for the Pi (no PD → no e-marker
enforcement; the E-MARGIN derivation budgets ~45 mΩ for it — verify with gate Q5).

## 5. Protection behavior (discrete SECONDARY protection — ADR-0002, HONEST)
- **Over-current:** F2 PPTC trips on a short/overload (resettable).
- **Over-voltage — SECONDARY / best-effort:** on a buck-fail-high, D5 clamps
  (~10.3 V @Ipp, above the Pi ceiling) and F2 must trip to end the exposure — a
  **crowbar, not a deterministic cutoff. NOT guaranteed against a buck high-side
  short.** Accepted for a supervised prototype with a replaceable Pi (BRIEF A3/D3).
- **Reverse-current / master-off:** Q6 (P-FET) is held OFF when the hub is switched
  off (SW1/ENKILL → Q7 opens Q6) → its body diode blocks a powered device on the
  port from back-feeding the pack. Reverse current is NOT instantaneously blocked
  while the port is actively ON (bounded by F2) — accepted for a Pi-dedicated sink.
- **Protected against:** shorts, overload, reverse-feed with the port off.
  **NOT guaranteed against:** a buck high-side short (fail-high). Escalation
  boundary (verbatim): "add active OVP if the system becomes unattended,
  hard-access, carries valuable storage, or powers expensive SDR".

## 6. Notes carried from v1.1/v1.2/v1.3
- RT-T3: LM5116 UVLO ~9.65 V cold-start > 9.0 V nominal — accepted P2 (doubles as
  LiPo deep-discharge protection); spec/silk read "9-12.6 V".
- Master-off SW1 kills both bucks + opens Q6 (~270 µA storage draw, power_tree E-OFF).
- First-power ritual (before ANY power): multimeter the XT60 blades against the
  board nets (polarity + continuity through F1/Q1) — 30 seconds of beeping beats
  every upstream analysis.
- v1.3's electrical fixes (all carried, board unchanged): R12 = catalog-verified
  4.12 k 0.1 % C2984354 (never C2933210 = 3.74 k); D5 = catalog-UNIDIRECTIONAL
  SMBJ6.0A C113976 (never C140903 = bidirectional); R30 = ledger-verified 100 k
  C25803 (never C2933195 = 3.09 k).
