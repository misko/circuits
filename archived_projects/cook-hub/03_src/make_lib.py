#!/usr/bin/env python3
"""Emit 03_src/lib/cookhub.pretty/ project footprints (deterministic text):

- Relay_StandexDIP_1A_pinout12 : Standex DIP05-1A72-12L reed relay,
  pin-out code 12 (DS p.3): 4 THT leads on the DIP-14 corner grid —
  coil pins 1/7 on the WEST column, contact pins 14/8 on the EAST column,
  columns 7.62mm apart, pins 15.24mm apart within a column. Body
  19.3 x 6.5mm (N-S x E-W as placed; pin 1 = NW). Pads 1.5mm/drill 0.8
  (lead 0.5x0.25mm). The isolation boundary runs N-S between the columns.
- Pico2_Socket_2x20 : the Raspberry Pi Pico 2 socket = 2x 1x20 female
  headers, rows 17.78mm apart, 2.54mm pitch (Pico 2 DS sec 3.1); pins
  1..20 down the WEST row, 21..40 up the EAST row, pin 1 = NW. Pads
  1.7/drill 1.0. Body 21 x 51mm silk outline for the module envelope.
- TerminalBlock_KF350_2P : KF350 3.5mm screw terminal (the std KiCad
  bornier is 5.08mm — wrong pitch). Pads 2.6/drill 1.2, pad 1 rect.
- IDC_2x16_Keyed : XKB X9555WV 2x16 shrouded IDC box header (std lib
  stops at 2x08-class). 32 pads 1.7/drill 1.0, columns 2.54, rows 2.54;
  pin 1 = NW (odd row north), key notch on the SOUTH shroud wall marked
  in silk. Shroud 46.6 x 8.8mm.

No FootprintLoad/Save (SWIG traps) — plain s-expr text.
Run: python3 03_src/make_lib.py
"""
from pathlib import Path

HERE = Path(__file__).parent
LIB = HERE / "lib" / "cookhub.pretty"
LIB.mkdir(parents=True, exist_ok=True)


def header(name, descr):
    return (f'(footprint "{name}" (version 20221018) (generator make_lib)\n'
            f'  (layer "F.Cu") (descr "{descr}") (attr through_hole)\n')


def tht_pad(num, x, y, size, drill, shape="circle"):
    return (f'  (pad "{num}" thru_hole {shape} (at {x:.3f} {y:.3f}) '
            f'(size {size:.2f} {size:.2f}) (drill {drill:.2f}) '
            f'(layers "*.Cu" "*.Mask") (remove_unused_layers no))\n')


def silk_rect(x0, y0, x1, y1, layer="F.SilkS", w=0.15):
    out = ""
    for (ax, ay, bx, by) in [(x0, y0, x1, y0), (x1, y0, x1, y1),
                             (x1, y1, x0, y1), (x0, y1, x0, y0)]:
        out += (f'  (fp_line (start {ax:.2f} {ay:.2f}) (end {bx:.2f} {by:.2f})'
                f' (stroke (width {w}) (type solid)) (layer "{layer}"))\n')
    return out


def texts(name):
    return (
        f'  (property "Reference" "REF**" (at 0 0 0) (layer "F.SilkS") (uuid "00000000-0000-0000-0000-00000000000a")'
        f' (effects (font (size 1 1) (thickness 0.15))))\n'
        f'  (property "Value" "{name}" (at 0 0 0) (layer "F.Fab") (uuid "00000000-0000-0000-0000-00000000000b")'
        f' (effects (font (size 1 1) (thickness 0.15))))\n')


# ------------------------------------------------- Standex DIP reed relay
# local frame: columns x=-3.81 (coil) / +3.81 (contact); rows y=-7.62 / +7.62
f = header("Relay_StandexDIP_1A_pinout12",
           "Standex DIP05-1A72 reed relay, pinout 12: coil 1/7 west, contacts 14/8 east (DS p.3)")
