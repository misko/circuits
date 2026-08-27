# USB-controlled debug hub 2A enclosure redesign commission

This is the canonical, resumable mechanical commission for the current PCB.
It is not yet an enclosure design or release. No printable STL is committed,
and no generated candidate is hidden under `08_reviews/`.

## Selected PCB parent

The intended parent is immutable PCB release `v0.1.2-2026-08-26`:

| Subject | Path | Bytes | SHA-256 |
|---|---|---:|---|
| release manifest | `07_releases/v0.1.2-2026-08-26/MANIFEST.txt` | 47,396 | `3757a209789842583c90e3e2e8c6b7c2c9668b72eb41d68e8aec230f6087dc3e` |
| PCB | `07_releases/v0.1.2-2026-08-26/source/usb_controlled_debug_hub_2a.kicad_pcb` | 3,526,418 | `de47f1053e9145b74cf75ab677caab2d4a287eb207acc233db2b316fb52c2a99` |

The release does not contain a complete whole-board mechanical STEP. Until a
reproducible assembly STEP and exact interface are generated and inspected,
`enclosure.yaml` and `enclosure-v2.yaml` intentionally do not exist and the
candidate cannot claim `CAD_READY`.

## Rejected prototype boundary

An earlier unmerged prototype used the four PCB mounting axes for both PCB
retention and case closure and stored a self-contained candidate beneath
`08_reviews/`. That topology is not migrated:

- removing the lid would also release the PCB;
- it was bound to an obsolete live-board snapshot rather than this sealed
  parent; and
- review storage obscured the distinction between source, disposable build
  output, immutable release payload, and physical evidence.

Useful requirements are retained here: four north USB-A openings, west USB-C
power and data openings, simultaneous six-cable mating, support-conscious FDM
orientation, an insert coupon, and a high-risk closed-case load test.

## Required redesign

The next CAD candidate must provide:

1. four PCB screws that retain the board to the base with the lid removed;
2. a distinct set of case screws/posts whose axes do not intersect the PCB;
3. a straight complete-PCB insertion/removal path and a straight complete-lid
   insertion/removal path;
4. close-in connector openings that do not use the connector bodies as board
   supports or insertion stops;
5. explicit plug envelopes for both USB-C and all four USB-A cables mated at
   once; and
6. typed coupon, drop-in, board-support, lid-off-retention,
   closure-independence, simultaneous-interface, and thermal-soak tests.

If separate perimeter posts force excessive connector recess, use an authored
wall-lid or pillar topology rather than weakening fastener independence.

## Resume

From repository root, first validate this commission:

```sh
project=projects/usb-controlled-debug-hub-2a-v1
build="$project/06_build/mechanical/current-redesign"

/usr/bin/python3 skills/pcb-enclosure/scripts/enclosure_v2.py \
  validate-intent "$project/03_src/mechanical/mechanical-intent-v2.yaml" \
  --output "$build/mechanical-intent-validation-v2.json"
```

Then generate a current assembly STEP and interface below `$build`, inspect
complete fitted-reference coverage, choose the independent-post topology, and
only then author exact v1/v2 configurations. A governing `FAIL` stays mutable
source work; a release is created only under `07_enclosure_releases/`.
