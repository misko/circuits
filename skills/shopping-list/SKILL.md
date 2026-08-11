---
name: shopping-list
description: Produce a per-distributor shopping list for a board's self-supplied parts — Mouser via its API, DigiKey and Amazon via recorded product-page reads — with the M-IMPORT grade of every number, a stock floor, and a coverage denominator. Use when asked what to order, where to buy the hand-soldered/self-supplied parts, whether a part is in stock, or whether one distributor has everything.
---

# shopping-list

    /shopping-list <project folder>
    /shopping-list projects/<name>

    skills/shopping-list/scripts/shopping_list.py PROJECT_DIR \
        [--scope self_supplied|all] [--boards N] [--min-stock 10] \
        [--bom CANDIDATE.csv] \
        [--required-pools 2 --jlc-stock-json stock.json] \
        [--out list.md] [--json list.json]

Answers one question — **what do I have to buy, from whom, and can I actually
get it** — for the parts the fab will not source. Every number it prints carries
its provenance and a confidence grade, because a distributor fact is a fact from
OUTSIDE this repo and is therefore governed by **`M-IMPORT`**.

---

## The three incidents this skill is made of

This repo's rules exist because each was paid for. These three are one escalating
lesson, and they are the same defect the canon already names — the
**adjacent-property error** (M-IMPORT's co-resident corollary): *measuring
something NEAR the property you need.*

### 1. GHR-10V-S — a snippet is not a stock figure

A JST GH connector was reported to the user as **available**, on the strength of
a DigiKey **search-result snippet** reading *"available to order today with
same-day shipping"*. The **product page** said **In Stock: 0**.

That sentence is boilerplate. It renders at zero stock. The property measured
was *the state of a search page*; the property needed was *the state of the
part*. Nothing about the snippet was false — it simply was not an answer to the
question being asked.

> **A SEARCH-RESULT SNIPPET IS NEVER A STOCK FIGURE.** Open the product page.

### 2. 10FDZ-BT — a machine-readable field is not automatically the right field

The obvious fix for incident 1 is "use an API". So: the Mouser Search API, asked
`partSearchOptions: "Exact"` for `10FDZ-BT(S)(LF)(SN)` — the **authoritative
manufacturer MPN**, exactly as this repo's own `02_parts/` dossier holds it —
returns **one** hit:

    ManufacturerPartNumber : 10FDZ-BT(S)(LF)(SN)
    MouserPartNumber       : N/A
    Availability           : null
    LifecycleStatus        : Obsolete
    PriceBreaks            : []

Obsolete. Machine-readable, timestamped, unambiguous, and **wrong**. The same
part, searched `partSearchOptions: "None"` on the suffix-stripped `10FDZ-BT`,
returns **two** records — one of them **37 In Stock at $0.96/1**, Mouser part
number **`306-10FDZBTSLFSN`**, whose own digits encode **S / LF / SN**. The live
record *is* the (S)(LF)(SN) variant. It is merely catalogued under the bare MPN
while a dead record squats on the suffixed one.

**One physical part. Three catalog records. Three different answers.** Measured
2026-07-27; the responses are recorded verbatim in
`tests/fixtures/shopping_list/mouser/`.

> **ONE RECORD IS NOT THE PART.** Incident 1 measured the state of a *search
> page*. Incident 2 measured the state of a *catalog entry*. Neither measured
> the state of the *part*. The second fires through a JSON API — which is why
> "prefer the API" is a tier ordering, not the lesson.

### 3. The corollary that falls out — widening the query is not widening the part

Search `B5B-XH-A` broad and Mouser also returns `B5B-XH-A-GU`, `B5B-XH-A-G` and
`B5B-XH-AM(LF)(SN)` — all in stock, all **different connectors**. A tool that
searches wider and then takes the deepest-stock hit has stopped reporting and
started **substituting**, silently, on a board where four of six self-supplied
lines are marked DO-NOT-SUBSTITUTE because the part *is* the safety argument.

> **A near MPN is a PROPOSAL for a human, never a sourced line.**

---

## The three tiers, and they are not equals

| distributor | method | grade |
|---|---|---|
| **Mouser** | the Search API (`search/partnumber`), two searches per part | **CITED** — machine-readable, timestamped |
| **DigiKey** | a **product page** a human opened, recorded with its URL and read date | **CITED** from a product page; a snippet is **REFUSED** |
| **Amazon** | direct product links, hand-recorded | **ESTIMATED, always** |

The grades are M-IMPORT's closed vocabulary: **CITED** (a vendor document or a
machine-readable source, with the page/URL/date), **ESTIMATED** (derived,
volatile, unverifiable — and it must carry its uncertainty), **OWED** (nobody
has this fact; say how to obtain it, and do not spend it).

