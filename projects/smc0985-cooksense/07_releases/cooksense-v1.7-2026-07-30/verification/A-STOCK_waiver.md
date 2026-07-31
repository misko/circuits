# A-STOCK waiver — cooksense v1.7 — `C265111` on `J_THERM_A` / `J_THERM_B`

**Canon**: M4 (evidence-backed exceptions — the measurement is a COMMAND AND ITS
OUTPUT, not a digit) and A-STOCK (`skills/jlcpcb-fab/scripts/jlc_stock_check.py`,
07_releases contract "Forbidden": *sealing against stock evidence that does not
PASS*).

**Gate exit code**: `1`. It is not silenced, not weakened, and not re-run until
it agreed. It is red, it is reported red in `build_gates.md`, its FAIL verdict
ships verbatim in `stock_check.json` / `stock_check.txt` beside this file, and
this document is the argument for sealing anyway.

**Machine-readable home of the exception**: `03_src/rules/assembly.yaml`
`sourcing_plan:`, the mechanism `release_freshness_check.py` check (e) actually
reads. This file is the argument; that entry is what the gate grades.

---

## 1. The argument: a stock gate measures the WORLD, not the BOARD

Every other gate in this repo grades an artifact we control. DRC grades copper.
`policy_audit` grades declarations against copper. `bom_source_check` grades one
of our files against another of our files. If any of them is red, **there exists
an edit to this design that turns it green**, and refusing to seal is therefore
the correct response: the red is a defect in the thing being sealed.

A-STOCK is not that kind of gate. It reads a number off a vendor's live catalog.
Today that number is 5 and yesterday it was 0; tomorrow it may be 21. **No edit
to this design changes it.** The only "fix" available inside the design is to
specify a *different part*, which is not a repair of a defect — it is a
purchasing decision, and one with its own unverified risk (§4).

So for this finding, and specifically for this one, A-STOCK is gating at the
wrong time. It asks an ORDER-time question at SEAL time. **Sealing is not
ordering**: this archive is a statement of what the design IS, and a purchase is
an event that has not happened. The release model currently makes one claim
where there are two, and that is filed as a proposed skill patch, not fixed
here (`owed_skill_patches.md`, patch 1).

**This waiver does not generalise.** It applies to a red whose remedy is
provably outside the fab set (§3). A stock red on a part whose replacement would
move copper is a different finding and this argument does not cover it.

---

## 2. The evidence, part one: the dated live reading

**Command (through the gate):**

```
/usr/bin/python3 skills/jlcpcb-fab/scripts/jlc_stock_check.py \
    06_build/staging/cooksense-v1.7/fab/bom.csv \
    --out .../stock_check.txt --json .../stock_check.json
```

**Exit code: 1.** Verdict line, verbatim:

```
FAIL: 57/58 coded BOM lines have stock >= 5 x qty (1 with problems); 3/61 lines carry NO LCSC and were NOT graded by this tool
  SCOPE: graded against LCSC CATALOG stock (stockCount). JLC's assembly uploader
  allocates from a DIFFERENT pool, so a PASS here does NOT mean the line will
  clear at order time. A FAIL is real; a PASS is necessary and not sufficient.
```

The one problem line, verbatim from the same run:

```
  LOW_STOCK(5)     C265111    x2   SM08B-GHS-TB                           expand stock=5
```

`stock_check.json` records `"verdict": "FAIL"`, `graded_lines: 58`,
`failures: 1`, `uncoded_lines: 3`.

**Command (independent of the gate — canon M1, checker and checked must not
share a method).** Raw POST to the same catalog endpoint, own parser, no import
of `jlc_stock_check`:

```python
URL = ("https://jlcpcb.com/api/overseas-pcb-order/v1/"
       "shoppingCart/smtGood/selectSmtComponentList")
body = {"currentPage": 1, "pageSize": 20, "keyword": <code>}
```

**Output, `2026-07-30T21:33:59Z`:**

