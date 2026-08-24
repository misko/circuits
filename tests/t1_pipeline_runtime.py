#!/usr/bin/env python3
"""Focused tests for declarative pipeline runtime and telemetry."""
from __future__ import annotations

import io
import hashlib
import json
import os
import signal
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, contains, eq, main, test, tmpdir  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RUNTIME_SCRIPTS = ROOT / "skills" / "pcb-design" / "scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))
import pipeline_runtime as pipeline_runtime_module  # noqa: E402
from pipeline_runtime import (  # noqa: E402
    EXIT_TIMEOUT, RuntimeOutcome, execute_attempt, run_stage,
)
from pipeline_contract import StageResult, StageSpec  # noqa: E402
from pipeline_execution import TaskEnvelope  # noqa: E402
from pipeline_identity import TypedIdentityInput, subject_identity  # noqa: E402

KICAD_SCRIPTS = ROOT / "skills" / "kicad-pcb" / "scripts"
sys.path.insert(0, str(KICAD_SCRIPTS))
import process_runner as process_runner_module  # noqa: E402
from process_runner import run_bounded  # noqa: E402


@dataclass(frozen=True)
class Spec:
    id: str = "P-RUNTIME"
    work_class: str = "local"
    timeout_s: float = 2.0


def execute(code: str, *, spec: Spec | None = None, **kwargs):
    directory = tmpdir("pipeline_runtime_")
    console = io.StringIO()
    result = run_stage(
        spec or Spec(), [sys.executable, "-c", code],
        log_path=directory / "run.log", console=console,
        heartbeat_s=kwargs.pop("heartbeat_s", 0.05), **kwargs)
    return result, console.getvalue(), directory


def assert_pid_gone(pid: int, detail: str) -> None:
    for _ in range(40):
        stat_path = Path(f"/proc/{pid}/stat")
        if not stat_path.exists() or stat_path.read_text().split()[2] == "Z":
            return
        time.sleep(0.025)
    raise AssertionError(f"{detail}: process {pid} survived")


def attempt_envelope(root: Path, *, owned=("allowed.txt",), packet=True,
                     deadline_s=2.0, output_path="06_build/attempt.json"):
    input_packet = []
    if packet:
        source = root / "input.txt"
        data = source.read_bytes()
        input_packet = [{
            "name": "source", "path": "input.txt",
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
        }]
    subject = subject_identity("runtime-attempt", 1, [TypedIdentityInput(
        "fixture", "mapping", {"stage": "P-RUNTIME"},
        b"stage: P-RUNTIME\n")])
    deadline = (datetime.now(timezone.utc) + timedelta(seconds=deadline_s))
    deadline_at = deadline.isoformat(timespec="microseconds").replace(
        "+00:00", "Z")
    writer_scope = ({"mode": "READ_ONLY", "paths": []} if not owned else
                    {"mode": "EXCLUSIVE", "paths": list(sorted(owned))})
    return TaskEnvelope(
        task_id="runtime-attempt", stage_id="P-RUNTIME", run_id="run-1",
        subject=subject, executor="subprocess", execution_class="local",
        recommended_agent_role=None, agent_role=None,
        role_escalation_reason=None, context_mode="NOT_APPLICABLE",
        input_handoff_id=None, input_packet=input_packet,
        deadline_at=deadline_at, max_nonimproving_attempts=1,
        replacement_limit=0, writer_scope=writer_scope,
        output_path=output_path)


