# ADR-0006 — A fab artifact is graded as its RECIPIENT will parse it, not as we wrote it

status: proposed
date: 2026-07-27
tags: canon, fab, bom, jlcpcb, meta

## Context

`crow-recorder-central-v2` v1.5's BOM was uploaded to JLCPCB and parts "were not
being picked up by their web processing".

Every BOM check this repo owns asks **"is this value correct?"** —
`bom_source_check` leg A (BOM LCSC == source LCSC), leg C (decoded catalog value
== labelled value), A-POP (population), A-ROT (rotation), A-STOCK (availability).
All semantic. All judged by our own lights.

**Not one asks whether the recipient can PARSE the file.**

That is canon M1 again — checker and checked must not share a method. Every BOM
check reads the document the way WE wrote it. None reads it the way JLC will.
It is exactly the F-PAYLOAD lesson from ADR-0004 (nothing had ever read the
gerber the way the fab reads it), moved from the copper to the BOM.

### What was measured, fleet-wide

| | |
|---|---|
| rows with **blank MPN** | **914 / 1205 (76 %)** |
| rows whose **Comment is an LCSC code or a generator placeholder** | **470 / 1205 (39 %)** |
| BOMs containing non-ASCII with **no UTF-8 byte-order-mark** | **23 / 26 (88 %)** |

### The root cause is sharper than "the exporter omits MPN"

`export_jlc_package.py` fills the MPN column from an **OPTIONAL, HAND-MAINTAINED
SIDE-FILE**:

```python
mpn_map = {}
mpn_path = out / "lcsc_mpn_map.csv"
if mpn_path.exists():                       # <- opt-in
    ...
w.writerow([..., mpn_map.get(code, ""), code])   # <- silently blank on a miss
```

**Only ONE project has ever created that file** — `usb-hub-3s-v3`. Eight of nine
have zero, so their BOMs ship 100 % blank MPN and nothing notices.

Meanwhile **the authoritative MPN already exists**: `02_parts/<MPN>/part.yaml`,
where the DIRECTORY NAME IS THE MPN. The exporter does not look there.

Three previously-named defect shapes, stacked:

1. **A second home for a fact that already has one.** `02_parts/<MPN>/` is the
   MPN; `lcsc_mpn_map.csv` is a hand-maintained duplicate that drifts. The same
   drift gave cooksense v1.1 thirteen CPL rows contradicting its own MANIFEST.
2. **A silent default.** `mpn_map.get(code, "")` — a miss produces a blank
   column with no warning, the `row_kind` failure shape exactly (canon M-COVER).
3. **Opt-in by construction.** A capability nobody is required to use is a
   capability most boards will not have.

The variance across usb-hub's own releases proves the mechanism:

| release | blank MPN | why |
|---|---|---|
| v1.0 – v1.4 | all | no side-file yet |
| **v1.5** | **0** | side-file present and complete |
| v1.6 – v1.8 | 3 | side-file present, but the 3 parts ADDED in v1.6 were never appended to it |

Those three — `C25757`, `C2296`, `C2297` — **all have `02_parts` dossiers**
(`0402WGF1603TCE`, `KT-0805Y`, `KT-0805G`). The MPN was sitting in the tree the
whole time; the exporter read the duplicate instead.

### The exporter's own comment documents the user's symptom

```
# Optional OUTDIR/lcsc_mpn_map.csv (LCSC,MPN): adds an exact manufacturer
# part number column — JLC's matcher auto-selects far more reliably with
# the full MPN (a Comment like "LM5145" left C485912 at "No Part Selected";
# "LM5145RGYR" matches).
```

**The fix already existed and its author had already diagnosed this exact
failure — "No Part Selected".** It was made optional, and 8 of 9 boards never
opted in. A known remedy behind an opt-in flag is not a remedy.

### Two further legibility defects in the same file

**The Comment column carries three different kinds of thing** — real values
(`1nF`), LCSC codes (`C82317`), and generator placeholders (`simple_inductor`,
`simple_chip`). On crow-recorder-central-v2, **24 of 49 rows have no
human-readable value at all**. A row nobody can read is a row nobody can check.

