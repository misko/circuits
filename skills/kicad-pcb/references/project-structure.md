# Project structure: spec → fab

There is no industry standard. OSHWA covers licensing and documentation
completeness, not layout; the KiCad community agrees only on "name the repo
after the hardware, put the project in a subfolder, use `${KIPRJMOD}` for
local libs". So pick a PRINCIPLE, not a template.

**The principle: organize by who writes it and whether it may change.**
Source (humans/generators) → generated (tools, committed for review) →
build (tools, disposable) → releases (frozen forever).

Every structural failure on the SPF power board traced to mixing these: a
single mutable `fab/` re-exported ~15 times silently mixed KiCad 7 and
KiCad 10 gerbers, derived PNG/PDF/netlists churned git on every export, and
a repo-wide `**/*.csv` ignore nearly ate the part-decision record.

## The layout

```
board-name/
├── README.md               what it is, status, current release
├── docs/                   ← human truth, hand-written
│   ├── DESIGN.md           architecture + requirements
│   ├── DETAIL_DESIGN.md    the math (ripple, compensation, ampacity)
│   ├── decisions/          part choices + WHY; review dispositions;
│   │                       rejected candidates and the reason
│   └── CHECKLIST.md        revision gate
├── src/                    ← THE ONLY SOURCE OF TRUTH
│   ├── generate_schematic.py
│   ├── generate_board.py
│   ├── audit_board.py
│   ├── rules/              *.kicad_dru, netclass definitions
│   └── lib/                *.pretty, 3D models
├── parts/                  ← per-MPN facts + datasheet (see below)
├── kicad/                  ← GENERATED, committed for reviewable diffs
│   └── board.kicad_{pro,sch,pcb}
├── firmware/
├── build/                  ← gitignored, regenerate freely
│   ├── renders/  netlists/  drc/  cache/
└── releases/               ← IMMUTABLE, committed, one dir per fab order
    └── v4.10-2026-07-14/
        ├── ORDER_README.md   order options, checklists, hand-solder list
        ├── gerbers.zip  bom.csv  cpl.csv
        ├── MANIFEST.txt      git SHA + KiCad version + checksums
        └── verification/     the DRC/audit reports that passed
```

**`releases/` is the load-bearing part.** Each fab order is a frozen,
checksummed snapshot — never re-exported into, never edited. It makes the
stale-gerber failure structurally impossible and answers "what did we
actually send?" when a board comes back dead. Generators may write to
`kicad/` and `build/`; they must NEVER write to `releases/`.

Two rules that fall out:
- `.gitignore` derived artifacts, but NEVER decision records. Invert the
  common accident: `docs/decisions/` deserves the most protection, not the
  least — it is the only thing that cannot be regenerated.
- Committed-but-generated (`kicad/`) is deliberate: it makes generator bugs
  visible as diffs. Expect timestamp-only churn on re-export; `git checkout`
  the noise rather than committing it.

## Multi-board (product line)

```
product_v3/
├── docs/            system architecture, interface contracts
├── boards/          one full structure (above) per board
├── shared/lib/      footprints/symbols shared across boards
├── shared/rules/    house netclasses + fab floors (policy, not memory)
└── releases/        system-level BOM rollups
```
Do NOT symlink shared parts into boards — symlinks break the transferability
that makes a project openable in three years. Duplication is the price of
standalone, and it is worth paying.

## parts/ — datasheets and extracted facts

Three tiers with opposite requirements. Getting them confused is the
default mistake:

| Tier | Cost to obtain | Lifetime | Home |
|---|---|---|---|
| PDF blob | seconds | until vendor revises | global cache, NOT git |
| Extracted facts | expensive, error-prone | until revision changes | `parts/`, committed |
| Market data (stock/price) | seconds | hours | `build/cache/`, TTL'd |

**The download is not the expensive part — the extraction is.** Reading a
60-page datasheet to get physical pad numbers right is the costly,
error-prone work. Do it once, write it down, never re-read.

```
parts/
└── LM5145RGYR/
    ├── part.yaml        facts + provenance
    └── SNVSAI4F.pdf     committed; filename carries the REVISION
```

Flow: check global cache (`~/.cache/datasheets/<sha256>.pdf`) → download only
on miss → extract facts once → **when the part is actually USED, copy the PDF
from the cache into `parts/<MPN>/` and commit**. Rejected candidates stay
cache-only; their PDF is worthless but the REASON is not — record it in
`docs/decisions/`.

The two tiers do different jobs: the global cache is a speed optimization
(iterate over five candidates, download each once, forever); the project copy
is the archive of record (standalone, immune to URL rot). The `sha256` proves
they are the same document.

```yaml
mpn: LM5145RGYR
manufacturer: Texas Instruments
type: buck_controller          # explicit CLASS — a "10k NTC 3380K" coded as a
                               # plain 10k resistor shipped once; type: kills it
datasheet:
  doc_id: SNVSAI4
  revision: SNVSAI4F           # PIN IT — pinouts change between revisions
  url: https://www.ti.com/lit/ds/symlink/lm5145.pdf
  sha256: 9f2c...              # lets a re-download prove it is the same doc
  fetched: 2026-07-14
package: VQFN-20 RGY 3.5x4.5
pins:                          # physical PADS, from the datasheet's pinout figure
  1: EN
  20: VIN
  21: {name: EP, tie: GND, note: "thermal pad, must be grounded"}
limits: {vin_max: 75V, tj_max: 125C}
gotchas:
  - "EP is pad 21, not implicit — a generator that omits it floats the pad"
verified: "pin map cross-checked against datasheet fig 6-1 — 2026-07-14"
sourcing: {lcsc: C485912, alternates: [C2650259, C3188678]}
```

`part.yaml` must be complete enough that **the PDF is never needed for normal
work** — only for re-verification. That is what makes it context-efficient:
read 40 lines of YAML, not 60 pages.

Record polarity as a PART FACT where it exists: `pin 1: "-" blade` on an XT60
is exactly the fact whose absence shipped a reversed battery connector.

**Parity gate**: every BOM part has a `parts/` entry; every `parts/` entry is
in the BOM. Same spirit as `kicad-cli pcb drc --schematic-parity`. Catches a
used part with no datasheet on file, a stale entry for a swapped part
(ATtiny816 → ATtiny1616), and MPNs that were never orderable ("ATtiny816-SSN"
does not exist; the part is ATTINY816-SN).

Licensing: committing vendor PDFs is normal for private/internal repos and
legally gray for public ones. Decide before a design repo goes public.

## Migrating an existing board

Move, don't rewrite: generators → `src/`, design docs → `docs/`, the current
mutable `fab/` → a frozen `releases/<version>-<date>/` with a MANIFEST
pinning git SHA and tool versions, everything regenerable → `build/` and
gitignore it. The first release directory is the one that retroactively
answers "what did we send?".
