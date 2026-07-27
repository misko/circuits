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

## INDEPENDENTLY CONFIRMED, and the uncertainty is now closed

A second, independent extraction of the same plot (different method: content-
stream footprint coordinates rather than rendered pixels) reproduces every
number above, and closes the scale question five ways instead of my two:

| quantity | my pixel measurement | independent CAD extraction | agreement |
|---|---|---|---|
| T2–R2 | 12.02 mm | **12.023 mm** | 0.003 mm |
| R2–R1 | 11.60 mm | **11.599 mm** | 0.001 mm |
| R1–T1 | 11.98 mm | **11.980 mm** | 0.000 mm |
| total span | 35.60 mm | **35.602 mm** | 0.002 mm |
| board outline | 66.63 × 99.48 | **66.590 × 99.441** | 0.04 mm |

The stronger scale proof: the board's 2×6 headers measure **exactly 15.240 mm =
6 × 2.54**, and a repo photo confirms they really are 2×6 headers. Footprints
land on exact mil values (320/220/600) while placements land on exact 0.01 mm
values — the signature of a 1:1 plot.

**Design intent is almost certainly 12.00 / 11.60 / 12.00 mm** — the three sum
to exactly 35.60 and the group is centred on the board to within 0.04 mm.

The ±1.5 % uncertainty I recorded is therefore RESOLVED, and a caliper check is
no longer needed for the PITCH. It is still worth doing to confirm the user's
unit is the 2020 revision.

**The silkscreen confirms the port map independently.** A board photo reads
**T2 R2 R1 T1** in physical order, matching the schematic net names exactly.

**The non-uniform pitch survived an attempt to refute it.** The first
photogrammetric pass measured the protruding BARRELS and found near-uniform
spacing — but those barrels stick out ~11 mm toward the camera, and parallax
swamps a 3.5 % difference. Re-measured on the SILKSCREEN boxes, which lie flat
at equal depth, the CAD ratios reproduce and uniform pitch is excluded at ~3σ.
That is the adjacent-property trap caught in the act: the barrel is not the
feature whose spacing you want.

## Uncertainty — superseded by the section above

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

## CORRECTION — my revision caveat was WRONG

I previously recorded that `Top.pdf` (titled `PLUTOX-SDR-TV4.0-202111`) and the
schematic (`PLUTOX_SDR-V1.0-20201212`) were "about a year apart" and might
describe different boards. **That is wrong.**

`202111` is a JOB/PROJECT NUMBER, not November 2021. Both CAM plots carry a
footer timestamp of **Sat Dec 19 2020**, and the PDF metadata reads
`Producer: Microsoft: Print To PDF, CreationDate: Sat Dec 19 2020`. The plots
are **7 days after** the schematic and belong to the same design. There is no
year gap and no mismatch.

## But there ARE three different boards called "Pluto+" — and this one matters

| what | what it is |
|---|---|
| **Pluto+ "Release V1"** (2020/21) | The board these files describe. JTAG rail **1.8 V** (silk `1V8 TMS TCK TDO TDI GND`), Samsung K4B4G1646E DDR3. |
| **Pluto+ "Release V2"** (from ~Sept 2021) | Genuine vendor respin. **3.3 V SPI-flash, JTAG rail 1.8 V → 3.3 V**, DDR3 Samsung → Micron. Vendor: *"The ones that are purchased online now… are the v2 version."* |
| **"Pluto+ V2" sold from 2025** | **A KNOCK-OFF, not a vendor revision.** Completely different PCB artwork, no RF shield can, DIP switches instead of jumpers, ext-clock select via MIO48 HIGH instead of shorting `EXTCLK` to GND. Reported low-quality TCXO. |

**Anyone buying today most likely has V2 or the knock-off, NOT the board these
plots describe.** The vendor never mentioned moving a connector in the V1→V2
respin, and the knock-off's own layout image shows the same edge with the same
port order (labelled `TX2A RX2A RX1A TX1A`) — so the geometry PROBABLY carries
across. Nobody has published a side-by-side dimensional comparison, and
"probably" is not what you build a rigid mount on.

**How to identify which board is in hand:** read the JTAG header silk. `1V8`
next to the TMS/TCK/TDO/TDI/GND rail ⇒ V1. Look for an RF shield can — the
genuine boards have one, the 2025 knock-off does not. The knock-off also adds a
second U.FL (`CLK_OUT`) beside `CLK_IN`, and `DAC1/DAC2` + `GPO0–GPO3` pads.

## Scale — one unresolved tension, recorded rather than smoothed over

Two independent extractions disagree slightly about whether the plot is exactly
1:1, because they calibrated on different features:

