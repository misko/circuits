# Source-closure verification — v0.1.2

status: PASS
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
source_commit: 87eaa91fd36cb939383e806a3e5b96aae8615dbf
predecessor: v0.1.1-2026-08-21
board_sha256: de47f1053e9145b74cf75ab677caab2d4a287eb207acc233db2b316fb52c2a99

This ordinary full successor closes the active project's last filesystem
dependency on `usb-controlled-debug-hub-v2` before that project is archived.
It does not claim an electrical, placement, routing, fabrication, or order
change.

## Exact bounded source delta

The predecessor and this release differ under `source/` at exactly five file
paths:

- `source/project/03_src/floorplan.yaml`: the
  `usb_controlled_debug_hub` library path changes from the sibling-project
  path to `03_src/lib/usb_controlled_debug_hub.pretty`. SHA-256 changes from
  `538d6bb182ab532f15db9fca98a489f4d20f87a0cbc7300cbd00a61cb15c05e2`
  to `3a6b4410f6a50dbece3b06b49d0c272407663359a4cd059c9971229045631c03`.
- `source/project/04_kicad/fp-lib-table`: the same library URI changes from
  an absolute workstation path to
  `${KIPRJMOD}/../03_src/lib/usb_controlled_debug_hub.pretty`. SHA-256 changes
  from `80247b394e4aa64b0dc16e5eb591675a26eaa08959d73c21bb28b268f0830dfc`
  to `1a869fc22af2cc36ba8b16934d922f21d81b67ac371dd9073cc2d348b5cb558c`.
- Three footprint definitions are added below
  `source/project/03_src/lib/usb_controlled_debug_hub.pretty/`:
  `Diodes_SOT23_2N7002K.kicad_mod` at
  `02a91b20fee34df18fa243c870fce05d2aaa6e9530fa43e3048a7c92a56652ea`,
  `Panasonic_C6_6.3x5.9.kicad_mod` at
  `bfd635a56859a03a7a8d8f81af4465407a3ac1f29077eb3d8c4ccdc94411b19f`,
  and `Sunlord_SWPA4030S.kicad_mod` at
  `95ff8d4363c13a9a075fa6e3bfb1053ed5bbc1e8fc95ec934305c38cb2447196`.

Each added footprint is byte-identical to the former provider under
`archived_projects/usb-controlled-debug-hub-v2/03_src/lib/`. The unchanged
board uses exactly these three library members across seven placements
(4 + 2 + 1 respectively); no unused member of the former 14-footprint library
was copied.

## Unchanged manufactured subject

- Live board, predecessor source board, and this release source board are all
  byte-identical at SHA-256
  `de47f1053e9145b74cf75ab677caab2d4a287eb207acc233db2b316fb52c2a99`.
- `fab/` is an exact 20-file identity with the predecessor. The canonical
  path/hash/size census digest is
  `930e94e00029c3f7b854192fcb2e835247c7f19bb2efc212d71503a61edf970e`.
- `pdf/` is an exact 3-file identity with the predecessor. The canonical
  path/hash/size census digest is
  `be0a3a5325217f7294b17ab58e7e58919fe2f7bac0c9b17403a3acbef1fc64c8`.

## Independent reopen checks

- A standalone generator run from this release-local source resolved all
  libraries, placed 183/183 anchored footprints, passed 34/34 source asserts,
  found 0 pad-overlap/short findings, and emitted 12 library bindings. Its
  track-free generated board SHA-256 was
  `341b01ed2135c1d71213128afd344720cfc5433f8cb5a907963a80cf47d7461a`.
- `verification/standalone_archive_drc.json` was generated from the copied
  release board with the copied release-local `fp-lib-table`; it reports
  0 violations, 0 unconnected items, and 0 schematic-parity findings. Its
  SHA-256 before manifest sealing was
  `897c6e61ca269f9b3ff7cdc022bfa9b2658636e03f93570c5951bb745bbb2224`.

This evidence proves source self-containment only. It does not authorize an
order; sourcing and first-article holds remain unchanged.
