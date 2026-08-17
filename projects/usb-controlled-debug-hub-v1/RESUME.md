# USB-controlled debug hub v1 — resume state

Paused: 2026-08-17, while completing the routed Pi-controlled four-port USB
debug hub. Firmware is explicitly out of scope and must not be generated.

## Safe checked-in boundary

The repository has been restored to the last authenticated prefix. It declares:

```yaml
through_wave: usb_upstream
r0_sha256: 897479ffbee4fee7ce2240216bda1ff8947564a6bf848c9c36ca3148ab33e6f1
board_sha256: 4c001688273281e1eb487e237c7862615ff8b637708943456eb03ab54683257f
```

The matching `03_src/route/critical_prefix.kicad_pcb` has that board hash and
passed P-ROUTEBASE, the via-in-pad guard, and authoritative route-prefix DRC.
It is safe to use as the restart boundary.

The later experimental prefix with SHA256
`873001be5f50fe48074a36d6f6b8ce21160f26d7d0267cbcff7bf50897a3fb8a`
is **REJECTED**. When materialized with the authoritative `r0` project/rule
sidecars, the route-prefix gate found 15 USB-class clearance violations. The
isolated scratch DRC had silently used router-clamped 0.15 mm netclass settings,
which was too weak. It is retained only in the local, untracked recovery archive
as `recovery/paused-2026-08-17/rejected_prefix_873001be.kicad_pcb`.

This rejected prefix must not be released or treated as an authenticated
checkpoint. The recovery archive is diagnostic only and is not required to
resume from the checked-in source.

## Last unquestionably accepted boundary

The prior prefix candidate was:

```text
SHA256 4c001688273281e1eb487e237c7862615ff8b637708943456eb03ab54683257f
file   recovery/paused-2026-08-17/prefix_plus_DATA_CMD1.kicad_pcb
through_wave: usb_upstream
```

It passed:

- P-ROUTEBASE against the exact prepared `r0`;
- zero newly created via-in-pad findings;
- authoritative route-prefix physical DRC when replayed by the normal driver.

Starting from that accepted prefix, the `control_commands` wave routed its
remaining eight nets successfully. It reported 25/25 multipoint endpoint pads
connected and zero hard physical DRC findings. The subsequent `control_misc`
wave recovered `USB_UP_VBUS` but left `I2C_SCL` and `I2C_SDA` open.

The old wave-16 board was later overwritten when the rejected prefix was
materialized. `recovery/paused-2026-08-17/r16_no_i2c.kicad_pcb` is a
reconstructed command-wave
candidate made by removing all I2C routed items from the rejected prefix. It
passes P-ROUTEBASE, but should be rechecked with the authoritative `r0`
sidecars before promotion.

## I2C investigation and useful candidates

The two I2C nets are three-terminal nets:

- `I2C_SCL`: `U_CTRL.10` -> `R_I2C_SCL.2` -> `U_EXP.12`
- `I2C_SDA`: `U_CTRL.9` -> `R_I2C_SDA.2` -> `U_EXP.13`

The package endpoints are adjacent, but the real difficulty is the long field
route crossing the already authenticated USB/control field. A uniform 0.15 mm
search can connect both but violates the 0.30 mm USB-class boundary. A uniform
0.30 mm search can connect either line independently but is over-conservative
between ordinary control nets and cannot discover both together.

Useful recovery artifacts currently present:

| Artifact | Status |
| --- | --- |
| `recovery/paused-2026-08-17/r16_no_i2c.kicad_pcb` | Reconstructed wave-16 base with both I2C routes removed; P-ROUTEBASE passes; re-run authoritative physical DRC before use. |
| `recovery/paused-2026-08-17/r16_i2c_scl_c30.kicad_pcb` | SCL alone, 3/3 pads connected at 0.30 mm search clearance. |
| `03_src/route/_candidate_scl.kicad_pcb` | SCL candidate paired with authoritative `r0` sidecars; via-in-pad PASS and full-rule physical DRC PASS (284 deferred partial findings). |
| `recovery/paused-2026-08-17/r16_i2c_sda_c30.kicad_pcb` | SDA alone, 3/3 pads connected at 0.30 mm, but its original `U_CTRL.9` via was in-pad. |
| `03_src/route/_candidate_sda_dogbone.kicad_pcb` | SDA candidate with the `U_CTRL.9` transition moved onto an off-pad dogbone; via-in-pad PASS and authoritative full-rule physical DRC PASS (284 deferred partial findings). |
| `03_src/route/_candidate_i2c_merged.kicad_pcb` | Mechanical merge of the independently clean SCL and SDA routes; rejected due route collisions. Initial result: 19 shorts, one clearance violation, two hole-to-hole violations, concentrated at three shared transition areas. |
| `recovery/paused-2026-08-17/i2c_manual1.kicad_pcb` | Work-in-progress repair of the merged route. It reduced the interaction to six shorts and two clearances. It is still rejected/incomplete. |
| `03_src/route/_candidate_i2c_manual1.kicad_pcb` | Snapshot of the same incomplete manual candidate used for authoritative DRC. |

