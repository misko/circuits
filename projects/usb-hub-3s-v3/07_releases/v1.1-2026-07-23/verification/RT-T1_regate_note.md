# RT-T1 re-gate note — topology verdict is substantively ORDER

**Purpose.** This note records why the release seals with topology = ORDER even
though the *original* archived topology memo
(`2026-07-22_v1.0_redteam_topology.md`) carries the verdict word
**DO-NOT-ORDER**. That memo is immutable and shipped verbatim; this note is the
disposition that sits beside it. Nothing in either memo was edited.

## The original DO-NOT-ORDER was driven by exactly one P1, now fixed

- The original topology red-team returned **DO-NOT-ORDER**, and stated in its own
  rationale: **"No P0 exists."** The single order-blocking finding was **RT-T1**:
  the input fuse was doubly-specified — silk `FUSE 10A MINI` vs
  `02_parts/3568/part.yaml` element `20A/0297020` — and the 20 A value was a
  **stale carry-over of v1/v2's 15.5 A buck-boost trunk**, leaving the ~8–27 A
  overload band unprotected on this 6.8 A board.
- **RT-T1 is FIXED in-tree** (committed `071fe56`, before this seal):
  - `02_parts/3568/part.yaml` reconciled to a **10 A** element (Littelfuse
    0297010) for the 6.8 A worst-case trunk, with the 15.5 A→6.8 A justification
    corrected.
  - Board silk reads **`FUSE 10A MINI`**; **zero** `20A` strings remain on the
    board (verified: silk-text extraction over `usb_hub_3s_v2.kicad_pcb`).

## An independent zero-context re-review then returned ORDER

`2026-07-22_v1.0_redteam_topology_rereview.md` (committed `81faa99`) is a fresh,
zero-context topology red-team that read only the design source (no prior memo).
Its **HEADLINE VERDICT: ORDER**, and on the fuse specifically:
**"RT-T1 fuse verdict: YES — 10 A is correctly sized."** It re-derived the trunk
current from first principles (55 W out / 0.9 / 9.0 V = **6.79 A ≈ 6.8 A**) and
placed 10 A at **1.47× continuous-max** — a textbook 1.25–1.5× fuse ratio —
confirming no nuisance-trip (68 % loading, gentle soft-started inrush) and real
overload protection the 20 A element did not give.

The re-review also independently describes the assembly split this release
ships: **"hand-inserted MINI blade element (e.g. Littelfuse 0297010) in a
machine-placed Keystone-3568 holder"** — i.e. the F1 holder (C5249699) is on the
CPL/BOM (JLC places it), the 10 A blade element is off-CPL and hand-fitted.

## Disposition

- **Topology: substantively ORDER.** The sole P1 blocker is fixed, and an
  independent checker (not sharing a method with the fixer) confirms the fix by
  first principles. Per `07_releases/contracts.md`, only a **P0** hard-blocks a
  release; there is no P0 in either memo.
- The one remaining open item, **F-2.1** (LM5116 UVLO turn-on ≈ 9.65 V rising /
  8.84 V falling, above the BRIEF's 9.0 V nominal floor), is a **documented P2**
  per explicit user decision: cold-start from a 9.0–9.65 V pack is **not** a
  requirement, and the elevated UVLO doubles as LiPo deep-discharge protection.
  Recorded in `ORDER_README.md` (next-rev work order).
- **Layout lens** (`2026-07-22_v1.0_redteam_layout.md`): **ORDER**, zero P0/P1;
  every finding P2.

**Both lenses = ORDER; zero unresolved P0. Cleared to seal.**
