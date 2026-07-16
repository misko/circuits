# contract: build/

**Purpose** — everything a tool can regenerate. Disposable by definition.
`rm -rf build/` must always be safe.

**Mutability** — free. **Gitignored in its entirety** except this file.

## Allowed

| Path | What | TTL |
|---|---|---|
| `renders/` | PNG/SVG/PDF of schematic and board | regenerate |
| `netlists/` | exported netlists | regenerate |
| `drc/` | DRC/ERC/audit reports | regenerate |
| `cache/` | **volatile market data**: stock, price, distributor attrs | hours |
| `contracts.md` | this file (the only tracked file here) | |

## Why `cache/` matters

Volatile lookups (JLC stock, LCSC attributes, distributor pricing) are cheap
per call but add up: one session fetched attributes for 287 parts at ~1.2s
each and left them in a SESSION-scratch directory, so the next session would
pay all ~6 minutes again. Cache them here, keyed by query, with a
`fetched_at` — and **re-fetch before ordering regardless**, because stock
moves and a stale number is worse than no number.

Never promote anything from `cache/` into `parts/`. Facts are permanent;
market data is not.

## Forbidden

- Anything unregenerable. If `rm -rf build/` would lose information, that
  information is in the wrong folder.
- Committing anything here (except this contract).
- Treating a cached stock number as truth at order time.

## Validate

- `.gitignore` covers `build/` and `git ls-files build/` returns only
  `build/contracts.md`
- every `cache/` entry carries a `fetched_at`
- deleting `build/` and re-running the generators + exports reproduces it

## Repair

- Tracked file in `build/` → decide: regenerable (delete + gitignore) or not
  (move to `src/`, `docs/`, `parts/`, or `releases/`).
- Cache entry with no timestamp → delete; unknown age is unusable.
