# ORDER README — crow-recorder-central-v2 (8-channel CENTRAL recorder)

Central hub of the CROW ACOUSTIC LOCALIZATION ARRAY: 8 remote mic pods home-run
over custom-pinout Cat5e into 8 RJ45 ports (J3–J10), 2x PCM1865 4-ch ADCs
(U2/U3), XU316-1024 USB-Audio SoC (U1) to a USB-C host port (J2), shared-clock
topology (ADR-0004), beeper calibration bus, 5V brick input (GST25A05, J1) with
AO3401A reverse-polarity FET (Q1) + SMAJ5.0A (D1) + 2A fuse (F_IN).
Release **v1.0-2026-07-23**. Board **170.1 × 120.1 mm, 6 layer**.

Gates at seal: DRC 0/0/0 (--severity-all --refill-zones --schematic-parity),
check_port_nets 115/115 labels + 8/8 ports pin-for-pin, ERC 0 errors,
count_parity 194 x4, policy_audit 0 FAIL (3 evidence-backed waivers), E-INV
7/7, E-TOPO 2/2. Evidence in `verification/`; hashes + provenance in
`MANIFEST.txt`.

---

## 0. ⚠️⚠️ CRITICAL DEPLOYMENT CONSTRAINT — PORTS ARE NOT ETHERNET ⚠️⚠️

**All 8 RJ45 ports (J3–J10) carry a CUSTOM 5 V AUDIO/POWER pinout
(1,2 = AUDIO±; 3,6 = +5V_BEEP/RETURN; 4,7 = +5V_AUDIO; 5,8 = GND). NEVER plug
any port into an Ethernet switch, router, or ANY PoE source.**

WHY (accepted-risk sign-off, ADR-0007, carrying the pod-v2 ADR-0005 user
waiver): an 802.3 endspan injector (mode B: 4/5 = +, 7/8 = −) drives ~48 V
through the per-port PTC into the shared 5 V rail — above the AP61102 buck
vin_abs_max (6.5 V) and every 5 V-rated part. The input TVS (D1) sits on
VIN_RAW, the wrong side of Q1 to clamp a rail-side injection. There is
deliberately NO per-port OVP this rev. Mitigations are administrative: per-port
**"NOT ETH 5V!"** silk at every jack + the banner, custom-crimped cables only,
closed owner-cabled deployment. The beeper legs (3,6) are also per-port
UNFUSED — a beeper-pin short opens F_IN (2 A) = whole-board outage (ADR-0007;
v-next: F_BEEP PTC + shared SMBJ5.0A on the P5VA spine).

---

## 1. JLCPCB order options

| Setting | Value |
|---|---|
| Layers | **6** |
| Dimensions | **170.1 × 120.1 mm** |
| Via/process tier | **`jlc_6layer_smallvia`** (ADR-0002) — 0.30/0.15 mm via-in-pad; **ADVANCED small-via option REQUIRED** or JLC rejects the drill set |
| Impedance control | not required (USB FS/HS pairs kept short; no controlled-Z spec) |
| Surface finish | ENIG preferred (0.4 mm-pitch TQFP-128 + USON paste release) |

Upload set (in `fab/`):
- **PCB order:** `crow_recorder_central_v2_gerbers.zip` (6 copper layers, F/B
  mask+paste+silk, Edge_Cuts, PTH+NPTH drills). BOM/CPL are **not** in the zip.
- **Assembly BOM:** `fab/bom.csv` — `Comment,Designator,Footprint,MPN,LCSC`.
- **Assembly CPL:** `fab/cpl.csv` — rotation-DB-corrected.

Re-run a same-day stock check before paying (stock moved during staging;
L1 C882626 was at 665 units).

## 2. Sourcing swaps + consignment lines (decided at staging, all documented)

