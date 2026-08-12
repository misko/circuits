#!/usr/bin/env python3
"""Bounded execution and work-class telemetry for declarative PCB stages.

This is an execution adapter, not a workflow engine and not an engineering
gate.  It deliberately does not decide applicability or validate produced
artifacts.  The caller supplies an applicable ``StageSpec`` and may name only
outputs which another layer has already accepted.

The implementation preserves the useful properties of
``kicad-pcb/scripts/process_runner.py`` while adding the Wave-1 runtime
contract:

* the deadline terminates the child's whole process group;
* quiet work emits bounded heartbeats;
* combined stdout/stderr is written losslessly to a per-run log;
* interactive child output is sampled to a fixed head/tail budget; and
* timing is attributed to the stage's declared work class.

``RuntimeOutcome.to_stage_result`` imports ``pipeline_contract`` lazily.  This
keeps the runtime independently testable while the frozen contract modules are
landed in parallel.
"""
from __future__ import annotations

import codecs
import math
import os
import queue
import signal
import subprocess
import sys
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence, TextIO


EXIT_TIMEOUT = 124
EXIT_CANCELLED = 125

WORK_CLASSES = frozenset({
    "local", "network", "backoff", "review_wait", "operator_wait",
})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z")


def _field(value: object, name: str) -> Any:
    if isinstance(value, Mapping):
        return value[name]
    return getattr(value, name)


def _new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def _write(console: TextIO | None, line: str) -> None:
    if console is None:
        return
    console.write(line.rstrip("\r\n") + "\n")
    console.flush()


def _terminate_group(proc: subprocess.Popen[bytes], grace_s: float) -> None:
    """Terminate every process in the session started for ``proc``."""
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    # The direct child can exit after spawning a descendant which inherited
    # the output pipe.  In that case ``proc.poll()`` is already non-null but
    # the stage is still live, so signalling may not stop at the group leader.
    if proc.poll() is None:
        try:
            proc.wait(timeout=grace_s)
        except subprocess.TimeoutExpired:
            pass
        else:
            # Give descendants the same grace interval rather than declaring
            # the whole session finished merely because its leader exited.
            deadline = time.monotonic() + grace_s
            while time.monotonic() < deadline:
                try:
                    os.killpg(proc.pid, 0)
                except ProcessLookupError:
                    return
                time.sleep(min(0.02, deadline - time.monotonic()))
    else:
        deadline = time.monotonic() + grace_s
        while time.monotonic() < deadline:
            try:
                os.killpg(proc.pid, 0)
            except ProcessLookupError:
                return
            time.sleep(min(0.02, deadline - time.monotonic()))
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=grace_s)
    except subprocess.TimeoutExpired:
        # This should be unreachable for a direct child.  Keep the runtime
        # bounded even if a platform does not honour process-group signals.
        pass


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
                 console: TextIO | None) -> None:
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
        self._console = console
        self.total = 0
        self.emitted = 0

    def add(self, line: str) -> None:
        self.total += 1
        clean = line.rstrip("\r\n")
        if len(clean) > self._line_chars:
            omitted = len(clean) - self._line_chars
            clean = clean[:self._line_chars] + f" [... {omitted} chars omitted]"
        if self.total <= self._head_limit:
            _write(self._console, clean)
            self.emitted += 1
        elif self._tail.maxlen:
            self._tail.append(clean)

    def finish(self, stage_id: str) -> int:
        tail = list(self._tail)
        omitted = self.total - self.emitted - len(tail)
        if omitted > 0:
            _write(self._console,
                   f"[{stage_id}] ... {omitted} child output lines omitted; "
                   "complete output retained in the run log ...")
        for line in tail:
            _write(self._console, line)
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


