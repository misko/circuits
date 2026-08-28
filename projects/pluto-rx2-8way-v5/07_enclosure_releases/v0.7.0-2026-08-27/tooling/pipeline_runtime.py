#!/usr/bin/env python3
"""Bounded execution and work-class telemetry for declarative PCB stages.

This is an execution adapter, not a workflow engine and not an engineering
gate.  It deliberately does not decide applicability or validate produced
artifacts.  The caller supplies an applicable ``StageSpec`` and may name only
outputs which another layer has already accepted.

The implementation preserves the useful properties of
``kicad-pcb/scripts/process_runner.py`` while adding the Wave-1 runtime
contract:

* the deadline terminates the child's whole process scope, including nested
  bounded runners;
* quiet work emits bounded heartbeats;
* combined stdout/stderr is written losslessly to a per-run log;
* interactive child output is sampled to a fixed head/tail budget; and
* console and event observers cannot block deadline enforcement; and
* timing is attributed to the stage's declared work class.

``execute_attempt`` is the narrow content-addressed entry point.  It verifies
an envelope's packet both before and after execution, records net filesystem
changes against its ``WriterScope``, and atomically publishes one terminal
``TaskAttempt``.  The filesystem receipt is a post-execution detector, not a
claim of hermetic execution or network isolation.

``RuntimeOutcome.to_stage_result`` imports ``pipeline_contract`` lazily.  This
keeps the runtime independently testable while the frozen contract modules are
landed in parallel.
"""
from __future__ import annotations

import codecs
import hashlib
import json
import math
import os
import queue
import re
import signal
import stat
import subprocess
import sys
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence, TextIO

if TYPE_CHECKING:
    from pipeline_execution import TaskAttempt, TaskEnvelope


EXIT_TIMEOUT = 124
EXIT_CANCELLED = 125

# Children launched by this runtime inherit this private marker.  A runtime
# invoked from one of those children must not create a new session: doing so
# would detach it from the enclosing stage's topology.  A nested runtime
# creates an owned process *subgroup* in the enclosing session.  Its inner
# deadline and successful-exit cleanup own that subgroup, while an outer
# deadline discovers and signals every descendant subgroup before its parent
# dies.  Detection validates the marker inherited by the current process
# against its actual session/group topology; the requested child environment
# is not trusted to decide whether execution is nested.
_RUNTIME_SCOPE_ENV = "_PCB_PIPELINE_RUNTIME_SCOPE"
_SCOPE_SESSION = "session-v1"
_SCOPE_SUBGROUP = "subgroup-v1"
_OBSERVER_DRAIN_S = 0.05

WORK_CLASSES = frozenset({
    "local", "network", "backoff", "review_wait", "operator_wait",
})
SYMBOL_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z")


def _field(value: object, name: str) -> Any:
    if isinstance(value, Mapping):
        return value[name]
    return getattr(value, name)


def _new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def _inherited_runtime_scope() -> bool:
    """Validate the current process's runtime marker against its topology.

    Detection intentionally reads this process's inherited environment, not
    the caller-selected environment for the next child.  A sanitized child
    environment therefore cannot escape its outer deadline, while an
    untrusted marker supplied only in ``env=`` cannot change launch topology.
    """
    marker = os.environ.get(_RUNTIME_SCOPE_ENV)
    pid = os.getpid()
    try:
        group = os.getpgrp()
        session = os.getsid(pid)
    except OSError:
        return False
    if marker == _SCOPE_SESSION:
        return group == pid and session == pid
    if marker == _SCOPE_SUBGROUP:
        return group == pid and session != pid
    return False


def _nested_group_discovery_available() -> bool:
    """Return whether the outer runtime can discover nested process groups."""
    return Path("/proc/self/stat").is_file()


def _write(console: TextIO | None, line: str) -> None:
    if console is None:
        return
    console.write(line.rstrip("\r\n") + "\n")
    console.flush()


class _CallbackDispatcher:
    """Run an untrusted observer on a daemon without blocking the watchdog.

    Observer delivery is deliberately best-effort and bounded.  Exceptions,
    backlog overflow, and callbacks which do not drain promptly become typed
    runtime errors; none can hold the child deadline loop or terminal return.
    """

    def __init__(self, label: str, callback: Callable[[object], None] | None,
                 *, max_pending: int) -> None:
        self._label = label
        self._callback = callback
        self._queue: queue.Queue[object] = queue.Queue(maxsize=max_pending)
        self._idle = threading.Event()
        self._idle.set()
        self._lock = threading.Lock()
        self._errors: list[str] = []
        self._failed = False
        self._accepting = callback is not None
        self._thread: threading.Thread | None = None
        if callback is not None:
            self._thread = threading.Thread(
                target=self._run, name=f"pipeline-{label}", daemon=True)
            self._thread.start()

    @property
    def errors(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._errors)

    def _record(self, message: str) -> None:
        with self._lock:
            if message not in self._errors:
                self._errors.append(message)
            self._failed = True

    def submit(self, value: object) -> None:
        if not self._accepting or self._callback is None:
            return
        self._idle.clear()
        try:
            self._queue.put_nowait(value)
        except queue.Full:
            self._record(
                f"runtime {self._label} backlog exceeded bounded capacity")

    def _run(self) -> None:
        assert self._callback is not None
        while True:
            value = self._queue.get()
            try:
                if not self._failed:
                    try:
                        self._callback(value)
                    except BaseException as exc:
                        self._record(
                            f"runtime {self._label} failed: "
                            f"{type(exc).__name__}: {exc}")
            finally:
                self._queue.task_done()
                if self._queue.empty():
                    self._idle.set()

    def finish(self, timeout_s: float = _OBSERVER_DRAIN_S) -> None:
        """Stop accepting records and wait only a fixed observer grace."""
        self._accepting = False
        if self._callback is None:
            return
        if not self._idle.wait(timeout_s):
            self._record(
                f"runtime {self._label} did not drain within "
                f"{timeout_s:g}s")


