# 03_tscircuit — crow-mic-pod-v2 authoring source

The remote microphone POD (board a of the CROW ACOUSTIC LOCALIZATION ARRAY)
authored in tscircuit/TSX. `src/crow_mic_pod_v2.tsx` is THE board; the
converter (`circuit_json_to_kicad_sch.py`) compiles it to the KiCad backend.

- Human schematic = `build/schematic.pdf` (tscircuit's own render, S6).
- Machine bridge = `kicad/crow_mic_pod_v2.kicad_sch` (ERC / netlist / parity).

S-DSL positioning: the TSX declares the circuit; every gate runs on the
native KiCad artifacts, never on tscircuit's claims. Routing (KRT) + the
digital twin stay KiCad-side (the two hard lines, ADR-0002).

Specialty parts author `supplierPartNumbers={{ jlcpcb: ["C…"] }}` (resolves
the FPID from `02_parts/*/part.yaml`) and a `<footprint>` child where the
footprinter can't express the land pattern (RJ45 jack, the CMT-8504
transducer, the AOM-5024 mic capsule). Leading-digit rails authored
N-prefixed (`N5V_AUDIO`→`5V_AUDIO`, `N5V_BEEP`→`5V_BEEP`).
