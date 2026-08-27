# Mechanical commissioning

Commission the assembly before choosing topology or drawing printable solids.
Copy `assets/mechanical-intent.template.yaml` into the mutable mechanical
workspace, replace every example, and bind the exact file from the schema-v2
configuration. The intent file is authority for assembly behavior; a render,
an inspiration STL, or a later verbal assumption is not.

## Record the target without promoting it

`desired_release.lifecycle` is `draft` or `immutable`.
`desired_release.readiness` is the requested target, not an achieved result:
`CAD_READY`, `PRINT_VERIFIED`, or `THERMALLY_VERIFIED`. Verification still
aggregates the actual required scopes conservatively.

## Enumerate installed and service states

Declare at least one `installed` state and exactly one `lid_removed` state.
For every state, list:

- parts physically present;
- fastener groups actually secured;
- whether the enclosure is closed;
- whether the PCB is independently retained.

The installed state contains every `config.installed_parts` entry and secures
every installed fastener group. The lid-removed state must omit the lid and
case-closure hardware while still securing every board-retention group. Schema
v2 requires this lid-off retention invariant; it turns serviceability into a
checked property instead of a review comment.

## Describe every insertion and removal

Schema v2 initially accepts only bounded `linear_insert` and `linear_remove`
operations. Each operation names its before and after states, moving parts,
nonzero direction, positive travel, cable condition, allowed cable actions,
and one clearance case. The moving-part census must equal the state delta.

If the real operation needs rotation, flexing, a compound path, or temporary
deformation, do not approximate it as linear. Keep the design `INCOMPLETE`
until a future motion primitive or reviewed project-specific verifier models
that behavior.

## Treat prewired parts as whole assemblies

For each cabled installed part, state whether the cable is already attached
and whether threading, bending, or disconnecting is permitted. V2 does not
authorize threading a pre-attached cable. A prewired/no-threading part must:

- have a declared linear insertion operation;
- remain `pre_attached` through that operation;
- use a clearance case whose envelope is `full_part`;
- sweep the complete body through the named opening, not merely the cable.

For a right-angle antenna accessory this means the antenna body, connector,
and already-attached lead slide through the bottom opening along the declared
holder's straight insertion leg. A cable-radius arch is insufficient.

## Preserve unknowns and exclusions

Every unresolved dimension or operation is an `unknowns` row with a scope,
question, and the readiness level it blocks. Never delete an unknown merely
to raise status. `excluded_claims` records statements the intent does not make,
such as physical fit or thermal performance.

External references carry their own authority grade and excluded claims in
the v2 config. An inspiration STL may guide topology, but it cannot silently
become antenna geometry, manufacturing dimensions, clearance evidence, or
physical-fit evidence.

## Validate before CAD

Run:

```bash
/usr/bin/python3 skills/pcb-enclosure/scripts/enclosure_v2.py \
  validate-intent "$PROJECT/03_src/mechanical/mechanical-intent-v2.yaml" \
  --output "$PROJECT/06_build/mechanical/intent-validation-v2.json"
```

Then validate the bound configuration with `validate-config`. Run the existing
CAD adapter on only the exact v1 file bound as `subject.cad_design`; do not
re-author a similar geometry config after validation. Retain the v2 validation
report beside the v1 generation receipt. The current v1 generator does not
embed every v2 operation, scope, or unknown, so bind any project-specific
motion result separately and never treat the validated declaration itself as
completed geometry evidence.
