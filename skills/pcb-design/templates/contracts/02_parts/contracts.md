# contract: 02_parts/

**Purpose** — one directory per MPN actually used on the board, holding the
datasheet and the facts extracted from it. Makes the project standalone: a
clone with no network still knows every pad number, limit and polarity.

**Mutability** — append on part addition; edit a `part.yaml` only when the
datasheet REVISION changes.

## The three tiers (confusing them is the default mistake)

| Tier | Cost | Lifetime | Home |
|---|---|---|---|
| PDF blob | seconds | until vendor revises | global `~/.cache/datasheets/<sha256>.pdf` (never git) + a project copy HERE once used |
| Extracted facts | expensive, error-prone | until revision changes | `part.yaml`, committed |
| Stock / price | seconds | hours | `06_build/cache/`, TTL'd, **never** here |

**The download is not the expensive part — the extraction is.** Reading a
60-page datasheet to get physical pad numbers right is the costly work. Do it
once. A committed stock number is a lie within a day; a committed pad number
is true for the life of the revision.

## Flow

```
need a datasheet
  → global cache hit? yes: free. no: download, hash, store in cache
  → extract facts ONCE into 02_parts/<MPN>/part.yaml
  → is the part actually USED (in the schematic/BOM)?
      yes → copy the PDF from cache into 02_parts/<MPN>/ and commit
      no  → cache-only. Record WHY it lost in 01_docs/decisions/NNNN-*.md
```

Rejected candidates never get a committed PDF — the binary is worthless, the
reason is not. The global cache still means you never re-download while
iterating over alternatives.

## Allowed

| Pattern | What |
|---|---|
| `<MPN>/part.yaml` | the facts + provenance. Required for every used part |
| `<MPN>/<DOCID><REV>.pdf` | the datasheet. Filename carries the REVISION |
| `<MPN>/notes.md` | optional: errata, application gotchas too long for `gotchas:` |
| `README.md` | folder status + **deviations register**: every departure from this contract (unfetchable PDF, series-sheet passives without PDFs), each with why + what must happen before bring-up | required if any deviation exists |
| `contracts.md` | this file |

`<MPN>` is the exact orderable manufacturer part number — the string you
would type at a distributor. Not a family ("ATtiny816"), not an invented
suffix. **"ATtiny816-SSN" was carried for weeks and is not an orderable part;
the 20-pin SOIC is ATTINY816-SN.** A `part.yaml` validated once kills this.

## Structure: `part.yaml`

