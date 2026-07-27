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
                            # For a CONVERTER the class is machine-graded by
                            # E-TOPO against the topology DERIVED from
                            # 03_src/rules/power_tree.yaml voltage envelopes.
                            # Recognised (substring, in this order):
                            #   buck+boost -> BUCK_BOOST
                            #   buck       -> BUCK
                            #   boost      -> BOOST
                            #   ldo|linear|low-dropout -> LINEAR
                            # An over- or under-capable class FAILS
                            # (buck_boost where a buck suffices = FAIL).
                            # A part that is NOT a converter (a load switch,
                            # an eFuse, a pass FET, a ferrite) classifies as
                            # NOTHING and may not appear on a `rails:` entry —
                            # such a stage converts nothing and E-TOPO has
                            # nothing to derive.

# LINEAR CONVERTERS ONLY — both REQUIRED before E-TOPO will grade a rail whose
# converter is one. A linear regulator's failure modes are DROPOUT and
# DISSIPATION, and the Vin-vs-Vout topology derivation is blind to BOTH, so a
# LINEAR rail without them is a rail the gate cannot grade — a FAIL, never a
# pass (canon M-COVER). Until 2026-07-27 `normalize_type()` rejected every
# linear part outright, so the only route to a green E-TOPO on an LDO-only
# board was to DELETE power_tree.yaml; three fleet boards took it.
# dropout_mv: 120           # datasheet MAX dropout at the part's RATED output
                            # current (the conservative reading). A rail may
                            # override with the number at ITS own iout_max_A.
                            # Graded: vin_min - vout_max >= dropout_mv.
# pdiss_max_mw: 300         # package power rating. A rail may override with a
                            # board-specific derating (hot ambient, no copper
                            # under the part). Graded:
                            #   (vin_max - vout_min) * iout_max_A <= this.
                            # STATE THE AMBIENT if the datasheet does; a
                            # rating with no stated datum is ESTIMATED, not
                            # CITED (canon M-IMPORT).
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
asserts:                    # OPTIONAL, canon P-FACT. The part's own facts,
                            # made EXECUTABLE. Everything above this line that
                            # a machine does not read lands in `gotchas:` as
                            # free prose — and FOUR such facts were written
                            # down correctly and became defects anyway:
                            #   "PAD 1 IS NEGATIVE - polarity is a PART FACT"
                            #      -> the XT60 shipped REVERSED
                            #   "keep off the JLC-assembly BOM"
                            #      -> the code reached the BOM
                            #   "no copper under the opto"
                            #      -> the LTV-817S 5kV barrier shipped with
                            #         0.175mm of copper under it
                            #   "MSL 3, 168h floor life"
                            #      -> the consigned XU316 shipped with ZERO
                            #         MSL text in the order paperwork
                            # A fact written down and never read is
                            # indistinguishable from a fact nobody knew.
                            # EVERY entry REQUIRES `why:` (canon M4 — a part
                            # fact without its reason IS the prose gotcha this
                            # block replaces). Graded by
                            # `jlcpcb-fab/scripts/part_facts_check.py`.
  - assert: pad1_net_polarity      # pad 1's NET must carry this polarity.
    pad: 1                         # Read from the exported NETLIST — a
    polarity: negative             # DIFFERENT artifact from the BOARD that
    why: "AMASS drawing fig 2: pad 1 is the '-' blade. A reversed XT60 already
      shipped once and the netlist is self-consistent either way, so no ERC,
      DRC or parity check can see it"
  - assert: value                  # the fab BOM's Comment for every ref of
    equals: 1k                     # this part must DECODE to this value.
    tolerance_pct: 5               # SI-aware: 1k / 1kOhm / 1kΩ / 4k7 / 0R1
    why: "I_IL(max) 190uA x R < V_IL 0.99V => R <= 5.2k; TI SLVS165O 7.3.4
      names 1k explicitly"         # NB m is MILLI and M is MEGA
  - assert: not_on_assembly_bom    # no ref of this part may carry an LCSC on
    why: "THT on an SMT-only order and stock 0 on all three siblings (live
      query 2026-07-25) — hand-wire from Digi-Key"   # the BOM, or sit on CPL
  - assert: msl                    # the release's ORDER paperwork must STATE
    level: 3                       # the level + floor life. An assembler
    floor_life_h: 168              # cannot INFER a moisture obligation, and a
    why: "consigned; J-STD-033D bake if the bag has been open >168h below
      30C/60% RH"                  # popcorned 0.4mm TQFP is unrecoverable
  # - assert: keepout_region       # DECLARED BUT NOT YET GRADED: needs board
  #   layers: [F.Cu, In1.Cu, In2.Cu, B.Cu]      # geometry. The checker names
  #   region: under_body                        # it DEFERRED and FAILs it
  #   why: "5kV isolation barrier ..."          # under --strict rather than
                                                # going quiet — a deferred
                                                # kind that silently returns
                                                # clean is worse than none.
