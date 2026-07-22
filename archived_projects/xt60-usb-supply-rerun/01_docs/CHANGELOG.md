# changelog: xt60-usb-supply

## v1.0.2 — 2026-07-16
Released: 07_releases/v1.0.2-2026-07-16/
- Verification refresh: twin v2 renders (Q1 seated via evidence-backed
  model_dy nudge), XT60 body mounted. Fab byte-identical to v1.0.
- Retro-note (2026-07-17): its MANIFEST git_sha reads "HEAD@release"
  rather than an exact hash — release dirs are immutable, so this is
  waived with evidence in 03_src/rules/policy_waivers.yaml; the exact
  content commit is 41ae1a6 (snapshot sync).

## v1.0.1 — 2026-07-16
Released: 07_releases/v1.0.1-2026-07-16/ (SUPERSEDED — bad Q1 render)
- Verification refresh whose Q1 nudge was applied in the wrong frame;
  superseded by v1.0.2. Fab byte-identical to v1.0.


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
