# SUPERSEDED by cooksense-v1.4-2026-07-26 — DOCUMENTATION ONLY

## The board is unchanged and it is CORRECT

**Nothing is wrong with this board and nothing is wrong with these gerbers.**
`fab/`, `source/`, `3d/` and `pdf/` in v1.4 are **byte-identical** to the files
in this directory — verified by directory-wide sha256, and asserted by the
freshness gate in `--docs-only-supersede` mode.

- 226 footprints, 3925 tracks, **1047 vias**, all 0.25/0.15 mm
- **DRC 0 violations / 0 unconnected / 0 schematic parity**, reproducible from
  `source/` alone
- **H4 genuinely passes its isolation requirement at 6.5984 mm CREEPAGE** against
  6.000 mm required
- both v1.3 P0 fixes present in every artifact: `R_OPENT` = C37825 (62 kΩ),
  `R_WDPETPD` = C11702 (1 kΩ)

**If you are holding this release's fab package, the FILES are correct and need
no regeneration.** "Orderable" still means orderable *after* this release's own
`MANIFEST.txt` **MANDATORY BEFORE ORDERING** list — the unsupervised-door
decision, the order-day stock recheck, the 17-row §6 order-preview human gate,
the `R_OPENT` = C37825 check, and the non-conductive-enclosure assumption. **This
supersede clears none of those; it only replaces the assembly warning.**

## Why v1.4 exists

**This release's `MANIFEST.txt` `READ BEFORE ASSEMBLY` block is wrong in two
ways, and it is the block an assembler reads first.**

| | v1.3 MANIFEST said | correct |
|---|---|---|
| which notch bank governs | "H4's centre is 3.200 mm from the notch's **near** edge" | centre → **near (south)** bank y49.800 = **2.200 mm**; centre → **far (north)** bank y48.800 = **3.200 mm**. **The FAR bank governs**, because bridging requires the washer to reach the far side. |
| the collapse figure | "creepage collapses 6.5984 → **3.8286 mm**" | **3.8286 mm is the straight-line CLEARANCE, not creepage.** The true post-collapse **creepage** is **4.7195 mm**. The cliff is **6.3815 → 4.7195 mm**. |

**The harm the first error would have done.** An assembler follows
`READ BEFORE ASSEMBLY`, measures H4's centre to the nearest notch edge with a
caliper, gets **2.200 mm**, reads the document's claim of 3.200 mm, and applies
the document's own rule — *washer radius ≥ that distance ⇒ the washer bridges the
notch*. The **specified** DIN 125 A2.7 washer has radius 3.000 mm. They conclude
the specified part already destroys the barrier. **The clause written to prevent
a substitution would have condemned the part it exists to protect.**

## What was already right in this release

`ORDER_README.md` §1 was corrected **before this release sealed** and states both
distances, which one governs and why, with the corrected 4.7195 mm in the cliff
table. **The defect is not that the correction was missed — it is that the
correction landed in the document and not in the document's summary.** Nothing
checked the copies.

That is the whole lesson, and it is why v1.4's acceptance test is a
consistency **sweep** — grep every shipped file for the retracted strings and
report the count — rather than a re-read of the file that was edited.

## What to do

| you have | do |
|---|---|
| v1.3 **gerbers / BOM / CPL** | **Order them.** They are correct and byte-identical to v1.4's. |
| v1.3 **MANIFEST assembly warning** | **Do not use it.** Use v1.4's, or `ORDER_README.md` §1 REQUIRED FASTENER SPEC clause (2) in either release. |
| v1.3 **ORDER_README.md** | Correct as it stands; v1.4's adds only a release banner. |

**The fastener rule, stated correctly, in one line:** the maximum conductive
diameter at H4 is **6.0 mm** (DIN 125 A2.7), hard limit **6.3 mm**; at **6.4 mm**
the washer reaches the notch's **far** bank, bridges it, and creepage collapses
from 6.3815 mm to 4.7195 mm — a FAIL, invisibly.

## One note for anyone verifying this release's digests

`MANIFEST.txt` in this directory lists **80** files and **this file is not one of
them** — the directory holds **82** (80 digested + `MANIFEST.txt` + `SUPERSEDED.md`).
That is correct and expected: **v1.3 was sealed before it was superseded, and a
sealed release is immutable.** `SUPERSEDED.md` is the single sanctioned addition
to a sealed release, so it necessarily post-dates the digest list that cannot be
regenerated without breaking the seal. All 80 listed digests still verify with
**0 mismatches**. If you want a self-consistent digest list covering every file,
use **v1.4**, where `MANIFEST.txt` lists 80 of 81 (itself excepted).
