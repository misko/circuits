# ADR-0001 — Input protection (mandatory ADR)

Context: external SELV 5 V ≥2 A wall supply on a barrel jack (§7.1); board
carries safety-critical relay coils; no battery, no UVLO need.

Decision: polyfuse (Bourns MF-MSMF200L-2, 2 A hold/4 A trip/16 V, C89650) →
reverse-polarity PFET (AO3401A, C15127: −30 V Vds, 60 mΩ, drop <0.1 V; body
diode bootstraps, gate to GND) → SMBJ5.0A TVS (C113974) + 220 µF electrolytic
+ 2×22 µF X5R bulk on 5VP. Local 100 n at every IC (§7.3).

Alternatives rejected:
- Series Schottky reverse protection: 0.3–0.4 V loss ⇒ AMS1117 dropout margin
  (needs Vin ≥ 4.8 V for 3.3 V out at load) too thin on a nominal-5 V rail.
- Glass fuse holder: board space + not resettable during bench bring-up; §7.3
  explicitly allows resettable polyfuse.
- Ideal-diode controller: cost/complexity unjustified at 2 A.

Residual risks (recorded): TVS clamp (~9.2 V surge) exceeds Pico VSYS abs max
during the surge event itself (see DETAIL_DESIGN #1); wrong-polarity 12 V
supply plugged into the 5.5/2.1 barrel would stress SMBJ5.0A to clamp —
polyfuse trips (documented in ORDER_README first-power ritual).

UVLO/over-discharge: N/A (no battery). OV: TVS only, per SELV bench-supply
scope. Verified against live stock 2026-07-19 (all codes ≥3 k stock).
