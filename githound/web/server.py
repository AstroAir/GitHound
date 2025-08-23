#!/usr/bin/env python3
"""
GitHound Web Server

A simple server script to run the GitHound web interface.
"""

import sys
from pathlib import Path

import typer
import uvicorn

# Add the parent directory to the path so we can import githound
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

app = typer.Typer()


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
    log_level: str = typer.Option("info", "--log-level", "-l", help="Log level"),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of worker processes"),
) -> None:
    """
    Start the GitHound web server.

    This will start a FastAPI server with the GitHound web interface,
    providing both a REST API and a web-based GUI for Git history searching.

    Examples:

    \b
    # Start server on default port (8000)
    python -m githound.web.server serve

    \b
    # Start with auto-reload for development
    python -m githound.web.server serve --reload

    \b
    # Start on custom host and port
    python -m githound.web.server serve --host 127.0.0.1 --port 8080

    \b
    # Start with multiple workers for production
    python -m githound.web.server serve --workers 4
    """

    print("🐕 Starting GitHound Web Server...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Workers: {workers}")
    print(f"   Reload: {reload}")
    print(f"   Log Level: {log_level}")
    print()
    print("Available endpoints:")
    print(f"   Web Interface: http://{host}:{port}/")
    print(f"   API Docs: http://{host}:{port}/api/docs")
    print(f"   Health Check: http://{host}:{port}/health")
    print()
    print("Press Ctrl+C to stop the server")
    print()

    try:
        uvicorn.run(
            "githound.web.api:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            workers=workers if not reload else 1,  # Can't use workers with reload
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n👋 GitHound server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


@app.command()
def dev() -> None:
    """
    Start the development server with auto-reload and debug logging.

    This is equivalent to:
    serve --reload --log-level debug --host 127.0.0.1
    """
    print("🚀 Starting GitHound Development Server...")
    serve(host="127.0.0.1", port=8000, reload=True, log_level="debug", workers=1)


@app.command()
def prod(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    workers: int = typer.Option(4, "--workers", "-w", help="Number of worker processes"),
) -> None:
    """
    Start the production server with optimized settings.

    This configures the server for production use with:
    - Multiple workers
    - Info-level logging
    - No auto-reload
    """
    print("🏭 Starting GitHound Production Server...")
    serve(host=host, port=port, reload=False, log_level="info", workers=workers)


@app.command()
def health(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Server host"),
    port: int = typer.Option(8000, "--port", "-p", help="Server port"),
) -> None:
    """
    Check if the GitHound server is running and healthy.
    """
    import requests

    try:
        response = requests.get(f"http://{host}:{port}/health", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print("✅ GitHound server is healthy!")
            print(f"   Status: {data['status']}")
            print(f"   Version: {data['version']}")
            print(f"   Uptime: {data['uptime_seconds']:.1f} seconds")
            print(f"   Active Searches: {data['active_searches']}")
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            sys.exit(1)

    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to server at {host}:{port}")
        print("   Make sure the server is running.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"❌ Server at {host}:{port} did not respond within 5 seconds")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
