#!/bin/bash
# GitHound Development Environment Manager
# Cross-platform wrapper for dev-env.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$SCRIPT_DIR/../dev-env.py" "$@"
