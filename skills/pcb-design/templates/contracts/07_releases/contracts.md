# contract: 07_releases/

**Purpose** — one immutable directory per **fab order**. Answers, forever,
the only question that matters when a board comes back wrong: *what did we
actually send?* — and, since 2026-07-20, the follow-up question:
*…and can I inspect or rebuild it without leaving this directory?*

**A release is a COMPLETE, SELF-CONTAINED ARCHIVE.** Not a pointer to a git
SHA. The `git_sha` proves provenance; it must not be the only way to see what
was built. A release that ships gerbers but not the `.kicad_sch`/`.kicad_pcb`
they came from cannot be inspected, diffed, or rebuilt without checking out a
commit, resolving a toolchain, and re-running a pipeline — which is exactly
what nobody can do three years later when a board comes back wrong. The
archive must stand alone.

**Mutability** — **IMMUTABLE**. A release directory is written once, at
order time, and never touched again. Not re-exported into. Not "refreshed".
Not tidied. ONE exception: when a later release supersedes this one, a
single new file `SUPERSEDED.md` may be ADDED (never editing anything that
exists) naming the successor directory and the one-line reason.

**Immutability is UNCHANGED by the completeness requirement below.** The
self-contained-archive structure applies to **NEW** releases, from
2026-07-20 forward. Existing sealed releases are **NOT** retro-filled, not
reorganized into the new layout, and not "upgraded" — they are historical
facts about what was sent, and a directory that gains files after the fact
is no longer evidence of anything. A board that wants the fuller archive
gets a **NEW version**, and the old one gains only its `SUPERSEDED.md`
pointer. These two rules do not conflict: completeness governs what you
write at seal time; immutability governs everything after.

## Why this folder exists

One real project used a single mutable `fab/` directory and re-exported into
it ~15 times in a day. A KiCad version change renamed the inner-layer gerbers
(`.g2/.g3` → `.g1/.g2`), so stale KiCad-7 files sat mixed with KiCad-10 files
and a naive zip shipped **both**. The export script grew a stale-file warning
— a workaround for a structural problem. An immutable per-order directory
makes the failure impossible instead of detectable.

## Allowed — the complete archive (REQUIRED for new releases)

Machine-readable patterns (contracts_audit; the tree below is the human view):

