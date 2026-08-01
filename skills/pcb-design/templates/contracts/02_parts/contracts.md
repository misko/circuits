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
mechanical:                 # THE 3D ENVELOPE — the part's shape ABOVE and BELOW
                            # its land pattern. REQUIRED for a part the carrier
                            # must physically ACCOMMODATE rather than merely
                            # land: a purchased MODULE (`escape.style: module`),
                            # any assembly that is not flat-backed, a connector
                            # that overhangs the outline it is mounted on. OMIT
                            # it entirely for a part whose only geometry is its
                            # land pattern — an empty block declares nothing and
                            # `land_pattern:` is where 2D copper geometry lives.
                            # EVERY NUMBER HERE IS AN IMPORTED FACT (canon
                            # M-IMPORT) AND MUST SAY HOW IT WAS OBTAINED: a STEP
                            # / 3D model is MEASURED (machine-readable), a
                            # dimension drawing is CITED with its figure, a
                            # number off a render is ESTIMATED and needs its
                            # error bar. WHERE A DRAWING AND THE MODEL DISAGREE
                            # THE MACHINE-READABLE SOURCE WINS, and the loser is
                            # recorded so nobody re-derives the conflict.
  pcb_thickness_mm: 1.091                # the module's own laminate
  top_side_max_height_mm: 3.250          # tallest feature AWAY from the carrier
  bottom_side_max_protrusion_mm: 1.000   # tallest feature on the CARRIER-FACING
                            # face. THE SEATABILITY NUMBER: non-zero means the
                            # part CANNOT SIT FLAT, which is a POPULATION
                            # decision — a standoff, a hand-solder, an
                            # `03_src/rules/assembly.yaml` entry — and not a
                            # footprint note. Say which feature it is.
  total_thickness_mm: 5.341 # DERIVED: bottom + laminate + top. Stated so the
                            # enclosure stack is one number AND so the sum is
                            # falsifiable (1.000 + 1.091 + 3.250).
  <feature>:                # ONE ENTRY PER NAMED 3D FEATURE the model contains
    side: bottom            # top|bottom — which face it stands on
    protrusion_mm: 1.000    # how proud it stands on that face (a top-side
                            # feature reads the same way as `height_mm`)
    extent_mm: [[6.975, 10.925], [3.320, 6.420]]   # its footprint, part frame
    # `centre_mm` / `body_mm` / `part` and per-kind CONNECTOR terms
    # (`mating_face_y_mm`, `z_mm`, `shell_x_mm`) are open — the feature bag is
    # declared BLANKET in the `### keys:` table below and the four scalars
    # above are enumerated OUT of it, because they are not open.
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
  keep_short:               # P-ADJ measures THE ANCHOR PIN to its NEAREST
                            # QUALIFYING PARTNER — not the net's worst pad pair
                            # (changed 2026-07-29). The anchor is a pad of THIS
                            # part; the partner is the nearest pad on the same
                            # net belonging to another footprint; the graded
                            # number is the worst anchor pin's distance, and
                            # the report NAMES THE PAIR it graded. Rationale:
                            # a datasheet sentence is about a PIN ("100 nF
                            # close to EACH IOVDD pin"), and the whole-net
                            # maximum made a budget score WORSE when a
                            # correctly-placed bulk cap was added to the net.
                            # Measured: pluto-cal-switch RP2040:3V3 read
                            # 72.96mm against 4mm on the whole net (it is a
                            # poured rail crossing the board) and 2.60mm
                            # (U_MCU.26 -> C_IO3.1) on the anchor.
    - {net: RSNS,  max_span_mm: 5, why: "Kelvin sense R adjacent to ISNS/VPWR"}
    - {net: PDSRC, max_span_mm: 5, why: "pass-FET source common node at chip"}
    # - {net: DVDD, max_span_mm: 10, anchor_pins: [45], why: "..."}
                            # `max_span_mm` is a pad-CENTRE span, in mm.
                            # `anchor_pins:` (optional) names the pin numbers
                            # the datasheet sentence is about, when it is about
                            # one pair; omitted, every pad of this part on the
                            # net is an anchor and the worst one is graded.
                            # `net:` MUST be a NET NAME ON THIS BOARD carrying
                            # >= 2 pads, ONE OF WHICH IS THIS PART'S. A name
                            # copied out of the datasheet's reference design, a
                            # renamed net, a node split by a series element
                            # (RP2040's USB_DP becomes USB_DP_MCU after the
                            # 27R), or prose like "V+ decoupler (pin 8)"
                            # resolves to nothing, and P-ADJ-UNREACHED FAILS it
                            # by name: a budget nothing evaluates is not a
                            # pass. **E-NETREF grades the same field from the
                            # NETLIST ALONE** (`net_reference_audit.py`, kind
                            # K7) — so it reaches a project BEFORE there is a
                            # board, it isolates "no such net" from P-ADJ's two
                            # other causes, and it NAMES THE NEAR-MISS, which
                            # is the fix: `N3V3` -> `3V3` (the tsx
                            # author-prefix), `5V_SELV` -> the `5V_*` family.
                            # Measured 2026-07-29 across six boards: 64 of 181
                            # declared keep_short nets do not exist on their
                            # own board — cooksense's eFuse input-decoupling
                            # budget among them, and ALL 64 of the fleet's
                            # ghost net references across every kind land in
                            # THIS field.
                            # Measured 2026-07-28 before that gate
                            # existed: 61 of 119 budgets fleet-wide (51%) were
                            # graded by NOTHING; measured again 2026-07-29 with
                            # the anchor rule, 7 MORE (4 on pluto-cal-switch —
                            # KH-SMA-KE-Z SW1_ANT/SW2_ANT and RP2040
                            # USB_DP/USB_DM — and 3 on pluto-rx2-8way) were
                            # being graded off pads belonging to OTHER parts
                            # entirely.
  adjacency:                # REFDES-PAIR budgets, graded as P-ADJ-PAIR (a
                            # SEPARATE row from P-ADJ since 2026-07-29,
                            # because a P-ADJ waiver's evidence is a list of
                            # measured keep_short spans and must not absorb a
                            # different class — same reason as
                            # P-ADJ-UNREACHED). Read by NOTHING before that
                            # date: the field was in this contract and in the
                            # part.yaml files and no gate opened it, which
                            # reads as covered and is worse than absent.
    - {refdes: [U_ESD, J_USB], max_mm: 2.0, why: "ST DocID11265 sec 2.2: 6 nH
        per 10 mm turns a 17 V clamp into 305 V, so this is a clamp-voltage
        term and not tidiness"}
                            # `max_mm` is the COPPER GAP — pad EDGE to pad
                            # edge, i.e. the track length the nH/mm arithmetic
                            # applies to — measured on the worst net the two
                            # parts share. POURED nets are excluded and said
                            # to be: a plane joins two parts without a track,
                            # so a pad gap does not measure it (that is stitch
                            # / R-THERM work). A pair sharing no un-poured net,
                            # or naming a refdes absent from the board, is
                            # P-ADJ-UNREACHED.
  # notes: [...]            # free-text rules for the half no gate can grade
layout_refs:                # REQUIRED for every HARD part (dense escapes,
                            # switching power, >0.5A analog, RF): the LAYOUT
                            # PRECEDENT SEARCH record — the routed references
                            # consulted before drawing the local layout, in
                            # datasheet-first authority order. STUDY then
                            # RE-DERIVE; never import copper (M3). Harvested into
                            # proven-parts.yaml with the part, so the search is
                            # paid once per part, ever.
                            # TWO FORMS, AS `pins.<N>` AND `sourcing.alternates`
                            # ALSO HAVE. The BARE STRING below is legal and is
                            # what 45 of the fleet's 89 in-scope parts use; it
                            # is counted OWED by P-PREC, never failed. The
                            # MAPPING form is GRADED (canon P-PREC).
  - "datasheet SNVSAI4F Sec.11 layout figure"    # (1) mfr's own routed picture
  - "TI EVM SLVUAP7A design files"               # (2) tested instance of circuit
  - "OSHWLab by-LCSC C485912"                     # (3) JLC-fabbed board, Cu viewable
  # - "GitHub kicad project <url>"               # (4) unvetted — weakest
                            # THE GRADED (MAPPING) FORM. `tier:` is the SKILL.md
                            # authority order 1-4; `artifact:` names the thing
                            # (URL / document + figure + page / design-file
                            # name); `reached:` separates CONSULTED from merely
                            # KNOWN-OF; `why:` is REQUIRED (>=20 chars) on an
                            # unreached tier, because a debt states its reason.
                            # THE LADDER MUST NAME ITS CEILING: if the best
                            # `reached: true` tier is below 4, at least one
                            # `reached: false` entry must name what sits above
                            # it. Reaching only tier 1 with the gap NAMED is a
                            # PASS — what is graded is honesty about the
                            # ceiling, not possession of it, because no gate can
                            # know what exists on the web for an arbitrary part.
                            # TIER 2 IS ANY OPEN-HARDWARE REFERENCE DESIGN WITH
                            # PUBLISHED LAYOUT, not just a vendor EVM, and an
                            # EDITABLE design file OUTRANKS A RENDERED FIGURE —
                            # you can open it and MEASURE it. Licence matters
                            # here (it is what makes the file openable) but
                            # never licenses copying: study-then-re-derive is M3.
  # - {tier: 1, reached: true,
  #    artifact: "Hardware design with RP2040 Fig 6, PDF p9 (raster, 200 dpi)"}
  # - {tier: 2, reached: false,
  #    artifact: "Raspberry Pi 'Minimal Viable Board' KiCad reference design,
  #      raspberrypi.com/documentation/microcontrollers/rp2040.html",
  #    why: "19.9 MB fetch not attempted at the parts stage; Figure 6's raster
  #      used instead. Recorded as NOT DONE, not as absent."}
sourcing: {lcsc: C485912, alternates: [C2650259, C3188678]}
                            # ALTERNATES TAKE TWO FORMS AND THEY ARE NOT
                            # EQUIVALENT. A BARE code (the form shown above) is
                            # READ — its leading `C...` is keyed — but it
                            # declares NO mpn, and the PARENT's `mpn:` IS NOT
                            # ITS MPN: `C47023` is `MCP23017-E/SO` (SOIC-28W, a
                            # DIFFERENT FOOTPRINT), not the `-E/SS` the dossier
                            # it sits in is about. So an alternate whose code
                            # can ever appear on a BOM MUST use the mapping form
                            # `{lcsc: C..., mpn: ...}`, or F-MPN will FAIL that
                            # row by name. Measured fleet-wide 2026-07-29: 351
                            # bare vs 2 mapping — and `bom_legibility_check.py`
                            # read ONLY the mapping form, so the MPN authority
                            # understood 0.6% of its own documented dialect,
                            # silently, for the file's whole life. Inheriting
                            # the parent mpn: was REJECTED as the fix precisely
                            # because it would have written `-E/SS` for a
                            # `-E/SO` part: a confident wrong answer in place of
                            # a silent skip is not an improvement. A bare
                            # alternate now resolves as a KNOWN CODE WITH AN
                            # UNDECLARED MPN, which is diagnosable by name.
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
  - assert: value                  # ...and an `equals:` the SI decoder cannot
    equals: PE42482A-X             # read is a LITERAL, compared EXACTLY to the
    why: "the Comment must NAME the switch; a pin-compatible SPDT in the same
      land is a different part"    # Comment (whitespace-stripped, NOT
                                   # case-folded and NOT punctuation-
                                   # normalised: `SS12D07VG6 087` vs
                                   # `SS12D07VG6-087` is a drift this fleet has
                                   # already shipped). `tolerance_pct:` on a
                                   # literal is a CONFIG ERROR — a percentage
                                   # band around a part number grades nothing.
                                   # Until 2026-07-28 a non-numeric `equals:`
                                   # emitted a non-blocking P-FACT-CONFIG and
                                   # checked NOTHING while the run printed
                                   # `P-FACT OK`: 11 of 13 asserts on
                                   # pluto-rx2-8way and 5 on pluto-cal-switch.
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
- `02_parts/` entry not in the BOM → the part was swapped. **DO NOT reflexively
  delete the directory, and note that the parenthetical this bullet USED to
  carry — "git history keeps it" — is the exact wrong reassurance: git keeps the
  BYTES, but every gate reads the WORKING TREE.** `02_parts/` is the MPN
  authority for EVERY sealed release, not just the current board, so removing a
  dossier — or moving its `sourcing.lcsc`/`mpn:` — can break an immutable
  archive that may never be edited (canon **M-DEPEND**).
  It is NOT append-only: a board that legitimately drops a part must be able to
  drop its dossier. What is REQUIRED is that the code every sealed
  `fab/bom.csv` cites still resolves afterwards. Three legitimate outcomes:
  keep the dossier; keep the retired code resolvable as a **mapping-form**
  `alternates:` entry (`- {lcsc: C506653, mpn: MCP23017-E/SS}` — the BARE form
  declares no part number and resolves nothing, see the `sourcing:` note above);
  or move the code->MPN fact to
  `skills/jlcpcb-fab/references/lcsc_passives_ledger.yaml`, the live
  hand-verified home for a code no board vendors any more. Then note the swap in
  `01_docs/CHANGELOG.md`.
  Gated by `sealed_dependency_check.py PROJECT_DIR` and `policy_audit`'s
  M-DEPEND row — which exist because this bullet, as written, CAUSED the
  incident: cooksense's v1.7 work followed it, removed `02_parts/ULN2803ADWR/`,
  and the sealed byte-unchanged `cooksense-v1.6-2026-07-27` flipped F-MPN
  PASS->FAIL on row 56, then flipped BACK when the dossier was restored — twice
  in opposite directions in one session, with nothing recording that it had been
  red. Measured fleet-wide 2026-07-29: **539 rows across 25 of 33 sealed
  releases resolve ONLY because a dossier is still in the tree**, and the 8
  releases carrying their own map contribute zero of them.
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
  budget. **P-ADJ** measures each `layout.keep_short` budget from THE ANCHOR PIN
  (a pad of the declaring part on that net) to its NEAREST QUALIFYING PARTNER
  (the nearest pad on the same net on another footprint), worst anchor wins, and
  names the pair — the datasheet's "keep it local" rule made mechanical, at the
  granularity the sentence has. It is NOT the whole net's worst pad pair: that
  metric made a budget score WORSE when a correctly-placed bulk capacitor was
  added, so it could not guide placement (changed 2026-07-29; the usb-hub-3s-v2
  RSNS incident still FAILS, 7.34mm U1.19 -> Q6.5 against 5mm).
  **P-ADJ-PAIR** grades `layout.adjacency` refdes pairs on the copper GAP
  between them. **P-ADJ-UNREACHED** covers both kinds.
  **E-NETREF** (`net_reference_audit.py`, canon E-NETREF) is the netlist-only
  sibling of P-ADJ-UNREACHED for the `keep_short[].net` field: same defect
  class, different oracle and different reach — no board and no pcbnew, so it
  grades a project before routing; it distinguishes "this net does not exist"
  from P-ADJ's other unreached causes; and it names the NEAR-MISS. It is one of
  eleven reference kinds it grades, because a net name in ANY hand-authored
  source is a reference something will look up (canon M-WIDTH).
  Both are SEPARATE rows and NEITHER is waivable by a P-ADJ waiver:
  P-ADJ-UNREACHED fails any budget that does not resolve to a measurable pair
  here (no such net, fewer than 2 pads, no pad of the declaring part, no shared
  un-poured net, a refdes not on the board). The split is deliberate — a P-ADJ
  waiver's evidence is a set of MEASURED spans, and letting it also cover
  budgets that were never measured, or a different budget KIND, is exactly the
  waiver-widening canon M4 forbids. Any of the three reporting `PASS` over ZERO
  measured budgets is itself a FAIL (canon M-COVER).
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

## Every schema key here NAMES THE GATE THAT READS IT — canon G-ORPHAN

**`schema_reader_audit.py --root REPO`** (`--families` prints the denominator).
**THIS IS THE FILE THE RULE WAS WRITTEN FOR.** `layout.adjacency:` — a
refdes-pair proximity budget — sat in these dossiers looking live while P-ADJ
read `keep_short` entries ONLY, so pluto-rx2-8way's requirement that `U_ESD` sit
within ~2.0 mm of `J_USB`, where 6 nH per 10 mm of loop turns a 17 V clamp into
a 305 V spike, was graded by NO GATE AT ALL and a human had to hand-measure it.
`part.yaml` is the most expensive artifact this pipeline makes and the easiest
place to write a fact that nothing consumes: P-FACT's own row records that until
2026-07-25 only five of its blocks reached any gate.

So every key is classified, and the classification is PROVED out of the named
reader's AST on every run. A key in a real dossier with no row below is an
ORPHAN and FAILS. `ADVISORY` and `OWED` are DECLARED states and both REQUIRE a
reason (canon M4): ADVISORY means nobody reads it AND THAT IS CORRECT — a
datasheet fact spent by a human at part-selection time, whose executable channel
is the `asserts:` block beside it; OWED means a gate is INTENDED and absent.
A trailing `.*` declares a whole subtree, which is how the open per-part fact
bags (`limits:`, `land_pattern:`, `ratings:`) are covered without pretending
their contents are a closed schema — but a subtree declaration is a CLAIM about
the whole bag, and enumerating a key out of one is always the stronger move.

`pins.<N>.tie` IS THE MEASURED HOLE HERE AND IT IS OWED WITH ITS PATCH.
84 pins across 43 dossiers declare which net they must land on, and NOTHING
reads it — not `pin_audit.py`, not `electrical_invariants.py`, not
`net_reference_audit.py`. That is the exact field class the `GND_ISO` ghost that
reached shipped F.Silkscreen lived in: a net NAME in hand-authored source with
no consumer. It belongs to E-NETREF, not to a second net resolver; the K13 patch
is written out in `schema_reader_audit.py`'s docstring, including the
`tie: none` exclusion (`XU316-1024-TQ128-I24` floats four IO-voltage straps
deliberately, and failing those is how a new kind gets waived).

`mechanical:` IS THE SECOND MEASURED HOLE, IT ARRIVED 2026-07-30, AND THE
OBVIOUS READER FOR IT IS A TRAP. The block is a part's 3D ENVELOPE, and the one
dossier that declares it — pluto-rx2-8way-v2's RP2040-Zero — took every number
off the vendor Creo STEP, which is the MEASURED grade (canon M-IMPORT: a
machine-readable source). It is not decoration: `bottom_side_max_protrusion_mm:
1.000` is *why* that board's `assembly.yaml` refuses to have `U_MCU` machine
placed, because 23 components on the carrier-facing face put the joint plane and
the collision plane in the same plane and the module cannot sit down. So the
physics is stated TWICE, in two files, and no gate can make the two disagree.

Which gate is owed it is a real question with a wrong-looking answer, and the
wrong answer is the one this gate exists to refuse. **`assembly_coverage.py`
contains the exact string `"mechanical"` in a READ POSITION — a set literal at
line 84 — so naming it here would score PROVEN and grade NOTHING**, because that
occurrence is the closed `reason:` vocabulary of `03_src/rules/assembly.yaml`, a
different file and a different structure. That is limitation (a) in
`schema_reader_audit.py`'s own docstring ("cannot prove the read is off THIS
structure") arriving as a live temptation rather than a caveat, and it is worth
more than the row: the fix that makes the finding go quiet is available, costs
one word, and is false. Measured 2026-07-30 across nine candidate consumers —
`import_provenance_check.py`, `policy_audit.py`, `escape_check.py`,
`part_facts_check.py`, `pin_audit.py`, `generate_board_generic.py`,
`export_jlc_package.py`, `placement_gates.py` and `assembly_coverage.py` — the
key reaches a read position in exactly one of them, and that one is the
collision. Pinned by `tests/t1_schema_reader.py`
`t_real_finding_module_envelope_has_no_reader_and_the_obvious_one_is_a_collision`.

The honest home is M-IMPORT's machine half. `import_provenance_check.py` already
grades exactly this class — a foreign device's geometry, with a provenance grade
per fact — and is scoped to `03_src/rules/mates.yaml` against `spf/<device>/`,
which this contract's own M-IMPORT section says in as many words does not reach
this folder. A purchased module IS foreign hardware the board mates to, so the
debt has two admissible settlements and both are cheap to state: either the
envelope moves to `spf/<device>/` with a `mates.yaml` reference (canon
M-RESTATE — one home per fact, boards reference and never restate), or
`import_provenance_check.py` grows a `02_parts` reach. Until one of them lands,
these five rows are OWED, and the two self-consistency sums named in the table
(`total_thickness_mm` against its three terms, `bottom_side_max_protrusion_mm`
against the `side: bottom` features) are the cheapest first bite.

### keys: 02_parts/*/part.yaml

| key | reader | why |
|---|---|---|
| `mpn` | `part_facts_check.py, bom_source_check.py, shopping_list.py` | the MPN authority (F-MPN prefers this FIELD over the directory name) |
| `manufacturer` | `shopping_list.py` | distributor search + M-QUOTE |
| `package` | `escape_check.py` | P-ESC/P-TIER package class |
| `footprint` | `generate_board_generic.py, escape_check.py, policy_audit.py` | the FPID realised on the board |
| `type` | `module_first_check.py, policy_audit.py, power_topology.py, bom_source_check.py` | P-MOD complex-subsystem scope + E-TOPO topology assertion + BOM row class |
| `value` | `part_facts_check.py, bom_source_check.py, bom_legibility_check.py` | the BOM/CPL value, graded against the fab BOM |
| `verified` | `pin_audit.py, policy_audit.py` | S-VER: the datasheet figure+page citation, read as a KEY not by grep |
| `status` | `jlc_stock_check.py, release_freshness_check.py, shopping_list.py` | lifecycle |
| `superseded_by` | OWED | the retirement pointer of a replaced dossier; `status:` is read, this is not, so a superseded part names its replacement to nobody |
| `function` | ADVISORY | a one-line human summary of what the part is for; the graded facts are `type`, `value` and the `asserts:` block |
| `design` | ADVISORY | the free-prose design narrative (a `\|` block on five converter dossiers); its numbers belong in `electrical:`/`limits:` where they can be asserted |
| `notes` | `policy_audit.py` | P8: the part's placement/design notes, whose PRESENCE P-LAYOUT grades |
| `gotchas` | ADVISORY | warnings addressed to the next author to touch this part (128 dossiers). Machine-grading English here would be theatre; what IS graded is that the expensive facts it warns about live in `pins:`/`escape:`/`limits:` |
| `note_dirname` | ADVISORY | records why the directory name differs from the MPN; the MPN authority reads `mpn:` |
| `on_live_board` | OWED | a claim that this exact part is on a shipped board — checkable against the sealed BOM and checked by nothing |
| `layout_refs` | `policy_audit.py` | the LAYOUT PRECEDENT SEARCH record. **Was OWED until 2026-07-30**, and the debt was real: P8 grades `layout.source:`, while this parallel list — the record of WHAT ELSE EXISTED and how strong it was — was read by nobody. P-PREC now reads it, counting the bare-string form OWED and grading the mapping form |
| `layout_refs[].tier` | `policy_audit.py` | P-PREC: the SKILL.md authority tier this artifact sits at, 1-4. The tier IS the grade — without it an entry names what was read and still cannot be ranked |
| `layout_refs[].artifact` | `policy_audit.py` | P-PREC: the thing itself (URL / document + figure + page / design-file name). An unnamed precedent is not a precedent, and `tier: 2, reached: true` with nothing named is an unfalsifiable claim to have done the most valuable half of the search |
| `layout_refs[].reached` | `policy_audit.py` | P-PREC: CONSULTED (`true`) vs merely KNOWN-OF (`false`). This is the whole distinction the gate exists to make — the pluto-rx2-8way RP2040 dossier drew it correctly in PROSE and no machine could see it |
| `layout_refs[].why` | `policy_audit.py` | P-PREC: REQUIRED (>=20 chars) on a `reached: false` entry. An unreached tier is a DEBT, and a debt without a reason is the waiver-without-evidence shape (canon M-WAIV) |
| `datasheet.url` | `pin_audit.py` | the datasheet under review |
| `datasheet.local` | OWED | the in-tree PDF path. M-DEPEND grades that a sealed release carries its dossiers; nothing grades that this path RESOLVES, so a moved PDF is silent |
| `datasheet.sha256` | OWED | the fetched PDF's digest — an M-IMPORT provenance grade nothing recomputes, so a re-fetched or substituted revision cannot be detected |
| `datasheet.revision` | OWED | the revision the pin map and limits were read from; a datasheet revving under a sealed release is exactly M-DEPEND's class and this field is where it would be caught |
| `datasheet.doc_id` | ADVISORY | the vendor document number, for a human re-fetching it |
| `datasheet.fetched` | ADVISORY | the date the PDF was pulled, for a human judging staleness |
| `datasheet.pages` | ADVISORY | page count, so a truncated download is visible to a reader |
| `datasheet.note` | ADVISORY | prose about the fetch |
| `datasheet.provenance` | ADVISORY | prose about where the PDF came from |
| `datasheet.product_page` | ADVISORY | the vendor landing page |
| `datasheet.lcsc_url` | ADVISORY | the distributor page the PDF was reached through |
| `datasheet.package_url` | ADVISORY | a human retrieval link for the vendor package page; the executable package identity is `package`/`footprint`, and no gate reads this URL |
| `datasheet.drawing` | ADVISORY | a human citation to the package drawing; `pin_audit.py` grades the figure/page citation in `verified`, not this parallel prose field |
| `datasheet.drawing.url` | ADVISORY | the human retrieval URL for the cited package drawing; no gate fetches it |
| `datasheet.drawing_url` | ADVISORY | legacy flat spelling of the human retrieval URL for a package drawing; no gate fetches it |
| `datasheet.drawing.revision` | ADVISORY | the human-readable package-drawing revision; no gate compares it with the vendored footprint |
| `datasheet.drawing.sha256` | OWED | the package-drawing digest is a checkable provenance claim, but no reader recomputes it, so substituted drawing content is silent |
| `datasheet.pdf` | ADVISORY | an alternate spelling of `local:` on two dossiers; consolidate on `local:` |
| `datasheet.file` | ADVISORY | as `pdf:` |
| `pins.<N>` | `pin_audit.py, circuit_json_to_kicad_sch.py, policy_audit.py` | the pin map, in the bare `<N>: "name"` scalar form |
| `pins.<N>.name` | `pin_audit.py, circuit_json_to_kicad_sch.py, policy_audit.py` | the pin map, mapping form |
| `pins.<N>.note` | ADVISORY | per-pin datasheet prose (274 pins). The CONSTRAINTS inside it belong in `electrical.pins.<N>`, which IS graded by `node_level` |
| `pins.<N>.tie` | OWED | 84 pins name the net they must land on and NOTHING reads it — the `GND_ISO` field class. E-NETREF K13; the patch is in `schema_reader_audit.py`'s docstring |
| `escape.style` | `escape_check.py` | P-ESC escape geometry class |
| `escape.pitch` | `escape_check.py` | P-ESC pitch |
| `escape.tier_required` | `escape_check.py, policy_audit.py` | P-TIER: the fab tier the escape needs |
| `escape.escapes_worst_side` | `escape_check.py` | P-ESC worst-side count |
| `escape.conditions` | `escape_check.py` | P-ESC qualifying conditions |
| `escape.tier_conditional` | OWED | a declared conditional fab tier that no reader compares with `escape_check.py`'s independently computed `tier_conditional()` result; a stale declaration is currently silent |
| `escape.checked` | OWED | the date/method the escape was calibrated. 125 dossiers carry it; `escape_check.py` recomputes the geometry and never reads this, so a stale calibration note is invisible |
| `escape.loaded_side_escapes` | OWED | a second escape count for the loaded side, declared once and read by nothing |
| `escape.per_pin.<N>` | OWED | per-pin escape overrides; not declared by any dossier today, and P-ESC would not see one if it were |
| `mates` | `escape_check.py` | the mating connector class |
| `layout.source` | `policy_audit.py` | P8: the datasheet Layout section cited |
| `layout.reviewed` | OWED | the date the layout section was read. P-LAYOUT grades that `layout:` EXISTS and that `source:` is cited; nothing grades this, so an unreviewed copy of a sibling's block reads identically |
| `layout.notes` | `policy_audit.py` | P-LAYOUT: prose rules, whose presence satisfies the declare-something obligation |
| `layout.keep_short[].net` | `policy_audit.py, net_reference_audit.py` | P-ADJ span budget subject (E-NETREF K7) |
| `layout.keep_short[].max_span_mm` | `policy_audit.py` | P-ADJ budget; a non-numeric value is a FAIL, not a skip |
| `layout.keep_short[].anchor_pins` | `policy_audit.py` | P-ADJ anchor override — an unstated anchor is a hidden assumption |
| `layout.keep_short[].why` | `policy_audit.py` | the datasheet requirement being honoured |
| `layout.adjacency[].refdes` | `policy_audit.py` | P-ADJ refdes-pair budget (the incident: read by nothing until 2026-07-29) |
| `layout.adjacency[].a` | `policy_audit.py` | P-ADJ pair member |
| `layout.adjacency[].b` | `policy_audit.py` | P-ADJ pair member |
| `layout.adjacency[].max_mm` | `policy_audit.py` | P-ADJ copper-gap budget |
| `layout.adjacency[].why` | `policy_audit.py` | the datasheet requirement being honoured |
| `asserts[].assert` | `part_facts_check.py` | P-FACT: which assertion kind |
| `asserts[].equals` | `part_facts_check.py` | P-FACT expected value |
| `asserts[].tolerance_pct` | `part_facts_check.py` | P-FACT tolerance window |
| `asserts[].polarity` | `part_facts_check.py` | P-FACT `pad1_net_polarity` |
| `asserts[].pad` | `generate_board_generic.py, part_facts_check.py` | P-FACT subject pad |
| `asserts[].level` | `part_facts_check.py` | P-FACT `msl` level |
| `asserts[].floor_life_h` | `part_facts_check.py` | P-FACT `msl` floor life |
| `asserts[].layers` | `generate_board_generic.py` | `keepout_region` layers (DEFERRED, and P-FACT says so) |
| `asserts[].region` | `generate_board_generic.py` | `keepout_region` outline (DEFERRED) |
| `asserts[].why` | `part_facts_check.py` | REQUIRED evidence (canon M4) |
| `electrical.vdd` | `electrical_invariants.py` | `node_level` supply reference |
| `electrical.vdd_net` | `electrical_invariants.py` | `node_level` supply net |
| `electrical.defaults.*` | `electrical_invariants.py` | `node_level` per-part default thresholds and drive strength |
| `electrical.pins.<N>.*` | `electrical_invariants.py` | `node_level` per-pin thresholds (`v_ih_min`, `v_il_max`, their `_frac_vdd` forms, `r_on_ohm_max`) and per-pin prose |
| `electrical.source` | ADVISORY | the datasheet section the electrical block was read from, for a reviewer |
| `electrical.*` | OWED | the rest of the block is per-part datasheet numbers with no consumer: coil pull-in/resistance over temperature, Vce(sat)/Vds points, r_on corners, dropout, tempco, `t_op`. Each is the kind of number a `part_value`/`node_level` invariant SHOULD cite, and the cooksense relay coil at 70 C is the worked case for why (it was checked by hand) |
| `limits.*` | ADVISORY | the open per-part absolute-maximum/rating fact bag. The EXECUTABLE channel for anything in here is an `asserts:` entry or an `electrical_invariants.yaml` `part_value`/`node_level` that cites it; the bag itself is a human's datasheet transcription and forcing a schema on it would only push the facts out of the tree |
| `land_pattern.*` | ADVISORY | the human derivation record for a vendored footprint — pad sizes, fillet balance, datums, the datasheet figure they came from. Its CONSEQUENCE is graded, hard, by `jlc_twin` against JLC's own CAD model (canon M1), which is a stronger check than reading this back would be |
| `ratings.*` | OWED | per-part electrical ratings (`i_sat`, `dcr_max`, `impedance_100mhz`, `voltage`, `dielectric`, ...). Unlike `limits:` these are the SELECTION criteria the part was chosen on, so they are assertable — an inductor's `i_sat` against the rail's `iout_max_A` is arithmetic nothing does |
| `power_pins.<NAME>.*` | OWED | a per-rail pin grouping on the one 128-pin MCU dossier. `pins:` is graded; this parallel structure is a second home for the same map and read by nobody |
| `mechanical.pcb_thickness_mm` | OWED | the part's own laminate thickness — one term of the carrier stack and of `total_thickness_mm`'s sum, read by nothing |
| `mechanical.top_side_max_height_mm` | OWED | tallest feature on the face AWAY from the carrier: the enclosure/lid budget. Spent by a human today, and nothing reconciles it against the per-feature heights in the bag below |
| `mechanical.bottom_side_max_protrusion_mm` | OWED | **THE SEATABILITY NUMBER, and the load-bearing key of this block.** Tallest feature on the CARRIER-FACING face, so non-zero means the part cannot be reflowed flat — a POPULATION decision, not a footprint note. RP2040-Zero declares 1.000 (the 12 MHz crystal, MEASURED off the vendor STEP) and pluto-rx2-8way-v2's `assembly.yaml` carries the matching `not_assembled` entry for `U_MCU`, whose evidence opens "MECHANICAL, and MEASURED rather than argued". `assembly_coverage.py` grades that entry's SHAPE — reason inside the closed vocabulary, dated evidence, the ref off the CPL — and never that the reason is TRUE. The intended gate is the one that makes the two homes able to DISAGREE OUT LOUD |
| `mechanical.total_thickness_mm` | OWED | the stack, and it is DERIVED: bottom protrusion + laminate + top height (1.000 + 1.091 + 3.250 = 5.341 on the one dossier that declares it). A sum nothing re-adds is the `ratings.*` shape — assertable arithmetic with no assertion |
| `mechanical.*` | OWED | the per-FEATURE 3D bag: one entry per named feature the vendor model contains (`usb_c`, `buttons`, `ws2812`, `rp2040`, `crystal`, `rt9013`, `flash` on the RP2040-Zero), each carrying its `side`, its footprint (`extent_mm`/`centre_mm`/`body_mm`) and how proud it stands (`protrusion_mm`/`height_mm`), plus per-kind connector terms (`mating_face_y_mm`, `z_mm`, `shell_x_mm`, `cavity_centreline_above_pcb_top_mm`). BLANKET because the feature NAMES and their per-kind terms are both open; the four scalars above are enumerated OUT of it because they are not. Two facts in here are ARITHMETIC against those scalars and nothing performs it: `bottom_side_max_protrusion_mm` must be the max `protrusion_mm` over the `side: bottom` entries (max(0.850, 1.000, 0.700) = 1.000 today), and a `mating_face_y_mm` past the part outline is a carrier KEEPOUT the floorplan must honour (24.816 against an outline ending at 23.500 — 1.21 mm of receptacle hanging over the board edge) |
| `mechanical_pads.<NAME>.*` | OWED | shield/NPTH pads and their KiCad pad names — the field that decides whether a shell tab is a net or a hole, read by nothing |
| `orientation.*` | OWED | the as-placed rotation and pin-1/pole marker evidence. The rotation AUTHORITY is `jlc_rotation_*`; this per-dossier claim is not cross-checked against it, which is the M-PROV shape |
| `loading_caps.*` | OWED | a crystal's load-capacitor formula and per-leg value — an `electrical_invariants.yaml` `part_value` waiting to be written |
| `i2c.address` | OWED | the device address; a bus with two parts at one address is checkable from the dossiers alone |
| `dropout_mv` | `power_topology.py` | E-TOPO linear dropout bound |
| `pdiss_max_mw` | `power_topology.py` | E-TOPO linear dissipation bound |
| `sourcing.lcsc` | `bom_source_check.py, part_facts_check.py, shopping_list.py` | the LCSC code on the BOM |
| `sourcing.alternates[].lcsc` | `bom_legibility_check.py` | F-ECHO substitution candidates |
| `sourcing.alternates[].mpn` | `bom_legibility_check.py` | F-ECHO substitution candidates |
| `sourcing.digikey` | `shopping_list.py` | Q-family distributor lookup |
| `sourcing.note` | `shopping_list.py` | sourcing prose surfaced in the shopping list |
| `sourcing.jlc_basic` | OWED | basic-vs-extended, which sets the assembly fee and the stock risk; `jlc_stock_check.py` queries the catalog and never reads this claim, so the two cannot be reconciled |
| `sourcing.do_not_use` | OWED | an explicit ban on a code. Nothing reads it, so a banned code can be typed back into a BOM with every gate green |
| `sourcing.mfr_substituted` | OWED | records that the manufacturer was substituted; `release_freshness_check.py --sourcing-supersede` grades the BOM/CPL delta of a substitution and does not read this |
