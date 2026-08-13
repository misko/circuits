# Schematic-stage review dispositions

The exact schematic checkpoint has zero open blocking topology or readability
findings.  `SOUND` advances the design to PCB mechanics/placement; it does not
authorize an order.

| id | finding | severity | disposition |
|---|---|---|---|
| SCH-V5-P1-01 | The first generated PDF gave incorrect function names to several unused U2 pins although its connected pins were correct. | P1 | closed before review signature — corrected against ST DS13866, discarded the old checkpoint, reran the full pipeline and inspected all four replacement pages |
| SCH-V5-P2-01 | Direct Raspberry Pi GPIO SWD is host/configuration dependent and has not been exercised on hardware. | P2 | recorded — TP1-TP5 provide target sense, ground, SWDIO, SWCLK and NRST; firmware/programming validation remains a later stage |
| SCH-V5-P1-02 | Exact SMA mechanics, current Amphenol drawing capture and JLC impedance/launch geometry remain unresolved. | P1 | deferred by project findings V5-F1 through V5-F3; blocks DESIGN_CLEAN and any order, not schematic-stage progression |
