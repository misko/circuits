# Source-to-preparation board authority

Use this reference before placement-feasibility grading or deterministic route
preparation. It owns the closed source facts from which physical layer order,
routing-class eligibility, reference relationships, via spans, route-wave
ownership, and conservative stitch defaults are derived. It does not own
placement geometry, router mechanics, final DRC, or manufacturer stackup
confirmation.

## Contents

1. Authority chain and schemas
2. `stackup-v1`
3. Live topology and migration
4. Route ownership and derived defaults
5. Receipt and compatibility rollout
6. Promotion canaries

## Authority chain

```text
authored closed contracts       independently observed source facts
  stackup-v1                 + observed-source-facts-v1
  route-plan-v1              + optional topology-migration-v1
                 \             /
                  board_authority.py
                           |
                  source-prep-authority-v1
                           |
        future promoted P-FEASIBILITY / route-preparation adapters
                           |
                   realized-board verification
```

The compiler is data-only and does not import `pcbnew`. An adapter may extract
live refs, nets, MPNs, and KiCad layer IDs, but the adapter must not reinterpret
their meaning. The four normalized inputs and the receipt are canonical-JSON
SHA-256 bound. Reopen the receipt with the same inputs before consuming it.
Structural/self-hash verification without exact inputs is inspection only: an
actor can rewrite a receipt and recompute an unkeyed digest. Every execution
seam must reopen against the exact stack, observations, route plan and optional
migration. During rollout, the placement hot path only records those inputs in
a pending shadow request; a separately budgeted canary compiles and reopens the
receipt. Only a future promoted consumer may rely on an accepted bundle.

Use these public functions from
`skills/kicad-pcb/scripts/board_authority.py`:

- `compile_source_prep_authority(...)` to compile;
- `write_authority(...)` to serialize atomically;
- `reopen_authority(...)` or `verify_authority(...)` before consumption;
- `physical_copper_order(...)` and `physical_via_span(...)` when an adapter
  needs physical order without compiling the complete receipt.

Do not sort KiCad numeric layer IDs. They identify API layers; they do not
encode physical top-to-bottom order.

## `stackup-v1`

The authored `copper` list is the sole physical-order authority. It begins at
`F.Cu`, ends at `B.Cu`, and contains at least two unique layer names.

```yaml
schema: stackup-v1
copper:
  - {name: F.Cu, thickness_um: 35, role: signal}
  - {name: In1.Cu, thickness_um: 18, role: reference_plane, plane_net: GND}
  - {name: In2.Cu, thickness_um: 18, role: mixed}
  - {name: B.Cu, thickness_um: 35, role: signal}
routing_classes:
  usb_hs:
    allowed_layers: [F.Cu, B.Cu]
    references: {F.Cu: In1.Cu}
    reference_required: true
  control:
    allowed_layers: [In2.Cu]
    references: {}
    reference_required: false
via_families:
  ordinary_through:
    {from_layer: F.Cu, to_layer: B.Cu, kind: through}
```

Roles are `signal`, `mixed`, `reference_plane`, or `power`. Only `signal` and
`mixed` are generically routable. A `reference_plane` or `power` layer must
name its plane net. A routable layer must not also claim a plane net.

Set `reference_required: true` from the interface/SI contract when every legal
signal layer needs a continuous return reference. Do not infer this from a
class name. Declare a routing-class reference when more than one adjacent
reference could apply. The compiler may derive a reference only when exactly
one adjacent `reference_plane` with an explicit net exists. Ambiguity or a
missing required reference is a finding, never a guessed pass. Via kinds must
agree with the physical span:

- `through`: outermost to outermost;
- `blind`: exactly one outer endpoint;
- `buried`: neither endpoint outer;
- `microvia`: one physical copper-to-copper edge.

`adapt_legacy_stack(...)` is an authoring aid only. Its wrapper says
`authoritative: false`, exposes assumptions in `notes`, and returns a candidate
that a human must review and copy into an authored `stackup-v1` contract. Never
feed the wrapper into execution or treat an inferred 35 um layer as measured.

## Live topology and migration

The compiler grades route authority against independent current observations:

```yaml
schema: observed-source-facts-v1
refs: [J1, U1]
nets: [GND, USB_N, USB_P]
mpns: [EXACT-CONNECTOR-MPN, EXACT-HUB-MPN]
occurrences:
  - {kind: ref, value: U_OLD, source: 01_docs/decisions/0007.md,
     scope: historical}
```

