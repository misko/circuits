# Clean-room provenance

Checkpoint date: 2026-08-13

## Scope and authority

`pluto-rx2-8way-v5` is independently derived from this task's user statements,
fresh manufacturer/standards/fabricator/distributor evidence, files created
inside this v5 project, and generic process contracts/checkers. Existing
`pluto-rx2-8way*` project results are excluded as design inputs. Generic skills
and `improvements.md` are process inputs only; their incident descriptions do
not supply v5 component, topology, schematic, placement, or route decisions.

Evidence priority is: current standard or exact manufacturer document; current
JLC capability/order evidence; exact-code distributor identity/availability;
textbook principle; tutorial/video orientation. A lower tier cannot override a
higher one, and no tutorial or video is an authority for an exact pin, rating,
footprint, or fab option.

## Exclusion incident and containment

During the exact-parts stage, one repository-wide text search accidentally
surfaced filenames and short matching snippets from excluded legacy Pluto
paths. No excluded legacy design file was intentionally opened, copied,
executed, diffed, or used to select a v5 part or design value. From that point,
searches were scoped to this v5 path or generic skill paths. All v5 electrical
facts below were independently re-derived from current external evidence and
the exact local manufacturer dossiers. This disclosure replaces the earlier,
over-broad claim that excluded names had never even been listed or searched.

No legacy schematic, PCB, route, fab, assembly, review, or release artifact is
present in v5. No schematic, PCB, or fab artifact has yet been generated.

## Fresh evidence used

| Authority | What it establishes | Boundary |
|---|---|---|
| User D1–D8 | 1-of-8 receive selection, 100 MHz–5.9 GHz, SMA, JLCPCB, accepted AD9363 extended-range risk, autonomous unique dwell control, independent USB-C 5 V, and continuation with the presented exact architecture | Product authority |
| pSemi DOC-75785-4 | PE42482A-X pinout, truth table, 10 MHz–8 GHz device range, absorptive/all-off behavior, supply/logic limits, RF DC condition, package and switching figures | Device facts, not board performance |
| ST DS13866 Rev 4 local / Rev 5 online | STM32C011F4P6 TSSOP-20 pinout, supply, HSI48 error, BOR, watchdog, SWD and decoupling | Exact controller interface; local revision deviation recorded |
| TI SBVS395E / SLLSEG9C | TPS7A2433 input/output/thermal bounds and TPD2E2U06 ESD bounds/layout guidance | Exact power/protection interfaces |
| GCT USB4105 Rev B, Littelfuse, Samsung, Yageo, Amphenol exact documents | Connector layouts and passive ratings/polarities/packages | Exact code facts; Amphenol PDF download deviation recorded |
| USB-IF Type-C Release 2.5 and TI Type-C guide | Current Type-C authority and two independent 5.1-kohm Rd implementation for the simple 5-V sink | Power-only attach; no data or PD claim |
| JLCPCB capability, stackup and impedance calculator pages | JLC04161H-7628 layer build and calculator inputs; current controlled-impedance order process | Does not establish unsolved trace geometry or order allocation |
| JLC/LCSC plus independent distributor checks dated 2026-08-13 | Exact-code catalog identity and dated stock observations | Volatile; uploader/order echo still mandatory |
| ADI AD9363/AD9361 pages and CN0534 | Official device bands and AD9363 RF-input damage ceiling | User accepts physical AD9363 operation outside its official band |

The detailed link index and comparison against engineering literature are in
[`research/exact-parts-and-interfaces.md`](research/exact-parts-and-interfaces.md).
Exact PDFs, hashes, extracted facts, pin maps, source observations, and package
evidence live under `02_parts/<MPN>/`.

## Validation boundary

This checkpoint validates source declarations only. It does not claim ERC,
footprint, layout, DRC, Gerber, assembly-uploader, or measured RF success.
Those gates require artifacts that do not yet exist. A green source gate
authorizes schematic entry after the requested pause, not PCB generation.
