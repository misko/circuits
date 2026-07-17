# changelog: xt60-usb-supply

(newest first; one entry per revision; `Released:` links a fab order)

## v1.0 — 2026-07-16  [tag: v1.0-xt60usb]
- Review-triage round: USB-C BC1.2 DCP short (ADR 0008), U3 VBUS rescue
  via, silk refdes de-collide, H-refs hidden.
- Verification complete: stock 20/20 coded lines, digital twin 0
  unadjudicated criticals (Q1 MODEL-REG adjudicated with pixel
  evidence), fresh-context pin review ALL PASS, render review
  dispositioned.
Released: 07_releases/v1.0-2026-07-16

## v1.0-rc — 2026-07-16  [tag: v1.0-rc-xt60usb]
- First fully placed + routed revision: DRC gate green (0 violations /
  0 unconnected / 0 schematic parity), audit + proximity + polarity PASS.
- Two SY8368QNC bucks (ILMT low both rails per ADR 0007), designed-copper
  corridors for the QFN signal row (EN/ILMT/VCC/FB/BST), KRT for port
  signals, In2 power patches with via stitching.
Released: no