`occurrences` are provenance, not a second population. Only `scope: live`
contributes a current fact; `scope: historical` cannot resurrect removed
refs, nets, or MPNs.

When topology changes, declare only the intended delta:

```yaml
schema: topology-migration-v1
id: replace-regulator
why: replace the package and external switch node
remove: {refs: [U_OLD], nets: [OLD_SW], mpns: [OLD-MPN]}
add: {refs: [U_NEW], nets: [NEW_SW], mpns: [NEW-MPN]}
```

Every removal must be absent from live observations and every addition must be
present. Unmentioned live population remains valid. Stale topology anywhere
in dormant groups or exclusions still fails; a migration is not permission to
keep two competing authorities.

## Route ownership and derived defaults

`route-plan-v1` assigns every live net exactly once to a wave, deterministic
producer, or explicit exclusion:

```yaml
schema: route-plan-v1
groups: {usb: [USB_N, USB_P]}
waves:
  - {name: usb, group: usb, routing_class: usb_hs}
exclusions:
  - {pattern: GND, owner: reference-plane, why: ordinary ground pour}
deterministic_owners: []
```

Groups and explicit net lists are set-like; wave order remains authored. A
`rest` wave receives the unclaimed live complement. Multiple owners, uncovered
nets, empty waves, absent groups/classes, removed nets, and classes with no
legal physical layers fail compilation.

The receipt can derive only facts entailed by this authority:

- legal physical layers and declared/unambiguous reference-plane checks;
- inclusive physical via spans;
- reference layers and nets available for stitching;
- one stitch via family only when exactly one declared family spans every
  reference plane; otherwise `requires_explicit_via_family`;
- cleanup scope `emitted`, so a producer cannot delete foreign copper.

It never guesses signal-net membership, stitch bounds, via geometry, a plane
net, or placement coordinates.

## Receipt and compatibility rollout

`source-prep-authority-v1` records input hashes, nonzero coverage, sorted
findings, physical order, resolved classes/vias, live facts, migration result,
resolved route owners, and derived defaults. A PASS says these source facts are
closed and internally consistent. It does not prove that a route exists or
that the realized board matches the receipt.

Roll out with one authority and separate diagnostics:

```text
legacy prep/placement verdict ---------------------> execution decision
                 |
                 +-> pending request
                         |
                         +-> separate compile/reopen -> canary comparison
                                                        diagnostic only
```

During shadow operation:

- let the placement hot path record only the pending request; it does not run
  this compiler;
- in a separately budgeted canary, record the new receipt and its exact
  subject/input hashes;
- keep a compiler/read/verification error inside that canary diagnostic; it
  must not replace the authoritative verdict or legacy accepted-state identity;
- never let a shadow PASS loosen a legacy fail, incomplete, or stop;
- preserve the prior accepted prep/placement/route state on disagreement;
- classify disagreement by input resolution, applicability, denominator,
  predicate, or backtrack owner;
- change only the owning source, then regenerate downstream evidence.

Promotion is one boundary at a time. In the promotion change, make the new
receipt authoritative and remove the replaced duplicate invocation. Git keeps
the old implementation; do not retain a second live legacy switch indefinitely.

## Promotion canaries

Require all of the following before authority changes:

1. Focused green and known-bad fixtures for two-, four-, and six-layer stacks;
   physical layer-ID ordering; missing/ambiguous plane facts; via-kind spans;
   removed topology; duplicate/uncovered route ownership; tampered receipts;
   and non-authoritative legacy adapters.
2. USB Hub v4, Pluto RX2 8-way v4, and USB-controlled-debug-hub traces using
   repository source, not hand-shaped fixture inputs.
3. Old/new agreement on stage order, applicability, subject identity,
   denominators, verdict, blockers, and typed backtrack target.
4. A reviewed explanation for every new stricter failure. A shadow mismatch is
   evidence to investigate, not a reason to weaken the new predicate.
5. A no-op rerun with identical receipt identity and a changed-input rerun that
   invalidates reuse.

Keep the legacy decision authoritative until these canaries are green. A new
checker that cannot observe an independent fact stays shadow even if its unit
tests pass.
