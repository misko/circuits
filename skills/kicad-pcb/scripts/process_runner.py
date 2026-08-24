#!/usr/bin/env python3
"""Compatibility adapter for the PCB pipeline's bounded process runtime.

``pipeline_runtime`` is the sole owner of subprocess launch, output draining,
deadline enforcement, and process-group termination.  This module preserves
the small legacy ``RunResult`` API and state-file shape used by KiCad scripts.
Nested calls remain inside an enclosing runtime's kill scope while retaining
their own subtree deadline. Nested execution is Linux-only until an equivalent
portable descendant-discovery primitive exists. It does not provide hermetic
or network isolation.
"""
from __future__ import annotations

import json
import math
import os
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence, TextIO


PCB_DESIGN_SCRIPTS = (Path(__file__).resolve().parents[2] /
                      "pcb-design" / "scripts")
if str(PCB_DESIGN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PCB_DESIGN_SCRIPTS))

from pipeline_runtime import (  # noqa: E402
    EXIT_CANCELLED, EXIT_TIMEOUT, RuntimeOutcome, run_stage,
)


# Historical callers could omit ``timeout_s``.  Keep that call shape while
# ensuring the low-level authority still receives a finite safety ceiling.
# Repository-owned callers all declare materially shorter stage deadlines.
LEGACY_SAFETY_TIMEOUT_S = 24 * 60 * 60


@dataclass(frozen=True)
class RunResult:
    returncode: int
    output: str
    elapsed_s: float
    timed_out: bool = False
    cancelled: bool = False