def _group_has_live_members(process_group_id: int) -> bool:
    """Return whether a process group contains a non-zombie process.

    Linux exposes process-group membership and state through ``/proc``.  The
    signal-zero fallback is less precise on other POSIX hosts because it may
    also observe an unreaped zombie, but remains safe for deciding whether a
    final cleanup signal is warranted.
    """
    proc_root = Path("/proc")
    if proc_root.is_dir():
        try:
            entries = os.scandir(proc_root)
        except OSError:
            entries = None
        if entries is not None:
            with entries:
                for entry in entries:
                    if not entry.name.isdigit():
                        continue
                    try:
                        value = Path(entry.path, "stat").read_text()
                    except (OSError, UnicodeError):
                        continue
                    close = value.rfind(")")
                    fields = value[close + 2:].split() if close >= 0 else []
                    # Fields after ``comm`` begin with state, ppid, pgrp.
                    if len(fields) < 3:
                        continue
                    try:
                        member_group = int(fields[2])
                    except ValueError:
                        continue
                    if member_group == process_group_id and fields[0] != "Z":
                        return True
            return False
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _proc_table() -> dict[int, tuple[str, int, int]]:
    """Return Linux ``pid -> (state, ppid, pgrp)`` process metadata.

    The runtime is already POSIX-specific because it relies on process-group
    signals. Linux metadata lets an outer deadline discover nested runtime
    subgroups before terminating their parent. Nested execution is refused
    before launch when this metadata is unavailable; a separate subgroup must
    never be created when the outer deadline cannot discover it.
    """
    root = Path("/proc")
    if not root.is_dir():
        return {}
    result: dict[int, tuple[str, int, int]] = {}
    try:
        entries = os.scandir(root)
    except OSError:
        return result
    with entries:
        for entry in entries:
            if not entry.name.isdigit():
                continue
            try:
                pid = int(entry.name)
                value = Path(entry.path, "stat").read_text()
            except (OSError, UnicodeError, ValueError):
                continue
            close = value.rfind(")")
            fields = value[close + 2:].split() if close >= 0 else []
            # Fields after ``comm`` begin with state, ppid, pgrp.
            if len(fields) < 3:
                continue
            try:
                result[pid] = (fields[0], int(fields[1]), int(fields[2]))
            except ValueError:
                continue
    return result


def _descendant_pids(root_pid: int,
                     table: Mapping[int, tuple[str, int, int]]) -> set[int]:
    descendants = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, (_state, parent, _group) in table.items():
            if pid not in descendants and parent in descendants:
                descendants.add(pid)
                changed = True
    return descendants


def _pid_is_live(pid: int) -> bool:
    row = _proc_table().get(pid)
    if row is not None:
        return row[0] != "Z"
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _signal_scope(pids: set[int], groups: set[int], sig: int, *,
                  owns_group: bool) -> None:
    """Signal a captured child scope without ever signalling this runtime."""
    own_pid = os.getpid()
    own_group = os.getpgrp()
    if owns_group:
        for group in sorted(groups, reverse=True):
            if group <= 0 or group == own_group:
                continue
            try:
                os.killpg(group, sig)
            except (ProcessLookupError, PermissionError):
                pass
    # Exact PID signalling complements subgroup signalling and closes races
    # around unusual group membership in either a nested or top-level scope.
    for pid in sorted(pids, reverse=True):
        if pid <= 1 or pid == own_pid:
            continue
        try:
            os.kill(pid, sig)
        except (ProcessLookupError, PermissionError):
            pass