| Pattern | What |
|---|---|
| `contracts.md` | this file |
| `<version>-<date>/MANIFEST.txt` `<version>-<date>/ORDER_README.md` `<version>-<date>/SUPERSEDED.md` | release root documents |
| `<version>-<date>/fab/**` | gerber zip, drill, bom.csv, cpl.csv |
| `<version>-<date>/pdf/**` | schematic (tscircuit's own render), pcb_layers, assembly |
| `<version>-<date>/source/**` | the EXACT source artifacts incl. fp-lib-table + vendored `.pretty` (V-REL-FPLIB, usb-hub-3s 2026-07-21: without them a standalone archive re-measure raises lib_footprint_issues — the archive must re-measure DRC clean) |
| `<version>-<date>/3d/**` | STEP/GLTF |
| `<version>-<date>/verification/**` | every gate's evidence |


### The directory NAME is how a machine tells the boards apart

Two shapes ship: bare `v<N>[.<N>…]-<YYYY-MM-DD>` and, when a project builds
more than one board, per-board `<board>-v<N>[.<N>…]-<YYYY-MM-DD>`
(`cooksense-v1.4-2026-07-26`). **`<board>` MUST be the `04_kicad` board stem**
(separator style and case are free: `crow_recorder_central_v2` and
`crow-recorder-central-v2` are the same board). This is not cosmetic — it is
the only thing that says which board a sealed archive belongs to.

- **A MULTI-BOARD project MUST use the per-board form for every release**,
  including the first. A bare name in a multi-board `07_releases/` is
  unattributable and every gate that resolves "this board's latest release"
  REFUSES it (`release_index.py`, canon M-COVER) rather than guessing.
- **Versions order NUMERICALLY PER COMPONENT**: `v1.10 > v1.9 > v1.2`. Never
  sort these names as text, and never re-implement the ordering — import
  `jlcpcb-fab/scripts/release_index.py`, which is its one home.
- **"The latest release" means the newest of THIS BOARD's series**, never the
  last directory in `07_releases/`. `smc0985-cooksense` holds `cooksense-*`
  and `interposer-*`; `interposer-…` sorts last, and a gate taking `rels[-1]`
  graded the interposer while reporting on cooksense, then demanded
  `SUPERSEDED.md` on the live `cooksense-v1.4` and blocked its successor
  (2026-07-27).
- `SUPERSEDED.md` is a WITHIN-SERIES claim: it is owed by this board's earlier
  releases, never by a sibling board's.

```
07_releases/
└── [<board>-]<version>-<YYYY-MM-DD>/   e.g. v4.10-2026-07-14,
    │                                   cooksense-v1.4-2026-07-26
    ├── MANIFEST.txt                REQUIRED — sha256 of EVERY file below
    ├── ORDER_README.md             REQUIRED — order options, hand-solder list,
    │                               first-power ritual
    ├── fab/                        REQUIRED — the JLCPCB order set, exactly as uploaded
    │   ├── <board>_gerbers.zip     the PCB order page
    │   ├── <board>.drl (+ NPTH)    drill files (also inside the zip; kept loose
    │   │                           so the archive is readable without unzipping)
    │   ├── bom.csv                 JLC format — assembly step
    │   └── cpl.csv                 JLC format — assembly step
    ├── pdf/                        REQUIRED — the human-readable board documents
    │   ├── schematic.pdf           for a tscircuit board this is tscircuit's OWN
    │   │                           render (03_tscircuit/build/schematic.pdf),
    │   │                           NOT a KiCad re-render (ADR-0002)
    │   ├── pcb_layers.pdf
    │   └── assembly.pdf
    ├── source/                     REQUIRED — the EXACT artifacts the fab files
    │   │                           came from, so the release is inspectable and
    │   │                           reproducible STANDALONE
    │   ├── <board>.kicad_sch       the sealed schematic
    │   ├── <board>.kicad_pcb       the sealed board — what the gerbers plotted from
    │   ├── <board>.tsx             the AUTHORING source — REQUIRED on a
    │   │                           tscircuit board, absent on a hand-KiCad
    │   │                           one (where .kicad_sch IS the authoring source)
    │   └── <board>.net             the exported netlist (the parity reference)
    ├── 3d/                         REQUIRED WHERE AVAILABLE — mechanical fit
    │   ├── <board>.step            for enclosure/clearance checks
    │   └── <board>.gltf            (either or both; note absence in the MANIFEST)
    └── verification/               REQUIRED — all evidence, the reports that PASSED
        ├── drc.json                DRC 0/0/0 (--severity-all --refill-zones
        │                           --schematic-parity)
        ├── erc.json                ERC 0 errors
        ├── audit.txt               placement/pad invariant gate
        ├── assembly_coverage.txt    REQUIRED — A-POP: {board} − {CPL} equals
        │                            assembly.yaml's not_assembled set, plus
        │                            the per-side placement histogram
        │                            (`assembly_coverage.py`)
        ├── stock_check.json         REQUIRED — A-STOCK: the MACHINE-READABLE
        │                            stock evidence, with an EXPLICIT
        │                            `verdict` (`jlc_stock_check.py --json`).
        │                            The fleet shipped three incompatible
        │                            text formats and one release with ZERO
        │                            verdict lines; this is the one shape the
        │                            gate grades. A missing/unparseable
        │                            verdict is a FAIL, never a skip
        ├── stock_check.{txt,csv}
        ├── bom_source_check.txt     fab/bom.csv LCSC == source per refdes
        │                            (bom_source_check.py / policy_audit M-BOM):
        │                            no merged/substituted/missing/dropped code —
        │                            the v1.1 25V-for-50V-cap defect (canon M6)
        ├── bom_legibility.txt       REQUIRED — canon F-LEGIBLE (ADR-0006): the
        │                            BOM graded AS JLC PARSES IT, not as we
        │                            wrote it (`bom_legibility_check.py
        │                            <release_dir>`). F-MPN every coded row
        │                            carries BOTH MPN and LCSC, resolved from
        │                            02_parts/<MPN>/part.yaml then the vetted
        │                            passives ledger, the two agreeing;
        │                            F-WORDS the Comment is a human-readable
        │                            value, never an LCSC code or a `simple_*`
        │                            placeholder; F-ENCODE the file decodes
        │                            identically under UTF-8 and cp936.
        │                            bom_source_check asks "is this value
        │                            RIGHT?"; this asks "can the recipient READ
        │                            it?" — one BOM was uploaded and its parts
        │                            "were not being picked up by their web
        │                            processing" while every semantic gate was
        │                            green (canon M1)
        ├── bom_echo_gate.txt        REQUIRED where the order has been placed —
        │                            canon F-ECHO, the human-gated half. Written
        │                            by `export_jlc_package.py` beside A-POL's
        │                            rotation_human_gate.txt: the (code, value,
        │                            refs) triples to compare against JLC's OWN
        │                            resolved table after upload. A code JLC
        │                            redirects is a SUBSTITUTION and a FINDING
        │                            (C82317 -> C131025 on a shipped board;
        │                            nothing in this repo could see it)
        ├── twin_report.{csv,txt}   the JLC digital-twin verification (jlc_twin.py)
        ├── twin_{top,bottom,iso_nw,iso_se,edge_west,edge_east}.png
        │                            six renders of the board with JLC's part
        │                            bodies - top/bottom, two isometrics, two
        │                            edge profiles (component heights)
        ├── render_{top,bottom}_bare.png
        │                            the no-components truth view per side
        │                            (kicad-cli Cu+Mask+SilkS+Edge, rasterized) —
        │                            paired with the modeled twin renders above
        ├── missing_models.txt       every CPL ref with no attached 3D body in the
        │                            modeled render (a bodiless footprint means "no
        │                            model", NEVER "not placed" — CPL is population truth).
        │                            GENERATED by jlc_twin's NO-BODY pass (canon
        │                            A-BODY) and carrying its `bodies mounted: N/M`
        │                            header — NEVER hand-authored: v1.5 of one board
        │                            shipped a hand-written copy claiming zero while
        │                            7 of 108 placements rendered nothing
        ├── pin_review.md            fresh-context pin review verdicts (pin-review-protocol)
        ├── render_review.md         fresh-eyes render review verdicts
        ├── redteam_topology.md      RED-TEAM release review, topology/protection/
        │                            ratings lens — ORDER verdict; verbatim copy of
        │                            the 08_reviews/ archive (a P0 blocks the release)
        ├── redteam_layout.md        RED-TEAM release review, layout/thermal/
        │                            power-integrity lens — ORDER verdict; verbatim
        │                            copy of the 08_reviews/ archive
        ├── policy_audit.md          zero FAIL, waivers evidence-backed
        └── parity.md                node-for-node netlist parity vs the source
```

Nothing else. No working files, no "v2" of a release, no edits.

**The completeness test** — a release passes only if someone with this
directory, KiCad, and no network can: open the board, read the schematic,
check mechanical fit, see every gate's evidence, and re-plot the gerbers.
`source/` is what makes that true; `git_sha` only proves where it came from.

**Where the files come from.** `source/` is a COPY of the sealed `04_kicad/`
board + schematic, the `03_tscircuit/src/<board>.tsx`, and the exported
netlist — copied at seal time, never symlinked (a symlink into a mutable
folder defeats the entire archive). For a tscircuit-authored board the
schematic PDF is copied from `03_tscircuit/build/schematic.pdf`.

## Structure: `MANIFEST.txt`

The provenance that makes the release auditable:

```
board:        power_board_v1
version:      v4.10
ordered:      2026-07-14
git_sha:      a5e7ca7                 # the EXACT commit these came from
git_dirty:    false                   # scope: projects/<board>/ + skills/ — never seal with these inputs dirty
kicad:        10.0.4
tools:        KRT@<sha>, python 3.12
fab:          JLCPCB, 4 layer, advanced small-via option (0.25/0.15 vias)
quantity:     5
gates:        DRC 0/0/0 · netlist parity 0 · audit PASS · ERC 0 err ·
              twin PASS · pin_review PASS · policy_audit 0 FAIL ·
              redteam ORDER/ORDER, 0 open P0 · stock 55/55 verified
3d:           step present, gltf absent (no exporter for this board)
sha256:       # EVERY file in the release, not just the fab set
  fab/power_board_v1_gerbers.zip   f5d56393...
  fab/power_board_v1.drl           9e01...
  fab/bom.csv                      1a2b...
  fab/cpl.csv                      3c4d...
  pdf/schematic.pdf                7f8e...
  pdf/pcb_layers.pdf               2b3c...
  pdf/assembly.pdf                 5d6e...
  source/power_board_v1.kicad_sch  aa11...
  source/power_board_v1.kicad_pcb  bb22...
  source/power_board_v1.tsx        cc33...
  source/power_board_v1.net        dd44...
  3d/power_board_v1.step           ee55...
  verification/drc.json            ff66...
  ... every remaining verification/ file
assembly:     JLC standard, top side only, 5 boards, fiducials: none (JLC rail)
consigned:    U1 C6938291 (XU316) — MSL 3, 168h floor life (ds v2.0.0 s.15.2)
msl:          U1 MSL-3 (bake if floor life exceeded); no other exposed-pad part
not_assembled: J4,J5,J13 (THT USB-A, not_in_catalog) · F1 element (user_supplied)
```

### `not_assembled:` is a REQUIRED, GENERATED block

**Required** whenever the board has any unpopulated non-exempt part,
**GENERATED from `03_src/rules/assembly.yaml`** — never hand-written — and a
BARE REFDES LIST, never prose. Reasons belong in `assembly.yaml`; a line
carrying free text is reported as UNGRADEABLE and cross-checked against
nothing, because scraping refdes out of prose accuses the wrong parts
(usb-hub-3s-v3 v1.4: 50 tokens, 44 of them English words, and its four real
refdes sit in a clause saying they *are* populated). It was a
prose sentence in two places and the two drifted: cooksense v1.1's MANIFEST
declared 12 refs not_assembled while its own CPL told JLC to place all 12, and
a 13th (J_TC) was declared nowhere. `assembly_coverage.py` (A-POP) FAILs both
the absence and any disagreement with `assembly.yaml`.

Each ref traces to an `assembly.yaml` entry whose `reason:` is the CLOSED
vocabulary — `not_in_catalog` · `user_supplied` · `dnp_by_design` ·
`mechanical` · `test_point` — with a DATED `evidence:` measurement (the
catalog query and its result) and a `disposition:`. `consign` is NOT a
population reason: a consigned part is POPULATED, stays ON the CPL, and
belongs in the `consigned:` MANIFEST line above (crow-recorder-central-v2 v1.3
declared its placed U1 "not_assembled" that way). The `msl:` line is REQUIRED
for every consigned part and every exposed-pad package — JLC cannot bake what
they are not told is moisture-sensitive (crow-recorder-central v1.0 shipped a
consigned MSL-3 XU316 with zero MSL text while its own part.yaml recorded
"MSL 3, 168h floor life").

`git_sha` + `git_dirty: false` is the load-bearing pair for PROVENANCE: it says
where the release came from. The sha256 table over **every** file is the
load-bearing pair for INTEGRITY: it says the archive still is what was sent.
A release needs both — provenance without a complete archive is a promise you
can only cash by rebuilding the past.

### `git_dirty` — scoped to the release's INPUTS, not the whole repo

`git_dirty` records whether the artifacts this release regenerates from were
committed at `git_sha`. Those inputs are exactly the board's own project
subtree and the shared skill backend — nothing else feeds the fab set:

    the release is CLEAN  iff  `git status --porcelain -- projects/<board>/ skills/`  is empty

A dirty SIBLING project (a concurrently-building board) has ZERO bearing on
THIS release's reproducibility and MUST NOT block the seal. A dirty `skills/`
backend, or a dirty / untracked file inside this board's own subtree, DOES
block — those are the inputs the gerbers are reproducible from. (This replaced
a repo-wide `git status --porcelain` that blocked a seal on unrelated sibling
dirt, forcing pause-coordination between independent boards — 2026-07-23.) The
board's own `07_releases/`, `06_build/`, `01_docs/` sit inside the in-scope
subtree and are checked: the seal commits the board's own artifacts first, so
at `git_sha` the whole subtree is committed-clean; only OTHER boards are exempt.

The MANIFEST records the flag WITH its scope noted, so no reader mistakes it
for a whole-repo claim:

    git_dirty:    false                   # scope: projects/<board>/ + skills/

**Helper (declared here):** `skills/kicad-pcb/scripts/release_git_dirty.py
<board>` computes this scoped flag, prints the exact MANIFEST line above, and
exits non-zero when dirty — the seal calls it and gates on the exit code
rather than eyeballing `git status`.

## Seal procedure (normative — the 2-commit seal)

The ONE home for HOW a release is cut; SKILL.md stage 7, the revision
CHECKLIST, and ORCHESTRATION_STATE.md all point HERE (single-homed
2026-07-23 — before that the dance lived only in one board's journal and
was re-derived per seal). The staging boundary carries the immutability
rule: the release directory is MUTABLE STAGING until the seal commit
lands; **immutability begins the moment the seal commit exists.**

0. **Stage.** Write the complete archive into `07_releases/<ver>-<date>/`.
   Run EVERY gate and review against this staging dir — DRC/ERC/parity,
   twin, policy_audit, freshness, semantic M-BOM, and the review lenses
   (breadth per canon "Verification scoping": initial release = full
   battery; fix-pass = diff-verified delta + targeted confirms + ONE
   integrated fresh-context lens). **A finding here costs an edit; the
   same finding after the seal costs a supersede** (3 of one family's 4
   seals died to post-ceremony reviews, mean seal lifetime 5.6h,
   2026-07-23). Do not proceed with any open P0 or FAIL.
1. **Source commit S.** Commit every INPUT: the board's own subtree and
   any `skills/` changes. `release_git_dirty.py <board>` must report
   clean apart from the staged release dir itself (the release dir is
   OUTPUT — the seal commit will carry it; any OTHER dirt blocks). Strip
   kicad-cli droppings LAST — any board-open regenerates gitignored
   `*.kicad_prl` / stray `*.kicad_pcb.kicad_pro` files, so the
   `git check-ignore` sweep is the FINAL pre-seal check (bit two boards,
   2026-07-23).
2. **Stamp.** Write `git_sha: S`, `git_dirty: false` into `MANIFEST.txt`
   and (re)compute its sha256 table over every file (MANIFEST itself is
   the one exclusion — it cannot hash itself). THEN re-run `policy_audit`
   M-REL and `release_freshness_check.py` so the shipped audit grades the
   REAL manifest (the v1.2 audit-vs-manifest disagreement class).
   `release_freshness_check.py` also gates MANIFEST SELF-CONSISTENCY
   (M-CONS, check d): every count the MANIFEST's gate summary states must
   match the shipped machine evidence (ERC errors/warnings vs the
   policy_audit S-ERC row and erc.json; bom_source_check line count vs
   fab/bom.csv data rows), and every `07_releases/<dir>/` path embedded in
   verification evidence must name THIS release's directory (or an
   existing sibling — diffing a real predecessor is legitimate). Re-run it
   after the stamp — the crow-recorder-central-v2 v1.0 class (2026-07-23)
   shipped prose counts and a staging path no gate compared. The gate's
   version key covers board-prefixed release names (`<board>-v1.x-<date>`)
   — before 2026-07-24 those silently skipped the stale-artifact check.
