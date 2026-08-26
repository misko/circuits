> ## ⚠️ READ THE CORRECTION AT THE END OF THIS FILE FIRST
>
> This file is **MIXED**. The body below is the historical C22046 record —
> including the line "Status: BLOCKS THE v1.2 SEAL", which is history, and
> a "12 remaining rows" table that is **WRONG on three of its seven codes**.
> The `CORRECTION, 2026-07-26` block at the END of this file is a **CURRENT
> v1.3 measurement** and is what ORDER_README §6 and §13 item 10 rely on.
> It resolves the disagreement, operator-free, in the authority table's
> favour on all seven codes.

---

# MEASURED: C22046 (SN74LVC1G11DBVR, SOT-23-6) CPL rotation is 90 degrees WRONG

**Status: BLOCKS THE v1.2 SEAL. Reported to the coordinator, NOT acted on** —
the fix is a row in `skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv`, which
the coordinator owns and this task was told not to touch.

## What jlc_twin reported

    C22046,U_AND1,ROT-DB-SUGGEST,"fit=0.21mm jlc_offset=180 db=-90.0 src=name-DB
                                  -> add LCSC row C22046,180 to jlc_lcsc_rotations.csv"

…identically for all TEN refs. The task instruction was: do not act on a
90/270-class suggestion — MEASURE it (fit the board footprint against JLC's
cached model, pads matched by NUMBER) and report. Done below.

## The measurement (independent of jlc_twin's own xform)

JLC's cached model, fetched by this run:
`06_build/twin_v12/easyeda/C22046/jlc.pretty/SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BR.kicad_mod`

| pad | JLC model (fp-local mm) | OURS, U_CAND1 de-rotated to fp-local (mm) |
|---|---|---|
| 1 | (+1.350, +0.950) | (−1.137, −0.950) |
| 2 | (+1.350, +0.000) | (−1.137, +0.000) |
| 3 | (+1.350, −0.950) | (−1.137, +0.950) |
| 4 | (−1.350, −0.950) | (+1.137, +0.950) |
| 5 | (−1.350, +0.000) | (+1.137, +0.000) |
| 6 | (−1.350, +0.950) | (+1.137, −0.950) |

Rotating JLC's model by each candidate CPL offset and matching pads **by
number**, mean/worst pad-to-pad distance over all 6 pads:

| offset | mean | worst |
|---|---|---|
| 0° | 2.916 mm | 3.130 mm |
| 90° | 2.066 mm | 2.308 mm |
| **180°** | **0.213 mm** | **0.213 mm** |
| 270° | 2.066 mm | 2.308 mm |

