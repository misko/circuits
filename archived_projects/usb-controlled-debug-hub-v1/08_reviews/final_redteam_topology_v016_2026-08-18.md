subject: usb-controlled-debug-hub-v1 v0.1.6-2026-08-18 staging
date: 2026-08-18
reviewer: redteam-agent (GPT-5, topology/protection/ratings-lens)
context-given: full-tree; fresh exact-hash review using primary manufacturer authorities
source_commit: 14ffbbeb6db47e480898932303a0ef77d91bc83f
board_sha256: 088c5724c4259d727fff9093a71a7c41b903ad8022ad798c0ebedff2d0e08d18
schematic_sha256: 3948caded0e7cc4e695d6338786dfb9fbe0cd2bec106673619b36a2fc14e8023
netlist_sha256: d84493f6cf7c991aeee089e40af0181f258271cfb54f47127cfeb20b10ad22de
bom_sha256: ce1adf59be3536cc2dfc82cb2482d5739eb7288527899a82cbe6c8d5de0ec2f3
cpl_sha256: 4491024fcf06462f07fe3ba681318ce4e5598a3ea9f7c9e0915c0839de708e67
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING

# Fresh adversarial topology / electrical review

## Verdict

The v0.1.6 electrical design is **SOUND for release staging**. ADR-0011 closes
the prior USB2517I VBUS_DET threshold defect, and fresh regeneration introduced
no topology, pin, placement, copper, or CPL-coordinate regression.

This is **not order authorization**. Exact quantity-5 JLCPCB allocation and
uploader evidence remain absent, so the independent order verdict is
`BLOCKED-SOURCING`.

Severity counts: **P0 0, P1 0, P2 1**. Findings/notes graded: **1/1**.
Functional blocks traced: **6/6**. Critical regenerated identities hashed:
**6/6**. ADR-0011 electrical predicates: **8/8**.

## ADR-0011 full-corner re-derivation — PASS

Exact realized circuit:

```text
J_UP.1 USB_UP_VBUS
  -> R_VBUS_TOP = 47 kOhm, 1%, C25792
  -> HUB_VBUS_SENSE = U_HUB.44 VBUS_DET
  -> R_VBUS_BOT = 100 kOhm, 1%, C25741
  -> GND
```

Primary limits:

- Microchip USB2517 Hardware Design Checklist `DS00004211A`, section 5.1:
  alternate divider values are allowed if the connector-to-detector path is
  high impedance and VBUS_DET is sufficient across VBUS = 4.5–5.5 V.
- Microchip USB2517I data sheet `DS00001598C`, Table 8-2:
  `VIH(min)=2.0 V`, `VIL(max)=0.8 V`, input leakage `IIL=-10..+10 uA`.
- `DS00001598C`, section 8.2: a powered I/O pin may operate to 5.5 V while all
  3.3 V supplies remain at or above 3.0 V. Section 8.1 gives 5.5 V as the I/O
  absolute maximum.

Independent full-corner calculation:

```text
VDET = (VBUS / RTOP - ILEAK_SINK) / (1/RTOP + 1/RBOT)

minimum HIGH:
  VBUS = 4.5 V, RTOP = 47.47 kOhm, RBOT = 99 kOhm,
  ILEAK_SINK = 10 uA
  VDET_MIN = 2.720725746 V
  margin above VIH(min) = 0.720725746 V

maximum detector voltage:
  VBUS = 5.5 V, RTOP = 46.53 kOhm, RBOT = 101 kOhm,
  leakage sources 10 uA into the node
  VDET_MAX = 4.083883278 V
  margin below 5.5 V powered-I/O maximum = 1.416116722 V
```

Nominal divider current at 5.0 V is `5/(47k+100k)=34.0 uA`. This is a
high-impedance sense path and preserves isolation between upstream VBUS and
the self-powered 5 V trunk. When VBUS is absent, the 100 kOhm lower leg holds
VBUS_DET low; there is no alternate source on the net.

Result: **8/8 PASS** — upper value, lower value, both endpoint nets, pin 44
net, low-range HIGH threshold, high-range pin voltage, and upstream/trunk
isolation.

