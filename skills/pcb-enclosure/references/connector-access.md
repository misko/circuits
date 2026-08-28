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

- board receptacle body that crosses or approaches the wall;
- complete mated plug/overmold width, height, and insertion depth;
- rear termination, solder cup, boot, heat-shrink, or strain-relief body;
- cable outside diameter and any rigid straight run behind the termination;
- minimum bend radius, swept bend envelope, and intended exit vector;
- latch, release-tab, nut, washer, wrench, and finger access;
- neighboring-cable interference and every simultaneously mated connector;
- the service state and installation/removal sweep with cables attached as used;
- board-placement and enclosure-registration tolerances.

Set `plug_envelope_mm` to the mating envelope, not only the receptacle. Set per-side `clearance_mm`; the verifier requires each opening dimension to cover plug dimension plus twice that clearance.

For new schema-v2 work, bind `interface_assemblies` to the exact compiled PCB
connector receipt and map every `opening` or `service_opening` to its shared
assembly profile. The same block accounts for every other receipt instance in
`non_enclosure_refs`, using only the closed `no_enclosure_interface`
disposition and a non-empty human reason. Mapped refs plus those explicit
dispositions must exactly equal the receipt instance census. A simultaneous
group touched by any mapping must still map every populated member as an
obstacle; a non-enclosure disposition cannot remove a neighbor from that
service case. A wholly irrelevant group is acceptable only when every one of
its refs is explicitly dispositioned.
Do not retype connector, tool, torque, cable, or tolerance dimensions in the
schema-v2 mapping. Legacy v1 `plug_envelope_mm` and `clearance_mm` remain
candidate opening inputs, not shared connector-service authority, until a
receipt-derived projection replaces them. Inline `service_envelopes` remain a migration form that can
record conservative or dimensionless observations but cannot promote
readiness. The v1 opening check grades only its two opening axes; its third plug-envelope value
does not prove insertion depth, a cable bend, simultaneous mating, or a motion
sweep. An operation named by `mated_during_operations` must explicitly use
`cable_condition: pre_attached` and forbid both threading and disconnecting.
All populated members of a shared `simultaneous_group` must be associated with
the enclosure, share one required scope and identical nonempty mated-state
censuses, and share the same mated-during-operation census. Each touched group
also binds its connector `required_state` to one or more enclosure states. An
empty mated-during list means the enclosure makes no claim that a case motion
occurs while those cables remain attached; it does not erase the connector
contract's own required mate/fasten/service operations. A legacy config may
omit the checklist structurally, but any opening or service opening then caps
the complete required scope closure at `INCOMPLETE`.

Do not infer dimensions from a fit photograph. A dated image may establish a
relational fact—such as a heat-shrunk lead contacting a skirt—and should be
recorded as `physical_observation` with null dimensions. It can disprove the
old envelope while remaining non-transferable to the redesign. Record the
exact combination and its limits in the repository-wide
[connector assembly registry](../../../docs/connector-assembly-registry.md).

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

At `PRINT_VERIFIED`, install the actual board and mate every required cable/tool
simultaneously in each declared service state. Exercise the cable exit and
installation/removal operation, inspect for hard contact and chafe, and record
photos or measurements for each interface. A gauge, drawing, screenshot, or
render alone is not mating evidence.
