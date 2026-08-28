# Schematic-stage review dispositions

The exact schematic checkpoint has zero open blocking topology or readability
findings.  `SOUND` advances the design to PCB mechanics/placement; it does not
authorize an order.

| id | finding | severity | disposition |
|---|---|---|---|
| SCH-V5-P1-01 | The first generated PDF gave incorrect function names to several unused U2 pins although its connected pins were correct. | P1 | closed before review signature — corrected against ST DS13866, discarded the old checkpoint, reran the full pipeline and inspected all four replacement pages |
| SCH-V5-P2-01 | Direct Raspberry Pi GPIO SWD is host/configuration dependent and has not been exercised on hardware. | P2 | recorded — keyed J11 provides standard Cortex VTref, ground, SWDIO, SWCLK and NRST; firmware/programming validation remains a later stage |
| SCH-V5-P1-02 | Exact SMA mechanics, current Amphenol drawing capture and JLC impedance/launch geometry were unresolved at the schematic pause. | P1 | mechanics/drawing closed before routing by exact Rev-C lands, native exact-code STEP registration and outward edge review; routed launch/return geometry and order-stage DFM remain open under V5-F3 |

## Connector-service first-article disposition

| id | finding | severity | disposition |
|---|---|---|---|
| CONN-V5-P1-01 | Fabricated-board feedback reports that adjacent SMA coupling hardware is difficult to hand-tighten and that the nominally flush mating faces provide insufficient grip exposure. | P1 | open for successor PCB/enclosure work — [the dated qualitative observation](2026-08-27_connector-service_first-article.md) supersedes the earlier render-only coupling-nut/tool-access conclusion; no replacement pitch or overhang is authorized until exact mating hardware, tool, torque, neighbors, enclosure, and physical measurements are bound |
