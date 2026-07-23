# architecture: usb-hub-3s-v3

v3 = v2 with the USB-C PD cell removed (ADR-0001). All other cells carry forward
from v2 unchanged and proven-routable.

## Block diagram

    3S LiPo (9-12.6V)
      XT60 -> F1 fuse -> Q1 reverse-polarity P-FET -> D1 TVS(on VIN) -> VIN
        |
        +--> BUCK A (LM5116 + Q2/Q3 + L + shunt) --> 5VA rail (<=6A)
        |       -> 3x [TPS2557 switch + USBLC6 ESD] -> 3x USB-A receptacle (5V/2A)
        |       -> 2x TPS2513A DCP (data-line charging advertisement)
        |
        +--> BUCK C (LM5116 + Q4/Q5 + L + shunt) --> 5VC rail (<=5A)
                -> [optional e-fuse] -> USB-C VBUS  (5V/5A, PLAIN — no PD)
                -> CC1/CC2 Rp pull-ups (source-present advertisement)
                -> VBUS bulk caps + ESD

## Power tree
See `03_src/rules/power_tree.yaml` — both rails step-down bucks, E-TOPO PASS,
worst-case input 6.8A @ 9V (55W / 0.9 eff).

## The USB-C port (the v3 delta)
- VBUS = the 5VC buck output, brought directly to the receptacle. No PD source
  controller, no pass FETs, no gate/sense/discharge network.
- CC1/CC2: Rp pull-up resistors so the Pi detects an attached source +
  orientation. The Pi is configured `PSU_MAX_CURRENT=5000` (bootloader EEPROM)
  to skip PD negotiation and draw its full 5A — see ADR-0001.
- Optional simple e-fuse / current-limit switch on VBUS for short-circuit
  protection (a single part, NOT a PD PHY).
- This port is Pi-DEDICATED by design; a generic USB-C device would see a
  non-PD source (cap at 3A). Documented in the release README + a silk hint.

## Fab tier
STANDARD target — the advanced-tier driver (the TPS25740A 0.5mm QFN) is gone.
Every remaining IC is leaded (HTSSOP / SOT / SOIC), all proven-routable on v2.

## What carries forward from v2 (do not redesign)
- Input protection chain (D1-corrected: TVS after Q1 on VIN).
- Both LM5116 5V buck cells (control cluster + FET pair + inductor + shunt).
- 3x USB-A port cells (TPS2557 + USBLC6 + connector) + the DCP.
Only the PD cell is removed and replaced by the simple USB-C port above.
