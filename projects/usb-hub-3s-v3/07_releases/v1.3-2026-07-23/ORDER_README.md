# ORDER README — usb-hub-3s-v3 **v1.3** (internal board name `usb_hub_3s_v2`)

3S-LiPo powered power-distribution board: XT60 pack in -> 10 A MINI-blade fuse ->
dual synchronous bucks (LM5116) -> 3x USB-A (5 V charging, no-data) + 1x
Pi-dedicated USB-C (5 V/5 A, **discrete-protected**). **NOT a USB hub, NOT USB-PD.**
Release **v1.3-2026-07-23**. Board **130.1 x 92.1 mm**, **4 layer**, **110 parts**.

**v1.3 supersedes v1.2-2026-07-23 (DO-NOT-ORDER — see its SUPERSEDED.md).** v1.3
fixes the externally-found blockers:
- **R12** now the CATALOG-VERIFIED 4.12 kΩ 0.1 % **C2984354** (AR03BTCX4121), code
  BAKED into the source (v1.2's BOM resolved R12 to C2933210 = **3.74 kΩ**, an
  undervoltage order-blocker).
- **D5** now the catalog-confirmed **UNIDIRECTIONAL** SMBJ6.0A **C113976**
  (v1.2's C140903 is listed bidirectional by JLC).
- Buck-C setpoint re-derived against the real Q6+F2 delivery path (E-MARGIN PASS);
  all release artifacts regenerated fresh from v1.3 source.

---

## ⚠️ DEPLOYMENT GATE — REQUIRED PRE-PI-CONNECTION BENCH QUALIFICATION

**Do not connect a Pi until ALL of these pass.** This is a documented deployment
gate (same contract as pod-v2's continuity check). The board is a supervised
prototype whose over-voltage protection is SECONDARY/best-effort (ADR-0002): these
tests are what stands between an assembly/derivation error and the Pi.

| # | Test | Pass criterion | Reject / action |
|---|---|---|---|
| **Q1** | **Measure the assembled R12 BEFORE first power** (0603 next to U11, buck-C FB-top; meter across it in-circuit or lifted) | **~4.12 kΩ** (in-circuit reading ≥ ~3.4 k due to R13 divider path is investigable; a clean 4.1 k read passes) | **REJECT the board if it reads ~3.74 kΩ** — that is the v1.2 wrong-part bug (C2933210); 5VC would regulate at ~4.97 V. Rework R12 before proceeding. |
| **Q2** | **8-24 h at max load on an ELECTRONIC LOAD** — 5 A on USB-C (VBUSC) + 6 A total on the USB-A ports, NOT the Pi | Voltage stable (VBUSC ≥ 5.0 V at the board), no F2 nuisance trip, no thermal runaway | Any trip/droop/drift: diagnose before any Pi contact. |
| **Q3** | **Scope BOTH switch nodes (SW_A, SW_C) at Vin = 12.6 V** during startup, shutdown (SW1), and abrupt load steps (0→5 A→0) | Ringing within FET ratings, no sustained overshoot on 5VA/5VC, clean monotonic soft-start | Overshoot reaching the 5 V rails: stop; snubber/compensation rework. |
| **Q4** | **Thermal soak at the hottest expected ambient** at full load (IR camera or thermocouples: L1/L2, Q2-Q5, U2/U11, F2) | Steady-state temps in rating with margin; F2 below trip-derate at 5 A | Overheating: derate the load spec or rework before deployment. |
| **Q5** | **Verify VBUSC at the END of the actual USB-C cable** (the very cable that will feed the Pi), at 5 A electronic load | **≥ 4.75 V at the cable end** (Pi UV supervisor trips ~4.63 V; margin required) | Below: use a shorter/better 5 A cable, or apply the documented R12 4.12k→4.22k mitigation (power_tree.yaml) and re-derive. |

Only after Q1-Q5 pass may a Pi be connected — and it should be a **replaceable** Pi
(supervised-prototype context, BRIEF A3/D3). Escalation boundary (verbatim): "add
active OVP if the system becomes unattended, hard-access, carries valuable storage,
or powers expensive SDR".

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
| Assembly | BOM `bom_jlc.csv` + CPL `cpl_jlc.csv` (per-refdes LCSC keyed off circuit.json). Hand-solder list below. |

## 2. Hand-solder / off-CPL list
| Ref | Part | Why off-CPL |
|---|---|---|
| **F1** + blade fuse | 10 A MINI-blade holder (KH-AF90DIP-112) | THT, no JLC placement model (as in v1.1/v1.2). |
| **SW1** | SS12D07 master-off slide (C2939728) | **v1.3: removed from automated assembly** — the SS12D07 **VG4-vs-VG6 pin-pitch variant is not physically confirmed** against the board's vendored land. Hand-solder after verifying the received part's pitch against the pads. **Fallback if the pitch is wrong:** fit a 2.54 mm 3-pin header + shunt on the same land (COM-T1 shunted = ON; shunt removed = OFF); the switch can be fitted on a later revision. |

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

## 6. Notes carried from v1.1/v1.2
- RT-T3: LM5116 UVLO ~9.65 V cold-start > 9.0 V nominal — accepted P2 (doubles as
  LiPo deep-discharge protection); spec/silk read "9-12.6 V".
- Master-off SW1 kills both bucks + opens Q6 (~270 µA storage draw, power_tree E-OFF).
- First-power ritual (before ANY power): multimeter the XT60 blades against the
  board nets (polarity + continuity through F1/Q1) — 30 seconds of beeping beats
  every upstream analysis.