3. **Seal commit.** A commit that adds ONLY the release directory, the
   `01_docs/CHANGELOG.md` entry, and `SUPERSEDED.md` on the predecessor.
   From this commit on the directory is IMMUTABLE.
4. **Refresh the beacon — the seal is not complete without it (canon
   M-BEACON).** OVERWRITE `01_docs/STATUS*.md` (the board's own, on a
   multi-board project) so that `step:` names the release just created,
   `state:` is `done`, and `updated:` is now; then run
   `status_beacon_check.py <project>` and require exit 0. The beacon is the
   coordinator's only between-gates eye and it does not go blank when it goes
   stale — it keeps reporting the PREVIOUS release as live, with a plausible
   `sealed / done`. Measured 2026-07-27, before this step existed: EVERY
   beacon in the fleet named a superseded release (13 M-BEACON findings across
   4 of 6 boards), and one had a whole second frame APPENDED into a file this
   contract says is OVERWRITTEN. This step is where that class is closed —
   the gate catches drift AFTER the fact; the ritual is what prevents it.
   It comes AFTER the seal commit deliberately: the release directory it must
   name does not exist until then. Commit the refreshed beacon with the next
   working commit (it is `01_docs/` working state, never part of the sealed
   archive, and it must NEVER be added to the release directory).