def _terminate_group(proc: subprocess.Popen[bytes], grace_s: float, *,
                     owns_group: bool = True) -> bool:
    """Terminate the launched process and every discoverable descendant.

    A top-level stage owns a fresh session/process group.  A nested stage owns
    a fresh subgroup in the enclosing session, so its inner timeout cannot
    signal the caller.  Linux process-tree discovery lets the outer owner find
    and terminate every such subgroup before it kills the subgroup parents.
    """
    table = _proc_table()
    tracked = _descendant_pids(proc.pid, table)
    groups = {
        table[pid][2] for pid in tracked
        if pid in table and table[pid][2] > 0
    }
    tracked.add(proc.pid)
    if owns_group:
        groups.add(proc.pid)
    _signal_scope(tracked, groups, signal.SIGTERM, owns_group=owns_group)

    deadline = time.monotonic() + grace_s
    while time.monotonic() < deadline:
        # While a parent is still alive, include any child created in the
        # narrow interval between the first snapshot and SIGTERM delivery.
        current = _proc_table()
        expanded: set[int] = set()
        for root_pid in tuple(tracked):
            expanded.update(_descendant_pids(root_pid, current))
        new_pids = expanded - tracked
        if new_pids:
            tracked.update(new_pids)
            groups.update(current[pid][2] for pid in new_pids
                          if pid in current and current[pid][2] > 0)
            _signal_scope(new_pids, groups, signal.SIGTERM,
                          owns_group=owns_group)
        if not any(_pid_is_live(pid) for pid in tracked):
            return True
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(0.02, remaining))

    _signal_scope(tracked, groups, signal.SIGKILL, owns_group=owns_group)
    kill_deadline = time.monotonic() + grace_s
    while time.monotonic() < kill_deadline:
        if not any(_pid_is_live(pid) for pid in tracked):
            return True
        time.sleep(min(0.02, kill_deadline - time.monotonic()))
    return not any(_pid_is_live(pid) for pid in tracked)


@dataclass(frozen=True)
class WorkTiming:
    """One measured span attributed to a closed-vocabulary work class."""

    work_class: str
    started_at: str
    finished_at: str
    elapsed_s: float

    def __post_init__(self) -> None:
        if self.work_class not in WORK_CLASSES:
            raise ValueError(f"unknown work_class: {self.work_class!r}")
        if self.elapsed_s < 0:
            raise ValueError("elapsed_s must be non-negative")

    def to_mapping(self) -> dict[str, object]:
        return {
            "work_class": self.work_class,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed_s": round(self.elapsed_s, 6),
        }


@dataclass(frozen=True)
class RuntimeOutcome:
    """Execution evidence which can be projected into a ``StageResult``."""

    stage_id: str
    run_id: str
    status: str
    started_at: str
    finished_at: str
    elapsed_s: float
    returncode: int | None
    work_timing: WorkTiming
    log_path: Path
    output_bytes: int
    output_lines: int
    console_child_lines: int
    suppressed_child_lines: int
    findings: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    pid: int | None = None

    @property
    def timed_out(self) -> bool:
        return self.status == "TIMED_OUT"

    def to_mapping(self) -> dict[str, object]:
        """Return runtime telemetry; this is not an artifact-bundle manifest."""
        return {
            "schema": 1,
            "stage_id": self.stage_id,
            "run_id": self.run_id,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed_s": round(self.elapsed_s, 6),
            "returncode": self.returncode,
            "work_timing": self.work_timing.to_mapping(),
            "log_path": str(self.log_path),
            "output_bytes": self.output_bytes,
            "output_lines": self.output_lines,
            "console_child_lines": self.console_child_lines,
            "suppressed_child_lines": self.suppressed_child_lines,
            "findings": list(self.findings),
            "outputs": list(self.outputs),
        }

    def to_stage_result(
            self, spec: object, subject: object, *,
            result_factory: Callable[..., object] | None = None) -> object:
        """Project this applicable execution into frozen StageResult schema 1.

        ``result_factory`` exists for dependency injection and parallel module
        landing.  When omitted, the public ``pipeline_contract.StageResult``
        constructor is imported only when this method is called.
        """
        spec_id = str(_field(spec, "id"))
        if spec_id != self.stage_id:
            raise ValueError(
                f"outcome stage_id {self.stage_id!r} does not match {spec_id!r}")
        if result_factory is None:
            from pipeline_contract import StageResult  # type: ignore
            result_factory = StageResult
        passed = self.status == "PASS"
        return result_factory(
            stage_id=self.stage_id,
            run_id=self.run_id,
            subject=subject,
            applicability="APPLIES",
            applicability_reason=None,
            status=self.status,
            started_at=self.started_at,
            finished_at=self.finished_at,
            elapsed_s=self.elapsed_s,
            graded=1 if passed else 0,
            total=1,
            outputs=self.outputs if passed else (),
            findings=self.findings,
            resume=None,
            schema=1,
        )


class _ConsoleSample:
    """Stream a bounded head and retain a bounded tail for final display."""

    def __init__(self, *, limit: int, tail_lines: int, line_chars: int,
                 write_line: Callable[[str], None]) -> None:
        if limit < 0:
            raise ValueError("console_line_limit must be non-negative")
        if tail_lines < 0 or tail_lines > limit:
            raise ValueError(
                "console_tail_lines must be between zero and console_line_limit")
        if line_chars <= 0:
            raise ValueError("console_line_chars must be positive")
        self._head_limit = limit - tail_lines
        self._tail: deque[str] = deque(maxlen=tail_lines)
        self._line_chars = line_chars
        self._write_line = write_line
        self.total = 0
        self.emitted = 0

    def add(self, line: str) -> None:
        self.total += 1
        clean = line.rstrip("\r\n")
        if len(clean) > self._line_chars:
            omitted = len(clean) - self._line_chars
            clean = clean[:self._line_chars] + f" [... {omitted} chars omitted]"
        if self.total <= self._head_limit:
            self._write_line(clean)
            self.emitted += 1
        elif self._tail.maxlen:
            self._tail.append(clean)

    def finish(self, stage_id: str) -> int:
        tail = list(self._tail)
        omitted = self.total - self.emitted - len(tail)
        if omitted > 0:
            self._write_line(
                f"[{stage_id}] ... {omitted} child output lines omitted; "
                "complete output retained in the run log ...")
        for line in tail:
            self._write_line(line)
            self.emitted += 1
        return max(0, self.total - self.emitted)


