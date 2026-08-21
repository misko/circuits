# commission journal

## 2026-08-20 — start

- state: working
- subject: new clean project `usb-controlled-debug-hub-2a-v1`
- input: user requested a board similar to the two-USB-C debug hub with each
  USB-A capable of 2 A, and asked to preserve high-cost purchased parts where
  possible.
- measured: predecessor contract is 2.58 A total, one TPS56637 is rated 6 A,
  and its 15 V/3 A PD source provides 45 W. New external output alone is 40 W.
- finding: the predecessor KH-AF90DIP-112 authority publishes no current
  rating; GCT USB1130-15-A publishes 3 A/contact.
- decision: evaluate 20 V/3 A PD with two retained 6 A converters and two
  two-port banks. Firmware remains forbidden.
- next: close exact input protection and current-limit corners; build a
  preliminary quantity-five BOM and run the early manufacturing gate.

## 2026-08-20 — early boundary closed

- `early_design_check.py`: PASS 3/3 (`D-SPEC/E-PATH`, `E-SURGE`, adopted
  commission contracts).
- The gate rejected TPS259827O before schematic generation because the
  TVS2200 28.35 V worst clamp exceeds its 24 V recommended operating maximum.
- TPS26630 passed electrically but exact TI public stock was zero. It was not
  replaced by the similarly named clone because that is a different device.
- Selected candidate TPS16630PWPR is 60 V operating/67 V absolute, provides
  programmable UVLO/OVP and showed over 1,250 exact TI units publicly stocked.
- Machine corners: UVLO rising 16.1171–17.9106 V; OVP rising
  22.3402–24.7388 V. The former rejects 15 V PDOs and accepts 20 V PDOs; the
  latter stays below the retained converters' 28 V operating ceiling.
- Initial 5 V service proof closes at 4.785 V at the mated 2 A test plug with a
  90 mOhm path allocation. This is a strict placement/routing/first-article
  budget, not permission to round copper resistance down.
- next: close aggregate/port breaker fault timing and inrush, then issue the
  complete preliminary quantity-five BOM for JLC prelayout screening.

## 2026-08-20 — fault envelope, source identity and first schematic green

- `early_design_check.py`: PASS 4/4. Bank A normal/peak is 4.1/5.392 A;
  bank B is 4.0/5.292 A. Both coordinate with 300 ohm TPS259804 breakers and
  the 6.3 A minimum TPS56637 valley limit.
- Selected stocked 1.40 kOhm 1% port programmers. Full-corner port limit is
  2.080-2.646 A, above the 2 A service claim and below the 3 A connector.
- Replaced the uncommon 931 kOhm input-divider top leg with stocked 910 kOhm
  + 22 kOhm parts. Recomputed UVLO is 16.0696-17.8584 V and OVP is
  22.4135-24.8191 V.
- Fresh public catalog check: PASS 51/51 exact codes at quantity five.
  Tight rows are C1985204 crystal (8 for 5), C352384 910 kOhm (22 for 5),
  MCP2221A (27 for 5), and TPS259804 (122 for 10). This is not allocation.
- Manufacturing selection receipt: ACCEPTED 2/2 (183/183 exact source codes,
  all authored R/C values independently resolved).
- First TSX/KiCad bridge: 183 components, TSX diagnostics 0 errors, converter
  ERC 0 errors, S-COUNT 3/3 over 183 refs. The first value-only invariant set
  was then expanded to 55/55 value and exact-pin topology checks covering the
  complete protected input, both banks, all four port eFuses and management
  power assignment.
- Generated the quantity-expanded `prelayout_request.json` and blank
  `prelayout_response.csv`. Placement remains blocked until JLC's PCBA UI or
  export supplies availability, MOQ, minimum-cash and surplus-cost evidence.

## 2026-08-20 — exact pre-layout checkpoint

- Re-ran the current exact source: `EARLY-DESIGN` 4/4, `E-TOPO` 7/7,
  `E-INV` 55/55, `S-COUNT` 3/3 over 183 refs, and `S-OCCL` with zero
  occlusions. `git diff --check` is clean.
- Re-issued manufacturing selection readiness: ACCEPTED 2/2. The public
  catalog probe remains 51/51, but it is advisory and does not prove JLC PCBA
  allocation, preorder MOQ, order multiple, or surplus cash exposure.
- Regenerated the human review PNGs from the exact 10-page schematic PDF.
- State is intentionally `blocked_operator_evidence`: do not promote exact
  footprints or place/rout the PCB until the quantity-five JLC response is
  recorded and graded.

## 2026-08-20 — absolute +200 stock buffer adopted

- User rejected the quantity-only public-stock pass and required at least 200
  catalogue units beyond the complete five-board requirement for every line.
- Replaced the tight machine-populated lines before footprint promotion:
  C70590 crystal (101,010 stock), C3709087 ESD (2,523), C25800 910 kOhm
  resistor (42,065), C130462 MCP2221A-I/ST (380), and C2155765
  TPS259827ONRGET (603). Electrical topology remains unchanged except the
  pin-compatible 5 V bank breaker suffix and MCP2221A package.
- Kept exact 3 A GCT USB1130-15-A connectors because the high-stock JLC hits
  were under-rated or undocumented. They are explicitly excluded from turnkey
  assembly and must be hand-fitted or consigned; DigiKey publicly listed
  18,788 exact units.
- Extended `jlc_stock_check.py` with `--min-surplus`. Fresh result is PASS
  50/50 at quantity five plus 200 absolute surplus. The tightest remaining
  machine line is C17700166: 299 stock for 10 required, 289 surplus.
- Regenerated the exact 183-component schematic/netlist and fresh 50-line JLC
  pre-layout request. Gates: EARLY-DESIGN 4/4, E-TOPO 7/7, E-INV 55/55,
  S-COUNT 3/3, manufacturing selection 2/2.

## 2026-08-20 — user-accepted public-catalog pre-layout boundary

- The user explicitly accepted the fresh `required quantity + 200` public
  catalogue result as sufficient to proceed without the logged-in pre-layout
  JLC response.
- ADR 0003 bounds that choice to pre-layout and preserves DO-NOT-ORDER until
  exact final-uploader allocation, economics and BOM echo are captured.
- `manufacturing_readiness.py` verified 183/183 source components, 50/50 exact
  public-catalog lines, source-value identity and the explicit deferral:
  S-PART-FREEZE `ACCEPTED 4/4`.
- The next work owner is placement. The carried floorplan/route geometry is
  still an unadopted template scaffold and remains an explicit STOP until
  replaced by board-specific connector, power-cell and USB-corridor intent.
