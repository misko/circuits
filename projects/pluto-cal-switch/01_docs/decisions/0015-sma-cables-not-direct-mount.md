---
id: 0015
date: 2026-07-27
status: accepted
tags: [mechanical, topology]
---
# 0015 — SMA CABLES to the Pluto; five true SMA jacks on the board

## Context

The user reversed the mating strategy:

> "lets not do the fixed bulkhead version, lets use SMA cables to connect our
> board to the pluto."

and closed two open items in the same breath: **the PlutoPlus RF ports are SMA
FEMALE (jacks)** — the owner has both units in hand — and **the Pluto lives in
a two-part aluminium case, so its PCB was never the mating reference at all.**
Recorded as **A8** in `BRIEF.md`.

This does not refute ADR-0006; it dissolves the problem ADR-0006 was solving.
ADR-0006 proved that rigid three-connector SMA direct-mount is dead (±0.05 mm
thread-start window against a ±0.49 mm RSS two-board stack, a coupling nut that
draws the boards together by 2.8 mm as it tightens, and no wrench access at
11.6 mm pitch) and then bought back the float with SMA→SMP adapters. All three
proofs stand. What changed is that **the user is willing to pay for the float
with a cable instead of with $101 of adapters**, and a cable has more float
than any connector interface can.

The second half of A8 matters as much as the first. `spf/plutoplus_hardware/`
measured the two units' PCB-referenced geometry to a caliper; the mating faces
a cable actually meets are the **panel-mounted jack faces protruding through
the case**, whose position relative to the PCB nobody measured and nobody now
needs to.

## Options

- **Keep ADR-0006** — SMA→SMP adapters on the Pluto, edge-launch SMP on the
  board. Works, and is designed. Costs **$101** in three Cinch `134-1019-451`
  adapters (21 in stock, one distributor), **$18.75** in three board-side SMP
  jacks, up to **135 N** of push-on force with no vendor guidance on the
  permissible in-plane load, an unresolved JLC DFM question about whether an
  edge-launch part straddling a routed notch is even PLACEABLE, and a board
  outline pinned to a foreign dimension that two physical units disagree about
  by 0.32 mm. REVERSED by A8.
- **Short semi-rigid jumpers.** ADR-0006's own fallback. Strictly worse than
  flexible cable here: same connector count, same cost class, less float, and
  a formed jumper has to be made to a length that depends on the case.
- **SMA cables, board carries five SMA jacks.** CHOSEN.

## Decision

**Three SMA male–male cables run from the Pluto's three jacks to three of this
board's five SMA jacks. The board carries 5 × `KH-SMA-KE-Z` — the part ADR-0007
already selected for the two antenna ports, now used for all five.**

### The gender chain, closed on evidence rather than on a suffix

```
PlutoPlus port     SMA JACK  (female shell, female socket)   MEASURED — owner, both units
      | cable end A: SMA PLUG (male shell, MALE PIN)
cable            male–male
      | cable end B: SMA PLUG (male shell, MALE PIN)
this board       SMA JACK  (female shell, female socket)     verified below
```

**`KH-SMA-KE-Z` is a JACK. The datasheet field is the product-name field on
p.1: `产品名称 = SMA 直式印制面板插座`** — *插座* is receptacle/socket, i.e.
jack. Sheet 2/2 corroborates the shell independently: the mating end is a
**fixed barrel carrying an EXTERNAL `1/4-36UNEF` thread at Ø6.2 mm with no
coupling nut**, which is the jack form; a plug's shell sits inside a rotating
internal-thread coupling nut.

**What the datasheet does NOT print, stated rather than glossed:** neither page
states the centre-contact polarity in words, so the two pages above prove
*female shell* and do not by themselves exclude **RP-SMA** (whose receptacle
also has an external thread but a male pin). That residual is closed by a
second, independent source — the LCSC product page for **C504007**, read
2026-07-27, whose parametrics give `CONN RCPT SMA TH` and interface type
**"Inner hole"** (M-QUOTE: a product page with its URL and read date, CITED).
Two sources, two different properties, and the gap between them named.

**A correction to this project's own record while we are here:** `part.yaml`
claimed the gender was *"read from the part-number decode on p.1"*. **There is
no part-number decode on p.1** — p.1 carries the model string in the 型号 field
and nothing else. The `K = 孔 (hole)` reading is industry convention, not a
printed field, and the brief instruction that produced this ADR was explicit
that gender must not be taken from a suffix. `part.yaml` now cites the fields
that actually exist.

### What the cable absorbs that nothing else could

| ADR-0006's problem | how the cable answers it |
|---|---|
| ±0.05 mm thread-start capture vs ±0.49 mm RSS stack | there is no stack: two independently-positioned connectors joined by a flexible link |
| coupling nut draws the boards together 2.8 mm, so torquing one moves the datum for the others | each cable end is torqued against a connector that is not mechanically tied to the other two |
| 7.85–8.00 mm nut hex at 11.6 mm pitch — no wrench fits | our five ports are placed on OUR pitch, chosen for wrench access |
| 135 N push-on, 27 N pull-off | none |
| edge-launch SMP may not be JLC-placeable | the SMA is a conventional THT flange part JLC hand-solders as part of Standard PCBA |
| board outline pinned to a foreign dimension two units disagree about | the outline is now free |