def run_stage(
        spec: object, command: Sequence[str], *, log_path: str | Path,
        cwd: str | Path | None = None, env: Mapping[str, str] | None = None,
        heartbeat_s: float = 10.0, console_line_limit: int = 100,
        console_tail_lines: int = 20, console_line_chars: int = 1000,
        console: TextIO | None = sys.stdout,
        cancel_event: threading.Event | None = None, terminate_grace_s: float = 2.0,
        run_id: str | None = None, outputs: Sequence[str] = ()) -> RuntimeOutcome:
    """Execute one applicable stage under its declared hard deadline.

    ``outputs`` must contain only symbols already accepted by the caller.  A
    successful exit alone does not establish artifact freshness or validity.
    The log is opened with exclusive creation so a new run can never overwrite
    earlier execution evidence.
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
    accepted_outputs = tuple(sorted(set(str(item) for item in outputs)))
    if any(not item for item in accepted_outputs):
        raise ValueError("output symbols must be non-empty")

    log = Path(log_path).resolve()
    log.parent.mkdir(parents=True, exist_ok=True)
    sample = _ConsoleSample(
        limit=console_line_limit, tail_lines=console_tail_lines,
        line_chars=console_line_chars, console=console)
    decoder = _BoundedLineDecoder(sample.add, max_pending=console_line_chars)
    actual_run_id = run_id or _new_run_id()
    started_at = _utc_now()
    started = time.monotonic()
    _write(console, f"[{stage_id}] START run={actual_run_id} "
           f"work_class={work_class} timeout={timeout_s:g}s log={log}")

    proc: subprocess.Popen[bytes] | None = None
    output_bytes = 0
    cancelled = timed_out = False
    launch_error: str | None = None
    reader_errors: list[str] = []

    # Exclusive creation protects earlier lossless evidence from accidental
    # run-id reuse.  It also gives the reader thread one stable binary sink.
    with log.open("xb") as log_file:
        try:
            proc = subprocess.Popen(
                argv,
                cwd=str(cwd) if cwd is not None else None,
                env=dict(env) if env is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                start_new_session=True,
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

            while proc.poll() is None or not reader_done:
                now = time.monotonic()
                if reader_errors and not cancelled and not timed_out:
                    _write(console, f"[{stage_id}] ERROR {reader_errors[0]}; "
                           "terminating process group")
                    _terminate_group(proc, terminate_grace_s)
                elif (cancel_event is not None and cancel_event.is_set()
                        and not cancelled):
                    cancelled = True
                    _write(console, f"[{stage_id}] CANCEL elapsed={now-started:.3f}s "
                           f"pid={proc.pid}; terminating process group")
                    _terminate_group(proc, terminate_grace_s)
                elif now - started >= timeout_s and not timed_out:
                    timed_out = True
                    _write(console, f"[{stage_id}] TIMEOUT elapsed={now-started:.3f}s "
                           f"limit={timeout_s:g}s pid={proc.pid}; "
                           "terminating process group")
                    _terminate_group(proc, terminate_grace_s)

                wait_s = max(0.005, min(0.1, next_heartbeat - now))
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

                now = time.monotonic()
                if proc.poll() is None and now >= next_heartbeat:
                    remaining = max(0.0, timeout_s - (now - started))
                    _write(console, f"[{stage_id}] HEARTBEAT "
                           f"work_class={work_class} elapsed={now-started:.3f}s "
                           f"remaining={remaining:.3f}s pid={proc.pid}")
                    next_heartbeat = now + heartbeat_s

            if reader is not None:
                reader.join(timeout=terminate_grace_s)

    decoder.finish()
    suppressed = sample.finish(stage_id)
    finished_at = _utc_now()
    elapsed_s = time.monotonic() - started

    if launch_error is not None or reader_errors:
        status = "ERROR"
        returncode = None if proc is None else proc.poll()
        findings = tuple(
            item for item in ([launch_error] + reader_errors) if item is not None)
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
    )
    _write(console, f"[{stage_id}] {status} rc={returncode} "
           f"elapsed={elapsed_s:.3f}s output={output_bytes}B "
           f"lines={sample.total} suppressed={suppressed} log={log}")
    return outcome
