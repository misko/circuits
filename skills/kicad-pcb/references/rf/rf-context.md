# Conditional RF module

This adapter routes `RF-CONTRACT`, `RF-CONTEXT`, `RF-SOLVER`, `RF-SOURCE`, and
`RF-REALIZED` to their executable checks without adding another pipeline owner.

Load this module only when `03_src/rules/rf.yaml` says `rf.enabled: true`.
`rf_context.py` selects the relevant local source cards before schematic or
layout generation. It performs no web search, launches no agent, and owns no
human-review wait.

## Source voices

Keep these distinct:

- **Normative** — manufacturer or component-vendor guidance usable as a design
  input, subject to its stated limits.
- **Background** — textbook or industry-standard framing. It explains why a
  check matters but does not invent a manufacturer tolerance.
- **Tool capability** — what the editor/file format can represent. It is not an
  RF-performance claim.
- **Precedent/incident** — prior-board evidence. Clean-room mode excludes it;
  an explicit project policy is required to admit it.

## Bounded sequence

1. **Applicability** — decide RF/non-RF and risk tier in source.
2. **Context** — select source cards locally and fail fast on missing topic
   coverage.
3. **Source geometry** — inventory the exact RF denominator, stackup,
   cross-section, planned line/arc primitives, fence authority, and bend
   policy before expensive generation.
4. **Realized geometry** — independently reopen the saved board and measure
   RF nets, widths/layers, topology, bends/arcs, vias/stubs, and both fence
   flanks. Bind the report to the exact board bytes.
5. **Human review** — use the existing independent RF schematic/PCB/fab
   reviews. Do not add another reviewer or another polling stage.
6. **Fabrication/first article** — bind the exact JLC order previews and perform
   the declared VNA or time-domain measurements. Planning calculations do not
   turn those obligations green.

`rf.analysis.solver_jobs[].network: false` is a reviewed policy assertion, not
an OS network sandbox on hosts that cannot create a network namespace. Solver
commands therefore remain project-owned direct argv over declared local inputs;
the hard deadline/process-group kill is enforced independently.

Geometry checking begins advisory. It becomes blocking only when
`rf.process.geometry_policy: blocking` adopts an executable threshold and any
exception names one measured site with rationale and evidence. Arc support is
an end-to-end capability: emission, saved-board reading, fence measurement,
DRC, rendering, and audit must all accept the same primitive before the policy
may require arcs.
