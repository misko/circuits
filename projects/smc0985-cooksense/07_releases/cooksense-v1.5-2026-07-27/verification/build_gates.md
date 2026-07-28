# Build-gate evidence — cooksense v1.3, 2026-07-26

These four gates were asserted in prose only in the previous staging. Their
actual output now ships.

## P-COLLIDE (canon P11, generate_board_generic.py, after legalize)
```
P-COLLIDE: 0 pad shorts, 0 anchored courtyard overlap(s) (795 copper pads, 83 anchored parts)
```
No two pads on different nets share copper; no two ANCHORED footprints
overlap courtyards. This is the gate that refused the v1.3 placement in
which J_ESTOPLOOP sat inside J_DOOR.

## contracts_audit (structure governance)
```
contracts_audit: 189 files, 0 violations
```

## tests/run_tests.sh (fast tier)
```
  TOTAL                    498 passed, 0 failed, 284 known-bad fixtures made their checker fail
ALL SUITES PASSED
```
284 of those are KNOWN-BAD fixtures that made their checker fail as required.

## stitch gate (route_and_stitch_generic.py, final pass)
```
seed_stubs: 58 pin(s) served (60 segments/vias placed, 0 idempotent-skip), 0 refused
gate: clean
```
