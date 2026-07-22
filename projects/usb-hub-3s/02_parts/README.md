# 02_parts — status + deviations register

All active/multi-pin parts carry full part.yaml + committed datasheet PDF.

## Deviations from the contract (each with why + closure condition)

1. **Series-sheet 2-pad commodity parts WITHOUT individual PDFs** (allowed by
   contract): SMBJ15A (C83846), SMAJ30A (C148230), SMAJ24A (C148222),
   BZT52C12 (C173429), SS210 (C14996), 1N4148WS (C2128), LESD5D5.0CT1G
   (C5246195), PMR100HZPFU5L00 (C308572), 25121WF100MT4E (C127692),
   MA25V100M6x6 (C46550465), plus generic 0603/0805/1210/1812 R/C.
   WHY: single-value picks from series datasheets; identity + polarity facts
   live in the BOM comments + floorplan pad_net asserts.
   CLOSURE: part.yaml stubs for every coded BOM line land at the bom_seed
   stage (every BOM line maps or bom_seed FAILS); polarized 2-pad parts
   (TVS/diodes/zener/schottky/polymer) get pad-1-cathode/positive asserts in
   the floorplan before routing.
2. **LM5116MHX/NOPB directory named LM5116MHX-NOPB** — '/' not usable in a
   path; the yaml carries the exact orderable MPN.
3. **TYPE-C-31-M-12A datasheet is LCSC's 1-page drawing** — the full HRO
   series sheet is not publicly hosted; land pattern authority = KiCad std
   footprint (proven designed-in per ledger) + jlc_twin PAD-GEOM gate at
   verification.
4. **Hand-solder uncoded lines** (not in JLC assembly catalog): F1 Keystone
   3568 clips (LCSC C5249699 is the SINGLE clip - order 2/board) + 20A MINI
   blade fuse. Listed in ORDER_README hand-solder list. J1 XT60PW-M (C98732)
   and J2-J4 (C503996) are coded THT lines (JLC through-hole assembly or
   hand-solder).
5. **1001-011-01101 REMOVED at verification** (2026-07-21): the fresh-context
   pin review read its drawing title - "USB 4P AM SMT" is a USB-A MALE PLUG
   rated 1.5A, not a receptacle. Parts stage had it recorded as a receptacle;
   every downstream artifact was consistently wrong together. Replaced by
   Kinghelm KH-AF90DIP-112 (female, THT, vendored footprint from the vendor
   drawing). ADR 0006.
6. **TPS2513 -> TPS2513ADBVR at verification** (2026-07-21): pin review
   caught the non-A variant claiming the A-only 2.7/2.7V Apple 2.4A divider.
   Promoted the recorded alternate C473910 to primary; pin map identical.
