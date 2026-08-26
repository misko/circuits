# `03_tscircuit/` — v4 circuit source

`src/pluto_rx2_8way_v4.tsx` is the electrical source for the carrier board. It
contains 28 declared components: the PE42482 RF core, ten SMA jacks, the RX1
pickoff, control conditioning, filtered switch power, status LED, and one
RP2040-Zero module boundary.

USB, flash, clock, boot/reset and regulation are inside the module and do not
appear as separate carrier components. `manifest.yaml` is the independent
refdes-count baseline; `net_aliases.txt` maps the two digit-leading rails; the
empty `parity_padmap.txt` explicitly records that every carrier pad is numeric.

Generated `build/`, `kicad/`, and `verification/` artifacts must never be
hand-edited. The generic bridge and backend regenerate them from this source.
