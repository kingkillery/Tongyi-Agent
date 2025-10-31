"""
Sandboxed Python Execution (Docker/cgroups isolation with subprocess fallback)
---------------------------------------------------------------------------
Goals:
- Run untrusted Python snippets with:
  - wall-clock timeout (default 60s)
  - stdout/stderr capture with size caps
  - deterministic RNG seeding
  - containerized isolation (Docker) with resource caps and no-network
  - audit logging

Fallback:
- If Docker is unavailable, falls back to controlled subprocess execution.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
import logging
import uuid
from dataclasses import dataclass
from typing import Dict, Optional

DEFAULT_TIMEOUT_S = 60
STDIO_LIMIT = 64 * 1024  # 64 KB each
DOCKER_IMAGE = "python:3.13-slim"
MEMORY_LIMIT = "256m"
CPU_LIMIT = "0.5"  # half a core

# Configure audit logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


@dataclass
class ExecResult:
    ok: bool
    stdout: str
    stderr: str
    returncode: int
    duration_ms: int
    container_id: Optional[str] = None  # Docker container ID if used
    isolated: bool = False  # True if Docker isolation was used


def _docker_available() -> bool:
    """Check if Docker daemon is available."""
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True, timeout=5)
        subprocess.run(["docker", "info"], check=True, capture_output=True, timeout=5)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _run_in_docker(code: str, input_json: Optional[Dict] = None, timeout_s: int = DEFAULT_TIMEOUT_S, seed: int = 1337, base_dir: Optional[str] = None) -> ExecResult:
    """Execute code inside a Docker container with resource caps and no-network."""
    harness = (
        "import json, os, random, sys, time\n"
        f"random.seed({seed})\n"
        "try:\n"
        "    __input = json.loads(os.environ.get('SANDBOX_INPUT','{}'))\n"
        "except Exception:\n"
        "    __input = {}\n"
        "start = time.time()\n"
        "try:\n"
    ) + textwrap.indent(code, "    ") + (
        "\nexcept Exception as e:\n"
        "    import traceback\n"
        "    traceback.print_exc()\n"
        "finally:\n"
        "    pass\n"
    )
    # Determine base directory to mount read-only; default to current working dir
    mount_src = base_dir or os.getcwd()
    with tempfile.TemporaryDirectory() as td:
        script_path = os.path.join(td, "snippet.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(harness)
        # Generate a unique container name for audit
        container_name = f"sandbox_{uuid.uuid4().hex[:8]}"
        start = time.time()
        try:
            # Pull image if not present (suppress output)
            subprocess.run(["docker", "pull", DOCKER_IMAGE], check=True, capture_output=True, timeout=30)
            cmd = [
                "docker", "run", "--rm",
                "--name", container_name,
                "--network", "none",  # no network
                "--memory", MEMORY_LIMIT,
                "--cpus", CPU_LIMIT,
                "--read-only",
                "--tmpfs", "/tmp:noexec,nosuid,size=100m",
                # Mount base directory read-only at /workspace
                "-v", f"{mount_src}:/workspace:ro",
                # Mount script read-only at /snippet.py
                "-v", f"{script_path}:/snippet.py:ro",
                "-e", "SANDBOX_INPUT=" + json.dumps(input_json or {}),
                "-e", "PYTHONPATH=/workspace",
                DOCKER_IMAGE,
                "python", "-u", "/snippet.py"
            ]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)
            stdout, stderr = proc.communicate(timeout=timeout_s)
            duration = int((time.time() - start) * 1000)
            logger.info("Docker sandbox completed: container=%s ok=%s rc=%s ms=%s", container_name, proc.returncode == 0, proc.returncode, duration)
            return ExecResult(
                ok=proc.returncode == 0,
                stdout=stdout[:STDIO_LIMIT].decode(errors="ignore"),
                stderr=stderr[:STDIO_LIMIT].decode(errors="ignore"),
                returncode=proc.returncode,
                duration_ms=duration,
                container_id=container_name,
                isolated=True
            )
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", container_name], capture_output=True)
            stdout, stderr = proc.communicate()
            duration = int((time.time() - start) * 1000)
            logger.warning("Docker sandbox timed out: container=%s ms=%s", container_name, duration)
            return ExecResult(
                False,
                stdout[:STDIO_LIMIT].decode(errors="ignore"),
                stderr[:STDIO_LIMIT].decode(errors="ignore"),
                -9,
                duration,
                container_id=container_name,
                isolated=True
            )
        except Exception as exc:
            duration = int((time.time() - start) * 1000)
            logger.error("Docker sandbox error: container=%s exc=%s", container_name, exc)
            return ExecResult(
                False,
                "",
                str(exc)[:STDIO_LIMIT],
                -1,
                duration,
                container_id=container_name,
                isolated=True
            )


def run_snippet(code: str, input_json: Optional[Dict] = None, timeout_s: int = DEFAULT_TIMEOUT_S, seed: int = 1337, base_dir: Optional[str] = None) -> ExecResult:
    """Execute code in Docker if available; otherwise subprocess with minimal harness."""
    if _docker_available():
        logger.info("Using Docker sandbox isolation (seed=%s, timeout=%s, base_dir=%s)", seed, timeout_s, base_dir)
        try:
            return _run_in_docker(code, input_json, timeout_s, seed, base_dir)
        except Exception as exc:
            logger.warning("Docker isolation failed, falling back to subprocess: %s", exc)
            return _run_subprocess(code, input_json, timeout_s, seed)
    else:
        logger.info("Docker unavailable; using subprocess sandbox (seed=%s, timeout=%s)", seed, timeout_s)
        return _run_subprocess(code, input_json, timeout_s, seed)


def _run_subprocess(code: str, input_json: Optional[Dict] = None, timeout_s: int = DEFAULT_TIMEOUT_S, seed: int = 1337) -> ExecResult:
    """Execute code in a subprocess with a minimal harness (fallback)."""
    harness_header = (
        "import json, os, random, sys, time\n"
        f"random.seed({seed})\n"
        "try:\n"
        "    __input = json.loads(os.environ.get('SANDBOX_INPUT','{}'))\n"
        "except Exception:\n"
        "    __input = {}\n"
        "start = time.time()\n"
        "stdout_capture = []\n"
        "stderr_capture = []\n"
        "try:\n"
    )
    harness_footer = (
        "\nexcept Exception as e:\n"
        "    import traceback\n"
        "    traceback.print_exc()\n"
        "finally:\n"
        "    pass\n"
    )
    harness = harness_header + textwrap.indent(code, '    ') + harness_footer
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "snippet.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(harness)
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "UTF-8"
        env["SANDBOX_INPUT"] = json.dumps(input_json or {})
        start = time.time()
        try:
            proc = subprocess.Popen(
                [sys.executable, "-u", path],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=td,
                text=False,
            )
            stdout, stderr = proc.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            duration = int((time.time() - start) * 1000)
            logger.warning("Subprocess sandbox timed out (seed=%s, ms=%s)", seed, duration)
            return ExecResult(False, stdout[:STDIO_LIMIT].decode(errors="ignore"), stderr[:STDIO_LIMIT].decode(errors="ignore"), -9, duration, container_id=None, isolated=False)
        duration = int((time.time() - start) * 1000)
        logger.info("Subprocess sandbox completed: ok=%s rc=%s ms=%s", proc.returncode == 0, proc.returncode, duration)
        return ExecResult(proc.returncode == 0, stdout[:STDIO_LIMIT].decode(errors="ignore"), stderr[:STDIO_LIMIT].decode(errors="ignore"), proc.returncode, duration, container_id=None, isolated=False)


if __name__ == "__main__":
    demo = "print('hello from sandbox'); import random; print(random.randint(1,3))"
    res = run_snippet(demo)
    print(json.dumps({"ok": res.ok, "rc": res.returncode, "stdout": res.stdout, "stderr": res.stderr, "ms": res.duration_ms}, indent=2))
