# 10FDZ-BT land-pattern confirm — the physical-part gate

status: **OPEN — USER-HELD.** Nothing in this repo can close it.
gate: `07_releases/interposer-v1.0-2026-07-24/ORDER_README.md` §0 gate 1
blocks: fab ORDER of the interposer (Board C). Not the seal, not the design.
written: 2026-07-27
part: JST `10FDZ-BT(S)(LF)(SN)` — `02_parts/10FDZ-BT/`, datasheet `eFDZ.pdf`

---

## 0. Why this gate exists (read once, it takes 30 seconds)

The interposer's `J_MEMBRANE` and `J_CN1_JUMPER` land pattern was authored from
**one drawing** — eFDZ p.3, "PC board layout and Assembly layout / Top entry
type" — whose own **note 4** says:

> "Hole dimensions differ depending on the type of PCB and PCB drilling method.
> The above dimensions are for reference only. Please contact JST for further
> details."

The drawing also **never numbers the circuits**. So two things are unproven:

1. **Fit** — do the real pins and the real polarization boss drop into our
   ø0.90 / ø1.80 holes?
2. **Polarity** — which end of the housing carries circuit 1? Our footprint
   assumes *circuit 1 = the boss end*. If the real part is the other way round,
   the pass-through still works (all ten lines still pass) but **every U/D label
   and test point on the board names the wrong physical conductor**
   (`verification/redteam_topology.md` P1).

You now have the connectors in hand. This document is the instrument.

---

## 1. What the SHIPPED files actually contain (independently re-measured)

Measured out of the sealed release, not out of the CAD:

| fact | value | source |
|---|---|---|
| signal holes | **20 × ø0.900 (T2 C0.900)** — two rows of 10 | `fab/interposer-PTH.drl` |
| pitch set | **{2.5400} exactly**, no accumulation | same |
| row span, pin 1 → pin 10 | **22.8600 mm** (25.000 → 47.860) | same |
| polarization bosses | **2 × ø1.800 NPTH (T1 C1.800)** at x=22.460 | `fab/interposer-NPTH.drl` |
| boss offset | **2.5400 mm outside pin 1**, colinear on the row centreline | same |
| pad | 1.60 mm on 0.90 mm drill → **0.35 mm annular ring** | footprint |
| pin 1 marker | **RECT pad**; pins 2-10 circles | footprint |
| both connectors | placed at rotation 0, pin 1 west, boss further west | `source/interposer.kicad_pcb` |

Datasheet values the above was derived from (eFDZ, re-read 2026-07-27):

| eFDZ | value |
|---|---|
| p.2 table, 10 circuits | A = **22.86**, B = **36.26** |
| p.3 top-entry board layout | ø0.9±0.05 holes, pitch 2.54±0.05, ø1.8±0.05 boss 2.54 outside the first hole, (5.3) housing edge → first hole, (2.6) front edge → row |
| p.2 outline | depth **7.7**, installed height **10.2**, slider open **(12.7)**, pin protrusion 3.5 |
| p.1 | applicable PCB thickness **1.6 mm**; 50 mA / 250 V; contact R 10 Ω initial / 15 Ω after test |

Derived once, and it is the polarity discriminator you can measure with nothing
but a caliper: B − A − 5.3 = 36.26 − 22.86 − 5.30 = **8.10 mm**. The housing is
**asymmetric** — it overhangs the end pin by **5.30 mm on the boss end** and
**8.10 mm on the far end**.

---

## 2. The 1:1 overlay — use the SEALED PDFs, do not generate anything

No new artifact is needed. Two pages already in the sealed release print 1:1.
Both were verified by rendering at 1200 dpi and measuring the ink:

| page | what it proves | 1:1 verification (measured) |
|---|---|---|
| `pdf/pcb_layers.pdf` **page 1 of 7** (F.Cu, top copper, component-side view) | **the drill pattern**: 10 pads with open ø0.9 centres, the square pin-1 pad, and the ø1.8 boss as a solid dot | mounting-hole dots measured at x = 13.991 / 59.986 mm and ø2.710 vs nominal 14.000 / 60.000 / ø2.700 → **1:1 within 0.01 mm** |
| `pdf/assembly.pdf` (1 page) | **the housing outline and orientation**: the 36.26 × 7.70 body rectangle, the silk "1" and "10" numerals, the board edge | board outline ink measured 9.948 → 64.008 mm and 9.948 → 56.007 mm vs a 54.00 × 46.00 board with 0.15 mm line → **1:1** |

**`assembly.pdf` alone is NOT sufficient** — it plots fab/silk outlines only. It
contains **no pads and no holes**. Use it for the housing and the numerals; use
`pcb_layers.pdf` page 1 for the hole pattern.

### Print settings (both files)

- A4, **landscape**
- Scale: **100% / "Actual size"**. **Fit to page OFF. "Shrink oversized pages"
  OFF. Auto-rotate-and-centre OFF.** Any of these silently scales the print and
  makes the overlay a lie.
