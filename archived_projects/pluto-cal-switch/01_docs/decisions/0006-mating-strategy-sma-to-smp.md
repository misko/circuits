---
id: 0006
date: 2026-07-27
status: superseded-by-0015
tags: [mechanical, topology]
---
# 0006 — SMA→SMP adapters on the Pluto; the board carries edge-launch SMP

## Context

Three of the five ports face the PlutoPlus. The obvious build — three SMA
plugs on the daughter board threading onto the Pluto's three jacks — is
**DEAD**, for three independently fatal reasons established in
`01_docs/pluto-plus-mechanical.md`:

1. **SMA has essentially no float.** MIL-STD-348B gives a guaranteed radial
   float of 0.0025 mm and a thread-start capture window of ±0.05 mm, against a
   two-board fabrication stack of **±0.49 mm RSS / ±1.27 mm arithmetic worst
   case** (every term sourced from published fab capability, IPC-7351 and
   connector-vendor specs). That is **10× to 25× over.** Knowing the Pluto's
   pitch exactly does not save it.
2. **Tightening is COUPLED.** The coupling nut draws the boards together
   axially by up to **2.8 mm** over its 3–4 turns to engagement (1/4-36 UNS,
   0.7056 mm/turn), so torquing the first connector MOVES THE DATUM for the
   other two. No order of operations converges.
3. **No wrench fits.** The coupling-nut hex is 7.85–8.00 mm across flats; at
   the Pluto's **11.60 mm** RX2–RX1 pitch adjacent nuts leave **2.43 mm**
   corner-to-corner, against vendor guidance of 12–14 mm minimum pitch for
   wrench access. The specified 7–10 in-lb mating torque cannot be applied.

Blind-mate does not rescue it either: it requires the interface on BOTH sides,
and the Pluto side is already fabricated. And **no float-mount SMA exists** —
Amphenol, Radiall, TE, SV and Cinch all publish none, because the coupling nut
IS the alignment mechanism.

The structural principle, from Samtec on mezzanine stack-ups: ONE connector
self-aligns and the board floats to it; THREE connectors fight each other, and
the tolerance is in the boards, not the drawing.

## Options

- **Rigid SMA direct-mount.** DEAD, above.
- **Solder-after-mate** — mount the Pluto-facing SMAs as through-hole, plug the
  bare board on, then hand-solder in position. REJECTED: it fixes tolerance
  (1) but not coupling (2) or wrench access (3).
- **Short semi-rigid jumpers.** The fallback. Concedes the no-cables goal.
- **Convert the interface ONCE: SMA→SMP adapters on the Pluto's jacks, SMP on
  the board.** CHOSEN.

## Decision

**Screw an SMA-plug-to-SMP adapter onto each of the Pluto's three jacks; the
daughter board carries three EDGE-LAUNCH SMP jacks and PUSHES ON.**

Why this solves all three:

- Each adapter threads on **independently**, one at a time, with nothing else
  installed — so wrench access is a one-time fiddle instead of an
  every-connect ritual, and there is **no coupled datum** because nothing else
  is attached while you do it.
- The daughter-board interface becomes push-on with **±0.25–0.30 mm radial
  and ~4° angular float**, against SMA's 0.0025 mm.
- Mating and unmating become a push/pull, which is what a bench calibration
  switch actually wants.

### Parts, with the gender chain closed

| role | MPN | source | stock | price |
|---|---|---|---|---|
| board SMP jack ×3 | **SMP-MSLD-PCE-5T** (Amphenol RF) | LCSC **C6297051**, JLC Extended | 540 | $6.25 @1 |
| adapter ×3 | **134-1019-451** (Cinch/Johnson) | DigiKey | 21 | $33.83 @1 |
| adapter alternate | SF1129-6154 (SV Microwave) | DigiKey | 100 | $77.41 @1 |
| board SMP, vertical fallback | SMP-MSLD-PCS20T | LCSC C3175159 | 546 | $4.58 @1 |