**Docs-only supersede mode.** When the new release changes ONLY
documentation (dispositions, README, MANIFEST — no fab/source/3d delta),
gate the staging with `release_freshness_check.py <release_dir>
--docs-only-supersede <prior-release-dir>`: fab/, source/ and 3d/ must be
BYTE-IDENTICAL to the prior release (any differing/missing/added file
FAILS — it is not docs-only), identical pdf/ is allowed, and the order
README + MANIFEST must byte-differ (otherwise the release supersedes
nothing). The audit/manifest-agreement and draft-marker checks still run.
Never waive fab-identical files one-by-one for this case — the mode
asserts the identity instead of flagging it.

**BOM-only supersede mode.** The one case docs-only mode correctly refuses:
the copper is untouched but the ASSEMBLY BOM must lose rows, because canon
A-POP requires an unplaced part to LEAVE the BOM rather than sit on it
uncoded. Gate it with `--bom-only-supersede <prior-release-dir>`, which is
docs-only PLUS an exemption for exactly one file, `fab/bom.csv` — and only
because the mode then asserts something STRONGER about that file than
identity: the delta must be **whole rows REMOVED, for designators that are
NOT on the CPL**. A row ADDED, a row EDITED (a changed value/footprint/LCSC
is a different board), or a removal for a designator still on the CPL all
FAIL. Everything else in `fab/`, and all of `source/` and `3d/`, must still
be byte-identical. Motivating case: crow-mic-pod-v2 v1.0 (2026-07-25) shipped
MK1 with its MPN *and* LCSC columns both empty and J1 at stock 0, neither on
the CPL — the upload stalls at JLC's BOM/CPL matcher, and fixing it changes
`fab/`, so a plain docs-only claim would have been a lie. Do NOT reach for
`--allow-identical` waivers here; the point is to assert the shape of the
change, not to excuse it.

