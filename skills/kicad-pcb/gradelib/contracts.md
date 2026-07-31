# contract: skills/kicad-pcb/gradelib/

**Purpose** — the TRACER behind canon `GG-SHADOW` / `GG-RESOLVE`. It records
which paths a gate OPENED and which it merely STATTED, so `trace_audit.py` can
grade whether a checker could SEE its subject. It is not a checker itself: it
emits no verdict, no exit code and no check-ID.

**This is NOT a normal python package and must never become one.** It is a
directory placed on `PYTHONPATH`, so CPython imports `sitecustomize` from it
automatically at interpreter start — that is the whole mechanism, and it is why
~40 gates can be observed at once with zero edits to any of them.

## Allowed

| Pattern | What |
|---|---|
| `sitecustomize.py` | the auto-imported entry point: audit hook + trace flush |
| `shims.py` | the STAT-FAMILY roster and its install loop |
| `contracts.md` | this file |

Nothing else. A third module here would be imported into **every gate in the
fleet** by side effect, which is the largest blast radius in this repo.

## Audit

- **OFF BY DEFAULT.** With `GRADELIB_TRACE_DIR` unset, `sitecustomize.py`
  installs nothing and returns. A tracer that changes the thing it observes
  cannot be used on the battery it exists to grade. MEASURED and pinned:
  `t1_trace_audit.py::t_tracer_is_transparent` runs a real gate with and
  without the tracer and requires byte-identical stdout AND exit code — and
  also requires that a trace file WAS written, or the test would be vacuous.
- **NEVER CRASH THE GATE.** Every hook body is `try/except: pass`. A tracer
  that raises would make every gate look broken, which is worse than no tracer.
- **THE ROSTERS ARE WHAT THE INSTALL LOOP ITERATES**, never a parallel
  description of it. `PATH_PROBES` and `OSPATH_PROBES` are read by `install()`;
  a roster that merely DESCRIBES code drifts away from it, and a declaration
  nothing reads is the defect class this layer exists to find.
- **`UNOBSERVABLE` IS A MEASUREMENT, NOT A WAIVER.** It enumerates the
  path-level channels this tracer knows it cannot see (a non-python child,
  pcbnew's C++ object model, an fd-inherited open). `trace_audit.py` prints its
  length on every run and **never sums it into any coverage number** — adding a
  known gap to an observed count is how `coverage: 35/35` happened.
- **READS AND PROBES ARE SEPARATE CHANNELS.** `open` is raised by the
  interpreter and is complete; the stat family is shimmed here because none of
  `Path.exists/is_file/is_dir/stat` or `os.path.*` raises an audit event. A
  probe is weaker evidence than a read, the two are never summed, and the probe
  channel may not carry a verdict.
- `Path.stat` is patched LAST, because `exists`/`is_file`/`is_dir` are built on
  it and patching it first would double-record. The probe set is a set, so the
  duplication would be harmless — but a number that is only right because it is
  de-duplicated is the kind of number this layer exists to distrust.
- Changing what is observed changes what every `GG-*` verdict means. A roster
  edit requires a matching row edit in
  `references/design-policies.md` and a red-verification in
  `tests/t1_trace_audit.py` that MEASURES the pre-edit behaviour going blind
  (`t_kb_the_stat_channel_off_blinds_resolve` is the worked example: it builds
  a copy of this directory with the stat family removed and requires GG-RESOLVE
  to go silent while GG-SHADOW stays firing).
