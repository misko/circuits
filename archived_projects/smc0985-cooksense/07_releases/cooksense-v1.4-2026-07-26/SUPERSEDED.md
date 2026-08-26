# SUPERSEDED by cooksense-v1.5-2026-07-27 — THIS RELEASE'S BOM CANNOT BE ORDERED

## The board is unchanged and it is CORRECT

**Nothing is wrong with this board and nothing is wrong with these gerbers.**
`source/cooksense.kicad_pcb` here is md5-identical
(`420445b5141dd1111eccab038c68511b`) to v1.5's, to v1.3's and to `04_kicad/`'s.
v1.5 re-plotted from that same file and 11 of 13 gerber/drill members came out
GEOMETRICALLY IDENTICAL under an aperture-resolved comparator; the two that
differ do so by 3 duplicate / sub-nanometre-collinear pour vertices out of
29 587, and **poured copper AREA is equal to six decimal places on all four
copper layers**. `fab/cpl.csv` and `fab/rotation_human_gate.txt` are
byte-identical between the two releases. See
`cooksense-v1.5-2026-07-27/verification/copper_did_not_move.md`.

- 226 footprints, 3925 tracks, **1047 vias**, all 0.25/0.15 mm
- **DRC 0 violations / 0 unconnected / 0 schematic parity** — re-run on this
  board at the v1.5 seal and still 0/0/0
- **H4 still passes its isolation requirement at 6.5984 mm CREEPAGE** against
  6.000 mm required, and this release's `READ BEFORE ASSEMBLY` block — the
  correction v1.4 exists for — is **still correct and is carried forward verbatim
  into v1.5**
- both v1.3 P0 fixes present in every artifact: `R_OPENT` = C37825 (62 kΩ),
  `R_WDPETPD` = C11702 (1 kΩ)

**If you are holding this release's GERBERS, they are correct and need no
regeneration. DO NOT UPLOAD THIS RELEASE'S `fab/bom.csv`.**

## Why v1.5 exists — three reasons, all of them in the BOM

### 1. Two BOM lines JLC cannot supply

Read live 2026-07-27 (`selectSmtComponentList`, exact `componentCode` match):

| | v1.4 ships | live 2026-07-27 | v1.5 ships |
|---|---|---|---|
| 17 refs — R_BID0/1, R_DOORPD, R_ESTOPPD, R_EXPRST, R_MODEPD, R_OE, R_OS2, R_REF0-7, R_TEMPOK | `C25744` 0402WGF1002TCE, UNI-ROYAL, **base** | **`stockCount` 0**, `minPurchaseNum` 5268 | `C60490` **RC0402FR-0710KL**, YAGEO, expand, stock 8 404 363 |
| R_ILM | `C25862` 0402WGF1201TCE, UNI-ROYAL | `stockCount` **25 / 65 / 90 across one afternoon**, `minPurchaseNum` **7463** | `C138040` **RC0402FR-071K2L**, YAGEO, stock 472 208 |

**C25744 is the same code and the same shortage that forced usb-hub-3s-v3 v1.11
hours earlier**, on a different board, in a different circuit — a CATALOG event,
not a cooksense one. It was the only basic-library 10 kΩ 0402, so every
replacement is an EXTENDED part and the one-time feeder fee is a property of the
shortage.

**C25862 is the more interesting one, because this release's own stock evidence
PASSES it.** `verification/stock_check.json` here grades every coded line at
`stock >= 5 x qty`, and 90 ≥ 5. A line whose *minimum purchase* is 7463 against
double-digit stock is one JLC cannot commit against for a 5-board order, and the
gate cannot see that. The v1.5 dossier records it; the gate is unchanged and the
limitation is named rather than quietly fixed.

Both replacements' catalog `describe` strings are **CHARACTER-IDENTICAL** to the
parts they replace, compared AS STRINGS; `componentSpecificationEn` is `0402` on
both sides; `leastPatchNumber` is 20 on both sides. Zero Footprint changes.

### 2. A BOM its recipient cannot read

