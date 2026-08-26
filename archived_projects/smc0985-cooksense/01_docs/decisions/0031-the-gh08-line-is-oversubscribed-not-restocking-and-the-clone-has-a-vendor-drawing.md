# ADR-0031 — `C265111` is OVERSUBSCRIBED, not "restocking": the escape route is
# a purchasing decision with a real vendor drawing, and the board is NOT ordered

---
id: 0031
date: 2026-07-31
status: accepted
---

tags: sourcing, parts, connectors, thermal, envelope, gates, order-day
relates: ADR-0029/0030 (the 65 °C envelope and the part that binds it — this
ADR checks the connector candidates against that envelope), ADR-0024 (pod
mismate geometry, written about the GH FAMILY — the axis a clone shroud falls
outside of)
amends: `02_parts/SM08B-GHS-TB/part.yaml` (`layout` factual defect, `gotchas`),
`03_src/cooksense/rules/assembly.yaml` (`sourcing_plan:` prose)
supersedes nothing. **`cooksense-v1.7-2026-07-30` is SEALED and IMMUTABLE;
nothing here edits it. No v1.8 is cut, because nothing here clears the block.**

## Context — the re-measurement that was supposed to clear the block deepened it

`cooksense-v1.7-2026-07-30` sealed `DESIGN: PASS` / `SOURCING: BLOCKED-1` on one
line: `C265111` (JST `SM08B-GHS-TB(LF)(SN)`, `J_THERM_A`/`J_THERM_B`, 2/board),
measured 2026-07-30 at **stock 5 / MOQ 21**. The seal is correct — the A-BUY
rule exists so a non-orderable release may seal, loudly. The open question was
whether a day of restocking cleared it.

**It did not. MEASURED 2026-07-31, two instruments that share no code:**

1. A MOQ-aware probe written for this pass — raw `urllib` against
   `selectSmtComponentList`, 18:46:23Z and again 18:58:14Z. Controls in the
   same run: POSITIVE `C5620` → **5206**; NEGATIVE `C99999999` →
   **NO_EXACT_MATCH over 25 fuzzy rows**. `controls_ok = True`. Its reading
   is `06_build/cache/gh08_sourcing_2026-07-31.json` (volatile, TTL 6 h,
   gitignored); the method is specified under *How to reproduce* below.
2. `skills/jlcpcb-fab/scripts/jlc_stock_check.py` against the sealed archive's
   own `fab/bom_jlc.csv`, UNPIPED, **RAW EXIT 1**, verbatim row:
   `LOW_STOCK(0)     C265111    x2   SM08B-GHS-TB    expand stock=0`.

| LCSC | brand | MPN | stock | **MOQ** | preMOQ | **canPresale** | buyable at any qty |
|---|---|---|---|---|---|---|---|
| **`C265111`** (the BOM) | JST | SM08B-GHS-TB(LF)(SN) | **0** | **21** | 21 | **−1285** | **NO** |
| `C22391766` | JST | SM08B-GHS-TB | 0 | 444 | 444 | 0 | NO |
| `C42376901` | SHOU HAN | SH-SM08B-GHS-TB(LF)(SN) | 5868 | 1 | 137 | 5784 | yes |
| `C54110154` | XYECONN | XY-SM08B-GHS-WB | 968 | 1 | 88 | 966 | yes |
| `C133062` | JST | BM08B-GHS-TBT(LF)(SN) | 32068 | 1 | 25 | 30350 | yes |

The stock sequence is now **0 → 5 → 0 → 5 → 5 → 0** over six readings in 72 h on
a board whose md5 never moved, and **`minPurchaseNum` has read 21 at every one
of the six.** v1.7 §5-0 is right that the MOQ is the blocker and always was.

### The one genuinely new fact, and it points the wrong way

**`canPresaleNumber` = −1285 on `C265111`.** MEASURED; it is the only negative
in the set — the three in-stock candidates all read positive and approximately
equal to their own stock (5784/5868, 966/968, 30350/32068).

