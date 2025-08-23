#!/usr/bin/env python3
"""Find f-string issues in mcp_server.py"""

import re

def find_fstring_backslash_issues(filename):
    """Find f-strings that contain backslashes which cause syntax errors."""
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    issues = []
    for i, line in enumerate(lines, 1):
        # Look for f-strings that might contain backslashes
        if re.search(r'f["\'].*\\.*["\']', line):
            issues.append((i, line.strip()))
    
    return issues

if __name__ == "__main__":
    issues = find_fstring_backslash_issues('githound/mcp_server.py')
    if issues:
        print("Found potential f-string backslash issues:")
        for line_num, line in issues:
            print(f"Line {line_num}: {line}")
    else:
        print("No obvious f-string backslash issues found")
