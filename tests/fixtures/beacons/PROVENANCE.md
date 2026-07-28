# fixtures/beacons — REAL drifted STATUS beacons, verbatim

Two beacons as they actually stood in the tree at commit **98f4c3a**
(2026-07-27), copied byte-for-byte. They are the known-bad inputs for
`status_beacon_check.py` (canon M-BEACON) in `t1_status.py`.

Nothing here is fabricated. When the gate was written, four of the fleet's six
beacons named the wrong release; these two carry all four defect properties
between them, so no synthetic beacon was needed and none was written.

| file | copied from | defects it carries |
|---|---|---|
| `crow-mic-pod-v2_STATUS.md` | `projects/crow-mic-pod-v2/01_docs/STATUS.md` | **M-BEACON-DUP** — `stage:`/`step:`/`measure:`/`state:` each appear TWICE (lines 8-11 = v1.1's `blocked` seal frame, lines 12-15 = v1.2's `done` frame APPENDED below it) in a file the 01_docs contract says is OVERWRITTEN. `pcb_status.py` takes the last value, so it reported `sealed / done` — plausible, internally consistent, and naming a superseded release. **M-BEACON-REL** — claims a completed seal of v1.2 while the live release is `crow-mic-pod-v2-v1.3-2026-07-27`. **M-BEACON-AGE** — `updated: 2026-07-26T12:15:00` predates that seal. |
| `smc0985-cooksense_STATUS-cooksense.md` | `projects/smc0985-cooksense/01_docs/STATUS-cooksense.md` | **M-BEACON-FIELD** — no `step:`, no `op_pid:`, no `updated:` at all (it carries 20 non-schema narrative keys instead, which the reader ignores entirely). **M-BEACON-AGE** — with no clock, it cannot be shown fresher than the `cooksense-v1.4-2026-07-26` seal; the frame still read `stage: routed` two releases later. |

The tests run these against the REAL sealed `07_releases/` directory sets of
the same two boards (read-only, via `--releases-root`), so the tree half of
every verdict is real too — the release names, the numeric ordering and the
`SUPERSEDED.md` chain are not mocked.
