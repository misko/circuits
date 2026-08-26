# CHANGELOG — pluto-rx2-8way-v2

8-way RF receiver splitter / switch matrix for the PlutoSDR RX chain.
One entry per REVISION (a design state). Reverse-chronological.
`Released:` is `no`, or the name of the `07_releases/` directory that shipped it.

> ## ⚠ NO `07_releases/` DIRECTORY EXISTS FOR THIS BOARD YET
>
> **Nothing here has been sealed.** `07_releases/` holds only its
> `contracts.md`. The complete archive lives at `06_build/staging/` and is
> explicitly marked `*** STAGED, NOT SEALED ***` in its own `MANIFEST.txt`.
>
> This file exists BEFORE the first seal on purpose. `policy_audit`'s **M-REL**
> checks the CHANGELOG with `if cl.exists()` — so on a project with no
> CHANGELOG the check is a **SILENT SKIP**, and it skips precisely where there
> is nothing yet to check. A board that has never had a CHANGELOG is
> indistinguishable from one whose CHANGELOG is complete. Four sealed boards in
> this fleet carry one (223 / 480 / 1347 / 1454 lines); this board carried none
> until 2026-07-31.
>
> When the seal commit lands it MUST add the release-directory name to the
> newest entry below — that is the string M-REL looks for, per release
> directory, across the whole project.

---

## v1.0 — 2026-07-31 — first orderable state (STAGED, not sealed)  [tag: none yet]

**Released:** `no` — staged at `06_build/staging/`.
**Fab tier:** `jlc_4layer_advanced`, stackup **JLC04161H-7628** (1.6 mm),
0.25/0.15 mm vias, impedance control requested.
**Board:** 50.10 × 73.10 mm, 4 copper layers, 32 footprints, 27 CPL
placements, 11 BOM lines, 3446 vias.

### What it is

Ten vertical SMA ports (`J_ANT1..8`, `J_RX1`, `J_RX2`) around a PE42482A-X
SP8T in a QFN-24, driven by an RP2040-Zero module. Nine equal-radius
14.00 mm GCPW arms in a star, so the arm phases are comparable; `In1.Cu` is an
unbroken reference beneath every arm apart from the launch antipads.

### The gates it stands on (all MEASURED, all UNPIPED, RAW exits in ORDER_README)

| gate | result |
|---|---|
| DRC `--severity-all --refill-zones --schematic-parity` | 0 violations / 0 unconnected / 0 parity |
| netlist parity, node-for-node | 0 over 24 nets / 114 nodes |
| ERC errors | 0 (209 warnings baselined: 120 `endpoint_off_grid` + 89 `lib_symbol_issues`, both converter geometry/symbol artefacts) |
| `fence_pitch.py` | worst interior along-arm gap 1.1769 mm vs λ_pp/20 = 1.1910 mm; 22 arm-sides, 0 OVER |
| `fence_apertures.py` | 0 apertures over the same bound, over 3473 fence elements |
| P-LAND escape | 47 graded / 130 copper pads, 0 failing |
| jlc_twin | 26 OK / 56 rows, bodies mounted 27/27, 0 CRITICAL |
| live LCSC stock | 11/11 coded lines ≥ 5× qty |

### The revision's own history — the defects it was cut around

Each of these was found and FIXED inside this revision; none of them shipped.

- **The seal was refused once already** (`c7ebda44`): the board went green on
  every machine gate and two zero-context lenses called it DEFECTIVE anyway.
  Everything below is downstream of that refusal.
- **The RF tap was a quarter-wave stub** (`5425538b`) — fixed by a placement,
  a board width and a corridor, not by a rule change.
- **The arms were never microstrip** (`c566911b`): re-classified as
  conductor-backed coplanar waveguide, which made the stitch bound TIGHTER
  (λ_pp/20 = 1.1910 mm, not the microstrip figure).
- **A stitch guard sat 0.05 mm above the pitch** (`1dedd3e8`), so asking for a
  FINER fence made the fence SPARSER.
- **The fence classifier counted 3433 of 3473 grounds** (`70f0a1e9`) — it saw
  only `PCB_VIA` and missed the 40 PTH GND launch posts, and so reported a
  1.9000 mm aperture on `RX1_TAP` that does not exist. Its sibling gate
  `fence_pitch.py` had it right all along.
- **The vendored pad numbering was invented on a false premise** (`16c54169`)
  and the vendor's is its exact reverse; the RP2040-Zero module additionally
  cannot sit down on a flat carrier (23 components on its carrier-facing face,
  tallest 1.000 mm), so it is hand-soldered — `on_bom: false`, off the CPL.
- **Ten RF ports sat on an SMT-only CPL with fifty plated holes and paste on
  none of them** (`2e6815c0`). Resolved by BUYING the through-hole line rather
  than declaring a hand-solder wall: C504007 is in JLC's assembly library as a
  `Plugin` part. Selecting that process is an ORDER-TIME HUMAN GATE.
- **The generated sheet drew two nets as one conductor** (`37ff74d3`,
  `0a021353`): 49 wires → 35, S-WNET 0 over 35 wires, and the netlist did not
  move a single node — symdiff 0 across 40 nets.

### Fixed at 2026-07-31, after the independent seal judge refused the archive

The copper was never in question and did not move; every finding was in the
SHIPPED ARTIFACTS, and a seal freezes artifacts.

- `fab/bom.csv` + `fab/cpl.csv` — the archive shipped the exporter's
  `bom_jlc.csv`/`cpl_jlc.csv` instead. **Fixed in the producer**
  (`export_jlc_package.py`), not by a hand-copy: the contract and all 34 sealed
  releases require the plain names, and `release_freshness_check.py` resolves
  A-STOCK and A-BUY through `fab/bom.csv` — with the name absent both gates
  reached a ZERO DENOMINATOR and emitted NOTES instead of failures.
- `verification/fence_apertures.txt` was the PRE-FIX output, asserting a
  1.9000 mm violation of a 1.1910 mm bound inside the same directory where
  `fence_pitch.txt` said PASS / 0 OVER. Re-run: 0 apertures.
- Ten contract-REQUIRED artifacts were absent (`A-EVID`); all ten now present.
- `ORDER_README.md` named no fab option at all — no stackup, no surface finish,
  no via tier — while 3446 of 3496 holes are under JLC's standard-tier process
  minimum. The exact required sentence already existed verbatim in
  `03_src/rules/nets.yaml`; it now reaches the document a human reads.
- `verification/bom_source_check.txt`, `bom_legibility.txt` and
  `part_facts.txt` all named `07_releases/v1.0-2026-07-30/`, a directory that
  does not exist. Re-run against the real staging path. **Sealing under that
  name would have turned the gate green without making the evidence truer.**
- `MANIFEST.txt` gained `git_dirty:` and a current `git_sha:`.
- This file.

---

## v0.1 — 2026-07-30 — commission through schematic gate  [tag: none yet]

**Released:** `no`.

`ea6d1fa1` … `17a21f2d`. D-SPEC settled the module-vs-PICO tension on spur
grounds; ARCHITECTURE + DETAIL_DESIGN re-derived every number rather than
copying it; the tscircuit scaffolding landed with its own preflight; 13
schematic-stage gates, every one exit 0, every one run unpiped.
