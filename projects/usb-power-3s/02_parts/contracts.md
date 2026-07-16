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
datasheet:
  doc_id: SNVSAI4
  revision: SNVSAI4F        # PIN IT — pinouts change between revisions
  url: https://www.ti.com/lit/ds/symlink/lm5145.pdf
  sha256: 9f2c...           # proves a re-download is the same document
  fetched: 2026-07-14
package: VQFN-20 RGY 3.5x4.5
footprint: power_board_v1:VQFN-20_3.5x4.5_P0.5_LM5145RGY
pins:                       # PHYSICAL PADS, read from the pinout figure
  1: EN
  20: VIN
  21: {name: EP, tie: GND, note: "thermal pad, must be grounded"}
limits: {vin_max: 75V, tj_max: 125C}
gotchas:
  - "EP is pad 21, not implicit — a generator that omits it floats the pad"
verified: "pin map cross-checked against datasheet fig 6-1 — 2026-07-14"
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
