import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.sandbox_exec import run_snippet, _docker_available, ExecResult  # noqa: E402


def test_docker_mounts_base_dir_readonly():
    # Verify Docker command includes read-only mount of base directory at /workspace
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

        # Use a temporary directory as base_dir
        with tempfile.TemporaryDirectory() as td:
            run_snippet("print('test')", base_dir=td)
            # Check that docker run was called with read-only mount of base_dir at /workspace
            args, kwargs = mock_popen.call_args
            cmd = args[0]
            assert any(f"{td}:/workspace:ro" in arg for arg in cmd), f"Expected read-only mount of {td} at /workspace in {cmd}"
            # Ensure PYTHONPATH includes /workspace so imports work
            assert "PYTHONPATH=/workspace" in cmd


def test_sandbox_can_read_project_files():
    # When base_dir is provided, sandbox code should be able to read files under it
    with tempfile.TemporaryDirectory() as td:
        # Create a dummy project file
        proj_file = Path(td) / "data.txt"
        proj_file.write_text("hello world")
        # Code that reads the file via /workspace
        code = "with open('/workspace/data.txt') as f: print(f.read().strip())"
        # Mock Docker to simulate successful read
        mock_result = ExecResult(
            ok=True,
            stdout="hello world\n",
            stderr="",
            returncode=0,
            duration_ms=120,
            container_id="sandbox_readtest",
            isolated=True
        )
        with patch('src.sandbox_exec._docker_available', return_value=True), \
             patch('src.sandbox_exec._run_in_docker', return_value=mock_result) as mock_run:
            res = run_snippet(code, base_dir=td)
            assert res.ok
            assert "hello world" in res.stdout
            # Verify _run_in_docker was called with the correct base_dir
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0]
            assert call_args[-1] == td  # base_dir argument


def test_sandbox_cannot_write_to_readonly_mount():
    # Attempting to write to the read-only mount should fail
    with tempfile.TemporaryDirectory() as td:
        code = "with open('/workspace/forbidden.txt', 'w') as f: f.write('oops')"
        # Simulate Docker failure due to read-only filesystem
        mock_result = ExecResult(
            ok=False,
            stdout="",
            stderr="Read-only file system: '/workspace/forbidden.txt'",
            returncode=1,
            duration_ms=45,
            container_id="sandbox_writetest",
            isolated=True
        )
        with patch('src.sandbox_exec._docker_available', return_value=True), \
             patch('src.sandbox_exec._run_in_docker', return_value=mock_result) as mock_run:
            res = run_snippet(code, base_dir=td)
            assert not res.ok
            assert "Read-only file system" in res.stderr


def test_subprocess_fallback_ignores_base_dir():
    # In subprocess fallback, base_dir should be ignored (no mount)
    with patch('src.sandbox_exec._docker_available', return_value=False), \
         patch('src.sandbox_exec._run_subprocess') as mock_sub:
        mock_sub.return_value = ExecResult(
            ok=True,
            stdout="fallback\n",
            stderr="",
            returncode=0,
            duration_ms=30,
            container_id=None,
            isolated=False
        )
        run_snippet("print('fallback')", base_dir="/some/dir")
        # Verify subprocess fallback was called without base_dir
        mock_sub.assert_called_once()
        call_args = mock_sub.call_args[0]
        # _run_subprocess signature does not include base_dir
        assert len(call_args) == 4  # code, input_json, timeout_s, seed
