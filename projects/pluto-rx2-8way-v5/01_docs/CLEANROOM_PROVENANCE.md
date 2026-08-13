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

During the PCB-mechanics stage, two generic searches were also too broad. One
displayed a legacy Pluto-specific rotation-evidence row and another displayed
short legacy floorplan snippets while locating the shared floorplan schema.
Those results are excluded: no coordinate, rotation, outline, footprint,
launch, route, or review value from them is used here. The v5 mechanics are
instead derived from the exact current Amphenol/GCT/pSemi documents, fresh
exact-code JLC CAD used only as an independent comparator, the selected JLC
stackup/solver result, and the generic generator's project-independent schema.
Subsequent PCB searches remain scoped to v5, exact external evidence, or
project-independent process sources.

During D16 route-tool capability discovery, a repository-wide search for a
generic route-following fence implementation again surfaced legacy Pluto
filenames and short review/config snippets. Those results are excluded. No
legacy coordinate, route, via pattern, pitch, impedance model or review value
was copied into v5. The v5 RF polylines are exact-collision-derived from its
own D15 board; its 1.40 mm fence requirement is independently derived from the
retained v5 JLC effective dielectric constant and current Analog Devices
layout guidance. Subsequent route searches were restricted to v5 and shared
backend implementation.

No legacy schematic, PCB, route, fab, assembly, review, or release artifact is
present in v5. The v5 schematic, exact footprints and unrouted placement were
generated independently. The canonical PCB remains segment-free; D16 now also
has a derived, deterministic r0 containing reviewed RF/GND preparation copper.
No KRT route, promoted route, fab package or release artifact exists.

## Fresh evidence used

| Authority | What it establishes | Boundary |
|---|---|---|
| User D1–D15 | 1-of-8 receive selection, 100 MHz–5.9 GHz, SMA, JLCPCB, accepted AD9363 extended-range risk, autonomous unique dwell control, independent USB-C 5 V, fast programmable dwell profile, direct Raspberry Pi SWD, exact 901-143-6RFX confirmation, a proper programming connector, compact mechanics and exact D15 placement approval | Product authority |
| pSemi DOC-75785-4 | PE42482A-X pinout, truth table, 10 MHz–8 GHz device range, absorptive/all-off behavior, supply/logic limits, RF DC condition, package and switching figures | Device facts, not board performance |
| ST DS13866 Rev 4 local / Rev 5 online | STM32C011F4P6 TSSOP-20 pinout, supply, HSI48 error, BOR, watchdog, SWD and decoupling | Exact controller interface; local revision deviation recorded |
| TI SBVS395E / SLLSEG9C | TPS7A2433 input/output/thermal bounds and TPD2E2U06 ESD bounds/layout guidance | Exact power/protection interfaces |
| GCT USB4105 Rev B, Littelfuse, Samsung, Yageo, Amphenol and Samtec exact documents | Connector layouts and passive ratings/polarities/packages | Exact code facts; exact Amphenol Rev-C drawing/PCN and Samtec FTSH series/footprint prints retained with hashes |
| KiCad 10 exact GCT USB4105 footprint/model and fresh JLC exact-code CAD | Independent package/model comparison and reproducible project-local connector render bodies | Manufacturer drawings remain dimensional authority; catalog/stock CAD does not override them. Native C429844 STEP corrects the visibly misregistered converted-WRL SMA render without changing copper. |
| USB-IF Type-C Release 2.5 and TI Type-C guide | Current Type-C authority and two independent 5.1-kohm Rd implementation for the simple 5-V sink | Power-only attach; no data or PD claim |
| JLCPCB capability, stackup and impedance calculator pages | JLC04161H-7628 layer build, retained 0.295/0.200-mm CPWG solution and current controlled-impedance order process | Live 1.0-mil coating input differs from the written guide's 1.2 mil; order echo and allocation remain mandatory |
| JLC/LCSC plus independent distributor checks dated 2026-08-13 | Exact-code catalog identity and dated stock observations | Volatile; uploader/order echo still mandatory |
| ADI AD9363/AD9361 pages and CN0534 | Official device bands and AD9363 RF-input damage ceiling | User accepts physical AD9363 operation outside its official band |

The detailed link index and comparison against engineering literature are in
[`research/exact-parts-and-interfaces.md`](research/exact-parts-and-interfaces.md).
Exact PDFs, hashes, extracted facts, pin maps, source observations, and package
evidence live under `02_parts/<MPN>/`.

## Validation boundary

The schematic checkpoint validates ERC, exact connectivity, pin-map parity and
human/RF schematic intent. The current track-free placement additionally
validates realized footprint identity, connector datums, package separation,
placement-stage DRC and renderability. D16's derived r0 validates deterministic
RF geometry, zero RF vias, early ground service and the exact remaining route
denominator. It does not claim completion of the control/power route, RF-fence
closure, Gerber correctness, assembly-uploader acceptance or measured RF
success.
