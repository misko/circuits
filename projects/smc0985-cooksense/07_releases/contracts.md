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


```
07_releases/
└── <version>-<YYYY-MM-DD>/         e.g. v4.10-2026-07-14
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
        ├── stock_check.{txt,csv}
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
        │                            model", NEVER "not placed" — CPL is population truth)
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
git_dirty:    false                   # MUST be false — never release from a dirty tree
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
not_assembled: J4,J5,J13 (THT USB-A, hand-solder) · F1 cartridge (user-supplied)
```

`git_sha` + `git_dirty: false` is the load-bearing pair for PROVENANCE: it says
where the release came from. The sha256 table over **every** file is the
load-bearing pair for INTEGRITY: it says the archive still is what was sent.
A release needs both — provenance without a complete archive is a promise you
can only cash by rebuilding the past.

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
- Releasing from a dirty working tree (`git_dirty: true`).
- A release whose gates did not pass. `verification/` holds the evidence;
  an empty or failing `verification/` means it is not a release.
- **A release carrying an unresolved P0 red-team finding.** A P0 blocks the
  release — fix and re-gate, or supersede; it may not seal open.
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
- `git_dirty: false`
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
  parity 0, audit PASS, policy_audit 0 FAIL, twin/pin/render reviews PASS
- red-team review present in `verification/`, both lenses'
  (topology/protection + layout/thermal) verdicts = ORDER, zero unresolved
  P0 (a P0 blocks the release); archived verbatim in `08_reviews/`
- the bare/modeled render pair for both sides (`render_{top,bottom}_bare.png`
  beside the twin renders) and `missing_models.txt` are present in
  `verification/`
- `01_docs/CHANGELOG.md` has an entry whose `Released:` names this directory

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
  false`; every sha256 in the table verifies against the file beside it,
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

Audit: `policy_audit.py <project>` runs M-REL mechanically; a release cut
with any policy FAIL is invalid (cut a new one after the fix or waiver).
