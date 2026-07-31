# GH-08 clone mate/retention confirm — the physical-part gate for `C42376901`

status: **OPEN — WRITTEN 2026-07-31, NOT YET EXECUTED.** Nothing here is
adopted. `07_releases/cooksense-v1.7-2026-07-30/fab/bom.csv` still names
`C265111` and will keep naming it until this gate PASSES and a v1.8 is cut.
gate: the substitution `C265111` → `C42376901` on `J_THERM_A` / `J_THERM_B`.
blocks: **the fab ORDER of cooksense.** Not the seal — v1.7 is sealed and
      correct — and not the design. `SOURCING: BLOCKED-1` is the honest
      current state and stays so until this document has numbers in §5.
decided by: the USER, 2026-07-31 (bench-check the clone in preference to
      spending a copper revision on the top-entry `C133062`).
written: 2026-07-31
part under test: SHOU HAN `SH-SM08B-GHS-TB(LF)(SN)` — LCSC `C42376901`
incumbent: JST `SM08B-GHS-TB(LF)(SN)` — LCSC `C265111`, `02_parts/SM08B-GHS-TB/`
ledger: `01_docs/decisions/0031-*.md` (the candidate sweep and why each lost)

---

## 0. Why this gate exists, and why it is the ONLY thing left on this line

`C265111` is **design-sound and unbuyable.** Six readings over 72 h ran
`0 → 5 → 0 → 5 → 5 → 0` with **`minPurchaseNum` = 21 at every one of them**, and
the 2026-07-31 read added `canPresaleNumber` = **−1285** — the only negative in
the candidate set, reading as ~1285 units of committed demand queued ahead of
any incoming reel. A purchase is possible only when `stockCount ≥ minPurchaseNum`;
that predicate has never once been true, and the presale field says the next
reel does not make it true either. The board needs **2 per board × 5 boards = 10**.

The user has chosen the SHOU HAN clone (`C42376901`, stock 5868, **MOQ 1**) as
the cheapest path to an orderable board.

**Everything about that substitution that CAN be checked from a terminal HAS
been checked, and it passes.** §2 records the evidence so this bench does not
re-derive it. What remains is one question no amount of catalog reading closes:

> **Does a genuine JST `GHR-08V-S` plug seat, latch and stay latched in a
> SHOU HAN shroud — and does it land circuit 1 on the pad this board calls 1?**

Pad correspondence is not mate compatibility. `01_docs/decisions/0024-*.md`'s
mismate geometry is written about the GH **family**, and a clone shroud is
outside what it measured. This needs one part and one hour on a bench.

---

## 1. WHAT TO ORDER — exact codes, exact quantities

All five lines below are **MOQ 1 and in stock**, so the whole test-article set
goes in one LCSC/JLCPCB parts cart today. Prices are the 2026-07-31 first tier.

| # | what | LCSC | qty | unit | ext | why this line exists |
|---|---|---|---|---|---|---|
| **A** | SHOU HAN `SH-SM08B-GHS-TB(LF)(SN)` | **`C42376901`** | **10** | $0.0831 | $0.83 | **THE ARTICLE UNDER TEST.** 10 = 2 boards' worth for the fit checks, plus spares for the destructive mate-cycle test in GH7 |
| **B** | JST `GHR-08V-S` plug housing, 8 circuit | **`C485357`** | **5** | $0.0683 | $0.34 | **THE REFERENCE MATE.** This is the housing `02_parts/SM08B-GHS-TB/part.yaml` already specifies the pod harness is built to. It must be **genuine JST** — the whole question is clone-shroud-against-genuine-plug |
| **C** | JST `SSHL-002T-P0.2` crimp contacts | **`C189897`** | **100** | $0.0132 | $1.32 | genuine JST contacts, 8 per plug. 100 covers 5 plugs plus re-crimps. **Do not substitute these either** — GH1/GH6 measure the contact, not just the housing |
| **D** | JST `BM08B-GHS-TBT(LF)(SN)` | **`C133062`** | **5** | $0.4599 | $2.30 | **THE GENUINE-JST CONTROL — see §1.1. NOT a board part.** Bought only so every force and resistance number has a genuine-JST twin measured on the same rig with the same plug |
| **E** | Molex `436500224` | **`C587657`** | **10** | $0.6471 | $6.47 | **UNRELATED TO THIS GATE, RECOMMENDED ANYWAY — see §8.** `J_PWR`, single-source, no drop-in, fallen 130 → 80 → 70 → 70 → **43** |

**Bench-article subtotal (A–D): $4.79.** With E: $11.26. Plus shipping.

Where from: **LCSC / JLCPCB's own parts catalogue**, the same cart the board's
assembly parts come from. Every code above was read 2026-07-31 from the
product record via the ADR-0031 declared method (raw `selectSmtComponentList`,
positive control `C5620` → 5206, negative control `C99999999` → no exact row
over 25 fuzzy neighbours, **`controls_ok = True`**). The reading is
`06_build/cache/gh08_mate_articles_2026-07-31.json`, **TTL 6 h — re-read before
you actually place the order.** No stock, price or MOQ from this section is
committed into any `part.yaml`; that is what the cache is for.

### 1.1 Why buy a top-entry JST header you cannot put on the board

`C133062` is genuine JST, MOQ 1, 32068 in stock — and it is **top-entry**, so
adopting it onto the board is a copper revision (ADR-0031 rejects it for that
reason, and that rejection stands). But **the mating interface is the same GH
interface**: JST's own `eGH.pdf` p.3/p.4 tables list the top-entry and
side-entry headers for a given circuit count side by side against the same
`GHR-08V-S` housing and the same `A`/`B` dimensions. Only the board mounting
differs.

So for **$2.30 you buy a genuine-JST shroud to measure against**, and every
number in §3 stops being a lone reading against a spec sheet and becomes a
**comparison between two shrouds on one rig with one plug** — which is canon M1
(checker and checked must not share a method) applied to a bench instead of to
code. **The genuine `C265111` cannot serve as that control, because you cannot
buy it. That is the entire problem.** `C133062` is the closest genuine article
that money can get today.

### 1.2 Tools

| tool | what for | if you do not have one |
|---|---|---|
| digital caliper (0.01 mm) | GH2 | — |
| **force gauge, 0–50 N** | GH4, GH5 | GH4 has a **zero-instrument form**: hang a mass. See GH4 |
| **4-wire milliohm meter** | GH6 | pass 100 mA and read millivolts on a DMM: 20 mΩ ⇒ **2.00 mV**. See GH6 |
| DMM with continuity/ohms | GH3 | — |
| JST `WC-160` hand crimper, or any 1.25 mm GH/PH crimper | building the plug | **solder the wire into the contact's barrel** and push it into the housing until the lance clicks. The lance and the housing are what GH4 measures; a soldered barrel does not change them. Say which you did in §5 |
| A4 printer | GH1 | GH1 can be skipped if you have GH2's caliper numbers, but GH1 is the cheaper check |

---

## 2. THE EVIDENCE ALREADY IN HAND — do not re-derive any of this

### 2.1 A real SHOU HAN vendor drawing exists and has been recovered

