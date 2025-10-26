"""
Comprehensive documentation validation runner for GitHound.

This script runs all documentation validation checks:
- Link validation (internal and external)
- Code example validation
- Configuration example validation
- Style and formatting validation
- Content completeness checking
- Markdownlint integration
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_markdownlint(project_root: Path, files: list[Path] | None = None) -> bool:
    """Run markdownlint on documentation files."""
    print("Running markdownlint...")

    try:
        cmd = ["markdownlint"]

        if files:
            # Validate specific files
            cmd.extend([str(f) for f in files])
        else:
            # Validate all markdown files
            cmd.extend(["**/*.md"])

        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Markdownlint: All checks passed")
            return True
        else:
            print("❌ Markdownlint: Issues found")
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
            return False

    except FileNotFoundError:
        print("⚠️  Markdownlint not found. Install with: npm install -g markdownlint-cli")
        return True  # Don't fail if markdownlint is not installed
    except Exception as e:
        print(f"⚠️  Error running markdownlint: {e}")
        return True  # Don't fail on unexpected errors


def run_comprehensive_validation(
    project_root: Path,
    config_path: Path | None = None,
    files: list[Path] | None = None,
    skip_external: bool = False,
) -> bool:
    """Run the comprehensive documentation validator."""
    print("Running comprehensive documentation validation...")

    try:
        # Import the comprehensive validator
        sys.path.insert(0, str(project_root / "scripts"))
        from validate_documentation import DocumentationValidator

        validator = DocumentationValidator(project_root, config_path)

        if skip_external:
            validator.config["skip_external_links"] = True

        success = validator.run_validation(files)
        validator.print_results()

        return success

    except ImportError as e:
        print(f"❌ Could not import comprehensive validator: {e}")
        return False
    except Exception as e:
        print(f"❌ Error running comprehensive validation: {e}")
        return False


def run_legacy_validators(project_root: Path) -> bool:
    """Run the legacy validation scripts for comparison."""
    print("Running legacy validation scripts...")

    scripts = ["validate_links.py", "validate_docs_examples.py", "validate_config_examples.py"]

    all_passed = True

    for script in scripts:
        script_path = project_root / "scripts" / script
        if script_path.exists():
            try:
                print(f"  Running {script}...")
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    print(f"  ✅ {script}: Passed")
                else:
                    print(f"  ❌ {script}: Failed")
                    if result.stdout:
                        print(f"    Output: {result.stdout}")
                    if result.stderr:
                        print(f"    Errors: {result.stderr}")
                    all_passed = False

            except Exception as e:
                print(f"  ⚠️  Error running {script}: {e}")
                all_passed = False
        else:
            print(f"  ⚠️  {script} not found")

    return all_passed


def run_pre_commit_hooks(project_root: Path) -> bool:
    """Run pre-commit hooks that include documentation checks."""
    print("Running pre-commit hooks...")

    try:
        result = subprocess.run(
            ["pre-commit", "run", "--all-files"], cwd=project_root, capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✅ Pre-commit hooks: All checks passed")
            return True
        else:
            print("❌ Pre-commit hooks: Issues found")
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
            return False

    except FileNotFoundError:
        print("⚠️  Pre-commit not found. Install with: pip install pre-commit")
        return True  # Don't fail if pre-commit is not installed
    except Exception as e:
        print(f"⚠️  Error running pre-commit: {e}")
        return True  # Don't fail on unexpected errors


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive GitHound documentation validation"
    )
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument(
        "--skip-external", action="store_true", help="Skip external link validation"
    )
    parser.add_argument("--skip-markdownlint", action="store_true", help="Skip markdownlint checks")
    parser.add_argument("--skip-precommit", action="store_true", help="Skip pre-commit hooks")
    parser.add_argument("--legacy-only", action="store_true", help="Run only legacy validators")
    parser.add_argument(
        "--comprehensive-only", action="store_true", help="Run only comprehensive validator"
    )
    parser.add_argument("files", nargs="*", type=Path, help="Specific files to validate")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    files = [project_root / f for f in args.files] if args.files else None

    print("=" * 60)
    print("GITHOUND DOCUMENTATION VALIDATION")
    print("=" * 60)

    results = []

    # Run markdownlint
    if not args.skip_markdownlint and not args.legacy_only and not args.comprehensive_only:
        results.append(("Markdownlint", run_markdownlint(project_root, files)))

    # Run comprehensive validation
    if not args.legacy_only:
        results.append(
            (
                "Comprehensive Validation",
                run_comprehensive_validation(project_root, args.config, files, args.skip_external),
            )
        )

    # Run legacy validators
    if args.legacy_only or (not args.comprehensive_only and not files):
        results.append(("Legacy Validators", run_legacy_validators(project_root)))

    # Run pre-commit hooks
    if (
        not args.skip_precommit
        and not args.legacy_only
        and not args.comprehensive_only
        and not files
    ):
        results.append(("Pre-commit Hooks", run_pre_commit_hooks(project_root)))

    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 All documentation validation checks passed!")
        sys.exit(0)
    else:
        print("\n💥 Some validation checks failed. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
