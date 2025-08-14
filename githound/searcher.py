"""Encapsulates the core search logic using the ripgrep (rg) command."""

import json
import subprocess
from pathlib import Path
from typing import List

from githound.models import SearchConfig, SearchResult, SearchType


def search_blob_content(
    content: bytes, query: str, config: SearchConfig, commit_hash: str, file_path: str
) -> List[SearchResult]:
    """
    Searches the given content for the query using the ripgrep (rg) command.

    Args:
        content: The content to search, as bytes.
        query: The regex pattern to search for.
        config: The search configuration.
        commit_hash: The hash of the commit being searched.
        file_path: The path of the file being searched.

    Returns:
        A list of search results.
    """
    rg_args = ["rg", "--json", query, "-"]
    if not config.case_sensitive:
        rg_args.append("-i")

    try:
        process = subprocess.run(
            rg_args, input=content, capture_output=True, check=True, text=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # ripgrep not found or returned an error (e.g., no matches)
        return []

    results: List[SearchResult] = []
    for line in process.stdout.strip().split("\n"):
        if not line:
            continue
        match = json.loads(line)
        if match["type"] == "match":
            data = match["data"]
            results.append(
                SearchResult(
                    commit_hash=commit_hash,
                    file_path=Path(file_path),
                    line_number=data["line_number"],
                    matching_line=data["lines"]["text"].strip(),
                    commit_info=None,
                    search_type=SearchType.CONTENT,
                    relevance_score=0.0,
                    match_context=None,
                    search_time_ms=None
                )
            )
    return results