DERIVED, and flagged as derived because JLC documents none of these fields:
a presale headroom of −1285 against a stock of 0 reads as **~1285 units of
already-committed demand queued ahead of any incoming reel.** If that reading is
right, the next delivery does not become buyable stock — it is spoken for, and
the line does not cross 21 on the first restock.

**This is the first evidence this project has ever had bearing on *when* the
line crosses 21, and it points the wrong way.** v1.7's ORDER_README says
`C265111` "is restocking rather than discontinued — but that says nothing about
*when* it crosses 21." That sentence was honest and is now improvable: the
catalog's own presale field says there is a backlog. **INHERITED CAVEAT: this is
an inference from an undocumented field, not a vendor lead-time quote.** It is
not strong enough to declare the part dead. It IS strong enough that "wait for
the next reel" should stop being described as the low-risk default without a
lead time from the distributor.

## The candidate ledger — every GH-08 SMD row JLC lists, and why each lost

Swept `SM08B-GHS-TB`, `SM08B-GHS`, `GHS-TB 8`, `BM08B-GHS-TB`, `SM08B-GHDS-TB`;
9 unique codes, 5 of them plausibly relevant. Per the `02_parts` contract,
**rejected candidates get no committed PDF — the binary is worthless, the reason
is not** — so the reasons live here and no `02_parts/<MPN>/` directory is
created for any of them.

### `C133062` — JST `BM08B-GHS-TBT(LF)(SN)`, stock 32068, MOQ 1 — REJECTED: **wrong mounting**

The genuine article, deep stock, MOQ 1, real datasheet. It is the **top-entry**
variant: catalog `Mounting Type = Surface Mount,**Vertical**` against the
board's `Surface Mount, Right Angle`. `02_parts/SM08B-GHS-TB/part.yaml` already
carries this as gotcha #1 — *"SM = side-entry = KiCad Horizontal (right-angle)
SMD; NOT top-entry (that is BM08B-GHS-TBT, a different footprint)"* — and the
gotcha is correct. Different land, different mating direction, so the pod
pigtails leave the board on a different axis.

**This is a COPPER REVISION, not a BOM swap.** Recorded because it is the only
genuine-JST escape that exists at all, and a future pass should not have to
rediscover both that it exists and that it costs a board rev.

### `C54110154` — XYECONN `XY-SM08B-GHS-WB`, stock 968, MOQ 1 — REJECTED: two independent reasons

New this pass; not considered by any previous pass. Right-angle SMD, 1.25 mm,
1×8P, so it survives the first filter. It fails on:

1. **NO DATASHEET EXISTS.** `dataManualUrl` is `None` **and**
   `dataManualFileAccessId` is the empty string — both routes empty on the
   product record. That is a **declared catalog absence**, which is the one form
   of negative evidence this repo accepts. With no drawing there is no pin-map
   figure, no land pattern and no ratings page, so the substitution bar
   (`part.yaml` with the pin map read off a FIGURE) **cannot be met at all**.
2. **`Contact Material = Brass`**, where the incumbent JST and the SHOU HAN
   candidate are both **Phosphor bronze**. Also `Y-Width 4.05 / Z-Height 4.35`
   against the incumbent's `4.13 / 4.25` — a different body, and the MPN suffix
   is **`-WB`, not `-TB`**.

### `C22391766` — JST `SM08B-GHS-TB`, stock 0, MOQ 444 — REJECTED: stock 0, and a worse MOQ than the part it would replace.

### `C42376901` — SHOU HAN, stock 5868, MOQ 1 — **NOT REJECTED, NOT ADOPTED: it is the user's purchasing decision, and this ADR strengthens its evidence without taking it**

v1.7 §5-0 already carries this candidate with a measured land-pattern fit. What
that analysis had was **JLC's own recommended land, read out of the EasyEDA
`packageDetail` pad records** — a JLC-library artifact. What it did **not** have
was anything from the vendor. Two things follow.

