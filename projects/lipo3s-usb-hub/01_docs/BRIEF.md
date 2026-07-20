# BRIEF — lipo3s-usb-hub

<!-- prompt-verbatim-begin -->
Ok lets try out our new system. Please from scratch start a new project, and lets design a board that takes 3S lipo XT60 power as input , and outputs 3 x USB A ports (2.5A max) and 1 x USB C port (6A max). Please internally research and make all design decisions. The output should be a fully designed , placed, routed board with JLCPCB manufacturing files
<!-- prompt-verbatim-end -->
sha256: b26444b8fbed5e2b6eee7713d3e4afa0e9e546fa99f8a33736157eb5da415230

## Context
Act 2 validation of the tscircuit-native pipeline (ADR-0002). This is the SAME
brief that commissioned usb-power-3s (the project's first board, built the old
hand-KiCad/schwriter2 way, sealed v1.3-2026-07-17). Built here FROM SCRATCH through
the new tscircuit-native system (TSX authoring -> converter -> tsx_to_board.sh).
usb-power-3s is PRIOR ART / a sanity cross-check only — design decisions are made
independently and may differ.

## Parsed requirements
- P1: Input 3S LiPo via XT60 (≈9.0-12.6 V; abs-max headroom for a fresh pack ~12.9 V).
- P2: 3x USB-A output ports, 2.5 A max each.
- P3: 1x USB-C output port, 6 A max.
- P4: Internally research + make ALL design decisions (user directive — NO clarifying
  questions; decide conservatively, record every choice as D#).
- P5: Deliverable = fully designed, PLACED, ROUTED board + JLCPCB manufacturing files
  (i.e. a sealed, orderable release).

## Q&A
- A1 (user directive, verbatim in P4): "Please internally research and make all design
  decisions." → the commission's ask-2-4-questions step is WAIVED by the user; all
  open choices become D# with rationale, flagged in the final report.

## Decisions (D#, appended over time)
