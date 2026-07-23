# ADR-0003 — MCP23017 expander closes the Pi GPIO budget

status: accepted
date: 2026-07-22

Native demand ~29 signals vs 28 Pi GPIO (overflow found in review).
Decision (user D3/F1): MCP23017-E/SS on the Board-A-local I2C bus
absorbs SLOW signals: 4-6 switched-rail enables, power-good, mode/
door/latch readbacks, BOARD_ID, TC /FAULT. Fast/safety-critical stays
native: shift-register lines, OE_N/RESET_N, E-stop, TC /DRDY, HX711,
heartbeat. Post-split: ~22-24 native, margin 4-6. The firmware-less
pin-map table (Pi GPIO + expander bits) is a MAINTAINED gate artifact
(Gate 4 deliverable): any addition fights for a documented pin.
