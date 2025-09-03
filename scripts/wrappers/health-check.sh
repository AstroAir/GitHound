#!/bin/bash
# GitHound Health Check
# Cross-platform wrapper for health-check.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$SCRIPT_DIR/../health-check.py" "$@"
