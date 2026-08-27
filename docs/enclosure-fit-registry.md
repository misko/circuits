# Enclosure fit and tolerance registry

This is the repository-wide evidence ledger for process-sensitive enclosure
dimensions. It records what was modeled, what physical subject it was compared
with, and how strongly the result has been demonstrated. Use it to choose the
centre of a new fit coupon—not as a table of universal defaults.

Registry snapshot: **2026-08-27**.

The owning procedure remains the
[PCB enclosure skill](../skills/pcb-enclosure/SKILL.md). Exact project source,
immutable enclosure releases, and dated physical records remain authoritative
for an individual design.

## Reading the numbers

For a circular feature:

`diametral allowance = CAD opening diameter - target diameter`

`per-side allowance = diametral allowance / 2`

Positive values are nominal clearance. Negative values are nominal
interference. For a slot or rectangular opening, apply the same rule to each
axis. These are CAD relationships; an FDM printed hole, gap, or wall is not
assumed to equal its modeled dimension.

Keep these feature classes separate:

- **press fit** — a hardware insertion fit, such as a heat-set or cold-press
  insert pilot;
- **clearance fit** — a non-retaining shell, panel, connector, or service
  opening;
- **compliant retention** — a clip, key, tongue, or flexure that intentionally
  deforms; and
- **bearing/contact** — a hard stop or support surface. Contact is not zero
  clearance everywhere else.

Do not transfer a number between feature classes merely because both are
described informally as “snug.”

## Evidence grades

| Grade | Meaning | Permitted use |
|---|---|---|
| `CAD_ONLY` | Authored dimensions and automated geometry evidence; no physical fit result | Centre a bracketed coupon only |
| `REFERENCE_GEOMETRY` | Traceable measurement of a reference model or article that is not the installed production part | Inform topology and coupon span; never substitute for target dimensions |
| `REPORTED_COUPON_SELECTION` | An immutable release records an operator-selected coupon result, but the registry lacks a complete raw process/measurement record | Reuse only as a prior for the same hardware and nominal process; requalify |
| `MEASURED_COUPON` | Coupon, printer, material, profile, orientation, local wall geometry, measurement, and outcome are all recorded | Seed the same process and feature geometry; still bracket after material or geometry changes |
| `ASSEMBLY_VERIFIED` | The actual installed part passed insertion, retention/removal, damage, and cycle checks under a dated test | Strongest local prior; not a universal tolerance |

A later result may supersede an earlier observation, but the earlier record
stays visible. A failed coupon is useful evidence and should not be deleted.

## Current comparison

The USB Hub 3S v3 and Pluto RX2 eight-way v5 enclosures do **not** use the same
press-fit size or tolerance.

| Feature | USB Hub 3S v3 enclosure v0.1.0 | Pluto enclosure lineage/current v0.6.0 | Same? |
|---|---:|---:|---|
| E-Z LOK 260-M3 nominal insert body | 4.216 mm | 4.216 mm | Yes—same hardware family |
| Modeled insert pilot | 3.95 mm, datasheet basis | 4.25 mm, coupon-selected basis | **No; Pluto is 0.30 mm larger** |
| Nominal pilot allowance against body | -0.266 mm diameter (-0.133 mm/side) | +0.034 mm diameter (+0.017 mm/side) | No—and this arithmetic does not predict printed grip |
| Closure locating fit | 0.30 mm skirt/base and skirt/post clearances | Current pillar-only base has no perimeter press-fit lip | No comparable active fit |
| Board-edge connector opening | XT60 +2.0 mm/side; USB-A and USB-C +1.0 mm/side | SMA throat +0.10 mm radius, outer access +1.0 mm radius against a D10 envelope | Different connector and purpose |
| Top antenna retention | Not applicable | Intentional compliant interference; see antenna records below | Not comparable |

Both cases specify PETG, a 0.4 mm nozzle, and 0.2 mm layers in their CAD
contracts. That common nominal process does not make the features equivalent:
local wall thickness, orientation, geometry, printer calibration, material
lot, and retention mechanism still differ.

## Observation records

### FIT-001 — E-Z LOK 260-M3 pilot, USB Hub candidate

