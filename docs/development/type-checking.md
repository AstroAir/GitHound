# Type Checking with MyPy

GitHound maintains strict type safety through comprehensive MyPy type checking. This document covers our type checking setup, best practices, and how to maintain type safety when contributing to the project.

## Current Status

✅ **Zero MyPy Errors**: GitHound currently passes MyPy type checking with zero errors  
✅ **Full Type Coverage**: All modules are fully type-annotated  
✅ **Strict Configuration**: Comprehensive MyPy configuration for maximum type safety

## MyPy Configuration

Our MyPy configuration is defined in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = false
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
show_error_codes = true
show_column_numbers = true
ignore_missing_imports = false
plugins = ["pydantic.mypy"]
exclude = ["build/", "githound.egg-info/"]

# Per-module options
[[tool.mypy.overrides]]
module = [
    "ripgrepy.*",
    "diskcache.*",
    "redis.*",
]
ignore_missing_imports = true
```

### Configuration Explanation

#### Core Settings

- **`python_version = "3.11"`**: Target Python version for type checking
- **`warn_return_any = true`**: Warn when functions return `Any` type
- **`warn_unused_configs = true`**: Warn about unused configuration options

#### Type Definition Requirements

- **`disallow_incomplete_defs = true`**: Require complete type annotations for function definitions
- **`check_untyped_defs = true`**: Type-check functions without annotations
- **`no_implicit_optional = true`**: Require explicit `Optional` for nullable types

#### Warning Configuration

- **`warn_redundant_casts = true`**: Warn about unnecessary type casts
- **`warn_unused_ignores = true`**: Warn about unused `# type: ignore` comments
- **`warn_no_return = true`**: Warn about functions that don't return
- **`warn_unreachable = true`**: Warn about unreachable code

#### Output Configuration

- **`show_error_codes = true`**: Show error codes for easier debugging
- **`show_column_numbers = true`**: Show column numbers in error messages

#### Plugin Configuration

- **`plugins = ["pydantic.mypy"]`**: Enable Pydantic plugin for better model type checking

## Running Type Checks

### Basic Type Checking

```bash
# Check all files
mypy githound

# Check specific file
mypy githound/cli.py

# Check with verbose output
mypy --verbose githound
```

### Integration with Testing

```bash
# Run both tests and type checking
pytest && mypy githound

# Run with coverage
pytest --cov=githound && mypy githound
```

### Continuous Integration

Our CI pipeline runs MyPy on every commit:

```yaml
# .github/workflows/test.yml
- name: Type check with MyPy
  run: mypy githound
```

## Type Annotation Best Practices

### 1. Function Annotations

```python
# Good: Complete type annotations
def search_commits(
    repo: Repo,
    query: str,
    author: Optional[str] = None,
    max_results: int = 100
) -> List[CommitInfo]:
    """Search commits with type-safe parameters."""
    pass

# Avoid: Missing return type
def search_commits(repo: Repo, query: str):
    pass
```

### 2. Class Annotations

```python
# Good: Fully annotated class
class SearchResult:
    commit_hash: str
    file_path: Path
    line_number: int
    relevance_score: float

    def __init__(
        self,
        commit_hash: str,
        file_path: Path,
        line_number: int,
        relevance_score: float
    ) -> None:
        self.commit_hash = commit_hash
        self.file_path = file_path
        self.line_number = line_number
        self.relevance_score = relevance_score
```

### 3. Generic Types

```python
from typing import TypeVar, Generic, List, Dict, Optional

T = TypeVar('T')

class SearchCache(Generic[T]):
    """Type-safe cache implementation."""

    def __init__(self) -> None:
        self._cache: Dict[str, T] = {}

    def get(self, key: str) -> Optional[T]:
        return self._cache.get(key)

    def set(self, key: str, value: T) -> None:
        self._cache[key] = value
```

### 4. Async Functions

```python
from typing import AsyncGenerator, List
import asyncio

async def search_async(
    repo: Repo,
    query: SearchQuery
) -> AsyncGenerator[SearchResult, None]:
    """Async search with proper type annotations."""
    for result in await perform_search(repo, query):
        yield result

async def get_results(repo: Repo, query: SearchQuery) -> List[SearchResult]:
    """Collect async results into a list."""
    results = []
    async for result in search_async(repo, query):
        results.append(result)
    return results
```

### 5. Pydantic Models

```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

class CommitSchema(BaseModel):
    """Type-safe commit schema with Pydantic."""

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True
    )

    hash: str = Field(..., description="Commit hash")
    message: str = Field(..., description="Commit message")
    author: str = Field(..., description="Author name and email")
    date: datetime = Field(..., description="Commit date")
    files_changed: List[str] = Field(default_factory=list, description="Changed files")
```

## Common Type Issues and Solutions

### 1. Optional vs None

