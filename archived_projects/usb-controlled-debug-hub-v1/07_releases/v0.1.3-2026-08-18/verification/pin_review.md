review_kind: pin_review
subject: usb-controlled-debug-hub v0.1.2 final physical pin and polarity review
date: 2026-08-17
reviewer: Codex independent package, connector and signal-direction review
evidence_scope: exact staged PCB, netlist, BOM, 23 generated pin dossiers and cited part records
board_sha256: c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Final physical-pin review

Twenty-three staged dossiers cover the input fuse and all critical connectors,
USB devices, power devices, logic, controller/expander and crystal. I traced
the board nets through the staged netlist rather than accepting net names as
proof.

The following critical maps are internally and datasheet consistent:

- `J_UP` TE 292304-1: 1=upstream VBUS sense, 2=D-, 3=D+, 4=GND, shell=GND.
- `U_HUB` USB2517I: upstream 58/59 are D-/D+; downstream physical ports 1--5
  occupy 1/2, 3/4, 6/7, 8/9 and 11/12; PRTPWR/OCS pins map consistently to the
  management channel and external ports; pins 25/62 are the two 1.8 V bypass
  outputs, pin 63 is RBIAS and exposed pad 65 is GND.
- `U_DATA1..4` FSUSB42: SEL is low and HSD2 is NC. Logical D+ deliberately
  traverses package channel 6-to-4 and logical D- channel 7-to-3. Both ends are
  swapped as a complete symmetric channel assignment, so this is not a USB
  polarity inversion. OE is active-high disconnect and has a physical pull-up.
- `U_ESD_UP` and `U_ESD1..4`: pins 1/2 are the two symmetric USB shunts and pin
  3 is the ground return. The connector-side assignments preserve D+/D-.
- `U_PWR_CTRL` and `U_PWR1..4` TPS2557: 1/EP=GND, 2/3=IN, 4=active-high EN,
  5=ILIM, 6/7=OUT and 8=active-low open-drain fault. No channel crosses another
  channel's power or OCS net.
- `U_AGG` TPS259474L: 5=IN on `P5V_FUSED`, 6=OUT on `P5V_PROTECTED`, 8=GND,
  with EN/UVLO, OVLO, PGTH, DVDT, ILM and ITIMER on the intended support nets.
  The four apparent 0.005 mm custom-pad base sizes in the dossier are anchors
  for explicit polygon primitives, not missing lands.
- `U_BUCK`, `U_CTRL`, `U_EXP`, both 74LVC08 devices, the four 2N7002 devices
  and `Y_HUB` have the expected top-view winding, supply pins, reset pins and
  exposed-pad/ground assignments. The 5 V expander command levels enter
  5.5 V-tolerant 74LVC08 inputs; no 5 V command is applied to a non-tolerant
  3.3 V pin.
- `F_IN` has both duplicated pad-1 holes on `P5V_RAW` and both pad-2 holes on
  `P5V_FUSED`. It is intentionally absent from BOM/CPL and therefore requires
  the exact holder plus exact 4 A fuse to be installed and continuity-checked
  manually.

## Resolved exact-connector finding

The independent review initially raised a P1 because the one-page manufacturer
drawing does not print contact numbers. That finding is now closed by
`connector_pin_authority.md` and the retained exact-code JLC/EasyEDA library.
The board's
board assigns the four Kinghelm `KH-AF90DIP-112` tails left-to-right as
1=VBUS, 2=D-, 3=D+, 4=GND and the footprint geometry matches the vendor's
2.5/2.0/2.5 mm signal spacing and 13.240 mm shell spacing. The exact JLC code
`C503996` library names its paired symbol pins 1=VCC, 2=D-, 3=D+, 4=GND and
places those same numbered pads on the same asymmetric row, with the same shell
field and mating-mouth direction. After a pure +3.49-mm X translation its pad
coordinates coincide with the project footprint. Symbol and footprint hashes
are retained in `connector_pin_authority.md`; this is exact-part evidence, not
generic USB convention.

The design verdict is therefore SOUND. The order verdict remains DO-NOT-ORDER
until the JLC THT/rotation/polarity previews, stackup/impedance solve, and
selective-via process are explicitly accepted. The separate exact
connector-facing views were approved on 2026-08-17 and are bound in
`orientation_approval.md`.