@test("runtime returns PASS telemetry and a schema-1 StageResult projection")
def t_clean():
    result, console, directory = execute(
        "print('clean output', flush=True)", outputs=("runtime_report",))
    check(isinstance(result, RuntimeOutcome), "typed runtime result")
    eq(result.status, "PASS", "runtime status")
    eq(result.returncode, 0, "return code")
    eq(result.work_timing.work_class, "local", "work class")
    eq(result.log_path, (directory / "run.log").resolve(), "lossless log path")
    eq(result.log_path.read_bytes(), b"clean output\n", "lossless log bytes")
    eq(result.outputs, ("runtime_report",), "accepted output symbols")
    contains(console, "[P-RUNTIME] START", "start telemetry")
    contains(console, "[P-RUNTIME] PASS", "finish telemetry")

    captured = {}

    def factory(**fields):
        captured.update(fields)
        return fields

    stage = result.to_stage_result(
        Spec(), {"semantic_sha256": "a" * 64, "raw_sha256": "b" * 64},
        result_factory=factory)
    eq(stage["stage_id"], "P-RUNTIME", "stage projection id")
    eq(stage["status"], "PASS", "stage projection status")
    eq(stage["applicability"], "APPLIES", "stage applicability")
    eq(stage["applicability_reason"], None, "applies reason")
    eq((stage["graded"], stage["total"]), (1, 1), "stage denominator")
    eq(stage["schema"], 1, "stage result schema")
    json.dumps(result.to_mapping())

    real_spec = StageSpec(
        id="P-RUNTIME", owner="pcb-design", lifecycle="schematic",
        cost="cheap", work_class="local", timeout_s=2,
        produces=("runtime_report",), requires=(), blocks=(), invalidated_by=())
    real_result = result.to_stage_result(
        real_spec,
        {"semantic_sha256": "a" * 64, "raw_sha256": "b" * 64})
    check(isinstance(real_result, StageResult), "public StageResult integration")
    eq(real_result.to_mapping()["status"], "PASS", "serialized result status")


@test("quiet runtime emits heartbeats with deadline and work-class context")
def t_quiet_heartbeat():
    result, console, _ = execute(
        "import time; time.sleep(.18)", heartbeat_s=0.04)
    eq(result.status, "PASS", "quiet child status")
    contains(console, "HEARTBEAT work_class=local", "quiet heartbeat")
    contains(console, "remaining=", "deadline remaining")
    check(result.elapsed_s >= 0.15, "measured quiet work duration")


@test("chatty runtime bounds console while retaining exact combined output")
def t_chatty_bounded():
    code = (
        "import sys\n"
        "for i in range(250):\n"
        " print(f'out-{i:03}', flush=True)\n"
        " print(f'err-{i:03}', file=sys.stderr, flush=True)\n")
    result, console, _ = execute(
        code, console_line_limit=12, console_tail_lines=4)
    eq(result.status, "PASS", "chatty child status")
    expected = "".join(
        f"out-{i:03}\nerr-{i:03}\n" for i in range(250)).encode()
    eq(result.log_path.read_bytes(), expected, "complete ordered combined log")
    eq(result.output_lines, 500, "complete output line count")
    eq(result.console_child_lines, 12, "interactive child-line budget")
    eq(result.suppressed_child_lines, 488, "suppressed child lines")
    contains(console, "488 child output lines omitted", "suppression summary")
    contains(console, "out-000", "head retained")
    contains(console, "err-249", "tail retained")
    child_lines = [line for line in console.splitlines()
                   if line.startswith("out-") or line.startswith("err-")]
    eq(len(child_lines), 12, "bounded interactive child output")


@test("CRLF output is counted as one line while raw bytes stay unchanged")
def t_crlf():
    result, console, _ = execute(
        "import os; os.write(1, b'one\\r\\ntwo\\r\\n')")
    eq(result.status, "PASS", "CRLF child status")
    eq(result.log_path.read_bytes(), b"one\r\ntwo\r\n", "raw CRLF log")
    eq(result.output_lines, 2, "CRLF logical line count")
    eq([line for line in console.splitlines() if line in {"one", "two"}],
       ["one", "two"], "CRLF console records")


@test("runtime timeout kills a spawned grandchild process group",
      kind="known_bad")
def t_timeout_group():
    directory = tmpdir("pipeline_timeout_")
    child_pid = directory / "grandchild.pid"
    code = (
        "import pathlib,subprocess,sys,time\n"
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])\n"
        "pathlib.Path(sys.argv[1]).write_text(str(p.pid))\n"
        "print('grandchild',p.pid,flush=True)\n"
        "time.sleep(60)\n")
    console = io.StringIO()
    result = run_stage(
        Spec(timeout_s=0.25),
        [sys.executable, "-c", code, str(child_pid)],
        log_path=directory / "run.log", console=console, heartbeat_s=0.05,
        terminate_grace_s=0.5)
    eq(result.status, "TIMED_OUT", "timeout status")
    eq(result.returncode, EXIT_TIMEOUT, "timeout return code")
    check(result.elapsed_s < 2, f"execution was not bounded: {result.elapsed_s}")
    contains(console.getvalue(), "TIMEOUT", "visible timeout")
    pid = int(child_pid.read_text())
    for _ in range(30):
        stat = Path(f"/proc/{pid}/stat")
        if not stat.exists() or stat.read_text().split()[2] == "Z":
            break
        time.sleep(0.05)
    else:
        raise AssertionError(f"grandchild {pid} survived process-group timeout")


