# journal: 03_schematic

## 2026-07-23 — start
- did: wrote the COMPLETE net binding spec (every part, every pin->net) from the
  18 verified part.yamls — power/protection, 2 bucks + 2 LDOs, XU316 128-pin
  (power domains, straps, QSPI boot pins, USB, JTAG, IOT-bank audio GPIO, PLL
  filter), 2x PCM1865 (clock trap XI->GND, SCKI<-buffered MCLK, TDM DOUT shared),
  NC7NZ34 1->2 clock fanout + 33R source-series, FA-238 osc (Rf1M/Rd680R/22pF),
  W25Q16 QSPI, SHT40 I2C, USB-C + TPD4EUSB30 (VBUS sense-only), beeper FET + gate
  RC, 8 RJ45 port channels (custom NOT-ETHERNET pinout + per-port ESD/PTC/input
  RC), 12 test points, injection header. Single GND net (TI PCM1865 guidance).
- result: spec captured all 8 electrical invariants. Delegated the tscircuit
  authoring + ERC/parity/count_parity closure loop to a dedicated agent (the
  128-pin SoC with ~90 unused GPIO + specialty footprint children + USB-C
  alphanumeric pads is a large mechanical+iterative surface).
- next: review the agent's netlist against the spec; confirm ERC 0 + count_parity
  0 + FPID complete + 8 invariants pass; CHECKPOINT at the schematic gate.

## 2026-07-23 — finish (schematic gate GREEN)
- did: delegated tscircuit authoring to a sub-agent; independently re-verified its
  output against the binding spec. Fixed the project .gitignore to cover
  03_tscircuit/{.tscircuit,dist,node_modules,tsx_build} (commission template
  missed them). Confirmed the converter's pinrow6/7/8 COMMODITY_FP addition is in
  the REPO skills/ (version-controlled; ~/.claude is a symlink to it) — additive
  1x06/1x07/1x08 header tokens for the JTAG (1x08) + injection (1x03) headers.
- result: SCHEMATIC GATE GREEN, independently re-run:
    ERC = 0 errors (1332 warnings, all baselined parametric)
    count_parity = 194 == 194 (manifest / circuit.json / kicad_sch / netlist)
    FPID = 194/194 (every component resolved)
    E-INV = 7/7 (PCM XI->GND x2, SCKI->MCLK_A1/A2, Q1 RPP series_chain D->S,
                  VIN_RAW TVS, 5V bulk cap)
    policy_audit = no FAIL
  Spot-checked critical nets in the netlist: VBUS is a SEPARATE net from 5V
  (sense-only, no back-feed); USB_DP/DM -> U1.60/U1.59 + D_USB ESD + J2 pads.
  194 components total.
- next: CHECKPOINT for commit. Then placement (mixed-signal-audio-hub archetype:
  ADC spine center, switchers+beeper in the north/SW away from ADCs; XU316 needs
  a project-local TQFP-128_EP footprint + 16-via thermal grid) -> routing -> DRC 0/0/0.

## 2026-07-23 — placement stage (audit PASS)
- did: created project-local footprints (TQFP-128_EP + 16-via thermal grid via
  sub-agent; US8 for NC7NZ34) + vendored USB4105/RJHSE538X with numeric pads to
  match the tscircuit netlist (alphanumeric pads -> 1..17 / SH->13); repointed 4
  FPIDs (XU316 EP, PCM1865/SHT40 to KiCad stock) + regenerated schematic (ERC 0,
  194/194 FPID held). Extended generate_board_generic LAYER_NAMES with In3/In4
  (6-layer support — flagged to coordinator, test pending). Authored floorplan.yaml
  (mixed-signal-audio-hub: 39 anchors + patterns snapping 155 passives to their
  IC/region; In1+In4 GND planes). Converged the audit: RJ45 rot 0 opening-north +
  y=18 overhang, 20mm pitch, mounting holes out of the port band, buck cluster
  clear of the barrel jack.
- result: generate_board OK (194 parts, 6 copper layers, 4 holes); audit_template
  I1-I8 PASS (0 fails/0 warns). DRC baseline: clearance_real 0, hole_clearance_real
  0, 333 unconnected (unrouted). Board at 06_build/proof/.
- next: generate_rules (netclasses into board) -> route.yaml -> KRT -> stitch ->
  DRC 0/0/0 (routing gate). Add the generate_board In3/In4 test + RED-verify.

## 2026-07-23 — generate_board In3/In4 test (coordinator reproducibility ask)
- did: added t1_generate_board.py::t_six_layer_inner_planes (GREEN: a 6-layer
  board places GND planes on In3.Cu+In4.Cu) + t_in4_needs_six_layers (known-bad:
  In4.Cu on a 4-layer board rejected). RED-verified: reverting the LAYER_NAMES/
  INNER_LAYERS In3/In4 rows turns the positive test RED ("zone on unknown layer
  In3.Cu"); restored -> 27 passed / 0 failed.
- result: the generate_board_generic In3/In4 6-layer change is test-covered +
  RED-verified. Ready for the coordinator to commit generate_board_generic.py WITH
  the board files. Board regenerates from restored source (verified In3.Cu present).
- next: routing stage — route.yaml + generate_rules -> KRT -> stitch -> DRC 0/0/0.