**LEGIBLE-BOM supersede mode.** The case all three modes above correctly
refuse. Canon **F-LEGIBLE** (ADR-0006): the copper is untouched but
`fab/bom.csv` must be rewritten so the RECIPIENT can PARSE it — MPN filled
from the part's own `02_parts/<MPN>/part.yaml` (then the vetted passives
ledger), a Comment that is a human-readable value instead of an LCSC code or
a `simple_*` generator placeholder, and a UTF-8 byte-order-mark so a cp936
reader cannot render `Ω` as `惟`. That EDITS every row, so docs-only
refuses (fab/ changed) and BOM-only refuses too — rightly, since it FAILs on
any edited row for the A-POP defect IT guards. Gate it with
`--legible-bom-supersede <prior-release-dir>`: docs-only PLUS an exemption
for exactly `fab/bom.csv`, and the mode then asserts something STRONGER than
identity about it — **every row's designator group, `Footprint` and `LCSC`
UNCHANGED; no row added or removed; no MPN blanked; only `Comment` and `MPN`
may move** — and, taken from the F-LEGIBLE gate itself rather than
re-implemented, **this release's BOM must PASS `bom_legibility_check.py` and
the prior one must FAIL it**. A changed `LCSC` is a SUBSTITUTION (the
C82317 → C131025 class) and FAILs; a changed `Footprint` is a different
board and FAILs. Motivating case: crow-recorder-central-v2 v1.5 (2026-07-27)
— its BOM was uploaded to JLCPCB and the parts "were not being picked up by
their web processing".

