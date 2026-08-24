# Connector and service access

Start from exhaustive disposition, then size openings from real mating hardware. A footprint courtyard is not a plug envelope.

## Disposition every candidate

Assign exactly one disposition to every extracted access candidate:

- `opening`: routine edge access with a cable or mating part.
- `service_opening`: top or occasional tool/fuse/programming access.
- `internal`: intentionally enclosed and not accessed while assembled.
- `not_fitted`: absent from the assembled variant.

Do not omit a candidate to imply `internal`. The verifier treats omission as failed coverage.

For `internal` and `not_fitted`, set `shape: none`, opening and plug vectors to zero, and clearance to zero. For an opening, use `round`, `rect`, or `arch` and positive dimensions. Top access must be `service_opening`.

## Coordinate convention

Express `center_mm` in the interface case frame: outline-bounding-box center in x/y, PCB back surface at z zero, positive z toward the component front. Sides are `north`, `south`, `east`, `west`, or `top`.

Confirm orientation against a rendered assembly and a physical board. Mirrored east/west or north/south mappings often produce plausible but unusable CAD.

## Opening and plug envelope

Measure or obtain from drawings:

- connector body that crosses the wall;
- mating plug maximum width and height;
- plug insertion depth and strain relief;
- latch, release-tab, nut, washer, wrench, and finger access;
- cable bend radius and neighboring-cable interference;
- board-placement and enclosure-registration tolerances.

Set `plug_envelope_mm` to the mating envelope, not only the receptacle. Set per-side `clearance_mm`; the verifier requires each opening dimension to cover plug dimension plus twice that clearance.

Use `arch` for openings that need a flat floor with a rounded crown. Use `round` for coax barrels or circular controls. Use `rect` where corner radius does not obstruct the real mating envelope.

## Common connector checks

- USB: test multiple overmold styles and ensure the shell does not become the insertion stop.
- SMA/coax: include hex nut and wrench clearance, cable bend, and connector rotation if applicable.
- Barrel, XT, or pluggable power: include polarity features, grip body, latch, and high-current cable bend radius.
- Switches: distinguish actuator access from complete part removal; account for travel and guard against accidental actuation.
- Replaceable fuses: provide extraction-tool or finger clearance and a safe service path.
- Programming headers: include keyed plug body, cable exit, pin-one visibility if required, and probe keepout.
- LEDs: use a light-pipe or sight opening only when required; disposition it explicitly.

## Physical mating test

At `PRINT_VERIFIED`, install the actual board and mate every required cable/tool simultaneously where the use case demands it. Record photos or measurements for each interface. A gauge, drawing, screenshot, or render alone is not mating evidence.
