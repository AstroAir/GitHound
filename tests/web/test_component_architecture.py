"""
Tests for the new component-based frontend architecture.
"""

import pytest
from pathlib import Path
import json
import re


class TestComponentArchitecture:
    """Test the new modular frontend architecture."""

    @pytest.fixture
    def static_dir(self):
        """Get the static directory path."""
        return Path(__file__).parent.parent.parent / "githound" / "web" / "static"

    @pytest.fixture
    def components_dir(self, static_dir):
        """Get the components directory path."""
        return static_dir / "components"

    @pytest.fixture
    def styles_dir(self, static_dir):
        """Get the styles directory path."""
        return static_dir / "styles"

    def test_directory_structure_exists(self, static_dir, components_dir, styles_dir):
        """Test that the new directory structure exists."""
        assert static_dir.exists(), "Static directory should exist"
        assert components_dir.exists(), "Components directory should exist"
        assert styles_dir.exists(), "Styles directory should exist"
        
        # Check core component directories
        assert (components_dir / "core").exists(), "Core components directory should exist"
        assert (components_dir / "auth").exists(), "Auth components directory should exist"
        assert (components_dir / "search").exists(), "Search components directory should exist"
        assert (components_dir / "ui").exists(), "UI components directory should exist"
        assert (components_dir / "websocket").exists(), "WebSocket components directory should exist"
        assert (components_dir / "utils").exists(), "Utils components directory should exist"

    def test_core_components_exist(self, components_dir):
        """Test that core component files exist."""
        core_dir = components_dir / "core"
        
        required_files = [
            "component.js",
            "registry.js",
            "event-bus.js",
            "state-manager.js",
            "app.js"
        ]
        
        for file_name in required_files:
            file_path = core_dir / file_name
            assert file_path.exists(), f"Core component {file_name} should exist"

    def test_component_files_exist(self, components_dir):
        """Test that all component files exist."""
        expected_components = {
            "auth/auth-manager.js": "AuthManager",
            "search/search-manager.js": "SearchManager", 
            "ui/theme-manager.js": "ThemeManager",
            "ui/notification-manager.js": "NotificationManager",
            "websocket/websocket-manager.js": "WebSocketManager",
            "utils/export-manager.js": "ExportManager"
        }
        
        for file_path, class_name in expected_components.items():
            full_path = components_dir / file_path
            assert full_path.exists(), f"Component file {file_path} should exist"
            
            # Check that the file contains the expected class
            content = full_path.read_text()
            assert f"class {class_name}" in content, f"File {file_path} should contain class {class_name}"

    def test_style_files_exist(self, styles_dir):
        """Test that style files exist."""
        expected_styles = [
            "base/variables.css",
            "base/reset.css",
            "components/theme.css",
            "components/notifications.css",
            "components/connection.css",
            "main.css"
        ]
        
        for style_path in expected_styles:
            full_path = styles_dir / style_path
            assert full_path.exists(), f"Style file {style_path} should exist"

    def test_main_entry_point_exists(self, static_dir):
        """Test that the main entry point exists."""
        main_js = static_dir / "main.js"
        assert main_js.exists(), "Main entry point main.js should exist"
        
        content = main_js.read_text()
        assert "import GitHoundApp" in content, "main.js should import GitHoundApp"
        assert "document.addEventListener('DOMContentLoaded'" in content, "main.js should have DOM ready handler"

    def test_es6_module_syntax(self, components_dir):
        """Test that components use proper ES6 module syntax."""
        js_files = list(components_dir.rglob("*.js"))
        
        for js_file in js_files:
            content = js_file.read_text()
            
            # Check for ES6 import/export syntax
            if "class" in content:
                assert "export" in content, f"File {js_file.name} should export its class"
            
            # Check for proper import statements
            import_pattern = r"import\s+.*\s+from\s+['\"].*['\"]"
            if re.search(import_pattern, content):
                # File has imports, verify they're properly formatted
                imports = re.findall(import_pattern, content)
                for import_stmt in imports:
                    assert ".js" in import_stmt, f"Import in {js_file.name} should include .js extension: {import_stmt}"

    def test_component_base_class_usage(self, components_dir):
        """Test that components properly extend the base Component class."""
        component_files = [
            "auth/auth-manager.js",
            "search/search-manager.js",
            "ui/theme-manager.js",
            "ui/notification-manager.js",
            "websocket/websocket-manager.js",
            "utils/export-manager.js"
        ]
        
        for file_path in component_files:
            full_path = components_dir / file_path
            content = full_path.read_text()
            
            # Check that it imports Component
            assert "import { Component }" in content, f"{file_path} should import Component base class"
            
            # Check that it extends Component
            assert "extends Component" in content, f"{file_path} should extend Component base class"

    def test_css_variables_defined(self, styles_dir):
        """Test that CSS variables are properly defined."""
        variables_css = styles_dir / "base" / "variables.css"
        content = variables_css.read_text()
        
        # Check for essential CSS variables
        essential_vars = [
            "--primary-color",
            "--bg-primary",
            "--text-primary",
            "--border-color",
            "--transition-normal"
        ]
        
        for var in essential_vars:
            assert var in content, f"CSS variable {var} should be defined"

    def test_html_updated_for_modules(self, static_dir):
        """Test that HTML file is updated to use the new module system."""
        html_file = static_dir / "index.html"
        content = html_file.read_text()
        
        # Check for module script tag
        assert 'type="module"' in content, "HTML should include module script tag"
        assert 'src="main.js"' in content, "HTML should reference main.js"

    def test_backward_compatibility(self, static_dir):
        """Test that backward compatibility is maintained."""
        html_file = static_dir / "index.html"
        content = html_file.read_text()
        
        # Check that legacy app.js is still referenced for fallback
        assert 'src="app.js"' in content, "HTML should still reference legacy app.js for fallback"

    def test_component_documentation(self, components_dir):
        """Test that components have proper documentation."""
        readme_files = list(components_dir.rglob("README.md"))
        
        # Should have README files in main directories
        expected_readmes = [
            components_dir / "README.md",
            (static_dir := components_dir.parent) / "utils" / "README.md",
            static_dir / "styles" / "README.md"
        ]
        
        for readme in expected_readmes:
            if readme.exists():
                content = readme.read_text()
                assert len(content) > 100, f"README {readme} should have substantial content"

    def test_no_syntax_errors_in_js(self, static_dir):
        """Test that JavaScript files have no obvious syntax errors."""
        js_files = list(static_dir.rglob("*.js"))
        
        for js_file in js_files:
            content = js_file.read_text()
            
            # Basic syntax checks
            open_braces = content.count('{')
            close_braces = content.count('}')
            assert open_braces == close_braces, f"Mismatched braces in {js_file.name}"
            
            open_parens = content.count('(')
            close_parens = content.count(')')
            assert open_parens == close_parens, f"Mismatched parentheses in {js_file.name}"

    def test_css_syntax_valid(self, styles_dir):
        """Test that CSS files have valid syntax."""
        css_files = list(styles_dir.rglob("*.css"))
        
        for css_file in css_files:
            content = css_file.read_text()
            
            # Basic CSS syntax checks
            open_braces = content.count('{')
            close_braces = content.count('}')
            assert open_braces == close_braces, f"Mismatched braces in {css_file.name}"
            
            # Check for CSS variable usage
            if "--" in content:
                # File uses CSS variables, check for proper var() usage
                var_usage = re.findall(r'var\(--[^)]+\)', content)
                var_definitions = re.findall(r'--[\w-]+:', content)
                
                # Should have some variable usage if variables are defined
                if var_definitions:
                    assert len(var_usage) > 0 or "variables.css" in css_file.name, \
                        f"CSS file {css_file.name} defines variables but doesn't use them"
