# 02_parts/ status — 2026-07-16 (crowsync-recorder)

27 MPNs. Pin maps read from datasheet FIGURES on 2026-07-16 (each
`verified:` names figure + page). USB4105-GF-A + KT-0805G facts carry
usb-power-3s provenance (verified there 2026-07); USB4105 drawing PDF
fetched and committed here.

**Known deviations from 02_parts/contracts.md:**
- GZ1608D601TF (ferrite): LCSC datasheet viewer blocks non-browser fetch;
  specs live-verified via JLC attributes. FETCH BEFORE BRING-UP if the
  bead's Z-profile ever matters beyond 600R@100MHz.
- KT-0805G (LED): series-sheet part, PDF not committed (indicator only;
  polarity fact pad1=cathode carried from usb-power-3s footprint check).
- R/C passives: series-sheet parts, PDFs not committed; facts are
  live-verified JLC attributes (06_build/cache/spec_confirm_2026-07-16.txt
  — regenerable, cached copy in verification/ of the release).
- SM03B-GHS-TB / SM02B-GHS-TB: directory names omit the (LF)(SN) suffix
  (filesystem-hostile chars); sourcing.note carries the full orderable string.
