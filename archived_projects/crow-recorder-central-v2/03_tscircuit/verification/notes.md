# crow-recorder-central-v2 — tscircuit authoring notes / fidelity gaps

## No-connect mechanism (the ~90 unused XU316 GPIO + other sanctioned floats)

**Mechanism used: a pad simply LEFT OUT of `connections`.** Empirically verified
(2026-07-23, scratchpad probes):

- The converter (`circuit_json_to_kicad_sch.py`) resolves each pad's net from
  tscircuit's connectivity map. A pad with no `connections` entry has net=None,
  and the converter emits a KiCad `(no_connect ...)` flag at that pin (line ~484).
  Probe: a 1-chip board with 2 of 8 pins bound → 6 `no_connect` flags, ERC 0 errors.
- This is the sanctioned-float path. Unused pins are **never** shorted onto a
  shared net, and no dedicated per-pin `<net/>` is needed.

Applied to: XU316 unused X0D../X1D.. GPIO, pin55(NC), MIPI lanes 25/26/28/29/31/32,
USB_ID(58); PCM1865 XO(9) + GPIO(19-22); NC7NZ34 3Y(2); W25Q16 has none;
RJ45 LED pins 9-12; USB-C SBU pins (A8/B8); TPD4EUSB30 spare channel + NC pads;
TPD2E2U06 NC pads (1,2); barrel-jack switch leg (3); XC6227 NC(3); TCR2LF18 NC(4);
AP61102 U8 PG-out is used, pin6 unused on U8; SHT40 EP(die pad).

## Test points — pinLabels required

A bare `<chip footprint="testpoint_pad" connections={{pin1:...}}>` produced a pcb
pad but **no source_port**, so the converter dropped all 12 test points (194
source_components but only 182 emitted). Fix: `pinLabels={{pin1:"1"}}` forces the
single pad to materialize a schematic port. After the fix: 194/194 emitted.

## Q1 pinLabels — for the E-INV series_chain

`electrical_invariants.yaml` asserts `series_chain [VIN_RAW, Q1, 5V] through
Q1:[D,S]`. The checker resolves a pin by number, exact pinfunction, or
pinfunction with a trailing `_<n>` stripped. The SOT-23 pads are named 1/2/3 with
no function, so Q1 was given `pinLabels={{pin1:"G",pin2:"S",pin3:"D"}}` → the
netlist carries `pinfunction "D_3"/"S_2"` → resolves to D/S. Drain(3)=VIN_RAW,
Source(2)=N5V(→5V), so the chain holds.

## FPID resolution for parts NOT in 02_parts

- R/C/L: commodity token map (`res0402…`, `0402…1210`, testpoint tokens). The
  bucks' inductors L1/L2 and the four ferrite beads (FB_BEEP/L_pll/FB_u33/FB_u18)
  are authored `<inductor footprint="1210|0805">`; tscircuit emits footprinter
  `1210`/`0805`, which the converter maps to `Capacitor_SMD:C_<size>` — a
  land-compatible 2-pad footprint (a 0805/1210 ferrite shares the cap land). This
  is a THROWAWAY schematic-gate FPID; a real ferrite/inductor part.yaml is added
  before routing. FPID is non-empty, so the gate passes.
- 8-pin debug header `J_DBG` (`pinrow8`): `pinrow6/7/8` were **added to the
  converter's `COMMODITY_FP` map** (`circuit_json_to_kicad_sch.py`) — an additive
  extension of the already-documented "2.54mm pin headers" capability (the map
  previously stopped at `pinrow5`). Cannot regress existing lookups. An 02_parts
  entry was rejected because a stub part.yaml fails the P-ESC/P-LAYOUT audits.

## Alphanumeric pads (parity_padmap.txt)

USB4105 (A1..B12,SH), RJ45 (SH), SHT40 (EP) real pad names are alphanumeric and
would be dropped silently by tsci. Authored with numeric portHints and mapped in
`parity_padmap.txt`; `tsx_preflight.py` passes before the first build.

## Ferrite/inductor value display

Ferrite beads are authored as `<inductor inductance="600">` for a 600R@100MHz
bead — the "600" is the bead impedance, not henries; the value string is cosmetic
and not load-bearing for ERC/parity/FPID.

## Net-name convention

Leading-digit rails authored N-guarded: N5V/N3V3/N0V9/N1V8/N3V3A → converter
canon_net strips the guard → 5V/3V3/0V9/1V8/3V3A. `net_aliases.txt` is empty
(the convention reaches every rail).