@test("outer deadline kills nested leaf despite sanitized inner env",
      kind="known_bad")
def t_nested_outer_timeout_kills_leaf():
    directory = tmpdir("pipeline_nested_outer_")
    leaf_pid = directory / "leaf.pid"
    middle = (
        "import sys\n"
        "sys.path.insert(0,sys.argv[1])\n"
        "from process_runner import run_bounded\n"
        "leaf=(\"import pathlib,sys,time;\"\n"
        "      \"pathlib.Path(sys.argv[1]).write_text(str(__import__('os').getpid()));\"\n"
        "      \"time.sleep(60)\")\n"
        "run_bounded([sys.executable,'-c',leaf,sys.argv[2]],env={},"
        "timeout_s=60,heartbeat_s=.05,label='inner',echo=False)\n")
    started = time.monotonic()
    result = run_stage(
        Spec(timeout_s=0.5),
        [sys.executable, "-c", middle, str(KICAD_SCRIPTS), str(leaf_pid)],
        log_path=directory / "outer.log", console=io.StringIO(),
        heartbeat_s=0.05, terminate_grace_s=0.15)
    wall = time.monotonic() - started
    eq(result.status, "TIMED_OUT", "outer nested timeout status")
    check(wall < 1.5, f"nested outer deadline returned after {wall:.3f}s")
    check(leaf_pid.is_file(), "nested leaf never reached its PID fixture")
    assert_pid_gone(int(leaf_pid.read_text()),
                    "outer deadline missed nested bounded leaf")


@test("inner nested timeout kills only its leaf and preserves its caller",
      kind="known_bad")
def t_nested_inner_timeout_preserves_outer():
    directory = tmpdir("pipeline_nested_inner_")
    leaf_pid = directory / "leaf.pid"
    middle_done = directory / "middle.done"
    middle = (
        "import pathlib,sys\n"
        "sys.path.insert(0,sys.argv[1])\n"
        "from process_runner import run_bounded\n"
        "leaf=(\"import pathlib,sys,time,os;\"\n"
        "      \"pathlib.Path(sys.argv[1]).write_text(str(os.getpid()));\"\n"
        "      \"time.sleep(60)\")\n"
        "result=run_bounded([sys.executable,'-c',leaf,sys.argv[2]],"
        "timeout_s=.15,heartbeat_s=.04,label='inner',echo=False)\n"
        "pathlib.Path(sys.argv[3]).write_text(str(result.returncode))\n")
    result = run_stage(
        Spec(timeout_s=2),
        [sys.executable, "-c", middle, str(KICAD_SCRIPTS), str(leaf_pid),
         str(middle_done)],
        log_path=directory / "outer.log", console=io.StringIO(),
        heartbeat_s=0.05, terminate_grace_s=0.15)
    eq(result.status, "PASS", "outer caller survived inner timeout")
    eq(middle_done.read_text(), str(EXIT_TIMEOUT), "inner timeout result")
    assert_pid_gone(int(leaf_pid.read_text()),
                    "inner timeout missed its own nested leaf")


@test("nested successful leader cannot launder a DEVNULL leaf",
      kind="known_bad")
def t_nested_success_cleans_devnull_leaf():
    directory = tmpdir("pipeline_nested_success_")
    leaf_pid = directory / "leaf.pid"
    middle_done = directory / "middle.done"
    middle = (
        "import pathlib,sys\n"
        "sys.path.insert(0,sys.argv[1])\n"
        "from process_runner import run_bounded\n"
        "inner=\"import pathlib,subprocess,sys; "
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'], "
        "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); "
        "pathlib.Path(sys.argv[1]).write_text(str(p.pid))\"\n"
        "result=run_bounded([sys.executable,'-c',inner,sys.argv[2]],"
        "timeout_s=2,heartbeat_s=.05,label='inner',echo=False)\n"
        "pathlib.Path(sys.argv[3]).write_text(str(result.returncode))\n")
    result = run_stage(
        Spec(timeout_s=3),
        [sys.executable, "-c", middle, str(KICAD_SCRIPTS), str(leaf_pid),
         str(middle_done)],
        log_path=directory / "outer.log", console=io.StringIO(),
        heartbeat_s=0.05, terminate_grace_s=0.15)
    eq(result.status, "PASS", "outer caller after nested cleanup")
    check(int(middle_done.read_text()) != 0,
          "nested runtime laundered live descendant into exit zero")
    assert_pid_gone(int(leaf_pid.read_text()),
                    "nested success cleanup missed DEVNULL leaf")


