# CHANGELOG — ble-bus-bar

## v1.0 — 2026-07-19  [tag: bbar-v1.0]
- Initial design: 12–24 V / 60 A bus bar, 6× ATO-fused 30 A ports,
  per-port INA238 + WSLP2726 0.5 mΩ high-side sensing, ESP32-C3 BLE,
  W25Q64 stats flash, LMR16006X 60 V buck, USB-C flash/debug.
- 2-layer 2 oz 165×64; paired trunk pours; ampacity floors as netclass
  DRU rules; hand-routed sense channels + I2C corridor, KRT west zone.
- Gates: ERC 0 · DRC severity-all 0/0/0 · audit PASS · policy audit
  0 FAIL (2 evidence waivers) · pin review 0 FAIL · stock ≥25× PASS.
Released: v1.0-2026-07-19