**Amazon is ESTIMATED by construction, not by accident.** There is no usable API
(PA-API needs an affiliate account); listings are third-party-seller-dependent;
stock and price move without notice; and marketplace listings do not carry
manufacturer part numbers as a first-class field, so an Amazon "match" is usually
a substitution wearing a part number in its title. No Amazon row may ever grade
CITED — `t_amazon_is_estimated_even_from_a_product_page` asserts it.

### DigiKey: what would make it a peer

DigiKey **has** an API. This skill does not use it, and the reason is not
technical: it needs OAuth 2.0 client credentials nobody has provided, and **an
agent cannot create an account or obtain a key.** That is stated in the report
itself, every run, so nobody mistakes the gap for a judgement. To close it:

1. Sign in at <https://developer.digikey.com/>.
2. Create an Organization, then a **Production** app (Sandbox data is
   structurally correct but incomplete — never source from it).
3. Subscribe the app to **Product Information V4**.
4. Copy the **Client ID** and **Client Secret**.
5. Put them in `<repo>/.secrets/digikey.env`, mode 600 (`.secrets/` is
   gitignored — check with `git check-ignore .secrets/`).
6. The 2-legged flow then becomes a peer of the Mouser path: POST
   `client_id` + `client_secret` + `grant_type=client_credentials` to
   `https://api.digikey.com/v1/oauth2/token`, then
   `GET /products/v4/search/{mpn}/productdetails`.

Until then every DigiKey row is CITED-from-a-page or OWED. Neither is a peer of
an API response, and the report says which it is per line.

---

## The Mouser protocol — and why the order is structural

```
1. Exact  on the AUTHORITATIVE MPN            (02_parts/<dir>/part.yaml `mpn:`)
2. None   on the SUFFIX-STRIPPED MPN          (10FDZ-BT(S)(LF)(SN) -> 10FDZ-BT)
3. reconcile every record from both, keeping which search found it
4. keep only records whose manufacturer MPN IS the part (Q-IDENT)
5. choose the deepest-stock survivor; report the rest anyway
```

Trailing parenthesised groups of ≤4 alphanumerics — `(S)`, `(LF)`, `(SN)` and
combinations — are **packaging and plating qualifiers**, not different parts.

Step 2 runs **unconditionally**, and `grade_mouser()` *asserts*
`RecordSet.broad_done` before it is permitted to emit an unsourceable verdict. A
lone exact hit that reads Obsolete produces `INCONCLUSIVE`, never a finding.
That is incident 2 made mechanical rather than remembered — a comment saying
"remember to search wider" is a comment, and comments do not gate.

**`FactoryStock` and `LeadTime` are part of the answer.** *37 in stock* alone
lets someone plan a 200-piece build; *37 in stock, FactoryStock 0, lead 180 days*
says the shelf is the entire supply for half a year. The report prints both and
raises a supply caution whenever factory stock is zero.

### Rate limit and cache

