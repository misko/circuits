# Physical-fit observation — 2026-08-26

Status: **observed predecessor failure; revised CAD not physically retested**.

These four user-supplied photographs are visual evidence only. They provide
relative contact/clearance observations; no pixel-derived dimension is used as
CAD authority.

| Attachment | SHA-256 | Observation |
|---|---|---|
| `IMG_6709.HEIC` | `d8095d9db80cb8c68ac9de03dda667994d720c6f3e830fff8486b24bbe5e10b1` | The right-angle antenna elbow/hinge has visible lateral freedom in the predecessor adapter. |
| `IMG_6710.HEIC` | `2ba47c6a031d218e33a389d8ca5335f2563752e924da3852a85e7cb5be011566` | The PCB and USB-C edge sit high while the predecessor lower perimeter approaches the SMA bodies. |
| `IMG_6711.HEIC` | `447975bdfa18c88abc087952e4f1d333a255a1f946dc93b37b0bb36d446902c2` | The predecessor wall-to-SMA relationship is consistent with connector contact before the PCB reaches all intended supports. |
| `IMG_6712.HEIC` | `9be8e791045dfeb9103424712a78fcd5e2c19e4f534ac92435cfcd29da0139b9` | The narrow rectangular hinge/tongue sits in a visibly wider circular/rectangular opening; a localized open-bottom key is appropriate. |

## Design response

- Remove the base perimeter wall and alignment lip completely. Retain a flat
  printable foundation, four PCB support/insert pillars at H1–H4, and four
  independent case-closure posts outside the PCB corners.
- The PCB must bear only on the four intended supports and be retained by its
  own four M3 screws. SMA/USB-C bodies and case screws are not PCB supports.
- Preserve the adapter's 10.8 mm rigid full-part loading path, upright opening,
  and south arch so the already-wired L antenna still enters from below without
  threading its cable.
- Add only a short open-bottom compliant key near the elbow/tongue. Its 9.75 mm
  grip gap, 11.75 mm open mouth, and 1.0 mm lead-in come from the exact bound
  holder STL's compliant void; its four-millimetre axial length is a candidate.
- Print the 9.50/9.75/10.00/10.25 mm channel-gap coupon before selecting final
  production clearance.

## Required retest

1. Print the revised base and confirm the bare PCB seats simultaneously on all
   four supports with daylight around every SMA/USB-C body.
2. Install only the four PCB screws, remove lid/case screws, and confirm the PCB
   cannot rock or move.
3. Mate every connector while the PCB remains supported only by its pillars.
4. Print the channel coupon and adapter; verify bottom insertion/removal of the
   complete prewired antenna, snug elbow/tongue retention, no cable pinching,
   and no rattle after the adapter is screwed down.

Until those tests are recorded, both PCB seating and antenna retention remain
`INCOMPLETE` regardless of collision/render results.
