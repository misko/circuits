# ADR-0030 — the part that binds the declared ambient is the REED RELAY at
# +70 °C, not the LDO and not the fuse — so 65 °C was righter than its own reason

---
id: 0030
date: 2026-07-30
status: accepted
---

tags: power, thermal, envelope, parts, gates, bench-obligation
relates: ADR-0029 (declares the 65 °C envelope — this ADR corrects its
JUSTIFICATION and withdraws one of its claims), ADR-0026/0027/0028 (the LDO
analysis), ADR-0023 (the reed pull-in invariant, which already read this
dossier's temperature rows)
amends: `02_parts/MF-MSMF200L-2/part.yaml` (`limits:`),
`07_releases/cooksense-v1.7-2026-07-30/ORDER_README.md` (§0-T, §7b)

## Context

ADR-0029 narrowed the declared operating ambient to 65 °C on a thermal argument
about `U_LDO`, and named `F1`'s **−40…+85 °C** as the next constraint below the
junction. Four fresh-context lenses were then re-gated against the staging
archive. All four returned `design_verdict: SOUND` with **zero P0s** — and
**three of the four independently raised the same P1**, which is the strongest
signal this pass produced.

**The board's narrowest operating-temperature rating is `DIP05-1A72-13L` at
−20…+70 °C**, and twelve of them are fitted, including `K_STOP`. MEASURED (by
me, sweeping the `t_op` declarations of all 47 `02_parts/*/part.yaml`): **+70 °C
is the UNIQUE minimum.** `F1`'s +85 °C — the figure ADR-0028's "what binds"
table, ADR-0029 and the first draft of ORDER_README §0-T all named — is **15 °C
looser** and was never the binding constraint.

The fact was already in the tree. `02_parts/DIP05-1A72-13L/part.yaml` carries it
twice (`t_op: "-20..+70C"` and `t_op: [-20, 70]`, cited to DS p.3 Relay Data),
and `02_parts/S4B-ZR-SM4A-TF/part.yaml` calls the DIP05 "this board's binding
limit" in prose. **Nothing read it into the envelope argument**, and the same
dossier publishes a `v_pullin_max_75C` row labelled "the hard limit" for a part
that is not rated to 75 °C at all.

## Options

**(a) ACCEPT THE FINDING, CORRECT THE JUSTIFICATION, KEEP THE 65 °C DECISION —
CHOSEN.** The decision does not move; only its reason and one of its claims do.

**(b) RE-OPEN THE ENVELOPE DECISION.** Rejected: the finding makes 65 °C **more**
necessary, not less. There is nothing to re-decide.

**(c) TREAT IT AS A P0 AND BLOCK THE SEAL.** Rejected: 65 < 70, so the declared
envelope is INSIDE the rating with margin. A P0 is a defect in the artifact;
this is a defect in the artifact's EXPLANATION, and the remedy is a document
edit taken before the seal — which is exactly what pre-seal review is for.

## Decision

**1. THE BINDING CONSTRAINT AT THE DECLARED AMBIENT IS THE RELAY, AND IT IS THE
TIGHTEST POSITIVE MARGIN ON THE BOARD.**

| Ta | relay margin to its +70 °C rating | `U_LDO` junction margin (honest) |
|---|---|---|
| **65 °C — DECLARED** | **+5.00 °C** | +13.3…16.4 °C |
| 70 °C | 0.00 °C | +8.3…11.4 °C |
| 75 °C | **−5.00 °C — OUTSIDE THE RATING** | +3.3…6.4 °C |

**65 °C is the only rung on the BRIEF's enclosure ladder (`50 / 55 / 65 / 75`)
that fits twelve DO-NOT-SUBSTITUTE relays at all.** ADR-0029 chose it for the
LDO junction and got the relay for free without knowing it. An integrator sizing
an enclosure must design against **5.00 °C**, not against 13.3…16.4 °C.

**2. ADR-0029's "PASSING B1–B6 MAY REOPEN 75 °C" IS WITHDRAWN AND REPLACED.**
This is the part of ADR-0029 that was not merely under-explained but **wrong**,
and it is named plainly rather than quietly softened. B1–B6 measure the LDO's
dropout at 0.2 A, `F1`'s tempco, `θ_JA`, `ΔT_board` and a thermal time constant.
**No bench measurement moves a catalogue relay rating.** The correct statement:

> Passing B1–B6 is **NECESSARY BUT NOT SUFFICIENT** to reopen 75 °C. What B1–B6
> alone can reopen is the range **65 → 70 °C**. Above 70 °C additionally requires
> re-rating or replacing the twelve `DIP05-1A72-13L` — a BOM change and therefore
> a NEW BOARD REVISION, **not** a documentation-only supersede.

On the relay axis 75 °C is not unproven, it is **refuted**.

**3. §7b ITEM B5 ASKED FOR A STATE THE HARDWARE CANNOT PRODUCE, AND IS
CORRECTED.** MEASURED (by me, from the shipped `fab/bom.csv`): the selector lines
come from **two** SN74HC238 **1-of-8** decoders (`C5620`, one BOM row covering
`U_DECD` + `U_DECU`), so at most **one U coil + one D coil + PRESS + STOP = FOUR
coils** can be energised at once. "All 12 reed coils energised" is forbidden by
the interlock, by design. B5 now measures the four-coil case and requires the
report to state the coil count and any extrapolation. **This makes the published
+1.55…+4.65 °C board-rise band conservative — in the right direction, and now
for a written-down reason rather than by accident.**

The release already contained the contradicting fact: its own `R-POUR` waiver
calls the all-12 case "un-reachable … which the interlock forbids". **Two files
that were never read together** — the same shape as ADR-0028 Decision 1 and
Decision 8, and the third instance of it on this board.

**4. `F1`'s VOLTAGE ROW IS NOT ESTABLISHED, AND BOTH PRIOR CLAIMS ABOUT IT WERE
WRONG.** `02_parts/MF-MSMF200L-2/part.yaml` asserted `type: polyfuse_2a_16v` /
`vmax: "16 V"` on the `MF-MSMF200/16X` row; the re-gate-4 topology lens read the
same committed PDF and concluded `/8X` (8 V). MEASURED (by me, `pdftotext
-layout` on this dossier's own committed `BOURNS-MF-MSMF-SERIES.pdf`): **neither
is established.** The "How to Order" scheme is `MF - MSMF <Ihold> / <Voltage> X -
<packaging>` with the voltage vocabulary `{6, 8, 12, 16}`, and **`L` is not in
it** — `MF-MSMF200L-2` is an LCSC catalog string, not a Bourns order code in this
scheme.

**What IS established is the load-bearing half:** the electrical table lists
`MF-MSMF200/8X`, `/12X` and `/16X` and **all three carry R Min 0.020 Ω and R1 Max
0.070 Ω**. So the 70 mΩ that ADR-0027's 328.29 mΩ series sum, ADR-0028's dropout
ladder and E-TOPO's headroom all spend is **INVARIANT under the ambiguity — no
margin on this board moves either way.** Only `vmax` is in dispute; the lowest
candidate is 8 V; the protected rail is 5.250 V max with `D_TVS` clamping at
6.40–7.00 V, both inside 8 V. The dossier now records this as NOT ESTABLISHED
with 8 V as the number to design against, and the vendor confirmation is OWED.

**5. NO COPPER, NO NETLIST, NO BOM AND NO CPL CHANGE.**
`04_kicad/cooksense.kicad_pcb` md5 `9f4fd5fae810f40a52b1035df727243c`,
re-verified unchanged by all four lenses independently.

## Consequences

**What is now true that was not.** The envelope has the right reason attached to
it, the tightest margin on the board is named and quantified, an order document
no longer promises a reopening that cannot happen, and a mandatory bench item no
longer instructs a measurement nobody can take.

**What this commits us to.** An enclosure designed against 5.00 °C of relay
margin, not 13 °C of LDO margin; and a BOARD REVISION, not a docs supersede, as
the price of any ambient above 70 °C.

**What breaks if reversed.** Restoring `F1`'s +85 °C as the named constraint
re-hides a 15 °C error behind a looser part. Restoring the unqualified "may
reopen 75 °C" puts a promise in order paperwork that no measurement can keep.
Restoring B5's twelve coils asks a technician for a state the decoders forbid.

**THE PATTERN, RECORDED BECAUSE IT IS NOW THE THIRD INSTANCE ON THIS ONE BOARD.**
ADR-0028 Decision 1 (a worked example reading an ungraded key), Decision 8 (a
derived constant copied without a link to its deriving ADR), and now TWO more:
a part limit that lived in a dossier and in a neighbouring dossier's prose but
never reached the envelope argument, and a hardware interlock that was written
in a waiver and contradicted in a bench instruction. **Every one of them is a
fact this repository already held, in a file nobody read next to the file that
needed it.** None was found by a gate; all were found by adversarial readers with
no stake in the answer. That is the argument for the review lenses, stated as a
measurement rather than a principle: **three of four lenses, independently, in
one pass, on a board that had already survived eight sealing attempts.**

**Owed skill patch — NOT IMPLEMENTED, `skills/` is outside this board's
partition.** Filed with P15–P18, P20, P21:

* **P22 — a declared ambient must be graded against EVERY part's `t_op`.** Every
  dossier in this fleet already carries `t_op`, and nothing compares the minimum
  of that set against the rail's declared ambient. The checkable form: where
  `power_tree.yaml` declares an ambient, a gate sweeps `02_parts/*/part.yaml`
  `t_op` maxima over the refdes actually ON THE BOARD, names the minimum, and
  FAILS when the declared ambient meets or exceeds it. On this board that check
  is four lines and it would have found in milliseconds what three frontier
  review agents each spent a full pass finding.