JLC's `dataManualUrl` is **blank** for `C42376901` while `dataManualFileAccessId`
is **populated** — which is what made the drawing look absent to two earlier
passes. It is not absent. The EasyEDA product API resolves it:

```
GET https://easyeda.com/api/products/C42376901/components?version=6.4.19.5
    → pull the .pdf URL out of the JSON
sha256 866a52b6242453fb7b99eca62a87fc06590c5692845ffc8eb81ef3cbd313ea58
7 pages, A4. Sheet 1 = CUSTOMER DRAWING, 深圳市首韩科技有限公司 /
SHENZHEN SHOUHAN TECHNOLOGY CO., LTD, P/N SH-SM08B-GHS-TB(LF)(SN),
12502 SERIES, REV 1.00, 2020-03-22, SHEET 1/1.
Sheets 2–7 = the matching SPECIFICATION (承认书), same P/N.
```

**Grade: MEASURED** — the file was fetched and hashed in this repo on
2026-07-31, and the hash matches the one ADR-0031 recorded independently.
It is **not committed**: `02_parts/contracts.md` forbids a committed PDF for a
part that is not on the board, and this part is not on the board yet. Re-fetch
it by the route above and check the hash; if the hash differs, the vendor
revised the drawing and **every number below must be re-read before use.**

### 2.2 The land: two sources that share no method agree

