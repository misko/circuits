# ADR-0000 — commission scope: TWO projects, pod first

Status: accepted 2026-07-21

## Context

The Rev-A commission contains two custom PCBs: the small 2-layer remote
microphone POD and the large central RECORDER (XU316 + 2x PCM1865). One
project per board keeps releases, gates, and BOMs independent — they are
ordered, assembled and revised on different cadences and different fab
tiers (pod: 2-layer standard; central: 6-layer + small-via, per the
archived execution's ADR-0008/0009).

## Decision

1. Two projects: `projects/crow-mic-pod` (this board) and
   `projects/crow-recorder-central`.
2. The POD executes to full release FIRST. It is step 1 of the document's
   own build sequence ("pod prototype first"), it is small, and it
   de-risks the analog cell (mic bias, balanced driver, beeper clamp)
   that the central board's port design interops with.
3. Interop authority: the RJ45 contact map is defined ONCE (pod
   decisions/0004) and the central board must match it contact-for-contact.

## Rejected

- One combined project: couples a 15-part 2-layer board's release cadence
  to a ~90-part 6-layer board; a pod-only fix would re-gate the central.
- Central first: inverts the document's own build sequence and delays the
  cheapest risk-retirement (the analog cell).
