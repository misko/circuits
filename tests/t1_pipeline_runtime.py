#!/usr/bin/env python3
"""Focused tests for declarative pipeline runtime and telemetry."""
from __future__ import annotations

import io
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, contains, eq, main, test, tmpdir  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RUNTIME_SCRIPTS = ROOT / "skills" / "pcb-design" / "scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))
from pipeline_runtime import (EXIT_TIMEOUT, RuntimeOutcome, run_stage)  # noqa: E402
from pipeline_contract import StageResult, StageSpec  # noqa: E402


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
