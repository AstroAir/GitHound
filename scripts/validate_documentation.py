#!/usr/bin/env python3
"""
Comprehensive documentation validation script for GitHound.

This script combines and enhances existing validation capabilities:
- Link validation (internal and external)
- Code example validation
- Configuration example validation
- Style and formatting validation
- Content completeness checking
"""

import ast
import json
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
import argparse

class DocumentationValidator:
    """Comprehensive documentation validator."""

    def __init__(self, project_root: Path, config_path: Optional[Path] = None):
        self.project_root = project_root
        self.config = self._load_config(config_path)
        self.errors = []
        self.warnings = []
        self.stats = {
            'files_checked': 0,
            'links_checked': 0,
            'code_examples_checked': 0,
            'config_examples_checked': 0,
            'style_issues_found': 0
        }
        self.external_cache = {}  # Cache for external URL checks

    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load validation configuration."""
        default_config = {
            'skip_external_links': False,
            'external_timeout': 10,
            'allowed_extensions': ['.md', '.rst', '.txt'],
            'doc_directories': ['docs', '.', 'examples'],
            'required_sections': {
                'README.md': ['Installation', 'Usage', 'Documentation'],
                'user-guide': ['Overview', 'Prerequisites', 'Examples'],
                'api-reference': ['Overview', 'Authentication', 'Endpoints']
            },
            'style_rules': {
                'max_line_length': 100,
                'require_code_language': True,
                'require_heading_hierarchy': True,
                'require_cross_references': True
            }
        }

        if config_path and config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                self.warnings.append(f"Could not load config {config_path}: {e}")

        return default_config

    def find_documentation_files(self) -> List[Path]:
        """Find all documentation files in the project."""
        doc_files = []
        extensions = self.config['allowed_extensions']

        for doc_dir in self.config['doc_directories']:
            doc_path = self.project_root / doc_dir
            if doc_path.exists():
                if doc_path.is_file() and doc_path.suffix in extensions:
                    doc_files.append(doc_path)
                elif doc_path.is_dir():
                    for ext in extensions:
                        doc_files.extend(doc_path.rglob(f"*{ext}"))

        return list(set(doc_files))  # Remove duplicates

    def validate_links(self, file_path: Path) -> None:
        """Validate links in a documentation file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.errors.append(f"Could not read {file_path}: {e}")
            return

        # Extract markdown links
        link_pattern = r'\[([^\]]*)\]\(([^)]+)\)'
        links = re.finditer(link_pattern, content)

        for match in links:
            link_text = match.group(1)
            link_url = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            self.stats['links_checked'] += 1

            if link_url.startswith('http'):
                self._validate_external_link(link_url, file_path, line_num)
            elif link_url.startswith('#'):
                self._validate_anchor_link(link_url, content, file_path, line_num)
            else:
                self._validate_internal_link(link_url, file_path, line_num)

    def _validate_external_link(self, url: str, file_path: Path, line_num: int) -> None:
        """Validate external URL."""
        if self.config['skip_external_links']:
            return

        if url in self.external_cache:
            if not self.external_cache[url]:
                self.errors.append(f"{file_path}:{line_num}: External link failed: {url}")
            return

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'GitHound-DocValidator'})
            with urllib.request.urlopen(req, timeout=self.config['external_timeout']) as response:
                self.external_cache[url] = response.status == 200
        except Exception:
            self.external_cache[url] = False
            self.errors.append(f"{file_path}:{line_num}: External link failed: {url}")

    def _validate_internal_link(self, link_url: str, file_path: Path, line_num: int) -> None:
        """Validate internal file link."""
        # Handle relative paths
        if link_url.startswith('./') or link_url.startswith('../'):
            target_path = (file_path.parent / link_url).resolve()
        else:
            target_path = self.project_root / link_url

        # Handle anchor links in other files
        if '#' in link_url:
            file_part, anchor = link_url.split('#', 1)
            if file_part:
                target_path = (file_path.parent / file_part).resolve()

        if not target_path.exists():
            self.errors.append(f"{file_path}:{line_num}: Internal link not found: {link_url}")

    def _validate_anchor_link(self, anchor: str, content: str, file_path: Path, line_num: int) -> None:
        """Validate anchor link within the same file."""
        anchor_id = anchor[1:]  # Remove #

        # Look for heading that would generate this anchor
        heading_pattern = r'^#+\s+(.+)$'
        headings = re.finditer(heading_pattern, content, re.MULTILINE)

        valid_anchors = set()
        for heading_match in headings:
            heading_text = heading_match.group(1).strip()
            # Convert heading to anchor format (simplified)
            anchor_text = re.sub(r'[^\w\s-]', '', heading_text.lower())
            anchor_text = re.sub(r'\s+', '-', anchor_text)
            valid_anchors.add(anchor_text)

        if anchor_id not in valid_anchors:
            self.warnings.append(f"{file_path}:{line_num}: Anchor not found: {anchor}")

    def validate_code_examples(self, file_path: Path) -> None:
        """Validate code examples in documentation."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.errors.append(f"Could not read {file_path}: {e}")
            return

        # Find code blocks
        code_patterns = {
            'python': r'```python\n(.*?)\n```',
            'bash': r'```bash\n(.*?)\n```',
            'yaml': r'```yaml\n(.*?)\n```',
            'json': r'```json\n(.*?)\n```'
        }

        for language, pattern in code_patterns.items():
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                code = match.group(1).strip()
                line_num = content[:match.start()].count('\n') + 1
                self.stats['code_examples_checked'] += 1

                if language == 'python':
                    self._validate_python_code(code, file_path, line_num)
                elif language == 'yaml':
                    self._validate_yaml_code(code, file_path, line_num)
                elif language == 'json':
                    self._validate_json_code(code, file_path, line_num)
                elif language == 'bash':
                    self._validate_bash_code(code, file_path, line_num)

    def _validate_python_code(self, code: str, file_path: Path, line_num: int) -> None:
        """Validate Python code syntax."""
        try:
            ast.parse(code)
        except SyntaxError as e:
            self.errors.append(f"{file_path}:{line_num}: Python syntax error: {e}")

        # Check for GitHound imports
        if 'from githound' in code or 'import githound' in code:
            # Validate that imports are current
            if 'from githound.search_engine' in code:
                self.warnings.append(f"{file_path}:{line_num}: Check if import path is current")

    def _validate_yaml_code(self, code: str, file_path: Path, line_num: int) -> None:
        """Validate YAML syntax."""
        try:
            yaml.safe_load(code)
            self.stats['config_examples_checked'] += 1
        except yaml.YAMLError as e:
            self.errors.append(f"{file_path}:{line_num}: YAML syntax error: {e}")

    def _validate_json_code(self, code: str, file_path: Path, line_num: int) -> None:
        """Validate JSON syntax."""
        try:
            json.loads(code)
        except json.JSONDecodeError as e:
            self.errors.append(f"{file_path}:{line_num}: JSON syntax error: {e}")

    def _validate_bash_code(self, code: str, file_path: Path, line_num: int) -> None:
        """Validate bash commands."""
        # Check for common GitHound commands
        if 'githound' in code:
            # Basic validation - could be enhanced
            lines = code.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('githound') and '--invalid-option' in line:
                    self.warnings.append(f"{file_path}:{line_num + i}: Check command validity")

    def validate_style(self, file_path: Path) -> None:
        """Validate documentation style and formatting."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.errors.append(f"Could not read {file_path}: {e}")
            return

        lines = content.split('\n')

        # Check line length
        max_length = self.config['style_rules']['max_line_length']
        for i, line in enumerate(lines, 1):
            if len(line) > max_length:
                self.stats['style_issues_found'] += 1
                self.warnings.append(f"{file_path}:{i}: Line too long ({len(line)} > {max_length})")

        # Check heading hierarchy
        if self.config['style_rules']['require_heading_hierarchy']:
            self._validate_heading_hierarchy(content, file_path)

        # Check code block language specification
        if self.config['style_rules']['require_code_language']:
            self._validate_code_block_languages(content, file_path)

    def _validate_heading_hierarchy(self, content: str, file_path: Path) -> None:
        """Validate heading hierarchy (H1 -> H2 -> H3, etc.)."""
        heading_pattern = r'^(#+)\s+(.+)$'
        headings = re.finditer(heading_pattern, content, re.MULTILINE)

        previous_level = 0
        for match in headings:
            level = len(match.group(1))
            line_num = content[:match.start()].count('\n') + 1

            if level > previous_level + 1:
                self.warnings.append(f"{file_path}:{line_num}: Heading level skipped (H{previous_level} -> H{level})")

            previous_level = level

    def _validate_code_block_languages(self, content: str, file_path: Path) -> None:
        """Check that code blocks specify languages."""
        # Find code blocks without language specification
        unlabeled_pattern = r'^```\s*\n'
        matches = re.finditer(unlabeled_pattern, content, re.MULTILINE)

        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            self.warnings.append(f"{file_path}:{line_num}: Code block missing language specification")

    def validate_content_completeness(self, file_path: Path) -> None:
        """Validate that required sections are present."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.errors.append(f"Could not read {file_path}: {e}")
            return

        # Check for required sections based on file type
        file_name = file_path.name.lower()
        required_sections = None

        for pattern, sections in self.config['required_sections'].items():
            if pattern in file_name or file_path.match(pattern):
                required_sections = sections
                break

        if required_sections:
            for section in required_sections:
                if section.lower() not in content.lower():
                    self.warnings.append(f"{file_path}: Missing required section: {section}")

    def run_validation(self, files: Optional[List[Path]] = None) -> bool:
        """Run comprehensive validation on documentation files."""
        if files is None:
            files = self.find_documentation_files()

        print(f"Validating {len(files)} documentation files...")

        for file_path in files:
            self.stats['files_checked'] += 1
            print(f"Validating: {file_path.relative_to(self.project_root)}")

            self.validate_links(file_path)
            self.validate_code_examples(file_path)
            self.validate_style(file_path)
            self.validate_content_completeness(file_path)

        return len(self.errors) == 0

    def print_results(self) -> None:
        """Print validation results."""
        print("\n" + "="*60)
        print("DOCUMENTATION VALIDATION RESULTS")
        print("="*60)

        print(f"\nFiles checked: {self.stats['files_checked']}")
        print(f"Links checked: {self.stats['links_checked']}")
        print(f"Code examples checked: {self.stats['code_examples_checked']}")
        print(f"Config examples checked: {self.stats['config_examples_checked']}")
        print(f"Style issues found: {self.stats['style_issues_found']}")

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All validation checks passed!")
        elif not self.errors:
            print(f"\n✅ No errors found, but {len(self.warnings)} warnings to review.")
        else:
            print(f"\n❌ Validation failed with {len(self.errors)} errors and {len(self.warnings)} warnings.")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate GitHound documentation")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument("--skip-external", action="store_true", help="Skip external link validation")
    parser.add_argument("files", nargs="*", type=Path, help="Specific files to validate")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    validator = DocumentationValidator(project_root, args.config)

    if args.skip_external:
        validator.config['skip_external_links'] = True

    files = [project_root / f for f in args.files] if args.files else None
    success = validator.run_validation(files)
    validator.print_results()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
