# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

<!-- reader parses from here down -->
stage:   sealed
step:    "v1.1 SEALED: 07_releases/crow-recorder-central-v2-v1.1-2026-07-24 (seal d9d5ae1 on source S b08f182). Supersedes v1.0 (external DO-NOT-ORDER + LV-strap P0). Fresh lens ORDER on the final bytes."
measure: "DRC 0/0/0 standalone; ERC 0/1201; parity 0; port nets 115/115+8/8; policy 0 FAIL (M-REL+R-LEN PASS); twin 0 (160/359); MANIFEST 47/47 both directions; freshness PASS; pin+render PASS; lens ORDER"
state:   done
next:    "Order per ORDER_README (JLC06161H-3313 stackup + ADVANCED small-via + FILLED+CAPPED vias REQUIRED; sec 1a U1 fab note; sec 3a assembly closure; sec 4a first-article gates incl. USB-HS matrix + U1 EP X-ray). v-next: ADR-0007 OVP/F_BEEP + D_USB in-path."
op_pid:
updated: 2026-07-24T11:03:34
