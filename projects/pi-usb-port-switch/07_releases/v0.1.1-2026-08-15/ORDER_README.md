# ORDER README — Pi USB port switch v0.1.1

DESIGN: PASS
SOURCING: CLEAR for five prototypes as measured 2026-08-15
ORDER: DO-NOT-ORDER until every uploader hold below is accepted
PRODUCTION: HOLD until the first-article plan passes

SUPERSEDES: v0.1.0-2026-08-15. This corrective release preserves identical
copper, BOM/CPL, drawings, STEP and reviewed board bytes, while correcting the
standalone source archive: the canonical root PCB is now byte-identical to the
live reviewed PCB, and `source/exact/` retains its original relative source
tree so custom models resolve without rewriting the PCB.

This is a hardware-only four-channel Raspberry Pi USB disconnect fixture.
It needs no firmware. It attempts USB 3 Gen 1 and accepts USB 2 as the fallback;
it makes no USB-IF compliance claim.

## Blocking JLCPCB uploader confirmations

1. Select **4 layers, advanced process** and a named controlled-impedance
   stackup. Ask JLCPCB to solve/confirm **90 ohm differential** for the shipped
   0.25 mm width / 0.18 mm gap geometry. Do not pay if the preview changes the
   copper or does not echo the selected stackup.
2. Select copper-paste fill plus copper cap for the complete **0.25 mm drill
   family only**: exactly 61 protected 0.35/0.25 mm via-in-pad barrels. Do not
   fill/cap the ordinary 0.20 mm or 0.30 mm drill families (688 vias).
3. Select top-side SMT plus JLCPCB through-hole/wave-selective assembly for
   `J1, J2, J3, J5, J7, J9`. Confirm their orientation and every THT hole in
   the placement/assembly preview.
4. Upload `fab/bom.csv` and `fab/cpl.csv`. Compare JLCPCB's resolved MPN/LCSC
   table against `fab/bom_echo_gate.txt`; reject any substitution or redirect.
   Compare rotations against `fab/rotation_human_gate.txt` and the six twin
   views before payment.
5. Order **five prototypes only**. Production remains blocked on the supplied
   first-article electrical, thermal and USB qualification plan.

## Fabrication package

- Board: `pi_usb_port_switch`, 150 x 120 mm, four layers
- Gerbers/drills: `fab/pi_usb_port_switch_gerbers.zip`
- Copper: use the stackup/copper weight accepted in the controlled-impedance
  preview; do not infer impedance from trace width alone
- Solder mask/silkscreen: as plotted
- Quantity: 5
- Assembly side: top
- Fitted by JLC: 185 CPL designators
- Deliberately not on CPL: `F1, J4, J6, J8, J10`

## Required hand assembly

- `J4/J6/J8/J10`: exact Wurth 692121030100 USB 3 Type-A receptacles, sourced
  from an authorized distributor. Do not fit a pin-compatible-looking
  substitute without a new land/pin/model review.
- `F1`: two Keystone 3568 MINI-blade fuse clips per board, then one Littelfuse
  029707.5WXNV 7.5 A MINI fuse. One CPL centroid cannot describe two clips.
- Inspect every USB signal pin and shell stake after hand soldering.

## External connections and safe first power

Use a regulated **5.15-5.25 V, at least 5 A** supply at J1, observing polarity.
The upstream Raspberry Pi USB VBUS pins are intentionally isolated and do not
power the downstream ports. Ground remains common and is never switched.

Connect J2 to a Raspberry Pi 4 or 5 40-pin header with pin 1 correctly indexed.
The eight commands are:

| Port | Power command | Data command |
|---|---|---|
| 1 | GPIO17, physical pin 11 | GPIO27, physical pin 13 |
| 2 | GPIO22, physical pin 15 | GPIO23, physical pin 16 |
| 3 | GPIO24, physical pin 18 | GPIO25, physical pin 22 |
| 4 | GPIO5, physical pin 29 | GPIO6, physical pin 31 |

All controls have hardware pull-downs. Floating, reset or unpowered GPIOs make
all channels fully off. Hardware interlocks force data off whenever that port's
power command is off. Logic truth table:

| PWR_EN | DATA_EN | Result |
|---:|---:|---|
| 0 | 0 | VBUS off, data disconnected |
| 0 | 1 | VBUS off, data disconnected |
| 1 | 0 | VBUS on, all data disconnected |
| 1 | 1 | VBUS on, USB 2/SuperSpeed path connected |

For first power, leave the Pi disconnected, use a current-limited bench supply
at 5.20 V / 0.25 A, and follow
`verification/FIRST_ARTICLE_TEST_PLAN.md`. Do not assume a generic 5.0 V
adapter can meet the guaranteed 4.75 V minimum at a loaded downstream plug.

## Archive and evidence

`source/pi_usb_port_switch.kicad_pcb` is byte-identical to the live reviewed
board. Open `source/exact/04_kicad/pi_usb_port_switch.kicad_pcb` for the
standalone tree whose original `../03_src/lib` paths resolve the vendored
custom footprints and models without mutating the canonical PCB. `pdf/`
contains the human schematic,
layer and assembly drawings. `3d/` contains a component-bearing STEP with all
190 fitted model assignments resolved. `verification/` contains DRC/ERC,
parity, power/SI/via audits, sourcing evidence, twin registration and reviews.