All `_candidate_*` files are diagnostic artifacts, not release sources.

## Exact remaining interaction in `i2c_manual1`

After staggering the shared transitions, the authoritative report contained
eight hard findings:

- the remaining SDA layer-change cluster around `(95.6, 78.0)` collides with
  SCL and with the P4 USB pair;
- the SDA local dogbone from `U_CTRL.9` toward `(78.0, 79.35)` crosses
  `HUB_SWAP6`;
- no via-in-pad or hole-to-hole findings remained in that snapshot.

The intended next repair was to eliminate the two unnecessary SDA layer
changes around x=95.6/98.325 entirely. Keep that section on B.Cu and join:

```text
(98.425,77.475)
  -> (99.0,78.05)
  -> (99.0,81.175)
  -> (97.55,81.175)
```

This replaces the SDA vias near `(95.6,78.0)` and `(98.325,81.175)` plus the
F.Cu bridge between them. It should clear the SCL transitions and P4 pair, but
must be proven by authoritative DRC rather than assumed.

For the `U_CTRL.9` branch, prefer joining the pull-up branch to SDA's existing
off-pad via at approximately `(76.3,80.65)` on B.Cu, or otherwise route a
reviewed local dogbone that does not cross `HUB_SWAP6` or SCL. Do not restore a
via centered in `U_CTRL.9`.

## Safe restart sequence

1. Do not trust isolated DRC with router-modified sidecars. For every candidate,
   copy `06_build/route/r0.kicad_pro` and `r0.kicad_dru` beside the candidate
   under the candidate's exact basename before running `kicad-cli pcb drc`.
2. Finish the combined I2C route from
   `recovery/paused-2026-08-17/i2c_manual1.kicad_pcb`, or restart from the two
   independently clean strict-clearance candidates.
3. Require all of the following before promotion:

   ```bash
   /usr/bin/python3 skills/kicad-pcb/scripts/promoted_route_check.py \
     --prepared projects/usb-controlled-debug-hub-v1/06_build/route/r0.kicad_pcb \
     --chain CANDIDATE.kicad_pcb

   /usr/bin/python3 skills/kicad-pcb/scripts/via_in_pad_guard.py \
     projects/usb-controlled-debug-hub-v1/recovery/paused-2026-08-17/r16_no_i2c.kicad_pcb \
     CANDIDATE.kicad_pcb \
     --json CANDIDATE_via.json
   ```

   Then run the route driver's `_wave_drc_gate` or `kicad-cli pcb drc` with
   the exact `r0` sidecars. Require zero hard findings. Finally prove both I2C
   nets are 3/3 connected.
4. Only then replace `03_src/route/critical_prefix.kicad_*`, update its SHA256,
   and retain `through_wave: control_commands`.
5. Run the normal route command. The final `control_misc` wave should skip the
   two promoted I2C nets and route only the remaining miscellaneous nets.
6. Continue with import, taps, quick checks, stitch/fill, full electrical/USB/
   manufacturing gates, renders, artifact parity, and first-article release.

## Pipeline lesson captured by this pause

A candidate DRC is only authoritative when it uses the same project and custom
rule sidecars as the prepared board. Router-generated `.kicad_pro` files may
clamp netclasses to the search clearance and make a dense route appear clean.
The prefix gate's practice of replacing sidecars from `r0` is correct and is
what prevented the invalid I2C route from being promoted into a release.

No fabrication release has been minted, and the board is not yet ready for
fabrication.

All session artifacts needed for continuation are inside the repository tree;
this resume procedure has no dependency on `/tmp`.
