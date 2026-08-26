# ADR-0011 — close the USB2517I VBUS_DET full-corner divider

status: accepted for regeneration
date: 2026-08-18
tags: [usb, hub, vbus, electrical-margin]

## Context

The original detachable-host detector followed Microchip checklist
DS00004211A Figure 5-1 literally: 100 kOhm from upstream VBUS to VBUS_DET and
100 kOhm from VBUS_DET to ground. An independent pre-order review then applied
the USB2517I DC limits that the figure does not tabulate. With VBUS at the
checklist minimum, 1% resistor corners, and the specified 10 uA input leakage,
the original divider can fall below the 2.0 V guaranteed HIGH threshold.

The checklist requires both high impedance when upstream VBUS precedes hub
power and a sufficient VBUS_DET level over 4.5 V to 5.5 V. The data sheet
permits up to 5.5 V on an I/O pin while the 3.3 V supplies are in their normal
operating range. The design therefore needs a divider that proves both sides
of this envelope rather than copying the nominal example without a corner
calculation.

## Decision

Use a 47 kOhm, 1% upper resistor and a 100 kOhm, 1% lower resistor. Retain the
existing `USB_UP_VBUS -> R_VBUS_TOP -> HUB_VBUS_SENSE -> R_VBUS_BOT -> GND`
topology and keep upstream VBUS isolated from the self-powered 5 V trunk.

For a sinking 10 uA input leakage current, the minimum detector voltage is:

```text
VDET_MIN = (4.5 V / 47.47 kOhm - 10 uA)
           / (1 / 47.47 kOhm + 1 / 99 kOhm)
         = 2.721 V
```

This clears `VIH(min)=2.0 V` by 0.721 V. With 5.5 V, the opposite resistor
corners, and 10 uA leakage sourcing into the node:

```text
VDET_MAX = (5.5 V / 46.53 kOhm + 10 uA)
           / (1 / 46.53 kOhm + 1 / 101 kOhm)
         = 4.084 V
```

This remains below the 5.5 V operating maximum for an I/O pin. At nominal
5.0 V the divider draws about 34 uA, retaining a high-impedance sense path.

## Consequences

- `R_VBUS_TOP` changes from the superseded 100 kOhm selection to
  47 kOhm/C25792; its 0402
  footprint and placement do not change.
- `R_VBUS_BOT` remains 100 kOhm and uses the current orderable C25741.
- The schematic, BOM, CPL value field, board, Gerbers, evidence, and release
  hashes must be regenerated even though the copper geometry can remain the
  same.
- Electrical invariants bind both divider values and all five relevant
  pin-to-net relationships to this ADR.
- First article testing must verify enumeration while upstream VBUS is swept
  through the supported low-voltage corner.

## Authority

- Microchip DS00004211A, section 5.1 and Figure 5-1: detachable-host sensing,
  high-impedance requirement, and 4.5 V to 5.5 V range.
- Microchip DS00001598C, Tables 5-1, 8-2 and operating conditions: VBUS_DET
  function, 2.0 V HIGH threshold, +/-10 uA input leakage, and I/O limits.
