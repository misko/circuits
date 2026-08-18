# v0.1.4 sourcing candidate — uploader checkpoint

This is a **candidate BOM, not a release and not an order authorization**.
It exists before source adoption so a failed JLCPCB availability check cannot
force another schematic/PCB/release backtrack.

The nine v0.1.3 lines reported unavailable by the JLCPCB PCBA interface are
replaced as follows. Electrical/package qualification is complete enough for
the availability checkpoint; exact source dossiers and rotation evidence are
updated only after JLCPCB returns `AVAILABLE` for all 33 lines.

| Function | Rejected v0.1.3 code | Candidate code / MPN | Candidate filter |
|---|---|---|---|
| 100 kΩ, 1%, 0402 | C481918 | C25741 / 0402WGF1003TCE | Basic; 50 V, 62.5 mW, 100 ppm/°C |
| 100 nF, 16 V, X7R, 0402 | C392963 | C60474 / CC0402KRX7R7BB104 | X7R, 16 V, 10% |
| 10 kΩ, 1%, 0402 | C843837 | C25744 / 0402WGF1002TCE | Basic; 50 V, 62.5 mW, 100 ppm/°C |
| 165 kΩ, 1%, 0402 ILIM | C2483395 | C2076721 / ERJ2RKF1653X | 1%, 0402; TPS2557 current-limit value unchanged |
| 1 µF, 25 V, X5R, 0402 | C326568 | C52923 / CL05A105KA5NQNC | Basic; original qualified exact part |
| 22 µF, 16 V+, X7R, 1210 | C55530 | C21397 / GRM32ER71E226KE15L | 25 V, X7R, 10%; rating is stronger |
| 3.3 nF, 50 V, C0G, 5%, 0603 | C342849 | C107048 / CC0603JRNPO9BN332 | NP0/C0G, 5%, timing value unchanged |
| 4.7 kΩ, 1%, 0402 | C482193 | C25900 / 0402WGF4701TCE | Basic; 50 V, 62.5 mW, 100 ppm/°C |
| active-high adjustable USB switch, DRB-8 | C2150199 | C130056 / TPS2557DRBR | Original exact design MPN and footprint |

The public JLC/LCSC catalog endpoint reported non-zero stock for all nine on
2026-08-18, but that is deliberately **not** treated as PCBA availability.
Only the quantity-expanded JLCPCB BOM/uploader result may complete this gate.

## Required operator action

1. Upload `bom.csv` in the existing JLCPCB PCBA project for quantity 5.
2. Confirm the uploader resolves each requested LCSC code exactly; do not
   accept an automatic substitute.
3. Enter JLCPCB's returned status and available quantity in
   `prelayout_response.csv`. Preserve a screenshot/export link or filename in
   `Evidence`.
4. Do not edit `prelayout_request.json`; it is hash-bound to this candidate.

After all 33 rows grade `AVAILABLE`, the nine identities can be adopted
source-first, the board regenerated, and an exact final BOM checked again for
`ALLOCATED` before the v0.1.4 release is sealed.
