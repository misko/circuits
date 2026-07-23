# architecture: usb-hub-3s-v3 (rev v1.1)

**What this board IS:** a PROPRIETARY 3S-LiPo POWER-DISTRIBUTION board - NOT a
USB hub, NOT USB-PD / USB-standards-compliant. It fans a protected 3S pack out
to 3x USB-A **charging** ports (5V, dumb DCP advertisement, NO data hub) and 1x
USB-C **power** port that is a proprietary Pi-dedicated 5V/5A rail (Raspberry Pi
5 with `PSU_MAX_CURRENT=5000`; a standards sink sees only the 3A CC-Rp offer).
Input is a PROTECTED 3S pack + balance charger ONLY.

v3 = v2 with the USB-C PD cell removed (ADR-0001). v1.1 hardens the sealed v1.0:
a TPS26631 eFuse + reverse-current-block FET pair now protects the USB-C VBUS
(the ARCHITECTURE 'optional e-fuse' is now POPULATED), the buck-C loop senses at
the connector, a master-off slide switch gates both bucks, input/output MLCC
ratings are raised, and each SW node gets an optional RC snubber. All other cells
carry forward from v2 unchanged and proven-routable.

## Block diagram

    3S LiPo (9-12.6V)
      XT60 -> F1 fuse -> Q1 reverse-polarity P-FET -> D1 TVS(on VIN) -> VIN
        |
        +--> BUCK A (LM5116 + Q2/Q3 + L + shunt) --> 5VA rail (<=6A)
        |       -> 3x [TPS2557 switch + USBLC6 ESD] -> 3x USB-A receptacle (5V/2A)
        |       -> 2x TPS2513A DCP (data-line charging advertisement)
        |
        +--> BUCK C (LM5116 + Q4/Q5 + L + shunt) --> 5VC rail (<=5A)
                -> Q6/Q7 reverse-block FET pair -> U13 TPS26631 eFuse -> VBUSC
                     (v1.1: current-limit 5.83A / ~5.9V input-OV cutoff / soft-
                      start / reverse-current block) -> USB-C VBUS (5V/5A, PLAIN)
                -> buck-C FB SENSES VBUSC (connector held ~5.15V despite eFuse drop)
                -> CC1/CC2 Rp pull-ups (source-present advertisement)
                -> VBUS bulk caps + ESD
     (master-off: SS12D07 slide switch grounds both LM5116 EN pins -> all off)

## Power tree
See `03_src/rules/power_tree.yaml` — both rails step-down bucks, E-TOPO PASS,
worst-case input 6.8A @ 9V (55W / 0.9 eff).

## The USB-C port (v3 no-PD; v1.1 PROTECTED)
- VBUS = **VBUSC**, the OUTPUT of a TPS26631 eFuse (U13) fed from the 5VC buck
  through a reverse-current-blocking FET pair (Q6 AON6354 power FET + Q7 BSS138
  fast gate-pulldown, per SLVSE94G 8.3.5). No PD source controller, no PD pass
  FETs, no gate/sense/discharge network.
- Protection (v1.1): adjustable current limit R_ILIM 3.09k -> 5.83A; ~5.9V
  input-OV cutoff (OVP divider, protects the Pi from a buck HS-short); 10nF dVdT
  soft-start; MODE->GND auto-retry; and true reverse-current blocking (a powered
  sink can no longer back-feed the pack — red-team RT-T4).
- Setpoint (v1.1): the buck-C FB senses VBUSC (post-eFuse), so the loop holds the
  CONNECTOR at ~5.15V regardless of the eFuse+FET series drop (>=5.0V @5A while
  <5.25V no-load). R3/R12 3.74k->3.92k (0.1%).
- CC1/CC2: Rp pull-up resistors so the Pi detects an attached source +
  orientation. The Pi is configured `PSU_MAX_CURRENT=5000` (bootloader EEPROM)
  to skip PD negotiation and draw its full 5A — see ADR-0001.
- This port is Pi-DEDICATED and NON-standards-compliant by design; a generic
  USB-C device would see a non-PD source (cap at 3A). Silk + README say so.

## Fab tier
STANDARD target — the advanced-tier driver (the TPS25740A 0.5mm QFN) is gone.
Every remaining IC is leaded (HTSSOP / SOT / SOIC), all proven-routable on v2.

## What carries forward from v2 (do not redesign)
- Input protection chain (D1-corrected: TVS after Q1 on VIN).
- Both LM5116 5V buck cells (control cluster + FET pair + inductor + shunt).
- 3x USB-A port cells (TPS2557 + USBLC6 + connector) + the DCP.
Only the PD cell is removed and replaced by the simple USB-C port above.
