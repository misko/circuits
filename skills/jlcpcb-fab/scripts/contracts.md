# contract: skills/jlcpcb-fab/scripts/

**Purpose** — executable order/verification tooling (gerber export, BOM/CPL,
stock, twin).

## Allowed

| Pattern | What |
|---|---|
| `*.py` | tools — network access mocked in tests via `$EASYEDA2KICAD` seam |
| `*.sh` | drivers |
| `*.csv` | data tables: `jlc_lcsc_rotations.csv` — the ONLY rotation AUTHORITY, `LCSC,rotation,evidence,polarity` (canon A-ROT); and `jlc_rotations_db.csv` — the footprint-NAME DB, kept loaded as an ADVISORY cross-check and never obeyed |
| `contracts.md` | this file |

## Audit

- Checkers: clean + known-bad tests in `tests/` (t1_jlc_twin.py,
  t1_bom_source.py, t1_release_freshness.py, t1_assembly_gates.py,
  t1_fab_payload.py, t1_bom_legibility.py,
  t1_sealed_dependency.py).
- **The FAB LEGIBILITY family (canon F-LEGIBLE, ADR-0006) — the BOM is graded
  AS JLC PARSES IT, not as we wrote it.**
  - `bom_legibility_check.py TARGET` (a sealed release dir, a project dir, or
    a BOM csv; plain python3, offline, no pcbnew) runs **F-MPN** (every coded
    row carries BOTH MPN and LCSC, resolved from `02_parts/<MPN>/part.yaml`
    then the vetted `references/lcsc_passives_ledger.yaml`, and the two paths
    must AGREE), **F-WORDS**
    <!-- TARGET SEMANTICS: the target's MUTABILITY changes the verdict, so
    TARGET is not merely a path. Both authorities above are EXTERNAL to the
    artifact, so a SEALED release's verdict was a function of the CURRENT
    `02_parts/` tree — cooksense v1.6 flipped PASS->FAIL and back on unchanged
    immutable bytes in one session, and 9 of 33 sealed releases failed once both
    external authorities were neutralised. A release dir is therefore graded
    with its own `verification/stock_check.csv` as a release-internal
    code->mpn map, consulted LAST and as an EXISTENCE authority only (JLC's
    `componentModelEn` is a catalog DESCRIPTION, not the MPN, on 7 of 156 fleet
    rows). A row no hand-verified authority resolves reports NOT RE-DERIVABLE
    (CORROBORATED / UNGRADEABLE, with a denominator) on an IMMUTABLE target and
    a plain FAIL on a MUTABLE one — a project dir or a staging BOM is still
    live, so nothing there is excused. A blank MPN on a coded row is graded
    BEFORE resolution and so is an unconditional FAIL on every target:
    immutability can never excuse it, because no authority is needed to see
    it. --> (the Comment is a human-readable value — never an
    LCSC code, never a `simple_*` placeholder, never blank) and **F-ENCODE**
    (the file decodes IDENTICALLY under UTF-8 and cp936; a byte-order-mark or
    ASCII `Ohm` both pass — the check is INDIFFERENT to which). `--echo
    JLC_RESOLVED.csv` runs **F-ECHO**, the human-gated half: JLC's resolved
    table diffed back against ours, a substitution is a FINDING.
    WHY: crow-recorder-central-v2 v1.5's BOM was uploaded and its parts "were
    not being picked up by their web processing". Every prior BOM check asked
    "is this value CORRECT?" and none asked whether the recipient can PARSE
    the file — canon M1, all of them reading the document the way WE wrote it.
    MEASURED over 26 sealed BOMs / 1205 rows: **914 blank MPN** (962 counting
    the one file with NO MPN COLUMN at all, which the 914 denominator silently
    excluded), **470 illegible Comments**, **23/26 carrying `Ω` with no UTF-8
    byte-order-mark** so a cp936 reader sees `惟`. **25 of 26 fail.**
    The MPN AUTHORITY is the dossier's `mpn:` FIELD, not its directory name:
    a path cannot hold the `/` in `LM5116MHX/NOPB` or `SMD2920-700/16N`, and
    shipping the directory name for those would put a string that is not the
    part number in the column whose whole job is to be the part number.
    The graded artifact is the SHIPPED bom.csv (canon M-SHIP); the authority
    lives in the project, not the archive, and is NAMED in the output.
  - `export_jlc_package.py` enforces the same three at export time and BLOCKS
    (exit 3), writing nothing uploadable — a coded row with no resolvable MPN
    or an illegible Comment stops the package, exactly as A-ROT does for an
    unsourced rotation. `--allow-illegible-bom` is the loud, discouraged
    escape hatch. It writes the BOM as **UTF-8 with a byte-order-mark**, and
    emits `bom_echo_gate.txt` — the F-ECHO worklist, the sibling of A-POL's
    `rotation_human_gate.txt`.
  - **`lcsc_mpn_map.csv` is RETIRED as an input.** It was an OPTIONAL,
    HAND-MAINTAINED side-file read through `mpn_map.get(code, "")` — a second
    home for a fact `02_parts/<MPN>/` already owned, a silent default (the
    `row_kind` shape canon M-COVER forbids), and opt-in by construction, all
    three at once. Only ONE project ever created it; eight of nine shipped
    100% blank MPN. Where it DID exist it drifted: usb-hub-3s-v3 v1.5-v1.8
    ship SW1 as `SS12D07VG6 087` against the dossier's `SS12D07VG6-087`. A
    leftover file is now IGNORED loudly and its drift REPORTED. An MPN
    override belongs in the part's own `part.yaml`, which is the one home.
  - **F-ECHO stays HUMAN-GATED by decision, not by omission** (ADR-0006 "NOT
    built"): a JLCPCB API integration would require handing over credentials,
    the same line already drawn on the Mouser/Nexar APIs. The one substitution
    this fleet has seen — our C82317 for crow-recorder-central-v2's U5 in
    THREE places, JLC's resolved output C131025 — is only visible from inside
    their UI, and the ritual lives in the release ORDER_README.
- **M-DEPEND (canon M-DEPEND, ADR-0007's M-ENTRY half) — a SEALED release may
  not depend on a mutable fact it does not carry.**
  - `sealed_dependency_check.py PROJECT_DIR` (also `--release DIR`, `--fleet`,
    `--json OUT`, `-v`; plain python3, offline, no pcbnew and **no git**)
    grades every LCSC code in every sealed `fab/bom.csv` the project ships —
    ALL of them, not just the newest, because the victims of a deletion are the
    OLD releases and v1.6 does not stop being orderable because v1.7 exists.
    Ladder: **GRADED** (a hand-verified authority resolves it) > **CORROBORATED**
    (only the release's own `verification/stock_check.csv`, an EXISTENCE record)
    > **ORPHAN** (nothing). ORPHAN FAILs; CORROBORATED with a FILLED MPN cell
    FAILs; CORROBORATED with a BLANK cell is the WHOLE WAIVER and is structural
    — there is no waiver FILE, because a waiver a human writes gets copied to
    the next board and becomes an inherited defect. A DISAGREE between the
    sealed cell and the live authority is REPORTED and NOT re-failed: equality
    is F-MPN's home (canon M-WIDTH).
    It imports `bom_legibility_check.MpnAuthority` rather than re-deriving the
    resolution order, so the two gates cannot disagree about what the authority
    says — F-LEGIBLE MEASURED that consulting the release map FIRST manufactures
    7 false DISAGREE failures across four sealed releases, two of them LIVE.
    WHY: cooksense's v1.7 work removed `02_parts/ULN2803ADWR/` (ADR-0023
    legitimately replaced the coil driver) and the SEALED
    `cooksense-v1.6-2026-07-27` — immutable, bytes unchanged — flipped F-MPN
    **PASS → FAIL** on row 56 (`C9683`), then flipped **back** when the dossier
    was restored. **Twice in opposite directions in one session, and the
    self-healing direction is the worse half: `t1_fleet_regrade` went green on
    its own and nothing recorded that it had been red.** 9 of 33 sealed releases
    would have failed. THE TRIGGER IS NOT ONLY A DELETION —
    `02_parts/MCP23017-E-SS` was **EDITED** (`sourcing.lcsc` C506653 → C558584
    at stock 0) and 57044c0 repaired it by hand with the comment *"The old code
    MUST stay resolvable here forever"*, a human promise with no gate.
    **IT GRADES STATE AND NOT A GIT DIFF, on measurement:** a HEAD diff cannot
    see a deletion that is ALREADY COMMITTED (exactly how the incident
    happened), cannot reach an orphan nobody touched (usb-hub-3s-v3 v1.1
    `C2866319` and v1.2 `C140903` resolve from nothing TODAY, and
    `07_releases/` is immutable so they never can be fixed there), and has no
    stable reference while sibling agents hold uncommitted work. State grading
    SUBSUMES the diff: a deletion and an edit land as the same state.
    CENSUS 2026-07-29 (1327 coded rows / 33 releases): 8 carry a map, 25 do
    not, **539 rows across 25 releases are GRADED only because a dossier is
    still in the tree**, 2 releases are already broken, 5 carry a
    tree-dependent finding, 0 sit at CORROBORATED-with-a-filled-cell.
    Pinned by `tests/t1_sealed_dependency.py` — 4 known-bad, and the headline
    two are the REAL edits (the ULN2803ADWR deletion and the MCP23017-E-SS
    re-source) replayed on a scratch copy of the real archive.
- **The FAB PAYLOAD family (canon F-*) — the shipped zip is a GRADED
  artifact, not merely a hashed one (canon M6, ADR-0004).**
  - `fab_payload_census.py RELEASE_DIR` opens `fab/*_gerbers.zip` and grades
    it against `source/*.kicad_pcb`. **F-POUR**: a copper layer carrying pour
    zones must carry G36 regions in the shipped gerber, and regions on a layer
    the board declares no zone for fail in reverse. **F-IDENT**: two copper
    layers with different `%TF.FileFunction` must not be byte-identical once
    that line is normalised out.
    WHY: usb-hub-3s-v3 shipped v1.6/v1.7/v1.8 with **0 G36 regions on all four
    copper layers** — 44287.91 mm2 of missing copper — and every gate was
    green, because `kicad-cli pcb drc --refill-zones` REFILLS IN MEMORY and so
    returns 0/0/0 on a board whose saved file has no fill. `In1_Cu.g1` and
    `In2_Cu.g2` were byte-identical at 18921 B apart from `Copper,L2` vs `L3`.
    Nothing in this repo had ever opened the zip that becomes copper.
    It parses the board from `.kicad_pcb` TEXT and the payload from GERBER
    TEXT — **neither uses pcbnew**, so it cannot inherit the in-memory-refill
    blindness of the tool under test (canon M1).
    KEEPOUT/rule-area zones are excluded from the pour census: they have no
    fill by design, and counting them made a first draft report a good board's
    two keepout-only inner layers as bare (the adjacent-property error).
    A genuinely pourless board (the cooksense interposer: BRIEF S4/S7 forbid a
    plane in the keypad zone) must DECLARE `pourless: "<reason>"` in
    `assembly.yaml` — a bare `pourless: true` is refused, because a waiver
    needs evidence rather than assertion.
- **A-RENDER (canon M1) — the twin render is GRADED, not merely produced.**
  - `twin_overlay.py BOARD TWIN.png --side {top,bottom} --twin-dir DIR
    --bom fab/bom.csv --assembly 03_src/rules/assembly.yaml
    --twin-report twin_report.csv` measures each body **in PIXELS** out of the
    PNG and compares it against the position the BOARD implies (mesh bbox x
    JLC's own model transform x placement). The two channels are independent by
    construction, so it **cannot agree with a wrong mount** — an analytic-only
    check would share `jlc_twin`'s method and inherit its error.
    WHY: crow-recorder-central-v2 v1.5 sealed with its USB-C drawn 90 degrees
    rotated because `jlc_twin` mounted the mesh on a pad-number fit it had
    ITSELF declared unreliable in the same row (`PAD-MISMATCH`), while telling
    the reviewer to "VERIFY leads sit on pads visually" — pointing at the
    picture that failed fit had corrupted. The predecessor tool drew courtyard
    boxes and computed no body position anywhere in the file: a rendering aid
    wearing a checker's docstring, wired into nothing, with no known-bad.
    **Headline acceptance:** against the SEALED v1.5 render it FAILS on J2 at
    centre delta 1.435 mm / outward 1.491 mm. The fab data is correct; the
    RENDER lied, and that distinction is what a reviewer cannot make unaided.
    **Coverage is partial by construction** — pixel extraction resolves large
    isolated parts, not dense 0402 fields (v1.5: `22 measured / 177`). Every
    uncovered ref is NAMED with its reason, and a ref that SHOULD have been
    measurable and was not is a FAILURE, never an omission.
    It REFUSES rather than drawing boxes it cannot trust: perspective/iso
    renders, a `--side` contradicting the filename, a side with no courtyards.
    Run AFTER `jlc_twin` and BEFORE the fresh-context render review — that
    review is worthless on a render nobody has proved faithful.
- **The ASSEMBLY family (canon A-POP / A-STOCK) — PCBA is the deliverable,
  so the order artifacts are GATED, not just produced.**
  - `assembly_coverage.py TARGET` (A-POP), plain python3, takes a sealed
    release dir OR a project dir. It requires
    `{board footprints} − {CPL designators}` to EQUAL `assembly.yaml`'s
    `not_assembled:` set (honouring declared `exempt_prefixes:`), and FAILs
    a blank-LCSC BOM row whose refs are on the CPL, a declared-unpopulated
    ref still placed or missing `exclude_from_pos_files`, a board part
    carrying that attribute yet placed, a schema entry without
    reason/evidence/disposition, a consigned part listed as not_assembled,
    and a MANIFEST `not_assembled:` line that is absent or disagrees with
    `assembly.yaml`. Prints the per-side placement histogram.
    Its board reader (`read_footprints`) parses the `.kicad_pcb`
    s-expression DIRECTLY — no pcbnew — so the checker shares no oracle with
    `export_jlc_package.py`, which reads the same facts through the pcbnew
    API (canon M1). The two are cross-checked on a real sealed board
    (195/195 footprints agree on refdes/footprint/orientation/layer/pad
    count/attrs, 0 mismatches) and that agreement is pinned as a test, so the
    independent parser cannot rot into a second, quieter bug.
  - A-STOCK lives in `release_freshness_check.py` check (e), always on —
    see below.
  - `jlc_twin.py --assembly 03_src/rules/assembly.yaml` reads the coded
    not-assembled/consigned REF=LCSC pairs from the ONE declared home
    (`--also` still works for an ad-hoc probe).
- **A-ROT / A-POL / M-PROV (rotation authority) — LANDED 2026-07-25, blocking
  BY DEFAULT.** A footprint-NAME match can no longer decide a CPL cell; the
  per-LCSC MEASURED table is the only authority and silence is a FAIL.
  - `jlc_rotation_resolve.py` (shared, no-pcbnew, unit-testable) returns
    source `lcsc` or `unsourced`. There is no `name` source any more.
    `cross_check()` reports an advisory-name-DB disagreement and NAMES an
    EXACTLY-180 gap as what it is — a negated rotation operator or an
    opposite pad-1 convention, never "the DB is stale".
  - `export_jlc_package.py` BLOCKS (exit 2) on any unsourced placement,
    writes `rotations_unsourced.csv` as the worklist, and REMOVES a stale
    `bom_jlc.csv`/`cpl_jlc.csv` so a blocked run leaves nothing uploadable.
    `--allow-unsourced-rotations` is the loud, discouraged escape hatch.
  - The ONE exemption is MEASURED, not named: `jlc_footprint_symmetry.py`
    exempts a footprint that is its own 180-degree reflection in BOTH pads
    and graphics (2 pads only). Measured on usb-hub-3s-v3: chip R/C/L/fuse
    exempt at 0.000 mm; `CP_Elec_6.3x7.7` NOT (pads 0.000 mm, graphics
    1.812 mm) — the polarized cap that shipped REVERSED on two boards is
    caught by the graphics channel alone.
  - `jlc_rotation_audit.py --table` grades the authority itself: **M-PROV**
    (a dated measurement with a residual, and no provenance naming this
    pipeline's own output — the six rows populated FROM `jlc_twin.xform()`
    are the incident) and **A-POL** (the `polarity` column declares
    `n/a | two-channel | single-channel`; a numbering-free channel must be
    RECORDED in the row, or the JLC order-preview human gate named).
    A-POL's `n/a` grading is ACCEPT-ON-EVIDENCE, not reject-on-keyword
    (2026-07-26): the polarity-vocabulary regex is a substring match that
    cannot see a negation and fired twice on TRUE statements ("confirmed
    ..., not assumed"; "THE PART IS NOT POLARIZED"). An `n/a` row may use
    polarity vocabulary freely PROVIDED it makes a positive unpolarized
    claim AND cites the manufacturer document (section/table ref or
    archived .pdf) — BOTH required; the bar is a datasheet because symmetry
    is the one polarity question geometry cannot settle.
    `--fleet` prints the per-board UNSOURCED migration worklist.
  - `jlc_rotation_resolve.py` reads the authority table path from
    `$JLC_LCSC_ROTATIONS` (fallback: the shipped `jlc_lcsc_rotations.csv`).
    This is a TEST SEAM, never a production override: it exists because two
    known-bad export fixtures borrowed the real usb-hub-3s-v3 board's
    unsourced state and EXPIRED the moment its rows were measured
    (2026-07-26) — a known-bad fixture must own its brokenness, so the
    tests inject a header-only table instead.
  - `jlc_rotation_measure.py` is the ONE way a row is MADE. It reports the
    channels separately and never merges them, and every geometric channel
    must be read in the footprint-LOCAL frame: `pad.GetFPRelativePosition()`
    is local, but `shape.GetStart() - fp.GetPosition()` is the BOARD frame
    (there is no `PCB_SHAPE.GetStart0()` on this build), and mixing the two
    ran the PIN-1-MARK channel exactly `board_rot` degrees out of step with
    every pad channel — 2026-07-28, C485354/J_MODE at board_rot 90, the
    fleet's FIRST non-zero placement to reach that channel; every earlier
    pin-1-decided row sits at board_rot 0 where it is invisible. A BACK-SIDE
    footprint is additionally mirrored and gets NO channel rather than a
    wrong one.
  - **PIN-1 DISSENT is BLOCKING (exit 1) and WITHHOLDS the row.** A decisive
    pin-1 marking naming a different angle from the one the row would claim
    is the A-POL alarm itself; before this it was four numbers in a channel
    row with no verdict, so catching it was a human's job. Resolve from the
    DATASHEET terminal drawing, never by outvoting a channel.
  - Pinned by `tests/t1_rotation_authority.py` (one known-bad per mechanism,
    red-verified against the restored pre-fix resolver: 8 tests go RED; plus
    the two 2026-07-28 frame tests, RED at 0 passed / 2 failed).
- **`release_index.py` is the ONE home for release SELECTION** — "which board
  does this release directory belong to" and "which of them is newest". A
  LIBRARY (no verdict, nothing graded); `release_freshness_check.py`,
  `policy_audit.py`, `shopping_list.py` and `power_topology.py` all import it,
  so no consumer of release ordering can re-derive it differently (canon
  M-WIDTH). Board identity is the slugged stem of `04_kicad/*.kicad_pcb` —
  authoritative, in-tree, no hardcoded name list — and slugging is what makes
  `crow_recorder_central_v2` and `crow-recorder-central-v2` one board.
  Versions order NUMERICALLY PER COMPONENT: `v1.10 > v1.9 > v1.2`.
  **A set it cannot attribute raises `ReleaseSetError` naming the directory —
  never a guess** (canon M-COVER): an unparseable dir name, a prefix naming a
  board the project does not build, a BARE `v1.0-<date>` where the project
  builds more than one board, or "the latest" asked with no board named when
  two series exist.
  WHY, measured 2026-07-27: `smc0985-cooksense` holds `cooksense-v1.0…v1.4`
  AND `interposer-v1.0`; `rels[-1]` returned the INTERPOSER, so policy_audit's
  M-REL/M-BOM/A-POP/A-BODY graded the wrong archive while the board under
  audit was cooksense, and M-REL demanded `SUPERSEDED.md` on the live
  `cooksense-v1.4` — blocking a v1.5 seal. Separately `v1.10` sorted BEFORE
  `v1.9` as text (usb-hub-3s-v3, 2026-07-27): fixed in policy_audit and left
  standing in `shopping_list.newest_release_boms`, the M-WIDTH failure this
  module closes. Pinned by `tests/t1_release_index.py` (5 known-bad, the
  headline one running the PRE-FIX selector against the real tree so the red
  side is measured on every run).
- `release_freshness_check.py <release_dir>` gates a seal: it FAILS when a
  generated fab/PDF artifact is sha256-identical to an earlier release of the
  same board (stale/inherited output), when the shipped
  `verification/policy_audit.md` result disagrees with the MANIFEST's claimed
  result (audit FAIL vs manifest 0-FAIL/PASS), or when the shipped
  `ORDER_README.md` still carries a draft/placeholder marker — the three
  defects usb-hub-3s-v3 v1.2 shipped DO-NOT-ORDER past every other gate
  (2026-07-23). Documented same-name-identical exceptions (with a reason) go
  in `<release_dir>/verification/freshness_exceptions.txt`.
- `release_freshness_check.py` also runs **A-STOCK (check (e), always on)**:
  every coded BOM line with a CPL row is graded OFFLINE against the stock
  evidence the release ships — `stock >= qty x build_quantity`, or an
  `assembly.yaml` `sourcing_plan:` entry with `measured_stock` +
  `measured_on`. A MISSING OR UNPARSEABLE VERDICT IS A FAIL, NOT A SKIP
  (cooksense v1.1 ships a raw `--out` CSV report as `stock_check.txt` with
  ZERO verdict lines; crow-recorder-central-v2 v1.0-v1.3 each end in `FAIL:`
  with their own CPU at `LOW_STOCK(0)`, and nothing read it). Live re-query
  stays in the opt-in `--net` tier — a gate that needs the network is a gate
  that gets skipped. `jlc_stock_check.py --json OUT` writes the one
  machine-readable sidecar with an EXPLICIT verdict; ship it as
  `verification/stock_check.json`.
- `release_freshness_check.py <release_dir> --docs-only-supersede <prior>`
  is the mode for a DOCUMENTATION-ONLY supersede release (usb-hub-3s-v3
  v1.4, 2026-07-23), which intentionally ships fab bytes identical to its
  predecessor: declared identity is ASSERTED, not flagged — fab/, source/,
  3d/ MUST be byte-identical to the prior release (any differing, missing,
  or added file FAILS: a "docs-only" release that changes fab is lying),
  identical pdf/ is allowed, the order README + MANIFEST MUST differ from
  the prior's, and the audit==manifest + no-draft-marker checks still run.
  Default mode is byte-for-byte unchanged.
- The same script carries FIVE more supersede modes, each docs-only PLUS an
  exemption for exactly the artifact that legitimately moves, about which it
  then asserts something STRONGER than identity: `--bom-only-supersede` (whole
  rows REMOVED for refs NOT on the CPL, canon A-POP), `--cpl-only-supersede`
  (coordinate moves; a ROTATION/`Layer`/`Val`/`Package` change FAILs, canon
  A-POS), `--legible-bom-supersede` (only `Comment`+`MPN` move and the
  F-LEGIBLE verdict flips, ADR-0006), `--sourcing-supersede` (`MPN`+`LCSC`
  move together on the substituted rows, canon M8), and
  `--value-change-supersede … --designators R4,R5` (a part VALUE moves on
  already-placed parts: gerbers/drills identical after stripping only the
  plot's own timestamps, the CPL delta confined to `Val` cells, the BOM delta
  confined to the DECLARED refs, and the source REQUIRED to have moved with
  them — canon M3). Their normative statements live in ONE place, the
  `07_releases/contracts.md` supersede-mode sections; this list is an index,
  not a second home. Never gate a supersede with hand-written
  `--allow-identical` waivers instead: an assertion the gate makes beats a
  waiver a human writes.
- Fetch/stock classifiers must treat any UNRECOGNIZED failure as a blocking
  failure, never as an affirmative disposition (the NO-CAD incident,
  2026-07-20).
- Populate `jlc_lcsc_rotations.csv` ONLY from a fit of the BOARD footprint
  against JLC's cached model with an operator VERIFIED AGAINST PCBNEW ITSELF
  (RULE 2 in the table header) — never from `jlc_twin`'s `jlc_offset`, which
  is this pipeline's own output (canon M1; six rows were populated that way
  and were all 180 deg wrong). Record residual + next-best separation + date;
  a measurement that is not its own ROW does not exist (RULE 1). For a
  polarized or 2-pad collinear part the row ALSO needs a numbering-free
  channel (RULE 3 / canon A-POL) — a pad-NUMBER fit structurally cannot see a
  library that numbers the terminals the other way round, and a HIGH FIT
  MARGIN IS NOT CONFIDENCE (C2296/C2297: fit 180 at 17.7x, true offset 0).
- The fab BOM's LCSC code is the SOURCE's per-refdes code
  (`circuit.json supplier_part_numbers`), never a value+footprint match:
  `export_jlc_package.py` groups by (LCSC, footprint) so two distinct codes
  on one value+footprint stay on separate rows, and `bom_source_check.py`
  (canon M6 / policy_audit M-BOM) FAILS a merged/substituted/missing/
  dropped-vendored BOM (usb-hub-3s-v3 v1.1 shipped 25V caps for 50V,
  2026-07-23).
- Code identity is not enough: `bom_source_check.py` also runs a SEMANTIC
  value check (leg C) — for every R/C row it resolves the catalog value in
  order BOM MPN column -> vendored `02_parts/<MPN>/part.yaml` dir name ->
  vetted `references/lcsc_passives_ledger.yaml` (catalog-verified ONCE per
  code), decodes/compares OFFLINE, FAILING a VALUE-MISMATCH and FLAGGING a
  row no source resolves as UNVERIFIABLE-VALUE (never a silent pass). The
  ledger is load-bearing: real fab BOMs ship a BLANK MPN column and basic
  passives have no part.yaml, so without it the sealed usb-hub-3s-v3 v1.2
  R12 defect (C2933210 = 3.74k labeled 4.12k, 2026-07-23) is invisible —
  measured. A live catalog fetch, when in-env, is a stronger add-on but the
  offline check stands alone. The MPN grammar reads BOTH ceramic shapes: `<code><tolerance>` terminated (`...104KA01`) and `<code><tolerance><3-digit voltage>` (`0402CG101J500NT` = C0G, code 101, tol J, 50 V) — the second was refused until 2026-07-28 by a `(?![0-9])` lookahead, and the ledger carried three hand-written `value:` rows working around it, which is a PARSER BUG recorded as a part fact. A ledger row must never be the fix for something the grammar should read; cross-checked at 146/146 rows, 0 disagreements, by `t1_bom_source.t_legc_ledger_cross_check`.
  **Leg C prints `coverage leg C: N/M` and reports every COVERAGE-GAP by name
  (canon M-COVER).** It had two defects that CANCELLED, which is why neither
  was ever observed: `row_kind` classified by the whole leading-alpha run, so
  a descriptive refdes poisoned its entire row (`RS1` -> "RS", `CE1` -> "CE",
  and a row of `C_5V2` + `CL1` yields {"C","CL"} != {"C"}) — **87 of 673
  all-R/C rows fleet-wide were dropped while the tool printed PASS**; and
  `labeled_resistance("10mOhm")` returned 1.0e7 because the multiplier was
  UPPERCASED before lookup, so MILLI decoded as MEGA. The rows that would have
  exposed the second bug were exactly the rows the first bug dropped: RS1/RS2,
  the 10 mOhm shunts setting BOTH LM5116 buck current limits. `CE1` — the only
  electrolytic, the part that shipped REVERSED in cooksense v1.0/v1.1 — was
  dropped by the same mechanism. Now: 0/673 dropped, `m` is milli and `M` is
  mega (the rule `electrical_invariants.yaml`'s contract already stated), and
  an all-R/C row leg C still cannot classify is a **LEG-C-BLIND FAIL**, not a
  skip. Measured after: crow-recorder-central-v2 v1.5 leg C 13/25 -> 25/25;
  usb-hub-3s-v3 v1.8 23/26 -> 25/26, with RS1/RS2 now surfacing as
  UNVERIFIABLE-VALUE (C127692 needs a ledger entry) instead of vanishing.