class _BoundedLineDecoder:
    """Decode console lines without retaining an unbounded unterminated line."""

    def __init__(self, sink: Callable[[str], None], max_pending: int) -> None:
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._sink = sink
        self._max_pending = max_pending
        self._pending = ""
        self._discarded = 0
        self._after_cr = False

    def _append(self, text: str) -> None:
        room = max(0, self._max_pending - len(self._pending))
        self._pending += text[:room]
        self._discarded += max(0, len(text) - room)

    def _emit(self) -> None:
        line = self._pending
        if self._discarded:
            line += f" [... {self._discarded} chars omitted]"
        self._sink(line)
        self._pending = ""
        self._discarded = 0

    def feed(self, raw: bytes) -> None:
        text = self._decoder.decode(raw)
        start = 0
        for index, char in enumerate(text):
            if char == "\n" and self._after_cr and index == start:
                # CRLF is one record boundary, including when the two bytes
                # arrive in separate reads.
                self._after_cr = False
                start = index + 1
            elif char in "\r\n":
                self._append(text[start:index])
                self._emit()
                self._after_cr = char == "\r"
                start = index + 1
            else:
                self._after_cr = False
        self._append(text[start:])

    def finish(self) -> None:
        self._append(self._decoder.decode(b"", final=True))
        if self._pending or self._discarded:
            self._emit()


def _project_path(root: Path, relative: str, where: str) -> Path:
    """Resolve one already-normalized contract path below ``root``."""
    path = (root / relative).resolve(strict=False)
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{where} escapes project root: {relative}") from exc
    return path


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_snapshot(root: Path, *, ignored: frozenset[str]) -> dict[str, str]:
    """Return a stable, non-following snapshot of the project filesystem."""
    snapshot: dict[str, str] = {}
    for current, dirnames, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        dirnames.sort()
        filenames.sort()
        for name in tuple(dirnames):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if relative in ignored:
                dirnames.remove(name)
                continue
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                snapshot[relative] = "symlink:" + os.readlink(path)
                dirnames.remove(name)
            else:
                snapshot[relative] = f"directory:{stat.S_IMODE(info.st_mode):o}"
        for name in filenames:
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if relative in ignored:
                continue
            info = path.lstat()
            mode = stat.S_IMODE(info.st_mode)
            if stat.S_ISLNK(info.st_mode):
                value = "symlink:" + os.readlink(path)
            elif stat.S_ISREG(info.st_mode):
                value = f"file:{mode:o}:{info.st_size}:{_file_sha256(path)}"
            else:
                value = f"special:{stat.S_IFMT(info.st_mode):o}:{mode:o}"
            snapshot[relative] = value
    return snapshot