**Encoding.** The file is valid UTF-8 and `Ω` is correctly `CE A9`, but there is
**no byte-order-mark**, so a reader defaulting to GBK/CP936 renders those two
bytes as `惟` — which is what the user saw. Nothing is corrupt; the reader's
assumption is wrong, and we gave it nothing to correct itself with.

### And one silent substitution nobody would have caught

Our source says `C82317` for U5 in three places (`part.yaml`, the `.tsx`, the
shipped BOM). **JLC's resolved output says `C131025`.** It redirected our code
to a different one. We had no mechanism to notice, and this repo has already
shipped two DO-NOT-ORDER releases from the substituted-part class.

## Options

- **Populate the side-file for every board.** REJECTED — it keeps the second
  home, so it keeps the drift, and it stays opt-in.
- **Emit MPN from `02_parts/` and keep blanks silent.** REJECTED — a coded row
  with no MPN would still ship unnoticed.
- **Read the authoritative source, FAIL on a miss, and grade the artifact the
  way the recipient parses it.** CHOSEN.

## Decision

### F-LEGIBLE, into `design-policies.md`

> **F-LEGIBLE — a fab artifact is graded as its RECIPIENT will parse it, not as
> we wrote it.** Semantic correctness is necessary and not sufficient: a value
> that is right and unreadable buys nothing, because the machine that consumes
> it is not ours and does not share our assumptions.

### Four checks — three mechanical, one human-gated

| ID | property | why |
|---|---|---|
| **F-MPN** | every coded row carries **both** MPN and LCSC, MPN resolved from `02_parts/<MPN>/`; a coded row resolving no MPN is a **FAIL**, never a blank | two independent match paths, so a stale or merged code cannot kill a row silently. Redundancy as design — the same reasoning that puts one cooksense net on two screws |
| **F-WORDS** | the Comment column is a human-readable value: never an LCSC code, never a `simple_*` placeholder | 470 rows currently cannot be reviewed by a human on either side |
| **F-ENCODE** | the file decodes **identically** under UTF-8 and under the recipient's likely default (cp936) | three lines to test; fix is a BOM marker or ASCII `Ohm`, and the check is indifferent to which |
| **F-ECHO** | JLC's RESOLVED BOM is diffed back against ours; a substitution is a FINDING | human-gated, beside the existing A-POL order-preview ritual. **The only thing that would have caught C82317 → C131025** — and the user performed it manually this session by pasting JLC's output back |

`lcsc_mpn_map.csv` is RETIRED as an input. If a board needs an MPN override, it
belongs in the part's own `part.yaml`, which is the one home.

### Free RED fixtures

**23 of 26 sealed BOMs** fail at least one check today. Nothing synthetic needs
building — the same property ADR-0004 and ADR-0005 relied on. The defects keep
supplying their own known-bads.

## Consequences

### Sequencing

1. **Fix `export_jlc_package.py`** — one file, all boards inherit it. MPN from
   `02_parts/<MPN>/`, a real value into Comment, and the encoding decision.
2. **F-MPN / F-WORDS / F-ENCODE** with fixtures drawn from the sealed BOMs.
3. **F-ECHO** as an ORDER_README ritual beside the rotation preview.
4. **`fleet_regrade.py`** already exists — run it to enumerate which sealed
   releases are affected. Expect most of them.

Sealed releases are NOT retro-fixed (07_releases immutability). A board that
needs a legible BOM gets a new version; the regrade tells us which.

### NOT built, and why

**Auto-upload to JLCPCB.** F-ECHO stays human-gated. An API integration is a
much larger commitment and would require handing over credentials — the same
line already drawn on the Mouser/Nexar APIs.

**Any conclusion about the twelve zero-stock rows.** Twelve rows came back `0`
with no price, including `C1525` — a 100 nF 0402, one of the most stocked parts
in existence. Simultaneous genuine stock-out of twelve including that one is
implausible; a matching failure caused by the defects above is more likely. **But
that is a hypothesis, not a finding**, and it is not resolvable from outside
JLC's UI. It becomes a skill issue only once someone checks `C1525` in their
part search and reports which it was.

### What this does not do

It does not make JLC accept the BOM. It removes every reason we control for JLC
to fail to parse it, and it makes a substitution visible when JLC changes
something on their side.
