# Exact-part evidence deviations

The selected BOM has one directory per exact orderable MPN. Manufacturer PDFs
or explicitly qualified exact-document captures are committed beside the
extracted facts except for the remaining explicit case below.

- `901-143-6RFX`: the current exact Amphenol product page identifies customer
  drawing `SMA6252A2-3GT50G-50`; the official asset endpoint returned HTTP 403
  to the local client. An exact Rev-C byte copy from a distributor mirror is
  retained with its SHA-256, and its visible part number, drawing number and
  revision match the official link identity. Amphenol PCN-031726 is also
  retained; it lists this MPN and states that the 2026 CN-to-VN production
  transfer changes no form, fit, function, specification, material or process.
  This closes drawing availability for footprint authoring without claiming
  that the mirror bytes came from Amphenol's server.
- `STM32C011F4P6`: the committed ST document is DS13866 Rev 4 obtained from the
  JLC listing because ST's Rev 5 download endpoint rejected the local client.
  Pinout, supply, HSI48 error, BOR and decoupling facts used here were
  independently cross-checked against ST's current DS13866 Rev 5 online on
  2026-08-13. Replace the local copy with Rev 5 before release; no relevant
  TSSOP-20 pin or package change was observed.

The remaining ST deviation is a visible blocker at design freeze. It does not
authorize release from weaker evidence.
