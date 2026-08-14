# contract: skills/shopping-list/scripts/

**Purpose** — the buying checker. Plain `python3`, no `pcbnew`; the only
network call in the folder is Mouser's Search API, and every test replays
recorded responses so the suite never makes one.

## Allowed

| Pattern | What |
|---|---|
| `shopping_list.py` | `PROJECT_DIR -> per-distributor list + verdict`. Derives exact dossier identity plus quantities from a candidate `--bom` or newest sealed BOM. `--required-pools N --jlc-stock-json FILE` enables **Q-2SOURCE**: every exact `(manufacturer, full MPN)` row must qualify at N independent authorized pools among JLC/LCSC, Mouser and DigiKey; Amazon never counts. The fresh JLC sidecar is joined by LCSC, MPN, manufacturer and per-board quantity. Emits **Q-COVER**, **Q-WIDE**, **Q-IDENT**, **Q-MFR-IDENT**, **Q-STOCK**, **Q-SNIPPET**, **Q-GRADE** and **Q-2SOURCE**. A missing/mismatched candidate-BOM row is a failure, never a guessed quantity. Terminal progress carries row/total, START/DONE and elapsed time |
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
- **Re-deriving "the newest release".** `newest_release_boms` imports
  `jlcpcb-fab/scripts/release_index.py`; it must not sort release directories
  itself. It did, with `d.name > prev[0]` — a TEXT comparison under which
  `v1.10-2026-07-27` is older than `v1.9-2026-07-27` — so it would have quoted
  the SUPERSEDED BOM, and therefore the wrong refdes set and the wrong
  quantities, while naming it as the newest (usb-hub-3s-v3 reached a
  double-digit minor 2026-07-27). The same defect had already been fixed in
  policy_audit and left standing here: canon M-WIDTH, a rule written at the
  width of its incident rather than its class.

## Audit

- `gate_contract_audit.py` — G-INPUT / G-COVER / G-RED (`shopping_list.py`
  prints a verdict).
- `tests/t1_shopping_list.py` — 26 tests, 14 known-bad, hermetic via
  `--replay tests/fixtures/shopping_list/mouser/`. Q-WIDE, Q-SNIPPET and
  Q-IDENT are each RED-verified against a neutered checker, with the measured
  pass/fail counts recorded in the suite docstring.
- Rate limit: Mouser publishes 50 parts/call, 30 calls/min, 1,000 calls/day.
  2.1 s spacing and a `--call-budget` ceiling are the enforcement.
