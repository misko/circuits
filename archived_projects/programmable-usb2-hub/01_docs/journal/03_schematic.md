## 2026-08-01 23:18 — iterate 1 (post-back)
- did: Re-entered the schematic gate after the four-port power-architecture and sourcing backtrack; audited the LTC3889 cycle-by-cycle current-limit corner before topology sign-off.
- result: MEASURED at 24 V, 5.21484375 V, 250 kHz, two 6.8 uH -20% inductors in parallel: 6.0026 A peak-to-peak total ripple and 9.0013 A peak at the 6 A rail load. The adopted 48.2 mV tier provides only 8.6537 A at the conservative 68/75 threshold ratio and +1% effective shunt corner, so it fails before placement.
- next: Encode the corrected 58.9 mV tier and its lower/upper tolerance bounds in power_stages.yaml and early_design_check.py, then regenerate the canonical schematic.

## 2026-08-01 23:29 — iterate 2 (post-back)
- did: Added the schema-2 current-limit gate, corrected LTC3889 `IOUT_OC_FAULT_LIMIT` to 0xD2F2, regenerated the canonical TSX/KiCad schematic, and ran the full pre-placement semantic battery.
- result: MEASURED run 656ab9d769eb passed P-MOD 3/3, TSX-PRE 40/40, M-FRESH 9/9, 220 components/877 pins, S-NETMERGE 157/157, pin-map 44/44, E-INV 131/131, E-ADR 2/2, EARLY-DESIGN 3/3, E-TOPO 6/6, E-MARGIN 4/4, S-COUNT 220, circuit BOM value check, and ERC 0 errors. It stopped only at PR-REVIEW 0/1 because the required exact-hash topology review does not yet exist.
- next: Review the fresh netlist/dossiers independently, write a hash-bound SOUND or DEFECTIVE topology verdict, and rerun the canonical chain before placement.

## 2026-08-02 00:53 — iterate 3 (ADR-0007 correction)
- did: Dispositioned the exact-hash review's six P0 findings; restored the locked 2 A requirement; replaced each TPS259830/AON6354 cell with dual-sourced TPS259470; derated each LTC3889 channel to one 6.8 uH inductor, one 10 mOhm shunt and 4 A; corrected LM74810 OV and isolated LTC VDD33; added exact machine-tested LTC3889/USB2517 startup images. The startup derivation also found and fixed grounded LTC ASEL pins and the impossible claim that USB2517 could be configured while reset was asserted.
- result: MEASURED fresh run 2e70d1861754 passed P-MOD 3/3, TSX-PRE 40/40, M-FRESH 9/9, 211 components/771 pins, S-NETMERGE 150/150, pin-map 44/44, E-INV 115/115, E-ADR 2/2, EARLY-DESIGN 3/3, E-TOPO 6/6, E-MARGIN 4/4, S-COUNT 211/211, coded-value BOM and ERC 0 errors. Firmware passed both C binaries and 12 Python tests, including forced readback mismatch and missing-power-good safe-state cases. The chain stopped at PR-REVIEW because the prior DEFECTIVE review is correctly stale.
- next: Complete an independent topology review bound to the new netlist/parts/rules hashes. Enter placement only if it returns SOUND.
