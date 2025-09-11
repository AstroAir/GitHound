#!/usr/bin/env python3
"""
GitHound Services Manager

This script manages GitHound services (web server, MCP server) with cross-platform
support, health checks, and service monitoring.

Usage:
    python scripts/services.py [command] [options]

Commands:
    start       - Start services
    stop        - Stop services
    restart     - Restart services
    status      - Check service status
    logs        - View service logs
    health      - Health check for services
"""

from utils import (
    check_port_available,
    console,
    get_free_port,
    get_project_root,
    print_error,
    print_header,
    print_info,
    print_section,
    print_step,
    print_success,
    print_warning,
    run_command_with_output,
    StatusContext,
    confirm,
    is_windows,
)
import json
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optionalnal, Tuple

import typer
import requests
from rich.live import Live
from rich.table import Table

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))


app = typer.Typer(
    name="services",
    help="GitHound Services Manager",
    add_completion=False,
)


class ServiceManager:
    """Manages GitHound services."""

    def __init__(self) -> None:
        self.project_root = get_project_root()
        self.services_config = {  # [attr-defined]
            "web": {
                "name": "Web Server",
                "default_port": 8000,
                "health_endpoint": "/health",
                "command": ["python", "-m", "githound.web.server", "serve"],
                "log_file": "logs/web-server.log",
            },
            "mcp": {
                "name": "MCP Server",
                "default_port": 3000,
                "health_endpoint": None,  # MCP doesn't have HTTP health endpoint
                "command": ["python", "-m", "githound.mcp_server"],
                "log_file": "logs/mcp-server.log",
            }
        }
        self.pid_dir = self.project_root / ".pids"
        self.log_dir = self.project_root / "logs"

        # Ensure directories exist
        self.pid_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

    def get_service_pid_file(self, service: str) -> Path:
        """Get PID file path for service."""
        return self.pid_dir / f"{service}.pid"

    def get_service_log_file(self, service: str) -> Path:
        """Get log file path for service."""
        log_file = self.services_config[service]["log_file"]  # [attr-defined]
        return self.project_root / log_file

    def is_service_running(self, service: str) -> Tuple[bool, Optional[int]]:
        """Check if service is running and return PID if found."""
        pid_file = self.get_service_pid_file(service)

        if not pid_file.exists():
            return False, None

        try:
            pid = int(pid_file.read_text().strip())

            # Check if process is actually running
            if is_windows():
                # Windows process check
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}"],
                    capture_output=True,
                    text=True
                )
                if str(pid) in result.stdout:
                    return True, pid
            else:
                # Unix process check
                try:
                    import os
                    os.kill(pid, 0)  # Signal 0 just checks if process exists
                    return True, pid
                except OSError:
                    pass

            # Process not running, clean up stale PID file
            pid_file.unlink(missing_ok=True)
            return False, None

        except (ValueError, FileNotFoundError):
            return False, None

    def start_service(
        self,
        service: str,
        port: Optional[int] = None,
        host: str = "localhost",
        background: bool = True
    ) -> bool:
        """Start a service."""
        if service not in self.services_config:  # [attr-defined]
            print_error(f"Unknown service: {service}")
            return False

        config = self.services_config[service]  # [attr-defined]

        # Check if already running
        running, pid = self.is_service_running(service)
        if running:
            print_warning(f"{config['name']} is already running (PID: {pid})")
            return True

        # Determine port
        if port is None:
            port = config["default_port"]

        if not check_port_available(port, host):
            print_error(f"Port {port} is not available")
            # Try to find alternative port
            alt_port = get_free_port(port + 1)
            if alt_port and confirm(f"Use port {alt_port} instead?"):
                port = alt_port
            else:
                return False

        # Prepare command
        command = config["command"].copy()
        if service == "web":
            command.extend(["--host", host, "--port", str(port)])
        elif service == "mcp":
            command.extend(["--port", str(port)])

        # Start service
        log_file = self.get_service_log_file(service)
        pid_file = self.get_service_pid_file(service)

        try:
            with StatusContext(f"Starting {config['name']}"):
                if background:
                    # Start in background
                    with open(log_file, "w") as log:
                        process = subprocess.Popen(
                            command,
                            cwd=self.project_root,
                            stdout=log,
                            stderr=subprocess.STDOUT,
                            start_new_session=True
                        )

                    # Save PID
                    pid_file.write_text(str(process.pid))

                    # Wait a moment to check if it started successfully
                    time.sleep(2)
                    if process.poll() is not None:
                        print_error(f"{config['name']} failed to start")
                        return False
                else:
                    # Start in foreground
                    process = subprocess.run(command, cwd=self.project_root)
                    return process.returncode = = 0

            print_success(f"{config['name']} started on {host}:{port}")
            print_info(f"PID: {process.pid}")
            print_info(f"Logs: {log_file}")

            return True

        except Exception as e:
            print_error(f"Failed to start {config['name']}: {e}")
            return False

    def stop_service(self, service: str, force: bool = False) -> bool:
        """Stop a service."""
        if service not in self.services_config:  # [attr-defined]
            print_error(f"Unknown service: {service}")
            return False

        config = self.services_config[service]  # [attr-defined]
        running, pid = self.is_service_running(service)

        if not running:
            print_info(f"{config['name']} is not running")
            return True

        try:
            with StatusContext(f"Stopping {config['name']}"):
                if is_windows():
                    # Windows process termination
                    if force:
                        subprocess.run(
                            ["taskkill", "/F", "/PID", str(pid)], check=True)
                    else:
                        subprocess.run(
                            ["taskkill", "/PID", str(pid)], check=True)
                else:
                    # Unix process termination
                    import os
                    if force:
                        os.kill(pid, signal.SIGKILL)
                    else:
                        os.kill(pid, signal.SIGTERM)

                        # Wait for graceful shutdown
                        for _ in range(10):
                            time.sleep(0.5)
                            if not self.is_service_running(service)[0]:
                                break
                        else:
                            # Force kill if still running
                            try:
                                os.kill(pid, signal.SIGKILL)
                            except OSError:
                                pass

            # Clean up PID file
            self.get_service_pid_file(service).unlink(missing_ok=True)

            print_success(f"{config['name']} stopped")
            return True

        except Exception as e:
            print_error(f"Failed to stop {config['name']}: {e}")
            return False

    def get_service_status(self, service: str) -> Dict:
        """Get detailed service status."""
        if service not in self.services_config:  # [attr-defined]
            return {"error": f"Unknown service: {service}"}

        config = self.services_config[service]  # [attr-defined]
        running, pid = self.is_service_running(service)

        status = {
            "name": config["name"],
            "service": service,
            "running": running,
            "pid": pid,
            "port": config["default_port"],
            "log_file": str(self.get_service_log_file(service)),
        }

        if running and config["health_endpoint"]:
            # Check HTTP health endpoint
            try:
                url = f"http://localhost:{config['default_port']}{config['health_endpoint']}"
                response = requests.get(url, timeout=5)
                status["health"] = "healthy" if response.status_code = = 200 else "unhealthy"
                status["health_details"] = response.json() if response.headers.get(
                    "content-type", "").startswith("application/json") else response.text
            except Exception as e:
                status["health"] = "unhealthy"
                status["health_details"] = str(e)

        return status

    def health_check(self, service: Optional[str] = None) -> Dict:
        """Perform health check on services."""
        if service:
            services = [service] if service in self.services_config else []  # [attr-defined]
        else:
            services = list(self.services_config.keys())  # [attr-defined]

        results: dict[str, Any] = {}
        for svc in services:
            results[svc] = self.get_service_status(svc)

        return results


