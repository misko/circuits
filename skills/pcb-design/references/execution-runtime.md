# Bounded execution runtime

This reference owns how an already-selected PCB pipeline stage is executed. It
does not decide whether the stage applies, whether an engineering artifact
passes, or which artifact is accepted. Those decisions remain with the stage
contract and the owning domain gate.

Runtime policy ID owned here: `M-BOUND`.

## Contents

1. Authority boundary
2. Task envelope and attempt
3. Process-group control and filesystem detection
4. Terminal outcomes and replacement
5. Migration and canaries

## Authority boundary

The runtime receives a reviewed task envelope and direct argv. It may execute,
observe, terminate, and record that attempt. It may not synthesize missing
inputs, retry without an admitted replacement, reinterpret a gate verdict, or
promote a partial artifact.

Keep these axes separate:

- `StageSpec` says what engineering work exists.
- applicability says whether project facts require it.
- `TaskEnvelope` says how one bounded attempt may run.
- the owning gate judges the resulting engineering evidence.
- an artifact transaction chooses whether verified bytes replace an accepted
  bundle.

The current shared runtime is bounded, not hermetic. It does not enforce network
isolation, syscall/read confinement, executable digests, or OS-level writer and
process containment. Do not call a future run hermetic unless those properties
are enforced and recorded. A declaration alone is evidence of intent, not
containment.

## Task envelope and attempt

`pipeline_execution.py` owns the closed schema-1 `TaskEnvelope`, `TaskAttempt`,
`WriterScope`, and `AgentSpan` objects. Generated envelopes live under
`06_build`; they are not authored project policy.

Every executable attempt names:

- task, stage, run, and exact semantic/raw subject identities;
- direct argv, explicit cwd, finite deadline, and execution class;
- a content-addressed input packet checked before and after execution;
- an explicit environment projection rather than an accidental shell session;
- read-only or exclusive writer paths with no traversal;
- one durable attempt output path and the permitted replacement count.

Fresh-context work requires a non-empty input packet. Reviewers are fresh and
read-only. Non-agent work records context as not applicable. Model names never
enter project authority; role escalation above the recommended mechanical,
authoring, or judgment role requires a reason.

`pipeline_runtime.run_stage(...)` is the low-level bounded-process seam, and
`execute_attempt(...)` adds the content-addressed task-envelope contract.
`process_runner.run_bounded(...)` is the compatibility adapter used by the
engineering paths migrated in this robustness slice. Those migrated paths must
not retain a second timeout/process implementation. This is a scoped migration,
not a claim that every legacy subprocess owner in the repository has already
been converted. Within the migrated `pcb_flow.py` path, read-only local Git
provenance probes remain a direct-process exception: each has a 30-second
timeout, performs no network operation or project mutation, and runs before
engineering execution.

Nested bounded execution currently requires Linux `/proc` process metadata.
The outer runtime uses it to discover every child-owned subgroup before killing
the parent. On a host without that metadata, a nested attempt is refused before
launch; it never falls back to an undiscoverable subgroup.

## Process-group control and filesystem detection

The runner must:

1. verify every declared input byte and cwd before launch;
2. use direct argv and an explicit environment;
3. start a new process group, retain every stdout/stderr byte read before any
   bounded transport cutoff, and emit heartbeat;
4. enforce the finite deadline even if the group leader exits while a
   descendant keeps an inherited pipe open;
5. after leader exit and pipe EOF, inspect the original process group; a quiet
   remaining group member is a runtime error, not successful completion;
6. terminate the original process group, then escalate after the grace period;
7. verify inputs again and inventory writer paths after exit;
8. reject detected undeclared changes inside the snapshotted project root or
   changed inputs as `INCOMPLETE`;
9. persist exactly one terminal attempt and release the writer lease in
   `finally`.

Process-group containment is bounded execution, not a sandbox. A hostile child
can create a new session and escape `killpg`; the runner cuts any inherited
output transport after the deadline/grace period and returns a non-passing
result, but cgroup/subreaper containment would be required to guarantee that
such a foreign-session process is itself reaped.

Writer-scope comparison is likewise post-hoc detection, not confinement. It
observes the project-root snapshot; it cannot prevent writes or prove the
absence of writes elsewhere on the host.

Runtime output belongs in a fresh workspace. It cannot update a live board,
accepted pointer, release, or stage result until the owning gate and artifact
transaction reopen and verify it.

Network posture is fail-closed only when the runner actually enforces it. Until
then, `network: forbidden` is a recorded expectation and the attempt must not be
described as network-isolated. The same truth rule applies to tool digests and
read-set tracing.

## Terminal outcomes and replacement

An attempt ends once as `PASS`, `FAIL`, `TIMED_OUT`, `INCOMPLETE`, `ERROR`, or
`HANDOFF_REQUIRED`. Timeout, stale input, undeclared write, missing output,
telemetry loss, or runtime error never becomes PASS. Non-pass terminal states
name unresolved rows and preserve the previous accepted bundle.

Only the coordinator may admit a replacement, and only within the envelope's
limit. A late or superseded attempt remains forensic evidence and cannot update
authority. Token telemetry is optional; missing telemetry is `UNKNOWN`, and
different accounting authorities or metrics are never summed.

## Migration and canaries

Adopt the shared runner in three steps:

1. shadow the legacy conductor and compare argv, cwd, input hashes, elapsed
   outcome, process cleanup, writes, and stage result;
2. make the shared runner authoritative while the legacy adapter remains a
   compatibility shim;
3. delete the duplicate implementation after simple, high-speed digital, RF,
   and multi-layer canaries agree.

`pcb_flow.py` intentionally applies a finite 3600-second safety ceiling when a
legacy project declares no `flow.timeouts_s.<stage>` and no
`flow.timeouts_s.default`. This replaces the old effectively-unbounded wait.
Projects with legitimately longer work must declare a stage-specific timeout;
promotion canaries must exercise that declaration rather than silently raising
the fleet-wide fallback.

Known-bad tests must cover descendants with inherited pipes, descendants that
redirect all output, timeout cleanup, stale input, writer-scope escape,
duplicate terminal writes, late replacements, and a missing executable. A
shadow runtime must not change authoritative identity, verdict, pointer, or
median elapsed time beyond the documented migration budget.
