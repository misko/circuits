# Connector assembly evidence registry

This repository-wide ledger records connector, mate, tool, cable, process, and
service-state combinations. Use a close record only to plan a bracketed coupon
or first-article test. It is not a table of universal pitches, openings,
overhangs, bend radii, or hand clearances.

Registry snapshot: **2026-08-27**.

The machine authority for one design is its authored
`03_src/rules/connector_assemblies.yaml` plus the freshly compiled receipt. The
[connector assembly contract](../skills/pcb-design/references/connector-assembly-contract.md)
owns the procedure.
Project source, immutable releases, and dated physical records remain
authoritative for their exact subjects.

## Evidence semantics

Keep geometry authority separate from physical outcome:

| Contract grade | Meaning |
|---|---|
| `exact` | The selected fact is bound to an exact cited source for the stated hardware/process scope |
| `conservative` | The bound geometry deliberately contains the cited exact or measured subject and states its allowances |
| `unknown` | The fact is absent, ambiguous, or only qualitative; it blocks a complete connector receipt |

| Physical outcome | Meaning |
|---|---|
| `NOT_RUN` | No operation on the exact combination is recorded |
| `REPORTED_FAIL` | A dated operator report establishes a problem but lacks the complete measured test record |
| `COUPON_TESTED` | Exact hardware, coupon, process, state, method, and result are recorded |
| `FIRST_ARTICLE_VERIFIED` | The fabricated board/enclosure combination passed all declared operations and simultaneous groups |

A `REPORTED_FAIL` is enough to reject the observed design claim. It does not
create a replacement dimension. `exact` geometry does not imply physical fit,
and a physical pass cannot upgrade an uncited manufacturer fact to exact.

Typed source roles are part of the evidence claim. Drawings and dossiers may
support explicit dimensions, but only the contract's closed 3D-model kinds may
serve as `model_source_id`, and only its closed placement/orientation kinds may
serve as `orientation_source_id`. A filename ending in `.step` or a prose note
saying “oriented” does not establish either role.

## Combination records

### CONN-001 — Pluto RX2 eight-way v5 dense SMA bank

| Field | Record |
|---|---|
| Date | 2026-08-27 |
| Receptacle | Amphenol RF `901-143-6RFX`, right-angle through-hole SMA jack |
| Supported mate | `unknown`; the reported antenna/cable plug MPN and coupling-body geometry were not recorded |
| Tool and torque | `unknown`; no selected wrench solid, sweep, counter-hold, or connector-specific torque authority was bound |
| Cable/termination | `unknown` |
| Realized PCB geometry | Exact board source uses 15 mm pitch on the five-port north bank, 18 mm pitch on the side banks, and nominally flush mating planes at the board edge |
| Simultaneous state | `unknown`; prior CAD review did not bind a fully populated mate/cable/tool state |
| Physical outcome | `REPORTED_FAIL` / qualitative `FIRST_ARTICLE_OBSERVATION`: operator reports that adjacent SMA connectors are difficult to hand tighten and lack enough outboard exposure for a good grip |
| Evidence ceiling | `unknown` for replacement spacing, exposure, tool, torque, cable, and enclosure service allowances |
| Existing authority | [unbound qualitative connector-service observation](../projects/pluto-rx2-8way-v5/03_src/mechanical/reference/pluto-v5-unbound-qualitative-connector-service-observation-2026-08-27.md), [floorplan source](../projects/pluto-rx2-8way-v5/03_src/floorplan.yaml), and [prior render review](../projects/pluto-rx2-8way-v5/08_reviews/2026-08-13_dae8320d_render_review.md) |
| Correct use | Reject the earlier render-only access conclusion; select actual mates/tools, measure the board, and build a connector-bank coupon before choosing new pitch or overhang |

The useful reusable result is the failure class: bare-body and mating-axis
clearance did not prove an executable hand/tool operation. The 15 mm or 18 mm
pitch must not be copied as a passing or failing universal SMA threshold; the
unknown mating body, tool, torque method, enclosure state, and neighbor census
change the required service cell.

The current enclosure schema-v2 adapter binds the shared connector receipt and
its ref/group census, but its schema-v1 CAD subject still contains separate
inline plug/clearance candidates and it does not yet execute complete
plug/tool/cable solids. Therefore no enclosure row may claim that the shared
contract has already eliminated duplicate v1 dimensions or physically closed
the Pluto service failure.

### CONN-002 — USB Hub 3S XT60 mated lead versus lid skirt

| Field | Record |
|---|---|
| Date | 2026-08-27 |
| Receptacle | Board-mounted XT60-family input; exact physical article and printed enclosure revision unbound |
| Supported mate | Received XT60 lead assembly; exact MPN, rear termination, heat-shrink, and cable construction unbound |
| Tool and torque | Hand-mated; insertion/removal force and reaction path unmeasured |
| Cable/termination | Qualitatively thick lead with a rising/flaring rear exit; no OD, straight run, bend radius, or exit-vector measurement |
| Prior enclosure assumption | A 22 × 15 mm opening around an 18 × 11 × 35 mm candidate plug envelope (+2.0 mm/side on two opening axes) |
| Simultaneous state | Physical XT60 lead mated; other simultaneous leads and lid service sequence unbound |
| Physical outcome | `REPORTED_FAIL` / `FIRST_ARTICLE_OBSERVATION`: rear termination/cable occupies the lid-skirt service volume and creates interference/chafe risk |
| Numeric result | None; this rejects the two-axis opening-only model, not a measured +2.0 mm/side allowance |
| Existing authority | [unbound qualitative XT60 fit observation](../projects/usb-hub-3s-v3/03_src/mechanical/reference/usb-hub-wall-lid-unbound-qualitative-xt60-fit-observation-2026-08-27.md) and [FIT-008](enclosure-fit-registry.md#fit-008--usb-hub-xt60-mated-cable-interference-observation) |
| Correct use | Model the complete received connector assembly and cable service volume; test any roof-only or enlarged-opening candidate physically before transferring a number |

The transferable lesson is that depth, rear termination, cable direction, and
bend volume remain load-bearing after a plug body clears a panel opening. A
two-dimensional per-side opening allowance is not a complete connector or
cable tolerance.

## Adding a record

Append; never rewrite an earlier observation to match a later design. Record:

| Field | Required content |
|---|---|
| ID/date | Monotonic `CONN-NNN` and ISO date |
| Receptacle | Exact MPN, mounting method, drawing/model authority |
| Mate/grip | Exact supported MPN and complete coupling/latch/overmold geometry |
| Fastening | Method, final torque authority, selected tool and reaction load path |
| Cable | Exact termination, OD, straight run, exit and bend authority |
| PCB/enclosure | Exact subjects, mating-plane exposure, opening/wall state and process |
| Neighbor state | Every populated member and which connector must remain serviceable |
| Operations | Ordered mate/fasten/service/remove actions actually exercised |
| Tolerances | Each source, `exposure_setback` / radial / axial / other effect, and one-sided stack; no single generic connector number |
| Physical method | Coupon/article, process, measurement tools, cycles and acceptance |
| Result | Pass/fail plus damage, rotation, cross-threading, rattle, chafe or load observations |
| Limits | What remains unknown and which future design may not inherit the result |

When printer/process fit is also relevant, cross-reference
[the enclosure fit registry](enclosure-fit-registry.md) rather than duplicating
its print coupon facts here.
