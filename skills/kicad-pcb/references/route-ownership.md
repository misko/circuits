# Route ownership and corridor preflight

Use this module when a board has many-pad power, crystals, RF launches,
strict no-via nets, or two wave groups competing for one physical escape.
Ordinary low-density point-to-point boards do not need declarations.

```text
nets.yaml intent + pad cardinality + constrained pairs + wave order
                              |
                              v
                 route_ownership_preflight.py
                   /                       \
      owner/order is explicit          contradiction or omission
              |                                  |
              v                                  v
           route KRT                  stop before search; backtrack
```

## Configuration

Add `route.ownership` only for facts that need ownership:

```yaml
route:
  ownership:
    multipad_threshold: 8
    nets:
      P5V_PROTECTED:
        topology: wide_trunk
        owner: prep.seed_stubs
        why: reviewed three-amp trunk with named local launches
    corridors:
      hub_top_escape:
        claim_order: [control_crystal, usb_upstream, control_bulk]
        why: the F.Cu-only oscillator owns the only legal local exit
```

If a net is owned by `zone`, `prep.seed_stubs`, `stitch.seed_stubs`, or
`taps.connections`, do not also put the complete net in a generic route wave.
`route.wave` is permitted for a many-pad pour/wide intent only with the loud
`allow_generic_router: true` exception and reviewed evidence in `why`.

Run before KRT:

```bash
/usr/bin/python3 skills/kicad-pcb/scripts/route_ownership_preflight.py \
  PROJECT/03_src/route.yaml --json PROJECT/06_build/route/ownership.json
```

## Minimal acceptance tests

| Case | Expected |
| --- | --- |
| 22-pad `pour_or_wide_track` net, no owner | `O-PWR` fail |
| Deterministic trunk also requested by KRT | `O-DOUBLE` fail |
| Deterministic trunk excluded from KRT | pass |
| Flexible wave claims a shared corridor before F.Cu-only crystal | `O-FLEX` fail |
| Simple point-to-point board with no special facts | N-A/pass with no ceremony |
