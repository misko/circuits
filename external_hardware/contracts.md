# contract: external_hardware/

**Purpose** — MEASURED reference data about hardware **we did not design** and
must mate to: connector geometry, port maps, enclosure constraints, board
outlines. One folder per device.

## Why this is not `projects/` and not `examples/`

`projects/` holds boards this repo designs. `examples/` holds frozen snapshots
of our OWN worked evidence that skills may cite. Neither fits a caliper reading
taken off someone else's product.

It is separate from any one board because the data OUTLIVES the board that
prompted it. `plutoplus_hardware/` was measured for `pluto-cal-switch`, but the
next board that talks to a PlutoPlus should not re-measure it — the same
compounding rule as `proven-parts.yaml`, applied to mechanical facts instead of
part selections.

## Allowed

| Pattern | What |
|---|---|
| `README.md` | registry purpose, authority boundary, and consumer entry point |
| `plutoplus_hardware/**` | ADALM-PlutoPlus SDR — SMA port geometry, port map, enclosure, two physical units measured |
| `contracts.md` | this file |

Inside a device folder, two names are FIXED because machines read them:
`README.md` is the human record, and `facts.yaml` is its machine index — the
only thing a board is allowed to reference (canon M-IMPORT / D-MATE, ADR-0005).

Each device gets its own `<device>/**` row naming the device, deliberately —
rather than a blanket `*/**` — so that adding a device is a decision recorded
here, and so the reader can see at a glance what hardware this repo has
measured. Coverage is WHOLESALE within a device folder because the internals are
data (a README, photographs, occasionally an extracted file), not a structure
worth policing.

## Audit

- Each `<device>/README.md` is the device's record and MUST state, for every
  number, **how it was obtained**: caliper on a physical unit, extracted from a
  vendor file, or photogrammetric estimate. A dimension with no stated method is
  a defect here, because these numbers get built into copper and the reader
  cannot re-derive them.
- **Separate MEASURED from ESTIMATED from NOT ESTABLISHED, explicitly.** The
  "not established" list is the most valuable section: it is what stops a
  downstream board assuming a number nobody has.
- Where a vendor file and a physical measurement disagree, record BOTH and say
  which wins and why. **The physical object wins over its drawing** — a drawing
  is a proxy for the thing, and this repo has already paid for measuring a proxy
  instead of the property (canon M1).
- Photographs are evidence, not decoration: name what each one shows and why it
  is worth keeping. A photo that proves a field-identification tell (a shield
  can, a silk label) earns its place; a general product shot does not.
- Where multiple physical units of nominally the same device exist and DISAGREE,
  that disagreement is the headline finding, not a footnote.
- **`<device>/facts.yaml` is the MACHINE INDEX of the README, and it is graded
  against it.** One entry per number a board may reference:
  `{id, what, value (a STRING, exactly as the record writes it), units, grade,
  method, quote}` plus `error_bar` for ESTIMATED and `how_to_obtain` for OWED.
  `grade` is the closed M-IMPORT vocabulary **MEASURED / CITED / ESTIMATED /
  OWED**. `quote` MUST appear in the record VERBATIM, with the value inside it —
  that is what stops the index and the record drifting, which is the failure
  mode any second home creates (cooksense v1.1's CPL vs its own MANIFEST).
  Run `skills/kicad-pcb/scripts/import_provenance_check.py --root <repo>`.
  An entry here is a claim that someone can DEFEND the number: a fact with no
  bar and no method belongs in the README's "NOT established" list instead, and
  a board that references it dimensionally fails M-BAR — correctly.
- **OWED is a first-class grade, not a gap in the table.** A number nobody has
  is recorded with how to obtain it and what it blocks. The alternative is that
  a downstream board invents a plausible one, which is the failure this whole
  folder exists to prevent.

## Repair

- A number that cannot state its method → re-measure it or delete it. There is
  no third option; an unattributed dimension is worse than a gap, because a gap
  is visible.
- A device folder that has drifted from the physical unit → re-measure and
  supersede the numbers in place, with the date. These are observations, not
  releases: they are not immutable, but they ARE dated.
