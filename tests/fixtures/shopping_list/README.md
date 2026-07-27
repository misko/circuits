# fixtures/shopping_list/ — recorded Mouser Search API responses

Replayed by `t1_shopping_list.py` via `shopping_list.py --replay DIR`, so the
suite is hermetic: **no test in this repo ever calls Mouser.**

## Provenance

Recorded 2026-07-27 against `https://api.mouser.com/api/v1/search/partnumber`,
one file per `(mouserPartNumber, partSearchOptions)` query. The filename is the
same slug `shopping_list.py` computes, so a file dropped in here is found by the
replay path with no index.

| file | query | what it is evidence OF |
|---|---|---|
| `mouser/10FDZ_BT_S_LF_SN_Exact.json` | `10FDZ-BT(S)(LF)(SN)` / `Exact` | **THE INCIDENT.** 1 hit: `Availability: null`, `LifecycleStatus: "Obsolete"`, `MouserPartNumber: "N/A"`, 0 price breaks. A confident, machine-readable, wrong answer |
| `mouser/10FDZ_BT_None.json` | `10FDZ-BT` / `None` | the same physical part, 2 records, one of them **37 In Stock** at $0.96 under `306-10FDZBTSLFSN` — whose digits encode S / LF / SN |
| `mouser/B5B_XH_A_LF_SN_Exact.json` | `B5B-XH-A(LF)(SN)` / `Exact` | the ordinary case: exact match, 30599 in stock |
| `mouser/B5B_XH_A_None.json` | `B5B-XH-A` / `None` | **the Q-IDENT hazard**: the broad search also returns `B5B-XH-A-GU`, `B5B-XH-A-G` and `B5B-XH-AM(LF)(SN)`, all in stock, all different connectors |
| `mouser/DIP05_1A72_12L_Exact.json`, `..._None.json` | `DIP05-1A72-12L` | a part where both searches agree — the boring baseline a suite needs so the interesting fixtures mean something |
| `mouser/PCC_SMP_K_Exact.json`, `..._None.json` | `PCC-SMP-K` | **zero hits, both searches.** "This distributor does not list the part" is a finding with its own status, not a stock figure and not a skip |

## The credential

Mouser passes the API key in the **query string**, not the body, so these
response payloads never contained one. That is checked rather than assumed:
`t1_shopping_list.t_fixtures_carry_no_credential` greps every file here for
`apiKey`, `api_key` and UUID-shaped tokens and fails the suite on a hit. The
recording script asserted the live key was absent from each file before writing.

## Re-recording

    export MOUSER_API_KEY=...            # never commit it; .secrets/ is ignored
    shopping_list.py <project> --out /dev/null      # populates 06_build/cache
    # then copy 06_build/cache/mouser/<slug>.json's `payload` object here

Mouser's API terms forbid caching their content; these are a handful of
responses kept as TEST EVIDENCE of a specific defect, not a catalog mirror, and
the numbers in them are already stale by design — no test asserts they are
current, only that the tool reads them correctly.