Mouser publishes **50 parts per call, 30 calls/minute, 1,000 calls/day**
(<https://www.mouser.com/api-search/>). The tool sleeps 2.1 s between calls
(28.6/min) and refuses to exceed `--call-budget` (default 200) in one run.

Mouser's API terms **forbid caching their content**, so the cache is a *session*
cache and nothing more: `06_build/cache/mouser/`, gitignored and disposable,
every entry stamped `fetched_at`, 6-hour TTL, never committed, and never truth at
order time — which is already the 06_build contract's own rule. Re-run before
you pay.

---

## The credential

Resolution order, and the skill hardcodes none of it:

1. `$MOUSER_API_KEY` (the literal value `none` declares it explicitly absent)
2. `<repo root>/.secrets/mouser.env`

Repo root is found by walking up for a directory holding **both** `skills/` and
`contracts.md`, and then by `git rev-parse --git-common-dir`'s parent.
**Not** `git rev-parse --show-toplevel`: inside a linked worktree that returns
the *worktree*, a relative `.secrets/` resolves to a directory that does not
exist, and the tool silently loses its key. That is the adjacent-property error
again — the property is *where the repo's secrets live*, not *where git thinks I
am* — and it was got wrong the first time, here, on this skill.

**The key is never printed, logged, echoed into a URL, written to a cache file,
or recorded in a fixture.** Mouser puts it in the **query string**, so every URL
the tool records is a leak site; `Mouser.call()` scrubs it out of every error
path, and `t_the_key_is_never_printed` plants a sentinel key and greps stdout,
the markdown, the JSON sidecar and every cache file for it.

**If the credential is absent the tool says so, degrades to the manual path, and
grades every Mouser line OWED.** It does not crash, and it does not emit an
unsourced list that looks sourced.

---

## What goes in, what comes out

**In** — the authoritative sources already in the tree. Nothing is invented:

| source | what it decides |
|---|---|
| `02_parts/<dir>/part.yaml` | **the MPN**, from the `mpn:` FIELD. The directory name is a *sanitised rendering* — real MPNs contain `/` (`MCP23017-E/SS`) and `*` (`2.54-2*20PPC104`). A path is not an MPN |
| the newest sealed `07_releases/*/fab/bom.csv` per board | which refdes exist, and therefore the quantity. Opened **read-only** — releases are immutable |
| `03_src/**/rules/assembly.yaml` | `not_assembled:` / `consigned:` — the refs the fab will not place, i.e. the ones you buy |
| `--bom CANDIDATE.csv` | pre-release refdes/quantity authority; replaces sealed-release discovery so three parts per board times five boards is 15, not a guessed 5 |
| `--jlc-stock-json stock.json` | fresh, timestamped `jlc_stock_check.py` sidecar; joined by LCSC, full MPN, manufacturer and per-board quantity |
| `01_docs/sourcing/manual_quotes.yaml` | every DigiKey / Amazon number, each with manufacturer, page URL and read date |

Scope defaults to `self_supplied`: a part is selected if its `sourcing.lcsc` is
empty, or it asserts `not_on_assembly_bom`, or its BOM row has a blank LCSC, or
any of its refs is in an `assembly.yaml` `not_assembled`/`consigned` block.
`--scope all` prices the whole tree.

**Out** — `--out list.md` (per-distributor tables, every catalog record seen,
distributor gaps, a row-level composed-pool verdict and DigiKey enablement)
and `--json list.json`
(the same with an explicit `verdict`). The committed home is
`01_docs/sourcing/shopping-list-<date>.md` — a dated observation, never truth.
The terminal is also an operational output: each selected MPN emits
`START`/`DONE`, `current/total`, elapsed seconds and the pools reached, so a
slow external lookup cannot look like a stalled pipeline.

---

## The check IDs (canon `M-QUOTE`)

| ID | What it forbids |
|---|---|
| **Q-COVER** | passing while grading nothing. `N/M` per distributor; a part the tool could not look up is a FAIL, never an omission; a zero denominator is a FAIL |
| **Q-WIDE** | calling a part unsourceable before the broad search has run. Enforced structurally, not by comment |
| **Q-IDENT** | substituting. A record whose MPN is not the authoritative one (modulo packaging suffixes) is a proposal, never a source |
| **Q-MFR-IDENT** | treating a generic/base MPN from a different manufacturer as the selected part; manufacturer plus full orderable MPN is the source key |
| **Q-STOCK** | sourcing below the floor. `stock > --min-stock` (default 10, the user's standing bar) **and** `stock >= qty needed`. A failing line is REPORTED, never dropped |
| **Q-SNIPPET** | a search snippet, or a stale read, as a stock figure. A quote names its page and its read date or it is invalid |
| **Q-GRADE** | an ungraded number. Absent is a FAIL — an ungraded fact reads as ESTIMATED and a machine may not quietly promote it |
| **Q-2SOURCE** | judging each distributor in isolation when the policy is a composed pool. With `--required-pools 2`, every exact row must qualify at two of JLC/LCSC, Mouser and DigiKey; Amazon never counts |

`source: catalog_absence` is the **one** case where a search page is legitimate
evidence: the property *"this catalog does not list the part"* **is** a property
of the search. Reading PRESENCE off a search page is the GHR-10V-S error;
reading ABSENCE off one is not. It requires `listed: false` and a `note:` saying
what the catalog returned instead — *"no results"* and *"only pack-quantity
variants"* are different findings.

The pre-selection invocation is one command, so the composed verdict cannot
drift into a hand-written join:

    shopping_list.py PROJECT_DIR --scope all --boards 5 \
      --bom CANDIDATE.csv --required-pools 2 \
      --jlc-stock-json STOCK.json --out REPORT.md --json REPORT.json

## Reading the output honestly

- **A total counts only what you can actually buy.** Summing a line priced at a
  quantity you cannot order (MOQ 100 against a need of 2, or a part at 0 stock)
  gives a number that is arithmetically right and operationally false. Partial
  totals say `INCOMPLETE` and name the missing lines.
- **`Active` and `in stock` are different facts.** DigiKey lists 10FDZ-BT as
  *Active*, *not kept in stock*, MOQ 100, 16-week lead. Lifecycle is not
  availability.
- **A pack-quantity variant is a packaging question, not a substitution**, but it
  is still not the MPN you asked for. The tool reports it and refuses to resolve
  it for you.

## Tests

`tests/t1_shopping_list.py` — 26 tests, 14 known-bad. The two headline fixtures
are the real recorded responses from incidents 1 and 2, and all three checks
(Q-WIDE, Q-SNIPPET, Q-IDENT) are RED-verified against a deliberately neutered
checker with the measurements written into the suite docstring. `--replay`
makes the suite hermetic: **no test in this repo calls Mouser.**
