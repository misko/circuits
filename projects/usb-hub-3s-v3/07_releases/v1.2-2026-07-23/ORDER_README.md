# ORDER README — usb-hub-3s-v3 **v1.2** (internal board name `usb_hub_3s_v2`)

> DRAFT for the v1.2 seal (staged in `06_build/verification/`). At seal time this
> moves to the release root `07_releases/v1.2-2026-07-23/ORDER_README.md`.

3S-LiPo powered power-distribution board: XT60 pack in -> 10 A MINI-blade fuse ->
dual synchronous bucks (LM5116) -> 3x USB-A (5 V charging, no-data) + 1x
Pi-dedicated USB-C (5 V/5 A, **discrete-protected**). **NOT a USB hub, NOT USB-PD.**
Release **v1.2-2026-07-23**. Board **130.1 x 92.1 mm**, **4 layer**, **110 parts**.

**v1.2 supersedes v1.1-2026-07-23** — DROPS the TPS26631 eFuse (over-built for a
5 V/5 A Pi rail; root cause of the routing wall + v1.1's two electrical blockers)
and replaces it with a simple discrete VBUS protection chain (ADR-0002, BRIEF
A2/D2 user decision):
`5VC -> Q6 (AON6403 P-FET, ENKILL-gated reverse-block via Q7 BSS138) -> F2 (PPTC
polyfuse) -> VBUSC -> J5`, with D5 (SMBJ6.0A TVS) over-voltage clamp. buck-C FB
stays on LOCAL 5VC (v1.1 runaway fix).

Gates at this draft: DRC **0/0/0** (incl. schematic-parity 0), ERC 0, parity
**110 x5 sources**, policy_audit **0 board-FAIL** (its M-BOM vs the v1.1 sealed
release is the expected pre-seal false-positive), E-INV **24/24**, M-BOM
(bom_source_check) **PASS** (every BOM LCSC == source). Fresh zero-context
red-team: orchestrator-dispatched (fold its verdict in before seal).

---

## ⚠️ MANDATORY ORDER-DAY STOCK RECHECK (two Extended-tier parts)

**Both were selected by parts-research but their JLC stock/rating could NOT be
verified in the sealed build env. Re-run `jlc_stock_check` on order day and
confirm BEFORE placing the order:**

| Ref | Function | LCSC | MPN | Confirm | Fallback |
|---|---|---|---|---|---|
| **F2** | VBUS over-current PPTC | **C6165170** | SMD2920-700/16N (2920) | **7 A hold + ≥16 V Vmax + in stock.** 7 A (not 6 A) required: a 6 A hold derates to ~4.8 A @50 °C < the 5 A continuous load → nuisance-trip. 16 V covers a buck-fail-high (~12.6 V at the fuse). | **C3762416** (Littelfuse 2920L600/16MR-A, 6 A/16 V, CONFIRMED) — but nuisance-trips at 5 A @50 °C (**degraded**; use only if no 7 A/16 V 2920 is stocked). |
| **D5** | VBUS over-voltage TVS | **C140903** | SMBJ6.0A (SMB) | Uni-dir, Vwm 6.0 V, in stock. Reject SMBJ5.0A (5 V standoff conducts on the 5.4 V rail). | **C1973522** (Bourns SMBJ6.0A alt). |

All other LCSC codes are library-standard / previously-shipped and pass M-BOM.

---

## 1. JLCPCB order options
| Setting | Value |
|---|---|
| Layers | **4** |
| Dimensions | 130.1 x 92.1 mm |
| Via tier | **`jlc_4layer_standard`** — 0.45 mm pad / 0.30 mm drill. **Standard process is sufficient — do NOT select the advanced small-via option.** |
| Assembly | BOM `bom_jlc.csv` + CPL `cpl_jlc.csv` (per-refdes LCSC keyed off circuit.json). F1 (10 A MINI-blade holder) + the blade fuse are hand-solder / off-CPL. |

## 2. Required Pi setting (ADR-0001)
The USB-C port is a **plain 5 V/5 A rail, NOT USB-PD**. The Pi MUST draw 5 A
without PD: set **`PSU_MAX_CURRENT=5000`** in the bootloader EEPROM (or
`usb_max_current_enable=1` in `config.txt`). Without it the Pi caps downstream USB
at 600 mA (still boots). A generic USB-C device sees a non-PD 3 A-advertised source.

## 3. Cable note
Use a short, **5 A-rated USB-C cable** for the Pi (no PD → no e-marker enforcement).

## 4. Protection behavior (discrete, ADR-0002)
- **Over-current:** F2 PPTC trips on a short/overload (resettable).
- **Over-voltage:** on a buck-fail-high, D5 TVS clamps + F2 trips (crowbar).
- **Reverse-current / master-off:** Q6 (P-FET) is held OFF when the hub is switched
  off (SW1/ENKILL → Q7 opens Q6) → its body diode blocks a powered device on the
  port from back-feeding the pack. Reverse current is NOT instantaneously blocked
  while the port is actively ON (bounded by F2) — an accepted right-sizing for a
  Pi-dedicated sink.

## 5. Notes carried from v1.1
- RT-T3: LM5116 UVLO ~9.65 V cold-start > 9.0 V nominal — accepted P2 (doubles as
  LiPo deep-discharge protection); spec/silk read "9-12.6 V".
- Master-off SW1 (SS12D07) kills both bucks + opens Q6 (mA-scale storage draw);
  confirm the SW1 land pitch on the JLC preview (hand-solder part).

## 6. First-power / bench gates (order-day + bring-up — NOT board defects)
- **(a) F2 + D5 order-day `jlc_stock` recheck** — see the ⚠️ table at the top.
- **(b) FIRST-POWER OV CAUTION (documented downgrade, ADR-0002-accepted).** On a
  buck HS-FET short, 5VC/PMID → ~12.6 V; D5 (TVS) clamps VBUSC to ~8-10 V (above
  the Pi's ~6 V ceiling) and relies on the PPTC **F2 tripping (slow, ~seconds)** to
  end the exposure. This is a **downgrade from v1.1's active eFuse OVP cutoff** —
  the accepted cost of the discrete simplification (the user's simplify tradeoff;
  a hard buck-HS-short is a rare single-fault event). Bring-up: on first power,
  scope VBUSC and confirm ~5.1-5.2 V.
- **(c) BENCH-VERIFY.** (i) **5A-hot connector delivery vs Pi UV 4.63 V** — E-MARGIN
  on the 100 mΩ floor: 5.18 V typ connector − 4.63 = 550 mV = 110 mΩ cable budget
  (worst quad-corner ~5.03 V → ~80 mΩ; measure the real cable IR). (ii) **F2 hold
  margin hot** — ~5.6 A @50 °C vs the 5 A load = 1.12x; confirm no nuisance trip at
  real ambient.
