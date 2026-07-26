# DISPOSITIONS — cooksense v1.3, 2026-07-26

Every finding raised during this revision and what was done about it. A finding
with no disposition is an open defect; there are none of those below.

## FIXED IN v1.3

| # | finding | disposition |
|---|---|---|
| P0-A | `J_ESTOPLOOP` placed INSIDE `J_DOOR` — the isolated 30 V loop shorted to 3V3/GND/DOOR_RAW, 1.300 x 0.600 mm of overlapping pad copper | Merged both isolated connectors into ONE 4-pole block `J_ISOLOOP` (user decision, ADR-0013). East column re-solved; P-COLLIDE 0/0. |
| P0-B | `R_OPENT` ORDERED at 6.2 kΩ (C25915) where the design needs 62 kΩ — open-thermistor detect threshold would sit at 3.1073 V, above the LMV393's 2.500 V VICR ceiling, so an open head reads FINE | Pinned to **C37825** (62 kΩ). All four divider resistors pinned and ledger-verified. |
| P0-C | `R_WDPETPD` ORDERED at 100 kΩ (C25741) where the design needs 1 kΩ — TPS3823 WDI sources 190 µA, R_max = 5.21 kΩ, so the watchdog would be silently disabled | Pinned to **C11702** (1 kΩ). Whole class swept: 90 unpinned passives, exactly one mismatch. |
| P1-1 | `R_TEMPOK` pulled up from the DIGITAL rail while both comparators run on 3V3_ANALOG — one open ferrite drives TEMP_OK to 3.235 V = PERMISSIVE | Moved to `3V3_ANALOG`. Failure now gives 0.000 V = restrictive. Cost a re-race (see ORDER_README §13). |
| P0-1 | H4 mounting hardware 3.737 mm from keypad copper against a 6.000 mm requirement | Edge-reaching isolation notch; I-HW now measures 6.598 mm around it. |
| — | `opto_isolation_2mm` measured 0.199 mm on v1.2 copper | Pour keepouts + User.4 route mirror; now 2.0000 mm (all copper, all layers). |
| — | Board silk read `sidecar v1.2` on a v1.3 release | Bumped to v1.3. |
| — | `electrical_invariants.yaml` still asserted the 6.2 k / 3.107 V DEFECT | Corrected to 62 k / 2.0370 V, old text quoted in place. |
| — | tsx header claimed `DOOR (NC reed+EOL)` over NO/no-EOL code | Header corrected to state what is built and name the gap. |
| — | I-HW gave pads a geodesic and TRACKS a straight line — false FAIL at H4 (4.617 mm through a through-cut; true surface path 7.165 mm) | Track branch now uses the same visibility-graph geodesic. RED-verified: pre-notch board still fails at 4.031 mm. |
| — | 13 CPL rows with blank LCSC; J_LOADCELL/J_PI THT on an SMT-only CPL; J_PI 24.1634 mm off datum | All corrected; A-POP PASS, A-POS 189/189 at 0.00000 mm. |

## DEFERRED TO v1.4 — with the reason, and none of them fail permissive

| # | finding | why deferred |
|---|---|---|
| D-1 | **Door input is NO with no EOL**; a SHORT reads "closed" undetectably, across a 0.650 mm JST-GH pad gap in a pollution-degree-3 steam environment | v1.3 closes the defect it claimed (fail-permissive on wire break). Supervision is a different, stronger property that needs a new analog path — all 8 ADC channels and all 4 comparator channels are used — plus a harness re-spec and firmware. A specification, not a patch. **Prominent in ORDER_README §2-0; commissioning decision required.** |
| D-2 | **R_HYS gives U_COMP2 NEGATIVE feedback** — the open-detect has no hysteresis | Structural, not a wiring slip: TH_CAM_A is one node feeding U_COMP's IN+ and U_COMP2's IN−, so one resistor cannot be positive feedback for both. The only correct fix is a new part (R_HYS3: TEMP_OK → TCAM_OPEN) which RE-SPECS the threshold to ~2.0836 V — the number the whole VICR argument rests on. Bounded: a real open moves the node 15.5 mV against 232 mV of overdrive so it still latches solidly; exposure is chatter at the −10.4 °C boundary; direction is LOCKOUT, not permissive. |
| D-3 | **TH_CAM_A/B routed 93.62 / 87.75 mm** against a declared `keep_short max_span_mm: 8`; closest aggressor SPI_SCLK at 0.206 mm | Needs re-placement; not re-opening the floorplan on a board with a live safety fix. Direction is fail-safe. The GATE half is a fleet item: `audit_board`'s I-PROX has no span check at all, so the budget passed vacuously. |
| D-4 | Our `Diode_SMD:D_SOD-323` land draws a cathode band on a **bidirectional** part (5 refs) | Assembly risk nil — JLC places from the CPL, not our silk. Reviewer risk is real. Five footprint swaps after the DRC gate was measured is not worth invalidating it. |
| D-5 | Twin does not cover 2 of 54 coded BOM lines (C25768, C37825) | Both entered the BOM after the twin run; both are 0402 chip passives on land classes the twin checked 30+ times. Declared in ORDER_README §13. |

## FLEET ITEMS RAISED HERE, OWNED ELSEWHERE

- Deterministic UUIDs in `generate_board_generic.py` — makes M-REPRO byte-checkable and stops a data-only CPL fix reading as a full respin.
- `policy_audit` multi-board mis-targeting (`rels[-1]` selects the interposer release on this ADR-0007 project).
- `bom_source_check` leg C: an AGGREGATED BOM Comment (`"100kΩ / 1kΩ"`) defeats the decade check because the label parser takes the first token. Needs a known-bad fixture.
- `jlc_rotation_measure` / `jlc_twin` have no cathode-band channel, so they report BLIND on rectifiers whose polarity is carried by a band.
