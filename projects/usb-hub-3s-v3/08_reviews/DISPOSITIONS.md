# DISPOSITIONS — usb-hub-3s-v3 review findings ledger

The living decision register across ALL reviews (08_reviews contract). Started
2026-07-23 with the post-seal external v1.3 review; findings from the earlier
red-team/fix-confirmation reviews were dispositioned inside their release
verifications (v1.0-v1.3 `verification/` + SUPERSEDED.md chains) before this
ledger existed and are not retro-transcribed — their reviews remain the
evidence of record.

Severity vocabulary: P0/P1/P2 (SKILL.md stage 7). Every finding is a CLAIM,
independently re-verified against artifacts before disposition.

## 2026-07-23_v1.3_external-user_full.md (received post-seal; examined pre-seal state)

| id | review file | finding (one line) | severity | verification | disposition |
|---|---|---|---|---|---|
| EXT13-1 | 2026-07-23_v1.3_external-user_full.md | §1: v1.3 is a staged, blocked release — gate iii + seal pending | P0 (at review time) | confirmed for the PRE-SEAL state the reviewer saw; overtaken when received — seal completed same day (source S=01983b0, seal=d137e00; fresh lens VERDICT ORDER archived 2026-07-23_v1.3_redteam_fresh-lens.md) | fixed — overtaken by seal d137e00; the demanded gate-iii fresh red-team + 2-commit seal are exactly what completed |
| EXT13-2 | 2026-07-23_v1.3_external-user_full.md | §2: R30 still C2933195 = 3.09 kΩ, not 100 kΩ | P0 (at review time) | confirmed for the pre-seal state; overtaken — sealed v1.3 BOM has R30 on C25803 (100 k, merged into the R1/R8/R17 row), sealed verification/bom_source_check.txt PASS incl. the semantic value-vs-ledger leg; forbidden-code sweep in the fresh lens found no C2933195 anywhere | fixed — v1.3 gate ii-b commit 01983b0 (pre-seal); reviewer's recommended part C25803 is the one shipped |
| EXT13-3 | 2026-07-23_v1.3_external-user_full.md | §3: divider worst-case math omits R13/R4 ±1% (C5126242 = FRC0603F1211TS, ledger row 150); true 5VC range ≈5.227-5.479 V, not 5.27-5.43 V | P1 | confirmed — ledger decode FRC0603F**1211**TS = 1.21 k ±1% ("F" series = 1%); recomputed: 5VC min 5.227 V / max 5.479 V (R12 ±0.1%, R13 ±1%, Vref ±1.5%); low-corner headroom 597 mV vs 440 mV IR budget = still PASS with 157 mV slack; USB-A top corner 5.273 V slightly above the 5.25 V ceiling (R3 C728591 is 0.1%) | fixed — v1.4-2026-07-23 ORDER_README ships the tolerance-inclusive worst-case table + no-load ceiling criteria; hardware option (0.1% R13/R4) recorded as a next-rev choice, not required (margins still pass) |
| EXT13-4 | 2026-07-23_v1.3_external-user_full.md | §4: README SW1 fallback-header polarity REVERSED ("COM-T1 shunted = ON") | P1 | confirmed — tsx SW1 `connections={{ pin1: "net.GND", pin2: "net.ENKILL" }}` (pin1=T1, pin2=COM); power_tree off_control: grounding ENKILL turns BOTH bucks off + opens Q6. COM-T1 shunted therefore = OFF | fixed — v1.4-2026-07-23 ORDER_README: "COM-T1 shunted = OFF; shunt removed = ON" + continuity-verify step in the bench gate |
| EXT13-5 | 2026-07-23_v1.3_external-user_full.md | §4b: README calls F1 "KH-AF90DIP-112" (the USB-A connector family) | P2 | confirmed — sealed fab/bom.csv row 38: `C5249699,F1,Fuseholder_Blade_Mini_Keystone_3568`; KH-AF90DIP-112 is the USB-A receptacle footprint family | fixed — v1.4-2026-07-23 ORDER_README names F1 = Keystone 3568 mini-blade holder, C5249699 |
| EXT13-6 | 2026-07-23_v1.3_external-user_full.md | §5: F1 + SW1 on fab/bom.csv but absent from cpl.csv → JLC upload shows 2 unmatched designators | P2 | confirmed — bom.csv rows 32 (SW1 C2939728) + 38 (F1 C5249699); neither refdes in cpl.csv (intentional hand-solder, FP_EXCLUDE_FROM_POS_FILES) | fixed — v1.4-2026-07-23 ORDER_README packaging note: mark F1/SW1 DNP/not-assembled in the JLC order review; purchasing list incl. the 10 A MINI blade fuse element |
| EXT13-7 | 2026-07-23_v1.3_external-user_full.md | §6: fail-high protection is best-effort, not deterministic; acceptable for supervised prototype | P2 | confirmed and already recorded — this IS the documented OV posture (Option 2, BRIEF A3/D3, ADR-0002; escalation boundary verbatim in ORDER_README/MANIFEST) | recorded — consistent with the user-recorded decision; reviewer concurs with the acceptance; text kept VERBATIM in v1.4 |
| EXT13-8 | 2026-07-23_v1.3_external-user_full.md | §7: tighten bench pass criteria (VBUSC@5A ≥5.00 V, cable-end ≥4.80-4.85 V hot, no-load ceiling, load-release overshoot, get_throttled) | P1 | confirmed reasonable — criteria strictly tighten the existing Q1-Q5 gate; no conflict with recorded decisions | fixed — v1.4-2026-07-23 ORDER_README adopts the tightened Q1-Q5 criteria + adds R30 visual/ohmmeter pre-power check, no-load ≤5.45 V firm ceiling, 5 A→0 A overshoot capture, SW1 continuity logic check, vcgencmd get_throttled monitoring |
