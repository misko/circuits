# ADR-0010: v0.1.4 orderable sourcing supersede

- Status: accepted for the v0.1.4 sourcing-only release
- Date: 2026-08-18
- Scope: assembly identity only; no value, footprint, topology, placement,
  copper, CPL, or firmware change

## Context

The live JLCPCB BOM matcher later reported zero availability for nine v0.1.3
rows. A replacement-candidate upload resolved those rows, but the shortened
`74LVC08APW / C54411084` identity did not match at all. The newly introduced
pre-layout procurement gate also requires MOQ and gross-surplus cost to be
evaluated independently from catalog stock before a part is frozen.

## Decision

Adopt these paired MPN/LCSC substitutions at TSX source:

| Rejected v0.1.3 identity | v0.1.4 identity | Retained requirement |
|---|---|---|
| C481918 / CRCW0402100KFKED | C25741 / 0402WGF1003TCE | 100k, 1%, 0402 |
| C392963 / TCC0402X7R104K160AT | C60474 / CC0402KRX7R7BB104 | 100nF, X7R, 16V, 0402 |
| C843837 / CRCW040210K0FKEE | C25744 / 0402WGF1002TCE | 10k, 1%, 0402 |
| C2483395 / RMCF0402FT165K | C2076721 / ERJ2RKF1653X | 165k, 1%, 0402 ILIM |
| C326568 / CC0402KRX5R8BB105 | C52923 / CL05A105KA5NQNC | 1uF, X5R, 25V, 0402 |
| C55530 / CL32B226KOJNNNE | C21397 / GRM32ER71E226KE15L | 22uF, X7R, 25V, 1210 |
| C342849 / C1608C0G1H332JT000N | C107048 / CC0603JRNPO9BN332 | 3.3nF, C0G, 5%, 0603 |
| C482193 / CRCW04024K70FKED | C25900 / 0402WGF4701TCE | 4.7k, 1%, 0402 |
| C2150199 / TPS2557QDRBRQ1 | C130056 / TPS2557DRBR | active-high TPS2557, DRB-8 |
| C54411084 / 74LVC08APW | C6053 / 74LVC08APW,118 | exact Nexperia PW TSSOP-14 identity |

`C6053` and `C130056` restore the exact qualified design identities already
used and geometry-checked in v0.1.2. The passive replacements retain or exceed
the reviewed electrical and package requirements.

## Release conditions

1. The sourcing-supersede gate must prove byte-identical PCB and CPL plus
   semantically identical Gerbers/drills against v0.1.3.
2. The exact BOM must be re-uploaded; all rows must resolve without automatic
   substitution.
3. A schema-v2 JLC receipt must separately accept availability and procurement
   economics at the actual build quantity. Public catalog stock is advisory.
4. Order-time allocation, BOM echo, rotation/polarity, THT, selective-via and
   impedance previews remain mandatory.
5. No firmware is generated or included.
