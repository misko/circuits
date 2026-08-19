# Project native model physical registration

board_sha256: a0acddd9b0b4e1888583ffacad43f2c2446e76cb040ebc64844cd25779a73987
a-render_verdict: PASS
registration_kind: P-MODEL-REG
config_sha256: f9ee0265f0200094e098752e1d5a3c65dcfb0f837a7f39e7ff7a81e1194bdc2a
stage_receipt: 06_build/release_staging/v0.1.1-2026-08-18/verification/model_registration.stage.json
accepted_bundle: 06_build/release_staging/v0.1.1-2026-08-18/verification/model_registration_bundle/bundle.json

This aggregate is independent physical-registration evidence. Each group uses an origin-centred coupon and compares native-model pixels with F.Fab, F.CrtYd, and each group's declared drilled-centre or all-pad-centre datum. Catalog-twin renderer fidelity is a separate gate.

| group | refs | tuple cache key | group report | result |
|---|---|---|---|---|
| usb_a_kh_af90dip_112 | J_PORT1,J_PORT2,J_PORT3,J_PORT4 | `bfcd193267ac3f4e5bdb1c65784ad1c401ec5e400c72de9c2c6babde13c124fb` | `06_build/pre_route/native_registration/usb_a_kh_af90dip_112/native_model_registration.md` | CACHE-HIT |
| usb_c_hro_type_c_31_m_12 | J_DATA,J_POWER | `82531bc124ebfe391b424efdacd95a81c315282dbb432dffcf4069547d56733f` | `06_build/pre_route/native_registration/usb_c_hro_type_c_31_m_12/native_model_registration.md` | CACHE-HIT |
| aggregate_efuse_tps259474lrpwr | U_AGG | `0cdf1de996546a677443a9567c5f47d9829de3fcc554c236de74d0dbf15cf9fd` | `06_build/pre_route/native_registration/aggregate_efuse_tps259474lrpwr/native_model_registration.md` | CACHE-HIT |