```
--- C265111 -> 1 hit(s)
   C265111      JST SM08B-GHS-TB(LF)(SN)       JST         stock=5      MOQ=21   type=expand
--- C42376901 -> 1 hit(s)
   C42376901    SHOU HAN SH-SM08B-GHS-TB(LF)(S SHOU HAN    stock=6030   MOQ=1    type=expand
--- C22391766 -> 1 hit(s)
   C22391766    JST SM08B-GHS-TB               JST         stock=0      MOQ=444  type=expand
--- C5620 -> 20 hit(s)          [CONTROL, same minute]
   C5620        Nexperia 74HC238D,653          Nexperia    stock=5212   MOQ=1    type=expand
```

The control returns live stock, so the 5 and the 0 are the catalog's answer and
not a dead field.

**The fact the gate cannot express: `minPurchaseNum` 21 > `stockCount` 5.** The
genuine part is **unbuyable at any quantity today** — you cannot order 21 pieces
when 5 exist, and you cannot order 5. The gate's floor (10 = qty 2 × 5 boards)
is therefore the wrong threshold to watch; **21 is.** A-STOCK reads
`stockCount` and has no MOQ term at all — filed as proposed skill patch 2.

---

## 3. The evidence, part two: THE DESIGN IS INVARIANT UNDER THE REMEDY

This is the load-bearing measurement. If the substitution moved copper, none of
§1 would matter.

**Method** — deliberately NOT `jlc_twin`, which produced the inherited "0.01 mm"
figure this re-derives (canon M1):

1. JLC's own recommended land for each LCSC code, read straight out of the
   EasyEDA `result.packageDetail.dataStr` `PAD~` records
   (`https://easyeda.com/api/products/<code>/components?version=6.4.19.5`),
   converted at 25.4/100 mm per unit and re-origined on the package head.
2. This board's own copper, read out of `source/cooksense.kicad_pcb` with
   `pcbnew`, de-rotated into the footprint frame.
3. A translation-only rigid fit — no rotation, no reflection — with the
   correspondence fixed by pad number for the signal row and by x-sign for the
   two mechanical tabs.

**Board copper (`Connector_JST:JST_GH_SM08B-GHS-TB_1x08-1MP_P1.25mm_Horizontal`,
identical on both refs):** pads 1–8 at x −4.375 … +4.375 (1.2500 mm pitch),
y −1.850, size 0.600 × 1.700; two `MP` tabs at x ±6.225, y +1.350, size
1.000 × 2.700, **both on `GND`**.

**Result:**

| land graded | signal pads 1–8 residual | mechanical tab residual | fit dx | mirrored |
|---|---|---|---|---|
| `C265111` (genuine JST) | **0.0002 mm** | 0.0002 mm | −0.0000 | no |
| `C42376901` (SHOU HAN) | **0.0100 mm** (all eight equal) | **0.0399 mm** | +0.0001 | no |

| | board | `C265111` | `C42376901` |
|---|---|---|---|
| pitch | 1.2500 | 1.2499 | 1.2499 |
| tab \|x\| | 6.2250 | 6.2249 | 6.2249 |
| signal-row → tab-row separation | 3.2000 | 3.1999 | 3.1501 |
| signal pad size | 0.600 × 1.700 | 0.600 × 1.700 | 0.700 × 1.800 |
| **mechanical tab size** | **1.000 × 2.700** | **1.210 × 2.700** | **1.000 × 2.500** |

**THE TAB-SIZE ROW WAS MISSING FROM THIS TABLE AND IT MATTERS (RG-P2-2).** The
residual is a centre-position fit and is **structurally blind to pad size** —
which is the one term that governs a solder-fillet retention tab, i.e. exactly
the axis §4 declares unverified. Measured: the board's tab copper is
**0.210 mm / 17.4 % NARROWER** than JLC's recommended land for the **genuine**
part, and **matches the clone's tab width exactly**. So the parenthetical
"the board's footprint IS the genuine part's land" holds on the eight signal
pads (exact to 0.001 mm in size and position) and **fails on both retention
tabs**. It is a KiCad-library-vs-JLC-library difference, it pre-dates the
substitution question, and it cuts *toward* the clone rather than against it —
but a waiver that omits a term on its own declared-unverified axis is not a
waiver, so it is published.

Non-mirrored is measured, not asserted: pin 1 → pin 8 sweeps **+8.750 mm** on
both vendor lands and on the board.

