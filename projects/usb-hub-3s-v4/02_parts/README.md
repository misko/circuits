# Stage 1 evidence exceptions

Every selected complex or polarity-sensitive part has an immutable fact dossier.
Vendor PDFs are pinned beside the dossier where the primary server returned a
real PDF. Two deliberate exceptions remain visible rather than being disguised:

- Littelfuse's SMBJ series URL returned an access-denied HTML document on
  2026-08-10. That invalid payload was deleted. The dossier records the official
  URL and the independently read exact SMBJ15A row, but leaves `sha256: null`.
- Phoenix Contact's dynamic PDF endpoint rejected the automated fetch for
  1715022 on 2026-08-10. Its exact manufacturer product record was independently
  read for the 5mm pitch, 1.3mm hole, current and mechanical-use requirements;
  `sha256` remains null. The exact custom footprint still requires the normal
  manufacturer-source and order-upload geometry review before placement freezes.

Stock counts and price are intentionally not copied into dossiers because they
change. The dated live catalog response and the final 16/16 candidate report are in
`../06_build/cache/`; the JLC order uploader remains the final assembly-allocation
authority.