Graded the way JLC parses it (canon F-LEGIBLE, ADR-0006), this release's
`fab/bom.csv` carries **83 findings and 0 checks passed**:

- **55 F-MPN** — EVERY coded row ships a BLANK MPN column. JLC's matcher leaves a
  code-only line at *"No Part Selected"*.
- **26 F-WORDS** — the Comment is the LCSC code repeated (`C10092`, `C22046`, …),
  which is already in the LCSC column. A row nobody can read is a row nobody can
  check, on either side of the upload.
- **2 F-ENCODE** — `Ω` with no UTF-8 byte-order-mark; a reader defaulting to
  cp936 sees `惟`.

v1.5: **0 findings, 56 checks.** Nothing was invented — 54/54 coded rows resolve
their MPN from dossiers and the vetted passives ledger, both of which already
held the answer.

### 3. Three gate FAILs this release carries, now closed or graded

- **M-REL** — this release has **no CHANGELOG entry at all**. Entries existed for
  v1.0, v1.1, interposer-v1.0, v1.3 and interposer-v1.1; the LIVE release was
  missing from its own project changelog. Also `git_dirty: no`, a string where
  the schema wants `false`. Both fixed at v1.5 (the changelog entry is written
  there, in the project document — **this sealed directory is not retro-filled**).
- **M-BOM** — `UNVERIFIABLE-VALUE` on `220uF [CE1]` (`C2887273`): labelled 220 µF
  and no source yielded the catalog value, because the 2026-07-23 ledger seed
  missed it while its own one-digit-away sibling `C2887276` was already there.
  The catalog `describe` says `220uF` verbatim; the ledger now does too.
- **A-BODY** — `missing_models.txt` here was generated with **no `--cpl`**, so
  its denominator was 186 BOARD footprints instead of the 189 CPL placements, and
  it counted `J_ISOLOOP` — which is `not_assembled` / `exclude_from_pos_files`
  and **is not on the CPL at all**. Regenerated against `fab/cpl.csv`: **189/189
  bodies mounted**.

## What v1.5 does NOT fix, and says so

**E-TOPO FAILS on v1.5, and it also fails here — differently, and worse.** This
release declares `rails: []` with its envelopes parked in a `linear_rails:` key
the checker ignores by design, so E-TOPO grades **0 of 1** converters: an
LDO-only board reaching a green gate by showing it nothing. v1.5 declares the
AMS1117-3.3 rail properly and the gate returns a specific, cited number:

    headroom 1101 mV (Vin_min 4.500 - Vout_max 3.399) vs dropout 1300 mV
    -> FAIL, short by 199 mV

The 1300 mV is ds1117 p.3, MAX, **at IOUT = 0.8 A** — 2.67× this rail's 0.3 A
load. The datasheet publishes **no** dropout figure at 0.3 A and **no**
dropout-vs-load curve, so that number is **OWED**, and `vin_min` was left at 4.5
rather than raised to the 4.75 that would make the gate pass. **The finding is a
SUPPLY SPECIFICATION, not a copper defect** — "5 V SELV" was never given a
tolerance, and this board needs ≥ 4.699 V at the LDO input. v1.5's ORDER_README
§0 says what to buy and what to measure. **It does not block ordering either
release.**

## The MANDATORY-BEFORE-ORDERING list is unchanged

This supersede clears none of it. v1.5 carries all of it forward verbatim: the
unsupervised-door decision, the §6 order-preview human gate (17 rows, including
the three POLARITY-FIT-BLIND diodes), `R_OPENT` = C37825, the non-conductive
enclosure assumption (ADR-0012), the H4 fastener spec, and the `J_ISOLOOP` pole
legend.

**C42400616 (KF350-3.5-4P, J_ISOLOOP) is still `stockCount` 0 in v1.5 and was
deliberately NOT substituted** — it is THT on an SMT-only order, `not_assembled`,
off the CPL, and every JLC-stocked 3.5 mm 4-pole alternative is a pluggable
2EDG-family part with a different body, i.e. a footprint change that would move
copper and void every review verdict this board carries. v1.5 ORDER_README §5
states the three options.