```python
# Good: Explicit Optional
def get_author(commit_hash: str) -> Optional[str]:
    if commit_hash in authors:
        return authors[commit_hash]
    return None

# Avoid: Implicit Optional (with no_implicit_optional = true)
def get_author(commit_hash: str) -> str | None:  # Use Optional[str] instead
    pass
```

### 2. Any Type Usage

```python
# Good: Specific types
def process_data(data: Dict[str, Union[str, int, List[str]]]) -> ProcessedData:
    pass

# Avoid: Any type
def process_data(data: Any) -> Any:
    pass
```

### 3. Type Ignores

```python
# Good: Specific ignore with explanation
result = external_library.function()  # type: ignore[attr-defined]  # Library has no stubs

# Avoid: Broad ignore
result = external_library.function()  # type: ignore
```

### 4. Union Types

```python
from typing import Union

# Good: Specific union types
def format_value(value: Union[str, int, float]) -> str:
    return str(value)

# Consider: Use overloads for complex cases
from typing import overload

@overload
def get_data(as_dict: Literal[True]) -> Dict[str, Any]: ...

@overload
def get_data(as_dict: Literal[False]) -> List[Any]: ...

def get_data(as_dict: bool) -> Union[Dict[str, Any], List[Any]]:
    if as_dict:
        return {}
    return []
```

## Type Stub Files

For external libraries without type information:

### Creating Stub Files

```python
# stubs/ripgrepy.pyi
from typing import List, Optional, Iterator

class Ripgrepy:
    def __init__(self, pattern: str, path: str) -> None: ...
    def run(self) -> Iterator[str]: ...
    def with_filename(self) -> 'Ripgrepy': ...
    def line_number(self) -> 'Ripgrepy': ...
```

### Using Stub Files

```toml
# pyproject.toml
[tool.mypy]
mypy_path = "stubs"
```

## Development Workflow

### 1. Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: mypy
        language: system
        types: [python]
        args: [--config-file=pyproject.toml]
```

### 2. IDE Integration

#### VS Code

```json
// .vscode/settings.json
{
  "python.linting.mypyEnabled": true,
  "python.linting.mypyArgs": ["--config-file=pyproject.toml"]
}
```

#### PyCharm

- Enable MyPy plugin
- Configure MyPy executable path
- Set configuration file to `pyproject.toml`

### 3. Type Checking in Tests

```python
# tests/test_types.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Import only for type checking
    from mypy import api

def test_mypy_compliance() -> None:
    """Ensure MyPy passes on all source files."""
    result = api.run(['githound', '--config-file=pyproject.toml'])
    assert result[2] == 0, f"MyPy failed: {result[0]}"
```

## Troubleshooting Type Issues

### Common Error Patterns

#### 1. Missing Return Type

```
error: Function is missing a return type annotation
```

**Solution**: Add explicit return type annotation

#### 2. Incompatible Types

```
error: Argument 1 to "function" has incompatible type "str"; expected "int"
```

**Solution**: Check argument types and fix the mismatch

#### 3. Optional Type Issues

```
error: Item "None" of "Optional[str]" has no attribute "upper"
```

**Solution**: Add None check before accessing attributes

```python
# Good
if value is not None:
    return value.upper()
return None
```

#### 4. Any Type Warnings

```
error: Returning Any from function declared to return "str"
```

**Solution**: Add proper type annotations or type assertions

### Debugging Type Issues

```bash
# Show detailed error information
mypy --show-error-codes --show-column-numbers githound

# Check specific error code
mypy --error-summary githound

# Generate type coverage report
mypy --html-report mypy-report githound
```

## Maintaining Type Safety

### 1. Regular Type Checks

- Run MyPy before every commit
- Include type checking in CI/CD pipeline
- Monitor type coverage metrics

### 2. Code Review Guidelines

- Ensure all new code has proper type annotations
- Review type ignore comments for necessity
- Check for proper use of generic types

### 3. Dependency Management

- Keep type stub packages updated
- Monitor for new type information in dependencies
- Contribute type stubs to upstream projects when possible

### 4. Documentation

- Document complex type relationships
- Explain type ignore comments
- Maintain type annotation examples

## Future Improvements

### Planned Enhancements

- **Stricter Configuration**: Gradually increase MyPy strictness
- **Type Coverage Metrics**: Track type annotation coverage
- **Automated Type Stub Generation**: Generate stubs for internal APIs
- **Performance Optimization**: Optimize type checking performance

### Contributing Guidelines

- All new code must pass MyPy type checking
- Type annotations are required for all public APIs
- Complex type relationships should be documented
- Type ignore comments must include explanations

## Resources

- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pydantic MyPy Plugin](https://pydantic-docs.helpmanual.io/mypy_plugin/)
- [Type Checking Best Practices](https://typing.readthedocs.io/en/latest/)
