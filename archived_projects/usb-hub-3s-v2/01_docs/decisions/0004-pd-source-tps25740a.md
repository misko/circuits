---
id: 0004-v2
date: 2026-07-22
status: accepted
supersedes: usb-hub-3s v1 ADR-0004 (IP6559-C buck-boost)
---
# 0004-v2 — PD source: TPS25740A (sourcing spike REFUTES v1's "no simple part")

## Context
v1 ADR-0004 ran a sourcing spike for the spec-critical "5 A compliant USB-C"
function and concluded: *"Two-stage (5 V buck + standalone 5 V/5 A fixed-PDO
controller) — REJECTED: no such stocked controller exists."* It therefore
defaulted to the **IP6559-C buck-boost** (a 100 W PD SoC with 4 external FETs +
a 10 µH inductor), which E-TOPO now classifies as over-engineering for a
5 V-only port. v2's founding correction (D1) is that the port is fixed 5 V, so
the DC-DC is a plain buck; the remaining question is purely the PD *signalling*
source, which is what v1 got wrong.

## Sourcing spike (re-run 2026-07-22, live JLC/LCSC stock)
The v1 claim is **false**. A stocked, simple, standalone fixed-5 V/5 A PD SOURCE
controller exists:

| Candidate | Package | Role | 5 V/5 A? | Internal DC-DC? | Stock | Verdict |
|---|---|---|---|---|---|---|
| **TPS25740A** (C544309) | VQFN-24 0.5 mm | **DFP source PHY** | **yes** (HIPWR=5A) | **NO** — external FETs | **~2974** | **CHOSEN** |
| IP2726 (C2930955) | QFN-24-EP | DFP, dual-port | needs verify | no | 61 | backup (thin stock, more config) |
| IP2736 / CH237 | QFN-24 | combo power-loop SoC | yes | likely yes | varies | REJECT (IP6559 class — the thing we're removing) |
| IP2721, HUSB238, TPS25730/50, CH224 | various | **SINK/trigger (UFP)** | n/a | n/a | varies | REJECT — not a source |
| plain Rp (no chip) | — | Type-C current adv. | **3 A only** | n/a | n/a | fallback if 5 A relaxed (T4) |

**TPS25740A is exactly the architecture v1 said didn't exist:** a pure PD PHY
(CC1/CC2 monitor + BMC PD comms + gate driver for an EXTERNAL power NMOS),
NO internal converter. TI's own reference design (SLVUAP7A / EVM SLVUB28) feeds
it a regulated 5 V rail from an external buck/buck-boost — precisely our USB-C
buck → TPS25740A → USB-C VBUS topology. Configuration is RESISTOR PIN-STRAP
ONLY: no firmware, no EEPROM, no MCU, no vendor tool.
- `HIPWR` → GND: advertise **5 A** (vs 3 A when high).
- `EN9V` / `EN12V` left low: advertise **5 V ONLY** (no higher PDOs).

## Options
- **TPS25740A** — CHOSEN: only in-stock, simple, standalone 5 V/5 A PD SOURCE
  PHY; full public TI reference schematic + layout; pin-strap config; drives
  one external path NMOS. Package VQFN-24 0.5 mm → jlc_4layer_advanced
  (ADR-0011). Delivers a real 5 A PD contract with an e-marked cable.
- **IP6559-C buck-boost (v1's pick)** — REJECTED: over-capable (E-TOPO FAIL for
  a 5 V-only rail); QFN-48; 4 FETs + inductor; the over-engineering v2 exists to
  remove.
- **Plain Rp, no PD chip** — REJECTED for the 5 A spec: Type-C current
  advertisement tops at 3 A. Kept as the documented downgrade if the user
  relaxes to 3 A (BRIEF T4) — it would also drop the board to STANDARD tier.
- **IP2726** — REJECTED: 61 units stock (< 5× need), dual-port config surface
  we don't need. Named as the backup if TPS25740A stock evaporates.

## Known tensions / risks
- **NRND lifecycle.** TPS25740A is Not-Recommended-for-New-Designs at TI;
  ~2974 units in stock today satisfies 5× need, but order-day recheck is
  MANDATORY and alternates (IP2726 backup) are thin. Migration path if a respin
  is needed years out: TPS65987D (a heavier full-PD controller that needs a
  config tool + firmware — explicitly the complexity we avoid now). Recorded in
  ORDER_README.
- **Pin-strap correctness is a first-power check.** A mis-strap could advertise
  3 A or enable 9 V/12 V PDOs the 5 V buck cannot supply. First-power ritual:
  PD-analyzer read of the advertised PDO list BEFORE field use (ORDER_README).

## Decision
TPS25740A (LCSC C544309), fixed 5 V-only + 5 A pin-strap, driving one external
high-side NMOS path FET onto the USB-C VBUS, powered from the USB-C buck's 5 V
output. Exact pin map + strap values from the datasheet figure land in
02_parts/TPS25740ARGER/part.yaml (research in progress at parts stage).

## Consequences
- fab_tier rises to jlc_4layer_advanced (ADR-0011) — but for ONE small QFN-24,
  not a whole buck-boost power cell.
- Ledger harvest at release: the `pd-source-5v5a` entry gains a SECOND, simpler
  candidate (TPS25740A) with the "v1's no-such-part claim was wrong" note — the
  most valuable kind of harvest (a resolved over-engineering).
