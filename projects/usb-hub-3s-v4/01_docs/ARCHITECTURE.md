# USB Hub 3S v4 — provisional architecture

This is the commission-stage architecture boundary, not a selected circuit.
Machine-readable facts live in `../03_src/rules/`; parts and component values
remain open until the parts gate.

## Power tree

```text
3S LiPo pack (9.0–12.6 V)
  -> input disconnect/protection (selection pending)
     -> step-down conversion for USB-A service
        -> three individually protected USB-A charge-only receptacles
     -> step-down conversion for USB-C service
        -> one protected USB-C power-only receptacle for Raspberry Pi 4
```

The load-derived envelopes are in `rules/power_tree.yaml`; converter names in
that file are Stage 1 candidates, not approved selections. With 5 V outputs
always below the 9 V minimum input, the required conversion class is buck.

## Net domains

`rules/nets.yaml` deliberately contains no final netclasses at commission.
Stage 1 must derive at least the battery-input trunk, each switching loop,
regulated output trunks, per-port protected outputs, ground, feedback/sense,
enable/control, and Type-C CC domains from the selected parts. No USB D+/D−
domain is permitted by D1.

## Stackup

Provisional JLCPCB standard four-layer stack:

| Layer | Intended purpose |
|---|---|
| F.Cu | Components, short switching loops, local power and signals |
| In1.Cu | Solid, unsplit ground reference |
| In2.Cu | Power distribution, partitioned only after return-path review |
| B.Cu | Low-density escape/control routing and ground pour |

The exact JLCPCB stackup and any impedance option must be cited before board
generation. No controlled-impedance signal is currently in scope.

## Ground strategy

Use an uninterrupted In1 ground reference. Keep high-di/dt converter loops
local and return them directly to their local input/output capacitor grounds.
Do not use a split ground as a substitute for placement and return-path control.
The final via-stitch plan follows, rather than precedes, the selected packages
and reviewed placement.

## Critical geometries

- converter input-capacitor, switch and rectification loops;
- switch-node copper area and separation from feedback/sense paths;
- Kelvin current-sense and feedback connections;
- high-current battery and 5 V delivery paths, including connector contacts;
- local decoupling adjacency and thermal-pad via fields;
- connector edge access, shell clearances and mechanical retention;
- CC pull-up placement at the USB-C source receptacle;
- protection-device ordering so the protected/unprotected boundary is visible.

No geometry, footprint, or width is approved until the corresponding dossier,
netclass and placement constraint is present in machine-readable source.
