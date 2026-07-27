# ADR-0004 — A gate must grade the shipped bytes and declare its coverage

status: accepted (phases 0-4 implemented 2026-07-27)
date: 2026-07-27
tags: canon, gates, pipeline, fab, meta

## Context

A five-release fleet audit (2026-07-26/27) graded every sealed release against its
own contract. Two are not orderable. **Every gate on both was green.**

- **usb-hub-3s-v3 v1.6 / v1.7 / v1.8** ship gerbers with **zero copper pour on any
  layer** — 51 zones on the board, 0 `filled_polygon` blocks, G36 region count 0
  on F_Cu / In1_Cu / In2_Cu / B_Cu. Missing copper **44 287.91 mm²**. `In1_Cu.g1`
  and `In2_Cu.g2` are byte-identical apart from `%TF.FileFunction,Copper,L2` vs
  `L3` — impossible for a GND plane and a VIN plane, and diagnostic: both files
  contain only the layer-independent PTH flash list. The regression landed at
  v1.6, the release that declared v1.5 and earlier DO-NOT-ORDER, so **every
  currently-orderable release of that board has it.**
- **interposer v1.0** ships `J_KEY_MATRIX` at CPL rotation 90.0 where the measured
  authority says 270.0 — **180° reversed**, mapping `KP_U1`↔`KP_D4` and reversing
  the entire ten-line keypad ribbon. The pad array is symmetric about its own
  centre, so at 180° every pad still lands on a pad and the part solders
  perfectly. It also places two blank-LCSC through-hole connectors that no SMT
  process can solder.

Neither is a design error. Both are **artifact** errors that every gate was
structurally unable to see.

### Root cause 1 — gates grade a reconstruction, never the bytes that ship

| gate | input it actually read | artifact that ships |
|---|---|---|
| `kicad-cli pcb drc --refill-zones` | zones refilled **in memory** | a gerber with 0 pour |
| `policy_audit` (interposer) | a `06_build` **shadow tree** | the archive — 79 vs 102 warnings |
| `bom_source_check` | `06_build/…/bom_jlc.csv` | `fab/bom.csv`, a different filename |
| A-EVID | **filename presence** | Eeschema-PDF where tscircuit was promised; a 1-page `assembly.pdf` |
| `twin_overlay` | courtyards **from the board** | a render nothing measures |

The fab payload — the zip that is uploaded and turned into copper — is the one
artifact nothing in this repo has ever read. That single sentence is the whole
usb-hub P0.

### Root cause 2 — a gate may print PASS while grading nothing

| gate | measured coverage |
|---|---|
| A-AMP `parse_amps` | **0/8**, **0/3**, **1/11** net classes across three boards — any qualifier returns `None`, then prints `ok … n/a (no current: declared)` |
| `bom_source_check.row_kind` | drops `RS1/RS2` (the 10 mΩ shunts setting **both** buck current limits), `CE1` (the only electrolytic — **shipped reversed** in v1.0/v1.1), 12 of 25 crow-recorder rows |
| `labeled_resistance("10mΩ")` | **1.0e7 Ω** — the multiplier is uppercased, so milli decodes as mega |
| v1.4 retraction sweep | **0 USES** beside a live instance, because it greps one literal spelling |
| `read_twin_findings` | the 8 RJ45s — the only parts with **no JLC CAD** — drawn as clean |

### Why the existing canon did not prevent this

`CLAUDE.md` already carries, learned by paying for it:

> `generate_rules` runs **LAST** again after stitch/fill — pcbnew saves clobber
> netclasses.

The rule names **netclasses**. The law is *a pcbnew save drops state that is not
in the source.* **Zone fills are the same class and had no rule.** The post-mortem
produced a sentence about the thing that broke; the category stayed unnamed and
re-entered through its next member.

## Options

- **Patch each defect.** Fix `parse_amps`, `row_kind`, `labeled_resistance`, the
  retraction sweep, `read_twin_findings`. REJECTED — five patches, and the sixth
  member of the class is unwritten. It also leaves root cause 1 untouched.