| Field | Record |
|---|---|
| Feature class | Press fit / insert pilot |
| Evidence grade | `CAD_ONLY` |
| Target | E-Z LOK E-Z Press 260-M3-BR or 260-M3-CR; nominal body D4.216 mm, flange D5.537 mm |
| Modeled production pilot | D3.95 mm |
| Coupon ladder | D3.95, 4.05, 4.15, 4.25, 4.35 mm |
| Nominal process | PETG, 0.4 mm nozzle, 0.2 mm layer; coupon oriented like the production boss |
| Result | No coupon or insert-fit result recorded; enclosure status remains `INCOMPLETE` |
| Authority | [USB enclosure v0.1.0 README](../projects/usb-hub-3s-v3/07_enclosure_releases/v0.1.0-2026-08-27/README.md), [authored config](../projects/usb-hub-3s-v3/03_src/mechanical/enclosure.yaml), and [authored SCAD](../projects/usb-hub-3s-v3/03_src/mechanical/usb_hub_3s_v3_case.scad) |

Do not promote 3.95 mm as a production recommendation. Print the existing
ladder and record seating, boss damage, spin-out, and pull-out observations.

### FIT-002 — E-Z LOK 260-M3 pilot, Pluto selection

| Field | Record |
|---|---|
| Feature class | Press fit / insert pilot |
| Evidence grade | `REPORTED_COUPON_SELECTION` |
| Target | Same E-Z LOK 260-M3-BR or 260-M3-CR family; nominal body D4.216 mm |
| Predecessor production pilot | D3.95 mm |
| Selection ladder | D4.15, 4.25, 4.35, 4.45 mm |
| Selected modeled pilot | **D4.25 mm** |
| Nominal process contract | PETG, 0.4 mm nozzle, 0.2 mm layer |
| Result | Immutable v0.1.2 records 4.25 mm as the smallest reliable operator-selected coupon size; later Pluto candidates preserve it |
| Limitation | The release does not contain the complete raw printer/profile, insertion-force, pull-out, or cycle record required for `MEASURED_COUPON` |
| Authority | [Pluto enclosure v0.1.2 README](../projects/pluto-rx2-8way-v5/07_enclosure_releases/v0.1.2-2026-08-24/README.md) and [current config](../projects/pluto-rx2-8way-v5/03_src/mechanical/enclosure.yaml) |

This is the best insert-pilot prior currently in the repository, but it must
be requalified when the printer, material, orientation, boss wall, or insert
lot changes. The useful lesson is not that “4.25 mm always fits”; it is that a
3.95 mm datasheet start and a 4.25 mm printed-process selection differed by
0.30 mm in modeled diameter.

### FIT-003 — USB Hub lid and connector clearances

| Field | Record |
|---|---|
| Feature class | Clearance fit; not press fit |
| Evidence grade | `CAD_ONLY` |
| Lid location | 0.30 mm skirt-bottom clearance and 0.30 mm minimum skirt-end to case-post clearance |
| XT60 opening | 22 × 15 mm opening around an 18 × 11 mm candidate plug envelope: +2.0 mm/side on both axes |
| USB-A openings | 20 × 12 mm around 18 × 10 mm: +1.0 mm/side on both axes |
| USB-C opening | 17 × 11 mm around 15 × 9 mm: +1.0 mm/side on both axes |
| Result | Exact CAD obstruction collision is empty; physical lid closure and received-plug mating remain untested |
| Authority | [USB enclosure v0.1.0 README](../projects/usb-hub-3s-v3/07_enclosure_releases/v0.1.0-2026-08-27/README.md), [authored config](../projects/usb-hub-3s-v3/03_src/mechanical/enclosure.yaml), and [authored SCAD](../projects/usb-hub-3s-v3/03_src/mechanical/usb_hub_3s_v3_case.scad) |

Connector openings include access and received-overmold uncertainty; they are
not examples of a desirable snug fit.

### FIT-004 — Pluto board-mounted SMA access openings

| Field | Record |
|---|---|
| Feature class | Connector clearance/access fit |
| Evidence grade | `CAD_ONLY` for physical mating |
| Candidate coupling envelope | D10.0 mm |
| Inner throat | D10.20 mm: +0.20 mm diametral, +0.10 mm radial allowance |
| Outer access | D12.00 mm: +2.00 mm diametral, +1.00 mm radial allowance |
| Geometry | A frustum opens outward to admit the SMA coupling nut and tool/finger approach |
| Result | CAD interface and collision checks pass; current release does not contain a dated received-connector mating record |
| Authority | [Pluto authored config](../projects/pluto-rx2-8way-v5/03_src/mechanical/enclosure.yaml) and [authored SCAD](../projects/pluto-rx2-8way-v5/03_src/mechanical/pluto_rx2_8way_case.scad) |