- **2×6 header pitch = 15.240 mm = exactly 6 × 2.54.** Strongest evidence: header
  pitch is exact by definition and this is a pin-to-pin measurement.
- **Zynq CLG400 body = 16.78 mm vs 17.00 nominal (×1.013); HanRun RJ45 = 21.04 ×
  16.09 vs 21.3 × 16.0 (×1.012 / ×0.994).** These are courtyard outlines, which
  need not equal package bodies — and the plot passed through
  `Microsoft: Print To PDF`.

Reading the two together: the pitches are right to ~1 %, i.e. **±0.12 mm on a
12 mm pitch**, better than my original ±1.5 % but NOT zero. The three
independent measurements of the pitches themselves agree to 0.003 mm, so the
RATIOS are solid; it is the absolute scale that carries the residual 1 %.

For the SMP-adapter path this is comfortably inside the ±0.3 mm float. For a
rigid mount it would still matter — one more reason that path is dead.

## Enclosure — established, and it has a consequence

PlutoPlus ships in a **two-part aluminium shell**, upper half removable. The
SMAs are PCB edge-mount jacks that **pass through plain holes in the end panel
and are retained by their own nuts** — the end panel is captured ON the SMA
barrels.

**Consequence: unscrewing the SMA nuts to fit adapters partially frees the end
panel.** Not a blocker, but it means fitting the SMA→SMP adapters is a
case-disassembly-adjacent operation, not a purely external one.

Threaded barrel protrusion past the case face ≈ **7 mm** (photogrammetric
estimate, not published). Case outer ≈ 103–106 × 71 mm, height not established.
No vendor publishes device dimensions, no mechanical drawing, no STEP file.
The `150×120×60 mm / 0.3 kg` figure seen on one reseller is the **shipping box**,
from a WooCommerce shipping field — not the device.

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

---

# VERDICT: rigid SMA direct-mount is DEAD. Three reasons, any one fatal.

My earlier reasoning — "the SMA coupling nut rotates independently of the body,
so three rigid plugs can be threaded onto three fixed jacks" — is TRUE and
INSUFFICIENT. The nut rotating is necessary, not sufficient. Three things kill
it, and I had only considered the tolerance one.

### 1. SMA publishes no float because it has essentially none

MIL-STD-348B: plug spigot OD ≤ 4.593 mm against jack bore ≥ 4.597 mm —
**guaranteed radial float 0.0025 mm.** The thread-start capture window is
**±0.05 mm** worst case. Outer conductors butt at the reference plane, so axial
float is **zero**.

Our two-board stack-up (hole position ±0.05, profile-to-hole ±0.20 per board,
JLCPCB/Eurocircuits published tolerances) is **±0.31 mm RSS, ±0.70 mm worst
case** — **6 to 14× the capture window.** Knowing the pitch exactly does not
save it; PCB fabrication tolerance alone exceeds what SMA can absorb.

### 2. Tightening is COUPLED — this is the one I missed

The coupling nut does not merely rotate, it **draws the boards together
axially, by up to 2.8 mm** over its 3–4 turns to engagement (1/4-36 UNS,
0.7056 mm/turn). So tightening the first connector MOVES THE DATUM for the
other two. There is no order of operations that converges: each nut you torque
mis-seats the ones already done.

### 3. No wrench fits between the connectors

The SMA coupling-nut hex is 7.85–8.00 mm across flats. At the **11.60 mm**
R2–R1 pitch, adjacent nuts leave **2.43 mm corner-to-corner**. Vendor guidance
is 12–14 mm minimum SMA pitch for wrench access; **this board is below it.**
Mating torque is specified at 7–10 in-lb (MIL-PRF-39012/55H) and cannot be
applied.

Note this also weakens the solder-after-mate idea: it fixes the tolerance
problem (1) but not the coupling (2) or the wrench access (3).

## The alternative that works: convert the interface ONCE

Screw an **SMA→SMP adapter** onto each of the Pluto's three jacks (e.g.
Amphenol `AD-SMAJSMPP-2`). Then the daughter board carries SMP and **pushes
on** — no threads, no torque, no coupling.

Why this actually solves all three:

- Each adapter threads on **independently**, one at a time, with nothing else
  installed — so the wrench-access problem is a one-time fiddle instead of a
  every-connect ritual, and there is no coupled datum because nothing else is
  attached while you do it.
- The daughter-board interface becomes SMP push-on: **±0.254–0.3 mm radial and
  4° angular** float, versus SMA's 0.0025 mm.
- Mating and unmating the adapter board becomes a push/pull, which is what a
  bench calibration switch actually wants.