@test("spoofed nested marker cannot disable descendant cleanup",
      kind="known_bad")
def t_spoofed_scope_marker_is_safe():
    directory = tmpdir("pipeline_spoofed_scope_")
    leaf_pid = directory / "leaf.pid"
    code = (
        "import pathlib,subprocess,sys\n"
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],"
        "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
        "pathlib.Path(sys.argv[1]).write_text(str(p.pid))\n")
    spoofed_env = dict(os.environ)
    spoofed_env["_PCB_PIPELINE_RUNTIME_SCOPE"] = "subgroup-v1"
    result = run_stage(
        Spec(timeout_s=2),
        [sys.executable, "-c", code, str(leaf_pid)],
        log_path=directory / "run.log", console=io.StringIO(),
        env=spoofed_env, heartbeat_s=0.05, terminate_grace_s=0.15)
    eq(result.status, "ERROR", "spoofed marker survivor status")
    assert_pid_gone(int(leaf_pid.read_text()),
                    "spoofed marker disabled descendant cleanup")


@test("nested runtime refuses a host without process-table discovery",
      kind="known_bad")
def t_nested_without_proc_is_refused_before_launch():
    directory = tmpdir("pipeline_nested_no_proc_")
    marker = directory / "launched"
    original_scope = pipeline_runtime_module._inherited_runtime_scope
    original_discovery = \
        pipeline_runtime_module._nested_group_discovery_available
    pipeline_runtime_module._inherited_runtime_scope = lambda: True
    pipeline_runtime_module._nested_group_discovery_available = lambda: False
    try:
        try:
            run_stage(
                Spec(), [sys.executable, "-c",
                         "open(__import__('sys').argv[1],'w').write('bad')",
                         str(marker)],
                log_path=directory / "run.log", console=io.StringIO())
        except RuntimeError as exc:
            contains(str(exc), "requires Linux /proc",
                     "non-Linux nested refusal diagnosis")
        else:
            raise AssertionError("nested stage launched without discovery")
    finally:
        pipeline_runtime_module._inherited_runtime_scope = original_scope
        pipeline_runtime_module._nested_group_discovery_available = \
            original_discovery
    check(not marker.exists(), "unsupported nested command was launched")


@test("blocking event sink cannot stall watchdog or launder telemetry",
      kind="known_bad")
def t_blocking_event_sink_is_bounded_error():
    directory = tmpdir("pipeline_blocked_event_")
    release = threading.Event()
    entered = threading.Event()

    def blocked_event(_event):
        entered.set()
        release.wait(30)

    started = time.monotonic()
    try:
        result = run_stage(
            Spec(timeout_s=0.1),
            [sys.executable, "-c", "import time;time.sleep(60)"],
            log_path=directory / "run.log", console=io.StringIO(),
            event_sink=blocked_event, heartbeat_s=0.02,
            terminate_grace_s=0.05)
    finally:
        release.set()
    wall = time.monotonic() - started
    check(entered.is_set(), "blocking event sink fixture never ran")
    eq(result.status, "ERROR", "blocking event sink status")
    check(wall < 0.5, f"event sink held watchdog for {wall:.3f}s")
    contains("; ".join(result.findings), "event sink did not drain",
             "blocking event sink diagnosis")


@test("observer exception becomes typed ERROR rather than escaping",
      kind="known_bad")
def t_event_sink_exception_is_typed_error():
    directory = tmpdir("pipeline_broken_event_")

    def broken_event(_event):
        raise RuntimeError("fixture observer broke")

    result = run_stage(
        Spec(timeout_s=2),
        [sys.executable, "-c", "import time;time.sleep(.2)"],
        log_path=directory / "run.log", console=io.StringIO(),
        event_sink=broken_event, heartbeat_s=0.02,
        terminate_grace_s=0.05)
    eq(result.status, "ERROR", "observer exception status")
    contains("; ".join(result.findings),
             "event sink failed: RuntimeError: fixture observer broke",
             "observer exception diagnosis")


@test("blocking console cannot stall watchdog or launder telemetry",
      kind="known_bad")
