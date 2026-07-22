# CHANGELOG — ble-bus-bar

## v1.1 — 2026-07-19  [tag: bbar-v1.1]
- Durable mechanical anchoring (user feedback A4, D9, ADR-0007): 7× M4
  PLATED mounts with Ø9 washer lands at the load-entry points (stud
  torque in shear, fuse-row mid-span bracketed); metal standoffs, nylon
  rejected with load math; board 64→74 mm tall; all electrical content
  keeps v1.0 coordinates.
Released: v1.1-2026-07-19

## v1.0 — 2026-07-19  [tag: bbar-v1.0]
- Initial design: 12–24 V / 60 A bus bar, 6× ATO-fused 30 A ports,
  per-port INA238 + WSLP2726 0.5 mΩ high-side sensing, ESP32-C3 BLE,
  W25Q64 stats flash, LMR16006X 60 V buck, USB-C flash/debug.
- 2-layer 2 oz 165×64; paired trunk pours; ampacity floors as netclass
  DRU rules; hand-routed sense channels + I2C corridor, KRT west zone.
- Gates: ERC 0 · DRC severity-all 0/0/0 · audit PASS · policy audit
  0 FAIL (2 evidence waivers) · pin review 0 FAIL · stock ≥25× PASS.
Released: v1.0-2026-07-19
