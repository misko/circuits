# learnings — stages 1-3 (design docs, parts, rules)

Harvest source for the canon, per M9. Raw evidence lives here; the distilled
conclusions belong in `design-policies.md` only after a harvest pass.

---

## L1 — A SPIKE'S SUMMARY AND ITS ADVERSARIAL PASS CAN DISAGREE, AND THE HANDOFF CARRIES THE SUMMARY

**Issue.** This stage inherited a D-SPEC sourcing spike whose six functions all
returned `sourceable`, presented as "parts are chosen". Reading the spike's own
`adversarial` field for each function told a different story: **five of six
returned WEAKENED and one returned REFUTED.** Three part choices changed and
two derived layout rules were found stated BACKWARDS.

**Root cause.** The verdict field (`sourceable`) answers "can this function be
bought?", which is D-SPEC's actual question. The adversarial field answers "is
this the right part, and are its numbers real?" — a different question whose
answer does not propagate into the verdict. A downstream reader who trusts the
verdict inherits the defects.

**How to avoid.** A spike result should carry a SECOND, separate field — call
it `pick_confidence: confirmed | weakened | refuted` — populated from the
adversarial pass, and the handoff prompt should quote it beside the MPN. Cheap,
mechanical, and it would have surfaced all three swaps in the first paragraph.

`candidate-canon: yes` — suggested ID **D-SPIKE**: *a sourcing spike's
per-function verdict must carry its adversarial pass's confidence, and a
downstream stage may not treat a `sourceable` verdict as a settled PICK.*

---

## L2 — THE STACKUP DECISION MOVED A COMPONENT VALUE, AND NOBODY OWNED IT

**Issue.** The spike's SMA function argued for 2-layer 1.6 mm FR4; its
splitter, attenuator and MCU functions all independently assumed 4-layer. Two
of them quoted DIFFERENT εeff values in the same document. Nobody declared a
stackup, so the microstrip loss term was budgeted at 0.013 dB/mm (a 3 mm line
on 1.6 mm) when the parts force 0.036 dB/mm (0.35 mm on 0.2104 mm prepreg).

**Result.** The chain tilt was under-stated by 2× — 1.64 dB against a re-derived
3.09 dB — and **that error was large enough to change the attenuator value**.

**Root cause.** The stackup is an input to almost every RF number, and it was
treated as a layout-stage output. The 2-layer argument was also decided on the
wrong axis: it optimised the SMA launch, when the binding constraint is that a
50 Ω line on 1.6 mm is 2.9–3.1 mm wide against 0.25–0.30 mm component lands —
**the line does not fit the parts**, which no launch model would ever reveal.

**How to avoid.** For any board with a controlled-impedance requirement, DECLARE
THE STACKUP AT COMMISSION alongside `fab_tier`, and require every loss/geometry
estimate to name it. A parametric spike that does not name a stackup has not
produced a number.

`candidate-canon: yes` — suggested ID **D-STACK**: *on an impedance-controlled
board the stackup is a COMMISSION-stage declaration, not a layout output; a
derived RF number that does not name its stackup is not a number.*

---

## L3 — `adr: 0011` IS OCTAL 9

**Issue.** In `electrical_invariants.yaml`, unquoted four-digit ADR references
with leading zeros are parsed by YAML as OCTAL where the digits allow it:
`0011` → 9, `0012` → 10, `0005` → 5, while `0008`/`0009` stay STRINGS (8 and 9
are not octal digits). `_norm_adr()` then zero-pads, so **`adr: 0011` silently
satisfies ADR-0009 and `adr: 0012` satisfies ADR-0010.**

Not caught by the checker, because both forms produce a valid 4-digit id.

**How to avoid.** Quote the value in the schema example, or have `_norm_adr()`
reject a bare int and require a string. The schema example currently shows
`adr: 0001`, which is unambiguous only by accident.

`candidate-canon: yes` — suggested ID **E-INV-OCTAL** (or a fix to the schema
example). Low severity, near-zero cost, and silent by construction.

