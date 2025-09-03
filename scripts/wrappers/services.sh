#!/bin/bash
# GitHound Services Manager
# Cross-platform wrapper for services.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$SCRIPT_DIR/../services.py" "$@"
