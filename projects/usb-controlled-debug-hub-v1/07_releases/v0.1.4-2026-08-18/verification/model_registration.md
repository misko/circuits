# Project native model physical registration

board_sha256: c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68
a-render_verdict: PASS
registration_kind: P-MODEL-REG
config_sha256: 31755338cd2217d0a1510cc22cb7450099da19ddc926b74657ae3ad9775d9f46
stage_receipt: 06_build/release_staging/v0.1.2-2026-08-17/verification/model_registration.stage.json
accepted_bundle: 06_build/release_staging/v0.1.2-2026-08-17/verification/model_registration_bundle/bundle.json

This aggregate is independent physical-registration evidence. Each group uses an origin-centred coupon and compares native-model pixels with F.Fab, F.CrtYd, and each group's declared drilled-centre or all-pad-centre datum. Catalog-twin renderer fidelity is a separate gate.

| group | refs | tuple cache key | group report | result |
|---|---|---|---|---|
| usb_a_kh_af90dip_112 | J_PORT1,J_PORT2,J_PORT3,J_PORT4 | `bfcd193267ac3f4e5bdb1c65784ad1c401ec5e400c72de9c2c6babde13c124fb` | `06_build/pre_route/native_registration/usb_a_kh_af90dip_112/native_model_registration.md` | CACHE-HIT |
| usb_b_te_292304_1 | J_UP | `9d8399c2c1068ab54783be9f30bb90172475c386b6b554101533528b916d25af` | `06_build/pre_route/native_registration/usb_b_te_292304_1/native_model_registration.md` | CACHE-HIT |
| power_terminal_phoenix_1935161 | J_PWR | `8c9cd286cdf458c1f8cc19b426a86d5c39ca342911256cbc8871a813756ad4a5` | `06_build/pre_route/native_registration/power_terminal_phoenix_1935161/native_model_registration.md` | CACHE-HIT |
| aggregate_efuse_tps259474lrpwr | U_AGG | `0cdf1de996546a677443a9567c5f47d9829de3fcc554c236de74d0dbf15cf9fd` | `06_build/pre_route/native_registration/aggregate_efuse_tps259474lrpwr/native_model_registration.md` | CACHE-HIT |