```yaml
mpn: LM5145RGYR
manufacturer: Texas Instruments
type: buck_controller       # REQUIRED. The part CLASS, not its value.
                            # "10k NTC 3380K" on an R_0402 footprint is a
                            # THERMISTOR; it was coded as a plain 10k resistor
                            # and would have shipped as the temp sensor.
                            # For a CONVERTER the class (buck|boost|buck_boost)
                            # is machine-graded by E-TOPO against the topology
                            # DERIVED from 03_src/rules/power_tree.yaml voltage
                            # envelopes — an over- or under-capable class FAILS
                            # (buck_boost where a buck suffices = FAIL).
datasheet:
  doc_id: SNVSAI4
  revision: SNVSAI4F        # PIN IT — pinouts change between revisions
  url: https://www.ti.com/lit/ds/symlink/lm5145.pdf
  sha256: 9f2c...           # proves a re-download is the same document
  fetched: 2026-07-14
package: VQFN-20 RGY 3.5x4.5
footprint: power_board_v1:VQFN-20_3.5x4.5_P0.5_LM5145RGY
# mates: receptacle        # CONNECTORS ONLY (plug|receptacle): the part's
                            # GENDER, read off the drawing TITLE BLOCK
                            # ("AM"/"AF"). A male plug served weeks as a
                            # receptacle because footprint+netlist+silk were
                            # consistently wrong TOGETHER (usb-hub-3s
                            # ADR-0006, 2026-07-21). Role-vs-gender remains
                            # a HUMAN pin-review call — no machine gate covers
                            # connector gender/role at this stage (do not cite
                            # one; M-REL is the release-immutability checker)
escape:                     # REQUIRED for every multi-pin part (D-ESC).
                            # Emitted by skills/kicad-pcb/scripts/
                            # escape_check.py --style qfn --pitch 0.5;
                            # policy_audit P-ESC recomputes it and P-TIER
                            # compares tier_required against the board's
                            # declared fab_tier (nets.yaml). Never copy
                            # this block between parts — the checker
                            # cross-checks it against the footprint text.
  style: qfn                # qfn|dfn|leaded|bga|connector|module|passive
  pitch: 0.5                # mm, from the datasheet land pattern
  escapes_worst_side: 5     # OPTIONAL: escape count on the worst single
                            # side (nets leaving the package, not GND/EP).
                            # Declaring it enables escape_check v2's
                            # CONDITIONAL verdicts (escape-budget model)
  tier_required: jlc_4layer_advanced
  # conditions: [outward-only-local]
                            # REQUIRED iff tier_required is a CONDITIONAL
                            # tier for this geometry — must match the
                            # checker's computed conditions exactly, or
                            # P-ESC fails. Vocabulary (escape_check.py):
                            #   outward-only-local — every fine-pad net
                            #     terminates in an adjacent local passive
                            #     (D-ADJ); no crossings, no layer drops
                            #   escape-corridor — a reserved routing lane
                            #     at placement (floorplan escape_corridors:)
  checked: escape_check 2026-07-21
pins:                       # PHYSICAL PADS, read from the pinout figure
  1: EN
  20: VIN
  21: {name: EP, tie: GND, note: "thermal pad, must be grounded"}
                            # `tie: <net>` is LOAD-BEARING (converter-consumed):
                            # for a PHYSICAL pad ABSENT from circuit.json (an EP /
                            # mechanical tab the authoring tool drops), the
                            # converter (circuit_json_to_kicad_sch.py load_part_ties)
                            # emits an extra symbol pin on <net> so the pad is tied
                            # in the netlist in BOTH grid + layout modes — not
                            # floated. Scoped to the pins: block so a stray `tie:`
                            # elsewhere cannot fire; parts without it are byte-
                            # identical. Board stage still owns the copper (thermal
                            # vias into the EP); `tie:` only fixes the netlist blind
                            # spot. (crow-recorder... TPS259573 EP floated pre-2026-07-23.)
limits: {vin_max: 75V, tj_max: 125C}
gotchas:
  - "EP is pad 21, not implicit — without the pins: entry + tie: it floats (the converter ties it only when tie: is declared)"
verified: "pin map cross-checked against datasheet fig 6-1 — 2026-07-14"
layout:                     # REQUIRED for ICs + power/sense parts (P-LAYOUT).
                            # The THIRD datasheet read, after verified: (pinout)
                            # and escape: (package): read the LAYOUT/APPLICATION
                            # section + reference design/EVM/app note and encode
                            # the placement rules the chip demands. Absent it, a
                            # floorplan is authored from first principles and
                            # fights the part (usb-hub-3s-v2 TPS25740A: FET row
                            # placed 7mm off the power-stage edge -> unroutable).
  source: "TI SLVSDG8B Sec.11 + EVM SLVUAP7A: pass FET + sense R + VBUS caps
    HARD against the power-stage pin edge; Kelvin-sense back to the chip"
  reviewed: "2026-07-14"
  keep_short:               # nets whose pad-span P-ADJ measures on the board
    - {net: RSNS,  max_span_mm: 5, why: "Kelvin sense R adjacent to ISNS/VPWR"}
    - {net: PDSRC, max_span_mm: 5, why: "pass-FET source common node at chip"}
  # adjacency: [...]        # optional refdes-pair form; notes: free-text rules
layout_refs:                # REQUIRED for every HARD part (dense escapes,
                            # switching power, >0.5A analog, RF): the LAYOUT
                            # PRECEDENT SEARCH record — the routed references
                            # consulted before drawing the local layout, in
                            # datasheet-first authority order. STUDY then
                            # RE-DERIVE; never import copper (M3). Harvested into
                            # proven-parts.yaml with the part, so the search is
                            # paid once per part, ever.
  - "datasheet SNVSAI4F Sec.11 layout figure"    # (1) mfr's own routed picture
  - "TI EVM SLVUAP7A design files"               # (2) tested instance of circuit
  - "OSHWLab by-LCSC C485912"                     # (3) JLC-fabbed board, Cu viewable
  # - "GitHub kicad project <url>"               # (4) unvetted — weakest
sourcing: {lcsc: C485912, alternates: [C2650259, C3188678]}
```

