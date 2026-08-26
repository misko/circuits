# Assembly, motion, and service verification

Final-position collision is necessary but not sufficient. A reasonable
enclosure must admit a declared assembly path, preserve required service
states, and keep each retained member secured by the intended hardware.

## State graph

Treat `mechanical-intent.yaml` as a small state graph:

```text
lid removed, PCB secured
        │ linear accessory insertion using full body
        ▼
lid removed, accessory installed, PCB still secured
        │ linear lid installation
        ▼
closed installed assembly
```

The validator checks part and fastener censuses at each node. The installed
node contains every installed part and secured closure group. The lid-removed
node omits the lid and closure group while preserving board-retention groups.

## Supported motion

V2 supports only rigid linear insertion and removal:

```text
p(t) = p0 + unit(direction) * travel_mm * t,  0 <= t <= 1
```

An exact sweep must evaluate the complete moving solid throughout that
interval. A conservative-envelope sweep must evaluate a declared full-body
envelope over the same interval. Both are stronger than checking only `t = 1`.
The bundled v2 tool validates these method declarations but does not execute
the sweep; use a reviewed project-specific verifier or keep the affected scope
`INCOMPLETE`.

Do not encode an L-shaped *part* as an S-shaped or compound *motion*. For a
top-mounted antenna holder, model the holder's fixed right-angle geometry,
then model the antenna's actual straight insertion leg from the wide bottom
opening. When the cable is already attached and exits the top, there is no
cable-threading operation.

## Clearance-case construction

For each operation:

1. Select the complete moving installed part or conservative full-body twin.
2. Name every static installed obstacle present during the operation.
3. Use the same frame and transform as the final assembly.
4. Sweep over the complete declared travel.
5. Check the requested minimum clearance, not only zero intersection.
6. Bind the generated collision evidence to the config, subjects, transforms,
   operation ID, and tool identity.

If the geometry authority is merely inspiration, do not run a plausible sweep
and call it clearance. Preserve the inspiration reference and leave the scope
`INCOMPLETE` until actual dimensions or a conservative candidate envelope is
bound with honest excluded claims.

## No-threading rule

When a cable is pre-attached and threading is prohibited, the clearance case
must use `full_part`. The opening must pass the largest traversing antenna/body
radius plus clearance. `cable_only` and `conservative_body` are rejected for
this operation because neither proves that the complete prewired assembly can
be slid into place.

## Independent fastener service invariant

Removing case-closure screws and the lid must not loosen the PCB. Verify both
the declared state and generated geometry:

- board-retention and case-closure axes are disjoint;
- board-retention retains PCB plus base, not lid;
- case-closure retains base plus lid, not PCB;
- the lid-removed state keeps board-retention groups secured;
- a physical lid-off retention test is required for print qualification.

The schema catches role or axis contradictions. CAD verification must still
check local material, engagement, head bearing, tip clearance, tool approach,
and collision with board/components.

## Unsupported operations

Stop at `INCOMPLETE` for rotations, snap deflection, elastic clips, routed
cables, hinged motion, multi-leg insertion, or temporary disassembly unless a
reviewed project-specific verifier models them. Never replace unsupported
motion with a render or an unrecorded hand-assembly assumption.
