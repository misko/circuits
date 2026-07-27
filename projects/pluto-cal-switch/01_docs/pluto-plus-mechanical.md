# PlutoPlus SMA port geometry — measured, with its uncertainty stated

Source of every number below: the PlutoPlus open-hardware repo
<https://github.com/plutoplus/plutoplus>, files `sch/Top.pdf` and
`sch/PLUTOX_SDR-V1.0-20201212.pdf`. Measured 2026-07-27.

**The repo publishes NO PCB source and NO dimensioned mechanical drawing.**
There is no `.kicad_pcb`, no Altium, no DXF, no STEP. `sch/Top.pdf` is an
undimensioned vector assembly plot. Everything here is therefore DERIVED from
that plot, and the derivation and its error bars are given so the next reader
can check them rather than trust them.

## Port identities — DEFINITIVE, read from the schematic

The schematic names four SMA connectors, all with value `SMA-L`:

| refdes | net pair | port |
|---|---|---|
| **U7** | `TX2A_P` / `TX2A_N` | **TX2** |
| **U10** | `RX2A_P` / `RX2A_N` | **RX2** |
| **U14** | `RX1A_P` / `RX1A_N` | **RX1** — sheet titled "RX SMA CONNECTOR" |
| **U12** | `TX1A_P` / `TX1A_N` | **TX1** — sheet titled "TX SMA CONNECTOR" |

Physical order along the edge, left to right in the Top.pdf view:

    U7        U10       U14       U12
    TX2       RX2       RX1       TX1

**The two RX ports are ADJACENT, in the middle.** That is good news for this
board: the two loopback runs that must be length-matched terminate at
neighbouring connectors, and the TX we tap is on one end or the other.

## Scale calibration — two independent known packages

`Top.pdf` is an A4 MediaBox with a content transform, so PDF units are not
directly mm. The plot was rendered at 600 dpi and calibrated against two
packages whose size is fixed by their part number, both found in the schematic:

| package | part | measured | nominal | error |
|---|---|---|---|---|
| BGA-400, CLG400 | `XC7Z010-1CLG400I` | 396 × 397 px = 16.76 × 16.81 mm, aspect **1.003** | 17.0 × 17.0 mm | 1.4 % |
| CSP-BGA-144 | `AD9361BBCZ` | 240 × 238 px = 10.16 × 10.08 mm, aspect **0.992** | 10.0 × 10.0 mm | 1.6 % |

Both land within ~1.5 % of nominal and both measure square, which is what a
stroke-width error on a drawn courtyard outline looks like. **Scale = 23.622
px/mm — the plot is 1:1 at 600 dpi.**

Two independent references agreeing is the reason to believe this at all; one
would have been a coincidence.

## Measured geometry

Connector footprint outlines, all four **192.0 px wide — identical to 0.1 px**,
which is itself evidence the extraction is sound:

| span | px | mm |
|---|---|---|
| connector outline width | 192.0 | **8.13** |
| **U7 (TX2) → U10 (RX2)** | 284.0 | **12.02** |
| **U10 (RX2) → U14 (RX1)** | 274.0 | **11.60** |
| **U14 (RX1) → U12 (TX1)** | 283.0 | **11.98** |
| U7 → U12 total span | 841.0 | **35.60** |
| board outline | 1574 × 2350 | **66.63 × 99.48** |

## THE FINDING: the pitch is NOT uniform

**12.02 / 11.60 / 11.98 mm.** The RX2↔RX1 gap is ~0.42 mm tighter than the two
outer gaps.

This is not measurement noise, and it was confirmed a second way — by the gaps
between connector bodies rather than between centres:

    U7→U10 gap 92 px    U10→U14 gap 82 px    U14→U12 gap 91 px

Same asymmetry, same magnitude, derived from different pixels. And all four
outline widths came out identical to 0.1 px, so the extraction is not drifting.

**Consequence for a direct-mount daughter board: a uniform connector pitch will
not mate.** The mating connectors must be placed at the measured non-uniform
spacing.

## Uncertainty — and why it probably blocks a rigid direct mount

The scale carries ~1.5 % uncertainty from the courtyard-vs-package stroke
question. On a 12 mm pitch that is **±0.18 mm**, and the error accumulates
across the span: **±0.5 mm over the 35.60 mm U7→U12 reach.**

The pitch RATIOS (284 : 274 : 283) are exact and scale-free — those are
trustworthy. The absolute millimetres are not, to better than ±1.5 %.

