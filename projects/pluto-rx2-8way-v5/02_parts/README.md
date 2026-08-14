# Exact-part evidence deviations

The selected BOM has one directory per exact orderable MPN. Manufacturer PDFs
or explicitly qualified exact-document captures are committed beside the
extracted facts. The one non-origin byte source is explicit below.

- `901-143-6RFX`: the current exact Amphenol product page identifies customer
  drawing `SMA6252A2-3GT50G-50`; the official asset endpoint returned HTTP 403
  to the local client. An exact Rev-C byte copy from a distributor mirror is
  retained with its SHA-256, and its visible part number, drawing number and
  revision match the official link identity. Amphenol PCN-031726 is also
  retained; it lists this MPN and states that the 2026 CN-to-VN production
  transfer changes no form, fit, function, specification, material or process.
  This closes drawing availability for footprint authoring without claiming
  that the mirror bytes came from Amphenol's server.
- `STM32C011F4P6`: ST's current official DS13866 Rev 5, February 2026, is the
  digest-selected local authority. The earlier file obtained through the JLC
  listing identified itself as Rev 3 despite its legacy `Rev4` filename; it is
  retained as `DS13866-Rev3.pdf` for audit history only. A focused comparison
  found no change to the TSSOP-20 pin sequence, BOR4 thresholds, HSI48 bounds
  or package dimensions consumed by this design.