- Print `pcb_layers.pdf` **page 1 only** (`-P 1`), not the whole file.

### Calibrate the printout BEFORE you trust it

| print | measure | must read | if it does not |
|---|---|---|---|
| `pcb_layers.pdf` p1 | centre-to-centre, the two big dots on the same long edge (horizontal) | **46.00 mm** | reprint — the driver scaled it |
| `pcb_layers.pdf` p1 | centre-to-centre, the two big dots on the same short edge (vertical) | **38.00 mm** | reprint |
| `pcb_layers.pdf` p1 | square pad centre → far end round pad centre, one row | **22.86 mm** | reprint |
| `pcb_layers.pdf` p1 | row-to-row, matching pads | **26.00 mm** | reprint |
| `assembly.pdf` | outer board rectangle | **54.00 × 46.00 mm** | reprint |

Tolerance on the calibration: **±0.3 mm**. Outside that, the print is scaled;
do not use it.

### The overlay test

Lay the connector **pins DOWN** on `pcb_layers.pdf` page 1, over either
connector row. Pins-down is the same view as the plot (both are "seen from the
component side"), so **nothing is mirrored** — do not flip the page, do not
flip the part.

**PASS** = all ten pins sit inside the ten printed rings *and* the boss sits on
the solid dot, **simultaneously and without forcing the part sideways**.

**FAIL** = the boss lands on the far end, or lands off the row line, or the pins
walk off the rings across the row (that is a pitch error).

---

## 3. Caliper measurements — take these on the PART

Digital caliper, mm, on **one** connector; then repeat #1/#3/#9/#10 on a second
to catch a mixed bag. Measure pin **centres** where stated (measure outside-to-
outside and subtract one pin width if that is easier).

| # | measure | expected | PASS band | CONDEMNS the footprint if |
|---|---|---|---|---|
| M1 | end pin centre → other end pin centre (9 pitches) | **22.86** | 22.71 – 23.01 | 11.43 (a 1.27 mm part) · 20.32 (9-way) · 25.40 (11-way) — **wrong part** |
| M2 | pin 1 centre → pin 5 centre (4 pitches), then ÷4 | **2.540** | 2.52 – 2.56 | ≤ 2.50 or ≥ 2.58 — pitch is wrong, holes will not line up across the row |
| M3 | boss centre → nearest pin centre | **2.54** | 2.39 – 2.69 | > 0.2 off — the boss NPTH is in the wrong place |
| M4 | boss diameter | ~1.70 (nominal for a ø1.80 hole) | ≤ 1.75 | **> 1.80** — the boss will not enter the hole. STOP |
| M5 | pin cross-section (largest dimension) | ~0.6 | ≤ 0.80 | **> 0.90** — pins will not enter. STOP |
| M6 | housing length (B) | **36.26** | 36.0 – 36.5 | 31.18 → 8-way · 33.72 → 9-way · 38.80 → 11-way — **wrong circuit count** |
| M7 | housing depth (front face → back face) | **7.70** | 7.5 – 7.9 | out of band, or the **tail slot opens SIDEWAYS instead of upward** — that is **10FDZ-ST, the WRONG VARIANT** (different land pattern: its row sits 8.2 mm from the outline, not 2.6). Do not use it. "BT" must appear on the label |
| M8 | housing height, slider closed / slider open | **10.2 / 12.7** | ±0.4 | (clearance check only, not a condemn) |
| M9 | **boss-end** housing face → nearest pin centre | **5.30** | 5.0 – 5.6 | see M10 |
| M10 | **far-end** housing face → nearest pin centre | **8.10** | 7.8 – 8.4 | **if M9 reads ≈8.1 and M10 reads ≈5.3, the boss is at the opposite end from the drawing → our footprint is MIRRORED. STOP, report, do not order** |
| M11 | count the pins | **10** | exactly 10 | — |
| M12 | boss is on the **bottom** face, on the **same line** as the pin row | yes | — | boss offset off the row line → footprint wrong |
| M13 | with the part on a 1.6 mm scrap: pin length below the board | ~1.9 (3.5 − 1.6) | > 1.0 | < 0.5 — not hand-solderable, needs a thinner board |

M1, M2, M3, M9/M10 are the four that matter. M4/M5 are go/no-go: if the boss or
the pins do not fit the holes, the boards are scrap whatever else reads right.

---

## 4. Polarity — which end carries circuit 1

The datasheet does not answer this. **You do not need JST's answer.** Adopt the
convention the board already uses and make everything else agree with it:

> **Pin 1 = the contact at the BOSS end.** That is the square (RECT) pad on the
> board and the silk numeral "1"; it carries `KP_U1`. Pin 10 (`KP_D4`) is at the
> far end.

That convention is self-consistent *provided the same reference is used at the
appliance*. So the one thing to record is which end of the **OEM's CN1** is its
boss end:

- **P1.** On the appliance board, find CN1's ø1.8 polarization-boss hole (it is
  the un-plated hole in line with the ten contacts, one pitch outside an end
  contact). **Which end of CN1 is it at — the same end the OEM silkscreen calls
  pin 1, or the opposite end?** If CN1 is inaccessible, use M9/M10 on CN1's own
  housing instead: the **5.30 mm** overhang end is the boss end.
