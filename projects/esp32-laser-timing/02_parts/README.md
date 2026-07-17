# 02_parts/ status — 2026-07-17 (esp32-laser-timing)

Connector/electromechanical entries added 2026-07-17; facts read from
datasheet DRAWINGS (each `verified:` names the drawing + rev). PDFs
committed for TYPE-C-31-M-12, TS-1187A-B-A-B, KF128L-3.5-2P,
RVT100UF16V67RV0016 and the BOOMELE female socket; all also live in the
global cache `~/.cache/datasheets/<sha256>.pdf`.

**Known deviations from 02_parts/contracts.md:**
- KT-0805G (LED): series-sheet part, PDF not committed (indicator only;
  polarity fact pad1=cathode carried from crowsync-recorder / usb-power-3s
  footprint check, 2026-07-14). Fetch a real KENTO sheet before any use
  where Vf/If margins matter beyond 5mA indicator duty.
- 2.54-1x4P-Female (OLED socket): directory name sanitizes the orderable
  BOOMELE model string `2.54-1*4P` (`*` is filesystem-hostile);
  `sourcing.note` carries the exact string, LCSC C2718488. Committed PDF is
  the 1xN SERIES drawing (2.54-1xNA-H8.5MM), not a 4P-specific sheet.
  Decision: picked C2718488 (THT vertical, 234k stock, Ø1.0 holes matching
  the KiCad PinSocket 1x04 footprint) over SMD/right-angle candidates; any
  user-supplied 2.54mm 1x4 (or cut-down 1xN) female socket is acceptable.
- RVT100UF16V67RV0016: KNSCHA spec sheet carries no revision field;
  `datasheet.revision: undated`, identity pinned by sha256 only.
- KF128L-3.5-2P: footprint deviates from plan — the planned
  `TerminalBlock_Phoenix_MPT-0,5-2-3.5_1x02` does not exist in the KiCad
  std lib (MPT-0,5 series is 2.54mm pitch only); using
  `TerminalBlock_Phoenix_PT-1,5-2-3.5-H_1x02_P3.50mm_Horizontal`
  (3.5mm pitch ✓, 1.2mm drill vs Kefa-recommended 1.3mm — pin diagonal
  0.94mm fits; enlarge to 1.3mm if hand insertion is tight).
- TS-1187A-B-A-B: footprint `esp32_laser_timing:SW_TS-1187A` is to be
  vendored from EasyEDA C318884 — pad table in TS-1187A-B-A-B/notes.md.
  Until vendored, the footprint name is a forward reference.