def t_blocking_console_is_bounded_error():
    directory = tmpdir("pipeline_blocked_console_")
    release = threading.Event()
    entered = threading.Event()

    class BlockedConsole:
        def write(self, text):
            entered.set()
            release.wait(30)
            return len(text)

        def flush(self):
            return None

    started = time.monotonic()
    try:
        result = run_stage(
            Spec(timeout_s=0.1),
            [sys.executable, "-c", "import time;time.sleep(60)"],
            log_path=directory / "run.log", console=BlockedConsole(),
            heartbeat_s=0.02, terminate_grace_s=0.05)
    finally:
        release.set()
    wall = time.monotonic() - started
    check(entered.is_set(), "blocking console fixture never ran")
    eq(result.status, "ERROR", "blocking console status")
    check(wall < 0.5, f"console held watchdog for {wall:.3f}s")
    contains("; ".join(result.findings), "console observer did not drain",
             "blocking console diagnosis")


@test("deadline also kills a pipe-holding grandchild after its parent exits",
      kind="known_bad")
def t_timeout_after_parent_exit():
    directory = tmpdir("pipeline_orphan_timeout_")
    child_pid = directory / "grandchild.pid"
    code = (
        "import pathlib,subprocess,sys\n"
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])\n"
        "pathlib.Path(sys.argv[1]).write_text(str(p.pid))\n"
        "print('leader exiting',flush=True)\n")
    console = io.StringIO()
    result = run_stage(
        Spec(timeout_s=0.25),
        [sys.executable, "-c", code, str(child_pid)],
        log_path=directory / "run.log", console=console, heartbeat_s=0.05,
        terminate_grace_s=0.2)
    eq(result.status, "TIMED_OUT", "orphaned session timeout status")
    pid = int(child_pid.read_text())
    for _ in range(30):
        stat = Path(f"/proc/{pid}/stat")
        if not stat.exists() or stat.read_text().split()[2] == "Z":
            break
        time.sleep(0.05)
    else:
        raise AssertionError(f"pipe-holding grandchild {pid} survived deadline")


@test("leader exit with a DEVNULL descendant is cleaned and rejected",
      kind="known_bad")
def t_success_cleans_devnull_descendant():
    directory = tmpdir("pipeline_devnull_descendant_")
    child_pid = directory / "grandchild.pid"
    code = (
        "import pathlib,subprocess,sys\n"
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],"
        "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
        "pathlib.Path(sys.argv[1]).write_text(str(p.pid))\n"
        "print('leader completed',flush=True)\n")
    console = io.StringIO()
    result = run_stage(
        Spec(timeout_s=2),
        [sys.executable, "-c", code, str(child_pid)],
        log_path=directory / "run.log", console=console, heartbeat_s=0.05,
        terminate_grace_s=0.2)
    eq(result.status, "ERROR", "leader exit status after descendant cleanup")
    eq(result.returncode, 0, "leader return code")
    eq(result.log_path.read_bytes(), b"leader completed\n",
       "leader output preservation")
    contains(console.getvalue(), "CLEANUP leader_rc=0",
             "successful descendant cleanup telemetry")
    pid = int(child_pid.read_text())
    for _ in range(30):
        stat_path = Path(f"/proc/{pid}/stat")
        if not stat_path.exists() or stat_path.read_text().split()[2] == "Z":
            break
        time.sleep(0.05)
    else:
        raise AssertionError(
            f"DEVNULL grandchild {pid} survived successful leader exit")


@test("legacy runner cannot launder a cleaned descendant into exit zero",
      kind="known_bad")
def t_compat_devnull_descendant_is_nonzero():
    directory = tmpdir("compat_devnull_descendant_")
    child_pid = directory / "grandchild.pid"
    code = (
        "import pathlib,subprocess,sys\n"
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],"
        "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
        "pathlib.Path(sys.argv[1]).write_text(str(p.pid))\n"
        "print('leader completed',flush=True)\n")
    result = run_bounded(
        [sys.executable, "-c", code, str(child_pid)], cwd=directory,
        timeout_s=2, heartbeat_s=0.05, label="compat-devnull", echo=False)
    check(result.returncode != 0, "runtime ERROR was adapted back to exit zero")
    check(not result.timed_out, "cleanup error was mislabeled as timeout")
    eq(result.output, "leader completed\n", "leader output preservation")


@test("runtime enforces deadline after a live child closes its output pipes",
      kind="known_bad")
