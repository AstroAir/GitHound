"""
Verification script for the frontend refactoring.
Checks that all components and files are properly created.
"""

import sys
from pathlib import Path


def check_file_exists(file_path, description):
    """Check if a file exists and print result."""
    if file_path.exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (MISSING)")
        return False


def check_directory_exists(dir_path, description):
    """Check if a directory exists and print result."""
    if dir_path.exists() and dir_path.is_dir():
        print(f"✅ {description}: {dir_path}")
        return True
    else:
        print(f"❌ {description}: {dir_path} (MISSING)")
        return False


def check_file_contains(file_path, text, description):
    """Check if a file contains specific text."""
    try:
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            if text in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description} (TEXT NOT FOUND)")
                return False
        else:
            print(f"❌ {description} (FILE NOT FOUND)")
            return False
    except Exception as e:
        print(f"❌ {description} (ERROR: {e})")
        return False


def main():
    """Main verification function."""
    print("🔍 GitHound Frontend Refactoring Verification")
    print("=" * 50)

    # Get the project root
    project_root = Path(__file__).parent.parent
    static_dir = project_root / "githound" / "web" / "static"

    all_checks_passed = True

    print("\n📁 Directory Structure:")
    directories = [
        (static_dir / "components", "Components directory"),
        (static_dir / "components" / "core", "Core components"),
        (static_dir / "components" / "auth", "Auth components"),
        (static_dir / "components" / "search", "Search components"),
        (static_dir / "components" / "ui", "UI components"),
        (static_dir / "components" / "websocket", "WebSocket components"),
        (static_dir / "components" / "utils", "Utils components"),
        (static_dir / "styles", "Styles directory"),
        (static_dir / "styles" / "base", "Base styles"),
        (static_dir / "styles" / "components", "Component styles"),
        (static_dir / "utils", "Utilities directory"),
    ]

    for dir_path, description in directories:
        if not check_directory_exists(dir_path, description):
            all_checks_passed = False

    print("\n📄 Core Component Files:")
    core_files = [
        (static_dir / "components" / "core" / "component.js", "Base Component class"),
        (static_dir / "components" / "core" / "registry.js", "Component Registry"),
        (static_dir / "components" / "core" / "event-bus.js", "Event Bus"),
        (static_dir / "components" / "core" / "state-manager.js", "State Manager"),
        (static_dir / "components" / "core" / "app.js", "Main App Component"),
    ]

    for file_path, description in core_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    print("\n🧩 Component Files:")
    component_files = [
        (static_dir / "components" / "auth" / "auth-manager.js", "Auth Manager"),
        (static_dir / "components" / "search" / "search-manager.js", "Search Manager"),
        (static_dir / "components" / "ui" / "theme-manager.js", "Theme Manager"),
        (static_dir / "components" / "ui" / "notification-manager.js", "Notification Manager"),
        (static_dir / "components" / "websocket" / "websocket-manager.js", "WebSocket Manager"),
        (static_dir / "components" / "utils" / "export-manager.js", "Export Manager"),
    ]

    for file_path, description in component_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    print("\n🎨 Style Files:")
    style_files = [
        (static_dir / "styles" / "base" / "variables.css", "CSS Variables"),
        (static_dir / "styles" / "base" / "reset.css", "CSS Reset"),
        (static_dir / "styles" / "components" / "theme.css", "Theme Styles"),
        (static_dir / "styles" / "components" / "notifications.css", "Notification Styles"),
        (static_dir / "styles" / "components" / "connection.css", "Connection Styles"),
        (static_dir / "styles" / "main.css", "Main Stylesheet"),
    ]

    for file_path, description in style_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    print("\n🔧 Utility Files:")
    utility_files = [
        (static_dir / "utils" / "api.js", "API Utilities"),
        (static_dir / "utils" / "dom.js", "DOM Utilities"),
    ]

    for file_path, description in utility_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    print("\n🚀 Entry Points:")
    entry_files = [
        (static_dir / "main.js", "New Main Entry Point"),
        (static_dir / "index.html", "HTML File"),
        (static_dir / "app.js", "Legacy App (for fallback)"),
    ]

    for file_path, description in entry_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    print("\n🔍 Content Verification:")
    content_checks = [
        (static_dir / "main.js", "import GitHoundApp", "Main.js imports GitHoundApp"),
        (static_dir / "index.html", 'type="module"', "HTML uses ES6 modules"),
        (
            static_dir / "components" / "core" / "component.js",
            "export class Component",
            "Component class is exported",
        ),
        (
            static_dir / "components" / "auth" / "auth-manager.js",
            "extends Component",
            "AuthManager extends Component",
        ),
        (
            static_dir / "styles" / "base" / "variables.css",
            "--primary-color",
            "CSS variables defined",
        ),
    ]

    for file_path, text, description in content_checks:
        if not check_file_contains(file_path, text, description):
            all_checks_passed = False

    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 All checks passed! Frontend refactoring completed successfully.")
        print("\n📋 Next Steps:")
        print("1. Test the new modular frontend in a browser")
        print("2. Run the web frontend tests")
        print("3. Update documentation")
        return 0
    else:
        print("❌ Some checks failed. Please review the missing files/content above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