def _json_temp(path: Path, value: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(
        f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return temp


def _atomic_json(path: Path, value: dict) -> None:
    temp = _json_temp(path, value)
    try:
        os.replace(temp, path)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def _atomic_live_json(path: Path, value: dict, *,
                      commit: Callable[[Path, Path], bool]) -> bool:
    """Prepare live bytes, then let the caller atomically admit the replace."""
    temp = _json_temp(path, value)
    try:
        return commit(temp, path)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


class _LegacyConsole:
    """Adapt runtime console records to the legacy ``echo`` behavior."""

    def __init__(self, label: str, echo: bool,
                 stream: TextIO | None = None) -> None:
        self._prefix = f"[{label}] "
        self._echo = echo
        self._stream = sys.stdout if stream is None else stream

    def write(self, text: str) -> int:
        for line in text.splitlines(keepends=True):
            tail = line[len(self._prefix):] if line.startswith(self._prefix) else ""
            live_telemetry = tail.startswith((
                "HEARTBEAT ", "TIMEOUT ", "CANCEL ", "ERROR "))
            runtime_summary = tail.startswith((
                "START ", "CLEANUP ", "PASS ", "FAIL ", "TIMED_OUT ",
                "INCOMPLETE "))
            if live_telemetry or (self._echo and not runtime_summary):
                self._stream.write(line)
        return len(text)

    def flush(self) -> None:
        self._stream.flush()


def _adapter_spec(label: str, timeout_s: float) -> dict[str, object]:
    return {"id": label, "work_class": "local", "timeout_s": timeout_s}


def run_bounded(
        command: Sequence[str], *, cwd: str | Path | None = None,
        env: Mapping[str, str] | None = None, timeout_s: float | None = None,
        heartbeat_s: float = 10.0, label: str = "stage",
        state_path: str | Path | None = None,
        cancel_event: threading.Event | None = None,
        echo: bool = True) -> RunResult:
    """Run through ``pipeline_runtime`` and adapt its result for old callers."""
    if timeout_s is not None and (
            not math.isfinite(float(timeout_s)) or float(timeout_s) <= 0):
        raise ValueError("timeout_s must be positive and finite")
    if not math.isfinite(float(heartbeat_s)) or float(heartbeat_s) <= 0:
        raise ValueError("heartbeat_s must be positive and finite")
    argv = [str(item) for item in command]
    if not argv:
        raise ValueError("command must not be empty")

    declared_timeout = None if timeout_s is None else float(timeout_s)
    effective_timeout = (LEGACY_SAFETY_TIMEOUT_S if declared_timeout is None
                         else declared_timeout)
    actual_cwd = Path.cwd().resolve() if cwd is None else Path(cwd).resolve()
    # This freezes legacy inheritance explicitly; it is not an environment
    # allowlist and does not imply network isolation.
    actual_env = dict(os.environ) if env is None else dict(env)
    started_wall = time.time()
    state = Path(state_path) if state_path else None
    base = {
        "schema": 1, "label": label, "command": argv,
        "pid": None, "status": "starting", "started_at": started_wall,
        "timeout_s": declared_timeout, "heartbeat_s": float(heartbeat_s),
    }
    if state:
        _atomic_json(state, base)

    # Event delivery is asynchronous so it cannot block the watchdog.  A live
    # callback may therefore already be preparing filesystem bytes when the
    # runtime publishes the terminal record.  Live writers prepare a unique
    # temp outside the lock, then check the latch and replace while holding the
    # short commit lock.  A late callback can never replace terminal bytes,
    # and the watchdog never waits for its potentially blocking preparation.
    state_guard = threading.Lock()
    terminal_state: dict | None = None

    def commit_live(temp: Path, target: Path) -> bool:
        with state_guard:
            if terminal_state is not None:
                return False
            os.replace(temp, target)
            return True

    def observe(event: Mapping[str, object]) -> None:
        if state is None:
            return
        with state_guard:
            if terminal_state is not None:
                return
            if event["event"] == "running":
                base.update({"pid": event["pid"], "status": "running"})
                live = dict(base)
            elif event["event"] == "heartbeat":
                live = dict(base)
                live.update({"heartbeat_at": time.time(),
                             "elapsed_s": round(
                                 float(event["elapsed_s"]), 3)})
            else:
                return
        _atomic_live_json(state, live, commit=commit_live)

    console: TextIO = _LegacyConsole(label, echo)
    with tempfile.TemporaryDirectory(prefix="pcb-process-runner-") as directory:
        log_path = Path(directory) / "run.log"
        outcome: RuntimeOutcome = run_stage(
            _adapter_spec(label, effective_timeout), argv, log_path=log_path,
            cwd=actual_cwd, env=actual_env, heartbeat_s=float(heartbeat_s),
            console=console, cancel_event=cancel_event,
            event_sink=observe,
            # The legacy runner relayed all lines.  Keep a finite but generous
            # compatibility budget while the authoritative log remains exact.
            console_line_limit=100_000, console_tail_lines=0,
            console_line_chars=1_000_000)
        output = log_path.read_bytes().decode("utf-8", errors="replace")

    rc = outcome.returncode
    if rc is None:
        rc = 1
    if outcome.status == "ERROR" and rc == 0:
        # The group leader may have returned zero while leaving a live
        # descendant or while runtime bookkeeping failed.  Legacy callers see
        # only this integer, so preserving zero would launder a runtime error
        # into success.
        rc = 1
    timed_out = outcome.status == "TIMED_OUT"
    cancelled = outcome.status == "INCOMPLETE" and rc == EXIT_CANCELLED
    if state:
        with state_guard:
            done = dict(base)
            done.update({
                "pid": outcome.pid,
                "status": "timed_out" if timed_out else
                          "cancelled" if cancelled else
                          "error" if outcome.status == "ERROR" else "finished",
                "finished_at": time.time(),
                "elapsed_s": round(outcome.elapsed_s, 3),
                "returncode": rc,
            })
            terminal_state = dict(done)
        _atomic_json(state, done)
    return RunResult(rc, output, outcome.elapsed_s, timed_out, cancelled)


__all__ = ["EXIT_CANCELLED", "EXIT_TIMEOUT", "RunResult", "run_bounded"]