For a rigid three-connector SMA mount, ±0.5 mm of accumulated position error is
very likely too much: SMA mating does not tolerate that much lateral offset
across three simultaneous engagements. **This number is not yet safe to commit
to copper.**

Resolving it needs ONE of:

1. **A caliper measurement on a physical PlutoPlus** — centre-to-centre between
   adjacent SMA bodies, all three gaps. This collapses the uncertainty to the
   caliper's, and is by far the cheapest option. It is the recommended path.
2. **The vendor's mechanical drawing**, if one exists outside this repo.
3. **A float/blind-mate design** that tolerates ±0.5 mm — slotted mounting, a
   float-mount SMA, or short semi-rigid jumpers on one or more ports, which
   partially concedes the no-cables goal.

## Revision caveat — the two files disagree about which board they describe

`Top.pdf` is titled **`PLUTOX-SDR-TV4.0-202111`** (Nov 2021). The schematic is
**`PLUTOX_SDR-V1.0-20201212`** (Dec 2020). Different version strings, roughly a
year apart.

The refdes U7/U10/U12/U14 and their net names appear consistently in both, so
the PORT IDENTITIES are safe. The GEOMETRY, however, comes only from the TV4.0
plot, and nothing here proves the user's physical unit is that revision. The
caliper check in option 1 settles this too.

## Still unestablished

- **SMA gender on the PlutoPlus.** Almost certainly jacks (female) — the
  universal SDR convention — but the value string `SMA-L` names no manufacturer
  part and the plot cannot show gender. This decides the daughter board's
  mating gender and is trivially easy to get backwards.
- **Enclosure.** The stock ADALM-PLUTO ships in a plastic case with the SMAs
  protruding. If PlutoPlus does too, the case thickness sets the standoff and
  may block a daughter board entirely.
- **Connector protrusion** past the board edge.
- **Mounting holes**, which would let a standoff carry the daughter board's
  weight instead of the connector solder joints.

## Mating strategy — the blind-mate escape hatch does NOT apply here

A survey of blind-mate coax families was run to see whether a float-mount
interface could absorb the ±0.5 mm uncertainty above. Result, with sources:

| family | radial float | axial float | band |
|---|---|---|---|
| SMP / SMPM / SMPS / GPO / GPPO | **±0.254 mm** | 0–0.254 mm | to 40–100 GHz |
| SMP/SMPM **spring** bullets | ±0.254 mm | **0.81–2.54 mm** | to 65 GHz |
| BMA float-mount (Radiall, TE OSP) | **±0.51 mm** | **1.52 mm** | DC–22 GHz |
| **Amphenol HD-EFI** | **±1.4 mm** | **±1.4 mm**, 5° | **DC–6 GHz** |

The whole SMP family converges on the same MIL-STD-348 number, ±0.254 mm — less
than our uncertainty. Only BMA float and HD-EFI beat it, and HD-EFI is
purpose-built for "multiple RF lines between PCBs" with a band ceiling of
6 GHz that matches this design's top end exactly.

**None of it helps.** Blind-mate requires the interface on BOTH sides, and the
PlutoPlus side is fixed: four threaded SMA jacks, already fabricated. We cannot
put HD-EFI on a board we are not making.

And the survey's other finding closes the remaining door: **no float-mount SMA
exists.** No major manufacturer publishes an SMA with a floating flange or
bushing, because SMA is a threaded, rigidly-located interface — the coupling
nut IS the alignment mechanism. Amphenol, Radiall, TE, SV, Cinch: none.

### What that leaves

1. **Rigid SMA plugs at the measured pitch.** Requires the pitch to roughly
   ±0.1 mm, which means the caliper measurement is now LOAD-BEARING, not a
   nice-to-have. This is the clean answer if the number can be had.
2. **Solder-after-mate.** Mount the three Pluto-facing SMAs as THROUGH-HOLE with
   modest hole clearance, plug the bare board onto the Pluto, then hand-solder
   the connectors in position. The assembly self-aligns and the tolerance
   problem disappears entirely. Cost: three hand-soldered joints, which under
   this repo's PCBA-is-the-deliverable rule needs an `assembly.yaml` entry with
   reason and evidence — a recorded decision, not a silent one.
3. **Short semi-rigid jumpers** on one or more ports. Partially concedes the
   no-cables goal and is the fallback if 1 and 2 both fail.

Option 2 is worth serious consideration even if the caliper number arrives: it
removes the tolerance stack-up rather than budgeting for it, and this board is
a low-volume bench adapter where three hand-solder joints cost little.
