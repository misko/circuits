# Exact source layout

`pi_usb_port_switch.kicad_pcb` at this directory's root is the canonical
release source and is byte-identical to the live reviewed PCB.

The `exact/` subtree preserves the original project-relative layout:

- `exact/04_kicad/` contains the exact KiCad project;
- `exact/03_src/lib/` contains its project-local footprints and 3D models;
- `exact/03_tscircuit/src/` contains the TSX authoring source; and
- `exact/06_build/netlists/` contains the exported parity netlist.

Open the PCB from `exact/04_kicad/` when inspecting models offline. Its
unchanged `${KIPRJMOD}/../03_src/lib/...` paths resolve inside this archive.
This duplicate tree avoids the v0.1.0 defect where making paths standalone
silently changed the supposedly exact archived PCB bytes.