```
PlutoPlus connector    SMA JACK  (female shell, female socket)   [INFERRED — see below]
      ↕ threaded
adapter end A          SMA PLUG  (male shell, MALE PIN)          ✓
adapter end B          SMP       (smooth barrel, FEMALE SOCKET)
      ↕ push-on, limited detent
board                  SMP JACK  (detent bore, MALE PIN)         ✓  chain closes
```

### The part this project was handed is the WRONG GENDER

**`AD-SMAJSMPP-2`, named in the mating-strategy handoff, is SMA JACK → SMP
PLUG.** Its Pluto-facing end is an SMA **jack** — the same gender as the
Pluto's own connectors. **It cannot screw onto the Pluto.** Its mirror
`AD-SMAPSMPJ-2` has the right SMA end but its SMP end is a male-pin
limited-detent jack, i.e. identical gender to our board part; two shrouds need
a bullet between them. Cinch `134-1019-441` fails the same way.

The trap that makes this so easy to get wrong: **Amphenol and Cinch use
OPPOSITE plug/jack words for the same physical SMP half.** The only reliable
discriminator is the **centre contact** — our board part has a male pin, so the
adapter's SMP end must have a female socket. Two parts both labelled "SMP
Jack" by a distributor do in fact mate.

### Detent class: LIMITED DETENT

| class | engage max | disengage min | cycles min | JLC stock |
|---|---|---|---|---|
| full detent | 15.0 lb | 5.0 lb | 100 | **0 across all 5 SKUs** |
| **limited detent** | **10.0 lb (45 N)** | **2.0 lb (9 N)** | **500** | 540 / 546 |
| smooth bore | 2.0 lb | 0.5 lb | 1000 | 2 |

(Cinch SMP/SMPM catalog p.4, "Interface Design: MIL-STD-348A"; independently
confirmed on Amphenol drawing SMP-MSLD-PCE-5X Rev A note 3.)

LD is right on the merits AND is the only class with stock. Cinch p.3, vendor
guidance: *"The LD is typically selected as the snap-on interface in PCB mount
or blind-mate applications, while the FD is mainly used for cabled connections
where higher retention forces are required."* Retention is 3 × 9 N = **27 N
minimum** to pull the board off — survives a cable tug; smooth bore's 6.7 N
total would not.

### Why EDGE-LAUNCH rather than vertical

1. **The 45 N engagement force acts IN the board plane**, taken as shear along
   the substrate. On a vertical connector the same force is normal to the
   board — **peel** on SMT pads, up to 3 × 45 = 135 N of it.
2. DC–26.5 GHz, VSWR **1.11 max over DC–6 GHz** (RL 26 dB) — covers the band
   with margin. The vertical PCS20T is DC–20 GHz.
3. The board stays **coplanar with the RF axis**, which is the geometry the
   floorplan assumes.

## Consequences

- **The board carries 3 SMP + 2 SMA, not 5 SMA.** The brief's "5 SMA ports"
  is still delivered — the SMA interface has moved onto the adapters.
- **RF axis sits 2.00 mm above the board's top surface** (drawing
  SMP-MSLD-PCE-5X sheet 2, "2 REF [.079]"). This is the hardest mechanical
  number in the project. The board's top copper plane must sit 2.00 mm below
  the plane containing the Pluto's three SMA axes.
- **Board edge lands ≈10.2 mm off the Pluto's SMA faces** (adapter overall
  14.25 ± 0.51 mm, less an ESTIMATED ~4.0 mm of coupling-nut thread
  engagement — that 4.0 mm has **no primary source** and is the dominant error
  in the separation).
- **Edge-launch means a routed notch in the board outline**: 7.65 mm wide ×
  6.4 mm deep, 4.12 mm mouth, 0.83 mm centre trace, 1.84 mm side pads,
  surfaces coplanar within 0.13 mm. **Three notches at 11.60 / 11.98 mm pitch
  leave only ~3.95 mm of board web between adjacent ones** — a floorplan
  constraint, and a mechanical one.
