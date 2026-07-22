# pin dossier: BZ1  (CMT-8504-100-SMT-TR)

- footprint: pod:CMT-8504
- board position: (72.0, 84.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: 02_parts/CMT-8504-100-SMT-TR/cmt-8504-100-smt-tr_2024-09-11.pdf
- part.yaml verification note: pad polarity + land pattern read from datasheet Mechanical Drawing (top/bottom views) and 'Recommended PCB Layout Top View', page 2, rev 2024-09-11 — 2026-07-18

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-3.50,-3.50) | N | 2.5x2.5 | + | BZ_P |
| 2 | (-3.50,+3.50) | S | 2.5x2.5 | - | BEEP_RET |
| 3 | (+3.50,+3.50) | S | 2.5x2.5 | DUMMY | unconnected-(BZ1-DMY-Pad3) |
| 4 | (+3.50,-3.50) | N | 2.5x2.5 | DUMMY | unconnected-(BZ1-DMY-Pad4) |
