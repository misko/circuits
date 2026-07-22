# CHANGELOG — shitty-kitty

## v1.0 — 2026-07-18  [tag: sk-v1.0]
- Initial release: ESP32-S3-WROOM-1 controller, TMC2209 stepper driver
  (motor hardware-disabled at boot via R8 ENN pullup), 4x MPR121QR2 (24
  electrode lines, inner/outer ring headers), LIS2DH12 accelerometer,
  12V entry protection chain (polyfuse + P-FET reverse polarity +
  SMBJ16A), AP63205 5V/2A buck + AMS1117 3V3, USB-C programming port,
  host header (5V/1.5A + UART). 4-layer, JLC standard tier.
- Routing surgery finished from the WIP checkpoint (18->7->0 DRC): fine-pitch
  GND-via consolidation, ACC_INT offset-junction vertex-snap, VIN_12V pour
  min-thickness corner fix, Q1/U9 R-THERM power-pad vias. DRC 0/0/0.
- Gates: DRC 0/0/0 · policy_audit zero-FAIL · jlc_twin exit 0 · pin review
  PASS (5 fresh agents) · render review PASS-WITH-NOTES · stock 27/27 >=5x.
Released: 07_releases/v1.0-2026-07-18/
