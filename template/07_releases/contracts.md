# contract: 07_releases/

**Purpose** — one immutable directory per **fab order**. Answers, forever,
the only question that matters when a board comes back wrong: *what did we
actually send?*

**Mutability** — **IMMUTABLE**. A release directory is written once, at
order time, and never touched again. Not re-exported into. Not "refreshed".
Not tidied.

## Why this folder exists

One real project used a single mutable `fab/` directory and re-exported into
it ~15 times in a day. A KiCad version change renamed the inner-layer gerbers
(`.g2/.g3` → `.g1/.g2`), so stale KiCad-7 files sat mixed with KiCad-10 files
and a naive zip shipped **both**. The export script grew a stale-file warning
— a workaround for a structural problem. An immutable per-order directory
makes the failure impossible instead of detectable.

## Allowed

```
07_releases/
└── <version>-<YYYY-MM-DD>/         e.g. v4.10-2026-07-14
    ├── MANIFEST.txt                REQUIRED — see below
    ├── ORDER_README.md             REQUIRED — order options + human checklist
    ├── <board>_gerbers.zip         what goes to the PCB order page
    ├── bom.csv  cpl.csv            what goes to the assembly step
    ├── pdf/                        REQUIRED human-readable documentation
    │   ├── schematic.pdf           kicad-cli sch export pdf
    │   ├── pcb_layers.pdf          multipage: every copper layer + silk/mask,
    │   │                           Edge.Cuts on every page
    │   └── assembly_top.pdf        F.Fab + silk + sketch pads + refdes -
    │                               the hand-solder / rework / debug aid
    └── verification/               the reports that PASSED, as evidence
        ├── drc.json  audit.txt  stock_check.{txt,csv}
        ├── twin_report.csv          the JLC digital-twin verification (jlc_twin.py)
```

Nothing else. No working files, no "v2" of a release, no edits.

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
gates:        DRC 0/0 · parity clean · audit PASS · stock 55/55 verified
sha256:
  power_board_v1_gerbers.zip  f5d56393...
  bom.csv                     1a2b...
  cpl.csv                     3c4d...
not_assembled: J4,J5,J13 (THT USB-A, hand-solder) · F1 cartridge (user-supplied)
```

`git_sha` + `git_dirty: false` is the load-bearing pair: it means the release
can be reproduced byte-for-byte from source.

## Forbidden

- **Generators writing here.** They write `04_kicad/` and `06_build/` only.
- Editing any file in a release directory after it is written. If something
  is wrong, cut a NEW release; the wrong one is a historical fact.
- Releasing from a dirty working tree (`git_dirty: true`).
- A release whose gates did not pass. `verification/` holds the evidence;
  an empty or failing `verification/` means it is not a release.

## Validate

- directory name matches `^v[0-9]+(\.[0-9]+)*-[0-9]{4}-[0-9]{2}-[0-9]{2}$`
- `MANIFEST.txt` and `ORDER_README.md` present
- every `sha256` in the MANIFEST matches the file beside it
- `git_dirty: false`
- `git_sha` exists in this repo's history
- exactly one gerber zip; the BOM/CPL are siblings, **not inside** the zip
  (fab uploads them separately)
- `pdf/` holds schematic.pdf + pcb_layers.pdf + assembly_top.pdf, each listed
  in the MANIFEST sha256 table and visually verified via PNG before release
- `verification/` non-empty and its reports show passing gates
- `01_docs/CHANGELOG.md` has an entry whose `Released:` names this directory

## Repair

- Missing MANIFEST → reconstruct ONLY if the git SHA is certain; otherwise
  mark the directory `UNVERIFIED-` and cut a fresh release. A release you
  cannot trace is worse than no release.
- sha256 mismatch → the directory was mutated after the fact. It is no longer
  evidence of anything. Rename to `TAINTED-<name>` and re-release.
- Someone re-exported into an existing release → same as above. The whole
  point is that this is detectable.