def t_timeout_closed_pipe():
    result, console, _ = execute(
        "import os,time; os.close(1); os.close(2); time.sleep(60)",
        spec=Spec(timeout_s=0.25), terminate_grace_s=0.2)
    eq(result.status, "TIMED_OUT", "closed-pipe timeout status")
    eq(result.returncode, EXIT_TIMEOUT, "closed-pipe timeout code")
    check(result.elapsed_s < 2, f"closed-pipe child escaped deadline: "
          f"{result.elapsed_s}")
    contains(console, "TIMEOUT", "closed-pipe timeout telemetry")


@test("escaped-session pipe cannot hold runtime past deadline and grace",
      kind="known_bad")
def t_escaped_session_pipe_is_bounded():
    directory = tmpdir("pipeline_escaped_session_")
    child_pid = directory / "escaped.pid"
    code = (
        "import pathlib,subprocess,sys\n"
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],"
        "start_new_session=True)\n"
        "pathlib.Path(sys.argv[1]).write_text(str(p.pid))\n")
    started = time.monotonic()
    result = run_stage(
        Spec(timeout_s=0.05),
        [sys.executable, "-c", code, str(child_pid)],
        log_path=directory / "run.log", console=io.StringIO(),
        heartbeat_s=0.02, terminate_grace_s=0.05)
    wall = time.monotonic() - started
    eq(result.status, "ERROR", "escaped-session transport status")
    check(wall < 0.5, f"escaped output pipe blocked runtime for {wall:.3f}s")
    contains("; ".join(result.findings), "escaped the process group",
             "escaped-session diagnosis")
    pid = int(child_pid.read_text())
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


@test("attempt deadline cleans up a descendant after its leader exits",
      kind="known_bad")
def t_attempt_descendant_cleanup():
    root = tmpdir("attempt_orphan_timeout_")
    child_pid = root / "child.pid"
    envelope = attempt_envelope(
        root, owned=("child.pid",), packet=False, deadline_s=0.3)
    code = (
        "import pathlib,subprocess,sys\n"
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])\n"
        "pathlib.Path('child.pid').write_text(str(p.pid))\n"
        "print('leader exited',flush=True)\n")
    started = time.monotonic()
    attempt = execute_attempt(
        envelope, [sys.executable, "-c", code], cwd=root,
        env=dict(os.environ), console=io.StringIO(), heartbeat_s=0.05,
        terminate_grace_s=0.2)
    eq(attempt.status, "TIMED_OUT", "attempt timeout status")
    check(time.monotonic() - started < 2,
          "pipe-holding descendant escaped the finite deadline")
    pid = int(child_pid.read_text())
    for _ in range(30):
        stat_path = Path(f"/proc/{pid}/stat")
        if not stat_path.exists() or stat_path.read_text().split()[2] == "Z":
            break
        time.sleep(0.05)
    else:
        raise AssertionError(f"attempt descendant {pid} survived timeout")


@test("legacy runner shim cannot reintroduce the descendant-stdout hang",
      kind="known_bad")
def t_legacy_shim_descendant_cleanup():
    root = tmpdir("legacy_shim_orphan_")
    child_pid = root / "child.pid"
    code = (
        "import pathlib,subprocess,sys\n"
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])\n"
        "pathlib.Path(sys.argv[1]).write_text(str(p.pid))\n"
        "print('shim leader exited',flush=True)\n")
    result = run_bounded(
        [sys.executable, "-c", code, str(child_pid)], cwd=root,
        env=dict(os.environ), timeout_s=0.3, heartbeat_s=0.05,
        label="compat-descendant", state_path=root / "state.json", echo=False)
    eq(result.returncode, EXIT_TIMEOUT, "shim timeout return code")
    check(result.timed_out and result.elapsed_s < 2,
          "compatibility shim did not remain bounded")
    contains(result.output, "shim leader exited", "shim retained output")
    state = json.loads((root / "state.json").read_text())
    eq(state["status"], "timed_out", "shim terminal state")
    check(isinstance(state["pid"], int), "shim discarded process identity")
    pid = int(child_pid.read_text())
    for _ in range(30):
        stat_path = Path(f"/proc/{pid}/stat")
        if not stat_path.exists() or stat_path.read_text().split()[2] == "Z":
            break
        time.sleep(0.05)
    else:
        raise AssertionError(f"shim descendant {pid} survived timeout")