---

## L4 — A GATE'S BLAST RADIUS ON A SCHEMA ERROR IS THE WHOLE FILE

**Issue.** One `why:` string the checker judged non-substantive made
`load_invariants` raise, and `--adr-coverage` catches `LoadError` with
`cited = set()` — *a broken file cites nothing*. The report then listed EVERY
protection/topology ADR as uncited, with no mention of the parse failure.

**Root cause.** The failure mode is correct (fail closed) but the MESSAGE is
misleading: it names 10 symptoms and not the cause. A reader would go add
invariants that already existed.

**How to avoid.** On `LoadError` in the coverage path, print the load error
FIRST and say plainly that coverage could not be computed.

`candidate-canon: yes` — generalises past this checker: *when a gate fails
closed on an input error, the report must name the INPUT ERROR, not the
downstream symptoms it causes.*

---

## L5 — E-TOPO CANNOT EXPRESS A LINEAR REGULATOR

**Issue.** `power_topology.py:normalize_type()` maps a part's `type:` to
buck / boost / buck_boost by substring; anything else raises and the gate exits
2. `converter:` is REQUIRED per rail. **An LDO-only board therefore cannot pass
E-TOPO**, and the only ways to get green are to delete `power_tree.yaml`
(a silent skip — the M-COVER class) or to mislabel the part.

Two existing fleet boards carry `type: ldo_regulator_fixed_1v8` and simply do
not list the LDO as a `converter:` — so the gap already exists and is already
being routed around, quietly.

**How to avoid.** Add a LINEAR class that is derived as a legitimate
implementation of a STEP-DOWN requirement, and grade its DROPOUT and
DISSIPATION rather than its topology. Those are the two numbers that actually
kill LDO designs, and neither is checked today. An LDO-only board is not
exotic — it is most small boards.

`candidate-canon: yes` — reported upstream rather than patched here.

---

## L6 — CONNECTOR GENDER WORDS ARE VENDOR-DEPENDENT, AND THE HANDOFF NAMED THE WRONG PART

**Issue.** The mating strategy arrived naming `AD-SMAJSMPP-2` as the SMA→SMP
adapter. It is **SMA JACK → SMP PLUG**: its Pluto-facing end is an SMA jack,
the same gender as the Pluto's own connectors. **It cannot screw onto the
Pluto.** Its mirror has the right SMA end and the wrong SMP end.

**Root cause.** Amphenol and Cinch use OPPOSITE plug/jack words for the same
physical SMP half. Two parts both labelled "SMP Jack" by a distributor do in
fact mate. The only reliable discriminator is the CENTRE CONTACT (pin vs
socket).

**How to avoid.** For any mated pair, write the gender chain out end to end
naming the CONTACT at each interface and confirm it closes, before ordering.
`part.yaml` already has a `mates:` field for exactly this class of defect (it
exists because a male plug served weeks as a receptacle) — it should carry the
contact, not just plug/receptacle.

`candidate-canon: yes` — suggested extension to the existing `mates:` field:
*record the CENTRE CONTACT (pin/socket), not only the shell gender, and for a
multi-part mating chain record the chain.*

---

## L7 — THE FAIL-SAFE FAILURE IS THE ONE THAT REACHES A SEAL

**Issue.** PlutoPlus IO is 1.8 V and RP2040's VIH is a flat 2.0 V, so the GPIO
header — the control surface the VERBATIM brief asks for — would have read
permanently LOW.

**Why it matters more than a normal bug.** The failure is FAIL-SAFE. It passes
every test that asks "can this board spuriously enter loopback", which is the
question a safety-minded reviewer asks. It surfaces only as "the GPIO control
doesn't work", plausibly after seal.

**How to avoid.** When a design has a declared SAFE state, review must ask both
questions: *can it reach the unsafe state when it should not*, and *can it
reach the FUNCTIONAL state when it should*. The second is the one that gets
skipped.

`candidate-canon: yes` — suggested addition to the red-team topology/protection
lens's required-question list.
