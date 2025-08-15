#!/usr/bin/env python3
"""
GitHound MCP Client Example

This example demonstrates how to use FastMCP client to interact with GitHound's
MCP server for comprehensive git repository analysis.

Usage:
    python examples/mcp_server/clients/githound_client.py [repo_path]

This example covers:
- Connecting to GitHound MCP server
- Repository analysis and metadata extraction
- Commit history analysis
- File change tracking
- Author statistics and contributions
- Resource access for structured data
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport
from fastmcp.exceptions import ToolError, McpError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def analyze_repository_comprehensive(client: Client, repo_path: str) -> Dict[str, Any]:
    """
    Perform comprehensive repository analysis using GitHound MCP server.
    
    Args:
        client: Connected FastMCP client
        repo_path: Path to the Git repository
        
    Returns:
        Dict containing comprehensive repository analysis
    """
    logger.info(f"Starting comprehensive analysis of repository: {repo_path}")
    
    analysis_results = {}
    
    try:
        # 1. Basic repository analysis
        logger.info("1. Analyzing repository metadata...")
        repo_result = await client.call_tool("analyze_repository", {"repo_path": repo_path})
        
        if repo_result.data:
            repo_info = repo_result.data
            analysis_results["repository"] = repo_info
            
            logger.info(f"✓ Repository: {repo_info.get('name', 'Unknown')}")
            logger.info(f"  Total commits: {repo_info.get('total_commits', 0)}")
            logger.info(f"  Total files: {repo_info.get('total_files', 0)}")
            logger.info(f"  Total authors: {repo_info.get('total_authors', 0)}")
            logger.info(f"  Branches: {', '.join(repo_info.get('branches', []))}")
        
        # 2. Recent commit history
        logger.info("2. Analyzing recent commit history...")
        history_result = await client.call_tool("get_commit_history", {
            "repo_path": repo_path,
            "limit": 10
        })
        
        if history_result.data:
            commits = history_result.data
            analysis_results["recent_commits"] = commits
            
            logger.info(f"✓ Retrieved {len(commits)} recent commits")
            for i, commit in enumerate(commits[:3]):  # Show first 3
                logger.info(f"  {i+1}. {commit.get('hash', '')[:8]} - {commit.get('message', '')[:50]}...")
        
        # 3. Author statistics
        logger.info("3. Analyzing author contributions...")
        authors_result = await client.call_tool("get_author_stats", {"repo_path": repo_path})
        
        if authors_result.data:
            author_stats = authors_result.data
            analysis_results["author_statistics"] = author_stats
            
            logger.info(f"✓ Found {author_stats.get('total_authors', 0)} contributors")
            authors = author_stats.get('authors', [])
            for i, author in enumerate(authors[:3]):  # Show top 3
                logger.info(f"  {i+1}. {author.get('name', 'Unknown')} - {author.get('commits', 0)} commits")
        
        analysis_results["analysis_completed"] = True
        analysis_results["analysis_timestamp"] = datetime.now().isoformat()
        
        return analysis_results
        
    except ToolError as e:
        logger.error(f"Tool execution failed during repository analysis: {e}")
        analysis_results["error"] = str(e)
        return analysis_results
    except Exception as e:
        logger.error(f"Repository analysis failed: {e}")
        analysis_results["error"] = str(e)
        return analysis_results


async def analyze_specific_commit(client: Client, repo_path: str, commit_hash: str) -> Dict[str, Any]:
    """
    Analyze a specific commit in detail.
    
    Args:
        client: Connected FastMCP client
        repo_path: Path to the Git repository
        commit_hash: Hash of the commit to analyze
        
    Returns:
        Dict containing detailed commit analysis
    """
    logger.info(f"Analyzing specific commit: {commit_hash}")
    
    try:
        result = await client.call_tool("analyze_commit", {
            "repo_path": repo_path,
            "commit_hash": commit_hash
        })
        
        if result.data:
            commit_info = result.data
            
            logger.info(f"✓ Commit Analysis:")
            logger.info(f"  Hash: {commit_info.get('hash', 'Unknown')}")
            logger.info(f"  Author: {commit_info.get('author', 'Unknown')}")
            logger.info(f"  Date: {commit_info.get('date', 'Unknown')}")
            logger.info(f"  Message: {commit_info.get('message', 'No message')}")
            logger.info(f"  Files changed: {commit_info.get('files_changed', 0)}")
            logger.info(f"  Insertions: {commit_info.get('insertions', 0)}")
            logger.info(f"  Deletions: {commit_info.get('deletions', 0)}")
            
            return {
                "commit_analysis": commit_info,
                "analysis_successful": True
            }
        else:
            return {"error": "No commit data returned"}
            
    except ToolError as e:
        logger.error(f"Commit analysis failed: {e}")
        return {"error": str(e)}


async def analyze_file_history(client: Client, repo_path: str, file_path: str) -> Dict[str, Any]:
    """
    Analyze the history of a specific file.
    
    Args:
        client: Connected FastMCP client
        repo_path: Path to the Git repository
        file_path: Path to the file to analyze
        
    Returns:
        Dict containing file history analysis
    """
    logger.info(f"Analyzing file history: {file_path}")
    
    try:
        result = await client.call_tool("get_file_history", {
            "repo_path": repo_path,
            "file_path": file_path,
            "limit": 5
        })
        
        if result.data:
            file_commits = result.data
            
            logger.info(f"✓ File History for {file_path}:")
            logger.info(f"  Total commits affecting this file: {len(file_commits)}")
            
            for i, commit in enumerate(file_commits):
                logger.info(f"  {i+1}. {commit.get('hash', '')[:8]} - {commit.get('author', 'Unknown')} - {commit.get('message', '')[:40]}...")
            
            return {
                "file_path": file_path,
                "commit_history": file_commits,
                "total_commits": len(file_commits),
                "analysis_successful": True
            }
        else:
            return {"error": "No file history data returned"}
            
    except ToolError as e:
        logger.error(f"File history analysis failed: {e}")
        return {"error": str(e)}


async def access_repository_resources(client: Client, repo_path: str) -> Dict[str, Any]:
    """
    Access GitHound repository resources through MCP.
    
    Args:
        client: Connected FastMCP client
        repo_path: Path to the Git repository
        
    Returns:
        Dict containing resource access results
    """
    logger.info("Accessing repository resources...")
    
    resource_results = {}
    
    try:
        # 1. Repository summary resource
        logger.info("1. Accessing repository summary resource...")
        summary_uri = f"githound://repository/{repo_path}/summary"
        
        try:
            summary_content = await client.read_resource(summary_uri)
            if summary_content:
                summary_text = getattr(summary_content[0], 'text', str(summary_content[0]))
                summary_data = json.loads(summary_text)
                resource_results["summary"] = summary_data
                
                logger.info("✓ Repository summary accessed")
                logger.info(f"  Activity level: {summary_data.get('summary', {}).get('activity_level', 'Unknown')}")
                logger.info(f"  Team size: {summary_data.get('summary', {}).get('team_size', 'Unknown')}")
                logger.info(f"  Maturity: {summary_data.get('summary', {}).get('maturity', 'Unknown')}")
        except Exception as e:
            logger.warning(f"Failed to access summary resource: {e}")
            resource_results["summary_error"] = str(e)
        
        # 2. Contributors resource
        logger.info("2. Accessing contributors resource...")
        contributors_uri = f"githound://repository/{repo_path}/contributors"
        
        try:
            contributors_content = await client.read_resource(contributors_uri)
            if contributors_content:
                contributors_text = getattr(contributors_content[0], 'text', str(contributors_content[0]))
                contributors_data = json.loads(contributors_text)
                resource_results["contributors"] = contributors_data
                
                logger.info("✓ Contributors resource accessed")
                summary = contributors_data.get('summary', {})
                logger.info(f"  Total contributors: {summary.get('total_contributors', 0)}")
                logger.info(f"  Top contributor: {summary.get('top_contributor', 'Unknown')}")
                logger.info(f"  Total commits: {summary.get('total_commits', 0)}")
        except Exception as e:
            logger.warning(f"Failed to access contributors resource: {e}")
            resource_results["contributors_error"] = str(e)
        
        resource_results["resources_accessed"] = True
        return resource_results
        
    except Exception as e:
        logger.error(f"Resource access failed: {e}")
        return {"error": str(e)}


async def demonstrate_advanced_queries(client: Client, repo_path: str) -> Dict[str, Any]:
    """
    Demonstrate advanced query patterns with GitHound MCP server.
    
    Args:
        client: Connected FastMCP client
        repo_path: Path to the Git repository
        
    Returns:
        Dict containing advanced query results
    """
    logger.info("Demonstrating advanced query patterns...")
    
    advanced_results = {}
    
    try:
        # 1. Filtered commit history by author
        logger.info("1. Querying commits by specific author...")
        
        # First get author stats to find an author
        authors_result = await client.call_tool("get_author_stats", {"repo_path": repo_path})
        if authors_result.data and authors_result.data.get('authors'):
            top_author = authors_result.data['authors'][0]['name']
            
            filtered_commits = await client.call_tool("get_commit_history", {
                "repo_path": repo_path,
                "limit": 5,
                "author": top_author
            })
            
            if filtered_commits.data:
                advanced_results["author_commits"] = {
                    "author": top_author,
                    "commits": filtered_commits.data,
                    "count": len(filtered_commits.data)
                }
                logger.info(f"✓ Found {len(filtered_commits.data)} commits by {top_author}")
        
        # 2. Recent commits with date filtering
        logger.info("2. Querying recent commits with date filtering...")
        
        recent_commits = await client.call_tool("get_commit_history", {
            "repo_path": repo_path,
            "limit": 20,
            "since": "2024-01-01T00:00:00Z"
        })
        
        if recent_commits.data:
            advanced_results["recent_commits"] = {
                "since": "2024-01-01",
                "commits": recent_commits.data,
                "count": len(recent_commits.data)
            }
            logger.info(f"✓ Found {len(recent_commits.data)} commits since 2024-01-01")
        
        # 3. Multiple file history analysis
        logger.info("3. Analyzing multiple file histories...")
        
        common_files = ["README.md", "setup.py", "pyproject.toml", "main.py", "app.py"]
        file_analyses = []
        
        for file_path in common_files:
            try:
                file_result = await client.call_tool("get_file_history", {
                    "repo_path": repo_path,
                    "file_path": file_path,
                    "limit": 3
                })
                
                if file_result.data:
                    file_analyses.append({
                        "file": file_path,
                        "commits": len(file_result.data),
                        "latest_commit": file_result.data[0] if file_result.data else None
                    })
                    logger.info(f"  {file_path}: {len(file_result.data)} commits")
            except ToolError:
                # File doesn't exist or no history
                continue
        
        advanced_results["file_analyses"] = file_analyses
        
        advanced_results["advanced_queries_completed"] = True
        return advanced_results
        
    except Exception as e:
        logger.error(f"Advanced queries failed: {e}")
        return {"error": str(e)}


async def main(repo_path: str = ".") -> Dict[str, Any]:
    """
    Main function demonstrating comprehensive GitHound MCP client usage.
    
    Args:
        repo_path: Path to the Git repository to analyze
        
    Returns:
        Dict containing all analysis results
    """
    print("=" * 60)
    print("GitHound MCP Client - Repository Analysis")
    print("=" * 60)
    print(f"Analyzing repository: {Path(repo_path).absolute()}")
    print("=" * 60)
    
    # Path to GitHound MCP server
    server_script = Path(__file__).parent.parent / "servers" / "githound_server.py"
    
    if not server_script.exists():
        logger.error(f"GitHound MCP server not found at: {server_script}")
        return {"error": "GitHound MCP server not found"}
    
    results = {}
    
    try:
        # Connect to GitHound MCP server
        transport = PythonStdioTransport(str(server_script))

        async with Client(transport) as client:
            logger.info("✓ Connected to GitHound MCP Server")
            
            # 1. Comprehensive repository analysis
            logger.info("\n1. Comprehensive Repository Analysis")
            repo_analysis = await analyze_repository_comprehensive(client, repo_path)
            results["repository_analysis"] = repo_analysis
            
            # 2. Resource access
            logger.info("\n2. Repository Resource Access")
            resource_results = await access_repository_resources(client, repo_path)
            results["resource_access"] = resource_results
            
            # 3. Advanced queries
            logger.info("\n3. Advanced Query Patterns")
            advanced_results = await demonstrate_advanced_queries(client, repo_path)
            results["advanced_queries"] = advanced_results
            
            # 4. Specific commit analysis (if we have commits)
            if repo_analysis.get("recent_commits"):
                latest_commit = repo_analysis["recent_commits"][0]
                commit_hash = latest_commit.get("hash")
                
                if commit_hash:
                    logger.info(f"\n4. Specific Commit Analysis ({commit_hash[:8]})")
                    commit_analysis = await analyze_specific_commit(client, repo_path, commit_hash)
                    results["commit_analysis"] = commit_analysis
            
            # 5. File history analysis (common files)
            logger.info("\n5. File History Analysis")
            file_history_results = []
            
            common_files = ["README.md", "pyproject.toml", "setup.py"]
            for file_path in common_files:
                file_result = await analyze_file_history(client, repo_path, file_path)
                if not file_result.get("error"):
                    file_history_results.append(file_result)
                    break  # Just analyze one file for demonstration
            
            results["file_history"] = file_history_results
            
            print("\n" + "=" * 60)
            print("GitHound MCP Client analysis completed!")
            print("=" * 60)
            
            return results
            
    except McpError as e:
        logger.error(f"Failed to connect to GitHound MCP server: {e}")
        return {"error": f"Connection failed: {e}"}
    except Exception as e:
        logger.error(f"GitHound MCP client analysis failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Get repository path from command line or use current directory
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    # Run the GitHound MCP client analysis
    result = asyncio.run(main(repo_path))
    
    # Print summary
    print(f"\nAnalysis Summary:")
    if "error" in result:
        print(f"  Error: {result['error']}")
    else:
        if "repository_analysis" in result:
            repo_info = result["repository_analysis"].get("repository", {})
            print(f"  Repository: {repo_info.get('name', 'Unknown')}")
            print(f"  Commits: {repo_info.get('total_commits', 0)}")
            print(f"  Authors: {repo_info.get('total_authors', 0)}")
        
        print(f"  Analysis sections completed: {len([k for k in result.keys() if not k.startswith('error')])}")
        print(f"  Total data points collected: {sum(len(str(v)) for v in result.values()) // 100} (approx)")
