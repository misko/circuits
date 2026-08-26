# Shopping list — smc0985-cooksense

Generated `2026-07-27 21:08 UTC` by `shopping_list.py` (scope `self_supplied`, 1 board set(s), stock floor `> 10`).

**Every number here is a dated OBSERVATION, not a fact.** Stock and price move; re-run before you pay. Each row carries its M-IMPORT grade: **CITED** = machine-readable API response or a product page read with its URL and date · **ESTIMATED** = volatile/unverifiable · **OWED** = nobody has this number yet.

## Coverage (Q-COVER)

- parts in `02_parts/`: **41**
- selected for this list (`self_supplied`): **6**
- **mouser**: graded **6/6**, sourceable **3/6**
- **digikey**: graded **6/6**, sourceable **2/6**
- **amazon**: graded **0/6**, sourceable **0/6**

## Is there one distributor that has everything?

**No.** No single distributor covers all 6 selected lines at stock > 10. Best coverage: mouser 3/6, digikey 2/6, amazon 0/6.

## Mouser

*Method: Mouser Search API (search/partnumber). TWO searches per part: `Exact` on the authoritative MPN, then `None` on the suffix-stripped MPN — one part has several catalog records and they disagree. CITED.*

| MPN | qty | dist. part no. | stock | factory / lead | min/mult | lifecycle | unit @ break | extended | grade | status | link |
|---|---:|---|---:|---|---|---|---:|---:|---|---|---|
| `10FDZ-BT(S)(LF)(SN)` | 2 | 306-10FDZBTSLFSN | 37 | 0 / 180 Days | 1/1 | — | $0.9600 @ 1 | $1.92 | CITED | OK | [page](https://www.mouser.com/en/ProductDetail/JST-Commercial/10FDZ-BT?qs=olJun0bQHM99eR757fzIdQ%3D%3D) |
| `2.54-2*20PPC104` | 1 | — | — | — | —/— | — | — | — | CITED | NOT-IN-CATALOG | — |
| `B5B-XH-A(LF)(SN)` | 1 | 306-B5BXHALFSN | 30599 | 0 / 112 Days | 1/1 | — | $0.2000 @ 1 | $0.20 | CITED | OK | [page](https://www.mouser.com/en/ProductDetail/JST-Commercial/B5B-XH-ALFSN?qs=cdbOS8ANM9ApoXpxtybURg%3D%3D) |
| `DIP05-1A72-12L` | 12 | 876-DIP05-1A72-12L | 132 | 0 / 125 Days | 1/1 | — | $3.4500 @ 10 | $41.40 | CITED | OK | [page](https://www.mouser.com/en/ProductDetail/MEDER-electronic/DIP05-1A72-12L?qs=k5V78Jg%2Feq5x%2FLYUrMtrGw%3D%3D) |
| `KF350-3.5-4P` | 1 | — | — | — | —/— | — | — | — | CITED | NOT-IN-CATALOG | — |
| `PCC-SMP-K` | 1 | — | — | — | —/— | — | — | — | CITED | NOT-IN-CATALOG | — |

**mouser total: INCOMPLETE — $43.52 covers only 3 of 6 lines.** A total over a partial list is not a total. Only SOURCEABLE lines are summed: pricing a line you cannot order at the quantity you need (0 stock, or an MOQ above the need) gives a number that is arithmetically right and operationally false. The missing lines are named below.

## Digikey

*Method: PRODUCT PAGE read by a human and recorded in 01_docs/sourcing/manual_quotes.yaml. No API key available (OAuth client credentials not provided). CITED from a product page; a search snippet is REFUSED.*

| MPN | qty | dist. part no. | stock | factory / lead | min/mult | lifecycle | unit @ break | extended | grade | status | link |
|---|---:|---|---:|---|---|---|---:|---:|---|---|---|
| `10FDZ-BT(S)(LF)(SN)` | 2 | 455-10FDZ-BT-ND | 0 | — | 100/100 | Active | $0.5758 @ 100 | $1.15 | CITED | LOW-STOCK | [page](https://www.digikey.com/en/products/detail/jst-sales-america-inc/10FDZ-BT/28540420) |
| `2.54-2*20PPC104` | 1 | — | 0 | — | —/— | — | — | — | CITED | NOT-IN-CATALOG | [page](https://www.digikey.com/en/products/result?keywords=2.54-2%2A20PPC104) |
| `B5B-XH-A(LF)(SN)` | 1 | 455-B5B-XH-A-ND | 63329 | — | 1/1 | Active | $0.2000 @ 1 | $0.20 | CITED | OK | [page](https://www.digikey.com/en/products/detail/jst-sales-america-inc/B5B-XH-A/1530483) |
| `DIP05-1A72-12L` | 12 | DIP05-1A72-12L-ND | 56 | — | 1/1 | Active | $3.4480 @ 10 | $41.38 | CITED | OK | [page](https://www.digikey.com/en/products/detail/standex-meder-electronics/DIP05-1A72-12L/1949339) |
| `KF350-3.5-4P` | 1 | — | 0 | — | —/— | — | — | — | CITED | NOT-IN-CATALOG | [page](https://www.digikey.com/en/products/result?keywords=KF350-3.5-4P) |
| `PCC-SMP-K` | 1 | — | 0 | — | —/— | — | — | — | CITED | NOT-IN-CATALOG | [page](https://www.digikey.com/en/products/result?keywords=PCC-SMP-K) |

**digikey total: INCOMPLETE — $41.58 covers only 2 of 6 lines.** A total over a partial list is not a total. Only SOURCEABLE lines are summed: pricing a line you cannot order at the quantity you need (0 stock, or an MOQ above the need) gives a number that is arithmetically right and operationally false. The missing lines are named below.

## Amazon

*Method: Direct product links only, hand-recorded. No usable API (PA-API needs an affiliate account). ESTIMATED, always — stock and price are volatile and unverifiable.*

| MPN | qty | dist. part no. | stock | factory / lead | min/mult | lifecycle | unit @ break | extended | grade | status | link |
|---|---:|---|---:|---|---|---|---:|---:|---|---|---|
| `10FDZ-BT(S)(LF)(SN)` | 2 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `2.54-2*20PPC104` | 1 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `B5B-XH-A(LF)(SN)` | 1 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `DIP05-1A72-12L` | 12 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `KF350-3.5-4P` | 1 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `PCC-SMP-K` | 1 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |

**amazon total: INCOMPLETE — $0.00 covers only 0 of 6 lines.** A total over a partial list is not a total. Only SOURCEABLE lines are summed: pricing a line you cannot order at the quantity you need (0 stock, or an MOQ above the need) gives a number that is arithmetically right and operationally false. The missing lines are named below.

## Every Mouser catalog record seen, per part

One physical part has SEVERAL catalog records and they disagree — that is the expected case, not an anomaly, so every record is printed with its own numbers and the one this list picked is marked. A record whose manufacturer part number is not the authoritative MPN (modulo packaging/plating suffixes) is a **substitute proposal for a human**, never a sourced line (Q-IDENT).

| MPN asked | search | mfr part no. | Mouser no. | stock | lifecycle | factory / lead | same part? | used |
|---|---|---|---|---:|---|---|---|---|
| `10FDZ-BT(S)(LF)(SN)` | exact | `10FDZ-BT(S)(LF)(SN)` | N/A | **unparseable** | Obsolete | None / 0 Days | yes |  |
| `10FDZ-BT(S)(LF)(SN)` | broad | `10FDZ-BT` | 306-10FDZBTSLFSN | 37 | — | 0 / 180 Days | yes | **chosen** |
| `10FDZ-BT(S)(LF)(SN)` | broad | `10FDZ-BT(LF)(SN)` | 306-10FDZBTLFSN | 0 | New at Mouser | 0 / 180 Days | yes |  |
| `2.54-2*20PPC104` | `2.54-2*20PPC104`/Exact + `2.54-2*20PPC104`/None | — | — | — | — | — | — | **NOT-IN-CATALOG** |
| `B5B-XH-A(LF)(SN)` | exact | `B5B-XH-A(LF)(SN)` | 306-B5BXHALFSN | 30599 | — | 0 / 112 Days | yes | **chosen** |
| `B5B-XH-A(LF)(SN)` | broad | `B5B-XH-A-GU` | 306-B5B-XH-A-GU | 552 | — | 0 / 112 Days | NO — different part |  |
| `B5B-XH-A(LF)(SN)` | broad | `B5B-XH-AM(LF)(SN)` | 306-B5BXHAMLFSN | 534 | — | 0 / 112 Days | NO — different part |  |
| `B5B-XH-A(LF)(SN)` | broad | `B5B-XH-A-G` | 306-B5B-XH-A-G | 282 | — | 0 / 112 Days | NO — different part |  |
| `DIP05-1A72-12L` | exact | `DIP05-1A72-12L` | 876-DIP05-1A72-12L | 132 | — | 0 / 125 Days | yes | **chosen** |
| `KF350-3.5-4P` | `KF350-3.5-4P`/Exact + `KF350-3.5-4P`/None | — | — | — | — | — | — | **NOT-IN-CATALOG** |
| `PCC-SMP-K` | `PCC-SMP-K`/Exact + `PCC-SMP-K`/None | — | — | — | — | — | — | **NOT-IN-CATALOG** |

**Supply cautions (a stock number alone is not a plan):**

- `10FDZ-BT(S)(LF)(SN)` — distributor stock 37 is the whole near-term supply: FactoryStock 0, lead 180 Days — a re-order is not quick
- `B5B-XH-A(LF)(SN)` — distributor stock 30599 is the whole near-term supply: FactoryStock 0, lead 112 Days — a re-order is not quick
- `DIP05-1A72-12L` — distributor stock 132 is the whole near-term supply: FactoryStock 0, lead 125 Days — a re-order is not quick

## CANNOT SOURCE — every line that failed, and why

| MPN | qty | distributor | status | why |
|---|---:|---|---|---|
| `10FDZ-BT(S)(LF)(SN)` | 2 | digikey | **LOW-STOCK** | Q-STOCK: stock 0 is not > the 10 floor; stock 0 < the 2 needed; minimum order quantity 100 exceeds the 2 needed — the extended price shown is for 2, you would pay for 100; note: "Not kept in stock at DigiKey" — non-stocked, factory-order only, minimum 100 pieces at a manufacturer standard lead time of 16 weeks. ACTIVE and ZERO STOCK are not the same fact, and this is the row that proves it: the lifecycle field says Active on a part you cannot get for four months. |
| `10FDZ-BT(S)(LF)(SN)` | 2 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `2.54-2*20PPC104` | 1 | mouser | **NOT-IN-CATALOG** | 0 catalog records for '2.54-2*20PPC104' (Exact) or '2.54-2*20PPC104' (broad). This distributor does not list the part at all — which is a FINDING, not a stock figure |
| `2.54-2*20PPC104` | 1 | digikey | **NOT-IN-CATALOG** | catalog searched 2026-07-27, authoritative MPN not listed as its own orderable line: "Sorry, '2.54-2*20PPC104' did not return any results." Expected: this string is an LCSC HOUSE-BRAND DESCRIPTOR that happens to be the orderable MPN at LCSC, not a manufacturer part number any western distributor indexes. J_PI is explicitly substitutable (any 2x20 2.54mm female header), so this line is a catalog miss, not a sourcing wall. |
| `2.54-2*20PPC104` | 1 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `B5B-XH-A(LF)(SN)` | 1 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `DIP05-1A72-12L` | 12 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `KF350-3.5-4P` | 1 | mouser | **NOT-IN-CATALOG** | 0 catalog records for 'KF350-3.5-4P' (Exact) or 'KF350-3.5-4P' (broad). This distributor does not list the part at all — which is a FINDING, not a stock figure |
| `KF350-3.5-4P` | 1 | digikey | **NOT-IN-CATALOG** | catalog searched 2026-07-27, authoritative MPN not listed as its own orderable line: "Sorry, 'KF350-3.5-4P' did not return any results." DigiKey does not carry the Cixi Kefa 350 family at all. The board sanctions XY350-3.5-4P and DG350-3.5-4P as approved alternates (assembly.yaml disposition) — neither was searched here, because an alternate is a decision, not a lookup. |
| `KF350-3.5-4P` | 1 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `PCC-SMP-K` | 1 | mouser | **NOT-IN-CATALOG** | 0 catalog records for 'PCC-SMP-K' (Exact) or 'PCC-SMP-K' (broad). This distributor does not list the part at all — which is a FINDING, not a stock figure |
| `PCC-SMP-K` | 1 | digikey | **NOT-IN-CATALOG** | catalog searched 2026-07-27, authoritative MPN not listed as its own orderable line: The bare Omega MPN `PCC-SMP-K` is not listed as its own orderable line. What IS listed is six PACK-QUANTITY variants — PCC-SMP-K-5 / -50 / -100 and their -R counterparts. PCC-SMP-K-5 shows 210 in stock at $48.91 (product page 25639954, read 2026-07-27), but the page does not state whether that price is per pack of five or per piece, so the per-piece cost is UNRESOLVED and this is a substitute proposal for a human, not a sourced line. J_TC is DO-NOT-SUBSTITUTE (the chromel/alumel contacts ARE the cold-junction interface) — but a pack quantity of the same Omega part is a packaging question, not a substitution one. Resolve it before ordering. |
| `PCC-SMP-K` | 1 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |

## What each line is, and why it is on this list

| MPN | mfr | qty | refs | why self-supplied |
|---|---|---:|---|---|
| `10FDZ-BT(S)(LF)(SN)` | JST | 2 | interposer: J_CN1_JUMPER, J_MEMBRANE | interposer BOM row carries a BLANK LCSC; part.yaml sourcing.lcsc is empty — no fab-library line exists, so it is self-supplied |
| `2.54-2*20PPC104` | BOOMELE (Boom Precision Elec) | 1 | cooksense: J_PI | assembly.yaml not_assembled: J_PI (process_incompatible) — hand-soldered, you supply it |
| `B5B-XH-A(LF)(SN)` | JST | 1 | cooksense: J_LOADCELL | assembly.yaml not_assembled: J_LOADCELL (process_incompatible) — hand-soldered, you supply it |
| `DIP05-1A72-12L` | Standex-Meder Electronics | 12 | cooksense: K_D1, K_D2, K_D3, K_D4, K_PRESS, K_STOP, K_U1, K_U2, K_U3, K_U4, K_U5, K_U6 | assembly.yaml not_assembled: K_D1, K_D2, K_D3, K_D4, K_PRESS, K_STOP, K_U1, K_U2, K_U3, K_U4, K_U5, K_U6 (not_in_catalog) — hand-soldered, you supply it; cooksense BOM row carries a BLANK LCSC; part.yaml asserts not_on_assembly_bom; part.yaml sourcing.lcsc is empty — no fab-library line exists, so it is self-supplied |
| `KF350-3.5-4P` | Cixi Kefa | 1 | cooksense: J_ISOLOOP | assembly.yaml not_assembled: J_ISOLOOP (not_in_catalog) — hand-soldered, you supply it |
| `PCC-SMP-K` | Omega Engineering (Newport Electronics) | 1 | cooksense: J_TC | assembly.yaml not_assembled: J_TC (not_in_catalog) — hand-soldered, you supply it; cooksense BOM row carries a BLANK LCSC; part.yaml asserts not_on_assembly_bom; part.yaml sourcing.lcsc is empty — no fab-library line exists, so it is self-supplied |

## DigiKey: what would make these rows CITED

```
DigiKey HAS an API and this tool does not use it, because it needs OAuth 2.0
client credentials nobody has provided and an agent cannot create an account or
obtain a key. To promote every DigiKey row from ESTIMATED/OWED to CITED:

  1. Sign in at https://developer.digikey.com/ with a DigiKey account.
  2. Create an Organization, then a PRODUCTION app (Sandbox returns
     structurally-correct but incomplete data — do not source from it).
  3. Subscribe the app to **Product Information V4**.
  4. Copy the app's **Client ID** and **Client Secret**.
  5. Append them to `<repo>/.secrets/digikey.env` (mode 600; `.secrets/` is
     already gitignored):
         DIGIKEY_CLIENT_ID=...
         DIGIKEY_CLIENT_SECRET=...
  6. Tell me, and the 2-legged flow (POST client_id + client_secret +
     grant_type=client_credentials to https://api.digikey.com/v1/oauth2/token,
     then GET /products/v4/search/{mpn}/productdetails) becomes a peer of the
     Mouser path.

Until then DigiKey numbers come only from a PRODUCT PAGE a human opened,
recorded in `01_docs/sourcing/manual_quotes.yaml` with its URL and read date.
NEVER from a search-results snippet — that is the GHR-10V-S defect.
```

