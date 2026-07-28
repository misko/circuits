# E-INV RED VERIFICATION — cooksense v1.3, 2026-07-26

Canon: a gate that cannot fail is worthless. This file proves the E-INV
checker CAN fail, against the **83 invariants this release actually ships**
(the v1.2 predecessor of this file proved it against 63, and was carried
forward unchanged onto an 83-invariant release — 20 invariants had no
can-fail proof at all).

Method: mutate ONE invariant in electrical_invariants.yaml, run the checker,
require a non-zero exit naming that invariant, restore, require exit 0 and a
byte-identical file. Both mutations below are semantic (a real net / a real
value), not syntax errors.

```
invariant kinds present: ['net_has_part', 'part_value', 'pin_on_net', 'series_chain']  (total 83 invariants)

BASELINE: exit 0 -> E-INV OK: 83 invariants hold against cooksense.net

net_has_part   RED-TEST SKIPPED (no single-token mutation that is unambiguous)
part_value     mutate 'equals: "1k"' -> 'equals: "100k"': exit 1  RED (checker FAILED as required)
                E-INV FAIL: 1/83 invariants violated (netlist cooksense.net):
                  part_value (ADR 0011): R_WDPETPD is 1kΩ (1k), invariant requires 100k — THE 100k VERSION OF THIS PART PASSED ALL THREE WD_PET TOPOLOGY ASSERTS. R_WD
pin_on_net     mutate 'net: CONTACTOR_C' -> 'net: GND': exit 1  RED (checker FAILED as required)
                E-INV FAIL: 1/83 invariants violated (netlist cooksense.net):
                  pin_on_net (ADR 0011): J_ISOLOOP.1 is on net 'CONTACTOR_C', invariant requires 'GND' — the opto-isolated loop lands on J_ISOLOOP, the ONE 4-pole 3.5
series_chain   RED-TEST SKIPPED (no single-token mutation that is unambiguous)

RESTORED: exit 0 -> E-INV OK: 83 invariants hold against cooksense.net
file restored byte-identical: True
```

## Coverage and its limits, stated honestly

| assert kind | invariants | RED-proved |
|---|---|---|
| `net_has_part` | 6 | no — see below |
| `part_value` | 2 | YES |
| `pin_on_net` | 71 | YES |
| `series_chain` | 4 | no — see below |
| **total** | **83** | **73 of 83 invariants are of a RED-proved kind** |

`net_has_part` and `series_chain` are NOT red-proved here. Both are
structural asserts whose single-token mutation is ambiguous (changing a part
name or a chain member can produce a *different valid* assertion rather than
a false one), so a mechanical mutation would prove nothing. They are
exercised by tests/t1_electrical_invariants.py, which carries known-bad
fixtures for both. That is a weaker statement than the two above and it is
made deliberately rather than rounded up.