## Consequences

- **The board is 5 × SMA, exactly as the brief's P1 says.** The interface no
  longer "moves onto the adapters" (ADR-0006 §Consequences); the brief is met
  literally for the first time.
- **BOM: −$119.75, +$1.41.** Out go 3 × Cinch `134-1019-451` at $33.83
  (**$101**, and they cost more than the board) and 3 × `SMP-MSLD-PCE-5T` at
  $6.25 ($18.75). In come 3 more `KH-SMA-KE-Z` at $0.4708 ($1.41). `02_parts/
  SMP-MSLD-PCE-5T/` is deleted, per the 02_parts contract's repair rule
  ("`02_parts/` entry not in the BOM → the part was swapped; delete the
  directory") — its evaluation survives here and in ADR-0006.
- **The cables are USER-SUPPLIED and are NOT on this BOM.** Three of them, and
  the brief's "same path length on each run" (P6) now lands on them: **two of
  the three must be IDENTICAL** — the two RX runs. The TX run's length is free.
  This is a better place for that requirement than a PCB trace-match ever was,
  because a matched pair of cables is a purchasable object and a matched pair
  of microstrips is a routing negotiation. The user's standing position from
  commission (**A6**) governs the tolerance: *"not tight, as long as distance is
  precisely known, it will be software offset."*
- **The board's own arm-to-arm match obligation (D4/ADR-0011) is UNCHANGED and
  is now the smaller term.** It still publishes its measured per-arm length and
  delta; the cables add a second, larger, user-owned term that the release
  cannot measure. **The release must therefore state its measurement plane
  explicitly: this board's SMA jacks, not the Pluto's.** ADR-0013 flagged that
  same quiet tension for the adapters; with cables it is no longer quiet.
- **CABLE LOSS ENTERS THE LOSS BUDGET, and it is the largest single non-pad
  term at the top of the band.** Two 0.3 m RG316-class cables carry ≈0.4 dB at
  70 MHz and ≈3.0 dB at 6 GHz [EST, ×2 bar], which nearly DOUBLES the chain's
  tilt: **3.09 dB → 6.13 dB** across 70 MHz–6 GHz (DETAIL_DESIGN §3). Two
  consequences: (a) any attempt to hold a scalar attenuation figure across the
  band got harder, not easier — see ADR-0016, which stops trying; (b) the
  cable term is user-owned, so the design must not depend on it. It does not:
  ADR-0016's ≥40 dB minimum credits both cables at **zero**.
- **Thirteen of the fifteen `mates.yaml` consumptions retire** (span, seven
  pitches, barrel OD, connector outline width, the superseded CAD span, the
  RF-axis height and the mounting-hole positions). They are marked RETIRED
  with the date and cause rather than deleted. Two survive — port order and
  gender — and three ELECTRICAL facts arrive to replace them (ADR-0016).
  `import_provenance_check.py` grades **18/18, 0 fails**.
- **D6 is retired, not answered.** ADR-0014 chose the 34.88 mm midpoint between
  a genuine unit's 35.04 mm and a clone's 34.72 mm, spending ±0.16 mm of a
  ±0.25–0.30 mm float budget on an unanswered question. **A cabled board fits
  both units and any future revision, because it is referenced to neither.**
  That is the strongest possible resolution of a spec tension: not a decision,
  a dissolution.
- **The $101 gender exposure is retired too, and this is worth being precise
  about.** ADR-0006 recorded that "$101 of adapters rides on" the Pluto's
  gender being female. **With a cable in the path, this board's own port gender
  no longer depends on the Pluto's at all** — the cable absorbs it. If the
  Pluto's ports turned out to be plugs, the fix would be buying male-female
  cables instead of male-male, a ~$5 error rather than a $101 one. The board
  stays a jack either way, because a jack is what a standard male cable end
  mates with.
- **A NEW ground-loop path, stated because ADR-0009 already owns this problem.**
  Three coax shields now bond this board's ground to the Pluto's over a
  cable-position-dependent geometry. ADR-0009 recorded that a second USB cable
  makes this fixture a ground bridge whose coupling "differs between the
  calibration run and the measurement run"; longer, more mobile cables make
  that term LARGER, not smaller. No mitigation is designed in, for the same
  reason as before — the right one depends on the user's bench — but the
  cables should be dressed identically between the two runs, and that belongs
  in the user documentation.
- **What we give up, honestly.** ADR-0006's push-on interface was a
  *no-cable* fixture: plug the board on, done. Cables are three more things to
  buy, three more things to lose, and six more connector interfaces in the
  path (≈0.66 dB at 6 GHz against the SMP path's ≈0.70 dB — a wash) plus the
  cables' own loss (≈3.0 dB at 6 GHz — not a wash). The calibration is a
  *measurement* of that path, so the loss costs SNR and not accuracy. It is
  the right trade at this board's power levels; it would not be at −80 dBm.
- **Placement is now FREE, and that is a real gain.** ARCHITECTURE §10 wanted
  the RP2040 and micro-USB as far as possible from the RF, the two loopback
  arms mirror-symmetric, and the SMA launches fenced. Under ADR-0006 three of
  the five ports were pinned to a foreign pitch of 11.60 / 11.98 mm with only
  ~3.95 mm of board web between adjacent notches. All five ports may now be
  placed where the RF wants them.