**(1) A REAL SHOU HAN CUSTOMER DRAWING EXISTS, and v1.7 did not know it.**
`dataManualUrl` is the empty string on the JLC row — which is what made it look
absent — but `dataManualFileAccessId` is populated, and the EasyEDA product API
resolves it: a 7-page PDF, `sha256
866a52b6242453fb7b99eca62a87fc06590c5692845ffc8eb81ef3cbd313ea58`, title block
*Shenzhen Shouhan Technology Co., Ltd / CUSTOMER DRAWING / P/N
SH-SM08B-GHS-TB(LF)(SN) / 12502 SERIES / REV. 1.00 / 2020-03-22 / sheet 1/1*.

**(2) The drawing INDEPENDENTLY CORROBORATES v1.7's land numbers.** Sheet 1's
recommended-land figure (labelled 印制线路板, "printed circuit board") dimensions
the signal pad **0.7 × 1.8 mm** and the mechanical-tab pad **2.5 mm** tall, with
`DIM.B = 8.75` for the 8-circuit row (= 7 × 1.25 pitch) and `DIM.A = 13.25`.
v1.7 §5-0's table, derived from JLC's EasyEDA record, states **0.700 × 1.800**
signal and **1.000 × 2.500** tab. **Two sources that share no method agree**
(canon M1). The geometric half of the substitution argument is now
double-sourced instead of single-sourced.

**RATINGS — the axis §5-0 has NO ROW FOR, and it should have had one first.**

