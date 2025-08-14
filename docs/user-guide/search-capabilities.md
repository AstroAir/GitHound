# Search Capabilities

Overview of GitHound's search features and filters.

## Highlights

- Content, author, message, and date range filters
- File path, file type, and commit hash targeting
- Fuzzy search with adjustable threshold
- Combined multi-criteria queries

## Examples

```bash
githound search --author "alice" --file-type py "def handler" .
githound search --fuzzy --fuzzy-threshold 0.8 "functon" .
```

See also: [CLI Usage](cli-usage.md)