- **Add a gerber-reading gate only.** Closes the P0, nothing else. REJECTED as
  incomplete for the same reason.
- **Two structural rules that make both classes unwritable, plus a gate over the
  gates.** CHOSEN. Each rule is checkable *about* gates, not merely by them.

## Decision

### Two meta-principles, added to `design-policies.md` beside M1

NAMING NOTE: an earlier draft of this ADR called these M6 and M7. **Both IDs are
already taken** — M6 is "the authoritative source wins over the derived metric"
and M7 is the contracts.md governance rule. Landing them under those numbers
would have silently redefined two live canon entries, which is the documentation
form of the very defect this ADR is about. They take mnemonic IDs, matching the
convention the newer canon rows already use (M-PROV, M-DISC, M-CONS).

> **M-SHIP — Grade the shipped bytes.** A gate's input path MUST resolve inside
> the sealed release directory. Reconstruction (refill-in-memory, a `06_build`
> shadow, a regenerated export) is permitted only as a SECOND opinion, never as
> the primary. Where the two disagree, the shipped bytes are authoritative.
>
> **M-WIDTH — A rule is written at the width of its class, not its incident.**
> When a post-mortem names a specific thing, the rule MUST name the category and
> enumerate its known members. `netclasses` → *everything a pcbnew save drops*.

### A new `F-` family — the fab payload is a graded artifact, not a hashed one

| ID | property | free RED fixture |
|---|---|---|
| **F-POUR** | G36 regions per copper layer vs the board's filled-zone census | **usb-hub v1.8 zip** |
| **F-IDENT** | no two layer files byte-identical across different `TF.FileFunction` | same |
| **F-DRILL** | drill census vs pad census | interposer *(passes — verified to the micron)* |
| **F-SMT** | no CPL row has plated drilled pads with no paste | **interposer `fab/cpl.csv`** |

No fixture is synthetic. Every one is a sealed, immutable release this project
already paid for.

### A new `G-` family — a gate on gates, run by `tests/run_tests.sh`

Every script under `skills/*/scripts/` that prints a verdict MUST:

| ID | requirement |
|---|---|
| **G-INPUT** | name its input path, and that path resolves under the release dir (M6) |
| **G-COVER** | emit `N graded / M total`; **unparseable input is FAIL, never skip**; a zero denominator is FAIL |
| **G-RED** | have a fixture in `tests/` that makes it fail |

G-COVER alone retires `parse_amps`, `row_kind`, the milli/mega decode, the
literal-string sweep and `read_twin_findings` — not by patching five functions,
but by making the shape illegal. This is `contracts_audit.py` for gates, and it
is the piece that compounds: the next gate written cannot be born silent.

### Stage read-backs — M1 applied to STAGES, not only to gates

Canon M1 says checker and checked must not share a method. The pipeline violates
it at every stage boundary: each stage trusts that what it wrote is what it meant.

| stage | read-back assertion |
|---|---|
| fill | reopen the SAVED file; `filled_polygon` count > 0 per zone |
| route | reopen; track census matches the chain file |
| netclass | reopen; rules survived the save |
| **export** | **open the written zip, parse it, assert against the board** |
| seal | extract `source/` to a temp dir; DRC from there alone |

The export stage today writes a zip and never reads it. That gap is the
44 287.91 mm².

### Shift-left: where a gate is fragile, look upstream for prose that should be a field

`parse_amps` is not badly written. It is handed `"~1.6A worst case (…)"` and asked
for a number. The defect is in the source schema.

```yaml
# nets.yaml — today
current: "2.5A per port"           # -> None -> prints "ok"
# after
current_a: 2.5                     # a number; nothing to misparse
current_note: "per port, 3 ports"  # prose, graded by nobody
```

Same for BOM values: a typed `resistance_ohms: 0.010` never meets the milli/mega
hazard because `10mΩ` becomes display, not data. **The parser is deleted rather
than fixed.**

Two further upstream moves, same shape:

