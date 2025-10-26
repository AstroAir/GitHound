#!/bin/bash
# GitHound Cache Manager
# Cross-platform wrapper for cache-manager.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$SCRIPT_DIR/../cache-manager.py" "$@"