### ⚠️ AND THE INHERITED "0.01 mm" TURNS OUT NOT TO HAVE BEEN EVIDENCE

The figure this release inherited was stated as: *"jlc_twin fitted
**C42376901's** own JLC footprint against this board's … at **0.01 mm**
residual, NON-MIRRORED, `jlc_offset` 0, independently on both refs."* My own
number lands on 0.0100 mm, so the CONCLUSION is right — but the provenance is
not, and canon M4 is explicit that a number nobody can re-run is graded by
nothing. Two things, both checkable in this archive:

1. **That exact triple is the GENUINE part's own rows.** `verification/twin_run.log`,
   lines 440–441:

   ```
   C265111  J_THERM_A  OK  fit=0.01mm jlc_offset=0 db=0.0 src=lcsc
   C265111  J_THERM_B  OK  fit=0.01mm jlc_offset=0 db=0.0 src=lcsc
   ```

   `0.01` / `jlc_offset=0` / both refs — for **`C265111`**, not `C42376901`.
2. **No `jlc_twin` artifact for `C42376901` exists anywhere in `06_build/`.** A
   search of the whole build tree returns the code only in four PROSE files.

`fit=` is jlc_twin's **max per-pad residual** printed at `%.2f`, so `0.01` is
what it prints for any good fit — **it cannot discriminate the clone from the
genuine part**, because it prints the same value for both. The inherited number
was therefore incapable of supporting the claim it was carrying.

**The measurement in the table above is what actually grades the clone**, and it
is the first evidence in this tree that distinguishes the two parts at all.
Two terms it carries which the inherited claim did not, decomposed here because
a residual that hides its terms is the adjudication defect M4 is named after:

- **(a)** the clone's own recommended land is **0.100 × 0.100 mm larger** per
  signal pad, and its signal-row-to-tab-row separation is 3.1501 mm against the
  board's 3.2000 — a fillet preference plus a **0.0499 mm** row offset, absorbed
  inside a 1.700 mm-tall pad. That is why the tab residual is 4× the signal
  residual, and why both are still deep inside the land.
- **(b)** JLC's two lands **number the mechanical tabs oppositely**: pad `9` sits
  at x −6.225 on `C265111` and at +6.225 on `C42376901`. This is electrically
  null **on this board and only on this board** — both tabs are on `GND` on both
  refs, measured off the board, not assumed from the library name.

### What the substitution actually edits — counted, not estimated

An earlier version of this waiver said "zero bytes of the fab set". **That was too
strong and it is corrected here**, because this board's CPL emitter writes the
LCSC code into the `Val` column. Measured occurrences of `C265111` in `fab/`:

| file | rows carrying the code | what would change |
|---|---|---|
| `fab/bom.csv` | 1 | `MPN` + `LCSC` cells |
| `fab/bom_jlc.csv` | 1 | `MPN` + `LCSC` cells |
| `fab/cpl.csv` | 2 | `Val` cell (this emitter puts the LCSC code there) |
| `fab/cpl_jlc.csv` | 2 | `Val` cell |
| all 11 gerbers + both `.drl` | **0** | **nothing** |

**6 cells across 4 files** (the re-gate's independent census agrees to the cell:
`bom.csv` L51 col `LCSC`, `bom_jlc.csv` L51 col `LCSC`, `cpl.csv` L77/78 col
`Val`, `cpl_jlc.csv` L77/78 col `Val`), and **not one byte of any gerber or
drill file** — `J_THERM_*` has **0 drilled pads**, so there is no hole that
could move. Decisively, **no coordinate, no rotation and no layer**:
`J_THERM_A` stays at `(32.0, −96.75, top, 0.0)` and `J_THERM_B` at
`(54.0, −96.75, top, 0.0)` either way.

**The claim this waiver rests on, stated in its surviving form:** *the
substitution changes zero bytes of the **gerbers, the drill files and the CPL
geometry**.* That is true, it is the engineering-load-bearing half, and it is
what the land-pattern measurement establishes. The **"zero bytes of the fab
set"** form does **not** survive — the BOM and the CPL's identity column both
carry the code — and it is retracted rather than reworded.