Residual concern to size during design: SMP's ±0.3 mm is close to our ±0.31 mm
RSS stack. Mitigations, in order of preference: tighten the daughter board's
own connector-position tolerance (it is the half we control), use SMP spring
bullets for axial compliance, or take load off the interface with a bracket on
the Pluto's four corner mounting holes.

## STILL BLOCKING, and it must be measured on a physical unit

**RF axis height above the PCB top surface — NOT ESTABLISHED.** These are
RIGHT-ANGLE through-hole SMA jacks (5 solder joints each: 4 ground pins on a
~5.1 mm square plus a centre signal pin), so the RF axis sits ABOVE the board
plane, not in it. Geometric lower bound is ≥3.2 mm (half the 6.35 mm barrel
must clear the board); typical for the family is 4.5–6 mm.

**This number sets the daughter board's connector height and therefore its
entire mechanical relationship to the Pluto. It cannot be guessed.**

Also still open: the aluminium case's panel cutout geometry (PlutoPlus ships
assembled in a case, SMAs protruding — the case may set the standoff or block
the board entirely); mounting-hole diameter and exact position (photogrammetric
±0.5 mm only); whether post-2020 production changed the RF geometry; standard
SMA vs RP-SMA centre contact.

**ADALM-PLUTO geometry does NOT transfer** — ADI Rev D has 2 SMA on a
109.14 × 63.14 mm board. Different board entirely; do not reuse its numbers.

---

# The tolerance stack, now MEASURED rather than argued

An independent study sourced every term from published fab capability, IPC, and
connector-vendor specs. It confirms the verdict above with numbers.

| term | value | source |
|---|---|---|
| board outline routing | ±0.20 mm | JLCPCB, routed edge, regular precision |
| hole/pad pattern → outline registration | ±0.20 mm | **Eurocircuits, explicitly labelled "Profile/Cut-Out to Hole"** |
| copper feature location → datum | ±0.20 mm (Level B) | IPC-7351 Table 3-18 |
| placement, connector-sized part | ±0.035 mm | Yamaha YRM20 HM head, Cpk≥1.0 |
| reflow drift, connector-sized part | **unquantified** | no published data exists |

**Per board: ±0.35 mm RSS, ±0.64 mm arithmetic worst case.**
**Two boards mating: ±0.49 mm RSS, ±1.27 mm AWC.**

Against SMA's ±0.05 mm thread-start capture window that is **10× to 25× over**.
Independent of the earlier ±0.31 mm estimate and the same conclusion, harder.

## THE TRAP: the fab number you want is not the one published

**JLCPCB's ±0.05 mm "Hole Position Tolerance" has NO STATED DATUM**, and using
it as the connector-to-board-edge term would understate this budget by 4×.

Every fab that *does* label its datum shows why. Eurocircuits publishes both:

    Hole Positional Tolerance      0.10 mm    "Hole to Hole"
    Positional Tolerance
      Profile/Cut-Out to Hole      ±0.20 mm

The profile is a **separate machine setup**, so hole-to-outline is roughly
double hole-to-hole. JLCPCB's ±0.05 mm matches the hole-to-hole-within-one-pass
figure, not the outline-referenced one — and JLCPCB publishes **no**
hole-to-outline, no drill-to-copper, no layer-to-layer registration, and **no
SMT placement accuracy at all** on either capabilities page.

This board's SMA positions are referenced to the BOARD EDGE, because that is
what aligns to the Pluto. The edge-referenced term is the one that matters and
it is the one JLCPCB does not publish. **Take it from a fab that labels its
datum, not from the number that happens to be printed.**

This generalises beyond this board and is a candidate for the canon.

## The structural principle underneath all of it

Samtec, on multi-connector mezzanine stack-ups:

> in a **single connector** application the daughtercard is assumed to be free
> floating with alignment features within the connectors themselves ensuring
> perfect alignment, **therefore being unimpacted by PCB fabrication and
> assembly process tolerances**. However, in a **multi-connector** application
> with two or more connectors, mechanical tolerances will stack in any
> direction at any distance.

That is the whole story in one sentence. ONE connector self-aligns and the
board floats to it. THREE connectors fight each other, and no amount of
knowing the pitch changes that — the tolerance is in the boards, not the
drawing.

Samtec's own SEAM/SEAF spec puts the acceptance limit at **±0.13 mm** X and Y,
and notes the report's sharpest line: **even the single-board RSS figure of
±0.35 mm blows that budget.** Their guidance is float, standoffs, or a
mechanical datum other than the routed edge — which is exactly the SMA→SMP
adapter path recommended above.