`part.yaml` must be complete enough that **the PDF is never opened again for
normal work** — only for re-verification. That is what makes it
context-cheap: 40 lines of YAML instead of 60 pages.

**Record polarity as a part fact wherever the part has one.** `pins: {1: {name: "-", note: "negative blade"}}`
on an XT60 is exactly the fact whose absence shipped a reversed battery
connector — a bug no electrical check can see, because the netlist is
self-consistent either way.

## Forbidden

- A `part.yaml` for a part not on the board (stale after a swap).
- A committed PDF for a rejected candidate.
- Stock/price/availability fields — volatile.
- A family name or invented MPN as the directory name.

## Validate — the parity gate

Same spirit as `kicad-cli pcb drc --schematic-parity`, which caught a missing
part nothing else could:

- every part in the BOM has a `02_parts/<MPN>/` with a `part.yaml`
- every `02_parts/<MPN>/` is in the BOM (catches stale entries after a swap:
  ATtiny816 → ATtiny1616)
- `part.yaml.mpn` == directory name
- every used part's PDF is present (project is standalone)
- `sha256` matches the committed PDF
- `datasheet.revision` appears in the PDF filename
- every `pins:` entry the generator relies on is present
- `type:` present and not merely the value string

## Repair

- BOM part with no `02_parts/` entry → fetch, extract, commit. Do not order
  until it exists.
- `02_parts/` entry not in the BOM → the part was swapped; delete the directory
  (git history keeps it) and note the swap in `01_docs/CHANGELOG.md`.
- sha256 mismatch → the PDF was replaced with a different revision. STOP: the
  extracted facts may be wrong. Re-verify `pins:` before trusting anything.

## Compliance audit (design-policies.md IDs)

This folder answers: **S3** — every part.yaml pin map read from the
datasheet FIGURE with a `verified:` note citing figure+page (2-pad
passives exempt), and the PDF set includes the PACKAGE/land-pattern
drawing, not just electricals.

- Audit: `policy_audit.py` S-VER flags weak/missing citations
  mechanically; the fresh-context pin review re-derives pinouts for
  actives (the independent half of S3).
- A part that fails S-VER may not enter the BOM until its note cites the
  figure. "Same as <other part>" and "standard pinout" are not citations.

This folder also answers **P-LAYOUT / P-ADJ** — the datasheet LAYOUT section is
read (not just the pin table) and encoded as a `layout:` block for every IC and
power/sense part (with the routed precedents behind that read catalogued in
`layout_refs:` — datasheet figure, EVM/app-note, OSHWLab-by-LCSC, KiCad
projects — harvested into `proven-parts.yaml` so the search is paid once), and
the board's placement HONOURS it:

- Audit: `policy_audit.py` **P-LAYOUT** fails an in-scope part (multi-pin active,
  or `type:` matching fet/mosfet/current_sense/shunt/crystal/oscillator/inductor)
  that has no `layout:` block with a `source:` citation + a keep_short/adjacency
  budget. **P-ADJ** measures each `layout.keep_short` net's pad-span on the board
  and flags any that exceeds its `max_span_mm` (the datasheet's "keep it local"
  rule made mechanical) — warn+waiver: a real over-span must be re-placed or
  dispositioned in `policy_waivers.yaml` with the measured span + why.
- The Layout read is the independent human half: escape/pinout can be right while
  the part is still placed wrong (usb-hub-3s-v2 TPS25740A). P-ADJ is the machine
  half — it caught RSNS span 11.5mm > 5mm on that exact board.
