# PR2-P0-1 fix verification — v1.0-relative netlist node diff (2026-07-24)

Method: paren-walked both kicadsexpr netlists (sealed v1.0 source/ .net vs the
v1.1 rebuilt 06_build/netlists/*.net), keyed every (ref,pin) node to its net,
diffed. 734 nodes each side.

Result: EXACTLY 7 node moves, nothing else on the whole board:
- USB_DM -> USB_DN rename (F2): D_USB.2, J2.5, J2.13, U1.59
- LV strap fix (PR2-P0-1): U1.40 3V3 -> unconnected-(U1-Pad40)
                            U1.43 3V3 -> unconnected-(U1-Pad43)
                            U1.52 3V3 -> unconnected-(U1-Pad52)

Board pads measured (pcbnew, rebuilt 04_kicad): U1.40/43/52 all
unconnected-(U1-PadNN); schematic carries 3 no_connect markers at the pin
ends (sanctioned float, XU316 ds v2.0.0 §4.8 — internal PU selects 3V3 mode).
ERC after fix: 0 errors / 1201 warnings (was 1215; -14 = the excised branch's
wire warnings). DRC 0/0/0; parity 0 (588 connected nodes = 591-3;
no-connects 146 = 143+3); check_port_nets 115/115 + 8/8; count_parity 194 x4.
Chain surgery: 7 copper items removed (3 in-pad 3V3 vias at the strap pads +
4 dead branch segments B.Cu/In2); no dangling-track findings at
--severity-all.
