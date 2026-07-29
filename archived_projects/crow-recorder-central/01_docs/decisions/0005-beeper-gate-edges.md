> Adopted 2026-07-21 into crow-recorder-central from archived_projects/crow-array-central (provenance ADR 0011; re-verified by this project's own gates before any release). Original text follows.

# ADR-0005 — beeper driver: slowed gate edges + separate return topology

Status: accepted 2026-07-18 (brief §5A: "Slow beeper MOSFET edges
modestly; fast edges provide no acoustic benefit and increase crosstalk")

## Context

Each port's AO3400A switches ~150mA at 4kHz into 35ft of Cat5e pair +
the pod transducer. The audio pairs ride the same cable; a fast drain
edge (ns-class) couples capacitively into AUDIO+/- and shows up as the
brief's "zero-delay artifact" (§9 risk table). The acoustic burst only
needs ~4kHz bandwidth — edge content above ~50kHz is pure crosstalk.

## Decision (per port, in the 8x port-channel generator)

- **R_g = 1k** series from the XU316 GPIO (3V3 drive) to the gate.
- **C_gs = 4.7nF** gate-source at the FET.
- **R_pd = 100k** gate pulldown (FET off while the XU316 boots/floats).

tau = 1k x 4.7nF ~= 4.7us -> 10-90 edge ~10us: >=1000x slower than a raw
GPIO edge (>=60dB less dV/dt coupling at the audio band's crosstalk
mechanism), yet only 4% of the 4kHz half-period (125us) — burst envelope
intact for the matched filter. AO3400A stays in its linear region ~10us
per edge at 150mA/2.5V worst case ~ 0.2mJ/burst-second — far inside SOA.

- **Separate return**: BEEP_RETn (RJ45 pin 6) lands on the FET drain and
  NOWHERE else; FET sources star to GND at the port strip. Return current
  never shares copper with GND_AUDIO (pins 5/8) on the board — the same
  discipline the cable enforces by pairing (green pair carries feed +
  switched return together = minimal loop).
- Clamp lives at the POD (SS14 flyback, pod ADR-0002); the central drain
  gets no clamp — the pod clamp holds the pair at <=5.4V. TVS reserve for
  the drain exists as the port ESD array's spare channel budget; not
  populated.

## Rejected

- Gate-drain Miller cap (true dV/dt control): better linearity of the
  edge but the added drain-gate path injects switching charge back into
  the GPIO bank; RC-on-gate is the reference-design-style simple slow.
- Software-only PWM shaping: firmware-dependent; hardware must be safe
  with naive firmware (P6 build sequence runs eval-board firmware first).
