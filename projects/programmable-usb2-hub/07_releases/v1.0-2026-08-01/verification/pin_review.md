subject: programmable-usb2-hub v1.0-2026-08-01 pre-seal staging
date: 2026-08-01
reviewer: pin-review (three fresh-context groups plus targeted fix confirmations)
context-given: zero-context
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
board_sha256: 886c12bc3cc277e35faad2590a61dc86df5f402bca6505b1345ba6820c367441

# Fresh-context pin-review aggregate

All 34 multi-pin/high-risk references passed against manufacturer authorities.
The generated P-PINMAP gate independently graded 33 multi-pin references and
385 physical identities across part.yaml, tscircuit ports, and board pads.

## Final per-reference verdicts

- PASS: F1, J2, J3, J4, J5, J6, J7, Y1.
- PASS: Q1, Q2, Q3, Q4, Q5, Q6.
- PASS: U1, U2, U3, U4, U5, U6, U7, U8, U9, U10, U11, U12, U13,
  U14, U15, U16, U17, U18, U19, U20.
- FAIL: none.
- QUESTION: none.

## Closed findings

- Q1-Q6 physical drain identities were repaired in source and footprints;
  the fresh protection/switches review passed all 11 assigned references.
- U4 was rechecked against the exact automotive DS43698 authority and passed.
- J2 signal winding is CCW in top view and matches the TE drawing. Its two
  physical shell locks remain visible as two pad rows and their intentional
  common-shell collapse is declared `fused: true` with manufacturer evidence;
  the targeted fix-confirmation review passed J2.

Verbatim evidence is archived in `08_reviews/` under the dated protection,
power-control, connectors/clock, J2/U4 re-gate, and J2 fix-confirmation files.
The order verdict reflects the independently measured U4 catalog-stock
shortfall; it is not a pin-design finding.