@test("legacy runner shim preserves running PID and heartbeat state")
def t_legacy_shim_live_state():
    root = tmpdir("legacy_shim_state_")
    state_path = root / "state.json"
    outcome = {}

    def run_quiet_child():
        try:
            outcome["result"] = run_bounded(
                [sys.executable, "-c", "import time; time.sleep(.25)"],
                cwd=root, env=dict(os.environ), timeout_s=2,
                heartbeat_s=0.04, label="compat-live",
                state_path=state_path, echo=False)
        except Exception as exc:  # surfaced with the main test traceback
            outcome["error"] = exc

    worker = threading.Thread(target=run_quiet_child, daemon=True)
    worker.start()
    live = None
    observation_deadline = time.monotonic() + 1.5
    while time.monotonic() < observation_deadline:
        if state_path.is_file():
            try:
                candidate = json.loads(state_path.read_text())
            except json.JSONDecodeError:
                candidate = {}
            if (candidate.get("status") == "running" and
                    "heartbeat_at" in candidate):
                live = candidate
                break
        time.sleep(0.01)
    worker.join(timeout=3)
    check(not worker.is_alive(), "legacy shim worker did not finish")
    if "error" in outcome:
        raise outcome["error"]
    check(live is not None, "no live heartbeat state was published")
    check(isinstance(live["pid"], int) and live["elapsed_s"] > 0,
          "live state omitted PID or elapsed time")
    eq(outcome["result"].returncode, 0, "quiet shim return code")
    final = json.loads(state_path.read_text())
    eq(final["status"], "finished", "shim final state")
    eq(final["pid"], live["pid"], "stable process identity")


@test("late async live callback cannot overwrite terminal runner state",
      kind="known_bad")
def t_legacy_state_terminal_latch():
    root = tmpdir("legacy_shim_terminal_latch_")
    state_path = root / "state.json"
    entered = threading.Event()
    release = threading.Event()
    late_write_done = threading.Event()
    original_live = process_runner_module._atomic_live_json
    blocked_once = False

    def delayed_live(path, value, *, commit):
        nonlocal blocked_once
        is_delayed_live = value.get("status") == "running" and not blocked_once
        if is_delayed_live:
            blocked_once = True
            entered.set()
            release.wait(30)
        try:
            return original_live(path, value, commit=commit)
        finally:
            if is_delayed_live:
                late_write_done.set()

    process_runner_module._atomic_live_json = delayed_live
    try:
        result = run_bounded(
            [sys.executable, "-c", "import time;time.sleep(.1)"],
            cwd=root, env=dict(os.environ), timeout_s=2,
            heartbeat_s=0.02, label="compat-terminal-latch",
            state_path=state_path, echo=False)
        check(entered.is_set(), "delayed live callback fixture never ran")
        check(result.returncode != 0,
              "blocked telemetry did not produce a runtime error")
        terminal = json.loads(state_path.read_text())
        eq(terminal["status"], "error", "terminal state before late callback")
        release.set()
        check(late_write_done.wait(1), "late live write never resumed")
        terminal = json.loads(state_path.read_text())
        eq(terminal["status"], "error", "state after late live callback")
        check("finished_at" in terminal and "returncode" in terminal,
              "late callback stripped terminal fields")
    finally:
        release.set()
        process_runner_module._atomic_live_json = original_live


@test("attempt refuses stale packet bytes before and after execution",
      kind="known_bad")
def t_attempt_stale_input():
    before_root = tmpdir("attempt_stale_before_")
    (before_root / "input.txt").write_text("adopted\n")
    before = attempt_envelope(before_root, owned=("allowed.txt",))
    (before_root / "input.txt").write_text("changed before launch\n")
    refused = execute_attempt(
        before,
        [sys.executable, "-c", "open('allowed.txt','w').write('ran')"],
        cwd=before_root, env=dict(os.environ), console=io.StringIO())
    eq(refused.status, "ERROR", "pre-launch stale status")
    check(not (before_root / "allowed.txt").exists(),
          "stale packet command was launched")
    eq(refused.output["input_packet"]["before"]["status"], "FAIL",
       "pre-launch packet receipt")

    after_root = tmpdir("attempt_stale_after_")
    (after_root / "input.txt").write_text("adopted\n")
    after = attempt_envelope(after_root, owned=("input.txt",))
    moved = execute_attempt(
        after,
        [sys.executable, "-c",
         "open('input.txt','w').write('changed during execution\\n')"],
        cwd=after_root, env=dict(os.environ), console=io.StringIO())
    eq(moved.status, "ERROR", "post-execution stale status")
    eq(moved.output["input_packet"]["before"]["status"], "PASS",
       "initial packet receipt")
    eq(moved.output["input_packet"]["after"]["status"], "FAIL",
       "post-execution packet receipt")


