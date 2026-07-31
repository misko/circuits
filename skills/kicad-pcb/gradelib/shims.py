"""gradelib/shims.py — the STAT FAMILY, shimmed (canon GG-SHADOW, GG-RESOLVE).

`sitecustomize.py` observes every path a gate OPENS through `sys.addaudithook`,
and that channel is COMPLETE: the interpreter raises the `open` event itself, so
no reader can evade it. Nothing here is needed for it.

This file exists for the OTHER channel. **A gate almost never opens a file to
ask whether it is there.** MEASURED 2026-07-31 over `skills/*/scripts/*.py` +
`scripts/*.py`: 160 `.is_file()`, 88 `.is_dir()`, 82 `.exists()`, 6 `.stat()`
and 12 `os.path.*` guards across 47 of 58 scripts — and MEASURED, none of them
raises a Python audit event. An `open`-only view therefore measured EXACTLY ZERO
on GG-RESOLVE's own motivating incident (`waiver_provenance` guarding a flat
`03_src/rules/policy_waivers.yaml` with `p.is_file()`, opening nothing). So the
stat family is wrapped here and recorded as a PROBE.

**A PROBE IS ITS OWN CHANNEL AND IS NEVER SUMMED WITH A READ.** A gate that
statted a path has LOOKED at it — which is exactly the question GG-RESOLVE asks
— but it has not read it, and a coverage number that adds a probe to a read is a
strong number diluted by a weak one. `trace_audit.py` keeps them apart in every
place they are printed, and the probe channel may not carry a verdict.

`os.stat` ITSELF IS DELIBERATELY NOT PATCHED. It is on the import machinery's
hot path and takes fds and `dir_fd`; wrapping it buys the same paths through a
far riskier seam. The high-level predicates below are what gates actually write.
"""
import os
import pathlib

#: (attribute name, probe kind) pairs. THESE LISTS ARE WHAT `install()`
#: ITERATES — they are not a parallel description of the install loop, because
#: a roster that merely DESCRIBES code drifts away from it, and a declaration
#: nothing reads is the defect class this whole layer exists to find.
PATH_PROBES = [("exists", "exists"), ("is_file", "is_file"),
               ("is_dir", "is_dir")]
OSPATH_PROBES = [("exists", "exists"), ("isfile", "is_file"),
                 ("isdir", "is_dir"), ("lexists", "exists")]

#: PATH-LEVEL OBSERVATION WE KNOW WE DO NOT HAVE. This list is the honest
#: denominator of the gap; `trace_audit.py` prints its length on every run and
#: never sums it into anything. Adding a row here is a MEASUREMENT, not a
#: waiver.
UNOBSERVABLE = [
    ("a NON-PYTHON child process", "the tracer is installed via `PYTHONPATH`, "
     "so a python child inherits it and writes its own trace; a `kicad-cli` "
     "or `bun` child does not. Its ARGV is visible to the caller's own reads, "
     "its opens are not."),
    ("pcbnew's object model", "`LoadBoard(path)` takes a Python str so FILE "
     "identity IS observed like any other open — but pad/net/zone traversal "
     "is C++ and raises no Python event. GG-SHADOW/GG-RESOLVE are FILE-level "
     "predicates, so this bounds what a clean run means, not what it counts."),
    ("a C extension opening by fd", "an extension that dups or inherits a "
     "descriptor issues no `open` event for the path."),
]


class _Sink:
    """Shared record of the paths a process STATTED without opening."""

    def __init__(self):
        self.probes = set()        # (kind, abspath)

    def probe(self, kind, path):
        try:
            if isinstance(path, (str, bytes, os.PathLike)):
                self.probes.add((kind, os.path.abspath(os.fspath(path))))
        except Exception:
            pass


def install(sink):
    """Wrap every predicate in the two rosters. Returns the count patched."""
    n = 0

    def _wrap_path_pred(name, kind):
        orig = getattr(pathlib.Path, name)

        def pred(self, *a, **k):
            sink.probe(kind, self)
            return orig(self, *a, **k)
        pred.__name__ = name
        setattr(pathlib.Path, name, pred)

    for _nm, _kind in PATH_PROBES:
        _wrap_path_pred(_nm, _kind)
        n += 1

    def _wrap_ospath(name, kind):
        orig = getattr(os.path, name)

        def pred(path, *a, **k):
            sink.probe(kind, path)
            return orig(path, *a, **k)
        pred.__name__ = name
        setattr(os.path, name, pred)

    for _nm, _kind in OSPATH_PROBES:
        _wrap_ospath(_nm, _kind)
        n += 1

    # `Path.stat` LAST: `Path.exists`/`is_file`/`is_dir` are implemented ON TOP
    # of it, so patching it first would make every predicate above record
    # twice. The probe set is keyed on (kind, abspath) so the duplication would
    # be harmless — but a number that is only right because it is de-duplicated
    # is the kind of number this layer exists to distrust.
    _pstat = pathlib.Path.stat

    def _stat(self, *a, **k):
        sink.probe("stat", self)
        return _pstat(self, *a, **k)
    pathlib.Path.stat = _stat
    n += 1
    return n