@app.command()
def start(
    service: str = typer.Argument(...,
                                  help="Service to start (web, mcp, or all)"),
    port: Optional[int] = typer.Option(
        None, "--port", "-p", help="Port to use"),
    host: str = typer.Option("localhost", "--host",
                             "-h", help="Host to bind to"),
    foreground: bool = typer.Option(
        False, "--foreground", "-f", help="Run in foreground"),
) -> None:
    """Start GitHound services."""
    manager = ServiceManager()

    if service == "all":
        services = list(manager.services_config.keys())  # [attr-defined]
    else:
        services = [service]

    success = True
    for svc in services:
        if svc not in manager.services_config:  # [attr-defined]
            print_error(f"Unknown service: {svc}")
            success = False
            continue

        svc_success = manager.start_service(
            svc,
            port=port,
            host=host,
            background=not foreground
        )
        success = success and svc_success

    sys.exit(0 if success else 1)


@app.command()
def stop(
    service: str = typer.Argument(...,
                                  help="Service to stop (web, mcp, or all)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force stop"),
) -> None:
    """Stop GitHound services."""
    manager = ServiceManager()

    if service == "all":
        services = list(manager.services_config.keys())  # [attr-defined]
    else:
        services = [service]

    success = True
    for svc in services:
        if svc not in manager.services_config:  # [attr-defined]
            print_error(f"Unknown service: {svc}")
            success = False
            continue

        svc_success = manager.stop_service(svc, force=force)
        success = success and svc_success

    sys.exit(0 if success else 1)


