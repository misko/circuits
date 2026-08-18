# v0.1.3 sourcing-supersede evidence

This quick release changes supplier identities only. Its parent design release
is `v0.1.2-2026-08-17`; the exact PCB SHA-256 remains
`c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68`.

The generated BOM has 33 coded rows and the CPL has 138 placements. All CPL
rotations have measured authority. Exact-code measurements made 2026-08-18:

- C2150199 / TPS2557QDRBRQ1: offset 0 degrees, single-channel; JLC pin-1
  preview required for U_PWR1, U_PWR2, U_PWR3, U_PWR4 and U_PWR_CTRL.
- C54411084 / 74LVC08APW: offset 270 degrees, single-channel; JLC pin-1
  preview required for U_AND_DATA and U_AND_PWR.

The EasyEDA/JLC CAD API returned and registered eight of the ten replacement
codes. It repeatedly did not return C843837 or C2483395. These are
non-polarized 0402 resistors and do not alter board geometry, but this is an
order-time evidence gap: confirm both resolve to 0402/1005 metric lands in the
JLC uploader. Do not order on a redirect or package mismatch.

No firmware was generated or included.