- **The board-outline routing tolerance now enters the RF reference plane.**
  It affects all three notches through the SAME tool path, so the arm-to-arm
  difference is the router's within-board repeatability rather than JLC's
  ±0.2 mm board-to-board figure — but this must be MEASURED and folded into
  the D4 published delta (ADR-0011), not assumed away.
- **Engagement force is a usability cost.** Pushing the board onto three
  limited-detent SMPs takes up to 135 N (30 lbf). No vendor guidance exists on
  the maximum permissible in-plane force for this footprint. Consider a
  handle/stiffener on the board and mount all three from the same MPN so the
  axial locations agree.
- **THE ADAPTERS COST MORE THAN THE BOARD.** 3 × $33.83 = **$101** (or $232 for
  the SV Microwave alternate) against a board BOM near $45. This must be
  flagged to the user; it is not obvious from "use an adapter".
- **Adapter stock is THIN**: 21 pieces of 134-1019-451. Order early.
- **The PlutoPlus SMA gender is INFERRED, not cited.** The schematic value
  string is only `SMA-L` with no manufacturer part. SMA jack is the universal
  SDR convention and no contrary evidence was found, but **this is a
  five-minute caliper check that should happen before $100 of adapters is
  ordered.**
- **JLC assemblability of the edge-launch part is the weakest claim here.**
  "In the library, 540 in stock, `isBuyComponent: 1`" means PURCHASABLE, not
  PLACEABLE: the part straddles a routed outline notch and demands 0.13 mm
  coplanarity. **Submit the real gerbers + CPL to JLC DFM review before
  committing.** `SMP-MSLD-PCS20T` (vertical, 546 in stock, conventional SMT
  footprint) is the pre-designed fallback; hand-solder of three connectors on
  a low-volume board is acceptable but must be a recorded `assembly.yaml`
  decision with the catalog query and its date, not a discovery at fab time.
- **Residual risk.** SMP's ±0.25–0.30 mm float is close to the ±0.49 mm RSS
  two-board stack. Mitigations in preference order: tighten the daughter
  board's own connector-position tolerance (it is the half we control), or take
  load off the interface with a bracket on the Pluto's corner mounting holes.
  Note also that a DETENTED mate LOCATES axially, so three in parallel are
  axially over-constrained — all three adapters must be the same MPN, and
  MIL-STD-348 permits 0.254 mm of mated axial misalignment.

## Superseded — 2026-07-27, by ADR-0015 (user directive A8)

> "lets not do the fixed bulkhead version, lets use SMA cables to connect our
> board to the pluto."

**Cause: the user chose to pay for the mating float with a cable instead of
with $101 of adapters.** Nothing above is refuted. The three fatal proofs
against rigid SMA direct-mount — the ±0.05 mm thread-start window against a
±0.49 mm RSS stack, the coupling nut that draws the boards together by 2.8 mm
so torquing one moves the datum for the others, and the 2.43 mm of
corner-to-corner wrench clearance at 11.60 mm pitch — **all still stand, and
they are the reason a cable is now in the path.** This ADR is the record of
*why the obvious build is impossible*; ADR-0015 is the record of what replaced
it.

What is DEAD from this ADR: the three Cinch `134-1019-451` adapters ($101), the
three board-side `SMP-MSLD-PCE-5T` edge-launch jacks ($18.75, `02_parts/`
directory deleted), the SMP-vs-SMA gender chain, the limited-detent /
engagement-force analysis (135 N push-on, 27 N retention), the 7.65 × 6.4 mm
routed outline notches and the ~3.95 mm board web between them, the ≈10.2 mm
board-to-Pluto separation with its unverified ~4.0 mm thread-engagement term,
the 2.00 mm RF-axis-above-our-top-surface requirement, and the open JLC-DFM
question about whether an edge-launch part straddling a routed notch is
PLACEABLE.

What SURVIVES and moved: the gender-chain DISCIPLINE (ADR-0015 closes the SMA
chain on two independent printed sources rather than on a part-number suffix),
and the observation that vendors use opposite plug/jack words for the same
physical half — which is precisely why this board got a $101 recommendation
wrong once already.