**CPL-only supersede mode.** When the new release changes ONLY
`fab/cpl.csv` — a PLACEMENT fix — gate the staging with
`release_freshness_check.py <release_dir> --cpl-only-supersede
<prior-release-dir>`: everything else in `fab/`, and all of `source/` and
`3d/`, must be BYTE-IDENTICAL, and the CPL delta must be coordinate moves
and/or whole rows REMOVED for parts that are no longer populated. A
ROTATION, `Layer`, `Val` or `Package` change FAILs, and so does an ADDED
row, and so does a CPL that did not change at all (that is a docs-only
supersede). This exists because a wrong CPL coordinate is the one defect
that is 100% assembly data and 0% copper: crow-recorder-central-v2 v1.4
shipped its only USB-C 1.3025mm off its own pads (canon A-POS — the
exporter emitted KiCad's footprint ANCHOR, not JLC's pad-array datum),
and fixing it changes exactly one file. Keeping rotation OUT of this mode
is load-bearing: the v1.3 -> v1.4 supersede was ALSO a CPL-only change and
it moved seven ROTATIONS, so without the split the two defect classes
would share one unaccountable channel.

Deviations that force rework (both happened, 2026-07-23): regenerating ANY
artifact after S makes S stale — return to step 1 with a new S. Committing
the staged release INSIDE the source commit (usb-hub-3s-v3 v1.3 gate-ii)
leaves MANIFEST pointing at an older sha and forces a follow-up re-stamp
commit + `policy_audit --skip-drc` re-clear — legal but three commits
instead of two; follow the order above. The orchestrator's INDEPENDENT
re-measure after sealing is ORCHESTRATION_STATE.md "Seal-verify protocol".

## Fix-claim evidence rule

