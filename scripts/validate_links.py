#!/usr/bin/env python3
"""
Script to validate links and cross-references in GitHound documentation.

This script checks internal links, external URLs, and cross-references
to ensure they are current and functional.

Note: This script is now integrated with the comprehensive validation script
(validate_documentation.py). Consider using that for full validation.
"""

import re
import sys
import urllib.parse
from pathlib import Path
from typing import List, Dict, Set, Tuple
import urllib.request
import urllib.error

class LinkValidator:
    """Validates links and cross-references in documentation."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.errors = []
        self.warnings = []
        self.checked_links = 0
        self.external_cache = {}  # Cache for external URL checks

    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in the project."""
        markdown_files = []

        # Check common documentation locations
        doc_dirs = ["docs", ".", "examples"]

        for doc_dir in doc_dirs:
            doc_path = self.project_root / doc_dir
            if doc_path.exists():
                if doc_path.is_file() and doc_path.suffix == '.md':
                    markdown_files.append(doc_path)
                elif doc_path.is_dir():
                    markdown_files.extend(doc_path.rglob("*.md"))

        return list(set(markdown_files))  # Remove duplicates

    def extract_links(self, file_path: Path) -> List[Tuple[str, str, int]]:
        """
        Extract links from a markdown file.

        Returns:
            List of tuples: (link_text, link_url, line_number)
        """
        links = []

        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.warnings.append(f"Could not read {file_path}: {e}")
            return links

        lines = content.split('\n')

        # Patterns for different link types
        patterns = [
            r'\[([^\]]*)\]\(([^)]+)\)',  # [text](url)
            r'<([^>]+)>',               # <url>
            r'href=["\']([^"\']+)["\']', # href="url"
        ]

        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    if len(match.groups()) == 2:
                        # [text](url) format
                        link_text, link_url = match.groups()
                    else:
                        # <url> or href format
                        link_url = match.group(1)
                        link_text = link_url

                    links.append((link_text, link_url, line_num))

        return links

    def is_external_url(self, url: str) -> bool:
        """Check if URL is external (starts with http/https)."""
        return url.startswith(('http://', 'https://'))

    def is_anchor_link(self, url: str) -> bool:
        """Check if URL is an anchor link (starts with #)."""
        return url.startswith('#')

    def is_email_link(self, url: str) -> bool:
        """Check if URL is an email link (starts with mailto:)."""
        return url.startswith('mailto:')

    def resolve_relative_path(self, base_file: Path, relative_url: str) -> Path:
        """Resolve relative path from base file."""
        # Remove anchor if present
        if '#' in relative_url:
            relative_url = relative_url.split('#')[0]

        if not relative_url:  # Just an anchor
            return base_file

        # Resolve relative to the directory containing the base file
        base_dir = base_file.parent
        resolved = (base_dir / relative_url).resolve()

        return resolved

    def check_internal_link(self, base_file: Path, link_url: str) -> bool:
        """Check if internal link exists."""
        try:
            resolved_path = self.resolve_relative_path(base_file, link_url)

            # Check if file exists
            if resolved_path.exists():
                return True

            # Check if it's a directory with index file
            if resolved_path.is_dir():
                index_files = ['index.md', 'README.md', 'index.html']
                for index_file in index_files:
                    if (resolved_path / index_file).exists():
                        return True

            return False

        except Exception:
            return False

    def check_external_url(self, url: str) -> bool:
        """Check if external URL is accessible."""
        # Use cache to avoid repeated requests
        if url in self.external_cache:
            return self.external_cache[url]

        try:
            # Create request with user agent
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'GitHound Link Validator'}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                success = response.getcode() < 400
                self.external_cache[url] = success
                return success

        except (urllib.error.URLError, urllib.error.HTTPError, Exception):
            self.external_cache[url] = False
            return False

    def validate_file_links(self, file_path: Path) -> None:
        """Validate all links in a single file."""
        print(f"Checking {file_path.relative_to(self.project_root)}")

        links = self.extract_links(file_path)

        for link_text, link_url, line_num in links:
            self.checked_links += 1

            # Skip certain types of links
            if self.is_email_link(link_url):
                continue  # Skip email links

            if link_url.startswith('javascript:'):
                continue  # Skip JavaScript links

            # Check anchor links (just validate format)
            if self.is_anchor_link(link_url):
                if not re.match(r'^#[a-zA-Z0-9_-]+$', link_url):
                    self.warnings.append(f"Malformed anchor link '{link_url}' in {file_path}:{line_num}")
                continue

            # Check external URLs
            if self.is_external_url(link_url):
                if not self.check_external_url(link_url):
                    self.warnings.append(f"External URL not accessible: '{link_url}' in {file_path}:{line_num}")
                continue

            # Check internal links
            if not self.check_internal_link(file_path, link_url):
                self.errors.append(f"Broken internal link: '{link_url}' in {file_path}:{line_num}")

    def check_cross_references(self) -> None:
        """Check for common cross-reference patterns."""
        markdown_files = self.find_markdown_files()

        # Build a map of available files
        available_files = set()
        for file_path in markdown_files:
            relative_path = file_path.relative_to(self.project_root)
            available_files.add(str(relative_path))
            available_files.add(str(relative_path).replace('\\', '/'))  # Windows compatibility

        # Check for references to documentation sections
        common_refs = [
            'docs/getting-started/installation.md',
            'docs/getting-started/configuration.md',
            'docs/user-guide/cli-usage.md',
            'docs/api-reference/rest-api.md',
            'docs/mcp-server/README.md',
            'docs/development/contributing.md',
            'README.md',
            'CHANGELOG.md'
        ]

        for ref in common_refs:
            ref_path = self.project_root / ref
            if not ref_path.exists():
                self.warnings.append(f"Common reference file missing: {ref}")

    def run_validation(self) -> bool:
        """Run complete link validation."""
        print("🔗 Validating links and cross-references...")

        markdown_files = self.find_markdown_files()
        print(f"Found {len(markdown_files)} markdown files")

        if not markdown_files:
            print("⚠️  No markdown files found")
            return True

        # Validate links in each file
        for file_path in markdown_files:
            self.validate_file_links(file_path)

        # Check cross-references
        self.check_cross_references()

        # Print results
        print(f"\n📊 Validation Results:")
        print(f"   Links checked: {self.checked_links}")
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
            print("✅ All links and cross-references are valid!")

        return len(self.errors) == 0


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    validator = LinkValidator(project_root)

    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
