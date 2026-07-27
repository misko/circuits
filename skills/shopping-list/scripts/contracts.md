# contract: skills/shopping-list/scripts/

**Purpose** — the buying checker. Plain `python3`, no `pcbnew`; the only
network call in the folder is Mouser's Search API, and every test replays
recorded responses so the suite never makes one.

## Allowed

| Pattern | What |
|---|---|
| `shopping_list.py` | `PROJECT_DIR -> per-distributor list + verdict`. Derives the part set from `02_parts/<dir>/part.yaml` (the `mpn:` FIELD is the authority — a directory name is a sanitised rendering and real MPNs contain `/` and `*`), the newest sealed `07_releases/*/fab/bom.csv` per board (read-only; releases are immutable), `03_src/**/rules/assembly.yaml` (`not_assembled`/`consigned` = the refs you buy) and `01_docs/sourcing/manual_quotes.yaml` (every hand-read DigiKey/Amazon number, with its page URL and read date). Emits **Q-COVER** (`N/M` per distributor; an un-looked-up part is a FAIL, never an omission; zero denominator is a FAIL), **Q-WIDE** (an unsourceable verdict is unreachable until the broad suffix-stripped search has run — enforced by an assertion on `RecordSet.broad_done`, not by a comment), **Q-IDENT** (a record whose manufacturer MPN is not the authoritative one modulo packaging suffixes is a PROPOSAL, never a source — the broad search widens the QUERY, not the PART), **Q-STOCK** (`stock > --min-stock`, default 10, AND `stock >= qty`; a failing line is REPORTED, never dropped or substituted), **Q-SNIPPET** (a quote must name its page and read date; `source: search_snippet` and a stale read are both REFUSED as stock figures) and **Q-GRADE** (every number carries CITED / ESTIMATED / OWED; absent is a FAIL, never a quiet promotion). `source: catalog_absence` is the one admissible use of a search page — absence IS a property of the search, presence is not |
| `*.py` | further buying tools, same rules |
| `contracts.md` | this file |

## Forbidden

- **Any credential, in any file here.** The key is read from
  `$MOUSER_API_KEY` or `<repo root>/.secrets/mouser.env` at runtime. No
  hardcoded key, and no hardcoded absolute path to one — repo root is resolved
  by marker-walk (`skills/` + `contracts.md`) then
  `git rev-parse --git-common-dir`'s parent, because `--show-toplevel` returns
  the WORKTREE and loses the key.
- Printing, logging or embedding the key in a URL, an error message, a cache
  file, a report or a fixture. Mouser passes it in the QUERY STRING, so error
  paths must scrub it.
- Treating a cached response as truth. `06_build/cache/mouser/` is a gitignored
  session cache with a `fetched_at` and a 6-hour TTL — Mouser's API terms
  forbid caching their content, and the 06_build contract already forbids
  treating a cached stock number as truth at order time.
- Substituting a part. Naming a near MPN is reporting; choosing one is not.

## Audit

- `gate_contract_audit.py` — G-INPUT / G-COVER / G-RED (`shopping_list.py`
  prints a verdict).
- `tests/t1_shopping_list.py` — 17 tests, 11 known-bad, hermetic via
  `--replay tests/fixtures/shopping_list/mouser/`. Q-WIDE, Q-SNIPPET and
  Q-IDENT are each RED-verified against a neutered checker, with the measured
  pass/fail counts recorded in the suite docstring.
- Rate limit: Mouser publishes 50 parts/call, 30 calls/min, 1,000 calls/day.
  2.1 s spacing and a `--call-budget` ceiling are the enforcement.
