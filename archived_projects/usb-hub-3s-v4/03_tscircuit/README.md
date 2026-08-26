# USB Hub 3S v4 schematic source

`src/usb_hub_3s_v4.tsx` is the hand-written electrical truth for this power-
only board. It compiles to both `build/schematic.pdf` for human review and the
KiCad schematic/netlist used by every later board and manufacturing gate.

The source intentionally contains no USB data or USB-PD topology. USB-A data
contacts end at TPS2513A charge-signature controllers; the Type-C data and SBU
contacts are unconnected. The TPS25810 controls Type-C attach, 3 A current
advertisement and cold-socket VBUS switching.

Generated paths under `build/`, `kicad/`, `verification/` and `fab/` must never
be hand-edited. Correct this source or its declared maps and regenerate.