- **P2.** Does the connector carry any moulded or printed "1", triangle, or
  chamfer? If yes, **which end** — boss end or far end? Photograph it.

**Both answers are recorded, not acted on.** They do not change the copper. They
decide only whether `TP_M_U1 … TP_M_D4` name the conductors the OEM names the
same way, and that is what a mirrored read would silently corrupt.

Cross-check that costs nothing: with the OEM tail seated in `J_MEMBRANE`, the
tail's contacts face one way only — a 10FDZ-BT has contacts on one side of the
slot, so the tail **cannot** be inserted flipped and still make contact. The
insertion is self-keying; only the *naming* is at risk.

---

## 5. New: two questions the datasheet just raised (answer them while you have
the part in your hand)

Re-reading eFDZ p.3 on 2026-07-27 turned up something that contradicts a
recorded decision. The **"Recommended dimensions for membrane switch lead"**
drawing shows the tail with **two punched oblong slots** — 1.2 ±0.1 mm wide ×
3 ±0.2 mm long, one near each end, each centred **3.81 ±0.1 mm inboard of the
outer conductor centreline**, the slot starting **5 ±0.2 mm back from the tail's
leading edge**. (Measured off the drawing at 1200 dpi against its own 2.54 mm
pitch: 4.98 / 2.99 / 3.796 mm.)

ADR-0008 states the opposite — "a genuine FDZ would not use, or need, tail
holes" — and used the OEM tail being *plain* as its decisive evidence. ADR-0005
(D5) had earlier recorded, from photos, that the OEM tail **does** have two
punched lock-slots. The datasheet sides with ADR-0005's observation. See
ADR-0017; this does **not** overturn the 10FDZ-BT identification, but it does
retire the argument, and it changes the flex-jumper design.

While the part is in your hand:

- **S1.** Look into the slider / the contact slot. Are there **two lock pips or
  hooks** positioned to catch a slot ~3.81 mm inboard of each outer contact?
  Photograph.
- **S2.** Re-photograph the **OEM keypad tail**: does it have two punched
  oblong slots, or is it plain? (This settles D5 vs D8 and decides whether the
  flex jumper is built slotted or plain — see `01_docs/flex-jumper-spec.md`.)

---

## 6. Verdict — fill this in and report back

```
10FDZ-BT PHYSICAL CONFIRM — reported by: ............  date: ..........
connectors measured: ....  (qty)   lot/marking on label: ................

print calibration     46.00 ....  38.00 ....  22.86 ....  26.00 ....  54x46 ....
overlay test          PASS / FAIL      (pins + boss drop in together?)

M1  span 9 pitches    ........   M8  height cl/open  ...... / ......
M2  pitch             ........   M9  boss-end face→pin  ........
M3  boss→pin 1        ........   M10 far-end face→pin   ........
M4  boss dia          ........   M11 pin count          ........
M5  pin size          ........   M12 boss on row line   Y / N
M6  housing length    ........   M13 pin below 1.6mm    ........
M7  housing depth     ........

P1  CN1 boss end is at the ......... end (same as / opposite to OEM pin 1)
P2  moulded "1" or key mark?  none / at boss end / at far end
S1  slider lock pips?         yes / no      S2  OEM tail slots?  yes / no

VERDICT:  PASS — order fab   |   FAIL — see notes   |   MIRRORED — do not order
notes: ......................................................................
```

**PASS** requires: overlay test PASS **and** M1-M3 in band **and** M4/M5 go
**and** M6/M7 in band **and** M9≈5.30 with M10≈8.10.

**Any single FAIL keeps the gate shut.** M4, M5, M7 and the M9/M10 swap are
hard stops — they mean the boards would be scrap, not merely mislabelled.

---

## 7. Status of this gate

**OPEN.** It cannot be closed from this repo, by any agent, by any amount of
re-measuring the CAD — the CAD is the thing under test. `STATUS-interposer.md`
carries it as USER-HELD and unchanged. The interposer release is separately
**DO-NOT-ORDER** for an unrelated CPL rotation defect (task #18); closing this
gate does not unblock ordering v1.0, it unblocks ordering the **v1.1 re-seal**
that fixes the CPL.

When you report the filled block above, the results land in
`02_parts/10FDZ-BT/part.yaml` (`verified:` → replace `NEEDS-PHYSICAL-CONFIRM`
with the measured numbers and the date) and in an ADR if anything reads wrong.
