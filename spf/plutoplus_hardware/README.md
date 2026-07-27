# PlutoPlus hardware — two physical boards, measured

Reference data for building anything that mates to a PlutoPlus SMA panel.
Collected 2026-07-27 for `projects/pluto-cal-switch`, but kept here because it
describes SOMEONE ELSE'S hardware and is useful to any future board.

**There are two units in hand and THEY ARE NOT THE SAME BOARD.** One is a
genuine Pluto+, the other is a 2025 clone. Their SMA spans differ by 0.32 mm.
Anything that mates to "a PlutoPlus" must say which one, or tolerate both.

## The two boards at a glance

| | **Board A — genuine Pluto+** | **Board B — 2025 clone** |
|---|---|---|
| RF shield can | **YES**, over the AD9363 | **NO** — AD9363 bare and readable |
| U.FL clock | `CLK-IN` only | **`CLK_IN` *and* `CLK_OUT`** |
| SMA silk | `T2 R2 R1 T1` | **`TX2A RX2A RX1A TX1A`** |
| boot select | jumpers | **`BOOT MODE` switch table** (`JTAG ON ON / SPI OFF ON / TF OFF OFF`), `S1` on underside |
| extra pads | — | **`DAC1/DAC2`, `GPO0`–`GPO3`, `GND4`** |
| artwork | cartoon logo, 一蓑烟雨任平生 | different logo, no cartoon |
| Zynq | XC7Z010 CLG400 | XC7Z010 CL400ABX2317 |
| RJ45 | HanRun HR911130A 23/42 | HanRun HR911130A 24/43 |

Board B matches every published tell of the clone sold from ~March 2025 on
Banggood/AliExpress. It is **not** a vendor revision — the genuine V1→V2 respin
(~Sept 2021) changed only the SPI-flash and the JTAG rail voltage (1.8 V →
3.3 V), never the artwork.

**Fast field ID:** look for the shield can. Genuine has one; the clone does not.

## Measurements — method matters, so it is recorded

Taken with calipers on the physical units. **Outside-to-outside across barrel
pairs, then subtract the barrel OD** — chosen because centre-to-centre on round
barrels cannot be seen directly and is systematically biased by eye. An earlier
freehand centre-to-centre attempt on Board B read 11.39 / 11.17 / 11.27, which
is ~5 % low; the technique below removes that.

**Barrel outside diameter, both boards: 6.25 mm.**

### Raw, outside-to-outside from TX2's outer edge

| span | Board A (genuine) | Board B (clone) |
|---|---|---|
| TX2 → RX2 | 17.98 | 17.84 |
| TX2 → RX1 | 29.49 | 29.26 |
| TX2 → TX1 | 41.29 | 40.97 |

### Derived centre-to-centre

Subtracting D = 6.25 for the cumulative distances. **The middle two pitches are
differences of two outside measurements, so D cancels entirely** — those are the
most trustworthy numbers here and carry no diameter assumption.

| | Board A | Board B | A − B |
|---|---|---|---|
| TX2 ↔ RX2 | 11.73 | 11.59 | 0.14 |
| **RX2 ↔ RX1** (D-free) | **11.51** | **11.42** | 0.09 |
| **RX1 ↔ TX1** (D-free) | **11.80** | **11.71** | 0.09 |
| **total span** | **35.04** | **34.72** | **0.32** |

### Three things these numbers establish

**The pitch is NOT uniform, on both boards.** The middle gap (RX2↔RX1) is the
smallest of the three, on the genuine board and on the clone, and on both it is
shown by the D-free pitches — no diameter assumption involved. The asymmetry is
real and it survived onto the clone.

**The clone is a uniform ~0.9 % shrink of the genuine.** 11.42/11.51 = 0.992 and
11.71/11.80 = 0.992 — the same ratio on both D-free pitches. A consistent scale
factor, not a redraw. That is what reverse-engineering from a scan or photo
looks like.

**The published CAD agrees with the genuine board within its error.** See below.

## Comparison with the published CAD

`github.com/plutoplus/plutoplus` ships **no PCB source** — three PDFs only, no
KiCad/Altium/DXF/STEP, and no dimensioned drawing. Geometry was extracted from
the undimensioned vector assembly plot `sch/Top.pdf`, rendered at 600 dpi.

| | CAD | Board A | CAD vs A |
|---|---|---|---|
| TX2 ↔ RX2 | 12.02 | 11.73 | +2.5 % |
| RX2 ↔ RX1 | 11.60 | 11.51 | +0.8 % |
| RX1 ↔ TX1 | 11.98 | 11.80 | +1.5 % |
| **span** | **35.60** | **35.04** | **+1.6 %** |
| board outline | 66.59 × 99.44 | not measured | — |

**+1.6 % on the span sits inside the ±1.5 % scale uncertainty** the extraction
carried, so the CAD and the genuine board agree within error. The plot went
through `Microsoft: Print To PDF`, and the calibration targets scattered:

- 2×6 header = **15.240 mm = exactly 6 × 2.54** (strongest — pitch is exact by
  definition, and it is a pin-to-pin measurement)