## Regeneration-delta proof — PASS

Fresh machine comparison against the immediately preceding exact candidate
showed:

- normalized net name -> `{ref.pin}` connectivity: **0 differences**;
- PCB source: exactly one semantic difference, R_VBUS_TOP `Value` changes
  `100kOhm -> 47kOhm`; no coordinate, footprint, pad, track, via, zone, net,
  outline, or model transform changed;
- BOM: R_VBUS_TOP leaves the 100 kOhm group and appears once as
  `47kOhm / 0402WGF4702TCE / C25792`;
- CPL: only the R_VBUS_TOP value field changes; its `(78.0,-60.0,top,0.0)`
  placement is unchanged;
- independent native ERC: 0 violations;
- independent native DRC: 0 error-severity violations, 0 unconnected items,
  0 schematic-parity findings. The standalone archive context reports 12
  library-resolution warnings; all 12 are the same missing project-library
  registration class, not copper or connectivity defects.

## Repeated topology trace — PASS

- Power entry remains J_PWR -> F_IN -> TPS259474L aggregate latch-off/reverse-
  blocking eFuse -> P5V_PROTECTED. The 3.3 V buck and all five TPS2557 inputs
  remain downstream.
- Upstream VBUS remains sense-only. It has no connection to P5V_RAW,
  P5V_FUSED, P5V_PROTECTED, VBUS_CTRL, or any external-port VBUS output.
- USB2517I port 1 feeds the onboard MCP2221A management device; physical ports
  2–5 feed external ports 1–4. PRTPWR and OCS_N mapping remains one-for-one.
- Each external power path is gated by `hub PRTPWR AND PWR_CMD`. Each data
  switch connects only when `PWR_EN AND DATA_CMD`; all commands/enables have
  hardware pulldowns and FSUSB42 OE has a disconnect-default pullup.
- USB2517I configuration remains internal-default/strap mode, self-powered,
  port 1 non-removable, ports 6/7 disabled, and port-1 data polarity swap
  paired with PRT_SWP1.
- Management sequencing remains coherent: the hub-controlled TPS2557 powers
  MCP2221A/MCP23017 from VBUS_CTRL; pull-downs keep all external outputs off
  before I2C commands exist.

## P2-1 — retain first-article power-ordering observation

`DS00004211A` deliberately describes the unpowered-hub case qualitatively:
the series impedance must minimize input leakage when upstream VBUS arrives
first. It gives no numeric injection-current acceptance limit. The 47 kOhm
upper leg is still high impedance and is allowed by the checklist's explicit
alternate-value rule, so this is not a design blocker. During first article,
measure external-5-V-off current from J_UP VBUS and confirm that applying
upstream VBUS alone neither raises 3V3_MAIN nor causes partial hub operation.
Then apply external 5 V and sweep upstream VBUS through 4.5 V while confirming
enumeration. This is a falsifiable production-evidence item, not an order-day
waiver.

## Commands and evidence

```text
sha256sum source/usb_controlled_debug_hub.{kicad_pcb,kicad_sch,net,tsx} \
  fab/bom.csv fab/cpl.csv
kicad-cli sch export netlist --format kicadxml -o /dev/stdout source/*.kicad_sch
diff -u <normalized-v0.1.5-net-map> <normalized-v0.1.6-net-map>
diff -u v0.1.5/source/*.kicad_pcb v0.1.6/source/*.kicad_pcb
diff -u v0.1.5/fab/bom.csv v0.1.6/fab/bom.csv
diff -u v0.1.5/fab/cpl.csv v0.1.6/fab/cpl.csv
kicad-cli sch erc --severity-all --format json --output /dev/stdout source/*.kicad_sch
kicad-cli pcb drc --severity-all --format json --output /dev/stdout source/*.kicad_pcb
```

The online primary checklist was verified at Microchip's official publication:
`https://ww1.microchip.com/downloads/aemDocuments/documents/UNG/ProductDocuments/DesignChecklist/USB2517-Hardware-Design-Checklist-00004211.pdf`.

