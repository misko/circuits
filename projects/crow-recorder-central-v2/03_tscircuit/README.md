# 03_tscircuit — crow-recorder-central-v2 authoring source

The CENTRAL 8-channel USB-audio recorder authored in tscircuit (TSX). Compiled
by `circuit_json_to_kicad_sch.py` into the KiCad artifacts the backend gates and
fabricates (ADR-0002 / canon S-DSL).

- Humans read `build/schematic.pdf` (tscircuit's own render — ships in release).
- The machine reads `kicad/crow_recorder_central_v2.kicad_sch` (our converter).

Authoring positioning: tscircuit is the design front-end; the KiCad backend +
KRT routing + jlc_twin stay authoritative (the two hard lines). Specialty parts
(XU316, PCM1865, USB4105, RJHSE-5384, barrel jack, etc.) each author
`supplierPartNumbers={{jlcpcb:["Cxxxx"]}}` + a `<footprint>` child so their FPID
resolves from `02_parts/`.

Net convention: leading-digit rails are `N`-prefixed in TSX (`N5V`,`N3V3`,`N1V8`,
`N0V9`,`N3V3A`,`NP5V_AUDIO`,`NP5V_BEEP`) — the converter strips the guard `N`.
See `net_aliases.txt` for anything the convention can't reach.