@test("attempt records and rejects writer-scope escapes", kind="known_bad")
def t_attempt_writer_escape():
    root = tmpdir("attempt_writer_escape_")
    envelope = attempt_envelope(
        root, owned=("allowed.txt",), packet=False)
    escaped = execute_attempt(
        envelope,
        [sys.executable, "-c", "open('foreign.txt','w').write('escape')"],
        cwd=root, env=dict(os.environ), console=io.StringIO())
    eq(escaped.status, "ERROR", "writer escape terminal status")
    receipt = escaped.output["writer_scope"]
    eq(receipt["status"], "FAIL", "writer receipt verdict")
    eq(receipt["violations"], ["foreign.txt"], "escaped path receipt")

    symlink_root = tmpdir("attempt_writer_symlink_")
    outside = tmpdir("attempt_writer_outside_")
    (symlink_root / "owned").symlink_to(outside, target_is_directory=True)
    symlink_envelope = attempt_envelope(
        symlink_root, owned=("owned/result.txt",), packet=False)
    refused = execute_attempt(
        symlink_envelope,
        [sys.executable, "-c", "open('owned/result.txt','w').write('escape')"],
        cwd=symlink_root, env=dict(os.environ), console=io.StringIO())
    eq(refused.status, "ERROR", "symlink scope escape status")
    check(not (outside / "result.txt").exists(),
          "writer-scope symlink escape was launched")
    check(refused.output["writer_scope"]["resolution_failures"],
          "symlink escape lacks a resolution failure receipt")


@test("attempt output admits exactly one terminal record", kind="known_bad")
def t_attempt_terminal_uniqueness():
    root = tmpdir("attempt_terminal_once_")
    envelope = attempt_envelope(root, owned=(), packet=False)
    first = execute_attempt(
        envelope, [sys.executable, "-c", "pass"], cwd=root,
        env=dict(os.environ), console=io.StringIO())
    eq(first.status, "PASS", "first terminal attempt")
    terminal = root / envelope.output_path
    original = terminal.read_bytes()
    eq(json.loads(original), first.to_mapping(), "published terminal mapping")
    try:
        execute_attempt(
            envelope,
            [sys.executable, "-c", "open('ran_twice','w').write('bad')"],
            cwd=root, env=dict(os.environ), console=io.StringIO())
    except FileExistsError as exc:
        check("terminal attempt already exists" in str(exc),
              "duplicate terminal diagnosis")
    else:
        raise AssertionError("a second terminal attempt was admitted")
    eq(terminal.read_bytes(), original, "first terminal record stability")
    check(not (root / "ran_twice").exists(), "duplicate command was launched")


@test("nonzero child exit becomes a failed, nonpassing StageResult",
      kind="known_bad")
def t_exit_failure():
    result, console, _ = execute(
        "import sys; print('specific failure', flush=True); sys.exit(7)",
        outputs=("must_not_publish",))
    eq(result.status, "FAIL", "failed child status")
    eq(result.returncode, 7, "failed child return code")
    eq(result.findings, ("command exited 7",), "failure finding")
    contains(console, "specific failure", "failure output")

    def factory(**fields):
        return fields

    stage = result.to_stage_result(Spec(), object(), result_factory=factory)
    eq((stage["graded"], stage["total"]), (0, 1), "failed denominator")
    eq(stage["outputs"], (), "failed stages publish no outputs")


@test("runtime REFUSES an output absent from the StageSpec", kind="known_bad")
def t_undeclared_output():
    directory = tmpdir("pipeline_runtime_output_")
    spec = StageSpec(
        id="P-RUNTIME", owner="pcb-design", lifecycle="schematic",
        cost="cheap", work_class="local", timeout_s=2,
        produces=("declared_report",), requires=(), blocks=(),
        invalidated_by=())
    try:
        run_stage(
            spec, [sys.executable, "-c", "pass"],
            log_path=directory / "run.log", outputs=("other_report",))
    except ValueError as exc:
        check("not declared" in str(exc), "undeclared-output diagnosis")
    else:
        raise AssertionError("runtime accepted an output absent from StageSpec")


if __name__ == "__main__":
    raise SystemExit(main())
