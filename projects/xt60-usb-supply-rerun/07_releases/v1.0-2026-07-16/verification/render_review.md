# Fresh-eyes render review — findings and dispositions (v1.0)

Reviewer: independent agent, renders only (schematic PNGs, layer SVGs,
assembly.pdf), 2026-07-16. Electrical trace: CLEAN (FB dividers 22k/3k ->
5.000 V both rails; TVS cathode to VBAT_P; P-FET D=battery/S=load;
per-port D+/D- DCP shorts; CC Rp 10k to 5V_C).

| # | Finding | Severity | Disposition |
|---|---|---|---|
| 1 | XT60 polarity must be physically verified (pad 1 = "-") | BLOCKER (process) | Pad-1='-' verified 3 ways in 02_parts/XT60PW-M/part.yaml + pin_review.md PASS; physical beep test is step 1 of the ORDER_README first-power ritual |
| 2 | Silkscreen text collisions, values unreadable | BLOCKER (render) | Values are on F.Fab, not silk — the reviewed render composite- stacked F.Cu+silk+fab. Genuine silk refdes merges (RFA/RFC pairs, COUT_C3/C4, U6/R3/R4 cluster, CVCC/CBS) fixed via REF_TEXT_OFFSET pass in generate_board.py; silk-only render re-verified |
| 3 | ILMT tied directly to GND — is that a valid setting? | SHOULD-FIX (question) | RESOLVED-VALID: SY8368 pin table (AN_SY8368 p.2): ILMT low = 8 A valley limit, the designed value (ADR 0007); confirmed independently by pin review |
| 4 | USB-C D+/D- floating -> legacy A-to-C devices fall back to 500 mA | SHOULD-FIX | FIXED: BC1.2 DCP short across A6/A7/B6/B7 (net DCPC), ADR 0008 |
| 5 | Mounting-hole ref text clipped off-board | SHOULD-FIX | FIXED: H1-H4 references hidden (board-only parts, identity in fab data) |
| 6 | assembly.pdf scale too small | COSMETIC | ACCEPTED: PDF is vector — zoomable; PNG renders provided alongside |
| 7 | USB-A jack drawing lacks signal labels (pin map from 3 agreeing sources) | NOTE | Bring-up beep test added to ORDER_README (shell->GND, VBUS-not-shell) |
