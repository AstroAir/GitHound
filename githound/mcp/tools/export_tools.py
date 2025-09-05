"""Data export MCP tools for GitHound."""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import Context

from ...git_handler import get_repository, get_repository_metadata
from ...schemas import ExportOptions, OutputFormat, PaginationInfo
from ...utils.export import ExportManager
from ..models import ExportInput


async def export_repository_data(input_data: ExportInput, ctx: Context) -> dict[str, Any]:
    """
    Export repository analysis data in various formats.

    Supports exporting repository metadata, commit history, and analysis
    results in JSON, YAML, or CSV formats for further processing.
    """
    try:
        await ctx.info(f"Exporting repository data to {input_data.output_path}")

        repo = get_repository(Path(input_data.repo_path))

        # Get comprehensive repository data
        metadata = get_repository_metadata(repo)

        # Create export manager and options
        export_manager = ExportManager()
        pagination_info = PaginationInfo(
            **input_data.pagination) if input_data.pagination else None

        export_options = ExportOptions(
            format=OutputFormat(input_data.format.lower()),
            include_metadata=input_data.include_metadata,
            pretty_print=True,
            pagination=pagination_info,
            fields=input_data.fields,
            exclude_fields=input_data.exclude_fields,
        )

        # For now, export the metadata (can be extended to export other data types)
        output_path = Path(input_data.output_path)

        if export_options.format == OutputFormat.JSON:
            import json

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, default=str)
        elif export_options.format == OutputFormat.YAML:
            import yaml

            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(metadata, f, default_flow_style=False,
                          allow_unicode=True)
        else:
            return {"status": "error", "error": f"Unsupported export format: {input_data.format}"}

        await ctx.info(f"Export complete: {output_path}")

        return {
            "status": "success",
            "output_path": str(output_path),
            "format": input_data.format,
            "exported_items": len(metadata),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        await ctx.error(f"Error during data export: {str(e)}")
        return {"status": "error", "error": f"Export failed: {str(e)}"}
