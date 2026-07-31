"""gradelib/sitecustomize.py — the tracer (canon GG-SHADOW, GG-RESOLVE).

    export PYTHONPATH=<repo>/skills/kicad-pcb/gradelib:$PYTHONPATH
    export GRADELIB_TRACE_DIR=/some/dir
    <run any gate normally>

WHY A TRACER AND NOT A DECLARATION. The defect class this exists to kill is "a
gate that is green, internally honest, and STRUCTURALLY INCAPABLE OF SEEING ITS
SUBJECT". Sixteen instances were found BY HAND in one session; every one was
written by an author who believed the gate read its subject. A mechanism that
asks that author to DECLARE what the gate reads asks exactly the question they
already got wrong, and grades zero on day one because nobody has filled it in.
What a gate actually opened is not a matter of opinion, so it is measured.

TWO CHANNELS, NEVER SUMMED.

  events    `open`, raised by the interpreter itself. COMPLETE — no reader can
            evade it. This is GG-SHADOW's evidence and half of GG-RESOLVE's.
  probes    the stat family (`Path.exists/is_file/is_dir/stat`, `os.path.*`),
            wrapped in `shims.py` because NONE of them raises an audit event.
            A path a gate STATTED was looked at but not read; that is weaker
            evidence and `trace_audit.py` keeps it in its own column.

WHAT THIS DOES NOT OBSERVE, stated here rather than left to be discovered: a
gate's PREDICATE. A gate can read its entire subject and compute the wrong
thing — a net-blind spacing guard, a Euclidean test on a topological question,
a lattice pitch measured on the wrong axis. No read-set reaches those. Say so
out loud rather than letting a green GG-* imply it.

OFF BY DEFAULT. With `GRADELIB_TRACE_DIR` unset this module installs nothing and
returns immediately — a gate run without the variable behaves exactly as it did
before, byte for byte. That is deliberate: a tracer that changes the thing it
observes cannot be used on the battery it is meant to grade. Pinned by
`tests/t1_trace_audit.py::t_tracer_is_transparent`, which compares a real gate's
stdout and exit code with and without it.

THE FAILURE MODE OF THIS FILE. Drop `PYTHONPATH`, run under `env -i`, or add a
driver stage that shells out with a cleaned environment, and every gate silently
loses observation while still printing its verdict. **A MISSING TRACE IS
INDISTINGUISHABLE, FROM INSIDE THE TRACE, FROM A GATE THAT READ NOTHING.** The
defence here is the CANARY: `trace_audit.py` runs hand-written gates with known
defects FIRST, and their silence is exit 5 (UNOBSERVABLE), never exit 0.
"""
import atexit
import json
import os
import sys

_DIR = os.environ.get("GRADELIB_TRACE_DIR")

if _DIR:
    # Loaded BY PATH, not by name: `sitecustomize` is imported from whatever is
    # first on sys.path, and a bare `import shims` would take any other module
    # of that name ahead of ours. The roster is load-bearing.
    import importlib.util as _ilu                    # noqa: E402

    _spec = _ilu.spec_from_file_location(
        "gradelib_shims",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "shims.py"))
    shims = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(shims)

    _SINK = shims._Sink()
    _EV = []
    _CAP = int(os.environ.get("GRADELIB_MAX_EVENTS", "200000"))
    _BUSY = [False]

    #: paths every process touches that say nothing about the gate's subject.
    _NOISE = ("/usr/lib/python", "/usr/lib64/python", "site-packages",
              "dist-packages", "__pycache__", "/proc/", "/sys/",
              "/dev/", "/etc/ld.so", "encodings/")

    def _boring(p):
        return (not isinstance(p, str)) or any(n in p for n in _NOISE) \
            or p.endswith((".pyc", ".so"))

    def _hook(event, args):
        # Reentrancy guard: the hook itself must never recurse through open().
        if _BUSY[0] or len(_EV) >= _CAP:
            return
        _BUSY[0] = True
        try:
            if event == "open":
                p = args[0]
                if isinstance(p, int) or _boring(p):
                    return
                _EV.append({"k": "open", "p": str(p),
                            "m": str(args[1]) if len(args) > 1 else "r"})
        except Exception:
            pass
        finally:
            _BUSY[0] = False

    def _flush():
        _BUSY[0] = True            # our own writes are not the gate's reads
        try:
            probes = [{"how": k, "p": p} for k, p in sorted(_SINK.probes)
                      if not _boring(p)]
            rec = {
                "pid": os.getpid(),
                "argv": [str(x) for x in sys.argv],
                "cwd": os.getcwd(),
                "events": _EV,
                "probes": probes,
                "probes_patched": _N_PATCHED,
                "unobservable": len(shims.UNOBSERVABLE),
                # READ BY `trace_audit.truncated_traces()`, WHICH TURNS IT INTO
                # EXIT 5. It was written here and read by NOTHING for the whole
                # of this tracer's first life — a declaration with no consumer,
                # which is the defect class this layer exists to report. It is
                # not advisory: `_EV` STOPS APPENDING at the cap, so a truncated
                # record is a PREFIX of the read-set, and GG-SHADOW's claim is
                # *nothing opened this file* — the one claim a prefix cannot
                # support. Truncation therefore manufactures FALSE findings
                # rather than losing true ones, so a run that hits the cap
                # carries no GG verdict at all.
                "truncated": len(_EV) >= _CAP,
            }
            os.makedirs(_DIR, exist_ok=True)
            out = os.path.join(_DIR, f"trace.{os.getpid()}.json")
            with open(out, "w") as fh:                    # the REAL open
                json.dump(rec, fh)
        except Exception:
            # A tracer that crashes the gate it observes is worse than no
            # tracer: it would make every gate look broken. Stay silent here
            # and let `trace_audit.py` report the MISSING trace, which is a
            # finding about observability, not a skip.
            pass

    _N_PATCHED = shims.install(_SINK)
    sys.addaudithook(_hook)
    atexit.register(_flush)
