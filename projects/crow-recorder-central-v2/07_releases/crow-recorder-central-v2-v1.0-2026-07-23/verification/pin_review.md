# Pin review — v1.0-2026-07-23 (fix-pass scoping)

Per canon "Verification scoping" (SKILL.md stage 7), this fix-pass release
carries ONE integrated zero-context lens instead of the full multi-lens
battery; its verdict covers the pin dimension. See fresh_lens.md (this dir).
Machine pin evidence independent of that lens:
- audit_board.py: 21 pad-1/pin-net polarity facts (J1 center+, D1 band, Q1
  D->S GUARD, Q2 low-side, U7/U8 VIN/GND/SW, U9/U10 LDO pins) — PASS, and
  red-tested (a swapped D1 fact trips FAIL).
- check_port_nets.py: all 8 RJ45 ports pin-for-pin per the brief (115/115
  label survival) — PASS.
- S-VER: 17/17 part.yaml pinouts carry datasheet figure/page citations
  (policy_audit).
