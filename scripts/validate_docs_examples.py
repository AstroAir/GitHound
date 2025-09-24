#!/usr/bin/env python3
"""
Script to validate code examples in GitHound documentation.

This script scans documentation files for code examples and validates them
against the current implementation.

Note: This script is now integrated with the comprehensive validation script
(validate_documentation.py). Consider using that for full validation.
"""

import ast
import re
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
import tempfile
import os

# Documentation directories to scan
DOC_DIRS = [
    "docs",
    "README.md",
    "examples"
]

# File extensions to scan
DOC_EXTENSIONS = [".md", ".rst", ".txt"]

# Code block patterns
CODE_BLOCK_PATTERNS = [
    r"```python\n(.*?)\n```",
    r"```bash\n(.*?)\n```",
    r"```yaml\n(.*?)\n```",
    r"```json\n(.*?)\n```",
]

class DocumentationValidator:
    """Validates code examples in documentation."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.errors = []
        self.warnings = []
        self.validated_examples = 0

    def scan_documentation(self) -> List[Tuple[Path, str, str, str]]:
        """
        Scan documentation files for code examples.

        Returns:
            List of tuples: (file_path, language, code, context)
        """
        examples = []

        for doc_dir in DOC_DIRS:
            doc_path = self.project_root / doc_dir
            if not doc_path.exists():
                continue

            if doc_path.is_file():
                # Single file (like README.md)
                examples.extend(self._extract_examples_from_file(doc_path))
            else:
                # Directory
                for file_path in doc_path.rglob("*"):
                    if file_path.suffix in DOC_EXTENSIONS:
                        examples.extend(self._extract_examples_from_file(file_path))

        return examples

    def _extract_examples_from_file(self, file_path: Path) -> List[Tuple[Path, str, str, str]]:
        """Extract code examples from a single file."""
        examples = []

        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.warnings.append(f"Could not read {file_path}: {e}")
            return examples

        # Extract code blocks
        for pattern in CODE_BLOCK_PATTERNS:
            language = pattern.split('\\n')[0].replace('```', '').replace('\\n', '')
            matches = re.finditer(pattern, content, re.DOTALL)

            for match in matches:
                code = match.group(1).strip()
                if code:
                    # Get context (surrounding lines)
                    start_pos = match.start()
                    lines_before = content[:start_pos].split('\n')[-3:]
                    context = '\n'.join(lines_before).strip()

                    examples.append((file_path, language, code, context))

        return examples

    def validate_python_examples(self, examples: List[Tuple[Path, str, str, str]]) -> None:
        """Validate Python code examples."""
        python_examples = [ex for ex in examples if ex[1] == 'python']

        for file_path, _, code, context in python_examples:
            self._validate_python_code(file_path, code, context)

    def _validate_python_code(self, file_path: Path, code: str, context: str) -> None:
        """Validate a single Python code example."""
        self.validated_examples += 1

        # Check syntax
        try:
            ast.parse(code)
        except SyntaxError as e:
            self.errors.append(f"Syntax error in {file_path}: {e}")
            return

        # Check for GitHound imports
        if "from githound" in code or "import githound" in code:
            self._validate_githound_usage(file_path, code, context)

        # Check for common patterns
        self._check_common_patterns(file_path, code, context)

    def _validate_githound_usage(self, file_path: Path, code: str, context: str) -> None:
        """Validate GitHound-specific code usage."""
        # Check for correct import patterns
        if "from githound import GitHound" in code:
            # Good import pattern
            pass
        elif "import githound" in code and "githound.GitHound" not in code:
            self.warnings.append(f"Consider using 'from githound import GitHound' in {file_path}")

        # Check for proper Path usage
        if "GitHound(" in code and "Path(" not in code and '"/path/to' not in code:
            self.warnings.append(f"GitHound constructor should use Path objects in {file_path}")

        # Check for async/await usage
        if "search_advanced(" in code and "await" not in code:
            self.warnings.append(f"search_advanced() is async and requires 'await' in {file_path}")

        if "search_advanced_sync(" in code and "await" in code:
            self.warnings.append(f"search_advanced_sync() is synchronous, remove 'await' in {file_path}")

    def _check_common_patterns(self, file_path: Path, code: str, context: str) -> None:
        """Check for common coding patterns and issues."""
        # Check for hardcoded paths
        if "/path/to/" in code and "# Example" not in context:
            self.warnings.append(f"Hardcoded example path in {file_path}, consider using relative paths")

        # Check for missing error handling in examples
        if ("GitHound(" in code or "search_" in code) and "try:" not in code and "except" not in code:
            if "# Error handling" not in context and "safe_" not in code:
                self.warnings.append(f"Consider adding error handling example in {file_path}")

        # Check for deprecated patterns
        if "git_handler" in code:
            self.warnings.append(f"git_handler module usage may be deprecated in {file_path}")

    def validate_bash_examples(self, examples: List[Tuple[Path, str, str, str]]) -> None:
        """Validate bash/shell command examples."""
        bash_examples = [ex for ex in examples if ex[1] in ['bash', 'sh', 'shell']]

        for file_path, _, code, context in bash_examples:
            self._validate_bash_code(file_path, code, context)

    def _validate_bash_code(self, file_path: Path, code: str, context: str) -> None:
        """Validate bash command examples."""
        self.validated_examples += 1

        lines = code.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Check for GitHound CLI usage
            if line.startswith('githound '):
                self._validate_cli_command(file_path, line, context)

            # Check for common command patterns
            if 'pip install' in line and 'githound' in line:
                self._validate_pip_command(file_path, line, context)

    def _validate_cli_command(self, file_path: Path, command: str, context: str) -> None:
        """Validate GitHound CLI command examples."""
        # Check for required arguments
        if 'githound search' in command and '--repo-path' not in command:
            self.warnings.append(f"CLI search command missing --repo-path in {file_path}")

        # Check for deprecated options
        deprecated_options = ['--auth', '--api-key']
        for option in deprecated_options:
            if option in command:
                self.warnings.append(f"Deprecated CLI option {option} in {file_path}")

        # Check for valid export formats
        if '--export' in command:
            export_match = re.search(r'--export\s+(\S+)', command)
            if export_match:
                export_file = export_match.group(1)
                valid_extensions = ['.json', '.yaml', '.yml', '.csv', '.xlsx', '.xml']
                if not any(export_file.endswith(ext) for ext in valid_extensions):
                    self.warnings.append(f"Unknown export format in {file_path}: {export_file}")

    def _validate_pip_command(self, file_path: Path, command: str, context: str) -> None:
        """Validate pip installation commands."""
        # Check for virtual environment recommendation
        if 'pip install githound' in command and 'venv' not in context and 'virtual' not in context:
            self.warnings.append(f"Consider mentioning virtual environment for pip install in {file_path}")

    def validate_yaml_examples(self, examples: List[Tuple[Path, str, str, str]]) -> None:
        """Validate YAML configuration examples."""
        yaml_examples = [ex for ex in examples if ex[1] in ['yaml', 'yml']]

        for file_path, _, code, context in yaml_examples:
            self._validate_yaml_code(file_path, code, context)

    def _validate_yaml_code(self, file_path: Path, code: str, context: str) -> None:
        """Validate YAML configuration examples."""
        self.validated_examples += 1

        try:
            import yaml
            yaml.safe_load(code)
        except ImportError:
            self.warnings.append(f"PyYAML not available to validate YAML in {file_path}")
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in {file_path}: {e}")

    def validate_json_examples(self, examples: List[Tuple[Path, str, str, str]]) -> None:
        """Validate JSON examples."""
        json_examples = [ex for ex in examples if ex[1] == 'json']

        for file_path, _, code, context in json_examples:
            self._validate_json_code(file_path, code, context)

    def _validate_json_code(self, file_path: Path, code: str, context: str) -> None:
        """Validate JSON examples."""
        self.validated_examples += 1

        try:
            import json
            json.loads(code)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in {file_path}: {e}")

    def run_validation(self) -> bool:
        """Run complete validation and return success status."""
        print("🔍 Scanning documentation for code examples...")

        examples = self.scan_documentation()
        print(f"Found {len(examples)} code examples")

        if not examples:
            print("⚠️  No code examples found")
            return True

        print("🐍 Validating Python examples...")
        self.validate_python_examples(examples)

        print("🐚 Validating bash examples...")
        self.validate_bash_examples(examples)

        print("📄 Validating YAML examples...")
        self.validate_yaml_examples(examples)

        print("📋 Validating JSON examples...")
        self.validate_json_examples(examples)

        # Print results
        print(f"\n📊 Validation Results:")
        print(f"   Examples validated: {self.validated_examples}")
        print(f"   Errors: {len(self.errors)}")
        print(f"   Warnings: {len(self.warnings)}")

        if self.errors:
            print(f"\n❌ Errors:")
            for error in self.errors:
                print(f"   {error}")

        if self.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   {warning}")

        if not self.errors and not self.warnings:
            print("✅ All code examples are valid!")

        return len(self.errors) == 0


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    validator = DocumentationValidator(project_root)

    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