| Ref(s) | Ordered part | Why |
|---|---|---|
| U9 | **TLV70018DDCR (C79924)** | TCR2LF18 (C150173) stock 0; ADR-0006 documented pin-compatible drop-in |
| Y1 | **NX3225SA-24MHZ-EXS00A-CS08583 (C2762192)** | FA-238 MD50Y stock 0; same 3225-4P, same CL 9 pF (02_parts note) |
| R_fb2b | **402 kΩ (C25785)** | 400 k not stocked; −0.17 % on the 0V9 setpoint, inside tolerance |
| FB_BEEP, FB_u33, FB_u18, L_pll | **BLM21SP601SN1D (C3716677)** | first pick BLM21PG600SN1D is a **60 Ω** part (Murata code 600 = 60 Ω) — wrong-part caught at M-BOM staging |
| CL1, CL2 | **12 pF C0G (C1547)** | fresh-lens P1: authored 22 pF vs the crystal's CL 9 pF (eff. 14 pF, ~30-50 ppm pull); 2×(9−3 pF stray) = 12 pF |
| Cout_U10 | **2.2 µF 25 V X5R (C72203)** | fresh-lens P1: Torex XC6227 requires CL 2.2 µF for phase compensation (authored 1 µF); 25 V rating keeps DC-bias derating mild (~1.9 µF eff at 3.3 V) |
| U1 | XU316-1024-TQ128-I24 (C6938291) | **consignment/global-sourcing** (ADR-0003): JLC assembly stock chronically 0; source Digi-Key/Mouser + consign, or hand-place (0.4 mm TQFP, hot-air skill required) |
| J3–J10 | RJHSE-5384 (C9900035627) | C99* = consign-only code (no JLC assembly line); hand-solder THT or consign (same certified footprint as pod-v2, pad-1 continuity backstop below) |

## 3. Hand-solder / off-CPL parts

| Ref | Part | Note |
|---|---|---|
| J3–J10 | RJHSE-5384 RJ45 x8 | THT; consign or hand-solder |
| U1 | XU316 (if not consigned) | prefer JLC consignment line |
| JP_INJ | 1x03 2.54 mm header | uncoded, hand-solder (beep-injector jumper) |
| J_DBG | 1x08 2.54 mm header | uncoded, hand-solder (JTAG 1V8) |

## 4. First-power ritual (when boards arrive)

1. **Before any power:** multimeter every RJ45 port against the silk legend
   (1,2 = AUDIO±; 3,6 = +5VBEEP/RTN; 4,7 = +5VAUD; 5,8 = GND) and pad-1 →
   contact-1 continuity on one port (footprint certified on pod-v2; one-time
   coupon check).
2. Confirm D1 band → VIN_RAW, Q1 orientation (drain = VIN_RAW — CORRECT
   as-built; do not "fix"), J1 center = +.
3. Power from the GST25A05 brick only. Verify 5 V, then 3V3 → PG_3V3 → 0V9
   sequencing (ADR-0005), 3V3A, 1V8.
4. Enumerate USB-Audio on the host; verify per-port pod power (4/7 vs 5/8
   = 5 V) on all 8 ports before connecting pods.

## 5. Recorded P2s (fresh lens, non-blocking)

- Buck Cin hot loop 2.51 mm vs the <2 mm part.yaml budget (0.51 mm over;
  same-side cap, small loop at 2.2 MHz) — nudge Cin at next re-place.
- L1 (C882626) stock was 665 at staging — order-day recheck mandatory.
- ROT-DB-SUGGEST rows in verification/twin_report.txt (SOT-23 180 vs DB −90
  etc.): the rotations-DB values are assembly-zero truth — verify every
  diode/SOT/TSSOP orientation in the JLC order preview, do not blind-apply.

## 6. Next-rev work order (non-blocking)

- F_BEEP PTC (~1.1 A hold) in series with FB_BEEP; shared SMBJ5.0A on the
  P5VA spine (ADR-0007).
- Optional forced-PWM EN divider on U7 if 3V3 PFM ripple ever shows in the
  audio chain (ADR-0005 amendment).
- Converter wire-crossing invariant upstream (the net-merge class that forced
  this board's check_port_nets gate).
