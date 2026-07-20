# 02_parts/ status — 2026-07-16

36 MPNs. Pin maps / polarity facts carry provenance from the SPF power
board (verified against datasheets there, 2026-07) — see each `verified:`.

Datasheet PDFs committed: LM5145RGYR, TPS2557DRBR, CSD18543Q3A (TI direct).
**Known deviations from 02_parts/contracts.md** (recorded per contract):
- LM74800QDRRRQ1: TI CDN refused non-browser fetch; facts verified on SPF.
  FETCH BEFORE BRING-UP.
- Connectors/passives/diodes: series-sheet parts; url recorded, PDF not
  committed. Facts are live-verified JLC attributes (2026-07-14).
- 3 new resistor values (432R, 24k3, 52k3): LCSC codes TBD at stock check.
