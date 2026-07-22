# crowsync-recorder

USB-powered stereo acoustic recorder for CrowSync (TDOA crow localization):
PCM2900CDBR USB audio codec — CH1 = outdoor electret mic via TLV9062
preamp, CH2 = GNSS PPS timing waveform. 65x42mm, 4-layer, all top-side SMT,
JLC-assembled including connectors.

- Status: **released** — current release: `07_releases/v1.0-2026-07-16/`
- Rebuild + gate: `bash 03_src/rebuild_all.sh` (must end `violations: 0` /
  `unconnected: 0`); re-route from scratch: `03_src/route_prep.py` +
  `03_src/route_waves.sh` (needs KiCadRoutingTools).
- Docs: `01_docs/` (BRIEF, ARCHITECTURE, DETAIL_DESIGN, decisions/);
  parts + datasheets: `02_parts/`.
- Mic gain variants (decisions/0003): ship R11 = 3k01 (-24dB capsule);
  -44dB capsule build swaps R11 to 39k.