A release whose MANIFEST claims a FIX or verification refresh relative to a
prior release must carry, in `verification/`, the MEASUREMENT that proves
that specific claim (numbers + method + what was measured), by a method
able to FALSIFY it independently of whoever produced the fix (render
before/after diff, landmark-calibrated pixels, or a fresh-context agent
confirming the specific claim). A refresh once shipped claiming a model
re-seated when the nudge had moved it 90deg the wrong way — checker and
checked shared a method.

## Forbidden

- **Generators writing here.** They write `04_kicad/` and `06_build/` only.
- Editing any file in a release directory after it is written. If something
  is wrong, cut a NEW release; the wrong one is a historical fact.
- Releasing with dirty INPUTS (`git_dirty: true`) — a dirty `skills/` backend
  or a dirty/untracked file in the board's own subtree. Scope is
  `projects/<board>/ + skills/`, NOT the whole repo: a dirty SIBLING project
  does not block (`release_git_dirty.py <board>` computes it).
- A release whose gates did not pass. `verification/` holds the evidence;
  an empty or failing `verification/` means it is not a release.
- **A release carrying an unresolved P0 red-team finding.** A P0 blocks the
  release — fix and re-gate, or supersede; it may not seal open.
- **A CPL row whose BOM line has a BLANK LCSC** (canon A-POP). JLC is being
  told to place a part it has no code to source. An uncoded line is a FAILED
  sourcing decision: it needs an `assembly.yaml` entry with a
  closed-vocabulary `reason:` and dated `evidence:`, AND the part must leave
  the CPL (`exclude_from_pos_files` on the board).
- **Sealing against stock evidence that does not PASS** (canon A-STOCK), or
  against evidence with no parseable verdict at all. Five sealed releases in
  this fleet shipped a `FAIL:` last line, one with the board's own CPU at
  stock 0. Fix the sourcing or record the `sourcing_plan:` entry with the
  measured number and its date.
- **A release that outsources its own contents to git.** No `source/` means
  no release — "it's at that SHA" is not an archive. Likewise no symlinks
  into `04_kicad/` or `03_tscircuit/`; those folders keep moving.
- **Retro-filling a sealed release** to satisfy the completeness structure.
  Cut a new version with a `SUPERSEDED.md` on the old one instead.

## Validate

- directory name matches `^v[0-9]+(\.[0-9]+)*-[0-9]{4}-[0-9]{2}-[0-9]{2}$`
- `MANIFEST.txt` and `ORDER_README.md` present
- **every file in the directory appears in the MANIFEST sha256 table, and
  every sha256 matches** — both directions. A file not in the table is
  unaccounted-for; a table entry with no file is a missing artifact.
  (`MANIFEST.txt` itself is the one exclusion — it cannot hash itself.)
- `git_dirty: false` — scope `projects/<board>/ + skills/` (a dirty sibling
  project does not count); compute with `release_git_dirty.py <board>`
- `git_sha` exists in this repo's history
- **`fab/`, `pdf/`, `source/`, `verification/` all present and non-empty**
  (new releases); `3d/` present or its absence explained in the MANIFEST
- exactly one gerber zip in `fab/`; the BOM/CPL are siblings, **not inside**
  the zip (fab uploads them separately)
- `source/` opens: `kicad-cli pcb drc source/<board>.kicad_pcb` runs, and the
  board it loads is the one the gerbers were plotted from — re-plot from
  `source/` and the gerbers match
- `source/<board>.net` is node-for-node identical to the netlist the sealed
  `04_kicad` board produced at `git_sha`
- `verification/` reports show passing gates: DRC 0/0/0, ERC 0 errors,
  parity 0, audit PASS, policy_audit 0 FAIL (incl. M-BOM: fab BOM LCSC ==
  source per refdes), twin/pin/render reviews PASS
- **the ASSEMBLY battery on THIS release's own bytes (canon A-POP/A-STOCK —
  PCBA is the deliverable):**
  - `assembly_coverage.py <release_dir>` exits 0 — `{board} − {CPL}` equals
    `assembly.yaml`'s `not_assembled:` set, no blank-LCSC ref on the CPL, and
    the MANIFEST `not_assembled:` line matches `assembly.yaml`
  - `release_freshness_check.py <release_dir>` exits 0 including check (e):
    the shipped stock evidence carries a PARSEABLE PASS verdict and every
    coded, placed line clears `qty x build_quantity` or names a
    `sourcing_plan:` entry with its measured stock and date
  - `bom_legibility_check.py <release_dir>` exits 0 (canon F-LEGIBLE) — every
    coded row carries an MPN that AGREES with its dossier, every Comment is a
    human-readable value, and the file decodes identically under UTF-8 and
    cp936. **Adopted-forward**: 25 of the 26 releases sealed before ADR-0006
    fail this and are NOT retro-fixed (07_releases immutability). A board that
    needs a legible BOM gets a NEW version; `fleet_regrade.py` says which
