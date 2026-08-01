# contract: 01_docs/sourcing/

**Purpose** — what to BUY for the parts the fab will not source, and the
evidence behind each number. Produced and graded by `/shopping-list`
(`skills/shopping-list`), governed by canon **`M-QUOTE`** — the narrow instance
of `M-IMPORT` scoped to distributor facts.

**Why this folder exists rather than `06_build/cache/`.** `01_docs/` otherwise
FORBIDS stock, price and availability, and that rule stands: a market number may
never be committed **as truth**. What lives here is not truth — it is a **dated
observation with its provenance**, the same shape as a journal entry. The
distinction is load-bearing and mechanical, not rhetorical:

- every file is stamped with the date it was produced and says, in its own
  first paragraph, that the numbers are stale;
- every number carries its M-IMPORT grade and the URL/date it was read from;
- the raw API responses stay in `06_build/cache/` (gitignored, TTL'd, never
  committed), and nothing here is re-consumed by a build.

**Mutability** — APPEND-ONLY, one dated file per run. A shopping list is
evidence of what a distributor said on a day; superseding it means adding the
next dated file, never editing the old one. `manual_quotes.yaml` is the one
mutable file: it is an INPUT, and a re-read replaces the entry it re-reads.

## Allowed

| File | What | Rule |
|---|---|---|
| `shopping-list-<YYYY-MM-DD>.md` | the generated per-distributor list: MPN, distributor part number, stock, min/multiple, lifecycle, unit price at the needed break, extended price, direct product URL; every catalog record seen; a CANNOT-SOURCE section naming every failed line with its reason; and the coverage denominator | GENERATED — never hand-edited. Regenerate with `shopping_list.py PROJECT_DIR --out ...` and add a NEW dated file |
| `shopping-list-<YYYY-MM-DD>.json` | the machine sidecar for the same run, carrying an explicit `verdict` | GENERATED. A missing or unparseable verdict is a FAIL, never a skip |
| `dual-source-<YYYY-MM-DD>.md` | dated Q-2SOURCE join of JLC catalog stock, Mouser API results, and only the exact DigiKey product pages needed where JLC+Mouser do not already clear the rule | DERIVED EVIDENCE — names both qualifying pools or the exact rejection reason for every selected dossier MPN |
| `manual_quotes.yaml` | every DigiKey / Amazon number, because neither has a usable API here. One entry per `{mpn, distributor}`: `source:` (`product_page` \| `search_snippet` \| `catalog_absence`), `url:`, `read_on:` (ISO date), then `stock:`, `min:`, `mult:`, `lifecycle:`, `unit_price_usd:` or `price_breaks: [{qty, usd}]`, `note:` | HAND-WRITTEN, and every field is evidence. **`source: search_snippet` is REFUSED as a stock figure** (Q-SNIPPET): GHR-10V-S was reported available on a snippet reading "available to order today with same-day shipping" while the product page said In Stock: 0. **`source: catalog_absence`** is the ONE admissible use of a search page — absence IS a property of the search — and requires `listed: false` plus a `note:` saying what the catalog returned instead. A quote with no `url:`/`read_on:`, or an absent `source:`, is QUOTE-INVALID (Q-GRADE): an ungraded fact reads as ESTIMATED and a machine may not quietly promote it |
| `contracts.md` | this file | |

## Forbidden

- Hand-editing a generated list. If a number is wrong, fix the input
  (`manual_quotes.yaml`, `02_parts/<dir>/part.yaml`) and regenerate.
- A stock or price number with no `url:` and no `read_on:`.
- An invented product link, ASIN or distributor part number. A row nobody has
  is **OWED** and stays OWED — "no quote recorded" is a finding, and padding the
  table to make it look complete is the defect this whole folder exists against.
- A substituted part. A near MPN is a PROPOSAL for a human (Q-IDENT); recording
  one against the authoritative MPN's line is a silent substitution.
- Any credential. The Mouser key lives in `<repo>/.secrets/mouser.env`.

## Audit

- **Pre-selection Q-2SOURCE gate:** a component may enter the schematic only
  when at least two independent authorized distributor pools each list the
  exact authoritative MPN (or an explicitly approved dossier alternate) as
  active and orderable, with stock greater than 10 and sufficient for five
  board sets. JLCPCB/LCSC is one pool, Mouser is one, and DigiKey is one;
  marketplaces and multiple listings from the same distributor do not increase
  the count. Fewer than two qualifying pools rejects the selection rather than
  creating a release-time waiver. Run this once after the part/footprint/
  assembly freeze and before schematic completion, then repeat it on order day.
- `shopping_list.py PROJECT_DIR` = the gate: **Q-COVER** (`N/M` per
  distributor; a part it could not look up is a FAIL, never an omission),
  **Q-WIDE**, **Q-IDENT**, **Q-STOCK** (`stock > 10` AND `>= qty`),
  **Q-SNIPPET**, **Q-GRADE**.
- Known-bads: `tests/t1_shopping_list.py`.
- **Re-run on order day regardless.** Stock moves; a committed list is a record
  of a past answer, not a current one.
