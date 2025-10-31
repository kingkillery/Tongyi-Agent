import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.sandbox_exec import run_snippet, _docker_available, ExecResult  # noqa: E402


def test_sandbox_subprocess_fallback():
    # Force subprocess fallback by mocking Docker unavailable
    with patch('src.sandbox_exec._docker_available', return_value=False):
        res = run_snippet("print('hello')", seed=42)
        assert res.ok
        assert 'hello' in res.stdout
        assert not res.isolated
        assert res.container_id is None
        assert res.duration_ms >= 0


def test_sandbox_deterministic_seed():
    # With a fixed seed, random output should be deterministic
    code = "import random; print(random.randint(1, 1000))"
    with patch('src.sandbox_exec._docker_available', return_value=False):
        res1 = run_snippet(code, seed=123)
        res2 = run_snippet(code, seed=123)
        assert res1.stdout.strip() == res2.stdout.strip()


def test_sandbox_timeout_enforcement():
    # A long-running snippet should be terminated and return failure
    slow_code = "import time; time.sleep(10); print('should not appear')"
    with patch('src.sandbox_exec._docker_available', return_value=False):
        res = run_snippet(slow_code, timeout_s=2)
        assert not res.ok
        assert res.returncode == -9
        assert 'should not appear' not in res.stdout


def test_sandbox_stdio_caps():
    # Excessive output should be truncated to STDIO_LIMIT
    long_output = "x" * 130_000  # Much larger than 64 KB limit
    code = f"print({repr(long_output)})"
    with patch('src.sandbox_exec._docker_available', return_value=False):
        res = run_snippet(code)
        assert len(res.stdout) <= 64 * 1024


def test_docker_isolation_when_available():
    # Mock Docker available and simulate successful container run
    mock_result = ExecResult(
        ok=True,
        stdout="docker output",
        stderr="",
        returncode=0,
        duration_ms=150,
        container_id="sandbox_abc123",
        isolated=True
    )
    with patch('src.sandbox_exec._docker_available', return_value=True), \
         patch('src.sandbox_exec._run_in_docker', return_value=mock_result) as mock_docker:
        res = run_snippet("print('test')")
        assert res.isolated
        assert res.container_id == "sandbox_abc123"
        mock_docker.assert_called_once()


def test_docker_resource_caps_and_no_network():
    # Verify Docker command includes resource caps and no-network flags
    with patch('src.sandbox_exec._docker_available', return_value=True), \
         patch('src.sandbox_exec.subprocess.run') as mock_pull, \
         patch('src.sandbox_exec.subprocess.Popen') as mock_popen, \
         patch('src.sandbox_exec.uuid.uuid4') as mock_uuid:
        mock_uuid.return_value.hex = "deadbeef12345678"
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (b"ok\n", b"")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc
        mock_pull.return_value = MagicMock(returncode=0)

        run_snippet("print('test')", timeout_s=30)
        # Check that docker run was called with isolation flags
        args, kwargs = mock_popen.call_args
        cmd = args[0]
        assert "--network" in cmd and "none" in cmd
        assert "--memory" in cmd and "256m" in cmd
        assert "--cpus" in cmd and "0.5" in cmd
        assert "--read-only" in cmd


def test_audit_logging_output():
    # Ensure audit logging is configured and execution does not raise
    with patch('src.sandbox_exec._docker_available', return_value=False):
        # If logging wasn't configured, this would raise; success means audit path works
        res = run_snippet("print('audit test')", seed=99, timeout_s=10)
        assert res.ok
        assert 'audit test' in res.stdout
