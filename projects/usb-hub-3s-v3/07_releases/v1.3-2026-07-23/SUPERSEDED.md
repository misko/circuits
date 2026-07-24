# SUPERSEDED — by v1.4-2026-07-23 (docs-only supersede)

**Do not order from this directory. Order from `../v1.4-2026-07-23/`.**

Reason: a post-seal user-supplied external review
(`08_reviews/2026-07-23_v1.3_external-user_full.md`, dispositions EXT13-1..8)
found three defects LIVE in this release's DOCUMENTATION — the board itself is
electrically correct and is shipped UNCHANGED by v1.4:

1. **ORDER_README section 2 misdocuments the SW1 fallback-header shunt
   polarity — REVERSED.** It says "COM-T1 shunted = ON; shunt removed = OFF".
   The source wires SW1 pin1=T1→GND, pin2=COM→ENKILL, and grounding ENKILL
   shuts BOTH bucks down and opens Q6: **COM-T1 shunted = OFF; shunt removed
   = ON.** Following this README during commissioning inverts the master-off
   logic.
2. **ORDER_README section 2 misnames the F1 fuse holder** as "KH-AF90DIP-112"
   (that is the USB-A connector family). F1 = **Keystone 3568 MINI-blade
   holder, C5249699** (fab/bom.csv row 38).
3. **The margin analysis omits the divider-bottom tolerance.** R13/R4 =
   C5126242 = FRC0603F1211TS **±1 %**; the documented 5VC range (5.27-5.43 V)
   applied only Vref ±1.5 %. Tolerance-inclusive: **5.227-5.479 V** (headroom
   597 mV vs the 440 mV IR budget — conclusion unchanged, still PASS).

**Board copper, BOM, CPL, gerbers, source and PDFs are byte-identical between
this release and v1.4** (declared and sha256-verified in v1.4's MANIFEST).
Everything else in this directory remains valid sealed evidence; only the
ORDER_README statements above are corrected — in v1.4, never here.