```

`part.yaml` must be complete enough that **the PDF is never opened again for
normal work** — only for re-verification. That is what makes it
context-cheap: 40 lines of YAML instead of 60 pages.

**Record polarity as a part fact wherever the part has one.** `pins: {1: {name: "-", note: "negative blade"}}`
on an XT60 is exactly the fact whose absence shipped a reversed battery
connector — a bug no electrical check can see, because the netlist is
self-consistent either way. **And record it in `asserts:` as well, not only in
prose:** that same XT60's part.yaml already said "PAD 1 IS NEGATIVE - polarity
is a PART FACT" in `gotchas:` and the connector shipped reversed anyway,
because nothing machine-readable ever consulted it (canon P-FACT).

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

**S-VER IS THE NARROW INSTANCE OF `M-IMPORT` (canon Meta, landed 2026-07-27,
ADR-0005 phase 1).** The class is *every fact imported from outside this repo*;
a pin map is one member, and this folder is where that member is governed. The
grades M-IMPORT defines apply to everything else a `part.yaml` imports too:
**MEASURED** (the physical object, or a machine-readable source — a
`.kicad_pcb`, a drill file, a STEP), **CITED** (a vendor document, WITH figure /
page / section — what a `verified:` note is), **ESTIMATED** (derived,
photogrammetric, inferred — and it MUST carry an error bar). A dimension used in
COPPER is MEASURED or CITED, never ESTIMATED without its bar; a published number
whose DATUM is unstated is ESTIMATED, not CITED; and where the grades disagree
**the object beats its drawing**. The wider rule gained its machine half on
2026-07-27 (ADR-0005 phases 2-4): `03_src/rules/mates.yaml` + `spf/<device>/`,
graded by `import_provenance_check.py` for M-EXIST/M-GRADE/M-BAR/M-PROXY/
M-OWED/M-RESTATE/D-MATE. **It reaches MATING geometry, not this folder**: a
`part.yaml` imports its facts from a datasheet and is still graded by S-VER
plus review, so outside pin maps and outside a `mates.yaml` this remains [H],
and this contract says so rather than implying a check that does not exist.

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

And it answers **P-FACT** — the part's own facts are graded against the board
and the release, not merely written down:

- Audit: `jlcpcb-fab/scripts/part_facts_check.py PROJECT_OR_RELEASE [--strict]`
  (offline; no pcbnew, no network). It grades `pad1_net_polarity` against the
  exported NETLIST, `value` against the fab BOM, `not_on_assembly_bom` against
  BOM+CPL, and `msl` against the release's ORDER paperwork.
- `keepout_region` is DECLARED but NOT YET GRADED (it needs board geometry).
  The checker names it DEFERRED and FAILs it under `--strict`; it never
  reports clean. That is the LTV-817S isolation-barrier class and it is the
  open half of P-FACT.
- An assertion that reaches NO board ref is reported UNREACHED, never passed.
  A gate that grades zero things and prints OK is the `jlc_twin` exit-0 class.
- Adoption is opt-in per part and the coverage line prints
  `N/M part.yaml declare an asserts: block`, so "we check part facts" can
  never be true-sounding and empty.