- **the ORDER-TIME F-ECHO ritual (canon F-LEGIBLE, human-gated).** The
  ORDER_README carries it beside the A-POL rotation-preview gate: after
  uploading `fab/bom.csv`, save JLC's OWN resolved/matched part table out of
  their UI and run `bom_legibility_check.py fab/bom.csv --echo SAVED.csv`
  against `bom_echo_gate.txt`. A code JLC redirects is a SUBSTITUTION and a
  FINDING to adjudicate BEFORE paying, never after. There is deliberately no
  JLCPCB API integration (ADR-0006): it would require handing over
  credentials, the same line already drawn on the Mouser/Nexar APIs
- red-team review present in `verification/`, both lenses'
  (topology/protection + layout/thermal) verdicts = ORDER, zero unresolved
  P0 (a P0 blocks the release); archived verbatim in `08_reviews/`
- the bare/modeled render pair for both sides (`render_{top,bottom}_bare.png`
  beside the twin renders) and `missing_models.txt` are present in
  `verification/`; `missing_models.txt` carries the `GENERATED by jlc_twin`
  provenance line and a `bodies mounted: N/M` header with **N == M** (canon
  A-BODY). A missing or unparseable counter is a FAIL, not a skip
- `01_docs/CHANGELOG.md` has an entry whose `Released:` names this directory
- while this directory is the LIVE release (no `SUPERSEDED.md`), the board's
  `01_docs/STATUS*.md` beacon NAMES it and is not older than it —
  `status_beacon_check.py <project>` exits 0 (canon M-BEACON). The beacon is
  working state, not release content: it is refreshed by seal step 4 and never
  written into this directory

## Repair

- Missing MANIFEST → reconstruct ONLY if the git SHA is certain; otherwise
  mark the directory `UNVERIFIED-` and cut a fresh release. A release you
  cannot trace is worse than no release.
- sha256 mismatch → the directory was mutated after the fact. It is no longer
  evidence of anything. Rename to `TAINTED-<name>` and re-release.
- Someone re-exported into an existing release → same as above. The whole
  point is that this is detectable.
- **A sealed release predating the complete-archive rule** (no `source/`,
  no `3d/`, fab files loose at the root) → **leave it exactly as it is.**
  It is a valid historical release under the contract in force when it was
  sealed. Do NOT backfill. If the board needs the fuller archive, cut a new
  version from the current source and add `SUPERSEDED.md` to the old one
  naming it. Retro-editing would destroy the one property that makes any of
  these directories worth keeping.

## Compliance audit (design-policies.md IDs)

This folder answers **M5** (M-REL) and hosts the evidence for everything:

- MANIFEST `git_sha` is an EXACT commit hash that exists; `git_dirty:
  false` (scoped to `projects/<board>/ + skills/` via
  `release_git_dirty.py`, NOT the whole repo — a dirty sibling project does
  not block); every sha256 in the table verifies against the file beside it,
  and every file in the directory is in the table.
- The archive is SELF-CONTAINED: `fab/`, `pdf/`, `source/`, `verification/`
  present; `source/` holds the exact `.kicad_sch` / `.kicad_pcb` / `.tsx` /
  `.net` the fab set was produced from.
- `01_docs/CHANGELOG.md` has an entry naming this directory.
- Every superseded sibling carries `SUPERSEDED.md`.
- Any fix-claim in the MANIFEST has its falsifiable measurement IN
  `verification/` (checker and claimed-fixer must not share a method).
- `verification/policy_audit.md` ships in the bundle: zero FAIL, waivers
  evidence-backed, HUMAN items (S5/S6/S7, M1) carrying reviewer verdicts.

Audit: `policy_audit.py <project> [--board <04_kicad stem>]` runs M-REL
mechanically; a release cut with any policy FAIL is invalid (cut a new one
after the fix or waiver). **On a multi-board project `--board` is REQUIRED to
grade the second board** — the audit grades one board per run (the report's
header line names it), and M-REL/M-BOM/A-POP/A-BODY resolve the release from
THAT board's series.
