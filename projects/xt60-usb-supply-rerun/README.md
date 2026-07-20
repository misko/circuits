# xt60-usb-supply

3S LiPo (XT60, 9.0-12.6 V) to four USB charge ports: 3x USB-A (2.5 A
each, BC1.2 DCP) + 1x USB-C (6 A capable, Rp 3 A advertisement + DCP).
Two SY8368QNC synchronous 5 V bucks (8 A rail for the USB-A trio, 6 A
rail for USB-C), fuse + P-FET reverse-polarity + TVS input protection.
92x62 mm, 4-layer JLCPCB standard.

- **Status**: delivered — fab package cut, order not yet placed.
- **Current release**: `07_releases/v1.0.2-2026-07-16/` (fab byte-identical
  to v1.0; current verification renders live here) (gerbers, BOM/CPL,
  PDFs, verification evidence, MANIFEST; see its ORDER_README for the
  order + bring-up checklist).

## How to build

```bash
bash 03_src/rebuild_all.sh     # regenerate everything + gates; must end
                               #   violations: 0 {} / unconnected: 0
bash 03_src/route_board.sh     # only to RE-ROUTE from scratch (KRT)
bash 03_src/export_pdfs.sh     # PDFs + PNG verification renders
```

Contracts: `contracts.md` at root and per folder. Commission record:
`01_docs/BRIEF.md`. Design rationale: `01_docs/decisions/` (ADRs
0001-0008). Resume point: `PROGRESS.md`.
