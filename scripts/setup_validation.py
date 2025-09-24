#!/usr/bin/env python3
"""
Setup script for GitHound documentation validation tools.

This script ensures all validation scripts are properly configured and executable.
"""

import os
import stat
import sys
from pathlib import Path

def make_executable(script_path: Path) -> None:
    """Make a script executable."""
    current_permissions = script_path.stat().st_mode
    script_path.chmod(current_permissions | stat.S_IEXEC)
    print(f"✅ Made {script_path.name} executable")

def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    required_packages = [
        'yaml',
        'requests',
        'pathlib'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install with: pip install pyyaml requests")
        return False

    print("✅ All required Python packages are installed")
    return True

def setup_validation_scripts() -> bool:
    """Setup validation scripts."""
    script_dir = Path(__file__).parent
    validation_scripts = [
        'validate_documentation.py',
        'validate_all_docs.py',
        'validate_links.py',
        'validate_docs_examples.py',
        'validate_config_examples.py'
    ]

    success = True

    for script_name in validation_scripts:
        script_path = script_dir / script_name
        if script_path.exists():
            try:
                make_executable(script_path)
            except Exception as e:
                print(f"❌ Failed to make {script_name} executable: {e}")
                success = False
        else:
            print(f"⚠️  Script not found: {script_name}")
            success = False

    return success

def check_config_files() -> bool:
    """Check if configuration files exist."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    config_files = [
        script_dir / 'validation-config.yaml',
        project_root / '.markdownlint.json',
        project_root / '.pre-commit-config.yaml'
    ]

    success = True

    for config_file in config_files:
        if config_file.exists():
            print(f"✅ Found config file: {config_file.name}")
        else:
            print(f"❌ Missing config file: {config_file}")
            success = False

    return success

def test_validation_scripts() -> bool:
    """Test that validation scripts can be imported/executed."""
    script_dir = Path(__file__).parent

    # Test importing the main validation module
    try:
        sys.path.insert(0, str(script_dir))
        from validate_documentation import DocumentationValidator
        print("✅ Main validation module can be imported")
    except ImportError as e:
        print(f"❌ Failed to import validation module: {e}")
        return False

    # Test basic functionality
    try:
        project_root = script_dir.parent
        validator = DocumentationValidator(project_root)
        print("✅ DocumentationValidator can be instantiated")
    except Exception as e:
        print(f"❌ Failed to create DocumentationValidator: {e}")
        return False

    return True

def setup_pre_commit_hook() -> bool:
    """Setup pre-commit hook if pre-commit is available."""
    try:
        import subprocess
        result = subprocess.run(['pre-commit', '--version'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Pre-commit is available")

            # Install the hooks
            project_root = Path(__file__).parent.parent
            result = subprocess.run(['pre-commit', 'install'],
                                  cwd=project_root, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Pre-commit hooks installed")
                return True
            else:
                print(f"⚠️  Failed to install pre-commit hooks: {result.stderr}")
                return False
        else:
            print("⚠️  Pre-commit not available")
            return True  # Not a failure, just not available
    except FileNotFoundError:
        print("⚠️  Pre-commit not installed")
        return True  # Not a failure, just not available
    except Exception as e:
        print(f"⚠️  Error checking pre-commit: {e}")
        return True  # Not a failure, just not available

def main():
    """Main setup function."""
    print("GitHound Documentation Validation Setup")
    print("=" * 40)

    checks = [
        ("Checking dependencies", check_dependencies),
        ("Setting up validation scripts", setup_validation_scripts),
        ("Checking configuration files", check_config_files),
        ("Testing validation scripts", test_validation_scripts),
        ("Setting up pre-commit hooks", setup_pre_commit_hook)
    ]

    all_passed = True

    for description, check_func in checks:
        print(f"\n{description}...")
        if not check_func():
            all_passed = False

    print("\n" + "=" * 40)
    if all_passed:
        print("✅ Documentation validation setup completed successfully!")
        print("\nYou can now run:")
        print("  make docs-validate          # Full validation")
        print("  make docs-validate-quick     # Quick validation")
        print("  make docs-lint               # Markdown linting")
        print("  python scripts/validate_all_docs.py  # Direct script execution")
    else:
        print("❌ Setup completed with some issues.")
        print("Please review the output above and fix any problems.")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
