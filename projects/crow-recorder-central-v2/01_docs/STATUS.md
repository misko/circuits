# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

<!-- reader parses from here down -->
stage:   routing
step:    "ROUTING GATE GREEN — DRC 0 violations / 0 unconnected (kicad-cli --severity-all --refill-zones, stitch gate clean). D-BACK reframed (6/8 GND were config, not placement); U8.2 solved via authorized Option A SW-corner re-plan (0V9 In2 detour + 5V L-path, pcb_toolkit-verified); U6 vendored footprint; 5V/U7 reroute; starved via targeted pad_overrides; silk de-collided (RJ45 edge trim + 3 captions relocated)."
measure: "79 viol / 8 unc  ->  0 viol / 0 unc. All classes cleared: 8 GND unconnected, 23 starved_thermal, 48 silk, 4 items_not_allowed (U6), 2 track_width, 1 hole_to_hole, 2 clearance. Board↔netlist parity holds by construction (generate_board asserts pad nets from the gated netlist)."
state:   done
next:    "Routing gate reached. Handing to coordinator for independent verify (fresh DRC + pcb_toolkit) + commit (board + config; skills already committed at 60f0a13) -> red-team -> seal. Config all projects/crow-recorder-central-v2/-scoped; NO skills/ edits."
op_pid:
updated: 2026-07-23T15:30:00
