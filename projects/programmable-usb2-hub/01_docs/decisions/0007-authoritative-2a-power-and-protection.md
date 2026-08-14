---
status: accepted
---
# ADR-0007 — Honor the locked 2 A requirement with coordinated protection

date: 2026-08-01
tags: [topology, power, protection, requirements, safe-startup]

## Context

BRIEF Q2, G2, C9, and the commission fact-lock replace the original 3 A
guarantee with 2 A continuous at each mated USB-A test plug. ADR-0006 restored
3 A without a later user directive and is therefore invalid. The exact-hash
pre-route review also found its TPS259830 limit uncoordinated with the 3 A
connector, its PG output misrepresented as FLT, the LM74810 OV divider
miswired, LTC3889 VDD33 tied against the system 3.3 V regulator, and the
required digital configuration absent.

## Decision

Retain the LTC3889 dual controller because its two independently held-off,
telemetric rails and tight programmable voltage window still reduce total
system risk. Derate each rail to 4 A continuous. Each channel uses one
MWSA1206S-6R8MT 6.8 uH inductor and one WSL2512R0100FEA 10 mOhm Kelvin shunt.
Program and read back:

- `VOUT_COMMAND = 0x14DC` = 5.21484375 V;
- `IOUT_CAL_GAIN = 0xD280` Linear11 = 10 mOhm;
- `IOUT_OC_FAULT_LIMIT = 0xCBC0` Linear11 = 7.5 A, selecting the explicit
  75 mV current-limit tier;
- 250 kHz, channel phases 0 and 180 degrees, and the declared fault responses.

At 24 V input, 5.21484375 V output, 250 kHz, and the -20% inductor corner,
ripple is 3.0013 A peak-to-peak. The 4 A full-load peak is 5.5006 A; the 15%
required peak is 6.3257 A. The datasheet's explicit 68/75/82 mV threshold
range and +/-1% shunt give 6.7327-8.2828 A. The low corner passes, the high
corner is below the 15.2 A inductor Isat(-20%) rating, and the high-corner
shunt dissipation is 0.686 W below its 1 W rating.

Use TPS259470ARPWR on each port with `RILM = 1.47 kOhm +/-1%`. TI specifies
active current limiting, a dedicated active-low FLT output, and integrated
true reverse-current blocking. Equation 5 and the +/-10% limit accuracy bound
the threshold to approximately 2.02-2.52 A, guaranteeing 2 A while staying
below the connector's 3 A continuous rating. The 2.2 nF ITIMER remains a
bounded transient blanking interval; persistent limiting asserts FLT and the
MCU latches the command off. Post-switch ADC telemetry remains the truthful
voltage-present signal.

The complete path is 45 mOhm maximum TPS259470, 10 mOhm budgeted PCB/vias/
joints, and 80 mOhm maximum mated VBUS plus GND contacts: 135 mOhm. At 2 A
with 20% residual margin the drop is 324 mV. The 5.183925 V worst-low rail
therefore leaves 4.859925 V at the mated plug, above 4.75 V; the unloaded
5.246075 V high corner remains below 5.25 V.

Reconnect LM74810 `SW -> R1 90.9 kOhm -> OV -> R3 4.64 kOhm -> GND`; no zero
ohm SW-to-OV link is permitted. Isolate LTC3889 VDD33 on a private bypassed
node. Leave ASEL0/ASEL1 in the datasheet-defined open state; firmware writes
`MFR_ADDRESS=0x4F` through global address `0x5A` before device-addressed
readback. Hardware keeps both RUN pins low until every load-bearing LTC3889
value is written and read back. USB2517 reset is then released to latch SMBus
mode, but the hub remains unattached until its register image is written and
verified and firmware issues `USB_ATTACH`. Any mismatch leaves rails, hub,
port power, and data isolated.

## Sourcing

TPS259470ARPWR passed the user's pre-selection rule on 2026-08-01: MEASURED
Mouser API stock 9,831 for exact manufacturer MPN and MEASURED JLC/LCSC
`C3662799` catalog stock 1,736. The retained LTC3889 power-stage parts already
have two-authorized-supplier evidence. Stock is volatile and must be rerun on
order day.

## Consequences

- ADR-0006 is superseded; its 3 A claim, parallel magnetics/shunts,
  TPS259830/AON6354 cells, and `0xD2F2` setting must not remain live.
- The schematic, placement, route, reviews, and staged release are invalidated
  and must be regenerated from declarative source.
- Release requires a machine-tested startup image, independent exact-hash
  topology approval, placement/P-ADJ reviews, DRC 0/0/parity 0, JLC twin and
  stock gates, adversarial release reviews, and a fresh sealed archive.