- **Part dossiers get executable facts.** `10FDZ-BT/part.yaml` already says "keep
  off the JLC-assembly BOM" — as prose, with no `asserts:` block, so nothing
  reads it. On cooksense, **4 of 41 dossiers have asserts; 37 carry facts no gate
  reads.** A dossier declaring `assembly: hand_solder` makes THT-on-CPL
  structurally impossible nine stages before export.
- **Producers stamp provenance.** A-EVID guesses from filenames, which is how
  Eeschema-PDF passed as tscircuit's render and a 1-page `assembly.pdf` passed as
  a two-sided drawing. Writing `produced_by:` / `pages:` at export time turns
  inference into verification.

### Fleet regrade — the only control for defects that BECOME wrong

The interposer's reversed CPL came from name-DB rule `^JST_GH_SM,180`. The
release sealed **2026-07-24**. That rule was refuted **2026-07-25**. The release
was *correct by the knowledge of its day.*

No schema, read-back or stricter gate catches that. Only regrading sealed work
against later knowledge does.

- **When a gate lands, regrade the fleet** — one command, every sealed release,
  today's gate set, report what would now fail.
- **Seal-time `graded_by:`** listing every gate that existed at seal, so a gate
  with no verdict is a visible hole rather than an absence. **M-GRADE** fails on
  a hole. The interposer's `policy_audit.md` has no A-POP / A-POS / A-ROT /
  A-POL / A-BODY / A-STOCK row **at all** — sealed the same days that family was
  landing, never re-graded. Every one of its P0s lives in a gate it was never
  subjected to.

### The seal question changes

From *"did every gate pass?"* to *"what did each gate not look at?"* —
`policy_audit` grows a coverage column. A release whose gates all pass at 40 %
coverage should read as what it is.

## Consequences

### Sequencing is forced, not preferred

**Phase 0 — measure, before building anything.** Count today: net classes with
unparseable current; dossiers lacking `asserts:`; gates G-COVER would flag; gates
reading outside the release dir. If those numbers are small, this design is aimed
at the wrong thing. Read-only, cheap, and it turns a plausible plan into a sized
one.

**Phase 1 — mark the DO-NOT-ORDER releases.** `SUPERSEDED.md` on usb-hub
v1.6/v1.7/v1.8 and interposer v1.0, each naming the measured defect. No code; the
only cost of delay is someone spending money.

**Phase 2 — F-POUR and G-COVER.** These MUST land before any re-seal. A v1.9
graded by the same blind gate set proves nothing about whether the pour returned.

**Phase 3 — stage read-backs**, starting with the fill wrapper (catches the P0 at
the moment of damage and the crow-recorder stranded islands with it).

**Phase 4 — re-seal usb-hub v1.9 and interposer v1.1**, now provable.

**Phase 5 — typed schemas**, measured before/after (A-AMP 1/22 → 22/22).

**Phase 6 — contracts catch up in the same change**, per the standing rule:
`skills/pcb-design/templates/contracts/` is the source of truth, and
`t1_contracts.py::t_skill_contract_sync` is the machine backstop.

### What this would have caught

| change | catches |
|---|---|
| export read-back / F-POUR | **usb-hub P0** — 3 releases, 44 287.91 mm² |
| fleet regrade + `graded_by:` | **interposer P0** — CPL 180°, and THT-on-CPL |
| M6 | interposer 102-vs-79, `bom_source_check` path, A-EVID presence |
| G-COVER | A-AMP across 3 boards, `row_kind`, milli/mega, retraction sweep |
| seal extract-and-DRC | interposer `fp-lib-table` pointing outside the archive |
| M7 | *the next one* |

### What it does not catch, stated plainly

Defects that were correct when sealed. Only the regrade finds those, and the
regrade is only as good as the day's knowledge — it converts an unknown-unknown
into a dated one, it does not eliminate it.

### Risk

**G-COVER is itself a gate and could be written so it cannot fail.** The honest
acceptance test is that it reports a LARGE violation count against the current
`skills/` tree on its first run. If it comes back clean on a codebase measured to
be riddled, it is decoration and must be rejected. That number is Phase 0's
primary output.
