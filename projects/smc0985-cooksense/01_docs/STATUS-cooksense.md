# STATUS beacon — cooksense MAIN board (live head; overwritten each transition)
<!-- reader parses from here down -->
stage:   v1.1-floorplan
step:    "v1.1 shrink (D7: pitch 20->15.24mm, single row) BLOCKED pre-build: rot90 relay courtyard 19.90mm along the row => 15.24mm pitch overlaps courtyards 4.66mm (parts collide); v1.0's 20mm pitch already at 0.10mm courtyard gap — zero pitch shrink exists in this orientation. 15.24mm is coupling evidence from the rot0 column layout, not a rot90 fit claim."
measure: "courtyard +-9.95mm (fp CrtYd) along row @ rot90; body 19.3mm; pitch 15.24 => -4.66mm overlap; current gap 20.00-19.90=0.10mm"
state:   blocked
op_pid:  none
next:    "USER DECISION (escalated, D7): (a) no meaningful single-row shrink (edge trims only, ~246x92 best case); (b) run the relay-coupling bench measurement (U+D+PRESS triple energize on physical v1.0 boards) to license the two-row repack; or (c) vertical-relay topology redesign. No source/board change made; v1.0 (cooksense-v1.0-2026-07-23) remains the orderable release."
updated: 2026-07-23T21:45:00
