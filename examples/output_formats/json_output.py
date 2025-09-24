#!/usr/bin/env python3
"""
JSON Output Format Examples

This example demonstrates GitHound's JSON output capabilities including
structured data export, schema validation, and various JSON formatting options.

Usage:
    python examples/output_formats/json_output.py /path/to/repository

This example covers:
- Repository metadata in JSON format
- Commit history JSON export
- Author statistics JSON output
- Structured data validation
- Pretty-printed vs compact JSON
- Custom JSON serialization
- Schema documentation
"""

import json
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

from githound.git_handler import (
    get_repository, get_repository_metadata, extract_commit_metadata,
    get_commits_with_filters
)
from githound.git_blame import get_author_statistics
from githound.utils.export import ExportManager
from githound.schemas import ExportOptions, OutputFormat


# Configure logging
logging.basicConfig(  # [attr-defined]
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JSONOutputDemo:
    """Demonstration of JSON output formats and capabilities."""

    def __init__(self, repo_path: str) -> None:
        """Initialize with repository path."""
        self.repo_path = Path(repo_path)
        self.repo = None
        self.export_manager = ExportManager()

    def load_repository(self) -> bool:
        """Load the repository."""
        try:
            self.repo = get_repository(self.repo_path)
            logger.info(f"✓ Repository loaded: {self.repo_path}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to load repository: {e}")
            return False

    def demonstrate_repository_metadata_json(self) -> Dict[str, Any]:
        """Demonstrate repository metadata in JSON format."""
        logger.info("\n=== Repository Metadata JSON ===")

        if not self.repo:
            return {"error": "Repository not loaded"}

        try:
            # Get repository metadata
            metadata = get_repository_metadata(self.repo)

            # Create structured JSON output
            json_output = {
                "schema_version": "1.0",
                "export_timestamp": datetime.now().isoformat(),
                "repository": {
                    "path": str(self.repo_path),
                    "name": metadata.get('name', self.repo_path.name),
                    "metadata": metadata
                }
            }

            # Pretty print JSON
            pretty_json = json.dumps(json_output, indent=2, default=str)
            logger.info("Repository metadata JSON structure:")
            print(pretty_json[:500] + "..." if len(pretty_json) > 500 else pretty_json)

            # Save to file
            output_file = self.repo_path.name + "_metadata.json"
            with open(output_file, 'w') as f:
                json.dump(json_output, f, indent=2, default=str)

            logger.info(f"✓ Repository metadata saved to: {output_file}")

            # Demonstrate compact JSON
            compact_json = json.dumps(json_output, separators=(',', ':'), default=str)
            logger.info(f"Compact JSON size: {len(compact_json)} characters")
            logger.info(f"Pretty JSON size: {len(pretty_json)} characters")
            logger.info(f"Size difference: {len(pretty_json) - len(compact_json)} characters")

            return json_output

        except Exception as e:
            logger.error(f"✗ Repository metadata JSON generation failed: {e}")
            return {"error": str(e)}

    def demonstrate_commit_history_json(self, max_commits: int = 20) -> Dict[str, Any]:
        """Demonstrate commit history in JSON format."""
        logger.info(f"\n=== Commit History JSON (last {max_commits} commits) ===")

        if not self.repo:
            return {"error": "Repository not loaded"}

        try:
            # Get commit history
            commits = get_commits_with_filters(
                repo=self.repo,
                max_count=max_commits
            )

            commit_list: list[Any] = []
            for commit in commits:
                try:
                    commit_info = extract_commit_metadata(commit)
                    commit_data = commit_info.model_dump()
                    commit_list.append(commit_data)
                except Exception as e:
                    logger.warning(f"Failed to process commit {commit.hexsha[:8]}: {e}")
                    continue

            # Create structured JSON output
            json_output = {
                "schema_version": "1.0",
                "export_timestamp": datetime.now().isoformat(),
                "commit_history": {
                    "repository_path": str(self.repo_path),
                    "total_commits_analyzed": len(commit_list),
                    "max_commits_requested": max_commits,
                    "commits": commit_list
                },
                "metadata": {
                    "export_format": "json",
                    "data_types": {
                        "hash": "string",
                        "author_name": "string",
                        "author_email": "string",
                        "timestamp": "ISO 8601 datetime string",
                        "message": "string",
                        "files_changed": "array of strings",
                        "insertions": "integer",
                        "deletions": "integer",
                        "parent_hashes": "array of strings"
                    }
                }
            }

            # Save to file with different formatting options
            base_name = self.repo_path.name + "_commits"

            # Pretty formatted JSON
            pretty_file = base_name + "_pretty.json"
            with open(pretty_file, 'w') as f:
                json.dump(json_output, f, indent=2, default=str, ensure_ascii=False)

            # Compact JSON
            compact_file = base_name + "_compact.json"
            with open(compact_file, 'w') as f:
                json.dump(json_output, f, separators=(',', ':'), default=str, ensure_ascii=False)

            # Sorted keys JSON (for consistency)
            sorted_file = base_name + "_sorted.json"
            with open(sorted_file, 'w') as f:
                json.dump(json_output, f, indent=2, sort_keys=True, default=str, ensure_ascii=False)

            logger.info(f"✓ Commit history saved in multiple formats:")
            logger.info(f"  Pretty formatted: {pretty_file}")
            logger.info(f"  Compact format: {compact_file}")
            logger.info(f"  Sorted keys: {sorted_file}")

            # File size comparison
            pretty_size = Path(pretty_file).stat().st_size
            compact_size = Path(compact_file).stat().st_size
            sorted_size = Path(sorted_file).stat().st_size

            logger.info(f"File sizes:")
            logger.info(f"  Pretty: {pretty_size:,} bytes")
            logger.info(f"  Compact: {compact_size:,} bytes ({compact_size/pretty_size:.1%} of pretty)")
            logger.info(f"  Sorted: {sorted_size:,} bytes")

            return json_output

        except Exception as e:
            logger.error(f"✗ Commit history JSON generation failed: {e}")
            return {"error": str(e)}

    def demonstrate_author_statistics_json(self) -> Dict[str, Any]:
        """Demonstrate author statistics in JSON format."""
        logger.info("\n=== Author Statistics JSON ===")

        if not self.repo:
            return {"error": "Repository not loaded"}

        try:
            # Get author statistics
            author_stats = get_author_statistics(self.repo)

            # Transform data for better JSON structure
            authors_list: list[Any] = []
            for author_name, stats in author_stats.items():
                author_data = {
                    "name": author_name,
                    "email": stats.get('email', 'unknown'),
                    "statistics": {
                        "total_commits": stats.get('total_commits', 0),
                        "total_files": stats.get('total_files', 0),
                        "lines_added": stats.get('lines_added', 0),
                        "lines_deleted": stats.get('lines_deleted', 0),
                        "first_commit": stats.get('first_commit', None),
                        "last_commit": stats.get('last_commit', None)
                    }
                }

                # Calculate additional metrics
                total_lines = author_data["statistics"]["lines_added"] + author_data["statistics"]["lines_deleted"]
                author_data["statistics"]["total_lines_changed"] = total_lines

                if author_data["statistics"]["total_commits"] > 0:
                    author_data["statistics"]["avg_lines_per_commit"] = round(
                        total_lines / author_data["statistics"]["total_commits"], 2
                    )

                authors_list.append(author_data)

            # Sort by commit count
            authors_list.sort(key=lambda x: x["statistics"]["total_commits"], reverse=True)

            # Create structured JSON output
            json_output = {
                "schema_version": "1.0",
                "export_timestamp": datetime.now().isoformat(),
                "author_statistics": {
                    "repository_path": str(self.repo_path),
                    "total_authors": len(authors_list),
                    "authors": authors_list
                },
                "summary": {
                    "total_commits": sum(author["statistics"]["total_commits"] for author in authors_list),
                    "total_lines_changed": sum(author["statistics"]["total_lines_changed"] for author in authors_list),
                    "most_active_author": authors_list[0]["name"] if authors_list else None,
                    "least_active_author": authors_list[-1]["name"] if authors_list else None
                },
                "metadata": {
                    "export_format": "json",
                    "data_schema": {
                        "authors": {
                            "type": "array",
                            "items": {
                                "name": "string",
                                "email": "string",
                                "statistics": {
                                    "total_commits": "integer",
                                    "total_files": "integer",
                                    "lines_added": "integer",
                                    "lines_deleted": "integer",
                                    "total_lines_changed": "integer",
                                    "avg_lines_per_commit": "float",
                                    "first_commit": "ISO 8601 datetime string or null",
                                    "last_commit": "ISO 8601 datetime string or null"
                                }
                            }
                        }
                    }
                }
            }

            # Save to file
            output_file = self.repo_path.name + "_authors.json"
            with open(output_file, 'w') as f:
                json.dump(json_output, f, indent=2, default=str, ensure_ascii=False)

            logger.info(f"✓ Author statistics saved to: {output_file}")
            logger.info(f"Total authors: {len(authors_list)}")

            if authors_list:
                top_author = authors_list[0]
                logger.info(f"Most active author: {top_author['name']} ({top_author['statistics']['total_commits']} commits)")

            return json_output

        except Exception as e:
            logger.error(f"✗ Author statistics JSON generation failed: {e}")
            return {"error": str(e)}

    def demonstrate_custom_json_serialization(self) -> Dict[str, Any]:
        """Demonstrate custom JSON serialization techniques."""
        logger.info("\n=== Custom JSON Serialization ===")

        # Custom JSON encoder for special data types
        class GitHoundJSONEncoder(json.JSONEncoder):
            """Custom JSON encoder for GitHound data types."""

            def default(self, obj) -> None:
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, Path):
                    return str(obj)
                elif hasattr(obj, 'model_dump'):  # Pydantic models
                    return obj.model_dump()
                elif hasattr(obj, '__dict__'):  # Generic objects
                    return obj.__dict__
                return super().default(obj)

        # Example data with various types
        sample_data = {
            "timestamp": datetime.now(),
            "repository_path": self.repo_path,
            "analysis_results": {
                "completed": True,
                "duration_seconds": 45.67,
                "items_processed": 1234,
                "success_rate": 0.987
            },
            "configuration": {
                "max_commits": 100,
                "include_merges": True,
                "output_formats": ["json", "yaml"],
                "filters": {
                    "authors": ["alice", "bob"],
                    "date_range": {
                        "start": datetime.now() - datetime.now().replace(day=1),
                        "end": datetime.now()
                    }
                }
            }
        }

        # Serialize with custom encoder
        custom_json = json.dumps(sample_data, cls=GitHoundJSONEncoder, indent=2)

        logger.info("Custom JSON serialization example:")
        print(custom_json)

        # Save example
        output_file = "custom_serialization_example.json"
        with open(output_file, 'w') as f:
            json.dump(sample_data, f, cls=GitHoundJSONEncoder, indent=2)

        logger.info(f"✓ Custom serialization example saved to: {output_file}")

        return {"custom_serialization": "completed", "output_file": output_file}

    def demonstrate_json_schema_validation(self) -> Dict[str, Any]:
        """Demonstrate JSON schema validation."""
        logger.info("\n=== JSON Schema Validation ===")

        # Define a schema for repository metadata
        repository_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "GitHound Repository Metadata",
            "type": "object",
            "required": ["schema_version", "export_timestamp", "repository"],
            "properties": {
                "schema_version": {
                    "type": "string",
                    "pattern": "^\\d+\\.\\d+$"
                },
                "export_timestamp": {
                    "type": "string",
                    "format": "date-time"
                },
                "repository": {
                    "type": "object",
                    "required": ["path", "name", "metadata"],
                    "properties": {
                        "path": {"type": "string"},
                        "name": {"type": "string"},
                        "metadata": {
                            "type": "object",
                            "properties": {
                                "total_commits": {"type": "integer", "minimum": 0},
                                "total_branches": {"type": "integer", "minimum": 0},
                                "total_tags": {"type": "integer", "minimum": 0},
                                "contributors": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }

        # Save schema
        schema_file = "githound_repository_schema.json"
        with open(schema_file, 'w') as f:
            json.dump(repository_schema, f, indent=2)

        logger.info(f"✓ JSON schema saved to: {schema_file}")
        logger.info("Schema defines structure for repository metadata JSON")

        # Example of schema usage documentation
        schema_docs = {
            "schema_info": {
                "title": "GitHound Repository Metadata Schema",
                "version": "1.0",
                "description": "JSON schema for validating GitHound repository metadata exports"
            },
            "usage_example": {
                "validation_command": "jsonschema -i data.json schema.json",
                "python_validation": "jsonschema.validate(data, schema)"
            },
            "field_descriptions": {
                "schema_version": "Version of the data schema used",
                "export_timestamp": "ISO 8601 timestamp of when data was exported",
                "repository.path": "File system path to the repository",
                "repository.name": "Name of the repository",
                "repository.metadata.total_commits": "Total number of commits in repository",
                "repository.metadata.contributors": "List of contributor names"
            }
        }

        docs_file = "schema_documentation.json"
        with open(docs_file, 'w') as f:
            json.dump(schema_docs, f, indent=2)

        logger.info(f"✓ Schema documentation saved to: {docs_file}")

        return {
            "schema_file": schema_file,
            "documentation_file": docs_file,
            "validation": "schema_available"
        }


async def main() -> None:
    """Main demonstration function."""

    if len(sys.argv) != 2:
        print("Usage: python json_output.py /path/to/repository")
        sys.exit(1)

    repo_path = sys.argv[1]

    if not Path(repo_path).exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        sys.exit(1)

    print("=" * 70)
    print("GitHound - JSON Output Format Examples")
    print("=" * 70)
    print(f"Repository: {repo_path}")
    print()

    demo = JSONOutputDemo(repo_path)

    try:
        # Load repository
        if not demo.load_repository():
            sys.exit(1)

        # Run all demonstrations
        demo.demonstrate_repository_metadata_json()
        demo.demonstrate_commit_history_json(max_commits=10)
        demo.demonstrate_author_statistics_json()
        demo.demonstrate_custom_json_serialization()
        demo.demonstrate_json_schema_validation()

        print("\n" + "=" * 70)
        print("JSON output format demonstration completed!")
        print("=" * 70)
        print("\nGenerated files:")

        # List generated files
        for file_path in Path.cwd().glob(f"{Path(repo_path).name}_*.json"):
            print(f"  - {file_path.name}")

        for file_path in Path.cwd().glob("*schema*.json"):
            print(f"  - {file_path.name}")

        for file_path in Path.cwd().glob("custom_*.json"):
            print(f"  - {file_path.name}")

    except Exception as e:
        logger.error(f"JSON output demonstration failed: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
