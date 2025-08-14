# Export Options

GitHound supports exporting results to multiple formats for downstream use.

## Supported Formats

- JSON (default)
- YAML
- CSV
- XML
- Excel (xlsx)

## Examples

```bash
githound search "function" . --export results.json --format json
githound search "function" . --export results.yaml --format yaml
githound search "function" . --export results.csv  --format csv
```

## Tips

- Use filters to reduce exported data size
- Include metadata for richer context