**AND THE REMEDY MUST BE A REGENERATION, NOT A HAND EDIT (canon M3).** The LCSC
code is authored in `03_tscircuit/src/cooksense.tsx` lines 1216/1218
(`supplierPartNumbers={{ jlcpcb: ["C265111"] }}`); change it there and all six
cells follow. An earlier version of this waiver, and of `ORDER_README` §5-0,
told a buyer to *"edit one cell of `fab/bom.csv`"* — **`fab/bom.csv` is not the
file JLC receives** (`bom_jlc.csv` and `cpl_jlc.csv` are), so that instruction
would have shipped the unbuyable part. Corrected; see RG-P1-1.

---

## 4. What is NOT waived, and is stated as unverified

**Pad correspondence is not MATE compatibility.** `J_THERM_A` / `J_THERM_B`
carry the thermistor pods — third-party SHT45 modules on genuine JST GHR-08V
pigtails. **Whether a genuine GHR-08V plug seats and RETAINS in a SHOU HAN
shroud is UNVERIFIED**, and ADR-0024's pod-mismate analysis is written about the
GH *family's* geometry, so a clone shroud is outside what it measured.

This is precisely why the sealed BOM names the **genuine** part. Choosing the
clone now would bake an unverified mechanical-retention risk into an immutable
release — on the connectors that carry the only `TEMP_OK` sensing path — and buy
nothing, because nobody is ordering today. Naming the genuine part costs nothing
and preserves both options, since the fab set does not move under either.

`ORDER_README.md` §5-0 carries this to the buyer as a **mate-and-pull check
before committing the assembly order**, stated plainly rather than buried.

---

## 5. What this waiver claims, exactly

- **"This design is correct."** — TRUE, and independently measured this pass:
  `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` →
  **0 violations / 0 unconnected / 0 parity, exit 0**; `policy_audit.py` →
  **exit 0, FAIL=0** (PASS=28, WAIVED=6, HUMAN=6, N-A=5).
- **"This design is orderable today."** — **FALSE, on one line**, for the reason
  in §2, with the remedy in §3 and the caveat in §4.

**THE MODEL NO LONGER CONFLATES THOSE TWO CLAIMS, AND THAT IS WHY THIS RELEASE
SEALED.** When the paragraph above was first written the release model had ONE
verdict field for both claims, so a lens that judged the design correct and the
part unbuyable had no way to say so — and successive agents declined this board,
every one of them on this single BOM line, with zero design defects in any pass.
The last of them wrote it out loud: *"I would accept the seal ... but sealing is
not the question this verdict field asks."*

Owed skill patches P1 and P10 landed in commit `217ea175` on 2026-07-30, and
this release is the first to seal under them:

- `release_freshness_check.py` now prints and grades TWO verdicts —
  `DESIGN: PASS|FAIL` and `SOURCING: CLEAR|PLANNED-<n>|BLOCKED-<n>` — with new
  check **(f) A-BUY**: a non-orderable release MAY seal, and only OUT LOUD. The
  count, every blocked LCSC and the measurement DATE must appear in the MANIFEST
  gate summary AND on the first screen of `ORDER_README.md`, cross-checked
  against the shipped measurement **in both directions**, so a release may
  neither hide a blocked line nor invent one.
- The `08_reviews` contract now declares `design_verdict: SOUND|DEFECTIVE` and
  `order_verdict: ORDER|DO-NOT-ORDER|BLOCKED-SOURCING`, graded by check
  **(g) M-REV**. The SEAL gate reads `design_verdict`; the ORDER_README reads
  `order_verdict`. Both red-team lenses were RE-GATED fresh-context on that
  vocabulary for this seal, and both returned `design_verdict: SOUND` +
  `order_verdict: BLOCKED-SOURCING` — see `redteam_topology.md` and
  `redteam_layout.md` in this directory.

The split is a NET TIGHTENING, not an escape hatch: before it, a
`sourcing_plan:` entry silently cleared its line whatever its own measured
number said, so a release could seal unbuyable with nothing anywhere saying so.
Now an unclassified shortfall is a FAIL, and this entry classifies itself
`order_status: BLOCKED`.

The remaining items in `owed_skill_patches.md` (P2, P3, P4, P9) are still owed
and deliberately **not** implemented here — a board agent does not edit
`skills/`.
