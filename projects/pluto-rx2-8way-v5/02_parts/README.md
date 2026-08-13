# Exact-part evidence deviations

The selected BOM has one directory per exact orderable MPN. Manufacturer PDFs
are committed beside the extracted facts except for the two explicit cases
below.

- `901-143-6RFX`: Amphenol's current product page and customer drawing were
  read online on 2026-08-13. The PDF endpoint returned HTTP 403 to unattended
  download, so the dossier records the official URLs, drawing number and
  dimensions without committing a stale third-party mirror. Re-fetch the
  current drawing before authoring or approving the custom footprint.
- `STM32C011F4P6`: the committed ST document is DS13866 Rev 4 obtained from the
  JLC listing because ST's Rev 5 download endpoint rejected the local client.
  Pinout, supply, HSI48 error, BOR and decoupling facts used here were
  independently cross-checked against ST's current DS13866 Rev 5 online on
  2026-08-13. Replace the local copy with Rev 5 before release; no relevant
  TSSOP-20 pin or package change was observed.

These deviations are visible blockers at their affected future gates. They do
not authorize a footprint or release from weaker evidence.
