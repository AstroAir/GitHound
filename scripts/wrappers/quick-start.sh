#!/bin/bash
# GitHound Quick Start
# Cross-platform wrapper for quick-start.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$SCRIPT_DIR/../quick-start.py" "$@"
