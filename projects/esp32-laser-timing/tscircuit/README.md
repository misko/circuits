# tscircuit render — esp32-laser-timing

An **alternate, non-authoritative** tscircuit design of this board (~76 parts).
KiCad (`../04_kicad/esp32_laser_timing.kicad_pcb`) remains the fab-of-record; this folder is a
second-opinion render + verification stack. Format + rationale (canon S-DSL):
`skills/kicad-pcb/references/tscircuit-folder.md`.

Status: **RENDERED** (Phase-1 schematic-bridge study, ADR-0001).

Parity headline (`verification/parity.md`, `verification/notes.md`):
- **72 / 72** electrical components authored node-for-node (real footprints + JLC parts).
- **tscircuit MODEL net parity: 36 / 36** named nets node-for-node — the design is exact,
  including the 41-pin ESP32-S3-WROOM-1 module and the 14-pin LM339 (zero pin-label mismatches).
- **tscircuit kicad_sch EXPORT net parity: 14 / 36** — the DSL→native-KiCad schematic exporter
  is **not** fidelity-preserving at this scale: it collapses 2+ hand-authored-footprint chips
  (U1, J1) onto one shared `Device:U_chip` symbol (truncated to 2 pins each) and fragments the
  densest nets (GND, VTH). Root-caused in `notes.md`.
- ERC 563 (mostly parametric); DRC-on-export 260/150 (mostly parametric; 9 real shorts).

**Verdict:** tscircuit *authors* a large/active board perfectly (parity by construction), but
its native `kicad_sch` export clears the bridge only for a board with ≤1 many-pin custom-footprint
chip. KiCad `../04_kicad/` remains the sole authoritative fab-of-record.