| | JST `C265111` — repo's own sha256-pinned `eGH.pdf` p.1 "Specifications" | SHOU HAN `C42376901` — vendor drawing sheet 1/1 |
|---|---|---|
| temperature | **−40 … +105 °C** (incl. temperature rise in applying current) | **−25 … +85 °C** |
| voltage | 50 V AC/DC | **125 V AC/DC** |
| current | 1.0 A AC/DC (AWG #26) | 1 A |
| contact resistance | 30 mΩ max initial / **50 mΩ max after test** | 20 mΩ max (**no after-test figure published**) |
| insulation resistance | 100 MΩ min | 100 MΩ min |
| withstanding voltage | 500 V AC for 1 minute | 500 V AC/minute |
| housing | PA9T | LCP, UL94V-0 |
| contacts | phosphor bronze | phosphor bronze, bright tin 60 µ″ min |

**Checked against the declared envelope FIRST, as the DIP05 lesson requires.**
The board declares `Ta = 65 °C` with a 75 °C SURVIVE corner (ADR-0029), and
ADR-0030 established that **`DIP05-1A72-13L` at −20…+70 °C is the unique
minimum** across all 47 part dossiers. The SHOU HAN part at −25…+85 °C is
**wider than the relay at both ends** (−25 < −20, +85 > +70), so **the
substitution does not move the board's envelope**: the relay still binds, and
the beacon's existing rule — that passing bench gate B1–B6 reopens at most
65 → 70 °C, never 75 °C, because above 70 °C means re-rating twelve relays —
is unchanged by it.

**Said plainly, because it is a real narrowing even though it does not bind:**
the clone gives up **20 K at the top and 15 K at the bottom** against the
genuine part. At the 75 °C survive corner the genuine connector holds 30 K of
headroom and the clone holds 10 K. Nothing on this board is rated to reach
either, but a future revision that re-rates the relays would meet the connector
next, and it would meet the clone 20 K sooner.

**THE DISTRIBUTOR TEMPERATURE FIELD IS BOILERPLATE AND MUST NOT BE USED HERE.**
JLC's structured `Operating Temperature` attribute reads **`-25℃~+85℃` on all
four candidates — including `C265111`, whose own manufacturer drawing (in this
repo, hash-pinned) says −40…+105 °C.** So that field (a) is demonstrably wrong
on the one part where we hold the drawing, and (b) reads identically on the
genuine part and on every clone, so it cannot distinguish them in either
direction. It is Q-SNIPPET-class evidence. **Do not "verify" a clone with it,
and do not "correct" `02_parts/SM08B-GHS-TB/part.yaml` to match it** — the
part.yaml is right and the catalog is wrong.

**WHAT IS STILL NOT VERIFIED, AND IT IS THE SAME THING v1.7 NAMED:** whether a
genuine JST `GHR-08V` plug from a third-party pod pigtail **seats and retains**
in a SHOU HAN shroud. Pad correspondence is not mate compatibility; ADR-0024's
mismate geometry is written about the GH FAMILY, and a clone shroud is outside
what it measured. **No amount of catalog reading closes this. It needs one part
and five minutes on a bench**, and it is the user's call, exactly as v1.7 says.

## A factual defect found on the way, and it was propagating

`J_THERM_A` / `J_THERM_B` are **NOT thermocouple connectors.** MEASURED with
`pcbnew` over every pad of both refs on the sealed v1.7 board:

```
J_THERM_A  1=3V3_SW_A 2=GND 3=SDA_A 4=SCL_A
           5=TH_CAM_A 6=TH_MOUNT_A 7=TH_PORT_A 8=SHIELD_DRAIN   MPx2=GND
J_THERM_B  1=3V3_SW_B 2=GND 3=SDA_B 4=SCL_B
           5=TH_CAM_B 6=TH_MOUNT_B 7=TH_PORT_B 8=SHIELD_DRAIN   MPx2=GND
J_TC       1=TC_POS_IN 2=TC_NEG_IN        (Omega_PCC-SMP-K_TypeK_PCpin)
```

Not one thermocouple net touches either ref. `02_parts/SM08B-GHS-TB/part.yaml`
nonetheless said *"Carries the thermocouple pairs to the MAX31856: route each
TC+/TC- pad pair as a tight differential"* — **J_TC's job, described on
J_THERM's page.** There is no TC pair on this connector to route.

**It was propagating**: an agent brief dated 2026-07-30 opened by calling
`J_THERM_A`/`J_THERM_B` "thermocouple connectors on a board with a
mains-adjacent isolation barrier" and reasoned about this very substitution from
there. **It matters because the two parts fail differently.** On a real TC
connector the governing substitution risk is CONTACT METALLURGY — dissimilar
metals at the junction form a parasitic thermocouple in series with a microvolt
signal, so a clone with different contact alloy is disqualifying, which is
exactly why `J_TC` is declared DO-NOT-SUBSTITUTE. On **this** connector the
signals are 3.3 V logic, I²C and three ratiometric NTC divider taps, so the
governing term is contact RESISTANCE, not EMF. DERIVED against this board's own
divider legs (`R_REF0` 10 k, `R_CLMPA` 22 k, `R_OPENT` 62 k, `R_OPENB` 100 k):
even JST's worst published after-test contact resistance, 50 mΩ, is
0.050/10000 = **5.0 × 10⁻⁶** of the 10 k leg. Negligible by four orders. These
are also all SELV nets — nothing here crosses the isolation barrier, so the
connector's voltage rating is not a barrier term either.

Corrected in `part.yaml` as a dated correction rather than a silent reword.

## Decision

**(a) REPORT `BLOCKED-SOURCING` AS THE TRUE CURRENT STATE. DO NOT CUT v1.8.
CHOSEN.**

Nothing measured this pass clears the block. The genuine part is at stock 0
with an MOQ of 21 and a negative presale headroom; the only drop-in candidate
turns on a physical check nobody has performed. **Adopting the substitution to
make the verdict green is precisely the move this project has paid for before.**
A partial result honestly reported is worth more than a passing claim.

**(b) Adopt `C42376901` into the BOM and cut v1.8 — REJECTED.** It would convert
a purchasing decision the user owns into a design change made on their behalf,
on the strength of an unverified retention claim, and it would spend a release
cut to do it. The two owed fixes that were to ride along with v1.8 (task #53's
`kicad_prl` MANIFEST row and the bijection assert; producing `fab/` from the
fixed exporter) stay owed and **still ride the next cut, whenever the block
clears** — they were judged not worth a respin alone and that judgement holds.

**(c) Re-spec to `C133062` (genuine JST, 32068 in stock) — REJECTED for now**,
but recorded as the standing fallback: it is a copper revision, and a copper
revision is not the right answer to a sourcing problem while a drop-in
candidate and a restock are both live.

## How to reproduce — the probe method, on order day

The probe is **not committed**: `06_build/` forbids anything unregenerable
("if `rm -rf 06_build/` would lose information, that information is in the wrong
folder"), and only its volatile READING belongs in `cache/`. So the method is
specified here, which is the folder that keeps reasons.

POST to `https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/`
`selectSmtComponentList` with `{"currentPage":1,"pageSize":25,"keyword":<CODE>}`,
take the row whose `componentCode` equals `<CODE>` **exactly** (the endpoint is a
fuzzy search — a keyword with no exact row still returns 25 neighbours, which is
what makes the negative control meaningful), and read:

| field | why it is read |
|---|---|
| `stockCount` | how many exist. The ONLY field `jlc_stock_check.py` reads |
| `minPurchaseNum` | **the smallest order the catalog accepts. THE BLOCKER.** |
| `preMinPurchaseNum` | the MOQ on the pre-sale/backorder path |
| `canPresaleNumber` | headroom on that path; NEGATIVE means oversubscribed |
| `attributes[]` | the STRUCTURED specs — never the `describe` snippet |
| `dataManualUrl` + `dataManualFileAccessId` | whether a datasheet exists at all; **both empty is a declared catalog absence, and an empty URL with a populated file id is NOT** |

**A purchase is possible only when `stockCount >= minPurchaseNum`.** That is the
predicate, and it is not the A-STOCK floor.

Rules that make the run evidence rather than a number: pace ~1.4 s between
calls; run a POSITIVE control (`C5620`) and a NEGATIVE control (`C99999999`) in
the SAME run and record both, so a zero cannot be confused with a dead endpoint;
and do NOT import `jlc_stock_check` (canon M1 — when the two agree that is two
instruments; sharing code makes it one instrument twice). Write the result to
`06_build/cache/` with a `fetched_at`, an `expires_at` and a short TTL.

The SHOU HAN drawing is reachable by GET on
`https://easyeda.com/api/products/<CODE>/components?version=6.4.19.5` and
pulling the `.pdf` URL out of the JSON — the route that works when JLC's own
`dataManualUrl` is blank.

## Consequences

- **The board remains DESIGN-SOUND and NOT ORDERABLE.** v1.7 stays the current
  release and its §5-0 remains correct; this ADR adds the ratings table, the
  vendor drawing and the presale finding that §5-0 did not have.
- **What would change the verdict, exactly:** `C265111` `stockCount` reaching **21 or more**
  (not 10 — the gate's floor is the wrong number to watch), *or* a bench
  mate/pull check passing on one `C42376901` against a genuine `GHR-08V`
  pigtail, *or* a decision to take the copper revision to `C133062`.
- **`C587657` (Molex 436500224, `J_PWR`, single-source) has fallen again:
  130 → 80 → 70 → 70 → 43**, MEASURED in the same run, with a presale headroom
  of **12**. It still clears the 5 × qty floor and is NOT blocking. It is now
  the thinnest line on the BOM with no drop-in fallback (the only alternate,
  C293740, is through-hole = a footprint change = copper). Re-specify before it
  reaches the build quantity, not after it reaches zero.
- **A gate hole is now on the record (not fixed here — `skills/` is outside this
  partition).** `jlc_stock_check.py` reads `stockCount` and never
  `minPurchaseNum`, so **a line can PASS A-STOCK and be unbuyable at every
  quantity**: had `C265111` read stock 15, the tool would have printed `OK`
  (15 clears the floor of 5 × 2) while MOQ 21 still made a purchase impossible. That is not
  hypothetical for this board — it is the exact shape of its blocker, and the
  only reason the tool has been right so far is that stock never got high enough
  to expose it. The probe below reads the MOQ fields and is the
  instrument this pass used; the fix belongs in the fleet tool. It is NOT
  committed under `06_build/`, whose contract forbids anything unregenerable
  ("if `rm -rf 06_build/` would lose information, that information is in the
  wrong folder") — only its volatile READING lives in `cache/`.
