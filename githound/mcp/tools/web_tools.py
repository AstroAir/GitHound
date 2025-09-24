"""Web interface integration MCP tools for GitHound."""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import Context
from git import GitCommandError

from ...git_blame import get_author_statistics
from ...git_handler import get_repository, get_repository_metadata
from ..models import RepositoryInput, WebServerInput


async def start_web_server(input_data: WebServerInput, ctx: Context) -> dict[str, Any]:
    """
    Start the GitHound web interface server.

    Launches the web interface for interactive repository analysis
    with the specified configuration.
    """
    try:
        await ctx.info(f"Starting web server for repository {input_data.repo_path}")

        # Import web server components
        try:
            import threading
            import time

            import uvicorn

            from ...web.api import app  # type: ignore[import-not-found]
        except ImportError as e:
            return {"status": "error", "error": f"Web server dependencies not available: {str(e)}"}

        # Validate repository
        repo = get_repository(Path(input_data.repo_path))

        # Use the existing web app
        web_app = app

        # Start server in background thread
        def run_server() -> None:
            uvicorn.run(web_app, host=input_data.host, port=input_data.port, log_level="info")

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # Give server time to start
        time.sleep(2)

        server_url = f"http://{input_data.host}:{input_data.port}"

        await ctx.info(f"Web server started at {server_url}")

        # Optionally open browser
        if input_data.auto_open:
            try:
                import webbrowser

                webbrowser.open(server_url)
                await ctx.info("Browser opened automatically")
            except Exception as e:
                await ctx.info(f"Could not open browser: {str(e)}")

        return {
            "status": "success",
            "server_url": server_url,
            "host": input_data.host,
            "port": input_data.port,
            "repository_path": input_data.repo_path,
            "auto_opened": input_data.auto_open,
            "start_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error starting web server: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error starting web server: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def generate_repository_report(input_data: RepositoryInput, ctx: Context) -> dict[str, Any]:
    """
    Generate a comprehensive repository analysis report.

    Creates a detailed report including repository statistics, contributor analysis,
    recent activity, and code quality metrics.
    """
    try:
        await ctx.info(f"Generating comprehensive report for {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))

        # Gather comprehensive data
        metadata = get_repository_metadata(repo)
        author_stats = get_author_statistics(repo)

        # Create comprehensive report
        report = {
            "repository_path": input_data.repo_path,
            "generation_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_commits": metadata.get("total_commits", 0),
                "total_contributors": len(metadata.get("contributors", [])),
                "total_branches": len(metadata.get("branches", [])),
                "total_tags": len(metadata.get("tags", [])),
                "total_remotes": len(metadata.get("remotes", [])),
                "active_branch": metadata.get("active_branch"),
                "first_commit_date": metadata.get("first_commit_date"),
                "last_commit_date": metadata.get("last_commit_date"),
            },
            "contributors": author_stats,
            "branches": metadata.get("branches", []),
            "tags": metadata.get("tags", []),
            "remotes": metadata.get("remotes", []),
            # Last 20 commits
            "recent_activity": metadata.get("recent_commits", [])[:20],
        }

        await ctx.info("Repository report generation complete")

        return {
            "status": "success",
            "report": report,
            "generation_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error generating report: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error generating report: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}
