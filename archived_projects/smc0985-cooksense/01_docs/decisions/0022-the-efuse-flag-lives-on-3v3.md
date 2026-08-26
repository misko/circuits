# ADR-0022 — The eFuse fault flag lives on 3V3, and the divider is deleted

Status: accepted, 2026-07-29 (cooksense v1.7)
Supersedes: the un-numbered "PIN P0-b divider" decision recorded in the v1.7
draft `cooksense.tsx` comment and in `electrical_invariants.yaml`. That decision
was WRONG and is recorded here as wrong rather than quietly removed.

## Context

`U_EFUSE` is a TPS259573 (SLVSE57C). Its `/FLT` pin 6 is **open-drain**: it can
pull LOW and nothing else. The board reads it in software at the MCP23017
expander `U_EXP` **pad 1 = GPB0** (not GPA0 — pad 21 is GPA0 and carries
`RAIL_EN_A`, an output; the whole v1.7 paper trail had this wrong, PIN Q-1), and
a human reads it at `TP_PGOOD`.

Two review findings, one week apart, are the same defect seen from both ends.

**PIN P0-b (2026-07-28).** `R_PG`, the flag's pull-up, hung on `5V_PROTECTED`.
With no fault the node idled at **5.0 V** into a part whose absolute-maximum
input is VDD + 0.3 = **3.6 V** — roughly 14 µA of continuous injection into 3V3
through the input clamp, forever, on the part that also carries five safety
readbacks.

**PIN-P0-1 / TOPO P1-1 (2026-07-28), found independently by two lenses with no
shared method.** The remedy v1.7 shipped for P0-b was a 10 k / 22 k divider from
`EFUSE_FLT_N` to a new net `EFUSE_FLT_DIV`, computed as
5.00 × 22/32 = **3.4375 V**. That arithmetic treats `EFUSE_FLT_N` as a stiff 5 V
source. It is not one. Its **only** source of logic-high is `R_PG` itself, so
the true network is R_PG + R_top over R_bot:

| | |
|---|---|
| chain | 100 k (`R_PG`) + 10 k (`R_FLTDIVT`) over 22 k (`R_FLTDIVB`) |
| ratio | 22/132, **not** 22/32 |
| level at `U_EXP.1` | **0.833 V** |
| MCP23017 V_IH(min) = 0.8 × VDD | **2.640 V** |
| MCP23017 V_IL(max) = 0.2 × VDD | 0.660 V |

0.833 V sits in the **indeterminate band**: not a guaranteed high, not a
guaranteed low. **The eFuse fault readback could never report power-good.** The
"protection" killed the function.

There is no value fix. At `R_PG` = 100 k, solve
3.3 ≤ 5 · R_b/(100k + R_t + R_b) with R_t > 0 and R_b chosen freely: the ratio
is bounded above by R_b/(100k+R_b) → 5 V × that must reach 2.64 V, requiring
R_b ≥ 111.9 k **and** R_t ≈ 0. **No R_top > 0 solution exists.** The choice is
between resizing `R_PG` itself and moving it.

`TP_PGOOD` was deliberately left on the "raw" node with the recorded rationale
that *"the instrument must see the real node."* **That rationale was false as
built.** The divider's 32 k loaded the 100 k pull-up, so the node a probe would
have touched rested at 5.000 × 32/132 = **1.212 V**, not 5 V. Recorded, refuted,
kept.

## Decision

> **Move `R_PG`'s top end from `5V_PROTECTED` to `3V3`, and delete both divider
> resistors.**

`R_FLTDIVT`, `R_FLTDIVB` and the net `EFUSE_FLT_DIV` cease to exist. `U_EXP.1`
and `TP_PGOOD` connect directly to `EFUSE_FLT_N`.

Why this is sound and not merely convenient:

- **The eFuse does not care which rail.** SLVSE57C specifies no minimum pull-up
  voltage for `/FLT`; the pin's absolute maximum is 20 V, so 3.3 V is deep
  inside it. The flag's *function* — pull low on fault — is unchanged.
- **Both defects die at the root.** The node idles at exactly 3.300 V, which is
  simultaneously inside the 3.6 V abs-max (P0-b) and above the 2.640 V V_IH
  (P0-1). No band, no ratio, no arithmetic to get wrong.
- **It removes parts.** Two 0402s and one net leave the design. The competing
  option (keep 5 V, delete `R_FLTDIVT`, set `R_FLTDIVB` ≈ 150 k) keeps a
  resistor whose value has a 112–257 k admissible window that depends on
  `R_PG` — a constraint coupling two parts across the schematic.
- **`TP_PGOOD` reads what the firmware reads.** One number in the bring-up
  table instead of two, and the number is now true.

**Leakage, carried explicitly.** 100 k is a high-ish pull-up. Against the
MCP23017's ±1 µA input leakage and the eFuse's 1 µA `/FLT` leakage, worst case
2 µA × 100 k = **200 mV** of droop, leaving 3.100 V against V_IH 2.640 V —
**+460 mV**. That is the reason `R_PG`'s value is itself asserted, not just its
rails.

## The check, not the claim (ADR-0007)

The deleted block asserted `part_value` on both divider legs and `pin_on_net` on
all four of their ends. **Every one of those six asserts PASSED on the broken
board.** They graded the mechanism — two resistors exist, at these values, on
these nets — and nothing graded the outcome. E-INV was 136/136 green while the
pin it existed to protect was dead.

This ADR therefore lands with a `node_level` assert (ADR-0007's new kind), which
resolves the DC network from the netlist and grades the resulting level against
the receiver's published thresholds:

```yaml
- assert: node_level
  net: EFUSE_FLT_N
  receiver: U_EXP.1
  driver_state: released
  must_be: logic_high
  adr: "0022"
```

and with `pin_on_net R_PG.2 → 3V3`, which is the single assert that
distinguishes the fixed board from the broken one.

**A checker defect was found while landing this.** `electrical_invariants.yaml`
declared `supplies: {5V_PROTECTED: 5.0, N3V3: 3.3}` — the tsx author-prefix
form. No net named `N3V3` exists in the netlist (the converter strips the `N`),
so the 3V3 rail was **invisible to every `node_level` grade**. It did not
misreport the divider (that network genuinely hung off 5V_PROTECTED) but it
would have reported UNREACHED on this fix. Corrected to `3V3: 3.3`, and found by
reading the netlist, not by any gate — recorded because the same class of typo
would silently weaken any future `node_level`.

## Consequences

- BOM: −2 lines-worth of placements (`R_FLTDIVT` C60490, `R_FLTDIVB` C25768);
  C60490 remains on the board via the five ADR-0020 series resistors, C25768's
  other users are unaffected.
- Copper: two 0402 lands and the `EFUSE_FLT_DIV` net disappear; `R_PG`'s pad 2
  moves from the 5V_PROTECTED pour to 3V3. Re-placed and re-routed, not patched.
- `ORDER_README` bring-up: `TP_PGOOD` reads **3.3 V healthy / ≈ 0 V faulted**,
  where v1.6 said 5 V and the v1.7 draft would have delivered 1.212 V.
- The 5 V domain no longer touches any MCP23017 pin anywhere on this board.