def _snapshot_sha256(snapshot: Mapping[str, str]) -> str:
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _changed_paths(before: Mapping[str, str],
                   after: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(sorted(
        path for path in set(before) | set(after)
        if before.get(path) != after.get(path)))


def _claim_attempt(path: Path, digest: str) -> Path:
    """Reserve one attempt output without publishing a nonterminal record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        raise FileExistsError(f"terminal attempt already exists: {path}")
    claim = path.with_name(f".{path.name}.claim")
    try:
        fd = os.open(claim, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise FileExistsError(f"attempt output is already claimed: {path}") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(digest + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return claim


def _publish_attempt(path: Path, attempt: object) -> None:
    """Atomically publish one complete terminal attempt mapping."""
    mapping = getattr(attempt, "to_mapping")()
    encoded = (json.dumps(mapping, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False) + "\n").encode()
    temporary = path.with_name(
        f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _deadline_remaining(deadline_at: str) -> float:
    deadline = datetime.fromisoformat(deadline_at[:-1] + "+00:00")
    return (deadline - datetime.now(timezone.utc)).total_seconds()


def _elapsed_between(started_at: str, finished_at: str) -> float:
    started = datetime.fromisoformat(started_at[:-1] + "+00:00")
    finished = datetime.fromisoformat(finished_at[:-1] + "+00:00")
    return max(0.0, (finished - started).total_seconds())


def _scope_path_failures(root: Path, paths: Sequence[str]) -> list[str]:
    failures: list[str] = []
    for relative in paths:
        try:
            _project_path(root, relative, "writer scope path")
        except (OSError, RuntimeError, ValueError) as exc:
            failures.append(
                f"writer scope path cannot be safely resolved: {relative}: "
                f"{type(exc).__name__}: {exc}")
    return failures


def run_stage(
        spec: object, command: Sequence[str], *, log_path: str | Path,
        cwd: str | Path | None = None, env: Mapping[str, str] | None = None,
        heartbeat_s: float = 10.0, console_line_limit: int = 100,
        console_tail_lines: int = 20, console_line_chars: int = 1000,
        console: TextIO | None = sys.stdout,
        cancel_event: threading.Event | None = None, terminate_grace_s: float = 2.0,
        run_id: str | None = None, outputs: Sequence[str] = (),
        event_sink: Callable[[Mapping[str, object]], None] | None = None,
) -> RuntimeOutcome:
    """Execute one applicable stage under its declared hard deadline.

    ``outputs`` must contain only symbols already accepted by the caller.  A
    successful exit alone does not establish artifact freshness or validity.
    The log is opened with exclusive creation so a new run can never overwrite
    earlier execution evidence.  Console and event callbacks are observers:
    they are delivered asynchronously, have bounded backlogs/drain time, and
    any delivery failure tightens the result to ``ERROR``.
    """
    stage_id = str(_field(spec, "id"))
    work_class = str(_field(spec, "work_class"))
    raw_timeout = _field(spec, "timeout_s")
    if raw_timeout is None:
        raise ValueError("run_stage requires an executable spec with timeout_s")
    timeout_s = float(raw_timeout)
    if work_class not in WORK_CLASSES:
        raise ValueError(f"unknown work_class: {work_class!r}")
    if not math.isfinite(timeout_s) or timeout_s <= 0:
        raise ValueError("stage timeout_s must be positive and finite")
    if not math.isfinite(heartbeat_s) or heartbeat_s <= 0:
        raise ValueError("heartbeat_s must be positive and finite")
    if not math.isfinite(terminate_grace_s) or terminate_grace_s <= 0:
        raise ValueError("terminate_grace_s must be positive and finite")
    argv = [str(part) for part in command]
    if not argv:
        raise ValueError("command must not be empty")
    # Keep the public defaults for legacy callers, but freeze them before
    # launch so the low-level executor always receives an explicit cwd and
    # environment.  This is an inherited environment snapshot, not an
    # allowlist or a network-isolation claim.
    actual_cwd = Path.cwd().resolve() if cwd is None else Path(cwd).resolve()
    actual_env = dict(os.environ) if env is None else dict(env)
    nested_scope = _inherited_runtime_scope()
    if nested_scope and not _nested_group_discovery_available():
        raise RuntimeError(
            "nested bounded execution requires Linux /proc process metadata; "
            "refusing a subgroup the outer deadline could not discover")
    actual_env[_RUNTIME_SCOPE_ENV] = (
        _SCOPE_SUBGROUP if nested_scope else _SCOPE_SESSION)
    accepted_outputs = tuple(sorted(set(str(item) for item in outputs)))
    if any(SYMBOL_RE.fullmatch(item) is None for item in accepted_outputs):
        raise ValueError("outputs must be symbolic names")
    try:
        declared_outputs = frozenset(_field(spec, "produces"))
        has_output_declaration = True
    except (AttributeError, KeyError):
        declared_outputs = frozenset()
        has_output_declaration = False
    if accepted_outputs and has_output_declaration and not (
            set(accepted_outputs) <= declared_outputs):
        undeclared = sorted(set(accepted_outputs) - declared_outputs)
        raise ValueError(
            "accepted outputs are not declared by the stage: "
            + ", ".join(undeclared))

    log = Path(log_path).resolve()
    log.parent.mkdir(parents=True, exist_ok=True)
    console_callback: Callable[[object], None] | None = None
    if console is not None:
        console_callback = lambda value: _write(console, str(value))
    console_dispatch = _CallbackDispatcher(
        "console observer", console_callback, max_pending=4096)

    def write_console(line: str) -> None:
        console_dispatch.submit(line.rstrip("\r\n"))

    event_callback: Callable[[object], None] | None = None
    if event_sink is not None:
        event_callback = lambda value: event_sink(value)  # type: ignore[arg-type]
    event_dispatch = _CallbackDispatcher(
        "event sink", event_callback, max_pending=256)
    sample = _ConsoleSample(
        limit=console_line_limit, tail_lines=console_tail_lines,
        line_chars=console_line_chars, write_line=write_console)
    decoder = _BoundedLineDecoder(sample.add, max_pending=console_line_chars)
    actual_run_id = run_id or _new_run_id()
    started_at = _utc_now()
    started = time.monotonic()
    write_console(f"[{stage_id}] START run={actual_run_id} "
                  f"work_class={work_class} timeout={timeout_s:g}s log={log}")

    proc: subprocess.Popen[bytes] | None = None
    output_bytes = 0
    cancelled = timed_out = False
    launch_error: str | None = None
    reader_errors: list[str] = []

    def emit_event(event: str, **fields: object) -> None:
        value = {"event": event, "stage_id": stage_id,
                 "run_id": actual_run_id, **fields}
        event_dispatch.submit(value)

    # Exclusive creation protects earlier lossless evidence from accidental
    # run-id reuse.  It also gives the reader thread one stable binary sink.
    with log.open("xb") as log_file:
        try:
            proc = subprocess.Popen(
                argv,
                cwd=str(actual_cwd),
                env=actual_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                start_new_session=not nested_scope,
                process_group=0 if nested_scope else None,
                bufsize=0,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            launch_error = f"could not launch command: {type(exc).__name__}: {exc}"
            log_file.write((launch_error + "\n").encode("utf-8", errors="replace"))
            log_file.flush()

        # Bound transport memory while retaining bytes losslessly on disk.
        # Back-pressure is acceptable here: output capture is part of the
        # stage deadline, and a producer emitting faster than it can be logged
        # must not consume unbounded RAM.
        chunks: queue.Queue[bytes | None] = queue.Queue(maxsize=64)
        reader: threading.Thread | None = None
        if proc is not None:
            emit_event("running", pid=proc.pid, started_at=started_at,
                       timeout_s=timeout_s)

            def read_output() -> None:
                assert proc is not None and proc.stdout is not None
                try:
                    while True:
                        data = proc.stdout.read(65536)
                        if not data:
                            break
                        log_file.write(data)
                        log_file.flush()
                        chunks.put(data)
                except (OSError, ValueError) as exc:
                    reader_errors.append(
                        f"could not retain child output: {type(exc).__name__}: {exc}")
                finally:
                    chunks.put(None)

            reader = threading.Thread(
                target=read_output, name=f"{stage_id}-output", daemon=True)
            reader.start()
            reader_done = False
            next_heartbeat = started + heartbeat_s
            abort_deadline: float | None = None

            while proc.poll() is None or not reader_done:
                now = time.monotonic()
                runtime_errors = (reader_errors +
                                  list(console_dispatch.errors) +
                                  list(event_dispatch.errors))
                if runtime_errors and not cancelled and not timed_out:
                    write_console(
                        f"[{stage_id}] ERROR {runtime_errors[0]}; "
                        "terminating process scope")
                    abort_deadline = abort_deadline or now + terminate_grace_s
                    _terminate_group(proc, terminate_grace_s, owns_group=True)
                elif (cancel_event is not None and cancel_event.is_set()
                        and not cancelled):
                    cancelled = True
                    abort_deadline = now + terminate_grace_s
                    write_console(
                        f"[{stage_id}] CANCEL elapsed={now-started:.3f}s "
                        f"pid={proc.pid}; terminating process scope")
                    _terminate_group(proc, terminate_grace_s, owns_group=True)
                elif now - started >= timeout_s and not timed_out:
                    timed_out = True
                    abort_deadline = now + terminate_grace_s
                    write_console(
                        f"[{stage_id}] TIMEOUT elapsed={now-started:.3f}s "
                        f"limit={timeout_s:g}s pid={proc.pid}; "
                        "terminating process scope")
                    _terminate_group(proc, terminate_grace_s, owns_group=True)

                deadline_wait = max(0.0, timeout_s - (now - started))
                wait_s = max(
                    0.005, min(0.1, next_heartbeat - now, deadline_wait))
                try:
                    item = chunks.get(timeout=wait_s)
                except queue.Empty:
                    item = b""
                if item is None:
                    reader_done = True
                elif item:
                    output_bytes += len(item)
                    decoder.feed(item)
                    # Drain burst output immediately so console sampling never
                    # creates avoidable back-pressure on the child.
                    while True:
                        try:
                            extra = chunks.get_nowait()
                        except queue.Empty:
                            break
                        if extra is None:
                            reader_done = True
                            break
                        output_bytes += len(extra)
                        decoder.feed(extra)

                # A descendant can call setsid(), escape the original process
                # group, and retain the inherited output pipe. We cannot reap
                # that foreign session without an OS containment primitive,
                # but transport wait is still bounded: close our read side and
                # return a non-passing outcome after the declared grace.
                now = time.monotonic()
                if (abort_deadline is not None and not reader_done and
                        now >= abort_deadline):
                    reader_errors.append(
                        "output pipe remained open after bounded group cleanup; "
                        "a descendant may have escaped the process group")
                    if proc.stdout is not None:
                        try:
                            proc.stdout.close()
                        except OSError:
                            pass
                    reader_done = True
                    break

                if (proc.poll() is None or not reader_done) and now >= next_heartbeat:
                    remaining = max(0.0, timeout_s - (now - started))
                    write_console(
                        f"[{stage_id}] HEARTBEAT "
                        f"work_class={work_class} elapsed={now-started:.3f}s "
                        f"remaining={remaining:.3f}s pid={proc.pid}")
                    emit_event("heartbeat", pid=proc.pid,
                               elapsed_s=now - started,
                               remaining_s=remaining)
                    next_heartbeat = now + heartbeat_s

            if reader is not None:
                reader.join(timeout=terminate_grace_s)

            # A successful group leader can intentionally or accidentally
            # leave a descendant behind after every inherited output FD has
            # been redirected or closed.  Pipe EOF therefore is not terminal
            # evidence.  Reap the leader, inspect its original process group,
            # and clean any remaining live members before grading the exit.
            proc.poll()
            if _group_has_live_members(proc.pid):
                write_console(
                    f"[{stage_id}] CLEANUP leader_rc={proc.returncode} "
                    f"pid={proc.pid}; terminating remaining process group")
                reader_errors.append(
                    "group leader exited while live descendants remained")
                if not _terminate_group(
                        proc, terminate_grace_s, owns_group=True):
                    reader_errors.append(
                        "process group retained live descendants after cleanup")

    decoder.finish()
    suppressed = sample.finish(stage_id)
    event_dispatch.finish()
    finished_at = _utc_now()
    elapsed_s = time.monotonic() - started

    runtime_errors = (reader_errors + list(event_dispatch.errors) +
                      list(console_dispatch.errors))
    if launch_error is not None or runtime_errors:
        status = "ERROR"
        returncode = None if proc is None else proc.poll()
        findings = tuple(
            item for item in ([launch_error] + runtime_errors) if item is not None)
    else:
        assert proc is not None
        raw_returncode = proc.wait()
        if timed_out:
            status = "TIMED_OUT"
            returncode = EXIT_TIMEOUT
            findings = (f"command exceeded hard deadline of {timeout_s:g}s",)
        elif cancelled:
            status = "INCOMPLETE"
            returncode = EXIT_CANCELLED
            findings = ("command cancelled before completion",)
        elif raw_returncode == 0:
            status = "PASS"
            returncode = 0
            findings = ()
        else:
            status = "FAIL"
            returncode = raw_returncode
            findings = (f"command exited {raw_returncode}",)

    # Terminal console delivery is also isolated.  Its status text describes
    # the command/runtime candidate; a terminal observer failure can still
    # tighten the returned outcome to ERROR below.
    write_console(f"[{stage_id}] {status} rc={returncode} "
                  f"elapsed={elapsed_s:.3f}s output={output_bytes}B "
                  f"lines={sample.total} suppressed={suppressed} log={log}")
    console_dispatch.finish()
    terminal_console_errors = list(console_dispatch.errors)
    if terminal_console_errors:
        status = "ERROR"
        findings = tuple(dict.fromkeys(
            tuple(findings) + tuple(terminal_console_errors)))
        accepted_outputs = ()

    finished_at = _utc_now()
    elapsed_s = time.monotonic() - started
    timing = WorkTiming(
        work_class=work_class, started_at=started_at, finished_at=finished_at,
        elapsed_s=elapsed_s)
    outcome = RuntimeOutcome(
        stage_id=stage_id,
        run_id=actual_run_id,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        elapsed_s=elapsed_s,
        returncode=returncode,
        work_timing=timing,
        log_path=log,
        output_bytes=output_bytes,
        output_lines=sample.total,
        console_child_lines=sample.emitted,
        suppressed_child_lines=suppressed,
        findings=findings,
        outputs=accepted_outputs if status == "PASS" else (),
        pid=None if proc is None else proc.pid,
    )
    return outcome


def execute_attempt(
        envelope: "TaskEnvelope", command: Sequence[str], *, cwd: str | Path,
        env: Mapping[str, str], attempt_index: int = 0,
        replacement_index: int = 0, heartbeat_s: float = 10.0,
        console: TextIO | None = sys.stdout,
        cancel_event: threading.Event | None = None,
        terminate_grace_s: float = 2.0) -> "TaskAttempt":
    """Execute and persist exactly one terminal ``TaskAttempt``.

    ``cwd`` is also the project root for packet and writer-scope paths.  Both
    it and ``env`` are mandatory at this content-addressed boundary.  The
    writer receipt compares pre/post snapshots and rejects observed net
    changes outside the declared scope; it does not sandbox the child or
    enforce a network policy.
    """
    # Imports remain local so ``run_stage`` stays usable as a small standalone
    # adapter by legacy KiCad scripts.
    from pipeline_execution import (  # type: ignore
        TaskAttempt, TaskEnvelope, envelope_sha256, verify_input_packet,
        writer_scope_receipt,
    )

    if not isinstance(envelope, TaskEnvelope):
        raise TypeError("envelope must be a TaskEnvelope")
    if envelope.executor != "subprocess":
        raise ValueError("execute_attempt requires a subprocess envelope")
    argv = [str(part) for part in command]
    if not argv:
        raise ValueError("command must not be empty")
    for value, where in ((attempt_index, "attempt_index"),
                         (replacement_index, "replacement_index")):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{where} must be a non-negative integer")
    root = Path(cwd).resolve()
    if not root.is_dir():
        raise ValueError(f"cwd must be an existing directory: {root}")
    if not isinstance(env, Mapping):
        raise TypeError("env must be an explicit string mapping")
    explicit_env = dict(env)
    if any(not isinstance(key, str) or not isinstance(value, str)
           for key, value in explicit_env.items()):
        raise ValueError("env keys and values must be strings")

    digest = envelope_sha256(envelope)
    output_path = _project_path(root, envelope.output_path, "output_path")
    log_path = output_path.with_name(output_path.name + ".log")
    output_relative = output_path.relative_to(root).as_posix()
    log_relative = log_path.relative_to(root).as_posix()
    claim = _claim_attempt(output_path, digest)
    claim_relative = claim.relative_to(root).as_posix()

    started_at = _utc_now()
    runtime: RuntimeOutcome | None = None
    status = "ERROR"
    enforcement_errors: list[str] = []
    before_valid = after_valid = False
    before_failures: list[str] = []
    after_failures: list[str] = []
    before_snapshot: dict[str, str] = {}
    after_snapshot: dict[str, str] = {}
    scope_preflight = _scope_path_failures(root, envelope.writer_scope.paths)
    enforcement_errors.extend(scope_preflight)

    try:
        before_valid, before_failures = verify_input_packet(envelope, root)
        if not before_valid:
            enforcement_errors.extend(
                f"input packet stale before execution: {row}"
                for row in before_failures)
        try:
            before_snapshot = _tree_snapshot(
                root, ignored=frozenset({log_relative}))
        except (OSError, UnicodeError) as exc:
            enforcement_errors.append(
                f"could not snapshot writer scope before execution: "
                f"{type(exc).__name__}: {exc}")

        if not enforcement_errors:
            remaining_s = _deadline_remaining(envelope.deadline_at)
            if not math.isfinite(remaining_s) or remaining_s <= 0:
                status = "TIMED_OUT"
                enforcement_errors.append(
                    "envelope deadline elapsed before process launch")
            else:
                runtime = run_stage(
                    {"id": envelope.stage_id,
                     "work_class": envelope.execution_class,
                     "timeout_s": remaining_s},
                    argv, log_path=log_path, cwd=root, env=explicit_env,
                    heartbeat_s=heartbeat_s, console=console,
                    cancel_event=cancel_event,
                    terminate_grace_s=terminate_grace_s,
                    run_id=envelope.run_id)
                status = runtime.status
    except Exception as exc:
        enforcement_errors.append(
            f"execution authority error: {type(exc).__name__}: {exc}")
        status = "ERROR"

    # Reopen packet and scope state after every admitted attempt, including a
    # preflight refusal.  This keeps one receipt shape for all terminal paths.
    try:
        after_valid, after_failures = verify_input_packet(envelope, root)
        if not after_valid:
            enforcement_errors.extend(
                f"input packet stale after execution: {row}"
                for row in after_failures)
    except Exception as exc:
        enforcement_errors.append(
            f"could not verify input packet after execution: "
            f"{type(exc).__name__}: {exc}")
    try:
        after_snapshot = _tree_snapshot(
            root, ignored=frozenset({log_relative}))
    except (OSError, UnicodeError) as exc:
        enforcement_errors.append(
            f"could not snapshot writer scope after execution: "
            f"{type(exc).__name__}: {exc}")

    scope_postflight = _scope_path_failures(root, envelope.writer_scope.paths)
    enforcement_errors.extend(scope_postflight)
    changes = _changed_paths(before_snapshot, after_snapshot)
    scope_receipt = writer_scope_receipt(
        envelope.writer_scope, changes,
        before_sha256=_snapshot_sha256(before_snapshot),
        after_sha256=_snapshot_sha256(after_snapshot),
        protected_paths=tuple(sorted((claim_relative, output_relative))))
    if scope_preflight or scope_postflight:
        scope_receipt["resolution_failures"] = sorted(set(
            scope_preflight + scope_postflight))
        scope_receipt["status"] = "FAIL"
    if scope_receipt["violations"]:
        enforcement_errors.extend(
            f"writer scope violation: {path}"
            for path in scope_receipt["violations"])

    # Freshness and writer-scope authority can only remove a PASS.  A timeout
    # remains visible in the nested runtime receipt, while its terminal attempt
    # becomes ERROR if it also violated the envelope.
    if enforcement_errors:
        clean_prelaunch_timeout = (
            status == "TIMED_OUT" and
            all(row.startswith("envelope deadline elapsed")
                for row in enforcement_errors))
        if not clean_prelaunch_timeout:
            status = "ERROR"

    unresolved: list[dict[str, str]] = []
    if status == "TIMED_OUT":
        unresolved.append({
            "check": "bounded subprocess completion", "status": "INCOMPLETE",
            "detail": (runtime.findings[0] if runtime and runtime.findings
                       else "envelope deadline elapsed before process launch"),
        })
    elif status == "INCOMPLETE":
        unresolved.append({
            "check": "bounded subprocess completion", "status": "INCOMPLETE",
            "detail": "attempt was cancelled before completion",
        })

    finished_at = _utc_now()
    attempt_output = {
        "schema": 1,
        "runtime": None if runtime is None else runtime.to_mapping(),
        "input_packet": {
            "before": {"status": "PASS" if before_valid else "FAIL",
                       "failures": before_failures},
            "after": {"status": "PASS" if after_valid else "FAIL",
                      "failures": after_failures},
        },
        "writer_scope": scope_receipt,
        "enforcement_errors": enforcement_errors,
    }
    attempt = TaskAttempt(
        task_id=envelope.task_id, envelope_sha256=digest,
        attempt_index=attempt_index, replacement_index=replacement_index,
        subject=envelope.subject, started_at=started_at,
        finished_at=finished_at,
        elapsed_s=_elapsed_between(started_at, finished_at), status=status,
        unresolved=unresolved, output=attempt_output)
    try:
        _publish_attempt(output_path, attempt)
    finally:
        try:
            claim.unlink()
        except FileNotFoundError:
            pass
    return attempt
