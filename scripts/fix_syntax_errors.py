"""
Script to fix common syntax errors in test files.
Specifically fixes '= =' to '==' and other common issues.
"""

import re
import sys
from pathlib import Path


def fix_syntax_errors(file_path: Path) -> tuple[bool, list[str]]:
    """
    Fix syntax errors in a Python file.

    Returns:
        Tuple of (was_modified, list_of_changes)
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return False, [f"Error reading file: {e}"]

    original_content = content
    changes = []

    # Fix 1: Replace '= =' with '=='
    pattern1 = r"(\w+(?:\.\w+)*)\s*=\s*=\s*"
    matches = re.findall(pattern1, content)
    if matches:
        content = re.sub(pattern1, r"\1 == ", content)
        changes.append(f"Fixed {len(matches)} '= =' syntax errors")

    # Fix 2: Fix common indentation issues (basic)
    lines = content.split("\n")
    fixed_lines = []
    for i, line in enumerate(lines):
        # Fix mixed tabs/spaces (convert tabs to 4 spaces)
        if "\t" in line:
            line = line.replace("\t", "    ")
            if i == 0 or not any("\t" in l for l in lines[:i]):
                changes.append("Fixed tab/space indentation issues")
        fixed_lines.append(line)

    content = "\n".join(fixed_lines)

    # Fix 3: Fix common typos in docstrings
    if content.startswith('ji"""'):
        content = content.replace('ji"""', '"""', 1)
        changes.append('Fixed docstring typo \'ji"""\' -> \'"""\'')

    # Fix 4: Fix unmatched indentation (basic detection)
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.strip().startswith("async with") and line.endswith(":"):
            # Check if next line is properly indented
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.strip() and not next_line.startswith("    "):
                    # This might be an indentation error, but we'll be conservative
                    pass

    # Write back if modified
    if content != original_content:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, changes
        except Exception as e:
            return False, [f"Error writing file: {e}"]

    return False, []


def main():
    """Main function to fix syntax errors in test files."""
    if len(sys.argv) > 1:
        test_dir = Path(sys.argv[1])
    else:
        test_dir = Path("tests")

    if not test_dir.exists():
        print(f"Error: Directory {test_dir} does not exist")
        return 1

    print(f"Fixing syntax errors in {test_dir}...")

    total_files = 0
    modified_files = 0
    total_changes = 0

    # Find all Python test files
    for py_file in test_dir.rglob("*.py"):
        if py_file.name.startswith("test_") or py_file.parent.name == "tests":
            total_files += 1
            was_modified, changes = fix_syntax_errors(py_file)

            if was_modified:
                modified_files += 1
                total_changes += len(changes)
                print(f"✓ Fixed {py_file}: {', '.join(changes)}")
            else:
                if changes:  # Had errors but couldn't fix
                    print(f"✗ Could not fix {py_file}: {', '.join(changes)}")

    print("\nSummary:")
    print(f"  Total files processed: {total_files}")
    print(f"  Files modified: {modified_files}")
    print(f"  Total changes made: {total_changes}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
