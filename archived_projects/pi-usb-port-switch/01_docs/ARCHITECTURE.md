# pi-usb-port-switch — architecture

Status: routed layout sealed for the initial hardware-only release. D3 and A5
lock the topology and VBUS envelope; 27 exact parts passed pinned-datasheet and
dated two-source qualification. The generated schematic, netlist and board
agree on 190 component identities and 282/282 electrical invariants.

## Required functional boundary

The board is four independent one-to-one inline USB channels, not an onboard
USB hub. Each uses a USB 3 Type-B upstream cable connection and a USB 3 Type-A
downstream receptacle. The PCB paths are identical: a USB 2 switch handles
D+/D- and a dual-channel USB 3 Gen 1 redriver with shutdown handles TX/RX. On a
Pi 4 or Pi 5, the two blue ports can run USB 3 Gen 1 while the other two use
only the backward-compatible USB 2 conductors. For each channel the Raspberry
Pi controls VBUS and all data pairs separately. Ground remains common.

| Power control | Data control | Required behavior |
|---|---|---|
| off | off | full disconnect except common ground/shield policy |
| on | off | downstream device remains powered; D+/D-, SuperSpeed TX and SuperSpeed RX are high impedance |
| on | on | normal USB connection |
| off | on | forbidden by hardware; resolves to data disconnected |

## Power tree

```text
external regulated 5 V input
  -> input reverse/fault protection
  -> protected 5 V trunk
       -> per-port 0.9 A current-limited reverse-protected switch x4
            -> downstream USB-A VBUS x4
       -> local 3.3 V logic/data-switch rail
```

Upstream Pi USB VBUS pins do not connect to the downstream 5 V rail and cannot
be back-powered. The source must hold 5.15-5.25 V at the board input and provide
at least 5 A; the downstream requirement is 4.75-5.25 V at each mated test plug
with all four ports loaded to 0.9 A.

## Net domains

The machine contract has USB 3 differential, USB 2 differential, protected
5 V trunk, four switched VBUS, 3.3 V, GPIO/control and ground-return classes.
USB pairs route on the outer layer over an uninterrupted inner ground
reference. Exact names and pre-layout limits live in
`../03_src/rules/nets.yaml`; the 90-ohm width/gap remains an order-time JLCPCB
stackup input rather than an unsupported source-stage claim.

## Stackup

The board uses four layers at JLCPCB's advanced tier: outer-layer USB pairs,
a solid adjacent ground plane, a power plane, and a secondary signal/ground
layer. Routed pairs use 0.25 mm width / 0.18 mm gap. These dimensions are a
layout constraint, not an impedance certificate: the exact named JLCPCB
stackup and the fabricator's 90-ohm differential solve remain mandatory
order-preview inputs before payment.

## Ground strategy

The signal return is not a user-switched function. The USB reference plane must
remain solid under connectors, ESD arrays, data switches and pair transitions.
Connector shells are tied to the board ground/shield reference and are not
GPIO-controlled. Ground is never disconnected by the channel controls.

## Critical geometries

USB differential-pair continuity through two connectors, ESD protection and
data switches is the principal geometry. The three pairs per channel must be
inventoried before routing. The SuperSpeed chain is a prototype claim because
the inline fixture adds a second cable segment and an active data path; the exact
release must bind trace length, insertion-loss guidance, unbroken return,
zero-via preference and first-article USB 3 link/throughput evidence.

## Interfaces

Four short standard USB 3 A-to-B cables connect the Pi ports to the board. A
40-pin Raspberry Pi GPIO ribbon/header carries eight commands: `PWR_EN[1:4]`
and `DATA_EN[1:4]`. The board does not mechanically align to either Pi. Use a
keyed or carefully indexed ribbon cable and verify pin 1 before power.

## Firmware boundary

No firmware is authorized. GPIO input pulls and logic must establish safe
states before Linux starts and when the Pi is unpowered.
