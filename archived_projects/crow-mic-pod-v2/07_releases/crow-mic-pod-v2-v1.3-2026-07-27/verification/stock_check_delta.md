# stock re-check delta — arming run (2026-07-25) vs seal-day run (2026-07-26)

Both runs PASS 15/15 coded lines, 0 uncoded. The tight line is unchanged:
C22359707 (LS1, buzzer) stock = 69 in BOTH runs (need 1/board; >= 5x need but
thin — re-check same-day at order). All other deltas are drift on
million-plus-stock basic passives (e.g. C25803 7,606,271 -> 7,925,541) or
five-digit expand parts (C192421 4,887 -> 4,860; C49066 60,511 -> 60,504).
verification/stock_check.json carries the seal-day (2026-07-26) run.
