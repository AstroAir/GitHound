"""
Script to validate configuration examples in GitHound documentation.

This script tests YAML configuration examples to ensure they are valid
and consistent with the current implementation.

Note: This script is now integrated with the comprehensive validation script
(validate_documentation.py). Consider using that for full validation.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


class ConfigValidator:
    """Validates configuration examples in documentation."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.errors = []
        self.warnings = []
        self.validated_configs = 0

    def extract_yaml_examples(self, file_path: Path) -> list[tuple[str, str]]:
        """Extract YAML code blocks from documentation files."""
        examples = []

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.warnings.append(f"Could not read {file_path}: {e}")
            return examples

        # Find YAML code blocks
        yaml_pattern = r"```yaml\n(.*?)\n```"
        matches = re.finditer(yaml_pattern, content, re.DOTALL)

        for match in matches:
            yaml_content = match.group(1).strip()
            if yaml_content:
                # Get context (preceding lines for identification)
                start_pos = match.start()
                lines_before = content[:start_pos].split("\n")[-3:]
                context = "\n".join(lines_before).strip()
                examples.append((yaml_content, context))

        return examples

    def validate_yaml_syntax(self, yaml_content: str, context: str, file_path: Path) -> bool:
        """Validate YAML syntax."""
        try:
            yaml.safe_load(yaml_content)
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML syntax in {file_path} ({context}): {e}")
            return False

    def validate_config_structure(
        self, config: dict[str, Any], context: str, file_path: Path
    ) -> None:
        """Validate configuration structure and values."""
        # Check for known configuration sections
        known_sections = {
            "search",
            "cache",
            "export",
            "web",
            "mcp",
            "logging",
            "performance",
            "aliases",
            "export_templates",
        }

        for section in config.keys():
            if section not in known_sections:
                self.warnings.append(
                    f"Unknown config section '{section}' in {file_path} ({context})"
                )

        # Validate specific sections
        if "search" in config:
            self._validate_search_config(config["search"], context, file_path)

        if "web" in config:
            self._validate_web_config(config["web"], context, file_path)

        if "mcp" in config:
            self._validate_mcp_config(config["mcp"], context, file_path)

        if "cache" in config:
            self._validate_cache_config(config["cache"], context, file_path)

    def _validate_search_config(
        self, search_config: dict[str, Any], context: str, file_path: Path
    ) -> None:
        """Validate search configuration."""
        valid_keys = {
            "max_results",
            "fuzzy_threshold",
            "include_binary_files",
            "case_sensitive",
            "file_patterns",
            "exclude_patterns",
            "parallel",
            "max_workers",
            "timeout",
        }

        for key in search_config.keys():
            if key not in valid_keys:
                self.warnings.append(
                    f"Unknown search config key '{key}' in {file_path} ({context})"
                )

        # Validate specific values
        if "max_results" in search_config:
            if (
                not isinstance(search_config["max_results"], int)
                or search_config["max_results"] <= 0
            ):
                self.errors.append(
                    f"max_results must be positive integer in {file_path} ({context})"
                )

        if "fuzzy_threshold" in search_config:
            threshold = search_config["fuzzy_threshold"]
            if not isinstance(threshold, int | float) or not 0 <= threshold <= 1:
                self.errors.append(
                    f"fuzzy_threshold must be between 0 and 1 in {file_path} ({context})"
                )

    def _validate_web_config(
        self, web_config: dict[str, Any], context: str, file_path: Path
    ) -> None:
        """Validate web server configuration."""
        valid_keys = {
            "host",
            "port",
            "auto_open_browser",
            "cors_origins",
            "auth_enabled",
            "rate_limit",
            "workers",
            "timeout",
        }

        for key in web_config.keys():
            if key not in valid_keys:
                self.warnings.append(f"Unknown web config key '{key}' in {file_path} ({context})")

        # Validate port
        if "port" in web_config:
            port = web_config["port"]
            if not isinstance(port, int) or not 1 <= port <= 65535:
                self.errors.append(f"port must be between 1 and 65535 in {file_path} ({context})")

    def _validate_mcp_config(
        self, mcp_config: dict[str, Any], context: str, file_path: Path
    ) -> None:
        """Validate MCP server configuration."""
        valid_keys = {
            "host",
            "port",
            "max_connections",
            "enable_auth",
            "rate_limit_enabled",
            "auth_required",
            "api_key",
        }

        for key in mcp_config.keys():
            if key not in valid_keys:
                self.warnings.append(f"Unknown MCP config key '{key}' in {file_path} ({context})")

        # Check for deprecated keys
        deprecated_keys = ["auth_required", "api_key"]
        for key in deprecated_keys:
            if key in mcp_config:
                self.warnings.append(
                    f"Deprecated MCP config key '{key}' in {file_path} ({context}). Use environment variables instead."
                )

    def _validate_cache_config(
        self, cache_config: dict[str, Any], context: str, file_path: Path
    ) -> None:
        """Validate cache configuration."""
        valid_keys = {"directory", "max_size", "ttl", "compress", "cleanup_interval", "backend"}

        for key in cache_config.keys():
            if key not in valid_keys:
                self.warnings.append(f"Unknown cache config key '{key}' in {file_path} ({context})")

        # Validate TTL
        if "ttl" in cache_config:
            ttl = cache_config["ttl"]
            if not isinstance(ttl, int) or ttl < 0:
                self.errors.append(f"ttl must be non-negative integer in {file_path} ({context})")

    def validate_json_examples(self, file_path: Path) -> None:
        """Validate JSON configuration examples."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.warnings.append(f"Could not read {file_path}: {e}")
            return

        # Find JSON code blocks
        json_pattern = r"```json\n(.*?)\n```"
        matches = re.finditer(json_pattern, content, re.DOTALL)

        for match in matches:
            json_content = match.group(1).strip()
            if json_content:
                self.validated_configs += 1
                try:
                    json.loads(json_content)
                except json.JSONDecodeError as e:
                    self.errors.append(f"Invalid JSON in {file_path}: {e}")

    def validate_file(self, file_path: Path) -> None:
        """Validate all configuration examples in a file."""
        print(f"Validating {file_path.relative_to(self.project_root)}")

        # Validate YAML examples
        yaml_examples = self.extract_yaml_examples(file_path)
        for yaml_content, context in yaml_examples:
            self.validated_configs += 1

            if self.validate_yaml_syntax(yaml_content, context, file_path):
                try:
                    config = yaml.safe_load(yaml_content)
                    if isinstance(config, dict):
                        self.validate_config_structure(config, context, file_path)
                except Exception as e:
                    self.errors.append(
                        f"Error validating config structure in {file_path} ({context}): {e}"
                    )

        # Validate JSON examples
        self.validate_json_examples(file_path)

    def run_validation(self) -> bool:
        """Run validation on all configuration documentation."""
        print("🔍 Validating configuration examples...")

        # Files to validate
        config_files = [
            "docs/getting-started/configuration.md",
            "docs/configuration/environment-variables.md",
            "docs/mcp-server/configuration.md",
            ".env.example",
        ]

        for file_path_str in config_files:
            file_path = self.project_root / file_path_str
            if file_path.exists():
                self.validate_file(file_path)
            else:
                self.warnings.append(f"Configuration file not found: {file_path}")

        # Print results
        print("\n📊 Validation Results:")
        print(f"   Configurations validated: {self.validated_configs}")
        print(f"   Errors: {len(self.errors)}")
        print(f"   Warnings: {len(self.warnings)}")

        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"   {error}")

        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   {warning}")

        if not self.errors and not self.warnings:
            print("✅ All configuration examples are valid!")

        return len(self.errors) == 0


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    validator = ConfigValidator(project_root)

    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