**180° is the answer, and it is not close** — 10x better than any alternative.
The 0.213 mm residual is not error: it is exactly the pad-length difference
(our pad centre |x| = 1.137, JLC's = 1.350, difference 0.213), i.e. the same
KiCad-IPC-vs-EasyEDA fillet class already adjudicated on this board for SOIC/
SOT/SOD packages. At 180° the fit is otherwise perfect.

## What ships today, and why that is a P0

The CPL as exported puts all ten at **270.0** (name-DB `−90`; note a grep for
`SOT-23-6` finds NO row in `jlc_rotations_db.csv`, so the −90 is arriving from
a broader pattern — worth the coordinator's attention when fixing the row):

    U_AND1 270.0   U_AND2 270.0   U_AND3 270.0   U_FAULTAND 270.0
    U_CAND1 270.0  U_CAND2 270.0  U_DECDEN 270.0 U_DECUEN 270.0
    U_LATCHG 270.0 U_OSCLR 270.0

That is **90° off on ten parts**, and the ten are not incidental:

- `U_AND1`, `U_AND2`, `U_AND3` — the entire 7-condition safety AND-chain that
  gates the relay coil rail.
- `U_FAULTAND` — the fault-latch SET gate.
- `U_CAND1`, `U_CAND2` — the external cooking-contactor permission gates.
- `U_DECUEN`, `U_DECDEN` — the decoder-enable STOP gates.
- `U_LATCHG` — the 595 latch-freeze gate.
- `U_OSCLR` — the PRESS one-shot clear gate.

A 90°-rotated SOT-23-6 does not connect its intended nets. Every hardware
safety interlock on this board is one of these ten parts.

This is precisely the incident class `skills/pcb-design/SKILL.md` opens with:
*"crow-recorder-central-v2 v1.2 sealed with U1 at CPL 270 when its own shipped
twin measured 90: 180 degrees off. Cost a superseding release whose fab set
differs from v1.2 in exactly one file."*

## Recommended action (coordinator's call — this task did not take it)

Add one row to `skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv`:

    C22046,180

then re-export the fab package and re-run `jlc_twin`; the ten ROT-DB-SUGGEST
rows should become OK and the CPL should read 180.0 for all ten. The per-LCSC
table already wins over the name DB by design, and the header records exactly
this rationale: *"JLC's zero-orientation is a per-part fact, and two parts that
share a footprint NAME can need different offsets."*

Cross-check available at zero cost: `U_STOPINV` is an SN74LVC1G00 in **SOT-353**
(a different package) and fits at 180 with `db=180.0`, i.e. the name DB is
already right there — the disagreement is specific to the SOT-23-6 row.

## The other 9 twin CRITICALs (PAD-GEOM / POLARITY-CHECK)

Not blocking, but unadjudicated in `03_src/cooksense/rules/twin_adjudications.yaml`
because they are v1.2-new parts:

| refs | LCSC | class | measured |
|---|---|---|---|
| U_ONESHOT | C133954 | PAD-GEOM | SOIC-16 pad 1↔16 ours 4.95 vs JLC 5.48 (Δ0.53) |
| U_CAND1/2, U_DECDEN/UEN, U_LATCHG, U_OSCLR | C22046 | PAD-GEOM | SOT-23-6 pad 1↔6 ours 2.28 vs JLC 2.70 (Δ0.42) |
| D_ESTOP | C5158048 | PAD-GEOM + POLARITY | SOD-323 pad 1↔2 ours 2.10 vs JLC 2.40 (Δ0.30) |
| D_KSTOP | C8678 | PAD-GEOM + POLARITY | SMA pad 1↔2 ours 4.00 vs JLC 4.40 (Δ0.40) |

All four are the SAME precedented fillet/pad-length class already adjudicated
on this board for other refs (D_REVCLAMP is C8678 in the identical SMA
footprint and IS adjudicated). They need adjudication entries written against
the new refs — cheap, but it must happen after the rotation row lands, because
a re-export changes the report.

---

# ADDENDUM (post-fix, 2026-07-25): the row landed, and the 12 OTHER suggestions

## C22046 is CLOSED

Coordinator landed `C22046,180` (commit 95317d5) after independently
re-measuring all ten refs: rms 0.2125 mm at 180 vs 2.0784 mm next best (9.8x),
10/10. Resolver now returns `(180.0, 180.0, 'lcsc')`; without the row it
returned `(270.0, -90.0, 'name')`, reproducing the defect.

Re-export CPL diff vs the pre-fix export, cell by cell:

    rows: pre=186 post=186   added=NONE   removed=NONE
    CHANGED CELLS: 10 — all in the Rotation column, all 270.0 -> 180.0
      U_AND1 U_AND2 U_AND3 U_CAND1 U_CAND2 U_DECDEN U_DECUEN U_FAULTAND
      U_LATCHG U_OSCLR
    columns touched: {'Rotation'}
    bom_jlc.csv: byte-identical to the pre-fix export (rotation is CPL-only)

Exactly the ten expected and nothing else. `jlc_twin` now exits 0.

Third distinct failure mode of name-keyed rotation, per the coordinator: no
`SOT-23-6` rule exists at all, so the −90 arrived from the broader `^SOT-23`
prefix — correct for the 3-pin part, wrong for the 6-pin one.

## The 12 remaining ROT-DB-SUGGEST rows — MEASURED, NOT ACTED ON

None is CRITICAL, none gates the twin's exit, and **none is changed by this
release** — all twelve ship at whatever the name DB gives, exactly as v1.0 and
v1.1 shipped. I measured all seven distinct LCSC codes anyway, with the same
independent operator used on C22046 (JLC's cached model rotated through all four
offsets, pads matched BY NUMBER, rms over every pad):

| LCSC | ref(s) | name-DB | twin says | MY rms 0 / 90 / 180 / 270 | my best | ratio |
|---|---|---|---|---|---|---|
| C2887273 | CE1 | 180 | 0 | 0.030 / 3.797 / 5.370 / 3.797 | **0** | 126.6x |
| C125121 | U_OPTO | 0 | 270 | 7.137 / 0.235 / 7.137 / 10.090 | **90** | 30.4x |
| C157991 | J_LOADCELL | 0 | 180 | 8.707 / 7.100 / 5.000 / 7.100 | **180** | 1.4x |
| C189896 | J_DOOR J_ESTOP J_MODE J_RH_AMBIENT J_RH_EXHAUST | 180 | 0 | 4.940 / 3.497 / 0.250 / 3.497 | **180** | 14.0x |
| C265111 | J_THERM_A J_THERM_B | 180 | 0 | 0.250 / 4.733 / 6.689 / 4.733 | **0** | 18.9x |
| C2683602 | J_KEY_MATRIX | 180 | 0 | 7.969 / 5.638 / 0.250 / 5.637 | **180** | 22.5x |
| C587657 | J_PWR | 0 | 180 | 5.699 / 4.154 / 1.425 / 4.154 | **180** | 2.9x |

**I am NOT proposing any of these as rotation rows, for two honest reasons.**

1. **My operator and the twin DISAGREE on three of the seven** (C125121,
   C189896, C2683602). On C22046 they agreed and the coordinator's third
   measurement agreed too — but 0 and 180 are sign-invariant, so that agreement
   never tested handedness. These three disagreements are the test, and it
   fails. My operator answers "rotate JLC's model by X to land on our
   footprint-local pads"; the twin's `jlc_offset` is the CPL correction relative
   to the board's own rotation. Those are related but NOT the same quantity, and
   until someone reconciles the two definitions on a part whose answer is known,
   neither number should be written into a fleet-wide table. Two operators that
   disagree mean you have no measurement yet, not two candidates.

2. **C157991 (1.4x) and C587657 (2.9x) do not separate.** Compare C22046 at
   9.8x, or C2887273 at 126.6x. A 1.4x margin on a 5-pin THT connector is noise;
   acting on it would be guessing with a decimal point attached.

**The one that deserves the coordinator's eye regardless: CE1.** It is a 220 µF
**polarized** electrolytic, my fit says 0 at 126.6x, and the name DB says 180 —
and "a polarized part shipped 180° reversed" is verbatim the usb-hub-3s-v3 v1.5
incident (C1/C2). It ships in this release at the name-DB value, unchanged from
v1.0/v1.1, so it is not a v1.2 regression; but it is on the ORDER_README §3
human-gate list by name, because a reversed electrolytic is visible in the JLC
order preview and that is the last line of defence.

---

# CORRECTION, 2026-07-26 — THE SECOND OPERATOR IN THIS FILE HAD A FRAME ERROR

Everything above this line is preserved as written. **The "12 remaining
ROT-DB-SUGGEST rows" table is WRONG on three of its seven codes, and the reason
is a defect in my operator, not in the authority table.**

## What was wrong

My operator recovered each footprint's local pad coordinates by de-rotating the
board-absolute positions with a **standard counter-clockwise rotation matrix**.
KiCad's Y axis points **DOWN**. Applying a CCW matrix to a Y-down coordinate
system produces the **mirror image** of the intended rotation, which swaps 0 with
180 and 90 with 270. Every 0/180 code it reported was a coin flip; every 90/270
code was inverted.

Determined empirically, not assumed — `J_KEY_MATRIX` sits at orientation −90°
and its library pad 1 is at (−5.625, −1.850):

| | pad-1 delta from anchor |
|---|---|
| what pcbnew actually reports | **(+1.850, −5.625)** |
| standard CCW matrix | (−1.850, +5.625) — **wrong** |
| Y-down matrix `[[cos, sin], [−sin, cos]]` | **(+1.850, −5.625)** — matches |

## The re-measurement, with no operator at all

The cleanest possible method, and the one that should have been used first:
**compare the two `.kicad_mod` files directly.** Our footprint and JLC's model
are both stored in footprint-local coordinates in the same file format, so no
board frame, no orientation, and no de-rotation is involved — only a centroid
alignment and four candidate rotations.

| LCSC | ref(s) | rms 0 / 90 / 180 / 270 | best | sep | landed row | verdict |
|---|---|---|---|---|---|---|
| C189896 | J_DOOR J_ESTOP J_MODE J_RH_AMBIENT J_RH_EXHAUST | 0.0000 / 2.5000 / 3.5355 / 2.5000 | **0** | exact | 0 | AGREE |
| C265111 | J_THERM_A J_THERM_B | 0.0050 / 4.0520 / 5.7304 / 4.0520 | **0** | 810x | 0 | AGREE |
| C2683602 | J_KEY_MATRIX | 0.0049 / 5.0792 / 7.1831 / 5.0792 | **0** | 1037x | 0 | AGREE |
| C157991 | J_LOADCELL | 7.1276 / 5.0402 / 0.0566 / 5.0402 | **180** | 89x | 180 | AGREE |
| C587657 | J_PWR | 2.7500 / 1.9526 / 0.2500 / 1.9526 | **180** | 8x | 180 | AGREE |
| C125121 | U_OPTO | 7.1366 / 10.0899 / 7.1366 / 0.2350 | **270** | 30x | 270 | AGREE |
| C2887273 | CE1 | 0.0300 / 3.7972 / 5.3700 / 3.7972 | **0** | 127x | 0 | AGREE |

**Seven of seven agree with the authority table**, including the two safety-
critical ones — **C125121 (U_OPTO, the isolation barrier) at 270** and
**C2887273 (CE1, the polarized electrolytic) at 0**. The rms figures also
reproduce the landed rows' recorded numbers (0.0000/2.5000, 0.0050/4.0520,
0.0049/5.0792, 0.0566, 0.2350, 0.0300) — same fit, and now the same label.

**No CPL row changes. No table row changes.** The shipped CPL was already
correct on all seven codes; verified independently by walking the board and the
CPL together, `CPL == (board_rot + landed_offset) mod 360` on every ref.

## What this file got RIGHT, and should be read for

The refusal on line 163 — *"Two operators that disagree mean you have no
measurement yet, not two candidates"* — was the correct call and it held the
line. It stopped seven wrong rows from being proposed into a fleet-wide table on
the strength of a broken operator. **The lesson is not "trust the table"; it is
that the tie-break must be a THIRD method that shares no code with either
side** (canon M1). Here that method was reading two files.

**Cross-reference fix:** line 174 above sends the reader to "ORDER_README §3
human-gate list". The human gate is **§6**, not §3.