| | our board, MEASURED with `pcbnew` over the SEALED v1.7 `.kicad_pcb` | SHOU HAN sheet 1, recommended land (印制线路板) |
|---|---|---|
| signal pad | **0.600 × 1.700** | **0.700 × 1.800** |
| tab pad | **1.000 × 2.700** | **1.000 × 2.500** |
| pitch | **1.2500** | 1.25 |
| pad 1 → pad 8 span | **8.7500** | `DIM.B = 8.75` |
| overall / tab-to-tab datum | tab centres **12.4500** apart | `DIM.A = 13.25` (body) |
| signal row → tab row | **3.2000** | 3.16 (from the drawing's own pad centres) |

**The board's land is a subset of the vendor's recommendation in both
directions that matter** — pads 0.1 mm narrower and 0.1 mm shorter, tab pad
0.2 mm *taller*, rows 0.04 mm further apart. Same pitch, same span, same datum.
The consequence is slightly less solder fillet, not a fit problem: the vendor
draws its terminal foot at **0.2 ± 0.05 mm** wide (drawing sheet 1, front view),
i.e. one third of our 0.600 mm pad.

This is the corroboration ADR-0031 added. v1.7 §5-0's fit argument was derived
from JLC's EasyEDA `packageDetail` pad records — a JLC-library artifact. The
vendor drawing is a **second source that shares no method with it**, and it
agrees. **GH1/GH2 below are therefore a confirmation, not a discovery.**

### 2.3 Ratings — and the envelope does not move

| | JST `C265111`, from this repo's sha256-pinned `eGH.pdf` p.1 | SHOU HAN `C42376901`, vendor drawing sheet 1 + spec §5 |
|---|---|---|
| temperature | **−40 … +105 °C** | **−25 … +85 °C** |
| voltage | 50 V AC/DC | 125 V AC/DC |
| current | 1.0 A AC/DC (AWG #26) | 1 A AC/DC |
| contact resistance | 30 mΩ initial / **50 mΩ after test** | **≤ 20 mΩ** (initial *and* after heat/cold/humidity/salt, spec §7.3–§7.7) |
| insulation resistance | 100 MΩ min | ≥ 100 MΩ |
| withstanding voltage | 500 V AC, 1 min | ≥ 500 V AC/minute |
| **plug-in force** | **not published in `eGH.pdf`** | **≤ 3 N per pin** (spec §6.3) |
| **plug-out force** | **not published in `eGH.pdf`** | **≥ 0.5 N per pin** (spec §6.4) |
| contact retention in housing | not published in `eGH.pdf` | ≥ 10 N per pin (spec §6.1/§6.2) |
| housing | PA9T | LCP, UL94V-0 |
| contacts | phosphor bronze | phosphor bronze, bright tin 60 µ″ min |
| applicable wire | AWG #30–#26 | AWG #32–#28 |

**The swap does not move this board's thermal envelope.** The board declares
`Ta = 65 °C` (ADR-0029) and ADR-0030 established that **`DIP05-1A72-13L` at
−20 … +70 °C is the unique minimum across all 47 part dossiers.** The clone at
−25 … +85 °C is **wider than the relay at both ends**, so the relay still binds
and the existing rule — that passing `ORDER_README` §7b B1–B6 reopens at most
65 → 70 °C, never 75 °C — is untouched.

Said plainly, because it is a real narrowing even though it does not bind: the
clone gives up **20 K at the top and 15 K at the bottom** against the genuine
part. A future revision that re-rates the relays would meet the connector next,
and would meet the clone 20 K sooner.

Note the asymmetry in the force rows, because it shapes §3: **the clone
publishes an insertion/withdrawal force spec and JST's catalogue sheet in this
repo does not.** That is why §3's thresholds are the clone's own published
numbers (holding a vendor to its own claim) *and* a side-by-side comparison
against `C133062` (a second instrument).

### 2.4 🛑 A TRAP — the distributor temperature field is boilerplate, and it is WRONG

**JLC's structured `Operating Temperature` attribute reads `-25℃~+85℃` on ALL
FOUR GH-08 candidates — INCLUDING the genuine JST `C265111`, whose own
manufacturer drawing (in this repo, hash-pinned) says −40 … +105 °C.**

So that field is (a) **demonstrably wrong on the one part where we hold the
drawing**, and (b) **identical on the genuine part and on every clone**, so it
cannot distinguish them in either direction. It is Q-SNIPPET-class evidence.

- **Do not "verify" the clone with it.** It would look like agreement and mean
  nothing.
- **Do not "correct" `02_parts/SM08B-GHS-TB/part.yaml` to match it.** The
  part.yaml is right and the catalogue is wrong. That gotcha is already written
  into the file; leave it there.
- The clone's real rating, −25 … +85 °C, comes from **its own vendor drawing**,
  not from this field. It happens to be the same numbers. That coincidence is
  exactly what makes the field dangerous.

---

## 3. THE MEASUREMENTS — GH1 … GH7

Take them in order; GH1–GH3 are cheap and two of them are hard stops.
Do all of GH4/GH5/GH6 **twice**: once on a `C42376901` (A) and once on a
`C133062` (D), same plug, same rig, same session. The paired reading is the
evidence; the absolute reading is only the sanity floor.

---

### GH1 — land fit on the board's own 1:1 print  *(cheap, no caliper)*

**Print** `07_releases/cooksense-v1.7-2026-07-30/pdf/pcb_layers.pdf`
**page 1 of 11** — that is **F.Cu**, the top copper, viewed from the component
side. (MEASURED: pages 1–4 are the four copper layers in stackup order, by ink
fraction; page 1 is the dark top-copper plot. If the page you printed shows
only outlines and text with no solid copper, you have a silkscreen page.)

Also print **`pdf/assembly.pdf`** — it carries the **F.Fab pin-1 chevron** that
GH3 uses. It has no pads and no holes; it is not a substitute for page 1.

**Print settings, both files:** A4 **landscape**, scale **100% / "Actual
size"**. **Fit-to-page OFF. Shrink-oversized-pages OFF. Auto-rotate-and-centre
OFF.** Any of those silently scales the print and makes the overlay a lie.

**Calibrate before you trust it** (all MEASURED off the sealed board):

| on | measure | must read | tolerance |
|---|---|---|---|
| page 1 | centre-to-centre, the two ø2.70 mounting holes on the **long bottom edge** (`H1`→`H2`) | **170.00 mm** | ±0.3 |
| page 1 | `J_THERM_A` pad 1 centre → pad 8 centre | **8.75 mm** | ±0.2 |
| page 1 | `J_THERM_A` west tab-pad centre → east tab-pad centre | **12.45 mm** | ±0.2 |
| page 1 | `J_THERM_A` pad 1 → `J_THERM_B` pad 1 | **22.00 mm** | ±0.3 |
| page 1 | board outline (from the Edge_Cuts extent) | **188.10 × 92.10 mm** | ±0.4 |

Outside tolerance: **reprint.** The driver scaled it.

**The overlay test.** Lay the connector **tails DOWN** on page 1 over
`J_THERM_A`. Page 1 is plotted "seen from the component side", which is the
same view, so **nothing is mirrored — do not flip the page and do not flip the
part.**

There is **only one orientation that can fit**: the eight signal pads and the
two tab pads sit on **opposite sides of the body, 3.20 mm apart, and are
different sizes**. If you have the part end-for-end, the tails land on the tab
pads and nothing lines up.

| | |
|---|---|
| **PASS** | all eight tails sit inside the eight printed rectangles **and** both solder tabs sit on the two large rectangles, **simultaneously, without forcing the part sideways** |
| **FAIL** | tails walk off the rectangles across the row (pitch error), or a tab misses its pad |

---

### GH2 — caliper, on the part  *(confirmation of §2.2, not discovery)*

Digital caliper, mm. One part fully; then repeat GH2-a and GH2-e on a second
part to catch a mixed bag.

| # | measure | expected | PASS band | CONDEMNS if |
|---|---|---|---|---|
| **a** | tail 1 centre → tail 8 centre (7 pitches) | **8.75** | 8.60 – 8.90 | 7.50 → a **7-way** part · 10.00 → a **9-way** part. **Wrong part — STOP** |
| **b** | pitch, from (a) ÷ 7 | **1.250** | 1.24 – 1.26 | ≤ 1.23 or ≥ 1.27 — the row will not line up |
| **c** | body length (`DIM.A`) | **13.25** | 13.0 – 13.5 | 12.00 → 7-way · 14.50 → 9-way. **Corroboration only, not a discriminator — see the note below** |
| **d** | body depth | **4.25** | 4.05 – 4.45 | out of band |
| **e** | **count the tails** | **8** | exactly 8 | **DECISIVE.** Anything but 8 is the wrong part, STOP |
| **f** | tail foot width | **0.20** | 0.15 – 0.25 | > 0.55 — will not sit inside a 0.600 mm pad |
| **g** | tab centre → nearest tail centre, along the row | **1.85** ( = (12.45 − 8.75)/2 ) | 1.65 – 2.05 | > 0.3 off — the tab pads will not register |
| **h** | signal-row plane → tab-pad plane, across the body | **3.20** | 3.0 – 3.4 | out of band |
| **i** | body height above board (`4.05` per drawing) | **4.05** | 3.85 – 4.25 | clearance check only, not a condemn |

> **GH2-e and GH2-a are the discriminators; GH2-c is corroboration only.**
> This is written down because the interposer's own 10FDZ gate got it wrong the
> other way round: a housing outline was offered as a circuit-count
> discriminator, the measurement reference was never pinned down, the same part
> yielded two readings 2.66 mm apart and one of them collided with a real
> condemn value. A pin **count** cannot be ambiguous; an outline across moulded
> flanges can. See `01_docs/10fdz-bt-land-pattern-confirm.md` §6.

---

### GH3 — 🛑 PIN 1 / ROW ORDER — **the one that can ship a reversed harness**

**Nobody asked for this measurement. Take it anyway, and take it before GH4.**

**The vendor drawing DOES NOT NUMBER THE CIRCUITS.** MEASURED: sheet 1's plan
view shows a left-right **symmetric** body, no "1", no chamfer, no polarity
mark; the three numerals on the isometric view are BOM item callouts (1 =
Housing, 2 = PIN, 3 = FITTING NAIL), **not circuit numbers.** The recommended
land is symmetric about the row centre as well.

So circuit 1's end is **not established by the vendor's own document.** The only
thing that says it is JLC's EasyEDA library footprint — a JLC artifact, the same
single-sourced class of evidence ADR-0031 set out to stop relying on.

**Why this is not a labelling nit.** A GH plug is keyed on a **face** (the lock
ramp), not on an **end**. If the clone's shroud moulding carries its lock recess
on the opposite face, the plug goes in flipped, and **the row reverses
end-for-end while mating and latching perfectly.** Every number is valid in both
systems and names a different pad. This repo has already paid for exactly that
shape once (commit `16c54169`: a pad numbering invented on a false premise whose
vendor truth was its exact reverse, `ours_n = 24 − vendor_n` on all 23 pads).

**And here it is electrically live.** MEASURED from the sealed v1.7 board:

```
board pad:  1=3V3_SW_A  2=GND  3=SDA_A  4=SCL_A  5=TH_CAM_A  6=TH_MOUNT_A  7=TH_PORT_A  8=SHIELD_DRAIN
reversed :  plug wire n lands on board pad 9−n
  pod 3V3_SW feed  →  pad 8  SHIELD_DRAIN
  pod GND          →  pad 7  TH_PORT
  pod SHIELD_DRAIN →  pad 1  3V3_SW      ← the switched 3V3 rail driven into the pod shield
```

That is a direct short of the switched 3V3 rail to shield ground through
`Q_SWA`, on a board that otherwise assembles, powers up and looks right.

**The test** (needs the GH1 print, one clone header, one built plug, a DMM):

1. Seat the clone header on page 1 at `J_THERM_A` in the **only** orientation
   GH1 allows (tails on the eight small pads, tabs on the two large ones).
2. Identify **printed pad 1**. Two independent marks, both MEASURED off the
   sealed board:
   - **F.Cu / page 1:** pad 1 is the **west-most** signal pad, at
     x = 27.625 on `J_THERM_A` (pad 8 at x = 36.375). West = the end nearer the
     board's left edge.
   - **F.Silkscreen:** a **0.99 mm tick at x = 27.065**, running north (away
     from the body), immediately west of pad 1 — and it is on the **west side
     only**; there is no east counterpart. This tick prints on the real board.
   - **F.Fab / `assembly.pdf`:** a chevron whose apex is at **x = 27.625,
     exactly pad 1's centre.**
3. Mate the genuine `GHR-08V-S` plug in the only orientation its lock allows.
4. Ohm from **plug circuit 1** to the header tail sitting on **printed pad 1**.

| | |
|---|---|
| **PASS** | plug circuit 1 rings out to the tail on printed pad **1**, and plug circuit 8 to the tail on printed pad **8** |
| 🛑 **FAIL — REVERSED** | plug circuit 1 rings out to the tail on printed pad **8**. **STOP. Do not order.** Report it: the fix is a `.tsx` pin-map change, not a bench waiver, and it changes which candidate is even viable |
| 🛑 **FAIL — NO KEY** | the plug seats in **either** rotation. The clone's shroud does not key at all; a field harness can be plugged in reversed. **STOP** |

Repeat on a **second** clone header. A moulding error is a tool property, so
two agreeing parts is meaningful and one is not.

> **Take the same reading on the `C133062` control.** It is genuine JST, so it
> *defines* the right answer; if the control comes out reversed, your rig or
> your plug is wired wrong, not the clone.

---

### GH4 — 🛑 RETENTION / withdrawal force  *(the question the user actually asked)*

Mate a fully-populated plug (all 8 contacts crimped or soldered) into the clone
header. Pull **along the mating axis**, steadily, no jerk. Record the force at
which the plug releases.

**Threshold: ≥ 4.0 N.**
**Where it comes from:** the SHOU HAN specification's own §6.4,
*Plug-out force ≥ 0.5 N per pin* × 8 circuits. It is the vendor's published
claim about its own part, which is the right thing to hold it to. JST's
`eGH.pdf` publishes **no** force figure, so there is no genuine-JST number to
compare against on paper — which is why you bought `C133062`.

| | |
|---|---|
| **PASS** | releases at **≥ 4.0 N**, **and** ≥ 60 % of the `C133062` control measured on the same rig with the same plug |
| **MARGINAL** | ≥ 4.0 N but < 60 % of control → record both numbers, do not decide alone, report |
| 🛑 **FAIL** | releases below **4.0 N**, or the latch does not engage at all, or the plug walks out under GH7's cycling |

**Zero-instrument form, if you have no force gauge:** clamp the header
tails-up, mate the plug, and hang a **500 g** mass from the wire bundle
(gathered so the pull is axial, not a peel). 500 g = **4.90 N**, i.e. 1.22× the
threshold. Hold 30 s. **It must not separate.** This is a go/no-go, not a
measurement — it cannot produce the ratio-to-control number, so report it as
`≥4.90 N (mass test)` and say the control comparison was not taken.

**Do not test retention by pulling on the wires individually** — that measures
§6.2 contact-retention-in-housing, a different spec, and it will destroy the
plug before it tells you anything about the shroud.

---

### GH5 — insertion force

Same rig, pushing.

**Threshold: ≤ 24 N** ( = SHOU HAN spec §6.3, *Plug-in force ≤ 3 N per pin* × 8 ).

| | |
|---|---|
| **PASS** | seats at **≤ 24 N** with an audible/tactile latch click |
| **FAIL** | > 24 N, or it needs a tool, or it seats without ever latching |

Qualitative fallback with no gauge: **a GH plug is a low-insertion-force
connector** (JST's `eGH.pdf` p.1 says so in as many words). If it takes two
hands and visible effort, that is a fail whatever the number would have been.

---

### GH6 — contact resistance, 4-wire, mated

**Read §6.1 before choosing a threshold — this connector is governed by contact
RESISTANCE, not contact METALLURGY, and the circuit's own tolerance is enormous.**

Measure **header solder tail → plug wire at 25 mm from the housing**, 4-wire,
on the mated pair. Do it on the `3V3_SW` circuit (pin 1), the `GND` circuit
(pin 2) and one NTC sense circuit (pin 5).

**Threshold: ≤ 30 mΩ per circuit.** That is the vendor's own **≤ 20 mΩ**
(spec §5.3, held for initial *and* after heat/cold/humidity/salt) plus a
budget for what your measurement unavoidably includes and the vendor's does not:
~5 mΩ of crimp and ~3–5 mΩ of wire (AWG 26 is 0.1339 Ω/m → 3.35 mΩ per 25 mm;
AWG 28 is 0.2129 Ω/m → 5.3 mΩ). Subtract your own wire term if you want the
contact figure alone.

**No milliohm meter?** Force **100 mA** through the loop and read the volt drop:
20 mΩ ⇒ **2.00 mV**, 30 mΩ ⇒ **3.00 mV**. Any DMM with a mV range reads that.
Use 4 separate leads — a 2-wire ohms reading is all lead resistance.

| | |
|---|---|
| **PASS** | ≤ 30 mΩ on all three circuits, **and** within 2× of the `C133062` control |
| **REPORT, DO NOT FAIL** | 30 mΩ – 1 Ω. This is a **workmanship** finding, not a circuit finding — see §6.1. Record it, re-crimp, re-measure |
| 🛑 **FAIL** | > 1 Ω, or intermittent when you wiggle the plug. Intermittency is the real failure mode and it does not show as a number |

#### 6.1 Why the threshold is a workmanship screen and NOT a circuit limit

**MEASURED from `07_releases/cooksense-v1.7-2026-07-30/source/cooksense.net`:**

```
3V3_ANALOG ──[ R_REF0 10k, ON BOARD ]── TH_CAM_A ── J_THERM_A.5 ──(contact)── pod NTC ──(contact)── J_THERM_A.2 ── GND
3V3_ANALOG is ALSO U_ADC.15 (VDD) and U_ADC.16 (VREF)  ← same net, so the divider is
                                                          truly RATIOMETRIC against the ADC reference
```

The 10 k reference leg is **on the board**. Only the NTC leg crosses the
connector, through **two** contacts (the sense pin and the shared GND return).
So a contact resistance `R_c` perturbs the divider by `2·R_c / 10 000`.

With the board's own NTC constants (`02_parts/KNTC0603-10KF3950/part.yaml`:
R25 = 10 kΩ, B25/85 = **3987 K**), sensitivity is `B/T² = 3987/298.15² =
0.044853 per K`, i.e. 4.4853 %/K. Therefore:

| `R_c` per contact | fractional error | temperature error |
|---|---|---|
| 20 mΩ (SHOU HAN's own spec) | 4.0 × 10⁻⁶ | **8.9 × 10⁻⁵ K** |
| 50 mΩ (JST's worst published after-test) | 1.0 × 10⁻⁵ | **2.2 × 10⁻⁴ K** |
| **22.4 Ω** | 4.49 × 10⁻³ | **0.1 K** ← the circuit-derived condemn level |

**The circuit tolerates about 22 Ω per contact before a tenth of a degree
moves. The vendor promises 0.02 Ω. That is a margin of roughly 1120×.**

So GH6 is not asking whether the connector is good enough for the circuit —
that question is answered, by four orders of magnitude, and it is answered
identically for JST and for the clone. **GH6 is asking whether this particular
lot's plating and crimping are sound**, because a bad lot shows up here first
and as intermittency later.

**And note what is NOT at stake, because an agent brief got this wrong on
2026-07-30 and reasoned from it:** `J_THERM_A`/`J_THERM_B` are **not**
thermocouple connectors. Not one thermocouple net touches either ref — the
thermocouple is `J_TC` (`Omega_PCC-SMP-K_TypeK_PCpin`, pads 1/2 = `TC_POS_IN`/
`TC_NEG_IN`), a different, self-supplied, **DO-NOT-SUBSTITUTE** part. On a real
TC connector the governing substitution risk is **contact metallurgy** —
dissimilar metals form a parasitic thermocouple in series with a microvolt
signal, so a different contact alloy is disqualifying. On **this** connector the
signals are 3.3 V logic, I²C and three ratiometric NTC taps, so the governing
term is **resistance**. These are also all SELV nets; nothing here crosses the
isolation barrier, so the connector's voltage rating is not a barrier term
either. `02_parts/SM08B-GHS-TB/part.yaml` carries this as a dated correction.

One term that does not cancel: pin 1 (`3V3_SW_A`) carries the **pod's** supply,
so its contact drop lands on the pod's rail as `I_pod × R_c` — at 20 mΩ and a
100 mA pod that is **2 mV**. It does **not** affect any NTC reading, because the
divider's top is `3V3_ANALOG` on the board, not the pod's rail.

---

### GH7 — durability: 5 mate cycles, then repeat GH4 and GH6

Mate and unmate **5 times**, then re-take GH4 and GH6 on the same pair.

| | |
|---|---|
| **PASS** | GH4 still ≥ 4.0 N and GH6 still ≤ 30 mΩ |
| **REPORT** | any fall > 25 % in retention, or any rise > 2× in resistance |
| 🛑 **FAIL** | the latch deforms, the shroud cracks, or a contact backs out of the housing |

Five cycles is deliberately modest — it is a **shipping-and-service** figure,
not a life test, and it is chosen so the whole gate fits in one sitting. It
mirrors `ORDER_README` §7b **B2**, which already requires ≥ 5 mating cycles
before `J_PWR`'s contact resistance is believed.

---

## 4. WHAT A PASS LICENSES — and what it does NOT

**A PASS authorises the substitution `C265111` → `C42376901` on
`J_THERM_A`/`J_THERM_B`, ON THIS BOARD, for the lot you tested.** That is all.

It is **NOT**:

- **not a general approval of SHOU HAN as a vendor.** It is one part, one lot,
  one mating system, measured once. `02_parts/contracts.md`'s rule that a
  waiver copied from another board is an inherited defect applies to vendor
  approvals too.
- **not approval to substitute any other part on this board.** `J_TC`
  (`PCC-SMP-K`) and `DIP05-1A72-13L` are **DO-NOT-SUBSTITUTE** for reasons that
  have nothing to do with this gate — see §6.1 on why the TC connector fails
  differently.
- **not a change to the thermal envelope.** §2.3: the relay still binds at
  −20 … +70 °C, `ORDER_README` §7b B1–B6 is still mandatory, and passing it
  still reopens at most 65 → 70 °C.
- **not a substitute for `ORDER_README` §7b.** Different gate, different
  question, both owed.
- **not permission to edit `cooksense-v1.7-2026-07-30`.** A fix is a NEW
  release plus `SUPERSEDED.md` on the old one, never an edit. §7.

**A FAIL is also an outcome, and it has a named next move**: fall back to
`C133062` (genuine JST, 32068 in stock, MOQ 1) and pay the **copper revision**
for top-entry mounting — a new footprint, a new placement for both refs, a
re-route and a full re-gate. ADR-0031 records it as the standing fallback for
exactly this branch. That is expensive, which is why the bench hour is worth
buying first, not because the fallback does not exist.

---

## 5. VERDICT — fill this in and report back

```
GH-08 CLONE MATE CONFIRM — reported by: ............   date: ..........
clone headers tested: ....   lot/reel marking: ....................
plug built with:  [ ] crimped (tool: ..........)   [ ] soldered barrel
control article:  [ ] C133062 measured   [ ] not bought — comparisons N/A

GH1 print calibration   170.00 ....   8.75 ....   12.45 ....   22.00 ....
GH1 overlay             PASS / FAIL

GH2  a span 7 pitches ........   e TAIL COUNT ........   (a and e are decisive)
     b pitch ........   c body len ........   d depth ........   f foot w ........
     g tab->tail ........   h row->tab ........   i height ........

GH3  PIN 1        plug circuit 1 rings out to printed pad ....     (must be 1)
     plug seats in  [ ] one rotation only   [ ] either rotation (= FAIL, no key)
     second header agrees?  Y / N        control C133062 reads pad ....

GH4  retention    clone ........ N     control ........ N     ratio ........
     (or) 500 g mass test:  held / separated
GH5  insertion    clone ........ N     control ........ N
GH6  4-wire mOhm  clone pin1 ....  pin2 ....  pin5 ....
                  control pin1 ....  pin2 ....  pin5 ....
GH7  after 5 cycles:  retention ........ N     resistance ........ mOhm

VERDICT:   PASS — adopt C42376901, cut v1.8   |   FAIL — see notes
           REVERSED — do not order, GH3 failed
notes: ......................................................................
```

**PASS requires:** GH1 overlay PASS **and** GH2-a/GH2-e in band **and**
**GH3 PASS on two headers** **and** GH4 ≥ 4.0 N **and** GH5 ≤ 24 N **and**
GH6 ≤ 30 mΩ on all three circuits **and** GH7 holding both.

**Any single FAIL keeps the gate shut.** GH3, GH4 and GH2-e are hard stops.

---

## 6. Where the results go when they exist

1. **Here**, as a dated `§6 RESULTS` section appended below — this file is the
   instrument and the record, the same shape as
   `01_docs/10fdz-bt-land-pattern-confirm.md`.
2. Grade every number **MEASURED** (canon M-IMPORT: a human touched the
   physical object). If the caliper's resolution is not stated, say the third
   digit is indicative.
3. **A number that comes back worse than assumed is a result, not a setback.**
   Record it as measured and let it decide. Do not explain it away, and do not
   collapse a range into a single figure — that is an assumption wearing a
   measurement's clothes, and this project has already made that exact error
   once (10FDZ §6b, M1/M2/M5).

---

## 7. WHAT HAPPENS ON A PASS — the v1.8 cut, staged and waiting

**None of this is done, and none of it may be started before §5 has numbers.**
It is written now so that a PASS is followed by execution, not by design.

### 7.1 The substitution itself

`03_tscircuit/cooksense.tsx` is the only place the part is chosen. Change the
`J_THERM_A` / `J_THERM_B` LCSC code and MPN **together** (canon M8 — both codes
must move as one, and **both must be NAMED in `MANIFEST.txt` and in the first
40 lines of `ORDER_README.md`**), then rebuild. **The footprint does not
change** — §2.2 shows the land is already correct for both parts, and the
sealed twin log already reads `C265111 J_THERM_A OK fit=0.01mm jlc_offset=0`.
`J_THERM_*` has **zero drilled pads**, so no hole can move; the CPL rows stay
at `(32.0, −96.75, top, 0.0)` and `(54.0, −96.75, top, 0.0)`.

This is the `--sourcing-supersede` shape in `skills/pcb-design/SKILL.md`: MPN
and LCSC move together, board md5 identical, CPL byte-identical.

### 7.2 🛑 `fab/` MUST COME FROM THE EXPORTER — never a hand-copy (M-HANDFIX)

**MEASURED on the sealed v1.7 archive, and this is the defect's fingerprint:**

```
fab/bom.csv  sha256 80b8319b6b9980a07e354037f22be131f1c7c7b4d756249306cbac1d04320305
fab/bom_jlc.csv  IDENTICAL
fab/cpl.csv  sha256 c3e4ddacfec118d681048cbcb2621c7f0609c3eb0e7a6952d8158ed1c3d3c521
fab/cpl_jlc.csv  IDENTICAL
```

Byte-identical pairs are what a hand-copy looks like. `export_jlc_package.py`
wrote `bom_jlc.csv`/`cpl_jlc.csv` for its whole existence while
`07_releases/contracts.md` required `bom.csv`/`cpl.csv`, and **34 releases
bridged the gap by hand** — which is exactly what kept it invisible. On
pluto-rx2-8way-v2 the hand-copy did not happen and two stock gates (`A-STOCK`,
`A-BUY`) reached a **zero denominator** and emitted notes instead of failures.

**The exporter is fixed** (commit `628ee3d4`; it now writes `bom.csv` and
`cpl.csv` directly and reads the legacy names only for LCSC carry-over).
**Run it. Do not copy, do not rename.**

> **The rule, generalised, because it is the reusable part:** if you find
> yourself hand-copying or renaming anything on the way to a gate, **STOP and
> file it against the producer.** A human silently reconciling a producer with
> its contract, once per release, is how a defect survives 34 releases.

### 7.3 The two owed packaging fixes — they ride this cut

Both are OWED from before this gate and both are **release-procedure**, not
board changes. They were judged not worth a respin on their own; that judgement
holds and they travel with whatever cut clears the sourcing block.

**(a) task #53 / #45 — strip gitignored files LAST.**
`kicad-cli` **regenerates `.kicad_prl` merely by opening a board.** So the
`git check-ignore` sweep must be the **final** pre-seal action — after *every*
`kicad-cli` invocation **including the final DRC**, not before it. This already
bit two boards on 2026-07-23. `07_releases/contracts.md` step 1 carries the
clause; what is owed is doing it in that order.
*(v1.7 came out clean on this: `source/cooksense.kicad_prl` is present **and**
is in the MANIFEST at row 445. It was right by care, not by construction.)*

**(b) task #58 — assert the MANIFEST is BIJECTIVE, both ways.**
`sha256sum -c` walks the manifest and checks each row against a file. **It
cannot see a file that is present in the archive but absent from the manifest**
— which is precisely what a regenerated `.kicad_prl` after a stamp produces: a
green verify over an archive with an unaccounted file in it.

MEASURED on v1.7 — it passes today, and no gate proves it:

```
manifest rows: 122   files on disk: 122
IN ARCHIVE NOT IN MANIFEST: []      IN MANIFEST NOT IN ARCHIVE: []
sha256sum -c   RAW_EXIT=0
```

**Neither `release_freshness_check.py` nor `policy_audit.py` implements this
check** (grepped 2026-07-31: no bijection assertion in either). The machine
backstop is genuinely missing and belongs in the fleet tool, which is outside
this board's partition. Until it lands, run it by hand as the last pre-seal
step, from inside the staged release directory:

```bash
/usr/bin/python3 - <<'EOF'
import re, os
lines = open('MANIFEST.txt', encoding='utf-8').read().splitlines()
i = [n for n, l in enumerate(lines) if l.startswith('FILE DIGEST ')][0]
rows = {m.group(1) for l in lines[i+3:]
        for m in [re.match(r'^\s+(\S+)\s+[0-9a-f]{64}\s*$', l)] if m}
files = {os.path.relpath(os.path.join(dp, f), '.')
         for dp, _, fn in os.walk('.') for f in fn} - {'MANIFEST.txt'}
print('rows', len(rows), 'files', len(files))
print('IN ARCHIVE NOT IN MANIFEST:', sorted(files - rows))
print('IN MANIFEST NOT IN ARCHIVE:', sorted(rows - files))
raise SystemExit(0 if rows == files else 1)
EOF
```

Both sets empty and RAW_EXIT 0, or the manifest is not a manifest.

### 7.4 The `part.yaml`, written and NOT adopted

The dossier below is ready to drop in at adoption. **It is deliberately not
created as a directory yet**: `02_parts/contracts.md` forbids a `part.yaml` for
a part that is not on the board, and the BOM-parity gate reads
`02_parts/` ↔ BOM in both directions. Creating it today would be a stale entry
by that contract's own definition, and the repo's contracts audit is sitting
**exactly at its debt ceiling (2646)**, so a new unpermitted path fails the
gate rather than accruing quietly.

**On PASS**, create `02_parts/SH-SM08B-GHS-TB(LF)(SN)/` — the directory name is
the exact orderable MPN — write the file below into it, drop the vendor PDF
(sha256 in §2.1) in beside it as `SH-SM08B-GHS-TB-REV1.00.pdf`, and **delete
`02_parts/SM08B-GHS-TB/` in the same change** (git history keeps it), noting the
swap in `01_docs/CHANGELOG.md` as `02_parts/contracts.md` **Repair** requires.

> **PENDING BENCH — the `verified:` note below cites a FIGURE for the land and
> explicitly does NOT claim a vendor-numbered pin map, because there is not one
> (GH3). Do not soften that sentence to make a gate green.**

```yaml
# ==========================================================================
# STAGED, NOT ADOPTED — 2026-07-31.
# Do NOT create 02_parts/SH-SM08B-GHS-TB(LF)(SN)/ until
# 01_docs/gh08-clone-mate-confirm.md §5 reads PASS. See §7.4 there.
# ==========================================================================
mpn: SH-SM08B-GHS-TB(LF)(SN)
manufacturer: SHOU HAN                # Shenzhen Shouhan Technology Co., Ltd
type: connector_wire_to_board_header_1x8   # CLASS: 1.25mm GH-compatible SMD side-entry header
datasheet:
  doc_id: SH-SM08B-GHS-TB
  revision: REV1.00                   # title block: REV. 1.00, 2020-03-22
  url: https://easyeda.com/api/products/C42376901/components?version=6.4.19.5
  # ^ JLC's own dataManualUrl is BLANK for this code while
  #   dataManualFileAccessId is POPULATED. The EasyEDA product API is the
  #   route that resolves it; two earlier passes read the blank URL as
  #   "no datasheet exists" and it is not the same thing (ADR-0031).
  sha256: 866a52b6242453fb7b99eca62a87fc06590c5692845ffc8eb81ef3cbd313ea58
  fetched: 2026-07-31
package: GH 1.25mm 8-circuit SMD side-entry (right-angle) shrouded header, 2 solder tabs
footprint: Connector_JST:JST_GH_SM08B-GHS-TB_1x08-1MP_P1.25mm_Horizontal
  # UNCHANGED from the incumbent, and that is the point of the substitution.
  # Board land MEASURED off the sealed v1.7 .kicad_pcb: 8 signal pads
  # 0.600 x 1.700 on 1.250 pitch (span 8.750), 2 tab pads 1.000 x 2.700
  # (centres 12.450 apart), rows 3.200 apart. Vendor sheet 1's recommended
  # land is 0.700 x 1.800 signal / 1.000 x 2.500 tab, DIM.B 8.75, DIM.A 13.25
  # — same pitch, same span; our pads are a subset. Terminal foot is
  # 0.20 +/- 0.05 wide, one third of our pad.
escape:                               # escape_check.py --style connector --pitch 1.25
  style: connector
  pitch: 1.25
  tier_required: jlc_2layer_default
  checked: "RE-RUN escape_check AT ADOPTION — do not copy this line in; the
    checker cross-checks it against the footprint text"
pins:                                 # 1..8 signal + 2 mechanical tabs (KiCad pad name "MP")
  1: P1
  2: P2
  3: P3
  4: P4
  5: P5
  6: P6
  7: P7
  8: P8
  MP: {name: MP, tie: GND, note: "two tin-plated FITTING NAILs (vendor BOM item 3, 2 PCS, phosphor bronze + bright tin 60u\" min); footprint pad 'MP' x2 = one common node; carry no signal current — tie to GND for retention + shield return"}
limits: {current_per_contact: "1A AC/DC", voltage: "125V AC/DC", temp_range: "-25..+85C", contact_resistance: "20mOhm max (initial and after heat/cold/humidity/salt)", insulation: "100MOhm min", withstanding: "500V AC 1 min", wire: "AWG #32-#28", pcb_thickness: "1.2-1.6mm", plug_in_force: "3N/pin max", plug_out_force: "0.5N/pin min", contact_retention: "10N/pin min"}
gotchas:
  - "SECOND SOURCE for JST SM08B-GHS-TB (C265111), adopted ONLY because the
     genuine part is UNBUYABLE: stock 0 at MOQ 21 with canPresaleNumber -1285
     over six readings in 72 h. This is a sourcing substitution, not a
     preference. The genuine part remains the reference design."
  - "*** THE VENDOR DRAWING DOES NOT NUMBER THE CIRCUITS. *** Sheet 1's plan
     view is left-right SYMMETRIC — no '1', no chamfer, no polarity mark; the
     numerals 1/2/3 on the isometric are BOM item callouts (Housing / PIN /
     FITTING NAIL). The pin map above is the FOOTPRINT's numbering, confirmed
     against a genuine GHR-08V-S plug ON A BENCH (see verified:), NOT read off
     a vendor figure. A GH plug keys on a FACE, not an END, so a mirrored
     shroud moulding would mate and latch while reversing the row — putting
     3V3_SW on SHIELD_DRAIN. cf. commit 16c54169, where an invented pad
     numbering turned out to be the vendor's exact reverse."
  - "DO NOT 'CORRECT' temp_range TO MATCH THE DISTRIBUTOR — and note the trap
     runs the other way here. JLC's structured `Operating Temperature`
     attribute reads -25C~+85C on this part AND on C265111 AND on C54110154
     AND on C133062. It is SERIES-LEVEL BOILERPLATE: demonstrably wrong on
     C265111 (whose hash-pinned eGH.pdf p.1 says -40..+105C) and identical on
     genuine and clone, so it can neither clear nor condemn a substitute.
     The -25..+85C above comes from THIS part's OWN vendor drawing, not from
     that field. The agreement is a coincidence. Q-SNIPPET class."
  - "-25..+85C is 20 K narrower at the top and 15 K at the bottom than the
     genuine JST part. It does NOT bind this board: DIP05-1A72-13L at
     -20..+70C is the unique minimum across all part dossiers (ADR-0030), so
     the relay still sets the envelope. A future revision that re-rates the
     relays meets this connector next, and meets it 20 K sooner than it would
     have met a genuine JST one."
  - "mates with JST GHR-08V-S (C485357) + SSHL-002T-P0.2 contacts (C189897) —
     build the pod harness to the GENUINE JST plug, not to a clone plug. The
     bench gate qualified this shroud against that plug and nothing else."
  - "NOT a thermocouple connector. The governing substitution risk here is
     contact RESISTANCE, not contact METALLURGY: signals are 3.3 V logic, I2C
     and three RATIOMETRIC NTC divider taps. The thermocouple is J_TC
     (PCC-SMP-K), DO-NOT-SUBSTITUTE, for exactly the metallurgy reason this
     part is exempt from."
verified: "PENDING BENCH -> replace this whole string at adoption.
  LAND read from the vendor CUSTOMER DRAWING sheet 1/1 recommended-land figure
  (labelled 印制线路板): signal pad 0.7 x 1.8, tab pad 2.5 tall, DIM.B 8.75
  (= 7 x 1.25), DIM.A 13.25 — REV 1.00, 2020-03-22, sha256 866a52b6...
  RATINGS from the same sheet's specification block and spec sheets 4-6
  (§5.1-5.5 electrical, §6.1-6.4 mechanical, §7.1-7.7 endurance).
  *** PIN MAP IS **NOT** FROM A VENDOR FIGURE — THE DRAWING NUMBERS NO
  CIRCUITS. *** It is the footprint's numbering, and it is valid only once
  01_docs/gh08-clone-mate-confirm.md GH3 has confirmed on TWO physical parts
  that a genuine GHR-08V-S lands circuit 1 on the pad this board calls 1.
  At adoption, replace this with: 'pin map CONFIRMED on the bench <date>:
  GHR-08V-S circuit 1 -> pad 1 on N parts (gh08-clone-mate-confirm.md §6)'."
layout:
  source: "vendor CUSTOMER DRAWING sheet 1/1 recommended land + 2x FITTING NAIL
    retention (mechanical). This header is the THERMAL-HEAD POD input: switched
    3V3, GND, one I2C bus, three NTC sense lines, shield drain."
  reviewed: "PENDING BENCH — set at adoption"
  notes: "Passive interconnect — layout-agnostic, no self net-span budget.
    Carries the THERMAL-HEAD POD harness: switched 3V3, GND, one I2C bus
    (SDA/SCL, shared with that side's camera), THREE NTC thermistor sense lines
    (TH_CAM / TH_MOUNT / TH_PORT) and SHIELD_DRAIN. Keep the three NTC sense
    lines clear of heater/contactor/switching nodes — they are high-impedance
    divider taps (10k-100k class) and the open-thermistor detect trips on them.
    Tie both MP tabs to GND. NOT the thermocouple path: that is J_TC ->
    R_TCP/R_TCN -> MAX31856, and the TC input RC filter and cold-junction sense
    belong AT the MAX31856, never here."
sourcing:
  lcsc: C42376901
  alternates: [C265111, C133062]
  # NO stock, MOQ or price committed here — TIER 3 (volatile, TTL hours),
  # 06_build/cache/ only, per 02_parts/contracts.md. Live readings:
  # 06_build/cache/gh08_sourcing_<date>.json and gh08_mate_articles_<date>.json.
  # Candidate ledger and the reason each alternate lost: ADR-0031.
  note: "SHOU HAN SH-SM08B-GHS-TB(LF)(SN), second source for JST
    SM08B-GHS-TB(LF)(SN) = C265111, which is DESIGN-CORRECT and UNBUYABLE
    (stock 0 / MOQ 21 / canPresale -1285 over six readings). C133062 is the
    genuine-JST fallback but is TOP-ENTRY = a copper revision. C54110154
    (XYECONN) REJECTED: no datasheet exists at all (dataManualUrl None AND
    dataManualFileAccessId empty = a declared catalog absence) and brass
    contacts. Full ledger: ADR-0031. Bench qualification:
    01_docs/gh08-clone-mate-confirm.md."
```

### 7.5 The cut, in order

1. §5 reads **PASS**. Not before.
2. `03_tscircuit/cooksense.tsx`: MPN + LCSC together on both refs. Rebuild.
3. `02_parts/`: create the new dir per §7.4, delete `SM08B-GHS-TB/`,
   `CHANGELOG.md` entry. Re-run `escape_check` for real.
4. **Run the FIXED exporter** for `fab/` (§7.2). No hand-copy, no rename.
   🛑 **IT WILL BLOCK ON A-ROT AT `C160403`, AND THAT IS NOT THIS
   SUBSTITUTION'S FAULT — SEE §7.6. Budget for it.**
5. Re-gate: DRC `--severity-all --refill-zones --schematic-parity`, **both
   halves, 0 violations / 0 unconnected / 0 parity**; ERC; `policy_audit`;
   `release_freshness_check`; `jlc_stock_check` — **and re-read the MOQ**, which
   `jlc_stock_check.py` does not read (ADR-0031 Consequences: a line can PASS
   A-STOCK and be unbuyable at every quantity).
6. Commit the source. Confirm `release_git_dirty.py` clean apart from the
   staged release dir.
7. **Strip gitignored droppings LAST** (§7.3a) — after the final `kicad-cli`
   run, not before.
8. Stamp `MANIFEST.txt` (`git_sha`, `git_dirty: false`, full sha256 table),
   **name both LCSC codes in the MANIFEST and in `ORDER_README.md`'s first 40
   lines** (canon M8), re-run `policy_audit` M-REL + freshness so the shipped
   audit grades the real manifest.
9. **Bijection check** (§7.3b). Both sets empty, RAW_EXIT 0.
10. Seal commit: the release dir + `CHANGELOG.md` + `SUPERSEDED.md` on v1.7.
    **`07_releases/` is IMMUTABLE from that commit; `cooksense-v1.7-2026-07-30`
    is never edited, only superseded.**

### 7.6 🛑 A BLOCKER THE CUT INHERITS — `C160403` has no rotation authority

Found by **running the fixed exporter as a dry run on 2026-07-31**, precisely so
that §7.5 step 4 would not be discovered cold. It stopped:

```
export_jlc_package.py --layers 4 04_kicad/cooksense.kicad_pcb <scratch>
RAW_EXIT 2
rotations_unsourced.csv:
  C160403, JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal, J_ESTOP
  "5 pads — the exemption is only for 2-terminal chip parts
   (a symmetric part with more pads can still be 90 deg wrong)"
```

**MEASURED:** `C160403` has **zero** rows in
`skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv` and zero in
`jlc_rotations_db.csv` (`grep -c` → 0, RAW_EXIT 1 on both; control `C5620` → 4
rows, so the file is being read). `git log --all -S C160403` over that path
returns **nothing at all — it has never had a row.**

**What that means for v1.7, stated carefully.** The sealed release's
`fab/cpl.csv` line 71 carries `J_ESTOP,C160403,…,90.0`, and the A-ROT gate that
now refuses it ("silence is now a FAIL") landed **2026-07-25**, five days before
the **2026-07-30** seal. No `rotations_unsourced.csv` was shipped in `fab/`, so
the export was run through the `--allow-unsourced-rotations` escape hatch and
the worklist did not travel with the release. `C160403` is also **not** on
`fab/rotation_human_gate.txt`'s A-POL list, so it is on neither the machine path
nor the human path.

**It is not unevidenced.** `verification/twin_overlay_lowres.md` line 47 records
`J_ESTOP | C160403 | 0deg @0.00mm | margin 0.205` — jlc_twin measured a zero
offset against JLC's own model at a good margin. But the exporter explicitly
refuses that as the authority (*"an operator VERIFIED AGAINST PCBNEW ITSELF,
never jlc_twin's `jlc_offset` — canon M1"*), because the twin and the placement
are not independent.

**Disposition — and this is deliberately NOT decided here.** Whether v1.7 needs
anything is a release-integrity call, not this gate's; the rotation may well be
right, and `07_releases/` is immutable regardless. What IS certain and what this
section exists to prevent:

- **The v1.8 cut blocks at step 4 until `C160403` gets a real measured row**
  (fit the board footprint against JLC's cached model with an operator verified
  against `pcbnew` itself, then add the row with residual + next-best separation
  + date + the polarity column). `J_ESTOP` is a 3-circuit polarised connector,
  so canon A-POL also wants a **numbering-free channel** on that row.
- **`jlc_lcsc_rotations.csv` is a FLEET file under `skills/`, outside this
  board's partition.** It is not edited from here. Whoever cuts v1.8 either owns
  that file for the duration or hands the row off — and must not reach for
  `--allow-unsourced-rotations` a second time, because doing that once is how
  this arrived unannounced.

---

## 8. ⚠️ SEPARATE WATCH — `C587657` is now the thinnest line on the BOM

Not blocking today. Recorded here because this is the document the next person
holds, and because **the order in §1 is the cheapest moment to act on it.**

`C587657` — **Molex `436500224`**, `J_PWR`, 1/board, **single-source, no
drop-in fallback.** Measured across the same reading series:

```
stock  130 → 80 → 70 → 70 → 43        canPresaleNumber 12      MOQ 1
```

It still clears the floor: 1/board × 5 boards = **5 needed** against 43. **It
is not the blocker and must not be reported as one.** But it has lost 67 % in
five readings, its presale headroom is 12, and the only alternate the sweep
found (`C293740`) is **through-hole** — a footprint change, i.e. copper.

**Re-specify before it reaches the build quantity, not after it reaches zero.**
The cheap move is line **E** in §1: buy 10 now, while you are buying the bench
articles anyway, so a JLC stock-out cannot strand the build.

---

## 9. Carried forward — a silk item this gate turned up

**`J_THERM_A`/`J_THERM_B` pin-1 marking is a 0.99 mm silk tick, and nothing
else.** MEASURED on the sealed v1.7 board: a single segment at x = 27.065
running y 95.290 → 94.300, on the **west side only**, with no east counterpart.
It is correct and it is unambiguous to an instrument. It is also easy for a
human to miss on a board this dense, and GH3 is the whole reason that matters.

**v-NEXT (not this cut, no board change justified on its own):** add a filled
pin-1 dot or a `1` numeral on `F.Silkscreen` at both refs. It is the standing
mitigation for the reversal GH3 tests for, and it costs nothing on a revision
that is happening anyway.
