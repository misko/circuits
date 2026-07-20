# tscircuit render — cook-loadcell

An **alternate, non-authoritative** tscircuit design of this board (~33 parts).
KiCad (`../04_kicad/cook_loadcell.kicad_pcb`) remains the fab-of-record; this folder is a
second-opinion render + verification stack. Format + rationale (canon S-DSL):
`skills/kicad-pcb/references/tscircuit-folder.md`.

Status: **RENDERED** (2026-07-19, tsci 0.0.2112 / bun 1.3.14).

**Parity headline: node-for-node parity ACHIEVED after net-name normalization** —
components 29/29 electrical matched (33/33 with the 4 M3 mounting holes), nets 16/16
matched pad-for-pad, U1's 2 no-connects preserved. Only normalization: two mechanical
net renames `3V3→N3V3`, `5V→N5V` (tscircuit selectors reject a leading digit); all 14
other net names and every refdes preserved verbatim.

DRC-on-export (kicad-cli `--severity-all`): **451 violations + 3 unconnected** —
~430 parametric/cosmetic (0.15 vs 0.20 mm tracks, 0.30 vs 0.50 mm vias, silk text
size, a missing-`tscircuit`-lib note), ~14 genuinely-electrical auto-router defects
(2 shorts, 3 crossings, 6 mask bridges, 3 GND stubs) all in the congested SH/GND
corner — router imperfection, not an authoring error (netlist parity is 100%).

Footprint fidelity: pad count + pitch match on 32/33 parts; SJ1 is the sole miss
(2.54 mm bridged vs KiCad's 1.3 mm open, DNP). U1/D land patterns match count/pitch
but differ in copper from the exact JLC part (IoU 0.70 / 0.47) — not JLC-twinned.

Honest fidelity write-up: `verification/notes.md`. This is a design study; **KiCad
remains the fab-of-record and the only order source.**
