# Output Format Examples

This directory contains examples demonstrating GitHound's various output formats and export capabilities.

## Examples Overview

- `json_output.py` - JSON format examples and schemas
- `yaml_output.py` - YAML configuration and export
- `csv_export.py` - CSV data export for analysis
- `custom_formats.py` - Custom format implementations
- `structured_data.py` - Structured data patterns
- `export_options.py` - Export configuration examples

## Supported Output Formats

### JSON Format
- Structured JSON output
- Schema validation
- Nested data representation
- API-compatible format

### YAML Format
- Human-readable configuration
- Configuration file export
- Hierarchical data structure
- Comments and documentation

### CSV Format
- Tabular data export
- Spreadsheet compatibility
- Data analysis ready
- Bulk data processing

### Custom Formats
- Template-based output
- Custom serialization
- Integration-specific formats
- Extensible format system

## Running Examples

```bash
python examples/output_formats/json_output.py
python examples/output_formats/yaml_output.py
python examples/output_formats/csv_export.py
# etc.
```

## JSON Output Examples

### Repository Metadata JSON
```json
{
  "repository": {
    "path": "/path/to/repo",
    "name": "my-project",
    "total_commits": 1250,
    "total_branches": 15,
    "total_tags": 8,
    "size_mb": 45.2,
    "created_at": "2022-01-15T10:30:00Z",
    "last_commit": {
      "hash": "abc123def456",
      "author": "Alice Developer",
      "date": "2023-11-15T14:30:00Z",
      "message": "Fix critical authentication bug"
    },
    "contributors": [
      {
        "name": "Alice Developer",
        "email": "alice@example.com",
        "commits": 450,
        "first_commit": "2022-01-15T10:30:00Z",
        "last_commit": "2023-11-15T14:30:00Z"
      }
    ],
    "branches": [
      {
        "name": "main",
        "commits": 1200,
        "last_commit": "abc123def456"
      }
    ]
  }
}
```

### Commit History JSON
```json
{
  "commits": [
    {
      "hash": "abc123def456",
      "short_hash": "abc123d",
      "author": {
        "name": "Alice Developer",
        "email": "alice@example.com"
      },
      "committer": {
        "name": "Alice Developer",
        "email": "alice@example.com"
      },
      "date": "2023-11-15T14:30:00Z",
      "message": "Fix critical authentication bug",
      "files_changed": 3,
      "insertions": 25,
      "deletions": 8,
      "files": [
        {
          "path": "src/auth.py",
          "status": "modified",
          "insertions": 15,
          "deletions": 3
        }
      ]
    }
  ],
  "pagination": {
    "total": 1250,
    "page": 1,
    "per_page": 50,
    "has_next": true
  }
}
```

## YAML Output Examples

### Repository Configuration YAML
```yaml
repository:
  name: my-project
  path: /path/to/repo
  metadata:
    total_commits: 1250
    total_branches: 15
    total_tags: 8
    size_mb: 45.2
    created_at: "2022-01-15T10:30:00Z"

  contributors:
    - name: Alice Developer
      email: alice@example.com
      commits: 450
      first_commit: "2022-01-15T10:30:00Z"
      last_commit: "2023-11-15T14:30:00Z"

  branches:
    - name: main
      commits: 1200
      last_commit: abc123def456
      protected: true
    - name: develop
      commits: 1180
      last_commit: def456ghi789
      protected: false

analysis_config:
  search_patterns:
    - "*.py"
    - "*.js"
    - "*.md"

  exclude_patterns:
    - "node_modules/"
    - "__pycache__/"
    - "*.pyc"

  filters:
    date_range:
      from: "2023-01-01"
      to: "2023-12-31"
    authors:
      - alice@example.com
      - bob@example.com
```

## CSV Export Examples

### Commit History CSV
```csv
hash,short_hash,author_name,author_email,date,message,files_changed,insertions,deletions
abc123def456,abc123d,Alice Developer,alice@example.com,2023-11-15T14:30:00Z,Fix critical authentication bug,3,25,8
def456ghi789,def456g,Bob Developer,bob@example.com,2023-11-14T16:45:00Z,Add new feature implementation,5,120,15
```

### Author Statistics CSV
```csv
author_name,author_email,total_commits,total_files,first_commit,last_commit,lines_added,lines_deleted
Alice Developer,alice@example.com,450,125,2022-01-15T10:30:00Z,2023-11-15T14:30:00Z,15420,3250
Bob Developer,bob@example.com,380,98,2022-02-01T09:15:00Z,2023-11-14T16:45:00Z,12850,2890
```

## Export Configuration

### Export Options
```python
from githound.schemas import ExportOptions, OutputFormat

export_options = ExportOptions(
    format=OutputFormat.JSON,
    include_metadata=True,
    include_file_contents=False,
    compress_output=True,
    pagination=PaginationInfo(
        page_size=100,
        max_pages=10
    )
)
```

### Custom Format Implementation
```python
from githound.utils.export import ExportManager

class CustomExporter:
    def export_repository(self, repo_data, options):
        # Custom export logic
        return formatted_output
```