f += texts("DIP05-1A72-12L")
f += tht_pad("1", -3.81, -7.62, 1.5, 0.8, "rect")
f += tht_pad("7", -3.81, 7.62, 1.5, 0.8)
f += tht_pad("8", 3.81, 7.62, 1.5, 0.8)
f += tht_pad("14", 3.81, -7.62, 1.5, 0.8)
f += silk_rect(-3.25, -9.65, 3.25, 9.65)
f += silk_rect(-3.15, -9.55, 3.15, 9.55, layer="F.Fab", w=0.1)
# pin-1 marker (NW)
f += ('  (fp_circle (center -4.6 -9.2) (end -4.3 -9.2)'
      ' (stroke (width 0.2) (type solid)) (fill solid) (layer "F.SilkS"))\n')
f += silk_rect(-4.9, -9.95, 4.9, 9.95, layer="F.CrtYd", w=0.05)
f += ")\n"
(LIB / "Relay_StandexDIP_1A_pinout12.kicad_mod").write_text(f)

# ------------------------------------------------------- Pico 2 socket
f = header("Pico2_Socket_2x20",
           "Raspberry Pi Pico 2 socket: 2x 1x20 female 2.54mm, rows 17.78mm (Pico 2 DS 3.1)")
f += texts("Pico2_Socket")
for i in range(20):
    y = -24.13 + i * 2.54
    f += tht_pad(str(i + 1), -8.89, y, 1.7, 1.0, "rect" if i == 0 else "circle")
    f += tht_pad(str(40 - i), 8.89, y, 1.7, 1.0)
f += silk_rect(-10.5, -25.5, 10.5, 25.5)
f += silk_rect(-10.4, -25.4, 10.4, 25.4, layer="F.Fab", w=0.1)
f += ('  (fp_circle (center -11.3 -24.13) (end -11.0 -24.13)'
      ' (stroke (width 0.2) (type solid)) (fill solid) (layer "F.SilkS"))\n')
f += ('  (fp_text user "USB END" (at 0 -24.5 0) (layer "F.Fab")'
      ' (effects (font (size 1 1) (thickness 0.15))))\n')
f += silk_rect(-11.6, -26.0, 11.6, 26.0, layer="F.CrtYd", w=0.05)
f += ")\n"
(LIB / "Pico2_Socket_2x20.kicad_mod").write_text(f)

# --------------------------------------------------- KF350 3.5mm terminal
f = header("TerminalBlock_KF350_2P", "KF350 3.5mm 2P screw terminal (C474892)")
f += texts("KF350-2P")
f += tht_pad("1", -1.75, 0, 2.6, 1.2, "rect")
f += tht_pad("2", 1.75, 0, 2.6, 1.2)
f += silk_rect(-3.5, -3.4, 3.5, 3.6)
f += silk_rect(-3.4, -3.3, 3.4, 3.5, layer="F.Fab", w=0.1)
f += silk_rect(-3.8, -3.7, 3.8, 3.9, layer="F.CrtYd", w=0.05)
f += ")\n"
(LIB / "TerminalBlock_KF350_2P.kicad_mod").write_text(f)

# ------------------------------------------------------ IDC 2x16 keyed
# columns 2.54 (16), rows 2.54 (2); pin1 NW; odd pins north row.
f = header("IDC_2x16_Keyed", "XKB X9555WV-2x16 shrouded keyed IDC box header (C692429)")
f += texts("X9555WV-2x16")
for col in range(16):
    x = (col - 7.5) * 2.54
    f += tht_pad(str(2 * col + 1), x, -1.27, 1.7, 1.0,
                 "rect" if col == 0 else "circle")
    f += tht_pad(str(2 * col + 2), x, 1.27, 1.7, 1.0)
f += silk_rect(-23.3, -4.55, 23.3, 4.55)
f += silk_rect(-23.2, -4.45, 23.2, 4.45, layer="F.Fab", w=0.1)
# key notch marker: south wall center
f += ('  (fp_line (start -2.5 4.55) (end 2.5 4.55)'
      ' (stroke (width 0.5) (type solid)) (layer "F.SilkS"))\n')
f += ('  (fp_circle (center -24.1 -1.27) (end -23.8 -1.27)'
      ' (stroke (width 0.2) (type solid)) (fill solid) (layer "F.SilkS"))\n')
f += silk_rect(-23.6, -4.85, 23.6, 4.85, layer="F.CrtYd", w=0.05)
f += ")\n"
(LIB / "IDC_2x16_Keyed.kicad_mod").write_text(f)

print(f"cookhub.pretty: {len(list(LIB.glob('*.kicad_mod')))} footprints written")
