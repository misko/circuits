# Changelog — crow-mic-pod

## v1.0 — 2026-07-21

First orderable release of the crow-mic-pod project: fresh execution of the
Rev-A pod commission WITH the "ethernet connectors everywhere" directive
already baked in (RJ45 RJHSE-5384 at J1, custom NOT-ETHERNET pinout,
ADR-0004). Design adopted from the archived crow-array-pod v1.1 under
ADR-0005 (provenance + full re-verification); route is THIS project's own
fresh KRT chain (the archive's promoted chain was found stale — canon
M3/3g finding, learnings/routing.md). AOM-5024L + OPA1678 active-balanced
cell (~3 V/V diff), CMT-8504 calibration transducer, TPD2E2U06 entry ESD,
SS14 flyback + empty TVS position, choke/shield reserves unpopulated,
1551WY max-PCB outline.
Gates (all MEASURED this project): ERC severity-all 0; audit PASS x2; DRC
severity-all --refill-zones --schematic-parity = 0 violations / 0
unconnected / 0 parity; KRT waves 11/11 + 43/43, 0 failed; stock 25/25
coded lines (CMT-8504 thin=104, order-day recheck); jlc_twin exit 0, 3
evidence-backed adjudications, missing_models = J1/J2 (hand-solder);
fresh-context pin reviews PASS x2 (RJ45 interop map independently
re-derived); render review: see verification/; policy_audit 0 FAIL.
Released: 07_releases/v1.0-2026-07-21
