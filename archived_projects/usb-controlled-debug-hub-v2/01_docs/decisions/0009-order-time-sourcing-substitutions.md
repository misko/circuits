# ADR-0009: order-time sourcing substitutions

- Status: proposed for the v0.1.3 sourcing-only release
- Date: 2026-08-18
- Scope: assembly identity only; no copper, placement, value, topology, or firmware change

## Context

The JLC top-side component matcher reported zero assembly allocation for ten
otherwise valid BOM codes in v0.1.2. Fresh LCSC catalog reads found compatible
same-package candidates. The release contract provides a sourcing-supersede
path that requires an unchanged PCB, CPL and normalized Gerber/drill set while
changing MPN and LCSC together at source.

## Decision

Use these substitutions:

| Prior | Replacement | Requirement retained |
|---|---|---|
| C60491 / RC0402FR-07100KL | C481918 / CRCW0402100KFKED | 100k, 1%, 0402, 50V |
| C1525 / CL05B104KO5NNNC | C392963 / TCC0402X7R104K160AT | 100nF, X7R, 16V, 0402 |
| C60490 / RC0402FR-0710KL | C843837 / CRCW040210K0FKEE | 10k, 1%, 0402, 50V |
| C327368 / RC0402FR-07165KL | C2483395 / RMCF0402FT165K | 165k, 1%, 0402, 50V |
| C52923 / CL05A105KA5NQNC | C326568 / CC0402KRX5R8BB105 | 1uF, X5R, 25V, 0402 |
| C342660 / C3225X7R1C226KT000N | C55530 / CL32B226KOJNNNE | 22uF, X7R, 16V, 1210 |
| C77036 / GRM1885C1H332JA01D | C342849 / C1608C0G1H332JT000N | 3.3nF, C0G, 5%, 50V, 0603 |
| C105871 / RC0402FR-074K7L | C482193 / CRCW04024K70FKED | 4.7k, 1%, 0402, 50V |
| C6053 / 74LVC08APW,118 | C54411084 / 74LVC08APW | quad AND, TSSOP-14, 3.3V and overvoltage-tolerant inputs |
| C130056 / TPS2557DRBR | C2150199 / TPS2557QDRBRQ1 | active-high TPS2557, DRB-8, exposed pad, adjustable ILIM; 100 catalog units at mint time versus only 8 for the rejected C2149775 small-reel code |

## Release conditions

The substitutions are not an order authorization. Before payment:

1. JLC must show allocation for every replacement code on both assembly sides.
2. The resolved BOM echo must preserve the exact replacement MPNs and codes.
3. JLC rotation, polarity, THT, selective-via and impedance previews remain
   mandatory.
4. The v0.1.3 sourcing-supersede gate must prove PCB/CPL/copper identity to
   v0.1.2 and confine BOM changes to paired MPN/LCSC substitutions.

No firmware is generated or included.
