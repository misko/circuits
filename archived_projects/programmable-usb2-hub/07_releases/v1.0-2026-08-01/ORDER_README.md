# Order README — programmable USB 2.0 hub v1.0

> MUTABLE PRE-SEAL STAGING. Do not upload or order this directory until the
> independent reviews pass, the source commit is made, and MANIFEST.txt is
> stamped with `git_dirty: false` and complete hashes.

DESIGN: PRE-SEAL REVIEWS IN PROGRESS

SOURCING: PLANNED-1 (C5248536; measured 2026-08-01)

order_verdict: BLOCKED-SOURCING. Machine design gates, P-PINMAP, pin review,
and A-RENDER are green. The archive remains mutable until all independent
render/topology/layout and USB-high-speed review phases are archived and the
two-commit seal is stamped. U4 consignment remains the measured order blocker.

## JLCPCB order settings

- Four copper layers; board outline 130 x 90 mm; finished thickness 1.6 mm.
- Select JLCPCB stackup `JLC04161H-7628`, ENIG, and controlled impedance.
  The USB 2.0 pairs are 0.25 mm trace / 0.15 mm gap on L1 over the solid L2
  reference and target 90 ohm differential, acceptance 90 ohm +/-15%.
  Do not accept a stackup, width, gap, or reference-layer substitution.
- Quantity: 5.
- Top-side SMT assembly plus JLC post-through-hole assembly for J1, J2, J7.
- PCB upload: `fab/programmable_usb2_hub_gerbers.zip`.
- Assembly uploads: `fab/bom.csv` and `fab/cpl.csv`.

## Population and post-assembly work

- U4 is the exact AP63203QWU-7, consigned from Mouser or DigiKey; no substitution is authorized.
- F1 is not placed by JLC. Install two exact Keystone 3568 clips and the specified MINI blade fuse after PCBA.
- J3-J6 are exact GCT USB1130-15-A receptacles installed after PCBA; no catalog substitution is authorized.

## Mandatory before payment

1. Upload the BOM and compare JLC's resolved table to `verification/bom_echo_gate.txt`; any redirected code is a substitution finding.
2. Inspect all 15 exact codes in `verification/rotation_human_gate.txt` in JLC's placement preview, including pad-1/polarity.
3. Confirm J1, J2, and J7 remain in JLC post-through-hole assembly.
4. Confirm U4 consignment acceptance and moisture/ESD handling.
5. Re-run the JLC stock check and Q-2SOURCE supplier audit on the payment date.

## First-power ritual

Current-limit the 24 V input, install no downstream USB loads, and verify the
protected input, both 5 V buck rails, 3.3 V logic rail, and each port's
disabled-state VBUS before enabling ports one at a time. Stop on unexpected
current, heating, or rail voltage.