- Zynq CLG400 courtyard = 16.76 vs 17.00 nominal (1.4 % small)
- AD9361 courtyard = 10.16 vs 10.00 nominal (1.6 % large)
- HanRun RJ45 = 21.04 × 16.09 vs 21.3 × 16.0

Courtyard outlines need not equal package bodies, which is the likely source of
the scatter. **Where CAD and caliper disagree, the physical board wins.**

## Port map — confirmed three ways

From the schematic net names, the assembly plot refdes, and the silkscreen in a
board photo:

| refdes | net pair | Board A silk | Board B silk |
|---|---|---|---|
| U7 | `TX2A_P/N` | `T2` | `TX2A` |
| U10 | `RX2A_P/N` | `R2` | `RX2A` |
| U14 | `RX1A_P/N` | `R1` | `RX1A` |
| U12 | `TX1A_P/N` | `T1` | `TX1A` |

Physical order along the short edge: **TX2 · RX2 · RX1 · TX1**.
**The two RX ports are adjacent, in the middle.**

There is **no GPS or clock SMA** on the panel of either board — the external
reference is a U.FL only.

## Connector construction

**Right-angle (90°) through-hole SMA JACKS (female).** Five solder joints each:
four ground pins on a ~5.1 mm square plus a centre signal pin. The body sits on
the top surface; the barrel points horizontally out past the board edge, so the
**RF axis is ABOVE the board plane, not in it**.

Footprint outline 8.13 × 8.13 mm, outer edge flush with the PCB edge.

**A mating board therefore needs SMA PLUGS (male).**
⚠️ Standard SMA vs RP-SMA was not visually confirmed — standard is near-certain
for an SDR, but the centre contact was not resolvable in the photos.

## Enclosure

Two-part aluminium shell, upper half removable. The SMAs pass through **plain
holes in the end panel and are retained by their own nuts** — the end panel is
captured on the barrels, and it stays fitted even with the shell off. Unscrewing
the nuts to fit adapters partially frees the panel.

Barrel protrusion past the case face ≈ 7 mm (photogrammetric estimate).
Case ≈ 103–106 × 71 mm; height not established. No vendor publishes device
dimensions, and there is no mechanical drawing or STEP file anywhere.
The `150 × 120 × 60 mm / 0.3 kg` figure on one reseller is the **shipping box**,
read out of a WooCommerce shipping field.

Four corner mounting holes with plated pads are present on both boards — usable
for a bracket to take load off the connectors. **Positions and diameter are NOT
established**: the mounting holes are not drawn on the assembly layer.

## NOT established — measure before relying on any of it

- **RF axis height above the PCB top surface.** Right-angle jacks put the axis
  above the board plane. Lower bound ≥3.2 mm (half the barrel must clear the
  board); family typical 4.5–6 mm. **Sets the Z position of anything that mates.**
- Board outline dimensions of the physical units (only the CAD figure exists).
- Mounting-hole positions and diameter.
- Case panel cutout geometry, wall thickness, outer height.
- Standard SMA vs RP-SMA.
- Which genuine revision Board A is (V1 vs the ~Sept 2021 V2 respin) — read the
  JTAG header silk: `1V8` ⇒ V1, `3V3` ⇒ V2.

## Consequence for a mating board

SMA has **essentially zero float**: MIL-STD-348B gives plug spigot OD ≤4.593 mm
against jack bore ≥4.597 mm — 0.0025 mm guaranteed radial, ±0.05 mm thread-start
capture window, zero axial. A two-board PCB tolerance stack is ±0.31–0.49 mm RSS,
which is 6–14× that window. Add that the coupling nut **draws the boards together
by up to 2.8 mm** as it tightens (so torquing one connector moves the datum for
the others), and that the 7.85–8.00 mm nut hex leaves only **2.43 mm
corner-to-corner** at the 11.5 mm pitch — no wrench fits.

**Rigid three-connector SMA direct-mount does not work.** Full reasoning, with
sources, in `projects/pluto-cal-switch/01_docs/pluto-plus-mechanical.md`.

The 0.32 mm span difference between these two boards reinforces it: no rigid
design fits both, whereas an SMP-based interface (±0.254–0.3 mm float, reached
via SMA→SMP adapters screwed onto the Pluto) plausibly fits both if designed to
the **34.88 mm midpoint**.

## Sources

- Repo (schematic + CAM plots, no PCB source): <https://github.com/plutoplus/plutoplus>
- `sch/PLUTOX_SDR-V1.0-20201212.pdf` — 4-page schematic
- `sch/Top.pdf` / `sch/Bottom.pdf` — assembly plots, footer `PLUTOX-SDR-TV4.0-202111`.
  **`202111` is a job number, not a date**: both carry a `Sat Dec 19 2020`
  timestamp and PDF `CreationDate` to match, i.e. 7 days after the schematic.
- Issue #41 "PCB dimensions" — open and unanswered since 2024-05-06. Nobody has
  published this.
