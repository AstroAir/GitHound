"""
Basic MCP usage examples for GitHound.

This script demonstrates how to interact with GitHound's MCP server
programmatically using the FastMCP client.
"""

import asyncio
from pathlib import Path

from fastmcp import FastMCPClient


async def main() -> None:
    """Demonstrate basic GitHound MCP usage."""

    # Connect to GitHound MCP server
    client = FastMCPClient()

    # Example repository path (adjust as needed)
    repo_path = str(Path.cwd())

    print("🔍 GitHound MCP Examples")
    print("=" * 50)

    # Example 1: Repository Analysis
    print("\n1. Repository Analysis")
    print("-" * 30)

    try:
        result = await client.call_tool("analyze_repository", {"repo_path": repo_path})

        if result["status"] == "success":
            metadata = result["metadata"]
            print(f"Repository: {metadata['name']}")
            print(f"Total commits: {metadata['total_commits']}")
            print(f"Contributors: {len(metadata['contributors'])}")
            print(f"Branches: {len(metadata['branches'])}")
        else:
            print(f"Error: {result['error']}")

    except Exception as e:
        print(f"Failed to analyze repository: {e}")

    # Example 2: Advanced Search
    print("\n2. Advanced Search")
    print("-" * 30)

    try:
        result = await client.call_tool(
            "advanced_search",
            {
                "repo_path": repo_path,
                "content_pattern": "def main",
                "file_extensions": [".py"],
                "max_results": 10,
            },
        )

        if result["status"] == "success":
            results = result["results"]
            print(f"Found {len(results)} matches:")

            for i, match in enumerate(results[:3], 1):
                print(f"  {i}. {match['file_path']}:{match['line_number']}")
                print(f"     {match['matching_line'].strip()}")
        else:
            print(f"Error: {result['error']}")

    except Exception as e:
        print(f"Failed to perform search: {e}")

    # Example 3: Fuzzy Search
    print("\n3. Fuzzy Search")
    print("-" * 30)

    try:
        result = await client.call_tool(
            "fuzzy_search",
            {
                "repo_path": repo_path,
                "search_term": "authentication",
                "threshold": 0.7,
                "max_results": 5,
            },
        )

        if result["status"] == "success":
            results = result["results"]
            print(f"Found {len(results)} fuzzy matches:")

            for match in results:
                print(f"  - {match['file_path']} (score: {match['similarity_score']:.2f})")
        else:
            print(f"Error: {result['error']}")

    except Exception as e:
        print(f"Failed to perform fuzzy search: {e}")

    # Example 4: File History
    print("\n4. File History")
    print("-" * 30)

    try:
        # Find a Python file to analyze
        python_files = list(Path(repo_path).rglob("*.py"))
        if python_files:
            file_path = str(python_files[0].relative_to(repo_path))

            result = await client.call_tool(
                "get_file_history_mcp",
                {"repo_path": repo_path, "file_path": file_path, "max_count": 5},
            )

            if result["status"] == "success":
                history = result["history"]
                print(f"History for {file_path} ({len(history)} commits):")

                for commit in history[:3]:
                    print(f"  - {commit['hash'][:8]} by {commit['author_name']}")
                    print(f"    {commit['message'][:60]}...")
            else:
                print(f"Error: {result['error']}")
        else:
            print("No Python files found in repository")

    except Exception as e:
        print(f"Failed to get file history: {e}")

    # Example 5: Author Statistics
    print("\n5. Author Statistics")
    print("-" * 30)

    try:
        result = await client.call_tool("get_author_stats", {"repo_path": repo_path})

        if result["status"] == "success":
            stats = result["author_stats"]
            print("Top contributors:")

            # Sort by commit count and show top 3
            sorted_authors = sorted(stats.items(), key=lambda x: x[1]["commit_count"], reverse=True)

            for author, data in sorted_authors[:3]:
                print(f"  - {author}: {data['commit_count']} commits")
        else:
            print(f"Error: {result['error']}")

    except Exception as e:
        print(f"Failed to get author statistics: {e}")

    # Example 6: Using Resources
    print("\n6. Repository Resources")
    print("-" * 30)

    try:
        # Get repository summary resource
        summary = await client.get_resource(f"githound://repository/{repo_path}/summary")

        print("Repository Summary:")
        print(summary[:200] + "..." if len(summary) > 200 else summary)

    except Exception as e:
        print(f"Failed to get resource: {e}")

    # Example 7: Using Prompts
    print("\n7. Bug Investigation Prompt")
    print("-" * 30)

    try:
        prompt = await client.get_prompt(
            "investigate_bug",
            {
                "bug_description": "Authentication fails for new users",
                "suspected_files": "auth.py, user.py",
                "time_frame": "last 7 days",
            },
        )

        print("Generated investigation workflow:")
        print(prompt[:300] + "..." if len(prompt) > 300 else prompt)

    except Exception as e:
        print(f"Failed to get prompt: {e}")

    print("\n✅ Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