Record connector body diameter, across-flat nut size, installed centre error,
tool access, and cable bend envelope before narrowing a future SMA opening.

### FIT-005 — Supplied compliant antenna-holder reference

| Field | Record |
|---|---|
| Feature class | `REFERENCE_GEOMETRY`; compliant retention inspiration |
| Evidence grade | `REFERENCE_GEOMETRY` |
| Measured holder void | D9.75 mm lower grip, D8.75 mm retention throat, D11.75 mm bottom mouth |
| Compliance geometry | Four 0.40 mm split slots, R1.0 mm entry blend |
| Candidate witness used for comparison | D10.0 mm lower antenna body; this is conservative derived geometry, not a production antenna measurement |
| Implied reference overlap | D9.75 grip: -0.25 mm diametral / -0.125 mm radial; D8.75 throat: -1.25 mm diametral / -0.625 mm radial |
| Authority | [Bound holder measurement](../projects/pluto-rx2-8way-v5/03_src/mechanical/reference/antenna-holder-measurement.json) |

The supplied STL proves the holder’s geometry, not the antenna’s dimensions.
Its gaps are only meaningful with its petal length, material, wall section,
slot width, print orientation, and real antenna.

### FIT-006 — Pluto v0.6 RX2 antenna candidate

| Field | Record |
|---|---|
| Feature class | Local compliant retention plus full-body loading clearance |
| Evidence grade | `CAD_ONLY` / physical fit required |
| Conservative witness | D10.0 mm lower L-shaped antenna body; actual antenna OD remains unmeasured |
| Compliant key | D8.50 mm gap: -1.50 mm diametral / **-0.75 mm per side** interference |
| Upright capture hole | D9.55 mm: -0.45 mm diametral / **-0.225 mm radial** interference |
| Open key mouth | 10.50 mm: +0.50 mm total / +0.25 mm per side clearance |
| Full-body loading arch | D10.80 mm: +0.80 mm diametral / +0.40 mm radial clearance |
| Coupon ladder | 8.25, 8.50, 8.75, 9.00 mm gaps |
| Automated result | All non-fit collisions empty; intended key and aperture overlaps are isolated and solid |
| Physical result | Not run; insertion force, retention, marring, permanent set, and cycle durability remain unknown |
| Authority | [Pluto enclosure v0.6.0 README](../projects/pluto-rx2-8way-v5/07_enclosure_releases/v0.6.0-2026-08-27/README.md) and [fit-adjustment record](../projects/pluto-rx2-8way-v5/03_src/mechanical/reference/fit-adjustment-2026-08-27.json) |

Do not use D8.50 or D9.55 as a future antenna default. They are deliberately
aggressive candidate values awaiting the existing fit-gauge and real-antenna
test.

## Choosing a future starting tolerance

1. Classify the feature as press, clearance, compliant, or bearing/contact.
2. Bind the exact target hardware drawing or traceable measurement. If that is
   unavailable, state the candidate envelope and readiness ceiling.
3. Filter this registry to the same feature class, hardware family, material,
   orientation, local wall/flexure geometry, and evidence grade.
4. Use the closest credible record only as the centre of a bracketed coupon.
   Include a datasheet/measurement-based station even when a prior process
   result suggests another value.
5. Print the coupon with the production printer, material, slicer profile,
   orientation, and local wall section.
6. Measure the printed feature and test the real mating part. For retention,
   record insertion/removal force or a repeatable qualitative scale, surface
   damage, rattle, pull-out tendency, and cycles.
7. Preserve the failed and selected stations in project evidence. Add a new
   registry record only after its authority and limitations are explicit.

## Record template

Copy this table into a new observation section; never overwrite a prior
record to make the current design look cleaner.

| Field | Required value |
|---|---|
| Record ID and date | Monotonic `FIT-NNN`, ISO date |
| Feature class | Press / clearance / compliant / bearing |
| Evidence grade | One exact grade from this document |
| Target authority | MPN+drawing revision, measured article, or explicit candidate envelope |
| CAD geometry | Diameter or per-axis opening, lead-in, flexure/wall geometry, and local orientation |
| Allowance | Total and per-side, with sign |
| Print process | Printer, nozzle, material/lot, layer, extrusion/scale compensation, slicer/profile, orientation |
| Coupon | All station values and which station was selected or failed |
| Physical method | Measurement tool, fit/force method, cycle count, temperature if relevant |
| Result | Pass/fail observations and damage/rattle/retention outcome |
| Authority | Immutable release or dated project evidence link |
| Limits | What this result does not prove |
