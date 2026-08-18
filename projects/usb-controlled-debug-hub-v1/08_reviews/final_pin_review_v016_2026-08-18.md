subject: usb-controlled-debug-hub-v1 v0.1.6-2026-08-18 staging
date: 2026-08-18
reviewer: pin-review (GPT-5, fresh exact-hash physical-pin lens)
context-given: full-tree; exact staging archive plus primary manufacturer pin tables
source_commit: 14ffbbeb6db47e480898932303a0ef77d91bc83f
board_sha256: 088c5724c4259d727fff9093a71a7c41b903ad8022ad798c0ebedff2d0e08d18
schematic_sha256: 3948caded0e7cc4e695d6338786dfb9fbe0cd2bec106673619b36a2fc14e8023
netlist_sha256: d84493f6cf7c991aeee089e40af0181f258271cfb54f47127cfeb20b10ad22de
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING

# Fresh exact-hash pin review

## Verdict and coverage

Pin identity and realized nets are **SOUND**. Critical physical instances
reviewed: **33/33**. Primary package/pin-map families re-derived: **15/15**.
Critical regenerated board/netlist identities: **3/3**. P0/P1/P2 findings:
**0/0/0**.

Order remains `BLOCKED-SOURCING` because pin correctness does not substitute
for exact JLCPCB allocation and uploader previews.

## Instance coverage

| family | instances | result |
|---|---:|---|
| power entry, fuse, aggregate eFuse, buck | J_PWR, F_IN, U_AGG, U_BUCK (4) | PASS 4/4 |
| hub upstream and clock | J_UP, U_ESD_UP, U_HUB, Y_HUB (4) | PASS 4/4 |
| TPS2557 power cells | U_PWR_CTRL, U_PWR1–U_PWR4 (5) | PASS 5/5 |
| USB data switches and pull-down FETs | U_DATA1–4, Q_DATA1–4 (8) | PASS 8/8 |
| downstream ESD and connectors | U_ESD1–4, J_PORT1–4 (8) | PASS 8/8 |
| management and interlocks | U_CTRL, U_EXP, U_AND_PWR, U_AND_DATA (4) | PASS 4/4 |

Total: **33/33**.

## Critical pin conclusions

- `J_PWR.1=P5V_RAW`, `J_PWR.2=GND`; fuse pins remain
  `1=P5V_RAW`, `2=P5V_FUSED`.
- TPS259474L RPW pin map is preserved: 1 EN/UVLO, 2 OVLO, 4 PGTH/GND in this
  implementation, 5 IN, 6 OUT, 7 DVDT, 8 GND, 9 ILM, 10 ITIMER; unused pin 3
  PG is explicitly unconnected.
- AP63203Q TSOT-23-6 is `1 FB/output sense`, `2 EN`, `3 VIN`, `4 GND`, `5 SW`,
  `6 BST`; the fixed 3.3 V part correctly ties pin 1 to 3V3_MAIN.
- USB2517I QFN-64+EP power, upstream, downstream, strap, PRTPWR/OCS, crystal,
  RBIAS, regulator-cap and exposed-pad assignments match `DS00001598C`.
  Specifically, pin 44 is HUB_VBUS_SENSE, pins 58/59 are upstream DM/DP,
  pins 60/61 are XTAL2/XTAL1, pin 63 is RBIAS, and pin 65 EP is GND.
- R_VBUS_TOP and R_VBUS_BOT still terminate only at
  `J_UP.1 -> HUB_VBUS_SENSE/U_HUB.44 -> GND`; the value-only regeneration did
  not move or remap their pads.
- TPS2557 DRB pins are consistent on all 5/5 instances: 1/9 GND/EP, 2/3 IN,
  4 active-high EN, 5 ILIM, 6/7 OUT, 8 active-low open-drain FAULT.
- FSUSB42 MSOP-10 is consistent on all 4/4 instances: 1 VCC, 2 SEL=GND,
  3 D+, 4 D-, 5 GND, 6 HSD1-, 7 HSD1+, 8/9 unused HSD2, 10 active-high OE.
  The intentional symmetric-channel lane assignment preserves logical USB
  D+/D- from each hub port to connector pins 3/2.
- PESD2USB3UX SOT-23 is consistent on all 5/5 instances: pins 1/2 are line
  cathodes and pin 3 is common-anode GND.
- 2N7002K SOT-23 is consistent on all 4/4 instances: pin 1 gate, pin 2 source
  to GND, pin 3 drain to FSUSB42 OE.
- MCP2221A SOIC-14 pins 1/11/12/13/14 are VDD/VUSB/D-/D+/VSS; I2C is pins
  9/10 and reset is pin 4. MCP23017 SSOP-28 pins 9/10 are VDD/VSS, 12/13 are
  SCL/SDA, 15–17 address low, 18 reset, and GPA0–7 pins 21–28 are the eight
  commands.
- 74LVC08A TSSOP-14 maps four `A,B -> Y` gates as 1,2->3; 4,5->6;
  9,10->8; 12,13->11 with GND=7 and VCC=14. Both devices follow that map.
- USB Type-B and four Type-A connectors remain VBUS=1, D-=2, D+=3, GND=4;
  shield lands are grounded. J_PWR/USB connector placement was not changed by
  ADR-0011.

## Regression proof

Normalized exact schematic net connectivity contains **0 differences** from
the immediately preceding candidate. Exact PCB source diff contains one and
only one changed field: R_VBUS_TOP's displayed value. Native DRC independently
reports 0 unconnected items and 0 schematic-parity findings. BOM/CPL diffs are
limited to the intended 47 kOhm identity/value and preserve its footprint,
side, coordinate, and rotation.

No pin-map, exposed-pad, polarity, connector, USB-lane, power-domain, or
control-line regression was found.