@app.command()
def restart(
    service: str = typer.Argument(...,
                                  help="Service to restart (web, mcp, or all)"),
    port: Optional[int] = typer.Option(
        None, "--port", "-p", help="Port to use"),
    host: str = typer.Option("localhost", "--host",
                             "-h", help="Host to bind to"),
) -> None:
    """Restart GitHound services."""
    manager = ServiceManager()

    if service == "all":
        services = list(manager.services_config.keys())  # [attr-defined]
    else:
        services = [service]

    success = True
    for svc in services:
        if svc not in manager.services_config:  # [attr-defined]
            print_error(f"Unknown service: {svc}")
            success = False
            continue

        # Stop first
        manager.stop_service(svc)
        time.sleep(1)  # Brief pause

        # Then start
        svc_success = manager.start_service(svc, port=port, host=host)
        success = success and svc_success

    sys.exit(0 if success else 1)


@app.command()
def status(
    service: Optional[str] = typer.Argument(
        None, help="Service to check (web, mcp, or all)"),
    watch: bool = typer.Option(
        False, "--watch", "-w", help="Watch status continuously"),
) -> None:
    """Check service status."""
    manager = ServiceManager()

    def create_status_table() -> None:
        table = Table(title="GitHound Services Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("PID", style="yellow")
        table.add_column("Port", style="blue")
        table.add_column("Health", style="magenta")

        health_results = manager.health_check(service)

        for svc, status_info in health_results.items():
            status_text = "🟢 Running" if status_info["running"] else "🔴 Stopped"
            pid_text = str(status_info["pid"]) if status_info["pid"] else "-"
            port_text = str(status_info["port"])
            health_text = status_info.get("health", "N/A")

            table.add_row(
                status_info["name"],
                status_text,
                pid_text,
                port_text,
                health_text
            )

        return table

    if watch:
        with Live(create_status_table(), refresh_per_second=1) as live:
            try:
                while True:
                    time.sleep(1)
                    live.update(create_status_table())
            except KeyboardInterrupt:
                print_info("Status monitoring stopped")
    else:
        console.print(create_status_table())


@app.command()
def logs(
    service: str = typer.Argument(...,
                                  help="Service to show logs for (web or mcp)"),
    follow: bool = typer.Option(
        False, "--follow", "-f", help="Follow log output"),
    lines: int = typer.Option(
        50, "--lines", "-n", help="Number of lines to show"),
) -> None:
    """View service logs."""
    manager = ServiceManager()

    if service not in manager.services_config:  # [attr-defined]
        print_error(f"Unknown service: {service}")
        sys.exit(1)

    log_file = manager.get_service_log_file(service)

    if not log_file.exists():
        print_warning(f"Log file does not exist: {log_file}")
        return

    if follow:
        # Follow logs (tail -f equivalent)
        try:
            with open(log_file, 'r') as f:
                # Go to end of file
                f.seek(0, 2)

                print_info(f"Following logs for {service} (Ctrl+C to stop)")
                while True:
                    line = f.readline()
                    if line:
                        print(line.rstrip())
                    else:
                        time.sleep(0.1)
        except KeyboardInterrupt:
            print_info("Log following stopped")
    else:
        # Show last N lines
        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(
                    all_lines) > lines else all_lines

                for line in recent_lines:
                    print(line.rstrip())
        except Exception as e:
            print_error(f"Failed to read log file: {e}")


@app.command()
def health(
    service: Optional[str] = typer.Argument(
        None, help="Service to check (web, mcp, or all)"),
) -> None:
    """Perform health check on services."""
    manager = ServiceManager()

    print_header("GitHound Services Health Check")

    health_results = manager.health_check(service)

    all_healthy = True
    for svc, status_info in health_results.items():
        print_section(f"{status_info['name']} ({svc})")

        if status_info["running"]:
            print_step("Service running", "success")
            print_info(f"PID: {status_info['pid']}")

            if "health" in status_info:
                if status_info["health"] == "healthy":
                    print_step("Health check", "success")
                else:
                    print_step("Health check", "error")
                    all_healthy = False
                    if "health_details" in status_info:
                        print_error(
                            f"Details: {status_info['health_details']}")
        else:
            print_step("Service running", "error")
            all_healthy = False

    if all_healthy:
        print_success("All services are healthy! ✨")
    else:
        print_warning("Some services have issues")
        sys.exit(1)


if __name__ == "__main__":
    app()
