#!/usr/bin/env python3
"""Bounded, streaming subprocess execution for PCB pipeline stages.

This module is deliberately a library, not another workflow engine.  It gives
the existing drivers three properties that ``subprocess.run`` does not:

* output is relayed while the child is running;
* a quiet child still produces a periodic heartbeat;
* timeout/cancellation terminates the whole process group, not only the shell
  or Python parent that happened to be launched first.

``run_bounded`` returns a small result object and can atomically publish a JSON
state file under ``06_build``.  Exit 124 means timeout and 125 cancellation.
"""
from __future__ import annotations

import json
import os
import queue
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


EXIT_TIMEOUT = 124
EXIT_CANCELLED = 125


@dataclass(frozen=True)
class RunResult:
    returncode: int
    output: str
    elapsed_s: float
    timed_out: bool = False
    cancelled: bool = False


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temp, path)


def _terminate_group(proc: subprocess.Popen, grace_s: float = 2.0) -> None:
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=grace_s)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_bounded(
        command: Sequence[str], *, cwd: str | Path | None = None,
        env: Mapping[str, str] | None = None, timeout_s: float | None = None,
        heartbeat_s: float = 10.0, label: str = "stage",
        state_path: str | Path | None = None,
        cancel_event: threading.Event | None = None,
        echo: bool = True) -> RunResult:
    """Run ``command`` with streamed output, heartbeat and a hard deadline."""
    if timeout_s is not None and timeout_s <= 0:
        raise ValueError("timeout_s must be positive")
    if heartbeat_s <= 0:
        raise ValueError("heartbeat_s must be positive")
    argv = [str(x) for x in command]
    started_wall = time.time()
    started = time.monotonic()
    state = Path(state_path) if state_path else None
    base = {
        "schema": 1, "label": label, "command": argv,
        "pid": None, "status": "starting", "started_at": started_wall,
        "timeout_s": timeout_s, "heartbeat_s": heartbeat_s,
    }
    if state:
        _atomic_json(state, base)

    proc = subprocess.Popen(
        argv, cwd=str(cwd) if cwd is not None else None,
        env=dict(env) if env is not None else None,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        start_new_session=True)
    base.update({"pid": proc.pid, "status": "running"})
    if state:
        _atomic_json(state, base)

    chunks: queue.Queue[bytes | None] = queue.Queue()

    def read_output() -> None:
        assert proc.stdout is not None
        try:
            while True:
                # read1 relays whatever is available; read(4096) may wait for
                # its entire request and make a chatty child look silent.
                data = proc.stdout.read1(4096)
                if not data:
                    break
                chunks.put(data)
        finally:
            chunks.put(None)

    reader = threading.Thread(target=read_output,
                              name=f"{label}-output", daemon=True)
    reader.start()
    output: list[str] = []
    reader_done = False
    next_heartbeat = started + heartbeat_s
    timed_out = cancelled = False

    while proc.poll() is None or not reader_done:
        now = time.monotonic()
        if cancel_event is not None and cancel_event.is_set() and proc.poll() is None:
            cancelled = True
            print(f"[{label}] CANCEL: terminating process group {proc.pid}",
                  flush=True)
            _terminate_group(proc)
        elif timeout_s is not None and now - started >= timeout_s \
                and proc.poll() is None:
            timed_out = True
            print(f"[{label}] TIMEOUT after {now - started:.1f}s "
                  f"(limit {timeout_s:g}s): terminating process group {proc.pid}",
                  flush=True)
            _terminate_group(proc)

        wait = max(0.01, min(0.25, next_heartbeat - now))
        try:
            item = chunks.get(timeout=wait)
        except queue.Empty:
            item = b""
        if item is None:
            reader_done = True
        elif item:
            text = item.decode("utf-8", errors="replace")
            output.append(text)
            if echo:
                sys.stdout.write(text)
                sys.stdout.flush()

        now = time.monotonic()
        if proc.poll() is None and now >= next_heartbeat:
            elapsed = now - started
            print(f"[{label}] heartbeat: running {elapsed:.1f}s "
                  f"(pid {proc.pid})", flush=True)
            if state:
                live = dict(base)
                live.update({"heartbeat_at": time.time(),
                             "elapsed_s": round(elapsed, 3)})
                _atomic_json(state, live)
            next_heartbeat = now + heartbeat_s

    raw_rc = proc.wait()
    elapsed = time.monotonic() - started
    rc = EXIT_TIMEOUT if timed_out else EXIT_CANCELLED if cancelled else raw_rc
    if state:
        done = dict(base)
        done.update({
            "status": "timed_out" if timed_out else
                      "cancelled" if cancelled else "finished",
            "finished_at": time.time(), "elapsed_s": round(elapsed, 3),
            "returncode": rc,
        })
        _atomic_json(state, done)
    return RunResult(rc, "".join(output), elapsed, timed_out, cancelled)
