"""
Test server management for GitHound web tests.
"""

import os
import subprocess
import time
from pathlib import Path

import requests


class TestServerManager:
    """Manages the test server lifecycle."""

    def __init__(self, test_data_dir: Path):
        self.test_data_dir = test_data_dir
        self.server_process: subprocess.Popen[bytes] | None = None
        self.base_url = "http://localhost:8000"
        self.startup_timeout = 30

    def start(self) -> None:
        """Start the test server."""
        if self.is_running():
            return

        # Set test environment variables
        env = os.environ.copy()
        env.update(
            {
                "TESTING": "true",
                "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
                "REDIS_URL": "redis://localhost:6379/15",
                "GITHOUND_LOG_LEVEL": "WARNING",
                "TEST_DATA_DIR": str(self.test_data_dir),
            }
        )

        # Start the server
        self.server_process = subprocess.Popen(
            ["python", "-m", "githound.web.main"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to start
        self._wait_for_server()

    def stop(self) -> None:
        """Stop the test server."""
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.server_process.wait()
            self.server_process = None

    def is_running(self) -> bool:
        """Check if the server is running."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def _wait_for_server(self) -> None:
        """Wait for the server to start responding."""
        start_time = time.time()
        while time.time() - start_time < self.startup_timeout:
            if self.is_running():
                return
            time.sleep(0.5)

        # If we get here, the server didn't start
        if self.server_process:
            stdout, stderr = self.server_process.communicate()
            raise RuntimeError(
                f"Server failed to start within {self.startup_timeout} seconds.\n"
                f"STDOUT: {stdout.decode()}\n"
                f"STDERR: {stderr.decode()}"
            )
        else:
            raise RuntimeError("Server process was not started")

    def restart(self) -> None:
        """Restart the test server."""
        self.stop()
        self.start()

    def get_logs(self) -> tuple[str, str]:
        """Get server logs."""
        if self.server_process:
            stdout, stderr = self.server_process.communicate(timeout=1)
            return stdout.decode(), stderr.decode()
        return "", ""
